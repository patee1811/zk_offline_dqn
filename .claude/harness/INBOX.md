# Harness inbox

Append-only. `/harness-sync` merges approved items. Do not edit rules from here.

Format:

```markdown
## YYYY-MM-DD — người sửa|phát hiện mới|thất bại — scope <scope>
**Kích hoạt:** …
**Bài học:** …
**Đích đề xuất:** …
**Độ tin cậy:** cao|trung|thấp
**Trạng thái:** đã áp dụng (1.7.0)
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

## 2026-09-06 — phát hiện mới — scope data
**Kích hoạt:** `verify_dataset_commitment` trả `False` cho `minari-pointmaze-umaze-v2-10000` và `-50000` với lỗi `manifest_hash mismatch for normalized dataset_manifest.json`. Chạy lại trên code chưa sửa cho thông báo giống hệt — lỗi có sẵn, không do đổi quy tắc lá.
**Bài học:** manifest bị ghi sau khi `merkle_tree.json` đã chốt `manifest_hash`, nên hai file lệch nhau. Hai dataset này chống lưng cho ba dòng `merkle_membership` của Table 2 mà **không cổng nào chạy `verify_dataset_commitment`** — cổng chỉ kiểm sự tồn tại của root, không kiểm root còn tự nhất quán không. Commit lại là hết, root không đổi.
**Đích đề xuất:** `rules/90-domain/data-pipeline.md`; cân nhắc cho `check_public_dataset_coverage` gọi `verify_dataset_commitment`
**Độ tin cậy:** cao (đối chiếu trước/sau khi sửa code, hai dataset)
**Trạng thái:** đã áp dụng (1.7.0)

## 2026-09-06 — phát hiện mới — scope relations
**Kích hoạt:** dataset cam kết bằng `sha256(canonical_json(transition))` còn quan hệ băm số nguyên fixed-point. Trên cartpole-expert-v2: root `88cb5f28` so với `02de61a9` trên cùng 50.261 transition.
**Bài học:** hai quan hệ trung tâm cam kết vào hai vật thể khác nhau — `merkle_membership` kiểm cây JSON, `training_fragment` kiểm cây fixed-point — và không gì công bố gốc fixed-point, nên prover tự chọn được cây mình đã huấn luyện. Cách sửa theo Garg và cộng sự (CCS 2023): dataset cam kết **chính là** dataset fixed-point. Lá liên tục (PointMaze) không biểu diễn được nên giữ quy tắc JSON, ghi theo từng dataset ở `leaf_hash_rule`.
**Đích đề xuất:** `rules/90-domain/relations.md` hoặc `data-pipeline.md`
**Độ tin cậy:** cao (đối chiếu 3.000 transition, khớp cả bản Rust trong guest)
**Trạng thái:** đã áp dụng (1.7.0)

## 2026-09-06 — thất bại — scope experiments
**Kích hoạt:** prove một lá `training_fragment` 504.115.089 cycles trên g5.xlarge. `CudaClientError: early eof`; `dmesg` cho `Out of memory: Killed process 2810 (sp1-gpu-server)` với `anon-rss 4,65GB + shmem-rss 8,91GB ≈ 13,5GB` trên máy 15GB, trong khi **VRAM dùng 0 MiB**.
**Bài học:** dòng "recursion: bộ nhớ phẳng, VRAM 18,4GB không đổi" **chỉ đúng cho proof đệ quy**. Proof `training_fragment` thì bộ nhớ tăng theo cycles và tiêu **RAM máy chủ**, không phải VRAM — nút thắt nằm ở `sp1-gpu-server`, một tiến trình riêng, nên peak RSS của host chỉ báo 1,5GB và không hề lộ nguyên nhân. Chọn máy cho phase 3 phải theo RAM chứ không theo VRAM. Ngoại suy từ điểm OOM này: ~27 byte mỗi cycle.
**Đích đề xuất:** `rules/90-domain/experiments.md` — tách dòng bộ nhớ recursion thành hai vế theo loại proof
**Độ tin cậy:** cao (dmesg trực tiếp, VRAM 0 MiB xác nhận không phải GPU)
**Trạng thái:** đã áp dụng (1.7.0)

## 2026-09-06 — thất bại — scope experiments
**Kích hoạt:** `aws ec2 run-instances` trả `Connection was closed before we received a valid response from endpoint URL` — không biết máy đã tạo hay chưa. Sau đó `sudo shutdown -c` rồi `sudo shutdown -h +45` làm máy tắt **ngay lập tức** thay vì sau 45 phút.
**Bài học:** lệnh launch chết giữa chừng phải **kiểm `describe-instances` trước khi thử lại**, nếu không sẽ có hai máy GPU cùng chạy mà chỉ theo dõi một. Và đừng đụng vào `shutdown` đã hẹn từ user-data: huỷ rồi đặt lại làm máy tắt ngay, mất phần việc còn dở. Đặt hẹn một lần trong user-data rồi để yên.
**Độ tin cậy:** cao (quan sát cả hai lỗi trong một phiên)
**Đích đề xuất:** `rules/90-domain/experiments.md` dòng máy thuê
**Trạng thái:** đã áp dụng (1.7.0)

## 2026-09-07 — phát hiện mới — scope backends
**Kích hoạt:** guest tràn i64 im lặng vì Cargo release để `overflow-checks = false`. Đặt `[profile.release] overflow-checks = true` ở gốc workspace `zk_backend/<rel>/sp1/Cargo.toml` thì guest abort đúng chỗ: `panicked at shared/src/lib.rs:1044: attempt to multiply with overflow`. Chi phí đo được **+3,9% cycles** trên `training_fragment` (609.970.390 → 633.997.073).
**Bài học:** hướng dẫn bảo mật SP1 bảo đặt vào `Cargo.toml` của **guest package** — đúng với template standalone nhưng ở repo này guest là **member workspace** nên Cargo bỏ qua kèm cảnh báo `profiles for the non root package will be ignored`, tức là im lặng không có tác dụng. `sp1_build::get_program_build_args` cứng `build --release` không ghi đè profile, và chạy cargo với `current_dir` = thư mục guest nên nó tìm lên gốc workspace. Kiểm bằng cách chạy cargo từ trong `guest/` và xem `-C overflow-checks=on` có tới rustc không.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md`; đã có `tests/unit/test_guest_overflow_checks.py` khoá cả hai nửa
**Độ tin cậy:** cao (thử nghiệm cả hai chiều + panic thật trên guest riscv32im)
**Trạng thái:** đã áp dụng (1.7.0)

