# THIẾT KẾ XÂY LẠI THE BRAIN — bản 16/09/2026

> Đối chiếu `Desktop/hethong.txt` (LUẬT SỐ 0) trước khi đọc. Sơ đồ của chủ dự án là
> SÀN, không phải TRẦN. Bản này không thay sơ đồ đó — nó nói **cái đã xây lệch khỏi
> sơ đồ ở đâu, và sắp lại theo thứ tự nào**.

---

## 0. Một câu trả lời trước, để khỏi mất thời gian

**Không xây lại từ đầu.** Hệ không hỏng vì code — 29 test của bản đồ chạy sạch, 9 hệ
đã qua cổng thật, engine backtest khớp MT5 tester 100%. Hệ hỏng vì **tổ chức lệch với
cái đã đo được là ra tiền**: chỗ tốn công nhất lại là chỗ đo được ít tiền nhất.

Xây lại từ đầu sẽ mắc đúng lỗi mà chính sổ ghi nhớ của dự án đã ghi ba lần: *"tự dựng
lại thứ hệ đã có"* (12/09: xây lại `uu_tien.py`, `noi_sinh.py`, và một EVO thứ hai).
Bản thiết kế này là **tái tổ chức**, không phải viết lại.

---

## 1. Số đo, trước khi bàn thiết kế

Tất cả lấy từ `b toan-canh`, `b he`, `b kien-truc` chạy ngày 16/09/2026.

### 1.1 Phễu vào

| Chặng | Số | Tỉ lệ còn lại |
|---|---|---|
| Tài liệu thu được | 12.078 | 100% |
| Đọc trọn vẹn | 7.348 | 61% |
| **Mẫu chiến lược trong kho** | **18** | **0,15%** |
| Công cụ trong kho | 148 | — |

12.078 tài liệu đổi lấy 18 mẫu. Và sổ ghi nhớ đã đo một lần nữa từ hướng khác:
**kho ×6 mà ứng viên chạm cổng vẫn 21, hệ giao dịch được vẫn 1**. Hai phép đo độc lập
cùng nói một điều: **thu thập thêm không làm tăng đầu ra**.

### 1.2 Phễu ra

| Chặng | Số |
|---|---|
| Giả thuyết đăng ký | 387 |
| Kết quả | 1.284 |
| Ứng viên xếp hạng | 705 |
| Qua holdout của phễu | 592 |
| **Qua cổng thật** | **9** (8 sạch) |
| Dòng FDR đã tiêu | 1.811 |

### 1.3 Chín hệ đó kiếm được bao nhiêu

```
he                                        CAGR%  Sharpe  DD%    lenh  l/tuan
XM_US100CASH.D1.mean_reversion_z5.CHIP    14.05   1.16  -13.51   204   0.64
AUDCAD.H4.ou_quay_ve.n50_z2.5              4.46   0.95   -5.50   100   0.36
AUDCAD.H4.rsi_dao_chieu.n14_vao30_ra_5     4.16   1.16   -3.72    62   0.22
EURGBP.H4.ou_quay_ve.n200_z2.0             3.55   0.89   -7.29    50   0.18
AUDCAD.H4.mat_can_bang_lenh_dong_cua       0.69   0.94   -1.17    53   0.19
EURGBP.H4.mat_can_bang_lenh_dong_cua       0.62   1.47   -0.28    49   0.18
```

Đọc bảng này theo LUẬT SỐ 0 (*mục đích cuối cùng là có tiền*):

- Hệ **đứng đầu bảng xếp hạng hiện tại** là `EURGBP...mat_can_bang` — Sharpe 1,47,
  cao nhất. Nó làm ra **0,62%/năm** với **9 lệnh/năm**. Trên vốn 100 triệu là
  620 nghìn/năm. Đây không phải một hệ, đây là một phép đo.
- Hệ **duy nhất ra tiền thật** là z5 trên US100 (14%/năm) — và sổ ghi nhớ đã đóng nó
  lại: *z5 ÂM trên 55,5 và 98,6 năm, 0/48 ô trên MDE, nó là IBS dưới tên khác*.
