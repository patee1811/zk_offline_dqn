---
name: plan-change
description: >
  Plan a code change before editing. Use when the user asks to design,
  scope, or /plan-change a feature or bugfix.
---

# /plan-change

1. Phân lớp: relation / verifier / schema / SP1 / script / paper / harness. Sai lớp thì dừng.
2. Đọc code hiện có cùng abstraction (`relations/*.py`, verifier cặp, test golden/negative).
3. Liệt kê file sẽ đụng. Nếu đụng `paper/`, `claim_matrix.md`, `zk_specs.py`, `test_vectors/`, `final_ndss/`, schema version, field roles — ghi “cần hỏi người”.
4. Kế hoạch tối thiểu:
   - thay đổi semantics ở đâu
   - test nào (unit / golden / negative / paper-claims)
   - claim nào **không** được viết
   - rollback
5. Không implement trong skill này trừ khi người dùng bảo tiếp.
6. Lưu kế hoạch vào `.claude/plans/<scope>-<slug>.md` nếu thay đổi >1 lớp.
