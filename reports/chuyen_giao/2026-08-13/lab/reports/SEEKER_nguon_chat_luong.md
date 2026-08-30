# SEEKER — Biên mục NGUỒN CHẤT LƯỢNG (Bậc 1-2 trong NGUON.md)

> Vai: SEEKER · Đợt 1 mở rộng nguồn · Cập nhật: 2026-08-12
> Nguyên tắc: ưu tiên nơi lộ ra hiệu suất THỰC (bằng chứng sống, track record, xếp hạng).
> Cột "Lấy không cần login": `public` = scrape không login · `api` = API công khai ·
> `token` = cần key/đăng ký miễn phí · `login` = cần đăng nhập (KHÔNG vượt CAPTCHA/robots).
> Độ ưu tiên: `1` cao nhất (vào pipeline) → `3` thấp (chờ parser).

---

## 1. Leaderboard quỹ / prop firm (funded trader)

| Tên | URL | Dữ liệu lộ ra | Không cần login? | Ưu tiên | Ghi chú |
|---|---|---|---|---|---|
| FTMO | https://ftmo.com/en/leaderboard/ | Hồ sơ trader funded, % LN, drawdown, payout | public | 1 | Trang chủ bị Cloudflare chặn request thuần (SSL EOF). `api.ftmo.com` phản hồi JSON nhưng trả `NOT_FOUND` mọi endpoint không xác thực → cần parser trình duyệt hoặc xác minh endpoint có auth. |
| TopStep | https://www.topsteptrader.com/leaderboard | Xếp hạng Combine, P&L, equity | public | 1 | Request thuần bị drop (Cloudflare). Cần Playwright/session. |
| Apex Trader Funding | https://apextraderfunding.com/ | Leaderboard funded trader | public | 1 | Cùng họ Cloudflare; chờ parser trình duyệt. |
| FundedNext | https://fundednext.com/ | Leaderboard + payout | public | 1 | Theo dõi cùng cụm prop. |
| The5ers | https://the5ers.com/ | Leaderboard funded trader | public | 1 | Cùng cụm prop. |
| Mở rộng: E8 Funding, FunderPro, Alpha Capital Group, TopTier, Earn2Trade | e8funding.com, funderpro.com, alphacapitalgroup.com, toptiertrader.com, earn2trade.com | Leaderboard + payout | public | 2 | Đã thêm tên vào `keywords_nguon.py` (`prop_firm`). |

## 2. Copy / signal có track record kiểm toán

| Tên | URL | Dữ liệu lộ ra | Không cần login? | Ưu tiên | Ghi chú |
|---|---|---|---|---|---|
| Collective2 | https://www.collective2.com/ | Thư viện chiến lược, return, drawdown, track record | api/login | 1 | Request thuần trả 403 (Cloudflare). Cần login/tiếp cận qua parser trình duyệt. |
| Darwinex D-Live | https://www.darwinex.com/d-live | DARWIN track record kiểm toán (qua broker thật) | api | 1 | **Đã có trong dự án** (`darwinex_ocr.py`, `reports/darwinex_*.json`). Nguồn "đã xác minh" tốt nhất nên khai thác trước. |
| Myfxbook | https://www.myfxbook.com/ | Xếp hạng tài khoản, equity, drawdown, win-rate | api (token miễn phí) | 1 | Request thuần bị chặn (SSL EOF). API `myfxbook.com/api` cần key miễn phí (đăng ký) — không cần vượt CAPTCHA. |
| Mở rộng: ZuluTrade, eToro Popular Investor, MQL5 Signals, FX Blue | zulutrade.com, etoro.com/people, mql5.com/en/signals, fxblue.com | Xếp hạng trader/signal | public/api | 2 | MQL5 Signals track record công khai tốt; eToro Popular Investor public. |

## 3. Sàn đấu vô địch (championship)

