# 02 — KINH NGHIỆM ĐÃ TRẢ GIÁ (the-brain, 08/2026 → 10/2026)

> Đọc sau `01_LUAT_CHU_DU_AN.md`. Mục đích: brain2 khỏi phải trả lại những cái giá này.
> Mỗi mục có: **chuyện gì đã xảy ra · con số · làm gì thay thế**. Nguồn nằm trong ngoặc vuông,
> là đường dẫn trong kho `the-brain` (gốc link ở `README.md`). Số nào chưa đo thì ghi rõ "chưa đo".
> Nhãn trạng thái dùng xuyên suốt: **MÔ PHỎNG** (engine Python/C chạy trên nến) · **TESTER** (MT5 Strategy Tester) ·
> **LỊCH SỬ THẬT** (lệnh đã khớp của một tài khoản) · **ĐO TRÊN GIÁ** (thống kê giá, chưa có lãi/lỗ) · **CHƯA ĐO**.

---

## 0. MƯỜI ĐIỀU QUAN TRỌNG NHẤT (đọc nếu chỉ có 5 phút)

1. **"Có lãi trong mẫu" của lưới/DCA không phải bằng chứng.** Trên chuỗi giá giả chỉ có nhiễu, ô tốt nhất của lượt quét
   vẫn "qua" kiểm ngoài mẫu **86–88 %** (ô ngẫu nhiên cùng lưới: 84–85 %). Cổng nhị phân "lãi sau phí" bị bão hòa. → mục C1.
2. **Engine mô phỏng theo nến lạc quan với lưới có "tia lệnh"** (ghép cặp lệnh sâu nhất với lệnh đầu rồi đóng cả cặp):
   so với MT5 tester thật trên 125 ô, engine lãi hơn ở **50/68** ô có tia lệnh, lệch trung vị **+4,4 điểm %/năm** (có chỗ +32 điểm).
   Dùng engine để **xếp hạng và nhìn hình dạng**, không dùng để nói "lãi X %/năm". → mục B1.
3. **MT5 tester không ghi swap** (0 ở 125/125 ô, 286/286 hàng đã lưu). Lưới giữ lệnh lâu mất ~4–5 %/năm vì swap;
   trong 61 ô tester-dương, **22 ô thành ≤ 0** sau khi ước swap. Mọi "ĐẠT" của tester trước 09/10 là **trước swap**. → B3.
4. **Quản lí lệnh quan trọng hơn vào lệnh.** AUDCAD H4: quét 668 cơ chế vào lệnh → không cơ chế nào vừa đủ tần suất vừa Sharpe > 0.
   Cùng bộ tham số lưới, chỉ bật "tia lệnh": **+0,66 → +13,26 %/năm** (MÔ PHỎNG, chưa qua tester). → `03`, mục R5.
5. **Khép vòng lặp trước, làm nhánh sau.** 12.078 tài liệu → 285 cơ chế (2,4 %) → 18 mẫu (0,15 %); **84 % giờ máy** là quét trong mẫu;
   **0/698** vùng lãi từng được kiểm ngoài mẫu. Nhiều giờ máy ≠ tiến bộ. → A1, A4.
6. **Đường ngắn nhất từ "đang ra tiền" sang "của ta"**: lịch sử lệnh thật → bóc luật quản lí lệnh → dựng lại → thử trên giá thật.
   Đã làm được cho 2 bot vàng: công thức lot khớp 3114/3114, 1467/1467, 1962/1962 lệnh; EA dựng lại khớp 2.244/2.244 chuỗi. → A7.
7. **Danh sách "người thắng" đã được lọc sẵn.** 400/400 hồ sơ tín hiệu có tăng trưởng > 0 và không hồ sơ nào có DD công bố ≥ 80 %,
   nên hai tiêu chí đó không phân biệt gì; chỉ **tuổi sống ≥ 2 năm** là thước lọc thật: 94 (≥ 1 năm) → **31** (≥ 2 năm). → C14.
8. **Đừng tin nhãn lấy bằng regex trên cả trang HTML**: 19/31 hồ sơ bị gán sai mã (vàng bị ghi là USDCHF). Đọc bảng có cấu trúc. → D5.
9. **Dùng AI để điền trường thì phải có cổng bằng code**: LLM điền "cơ chế" cho 48 khai báo, thẩm định bác 41. Lời nhắc dài kèm danh sách loại trừ
   khiến LLM trả về 0. → E1, E2.
10. **Chi phí = số lần gọi × kích thước ngữ cảnh.** Phần AI tự sinh (suy nghĩ + lệnh) ≈ 52 % tổng chi phí. Lõi C cho engine lưới nhanh **×134** (khớp từng bit),
    nên **không cần thêm lõi hay VPS** để quét lưới. → E5, `04`.

---

## A. CÁCH LÀM VIỆC VÀ CHIẾN LƯỢC

