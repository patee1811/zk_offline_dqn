# Giải thích toàn cảnh dự án

Tài liệu này viết cho người **chưa biết gì** về cả hai lĩnh vực mà dự án đứng
giữa: học tăng cường và chứng minh không tiết lộ tri thức. Mục tiêu là sau khi
đọc hết, bạn giải thích được cho người khác — kể cả người hướng dẫn — rằng dự án
làm gì, mỗi con số trong paper nghĩa là gì, và vì sao từng lựa chọn kỹ thuật lại
là lựa chọn đó chứ không phải cái khác.

## Cách đọc file này

Tài liệu chia làm bốn khối:

| Khối | Mục | Dành cho |
| --- | --- | --- |
| **A. Bối cảnh** | 1 | vì sao bài toán tồn tại |
| **B. Nền tảng** | 2–4 | học tăng cường, mật mã, zkVM — từ con số không |
| **C. Dự án** | 5–8 | kiến trúc, dữ liệu, kết quả, lỗi đã tìm ra |
| **D. Trình bày** | 9–12 | bản đồ paper, câu hỏi phản biện, chỗ tra số |

Nếu chỉ có 30 phút trước buổi gặp thầy: đọc mục 1, mục 5.2, mục 7.2–7.3, mục 8,
rồi mục 9 và 10. Mục 10 là mười câu hỏi phản biện kèm câu trả lời sẵn.

**Quy ước về nguồn của mọi con số.** Tài liệu đánh dấu rõ ba loại phát biểu, vì
trộn chúng vào nhau là cách nhanh nhất để mất uy tín trước phản biện:

| Nhãn | Nghĩa |
| --- | --- |
| **[đo]** | số đo thật trong repo, truy được về một file artifact cụ thể |
| **[nền]** | kiến thức nền chung của lĩnh vực, không phải kết quả của dự án |
| **[chưa kiểm]** | giả thuyết, chưa có phép đo chống lưng — nói rõ để không ai trích nhầm |

Chỗ nào chưa đo thì ghi là chưa đo. Không có con số nào ở đây là mục tiêu hay
ước lượng đẹp.

---

# KHỐI A — BỐI CẢNH

## 1. Bài toán: vì sao cần chứng minh việc huấn luyện

### 1.1 Tình huống, kể chậm lại

Câu trong paper là *"một công ty nộp cho cơ quan quản lý một chính sách điều
khiển đã huấn luyện"*. Câu đó nén ba khái niệm, tách ra như sau.

**"Chính sách" (policy) là gì?**

Chính sách là **quy tắc quyết định**: một hàm nhận vào tình huống hiện tại và
trả ra hành động nên làm.

```
chính sách:  tình huống  →  hành động
```

Ví dụ cụ thể để bám vào suốt tài liệu:

| Lĩnh vực | Tình huống (state) | Hành động (action) |
| --- | --- | --- |
| Xe tự lái | tốc độ, khoảng cách xe trước, góc vô lăng | ga / phanh / đánh lái |
| Kê thuốc | chỉ số xét nghiệm, tuổi, tiền sử của bệnh nhân | liều thuốc tuần tới |
| Điều hoà toà nhà | nhiệt độ trong/ngoài, số người, giá điện | tăng/giảm/giữ công suất |
| CartPole (dùng trong dự án) | vị trí xe, vận tốc xe, góc gậy, vận tốc góc | đẩy trái / đẩy phải |

Trong thực tế, "chính sách" ở đây là **một tệp trọng số mạng nơ-ron** — vài
nghìn tới vài triệu con số. Nộp chính sách nghĩa là nộp tệp đó. Nhìn vào tệp
trọng số, **không ai đọc ra được nó được huấn luyện thế nào**, y như nhìn vào
một pho tượng không đọc ra được người thợ đã đục thế nào.

Đây chính là chỗ sinh ra vấn đề.

**"Cơ quan quản lý" muốn gì?**

Không phải muốn biết chính sách *tốt* hay không — cái đó đo được bằng cách chạy
thử. Cơ quan quản lý muốn biết **quá trình tạo ra nó có sạch không**:

- Có đúng là huấn luyện trên tập dữ liệu đã đăng ký không, hay đã âm thầm thêm
  dữ liệu khác vào?
- Có ai sửa dữ liệu cho đẹp không?
- Có đúng thuật toán và siêu tham số đã khai báo không?

Vì sao "chạy thử là đủ" lại sai: một chính sách có thể đạt điểm cao trên bộ thử
nghiệm mà vẫn được huấn luyện bằng dữ liệu bịa. Nó cũng có thể được huấn luyện
trên dữ liệu bệnh nhân không được phép dùng. Điểm thi không nói gì về nguồn gốc.

### 1.2 Bốn cách gian lận cụ thể

Giả sử một bên không trung thực. Họ có thể:

1. **Sửa phần thưởng.** Trong dữ liệu, mỗi dòng ghi kết quả của một hành động là
   tốt hay xấu (con số này gọi là *reward*). Nâng phần thưởng ở những dòng có
   lợi thì mô hình học ra một thế giới đẹp hơn thế giới thật.
2. **Đổi cờ kết thúc.** Mỗi dòng có một cờ báo "sau hành động này thì tình huống
   kết thúc" (xe đâm, gậy đổ, tàu rơi). Xoá cờ ở các lần thất bại thì thất bại
   biến mất khỏi dữ liệu.
3. **Thay giá trị mục tiêu.** Trong lúc học, thuật toán tự tính ra một con số
   mục tiêu cho mỗi bước (mục 2.8). Sửa con số này thì sai số trông nhỏ đi.
4. **Sửa gradient.** Gradient là hướng cập nhật trọng số. Sửa nó nghĩa là can
   thiệp thẳng vào mô hình rồi vẫn khai là "học ra tự nhiên".

Điểm chung của cả bốn: **kết quả cuối cùng vẫn tự nhất quán**. Không có mâu
thuẫn nội tại nào để một người kiểm tra bên ngoài phát hiện ra.

### 1.3 Mâu thuẫn ở giữa

Có hai cách kiểm tra hiển nhiên, và cả hai đều hỏng:

| Cách | Vì sao hỏng |
| --- | --- |
| Chỉ nộp mô hình cuối | không kiểm được gì cả — đó là pho tượng không có nhật ký |
| Nộp cả dữ liệu + toàn bộ nhật ký huấn luyện | lộ dữ liệu: bí mật kinh doanh, dữ liệu bệnh nhân, và bên kiểm phải chạy lại toàn bộ, tốn đúng bằng chi phí huấn luyện |

Cần một thứ ở giữa: **kiểm được mà không phải xem**.

### 1.4 Zero-knowledge proof

**Zero-knowledge proof** (ZKP, chứng minh không tiết lộ tri thức) là kỹ thuật mật
mã cho phép: **[nền]**

> Bên A chứng minh cho bên B rằng *"tôi đã thực hiện đúng phép tính này trên dữ
> liệu thoả điều kiện kia"*, mà **không cần cho B xem dữ liệu**.

Ba tính chất định nghĩa nó:

| Tính chất | Nghĩa |
| --- | --- |
| **Completeness** (đầy đủ) | nếu A trung thực thì bằng chứng luôn được chấp nhận |
| **Soundness** (đúng đắn) | nếu A gian lận thì bằng chứng bị từ chối, trừ một xác suất nhỏ tới mức bỏ qua được (cỡ 2⁻¹⁰⁰) |
| **Zero-knowledge** (không tiết lộ) | bằng chứng không rò rỉ gì về dữ liệu riêng ngoài chính phát biểu được chứng minh |

Một ví von hay dùng: bạn chứng minh mình biết đường đi trong mê cung bằng cách
bước ra đúng cửa đối diện, mà không phải vẽ lại lộ trình.

Hai vai trò cần nhớ suốt tài liệu:

| Vai | Tên | Chi phí |
| --- | --- | --- |
| Bên tính toán và tạo bằng chứng | **prover** | rất đắt |
| Bên kiểm bằng chứng | **verifier** | rất rẻ |

Sự **bất đối xứng** đó là toàn bộ giá trị của kỹ thuật: dồn chi phí về phía kẻ
phải chứng minh sự trong sạch của mình, người kiểm gần như không tốn gì.

Số đo trong dự án minh hoạ thẳng điều đó **[đo]**:

| | Prove | Verify | Tỉ lệ |
| --- | ---: | ---: | ---: |
| Proof đắt nhất (Groth16 child, T=16) | 1.596,9 s | 68,0 s | 23× |
| Proof recursion nặng nhất (T=64) | 755,2 s | **0,054 s** | **14.000×** |
| Proof rẻ nhất (Merkle canonical) | 50,2 s | 0,123 s | 408× |

Dòng giữa là điều đáng nhớ: 1,68 **tỉ** cycles tính toán, kiểm xong trong **54
mili giây**.

### 1.5 Vì sao chưa ai làm cho học tăng cường

Đã có khá nhiều công trình chứng minh việc huấn luyện cho **học có giám sát**
(supervised learning) — nhận diện ảnh, hồi quy, cây quyết định. Một khảo sát về
ZKML mà dự án trích dẫn tự mô tả phạm vi của mình là *"we primarily focus on
supervised learning"* và liệt kê hồi quy, SVM, K-means, cây quyết định, mạng
nơ-ron sâu — **không có mục nào về học tăng cường**. **[nền]**

Học tăng cường không phải "thêm một loại mô hình nữa". Nó mang **ba nghĩa vụ xác
minh** mà học có giám sát không hề gặp. Ba nghĩa vụ đó là đóng góp chính của dự
án, và được giải thích ở mục 5.4 — sau khi bạn đã có đủ từ vựng.

---

# KHỐI B — NỀN TẢNG

Khối này dài. Nó phải dài, vì mọi con số ở khối C chỉ có nghĩa khi bạn đã có từ
vựng ở đây. Đọc theo thứ tự; mỗi mục dùng lại mục trước.

## 2. Học tăng cường, từ con số không

### 2.1 Vòng lặp cơ bản

Học tăng cường (reinforcement learning, RL) mô tả mọi bài toán ra quyết định
tuần tự bằng đúng một vòng lặp: **[nền]**

```
        ┌──────────────────────────────┐
        │                              │
        ▼                              │
   ┌─────────┐   hành động a     ┌──────────────┐
   │  AGENT  │ ────────────────▶ │ MÔI TRƯỜNG   │
   │(tác nhân)│                   │(environment) │
   └─────────┘ ◀──────────────── └──────────────┘
        ▲     trạng thái mới s'
        │     phần thưởng r
        └── lặp lại cho tới khi kết thúc
```

Năm danh từ, và tôi sẽ dùng chúng suốt tài liệu:

| Ký hiệu | Tên | Nghĩa | Ví dụ CartPole |
| --- | --- | --- | --- |
| `s` | **state** (trạng thái) | mô tả tình huống hiện tại bằng số | `[vị trí xe, vận tốc xe, góc gậy, vận tốc góc]` — 4 số thực |
| `a` | **action** (hành động) | việc agent chọn làm | `0` = đẩy xe sang trái, `1` = đẩy sang phải |
| `r` | **reward** (phần thưởng) | điểm số môi trường trả về ngay sau hành động | `+1` cho mỗi bước gậy chưa đổ |
| `s'` | **next state** | trạng thái sau khi hành động | 4 số mới |
| `done` | **cờ kết thúc** | tình huống đã chấm dứt chưa | `True` khi gậy nghiêng quá 12° hoặc xe ra khỏi màn hình |

**CartPole** là bài toán chuẩn dùng để so sánh thuật toán: một cây gậy dựng
đứng trên một cái xe trượt ngang, agent phải đẩy xe qua lại để giữ gậy không đổ.
Càng giữ lâu, điểm càng cao. Điểm tối đa trong phiên bản dự án dùng
(`CartPole-v1`) là **500** — giữ được 500 bước thì tự dừng. **[nền]**

**LunarLander** là bài toán thứ hai: hạ cánh một tàu vũ trụ xuống bãi đáp. State
có 8 số (vị trí, vận tốc, góc, hai chân đã chạm đất chưa), 4 hành động (không
làm gì, bắn động cơ trái / phải / chính). Phần thưởng dương khi tiến gần bãi và
hạ cánh êm, **âm nặng khi rơi**. Điểm không có trần cứng như CartPole; hạ cánh
tốt vào khoảng **+200 tới +300**, rơi thì có thể **−300 hoặc thấp hơn**. **[nền]**

### 2.2 Transition là gì — và vì sao dữ liệu RL khác dữ liệu thường

Một **transition** là **một dòng dữ liệu**, ghi lại đúng một lượt của vòng lặp
trên:

```
transition = (s, a, r, s', done)
```

Ví dụ một dòng thật, đã làm tròn cho dễ đọc:

```
s     = [ 0.03, -0.19,  0.02,  0.31]   ← xe hơi lệch trái, gậy nghiêng nhẹ phải
a     = 1                              ← đẩy sang phải
r     = 1.0                            ← còn sống thêm một bước
s'    = [ 0.02, -0.39,  0.03,  0.61]   ← gậy nghiêng thêm
done  = False                          ← chưa đổ
```

**Vì sao đây không phải dữ liệu học có giám sát.** Trong học có giám sát bạn có
cặp `(đầu vào, nhãn đúng)` — ảnh con mèo kèm chữ "mèo". Nhãn là **sự thật cố
định**, do người gán.

Trong RL **không có nhãn**. Không ai biết ở trạng thái `s` thì hành động nào là
đúng. Thứ duy nhất bạn có là `r = 1.0` — "bước này được 1 điểm" — và điểm đó
không nói hành động vừa rồi khôn hay dại, vì hậu quả có thể tới sau hai chục
bước. Đây gọi là bài toán **gán công (credit assignment)**. **[nền]**

Toàn bộ phần còn lại của mục 2 là cách RL xoay quanh việc không có nhãn.

### 2.3 Episode và return

Một **episode** (lượt chơi) là chuỗi transition từ lúc bắt đầu tới lúc `done`.
CartPole: từ lúc thả gậy tới lúc gậy đổ. Một episode có thể dài 9 bước (chính
sách dở) hoặc 500 bước (chính sách giỏi).

**Return** là tổng phần thưởng của cả một episode. Đây chính là con số ở cột
"Avg Return" của Bảng 1. CartPole return = số bước sống sót, nên đọc thẳng ra
được: **9,3 nghĩa là gậy đổ sau 9 bước; 311 nghĩa là gần chạm trần 500.**

### 2.4 Chiết khấu γ — vì sao thưởng tương lai đáng giá kém hơn

Đây là câu hỏi bạn nêu, và nó có **ba** lý do độc lập, không phải một.

Ta muốn định nghĩa "giá trị" của một tình huống là tổng thưởng tương lai. Nhưng
tổng thẳng thì gặp vấn đề:

```
G = r₀ + r₁ + r₂ + r₃ + ...        ← có thể là tổng vô hạn
```

Thay vào đó, RL dùng **tổng có chiết khấu**:

```
G = r₀ + γ·r₁ + γ²·r₂ + γ³·r₃ + ...      với 0 ≤ γ < 1
```

Với γ = 0,99 (giá trị dự án dùng):

| Phần thưởng ở bước | Hệ số | Còn lại bao nhiêu |
| --- | --- | --- |
| 0 (ngay bây giờ) | γ⁰ = 1 | 100% |
| 10 | γ¹⁰ = 0,904 | 90% |
| 100 | γ¹⁰⁰ = 0,366 | 37% |
| 500 | γ⁵⁰⁰ = 0,0066 | 0,7% |

**Ba lý do:**

**(1) Toán học — để tổng hội tụ.** Nếu môi trường không bao giờ kết thúc và mỗi
bước được +1, thì `1 + 1 + 1 + ...` là vô hạn, và **mọi** chính sách đều có giá
trị vô hạn — không so sánh được cái nào hơn. Với γ < 1 thì tổng bị chặn:

```
1 + γ + γ² + ... = 1/(1−γ) = 1/0,01 = 100
```

Con số **100** này sẽ quay lại nhiều lần trong tài liệu: nó là **giá trị tối đa
mà Q có thể đạt** nếu mỗi bước được +1 và trò chơi kéo dài vô hạn. Nhớ nó, vì
mục 8.2 sẽ cho bạn thấy Q trong dự án từng leo tới **4,14 × 10¹⁶** — lớn hơn
mức đúng khoảng **10¹⁴ lần**. Đó là dấu hiệu hỏng, và con số 100 là thước đo.

**(2) Kinh tế — tiền hôm nay hơn tiền năm sau.** γ đóng vai lãi suất. Một phần
thưởng hứa hẹn ở xa thì kém chắc chắn hơn phần thưởng cầm trong tay.

**(3) Thực dụng — giảm phương sai.** Tương lai xa phụ thuộc vào rất nhiều lựa
chọn chưa xảy ra, nên ước lượng nó rất nhiễu. Chiết khấu làm những đóng góp
nhiễu nhất teo lại, giúp việc học ổn định hơn.

Trong dự án, γ = 0,99 và được mã hoá thành số nguyên `GAMMA_FP = 990` (mục 3.5).
Giá trị 0,99 là mặc định phổ biến cho các bài toán dài vài trăm bước. **[nền]**

### 2.5 Chính sách, và vì sao cần Q

Ta muốn tìm chính sách tốt nhất. Cách trực tiếp — thử mọi chính sách rồi chọn
cái điểm cao nhất — bất khả thi: không gian chính sách là mọi bộ trọng số mạng
nơ-ron.

Cách gián tiếp: học một **hàm giá trị**, rồi suy ra chính sách từ nó.

### 2.6 Q(s, a) — hàm giá trị hành động

**Định nghĩa:**

> `Q(s, a)` = tổng phần thưởng có chiết khấu mà ta kỳ vọng nhận được **nếu** đang
> ở trạng thái `s`, **làm** hành động `a`, rồi từ đó về sau chơi tối ưu.

Chữ Q là **Quality** — chất lượng của cặp (tình huống, hành động). **[nền]**

Ví dụ với CartPole, giả sử ta đã biết Q hoàn hảo:

```
s = gậy đang nghiêng sang phải
      Q(s, đẩy phải)  = 87,3     ← đẩy xe sang phải để đỡ gậy → sống lâu
      Q(s, đẩy trái)  = 12,1     ← đẩy ngược → gậy đổ nhanh
```

**Biết Q thì có chính sách ngay lập tức**, không cần học gì thêm:

```
chính sách(s) = argmax over a of  Q(s, a)
```

nghĩa là: liệt kê mọi hành động, tính Q cho từng cái, chọn cái lớn nhất. Ở ví dụ
trên: chọn "đẩy phải" vì 87,3 > 12,1.

Đây là lý do toàn bộ dự án xoay quanh Q chứ không xoay quanh chính sách trực
tiếp. **Q là thứ được học; chính sách chỉ là hệ quả.**

### 2.7 Phương trình Bellman — phân biệt Q(s,a) và max Q(s',a')

Đây là chỗ bạn nói chưa rõ, nên tôi tách thật chậm.

**Vấn đề:** định nghĩa của Q ở trên nhắc tới "tổng phần thưởng tương lai", mà
tương lai thì chưa xảy ra. Làm sao tính được?

**Ý tưởng của Bellman:** tách tổng vô hạn thành **hai phần — bước ngay bây giờ,
và tất cả phần còn lại**.

```
Q(s,a) =  r  +  γ · (giá trị của toàn bộ tương lai từ s')
          ↑        ↑
      thưởng     phần còn lại, đã chiết khấu
      tức thì
```

Mà "giá trị của toàn bộ tương lai từ `s'`, nếu chơi tối ưu" — theo đúng định
nghĩa của Q — chính là `max Q(s', a')`: giá trị của hành động **tốt nhất có
thể** tại `s'`.

Ghép lại, ta có **phương trình Bellman tối ưu**: **[nền]**

```
Q(s, a)  =  r  +  γ · max Q(s', a')
                        a'
```

**Bảng phân biệt hai vế — đây là chỗ hay nhầm nhất:**

| | `Q(s, a)` | `max Q(s', a')` |
| --- | --- | --- |
| Trạng thái nào? | `s` — trạng thái **hiện tại** | `s'` — trạng thái **kế tiếp** |
| Hành động nào? | `a` — hành động **đã thực sự làm**, ghi trong dữ liệu | `a'` — hành động **tốt nhất giả định**, ta tự chọn |
| Có max không? | **Không.** Một giá trị duy nhất, ứng với đúng `a` | **Có.** Duyệt mọi hành động khả dĩ tại `s'`, lấy giá trị lớn nhất |
| Vai trò | thứ ta **đang ước lượng** | một phần của **mục tiêu** để so |
| Ví dụ CartPole | `Q(s, "đẩy trái")` = 41,2 vì trong dữ liệu agent đã đẩy trái | tại `s'`: `Q=52,8` (trái), `Q=61,4` (phải) → max = **61,4** |

