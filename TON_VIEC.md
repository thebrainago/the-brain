# TỒN VIỆC — chốt 15/09/2026

Anh nói đúng: tồn từ hôm qua, hôm nay lại thêm. Đây là **toàn bộ** danh sách,
xếp theo thứ tự nên làm, không phải theo thứ tự tôi nghĩ ra.

---

## A. LÀM ĐƯỢC HÔM NAY (đã xong, không cần đụng lại)

1. **3 hệ làn nhanh đã qua MT5 tester thật** — 2 sống, 1 âm.
   AUDCAD `rsi_dao_chieu` **+11,92%/năm** ở sụt giảm 20% (mốc mua-giữ +1,14%);
   `ou_quay_ve n50 mua` +8,45%. EURGBP `ou n200 mua` +8,95%.
   `mat_can_bang_lenh_dong_cua` **−1,65%** → bỏ khỏi làn nhanh.
   Chi tiết: `BAO_CAO_2026_09_15.md`.
2. **Sửa `than_nen` mất dấu khi dịch sang MQL5** — 56/3189 cơ chế đang ra 0 lệnh oan.
3. **Bảng tester so được ở cùng rủi ro** (cột `%/nam@DD20`) + `--lot` + `--loc` nhiều bộ lọc.
4. **`nhan/tinh_cach_chieu.py`** — tính cách tài sản → chiều lưới / bước / chân trời giữ.

---

## B. ANH GIAO HÔM NAY — CHƯA LÀM

Xếp theo "gần tiền" nhất trước.

### B1. Ghép nhiều hệ trên cùng một cặp + tăng lot  ← ĐI ĐẦU
Anh: *"Với các cặp đang có kỳ vọng dương thì tăng lot lên chấp nhận dd cao hơn
để có lãi to hơn, cùng 1 cặp thì kết hợp nhiều hệ thống lại."*

Làm được ngay: AUDCAD có **4 hệ dương** ở holdout thật. Chạy chúng **đồng thời**
một tài khoản (EA nhiều slot, mỗi slot một magic — đã có, ghi ở
`ea-nhieu-slot-chay-dong-thoi`), đo sụt giảm của **đường vốn gộp**, rồi mới
chọn lot. Câu hỏi thật: bốn chân này tương quan bao nhiêu — ghép vào có giảm
sụt giảm không, hay chỉ cộng rủi ro.

### B2. Tương quan giữa các cặp
Đã đo tính cách **từng cặp** (158 mã) nhưng **chưa đo tương quan cặp–cặp**, nên
chưa trả lời được "ghép AUDCAD với EURGBP thì lợi hay hại". `nhan/tinh_cach_chieu.py`
mới trả lời được câu một cặp.

### B3. Nối `tinh_cach_chieu` vào đường chạy
Module đã xây và chạy đúng, nhưng **chưa cắm vào `pmg_quet.quet()`** — chiều vẫn
đang quét mù. Đây đúng là họ lỗi "luật có viết nhưng không nằm trên đường chạy".
Một điểm cần xem khi nối: **XM_US100CASH lệch nhau giữa hai khung** — hồ sơ D1
nói HỒI_QUY (→ đánh về giữa) nhưng G0 trên M5 nghiêng WITH ở 6/8 chân trời
(không cái nào qua FDR). Module đang ưu tiên G0, nhưng ô này G0 rỗng nên nó rơi
về D1. Phải quyết: quét G0 cho US100 rồi mới đặt lưới, đừng tin D1.

### B4. Bổ sung họ quản trị lệnh còn thiếu
Anh liệt kê: *"trailing dương cắt âm, cắt từng phần"*, đặt lưới, xử lí lệnh.
Hiện `quan_tri_nhieu.bo_luat()` chỉ có **5 họ**: hedge · luoi_dca · stop_2_dau ·
tt_stop_doi · thoi_gian. **Thiếu hẳn:**
- cắt từng phần (partial close / scale-out)
- nhồi thuận khi đang lãi (pyramid)
- trailing bất đối xứng (nới bên lãi, thắt bên lỗ)
- đóng cả rổ khi tổng lãi chạm mốc (basket close)

