# HUONG DAN CHO CLAUDE CODE — lab/ (THE BRAIN)

## LUAT SO 0 — DOI CHIEU SO DO TRUOC MOI PHIEN (chot 12/09/2026)

**Nguon duy nhat cua CAU TRUC he thong la `Desktop/hethong.txt`**, ban chep dong bo
o `lab/SO_DO_HE_THONG.txt`. Moi phien PHAI mo no ra doi chieu truoc khi lam gi.

Vi sao co luat nay: phien 12/09 toi lam ca ngay theo `KE_HOACH_XAY.md` va so
`van_de` cua lab, nen xep ca BANKER va NGHI vao "viec phai hoan thien" - hai thu
**khong co trong so do**. Chu du an phai hoi "lam gi co banker nao?" toi moi biet.

So do that: **BA module** - SEEKER (phe u + bo loc) · QUANTLAB (tong quan tai san ·
**co che quan li** · chien luoc · noi sinh · luong uu tien) · EVO (+ FINDER).

**BO SUNG 13/09/2026 (chu du an duyet):** them **HEPHAESTUS** (`nhan/hephaestus.py`,
`b hepha`) - module DE CO CHE. Ranh gioi moi: **SEEKER chi lo NGUON VAO** (chi bao,
y tuong ghep) · **HEPHAESTUS de co che** (rai luoi tham so, ghep nut) · **QUANTLAB
test**. Ly do: kho chi rong 8 chi bao vi do rong phu thuoc vao "co ai viet bai ve no
khong"; 20 kieu dung Ichimoku la 1 chi bao + luoi tham so, khong phai 20 lan boc
tai lieu. Xem `SO_DO_HE_THONG.txt` muc bo sung va `tai_lieu/BAN_GIAO_HE_THONG.md` muc 9.

Ba dieu trong so do ma de lam nguoc:

1. **MUC TIEU LA TIEN, khong phai chat che hoc thuat.** Nguyen van: *"khong phai
   nhung mo hinh kinh te hay quan tri quy de ma can de cao qua nhieu tieu chi hoc
   thuat hay cac chi tieu chat che. Muc dich cuoi cung la co tien chap nhan ca chi
   phi va rui ro cao"*.
   MDE / FDR / placebo la **NHAN CANH BAO**, khong phai CONG CHAN.
   **TIEU CHI DUYET (chu du an 25/09/2026, thay "chi chan khi thua mua-giu")**:
   *"toi khong quan tam martingale hay dca hay la phuong phap gi. Toi trade don bay
   toi chap nhan rui ro, chi can co lai va maxdd duoi 80% la ok"*. Cong CHAN chi con
   **co lai sau phi + maxDD < 80%** (`cham_diem.TRAN_SUT_GIAM` - MOT nguon cho
   `cong`, `cong_ra_tien`, `bang_he`, `nc_*`) + tinh dung cua so (phi do duoc, du
   lenh, khong an khe dao ngay). Thua mua-giu o cung rui ro va "kieu martingale"
   (tang 2 kinh te) xuong NHAN: van tinh, van hien, khong chan (THE_HE_CONG 6).
2. **QUAN LI LENH quan trong hon ENTRY** - "module quan trong trong toan bo he thong".
3. **"FX" = KIEU GIAO DICH LONG/SHORT**, khong phai chi cap tien. San fx co ca chi
   so, hang hoa, kim loai. Chon tai san theo viec no co ra tien khong, khong theo lop.

**Khong duoc dung lai o muc mo ta.** Chu du an: *"toi muon claude phai lam duoc he
thong do va co the nang cap phat trien hon ca mo ta cua toi"*. So do la SAN, khong
phai TRAN.

## LUAT SO 1 — AI LA NHA NGHIEN CUU CHINH (chot 25/09/2026)

Chu du an: *"The Brain la cong cu va cac phuong an cho cau. Phan thuc thi chinh va
suy luan chinh phai do AI nam quyen"*. Thiet ke: `tai_lieu/NHA_NGHIEN_CUU.md`.