Ba câu để nhớ:

1. Vế trái **không có max** vì hành động đã xảy ra rồi, không chọn lại được.
2. Vế phải **có max** vì bước kế chưa xảy ra, và định nghĩa của Q giả định từ đó
   trở đi ta chơi tối ưu.
3. Cả hai vế đều gọi **cùng một hàm Q** — đó chính là điều làm phương trình này
   vừa mạnh vừa nguy hiểm (mục 2.11).

**Ví dụ số đầy đủ**, γ = 0,99:

```
Dữ liệu ghi:  s, a = "đẩy trái", r = 1.0, s', done = False

Mạng hiện tại nói:
    Q(s,  "đẩy trái")  = 41,2      ← vế trái
    Q(s', "đẩy trái")  = 52,8   ┐
    Q(s', "đẩy phải")  = 61,4   ┘  → max = 61,4

Vế phải  =  1,0 + 0,99 × 61,4  =  1,0 + 60,79  =  61,79
```

Hai vế lệch nhau: 41,2 so với 61,79.

### 2.8 TD target và TD error — chính xác là gì

Vế phải của phương trình Bellman có tên riêng:

> **TD target** = `r + γ · max Q(s', a')`, và nếu `done = True` thì TD target
> = `r` (không có tương lai để cộng vào).

TD là viết tắt của **temporal difference** — "sai khác theo thời gian", vì nó so
ước lượng ở thời điểm `t` với ước lượng ở thời điểm `t+1`. **[nền]**

> **TD error** = `TD target − Q(s, a)`

Với ví dụ trên:

```
TD target = 61,79
Q(s, a)   = 41,2
TD error  = 61,79 − 41,2 = 20,59      ← mạng đang đánh giá thấp 20,59
```

**Toàn bộ việc huấn luyện chỉ là: đẩy `Q(s,a)` lại gần TD target.** Lặp đi lặp
lại trên hàng chục nghìn transition, Q dần thoả phương trình Bellman.

**Vì sao gọi TD target là "nhãn":** trong học có giám sát nhãn do người gán. Ở
đây, TD target đóng đúng vai nhãn — nó là con số mà ta ép đầu ra khớp vào. Khác
biệt sống còn: **nhãn này do chính mạng đang học tự sinh ra.** Đây là nghĩa vụ
xác minh số 1 ở mục 5.4, và là lý do dự án tồn tại.

**Xử lý `done`.** Nếu bước này kết thúc episode thì không có `s'` có ý nghĩa, nên
TD target = `r` thôi. Đây là lý do việc **lật cờ `done`** (cách gian lận số 2 ở
mục 1.2) làm hỏng mọi thứ: nó thêm hoặc bớt cả một cục `γ · max Q(s', a')` khỏi
nhãn.

### 2.9 Hàm mất mát — SmoothL1

Ta có TD error. Biến nó thành một con số để tối ưu bằng **hàm mất mát** (loss).

Cách hiển nhiên là bình phương: `loss = (TD error)²`. Nhưng nếu TD error lớn —
mà trong RL thì rất hay lớn — bình phương làm nó bùng nổ, và một transition
nhiễu duy nhất kéo lệch cả mô hình.

**SmoothL1** (còn gọi là **Huber loss**) là dung hoà: bình phương khi sai số
nhỏ, tuyến tính khi sai số lớn. **[nền]**

```
                    ⎧  0,5 · e²          nếu |e| ≤ β
SmoothL1(e)  =      ⎨
                    ⎩  β·(|e| − 0,5·β)   nếu |e| > β
```

Dự án dùng β = 1,0 (`SMOOTH_L1_BETA_FP = 1000` ở thang fixed-point), khớp đúng
mặc định của `torch.nn.SmoothL1Loss()`. **[đo]** — điều này quan trọng vì bản
Python phải cho ra cùng kết quả với bản Rust đến từng bit (mục 5.3).

### 2.10 DQN — mạng nơ-ron thay cho bảng

Với CartPole, state là 4 **số thực**. Số trạng thái khả dĩ là vô hạn — không thể
lập bảng Q cho từng trạng thái.

**DQN (Deep Q-Network)** thay bảng bằng **mạng nơ-ron**: **[nền]**

```
   [4 số state]  →  lớp ẩn 64 nơ-ron  →  [2 số: Q(s,trái), Q(s,phải)]
```

Đây chính là ký hiệu `[4, 64, 2]` ở cột Network của Bảng 2 **[đo]**: 4 đầu vào,
64 nơ-ron ẩn, 2 đầu ra. LunarLander là `[8, 64, 4]` — 8 số state, 4 hành động.

Chú ý mạng trả ra **tất cả** Q của mọi hành động trong một lần chạy. Nhờ vậy
`max Q(s', a')` chỉ tốn một lần chạy mạng rồi lấy max của 2 (hoặc 4) số.

Vòng huấn luyện DQN, một bước:

```
1. lấy một transition (s, a, r, s', done) từ dữ liệu
2. chạy mạng trên s   → lấy Q(s, a)                    [dự đoán]
3. chạy mạng trên s'  → lấy max Q(s', a')              [cho nhãn]
4. TD target = r + γ · max Q(s', a')   (hoặc = r nếu done)
5. loss = SmoothL1(TD target − Q(s,a))
6. tính gradient của loss theo trọng số
7. cập nhật trọng số ngược hướng gradient
```

Bảy dòng này là **toàn bộ thứ mà dự án đi chứng minh**. Mỗi quan hệ SP1 ở mục
5.2 phủ một hoặc vài dòng trong đó.

### 2.11 Target network và "sync" — sync nghĩa là gì

Nhìn lại bước 2 và 3 ở trên: **cùng một mạng** vừa cho dự đoán vừa cho nhãn.

Đó là con rắn cắn đuôi. Ta cập nhật mạng để `Q(s,a)` gần nhãn hơn — nhưng cập
nhật đó cũng làm đổi luôn `Q(s', a')`, tức là **đổi luôn nhãn**. Mục tiêu chạy
trốn khỏi mũi tên đang đuổi theo nó. Việc học dao động hoặc phân kỳ.

**Cách chữa chuẩn của DQN:** giữ **hai** mạng. **[nền]**

| Mạng | Tên | Vai trò | Cập nhật khi nào |
| --- | --- | --- | --- |
| Mạng chính | **online network** | cho `Q(s, a)` ở bước 2 | **mỗi** bước |
| Bản sao đông lạnh | **target network** | cho `max Q(s', a')` ở bước 3 | chỉ sau mỗi *N* bước |

**"Sync" (đồng bộ) chính xác là gì:** cứ mỗi *N* bước, **sao chép toàn bộ trọng
số từ mạng online sang mạng target**. Không phải trung bình, không phải học — là
gán đè, một phép copy.

```
bước 0    : target ← copy(online)      ← sync
bước 1..N−1: target đứng yên; online học tiếp
bước N    : target ← copy(online)      ← sync
bước N+1..: lại đứng yên
```

Con số *N* gọi là **`target_sync_interval`** (chu kỳ đồng bộ target). Giữa hai
lần sync, nhãn **cố định** — đó chính là thứ làm việc học ổn định.

**Đánh đổi:**

- *N* nhỏ (ví dụ 4): nhãn gần đúng hơn với mạng hiện tại, nhưng gần như quay lại
  bài toán con rắn cắn đuôi → mất ổn định.
- *N* lớn (ví dụ 2000): rất ổn định, nhưng nhãn cũ, học chậm.

Trong dự án này `target_sync_interval` hoá ra là **tham số quan trọng nhất của
toàn hệ**, quan trọng hơn cả learning rate hay batch size. Mục 7.4 kể vì sao,
kèm số đo: đổi từ 4 sang 2000 kéo `lunarlander-random` từ **−649,1** lên
**−197,4** trong lưới quét, và cấu hình cuối đạt **−152,7**. **[đo]**

### 2.12 Double DQN

Phương trình Bellman dùng `max`, và max của các ước lượng nhiễu thì **thiên lệch
lên trên**: nếu 4 hành động đều có giá trị thật là 50 nhưng ước lượng nhiễu
±10, thì max của chúng trung bình lớn hơn 50. Sai lệch này tích luỹ qua từng
bước và thổi phồng Q. **[nền]**

**Double DQN** tách phép max thành hai việc do hai mạng khác nhau làm: **[nền]**

```
DQN thường:   target = r + γ · max Q_target(s', a')
                                 a'
              → mạng target vừa CHỌN hành động vừa CHẤM ĐIỂM nó

Double DQN:   a*     = argmax Q_online(s', a')     ← mạng online CHỌN
                        a'
              target = r + γ · Q_target(s', a*)    ← mạng target CHẤM ĐIỂM
```

Ai chọn thì không chấm. Điều này cắt phần lớn thiên lệch lên.

Dự án chứng minh **Double DQN**, không phải DQN thường (`PROVED_ALGORITHM =
"double_dqn"` **[đo]**). Đó là lý do quan hệ phải mang **hai** checkpoint mạng
trong public input chứ không phải một — và cũng là lý do có một loại giả mạo
riêng trong Bảng 3 tên `tamper_..._next_action_online`: sửa hành động mà mạng
online chọn.

### 2.13 Offline RL và replay dataset — vì sao phải dùng

**Online RL** là vòng lặp ở mục 2.1: agent hành động, môi trường phản hồi, agent
học, lặp lại. Agent **tự sinh ra dữ liệu của chính nó**.

**Offline RL** cấm điều đó. Agent **không được tương tác** với môi trường trong
lúc học. Nó chỉ có một tập dữ liệu cố định, đã ghi sẵn từ trước — gọi là
**replay dataset** (hoặc replay buffer khi nằm trong bộ nhớ).

**Vì sao phải dùng replay dataset?** Ba lý do, xếp theo mức quan trọng với dự án:

**(1) An toàn — và đây là lý do gắn với bài toán ở mục 1.** Không ai cho một
thuật toán đang học thử nghiệm trực tiếp trên bệnh nhân, trên đường phố, hay
trên lưới điện. Trong y tế, "thử một liều thuốc để xem có tốt không" là điều
không thể chấp nhận. Nên mọi ứng dụng RL trong lĩnh vực có quản lý **buộc phải**
là offline: học từ hồ sơ đã có. Đúng lĩnh vực mà cơ quan quản lý sẽ hỏi "anh
huấn luyện trên dữ liệu nào?".

**(2) Kiểm chứng được — lý do kỹ thuật riêng của dự án.** Đây là điểm mấu chốt
và đáng nói trước thầy:

> Dữ liệu offline là **cố định**, nên **cam kết được** (mục 3.2). Dữ liệu online
> do chính agent sinh ra trong lúc chạy, nên **không có gì để cam kết trước** —
> muốn chứng minh online RL thì phải chứng minh luôn cả bản thân môi trường mô
> phỏng, một bài toán khác hẳn và lớn hơn nhiều.

Nói cách khác: **offline RL là thứ duy nhất trong RL mà proof-of-training có
nghĩa với công nghệ hiện tại.** Đó không phải sự tiện lợi, đó là điều kiện cần.

**(3) Kinh tế.** Tương tác với môi trường thật đắt. Dữ liệu đã thu thập thì dùng
lại được nhiều lần.

**Cái giá của offline RL:** agent chỉ thấy những gì trong dữ liệu. Nếu dữ liệu
toàn hành động dở, agent khó học được hành động giỏi. Và tệ hơn — nó có thể
tưởng tượng ra giá trị cao cho những hành động **không hề có trong dữ liệu**, vì
không có gì bác bỏ. Hiện tượng này gọi là **extrapolation error**, và nó là lý
do thuật toán `cql_lite` xuất hiện trong Bảng 1: CQL (Conservative Q-Learning)
thêm một phạt để ghìm Q của các hành động ngoài dữ liệu xuống. **[nền]**

### 2.14 Minibatch và lấy mẫu

Cập nhật trọng số theo từng transition một thì rất nhiễu. Cách thông thường:
lấy **một nhóm** transition cùng lúc, tính loss trung bình, rồi cập nhật một
lần. Nhóm đó gọi là **minibatch**, và số phần tử là **batch size**.

Các chỉ số của minibatch được **rút ngẫu nhiên** từ dataset. Đây là chi tiết
tưởng nhỏ nhưng sinh ra nghĩa vụ xác minh số 3 (mục 5.4) và lỗi nghiêm trọng
nhất dự án từng tìm ra (mục 8.1).

Dự án chứng minh ở **batch size = 1** (`PROVED_BATCH_SIZE = 1` **[đo]**), trong
khi cấu hình tinh chỉnh của Bảng 1 dùng 256. Khoảng cách đó được **đo** chứ
không phỏng đoán — mục 7.4.

### 2.15 SGD và Adam — hai bộ tối ưu

Sau khi có gradient, phải quyết định **cập nhật trọng số như thế nào**. Đó là
việc của **optimizer** (bộ tối ưu).

**SGD (Stochastic Gradient Descent)** — hạ gradient ngẫu nhiên. Quy tắc đơn giản
nhất có thể: **[nền]**

```
trọng_số_mới = trọng_số_cũ − η · gradient
```

`η` (eta) là **learning rate** (tốc độ học) — bước đi dài bao nhiêu. Chỉ có thế.
Một phép nhân và một phép trừ cho mỗi tham số. **Không có trạng thái nào được
nhớ giữa các bước.**

**Adam (Adaptive Moment Estimation)** — phức tạp hơn nhiều. Nó nhớ hai đại lượng
trung bình trượt cho **mỗi** tham số: **[nền]**

```
m ← β₁·m + (1−β₁)·g              trung bình trượt của gradient      (momentum)
v ← β₂·v + (1−β₂)·g²             trung bình trượt của bình phương   (độ lớn)

m̂ ← m/(1−β₁ᵗ)                    hiệu chỉnh thiên lệch đầu chuỗi
v̂ ← v/(1−β₂ᵗ)

trọng_số_mới = trọng_số_cũ − η · m̂ / (sqrt(v̂) + ε)
```

Mặc định: β₁ = 0,9, β₂ = 0,999, ε = 10⁻⁸, η = 3 × 10⁻⁴.

Adam thường học nhanh hơn SGD vì nó tự điều chỉnh bước đi cho từng tham số. Bảng
1 cho thấy điều đó không phải luôn đúng **[đo]** — trên `cartpole-random`, SGD
được **311,0** còn Adam chỉ **240,0**.

**Vì sao dự án chỉ chứng minh SGD.** Ba trở ngại độc lập, mỗi cái đủ để chặn:

| Trở ngại | Chi tiết |
| --- | --- |
| **Learning rate không biểu diễn được** | ở `FP_SCALE = 1000`, `3 × 10⁻⁴` mã hoá thành `round(0,0003 × 1000) = 0`. Ở thang này Adam **không tồn tại** ở tốc độ học mặc định của chính nó. **[đo]** |
| **Căn bậc hai** | `sqrt(v̂)` là phép mà mạch số học nguyên phải chứng minh bằng cách tìm nghiệm rồi kiểm bình phương — tốn cycles và phải xử lý làm tròn |
| **Trạng thái mang theo** | `m` và `v` phải được cam kết và mang qua từng bước, nhân đôi kích thước checkpoint và thêm ràng buộc cho mọi quan hệ |

Đây là một **giới hạn được ghi rõ trong paper**, không phải chỗ giấu đi.

### 2.16 Gradient clipping — và vì sao dự án dùng kiểu khác

Khi gradient quá lớn, một bước cập nhật có thể phá nát mô hình. **Gradient
clipping** là cắt bớt gradient trước khi cập nhật. Có hai kiểu: **[nền]**

| Kiểu | Cách làm | Đặc điểm |
| --- | --- | --- |
| **Clip theo chuẩn (norm)** | tính độ dài L2 của **toàn bộ** vector gradient; nếu > ngưỡng thì chia tỉ lệ cả vector | giữ nguyên **hướng**, chỉ đổi độ dài |
| **Clip theo giá trị (value)** | kẹp **từng thành phần** vào khoảng `[−c, +c]` | có thể đổi hướng, nhưng chỉ cần so sánh |

`agents.py` của Bảng 1 dùng `clip_grad_norm_(10.0)` — clip theo chuẩn. Quan hệ
SP1 dùng clip theo giá trị, `DEFAULT_GRADIENT_CLIP_FP = 10_000` (tức 10,0 ở
thang fixed-point) **[đo]**.

**Vì sao đổi:** clip theo chuẩn cần `sqrt` của tổng bình phương — cùng vấn đề
với Adam. Clip theo giá trị chỉ cần so sánh và gán, gần như miễn phí trong mạch.

**Cái giá của việc đổi đã được đo, và nó nhỏ:** trên `cartpole-random`, đổi từ
clip-norm sang clip-value làm điểm rơi từ **78,0** xuống **75,4** — mất 3,3%
**[đo]**. Xem mục 7.4.

### 2.17 Deadly triad — vì sao offline DQN hay phân kỳ

Ba thứ khi đi cùng nhau thì việc học có thể **phân kỳ**, không phải chỉ chậm:
**[nền]**

1. **Xấp xỉ hàm** — dùng mạng nơ-ron thay bảng tra
2. **Bootstrapping** — nhãn tính từ chính ước lượng của mình (chính là TD)
3. **Off-policy** — học từ dữ liệu do chính sách **khác** sinh ra

Offline RL có **cả ba**, luôn luôn. Đó là lý do offline DQN nổi tiếng khó tính.

Trong dự án, sự phân kỳ này không phải chuyện lý thuyết. Đo trên chuỗi CartPole
ở `learning_rate_fp = 50`, mỗi chunk 156 bước, giá trị Q lớn nhất **[đo]**:

```
chunk 1:  5,50 × 10⁴
chunk 2:  9,46 × 10⁵      ← ×17
chunk 3:  2,17 × 10⁷      ← ×23
chunk 4:  9,03 × 10⁸
chunk 5:  2,17 × 10¹⁰
chunk 6:  9,45 × 10¹¹
chunk 7:  3,96 × 10¹³
chunk 8:  9,49 × 10¹⁴
chunk 9:  4,14 × 10¹⁶     ← đã vượt ngưỡng tràn số nguyên
```

Nhớ lại mục 2.4: giá trị **đúng** của Q trên CartPole bị chặn ở khoảng **100**.
Ở đây nó là 4 × 10¹⁶. Q tăng khoảng **×22 mỗi 156 bước** — hàm mũ, không phải
tuyến tính.

Đây là phát hiện có hệ quả rất cụ thể cho dự án, và đáng nói trước thầy:

> **Độ dài lượt chạy chứng minh được bị chặn bởi tính ổn định số học, không phải
> bởi chi phí proof.** Ta hết số nguyên trước khi hết tiền thuê GPU.

Cách xử lý ở mục 8.2.

---
## 3. Mật mã, từ con số không

### 3.1 Hàm băm

**Hàm băm** (hash function) nhận vào dữ liệu dài tuỳ ý, trả ra một chuỗi dài cố
định. Dự án dùng **SHA-256**, trả ra 256 bit — viết dưới dạng 64 ký tự hex.
**[nền]**

```
SHA256("xin chao")  →  c9b48a4a...  (64 ký tự hex)
SHA256(cả bộ phim)  →  7f2e1d9c...  (vẫn đúng 64 ký tự)
```

Ba tính chất làm nó dùng được cho việc niêm phong: **[nền]**

| Tính chất | Nghĩa |
| --- | --- |
| **Tất định** | cùng đầu vào luôn cho cùng đầu ra, trên mọi máy, mọi thời điểm |
| **Kháng tiền ảnh** | biết `h`, không tìm ngược ra được `x` sao cho `SHA256(x) = h` |
| **Kháng va chạm** | không tìm được hai `x ≠ y` mà `SHA256(x) = SHA256(y)` |
| **Hiệu ứng tuyết lở** | đổi **một bit** đầu vào làm đổi khoảng **một nửa** số bit đầu ra |

Hệ quả dùng được: **công bố hash của một tệp là tự trói mình vào đúng tệp đó.**
Sau đó không sửa được nữa mà vẫn giữ hash cũ.

### 3.2 Cam kết dữ liệu, và vì sao lại là Merkle tree

Ta cần một cơ chế cho phép: công bố **một** giá trị ngắn đại diện cho cả dataset
50.000 dòng, rồi **sau đó** chứng minh "dòng số 4.213 nằm trong dataset đó" mà
không phải đưa 49.999 dòng còn lại.

