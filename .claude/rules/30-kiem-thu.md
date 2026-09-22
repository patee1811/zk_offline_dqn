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
- Cổng mới phải **được nhìn thấy đỏ** một lần: phá đúng thứ nó canh, chạy lại, khôi phục. Một phiên có ba cổng xanh mà không thể đỏ — cổng escape chỉ nêu TAB nên backspace lọt, `read_text` xoá CR nên hai bản sửa đều xanh trên file hỏng, và `assertIn("193", text)` được thoả bởi chữ số ở câu khác. Ghim **nguyên cụm**, đừng ghim chữ số trần.
- Coverage không phải mục tiêu. Không viết assert chỉ để tăng số.
- Đụng paper/README/docs: chạy `python scripts/experiments/check_paper_claims.py`.
- Regression 15 check: `run_full_regression.py` cần fixture CI (pkl, merkle JSON, `.pt`). Thiếu thì nói rõ, đừng bịa pass. Test đọc **output** của nó (`regression_summary.json`, `*_python_smoke/summary.json` — đều gitignore) phải `skipTest`, không fail: clone sạch không có chúng.
- Đổi quan hệ thì cổng cuối trước khi tiêu tiền GPU phải chạy trên **lá thật của cây** — dataset thật, lưới thật, `k` thật — chứ không chỉ vector canonical. Sinh lại 8 lá của cây 1248 bằng code mới và so từng byte với `leaf_cases` đã lưu mất **22 giây Python**, và nó đóng đúng khả năng “đúng trên đồ chơi, sai trên dữ liệu thật”.
