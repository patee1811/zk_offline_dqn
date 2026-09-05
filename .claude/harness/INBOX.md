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
**Đích đề xuất:** đã có trong `rules/90-domain/sp1-backend.md` từ 1.2.0 — hook bắt đúng nhưng trùng bản ghi tay cùng ngày.
**Độ tin cậy:** thấp (tự động, chưa duyệt)
**Trạng thái:** đã áp dụng (1.2.0, trùng)

## 2026-08-30 — thất bại — scope experiments
**Kích hoạt:** instance spot `i-0ec16b5228e081751` chạy 14 giờ rồi biến mất khỏi `describe-instances`. Script có thể đã xong nhưng `memory_profile_ec2.tar.gz` nằm cùng máy.
**Bài học:** spot rẻ hơn ~$1.2 cho 3 giờ, đổi lại AWS thu hồi bất cứ lúc nào. Với việc chạy một lần thì đó là đổi chác tệ. Và kết quả phải rời khỏi máy trước khi máy chết — terminate chỉ sau khi kiểm tarball có trên đĩa.
**Đích đề xuất:** `rules/90-domain/experiments.md`
**Độ tin cậy:** cao (mất một lần chạy thật)
**Trạng thái:** đã áp dụng (1.3.0)

## 2026-08-30 — thất bại — scope backends
**Kích hoạt:** hai arm `wide_tree` và `both` panic sau 1–3 giây với `arity not supported`, sau khi đặt `SP1_WORKER_MAX_COMPOSE_ARITY=10`.
**Bài học:** biến đó tồn tại và được `env::var` đọc, nhưng `compress_proof_shape_from_arity` (`sp1-prover-6.1.0/src/shapes.rs:190`) chỉ khớp `DEFAULT_ARITY = 4`, mọi giá trị khác trả `None` rồi `.expect()` panic. Cách arity-10 của SUMMER không chuyển sang SP1 được.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md`
**Độ tin cậy:** cao (đọc mã nguồn 6.1.0 + hai lần panic)
**Trạng thái:** đã áp dụng (1.3.0)

## 2026-08-30 — phát hiện mới — scope experiments
**Kích hoạt:** sweep bốn cấu hình recursion: T=8 (1 child) 30399MB, T=16 (2 child) 29612MB, T=32 (4 child) 29255MB.
**Bài học:** đỉnh RSS không tương quan với số proof con — giả thuyết "làm nhỏ dữ liệu để lách trần" sai. Chi phí nằm ở việc dựng mạch recursion của SP1, phát sinh dù gộp một hay bốn proof.
**Đích đề xuất:** `rules/90-domain/experiments.md`
**Độ tin cậy:** cao (bốn phép đo)
**Trạng thái:** đã áp dụng (1.3.0)

## 2026-08-30 — thất bại — scope harness
**Kích hoạt:** một lệnh `cd .claude` làm cwd phiên đổi, và cả bảy hook chết với `can't open file ...\.claude\.claude\hooks\...`. Hook fail thì chặn cả Bash lẫn Edit — không sửa được bằng chính hai công cụ đó.
**Bài học:** `"command": "python .claude/hooks/x.py"` phân giải theo cwd phiên, không phải repo root. Tài liệu chính thức dùng `$CLAUDE_PROJECT_DIR`, biến này Claude Code luôn đặt về root. Đã sửa cả bảy.
**Đích đề xuất:** `.claude/settings.json` (đã áp dụng); `rules/60-bao-tri-harness.md`
**Độ tin cậy:** cao (tự khóa mình một lần, xác minh bằng docs hooks-guide)
**Trạng thái:** đã áp dụng (1.3.1)

## 2026-08-30 — phát hiện mới — scope backends
**Kích hoạt:** chạy lại vector đã commit dưới `cargo-prove 92b8eab`: `training_aggregation_t32` cho 798811 so với 785786 ghi ở `713544d` (+1.66%); `short_trace` cho 115324 so với 115363 (−0.03%). Output relation khớp cả hai.
**Bài học:** `cycle_count` tất định theo cặp `(guest ELF, input)`. Provenance chỉ khóa input; không có `rust-toolchain.toml` nào, `sp1up` luôn cài toolchain mới nhất, và `sp1_version` là chuỗi hardcode ghi phiên bản crate. Đã thêm `guest_elf_sha256` vào cả 7 host. Pin toolchain: `sp1up --version v6.1.0`.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md`
**Độ tin cậy:** cao (hai phép đo + `sha256sum` ELF khớp field ghi ra)
**Trạng thái:** đã áp dụng (1.4.0)

## 2026-08-31 — phát hiện mới — scope backends
**Kích hoạt:** recursion native chạy được trên A10G (CC 8.6, 23GB VRAM) ở T=16/32/64 phẳng và T=16 cây nhị phân, đỉnh 18.4GB VRAM không đổi qua 20 lần chênh lệch cycles; CPU không hoàn tất trong 61GB.
**Bài học:** dòng "Prover chạy **CPU**: cả tám host hardcode `ProverClient::builder().cpu()`, không có feature `cuda`. Nút thắt là RAM CPU, không phải VRAM" nay sai với `training_aggregation` (đã có `SP1_CUDA=1`). Nút thắt là **hằng số dựng mạch recursion**, không phải khối lượng: >61GB trên RAM host, 18.4GB trên VRAM. `sp1-cuda` 6.1.0 **không cần Docker** — tải `sp1-gpu-server` rồi nối qua Unix socket. Yêu cầu: CC ≥ 8.0, ≥24GB VRAM.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md` dòng 18
**Độ tin cậy:** cao (6 phép đo, hai tô-pô, hai chế độ child proof)
**Trạng thái:** đã áp dụng (1.4.0)

