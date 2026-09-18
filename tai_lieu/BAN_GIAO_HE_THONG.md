# BÀN GIAO THE BRAIN — trạng thái hệ thống, 13/09/2026

Đọc file này **cùng với `Desktop/hethong.txt`**. `hethong.txt` là LUẬT SỐ 0 —
nguồn duy nhất của *cấu trúc*. File này là *trạng thái*: cái gì đang chạy, cái
gì hỏng, cái gì đã đo rồi đừng đo lại.

Bản đồng bộ của sơ đồ nằm ở `lab/SO_DO_HE_THONG.txt`. Luật vận hành hằng ngày ở
`lab/CLAUDE.md` và `AGENTS.md`. Kho memory của Claude ở
`~/.claude/projects/C--Users-SV-STORE/memory/` (~200 mục, index trong `MEMORY.md`).

---

## 0. ĐIỀU QUAN TRỌNG NHẤT: HỌ LỖI CỦA HỆ THỐNG NÀY

Đây là thứ cần tư duy hệ thống, không phải thứ cần thêm code. Hệ đã đủ đồ sộ để
**mọi lỗi lớn đều cùng một hình dạng**, và hình dạng đó là:

> **Bộ phận có tồn tại, luật có được viết ra, nhưng nó không nằm trên đường chạy.**
> Và khi nó không nằm trên đường chạy, hệ vẫn báo một con số bình thường.

Bốn lần độc lập trong một ngày, bốn nguyên nhân khác hẳn nhau, cùng hình dạng đó:

| # | Luật/bộ phận đã có | Không nằm ở đâu | Hậu quả đo được |
|---|---|---|---|
| 1 | *"`cp.do_tin` là KHAI thì không bao giờ PASS"* (`lab/CLAUDE.md`) | `to_hop` chưa đọc `do_tin` lần nào | 8/8 mã dẫn đầu phễu đều KHAI; **một nửa công suất máy đổ vào ô không thể PASS** |
| 2 | Chặng 4 (holdout) — phép thử duy nhất có nghĩa | Kết quả nằm trong JSON, `b he` không đọc | Phễu chạy 110 phút, **không gì tích luỹ lại** |
| 3 | Luật *"hiệu chuẩn hai chiều"* | `mach.c_pheu_ung_vien` chỉ đếm một chiều | Đèn đỏ chỉ sang việc SAI suốt nhiều phiên |
| 4 | `--khung` trong CLI của `to_hop` | Rơi xuống nhánh `else` | Chạy được **do may**; `TO_HOP.json` ghi `"khung": ["--khung","D1"]` |

**Việc của phiên sau không phải là thêm module.** Là đi tìm tiếp những chỗ cùng
hình dạng này. `b ban-do` sinh bản đồ TỪ MÃ NGUỒN và trả lời đúng câu hỏi đó:
*module nào không nằm trên đường chạy nào*. Lần đo 12/09: **31 mồ côi thật**,
trong đó có cả `nhan/han_muc.py` — kill-switch của hệ.

Luật gốc: **"Một luật chỉ sống nếu nó nằm ở chỗ HẸP NHẤT"** và
**"Công cụ không nằm trên đường chạy thì bằng không có"** (luật L7).

---

## 1. HỆ THỐNG LÀ GÌ, CHẠY BẰNG LỆNH NÀO

Ba trụ theo sơ đồ: **SEEKER** (phễu + bộ lọc) · **QUANTLAB** (tổng quan tài sản ·
**cơ chế quản lí lệnh** · chiến lược · nội sinh · luồng ưu tiên) · **EVO** (+FINDER).

```
cd "Downloads/Research SP500/lab"
b vao            trạng thái sống + bàn giao hôm qua (~2 giây)
b ban-do         SINH bản đồ từ mã nguồn — CHẠY TRƯỚC KHI XÂY GÌ MỚI
b mach           mạch đập 10 chặng đường ống + mutation audit
b he             BẢNG SẢN PHẨM: hệ đã qua cổng + hệ qua holdout của phễu
b ngan-sach      sổ tài nguyên (TESTER=1 là ràng buộc VẬT LÝ)
b day-chuyen     SEEKER: săn -> đọc song song -> bóc cơ chế
b test-me        chạy test theo mẻ (tránh ENOMEM do process mồ côi)
python -m nhan.to_hop --khung D1 [--ma N] [--co-che N] [--tien-trinh N]
python -m nhan.vong_day_du        MỘT lệnh chạy cả 8 chặng ba trụ
```

Python **duy nhất** dùng được:
`C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe`
(`b.cmd` đã trỏ đúng). Đừng dùng `WindowsApps\python.exe`.

---

## 2. TRẠNG THÁI ĐO ĐƯỢC (13/09/2026)

### Phễu nguồn, đầu vào

```
11.787 tài liệu -> 7.911 đã đọc -> 2.443 bóc được (31%) -> 3.222 cơ chế trong kho
2.319 cơ chế lọt khoảng kích hoạt [2%, 60%]
```

**Tồn kho 3.656 bản chưa đọc là RÁC** — đã xác minh bằng hiệu chuẩn hai chiều:
400/400 bản *đã bóc* chấm >= 1 điểm (trung vị 2), còn 0/3.656 bản tồn chấm được
điểm nào, ở **mọi** loại kể cả 24 EA. Đọc tay 5 bản ngẫu nhiên: trang điều hướng
QuantConnect, app khoá màn hình Windows tiếng Ba Tư, thông báo bản quyền, khung
trang TikTok, danh sách file của repo game server.

→ **Đừng nới bộ lọc. Đi tìm nguồn mới.** Đây là việc số 1 của SEEKER.

### Bảng sản phẩm (`b he`)

9 hệ đã qua cổng thật, 8 sạch. Tốt nhất:

```
XM_US100CASH.D1.mean_reversion_z5   CAGR 14,05%  Sharpe 1,16 (+0,66 vs mua-giữ)
                                    DD −13,5%    204 lệnh   0,64 lệnh/tuần
```

**Cả 9 hệ đều < 1 lệnh/tuần**, trong khi luật dự án loại thẳng hệ < 2 lệnh/tuần.
Ba giả thuyết đã kiểm:

- (a) cổng chọn lọc hệ thưa → **SAI** (PASS 0,22 vs FAIL 0,23 lệnh/tuần)
- (b) cơ chế từ EA mql5 dày hơn → **ĐÚNG** (kích hoạt 0,422 vs 0,257)
- (c) trần kích hoạt 0,60 vô căn cứ → **SAI** (nhóm >= 60% là nhóm TỆ NHẤT:
  CAGR trung vị −1,89%, tỉ lệ PASS 0% trên 356 mẫu)

