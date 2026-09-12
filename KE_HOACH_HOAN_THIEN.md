# KẾ HOẠCH HOÀN THIỆN THE BRAIN

> **Nguồn duy nhất của cấu trúc: `Desktop/hethong.txt` (chủ dự án, 11/09/2026).**
> Bản trước của tài liệu này dựng theo `KE_HOACH_XAY.md` và sổ `van_de` của lab —
> **sai cấu trúc**, đã chuyển vào `nhat_ky/KE_HOACH_HOAN_THIEN_SAI_CAU_TRUC_12_09.md`.
> Lab đã mọc thêm BANKER và NGHI, hai thứ **không có trong sơ đồ**, và tôi đã
> xếp chúng vào việc phải làm.

---

## 0. Hai điều chỉnh về TINH THẦN — đọc trước khi đọc việc

**(a) Mục tiêu là TIỀN, không phải chặt chẽ học thuật.** Chủ dự án viết:

> *"mục tiêu là lợi nhuận còn lại không phải những mô hình kinh tế hay quản trị
> quỹ để mà cần đề cao quá nhiều tiêu chí học thuật hay các chỉ tiêu chặt chẽ.
> Mục đích cuối cùng là có tiền chấp nhận cả chi phí và rủi ro cao"*

Phiên 12/09 tôi làm ngược: lấy **MDE / FDR / placebo làm tường chặn** rồi lần
lượt tuyên bố trailing, ghép, z5, quantora là ÂM. Những phép đo đó **không sai**,
nhưng dùng làm **cổng chặn** thì sai vai. Vai đúng là **nhãn cảnh báo** — *"cái
này mỏng, vào tiền thì size nhỏ"* — chứ không phải *"cấm cửa"*.

Hệ quả cụ thể: một cơ chế dưới MDE **vẫn được đi tiếp**, kèm nhãn. Chỉ chặn khi
nó **thua mua-giữ ở cùng rủi ro** — đó mới là câu hỏi tiền.

**(b) QUẢN LÍ LỆNH quan trọng hơn ENTRY.** Chủ dự án viết:

> *"việc sử dụng kỹ thuật quản lí lệnh tốt còn hơn việc có 1 entry tốt"*
> *"Riêng mục này cần chú ý vì nó là module quan trọng trong toàn bộ hệ thống"*

Sáng 12/09 tôi chạy placebo trên họ trailing rồi đóng lại là ÂM. Theo (a), đó là
**một nhãn**, không phải bản án. Mở lại hướng này.

**(c) Nền tảng là FX.** Cả phiên 12/09 tôi ở chỉ số Mỹ.

---

## 1. Sơ đồ đúng — BA module

### THE SEEKER

| mục trong sơ đồ | trạng thái |
|---|---|
| A. phễu fetch đa nguồn | **CÓ** `tru/seeker.py` · 73 nguồn BẬT · 10.479 tài liệu |
| trình duyệt riêng + Gmail/social | **CÓ** `nhan/cau_browser.py` · 25 nguồn trình duyệt |
| né chặn bot | **CÓ** (WARP · CDP · mô phỏng người dùng) |
| quét thông minh: soi lại trang 1 rồi đi sâu | **CÓ** con trỏ biên giới · 75 trang / 4 vòng |
| xếp hạng ưu tiên nguồn có file dùng được | **CÓ** `uu_tien` trong bảng `nguon` |
| tự follow kênh / nhóm / cá nhân | **CÓ** telegram · 9 kênh theo dõi |
| tự sinh từ khoá mới | **CÓ** bảng `tu_khoa` |
| tìm kiếm ĐA NGÔN NGỮ | **CÓ** habr_nga · qiita_nhat · velog_han · cnblogs_trung |
| nguồn có LỊCH SỬ GIAO DỊCH | **CÓ** mql5_signals · myfxbook · darwinex · collective2 · zulutrade |
| B. bộ lọc — mq5/c++ dùng luôn | **CÓ** `nhan/doc_ma.py` · 570 mã nguồn trong kho |
| văn bản → cơ chế | **CÓ** `nhan/doc_hieu.py` |
| VIDEO → cơ chế | **CÓ** `nhan/doc_video.py` |
| ẢNH → cơ chế | **CÓ** `nhan/doc_anh.py` · OCR kiểm 12/09, trùng khớp từ 78,8% |
| xếp hàng theo chất lượng đầu vào | **CÓ** `candidate_queue` + `uu_tien` |
| suy ngược từ lịch sử giao dịch | **CÓ** `nhan/tin_hieu_mql5.py` |

