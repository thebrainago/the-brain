# 03 — KẾT QUẢ ĐÃ ĐO (the-brain → brain2)

> Mười bốn kết quả (R1–R14) mà the-brain đã đo, **kèm nhãn trạng thái, giới hạn và nguồn**. Đọc sau `02_KINH_NGHIEM.md`.
> Nhãn: **MÔ PHỎNG** (engine Python/C chạy trên nến) · **TESTER** (MT5 Strategy Tester, tick do MT5 tự sinh từ M1 hoặc tick thật) ·
> **LỊCH SỬ THẬT** (lệnh đã khớp; ở đây là lịch sử của *máy thử MT5*, chưa phải tài khoản tiền thật) · **ĐO TRÊN GIÁ** (thống kê giá, chưa có lãi/lỗ) ·
> **SỐ CÔNG BỐ** (số do trang nguồn công bố, chưa đối chiếu cách tính) · **CHƯA ĐO**.
> **Chưa có kết quả nào ở đây là tiền thật.** Không có dòng nào đủ để nói "hệ này ra tiền"; chúng là *thước đo, bẫy đã biết và ứng viên* để brain2 khỏi phải đo lại.
> Mốc thời gian: kho ở commit `8a1151c` (10/10/2026). Nguồn = đường dẫn trong kho `the-brain`, gốc link ở `README.md`.

---

## Bảng tóm tắt

| # | Kết quả | Nhãn | Một dòng |
|---|---|---|---|
| R1 | Hiệu chuẩn engine nến ↔ MT5 tester, 125 ô lưới | MÔ PHỎNG vs TESTER | lưới có *tia lệnh*: engine lạc quan trung vị +8,7 điểm %/năm (cùng thước); không tia: +0,03 |
| R2 | Đối chứng nhiễu cho đường ống quét lưới | MÔ PHỎNG (chuỗi giả) | ô tốt nhất "qua" ngoài mẫu 86–88 % **trên chuỗi chỉ có nhiễu** (ô ngẫu nhiên 84–85 %) |
| R3 | Swap | TESTER + ƯỚC | tester ghi swap = 0; engine ước trung vị −4,4 %/năm; 22/61 ô tester-dương thành ≤ 0 |
| R4 | AUDCAD H4, 668 cơ chế *vào lệnh* thuần | TESTER (13,66 năm) | không cơ chế nào vừa đủ tần suất vừa Sharpe > 0 |
| R5 | AUDCAD H4, lưới hai chiều ± *tia lệnh* | MÔ PHỎNG (giữ-lại), chưa qua tester | +0,66 → +13,26 %/năm; **đỉnh lỗ treo 11 % vốn** |
| R6 | Làm lại cài đặt của một tín hiệu công khai trên AUDCAD M15 | MÔ PHỎNG, **LÀM LẠI** | +8,45 % (khám phá) / +5,56 % (xác nhận); lỗ treo đỉnh 29,65 % / 4,30 % |
| R7 | PMG: quản lí lệnh *không* có tín hiệu vào | ĐO TRÊN GIÁ + MÔ PHỎNG | FX chéo và vàng hồi quy ở hầu mọi thang; chỉ số ≈ không có gì; cấu hình sống sót duy nhất = 0,015 %/năm |
| R8 | Thẻ cơ chế của hai bot vàng, bóc từ lệnh | LỊCH SỬ THẬT (máy thử) | công thức lot khớp 3114/3114 · 1467/1467 · 1962/1962 |
| R9 | Dựng lại EA cho bot B | MÔ PHỎNG, **vòng khép kín** | 2.246/2.246 chuỗi khớp lot/SL; tái tạo 2.244/2.244 |
| R10 | 400 hồ sơ tín hiệu MQL5 → người thắng | SỐ CÔNG BỐ | 400 → 94 (≥ 1 năm) → 31 (≥ 2 năm) |
| R11 | Phễu bóc cơ chế (tài liệu → cơ chế → mẫu) | MÔ PHỎNG/đếm (trước 02/10) | 12.078 → 285 (2,4 %) → 18 (0,15 %); 8 EA breakout → 0 cơ chế |
| R12 | Bảng điểm vòng lặp 10/10 | đếm từ git | 84 % giờ máy ở quét trong mẫu; **0/698** vùng lãi từng kiểm ngoài mẫu; 0 cơ chế giữ lại |
| R13 | Quét rộng vs giả thuyết có chủ đích | MÔ PHỎNG (chuỗi có đáp án) | rộng ~3.000 điều kiện thấy edge yếu 3/8; có chủ đích 8/8 |
| R14 | Tốc độ & chi phí | ĐO | nhân C ×134 (khớp từng bit); 54 ô: 31,2 s → 0,62 s; phần AI tự sinh ≈ 52 % token |

