# TIEP TUC NGAY MAI — chot phien 2026-09-07 16:41

ghep he: chan am re hon chan manh; dao chieu tang doi chan duong; loi the ghep SONG o holdout (39/45 cap) trong khi bang he don la nhieu

## Trang thai do duoc luc chot
> May tu dien phan nay luc `b ket`. **Dung sua tay** — sua thi mai het so sanh
> duoc. Cot "doi" so voi moc 2026-09-06.

| chi so | hom nay | doi |
|---|---:|---:|
| file test (lab) | 88 |  |
| ham test (lab) | 1229 |  |
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
| file .py o goc lab | 238 | +10 |

- co DUNG_LAI: **CO (he dang nam im)**
- viec CHO theo loai: bac_cau_san=1, mt5_tick=1
- commit hom nay:
```
5c6e949 ghep he: chan am re hon chan manh - va dao chieu tang doi so chan duong
```
- file dang doi luc chot: **19**

## Một đoạn đọc là hiểu cả phiên

Phiên 07/09 đi từ "thử ghép hai hệ" đến tận nút thắt của cả hướng, và **kết quả
lớn nhất là một phát biểu đã qua kiểm ngoài mẫu**:

> Bảng xếp hạng **hệ đơn** gần như là nhiễu — hệ đầu bảng train rơi 822,7 → 40,7
> ở holdout, hụt 20 lần. Nhưng **lợi thế GHÉP thì sống**: 39/45 cặp đầu bảng
> train vẫn hơn chính hệ đơn đó ở holdout, trung vị cao gấp 2-4,5 lần.
> **Chọn cơ chế là may rủi; chọn ghép thì không.**

Ở cùng sụt giảm 15% trên US100: z5 một mình 6,14%/năm, ghép với quantora
**20,25%/năm**. Đỉnh đường ghép **30,45%/năm @ DD 19,26%** so với z5 một mình
25,39% @ DD 38,00% — lãi cao hơn ở đúng một nửa sụt giảm.

**Nút thắt đã truy đến tận cùng.** Lợi thế ghép đến từ chân **NGƯỢC CHIỀU**:
93-94% cặp ngược chiều có tương quan âm, cùng chiều chỉ 3-4% và **0% đạt
r < −0,2**. Tài sản khác chỉ cho ĐỘC LẬP (r≈0), cùng tài sản ngược chiều mới cho
TRIỆT TIÊU. Mà **trong 60 chân dương tốt nhất chỉ có 4 chân chiều BÁN**.

Ba hướng đã thử đều thất bại **vì cùng một lý do — không cái nào sinh thêm chân
bán**: H4 (5/15 cặp giữ hạng so với 39/45), khung nhỏ hơn (chân dương 84 → 61 →
29 → 16 theo đúng tỉ lệ chi phí), tài sản khác (trung vị holdout 71,5 so với
108,3 của cùng tài sản).

**Mở kho là đường rẻ nhất và đã đi.** Miễn cổng `co_che` → 530 cơ chế ra tester
trong 14 giây. 129 cơ chế âm cả hai đoạn, **đảo chiều 38 cái thành dương** — chân
dương 46 → 84 mà không cần seeker. Và 91 cái lỗ ở CẢ HAI chiều là chữ ký của chi
phí, không phải tiền chùa. Đảo chiều hiện là **cỗ máy duy nhất sinh chân bán**.

**Quản trị vị thế: sáu cơ chế, chỉ một sống.** Đặt huề +4,8% (sụt giảm không
đổi) · tỉa lệnh +0,17% · trailing **−68%** · giữ-đến-khi-chân-kia-vào −71% ·
nhồi lệnh đẹp trong mẫu nhưng **cháy tài khoản ngoài mẫu** (−9.999,70 / DD 100%).

**Bộ đổi khung đã xây xong** (`nhan/doi_khung.py`, ba bước: chu kỳ × tỉ lệ bar đo
được + khớp phân vị + hiệu chỉnh gộp). Tác dụng thật là **chống câm**: trên 26
chân có ngưỡng, số chân bị câm 7 → 1. Nó **không** biến cơ chế lỗ thành lãi.