Moi phien Claude Code:
1. **Mo dau bang `b nc`** - ho so nghien cuu (cau hoi mo, cua chu du an xep truoc;
   gia thuyet dang song; thi nghiem tot nhat; hieu biet co bang chung; phep thu da tieu).
2. **Tu chon viec co gia tri nhat va lam** - khong cho giao viec. Chu du an la nha
   tai tro: dat muc tieu, gui y tuong qua `b nc hoi "..."`, doc so tay.
3. **Moi phep do nghien cuu di qua `b nc cc <cong_cu> '<json>'`** (16 cong cu: ho so,
   tim quy luat, thu co che, quet, mo xe lenh, thu luoi, xac nhan, niem phong...) de
   no vao so tay `nc.db`. Khong viet them script `_*.py` roi cho mot thi nghiem moi -
   ket qua ngoai so tay la ket qua khong ai tim lai duoc.
4. **Ket phien**: ghi hieu biet (kem tn_id) + cau hoi moi + trang thai gia thuyet.

Code do va cham, AI khong tu viet ket qua: 3 doan (niem phong mo MOT lan), van tay
thi nghiem, phep thu dem theo dong gia thuyet, ba trang thai. DAT = co lai sau phi;
`tien.cagr_duoi_tran_pct` = CAGR tot nhat voi maxDD < 80% (don bay <= 10, khong qua
Kelly). Niem phong chot DON BAY tren kham pha + xac nhan roi moi mo: DAT = co lai VA
maxDD < 80% o chinh don bay do. Martingale/DCA/luoi hop le. Hai con so ly do:
(a) ket qua tot nhat cua lab (AUDCAD luoi co tia, holdout +13,26%/nam) den tu vong
nghien cuu, khong den tu pheu; (b) tren chuoi co dap an, do tim rong ~3.000 dieu
kien thay edge yeu **3/8**, mot gia thuyet co chu dich thay **8/8** (`b nc kiem 30`).
Hoc tu lenh dung/sai = `mo_xe_lenh`. Het token: `b nc tu-lai MA KHUNG` (khong LLM).

## VAN HANH (chot 12/09/2026)
- Duyet san moi de xuat, **lam lien tuc khong cho duyet**.
- `q ultracode` - ngan sach thoai mai: CPU 95% (10 nhan / 20 luong), lan CPU 6 ·
  LLM 3 · MANG 3 · NHE 8 · **TESTER 1** (mot terminal64.exe la rang buoc VAT LY,
  ngan sach khong mua duoc cai thu hai). Token 8.000 · timeout 300s · thu lai 5.
- Chay DA LUONG cho moi viec khong dung chung trang thai.


File nay tu nap moi khi doc file trong `lab/`. Muc dich: dung mat 15 phut dau
phien de tim lai luat. Ban day du van o `../AGENTS.md`.

## QUY TAC PHIEN — khi chay NHIEU phien Claude Code (chot 16/09/2026)

Nen: `HO_SO_HE_THONG.md` muc 11.10 do duoc **8 tai nguyen dung chung**, va thu
nguy hiem nhat (**MT5 tester**) va cham **khong bao loi nao** - bang so doc y
het mot ket qua that.

- **Chi MOT phien la [GHI]**: duy nhat duoc dung MT5 tester, ghi `nao.db`,
  sua `config/*.json`, va commit vao `master`.
- **Cac phien khac la [DOC]**: moi phien mot `git worktree` + nhanh rieng.
  KHONG tester · KHONG ghi `nao.db` that (dung ban chup chi doc) ·
  KHONG sua `config/*.json` · KHONG mo Chrome CDP 9224.
- Phien [DOC] xong viec -> phien [GHI] review, gop, chay kiem tra that.
- Moi ket luan phai phan biet `CHUA_DO_DUOC` voi ket qua AM.
- Ket moi goi viec: chay test lien quan + ghi `reports/goi_<ten>.md` gom:
  da lam gi · bang chung · so truoc/sau · rui ro con lai · viec chua lam.

Sau khi co slot tester (goi G2-A) thi noi ra: moi phien giu **mot slot rieng**.

