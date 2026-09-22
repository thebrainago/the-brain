
---

## BỔ SUNG: hiến pháp của dự án bắt lại tôi

`test_hien_phap.py::KhongTestRong` — *"không hàm test nào tự báo PASSED mà không
kiểm gì"* — bắt đúng **hai bài tôi vừa viết**:

```python
with GAT.khoa(tep, cho_giay=2.0, nhip=0.05):
    pass          # vao duoc la dat
```

*"Vào được là đạt"* chỉ là một khẳng định **ngầm**. Đã nói ra thành lời, và thêm
một khẳng định nữa còn quan trọng hơn: **phải thu hồi NGAY**, không phải chờ hết
`cho_giay` rồi mới vào (bài cũ sẽ xanh cả trong trường hợp đó).

## VÀ MỘT BÀI ĐỎ SẴN ĐÃ SỬA LUÔN

`test_duoc_o_lai_chi_giu_the_CU_NHAT` dùng `1.the` với ghi chú *"pid 1 gần như
chắc chắn không sống"*. Trong **container** thì pid 1 là tiến trình init và nó
**có thật** — nên bài này đỏ trên mọi máy chạy bằng container, kể cả cloud của
chính dự án. Nó đỏ trên `origin/main`, và nó làm nhiễu mọi lần đối chiếu đường
cơ sở.

Nay sinh một tiến trình con rồi chờ nó chết hẳn: pid đó **chắc chắn** không còn
sống, và không phụ thuộc máy đang chạy ở đâu. Kèm một khẳng định rằng nó thật sự
đã chết — nếu không thì bài lại đang đo thứ khác.

`test_ghi_an_toan.py`: **13 passed, 1 skipped, 0 failed** (ổn định 3/3 lần).