Hãy xét lần lượt các phương án. Đây là câu hỏi bạn nêu — *vì sao Merkle chứ
không phải cái khác* — và câu trả lời chỉ rõ ràng khi đặt cạnh nhau.

**Phương án 1 — băm cả tệp.** `root = SHA256(toàn bộ dataset)`.

- ✅ Ngắn gọn, một giá trị.
- ❌ **Chứng minh một dòng thì phải đưa toàn bộ dataset** để người kiểm băm lại.
  Mất hết tính riêng tư, và tốn đúng bằng việc gửi cả dataset.

**Phương án 2 — danh sách hash.** Công bố `[h₁, h₂, ..., h₅₀₀₀₀]`.

- ✅ Chứng minh một dòng chỉ cần đưa dòng đó.
- ❌ **Cam kết dài 50.000 hash = 1,6 MB.** Nó không còn là "một giá trị ngắn".
  Và trong zkVM, guest phải nạp cả 1,6 MB đó vào bộ nhớ.

**Phương án 3 — Merkle tree.** Băm từng dòng thành **lá**, rồi ghép đôi băm lên
tới khi còn một giá trị duy nhất là **root**.

```
                    root  ← chỉ công bố giá trị này
                  /      \
             h(1,2)      h(3,4)
             /    \      /    \
           lá1   lá2   lá3   lá4
            |     |     |     |
          dòng1 dòng2 dòng3 dòng4
```

Muốn chứng minh `dòng3` thuộc cây, ta đưa **dòng3** cùng các **anh em trên đường
lên gốc**: `lá4` và `h(1,2)`. Người kiểm tự tính:

```
lá3'    = SHA256(dòng3)                ← tự băm lại từ dữ liệu được đưa
h(3,4)' = SHA256(lá3' ‖ lá4)
root'   = SHA256(h(1,2) ‖ h(3,4)')
so sánh root' với root đã công bố
```

Nếu khớp thì `dòng3` chắc chắn nằm trong tập đã cam kết. Chuỗi anh em đó gọi là
**Merkle path** hoặc **membership proof**.

- ✅ Cam kết chỉ **32 byte**, bất kể dataset lớn cỡ nào.
- ✅ Chứng minh một dòng chỉ cần **log₂(n)** hash — 100.000 dòng → **17** hash.
- ✅ Chỉ dùng hàm băm. Không cần trusted setup, không cần đường cong elliptic.
- ✅ **Rẻ trong zkVM**, vì SP1 có precompile SHA-256 chạy nhanh hơn hẳn code thường.

**Phương án 4 — cam kết đa thức (KZG), accumulator RSA, Verkle tree.** **[nền]**

| | Ưu | Nhược trong bối cảnh này |
| --- | --- | --- |
| **KZG** | proof kích thước **hằng số** (không phụ thuộc n), nhỏ hơn Merkle | cần **trusted setup**; dùng pairing trên đường cong elliptic — rất đắt để chứng minh **bên trong** một zkVM không có precompile cho nó |
| **RSA accumulator** | proof hằng số | cần nhóm bậc chưa biết, tức là trusted setup hoặc class group; số học modulo 2048-bit trong zkVM còn đắt hơn |
| **Verkle tree** | path ngắn hơn Merkle | dựa trên cam kết vector trên đường cong elliptic — lại rơi vào cùng vấn đề |

**Kết luận và cách nói trước phản biện:**

> Merkle thắng **không phải vì nó hiệu quả nhất về lý thuyết** — KZG cho proof
> ngắn hơn. Nó thắng vì mọi thao tác của nó là **băm**, và băm là thứ **rẻ nhất
> để chứng minh lại bên trong zkVM**. Chọn KZG sẽ đổi một proof ngắn hơn ở ngoài
> lấy hàng chục triệu cycles ở trong. Với dự án này, chi phí nằm ở phía prover,
> nên phải tối ưu phía đó.

**Chi phí đo được [đo].** Bốn dòng `merkle_membership` của Bảng 2:

| Số lá | Độ sâu | Cycles | Chênh so với dòng trên |
| ---: | ---: | ---: | ---: |
| 1.000 | 10 | 357.965 | — |
| 10.000 | 14 | 470.318 | +28.088 / tầng |
| 50.000 | 16 | 526.578 | +28.130 / tầng |
| 100.000 | 17 | 554.100 | +27.522 / tầng |

Hồi quy tuyến tính: **≈ 28.000 cycles cho mỗi tầng độ sâu**, phần cố định
≈ 77.600 cycles. Vì độ sâu tăng theo **logarit**, nhân dữ liệu lên 10 lần chỉ
thêm khoảng 3 tầng ≈ 84.000 cycles. Đó là lý do cột cycles gần như không nhúc
nhích khi dataset tăng 100 lần: **357.965 → 554.100**, chỉ +55%.

*Ghi chú lịch sử:* con số **23.571 cycles/tầng** từng được ghi trong các bản
trước là số đo **trước khi bật `overflow-checks`** (mục 8.2). Kiểm tra tràn số
làm quan hệ Merkle nặng thêm 13,0…17,7%, và 23.571 × 1,177 ≈ 27.700 — khớp với
số hiện tại. Bảng 2 hiện tại là số sau khi bật.

**Chi tiết cài đặt cần biết khi đọc code [đo]:**

- Lá: nối các số nguyên bằng dấu phẩy (`",".join(str(int(x)))`) rồi SHA-256 hex.
- Nút trong: `SHA256(bytes.fromhex(trái) + bytes.fromhex(phải))`.
- Số lá lẻ thì **nhân đôi lá cuối** (kiểu Bitcoin) để ghép đủ đôi.

### 3.3 Cam kết vào **cái gì** — một cái bẫy thật đã xảy ra

Một cạm bẫy tinh vi mà dự án đã mắc và đã sửa **[đo]**:

Dataset được cam kết bằng `SHA256(canonical_json(transition))` — băm biểu diễn
JSON. Nhưng quan hệ huấn luyện làm việc trên **số nguyên fixed-point**, và cây
Merkle của nó băm các số nguyên đó. Trên `cartpole-expert-v2`, hai cây cho hai
gốc khác nhau trên cùng 50.261 transition:

```
cây JSON             : 88cb5f28...
cây fixed-point      : 02de61a9...
```

Hệ quả: `merkle_membership` kiểm cây JSON, `training_fragment` kiểm cây
fixed-point, **và không có gì công bố gốc fixed-point** — nên prover tự chọn
được cây mà mình đã huấn luyện trên đó. Cách sửa theo Garg và cộng sự (CCS
2023): **dataset được cam kết chính là dataset fixed-point**. Với dữ liệu liên
tục không biểu diễn được bằng số nguyên (PointMaze) thì giữ quy tắc JSON và ghi
rõ ở trường `leaf_hash_rule` của từng dataset.

Bài học chung, đáng nhớ: **cam kết đúng thuật toán chưa đủ; phải cam kết vào
đúng vật thể mà phép tính thật sự đọc.**

### 3.4 Vì sao muốn có proof lại phải "viết mạch"

Đây là câu hỏi bạn nêu, và nó là câu hỏi hay nhất trong danh sách, vì trả lời
được nó thì hiểu được toàn bộ phần còn lại.

**Vấn đề gốc:** hệ chứng minh không biết "chương trình" là gì. Nó không hiểu
vòng lặp, hàm, con trỏ. Thứ duy nhất mà toán học của ZKP biết làm việc là:

> **hệ phương trình đa thức trên một trường hữu hạn.**

Nên muốn chứng minh bất cứ điều gì, ta phải **dịch phép tính thành một hệ phương
trình**. Hệ phương trình ấy chính là cái ta gọi là **mạch (circuit)**. **[nền]**

**Ví dụ cụ thể.** Muốn chứng minh "tôi biết `x` sao cho `x³ + x + 5 = 35`". Viết
lại thành các phép nhân/cộng cơ bản, mỗi phép một biến trung gian:

```
v₁ = x  · x          ← ràng buộc 1
v₂ = v₁ · x          ← ràng buộc 2
v₃ = v₂ + x          ← ràng buộc 3
v₄ = v₃ + 5          ← ràng buộc 4
v₄ = 35              ← ràng buộc 5 (đầu ra công khai)
```

Năm dòng đó là **mạch**. Bộ giá trị `(x, v₁, v₂, v₃, v₄)` thoả cả năm dòng gọi là
**witness** (nhân chứng). Nhiệm vụ của hệ chứng minh là thuyết phục verifier
rằng *"tôi biết một witness thoả toàn bộ ràng buộc"* mà không nói `x` bằng bao
nhiêu.

**Cơ chế đằng sau, kể ở mức trực giác [nền]:**

1. **Số hoá.** Mọi giá trị được coi là phần tử của một trường hữu hạn (mục 3.5).
2. **Đa thức hoá.** Toàn bộ bảng witness được biến thành các **đa thức** — mỗi
   cột của bảng thành một đa thức đi qua các điểm của cột đó.
3. **Ràng buộc thành một đa thức bằng 0.** Nếu witness đúng, một tổ hợp cụ thể
   của các đa thức đó **triệt tiêu tại mọi điểm ta quan tâm**. Nếu witness sai,
   nó không triệt tiêu.
4. **Kiểm ngẫu nhiên tại một điểm.** Đây là mấu chốt. Hai đa thức bậc `d` khác
   nhau chỉ trùng nhau tại **nhiều nhất `d` điểm**. Trường có cỡ 2⁶⁴ hoặc lớn
   hơn, còn `d` chỉ cỡ vài triệu — nên nếu verifier chọn **một điểm ngẫu nhiên**
   và hai bên khớp ở đó, xác suất prover gian lận mà lọt là `d / |trường|`, nhỏ
   tới mức bỏ qua được. Đây gọi là bổ đề **Schwartz–Zippel**.
5. **Cam kết để prover không đổi bài giữa chừng.** Prover phải "niêm phong" các
   đa thức **trước** khi biết điểm kiểm. STARK niêm phong bằng **cây Merkle của
   các đánh giá đa thức** cộng giao thức **FRI**; Groth16/PLONK niêm phong bằng
   cam kết trên đường cong elliptic.

Tóm lại trong một câu để nói với thầy:

> Proof không "quan sát" chương trình chạy. Nó biến chương trình thành một bài
> toán đa thức, rồi kiểm bài toán đó tại **một điểm ngẫu nhiên duy nhất** — đó
> là vì sao verify chỉ mất 54 mili giây trong khi phép tính gốc tốn hàng tỉ
> phép toán.

### 3.5 Trường hữu hạn — vì sao số nguyên chứ không phải số thực

**Trường hữu hạn** (finite field) là tập số hữu hạn `{0, 1, 2, ..., p−1}` với
phép cộng và nhân **lấy dư cho `p`**, trong đó `p` là số nguyên tố. **[nền]**

```
Trong trường p = 7:   5 + 4 = 9 mod 7 = 2
                      3 × 5 = 15 mod 7 = 1
```

**Vì sao ZKP bắt buộc phải làm việc trên đó:**

| Lý do | Giải thích |
| --- | --- |
| **Toán học cần nó** | Bổ đề Schwartz–Zippel, phép nội suy đa thức, FFT — tất cả đều phát biểu trên trường. Số thực dấu phẩy động **không phải một trường** theo nghĩa đó: `(a+b)+c ≠ a+(b+c)` do làm tròn |
| **Cần tất định tuyệt đối** | prover và verifier phải ra **đúng cùng một giá trị**. Số dấu phẩy động cho kết quả khác nhau giữa các CPU, các trình biên dịch, các mức tối ưu |
| **Cần biểu diễn hữu hạn, chính xác** | mỗi phần tử là một số nguyên gọn, không có mantissa, không có `NaN`, không có `±0`, không có tràn ngầm |

Nói ngắn: **số thực không có ngữ nghĩa xác định để mà chứng minh.** Câu hỏi "phép
nhân này có đúng không" không có câu trả lời duy nhất khi hai bên làm tròn khác
nhau.

### 3.6 Fixed-point — cách nhét số thực vào số nguyên

Nhưng học máy cần số thực: `γ = 0,99`, learning rate `0,01`, trọng số
`−0,0473`. Giải pháp chuẩn là **fixed-point**: nhân mọi số thực với một hằng số
rồi làm tròn thành số nguyên. **[nền]**

Dự án dùng `FP_SCALE = 1000` **[đo]**:

```
0,99   →  990       (đặt tên GAMMA_FP)
0,01   →  10
0,05   →  50
1,0    →  1000
−0,047 →  −47
```

**Phép nhân phải chia lại cho scale**, nếu không thang đo nhân đôi:

```
0,5 × 0,5 = 0,25
500 × 500 = 250.000            ← đây là 250,0 ở thang 1000, sai gấp 1000 lần
250.000 // 1000 = 250          ← đúng: 0,25
```

Nên quy tắc bất di bất dịch của repo là `(a * b) // fp_scale`, dùng **chia lấy
nguyên**, **không làm tròn** — vì Python và Rust phải cho kết quả giống nhau đến
từng bit, và hai ngôn ngữ làm tròn số âm khác nhau.

**Hai hệ quả không hiển nhiên, và cả hai đều quan trọng:**

**(1) Có những giá trị đơn giản là không tồn tại.** Learning rate mặc định của
Adam là `3 × 10⁻⁴` → `round(0,0003 × 1000) = 0`. Một tốc độ học bằng 0 nghĩa là
**không học gì cả**. Ở thang này, Adam không dùng được ở tham số mặc định của
chính nó. **[đo]**

**(2) Có trần.** Guest tính trên `i64`, tối đa ≈ 9,22 × 10¹⁸. Phép nhân chiết
khấu `990 × q` vượt trần khi `|q|` qua `i64::MAX / 990 ≈ 9,32 × 10¹⁵`. Nhớ lại
mục 2.17: Q trong lượt chạy đã leo tới `4,14 × 10¹⁶`. Nó **đã vượt**. Chuyện gì
xảy ra khi vượt, và cách sửa, ở mục 8.2.

### 3.7 Ba loại proof — STARK, Groth16, PLONK

Ba hệ chứng minh khác nhau về **cách niêm phong đa thức** ở bước 5 của mục 3.4.
Khác biệt đó kéo theo mọi khác biệt còn lại. **[nền]**

**Trước hết — trusted setup là gì.**

Một số hệ chứng minh cần một bộ tham số công khai được sinh ra từ một **bí mật
ngẫu nhiên** (thường gọi là "toxic waste", chất thải độc hại). Sau khi sinh xong,
bí mật đó **phải bị huỷ**. Nếu ai đó giữ lại được nó, họ **tạo được proof giả
cho phát biểu sai**, và không ai phát hiện ra — vì proof giả trông y hệt proof
thật.

Nghi lễ sinh tham số gọi là **ceremony**. Cách giảm rủi ro: cho **nhiều** người
cùng tham gia, mỗi người góp một phần ngẫu nhiên; hệ an toàn miễn là **ít nhất
một** người trung thực huỷ phần của mình. Ceremony lớn nhất từng tổ chức có hàng
nghìn người tham gia.

Vẫn là một **giả định tin cậy**, và nó là thứ mà một cơ quan quản lý sẽ hỏi tới.

| | **STARK** | **Groth16** | **PLONK** |
| --- | --- | --- | --- |
| Niêm phong bằng | băm + FRI | pairing trên đường cong elliptic | cam kết đa thức (KZG) |
| **Trusted setup** | **không cần** | **cần, và riêng cho từng mạch** | cần, nhưng **dùng lại được** cho mọi mạch |
| Kích thước proof | lớn (~2,7 MB ở đây) | rất nhỏ (~200 byte tới vài KB) | nhỏ (~500 byte tới vài KB) |
| Thời gian verify | rất nhanh | rất nhanh | nhanh |
| Giả định mật mã | chỉ cần hàm băm | pairing + setup | pairing + setup |
| Kháng lượng tử | **có** (chỉ dựa vào băm) | không | không |
| Đổi mạch thì sao | không phải làm gì | **phải làm lại ceremony** | dùng lại setup cũ |

**Dự án dùng gì và vì sao:**

- **STARK là mặc định.** SP1 sinh STARK. Không trusted setup nghĩa là **không có
  giả định tin cậy nào phải giải thích với cơ quan quản lý** — rất hợp với bối
  cảnh ở mục 1. Proof to nhưng ta gửi tệp, không đưa lên blockchain.

- **Groth16 được đo một dòng, để biết cái giá.** Dòng `groth16_recursive_t16`
  của Bảng 2 **[đo]**:

  | | STARK (`native_flat_recursive_t16`) | Groth16 child |
  | --- | ---: | ---: |
  | Cycles | 422.726.492 | **6.180.861.737** (×14,6) |
  | Prove | 193,4 s | **1.596,9 s** (×8,3) |
  | Verify | 0,054 s | **68,0 s** (×1.256) |
  | Proof size | 1.274.074 B | 1.468.175.345 B |

  Đây là **chi phí kiểm một proof Groth16 ở bên trong guest**, không phải chi phí
  dùng Groth16 làm proof cuối. Số liệu nói rõ: nhét kiểm-pairing vào trong zkVM
  thì rất đắt, vì zkVM không có precompile cho phép toán BN254.

  *Đọc đúng dòng này rất quan trọng khi trình bày:* nó **không** nói "Groth16
  tệ". Groth16 dùng đúng chỗ — làm lớp bọc cuối để đưa lên blockchain — thì cho
  proof vài trăm byte. Nó chỉ đắt khi bị đem vào **trong** mạch.

- **PLONK chưa dùng.** Đo cho thấy bước bọc PLONK cần khoảng **60 GB RAM**, vượt
  máy đã thuê (32 GB). Bước bọc Groth16 cần ~14 GB và cần Docker cho Gnark.
  **[đo]** Đây là giới hạn tài nguyên, không phải kết luận kỹ thuật.

---

## 4. zkVM và SP1

### 4.1 Từ mạch tới máy ảo — vì sao có zkVM

Mục 3.4 nói mọi phép tính phải thành mạch. Với `x³ + x + 5` thì viết tay được.
Với **vòng huấn luyện DQN bảy bước ở mục 2.10** thì viết tay là ác mộng: mỗi
phép nhân ma trận, mỗi lần so sánh, mỗi lần băm SHA-256 đều phải mở ra thành
ràng buộc, và **một ràng buộc sai là một lỗ hổng an toàn không ai nhìn thấy**.

**zkVM (zero-knowledge virtual machine)** đảo ngược cách làm: **[nền]**

> Thay vì viết mạch cho *chương trình của bạn*, người ta viết **một mạch cho
> chính CPU** — mạch mô tả "một bộ xử lý thực thi một lệnh thì đúng nghĩa là
> gì". Sau đó bạn viết chương trình bằng ngôn ngữ bình thường, biên dịch ra mã
> máy, và mạch-CPU đó chứng minh từng lệnh.

So sánh trực tiếp:

| | Viết mạch thủ công | zkVM |
| --- | --- | --- |
| Diễn đạt phép tính | mô tả từng ràng buộc | viết Rust bình thường |
| Công sức | rất lớn | thấp |
| Nguy cơ sai lặng lẽ | cao — ràng buộc thiếu thì không ai báo | thấp — sai thì chương trình chạy sai, thấy ngay |
| Tốc độ prove | nhanh hơn nhiều | chậm hơn (thường 10–1000×) |
| Reviewer kiểm được không | phải đọc mạch số học | **đọc thẳng mã nguồn Rust** |

**Lựa chọn của dự án và cách bảo vệ nó trước phản biện:**

> Dự án chọn zkVM và **chấp nhận chậm hơn**, vì mục tiêu là một artifact mà
> reviewer **kiểm chứng được**. Một reviewer mở
> `zk_backend/training_fragment/sp1/shared/src/lib.rs` là đọc được đúng quan hệ
> đang được chứng minh, bằng Rust thường. Nếu viết mạch thủ công, cùng reviewer
> đó sẽ phải tin vào vài nghìn ràng buộc số học mà không có cách nào đọc hiểu
> trong thời gian phản biện. Với một paper về **tính kiểm chứng được**, đánh đổi
> đó là đúng chiều.

### 4.2 RISC-V là gì

**RISC-V** (đọc là "risk five") là một **kiến trúc tập lệnh** (ISA — instruction
set architecture): bản đặc tả quy định một bộ xử lý có những lệnh nào, thanh ghi
nào, và mỗi lệnh làm gì. **[nền]**

Nó ngang hàng với x86 (Intel/AMD) và ARM (điện thoại, Apple Silicon) về vai trò,
nhưng khác ở hai điểm quyết định:

| | x86 | ARM | RISC-V |
| --- | --- | --- | --- |
| Bản quyền | Intel/AMD | ARM Ltd., phải trả phí | **mở, miễn phí** |
| Số lệnh | hàng nghìn, rất phức tạp | vài trăm | **~50 lệnh cơ bản** |
| Thiết kế | CISC, lệnh làm nhiều việc | RISC | **RISC, mỗi lệnh làm một việc** |

**Vì sao mọi zkVM đều chọn RISC-V** — ba lý do, và cả ba đều thiết thực:

1. **Ít lệnh nghĩa là mạch nhỏ.** Phải viết ràng buộc cho **từng** lệnh. 50 lệnh
   thì làm được; hàng nghìn lệnh x86 thì không.
2. **Mỗi lệnh làm một việc đơn giản.** Ràng buộc cho `ADD` là "c = a + b". Ràng
   buộc cho một lệnh x86 đọc bộ nhớ, cộng, rồi ghi ngược lại thì phức tạp hơn
   nhiều lần.
3. **Có sẵn trình biên dịch.** LLVM đã hỗ trợ RISC-V, nên Rust/C++ biên dịch
   sang được ngay, không phải viết compiler mới.

SP1 dùng biến thể **RV32IM**: 32-bit, tập lệnh cơ bản (I) cộng phần nhân/chia
(M). Đây là lý do guest tính trên `i64` bằng cách ghép hai thanh ghi 32-bit — và
là một lý do phép nhân 64-bit tốn nhiều cycles hơn ta tưởng.

### 4.3 Vì sao "mọi lệnh đều sinh ra bằng chứng"

Câu này trong tài liệu trước viết quá gọn nên gây hiểu nhầm. Nói cho chính xác:

> **Không phải mỗi lệnh sinh ra một proof riêng.** Cả chương trình sinh ra **một**
> proof, nhưng proof đó ràng buộc **mọi lệnh đã chạy** — không lệnh nào được bỏ
> qua khỏi phạm vi ràng buộc.

Cơ chế, kể theo trình tự: **[nền]**

**Bước 1 — chạy và ghi lại.** Host chạy chương trình guest trên một bộ mô phỏng
RISC-V và ghi lại **execution trace** (vết thực thi): một **bảng**, mỗi hàng là
trạng thái CPU sau một lệnh.

```
 hàng | pc   | lệnh      | x1  | x2  | x3  | ... | ghi/đọc bộ nhớ
------+------+-----------+-----+-----+-----+-----+----------------
    0 | 0x00 | ADDI x1,5 |   5 |   0 |   0 | ... | —
    1 | 0x04 | ADDI x2,7 |   5 |   7 |   0 | ... | —
    2 | 0x08 | ADD x3,x1,x2|  5 |   7 |  12 | ... | —
    3 | 0x0c | SW x3,(x4)|   5 |   7 |  12 | ... | ghi 12 vào 0x1000
  ... |      |           |     |     |     |     |
```

**Bước 2 — ràng buộc mọi hàng.** Mạch-CPU viết sẵn của SP1 phát biểu, dưới dạng
phương trình đa thức, những điều như:

- nếu opcode ở hàng này là `ADD` thì `x3[hàng i+1] = x1[hàng i] + x2[hàng i]`
- `pc[i+1] = pc[i] + 4` trừ khi lệnh là nhảy
- mỗi lần đọc bộ nhớ tại địa chỉ `A` phải trả về đúng giá trị của lần **ghi cuối
  cùng** vào `A` (kiểm tra tính nhất quán bộ nhớ, thường làm bằng permutation
  argument)

Các ràng buộc này gọi chung là **AIR** (Algebraic Intermediate Representation).

**Bước 3 — chứng minh cả bảng cùng lúc.** Mỗi **cột** của bảng thành một đa
thức. Nếu mọi hàng thoả ràng buộc thì một đa thức tổ hợp cụ thể triệt tiêu trên
toàn miền. Prover cam kết các đa thức đó (Merkle + FRI) và verifier kiểm tại một
điểm ngẫu nhiên.

**Đây là chỗ trả lời câu hỏi của bạn:** vì ràng buộc được áp cho **mọi hàng của
bảng**, và bảng chứa **mọi lệnh đã chạy**, nên không có lệnh nào nằm ngoài tầm
kiểm. Prover không thể bỏ bớt một lệnh, đổi kết quả một phép cộng, hay nhảy sai
chỗ — mỗi việc đó phá vỡ ràng buộc ở hàng tương ứng, và đa thức không còn triệt
tiêu.

**Bước 4 — chia shard.** Bảng của một lượt chạy lớn có hàng trăm triệu hàng,
không vừa bộ nhớ. SP1 cắt nó thành **shard**, chứng minh từng shard, rồi dùng
**recursion** (mục 6) để gộp các proof shard thành một. Đây là lý do một proof
STARK của SP1 thực chất đã là một proof đệ quy ở bên trong.

### 4.4 Cycles — chính xác là gì

> **Một cycle = một lệnh RISC-V đã thực thi = một hàng của bảng trace.**

Đó là toàn bộ định nghĩa. Cycles không phải đơn vị thời gian, không phải xung
nhịp CPU thật.

**Bốn tính chất khiến nó là đơn vị đo được dùng khắp Bảng 2 [đo]:**

1. **Tất định.** Cùng một guest ELF và cùng đầu vào luôn cho **đúng** cùng số
   cycles, trên mọi máy, mọi lúc. Thời gian thì không — nó phụ thuộc CPU, GPU,
   tải máy.
2. **Dự báo chi phí.** Chi phí prove gần như tuyến tính theo cycles.
3. **Dự báo bộ nhớ.** Ngoại suy từ một lần OOM thật: **≈ 27 byte RAM máy chủ cho
   mỗi cycle** ở proof `training_fragment` **[đo]**. Nhờ vậy tính được trên giấy
   máy nào chạy nổi trước khi thuê.
4. **So sánh được giữa các quan hệ.** Bảng 2 trải từ **116.750** (Merkle
   canonical) tới **6.180.861.737** (Groth16 child) — gấp **52.941 lần**.

**Cảnh báo khi đọc:** cycles tất định theo cặp `(guest ELF, đầu vào)` — nghĩa là
**đổi guest thì đổi cycles**. Đã đo: cùng vector nhưng khác phiên bản
`cargo-prove` cho `training_aggregation_t32` ra 798.811 so với 785.786 ghi trước
đó, lệch +1,66% **[đo]**. Nên khi so sánh phải cùng một lượt build.

### 4.5 Succinct Labs và SP1

**Succinct Labs** là công ty phát triển **SP1**, một zkVM mã nguồn mở cho RISC-V.
Dự án ghim phiên bản **6.1.0** ở cả ba crate (`sp1-build`, `sp1-sdk`,
`sp1-zkvm`). **[đo]**

Ba khái niệm của SP1 xuất hiện khắp repo — nhớ ba từ này thì đọc được cấu trúc
thư mục:

| Thành phần | Chạy ở đâu | Việc | Ở đâu trong repo |
| --- | --- | --- | --- |
| **guest** | **bên trong** zkVM | phép tính được chứng minh | `zk_backend/<quan hệ>/sp1/guest/` |
| **host** | bên ngoài, máy thường | nạp dữ liệu, gọi prover, ghi kết quả | `.../sp1/host/` |
| **shared** | cả hai bên | thư viện Rust chứa logic quan hệ | `.../sp1/shared/` |

Vài từ nữa sẽ gặp trong provenance:

| Từ | Nghĩa |
| --- | --- |
| **guest ELF** | tệp nhị phân của guest sau khi biên dịch sang RISC-V |
| **vkey** (verification key) | định danh mật mã của **chương trình** — verifier dùng nó để biết proof này chứng minh cho chương trình nào |
| **public values** | dữ liệu guest ghi ra công khai, verifier đọc được |
| **precompile** | mạch viết tay cho một phép tính hay dùng (SHA-256, phép toán trường), nhanh hơn nhiều so với để guest chạy từng lệnh |

**Vì sao SP1 chứ không phải công nghệ khác** — trả lời theo tiêu chí của dự án:

| Lựa chọn | Vì sao **không** chọn cho dự án này |
| --- | --- |
| **Circom / Halo2** (viết mạch tay) | mạnh và nhanh, nhưng reviewer không đọc nổi quan hệ DQN dưới dạng ràng buộc; và nguy cơ ràng buộc thiếu là lỗ hổng câm |
| **ezkl** (ONNX → mạch) | chuyên cho **suy luận** mạng nơ-ron, không cho **huấn luyện**. Nó không diễn đạt được sync target network, lấy mẫu replay, hay cập nhật checkpoint |
| **RISC Zero** | cùng họ zkVM RISC-V, ứng viên hợp lý. Đây là **lựa chọn thay thế thật sự**, không phải phương án bị loại vì kém |
| **Jolt** | zkVM dựa trên lookup, hứa hẹn nhanh, nhưng non hơn về recursion và lớp bọc Groth16 tại thời điểm chọn |
| **Cairo** (StarkWare) | ISA riêng, không phải RISC-V — không dùng lại được hệ sinh thái Rust và LLVM |

Lý do **chọn** SP1, theo đúng thứ tự quan trọng với dự án:

1. **Guest viết bằng Rust thường.** Logic quan hệ nằm trong `shared/`, dùng chung
   giữa host và guest — đọc được, test được trên CPU thường.
2. **Có đường CUDA.** `SP1_CUDA=1` cho `training_fragment` và
   `training_aggregation`. Đo được: `training_fragment_k8` từ **144,6 s** trên
   CPU xuống **3,8 s** trên A10G — **nhanh ~38×** **[đo]**. Không có nó thì
   Bảng 2 không chạy nổi trong ngân sách.
3. **Recursion chạy được thật.** Guest verify proof con bằng mật mã, đo được ở
   T = 16/32/64 và cây nhị phân tới 4.992 bước.
4. **Có lớp bọc Groth16/PLONK.** Cho phép **đo** cái giá của chúng thay vì chỉ
   trích dẫn.
5. **Precompile SHA-256.** Merkle là phép tính trung tâm của dự án; precompile
   làm nó rẻ.
6. **Không cần Docker cho CUDA.** `sp1-cuda` 6.1.0 tải `sp1-gpu-server` rồi nối
   qua Unix socket **[đo]** — bớt một tầng vận hành khi thuê máy theo giờ.

**Cách nói trung thực trước phản biện:** dự án **không** khảo sát so sánh có hệ
thống giữa SP1 và RISC Zero. Chọn SP1 vì đường CUDA và recursion đã dùng được
tại thời điểm bắt đầu. Nói thẳng như vậy tốt hơn là dựng ra một bảng so sánh
không có phép đo chống lưng.

### 4.6 Yêu cầu phần cứng, và những gì đã trả giá để biết

**[đo]** trong các phiên chạy thật:

| Sự thật | Số đo |
| --- | --- |
| GPU phải có Compute Capability ≥ 8.0 và ≥ 24 GB VRAM | T4 (CC 7.5) **không** đạt |
| Recursion không chạy nổi trên CPU | > 61 GB RAM, không hoàn thành |
| Recursion trên GPU thì bộ nhớ **phẳng** | 18,4 GB VRAM, **không đổi** qua 20 lần chênh lệch cycles |
| Nhưng proof `training_fragment` thì **không** phẳng | tăng theo cycles, và tiêu **RAM máy chủ** chứ không phải VRAM |
| Máy dùng | **AWS g5.2xlarge** — 1 GPU A10G, 32 GB RAM, ≈ **$1,2/giờ** |

Điểm thứ tư từng làm hỏng một lượt chạy và đáng kể lại: prove một lá
`training_fragment` 504.115.089 cycles trên máy g5.**x**large (15 GB RAM) chết
với `CudaClientError: early eof`. `dmesg` cho thấy `Out of memory: Killed process
sp1-gpu-server` với ≈ 13,5 GB, **trong khi VRAM dùng 0 MiB**. Nút thắt là
`sp1-gpu-server` — một tiến trình **riêng**, nên peak RSS của host chỉ báo 1,5 GB
và không hề lộ nguyên nhân. Bài học: **chọn máy theo RAM, không theo VRAM.**

Hai quy tắc vận hành khác, cũng học bằng cách trả giá **[đo]**:

- **Dùng on-demand, không dùng spot.** Một lượt spot 14 giờ bị AWS thu hồi, mất
  toàn bộ kết quả. Tiết kiệm $1,2 cho 3 giờ mà rủi ro mất tất cả — đổi chác tệ
  cho việc chạy một lần.
- **Kết quả phải rời khỏi máy sau mỗi bước.** Và đừng đụng vào lệnh `shutdown` đã
  hẹn sẵn: huỷ rồi đặt lại làm máy tắt **ngay lập tức**, mất phần việc dở.

---
# KHỐI C — DỰ ÁN

## 5. Kiến trúc

### 5.1 Bốn lớp

```
Lớp 1  DỮ LIỆU        thu thập → kiểm toán → cam kết Merkle → xác minh
                      scripts/data/ , artifacts/datasets/
   ↓
Lớp 2  QUAN HỆ        oracle Python thuần: không đọc file, không CLI, không
                      biến môi trường
                      zk_offline_dqn/relations/
   ↓
Lớp 3  BACKEND        guest / host / shared bằng Rust, sinh proof SP1
                      zk_backend/<quan hệ>/sp1/
   ↓
Lớp 4  GỘP            nối nhiều proof thành một proof duy nhất
                      training_aggregation
```

Lý do tách lớp: mỗi lớp kiểm được **độc lập**, và mỗi phát biểu trong paper truy
ngược được về một artifact cụ thể. Ranh giới được ép bằng quy tắc — `relations/`
**bị cấm** dùng `argparse`, đọc file, hay đọc biến môi trường, để logic toán học
không lẫn vào phần kịch bản. Một quan hệ chỉ nhận vào dict và trả ra dict.

### 5.2 Từng quan hệ nghĩa là gì trong quá trình huấn luyện

Đây là câu hỏi trung tâm của bạn. Nhớ lại **vòng huấn luyện bảy bước** ở mục
2.10:

```
1. lấy một transition (s, a, r, s', done) từ dữ liệu
2. chạy mạng trên s   → Q(s, a)
3. chạy mạng trên s'  → max Q(s', a')
4. TD target = r + γ · max Q(s', a')
5. loss = SmoothL1(TD target − Q(s,a))
6. tính gradient
7. cập nhật trọng số
```

Tám quan hệ có backend SP1 phủ vòng lặp đó theo kiểu **đồng tâm**: quan hệ nhỏ
chứng minh một mảnh, quan hệ lớn chứng minh cả cụm. Bảng dưới đọc từ trong ra
ngoài.

---

**(1) `merkle_membership` — "dòng dữ liệu này thật sự nằm trong tập đã cam kết"**

| | |
| --- | --- |
| Phủ bước | trước bước 1 |
| Phát biểu | "transition mà tôi dùng có mặt trong cây Merkle gốc `R`" |
| Public input | `dataset_root`, chỉ số dòng, độ sâu |
| Private witness | nội dung transition, Merkle path |
| Chống được | bịa transition không có trong dataset |

Đây là quan hệ **duy nhất** nối phép tính với **dữ liệu**. Không có nó, mọi thứ
phía sau chỉ chứng minh "tôi đã tính đúng trên **một** bộ số nào đó" chứ không
phải "trên **dữ liệu đã đăng ký**.

---

**(2) `td_mvp` — "TD target tính đúng cho một transition"**

| | |
| --- | --- |
| Phủ bước | 4 và 5 |
| Phát biểu | "cho transition này và các giá trị Q này, TD target và loss SmoothL1 tính đúng" |
| Chống được | sửa `r`, sửa `done`, sửa `γ`, tính sai loss |

MVP = *minimum viable proof* — quan hệ đầu tiên dựng được, chứng minh đúng công
thức ở mục 2.8. Nó **chưa** chứng minh Q đến từ đâu; Q vẫn là đầu vào.

---

**(3) `forward_td_mlp` — "các giá trị Q đó thật sự do mạng này sinh ra"**

| | |
| --- | --- |
| Phủ bước | 2 và 3 (rồi cộng luôn 4, 5) |
| Phát biểu | "chạy mạng có checkpoint hash `H` trên `s` cho ra đúng `Q(s,a)`, và trên `s'` cho ra đúng `max Q(s', a')`" |
| Chống được | bịa giá trị Q — lỗ mà `td_mvp` để hở |

Đây là quan hệ đóng lỗ lớn nhất của `td_mvp`: nó **nối Q với trọng số mạng**.
Nhân ma trận, ReLU, argmax — tất cả bằng số nguyên fixed-point trong guest.

---

**(4) `one_step_sgd_tiny` — "một bước cập nhật trọng số làm đúng"**

| | |
| --- | --- |
| Phủ bước | 6 và 7 |
| Phát biểu | "từ loss này, gradient tính đúng, và `w_mới = w_cũ − η·g` áp đúng, cho ra checkpoint hash `H'`" |
| Chống được | cách gian lận số 4 ở mục 1.2 — sửa gradient |

---

**(5) `training_update` — "một bước huấn luyện **hoàn chỉnh**"**

| | |
| --- | --- |
| Phủ bước | **1 → 7, toàn bộ** |
| Phát biểu | "từ checkpoint `H` và dataset gốc `R`, một bước huấn luyện dẫn đúng tới checkpoint `H'`" |
| Batch size | **1** (`training_update_batch1`; batch 4/8/16 chưa hỗ trợ) |

Đây là quan hệ đầu tiên có phát biểu **khép kín**: đầu vào là một checkpoint và
một cam kết dataset, đầu ra là checkpoint kế tiếp. Nó gộp (1)–(4) làm một.

---

**(6) `short_trace` — "chuỗi checkpoint nối đúng"**

| | |
| --- | --- |
| Phủ | *giữa* các bước |
| Phát biểu | "checkpoint cuối của bước `t` đúng là checkpoint đầu của bước `t+1`" |
| Chống được | ghép các bước huấn luyện rời rạc không liên quan thành một "lượt chạy" giả |

Nghe tầm thường nhưng không hề. Không có nó, prover chứng minh 1.000 bước hợp lệ
**riêng lẻ** rồi khai đó là một lượt chạy 1.000 bước, trong khi mỗi bước xuất
phát từ một mô hình khác nhau.

---

**(7) `training_fragment` — "*k* bước liên tiếp"**

| | |
| --- | --- |
| Phủ | *k* lần vòng lặp bảy bước, cộng logic sync target |
| Kích thước đã prove | `k ∈ {1, 4, 8}` trên vector canonical; `k = 1` trên dataset đã commit; `k = 156` làm **lá** của cây whole-run |
| Cycles | k=1: 979.945 · k=4: 2.799.333 · k=8: 5.193.244 **[đo]** |

Đây là **con ngựa thồ** của dự án. Ngoài vòng lặp, nó còn chứng minh ba thứ mà
các quan hệ nhỏ hơn không đụng tới:

- **Đồng bộ target đúng lịch** — cứ mỗi `target_sync_interval` bước thì target
  checkpoint phải bằng online checkpoint, và giữa hai lần thì phải **đứng yên**.
- **Chỉ số minibatch được dẫn xuất đúng** — không phải do prover khai (mục 8.1).
- **Giá trị Q nằm trong biên** — `|q| ≤ q_abs_max_fp`, kiểm **trước** phép nhân
  `γ · q` (mục 8.2).

Cycles tăng gần tuyến tính theo *k*: từ k=1 sang k=8, cycles ×5,3 cho 8× công
việc — phần chênh là chi phí cố định (nạp dữ liệu, kiểm Merkle gốc).

---

**(8) `training_aggregation` — "nhiều fragment ghép thành một lượt chạy"**

| | |
| --- | --- |
| Phủ | lớp 4 |
| Hai chế độ | `proof_manifest_chain` và `recursive_sp1` — mục 6 |

---

**Nhìn tổng thể, tám quan hệ là một dàn giáo đồng tâm:**

```
merkle_membership   ─┐
td_mvp              ─┤
forward_td_mlp      ─┼──▶ training_update ──▶ training_fragment ──▶ training_aggregation
one_step_sgd_tiny   ─┤        (1 bước)          (k bước)              (T bước)
short_trace         ─┘
```

Vì sao giữ cả những quan hệ nhỏ khi đã có quan hệ lớn? Vì mỗi cái là một **điểm
đo độc lập** cho Bảng 2, và vì khi một quan hệ lớn hỏng thì quan hệ nhỏ chỉ ra
được **hỏng ở đâu**.

### 5.3 Public input và private witness — nhìn một ví dụ thật

Từ vựng ở mục 3.4: **witness** là dữ liệu riêng, **public input** là phần công
khai mà proof ràng buộc vào. Đây là public input thật của
`training_fragment_cartpole_expert_k1` **[đo]**, rút gọn:

```
── Cam kết dữ liệu ──────────────────────────────
dataset_root              02de61a9…      ← gốc Merkle của cartpole-expert-v2
dataset_size              50261
dataset_id_hash           b91ea8a8…
manifest_hash             bdc07f0d…
audit_report_hash         06f123bd…      ← báo cáo kiểm toán dữ liệu
raw_trajectory_hash       f6c25677…
collection_log_final_hash 75e224aa…

── Siêu tham số (công khai, kiểm được) ──────────
fixed_point_scale         1000
gamma                     990            ← γ = 0,99
learning_rate             50             ← η = 0,05
batch_size                1
gradient_clip_fp          10000          ← clip 10,0
q_abs_max_fp              4503599627370496   ← 2^52, biên Q
target_sync_interval      4
target_sync_mode          hard           ← copy đè, không phải trung bình mềm
num_steps                 1
global_step_start         0

── Chuỗi checkpoint ─────────────────────────────
start_checkpoint_hash          107e13f5…
start_target_checkpoint_hash   11ee68b6…
final_checkpoint_hash          1c77751a…
final_target_checkpoint_hash   11ee68b6…   ← chưa sync nên bằng lúc đầu

── Cam kết vào diễn biến ────────────────────────
minibatch_indices_hash    2a323450…
loss_trace_hash           985dc22f…
gradient_trace_hash       f2915ac8…
update_trace_hash         59631bb3…
trace_hash                38c593b2…
sampler_seed              2393544246
sampler_type              lcg_mod_dataset_size
```

**Cách đọc bảng này — và đây là điểm rất đáng nói trước thầy:**

- Mọi thứ mô tả **thoả thuận** (siêu tham số, cam kết dữ liệu, checkpoint đầu và
  cuối) đều **công khai**. Cơ quan quản lý đọc được, kiểm được, so được với hồ sơ
  đã đăng ký.
- Mọi thứ chứa **dữ liệu** (transition thật, trọng số thật, gradient thật) đều
  **riêng tư**. Chỉ có *hash* của chúng lên public input.
- Nhờ vậy, một câu như *"anh đã dùng learning rate 0,05, γ = 0,99, clip 10,0,
  trên đúng dataset gốc `02de61a9`, và đi từ mô hình `107e13f5` tới `1c77751a`"*
  là **kiểm được trong 0,13 giây** mà không ai xem một dòng dữ liệu nào.

Đó là toàn bộ lời hứa ở mục 1, viết ra thành các trường cụ thể.

### 5.4 Ba nghĩa vụ xác minh mà học có giám sát không gặp

Đây là **đóng góp khoa học** của dự án — phần trả lời câu "vì sao đây không chỉ
là áp ZKP có sẵn lên một mô hình mới".

**Nghĩa vụ 1 — nhãn do chính mô hình đang học sinh ra.**

Học có giám sát: nhãn là dữ liệu cố định. Cam kết dataset **đã cam kết luôn**
nhãn. Xong.

RL: TD target được **tính ra trong lúc huấn luyện**, từ target network. Nên proof
phải chứng minh không chỉ *"tôi đã dùng nhãn này"* mà còn *"nhãn này được suy ra
đúng từ một checkpoint đã cam kết, theo đúng công thức Bellman"*. Đó là lý do
`forward_td_mlp` phải tồn tại, và là lý do public input phải mang **hai**
checkpoint (online và target) chứ không phải một.

**Nghĩa vụ 2 — đồng bộ target là sự kiện rời rạc.**

Nhớ mục 2.11: cứ *N* bước thì target ← copy(online). Đây là **sự kiện rời rạc**,
không phải một phép tính trơn.

Một prover được tự do dịch chuyển các thời điểm sync sẽ làm **đổi ý nghĩa của
mọi nhãn phía sau**. Và điều nguy hiểm: **lượt chạy kết quả vẫn hoàn toàn tự
nhất quán.** Không có mâu thuẫn nội tại nào để phát hiện — mọi phép tính vẫn
đúng, chỉ là đúng với một lịch sync khác lịch đã khai.

Nên `target_sync_interval` và `target_sync_mode` phải nằm trong **public input**,
và quan hệ phải kiểm rằng target checkpoint đứng yên đúng chỗ và nhảy đúng chỗ.
Bảng 3 có 11 phép thử riêng cho nhóm này (`target_network_sync`).

**Nghĩa vụ 3 — lấy mẫu replay không có thứ tự chuẩn tắc.**

Học có giám sát duyệt dataset tuần tự, epoch này qua epoch khác. Có một thứ tự
hiển nhiên, ai cũng kiểm được.

RL **rút ngẫu nhiên**. Không có thứ tự chuẩn. Và:

> **Prover nào chọn được cách rút thì chọn luôn dữ liệu mà phát biểu nói về.**

Nếu `sampler_seed` do prover khai, họ thử hàng nghìn seed cho tới khi tìm được
tập mẫu cho kết quả đẹp — rồi công bố seed đó. Mọi thứ vẫn kiểm đúng. Đây gọi là
**grinding tấn công** trên bộ sinh ngẫu nhiên.

Cách chữa: seed phải **dẫn xuất từ những thứ đã bị khoá**:

```
sampler_seed = SHA256("training_fragment_sampler_seed_v1", dataset_root,
                      global_step_start)  rồi lấy 64 bit đầu, mod LCG_M
```

`dataset_root` khoá vào dữ liệu; `global_step_start` khoá vào vị trí trong chuỗi.
Prover không còn bậc tự do nào.

**Nghĩa vụ thứ ba không phải lo xa — chính dự án đã mắc.** Xem mục 8.1. Đó là lý
do phần này đứng ở đây với đầy đủ trọng lượng, chứ không phải một mục lý thuyết.

### 5.5 Vì sao có **cả** Python và Rust — oracle là gì

Đây là câu hỏi bạn nêu rõ nhất: *"nếu chạy Python rồi thì sao phải chạy Rust
nữa, và ngược lại?"* Câu trả lời có hai tầng.

**Oracle / reference implementation là gì.**

Một **reference implementation** (bản cài đặt tham chiếu), còn gọi là **oracle**,
là bản viết **đơn giản nhất có thể, ưu tiên đọc hiểu hơn tốc độ**, dùng làm
**định nghĩa chuẩn** của phép tính. Khi hỏi "kết quả đúng là gì?", ta hỏi oracle.

Từ "oracle" ở đây theo nghĩa **nhà tiên tri** trong khoa học máy tính — thứ trả
lời đúng theo định nghĩa. Không liên quan tới oracle blockchain hay hãng Oracle.

**Hai bản làm hai việc khác nhau, không thay thế được cho nhau:**

| | **Python** `relations/` | **Rust** `zk_backend/*/shared/` |
| --- | --- | --- |
| Vai trò | **định nghĩa** quan hệ | **thi hành** quan hệ trong guest |
| Chạy ở đâu | máy thường, CPU | bên trong zkVM |
| Tốc độ | mili giây | giây tới hàng chục phút (kèm prove) |
| Sinh ra gì | dữ liệu kiểm thử, số liệu Bảng 1, artifact | **proof** |
| Ai đọc | reviewer, người viết test | guest, và reviewer đọc mã |
| Bỏ đi được không | **không** | **không** |

**Vì sao không bỏ Python được:**

1. **Nó sinh ra dữ liệu để chứng minh.** Muốn có proof thì phải có test vector,
   có checkpoint, có Merkle tree — Python sinh tất cả.
2. **Nó là mức so sánh.** Không có nó thì "guest tính đúng" so với **cái gì**?
3. **Nó bắt lỗi trong vài giây thay vì vài giờ.** Prove một fragment mất từ 1,6
   giây tới 25 phút tuỳ quan hệ. Chạy oracle Python mất mili giây. Sai lệch nào
   bắt được trên CPU thì không phải trả tiền GPU để bắt.
4. **Nó là thứ reviewer đọc.** Rust trong guest phải viết theo kiểu no-std, dựng
   chuỗi JSON bằng tay, không có thư viện. Python đọc dễ hơn nhiều.

**Vì sao không bỏ Rust được:**

1. **Python không sinh được proof.** SP1 chỉ nhận guest RISC-V; hiện thực tế là
   Rust.
2. **Chỉ thứ chạy trong guest mới được chứng minh.** Oracle Python chạy trên máy
   prover — nó **không** là bằng chứng gì cả với người ngoài. Ai cũng viết được
   một script Python in ra "đúng rồi".

**Và đây là phần quan trọng nhất: hai bản là một *cơ chế phòng thủ*, không phải
sự trùng lặp.**

Khi Python và Rust bất đồng, ta biết **có một lỗi ở đâu đó**, ngay lập tức, trên
CPU. Đây không phải lý thuyết:

> Lỗi tràn số nguyên ở mục 8.2 **chỉ bị phát hiện nhờ hai bản bất đồng.** Python
> dùng số nguyên độ chính xác tuỳ ý nên **không** gói vòng; Rust `i64` thì gói
> vòng thành số âm. Hai bên ra kết quả khác nhau, và điều đó lộ ra bug. Nếu chỉ
> có một bản, con số vô nghĩa đó đã được chứng minh thành công và không ai biết.

Repo còn có test đọc **thẳng mã nguồn Rust** để bắt trôi lệch giữa hai bên
(`tests/unit/test_canonical_payload_alignment.py`) **[đo]**.

**Cái giá phải trả, nói cho sòng phẳng:** mỗi lần đổi quan hệ phải sửa **cả
hai**, và chuỗi JSON chuẩn tắc phải khớp **đến từng byte** — guest không có bộ mã
hoá JSON nên nó dựng chuỗi bằng tay với các khoá gõ sẵn theo đúng thứ tự. Đây là
nguồn lỗi thật, và là lý do có một tầng test riêng cho nó.

---

## 6. Recursion — nối nhiều proof thành một

### 6.1 Vì sao phải nối

Một proof `training_fragment` phủ được *k* bước. Ta muốn phủ **cả lượt chạy** —
1.248 bước, 4.992 bước, lý tưởng là 50.000 bước.

**Cách ngây thơ: nhét cả 5.000 bước vào một guest.** Không khả thi, và lý do đo
được:

- Cycles tăng tuyến tính. Một lá 156 bước tốn khoảng 6 × 10⁸ cycles; 5.000 bước
  sẽ vào cỡ 2 × 10¹⁰.
- RAM tiêu thụ ≈ 27 byte/cycle **[đo]** → cỡ 540 GB. Máy 32 GB không có cửa.
- Proof lớn nhất từng chạy thành công là 1,68 tỉ cycles. 2 × 10¹⁰ vượt xa.

**Cách dùng — recursion:** viết một chương trình guest mà **việc của nó là kiểm
các proof khác**.

Vì "kiểm một proof" cũng chỉ là một phép tính, và zkVM chứng minh được mọi phép
tính, nên chương trình đó lại sinh ra một proof mới — **một proof chứng minh
rằng hai proof kia hợp lệ**.

```
              proof GỐC              ← kiểm 2 proof con bên dưới
              /       \
          proof       proof          ← mỗi cái lại kiểm 2 proof con
          /   \       /   \
        lá   lá     lá   lá          ← mỗi lá phủ 156 bước huấn luyện
```

Kết quả: **một** proof duy nhất phủ toàn bộ, và verifier chỉ kiểm đúng proof gốc
đó — **0,054 giây** **[đo]**.

### 6.2 Chi phí recursion — con số cần nhớ

Ba dòng `native_flat_recursive` của Bảng 2 **[đo]**:

| Dòng | T (bước) | Số proof con | Cycles | Cycles / proof con |
| --- | ---: | ---: | ---: | ---: |
| `native_flat_recursive_t16` | 16 | 2 | 422.726.492 | **211,4 M** |
| `native_flat_recursive_t32` | 32 | 4 | 842.015.859 | **210,5 M** |
| `native_flat_recursive_t64` | 64 | 8 | 1.683.525.837 | **210,4 M** |

(T = 16 với lá k = 8 nghĩa là 2 proof con.)

> **Khoảng 211 triệu cycles cho mỗi proof con được kiểm** — và con số này **không
> phụ thuộc** proof con phủ bao nhiêu bước huấn luyện.

Ba hệ quả, tất cả đều dùng được:

**(a) Ước được chi phí trên giấy trước khi thuê máy.** Cây `N` lá, arity 2, cần
`N − 1` lượt gộp.

**(b) Lá dài rẻ hơn lá ngắn.** Nếu mỗi lá phủ 8 bước, một lượt chạy 1.248 bước
cần 156 lá → 155 lượt gộp → ~33 tỉ cycles. Nếu mỗi lá phủ **156** bước thì chỉ
cần 8 lá → 7 lượt gộp → ~1,5 tỉ cycles. **Rẻ hơn khoảng 20 lần.** Đây chính là
lý do lá của cây whole-run là `k = 156`.

**(c) Nhưng lá không dài vô hạn được.** Lá 1.000 bước tốn khoảng 3,9 tỉ cycles —
vượt mức lớn nhất từng prove thành công (1,68 tỉ) và đụng trần RAM (~105 GB theo
27 byte/cycle). Đây là ranh giới **đo được**, không phải chỗ né tránh.

*Ghi chú lịch sử:* con số **154 triệu cycles/proof con** trong các bản trước là
số đo **trước** khi bật `overflow-checks`. Recursion là quan hệ chịu chi phí kiểm
tràn nặng nhất, **+36,8%**, và 154 × 1,368 ≈ 211 — khớp với số hiện tại.

**Một điểm dễ đọc nhầm trong Bảng 2**, cần nói rõ khi trình bày:

> Cột Cycles của dòng recursion là chi phí của **proof gốc**, không phải **tổng
> chi phí cả cây**. Bằng chứng: dòng `binary_tree_native_t1248_cartpole` phủ
> 1.248 bước với 8 lá, nhưng cycles của nó (422.415.621) gần như bằng đúng dòng
> `native_flat_recursive_t16` chỉ có 2 proof con (422.726.492). Cả hai đều là một
> nút gộp 2 con. Tổng chi phí cây phải cộng thêm 7 nút trong và 8 lá.

### 6.3 Hai chế độ gộp — và vì sao phân biệt chúng lại quan trọng

Dự án có **hai** chế độ, và nhầm chúng là hiểu sai sức mạnh của kết quả.

**Chế độ A — `proof_manifest_chain` (chuỗi hồ sơ proof)**

Guest **không** kiểm proof con. Nó chỉ:

- băm **hồ sơ** (manifest) của từng proof con,
- kiểm public input của các con **nhất quán** với nhau,
- kiểm `dataset_root` và cam kết cấu hình **giống nhau** ở mọi con,
- kiểm ranh giới chunk khớp: bước cuối của con `i` là bước đầu của con `i+1`,
- kiểm chuỗi checkpoint nối liền.

```
Phát biểu: "CÓ MỘT dãy T proof con có siêu dữ liệu nhất quán và nối
            liền nhau thành một lượt chạy."
Không nói: "và các proof con đó hợp lệ về mặt mật mã."
```

Ai đó **phải kiểm proof con ở ngoài**. Nếu bỏ qua bước đó, chế độ này không
chứng minh gì về tính đúng của việc huấn luyện.

- Rẻ: T=128 chỉ tốn **2.758.670** cycles, prove **2,5 s** **[đo]**.
- Yếu hơn: cần một giả định tin cậy bên ngoài.

**Chế độ B — `recursive_sp1` (đệ quy thật)**

Guest **thật sự chạy trình kiểm SP1 lên từng proof con, bên trong mạch**.

```
Phát biểu: "Tôi đã kiểm bằng mật mã rằng T proof con này hợp lệ, chúng
            khớp vkey của quan hệ training_fragment, và chúng nối liền
            thành một lượt chạy."
```

Không còn giả định ngoài nào. Đây mới là recursion đúng nghĩa.

- Đắt: T=64 tốn **1.683.525.837** cycles, prove **755 s** — gấp **610 lần** chế
  độ A ở cùng cỡ **[đo]**.
- **Chỉ chạy được trên GPU.** CPU cần > 61 GB RAM và không hoàn thành.

**So sánh trực tiếp ở cùng T = 32 [đo]:**

| | manifest chain | recursive |
| --- | ---: | ---: |
| Cycles | 880.030 (T=32) | 842.015.859 |
| Prove | 1,4 s | 385,9 s |
| Proof con được kiểm bằng mật mã trong guest? | **không** | **có** |

**Vì sao giữ cả hai** thay vì chỉ dùng cái mạnh: chúng đo hai thứ khác nhau. Chế
độ A đo chi phí của **logic ghép nối** (kiểm chuỗi checkpoint, ranh giới chunk).
Chế độ B đo thêm chi phí của **kiểm proof đệ quy**. Có cả hai thì tách được hai
thành phần chi phí — nếu chỉ có B, không biết bao nhiêu phần là ghép nối và bao
nhiêu là đệ quy.

**Và đây là chỗ phải nói thẳng trong paper:** claim của T ∈ {32, 64, 128} là
claim của **chế độ A**; claim của T ∈ {16, 32, 64} và cây tới 4.992 là của **chế
độ B**. Trộn hai cái là nới claim. Repo có một bộ quét tự động
(`scripts/experiments/check_paper_claims.py`) chặn đúng việc đó **[đo]**.

### 6.4 Arity — hai thứ trùng tên, đừng lẫn

Khi đọc code sẽ gặp chữ "arity" ở hai chỗ khác nghĩa hẳn **[đo]**:

| | Nghĩa | Giá trị | Đổi được không |
| --- | --- | --- | --- |
| **Arity nén nội bộ SP1** | SP1 gộp bao nhiêu shard mỗi lượt | **4**, cố định | Không. `SP1_WORKER_MAX_COMPOSE_ARITY` có tồn tại và được đọc, nhưng mọi giá trị khác 4 làm prover panic |
| **Arity cây gộp của repo** | cây gộp của dự án ghép mấy con mỗi nút | **2** | Không dễ: sáu trường `left_/right_child_*` là **public input**, đổi arity là migration schema và vô hiệu mọi provenance đã commit |

Độ **sâu** thì tự do: `leaf_chunk_count` nhận mọi luỹ thừa của 2 từ 2 trở lên.

---
## 7. Dữ liệu và kết quả

### 7.1 Dữ liệu — cái gì, vì sao, bao nhiêu

Repo có **mười** dataset đã cam kết, trong `artifacts/datasets/` **[đo]**. Chúng
phục vụ ba mục đích khác nhau — nhầm mục đích là hiểu sai bảng.

**Nhóm A — sáu dataset chính, dùng cho Bảng 1**

Tự thu thập, đã kiểm toán (`self_collected_replay_audited`):

| dataset_id | Môi trường | Chính sách | Transition | merkle_root |
| --- | --- | --- | ---: | --- |
| `cartpole-random-v2` | CartPole-v1 | random | 50.006 | `6f586441…` |
| `cartpole-medium-v2` | CartPole-v1 | medium | 50.045 | `f5002ce5…` |
| `cartpole-expert-v2` | CartPole-v1 | expert | 50.261 | `02de61a9…` |
| `lunarlander-random-v1` | LunarLander-v3 | random | 50.020 | `24eebb92…` |
| `lunarlander-medium-v1` | LunarLander-v3 | medium | 50.586 | `eb3e4f6c…` |
| `lunarlander-expert-v1` | LunarLander-v3 | expert | 50.552 | `328eb8b4…` |

**Vì sao ba mức chất lượng?** Đây là thiết kế chuẩn của benchmark offline RL
(D4RL đặt ra quy ước random / medium / expert). Lý do: **chất lượng dữ liệu là
biến số quan trọng nhất trong offline RL**, và một thuật toán có thể giỏi trên
dữ liệu chuyên gia mà vô dụng trên dữ liệu ngẫu nhiên, hoặc ngược lại. **[nền]**

- **random** — chính sách chọn hành động hoàn toàn ngẫu nhiên. Dữ liệu phủ rộng
  không gian trạng thái nhưng gần như không có hành vi tốt nào để bắt chước.
- **medium** — chính sách đã học một nửa. Có hành vi hợp lý, chưa giỏi.
- **expert** — chính sách đã huấn luyện xong, thêm nhiễu nhỏ (`policy_epsilon =
  0,02`, tức 2% số bước chọn ngẫu nhiên). Dữ liệu chất lượng cao nhưng **hẹp** —
  chỉ phủ các trạng thái mà một agent giỏi đi qua.

