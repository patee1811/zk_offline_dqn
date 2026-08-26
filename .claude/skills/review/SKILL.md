---
name: review
description: >
  Review a diff or PR against repo invariants and claim boundaries.
  Use when the user asks for a review or types /review.
---

# /review

Đọc `git diff` (hoặc PR). Kiểm theo thứ tự:

1. **Lớp** — semantics có lọt CLI/scripts không? Relation có I/O không?
2. **Số học / Merkle** — có `round` trong nhân FP không? Lá lẻ có đổi sang pad-zero không?
3. **Claim** — README/docs/paper có cụm bị `check_paper_claims.py` cấm không? Chạy scanner nếu đụng text.
4. **Schema** — `schema_version` / field roles có đổi lén không?
5. **Test** — có golden/negative tương ứng không? Có skip trần không?
6. **Secret / artifact** — `proof.bin`, kaggle output, token?
7. **Import** — Merkle/TD có đi thẳng `zk_offline_dqn.merkle` / `zk_offline_dqn.zk_specs` không, hay dựng lại lớp re-export?

Ghi finding: file:line, tác động, mức (block / nên sửa / ghi chú). Không rewrite cả PR.