**SEEKER đủ 14/14.** Việc còn lại là VẬN HÀNH (4 nguồn thu hoạch = 0), không phải xây.

### THE QUANTLAB

#### Tổng quan tài sản — CHỖ THIẾU THẬT SỰ

`nhan/ho_so_symbol.py` đã đo **159 mã**: hurst · VR(2)/VR(10) · ac1 · nửa đời ·
efficiency ratio · nhãn tính cách · biến động năm · ATR% · biên độ bar · spread ·
**phí qua đêm hai chiều** · độ tin chi phí.

| chủ dự án yêu cầu | trạng thái |
|---|---|
| biên độ · chi phí · phí qua đêm | **CÓ** |
| tính hồi quy / trend | **CÓ** (hurst → `nhan_tinh_cach`) |
| trượt giá | **một phần** — `chi_phi.truot_gia_frac`, chưa vào hồ sơ |
| **tính mùa vụ** (không / có / có thì cụ thể thế nào) | **THIẾU** |
| **tương quan** (âm / dương với mã khác) | **THIẾU** |
| **sóng zigzag**: biên độ đẩy · tần suất đẩy · tần suất hồi · biên độ hồi | **THIẾU** |
| **mốc magnetic** | **THIẾU** |
| **entry-time trong năm** (thời điểm xác suất cao) | **THIẾU** |
| các dạng nến | có template, chưa thành ĐẶC TÍNH tài sản |
| hình học / gann | có `gann_activator`, `gann_sq9` |

→ **Việc xây thật đầu tiên.**

#### Cơ chế QUẢN LÍ — module quan trọng nhất theo sơ đồ

| chủ dự án liệt kê | trạng thái |
|---|---|
| ATR | có (toán hạng) |
| trailing stop | **có, đã đo** — 5/42 hơn cả hai nửa · placebo p 0,596 |
| hedging | có trong DSL lưới |
| **buy/sell stop hai đầu** | **THIẾU** |
| **market + stop hedge đối diện** | **THIẾU** |
| DCA · DCA tính vốn | có (lưới AUDCAD / Bigmouse) |
| đánh nhanh chốt nhanh | có |
| chạy ĐỘC LẬP hoặc ĐẮP lên hệ khác | **CÓ** `_thu_quan_tri.py` |

Kho quản trị: **42 luật đã thử**, 18 trong `quan_tri_vi_the.json`.
Kho cơ chế 1.420 thì **0 cái có trường quản trị** — hai họ vẫn tách rời.

#### Chiến lược

| yêu cầu | trạng thái |
|---|---|
| test thô python → test phần mềm giao dịch | **CÓ** (`chay_tester_kho` + khoá tester) |
| backtest file có sẵn trước | **CÓ** |
| kiểm chỉ báo mũi tên / có entry | **CÓ** |
| dựng file chiến lược từ cơ chế | **CÓ** (bộ dịch DSL → MQL5) |
| truy ngược lịch sử giao dịch | **CÓ** |
| **đa cặp × đa khung × đa quản lí × đa thông số** | **một phần** |
| **kết hợp đa chỉ báo đa hệ thống** | **một phần** (`_ghep_he`) |
| bộ tổng kết: bài học + hướng nên tránh | **CÓ** 238 bài học |
| AI giám sát tư duy | **CÓ** EVO |

#### Nội sinh · Luồng ưu tiên

`nhan/noi_sinh.py` **CÓ**. Luồng ưu tiên khi chủ dự án gửi bài — **THIẾU cửa vào rõ ràng**.

### THE EVO

| mục | trạng thái |
|---|---|
| giám sát hiệu suất từng module | **CÓ** `tru/evolution.py` |
| cắt nghĩa vấn đề + đề xuất | **CÓ** — 82 vấn đề · 39 đề xuất |
| THE FINDER tìm công cụ / skill | **CÓ** `tru/finder.py` — 3 công cụ ≥70 điểm đang chờ |

