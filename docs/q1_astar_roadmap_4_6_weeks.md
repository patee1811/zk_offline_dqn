# Lộ trình 4-6 tuần để đưa ZK-Offline-DQN tới mức Q1/A*

## Tóm tắt

Mục tiêu thực tế nhất của project trong 4-6 tuần là một bài theo hướng security/crypto-systems:

> Một pipeline ZK-backed đầu tiên để kiểm chứng tính đúng đắn của temporal-difference computation trong offline DQN trên dữ liệu trajectory đã được commit.

Project hiện đã mạnh ở tầng pre-ZK: Python verifier đã kiểm tra Merkle membership, TD arithmetic, minibatch loss, checkpoint anchoring, one-step SGD consistency và short trace chaining. Tuy nhiên, project chưa đủ chuẩn Q1/A* vì chưa có proof backend thật.

Vì vậy, lộ trình này ưu tiên làm xong hệ thống trước, viết lại paper sau:

```text
Tuần 1-5: hoàn tất SP1 backend, benchmark, negative tests, reproducibility, mở rộng nếu kịp.
Tuần 6: khi kết quả đã khóa, viết lại paper từ đầu theo đúng claim đã chứng minh được.
```

Không viết lại paper quá sớm. Trong 5 tuần đầu chỉ ghi chú paper TODO ngắn, không dành nhiều thời gian polish manuscript. Lý do là claim cuối cùng phụ thuộc trực tiếp vào mức backend ZK làm được.

## Chiến lược venue

Track phù hợp nhất là security/crypto-systems, không phải pure RL.

Định vị nên theo hướng:

- Q1 journal nếu muốn có không gian trình bày hệ thống, benchmark, threat model và limitation đầy đủ.
- A*/top security conference nếu SP1 proof thật sự chạy tốt, benchmark tái lập được, negative tests rõ ràng, và narrative rất sắc.
- Workshop hoặc arXiv nếu chỉ dừng ở pre-ZK hoặc backend proof còn quá nhỏ.

Nhóm venue gợi ý:

- A*/top security: ACM CCS, USENIX Security, IEEE S&P, NDSS.
- Q1 journal: IEEE TDSC, IEEE TIFS, Future Generation Computer Systems, Computers & Security.
- Fallback: ZK/security workshop hoặc arXiv preprint.

Claim không nên nói là đã giải quyết full proof-of-training cho RL. Claim mạnh nhưng an toàn hơn:

```text
ZK-verifiable TD computation for offline DQN over committed trajectories,
with a pre-ZK path toward update and trace verification.
```

## Research gap cần bảo vệ

Project cần đứng giữa bốn dòng nghiên cứu:

- Proof-of-Learning và proof-of-training cho ML.
- zkML hoặc zk proof-of-training cho supervised/deep learning.
- Verifiable reinforcement learning và policy verification.
- ZK/privacy/audit systems cho RL hoặc federated RL.

Gap chính:

```text
Các công trình zk proof-of-training hiện chủ yếu tập trung vào supervised learning hoặc DNN training nói chung.
Các công trình verifiable RL chủ yếu kiểm chứng policy, safety hoặc compositional behavior.
Các công trình ZK+RL chủ yếu xử lý privacy, auditability, communication integrity hoặc action/reward compliance.
Vẫn còn thiếu hệ thống chứng minh cryptographic correctness của các computation đặc thù trong offline DQN training trên trajectory dataset đã commit.
```

Các yếu tố đặc thù RL cần nhấn mạnh:

- committed trajectory dataset;
- transition membership;
- Bellman backup;
- Double-DQN target structure;
- TD loss;
- replay sampling rule;
- target-network sync semantics;
- checkpoint chaining;
- lộ trình từ TD proof tới update proof và trace proof.

## Tuần 1: Khóa claim, relation và môi trường backend

Mục tiêu: chốt chính xác project sẽ chứng minh cái gì, không để vừa code vừa đổi claim.

### Deliverables

- Chốt target claim:
  - "A first ZK-backed verification pipeline for offline DQN temporal-difference computation over committed trajectory data."
  - Non-claim: chưa chứng minh full RL proof-of-training.
- Khóa TD MVP relation:
  - Merkle membership;
  - fixed-point Bellman target;
  - TD error;
  - SmoothL1 loss;
  - claimed target/loss consistency.
- Đồng bộ Python verifier và SP1 spec:
  - vector chuẩn: `zk_backend/test_vectors/td_mvp_case_0.json`;
  - semantic reference: `scripts/artifacts_export/verify_td_mvp_test_vector.py`.
