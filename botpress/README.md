# Botpress runtime payload: ANDY_RUNTIME_V1

Mình đã chuẩn hoá lại đoạn code bạn gửi để có thể chạy được như một Node.js worker (fix dấu nháy cong, template string, lỗi cú pháp, và kiểm tra pipeline không tồn tại).

## Cách dùng với Botpress

1. Vào Botpress Studio.
2. Tạo workflow hoặc action mới (kiểu **Execute Code** / custom integration service).
3. Dán toàn bộ nội dung từ `botpress/ANDY_RUNTIME_V1.js`.
4. Đảm bảo môi trường có các package:
   - `bull`
   - `ioredis`
5. Cấu hình Redis endpoint phù hợp production trước khi chạy.

## Lưu ý production

- Ngưỡng `ImpactScore` đang rất nghiêm ngặt (`< 0.9999` sẽ fail gần như luôn).
- Cần thay `Math.random()` bằng metric thật nếu muốn hệ thống ổn định.
