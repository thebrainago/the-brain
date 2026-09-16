# HO SO HE THONG — THE BRAIN

*Sinh tu ma nguon + `nao.db` luc 2026-09-16 11:58 bang `b ho-so`.*

> **Doc file nay the nao.** No TU DU: khong can mo repo. Moi con so o day
> do duoc luc sinh, khong chep tu bao cao cu. Ba muc **KHONG** co trong
> file: ma nguon chi tiet, du lieu gia, va ket qua tung backtest — neu can
> chung thi phai hoi nguoi co dia. Muc 7 (**luat doc ket qua**) la bat
> buoc doc truoc khi khuyen bat ky dieu gi.

## 1. He nay de lam gi

Mot phong nghien cuu tu dong: thu thap moi chien luoc / kien thuc / san pham giao
dich (EA, chi bao, he thong), kiem dinh chung, roi giu lai cai RA TIEN.

Bon rang buoc do chu du an dat, khong duoc suy dien nguoc:

1. **Muc tieu la TIEN, khong phai chat che hoc thuat.** Nguyen van: *"khong phai
   nhung mo hinh kinh te hay quan tri quy de ma can de cao qua nhieu tieu chi hoc
   thuat. Muc dich cuoi cung la co tien, chap nhan ca chi phi va rui ro cao"*.
   MDE / FDR / placebo la **NHAN CANH BAO**, chi chan khi he thua mua-giu O CUNG
   MUC RUI RO - do moi la cau hoi tien.
2. **QUAN LI LENH quan trong hon ENTRY.** Nguyen van: *"module quan trong trong
   toan bo he thong"*. Da do duoc: entry tinh SAI van cho 92-97%/nam khi co lop
   quan tri dung.
3. **"FX" = KIEU GIAO DICH long/short co don bay**, khong phai chi cap tien. San
   fx co ca chi so, hang hoa, kim loai. Chon tai san theo viec no co ra tien
   khong, khong theo lop tai san.
4. **Chay da luong**, duoc dung 95% CPU, duoc goi LLM re (qwen) het co.

## 2. So do duong di that

Sau chang. Con so trong ngoac la **so thuc te dang o chang do**, do luc sinh.

```
  [1] NGUON                tru/seeker.py
      github · openalex · crossref · mql5_code · tradingview_pine · reddit
        |                                              (12078 tai lieu)
        v
  [2] DOC TOAN VAN         nhan/toan_van · doc_pdf · doc_anh · doc_video · go_html
        |                                     (7348 doc tron, 4125 cho doc)
        v
  [3] BOC -> CO CHE        nhan/ngu_phap.py  <- CUA DUY NHAT kien thuc vao he
      doc_ma · doc_chi_bao · doc_hieu · boc_llm · quan_tri
        |                                        (18 mau chien luoc)
        v                                        (148 cong cu trong kho)
  [4] SINH GIA THUYET      noi_sinh · ngoai_sinh · suy_nguoc · to_hop
        |                                        (387 gia thuyet dang ky)
        v
  [5] KIEM DINH            mo_phong -> sang_loc(V0..V3) -> cong -> cham_diem
      MT5 tester: dich_mq5 -> terminal64.exe (LAN = 1, rang buoc VAT LY)
        |                     (1284 ket qua · 705 ung vien · 1811 dong FDR)
        v
  [6] RA THAT              danh_muc -> chay_that -> so_lenh -> suy_giam
                                        (9 he qua cong · he dang NAM IM)
```

**Cua vao that** (ngoai bon duong nay thi module coi nhu khong ton tai):
`b.py` (lenh nguoi go) · `dieu_phoi.py` (tru chay 24/7) · `day_viec.py` (hang doi xay) · `qwen/NHIEM_VU.json` (bang viec tu chay).

## 3. Nam tru — trang thai that

| Tru | Dong | Goi bao nhieu module loi | Danh gia |
|---|---|---|---|
| SEEKER | 2647 | 17 | dang chay, LON NHAT he |
| QUANTLAB | 1806 | 18 | dang chay |
| EVOLUTION | 1393 | 8 | dang chay |
| BANKER | 550 | 1 | **VO** — chua xay |
| FINDER | 442 | 2 | **VO** — chua xay |
| NGHI | 450 | 6 | co chay |

## 4. Ho so tung thanh phan

Moi thanh phan doc theo nam truong: **vai tro · nhiem vu · nang luc THUC TE · van de con ton · huong giai**. Truong 'nang luc thuc te' luon kem SO DO DUOC — khong co so thi ghi ro la chua do.

### TRU · SEEKER

| | |
|---|---|
| **Vai tro** | Pheu nguon. Cua duy nhat kien thuc ben ngoai di vao he. |
| **Nhiem vu** | Tim nguon -> tai tai lieu -> doc toan van -> day sang khau boc. |
| **Nang luc thuc te** | 12.078 tai lieu tu 8 nguon (github 3.309 · openalex 1.828 · crossref 1.485 · mql5_code 1.168 · tradingview_pine 696). 7.348 doc tron ven (~20.590 trang A4). 2.647 dong, goi 17 module loi — LON NHAT he. |
| **Van de con ton** | Chuyen doi **0,15%**: 12.078 tai lieu -> 18 mau chien luoc. 4.125 tai lieu con nam cho doc. mql5.com cam theo IP sau ~50-150 luot. Hang doi tung bi 406 URL TradingView chet chiem cho va bao 'het ton kho' gia. |
| **Huong giai** | **Dong bang quy mo.** Chuyen uu tien sang nguon CO FILE CHAY DUOC (`.mq5`/`.ex5`/`.set` ra tester duoc ngay) thay vi van xuoi. Do da chung minh hai lan: kho x6 khong lam tang dau ra. |

### TRU · QUANTLAB

