# Báo cáo cá nhân — Hoàng Trung Anh

## Thông tin

| Trường | Giá trị |
|---|---|
| Họ và tên | Hoàng Trung Anh |
| MSSV | `2A202602521` |
| Email | `ht.anh00411@gmail.com` |
| GitHub | `trungKoiKa` |
| Khóa/lớp | `K4-L3-DAY10` |
| Vai trò | RAG, evaluation và observability |

## Phạm vi phụ trách

- `src/retrieval/embeddings.py`: kết nối OpenAI `text-embedding-3-small`.
- ChromaDB index và các collection baseline/corrupted/repaired.
- `src/evaluation/testset.py`: tạo test set cố định 10 câu hỏi.
- `src/observability/quality.py` và `reporting.py`: quality gate, freshness và Markdown reports.

## Kết quả bàn giao

- Embedding/index được tạo cho 24 tài liệu baseline và các trạng thái corrupted/repaired.
- Test set dùng chung cho cả ba trạng thái, giúp so sánh công bằng.
- Baseline đạt retrieval hit rate `1.000`, token F1 `1.000`, judge score `5.000`.
- Repaired state khôi phục các chỉ số về đúng baseline; corrupted quality gate được phát hiện là Fail.

## Cách xác minh

Kiểm tra `data/eval/test_set.json`, `data/embeddings/`, `data/chroma/`, `data/results/*_metrics.json` và `data/reports/corruption_report.md`.

## Điều học được

Hiểu mối liên hệ giữa embedding/index, retrieval metrics và data observability; một lỗi dữ liệu nhỏ có thể làm giảm chất lượng truy hồi dù pipeline vẫn chạy không báo exception.
