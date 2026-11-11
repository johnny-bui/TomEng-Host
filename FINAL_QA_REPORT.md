# TomEng Host — Báo cáo QA / release

## Trạng thái hiện tại

- Ứng dụng: `TomEng Host` · app `1.0.0` · catalog `host-v1.0.0` · schema dữ liệu `7`.
- Repository độc lập: [johnny-bui/TomEng-Host](https://github.com/johnny-bui/TomEng-Host).
- Pages URL dự kiến: `https://johnny-bui.github.io/TomEng-Host/`.
- Phạm vi: dùng lại engine TomEng ổn định; thêm catalog Host độc lập; không thay đổi TomEng gốc hoặc deployment `/TomEng/`.

## Kết quả kiểm tra

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Bao phủ catalog | **PASS** | 1.200 ID duy nhất `p001`–`p1200`; 625 Everyday/Reflex giữ nguyên `id`, `en`, `vi`, `context`, `follow`; 575 ID Host. |
| Danh mục và scenario | **PASS** | 12 danh mục, 56 nhóm nhỏ, 258 bài; 115 scenario Host × 5 cụm bao phủ đủ 575 ID Host. |
| Mạch 5 câu Host | **PASS** | Các câu nối tiếp từng lượt, có role, ngữ cảnh, mục tiêu, nhiệm vụ áp dụng; QA xác nhận follow-up khớp câu kế tiếp. |
| Learning flow | **PASS** | Regression: Learn 5 → Recall 5 → Apply → lưu → tạo phiên ngày kế tiếp và ôn đúng 5 ID của phiên thật trước. |
| Tách dữ liệu cùng origin | **PASS** | Test nạp sẵn `tomeng_native_v3` và `tomeng_data_v2`; Host chỉ ghi `tomeng_host_*`, giá trị TomEng gốc không đổi. |
| Backup / restore | **PASS** | Export gắn `TomEngHost`; Host từ chối backup gắn `TomEng`; Host backup phiên bản cũ cùng schema có thể khôi phục theo ID ổn định. |
| Migration catalog | **PASS** | Migration Host v0.9 → v1.0 tạo snapshot trước khi ghi; regression xác nhận nếu snapshot không ghi được thì store cũ không bị thay thế. |
| PWA và offline shell | **PASS** | Test service worker, shell fallback offline và scope/cache riêng `tomenghost-*`; cache `tomeng-v15-native` được giữ. |
| App gốc sau thay đổi | **NOT TESTED** | Repo Host tách biệt và chưa triển khai; smoke check TomEng `/TomEng/` sẽ được ghi sau khi Host Pages deploy. |
| Responsive browser | **NOT TESTED** | Chưa kiểm tra browser thật tại 360 / 768 / 1440px. |
| Thiết bị thật | **NOT TESTED** | Chưa thử Chrome Android và Safari iPhone; cần owner kiểm tra TTS, micro và cài PWA trên thiết bị. |
| Biên tập toàn bộ tiếng Anh và tiếng Việt | **NOT TESTED** | QA tự động kiểm tra cấu trúc, placeholder, câu nối và một số mẫu lỗi. 575 câu Host chưa được native editor duyệt; không gắn nhãn native-approved. |

## Lệnh đã chạy

```text
python3 content/host/build_host_content.py — PASS (1.200 phrases / 258 scenarios / 12 categories)
python3 tests/content.test.py — PASS
node --check app.js && node --check sw.js — PASS
node tests/engine.test.cjs — PASS
node tests/pwa.test.cjs — PASS
git diff --check — PASS
```

## Rủi ro còn lại

- Tiến độ lưu cục bộ trong browser/device; không đồng bộ giữa thiết bị. Tải backup định kỳ.
- GitHub Pages và repository public; không lưu thông tin nhận dạng khách, mã cửa thật, hoặc dữ liệu bí mật.
- Tính tự nhiên của 575 câu mới cần biên tập dần theo cách người dùng thực tế giao tiếp. Các đoạn hội thoại là gợi ý thực hành, cần thay số phòng, giá, lịch, quy trình và quy định theo thực tế trước khi dùng với khách.
- TTS và speech recognition phụ thuộc browser, quyền micro và giọng đọc có trên thiết bị. Speech-to-text không chấm phát âm.

## Release record

| Mốc | Trạng thái | Evidence |
|---|---|---|
| Local verification | **PASS** | Các lệnh trên. |
| GitHub Actions quality | **NOT TESTED** | Chạy sau lần push đầu tiên. |
| GitHub Pages deployment | **NOT TESTED** | Chạy sau CI trên `main`. |
| Production smoke | **NOT TESTED** | Kiểm tra URL, asset, manifest, learning UI và offline sau deploy. |
| TomEng gốc không đổi | **NOT TESTED** | Xác minh `/TomEng/` vẫn HTTP 200 và tiếp tục phục vụ worker v15 sau Host release. |
