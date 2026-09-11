# TIEP TUC NGAY MAI — chot phien 2026-09-12 00:14

khoi 2-6 DAT: so bai hoc, anh chup bat bien, tang cham tien, 4 cua vao, khoa tester + de quan tri len EA ngoai. Cuu mat du lieu kho co che 1149->3

## Trang thai do duoc luc chot
> May tu dien phan nay luc `b ket`. **Dung sua tay** — sua thi mai het so sanh
> duoc. Cot "doi" so voi moc 2026-09-07.

| chi so | hom nay | doi |
|---|---:|---:|
| file test (lab) | 96 | +8 |
| ham test (lab) | 1379 | +150 |
| file test (ds/) | 82 |  |
| bang gia .parquet | 269 |  |
| dong so FDR | 1807 |  |
|   trong do bac bo | 406 |  |
| ung vien xep hang | 567 |  |
| ban doc da thu | 10115 | +3457 |
| co che trong thu vien | 32 |  |
| van de con mo | 12 |  |
|   muc NANG | 3 |  |
| viec dang CHO | 2 |  |
| file .py o goc lab | 260 | +17 |

- co DUNG_LAI: **CO (he dang nam im)**
- viec CHO theo loai: bac_cau_san=1, mt5_tick=1
- commit hom nay:
```
5feb032 go ky tu 0x08 con sot trong doc_hieu - chinh du an DA CO bai kiem bat no
b99022f MAT DU LIEU: kho co che tut 1.149 -> 3 vi doc-sua-ghi khong khoa. Da cuu va da va.
```
- file dang doi luc chot: **3**

## Mot doan doc la hieu ca phien

(dien tay: phien nay tim ra dieu gi, cai gi lat nguoc ket luan cu)

## Viec tiep theo, theo thu tu

1. (chua dien)

## KHONG DUOC QUEN
- **Cột kết quả GIỐNG HỆT NHAU trên toàn bảng** = tham số không có tác dụng.
  Dấu hiệu chung của 3 lỗi khác nhau trong phiên này. Kiểm đầu tiên.
- **EA nhiều-slot có thể làm lệch số — CHƯA TRUY RA.** Mọi đường vốn của ma trận
  ghép đều từ EA đó. Cần đối chứng switch-vs-nhiều-slot trên D1 với 40 slot.
- **Khử trùng theo ĐƯỜNG VỐN**, không theo tên: 11-13% kho là hàng trùng.
- **Script ở `lab/` phải có `__main__` guard.**
- **2012-2015 H4 và D1 có số bar y hệt nhau** — MT5 dồn bar NGÀY vào khung nhỏ.
- **Phí qua đêm 1,56 bps/đêm ĐẮT HƠN spread 0,98**; chân BÁN được **nhận** +0,18.
- **`Model=0/4` không chạy được**: M1 trong máy chỉ có từ 2026-05-28.
- **`PositionClosePartial` dưới min lot thất bại IM LẶNG** — chạy ở lot ≥ 2× min.
- Tài khoản MT5 là **THẬT** (trade_mode=2), số dư 0, và là **CHUẨN** không phải Micro.