**A1. Vòng khép kín trước, module nhỏ sau.** Chủ dự án (10/10/2026): vòng lặp "tìm nguồn chất lượng → bóc cơ chế → kiểm định → giữ lại, chọn lọc → áp dụng
vào vòng sau", còn việc đang làm "chỉ là những module nhỏ". Bảng điểm sinh từ git (`python3 b.py vong-lap --in`): TÌM/BÓC/KIỂM/GIỮ/ÁP DỤNG, mỗi chặng có số vào/ra và giờ máy.
Đo 10/10 (1.573 việc, 105 giờ máy): **84 %** giờ máy ở chặng quét trong mẫu, kiểm ngoài mẫu 0,0 %, tìm nguồn 0,2 %, bóc cơ chế 0,0 %, giữ lại 0,0 %, áp dụng 0,0 %;
**698 vùng lãi tìm được, 0 vùng kiểm ngoài mẫu**; 0 cơ chế "giữ lại" (cần ≥ 3 thị trường qua đoạn xác nhận, ≥ 50 % ứng viên). (Bảng `du_lieu/vung_lai_trong_mau.csv` có 880 dòng cao-nguyên/đối-chứng = 698 + 182, thêm 175 dòng ngẫu nhiên.)
Phễu (số **trước 02/10**, lấy từ hồ sơ cũ; `nao.db` mất khi cài lại máy nhà — chỉ dùng làm mốc xu hướng): 12.078 tài liệu → 285 cơ chế (2,4 %) → 18 mẫu (0,15 %);
tài liệu học thuật (openalex + crossref = 3.313 = 27,4 % số tài liệu) cho ≈ 0 cơ chế → cắt ngân sách. Trên 22 EA thật, bộ bóc bằng regex/DSL chỉ ra 7 cơ chế, tất cả từ 3/22 EA; 8 EA breakout khoảng giá/ORB ra **0**
vì điều kiện vào nằm trong *biến trung gian và trạng thái* (khoảng giá đầu phiên, cờ theo ngày, đếm vị thế, lệnh chờ) mà DSL "vào theo từng nến" không có. [`tai_lieu/RA_SOAT_KIEN_TRUC_03102026.md` §2, §4]
**Làm gì:** đo tỉ lệ vào/ra từng chặng; mở rộng chặng đang *đói*, không phải chặng dễ làm. Mỗi phiên mở bằng bảng điểm, không bằng cảm giác.
[`tai_lieu/VONG_LAP.md`, `tai_lieu/NGUON_NGUOI_THANG.md` §7]

**A2. "Có mã" ≠ "đang chạy".** Sơ đồ sinh từ mã nguồn (`b ban-do`) tìm thấy 31 module mồ côi (không nằm trên đường chạy nào), trong đó có cả công tắc tự ngắt (`han_muc.py`).
Một "họ lỗi" lặp lại nhiều lần: thành phần tồn tại nhưng không nằm trên đường chạy, trong khi một con số bình thường vẫn in ra.
**Làm gì:** mỗi module mới phải nằm trên một đường chạy có test; sinh sơ đồ từ mã thay vì viết tay. (brain2 đã có `nhan/ban_do.py`.)

**A3. Mã mới không tới máy đang chạy.** Máy nhà từng trễ ~275 commit; mọi sửa lỗi engine không hề chạy ở đó; 21/22 bộ chạy dùng mã cũ.
**Làm gì:** bộ chạy tự `fetch + merge --ff-only` đầu mỗi lượt; ghi **phiên bản engine** vào từng kết quả; sổ tay không xếp hạng kết quả của engine cũ. [`reports/chan_doan_hieu_suat_08102026.md`]

**A4. "24 giờ, hàng nghìn phép thử, ra 1 hệ +13 %/năm, DD > 30 %" (08/10) — chẩn đoán thật:**
(a) ~1.250 / ~1.500 phép thử là quét lưới trên **thước đo hỏng**: engine cũ báo "có lãi" ở gần *mọi* ô (vd 2.973/3.000), nên không phân biệt tốt/xấu;
đối chiếu 120 ô với tester thật: 109 lệch / 11 khớp; (b) 24 đơn tester chết ở giây ~95 (slot thiếu `Include\Trade\Trade.mqh`) mà nhiều đơn vẫn báo "ĐẠT" (thoát mã 0 nhưng in lỗi);
(c) đơn "quét sâu diễn đàn" xong trong 0,3 giây vì mã chỉ đọc trang 1; (d) con số +13 % là một EA lưới công khai chạy ở một mức lot tùy ý, chi phí còn "khai", Model 0.
**Làm gì:** trước khi chạy hàng loạt, *chứng minh thước đo phân biệt được tốt/xấu* (C1, C2). Đơn "sâu" mà xong trong chớp mắt là báo động. Phân loại "ĐẠT giả".
[`reports/chan_doan_hieu_suat_08102026.md`]

**A5. Đừng dựng engine/nguồn thứ hai khi cái thứ nhất chưa cho một kết quả đạt.** Lệnh 03/10: chưa có "ĐẠT" ở đoạn xác nhận thì không mở thêm nguồn hoặc engine mới
(cTrader hoãn; TradingView chỉ là nguồn ý tưởng vì không có API tester). [`tai_lieu/NGUON_NGUOI_THANG.md`]

**A6. Tái dùng cái đã chạy; chỉ dựng lại khi không có file.** Chủ dự án 09/10: *nếu bot có sẵn file MQL5 thì việc cần là backtest dạng **Optimize** để tìm input tốt nhất + thử thêm lớp quản lí vốn/lệnh bên ngoài; chỉ giả lập khi không có file.*
Bot có `.mq5`/`.ex5` + `.set` → chạy **nguyên file** trong MT5; lớp quản lí lệnh bên ngoài chỉ gắn được vào EA có mã nguồn (tester chạy MỘT EA mỗi lần); `.ex5` là hộp đen, chỉ tối ưu tham số của chính nó.
Không có file nhưng có lịch sử lệnh → bóc luật → dựng lại (A7). [`tai_lieu/MINI_BRAIN_CANCUBO.md` §10, `tai_lieu/LAN_EA_THO.md`]

**A7. Đường ngắn nhất từ "đang ra tiền" sang "của ta" = lịch sử lệnh thật → luật quản lí lệnh → EA của ta.**
Bóc từ lệnh thật của hai bot vàng (lịch sử của *máy thử MT5*, không phải tài khoản thật): công thức lot khớp 3114/3114 (bot A), 1467/1467 và 1962/1962 (bot B);
dựng lại EA cho bot B khớp tuyệt đối 2.246/2.246 chuỗi về lot/SL (sai số SL lớn nhất 0,05 pip), và EA chạy trên đường giá tối thiểu suy từ chính các chuỗi tái tạo 2.244/2.244 chuỗi (2 chuỗi thoát tay bị loại).
**Điểm nghẽn thật:** *tín hiệu vào* không bóc được từ lệnh (cần đường giá M1 thật + tester) — nên ưu tiên *quản lí lệnh* (cũng là quan điểm chủ dự án). [`reports/ho_so_bot_that_20261004.md`, `tai_lieu/MINI_BRAIN_CANCUBO.md`]