- Bốn hệ AUDCAD/EURGBP còn lại: 3,5–4,5%/năm, dưới lãi suất phi rủi ro.

- Đo lại ngày 16/09 với cột mua-giữ: **z5 trên US100 làm 14,05%/năm trong khi mua-giữ
  cùng mã cho 12,22%** — hơn đúng 1,83 điểm mà phải chịu sụt giảm −13,51%. Và
  `US500CASH.D1.mean_reversion_z5` **THUA mua-giữ 1,71 điểm** (8,26% so với 9,97%)
  nhưng vẫn nằm trong bảng "đã qua cổng".

**Kết luận thẳng: sau toàn bộ công sức, hệ chưa có hệ nào ra tiền.** Và những thứ
từng ra tiền thật (Sonic R H4 US500 26%/năm với L=3, lưới Bigmouse AUDCAD 62%/năm,
trailing lãi holdout ×4,8) **không nằm trong bảng 9 hệ này** — chúng ở ngoài đường chạy.

### 1.4 Bảng xếp hạng đang bị bản trùng bơm

Đầu bảng "592 hệ qua holdout":

```
US500M.D1.ns_nen_rau_tren_>_q98_giu10     23.78  67.47  14.90  52.57  20
US500M.D1.ns_nen_sao_bang_>_q98_giu10     23.78  67.47  14.90  52.57  20
```

Sáu con số trùng khít từng chữ số. "Râu trên > q98" và "sao băng > q98" là **một cơ
chế mang hai tên**. 16/18 dòng đầu bảng là các cặp như vậy. Khớp với phép đo đã có:
**616/3.236 cơ chế sinh tín hiệu y hệt nhau**.

Nên con số "592 hệ đang chờ" không phải 592 cơ hội. Và nguy hiểm hơn: **hai bản sao
trông như hai xác nhận độc lập**.

### 1.5 Mã nguồn

| Mục | Số |
|---|---|
| File `.py` | 524 |
| Trên đường chạy | 195 |
| Module lõi `nhan/` | 129 (đã xếp đủ 9 lớp) |
| File rời ở gốc `lab/` | 362 → **147 test (đúng chỗ) + 131 script chạy tay + 84 nợ thật** |
| File > 600 dòng | 32 (`tru/seeker.py` 2.647 · `nhan/ngu_phap.py` 2.328) |
| Module trong gói vẫn mồ côi | 3 |
| `nao.db` | **1,6 GB** |

---

## 2. Chẩn đoán — năm lỗi KIẾN TRÚC

Không phải lỗi code. Mỗi lỗi dưới đây đều có số đo ở mục 1.

### L1. Đầu tư ngược với hiệu quả đo được

| Lớp | Số module | Đầu ra đo được |
|---|---|---|
| THU THẬP | 19 | 12.078 tài liệu → 18 mẫu (0,15%) |
| BÓC TÁCH | 19 | nút thắt, đã biết |
| **QUẢN TRỊ VỊ THẾ** | **12** | **entry tính SAI vẫn cho 92–97%/năm; trailing lãi holdout ×4,8** |

Sơ đồ của chủ dự án nói rõ: *"quản lí lệnh tốt còn hơn việc có 1 entry tốt — module
quan trọng trong toàn bộ hệ thống"*. Mã nguồn nói ngược lại: lớp thu thập đông hơn
lớp quản trị 1,6 lần, và trụ SEEKER một mình 2.647 dòng.

### L2. Cổng ra tiền mồ côi → bảng xếp hạng xếp theo Sharpe

`nhan/cong_ra_tien.py` — *"CỔNG THỨ HAI. Hỏi có ra tiền không, không hỏi có thật
không"* — **không đường chạy nào gọi tới**. Hệ quả nhìn thấy ngay ở mục 1.3: hệ
0,62%/năm đứng đầu bảng vì Sharpe 1,47.

Đây là lỗi nặng nhất, và nó rẻ nhất để sửa.

### L3. Không có khâu khử trùng trước khi tiêu suất FDR

