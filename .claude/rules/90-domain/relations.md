---
paths:
  - "zk_offline_dqn/relations/**"
  - "zk_offline_dqn/zk_specs.py"
  - "zk_offline_dqn/merkle.py"
---

# Vùng relations

Lý do: semantics mới lọt vào CLI/scripts sẽ làm paper và SP1 lệch nhau.

- Chỉ oracle thuần: nhận mapping/artifact đã load, trả dataclass hoặc dict kết quả. Cấm argparse, `Path.open`, `subprocess`, biến môi trường quyết định semantics.
- Số học: `FP_SCALE=1000`, `GAMMA_FP=990`, `(a * b) // fp_scale`. `encode_fp` dùng `round` khi vào fixed-point; nhân/chia trong mạch dùng `//`. SmoothL1 beta 1.0 = `SMOOTH_L1_BETA_FP=1000`.
- Merkle: leaf `",".join(str(int(x)))` rồi SHA256 hex; node `SHA256(bytes.fromhex(L)+bytes.fromhex(R))`; lá lẻ **duplicate** (Bitcoin-style) trong `build_next_level`.
- Import Merkle/TD thẳng từ `zk_offline_dqn.merkle` và `zk_offline_dqn.zk_specs`. Wrapper `core/` đã bị xóa; đừng dựng lại lớp re-export.
- Không thêm relation SP1 mới từ đây. Python oracle có thể tồn tại khi chưa có backend; đừng viết claim “proved in SP1”.
- Aggregation: `AGGREGATION_MODE = "proof_manifest_chain"`. Không gọi đó là true recursive aggregation.