**A8. Chủ dự án phản biện đúng và đã cứu dự án nhiều lần** — hãy coi đó là dữ liệu:
(1) 18/09: quét 668 cơ chế *vào lệnh* rồi kết luận "AUDCAD không ra tiền" là kết luận **sai phạm vi**; tiền nằm ở quản trị vị thế.
(2) 25/09: tiêu chí duyệt chỉ là lãi sau phí + maxDD < 80 % ở đòn bẩy ≤ 10; không loại martingale/DCA/lưới.
(3) 03/10: "he lon, nhieu file, cam giac di duong vong" → tìm nơi đã có người thắng rồi khai thác trước.
(4) 08/10: "24 giờ, hàng nghìn phép thử mà chỉ ra 1 hệ 13 %, DD > 30 %: có chấp nhận được không?" → hóa ra thước đo hỏng (A4).
(5) 10/10: "đang tập trung nhánh nhỏ, mục tiêu là *vòng lặp*" (A1). (6) "cậu có đang làm phức tạp không?" — lấy logic đã vận hành sẵn → kiểm định → giữ cái dùng được.
**Làm gì:** khi bị hỏi "có đang phức tạp không?", trả lời bằng số đo (giờ máy, tỉ lệ vào/ra) và thu hẹp phạm vi, đừng làm thêm.

**A9. Báo cáo cho chủ dự án:** lời thường, 3–8 dòng: xong / chưa / kẹt ở đâu / cần chủ dự án làm gì. Chủ dự án không đọc thuật ngữ ("nhân C", "bit-y-hệt", "quét lưới"...).
Chỉ nhắn khi có tin thật hoặc cần quyết định; không gửi "ok / cảm ơn".

**A10. Quyết định không hoàn tác được thì hỏi trước.** Xóa, đẩy lên nhánh chính, trả tiền, gửi thư, đổi cài đặt máy: hỏi chủ dự án. Không tự đóng/ngắt hàng đợi việc của chủ dự án.

---

## B. BẪY MÔ PHỎNG / BACKTEST (kèm số đo)

**B1. Engine theo nến phóng đại cấu hình có TIA LỆNH so với MT5 tester** — 125 ô (AUDCAD 41 · EURCAD 45 · NZDCAD 39; M5 19 · M15 59 · M30 24 · H1 23; mỗi ô là một cửa sổ 6 tháng nằm trong 2018-01-03 → 2019-08-31; tester Model 0; engine v3 "cực trị" = thước đo cũ trước 08/10).
Tham số các ô: bước 8–80, TP 6–45, tầng tối đa 5–12, lot 0,02–0,5, hai chiều / chỉ mua / chỉ bán (97/15/13 ô), lot phẳng / nhân / cộng (27/82/16 ô).
Bảng đầy đủ: `du_lieu/hieu_chuan_125_o.csv`, tóm tắt: `du_lieu/hieu_chuan_tom_tat.json`. [`reports/hieu_chuan/*_e3.json` trong `viec/xong/`, `reports/lech_engine_EURCAD.md`]
- Engine (đã trừ swap) lãi hơn tester (chưa có swap) ở **69/125** ô; có tia lệnh **50/68**; không tia lệnh 19/57.
- Chênh lãi/năm (engine − tester), **trung vị**: có tia **+4,4 điểm %**; không tia −2,8. Vì tester không ghi swap (B3) còn engine đã trừ, hãy so **cùng thước** (bỏ swap khỏi engine):
  **có tia lệnh +8,7 điểm** (tứ phân vị +2,9 … +30,0) · **không tia lệnh +0,03** (−1,9 … +2,7). Nghĩa là: lưới *không* tia lệnh thì engine khớp tester ở trung vị; chỉ cấu hình có tia lệnh bị phóng đại.
- Theo khung (cùng thước, trung vị): có tia — M5 +4,8 · M15 **+14,2** · M30 +6,8 · H1 +7,1 (8 ô); không tia — M5 −0,5 · M15 −0,4 · M30 +1,5 · H1 +0,03 (15 ô, trong khoảng −3,9 … +3,1).
  Theo mã (có tia): EURCAD **+31,4** · AUDCAD +7,4 · NZDCAD +4,8. Lệch lớn nhất: EURCAD M15 (lịch sử 51 %) engine 153,6 vs tester 20,9 %/năm; NZDCAD M15 (lịch sử sạch) engine 64,8 vs tester −33,0.
- Số lệnh engine/tester: trung vị 1,06 (tứ phân vị 0,95–1,23); maxDD hai bên cùng cỡ (chênh trung vị −0,4 điểm).
- Theo chất lượng lịch sử (chỉ ô có tia lệnh): **sạch 100 %** (27 ô) +3,6 điểm (cùng thước +7,4), tỉ lệ engine/tester trung vị **≈ 0,9** (9 ô có tester ≥ +1 %/năm, tối đa 4,3);
  **51 %** (41 ô) +5,6 (cùng thước +10,6), tỉ lệ **≈ 2,9** (23 ô, tối đa 16,1).
  → *Không có hằng số "×2".* (Con số "×2,2, tới ×16" ở báo cáo 08/10 là trung vị/tối đa của 32 ô có tia lệnh với tester ≥ +1 %/năm; ô tester gần 0 cho tỉ lệ vô nghĩa, tối đa tới ×425,7.)
- Xếp hạng: Spearman **0,79**; top-15 theo engine chỉ trùng **8/15** với top-15 theo tester (nhóm đầu của engine cho 40–154 %/năm, cùng các ô đó tester cho từ −33 đến +53 %).
- **Làm gì:** engine dùng để *xếp hạng* và xem *hình dạng* vùng tham số; mọi con số tuyệt đối phải qua tester (hoặc engine `duong_di` đã hiệu chuẩn) trước khi nói "lãi X %/năm".
  Hiệu chuẩn **hai chiều** (ô engine khen mà tester chê, và ngược lại). Bảng 125 ô là *đáp án sẵn* để brain2 tự kiểm engine của mình mà không cần MT5 (xem `04`, `du_lieu/README.md`).