### Ba nguyên tắc vận hành

| | trạng thái |
|---|---|
| 1. bypass — duyệt sẵn mọi đề xuất | đang theo |
| 2. terminal thúc agent chạy tiếp (THE THORN) | **CÓ** `dieu_khien_xa.py` + `q` |
| 3. chạy SONG SONG các trụ không liên quan | **CÓ** `q` 5 làn · nhưng `dieu_phoi` tắt từ 01/09 |

### Ngoài sơ đồ

`tru/banker.py` (vĩ mô FRED) và `tru/nghi.py` — **không có trong sơ đồ**. Không
xoá, nhưng **không tính là việc phải hoàn thiện**.

---

## 2. Việc còn lại — theo sơ đồ, không theo sổ `van_de`

```
[x] Q1  ho_so_song.py — sóng zigzag + mốc magnetic · 159 mã/4s · đã quét cả H4
[x] Q2  ho_so_mua_vu.py — mùa vụ + entry-time · T2 tốt nhất 31/50, T6 tệ nhất 28/50
[x] Q3  ho_so_tuong_quan.py — có ĐỘ ỔN ĐỊNH, lọc TRÙNG CÔNG CỤ + NGHỊCH ĐẢO CƠ HỌC
        (19/20 cặp âm đầu là giả; còn EURAUD|NZDCHF −0,637 ổn định 0,93)
[x] Q4  vao_lenh.py — 7 cấu trúc, máy nhiều chân, tự tính tiền open-to-open
        + test_vao_lenh.py 18/18. Kết quả: KHÔNG cấu trúc nào thắng lệnh thị trường
[x] Q5  cong.py chế độ "nhan" (mặc định) — alpha/placebo/đăng-ký-trước/FDR/siết
        phơi nhiễm chỉ DÁN NHÃN; chặn cứng còn: thắng mốc · phí đo được · đủ lệnh ·
        không ăn khe giá. `verdict_chan` vẫn ghi song song để đối chiếu
[x] Q6  to_hop.py — phễu 3 chặng (39 triệu ô → chạy được), tỉa bằng Q3, có
        BỘ TỔNG KẾT nên-đi/nên-tránh + cảnh báo thiên lệch chọn lọc
[x] Q7  uu_tien.py ĐÃ CÓ TỪ 11/09 — nối thêm `phan_tich_ngay()` (xếp hàng ưu tiên 0
        + backtest ngay), nhận văn bản dán thẳng, và ĐỌC ĐƯỢC TIẾNG VIỆT CÓ DẤU
[x] S1  ĐÃ CHẨN ĐOÁN 12/09 — 5 nguồn rỗng là **4 ca khác nhau**, không phải một:
        quantconnect  CHẶN_JS    HTTP 200 nhưng là trang Cloudflare/'cần JavaScript'
        fxblue·etoro  BỘ_BÓC_SAI trang về được (526KB/181KB, sạch) → lỗi selector
        reddit_quant  ĐÃ_SỐNG_LẠI feed chạy bình thường; 6 lỗi trong sổ là đợt cũ
        mql5_ma_nguon CHẶN_MẠNG  ConnectionError; nguồn đang TẮT nên không "rỗng"
        Đã ghi chẩn đoán vào `nguon.ghi_chu`, xoá bộ đếm lỗi cũ của reddit.
[x] E1  CHỦ DỰ ÁN QUYẾT 12/09: hệ sẽ lên **VPS chạy 24/7 nhiều tháng**.
        => `dieu_phoi` GIỮ, không bỏ. Nhưng XONG HỆ THỐNG TRƯỚC rồi mới chuyển.
[x] E2  CHỦ DỰ ÁN DUYỆT HẾT 12/09: 4 công cụ ≥70đ (streaming_indicators 90,
        howtrader 84,7, pdf-to-markdown 79,8, mdpdf 70,3) → trạng thái DA_DUYET
```

**Q5 trước Q6**, vì chạy tổ hợp qua một cái cổng đặt sai vai thì lại loại sạch
như phiên 12/09.

**Q1–Q4 là xây thật.** Phần còn lại phần lớn là nối dây và vận hành.

---

## 3. Đo tiến độ

Không đo bằng số phép thử. Đo bằng **số dòng trong sơ đồ đã CÓ**:

