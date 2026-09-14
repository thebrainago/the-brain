# PMG — Position Management Grid Engine
### Đặc tả cơ chế để QuantLab nghiên cứu
Phiên bản 0.2 — 2026-09-14 · **do chủ dự án đưa vào qua LUỒNG ƯU TIÊN, xếp thẳng vào module QUẢN LÝ LỆNH**

> Bản này là NGUYÊN VĂN đặc tả chủ dự án đưa. Phần triển khai, những chỗ đặc tả
> nói một đằng mà toán học đòi một nẻo, và những gì đã đo được nằm ở
> `tai_lieu/PMG_TRIEN_KHAI.md`. Không sửa file này khi đổi code.

---

## 0. Nguyên tắc đặt vấn đề

Đây **không phải một chiến lược**. Đây là một **engine quản lý vị thế** không có điều kiện entry.
Vì không có entry signal, kỳ vọng của nó dưới giả thuyết random walk bằng đúng `−chi phí`.

→ Suy ra: engine chỉ có thể sinh lợi nếu **quá trình giá có bất đối xứng thật ở đúng timescale của bước lưới**.
→ Suy ra: **không test bot trước. Đo tính chất của quá trình giá trước.** (xem §6 — Pre-test, chi phí gần bằng 0, loại được cả họ chiến lược)

Đặc tả này viết theo dạng **tham số hoá**, không phải hai bot rời rạc, để QuantLab quét bản đồ không gian giả thuyết thay vì test từng card (hướng B đã chốt 2026-08-18).

**Đa tài sản mặc định.** Mọi tham số khoảng cách đều biểu diễn theo bội số ATR, không theo điểm tuyệt đối — bắt buộc, do lỗi price-scale đã ghi nhận. Bộ tài sản tối thiểu: US500, UK100, GER40, XAUUSD, và 1 FX major để có mẫu đối chứng khác lớp tài sản.

---

## 1. Kiến trúc engine — 7 khối tham số

Mọi biến thể của họ bot này (kể cả 2 mẫu đã bóc) đều là một điểm trong không gian 7 chiều dưới đây.

### 1.1 ANCHOR — gốc lưới
| Tham số | Miền giá trị |
|---|---|
| `anchor_mode` | `static` (cố định đến khi rổ đóng) / `trailing` (bám giá, re-anchor khi giá rời gốc > `reanchor_dist`) / `session` (reset đầu phiên) |
| `reanchor_dist` | 0.25 – 2.0 × ATR(period) |
| `arm_time` | 24/7 / chỉ phiên chỉ định / loại trừ cửa sổ tin |

### 1.2 DIRECTION — chiều nhồi
| Giá trị | Mô tả |
|---|---|
| `WITH` | Nhồi thuận xu hướng — buy stop trên, sell stop dưới. Cược vào **trend persistence**. |
| `AGAINST` | Nhồi nghịch — buy limit dưới, sell limit trên. Cược vào **mean reversion**. |
| `BOTH` | Hai lưới độc lập chạy song song, hedge nhau. |

> **Cảnh báo từ kết quả cũ:** ghép cơ chế DCA (`AGAINST`) lên setup momentum/breakout đã test và xác nhận thảm hoạ (−17,000 pt). Trong đặc tả này `DIRECTION` là **biến độc lập bắt buộc quét**, không được mặc định — và không được trộn hai chiều trên cùng một rổ trừ khi `BOTH` với hai rổ tách bạch hoàn toàn về kế toán.

### 1.3 STEP — hàm khoảng cách giữa các tầng
`h_k` = khoảng cách từ tầng k đến tầng k+1.

| `step_mode` | Công thức |
|---|---|
| `fixed` | `h_k = s × ATR` |
| `expanding` | `h_k = s × ATR × g^k`, g ∈ [1.0, 1.6] — giãn dần khi đi xa, giảm số leg ở đuôi |
| `vol_adaptive` | `h_k = s × ATR_t` tính lại tại thời điểm đặt lệnh |

Miền quét `s`: **0.1 – 3.0 × ATR**. (Mẫu bóc được nằm ở ~0.05–0.15 ATR — đầu cực thấp của miền. Yêu cầu của Mr Vanh là giãn ra; miền này bao trùm cả hai chế độ.)