### Phân bổ công sức của phễu (1.276 kết quả đã chấm)

```
phơi nhiễm   n     CAGR tv   Sharpe tv   tỉ lệ PASS
10–25%     494      −0,42      −0,15       1,2%    <- 39% công sức
25–40%     104      +0,86      +0,20       4,8%    <- chỉ 8% công sức
```

`_ty_le_kich_hoat` trong kho **dự báo phơi nhiễm thật với r = 0,964** (97 cặp),
nên xếp hạng trước khi chạy được. Đã sửa (mục 3.1).

### Quản trị lệnh (`b bench-qt`, đang chạy 3/7 mã)

EA `ea_QuanTriBench.mq5` — 11 họ, engine vào cố định, lưới an toàn ba tầng
(SL cứng 3 ATR + trần 120 nến + trần lỗ nổi 25% equity; tầng 3 vì tầng 1-2 không
chạm được họ lưới). Kết quả sơ bộ trên EURUSD/GBPUSD/USDJPY:

- **cao nguyên**: `tỉa`, `lưới DCA`, `huề trailing`, `trailing`
- **cái gai** (cực đại ngẫu nhiên): `stop 2 đầu`, `TT stop đôi`, `hedge`
- Báo cáo phải luôn có **trung vị + tỉ lệ ô hơn mốc**, không bao giờ chỉ max-of-N.

---

## 3. BỐN THỨ ĐÃ SỬA HÔM NAY (5 commit, đã test)

### 3.1 `to_hop.co_che_dung_duoc` — thứ tự duyệt theo VÙNG SINH LỢI

Trước: `sort(key=tên)` — bảng chữ cái. Khi `gioi_han` cắt thì cắt ngẫu nhiên.
Sau: xếp theo khoảng cách tới giữa vùng 0,25–0,40 (`VUNG_SINH_LOI`).
**Xác minh: 412/500 cơ chế duyệt đầu tiên nằm trong vùng sinh lợi (trước ~8%).**
Không loại thêm cơ chế nào — chỉ đổi THỨ TỰ.

### 3.2 `to_hop.ma_co_chi_phi_do_duoc` — chặn mã chi phí KHAI

Cơ chế của lỗi: mã không có nguồn phí = sàn không báo giá liên tục = cặp neo
(DKK neo EUR, CNH quản lý), cặp chết (EURRUR), cặp mỏng. Chúng **biến động thấp**,
mà `cagr_dd20` quy mọi thứ về cùng ngân sách sụt giảm 20% nên **phát đòn bẩy rất
lớn cho chuỗi ít biến động**. Kết quả: phễu thưởng cho sự thiếu hiểu biết.

Đo trên 1.100 ô chặng 1, top 40:

```
tất cả       cagr_dd20 tv 5,6 | mốc tv 0,0 | vượt mốc tv 5,39 | 39/40
chỉ mã SAN   cagr_dd20 tv 1,7 | mốc tv 2,2 | vượt mốc tv 0,62 | 26/40
```

`mốc = 0,0` chính là dấu hiệu: mua-giữ, bán-giữ và tiền mặt đều ~0 vì cặp không
đi đâu cả. Vũ trụ quét **145 → 72 mã**. Tắt được bằng `DOI_CHI_PHI_DO_DUOC`.

> Đính chính một nhãn đặt sai: `ho_so_symbol` ghi EURGBP/AUDCAD là `KHAI` spread 1,0
> — **bảng đó là bản cũ**. Đường chạy thật `chi_phi.tu_du_lieu` trả về `SAN` cho cả
> hai (đo từ cột spread bar H1: EURGBP 8,0 điểm, AUDCAD 19,0). 9 hệ của lab KHÔNG
> bị chấm bằng chi phí bịa. **Nhưng `ho_so_symbol.chon_ung_vien` dùng
> `TRAN_SPREAD_BPS = 8` trên chính bảng cũ đó → việc chọn ứng viên đang dùng spread
> giả. CHƯA SỬA.**

### 3.3 `to_hop.giu_co_han_ngach` — hạn ngạch theo mã ở chặng chọn

Chặng 1 trước là `sort()[:200]` không ràng buộc gì. Một mã chấm điểm cao có hệ
thống ăn trọn 200 suất → chặng 2/3/4 không còn nhìn thấy thị trường.
Đo 12/09 (khi còn bar hỏng): 200 ô sống sót → **2 mã**. Sau khi sửa bar: 23 mã,
mã dẫn đầu 8%. Hạn ngạch giữ đúng 200 ô, không hạ ngưỡng nào, trần 4%; ít mã quá
thì trần tự nới. Chặng 2 khoá theo `(mã, cơ chế)` vì mỗi hệ xuất hiện 15 lần ở đó.

### 3.4 `b he` đọc HAI nguồn — nối chặng 4 vào bảng sản phẩm

Khối A: `nao.db/ket_qua` (đã qua cổng thật). Khối B: `TO_HOP.json` (qua holdout
của phễu, **chưa** qua cổng). Khối B **không được ghi vào `ket_qua`** — làm vậy
là chiếm suất FDR bằng một phép đo.

Đọc ngay ra: hệ duy nhất qua holdout là `GBPTRY.D1.ns_nen_bua_<_q20_giu3`,
**hơn mốc 1,95 %/năm** — một sai số làm tròn trên một đồng tiền sụp đổ. Trước đây
con số đó không ai thấy.

---

## 4. VIỆC PHẢI LÀM, THEO THỨ TỰ

### A. Hai lần chạy đêm 13/09 — ĐÃ XONG, đọc kết quả ở đây

**Phễu D1** (`reports/TO_HOP.json`, 9.573 giây, 72 mã × 2.319 cơ chế):

```
chặng 1   162.330 ô -> 149.368 kết quả, 2.691 lỗi, 9.109s   giữ 200
chặng 2     3.000 ô ->   2.938 kết quả,     0 lỗi,   141s   giữ  40
chặng 3       155 ô
chặng 4     5.876 ô -> 2.248 cặp đủ hai đầu -> 592 "qua holdout"
```

Hạn ngạch có tác dụng thật, mạnh hơn tôi ước tính lúc viết mục 3.3: chặng 1 giữ
200 ô cho **44 mã**, nếu không có hạn ngạch thì chỉ **12 mã** và mã dẫn đầu ăn
**97/200 suất**. Chặng 2: 26 hệ thay vì 13.