```
SEEKER      14/14   đủ
QUANTLAB    17/24   thiếu 7
EVO          3/3    đủ
vận hành     2/3    dieu_phoi tắt
──────────────────────────────
            36/44 = 82%
```

Dán con số này vào mọi báo cáo.


---

## 12/09/2026 — HÀNG ĐỢI VIỆC XÂY

`day_viec.py`: chạy TUẦN TỰ và LIÊN TỤC, bền qua sự cố, lỗi không chặn hàng.
    python day_viec.py           chạy tiếp đến khi hết
    python day_viec.py --xem     bảng trạng thái
Thêm việc được ngay cả khi hàng đợi đang chạy (nó nạp lại sổ sau mỗi việc).

## BỐN LỖI ĐO ĐƯỢC TRONG NGÀY

1. `dap_quan_tri.dap()` TRỄ MỘT BAR: tính SL/TP từ `open[i+1]` rồi trả vị thế cho
   `mo_phong.chay` — mà hàm đó tự dịch thêm một bar nữa. Hệ ăn lợi suất bar i+2.
   Đã nối sang bộ tính tiền open-to-open. Mọi số quản trị trước 12/09 phải đo lại.
2. `giu_toi_da=N` trong `vao_lenh` giữ N+1 bar, lệch với `dap_quan_tri`.
3. HEDGE ĐƯỢC MIỄN PHÍ: `mo_phong.chay` thu phí theo `|diff(vị_thế_ròng)|`, nên
   hai chân ngược chiều trả 0 đồng spread. Đã thêm `phi_them`.
4. Vế THOÁT sau DẤU PHẨY bị nuốt vào vế VÀO → spec `rsi<30 VÀ rsi>55`, không bao
   giờ kích hoạt. Đã sửa; audit kho 1.460 cơ chế: 0 cái dính (chưa gây hại).

## ĐO ĐƯỢC: KHO BÀI BÁO HẦU NHƯ KHÔNG CHỨA LUẬT

200 tài liệu ngẫu nhiên → 2 cơ chế. Bóc tách theo chặng trên 120 bài:
24.244 câu → 441 câu (1,82%) có động từ mua/bán → 38 qua `loai_cau` → 4 ra điều
kiện. Các câu bị loại KIỂM TRA LẠI LÀ LOẠI ĐÚNG (văn kể chuyện, tiêu đề Reddit,
bài toán học). Tức nút thắt KHÔNG phải bộ lọc — là nguồn. Khớp với quy tắc đã có:
ưu tiên nguồn CÓ FILE (.mq5/.ex5/.set) chạy tester được ngay.


## 12/09/2026 (tiep) — LOI DU LIEU NEN, TIM RA TU MOT CON SO VO LY

Bang xep hang quan tri co dong `GBPZAR 591%/nam, maxDD -99,38%`. Truy nguoc:

- Doan 09/2023-01/2024 cua GBPZAR co **ca cot `high` bi nhan 10** (233,29 trong
  khi close 23,30), rai rac ca `open`. Duong von mua-giu vot len 9,19 lan.
- Sau khi sua: maxDD **-91,67% -> -38,93%**, Sharpe **0,763 -> -0,071**.
- Quet toan kho: **16/159 ma can sua** - 419 gia tri lech thang x10, 3.601 lan
  `open`/`close` nam ngoai `[low, high]` (toan nguon Yahoo). Cac phep kep KHONG
  phai lam tron: YH_DAUTUONG lech trung vi 0,71%, toi da **9%**.
- **Bay "rau nen hong" trong `du_lieu.kiem()` da dem duoc 154 bar hong cua chinh
  GBPZAR tu truoc. Khong co gi doc no.**

Da sua: `du_lieu.sua_bar_hong()`, `nap()` goi theo MAC DINH, `sua_bar=False` de
do chinh do hong. `test_sua_bar_hong.py` 9/9.

**Moi ket qua chay truoc 12/09/2026 tren 16 ma do deu phai chay lai.**

## TRANG THAI BO KIEM

