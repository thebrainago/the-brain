# CLAUDE.md — lab/ (THE BRAIN)

File nay tu nap moi khi doc file trong `lab/`. Muc dich: dung mat 15 phut dau
phien de tim lai luat. Ban day du van o `../AGENTS.md`.

## Vao phien / ket phien
```
b vao              trang thai song + ban giao hom qua  (~2 giay)
b ket "tom tat"    chot ngay: git commit + sinh TIEP_TUC_MAI.md moi
b                  menu day du
```
Python **duy nhat**: `C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe`.
Khong dung `WindowsApps\python.exe`. `b.cmd` da tro dung san.

## Bo cuc (30/08/2026 — da gop mot dau moi)
```
Research SP500/          <- kho git chinh (mo 30/08)
  lab/     nhan/  hat nhan dung chung: so, du_lieu, chi_phi, mo_phong, cong, mau...
           tru/   5 tru: seeker, quantlab, nghi, banker, evolution
           dieu_phoi.py  MOT supervisor, nao.db MOT so cai
  ds/      kho DeepSeek — GIU GIT RIENG (56 commit, 799 test).
           datalake, primitives, probes, schemas (card), gates G0-G7, mimic
  data/    parquet gia (ngoai git)
```
`ds/` truoc 30/08 nam o `Downloads/Promt cho DS`. Da chuyen vao. Duong dan cung
trong `ds/browser/*` va `lab/BROWSER_SCAN*.bat` da sua theo.

## Luat khong duoc pha (rut gon — ban day du: ../AGENTS.md muc 3)
- **Canary truoc, ket qua sau.** Canary hong -> dung tru, khong tinh p-value nao.
- **Chi phi phai DO DUOC.** `cp.do_tin` la `KHAI` thi **khong bao gio PASS**.
- **Pre-registration.** Phai co `plan_hash` truoc khi cham holdout. Doi ke hoach
  sau khi cham du lieu = gia thuyet KHAC.
- **Xac nhan la HAM Y NGUYEN.** Chay lai cung gia thuyet = nhin lai cung holdout.
- **`t_alpha > 5` = nghi nhin truoc** cho toi khi chung minh nguoc lai.
- **Nhieu PASS trong mot ngay la tin hieu HONG**, khong phai tin vui.
- **Hieu chuan cong phai HAI CHIEU**: `null_ty_le_lot` + `thu_luc_cong`. Mot cong
  tu choi TAT CA cho so lieu y het mot cong tot.
- **Kien thuc moi chi vao he qua `nhan/ngu_phap.py`** — khong `exec` ma LLM sinh.
- **Ket luan am tinh phai kem MDE** (`do_luc.luc_hai_chang` / `gop_lop.mde_gop`).
- **Do dac khong duoc chiem suat FDR**: truyen `ghi_so=False`.

## Bay da sap that — kiem TRUOC khi tin so
- `kho()` chon ban theo **do phu**, khong theo byte. Them file vao `data/` co the
  doi ban duoc chon cua ca mot ma.
- **Open bia**: nguong theo NGUON (`san` 0,60 / `ngoai` 0,20), khong theo ten ma.
- **Spread do tu bar D1 la chan tren** — H1 thap hon ~39% (do that tren EURCAD).
- **Model=1 cua MT5 noi doi** khi TP < 2x bien do nen M1. Phai chay Model=0/4.
- `swap_mode` co ba nhom cong thuc; mode 9 khong co trong API MT5 nhung FXCE tra ve.
- Tra cuu phi theo ten symbol tho -> lang le lay phi `MetaQuotes-Demo`.
- **Chuoi LAI TAP do phan giai** (sua 01/09): `khung_that()` lay TRUNG VI ca chuoi
  nen doan dau la bar NGAY deo nhan bar gio van qua cua. Dinh 5 ma: EURUSD/USDJPY
  1971-1998, GBPUSD 1993-1998, US500CASH 2011-2015, XAUUSDM 2014-2016. Da chan
  bang `du_lieu.cat_doan_tho`; quet lai bang `du_lieu.chan_doan_do_phan_giai()`.
