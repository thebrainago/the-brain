# THIẾT KẾ DÂY CHUYỀN NGHIÊN CỨU — bản gộp

*Chốt 2026-08-09 sau 5 vòng phản biện giữa Claude và DeepSeek V4.
Nguyên văn từng vòng: `reports/ds/THIET_KE_v1..v5_deepseek.md`,
`de_bai_thiet_ke.md`, `phan_bien_thiet_ke_v1.md`, `ban_luan_vong3..5.md`.*

> **Bài toán:** EURCAD tốn 2 ngày người mới ra kết luận đáng tin. Có hàng chục ý tưởng và
> 28+ thị trường. Cần chạy được quy trình 2-ngày-người đó tự động **mà không mất chất
> lượng**. Chạy 24/7 trên VPS 2 vCPU / 1-2 GB.

---

## Nguyên tắc xuyên suốt

**Cái gì không thể bác bỏ thì không phải khẳng định, chỉ là nhận xét.**
Mọi PASS phải có hạn dùng và biên an toàn; mọi kết luận âm tính phải có điều kiện để nó
sai; mọi dây chuyền phải có cách để nó lộ ra là đang hỏng.

**Rủi ro lớn nhất không phải một kết luận sai, mà là hàng trăm kết luận sai được sản xuất
cùng lúc, với bảng số đẹp và chữ ký "đã kiểm định".** Cái bào mòn thống kê không phải số
phép thử đã đếm, mà là những **quyết định nằm ngoài sổ**: chọn giả thuyết nào, chọn đoạn
dữ liệu nào, chọn bộ lọc nào, chọn cost model nào.

---

## 1. HAI LOẠI ALPHA — và loại thứ hai được ưu tiên cao hơn

Đây là kết luận có giá trị nhất của cả năm vòng, và nó sửa một thiên lệch của chính dự án.

| | Signal alpha | **Implementation alpha (alpha phép trừ)** |
|---|---|---|
| Phát biểu | "Tôi có dự báo về hướng giá" | "Tôi đã quyết định giữ exposure này, và tôi trả rẻ hơn X%/năm nhờ chọn đúng nơi giữ" |
| Cần backtest | có | **không** |
| Cần placebo / p-value | có | **không** |
| Tốn slot FDR | có | **không** |
| Độ chắc chắn | thấp | **cao** |

Tên của lỗi bỏ sót loại thứ hai: **signal myopia** (dạng streetlight effect). Dây chuyền
chỉ biết đánh giá thứ có hình dạng *tín hiệu → backtest → p-value* sẽ mù trước thứ có hình
dạng *cùng exposure, kênh này rẻ hơn kênh kia một khoản cố định*.

**Đã có sẵn hai phát hiện loại này và cả hai chưa tiêu:**

- Cùng phơi nhiễm SP500, phí giữ dài chênh **5,5 điểm %/năm** giữa các sàn — lớn hơn gần
  như mọi edge qua 324 phép thử.
- XM futures CFD swap = 0, rẻ hơn cash **1,2–2,7%/năm**.

**Module cần có: sổ chênh lệch chi phí triển khai**, chạy thường trực, không hỏi "có tín
hiệu không" mà hỏi *"nếu tôi đã giữ exposure này, kênh nào rẻ nhất bây giờ?"*

| Exposure | Kênh A | Kênh B | Chênh | Cơ chế | Điều kiện để sai |
|---|---|---|---|---|---|
| SP500 dài | sàn X 6%/năm | sàn Y 0,5%/năm | 5,5%/năm | phí cố định | Y đổi biểu phí; rủi ro đối tác tăng |

---

## 2. CỔNG PASS — neo vào mua-giữ, không neo vào hằng số

Ngưỡng tuyệt đối (`Sharpe > 1,0`, `maxDD < 25%`) **bị loại**: chúng loại mất chính V6
(Sharpe 0,95 đo trên MT5 thật) — thứ duy nhất dự án từng xác nhận.

Mốc chính là `buyhold_net` (mua-giữ CFD cùng danh mục, cùng kỳ, sau phí thật).
`buyhold_gross` (chỉ số không phí) chỉ để đọc, không làm điều kiện.

**PASS khi đồng thời:**