---

## R1 — Hiệu chuẩn engine nến ↔ MT5 tester (125 ô)
- **Cái đã đo:** cùng một cấu hình lưới chạy trên engine (v3 "cực trị", thước đo cũ trước 08/10) và trên MT5 tester (Model 0), mỗi ô là một cửa sổ 6 tháng nằm trong 2018-01-03 → 2019-08-31
  (AUDCAD 41 · EURCAD 45 · NZDCAD 39 ô; M5 19 · M15 59 · M30 24 · H1 23). 68 ô có tia lệnh, 57 ô không.
- **Số:** engine lạc quan hơn ở 50/68 ô có tia lệnh. Chênh lãi/năm (engine − tester), trung vị, **cùng thước** (đã bỏ swap khỏi engine): có tia **+8,7 điểm** (tứ phân vị +2,9…+30,0); không tia **+0,03** (−1,9…+2,7).
  Spearman xếp hạng 0,79; top-15 theo engine chỉ trùng 8/15 với top-15 theo tester. Không có hằng số "×2".
- **Nhãn:** engine = MÔ PHỎNG, đối chiếu = TESTER. Chất lượng lịch sử không đều (53 ô 100 %, 71 ô 51 %, 1 ô 1 %).
- **Giới hạn:** engine v4 (`duong_di`, mặc định từ 08/10) **chưa** được đo lại trên 125 ô (120 ô đang chờ máy nhà). Tester ở đây là *trước swap*.
- **Dùng cho brain2:** bảng `du_lieu/hieu_chuan_125_o.csv` là *đáp án sẵn* để tự kiểm mô phỏng H1 của brain2 (xem `04`, mảnh P4). Chi tiết: `02` mục B1.
- **Nguồn:** `du_lieu/hieu_chuan_125_o.csv`, `du_lieu/hieu_chuan_tom_tat.json`, `reports/lech_engine_EURCAD.md`, `nhan/hieu_chuan_luoi.py`.

## R2 — Đối chứng nhiễu
- **Cái đã đo:** chạy *chính đường ống thật* (quét 1.000 ô lưới → ô tốt nhất → đánh giá ngoài mẫu → ô ngẫu nhiên cùng lưới) trên **chuỗi giả có đáp án** (H1, 54.600 nến, ~9 %/năm, GARCH, spread ~15 điểm, chia 60/20/20).
- **Số:** chỉ nhiễu — ô tốt nhất "qua" ngoài mẫu 86 % (engine 4, 100 chuỗi) / 88 % (engine 3, 200 chuỗi), ô ngẫu nhiên 84 % / 85 %; "qua *và* hơn mua-giữ" 57 %/55 % vs 52 %.
  Hồi quy rất yếu/yếu/vừa: 89/86/89 % (qua) và 63/71/77 % vs 63/61/72 % (qua và hơn mua-giữ).
- **Nhãn:** MÔ PHỎNG trên chuỗi giả — *nhãn cảnh báo*, không phải cổng chặn.
- **Hiểu:** cổng nhị phân "lãi sau phí ngoài mẫu" **bão hòa** với lưới; chỉ thước không bão hòa (hơn mua-giữ, calmar so với phân vị nhiễu, cửa sổ ngoài mẫu dài gấp đôi) mới tách được. Chưa thử trên chuỗi thật.
- **Nguồn:** `tai_lieu/VONG_LAP.md` §8, `du_lieu/doi_chung_nhieu_tom_tat.json` (9 kịch bản), `nhan/doi_chung_nhieu.py` (đã **đóng băng**, đừng sửa để "cho đẹp").