- Setup SP1 trên Linux/macOS hoặc WSL2 Ubuntu:
  - chạy external SP1 hello-world proof;
  - ghi lại SP1 version, Rust version, OS, CPU, RAM;
  - ghi lại lỗi setup nếu có.
- Chỉ ghi chú paper TODO tối thiểu:
  - related-work clusters cần cập nhật;
  - bảng kết quả dự kiến;
  - limitation dự kiến.

### Task cụ thể

- Kiểm tra fixed-point constants với `zk_offline_dqn/zk_specs.py`.
- Kiểm tra leaf serialization với `zk_offline_dqn/merkle.py`.
- Kiểm tra `docs/zk_backend_mvp.md` và `docs/backend_selection_v0_12.md` có thống nhất về public/private fields không.
- Cập nhật ngắn `zk_backend/td_mvp/sp1/toolchain.md` với SP1 setup notes.
- Tạo checklist nội bộ cho các tamper cases cần chạy ở SP1.

### Go/no-go gate

Cuối tuần 1 phải có:

- SP1 hello-world proof chạy được;
- TD MVP relation đã khóa;
- canonical test vector pass Python verifier.

Nếu SP1 không chạy được cuối tuần 1:

- chuyển sang RISC Zero;
- hoặc downgrade claim thành pre-ZK systems prototype, khả năng A* thấp hơn nhiều.

## Tuần 2: Implement SP1 TD MVP

Mục tiêu: chuyển từ pre-ZK prototype sang proof backend thật cho statement nhỏ nhất nhưng có tính RL-specific.

### Deliverables

- Tạo Rust workspace dưới `zk_backend/td_mvp/sp1/`:
  - `host`;
  - `guest`;
  - `shared`.
- Implement shared typed structs:
  - public inputs;
  - private witness;
  - Merkle path steps;
  - fixed-point constants.
- Implement guest relation:
  - serialize transition leaf;
  - compute SHA-256 leaf hash;
  - verify Merkle path;
  - compute terminal/non-terminal Bellman target;
  - compute TD error;
  - compute SmoothL1 loss;
  - assert claimed target/loss.
- Implement host:
  - load `zk_backend/test_vectors/td_mvp_case_0.json`;
  - prepare prover input;
  - generate proof;
  - verify proof;
  - print proving time, verification time, proof size.
- Add SP1 negative tests:
  - wrong reward;
  - wrong done flag;
  - wrong Merkle sibling;
  - wrong claimed target;
  - wrong claimed loss.

### Task cụ thể

- Mirror Python semantics trước, chưa tối ưu.
- Tách parsing, input conversion và relation logic để negative tests dùng lại được.
- Public output tối thiểu:
  - `dataset_root`;
  - `claimed_target_fp`;
  - `claimed_loss_fp`;
  - `schema_version` nếu test vector đã hỗ trợ.
- Private witness tối thiểu:
  - transition contents;
  - Merkle path;
  - Q-value witnesses;
  - TD intermediate values.

### Go/no-go gate

Cuối tuần 2 phải có:

- ít nhất một valid SP1 proof verify thành công;
- ít nhất ba tamper cases bị reject;
- proof time, verification time và proof size được in ra.

Nếu không đạt gate này, không được claim có ZK backend trong paper.

## Tuần 3: Benchmark và reproducibility cho SP1 backend

Mục tiêu: biến SP1 result từ demo thành kết quả có thể đưa vào paper.

### Deliverables

- Benchmark matrix:
  - single-transition TD proof;
  - minibatch size 2, 4, 8 nếu khả thi;
  - proof generation time;
  - verification time;
  - proof size;
  - memory hoặc cycle count nếu SP1 expose rõ.
- So sánh SP1 với Python verifier:
  - cùng valid fixture đều accept;
  - cùng tampered fixtures đều reject;
  - Python verifier là semantic oracle;
  - SP1 là cryptographic backend.
- Thêm reproducibility commands:
  - một command cho Python regression;
  - một command cho SP1 valid proof;
  - một command cho SP1 negative tests.
- Xuất benchmark snapshot:
  - JSON/CSV nếu tiện;
  - Markdown summary để paper tuần 6 dùng lại.

### Benchmark matrix tối thiểu

| Case | Relation | Batch size | Output cần ghi |
| --- | --- | ---: | --- |
| TD-1 | Merkle + TD + SmoothL1 | 1 | prove time, verify time, proof size |
| TD-2 | Merkle + TD + SmoothL1 + average loss | 2 | prove time, verify time, proof size |
| TD-4 | Merkle + TD + SmoothL1 + average loss | 4 | prove time, verify time, proof size |
| TD-8 | Merkle + TD + SmoothL1 + average loss | 8 | prove time, verify time, proof size |
| Tamper-reward | invalid witness | 1 | proof fails hoặc verification rejects |
| Tamper-path | invalid Merkle path | 1 | proof fails hoặc verification rejects |
| Tamper-loss | wrong claimed loss | 1 | proof fails hoặc verification rejects |

