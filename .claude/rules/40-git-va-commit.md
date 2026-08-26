---
paths:
  - "**"
---

# Git và commit

Lý do: lịch sử phase 1–10 dùng “Add X”; từ harness này ép Conventional để review/CI đọc được.

Định dạng: `<type>(<scope>): <subject>` — English, imperative, chữ thường, không chấm, ≤72.

Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert.

Scopes bắt buộc, đúng danh sách: `relations`, `verifiers`, `artifacts`, `backends`, `data`, `cli`, `experiments`, `paper`, `tests`, `docs`, `ci`, `harness`, `scripts`, `rl`, `proof`, `tamper`.

Phá vỡ tương thích: `!` + footer `BREAKING CHANGE:`.

Thân (72 cột): tại sao / đánh đổi. Fix kèm cách tái hiện. Perf kèm số đo.

Footer: `Refs: #n`, `Closes #n`. Không bắt ticket (repo dùng GitHub PR, không có Issues bắt buộc). Không thêm `Co-authored-by` AI — `includeCoAuthoredBy: false`.

## Kỷ luật

- Commit nguyên tử. “và” trong subject → tách.
- Không trộn refactor với feature.
- Không commit: secret, `.env`, `proof.bin`, `artifacts/kaggle*`, lockfile thừa, `debug.log`.
- Không `git push --force` trên `master`. Nhánh riêng: `--force-with-lease`.
- Không `git add -A`. Stage có chủ đích.
- Cổng: `.claude/hooks/validate_commit_msg.py` + `.pre-commit-config.yaml` (commit-msg). `commitlint.config.cjs` là bản gương Node tùy chọn.

## Nhánh

Lịch sử thật: `duy/phase-N-kebab`, `refactor/relation-architecture`, `cleanup-project-structure`. Harness mới: `<type>/<mo-ta-kebab>` (`chore/ai-harness`, `fix/merkle-odd-leaf`). Không commit thẳng `master` trừ khi người dùng yêu cầu tường minh trong phiên đó.

PR: tiêu đề Conventional; thân gồm thay đổi / vì sao / đã chạy gì / rủi ro / rollback.
