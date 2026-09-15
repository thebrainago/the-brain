# AUDCAD — tổng kết hệ thống (15/09/2026)

## Hệ đã dựng: chuỗi 8 cụm hồi quy trên AUDCAD H4

Quy trình (đúng luật, không lấy đỉnh holdout):
CHỌN trên train 2016-2021 → XÁC NHẬN holdout 2021-2026 → gom cụm → placebo.

- Chọn top-40 train → **16/40 sống** holdout (nền 5,5%) = **7,24× nền**
- 16 hệ = **8 cụm độc lập** (tương quan trung vị 0,173)
- **PLACEBO: 8/8 cụm qua, danh mục p = 0,0000** — edge từ TIMING thật, không
  phải phơi nhiễm. Bằng chứng chắc nhất dự án từng có.

## Đường biên lãi–DD (chạy thật MT5, holdout, vốn 10k micro)

| lot | DD% | lãi đơn %/năm |
|---:|---:|---:|
| 20 | 20,6 | 14,75 |
| **36** | **30,2** | **26,55** ← điểm 27%/năm |
| 45 | 35,3 | 33,18 |
| 60 | ~47 | ~44 |

27%/năm là TRUNG BÌNH; 2022 (-64$), 2024 (-537$) gần hoà — bản chất hồi quy.

## Đường ra tiền LIVE — đã thông đầu-cuối trên demo

Tài khoản demo 345930355 (25k). Đặt lệnh thật khớp (retcode 10009). Chế độ live
gắn vào terminal người dùng (Algo bật). 8 chân đăng ký `b demo`, symbol AUDCAD#
(contract chuẩn, lot chia 100), lot verify 0.1. Điểm 27%/năm = lot 0.9/chân.

## Đã LOẠI (test tử tế, kết quả âm)
- **Khung thấp M15**: placebo danh mục p=0,49 (spread ăn edge). H4 đúng.
- **Chuyển 8 cụm sang cặp khác**: EURGBP/NZDCAD âm ở CHI PHÍ THẬT (Python
  placebo flat-cost lạc quan quá; tester là trọng tài).

## VIỆC TIẾP
1. **EURGBP chọn RIÊNG** (đang chạy train): nếu có danh mục riêng sống + độc
   lập AUDCAD → ghép 2 cặp → nâng Calmar. Scripts đã nhận --ma --khung.
2. **Tăng đòn bẩy** tới mục tiêu (chủ dự án không sợ rủi ro): đổi lot demo.
3. **Chạy nhip định kỳ** (cron mỗi 4h khi bar H4 đóng) để tự động 24/7.
4. Passview: săn Telegram để đọc cách quản lý lệnh AUDCAD người thật.
