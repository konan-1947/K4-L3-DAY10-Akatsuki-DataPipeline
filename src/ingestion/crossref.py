from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import html
import json
from pathlib import Path
import re
import time

import requests

from core.config import Settings
from core.utils import normalize_whitespace, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse a Crossref payload into a list of ``PaperRecord`` objects.

    Pseudo-code:
    1. Duyet `payload["message"]["items"]`.
    2. Lay DOI, title, abstract, authors, subject, dates, URLs.
    3. Chuan hoa text va bo record khong hop le.
    4. Tra ve list `PaperRecord`.
    """
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    def clean_text(value: object) -> str:
        text = html.unescape(str(value or ""))
        text = re.sub(r"<[^>]+>", " ", text)
        return normalize_whitespace(text)

    def first_value(item: dict, *keys: str) -> str:
        for key in keys:
            value = item.get(key)
            if isinstance(value, list) and value:
                value = value[0]
            cleaned = clean_text(value)
            if cleaned:
                return cleaned
        return ""

    def date_value(item: dict, *keys: str) -> str:
        for key in keys:
            value = item.get(key) or {}
            parts = value.get("date-parts", [[]]) if isinstance(value, dict) else [[]]
            parts = parts[0] if parts else []
            if parts:
                year = int(parts[0])
                month = int(parts[1]) if len(parts) > 1 else 1
                day = int(parts[2]) if len(parts) > 2 else 1
                try:
                    return date(year, month, day).isoformat()
                except ValueError:
                    return str(year)
        return ""

    for item in items:
        paper_id = clean_text(item.get("DOI") or item.get("URL"))
        title = first_value(item, "title")
        if not paper_id or not title:
            continue

        authors: list[str] = []
        for author in item.get("author", []) or []:
            if not isinstance(author, dict):
                continue
            name = normalize_whitespace(
                " ".join(part for part in [author.get("given", ""), author.get("family", "")] if part)
            )
            if name:
                authors.append(name)

        categories = [clean_text(value) for value in item.get("subject", []) or []]
        categories = [value for value in categories if value]
        published = date_value(item, "published", "published-print", "published-online", "issued", "created")
        updated = date_value(item, "updated", "created") or published
        links = item.get("link", []) or []
        pdf_url = next(
            (str(link.get("URL")) for link in links if link.get("content-type") == "application/pdf"),
            str(item.get("URL") or ""),
        )
        abs_url = str(item.get("URL") or (f"https://doi.org/{paper_id}" if paper_id else ""))
        summary = first_value(item, "abstract", "description")
        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=categories[0] if categories else "Uncategorized",
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=f"Crossref record {paper_id}",
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch the source API, persist the raw response, and parse records.

    Pseudo-code:
    1. Tao params tu `settings.source_query`, `settings.source_filter`, `settings.max_results`.
    2. Goi API voi retry cho cac status code nhu 429/503.
    3. Luu raw response vao `settings.paths.raw_api_response`.
    4. Parse payload bang `parse_crossref_payload`.
    5. Luu records vao `settings.paths.raw_records_json`.
    """
    # Prefer the checked-in snapshot for reproducible lab runs. Set
    # REFRESH_SOURCE=true when a live Crossref refresh is explicitly desired.
    if not settings.refresh_source and settings.paths.raw_records_json.exists():
        return load_raw_records(settings.paths.raw_records_json)

    endpoint = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
        "select": "DOI,title,abstract,author,subject,published,updated,created,URL,link",
    }
    headers = {"User-Agent": "day10-data-observability-lab/0.1 (mailto:lab@example.com)"}
    payload: dict | None = None
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = requests.get(endpoint, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            payload = response.json()
            write_json(settings.paths.raw_api_response, payload)
            break
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2**attempt)

    if payload is None:
        if settings.paths.raw_api_response.exists():
            payload = json.loads(settings.paths.raw_api_response.read_text(encoding="utf-8"))
        elif settings.paths.raw_records_json.exists():
            return load_raw_records(settings.paths.raw_records_json)
        else:
            raise RuntimeError(f"Unable to fetch Crossref data: {last_error}") from last_error

    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [record.__dict__ for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Read a JSON snapshot and map it to ``PaperRecord`` objects."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return parse_crossref_payload(payload)
    if not isinstance(payload, list):
        raise ValueError(f"Expected a list of raw records in {path}")
    return [PaperRecord(**item) for item in payload]
