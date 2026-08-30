# NGUON.md - Registry nguon THE BRAIN (phan 1 cua QUY_TRINH)

> Chuẩn duy nhất cho phần NGUỒN. Đọc kèm `KHUNG.md`. Cập nhật liên tục theo SOURCE LOOP.
> Cột "truy cập": api = API công khai · public = scrape trang không cần login ·
>             login = cần đăng nhập (Playwright, bạn đăng nhập 1 lần) · tay = người dùng dán.

## 0. THỨ TỰ ƯU TIÊN (5 bậc)
1. NGUỜI GIỎI ĐÃ XÁC MINH (quỹ/trader có tài liệu + track record thật) — mô phỏng trước.
2. NƠI THẤY ĐƯỢC HIỆU QUẢ THẬT (sàn đấu, xếp hạng, prop leaderboard, copy/signal, chỉ số quỹ).
3. THƯ VIỆN CODE + CHIẾN LƯỢC RÕ RÀNG (GitHub, MQL5, TradingView, QuantConnect, Amibroker...).
4. QUAN ĐIỂM / THẢO LUẬN MƠ HỒ (Reddit, RSS, blog) — chỉ nâng khi có bằng chứng sống.
5. PASSVIEW/LỊCH SỬ TÌM THẤY LUNG TUNG (FB...) — BẬC THẤP NHẤT, KHÔNG ƯU TIÊN.
   (Ngoại lệ duy nhất: chủ CHỦ ĐỘNG công khai + có bằng chứng về bản thân -> mới nâng lên REVERSER.)

## 1. BẬC 1 - NGUỜI GIỎI (seed; SOURCE LOOP bổ sung liên tục)
- Quỹ hệ thống: Winton(Harding) · AHL/Man · AQR(Asness) · Campbell & Co · Dunn · John W. Henry ·
  Systematica(Leda Braga) · Transtrend · CTA đã lâu năm.
- Academic/factor: Fama-French(Ken French data library) · momentum(Jegadeesh-Titman) · low-vol.
- Trader hệ thống: Turtle(Dennis/Eckhardt) · Ed Seykota · Larry Hite · Bill Dunn ·
  Andrea Unger · Kevin Davey · Andreas Clenow · Ernest Chan · Robert Carver · Michael Dever.
- Trader momentum/price-action: Mark Minervini · David Ryan · Peter Brandt.
- SOURCE LOOP: tu dong quet "top trader <nam>", champion moi, CTA/quant moi, ghi vao `reports/NGUOI_GIOI.md`.

## 2. BẬC 2 - NƠI THẤY HIỆU QUẢ THẬT (sàn đấu + nền tảng công khai)
### Sàn đấu / championship
| Nguồn | Theo dõi | Truy cập |
|---|---|---|
| World Cup of Automated Trading (wccta.net) | champion + track record | public |
| Robbins World Cup Futures Championship | champion + equity | public |
| US Investing Championship (USIC) | top traders | public |
| Trading Cup (tradingcup.com) | xếp hạng | public |
| Hungarian Trading Championship | xếp hạng | public |
| RoboForex / Exness / Alpari contests | xếp hạng | api/public |
| MoneyShow Top Traders | top | public |
| TradingView House Cup (TTHC) | nhà vô địch | public |
| StockCharts contests | top | public |
| Swissquote / OANDA comps | xếp hạng | public |

### Prop firm leaderboard (funded traders)
| Nguồn | Xem | Truy cập |
|---|---|---|
| FTMO leaderboard | funded profile + track | public |
| TopStep Trader Combine | leaderboard | public |
| Apex Trader Funding | leaderboard | public |
| FundedNext | leaderboard | public |
| The5ers | leaderboard | public |
| E8 Funding | leaderboard | public |
| FunderPro | leaderboard | public |
| Alpha Capital Group | leaderboard | public |
| Earn2Trade | leaderboard | public |
| TopTier Trader | leaderboard | public |

### Copy-trading / signal / xếp hạng trader
| Nguồn | Xem | Truy cập |
|---|---|---|
| Collective2 (C2) | thư viện chiến lược + kết quả | public/api |
| Darwinex D-Live | DARWIN track record kiểm toán | api |
| eToro Popular Investor | leaderboard | public |
| ZuluTrade | leaderboard | public |
| Myfxbook AutoTrade | xếp hạng | api/public |
| FX Blue | xếp hạng | api/public |
| MQL5 Signals | track record signal | public |
| MQL5 Market | EA top bán | public/api |
| CopyFX (RoboForex) | xếp hạng | public |
| Signal Start | signal | public |
| Peak Index | leaderboard | public |
| Binance / OKX / Bybit copy trade | top trader crypto | api/public |

