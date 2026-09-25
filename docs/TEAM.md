# Danh sách thành viên và phân công nhóm

- **Tên nhóm:** Akatsuki
- **Mã nhóm / lớp:** `K4-L3-DAY10`
- **Repository:** <https://github.com/konan-1947/K4-L3-DAY10-Akatsuki-DataPipeline>

## Thành viên

| STT | Họ và tên | MSSV | Email | GitHub | Phần việc chính | Báo cáo cá nhân |
|---:|---|---|---|---|---|---|
| 1 | Vũ Đình Đăng | `2A202602946` | `konan-1947@users.noreply.github.com` | `konan-1947` | Pipeline integration, cấu hình và báo cáo tổng hợp | [`report/2A202602946_VuDinhDang.md`](../report/2A202602946_VuDinhDang.md) |
| 2 | Nguyễn Chí Công | `2A202602634` | `nguyenchicong1141@gmail.com` | `NCCong1411` | Ingestion, cleaning, corruption và repair dữ liệu | [`report/2A202602634_NguyenChiCong.md`](../report/2A202602634_NguyenChiCong.md) |
| 3 | Hoàng Trung Anh | `2A202602521` | `ht.anh00411@gmail.com` | `trungKoiKa` | Retrieval, embedding, evaluation và observability | [`report/2A202602521_HoangTrungAnh.md`](../report/2A202602521_HoangTrungAnh.md) |

## Phân công chi tiết

### Vũ Đình Đăng — Pipeline integration

- Quản lý `src/core/config.py`, `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py`.
- Kiểm tra thứ tự chạy end-to-end, đường dẫn artifacts và khả năng tái lập pipeline.
- Tổng hợp kết quả baseline, corrupted và repaired vào báo cáo nhóm.

### Nguyễn Chí Công — Data foundation và recovery

- Quản lý `src/ingestion/crossref.py`, `cleaning.py` và `corruption.py`.
- Chuẩn hóa schema, tạo `text_for_embedding`, xử lý deduplication và freshness.
- Xây dựng corruption log và cơ chế repair từ raw snapshot bất biến.

### Hoàng Trung Anh — RAG, evaluation và observability

- Quản lý `src/retrieval/embeddings.py`, ChromaDB index và luồng QA.
- Xây dựng test set, metrics đánh giá và LLM judge.
- Thiết lập Great Expectations, freshness report và các artifact báo cáo.

## Quy ước chung

- Cả ba thành viên cùng chạy và hiểu được toàn bộ pipeline end-to-end.
- Không commit `.env`, API key hoặc token vào repository.
- Các artifact cần đối chiếu gồm baseline, corrupted và repaired với cùng một test set.
