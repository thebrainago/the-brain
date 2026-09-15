# AUDCAD khung thấp (M15) — đã test, BỊ LOẠI ở mức danh mục

Chủ dự án: *"với 1 cặp tốt như audcad thử đánh lowtimeframe, tần suất nhanh."*

Chạy đủ pipeline trên M15 (333k nến, 13,4 năm): chọn train → xác nhận holdout →
gom cụm → placebo. So với H4:

| | H4 | M15 |
|---|---|---|
| cơ chế hơn mốc holdout (nền) | 5,5% | **1,2%** (spread giết gần hết) |
| chọn top-40 train → sống holdout | 16/40 = 40% | 17/40 = 42,5% |
| bội số nền | 7,24× | **35×** (nền quá thấp) |
| return@DD20 đỉnh mỗi cụm | +9,97%/năm | **+4,29** (thấp hơn nhiều) |
| **placebo danh mục** | **p = 0,0000 ✅** | **p = 0,49 ❌** |

## Kết luận
Khung thấp trên AUDCAD **KHÔNG cho edge nhanh hơn**. Cơ chế M15 sống qua chọn
lọc nhưng return/rủi ro thấp hơn H4 rõ (spread 1 bps = ~10% biên độ nến M15 vs
0,8% nến H4). Và ở mức DANH MỤC, M15 không qua placebo: lãi đến từ phơi
nhiễm/trôi giá, không phải timing.

8/14 cụm M15 qua placebo riêng lẻ → có edge timing lẻ tẻ, nhưng gộp lại thành
exposure-dominated. Không nên đánh M15.

**H4 vẫn là khung đúng cho AUDCAD** (placebo p=0,0000). Tần suất ~60-120
lệnh/năm mỗi chân là mức spread còn chịu được.