## R3 — Swap
- **Cái đã đo:** cột Swap của MT5 tester = 0 ở 125/125 ô và 286/286 hàng hiệu chuẩn đã lưu; ước swap bằng bảng của sàn (`nhan/swap_uoc.py`).
- **Số:** engine ước trung vị **−4,4 %/năm** cho cấu hình lưới; tester-dương 61/125 → 39/125 sau khi trừ swap ước; **22/61** ô thành ≤ 0.
- **Nhãn:** TESTER (không ghi swap) + ƯỚC (tỉ lệ swap là bảng *hiện tại* của sàn, áp cho cả lịch sử; maxDD không sửa).
- **Giới hạn:** là ước lượng, không phải đo từ tài khoản thật. Mọi "ĐẠT" của tester trước 09/10 là *trước swap*.
- **Nguồn:** `tai_lieu/SWAP_THUOC_DO.md`, `nhan/swap_uoc.py`, `test_swap_uoc.py`.

## R4 — AUDCAD H4: vào lệnh thuần không đủ
- **Cái đã đo:** tester thật, 668 cơ chế họ RSI/hồi quy, lot 5,0, vốn 10.000, 2013-01-01 → 2026-09-01 (13,66 năm). Chất lượng dữ liệu kiểm: cửa sổ 6,67 năm = 71 lệnh vs 13,66 năm = 141 lệnh (50,4 % ↔ 48,8 %).
- **Số:** đủ tần suất (≥ 2 lệnh/tuần) 147/668 và **0** trong số đó có Sharpe > 0; 5 cơ chế Sharpe ≥ 1 có tần suất 0,03–0,24 lệnh/tuần (thấp hơn ngưỡng 8–65 lần). Giao hai điều kiện: rỗng.
  Ứng viên cũ qua cổng Python (Sharpe 1,156) → tester **0,68** (141 lệnh, PF 1,61, DD 3,46 %, +2,76 %/năm cùng rủi ro; mua-giữ +0,03 %/năm).
- **Nhãn:** TESTER. Kết luận "AUDCAD không ra tiền bằng vào lệnh" được chủ dự án phản biện là **sai phạm vi** (tiền nằm ở quản trị vị thế) → R5.
- **Nguồn:** `reports/AUDCAD_KET_LUAN_18092026.md`.

## R5 — AUDCAD H4: lưới hai chiều, bật/tắt tia lệnh
- **Cái đã đo:** 72 cấu hình, chia nửa đầu/nửa sau (huấn luyện/holdout) trên AUDCAD H4 (20.902 nến). Tia lệnh = ghép lệnh *sâu nhất* với lệnh *đầu tiên*, đóng cả cặp khi tổng lãi của cặp ≥ 4 pip, tối đa 1 cặp/nến.
- **Số:** 72/72 không cháy tài khoản ở cả hai nửa. Cấu hình dẫn đầu (bước 30, hệ số 1,0, TP 60, **tia**): huấn luyện +17,11 %/năm, **holdout +13,26 %/năm**, DD −3,5 %, **đỉnh lỗ treo 11,0 % vốn**, 578 lệnh/năm (~11 lệnh/tuần), phí ăn 19,7 % lãi gộp.
  Cùng bộ lưới chỉ tắt tia lệnh: holdout **+0,66 %/năm**, DD −9,1 % (bảng gốc; một câu chữ trong báo cáo gốc ghi −15,6 %, chưa rõ cái nào đúng).
- **Nhãn:** MÔ PHỎNG (engine cũ) — **chưa qua tester**; chưa đo placebo cho lưới. Cú lùi tồi nhất lịch sử (13,2 % ≈ 1.188 pip, kẹt 1.527 nến) **không rơi vào holdout**.
- **Đọc cùng R1:** engine cũ lạc quan chính ở cấu hình có tia lệnh, nên +13,26 % nhiều khả năng cao hơn số tester sẽ cho; hướng (tia lệnh là toàn bộ khác biệt) có lí do đáng tin hơn độ lớn.
- **Nguồn:** `reports/AUDCAD_LUOI_KET_QUA_18092026.md`.

