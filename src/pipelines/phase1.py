from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc, read_json, write_json, write_csv
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex

def main() -> None:
    """Build and run the baseline pipeline end-to-end.

    Pseudo-code:
    1. Load settings.
    2. Load hoac fetch raw records.
    3. Clean data.
    4. Save clean CSV/JSON.
    5. Build Chroma index.
    6. Tao hoac load evaluation set.
    7. Evaluate.
    8. Run quality checks va freshness report.
    9. Tao markdown report.
    10. Co the demo agent tren vai sample question.
    """
    settings = load_settings()
    records = fetch_source_records(settings)
    run_date = now_utc()
    df = build_clean_dataframe(records, run_date)
    if df.empty:
        raise RuntimeError("Cleaning produced no usable paper records.")

    write_csv(df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df.to_dict(orient="records"))

    quality = run_data_quality_checks(df, settings, "baseline")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)
    if not quality["success"]:
        raise RuntimeError("Baseline data quality gate failed; inspect data/quality/baseline_quality_report.json")

    index = LocalEmbeddingIndex.build(df, settings, settings.paths.embeddings_json)
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        build_test_set(df, settings.paths.eval_testset)
    else:
        # Validate the existing artifact is readable and has the expected shape.
        if len(read_json(settings.paths.eval_testset)) != 10:
            build_test_set(df, settings.paths.eval_testset)

    evaluation = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    source_summary = {
        "records": len(records),
        "mode": "live Crossref API" if settings.refresh_source else "offline snapshot",
        "embedding_model": settings.embedding_model,
    }
    metrics = dict(evaluation.summary)
    metrics["quality_success"] = quality["success"]
    metrics["freshness_is_fresh"] = freshness["is_fresh"]
    write_json(settings.paths.baseline_metrics, metrics)
    generate_phase1_report(settings.paths.baseline_report, source_summary, metrics, quality, freshness)
    print(f"Baseline complete: {len(df)} records, hit_rate={evaluation.summary['retrieval_hit_rate']:.3f}")
