# Giải thích toàn cảnh dự án

Tài liệu này dành cho người đọc muốn hiểu **dự án làm gì, mỗi công cụ là gì, và
vì sao chọn nó** — không giả định người đọc đã biết zero-knowledge proof hay
offline reinforcement learning. Các tài liệu khác trong `docs/` mô tả chi tiết
cài đặt bằng tiếng Anh; file này là bản dẫn nhập và bối cảnh, viết bằng tiếng
Việt.

Mọi con số ở đây là **số đo đã chạy**, không phải mục tiêu. Chỗ nào chưa đo thì
ghi rõ là chưa đo.

---

## 1. Bài toán: vì sao cần chứng minh việc huấn luyện

### Tình huống

Một công ty nộp cho cơ quan quản lý một chính sách điều khiển đã huấn luyện —
ví dụ chính sách lái xe hoặc chính sách kê thuốc. Cơ quan quản lý muốn biết:
chính sách này **có thật sự được huấn luyện từ tập dữ liệu đã công bố không**,
hay ai đó đã sửa dữ liệu cho kết quả đẹp hơn?

Một bên không trung thực có nhiều cách gian lận:

- Sửa một giá trị **phần thưởng** trong dữ liệu để chính sách trông tốt hơn.
- Đổi cờ **kết thúc episode** để giấu các quỹ đạo thất bại thảm hại.
- Thay **giá trị mục tiêu** trong công thức học để che sai số.
- Sửa **gradient** để giấu việc can thiệp mô hình.

Vấn đề: nếu chỉ đưa mô hình cuối cùng, không ai kiểm được. Còn nếu đưa toàn bộ
dữ liệu và quá trình huấn luyện thì lộ dữ liệu — thứ thường là bí mật kinh doanh
hoặc dữ liệu bệnh nhân.

### Zero-knowledge proof giải quyết đúng mâu thuẫn này

**Zero-knowledge proof** (chứng minh không tiết lộ tri thức) là một kỹ thuật mật
mã cho phép:

> Bên A chứng minh cho bên B rằng "tôi đã thực hiện đúng phép tính này", mà
> **không cần cho B xem dữ liệu đầu vào**.

B chỉ cần kiểm một mẩu bằng chứng nhỏ. Nếu A gian lận, bằng chứng sẽ không qua
được phép kiểm — trừ một xác suất nhỏ đến mức bỏ qua được.

Hai vai trò cần nhớ suốt tài liệu:

| Vai | Tên gọi | Việc |
| --- | --- | --- |
| Bên tính toán và tạo bằng chứng | **prover** | tốn rất nhiều tài nguyên |
| Bên kiểm bằng chứng | **verifier** | rất rẻ, thường dưới 1 giây |

Sự bất đối xứng đó chính là điều làm kỹ thuật này có giá trị: dồn chi phí về
phía người phải chứng minh, người kiểm gần như không tốn gì. Trong dự án này,
proof đắt nhất mất **1.596 giây** để tạo nhưng chỉ **0,054 giây** để kiểm.

---

## 2. Các thuật ngữ nền

### 2.1 Offline reinforcement learning

**Reinforcement learning** (học tăng cường) là kiểu học mà một tác nhân học
bằng cách hành động và nhận phần thưởng, thay vì học từ các cặp câu hỏi–đáp án
có sẵn.

**Offline** nghĩa là tác nhân **không được tương tác với môi trường** trong lúc
học. Nó chỉ có một tập dữ liệu cố định đã ghi sẵn — gọi là **replay dataset** —
gồm nhiều dòng, mỗi dòng là một **transition**:

```
(trạng thái, hành động, phần thưởng, trạng thái kế, cờ kết thúc)
```

Đây là bối cảnh thực tế nhất cho các lĩnh vực an toàn: không ai cho thuật toán
thử nghiệm trực tiếp trên bệnh nhân hay trên đường phố.

### 2.2 DQN và Q-value

