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

(dien tay: phien nay tim ra dieu gi, cai gi lat nguoc ket luan cu)

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