## R6 — Làm lại cài đặt của một tín hiệu công khai (AUDCAD M15)
- **Cái đã đo:** bóc cài đặt từ 2.327 lệnh lịch sử của tín hiệu công khai 2023752 (từ 2025-07-01, 449 lệnh: bước 21,2 pip, hệ số bước 1,20, lot cộng 0,25, TP 7,6 pip, tia lệnh, tầng tối đa 5, hai chiều), rồi chạy lưới của ta với lot 0,01, vốn 10.000.
  Quét 70 ô (bước 12–30 × TP 5–14 × tầng 5/9) trên khám phá: **70/70 ô có lãi**.
- **Số:** khám phá 2018-01-02 → 2023-07-02: **+8,45 %/năm**, maxDD −19,25 %, đỉnh lỗ treo **29,65 % vốn**, 6.584 lệnh (579 chuỗi/năm), phí ăn 50,7 % lãi gộp.
  Xác nhận 2023-07-03 → 2025-02-17: **+5,56 %/năm**, maxDD −3,98 %, lỗ treo đỉnh 4,30 %, 2.184 lệnh, phí 63,2 %.
- **Nhãn:** MÔ PHỎNG, **LÀM LẠI** (đoạn xác nhận chồng lên đời sống thật của tín hiệu từ 2023-08 nên không độc lập); phí ở mức *sàn* (hằng số cũ), chưa phải phí XM thật; engine chưa hiệu chuẩn với MT5.
  Lệnh/năm của ta 1.200–1.340 vs con thật ~800: lưới của ta hoạt động dày hơn cài đặt tác giả. "17.133 %/năm ở lot ×1000" trong báo cáo chỉ là *số nhân lot*, không phải kết quả (xem `02` B9).
- **Nguồn:** `reports/nc_2023752_luoi.md`.

## R7 — PMG: quản lí lệnh không có tín hiệu vào
- **Cái đã đo:** bản đồ G0 (M5, ATR(H1), 200 chuỗi null *đảo dấu*, FDR-BH 10 %, 6 mã × 8 thang = 48 ô, 392 giây): ô nào có cấu trúc hồi quy/xu hướng để quản lí lệnh khai thác.
- **Số:** 25/48 ô sống, 22 ô chết vào sổ loại trừ vĩnh viễn. AUDCAD và EURGBP **8/8**, vàng (XAUUSDM) 7/8; US500CASH và XM_US500CASH mỗi cái 1/8; **XM_US100CASH 0/8** (xu hướng WITH ở US100 không qua FDR — chỉ là giả thuyết để quét lại).
  Quét thật 3 ô (14/09): chỉ **một** cấu hình AUDCAD qua G3+G4: **+0,199 %/13,5 năm = 0,015 %/năm** (mua-giữ −0,44 %/năm) — *cơ chế thật, gần như bằng không về tiền*.
  Cấu hình dẫn đầu theo lãi (+22,16 %) bị cổng độ phân giải gắn CHƯA ĐO ĐƯỢC (bước chỉ 1,97× biên độ nến). Cùng cấu hình sống sót đó, chỉ đổi giả định thứ tự xử lí trong nến (tie-break): +2,753 % (bản mang tên "bi quan", thực ra là bản *đẹp hơn*) vs +0,199 % (bản thận trọng — số phải đọc), chênh ~14 lần chỉ do giả định.
- **Nhãn:** ĐO TRÊN GIÁ (G0) + MÔ PHỎNG (G1–G4). G6 (MT5 single-run) chưa nối; trục phiên (D2) và thang ATR (D3) chưa quét.
- **Nguồn:** `tai_lieu/PMG_DAC_TA.md`, `tai_lieu/PMG_TRIEN_KHAI.md` §4, §7b.