## Vao phien / ket phien
```
b nc               HO SO NGHIEN CUU - doc dau tien (LUAT SO 1)
b vao              trang thai song + ban giao hom qua  (~2 giay)
b ban-do           SINH ban do tu ma nguon - DOC TRUOC KHI XAY GI MOI
b kien-truc        SO DO KIEN TRUC: 129 module nhan theo LOP + VAI TRO + no kien truc
b ho-so            HO SO HE THONG: mot file TU DU dua cho AI khong co dia (Claude chat)
b ket "tom tat"    chot ngay: git commit + sinh TIEP_TUC_MAI.md moi
b                  menu day du
```

**`b kien-truc` truoc khi LEN KE HOACH.** `b ban-do` tra loi "co nam tren duong
chay khong"; `b kien-truc` tra loi "he co nhung TANG gi, module nao thuoc tang nao,
tang nao dang phinh hay rong" - tuc cau de lap ke hoach. Sinh ra `KIEN_TRUC.md`,
doc vai tro tu docstring dong dau cua chinh module nen khong bao gio cu. Module
moi ma quen xep lop trong `nhan/kien_truc.LOP` se hien o muc **CHUA XEP LOP**.

**`b ban-do` truoc khi xay module moi.** Phien 12/09 toi xay lai BA thu da co
(`uu_tien.py`, `noi_sinh.py`, va mot EVO thu hai canh `tru/evolution.py`). Ban do
nay sinh TU MA NGUON (`nhan/ban_do.py`) nen khong bao gio cu, va no tra loi dung
cau hoi can: **module nao khong nam tren duong chay nao**. Do 12/09: 31 mo coi
that (sau khi tach 151 script chay tay + 11 ha tang), trong do co ca
`nhan/han_muc.py` - cai KILL-SWITCH cua he.
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

### `ho 3` — PMG: quan li lenh KHONG CO TIN HIEU VAO (14/09/2026)
Dac ta chu du an dua qua LUONG UU TIEN, xep thang vao module quan li lenh:
`tai_lieu/PMG_DAC_TA.md` (nguyen van) + `tai_lieu/PMG_TRIEN_KHAI.md` (da dung gi,
do duoc gi). Cua vao: **`b pmg g0` -> `b pmg quet MA`**. Bon module `nhan/pmg*.py`.

Ba dieu phai thuoc truoc khi doc bat ky so nao cua ho nay:
- **Ky vong duoi random walk = `-chi phi`.** Khong co entry signal thi khong co gi
  khac de ky vong. Moi so duong phai chi ra duoc bat doi xung that o dung timescale.
- **BAR KHONG DO DUOC PMG khi buoc luoi hep hon nen.** Bar chi noi O/H/L/C nen moi
  mo hinh duong di deu phai ghe ca hai cuc tri; luoi nghich chieu duoc tang khong
  mot cu dao chieu moi nen. Do 14/09 tren random walk khong chi phi: buoc/bien_do
  = 0,54 cho **+720%**, o 3,24 cho **-2,3%** (dap an dung la 0). Da chan bang
  `NGUONG_PHAN_GIAI = 2.0` -> `trang_thai = CHUA_DO_DUOC`, KHONG phai `AM`.
- **Null cua ER phai la DAO DAU, khong phai block bootstrap.** Block bootstrap giu
  nguyen TRUNG BINH CUA KHOI, ma do chinh la tu so cua ER -> null nuot mat tin
  hieu (do: ER that 0,2011 vs null 0,2006 tren chuoi AR(+0,6) dung san).

Ban do G0 14/09 (M5, ATR H1, 200 null, FDR-BH 10%, 25/48 o song): **cap cheo FX va
vang HOI QUY o moi thang do** (AUDCAD/EURGBP 8/8 o, XAUUSDM 7/8), con **chi so gan
nhu khong co gi** (US500 va XM_US500 moi cai 1/8, **US100 0/8**). US100 co xu huong
nghieng `WITH` nguoc dau voi FX nhung **khong qua FDR** - la gia thuyet de quet lai,
KHONG phai phat hien.

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

