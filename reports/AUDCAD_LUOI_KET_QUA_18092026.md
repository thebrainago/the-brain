# AUDCAD — LUOI HAI CHIEU CO TIA LENH (do 18/09/2026)

Chu du an phan bien dung: quet 668 co che ENTRY roi ket luan "AUDCAD khong ra
tien duoc" la ket luan SAI PHAM VI. Tren FX, tien nam o QUAN TRI VI THE.

## Do truoc, dat tham so sau

Song AUDCAD H4 (20.902 bar, ZigZag boi_atr=2):

| | |
|---|---|
| Bien do day | trung vi **1,31%** · p75 1,76% |
| Bien do hoi | trung vi **0,83%** · p75 1,08% |
| Ti le hoi | trung vi **70,1%** (p25 53% · p75 85%) |
| Thoi gian | day 11 bar · hoi 6 bar |
| So song | **160/nam** · len 571 (1,297%) · xuong 528 (1,341%) |

**Gia lui bao xa truoc khi ve lai muc vao** (mua tai MOI bar, 20.900 mau):

| | lui | ket |
|---|---:|---:|
| p50 | 0,119% (~11 pip) | 1 bar |
| p90 | 0,325% (~29 pip) | 1 bar |
| p99 | 0,711% (~64 pip) | 1 bar |
| p99,9 | 2,054% (~185 pip) | 62 bar |
| **max** | **13,202% (~1.188 pip)** | **1.527 bar** |

99% so lan gia ve lai chi sau 1 bar — day la cai nuoi luoi. Duoi phan bo co cu
lui 13,2% ket gan mot nam — day la cai giet luoi khong du suc chiu.

## Ket qua quet 72 cau hinh (nua dau / nua sau)

**72/72 khong chay tai khoan o ca hai nua.**

| Cau hinh | train %/nam | DD | **hold %/nam** | DD | lo treo dinh | lenh/nam |
|---|---:|---:|---:|---:|---:|---:|
| buoc30 hs1,0 tp60 **tia** | 17,11 | −4,8 | **13,26** | −3,5 | 11,0% von | 578 |
| buoc20 hs1,3 tp60 **tia** | 11,47 | −4,1 | **10,19** | −1,8 | 5,9% von | 485 |
| buoc20 hs1,0 tp45 **tia** | 20,60 | −5,5 | 12,01 | −4,9 | 14,6% von | 618 |

## PHAT HIEN CHINH: tia lenh la TOAN BO su khac biet

| | hold %/nam | hold DD | Calmar |
|---|---:|---:|---:|
| **Co tia lenh** | **+13,26** | −3,5% | **3,75** |
| Khong tia lenh | +0,66 | −9,1% | 0,07 |

Cung bo tham so luoi, chi bat/tat `tia_lenh` (ghep lenh SAU NHAT voi lenh DAU
TIEN, dong ca cap khi tong lai cua cap >= 4 pip, toi da 1 cap/bar):
**+0,66%/nam -> +13,26%/nam**, va sut giam **−15,6% -> −3,5%**.

Dung nhu chu du an noi: *"dca chieu sai + nhoi chieu dung, dung lai tia lenh dan"*.

## No giai luon bai toan tan suat

Entry don thuan: 668 co che, khong co che nao vua dat 2 lenh/tuan vua Sharpe>0.
Luoi co tia: **578 lenh/nam ~ 11 lenh/tuan**, phi an 19,7% lai gop.

## CHUA DUOC COI LA KET LUAN

1. **Chua qua MT5 tester** — luat goc: Python chi la sang loc so bo.
2. **Lo treo dinh 11% von** — DD duong equity chi −3,5% vi lai da chot bu lai,
   nhung nguoi van hanh CO LUC om lo treo 11%; voi don bay that day la rui ro
   margin call, khong phai con so trang tri.
3. Chua do placebo cho luoi (luoi khong co "entry" theo nghia thong thuong nen
   phai thiet ke null khac: ngau nhien hoa BUOC va HUONG).
4. Cu lui 13,2%/1.527 bar trong lich su chua roi vao nua holdout — phai kiem
   rieng xem cau hinh nay song qua no khong.