1.811 dòng FDR đã tiêu, trong khi ~19% kho là bản sao. Mỗi bản sao tiêu một suất FDR
và làm chặt cổng cho tất cả những cái còn lại. Bản sao vừa **bơm** xếp hạng vừa
**siết** cổng.

### L4. Sơ đồ nói bốn trụ, mã nguồn có hai

| Trụ | Dòng | Gọi bao nhiêu module nhân |
|---|---|---|
| SEEKER | 2.647 | 17 |
| QUANTLAB | 1.806 | 18 |
| EVOLUTION | 1.393 | 8 |
| **BANKER** | 550 | **1** (chỉ `so`) |
| **FINDER** | 442 | **2** |
| NGHI | 450 | 6 |

BANKER và FINDER là vỏ. Chủ dự án đã chốt *"BANKER KHÔNG BỎ, chỉ hạ thứ tự ưu tiên"* —
bản thiết kế này giữ đúng vậy, nhưng phải gọi đúng tên: chúng **chưa được xây**, không
phải "đang chạy yếu".

### L5. Không có tầng SẢN PHẨM

Từ "hệ qua cổng" đến "tiền vào tài khoản" chỉ có `chay_that.py` và `so_lenh.py`, và hệ
đang `DUNG_LAI: CÓ` — nằm im. Toàn bộ 524 file phục vụ việc **tìm**, gần như không có
gì phục vụ việc **giữ cho cái đã tìm được chạy và sinh tiền**.

---

## 3. Thiết kế v3 — năm tầng, một chiều

Nguyên tắc: **mỗi tầng có một cổng ra, và cổng đó hỏi câu của tầng kế tiếp.**
Không tầng nào được đẩy hàng sang tầng sau mà chưa qua cổng của mình.

```
        ┌──────────────────────────────────────────────────────────┐
  T1    │ NGUỒN      giữ nguyên, ĐÓNG BĂNG quy mô                  │
        │            12.078 tài liệu đã đủ. Cổng ra: KHỬ TRÙNG     │
        └────────────────────────┬─────────────────────────────────┘
                                 │  cơ chế duy nhất (hash tín hiệu)
        ┌────────────────────────▼─────────────────────────────────┐
  T2    │ CƠ CHẾ     ho1 tín hiệu VÀO  +  ho2 QUẢN TRỊ  +  ho3 PMG │
        │            Cổng ra: "ghép được với ít nhất 1 cái khác"    │
        └────────────────────────┬─────────────────────────────────┘
                                 │
        ┌────────────────────────▼─────────────────────────────────┐
  T3    │ HỆ         ho1 × ho2 là ĐƠN VỊ CƠ BẢN, không phải ho1     │
        │            Cổng ra: CỔNG THẬT (placebo/MDE) — nhãn        │
        └────────────────────────┬─────────────────────────────────┘
                                 │
        ┌────────────────────────▼─────────────────────────────────┐
  T4    │ DANH MỤC   ghép cặp ngược chiều, đo tương quan CHUỖI VỐN  │
        │            Cổng ra: CỔNG RA TIỀN — thắng mua-giữ ở CÙNG DD│
        └────────────────────────┬─────────────────────────────────┘
                                 │
        ┌────────────────────────▼─────────────────────────────────┐
  T5    │ SẢN PHẨM   EA nhiều slot → VPS → sổ lệnh → suy giảm       │
        │            Cổng ra: tiền thật vào tài khoản               │
        └──────────────────────────────────────────────────────────┘
```

### Ba thay đổi cốt lõi so với hiện tại

**(a) Đơn vị cơ bản là CẶP, không phải cơ chế đơn.**
Đã đo: *hệ đơn 822 → 40 khi ra holdout, còn cặp giữ hạng 39/45*. Hệ đơn sống sót là
ngoại lệ; cặp sống sót là quy luật. Nên T3 không được xuất "một cơ chế" — nó xuất
`ho1 × ho2` (tín hiệu vào × luật quản trị). Cái này đảo ngược thứ tự làm việc hiện tại
và là thay đổi lớn nhất của bản thiết kế.