| Tên | URL | Dữ liệu lộ ra | Không cần login? | Ưu tiên | Ghi chú |
|---|---|---|---|---|---|
| World Cup of Trading (WCCTA) | https://wccta.com/ | Nhà vô địch Robo-Billionaire, track record | public | 1 | **TEST FETCH: 200 OK** (300KB). Trang chủ landing JS; dữ liệu chi tiết sau render JS hoặc trang con. Fetch nền được. |
| Robbins World Cup | https://www.robbinscta.com/ | Champion + equity | public | 1 | Cùng họ "world cup"; cần cập nhật URL chính xác. |
| US Investing Championship (USIC) | https://usic.org/ | Top trader, % return theo division | public | 1 | Request thuần lỗi SSL EOF (chặn). Cần parser trình duyệt. |
| Trading Cup | https://www.tradingcup.com/ | Xếp hạng, return chiến lược | public | 1 | **TEST FETCH: 200 OK**; trang `/signals` cùng 200 (198KB, có token %). FETCH ĐƯỢC. |
| Mở rộng: TradingView House Cup, Hungarian Trading Championship, RoboForex/Exness/Alpari contests | tradingview.com, mcsi.hu, roboforex.com | Nhà vô địch + xếp hạng | public | 2 | Đã thêm vào `keywords_nguon.py` (`san_dau`). |

## 4. Chỉ số quỹ CTA / managed futures

| Tên | URL | Dữ liệu lộ ra | Không cần login? | Ưu tiên | Ghi chú |
|---|---|---|---|---|---|
| SG CTA Index | https://www.sgindex.com/ | Chỉ số CTA/Trend, return theo tháng | public | 1 | Request thuần trả 403 (Cloudflare). Nên lấy bản dữ liệu Excel/PDF công khai thay vì trang JS. |
| BarclayHedge | https://www.barclayhedge.com/ | Barclay CTA Index, managed futures | public | 1 | **TEST FETCH: 200 OK** (154KB). FETCH ĐƯỢC. |
| NilssonHedge | https://nilssonhedge.com/ | CTA ranking, quỹ top | public | 2 | Request thuần trả 403. |
| Mở rộng: Eurekahedge, HFRI, Solactive CTA, UIS Managed Futures | eurekahedge.com, hfri.com, solactive.com | Hedge fund / CTA index | public/token | 2 | Đã thêm vào `chi_so_cta` trong keywords. |

## 5. Học thuật / định lượng

| Tên | URL | Dữ liệu lộ ra | Không cần login? | Ưu tiên | Ghi chú |
|---|---|---|---|---|---|
| arXiv q-fin | https://arxiv.org/list/q-fin/ | Bài báo quantitative finance | public/api | 1 | Có API công khai (export, rss) — fetch tốt. |
| SSRN | https://papers.ssrn.com/ | Working paper tài chính | public | 1 | Có trang abstract; một số PDF cần điều kiện. |
| QuantConnect Community | https://www.quantconnect.com/forum | Backtest/chiến lược nghiệp dư + chuyên | public/login | 1 | Forum public; submission cần login. Đã có profile trong `web_registry`. |
| Numerai | https://numer.ai/ | Tournament ranking, signal quality | api | 1 | API công khai; cần đăng ký tài khoản lấy token. |
| Kaggle | https://www.kaggle.com/competitions | Chiến thắng giải ML tài chính | public | 2 | Notebook/leaderboard public; dataset tuân giấy phép. |
| Reddit r/algotrading | https://www.reddit.com/r/algotrading/ | Thảo luận + bài học thuật/hướng dẫn | public/api | 2 | Đã có `nguon_reddit.py`. Dùng API JSON (không spam). |

## 6. Diễn đàn / professional (tự tìm thêm — 10 nguồn)

