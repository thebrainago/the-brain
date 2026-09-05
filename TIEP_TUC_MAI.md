# TIEP TUC NGAY MAI — chot phien 2026-09-05 14:39

boc .mq5 tu 0 len 70%: sua doc_ma viet cho Pine; kho co che 262->326; trailing x4,8 lai; XM_US100CASH PASS

## Trang thai do duoc luc chot
> May tu dien phan nay luc `b ket`. **Dung sua tay** — sua thi mai het so sanh
> duoc. Cot "doi" so voi moc 2026-09-05.

| chi so | hom nay | doi |
|---|---:|---:|
| file test (lab) | 77 |  |
| ham test (lab) | 1072 |  |
| file test (ds/) | 82 |  |
| bang gia .parquet | 269 |  |
| dong so FDR | 1807 | +2 |
|   trong do bac bo | 406 | +2 |
| ung vien xep hang | 567 |  |
| ban doc da thu | 6658 |  |
| co che trong thu vien | 32 |  |
| van de con mo | 12 |  |
|   muc NANG | 3 |  |
| viec dang CHO | 2 | +2 |
| file .py o goc lab | 199 | +7 |

- co DUNG_LAI: **CO (he dang nam im)**
- viec CHO theo loai: bac_cau_san=1, mt5_tick=1
- commit hom nay:
```
1baba4b cham tran 70%: kho co che 262 -> 326, 64 cai tu file .mq5
72f6ddb cham 42 co che quan tri: trailing thang, quy doi tham so bang ATR
af851a3 ho 2 tu 5 len 43 co che: cai trailing/breakeven + noi nguong boc
716598c sua doc_ma: no viet cho Pine nen 389 file .mq5 ra 0 co che
11c9883 chuan hoa quy trinh QuantLab: 5 buoc, 4 module dung lai duoc
f90e448 PASS dau tien: do duoc spread XM US100Cash -> chi phi KHAI thanh SAN
995e9b1 ho co che THU HAI: quan tri vi the + thuoc do tinh cach tai san
c62bfc7 boc .set THAT cua Bigmouse, chay tren AUDCAD: 62%/nam voi von 33$ cent
d324e84 vong quantlab AUDCAD: tiem nang -> 900 cau hinh -> ket qua am co gia tri
2a4bce1 cong ra tien + bo luan nguoc: he dau tien qua ca hai cong
1c44318 dien tay hai muc ban giao 05/09
c15e863 2026-09-05: 6 muc ban giao: 5 ket qua am + 4 con so 04/09 bi lat nguoc; sua tin_hieu_mql5 + them ap_luat_von
```
- file dang doi luc chot: **3**

## Mot doan doc la hieu ca phien

(dien tay: phien nay tim ra dieu gi, cai gi lat nguoc ket luan cu)

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
