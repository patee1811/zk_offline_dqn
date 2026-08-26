---
paths:
  - "**"
---

# Nguyên tắc cốt lõi

Lý do: agent mới hay mang “best practice” ngoài vào rồi phá lớp relation/verifier.

- Hòa vào code xung quanh. Repo này thắng mọi hướng dẫn ngoài. `Dict[str, Any]` cho JSON artifact là style đã chọn, không phải mùi cần siết kiểu.
- Đọc trước khi viết. Tìm helper trong `zk_offline_dqn/{merkle,zk_specs,io_utils}.py` trước khi tạo bản sao.
- Thay đổi nhỏ nhất giải quyết trọn vẹn vấn đề. Không nhét refactor vào một feature.
- Không khái quát hóa phòng xa. Relation mới chỉ khi có vector + provenance, không “để sau dùng”.
- Ưu tiên xóa hơn thêm. Ưu tiên nhàm chán hơn thông minh.
- Không để cây kiểm tra hỏng. Thay đổi Python: unittest liên quan xanh. Đụng paper: `check_paper_claims.py` xanh. Repo không có lint/typecheck sẵn có.
- Yêu cầu mơ hồ thì hỏi. Không đoán rồi đi tiếp — đặc biệt với claim paper, schema, field public/private.
- Nói rõ mức chắc chắn. “Đã chạy `python -m unittest …`, exit 0” hoặc “chưa đo `make reproduce-small`”.
