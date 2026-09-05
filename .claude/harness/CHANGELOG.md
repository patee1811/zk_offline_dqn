# Harness changelog

## 2026-09-06 — 1.6.0

**Kích hoạt:** phiên Phase 1 — huấn luyện chính sách nguồn, thu thập sáu dataset 50k, dựng lại Table 1. Ba bài học, hai trong đó là lỗi provenance đã lọt vào số liệu đã commit.

**Lý do:** cùng một lớp lỗi xuất hiện **hai lần** ở hai chỗ khác nhau (hardcode 10000), và cả hai lần đều sinh ra một bảng trông hợp lệ — không có cảnh báo nào ở output, nên chỉ rule mới chặn được. Mục thứ ba là ràng buộc quyết định con số nào của paper là số chứng minh được.

**Đã sửa:**

- `data-pipeline.md`: dòng `--policy random` đã sai từ khi thêm `--policy checkpoint`; nay ghi cả hai policy, `policy_hash` phải gồm SHA256 checkpoint + epsilon, và MountainCar vắng mặt vì DQN vanilla 200k bước cho đúng −200,0 ở cả 10 checkpoint.
- `data-pipeline.md`: thêm dòng số dataset trong report phải là dataset đã commit, kèm cả hai chỗ hardcode 10000 (`ensure_self_collected_dataset` tái tạo theo target size; `_dataset_transition_limit` cắt còn 10k trong khi `subset` lấy N dòng **đầu**) và nơi khoá lại chúng.
- `experiments.md`: thêm dòng đối chứng phải chạy đúng cấu hình của số đã in và quét tham số phải phủ cả hai nhánh, kèm quy tắc chọn bằng chuẩn hoá min-max trong từng ô — trung bình thô và đếm ô thắng đều cho kết quả sai trên chính bộ số này.
- `relations.md`: thêm ràng buộc `learning_rate` phải sống sót `encode_fp` (bội của 0,001); Adam mặc định 3e-4 mã hoá thành 0, nên số đo dưới Adam không phải số chứng minh được.

**Bỏ:** hai mục do `capture_learning.py` tự bắt — một chỉ thị lập plan dùng một lần, và một câu "đừng đoán bừa" đã được `rules/00` và `rules/20` phủ.

## 2026-09-02 — 1.5.0

**Kích hoạt:** phiên tổng quát hóa cây gộp (việc 0.2) và lượt prove lại 8 dòng `training_aggregation` sau khi guest ELF trôi. Bốn bài học, ba trong đó tốn máy thật hoặc suýt đưa số sai vào Table 2.

**Lý do:** hai mục là luật đo được (arity, cycles) giúp agent sau ước chi phí trên giấy thay vì thuê GPU. Hai mục còn lại là bẫy im lặng — không có cảnh báo nào ở output, nên chỉ rule mới chặn được.

**Đã sửa:**

- `sp1-backend.md`: dòng arity nay tách rõ **hai** thứ cùng tên — arity nén nội bộ SP1 (=4, panic nếu đổi) và arity cây gộp của repo (=2, nằm trong schema qua sáu field `left_/right_child_*`). Đổi cái sau là migration, không phải chỉnh tham số.
- `sp1-backend.md`: dòng prover nay ghi `SP1_CUDA` im lặng theo **cả hai chiều** — host thiếu feature thì bỏ qua biến và chạy CPU; host có feature thì đổi phần cứng của phép đo mà output không ghi lại. Kèm số đo cả hai chiều.
- `sp1-backend.md`: thêm sửa `shared/src/lib.rs` làm trôi ELF của **mọi** dòng dùng chung guest (8 dòng, không phải 3) — quét theo relation, không theo tên thư mục.
- `sp1-backend.md`: thêm `git archive` trên Windows áp `core.autocrlf`, làm lệch toàn bộ Witness Schema SHA256.
- `experiments.md`: dòng bộ nhớ recursion nay là luật hai vế — bộ nhớ phẳng, cycles tuyến tính ở ≈154M mỗi lượt verify con, giữ nguyên khi proof con là proof đệ quy. Kèm công thức a(N−1)/(a−1) để ước cây bất kỳ.

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