1. `net_return > buyhold_net_return`
2. `net_sharpe > buyhold_net_sharpe` — không phải do liều cao hơn
3. `net_calmar > buyhold_net_calmar` — không phải do ôm sụt giảm lớn hơn
4. `alpha_vs_buyhold > 0`, p ≤ ngưỡng — hồi quy lợi suất ròng lên `buyhold_net`, sai số
   chuẩn **Newey-West**. Đây là thứ chặn **đòn bẩy trá hình**: nếu chiến lược chỉ là
   mua-giữ phơi nhiễm đầy thì alpha ≈ 0 theo cấu tạo.
5. `placebo_p` ≤ ngưỡng, lấy **p xấu nhất trong ≥ 5 hạt** (verdict đã từng đổi theo hạt:
   95,8% với hạt 11 so với 94,8% với hạt 13)
6. `pre_registered = true` — nếu không, tối đa là `EXPLORATORY`, **không bao giờ** PASS

**Siết thêm khi `exposure` trung bình > 95%** (gần như luôn ở trong thị trường): alpha p và
placebo p ≤ 0,01, và phải có ít nhất một giai đoạn con dương. *Lý do: cơ chế VIX từng có
IC +0,106 dương ở cả 5 giai đoạn con nhưng placebo 10,2% — vì size trung bình 98-99% nên
nó gần như chính là mua-giữ.*

---

## 3. HAI TẦNG KIỂM SOÁT CHỌN LỌC — và chúng không thay nhau được

| | Xử lý | Chi phí |
|---|---|---|
| **SPA / White's Reality Check** | chọn lọc **trong một mẻ** — chọn 1 trong 324 cấu hình đã định trước | rẻ: bootstrap ma trận lợi suất chung 1 lần |
| **Null factory đầy đủ** | chọn lọc **theo thời gian** (adaptive search) + lỗi tầng dữ liệu và thực thi | đắt: chạy định kỳ, không cho từng chiến lược |

Bản đầu đòi null factory đầy đủ cho mọi PASS: 324 cấu hình × 28 thị trường × 100 hạt =
**907.200 lượt backtest ≈ 10,5 ngày** cho một họ. Cổng không ai qua nổi tương đương không
có cổng, chỉ khác là nó làm ta yên tâm. SPA rẻ hơn hai bậc và giải đúng bài toán đó.

**Điều kiện cài SPA:** mọi ứng viên trong một họ phải đánh giá trên **cùng một cửa sổ
ngoài mẫu** (`common_evaluation_window` khai báo trước). Cấu hình có `date_range` riêng chỉ
được nằm ở tầng khám phá, không dùng làm p-value chính thức.

### Null factory: cách sinh đúng

Bốc độc lập `F_gap`/`F_duration` là **sai** — chiến lược thật vào lệnh **cụm theo chế độ**
(V6 khai hoả khi IBS thấp, mà IBS thấp dồn vào giai đoạn biến động cao). Null i.i.d. không
cụm, nên nó sẽ **cấp giấy chứng nhận** cho đúng bẫy biến-động-cụm-lại — bẫy đã sập 3 lần
trong một buổi sáng 09/08.

Đúng: **stationary bootstrap trên chính chuỗi sự kiện vào lệnh**, giữ nguyên side/volume
trong block. Kiểm bằng KS-test: phân phối khoảng cách giữa các lệnh của null phải không
phân biệt được với thật.

### Adaptive search: không cứu được bằng cách gộp mẻ

Gộp 50 giả thuyết thành một mẻ chỉ làm *mẻ đó* hợp lệ với SPA; mẻ thứ hai vẫn sinh ra sau
khi nhìn mẻ thứ nhất. Đẩy vấn đề lùi một bước, không xoá.

Cách đúng: **p-value sạch + online FDR (LORD/LOND)**. Nhưng điều kiện không thể thiếu —
online FDR kiểm soát *chuỗi quyết định*, nó **không sửa được** một p-value tính trên chính
dữ liệu đã sinh ra giả thuyết. Không có p-value sạch thì online FDR chỉ là trang trí.

→ Tầng sinh giả thuyết dùng toàn bộ dữ liệu; tầng xác nhận dùng phần **chưa từng dùng để
sinh giả thuyết**.

---

## 4. PRE-REGISTRATION CƯỠNG CHẾ Ở TẦNG DỮ LIỆU

Không phải thủ tục giấy tờ — là ràng buộc kỹ thuật:

1. Mỗi giả thuyết có `analysis_plan` với `plan_hash`.
2. `plan_hash` ghi vào sổ **trước lần truy cập dữ liệu đầu tiên** trong phạm vi đó.
3. Chưa có hash hợp lệ → **tầng dữ liệu từ chối truy vấn**.
4. Đổi kế hoạch sau khi đã chạm dữ liệu → hash đổi → vĩnh viễn `EXPLORATORY`.

Máy tự sinh giả thuyết cũng **không tự mở khoá dữ liệu** trước khi đóng băng kế hoạch.
Đây cũng là lớp bắt **chạy chui** — một backtest không khai báo — chứ không chỉ bắt sửa file.

---

## 5. PHI DỪNG THEO THỜI ĐẠI

Bài học đắt nhất: **IBS chỉ sống sau 2005**; trên 64 năm CAGR **−0,08%**, sụt giảm **−86%**.
Walk-forward hai nửa không bắt được vì cả hai nửa cùng một thời đại.

- Danh sách mốc cấu trúc **đăng ký trước, người duyệt**: 1971, 1987, decimal hoá 2000-01,
  ETF phổ biến, 2008, HFT, lãi suất 0.
- Edge chỉ sống sau một mốc → `REGIME_LOCKED`, chỉ PASS được nếu: có cơ chế kinh tế viết
  ra, có dữ liệu ngoài mẫu **sau khi phát hiện** xác nhận, và không mốc nào khác chia tách
  làm edge biến mất.
- **Quarantine window** cho dò đứt gãy không giám sát: tầng khám phá chỉ quét
  `train_window`; T cố định từ train, kiểm trên `holdout_window`, **không ước lượng lại T
  trên holdout**.

**Máy không phân biệt được ảo giác khai thác dữ liệu với thay đổi cấu trúc thật — số liệu
giống hệt nhau.** Đây là một trong hai điểm bắt buộc cần người.

Và một điểm sáng: nếu mốc nằm trong holdout, ta sẽ không *đặt tên* được cho nó, nhưng vẫn
thấy edge sống sót ngoài mẫu — **đó mới là thứ cần để quyết định. Gán mốc là câu chuyện
lịch sử, không phải điều kiện PASS.**

---

## 6. HẠN DÙNG BẤT ĐỐI XỨNG THEO HẬU QUẢ

**PASS là tuyên bố về tiền** — sai thì mất tiền ngay. Hết hạn theo chất lượng:

| Hạng | Điều kiện | Hạn |
|---|---|---|
| A | biên lật > 50%, placebo p < 0,01, có cơ chế, đã qua ≥1 lần tái kiểm | 12 tháng |
| B | biên lật 20-50% | 6 tháng |
| C | biên lật < 20% hoặc chưa tái kiểm lần nào | 3 tháng |

**Kết luận âm tính là tuyên bố về sự vắng mặt** — sai thì chỉ mất cơ hội.
Trạng thái `CLOSED_UNLESS_TRIGGERED`, **không hết hạn theo đồng hồ**, nhưng bắt buộc kèm
**điều kiện để nó sai** viết theo *lớp sự kiện*, không theo ngày:

> *"Không có edge trên X vì chi phí vượt edge"* → điều kiện sai: môi giới mới spread < ngưỡng.

Trigger xuất hiện → `REOPENED_EXPLORATORY`, đi lại từ đầu. Không có "mở lại coi như cũ".

Tái kiểm là **bảo trì, không phải khám phá** → dùng lịch tiêu alpha định trước
(Lan-DeMets), **không cộng vào FDR của khám phá mới**.

---

## 7. CHI PHÍ BẢO TRÌ KHÔNG ĐƯỢC NUỐT CHI PHÍ KHÁM PHÁ

Mọi kết luận hết hạn theo quý + mỗi lần đổi cost model quét lại toàn bộ = sau 2 năm máy chỉ
còn bảo trì quá khứ. **Chết chậm, không báo lỗi.**

- **Định mức CPU cứng** (ví dụ 70% khám phá / 30% bảo trì). Bảo trì vượt thì xếp hàng
  thành "nợ bảo trì", ưu tiên theo rủi ro — biên mỏng và sắp hết hạn làm trước. **Khám phá
  không bị chặn.**
- **Lưu vector độ nhạy theo TỪNG thành phần chi phí** (spread / commission / swap /
  slippage / phí tối thiểu), không phải một số vô hướng. Δmetric ≈ Σ (∂metric/∂c_j) × Δc_j.