## R8 — Thẻ cơ chế của hai bot vàng (bóc từ lệnh)
- **Cái đã đo:** từ lịch sử lệnh *của máy thử MT5* (không phải tài khoản thật) của hai bot vàng dạng lưới/DCA. Mỗi tham số `.set` được xếp vào đúng MỘT kết quả: khớp / mâu thuẫn / tắt / bị che / chưa gặp / không đo được / không rõ.
- **Số:** bot A (thoát cả chuỗi ở 10/20 pip, lot phẳng tới lệnh 10 rồi ×1,2 / ×1,1, hedge khi chuỗi ≥ 16 lệnh): công thức lot khớp **3114/3114** lệnh (1.198 chuỗi, +19 lệnh hedge tách riêng).
  Bot B (chỉ MUA, bước cố định 100 pip, lot ×1,05 mỗi lệnh, thoát bằng khóa lời trượt): khớp **1467/1467** (xác nhận, 955 chuỗi) và **1962/1962** (khám phá, 1.291 chuỗi); **0/955 chuỗi lỗ** trong đoạn xác nhận.
  172 tham số có ở cả hai bộ `.set`; chỉ 4 tham số đổi *cùng lúc* với hành vi đổi.
- **Nhãn:** LỊCH SỬ THẬT (máy thử). "0/955 chuỗi lỗ" là *chữ ký của hệ lệch âm* (nhiều lãi nhỏ, hiếm lỗ lớn), không phải bằng chứng an toàn.
- **Chưa đo được:** *cách vào lệnh đầu* (cần đường giá M1 thật), hedge sau lệnh thứ 16 (chỉ 19 lệnh), tia lệnh, trần lot/số lệnh (chuỗi chưa chạm tới).
- **Nguồn:** `reports/ho_so_bot_that_20261004.md`, `nhan/ho_so_bot.py`, `nhan/ho_so_set.py`.

## R9 — Dựng lại EA cho bot B ("của ta")
- **Cái đã đo:** viết EA MQL5 theo cơ chế đã bóc; chạy trên sàn giả C++ (`nhan/ea_gia_lap.py`) với đường giá tối thiểu *suy từ chính các chuỗi đã tái tạo*.
- **Số:** cơ chế khớp tuyệt đối **2.246/2.246** chuỗi (sai số lot 0, sai số SL lớn nhất 0,05 pip; gồm 1.291 chuỗi khám phá + 955 chuỗi xác nhận); EA tái tạo **2.244/2.244** chuỗi (2 chuỗi thoát tay bị loại), mọi bộ đếm lệch = 0.
- **Nhãn:** MÔ PHỎNG, **VÒNG KHÉP KÍN**. Đường giá được suy từ chính các chuỗi, nên kết quả chỉ chứng minh *logic quản lí lệnh tái tạo được các chuỗi*, **không** chứng minh tín hiệu vào hay lãi trên giá thật.
  Bước thật còn lại: chạy EA này trên *giá thật* ở MT5 tester (Model 0/4) và so lãi/chuỗi với lịch sử.
- **Nguồn:** `tai_lieu/MINI_BRAIN_CANCUBO.md` (mục 1, 2, 10), `nhan/ea_cancubo_lai.py`, `test_ea_cancubo_lai.py`.

## R10 — Danh sách "người thắng" MQL5
- **Cái đã đo:** 400 hồ sơ tín hiệu (ID, mã chính, tăng trưởng, DD công bố, tuổi) → bộ lọc sống ≥ 1 năm/≥ 2 năm.
- **Số:** 400/400 có tăng trưởng > 0 và không hồ sơ nào DD công bố ≥ 80 % (hai điều kiện không phân biệt gì). Tuổi: ≥ 1 năm + tăng trưởng + DD < 80 % = **94**; ≥ 2 năm = **31 (7,8 %)**.
  Mã chính của 31 người thắng: XAUUSD 8 · EURUSD 5 · USDJPY 3 · BTCUSD 3 · AUDCAD 3 · GBPUSD 2 · 7 mã còn lại mỗi mã 1; 2/3 là danh mục nhiều mã. Câu "gần hết là lưới/DCA trên AUDCAD & anh em" **không có bằng chứng** (nhãn mã từng gán sai 19/31).