## 2026-09-07 — phát hiện mới — scope relations
**Kích hoạt:** đo giá trị Q qua chuỗi CartPole ở `learning_rate_fp=50`, mỗi chunk 156 bước: 5,50e4 → 9,46e5 → 2,17e7 → 9,03e8 → 2,17e10 → 9,45e11 → 3,96e13 → 9,49e14 → **4,14e16**. Ngưỡng tràn là 9,32e15 (i64::MAX / gamma).
**Bài học:** offline DQN phân kỳ theo **hàm mũ**, khoảng ×22 mỗi 156 bước, nên độ dài lần chạy chứng minh được bị chặn bởi **ổn định số học** chứ không phải chi phí proof. Đo trên 4992 bước: CartPole vỡ ở `lr_fp=10` (bước 3744), sống ở `lr_fp=5` (7,2% ngưỡng) và `lr_fp=1`; LunarLander sống ở cả ba. Ngoài ra `agents.py` cắt gradient (`clip_grad_norm_ 10.0`) còn quan hệ **không** — Bảng 1 và quan hệ đang chạy hai thuật toán khác nhau.
**Đích đề xuất:** `rules/90-domain/relations.md`; cân nhắc thêm biên tường minh vào quan hệ
**Độ tin cậy:** cao (mô phỏng đầy đủ 32 chunk, hai môi trường, ba learning rate)
**Trạng thái:** đã áp dụng (1.7.0)

## 2026-09-07 — phát hiện mới — scope experiments
**Kích hoạt:** `training-aggregation-host` chế độ `--child-proof-mode groth16_bn254` chết 4 lần liên tiếp ở bước prove tổng hợp: `Failed to create the CUDA prover impl: ConnectionRefused ... Could not connect to sp1-gpu-server socket`. Mỗi child proof tự dựng rồi bỏ lại `/tmp/sp1-cuda-0.sock`; server sau không bind được đường đã tồn tại, client nối vào socket chết. Watchdog xoá socket mỗi 0,5s vẫn hỏng (486s), nhưng gọi host **một mình** thì qua ngay (2216s, `proof_verified = true`).
**Bài học:** không phải mỗi file socket cũ — server của child groth16 vẫn đang tắt dở khi host tổng hợp khởi động. Cách chạy: để `run_phase7 ... --run-child-proves` sinh child + `tamper_report.json`, chấp nhận nó hỏng ở prove cuối, rồi gọi host trực tiếp cho **riêng** bước tổng hợp. `write_provenance` không đụng `tamper_report.json` nên fixture vẫn đủ. Chỉ groth16 dính; `native_sp1` chạy trọn qua phase script.
**Đích đề xuất:** `rules/90-domain/experiments.md` dòng recursion
**Độ tin cậy:** cao (4 lần hỏng, 2 lần qua, cùng một máy)
**Trạng thái:** đã áp dụng (1.7.0)

