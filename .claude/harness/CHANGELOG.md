# Harness changelog

## 2026-08-31 — 1.4.0

**Kích hoạt:** recursion native chạy được trên GPU sau khi thất bại ở 30GB và 61GB RAM host; và một lượt chạy GPU 4 giờ phải làm lại vì gọi host trực tiếp nên thiếu `tamper_report.json`.

**Lý do:** dòng "cả tám host hardcode `.cpu()`, nút thắt là RAM CPU" nay sai và sẽ dẫn agent sau đi lại ngõ cụt. Hai bài học còn lại đều tốn máy thật.

**Đã sửa:**

- `sp1-backend.md`: dòng prover CPU thay bằng sự thật đo được — nút thắt là hằng số dựng mạch (>61GB RAM host, 18.4GB VRAM), GPU cần CC ≥ 8.0 và ≥24GB VRAM, `sp1-cuda` 6.1.0 không cần Docker.
- `sp1-backend.md`: thêm `cycle_count` tất định theo `(guest ELF, input)`, provenance ghi `guest_elf_sha256`, đo lại phải `sp1up --version v6.1.0`.
- `experiments.md`: siết dòng bộ nhớ recursion — nay có số đo GPU, hằng số qua 20 lần chênh cycles.
- `experiments.md`: thêm provenance recursion phải qua script phase, `--out-dir` phải tuyệt đối.

## 2026-08-30 — 1.3.1

**Kích hoạt:** cwd phiên đổi sang `.claude/`, cả bảy hook chết và khóa luôn Bash + Edit.

**Lý do:** hook cưỡng chế đường biên, nên một hook không chạy được sẽ chặn mọi việc. Đường dẫn tương đối làm điều đó phụ thuộc vào chỗ người dùng đang đứng.

**Đã sửa:** cả bảy `command` trong `settings.json` dùng `\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/...` thay cho đường dẫn tương đối. Đây là mẫu trong tài liệu hooks chính thức. Kiểm chứng bằng cách chạy lại Bash từ chính `.claude/`.

## 2026-08-30 — 1.3.0

**Kích hoạt:** phiên thuê máy ngoài để phá trần bộ nhớ recursion. Mất một lần chạy 14 giờ và hai giả thuyết bị bác bỏ bằng số đo.

**Lý do:** ba bài học đều tốn thật — một cái tốn 14 giờ máy, hai cái còn lại tốn hai vòng sweep. Không rule nào phủ chúng.

**Đã thêm:**

- `experiments.md`: máy thuê chạy prove phải on-demand, không spot. Instance spot biến mất sau 14 giờ cùng toàn bộ kết quả.
- `experiments.md`: kết quả phải rời khỏi máy trước khi máy chết; terminate chỉ sau khi kiểm tarball có trên đĩa.
- `experiments.md`: đỉnh RSS recursion không phụ thuộc khối lượng — T=8 đo 30399MB, T=32 đo 29255MB. Giảm target không lách được trần.
- `sp1-backend.md`: arity cây recursion cố định ở 4. `SP1_WORKER_MAX_COMPOSE_ARITY` được đọc nhưng `compress_proof_shape_from_arity` panic với mọi giá trị khác.

**Đã bỏ:** mục `2026-08-27 — người sửa` (GPU/CPU) — hook `capture_learning` bắt đúng, nhưng bài học đã được ghi tay vào `sp1-backend.md` cùng ngày. Đánh dấu trùng, không thêm rule.

## 2026-08-27 — 1.2.0

**Kích hoạt:** phiên chuẩn bị nộp A* làm lộ ba điều về backend SP1 mà không rule nào ghi, và hai trong ba đã dẫn tới kết luận sai trước khi kiểm mã nguồn.

**Lý do:** rule vùng tồn tại để agent không phải suy ra API từ đầu mỗi phiên. Ba mục này đều là kiến thức không đọc được từ tên hàm — phải mở `main.rs` hoặc đọc log mới biết.

**Đã thêm:**