**Q-value** `Q(trạng thái, hành động)` là ước lượng "nếu ở trạng thái này mà làm
hành động kia thì tổng phần thưởng tương lai kỳ vọng là bao nhiêu". Biết Q thì
chính sách chỉ là: chọn hành động có Q lớn nhất.

**DQN** (Deep Q-Network) dùng một mạng nơ-ron để xấp xỉ Q. Nó học bằng cách ép
Q thoả **phương trình Bellman**:

```
Q(s, a)  ≈  r  +  γ · max Q(s', a')
             ↑        ↑
        phần thưởng   giá trị tốt nhất ở trạng thái kế
```

`γ` (gamma) là **hệ số chiết khấu**, ở đây bằng 0,99 — phần thưởng tương lai
đáng giá hơi kém hơn phần thưởng ngay lập tức.

Vế phải gọi là **TD target** (temporal-difference target — mục tiêu sai khác
thời gian). Chênh lệch giữa hai vế là **TD error**, và huấn luyện chính là giảm
sai số đó.

### 2.3 Target network — và vì sao nó quan trọng bất thường ở đây

Nếu tính TD target bằng chính mạng đang học thì mục tiêu thay đổi mỗi bước, và
việc học dễ mất ổn định. Cách chuẩn: giữ một **bản sao đông lạnh** của mạng, gọi
là **target network**, chỉ **đồng bộ** lại sau mỗi *N* bước.

Trong dự án này *N* được gọi là `target_sync_interval`. Nó hoá ra là **tham số
quan trọng nhất** trong toàn bộ hệ, vì lý do sẽ nói ở mục 7.

### 2.4 Merkle tree — cam kết dữ liệu

**Merkle tree** là cách "niêm phong" một tập dữ liệu bằng **một chuỗi hash duy
nhất**, gọi là **root** (gốc).

Cách dựng: băm từng dòng dữ liệu thành một **leaf** (lá), rồi ghép đôi và băm
lên dần cho tới khi còn một giá trị.

```
                    root  ← công bố duy nhất giá trị này
                  /      \
              h(1,2)      h(3,4)
              /    \      /    \
            lá1   lá2   lá3   lá4
             |     |     |     |
           dòng1 dòng2 dòng3 dòng4
```

Hai tính chất khiến nó hữu dụng:

1. **Sửa bất kỳ dòng nào cũng làm đổi root.** Công bố root trước là tự trói mình
   vào đúng tập dữ liệu đó.
2. **Chứng minh một dòng thuộc tập chỉ cần `log₂(n)` hash**, không cần đưa cả
   tập. Với 100.000 dòng chỉ cần 17 hash — gọi là **Merkle path** hay
   **membership proof** (chứng minh thành viên).

Chi phí đo được trong dự án: **23.571 cycles cho mỗi tầng độ sâu**. Vì độ sâu
tăng theo logarit, nhân dữ liệu lên 10 lần chỉ thêm khoảng 3 tầng.

### 2.5 Fixed-point — vì sao không dùng số thực

Hệ chứng minh làm việc trên **số nguyên** trong một trường hữu hạn. Số thực dấu
phẩy động không biểu diễn được trực tiếp. Giải pháp chuẩn: **fixed-point** — nhân
mọi số thực với một hằng số rồi làm tròn thành số nguyên.

Ở đây `FP_SCALE = 1000`, nghĩa là:

```
0,99  →  990          (gọi là GAMMA_FP)
0,01  →  10
0,05  →  50
```

Nhân hai số fixed-point phải chia lại cho scale: `(a * b) // 1000`. Dùng chia
lấy nguyên (`//`), **không làm tròn** — vì Python và Rust phải cho kết quả giống
nhau đến từng bit.

Hệ quả quan trọng và không hiển nhiên: **learning rate mặc định của Adam là
3e-4, mã hoá thành `round(0,0003 × 1000) = 0`.** Tức là ở thang đo này Adam
không biểu diễn được ở tốc độ học mặc định của chính nó. Đó là một lý do độc lập
khiến dự án chỉ chứng minh SGD.

---

## 3. Các công cụ đã chọn, và vì sao

