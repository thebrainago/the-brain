# 04 — MẢNH GHÉP NÊN LẤY (và mảnh KHÔNG nên lấy)

> Cho brain2. Nguyên tắc của chủ dự án (nguyên văn, 10/10): *"mục tiêu của ta là lấy những hệ thống và logic vốn đã vận hành sẵn → kiểm định và chỉnh sửa cho phù hợp → giữ lại những thứ dùng được và tận dụng những mảnh ghép tốt; sao phải tốn thời gian vậy nhỉ"*.
> Vì vậy file này **không** bảo brain2 bê cả the-brain sang. Brain2 gọn hơn, rẻ hơn, và ở vài chỗ **tốt hơn** (đọc thẳng MQL: 13/22 = 59,1 % so với 2/22 = 9,1 %; mô phỏng theo đường giá có stop-out từng lệnh; cổng có placebo cùng cấu trúc).
> Ở đây chỉ liệt kê cái brain2 **chưa có** hoặc có mà thước đo còn lạc quan. Mỗi mảnh có: **giá bao nhiêu** (công + tiền), **lấy ở đâu**, **kiểm xong chưa**, **khi nào nên làm**.
> Ràng buộc chi phí (xem `01` §7): chạy trên **máy hiện có**, **không nâng nhân CPU, không mua VPS**. Mọi mảnh P1, P3, P4, P5 bên dưới chạy được trên một nhân, không cần MT5.
> Đường dẫn dạng `nhan/…` là **tệp trong kho the-brain** (gốc link ở `README.md`). Brain2 đọc được; không cần chép nguyên cái nào trừ khi mục đó nói rõ.

## Bảng nhanh

| Mảnh | Là gì | Giá | Có sẵn | Nên làm |
|---|---|---|---|---|
| **P1** | Bảng 125 ô "engine ↔ MT5 tester" làm **đáp án sẵn** cho mô phỏng lưới H1 của brain2 | **0 đồng**, chỉ tải ~2 mã × 6 tháng nến H1 | `du_lieu/hieu_chuan_125_o.csv` | **ĐẦU TIÊN** (trước khi tin bất kỳ số lãi lưới nào của brain2) |
| **P4** | Đối chứng nhiễu **ở cấp đường ống** (chuỗi giả có đáp án) | ~100–150 dòng mã, vài phút/một nhân | **phương pháp**, không phải mã | **THỨ HAI** (rẻ nhất mà đổi nhiều nhất cách đọc "PASS") |
| **P3** | Swap **theo từng lệnh** (sửa lỗi "swap dính vào số dư chung" mà brain2 đã ghi) | ~80–150 dòng | ý tưởng + `nhan/swap_uoc.py` | Khi sửa mục swap |
| **P5** | Bảng điểm vòng lặp (giờ máy/chặng, vùng lãi đã/chưa kiểm ngoài mẫu) | ~100 dòng | ý tưởng + `nhan/vong_lap.py` | Khi vòng lặp chạy đều |
| **P6** | Cách "bóc luật từ lịch sử lệnh" (thẻ cơ chế: lot, bước, thoát) | vài trăm dòng | `nhan/ho_so_bot.py`, `nhan/ho_so_set.py` | **Sau**, khi đã có lịch sử lệnh |
| **P2** | Nhân C chạy lưới nhanh ×134 | **lớn** (~2.900 dòng + bài test) | `nhan/luoi_nhan.c` + `.py` | **KHÔNG làm mặc định** (xem bên dưới) |
| **P7** | Hiệu chuẩn thật với MT5 (`hieu_chuan_luoi`, `ea_gia_lap`, `ea_LuoiDayDu.mq5`) | cần một phiên MT5 | `nhan/hieu_chuan_luoi.py` … | **KHÔNG làm bây giờ** |

---

## P1 — Bảng hiệu chuẩn 125 ô: đáp án sẵn cho mô phỏng lưới

