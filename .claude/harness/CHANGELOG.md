# Harness changelog

## 2026-09-22 — 1.10.0

**Kích hoạt:** phiên đo chi phí MinAtar và ghim số paper. Inbox chỉ còn một mục (câu hỏi một lần), nhưng phiên sinh ra ba thất bại im lặng mà chưa rule nào chặn: build xanh, test xanh, kết quả sai.

**Lý do:** một dòng rule đang mô tả sai cổng của chính nó. `rules/00` nói cổng escape "chặn ký tự TAB"; trong phiên, `\bigskip` thành backspace + `igskip`, lọt qua cổng đó và in thẳng vào PDF với `latexmk` exit 0.

**Đã sửa:**

- `rules/00` — dòng heredoc: cổng nay chặn **mọi byte điều khiển** và đọc **bytes**, vì `read_text()` bật universal newline và tự xoá CR lạc — hai bản sửa cổng đầu tiên đều xanh trên file đang hỏng.
- `rules/30` — cổng mới phải **được nhìn thấy đỏ**: phá đúng thứ nó canh rồi chạy lại. Ba cổng không thể đỏ trong cùng một phiên (TAB-only, `read_text`, `assertIn("193")` thoả bởi chữ số ở câu khác); ghim nguyên cụm, không ghim chữ số trần.
- `90-domain/paper-claims.md` — `final_ndss/` không phải nơi duy nhất cần đối chiếu: ba con số sai nằm ngoài nó (`provenance/sp1_t*/` hoặc không đâu cả). Thêm quy tắc dải min–max phải nêu quần thể, và path `artifacts/reports/paper_support/**`.

**Gộp:** ba lần cổng không thể đỏ vào một dòng `rules/30` thay vì ba dòng; hai lỗi dải min–max và lỗi giây-mỗi-nút vào một dòng, vì cùng một hình.

**Bỏ:** mục 2026-09-17 ("ý tôi là bài của tôi có mạnh đến Q1 không ý") — câu hỏi một lần do `capture_learning.py` tự bắt.

**Không lên thang hook:** PreToolUse chặn heredoc-có-backslash đã bị bác ở 1.8.0 vì báo giả với `echo "\n"`, và lý do đó vẫn đúng. Cổng mạnh hơn đã nằm trong repo: `test_no_section_carries_a_mangled_escape` đọc byte, đã thử phá đủ ba kiểu (backspace, TAB, CR) và đỏ cả ba. "Nói rõ quần thể" không kiểm máy móc được; cơ chế thật là các test ghim từng con số trong `test_paper_numbers_match_artifacts.py`.

**Còn ngỏ:** ghi `cycle_count` từng lá vào provenance khi sinh lại cây, để dải min–max được sinh ra thay vì chép tay. Hiện test đọc lại `metrics.json` từng lá trong `provenance/sp1_t1248_lunarlander/` và `sp1_t4992_lunarlander_random/`, nhưng cây `provenance/sp1/_binary_native_work/` vẫn bị gitignore.

## 2026-09-16 — 1.9.0

**Kích hoạt:** ba phiên máy liên tiếp (prove lại toàn bộ Bảng 2, cây 4992, nhánh CUDA cho sáu host) đẩy 15 mục vào inbox, trong đó **bốn mục bác bỏ một dòng rule đang có** chứ không bổ sung gì.

**Lý do:** rule sai nguy hiểm hơn rule thiếu. Dòng `guest_elf_sha256` đang dạy một giả thuyết đã được đo là sai, và dòng prover đang mô tả một giới hạn vừa bị gỡ; cả hai đều đọc trôi chảy nên không ai nghi.

**Đã sửa:**