### 3.1 SP1 — zkVM

**zkVM** (zero-knowledge virtual machine) là một máy ảo mà **mọi lệnh nó chạy
đều sinh ra bằng chứng**. Bạn viết chương trình bằng Rust như bình thường,
biên dịch sang kiến trúc RISC-V, và zkVM cho ra một proof rằng chương trình đã
chạy đúng.

**Vì sao chọn zkVM thay vì viết mạch (circuit) thủ công?**

| | Mạch thủ công | zkVM |
| --- | --- | --- |
| Cách diễn đạt phép tính | mô tả từng phép cộng/nhân dưới dạng ràng buộc | viết Rust bình thường |
| Công sức | rất lớn, dễ sai | thấp |
| Tốc độ prove | nhanh hơn nhiều | chậm hơn |
| Kiểm tra được bằng mắt | khó | dễ, vì là mã nguồn thường |

Dự án này ưu tiên **tính kiểm chứng được của mã nguồn** hơn tốc độ, nên chọn
zkVM. Reviewer có thể đọc thẳng file Rust để biết quan hệ nào đang được chứng
minh, thay vì phải tin một mạch số học.

**SP1** là zkVM của Succinct Labs, pin ở phiên bản **6.1.0**. Ba khái niệm của
nó xuất hiện khắp repo:

- **guest** — chương trình chạy *bên trong* zkVM, thứ được chứng minh.
- **host** — chương trình chạy bên ngoài, nạp dữ liệu cho guest và gọi prover.
- **shared** — thư viện Rust dùng chung, chứa logic quan hệ để cả hai bên gọi.

Mỗi quan hệ có một workspace riêng theo đúng ba phần đó, tại
`zk_backend/<tên quan hệ>/sp1/`.

**cycles** là đơn vị đo khối lượng: số lệnh máy ảo đã chạy. Chi phí prove tỉ lệ
gần như tuyến tính với nó, nên cycles là đại lượng dự báo chi phí — và khác với
thời gian, nó **tất định**: cùng một guest và cùng đầu vào luôn cho cùng số
cycles, bất kể chạy trên máy nào.

### 3.2 STARK, Groth16, PLONK — ba loại proof

SP1 sinh **STARK** proof. Vài điểm cần biết để đọc bảng số liệu:

- **STARK** — proof lớn (khoảng 2,8 MB ở đây) nhưng kiểm rất nhanh (~0,05 s), và
  không cần "trusted setup" (nghi lễ khởi tạo mà nếu bị gian lận thì toàn hệ mất
  an toàn).
- **Groth16** — proof rất nhỏ (khoảng 13 KB), phù hợp khi cần đưa lên blockchain,
  nhưng cần trusted setup. Trong dự án, biến thể Groth16 tốn **gấp 20 lần
  cycles** nhưng witness nhỏ hơn **388 lần**.
- **PLONK** — chưa dùng; đo cho thấy cần khoảng 60 GB RAM.

### 3.3 Vì sao PyTorch **và** Rust — hai bản cài đặt cùng một phép tính

Repo cố ý có **hai bản** của cùng một logic:

1. **Python** (`zk_offline_dqn/relations/`) — gọi là **oracle** hay **reference
   implementation**. Chạy nhanh, dễ đọc, dùng để sinh dữ liệu và kiểm thử.
2. **Rust** (`zk_backend/*/sp1/shared/`) — chạy trong guest, là thứ thật sự được
   chứng minh.

Nghe như trùng lặp, nhưng nó là **cơ chế phòng thủ**: sai lệch giữa hai bản sẽ
lộ ra khi so kết quả, và bắt được trên CPU trong vài giây thay vì trên GPU sau
vài giờ. Trong dự án đã có test đọc thẳng mã nguồn Rust để bắt trôi lệch giữa
hai bên (`tests/unit/test_canonical_payload_alignment.py`).

Cái giá phải trả: mỗi lần đổi quan hệ phải sửa **cả hai** bản, và chuỗi JSON
chuẩn tắc phải khớp đến từng byte — vì guest không có bộ mã hoá JSON, nó dựng
chuỗi bằng tay với các khoá gõ sẵn theo thứ tự.