- **Chưa đo:** engine v4 (`duong_di`, mặc định từ 08/10) so với tester trên 120 ô — đơn đã xếp ở máy nhà, chưa có kết quả.

**B2. Mô hình nến.** "Cực trị" (v3) lạc quan hơn "đường đi" (v4): nến xanh đi O→L→H→C, nến đỏ O→H→L→C, khớp đúng tại ngưỡng, spread tính một lần cho mỗi lệnh.
Khi bước lưới < ~2 lần biên độ nến thì nến không phân giải được thứ tự chạm → trả **CHƯA ĐO ĐƯỢC**, không in số. Đo 14/09 trên random walk không chi phí: bước/biên độ = 0,54 cho **+720 %**,
= 3,24 cho −2,3 % (đáp án đúng = 0). Đã chặn bằng `NGUONG_PHAN_GIAI = 2.0`. [`tai_lieu/PMG_TRIEN_KHAI.md`]
Cùng bài học: **giả định thứ tự xử lí trong nến (tie-break)** đổi kết quả của cùng một cấu hình PMG từ +2,753 % xuống +0,199 % (~14×), và bản mang tên "bi quan" lại là bản *đẹp* hơn — luôn chạy cả hai giả định và báo bản thận trọng.

**B3. MT5 tester không ghi swap** (cột Swap = 0 tuyệt đối ở 125/125 ô, 286/286 hàng hiệu chuẩn đã lưu và 3 báo cáo độc lập). Tài khoản thật trừ/cộng swap mỗi đêm.
Engine ước swap trung vị **−4,4 %/năm** trên các cấu hình lưới; tester-dương 61/125 → **39/125** sau khi trừ swap ước; **22/61 ô dương thành ≤ 0**.
Quy tắc đã dùng (`nhan/swap_uoc.py`): không đoán tỉ lệ (không có thì `khong_uoc_duoc`); không tính hai lần (tester có ghi swap ≠ 0 thì dùng số đó); maxDD không sửa (tester không vẽ đường vốn sau swap) chỉ cảnh báo; tỉ lệ swap là bảng *hiện tại* của sàn, áp cho cả lịch sử (xấp xỉ).
**Làm gì:** coi "ĐẠT" của tester trên lưới/DCA là *trước swap* cho tới khi trừ swap. Đưa swap vào mô hình chi phí của engine. [`tai_lieu/SWAP_THUOC_DO.md`]

**B4. Mô hình tester.** Model 1 ("1 minute OHLC") nói dối khi TP < 2× biên độ nến M1; Model 0 (mọi tick do MT5 tự sinh từ M1) tốt hơn; Model 4 (tick thật) — XM chỉ có tick thật từ 2024-02-01.
Kết quả cuối phải qua Model 0/4. Với tester Model 1, nến M1 được chia thành 4 tick ở giây :00/:20/:40/:59 theo chiều nến (quan sát trên 2.246 chuỗi thật; *tương thích*, chưa chứng minh). [`tai_lieu/MINI_BRAIN_CANCUBO.md` §3]

**B5. Chất lượng lịch sử của tester & dữ liệu thiếu.** 71/125 ô chỉ có chất lượng lịch sử 51 %, 53 ô 100 %, 1 ô 1 % → không so được với nhau. Tester **không báo lỗi khi thiếu dữ liệu**
(một sàn từng bị cắt lịch sử từ 2022-08). Kiểm: chạy lại cùng cơ chế trên *nửa* cửa sổ, đếm lệnh; AUDCAD H4 6,67 năm = 71 lệnh vs 13,66 năm = 141 lệnh (50,4 % so với độ dài 48,8 %) → dữ liệu có thật cả kỳ.
Dữ liệu giá ở máy nhà chỉ có 14 mã nên 31 đơn dầu/gas/đường/lúa mì/XAUUSDM thành "không có dữ liệu".

**B6. Lưới thời gian của tester.** Lệnh nằm trên lưới 10 s hoặc 19,5 s → mọi thống kê cấp giây (trễ, khoảng cách) chỉ tin từ ~60 s trở lên. Thống kê theo pip không bị ảnh hưởng.

**B7. Đòn bẩy cộng LOG.** Gộp `(S_T/S_0)^L` bằng log làm mất lực cản biến động *và* khả năng cháy tài khoản: L=3 trên 98 năm ra **×76.289.488** thay vì **×2.406** (≈ ×31.700). Dùng gộp số học khi đòn bẩy ≠ 1.

**B8. Kelly cần Sharpe tính trên lợi suất SỐ HỌC**, không phải log (dùng log hạ trần `0,5·S²` đi ~27 %).

**B9. "Lợi suất ở trần maxDD 80 %" chỉ là số nhân lot, không phải kết quả.** Nhân lot lên cho tới khi sụt giảm chạm trần rồi báo CAGR phóng đại (lưới AUDCAD M15 theo cài đặt của một tín hiệu: **17.133 %/năm ở lot ×1000**) là vô nghĩa.
Số thật ở lot 0,01, vốn 10.000 USD (chi phí mức *sàn*, 04/10): khám phá 2018-01 → 2023-07 **+8,45 %/năm**, maxDD đường vốn −19,25 %, nhưng **lỗ treo đỉnh 29,65 % vốn**, phí ăn 50,7 % lãi gộp (6.584 lệnh, 579 chuỗi/năm);
xác nhận 2023-07 → 2025-02 **+5,56 %/năm**, maxDD −3,98 %, lỗ treo đỉnh 4,30 %, phí ăn 63,2 % lãi gộp. Kết quả AUDCAD 18/09 cũng vậy: holdout +13,26 %/năm, maxDD −3,5 %, **lỗ treo đỉnh 11,0 % vốn**.
**Làm gì:** báo ở đòn bẩy thật (≤ 10; `tien.cagr_duoi_tran_pct`) và luôn kèm **đỉnh lỗ treo**. Đường vốn đẹp vì lãi đã chốt bù lỗ; với đòn bẩy thật, lỗ treo là rủi ro gọi ký quỹ.
[`reports/nc_2023752_luoi.md`, `reports/AUDCAD_LUOI_KET_QUA_18092026.md`]

