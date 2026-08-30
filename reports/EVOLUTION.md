# EVOLUTION - SUC KHOE DAY CHUYEN
*2026-08-16 22:56:54*

> Do bang SUC KHOE, khong do bang so PASS. Mot he lanh manh hieu chuan tot ke ca khi tim duoc it edge.

## 1. Bon tru
| Tru | Lan cuoi | Tre | Trang thai |
|---|---|---|---|
| SEEKER | 2026-08-16 22:41:43 | 15 phut | nghi |
| QUANTLAB | 2026-08-16 22:56:54 | 0 phut | nghi |
| NGHI | 2026-08-16 21:39:42 | 77 phut | nghi |
| BANKER | 2026-08-16 22:08:02 | 48 phut | nghi |
| EVO | 2026-08-16 22:56:54 | 0 phut | chay |

## 2. San luong
- Tai lieu da thu: **952**
- Gia thuyet: {"FAIL": 346, "NGHI_NHIN_TRUOC": 1, "PASS": 7}
- Gia thuyet co ket qua cuoi: **354** (chua 888 lan chay lai/du phong da bo)
- Viec: cho 0 / treo 0 / loi 0
- Ty le vong lap rong cua SEEKER: **74%**

## 3. Hieu chuan (thu quan trong hon so PASS)
- **Null factory: 0% ca KHONG CO EDGE lot qua cong** (do luc 2026-08-16 09:18:16, muc tieu <= 10%)
  Day la phep do hieu chuan DUY NHAT dang tin: cho thu khong co edge di qua ca day chuyen roi dem xem bao nhieu lot.
- **Bai kiem LUC: cong PHAN BIET DUOC co edge voi khong co edge** (do luc 2026-08-16 09:18:19)
  Hai phep do phai doc CUNG NHAU: 'null lot 0%' mot minh khong phan biet duoc mot cong hieu chuan tot voi mot cong tu choi tat ca.
  - biet truoc 0.5 cua so lan -> `FAIL` (sharpe -0.513)
  - biet truoc 0.55 cua so lan -> `FAIL` (sharpe 0.242)
  - biet truoc 0.6 cua so lan -> `PASS` (sharpe 1.307)
- (tham khao) p placebo cua 113 ung vien: trung vi 0.325, ty le p<=0,05 la 23.0%
  KHONG dung so nay lam hieu chuan: ung vien da bi chon loc tren train nen p cua chung LE RA phai lech thap.
- FDR online: 8/279 gia thuyet bi bac bo (dem theo gia thuyet, bo du phong/NULL; tho 675 hang)
- Dong bo ba tang (so_gt_da_ket == fdr_tong): **TACH** - doi soat tiep khoan tinh nay

## 4. Tai nguyen + toan ven
- **Thoi gian song 7 ngay: 97.2%** (mat 4.7 gio qua 1 lan gian doan - may ngu hoac tat, khong phai tru chet)
- Dia trong: **16.0 GB** - MT5 tick-test: **GO**
- So cai: LANH (1687 dong lien mach)

## 5. Nguon
| Nguon | Lan goi | Loi | Thu hoach | Trang thai |
|---|---|---|---|---|
| arxiv | 4 | 0 | 113 | BAT |
| blog | 1 | 0 | 27 | BAT |
| collective2 | 2 | 0 | 10 | BAT |
| crossref | 1 | 0 | 40 | BAT |
| darwinex | 1 | 0 | 32 | BAT |
| etoro | 1 | 0 | 0 | BAT |
| facebook | 0 | 0 | 0 | BAT |
| fxblue | 2 | 0 | 0 | BAT |
| github | 3 | 0 | 179 | BAT |
| hackernews | 3 | 0 | 44 | BAT |
| lean_algo | 1 | 0 | 40 | BAT |
| mql5_code | 1 | 0 | 0 | BAT |
| mql5_signals | 3 | 0 | 30 | BAT |
| myfxbook | 3 | 0 | 37 | BAT |
| openalex | 3 | 0 | 216 | BAT |
| quantconnect | 1 | 0 | 0 | BAT |
| reddit_td | 1 | 0 | 90 | BAT |
| semantic | 1 | 0 | 0 | BAT |
| stackexchange | 3 | 0 | 69 | BAT |
| telegram | 2 | 0 | 13 | BAT |
| tiktok | 0 | 0 | 0 | BAT |
| x | 1 | 0 | 3 | BAT |
| youtube | 0 | 0 | 0 | BAT |
| zulutrade | 1 | 0 | 0 | BAT |

