# TIEP TUC NGAY MAI — chot phien 24/08/2026

Bao cao day du: `BAO_CAO_2026_08_24.md` (thu muc goc). Phien truoc:
`BAO_CAO_2026_08_23.md`.

## Trang thai
- lab: **321 test xanh** (dau phien 288). Bon file test moi:
  `test_chon_ban_du_lieu.py` (9), `test_lop_va_phi_tai_san.py` (14),
  `test_ghi_so_fdr.py` (6), `test_loai_ma_nguon.py` (4).
- `lab/DUNG_LAI` VAN GIU NGUYEN — he van dang co y nam im.
- Sao luu: `backups/nao_truoc_sua_ghi_so_20260824.db` + 6 file `.py` truoc khi sua
  + `backups/data_khung_cu_20260824/` (222 file cache khung cu, 77 MB).
- Module moi: `quet_be_mat.py` (quet 15 co che x 122 tai san o D1, chi V0-V3).

## Mot doan doc la hieu ca phien

Muc 0 cua ban 23/08 noi duong duy nhat de ha MDE nhom chi so la du lieu dai hon.
**Du lieu dai hon nam san trong kho tu dau — bo nap khong lay no.** `kho()` chon
file theo BYTE, ma file phut luon to hon file ngay, nen moi yeu cau D1 deu nhan
doan lich su NGAN NHAT. XM_US500CASH va XM_US100CASH chi co **367 bar** (duoi
nguong 1.500) nen **chua tung xuat hien trong bat ky vong quet D1 nao**.

Phien nay tim va sua **nam loi im lang**, moi cai o mot khau:

1. **Du lieu**: chon ban theo do phu thay vi byte -> 21 ma dai ra (toi 11x).
2. **Chi phi**: tien to `XM_`/`YH_` lam hong tra cuu phi cho 41 ma; bang lop tai
   san doi chieu bang chuoi con nen 15 chi so bi tinh gia FX cheo.
3. **So FDR**: bo do luc ghi ~80 dong/phut vao so quyet dinh; ca `pytest` cung
   tieu ngan sach (28 dong qua 2 lan chay).
4. **Sang loc**: tang kham pha nap CA CHUOI nen cham holdout, trai voi luat 1
   cua chinh no. Do tren 107 ung vien: 4 doi phan quyet, khong cai nao tu bi
   loai thanh song -> ket luan cu khong bi lat.
5. **Cau hinh**: 5 nut CHET trong `config/tieu_chi.json` (van nut ma khong co gi
   doi).

**Ket qua cho muc 0: US500CASH MDE 30 -> 20 bps/lenh**, duong tinh gia van 0%.
Hai chi so tu vang mat vao duoc be mat, XM_US100CASH co MDE **8,0 bps** — thap
nhat nhom chi so, nhung cung la cap DUY NHAT co duong tinh gia khac 0 (2,0%).
XAUUSD **te di** (20 -> 30) vi mat 1.163 bar Chu nhat cut ma `resample` che ra —
con so 30 la con so that.

## HUONG PHIEN TOI — THONG LUONG KIEM DINH (nguoi dung chot 24/08)

Nguoi dung noi ro: vi du "50 chien luoc" chi la vi du. **Bai toan that la 100
nghin truong hop phai test** — do la ly do QUANTLAB ra doi va can VPS 24/7.
Van de cua phien toi: **rut ngan thoi gian test va tang toc do test.**

### VPS KHONG phai don bay toc do — va ban do bang thong CHUA chac ap o day

Nguoi dung chi ra dung (24/08): **VPS thi so luong con IT hon**. VPS la de chay
24/7, khong phai de chay nhanh. Doi 20 luong lay 4 vCPU la thong luong te di.

Va phai can than voi chinh ban do bang thong: memory `may-nghet-bang-thong-ram`
do **9,4 GB/s phang tu 1 den 20 luong**, nhung do bang mot bai quet MANG LON.
Tap lam viec cua pheu D1 thi **ti hon**: 4.000 nen OHLC ~ **128 KB**, nam gon
trong cache L2/L3 va **khong cham toi kenh nho**. Viec nam trong cache van chia
luong gan nhu tuyen tinh KE CA khi cam mot thanh RAM.