**Nhưng con số 592 là VÔ GIÁ TRỊ** — xem mục 4.B.0. Ngoài rò rỉ ra còn hai thứ
phải trừ tiếp khi đọc lại: 592 hệ chỉ là **445 kết quả khác nhau** (phần còn lại
là cơ chế trùng mang tên khác — `ns_nen_rau_tren` và `ns_nen_sao_bang` cho số y
hệt nhau, cần khử trùng trong kho), và **210/592 hệ có dưới 30 lệnh** ở nửa
holdout (top bảng chỉ 17–20 lệnh).

**Bench quản trị lệnh** (`reports/QUET_BENCH_QT.json`, 7 mã × 3 engine = 19 ô;
13 ĐẠT · 1 ÂM · 5 CHƯA_ĐO_ĐƯỢC):

```
họ              cao nguyên  cái gai   Sharpe tv
trailing            7          7        −0,13
huề trailing        8          6        −0,15
tp cố định          7          4        −0,30
lưới DCA            7          6        −0,39
tỉa                 8          5        −0,42
đặt huề             6          4        −0,95
TT stop đôi         4          6        −1,11
hedge               5          7        −1,14
stop 2 đầu          4          7        −1,76
thời gian           4          2        −3,75
              mốc (không quản trị):     −0,57
```

Đọc đúng: **quản trị lệnh không tạo ra edge, nó giảm lỗ** — mọi con số đều âm vì
engine vào cố định không có edge trên 7 mã này. Năm họ đỡ được mốc −0,57;
năm họ còn lại tệ hơn cả việc không quản trị gì. `stop 2 đầu`/`hedge` nghiêng hẳn
về cái gai.

Hai chỗ phải biết:
- `thời gian` trên USDJPY cho Sharpe **5,94** — luật dự án nói `t_alpha > 5` là
  nghi nhìn trước; chính họ đó có trung vị tệ nhất bảng. Là cái gai, không phải
  phát hiện. Dùng trung vị thì nó không chui lọt.
- **US500Cash và US100Cash cho 0 lệnh trên toàn bộ 275 pass, cả ba engine** — tức
  bench **chưa hề đo được chỉ số CFD**, đúng chỗ hệ tốt nhất của lab đang sống.
  Bẫy đã ghi ở memory `tester-cfd-chi-so-3-bay`: cả ba kiểu hỏng đều ghi "0 lệnh".
  Máy gắn `CHƯA_ĐO_ĐƯỢC` chứ không gắn `ÂM` — ba trạng thái chạy đúng.

### B. Nút thắt thật, xếp theo giá trị

0. **CHẶNG 4 KHÔNG PHẢI HOLDOUT THẬT — ĐÃ SỬA, NHƯNG PHẢI CHẠY LẠI.**
   `v1`/`v2`/`v3` trong `to_hop.chay` là tuple 6 phần tử → `phan` mặc định `"het"`
   → **chặng 1, 2, 3 chọn trên TOÀN BỘ chuỗi, gồm cả nửa sau dùng làm holdout.**
   Hệ lọt tới chặng 4 đã được chọn bằng chính dữ liệu sắp dùng để kiểm.
   Hậu quả đo được đêm 13/09: **592/2.248 = 26% qua holdout.** Luật dự án gọi
   đúng tên: *"Nhiều PASS trong một ngày là tín hiệu HỎNG, không phải tin vui."*
   Lần chạy trước ra 1/2.609 chỉ vì bar hỏng của EURMXN nuốt cả bảng — tức lỗ
   hổng này **bị một lỗ hổng khác che mất**, chỉ lộ ra khi phễu bắt đầu chạy đúng.
   Đã sửa (commit `b6f359d`): ba chặng chọn đều chạy `"train"`, chỉ chặng 4 chạm
   cả hai nửa. **Việc đầu tiên của phiên sau: chạy lại `python -m nhan.to_hop
   --khung D1` (~2,5 giờ) — mọi con số ở mục 4.A đều phải đọc lại sau lần chạy đó.**

1. **SEEKER hết hàng.** Kho còn 3.656 bản nhưng là rác. Cần nguồn MỚI có LUẬT.
   Ưu tiên nguồn **CÓ FILE** (`.mq5`/`.ex5`/`.set` chạy tester được ngay) hơn văn
   xuôi. 223/840 file `.mq5` đã thu hồi chưa bóc — làm nốt trước khi đi săn.
2. **`ho_so_symbol` đang giữ spread giả 1,0 cho 90/159 mã** và `chon_ung_vien`
   lọc bằng chính nó. Chạy lại `ho_so_symbol.quet()` để nó lấy chi phí từ
   `chi_phi.tu_du_lieu` thay vì mặc định.
3. **Xếp hạng chọn ≠ tiêu chí xử.** Chặng 1/2 xếp theo `cagr_dd20` (tuyệt đối),
   chặng 4 xử theo `hơn mốc`. Chọn theo X rồi xử theo Y là lãng phí toàn bộ khâu
   chọn. Cả hai engine đều đã trả về `moc_dd20` sẵn → đổi khoá sort thành
   `cagr_dd20 - moc_dd20` là một dòng. **Chưa làm vì chưa đo được trên mẫu sạch
   đủ lớn** (mẫu cũ 100% EURMXN nên không phân biệt được). Đo rồi hãy đổi.
4. **`b ban-do` để truy 31 module mồ côi**, đặc biệt `nhan/han_muc.py` (kill-switch).
5. **Quản trị lệnh** — sơ đồ nói đây là *"module quan trọng trong toàn bộ hệ thống"*.
   Python mirror `_quet_quan_tri_python.py` chỉ làm được 6 họ một vị thế; 5 họ còn
   lại (hedge, lưới DCA, stop 2 đầu, TT stop đôi, thời gian) cần tester.
6. **Module so sánh tài sản / tương quan / mùa vụ** — chủ dự án yêu cầu ra thông
   tin phục vụ giao dịch được, "không phải hời hợt". `ho_so_symbol` đã đo được
   tính cách (Hurst dự báo được r = −0,567 trên 157 mã) nhưng chưa nối vào quyết định.

### B'. CHỦ DỰ ÁN CHỐT TỐI 13/09 — bảy điều, là LUẬT và ĐẶT HÀNG

**1. BỎ luật "< 2 lệnh/tuần → BỎ".** Nguyên văn: *"cứ có lãi là được. Tôi chỉ cần
lãi, ít lệnh thì ta kết hợp nhiều phương pháp hoặc đi lệnh to lên là được."*
→ Gỡ ngưỡng tần suất khỏi mọi bộ lọc (`cham_diem`, `cong.py`, `b he`). Ít lệnh
xử lý bằng **ghép nhiều hệ** cho kín lịch và **nâng size** (`bien_don_bay.py`,
trần `0,5·S²`), không phải bằng loại bỏ.