### Tại sao đây là mảnh quý nhất
Brain2 chấm lưới bằng **mô phỏng trên nến H1** (`nhan/luoi.py` bản cũ và `mo_phong.chay_he` có nhánh `ro.luoi`). Mô phỏng nến luôn phải *đoán* thứ tự giá bên trong một nến. The-brain đã đo chính chuyện đó: cùng cấu hình, cùng cửa sổ, chạy trên engine nến **và** trên MT5 tester (Model 0, tick sinh từ M1).
Kết quả (xem `03` R1): với lưới **có tia lệnh**, engine nến lạc quan trung vị **+8,7 điểm %/năm** (tứ phân vị +2,9 … +30,0); với lưới **không** có tia lệnh, chênh trung vị **+0,03** (−1,9 … +2,7). Xếp hạng giữa hai bên còn khá (Spearman 0,79) nhưng top-15 theo engine chỉ trùng 8/15 với top-15 theo tester.
→ Hình dạng đúng, **độ lớn của riêng những cấu hình có tia lệnh thì sai nhiều**. Số "ra tiền" của brain2 mà dựa vào tia lệnh/chốt cặp cần được kiểm với bảng này **trước**.

### Việc cụ thể (một nhân CPU, vài giờ công, không MT5)
1. **Lấy tập thí điểm 15 ô H1 có chất lượng lịch sử 100 %** (`khung == "H1"` và `chat_luong_lich_su_pct == 100`): AUDCAD 8 ô + NZDCAD 7 ô, cùng cửa sổ **2019-03-01 → 2019-08-31** (184 ngày, ≈ 3.100 nến H1 mỗi mã). Chỉ cần tải nến H1 của **hai mã × 6 tháng** — rất nhỏ, tránh lỗi 429 của Dukascopy (tải chậm, nghỉ giữa các ngày, lưu cache).
   *Đừng* dùng 71 ô chất lượng 51 % và 1 ô chất lượng 1 % làm đáp án — đó là cửa sổ tester thiếu dữ liệu một nửa, chênh lệch ở đó một phần là do dữ liệu chứ không do engine.
   Đã có sẵn bản tóm tắt 15 ô ở bảng cuối mục này, brain2 khỏi cần mở CSV nếu chỉ đọc qua link.
2. **Nạp tham số:** cột `tham_so_json` của CSV có đúng các khoá của `ThamSo` trong `nhan/luoi.py` của brain2 (buoc, tp, tran_tang, che_do, lot, muc_stopout, don_bay, cho_lui, kieu_lot, he_so_lot, tia_lenh, bien_cap, cap_moi_bar, chot_tien, dung_lo_tong, he_so_buoc, buoc_tran). Nên: `ThamSo(**json.loads(dong["tham_so_json"]))` chạy thẳng. `kieu_lot = "nhan"` nghĩa là `lot·he_so^k` (hệ số < 1 làm lot **nhỏ dần**); `cong` là `lot·(1+he_so·k)`. Cột `tia_lenh` trong CSV là chuỗi `"True"/"False"` — nhớ đổi sang bool.
3. **Quy đổi tiền:** AUDCAD, NZDCAD tính bằng **CAD** (tiền báo giá) còn tài khoản tester là **USD**, vốn 10.000. The-brain nhân vốn với hệ số `f` = số CAD ứng với 1 USD (≈ tỉ giá USDCAD lúc đó, **xấp xỉ 1,3**; ước từ chính các lệnh của tester) rồi chia mọi con số tiền cho `f`. Nếu brain2 chạy vốn 10.000 thẳng bằng CAD thì %/năm sai vài chục phần trăm *tương đối* — đó là nhầm đơn vị, không phải sai engine.
4. **So sánh đúng loại số:**
   - `tester_lai_nam_pct` = lãi/năm **đã tính cả lãi/lỗ chưa đóng** lúc hết cửa sổ (tester tự đóng "end of test"), quy năm bằng `ngay/365,25`; **chưa trừ swap** (tester luôn ghi swap = 0).
   - `engine_lai_nam_pct` của the-brain là **sau swap ước**; muốn so cùng thước thì `engine − engine_swap_nam_pct` (cột có sẵn) *hoặc* tắt swap trong mô phỏng của brain2 khi so.
   - Cũng so `so_lenh` và `maxDD`. Dung sai the-brain từng dùng cho nhãn KHỚP: lãi ≤ max(10 %, 1 điểm), DD ≤ max(25 %, 2 điểm), lệnh ≤ max(15 %, 3 lệnh) — **chỉ là nhãn của the-brain**: 114/125 ô ra "LECH" vì dung sai chặt, và nhãn không phân biệt lệch nhỏ (±2 điểm) với lệch lớn (+37 điểm ở ô có tia lệnh). Đừng học cái nhãn, hãy học cái **chênh**.
