# GÓI: BANKER — "giá trị CỦA ngày đó" ≠ "ngày đó ta BIẾT gì"

Việc kiểm **đầu tiên** tôi đặt ra cho trụ BANKER trong `NHIEM_VU_PHIEN_TOI.md`:
*"`banker.py` đang lưu ngày CÔNG BỐ hay ngày DỮ LIỆU? Nếu là ngày dữ liệu thì
mọi kết luận lịch sử của trụ này hỏng."*

**Kết quả: là ngày DỮ LIỆU. Lời khai point-in-time trong docstring là sai.**

## LỜI KHAI SAI

`tru/banker.py` dòng 4-6 viết:

> *"mỗi seri vĩ mô được LƯU VÀO SỔ theo thời gian, nên sau này trả lời được câu
> hỏi 'lúc đó ta biết gì' (point-in-time) chứ không phải lấy bản mới nhất áp
> ngược cho quá khứ."*

Mã nguồn ngay bên dưới nó: `vi_mo(seri, ngay, gia_tri, PRIMARY KEY(seri, ngay))`,
và `ngay` lấy **thẳng từ cột đầu CSV của FRED** — tức ngày của số liệu.

## BA HẬU QUẢ, CẢ BA IM LẶNG

1. **Nhìn trước theo độ trễ công bố.** CPI tháng 3 được FRED ghi `2026-03-01`
   nhưng giữa tháng 4 mới công bố. Câu hỏi *"ngày 2026-03-15 ta biết gì"* trả về
   số CPI tháng 3 — nhìn trước **hơn một tháng**.
2. **Không có chiều BẢN (vintage).** Một con số bị sửa lại không lưu ở đâu cả.
3. **`INSERT OR IGNORE` nuốt bản sửa.** Lần tải đầu tiên thắng — nhưng "lần đầu"
   là lúc nào thì không ghi ở đâu. Hai máy chạy cùng mã nguồn ở hai thời điểm
   khác nhau sẽ có hai `nao.db` khác nhau **mà không gì nói ra**.

## ĐÃ SỬA

- `DO_TRE_NGAY` — độ trễ công bố khai từng seri, **quy ước bảo thủ**: khi không
  chắc thì khai SỐ LỚN HƠN. Khai thừa một tuần chỉ mất một tuần dữ liệu; khai
  thiếu một tuần là nhìn trước một tuần, và nó không lộ ra ở bảng số nào.
- `gia_tri_biet_luc(seri, moc)` — đường **duy nhất** cho câu hỏi point-in-time.
  Ba trạng thái: `DAT` · `AM` (khai đủ nhưng chưa có số) · `CHUA_DO_DUOC` (seri
  chưa khai độ trễ).
- **Không có nhánh "mặc định 0 ngày".** Một mặc định như vậy sẽ lặng lẽ biến mọi
  seri mới thành nguồn nhìn trước, và cái giá không lộ ra ở đâu: bảng số vẫn
  đầy, p-value vẫn tính được, chỉ có kết luận là sai. Từ chối trả lời tốn một
  seri; đoán thì tốn cả kết luận.
- Bảng `vi_mo_ban(seri, ngay, ngay_biet, gia_tri, uoc_tinh, luc_tai)` trong
  `nhan/so.py` — giữ được nhiều bản của cùng một ngày. Cờ `uoc_tinh` phân biệt
  độ trễ **suy ra** với ngày công bố **thật** (ALFRED), vì nếu không một ước
  tính sẽ bị đọc như một sự kiện.
- Docstring đã sửa cho đúng sự thật.

## BIẾN LỜI KHAI THÀNH CON SỐ: `do_nhin_truoc()`

Một kết luận "đã sửa" mà không kèm con số thì không phân biệt được với "vẫn thế
nhưng nay có tên hàm mới". Hàm này so phép đọc cũ với phép đọc đúng:

| seri | thô thấy | đúng ra thấy | lệch |
|---|---|---|---|
| `CPIAUCSL` @ 2026-03-15 | 2026-03-01 | 2026-01-01 | **73 ngày**, lệch giá trị 2.0 |
| `VN_GDP` @ 2026-06-01 | 2025-12-31 | 2024-12-31 | **365 ngày** |
| `SP500` @ 2026-03-13 | 2026-03-13 | 2026-03-13 | **0** |

Dòng cuối là **hiệu chuẩn chiều ngược**: nếu hàm đo báo MỌI seri đều nhìn trước
thì nó đang đo thứ khác. Giá thị trường biết ngay trong ngày, và phép đo phải
nói đúng điều đó.

## BẰNG CHỨNG
- `test_banker_diem_thoi_gian.py`: **13 passed**, dùng `nao.db` tạm (không đụng
  sổ cái thật).
- `test_banker_fred.py` 2 bài đỏ — **đã đối chiếu `git stash`: đỏ sẵn**, do
  cloud không có dữ liệu trong `nao.db`.

## MỘT BÀI KIỂM CỦA CHÍNH TÔI SAI

`test_World_Bank_nhin_truoc_HANG_NAM` ban đầu đặt `moc = 2026-01-15` và đợi thấy
số của 2024. Sai: ở mốc đó `2024-12-31 + 400 ngày = 2026-02-04`, tức **chưa biết
cả hai** → đúng ra là `AM`. Bài kiểm sai, không phải mã nguồn. Đã sửa bài và giữ
lại cả hai mốc — chính nó cho thấy độ trễ này lớn đến mức nào.

## RỦI RO CÒN LẠI / VIỆC CHƯA LÀM

- **Độ trễ hiện là ƯỚC TÍNH, không phải ngày công bố thật.** Nguồn duy nhất cho
  ngày thật là **ALFRED** (FRED vintage). Chưa nối — và **không nối được từ
  cloud**: proxy trả `403 CONNECT` cho `fred.stlouisfed.org`,
  `alfred.stlouisfed.org`, `publicreporting.cftc.gov` (chính sách mạng, không
  phải lỗi tạm). Phải làm trên máy chủ dự án.
- `_luu_seri` **chưa** ghi vào `vi_mo_ban` — bảng đã có, đường ghi chưa nối.
  Chưa nối được vì không tải được dữ liệu thật từ cloud để kiểm.
- Chưa có phép so "hệ CÓ BANKER vs KHÔNG BANKER ở cùng ngân sách FDR" — đó mới
  là phép đo quyết định trụ này là edge hay là chi phí.