| | |
|---|---|
| **Vai tro** | Phong kiem dinh. Noi mot gia thuyet duoc phep doi doi. |
| **Nhiem vu** | Boc -> loc -> ho so tai san -> ghep ung vien -> cham diem -> cong. |
| **Nang luc thuc te** | 1.806 dong, goi 18 module. 387 gia thuyet dang ky · 1.284 ket qua · 705 ung vien · 592 qua holdout pheu · **9 he qua cong (that ra 7)**. Quy trinh 4 buoc chay het trong **6 giay**. |
| **Van de con ton** | Xep hang theo Sharpe chu khong theo tien (V1). 169/540 co che trong kho chua tung qua noi cong cua chinh he. Khong he nao vua ra tien vua cach xa mua-giu. |
| **Huong giai** | Noi `cong_ra_tien` lam cong CUOI. Chay lai ca kho qua cong sau khi khu trung. |

### TRU · EVOLUTION

| | |
|---|---|
| **Vai tro** | Tu giam sat: nhin ra he dang hong cho nao roi de xuat sua. |
| **Nhiem vu** | Cham suc khoe tung module, cat nghia, sinh de xuat. |
| **Nang luc thuc te** | 1.393 dong, goi 8 module. `b evo` chay duoc, co bang suc khoe module. |
| **Van de con ton** | Vong khong khep: EVO **de xuat** nhung khong co duong tu de xuat sang `day_viec.py` (hang doi viec xay), nen de xuat nam do. |
| **Huong giai** | Noi `evo` -> `day_viec`: moi de xuat dat nguong thi tu vao hang doi. |

### TRU · BANKER

| | |
|---|---|
| **Vai tro** | Vi mo: boi canh lai suat / dong tien de nghieng size. |
| **Nhiem vu** | Cap nhat vi mo lien tuc, phan tich sat sao. |
| **Nang luc thuc te** | 550 dong nhung **goi dung 1 module** (`so`). Tuc la VO. |
| **Van de con ton** | Chua xay. Bao cao lau nay coi no nhu 'dang chay yeu' — sai, no chua chay. |
| **Huong giai** | **Giu, ha uu tien** dung lenh chu du an: xong ba module that truoc. Manh macro da do duoc (tilt theo thay doi loi suat 10Y) thi giu lam hat giong. |

### TRU · FINDER

| | |
|---|---|
| **Vai tro** | Di san cong nghe/cong cu ngoai de nang ha tang, thay vi tu viet. |
| **Nhiem vu** | Tim repo/cong cu -> danh gia -> tich hop. |
| **Nang luc thuc te** | 442 dong, goi 2 module. Kho cong cu co **148 muc** (18 la phuong phap). |
| **Van de con ton** | 110 the ket o trang thai MOI; nut that la **bang anh xa** cong cu -> nhu cau, khong phai kha nang tim. |
| **Huong giai** | Sau dot 2. Khi lam thi lam bang anh xa truoc, dung san them. |

### TRU · NGHI

| | |
|---|---|
| **Vai tro** | Bien thu DOC DUOC thanh thu KIEM DINH DUOC, roi hoc tu ket qua. |
| **Nhiem vu** | Van xuoi -> khai bao DSL -> chay -> ghi bai hoc. |
| **Nang luc thuc te** | 450 dong, goi 6 module. So bai hoc tra loi duoc 'cai nay da thu chua'. |
| **Van de con ton** | Suat boc thap: LLM dien co che cho 48 khai bao, tham dinh bac 41, **rong cuu 3**. Kho bai bao 24.244 cau -> 4 dieu kien. |
| **Huong giai** | Doi nguon chu khong doi bo loc: bo loc dang loai DUNG, nut that la NGUON. |

### LOP · SO & HOP DONG

| | |
|---|---|
| **Vai tro** | Mot nguon su that cho ca nam tru. |
| **Nhiem vu** | Ghi gia thuyet / ket qua / FDR / bai hoc; ghim ban du lieu de tai lap. |
| **Nang luc thuc te** | `nao.db` **1,6 GB**, 26 bang. Pre-registration co `plan_hash`. `anh_chup` ghim ban du lieu cho moi ket qua. |
| **Van de con ton** | DB phinh lang le: `nao.db-wal` tung len 1,4 GB va lam 3 me boc bao XONG rc=0 ma kho khong doi. Dia day hien ra nhu ket qua rong. |
| **Huong giai** | `b don-dia` (gop WAL) vao nhip ngay. Dong bang kho sau khi dong bang thu thap. |

*10 module:* `so` · `hop_dong` · `quant_plan` · `anh_chup` · `bai_hoc` · `ket_qua_hoat_dong` · `bang_he` · `pham_vi` · `bi_mat` · `duong_dan`

### LOP · BOC TACH

| | |
|---|---|
| **Vai tro** | Khau HEP NHAT cua he: tai lieu -> khai bao kiem dinh duoc. |
| **Nhiem vu** | PDF/anh/video/HTML/ma nguon -> DSL qua `ngu_phap.py`. |
| **Nang luc thuc te** | Boc 389 file ma = **1,01 giay** (bang 0,12 lan mot backtest — khong co gi de toi uu o day). 360/408 co che ra tester trong 4 phut nho gop mot EA. |
| **Van de con ton** | 190/389 file la CHI BAO chua tung vao khau boc. `doc_ma` viet cho Pine nen cham `.mq5` 0 diem. Bo loc 'co dau hieu chua luat' viet cho van xuoi nen cham ma nguon 0 diem. PDF Telegram la ANH, can OCR. |
| **Huong giai** | Sua bo doc theo TUNG LOAI NGUON (Pine / MQL5 / van xuoi / anh), dung mot bo doc cham het. Do bang suat boc tung lan, khong bang so file. |

### LOP · DU LIEU & TAI SAN

| | |
|---|---|
| **Vai tro** | Nap gia tu CHINH cong cu se giao dich, va do dac tinh tung ma. |
| **Nhiem vu** | Nap bar -> kiem chat luong -> ho so tai san (tinh cach, chi phi, mua vu, song). |
| **Nang luc thuc te** | 194 symbol ra ho so trong **5 giay**. 111 bang >=12 nam. Chi phi DO DUOC (spread 0,9384 bps tu 5.747 bar). Hurst du bao duoc (r=-0,567/157 ma). |
| **Van de con ton** | Bar hong x10 o **16/159 ma**. `open` bia truoc 2006 (= close[t-1] o 95-98% ngay). H1 chi co tu 2016, M5 chi 1,4 nam. MT5 don bar NGAY vao khung nho khi thieu du lieu, **khong bao loi**. |
| **Huong giai** | `du_lieu.chan_doan_do_phan_giai()` va `cat_doan_tho` da co — bat buoc chay TRUOC moi backtest, khong phai tuy chon. |