### 1.4 SIZE — hàm khối lượng theo tầng
| `size_mode` | `q_k` | Ghi chú |
|---|---|---|
| `flat` | `q_0` | Baseline bắt buộc. Nếu flat không thắng thì mọi hàm tăng size chỉ là đòn bẩy trá hình. |
| `linear` | `q_0 × (k+1)` | Mẫu M2 |
| `geometric` | `q_0 × r^k`, r ∈ [1.2, 2.0] | Mẫu M1 (r=2, mỗi tầng 2 lệnh) |
| `inverse` | `q_0 / (k+1)` | Chiều ngược — giảm size khi đi xa. Chưa thấy ai làm, phải test vì nó là biến thể duy nhất có đệm giá vốn tăng theo số tầng. |

### 1.5 BASKET EXIT — chốt rổ
| Tham số | Miền |
|---|---|
| `tp_mode` | `avg_plus` (giá vốn bình quân + d) / `money` (đạt X% equity) / `trail` (trailing từ đỉnh lãi rổ) / `anchor_return` (giá quay về gốc lưới) |
| `tp_dist` | 0.1 – 2.0 × ATR |
| `trail_giveback` | 10 – 60 % lãi đỉnh |

### 1.6 BASKET STOP — điều kiện cắt rổ (KHÔNG ĐƯỢC BỎ TRỐNG)
| Tham số | Miền |
|---|---|
| `max_legs` | 3 – 40 |
| `max_basket_dd` | 0.5 – 8 % equity |
| `time_stop` | 15 phút – 3 ngày |
| `hard_sl_atr` | khoảng cách từ gốc lưới, 2 – 15 × ATR |

> Mẫu M2 (video XAUUSDc) **có cắt lỗ thật** — số dư giảm từ 33,811 → 33,249 USC. Đây là điểm phân biệt duy nhất giữa "engine" và "martingale chờ chết". Cấu hình không có BASKET STOP bị loại ngay, không cần test.

### 1.7 RE-ARM — tái vũ trang sau khi đóng rổ
`immediate` / `cooldown_bars(n)` / `require_anchor_move(x×ATR)`

---

## 2. Hai mẫu tham chiếu (điểm neo trong không gian tham số)

| | **M1 — Straddle Pyramid** | **M2 — Adaptive DCA Basket** |
|---|---|---|
| Nguồn | USTEC_x100, MT5 mobile | XAUUSDc, Exness cent |
| DIRECTION | `WITH` | `AGAINST` |
| STEP | fixed, 1.5 pt ≈ 0.05 ATR(M1) | vol_adaptive, 2.6–9.7 USD, không đều |
| SIZE | geometric r=2, mỗi tầng ×2 lệnh, 0.01→5.12 | linear, 0.01→0.08 |
| Tổng exposure nếu quét hết | ~20.4 lot/bên | 0.36 lot |
| ANCHOR | trailing, re-anchor liên tục | static theo rổ |
| BASKET STOP | không quan sát được | có, xác nhận qua balance giảm |
| Cược vào | trend persistence ở scale rất nhỏ | mean reversion + vol clustering |

---

## 3. Toán học bắt buộc kiểm chứng trong code

### 3.1 Khoảng cách hoàn vốn của rổ
Giá vốn bình quân cách **lệnh cuối cùng** một khoảng:

```
D_BE = h × Σ(k · q_k) / Σ(q_k)     , k = 0 tại lệnh mới nhất
```

Kết quả đóng:
- `geometric r=2` → **D_BE = h** (đúng 1 bậc, bất kể n bao nhiêu tầng)
- `linear`, n tầng → `D_BE = h·(n·Σk − Σk²)/Σk`; n=8 → **2.33 h**
- `flat`, n tầng → **(n−1)h / 2**
- `inverse` → tăng theo n

**Đây là biến quyết định sống chết.** `tp_dist` phải > `D_BE` + chi phí toàn rổ, nếu không rổ không bao giờ có đường thoát dương. Assert điều kiện này ở thời điểm sinh cấu hình — loại config vô nghiệm **trước khi** tốn CPU backtest.

### 3.2 Ràng buộc chi phí
```
Điều kiện cần:  N_legs × cost_per_leg  <  Σ q_k × (giá thoát − giá vốn BQ)
```
với `cost_per_leg = spread_thực + slippage + commission`, và swap × số đêm nếu rổ qua đêm.
Chi phí phải nạp từ đầu bằng spread Exness thực đo, không dùng hằng số.

