---
paths:
  - "scripts/data/**"
  - "zk_offline_dqn/data_pipeline.py"
  - "artifacts/datasets/**"
  - "data/**"
---

# Vùng data pipeline

Lý do: commitment bắt đầu sau thu thập; viết “honest collection” là overclaim.

- Chuỗi: `collect_audited_dataset.py` → `audit_replay_dataset.py` → `commit_audited_dataset.py` → `verify_dataset_commitment.py`.
- Phase 2 collect chỉ `--policy random`. Policy khác → `ValueError`.
- `data/` và `artifacts/datasets/` là generated, gitignore. Không commit replay mới trừ khi được hỏi.
- Public import (`import_public_dataset.py`) chỉ source-integrity, không chứng minh thu thập trung thực.
- Merkle root gắn manifest, audit report, raw trajectory, collection-log hashes. Tamper một hash phải fail (`tests/negative/test_dataset_provenance_tamper.py`).
- `make reproduce-data-audit` dùng CartPole 1 episode / 5 steps — đủ cho reviewer smoke, không phải dataset paper.