**B10. Nến D1 của CFD chỉ số KHÔNG phải nến phiên.** D1 của CFD chỉ số ôm ~23 giờ, biên độ rộng hơn phiên tiền mặt Mỹ **1,39×** (US500CASH 2018–2026); IBS tính hai kiểu chỉ tương quan 0,866 (98 ngày kích hoạt IBS < 0,2 theo phiên mà không theo D1, 91 ngày ngược lại). Cơ chế nói về *phiên* thì dùng dữ liệu phiên.

**B11. Spread đo từ D1 là CHẶN TRÊN** (H1 thấp hơn ~39 % — đo thật trên EURCAD). Spread quyết định khung đáng quét: 0,98 bps ăn 12,0 % biên độ một nến M5 nhưng chỉ 0,7 % biên độ nến D1; phí qua đêm 1,56 bps/đêm còn đắt hơn spread.

**B12. Chuỗi LAI độ phân giải.** Khung nhỏ của một mã có thể bắt đầu muộn (US100Cash: D1 từ 2011, H4/H1 từ 2016, M30 từ 2018-04, M15 từ 2022-06, M5 từ 2025-04). Nhà môi giới còn gộp nến ngày vào khung nhỏ khi thiếu dữ liệu mà không báo lỗi. Đếm số nến mỗi năm trước khi quét; đã có `du_lieu.cat_doan_tho`/`kiem_do_phan_giai`.

**B13. Cổ tức:** CFD chỉ số ở XM không trả cổ tức → dùng `co_tuc=False` cho chuỗi chỉ số giá.

**B14. Bẫy "chỉ số biến động thấp".** Xếp chỉ số theo biến động thấp nhất đưa lên đầu những chỉ số *âm sau phí* (UK100 mua-giữ **−2,77 %/năm** suốt 15 năm). Xếp theo CAGR ròng, không theo vol.

**B15. Đơn vị vàng.** Trong `.set`, 1 đơn vị khoảng cách = 1 pip sàn = **0,1 USD** trên vàng (đo bằng 4 nhóm số, hệ số 1 tuyệt đối). `chot_tien` là TIỀN (tiền báo giá trên 0,01 lot), không phải pip: cặp JPY gấp ~×100 cặp FX chuẩn.

**B16. Năm gác 9999 tràn số nguyên nano-giây** → thành năm 1815, chuỗi đang mở ở cuối cửa sổ bị chia thành nhiều chuỗi 1 lệnh `hết_giờ`. Dùng 2200-01-01. Lỗi này làm *mọi* số cuối cửa sổ lệch mà rất khó thấy bằng mắt.

**B17. Cơ chế theo GIỜ trên khung không có giờ** → tín hiệu hằng số. Ném lỗi, đừng trả 0.

**B18. "Closure nuốt tham số"** (`**_`): 152/170 mẫu cơ chế "điếc" (đổi tham số không đổi kết quả) và bộ đo độ ổn định chấm chúng là cao nguyên hoàn hảo. Từ chối khi `số_ô_khác_nhau < 2`.

**B19. "0/955 chuỗi lỗ"** trong lịch sử tester của bot B (chỉ MUA, DCA ×1,05, khóa lời trượt) là dấu hiệu của hệ **lệch âm** (nhiều lãi nhỏ, hiếm khi lỗ lớn), không phải bằng chứng an toàn. Trên cửa sổ ngắn, xác suất "có lãi và chưa cháy" tự nhiên cao (xem C1).

**B20. Cú lùi tồi nhất chưa rơi vào cửa sổ kiểm.** AUDCAD H4: 99 % số lần giá lùi chỉ cần 1 nến để quay lại (đó là thứ nuôi lưới); nhưng đuôi: lùi cực đại **13,2 % (~1.188 pip)** kẹt **1.527 nến** (~gần 1 năm) — không rơi vào nửa holdout. Phải kiểm riêng xem cấu hình có sống qua nó không. [`reports/AUDCAD_LUOI_KET_QUA_18092026.md`]

**B21. Đo sau khi *đo* phải cẩn thận:** phép đo hiệu chuẩn không được chiếm suất FDR/bộ đếm số lần thử (`ghi_so=False`).

---

## C. BẪY THỐNG KÊ / KIỂM ĐỊNH

**C1. ĐỐI CHỨNG NHIỄU — việc rẻ nhất, giá trị nhất.** Chạy *chính đường ống thật* (quét lưới → ô tốt nhất → đánh giá ngoài mẫu → ô ngẫu nhiên cùng lưới) trên **chuỗi giả có đáp án**.
Thiết kế: H1, 54.600 nến, biến động ~9 %/năm (GARCH), spread ~15 điểm, chia 60 % khám phá / 20 % xác nhận / 20 % niêm phong (không bao giờ cắt đoạn niêm phong), quét 1.000 ô × 9 mẫu (`che_do × kieu_lot`), ~1,7 năm ngoài mẫu.
Kết quả (MÔ TẢ, nhãn cảnh báo — không phải cổng chặn) [`tai_lieu/VONG_LAP.md` §8; `du_lieu/doi_chung_nhieu_tom_tat.json`]:
| Chuỗi | số chuỗi | lượt quét xếp "cao nguyên" | ô tốt nhất "qua" ngoài mẫu | ô ngẫu nhiên "qua" | tốt nhất "qua *và* hơn mua-giữ" | ngẫu nhiên "qua và hơn" |
|---|---|---|---|---|---|---|
| chỉ nhiễu, engine 4 | 100 | 72 % | **86 %** | 84 % | 57 % | 52 % |
| chỉ nhiễu, engine 3 | 200 | 70 % | **88 %** | 85 % | 55 % | 52 % |
| nhiễu + hồi quy rất yếu / yếu / vừa (VR(288) 0,96 / 0,86 / 0,54) | 30 mỗi loại | — | 89 % / 86 % / 89 % | — | 63 % / 71 % / 77 % | 63 % / 61 % / 72 % |
**Cách đọc:** (a) cổng "lãi sau phí ngoài mẫu" bị **bão hòa** với lưới (lãi nhỏ đều, lỗ lớn hiếm → trên cửa sổ ngắn xác suất tự nhiên cao); (b) ô tốt nhất hơn ô ngẫu nhiên chỉ **vài điểm %**,
chỉ tách ra khi có hồi quy mạnh; (c) "xếp hạng trong mẫu" gần như không thêm thông tin so với bốc bừa trên chuỗi tổng hợp này.
**Làm gì:** trước khi tin một tỉ lệ "qua", chạy chuỗi chỉ nhiễu qua *đúng* đường ống đó. Đọc theo thước **không bão hòa**: hơn mua-giữ, calmar so với phân vị của nhiễu, hoặc cửa sổ ngoài mẫu dài gấp đôi.
Kèm 3 chuỗi hồi quy liều lượng để biết phép đo có *nhạy* không (nếu tỉ lệ không tăng theo liều thì chặng KIỂM mù).