*19 module:* `du_lieu` · `nen` · `dem_nen` · `doi_khung` · `chi_phi` · `tai_tro` · `thang_gia` · `ten_ma` · `ho_so_symbol` · `ho_so_tai_san` · `ho_so_mua_vu` · `ho_so_song` · `ho_so_tuong_quan` · `tinh_cach` · `tinh_cach_chieu` · `quy_luat_song` · `dia` · `gop_wal` · `quy_doi_tham_so`

### LOP · SINH GIA THUYET

| | |
|---|---|
| **Vai tro** | Bon luong sinh: noi sinh, ngoai sinh, suy nguoc dau chan, to hop. |
| **Nhiem vu** | Sinh gia thuyet moi tu lich su ma / he da pass / 400 ho so signal / to hop. |
| **Nang luc thuc te** | 387 gia thuyet dang ky. To hop da cap x da khung x da quan li x da tham so chay duoc. Suy nguoc tu 400 signal ra AUDCAD (13/19 he DCA song). |
| **Van de con ton** | **~19% kho la ban trung** (616/3.236 co che sinh tin hieu y het). Sinh nhanh hon kha nang kiem dinh, nen hang don o cong. |
| **Huong giai** | Khu trung bang **hash chuoi tin hieu** ngay tai cho sinh, truoc khi ghi so. |

*11 module:* `noi_sinh` · `ngoai_sinh` · `suy_nguoc` · `dau_chan` · `luan_dau_chan` · `tin_hieu_mql5` · `to_hop` · `da_thoi_dai` · `gop_lop` · `chuyen_he` · `thu_hoi_thanh_phan`

### LOP · QUAN TRI VI THE

| | |
|---|---|
| **Vai tro** | Ho co che THU HAI — va theo chu du an la ho QUAN TRONG NHAT. |
| **Nhiem vu** | Trailing, dat hue, DCA/luoi, hedge, nhoi lenh, chuoi quan tri, don bay. |
| **Nang luc thuc te** | **Entry tinh SAI van cho 92-97%/nam** khi lop quan tri dung. Trailing: lai holdout **x4,8**, sut giam giam. Luoi AUDCAD do day du ~3,8%/nam holdout. Bigmouse .set that: 62%/nam tren von 33$ cent. |
| **Van de con ton** | Chi **12 module** so voi 19 cua thu thap — dau tu nguoc voi hieu qua. 262 co che trong kho la tin hieu VAO, chi 18 la quan tri. Quan tri can CHO de hoat dong: trailing/dat hue vo hieu tren he thoat nhanh. Nhoi lenh dep trong mau nhung Calmar xau ngoai mau; chi **dat hue** song sot. |
| **Huong giai** | **Truc chinh cua dot 2.** Moi tin hieu vao phai chay qua >=3 luat quan tri truoc khi vao so. Don vi co ban thanh `ho1 x ho2`. |

*12 module:* `pmg` · `pmg_engine` · `pmg_g0` · `pmg_quet` · `quan_tri_dsl` · `quan_tri_nhieu` · `chuoi_quan_tri` · `dap_quan_tri` · `de_quan_tri` · `luoi` · `vao_lenh` · `bien_don_bay`

### LOP · KIEM DINH & CONG

| | |
|---|---|
| **Vai tro** | Noi mot gia thuyet duoc phep doi doi. |
| **Nhiem vu** | Mo phong -> pheu V0..V3 -> cong that -> cham diem tien. |
| **Nang luc thuc te** | MDE do duoc: **30 bps/lenh** la edge nho nhat pheu con thay. Placebo hieu chuan hai chieu (null 0,005 vs nguong). 1.811 dong FDR. Engine mot cua (`mo_phong.py`) khop MT5 tester 100%. |
| **Van de con ton** | **FDR chua tung loai ai (0/703)** — nut that that la MDE. `cong_ra_tien` MO COI. Cong chua ap cho hang trong kho: 169/540 co che khong qua noi. Do dac tung chiem suat FDR khi quen `ghi_so=False`. |
| **Huong giai** | Dao thu tu: **cong ra tien la cong CUOI**, cong that ha xuong thanh NHAN (dung LUAT SO 0). Ap cong cho toan kho, khong chi hang moi. |

*11 module:* `mo_phong` · `sang_loc` · `cong` · `cong_ra_tien` · `cham_diem` · `do_luong` · `do_luc` · `loc_co_che` · `danh_muc` · `nha_may_null` · `suy_giam`

### LOP · MT5 / TESTER

| | |
|---|---|
| **Vai tro** | Do THAT. Quy tac chu du an: MT5 tester TRUOC, Python SAU. |
| **Nhiem vu** | DSL -> MQL5 -> terminal64.exe -> doc bao cao -> danh sach lenh. |
| **Nang luc thuc te** | **8.241 phep thu = 82 giay** khi nhoi het vao mot lan boot. 360/408 co che ra tester trong 4 phut. Doc duoc danh sach lenh that de truy nguoc luat vao. |
| **Van de con ton** | **LAN TESTER = 1 la rang buoc VAT LY** (mot `terminal64.exe`, ghi de cung file `.mq5`/`.ini`) — hai viec cung luc ghi de ket qua nhau va KHONG AI BAO LOI. `Model=1` che ra lai gia khi TP < 2x bien do nen M1 (lech 12 lan). 13/225 qua holdout. |
| **Huong giai** | Giu rang buoc lan=1, xep hang tuan tu. Bat buoc `Model=0/4` cho moi cau hinh TP ngan. Khoa `khoa_tester.py` phai la cua duy nhat. |

### LOP · DIEU HANH & GIAM SAT

