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
  - "artifacts/reports/paper_support/**"
---

# Vùng paper và claim

Lý do: sai một câu trên paper/README thì artifact hết reviewable.

- Cấm nới claim. Scanner: `scripts/experiments/check_paper_claims.py` (banned phrases + negated phrases).
- Cấm khẳng định: full DQN training, Adam, honest public collection, true recursive aggregation, mọi relation đều có SP1, k=16/32/128 proof-backed, Table 3 chứng minh training.
- `thm:manifest-aggregation` gồm cả hai chế độ gộp. Chuỗi proof-manifest **không** verify child proof trong guest; chế độ `recursive_sp1` thì có. Đừng gọi chế độ đầu là recursive, và đừng trỏ định lý bằng số.
- `generate_paper_reports.py` chỉ đọc output đã có, **không** prove/benchmark lại.
- Số trên paper phải khớp artifact, và `final_ndss/` **không phải** toàn bộ vũ trụ — ba con số sai gần nhất lấy nguồn từ `provenance/sp1_t*/` hoặc từ không đâu cả. Không truy được về artifact thì ghi nguồn vào `artifacts/reports/paper_support/` rồi ghim bằng test, hoặc bỏ.
- Dải min–max phải nói rõ **quần thể**. Ba lỗi cùng một hình: min/max của một tập con (4 trên 8 lá, rồi 20 trên 32 lá), và một số là đại lượng khác loại — giây mỗi **lá** của cây khác, in thành giây mỗi **nút**.
- Sửa `paper/`, `docs/claim_matrix.md`, `final_ndss/`, formal statements: dừng, hỏi người.
- `docs/` mô tả implementation; `paper/` là bản submit. Đừng “sửa docs cho khớp mong muốn” rồi quên scanner.
