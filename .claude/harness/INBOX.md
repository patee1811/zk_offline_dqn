# Harness inbox

Append-only. `/harness-sync` merges approved items. Do not edit rules from here.

Format:

```markdown
## YYYY-MM-DD — người sửa|phát hiện mới|thất bại — scope <scope>
**Kích hoạt:** …
**Bài học:** …
**Đích đề xuất:** …
**Độ tin cậy:** cao|trung|thấp
**Trạng thái:** chờ xử lý
```

## 2026-08-26 — thất bại — scope harness
**Kích hoạt:** R1 chỉ đổi 7 dòng import, nhưng `ruff format` (PostToolUse hook và pre-commit) reflow cả file thành diff 119 dòng. Phải `git checkout` hoàn tác hai lần.
**Bài học:** formatter chạy trên cả file mâu thuẫn với rule "diff chỉ chứa đúng thứ thay đổi cần" khi cây chưa từng được format. Đã gỡ `ruff format` khỏi cả hai hook, giữ `ruff check --fix`.
**Đích đề xuất:** đã áp dụng vào `.pre-commit-config.yaml`, `format_after_edit.py`, `ruff.toml`. Cân nhắc: format cả cây trong một commit riêng rồi bật lại?
**Độ tin cậy:** cao (quan sát trực tiếp hai lần)
**Trạng thái:** chờ xử lý