- `90-domain/sp1-backend.md` — viết lại **trọn** dòng `guest_elf_sha256`: docker mode + `tag` giải quyết được tái lập giữa các máy (5 workspace ra cùng sha256 trên hai máy khác hệ điều hành), kèm ba bẫy vận hành (mount một thư mục → soát phụ thuộc đệ quy; build bằng root; ELF nằm ở nhánh `docker/`). Hai giả thuyết cũ ghi rõ là **đã bị bác bỏ** để không ai dựng lại. Dòng prover: cả tám host nay đọc `SP1_CUDA`, kèm hai ràng buộc kiểu mà dạng generic bắt buộc (`Prover` có associated type; `P::Error` không phải `StdError`). Dòng coverage cập nhật theo bảng hiện tại.
- `90-domain/experiments.md` — 154M → **211M** mỗi proof con (hiệu ứng `overflow-checks`); thêm ba dòng vận hành: `rc=0` **không** chứng minh provenance đã làm mới (so `guest_elf_sha256` với ELF vừa build), thư mục làm việc của cây đặt tên chỉ theo target nên ghi đè mất tham số lá (mỗi môi trường một `--out-root`; khôi phục bằng `config_hash`), và ba thứ chặn một lượt thuê máy (dataset gitignore, khoá EC2 mất, hết chỗ theo AZ) cộng `zk-idle.service`.
- `90-domain/relations.md` — giá một lần `model_commitment` (26.800 + 1.311 cycles mỗi tham số) và cách cắt **đúng**: thay hash bằng so sánh cấu trúc với bước trước, không phải bỏ hash rồi mang giá trị sang.
- `rules/00` — ước lượng phải nói suy từ đâu, kèm ba lối suy đã sai thật (tỉ lệ tổng từ thành phần con; nhịp cây nhỏ suy ra cây lớn; cảnh báo cũng là ước lượng).
- `rules/30-kiem-thu.md` — cổng tương đương cuối phải chạy trên **lá thật của cây**, 22 giây Python, trước khi tiêu tiền GPU.
- `CLAUDE.md` — bất biến 1: phép nhân là `div_trunc_zero` (cắt về 0), không phải `//` của Python; bất biến 6: trỏ định lý bằng **label**, và `thm:manifest-aggregation` nay gồm cây tới T=4992.
- `90-domain/paper-claims.md` — bỏ "Theorem 7 = proof-manifest chain", thay bằng phát biểu theo label và phân biệt hai chế độ.

**Gộp:** năm mục về ELF/docker/toolchain vào **một** dòng `guest_elf_sha256` thay vì thêm bốn dòng mới — chúng là cùng một câu chuyện và mục sau bác bỏ mục trước. Hai mục về ước lượng sai gộp vào một vế của `rules/00`.

**Bỏ:** mục 2026-09-12 do `capture_learning.py` tự bắt ("ý tôi là bạn tự research ý tưởng luôn ý") — chỉ thị một lần cho một phiên, không phải quy ước.

**Không lên thang hook:** cổng so `guest_elf_sha256` với ELF vừa build đáng làm nhưng phải biết đường dẫn ELF của từng relation và chỉ có nghĩa ngay sau một lượt prove, nên nó là bước trong script phiên máy chứ không phải PreToolUse.

**Còn ngỏ:** cho `build_deck.py` đọc thẳng `table2_zk_proof_cost.csv` thay vì chép tay (nay đã có `tests/unit/test_docs_numbers_match_artifacts.py` chặn số chết, nhưng chưa bỏ được trùng lặp).

## 2026-09-10 — 1.8.0

**Kích hoạt:** phiên viết lại paper theo artifact. Ba mục tồn đọng: hai về hash guest ELF, một là thất bại lặp chưa từng được ghi dù đã gây bốn lỗi trong cùng một phiên.

**Lý do:** cả ba đều là bẫy **im lặng** — không có lỗi build, không có test đỏ, kết quả trông vẫn hợp lệ. Đó đúng là loại chỉ rule mới chặn được.

**Đã sửa:**