### 3.4 GPU và AWS — vì sao phải thuê máy

Prove là phép tính nặng. Đo trên máy đã dùng:

- **CPU**: `training_fragment_k8` mất **144,6 giây**.
- **GPU (NVIDIA A10G)**: cùng quan hệ mất **3,8 giây** — nhanh hơn khoảng 38 lần.

Ngoài ra, chế độ **recursion** (mục 5) **chỉ chạy được trên GPU**: bản CPU cần
hơn 61 GB RAM và không hoàn thành, còn GPU dùng 18,4 GB VRAM và chạy được.

Máy dùng là **AWS g5.2xlarge** (1 GPU A10G, 32 GB RAM), thuê theo giờ khoảng
**$1,2**. Vài quy tắc đã rút ra bằng cách trả giá:

- Dùng **on-demand**, không dùng **spot**. Một lượt spot 14 giờ từng bị AWS thu
  hồi, mất toàn bộ kết quả — tiết kiệm được $1,2 cho 3 giờ mà rủi ro mất tất cả.
- **Kết quả phải rời khỏi máy sau mỗi bước**, không đợi tới cuối. Đã từng mất
  toàn bộ log vì máy tự tắt trước khi kịp lấy.

---

## 4. Kiến trúc: bốn lớp

```
Lớp 1  Dữ liệu       thu thập → kiểm toán → cam kết Merkle → xác minh
                     (scripts/data/)
   ↓
Lớp 2  Quan hệ       oracle Python thuần, không đụng file, không CLI
                     (zk_offline_dqn/relations/)
   ↓
Lớp 3  Backend       guest/host/shared Rust, sinh proof SP1
                     (zk_backend/<quan hệ>/sp1/)
   ↓
Lớp 4  Gộp           nối nhiều proof thành một proof duy nhất
                     (training_aggregation)
```

Lý do tách lớp: mỗi lớp kiểm được độc lập, và mỗi phát biểu trong paper truy
ngược được về một artifact cụ thể. Ranh giới được ép bằng quy tắc — ví dụ
`relations/` **cấm** dùng argparse, đọc file, hay biến môi trường, để logic
không bị lẫn vào phần kịch bản.

### Từ vựng của repo

| Từ | Nghĩa |
| --- | --- |
| **relation** | một phát biểu toán học được chứng minh, ví dụ "TD target này tính đúng" |
| **witness** | dữ liệu riêng tư mà prover biết còn verifier không thấy |
| **public inputs** | phần công khai, verifier đọc được, proof ràng buộc vào nó |
| **test vector** | một trường hợp mẫu đã khoá, dùng làm chuẩn so sánh |
| **provenance** | hồ sơ ghi lại một lần prove: số đo, hash, báo cáo kiểm |
| **fragment** | một đoạn ngắn của quá trình huấn luyện, gồm *k* bước |
| **guest ELF** | file nhị phân của chương trình guest sau khi biên dịch |

---

## 5. Recursion — nối nhiều proof thành một

Một proof phủ được vài bước huấn luyện. Muốn phủ hàng nghìn bước thì làm sao?

**Cách ngây thơ:** đưa cả 5.000 bước vào một chương trình guest. Không khả thi:
bộ nhớ và cycles tăng tuyến tính, vượt xa giới hạn phần cứng.

**Cách dùng ở đây — recursion:** viết một chương trình guest mà **việc của nó là
kiểm các proof khác**. Vì kiểm proof cũng là một phép tính, nó lại sinh ra một
proof mới.

```
     proof gốc  ← kiểm hai proof con bên dưới
      /      \
  proof     proof     ← mỗi cái lại kiểm hai proof con
   /  \      /  \
 lá   lá    lá   lá   ← mỗi lá phủ 156 bước huấn luyện
```

Kết quả: **một** proof duy nhất phủ toàn bộ, và verifier chỉ kiểm đúng proof gốc
đó trong 0,054 giây.