**2. QUẢN LÍ LỆNH có thể là module RA TIỀN NHẤT, không chỉ là lớp phủ.**
Nguyên văn: *"có những kiểu đánh chỉ dùng quản lí lệnh lợi dụng sự di chuyển của
giá để chốt rất nhanh 1 lệnh."*
→ Bench hiện tại **sai khung**: nó gắn quản trị lên một engine vào cố định rồi
hỏi "thêm quản trị thì đổi gì". Phải thêm họ **KHÔNG CẦN TÍN HIỆU VÀO** — vào
bất kỳ / đều đặn / ngẫu nhiên, rồi sống bằng chốt nhanh, lưới, hedge. Đó là một
họ chiến lược riêng.

**3. BẢNG ĐẶC TÍNH TÀI SẢN — đặt hàng cụ thể, phải trả lời được:**
cặp nào hay trend / cặp nào sideway · trend mạnh hay yếu · trend **chính** là
tăng hay giảm · biên độ tăng và biên độ giảm · một sóng chạy bao lâu · một năm
trung bình bao nhiêu sóng và **bắt đầu lúc nào** · trong ngày **hay đẩy giờ nào,
nghỉ giờ nào**. Và *"nghĩ thêm những thứ có thể khai thác ra"*.
Nguyên liệu đã có sẵn: `ho_so_symbol` (159 mã), `ho_so_song`, `ho_so_mua_vu`.
Thiếu là **bảng đọc được** và các cột trên.

**4. BẢNG MÙA VỤ** — phải là bảng đọc được, không phải JSON để đấy.

**5. TƯƠNG QUAN đã có mà chưa từng được báo cáo**: 158 mã, 11.960 cặp, cửa sổ ổn
định 252 bar, có `r_trung_vi` / `r_tuyet_doi_trung_vi` / `on_dinh_trung_vi` /
top cặp cao nhất (`reports/HO_SO_TUONG_QUAN_{D1,H4,H1}.json`, 12/09).
Vấn đề: không chỗ nào đọc nó. Phải nối vào khâu **ghép hệ** và khâu **chọn mã**.

**6. SEEKER không đủ hàng cho 1 năm — và không phải vì chậm.** Nạp vẫn 700–3.000
tài liệu/ngày, nhưng **3.656 bản tồn mới nhất có 0 bản chứa luật**. Các nguồn
đang quét đã bị vét cạn. Cần mở lớp nguồn mới, không phải chạy nhanh hơn.

**7. EVO + FINDER phải lắp được SKILL và CODE nâng cấp vào hệ**, và **quét vòng
mới**. 148 công cụ FINDER săn về (`reports/cong_cu.json`, 13/09) đang để không.

### B''. NÚT THẮT SỐ LƯỢNG PHÉP THỬ — sửa gần như miễn phí

Chủ dự án hỏi *"seeker đào về rất nhiều, tại sao dựng cơ chế ra chiến lược và
test lại ít vậy"*. Đo ra ngay:

```
chặng 1 chạy  162.330 ô -> 149.368 kết quả -> GIỮ 200  = 0,134%
chặng 2 giữ 40
```

**99,87% cơ chế bị loại sau đúng một phép thử rẻ nhất** (một cấu trúc, một khung,
không quản trị). Nhưng giá của các chặng sau rất rẻ: chặng 1 tốn 9.109s, chặng 2
chỉ **141s cho 3.000 ô**, chặng 4 chỉ **259s cho 5.876 ô**. Nâng `GIU_CHANG1`
200 → 1.000 và `GIU_CHANG2` 40 → 200 thì chặng 2 ≈ 12 phút, chặng 4 ≈ 22 phút.
**Gấp 5 lần số hệ được kiểm tử tế, chỉ thêm ~35 phút.** Làm cùng lúc với lần chạy
lại ở mục 4.B.0.

### C. Việc cần người dùng thao tác

- Gỡ 2 bản MT5 thừa (cần quyền admin): `C:\Program Files\XM MT5` và
  `C:\Program Files\MetaTrader 5 EXNESS`.
- `config/tai_khoan.json`: myfxbook / collective2 / fxblue còn trống (DNS đã thông).

---

## 5. BẪY ĐO LƯỜNG — KIỂM TRƯỚC KHI TIN BẤT KỲ SỐ NÀO

- **Ba trạng thái, không phải hai**: `ĐẠT` / `ÂM` / `CHƯA_ĐO_ĐƯỢC`. Mã thoát != 0,
  thiếu file ra, file ra cũ hơn lúc bắt đầu → **không bao giờ là `ÂM`**.
- **Hiệu chuẩn hai chiều**: một cổng từ chối TẤT CẢ cho số liệu y hệt một cổng tốt.
  Mọi bộ lọc mới phải kèm phép thử chiều ngược.
- **Cao nguyên hay cái gai**: không bao giờ báo max-of-N mà thiếu trung vị + tỉ lệ
  ô hơn mốc. So cực đại phải so cùng cỡ mẫu với bản giả.
- **`Model=1` của MT5 nói dối** khi TP < 2× biên độ nến M1 → phải chạy Model=0/4.
- **`Optimization=2` là thuật di truyền**, không phải quét đủ. Luôn dùng `=1`.
- **TESTER = 1 là ràng buộc VẬT LÝ.** Hai việc tester cùng lúc ghi đè kết quả của
  nhau và **không ai báo lỗi**.
- **Đòn bẩy gộp bằng log là SAI** cho `(S_T/S_0)^L`. Trần lãi suất ở MỌI đòn bẩy
  là `0,5·S²` — thấy CAGR vượt xa trần đó thì phép đo hỏng, không phải phát hiện.
- **Bar D1 của CFD không phải bar phiên** (rộng hơn 1,39 lần). Dùng `du_lieu.nap_phien`
  khi cơ chế nói về PHIÊN.
- **Chân trời giữ lệnh phải theo cơ chế**, không phải một số cứng: 67% cơ chế khai
  `giu <= 5 bar` mà phễu từng chạy tất cả ở 60 bar.
- **Đĩa đầy hiện ra như kết quả rỗng** (3 mẻ bóc báo rc=0 mà kho không đổi).
  `nhan/dia.py` là cổng nhận; `nao.db-wal` từng phình 1,4 GB.
- **`doc_kho` hỏng từng xoá sạch kho** (2.741 → 130). Nay có 5 chốt + `MOC_CAO` +
  `.json.lui`. Đừng bỏ chúng.
- **mql5.com cấm theo IP** sau ~50–150 lượt — không phải chuyện bật/tắt WARP.
  Đi chậm 8s/lượt. `CHO_DOI_IP = False`: **đừng tự bật VPN**, chủ dự án đã phản đối
  hai lần.