**(b) Cổng ra tiền là cổng CUỐI, cổng thật chỉ là NHÃN.**
Đúng LUẬT SỐ 0: MDE/FDR/placebo là **nhãn cảnh báo**, chỉ chặn khi thua mua-giữ ở
cùng rủi ro. Hiện tại cổng thật đang chặn, cổng tiền đang mồ côi — ngược hoàn toàn.

**(c) Khử trùng đứng TRƯỚC mọi thứ tiêu suất FDR.**
Một cơ chế = một hash của **chuỗi tín hiệu sinh ra**, không phải tên. Hai tên cùng hash
→ một suất.

---

## 4. Kế hoạch — bốn đợt, mỗi đợt có tiêu chí dừng

Thứ tự này không tuỳ tiện: **đợt sau chỉ có nghĩa nếu đợt trước xong**. Đợt 1 làm cho
bảng xếp hạng nói thật; nếu bảng còn nói dối thì mọi việc ở đợt 2–4 đều xây trên cát.

### ĐỢT 1 — Làm cho bảng xếp hạng nói thật *(ước tính 1–2 phiên)*

| # | Việc | Xong khi |
|---|---|---|
| 1.1 | Nối `nhan/cong_ra_tien.py` vào đường chạy: `b he` xếp theo **CAGR ròng ở cùng DD**, Sharpe xuống cột phụ | `b he` không còn để hệ 0,62%/năm đứng đầu |
| 1.2 | Khử trùng bằng hash chuỗi tín hiệu, chạy trên cả 3.236 cơ chế trong kho | Báo cáo: bao nhiêu suất FDR đã tiêu oan cho bản sao |
| 1.3 | Chạy lại `b he` sau khử trùng | Danh sách 592 → con số thật |
| 1.4 | Nối 2 module mồ côi còn lại (`doc_video_cuc_bo`, `luoi`) hoặc khai tử có chủ đích | `b kien-truc` mục 4.4 = 0 |

**Tiêu chí dừng đợt 1:** `b he` trả lời được câu *"hệ nào đang ra tiền nhiều nhất trên
mỗi đơn vị sụt giảm"* — và câu trả lời không phải một bản trùng.

### ĐỢT 2 — Đảo trục sang QUẢN TRỊ VỊ THẾ *(2–4 phiên)*

| # | Việc | Xong khi |
|---|---|---|
| 2.1 | Lấy 84 file nợ ở gốc `lab/`: cái nào thuộc quản trị thì đưa lên `nhan/`, còn lại đổi tên `_*.py` hoặc xoá | `b kien-truc` mục 4.2 nhóm ba < 20 file |
| 2.2 | Đưa `dap_quan_tri` thành **bắt buộc** trong phễu: mọi ho1 phải chạy qua ít nhất 3 luật ho2 trước khi vào bảng | Không giả thuyết nào vào sổ mà thiếu chân quản trị |
| 2.3 | Thu hồi những thứ ĐÃ ra tiền mà đang ngoài đường chạy: Sonic R H4 (26%/năm, L=3), lưới Bigmouse AUDCAD, trailing (holdout ×4,8) | Cả ba có mặt trong `b he` với số đo cùng đơn vị |
| 2.4 | Bổ sung docstring cho 25 file đang câm | `b kien-truc` mục 4.1 = 0 |

**Tiêu chí dừng đợt 2:** có ít nhất **3 hệ CAGR ròng > 10%/năm** ở cùng mức sụt giảm
với mua-giữ, và cả ba đều có chân quản trị.

### ĐỢT 3 — Danh mục, không phải hệ đơn *(2–3 phiên)*

| # | Việc | Xong khi |
|---|---|---|
| 3.1 | `nhan/danh_muc.py` thành cổng bắt buộc: ghép **ngược chiều** (đã đo: 93–94% cặp ngược chiều cho tương quan âm) | Mọi hệ vào T5 đều là danh mục ≥ 2 chân |
| 3.2 | Đo tương quan **chuỗi vốn**, không phải chuỗi tín hiệu | Bảng tương quan có trong `b he` |
| 3.3 | Ghép chân âm với chân dương (đã đo: 6,14% → 20,25%/năm ở cùng sụt giảm) | Ít nhất 1 danh mục > 20%/năm |