Số đo quan trọng: **khoảng 154 triệu cycles cho mỗi proof con được kiểm**. Con số
này **không phụ thuộc** proof con phủ bao nhiêu bước huấn luyện. Nên chi phí ước
được trên giấy trước khi thuê máy: cây *N* lá cần *N−1* lượt kiểm.

Hệ quả thực dụng: **lá dài thì rẻ hơn lá ngắn**. Chuyển từ lá 8 bước sang lá 156
bước giảm số lượt kiểm đi khoảng 20 lần cho cùng độ dài huấn luyện.

Dự án dùng hai chế độ, và phân biệt chúng rất quan trọng khi đọc paper:

- **`proof_manifest_chain`** — chỉ băm *hồ sơ* của các proof con, **không kiểm
  chúng trong guest**. Rẻ, nhưng yếu hơn: phải tin rằng ai đó đã kiểm bên ngoài.
- **`recursive_sp1`** — **thật sự kiểm từng proof con bằng mật mã bên trong
  guest**. Đây mới là recursion đúng nghĩa. Chỉ chạy được trên GPU.

---

## 6. Ba nghĩa vụ mà học có giám sát không gặp

Đây là phần định vị đóng góp của dự án. Một khảo sát về zero-knowledge
proof-of-training phân loại toàn bộ lĩnh vực theo **lớp mô hình** — mạng sâu,
mạng tích chập, mạng hồi quy, cây quyết định, mô hình ngôn ngữ — và **không liệt
kê công trình nào về học tăng cường**.

Nhưng RL không chỉ là "thêm một lớp mô hình". Nó mang ba nghĩa vụ xác minh mà
các công trình học có giám sát không hề gặp:

### Nghĩa vụ 1 — nhãn do chính mô hình đang học sinh ra

Ở học có giám sát, nhãn là dữ liệu cố định; cam kết dataset là đã cam kết luôn
nhãn. Ở RL, TD target được **tính ra từ target network trong lúc huấn luyện**.
Nên proof phải chứng minh không chỉ "đã dùng nhãn này" mà còn "nhãn này được suy
ra đúng từ một checkpoint đã cam kết".

### Nghĩa vụ 2 — đồng bộ target là sự kiện rời rạc

Target được làm mới sau mỗi *N* bước. Một prover tự do dịch chuyển các thời điểm
đó sẽ làm đổi ý nghĩa của **mọi nhãn phía sau** — mà lượt chạy kết quả vẫn tự
nhất quán, không có gì mâu thuẫn để phát hiện.

### Nghĩa vụ 3 — lấy mẫu replay không có thứ tự chuẩn tắc

Chỉ số minibatch được **rút ngẫu nhiên**, không phải liệt kê tuần tự. Prover nào
chọn được cách rút thì chọn luôn dữ liệu mà phát biểu nói về.

**Nghĩa vụ thứ ba không phải lo xa — chính chúng tôi đã mắc.** Xem mục 8.

---

## 7. Kết quả hiện tại

### 7.1 Bảng 1 — hiệu năng học tăng cường

54 dòng: 6 tập dữ liệu × 4 thuật toán × 2 optimizer, cộng 6 dòng chạy đúng cấu
hình mà hệ chứng minh kiểm.

Sáu tập dữ liệu tự thu thập, mỗi tập 50.000 transition, ở ba mức chất lượng
(ngẫu nhiên / trung bình / chuyên gia) trên hai môi trường CartPole và
LunarLander.

**Kết quả trung tâm** — cấu hình chứng minh được so với cấu hình tinh chỉnh:

| Tập dữ liệu | cấu hình chứng minh được | tinh chỉnh (batch 256) |
| --- | --- | --- |
| cartpole-random | 17,0 | 311,0 |
| cartpole-medium | 11,0 | 9,8 |
| cartpole-expert | 9,7 | 9,6 |
| lunarlander-random | **−152,7** | −215,3 |
| lunarlander-medium | −829,7 | −366,6 |
| lunarlander-expert | −717,9 | −518,7 |