- **Bar D1 cua CFD KHONG phai bar phien.** D1 cua CFD chi so om ~23 gio, bien do
  rong hon bien do phien tien mat My **1,39 lan** (do tren US500CASH 2018-2026),
  va IBS tinh tren hai bar do chi tuong quan 0,866 — 98 ngay kich hoat IBS<0,2
  theo phien nhung khong theo D1, va 91 ngay nguoc lai. Dung `du_lieu.nap_phien`
  khi co che noi ve PHIEN chu khong ve ngay lich.

## Day chuyen theo MUC TIEU (03/09/2026 - moi)
```
b mang             kiem duong ra + bat Cloudflare WARP neu can
b day-chuyen [MA]  ca day chuyen: san -> doc song song -> boc co che
b san-nguon [MA]   LUONG 1: theo tai san + theo TEN HE THONG + MQL5 .mq5
b boc [N] [M]      LUONG 2: doc song song roi boc bang LLM
b noi-sinh [MA] [KHUNG]   LUONG 3: sinh co che tu chinh lich su cua ma
b pheu             do TUNG CHANG cua pheu nguon (tai lieu -> co che)
```
`nhan/day_chuyen.py` noi ca ba luong. Ngoai sinh: `nhan/ngoai_sinh.chuyen`
(he DA PASS -> tai san moi, **giu TY LE KICH HOAT chu khong giu con so**).

## Bay them - phien 03/09/2026 (tat ca deu tung bao so lieu BINH THUONG)
- **`don_bay` gop bang LOG** cho `(S_T/S_0)^L`: mat luc can bien dong va mat ca
  kha nang chay tai khoan. L=3 tren 98 nam ra x76.289.488 thay vi x2.406.
  Dung `gop="so_hoc"` (mac dinh `tu_dong` da lo khi don_bay != 1).
- **Sharpe cho Kelly phai tinh tren loi suat SO HOC**, khong phai log — dung
  log ha tran `0,5*S^2` di 27%.
- **CO TUC**: CFD chi so tra dieu chinh co tuc rieng; chuoi backtest la chi so
  GIA. Chu du an xac nhan XM **khong tra** -> dung `co_tuc=False`. `nhan/tai_tro.py`
  do duoc suat that (1990s 2,58% ... 2026 1,24%).
- **"Em a" la bay**: 3 chi so bien dong thap nhat thi 2 cai AM sau phi. UK100
  mua-giu **-2,77 %/nam** suot 15 nam. Xep chi so theo CAGR RONG, khong theo vol.
- **Closure DSL tung nuot tham so** (`**_`) -> 152/170 mau "diec", va bo do on
  dinh cham chung la CAO NGUYEN hoan hao. Nay `do_hinh_dang` tu choi khi
  `so_o_khac_nhau < 2`.
- **Co che theo GIO tren khung khong co gio** -> tin hieu hang so. `mau._phai_co_gio`
  va `ngu_phap` chi_bao 'gio' nay NEM LOI thay vi tra 0.
- **Tran phoi nhiem cua bo sinh** tung la 0,60 -> loai sach he XU HUONG. Nay 0,95.
  Cai chan "mua-giu doi ten" la phep so O CUNG RUI RO, khong phai tran phoi nhiem.
- **Bo loc "co dau hieu chua luat"** viet cho VAN XUOI thi cham ma nguon 0 diem.
- **Loi nhac cua bo boc** tung kem "KHONG de xuat lai, ke ca doi ten" + danh sach
  170 co che -> LLM tra ve 0. Bo loc phai o CONG, khong o loi nhac.
- **`Accept-Encoding: br` khi khong co brotli**: HTTP 200 nhung `r.text` RAC.
  Cung mot trang: 21.245 ky tu/0 link vs 82.347 ky tu/40 link.
- **DNS bi dau doc** tren mang nay (mql5.com): ba trieu chung khac nhau
  (RemoteDisconnected / ERR_HTTP2_PROTOCOL_ERROR / HTTP 000) cua MOT nguyen nhan.
  **Bat WARP la thong.** Du phong: `nhan/dns_vuot.py`.
- **Lam "giong nguoi" qua tay thi phan tac dung**: `requests.get` tran 4/4 = 200;
  phien giu cookie + Referer 4/4 = 403.
- **Tai HONG bi dich thanh "het trang"** -> con tro bien gioi MQL5 bi cat vinh
  vien xuong trang 3. Dung `seeker.lay_that_bai_vi_mang()`.
