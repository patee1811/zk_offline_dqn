# Kế hoạch refactor: gộp lớp và làm sạch tên

Trạng thái: **đề xuất, chưa thực hiện**. Ngày: 2026-08-26.

Bối cảnh: người dùng thấy cấu trúc "lộn xộn, không đồng bộ". Khảo sát cho thấy
phần lớn cảm giác đó đến từ **tên trùng qua nhiều lớp**, không phải code trùng.
Tài liệu này ghi cái gì đáng làm, cái gì không, và giá phải trả.

## Đã đo được

| Quan sát | Số liệu | Kết luận |
| --- | --- | --- |
| `core/` re-export | 77 dòng, **0** định nghĩa mới | Wrapper thuần |
| Ai dùng `core/` | 6 file `zk_offline_dqn/`, 3 file test | Cả hai đường song song |
| Ai dùng module gốc | `zk_specs` 21, `merkle` 11, `io_utils` 9 | Đường gốc vẫn chính |
| `forward_td_mlp.py` × 4 | 312 / 129 / 58 / 105 dòng | **Không** trùng logic |

Điểm mấu chốt: bốn file cùng tên `forward_td_mlp.py` là bốn lớp khác nhau —
logic gốc, relation thuần, verifier I/O, SP1 fixture. Trùng tên, không trùng
nội dung. Đây là quy ước phân lớp nhất quán (`relations/X.py` ↔ `verifiers/X.py`),
không phải sự lộn xộn. **Đề xuất giữ nguyên.**

## Việc đáng làm

### R1 — Gộp `core/` vào module gốc

Rủi ro: trung bình. Giá trị: xóa một lớp gián tiếp không mang ngữ nghĩa.

`core/merkle.py` và `core/td_arithmetic.py` chỉ `from zk_offline_dqn.merkle import *`
rồi liệt kê lại `__all__`. Chúng ra đời trong Phase 1B như bước đệm cho một cuộc
migrate chưa bao giờ hoàn tất. Hệ quả: người đọc gặp hai đường import cho cùng
một hàm và không biết đường nào là chuẩn.

Các bước:

1. Sửa 6 import trong `zk_offline_dqn/` sang module gốc.
2. Sửa 3 file test. `test_active_import_surface.py` mất lý do tồn tại — nó
   assert wrapper khớp module gốc. Cần **hỏi người** trước khi xóa test.
3. Xóa `zk_offline_dqn/core/`.
4. Chạy 237 test + `check_paper_claims.py`.

Cân nhắc ngược: bất biến số 8 trong [CLAUDE.md](../../CLAUDE.md) nói hai bên
phải khớp. Gộp lại làm bất biến đó biến mất — đơn giản hóa thật, nhưng phải cập
nhật CLAUDE.md và rule vùng relations trong cùng commit.

### R2 — Đặt tên nhất quán cho fixture membership

Rủi ro: **cao**. Giá trị: thấp.

`cartpole_dqn_eps010_*` mã hóa tham số vào tên file. Đổi tên sẽ gãy:
`regression.yml` (kiểm bằng đường dẫn tuyệt đối), `build_leaf_hashes.py` và
`build_merkle_root.py` (hardcode path), và các số trong `final_ndss/`.

**Đề xuất không làm.** Tên xấu nhưng ổn định; xem
[docs/fixture_provenance.md](../../docs/fixture_provenance.md) để hiểu nó là gì.

### R3 — `scripts/` phẳng hơn

Rủi ro: cao. Giá trị: thấp.

`run_full_regression.py` gọi 5 script trong `artifacts_export/` bằng đường dẫn
chuỗi. `docs/archive/internal_manifests/` trích dẫn hàng chục đường dẫn.
`check_release_readiness.py` assert file tồn tại theo path.

**Đề xuất không làm** khi paper còn đang review.

## Việc dứt khoát không nên làm

- Đổi tên `relations/` ↔ `verifiers/` cho "rõ hơn" — cặp tên hiện tại là hợp
  đồng, tests bám vào.
- Gộp `zk_specs.py` vào `core/` — 21 file import nó, gồm cả SP1 alignment test.
- Chạy `ruff format` toàn cây — diff khổng lồ, che mất mọi thay đổi thật sau đó.
- "Siết kiểu" `Dict[str, Any]` thành TypedDict — bất biến số 10.

## Đề xuất

Chỉ làm R1, thành một commit riêng, không kèm việc khác. Nếu paper còn đang
review thì hoãn cả R1 — lợi ích là code sạch hơn, không phải sửa lỗi, và mọi
thay đổi lúc này đều làm reviewer phải đọc lại.