Moi module QUANTLAB moi gio deu co nguoi kiem (`test_hien_phap` xanh):
    test_vao_lenh.py         18   cau truc vao lenh + bo tinh tien
    test_dap_quan_tri.py     14   tre mot bar, tie-break, moi nut co tac dung
    test_ho_so_quantlab.py   17   song · mua vu · tuong quan · quy luat song
    test_to_hop.py           11   phep tia, phep gop, canh bao thien lech
    test_sua_bar_hong.py      9   bar x10, open ngoai bien, chuoi sach khong dong
    test_doc_hieu_viet.py    11   tieng Viet co dau, ve thoat sau dau phay


## 12/09/2026 (tiep 2) — Q6 TU TO CAO NO, VA CHANG 4 RA DOI

Lan chay Q6 day du dau tien (145 ma x D1+H4 x 868 co che = 139.748 o chang 1,
16 phut) cho mot bang xep hang dep. Doc ky cot TAI SAN thi thay 200 o song sot
**gan nhu chi nam tren TRYJPY, GBPTRY, USDARS** - ba dong tien sup do. Do khong
phai co che tim ra edge, do la co che bat duoc mot xu huong mot chieu DA xay ra.

=> Them **CHANG 4 - HOLDOUT**: chon tren 60% dau, DO tren 40% sau.

### Hai loi tu tim ra khi dung chang 4

1. **Moc con dung cong thuc cu.** Toi doi cach quy cua HE sang chay lai o don
   bay that (`quy_ve_dd`) nhung de MOC o phep nhan tuyen tinh. Hai ben khac don
   vi va he duoc loi. Da gop ve mot ham `vao_lenh.moc_dd20`.
2. **Tieu chi qua holdout qua long.** Ban dau 29/35 he "thang moc" - khong tin
   duoc. Doc bang thi ro: `moc_hold = 0,00` (mua-giu VA ban-giu deu am nen moc
   tut ve tien mat, "thang moc" chi con nghia "duong"), va `train 1,67 -> hold
   48,86` (gap 30 lan = gap may che do, khong phai ben).
   Siet thanh: **hai nua deu thang moc CUA CHINH NO, va ti le hold/train trong
   [0,33 · 3,0]**. Con 19/35 tren mau thu 12 ma.
3. Bo tong ket TU SUY LAI tieu chi nen van in con so cu. Da danh dau
   `qua_holdout` ngay tren dong - mot cho dinh nghia duy nhat.

### Mau bat dau hien ra

Tren cac cap cheo (phi qua dem dat), `chot_nhanh_sl1_tp1` va cau truc `nhanh`
chiem gan het bang song sot. Khop voi cai da thay o GBPZAR: **vao nhanh ra nhanh
ne duoc phi qua dem**, va tren cap cheo thi phi qua dem chu khong phai spread la
thu quyet dinh.


## 12/09/2026 (tiep 3) — HIEU CHUAN HAI CHIEU LAT NGUOC KET LUAN

Q6 chay day du (chang 4 phu het chang 2): **2.841 he qua holdout, 0 thang moc**.

Truoc khi bao con so do, toi lam dieu ma memory `cong-pass-phai-hieu-chuan-hai-chieu`
bat buoc: **chung minh bo do bat duoc cai co that**. Cay mot edge 0,6 sigma song
dung 1 bar vao chuoi tong hop (`test_hieu_chuan_to_hop.py`).

Ket qua: **pheu TRUOT chieu duong**. Va truy ra hai loi cong lai:

1. **Chan troi giu lenh sai 12 lan.** 885/1460 co che (60,6%) khai `giu = 1`,
   978/1460 (67%) khai `giu <= 5`. Pheu chay TAT CA voi `giu_toi_da = 60`.
   Do duoc tren chuoi cay: edge giu 1 bar thi bat duoc va song qua holdout;
   giu 20 bar thi he **LO** (dd20 -2,53) du edge co dieu kien nguyen ven.
2. **Chan dong do het cua so khong duoc ghi vao so lenh.** Voi `giu_toi_da = 1`
   thi `so_lenh = 0`, va bo loc `so_lenh < 15` **loai sach moi co che `giu = 1`**.

Hai loi cong lai: hai phan ba khong gian bien mat khoi moi bang xep hang ma
khong bao gi. **Con so 0/2.841 khong noi gi ve thi truong.** Da sua ca hai va
chay lai.

