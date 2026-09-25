# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
|---|---|
| Khóa/lớp | `K4-L3-DAY10` |
| Tên nhóm | Akatsuki |
| Repository | <https://github.com/konan-1947/K4-L3-DAY10-Akatsuki-DataPipeline> |
| Ngày hoàn thành | `2026-09-25` |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
|---:|---|---|---|---|
| 1 | Vũ Đình Đăng | `2A202602946` | Pipeline integration | `core/`, `pipelines/`, tổng hợp report |
| 2 | Nguyễn Chí Công | `2A202602634` | Data foundation & recovery | `ingestion/`, raw/clean data, corruption/repair |
| 3 | Hoàng Trung Anh | `2A202602521` | RAG, evaluation & observability | `retrieval/`, `evaluation/`, `observability/` |

## 2. Tóm tắt kết quả

Nhóm đã hoàn thiện pipeline dữ liệu từ Crossref snapshot đến ingestion, cleaning, quality gate, embedding, ChromaDB retrieval, evaluation, corruption và repair. Baseline xử lý 24 bài báo, tạo clean CSV/JSON, embedding manifest, ChromaDB index, test set 10 câu hỏi và các báo cáo quality/freshness. Sáu dạng lỗi được tiêm gồm loại bản ghi mới nhất, xóa summary, chèn noise, làm ngắn title, làm cũ ngày xuất bản và duplicate rows. Corrupted state làm retrieval hit rate giảm từ 1.000 xuống 0.500, token F1 giảm còn 0.715 và judge score còn 3.7; quality gate chuyển sang Fail. Repair được xây dựng lại từ raw snapshot bất biến, khôi phục hit rate và token F1 về 1.000, judge score về 5.0 và quality gate về Pass. Giới hạn hiện tại là Ragas pass chưa bật mặc định và embedding dùng OpenAI `text-embedding-3-small` theo cấu hình nhóm thay cho MiniLM trong rubric gốc.

## 3. Kiến trúc và trách nhiệm

```text
Crossref snapshot/API -> raw preservation -> cleaning/data contract
    -> OpenAI embedding + ChromaDB -> baseline evaluation
    -> quality/freshness checks -> corruption -> re-evaluation
    -> repair from raw snapshot -> repaired evaluation/report
```

| Khối | Xử lý chính | Output | Owner |
|---|---|---|---|
| Ingestion | Fetch/retry, parse Crossref, offline fallback | `data/raw/` | Nguyễn Chí Công |
| Cleaning | Chuẩn hóa schema, deduplicate, `age_days`, embedding text | `data/clean/` | Nguyễn Chí Công |
| Embedding/index | OpenAI `text-embedding-3-small`, ChromaDB collections | `data/embeddings/`, `data/chroma/` | Hoàng Trung Anh |
| Evaluation | Test set, retrieval hit rate, token F1, LLM judge | `data/eval/`, `data/results/` | Hoàng Trung Anh |
| Observability | Great Expectations 1.x và freshness SLA | `data/quality/` | Hoàng Trung Anh |
| Corruption/repair | Sáu lỗi dữ liệu, repair từ raw snapshot | `corruption_log.json`, repaired artifacts | Nguyễn Chí Công |
| Orchestration | Điều phối baseline/corruption/repair và report | `data/reports/` | Vũ Đình Đăng |

## 4. Cấu hình và cách tái hiện

| Biến/cấu hình | Giá trị |
|---|---|
| `LLM_PROVIDER` | `openai` |
| `LLM_MODEL` | `gpt-4o-mini` |
| Embedding model | `text-embedding-3-small` |
| Số Crossref records | `24` |
| Retrieval `top_k` | `4` |
| Freshness threshold | `180` ngày |
| Test set | `10` câu hỏi dùng chung cho cả ba trạng thái |