- **Đổi tham số** cost model → dùng độ nhạy, chỉ tái kiểm cái lung lay.
  **Đổi cấu trúc** cost model (spread hằng số → spread theo biến động) → gradient vô hiệu,
  bắt buộc quét toàn bộ.
- Hai cấp: **consistency check** (tính lại PnL trên chuỗi lệnh đã lưu, ~0,1% chi phí
  backtest) trước, chỉ khi kết quả dịch gần ngưỡng mới chạy full backtest.

---

## 8. TOÀN VẸN SỔ — chống chối bỏ, không chống truy cập

Mô hình đe doạ đúng: **kẻ địch không phải người ngoài, mà là chính mình lúc 3 giờ sáng
đang muốn một kết quả đẹp.** HMAC với khoá nằm trên chính máy đó là vô nghĩa.

- Sổ **chỉ-thêm** + chuỗi hash — giữ, vì rẻ; mục đích là làm việc sửa lặng lẽ tốn công hơn.
- Tiến trình chết giữa chừng → `RUNNING`; khởi động lại chuyển hết thành
  `FAILED_INCOMPLETE`. **Không bao giờ là PASS.**
- Chạy lại cùng `params_hash` với dữ liệu mới → **thêm dòng mới**, dòng cũ trỏ
  `superseded_by`. Không ghi đè.
- Mọi thay đổi qua git commit có lý do. Không rebase, không force-push.
- **Báo cáo tuần tự động**: *"tuần này có N dòng bị sửa hồi tố"*, chỉ dismiss được sau khi
  đã bung ra xem.

---

## 9. GIỮ NGƯỜI TRONG VÒNG LẶP — giảm SỐ LƯỢNG cần duyệt, không giảm thời gian duyệt

Người là tài nguyên khan hiếm nhất — đó chính là lý do sinh ra đề bài này. Sinh 40 giả
thuyết/ngày thì người sẽ bấm đồng ý hàng loạt: cổng mất tác dụng mà vẫn giữ hình thức.

- Chỉ trình lên thứ đã qua cổng tự động **và** có cơ chế rõ ràng. Còn lại vào kho
  `EXPLORATORY`, không cần nhìn.
- **Quá nhiều PASS trong một ngày là tín hiệu HỎNG, không phải tin vui** — đó là tín hiệu
  từ null factory, phải kiểm dây chuyền trước khi duyệt tiếp.
- **Gom cụm**: cùng template, cùng tài sản, cùng cơ chế, chỉ khác tham số nhỏ → trình một
  đại diện. Chỉ tách ra khi có cái nằm ngoài phân phối của các anh em.
- Màn hình duyệt phải cho thấy trong 60 giây: **một câu mô tả cơ chế** (không phải danh
  sách tham số) · net return so với mua-giữ · alpha t-stat · placebo p · một đồ thị vốn so
  với mua-giữ · nút Duyệt/Loại.
- Không phản hồi = `PENDING`. **Không bao giờ tự động duyệt.**

---

## 10. QUY TẮC DỪNG

Không phép kiểm định nào chứng minh được "không có edge". Nhưng có quy tắc **tính được** —
đây là quyết định kinh doanh, không phải kiểm định:

```
Lịch sử: 324 + 914 + 520 = 1.758 phép thử, 0 thành công
Rule of three → chặn trên 95% của tỷ lệ thành công ≈ 3/1758 ≈ 0,0017

V = giá trị kỳ vọng của một chiến lược tốt (một năm)
C = chi phí toàn phần một lần tìm kiếm (tính toán + thời gian + vốn cơ hội)

TIẾP TỤC nếu  0,0017 × V > C     — ngược lại DỪNG
```

Không hoàn hảo (các phép thử không độc lập, không cùng phân bố) nhưng nó **biến cảm giác
nản thành một biểu thức kiểm tra được**.

**Phân biệt ba trường hợp dẫn tới ba hành động ngược nhau:**

| | Chẩn đoán | Hành động |
|---|---|---|
| (i) không có edge | meta-analysis trên toàn bộ phân phối thống kê đã thu; khoảng tin cậy loại trừ mọi effect có ý nghĩa kinh tế | dừng hẳn |
| (ii) thiếu lực | khoảng tin cậy vẫn chứa effect đáng giá | tăng mẫu — nhưng quy tắc dừng vẫn áp dụng |
| (iii) nhìn sai chỗ | kết quả cực nhạy với giả định vi cấu trúc (giá khớp, trượt giá, nhìn trước) | đổi bề mặt đo |

