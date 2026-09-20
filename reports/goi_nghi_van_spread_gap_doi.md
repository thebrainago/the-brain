# NGHI VẤN: `mo_phong_v2` có trừ spread **GẤP ĐÔI** không?

**Chưa kết luận.** Cloud không có `data/` nên không trả lời được. Đã viết phép
đo quyết định và xếp đơn `do-spread-hai-ban` (ưu tiên 2).

## CÂU HỎI

Cả hai bộ mô phỏng đều trừ phí theo **lượt khớp** (mở một lượt, đóng một lượt),
và `test_quan_tri_nhieu.py` chốt quy ước đó nguyên văn: *"hai chân, mỗi chân mở
+ đóng = **4 lượt khớp**"*. Đó là quy ước **có chủ đích**, không phải lỗi.

Nhưng hai bên lấy CON SỐ spread từ hai nguồn khác nhau:

| | nguồn | đơn vị | phí một vòng |
|---|---|---|---|
| `nhan/mo_phong.py` | `cp.spread_mang(idx)` — docstring ghi **"Spread MỘT CHIỀU"** | nửa spread | 2 × ½ = **1 spread** ✓ |
| `mo_phong_v2.py` | `m["spread"] / 10.0` từ bar M1 của MT5 | ? | 2 × ? |

Trường `spread` của MT5 là spread **đầy đủ** tính bằng point; chia 10 chỉ đổi
point → pip, **không chia đôi**. Nếu đúng vậy thì v2 trừ **hai** spread mỗi
vòng.

## VÌ SAO ĐIỀU NÀY QUAN TRỌNG

Hậu quả **không phải** một bảng số xấu đi một chút. Cổng `13_edge_vuot_spread`
đòi `lai_rong >= k * phi_spread`, nên gấp đôi `phi_spread` là **gấp đôi
ngưỡng**. Một hệ lưới thật sự ra tiền có thể bị loại vì một hệ số 2.

Đây là hướng **bảo thủ** (không tạo dương tính giả), nhưng LUẬT SỐ 0 nói mục
tiêu là TIỀN: **loại nhầm một hệ ra tiền cũng đắt y như nhận nhầm một hệ không**.

## VÌ SAO TÔI KHÔNG SỬA

Đổi cách tính chi phí là đổi **mọi con số lịch sử** hệ đã sinh ra. Làm việc đó
lúc 3 giờ sáng, không có dữ liệu để kiểm, dựa trên suy luận về nội dung một file
parquet tôi **không đọc được** — đó đúng là kiểu thay đổi không được phép làm
một mình.

## PHÉP ĐO QUYẾT ĐỊNH

```
ty_le = (sp_pip * PIP / gia_tb) / spread_frac_chung
```

- **~1,0** → hai bên cùng thang đo, câu hỏi đóng lại.
- **~2,0** → `mo_phong_v2` trừ gấp đôi. Phải sửa, và phải chạy lại mọi kết luận
  đã dựa trên nó.

Mã thoát: `0` = DAT · `1` = AM (đo được và lệch) · `2` = CHUA_DO_DUOC. Đã thêm
kiểu cổng `ba_muc` cho đúng ngữ nghĩa này — dùng `pytest` cho một script không
phải pytest thì đọc đơn dễ hiểu nhầm.