- `sp1-backend.md`: prover chạy CPU, không GPU. Tám host hardcode `.cpu()`, không có feature `cuda`. Kế hoạch trước đó mở đầu bằng ngưỡng VRAM — hoàn toàn không liên quan.
- `sp1-backend.md`: host aggregation nhận `--mode`, không `--proof-mode`, và từ chối mode mà case JSON không khai báo. Hai case recursion suýt chạy sai tham số rồi bị đọc nhầm là OOM.
- `experiments.md`: build mọi host trước khi đo bộ nhớ. Lần đo đầu, biên dịch `merkle_membership` lọt vào cửa sổ đo và 9915MB rơi nhầm vào `setup`.

**Ghi chú:** `capture_learning.py` không bắt được ba mục này vì `SESSION_NOTES.md` chưa bao giờ tồn tại — hook chỉ đọc file đó và không ai tạo. Đã sửa ngay trong phiên, xem 1.2.1.

## 2026-08-27 — 1.2.1

**Kích hoạt:** 1.2.0 ghi nhận thu nhận tự động là đường chết. Người dùng duyệt sửa luôn.

**Lý do:** ba mục của 1.2.0 vào INBOX chỉ vì gõ tay. Một vòng lặp tự tiến hóa mà khâu thu nhận không bao giờ chạy thì chỉ là vòng lặp trên giấy.

**Đã sửa:** `capture_learning.py` đọc transcript phiên thay vì file không ai viết. Nó quét message của người dùng tìm mẫu sửa lưng (Việt và Anh) và append candidate với độ tin cậy `thấp (tự động)` — `/harness-sync` vẫn là nơi quyết định.

**Kiểm chứng trên transcript thật của phiên này:** trước khi lọc, bộ dò trả 3 kết quả, trong đó 2 là thân skill bị chèn vào lượt user (11k và 249k ký tự). Thêm trần 2000 ký tự thì còn đúng 1 — chính câu người dùng sửa "30GB GPU đâu, ý tôi là 30GB CPU". Dedup theo chuỗi con chặn ghi lại mục đã có.

## 2026-08-26 — 1.1.0

**Kích hoạt:** phiên đầu tiên dùng harness thật (R1 refactor + merge phase-10) làm lộ bốn chỗ cổng chặn bắt nhầm.

**Lý do:** cổng chặn thứ hợp lệ thì người dùng học cách bypass, và thói quen đó phá chính thứ cổng bảo vệ.

**Đã sửa:**

- `validate_commit_msg.py`: cho qua subject `Merge ` / `Revert ` — git tự sinh, không thể là Conventional Commit.
- `validate_commit_msg.py`: bỏ payload `-m` trước khi tìm cờ bypass — message *nhắc tới* cờ không phải là dùng nó.
- `guard_protected_paths.py`: cho qua scratchpad và `/tmp` — vùng tạm hợp lệ, không phải ghi ngoài repo.
- `tests/regression/test_report_generation.py` + `rules/30-kiem-thu.md`: `skipTest` khi thiếu output của `run_full_regression.py`. Đây là bug có sẵn của repo, harness chỉ làm lộ ra: clone sạch fail 2 test.

**Đã gỡ trước đó (cùng ngày, trước khi đánh version):** `ruff format` khỏi PostToolUse hook và pre-commit — nó reflow cả file, biến 7 dòng đổi import thành 119 dòng diff.

**Còn ngỏ:** format cả cây trong một commit riêng rồi bật lại `ruff format`? Hoãn tới khi paper qua review — lúc này mọi diff lớn đều buộc reviewer đọc lại.

## 2026-08-26 — 1.0.0

**Kích hoạt:** bootstrap harness trên `origin/master` (f3ca555, PR #27).

**Lý do:** repo chưa có `.claude/`, linter, hay git hook. Paper claim và lớp relation/verifier cần cổng chặn, không chỉ lời khuyên.

**Đã thêm:** CLAUDE.md, AGENTS.md, rules, skills, agents, Python hooks, ruff (hẹp), commitlint gương, pre-commit.