## 2026-08-31 — thất bại — scope experiments
**Kích hoạt:** gọi host aggregation trực tiếp để sinh provenance recursion; test `test_recursive_committed_provenance_if_present_is_complete` fail vì thiếu `tamper_report.json`. Phải chạy lại 4 giờ máy GPU.
**Bài học:** provenance phải sinh qua script phase (`run_phase7 --run-prove`), không gọi host trực tiếp — chỉ script phase mới chạy vòng quét tamper. Ngoài ra `--out-dir` tương đối phân giải theo cwd của cargo nên rơi vào `zk_backend/<rel>/sp1/artifacts/...`; luôn truyền đường tuyệt đối.
**Đích đề xuất:** `rules/90-domain/experiments.md`
**Độ tin cậy:** cao (mất một lượt chạy)
**Trạng thái:** đã áp dụng (1.4.0)

## 2026-09-02 — phát hiện mới — scope backends
**Kích hoạt:** việc 0.2 tổng quát hóa cây gộp. Cân nhắc đổi arity 2 sang 8 để rẻ hơn, rồi đọc schema mới thấy sáu field `left_/right_child_{public_values,proof,vkey}_hash` là public input.
**Bài học:** repo có **hai** thứ tên arity. Arity nén nội bộ SP1 cố định ở 4 (đã ghi từ 1.3.0). Arity cây gộp cố định ở 2 và nằm trong schema — đổi nó là migration + vô hiệu provenance đã commit, không phải chỉnh tham số. Độ sâu thì tự do sau khi nới `leaf_chunk_count` thành mọi lũy thừa 2 ≥ 2.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md` — gộp vào dòng arity cũ.
**Độ tin cậy:** cao (đọc `relations/training_aggregation.py:250-255` + `shared/src/lib.rs`)
**Trạng thái:** đã áp dụng (1.5.0)

## 2026-09-02 — phát hiện mới — scope experiments
**Kích hoạt:** prove cây T=128 sâu 4 cho 309.951.502 cycles với 2 proof con, khớp các dòng 2/4/8 con đã đo.
**Bài học:** cycles recursion ≈ 154M mỗi lượt verify con, tuyến tính và độc lập với độ sâu — giữ nguyên cả khi proof con chính là proof đệ quy, không chỉ proof lá. Cây N lá arity a có a(N−1)/(a−1) lượt verify, nên ước được chi phí trên giấy trước khi thuê máy. Đây là mặt đối lập của luật bộ nhớ phẳng đã ghi ở 1.3.0/1.4.0.
**Đích đề xuất:** `rules/90-domain/experiments.md` — siết chung một dòng với luật bộ nhớ.
**Độ tin cậy:** cao (4 phép đo, hai tô-pô, khớp trong 0,5%)
**Trạng thái:** đã áp dụng (1.5.0)

## 2026-09-02 — thất bại — scope backends
**Kích hoạt:** nới `leaf_chunk_count` trong `shared/src/lib.rs` làm đổi guest ELF. Tôi báo cáo "3 dòng bị ảnh hưởng" sau khi chỉ nhìn các thư mục tên `*recursive*`; quét lại cả relation thì ra **8** dòng, gồm cả 3 dòng manifest chain.
**Bài học:** mọi dòng dùng chung một guest đều trôi `guest_elf_sha256`, không riêng nhánh vừa sửa. Quét theo relation, đừng quét theo tên thư mục khớp với thay đổi. Ngoài ra `git archive` trên Windows áp `core.autocrlf` nên hash witness schema lệch — dùng `git -c core.autocrlf=false -c core.eol=lf archive`.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md`
**Độ tin cậy:** cao (báo sai một lần, sửa bằng cách quét toàn relation)
**Trạng thái:** đã áp dụng (1.5.0)