- **Bar hỏng ×10** đã dính 16/159 mã (EURMXN/GBPZAR/EURNOK). `nap()` tự sửa, và
  `to_hop._mot_o` có cổng `du_lieu.kiem(...).dung_duoc`. Nếu thấy một mã cho
  "CAGR 942%/năm" thì kiểm bar TRƯỚC khi mừng.

---

## 6. RÀNG BUỘC MÁY

20 luồng / ~29 GB đĩa trống. `nhan/ngan_sach.py`: `BANG_THONG=1 · LLM=8 ·
TESTER=1 · CPU_NANG=4`; nhịp theo host ghi ra đĩa để các tiến trình chia nhau.
Test chết 4 lần ở 56–94% là do **process mồ côi** (`ENOMEM: uv_spawn`), không
phải do code → dùng `b test-me`. Lần chạy đầy đủ gần nhất: **1.789 passed / 0 failed**
(132 file test).

---

## 7. NGUYÊN TẮC CỦA CHỦ DỰ ÁN (đừng làm ngược)

1. **Mục tiêu là TIỀN**, không phải chặt chẽ học thuật. MDE/FDR/placebo là **NHÃN
   CẢNH BÁO**, không phải CỔNG CHẶN. Chỉ chặn khi **thua mua-giữ ở CÙNG RỦI RO**.
2. **Quản lí lệnh quan trọng hơn entry.**
3. **"FX" = kiểu giao dịch long/short**, không phải riêng cặp tiền. Sàn FX có cả
   chỉ số, hàng hoá, kim loại. Chọn tài sản theo việc nó có ra tiền không.
4. **Làm liên mạch, không chờ duyệt.** Duyệt sẵn mọi đề xuất.
5. **Sơ đồ là SÀN, không phải TRẦN** — *"tôi muốn Claude phải làm được hệ thống đó
   và có thể nâng cấp phát triển hơn cả mô tả của tôi"*.
6. Mục tiêu hiện tại **chưa phải ra nhiều cơ chế hay kiếm tiền, mà hệ thống phải
   tốt đã** — các module và trụ là cơ sở cho bóc tách và test sau này. Trong quá
   trình làm, **quan sát vấn đề phát sinh rồi sửa** để nâng cấp hệ.

---

## 8. KIẾN TRÚC CHO ENGINE TỔ HỢP (chốt tối 13/09)

Chủ dự án nói rõ mục đích ban đầu của The Brain: **test mọi tổ hợp và xác suất
của chỉ báo** — tổ hợp `symbol × timeframe × indicator × quản lí lệnh` (chưa tính
tương quan, mùa vụ, data ngoài, tin tức), hàng triệu tổ hợp, máy chạy 24/7 nhiều
tháng. Mọi thứ dưới đây phải đọc dưới góc đó.

### 8.1 Giá một ô là biến quyết định tất cả

Đo 13/09 trên `XM_US100CASH D1`:

```
nạp dữ liệu              0,798 s     <- chiếm 14/15 thời gian
sinh tín hiệu            0,002 s
mô phỏng + tính tiền     0,038 s
                        ---------
tính toán THẬT           0,040 s/ô   trong khi chặng 1 trả 0,56 s/ô
```

`du_lieu.nap` cache ra **parquet trên đĩa**, không cache trong bộ nhớ → mỗi ô
đọc lại file. Đã sửa bằng `to_hop._nap_nho` (LRU 4 bảng/tiến trình):
**0,56 → 0,0424 s/ô, nhanh gấp 13,2 lần.** Chặng 1 từ 2,5 giờ xuống ~12 phút.

Năng lực máy này sau khi sửa (10 tiến trình): **~236 ô/giây ≈ 20 triệu ô/ngày**.

```
   1 triệu ô  ->  ~70 phút
  10 triệu ô  ->  ~12 giờ
 100 triệu ô  ->  ~5 ngày
```

Tức "hàng triệu tổ hợp" là **chuyện vài giờ**, không phải vài tháng. Nút thắt
tiếp theo là 95% còn lại nằm trong `vao_lenh.so_cau_truc` (mô phỏng + tính tiền)
— vectorise chỗ đó là bước tăng tốc lớn kế tiếp.

### 8.2 Không enumerate cái tích — phải phân tầng

Ước lượng không gian thật: ~250 cặp (mã, khung) có đủ dữ liệu × (300 chỉ báo ×
8 tham số) ≈ 2.400 nút × ~4 dạng so sánh ≈ 10.000 tín hiệu vào.

```
đơn:   250 × 10.000        =   2,5 triệu ô   -> ~3 giờ        CHẠY HẾT ĐƯỢC
đôi:   250 × 2.400C2       = 720 triệu ô     -> ~35 ngày      KHÔNG chạy hết
```

Nên: **quét hết tầng đơn**, rồi chỉ ghép đôi/ba từ người sống sót, và ghép trên
vài mã đại diện trước khi mở ra toàn bộ. Hình dạng 4 chặng của `to_hop` đã đúng;
sai là **suất giữ**: chặng 1 giữ 200/149.368 = 0,13%. Với tốc độ mới, suất giữ
nên là hàng nghìn (xem mục 4.B'').

### 8.3 SEEKER phải đổi vai: cung cấp NGUYÊN LIỆU, không phải SẢN PHẨM

Quan sát của chủ dự án: *"ichimoku 10 trader châu Á có 20 kiểu dùng khác nhau"*.
Đúng — và điều đó có nghĩa cái biến thiên là **cách ghép và ngưỡng**, không phải
bản thân chỉ báo. Nên 20 kiểu dùng Ichimoku **không phải 20 lần bóc tài liệu**,
mà là **1 chỉ báo + lưới tham số + tổ hợp**, do máy sinh.

Đây giải thích cả hai triệu chứng cùng lúc:
- **Seeker cạn hàng** vì ta bắt nó đẻ ra sản phẩm cuối (cơ chế) từ tài liệu, mà
  tài liệu thì hữu hạn.
- **Kho chỉ rộng 8 chỉ báo** (EMA 546 · RSI 525 · SMA 463 · zscore 239 · ATR 114
  · Donchian 80 · ADX 36 · Stoch 35 · MACD 15; **Bollinger/Ichimoku/VWAP/Pivot/
  Fibonacci/Volume/FVG/order-block = 0**) vì độ rộng đang phụ thuộc vào việc có
  ai viết bài về nó hay không.

