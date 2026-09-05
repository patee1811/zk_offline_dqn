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
- Collect nhận `--policy random` hoặc `--policy checkpoint`. Checkpoint đi vào `policy_hash` (SHA256 file + epsilon), không chỉ `policy_type`. Nguồn ở `artifacts/source_policies/` — `*.pt` force-add qua gitignore vì `policy_hash` khoá đúng bytes đó. MountainCar vắng mặt: DQN vanilla 200k bước cho đúng −200,0 ở cả 10 checkpoint, không sinh nổi cặp medium/expert.
- Số dataset trong report phải là dataset **đã commit**. Hai chỗ hardcode 10000 từng làm Table 1 dẫn `merkle_root` không tồn tại trong repo: `ensure_self_collected_dataset` tái tạo theo target size thay vì theo spec, và `_dataset_transition_limit` cắt còn 10k trong khi `subset` lấy N dòng **đầu**. Tham số thu thập nằm trong `SelfCollectedSpec`; `tests/unit/test_source_dataset_identity.py` khoá 6 root.
- `data/` và `artifacts/datasets/` là generated, gitignore. Không commit replay mới trừ khi được hỏi.
- Public import (`import_public_dataset.py`) chỉ source-integrity, không chứng minh thu thập trung thực.
- Merkle root gắn manifest, audit report, raw trajectory, collection-log hashes. Tamper một hash phải fail (`tests/negative/test_dataset_provenance_tamper.py`).
- `make reproduce-data-audit` dùng CartPole 1 episode / 5 steps — đủ cho reviewer smoke, không phải dataset paper.
