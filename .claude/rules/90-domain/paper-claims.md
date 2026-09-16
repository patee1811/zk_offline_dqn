---
paths:
  - "paper/**"
  - "docs/claim_matrix.md"
  - "docs/backend_coverage.md"
  - "docs/theorem_artifact_map.md"
  - "README.md"
  - "scripts/experiments/check_paper_claims.py"
  - "scripts/experiments/check_paper_numbers_against_final_ndss.py"
  - "scripts/experiments/check_theorem_artifact_map.py"
  - "artifacts/reports/final_ndss/**"
---

# Vùng paper và claim

Lý do: sai một câu trên paper/README thì artifact hết reviewable.

- Cấm nới claim. Scanner: `scripts/experiments/check_paper_claims.py` (banned phrases + negated phrases).
- Cấm khẳng định: full DQN training, Adam, honest public collection, true recursive aggregation, mọi relation đều có SP1, k=16/32/128 proof-backed, Table 3 chứng minh training.
- `thm:manifest-aggregation` gồm cả hai chế độ gộp. Chuỗi proof-manifest **không** verify child proof trong guest; chế độ `recursive_sp1` thì có. Đừng gọi chế độ đầu là recursive, và đừng trỏ định lý bằng số.
- `generate_paper_reports.py` chỉ đọc output đã có, **không** prove/benchmark lại.
- Số trên paper phải khớp `artifacts/reports/final_ndss/` (`check_paper_numbers_against_final_ndss.py`).
- Sửa `paper/`, `docs/claim_matrix.md`, `final_ndss/`, formal statements: dừng, hỏi người.
- `docs/` mô tả implementation; `paper/` là bản submit. Đừng “sửa docs cho khớp mong muốn” rồi quên scanner.