## 2026-09-07 — sửa số cũ — scope backends
**Kích hoạt:** đo `overflow-checks = true` trên đủ 8 quan hệ, không chỉ `training_fragment`.
**Bài học:** con số **+3,9%** trong mục ngày 06-09 chỉ đúng cho `training_fragment`; chi phí **không đồng đều**: `training_fragment`/`training_update` +3,6%…+7,2%, `merkle_membership` +13,0%…+17,7%, recursion phẳng và cây nhị phân **+36,8%** (verify child proof trong guest nặng số học nhất), groth16 **+0,33%** (cycles do BN254 chi phối, không phải số học fixed-point). Tổng Bảng 2: 8,66G → 9,58G cycles, **+10,7%**. Đừng trích một con số cho cả bảng.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md`, cùng chỗ với mục overflow-checks
**Độ tin cậy:** cao (23 dòng proof_verified, đối chiếu từng dòng với bảng đã commit)
**Trạng thái:** đã áp dụng (1.7.0)

## 2026-09-07 — lỗi nghiêm trọng — scope relations
**Kích hoạt:** `generate_case` dùng `sampler_seed` hằng số và `step_id` đếm **trong nội bộ fragment**, nên mọi chunk của một chuỗi rút đúng cùng một tập chỉ số. Đo trực tiếp: chunk 0 (bước 0–7) và chunk 1 (bước 8–15) đều ra `[68, 83, 22, 125, 56, 55, 42, 1]`.
**Bài học:** chuỗi 1248 bước thực chất là **156 lần lặp trên 8 dòng** của dataset 50k, không phải một lượt quét dữ liệu — claim "train trên dataset đã cam kết" bị rỗng ruột mà không test nào bắt. Nay `sampler_seed = H(dataset_root, global_step_start)`, vừa chặn prover tự chọn seed (Tan et al. 2025) vừa buộc các chunk rút khác nhau. Có test hồi quy `test_chunks_of_one_chain_draw_different_transitions`.
**Đích đề xuất:** `rules/90-domain/relations.md` dòng aggregation
**Độ tin cậy:** cao (so sánh trực tiếp code cũ/mới trên cùng đầu vào)
**Trạng thái:** đã áp dụng (1.7.0)

## 2026-09-07 — phát hiện mới — scope backends
**Kích hoạt:** `forward_td_mlp` và `one_step_sgd_tiny` đổi `guest_elf_sha256` dù chỉ sửa host. Build lại tại chỗ cho **cùng** hash (tất định), nhưng cùng nguồn build ở `~/repo8` ra `b1e7a69d` còn ở `~/repo9` ra `1e2a8a38`.
**Bài học:** `guest_elf_sha256` định danh **lần build**, không phải mã nguồn — nó phụ thuộc đường dẫn build. Hai guest này là hai guest duy nhất có path dependency ra ngoài workspace (`td-mvp-shared`). Hệ quả: cổng `test_table2_guest_consistency` vẫn đúng mục đích (bắt việc chỉ prove lại một nửa, vì cùng lượt thì cùng đường dẫn), nhưng **không được** dùng hash ELF công bố như mỏ neo tái lập cho reviewer build từ clone sạch. Muốn hash đi được thì cần `RUSTFLAGS=--remap-path-prefix`.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md`
**Độ tin cậy:** cao (build lại 2 lần cùng chỗ + 1 lần khác đường dẫn)
**Trạng thái:** đã áp dụng (1.7.0)

## 2026-09-07 — phát hiện mới — scope rl
**Kích hoạt:** control D tách ba khác biệt giữa Bảng 1 tinh chỉnh và cấu hình quan hệ, trên cartpole-random, 5000 bước, 1 seed: tuned 78,0 → clip-by-value 75,4 → sync 4 **9,4** → batch 1 **9,4** → cả ba **9,4**.
**Bài học:** phép thay clipping mà chứng minh bắt buộc phải làm gần như **miễn phí**; thứ chặn việc học là **batch=1** và **chu kỳ đồng bộ target = 4**, mỗi cái độc lập đủ kéo về mức chính sách chưa học (9,4 trên CartPole). Nên lộ trình quan hệ kế tiếp là **batching và sync dài hơn**, không phải Adam — trái với thứ tự mục Limitations đang gợi ý.
**Đích đề xuất:** `rules/90-domain/relations.md`; `paper/sections/discussion.tex` khi viết lại Limitations
**Độ tin cậy:** trung bình cao (1 seed, 6 dataset; xu hướng nhất quán, biên độ chưa lấy trung bình nhiều seed)
**Trạng thái:** đã áp dụng (1.7.0)

