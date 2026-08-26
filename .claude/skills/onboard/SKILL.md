---
name: onboard
description: >
  Onboard a new contributor or agent to zk_offline_dqn. Use when someone
  asks how to set up, what to read first, or types /onboard.
---

# /onboard

1. Đọc [CLAUDE.md](../../../CLAUDE.md) rồi [docs/architecture.md](../../../docs/architecture.md) và [docs/claim_matrix.md](../../../docs/claim_matrix.md).
2. Cài từ root:
   ```text
   python -m venv .venv
   pip install -r requirements.lock || pip install -r requirements.txt
   pip install -e .
   pip install ruff pre-commit
   pre-commit install --hook-type pre-commit --hook-type commit-msg
   ```
   Windows: `$env:PYTHONPATH="."`. Make target: Git Bash/WSL.
3. Xác minh:
   ```text
   python -m compileall zk_offline_dqn scripts tests
   python -m unittest tests.unit.test_core_helpers
   python scripts/experiments/check_paper_claims.py
   python -m zk_offline_dqn.cli.main --help
   ```
4. Chỉ ra lớp: `relations/` (thuần) → `verifiers/` (I/O) → `cli/` / `scripts/`. SP1 ở `zk_backend/<rel>/sp1/`.
5. Nhắc bất biến: `FP_SCALE=1000`, Merkle duplicate lá lẻ, cấm nới paper claim, không commit `proof.bin`.
6. Không chạy `RUN_HEAVY_*` hay `cargo --prove` trong onboard.
