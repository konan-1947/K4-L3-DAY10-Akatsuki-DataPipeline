# Báo cáo cá nhân — Nguyễn Chí Công

## Thông tin

| Trường | Giá trị |
|---|---|
| Họ và tên | Nguyễn Chí Công |
| MSSV | `2A202602634` |
| Email | `nguyenchicong1141@gmail.com` |
| GitHub | `NCCong1411` |
| Khóa/lớp | `K4-L3-DAY10` |
| Vai trò | Data foundation và recovery |

## Phạm vi phụ trách

- `src/ingestion/crossref.py`: parse Crossref, làm sạch abstract và fallback về snapshot offline.
- `src/ingestion/cleaning.py`: chuẩn hóa schema, deduplicate, tính `age_days` và tạo `text_for_embedding`.
- `src/ingestion/corruption.py`: mô phỏng sáu dạng lỗi và ghi `corruption_log.json`.
- Xác minh repair luôn bắt đầu từ `data/raw/crossref_records.json`.

## Kết quả bàn giao

- Chuẩn hóa được 24 paper records thành clean CSV/JSON.
- Corruption log ghi đủ 6 event: drop, blank summary, noise, truncate title, stale date và duplicate rows.
- Corrupted dataset còn 22 rows và quality gate chuyển sang Fail.
- Repair tái tạo lại 24 records từ raw snapshot, khôi phục quality gate và metrics về baseline.

## Cách xác minh

Kiểm tra `data/clean/papers_clean*.json`, `data/results/corruption_log.json`, `data/quality/*quality_report.json` và `data/quality/*freshness_report.json`.

## Điều học được

Hiểu data lineage, vai trò của raw immutable snapshot và vì sao repair an toàn phải tái dựng dữ liệu từ nguồn đáng tin cậy thay vì vá trực tiếp corrupted output.