| | |
|---|---|
| **Vai tro** | Giu he chay 24/7 va tu thay duoc minh hong cho nao. |
| **Nhiem vu** | Canary, mach dap 10 chang, ngan sach tai nguyen, tran CPU, kill-switch. |
| **Nang luc thuc te** | 5 canary tu kiem. `b mach` do 10 chang duong ong. Ngan sach chia lan (CPU 6 · LLM 3 · MANG 3 · NHE 8 · TESTER 1). `q` chay qwen tu dong, CPU ~85%. |
| **Van de con ton** | **He dang NAM IM** (`DUNG_LAI` bat). 24/7 tung chet vi lease tren Windows — `os.replace` that bai im lang lam so 'thoi gian song' sai. 3 module trong goi van mo coi, trong do co `cong_ra_tien`. |
| **Huong giai** | Noi 3 mo coi, go `DUNG_LAI`, dat `suy_giam` vao nhip ngay de canh bao tu den dien thoai (da bat `inputNeededNotifEnabled`). |

*16 module:* `evo` · `canary` · `mach` · `do_im_lang` · `do_tai_nguyen` · `don_mo_coi` · `han_muc` · `ngan_sach` · `tran_cpu` · `ban_do` · `kien_truc` · `tri_tue` · `muc_tieu` · `vong_day_du` · `day_chuyen` · `day_chuyen_quantlab`

Vai tro tung module rieng le: `KIEN_TRUC.md` (sinh boi `b kien-truc`). Tong 130 module loi.

## 5. He da qua cong — 9 he

| He | CAGR% | mua-giu% | hon% | Sharpe | DD% | Calmar | Lenh | /tuan |
|---|---|---|---|---|---|---|---|---|
| `EURGBP.H4.mat_can_bang_lenh_dong_cua.` | 0.62 | -2.84 | 3.47 | 1.47 | -0.28 | 2.19 | 49 | 0.18 |
| `EURGBP.H4.mat_can_bang_lenh_dong_cua.mac_din` | 0.62 | -2.84 | 3.47 | 1.47 | -0.28 | 2.19 | 49 | 0.18 |
| `XM_US100CASH.D1.mean_reversion_z5.CHIPHI_DO` | 14.05 | 12.22 | 1.83 | 1.16 | -13.51 | 1.04 | 204 | 0.64 |
| `AUDCAD.H4.rsi_dao_chieu.n14_vao30_ra_55` | 4.16 | 0.60 | 3.55 | 1.16 | -3.72 | 1.12 | 62 | 0.22 |
| `US500CASH.D1.mean_reversion_z5.giu500_ra0_ph` | 8.26 | 9.97 | -1.71 | 0.95 | -10.21 | 0.81 | 197 | 0.61 |
| `AUDCAD.H4.ou_quay_ve.n50_z2.5` | 4.46 | 0.60 | 3.86 | 0.95 | -5.50 | 0.81 | 100 | 0.36 |
| `AUDCAD.H4.mat_can_bang_lenh_dong_cua.` | 0.69 | 0.60 | 0.09 | 0.94 | -1.17 | 0.59 | 53 | 0.19 |
| `AUDCAD.H4.mat_can_bang_lenh_dong_cua.mac_din` | 0.69 | 0.60 | 0.09 | 0.94 | -1.17 | 0.59 | 53 | 0.19 |
| `EURGBP.H4.ou_quay_ve.n200_z2.0` | 3.55 | -2.84 | 6.39 | 0.89 | -7.29 | 0.49 | 50 | 0.18 |

**Ba cai bay khi doc bang nay** — deu thay ngay trong chinh bang:

1. **Xep theo Sharpe, khong theo tien** (V1). Dong dau lam ra 0,62%/nam.
2. **Co ban trung** (V2): `mat_can_bang_lenh_dong_cua.` va
   `...mac_dinh` la mot thu hai ten — 4 dong, 2 cap trung khit. **9 dong = 7 he.**
3. **Cot `hon%` duong khong co nghia la ra tien.** EURGBP hon mua-giu 3,47 diem chi vi mua-giu EURGBP la **-2,84%/nam**. Thang mot moc am van la thang.

**Doc lai bang tren theo dung cau hoi TIEN** (*co hon mua-giu o cung rui ro khong*), va no doi hoan ket luan:

- He CAGR cao nhat — `XM_US100CASH.D1.mean_reversion_z5.CHIPHI`, **14.05%/nam** — chi hon mua-giu **1.83 diem** trong khi chiu sut giam **-13.51%**. Mua-giu cung ma da cho 12.22%/nam ma khong phai lam gi.
- `US500CASH.D1.mean_reversion_z5.giu500_ra` **THUA mua-giu 1.71 diem** (8.26% so voi 9.97%) — nhung van nam trong bang 'da qua cong'.
- Sau khi tru ban trung, con **7 he**, va khong he nao vua ra tien that vua cach xa mua-giu.

## 6. Van de va de xuat sua

Xep theo dot. **Dot sau chi co nghia neu dot truoc xong.**

### Dot 1

#### V1. Cong ra tien mo coi, nen bang xep hang xep theo Sharpe

- **Bang chung:** `nhan/cong_ra_tien.py` (*'CONG THU HAI. Hoi co ra tien khong, khong hoi co that khong'*) khong duong chay nao goi toi - `b kien-truc` muc 4.4.
- **Hau qua:** He dung dau bang la EURGBP Sharpe 1,47 nhung **0,62%/nam voi 9 lenh/nam**. Do la mot phep do, khong phai mot he. Trai thang rang buoc 1 cua muc tieu.
- **De xuat:** Noi `cong_ra_tien` vao `bang_he.bang()`. Xep theo **CAGR rong o cung sut giam**; Sharpe xuong cot phu.

#### V2. Ban trung bom bang xep hang va tieu suat FDR

- **Bang chung:** `mat_can_bang_lenh_dong_cua` xuat hien **4 lan** trong 9 he da qua cong, thanh 2 cap trung khit tung chu so. Dau bang 592 he holdout: `ns_nen_rau_tren` va `ns_nen_sao_bang` cho 6 con so y het, chiem 16/18 dong dau. Da do truoc do: 616/3.236 co che sinh tin hieu y het nhau.
- **Hau qua:** **9 he that ra la 7.** Hai ban sao trong nhu hai xac nhan doc lap. Moi ban sao con tieu mot suat FDR, tuc vua BOM xep hang vua SIET cong.
- **De xuat:** Khu trung bang **hash cua CHUOI TIN HIEU**, khong phai ten. Chay truoc moi thu tieu suat FDR. Chay lai bang sau khi khu.

