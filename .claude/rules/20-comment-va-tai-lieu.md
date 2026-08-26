---
paths:
  - "zk_offline_dqn/**"
  - "scripts/**"
  - "tests/**"
  - "zk_backend/**"
  - "docs/**"
---

# Comment và tài liệu

Lý do: comment diễn lại code sẽ lạc hậu; comment “tại sao” giữ được số học cố định và ranh giới claim.

Nguyên tắc: code nói cái gì, comment nói tại sao.

## Được viết khi

| Nhóm | Ví dụ trong repo |
| --- | --- |
| Lý do lựa chọn | `// 1000` rồi SHA256 — khớp artifact đã commit |
| Đánh đổi | Phase 7 = `proof_manifest_chain`, không verify child proof trong SP1 |
| Bất biến | `(a * b) // fp_scale`, không `round` |
| Cách lách lỗi | wrapper `core.merkle` re-export vì Phase 1B không migrate |
| Hiệu năng | chỉ khi có số đo (Kaggle cycle count), không đoán |
| Bảo mật | field `private` trong `artifacts/field_roles.py` |
| Việc cần làm | `TODO(human): đo thật` hoặc `TODO(owner): … (#n)` |

## Không viết

Diễn lại code, thuyết minh từng bước, nhật ký ngày tháng, chữ ký, docstring chỉ lặp chữ ký hàm.

## Định dạng

Câu hoàn chỉnh, thì hiện tại. Rules/CLAUDE.md: tiếng Việt. Docstring và comment trong source: **tiếng Anh**, khớp cây hiện tại (`"""Pure transition membership relation checks."""`). Không dịch ngược comment cũ.

Nhãn: `TODO`, `FIXME`, `HACK`, `NOTE`, `SAFETY`, `PERF` + `(owner):`.

## Docstring

PEP 257 / rustdoc. Bắt buộc với hàm export ra ngoài package. Đổi hành vi thì đổi docstring cùng commit. `docs/` mô tả implementation; `paper/` là claim — đừng trộn.
