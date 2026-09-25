from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from core.utils import write_json
from ingestion.cleaning import build_embedding_text


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate several data-corruption modes and record each event.

    Pseudo-code:
    1. Drop mot so latest records.
    2. Blank summary o mot so dong.
    3. Inject noise vao text.
    4. Lam title bi truncate.
    5. Lam published date cu di.
    6. Add duplicate rows.
    7. Rebuild `text_for_embedding`.
    8. Ghi corruption log vao output_log_path.
    """
    corrupted = df.copy(deep=True).reset_index(drop=True)
    log: list[dict[str, object]] = []

    if corrupted.empty:
        write_json(output_log_path, {"total_errors": 0, "events": []})
        return corrupted

    # 1. Drop the newest 20% of records, with at least one record affected.
    drop_count = max(1, int(len(corrupted) * 0.20))
    newest_ids = corrupted.sort_values("published", ascending=False).head(drop_count)["paper_id"].tolist()
    corrupted = corrupted[~corrupted["paper_id"].isin(newest_ids)].reset_index(drop=True)
    log.append({"type": "drop_latest_records", "count": len(newest_ids), "paper_ids": newest_ids})

    if corrupted.empty:
        write_json(output_log_path, {"total_errors": len(log), "events": log})
        return corrupted

    # Use different rows so every corruption remains observable in the log.
    target_positions = list(range(min(5, len(corrupted))))

    # 2. Blank summary.
    blank_pos = target_positions[0]
    blank_id = str(corrupted.at[blank_pos, "paper_id"])
    corrupted.at[blank_pos, "summary"] = ""
    log.append({"type": "blank_summary", "count": 1, "paper_ids": [blank_id]})

    # 3. Inject obvious noise into a summary.
    noise_pos = target_positions[min(1, len(target_positions) - 1)]
    noise_id = str(corrupted.at[noise_pos, "paper_id"])
    corrupted.at[noise_pos, "summary"] = "@@@ ### $$$ CORRUPTED_NOISE $$$ ### @@@ " + str(
        corrupted.at[noise_pos, "summary"]
    )
    log.append({"type": "inject_noise", "count": 1, "paper_ids": [noise_id]})

    # 4. Truncate a title below the required quality threshold.
    title_pos = target_positions[min(2, len(target_positions) - 1)]
    title_id = str(corrupted.at[title_pos, "paper_id"])
    corrupted.at[title_pos, "title"] = "Noisy"
    log.append({"type": "truncate_title", "count": 1, "paper_ids": [title_id]})

    # 5. Make a record stale by moving its publication date one year back.
    stale_pos = target_positions[min(3, len(target_positions) - 1)]
    stale_id = str(corrupted.at[stale_pos, "paper_id"])
    stale_date = datetime.now(UTC).date() - timedelta(days=365)
    corrupted.at[stale_pos, "published"] = stale_date.isoformat()
    corrupted.at[stale_pos, "age_days"] = 365
    log.append({"type": "stale_date", "count": 1, "paper_ids": [stale_id], "published": stale_date.isoformat()})

    # 6. Duplicate rows, preserving the same paper_id to trigger uniqueness checks.
    duplicate_count = min(2, len(corrupted))
    duplicates = corrupted.iloc[:duplicate_count].copy()
    corrupted = pd.concat([corrupted, duplicates], ignore_index=True)
    log.append(
        {
            "type": "duplicate_rows",
            "count": duplicate_count,
            "paper_ids": duplicates["paper_id"].astype(str).tolist(),
        }
    )

    # Recompute derived text after all field-level mutations.
    for index, row in corrupted.iterrows():
        corrupted.at[index, "summary_chars"] = len(str(row.get("summary", "") or ""))
        corrupted.at[index, "text_for_embedding"] = build_embedding_text(
            str(row.get("title", "") or ""),
            str(row.get("authors_joined", "") or ""),
            str(row.get("published", "") or ""),
            str(row.get("categories_joined", "") or ""),
            str(row.get("summary", "") or ""),
        )

    write_json(
        output_log_path,
        {
            "total_errors": len(log),
            "source_rows": int(len(df)),
            "corrupted_rows": int(len(corrupted)),
            "events": log,
        },
    )
    return corrupted