5. **Thứ tự giá trong nến là chỗ sai lớn nhất — chạy nhiều giả định và báo khoảng.** The-brain đo được (`nhan/luoi.py`, đoạn "HAI MÔ HÌNH BAR"):
   - Bản v3 "cực trị" xử lí mỗi nến theo thứ tự cố định *"thêm tầng ở low → chốt cặp tia ở HIGH → TP so với high"*: cặp tia bị chốt ở **cực trị của nến** thay vì ở **giá ngưỡng**, tối đa 999 cặp/nến, spread bị trừ hai lần, và thứ tự trong nến **luôn thuận lợi** (tầng hấp thụ cú nhún ngược rồi chốt ở đỉnh, nến nào cũng vậy). Hai thứ cộng lại tạo ra lợi nhuận *từ không khí* khi độ phân giải nến thấp.
   - Bản v4 "đường đi" (mặc định từ 08/10): nến xanh đi O→L→H→C, nến đỏ O→H→L→C; đoạn *ngược chiều* rổ thì thêm tầng (khớp tại mốc, hoặc tại giá đầu đoạn nếu nhảy giá), đoạn *thuận chiều* thì chốt cặp / TP **tại giá ngưỡng**; spread tính **một** lần lúc mở lệnh; lỗ treo đo trên **cả** đường, không chỉ ở low.
   - Đo bản v4 với **chính EA** chạy trên sàn giả C++ (12 cấu hình × 4 thứ tự cao/thấp trong nến): nằm trong ±5 % khi thứ tự EA = thứ tự mô hình giả định (theo màu nến); nhưng khi EA chạy thứ tự khác (thấp trước / cao trước / xen kẽ), các cấu hình *chờ giá lùi* (`cho_lui`) bị v4 đánh giá **thấp hơn 12–33 %** và cấu hình chỉ-bán −14,7 % ở 2/4 thứ tự; còn lại ≤ 7 %. (Âm = engine *bi quan* — an toàn cho xếp hạng, nhưng có thể loại nhầm.)
   - Trên dữ liệu tổng hợp (random walk, không chi phí, kỳ vọng thật = 0), sai lệch của mô hình **tăng theo cỡ nến** (đo tới M15; **H1 lớn hơn M15 ≈ 4 lần số tick/nến, chưa đo**). → Với nến H1, mô phỏng lưới của brain2 sẽ nằm ở vùng sai nhất mà the-brain chưa đo; càng phải báo khoảng.
   - **Việc cụ thể:** chạy tối thiểu ba thứ tự — (a) "cực trị gần open trước" (đúng `_duong_bar` của brain2), (b) "thấp trước luôn", (c) "cao trước luôn"; thêm (d) "theo màu nến" như v4 nếu rẻ. Hai quy tắc (a) và (d) thường trùng, chỉ khác ở nến có cực trị gần open nằm *ngược* phía màu nến (vd nến xanh nhưng high gần open hơn low). Báo **khoảng** giữa các thứ tự; nếu các thứ tự cho kết quả khác nhau quá một ngưỡng tự chọn → ghi **CHƯA ĐO ĐƯỢC**, không in một con số. Đừng chọn bản đẹp (bài học PMG: cùng một cấu hình, chỉ đổi giả định này đã chênh **14 lần** — `02` B2; và luật độ phân giải `NGUONG_PHAN_GIAI = 2,0`: bước lưới < ~2 lần biên độ nến thì nến không phân giải được thứ tự chạm).
