# QUANTLAB — Ichimoku Cross (tự xây, tự kiểm định)

Ngày: 2026-08-14 · Script: `lab/ichimoku_cross.py` · Dữ liệu: M1 local (Research SP500\data\*_M1_mq.parquet, không cần mạng)

## Giả thuyết (theo for ds.txt)
"2 đường ichi cắt nhau → vào lệnh; tìm khung thời gian + thời gian hold tốt nhất."
Phiên bản 1 (naive): LONG khi giá cắt lên Kijun(26) VÀ Tenkan(9) > Kijun.
Hold cố định 1/3/6/12/24 bar. Có trừ spread (2×spread điểm mỗi lệnh).

## Tự kiểm định
Placebo 100 lần: shuffle vị trí vào lệnh cùng số lệnh → phân phối PnL ngẫu nhiên → p-value = xác suất ngẫu nhiên ≥ thật. Ngưỡng edge: lenh≥20 AND tổng điểm>0 AND p<0.05.

## Kết quả EURCAD
| Khung | Hold | Lệnh | Điểm | Win% | p-value | Đạt? |
|---|---|---|---|---|---|---|
| H4 | 1 | 731 | -25291 | 42.5 | 0.149 | ❌ |
| H4 | 6 | 731 | -58163 | 45.4 | 0.97 | ❌ |
| H4 | 24 | 729 | +19369 | 50.9 | 0.297 | ❌ |
| D1 | 1 | 138 | -10106 | 44.2 | 0.683 | ❌ |
| D1 | 24 | 138 | -15660 | 43.5 | 0.861 | ❌ |

Kết luận: biến thể cross-Kijun+Tenkan (long) KHÔNG có edge trên EURCAD H4/D1 sau tập trừ spread — KHÔNG đưa lên MT5.

## Bước kế tiếp (EVO tự tinh chỉnh)
- Thử biến thể: cắt Tenkan/Kijun, thêm filter SenkouA/B + Chikou, thêm SHORT.
- Thử khung H1, cặp khác trong 8 cặp M1 đã tải.
- Chạy qua autopilot, mỗi cặp 1 lần, tự ghi kết quả.
