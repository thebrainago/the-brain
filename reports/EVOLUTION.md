# EVOLUTION - SUC KHOE DAY CHUYEN
*2026-09-14 20:10:16*

> Do bang SUC KHOE, khong do bang so PASS. Mot he lanh manh hieu chuan tot ke ca khi tim duoc it edge.

## 1. Bon tru
| Tru | Lan cuoi | Tre | Trang thai |
|---|---|---|---|
| SEEKER | 2026-09-14 19:59:34 | 10 phut | nghi |
| QUANTLAB | 2026-09-14 20:10:10 | 0 phut | chay |
| NGHI | 2026-09-14 19:01:29 | 68 phut | nghi |
| BANKER | 2026-09-14 19:55:40 | 14 phut | nghi |
| EVO | 2026-09-14 20:10:16 | 0 phut | chay |

## 2. San luong
- Tai lieu da thu: **11848**
- Gia thuyet: {"CO_CO_CHE": 1, "FAIL": 376, "PASS": 3, "QUARANTINED_V2": 7}
- Gia thuyet co ket qua cuoi: **380** (chua 904 dong lich su da supersede, invalidated hoac quarantine)
- Viec: cho 31 / treo 0 / loi 0
- Ty le vong lap rong cua SEEKER: **86%**
- Nang suat doc cua SEEKER: **0.16 gia thuyet/100 bai** (4 gia thuyet truy nguyen ve URL tai lieu, tren 2442 bai da boc; 678 ung vien tu 8087 artifact tai lieu). Noi sinh khong tinh vao day: 383 gia thuyet.
- Thanh phan thu hoi duoc tu ban doc: **285** (186 viet ra duoc bang ngu phap hien tai). Day la phan giu lai tu nhung he KHONG qua cong.
- Do sau quet (con tro bien gioi): etoro 0 trang/vong 0, mql5_code 6 trang/vong 0, tradingview_scripts 0 trang/vong 0

## 3. Hieu chuan (thu quan trong hon so PASS)
- **Null factory: 50% ca KHONG CO EDGE lot qua cong** (do luc 2026-09-14 18:52:38, muc tieu <= 10%)
  Day la phep do hieu chuan DUY NHAT dang tin: cho thu khong co edge di qua ca day chuyen roi dem xem bao nhieu lot.
- **Bai kiem LUC: cong PHAN BIET DUOC co edge voi khong co edge** (do luc 2026-09-14 18:52:40)
  Hai phep do phai doc CUNG NHAU: 'null lot 0%' mot minh khong phan biet duoc mot cong hieu chuan tot voi mot cong tu choi tat ca.
  - biet truoc 0.5 cua so lan -> `FAIL` (sharpe -2.692)
  - biet truoc 0.55 cua so lan -> `FAIL` (sharpe -0.096)
  - biet truoc 0.6 cua so lan -> `NGHI_NHIN_TRUOC` (sharpe 2.972)
- (tham khao) p placebo cua 108 ung vien: trung vi 0.36, ty le p<=0,05 la 19.4%
  KHONG dung so nay lam hieu chuan: ung vien da bi chon loc tren train nen p cua chung LE RA phai lech thap.
- FDR online: 3/284 gia thuyet bi bac bo (dem theo gia thuyet, bo dong da supersede)
  - hang so cai cua duong KHAM PHA: 35 (mot gia thuyet co the co nhieu hang: chay lai, doi the he cong)
  - hang cua DUNG CU DO, khong phai kham pha: 1101 (do_luc, do_mde, do_mde2, null_hieu_chuan, test_che_do, thu_luc_cong) - khong sinh khang dinh nao va khong lam chat nguong cua ho kham pha (LORD dem `j` theo tung epoch rieng)
  - hang trong EPOCH DA CHET (khoa `ho` cu truoc ngu phap fdr-v2): 675 - khong ho song nao ke thua chung, nen chung khong lam chat nguong cua ai
- Dong bo ba tang: **KHOP** (trung suat trong epoch song: 0, hang FDR mo coi ghi tu 01/09: 0)
  - 23 hang cu khong doi soat duoc theo cau tao (ghi truoc khi co cot `gt_ma_nguon`), khong tinh vao bat bien
  - 96 gia thuyet FAIL TRUOC buoc FDR nen khong tieu suat nao - day la thiet ke 'cong re truoc placebo', khong phai lech so sach
  - 131 truong hop trung suat nam TRON trong cac epoch da chet (15-16/08, truoc khi lord_v2 chong trung)

