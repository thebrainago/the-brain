# KIEM KE NGUON / DIEN DAN (03/10/2026 toi, tu code + lich su git; chu du an nho ">40 nguon" - DUNG, con nguyen trong code)

Khong mat. Danh sach nam trong **code**, khong phai file du lieu: tong **71 nguon da dang ky** + **19 ung vien dien dan quoc gia** (do 15/09).
Bang `nguon` trong `nao.db` (lich su thu hoach) moi la thu MAT cung may cu; `dang_ky_nguon()` (`tru/seeker.py`) dang ky lai tu code khi chay `mot_luot`.

| Nhom | Noi khai bao | So luong | Ma |
|---|---|---|---|
| API / keyword (khong can dang nhap) | `tru/seeker.NGUON` | 14 | arxiv, blog, crossref, etoro, fxblue, github, hackernews, lean_algo, mql5_code, openalex, quantconnect, semantic, stackexchange, tradingview_pine |
| Trinh duyet / can dang nhap | `tru/seeker.NGUON_TRINH_DUYET` | 23 | cnblogs_trung, collective2, darwinex, elitetrader, facebook, habr_nga, mql5_bai_viet, mql5_ma_expert, mql5_signals, myfxbook, paperswithcode, qiita_nhat, quantconnect_forum, quantpedia, reddit_td, smartlab_nga, tiktok, tradingview_ideas, tradingview_scripts, velog_han, x, youtube, zulutrade (+ `telegram` rieng) |
| RSS blog | `nhan/nguon_bai_viet.FEEDS` | 27 | allocatesmartly, alphaarchitect, alvarezquant, buildalpha, fh_financial_hacker, followingthetrend, gestaltu, hangukquant, headlandstech, mql5_articles, mrzepczynski, newtraderu, priceactionlab, qoppac, quantdare, quantinsti, quantitativo, quantpedia_blog, quantumtrading, reddit_algotrading(+_nam), reddit_quant, robotwealth, thinknewfound, tr8dr, tradingmarkets, tradingview_blog |
| Trang (khong RSS, da ngon ngu) | `nhan/nguon_bai_viet.TRANG` | 7 | fxon (ja), mql5_forum_ru (ru), note_fx (ja), quantifiedstrategies, smartlab_blog (ru), thaiforexschool (th), traderviet (vi) |
| Dien dan (cu) | `nguon_dien_dan.py` | 6 | futures.io, traderslaboratory, forexfactory, quant.stackexchange, smart-lab, traderviet |
| Ung vien dien dan QUOC GIA | `_do_dien_dan_quoc_gia.py` -> `reports/DIEN_DAN_QUOC_GIA.json` | 19 | do 15/09 tren MAY CU: vao duoc 7 (mql5_forum_ru 106 link, traderviet 89, thaiforexschool 55, note_fx 50, fx-on 28, smartlab_blog); KHONG vao duoc 11: arabictrader (ar), wallstreet-online (de), forexfactory + babypips (en), gogojungle (ja), forex-nawigator (pl), mmgp (ru), pantip (th), forexforum.com.tr (tr), fx168 (zh); kaskus (id) vao duoc nhung 0 link |
| Telegram ung vien | `config/nguon_ung_vien.json` | 26 | kenh tin hieu / EA (ForexFreeEA, pinescripter...) |
| Blog tu tim | `config/nguon_tu_tim.json` | 29 | |

## Lo hong so voi yeu cau "moi quoc gia >= 1 dien dan"
- Da co: vi (traderviet), ru (mql5 ru, smart-lab, habr), ja (fx-on, note, qiita, gogojungle*), th (thaiforexschool), zh (cnblogs; fx168*), ko (velog), en (nhieu).
- Chua co / chua vao duoc: ar, de, pl, tr, id, es, pt, fr, it, hi, ... va 11 trang bi "KHONG_VAO_DUOC" o may cu. **Do lai tu may nha (co the nha mang / IP cu la nguyen nhan; thu them WARP)** truoc khi ket luan chet.

## Viec port can lam (cloud giao, nha chay)
1. Cong cu cu ghi cung `C:\Users\SV STORE\...`, CDP 9222, IMAP `config/email_cong_tac.json`: chuyen sang CDP 9224 + `.browser_thebrain` (`mo_trinh_duyet_ai.cmd`); doc ma xac minh trong Gmail thebrainago ngay trong trinh duyet.
2. `NGUON_TRINH_DUYET` (23) doc qua trinh duyet: can dang nhap tung site (Sign in with Google neu co).
3. Lich quet: 1 tuan / lan (`config/tan_so_quet.json`); trang nhieu page: doc so trang, qua lan luot, nho moc.