### Dot 2

#### V3. Dau tu nguoc voi hieu qua do duoc

- **Bang chung:** Lop THU THAP 19 module -> 12.078 tai lieu -> **18 mau chien luoc (0,15%)**. Do doc lap: kho x6 ma ung vien cham cong van 21. Lop QUAN TRI VI THE chi 12 module, trong khi entry SAI + quan tri dung = 92-97%/nam.
- **Hau qua:** Cho ton cong nhat la cho cho it tien nhat. `tru/seeker.py` mot minh 2.647 dong - lon nhat he.
- **De xuat:** **Dong bang quy mo thu thap.** Chuyen cong sang quan tri vi the: moi tin hieu vao phai chay qua >=3 luat quan tri truoc khi vao so.

#### V7. Thu TUNG ra tien nam ngoai duong chay

- **Bang chung:** Sonic R H4 US500 (TP5%/SL1%, L=3 -> **26%/nam**, Calmar tang theo don bay), luoi Bigmouse tren AUDCAD (**62%/nam** tren von 33$ cent), trailing (lai holdout **x4,8**) - khong cai nao co trong bang 9 he.
- **Hau qua:** He dang do cac thu yeu hon trong khi thu manh hon nam ngoai so.
- **De xuat:** Keo ca ba vao `b he` do bang **cung don vi** voi phan con lai. Neu chung khong tai lap duoc thi biet som van hon.

#### V8. 84 file no o goc lab + 25 file khong khai vai tro

- **Bang chung:** 362 file o goc = 147 test (dung cho) + 131 script `_*.py` chay tay (dung ban chat) + **84 file no that**. 25 file khong co docstring nen khong vao duoc ban do vai tro nao.
- **Hau qua:** Nguoi moi vao khong biet cai nao dang chay. Da xay lai thu da co 3 lan trong mot phien vi ly do nay.
- **De xuat:** 84 file: len `nhan/`, hoac doi ten `_*.py`, hoac xoa. 25 file: them mot dong docstring. Ca hai deu do duoc bang `b kien-truc`.

### Dot 3

#### V4. Don vi co ban dang la co che DON, trong khi CAP moi song

- **Bang chung:** He don 822 -> 40 khi ra holdout. Cap giu hang **39/45**. Ghep chan am voi chan duong: 6,14% -> 20,25%/nam o **cung sut giam**. Nguoc chieu cho tuong quan am o 93-94% cap.
- **Hau qua:** Pheu dang loc va xep hang tung co che roi moi nghi den ghep - tuc loc bo chan am truoc khi biet no ghep duoc voi gi.
- **De xuat:** Don vi co ban la **`ho1 x ho2`** (tin hieu vao x luat quan tri). Cong T3 khong nhan co che don. `danh_muc.py` thanh cong bat buoc truoc khi ra that.

### Dot 4

#### V5. So do noi bon tru, ma nguon co hai

- **Bang chung:** BANKER 550 dong goi **1** module nhan (`so`); FINDER 442 dong goi **2**. SEEKER goi 17, QUANTLAB goi 18.
- **Hau qua:** Bao cao va ke hoach coi nhu co 4-5 tru dang chay, thuc te la 2 tru + 3 vo. Moi uoc luong tien do deu lech theo.
- **De xuat:** Goi dung ten: BANKER/FINDER la **chua xay**, khong phai 'dang chay yeu'. Chu du an da chot: xong ba module that truoc. Giu nguyen thu tu do.

#### V6. Khong co tang SAN PHAM - he dang nam im

- **Bang chung:** Tu 'he qua cong' den 'tien vao tai khoan' chi co `chay_that.py` + `so_lenh.py`. Co `DUNG_LAI` dang bat: he **nam im**. `nao.db` 1,6 GB.
- **Hau qua:** 524 file phuc vu viec TIM, gan nhu khong co gi phuc vu viec GIU cho cai da tim duoc chay va sinh tien.
- **De xuat:** EA nhieu slot (da co: moi slot mot magic, `lot=0` tat slot) -> VPS -> `so_lenh` paper -> `suy_giam` canh bao ngay. Gop WAL, dong bang kho.

**Tieu chi dung tung dot:**

1. `b he` tra loi duoc *'he nao ra tien nhat tren moi don vi sut giam'*, va cau tra loi khong phai mot ban trung.
2. Co >=3 he CAGR rong > 10%/nam o cung sut giam voi mua-giu, ca ba co chan quan tri.
3. Mot danh muc thang mua-giu o cung sut giam, **tren nua holdout**.
4. Tien that vao tai khoan that, va khong can ai ngoi may.

## 7. Luat doc ket qua — DOC TRUOC KHI KHUYEN BAT KY DIEU GI

Moi dong duoi day la mot loi DA SAP THAT trong du an nay, khong phai ly thuyet.

- **Ket luan AM phai phan biet voi CHUA DO DUOC.** Ma thoat != 0, thieu file ra,
  file ra cu hon luc bat dau, bang co cot so dung im -> deu la `CHUA_DO_DUOC`.
- **`Model=1` cua MT5 che ra lai gia** khi TP < 2x bien do nen M1: do duoc
  +1.161% (Model=1) vs -100,7% (tick that) tren cung cau hinh. Lech 12 lan.
- **Placebo phai hoan vi CHUOI VI THE**, khong phai chuoi lai/lo. Hoan vi lai/lo
  giu nguyen phan phoi nen luon ra ~50% va "ket luan" rang moi he deu truot.
- **So cuc dai phai so cung co mau.** "Tot nhat trong N" vs ban gia le thoi p sai
  24 lan, lat ket qua DAT thanh AM.
- **Don bay gop bang LOG la sai**: L=3 tren 98 nam ra x76.289.488 thay vi x2.406.
  Va tran lai suat o moi don bay la `0,5*S^2` - Sharpe phai tinh tren loi suat
  SO HOC.
