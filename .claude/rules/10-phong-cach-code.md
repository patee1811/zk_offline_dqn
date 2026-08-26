---
paths:
  - "zk_offline_dqn/**/*.py"
  - "scripts/**/*.py"
  - "tests/**/*.py"
  - "zk_backend/**/*.rs"
---

# Phong cách code

Lý do: cây hiện tại lệch nhau; agent hay “làm sạch” rồi phá wrapper/`Dict[str, Any]`.

## Lệch so với bộ nền (repo thắng)

- Không có formatter/linter sẵn có. Harness thêm `ruff` chỉ trên file vừa sửa (`ruff.toml`: py39, 100 cột, lint E9/F63/F7/F82). Không format cả cây; không thêm `ruff format --check` vào CI.
- `Dict[str, Any]` / `Mapping[str, Any]` cho JSON artifact là hợp đồng. Cấm siết thành TypedDict trong cùng PR trừ khi được hỏi.
- Module cũ (`merkle.py`, `zk_specs.py`) không bắt `from __future__ import annotations`. Module lớp mới thì có.
- Import: stdlib → third party → `zk_offline_dqn.*`. Không sắp xếp lại import ngoài phạm vi thay đổi.
- Tên hàm Python: `snake_case` (`check_transition_membership_artifact`). Rust: `snake_case`. Không camelCase.
- Test: `unittest.TestCase`, `self.assertEqual`, không pytest.

## Cấu trúc

- Guard clause, trần 3 tầng lồng. Hàm ~50 dòng là ngưỡng mềm.
- Hằng số có đơn vị trong tên: `FP_SCALE`, `GAMMA_FP`, `SMOOTH_L1_BETA_FP` đã có trong `zk_specs.py`.
- Logic thuần ở `relations/`; I/O ở `verifiers/` + `artifacts/io.py`; argparse ở `cli/` và `scripts/`.
- Lỗi: ném `ValueError` kèm ngữ cảnh (xem `require_schema_version`). CLI bắt `Exception` ở biên và in `accepted = False` — không nuốt trong relation.
- Bề mặt công khai: dataclass frozen + hàm `check_*` / `verify_*`. Không thêm `any` TypeScript-style.

## Vệ sinh

- Không code chết, không khối comment “phòng khi”, không emoji, không dấu vết AI.
- Không format tay. Không thêm dependency khi chưa được duyệt (`setup.py` gần như không pin; CI cài `requirements.txt`).
- Xóa bản bị thay thế. Giữ `scripts/artifacts_export/` vì regression còn gọi — đó không phải code chết.
