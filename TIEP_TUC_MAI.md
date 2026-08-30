# TIEP TUC NGAY MAI — chot phien 2026-08-30 10:45

gop 'Promt cho DS' vao ds/, mo git cho ca du an, dung bo lenh b + quy trinh chot phien, ra soat toan bo module

## Trang thai do duoc luc chot
> May tu dien phan nay luc `b ket`. **Dung sua tay** — sua thi mai het so sanh
> duoc. Cot "doi" so voi moc chua co moc.

| chi so | hom nay | doi |
|---|---:|---:|
| file test (lab) | 29 |  |
| ham test (lab) | 322 |  |
| file test (ds/) | 82 |  |
| bang gia .parquet | 252 |  |
| dong so FDR | 1769 |  |
|   trong do bac bo | 398 |  |
| ung vien xep hang | 107 |  |
| ban doc da thu | 1338 |  |
| co che trong thu vien | 32 |  |
| van de con mo | 24 |  |
|   muc NANG | 14 |  |
| viec dang CHO | 104 |  |
| file .py o goc lab | 97 |  |

- co DUNG_LAI: **CO (he dang nam im)**
- viec CHO theo loai: kham_pha_gop=1, kham_pha_theo_mau=103
- commit hom nay:
```
2222ad5 moc goc 30/08/2026: mo git cho THE BRAIN
```
- file dang doi luc chot: **7**

## Mot doan doc la hieu ca phien

Bao cao day du: `BAO_CAO_2026_08_30.md` (thu muc goc).

Hai nua du an da thanh mot: `Downloads/Promt cho DS` gio la
`Research SP500/ds/` (giu git rieng, 56 commit, 799 test). Truoc do hai ben da
noi voi nhau bang duong dan tuyet doi cung — 9 file `ds/browser/*` ghi thang vao
`lab`, con `lab/BROWSER_SCAN*.bat` nhet `Promt cho DS` vao `sys.path`. Sua 6 file,
chay lai ca hai bo test: **799 + 321 deu xanh**.

**Du an da chay hai thang khong co git.** Da `git init`: 2.021 file, 7,5 MB
(bo `data/`, `reports/` 1,4 GB, `backups/` 247 MB). Tu gio `b luu` thay cho copy tay.

Ha tang moi: `b` la mot cua vao duy nhat; `b ket "..."` chot phien (cat ban giao cu
sang `nhat_ky/`, sinh ban moi voi **phan SO do may dien**, commit, ghi anh
`nhip_song.json` de mai tinh chenh lech); `b vao` doc lai. Test **6:07 -> 2:30**
nho `-n 8 --dist loadfile`. 26 script mot lan dua vao `nghi_huu/vun_20260830/`.

**Hai con so cua ban ra soat toan he:** he da **tat 14 ngay** (co `DUNG_LAI` tu
16/08 23:13; NGHI/BANKER/EVO nhip cuoi 16/08, NGHI thoat rc=1), va van **0 PASS**.
Ba module giu bat bien coi nhat — `canary.py`, `quant_plan.py`, `evolution.py` —
**khong co file test nao**.

Ve cau hoi multi-agent / dynamic code (muc 5 cua bao cao): chia luong duoc cho
template + test + adapter, **khong** cho `cong/so/chi_phi/ngu_phap`; dynamic code
chi o duong KHAI BAO (`ngu_phap`) chu khong o duong quyet dinh. Va toc do xay
khong phai rang buoc dang chan — cong FDR bi niem kin moi la.

## Viec tiep theo, theo thu tu

0. **Cong FDR bi niem kin.** San p placebo 0,005 gap nguong LORD tu phep thu thu 4
   -> **346 FAIL hien co vo nghia**. Quyet dinh san p / nguong, bo ket qua cu,
   chay lai. Khong xong viec nay thi moi thu xay them deu do vao mot cai cong
   khong phan xu duoc.
0b. **QUYET 795 dong `family=do_luc` trong so FDR.** Viec cua chu du an: xoa dong
   khoi so kiem toan khong hoan tac duoc. Giu nguyen va danh dau, hoac chuyen sang
   bang `do_dac` rieng.
1. **Go `DUNG_LAI`, `b chay`**, xem `nghi.py` hong o dau (rc=1 tu 16/08).
2. **`b profile quet_be_mat.py`** — 10 phut, biet ty le thoi gian giua `MAU.sinh` /
   `MP.chay` / `DO.chi_so` / `du_luc_de_kiem`. **Dung doan, do.** Chua ai profile
   duong nay lan nao.
3. **Nap truoc bang MDE cho 122 cap D1** (~4 gio, MOT lan) roi bo `du_luc_de_kiem`
   lazy. Day la nut that that su: mot vong quet 15 x 122 keo theo hang tram phep do.
4. **Cache mua-giu theo (tai san, khung)** — bat bien nhung dang tinh lai o moi ung
   vien; 6 lan backtest moi o xuong con 2.
5. **Port `test_no_acceptance_test_is_vacuous` tu `ds` sang `lab`**, roi viet test
   cho `canary`, `quant_plan`, `evolution`. Day la dieu kien truoc khi chia luong.
6. **Ba template**: SuperTrend, Stochastic, do doc duong trung binh. Do 24/08 tren
   52 file `.mq5`: 12/18 chien luoc chua co template nen khong co duong vao QUANTLAB.
7. **Do spread H1 that cho nhom chi so tu terminal MT5** (`bao_dam_spread`).
   Spread do tu bar D1 la CHAN TREN — EURCAD D1 1,70 bps vs H1 1,22 bps (chenh 39%).
8. **Noi `ds` <-> `lab`**: chon MOT chieu. De xuat: `lab` la control plane, `ds` la
   thu vien duoc goi — khong phai hai bo nao chay song song. Hien SEEKER -> QuantLab
   ben `ds` van go tay, va `ds` khong co dich vu nen.
9. **MQL5: muon 50 chien luoc that thi quet 3-4 trang.** Trang 1 muc `experts`
   (40 bai) chi cho ~15 chien luoc that.
10. Muc con lai tu 23/08: `vuon_nguon.mot_luot_tim` (~100 ten chua thu), 193 ban
   `khong_doc_duoc`, 103 viec `kham_pha_theo_mau` dang cho, 12 nguon can trinh duyet
   (CDP chua mo).

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