Việc phải làm: **thư viện chỉ báo là một module hạng nhất**, sinh bằng máy, độc
lập với tài liệu. 190/389 file chỉ báo đã tải về chưa vào khâu bóc chính là kho
nguyên liệu đó — chúng không có "luật vào/ra" nên bộ bóc bỏ qua, nhưng một chỉ
báo là một **hàm số**, đúng thứ ngữ pháp cần. Việc là **dịch chỉ báo thành một
nút vẫn**, không phải bóc luật.

Khi đó vai của SEEKER đổi: đi tìm **chỉ báo mới và ý tưởng ghép**, chứ không đi
tìm chiến lược hoàn chỉnh.

### 8.4 Với hàng triệu phép thử, ĐIỂM CAO là rác — phải chọn theo HÌNH DẠNG

Quét 1 triệu tổ hợp thì cực đại của nhiễu thuần tuý cũng rất đẹp. Bộ lọc vì thế
không được xếp theo "điểm cao nhất" mà theo **hình dạng**:

- **cao nguyên** — hàng xóm tham số cũng tốt (`do_hinh_dang`). Nhiễu không có
  hàng xóm.
- **sống ở nửa sau** — holdout thật (xem mục 4.B.0).
- **sống trên nhiều mã** — placebo đa tài sản.

Ba công cụ này dự án **đã có**, nhưng đang nằm ở cuối dây chuyền như con dấu.
Trong một engine tổ hợp chúng phải là **tiêu chí chọn ở giữa**, vì đó là thứ duy
nhất phân biệt được phát hiện với cực đại ngẫu nhiên ở quy mô triệu.

### 8.5 Sổ kết quả phải đổi

20 triệu ô/ngày không ghi vào SQLite được (`nao.db-wal` đã từng phình 1,4 GB với
lượng nhỏ hơn nhiều). Kết quả thô nên ghi **parquet theo cột**, chỉ đẩy vào
`nao.db` những dòng đã qua chặng kiểm.

### 8.6 Bốn nguồn cơ chế — đánh giá

| loại | trạng thái | nhận định |
|---|---|---|
| 1. file mql5 + bài chiến lược | 773 cơ chế | đang chạy, nhưng **sẽ cạn** — kho hữu hạn và đã vét gần hết |
| 2. ghép vài chỉ báo thành phương pháp | **0** | **hố to nhất và rẻ nhất**; 190 file chỉ báo nằm sẵn; không phụ thuộc nguồn ngoài |
| 3. lý thuyết → cơ chế | gần 0 | đã thử: 24.244 câu cho **4 điều kiện**. Bài báo nói *hiện tượng*, không nói *ngưỡng*. Muốn khai thác phải đổi câu hỏi thành "biến X dự báo Y → dựng cơ chế nào đo X" |
| 4. ghép cơ chế (chân mua + chân bán) | có, làm tay | **đo được là sống tốt nhất**: hệ đơn qua holdout 822→40, cặp ghép giữ hạng 39/45; 129 cơ chế âm đảo chiều thành 38 dương. Nhưng phễu vẫn đẻ hệ ĐƠN, ghép là bước tách rời |

### 8.7 Suy ngược lịch sử giao dịch — phải có BÀI KIỂM CÓ ĐÁP ÁN

Chủ dự án lo: Ultima mất cả ngày mới ra luật thật (đọc log + `.set` + clip tác
giả), vậy quét hàng trăm chiến lược để suy ngược liệu có quá nhanh.

Cách giải quyết không phải tranh luận mà là hiệu chuẩn: cho bộ suy ngược chạy
trên lịch sử giao dịch của **Ultima, DongDongTV DCA, Session Trading V3** — ba
bot ta **đã biết chắc luật**. Nếu nó không dựng lại được luật đã biết đáp án thì
mọi kết quả trên chiến lược lạ đều là suy đoán, và con số "400 signal → AUDCAD"
phải đọc lại. Rẻ, và làm xong thì hết phải đoán.

### 8.8 Telegram: bộ vào ĐÃ CÓ từ 11/08

`telethon_ban` đã có khoá + phiên, cách cào tăng dần đã ghi. Nó chỉ **không nằm
trên đường chạy** của SEEKER. Việc số một không phải viết bộ cào mới mà là **cắm
cái đã có vào `day_chuyen`**, rồi mới mở sang social khác.

---

## 9. HEPHAESTUS — module đẻ cơ chế (duyệt tối 13/09)

Tên đã chốt: **HEPHAESTUS** (`nhan/hephaestus.py`, gọi tắt `b hepha`) — thần lò
rèn Hy Lạp. Đúng nghĩa cái lò: **nguyên liệu thô vào, cơ chế ra**.

Ranh giới ba việc, từ nay không ai làm hộ ai:

```
SEEKER       chỉ lo NGUỒN VÀO   — mang về chỉ báo, phương pháp, ý tưởng ghép
HEPHAESTUS   ĐẺ CƠ CHẾ          — rải lưới tham số, ghép nút, sinh tổ hợp
QUANTLAB     TEST               — phễu, quản lí lệnh, cổng
```

Hai bễ của Hephaestus:

- **`tu_vung`** — tự sinh thêm **từ khoá / chỉ báo / hướng tìm kiếm** trong lúc
  nghiên cứu, rồi **đẩy ngược về SEEKER**. Seeker không tự nghĩ ra "đi tìm
  Ichimoku"; Hephaestus bảo nó đi tìm. Chủ dự án đã yêu cầu việc này từ trước,
  hệ chưa bao giờ có.
- **`duc_co_che`** — lấy chỉ báo trong thư viện, rải lưới tham số, ghép 2–3 nút.

**Việc khởi động rẻ nhất:** 190/389 file chỉ báo đã nằm sẵn trên đĩa, bộ bóc bỏ
qua vì chúng không có "luật vào/ra". Nhưng chỉ báo là một **hàm số** — đúng thứ
`ngu_phap` cần. Dịch chúng thành **nút vẫn**, không phải bóc luật.

Vì sao đây là đường thoát cho việc Seeker cạn hàng: *"10 trader châu Á có 20
kiểu dùng Ichimoku"* nghĩa là cái biến thiên nằm ở **cách ghép và ngưỡng**, không
ở bản thân chỉ báo. 20 kiểu dùng **không phải 20 lần bóc tài liệu** — là 1 chỉ
báo + lưới tham số + tổ hợp, do máy sinh. Kho hiện chỉ rộng 8 chỉ báo vì độ rộng
đang phụ thuộc vào *có ai viết bài về nó hay không*.

---

## 10. GHÉP: KHÔNG ĐƯỢC LỌC TRƯỚC KHI GHÉP

