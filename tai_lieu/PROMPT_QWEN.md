# BỘ PROMPT CHO QWEN — chạy tiếp dự án The Brain

> ## CẬP NHẬT 08/09/2026 — GIỜ CHỈ CẦN MỘT LỆNH
>
> Tài liệu này vẫn đúng và vẫn nên đọc, nhưng **không còn phải dán tay vào chat**.
> Toàn bộ nội dung dưới đây đã được đóng thành một hệ tự chạy:
>
> ```
> cd "C:\Users\SV STORE\Downloads\Research SP500\lab"
> q
> ```
>
> `q` nạp bảng việc (`lab/qwen/NHIEM_VU.json` — chính 4 việc ở mục 2 và 5 việc ở
> mục E bên dưới), đo CPU và giữ máy ở ~85%, phóng việc song song theo làn, **chấm
> kết quả bằng code** (`lab/qwen/cong.py`), rồi để qwen đọc kết quả và viết nhật ký.
> Tắt máy giữa chừng cũng không sao — gõ `q` lại là nó đi tiếp.
>
> Đọc `lab/qwen/DOC_TRUOC.md` trước. Kiểm đường: `q kiem`. Xem bảng: `q trang-thai`.
>
> Ranh giới cứng của hệ đó, và lý do nó tồn tại: **qwen đọc và viết, code chấm và
> chặn.** Vì đã đo được — LLM điền `co_che` cho 48 khai báo, thẩm định bác 41, ròng
> cứu 3.

Viết 07/09/2026. Mục đích: **dự án chạy tiếp được khi không có Claude.**

Qwen sẽ sai. Tài liệu này viết để **cái sai bị bắt tại chỗ** chứ không đi vào báo
cáo. Nguyên tắc xuyên suốt: mọi con số phải qua một cổng kiểm; cổng nào không
chạy được thì ghi "CHƯA ĐO ĐƯỢC", tuyệt đối không ghi "không có edge".

---

## 0. NẠP BỐI CẢNH — dán nguyên khối này vào đầu mỗi phiên

```
Bạn đang làm việc trong dự án nghiên cứu định lượng "The Brain" tại
C:\Users\SV STORE\Downloads\Research SP500\lab

Python DUY NHẤT được dùng:
C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe

Trước khi làm bất cứ việc gì, đọc theo đúng thứ tự:
  1. lab/CLAUDE.md          — luật không được phá + bẫy đã sập
  2. lab/TIEP_TUC_MAI.md    — trạng thái và việc đang chờ
  3. PROMPT_QWEN.md         — file này
  4. BAO_CAO_2026_09_07.md  — kết quả mới nhất

Quy tắc bất di bất dịch:
- KHÔNG kết luận từ một con số chưa biết nó sinh ra thế nào.
- Kết quả ÂM phải phân biệt với CHƯA ĐO ĐƯỢC.
- Mọi bảng số phải kiểm: các dòng có GIỐNG HỆT NHAU không? Nếu có → hỏng.
- Trả lời tiếng Việt, ngắn, đi thẳng vấn đề.
```

---

## 1. DỰ ÁN ĐANG Ở ĐÂU (tính đến 07/09/2026)

Mục tiêu: tìm hệ giao dịch **thắng mua-giữ ở CÙNG mức sụt giảm**, kiểm bằng
MT5 Strategy Tester trên dữ liệu XM thật.

**Đã có gì**

| | |
|---|---:|
| cơ chế trong kho (`config/co_che_dsl.json`) | 574 |
| dịch được ra MQL5 | ~530 |
| chân dương trên D1 (train+holdout) | **84** (46 gốc + 38 đảo chiều) |
| chân dương trên H4 | 61 · H1 29 · M30 16 |

**Phát hiện lớn nhất, đã qua kiểm ngoài mẫu:**

> Bảng xếp hạng **hệ đơn** gần như là nhiễu (822,7 → 40,7 ở holdout).
> Nhưng **ghép hai chân** thì sống: 39/45 cặp đầu bảng train vẫn hơn chính hệ
> đơn đó ở holdout, trung vị cao gấp 2-4,5 lần.
> **Chọn cơ chế là may rủi; chọn GHÉP thì không.**

**Nút thắt đã truy ra:** lợi thế ghép đến từ chân **NGƯỢC CHIỀU** (93-94% cặp
ngược chiều có tương quan âm; cùng chiều chỉ 3-4%). Mà trong 60 chân dương tốt
nhất **chỉ 4 chân là chiều BÁN**. Ba hướng đã thử và đều thất bại vì cùng lý do
— chúng không sinh thêm chân bán nào:

- khung H4 → 5/15 cặp giữ hạng (D1: 39/45)
- khung nhỏ hơn → chân dương 84 → 61 → 29 → 16, giảm theo chi phí
- tài sản khác → trung vị holdout 71,5 so với 108,3 của cùng tài sản

---

## 2. BỐN VIỆC TIẾP THEO — làm theo thứ tự, không nhảy cóc

### VIỆC 1 — Sinh thêm CHÂN BÁN có lãi (ưu tiên cao nhất)

Đây là nút thắt thật. Hai đường:

**1a. Chạy đảo chiều trên MỌI mã, không chỉ US100.**
Đảo chiều là cỗ máy DUY NHẤT đang sinh chân bán (129 cơ chế âm → 38 chân dương).
Mới chạy cho US100/US500/US30. Chưa chạy: GER40, UK100, JP225, AUS200, FRA40,
EU50, HK50, US2000.

```
cd "C:\Users\SV STORE\Downloads\Research SP500\lab"
python _dem_ghep.py GER40Cash
```

**1b. Đào kho theo họ cơ chế BÁN.** Kho có 115 cơ chế `chieu = -1`, phần lớn
chưa từng ra tester. Lọc và chạy chúng.

**Cách kiểm việc 1 đã đúng chưa:** số chân dương chiều BÁN phải TĂNG. In ra:
```python
# đếm chân bán trong danh sách chân dương
import json
d = json.load(open('reports/DEM_CHAN_DUONG_<MA>.json', encoding='utf-8'))
```
Nếu số chân bán không tăng thì việc 1 **chưa xong**, đừng chuyển việc 2.

### VIỆC 2 — Bật ĐẶT HUỀ vào các bảng ra tiền

Đã đo: trong 6 cơ chế quản trị vị thế, **chỉ đặt huề sống sót** (+4,8% lãi, sụt
giảm không đổi). Nó miễn phí nên không có lý do không bật.

```
python _quan_tri_ghep.py US100Cash <chan_A> <chan_B>
```

**CẤM:** trailing (−68%), nhồi lệnh (cháy tài khoản ngoài mẫu), hệ số lot > 1,0
(cháy ngay trong mẫu). Đã đo cả ba, đừng đo lại.

### VIỆC 3 — Placebo cho 38 chân đảo chiều

Chúng mới qua train+holdout, **chưa qua placebo**. Chưa qua placebo thì không
được gọi là phát hiện.

```
python _quet_placebo_rong.py US100Cash,US500Cash,US30Cash,GER40Cash
```
Đạt = `p <= 0,05` trên **ít nhất 2 mã**. Một mã không đủ (đã đo: 5 cơ chế
"mạnh trên US100" chết sạch khi kiểm chéo).

### VIỆC 4 — Lệnh stop hai đầu

