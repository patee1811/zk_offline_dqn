# Harness inbox

Append-only. `/harness-sync` merges approved items. Do not edit rules from here.

Format:

```markdown
## YYYY-MM-DD — người sửa|phát hiện mới|thất bại — scope <scope>
**Kích hoạt:** …
**Bài học:** …
**Đích đề xuất:** …
**Độ tin cậy:** cao|trung|thấp
**Trạng thái:** chờ xử lý
```

## 2026-08-26 — thất bại — scope harness
**Kích hoạt:** R1 chỉ đổi 7 dòng import, nhưng `ruff format` (PostToolUse hook và pre-commit) reflow cả file thành diff 119 dòng. Phải `git checkout` hoàn tác hai lần.
**Bài học:** formatter chạy trên cả file mâu thuẫn với rule "diff chỉ chứa đúng thứ thay đổi cần" khi cây chưa từng được format. Đã gỡ `ruff format` khỏi cả hai hook, giữ `ruff check --fix`.
**Đích đề xuất:** đã áp dụng vào `.pre-commit-config.yaml`, `format_after_edit.py`, `ruff.toml`. Cân nhắc: format cả cây trong một commit riêng rồi bật lại?
**Độ tin cậy:** cao (quan sát trực tiếp hai lần)
**Trạng thái:** đã áp dụng (1.1.0)

## 2026-08-26 — thất bại — scope harness
**Kích hoạt:** `git merge origin/master` bị `validate_commit_msg.py` chặn — subject mặc định `Merge remote-tracking branch '...'` không thể theo Conventional Commits.
**Bài học:** merge commit là ngoại lệ có thật, không phải người dùng gõ sai. Hook nên bỏ qua subject bắt đầu bằng `Merge ` / `Revert ` thay vì bắt `--no-verify`. Ép `--no-verify` làm mòn thói quen dùng cổng chặn.
**Đích đề xuất:** `.claude/hooks/validate_commit_msg.py` — thêm allowlist prefix; `commitlint.config.cjs` cần khớp.
**Độ tin cậy:** cao (chặn một merge hợp lệ)
**Trạng thái:** đã áp dụng (1.1.0)

## 2026-08-26 — phát hiện mới — scope tests
**Kích hoạt:** `tests/regression/test_report_generation.py` fail trên mọi worktree sạch (kể cả `origin/master`), nhưng xanh trên cây làm việc.
**Bài học:** test đọc `artifacts/benchmarks/*_python_smoke/` — thư mục generated đã gitignore. Nó phụ thuộc trạng thái local, không phải hồi quy thật. CI qua được vì `run_full_regression.py` sinh ra chúng trước.
**Đích đề xuất:** `rules/30-kiem-thu.md` — ghi rõ test nào cần artifact sinh trước; hoặc thêm `skipUnless(...exists())` như các golden test khác.
**Độ tin cậy:** cao (kiểm chéo 3 worktree)
**Trạng thái:** đã áp dụng (1.1.0, PR #31)

## 2026-08-26 — thất bại — scope harness
**Kích hoạt:** `guard_protected_paths.py` từ chối ghi vào scratchpad của phiên — chính thư mục harness được chỉ định dùng cho file tạm.
**Bài học:** "đường dẫn tuyệt đối ngoài repo" quá rộng: nó bắt cả vùng tạm hợp lệ. Đã cho qua `/tmp` và scratchpad; đường dẫn tuyệt đối khác vẫn chặn.
**Đích đề xuất:** đã áp dụng vào `.claude/hooks/guard_protected_paths.py` (1.1.0).
**Độ tin cậy:** cao (chặn một thao tác hợp lệ)
**Trạng thái:** đã áp dụng (1.1.0)

## 2026-08-27 — phát hiện mới — scope backends
**Kích hoạt:** kế hoạch A* mở đầu bằng "VRAM ≥24GB — bạn có 30GB — đủ". Kiểm mã nguồn: cả tám host hardcode `ProverClient::builder().cpu()`, không có feature `cuda` ở đâu.
**Bài học:** ngưỡng VRAM của SP1 không áp dụng cho artifact này. Nút thắt luôn là RAM CPU. Ba dòng `failed_oom` là CPU RAM cạn, và PLONK ~60GB là ứng viên hàng đầu vì không có gì khác tranh bộ nhớ.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md`
**Độ tin cậy:** cao (đọc trực tiếp tám `main.rs` + grep Cargo.toml)
**Trạng thái:** đã áp dụng (1.2.0)

## 2026-08-27 — thất bại — scope backends
**Kích hoạt:** hai case recursion trong campaign dùng `--proof-mode groth16_bn254`. Host aggregation không có cờ đó — nó nhận `--mode`, và từ chối mode mà case JSON không khai báo. Cả ba vector đã commit đều `proof_manifest_chain`.
**Bài học:** nếu đẩy nguyên lên Kaggle, hai case fail vì sai tham số và tôi sẽ đọc nhầm là OOM — đúng thứ chiến dịch tồn tại để đo. Recursion phải sinh case trước bằng `run_phase7_sp1_training_aggregation_validation.py`.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md`; đã sửa campaign (PR #33, `0db8a21`).
**Độ tin cậy:** cao (đọc `main.rs:40` + ba test vector)
**Trạng thái:** đã áp dụng (1.2.0)

## 2026-08-27 — thất bại — scope experiments
**Kích hoạt:** lần đo bộ nhớ đầu tiên báo `merkle_membership` đỉnh 9915MB ở giai đoạn `setup`. Log cho thấy `Finished release profile in 10m 44s` — build chạy trong cửa sổ đo.
**Bài học:** warmup chỉ build `short-trace-host`, hai workspace kia compile lúc đang đo. Dòng đó là chi phí biên dịch, không phải proving. Build mọi host trước khi đo.
**Đích đề xuất:** `rules/90-domain/experiments.md`; kernel lần 2 đã build cả 5 host.
**Độ tin cậy:** cao (log Kaggle)
**Trạng thái:** đã áp dụng (1.2.0)

## 2026-08-27 — người sửa — scope harness
**Kích hoạt:** người dùng sửa lại trong phiên
**Bài học:** tôi có bảo 30GB GPU đâu, ý tôi là 30GB CPU ý=))
**Đích đề xuất:** /harness-sync quyết định
**Độ tin cậy:** thấp (tự động, chưa duyệt)
**Trạng thái:** chờ xử lý