6. **Cách đọc kết quả (đề xuất, không phải luật):**
   - Chênh cùng thước của ô **không tia** nằm quanh 0 (the-brain: +0,03; trên 10 ô H1 sạch: từ −1,2 đến +3,1) → mô phỏng *chấp nhận được* cho lưới thuần.
   - Chênh của ô **có tia** phải được **báo thành một khoảng** (the-brain trên 5 ô H1 sạch: +2,4; +3,1; +3,1; +8,4; **+37,0**). Nếu mô phỏng của brain2 *nhỏ hơn* khoảng này, tốt; nếu lớn hơn hoặc lệch dấu, **đừng tin** số lãi lưới-có-tia của brain2 cho đến khi sửa.
   - Tương quan hạng giữa mô phỏng và tester trên 15 ô: của the-brain ≈ **0,70** (thô, 15 điểm — sai số rất lớn, chỉ để biết cỡ).
7. **Giới hạn phải ghi cạnh kết quả:**
   - Giá của tester là dữ liệu của sàn XM (spread biến đổi theo nến); giá của brain2 là Dukascopy/Yahoo. Hai nguồn **không giống nhau từng nến** → so *hình dạng* và *chênh giữa có tia / không tia*, không so từng con số.
   - Chỉ 5 ô có tia và 10 ô không tia ở tập sạch H1: mẫu nhỏ. Muốn nhiều hơn phải có nến M5/M15 (nặng hơn nhiều) — **chưa cần**.
   - Cột engine là bản **v3 (cực trị — "lỗ trước")**, thước đo cũ trước 08/10; the-brain **chưa** đo lại bản v4 (đường đi) trên các ô này (120/125 ô đang chờ máy nhà). Đừng gọi các cột engine là "đáp án đúng": đáp án đúng là **cột tester**.

### Tóm tắt 15 ô thí điểm (H1, chất lượng 100 %, 2019-03-01 → 2019-08-31, vốn 10.000, đòn bẩy 100)
Dấu chấm thập phân. "Chênh" = (engine v3 đã bỏ swap) − tester, đơn vị điểm %/năm. Tia = tia lệnh; "biên cặp" là `bien_cap` (pip).