Cai that su nghet bang thong la **quet M1** (5 trieu nen ~ 40 MB moi tai san) va
20 agent MT5 — khong phai pheu D1.

Them mot dau hieu: **0,18 giay cho 4.000 nen la CHAM** so voi khoi luong tinh
toan do. Nghieng ve phi ton Python/pandas hon la bo nho. Neu dung vay thi
`Pool(10)` cho pheu D1 se an gan du 10 lan **ma khong phai mua gi**.

**Do 10 phut la biet, va PHAI do truoc khi khuyen nghi phan cung:** chay cung
mot vong 20 tai san voi 1 tien trinh roi voi 10 tien trinh, so thoi gian tuong.

Thu tu dung:
  1. **Do scaling** (1 vs 10 tien trinh tren pheu D1).
  2. Neu KHONG scale -> dung la nghet bang thong -> **nang RAM**: 4x 8GB DDR4 ECC
     RDIMM hang thao server (1,0-1,6tr), ban thanh LRDIMM 32GB cu duoc 1,2-1,8tr
     nen gan nhu bu tron. Muc tieu 9,4 -> 40+ GB/s, mo khoa dung 20 luong DA CO.
     Phai thao han LRDIMM cu ra — khong tron LRDIMM voi RDIMM duoc.
  3. Neu CO scale -> nut that la phi ton Python/pandas -> giam viec moi phep thu
     (xem ba huong ben duoi) + `Pool`.
  4. VPS chi de GIU MAY CHAY LIEN TUC, khong phai de tang toc.

### So do duoc toi 24/08 (dung lam moc, dung do lai tu dau)

| Viec | Thoi gian | Ghi chu |
|---|---|---|
| 1 lan `chay_pheu` V0-V3, D1, `pham_vi` truyen san | **~0,18 s** | re, khong phai nut that |
| 1 cap trong bang MDE (200 cua so x 9 delta + null) | **~5 phut** | 9.600 lan chay pheu |
| `pham_vi_cua` mot co che (nhom doi chung) | 30-45 s | goi 1 lan/co che, da cache |
| Quet 15 co che x 122 tai san (chi V0-V3) | **~10 phut** uoc | neu KHONG cham `du_luc_de_kiem` |
| Bo test day du | ~6 phut | 321 test |

### Nut that THAT SU da lo ra khi chay `quet_be_mat.py`

Vong quet dung tai co che dau tien co `pham_vi == CO_CO_CHE` (`ibs_bat_day`).
Ly do: V3 goi `du_luc_de_kiem` -> **do MDE cho tung tai san**, va moi lan cache
`reports/mde_cap.json` truot thi no chay ca mot duong cong luc. Tuc mot vong quet
15 x 122 = 1.830 o co the keo theo hang tram phep do MDE.

Ba huong cu the, xep theo ty le loi/cong:

1. **MDE la thuoc tinh cua CAP (tai san, khung), khong phai cua ung vien.**
   Do TRUOC mot lan cho ca be mat (122 cap D1) roi nap tu cache — thay vi do lazy
   giua vong quet. Cache da co (`mde_cap.json`, 78 muc) nhung chua duoc **nap
   truoc**. Uoc: 122 cap x ~2 phut = ~4 gio MOT LAN, sau do vong quet chay tu do.
2. **Xep thu tu cong theo GIA RE TRUOC.** V1 (sinh tin hieu + dem) re gap hang
   tram lan V3 (do luc). Da dung thu tu do, nhung V2 chay `MP.chay` HAI lan
   (co che + mua-giu) roi V3 chay THEM 3 lan nua (3 doan) + 1 lan cho nhay chi
   phi = 6 lan backtest moi o. Mua-giu cua mot (tai san, khung) la BAT BIEN —
   dang tinh lai o moi ung vien.
3. **`kho()` doc schema 253 parquet.** Da co cache trong tien trinh (van tay theo
   so file + tong mtime) nhung KHONG co cache tren dia: moi tien trinh moi tra
   ~0,34 s, va mot vong `_cap_ke_tiep` tren 29 tai san tung goi 80 lan = 27 giay.