**Năm lần tôi tự sửa mình trong phiên, đều cùng một kiểu** — tin một con số trước
khi kiểm nó sinh ra thế nào: "US30 ghép không hơn hệ đơn" · "Model=2 không đo
được quản trị" · "336 pass giống hệt = quản trị không ăn thua" · "nhồi lệnh +79%"
· "chéo tài sản là nguồn chưa khai thác".

## KHONG DUOC QUEN
- **Cột kết quả GIỐNG HỆT NHAU trên toàn bảng** = tham số không có tác dụng. Đây
  là dấu hiệu chung của 3 lỗi khác nhau trong phiên này. Kiểm đầu tiên.
- **Khử trùng theo ĐƯỜNG VỐN**, không theo tên: 11-13% kho là hàng trùng.
- **Script ở `lab/` phải có `__main__` guard** — một dòng `import` đã ghi đè mất
  báo cáo 4 mã bằng bản 1 mã.
- **2012-2015 H4 và D1 có số bar y hệt nhau** — MT5 dồn bar NGÀY vào khung nhỏ.
- **Phí qua đêm 1,56 bps/đêm ĐẮT HƠN spread 0,98**; chân BÁN được **nhận** +0,18.
- **`Model=0/4` không chạy được**: M1 trong máy chỉ có từ 2026-05-28.
- Tài khoản MT5 đang đăng nhập là **THẬT** (trade_mode=2), số dư 0, và là
  **CHUẨN** chứ không phải Micro.

## Việc tiếp theo

**Token tuần đã dùng 90%.** Chủ dự án chỉ đạo: từ sau phiên này **Qwen chạy
tiếp** — bàn giao đầy đủ ở `PROMPT_QWEN.md` (4 việc, 10 bẫy, chi phí thật, bảng
vốn↔lot, 5 câu tự kiểm trước khi báo kết quả).

Thứ tự việc, xếp theo giá trị trên mỗi giờ máy:

1. **SINH THÊM CHÂN BÁN CÓ LÃI** — nút thắt thật. (a) chạy `_dem_ghep.py` cho
   các mã chưa chạy (GER40, UK100, JP225, AUS200, FRA40, EU50, HK50, US2000) vì
   đảo chiều là cỗ máy duy nhất sinh chân bán; (b) đào 115 cơ chế `chieu=-1`
   trong kho, phần lớn chưa từng ra tester.
   **Cách kiểm đã xong: số chân dương chiều BÁN phải TĂNG.**
2. **Bật đặt huề vào các bảng ra tiền** — miễn phí, +4,8%. CẤM trailing, nhồi
   lệnh, hệ số lot > 1,0 (đã đo cả ba, đều hỏng).
3. **Placebo cho 38 chân đảo chiều** — mới qua train+holdout, chưa qua placebo.
   Đạt = p ≤ 0,05 trên ít nhất 2 mã.
4. **Lệnh stop hai đầu** — `_stop_hai_dau.py` đã viết và biên dịch được, phải
   tải M1 về trước.

### Đang chạy nền lúc chốt phiên
- `_thu_doi_khung.py US100Cash H1` — bản A xong (4/84 chân dương), bản B và C
  còn chạy. Kết quả sẽ rơi vào `reports/THU_DOI_KHUNG_US100Cash_H1.json` và
  cuối `reports/DEM_GHEP.log`. Đọc nó trước khi kết luận gì về bộ đổi khung ở
  H1 — bản D1→H4 đã xong và đó là bản đã dùng để viết mục 16 của báo cáo.

### Vướng mắc còn lại
- **Tỉ lệ lot trong mọi bảng ra tiền là chọn TRONG MẪU.** Bài kiểm holdout chỉ
  kiểm việc chọn CHÂN.
- **58/84 cơ chế không có hằng số ngưỡng** nên bộ đổi khung chỉ làm được bước 1.
- **Trường `co_che` của quantora và 38 bản đảo là do máy điền** — cổng ra tiền
  đòi câu này do NGƯỜI viết.
- **Khử trùng theo đường vốn nên thành cổng thường trực**, không phải một bước
  rời trong `_bo_ba.py`.
