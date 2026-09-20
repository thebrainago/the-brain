# GÓI: NỘI SINH — luận điểm nói ngược với lệnh

Tìm ra khi quét **cùng dạng lỗi** vừa sửa ở HEPHAESTUS. Hoá ra LUỒNG 3 của dây
chuyền bị nặng hơn nhiều, và có một lỗi thứ hai mà lệch chiều chỉ là triệu chứng.

## ĐO ĐƯỢC TRƯỚC KHI SỬA

```
sinh            585 cơ chế  ... long   585 / short 0
sinh_cap      2.998 cơ chế  ... long 2.998 / short 0
sinh_xu_huong    86 cơ chế  ... long    86 / short 0
```

**3.669 cơ chế, 3.669 long, 0 short.** Cả ba bộ sinh nhận `chieu: int = 1`, và
**không lời gọi nào trong cả kho truyền `-1`**.

## LỖI THỨ HAI, NẶNG HƠN: CÂU MÀN HÌNH DUYỆT ĐỌC NÓI NGƯỢC VỚI LỆNH

Lệch chiều là thiếu sót. Cái này là **mâu thuẫn đang chạy**. Bảng `CO_CHE_CUA`
có những ô mà luận điểm là một lập luận BÁN, nhưng `chieu` vẫn bị gán cứng `+1`:

| cơ chế | chiều | luận điểm đi kèm |
|---|---|---|
| `ns_heiken_<_q10_giu5` | **+1 MUA** | *"Thân HA dày chiều giảm: áp lực bán kéo dài qua nhiều bar."* |
| `ns_supertrend10_<_q20_giu5` | **+1 MUA** | *"chương trình bán đang chạy"* |
| `ns_donchian_<_...` | **+1 MUA** | *"nguồn cung bán ép tiếp"* |

`LUAT_THO_CODE.md` mục 4 ghi rõ câu `co_che` là **câu MÀN HÌNH DUYỆT ĐỌC**. Cổng
đang đọc một câu nói ngược với lệnh, và **không cổng nào bắt được** vì không cổng
nào đối chiếu VĂN với SỐ.

Cùng dạng ở `sinh_xu_huong`: `CO_CHE_CAP["<"]` viết *"đứng ngoài là một vị thế có
giá"* — lập luận không-mua — mà vẫn gán `+1`.

## CÁCH SỬA: SUY CHIỀU TỪ LUẬN ĐIỂM, KHÔNG GÁN CỨNG

`CHIEU_TU_HO[(ho, phía ngưỡng)]`:

| họ | thấp | cao |
|---|---|---|
| `quay_ve_trung_binh` | **+1** bán kiệt sức → mua | **−1** mua quá đà → bán |
| `xu_huong` | **−1** áp lực bán còn tiếp | **+1** lực mua còn tiếp |
| `pha_vo` | **−1** thủng đáy kênh | **+1** phá đỉnh kênh |
| `dao_chieu` | **+1** | **−1** |
| `bien_dong` | **KHÔNG suy ra được** → sinh cả hai chiều |

`chieu` nay chỉ còn là **bộ lọc**: `0` lấy cả hai (mặc định), `±1` lấy một bên.

## `CO_CHE_NGUOC` — cách đọc thứ hai

Mỗi cực trị có **đúng hai** cách đọc kinh tế, và chúng đi hai chiều ngược nhau:

- **KIỆT SỨC** — lực đẩy giá tới đáy đã hết → giá lùi lại
- **CÒN TIẾP** — lực đẩy giá vẫn đang chạy → giá đi tiếp

`CO_CHE_CUA` chỉ khai MỘT cách đọc mỗi ô, nên một nửa không gian giả thuyết chưa
bao giờ được sinh. Đã viết **24 cách đọc còn lại**. Bốn toán hạng không có mục
này (`adx`, `atr`, `bien_do`, `phan_vi`) đúng là bốn cái **không có chiều** —
ADX đo *độ mạnh* xu hướng chứ không đo dấu; một ADX = 40 xuất hiện cả trong cơn
tăng lẫn cơn sụp.

## SAU KHI SỬA

```
sinh          1.170 cơ chế ... long 575 / short 595 | 0 trùng tên
sinh_xu_huong    94 cơ chế ... long  47 / short  47 | 0 trùng tên
sinh_cap         16 cơ chế ... long   8 / short   8 | 0 trùng tên   (mẫu 3 toán hạng)
```

`ns2_rsi14<q5_cci20<q5_giu5` (+1, *"sức ép bán tới hạn; ai chịu ôm vị thế…"*) và
`..._b` (−1, *"một vị thế lớn đang được thoát dần…"*) — **cùng điều kiện, hai
luận điểm khác nhau, mỗi cái đúng chiều của chính nó**.

## BA LỖI BẮT ĐƯỢC BỞI CHÍNH BÀI KIỂM CỦA TÔI

1. `dao_chieu` (mẫu nến) thiếu trong `CHIEU_TU_HO` → 16 cơ chế mẫu nến sẽ im.
2. Một câu gương của tôi cho cơ chế **BÁN** chứa cụm *"được trả cao hơn"* — đúng
   nghĩa nhưng đọc nhập nhằng trên màn hình duyệt. Đã viết lại.