### Viec dau tien nen lam
Do PROFILE that mot vong `quet_be_mat.py` (cProfile, 1 co che x 20 tai san) de
biet ty le thoi gian giua `MAU.sinh` / `MP.chay` / `DO.chi_so` / `du_luc_de_kiem`.
**Dung doan — dung do.** Chua ai profile duong nay lan nao.

---

## Viec tiep theo, theo thu tu

0. **THONG LUONG KIEM DINH — xem phan tren.** Nguoi dung da chot day la
   huong chinh cua phien toi.
0b. **QUYET 795 dong `family=do_luc` trong so FDR.** Day la viec cua nguoi dung,
   khong phai cua may: xoa dong khoi so kiem toan khong hoan tac duoc. Hai lua
   chon: giu nguyen va danh dau, hoac chuyen sang bang `do_dac` rieng.
1. **Quet lai toan be mat sau khi sua.** `python quet_be_mat.py` — 15 co che x
   122 tai san o D1, chi V0-V3 nen khong tieu suat FDR. **Chay qua dem**: co che
   nao co `pham_vi == CO_CO_CHE` se lam moi tai san goi `du_luc_de_kiem` -> do
   MDE, rat cham khi cache `reports/mde_cap.json` con it (dang co 78 muc).
2. **Do spread H1 that cho nhom chi so tu terminal MT5** (`bao_dam_spread`).
   Sau khi sua muc 2, cac ma `YH_*` da co phi qua dem DO DUOC nhung van thieu
   spread nen `do_tin` con la KHAI. Va: **spread do tu bar D1 la CHAN TREN** —
   do doi chieu tren EURCAD, D1 cho 1,70 bps con H1 cho 1,22 bps (chenh 39%) vi
   bar ngay chi lay MOT mau spread va moc do roi vao gio dao phien.
3. **Them template cho SuperTrend, Stochastic, do doc duong trung binh.**
   Do 24/08 tren 52 file `.mq5`: 18 chien luoc / 12 tien ich / 22 chi bao; trong
   18 chien luoc co 6 da co template, 12 chua. Ba co che tren la thu that su
   thieu. Khong co template thi khong co duong vao QUANTLAB.
4. **MQL5: muon 50 chien luoc that thi quet 3-4 trang.** Trang 1 muc `experts`
   (40 bai) chi cho ~15 chien luoc that.
5. Muc 0b/1/2/3 cua ban 23/08 van nguyen gia tri: `vuon_nguon.mot_luot_tim`
   (~100 ten chua thu), 193 ban `khong_doc_duoc`, 103 viec `kham_pha_theo_mau`
   dang cho.

## Khong duoc quen (bo sung cho ban 23/08)

- **`kho()` chon ban theo DO PHU, khong theo byte.** Them mot file vao `data/`
  co the doi ban duoc chon cua ca mot ma. Cache mang ten file nguon nen no tu
  het han — nhung ket qua backtest cu thi khong.
- **Mot ma co ban `san` thi ban `ngoai` cung ten bi loai.** Do la cai chan
  `us500cash_daily` (thuc ra la Yahoo ^GSPC) khoi ma US500CASH (CFD).
- **Cung muc gia KHONG co nghia la cung chuoi.** Ba file `*_daily_dai` lech gia
  0,24-0,36% nhung tuong quan loi suat ngay chi 0,08-0,14.
- **Chi phi do o khung RIENG** (`du_lieu.khung_do_spread`), khong phai khung
  chay backtest: ban D1 dai nhat thuong khong co cot spread.
- **Do dac phai goi `ghi_so=False`.** Bat ky duong nao goi
  `cong.xet(tren_holdout=True)` tren du lieu tong hop deu phai truyen co nay.
- **`chay_pheu` khong truyen `df` = chi co TRAIN.** Muon ca chuoi thi noi ro
  `cham_holdout=True`.
- **Bo test cham duong FDR phai dat `SO.DB` sang CSDL tam.**
- **`CTrade trade;` co trong MOI tien ich quan ly lenh.** Ranh gioi chien luoc /
  tien ich la **MO VI THE MOI** (`bien_dich_ung_vien.loai_ma_nguon`).
