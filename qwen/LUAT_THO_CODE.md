# LUẬT THỢ CODE — đọc trước mọi đơn hàng

Mọi đơn hàng giao cho mô hình rẻ đều chịu file này. Đơn hàng chỉ nói **việc
riêng**; ràng buộc chung nằm ở đây, không chép lại.

> Chốt 19/09/2026 sau ba đơn hàng đầu. Lý do tồn tại: cùng một nhóm lỗi lặp ở
> cả ba, và đọc diff để bắt chúng là việc lặp lại — việc lặp lại thì không nên
> trả tiền cho một mô hình mạnh.

## 1. Bài test là ĐẶC TẢ. Không được sửa.

Khó làm nó xanh thì **sửa code**, không nới test.

Đây là kiểu hỏng kinh điển của mọi vòng "sửa đến khi xanh": sửa test dễ hơn sửa
mã, và lúc đó bảng số vẫn xanh còn cái cổng thì biến mất. Chính trong phiên
19/09, một bài đỏ ở mức 50% và cách dễ nhất là hạ ngưỡng — nếu hạ thì phát hiện
lớn nhất phiên đó đã không bao giờ tồn tại.

## 2. Chỉ sửa file trong danh sách trắng

Đơn hàng ghi `duoc_sua`. File ngoài danh sách: không đụng, kể cả khi thấy nó sai.
Thấy sai thì **báo trong báo cáo cuối**, đừng tự sửa.

Không `git commit`, không `git push`, không sửa `config/*.json`.

## 3. Quy ước viết mã

- Tiếng Việt **KHÔNG DẤU**. Không chú thích tiếng Anh.
- Docstring nói **RÕ VÌ SAO**, không mô tả lại code. Có số đo được thì dẫn số.
- Bắt chước văn phong của các hàm xung quanh trong chính file đó.

## 4. Câu `co_che` là câu MÀN HÌNH DUYỆT ĐỌC

Nó phải nói **ai trả tiền cho phơi nhiễm này, và vì sao họ buộc phải trả**.

- Không liệt kê lại tham số.
- **Không chép luận điểm của khuôn khác sang.** Hai khuôn chung một luận điểm
  là hai phép thử trả tiền FDR hai lần cho một câu hỏi. Nếu chúng thật sự khác
  nhau thì phải nói được khác ở đâu.

## 5. Ba trạng thái, không phải hai

    DAT            phép đo vượt ngưỡng
    AM             phép đo chạy được và không vượt ngưỡng
    CHUA_DO_DUOC   khâu đo hỏng — chưa nói được gì

Hết quota, thiếu file ra, lệnh không chạy được → `CHUA_DO_DUOC`, **không bao
giờ** là `AM`.

## 6. Không được NHẬN BỪA

Khi viết bộ bóc/nhận dạng: một dấu hiệu chỉ tính khi nó **chỉ xuất hiện** ở
đúng thứ cần nhận.

Ví dụ thật (đơn hàng 2): `*_Point` là cách viết "N điểm" của MQL5 và có mặt
khắp nơi — lọc spread, khoảng cách TP, khoảng cách tối thiểu sàn đòi. Bắt mọi
`X > BIEN*_Point` là trailing thì một EA chỉ lọc spread bị đọc thành
`trailing_tu = 30`: bịa ra cơ chế không có trong EA.

Hỏi trước khi nhận: **dấu hiệu này còn xuất hiện ở đâu nữa?**

## 7. Lệnh chấm chuẩn

Mọi đơn hàng đều phải qua, không chỉ bài test riêng:

```
python3 -m pytest <file_test_cua_don_hang> -q
python3 -m pytest test_kiem_quy_uoc.py test_hien_phap.py -q
```

`test_kiem_quy_uoc.py` bắt máy móc bốn lớp lỗi ở mục 3–4: chú thích có dấu ·
hai khuôn chung câu `co_che` · câu quá ngắn hoặc chỉ liệt kê tham số · `ho`
khai lệch nhóm toán hạng.

Nó **không** kiểm được mục 6 (nhận bừa) và không kiểm được câu `co_che` có thật
sự nói được ai trả tiền. Hai thứ đó vẫn do người đọc — nhưng ít hơn hẳn khi bốn
thứ kia đã được máy lọc trước.

## 8. Báo cáo cuối

Dán **nguyên văn** output của cả hai lệnh chấm. Nói rõ đã sửa gì và **vì sao**.

Thấy gì sai ngoài phạm vi đơn hàng thì ghi vào cuối báo cáo — đừng tự sửa.