## 2026-09-09 — thất bại — scope backends
**Kích hoạt:** `sp1_build` chỉ dựng lại guest khi **nguồn guest** đổi. Sửa `build.rs` của host không tính, nên phép so ELF hai đường dẫn đọc lại ELF cache của lượt trước và cho kết luận sai (`training_aggregation` ra đúng hash cũ của lần chạy trước đó). Cùng lượt, một `grep` trên `sp1-build/src/*.rs` bỏ sót `src/command/` và suýt kết luận `rustflags` là trường chết — thực ra nó được dùng ở `command/utils.rs:77`.
**Bài học:** muốn so ELF thì phải **xoá `guest/elf/` trong cây nguồn** trước, không chỉ xoá `CARGO_TARGET_DIR`. Và grep vào một crate phải quét cả thư mục con, không chỉ tầng `src/*.rs`.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md`, cùng chỗ với mục `guest_elf_sha256`
**Độ tin cậy:** cao (hash trùng khít lượt trước là bằng chứng trực tiếp)
**Trạng thái:** đã áp dụng (1.8.0)

## 2026-09-09 — phát hiện mới — scope backends
**Kích hoạt:** `--remap-path-prefix` truyền qua `BuildArgs.rustflags` **có** tác dụng: `strings` trên ELF cho `/zk_offline_dqn` 1 lần và `/home/ubuntu/alpha` 0 lần, ngược hẳn trước khi sửa. Nhưng hai ELF **vẫn khác hash**, trong khi mọi chuỗi đường dẫn còn lại giống hệt nhau.
**Bài học:** xoá đường dẫn khỏi nội dung ELF là **chưa đủ** để hash đi được giữa các máy. Giả thuyết chưa kiểm: chính cờ remap khác nhau giữa hai lượt build và cargo băm cờ vào metadata. Đường được `sp1_build` quảng cáo cho việc này là `BuildArgs { docker: true }` — *"Run compilation using a Docker container for reproducible builds"* — chưa thử.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md`
**Độ tin cậy:** cao cho phần đo; **giả thuyết nguyên nhân chưa kiểm chứng**
**Trạng thái:** đã áp dụng (1.8.0)

## 2026-09-09 — thất bại lặp — scope harness
**Kích hoạt:** heredoc `<<'PY'` của công cụ Bash ăn mất một tầng backslash. Bốn hậu quả trong một phiên: `flags.join("\x1f")` thành `join("")`; `\\` cuối dòng bảng LaTeX thành `\` (LaTeX báo `Misplaced \noalign` ở dòng *khác*); `\ref` thành ký tự CR làm vỡ dòng; và `\texttt` thành TAB + `exttt`, **compile sạch nên PDF in ra chữ `exttt{...}`**.
**Bài học:** không dùng heredoc cho nội dung có backslash — LaTeX, Rust, regex. Ghi script ra file bằng Write rồi `python <file>`. Trong regex Python phải `re.escape(chr(92))`, không viết `"\\c..."` trong heredoc. Lỗi loại này **không** làm build đỏ, nên cần một phép kiểm riêng: `tests/unit/test_paper_numbers_match_artifacts.py` nay chặn ký tự TAB trong mọi mục paper đang dùng.
**Đích đề xuất:** `rules/00-nguyen-tac-coi-loi.md`
**Độ tin cậy:** cao (bốn lần tái hiện, một lần lọt vào PDF)
**Trạng thái:** đã áp dụng (1.8.0)

## 2026-09-10 — phát hiện mới — scope experiments
**Kích hoạt:** viết lại `docs/giai_thich_toan_canh.md`, đối chiếu mọi con số với Bảng 2 hiện tại. Dòng rule ghi "cycles recursion ≈ 154M mỗi lượt verify con"; Bảng 2 cho `native_flat_recursive` t16/t32/t64 = 422.726.492 / 842.015.859 / 1.683.525.837 với 2/4/8 proof con, tức **211,4 / 210,5 / 210,4 triệu**.
**Bài học:** 154M là số đo **trước** khi bật `overflow-checks`. Recursion chịu chi phí kiểm tràn nặng nhất (+36,8% đã ghi ở dòng khác của cùng file rules), và 154 × 1,368 ≈ 211 — khớp. Cùng lớp lỗi: `23.571 cycles/tầng` của `merkle_membership` nay là **≈ 28.000** (hồi quy trên 4 dòng Bảng 2: 28.088 / 28.130 / 27.522 mỗi tầng), khớp với +17,7% đã ghi. Mọi con số cycles ghi trong rules trước 07-09 cần soát lại theo cùng cách.
**Đích đề xuất:** `rules/90-domain/experiments.md` dòng recursion; và soát dòng Merkle nếu có.
**Độ tin cậy:** cao (tính từ chính bảng đã commit, khớp hệ số +36,8% / +17,7% đã đo độc lập)
**Trạng thái:** đã áp dụng 1.9.0

## 2026-09-10 — phát hiện mới — scope paper
**Kích hoạt:** `CLAUDE.md` bất biến số 6 ghi "**Theorem 7** nay gồm hai chế độ: proof-manifest chain … và recursive_sp1". Đọc `paper/sections/theorems.tex`: thứ tự xuất hiện là 1 replay-membership, 2 dataset-commitment, 3 bellman-target, 4 update-correctness, 5 checkpoint-chain, 6 training-fragment, **7 sampler-binding**, **8 value-bound**, **9 manifest-aggregation**, 10 privacy-boundary.
**Bài học:** chèn hai định lý mới (sampler binding, bounded fixed-point) ở vị trí 7–8 đã đẩy định lý aggregation từ **7 sang 9**. Bất biến trong `CLAUDE.md` còn trỏ số cũ, nên một agent đọc rule rồi đi sửa "Theorem 7" sẽ sửa nhầm định lý. Nên trỏ bằng **label** (`thm:manifest-aggregation`) thay vì số — số định lý trôi mỗi lần chèn.
**Đích đề xuất:** `CLAUDE.md` bất biến 6; cân nhắc quy ước chung "trỏ định lý bằng label, không bằng số".
**Độ tin cậy:** cao (đọc trực tiếp thứ tự `\begin{theorem}` trong `theorems.tex`)
**Trạng thái:** đã áp dụng 1.9.0

## 2026-09-12 — phát hiện mới — scope relations
**Kích hoạt:** đọc lại lớp 2 để giải thích luồng. `CLAUDE.md` bất biến 1 ghi "nhân cố định `(a * b) // fp_scale` — không `round`". Code thật là `div_trunc_zero` (`relations/training_update.py:21`): `sign * (abs(num) // den)`, tức **cắt về phía 0**. Hai quy tắc chỉ trùng nhau khi tích không âm. Ví dụ thật từ `training_fragment_cartpole_expert_k1`: `gamma=990`, `q_target_next=-40` → tích `-39600`. Python `//` cho `-40`, code cho `-39`, và `td_target` đã commit là `961 = 1000 + (-39)`.
**Bài học:** một agent đọc bất biến rồi viết `(a*b) // scale` sẽ lệch 1 đơn vị fixed-point ở **mọi** phép nhân có tích âm — Q âm là chuyện thường trong DQN. Rust `i64` chia cũng cắt về 0, nên bản Rust đang đúng; chỉ câu chữ trong `CLAUDE.md` sai. Nên ghi là "cắt về 0 (`div_trunc_zero`), **không** phải `//` của Python, và không `round`".
**Đích đề xuất:** `CLAUDE.md` bất biến 1; cân nhắc nhắc lại ở `rules/90-domain/relations.md`.
**Độ tin cậy:** cao (đọc `div_trunc_zero` + đối chiếu `td_target` trong vector đã commit)
**Trạng thái:** đã áp dụng 1.9.0