**Vì sao hai môi trường?** CartPole đơn giản, 4 chiều state, 2 hành động, phần
thưởng dày (mỗi bước +1). LunarLander khó hơn hẳn: 8 chiều, 4 hành động, phần
thưởng thưa và có thể **âm nặng**. Có cả hai thì phân biệt được "thuật toán hoạt
động" với "bài toán quá dễ nên cái gì cũng chạy". Kết quả xác nhận điều đó — mục
7.2 cho thấy thứ tự thắng thua **đảo ngược** giữa hai môi trường.

**Vì sao ~50.000 transition mỗi tập?** Đủ lớn để việc học có nghĩa, đủ nhỏ để cây
Merkle sâu 16 tầng và toàn bộ pipeline chạy được trong ngân sách. Con số không
tròn (50.006 chứ không phải 50.000) vì việc thu thập dừng ở **ranh giới
episode**, không cắt giữa chừng — cắt giữa episode sẽ tạo ra transition cuối
không có `done` đúng.

**Nhóm B — bốn dataset đo tỉ lệ Merkle, dùng cho Bảng 2**

| dataset | Nguồn | Số lá | Độ sâu |
| --- | --- | ---: | ---: |
| `minari-pointmaze-umaze-v2-10000` | Minari / D4RL PointMaze | 10.000 | 14 |
| `minari-pointmaze-umaze-v2-50000` | Minari / D4RL PointMaze | 50.000 | 16 |
| (dẫn xuất) | | 1.000 | 10 |
| (dẫn xuất) | | 100.000 | 17 |

Đây là dataset **công khai**, nhập từ Minari — thư viện dataset chuẩn cho offline
RL. Dùng nó thay vì dataset tự thu thập cho phần đo Merkle vì hai lý do: (a) nó
chứng minh pipeline chạy được trên dữ liệu **không phải của mình**, và (b)
PointMaze có state **liên tục** không biểu diễn được bằng số nguyên, nên nó là ca
thử cho quy tắc lá JSON ở mục 3.3.

**Nhóm C — hai dataset lịch sử, không dùng trong bảng nào**

| dataset | Vì sao còn đó |
| --- | --- |
| `cartpole-random-v1` | phiên bản đầu (986 transition), giữ lại cho provenance cũ |
| `mountaincar-random-v1` | MountainCar đã **bị loại**: DQN vanilla 200.000 bước cho **đúng −200,0 ở cả 10 checkpoint** — không lần nào chạm cờ, nên không sinh nổi cặp medium/expert phân biệt được **[đo]** |

Dòng MountainCar đáng kể lại khi bị hỏi "sao chỉ có hai môi trường": không phải
ngại, mà là **đã thử và đã đo là không dùng được**.

**Pipeline dữ liệu — bốn bước, mỗi bước để lại một hash [đo]**

```
1. COLLECT  chạy chính sách trong môi trường, ghi transition
            → raw_trajectory_hash, collection_log_final_hash
            → base_seed ghi lại để tái lập
2. AUDIT    kiểm lại: reward có khớp môi trường không, replay có nhất
            quán không, episode có đóng đúng không
            → audit_report_hash, replay_audit_passed, reward_audit_passed
3. COMMIT   dựng cây Merkle
            → merkle_root, manifest_hash
4. VERIFY   dựng lại từ dữ liệu, so root
```

Bốn hash đó **đều nằm trong public input** của quan hệ (xem mục 5.3). Nghĩa là
proof không chỉ nói "tôi huấn luyện trên dataset gốc R" mà còn "dataset R đó đã
qua báo cáo kiểm toán có hash A, sinh từ log thu thập có hash C".

Với dataset expert, `policy_hash` cam kết cả **SHA-256 của checkpoint chính sách
đã dùng để thu thập** cộng với epsilon — nên "chính sách nào tạo ra dữ liệu này"
cũng bị khoá.

### 7.2 Bảng 1 — con số hiệu năng nghĩa là gì

**Bảng 1 không nói gì về zero-knowledge.** Đây là điểm hay bị hiểu nhầm nhất.
Bảng 1 trả lời một câu hỏi khác hẳn:

> **Cấu hình mà hệ chứng minh có thể kiểm được thì học tốt tới đâu, so với cấu
> hình mà người ta thật sự dùng?**

Không có bảng này, một người phản biện sẽ hỏi: *"anh chứng minh được một quá
trình huấn luyện, nhưng quá trình đó có ra được cái gì dùng được không, hay chỉ
là phép tính chạy cho có?"*

**Cấu trúc: 54 dòng = 6 dataset × 9 cấu hình.** Chín cấu hình gồm bốn thuật toán
× hai optimizer, cộng một dòng chạy đúng cấu hình mà hệ chứng minh kiểm:

| Thuật toán | Là gì |
| --- | --- |
| **`bc`** | Behavior Cloning — **bắt chước thuần**. Học `s → a` như bài toán phân loại thường, hoàn toàn bỏ qua phần thưởng và Bellman. Đây là mức nền: nếu một thuật toán RL thua BC thì nó chưa mang lại gì |
| **`offline_dqn`** | DQN thường (mục 2.10) chạy trên dữ liệu cố định |
| **`double_dqn`** | Double DQN (mục 2.12) — thuật toán mà dự án chứng minh |
| **`cql_lite`** | Conservative Q-Learning bản rút gọn — thêm phạt để ghìm Q của hành động ngoài dữ liệu (mục 2.13) |
| **`double_dqn_provable`** | Double DQN chạy **đúng** cấu hình mà quan hệ SP1 kiểm: batch = 1, SGD, clip theo giá trị, sync = 2000 |

**Cách đọc một dòng:**

```
cartpole-random-v2 | double_dqn | sgd | 3 seed | 311.033 +/- 56.982 | 5000 bước
```

- `3 seed` — chạy lại **3 lần** với ba hạt giống ngẫu nhiên khác nhau, vì RL rất
  nhiễu; một lần chạy đơn lẻ không nói lên điều gì.
- `311,033` — **return trung bình** (mục 2.3) qua các episode đánh giá, trung
  bình tiếp qua 3 seed.
- `± 56,982` — độ lệch chuẩn giữa các seed. **Độ lệch lớn nghĩa là kết quả không
  ổn định** — và trong bảng có những dòng độ lệch còn lớn hơn giá trị trung bình
  (`double_dqn adam` trên cartpole-random: 239,967 ± **186,601**), đó là tín hiệu
  phải nói rõ chứ không phải giấu đi.
- `5000 bước` — ngân sách huấn luyện, giống nhau ở mọi dòng để so sánh công bằng.

**Thang điểm để biết con số là tốt hay tệ:**

| Môi trường | Rất tệ | Chưa học được gì | Khá | Rất tốt |
| --- | --- | --- | --- | --- |
| CartPole (trần 500) | — | **≈ 9,3** | 200–350 | 450–500 |
| LunarLander | dưới −300 | ≈ −150 tới −250 | −50 tới +50 | +200 trở lên |

Con số **9,3** trên CartPole đáng nhớ: đó là điểm của một chính sách **chưa học
gì cả** — gậy đổ sau 9 bước. Trong bảng có rất nhiều dòng ở mức 9,3–9,8, và
chúng đều nghĩa là **thất bại hoàn toàn**, không phải "hơi kém".

**Ba điều bảng này nói ra [đo]:**

**(1) Offline DQN sập trên dữ liệu chất lượng cao.** Nghịch lý, nhưng đây là hiện
tượng đã biết trong offline RL:

| Dataset | `double_dqn` (sgd) | `bc` (sgd) |
| --- | ---: | ---: |
| cartpole-random | **311,0** | 35,6 |
| cartpole-medium | 9,8 | 341,8 |
| cartpole-expert | 9,6 | **492,2** |

Trên dữ liệu **ngẫu nhiên**, DQN thắng BC gấp 9 lần — vì BC bắt chước một chính
sách ngẫu nhiên thì cũng chỉ ra ngẫu nhiên, còn DQN **suy luận** ra hành vi tốt
từ phần thưởng. Trên dữ liệu **chuyên gia**, DQN sập về 9,6 còn BC đạt 492,2 —
dữ liệu expert hẹp, không phủ các trạng thái mà Q-learning cần để suy luận, nên
extrapolation error (mục 2.13) giết nó.

**(2) Adam không phải luôn thắng SGD.** Đếm trên 24 cặp so được:

```
Toàn bộ:      Adam 13  –  SGD 11        ← gần như hoà
CartPole:     Adam  2  –  SGD 10        ← SGD áp đảo
LunarLander:  Adam 11  –  SGD  1        ← Adam áp đảo
```

Kết quả **đảo ngược hoàn toàn** giữa hai môi trường. Đây là số liệu quan trọng
cho paper: nó nói rằng **việc hệ chứng minh chỉ hỗ trợ SGD (mục 2.15) không phải
một khiếm khuyết mang tính hệ thống** — trên cả một môi trường, SGD còn tốt hơn.

Và nó nhắc một điều về phương pháp: nếu chỉ chạy CartPole, ta sẽ kết luận "SGD
tốt hơn Adam" và sai. Nếu chỉ chạy LunarLander, kết luận ngược lại và cũng sai.

**(3) Kết quả trung tâm — cấu hình chứng minh được so với cấu hình tinh chỉnh:**

| Dataset | Cấu hình chứng minh được | Tinh chỉnh (batch 256) | Chênh |
| --- | ---: | ---: | --- |
| cartpole-random | 17,0 | **311,0** | thua nhiều |
| cartpole-medium | 11,0 | 9,8 | ngang (cả hai đều hỏng) |
| cartpole-expert | 9,7 | 9,6 | ngang (cả hai đều hỏng) |
| lunarlander-random | **−152,7** | −215,3 | **thắng** |
| lunarlander-medium | −829,7 | −366,6 | thua nhiều |
| lunarlander-expert | −717,9 | −518,7 | thua |

Đọc trung thực: **khoảng cách là thật và có chỗ rất lớn**, nhưng **không phải
luôn theo một chiều** — trên `lunarlander-random`, cấu hình chứng minh được
**vượt** cấu hình tinh chỉnh. Đó là kết quả đáng nói và đáng bảo vệ, không phải
đáng khoe: nó cho thấy khoảng cách phụ thuộc bài toán, chứ không phải một hằng
số "chứng minh được thì kém hơn X%".

Vì sao có khoảng cách, và nó gồm những thành phần nào — mục 7.4.

### 7.3 Bảng 2 — chi phí chứng minh, và vì sao CPU lẫn GPU

**Bảng 2 có 32 dòng, trong đó 25 dòng có proof thật [đo].** Bảy dòng còn lại ghi
rõ là **không** có proof:

| Trạng thái | Số dòng | Nghĩa |
| --- | ---: | --- |
| `proof_verified` | 25 | đã prove **và** đã verify thành công |
| `execute_only` | 3 | `training_fragment` k = 16/32/128: chỉ chạy mô phỏng, không prove |
| `not_supported_current_backend` | 4 | `training_update` batch 4/8/16 và mạng `small`: backend chưa hỗ trợ |

Giữ bảy dòng đó trong bảng là **cố ý**: chúng đánh dấu ranh giới của công trình.
Bỏ đi thì bảng trông tròn trịa hơn nhưng che mất chỗ hệ thống chưa với tới.

**Cách chạy ra Bảng 2 — chi tiết [đo]**

Quy trình gồm bốn tầng, và biết cấu trúc này thì trả lời được câu "làm sao tái
lập":

```
① Sinh test vector          (Python, CPU, mili giây)
   scripts/experiments/export_training_fragment_vector.py và các script phase
   → zk_backend/test_vectors/<tên>_case_0.json
   Mỗi vector gồm { schema_version, public_inputs, private_witness }

② Prove từng quan hệ        (Rust + SP1, nặng)
   RUN_SP1_PROVE=1 cargo run --release -p <host> -- --prove
   Host làm ba việc:
     a. precheck  — gọi verifier trong shared/ để kiểm vector TRƯỚC khi prove,
                    vì prove một vector sai là đốt tiền GPU vô ích
     b. prove     — nạp vector, chạy guest, sinh proof
     c. verify    — kiểm lại proof vừa sinh, ghi proof_verified
   → artifacts/reports/provenance/sp1/<case>/metrics.json

③ Quét giả mạo              (cùng lượt, xem mục 7.5)
   → .../tamper_report.json

④ Gom thành bảng            (Python)
   scripts/experiments/run_phase8_2_proof_benchmark.py --paper
   → artifacts/reports/final_ndss/table2_zk_proof_cost.csv
   zk_offline_dqn/experiments/paper_tables.py
   → paper/generated/table2_proof_cost.tex   (paper \input thẳng tệp này)
```

Mỗi `metrics.json` ghi 17 trường, và bốn trường trong đó là **mỏ neo truy vết**:

```
cycle_count          5193244
prove_time_seconds   3.810088194
verify_time_seconds  0.129283375
proof_size_bytes     2841071
prover               cuda
test_vector_sha256   f2656757…   ← đầu vào nào
guest_elf_sha256     ff2c14b1…   ← chương trình nào
public_inputs_sha256 0846d55b…   ← phát biểu gì
sp1_version          6.1.0
```

**Vì sao dòng thì CPU dòng thì GPU — câu hỏi bạn nêu**

Đếm ra: **15 dòng chạy CUDA, 10 dòng chạy CPU** **[đo]**. Trông như thiếu nhất
quán. Lý do là một sự thật kỹ thuật, không phải lựa chọn:

> **Chỉ hai trong tám host có nhánh CUDA:** `training_fragment` và
> `training_aggregation`. Sáu host còn lại — `td_mvp`, `merkle_membership`,
> `forward_td_mlp`, `one_step_sgd_tiny`, `short_trace`, `training_update` — **không
> có feature `cuda` nào trong mã nguồn**, và ghi thẳng `"prover": "cpu"` vào
> metrics.

Nên đây không phải "chọn chạy CPU cho vài dòng". Sáu host kia **không chạy GPU
được**, chấm hết. Muốn đồng bộ hoá thì phải viết thêm nhánh CUDA cho sáu
workspace Rust — một việc kỹ thuật thật, nằm ngoài phạm vi.

**Vì sao chuyện này quan trọng chứ không phải tiểu tiết:** nhìn cột Prove sẽ thấy
`merkle_membership` **50,2 s** trong khi `training_fragment_k8` chỉ **3,8 s** —
dù Merkle chỉ tốn 116.750 cycles còn fragment tốn 5.193.244 cycles, tức **gấp 44
lần công việc**. Nếu không biết cột Prover, con số này đọc ra kết luận sai hoàn
toàn. **Cột `Prover` trong bảng tồn tại chính để chặn việc đọc sai đó.**

**Và đây là một cái bẫy đã cắn thật, đáng kể lại [đo]:** biến `SP1_CUDA` **im
lặng theo cả hai chiều**.

- Host **không** có feature: biến bị bỏ qua, chạy CPU, GPU đứng im 0%. Đã mất
  ~6 phút mỗi lá cho 16 proof lá trong khi A10G không làm gì.
- Host **có** feature: biến đổi phần cứng của phép đo mà **output không ghi lại
  chuyện đó**. Ba dòng manifest chain từng rơi từ 32,5 / 39,2 / 47,8 s xuống
  1,4 / 1,7 / 2,4 s — nhanh 20 lần, nhưng **không phải vì quan hệ nhanh lên**, mà
  vì số cũ đo trên CPU. Ghi thẳng vào bảng là trộn hai loại phần cứng trong một
  cột.

Chiều thứ hai nguy hiểm hơn, vì kết quả trông hoàn toàn hợp lệ. Quy tắc rút ra:
**`nvidia-smi` là thứ nói thật, không phải biến môi trường.**

**Toàn bộ 25 dòng được sinh trong MỘT lượt chạy, trên MỘT máy g5.2xlarge.** Đó là
lý do lần này cột thời gian **so sánh được với nhau** — điều mà các bảng trước
không làm được vì số liệu đến từ nhiều máy, nhiều thời điểm.

**Đọc bảng — các dòng đáng chú ý [đo]:**

| Quan hệ | Cycles | Prove | Verify | Prover |
| --- | ---: | ---: | ---: | --- |
| Merkle (canonical) | 116.750 | 50,2 s | 0,123 s | cpu |
| Fragment k=1 | 979.945 | 1,6 s | 0,127 s | cuda |
| Fragment k=8 | 5.193.244 | 3,8 s | 0,129 s | cuda |
| Fragment, dữ liệu LunarLander | 6.746.304 | 4,6 s | 0,197 s | cuda |
| Agg. chain T=128 | 2.758.670 | 2,5 s | 0,126 s | cuda |
| Recursive T=64 | 1.683.525.837 | 755,2 s | **0,054 s** | cuda |
| Whole run, CartPole | 422.415.621 | 199,7 s | **0,054 s** | cuda |
| Groth16 child T=16 | 6.180.861.737 | 1.596,9 s | 68,0 s | cuda |

Dải cycles trải **từ 116.750 tới 6.180.861.737 — gấp 52.941 lần** — mà cột verify
gần như không nhúc nhích, thậm chí các dòng recursion còn **verify nhanh hơn**
(0,054 s so với 0,12 s) vì proof đệ quy đã được nén.

Đó là minh hoạ trực tiếp và bằng số cho tính bất đối xứng ở mục 1.4. Nếu chỉ nhớ
một điều từ Bảng 2 thì nhớ điều này.

### 7.4 Cấu hình chứng minh được — khoảng cách được **đo**, không phỏng đoán

Quan hệ SP1 kiểm một thủ tục **đơn giản hơn** thứ một cài đặt tinh chỉnh chạy:

| | Bảng 1 tinh chỉnh | Quan hệ chứng minh | Vì sao phải đổi |
| --- | --- | --- | --- |
| batch size | 256 | **1** | quan hệ hiện chỉ hỗ trợ 1; cycles nhân theo batch |
| optimizer | Adam hoặc SGD | **SGD thuần** | mục 2.15 — lr không biểu diễn được, cần sqrt, cần trạng thái |
| cắt gradient | chuẩn L2 | **theo từng thành phần** | chuẩn L2 cần sqrt |
| số học | float32 | **fixed-point i64** | mục 3.5 |
| sync target | 100 | **2000** | tự do — là public input, đổi không tốn gì |

Thay vì để người đọc tự đoán khoảng cách, dự án **đo nó** bằng một đối chứng đổi
**từng thứ một**, trên `cartpole-random`, 5.000 bước, 1 seed **[đo]**:

```
tinh chỉnh (batch 256, sync 100, clip chuẩn L2)     78,0
  chỉ đổi sang clip theo thành phần                 75,4    ← −3,3%
  chỉ đổi sync 100 → 4                               9,4    ← sập
  chỉ đổi batch 256 → 1                              9,4    ← sập
  cả ba (cấu hình quan hệ)                           9,4
```

**Đọc bảng này:** phép thay clipping — thứ **duy nhất** mà việc chứng minh **bắt
buộc** phải làm — chỉ tốn 3,3%. Hai thứ kia mỗi cái độc lập kéo về 9,4, tức mức
chính sách chưa học.

**Nhưng kết luận đó khái quát quá vội, và đây là phần đáng kể nhất về mặt phương
pháp.**

Đối chứng trên đo `batch = 1` tại **một** giá trị sync duy nhất rồi kết luận cho
mọi sync. Một đối chứng thứ hai quét **60 ô** ở batch = 1 (2 seed, nhiều giá trị
sync × learning rate × dataset) cho kết quả ngược **[đo]**:

| Môi trường | sync = 4 | sync = 2000 |
| --- | ---: | ---: |
| cartpole-random | 9,6 | **209,5** |
| lunarlander-random | −649,1 | **−197,4** |

**`batch = 1` không hề chết. Nó chết ở `sync = 100`, và sống rất tốt ở `sync =
2000`.** Xác nhận lại ở 3 seed trên cả sáu dataset, đúng ngân sách 5.000 bước của
Bảng 1, cho ra các con số đã công bố ở mục 7.2 — **cải thiện ở cả sáu**, và
`lunarlander-random` đạt **−152,7**, vượt cấu hình tinh chỉnh.

**Vì sao `sync = 2000` cứu được `batch = 1`** — giải thích, và nó khớp với mục
2.11 và 2.17:

Với batch = 1, mỗi bước cập nhật rất nhiễu. Nếu target network làm mới liên tục
(sync nhỏ), nhiễu đó lập tức chảy vào nhãn, rồi nhãn nhiễu sinh cập nhật nhiễu
hơn — đúng vòng xoáy deadly triad. Với sync = 2000, nhãn **đứng yên** trong 2.000
bước, nên nhiễu của từng bước riêng lẻ được trung bình hoá tự nhiên qua thời
gian, thay vì được khuếch đại.

Nói cách khác: **sync dài đóng vai của batch lớn, nhưng theo trục thời gian thay
vì trục dữ liệu.**