Trên `lunarlander-random`, cấu hình chứng minh được **vượt** cấu hình tinh chỉnh.

### 7.2 Bảng 2 — chi phí chứng minh

32 dòng, 25 dòng có proof thật, **cả 25 ghi rõ prover**. Toàn bộ sinh trong một
lượt chạy trên một máy, nên lần đầu tiên cột thời gian so sánh được với nhau.

| Quan hệ | Cycles | Prove | Verify |
| --- | ---: | ---: | ---: |
| groth16_recursive_t16 | 6.180.861.737 | 1.596,9 s | 68,0 s |
| native_flat_recursive_t64 | 1.683.525.837 | 755,2 s | 0,054 s |
| binary_tree_native_t1248 (CartPole) | 422.415.621 | 199,7 s | 0,054 s |
| training_fragment_k8 | 5.193.244 | 3,8 s | 0,129 s |
| merkle_membership (canonical) | 116.750 | 50,2 s | 0,123 s |

Dải cycles trải từ 117 nghìn tới 6,18 tỉ — gấp hơn 50.000 lần, mà verify vẫn
gần như không đổi. Đó là minh hoạ trực tiếp cho tính bất đối xứng ở mục 1.

### 7.3 Bảng 3 — kháng giả mạo

236 phép thử: sửa một trường trong artifact rồi kiểm xem hệ có phát hiện không.
**233 bị từ chối đúng như dự đoán, 3 không áp dụng.** Phủ 19 nhóm tấn công, từ
tầng dữ liệu (sửa phần thưởng, sửa hành động) tới tầng chứng minh (sửa public
input).

### 7.4 Lượt chạy trọn vẹn dưới một proof

| Môi trường | Bước | Cycles | Prove | Verify |
| --- | --- | ---: | ---: | ---: |
| CartPole | 0 → 1248 | 422.415.621 | 199,7 s | 0,054 s |
| LunarLander | 0 → 1248 | 422.396.109 | 198,1 s | 0,054 s |
| LunarLander (random) | **0 → 4992** | 422.386.830 | 188,8 s | 0,054 s |

Dòng cuối là kết quả mạnh nhất: nó phủ **đúng lượt chạy sinh ra con số −152,7
trong Bảng 1**, chứ không phải một lượt chạy minh hoạ nào khác. Nó chưa nằm
trong Bảng 2 vì lý do kỹ thuật ở mục 8.4.

---

## 8. Những lỗi đã tìm ra — và vì sao chúng đáng kể

Phần này quan trọng ngang phần kết quả. Cả bốn lỗi đều cùng một hình dạng: **hệ
thống báo xanh trong khi thứ nó kiểm không phải thứ ta tưởng**.

### 8.1 Mọi chunk lấy mẫu trùng nhau

`sampler_seed` là hằng số, và `step_id` đếm **trong nội bộ mỗi fragment**. Hệ
quả: mọi chunk của một chuỗi rút **đúng cùng một tập chỉ số**. Đo trực tiếp,
chunk 0 (bước 0–7) và chunk 1 (bước 8–15) đều cho:

```
[68, 83, 22, 125, 56, 55, 42, 1]
```

Nghĩa là "lượt chạy 1248 bước" thực chất là **156 lần lặp trên 8 dòng** của tập
50.000 dòng — không phải một lượt quét dữ liệu.

**Vì sao không lớp nào bắt được:** mọi hash đều khớp, mọi proof đều hợp lệ, và
cả 236 phép thử giả mạo đều xanh — vì **không trường nào bị sửa**. Đây là lỗi
*ngữ nghĩa* của quan hệ, loại mà benchmark tamper theo trường không phủ được.

**Cách sửa:** `sampler_seed = H(dataset_root, global_step_start)`. Một thay đổi
đóng hai lỗ cùng lúc — các chunk buộc phải rút khác nhau, và prover hết đường
tự chọn seed để lọc mẫu có lợi.

### 8.2 Guest tràn số nguyên trong im lặng