Số leg tỉ lệ nghịch bình phương bước lưới: `E[N_legs] ≈ σ²T / h²`.
→ **Giãn bước lưới gấp đôi thì số lệnh giảm 4 lần, chi phí giảm 4 lần.** Đây chính là điều Mr Vanh đề xuất, và nó đúng về mặt bậc độ lớn. Nhưng lợi nhuận mỗi vòng chỉ tăng tuyến tính theo h. Nên tồn tại `h*` tối ưu — tìm `h*` là một trong hai đầu ra chính của nghiên cứu này.

### 3.3 Vốn và margin
Ghi lại cho mọi config: peak exposure, margin đỉnh, equity DD đỉnh, và **vốn tối thiểu để không bị margin call ở kịch bản xấu nhất trong mẫu × 1.5**. Config nào cần vốn vượt ngưỡng thực tế thì loại dù PnL đẹp.

---

## 4. Khung lý thuyết — tại sao cơ chế này có thể có nghĩa

Lưới nhồi rời rạc là một **phép sao chép động (dynamic replication)** của một vị thế phi tuyến:

- `DIRECTION = WITH` ⇒ tổng hợp một **long straddle**: mất tiền đều đặn khi giá đi ngang, thắng lớn khi giá chạy. Chi phí sao chép = phí giao dịch = "phí quyền chọn" phải trả.
- `DIRECTION = AGAINST` ⇒ tổng hợp một **short straddle**: thu phí đều đặn, chết khi có cú chạy dài.

Kết quả chuẩn của lý thuyết sao chép: **lãi ≈ (biến động thực tế đã hiện thực) − (biến động ngầm định trong chi phí lưới)**.

→ Phát biểu chính xác của điều kiện có edge:

> `WITH` có lãi khi và chỉ khi giá **đi xuyên các bậc lưới có hướng** nhiều hơn mức một random walk cùng biến động sẽ làm.
> `AGAINST` có lãi khi và chỉ khi ngược lại.

Cái Mr Vanh thấy hay ở việc "nhích từng xu lẻ" chính là điều này: nó biến một **quyết định vào lệnh rời rạc** thành một **hàm exposure liên tục theo giá**. Đó là giá trị thật của cơ chế, và nó có tên trong lý thuyết. Nhưng cùng lý thuyết đó cũng nói rõ cái giá phải trả, và cho ta một bài test rẻ tiền ở §6.

---

## 5. Giao thức kiểm định (theo chuẩn pass hiện hành)

| Bước | Nội dung | Tiêu chí loại |
|---|---|---|
| G0 | Pre-test tính chất quá trình giá (§6) | ER không khác random-walk null ở mức FDR-BH 10% → **loại toàn bộ họ chiến lược trên tài sản/timescale đó** |
| G1 | Assert điều kiện §3.1 và §3.2 | Config vô nghiệm → loại trước khi backtest |
| G2 | Backtest full cost, toàn bộ dữ liệu | < 2 giao dịch rổ/tuần; lãi TB rổ < 5 pt sau phí |
| G3 | Placebo — chạy engine trên giá đảo dấu, giá shuffle theo block, và giá tổng hợp GBM cùng σ | Không tách khỏi placebo → loại. **Bước này quan trọng nhất với họ bot này** vì engine không có entry, nên nó cực dễ ăn drift. |
| G4 | Walk-forward 3 giai đoạn thời gian + kiểm tra era | Không ổn định qua các giai đoạn → loại |
| G5 | Bonferroni theo nhóm + FDR-BH 10% trên toàn bộ lưới tham số đã quét | Dưới VỪA → không đủ bằng chứng |
| G6 | MT5 single-run — trọng tài cuối | Không sống ⇒ không PASS |

**Cấm optimize trong MT5.** Dò tham số chỉ diễn ra ở G2 trong Python, và mọi tổ hợp đã thử phải đếm vào số phép kiểm ở G5.