### B5. Dùng phân tích kỹ thuật chọn chiều gỡ lệnh
Anh: *"sử dụng cả phân tích kĩ thuật làm indi để chọn chiều gỡ lệnh"*. Hiện
lưới gỡ theo khoảng cách thuần, không hỏi chỉ báo nào.

### B6. Bóc cơ chế từ mẻ SEEKER
`_san_quan_tri_lenh.py` đang chạy nền (21 từ khoá × 7 nguồn: hedging, trailing,
partial close, bot không điều kiện, **audcad hedging**, **eurgbp grid**...).
GitHub đã về 17 tài liệu mới. Xong thì `b boc` để bóc cơ chế ra.

### B7. Chạy lại 56 cơ chế dùng `than_nen`
Trước nay chúng ra 0 lệnh oan trên mọi lượt tester. Giờ sửa rồi, phải chạy lại.

---

## C. TỒN TỪ HÔM QUA (14/09) — CHƯA ĐỘNG

1. **Đổi mật khẩu MT5.** Tôi đã in nó ra màn hình hôm qua nên nó nằm trong nhật
   ký hội thoại. `config/tai_khoan.json` vẫn ngoài git, nhưng vẫn phải đổi.
2. **Issue #124** — 5 spec có điều kiện luôn đúng. Cần anh quyết: xoá hay sửa.
3. **Issues #122/#123** — 37+2 spec thiếu `co_che` thật. Không được bịa; máy điền
   thì 48 cái vào, thẩm định bác 41.
4. **PMG trục D2 (phiên) và D3 (khung M15/H4/D1)** — đã xây, chưa quét lần nào.
5. **Đo 11 họ quản trị theo từng thời kỳ** thay vì một bảng gộp.
6. **Hai hệ AUDCAD → demo.** Đây là chặng cuối trước tiền thật.

---

## D. Điều tôi làm sai trong tổ chức, để không lặp

- Có dữ liệu đo rồi mà không nối vào đường chạy (`tinh_cach_chieu` đáng lẽ phải
  có từ lúc hồ sơ 158 mã được tính xong).
- Có SEEKER mà không dùng khi nhận đề bài mới. Từ khoá quản trị lệnh nằm trong
  `TU_KHOA_GOC` từ 13/09 nhưng chưa lần nào được săn cho một đề bài cụ thể.
- Đi sâu vào kiểm chứng một nhánh trước khi mở đủ rộng các nhánh anh đã liệt kê.

---

# BỔ SUNG khuya 15/09 — SEEKER chỉ đọc tiếng Anh

Anh chỉ ra hai chỗ, cả hai đều đúng và đều là lỗ hổng kiến trúc chứ không phải
ca lẻ.

## Đã sửa được trong đêm

**1. Từ khoá đa ngôn ngữ** — `nhan/tu_khoa_da_ngon_ngu.py`
167 từ khoá / 7 khái niệm / 15 thứ tiếng, thay cho 21 từ chỉ tiếng Anh.
Không phải dịch máy — giữ **từ lóng bản địa** vì đó mới là chỗ tài liệu nằm:
`両建て` (Nhật, giữ đồng thời mua+bán) · `ナンピン` (nhồi khi lỗ) ·
`усреднение` (Nga) · `补仓`/`加仓` (Trung, phân biệt nhồi khi lỗ với khi lãi).
Tiếng Anh gộp cả ba thứ sau vào một chữ "averaging" nên tìm bằng tiếng Anh
không ra được kho đó.
→ Đã chạy: **102 tài liệu mới** vào kho.