## 6. Van de dang mo (21)
- **[NANG]** `qua_nhieu_pass` - 8 PASS trong mot ngay. Theo THIET_KE muc 9 day la tin hieu HONG chu khong phai tin vui - phai kiem day chuyen truoc khi duyet
- **[NANG]** `nghi_nhin_truoc_EURGBP.H4.mua_qua_dem.gio_vao20_gio_ra14` - EURGBP.H4.mua_qua_dem.gio_vao20_gio_ra14 cho t_alpha > 5 - nguong hieu chuan tu canary noi day phai gia dinh la nhin truoc
- **[NANG]** `llm_4ea25bb017` - [LLM chan doan] Co 1 gia thuyet vuot FDR nhung van bi cong loai — dau ra tang thong ke khong di duoc ra ngoai
- **[NANG]** `llm_30d8fbead6` - [LLM chan doan] Phan phoi p cua ung vien lech manh khoi null ma khong co gi ra khoi cong
- **[NANG]** `llm_523fcdc318` - [LLM chan doan] Nha may null qua nho de ket luan bat cu dieu gi ve cong
- **[NANG]** `llm_ce2c5af67a` - [LLM chan doan] Buoc kiem dinh quyet dinh (MT5 tick-test) dang bi khoa va nguong con dang tut
- **[NANG]** `llm_5f7a8fa671` - [LLM chan doan] Phan phoi p cua ung vien lech han khoi null — hoac co tin hieu that dang bi vut, hoac p-value dang tinh sai
- **[NANG]** `llm_7009967569` - [LLM chan doan] Khong the phan biet 'cong hieu chuan dung' voi 'cong tu choi tat ca' — nha may null qua nho de lam bang chung
- **[NANG]** `llm_c17d82c8bb` - [LLM chan doan] Cong PASS loai sach ca 8 gia thuyet da vuot FDR — day chuyen co dau ra o tang thong ke nhung khong co gi di ra khoi cong
- **[NANG]** `llm_f7f11f13ea` - [LLM chan doan] Nha may null qua nho va khong dai dien de ket luan bat cu dieu gi ve hieu chuan
- **[NANG]** `llm_ba1deaef7d` - [LLM chan doan] Phan phoi p cua ung vien KHONG phai phan phoi null — nhung khong co gi di ra khoi day chuyen
- **[NANG]** `llm_3c0a37d910` - [LLM chan doan] Cong loai bo ca 8 gia thuyet da vuot FDR — day la bang chung dinh luong dau tien cho gia thuyet 'cong qua chat', khong con la phong doan
- **[NANG]** `hieu_chuan_v6` - Cong PASS chua duoc hieu chuan bang V6 THAT. Ban thu 15/08 dung IBS<0,2 don gian tren US500M/US500CASH D1 va bi FAIL, nhung do CHUA phai V6: thieu lop bias>0, chay mot chi so thay vi danh muc 3 chi so My, va bar D1 cat theo UTC chu khong theo phien My. THIET_KE noi ro: cong nao loai mat V6 la cong SAI. Phai dung lai dung V6 (Sharpe 0,95 do tren MT5 that) roi cho qua cong truoc khi tin bat ky ket luan am tinh nao.
- **[VUA]** `nguon_can_trinh_duyet` - CDP trinh duyet CHUA MO - 12 nguon cao gia tri chua quet duoc. Mo Chrome .browser_darwinex kem CDP (vd 9224).
- **[VUA]** `can_mau_moi` - 4 tai lieu HANG A mo ta co che CHUA CO trong nhan/mau.py - can them template moi thi QUANTLAB moi kiem dinh duoc

## 7. EVO da tu sua trong luot nay
- Khong co gi can sua.

> EVO chi tu sua nhung viec da khai bao truoc: `don_viec_treo`, `don_cache_khung`, `xep_lai_viec_loi`, `gian_nguon_chet`, `dong_van_de_da_het`. Ngoai danh sach do thi chi ghi van de va cho nguoi - khong tu sua code.

## 8. Suy nghi sau (LLM doc so lieu van hanh)
- Bo qua luot nay: chua den ky (6 gio)