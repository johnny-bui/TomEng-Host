# TomEng Host — Báo cáo QA / release

## Trạng thái hiện tại

- Ứng dụng: `TomEng Host` · app `1.0.0` · catalog `host-v1.0.0` · schema dữ liệu `7`.
- Repository độc lập: [johnny-bui/TomEng-Host](https://github.com/johnny-bui/TomEng-Host).
- Production: [https://johnny-bui.github.io/TomEng-Host/](https://johnny-bui.github.io/TomEng-Host/).
- Phạm vi: tái sử dụng learning engine TomEng, triển khai catalog Host trong repo và đường dẫn Pages riêng; không thay đổi source/deployment TomEng gốc `/TomEng/`.
- Kiểm tra production gần nhất: 2026-11-11.

## Kết quả kiểm tra

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Bao phủ catalog | **PASS** | 1.200 ID duy nhất `p001`–`p1200`; 625 Everyday/Reflex giữ nguyên `id`, `en`, `vi`, `context`, `follow`; 575 ID Host. |
| Danh mục và scenario | **PASS** | 12 danh mục, 56 nhóm nhỏ, 258 bài; 115 scenario Host × 5 cụm bao phủ đủ 575 ID Host. |
| Mạch 5 câu Host | **PASS** | QA cấu trúc kiểm tra từng lượt, role, ngữ cảnh, mục tiêu, nhiệm vụ áp dụng và follow-up. |
| Learning flow và tiến độ | **PASS** | Regression: Learn 5 → Recall 5 → Apply → lưu → phiên kế tiếp ôn đúng 5 ID của phiên thực tế; tiếp tục sau refresh; ID cũ không bị tính thành câu mới. |
| Bảo vệ tiến độ TomEng gốc | **PASS** | Host ghi vào namespace `tomeng_host_*`; regression nạp sẵn key TomEng cũ và xác nhận giá trị không đổi. Cả hai Pages dùng cùng web origin nên localStorage là cùng vùng origin, nhưng namespace riêng và kiểm thử xác nhận không ghi đè các key gốc. |
| Backup / restore | **PASS** | Export gắn `TomEngHost`; Host từ chối backup gắn `TomEng`; backup Host cũ khôi phục theo ID ổn định. |
| Migration catalog | **PASS** | Host v0.9 → v1.0 tạo backup trước khi ghi; nếu backup thất bại, regression xác nhận dữ liệu cũ không bị thay thế. |
| PWA identity và cache | **PASS** | Manifest/scope riêng cho `/TomEng-Host/`; worker chỉ xóa cache `tomenghost-*`, giữ `tomeng-v15-native`. Automated PWA test xác nhận offline navigation shell fallback. |
| Responsive browser — 1440px | **PASS** | Browser production: viewport/document 1440px; app 1384px, 12 thẻ danh mục; không tràn ngang. |
| Responsive browser — 768px | **PASS** | Browser production: document 768px, app 738px, nội dung 640px; panel phụ ẩn; lưới danh mục chuyển sang 2 cột; không tràn ngang. |
| Responsive browser — 360px | **PASS** | Browser production: document/body/app đều 360px; rail desktop ẩn, bottom navigation hiện, panel phụ ẩn, input tìm kiếm 16px; không tràn ngang. Mở được trang học “Tìm studio theo tuần”. |
| Console trên production browser | **PASS** | Không có console error trong lượt kiểm tra live; trang scenario mở được. |
| GitHub Actions quality | **PASS** | [Run 43021797570](https://github.com/johnny-bui/TomEng-Host/actions/runs/43021797570), commit `c7ba5d5`; verify, content QA, engine, PWA và consistency checks đều xanh. |
| GitHub Pages deployment | **PASS** | [Run 43021797570](https://github.com/johnny-bui/TomEng-Host/actions/runs/43021797570); workflow deploy hoàn tất trên `main`. |
| Production HTTP smoke | **PASS** | Host URL, `app.js`, `manifest.webmanifest`, hai icon, `sw.js`, `data.js` trả HTTP 200; data tải được 1.200 phrase ID. |
| TomEng gốc sau triển khai Host | **PASS** | `https://johnny-bui.github.io/TomEng/` vẫn trả HTTP 200; xác nhận Host được đặt trong repo và đường dẫn Pages riêng. |
| Offline thật sau khi ngắt mạng | **NOT TESTED** | Service-worker fallback được kiểm tra bằng automated test; chưa ngắt mạng thiết bị/browser sau khi cài để xác nhận cả chu trình offline thực. |
| Thiết bị thật | **NOT TESTED** | Chưa thử Chrome Android và Safari iPhone; micro, TTS, cài PWA và hành vi nền phụ thuộc thiết bị cần owner thử. |
| Biên tập toàn bộ tiếng Anh và tiếng Việt | **NOT TESTED** | Tự động kiểm tra cấu trúc, placeholder, liên kết câu và một số mẫu lỗi; 575 câu Host mới chưa được native editor duyệt, không gắn nhãn native-approved. |

## Kiểm thử tự động đã chạy

```text
python3 content/host/build_host_content.py — PASS (1.200 phrases / 258 scenarios / 12 categories)
python3 tests/content.test.py — PASS
node --check app.js && node --check sw.js — PASS
node tests/engine.test.cjs — PASS
node tests/pwa.test.cjs — PASS
git diff --check — PASS
```

## Lỗi phát hiện

- Không phát hiện lỗi P0/P1 trong content/engine/PWA regression hoặc lượt kiểm tra giao diện production nói trên.
- Không lưu ảnh chụp thành file trong repository; các kích thước viewport và kết quả DOM/console được ghi làm bằng chứng. Ảnh live browser đã được xem trong phiên QA.

## Rủi ro còn lại

- Tiến độ lưu cục bộ theo browser/device, không đồng bộ giữa thiết bị. Tải backup định kỳ.
- GitHub Pages và repository public; không lưu thông tin nhận dạng khách, mã cửa thật hoặc dữ liệu bí mật.
- Tính tự nhiên của 575 câu mới cần biên tập dần từ phản hồi thực tế. Các đoạn hội thoại là gợi ý luyện tập; thay giá, thời gian, số phòng, quy trình và quy định theo nơi lưu trú trước khi dùng với khách.
- TTS và speech recognition phụ thuộc browser, quyền micro và giọng đọc có trên thiết bị. Speech-to-text không chấm phát âm.
- Kiểm tra viewport bằng browser automation xác nhận bố cục web responsive, nhưng không thay thế kiểm thử thiết bị Android/iPhone thật.

## Release record

| Mốc | Trạng thái | Evidence |
|---|---|---|
| Local verification | **PASS** | Các lệnh kiểm thử tự động ở trên. |
| GitHub Actions quality | **PASS** | [Run 43021797570](https://github.com/johnny-bui/TomEng-Host/actions/runs/43021797570). |
| GitHub Pages deployment | **PASS** | [Run 43021797570](https://github.com/johnny-bui/TomEng-Host/actions/runs/43021797570). |
| Host production smoke + browser | **PASS** | URL production HTTP 200; catalog 1.200; viewport 360/768/1440; scenario mở được, 0 console errors. |
| TomEng gốc không bị thay thế | **PASS** | `/TomEng/` HTTP 200; source và workflow ở repo riêng. |