| # | mã | chế độ | bước | TP | tầng | lot | kiểu lot (hệ số) | tia | biên cặp | tester: lãi %/năm · DD % · lệnh | engine v3: lãi %/năm (bỏ swap) · DD % · lệnh | chênh |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | AUDCAD | ban | 20 | 13 | 8 | 0.08 | nhan 0.5 | có | 4 | 9.353 · 3.68 · 143 | 12.45 · 3.922 · 136 | +3.1 |
| 2 | AUDCAD | ban | 20 | 45 | 6 | 0.15 | nhan 0.25 | có | 4 | 10.937 · 4.75 · 73 | 14.02 · 4.728 · 69 | +3.1 |
| 3 | AUDCAD | hai_chieu | 20 | 20 | 6 | 0.5 | nhan 0.15 | có | 3 | -10.819 · 7.44 · 137 | 26.22 · 4.49 · 181 | **+37.0** |
| 4 | AUDCAD | hai_chieu | 45 | 13 | 7 | 0.02 | nhan 0.4 | có | 4 | -2.33 · 2.06 · 162 | 0.08 · 0.619 · 129 | +2.4 |
| 5 | AUDCAD | hai_chieu | 12 | 45 | 6 | 0.04 | nhan 0.25 | không | – | -0.147 · 0.55 · 84 | -0.11 · 0.904 · 73 | +0.0 |
| 6 | AUDCAD | hai_chieu | 80 | 10 | 6 | 0.5 | nhan 0.25 | không | – | -9.503 · 6.55 · 111 | -9.17 · 15.814 · 106 | +0.3 |
| 7 | AUDCAD | mua | 20 | 34 | 6 | 0.02 | nhan 0.4 | không | – | -3.668 · 3.54 · 46 | -1.80 · 1.761 · 35 | +1.9 |
| 8 | AUDCAD | mua | 60 | 8 | 5 | 0.5 | nhan 0.25 | không | – | -43.393 · 32.56 · 50 | -41.11 · 31.43 · 52 | +2.3 |
| 9 | NZDCAD | hai_chieu | 20 | 10 | 7 | 0.04 | nhan 0.4 | có | 3 | -5.569 · 3.03 · 352 | 2.80 · 0.804 · 376 | +8.4 |
| 10 | NZDCAD | ban | 12 | 13 | 7 | 0.3 | nhan 0.25 | không | – | 29.497 · 10.6 · 158 | 28.33 · 10.172 · 165 | -1.2 |
| 11 | NZDCAD | hai_chieu | 20 | 8 | 5 | 0.08 | nhan 0.15 | không | – | -5.355 · 2.82 · 244 | -3.98 · 3.224 · 233 | +1.4 |
| 12 | NZDCAD | hai_chieu | 45 | 13 | 6 | 0.15 | nhan 0.4 | không | – | -8.57 · 4.7 · 145 | -8.60 · 7.598 · 142 | -0.0 |
| 13 | NZDCAD | hai_chieu | 80 | 34 | 8 | 0.02 | nhan 0.5 | không | – | -3.786 · 2.36 · 64 | -1.11 · 1.047 · 55 | +2.7 |
| 14 | NZDCAD | mua | 45 | 16 | 6 | 0.02 | nhan 0.5 | không | – | -7.188 · 4.4 · 35 | -4.05 · 2.805 · 33 | +3.1 |
| 15 | NZDCAD | mua | 80 | 6 | 6 | 0.3 | nhan 0.15 | không | – | -41.426 · 25.34 · 55 | -38.34 · 24.92 · 60 | +3.1 |

Điều nên thấy ngay từ bảng: ô 3 (hai chiều + tia lệnh): tester **lỗ 10,8 %/năm**, engine nến **lãi 26,2 %/năm**. Đó là loại sai lệch mà một cổng "lãi sau phí" trên mô phỏng nến sẽ cho **ĐẠT** nhầm.
Cũng thấy: nhiều ô tester lỗ — lưới *tuỳ tiện* trong 6 tháng này đa số **không** ra tiền; đừng đọc bảng như danh sách ứng viên.

---

## P4 — Đối chứng nhiễu ở cấp đường ống (chỉ cần phương pháp)

### Vấn đề nó giải
Brain2 đã có **placebo cùng cấu trúc** cho từng ứng viên — tốt. Nhưng khi quét **N** ô lưới rồi chọn ô tốt nhất, thứ cần hỏi thêm là: *"nếu thị trường chỉ là nhiễu, đường ống của mình còn cho PASS bao nhiêu lần?"* The-brain đo bằng chuỗi giả có đáp án (xem `03` R2): chỉ có nhiễu mà ô tốt nhất vẫn "qua" ngoài mẫu **86–88 %**, ô ngẫu nhiên **84–85 %** → cổng nhị phân "lãi sau phí ngoài mẫu" **bão hoà** với lưới (vì lưới dễ có lãi nhỏ + hiếm lỗ lớn trong cửa sổ ngắn).

