from __future__ import annotations

from typing import Any

from core.utils import write_text


def _metric_row(metrics: dict[str, Any]) -> str:
    return " | ".join(
        [
            f"{metrics.get('retrieval_hit_rate', 'n/a')}",
            f"{metrics.get('mean_token_f1', 'n/a')}",
            f"{metrics.get('judge_accuracy', 'n/a')}",
            f"{metrics.get('mean_judge_score', 'n/a')}",
        ]
    )


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write the markdown report for the baseline phase.

    Pseudo-code:
    1. Gom source summary.
    2. In metrics retrieval/evaluation.
    3. In data quality va freshness.
    4. Ghi markdown vao report_path.
    """
    text = f"""# Phase 1 — Baseline Pipeline Report

## Source

- Records processed: **{source_summary.get('records', source_summary.get('count', 'n/a'))}**
- Source mode: `{source_summary.get('mode', 'offline snapshot')}`
- Embedding model: `{source_summary.get('embedding_model', 'OpenAI embedding')}`

## Retrieval and answer metrics

| Retrieval hit rate | Mean token F1 | Judge accuracy | Mean judge score |
|---:|---:|---:|---:|
| {metrics.get('retrieval_hit_rate', 'n/a')} | {metrics.get('mean_token_f1', 'n/a')} | {metrics.get('judge_accuracy', 'n/a')} | {metrics.get('mean_judge_score', 'n/a')} |

## Data quality

- Quality gate success: **{quality.get('success')}**
- Rows checked: **{quality.get('row_count')}**
- Expectations evaluated: **{len(quality.get('expectations', []))}**

## Freshness

- Latest publication: `{freshness.get('latest_published')}`
- Oldest publication: `{freshness.get('oldest_published')}`
- Stale rows: **{freshness.get('stale_rows')} / {freshness.get('total_rows')}**
- Freshness SLA: **{freshness.get('is_fresh')}**

## Conclusion

The baseline artifacts provide the clean-data reference point for the later corruption and repair comparison.
"""
    write_text(report_path, text)


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Write a markdown comparison of baseline, corrupted, and repaired runs."""
    text = f"""# Corruption and Repair Comparison

## RAG metrics

| Metric | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| Retrieval hit rate | {baseline_metrics.get('retrieval_hit_rate', 'n/a')} | {corrupted_metrics.get('retrieval_hit_rate', 'n/a')} | {repaired_metrics.get('retrieval_hit_rate', 'n/a')} |
| Mean token F1 | {baseline_metrics.get('mean_token_f1', 'n/a')} | {corrupted_metrics.get('mean_token_f1', 'n/a')} | {repaired_metrics.get('mean_token_f1', 'n/a')} |
| Judge accuracy | {baseline_metrics.get('judge_accuracy', 'n/a')} | {corrupted_metrics.get('judge_accuracy', 'n/a')} | {repaired_metrics.get('judge_accuracy', 'n/a')} |
| Mean judge score | {baseline_metrics.get('mean_judge_score', 'n/a')} | {corrupted_metrics.get('mean_judge_score', 'n/a')} | {repaired_metrics.get('mean_judge_score', 'n/a')} |

## Quality and freshness signals

| Signal | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| Quality gate | `{baseline_metrics.get('quality_success', 'see phase1 report')}` | `{corrupted_quality.get('success')}` | `{repaired_quality.get('success')}` |
| Freshness SLA | `{baseline_metrics.get('freshness_is_fresh', 'see phase1 report')}` | `{corrupted_freshness.get('is_fresh')}` | `{repaired_freshness.get('is_fresh')}` |
| Stale rows | `n/a` | `{corrupted_freshness.get('stale_rows')}` | `{repaired_freshness.get('stale_rows')}` |

## Interpretation

The corrupted state intentionally introduces missing summaries, noisy text, a truncated title, stale dates,
missing recent records, and duplicate IDs. The quality gate and freshness checks should flag those violations.
The repaired state is rebuilt from the immutable raw snapshot, so rerunning repair is idempotent and should
return the same clean schema and evaluation behavior as the baseline.
"""
    write_text(report_path, text)