- **Nhãn:** SỐ CÔNG BỐ (`dd_pct` là số của trang). Không tính được "tỉ lệ có lãi của một tín hiệu bất kỳ".
- **Nguồn:** `du_lieu/mql5_400_phan_loai.csv`, `du_lieu/mql5_31_nguoi_thang.csv` (chỉ ID), `tai_lieu/NGUON_NGUOI_THANG.md`, `tai_lieu/RA_SOAT_KIEN_TRUC_03102026.md`.

## R11 — Phễu bóc cơ chế
- **Số (trước 02/10, lấy từ hồ sơ cũ; `nao.db` mất khi cài lại máy nhà):** 12.078 tài liệu → 285 cơ chế (2,4 %) → 18 mẫu (0,15 %). Tài liệu học thuật (openalex + crossref = 3.313 = 27,4 %) cho ≈ 0 cơ chế.
  Trên **22 EA thật** (12 tác giả độc lập + 10 file của một tác giả): 44 điểm vào lệnh → **7** cơ chế, tất cả từ **3/22** EA; 8 EA breakout khoảng giá/ORB ra **0** (điều kiện vào nằm trong biến trung gian/trạng thái mà DSL "vào theo từng nến" không có).
  Bài đo mốc `mau_thu/do_moc.py`: 0 (18/09) → **2/22 = 9,1 %** (03/10). Phân loại tay 16 chiến lược: điểm vào điền được bằng DSL đầy đủ/một phần/không = 6/6/4 (cả 6 "đầy đủ" phải ghép *tay*); quản lí lệnh khớp 20 nút có sẵn 10/5/0;
  **chạy thẳng EA nguyên bản trên tester: được 5 · rủi ro 2 · không 9** — chủ yếu vì **thiếu tệp `.mqh` của tác giả** (9/16 chiến lược cần; bài học: lấy *cả gói* của tác giả, không chỉ `.mq5`).
- **So với brain2:** cùng bài đo mốc, `mau_thu/do_moc.py` của brain2 đạt 13/22 = **59,1 %** khi *đọc thẳng MQL* — tốt hơn hẳn. **Đừng bê bộ bóc của the-brain sang** (xem `04`, danh sách "không lấy").
- **Nhãn:** đếm/mô phỏng, trước 02/10 — chỉ dùng làm mốc xu hướng. **Nguồn:** `tai_lieu/RA_SOAT_KIEN_TRUC_03102026.md` §2, §4, §8.

## R12 — Bảng điểm vòng lặp (10/10/2026)
- **Số:** 1.573 việc, 105,0 giờ máy: **84 %** giờ máy ở chặng quét trong mẫu; kiểm ngoài mẫu 0,0 %; tìm nguồn 0,2 %; bóc cơ chế 0,0 %; giữ lại 0,0 %; áp dụng 0,0 %.
  698 vùng lãi (cao nguyên) tìm được, **0 vùng** từng kiểm ngoài mẫu; **0** cơ chế "giữ lại" (cần ≥ 3 thị trường qua đoạn xác nhận, ≥ 50 % ứng viên).
- **Bảng thô:** `du_lieu/vung_lai_trong_mau.csv` — 1.055 dòng (cao 698 · đối 182 · ngẫu nhiên 175); cột `xac_nhan_ngoai_mau` **trống ở mọi dòng**; tỉ lệ ô có lãi trung vị 0,948 (cao) vs 0,386 (đối) — *trong mẫu và trên thước đo lạc quan, xem R1/R2*.
- **Nhãn:** đếm từ git (`python3 b.py vong-lap --in`). **Nguồn:** `tai_lieu/VONG_LAP.md`, `nhan/vong_lap.py`.

## R13 — Rộng vs sâu
- **Số:** trên chuỗi có đáp án, tìm rộng ~3.000 điều kiện thấy edge yếu **3/8**; một giả thuyết có chủ đích thấy **8/8** (`b nc kiem 30`).
- **Nhãn:** MÔ PHỎNG (chuỗi có đáp án). **Hiểu:** ngân sách đi vào giả thuyết có lí do kinh tế, không vào lưới tham số mù. **Nguồn:** CLAUDE.md (LUẬT SỐ 1), `tai_lieu/NHA_NGHIEN_CUU.md`.