### Bẫy riêng của họ bot này — bắt buộc xử lý trong code
1. **Fill giả định của pending order.** Dữ liệu bar không cho biết thứ tự chạm trong bar. Với lưới dày nhiều tầng trong 1 bar, sai số này lớn hơn cả edge. Bắt buộc chạy trên **tick data** hoặc chứng minh kết quả bất biến với giả định tie-break bi quan nhất.
2. **Bar-order ambiguity của TP/SL rổ** — lỗi đã ghi nhận trước đây, tái xuất hiện ở đây với mức nghiêm trọng hơn nhiều.
3. **Look-ahead** ở re-anchor: gốc lưới mới phải tính từ `Open[i+1]`.
4. **Survivorship của cấu hình**: rổ chưa đóng ở cuối mẫu phải mark-to-market, không được bỏ qua — nếu không thì mọi cấu hình `AGAINST` sẽ đẹp giả tạo.
5. **Chi phí theo giờ**: spread giãn đêm/tin. Lưới dày nhất lại hay khớp đúng lúc spread giãn. Cost model phải theo giờ, không phải một số trung bình.

---

## 6. Pre-test G0 — rẻ, chạy trước, có quyền phủ quyết cả hướng đi

Mục tiêu: trả lời "ở scale h này, tài sản này, thị trường có bất đối xứng thật không?" mà không cần viết engine.

**Thống kê dùng:** Efficiency Ratio ở đúng timescale của lưới.
```
ER(h) = |P_end − P_start| / Σ|ΔP| , đo trên cửa sổ chứa trung bình N bậc lưới
```

Quy trình:
1. Với mỗi tài sản × mỗi h ∈ {0.1 … 3.0} × ATR: tính phân phối ER thực nghiệm.
2. Sinh null bằng block-bootstrap và GBM cùng σ, cùng độ dài.
3. So sánh:
   - ER thực **>** null ⇒ tồn tại trend persistence ở scale đó ⇒ chỉ `DIRECTION = WITH` đáng test.
   - ER thực **<** null ⇒ mean reversion ⇒ chỉ `AGAINST` đáng test.
   - Không khác null ⇒ **loại cả tài sản × scale đó khỏi toàn bộ họ PMG, ghi vào sổ loại trừ vĩnh viễn.**
4. Xuất một bản đồ nhiệt `tài sản × h` → đây chính là bản đồ nói cho ta biết nên giãn lưới đến đâu, thay vì quét mù.

Bước này chạy trong vài phút và có khả năng cắt bỏ >80% không gian tham số trước khi tốn một giây backtest nào.

---

## 7. Đầu ra mong đợi

1. Bản đồ nhiệt ER(tài sản, h) + vùng nào của không gian tham số còn sống sau G0.
2. `h*` — bước lưới tối ưu theo tài sản, và bằng chứng nó ổn định qua các giai đoạn.
3. Bảng so sánh 4 hàm SIZE ở cùng `h*` — trả lời dứt điểm: hàm tăng size có tạo giá trị, hay chỉ là đòn bẩy trá hình che một baseline `flat` thua lỗ.
4. Đường equity + phân phối DD của các config sống sót, kèm vốn tối thiểu yêu cầu.
5. Nếu không có gì sống sót: một mục trong sổ loại trừ, ghi rõ họ chiến lược "position management không entry" đã bị bác ở những tài sản và scale nào, để không lặp lại.

---

## 8. Không gian biến thể NGOÀI engine — 3 trục quét

Ba trục dưới đây trực giao với 7 khối tham số ở §1. Một "ô" nghiên cứu là một bộ ba `(D1, D2, D3)`; trong mỗi ô mới quét lưới engine.

**Quy tắc gốc:** G0 (§6) chạy ở cấp độ ô, **trước** khi đụng tới engine. Ô nào chết ở G0 thì không bao giờ được cấp CPU. Đây là cơ chế duy nhất giữ cho tổng số phép kiểm không nổ tung.

### 8.1 D1 — Tài sản

| Tầng | Tài sản | Vai trò |
|---|---|---|
| A — chính | US500, UK100, GER40, XAUUSD | Nơi phát hiện |
| B — xác nhận | US30, USTEC, JP225 | Chạy lại **nguyên si**, không tinh chỉnh lại tham số |
| C — đối chứng khác lớp | EURUSD, USDJPY, BTCUSD | Kiểm tra cơ chế có phải đặc thù chỉ số hay không |

