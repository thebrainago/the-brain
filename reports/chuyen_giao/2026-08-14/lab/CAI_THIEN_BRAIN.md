# THE BRAIN — ĐÁNH GIÁ & LỘ TRÌNH "HỌC TỪ NGƯỜI ĐI TRƯỚC"

> Ghi 2026-08-11. Mục tiêu: biến The Brain thành kẻ đi sau, liên tục học và kế thừa
> di sản của những người giỏi hơn (đã trả giá, đã thực hành, đã có kết quả), bằng lợi
> thế công nghệ: quét rộng + chạy 24/7.

## 1. ĐIỂM MẠNH ĐÃ CÓ (giữ nguyên, đừng phá)
- Kiến trúc 8 vai + bảng công việc + khoá đơn phiên + retry/BO: kỹ thuật vững.
- Kỷ luật chống overfit thật sự: FDR, placebo, walk-forward, kiểm chéo cặp, ngưỡng PF.
- Kết luận cuối luôn qua MT5 tester (Python chỉ sàng lọc sơ).
- NGUON.md đã phân 5 bậc, ưu tiên "người giỏi đã xác minh" — đúng tầm nhìn.
- Playbook ULTIMA (nguồn thô -> hệ thống sống) đã được mã hoá thành 7 chặng.

## 2. NÚT THẮT LỚN NHẤT (ưu tiên nhất)
- Vai CODER hiện là STUB: chỉ đánh dấu KHONG_ANH_XA rồi dừng.
- Hệ quả: 32 cơ chế -> 22 KHONG_ANH_XA (không test được), 10 CHUA_KIEM. Chỉ có 1 EA
  khung (LuoiDoiXung), nên mọi cơ chế cần logic EA mới đều chết ở đây.
- Cơ chế VÀNG đang dở: "Daily Zone gold TP=50" survey PF 3.93 (win 99.5%) NHƯNG mới chỉ
  là Python trên M5, CHƯA qua MT5 tick. Đừng tin PF 3.93 trước khi test thật.
- Việc hôm nay (ke_hoach_mai.md): test MT5 thật Daily Zone gold TP=50; nếu chưa có EA
  phù hợp thì để vai CODER viết EA MQL5 mới.

## 3. "HỌC TỪ NGƯỜI ĐI TRƯỚC" — lộ trình ưu tiên
Bậc 1-2 trong NGUON.md (người giỏi đã xác minh + nơi thấy hiệu quả thật) vẫn đang ở
trạng thái "cho" (chưa có parser). Chính đó là kho vàng chưa khai thác:
- Prop leaderboard: FTMO, TopStep, Apex, FundedNext, The5ers (public).
- Copy/signal có track record kiểm toán: Collective2, Darwinex D-Live, Myfxbook.
- Sàn đấu vô địch: World Cup (wccta), Robbins, USIC, Trading Cup.
- Chỉ số quỹ CTA: SG CTA, BarclayHedge, NilssonHedge.
Các nguồn này nên là mục tiêu --dan đầu tiên (đã có để dành danh mục NEN_TANG).

## 4. ĐÃ TRIỂN KHAI (2026-08-11)
- VÒNG PHẢN HỒI NĂNG SUẤT NGUỒN: bảng `nguon_hi` ghi mỗi cơ chế kết thúc theo nguồn gốc
  (THAT/AO/KHONG_ANH_XA). `python bo_nao.py --nguon` in bảng xếp hạng nguồn nào thật sự ra
  cơ chế THAT -> não tự biết nên quét lại nguồn nào. Đây là hạt giống "học từ kinh nghiệm".
- Sửa lỗi PowerShell popup: task BrainWatchdog chạy qua wscript ẩn (không loé cửa sổ).
- Restart daemon nạp code mới.

## 5. NƯỚC TIẾP THEO (đề xuất, chưa làm)
1. Biến vai CODER thành thật: sinh EA MQL5 từ mô tả cơ chế (hoặc tạo EA khung thứ 2:
   breakout/mean-revert) để mở khoá 22 cơ chế KHONG_ANH_XA.
2. Xây parser cho bậc 1-2: bắt đầu từ Collective2 + Darwinex + FTMO leaderboard.
3. Dùng nguồn-yield để siết bộ lọc --dan (chỉ quét nguồn có yield cao).
4. Test MT5 thật cho Daily Zone gold TP=50 trước khi tin survey.
