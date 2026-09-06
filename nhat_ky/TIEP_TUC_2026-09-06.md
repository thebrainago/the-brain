# TIEP TUC NGAY MAI — chot phien 2026-09-06 16:31

do ho loi ra 182.550 o -> SAN_SANG_V4 = 0 (chan troi khong phai nut that); sua duong LLM chet; ap cong kiem_khai_bao cho 169 co che da o trong kho

## Trang thai do duoc luc chot
> May tu dien phan nay luc `b ket`. **Dung sua tay** — sua thi mai het so sanh
> duoc. Cot "doi" so voi moc 2026-09-05.

| chi so | hom nay | doi |
|---|---:|---:|
| file test (lab) | 87 | +9 |
| ham test (lab) | 1207 | +106 |
| file test (ds/) | 82 |  |
| bang gia .parquet | 269 |  |
| dong so FDR | 1807 |  |
|   trong do bac bo | 406 |  |
| ung vien xep hang | 567 |  |
| ban doc da thu | 6658 |  |
| co che trong thu vien | 32 |  |
| van de con mo | 12 |  |
|   muc NANG | 3 |  |
| viec dang CHO | 2 |  |
| file .py o goc lab | 214 | +13 |

- co DUNG_LAI: **CO (he dang nam im)**
- viec CHO theo loai: bac_cau_san=1, mt5_tick=1
- commit hom nay:
```
b1888ff 2026-09-06: bao cao phien + anh chup be mat truoc khi don kho
315aea2 do ho loi ra: 182.550 o, SAN_SANG_V4 = 0 - chan troi khong phai nut that
3ac77c9 cong chua tung ap cho hang da o trong kho: 169/540 co che khong qua noi
91c2b49 do spread that cho ca be mat: 44 -> 86 ma giao dich duoc
924c789 cong ngu phap: bi danh chi bao, phep ==, va chan dieu kien hien nhien
```
- file dang doi luc chot: **1**

## Một đoạn đọc là hiểu cả phiên

Phiên sáng làm xong mục 1 (đo spread thật: **44 → 86 mã giao dịch được**, riêng
D1 là **75 mã**). Câu hỏi tự nhiên: vũ trụ giao dịch được rộng gấp đôi thì bề mặt
đẻ ra bao nhiêu ứng viên? **Không cái nào.** 13 ứng viên `SẴN_SÀNG_V4`, **11 nằm
trên `YH_NASDAQ`**, 1 `YH_TSX`, 1 `EURILS` — cả ba đều `do_tin = KHAI`.

Nên phiên chiều làm mục 2 với giả thuyết: tín hiệu không vô giá trị, ta đang đo
chúng ở **sai chân trời**. 447/540 cơ chế không có `ra`, và 218 trong số đó có
`giu = 1` — số mặc định của `sinh_tu_spec`, không ai chọn nó cả; bản gốc *không
thể* nói gì về lối ra vì 190/389 file là chỉ báo, chúng vẽ mũi tên chứ không đặt
lệnh.

`quet_loi_ra.py` — **2.434 biến thể × 75 tài sản = 182.550 ô, 33 phút**:
chân trời **có** quan trọng (tỷ lệ `NÊN_GỘP` đi từ **15,1% ở giữ 1 nến lên 29,0%
ở giữ 10 nến**, 208/447 cơ chế sống thêm ở chân trời khác) — **nhưng
`SẴN_SÀNG_V4` = 0 trên cả 182.550 ô.** Đổi lối ra chuyển cơ chế từ LOẠI sang "có
cơ chế nhưng thiếu lực", không chuyển được cái nào thành ứng viên.

Hiệu chuẩn bộ đo trước khi tin số 0: chạy chính nó lên ba ô mà bề mặt ĐÃ tìm ra
ứng viên → tái tạo đúng cả ba. **Số 0 là phép đo thật, không phải cổng hỏng.**

=> **Nút thắt vẫn là MDE**, đúng như bộ nhớ đã ghi. Ba lý do trượt áp đảo đều về
LỰC: `thiếu_lệnh_để_kết_luận` 39.050 ô · `kích_hoạt_quá_thấp` 30.462 ·
`tần_suất_quá_thấp` 17.486.