## 4. Tai nguyen + toan ven
- **Thoi gian song 7 ngay: 100.0%** (mat 164.9 gio qua 2 lan gian doan - may ngu hoac tat, khong phai tru chet)
- Supervisor restart 24h: **0 lan** (do duoc, khong lan nao)
- Dia trong: **28.0 GB** - MT5 tick-test: **GO**
- So cai: LANH (18569 dong lien mach)

## 5. Nguon
| Nguon | Lan goi | Loi | Thu hoach | Trang thai |
|---|---|---|---|---|
| arxiv | 44 | 0 | 241 | BAT |
| blog | 39 | 0 | 39 | BAT |
| cnblogs_trung | 3 | 0 | 72 | BAT |
| collective2 | 4 | 0 | 12 | BAT |
| crossref | 27 | 0 | 1465 | BAT |
| darwinex | 3 | 0 | 39 | BAT |
| elitetrader | 2 | 0 | 30 | BAT |
| etoro | 6 | 0 | 100 | BAT |
| facebook | 5 | 0 | 15 | BAT |
| fxblue | 7 | 0 | 103 | BAT |
| github | 41 | 0 | 2413 | BAT |
| habr_nga | 3 | 0 | 128 | BAT |
| hackernews | 35 | 0 | 159 | BAT |
| lean_algo | 36 | 0 | 40 | BAT |
| mql5_bai_viet | 2 | 0 | 41 | BAT |
| mql5_code | 39 | 0 | 1166 | BAT |
| mql5_ma_expert | 2 | 0 | 18 | BAT |
| mql5_ma_nguon | 1 | 0 | 0 | TAT |
| mql5_signals | 5 | 0 | 36 | BAT |
| myfxbook | 5 | 0 | 38 | BAT |
| openalex | 39 | 0 | 1826 | BAT |
| paperswithcode | 2 | 0 | 32 | BAT |
| qiita_nhat | 2 | 0 | 60 | BAT |
| quantconnect | 30 | 0 | 0 | BAT |
| quantconnect_forum | 2 | 0 | 30 | BAT |
| quantpedia | 2 | 0 | 21 | BAT |
| reddit_td | 4 | 0 | 270 | BAT |
| rss_aligrithm | 6 | 0 | 19 | BAT |
| rss_allocatesmartly | 7 | 0 | 12 | BAT |
| rss_alphaarchitect | 7 | 0 | 10 | BAT |
| rss_alvarezquant | 6 | 0 | 4 | BAT |
| rss_betterbuyandhold | 6 | 0 | 3 | BAT |
| rss_beyondpassive | 6 | 0 | 14 | BAT |
| rss_buildalpha | 6 | 0 | 5 | BAT |
| rss_capitalspectator | 6 | 0 | 22 | BAT |
| rss_concretumgroup | 6 | 0 | 21 | BAT |
| rss_crackingmarkets | 6 | 0 | 12 | BAT |
| rss_factorinvestor | 1 | 0 | 12 | BAT |
| rss_fh_financial_hacker | 7 | 0 | 10 | BAT |
| rss_followingthetrend | 7 | 0 | 4 | BAT |
| rss_fxmacrodata | 1 | 0 | 4 | BAT |
| rss_gatambook | 1 | 0 | 8 | BAT |
| rss_gestaltu | 6 | 0 | 4 | BAT |
| rss_hangukquant | 6 | 0 | 16 | BAT |
| rss_headlandstech | 6 | 0 | 5 | BAT |
| rss_investresolve | 1 | 0 | 9 | BAT |
| rss_jonathankinlay | 1 | 0 | 10 | BAT |
| rss_mebfaber | 1 | 0 | 8 | BAT |
| rss_morguelabs | 1 | 0 | 5 | BAT |
| rss_mql5_articles | 7 | 0 | 16 | BAT |
| rss_mrzepczynski | 7 | 0 | 38 | BAT |
| rss_newtraderu | 6 | 0 | 24 | BAT |
| rss_outcastbeta | 1 | 0 | 10 | BAT |
| rss_oxford_capital | 1 | 0 | 10 | BAT |
| rss_papertoprofit | 1 | 0 | 12 | BAT |
| rss_philosophicaleconomics | 1 | 0 | 10 | BAT |
| rss_priceactionlab | 7 | 0 | 21 | BAT |
| rss_qoppac | 7 | 0 | 16 | BAT |
| rss_quant_galore | 1 | 0 | 12 | BAT |
| rss_quantdare | 6 | 0 | 12 | BAT |
| rss_quantfiction | 1 | 0 | 9 | BAT |
| rss_quantforhire | 1 | 0 | 10 | BAT |
| rss_quantifiableedges | 1 | 0 | 10 | BAT |
| rss_quantinsti | 7 | 0 | 16 | BAT |
| rss_quantish | 1 | 0 | 4 | BAT |
| rss_quantitativo | 6 | 0 | 15 | BAT |
| rss_quantjourney | 1 | 0 | 9 | BAT |
| rss_quantpedia_blog | 6 | 1 | 11 | BAT |
| rss_quantumtrading | 6 | 0 | 10 | BAT |
| rss_reddit_algotrading | 7 | 0 | 31 | BAT |
| rss_reddit_algotrading_nam | 6 | 0 | 12 | BAT |
| rss_reddit_quant | 2 | 0 | 9 | BAT |
| rss_returnstacked | 1 | 0 | 10 | BAT |
| rss_robotwealth | 7 | 0 | 12 | BAT |
| rss_rulyfi | 1 | 0 | 5 | BAT |
| rss_sixfigureinvesting | 1 | 0 | 10 | BAT |
| rss_thinknewfound | 6 | 0 | 10 | BAT |
| rss_tr8dr | 6 | 0 | 10 | BAT |
| rss_tradingmarkets | 6 | 0 | 9 | BAT |
| rss_tradingview_blog | 6 | 0 | 68 | BAT |
| semantic | 17 | 0 | 235 | BAT |
| smartlab_nga | 2 | 0 | 16 | BAT |
| stackexchange | 35 | 0 | 161 | BAT |
| telegram | 10 | 0 | 42 | BAT |
| tiktok | 5 | 0 | 101 | BAT |
| tradingview_ideas | 2 | 0 | 3 | BAT |
| tradingview_pine | 36 | 0 | 24 | BAT |
| tradingview_scripts | 2 | 0 | 101 | BAT |
| velog_han | 2 | 0 | 47 | BAT |
| x | 6 | 0 | 134 | BAT |
| youtube | 5 | 0 | 176 | BAT |
| zulutrade | 3 | 0 | 31 | BAT |