**C2. Chọn ô tốt nhất của lượt quét = lời nguyền người thắng.** Luôn kèm hai nhóm đối chứng: `ngẫu nhiên` (một ô bốc bừa cùng lưới, hạt giống cố định) và `đối` (ô tốt nhất của lượt quét *không* xếp cao nguyên). Hơn nhau mới nói được "bộ lọc có tác dụng".

**C3. Rộng ≠ sâu.** Trên chuỗi có đáp án, tìm rộng ~3.000 điều kiện thấy edge yếu **3/8**; một giả thuyết có chủ đích thấy **8/8** (`b nc kiem 30`). Ngân sách nên đi vào giả thuyết có lí do kinh tế, không vào lưới tham số mù.

**C4. "Cao nguyên" không đảm bảo gì.** Trong bảng 698 vùng "cao nguyên" (`du_lieu/vung_lai_trong_mau.csv`), tỉ lệ ô có lãi trong mẫu trung vị **0,95** (nhóm đối: 0,39) — nhưng với lưới trên thước đo lạc quan thì gần như ô nào cũng lãi trong mẫu (C1). Chưa vùng nào qua kiểm ngoài mẫu (cột `xac_nhan_ngoai_mau` trống).

**C5. Ba trạng thái, không phải hai.** ĐẠT / ÂM / **CHƯA ĐO ĐƯỢC**. Mã thoát ≠ 0, thiếu file ra, file ra *cũ hơn* lúc bắt đầu, bảng có phần lớn cột trống → `CHƯA ĐO ĐƯỢC`, **không bao giờ** là ÂM. "ĐẠT giả" (thoát 0 nhưng in lỗi) đã xảy ra ở nhiều đơn tester.

**C6. Niêm phong MỘT lần; đoạn dữ liệu đóng băng theo NGÀY** (`so_cai/doan.json`: dữ liệu mới thêm không kéo đoạn niêm phong nhảy). Trước khi chạm holdout phải có `plan_hash`. Xác nhận là hàm *y nguyên*: chạy lại cùng giả thuyết = nhìn lại cùng holdout. Đổi kế hoạch sau khi nhìn dữ liệu = giả thuyết *khác*.

**C7. Nhiều PASS trong một ngày là tín hiệu HỎNG**, không phải tin vui. `t_alpha > 5` = nghi nhìn trước. Kết luận âm tính phải kèm MDE (hiệu nhỏ nhất phát hiện được).

**C8. Null của ER phải là ĐẢO DẤU**, không phải block bootstrap (block bootstrap giữ nguyên trung bình khối — chính là tử số của ER — nên nuốt tín hiệu: ER thật 0,2011 vs null 0,2006 trên chuỗi AR(+0,6) có đáp án).

**C9. Hiệu chuẩn cổng phải HAI CHIỀU:** `null_ty_le_lot` (cổng có để lọt nhiễu không) *và* `thu_luc_cong` (cổng có bắt được tín hiệu thật không). Cổng từ chối *tất cả* cho số liệu y hệt cổng tốt.

**C10. Báo trung vị + tỉ lệ vượt chuẩn, không báo max-của-N.** "Ô tốt nhất" chỉ là một *lựa chọn*. Xếp hạng trong mẫu giữa ≤ 1.074 cấu hình không kiểm soát đa so sánh = gợi ý, không phải bằng chứng.

**C11. Lọc theo CHI PHÍ trước khi xếp hạng ứng viên.** Xếp thuần theo Hurst đưa GBPPLN (**98,5 bps**) và GBPZAR (20,8 bps) lên đầu — phí giết mọi lưới. `TRAN_SPREAD_BPS = 8`.

**C12. Quét vào lệnh thuần không cứu được FX intraday.** AUDCAD H4, tester thật, 668 cơ chế RSI/hồi quy, 13,66 năm: 147/668 đủ tần suất (≥ 2 lệnh/tuần) và **0** trong số đó có Sharpe > 0; 5 cơ chế Sharpe ≥ 1 có tần suất **0,03–0,24 lệnh/tuần** (thấp hơn ngưỡng 8–65 lần). Giao của hai điều kiện: **rỗng**.
Ứng viên cũ qua cổng Python Sharpe 1,156 → tester **0,68**: tester cắt gần nửa ("Python chỉ là sàng lọc sơ bộ"). [`reports/AUDCAD_KET_LUAN_18092026.md`]

**C13. Thiết kế null cho LƯỚI** khác cho vào lệnh (lưới không có "entry" theo nghĩa thường): ngẫu nhiên hóa BƯỚC và HƯỚNG; chuỗi random walk/AR âm làm đối chứng (C1).