- **Mua-giu la moc bat buoc trong moi bang**, va phai co CA HAI moc: mua-giu CFD
  (co phi qua dem) va mua-giu chi so (khong phi) - hai ket luan khac han nhau.
- **Phi qua dem dat hon spread**: 1,56 bps/dem so voi spread 0,98 bps. Chan BAN
  duoc TRA +0,18 bps/dem.
- **Bar D1 cua CFD khong phai bar phien** (om ~23 gio, bien do rong hon 1,39 lan).
- **Do sau du lieu phai kiem truoc moi backtest**: MT5 don bar NGAY vao khung nho
  khi thieu du lieu, khong bao loi. Dau hieu nhan ra la so bar/nam.
- **Exness cat lich su tu 2022-08** cho 24/25 symbol; XM tra H1 chi bang
  `copy_rates_from_pos`, va bar D1 cua XM co `spread = 0`.
- **Sharpe cao khong phai tien.** Xem V1: Sharpe 1,47 = 0,62%/nam.

## 8. Thuat ngu

- **ho 1** — co che **tin hieu VAO** (~262). DSL `vao`/`ra` trong `nhan/ngu_phap.py`.
- **ho 2** — co che **QUAN TRI VI THE** (~18). Ghep duoc voi moi he.
- **ho 3** — **PMG** — quan li lenh KHONG co tin hieu vao (luoi ro).
- **cong that** — placebo + MDE + FDR. Theo LUAT SO 0 day chi la **nhan**.
- **cong ra tien** — hoi 'co thang mua-giu o cung rui ro khong'. Cong quyet dinh.
- **MDE** — edge nho nhat ma he con nhin thay duoc (~30 bps/lenh).
- **placebo** — hoan vi **chuoi vi the** de xem edge co that khong.
- **holdout** — nua du lieu chua bao gio duoc cham khi thiet ke.
- **pheu V0-V3** — van tay -> re -> kinh te -> phan chung. `nhan/sang_loc.py`.
- **mua-giu** — moc bat buoc. Phai co ca ban CFD (co phi) va ban chi so.

## 9. So ma nguon

| Muc | So |
|---|---|
| File `.py` | 525 |
| Tren duong chay | 196 |
| Module loi `nhan/` | 130 |
| File goc `lab/` | 362 (147 test · 131 script chay tay · **84 no that**) |
| File > 600 dong | 33 |
| Module trong goi van mo coi | 3 |
| `nao.db` | 1.6 GB |
| Van de con mo trong so | 23 |

## 10. Nang luc cong cu cua phien lam viec

Muc nay cho nguoi doc ngoai biet **phien Claude Code chay du an nay lam gi duoc**, de dung giao viec ma cong cu khong lam noi — hoac nguoc lai, dung de xuat lam tay thu da tu dong.

**8 plugin dang bat:**

- `double-shot-latte@superpowers-marketplace`
- `episodic-memory@superpowers-marketplace`
- `feature-dev@claude-code-plugins`
- `financial-analysis@claude-for-financial-services`
- `hookify@claude-code-plugins`
- `security-guidance@claude-code-plugins`
- `superpowers@superpowers-marketplace`
- `trading-skills@agiprolabs-claude-trading-skills`

**~97 Agent Skill** nap tu cac plugin tren. Nhom dung cho du an nay: backtrader · vectorbt · walk-forward-validation · cointegration-analysis · correlation-analysis · portfolio-analytics · regime-detection · exit-strategies · position-sizing · kelly-criterion · slippage-modeling · volatility-modeling · ta-lib · pandas-ta.

41 skill crypto/DeFi/thue duoc dat `user-invocable-only`: khong hien trong danh sach model doc moi luot (de khoi ton ngu canh) nhung van goi duoc bang `/ten-skill`.

**Tu chay giua cac phien** — ba tang, khong can nguoi go:

1. `Stop` hook ghi ban giao song + `double-shot-latte` tu cham *co nen lam tiep khong* thay vi dung lai hoi.
2. `SessionStart` hook nap `BAN_GIAO.py` (trang thai he) roi in `TIEP_TUC_MAI.md` (viec con ton) — phien sau mo ra la biet viec.
3. `autoContinueAtUsageLimit`: cham tran han muc thi doi reset roi chay tiep.

**Ba lenh so do** (chay lai truoc khi tin bat ky so nao): `b ban-do` (duong chay) · `b kien-truc` (tang + vai tro) · `b ho-so` (file nay).

## 11. Ha tang ky thuat

*Do luc sinh, CHI DOC. Muc nao khong do duoc thi ghi ro la chua do duoc — khong suy dien, khong chep tu bao cao cu.*

### 11.1 May

| | |
|---|---|
| OS | Windows 10.0.19045 |
| CPU | Intel64 Family 6 Model 79 Stepping 1, GenuineIntel — **10 nhan / 20 luong** |
| RAM | 34.3 GB (trong 28.2 GB luc do) |
| Dia | C:\ 128GB (trong 26.9GB) · F:\ 128GB (trong 20.1GB) |
| GPU | **khong dung** — khong thu vien nao trong he goi CUDA/GPU |

### 11.2 Python va engine

| | |
|---|---|
| Phien ban | 3.14.7 @ C:\Python314\python.exe |
| Moi truong | KHONG — python he thong |
| Thu vien | numpy 2.5.1 · pandas 3.0.5 · scipy 1.18.0 · scikit-learn 1.9.0 · statsmodels — · numba — · matplotlib 3.11.1 · MetaTrader5 5.0.6090 · pyarrow 25.0.1 · polars — · requests 2.34.2 · httpx 0.28.1 · beautifulsoup4 4.15.0 · lxml — · playwright 1.62.0 · selenium — · pdfplumber 0.11.10 · PyMuPDF 1.28.2 · pillow 12.3.0 · pytest 9.1.1 · pytest-xdist 3.8.0 · openai 3.8.0 · psutil 7.2.2 · joblib 1.5.3 · tqdm 4.70.0 |
| `mo_phong.py` | 325 dong · **1 vong lap** · 55 dong vector hoa (`np.`/`.values`) — engine **vector hoa**, khong phai vong lap tung bar |
| numba | **KHONG** — chua ai dung JIT |
| song song | **45 file** dung `multiprocessing`/`concurrent.futures` |