`_stop_hai_dau.py` đã viết và biên dịch được, **chưa chạy**. Phải **tải M1 về
trước** (xem bẫy #6), vì nó là quản trị TRONG NẾN nên bắt buộc Model=0/4.

---

## 3. MƯỜI BẪY ĐÃ SẬP THẬT — kiểm trước khi tin bất cứ số nào

Mỗi bẫy dưới đây **đã từng cho ra một bảng số trông hoàn toàn bình thường**.

**1. Các dòng kết quả GIỐNG HỆT NHAU = tham số không có tác dụng.**
Đây là dấu hiệu chung của 3 lỗi khác nhau trong một phiên. Luôn kiểm:
```python
print('so gia tri khac nhau:', len(set(x['lenh'] for x in ds)))
```
Bằng 1 hoặc 2 trên hàng trăm pass → dừng lại, đi tìm lỗi.

**2. `PositionClosePartial` dưới lot tối thiểu thất bại IM LẶNG.**
Lot 0,10 với min 0,10 thì nửa vị thế = 0,05 → tỉa lệnh không bao giờ chạy, và
bảng số đọc y hệt "tỉa không ăn thua". Phải chạy ở lot ≥ 2× min.

**3. Đặt lệnh trong khối nến-mới → "Market closed", không dấu vết.**
Nến D1 đổi lúc 00:00, nằm NGOÀI phiên CFD chỉ số. Mọi lệnh phải đi qua
`KhopYDinh` (giữ ý định, khớp ở nến H1 đầu tiên giao dịch được).

**4. `import` file không có `__main__` guard = chạy lại cả lượt tester.**
Đã ghi đè mất một báo cáo 4 mã bằng bản 1 mã. Mọi script trong `lab/` phải có
`if __name__ == "__main__":`.

**5. MT5 dồn bar NGÀY vào khung nhỏ khi thiếu dữ liệu, không báo lỗi.**
2012-2015 H4 và D1 có **số bar y hệt nhau**. Độ sâu dữ liệu thật của
US100Cash: D1 từ 2011 · **H4/H1 từ 2016** · M30 từ 2018-04 · M15 từ 2022-06 ·
**M5 từ 2025-04 (1,4 năm)**. Kiểm bằng cách **đếm bar mỗi năm**, không nhìn ngày
đầu chuỗi.

**6. `Model=0/4` cần M1 mà máy chỉ có M1 từ 2026-05-28.**
Một lượt 10 năm tốn 19,5 phút rồi trả **bảng RỖNG**. Dùng `Model=2` cho logic
theo nến đóng (đúng và nhanh). Chỉ dùng Model=0/4 cho quản trị TRONG NẾN, và
phải tải M1 về trước.

**7. `Model=1` chế ra lãi giả 12 lần** khi TP < 2× biên độ nến M1.

**8. MT5 chỉ ghi tham số ĐƯỢC QUÉT thành cột XML.**
Tham số cố định (`||...||N`) không có cột → `d.get("InpKieuRa", 0)` trả 0 dù EA
chạy kiểu 2 → phán xử nhầm dòng mốc.

**9. `Optimization=2` là thuật di truyền, bỏ sót cơ chế.** Luôn dùng `=1`.

**10. EA NHIỀU-SLOT có thể làm lệch số — CHƯA TRUY RA.**
Cùng 36 chân, cùng phép đổi khung, ở H1: EA nhiều-slot (`dich_mq5_ghep`) cho
6/36 dương / −4.739; EA `switch` (`dich_mq5.sinh_ea` + `InpMaCoChe`) cho 22/36 /
+2.179. Trên D1 với 3 slot thì hai đường khớp chính xác. Nghi vấn ở **nhiều
slot** và/hoặc **`giu` bị nhân lớn ở khung nhỏ**.
→ **Việc cần làm sớm:** chạy đối chứng switch-vs-nhiều-slot trên D1 với 40 slot.
Nếu lệch thì mọi con số ghép (dựa trên đường vốn từ EA nhiều-slot) phải đo lại.

**11. Cơ chế TRÙNG LẶP dưới tên khác: 11-13% kho.**
`z_score_reversion` == `mua_khi_gia_duoi_dai_duoi_bollinger` (cùng chuỗi lệnh).
Khử trùng phải theo **ĐƯỜNG VỐN**, không theo tên hay vân tay spec.

---

## 4. CHI PHÍ THẬT — đo trực tiếp từ tài khoản, đừng giả định

```
US100Cash (XM, tài khoản 420568985 — THẬT, không phải demo, số dư 0)
  contract 1,0 | min lot 0,1 | bước 0,1 | max 240
  spread 2,90 điểm chỉ số ≈ 0,98 bps
  ký quỹ 0,1 lot = 2,96 USD (đòn bẩy 1:1000)
  swap MUA  -4,61/lot/đêm = 1,56 bps/đêm  ← ĐẮT HƠN spread
  swap BÁN  +0,52/lot/đêm = +0,18 bps/đêm ← chân bán được TRẢ tiền
```

Spread ăn bao nhiêu phần biên độ nến: M5 12,0% · M15 7,4% · M30 5,7% · H1 4,4%
· H4 1,9% · **D1 0,7%**.

---

## 5. VỐN ↔ LOT — công thức và chỗ nó gãy

Tester chạy **lot cố định**, nên `(lot L, vốn 10.000) == (lot L×k, vốn 10.000×k)`
— cùng %/năm, cùng sụt giảm %.

**Gãy ở lot tối thiểu.** Ở vốn 100 USD trên tài khoản CHUẨN, không cấu hình nào
chạy được — không phải "chạy nhỏ hơn" mà là **không đạt min lot**. Tài khoản
Micro/cent chia hợp đồng 100 lần nên bỏ được sàn đó: dòng "vốn 10.000" đọc thành
**100 USD thật trên Micro**.

```
python _von_va_lot.py US100Cash
```

---

## 6. CÔNG CỤ — file nào làm gì

| file | việc |
|---|---|
| `_dem_ghep.py` | dây chuyền 4 chặng: mở kho → đảo chiều → ma trận → cổng ra tiền |
| `_bo_ba.py` | ghép bộ ba + khử trùng theo đường vốn |
| `_ghep_holdout.py` | chấm cặp trên train, đọc holdout (KHÔNG tốn tester) |
| `_ghep_he.py` | ghép 2 hệ + mốc mua-giữ, hai chặng |
| `_ma_tran_ghep.py` | ma trận tương quan 41 slot trong 1 lần chạy |
| `_khung_nho.py` | quét chân trực tiếp trên từng khung |
| `_ghep_da_tai_san.py` | ghép chéo tài sản (không tốn tester) |
| `_do_thoi_gian_giu.py` | thời gian giữ lệnh từng chân |
| `_quan_tri_ghep.py` | 5 lượt quét quản trị vị thế |
| `_von_va_lot.py` | bảng vốn ↔ lot |
| `nhan/doi_khung.py` | **bộ đổi khung**: chu kỳ + khớp phân vị + hiệu chỉnh gộp |
| `nhan/dich_mq5_ghep.py` | EA N slot chạy đồng thời, mỗi slot một magic |
| `nhan/dich_mq5_quan_tri.py` | EA có quản trị vị thế |

---

## 7. BỘ ĐỔI KHUNG — dùng thế nào

```python
from nhan import doi_khung as DK
r = DK.doi(spec, 'XM_US100CASH', 'D1', 'H4', '2016-06-01', '2021-06-01')
r['spec']        # spec đã đổi
r['kich_hoat']   # {goc, chi_nhan_chu_ky, khop_tung_ve, sau_khop_phan_vi}
DK.dat(r)        # True nếu tỉ lệ kích hoạt sau khi đổi còn gần bản gốc
```

Ba bước, đừng bỏ bước nào:
1. **chu kỳ** (`n`, `giu`) × tỉ lệ bar **đo được từ dữ liệu** (D1→H4 là 5,956
   chứ không phải 6)
2. **ngưỡng** (`hang`) khớp **phân vị** — giữ độ hiếm của sự kiện
3. **hiệu chỉnh gộp** — một hệ số chung để tỉ lệ kích hoạt ĐỒNG THỜI khớp bản gốc

**Giới hạn phải biết:** chỉ 26/84 cơ chế có hằng số ngưỡng để chỉnh; 58 cái còn
lại là so sánh chỉ báo với chỉ báo nên bộ đổi chỉ làm được bước 1.

---

## 8. CỔNG — thứ tự và ngưỡng

```
1. train + holdout   dương ở CẢ HAI đoạn, >= 25 lệnh mỗi đoạn
2. placebo           dịch tín hiệu 201 độ, p <= 0,05
3. đa tài sản        đạt placebo trên >= 2 mã
4. cổng ra tiền      %/năm > mua-giữ ở CÙNG sụt giảm (mốc nằm trong cùng EA)
```

Chưa qua cả bốn thì gọi đúng tên: *"canh bạc có kỳ vọng dương đo được"*, chưa
phải phát hiện.

---

## 9. VIẾT BÁO CÁO THẾ NÀO

Mỗi phiên **một file** `BAO_CAO_<ngày>.md`, và bắt buộc có:

- **"Một đoạn đọc là hiểu cả phiên"** — 5-10 dòng, nói phát hiện lớn nhất và
  cái gì lật ngược kết luận cũ.
- Mọi bảng số phải có **số lệnh**, không chỉ %/năm.
- Kết quả âm phải ghi rõ **âm** hay **chưa đo được**.
- Phần **"Việc tiếp theo"** xếp theo giá trị trên mỗi giờ máy.
- Phần **"Vướng mắc còn lại"** — cái gì biết là chưa đúng nhưng chưa sửa.

Chốt phiên: `b ket "một câu tóm tắt"`

---

## 10. NĂM CÂU HỎI TỰ KIỂM TRƯỚC KHI BÁO BẤT KỲ KẾT QUẢ NÀO

1. Các dòng trong bảng có **giống hệt nhau** không? (→ tham số không tác dụng)
2. Con số này là **trong mẫu hay ngoài mẫu**? Tham số chọn ở đâu?
3. Có **mốc mua-giữ** trong cùng lần chạy không? Ở **cùng sụt giảm** chứ?
4. Số **lệnh** có đủ để kết luận không? (< 25 lệnh mỗi đoạn = chưa đo được)
5. Nếu kết quả âm: **âm thật** hay **chưa chạy được**? Bằng chứng đâu?

Trả lời được cả năm câu thì mới viết. Không thì ghi "CHƯA ĐO ĐƯỢC" — và đó là
một kết quả hợp lệ, không phải thất bại.

---

# CẬP NHẬT 08/09/2026 — BÀN GIAO CHO QWEN

Phiên này chủ dự án đưa **4 giả thuyết mới** và yêu cầu chạy hết công suất. Dưới
đây là trạng thái thật, **bốn lỗi đã vá**, và việc còn lại.

## A. Bốn giả thuyết, xếp lại theo nút thắt đã đo

| # | giả thuyết | đã có gì trong kho | ưu tiên |
|---|---|---|---|
| 2 | breakout grid / stop hai đầu | `pha_vo` 115 cơ chế nhưng **toàn tín hiệu VÀO** | **1** |
| 4 | Gann Square of 9 | `gann` = 0 → **đã cắm vào ngữ pháp** | 2 |
| 1 | reversal point | `quay_ve_trung_binh` 108, zscore 57, channel 27 | 3 (chỉ phân kỳ là mới) |
| 3 | lead-lag | `tuong_quan/lead/lag` = 0 | **4 — hoãn** |

Vì sao GT#2 đứng đầu: cả **574 cơ chế trong kho đều là tín hiệu VÀO**. Kho đã thu
61 hedge · 43 lưới · 43 DCA · 34 recovery mà **0 cái vào được thư viện** — schema
spec không có trường cho quản trị vị thế. Xem `nhan/quan_tri.py`.

Vì sao GT#3 hoãn: **MDE của phễu là 30 bps/lệnh**, lead-lag 1–10 bar hiếm khi
vượt 5 bps, và CFD có `volume=0` nên không đo được order flow.

**KHÔNG dồn máy vào việc săn thêm tín hiệu VÀO cho phễu chỉ số.** Đã đo: kho ×6
mà ứng viên chạm cổng vẫn 21, giao dịch được vẫn 1. Nút thắt là MDE, không phải
sản lượng.

## B. BỐN LỖI ĐÃ VÁ HÔM NAY — đọc trước khi tin bất kỳ kết quả âm nào

**B1. `_stop_hai_dau.py` chưa từng chạy được.** Lỗi cú pháp dòng 248 (một newline
thật lọt vào chuỗi). Báo cáo 07/09 ghi "đã biên dịch được" là nói về EA MQL5.

**B2. Hàng đợi đọc bị 406 URL chết chiếm.** `tradingview.com/script/PUB;<id>` là
mảnh JS nội bộ, không tải được, **không bao giờ bị đánh dấu** → vòng sau lại chọn
đúng chúng. Làn bóc báo *"hết tồn kho"* khi kho còn **4.560 tài liệu**. Đã đánh
dấu; `_qwen_het_cong_suat.py` giờ **ĐO** tồn kho trước khi dám nói "hết".

**B3. `boc_llm._diem_luat` mù với thư viện quant Python.** 60/60 bản github chấm
đúng 0 điểm, kể cả `smart-money-concepts` (40 KB mã FVG/order block/BOS — đúng
thứ `nguyen_thuy_vung` cần). Nguyên nhân: mọi mẫu mã nguồn đều giả định có LỆNH
(`strategy.entry`, `OrderSend`, `self.buy`); thư viện chỉ báo không đặt lệnh bao
giờ. **Đây là lần thứ BA cùng họ lỗi** (03/09 văn xuôi→mã nguồn, 04/09 tiếng
Anh→tiếng Việt có dấu). Đã thêm nhóm mẫu vector-pandas → github **0/60 → 15/60**,
`ung_vien` **0 → 65**.

**B4. Tester treo vì HẾT ĐĨA, không phải vì chậm.** `Tester/logs` ghi rõ
`"no memory for ticks generating"` và `"Tester Agent is wrong for task processing
due low disk space"`. C: còn 8,32 GB; metatester64 chạy 2 giờ tốn 12 giây CPU.
Đã dọn 1,37 GB (log tester + temp cũ) và hạ lưới **1.152 → 48 pass**.

> **C: hiện còn 9,69 GB. Hai thư mục ngốn nhất là `AppData\Local\Google` 13,74 GB
> và `AppData\Roaming\Apple Computer` 5,74 GB — dữ liệu của người dùng, PHẢI HỎI
> trước khi xoá.** Nếu tester lại báo "low disk space" thì hỏi chủ dự án, đừng tự xoá.

## C. Đã thêm vào hệ

- `nhan/ngu_phap.py`: toán hạng **`gann_sq9`** — `(√nền + hướng·k·góc/360)²`. Đo
  thật trên US500CASH.H4: góc 45 → bước 15,47 điểm = 0,387% giá. Đã đăng ký ở
  `CHI_BAO_CO` + `CHI_BAO_NHAN_COT`. **Bước mức tỉ lệ với √giá**, nên chuyển tài
  sản phải dùng `ngoai_sinh.quy_doi` khớp TỈ LỆ KÍCH HOẠT, đừng bê con số `góc`.
- `nhan/muc_tieu.py`: **`TU_KHOA_THEO_CHU_DE`** — săn theo CƠ CHẾ, không theo tài
  sản. 46 từ khoá cho 4 giả thuyết.
- `_san_4_gia_thuyet.py`, `_qwen_het_cong_suat.py` (lab), `boc/rut_luat.py` +
  `boc/tri_tue_cau.py` (Oracle).

## D. ORACLE — vừa nối được vào qwen lần đầu

`grep -rln "tri_tue|openai|qwen"` trên cả Oracle = **0 file**. Oracle chưa bao giờ
gọi được LLM. Đã nối sang `nhan/tri_tue.py` của The Brain qua `boc/tri_tue_cau.py`
— **không dựng lại đường mới**.

Tỉ lệ chuyển đổi đang là 6,8 MB sách → 68 KB luật = **1%**. `boc/rut_luat.py` rút
luật vào đúng shape `tuvy_rulebook.yaml` đang chạy, ghi ra `luat/rut_tu_sach.yaml`.

**Bộ kiểm máy là thứ làm việc giao qwen an toàn** — mỗi luật phải có `trích` là
chữ CÓ THẬT trong đoạn văn. Đang bắt được **~13% luật qwen bịa trích dẫn**.

Ba chốt chặn không được gỡ:
1. KHÔNG ghi đè rulebook đã verify. Ghi file riêng.
2. `user_verified` luôn `false` — chủ dự án tự bật sau khi mở sách đối chiếu.
3. Văn phong ĐIỀU KIỆN. Câu tự khẳng định tuyệt đối bị loại.

Còn hỏng: **`luat/magi_rulebook_v0.1.yaml` không parse được** (ParserError dòng 19).

## E. VIỆC TIẾP THEO — theo thứ tự

1. **Đọc bảng ra của 3 làn đang chạy** (`_stop_hai_dau.py` 48 pass Model=0;
   `_qwen_het_cong_suat.py`; `boc/rut_luat.py` 949 đoạn). Nếu GT#2 có cấu hình
   dương ở Model=0 thì **BẮT BUỘC chạy lại Model=4** trước khi tin — TP nhỏ hơn
   biên độ nến là ca xấu nhất của bẫy `Model=1`.
2. **Vá `magi_rulebook_v0.1.yaml`.**
3. **Sửa `_diem_luat` cho các lớp nguồn còn 0%**: reddit_td 0/60, hackernews 0/60,
   habr_nga 0/60. Cùng họ lỗi B3 — đo trước khi kết luận "nguồn rác".
4. **MQL5 Code Base tải 0 file** trong chiến dịch hôm nay dù `kiem_mang` báo OK.
   Đó là nguồn DUY NHẤT có file chạy tester được ngay. Đo lại `nhan/ma_nguon.py`.
5. **Đưa Gann vào một giả thuyết thật** rồi cho đi qua cổng như mọi cơ chế khác.

## F. NĂM CÂU TỰ KIỂM — trả lời trước khi ghi bất kỳ kết luận nào

1. Con số này sinh ra từ bao nhiêu phép thử? Nếu không biết → chưa được ghi.
2. Kết quả âm này là ÂM hay là CHƯA ĐO ĐƯỢC? Có đo được tồn kho / số lệnh không?
3. Các dòng trong bảng có giống hệt nhau không? Giống → tham số không vào được hệ.
4. Nếu là số tiền: đã trừ phí thật chưa, và mốc so sánh có mua được không?
5. Nếu là tester: chạy Model mấy? Có TP nhỏ hơn biên độ nến không?