## 2026-09-12 — người sửa — scope harness
**Kích hoạt:** người dùng sửa lại trong phiên
**Bài học:** ý tôi là bạn tự research ý tưởng luôn ý
**Đích đề xuất:** /harness-sync quyết định
**Độ tin cậy:** thấp (tự động, chưa duyệt)
**Trạng thái:** đã áp dụng 1.9.0

## 2026-09-15 — sửa số cũ — scope backends
**Kích hoạt:** chạy G1 thật trong WSL (Ubuntu 26.04, toolchain SP1 `d454975`, target **riscv64im**). Build guest `training_fragment` ở hai đường dẫn dài 26 và 37 ký tự, `build.rs` hiện tại (chỉ remap): **hash giống hệt nhau** — `3fc8ee1240c8cf96…`, 340.168 byte ở cả hai.
**Bài học:** giả thuyết ghi ngày 09-09 — *"chính cờ remap khác nhau giữa hai lượt build và cargo băm cờ vào metadata"* — **sai**. Cờ remap chứa repo root nên khác nhau giữa hai lượt, mà hash không đổi. Sâu hơn: đường dẫn repo **không hề lọt vào ELF** trên toolchain này (`strings` đếm 0 chuỗi chứa đường dẫn repo), nên comment trong `build.rs` — *"Exactly one absolute path reaches the binary"* — đúng với toolchain cũ nhưng **không còn đúng**. Rò rỉ còn lại là **9 đường dẫn cargo registry** dạng `/home/<user>/.cargo/registry/src/…`: giống nhau trên cùng máy, **khác trên máy khác** — đó mới là rào cản tái lập.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md` dòng `guest_elf_sha256`; và sửa comment trong cả 8 `build.rs`.
**Độ tin cậy:** cao (hai lượt build, đối chứng có/không docker, đếm `strings`)
**Trạng thái:** đã áp dụng 1.9.0

## 2026-09-15 — phát hiện mới — scope backends
**Kích hoạt:** `BuildArgs { docker: true }` (`sp1-build-6.1.0/src/lib.rs:41`, mô tả *"Run compilation using a Docker container for reproducible builds"*) build ở hai đường dẫn khác nhau.
**Bài học:** **docker mode giải quyết được tái lập giữa các máy.** Hash giống nhau ở cả hai đường dẫn (`5ef933421e130c04…`, 340.144 byte) và **`/home/<user>` biến mất hoàn toàn** (9 → 0), thay bằng `/root/.sp1/toolchains/…` là đường dẫn cố định trong container. Chi phí: lần đầu **+6m45s** kéo image, lần sau **16 giây**. Hai cảnh báo vận hành: (a) docker build chạy **bằng root**, để lại `target/elf-compilation` thuộc root nên build thường sau đó chết với `Permission denied` — phải xoá bằng `docker run --rm -v … alpine rm -rf` nếu không có sudo; (b) ELF docker nằm ở `target/elf-compilation/**docker**/riscv64im-…`, khác chỗ bản thường.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md`
**Độ tin cậy:** cao (đo trực tiếp, có đối chứng)
**Trạng thái:** đã áp dụng 1.9.0

