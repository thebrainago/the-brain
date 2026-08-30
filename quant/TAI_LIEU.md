# TÀI LIỆU QUANTLAB — KHO TƯ LIỆU & CÔNG CỤ

> Cập nhật: 2026-08-12 · Người dùng gửi 2 nguồn: link Drive (tài liệu quant) + GitHub pseud.
> Đây là bước "SEARCHER" của Quantlab: thu thập công trình/giả thuyết của người khác, rồi tự sinh + kiểm định giả thuyết riêng.

## 1. TÀI LIỆU DRIVE → `quant/tai_lieu_drive.pdf` (298 trang)
- **Đúng là cuốn "Finding Alphas — A Quantitative Approach to Building Trading Strategies" (2nd ed.)**, biên tập bởi **Igor Tulchinsky** (WorldQuant Virtual Research Center), NXB Wiley.
- Đây là **cuốn sách nền** về quy trình tìm alpha: cách phát biểu 1 giả thuyết định lượng, đặc tả bằng code (WorldQuant **Formulaic Alphas**), đo lường (IC, Sharpe, turnover, drawdown), và tránh overfit/regime shift.
- Bản text đã trích: `quant/finding_alphas_text.txt` (≈646 KB) — dùng làm nguồn tra cứu/từ khoá.
- **Áp dụng vào The Brain:** quy trình trong sách (giả thuyết → code → kiểm định → lọc → out-of-sample) trùng với pipeline `co_che_*.py` của Quantlab. Bổ sung: nên thêm đo lường **IC (Information Coefficient)** và **turnover** — hiện `metrics.py` mới có Sharpe/PF/Calmar/MaxDD.

## 2. GITHUB `PVinh-Quant/pseud` → `quant/thu_vien/pseud/`
- **pseud = "Quantitative OHLCV Anomaly Researcher"**: hệ thống AI nghiên cứu **dị biệt thống kê** từ dữ liệu nến **1-phút (OHLCV)** rồi **sinh giả thuyết kinh tế định lượng** bằng LLM + **Swarm đa-agent phản biện** (Advocate/Critic/Risk).
- Kiến trúc (đáng học nhất):
  1. **Quantitative Filter** (Polars/Rust): Moment Shift (skew/kurtosis), Volatility Jump (Garman-Klass & Parkinson), Volume-Price divergence. Dùng **Robust Z-score (Median/MAD)** — miễn nhiễm outlier, ngưỡng |Z|>2.0. Nén ~1 triệu dòng → 10–40 tín hiệu.
  2. **LLM sinh giả thuyết** (Gemini/OpenAI) từ các dị biệt đã lọc.
  3. **Swarm Review Tribunal** phản biện → verdict (APPROVED / APPROVED_WITH_CAUTION / REJECTED).
- File đã lưu: `pseud.zip` (172 MB), `pseud_tree.json`, `pseud_repo.json`, source đã giải nén trong `quant/thu_vien/pseud/`.
- **Ý tưởng vay mượn cho The Brain:**
  - Cơ chế **Robust Z-score (Median/MAD)** để phát hiện dị biệt → thêm 1 cơ chế Quantlab mới.
  - Quy trình **"sinh giả thuyết → phản biện đa góc nhìn"** trùng với vai EVO — nên dùng EVO làm "Review Tribunal" cho các giả thuyết do Quantlab/Seeker đề xuất.
  - Dữ liệu 1-phút → cần MT5 tick (khớp kế hoạch đưa chiến lược lên MT5 tester).

## 3. HƯỚNG TÌM THÊM CÔNG TRÌNH (roadmap Searcher)
- **Diễn đàn nghiên cứu định lượng chuyên nghiệp:** QuantConnect forum, Quantopian Lectures (đã đóng, còn archive), Wilson Quant, Quantstart, Reddit `r/algotrading` + `r/quantfinance`, Elite Trader (professional subsection).
- **Công trình/giả thuyết có công bố:** SSRN (quant finance working papers), arXiv `q-fin` (quantitative finance), Journal of Portfolio Management, SSRN "alpha" preprints.
- **Nguồn công thức alpha:** WorldQuant BRAIN (Formulaic Alphas), `pseud` (đã có), các repo public "alpha research" trên GitHub (tìm từ khoá `formulaic alpha`, `factor research`, `trading hypothesis`).
- **Tự sinh giả thuyết:** xem `quant/KET_QUA_ichimoku_cross.md` — ví dụ đã làm: "2 đường Ichimoku cắt nhau → vào lệnh, giữ bao lâu/tp bao nhiêu tốt nhất" (EURUSD hold 3 nến D1 thắng buy&hold).

## 4. KIỂM ĐỊNH GIẢ THUYẾT — QUY TRÌNH HIỆN TẠI
1. **Sàng lọc Python cấp 1** (`quant/tim_*.py`, `co_che_*.py`): dữ liệu D1 Yahoo, trừ spread+swap, so buy&hold.
2. **Nếu có edge** → đưa lên **MT5 Strategy Tester (dữ liệu tick)** để test khung intraday + đo độ trễ vào lệnh thật.
3. **Trước khi tin**: walk-forward / out-of-sample, không tinh chỉnh tham số trên cùng bộ dữ liệu đã tìm ra.
---
*Trạng thái: 2 nguồn đã thu về + đọc. Bước tiếp: trích IC/turnover vào `metrics.py`, thử cơ chế Robust Z-score, dùng EVO làm Review Tribunal.*