**Cảnh báo:** nếu không có cơ chế cụ thể nói rằng edge *nên* nằm ở đâu, thì "đổi bề mặt"
chỉ là **di chuyển máy đánh bạc**.

Và dừng phải định nghĩa theo **bề mặt tìm kiếm**: dừng "OHLCV ngày trên 21 thị trường"
≠ "thị trường không có edge". Nó nghĩa là *"với phương pháp này, trên bề mặt này, giá trị
kỳ vọng của việc tiếp tục không còn dương"*.

---

## 11. NGƯỠNG PHẢI SUY RA TỪ HÀM MẤT MÁT, KHÔNG PHẢI TỪ 0,05

0,05 là **mặc định của giới học thuật, không phải chân lý**. Chủ dự án khai báo ba con số
**một lần**, hệ tự suy ra mọi ngưỡng:

1. Một chiến lược thật sự tốt, sau chi phí, đáng bao nhiêu **một năm**?
2. Một chiến lược vô dụng lọt qua gây thiệt hại bao nhiêu **một năm** (gồm VPS, spread,
   thời gian)?
3. Trước khi thấy kết quả: xác suất một ý tưởng ngẫu nhiên trong không gian này là tốt?

**Ngân sách học phí (tuition budget)** — cách cấu trúc để hệ không mắc kẹt ở "không bao giờ
nói có":

- **Khai thác**: vốn thật, FDR thấp, chỉ chạy khi kỳ vọng dương rõ ràng.
- **Thăm dò**: một khoản nhỏ khai báo trước là **tiền học phí**, đánh giá bằng **mức độ cập
  nhật niềm tin**, không bằng lãi lỗ.

Và phân biệt hai trường hợp "không nói có":
- placebo FDR **đúng** target mà khám phá thật bằng 0 → "không" là câu trả lời đúng, không
  được hạ chuẩn.
- placebo FDR **thấp bất thường** (từ chối cả placebo lẫn thật) → lỗi hiệu chuẩn, phải sửa.

---

## 12. SỨC KHOẺ DÂY CHUYỀN — không đo bằng "số PASS"

| Tầng | Đo gì | Hỏng khi |
|---|---|---|
| **Placebo FDR** | tỷ lệ placebo vượt toàn bộ cổng | lệch khỏi target (target 5%, thực 12% → đang sản xuất phát hiện sai) |
| **Sai số ngoài mẫu chuẩn hoá** | z = (OOS thực − dự báo)/sd, gộp cửa sổ trượt 3 tháng | phân phối không xấp xỉ N(0,1) → ước lượng sai độ không chắc chắn |
| **Hiệu chuẩn nhóm live** | % chiến lược đã chạy có kết quả ngoài khoảng dự báo 95% | > 5% (lạc quan) hoặc << 5% (nghi ngờ) |

**Mutation audit hằng tháng:** cố tình chèn lỗi đã biết (`close[i]` thay `open[i+1]`, đảo
dấu phí, spread âm) và kiểm tra dây chuyền có gào lên không. **Không gào = các dây bẫy
không hoạt động** — hệ đang "bận rộn" chứ không "khoẻ".

**Ca cố định bắt buộc: point-in-time test** — dịch `close` lên một bar. Nếu dây chuyền
không báo động thì mọi kết luận phía sau vô nghĩa và **không SPA nào cứu được**. Đây là lỗi
nguy hiểm nhất vì nó âm thầm tạo ra alpha giả — đúng loại alpha "quá đẹp để là thật".

Một hệ lành mạnh **hiệu chuẩn tốt kể cả khi tìm được ít edge**: dự báo "Sharpe 0,4 ± 0,3"
rồi thực tế ra 0,45 là **thành công của dây chuyền**, dù chiến lược đó tầm thường.

---

## 13. MÔ PHỎNG — một khai báo, hai backend

Chiến lược khai báo bằng **template + tham số** (YAML), không sinh mã tuỳ ý. Mỗi template
có **hai bản cài đặt song ngữ**: Python (quét tham số) và MQL5 EA (MT5 Tester).

**Conformance test là hạ tầng bắt buộc, không phải tuỳ chọn**: cùng dữ liệu, cùng tham số,
hai bên phải cho cùng tín hiệu và cùng lệnh trong sai số cho phép. Lệch → template không
được dùng, và **mọi kết quả trên cả hai backend đều không đáng tin**.