### Cách làm lại trên đường ống của brain2 (~100–150 dòng, không port file cũ)
1. Sinh chuỗi H1 giả **không có edge**: dao động kiểu GARCH(1,1), biên độ năm ≈ 9 %, spread ≈ 15 điểm, ~54.600 nến (≈ 9 năm), chia 60/20/20 (huấn luyện / đánh giá / cuối). 100–200 chuỗi là đủ.
2. Chạy **đúng đường ống thật** (quét → chọn ô tốt nhất → đánh giá ngoài mẫu) và đồng thời một ô **ngẫu nhiên** cùng lưới.
3. Ghi tỉ lệ "qua" của ô tốt nhất vs ô ngẫu nhiên; nếu gần nhau → cổng bão hoà, đừng dựa vào tỉ lệ "qua" thuần.
4. Thước **không bão hoà** the-brain thấy dùng được: hơn mua-giữ ở **cùng rủi ro**, calmar so với phân vị nhiễu, cửa sổ ngoài mẫu dài gấp đôi.
5. (Tuỳ chọn, đáng làm nếu rẻ) thêm chuỗi **có edge cấy sẵn** để đo *độ nhạy* (cổng hiệu chuẩn hai chiều: tỉ lệ lọt khi chỉ nhiễu **và** sức phát hiện khi có edge; một cổng từ chối mọi thứ trông y hệt một cổng tốt).
- **Đừng port `nhan/doi_chung_nhieu.py`** (1.015 dòng, đã đóng băng, gắn với cấu trúc sổ tay riêng). Dùng `du_lieu/doi_chung_nhieu_tom_tat.json` (9 kịch bản) để so *con số* sau khi tự đo.
- **Nhãn, không phải cổng**: kết quả này nên thành một dòng "tỉ lệ nhiễu của đường ống = X %" cạnh mỗi kết luận, theo luật 25/09 của chủ dự án (xem `01` §3). Chưa đo trên chuỗi thật.

---

## P3 — Swap theo từng lệnh

Brain2 ghi nhận tồn đọng "swap gắn vào số dư chung, không theo lệnh". The-brain gặp cùng vấn đề, theo hướng khác: **MT5 tester luôn ghi swap = 0** (125/125 ô; 286/286 hàng hiệu chuẩn) nên "ĐẠT" của tester là *trước swap*, và lưới/DCA là loại giữ lệnh lâu nên chịu swap nhiều nhất (ước −4,4 %/năm trung vị; 22/61 ô tester-dương thành ≤ 0 — `03` R3).
Ý tưởng cần lấy (đã làm trong `nhan/swap_uoc.py`, 437 dòng, có test):
- Mỗi lệnh: `swap = − tỉ_lệ(chiều) × số_đêm × lot × K × giá / 365`; dấu dương của tỉ lệ = **trả**, âm = **nhận**. `số_đêm` đếm số lần **qua nửa đêm giờ máy chủ**, **thứ Tư tính 3** (FX), thứ Bảy/CN 0; mã không phải FX thì tính liên tục theo ngày lịch và ghi rõ.
- `K` = tiền tài khoản trên một đơn vị giá, một lot (gộp luôn hợp đồng và tỉ giá báo giá→tài khoản).
- Tách hai nửa để tính lại được khi đổi tỉ lệ: **độ phơi bày** (không phụ thuộc tỉ lệ) rồi **áp tỉ lệ**.
- **Không cộng hai lần:** nếu nguồn đã ghi swap khác 0 thì dùng số đo, không cộng thêm số ước. Ước không làm được (thiếu tỉ lệ) → báo "không ước được", **không đoán**.
- **Chưa làm được** (nói thẳng): swap làm sâu thêm maxDD (tester không có đường vốn sau swap) — chỉ cảnh báo, không sửa số. Tỉ lệ swap là bảng *hiện tại* của sàn áp cho cả lịch sử (vấn đề y hệt mục "áp phí hiện tại cho 2003–2010" của brain2).
- Với brain2, phiên bản gọn: cộng dồn swap **theo thời gian sống của từng lệnh**, tính vào P&L của lệnh khi đóng và vào equity (cho stop-out) khi còn mở.

## P5 — Bảng điểm vòng lặp (ý tưởng)

