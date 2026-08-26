---
name: harness-sync
description: >
  Merge approved learnings from the harness inbox into rules. Use when
  the user types /harness-sync or asks to update the AI harness.
---

# /harness-sync

1. Đọc `.claude/harness/INBOX.md` và `CHANGELOG.md`.
2. Bỏ mục một lần, bị phủ định, hoặc đã được rule hiện có phủ.
3. Gộp phần còn lại thành sửa nhỏ nhất. Ưu tiên sửa một dòng cũ hơn thêm file.
4. Chọn nơi đặt (rules/60): hook > domain rule > skill > CLAUDE.md.
5. Kiểm trần: CLAUDE.md ≤200, rule ≤120, SKILL.md ≤150. Cập nhật AGENTS.md nếu mục lục đổi.
6. **Trình diff, dừng.** Không ghi rules/CLAUDE.md khi chưa được duyệt.
7. Sau duyệt: áp dụng, đánh dấu inbox `đã áp dụng`, thêm CHANGELOG (ngày, kích hoạt, lý do), tăng `harnessVersion` trong `harness.lock.json`.