### Chỉ số quỹ / managed futures / hedge fund
| Nguồn | Xem | Truy cập |
|---|---|---|
| SG CTA / SG Trend Index | chuẩn ngành trend | public |
| BarclayHedge CTA Index | chuẩn ngành | public |
| NilssonHedge | CTA ranking | public |
| Eurekahedge / HFRI | hedge fund index | public |
| HFM Awards | top quỹ | public |
| Bloomberg/Reuters Top 50 HF | top quỹ | public |

### Thi đấu định lượng
| Nguồn | Xem | Truy cập |
|---|---|---|
| QuantConnect competitions | chiến lược thắng | public |
| Kaggle | thắng giải | public |
| Numerai tournament | chiến lược ranking | public |
| WorldQuant BRAIN WebSim | backtest + ranking | public |
| Alpaca challenges | thắng giải | public |
| QuantInsti contests | thắng giải | public |
| Optiver / Jane Street / IMC / Two Sigma comps | thắng giải | public |

## 3. BẬC 3 - THƯ VIỆN CHIẾN LƯỢC CÓ CODE
GitHub · MQL5 CodeBase/Market · TradingView community · QuantConnect LEAN ·
Quantstart · Quantocracy · Amibroker library · TradeStation EasyLanguage ·
NinjaTrader NinjaScript · MultiCharts · StrategyQuant · fxDreema · Quantpedia ·
Quantopian (archive) · Freqtrade · Backtrader · VectorBT · SSRN/arXiv q-fin ·
Fama-French data library · CME/CBOE research.

## 4. BẬC 4 - QUAN ĐIỂM / THẢO LUẬN
Reddit (algotrading/quant) · RSS (Investopedia quant, Quantocracy, SSRN top) ·
HuggingFace models/papers · blog tác giả bot · clip YouTube (yt-dlp phụ đề).
Chi nang uu tien khi co bang chung song hoac tham so cu the.

## 5. BẬC 5 - PASSVIEW LUNG TUNG (FB, copytrade tim thay bong)
- Khong uu tien, khong dua thang vao pipeline.
- Neu co them bang chung (ten that, bai viet, thoi gian ton tai) -> SCOUT cho qua lam tham khao.
- Passview tu nguoi CHU DONG cong khai + xac minh -> REVERSER do nguoc.

## 6. CACH CAO (nguyen tac)
- Python orchestrator cao (khong de LLM cao). timeout ngan, ngu giua request, certifi het SSL.
- API giong public -> requests; trang JS nang -> Playwright (ban dang nhap 1 lan giu phien);
  video -> yt-dlp; trang can login khong cong khai -> chi khi chu dong y (khong hack).
- Phan cap du lieu: nguon tho(jsonl) -> muc -> co_che(0-12) -> cong_viec -> ket luan.
- Chi co_che >= 8 vao hang doi kiem chung.

## 7. LOAI CHIEN LUOC (de dinh tuyen dung)
- Macro-dong tien (T-bill, credit spread, M2, FOMC) -> doc du lieu vi mo -> luat -> mo phong.
- Macro-breadth (nhom nganh chi phoi > X% da tang -> ngung buy) -> do breadth -> luat ngat.
- Mua vu (seasonal: thang/tuan/le/chu ky bau cu) -> kiem dinh theo chu ky tren M1.
- Cross-asset (vang-USD, dau, trai phieu) -> luat tuong quan -> mo phong.
- Ky thuat xu huong (breakout, MA, Donchian) -> MAPPER -> TEST.
- Dong luong (time-series / cross-sectional) -> factor -> mo phong.
- Hoi quy trung binh (RSI, Bollinger, z-score) -> MAPPER -> TEST.
- Chi bao (Supertrend, ATR, EMA, MACD...) -> TAI VE KIEM DINH TRUC TIEP.

## 8. SOURCE LOOP (tim "nguoi moi" lien tuc)
- Chay dinh ky 24/7: quet "top trader <nam>", champion moi, prop leaderboard moi,
  CTA/quant moi, "best algorithmic trading <nam>".
- Moi ten moi: XAC MINH nang luc truoc (track record, bai viet, code) roi moi vao pipeline.
- Ghi registry `reports/NGUOI_GIOI.md` tu cap nhat.
- Khong tin ten "tu xung"; uu tien nguon do luong duoc ket qua.