Thứ tự chạy (quy tắc 14 của dự án — tester trước, Python sau):

```
giả thuyết mới → sinh EA → MT5 smoke test 1-5 cấu hình đại diện
   → PF/Sharpe tệ thì BỎ, không chạy Python sweep
   → tạm ổn thì Python sweep rộng thăm dò tham số
   → top config → MT5 final → đối chiếu hai bên
```

MT5: **chỉ chấp nhận every-tick / real ticks**; thiếu `tester_model` → tự động loại.
**Tắt swap trong tester**, Python cộng chi phí từ `cost_model` (vì tester áp mức swap hôm
nay cho cả lịch sử).

**TP/SL cùng bar:** dùng **open của chính bar đó để đoán** (gần TP hơn → TP trước).
KHÔNG mặc định SL chạm trước — thận trọng có hệ thống vẫn là số sai, và nó giết đúng loại
edge mỏng đang tìm. *(Bài học: giả định spread 9 bps thay vì 0,7 là "thận trọng gấp 12
lần" và đã giết oan cả loạt chiến lược.)*

---

## 14. TẦNG DANH MỤC — cấm optimizer

Ghép V6 với Session vàng (tương quan +0,03) cho Calmar 0,75 — **cấu hình đầu tiên của dự
án vượt mua-giữ vàng**. Giá trị nằm ở chỗ ghép.

Nhưng cái chặn nó thành cuộc dò tham số thứ hai **không phải sức mạnh tính toán**, mà là
**không cho phép tối ưu hoá trọng số trên dữ liệu lịch sử**:

- Danh mục chỉ tạo từ chiến lược đã PASS đơn lẻ.
- Trọng số dùng quy tắc cố định **đăng ký trước khi xem tương quan**: equal weight /
  inverse-vol / equal risk contribution. **Không dùng optimizer.**
- Muốn thử nhiều quy tắc → liệt kê trong `analysis_plan` trước; mỗi quy tắc là một giả
  thuyết riêng chịu FDR.
- **Kelly fraction vẫn là một tham số.** Chọn `f = 0,5` sau khi nhìn kết quả cũng là khai
  thác dữ liệu, bất kể Kelly là toán đã chứng minh. Sizing thuộc về hypothesis, không phải
  tiện ích có sẵn.
- Tương quan tính trên dữ liệu **của chính công cụ sẽ giao dịch** — V6 nikkei-sp500 là
  0,17 trên bar chỉ số tiền mặt nhưng **0,58** trên bar CFD 24h của XM.

---

## 15. SỨC CHỨA — chiều nối research với live

Chiến lược PASS với giả định trượt giá cố định có thể không còn đúng khi vốn tăng: lệnh lớn
tự đẩy giá. Cần **scale-aware validation**: ước lượng độ sâu thanh khoản, tính trượt giá
như hàm của quy mô lệnh. Ở quy mô dự kiến mà không còn vượt mua-giữ → `CAPACITY_CONSTRAINED`.

---

## 16. LỆCH NGHIÊN CỨU ↔ THỰC TẾ

| Mô phỏng (có phân phối, ước lượng được) | Chỉ giám sát (không lường trước) |
|---|---|
| requote, khớp một phần, trượt giá, spread đổi, swap đổi, gap qua SL | mất kết nối VPS, sàn đổi spec giữa chừng, đình trệ |

Mô phỏng loại thứ hai **tạo cảm giác kiểm soát được trong khi thực tế vẫn bất ngờ** →
thuộc về reconciliation và kill switch.

**Đối chiếu tài khoản thật:** `magic` chứa mã chiến lược, `comment` chứa `attempt_id`.
Khớp lệnh theo `symbol + side + attempt_id + volume`; dự phòng theo thời gian ±60s.
**CUSUM** trên residual chuẩn hoá → `WARN` (dừng mở lệnh mới) → `CRITICAL` (halt).

**EA gọi WebRequest ra ngoài là lỗi kiến trúc, không phải lỗi mô phỏng.** Mọi thông tin ra
ngoài phải qua proxy được kiểm soát.

---

## 12b. CANARY — đã dựng và đã chứng minh là nhạy (`canary.py`)

Ngày 09/08 engine mắc **hai lỗi nghiêm trọng** và cả hai chỉ bị bắt vì **con số quá đẹp**,
tức bằng trực giác của người. Nếu kết quả là 16/28 thay vì 24/28 thì cả hai đã lọt.
Trực giác không phải cổng.

| Canary | Kỳ vọng tính được bằng tay | Bắt lỗi gì |
|---|---|---|
| luôn mua 100% | **bằng đúng** mua-giữ CFD (sai số 1e-9) | kế toán chi phí, cách ghép vị thế với lợi suất |
| luôn bán 100% | `−lợi suất thô − phí giữ − spread` | **phí qua đêm bất đối xứng** (lỗi thật #1) |
| đứng ngoài | **bằng đúng 0** | chi phí bị áp cho vị thế rỗng |
| trễ 1 bar: `sign(close[i-1]−open[i-1])` | alpha ≈ 0, \|t\| < 4 | **lệch độ trễ / nhìn trước** (lỗi thật #2) |
| biết trước: `sign(r[i])` | alpha **khổng lồ**, t > 20 | engine không nối vị thế với lợi suất |

Canary cuối quan trọng ngang các cái khác: nếu perfect-foresight **không** cho alpha khổng
lồ thì engine đứt dây, và **mọi kết quả âm tính đều vô nghĩa**.

**Canary phải tự chứng minh là nhạy** (`canary_kiem_do_nhay.py`): chèn lại đúng hai lỗi
thật rồi kiểm. Lần đầu canary "trễ 1 bar" **trượt 0/8** — nó tự có sẵn hai bar trễ nên lệch
một bar của engine không chạm tới. Viết lại đặt đúng biên một bar thì bắt **8/8**, và lỗi
hiện ra dưới dạng **alpha +214%/năm, t = +48**.

> Bài học: một bộ canary chưa từng bắt được lỗi nào thì không biết nó có tác dụng hay không.

### Hai con số hiệu chuẩn rút ra được

- **Phí qua đêm bất đối xứng** (chỉ tính cho chiều mua) tặng **~2%/năm** alpha giả cho mọi
  chiến lược có chiều bán — chiếm **63%** của "edge" quan sát được trong ca thật.
- **Lệch một bar** tặng **+26,8 điểm phần trăm/năm**: t trung vị nhảy từ **−0,74** lên
  **+10,05**, số thị trường có t > 2 nhảy từ **0/28** lên **25/28**.

→ **Ngưỡng báo động dùng được ngay:** trên tập sàng này, bất kỳ chiến lược nào cho **t > 5**
phải được giả định là có nhìn trước cho tới khi chứng minh ngược lại. Không có thứ thật nào
trông như thế.

---

## THỨ TỰ THI CÔNG

| # | Module | Vì sao thứ tự này |
|---|---|---|
| 0 | `schema_common.py` | không có schema chung thì validator viết không được |
| 1 | `brain_validator.py` | **thử ngay bằng V6 và 324 lần chạy cũ — cổng nào loại mất V6 là cổng sai** |
| 2 | `brain_null_factory.py` | kiểm chính dây chuyền; chạy được trên dữ liệu giả trước khi có simulator |
| 3 | `brain_chenh_lech_chi_phi.py` | **alpha phép trừ — chắc ăn nhất, không cần cổng nào** |
| 4 | `brain_sim_py.py` | bản tối thiểu: OHLCV ngày, `open[i+1]`, TP/SL đoán bằng open |
| 5 | `brain_sim_mt5.py` | chỉ sau khi Python đạt conformance với một template song ngữ |
| 6 | `brain_claim.py` | nguồn cấp — chạy trước validator chỉ làm tăng số giả thuyết, không tăng khả năng xét đúng sai |
| 7 | `brain_recon.py` | cuối, nhưng schema định nghĩa ngay ở bước 0 |

**Không có cổng thì simulator chỉ giúp sản xuất số sai nhanh hơn.**

---

## BA CON SỐ CẦN CHỦ DỰ ÁN TRẢ LỜI

Không ai khác trả lời thay được, và mọi ngưỡng trong tài liệu này suy ra từ chúng:

1. Một chiến lược thật sự tốt, sau chi phí, đáng bao nhiêu **một năm**?
2. Một chiến lược vô dụng lọt qua gây thiệt hại bao nhiêu **một năm**?
3. Trước khi thấy kết quả: xác suất một ý tưởng ngẫu nhiên trong không gian này là tốt?