Phép nhân fixed-point `(a * b) / 1000` chạy trên `i64`. Khi offline DQN phân kỳ,
Q tăng theo hàm mũ và `990 × q` vượt `i64::MAX` ở khoảng 9,3e15 — kết quả **gói
vòng** thành số âm, và guest vẫn chứng minh nó bình thường.

Điểm nguy hiểm: một prover sinh nhân chứng bằng cùng ngữ nghĩa `i64` sẽ khiến
`assert_eq!` trong guest **qua được**, và proof hợp lệ trên phép tính vô nghĩa.
Lượt chạy của dự án chỉ phát hiện được vì Python dùng số nguyên độ chính xác tuỳ
ý nên **không** gói vòng, và hai bên lệch nhau — một cơ chế phát hiện tình cờ.

**Cách sửa:** bật `overflow-checks = true` để guest dừng hẳn khi tràn. Nhưng chỗ
đặt mới là phần bẫy: tài liệu bảo mật của SP1 bảo đặt trong `Cargo.toml` của
guest — đúng với template độc lập, nhưng ở repo này guest là **member của
workspace** nên Cargo **bỏ qua** kèm một cảnh báo dễ trôi qua mắt. Phải đặt ở
gốc workspace.

Chi phí đo được **không đồng đều**, đừng trích một con số cho cả bảng:

| Nhóm | Tăng cycles | Vì sao |
| --- | ---: | --- |
| fragment, update | +3,6…7,2% | số học fixed-point là phần nhỏ |
| merkle | +13,0…17,7% | nhiều phép cộng chỉ số |
| recursion | **+36,8%** | kiểm proof con nặng số học nhất |
| groth16 | +0,33% | cycles do BN254 chi phối |

### 8.3 Số trong paper chưa bao giờ nối với pipeline

Pipeline **có** sinh bảng LaTeX từ dữ liệu, nhưng paper **không** dùng chúng —
bảng trong paper gõ tay. Chúng đã trôi rất xa:

| Dòng | Paper ghi | Thực tế |
| --- | ---: | ---: |
| `training_fragment_k8` | 440,6 s | **3,8 s** |
| `td_mvp` | 167,7 s | 60,5 s |
| cartpole-random Double DQN | 192,9 | 311,0 |

Cổng kiểm claim vẫn xanh suốt, vì nó kiểm **câu chữ** chứ không kiểm **số**.

### 8.4 Hash guest ELF định danh lần build, không phải mã nguồn

Mỗi dòng trong Bảng 2 ghi `guest_elf_sha256` để chứng minh nó đến từ đúng phiên
bản guest nào. Nhưng cùng một mã nguồn build ở `~/repo8` và `~/repo11` cho **hai
hash khác nhau** — vì một đường dẫn tuyệt đối lọt vào file nhị phân.

Điều này lộ ra khi proof 4992 bước trở về với hash khác 10 dòng anh em, dù
**không một dòng mã guest nào thay đổi** giữa hai lần build. Cổng kiểm tra đã
chặn đúng.

**Trạng thái hiện tại:** đã thêm `--remap-path-prefix` qua API của `sp1_build`,
và đo được là đường dẫn repo **đã biến mất** khỏi ELF. Nhưng hai hash **vẫn
lệch**, và mọi chuỗi đường dẫn còn lại đều giống nhau — nên nguyên nhân còn lại
nhiều khả năng là chính cái cờ remap khác nhau giữa hai lượt build, và cargo băm
cờ vào metadata. **Giả thuyết này chưa được kiểm chứng.**

Hệ quả cần nhớ: cổng kiểm ELF vẫn đúng mục đích (bắt việc chỉ prove lại một
nửa, vì cùng một lượt thì cùng đường dẫn), nhưng **không được** dùng hash ELF
công bố làm mỏ neo tái lập cho reviewer build từ clone sạch.

---

## 9. Cấu hình chứng minh được — khoảng cách được đo, không phỏng đoán

Quan hệ SP1 kiểm một thủ tục **đơn giản hơn** thứ một cài đặt tinh chỉnh chạy:

