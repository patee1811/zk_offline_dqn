---
paths:
  - "zk_offline_dqn/artifacts/**"
  - "zk_offline_dqn/artifact_schema_versions.py"
  - "zk_backend/test_vectors/**"
  - "artifacts/fixtures/**"
---

# Vùng schema artifact

Lý do: `schema_version` là hợp đồng ngược; đổi lén làm fixture CI và golden chết.

- Chuỗi version sống ở `artifact_schema_versions.py` và `artifacts/schemas.py`. Đổi = migration được duyệt.
- `require_schema_version` ném `ValueError` nếu thiếu hoặc lệch — giữ nguyên câu lỗi (test/golden bám text).
- Field roles (`public` / `private` / `debug`) ở `artifacts/field_roles.py`. Đổi phân loại = hỏi người.
- IO: `artifacts/io.py` (`load_json_artifact`). Không tự `json.load` kiểu khác trong verifier mới.
- Fixture regression bắt buộc (CI): pkl CartPole, merkle JSON, minibatch/one-step/short-trace artifacts, checkpoint `.pt`. Xóa = hỏi người.
- Test vector SP1 dưới `zk_backend/test_vectors/` là canonical đã khóa.