## 2026-09-15 — phát hiện mới — scope backends
**Kích hoạt:** soát path dependency của cả tám guest để tìm nguyên nhân dòng t4992 lệch hash.
**Bài học:** chỉ **`forward_td_mlp`** và **`one_step_sgd_tiny`** có path dependency ra ngoài workspace (`../../../td_mvp/sp1/shared`). **`training_aggregation` — quan hệ thực sự bị lệch ở dòng t4992 — chỉ có `../shared`**, tức không thuộc nhóm mà ghi chú cũ gán lỗi. Cộng với việc t4992 chạy ở phiên/máy khác và repo **không pin toolchain `succinct`**, nghi vấn hợp lý nhất cho t4992 là **khác phiên bản toolchain**, không phải khác đường dẫn. Bằng chứng gián tiếp: toolchain hiện tại target **riscv64im**, trong khi bản dựng Bảng 2 nhiều khả năng là **riscv32im**. Hệ quả: **pin toolchain** (`rust-toolchain.toml` hoặc `sp1up --version`) là cách sửa **miễn phí** và có thể đúng nguyên nhân hơn docker; hai cách bổ sung nhau chứ không thay thế.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md`; cân nhắc thêm pin toolchain vào repo
**Độ tin cậy:** cao cho phần soát path dependency; **nghi vấn toolchain chưa kiểm trực tiếp** (không có bản ghi toolchain của lượt chạy t4992 — `sp1_version` là chuỗi hardcode)
**Trạng thái:** đã áp dụng 1.9.0

## 2026-09-15 — phát hiện mới — scope backends
**Kích hoạt:** M1c — đo `--execute` ba biến thể của `verify_training_fragment` trên cùng một cây, cùng toolchain. Số lần `model_commitment` mỗi bước: 4 → 3 → 1.
**Bài học:** **một lần `model_commitment` trên mô hình 450 tham số tốn ~617.000 cycles**; trên mô hình 12 tham số tốn ~42.500. Khớp mô hình `26.800 cố định + 1.311 cycles mỗi tham số` — tức **1.311 cycles để băm một tham số**, do render số nguyên thành chuỗi thập phân rồi SHA-256. Với lá thật của cây whole-run (`[4,64,2]`, k=156, 504.115.089 cycles = 3.231.507 mỗi bước), bốn lần gọi chiếm **76% chi phí mỗi bước**. Bỏ 3 trong 4 lần: lá rẻ **2,33×**, cả cây **1,68×** → cùng ngân sách chứng minh được ~8.400 bước thay vì 4.992. Cả sáu lượt đo cho `final_checkpoint_hash` **giống hệt nhau** → bảo toàn ngữ nghĩa xác nhận bằng thực nghiệm. Cảnh báo khi cài đặt thật: biến thể đo đọc giá trị từ witness nên `assert` thành tầm thường và **làm yếu quan hệ**; bản thật phải **mang giá trị đã tính từ bước trước sang**.
**Đích đề xuất:** `rules/90-domain/relations.md` hoặc `sp1-backend.md`; và là cơ sở cho việc sửa `shared/src/lib.rs`
**Độ tin cậy:** cao (hai cách tính giá mỗi lần gọi khớp nhau trong 0,6%; hai cỡ mạng; output bất biến)
**Trạng thái:** đã áp dụng 1.9.0

## 2026-09-15 — thất bại — scope harness
**Kích hoạt:** hai lần trong cùng một phiên tôi đưa ra con số không có phép đo chống lưng, và **cả hai đều sai theo hướng làm hỏng quyết định**.
**Bài học:** (a) Tôi cảnh báo hai lần rằng *"toolchain khác nên cycles sẽ không so được với Bảng 2"*. Đo thật: 4.646.**392** so với 4.646.**677** đã commit — lệch **0,006%**. Cảnh báo quá đà suýt làm vứt bỏ giá trị của cả phép đo. (b) Tôi ước *"lá rẻ đi 2,5–3,5×, cả cây 2–2,5×"* bằng cách suy từ **byte băm**. Đo thật: lá **2,33×**, cả cây **1,68×** — vì phần số học và Merkle path không đổi nên làm loãng tỉ lệ tổng. **Không suy tỉ lệ chi phí tổng từ khối lượng của một thành phần con**; phải đo tổng. Cùng lớp với lỗi "khái quát từ một điểm đo" đã ghi ở 1.7.0.
**Đích đề xuất:** `rules/00-nguyen-tac-coi-loi.md` — mục "Nói rõ mức chắc chắn", thêm vế: ước lượng phải nói rõ nó suy từ đâu, và tỉ lệ tổng chỉ được suy từ phép đo tổng.
**Độ tin cậy:** cao (hai lần trong một phiên, có số đo đối chiếu)
**Trạng thái:** đã áp dụng 1.9.0

## 2026-09-16 — sửa mục cũ — scope backends
**Kích hoạt:** build thật cả 8 workspace dưới docker mode; 3 cái hỏng.
**Bài học:** mục 2026-09-15 viết *"`training_aggregation` chỉ có `../shared`, tức không thuộc nhóm có path dependency ra ngoài workspace"* — **sai**. Phép soát đó chỉ nhìn `guest/Cargo.toml`; phụ thuộc thoát ra nằm sâu hơn một tầng, ở `shared/Cargo.toml` (`training-aggregation-shared` → `training-fragment-shared`). Docker mount đúng **một** thư mục, nên cả ba (`forward_td_mlp`, `one_step_sgd_tiny`, `training_aggregation`) build hỏng với rc=101 cho đến khi mount ở tổ tiên chung: `workspace_directory: Some(zk_backend)`. Bài học chung: soát phụ thuộc phải đi **đệ quy qua mọi crate trong workspace**, không chỉ crate guest.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md`
**Độ tin cậy:** cao (3/8 hỏng trước, 8/8 xanh sau khi sửa)
**Trạng thái:** đã áp dụng 1.9.0

