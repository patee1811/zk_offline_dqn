# Lộ Trình 3 Tháng Nhắm NDSS / Security-Style A*

Tài liệu này là roadmap kỹ thuật và paper-facing cho giai đoạn 3 tháng tiếp
theo của dự án. Mục tiêu là nâng repo từ một prototype SP1 TD proof thành một
hệ thống ZK-verifiable offline RL artifact có claim rõ, benchmark lặp lại được,
và positioning phù hợp với top security/systems venue.

Mốc làm việc dự kiến:

- Bắt đầu: 13/05/2026.
- Freeze nội bộ: 13/08/2026.
- Deadline nhắm tới: NDSS 2027 Fall Cycle, 19/08/2026 AoE.

## 1. Định Vị Và Mục Tiêu

Mục tiêu không phải là viết lại dự án thành một full proof-of-training system
trong 3 tháng. Mục tiêu thực tế và mạnh hơn là xây dựng một proof stack theo
tầng cho offline DQN trên committed replay data.

Claim chính nên hướng tới:

```text
A layered ZK-verifiable artifact system for offline DQN over committed replay
data, covering committed transition membership, Bellman/TD computation,
minibatch aggregation, fixed-point neural forward/argmax anchoring, and
micro-scale one-step SGD update evidence.
```

Viết bằng tiếng Việt:

```text
Một pipeline chứng minh theo tầng cho offline DQN trên dữ liệu replay đã
commit: membership của transition, Bellman/TD arithmetic, minibatch
aggregation, fixed-point neural forward/argmax anchoring, và bằng chứng micro
cho một bước SGD update.
```

Không được claim:

- full proof-of-training từ initialization đến final checkpoint;
- full long-trace recursive proof;
- full Adam optimizer proof;
- honesty của data collection trước khi dataset được commit;
- privacy cho Python verifier;
- production-grade cryptographic infrastructure.

## 2. Trạng Thái Hiện Tại Của Repo

Nền hiện tại đã tốt cho một research prototype:

- Python regression đang pass 10/10.
- SP1 backend đã prove được TD-1, TD-2, TD-4, TD-8.
- Python và SP1 agree trên valid fixtures và tamper fixtures.
- Tamper suite đã cover schema, reward, rounding, done branch, Merkle path,
  target/loss, batch aggregation.
- Paper hiện tại đã biết tự giới hạn scope và không overclaim full training.

Điểm yếu cần sửa để có cơ hội A*:

- SP1 TD relation hiện tại vẫn nhận Q-values làm witness, chưa chứng minh Q-values
  được tính từ committed/private model weights.
- TD-2/4/8 benchmark hiện tại lặp lại canonical transition, chưa phải replay
  minibatch thực gồm nhiều transition riêng.
- Kết quả còn CartPole-focused, dễ bị reviewer xem là toy-only.
- Python one-step và short-trace verifiers chưa phải ZK proofs.
- Paper hiện tại giống artifact report hơn là một security/systems paper với
  threat model, formal statement, và evaluation narrative thật sắc.

## 3. Đóng Góp Cần Đạt Khi Nộp

Đến lúc nộp, paper nên có bốn đóng góp chính.

### 3.1 Formal RL-Specific ZK Statements

Định nghĩa rõ các relation:

- committed trajectory membership;
- terminal và non-terminal Bellman branch;
- Double-DQN argmax semantics;
- SmoothL1 TD loss;
- minibatch average loss;
- model-state commitment;
- optional tiny one-step SGD update.

Mỗi relation phải tách rõ:

- public inputs;
- private witness;
- relation checks;
- security guarantee;
- limitations.

### 3.2 SP1 Backend Implementation

Thêm hoặc nâng cấp các relation:

- `td_batch_distinct_v1`: minibatch TD với distinct committed transitions.
- `forward_td_mlp_v1`: fixed-point MLP forward, argmax, selected target value,
  Bellman target, SmoothL1 loss, Merkle membership, model commitment.
- `one_step_sgd_tiny_v1`: optional micro proof cho một bước SGD trên tiny
  Q-network.

`one_step_sgd_tiny_v1` chỉ là stretch goal. Nếu không xong đúng mốc, demote
sang appendix hoặc future work.

### 3.3 Adversarial Verification Suite

Cần có tamper matrix theo từng relation:

- transition tamper: obs, next_obs, action, reward, done;
- commitment tamper: leaf, leaf hash, Merkle sibling, path order, leaf index;
- arithmetic tamper: fixed-point rounding, target, TD error, SmoothL1 loss;
- model tamper: online weight, target weight, model commitment;
- forward tamper: activation, ReLU mask, argmax, selected target Q-value;
- batch tamper: item index, item order, batch size, claimed batch loss;
- optional update tamper: gradient tensor, delta tensor, learning rate, post
  model commitment.

### 3.4 Reproducible Artifact

Cần có một artifact package cuối cùng:

- one-command Python regression;
- SP1 execute/prove commands;
- frozen JSON/CSV/Markdown benchmark outputs;
- exact toolchain versions;
- smoke path cho reviewer không có prover mạnh;
- full path cho reviewer có WSL/Linux/Kaggle;
- clear expected outputs.

## 4. Implementation Plan

### Phase A: Distinct Minibatch TD, Tuần 1-3

Mục tiêu:

Thay benchmark TD-2/4/8 lặp lại một transition bằng minibatch gồm nhiều
transition thật từ committed dataset.

Cần làm:

- Tạo exporter chọn distinct indices từ committed transition dataset.
- Tạo batch fixture mới với `items[]`, mỗi item có:
  - `index`;
  - `transition`;
  - `leaf`;
  - `leaf_hash`;
  - `merkle_path`;
  - `td_witness`.
- Cập nhật Python verifier nếu cần để reject duplicate mode trong main benchmark.
- Cập nhật SP1 shared relation nếu hiện tại đã support items nhưng cần harden
  index/path/ordering checks.
- Thêm negative tests cho distinct batch:
  - duplicate index nếu public claim yêu cầu distinct;
  - wrong item index;
  - swapped item order;
  - wrong item loss;
  - wrong claimed batch average.
- Benchmark TD-1/2/4/8 với distinct transitions.
- Nếu compute cho phép, thêm TD-16.

Acceptance criteria:

- Python/SP1 agreement 100%.
- Tất cả accepted cases pass.
- Tất cả tamper cases reject.
- Benchmark matrix ghi rõ batch là distinct replay minibatch.
- Paper không còn dùng repeated-transition batch làm main result.

### Phase B: Forward-TD MLP Proof, Tuần 4-6

Mục tiêu:

Đóng gap lớn nhất hiện tại: SP1 phải chứng minh Q-values được tính từ model
weights, không chỉ tin vào Q-value witness.

Relation mới:

```text
forward_td_mlp_v1
```

Public inputs:

- `dataset_root`;
- `fp_scale`;
- `gamma_fp`;
- `loss_type`;
- `leaf_indices`;
- `network_spec_hash`;
- `online_model_commitment`;
- `target_model_commitment`;
- `claimed_item_losses_fp`;
- `claimed_batch_loss_fp`.

Private witness:

- transitions;
- Merkle paths;
- quantized online weights;
- quantized target weights;
- intermediate activations;
- ReLU masks;
- online Q-values for `s`;
- online Q-values for `s'`;
- target Q-values for `s'`;
- argmax result;
- selected target Q-value.

Relation checks:

- transition serializes canonically;
- Merkle path authenticates to public `dataset_root`;
- private online weights hash to `online_model_commitment`;
- private target weights hash to `target_model_commitment`;
- online MLP computes `Q_online(s)`;
- online MLP computes `Q_online(s')`;
- target MLP computes `Q_target(s')`;
- `q_online_action = Q_online(s)[action]`;
- `next_action_online = argmax_a Q_online(s')[a]`;
- `q_target_max = Q_target(s')[next_action_online]`;
- terminal/non-terminal Bellman target is correct;
- TD error is correct;
- SmoothL1 loss is correct;
- public claimed losses match recomputation.

Recommended network specs:

- Main forward proof: CartPole `4-16-16-2`.
- Cheaper proof or optional update proof: `4-8-2`.
- Existing `128-128` model remains Python/context result, not main SP1 forward
  proof target.

Acceptance criteria:

- Python fixed-point oracle and SP1 relation agree.
- SP1 execute passes for batch 1/2.
- SP1 proof generated for batch 1.
- Batch 2 proof is optional but valuable.
- Tamper model-weight, activation, ReLU, argmax, and target-value cases reject.

Paper impact:

Đây là upgrade quan trọng nhất. Sau Phase B, paper có thể nói backend proves
that TD values are anchored to model weights, không chỉ là arithmetic over
untrusted Q-value witnesses.

### Phase C: Micro One-Step SGD Proof, Tuần 7-8

Mục tiêu:

Chứng minh một bước update SGD ở quy mô nhỏ để tạo đường nối từ TD proof sang
proof-of-update.

Relation mới:

```text
one_step_sgd_tiny_v1
```

Public inputs:

- pre model commitment;
- post model commitment;
- dataset root;
- batch indices;
- learning rate;
- optimizer type `sgd`;
- network spec hash;
- claimed batch loss.

Private witness:

- pre-update weights;
- transitions;
- Merkle paths;
- forward activations;
- ReLU masks;
- SmoothL1 gradient branch;
- per-layer gradients;
- post-update weights.

Relation checks:

- forward-TD relation from Phase B holds;
- SmoothL1 derivative branch is correct;
- backprop for tiny MLP is correct;
- SGD update holds:

```text
post_weight = pre_weight - learning_rate * gradient
```

- post weights hash to public post commitment.

Scope:

- Required: batch 1.
- Optional: batch 2.
- No Adam.
- No target sync long trace.
- No full training proof.

Fallback rule:

Nếu không có SP1 proof ổn định trước 07/07/2026, không để Phase C chặn paper.
Khi đó:

- giữ Python one-step verifier làm pre-ZK extension;
- move `one_step_sgd_tiny_v1` sang appendix hoặc future work;
- main contribution vẫn là TD + distinct minibatch + forward-TD.

### Phase D: Second Environment, Tuần 6-9

Mục tiêu:

Giảm rủi ro bị review là single toy environment.

Recommended environment:

- `MountainCar-v0`.

Lý do:

- observation dimension nhỏ;
- action space discrete;
- phù hợp với DQN-style value function;
- proof relation gần với CartPole nhưng khác dynamics/task.

Minimum deliverables:

- offline dataset summary;
- Merkle root;
- TD or forward-TD fixture;
- Python verifier pass;
- SP1 execute pass;
- tamper rejection smoke.

Stretch deliverable:

- SP1 proof for forward-TD batch 1 trên MountainCar.

Nếu MountainCar training không ổn định:

- dùng synthetic classic-control-style fixture với network spec khác;
- nói rõ trong paper là second spec benchmark, không claim policy performance.

### Phase E: Benchmark And Artifact Hardening, Tuần 9-10

Mục tiêu:

Biến các kết quả thành benchmark matrix và artifact package có thể review được.

Benchmark matrix cần có:

- relation id;
- environment;
- network spec;
- batch size;
- Merkle depth;
- number of accepted fixtures;
- number of rejected tamper fixtures;
- prove time;
- verify time;
- proof size;
- cycle count;
- platform;
- command.

Output paths nên thêm:

```text
artifacts/benchmarks/final_ndss/summary.json
artifacts/benchmarks/final_ndss/benchmark_matrix.csv
artifacts/benchmarks/final_ndss/tamper_matrix.csv
artifacts/benchmarks/final_ndss/summary.md
artifacts/benchmarks/final_ndss/reproduction.md
```

Acceptance criteria:

- Mỗi số trong paper có source trong JSON/CSV.
- Mỗi command trong appendix chạy được hoặc có smoke alternative.
- Reviewer có thể reproduce Python path nhanh.
- Reviewer có thể reproduce SP1 proof path trên Linux/WSL/Kaggle.

## 5. Paper Plan

Paper cần được rewrite theo security/systems framing, không phải ML-only
framing.

Suggested sections:

1. Introduction.
2. Threat Model.
3. Background: offline DQN, Bellman TD, commitments, zkVM.
4. Formal Verification Statements.
5. System Design.
6. SP1 Backend Implementation.
7. Security Analysis.
8. Evaluation.
9. Limitations.
10. Related Work.
11. Conclusion.
12. Artifact Appendix.

### Introduction

Cần trả lời rõ:

- Ai là dishonest prover?
- Verifier muốn kiểm tra cái gì?
- Tại sao offline RL khác supervised proof-of-training?
- Tại sao Bellman/TD layer là decomposition point đúng?
- Hệ thống chứng minh được gì hôm nay?

### Threat Model

Cần nhấn mạnh:

- Prover có private dataset/model/witness.
- Verifier biết commitments và public claims.
- Prover có thể tamper transition, Merkle path, Q-values, model weights, losses,
  update deltas.
- System chỉ bảo vệ trong relation được formalize.

### Formal Statements

Viết theo bảng:

| Relation | Public | Private | Checks | Backend |
| --- | --- | --- | --- | --- |
| TD | root, target/loss | transition, path, Q witness | membership + TD arithmetic | SP1 |
| Distinct minibatch TD | root, batch loss | items | per-item TD + average | SP1 |
| Forward-TD MLP | root, model commitments | weights, activations | MLP + argmax + TD | SP1 |
| Tiny SGD update | pre/post commitments | weights, gradients | forward + backprop + SGD | SP1/Python fallback |

### Evaluation

Tables needed:

- Table 1: relation coverage vs current/future proof stack.
- Table 2: proof metrics by relation and batch size.
- Table 3: tamper rejection matrix.
- Table 4: comparison with PoL, zkDL, Kaizen/zkPoT, verifiable RL.
- Figure 1: layered architecture.
- Figure 2: proof cost scaling by batch size/network width.

### Related Work

Bắt buộc cover:

- Proof-of-Learning.
- zkDL.
- Kaizen / zero-knowledge proof of training for DNNs.
- zkPoT optimum vicinity.
- ZKML inference/training survey.
- DQN / Double DQN.
- Offline RL / CQL.
- Verifiable/interpretable RL.
- zkVMs: SP1 and RISC Zero context.

## 6. Weekly Milestones

### Week 1: 13/05 - 19/05

Deliverables:

- Lock final paper claim.
- Tạo relation checklist cho TD, minibatch, forward-TD, tiny SGD.
- Viết comparison matrix với prior work.
- Xác định file/schema nào cần đổi cho distinct minibatch.

Exit criteria:

- Có issue checklist hoặc doc nội bộ cho từng relation.
- Không còn ambiguity về main claim.

### Week 2: 20/05 - 26/05

Deliverables:

- Implement distinct minibatch exporter.
- Implement/extend Python verifier.
- Generate fixtures TD-1/2/4/8 với distinct transitions.
- Thêm negative tests batch mới.

Exit criteria:

- Python verifier pass valid cases.
- Python negative tests reject expected tampers.

### Week 3: 27/05 - 02/06

Deliverables:

- Port distinct minibatch relation vào SP1 nếu cần.
- Run SP1 execute for valid/tamper cases.
- Prove TD-1/2/4/8 distinct cases nếu compute cho phép.

Exit criteria:

- Python/SP1 agreement 100%.
- Benchmark summary mới được ghi lại.

### Week 4: 03/06 - 09/06

Deliverables:

- Implement fixed-point MLP forward oracle trong Python.
- Implement Rust fixed-point MLP helper trong SP1 shared crate.
- Define `network_spec_hash` và model commitment format.

Exit criteria:

- Python oracle có deterministic expected outputs.
- Rust unit/smoke logic match Python.

### Week 5: 10/06 - 16/06

Deliverables:

- Implement `forward_td_mlp_v1` SP1 guest path.
- Run SP1 execute for valid and tamper cases.
- Generate at least one SP1 proof for batch 1.

Exit criteria:

- Batch 1 forward-TD proof verified.
- Tamper weight/activation/argmax rejects.

### Week 6: 17/06 - 23/06

Deliverables:

- Add second env/spec benchmark.
- Prefer MountainCar-v0.
- Run Python and SP1 smoke.

Exit criteria:

- At least one non-CartPole relation execute pass.
- Artifact summary includes second env/spec.

### Week 7: 24/06 - 30/06

Deliverables:

- Implement tiny one-step SGD relation or decide to demote.
- Add Python oracle for tiny backprop if needed.
- Run SP1 execute for batch 1.

Exit criteria:

- Clear go/no-go for SP1 proof of one-step update.

### Week 8: 01/07 - 07/07

Deliverables:

- Finalize one-step proof if feasible.
- Build full tamper generator for all supported relations.
- Freeze whether one-step is main or appendix.

Exit criteria:

- No unresolved relation risk remains for main paper.

### Week 9: 08/07 - 14/07

Deliverables:

- Run final benchmark matrix.
- Generate JSON/CSV/Markdown summaries.
- Create plots and tables for paper.