**Tiêu chí dừng đợt 3:** một danh mục thắng mua-giữ ở cùng sụt giảm, **trên nửa holdout**.

### ĐỢT 4 — Tầng sản phẩm *(2–3 phiên)*

| # | Việc | Xong khi |
|---|---|---|
| 4.1 | EA nhiều slot (đã có: mỗi slot một magic, `lot=0` tắt slot) chạy danh mục của đợt 3 trên tester | Báo cáo tester khớp Python trong 10% |
| 4.2 | Lên VPS, `san_sang_vps.py` thành cổng | Chạy 2 tuần không người |
| 4.3 | `suy_giam.py` vào nhịp ngày: hệ đang chạy còn giống cái đã kiểm định không | Cảnh báo tự đến điện thoại |
| 4.4 | Gộp `nao.db` (1,6 GB) + đóng băng kho | Đĩa không còn là rủi ro im lặng |

**Tiêu chí dừng đợt 4:** tiền thật vào tài khoản thật, và **không cần ai ngồi máy**.

---

## 5. Cái KHÔNG làm — và vì sao

| Không làm | Vì đã đo |
|---|---|
| Thu thập thêm tài liệu | Kho ×6 → ứng viên chạm cổng vẫn 21. 12.078 → 18 mẫu |
| Quét thêm tham số | "Đổi tham số mà không đổi kết quả" — closure DSL từng nuốt tham số; và quét rộng là cách sinh cực đại ngẫu nhiên |
| Xây BANKER / FINDER | Chủ dự án đã chốt: xong ba module thật trước |
| Tin thêm một hệ ĐƠN nào | Hệ đơn 822 → 40 ở holdout |
| Viết lại từ đầu | Sổ ghi nhớ: đã tự dựng lại thứ đã có 3 lần trong 1 phiên |
| Nâng độ chặt học thuật | LUẬT SỐ 0: mục tiêu là TIỀN, MDE/FDR là nhãn |

---

## 6. Rủi ro của chính bản kế hoạch này

Nói trước để sau còn đối chiếu:

1. **Đợt 1.2 (khử trùng) sẽ làm kho sụt, và nó đã ăn vào cả 9 hệ "đã qua cổng".**
   Kiểm ngay khi viết bản này: `mat_can_bang_lenh_dong_cua` xuất hiện **4 lần**, thành
   2 cặp trùng khít từng chữ số (EURGBP 0,62 / 1,47 / −0,28 / 49 lệnh — hai dòng;
   AUDCAD 0,69 / 0,94 / −1,17 / 53 lệnh — hai dòng). Tức **9 hệ thật ra là 7**. Nếu
   19% kho là bản sao thì 592 hệ chờ có thể còn ~480. Đó là tin tốt giả trang tin xấu.
2. **Đợt 2.3 (thu hồi thứ đã ra tiền) có thể không tái lập được.** Sonic R và Bigmouse
   đo ở ngoài đường chạy, chưa qua cổng thật. Có thể chúng chỉ là cực đại ngẫu nhiên.
   Nếu vậy thì biết sớm vẫn hơn.
3. **Đợt 3 giả định tương quan âm giữ được ra ngoài mẫu.** Đã đo là cặp giữ hạng
   39/45, nhưng đó vẫn là quá khứ.
4. **Không đợt nào hứa hệ sẽ ra tiền.** Kế hoạch này chỉ hứa: sau đợt 1, ta sẽ **biết
   thật** hệ đang ở đâu — thay vì nhìn một bảng xếp hạng do bản trùng và Sharpe dựng nên.

---

*Sinh bởi phiên 16/09/2026. Số liệu từ `b toan-canh`, `b he`, `b kien-truc` cùng ngày.
Chạy lại ba lệnh đó trước khi dùng bản này để ra quyết định.*