Chủ dự án bắt đúng một mâu thuẫn trong đề xuất phân tầng ở mục 8.2:
*"nếu ta chỉ chọn những kẻ sống sót kết hợp lại thì liệu có ổn không?"*

**Không ổn.** Lọc tầng đơn theo "có lãi" vứt đúng thứ nguyên liệu làm việc ghép
có giá trị. Hai lý do, cả hai đã đo:

- chân **âm vì đi sai chiều** chỉ là dấu trừ — 129 cơ chế âm → 38 thành dương;
- chân **âm nhưng ngược pha** làm cặp tốt lên — ghép chân âm cho 6,14% →
  20,25%/năm ở **cùng sụt giảm**, rẻ hơn ghép chân mạnh.

**Lối thoát không phải lọc khéo hơn, là ĐỪNG LỌC.** Sai lầm trong mục 8.2 là
tính ghép bằng cách **mô phỏng lại** (720 triệu ô → 35 ngày → buộc phải lọc).
Không cần:

- Nếu tầng đơn **giữ lại chuỗi lợi suất** của mỗi chân (không chỉ giữ số tổng
  kết), ghép là **phép cộng vector**.
- Sharpe của một cặp tính **chính xác** từ `(μ₁, μ₂, σ₁, σ₂, ρ)` — không chạy lại
  gì. Với 10.000 chân trên một mã, ma trận hiệp phương sai là **một phép nhân ma
  trận** (BLAS, vài chục giây) và cho Sharpe của **toàn bộ ~50 triệu cặp** cùng lúc.
- Sụt giảm **không** cộng tuyến tính → chỉ vài nghìn cặp đầu bảng mới mô phỏng thật.

Hệ quả cho thiết kế tầng đơn: **lọc theo "tín hiệu hay nhiễu", không theo "lãi
hay lỗ"** — tức độ lớn hiệu ứng + **độ ổn định của DẤU** (kể cả dấu âm giữ
nguyên âm ở cả hai nửa) + đủ số lần kích hoạt. Chỉ chân **ngẫu nhiên** mới là rác.

Đường tới hàng tỷ tổ hợp, tính lại cho đúng:

```
mô phỏng THẬT      vài triệu chân đơn            ->  vài giờ
ghép bằng ĐẠI SỐ   hàng trăm triệu ~ tỷ cặp      ->  vài phút
mô phỏng lại       vài nghìn cặp đầu bảng        ->  vài phút
```

Một tỷ ô **mô phỏng** vẫn là 49 ngày. Hàng tỷ khả thi **bằng đại số, không bằng
cơ bắp**. Và ở quy mô đó, xếp theo điểm là tự đầu độc — phải xếp theo **hình
dạng** (mục 8.4).

---

## 11. HAI LÀN — giải bài toán "AUDCAD có hy vọng mà cứ đi xây máy"

Chủ dự án: *"ta đang thấy có hy vọng ở AUDCAD trong khi đó cứ mất thời gian xây
1 hệ thống dài hạn như này rất phí. Bài toán đó sau này cũng tương tự nếu ta test
nhiều hơn."*

Đây là bài toán **khai thác vs xây máy**, và nó sẽ lặp lại mãi — càng test nhiều
càng hay gặp. Lời giải là **hai làn tách hẳn, ngân sách cố định, không tranh nhau**.

```
LÀN NHANH (khai thác)   thứ đã có dấu hiệu ra tiền -> tester thật -> demo -> tiền thật
LÀN CHẬM  (xây máy)     Hephaestus · thư viện chỉ báo · engine tổ hợp · bảng đặc tính
```

**Chia tài nguyên theo ràng buộc VẬT LÝ, nên nó tự nhiên không tranh nhau:**
`TESTER = 1` là làn nhanh sở hữu; CPU nhiều nhân là làn chậm sở hữu. Làn chậm
chạy Python, làn nhanh chạy MT5 — hai tài nguyên khác nhau, chạy song song được.

**Luật vào làn nhanh (phải viết ra, không để cảm tính):**
1. đã qua holdout **thật** (nửa sau chưa hề bị chạm lúc chọn), và
2. hơn mốc `max(mua-giữ, bán-giữ, tiền mặt)` ở **cùng rủi ro**, và
3. chi phí `do_tin = SAN` (đo được, không phải khai), và
4. chạy được thật: đủ vốn, lot tối thiểu không kẹp, số lệnh đủ để không phải may rủi.

**Giới hạn việc dở dang (WIP) của làn nhanh: 3.** Quá 3 thì không nhận thêm dù
có hấp dẫn — nếu không, làn nhanh nuốt hết và ta lại không bao giờ xây xong máy.
Mỗi việc trong làn nhanh có **hạn chót**; hết hạn mà chưa ra tiền thì trả về kho.

**Điều đáng nói:** module này **đã nằm trong sơ đồ** — QUANTLAB có "luồng ưu
tiên", `nhan/uu_tien.py` đã tồn tại — và **chưa bao giờ chạy một lần nào**
(không có một file kết quả nào trong `reports/`). Lại đúng họ lỗi ở mục 0.
Việc cần làm không phải nghĩ ra cơ chế mới, mà là **cắm `uu_tien.py` vào đường
chạy và cho nó hai làn này**.

---

## 12. NHỊP GIÁM SÁT — chống lạc đề, chống sa vào tiểu tiết

Chủ dự án yêu cầu Claude giám sát khâu thiết kế + vận hành, *"vừa cụ thể vừa
luôn có cái nhìn tổng quan, tránh lạc đề và đi vào tiểu tiết quá"*. Bốn luật:

1. **Mỗi phiên chọn ĐÚNG MỘT nút thắt, và nút đó phải ĐÃ ĐO.** Không sửa thứ
   chưa đo — đó là cách một ngày trôi vào tiểu tiết. Ngày 13/09 mất nửa ngày vì
   đi sửa MT5 (chưa đo là nút thắt) thay vì phễu (đã đo).
2. **Mỗi module phải có định nghĩa "XONG" viết ra trước khi bắt đầu.** Không có
   thì nó thành vô hạn — như "tổng quan tài sản" đã chạy nhiều lần mà không ai
   nói được nó xong hay chưa.
3. **Báo cáo theo MODULE, không theo dòng thời gian.** Chủ dự án đã phải nhắc:
   *"hãy báo cáo theo form hệ thống để tôi biết từng module làm được gì rồi và
   vấn đề là gì"*. Mẫu đúng nằm ở mục 2 và mục 7 của file này.
4. **Đo trước khi đoán nút thắt.** Hôm nay: "giá một ô" đoán là mô phỏng, đo ra
   là **đọc lại file** (14/15 thời gian). Mọi lần đoán sai đều tốn một ngày.

