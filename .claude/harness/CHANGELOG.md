# Harness changelog

## 2026-08-26 — 1.1.0

**Kích hoạt:** phiên đầu tiên dùng harness thật (R1 refactor + merge phase-10) làm lộ bốn chỗ cổng chặn bắt nhầm.

**Lý do:** cổng chặn thứ hợp lệ thì người dùng học cách bypass, và thói quen đó phá chính thứ cổng bảo vệ.

**Đã sửa:**

- `validate_commit_msg.py`: cho qua subject `Merge ` / `Revert ` — git tự sinh, không thể là Conventional Commit.
- `validate_commit_msg.py`: bỏ payload `-m` trước khi tìm cờ bypass — message *nhắc tới* cờ không phải là dùng nó.
- `guard_protected_paths.py`: cho qua scratchpad và `/tmp` — vùng tạm hợp lệ, không phải ghi ngoài repo.
- `tests/regression/test_report_generation.py` + `rules/30-kiem-thu.md`: `skipTest` khi thiếu output của `run_full_regression.py`. Đây là bug có sẵn của repo, harness chỉ làm lộ ra: clone sạch fail 2 test.

**Đã gỡ trước đó (cùng ngày, trước khi đánh version):** `ruff format` khỏi PostToolUse hook và pre-commit — nó reflow cả file, biến 7 dòng đổi import thành 119 dòng diff.

**Còn ngỏ:** format cả cây trong một commit riêng rồi bật lại `ruff format`? Hoãn tới khi paper qua review — lúc này mọi diff lớn đều buộc reviewer đọc lại.

## 2026-08-26 — 1.0.0

**Kích hoạt:** bootstrap harness trên `origin/master` (f3ca555, PR #27).

**Lý do:** repo chưa có `.claude/`, linter, hay git hook. Paper claim và lớp relation/verifier cần cổng chặn, không chỉ lời khuyên.

**Đã thêm:** CLAUDE.md, AGENTS.md, rules, skills, agents, Python hooks, ruff (hẹp), commitlint gương, pre-commit.