**Ba lỗ hổng cấu trúc lộ ra trên đường đi, cùng một họ bệnh — hạ tầng đã có mà
không ai nối dây:**

1. **Đường LLM của The Brain đã tắt lặng lẽ.** `cc_switch_provider = "aibox goi
   moi"` không còn khớp provider nào (tên thật `AiBox qua cau noi`). Mọi lời gọi
   trả `"thiếu OPENAI_API_KEY"`, và `hoi_json` trả `{"loi":...}` chứ không ném —
   nên một mẻ bóc chạy 2 giây và báo "0 cơ chế", **đọc y hệt kết quả âm thật**.
   Sửa: khớp bằng `"aibox"`.
2. **Cổng `kiem_khai_bao` chưa từng áp cho hàng đã ở trong kho: 169/540 không
   qua nổi** (148 thiếu hẳn trường `co_che`). Chúng vào qua cửa sau và vẫn chạy
   trên bề mặt. LLM điền được **48**, trả lời `CHUA_BIET_LY_DO` **81** — 81 đó là
   danh sách chờ **BỎ**, không phải chờ điền nốt. `loc()` nay gọi cổng: bề mặt
   382 → 334.
3. **Ba bộ chặn ở mức khai báo**: `gia <phép> hằng ≤ 0` (27 vế, dấu vết bóc
   hỏng); `_hang_so_gia` đã có từ 05/09 nhưng `loc()` **chưa bao giờ gọi** nên
   `aapl_call_breakout_above_322_50` vẫn lên bề mặt; và 125 tên chưa chuẩn hoá —
   trong đó lộ ra **4 cơ chế trùng tên y hệt, bản thứ hai chưa từng chạy lần nào**
   vì `nap_vao_mau` có `if ten in MAU.MAU: continue`.

Phụ phẩm: sau khi chặn ở mức khai báo, `gần_không_bao_giờ_vào` tụt 103 → 46. Không
phải bớt bệnh, mà vì **lý do từ chối trở nên đúng tên**.

## Phiên chiều — "sửa lại hết"

Ba vướng mắc của phiên sáng đã đóng, và một nguyên thuỷ mới ra đời.

1. **Cổng về đúng CỬA.** `loc()` không phải cửa duy nhất vào `MAU.MAU` —
   `do_on_dinh`, `hinh_dang_vs_null`, `cham_lai_the_he`, `ngoai_sinh`,
   `p_null_vs_ung_vien` gọi thẳng `nap_vao_mau`. Cổng nay ở `nap_vao_mau`, và
   giữ bản ghi từ chối (`BI_TU_CHOI_KHI_NAP`) để `loc()` đọc.

2. **`co_che` KHÔNG điền được bằng máy.** Lượt thẩm định độc lập (rubric +
   "nghi ngờ thì BÁC") bác **41/48** câu LLM viết buổi sáng, kể cả một câu
   *ngược chiều với luật*. Còn 7. Ròng: 169 → **166** cơ chế trượt cổng, tức
   cứu được **3**. Và bộ thẩm định cũng **không ổn định** (`bullbreakout` được
   giữ lượt 1, bị bác lượt 2) — ghi ra chứ không giấu.

3. **Nguyên thuỷ `vùng`** (`ngu_phap._vung`): họ FVG/order block/ORB từ 0 lên
   **33 cơ chế chạy được**. Bóc lại 49 file: 92 khai báo, **68 dùng `vung`**,
   vào kho 34. Lượt đầu ra **0/9** dù bản tóm tắt ngữ pháp đã liệt kê — lời nhắc
   kết bằng ví dụ chỉ có dạng `{trai,phep,phai}`, mô hình bám ví dụ chứ không
   bám tham chiếu.

