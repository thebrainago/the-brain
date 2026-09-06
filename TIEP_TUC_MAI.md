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

## Việc tiếp theo, theo thứ tự

Thứ tự này thay bản 05/09: mục 2 đã cho kết quả âm, và nó **loại luôn giả thuyết
đứng sau mục 3 cũ** (chỉ báo thường cũng chỉ là tín hiệu vào ở sai chân trời —
vừa đo, không phải vậy).

1. **MDE, không phải cơ chế.** Con số quyết định là 39.050 ô chết vì thiếu lệnh
   và 30.462 vì kích hoạt quá thấp. Không thêm cơ chế nào sửa được. Hai đường có
   thật đều đã bị đo và đều gần cạn: **gộp lớp** (05/09: gộp 12 chỉ số chỉ hạ
   ngưỡng 0,535 → 0,511) và **khung nhỏ hơn** (`mde-va-cong-kha-thi`: H1 TỆ hơn
   D1 dù nhiều bar gấp 24). Câu hỏi phải trả lời TRƯỚC khi quét tiếp: **còn đường
   nào hạ MDE mà chưa thử không?** Nếu không, kết luận đúng là *kho cơ chế hiện
   có không đủ để chứng nhận bất cứ thứ gì ở mức Sharpe 0,3-0,5*, và hướng phải
   đổi chứ không phải quét thêm.

2. **81 cơ chế `CHUA_BIET_LY_DO`** — đang nằm trong kho, bị cổng chặn khỏi bề
   mặt, không mất. Việc đúng là **bỏ**, nhưng đọc 5-10 cái trước: trong đó có
   `SessionHighSweepBuy`, `OB bullish rectangle created`, `IHSMC zone detected` —
   họ **vùng**, thứ ngữ pháp chưa nói được. Chúng không có lý do vì bị **dịch
   sai**, không phải vì vô nghĩa. Danh sách đầy đủ ở `reports/DIEN_CO_CHE.json`.

3. **Nguyên thuỷ `vùng` cho FVG / order block / ORB** — mục 4 của bàn giao 05/09,
   chưa động tới, nay có thêm bằng chứng ủng hộ: 2.925 ô chết vì
   `DSL chi_bao='gio'` (cơ chế phiên chạy trên D1), và 5/5 spec bị bộ chặn hiển
   nhiên mới bắt đều thuộc họ FVG. Kho giữ 14 định nghĩa FVG, 19 order block, 23
   cấu trúc/BOS — tất cả đang bị dịch thành so sánh từng nến, tức dịch sai.

### Vướng mắc còn lại (chưa sửa)

- **48 câu `co_che` do LLM viết chưa được thẩm định.** Qua được cổng cú pháp, vài
  câu gần như diễn lại luật bằng từ ngữ về người. Đánh dấu
  `co_che_nguon = "llm_2026_09_06"` để truy ngược. Cổng `co_che` chỉ chặn được sự
  **vắng mặt**, không chặn được sự **rỗng**.
- `reports/LOI_RA_D1.json` dùng tên **TRƯỚC** khi chuẩn hoá — đối chiếu phải đi
  qua `chuan_hoa_ten`. Bản kho cũ ở `config/co_che_dsl.truoc_sua_ten.json`.
- Cổng `kiem_khai_bao` mới chỉ áp ở `loc()`; `nap_vao_mau` vẫn nạp mọi thứ, nên
  đường nào gọi thẳng `MAU.MAU` vẫn thấy đủ 557.
- `test_hien_phap` ĐỎ cũ đã hết: 7 module của 05/09 nay đã có test.

## KHONG DUOC QUEN (bo sung 03/09)
- `b mang` TRUOC khi san bat cu thu gi.
- **Lam "giong nguoi" qua tay thi phan tac dung**: `requests.get` tran 4/4 =
  200; phien giu cookie + Referer 4/4 = 403.
- `thu_thap` ghi vao bang `artifact`, KHONG vao `tai_lieu`.
- Payload artifact LONG mot tang: ma o `payload["payload"]["content"]`.
- `Accept-Encoding: br` khi khong co brotli -> HTTP 200 nhung `r.text` RAC.