Đo kèm cho thấy nó cũng chữa luôn phân kỳ: Q đỉnh còn **1,01 × 10⁵** so với biên
`4,50 × 10¹⁵` **[đo]** — thay vì `4,14 × 10¹⁶` ở mục 2.17.

**Ba bài học rút ra, và cả ba đều đáng nói trước thầy:**

1. **"X độc lập gây chết" cần một lưới quét, không phải một điểm đo.** Đây là lỗi
   phương pháp mà dự án tự mắc rồi tự sửa, và nó nằm trong paper.

2. **Thứ đắt hoá ra không phải nguyên nhân.** `batch_size` bị ràng buộc cứng và
   nhân cycles theo batch — sửa nó là việc lớn. `target_sync_interval` vốn đã là
   một public input **tự do**: đổi nó **không tốn gì**, không thêm một cycle nào.
   Nếu dừng lại ở đối chứng thứ nhất, dự án sẽ đi làm việc đắt và vô ích.

3. **Lộ trình kế tiếp của quan hệ là batching và sync dài hơn, không phải Adam.**
   Điều này **trái** với thứ tự mà mục Limitations ban đầu gợi ý, và đã được sửa
   trong paper theo đúng số đo.

### 7.5 Bảng 3 — kháng giả mạo: thử như thế nào, và làm sao biết bị từ chối

Đây là câu hỏi bạn nêu, và cơ chế thì đơn giản hơn cái tên của nó.

**Ý tưởng: bài kiểm ngược.** Bảng 2 chứng minh hệ **chấp nhận** thứ đúng. Bảng 3
chứng minh hệ **từ chối** thứ sai. Cả hai đều cần — một hệ chấp nhận mọi thứ cũng
sẽ chấp nhận đúng thứ đúng, và như thế thì vô dụng.

**Quy trình một phép thử, bốn bước:**

```
① Lấy một artifact HỢP LỆ đã có
     zk_backend/test_vectors/training_fragment_k8_case_0.json

② Sửa ĐÚNG MỘT trường, giữ nguyên mọi thứ khác
     ví dụ  reward:  1000  →  1001
     (mỗi loại giả mạo là một hàm make_tamper_* trong
      scripts/experiments/run_*_negative_tests.py)

③ Đưa bản đã sửa qua các tầng kiểm, theo thứ tự
     a. oracle Python   → nó có chấp nhận không?
     b. guest Rust      → chạy execute, nó có panic không?
     c. ràng buộc public input → hash có còn khớp không?

④ Ghi lại: tầng nào từ chối, lớp lỗi gì, thông điệp gì
     → artifacts/reports/provenance/sp1/<case>/tamper_report.json
```

**"Làm sao biết nó bị từ chối" — cụ thể, hệ thấy gì [đo].** Một mục thật trong
`tamper_report.json` của `training_fragment_k8`:

```json
{
  "case": "tamper_minibatch_index",
  "reference_accepted": false,
  "reference_reason": "deterministic sample index mismatch",
  "execute_passed": false,
  "execute_return_code": 101,
  "passed": true
}
```

Đọc bốn trường:

| Trường | Nghĩa |
| --- | --- |
| `reference_accepted: false` | **oracle Python từ chối** — và nó nói **vì sao**: chỉ số mẫu không khớp giá trị dẫn xuất |
| `execute_passed: false` | **guest Rust cũng từ chối** |
| `execute_return_code: 101` | 101 là mã thoát của một **panic Rust** — guest chạy tới `assert!` rồi dừng hẳn |
| `passed: true` | **phép thử thành công** — nghĩa là "hệ đã từ chối đúng như mong đợi" |

Chú ý chỗ dễ nhầm: `passed: true` **không** nghĩa là bản giả mạo qua được. Nó
nghĩa là **bài kiểm** qua được, tức hệ đã bắt được. Một `passed: false` mới là
tin xấu — bản giả mạo lọt lưới.

Và điểm quan trọng nhất: **giả mạo không bao giờ tới được bước prove.** Guest
panic ngay khi execute. Nghĩa là **không có proof nào được sinh ra cho một phát
biểu sai** — không phải "sinh proof rồi verify từ chối", mà là **không sinh
được**.

**Kết quả tổng: 236 phép thử, 233 bị từ chối đúng, 3 không áp dụng [đo].**

Ba dòng `not_applicable` — và cả ba đều có lý do chính đáng, không phải lỗi:

| Phép thử | Vì sao không áp dụng |
| --- | --- |
| `tamper_proof_bytes_if_available` | `proof.bin` **cố ý không commit** (dung lượng lớn), nên không có gì để sửa |
| `tamper_receipt_if_available` | receipt cũng bị xoá theo cùng chính sách |
| `tamper_public_collection_log_final_hash_absent` | dataset công khai nhập từ Minari **không có** trường log thu thập để sửa |

**Phủ bao nhiêu: 19 nhóm tấn công trên 20 thành phần [đo].** Bảy nhóm lớn nhất:

| Nhóm | Số phép thử | Sửa cái gì |
| --- | ---: | --- |
| `proof_public_input` | 59 | ràng buộc giữa proof và phát biểu công khai |
| `minibatch_index` | 43 | chỉ số mẫu — **nghĩa vụ 3** ở mục 5.4 |
| `checkpoint_hash` | 30 | chuỗi mô hình — cắt hoặc nối sai |
| `merkle_path` | 17 | đường chứng minh thành viên |
| `dataset_root` | 14 | đổi dataset đang nói tới |
| `manifest_hash` | 13 | siêu dữ liệu / cấu hình |
| `target_network_sync` | 11 | lịch đồng bộ — **nghĩa vụ 2** ở mục 5.4 |

Còn lại: `gradient` 7, `action` 6, `done` 6, `reward` 6, `q_value` 5,
`next_state` 5, `td_target` 4, `merkle_leaf` 4,
`collection_log_final_hash` 2, `raw_trajectory_hash` 2, `loss` 1,
`audit_report_hash` 1.

Đối chiếu với **bốn cách gian lận ở mục 1.2**: sửa phần thưởng → nhóm `reward`;
đổi cờ kết thúc → nhóm `done`; thay giá trị mục tiêu → nhóm `td_target`; sửa
gradient → nhóm `gradient`. **Cả bốn đều có phép thử riêng và đều bị chặn.** Đây
chính là cách nối Bảng 3 ngược về câu chuyện mở đầu khi trình bày.

**Tầng nào bắt được — con số nói lên cấu trúc phòng thủ [đo]:**

| Tầng từ chối | Số ca | Nghĩa |
| --- | ---: | --- |
| `python_semantic_oracle` | 103 | oracle Python bắt, trước cả khi đụng Rust |
| `rust_execute` | 62 | **guest panic khi chạy** — proof không sinh được |
| `public_input_binding` | 57 | hash public input không khớp |
| `dataset_commitment_verify` | 7 | gốc Merkle không dựng lại được |
| `dataset_audit` | 4 | báo cáo kiểm toán dữ liệu bắt |
| không áp dụng | 3 | ba ca ở trên |

Điều đáng nói: **kỳ vọng ban đầu là 165 ca sẽ bị oracle Python bắt, thực tế chỉ
103 — 62 ca bị guest Rust bắt trước.** Đây là kết quả **mạnh hơn** dự kiến: bắt
ở tầng Rust nghĩa là chính mạch chứng minh từ chối, không phải một script kiểm
tra bên ngoài từ chối.

**Giới hạn phải nói thẳng khi trình bày, đừng để người phản biện phải chỉ ra:**

> Bảng 3 kiểm giả mạo **theo từng trường**. Nó **không** phủ được lỗi **ngữ
> nghĩa** — trường hợp mà **không trường nào bị sửa**, mọi hash đều khớp, mọi
> proof đều hợp lệ, nhưng quan hệ đang chứng minh **sai thứ**.

Và đó không phải giả định — mục 8.1 là đúng một ca như vậy, và cả 236 phép thử
đều xanh trong lúc lỗi tồn tại.

### 7.6 Lượt chạy trọn vẹn dưới một proof

Kết quả mạnh nhất của dự án **[đo]**:

| Môi trường | Bước | Số lá | Cycles (proof gốc) | Prove | Verify |
| --- | --- | ---: | ---: | ---: | ---: |
| CartPole expert | 0 → 1.248 | 8 × 156 | 422.415.621 | 199,7 s | 0,054 s |
| LunarLander expert | 0 → 1.248 | 8 × 156 | 422.396.109 | 198,1 s | 0,054 s |
| LunarLander random | **0 → 4.992** | 32 × 156 | 422.386.830 | 188,8 s | 0,054 s |

**Ý nghĩa:** một proof duy nhất, kiểm trong **54 mili giây**, chứng minh rằng một
lượt huấn luyện 1.248 (hoặc 4.992) bước đã chạy đúng — đúng dữ liệu đã cam kết,
đúng siêu tham số đã công bố, đúng lịch sync, đúng chuỗi checkpoint.

Chú ý cycles của cả ba **gần như bằng nhau** dù số bước chênh 4 lần. Đó là hệ quả
của mục 6.2: cột này là chi phí **proof gốc**, và proof gốc luôn chỉ kiểm 2 proof
con, bất kể cây sâu bao nhiêu.

**Dòng cuối là dòng đáng giá nhất, và lý do rất cụ thể:** nó phủ **đúng lượt chạy
sinh ra con số −152,7 trong Bảng 1**, chứ không phải một lượt chạy minh hoạ nào
khác. Đây là chỗ Bảng 1 và Bảng 2 chạm vào nhau: cùng một lượt huấn luyện, vừa
được **đo hiệu năng** vừa được **chứng minh**.

Nó **chưa** nằm trong Bảng 2 vì một lý do kỹ thuật — mục 8.4.

---

## 8. Bốn lỗi đã tìm ra, và vì sao chúng đáng kể

Phần này quan trọng ngang phần kết quả, và khi trình bày nên nói **trước** khi bị
hỏi. Cả bốn lỗi cùng một hình dạng:

> **Hệ thống báo xanh trong khi thứ nó kiểm không phải thứ ta tưởng.**

Đó chính là chế độ hỏng nguy hiểm nhất của một hệ chứng minh — không phải hỏng
ầm ĩ, mà hỏng lặng lẽ trong khi mọi đèn đều xanh.

### 8.1 Mọi chunk lấy mẫu trùng nhau — lỗi nghiêm trọng nhất

**Triệu chứng:** không có triệu chứng nào. Mọi thứ xanh.

**Nguyên nhân:** `sampler_seed` là một **hằng số**, và `step_id` đếm **trong nội
bộ mỗi fragment** (0, 1, 2, ... rồi lại 0 ở fragment sau). Vì chỉ số mẫu được
tính từ `(seed, step_id)`, mọi chunk của một chuỗi rút **đúng cùng một tập chỉ
số**.

Đo trực tiếp, chunk 0 (bước 0–7) và chunk 1 (bước 8–15) **[đo]**:

```
chunk 0 → [68, 83, 22, 125, 56, 55, 42, 1]
chunk 1 → [68, 83, 22, 125, 56, 55, 42, 1]      ← giống hệt
```

**Hệ quả:** cái gọi là "lượt chạy 1.248 bước" thực chất là **156 lần lặp trên
đúng 8 dòng** của một dataset 50.000 dòng. Nó không phải một lượt quét dữ liệu.
Claim "huấn luyện trên dataset đã cam kết" bị **rỗng ruột** — về mặt kỹ thuật vẫn
đúng (8 dòng đó *có* nằm trong dataset), nhưng về mặt ý nghĩa thì vô giá trị.

**Vì sao không lớp nào bắt được** — và đây là phần đáng suy nghĩ nhất:

- Mọi hash đều khớp — vì không hash nào sai.
- Mọi proof đều verify được — vì phép tính thật sự đã chạy đúng.
- **Cả 236 phép thử giả mạo đều xanh** — vì **không trường nào bị sửa**.

Đây là lỗi **ngữ nghĩa của quan hệ**: quan hệ chứng minh chính xác điều nó nói,
nhưng điều nó nói không phải điều ta muốn nó nói. Loại lỗi này benchmark tamper
theo trường **về nguyên tắc không phủ được**.

**Cách sửa:**

```
sampler_seed = SHA256("training_fragment_sampler_seed_v1",
                      dataset_root, global_step_start)
```

Một thay đổi đóng **hai** lỗ cùng lúc:

1. `global_step_start` khác nhau giữa các chunk → các chunk **buộc phải** rút
   khác nhau.
2. Seed dẫn xuất từ `dataset_root` → prover **hết đường** tự chọn seed để lọc mẫu
   có lợi (nghĩa vụ 3, mục 5.4; và đây đúng là lớp tấn công mà Tan và cộng sự,
   2025, cảnh báo).

Kèm một test hồi quy: `test_chunks_of_one_chain_draw_different_transitions`.

**Bài học phương pháp, đáng nói trước thầy:** một bộ benchmark tamper 236 ca
xanh 100% **không chứng minh quan hệ đúng**. Nó chỉ chứng minh quan hệ nhạy với
việc **sửa trường**. Muốn bắt lỗi ngữ nghĩa thì phải có phép kiểm hỏi câu khác:
*"hai chunk khác nhau có thật sự đọc dữ liệu khác nhau không?"*

### 8.2 Guest tràn số nguyên trong im lặng

**Nguyên nhân:** phép nhân fixed-point `(a × b) // 1000` chạy trên `i64`. Khi
offline DQN phân kỳ (mục 2.17), Q tăng theo hàm mũ, và `990 × q` vượt `i64::MAX`
ở khoảng `9,32 × 10¹⁵`. Kết quả **gói vòng** thành số âm — và guest vẫn chứng
minh nó bình thường.

**Vì sao điểm này nguy hiểm hơn một bug thường:** một prover sinh nhân chứng bằng
**cùng ngữ nghĩa `i64`** sẽ khiến `assert_eq!` trong guest **qua được**. Proof
hợp lệ, trên một phép tính vô nghĩa. Không có gì trong hệ báo động.

Dự án chỉ phát hiện được **tình cờ**: Python dùng số nguyên độ chính xác tuỳ ý
nên **không** gói vòng, hai bản bất đồng, và điều đó lộ ra bug (mục 5.5).

**Cách sửa — hai nửa, và nửa thứ hai là cái bẫy:**

*Nửa 1:* bật `overflow-checks = true` để guest **dừng hẳn** khi tràn thay vì gói
vòng lặng lẽ.

*Nửa 2 — chỗ đặt:* tài liệu bảo mật của SP1 bảo đặt trong `Cargo.toml` của
**guest package**. Đúng với template độc lập. Nhưng ở repo này guest là **member
của workspace**, nên Cargo **bỏ qua** kèm một cảnh báo dễ trôi qua mắt:

```
profiles for the non root package will be ignored
```

Tức là **im lặng vô hiệu**: bạn tưởng đã bật, thực ra chưa. Phải đặt ở **gốc
workspace** `zk_backend/<quan hệ>/sp1/Cargo.toml`. Repo có
`tests/unit/test_guest_overflow_checks.py` khoá **cả hai nửa** **[đo]**.

*Nửa 3 — biên tường minh:* ngoài việc dừng khi tràn, quan hệ nay còn kiểm
`|q| ≤ q_abs_max_fp = 2⁵² ≈ 4,50 × 10¹⁵` **trước** khi thực hiện phép nhân
`γ · q`. Thứ tự đó quan trọng: kiểm **sau** phép nhân thì phép nhân đã tràn rồi.
(Bản đầu tiên của bản vá đặt sai thứ tự, và đã được sửa.)

**Chi phí đo được — và nó KHÔNG đồng đều, đừng trích một con số cho cả bảng
[đo]:**

| Nhóm quan hệ | Tăng cycles | Vì sao |
| --- | ---: | --- |
| fragment, update | +3,6…7,2% | số học fixed-point chỉ là phần nhỏ |
| merkle | +13,0…17,7% | rất nhiều phép cộng chỉ số |
| recursion, cây nhị phân | **+36,8%** | kiểm proof con là phần nặng số học nhất |
| groth16 | +0,33% | cycles do phép toán BN254 chi phối, không phải số học fixed-point |

**Tổng Bảng 2: 8,66 G → 9,58 G cycles, +10,7%.**

Đây là lý do các con số lịch sử trong tài liệu này (23.571 cycles/tầng Merkle,
154 M cycles/proof con) không khớp Bảng 2 hiện tại — chúng là số **trước** khi
bật kiểm tràn.

### 8.3 Số trong paper chưa bao giờ nối với pipeline

**Nguyên nhân:** pipeline **có** sinh bảng LaTeX từ dữ liệu, nhưng paper **không
dùng chúng** — bảng trong paper được gõ tay. Không có gì nối hai bên, nên chúng
trôi xa nhau, có chỗ tới **116 lần**:

| Dòng | Paper ghi | Thực tế | Lệch |
| --- | ---: | ---: | ---: |
| `training_fragment_k8` prove | 440,6 s | **3,8 s** | 116× |
| `td_mvp` prove | 167,7 s | 60,5 s | 2,8× |
| cartpole-random Double DQN | 192,9 | 311,0 | — |

Ngoài ra có **hai claim sai hẳn**, không phải chỉ lệch số: kết quả Adam–SGD ghi
là "hoà 12–12" trong khi đếm thật là **13–11**, và một tuyên bố về thời gian
verify đã cũ.

**Vì sao cổng kiểm không bắt:** repo **có** một cổng
`check_paper_claims.py`, và nó vẫn xanh suốt — vì nó kiểm **câu chữ** (có nới
claim không, có nói "full DQN training" không) chứ **không kiểm số**.

**Cách sửa:** cả ba bảng nay được **sinh** vào `paper/generated/` và paper
`\input` thẳng tệp sinh ra, cộng thêm một tầng test mới
(`tests/unit/test_paper_numbers_match_artifacts.py`) ghim 28 con số, từ chối các
giá trị đã bị rút (`440.6`, `2.84`, …) theo mặt chữ, và chặn cả ký tự TAB lọt vào
mục paper đang dùng **[đo]**.

Chi tiết cuối nghe kỳ nhưng có thật: một lỗi công cụ từng biến `\texttt` thành
ký tự TAB, LaTeX **biên dịch sạch, không báo lỗi**, và PDF in ra chữ
`exttt{lunarlander-random}`. Loại lỗi không làm build đỏ thì phải có phép kiểm
riêng.

### 8.4 Hash guest ELF định danh **lần build**, không phải mã nguồn

**Bối cảnh:** mỗi dòng Bảng 2 ghi `guest_elf_sha256` để chứng minh nó đến từ đúng
phiên bản guest nào.

**Vấn đề:** cùng một mã nguồn, build ở `~/repo8` và ở `~/repo9`, cho **hai hash
khác nhau** — vì một đường dẫn tuyệt đối lọt vào tệp nhị phân **[đo]**.

```
~/repo8  →  b1e7a69d…
~/repo9  →  1e2a8a38…      ← cùng nguồn, khác đường dẫn build
```

Điều này lộ ra khi proof 4.992 bước trở về với hash khác 10 dòng anh em, dù
**không một dòng mã guest nào thay đổi** giữa hai lần build. **Cổng kiểm tra đã
chặn đúng** — nó làm đúng việc của nó, chỉ là lý do khác với ta tưởng.

**Trạng thái hiện tại, nói chính xác [đo]:**

- Đã thêm `--remap-path-prefix` qua API mà `sp1_build` thật sự đọc
  (`BuildArgs.rustflags`).
- Đo được là **có tác dụng**: `strings` trên ELF cho `/zk_offline_dqn` **1 lần**
  và `/home/ubuntu/alpha` **0 lần**, ngược hẳn trước khi sửa.
- **Nhưng hai hash vẫn lệch**, trong khi mọi chuỗi đường dẫn còn lại giống hệt
  nhau.
- **[chưa kiểm]** Giả thuyết: chính cờ remap khác nhau giữa hai lượt build, và
  cargo băm cờ vào metadata. Đường mà `sp1_build` quảng cáo cho việc này là
  `BuildArgs { docker: true }` — **chưa thử**.

**Hệ quả phải nhớ, và đây là cách phát biểu đúng:**

> Cổng kiểm ELF **vẫn đúng mục đích** — nó bắt được việc "chỉ prove lại một
> nửa", vì trong cùng một lượt chạy thì cùng đường dẫn. Nhưng **không được** dùng
> hash ELF công bố làm **mỏ neo tái lập** cho reviewer build từ một bản clone
> sạch. Hai việc đó khác nhau, và paper phải nói đúng việc thứ nhất.

