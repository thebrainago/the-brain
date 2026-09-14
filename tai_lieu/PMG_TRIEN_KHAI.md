# PMG — TRIỂN KHAI: cái gì đã dựng, đo được gì, và chỗ nào đặc tả nói khác toán

*Phiên 14/09/2026. Đọc cùng `tai_lieu/PMG_DAC_TA.md` (nguyên văn đặc tả — không sửa file đó).*

PMG vào hệ qua **luồng ưu tiên** của chủ dự án, xếp thẳng vào **module quản lý lệnh**.
Đây đúng là họ mà bàn giao 13/09 mục 4.B'.2 đặt hàng: *"có những kiểu đánh chỉ dùng
quản lí lệnh lợi dụng sự di chuyển của giá để chốt rất nhanh 1 lệnh"* — bench cũ
(`ea_QuanTriBench.mq5`) gắn quản trị lên một engine vào **cố định** rồi hỏi "thêm quản trị
thì đổi gì"; PMG không có entry nào cả.

---

## 1. Bốn module, và đường chạy của chúng

| file | việc | cổng |
|---|---|---|
| `nhan/pmg.py` | không gian 7 khối · mã định danh + vân tay · toán `D_BE` · cổng G1 | G1 |
| `nhan/pmg_engine.py` | mô phỏng rổ trên bar · cổng độ phân giải · bất biến tie-break | G2 |
| `nhan/pmg_g0.py` | ER thực vs null · FDR-BH · bản đồ nhiệt · **sổ loại trừ** | G0, G5 |
| `nhan/pmg_quet.py` | sinh cấu hình prereg · placebo 3 bản · walk-forward · bộ đếm phép thử | G1→G4 |

Cửa vào: `b pmg g0` · `b pmg bang` · `b pmg quet <MA>` · `b pmg so`.
Bộ test: `test_pmg.py` (40 test, mọi test có **đáp án biết trước**).

