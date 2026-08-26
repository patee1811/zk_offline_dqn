# AGENTS.md

Bản gương mỏng của [CLAUDE.md](CLAUDE.md). Đọc file đó trước. Quy ước chi tiết: `.claude/rules/`.

## Project

Relation-level verification Offline-DQN + SP1 trên vector canonical. Không phải proof full training.

## Lệnh (từ root, `PYTHONPATH=.`)

```text
pip install -r requirements.lock || pip install -r requirements.txt
pip install -e .
python -m compileall zk_offline_dqn scripts tests          # ~0.1s
python -m unittest discover tests                          # ~38s
python -m unittest tests.unit.test_core_helpers            # ~0.1s
python scripts/experiments/run_full_regression.py          # cần fixture CI
python scripts/experiments/check_paper_claims.py           # ~0.1s
python -m zk_offline_dqn.cli.main --help                   # ~1.4s
make reproduce-small                                       # TODO(human): đo thật
```

Không có lint/format/typecheck sẵn có. Harness dùng `ruff` trên file vừa sửa. SP1 prove không thuộc regression mặc định.

## Quy ước

| File | Khi nào |
| --- | --- |
| `.claude/rules/00-nguyen-tac-coi-loi.md` | mọi thay đổi |
| `.claude/rules/10-phong-cach-code.md` | Python/Rust |
| `.claude/rules/20-comment-va-tai-lieu.md` | comment/docstring |
| `.claude/rules/30-kiem-thu.md` | tests/ |
| `.claude/rules/40-git-va-commit.md` | commit/nhánh |
| `.claude/rules/50-bao-mat-va-secret.md` | secret, fixture, claim |
| `.claude/rules/60-bao-tri-harness.md` | sửa harness |
| `.claude/rules/90-domain/*.md` | theo `paths:` |

## Hoàn thành

Test xanh, không nới paper claim, không đổi schema/`FP_*` lén, Conventional Commit, không commit `proof.bin` / kaggle outputs.

## Hỏi người trước

`paper/`, schema, test vectors, `artifacts/reports/final_ndss/`, `zk_specs` constants, dependency mới, SP1 relation mới.