### 11.3 Du lieu gia

- **Noi luu:** `F:\TheBrain_luu\data` — KHONG nam trong repo (o o dia khac)
- **Quy mo:** 270 file · **0.811 GB**
- **Dinh dang:** .parquet 269 · .json 1
- **Cach nap:** `nhan/du_lieu.py` -> `kho()` chon ban theo **do phu** (khong theo byte), roi `kiem()` chay 5 bay chat luong truoc khi tra ve.

### 11.4 `nao.db`

| | |
|---|---|
| Loai | SQLite, journal **wal**, `busy_timeout` 5000 ms |
| Kich thuoc | 1595.4 MB · WAL 0.0 MB |
| Trang | 389491 x 4096 B = 1.60 GB |
| Tong dong | **224,904** tren 26 bang |

| Trang TRONG | 231700 trang = 0.95 GB (**59.5% DB**), thu hoi duoc bang VACUUM |
| Du lieu THAT | 0.65 GB |

**Da DO, khong doan:** 1595.4 MB cho **224,904 dong**, trong do 231700 trang = 0.95 GB (**59.5% DB**), thu hoi duoc bang VACUUM. Phan con lai (0.65 GB) la du lieu that — chu yeu toan van tai lieu o `noi_dung`/`artifact`. VACUUM can cho trong bang kich thuoc DB tren CUNG o.

| Bang | Dong | | Bang | Dong |
|---|---|---|---|---|
| `vi_mo` | 113,419 | | `thanh_phan` | 285 |
| `chi_so_vh` | 51,030 | | `bai_hoc` | 238 |
| `su_kien` | 18,808 | | `anh_chup` | 181 |
| `tai_lieu` | 12,078 | | `van_de` | 134 |
| `artifact` | 10,202 | | `nguon` | 98 |
| `noi_dung` | 8,055 | | `khang_dinh` | 60 |
| `lenh_paper` | 3,573 | | `de_xuat` | 59 |
| `viec` | 2,006 | | `vi_mo_seri` | 30 |
| `fdr` | 1,811 | | `sqlite_sequence` | 16 |
| `ket_qua` | 1,284 | | `han_muc` | 11 |
| `candidate_queue` | 705 | | `theo_doi` | 9 |
| `tu_khoa` | 417 | | `nhip` | 7 |
| `gia_thuyet` | 387 | | `he_chay` | 1 |

**Ghi nhieu nhat:** `vi_mo` va `chi_so_vh` (tru BANKER do vi mo lien tuc) chiem 73% tong so dong.

**Ai ghi dong thoi:** `dieu_phoi.py` (5 tru, ThreadPool) · `day_viec.py` · `qwen/chay.py` · moi script chay tay goi `nhan/so.py`. WAL cho phep **nhieu doc + mot ghi**; xung dot ghi doi `busy_timeout` 5000 ms roi nem `database is locked`.

Loi `database is locked` **da tung gap** — day la ly do co `nhan/gop_wal.py` va lenh `b don-dia`: WAL tung phinh 1,4 GB va lam ba me boc bao XONG rc=0 ma kho khong doi.

### 11.5 LLM

- **Kieu:** API tu xa — `https://api.ai-box.vn/v1`
- **Model:** `qwen3.7-flash` (du phong `qwen3.6-flash`). **Khong chay local**, khong tai trong so ve may.
- **Toc do token/giay:** chua do duoc — he chi ghi *ban/giay* o muc day chuyen (do 13/09: 6 luong 0,071 ban/giay · 24 luong 0,101).
- **Lan goi/gio:** chua do duoc — khong co bo dem goi LLM theo gio.
- Muc tieu CPU cua `q`: 60.0% CA MAY.

### 11.6 Dieu phoi

- `dieu_phoi.py` — supervisor 24/7, **`ThreadPoolExecutor`** chay 5 tru, nhip tim ghi file moi 5 giay; hai nhip giao nhau = supervisor chet.
- `day_viec.py` — hang doi viec **tuan tu**, moi viec mot `subprocess`, co han gio va `taskkill /F /T` khi qua han.
- `qwen/dieu_toc.py` — AIMD giu CPU ca may quanh muc tieu, do that moi 5 giay.
- **Ngan sach lan** (`nhan/ngan_sach.py`): CPU giao cho dieu_toc · **LLM 8 slot** · MANG · NHE · **TESTER 1**.
- **Khoa tester** (`nhan/khoa_tester.py`): mot file khoa `config/khoa_tester.json` giu `{pid, viec, luc}`, tu thu hoi khoa mo coi, TTL 45 phut. Trang thai luc sinh: khong ai giu

### 11.7 MT5

- **6 ban cai** tren may: `FXCE MT5 Terminal` · `MetaTrader 5` · `MetaTrader 5 EXNESS` · `Ultima Markets MT5 Terminal` · `XM Global MT5` · `XM MT5`
- **8 thu muc du lieu terminal** trong `AppData/Roaming/MetaQuotes/Terminal`.
- Ma nguon hien **chi tro toi MOT** exe: `C:\Program Files\MetaTrader 5\terminal64.exe`
- Portable: **khong** — chay theo thu muc du lieu mac dinh cua tung ban cai.
- Tai khoan: khai trong `config/` va doc qua `nhan/bi_mat.py` (mot cua doc khoa). **Khong ghi so tai khoan/mat khau o day.**

**Danh gia: co chay duoc 2+ terminal portable song song khong?**

*May thi duoc* — da co 6 ban cai va 8 thu muc du lieu rieng. *Ma nguon thi chua*, va tro ngai la **bon cho cu the**, khong phai mot gioi han vat ly:

1. `chay_tester_kho.py` ghi de **cung mot** `MQL5/Experts/<TEN_EA>.mq5`, cung mot `.ini`, cung mot `.xml` trong MOT thu muc du lieu co dinh (`XM_DATA`). Hai viec cung luc ghi de ket qua cua nhau **va khong ai bao loi**.
2. `nhan/duong_dan.mt5_exe` tra **mot** duong dan, khong nhan tham so.
3. `nhan/khoa_tester.py` la khoa **toan cuc mot slot** — no dung de BAO VE cai (1), nen go khoa ma khong sua (1) la hong ngay.
4. `nhan/ngan_sach.py` dat `TESTER = 1` va goi do la rang buoc VAT LY. Do la mo ta **dung voi ma nguon hien tai**, khong dung voi cai may lam duoc.

=> Muon song song thi phai tham so hoa ca bon: `(exe, thu_muc_du_lieu, ten_ea, ten_ini)` thanh mot 'slot tester', doi khoa thanh khoa **theo slot**, va nang `TESTER` len bang so slot. Day la viec **sua logic** nen muc nay chi neu, khong lam.

### 11.8 Git va test

- Nhanh `master` · **346 commit** · 30 file dang ban · KHONG CO remote
- `git worktree`: **dung duoc** (repo binh thuong, 1 worktree dang co). Day la duong cho nhieu phien Claude Code lam viec tach nhau — xem 11.10.
- **Bo test:** 2026-09-16 · `pytest -q -n 8 --dist loadfile` · KHONG HOAN TAT. Chay ~10 phut, tien den 98% roi **gw5 node down: Not properly terminated**, khong in duoc dong tong ket nen KHONG CO so pass/fail. Thay 2 dau `F` trong tien trinh. Day dung la kieu hong da ghi truoc: `b test` chet giua chung tren may dang nghet -> dung `b test-me` (chia me, nhieu tien trinh pytest ngan). Tap con chay rieng thi SACH: `-k "ban_do or bang_he"` = 35 passed, 1 skipped, 68s.

### 11.9 Live

- `DUNG_LAI` dang **BAT** (noi dung: `dung`)
- **Ly do:** file chi chua mot tu `dung`, **khong ghi ly do**. Tim trong ma nguon: `b dung` chi ghi co, `dieu_phoi` doc co roi dung sau khi tru dang chay xong luot. Ly do THAT **chua do duoc tu file** — phai hoi nguoi dat co.
- He dang ky chay that: **10** · dang bat: ['audcad_c1', 'audcad_c2', 'audcad_c3', 'audcad_c4', 'audcad_c5', 'audcad_c6', 'audcad_c7', 'audcad_c8'] · duoc phep tien that: (khong cai nao)
- EA cho live: `nhan/dich_mq5*.py` sinh EA nhieu slot (moi slot mot `magic`, `lot=0` tat slot). VPS: **chua co** — `nhan/san_sang_vps.py` moi la cong kiem, chua co may.

### 11.10 Rui ro khi chay SONG SONG nhieu phien Claude Code

Tai nguyen dung chung, xep theo **do nguy hiem khi va cham**:

| Tai nguyen | Va cham the nao | Co bao loi khong |
|---|---|---|
| **MT5 tester** (`.mq5`/`.ini`/`.xml` co dinh + mot `terminal64.exe`) | ghi de ket qua cua nhau; bang so doc **y het mot ket qua that** | **KHONG** — nguy hiem nhat |
| **`nao.db`** (WAL, mot ghi) | ghi dong thoi -> doi `busy_timeout` roi `database is locked` | CO |
| **`config/*.json`** (`he_chay_that`, `day_viec`, `khoa_tester`...) | doc-sua-ghi khong nguyen tu -> mat thay doi cua phien kia | **KHONG** |
| **File sinh ra o goc `lab/`** (`BAN_DO.md`, `KIEN_TRUC.md`, file nay) | ghi de lan nhau | KHONG, nhung vo hai |
| **git index** (`b luu`, commit) | hai phien commit cung luc -> `index.lock` | CO |
| **Cong CDP 9224** (Chrome cua Seeker) | hai phien cung dieu khien mot trinh duyet | mot phan |
| **Kho gia tren o F:** | doc song song thi an toan; ghi/fetch cung luc thi khong | KHONG |
| **Lan LLM/CPU** (`ngan_sach`) | moi phien tu dem lan cua rieng no -> vuot tran CPU that | KHONG |

**Cach an toan nhat dang co:** `git worktree` cho moi phien (11.8) — tach file va git index. Nhung no **khong** tach `nao.db`, MT5, hay cong CDP: ba thu do van la mot. Nen quy tac thuc dung la **mot phien duoc dung tester va ghi so; cac phien khac chi doc**.

### 11.11 Nut that thong luong — xep hang

| # | Nut that | So do duoc | Vi sao no la tran |
|---|---|---|---|
| 1 | **MT5 tester, 1 lan** | `TESTER = 1`; 8.241 phep thu = 82 giay khi nhoi mot lan boot, nhung hai viec khong the chay cung luc | Moi ket luan cuoi cung phai qua tester. Ca 10 nhan / 20 luong CPU khong giup duoc gi o khau nay |
| 2 | **Suat boc tai lieu** | 12.078 tai lieu -> 18 mau (**0,15%%**); LLM dien 48 khai bao, tham dinh bac 41, rong **3** | Kho x6 ma ung vien cham cong van 21 — them dau vao khong di qua duoc khau nay |
| 3 | **Dia** | C: con 26.9GB | `nao.db` 1595.4 MB cho 224,904 dong; WAL tung phinh 1,4 GB va lam ba me boc bao XONG ma kho khong doi |
| 4 | **Mang / nguon bi chan** | mql5.com cam theo IP sau ~50-150 luot; phai di 8 giay/luot + doi IP | Chang [1] cua so do bi cat nhip, khong phai vi may yeu |
| 5 | **Mot luong ghi `nao.db`** | SQLite WAL: nhieu doc, **mot ghi**, `busy_timeout` 5000 ms | Moi tru + qwen + script tay deu ghi chung mot so |

**Doc bang nay cung muc 6:** nut 1 va 5 la ha tang (sua duoc bang ky thuat); nut 2 la **van de V3** (sua bang cach doi uu tien, khong phai bang may manh hon).

---

*Chay lai `b ho-so` truoc khi dung file nay de ra quyet dinh — so lieu doi moi phien.*