| | Bảng 1 tinh chỉnh | Quan hệ chứng minh |
| --- | --- | --- |
| batch size | 256 | **1** |
| optimizer | Adam hoặc SGD | SGD thuần |
| cắt gradient | theo chuẩn L2 | theo từng thành phần |
| số học | float32 | fixed-point i64 |

Thay vì để người đọc tự đoán khoảng cách, dự án **đo nó** bằng một đối chứng đổi
từng thứ một, trên cartpole-random:

```
tinh chỉnh (batch 256, sync 100, clip chuẩn L2)   78,0
chỉ đổi sang clip theo thành phần                 75,4   ← phép thay chứng minh ép buộc
chỉ đổi sync 100 → 4                               9,4
chỉ đổi batch 256 → 1                              9,4
cả ba, cấu hình quan hệ                            9,4
```

Đọc bảng này: phép thay clipping — thứ **duy nhất** mà việc chứng minh bắt buộc,
vì chuẩn L2 cần căn bậc hai mà guest phải chứng minh — chỉ tốn 3,3%. Còn hai thứ
kia mỗi cái độc lập kéo về 9,4, tức mức của chính sách chưa học.

**Nhưng kết luận đó khái quát quá vội.** Đối chứng trên đo batch=1 tại *một*
giá trị sync duy nhất rồi kết luận cho mọi sync. Một đối chứng thứ hai quét 60
ô ở batch = 1 cho thấy batch=1 chết ở `sync=100`, nhưng **sống tốt ở
`sync=2000`** (lưới quét, 2 seed, nên là xu hướng chứ chưa phải số công bố):

| Môi trường | sync=4 | sync=2000 |
| --- | ---: | ---: |
| cartpole-random | 9,6 | 209,5 |
| lunarlander-random | −649,1 | −197,4 |

Xác nhận lại ở 3 seed trên cả sáu tập dữ liệu, đúng ngân sách 5000 bước của
Bảng 1, cho ra các con số đã công bố ở mục 7.1 — cải thiện ở **cả sáu**, và
`lunarlander-random` đạt **−152,7**, vượt cấu hình tinh chỉnh.

Bài học phương pháp: **"X độc lập gây chết" cần một lưới quét, không phải một
điểm đo.**

Và điều may mắn về mặt kỹ thuật: `target_sync_interval` vốn đã là public input
tự do — đổi nó **không tốn gì**. Thứ đắt (`batch_size`, bị ràng buộc cứng và
nhân cycles theo batch) hoá ra không phải nguyên nhân.

---

## 10. Còn lại gì

| Việc | Trạng thái |
| --- | --- |
| Đưa proof 4992 bước vào Bảng 2 | chờ giải quyết mục 8.4 |
| CartPole ở quy mô học được (50.000 bước) | ngoài ngân sách — ~68 giờ GPU, ~$82 |
| Chứng minh Adam | không khả thi ở `FP_SCALE=1000` |
| Batch size > 1 | cần sửa quan hệ, cycles nhân theo batch |

Về giới hạn cuối cùng: đây là ranh giới **đo được**, không phải chỗ né tránh. Lá
lớn hơn cũng không cứu được — lá 1000 bước tốn khoảng 3,9 tỉ cycles, vượt mức
lớn nhất từng prove thành công (1,68 tỉ) và đụng trần RAM máy chủ (~27 byte mỗi
cycle, tức khoảng 105 GB).

---

## 11. Đọc tiếp

| Tài liệu | Nội dung |
| --- | --- |
| `docs/architecture.md` | kiến trúc mã nguồn và luồng làm việc |
| `docs/claim_matrix.md` | từng phát biểu và bằng chứng chống lưng |
| `docs/backend_coverage.md` | quan hệ nào có backend SP1, quan hệ nào chưa |
| `docs/reproducibility.md` | cách chạy lại regression và sinh lại báo cáo |
| `docs/recursion_cycle_analysis.md` | phân tích chi phí recursion |
| `CLAUDE.md` | quy ước cho người và agent đóng góp vào repo |
