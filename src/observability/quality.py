from __future__ import annotations

from typing import Any

import great_expectations as gx
import pandas as pd
from great_expectations.expectations import (
    ExpectColumnValueLengthsToBeBetween,
    ExpectColumnValuesToBeUnique,
    ExpectColumnValuesToNotBeNull,
    ExpectTableRowCountToBeBetween,
)

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run the data-quality checks and persist a JSON report.

    Pseudo-code:
    1. Check row count.
    2. Check `paper_id` not null va unique.
    3. Check `title` not null.
    4. Check do dai `summary`.
    5. Check freshness bang `age_days`.
    6. Ghi ket qua vao `data/quality/`.
    """
    context = gx.get_context(mode="ephemeral")
    source = context.data_sources.add_pandas(name=f"papers_source_{report_name}")
    asset = source.add_dataframe_asset(name=f"papers_asset_{report_name}")
    batch_definition = asset.add_batch_definition_whole_dataframe(f"papers_batch_{report_name}")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    expectations = [
        ExpectTableRowCountToBeBetween(min_value=5, max_value=5000),
        *(ExpectColumnValuesToNotBeNull(column=column) for column in ["paper_id", "title", "text_for_embedding"]),
        ExpectColumnValuesToBeUnique(column="paper_id"),
        ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30),
    ]
    expectation_results: list[dict[str, Any]] = []
    for expectation in expectations:
        try:
            result = batch.validate(expectation)
            expectation_results.append(result.to_json_dict())
        except Exception as exc:
            expectation_results.append(
                {
                    "success": False,
                    "expectation_config": {"type": expectation.expectation_type},
                    "exception_info": {"raised_exception": True, "exception_message": str(exc)},
                }
            )

    title_lengths = df["title"].fillna("").astype(str).str.len() if "title" in df else pd.Series(dtype=int)
    manual_title_check = {
        "success": bool(title_lengths.empty or (title_lengths >= 8).all()),
        "unexpected_count": int((title_lengths < 8).sum()) if not title_lengths.empty else 0,
        "rule": "title length >= 8",
    }
    quality_success = all(bool(result.get("success")) for result in expectation_results) and manual_title_check["success"]
    payload = {
        "report_name": report_name,
        "success": quality_success,
        "row_count": int(len(df)),
        "expectations": expectation_results,
        "manual_checks": {"title_length": manual_title_check},
    }
    if report_name == "baseline":
        report_path = settings.paths.baseline_quality_report
    elif report_name == "corrupted":
        report_path = settings.paths.corrupted_quality_report
    else:
        report_path = settings.paths.quality_dir / f"{report_name}_quality_report.json"
    write_json(report_path, payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Build and persist a freshness report.

    Pseudo-code:
    1. Tim latest va oldest published date.
    2. Dem so dong stale.
    3. Tao payload:
       - latest_published
       - oldest_published
       - stale_rows
       - total_rows
       - is_fresh
    4. Ghi JSON report.
    """
    dates = pd.to_datetime(df.get("published", pd.Series(dtype=str)), errors="coerce", utc=True).dropna()
    age_days = pd.to_numeric(df.get("age_days", pd.Series(dtype=float)), errors="coerce")
    stale_mask = age_days > settings.freshness_threshold_days
    stale_rows = int(stale_mask.fillna(False).sum())
    total_rows = int(len(df))
    stale_ratio = stale_rows / total_rows if total_rows else 1.0
    payload = {
        "latest_published": dates.max().date().isoformat() if not dates.empty else None,
        "oldest_published": dates.min().date().isoformat() if not dates.empty else None,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": stale_ratio,
        "threshold_days": settings.freshness_threshold_days,
        "max_stale_ratio": 0.25,
        "is_fresh": bool(total_rows and stale_ratio <= 0.25),
    }
    write_json(report_path, payload)
    return payload