## 2026-09-16 — phát hiện mới — scope experiments
**Kích hoạt:** đi tìm tham số đã sinh ra hai dòng `binary_tree_native_t1248` của Bảng 2; thư mục làm việc chỉ còn **một** bản.
**Bài học:** `run_phase7...validation.py` đặt tên thư mục làm việc và file case **chỉ theo target**: `_binary_native_work/t{T}` và `_binary_native_cases/..._t{T}_case_0.json`. Hai cây cartpole và lunarlander cùng T=1248 nên cây chạy sau **ghi đè** cây chạy trước, và thư mục làm việc là **nơi duy nhất còn ghi learning_rate / target_sync_interval / layer_sizes của lá**. Hệ quả thật: tham số cây cartpole đã mất khỏi repo. Cách chạy đúng: mỗi môi trường một `--out-root` riêng, rồi đổi tên thư mục provenance về `..._t{T}_{env}`. Cách khôi phục khi đã mất: tính lại `config_hash_from_fragment_public` trên không gian tham số nhỏ rồi so với `config_hash` trong `public_inputs.json` đã công bố — dò ra đúng bộ `(dataset_size, learning_rate, target_sync_interval, gradient_clip_fp)`, không phải đoán.
**Đích đề xuất:** `rules/90-domain/experiments.md`; cân nhắc sửa script để tên thư mục mang cả dataset
**Độ tin cậy:** cao (khôi phục xong cả ba cây, khớp hash tuyệt đối)
**Trạng thái:** đã áp dụng 1.9.0

## 2026-09-16 — phát hiện mới — scope experiments
**Kích hoạt:** chuẩn bị máy GPU cho phiên 2.
**Bài học:** ba thứ chặn một lượt thuê máy mà không lộ ra cho tới phút chót: (a) `artifacts/datasets/` bị gitignore, nên bản clone trên máy **không có** `raw_episodes.jsonl` — phải chuyển riêng; gói 3 dataset bỏ `collection_log.jsonl` (không cần cho `provenance_from`) còn **26,7 MB** nén, lên máy trong 11 giây; (b) khoá riêng của key pair `zk-sp1-v2` **không còn trên máy** (bản `zk-sp1.pem` trong Downloads là của key cũ đã xoá — vân tay SHA1 của DER không khớp), phải tạo key mới; (c) `g5.2xlarge` **hết chỗ ở us-east-1a và 1b** trong cùng một phút — `run-instances` phải thử vòng qua các subnet theo AZ thay vì cắm cứng một cái.
**Đích đề xuất:** `rules/90-domain/experiments.md` mục quy trình thuê máy
**Độ tin cậy:** cao (cả ba đều gặp thật trong phiên này)
**Trạng thái:** đã áp dụng 1.9.0

## 2026-09-16 — phát hiện mới — scope relations
**Kích hoạt:** cổng tương đương cuối trước khi thuê máy: sinh lại 8 lá thật của cây t1248 lunarlander bằng code M2 và so với `leaf_cases` đã lưu.
**Bài học:** M2 (bỏ băm lại mô hình mà chuỗi đã cam kết) **khớp tuyệt đối từng byte** trên lá thật — 156 bước, lưới `[8,64,4]`, dữ liệu lunarlander-expert-v1 thật, cả `public_inputs` lẫn `private_witness`; lá 7 cho `final_checkpoint_hash = 72b68b7c…` đúng bằng `output_checkpoint_hash` của root đã công bố. Cổng này rẻ (22 giây Python) và mạnh hơn hẳn các cổng chạy trên fixture tổng hợp: nó đóng lại khả năng "đúng trên đồ chơi, sai trên dữ liệu thật" **trước khi** tiêu tiền GPU.
**Đích đề xuất:** `rules/30-kiem-thu.md` — đổi quan hệ thì cổng cuối phải chạy trên lá thật của cây, không chỉ vector canonical
**Độ tin cậy:** cao (8/8 khớp byte)
**Trạng thái:** đã áp dụng 1.9.0

