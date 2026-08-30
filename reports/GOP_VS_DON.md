# GOP RO CO HA DUOC MDE KHONG
*2026-08-23 18:47:25*

Do bang **bps moi lenh** de dat canh duoc bang MDE don le.
Nguong bac bo lay tu chinh phan phoi null (phan vi 95), nen ca hai nhanh
deu co cung muc duong tinh gia 5% - so sanh moi cong bang.

## chi_so_my · D1 · 9 tai san

- Tuong quan trung binh giua cac chan: **0.081**
- So tai san HIEU DUNG: **5.46** trong 9
- Nguong bac bo (Sharpe): don 0.083 · gop 0.186

| delta (bps/lenh) | DON phat hien | GOP phat hien | Sharpe don (tv) | Sharpe gop (tv) |
|---|---|---|---|---|
| 0.0 | 5.0 % | **5.0 %** | 0.045 | 0.147 |
| 0.5 | 14.0 % | **25.0 %** | 0.056 | 0.17 |
| 1.0 | 33.5 % | **57.5 %** | 0.065 | 0.191 |
| 1.5 | 45.0 % | **85.5 %** | 0.079 | 0.213 |
| 2.0 | 59.0 % | **99.5 %** | 0.091 | 0.237 |
| 3.0 | 85.5 % | **100.0 %** | 0.115 | 0.282 |
| 5.0 | 100.0 % | **100.0 %** | 0.156 | 0.372 |
| 10.0 | 100.0 % | **100.0 %** | 0.257 | 0.593 |
| 20.0 | 100.0 % | **100.0 %** | 0.459 | 1.03 |

**MDE don = 3.0 bps/lenh · MDE gop = 1.5 bps/lenh**
→ gop ha MDE **2.00 lan**

## vang · D1 · 7 tai san

- Tuong quan trung binh giua cac chan: **0.07**
- So tai san HIEU DUNG: **4.94** trong 7
- Nguong bac bo (Sharpe): don -0.002 · gop -0.174

| delta (bps/lenh) | DON phat hien | GOP phat hien | Sharpe don (tv) | Sharpe gop (tv) |
|---|---|---|---|---|
| 0.0 | 5.0 % | **5.0 %** | -0.067 | -0.291 |
| 0.5 | 6.5 % | **12.0 %** | -0.058 | -0.271 |
| 1.0 | 11.0 % | **17.0 %** | -0.049 | -0.251 |
| 1.5 | 18.0 % | **20.0 %** | -0.034 | -0.226 |
| 2.0 | 28.0 % | **32.0 %** | -0.023 | -0.205 |
| 3.0 | 51.0 % | **61.0 %** | -0.001 | -0.159 |
| 5.0 | 90.0 % | **93.0 %** | 0.041 | -0.068 |
| 10.0 | 100.0 % | **100.0 %** | 0.152 | 0.16 |
| 20.0 | 100.0 % | **100.0 %** | 0.348 | 0.6 |

**MDE don = 5.0 bps/lenh · MDE gop = 5.0 bps/lenh**
→ **gop KHONG ha duoc MDE**

## fx · D1 · 6 tai san

- Tuong quan trung binh giua cac chan: **0.121**
- So tai san HIEU DUNG: **3.74** trong 6
- Nguong bac bo (Sharpe): don 0.004 · gop 0.19

| delta (bps/lenh) | DON phat hien | GOP phat hien | Sharpe don (tv) | Sharpe gop (tv) |
|---|---|---|---|---|
| 0.0 | 5.0 % | **5.0 %** | -0.125 | 0.084 |
| 0.5 | 17.5 % | **27.0 %** | -0.076 | 0.13 |
| 1.0 | 35.0 % | **45.5 %** | -0.027 | 0.175 |
| 1.5 | 63.0 % | **52.5 %** | 0.027 | 0.221 |
| 2.0 | 74.0 % | **62.5 %** | 0.078 | 0.266 |
| 3.0 | 78.0 % | **73.0 %** | 0.178 | 0.357 |
| 5.0 | 87.0 % | **89.0 %** | 0.315 | 0.543 |
| 10.0 | 100.0 % | **100.0 %** | 0.589 | 1.031 |
| 20.0 | 100.0 % | **100.0 %** | 1.383 | 2.047 |

**MDE don = 5.0 bps/lenh · MDE gop = 5.0 bps/lenh**
→ **gop KHONG ha duoc MDE**


---

## Ket luan va LUAT rut ra

| Lop | MDE don | MDE gop | Gop co giup khong |
|---|---|---|---|
| chi so My | 3,0 bps | **1,5 bps** | **co — ha 2 lan** |
| vang | 5,0 | 5,0 | khong |
| FX | 5,0 | 5,0 | **khong, va te di o vung giua** (delta 2 bps: don 74% so voi gop 62,5%) |

**Gop KHONG phai thuoc bo vo dieu kien.** No chi mua duoc luc khi co che that su
song o DA SO chan. Gop them nhung chan ma co che khong song se nang ca nen lan
phuong sai cua thong ke gop, nen nguong bac bo cung cao len - va phan duoc khong
bu noi phan mat.

**Luat da cai vao `sang_loc.v3_phan_chung`:** leo thang sang duong gop khi va chi
khi `pham_vi == CO_CO_CHE`. Do la khac biet giua mot buoc leo thang CO LY DO va
mot lan thu lai cau may.

## Vi sao khac ghi chep 22/08

So cai ghi: *"gop 12 chi so chi ha nguong 0,535 -> 0,511"*. Ban do hom nay cho
3,0 -> 1,5 bps. Hai ban **khong mau thuan** - chung do hai thu khac nhau, va diem
mau chot la:

**Tuong quan cua CHUOI LAI CHIEN LUOC (0,08) thap hon nhieu tuong quan cua TAI
SAN.** IBS bat day chi o trong thi truong ~18% thoi gian, va o nhung thoi diem
khac nhau tren tung chi so. Nen so tai san hieu dung la **5,46**, khong phai
1,13 nhu uoc luong tu tuong quan gia.

Bai hoc chung: khi tinh loi the cua viec gop, phai do tuong quan tren **chuoi lai
cua chien luoc**, khong phai tren chuoi gia.