## 2026-09-02 — thất bại — scope backends
**Kích hoạt:** lượt prove lại đặt `SP1_CUDA=1` cho tất cả. Ba dòng manifest chain rơi từ 32,5/39,2/47,8s xuống 1,4/1,7/2,4s — không phải relation nhanh lên mà vì số cũ đo trên CPU. Ghi thẳng vào Table 2 sẽ trộn hai loại phần cứng trong một cột.
**Bài học:** `SP1_CUDA` im lặng theo cả hai chiều. Host không có feature: bỏ qua biến, chạy CPU, GPU đứng im 0% (16 proof lá mất ~6 phút/lá). Host có feature: đổi phần cứng của phép đo mà output không ghi lại, kết quả trông vẫn hợp lệ nhưng không so được với số đã commit. Chiều thứ hai nguy hiểm hơn. Kiểm `nvidia-smi`, đừng tin biến môi trường.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md` dòng prover
**Độ tin cậy:** cao (quan sát cả hai chiều trong cùng một phiên)
**Trạng thái:** đã áp dụng (1.5.0)

## 2026-09-05 — người sửa — scope harness
**Kích hoạt:** người dùng sửa lại trong phiên
**Bài học:** cứ đọc kỹ hết các phần đi, rồi nghiên cứu so sánh các giải pháp, techstack ở từng mục, công đoạn 1 xem phần đó có thể làm tốt hơn không, tự đưa ra phản biện, rồi tự research trên mạng, xong update 1 plan thật chuẩn, tối ưu để mỗi bước làm không phải dò đường, mạnh nộp được A*/Q1 nhưng vẫn trong khả…
**Đích đề xuất:** /harness-sync quyết định
**Độ tin cậy:** thấp (tự động, chưa duyệt)
**Trạng thái:** bỏ (chỉ thị một lần, không phải luật)

## 2026-09-05 — người sửa — scope harness
**Kích hoạt:** người dùng sửa lại trong phiên
**Bài học:** đấy, phần nào cũng phải kiểm tra kĩ, có thông số đang hoàng, không được đonas bừa, đừng làm mất thời gian của tôi, làm bước 1,2 đi
**Đích đề xuất:** /harness-sync quyết định
**Độ tin cậy:** thấp (tự động, chưa duyệt)
**Trạng thái:** bỏ (đã phủ bởi rules/00 và rules/20)

## 2026-09-05 — phát hiện mới — scope data
**Kích hoạt:** `collect_audited_dataset.py` nay nhận `--policy checkpoint` (medium/expert từ `artifacts/source_policies/`), nhưng `rules/90-domain/data-pipeline.md` vẫn ghi "Phase 2 collect chỉ `--policy random`. Policy khác → `ValueError`".
**Bài học:** rule mô tả sai cổng hiện tại. `policy_hash` giờ commit SHA256 checkpoint + epsilon, nên dòng rule cần nói: policy hợp lệ là `random` hoặc `checkpoint`, và checkpoint phải vào `policy_hash` chứ không chỉ vào `policy_type`.
**Đích đề xuất:** `rules/90-domain/data-pipeline.md` dòng 2
**Độ tin cậy:** cao (đọc `collect_audited_dataset.py:65-68,131-145`)
**Trạng thái:** đã áp dụng (1.6.0)

## 2026-09-05 — phát hiện mới — scope rl
**Kích hoạt:** DQN online 200.000 bước trên MountainCar-v0 cho mọi checkpoint đúng −200,0 (1000 episode, không lần nào chạm cờ).
**Bài học:** MountainCar cần reward shaping / n-step / exploration khác thì DQN vanilla mới học được; ngân sách bước không cứu được. Nó không sinh nổi cặp medium/expert phân biệt, nên không dùng làm môi trường nguồn. Trùng với quyết định của plan là bỏ MountainCar.
**Đích đề xuất:** `rules/90-domain/data-pipeline.md` hoặc bỏ khỏi `ENV_BUDGET`
**Độ tin cậy:** cao (10 checkpoint, chấm trên return huấn luyện)
**Trạng thái:** đã áp dụng (1.6.0)

## 2026-09-05 — phát hiện mới — scope data
**Kích hoạt:** đối chiếu `merkle_root` từng dòng Table 1 với `artifacts/datasets/<id>/dataset_manifest.json`. Hai dòng self-collected **lệch**: cartpole-random-v1 báo n=9204 root=`33c743f3…` còn artifact đã commit là n=986 root=`24a45b12…`; mountaincar-random-v1 báo n=10000 root=`982a14e2…` còn artifact commit là n=2000 root=`a0274f16…`. Bốn dòng Minari (`…-100000`, `…dense-…`) không có dataset commit nào.
**Bài học:** `ensure_self_collected_dataset` chỉ thu thập lại khi `validate_phase2_dataset` fail, và thu vào `dataset_root` do lần chạy truyền, với `target_transitions` của sweep. Nên số ở cột Transitions và `merkle_root` của Table 1 là của dataset sinh lúc chạy, không phải dataset trong repo. Reviewer lần theo `merkle_root` sẽ không tìm thấy nó ở đâu cả. Chạy lại Table 1 phải trỏ benchmark vào `artifacts/datasets/` hoặc commit đúng dataset đã dùng.
**Đích đề xuất:** `rules/90-domain/data-pipeline.md`; sửa `run_phase8_1_rl_benchmark.py` / `datasets.py`
**Độ tin cậy:** cao (so 8 dataset_id, 2 lệch, 2 khớp, 4 thiếu)
**Trạng thái:** đã áp dụng (1.6.0)