| Tên | URL | Dữ liệu lộ ra | Không cần login? | Ưu tiên | Ghi chú |
|---|---|---|---|---|---|
| ForexFactory | https://www.forexfactory.com/ | Lịch kinh tế, diễn đàn, hệ thống | public | 2 | Diễn đàn tranh luận hệ thống; lịch kinh tế vĩ mô. |
| EliteTrader | https://www.elitetrader.com/ | Diễn đàn trader chuyên sâu | public | 2 | Trader kinh nghiệm chia sẻ phương pháp. |
| BabyPips | https://www.babypips.com/ | Học forex + diễn đàn | public | 3 | Giáo dục nền tảng, ít track record thật. |
| MQL5 Signals/CodeBase | https://www.mql5.com/en/signals | Track record signal + EA top | public/api | 1 | Track record công khai, filter theo profit. |
| eToro Popular Investor | https://www.etoro.com/people/ | Xếp hạng nhà đầu tư nổi bật | public | 2 | Leaderboard copy trader. |
| ZuluTrade | https://www.zulutrade.com/ | Xếp hạng tín hiệu + track record | public/login | 2 | Cùng họ copy/signal. |
| QuantStart | https://www.quantstart.com/ | Hướng dẫn/bài viết quant | public | 3 | Giáo dục quant chất lượng cao. |
| Quantocracy | https://quantocracy.com/ | Tổng hợp blog quant | public | 3 | Aggregator nhiều blog quant. |
| TradingView House Cup | https://www.tradingview.com/house-cup/ | Nhà vô địch hàng năm | public | 2 | Sàn đấu. |
| MoneyShow Top Traders | https://www.moneyshow.com/ | Phân tích từ trader nổi bật | public | 3 | Quan điểm; ưu tiên thấp. |

---

## KẾT QUẢ TEST FETCH THẬT (2026-08-12, `requests` thuần, tôn trọng robots — KHÔNG vượt CAPTCHA)

| Nguồn | URL | Kết quả | Diễn giải |
|---|---|---|---|
| FTMO leaderboard | https://ftmo.com/en/leaderboard/ | ❌ SSL EOF (Cloudflare) | Trang web chặn IP/UA thuần. `api.ftmo.com` phản hồi JSON nhưng trả `NOT_FOUND` mọi endpoint thử → không có feed leaderboard công khai ở mức này. |
| Myfxbook | https://www.myfxbook.com/community/outstanding | ❌ SSL EOF (Cloudflare) | Chặn request thuần. Đường API `myfxbook.com/api` cần key miễn phí (đăng ký), không cần vượt CAPTCHA — khả thi khi đăng ký hợp lệ. |
| Collective2 | https://www.collective2.com/ | ❌ 403 (Cloudflare) | Cần login/session trình duyệt. |
| TopStep | https://www.topsteptrader.com/leaderboard | ❌ RemoteDisconnected | Chặn request thuần. |
| **WCCTA** | https://wccta.com/ | ✅ **200 OK** | Fetch được bằng request thuần. Trang chủ landing JS; dữ liệu champion/equity sau render. |
| **Trading Cup** | https://www.tradingcup.com/ + `/signals` | ✅ **200 OK** | Fetch được; `/signals` trả data có token % (leaderboard). Sẵn sàng parser. |
| **BarclayHedge** | https://www.barclayhedge.com/ | ✅ **200 OK** | Fetch được bằng request thuần. |
| SG Index | https://www.sgindex.com/ | ❌ 403 | Chặn; lấy dữ liệu chỉ số từ file Excel/PDF công khai. |
| NilssonHedge | https://nilssonhedge.com/ | ❌ 403 | Chặn request thuần. |
| USIC | https://usic.org/ | ❌ SSL EOF | Chặn. |
| Darwinex D-Live | (đã có trong dự án) | ✅ Đã triển khai | `darwinex_ocr.py` + `reports/darwinex_*.json` đang hoạt động. |

**Kết luận fetch:** Request thuần fetch được **WCCTA, Trading Cup, BarclayHedge** (và Darwinex đã có sẵn). Các leaderboard prop (FTMO/TopStep/Apex/FundedNext/The5ers), Collective2, Myfxbook, SG/Nilsson bị Cloudflare chặn → cần parser trình duyệt (Playwright, `vao_web.py` + profile trong `web_registry.json`) hoặc dùng API có token. Tuân thủ quy tắc: KHÔNG vượt CAPTCHA, KHÔNG spam.

## Khuyến nghị đưa vào pipeline (đợt sau)
1. **Darwinex** (đã có) + **TradingCup `/signals`** + **WCCTA** — parser request thuần trước, nhanh nhất.
2. **BarclayHedge** — parser request thuần cho chỉ số CTA.
3. **Myfxbook API** — đăng ký token miễn phí (không vượt CAPTCHA) để lấy track record kiểm toán.
4. **FTMO/TopStep/Collective2** — parser trình duyệt (Playwright) khi có session đã đăng nhập, theo `web_registry.json`.
