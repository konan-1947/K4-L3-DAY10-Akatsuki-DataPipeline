from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from pipelines.phase1 import main as run_phase1
from retrieval.index import LocalEmbeddingIndex

def main() -> None:
    """Run corruption, evaluation, repair, and comparison flow.

    Pseudo-code:
    1. Load baseline metrics va clean dataset.
    2. Tao corrupted dataframe.
    3. Save corrupted artifacts.
    4. Rebuild index va evaluate.
    5. Run quality checks/freshness tren corrupted data.
    6. Repair lai tu raw records.
    7. Evaluate repaired dataset.
    8. Tao comparison report.
    """
    settings = load_settings()
    if not settings.paths.baseline_metrics.exists() or not settings.paths.clean_json.exists():
        run_phase1()

    baseline_metrics = read_json(settings.paths.baseline_metrics)
    baseline_df = pd.DataFrame(read_json(settings.paths.clean_json))

    corrupted_df = corrupt_clean_dataframe(baseline_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    corrupted_freshness = build_freshness_report(
        corrupted_df,
        settings,
        settings.paths.quality_dir / "corrupted_freshness_report.json",
    )
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df,
        settings,
        settings.paths.corrupted_embeddings_json,
    )
    corrupted_evaluation = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )

    # Repair always starts from the immutable raw snapshot, not from the corrupted CSV.
    repaired_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(repaired_records, now_utc())
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    repaired_quality = run_data_quality_checks(settings=settings, df=repaired_df, report_name="repaired")
    repaired_freshness = build_freshness_report(
        repaired_df,
        settings,
        settings.paths.quality_dir / "repaired_freshness_report.json",
    )
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df,
        settings,
        settings.paths.repaired_embeddings_json,
    )
    repaired_evaluation = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )

    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics,
        corrupted_evaluation.summary,
        repaired_evaluation.summary,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness,
    )
    print("\nState                 Hit Rate   Token F1   Judge Score")
    for name, metrics in [
        ("Baseline", baseline_metrics),
        ("Corrupted", corrupted_evaluation.summary),
        ("Repaired", repaired_evaluation.summary),
    ]:
        print(
            f"{name:<20} {metrics.get('retrieval_hit_rate', 0):>8.3f}"
            f" {metrics.get('mean_token_f1', 0):>10.3f}"
            f" {metrics.get('mean_judge_score', 0):>12.3f}"
        )