## R14 — Tốc độ và chi phí
- **Tốc độ (Linux cloud 4 vCPU dùng chung, chuỗi TỔNG HỢP 190.000 nến M15):** nhân C vs Python trên engine lưới **×134** (khớp từng bit; số lệnh, số rổ, bar, id, tầng trùng khít; lãi/maxDD cùng bit trên Python 3.11/3.12/3.13; ASan sạch).
  Một lần đánh giá 1 ô 1.547 ms → 18 ms (×86); quét 54 ô, 1 luồng: 31,2 s → **0,62 s** (×50); 2/4 luồng 0,39/0,35 s (thêm luồng chỉ nhanh thêm 1,6×/1,8×).
  Chưa đo trên Windows/Python 3.14 và chưa đo giây/lần chạy MT5 tester.
- **Hiểu:** nghẽn thật nằm ở *số giả thuyết độc lập* và ở MT5 (một terminal), không ở engine. Chạy nhanh hơn **không** tạo thêm edge — chỉ tạo thêm phép thử, tức thêm chọn lọc (mỗi ô vẫn là MỘT phép thử).
  Không chuyển numba/vectorbt/Rust/GPU: lưới/martingale phụ thuộc đường đi nên vector hóa không mô tả được.
- **Chi phí AI (02/10):** chi phí = số gọi × kích thước ngữ cảnh; token do AI tự sinh (đầu ra + "mang theo") ≈ 52 %.
- **Nguồn:** `tai_lieu/TOC_DO_TEST.md`, `tai_lieu/TOI_UU_TOKEN.md`, `nhan/luoi_nhan.c`.

---

## Những gì CHƯA ĐO (đừng suy diễn thành "chắc là được")
1. Engine v4 (`duong_di`) so với tester trên 125 ô (120 ô còn chờ máy nhà).
2. Bất kỳ kết quả tester nào đã **bao gồm swap** (tester luôn ghi 0; swap chỉ ước).
3. Phí XM thật (spread/commission/swap thật) cho các kết quả lưới "mức sàn" (R6).
4. Kiểm **ngoài mẫu** cho 698 vùng lãi trong mẫu (0 đã kiểm).
5. Tín hiệu vào (entry) của bot A/B — cần đường giá M1 thật + tester.
6. Hedge sau lệnh 16, tia lệnh, trần lot/số lệnh của bot A/B (chuỗi chưa tới mức đó).
7. Bằng chứng *độc lập* cho R6 (chỉ quãng *trước* khi tín hiệu bắt đầu mới độc lập).
8. R5 (+13,26 %/năm) trên MT5 tester; và đỉnh lỗ treo của R5/R6 ở đòn bẩy ≤ 10 thật.
9. PMG: G6 (MT5 single-run), trục phiên, thang ATR khác H1.
10. Mọi kết quả bằng tiền thật. Không có.
11. Theo ghi chú trong kho: bộ đọc diễn đàn đa ngôn ngữ (23 diễn đàn/14 nước) và công cụ `b link` **chưa chạy trên trang thật**.

## Cách đọc con số trong gói này
- Con số có nhãn MÔ PHỎNG chỉ nên dùng để *xếp hạng* và *nhìn hình dạng*; muốn nói "lãi X %/năm" phải qua tester (hoặc engine đã hiệu chuẩn) rồi trừ swap.
- Trước khi tin bất kỳ tỉ lệ "qua" nào, nhớ R2: chuỗi chỉ-nhiễu cũng "qua" 84–88 % với lưới.
- Mỗi số lãi lưới phải đi kèm **đỉnh lỗ treo** và mức đòn bẩy; maxDD đường vốn đẹp vì lãi đã chốt bù lỗ.
- Sổ tay nghiên cứu đã xuất (`du_lieu/so_tay_nghien_cuu/`) có thể cũ hơn `nc.db` ở máy nhà; ngày xuất ghi trong `du_lieu/README.md`.
