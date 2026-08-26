---
paths:
  - "**"
---

# Bảo mật và secret

Lý do: không có auth/thanh toán, nhưng proof, Kaggle token và số paper bị lộ/sửa sẽ phá artifact.

- Không hardcode token, khóa, chuỗi kết nối. Dùng `${TEN_BIEN}`. Kaggle: `KAGGLE_USERNAME` / `KAGGLE_KEY`, không commit `~/.kaggle/kaggle.json`.
- Không log secret, token, toàn bộ request body có chúng. Không commit `proof.bin` (đã gitignore dưới `artifacts/reports/provenance/sp1/**/proof.bin`).
- Đầu vào ngoài: JSON artifact đi qua `load_json_artifact` + `require_schema_version`. Không tin field lạ.
- Không nối chuỗi thành lệnh shell. SP1 helpers chỉ **trả argv** (`backends/sp1/commands.py`), không `subprocess` khi import.
- Đặc quyền tối thiểu. Không thêm permission `Bash(git push *)` hay `Bash(cargo run --release *)` vào allowlist.
- Dependency: `requirements.lock` khi được; CI hiện cài `requirements.txt` (lỏng hơn). Không thêm package khi chưa duyệt.
- Bắt buộc người duyệt: auth (không có), migration schema, field public/private, `zk_specs` constants, xóa fixture CI, `RUN_HEAVY_*`, deploy/publish (không có).
- SHA256 hex 64 ký tự là Merkle root/leaf — hook secret **không** chặn entropy hex trần.