`b ban-do` 14/09 xác nhận cả bốn nằm **trên đường chạy**, không module nào mồ côi —
đây là họ lỗi số 1 của hệ (*"bộ phận có tồn tại, luật có viết ra, nhưng nó không nằm
trên đường chạy"*), nên phải kiểm chứ không phải tin.

---

## 2. PHÁT HIỆN QUAN TRỌNG NHẤT — bar không đo được PMG khi lưới hẹp hơn nến

Đặc tả §5.1 cảnh báo *"sai số này lớn hơn cả edge"* và đòi tick data cho `h < 0.3 ATR`.
Câu hỏi thật không phải "h có nhỏ hơn 0,3 ATR không" mà là **"bước lưới có rộng hơn một
nến không"** — và câu đó đo được bằng số, trên chính chuỗi sắp chạy.

Đo trên random walk **không chi phí** (đáp án đúng: lãi ≈ 0):

| bước lưới / biên độ nến | số rổ | lãi | kết luận |
|---|---|---|---|
| 0,32 | 20.780 | **+1.544%** | ảo hoàn toàn |
| 0,54 | 10.450 | **+720%** | ảo hoàn toàn |
| 1,08 | 8.578 | −100% (cháy) | ảo |
| 2,16 | 1.269 | −48,9% | tạm |
| **3,24** | 971 | **−2,3%** | **đúng đáp án** |

Cơ chế của con số ảo: một bar chỉ nói O/H/L/C, nên mọi mô hình đường đi đều phải ghé
**cả hai cực trị**. Với lưới nghịch chiều, rổ mở ra ở cực trị thứ nhất luôn được tặng
không cú đảo chiều về cực trị thứ hai — mỗi nến một lần, miễn phí. Lưới càng hẹp so với
nến thì món quà đó càng lớn.

**Đã chặn bằng `NGUONG_PHAN_GIAI = 2.0`**: `mo_phong` trả `trang_thai = "CHUA_DO_DUOC"`
khi bước lưới < 2× biên độ nến trung vị. Ba trạng thái, không phải hai — theo đúng luật
của dự án.

Hai chỗ sửa kèm theo, cả hai đều là rò rỉ thật:
- **đường đi trong bar phải có ba chặng `O → X → Y → C`.** Bỏ chặng cuối thì mọi bar kết
  thúc ở một cực trị, và đó chính là nguồn của +327% ban đầu.
- **mức lưới kế tiếp phải tính từ MỨC LÝ THUYẾT, không từ giá khớp.** Một khe giá 97→80
  đáng lẽ khớp 6 tầng (94, 91, 88, 85, 82 đều nằm trong khe) chỉ khớp được 2, vì tầng kế
  tiếp bị dời theo giá khớp xuống 77.

### → Trả lời câu hỏi §9.1 của đặc tả (tick hay bar M1?)

**Bar M5 + ATR(H1) đo được `h ≥ 0,5–0,8` tuỳ tài sản. Hai mẫu tham chiếu M1 và M2 thì
KHÔNG, và không phải vì thiếu dữ liệu M1 — mà vì `h ≈ 0,05–0,15 ATR` của chúng nhỏ hơn
biên độ nến ở mọi khung ta có.** Muốn nghiên cứu đúng hai mẫu đó thì phải có tick; còn
miền `h` mà đặc tả muốn giãn ra (0,5–3,0 ATR) thì bar hiện có đủ.

Tỉ lệ đo được (bước lưới / biên độ nến M5, ATR H1):

```
XM_US100CASH   h × 4,65       EURGBP   h × 4,21       AUDCAD   h × 3,94
XAUUSDM        h × 4,37       US500CASH h × 4,53      XM_US500CASH h × 4,61
```
Tức `h ≥ 0,5` là đo được ở hầu hết, `h = 0,5` trên AUDCAD (1,97×) thì vừa trượt — và máy
tự gắn `CHUA_DO_DUOC` chứ không gắn `ÂM`.

---

## 3. Null của G0 phải là ĐẢO DẤU, không phải block bootstrap

Đặc tả §6.2 nói "sinh null bằng block-bootstrap và GBM". Làm đúng như vậy thì **G0 không
phát hiện được gì**, và đây là hai lần sai liên tiếp, cả hai đều đo được:

| null | ac1 của null | ER thật | ER null | kết luận trên chuỗi AR(+0,6) dựng sẵn |
|---|---|---|---|---|
| block bootstrap thuần | ~0,60 | 0,2011 | 0,2006 | null giữ luôn tự tương quan → **không phân biệt** |
| block + xáo trong khối | 0,03 | 0,2011 | 0,1910 | giết được ac1 nhưng **giữ trung bình của khối** → z = 0,7 |
| **đảo dấu ngẫu nhiên** | ~0 | — | — | **phân biệt được, p < 0,1** |

Lý do sâu: ER đo `|ΣΔP| / Σ|ΔP|`. Block bootstrap giữ nguyên *trung bình của khối*, mà
trung bình khối **chính là** tử số của ER khi khối dài bằng cửa sổ. Null nuốt đúng cái tín
hiệu đang đo.

Đảo dấu giải cả hai cùng lúc, và giải chính xác chứ không xấp xỉ: **mẫu số của ER không
đổi một chút nào** (giữ nguyên `|ΔP|` đúng từng vị trí thời gian, nên cụm biến động được
bảo toàn nguyên vẹn), chỉ tử số bị giết. Phép thử thành đúng một câu hỏi:
*với đúng đường biến động này, cái thứ tự dấu mà thị trường đã đi có cho ra net move khác
ngẫu nhiên không?*

`block` và `gbm` vẫn giữ lại làm bản đối chiếu (`kieu_null=`).

---

## 4. BẢN ĐỒ G0 — đầu ra số 1 của đặc tả (§7.1)

M5, ATR(H1), 200 chuỗi null, FDR-BH 10%, 48 ô, **392 giây**:

```
tài sản            0.1    0.2    0.3    0.5    0.8    1.2      2      3   qua FDR
AUDCAD               A      A      A      A      A      A      A      A     8/8
EURGBP               A      A      A      A      A      A      A      A     8/8
XAUUSDM              A      A      A      A      A      A      A      a     7/8
US500CASH            a      a      a      w      A      w      a      a     1/8
XM_US500CASH         a      a      w      A      a      w      a      a     1/8
XM_US100CASH         a      a      w      w      w      w      w      w     0/8
```
`A`/`W` = qua FDR · `a`/`w` = hướng đề xuất nhưng không qua FDR
**25/48 ô sống · 22 ô chết đã vào sổ loại trừ vĩnh viễn.**

Đọc được ba điều, và điều thứ ba phải đọc CHẶT:

1. **Cặp chéo FX hồi quy ở MỌI thang đo** (AUDCAD, EURGBP: 8/8 ô). Sạch và nhất quán.
   Khớp với thứ dự án đã biết từ trước về AUDCAD.
2. **Vàng cũng hồi quy**, 7/8 thang.
3. **Chỉ số thì gần như không có gì**: US500 và XM_US500 mỗi cái 1/8, **US100 là 0/8**.
   Có một XU HƯỚNG nghiêng về `WITH` ở US100 (6/8 thang có `huong_de_xuat` là WITH,
   thang mạnh nhất p = 0,09) và xu hướng đó **ngược dấu với FX** — nhưng **nó KHÔNG qua
   FDR**. Đây là một giả thuyết để quét lại, không phải một phát hiện. Ghi ra đây đúng
   để lần sau không ai đọc nó thành kết luận.

**Hạn chế phải nói rõ:** tầng A của đặc tả (§8.1) là US500 · UK100 · GER40 · XAUUSD.
Kho không có dữ liệu M5 cho **UK100 và GER40** — chỉ có D1. Hai tài sản đó hiện
`CHUA_DO_DUOC`, không phải `ÂM`.

---

## 5. Sáu chỗ đặc tả nói một đằng, toán đòi một nẻo

### 5.1 Điều kiện G1 tách làm hai, không phải một

Đặc tả §3.1: *"`tp_dist` phải > `D_BE` + chi phí toàn rổ"*. Đúng cho `anchor_return` và
`trail`, **sai cho `avg_plus`**: điểm thoát của `avg_plus` được định nghĩa TỪ giá vốn bình
quân, nên lãi mỗi đơn vị luôn bằng đúng `tp_dist` bất kể `D_BE` bao nhiêu. Ràng buộc thật
là `tp_dist > chi phí một vòng`.

Áp nguyên văn câu của đặc tả vào `avg_plus` sẽ **loại nhầm mọi cấu hình DCA sâu tầng** —
đúng cái mà mẫu tham chiếu M2 đang chạy thật. `kiem_g1` tách hai nhánh.

### 5.2 `tp_mode = anchor_return` + `direction = WITH` không bao giờ lãi

Đặc tả cho phép ghép tự do hai ô này. Nhưng với `WITH` các tầng nằm **phía sau** gốc lưới
theo hướng vị thế, nên "giá quay về gốc" là một khoản **lỗ chắc chắn**, không phải TP.
Đã loại ở G1 chứ không để nó ăn CPU.

### 5.3 `max_legs` KHÔNG phải một basket stop

Đặc tả xếp `max_legs` vào bảng §1.6 BASKET STOP. Nó là **trần phơi nhiễm**: chạm trần thì
ngừng thêm tầng, rổ vẫn mở. Cấu hình chỉ có `max_legs` mà không có `max_basket_dd` /
`time_stop` / `hard_sl_atr` là **martingale chờ chết** — đúng thứ §1.6 muốn cấm. G1 từ chối.

### 5.4 Mã định danh §8.7 KHÔNG duy nhất — và đặc tả bảo dùng nó làm khoá dedupe

Đặc tả §8.7 cho chuỗi:

```
PMG-{asset}-{session}-{atr_tf}-h{h}-{direction}-{step_mode}-{size_mode}-tp{tp_mode}-st{stop_mode}
```

Chuỗi đó **không phân biệt được `tp_dist`**, cũng như `size_r` và `step_g`. Hai cấu hình
khác hẳn nhau — `tp_dist = 0,5` và `tp_dist = 2,0` trên cùng một lưới — cho ra y hệt một
mã. Mà §8.7 lại nói: *"Hash rút gọn từ chuỗi này làm khoá dedupe. Bắt buộc, nếu không
QuantLab sẽ chạy trùng hàng nghìn lần."* Dùng nó làm khoá dedupe thì ta không chạy trùng —
ta **đánh rơi im lặng** mọi biến thể `tp_dist` trừ một cái.

Lỗ hổng này tự nó lộ ra: ngày 14/09 tôi dùng mã đó để dựng lại cấu hình duy nhất sống sót
của AUDCAD, đoán `tp_dist = 2,0` trong khi thật ra là `1,0`, và ra một kết quả khác hẳn.

Đã sửa: `ma_dinh_danh` thêm `tp_dist` (và `size_r` / `step_g` khi chúng có nghĩa). Khoá
dedupe THẬT vẫn là `van_tay()` — hash của toàn bộ dataclass — nên kho chưa bao giờ mất
cấu hình nào; chỗ hỏng chỉ nằm ở chuỗi cho người đọc. Có test chiều ngược: mọi cấu hình
trong lưới prereg phải có mã riêng.

### 5.5 So bốn hàm SIZE phải CHUẨN HOÁ ĐÒN BẨY, nếu không là so quy mô

Đặc tả §1.4 hỏi thẳng *"nếu flat không thắng thì mọi hàm tăng size chỉ là đòn bẩy trá
hình"*, và §7.3 đòi bảng so sánh bốn hàm ở cùng `h*`. Bảng đó chỉ trả lời được câu hỏi nếu
bốn hàm chạy ở **cùng phơi nhiễm đỉnh**:

```
geometric r=2, n=12  ->  tổng lot 4.095
flat n=12            ->  tổng lot 12          (chênh 341 lần)
```

Để nguyên thì ta đang so một cấu hình đòn bẩy 341× với một cấu hình đòn bẩy 1×, rồi kết
luận về "hình dạng hàm size". `sinh_cau_hinh` chia ngược `phoi_nhiem_1 = đòn_bẩy_đỉnh /
Σq_k`. Sau chuẩn hoá, chênh lệch giữa bốn hàm chỉ còn là **hình dạng phân bổ**.

(Đo 14/09 trên EURGBP M5 khi chưa chuẩn hoá: `flat` cháy tài khoản ở −98%. Đó không phải
kết luận về cơ chế, là kết luận về cỡ lot.)

### 5.6 "Bi quan" về thứ tự khớp KHÔNG có nghĩa là kết quả tệ hơn

Tên `bi_quan` mô tả **giả định về thứ tự khớp** (chạm cực trị bất lợi cho vị thế hiện có
trước), không mô tả kết quả. Và chiều của nó **đảo ngược theo `direction`**:

- `WITH`: chạm cực trị bất lợi trước = rổ breakout bị cản trước khi kịp nhồi thêm → đúng
  là bản tệ hơn.
- `AGAINST`: chạm cực trị bất lợi trước = **khớp sâu hơn, nhiều tầng hơn ở giá tốt hơn**,
  rồi cú hồi về mới ăn TP → bản này **lãi hơn**.

Đo 14/09 trên cấu hình AUDCAD duy nhất sống sót: `bi_quan` **+2,753%** còn `lac_quan`
**+0,199%** — chênh 14 lần, và bản mang tên "bi quan" là bản đẹp hơn. Đọc nhầm nó làm số
thận trọng thì một hệ bằng không thành một hệ có vẻ dùng được.

Đã thêm `lai_than_trong = min(hai bản)` và `ban_than_trong` vào `do_bat_bien`; cổng `song`
của phễu giờ đòi **bản thận trọng phải dương**, chứ không chỉ đòi "không lật dấu".

---

## 6. Cháy tài khoản — chốt engine phải có

Không có chốt này thì equity đi xuống âm và engine vẫn chạy tiếp; mọi số sau đó là số của
một tài khoản không còn tồn tại. Họ bot này dính đúng chỗ đó: `AGAINST` + tăng size là
đường thẳng tới nợ. `NGUONG_CHAY = 0,02` (2% vốn — sàn gọi margin call từ trước đó, và
tài khoản còn 2% thì không đặt nổi lot tối thiểu của bất kỳ cấu hình nào).

Đo trên EURGBP M5, `phoi_nhiem_1 = 1,0`, 13,5 năm: **cháy sau 3.322 rổ**.
Chi phí đo được: spread **0,816 bps** (`do_tin = SAN`), phí qua đêm **+2,62%/năm** chiều
mua và **−0,45%/năm** chiều bán.

Và kết quả khớp đúng lý thuyết của đặc tả §0: lỗ trung bình mỗi rổ ≈ **−1,3 bps** so với
chi phí một vòng ≈ **1,0 bps**. Tức **kỳ vọng = −chi phí**, không hơn không kém.

---

## 7. Sổ loại trừ và ngân sách phép thử (§8.5, §8.6)

- `reports/PMG_SO_LOAI_TRU.json` — mỗi ô chết một dòng. `ghi_loai_tru` **bắt buộc khai
  `cong`**, và chỉ `G0` mới đặt `vinh_vien = true`. Chết ở G0 là kết luận về **thị trường**
  (đóng vĩnh viễn được); chết ở G3 là kết luận về **engine** (mở lại được khi engine đổi).
  Trộn hai loại thì sổ mất giá trị, nên không cho phép ghi thiếu trường.
- `reports/PMG_BO_DEM_PHEP_THU.json` — **mọi cấu hình đã xét đều đếm, kể cả cấu hình bị
  loại ở G1**. Không đếm chúng thì số phép thử báo ở G5 nhỏ hơn sự thật và FDR thành dễ dãi.
- `LUOI_PREREG` có tên (`prereg_v1_2026_09_14`) và được ghi vào mọi kết quả quét. `h` của
  nó phải là tập con của `pmg_g0.CAC_H` — nếu không, `quet` tra hướng G0 của mức h đó,
  không thấy gì, rồi bỏ lặng lẽ cả cấu hình (đã sập đúng vậy với `h = 1.0`).
- `quet()` **từ chối cấp CPU cho ô chưa chạy G0**, và từ chối ô đã nằm trong sổ vĩnh viễn.

---

## 7b. Kết quả quét thật (G1→G4, ba ô, 14/09)

```
ô                  G0        G1                     G2 đo được   SỐNG
XM_US100CASH     0/8 qua   không cấp CPU (G0 phủ quyết)              -
AUDCAD           8/8 qua   giữ 120                  64/120           1
XAUUSDM          7/8 qua   giữ 64, BỎ 32 vô nghiệm  64/64            0
```

Cấu hình dẫn đầu theo LÃI là `h = 0,5` với **+22,16%** — và **cổng độ phân giải gắn nó
`CHUA_DO_DUOC`** (ở AUDCAD `h = 0,5` cho 1,97× biên độ nến, vừa trượt ngưỡng 2,0). Không
có cổng đó thì con số đẹp nhất của cả lần quét lại chính là con số ảo nhất.

Cái duy nhất qua G3 + G4:

```
PMG-AUDCAD-ALL-H1-h0.8-AGAINST-fixed-linear-tpavg_plus1-stdd0.03.t240.sl6.n12
  G3  thật +2,75%  vs  đảo dấu −0,06 · xáo khối −5,21 · GBM −9,64
  G4  ba giai đoạn +0,30% · +0,08% · +2,47%
  bất biến tie-break:  "bi quan" +2,753%  |  "lạc quan" +0,199%
```

**Bản mang tên "bi quan" lại là bản ĐẸP hơn** — xem §5.6. Số phải đọc là bản thận trọng:
**+0,199% / 13,5 năm = 0,015%/năm**. Mốc mua-giữ AUDCAD cùng kỳ là −0,44%/năm.

Đọc cho đúng: **cơ chế thật, và gần như bằng không về mặt tiền.** Bản `đảo dấu` là bản
yếu nhất trong ba placebo (−0,06%) trong khi `xáo khối` (−5,21%) và `GBM` (−9,64%) âm hẳn
— tức lưới này không sống bằng drift mà bằng **cấu trúc chuỗi** của chính AUDCAD, đúng thứ
G0 đã chỉ ra. Nó chỉ quá nhỏ để dùng.

---

## 8. Còn thiếu — việc của phiên sau

1. **G6 (MT5 single-run)** chưa nối. `TESTER = 1` là ràng buộc vật lý; PMG phải đi qua
   đường đã có (`chay_tester_kho.py`) chứ không mở đường thứ hai.
2. **Trục D2 (phiên)** đã dựng đủ (`bucket_phien`, `eod_flatten`, lọc `phien` trong engine
   và trong G0) nhưng **chưa quét**. Đặc tả nói kỳ vọng là WITH/AGAINST **đảo chiều theo
   phiên** — chưa kiểm.
3. **Trục D3 (scale)**: mới chạy `atr_tf = H1`. Cần M15/H4/D1. `atr_khung` đã hỗ trợ.
4. **UK100, GER40** — thiếu dữ liệu khung nhỏ. Việc của SEEKER, không phải của QuantLab.
5. **Tick data** cho miền `h < 0,3 ATR` (hai mẫu tham chiếu M1/M2). Chưa có.
6. ~~`do_bat_bien` chưa chạy trên cấu hình sống sót~~ — **đã chạy** (§7b), và nó lật cách
   đọc kết quả: xem §5.6. Việc còn lại là chạy nó cho *mọi* ứng viên vào G3, việc đó đã
   nối vào `pmg_quet.quet` nhưng lần quét 14/09 chạy bằng bản mã cũ hơn nên chưa có.

---

## 9. Trả lời năm câu hỏi §9 của đặc tả

| câu hỏi | trả lời |
|---|---|
| tick hay bar M1? | **bar M5 đủ cho `h ≥ 0,5–0,8`; cần tick cho `h < 0,3`** — đo được, xem §2. Và ngay trong vùng đo được, hai giả định thứ tự khớp vẫn chênh 14 lần (§5.6) — nên số phải đọc luôn là bản thận trọng |
| quét cả `WITH` lẫn `AGAINST`? | **Không cần quét cả hai** — G0 đã chỉ định hướng cho từng ô, và dấu **đảo ngược giữa FX và chỉ số**. Quét cả hai ở mọi ô là nhân đôi số phép thử để lấy thông tin G0 cho không |
| ngưỡng vốn để cắt config đòi margin cao | engine ghi `dinh_don_bay`, `von_toi_thieu` (= DD đỉnh × 1,5) và `chay_tai_khoan` cho mọi cấu hình. **Con số ngưỡng thì cần chủ dự án chốt** |
| 8 bucket phiên có đúng không | đã dựng theo **giờ sàn** (MT5 server = Europe/Helsinki, tự có DST) — không dùng offset UTC cố định. **Chưa quét, nên chưa biết bucket nào vô giá trị** |
| ngưỡng power tối thiểu (số rổ/năm) | engine ghi `ro_moi_nam`. **Cần chủ dự án chốt con số** |
