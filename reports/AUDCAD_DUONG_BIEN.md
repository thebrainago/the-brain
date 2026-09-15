# AUDCAD - đường biên lãi–sụt giảm của chuỗi 8 cụm

Holdout 2021-03-19 → 2026-07-29 (5,36 năm), lot micro / vốn 10.000 USD.
Đo bằng chạy thật MT5 (đường biên tuyến tính với lot đã xác nhận ở lot 15 và 36).

| lot | DD% thật | lãi USD | lãi đơn %/năm | CAGR %/năm |
|---:|---:|---:|---:|---:|
| 5 (gốc) | 6,60 | 1.977 | 3,69 | 3,42 |
| 15 (×3) | 16,70 | 5.930 | 11,06 | 9,07 |
| 20 | 20,65 | 7.906 | 14,75 | 11,48 |
| **36** | **30,16** | **14.232** | **26,55** | 17,95 |
| 45 | 35,32 | 17.789 | 33,18 | 21,00 |

**Điểm vận hành chốt (chủ dự án 15/09): lot 36 → ~27%/năm ở DD 30,16%.**
Tài khoản KHÔNG stop-out ở mức này (đã chạy thật).

## Ba điều phải nói kèm
1. Cột `%/nam@DD20` là **bất biến** của hệ (~Calmar 0,5) — nhân lot KHÔNG làm
   nó lớn lên, chỉ đưa DD thật tới gần 20%. Nhân ×3 cho 11%/năm, không phải 27%.
2. DD 30% = có lúc tài khoản mất 30% thật. Đó là rủi ro, không phải con số giấy.
3. 8 cụm chọn trên TRAIN (2016-2021) rồi xác nhận HOLDOUT, nhưng việc GOM CỤM
   dùng tín hiệu HOLDOUT → rò rỉ nhỏ. Chưa chạy placebo trên chính 8 cụm.

## Ổn định theo thời kỳ (lot 36, holdout)

Cả hai nửa holdout đều dương → KHÔNG phải hiện tượng một thời kỳ:
- nửa đầu 2021-03 → 2023-11: ~21%/năm
- nửa sau  2023-11 → 2026-07: ~32%/năm

**Nhưng lãi KHÔNG đều theo năm** — 27%/năm là trung bình, không phải đều:

| năm | lãi USD (lot 36) |
|---|---:|
| 2021 | +1.354 |
| 2022 | **−64** (gần hoà) |
| 2023 | +4.599 |
| 2024 | **−537** (âm nhẹ) |
| 2025 | +4.987 |
| 2026 (½) | +3.894 |

Hai năm gần hoà/âm; lãi dồn vào 2023/2025/2026. Bản chất hồi quy trên cặp chéo:
năm AUDCAD trending thì mean-reversion thua. Vào đúng 2022 hoặc 2024 thì cả năm
không lãi mà vẫn chịu DD.

## Việc kiểm định còn thiếu (trước khi ra tiền thật)
- Placebo/null trên chính 8 cụm (chưa chạy).
- 8 cụm chọn trên TRAIN nhưng GOM CỤM dùng tín hiệu HOLDOUT (rò rỉ nhỏ).
- Tất cả trên MỘT tài sản, MỘT khung.
