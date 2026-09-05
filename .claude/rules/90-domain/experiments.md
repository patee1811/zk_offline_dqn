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
- Recursion: **bộ nhớ phẳng, cycles tuyến tính**. Bộ nhớ không phụ thuộc khối lượng, trên cả CPU lẫn GPU — RSS 30399MB (T=8) vs 29255MB (T=32); VRAM 18437MB ở T=16/32/64, 18750MB ở cây sâu 4, và cả biến thể child Groth16 6.16B cycles; chi phí là dựng mạch, giảm target không lách được trần. Cycles thì ngược lại: ≈ **154M mỗi proof con verify trong guest** (309,4M / 615,5M / 1230,4M ở 2 / 4 / 8 con; phần gộp riêng dưới 1%), giữ nguyên cả khi proof con **chính là proof đệ quy** (cây T=128 sâu 4: 309,95M cho 2 con). Cây N lá arity a có a(N−1)/(a−1) lượt verify, nên ước được chi phí trên giấy trước khi thuê GPU. Child Groth16 đắt 20× cycles nhưng witness nhỏ 388× (13 KB vs 5.1 MB).
- Provenance recursion phải sinh qua script phase (`run_phase7 ... --run-prove`), **không** gọi host trực tiếp: chỉ script phase chạy vòng quét tamper, và thiếu `tamper_report.json` thì test fixture fail. `--out-dir` phải **tuyệt đối** — cargo chạy host từ workspace của nó nên đường tương đối rơi vào `zk_backend/<rel>/sp1/artifacts/...`.
- Máy thuê chạy prove phải là **on-demand**, không spot. Một lần chạy spot 14 giờ bị AWS thu hồi, mất toàn bộ kết quả. Chênh lệch ~$1.2 cho 3 giờ.
- Kết quả phải rời khỏi máy trước khi máy chết: `scp` về hoặc đẩy S3 **sau mỗi case**, không đợi hết. Terminate chỉ sau khi đã kiểm tarball có trên đĩa.
- Đối chứng phải chạy ở **đúng cấu hình của số đã in**, và quét tham số phải phủ **cả hai** nhánh. Quét learning rate chỉ cho SGD cho ra "SGD thắng Adam"; quét cả hai thì 12–12, và Adam cũng bị chính mặc định 3e-4 làm hại (0,402 so với 0,615 ở 1e-2). Chọn tham số: chuẩn hoá min-max **trong từng ô** rồi lấy trung bình — trung bình thô để LunarLander (−1400…200) lấn CartPole (0…500), còn đếm ô thắng thì bỏ qua biên độ (0,5 dẫn 6 ô thắng nhưng sụp ở cartpole-random). `run_table1_controls.py`, cổng `RUN_HEAVY_BENCHMARKS`.
- `Makefile` dùng Unix (`mkdir -p`). Trên Windows: Git Bash/WSL, không PowerShell thuần cho target reproduce.