**C14. Danh sách người thắng đã lọc sẵn.** 400 hồ sơ tín hiệu MQL5: cả 400 có tăng trưởng > 0 và **không** hồ sơ nào có DD công bố ≥ 80 %. Hai điều kiện ấy không phân biệt gì. Chỉ tuổi sống làm việc: ≥ 1 năm + tăng trưởng > 0 + DD < 80 % = **94**; ≥ 2 năm = **31 (7,8 %)**.
`dd_pct` là số trang công bố (chưa đối chiếu cách tính). Không tính được "tỉ lệ có lãi của một tín hiệu bất kỳ". Dùng làm *nguồn giả thuyết*, không phải bằng chứng. Đề xuất chụp lại 94 hồ sơ mỗi tuần × 8 tuần để đo độ bền của chính bảng xếp hạng (chưa làm).

**C15. Dựng lại từ lịch sử của người thắng chỉ chứng minh "làm lại được".** Đoạn xác nhận/niêm phong của một tín hiệu chồng lên đời sống thật của nó nên "ĐẠT" ở đó là *LÀM LẠI*, không phải phát hiện độc lập; chỉ quãng *trước* khi tín hiệu bắt đầu mới là bằng chứng độc lập. Ghi rõ trong `ghi_chu`. (Ví dụ trong `03`, R6.)

---

## D. BẪY THU THẬP DỮ LIỆU / NGUỒN

**D1. Bóc nguồn.** `Accept-Encoding: br` khi máy không cài brotli → HTTP 200 nhưng `r.text` là rác (cùng một trang: 21.245 ký tự/0 link so với 82.347/40 link). DNS bị đầu độc ở một số mạng (3 triệu chứng khác nhau của MỘT nguyên nhân) → bật WARP.
"Làm giống người" quá tay phản tác dụng: `requests.get` trơn 4/4 = 200, còn phiên giữ cookie + Referer 4/4 = 403.

**D2. Tải HỎNG bị dịch thành "hết trang".** Con trỏ phân trang MQL5 bị cắt vĩnh viễn xuống trang 3. Phải phân biệt *lỗi mạng* với *hết dữ liệu*. Và thu thập không phân trang → 4 vòng liên tiếp tải lại đúng 60 file cũ (thêm con trỏ `đến_trang_N` lưu lại để lần sau làm tiếp).

**D3. Phiên đăng nhập trình duyệt.** Chrome (bản 154) gắn cookie với thư mục gốc của hồ sơ → **sao chép hồ sơ là mất đăng nhập**. Cách đúng: dùng Chrome thật + thao tác màn hình (dán URL bằng clipboard, *không gõ phím* vì rơi ký tự), nhịp ≥ 5,5 s/lần.

**D4. Lịch sử lệnh MQL5 cần đăng nhập.** Dùng export chính thức `…/signals/<id>/export/positions` (CSV `;`, ngày mới nhất bị ẩn). Nhịp 3–5 s/trang; IP bị cấm sau ~50–150 request; gặp 403/429/Cloudflare thì DỪNG và ghi mã lỗi, lưu mốc "đã tới trang N".

**D5. Nhãn mã bị gán sai 19/31.** `_RX_SYM` đếm mọi chữ hoa 6 ký tự trong CẢ trang HTML, lấy 3 mã nhiều nhất → sót tên sàn không theo mẫu 6 chữ (`GOLD#`, `XAUUSDm`…) và đẩy mã hiếm lên nhãn. Ví dụ tín hiệu 2196457 (nhãn cũ USDCHF) thật ra là **vàng 1.549 lệnh**, USDCHF 2 lệnh.
Sửa: đọc bảng **Distribution** có cấu trúc (`link_nguon.phan_bo_symbol`/`chuan_symbol`). Hệ quả: câu "gần hết là lưới/DCA trên AUDCAD & anh em" **không có bằng chứng** — mã chính của 31 người thắng: XAUUSD 8 · EURUSD 5 · USDJPY 3 · BTCUSD 3 · AUDCAD 3 · GBPUSD 2 · 7 mã còn lại mỗi mã 1; 2/3 hồ sơ là **danh mục nhiều mã**. (`du_lieu/mql5_31_nguoi_thang.csv`)

**D6. Tồn kho 3.656 tài liệu chưa đọc là RÁC** (hiệu chuẩn hai chiều: 400/400 bản đã bóc chấm ≥ 1 điểm, 0/3.656 bản tồn chấm được). Đừng nuôi một kho tồn mà chưa hiệu chuẩn bộ chấm.

**D7. Bộ lọc "có dấu hiệu chứa luật" viết cho văn xuôi** chấm mã nguồn 0 điểm. Lời nhắc bóc kèm "KHÔNG đề xuất lại, kể cả đổi tên" + danh sách 170 cơ chế khiến LLM trả về 0 → bộ lọc phải ở CỔNG (code), không ở lời nhắc.

**D8. Nguồn đa ngôn ngữ.** Chủ dự án muốn ≥ 1 diễn đàn trader mỗi quốc gia; ngân hàng từ khóa đa ngôn ngữ `keywords_nguon.py`; 71 nguồn đã đăng ký, 23 diễn đàn/14 nước trong `config/dien_dan.json`. Đọc diễn đàn **chỉ ĐỌC**: không tự đăng ký/join/follow nếu chủ dự án chưa duyệt; quét lại mỗi 168 giờ; 403/429/captcha thì dừng. (Chưa chạy trên diễn đàn thật.)

**D9. Dữ liệu giá công khai vs riêng.** Giá ở máy nhà (XM demo) không lên git. Chỉ đưa giá lên repo công khai khi chủ dự án cho phép từng cặp.

**D10. Tải CẢ GÓI của tác giả, không chỉ `.mq5`.** Phân loại tay 22 EA (16 chiến lược): chạy thẳng nguyên bản trên tester được 5 · rủi ro 2 · **không 9**, chủ yếu vì thiếu tệp `.mqh`/chỉ báo kèm theo
(vd một thư viện pivot được 8 file gọi, chỉ 3 file khai báo nhưng 5 file dùng thật). Bộ kiểm tệp phải đọc `#include <...>` ngoài thư viện chuẩn MT5 và bỏ qua chú thích; đánh dấu `THIEU_TEP` *trước* khi tốn lượt tester. [`tai_lieu/RA_SOAT_KIEN_TRUC_03102026.md` §8]