Bai hoc phu: mot edge cay bang cach CONG DRIFT khong phan biet duoc voi mot XU
HUONG - lan dau toi cay xong thi moc mua-giu len 139%/nam va an tron cai edge.
Chuoi hieu chuan phai TRUNG TINH: ky vong khong dieu kien = 0.

## SUY NGUOC: hai dau hieu dong thuan da tai san (154 ma, D1)

Phep thu dung o day khong phai p tung ma (luc yeu - tot nhat chi 54/154 dat) ma
la **phep thu nhi thuc tren DAU**:

    truoc CU TANG  va  CU GIAM : bien dong dang NO RA (bd20/bd60 cao hon)
                                 126/154 va 118/154 ma cung dau
    truoc CU TANG            : gia THAP hon trung binh 20, do doc am, dang co
                                 chuoi bar giam  (110-117/154 ma)

Uoc ~79 ma doc lap nen p la chan duoi lac quan. Do lech chi 0,03-0,14 do lech
chuan: **mot xu huong co that, khong phai mot tin hieu giao dich duoc ngay.**


## 12/09/2026 — HAI QUYET DINH CUA CHU DU AN

**E1. He se len VPS chay 24/7 nhieu thang.** Nhung *"can xong he thong cho chuan
da"*. Hai he qua:
  * `dieu_phoi.py` GIU LAI, khong bo. No la control plane 24/7 - dung cai se can.
  * Nhung viec cua HOM NAY van la XONG HE THONG, khong phai chuyen VPS.

  Va mot he qua thu ba it ai de y: chay nhieu thang **khong co nguoi ngoi canh**
  thi EVO khong duoc phep chi la mot bao cao nam trong `reports/`. No phai TU
  NOI RA khi co van de. Cau Telegram da co (`b xa`) - con thieu duong noi
  EVO -> Telegram. Da them vao muc con lai.

**E2. Duyet het 4 cong cu >= 70 diem.** Da danh dau `DA_DUYET` trong
`reports/cong_cu.json`. Thu tu tich hop theo gia tri that:
  1. `streaming_indicators` (90) - lop `toan_tu_co_nho` ngu phap dang thieu, va
     chi bao co trang thai chay nhanh hon han khi quet 140.000 o.
  2. `pdf-to-markdown` (79,8) - duong doc PDF thu hai, doi chieu voi pymupdf.
  3. `mdpdf` (70,3) - Markdown -> PDF, dung de XUAT bao cao cho chu du an.
  4. `howtrader` (84,7) - hoc y tuong kien truc, KHONG thay engine hien co
     (hai engine ra hai so thi khong ai phan xu duoc).


## 12/09/2026 (tiep 4) — BA MUC NUA

**EVO -> Telegram.** He qua cua quyet dinh VPS 24/7: bo giam sat chi ghi vao
`reports/` thi trong nhieu thang bang khong co. `nhan/evo.bao_xa()` gui ra
Telegram, va **chi gui khi TAP VAN DE DOI** - gui cung mot dong moi gio suot ba
thang la 2.160 tin giong het nhau, den tin thu ba nguoi ta tat thong bao, tuc bo
giam sat tu lam minh vo hinh. Khi van de HET cung bao. `b evo --xa`.
Con thieu MOT buoc cua nguoi: `chat_id` = 0, cau Telegram chi bat duoc chat_id
sau khi chu du an nhan cho bot mot lan (`b xa` roi nhan gi do).

**Truy nguoc lich su giao dich: DA CO SAN, nut that la BANG ANH XA.**
`nhan/mimic_cau_noi.py` noi `ds/mimic` (cay quyet dinh nong tu so lenh -> luat
dang `"rsi_14 <= 30"`). Do 12/09: bang anh xa phu **5/7** dac trung, hai cai con
lai de `None` nen moi luat cham toi chung bi bo IM LANG. Da noi het 7/7:
  * them toan hang DSL `lech_tb` = (x - tb_n)/tb_n
  * `price_position` -> `stochastic(20)` **voi he so 100** (mimic dung [0,1],
    DSL dung [0,100]; quen he so thi `<= 0,2` thanh luat chet)
  * bay o ben mimic: dac trung ten `dist_ma200_atr` nhung CHIA CHO ma200 chu
    khong phai ATR -> `<= 0,02` la 2%, khong phai 0,02 ATR