**2. Diễn đàn quốc gia** — `_do_dien_dan_quoc_gia.py` + `_thu_dien_dan.py`
Đo 18 diễn đàn, **7 vào được**: mql5.com/ru/forum (106 link), traderviet (89),
thaiforexschool (55), note.com (50), fx-on.com (28), smart-lab (1).
→ Đã chạy thu thập: 19 tài liệu mới, 4 thứ tiếng.

## Ba lỗ hổng phát hiện khi làm (chưa sửa)

**a. Lớp cộng đồng phi-Anh thêm 30/08 chưa từng chạy.**
qiita/habr/smart-lab/cnblogs/velog nằm trong `NGUON_TRINH_DUYET` — chỉ chạy khi
Chrome CDP mở. CDP đang tắt. Tức cả lớp đó đã nằm ngoài đường chạy nửa tháng.
Chúng đọc được bằng `requests` thuần (đã đo). Phải chuyển sang đường thường.

**b. Bộ lọc tiêu đề quá chặt — mẻ thu thập gần như trắng.**
mql5 forum đọc 75 bài, **0 bài qua lọc**. thaiforexschool 48 → 0. fx-on 28 → 0.
Chỉ note_fx 18/75. Lý do: tôi lọc theo từ khoá trong **tiêu đề**, mà tiêu đề
diễn đàn thường chung chung ("Вопрос по советнику"). Phải lọc theo **thân bài**,
hoặc bỏ lọc ở khâu thu và để cổng bóc cơ chế lọc — cổng đã có sẵn cho việc đó.
Đây đúng họ lỗi "bộ dò phải thấy được cái CÓ".

**c. Mọi URL mql5 trong seeker vẫn ghim `/en/`.**
mql5.com có đủ 15 bản địa phương và **diễn đàn từng bản khác nhau**. Mới cắm
`/ru/` vào `_thu_dien_dan.py`, chưa sửa trong `tru/seeker.py`.

## Anh nói đúng về tư duy quản lí

Ba lần trong một phiên tôi xây xong một thứ rồi để nó nằm ngoài đường chạy:
`tinh_cach_chieu` chưa cắm vào `pmg_quet`; lớp cộng đồng phi-Anh mắc sau CDP;
`_thu_dien_dan` chưa đăng ký vào `seeker.NGUON`. Cùng một họ lỗi, và nó là họ
lỗi chính của dự án này (`b ban-do` vẫn truy ra 31 module mồ côi).

**Việc đầu tiên của phiên sau nên là: chạy `b ban-do`, đối chiếu mọi thứ dựng
hôm nay, cắm hết vào đường chạy — trước khi xây thêm bất cứ cái gì.**

---

## C. ANH GIAO TỐI 15→16/09 — GHI ĐỂ MAI LÀM

### C0. Báo cáo phải là TOÀN THE BRAIN, không chỉ AUDCAD
Sáng mai `b vao` rồi viết một báo cáo tổng: 3 module (SEEKER · QUANTLAB ·
EVO/FINDER) + HEPHAESTUS + PMG đang ở đâu, cái gì mới trong tuần, nút thắt hiện
tại — KHÔNG chỉ AUDCAD. (Hôm nay tôi báo cáo lệch, chỉ nói AUDCAD.)

### C1. AUDCAD — quản trị lệnh KHÔNG NHẤT QUÁN (lỗ hổng thật)  ← SỬA TRƯỚC
Anh chỉ đúng: cùng một nhóm thoát RSI (cụm 1 và cụm 3 đều VÀO khi RSI(14) cắt
lên 30) nhưng **cụm 1 giữ 20 bar, cụm 3 giữ 50 bar** — khi kích hoạt sẽ mở 1–3
lệnh cùng lúc mà mỗi lệnh quản lý một kiểu. Mở 1–3 lệnh thì không sao, nhưng
**cách quản lý lệnh phải NHẤT QUÁN cho cả danh mục**. Việc:
- Gộp các cụm trùng tín hiệu vào (RSI-cross-30 long) thành MỘT chân, một chính
  sách thoát duy nhất (đừng để hai hằng số giữ khác nhau trên cùng entry).
