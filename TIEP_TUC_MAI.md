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

Phiên này trả lời câu chủ dự án giao hôm qua — *"mai ta sẽ thử cả sự kết hợp hệ
thống"* — và câu trả lời lớn hơn cái đã hỏi.

**Ghép đắt giá hơn đi tìm thêm một cơ chế mạnh.** Trên US100, ở cùng sụt giảm
15%, `mean_reversion_z5` một mình cho 6,14%/năm; ghép với
`quantora_ma_dashboard_sell` cho **20,25%/năm**. Đỉnh đường ghép **30,45%/năm @
DD 19,26%** so với z5 một mình 25,39% @ DD 38,00% — **lãi cao hơn ở đúng một nửa
sụt giảm**. Cấu hình tốt nhất luôn nằm ở **góc lưới**, tức không phải điểm tối ưu
chọn tay.

**Và lợi thế đó SỐNG ngoài mẫu — đây là kết quả quan trọng nhất.** Chấm bảng xếp
hạng trên nửa đầu, đọc ở nửa sau: hệ đơn đầu bảng rơi 822,7 → 40,7 (hụt 20 lần,
tức bảng hệ đơn gần như là nhiễu), nhưng **39/45 cặp đầu bảng vẫn hơn chính hệ
đơn đó ở holdout**, trung vị cao gấp 2-4,5 lần. *Chọn cơ chế nào phần lớn là may
rủi; chọn GHÉP thì không.*

**Nút thắt tăng cơ chế nằm trong kho, không ở seeker.** Miễn cổng `co_che` (nó
chặn vì thiếu một câu văn) thì 530 cơ chế ra tester trong **14 giây**. 129 cơ chế
âm ở cả train lẫn holdout; **đảo chiều thì 38 thành dương** — chân dương đi từ 46
lên 84 mà không cần một lượt seeker nào. Và 29% là con số trung thực: **91 cái lỗ
ở CẢ HAI chiều** — chữ ký của chi phí.

**Giới hạn phải nói ra, quan trọng hơn con số:** trên GER40 tương quan **âm
nhất** (−0,4429) mà ghép lại **tệ hơn**, vì chân thứ hai lỗ −443,64.
**Tương quan âm không đủ — chân thứ hai phải tự nó có kỳ vọng dương.**

Ba hướng chủ dự án mở thêm: **quản trị vị thế** (đo được: gần như vô hiệu trên
cặp này vì hai chân thoát quá nhanh — chỉ đặt huề 0,05×ATR kích hoạt, cho +3,8%
lãi miễn phí; *"trailing luôn tốt nhất" đúng với hệ GIỮ LỆNH, không đúng với hệ
thoát nhanh*), **đa khung** (bê chân D1 sang H1 thì âm 4.739 — phải chọn chân
trên chính khung đó; và M5 chỉ có **1,4 năm dữ liệu** nên loại vì DỮ LIỆU chứ
không phải vì cơ chế), **vốn↔lot** (100 USD trên tài khoản CHUẨN không chạy được
cấu hình nào — không phải "chạy nhỏ hơn" mà là không đạt lot tối thiểu; Micro
chia 100 mới chạy).

**Ba lần tôi tự sửa mình trong phiên, đều cùng một kiểu — tin một con số trước
khi kiểm nó sinh ra thế nào:** "US30 ghép không hơn hệ đơn" (sai vì mới có 40
ứng viên, mở lên 84 thì US30 mạnh nhất) · "Model=2 không đo được quản trị" (chỉ
đúng cho quản trị TRONG NẾN; cái tôi viết là theo nến đóng) · "336 pass giống hệt
nhau = quản trị không ăn thua" (thật ra lớp phủ bị cổng sau `InpKieuRa != 0`,
không bao giờ được gọi).

## KHONG DUOC QUEN
- **Khử trùng phải theo ĐƯỜNG VỐN**, không theo tên hay vân tay spec: 11-13% kho
  là hàng trùng ở cả ba mã (`z_score_reversion` == `mua_khi_gia_duoi_dai_duoi_bollinger`).
- **Script ở `lab/` phải có `__main__` guard**: một dòng `import` đã chạy lại cả
  lượt quét và ghi đè `PLACEBO_RONG.json` bốn mã bằng bản một mã.
- **2012-2015 H4 và D1 có số bar y hệt nhau** — MT5 dồn bar NGÀY vào khung nhỏ
  khi thiếu dữ liệu, không báo lỗi.
- **Phí qua đêm 1,56 bps/đêm ĐẮT HƠN spread 0,98 bps**; chân BÁN được **nhận**
  +0,18 bps/đêm.
- Tài khoản MT5 đang đăng nhập là **THẬT** (trade_mode=2), số dư 0, và là
  **CHUẨN** chứ không phải Micro.

## Việc tiếp theo

Xếp theo **giá trị trên mỗi giờ máy**. Báo cáo đầy đủ: `BAO_CAO_2026_09_07.md`.

1. **Ghép quản trị vào chân GIỮ LỆNH LÂU.** Đo được: trên z5+quantora quản trị
   gần như vô hiệu vì hai chân thoát quá nhanh (chỉ BE 0,05×ATR kích hoạt). Việc
   đúng không phải hạ ngưỡng nhỏ hơn nữa mà là **chọn chân có thời gian giữ dài**
   rồi mới phủ trailing/đặt huề. Kèm: truy vì sao lượt `trailing` (`InpKieuRa=2`)
   chạy 773 giây chưa xong — nghi `InpVaoLai=1` làm hệ vào lại mỗi nến.

2. **Quét chân trực tiếp trên H4 / H1 / M30** — `_khung_nho.py` đã viết, **chưa
   chạy**. H4 có chân đơn tốt nhất mạnh hơn D1 (735,1 vs 542,8) nhưng phải chọn
   chân TRÊN H4. Bỏ M5 (1,4 năm dữ liệu), M30 là khung nhỏ nhất còn đáng quét.

3. **Placebo cho 38 chân đảo chiều** — mới qua train+holdout. Chạy
   `_quet_placebo_rong.py` (201 độ dịch) rồi placebo đa tài sản trước khi coi bất
   cứ cái nào là phát hiện.

4. **Lệnh stop hai đầu** — `_stop_hai_dau.py` đã viết và biên dịch được, chưa
   chạy. Phải **tải M1 về trước** vì nó là quản trị TRONG NẾN nên bắt buộc
   Model=0/4.

### Vướng mắc còn lại
- **Tỉ lệ lot trong mọi bảng ra tiền là chọn TRONG MẪU.** Bài kiểm holdout chỉ
  kiểm việc chọn CHÂN, chưa kiểm tỉ lệ lot giữa các chân.
- **Trường `co_che` của quantora và 38 bản đảo là do máy điền** — cổng ra tiền
  đòi câu này do NGƯỜI viết.
- **Khử trùng theo đường vốn nên thành cổng thường trực**, không phải một bước
  rời trong `_bo_ba.py`.
- **`_da_khung.py` làm thiếu khâu hiệu chỉnh ngưỡng theo tỉ lệ kích hoạt** (xem
  CLAUDE.md mục "ĐỔI KHUNG = ĐỔI TÀI SẢN"). Giữ làm mốc, đừng coi là kết luận.

