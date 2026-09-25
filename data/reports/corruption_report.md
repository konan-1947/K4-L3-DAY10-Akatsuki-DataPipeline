# Corruption and Repair Comparison

## RAG metrics

| Metric | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| Retrieval hit rate | 1.0 | 0.5 | 1.0 |
| Mean token F1 | 1.0 | 0.7150875576036866 | 1.0 |
| Judge accuracy | 1.0 | 0.6 | 1.0 |
| Mean judge score | 5 | 3.7 | 5 |

## Quality and freshness signals

| Signal | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| Quality gate | `True` | `False` | `True` |
| Freshness SLA | `True` | `True` | `True` |
| Stale rows | `n/a` | `2` | `1` |

## Interpretation

The corrupted state intentionally introduces missing summaries, noisy text, a truncated title, stale dates,
missing recent records, and duplicate IDs. The quality gate and freshness checks should flag those violations.
The repaired state is rebuilt from the immutable raw snapshot, so rerunning repair is idempotent and should
return the same clean schema and evaluation behavior as the baseline.
