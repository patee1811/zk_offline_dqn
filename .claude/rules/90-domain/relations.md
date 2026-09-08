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
- `learning_rate` là public input tự do nhưng phải sống sót `encode_fp`: bội của `1/FP_SCALE` = 0,001. Adam mặc định 3e-4 mã hoá thành **0** — không biểu diễn được, nên số đo dưới Adam không phải số chứng minh được. `provable_learning_rate` chặn trước khi train.
- Aggregation: `AGGREGATION_MODE = "proof_manifest_chain"`. Không gọi đó là true recursive aggregation.
- Dataset cam kết **chính là** dataset fixed-point (Garg và cộng sự, CCS 2023). Trước đây đường ống băm `canonical_json` còn quan hệ băm số nguyên, nên hai quan hệ trung tâm cam kết vào hai vật thể khác nhau và prover tự chọn được cây mình đã huấn luyện. Lá liên tục (PointMaze) giữ quy tắc JSON, ghi ở `leaf_hash_rule`.
- `sampler_seed = H(dataset_root, global_step_start)`, **không** phải hằng số. Với seed cố định và `step_id` đếm trong nội bộ fragment, mọi chunk rút đúng cùng tập chỉ số — chuỗi 1248 bước là 156 lần lặp trên 8 dòng của dataset 50k. Ràng buộc này cũng chặn prover grind seed (Tan và cộng sự, 2025).
- Quan hệ công bố `q_abs_max_fp` và `gradient_clip_fp`. Bound là range proof theo chuẩn ZK, và phải kiểm **trước** phép nhân `gamma * q`. Clip theo từng thành phần (không theo chuẩn L2 — cần căn bậc hai) gần như miễn phí: 78,0 → 75,4 trên cartpole-random. Thứ chặn việc học là **`target_sync_interval`**, không phải batch. Đối chứng D đo batch=1 tại sync=100 rồi kết luận cả hai độc lập gây chết — đúng tại sync đó, sai khi khái quát. Đối chứng E quét 60 ô ở batch=1: sync=4 cho sàn 9,4 ở mọi dataset, sync=2000 cải thiện cả sáu và đưa lunarlander-random từ −775,8 lên −152,7, vượt cấu hình tinh chỉnh batch-256 (−215,3). `target_sync_interval` là public input tự do nên đổi **không tốn proving**; `batch_size` thì bị assert cứng và nhân cycles. **Vector canonical giữ sync=4**: k=8 ở sync=2000 không có sự kiện đồng bộ nào, `tamper_target_sync_event` sẽ không còn gì để sửa.
