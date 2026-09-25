# HIEU CHUAN NHA NGHIEN CUU - chuoi co dap an

*2026-09-25 14:37:29 · sinh boi `python b.py nc kiem` (nhan/nc_tu_lai.hieu_chuan)*

Quy trinh TU LAI (khong LLM) chay tron ven tren chuoi TONG_HOP biet truoc edge (`nhan/nc_du_lieu.KICH_BAN`). Hieu chuan HAI chieu: tim ra edge that, KHONG DAT gi tren nhieu va tren bay chi phi.

## 1. Tu lai tron ven (tim quy luat -> mo xe -> quet -> xac nhan -> niem phong)

| chuoi | edge sau phi | luat qua null | ket cuc | chi tiet | danh gia | giay |
|---|---|---:|---|---|---|---:|
| TONG_HOP_NHIEU_1 | KHONG | 0 | KHONG | - | DUNG | 5 |
| TONG_HOP_NHIEU_2 | KHONG | 0 | KHONG | - | DUNG | 6 |
| TONG_HOP_NHIEU_3 | KHONG | 0 | KHONG | - | DUNG | 6 |
| TONG_HOP_HOI_QUY_1 | co | 3 | DAT | NIEM_PHONG_DAT, TRUOT_XAC_NHAN, NIEM_PHONG_DAT | DUNG | 29 |
| TONG_HOP_HOI_QUY_2 | co | 3 | DAT | BAC_BO_KHAM_PHA, NIEM_PHONG_DAT, BAC_BO_KHAM_PHA | DUNG | 15 |
| TONG_HOP_LOC_1 | co | 3 | CHUA_DO_DUOC | CHUA_DO_DUOC_XAC_NHAN, CHUA_DO_DUOC_XAC_NHAN, CHUA_DO_DUOC_XAC_NHAN | CHUA_KET_LUAN | 10 |
| TONG_HOP_XU_HUONG_1 | KHONG | 0 | KHONG | - | DUNG | 5 |

**6 dung · 1 chua ket luan · 0 sai** · bao dong gia 0

## 2. Hoc tu lenh dung/sai (mo xe he goc -> chay lai he da loc tren xac_nhan)

| chuoi | edge | bo loc tim ra | p_null | kv goc xn (bps) | kv loc xn (bps) | hon moc loc xn | danh gia |
|---|---|---|---:|---:|---:|---:|---|
| TONG_HOP_LOC_1 | co | atr_pv < 0.392 | 0.005 | -62.72 | 15.98 | 48.44 | DUNG |
| TONG_HOP_LOC_2 | co | atr_pv < 0.392 | 0.005 | -15.82 | 10.58 | 29.87 | DUNG |
| TONG_HOP_NHIEU_1 | KHONG | rsi2 < 8.988 VA r5_z < -0.7038 | 0.6418 | - | - | - | DUNG |
| TONG_HOP_NHIEU_2 | KHONG | kl_pv >= 0.79 | 0.8159 | - | - | - | DUNG |

## 3. Ti le bao dong gia cua tim_quy_luat tren 30 hat NHIEU THUAN

p_null <= 0,05: **6.7%** (ky vong ~5%) · p_null <= 0,10: **13.3%** (ky vong ~10%)

p tot nhat tung hat (sap xep): [0.025, 0.045, 0.07, 0.09, 0.119, 0.124, 0.313, 0.343, 0.378, 0.383, 0.393, 0.398, 0.502, 0.502, 0.522, 0.522, 0.552, 0.562, 0.582, 0.582, 0.612, 0.627, 0.721, 0.746, 0.746, 0.856, 0.881, 0.95, 0.995, 0.995]

## 4. Cong suat: DO TIM RONG vs GIA THUYET CO CHU DICH (edge yeu, 8 hat HOI_QUY_YEU)

| cach | phat hien | bao dong gia tren NHIEU cung hat |
|---|---:|---:|
| do tim rong (`tim_quy_luat`, ~3.000 dieu kien, p_null <= 0,05) | 3/8 | xem muc 3 |
| mot gia thuyet co chu dich (1 phep thu, t > 1,645) | 8/8 | 0/8 |

Doc: cung mot edge, cung du lieu. Moi dieu kien them vao cuoc do tim nang NGUONG cho moi dieu kien khac. Gia tri cua nha nghien cuu (AI hay nguoi) nam o viec dat IT gia thuyet co co so - khong phai quet nhieu hon.