---

## E. DÙNG AI / LLM

**E1. LLM "điền trường" thì sai theo hướng dễ chịu.** Đo: LLM điền `cơ chế` cho 48 khai báo, thẩm định bác **41**. **AI đọc và viết; mã chấm và chặn** (`qwen/cong.py`): AI không được tự phán đạt/âm.

**E2. Mô hình rẻ + cổng code + tối đa 2 vòng sửa.** Lời nhắc loại trừ dài → trả về 0 (D7). Bộ lọc ở cổng, lời nhắc ngắn.

**E3. AI là nhà nghiên cứu chính, nhưng mọi phép đo đi qua sổ tay có dấu vân tay.** Kết quả nằm ngoài sổ tay (script `_*.py` rời) là kết quả không ai tìm lại được. Ba đoạn niêm phong (mở MỘT lần), vân tay thí nghiệm, phép thử đếm theo dòng giả thuyết, ba trạng thái.
(Ví dụ sổ tay: `du_lieu/so_tay_nghien_cuu/`.)

**E4. Tri thức mới chỉ vào hệ qua ngữ pháp có kiểm** (`nhan/ngu_phap.py`) — không `exec` mã LLM sinh.

**E5. Chi phí token (đo 02/10, `tai_lieu/TOI_UU_TOKEN.md`).** Chi phí = **số gọi API × kích thước ngữ cảnh** (mỗi lần gọi đọc lại *cả* ngữ cảnh). Token do AI sinh (đầu ra 16,7 % + "mang theo" 35,0 %) ≈ **52 %** tổng.
Quy tắc: (1) gộp lệnh độc lập vào MỘT lần gọi / một script; không "thăm dò" bằng LLM — dùng lệnh không-LLM; (2) đầu ra lệnh nặng phải gọn (head/cut/tóm tắt); (3) thư ngắn, dữ liệu dài vào file; chỉ gửi khi có việc;
(4) nghỉ > 1 giờ = cache hết hạn, nên chốt một đợt rồi nghỉ; (5) **phiên mới sau mỗi mốc rẻ hơn giữ phiên dài** (cập nhật khối "tay" của file bàn giao rồi mở phiên mới); (6) subagent cho việc đọc nặng/tìm rộng/log dài (ngữ cảnh riêng nhỏ, chỉ trả kết luận).

**E6. Máy-nhà-chạy-liên-tục không có nghĩa là hiệu quả.** Khi máy bật thì luôn có việc *đúng* để làm (hàng đợi giữ ≥ 12 giờ việc), nhưng "đúng" nghĩa là đã qua chặng thước đo (A4) và đang ở chặng đói (A1), không phải quét thêm trong mẫu.

---

## F. VẬN HÀNH

**F1. Bộ chạy phải giết CẢ CÂY tiến trình khi hết hạn.** Bản cũ treo vô hạn vì tiến trình mồ côi giữ pipe.

**F2. Thư mục tạm rò rỉ:** 2.482 thư mục ≈ **29 GB** làm đầy ổ đĩa (`ea_gia_lap.chay()` nay dọn sau mỗi lần). Dọn sau mỗi lần chạy.

**F3. Chỉ MỘT slot tester** (một `terminal64.exe` là ràng buộc *vật lý*): hai việc tester cùng lúc ghi đè `.mq5/.ini/.xml` của nhau và **không ai báo lỗi**. Xếp hàng nối đuôi; khi tester bận làm việc *không dùng* tester (đọc deals, viết mã, test).

**F4. Kênh chỉ huy.** Phiên cloud chỉ huy, máy nhà thực thi qua git (`viec/cho → viec/xong`, nhịp tim `viec/may`); danh sách lệnh trắng; dừng khẩn `CAU_DUNG`. Repo công khai ⇒ không đưa khóa/token/số liệu riêng; thư cũng nằm trong repo.

**F5. Nhịp tim lệch múi giờ** từng báo nhầm 19/22 bộ chạy còn sống; luôn đổi sang UTC trước khi tính tuổi nhịp tim.

**F6. Máy nhà bật ~6–12 giờ/ngày; tắt là bình thường.** Không báo "máy chết"; hàng đợi phải đủ sâu (≥ 12 giờ việc) để máy bật lên là có việc ngay; khi nhiều đơn dồn lại, ưu tiên theo chặng đang đói (A1).

**F7. Bộ test mồ côi.** Cuộc kiểm 10/10: 19 test rỗng và 12 test đặt nhầm thư mục `nhan/` (không bị pytest thu thập). Test phải *thật sự chạy*; chạy một lượt `pytest --collect-only` đếm.

---

## G. NẾU CÓ NGÀY DÙNG MT5 TESTER (brain2 hiện chưa dùng)

- Dùng khi cần số *tuyệt đối* hoặc hiệu chuẩn engine; không dùng để quét rộng (một slot, ~90 phút/cửa sổ ~190 chuỗi).
- Dùng Model 0 hoặc 4, không dùng Model 1 (B4). Kiểm chất lượng lịch sử (B5). Trừ swap (B3). Kiểm slot có đủ `Include\Trade\Trade.mqh` trước khi xếp hàng (F, A4).
- Chạy NGUYÊN file EA tác giả bằng `bo_set` (`.set` của tác giả); `tham_so` sai tên/không phải số → TỪ CHỐI (MT5 bỏ qua im lặng); `.ex5` là hộp đen — terminal phải TẮT "Allow DLL imports"; bot của người khác KHÔNG BAO GIỜ vào git.
- Các cổng ĐẠT của lần EA thô chưa hiệu chuẩn với máy thật ở 5 điểm — đọc `tai_lieu/LAN_EA_THO.md` trước khi tin bất kỳ "ĐẠT" nào.