- Định nghĩa 1 chính sách quản trị chung cho cả 8 chân, rồi mới so với hiện tại.

### C2. Thêm TRAILING STOP vào AUDCAD — xem có tốt hơn không
Anh: *"khi add trailingstop vào xem xem có đạt được hiệu quả tốt hơn không."*
Harness ĐÃ CÓ: `_quan_tri_ghep.py` (sweep 5 nhánh: trailing · đặt-huề · tỉa ·
nhồi · kiểu-ra; mốc mua-giữ KHÔNG chịu quản trị để so cùng rủi ro). Việc:
- Tổng quát hoá nó cho **AUDCAD H4** (hiện cứng US100Cash/H1/D1): thêm `--khung`,
  đặt symbol `AUDCADmicro`, `sinh(khung="H4")`.
- **Model=0 (every-tick) cần tick M1** — máy chỉ có M1 từ 2026-05-28, phải TẢI M1
  AUDCAD nhiều năm trước khi chạy trailing-trong-nến; nếu không thì như hiện tại
  chỉ đo được quản trị THEO NẾN ĐÓNG (Model=2). Ghi rõ giới hạn này khi báo số.
- Chạy trên 2 chân mạnh nhất trước: cụm 4 `ou_quay_ve_dsl_n50_z2.5_mua` (PF 2,75)
  + cụm 1 `dashboard_mean_reversion_signal` (PF 1,86).
- Nhớ luật: [[trailing-la-co-che-manh-nhat-do-duoc]] (holdout x4,8) NHƯNG
  [[quan-tri-chi-dat-hue-song-sot]] (trailing −68% trên hệ thoát nhanh) và
  [[quan-tri-can-cho-de-hoat-dong]] (trailing cần CHỖ; hệ giữ 5–60 bar này có chỗ).
  Tester là trọng tài, không tin số Python.

### C3. HỌ CHIẾN LƯỢC MỚI — nến vol lớn ở RSI cực trị + râu nến quét
Anh: *"test thử chiến lược bắt những cây nến vol lớn khi RSI quá bán quá mua
(thử các số <30 và >70), thử vào lệnh ở những cây có độ dài đột biến (râu nến
quét)… dạng đánh như này có thể nghĩ thêm ra nhiều kiểu nữa."* Đây là một HỌ, mở
lưới ý tưởng chứ không một hệ:
- **Nến vol đột biến + RSI cực trị**: volume(hoặc range) > k×trung bình VÀ RSI<X
  (quét X ∈ 20/25/30) cho long, RSI>Y (quét 70/75/80) cho short. Vào đảo chiều.
- **Râu nến quét (wick sweep / stop-hunt)**: nến có râu dưới/trên dài đột biến
  (râu > k×thân, hoặc > k×ATR) quét qua đáy/đỉnh gần rồi đóng thân ngược lại →
  vào theo hướng đóng nến. (Gần cụm 7 liqsweep_ifvg đã sống — mở rộng họ này.)
- **Biến thể để nghĩ thêm**: kết hợp vol-spike + wick + RSI; lọc theo phiên;
  ngưỡng theo ATR thay hằng số; thử cả M15/H1/H4; xác nhận nến sau.
- Quét như PMG-G0 (placebo khối vị thế, FDR-BH), rồi ra tester thật.

### C4. Rồi CHẠY LẠI quy trình tìm tài liệu + tự nghiên cứu
Sau khi bổ sung họ C3 vào nhiệm vụ: `b san-nguon AUDCAD` / `b day-chuyen AUDCAD`
(3 luồng: săn nguồn theo tài sản + tên hệ + MQL5 → đọc song song → bóc cơ chế)
+ `b noi-sinh AUDCAD H4` (sinh cơ chế từ chính lịch sử), nhắm đúng vol-spike /
wick-sweep / RSI-extreme để nạp thêm ứng viên vào kho rồi lọc.

