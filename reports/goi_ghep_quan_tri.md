# GÓI: GHÉP QUẢN TRỊ LỆNH — lưới + NHIỀU cơ chế, như EA thật

## VÌ SAO ĐÂY LÀ HƯỚNG TẤN CÔNG ĐÚNG

`CLAUDE.md` đo được: *"hồ 2 QUẢN TRỊ VỊ THẾ … đo 05/09 nó **QUAN TRỌNG HƠN hồ
1** với lớp lưới: entry có tính SAI vẫn cho 92-97%/năm"*. Đây là module ra tiền
nhất của cả hệ.

## LỖ HỔNG

`duc_quan_tri` chỉ đẻ được cấu hình **MỘT KHUÔN**: một lưới + đúng một cơ chế
phụ. Một EA lưới thật ngoài đời chạy **bốn đến sáu** cơ chế cùng lúc — cắt hoa,
tỉa, chốt lùi, chặn vốn, hedge — và **chính sự kết hợp đó** mới là cái làm nó
sống qua một cú sụt. Đẻ từng cái một rồi kết luận *"quản trị lệnh không ăn thua"*
là kết luận về một thứ khác.

Mỗi khuôn phụ **đã gồm sẵn** lưới nền (`buoc`, `tp`), nên ghép hai khuôn phụ =
lưới + HAI cơ chế. Đó là hình dạng thật.

## MỘT LỖI TÔI TỰ BẮT NGAY TRONG GÓI NÀY

Bản đầu ghép cả `luoi_tran`. Nhưng `nut` của `luoi_tran` **đúng bằng** `NUT_NEN`
— nên `tran + X` không cho hai cơ chế, nó chỉ là `X` với `buoc`/`tp` khác: **một
biến thể tham số đội lốt một phép ghép**.

Hậu quả đo được: `tran` đứng đầu danh sách, nên **400 cặp đầu TOÀN LÀ `tran + X`**
và các cặp THẬT (phụ + phụ) bị hạn ngạch cắt sạch. Hàm ghép tiêu hết ngân sách
để sinh ra thứ nó không định sinh.

Sau khi chặn: 400 cặp, **6,5 núm trung bình**, phủ ≥8 cặp khuôn khác nhau —
`tia+chot_lui`, `chot_lui+cat_hoa`, `tia+hedge`, `chot_lui+trailing`…

## VÀ MỘT LỖI NỮA: ĐƠN HÀNG GỌI LỆNH KHÔNG TỒN TẠI

Tôi ra đơn `b hepha qt 300 --ghep` nhưng lại cài CLI thành một lệnh riêng
`qt-ghep`. Đơn sẽ **chạy nhầm đường mà không báo gì** — đúng kiểu lãng phí một
đêm máy chạy hết công suất để lấy về con số trả lời câu khác. Đã gộp `--ghep`
vào chính nhánh `qt`, và thêm **bài kiểm đối chiếu đơn THẬT trong `viec/cho/`
với bảng lệnh THẬT của `b.py`**.

## GIỚI HẠN CÓ CHỦ ĐÍCH: KHÔNG GHÉP BA

Số cặp là O(n²), số bộ ba là O(n³), và **mỗi cấu hình thêm là một suất FDR
thật**. Ghép ba chỉ đáng làm sau khi một cặp nào đó đã chứng minh được giá trị.

## BẰNG CHỨNG
`test_ghep_quan_tri.py`: **12 passed**, trong đó:
- mỗi bản ghép phải có ≥2 núm ngoài nền (**thật sự** hai cơ chế);
- đụng độ núm ngoài nền → **không ghép** (hai vế nói khác nhau về cùng một thứ);
- mọi núm phải là tham số **thật** của `mo_phong_v2.mo_phong` — một núm lạ không
  ném lúc đẻ, nó ném lúc CHẠY, sau khi đã tiêu một suất FDR để đăng ký;
- xác định: `han_ngach=20` phải là tiền tố của `han_ngach=100`;
- phủ ≥8 cặp khuôn — nếu 400 cặp đều từ 2-3 khuôn thì nó đang rải tham số quanh
  một góc chứ không phủ không gian.

Cụm HEPHAESTUS + cầu nối: **133 passed**.

## VIỆC CHƯA LÀM
Chưa chạy trên dữ liệu thật — đã xếp đơn `hepha-qt-ghep` (ưu tiên 6).