Chỉ đến 10/10 the-brain mới có bảng này, và nó cho thấy: 1.573 việc, 105 giờ máy, **84 %** ở chặng "quét trong mẫu", 0 % ở "kiểm ngoài mẫu", **0/698** vùng lãi từng kiểm ngoài mẫu (`03` R12). Không có bảng điểm này thì không ai thấy.
Việc cần làm ở brain2: gắn **nhãn chặng** (tìm nguồn / bóc cơ chế / kiểm / giữ lại / áp dụng / hạ tầng) và **thời lượng** vào mỗi lần chạy, rồi in một bảng 6 dòng. Quy tắc nhãn "GIỮ": qua đoạn xác nhận ở ≥ 3 thị trường — **là nhãn, không phải cổng chặn**. Tham khảo `nhan/vong_lap.py` (1.386 dòng — **chỉ để xem ý**, brain2 viết bản ~100 dòng) và `tai_lieu/VONG_LAP.md`.

## P6 — Bóc luật từ lịch sử lệnh (để dành cho bước "lấy lịch sử lệnh → hiểu luật")

Khi brain2 có lịch sử lệnh của một bot (từ máy thử MT5 hoặc từ tín hiệu công khai), cách the-brain làm (và có số đo, `03` R8–R9): gom lệnh thành **chuỗi**, khớp **công thức lot** (phẳng / cộng / nhân / nhiều pha) với từng lệnh, đo **bước**, đo **cách thoát** (chốt cả chuỗi theo pip/tiền, khoá lời trượt, cắt lỗ), rồi xếp **từng tham số** của tệp `.set` vào đúng **một** trong bảy ô: *khớp / mâu thuẫn / tắt / bị che / chưa gặp / không đo được / không rõ*. Ghi rõ những gì **chưa đo được** (cách vào lệnh đầu cần đường giá M1 thật).
Lấy ý: `nhan/ho_so_bot.py`, `nhan/ho_so_set.py`, `reports/ho_so_bot_that_20261004.md`. Làm sau, không phải bây giờ.

## P2 — Nhân C `luoi_nhan.c` (đã làm, nhưng KHÔNG khuyên làm mặc định)

- **Đã đo:** nhanh hơn ×134 trên chuỗi tổng hợp 190.000 nến M15, khớp từng bit, ASan sạch; một ô 1.547 ms → 18 ms; quét 54 ô 31,2 s → 0,62 s trên 1 luồng (`03` R14).
- **Giá thật:** để dùng, brain2 phải thay `nhan/luoi.py` (351 dòng) bằng bản của the-brain (`nhan/luoi.py` 1.285 dòng + `nhan/luoi_nhan.py` 907 + `nhan/luoi_nhan.c` 725 + `config/luoi_quy_cach.json` + bốn tệp test `test_luoi_nhan.py`, `test_luoi_duong_di.py`, `test_luoi_quy_cach.py`, `test_luoi_thoat_gio.py` ≈ 3.500 dòng). Cần numpy và ba tên trong `chi_phi` mà brain2 đã có. Mặc định bản mới là mô hình nến `duong_di`; để tái tạo số cũ dùng `khop_bar="cuc_tri"`. Không có trình biên dịch C thì tự lùi về Python (im lặng — **nhớ kiểm biến môi trường `LUOI_NHAN`** để biết đang chạy cái nào); Windows không có compiler: `pip install ziglang`.
- **Vì sao không nên:** ước tính *tuyến tính theo số nến* (chưa đo trên brain2): H1 116.000 nến, một ô cỡ ~1 giây bằng Python → **1.000 ô ≈ 17 phút trên một nhân**. Nút cổ chai của brain2 là *số giả thuyết độc lập và số lần LLM đọc ngữ cảnh*, không phải tốc độ quét lưới. Chạy nhanh hơn cũng **không tạo thêm edge**, chỉ tạo thêm phép thử — tức thêm chọn lọc (mỗi ô vẫn là MỘT phép thử).
- **Khi nào mới cân nhắc:** nếu sau P4 brain2 muốn quét hàng chục nghìn ô trên nến M5/M15 và thời gian thực sự là nút thắt đo được. Hỏi chủ dự án trước. Không phải lý do để nâng nhân hay mua VPS: phần lớn lợi ích đến từ việc đổi ngôn ngữ, không từ thêm máy.

## P7 — Hiệu chuẩn thật với MT5 (để dành)

