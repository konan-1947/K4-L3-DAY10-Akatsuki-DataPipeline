# Báo cáo cá nhân — Vũ Đình Đăng

## Thông tin

| Trường | Giá trị |
|---|---|
| Họ và tên | Vũ Đình Đăng |
| MSSV | `2A202602946` |
| Email commit | `konan-1947@users.noreply.github.com` |
| GitHub | [`konan-1947`](https://github.com/konan-1947) |
| Khóa/lớp | `K4-L3-DAY10` |
| Vai trò | Pipeline integration và report tổng hợp |
| Repository | `K4-L3-DAY10-Akatsuki-DataPipeline` |

## Phạm vi phụ trách

- `src/core/config.py`: cấu hình model, API provider, đường dẫn artifacts và freshness threshold.
- `src/pipelines/phase1.py`: điều phối baseline từ raw data đến quality, index, evaluation và report.
- `src/pipelines/corruption_flow.py`: điều phối corruption, re-index, repair và so sánh ba trạng thái.
- Kiểm tra tính nhất quán của metrics, reports và các đường dẫn output.

## Kết quả bàn giao

- Baseline chạy thành công với 24 records và 10 câu hỏi đánh giá.
- Corruption flow sinh đủ baseline/corrupted/repaired artifacts.
- Báo cáo so sánh thể hiện hit rate `1.000 -> 0.500 -> 1.000`.
- Đã kiểm tra compile và `git diff --check` không có lỗi.

## Cách xác minh

```bash
python3 script/run_phase1.py
python3 script/run_corruption_flow.py
```

Các bằng chứng chính: `data/results/*_metrics.json`, `data/reports/phase1_report.md` và `data/reports/corruption_report.md`.

## Điều học được

Hiểu cách thiết kế pipeline idempotent, tách raw snapshot khỏi dữ liệu biến đổi và dùng artifacts để kiểm chứng từng trạng thái thay vì chỉ kiểm tra output cuối cùng.