- **`ma_nguon.thu_thap` khong he phan trang** truoc 03/09 -> 4 vong lien tiep
  tai lai dung 60 file cu. Nay co con tro `config/ma_nguon_con_tro.json`.
- **`thu_thap` ghi vao bang `artifact`**, KHONG vao `tai_lieu`. Dem nham bang
  thi tuong nhu that bai.

## Sua code
- **Co git roi**: sua thang, `b luu "..."` de chot, `b lui <file>` de tra lai.
  **Dung copy tay vao `backups/`** (da phinh 247 MB) — do la thoi quen truoc git.
- `b test` = 8 tien trinh, ~2,5 phut / 321 test. `b test1` khi nghi song song sai.
- `b tim <tu>` tim trong ma nguon, khong loi nhoi ket qua tu data/reports.

## QUY TRINH QUANTLAB CHUAN (chot 05/09/2026 - dung lai, dung tu che)

Chu du an: *"Quy trinh cang ro rang va chuan hoa bao nhieu thi cang nhanh va
hieu qua bay nhieu"*. Nam buoc, chay NOI TIEP:

```
1 BOC    nhan/quan_tri.boc_kho()        389 file ma  -> spec co che (1,0 giay)
2 LOC    nhan/quan_tri.loc()            giu cai DUNG LAI DUOC (ghep moi he)
3 HO SO  nhan/ho_so_symbol.quet()       194 symbol -> tinh cach+bien do+chi phi (5s)
4 GHEP   ho_so_symbol.chon_ung_vien()   co gia thuyet -> nen thu tren ma nao
5 CHAM   nhan/cham_diem.cham()          TIEN + RUI RO, khong Sharpe/p-value
```
Goi ca bon buoc dau: `nhan/day_chuyen_quantlab.chay(kieu='hoi_quy')` — **6 giay**.

**KHONG song song hoa buoc 1-3.** Do 05/09: boc tach 389 file = **1,01 giay**,
ho so 194 symbol = 92 giay 1 luong, con MOT backtest luoi M5 = **8,17 giay**.
Boc tach ton bang 0,12 lan mot backtest — khong co gi de toi uu. Chay noi tiep
roi de backtest chiem may.

**CHUA 4 NHAN.** Khi chay 16 tien trinh quet, `mt5.initialize()` het 60 giay va
bao IPC timeout — dung thu dang chan `PASS`. Mac dinh `luong = so_nhan - 4`.

### Hai HO co che, khong duoc tron
- `ho 1` **tin hieu VAO** (262) — `nhan/ngu_phap.py`, DSL `vao`/`ra`.
- `ho 2` **QUAN TRI VI THE** (18) — `nhan/quan_tri.py`, chay bang `mo_phong_v2.py`.
  Ho 2 **ghep duoc voi moi he**, va do 05/09 no QUAN TRONG HON ho 1 voi lop luoi:
  entry co tinh SAI van cho 92-97%/nam.

### Bo loc co che (buoc 2) hoi gi
KHONG hoi "co lai khong" (do la viec `cham_diem`). Hoi **"co dung lai duoc khong"**:
>=2 nut van · khong trung · co tham so SO · co it nhat mot nut QUAN TRI.

### Bang diem (buoc 5) chi co sau con so
`lai_pct_nam` tren VON PHAI BO RA · `sut_giam_pct` · `von_can` (+ ban CENT chia 100)
· `hoi_von_thang` · `so_lenh_nam` · `nguy_co_chay`. Ba muc: **CHAY_DUOC / MONG / BO**.
Sharpe, Calmar, p-value, FDR **khong o day** — chung thuoc `nhan/cong.py`.
Mot cau hinh CHAY_DUOC ma chua qua cong that thi goi dung ten: *canh bac co ky
vong duong do duoc*, chua phai phat hien (`da_qua_cong_that`).

### Chon ung vien phai LOC CHI PHI TRUOC
Xep thuan theo Hurst thi GBPPLN (**98,5 bps**) va GBPZAR (20,8 bps) len dau —
nhung cap phi giet moi luoi. `TRAN_SPREAD_BPS = 8`, va `vong_quay_can=` neu he
quay nhieu.