---

## 13. KẾ HOẠCH NGÀY 100M TOKEN — 8 luồng song song, chạy được ngay

Gói 100M token/24h chỉ đáng tiền nếu **không mất nửa buổi đầu để chia việc**.
Dưới đây là đặc tả đủ chặt để mỗi luồng chạy độc lập ngay từ phút đầu.

**Ba luật bắt buộc cho mọi luồng:**
1. **Mỗi luồng SỞ HỮU file của nó** (cột "file sở hữu"). Không luồng nào sửa
   file của luồng khác — đó là cách duy nhất để 8 luồng không giẫm nhau.
2. **Mỗi luồng tự viết test của mình**, và test phải có **chiều ngược** (bộ lọc
   mới phải chứng minh nó không loại sạch, cũng không nhận sạch).
3. **Không luồng nào được sửa `nhan/ngu_phap.py` lõi, `nhan/so.py`, `nhan/cong.py`.**
   Cần đổi thì báo, Claude chính sửa. Đây là ba chỗ mọi thứ đi qua.

| # | Luồng | Việc | File sở hữu | XONG nghĩa là |
|---|---|---|---|---|
| 1 | **THƯ VIỆN CHỈ BÁO** | Dịch 190 file chỉ báo đã tải thành **nút vẫn** của ngữ pháp. Không bóc luật vào/ra — chỉ báo là một hàm số. | `nhan/thu_vien_chi_bao.py`, `test_thu_vien_chi_bao.py` | ≥ 120 chỉ báo gọi được bằng tên, mỗi cái có test sinh ra mảng đúng độ dài và không toàn NaN. Bollinger/Ichimoku/VWAP/Pivot/Fibonacci/volume **phải có** |
| 2 | **HEPHAESTUS — đúc cơ chế** | Rải lưới tham số + ghép 2–3 nút thành cơ chế hợp lệ | `nhan/hephaestus.py`, `test_hephaestus.py` | Sinh ≥ 50.000 cơ chế hợp lệ (`ngu_phap.kiem_khai_bao` không báo lỗi), khử trùng bằng `van_tay_dieu_kien`, ghi vào kho qua `them_co_che` |
| 3 | **HEPHAESTUS — từ vựng** | Tự sinh từ khoá / chỉ báo / hướng tìm mới, **đẩy ngược về SEEKER** | `nhan/hepha_tu_vung.py`, `test_hepha_tu_vung.py` | Sinh danh sách từ khoá có thứ hạng, ghi vào hàng đợi săn của `seeker`; chứng minh ≥ 1 từ khoá mới dẫn tới tài liệu mới |
| 4 | **ENGINE GHÉP** | Giữ **chuỗi lợi suất** từng chân; Sharpe mọi cặp bằng ma trận hiệp phương sai; chỉ mô phỏng lại top | `nhan/ghep_ma_tran.py`, `test_ghep_ma_tran.py` | 10.000 chân → Sharpe của mọi cặp < 60 giây; kiểm đối chiếu: 20 cặp tính bằng công thức phải khớp mô phỏng thật trong sai số 1e-6 |
| 5 | **BẢNG ĐẶC TÍNH** | 8 cột chủ dự án đặt: trend/sideway · trend mạnh yếu · chiều trend chính · biên độ tăng và giảm · thời gian một sóng · số sóng mỗi năm · sóng bắt đầu lúc nào · trong ngày đẩy giờ nào nghỉ giờ nào | `nhan/bang_dac_tinh.py`, `test_bang_dac_tinh.py` | Một bảng **đọc được** cho ≥ 72 mã, `b dac-tinh` in ra được, mỗi cột có test trên chuỗi dựng sẵn biết trước đáp án |
| 6 | **MÙA VỤ + TƯƠNG QUAN NỐI VÀO QUYẾT ĐỊNH** | Biến `HO_SO_MUA_VU` và `HO_SO_TUONG_QUAN` từ JSON để đấy thành bảng đọc được **và** thành đầu vào chọn mã / chọn cặp ghép | `nhan/bang_mua_vu.py`, `nhan/tuong_quan_dung.py`, test tương ứng | `b mua-vu` và `b tuong-quan` in bảng; và `ghep_ma_tran` gọi được hàm "cặp này có ngược pha không" |
| 7 | **QUẢN TRỊ LỆNH — họ không cần tín hiệu vào** | Thêm họ vào **bất kỳ / đều đặn / ngẫu nhiên** rồi sống bằng chốt nhanh, lưới, hedge. **Và sửa lỗi 0 lệnh trên chỉ số CFD** | `ea_QuanTriBench.mq5`, `chay_bench_quan_tri.py`, `_quet_bench_qt.py` | US500Cash/US100Cash ra **số lệnh > 0**; có ≥ 3 họ không dùng tín hiệu vào; báo cáo có trung vị + tỉ lệ ô hơn mốc |
| 8 | **HAI LÀN + SUY NGƯỢC CÓ ĐÁP ÁN** | Cắm `uu_tien.py` vào đường chạy với luật hai làn ở mục 11; và chạy bài kiểm có đáp án cho bộ suy ngược trên Ultima / DongDongTV / Session V3 | `nhan/uu_tien.py`, `nhan/suy_nguoc.py`, test tương ứng | `b uu-tien` in ra hai làn với WIP ≤ 3; và báo **tỉ lệ dựng lại đúng luật** của 3 bot đã biết đáp án |

**Thứ tự phụ thuộc** (cái nào phải xong trước):

```
1 THƯ VIỆN CHỈ BÁO  ->  2 HEPHAESTUS đúc cơ chế
4 ENGINE GHÉP       <-  cần chuỗi lợi suất, nên to_hop phải xuất thêm cột
5, 6, 7, 8          ->  độc lập hoàn toàn, chạy ngay từ phút đầu
3                   ->  độc lập, nhưng chỉ có ích sau khi 1 xong
```

Nên phút đầu tiên bật **1, 4, 5, 6, 7, 8** (sáu luồng), rồi **2, 3** khi luồng 1
giao được đợt chỉ báo đầu tiên.

**Việc của Claude chính trong ngày đó** (không giao cho luồng con): giữ kiến
trúc, duyệt từng luồng khi nó giao, chạy phễu và tester, và **không để 8 luồng
đẻ ra 8 cách đặt tên khác nhau**.

**Việc phải làm TRƯỚC khi bật 8 luồng** (nếu chưa xong trong 2–3 ngày tới):
chạy lại phễu đã sửa rò rỉ (mục 4.B.0) và nới suất giữ (mục 4.B''), để có một
mốc số sạch mà so.