- `90-domain/sp1-backend.md`: mục "Còn ngỏ" của 1.7.0 về `--remap-path-prefix` nay có câu trả lời **một nửa** — cờ đó xoá được đường dẫn khỏi nội dung ELF (`strings`: `/zk_offline_dqn` 1 lần, `/home/ubuntu/alpha` 0 lần) nhưng hai ELF **vẫn khác hash**, nên không đủ để hash đi được giữa các máy. Nguyên nhân vẫn là giả thuyết chưa kiểm; `BuildArgs { docker: true }` chưa thử. Cùng dòng, thêm bẫy cache: `sp1_build` chỉ dựng lại khi nguồn **guest** đổi, nên sửa `build.rs` của host rồi so ELF ngay là đọc lại binary của lượt trước — phải xoá `guest/elf/` trong cây nguồn.
- `rules/00`: cấm heredoc cho nội dung có backslash. Công cụ Bash ăn một tầng, và hậu quả không lộ ra ở chỗ gây lỗi: `\\` cuối dòng bảng LaTeX thành `\` báo `Misplaced \noalign` ở dòng khác, còn `\texttt` thành TAB + `exttt` thì **compile sạch** và chỉ lộ khi đọc PDF.

**Gộp:** hai mục ELF (cache trap và remap) vào cùng một dòng `guest_elf_sha256`, vì mục sau sửa mệnh đề cuối của dòng cũ. Bỏ vế "grep phải quét cả thư mục con" — đã phủ bởi `rules/00` "Đọc trước khi viết"; giữ con trỏ cụ thể `command/utils.rs:77`.

**Không lên thang hook:** một PreToolUse chặn heredoc-có-backslash sẽ báo giả với `echo "\n"` thường gặp, nên dừng ở rung rule.

**Còn ngỏ:** thử `BuildArgs { docker: true }` để quyết A/B/C cho dòng t4992 của Bảng 2; cho `check_public_dataset_coverage` gọi `verify_dataset_commitment`.

## 2026-09-08 — 1.7.0

**Kích hoạt:** một phiên "làm hết 6 mục" nở thành 3 lượt GPU, một lần chạy lại Bảng 1, và 12 mục inbox tồn đọng từ 06-09 tới 07-09.

**Lý do:** mỗi mục được giao lại lộ ra một lỗi mới, và lỗi nào cũng được sửa ngay tại chỗ thay vì ghi lại rồi hỏi. Phạm vi trôi, ngân sách trôi theo, và một trong các "bản sửa" tự nó là lỗi mới.

**Đã sửa:**

- `rules/00`: mục **Không trôi khỏi phạm vi**. Phát hiện giữa chừng thì ghi INBOX, chỉ sửa khi nó làm sai thứ vừa tạo ra trong chính lượt đó hoặc khi miễn phí. Mỗi lượt một phiên GPU; phiên thứ hai phải hỏi. Trước khi sửa một con số đã công bố, đọc file cấu hình đã sinh ra nó chứ không đọc hằng số trong code — đọc `PROVED_SGD_LEARNING_RATE = 0.01` rồi kết luận ngược với `sgd_learning_rate = 0.05` trong `table1_rl_performance_status.json` đã làm hỏng kết quả hoà 12–12 và tốn thêm một lượt prove.
- `90-domain/sp1-backend.md`: `overflow-checks` đặt ở gốc workspace (guest là member nên profile ở guest bị bỏ qua im lặng), chi phí không đồng đều +0,33%…+36,8%; `guest_elf_sha256` định danh lần build chứ không phải mã nguồn, phụ thuộc đường dẫn; sửa lại dòng `SP1_CUDA` cho đúng hai host có feature và sáu host ghi `prover: cpu`.
- `90-domain/relations.md`: dataset cam kết chính là dataset fixed-point; `sampler_seed` dẫn xuất từ `dataset_root` và `global_step_start`; `q_abs_max_fp` / `gradient_clip_fp` và kết quả ablation — clip gần như miễn phí, batch=1 và sync=4 mới chặn việc học.
- `90-domain/experiments.md`: tách dòng bộ nhớ theo loại proof (fragment tiêu RAM host ~27 byte/cycle, recursion phẳng); groth16 chạy hai bước vì socket; `describe-instances` trước khi thử lại `run-instances`, và không đụng `shutdown` đã hẹn.
- `90-domain/data-pipeline.md`: cổng coverage chỉ kiểm root tồn tại, không kiểm root tự nhất quán.

**Gộp:** hai mục `overflow-checks` (06-09 và 07-09) thành một dòng, vì mục sau sửa số của mục trước — +3,9% chỉ đúng cho `training_fragment`.

**Còn ngỏ:** `--remap-path-prefix` để hash ELF đi được giữa các máy; cho `check_public_dataset_coverage` gọi `verify_dataset_commitment`.

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