## 6. Van de dang mo (21)
> Mot PHAT HIEN = mot dong. Dien dat khac di khong de ra dong moi; no cong vao `x<n> lan`. Xem `CHU_DE_VAN_DE` trong tru/evolution.py.
- **[NANG]** `llm_6a6818d9c6` - [LLM chan doan] Null factory lot ty le cao (50%)
- **[NANG]** `quet_nong` - 88% lan chay SEEKER khong thu duoc gi moi, NHUNG chua nguon nao di het mot vong bien gioi - day la DO SAU QUET, khong phai chu ky qua day
- **[NANG]** `llm_874a010e43` **x2 lan** (gan nhat 2026-09-14 18:54:43) - [LLM chan doan] Tru NGHI và BANKER dừng hoạt động quá hạn
- **[NANG]** `vd_tick_test_bi_khoa` - [LLM chan doan] Đĩa cứng dưới ngưỡng an toàn, khóa kiểm định MT5
- **[NANG]** `null_lot_qua_nhieu` - Null factory: 5/10 ca KHONG CO EDGE van lot qua cong (50% so voi muc tieu 10%) - cong dang san xuat phat hien sai, phai siet truoc khi tin bat ky PASS nao
- **[VUA]** `tru_loi_NGHI` - Tru NGHI khong lanh manh (lan 1 lien tiep)
- **[VUA]** `llm_d6a2c4a6e3` - [LLM chan doan] Thieu moc hieu chuan that de kiem dinh cong
- **[VUA]** `llm_5cf5cc4505` **x2 lan** (gan nhat 2026-09-14 18:54:43) - [LLM chan doan] Lỗi xử lý LLM/EVO tích lũy làm nghẽn pipeline
- **[VUA]** `llm_953b89aae3` - [LLM chan doan] Vòng lặp SEEKER chạy trống chiếm 90% chu kỳ
- **[VUA]** `nang_suat_doc_thap` - Nang suat doc = 0.27 gia thuyet/100 bai (4 truy nguyen ve URL tren 1479 bai da boc; 567 ung vien tu 3278 artifact tai lieu). Day la thuoc do cua SEEKER, KHONG phai so tai lieu.
- **[VUA]** `ngu_phap_thieu_toan_hang` - 10 toan hang xuat hien trong ma THAT ma ngu phap chua dien dat duoc. Xep theo so lan dung: vwap (18 lan), atr (12 lan), linreg (10 lan), vwma (10 lan), mfi (8 lan), sar (8 lan). (186/285 thanh phan thu hoi duoc la viet ra duoc.)
- **[VUA]** `evo_xay_viec_hong` - EVO: viec loi / qua han
- **[VUA]** `evo_evo_van_de_mo` - EVO: van de con mo
- **[VUA]** `tai_lai_pdf_telegram` - 11 ban PDF tu Telegram trong so chi co 992-1.530 ky tu lop chu (slide xuat thanh ANH). File goc da mat khoi data/telegram. Can tai lai roi chay nhan/doc_pdf.quet_thu_muc - duong OCR da kiem chay thong 12/09 (trung khop tu 78,8%).
- **[VUA]** `cong_chua_co_moc_he_that` - Sau khi V6 bi loai lam moc hieu chuan (12/09), cong van CHUA co phep hieu chuan bang mot he THAT. Hai phep dang co (null_ty_le_lot, thu_luc_cong) deu dung tin hieu NHAN TAO. Can chon mot he that khac lam moc - ung vien: he da chay tien that cua chu du an.

