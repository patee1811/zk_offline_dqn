---
name: commit
description: >
  Stage and create a Conventional Commit. Use when the user asks to
  commit, or types /commit.
---

# /commit

1. `git status` + `git diff` + `git log -8 --oneline`. Đừng `git add -A`.
2. Loại khỏi stage: `.env*`, `proof.bin`, `artifacts/kaggle*`, `debug.log`, `.claude/settings.local.json`, `SESSION_NOTES.md`.
3. Tách commit nếu subject cần chữ “and”.
4. Subject: `type(scope): imperative` ≤72, English, không emoji. Scope thuộc danh sách trong `rules/40-git-va-commit.md`.
5. Chạy trước khi commit (phạm vi đụng):
   ```text
   python -m unittest <module>
   python scripts/experiments/check_paper_claims.py   # nếu đụng paper/docs/README
   ```
6. `git commit` để hook `validate_commit_msg.py` chạy. Không `--no-verify`.
7. Không push `master` trừ khi phiên này người dùng yêu cầu tường minh.
8. Không thêm `Co-authored-by` AI.
