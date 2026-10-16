# SP500 — Quant research framework (CFD index trading edges)

Tập trung toàn bộ chiến lược để bóc tách SP500. Dữ liệu gốc (parquet, báo cáo, code trên máy nhà) đã mất; thư mục này lưu lại **toàn bộ tri thức/kết quả còn giữ được** từ ghi chú dự án (cập nhật tới 2026-09).

| File | Nội dung |
|---|---|
| [overview.md](overview.md) | Mục tiêu, hạ tầng, framework Python, EA MQL5, phát hiện đã xác nhận, việc sắp tới |
| [methodology-and-standards.md](methodology-and-standards.md) | Chuẩn PASS chiến lược, 3 tầng thống kê, nguyên tắc rút ra, danh sách bug đã sửa |
| [research-log.md](research-log.md) | Nhật ký kết quả chi tiết: audit 2026-07-14, edge sống sót, ZigZag V-Reversion, mùa vụ, sinh tồn vốn |
| [related-systems.md](related-systems.md) | ONL DCA v2.0, Project Bien Do, UK100 pipeline, GEX scanner, DongDongTV EA, Sierra Chart/Rithmic |

Kết luận ngắn (SP500, sau ~2.3M giả thuyết, 3-4 tầng lọc): chỉ còn
1. Pivot_H1_S1 / breakout_up / E=+0.3 / SL=4.0xATR / TP 1.0–1.4xATR (5 combo), đã qua stats + economics + placebo + era-check.
2. Mùa vụ 56 năm daily (15 CHẶT + 11 VỪA) dùng làm bias hướng, không phải entry độc lập.
Bổ sung: ZigZag V-Reversion (tần suất thấp, phần lớn LONG là drift-harvesting).
