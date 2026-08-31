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
- Đo bộ nhớ trên Kaggle: build **mọi** host trước khi đo. Lần chạy 1 chỉ warm `short-trace-host`, nên biên dịch `merkle_membership` lọt vào cửa sổ đo và 9915MB rơi vào `setup` thay vì `prove`.
- Bộ nhớ recursion **không phụ thuộc khối lượng**, trên cả CPU lẫn GPU: RSS 30399MB (T=8) vs 29255MB (T=32); VRAM 18437MB ở T=16, T=32, T=64 và cả biến thể child Groth16 6.16B cycles. Chi phí là dựng mạch, không phải gộp proof con. Giảm target không lách được trần.
- Provenance recursion phải sinh qua script phase (`run_phase7 ... --run-prove`), **không** gọi host trực tiếp: chỉ script phase chạy vòng quét tamper, và thiếu `tamper_report.json` thì test fixture fail. `--out-dir` phải **tuyệt đối** — cargo chạy host từ workspace của nó nên đường tương đối rơi vào `zk_backend/<rel>/sp1/artifacts/...`.
- Máy thuê chạy prove phải là **on-demand**, không spot. Một lần chạy spot 14 giờ bị AWS thu hồi, mất toàn bộ kết quả. Chênh lệch ~$1.2 cho 3 giờ.
- Kết quả phải rời khỏi máy trước khi máy chết: `scp` về hoặc đẩy S3 **sau mỗi case**, không đợi hết. Terminate chỉ sau khi đã kiểm tarball có trên đĩa.
- `Makefile` dùng Unix (`mkdir -p`). Trên Windows: Git Bash/WSL, không PowerShell thuần cho target reproduce.
