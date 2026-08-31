# Giải thích toàn diện dự án zk_offline_dqn

Tài liệu này viết cho người **chưa biết gì** về đề tài. Nó đi từ từ vựng, đến bối cảnh,
đến vì sao chọn giải pháp này, đến kiến trúc, kết quả, và cuối cùng là những câu hỏi
hội đồng nhiều khả năng sẽ hỏi kèm câu trả lời.

Mọi con số trong tài liệu lấy trực tiếp từ mã nguồn và các file provenance đã commit.
Chỗ nào chưa chứng minh được, tài liệu nói rõ là chưa.

---

## Mục lục

- [Phần I — Từ vựng](#phần-i--từ-vựng)
- [Phần II — Bối cảnh và vấn đề thực tiễn](#phần-ii--bối-cảnh-và-vấn-đề-thực-tiễn)
- [Phần III — Các hướng giải pháp và lý do chọn](#phần-iii--các-hướng-giải-pháp-và-lý-do-chọn)
- [Phần IV — Kiến trúc tổng thể](#phần-iv--kiến-trúc-tổng-thể)
- [Phần V — Chi tiết từng quan hệ được chứng minh](#phần-v--chi-tiết-từng-quan-hệ-được-chứng-minh)
- [Phần VI — Mô hình đối thủ và tám định lý](#phần-vi--mô-hình-đối-thủ-và-tám-định-lý)
- [Phần VII — Kết quả đạt được](#phần-vii--kết-quả-đạt-được)
- [Phần VIII — Đánh giá trung thực](#phần-viii--đánh-giá-trung-thực)
- [Phần IX — Câu hỏi hội đồng và cách trả lời](#phần-ix--câu-hỏi-hội-đồng-và-cách-trả-lời)

---

## Phần I — Từ vựng

Đọc phần này trước. Mọi thuật ngữ về sau đều dựa vào đây.

### I.1 Học tăng cường (Reinforcement Learning — RL)

**Bài toán.** Một *agent* (tác nhân) tương tác với một *environment* (môi trường).
Ở mỗi bước, agent thấy **trạng thái** `s`, chọn **hành động** `a`, nhận **phần thưởng** `r`
và rơi vào trạng thái mới `s'`. Nếu ván kết thúc thì cờ **done** bật. Mục tiêu: học một
*policy* (chính sách) chọn hành động sao cho tổng phần thưởng dài hạn lớn nhất.

**Transition** là bộ bốn `(s, a, r, s', done)` — một bước kinh nghiệm. Đây là đơn vị dữ liệu
nhỏ nhất trong dự án này.

**CartPole** là môi trường kinh điển: giữ một cây gậy thăng bằng trên xe đẩy. Trạng thái là
4 số thực (vị trí xe, vận tốc xe, góc gậy, vận tốc góc), hành động là 2 lựa chọn (đẩy trái/phải).
Mỗi bước giữ được gậy thì +1 điểm. **MountainCar**: đẩy xe lên đỉnh đồi, mỗi bước −1 điểm,
tối đa 200 bước — nên −200 nghĩa là *không bao giờ tới đích*.

### I.2 Q-learning và DQN

**Hàm giá trị Q.** `Q(s, a)` ước lượng tổng phần thưởng kỳ vọng nếu ở trạng thái `s` ta chọn
hành động `a` rồi chơi tối ưu về sau.

**Phương trình Bellman** là quan hệ đệ quy mà Q phải thỏa:

```
Q(s, a) = r + γ · max Q(s', a')        nếu chưa kết thúc
Q(s, a) = r                             nếu done
```

`γ` (gamma) là **hệ số chiết khấu**, thường 0.99 — phần thưởng tương lai đáng giá ít hơn
phần thưởng ngay bây giờ.

**DQN (Deep Q-Network)** dùng một mạng nơ-ron xấp xỉ hàm `Q`. Huấn luyện bằng cách giảm
sai khác giữa giá trị mạng dự đoán và giá trị Bellman nói nó *nên* là.

**TD error** (Temporal-Difference error) chính là sai khác đó:

```
target   = r + γ · max Q_target(s', a')      (hoặc = r nếu done)
td_error = Q_online(s, a) − target
```

**Target network.** DQN dùng *hai* mạng: `Q_online` đang học, và `Q_target` là bản sao đông cứng,
thỉnh thoảng mới đồng bộ lại. Nếu chỉ dùng một mạng thì mục tiêu chạy theo chính nó và huấn luyện
mất ổn định.

**Hàm mất mát SmoothL1** (còn gọi Huber): bình phương khi sai số nhỏ, tuyến tính khi sai số lớn —
để một vài mẫu bất thường không kéo lệch cả quá trình.

```
loss = 0.5 · e²        nếu |e| < β
loss = |e| − 0.5·β     nếu |e| ≥ β
```
Dự án dùng `β = 1.0`, khớp `torch.nn.SmoothL1Loss()` mặc định.

### I.3 Offline RL

**Online RL**: agent vừa học vừa tương tác với môi trường thật.

**Offline RL** (còn gọi batch RL): agent **chỉ** học từ một tập dữ liệu đã thu sẵn, không được
tương tác thêm. Quan trọng vì trong y tế, tài chính, robot công nghiệp, việc để một agent chưa
thạo tự do thử nghiệm là quá đắt hoặc quá nguy hiểm.

**Replay buffer** là tập transition đã thu. Trong offline RL nó cố định. **Minibatch** là một
nhóm nhỏ transition lấy ra để cập nhật một bước.

Đây là bối cảnh của dự án: **huấn luyện offline DQN trên một tập dữ liệu cố định, đã được cam kết.**

### I.4 Hàm băm và cây Merkle

**Hàm băm (hash)** biến dữ liệu bất kỳ thành một chuỗi độ dài cố định. **SHA-256** cho ra 256 bit
(64 ký tự hex). Ba tính chất cần nhớ:

- *Tất định*: cùng đầu vào luôn cho cùng đầu ra.
- *Một chiều*: từ hash không suy ngược ra dữ liệu.
- *Chống va chạm*: không tìm được hai dữ liệu khác nhau cho cùng hash.

**Cam kết (commitment)** dùng hash để "niêm phong" dữ liệu: công bố hash trước, tiết lộ dữ liệu sau,
ai cũng kiểm được là bạn không tráo.

**Cây Merkle** cho phép cam kết cả một *tập* dữ liệu bằng **một** hash duy nhất (gọi là **root**),
mà vẫn chứng minh được từng phần tử thuộc tập đó mà không cần đưa cả tập.

```
                root = H(H12 ‖ H34)
               /                    \
        H12 = H(H1‖H2)        H34 = H(H3‖H4)
        /        \             /        \
      H1=H(t1)  H2=H(t2)   H3=H(t3)   H4=H(t4)
```

Muốn chứng minh `t3` thuộc cây, chỉ cần đưa `t3` cùng **đường Merkle** `[H4, H12]`. Người kiểm
tự tính `H3`, rồi `H34`, rồi `root`, và so với root đã công bố. Với 1 triệu phần tử, đường Merkle
chỉ dài 20 hash thay vì 1 triệu.

**Quy ước trong dự án này** (rất quan trọng, mọi hash phải khớp bit-for-bit giữa Python và Rust):

- Lá: nối các số nguyên bằng dấu phẩy — `",".join(str(int(x)))` — rồi SHA-256, lấy dạng hex.
- Nút trong: `SHA256(bytes.fromhex(trái) + bytes.fromhex(phải))` — nối **bytes**, không nối chuỗi hex.
- Số lá lẻ: **nhân đôi** lá cuối (kiểu Bitcoin).

### I.5 Chứng minh không tiết lộ tri thức (Zero-Knowledge Proof)

Một giao thức giữa **prover** (người chứng minh) và **verifier** (người kiểm chứng), cho phép
prover thuyết phục verifier rằng *"tôi biết một dữ liệu thỏa điều kiện X"* mà **không tiết lộ dữ liệu đó**.

Ba tính chất:

| Tính chất | Nghĩa |
|---|---|
| **Completeness** (đầy đủ) | Nếu phát biểu đúng và prover trung thực, verifier luôn chấp nhận. |
| **Soundness** (đúng đắn) | Nếu phát biểu sai, prover gian lận **không thể** làm verifier chấp nhận (trừ xác suất cực nhỏ). |
| **Zero-knowledge** | Verifier không học được gì ngoài chính sự thật của phát biểu. |

**Witness** (nhân chứng) là dữ liệu bí mật prover biết. **Public input** là dữ liệu cả hai bên
cùng thấy. Ví dụ trong dự án: `dataset_root` là public, còn transition cụ thể và trọng số mạng
là private witness.

**Relation** (quan hệ) là điều kiện toán học nối public input với witness. Trọn vẹn dự án này
xoay quanh việc **định nghĩa các relation cho huấn luyện offline DQN** rồi chứng minh chúng.

> **Điểm cần nhớ khi bảo vệ:** đóng góp khoa học chính nằm ở việc *định nghĩa relation*,
> không phải ở việc dùng ZK. ZK là công cụ; relation là nội dung.

### I.6 SNARK, STARK, và zkVM

**SNARK** (Succinct Non-interactive ARgument of Knowledge): proof rất ngắn, kiểm rất nhanh.
**Groth16** là một hệ SNARK nổi tiếng — proof chỉ 3 phần tử nhóm elliptic (~200–360 byte),
kiểm bằng 3 phép *pairing*, mất mili-giây. Nhược điểm: cần **trusted setup** riêng cho mỗi mạch.

**STARK**: không cần trusted setup, an toàn trước máy tính lượng tử, nhưng proof lớn hơn nhiều
(vài MB). SP1 sinh proof STARK.

**Mạch (circuit)**: cách truyền thống là biểu diễn phép tính thành một mạch số học rồi chứng minh
mạch chạy đúng. Viết mạch bằng tay rất khó, nhất là với rẽ nhánh và điều kiện.

**zkVM (zero-knowledge Virtual Machine)**: thay vì viết mạch, ta viết **chương trình bình thường**
(ở đây là Rust), biên dịch sang RISC-V, và zkVM chứng minh rằng *chương trình đó đã chạy đúng*.
Đổi lại chi phí cao hơn mạch viết tay, nhưng lập trình dễ hơn hàng bậc.

**SP1** là zkVM của Succinct Labs, phiên bản dự án dùng là `6.1.0`.

- **guest**: chương trình chạy *bên trong* zkVM.
- **host**: chương trình chạy bên ngoài, nạp dữ liệu vào guest, gọi prove và verify.
- **cycle**: một lệnh RISC-V. Số cycle là thước đo chi phí chính — càng nhiều cycle, prove càng lâu và càng tốn bộ nhớ.
- **precompile**: phép tính hay dùng (như SHA-256) được cài sẵn tối ưu, rẻ hơn nhiều so với để guest tự tính.

**Recursion (đệ quy)**: chứng minh *bên trong* một proof rằng một proof khác là hợp lệ. Cho phép
gộp nhiều proof thành một. Rất đắt vì máy ảo phải mô phỏng lại toàn bộ số học của verifier.

**Aggregation (gộp)**: gộp nhiều proof con thành một phát biểu chung.

### I.7 Số học fixed-point và vì sao bắt buộc

Máy tính biểu diễn số thực bằng **floating-point** (dấu phẩy động). Vấn đề: phép cộng
floating-point **không có tính kết hợp** — `(a+b)+c` có thể khác `a+(b+c)` — và kết quả phụ thuộc
phần cứng, thứ tự thực hiện, phiên bản thư viện.

Trong ZK, prover và verifier **phải** ra kết quả giống hệt nhau đến từng bit. Nên dự án dùng
**fixed-point**: biểu diễn số thực bằng **số nguyên** đã nhân với một hệ số.

```
FP_SCALE = 1000        →  0.75 được lưu là 750
GAMMA_FP = 990         →  γ = 0.99
SMOOTH_L1_BETA_FP = 1000  →  β = 1.0
```

Phép nhân hai số fixed-point phải chia lại cho scale:

```
fixed_point_mul(a, b) = (a * b) // FP_SCALE     ← chia lấy nguyên, KHÔNG làm tròn
```

> **Bất biến quan trọng:** dùng `//` (cắt phần thập phân), không dùng `round`. Chỉ cần một chỗ
> làm tròn khác đi là Python và Rust ra hai kết quả khác nhau, và toàn bộ hệ sụp.

---

## Phần II — Bối cảnh và vấn đề thực tiễn

### II.1 Tình huống cụ thể

Hình dung một công ty bán mô hình RL đã huấn luyện — ví dụ chính sách điều khiển cho robot kho hàng,
hoặc chính sách gợi ý điều trị. Công ty nói:

> *"Chúng tôi huấn luyện mô hình này trên 100.000 transition thu thập từ hệ thống thật,
> bằng thuật toán DQN với γ=0.99, learning rate 0.001, trong 5.000 bước."*

Người mua **không có cách nào kiểm chứng**. Họ chỉ thấy trọng số cuối cùng.

### II.2 Kẻ gian lận được lợi gì

| Kiểu gian lận | Động cơ |
|---|---|
| Huấn luyện trên dữ liệu khác | Dữ liệu thật kém chất lượng; dùng dữ liệu đẹp hơn rồi nói dối |
| Sửa phần thưởng trong dữ liệu | Làm mô hình trông tốt hơn thực tế |
| Bỏ bớt bước huấn luyện | Tiết kiệm chi phí tính toán, vẫn thu tiền như đã hứa |
| Dùng siêu tham số khác | Che giấu việc phải dò rất nhiều lần mới ra kết quả |
| Ghép các đoạn huấn luyện rời rạc | Giả vờ là một quá trình liên tục |

### II.3 Vì sao không thể chỉ "chạy lại để kiểm tra"

- **Dữ liệu thường là bí mật.** Hồ sơ bệnh án, log giao dịch — không thể đưa cho người kiểm.
- **Trọng số là tài sản.** Đưa ra là mất giá trị thương mại.
- **Chạy lại rất tốn.** Huấn luyện lớn tốn hàng nghìn giờ GPU.
- **Không tất định.** Floating-point, đa luồng, phiên bản thư viện — chạy lại thường không ra
  đúng con số cũ, nên khác biệt không phân biệt được là do gian lận hay do nhiễu.

### II.4 Phát biểu bài toán

> Cho một tập dữ liệu đã được cam kết công khai bằng `dataset_root`, và một quy trình huấn luyện
> đã công bố, hãy tạo ra bằng chứng thuyết phục rằng mô hình được huấn luyện **đúng như đã nói**,
> mà **không tiết lộ** dữ liệu lẫn trọng số.

---

## Phần III — Các hướng giải pháp và lý do chọn

### III.1 Bốn hướng khả dĩ

| Hướng | Cách làm | Vì sao không đủ |
|---|---|---|
| **Bên thứ ba tin cậy** | Thuê kiểm toán viên xem quá trình | Chuyển vấn đề tin cậy chứ không giải quyết; kiểm toán viên có thể sai hoặc bị mua |
| **TEE** (vùng thực thi tin cậy, như Intel SGX) | Chạy huấn luyện trong enclave phần cứng | Tin vào nhà sản xuất chip; đã có nhiều lỗ hổng side-channel bị công bố |
| **Chạy lại** | Người kiểm huấn luyện lại | Lộ dữ liệu, tốn kém, và không tất định |
| **Zero-knowledge proof** | Chứng minh toán học | Không cần tin ai; giấu được dữ liệu — **nhưng rất đắt** |

Dự án chọn hướng thứ tư, và toàn bộ khó khăn kỹ thuật nằm ở chữ *"rất đắt"*.

### III.2 Trong ZK, chọn công nghệ nào

Tài liệu quyết định gốc nằm ở `docs/archive/internal_manifests/backend_choice.md`. Năm ứng viên
được xét:

| Ứng viên | Loại | Đánh giá lúc đó |
|---|---|---|
| **SP1** | zkVM | **Được chọn** |
| RISC Zero | zkVM | Phương án thay thế chính |
| Noir | ngôn ngữ mạch | Giai đoạn sau, khi relation đã ổn định |
| Circom | mạch | Tối ưu về sau |
| Halo2 | khung mạch bậc thấp | Hướng nghiên cứu dài hạn |

**Lý do chọn zkVM thay vì mạch viết tay:** quan hệ cần chứng minh **không phải số học thuần**.
Nó có SHA-256, duyệt đường Merkle, và **rẽ nhánh có điều kiện**:

```
nếu done:  target = r
ngược lại: target = r + γ·max Q_target(s')

nếu |td_error| < β:  loss = vùng bậc hai
ngược lại:           loss = vùng tuyến tính
```

Mạch số học xử lý rẽ nhánh rất vụng — phải tính *cả hai* nhánh rồi chọn bằng phép nhân với bit
điều kiện. zkVM cho phép viết `if/else` bình thường.

**Lý do chọn SP1 thay vì RISC Zero:** viết bằng Rust, luồng prove/verify đơn giản, hệ sinh thái
đang phát triển nhanh. Tài liệu quyết định cũng ghi rõ tiêu chí lúc đó:

> *"The first research goal is not maximum constraint efficiency... developer speed matters more
> than proof-size optimality at this stage."*

**Quyết định này tự hẹn ngày xét lại**, và tài liệu ghi: *"custom arithmetic circuits should be
deferred until the relation is more stable"*. Đây là câu trả lời tốt nếu hội đồng hỏi
"sao không dùng mạch tối ưu hơn".

---

## Phần IV — Kiến trúc tổng thể

### IV.1 Ý tưởng trung tâm: cài đặt hai lần

Đây là điều quan trọng nhất về kiến trúc, và cũng là câu trả lời cho câu hỏi
*"làm sao biết code của các anh đúng?"*

```
                    test vector đã khoá (JSON)
                    public inputs + private witness
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
       Oracle Python                 Guest Rust
       relations/ (3.790 dòng)       zk_backend/*/sp1/shared
                 │                         │
                 └────────────┬────────────┘
                              ▼
               Hai bên PHẢI cho cùng kết quả
               khớp → ghi provenance;  lệch → lỗi
```

Quan hệ được cài **hai lần, bằng hai ngôn ngữ, bởi hai đường mã không dùng chung gì**. Người
đọc kiểm được cả hai bản và tự xác nhận chúng cùng ngữ nghĩa. Đây là lý do artifact này đáng
tin hơn một hệ chỉ có mạch ZK viết tay mà không ai đọc nổi.

### IV.2 Tám tầng

| # | Tầng | Vị trí | Quy mô | Nhiệm vụ |
|---|---|---|---|---|
| 0 | Nguồn gốc dữ liệu | `scripts/data/` | 683 dòng | collect → audit → commit → verify, sinh `dataset_root` |
| 1 | Huấn luyện | `scripts/training/`, `rl_benchmarks/` | 2.012 dòng | Huấn luyện các baseline, sinh checkpoint |
| 2 | Xuất artifact | `scripts/artifacts_export/` | 2.961 dòng | Biến lần chạy thành test vector JSON fixed-point |
| 3 | **Relations** | `zk_offline_dqn/relations/` | 3.790 dòng | **Lõi ngữ nghĩa** — định nghĩa thế nào là đúng |
| 4 | Verifiers | `zk_offline_dqn/verifiers/` | 1.134 dòng | Nạp JSON, kiểm schema, gọi relation |
| 5 | Backend SP1 | `zk_backend/*/sp1/` | 8 workspace, 60 file `.rs` | guest/host/shared — nhánh Rust |
| 6 | Mô tả backend | `zk_offline_dqn/backends/sp1/` | 1.418 dòng | Trả argv, **không bao giờ** tự chạy prove |
| 7 | Đo đạc, báo cáo | `proof_benchmarks/`, `tamper_benchmarks/`, `experiments/` | 4.827 dòng | Lắp Table 1, 2, 3 từ provenance |

### IV.3 Luồng dữ liệu đầu-cuối

```
1. Thu dữ liệu    → audit (chạy lại môi trường, kiểm reward/next_state/done)
2. Commit         → cây Merkle → dataset_root công bố
3. Huấn luyện     → checkpoint từng bước, hash liên kết thành chuỗi
4. Xuất vector    → lượng tử hoá fixed-point, đóng gói public/private
5. Kiểm hai nhánh → oracle Python ‖ guest Rust, phải khớp
6. Prove SP1      → proof.bin + provenance (metrics, tamper_report, ...)
7. Lắp bảng       → Table 1/2/3
8. Paper          → 8 định lý, mỗi định lý trỏ về code + test + provenance
```

### IV.4 Ranh giới public / private

Đây là điểm thường bị hỏi. Ví dụ với quan hệ minibatch TD:

| Public (ai cũng thấy) | Private (giữ bí mật) |
|---|---|
| `dataset_root` | transition cụ thể `(s,a,r,s',done)` |
| `batch_size`, `leaf_indices` | đường Merkle |
| `loss_type`, `batch_loss_fp` | trọng số mạng |
| `checkpoint_sha256` | các giá trị Q trung gian |
| hash của state dict online/target | gradient |

Người kiểm biết *loss là bao nhiêu* và *dữ liệu nào đã được cam kết*, nhưng không biết
*dữ liệu là gì* và *mạng nặng bao nhiêu*.

---

## Phần V — Chi tiết từng quan hệ được chứng minh

Có 10 quan hệ trong `relations/`. Dưới đây là những cái quan trọng nhất.

### V.1 Merkle membership — transition thuộc tập đã cam kết

**Kiểm:** cho một transition và đường Merkle, tính lại root và so với `dataset_root` công bố.

**Chặn được:** dùng dữ liệu không nằm trong tập đã cam kết; sửa transition sau khi commit;
làm giả đường Merkle.

### V.2 TD MVP — số học Bellman đúng

**Kiểm** (tất cả bằng fixed-point):

```
1. target_fp  = reward_fp                                    nếu done
   target_fp  = reward_fp + (GAMMA_FP · q_target_max) // 1000  nếu chưa
2. td_error_fp = q_online_action_fp − target_fp
3. loss_fp     = SmoothL1(td_error_fp)
4. mọi giá trị khai báo phải khớp giá trị tính lại
```

**Chặn được:** khai gian target, sai gamma, tính sai loss, đảo nhánh done.

Đây là quan hệ **nền tảng** — `forward_td_mlp` và `one_step_sgd_tiny` đều uỷ quyền cho nó.

### V.3 Forward-TD MLP — mạng nơ-ron tính đúng

**Điểm quan trọng cần nhấn mạnh khi bảo vệ:** guest **không** nhận giá trị Q có sẵn.
Nó **tính lại từ trọng số**:

```rust
for (row, bias_fp) in layer.weight.iter().zip(layer.bias.iter()) {
    let mut acc = *bias_fp;
    for (w_fp, x_fp) in row.iter().zip(activations.iter()) {
        acc += fixed_point_mul(*w_fp, *x_fp, fp_scale);   // tích ma trận-vector
    }
    pre.push(acc);
}
// ReLU + mask
```

rồi `assert_trace_eq` so trace khai báo với trace tính lại: `pre_activations`, `relu_masks`,
`outputs` đều phải khớp.

Mạng trong vector canonical: **[4, 16, 16, 2]**, khoảng 386 tham số.

### V.4 One-step SGD tiny — một bước cập nhật trọng số đúng

**Kiểm:** đạo hàm SmoothL1, lan truyền ngược, và trọng số sau khi cập nhật.

```
loss_grad_fp = SmoothL1'(td_error_fp)
gradient     = backprop(loss_grad, forward_trace)
post_model   = pre_model − lr · gradient
```

Guest tính lại cả gradient lẫn trọng số mới rồi đối chiếu. Mạng: **[4, 8, 2]**, ~58 tham số.

### V.5 Short trace / Checkpoint chain — chuỗi bước không đứt đoạn

**Kiểm:** hash checkpoint đầu ra của bước `i` phải bằng hash checkpoint đầu vào của bước `i+1`.

**Chặn được:** bỏ bước, đảo thứ tự bước, ghép hai đoạn huấn luyện rời rạc, sai thời điểm
đồng bộ target network.

### V.6 Training fragment — một đoạn k bước

Gộp k bước cập nhật thành một phát biểu. Dự án chứng minh được `k ∈ {1, 4, 8}`.

### V.7 Training aggregation — gộp nhiều đoạn

Đây là phần phức tạp nhất, và có **hai chế độ**:

**Chế độ 1 — proof-manifest chain** (`T ∈ {32, 64, 128}`)

Quan hệ ràng buộc hash của các proof con, hash public input của chúng, thứ tự chunk, liên kết
checkpoint. Nhưng guest **không** verify mật mã proof con — nó tin rằng ai đó đã verify bên ngoài.

**Chế độ 2 — recursive** (`T ∈ {16, 32, 64}`)

Guest **thực sự chạy verifier** trên từng proof con bên trong SP1:

```rust
match proof_mode {
    NATIVE_CHILD_PROOF_MODE => verify_native_child_proof(child, &public_values),
    GROTH16_CHILD_PROOF_MODE => Groth16Verifier::verify(...),
    ...
}
```

Chấp nhận proof gộp **kéo theo** các proof con đều hợp lệ. Đây là khác biệt về chất, và là
kết quả mới nhất của dự án.

---

## Phần VI — Mô hình đối thủ và tám định lý

### VI.1 Đối thủ là ai

Theo `paper/sections/threat_model.tex`: **một prover ác ý, có giới hạn tính toán, kiểm soát toàn bộ
quá trình huấn luyện**, muốn tạo ra proof thuyết phục nhưng gian dối. Bảy nhóm tấn công:

| Mã | Nhóm tấn công | Ví dụ |
|---|---|---|
| A1 | Giả mạo dữ liệu | Sửa reward, action, done, next_state; dùng transition ngoài tập |
| A2 | Giả mạo cam kết | Sửa đường Merkle, leaf index, leaf hash, root |
| A3 | Giả mạo lấy mẫu | Đổi chỉ số minibatch, lặp chỉ số trong batch |
| A4 | Giả mạo tính toán | Sửa Q, target, loss, đạo hàm, gradient, delta SGD |
| A5 | Giả mạo chuỗi | Bỏ bước, đảo bước, đứt chuỗi checkpoint, sai thời điểm sync |
| A6 | Giả mạo gộp | Đảo chunk, tráo proof con, hash public input không nhất quán |
| A7 | Giả mạo kiểm chứng | Verify proof với public input khác cái đã cam kết |

### VI.2 Tám định lý

| # | Định lý | Nội dung |
|---|---|---|
| 1 | Replay membership soundness | Transition thuộc tập đã cam kết |
| 2 | Audited dataset commitment soundness | Cam kết dữ liệu đã qua audit là đúng |
| 3 | Bellman target correctness | Target tính đúng theo Bellman |
| 4 | Forward, backprop, update correctness | Xuôi, ngược, cập nhật đều đúng |
| 5 | Checkpoint-chain soundness | Chuỗi checkpoint không đứt |
| 6 | Training-fragment soundness | Đoạn k bước đúng |
| 7 | Chunk-chain **and recursive** aggregation soundness | Gộp đúng, ở cả hai chế độ |
| 8 | Zero-knowledge and privacy boundary | Ranh giới những gì bị lộ |

Mỗi định lý được ánh xạ sang relation cụ thể, mã SP1, test, và file provenance trong
`docs/theorem_artifact_map.md`.

### VI.3 Ranh giới rõ ràng: những gì dự án KHÔNG chứng minh

Đây là phần **phải thuộc** khi bảo vệ. Trung thực về giới hạn mạnh hơn nhiều so với bị hỏi vặn.

- **Không** chứng minh toàn bộ quá trình huấn luyện DQN từ đầu đến cuối.
- **Không** chứng minh Adam — chỉ SGD đơn giản.
- **Không** chứng minh dữ liệu công khai (D4RL/Minari) được thu thập trung thực; chỉ cam kết
  tính toàn vẹn nguồn.
- **Không** chứng minh với batch size > 1.
- **Không** thử recursion ở `T = 128`, **không** thử child proof dạng PLONK.
- Recursion **đòi hỏi GPU** CUDA khoảng 20 GB; prover CPU không chạy nổi trong 61 GB.

Có một chương trình quét tự động (`scripts/experiments/check_paper_claims.py`) canh không cho
paper nói quá những ranh giới này.

---

## Phần VII — Kết quả đạt được

### VII.1 Table 1 — hiệu năng RL

48 dòng: **20 hoàn tất**, 28 bỏ qua do thuật toán không tương thích môi trường (thuật toán
hành động rời rạc không chạy trên môi trường liên tục, và ngược lại).

| Dataset | Baseline | Phần thưởng trung bình |
|---|---|---|
| cartpole-random-v1 | offline_dqn | 161,9 ± 49,9 |
| cartpole-random-v1 | double_dqn | 192,9 ± 69,3 |
| cartpole-random-v1 | cql_lite | 199,0 ± 34,8 |
| cartpole-random-v1 | bc | 11,0 ± 0,9 |
| mountaincar-random-v1 | offline_dqn | −200,0 ± 0,0 |

Kiến trúc huấn luyện: `hidden_dim = 64`, tức **[4, 64, 64, 2]**, khoảng 4.610 tham số.
Ba seed, 5.000 bước.

### VII.2 Table 2 — chi phí chứng minh ZK

27 dòng: **20 proof-backed**, 4 chưa hỗ trợ, 3 chỉ execute, **0 thất bại tài nguyên**.

Các quan hệ có proof thật: TD MVP, Merkle membership (kèm scaling tới 100k lá), Forward-TD MLP,
one-step SGD, short trace, training update (batch 1), fragment `k ∈ {1,4,8}`,
aggregation manifest `T ∈ {32,64,128}`, và **recursion** `T ∈ {16,32,64}`.

Số đo recursion trên NVIDIA A10G, toolchain pin `sp1up v6.1.0`:

| Cấu hình | Cycles | Thời gian prove |
|---|---|---|
| recursive T=16 | 309.406.040 | 141,8 s |
| binary tree T=16 | 308.585.812 | 153,6 s |
| recursive T=32 | 615.456.629 | 300,8 s |
| recursive T=64 | 1.230.443.488 | 580,4 s |
| Groth16 child T=16 | 6.162.312.409 | 1589,7 s |

Đỉnh VRAM đo riêng bằng một lượt profiling trên cùng các cấu hình (provenance không ghi
trường này): 18.437 MiB ở T=16, T=32 và biến thể Groth16; 18.469 MiB ở T=64; 18.373 MiB
ở cây nhị phân.

**Phát hiện đáng chú ý:** số cycle chênh nhau **20 lần** mà đỉnh bộ nhớ dao động **0,5%**.
Chi phí bộ nhớ là **hằng số dựng mạch recursion**, không phụ thuộc khối lượng. Đây là lý do
prover CPU thất bại giống hệt nhau ở 30 GB và 61 GB — hằng số đó nằm trên cả hai.

### VII.3 Table 3 — kháng giả mạo

**236 case**, 233 bị từ chối đúng như mong đợi, 3 không áp dụng, **0 case gian lận được chấp nhận**,
trải 19 nhóm tấn công.

Trong đó 65 case đặc thù cho recursion. Case mạnh nhất về mặt lập luận:

> `tamper_individually_valid_child_proofs_broken_chain` — **mọi proof con đều hợp lệ riêng lẻ**,
> nhưng chuỗi checkpoint giữa chúng bị cắt. Vẫn bị từ chối.

Một cơ chế gộp ngây thơ chỉ kiểm tính hợp lệ của từng con sẽ chấp nhận trường hợp này.

### VII.4 Kích thước proof

| Dạng | Kích thước |
|---|---|
| STARK (SP1 gốc) | ~2,79 MB |
| Groth16 (sau khi wrap) | **356 byte** |

Nhỏ hơn khoảng **7.800 lần**. Đổi lại, verify Groth16 *bên trong* mạch tốn 6,16 tỷ cycles,
gấp 20 lần đường native — nên Groth16 hữu ích như **lớp nén cuối**, không phải như cơ chế gộp.

---

## Phần VIII — Đánh giá trung thực

### VIII.1 Điểm mạnh

**Kỷ luật claim được máy canh.** Có chương trình quét paper tìm cụm từ vượt phạm vi và báo lỗi.
Rất ít artifact nghiên cứu có cơ chế này.

**Kháng giả mạo là bằng chứng mạnh nhất.** 236 case, 19 nhóm, không case nào lọt. Đây không phải
"chúng tôi tin relation đúng" mà là "chúng tôi đã thử phá 236 kiểu và đều bị chặn".

**Cài đặt hai lần độc lập.** Python và Rust, không dùng chung mã. Khớp nhau là bằng chứng, không
phải trùng lặp.

**Recursion thật.** Guest verify proof con bên trong SP1, ở `T` tới 64. Trước đó bất khả thi trên CPU.

**Phần ML được kiểm thật.** Không nhận giá trị có sẵn — tính lại cả xuôi lẫn ngược.

### VIII.2 Điểm yếu

**1. CI không chạy cổng kiểm tra nào.** `make check` có bốn cổng (unittest 234 test, quét claim,
kiểm nguồn báo cáo, kiểm bản đồ định lý). GitHub Actions chỉ chạy `run_full_regression.py`
(15 check), **không chứa cổng nào trong bốn**. Nghĩa là kỷ luật claim hiện phụ thuộc vào việc
con người nhớ gõ lệnh.

**2. Table 1 và Table 2 nói về hai mạng khác nhau.**

| | Kiến trúc | Tham số |
|---|---|---|
| Table 1 (kết quả RL) | [4, 64, 64, 2] | ~4.610 |
| Table 2 `forward_td_mlp` | [4, 16, 16, 2] | ~386 |
| Table 2 `one_step_sgd_tiny` | [4, 8, 2] | ~58 |

Chênh 12 đến 80 lần. Paper dùng chữ "tiny" nhiều chỗ mà chưa ghi con số cụ thể.

**3. Offline DQN chỉ chạy được ở một môi trường.** CartPole cho 161,9. MountainCar cho −200,
tức sàn timeout — chính sách không bao giờ tới đích. PointMaze không chạy được thuật toán rời rạc.

**4. Quy mô còn nhỏ.** Batch size 1, mạng vài chục đến vài trăm tham số, SGD chứ không Adam.

**5. Recursion đòi GPU.** Hạ thấp khả năng người khác tái lập.

**6. Rò rỉ ranh giới kiến trúc.** `relations/training_aggregation.py:1085` đọc hệ thống file,
trái với nguyên tắc "relation là oracle thuần".

### VIII.3 Vị trí so với công trình liên quan

Verifiable ML đã được nghiên cứu nhiều cho **suy luận** (inference) — SafetyNets và các công trình
sau. Điểm khác biệt của dự án này: quan hệ được chứng minh là về **huấn luyện**, không phải suy luận.
Cụ thể hơn nữa là **huấn luyện offline RL**, nơi ngoài phép tính mạng nơ-ron còn có số học Bellman,
lấy mẫu từ replay buffer đã cam kết, và chuỗi checkpoint.

---

## Phần IX — Câu hỏi hội đồng và cách trả lời

### Q1. "Đóng góp khoa học của em là gì? Dùng thư viện có sẵn thì có gì mới?"

SP1 là công cụ, không phải đóng góp. Đóng góp là **định nghĩa quan hệ**: phát biểu chính xác,
bằng số học tất định, thế nào là *một bước huấn luyện offline DQN đúng* — gồm tư cách thành viên
của transition trong tập đã cam kết, số học Bellman, lan truyền xuôi và ngược, liên kết checkpoint,
và cách gộp nhiều đoạn. Chưa có công trình nào làm điều này cho huấn luyện offline RL; các công
trình trước tập trung vào suy luận.

Đóng góp thứ hai là **bộ đánh giá kháng giả mạo 236 case** — nó biến "chúng tôi tin là đúng"
thành "chúng tôi đã thử phá và đây là kết quả".

### Q2. "Làm sao biết code của em đúng?"

Quan hệ được cài **hai lần độc lập**: một bản Python trong `relations/`, một bản Rust trong
`zk_backend/*/sp1/shared/`. Hai bản không dùng chung mã. Với mỗi test vector, cả hai phải cho
cùng kết quả; lệch là báo lỗi. Thầy có thể đọc cả hai bản và tự kiểm chúng cùng ngữ nghĩa.

Ngoài ra có 234 unit test, 236 case tamper, và mọi định lý trong paper đều trỏ về file mã,
file test, và file provenance cụ thể.

### Q3. "Mạng của em quá nhỏ, có ý nghĩa gì không?"

Em thừa nhận đây là giới hạn. Mạng được chứng minh có 58–386 tham số, trong khi mạng cho ra kết
quả RL có ~4.610 tham số.

Nhưng đóng góp không phải "chứng minh được mạng lớn" — hiện chưa ai làm được. Đóng góp là
**định nghĩa quan hệ và chứng minh nó chặt chẽ trên vector canonical**, cộng với **số đo chi phí thật**
để người sau biết bức tường nằm ở đâu. Ví dụ: em đo được recursion tốn ~153 triệu cycles cho mỗi
proof con, và bộ nhớ là hằng số 18,4 GB không phụ thuộc khối lượng — đó là dữ liệu chưa từng có.

### Q4. "Vì sao MountainCar cho −200?"

−200 là sàn timeout: chính sách không bao giờ tới đích. Nguyên nhân là dataset thu bằng chính sách
ngẫu nhiên, mà MountainCar cần một chuỗi hành động khá dài mới lên được đỉnh — chính sách ngẫu
nhiên gần như không bao giờ tạo ra chuỗi đó, nên trong dữ liệu không có tín hiệu để học.
Đây là giới hạn của **dữ liệu**, không phải của phương pháp chứng minh.

### Q5. "Vì sao dùng zkVM mà không dùng mạch tối ưu như Halo2 hay Circom?"

Vì quan hệ không phải số học thuần: nó có SHA-256, duyệt Merkle, và rẽ nhánh có điều kiện theo
`done` và theo vùng của SmoothL1. Mạch số học phải tính cả hai nhánh rồi chọn bằng phép nhân,
rất cồng kềnh và dễ sai.

Quyết định này được ghi lại từ đầu kèm điều kiện xét lại: *"custom arithmetic circuits should be
deferred until the relation is more stable"*. Giờ quan hệ đã ổn định, nên chuyển sang mạch viết
tay là hướng phát triển hợp lý tiếp theo — nhưng phải chấp nhận đánh đổi: mạch viết tay rẻ hơn
nhưng **rất khó đọc**, mà khả năng đọc được chính là thứ làm artifact này đáng tin.

### Q6. "Fixed-point có làm sai lệch kết quả không?"

Có, và đó là đánh đổi có chủ đích. `FP_SCALE = 1000` nghĩa là độ phân giải 0,001. Sai số lượng
tử hoá tích luỹ qua các bước.

Nhưng floating-point **không dùng được** trong ZK: phép cộng không có tính kết hợp, kết quả phụ
thuộc phần cứng và thứ tự thực hiện. Prover và verifier phải ra kết quả giống nhau đến từng bit.
Nên phát biểu của em là về **tương đương số học số nguyên**, không phải về việc tái hiện chính
xác PyTorch — và paper nói rõ điều đó.

### Q7. "Recursion đòi GPU thì ai kiểm chứng lại được?"

Đây là giới hạn thật và em ghi rõ trong paper. Cần GPU CUDA compute capability ≥ 8.0 với ≥ 20 GB
bộ nhớ — ví dụ NVIDIA A10G, thuê khoảng 1 USD/giờ.

Em cũng đã khoá được **một** case recursion vào repo (bản dùng child Groth16, chỉ 13 KB) để
dòng đó tái lập chính xác. Các case còn lại nặng 5–20 MB vì nhúng bytes proof con nên không
commit được — cùng lý do repo không commit `proof.bin`.

### Q8. "Nếu kẻ gian có tất cả proof con hợp lệ nhưng ghép sai thì sao?"

Bị chặn. Đó chính là case `tamper_individually_valid_child_proofs_broken_chain` trong bộ kiểm
thử: mọi proof con hợp lệ riêng lẻ, nhưng chuỗi checkpoint bị cắt — quan hệ vẫn từ chối, với
lý do "checkpoint link mismatch". Một cơ chế gộp chỉ kiểm tính hợp lệ của từng con sẽ bỏ lọt
trường hợp này.

### Q9. "Zero-knowledge ở chỗ nào? Em có giấu được gì không?"

Public input gồm `dataset_root`, kích thước batch, chỉ số lá, loại loss, giá trị loss, và các hash
cam kết. Private witness gồm transition cụ thể, đường Merkle, trọng số mạng, các giá trị Q trung
gian, và gradient.

Nên người kiểm biết *loss bằng bao nhiêu* và *dữ liệu nào đã được cam kết*, nhưng không biết
*dữ liệu là gì* và *mạng nặng bao nhiêu*. Định lý 8 phát biểu chính xác ranh giới này.

### Q10. "Hướng phát triển tiếp theo là gì?"

Bốn hướng, xếp theo tỉ lệ lợi ích trên công sức:

1. **Đưa `make check` vào CI** — hiện các cổng kiểm tra không tự chạy.
2. **Chứng minh một quan hệ trên đúng kiến trúc [4, 64, 64, 2]** mà Table 1 dùng, để hai bảng
   nói về cùng một hệ thống.
3. **Folding scheme (Nova/HyperNova)** — né hẳn việc verify proof trong mạch. Huấn luyện là
   tính toán tuần tự nên rất hợp với IVC.
4. **SnarkPack** — gộp các proof Groth16 *bên ngoài* mạch, tránh chi phí 6,16 tỷ cycles.
   Điều kiện đã thỏa: SP1 v6.1.0 chỉ có một khoá kiểm chứng Groth16 dùng chung.

---

## Phụ lục — Lệnh hay dùng

```bash
# Cài đặt
pip install -r requirements.lock || pip install -r requirements.txt
pip install -e .

# Kiểm tra nhanh
python -m compileall zk_offline_dqn scripts tests    # ~0.1 s

# Toàn bộ cổng kiểm tra
make check          # unittest 234 + quét claim + nguồn báo cáo + bản đồ định lý

# Một test đơn
python -m unittest tests.unit.test_core_helpers

# Sinh lại bảng cho paper
python scripts/experiments/generate_paper_reports.py

# Chứng minh SP1 (nặng, cần toolchain)
sp1up --version v6.1.0
RUN_SP1_PROVE=1 cargo run --release -p <host> -- --prove
```

**Lưu ý:** chạy từ thư mục gốc, đặt `PYTHONPATH=.`. Makefile dùng cú pháp Unix nên trên Windows
cần Git Bash hoặc WSL.
