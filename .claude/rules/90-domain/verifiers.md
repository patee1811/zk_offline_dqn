---
paths:
  - "zk_offline_dqn/verifiers/**"
  - "zk_offline_dqn/cli/**"
---

# Vùng verifiers và CLI

Lý do: verifier được phép I/O; nếu mang semantics vào đây thì hai đường verify sẽ lệch.

- Verifier: `load_json_artifact` → (schema) → gọi `relations.check_*`. Không tính lại TD/Merkle khác relation.
- Đường mặc định fixture nằm trong verifier (`DEFAULT_*_PATH`). Đổi path mặc định phải có test golden.
- CLI `python -m zk_offline_dqn.cli.main` chỉ có `verify` / `benchmark` / `report`. Namespace mới cần người duyệt.
- CLI bắt exception ở `_run_command`, in `accepted = False` + `error = Type: msg`, exit 1. Relation vẫn phải ném lỗi thật.
- Không đặt semantics mới vào `scripts/artifacts_export/` (legacy, regression còn gọi).
- `benchmark` hiện là placeholder namespace — đừng giả vờ nó chạy Phase 8.
