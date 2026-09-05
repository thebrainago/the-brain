# TIEP TUC NGAY MAI — chot phien 2026-09-05 07:45

6 muc ban giao: 5 ket qua am + 4 con so 04/09 bi lat nguoc; sua tin_hieu_mql5 + them ap_luat_von

## Trang thai do duoc luc chot
> May tu dien phan nay luc `b ket`. **Dung sua tay** — sua thi mai het so sanh
> duoc. Cot "doi" so voi moc 2026-09-04.

| chi so | hom nay | doi |
|---|---:|---:|
| file test (lab) | 77 |  |
| ham test (lab) | 1072 | +3 |
| file test (ds/) | 82 |  |
| bang gia .parquet | 269 |  |
| dong so FDR | 1805 | +6 |
|   trong do bac bo | 404 |  |
| ung vien xep hang | 567 |  |
| ban doc da thu | 6658 |  |
| co che trong thu vien | 32 |  |
| van de con mo | 12 |  |
|   muc NANG | 3 |  |
| viec dang CHO | 0 |  |
| file .py o goc lab | 192 | +5 |

- co DUNG_LAI: **CO (he dang nam im)**
- viec CHO theo loai: khong con
- commit hom nay:
```
(chua commit gi hom nay)
```
- file dang doi luc chot: **24**

## Mot doan doc la hieu ca phien

Lam het 6 muc cua ban giao 04/09. Ca 6 deu la KIEM CHUNG chu khong phai kham
pha, va **4 con so cua hom qua khong dung duoc khi do lai** — deu vi mot gia
dinh sai cua chinh toi, khong phai vi thi truong:

- **Lucky Cat**: ban 04/09 chua tung chay; chay ra von cuoi x1,4e28. Ba loi:
  lay nhanh LAI cua risk-json lam loi/ngay, coi don vi risk-json la % von, va
  goi mot he scalping XAUUSD la "luoi FX". Sua xong: phoi nhiem DO TRUC TIEP
  (khong doan don bay) — dinh 7,94% von mat tren 1% vang; cu vang giet tai
  khoan xay ra **1 lan / 3,16 nam** neu ket vi the ca ngay o muc tai dinh.
- **6 he dat 20%/nam: FAIL 6/6 tren holdout.** Sharpe train ~1,0 -> 0,20-0,34.
  KHONG he nao co CAGR bang mua-giu (6,22%/nam, Sharpe 0,287). Canh bao cua ban
  giao dung: mot hien tuong mac 6 ao.
- **Quet rong 262 co che x 194 ma D1** (37.060 phep do, 11 phut): 35 "vuot MDE"
  nhung ca 35 nam tren dung 3 ma co `chi_phi_do_tin=KHAI` (spread bia 1 bps).
  NZDHUF tu to cao: 620 bar ma MDE 0,120, trong khi EURUSD 5.729 bar duoc 0,596.
  **Buoc chi phi phai do duoc -> 0/37.060.**
- **"Chan DD 40% gan nhu mien phi" la AO** — do sut giam tren cai dinh DA DAT
  LAI. Do dung: -68,18% chu khong phai -42%. Chan DD la **nhieu**; thu duy nhat
  giam DD von ca nhan la **rut tien** (-54,3% -> -46,1%, gia -1,21d CAGR).
- **Ban do chi phi lien san: 0/59 dong qua xac minh.** FXCE =
  `NeotechFinancialServices-Demo`, Exness = `Exness-MT5Trial14`; chi XM la may
  chu that. Loc chu `demo` KHONG bat duoc `Trial`.
- **120 ho so mql5 signal**: nhom "giu ngan + cat sach + tai deu" CO THAT va
  16/17 danh XAUUSD (nen 55%, p=0,0006) — nhung nhom do kiem IT hon phan con
  lai (301% vs 458%). Ky luat do duoc khong di kem loi suat.

Sua vao HE chu khong chi bao cao: `nhan/tin_hieu_mql5.py` (rui_ro_json dung 5
truong, them `duong_von`, them `phan_loai_mang` nhan mang theo HINH DANG vi thu
tu khong co dinh), `nhan/bien_don_bay.ap_luat_von` (mot ban cai dat cho chan DD
+ rut dinh ky, ba cai dinh tach nhau) + 3 bai kiem chan loi quay lai,
`_quet_rong_d1.py` co `vuot_mde_do_duoc`.

Mot loi toi tu sua: cat doan D1 lan trong file vang M5 bang so cung
`iloc[1963:]`, trong khi du an DA CO `du_lieu.cat_doan_tho` cho dung viec do.
Da thay; ban cua du an con giu duoc nhieu hon (9,5 nam thay vi 9,2).

## Viec tiep theo, theo thu tu

1. **Bac cau san cho 3 ma chi phi KHAI.** Quet rong cho ket qua am ve CHUOI
   GIAO DICH DUOC, khong phai am ve co che. YH_NASDAQ / TS_BTC / NZDHUF deu la
   che do `nghien_cuu`. Goi `quantlab.bac_cau_san` de dua co che sang tai san
   cung LOP co chi phi DO DUOC. Luu y 6 he NASDAQ da FAIL holdout roi -> lay
   nhung co che con lai trong 35 dong.
2. **Do chi phi that cho cac ma dang KHAI.** Nut that lo ra o muc 3: 8.959/37.060
   phep do khong co MDE, va 3 ma duy nhat "vuot" deu la chi phi bia. Dieu quyet
   dinh do rong cua pheu bay gio la SO MA CO CHI PHI DO DUOC, khong phai so co
   che. Bat dau bang `chi_phi.do_moi_san()` tren XM (may chu that duy nhat).
3. **Ho so vang -> `noi_sinh`.** Dua ho so do duoc o muc 5 vao lam rang buoc
   sinh co che: vang, giu 7-600 phut, MAE/MFE <= 0,98, tai deu <= 0,87,
   ~1.000 lenh, PF ~1,5. Day la cach dung DUNG cua lop nguon signal — thu hep
   khong gian tim kiem, khong tu sinh luat.
4. **Rut tien dinh ky la luat DUY NHAT con dung** sau muc 4. Neu co he nao qua
   cong ve sau thi ap `bien_don_bay.ap_luat_von(rut_ky=...)`, va bao CA HAI so
   (DD tai khoan va DD von ca nhan). Dung bao chan DD nhu mot cai loi.
5. **Ban do chi phi lien san: mo tai khoan THAT nho o FXCE va Exness**, giu mot
   vi the qua dem, doi chieu SAO KE. Day la viec cua chu du an, khong lam thay
   duoc. Truoc khi do, KHONG dung bang do de quyet dinh chuyen tien.
6. Quet rong tren khung khac D1 (H4 giau nhat theo `quet-phai-mo-DA-KHUNG`) —
   nhung chi sau khi muc 2 xong, neu khong lai ra them 35 duong tinh gia.

## KHONG DUOC QUEN (bo sung 03/09)
- `b mang` TRUOC khi san bat cu thu gi.
- **Lam "giong nguoi" qua tay thi phan tac dung**: `requests.get` tran 4/4 =
  200; phien giu cookie + Referer 4/4 = 403.
- `thu_thap` ghi vao bang `artifact`, KHONG vao `tai_lieu`.
- Payload artifact LONG mot tang: ma o `payload["payload"]["content"]`.
- `Accept-Encoding: br` khi khong co brotli -> HTTP 200 nhung `r.text` RAC.