**Luật khái quát hoá:** một cấu hình PASS ở tầng A phải chạy lại ở tầng B/C với **đúng tham số đã chuẩn hoá ATR, không dò lại**. Nếu mỗi tài sản đòi một `h` riêng vượt ngoài chuẩn hoá ATR thì đó là fitting, không phải cơ chế — loại.

**Điều kiện dữ liệu bắt buộc trước khi mở ô nào:** bảng contract spec theo tài sản gồm tick size, tick value, min/max lot, stop level, **spread thực theo từng giờ**, swap long/short, giờ phiên, hành vi gap. Thiếu bảng này thì mọi con số G2 trở đi vô nghĩa.

### 8.2 D2 — Phiên trong ngày

Định nghĩa theo **giờ sàn có xét DST**, dẫn xuất từ dữ liệu đã chuẩn hoá Europe/Helsinki. Cấm định nghĩa phiên bằng offset UTC cố định — DST sẽ làm lệch một tiếng suốt nửa năm và nó len vào kết quả như một edge giả.

| Bucket | Giả thuyết chiều |
|---|---|
| `ASIA_QUIET` | AGAINST — biên độ hẹp, hồi quy |
| `LONDON_OPEN` (2h đầu) | WITH |
| `LONDON_MID` | trung tính |
| `NY_OPEN` (2h đầu, gồm overlap) | WITH |
| `NY_MID` | trung tính |
| `NY_CLOSE` / cash close | WITH — dòng đóng vị thế |
| `ROLLOVER` (quanh 00:00 giờ sàn) | dự kiến **tự loại**: spread giãn 5–10× |
| `WEEKEND_EDGE` (2h cuối T6, 2h đầu T2) | dự kiến tự loại: gap + thanh khoản mỏng |

Ba luật kèm theo:

1. **Bản đồ G0 trở thành 3 chiều:** `ER(tài sản, h, phiên)`. Kỳ vọng là câu trả lời WITH/AGAINST **đảo chiều theo phiên** — đó chính là lý do tồn tại của trục này. Nếu ER không đổi theo phiên trên mọi tài sản thì trục D2 vô giá trị, ghi nhận và bỏ luôn để khỏi tốn về sau.
2. **Tham số mới `eod_flatten`:** nếu `session_scoped = true` thì rổ bị ép đóng ở cuối cửa sổ phiên. Một chiến lược phiên mà ôm rổ xuyên qua biên phiên thì không phải chiến lược phiên — nó chỉ là chiến lược 24h có entry lệch giờ.
3. **Cost model phải theo bucket**, không dùng spread trung bình toàn ngày. Lưới dày nhất lại hay khớp đúng lúc spread giãn; dùng trung bình là tự tặng mình một edge không có thật.

**Cảnh báo chọn phiên hậu nghiệm:** 8 bucket × 2 chiều = 16 phát bắn. Chọn phiên đẹp nhất sau khi nhìn PnL là cách nhanh nhất để tạo edge giả trong toàn bộ đặc tả này. Phiên phải nằm trong prereg trước khi chạy, và mọi bucket đã thử đều đếm vào bộ đếm phép kiểm ở G5.

### 8.3 D3 — Scale / khung thời gian

**Bẫy khái niệm cần nói rõ cho QuantLab:** engine này không có entry signal, nên "đánh khung lớn hơn" **không phải** là đổi timeframe chạy. Khung thời gian chỉ đi vào hệ thống qua đúng ba đường:

| Đường vào | Tác động |
|---|---|
| `atr_tf` + `atr_period` | Quy đổi `h` ra giá trị tuyệt đối — đây mới là thứ thực sự "phóng to" cái lưới |
| Thang của `time_stop` và `reanchor_dist` | Phải giãn đồng bộ với `h` |
| Granularity mô phỏng | **Luôn giữ tick/M1 bất kể scale.** Không được nâng granularity mô phỏng theo scale — sẽ mất hết thông tin thứ tự chạm trong bar |

Thang quét: `atr_tf ∈ {M5, M15, H1, H4, D1}`, `h` biểu diễn theo bội số ATR của khung đó.

**Ba hệ quả bắt buộc theo dõi khi scale tăng:**