`nhan/hieu_chuan_luoi.py` (797 dòng), `nhan/ea_gia_lap.py` (sàn giả C++), `ea_LuoiDayDu.mq5` cần **một phiên MT5** (một terminal tester là ràng buộc vật lý: chỉ một việc tester tại một thời điểm). Chủ dự án nói brain2 chưa chạy MT5 vì chưa từng mở phiên đó. Việc này **không phải bây giờ**: P1 đã cho đáp án sẵn từ the-brain. Nếu có ngày chủ dự án chạy MT5 ở brain2, tái dùng giao thức 125 ô (cùng cửa sổ, cùng tham số, hai con số cạnh nhau, ghi cả chất lượng lịch sử).

---

## DANH SÁCH "KHÔNG LẤY" (để brain2 khỏi tốn công)

1. **Bộ bóc cơ chế của the-brain** (DSL `vao`/`ra`, `nhan/ngu_phap.py`, phễu 12.078 → 285 → 18). Brain2 đọc thẳng MQL đạt 13/22 = 59,1 %, the-brain 2/22 = 9,1 % trên cùng bài đo mốc. Lấy *bài học* (`02` mục D–E: bẫy dữ liệu/nguồn và dùng AI), không lấy mã.
2. **Sổ đăng ký nguồn / bộ đọc diễn đàn / `b link` / quy trình Telegram.** 23 diễn đàn / 14 nước và công cụ `b link` được ghi là **chưa chạy trên trang thật**; không có bằng chứng giá trị. (Bài học và bẫy mạng vẫn ở `02` mục D.)
3. **Chạy nền kiểu the-brain:** `qwen/` (bộ chạy tự động), kênh `b cau`, thư mục `viec/`, "máy nhà luôn chạy hết công suất". Brain2 không có máy nhà/đám mây kiểu đó; **đừng chép luật "chạy 100 % khi máy đang bật"** (xem `01` §7).
4. **Mọi thứ phụ thuộc `nao.db`** (đã mất khi cài lại máy nhà 02/10): các con số phễu cũ không tái tạo được; sổ tay nghiên cứu mới đã xuất ra `du_lieu/so_tay_nghien_cuu/`.
5. **Bản sao tài liệu rác 3.656 tài liệu tồn đọng** và các tệp EA / `.set` / lịch sử lệnh thô của tác giả khác — **không vào git** ở bất kỳ kho nào.
6. **Các cổng cứng kiểu cũ** (MDE/FDR/placebo là *nhãn cảnh báo*, không phải cổng chặn — luật của chủ dự án; xem `01` §3 về chỗ brain2 vẫn đang giữ cổng chặt hơn).

## Thứ tự làm đề xuất (rẻ → đắt)

1. **P1** (đọc CSV, tải 2 mã × 6 tháng, chạy 15 ô × 2 giả định; ~vài giờ công, 0 tiền). Kết quả: *một dòng* "chênh cùng thước: không tia a…b; có tia c…d" cạnh mọi số lưới.
2. **P4** (sinh chuỗi giả, chạy đường ống; ~100–150 dòng). Kết quả: *một dòng* "tỉ lệ nhiễu của đường ống".
3. **P3** khi động tới swap; **P5** khi vòng lặp chạy đều.
4. **P6** khi có lịch sử lệnh thật. **P2/P7**: chỉ khi chủ dự án đồng ý và nút thắt đã được đo.

## Nguồn trong kho the-brain
`du_lieu/hieu_chuan_125_o.csv`, `du_lieu/hieu_chuan_tom_tat.json`, `nhan/hieu_chuan_luoi.py`, `reports/lech_engine_EURCAD.md`, `tai_lieu/SWAP_THUOC_DO.md`, `nhan/swap_uoc.py`, `tai_lieu/TOC_DO_TEST.md`, `tai_lieu/VONG_LAP.md`, `nhan/vong_lap.py`, `reports/ho_so_bot_that_20261004.md`, `tai_lieu/RA_SOAT_KIEN_TRUC_03102026.md`.
