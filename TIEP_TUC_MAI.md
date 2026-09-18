# TIEP TUC NGAY MAI — chot phien 2026-09-19 00:00

AUDCAD: luoi hai chieu CO TIA LENH cho holdout +13,26%/nam DD -3,5% Calmar 3,75; tia_lenh la TOAN BO khac biet (khong tia chi +0,66%/nam). Do song truoc dat tham so sau. Truoc do 668 co che ENTRY qua tester that: 0 co che vua du 2 lenh/tuan vua Sharpe duong - ket luan 'AUDCAD khong ra tien' cua toi SAI PHAM VI, chu du an phan bien dung. Nap tong ket SP500 vao ha tang: them TANG 2 KINH TE vao cong. Gom kho: tach sp500_phase1 khoi The Brain, giai phong 2GB. Dua The Brain len GitHub rieng tu.

## Trang thai do duoc luc chot
> May tu dien phan nay luc `b ket`. **Dung sua tay** — sua thi mai het so sanh
> duoc. Cot "doi" so voi moc 2026-09-15.

| chi so | hom nay | doi |
|---|---:|---:|
| file test (lab) | 157 | +11 |
| ham test (lab) | 2179 | +98 |
| file test (ds/) | 82 |  |
| bang gia .parquet | 0 | -1 |
| dong so FDR | 1811 |  |
|   trong do bac bo | 406 |  |
| ung vien xep hang | 705 |  |
| ban doc da thu | 12078 |  |
| co che trong thu vien | 32 |  |
| van de con mo | 18 | -5 |
|   muc NANG | 3 | -2 |
| viec dang CHO | 34 |  |
| file .py o goc lab | 357 | -6 |

- co DUNG_LAI: **CO (he dang nam im)**
- viec CHO theo loai: kham_pha_theo_mau=34
- commit hom nay:
```
(chua commit gi hom nay)
```
- file dang doi luc chot: **4**

## Mot doan doc la hieu ca phien

(dien tay: phien nay tim ra dieu gi, cai gi lat nguoc ket luan cu)

## Viec tiep theo, theo thu tu

0. **ĐỌC `TON_VIEC.md` mục C trước** — anh giao tối 15/09, xếp trên mọi việc cũ:
   C0 báo cáo TOÀN The Brain (không chỉ AUDCAD) · C1 sửa quản trị AUDCAD không
   nhất quán (RSI-cross-30 mà giữ 20 vs 50 bar) · C2 test TRAILING trên AUDCAD H4
   (`_quan_tri_ghep.py`, tổng quát `--khung`) · C3 họ chiến lược mới nến-vol-lớn ở
   RSI cực trị + râu nến quét · C4 chạy lại quy trình tìm tài liệu + tự nghiên cứu.


1. **EURGBP chon RIENG** (train H4 da xong: `reports/TESTER_KHO_EURGBPmicro_H4.json`).
   Chay chuoi da nhan `--ma EURGBP --khung H4`:
   `_audcad_chon_va_xac_nhan.py` -> `_audcad_gom_cum.py` -> `_audcad_placebo.py`.
   Neu EURGBP co danh muc rieng qua placebo + tuong quan chuoi von THAP voi AUDCAD
   -> ghep hai cap thanh danh muc da tai san (nang Calmar, khong chi tang don bay).
   Can TESTER_EURGBP_H4_TRAIN.json + _HOLDOUT.json truoc khi chay buoc chon.
2. **Quyet dinh don bay lot demo** (chu du an: 27% it, khong so rui ro). Hien
   verify lot 0,1/chan. 27%/nam = lot 0,9/chan tren 25k; muon hon thi nang tiep
   theo duong bien trong AUDCAD_TONG_KET.md. Doi `b demo` lot roi chay `nhip --that`.
3. **Cron nhip --that moi 4h** (bar H4 dong) de tu dong 24/7. Terminal phai mo +
   Algo bat (che do live gan vao terminal nguoi dung, khong headless).
4. Passview: san Telegram/social lay tai khoan AUDCAD nguoi that de doc quan tri lenh.

> Đối chiếu mô tả 16/09: ~60%, xem reports/DOI_CHIEU_MO_TA_20260916.md