## 2026-09-16 — sửa mục cũ — scope backends
**Kích hoạt:** G4 — thêm nhánh CUDA cho sáu host còn lại.
**Bài học:** `rules/90-domain/sp1-backend.md` dòng 18 nay **sai**: *"sáu host kia không có nhánh CUDA nào và ghi thẳng `"prover": "cpu"` vào metrics"*. Cả tám host giờ đọc `SP1_CUDA` và ghi nhãn prover thật. Phần còn lại của dòng đó vẫn đúng và vẫn quan trọng: biến môi trường **im lặng theo cả hai chiều**, `nvidia-smi` mới là thứ nói thật. Hai điều kỹ thuật cần ghi kèm: (a) `Prover` có associated type nên không boxing được — phải tách `run_with_prover<P: Prover>`; (b) `setup()` và `prove()` trả `P::Error` **không** phải `StdError`, nên `anyhow::Context` không áp dụng được, phải `map_err`.
**Đích đề xuất:** `rules/90-domain/sp1-backend.md` dòng 18
**Độ tin cậy:** cao (build sạch 6/6, ELF trùng hash, đã prove thật trên cả hai prover)
**Trạng thái:** đã áp dụng 1.9.0

## 2026-09-16 — thất bại — scope experiments
**Kích hoạt:** G4 lộ ra rằng dòng `td_mvp` của Bảng 2 **chưa hề được prove lại** trong Phiên 2, dù tôi đã báo cáo "cả 26 dòng ra từ một thế hệ guest".
**Bài học:** `benchmark_sp1_td_mvp.py` ghi `summary.json`, `benchmark_matrix.csv`, `summary.md` — **không ghi `metrics.json`**. File đó chỉ do chính host ghi khi được gọi với `--out-dir`. Tôi đã cho rằng "chạy script phase là provenance được làm mới" mà không kiểm. Cách bắt lỗi rẻ: so `guest_elf_sha256` trong `metrics.json` với hash ELF vừa build — khớp thì mới thật sự là prove lại. Nên đưa phép so này thành bước mặc định sau mỗi lượt prove, thay vì tin vào `rc=0`.
**Đích đề xuất:** `rules/90-domain/experiments.md`; cân nhắc một cổng script so hash ELF
**Độ tin cậy:** cao (metrics cũ mang ELF `cd3057f7…`, ELF docker là `6cf19651…`)
**Trạng thái:** đã áp dụng 1.9.0

## 2026-09-17 — người sửa — scope harness
**Kích hoạt:** người dùng sửa lại trong phiên
**Bài học:** ý tôi là bài của tôi có mạnh đến Q1 không ý
**Đích đề xuất:** /harness-sync quyết định
**Độ tin cậy:** thấp (tự động, chưa duyệt)
**Trạng thái:** chờ xử lý

## 2026-09-21 — phát hiện mới — scope paper
**Kích hoạt:** Đo lại `--execute` 8 lá cam kết của cây t1248 (`artifacts/reports/provenance/sp1/_binary_native_work/t1248/leaf_cases/`, k=156, dataset 50.552, `target_sync_interval=4`) cho dải **493.5–497.7 M cycles** (leaf_0 … leaf_7). `results.tex` in dải họ interval-4 là "493.5--494.7 M" và kết luận hai họ "differ by under 0.4%". 493.5 = leaf_0 và 494.7 = leaf_3, nên con số đã in nhiều khả năng là min/max của **4 lá đầu**, không phải cả 8. Trên toàn bộ 8 lá, độ tản là 0,85%.
**Bài học:** dải min/max trong paper phải nêu rõ quần thể nào, và phải sinh lại từ artifact chứ không chép tay — không có file nào trong repo chứa 493.5/494.7, nên không cổng nào bắt được sai lệch này.
**Đích đề xuất:** `scripts/experiments/check_paper_claims.py` — thêm check cho dải cycles của lá; hoặc ghi cycle_count từng lá vào provenance khi sinh cây.
**Độ tin cậy:** cao (đo trực tiếp, và phép đo đã hiệu chuẩn: chạy lại `training_fragment_k156_case_0.json` cho đúng 73.471.504 cycles, trùng từng chữ số với `provenance/sp1/training_fragment_k156/metrics.json`)
**Trạng thái:** đã áp dụng. **Đính chính một kết luận sai của chính mục này:** tôi đã viết "không file nào trong repo chứa 493.5/494.7". Sai. `artifacts/reports/provenance/sp1_t1248_lunarlander/` và `sp1_t4992_lunarlander_random/` đều được track và chứa `cycle_count` từng lá; tôi đã tìm nhầm trong `provenance/sp1/_binary_native_work/` (thư mục bị gitignore). Phép đo WSL trùng 8/8 từng chữ số với provenance đó. Họ interval-4 sửa thành 493,5--497,7 M; họ interval-2000 cũng sai cận dưới (in 494,2 = leaf_19, thật là 493,5 = leaf_20) — đã sửa. Cổng mới `test_both_leaf_ranges_cover_every_leaf_of_their_tree` đọc thẳng provenance.
