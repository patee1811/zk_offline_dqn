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
- Không dùng heredoc cho nội dung có backslash (LaTeX, Rust, regex). Công cụ Bash ăn mất một tầng: `\\` cuối dòng bảng thành `\` (LaTeX báo `Misplaced \noalign` ở dòng *khác*), `\ref` thành CR, `\texttt` thành TAB + `exttt` — **compile sạch, PDF in ra chữ `exttt{...}`**. Ghi script ra file bằng Write rồi `python <file>`; trong regex dùng `re.escape(chr(92))`. Lỗi loại này không làm build đỏ, nên `tests/unit/test_paper_numbers_match_artifacts.py` chặn **mọi byte điều khiển** trong mục paper đang dùng, không chỉ TAB: `\bigskip` thành backspace + `igskip` đã lọt qua bản chỉ nêu TAB và in thẳng vào PDF. Cổng phải đọc **bytes** — `read_text()` bật universal newline nên nó tự xoá CR lạc, và hai bản sửa cổng đều xanh trên file đang hỏng.
- Yêu cầu mơ hồ thì hỏi. Không đoán rồi đi tiếp — đặc biệt với claim paper, schema, field public/private.
- Nói rõ mức chắc chắn. “Đã chạy `python -m unittest …`, exit 0” hoặc “chưa đo `make reproduce-small`”.
- Ước lượng phải nói **suy từ đâu**, và ba lối suy đã sai thật: (a) tỉ lệ chi phí tổng **không** suy được từ khối lượng một thành phần con — “lá rẻ 2,33×” suy từ byte băm, đo thật là 1,79×; (b) nhịp của một phép chạy nhỏ **không** suy ra nhịp của phép chạy lớn — cây 15 nút cho 50 phút, cây 63 nút không phải 1,5 giờ mà 3h56; (c) cảnh báo cũng là ước lượng — “cycles ở WSL không so được với Bảng 2” lệch **0,006%**, suýt làm vứt cả phép đo. Ngân sách lệch quá 50% thì dừng và hỏi, đừng chạy tiếp cho xong.

## Không trôi khỏi phạm vi

Lý do: một phiên “làm hết 6 mục” đã nở thành 3 lượt GPU và một lần chạy lại Bảng 1, vì mỗi mục lộ ra lỗi mới và lỗi nào cũng được sửa ngay tại chỗ.

- Phát hiện giữa chừng thì **ghi INBOX, không sửa**. Chỉ hai ngoại lệ: nó làm sai thứ vừa tạo ra trong chính lượt này, hoặc nó miễn phí và nằm trong file đang mở.
- Phát hiện hay vẫn là trôi phạm vi. Đổi phạm vi hoặc ngân sách thì **dừng lại hỏi**, kể cả khi cách sửa đã rõ.
- **Mỗi lượt một phiên GPU.** Phiên thứ hai phải hỏi. Ước lượng lệch quá 50% thì dừng, báo lại, đừng chạy tiếp cho xong.
- Trước khi “sửa” một con số đã công bố, đọc **file cấu hình đã sinh ra nó** (`*_status.json`, provenance), không đọc hằng số trong code rồi suy ra. Bảng 1 chạy ở `sgd_learning_rate = 0.05`; đọc `PROVED_SGD_LEARNING_RATE = 0.01` rồi kết luận ngược đã làm hỏng kết quả hoà 12–12 và tốn thêm một lượt prove.
- Báo cáo giữa chừng khi lượt chạy vượt dự kiến, đừng đợi tới lúc xong.