3. `heiken thấp`: hai cách đọc trùng **61,5%** từ → đúng cái "hai phép thử trả
   tiền FDR hai lần cho một câu hỏi" mà tôi đang canh. Đã viết lại thành một lập
   luận khác hẳn (bán theo **chương trình** cạn đột ngột, không tàn dần).

## VÀ MỘT LỖI TÔI TỰ TẠO RỒI TỰ BẮT

Đổi mặc định thành `chieu=0` làm `sinh_cap`/`sinh_xu_huong` gán thẳng
`"chieu": 0` — một cơ chế **không có hướng**. Sau đó `_cap_nhat_tri` bản đầu
`return` ngay cặp đầu tiên khớp, mà `_cac_cach_doc` liệt kê `CO_CHE_CUA` trước
(hầu hết đi chiều dương) → **lại lệch hết về MUA, lần này vì THỨ TỰ DUYỆT chứ
không vì một tham số**. Đã đổi thành duyệt hết.

## PHÁT HIỆN KÈM: `sinh_cap` KHÔNG hề chống nhìn trước

`sinh()` có `kiem_khong_nhin_truoc` từ đầu; `sinh_cap` thì **không**. Một cặp
nhìn trước y hệt một cơ chế đơn. Đã thêm.

## CÁI GIÁ PHẢI NÓI RÕ

Không gian giả thuyết **gấp đôi** → tiêu **gấp đôi** suất FDR. Đó là chi phí
thật. Nhưng chỉ thử một chiều không phải là "tiết kiệm FDR" — đó là **tự trả lời
trước câu hỏi**. Không thể tìm ra edge bán nếu không bao giờ thử bán, và trên FX
(long/short đối xứng) một nửa sân đang vô hình.

`sinh()` chạy 149 giây cho 1.170 cơ chế trên 1.200 bar — chậm hơn trước vì nhiều
cách đọc hơn và vì `sinh_cap` nay có thêm chốt nhìn trước.

## VIỆC CHƯA LÀM
- Chưa đo trên **dữ liệu thật** — mới chuỗi tổng hợp.
- Chưa so "cùng ngân sách FDR, có gương vs không gương thì bên nào ra nhiều cấu
  hình `CHAY_DUOC` hơn". Đó mới là phép đo quyết định.

---

## BỔ SUNG: chốt nhìn trước đặt SAI TẦNG (cùng đêm)

Tôi thêm `kiem_khong_nhin_truoc` vào `sinh_cap` ở mức **từng cặp**. Đo được:
**40 giây cho 300 cơ chế**, tức ~9 phút cho trần mặc định 4.000. Đó là một hồi
quy tốc độ do chính tôi tạo.

Chỗ đúng là mức **toán hạng**, và nó đúng về toán: `A VÀ B` chỉ đọc quá khứ khi
cả `A` lẫn `B` chỉ đọc quá khứ — phép hội của hai điều kiện nhân quả thì nhân
quả. `sinh_cap` duyệt tổ hợp nên ~20 toán hạng cho ra hàng nghìn cặp; kiểm ở mức
toán hạng là ~20 lời gọi.

**40 giây → 2 giây (nhanh 20×)**, 150 long / 150 short, 0 trùng tên, và chốt
chặn vẫn nguyên.

### Que thử bị chính cổng khai báo từ chối

`kiem_khai_bao` từ chối que thử vì `co_che = "probe"` không phải một câu thật —
*cổng đó đang làm đúng việc của nó*, chỉ là que thử không phải đối tượng của nó
(nó không bao giờ vào kho). Gọi nó ở đó làm `sinh_cap` trả về **0 cơ chế**.

### Bài hiệu chuẩn ngược đầu tiên của tôi VÔ NGHĨA

Tôi định dùng `tre` với `n` âm làm toán hạng nhìn trước. Đo được: `tre(-3)[0]`
trả **NaN** chứ không trả `close[3]` — ngữ pháp không cho dịch ngược. Nên bài
kiểm "xanh" đó đang chấm điểm trên một đầu vào **không hề nhìn trước**, và nó
không nói gì cả.

Đã thay bằng cách **bơm thẳng** một chuỗi dịch ngược 5 bar vào `toan_hang`. Nay
nó thật sự chứng minh được chốt chặn còn sống: chuỗi sạch đi qua, chuỗi dịch
ngược bị chặn.

## BẰNG CHỨNG
- `test_noi_sinh_hai_chieu.py`: **17 passed**, gồm hiệu chuẩn ngược thật.
- `test_nguong_chuyen_duoc.py` + `test_chan_hang_so.py` + `test_to_hop.py`:
  42 passed, 6 skipped, **1 đỏ** — `test_cache_KHONG_doi_ket_qua`, đã đối chiếu
  `reports/do_main.txt`: **đỏ sẵn trên `main`**.
- `test_cau_git.py` + `test_banker_diem_thoi_gian.py` +
  `test_hai_chieu_can_bang.py`: 66 passed.
