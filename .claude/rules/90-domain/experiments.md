---
paths:
  - "scripts/experiments/**"
  - "zk_offline_dqn/experiments/**"
  - "zk_offline_dqn/rl_benchmarks/**"
  - "zk_offline_dqn/proof_benchmarks/**"
  - "zk_offline_dqn/tamper_benchmarks/**"
---

# Vùng experiments

Lý do: script nặng lẫn với checker sẽ làm reviewer tưởng đã prove lại.

- Checker (`check_*.py`) phải chạy nhanh, không prove, không train.
- Runner nặng (`run_phase8_*`, `run_phase4_*_validation.py`) cổng `RUN_HEAVY_SP1`, `RUN_HEAVY_BENCHMARKS`, `RUN_HEAVY_TAMPER`. Mặc định không bật.
- `run_full_regression.py` = 15 check Python, cần fixture CI. SP1 prove không nằm trong đó.
- Report builders trong `zk_offline_dqn/experiments/` chỉ đọc snapshot. Output mặc định `artifacts/reports/final_ndss/`.
- Kaggle outputs gitignore. Không commit kernel output.
- `Makefile` dùng Unix (`mkdir -p`). Trên Windows: Git Bash/WSL, không PowerShell thuần cho target reproduce.
