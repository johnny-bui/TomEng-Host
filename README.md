# TomEng Host

TomEng Host là sổ tay luyện phản xạ tiếng Anh cho vận hành căn hộ dịch vụ: đặt phòng, đón khách, dọn phòng, bảo trì, xử lý phàn nàn, thanh toán, an toàn, bàn giao ca và nhắn tin.

## Catalog

- 1.200 ID từ `p001` đến `p1200`; 625 câu Everyday/Reflex được giữ nguyên nội dung tiếng Anh, tiếng Việt, ngữ cảnh và câu nối tiếp theo ID. 575 ID còn lại được dùng cho tiếng Anh lưu trú và vận hành căn hộ.
- 12 danh mục, 56 nhóm nhỏ và 258 tình huống học 5 câu. 115 tình huống Host bao phủ đủ 575 câu Host; các tình huống Everyday/Reflex được giữ từ catalog chung.
- Câu Host dùng hội thoại ngắn theo vai khách hoặc nội bộ. Bản dịch tiếng Việt và mẹo nhớ đi kèm từng cụm; QA cấu trúc không thay thế biên tập viên bản ngữ.
- Mỗi phiên giữ quy trình Review (nếu có) → Learn 5 → Recall 5 → nhiệm vụ tình huống. NEW được tính theo ID chưa giới thiệu; dữ liệu ôn và tiến độ được lưu cục bộ.

## Tách biệt với TomEng gốc

TomEng Host là repository và PWA riêng. Store dùng các khóa `tomeng_host_*`, backup yêu cầu `app: TomEngHost` và `contentVersion: host-v1.0.0`. App từ chối backup TomEng gốc hoặc app khác. Service worker chỉ tạo/xóa cache `tomenghost-*`, có scope riêng ở `/TomEng-Host/`; không xóa cache của `/TomEng/`.

Không có tài khoản hoặc đồng bộ đám mây. Tiến độ ở thiết bị hiện tại; hãy tải backup JSON định kỳ. Repo và nội dung là public do GitHub Pages public, vì vậy không nhập dữ liệu nhận dạng khách hoặc thông tin bí mật.

## Chạy và kiểm tra

Mở `index.html` để dùng giao diện. Service worker/PWA cần HTTP(S); CI kiểm tra syntax, learning flow, lưu trữ, backup/import, catalog, liên kết hội thoại và cache isolation.

```bash
node --check app.js && node --check sw.js
node tests/engine.test.cjs
node tests/pwa.test.cjs
python3 tests/content.test.py
```

Tạo lại file runtime và catalog từ common-core cùng nội dung Host:

```bash
python3 content/host/build_host_content.py
```

Chi tiết bằng chứng và giới hạn nằm trong [FINAL_QA_REPORT.md](FINAL_QA_REPORT.md). Bản xem trước tình huống đầu tiên ở [PREVIEW_14_DAYS.md](content/host/PREVIEW_14_DAYS.md).
