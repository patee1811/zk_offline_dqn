---
paths:
  - ".claude/**"
  - "CLAUDE.md"
  - "AGENTS.md"
  - "commitlint.config.cjs"
  - "ruff.toml"
  - ".pre-commit-config.yaml"
---

# Bảo trì harness

Lý do: không có vòng duyệt thì rules phình và mâu thuẫn với repo.

## Thu nhận

Ba nguồn **chỉ** ghi vào `.claude/harness/INBOX.md` (append), không sửa rules:

1. Người sửa lại (“không, ở đây mình luôn…”, “đừng X”, “lần sau…”).
2. Phát hiện mới (lệnh thật, bẫy phải thử lại).
3. Thất bại lặp (hook chặn, CI, review).

Mẫu mục: ngày — nguồn — scope; Kích hoạt; Bài học; Đích đề xuất; Độ tin cậy; Trạng thái: chờ xử lý.

`capture_learning.py` chỉ đọc dòng `LEARNING:` trong `SESSION_NOTES.md` (gitignore).

## Hợp nhất — /harness-sync

Người chạy. Đọc INBOX + CHANGELOG. Bỏ mục một lần, bị phủ định, hoặc đã có rule. Gộp thành sửa nhỏ nhất.

Thang bậc: không thể sai cơ học → hook/permission/lint; theo path → `90-domain`; theo quy trình → skill; mọi lúc → CLAUDE.md (cuối cùng).

Trình diff, chờ duyệt. Được duyệt: áp dụng, CHANGELOG + ngày + kích hoạt, đánh dấu inbox, tăng `harnessVersion`. Cập nhật AGENTS.md nếu mục lục đổi.

## Cắt tỉa

Rule không đụng 90 ngày, hoặc mâu thuẫn code, đánh dấu xóa. Trần: CLAUDE.md ≤200, rule ≤120, SKILL.md ≤150. Trùng → siết rule cũ, không thêm.

Agent đề xuất. Người duyệt. Luôn luôn.