**Ba lỗi do bài canary lôi ra, không cái nào lộ nếu chỉ đọc kết quả:**
   - vùng **tự kích hoạt ở chính nến sinh** → `song` và `huy` là **nút giả**
     (song 20/21/23/28 đều ra đúng 20). Nay vùng sống từ nến SAU nến sinh.
   - `_dat` **không đặt được** tham số trong danh sách lồng (`tao0` là token
     dính liền) → `tham_so_cua` liệt kê mà `ap_tham_so` trả spec y hệt.
   - `kiem_khong_nhin_truoc` **gần như mù với cơ chế thưa**: 40 mốc ngẫu nhiên
     không trúng mốc nào trong 16/400 bar bị rò rỉ. Lực của bộ đo tỉ lệ với tần
     suất kích hoạt. Nay ưu tiên mốc có tín hiệu; hiệu chuẩn hai chiều: bắt được
     canary, 0/374 dương tính giả.

**Và họ vùng dừng ở đúng bức tường ấy:** 33 cơ chế, 4.158 ô, 1.061 NÊN_GỘP,
**0 SẴN_SÀNG_V4**. Nhưng ô tốt nhất của nó nằm trên tài sản **giao dịch được**
(XM_US100CASH 0,58 · DE40 0,55 · XM_US30CASH 0,50), 37-153 lệnh — khác hẳn 12
ứng viên của bề mặt vốn nằm hết trên `YH_`.

Đó là lần thứ **ba** trong ngày cùng một bức tường.

## Phiên tối — hệ đã PASS ra tick THẬT lần đầu

Sổ cái có **2 giả thuyết PASS** và **cả hai chưa bao giờ chạy MT5 tester**. Lần
chạy tester gần nhất của cả dự án là **01/09** — năm ngày thuần Python, trong đó
hệ ba lần kết luận "nút thắt là MDE".

`lab/ea_MeanRevZ5.mq5` + `lab/chay_tester_z5.py`. Luật nguyên văn từ kho:
vào khi `zscore(close,5) < −1`, ra khi `>= −1`, chỉ MUA.

**Kết quả** (US100Cash H1 / tín hiệu D1, 2011.09.19–2026.07.29, Model=2,
lot 0,10 cố định, vốn 10.000 USD):

```
305 lệnh · lãi ròng 1.374,58 USD · PF 1,77 · Sharpe 1,13
sụt giảm vốn sở hữu tối đa 3,28% · hệ số hồi phục 3,89
```

Đối chiếu Python: **463 lần mở vị thế, 67,1 bps/lệnh → tester 305 lệnh,
46,4 bps/lệnh**. Cùng dấu, cùng bậc độ lớn, nhưng **ít hơn 34% số lệnh**.

**Ba lần chạy đầu đều hỏng, và cả ba đều ghi báo cáo "0 lệnh" — đọc y hệt kết
quả âm:**
1. Model=1 trên 15 năm D1 phải SINH tick M1 → ngốn 20.480 MB rồi chết
   `cannot generate history data` (đĩa còn 12 GB).
2. Model=2 trên khung D1: MT5 đặt tick ở OPEN nến D1 = 00:00, **ngoài phiên**
   của CFD chỉ số → 463 lệnh đều `Market closed`.
3. Chuyển EA sang H1 (tín hiệu vẫn từ D1): còn 3 lệnh — nến D1 đổi lúc 00:00 vẫn
   ngoài phiên.

Sửa thật: EA **ghi nhớ ý định** rồi khớp ở nến H1 đầu tiên có thể giao dịch. Đó
cũng là cách một bot thật phải chạy, không phải mẹo của tester.

## Việc tiếp theo, theo thứ tự

Ba mục dưới đây là **chủ dự án chốt cuối phiên 06/09**, sau khi đọc số đo suất
bóc và kết quả tester trong ngày.

1. **SEEKER: ưu tiên nguồn CÓ SẴN FILE.** Xếp hạng nguồn theo *có file hay
   không*, không theo độ dài hay uy tín. Ưu tiên `.mq5` / `.ex5` / `.set` /
   Pine — có `.ex5` + `.set` là **chạy tester được ngay**, bỏ qua hẳn khâu dễ
   sai nhất. **Đào sâu vào group, nhất là nhóm Telegram share EA** — khoá và
   phiên đã có sẵn (`nhan/telegram.py`, `telethon_ban`); nhóm là chỗ file được
   đính kèm, khác với kênh. Bỏ công: bài phân tích/quan điểm (300 bản → 33 cơ
   chế, phần lớn chết vòng sau), video không transcript.