- **Swap trở thành chi phí chi phối.** Ở H4/D1 rổ ôm qua đêm nhiều đêm; swap × số đêm × tổng lot có thể vượt toàn bộ lãi. Tính riêng cột `swap_share_of_pnl` — nếu > 30% thì cấu hình đó thực chất là một cược lãi suất, không phải cược cơ chế.
- **Gap thành rủi ro chính** (xem 8.4).
- **Sức mạnh thống kê sụp.** Ở scale D1, một tài sản có thể chỉ cho 20–40 rổ/năm. Không đủ để qua FDR trên một tài sản đơn lẻ. Suy ra: **ở scale lớn buộc phải gộp bằng chứng across tài sản**, mà muốn gộp hợp lệ thì cơ chế phải bất biến theo tài sản — vòng ngược lại đúng luật khái quát hoá ở 8.1. Ghi số rổ kỳ vọng/năm ngay lúc sinh config; ô nào dưới ngưỡng power tối thiểu thì loại trước, đừng chạy rồi mới biết.

### 8.4 Xử lý gap (bắt buộc, vì D2 và D3 đều đẩy rổ qua biên)

- Mọi tầng lưới nằm trong khoảng gap khớp tại **giá open sau gap**, không khớp tại giá tầng. Giả định bi quan, không thương lượng.
- BASKET STOP được đánh giá tại giá open sau gap, không tại mức stop.
- Với rổ `AGAINST`, gap xuyên qua stop chính là **chế độ chết** của cơ chế. Phải đo riêng thành thống kê `gap_stop_slippage` và báo cáo phân phối đuôi của nó, không được gộp vào DD chung.

### 8.5 Ngân sách phép kiểm và hiệu chỉnh

Phễu bắt buộc:

1. G0 lọc ở cấp ô `(tài sản × phiên × scale)` — rẻ, không cần engine.
2. Chỉ ô sống mới được cấp lưới engine, và **kích thước lưới engine phải prereg trước** cho từng ô.
3. Mọi config đã chạy ghi vào bộ đếm phép kiểm, kể cả config bị loại ở G1 vì vô nghiệm.
4. Bonferroni theo nhóm trong từng ô + FDR-BH 10% giữa các ô.
5. Báo cáo **số phép kiểm độc lập hiệu dụng**, không phải số thô — tài sản và phiên tương quan mạnh với nhau, dùng số thô sẽ khắt khe quá mức và giết cả cơ chế thật.

**Luật hậu nghiệm:** ô nào được mở ra *sau khi* đã xem kết quả của ô khác thì đánh cờ `post_hoc = true` và **không được tính vào PASS**. Nó chỉ có tư cách sinh giả thuyết cho vòng prereg sau.

### 8.6 Sổ loại trừ

Mỗi ô chết ghi một dòng: `tài sản | phiên | atr_tf | h | direction | gate chết | thống kê + giá trị | khoảng dữ liệu | ngày | ghi chú`.

Phân biệt rõ **chết ở G0** (thị trường không có bất đối xứng ở scale đó — kết luận về thị trường, bền vững) với **chết ở G3 placebo** (có bất đối xứng nhưng engine không khai thác được — kết luận về engine, có thể mở lại nếu engine đổi). Hai loại này không được trộn, vì loại đầu cho phép đóng vĩnh viễn còn loại sau thì không.

### 8.7 Mã định danh cấu hình

```
PMG-{asset}-{session}-{atr_tf}-h{h}-{direction}-{step_mode}-{size_mode}-tp{tp_mode}-st{stop_mode}
```
Hash rút gọn từ chuỗi này làm khoá dedupe. Bắt buộc, nếu không QuantLab sẽ chạy trùng hàng nghìn lần qua các phiên làm việc khác nhau.

---

## 9. Giả định cần Mr Vanh xác nhận trước khi code

- Nguồn dữ liệu: tick hay bar M1? Điểm 5.1 gần như bắt buộc tick cho `h < 0.3 ATR`.
- Có chấp nhận cả hai chiều `WITH` và `AGAINST` cùng vào vòng quét, hay chốt trước một chiều?
- Ngưỡng vốn thực tế để cắt các config đòi margin quá cao.
- Danh sách 8 bucket phiên ở 8.2 có đúng với cách Mr Vanh quan sát thị trường không, hay cần tách/gộp lại trước khi prereg.
- Ngưỡng power tối thiểu (số rổ/năm) để một ô ở scale lớn được phép chạy.