## DOI KHUNG = DOI TAI SAN ve mat phuong phap (chot 07/09/2026)

Chu du an: *"Sau nay chuyen khung can sua co che, cai nay can note vao quy trinh,
theo toi thay la do nhieu lon hon se can phai nang thong so len cao hon."*

Dung, va **co HAI duong khac nhau - dung lan**:

**A. Chuyen mot he DA CO sang khung khac** -> `nhan/ngoai_sinh.chuyen(gt, ma,
khung_dich)`. Phai giu **TY LE KICH HOAT**, khong giu con so. Ly do da ghi trong
chinh file do: cai khong doi khi sang tai san (hay khung) khac la **do HIEM cua
su kien**. `zscore(5) < -1,0` tren D1 kich hoat 19,6% so bar; cung nguong do tren
H1 kich hoat khac han - nhieu lon hon nen nguong phai **nang len** de giu cung
do chon loc.

  Quy doi chu ky (`n`, `giu`) theo ti le bar la **CAN NHUNG KHONG DU**. Do 07/09:
  be 36 chan chon tren D1 sang khung khac, chi quy doi chu ky:
      W1  12/36 chan duong, tong lai  -1.471
      H4  21/36,             tong lai  +6.420
      H1   6/36,             tong lai  -4.739
  `_da_khung.py` lam THIEU dung khau nay - giu lai lam moc, dung coi la ket luan
  ve khung.

**B. Tim he MOI tren khung khac** -> quet lai ca kho **truc tiep tren khung do**
(`_khung_nho.py`), khong chuyen gi ca. Duong nay khong dinh van de nguong vi no
chon lai tu dau.

**Do sau du lieu phai kiem TRUOC** [[khung-nho-do-du-lieu-quyet-dinh]]: dem bar
MOI NAM. US100Cash: D1 tu 2011 · H4/H1 tu **2016** · M30 tu 2018-04 · M15 tu
2022-06 · M5 tu **2025-04 (1,4 nam)**. 2012-2015 H4 va D1 co so bar y het nhau -
MT5 don bar NGAY vao khung nho khi thieu du lieu, khong bao loi.

**Chi phi quyet dinh khung nao dang quet**: spread 0,98 bps an **12,0%** bien do
mot nen M5 nhung chi 0,7% bien do nen D1. Nguoc lai, **phi qua dem 1,56 bps/dem
con dat hon spread**, va chan BAN duoc NHAN +0,18 bps/dem.

## HE TU CHAY BANG QWEN (08/09/2026) — lenh `q`

Khi het token Claude, du an chay tiep bang MOT lenh (cd vao `lab/` roi go `q`):

```
q                chay lien tuc nhieu ngay (Ctrl-C an toan; `q dung` de thoat em)
q trang-thai     xem bang viec + trang thai may
q kiem           tu kiem duong LLM + cong + dieu toc
```

Doc `lab/qwen/DOC_TRUOC.md`. Ba dieu phai nho:

- **qwen DOC va VIET; code CHAM va CHAN.** `qwen/cong.py` cham dat/am bang code,
  qwen khong duoc tu phan. Ly do la mot phep do: LLM dien `co_che` cho 48 khai
  bao, tham dinh bac 41, rong cuu 3.
- **Ba trang thai, khong phai hai.** Ma thoat != 0, thieu file ra, file ra CU hon
  luc bat dau chay, hay bang co phan lon cot so dung im -> deu la `CHUA_DO_DUOC`,
  khong bao gio la `AM`.
- **Lan TESTER = 1 la rang buoc VAT LY**, khong phai lua chon. `chay_tester_kho`
  ghi de cung mot `.mq5` / `.ini` / `.xml` va may chi co mot `terminal64.exe`.
  Hai viec tester cung luc thi ghi de ket qua cua nhau **va khong ai bao loi**.

Sua viec cua may = sua `lab/qwen/NHIEM_VU.json`. Muc tieu CPU o
`config/qwen.json` -> `muc_tieu_cpu` (mac dinh 85, la % cua CA MAY chu khong
rieng he nay, nen khi MT5 tester an 60% thi lan CPU tu co lai).