2. **BỘ LỌC: sửa ba chỗ.**
   - **Đưa placebo ĐA TÀI SẢN lên làm cổng tự động.** Hôm nay nó giết 5 cơ chế
     "mạnh trên US100" (Sharpe 1,66 · 1,47 · 1,25 · 0,99 · 0,84). Sharpe một mã
     và placebo một mã **đều không đủ**. Giá: ~2,5 phút/symbol cho một lượt gộp
     bản thật + 101 bản dịch.
   - **Cổng `co_che` chuyển từ cửa vào sang cửa ra tiền.** Cửa vào chỉ chặn thứ
     *không kiểm định được*: spec hỏng · kích hoạt 0% · mua-giữ trá hình · trùng
     điều kiện. Lý do: đo được rằng cổng không phân biệt tốt/xấu — nó chặn 4 cơ
     chế mà 4 cái đó hoá ra là rác, nhưng chặn vì thiếu một câu văn chứ không
     vì chất lượng.
   - **Bỏ hẳn vai phán xử của LLM.** Giữ nó ở khâu dịch. Đo được: nó bác 41/48
     câu do chính nó viết, và tự mâu thuẫn giữa hai lượt.

3. **Hai hệ, không phải một.** Cuối phiên tìm ra `quantora_ma_dashboard_sell`
   (bán khi close dưới cả bốn EMA 20/50/100/200) — placebo đạt 3/4 chỉ số
   y như z5, và cũng trượt đúng GER40. Nó nằm trong nhóm **32/40 cơ chế qua
   train+holdout mà chưa kịp thử placebo** — bài học: chạy placebo cho **mọi**
   ứng viên, đừng chọn tay. Rẻ: ~5 phút cho 40 cơ chế × 4 mã.
   Việc còn thiếu cho `quantora`: so mua-giữ ở cùng sụt giảm · chia theo năm ·
   %/năm ở đòn bẩy thật. z5 đã có đủ ba.

### Vướng mắc còn lại (chưa sửa)

- **Chênh lệch Python 463 lệnh vs tester 305 lệnh** vẫn chưa truy. Nhưng sau
  phiên tối nó tụt ưu tiên: nếu tester là trọng tài thì con số của Python sai
  bao nhiêu cũng chỉ ảnh hưởng khâu sàng thô.
- Bộ đo `Sharpe` của MT5 tester **không cùng định nghĩa** với Sharpe năm hoá của
  Python — dùng để XẾP HẠNG thì được, đừng so trực tiếp hai con số.
- `GOLD` trượt khỏi lượt quét đa tài sản (tên symbol) — chưa kiểm.

- **Bộ thẩm định `co_che` không ổn định giữa hai lượt.** Cùng dữ liệu, đổi phán
  xử. Nếu còn dùng nó thì phải chạy **nhiều lượt và lấy đa số**, hoặc chấp nhận
  nó chỉ dùng để LỌC THÔ.
- 4 câu `co_che` chưa được phán xử lượt nào (`_tham_dinh_co_che.py` chạy lại là
  xong, nhưng xem gạch đầu dòng trên).
- `TRAN_VUNG_SONG = 64` là chặn an toàn chưa ai đo: chưa biết có cơ chế thật nào
  cần hơn 64 vùng sống cùng lúc không.
- 8 khai báo vùng bị từ chối vì `vung.tao` thiếu vế `trai`/`phai` — đó là LLM
  trả sai định dạng, `chuan_hoa_spec` có thể vá được như nó đã vá `giu`.

## KHONG DUOC QUEN (bo sung 03/09)
- `b mang` TRUOC khi san bat cu thu gi.
- **Lam "giong nguoi" qua tay thi phan tac dung**: `requests.get` tran 4/4 =
  200; phien giu cookie + Referer 4/4 = 403.
- `thu_thap` ghi vao bang `artifact`, KHONG vao `tai_lieu`.
- Payload artifact LONG mot tang: ma o `payload["payload"]["content"]`.
- `Accept-Encoding: br` khi khong co brotli -> HTTP 200 nhung `r.text` RAC.