Exit criteria:

- All paper numbers come from frozen artifacts.

### Week 10: 15/07 - 21/07

Deliverables:

- Rewrite main paper around security/systems narrative.
- Insert formal statements and evaluation tables.
- Rewrite abstract/introduction/results/discussion.

Exit criteria:

- Full draft complete.
- Claims match artifact exactly.

### Week 11: 22/07 - 28/07

Deliverables:

- Artifact packaging.
- Anonymous reproduction workflow.
- Fresh-clone smoke test.
- Open Science / artifact appendix draft.

Exit criteria:

- Reviewer can run documented commands.
- No local-only hidden dependency.

### Week 12: 29/07 - 13/08

Deliverables:

- Internal review.
- Claim tightening.
- Figure/table polish.
- Final experiment freeze by 09/08.
- Final PDF/artifact freeze by 13/08.

Exit criteria:

- Submission-ready paper.
- Submission-ready artifact.
- 14/08 - 18/08 kept as upload/debug buffer.

## 7. Test Plan

Required commands:

```bash
python scripts/experiments/run_full_regression.py
```

Thêm commands mới cho final artifact:

```bash
python scripts/experiments/run_final_ndss_regression.py
python scripts/experiments/benchmark_distinct_td_sp1.py --prove
python scripts/experiments/benchmark_forward_td_mlp_sp1.py --prove
```

Nếu one-step SP1 được giữ:

```bash
python scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --prove
```

Required test classes:

- schema compatibility tests;
- public/private field validation;
- fixed-point rounding tests;
- Merkle membership tests;
- TD arithmetic tests;
- MLP forward tests;
- argmax tie-breaking tests;
- model commitment tests;
- batch aggregation tests;
- SP1 execute/prove tests;
- negative tamper tests;
- fresh-clone smoke test.

Required negative scenarios:

- wrong schema version;
- wrong reward;
- wrong done flag;
- wrong action;
- wrong observation;
- wrong next observation;
- wrong fixed-point rounding;
- wrong leaf encoding;
- wrong leaf hash;
- wrong Merkle sibling;
- wrong path order;
- wrong leaf index;
- wrong online model weight;
- wrong target model weight;
- wrong activation;
- wrong ReLU mask;
- wrong argmax;
- wrong selected target Q-value;
- wrong TD target;
- wrong TD error;
- wrong SmoothL1 loss;
- wrong batch size;
- wrong batch item order;
- wrong claimed batch average;
- wrong learning rate;
- wrong gradient tensor;
- wrong delta tensor;
- wrong post model commitment.

## 8. Non-Negotiable Rules

- Không claim full proof-of-training.
- Không claim Python verifier là zero-knowledge.
- Không dùng repeated-transition batch làm main result sau khi Phase A xong.
- Không thêm feature lớn sau 14/07/2026 nếu chưa có benchmark ổn định.
- Nếu one-step SP1 không ổn trước 07/07/2026, demote ngay.
- Mỗi paper number phải trace được về artifact JSON/CSV.
- Mỗi limitation quan trọng phải được nói thẳng trong paper.
- Không che giấu việc CartPole/MountainCar là small-scale benchmarks.

## 9. Assumptions

- Target venue: NDSS/security-style A*.
- Compute budget: Kaggle/WSL only.
- Main backend: SP1.
- RISC Zero chỉ là comparison/future backend trong 3 tháng này.
- Strongest feasible path là đóng proof gap quanh model-grounded forward-TD,
  không phải cố gắng prove full long training trace.
- Existing Python one-step và short-trace verifiers vẫn có giá trị như pre-ZK
  extension evidence, nhưng không được trình bày như ZK proofs.

## 10. Definition Of Done

Roadmap này được xem là hoàn thành nếu đến freeze nội bộ có:

- distinct minibatch TD SP1 results;
- forward-TD MLP SP1 proof ít nhất batch 1;
- tamper matrix cho TD, minibatch, và forward-TD;
- final benchmark artifact package;
- rewritten security/systems paper draft;
- artifact reproduction instructions;
- claim/limitation consistency giữa README, docs, paper, và benchmark outputs.

Stretch done:

- tiny one-step SGD SP1 proof batch 1;
- second environment forward-TD proof;
- TD-16 distinct batch proof;
- automated table consistency check between paper and benchmark JSON.
