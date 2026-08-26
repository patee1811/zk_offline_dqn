---
paths:
  - "tests/**"
  - "scripts/experiments/run_*.py"
  - "scripts/experiments/check_*.py"
---

# Kiểm thử

Lý do: unittest + fixture JSON là bằng chứng reviewable; pytest/mock bừa sẽ làm golden mất ý nghĩa.

- Framework: `unittest` (không phải pytest). Khám phá: `python -m unittest discover tests`.
- Bốn lớp: `tests/unit`, `tests/golden`, `tests/negative`, `tests/regression`. Golden đọc fixture đã commit. Negative tamper một field rồi `assertFalse`.
- Tên: `test_<hành_vi>_<điều_kiện>` — `test_fixed_point_td_helpers_are_deterministic`, `test_duplicate_batch_indices_rejected`.
- Một hành vi mỗi test. Setup lặp lại còn hơn helper thông minh. Helper hiện có (`make_tiny_membership_artifact`) được phép nếu chỉ xây fixture.
- Test hợp đồng công khai (`check_*`, `verify_*`). Không mock `relations/`. Mock chỉ ở biên (filesystem/checkpoint) khi test đã làm vậy.
- Tất định: không mạng, không `sleep`, không đồng hồ hệ thống. SP1 prove không thuộc unittest; chỉ fixture/command builder.
- Vá bug: thêm test fail trước. Không `skip` thiếu `TODO(owner)` / lý do fixture vắng (`skipUnless(...exists())` đã dùng).
- Coverage không phải mục tiêu. Không viết assert chỉ để tăng số.
- Đụng paper/README/docs: chạy `python scripts/experiments/check_paper_claims.py`.
- Regression 15 check: `run_full_regression.py` cần fixture CI (pkl, merkle JSON, `.pt`). Thiếu thì nói rõ, đừng bịa pass.