Không đưa API key hoặc `.env` vào báo cáo/repository.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
python3 script/run_phase1.py
python3 script/run_corruption_flow.py
```

| Luồng | Trạng thái | Bằng chứng |
|---|---|---|
| Baseline | Thành công | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` |
| Corruption + repair | Thành công | `data/results/corruption_log.json`, `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

| Thuộc tính | Giá trị |
|---|---|
| Source | Crossref REST API hoặc offline snapshot |
| Query | `agentic retrieval augmented generation large language model` |
| Filter | `has-abstract:true`, cửa sổ freshness 180 ngày |
| Records | 24 |
| Retry/fallback | Retry request; fallback sang `data/raw/crossref_records.json` |

Clean schema chính gồm `paper_id`, `title`, `summary`, `authors`, `categories`, `published`, `age_days`, `text_for_embedding` và `source_url`. Bản ghi thiếu ID/title bị loại, duplicate ID được xử lý giữ bản ghi đầu tiên, text được normalize whitespace và ghép theo các section title/authors/categories/published/summary. Repair luôn đọc lại raw snapshot thay vì sửa trực tiếp corrupted CSV.

## 6. Evaluation setup

| Thành phần | Cấu hình |
|---|---|
| Số câu hỏi | 10 |
| Question types | summary, authors, published date, categories |
| Ground-truth document ID | DOI trong `data/eval/test_set.json` |
| Embedding | OpenAI `text-embedding-3-small` |
| Vector store | ChromaDB, baseline/corrupted/repaired collections |
| Retrieval `top_k` | 4 |
| LLM judge | OpenAI `gpt-4o-mini` |
| Test set | `data/eval/test_set.json` dùng chung |

Test set được cố định để mọi thay đổi metrics chỉ phản ánh trạng thái dữ liệu/index, không phản ánh sự thay đổi đề thi.

## 7. Artifact và baseline metrics

| Artifact | Trạng thái |
|---|---|
| Raw records | Có — `data/raw/crossref_records.json` |
| Clean dataset | Có — `data/clean/papers_clean.csv/json` |
| Embedding/index | Có — `data/embeddings/`, `data/chroma/` |
| Evaluation set | Có — `data/eval/test_set.json` |
| Quality/freshness | Có — `data/quality/` |
| Baseline report | Có — `data/reports/phase1_report.md` |

| Metric | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| Retrieval hit rate | 1.000 | 0.500 | 1.000 |
| Mean token F1 | 1.000 | 0.715 | 1.000 |
| Judge accuracy | 1.000 | 0.600 | 1.000 |
| Mean judge score | 5.000 | 3.700 | 5.000 |
| Quality gate | Pass | Fail | Pass |
| Freshness SLA | Pass | Pass | Pass |

Ragas không chạy mặc định; metrics file ghi rõ có thể bật bằng `RUN_RAGAS=1` nếu cần.

## 8. Corruption và repair

| Corruption | Record bị tác động | Signal |
|---|---:|---|
| Drop newest records | 4 | Giảm coverage/retrieval |
| Blank summary | 1 | Non-null/embedding text fail |
| Inject noise | 1 | Text validity/retrieval giảm |
| Truncate title | 1 | Title length fail |
| Stale date | 1 | Freshness cảnh báo |
| Duplicate rows | 2 | Unique `paper_id` fail |

Tổng cộng có 6 event, corrupted dataframe còn 22 dòng. Repair đọc lại 24 raw records, chạy lại cleaning, quality, freshness, embedding và evaluation. Vì nguồn repair là raw snapshot bất biến nên kết quả repaired tái lập được baseline.

## 9. Kết luận và giới hạn

1. Corruption làm thay đổi dữ liệu đầu vào, khiến quality gate Fail và retrieval hit rate giảm từ 1.000 xuống 0.500; điều này được thể hiện trong `corruption_log.json`, quality reports và corrupted metrics.
2. Repair từ raw snapshot khôi phục schema, quality gate, retrieval hit rate, token F1 và judge score về đúng baseline.
3. Pipeline hiện dùng OpenAI Embeddings theo key đã cấu hình; nếu giảng viên chấm bắt buộc `all-MiniLM-L6-v2`, nhóm cần đổi lại embedding implementation trước khi nộp.

Giới hạn còn lại là chưa bật Ragas pass mặc định và repository URL/MSSV email của thành viên thứ ba chưa cần ghi nếu không có thông tin bổ sung.

## 10. Checklist trước khi nộp

- [x] Đã điền ba thành viên, MSSV và phân công.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Metrics khớp với file trong `data/results/`.
- [x] Quality/freshness reports đã sinh.
- [x] Không đưa `.env` hoặc API key vào source/report.
- [x] Đã điền email commit/GitHub của Vũ Đình Đăng từ GitHub CLI.
- [ ] Commit và push code, artifacts và reports lên repository.
- [ ] Mỗi thành viên nộp link repository trên LMS.