Một cái bẫy phụ đã cắn trong lúc gỡ chuyện này: `sp1_build` **chỉ dựng lại guest
khi nguồn guest đổi**. Sửa `build.rs` của host rồi so ELF ngay là **đọc lại
binary cache của lượt trước** — và cho một kết luận sai. Muốn so thì phải xoá
`guest/elf/` trong cây nguồn, không chỉ xoá `CARGO_TARGET_DIR`.

---
# KHỐI D — TRÌNH BÀY

## 9. Bản đồ paper — mỗi mục là gì, làm gì, và nói thế nào

Paper có 13 mục nội dung cộng phụ lục. Bảng dưới đi theo đúng thứ tự trong
`paper/main.tex`. Cột cuối là **một câu bạn có thể nói ra miệng** khi được hỏi
"mục này để làm gì?".

### 9.1 Bảng tra nhanh

| # | Mục | Việc của nó | Nói một câu |
| --- | --- | --- | --- |
| 1 | `abstract` | tóm tắt toàn bài trong ~200 từ | "Chúng tôi chứng minh được một lượt huấn luyện offline DQN, và đo giá của việc đó." |
| 2 | `introduction` | đặt vấn đề, nêu đóng góp | "Vì sao bài toán tồn tại, và bốn thứ chúng tôi làm mà chưa ai làm." |
| 3 | `background` | nền RL + ZKP + Merkle + SP1 + fixed-point | "Từ vựng tối thiểu để đọc phần sau." |
| 4 | `threat_model` | ai là kẻ tấn công, tấn công được gì | "Chúng tôi chống ai, và cố ý **không** chống ai." |
| 5 | `system_overview` | bảy giai đoạn của hệ | "Bản đồ đường đi từ dữ liệu thô tới proof gốc." |
| 6 | `relations` | định nghĩa hình thức từng quan hệ | "Chính xác thì chúng tôi chứng minh **cái gì**." |
| 7 | `formal_statements` | 10 định lý + chứng minh phác | "Mỗi phát biểu là một định lý, và mỗi định lý trỏ tới một artifact." |
| 8 | `proof_backend` | SP1 host/guest/shared, ràng buộc public input | "Chúng tôi **cài đặt** nó ra sao." |
| 9 | `training_fragment` | thuật toán fragment và chuỗi chunk | "Quan hệ trung tâm, viết thành mã giả." |
| 10 | `results` | ba bảng, whole-run, chi phí cấu hình, lỗi ngữ nghĩa | "Số đo." |
| 11 | `discussion` | kiểm được gì / **không** claim gì / khả năng mở rộng | "Ranh giới của công trình, tự nói ra trước." |
| 12 | `related_work` | so với Kaizen, zkPoT, VeriDP, khảo sát ZKML | "Chúng tôi đứng ở đâu trên bản đồ." |
| 13 | `conclusion` | tóm tắt + hướng tiếp | "Cái gì xong, cái gì chưa." |
| A | `appendix` | tệp artifact, lệnh tái lập, định nghĩa tamper, bảng định lý–artifact | "Cách chạy lại." |

### 9.2 Từng mục, chi tiết hơn

**§3 `background`** — sáu tiểu mục: MDP và DQN, offline RL, ZKP, cam kết Merkle,
SP1, số học fixed-point. Đây đúng là nội dung mục 2 và 3 của tài liệu này, viết
gọn lại.

*Chỗ đáng chỉ cho thầy:* tiểu mục fixed-point nói rõ **trần** của encoding — phép
nhân `γ · Q` ra khỏi vùng biểu diễn khi `|Q|` vượt `i64::MAX / γ ≈ 9,3 × 10¹⁵`,
và trỏ tới Định lý 8. Đó là chỗ một chi tiết cài đặt trở thành một phát biểu hình
thức.

**§4 `threat_model`** — mục quan trọng nhất về mặt học thuật, vì nó định nghĩa
**bài toán**. Sáu tiểu mục: vai trò, tài sản/public/private, mô hình đối thủ,
ranh giới đúng đắn của phần thưởng và dữ liệu, mục tiêu và **phi mục tiêu**, ma
trận claim.

Danh sách đối thủ đánh số `A1`, `A2`, … Hai mục mới thêm theo đúng hai lỗi ở mục
8 của tài liệu này:

| | Đối thủ | Tương ứng |
| --- | --- | --- |
| A4 | prover **mài seed lấy mẫu** (sampler grinding) | mục 8.1, Định lý 7 |
| A5 | prover khai thác **tràn số học** | mục 8.2, Định lý 8 |

*Chỗ đáng chỉ:* tiểu mục "Reward and Dataset Correctness Boundary". Hệ **không**
chứng minh phần thưởng trong dataset là **đúng sự thật** — nó chứng minh phần
thưởng ấy **khớp với thứ đã được cam kết và kiểm toán**. Phân biệt này là chỗ dễ
bị hỏi nhất, nên phải thuộc:

> *"Chúng tôi không chứng minh dữ liệu nói thật. Chúng tôi chứng minh anh đã
> huấn luyện trên đúng dữ liệu anh đã đăng ký, không sửa gì. Việc dữ liệu ấy có
> phản ánh thế giới thật không là bài toán kiểm toán dữ liệu, và nó nằm ngoài
> phạm vi — chúng tôi ghi rõ điều đó."*

**§5 `system_overview`** — bảy giai đoạn:

```
1–3  đường ống provenance dữ liệu      thu thập → kiểm toán → cam kết
4–5  proof của các quan hệ đơn         membership, TD, forward, SGD
6    training fragment                 k bước, sync target, biên Q
7    aggregation                       manifest chain HOẶC recursion
```

Kèm một hình xếp tầng. Tầng 5 nay ghi *"Aggregation (manifest chain or in-guest
recursion)"* — trước đó chỉ ghi manifest chain, tức là hình **hẹp hơn** thứ hệ
thật sự làm.

**§6 `relations`** — bảy tiểu mục, mỗi tiểu mục một quan hệ, cộng bảng tóm tắt
phạm vi backend. Đây là bản hình thức của mục 5.2 tài liệu này.

**§7 `formal_statements`** — **mười định lý**. Đây là mục để chỉ khi ai đó hỏi
"đóng góp lý thuyết đâu":

| # | Định lý | Nói gì |
| ---: | --- | --- |
| 1 | Replay membership soundness | không bịa được transition ngoài cây |
| 2 | Audited dataset commitment soundness | dataset khớp báo cáo kiểm toán |
| 3 | Bellman target correctness | TD target tính đúng công thức |
| 4 | Forward, backpropagation, update correctness | mạng, gradient, cập nhật đúng |
| 5 | Checkpoint-chain soundness | các bước nối liền, không ghép rời |
| 6 | Training-fragment soundness | *k* bước hợp thành đúng |
| **7** | **Sampler binding** | **seed dẫn xuất, prover không mài được** ← mới, từ mục 8.1 |
| **8** | **Bounded fixed-point arithmetic** | **không phép nhân nào tràn** ← mới, từ mục 8.2 |
| 9 | Chunk-chain and recursive aggregation soundness | **hai** chế độ gộp, mục 6.3 |
| 10 | Zero-knowledge and privacy boundary | cái gì lộ, cái gì không |

Định lý 7 và 8 là **hai định lý mới sinh ra từ hai lỗi tự tìm thấy**. Khi trình
bày, đó là một điểm mạnh chứ không phải điểm yếu: chúng cho thấy công trình đã
được tự phản biện chứ không chỉ được xây.

*Lưu ý khi đọc bản in cũ:* việc chèn Định lý 7 và 8 làm định lý aggregation dịch
từ số 7 sang **số 9**. Tài liệu nội bộ nào còn ghi "Theorem 7 = aggregation" là
đang nói tới đánh số cũ.

**§8 `proof_backend`** — sáu tiểu mục: tổ chức backend, **ba ràng buộc quan hệ
tự khai**, quy trình prove/verify, ràng buộc public input, test vector và
provenance, quét tamper trong backend.

*Chỗ đáng chỉ:* "Three Constraints the Relation Declares" — đây là ba thứ được
đưa lên thành **public input tường minh** thay vì để ngầm: `target_sync_interval`,
`q_abs_max_fp`, `gradient_clip_fp`. Ba con số này người kiểm đọc được và so được
với hồ sơ đăng ký.

**§9 `training_fragment`** — mã giả của quan hệ trung tâm. Bản hiện tại **dẫn
xuất** σ (seed lấy mẫu), **kẹp** gradient, và **kiểm biên** Q — trước đó cả ba
đều không có trong mã giả.

**§10 `results`** — tám tiểu mục. Đây là mục sẽ bị hỏi nhiều nhất:

| Tiểu mục | Nội dung tài liệu này |
| --- | --- |
| Experimental Setup | mục 7.1 |
| RL Performance (Bảng 1) | mục 7.2 |
| ZK Proof Cost (Bảng 2) | mục 7.3 |
| A Whole Training Run Under One Proof | mục 7.6 |
| What the Provable Configuration Costs | mục 7.4 |
| **A Defect the Tamper Suite Could Not See** | **mục 8.1** |
| Tamper Rejection (Bảng 3) | mục 7.5 |
| Artifact Reproducibility | mục 9.3 |

Tiểu mục in đậm là tiểu mục bất thường: một mục Results kể về **lỗi của chính
mình**. Đó là lựa chọn có chủ ý — nó biến một lỗi thành một đóng góp phương pháp,
và nó là chỗ trả lời trước cho câu hỏi "benchmark tamper của các anh có ý nghĩa
gì nếu nó bỏ sót?".

**§11 `discussion`** — năm tiểu mục, và hai cái đầu là quan trọng nhất:
"What the System Verifies" và **"What the System Does Not Claim"**. Tiểu mục thứ
hai liệt kê thẳng những thứ **không** claim:

- không phải huấn luyện DQN đầy đủ
- không có Adam
- không phải mọi quan hệ đều có backend SP1
- không claim việc thu thập dữ liệu công khai là trung thực
- recursion không phải ở mọi T
- child proof không phải PLONK

Repo có bộ quét `check_paper_claims.py` **chặn tự động** việc nới các claim này
**[đo]**. Nói ra được điều đó trước phản biện rất mạnh: *"chúng tôi có một cổng
CI từ chối commit nào nới claim vượt coverage."*

**§12 `related_work`** — so với Kaizen (CCS 2024), zkPoT (Tan và cộng sự, 2025),
VeriDP, và khảo sát ZKML.

*Cách định vị khi bị hỏi "khác gì Kaizen":*

> *"Kaizen chứng minh huấn luyện có giám sát ở quy mô lớn hơn chúng tôi nhiều.
> Chúng tôi không cạnh tranh về quy mô. Chúng tôi khác về **loại nghĩa vụ**: ba
> thứ ở mục 5.4 — nhãn tự sinh, sync rời rạc, lấy mẫu không có thứ tự chuẩn —
> không xuất hiện trong bất kỳ công trình học có giám sát nào, kể cả Kaizen."*

**§A `appendix`** — bốn phần: gói benchmark, provenance SP1, **lệnh tái lập**,
regression Python đầy đủ; cộng định nghĩa tamper và **bảng định lý → artifact**.

Bảng cuối đáng chỉ riêng: nó ánh xạ **từng định lý** sang **tệp artifact** chống
lưng cho nó. Đó là câu trả lời cho "làm sao tôi kiểm được phát biểu này".

### 9.3 Ba con đường tái lập, theo mức chi phí

Khi bị hỏi *"tôi kiểm lại bằng cách nào?"*, có ba mức, và nên nói cả ba:

| Mức | Lệnh | Chi phí | Kiểm được gì |
| --- | --- | --- | --- |
| **1. Không cần GPU** | `python -m unittest discover tests` | ~38 s, 237 test | oracle, schema, ràng buộc số paper, quy tắc claim |
| **2. Verify proof đã có** | host SP1 với proof trong `provenance/` | vài giây | proof thật sự verify được |
| **3. Prove lại từ đầu** | `RUN_SP1_PROVE=1 cargo run --release -p <host> -- --prove` | hàng giờ, cần GPU | toàn bộ Bảng 2 |

Điểm mạnh khi trình bày: **mức 1 không cần gì cả** — một reviewer clone repo và
chạy được ngay trên laptop, và đã kiểm được phần lớn tính nhất quán.

---

## 10. Câu hỏi phản biện, và cách trả lời

Mười câu dưới đây là những câu **có khả năng bị hỏi nhất**, xếp theo mức khó.
Mỗi câu có một câu trả lời ngắn để nói ra miệng, và số liệu để chống lưng.

**Q1. "Tại sao không chứng minh luôn cả 50.000 bước huấn luyện?"**

> Vì ta hết **số nguyên** trước khi hết tiền. Q phân kỳ theo hàm mũ, ×22 mỗi 156
> bước, và chạm trần `i64` ở khoảng 9,3 × 10¹⁵ (mục 2.17). Ngoài ra chi phí:
> ước tính ~68 giờ GPU ≈ $82 cho CartPole ở quy mô học được, ngoài ngân sách.
> **Cả hai giới hạn đều được đo, không phỏng đoán.**

**Q2. "Batch size = 1 thì có ý nghĩa gì? Không ai huấn luyện như thế."**

> Đúng là không ai dùng batch 1 **với sync ngắn**. Nhưng chúng tôi đã đo: batch 1
> **không** phải nguyên nhân sập — `sync = 100` mới là. Ở `sync = 2000`, batch 1
> đạt 209,5 trên cartpole-random và **−152,7** trên lunarlander-random, **vượt**
> cấu hình tinh chỉnh batch-256 (−215,3). Xem mục 7.4.

**Q3. "Nếu prover cứ tự khai một dataset khác thì sao?"**

> Không được. `dataset_root` là **public input**, và `merkle_membership` chứng
> minh mọi transition dùng trong huấn luyện nằm trong đúng cây đó. Đổi dataset là
> đổi root, và root nằm ngoài, người kiểm đọc được. Bảng 3 có 14 phép thử riêng
> cho nhóm `dataset_root`, tất cả đều bị từ chối.

**Q4. "Prover chọn seed có lợi thì sao?"**

> Đó chính là lỗi chúng tôi **tự tìm ra và tự sửa** (mục 8.1). Nay
> `sampler_seed = H(dataset_root, global_step_start)` — dẫn xuất, không khai. Đây
> là Định lý 7, và có test hồi quy khoá lại.

**Q5. "Benchmark tamper 236 ca xanh 100% — nghe như bài kiểm quá dễ."**

> Câu này đúng, và chúng tôi viết hẳn một tiểu mục Results để nói điều đó. Bộ
> tamper kiểm **theo trường**; nó bỏ sót lỗi **ngữ nghĩa**. Chứng cứ: nó xanh
> 100% trong suốt thời gian lỗi lấy mẫu tồn tại, vì không trường nào bị sửa. Đó
> là một giới hạn có thật của loại benchmark này, không riêng của chúng tôi.

**Q6. "Bảng 2 trộn CPU và GPU thì so sánh kiểu gì?"**

> Cột `Prover` ghi rõ từng dòng, và không dòng nào để trống. Sáu trong tám host
> **không có nhánh CUDA trong mã nguồn** — đó là sự thật kỹ thuật, không phải lựa
> chọn thí nghiệm. Chúng tôi so cycles (tất định, độc lập phần cứng) khi cần so
> khối lượng, và chỉ so thời gian trong cùng nhóm prover. Toàn bộ 25 dòng sinh ra
> trong **một lượt chạy trên một máy**, nên lần này chúng nhất quán nội bộ.

**Q7. "Vì sao STARK mà không phải Groth16, khi Groth16 cho proof nhỏ hơn ngàn
lần?"**

> Vì Groth16 cần **trusted setup**, và setup ấy phải làm lại cho **mỗi mạch**.
> Với một hệ mà cơ quan quản lý là người kiểm, thêm một giả định tin cậy là thêm
> một câu hỏi khó trả lời. Và chúng tôi **đã đo** cái giá của Groth16 khi đưa vào
> trong mạch: gấp 14,6 lần cycles, verify chậm hơn 1.256 lần (mục 3.7).

**Q8. "Adam là chuẩn công nghiệp. Không có Adam thì kết quả có nghĩa gì?"**

> Ba lý do kỹ thuật khiến Adam không dùng được ở `FP_SCALE = 1000` (mục 2.15),
> và chúng tôi ghi rõ đó là giới hạn. Nhưng số liệu nói thêm một điều: trên 24
> cặp so được, Adam thắng 13 – SGD 11 — **gần như hoà**. Và trên CartPole, SGD
> thắng **10–2**. Nên "không có Adam" không phải một khiếm khuyết mang tính hệ
> thống.

**Q9. "Hash guest ELF của các anh không tái lập được. Vậy con số của các anh có
kiểm được không?"**

> Câu này đúng và chúng tôi ghi rõ trong paper. Hash ELF định danh **lần build**,
> không phải mã nguồn. Nó **vẫn** dùng được cho mục đích thật của nó: phát hiện
> việc chỉ prove lại một phần bảng. Nó **không** dùng được làm mỏ neo tái lập cho
> reviewer build từ clone sạch, và chúng tôi **không** phát biểu như thế. Đường
> chưa thử là `BuildArgs { docker: true }` — chúng tôi nói rõ là chưa thử.

**Q10. "Đóng góp thật sự là gì? Nghe như áp một công cụ có sẵn lên một bài toán
mới."**

> Bốn thứ. **Một:** ba nghĩa vụ xác minh riêng của RL mà không công trình học có
> giám sát nào gặp, hình thức hoá thành Định lý 7 và 8 (mục 5.4). **Hai:** một
> lượt huấn luyện trọn vẹn 4.992 bước dưới **một** proof, verify trong 54 ms.
> **Ba:** đo bằng số cái giá của "cấu hình chứng minh được", và chỉ ra thứ đắt
> (batch size) **không** phải nguyên nhân — thứ miễn phí (sync interval) mới là.
> **Bốn:** hai lớp tấn công được phát hiện bằng chính việc dựng hệ, mà benchmark
> tamper theo trường về nguyên tắc không thấy được.

---

## 11. Còn lại gì

| Việc | Trạng thái |
| --- | --- |
| Đưa proof 4.992 bước vào Bảng 2 | chờ giải quyết mục 8.4 — thử `BuildArgs { docker: true }`, ~$0,5 |
| CartPole ở quy mô học được (50.000 bước) | ngoài ngân sách — ước ~68 giờ GPU, ~$82 |
| Chứng minh Adam | không khả thi ở `FP_SCALE = 1000` |
| Batch size > 1 | cần sửa quan hệ; cycles nhân theo batch |
| Bọc PLONK | cần ~60 GB RAM, vượt máy đã thuê (32 GB) |
| Nhánh CUDA cho sáu host còn lại | việc kỹ thuật thật, ngoài phạm vi hiện tại |

Về giới hạn độ dài: đây là ranh giới **đo được**, không phải chỗ né tránh. Lá lớn
hơn cũng không cứu được — lá 1.000 bước tốn khoảng 3,9 tỉ cycles, vượt mức lớn
nhất từng prove thành công (1,68 tỉ) và đụng trần RAM máy chủ (~27 byte mỗi
cycle, tức khoảng 105 GB).

---

## 12. Đọc tiếp

| Tài liệu | Nội dung |
| --- | --- |
| `docs/architecture.md` | kiến trúc mã nguồn và luồng làm việc |
| `docs/claim_matrix.md` | từng phát biểu và bằng chứng chống lưng |
| `docs/backend_coverage.md` | quan hệ nào có backend SP1, quan hệ nào chưa |
| `docs/reproducibility.md` | cách chạy lại regression và sinh lại báo cáo |
| `docs/recursion_cycle_analysis.md` | phân tích chi phí recursion |
| `docs/theorem_artifact_map.md` | từng định lý trỏ tới artifact nào |
| `CLAUDE.md` | quy ước cho người và agent đóng góp vào repo |

**Artifact để tra số:**

| Tệp | Chứa gì |
| --- | --- |
| `artifacts/reports/final_ndss/table1_rl_performance.csv` | 54 dòng Bảng 1 |
| `artifacts/reports/final_ndss/table2_zk_proof_cost.csv` | 32 dòng Bảng 2 |
| `artifacts/reports/final_ndss/table3_tamper_rejection.csv` | 236 dòng Bảng 3 |
| `artifacts/reports/provenance/sp1/<case>/metrics.json` | số đo từng lần prove |
| `artifacts/reports/provenance/sp1/<case>/tamper_report.json` | kết quả quét giả mạo |
| `artifacts/datasets/<id>/dataset_manifest.json` | provenance từng dataset |
| `zk_backend/test_vectors/*_case_0.json` | vector canonical đã khoá |
| `paper/generated/table*.tex` | bảng sinh ra, paper `\input` thẳng |
