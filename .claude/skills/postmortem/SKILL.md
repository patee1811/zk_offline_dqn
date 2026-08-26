---
name: postmortem
description: >
  Write a short postmortem after a hook block, CI fail, or review miss.
  Use after a repeated failure or when the user types /postmortem.
---

# /postmortem

1. Sự kiện: lệnh, file, thông báo lỗi (stderr hook / CI / review).
2. Tác động: claim, schema, test, secret.
3. Nguyên nhân gần: thiếu rule, hook hổng, hay agent trôi.
4. Mục inbox đề xuất (append, không sửa rules):
   ```markdown
   ## YYYY-MM-DD — thất bại — scope <scope>
   **Kích hoạt:** …
   **Bài học:** …
   **Đích đề xuất:** …
   **Độ tin cậy:** cao|trung|thấp
   **Trạng thái:** chờ xử lý
   ```
5. Không tự /harness-sync. Người chạy sau.