### Go/no-go gate

Cuối tuần 3 phải có:

- benchmark tái lập được bằng documented commands;
- không cần sửa file thủ công để reproduce main table;
- Python và SP1 thống nhất trên valid/tampered fixtures.

Nếu benchmark cần thao tác thủ công, chưa đủ chuẩn nộp.

## Tuần 4: Mở rộng hệ thống trước khi viết paper

Mục tiêu: tăng độ mạnh của contribution trước khi khóa claim cuối cùng.

### Ưu tiên 1: SP1 minibatch TD proof

Deliverables nếu khả thi:

- multiple Merkle memberships;
- per-sample TD target/loss;
- batch-average loss;
- public batch size;
- claimed batch loss;
- negative tests cho batch aggregation.

Lý do ưu tiên:

- gần với verifier hiện có;
- tăng sức nặng hơn single-transition proof;
- dễ đưa vào bảng benchmark và narrative Q1/A*.

### Ưu tiên 2: Stronger adversarial tests

Thêm các case:

- target-network value tamper;
- batch index tamper;
- schema version mismatch;
- fixed-point rounding mismatch;
- wrong `done` branch;
- wrong leaf index hoặc wrong path order.

### Ưu tiên 3: Backend comparison nhẹ

Chỉ làm nếu không làm chậm SP1:

- RISC Zero smoke comparison;
- hoặc document rõ vì sao chọn SP1 trước, RISC Zero để future comparison.

### Go/no-go gate

Cuối tuần 4 nên có ít nhất một upgrade mạnh:

- SP1 minibatch TD proof;
- hoặc adversarial test suite đủ dày;
- hoặc benchmark/reproducibility sạch hơn rõ rệt.

Nếu chưa có minibatch proof, paper vẫn có thể đi theo single-transition SP1 proof + pre-ZK short trace verifier, nhưng claim phải hẹp hơn.

## Tuần 5: Khóa implementation, benchmark và artifact package

Mục tiêu: kết thúc phần làm hệ thống. Sau tuần này không thêm feature lớn nữa.

### Deliverables

- Khóa final backend scope:
  - single-transition SP1 TD proof;
  - minibatch SP1 TD proof nếu đã xong;
  - Python one-step và short-trace verifier giữ vai trò pre-ZK extension.
- Chạy full Python regression:
  - compile checks;
  - TD/minibatch verifier;
  - one-step verifier;
  - short-trace verifier;
  - all negative tests.
- Chạy full SP1 suite:
  - valid proof;
  - negative tests;
  - benchmark command;
  - proof size/time report.
- Khóa benchmark snapshots:
  - existing offline RL results;
  - existing short-trace verifier results;
  - new SP1 proof results;
  - tamper rejection table.
- Cập nhật documentation kỹ thuật:
  - README status nếu cần;
  - SP1 run commands;
  - benchmark command notes;
  - limitation notes.

### Artifact package cần có

- Một command để verify Python regression.
- Một command để generate/verify SP1 proof.
- Một command để chạy SP1 negative tests.
- Một file benchmark summary cho SP1.
- Một bảng tamper rejection.
- Một test vector canonical.

### Go/no-go gate

Cuối tuần 5 phải trả lời được:

- claim mạnh nhất hiện có là gì;
- benchmark nào chắc chắn reproduce được;
- limitation nào bắt buộc phải viết trong paper;
- submission target nên là A*, Q1 journal hay workshop/preprint.

Sau gate này, không thêm feature lớn. Tuần 6 chỉ viết paper dựa trên kết quả đã khóa.

## Tuần 6: Viết lại paper sau khi đã làm xong hệ thống

Mục tiêu: viết lại manuscript từ kết quả thật, không viết theo roadmap giả định.

### Nguyên tắc viết

- Không claim feature chưa chạy.
- Không dùng "future work" để che phần đáng lẽ phải là contribution chính.
- Tất cả bảng kết quả phải lấy từ benchmark snapshot đã khóa ở tuần 5.
- Viết limitation rõ để reviewer không bắt lỗi quá-claim.

### Cấu trúc paper đề xuất

1. Abstract
   - Nêu bài toán: verifiable offline RL from committed trajectories.
   - Nêu gap: zkPoT hiện chưa xử lý RL-specific TD/update semantics.
   - Nêu contribution thực tế: pre-ZK verifier + SP1 TD proof.