## 6b. Kho ma dang cho NGUOI doc de doi chieu (4)
> Doc de DOI CHIEU voi cong, khong bao gio de THAY cong.
| Kho | Doi chieu voi | Vi sao |
|---|---|---|
| https://github.com/quantskills/skill-backtest-overfit | `nhan/do_luc.py` | Minimum Track Record Length - do 'bao nhieu quan sat moi du ket luan', dung bai toan MDE cua ta |
| https://github.com/OutOfSampleLab/oos-lab | `nhan/cong.py, nhan/do_luc.py` | haircut Sharpe - doi chieu voi nguong FDR LORD ta tu viet |
| https://github.com/0scarito/deflated-alpha | `nhan/cong.py` | deflated Sharpe - chieu LUC cua hieu chuan hai chieu |
| https://github.com/quantopian/zipline | `nhan/chi_phi.py, nhan/mo_phong.py` | mo hinh truot gia + phi giao dich cua mot engine 20.041 sao; mo hinh chi phi cua ta tu viet va la thu quyet dinh ca du an |

## 7. EVO da tu sua trong luot nay
- Khong co gi can sua.

> EVO chi tu sua nhung viec da khai bao truoc: `don_viec_treo`, `don_cache_khung`, `xep_lai_viec_loi`, `gian_nguon_chet`, `dong_van_de_da_het`, `gop_van_de_trung_lap`, `xep_hang_doc_cong_cu`. Ngoai danh sach do thi chi ghi van de va cho nguoi - khong tu sua code.

## 8. Suy nghi sau (LLM doc so lieu van hanh)
- Bo qua luot nay: chua den ky (6 gio)

## 9. Huong NEN TRANH (so bai hoc)
- so co 238 the: bay_do_luong 140 · huong_dang_mo 60 · quy_tac_nguoi_dung 29 · huong_nen_tranh 9
- **HUONG CHINH tu 24/08/2026 - rut ngan thoi gian test; may nghet bang thong nen KHONG duoc bat dau bang nhan luo**
  - bang chung: **Nguoi dung chot 24/08/2026:** vi du "lay 50 chien luoc" chi la vi du. Bai toan
- **"21/08/2026 - he chi thay duoc edge tu Sharpe 1,57; Sharpe 0,5 can 43 nam; gop tai san phai tinh theo k HIEU D**
  - bang chung: | 1,4 nam | Sharpe 3,32 (alpha 19,7%/nam) |
- **"Phuong phap moi sau khi quet tham so that bai: tim trong khong gian CO CHE (~40-60 phan tu). Co che 01 (cau t**
  - bang chung: - IC(20 ngay) **+0,106**, duong o ca 5 giai doan con — nhung KHONG chuyen thanh tien.
- **KHONG duoc mo hinh phi qua dem bang `swap_tuyet_doi * 365 / gia_tung_ngay`**
  - bang chung: chinh cai bay o muc 13, va toi da tu mac lai no ngay 28/07 (ra 38,8%/nam cho nam 2011).
- **Khong duoc mo hinh phi qua dem bang swap tuyet doi nhan 365**
  - bang chung: 38,8%/nam nam 2011 so voi 6,0-14,7%/nam do that
- **21/08/2026 - san p-value cua placebo (1/200) va nguong LORD va nhau tu phep thu thu 4; 346 phan quyet FAIL vo **
  - bang chung: Tu 15/08 den 21/08/2026 cong QUANTLAB khong the cho bat cu thu gi di qua, va
> Day la TRI NHO, khong phai lenh cam. Mot huong tung am o mot tai san / cua so / muc chi phi van co the duong o cho khac.