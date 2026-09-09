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
- Không dùng heredoc cho nội dung có backslash (LaTeX, Rust, regex). Công cụ Bash ăn mất một tầng: `\\` cuối dòng bảng thành `\` (LaTeX báo `Misplaced \noalign` ở dòng *khác*), `\ref` thành CR, `\texttt` thành TAB + `exttt` — **compile sạch, PDF in ra chữ `exttt{...}`**. Ghi script ra file bằng Write rồi `python <file>`; trong regex dùng `re.escape(chr(92))`. Lỗi loại này không làm build đỏ, nên `tests/unit/test_paper_numbers_match_artifacts.py` chặn ký tự TAB trong mọi mục paper đang dùng.
- Yêu cầu mơ hồ thì hỏi. Không đoán rồi đi tiếp — đặc biệt với claim paper, schema, field public/private.
- Nói rõ mức chắc chắn. “Đã chạy `python -m unittest …`, exit 0” hoặc “chưa đo `make reproduce-small`”.

## Không trôi khỏi phạm vi

Lý do: một phiên “làm hết 6 mục” đã nở thành 3 lượt GPU và một lần chạy lại Bảng 1, vì mỗi mục lộ ra lỗi mới và lỗi nào cũng được sửa ngay tại chỗ.

- Phát hiện giữa chừng thì **ghi INBOX, không sửa**. Chỉ hai ngoại lệ: nó làm sai thứ vừa tạo ra trong chính lượt này, hoặc nó miễn phí và nằm trong file đang mở.
- Phát hiện hay vẫn là trôi phạm vi. Đổi phạm vi hoặc ngân sách thì **dừng lại hỏi**, kể cả khi cách sửa đã rõ.
- **Mỗi lượt một phiên GPU.** Phiên thứ hai phải hỏi. Ước lượng lệch quá 50% thì dừng, báo lại, đừng chạy tiếp cho xong.
- Trước khi “sửa” một con số đã công bố, đọc **file cấu hình đã sinh ra nó** (`*_status.json`, provenance), không đọc hằng số trong code rồi suy ra. Bảng 1 chạy ở `sgd_learning_rate = 0.05`; đọc `PROVED_SGD_LEARNING_RATE = 0.01` rồi kết luận ngược đã làm hỏng kết quả hoà 12–12 và tốn thêm một lượt prove.
- Báo cáo giữa chừng khi lượt chạy vượt dự kiến, đừng đợi tới lúc xong.