2. Introduction
   - Động cơ outsourced/privacy-sensitive offline RL.
   - Vì sao offline DQN là target đầu tiên hợp lý.
   - Claim rõ: TD proof backend thật, update/trace vẫn là pre-ZK extension nếu chưa port sang SP1.

3. Background and Related Work
   - Offline RL và DQN/Double DQN.
   - Proof-of-Learning và proof-of-training.
   - zkML/zk proof-of-training.
   - Verifiable RL.
   - ZK+RL privacy/audit systems.

4. System and Threat Model
   - Dataset commitment.
   - Public/private fields.
   - Prover/verifier model.
   - Non-goals: honest data collection, full training proof, Adam proof, full NN proof nếu chưa có.

5. Verification Statements
   - TD MVP relation.
   - Minibatch relation nếu đã có.
   - One-step và short-trace pre-ZK relation.
   - Sampling rule và target sync semantics.

6. SP1 Backend
   - Host/guest/shared design.
   - Input/output format.
   - Relation implementation.
   - Proof generation and verification flow.

7. Experiments
   - Offline RL baseline results.
   - Python verifier short-trace benchmark.
   - SP1 proof benchmark.
   - Negative tamper rejection.
   - Optional ablation nếu tuần 4-5 làm được.

8. Discussion and Limitations
   - Single-transition hoặc minibatch TD proof chưa phải full proof-of-training.
   - Neural-network forward/backprop proof là next step.
   - Scalability hạn chế.
   - CartPole/extra env limitation.

9. Conclusion
   - Nhấn mạnh contribution đã chứng minh được.
   - Nêu lộ trình update proof, trace proof, recursive aggregation.

### Deliverables tuần 6

- Viết lại `paper/sections/introduction.tex`.
- Viết lại `paper/sections/related_work.tex`.
- Cập nhật system/threat model section.
- Cập nhật results section bằng benchmark snapshot tuần 5.
- Cập nhật discussion/limitations.
- Thêm appendix:
  - relation definitions;
  - artifact schema;
  - public/private field classification;
  - tamper-test definitions;
  - reproducibility commands.
- Chạy build paper nếu toolchain có sẵn.

### Submission decision cuối tuần 6

- Submit A*/top security nếu:
  - SP1 proof chạy ổn;
  - benchmark reproduce được;
  - negative tests đủ rõ;
  - writing đủ sắc;
  - claim không quá rộng.
- Submit Q1 journal nếu:
  - implementation chắc;
  - contribution tốt;
  - cần thêm không gian để giải thích hệ thống và limitation.
- Submit workshop/preprint nếu:
  - SP1 proof mới partial;
  - benchmark chưa đủ sạch;
  - narrative vẫn chủ yếu là roadmap.

## Acceptance criteria

Roadmap này chỉ được xem là thành công nếu:

- SP1 TD MVP generate và verify được proof thật.
- Ít nhất ba invalid witnesses fail.
- Proof time, verification time và proof size được report.
- Python verifier và SP1 backend thống nhất trên canonical test vector.
- Benchmark chạy lại được bằng command rõ ràng.
- Paper tuần 6 nói rõ full DQN training proof vẫn là future work.
- Research gap được đặt đúng giữa Proof-of-Learning, zk proof-of-training, verifiable RL và ZK+RL systems.

## Risks và fallback claims

| Risk | Impact | Fallback |
| --- | --- | --- |
| SP1 setup fail trên máy local | block ZK backend claim | dùng WSL2/Linux khác hoặc chuyển RISC Zero |
| SHA-256/Merkle semantics lệch Python | SP1 không so sánh được với verifier | khóa serialization bằng test vector trước khi tối ưu |
| SP1 proof quá chậm cho minibatch | scalability yếu | claim single-transition TD proof + Python short-trace verifier |
| One-step SGD proof quá lớn | chưa claim proof-of-update | chỉ claim TD proof, update/trace là pre-ZK |
| Paper scope quá rộng | reviewer bắt lỗi overclaim | giữ claim hẹp và precise |
| Chỉ có CartPole | RL generality yếu | thêm một discrete-control env nếu còn thời gian |

Fallback claim hierarchy:

1. Mạnh: ZK-backed offline DQN TD và minibatch verification over committed trajectories.
2. Trung bình: ZK-backed single-transition TD proof + pre-ZK update/trace verifier.
3. Yếu: pre-ZK verifier framework + research agenda, phù hợp workshop/preprint hơn Q1/A*.

## Assumptions

- Target chính là security/crypto-systems Q1/A*, không phải pure RL.
- SP1 là backend đầu tiên.
- RISC Zero là fallback hoặc comparison backend.
- Project không claim full proof-of-training trong 4-6 tuần.
- Tuần 6 mới viết lại paper hoàn chỉnh sau khi implementation và benchmark đã khóa.
