from __future__ import annotations

from datetime import date, datetime
import re
from typing import Iterable

import pandas as pd

from ingestion.crossref import PaperRecord
from core.utils import compact_join, normalize_whitespace


def _clean_text(value: object) -> str:
    text = str(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(text)


def _as_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [_clean_text(item) for item in value if _clean_text(item)]
    cleaned = _clean_text(value)
    return [cleaned] if cleaned else []


def _parse_date(value: object) -> date | None:
    if value is None or str(value).strip() == "":
        return None
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return None
    return parsed.date()


def build_embedding_text(
    title: str,
    authors_joined: str,
    published: str,
    categories_joined: str,
    summary: str,
) -> str:
    return "\n".join(
        [
            f"Title: {title}",
            f"Authors: {authors_joined}",
            f"Published: {published}",
            f"Categories: {categories_joined}",
            f"Summary: {summary}",
        ]
    )


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records into a dataframe ready for embedding.

    Pseudo-code:
    1. Normalize title, summary, authors, categories.
    2. Parse published/updated date.
    3. Tinh age_days.
    4. Tao cot helper:
       - authors_joined
       - categories_joined
       - summary_chars
       - text_for_embedding
    5. Drop duplicates va filter row xau.
    6. Sort dataframe va return.
    """
    run_day = run_date.date() if isinstance(run_date, datetime) else pd.Timestamp(run_date).date()
    rows: list[dict[str, object]] = []
    seen: set[str] = set()

    for record in records:
        paper_id = _clean_text(record.paper_id)
        title = _clean_text(record.title)
        published_day = _parse_date(record.published)
        if not paper_id or not title or published_day is None or paper_id.lower() in seen:
            continue
        seen.add(paper_id.lower())

        summary = _clean_text(record.summary)
        authors = _as_list(record.authors)
        categories = _as_list(record.categories)
        authors_joined = compact_join(authors)
        categories_joined = compact_join(categories)
        published = published_day.isoformat()
        updated_day = _parse_date(record.updated) or published_day
        text_for_embedding = build_embedding_text(
            title=title,
            authors_joined=authors_joined,
            published=published,
            categories_joined=categories_joined,
            summary=summary,
        )
        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "authors_joined": authors_joined,
                "categories": categories,
                "categories_joined": categories_joined,
                "primary_category": _clean_text(record.primary_category) or (categories[0] if categories else "Uncategorized"),
                "published": published,
                "updated": updated_day.isoformat(),
                "age_days": max(0, (run_day - published_day).days),
                "summary_chars": len(summary),
                "text_for_embedding": text_for_embedding,
                "abs_url": _clean_text(record.abs_url),
                "pdf_url": _clean_text(record.pdf_url),
                "comment": _clean_text(record.comment),
            }
        )

    columns = [
        "paper_id", "title", "summary", "authors", "authors_joined", "categories", "categories_joined",
        "primary_category", "published", "updated", "age_days", "summary_chars",
        "text_for_embedding", "abs_url", "pdf_url", "comment",
    ]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows, columns=columns).sort_values(
        by=["published", "paper_id"], ascending=[False, True], kind="stable"
    ).reset_index(drop=True)
