# CMT -> HE THONG (05/10/2026, chu du an: "cap nhat giao trinh cmt va ap dung vao he thong de loc bot thi nghiem thua va tang xac suat thang")

Gia dinh: CMT = Chartered Market Technician (giao trinh phan tich ky thuat). Neu y chu du an khac thi bao de sua.
Ma: `nhan/cmt_prior.py` (+ test `nhan/test_cmt_prior.py`), cong cu `b nc cc cmt_loc`. KHONG phai cong chan: chi NHAN + THU TU.

## Bon y trong giao trinh va cho he dung chung
| Y CMT | Dung o dau | Tac dung |
|---|---|---|
| Chi bao CUNG HO cho cung thong tin (RSI / Stochastic / CCI = dong luong dao dong; SMA / EMA / MACD = xu huong tre) | `cmt_prior.HO`, `loc()` | gom khai bao cung ho + cung chieu thanh 1 CUM = 1 thi nghiem; tham so cua cum di vao luoi (HEPHAESTUS), khong ton phep thu moi. **Kho that: 4.049 khai bao -> 90 cum.** Day la CAN TREN so thi nghiem doc lap, chua kiem bang du lieu |
| Xac nhan phai tu bang chung DOC LAP (khac ho) | `canh_bao` `xac_nhan_khong_doc_lap` | 246 khai bao trong kho chong nhieu dieu kien cung ho: khong xac nhan them gi |
| Khoi luong: CFD / FX chi co tick volume | `canh_bao` KHOI_LUONG | 20 khai bao dung OBV / VWAP / khoi_luong: de thu cuoi |
| Che do thi truong: dao dong dung o thi truong di ngang, theo xu huong o thi truong co xu huong | `UU_TIEN[tinh_cach]` | xep thu tu thu theo tinh cach tai san (hoi_quy / quan_tinh tu `ho_so_tai_san`), khong loai ho nao |
Chua dua vao: chu ky / mua vu (da co `ho 1` LICH), tuong quan lien thi truong (intermarket), tam ly dam dong - can du lieu ngoai.

## Gioi han (noi thang)
- 90 cum la uoc luong theo TEN chi bao. Hai khai bao cung ho nhung nguong rat khac van co the cho tin hieu khac nhau; muon biet that thi do tuong quan chuoi tin hieu tren du lieu (viec may nha: don `ni-cum-cmt`).
- Chua co bang chung rang uu tien theo che do lam tang ti le thang; la luat kinh nghiem cua giao trinh. Do bang: ti le cum DAT o xac_nhan giua thu tu moi va thu tu cu.
- Tri thuc o day la cua giao trinh pho thong; neu chu du an co giao trinh / ghi chu CMT cu the thi dua vao `reports/` de model re doc va bo sung HO / UU_TIEN.

## Viec LLM lam (job 3, 05/10): soan khai bao DSL theo y tuong CMT
`reports/deepseek/chay_dsl_cmt.py`: 10 y tuong x 2 chieu, T1, 1 vong sua; 17/20 qua `kiem_khai_bao` (48 d). **Claude doc mau: cac ban BAN (-1) bi dao sai nghia** (vi du mua nhip lui: EMA nhanh > cham + RSI<40 dung cho MUA; ban sao chep lai y nguyen dieu kien) -> xep vao `ban_chua_duyet/`, khong dung. Ban MUA la **ban nhap de may nha thu tren kham_pha**, chua vao `config/co_che_dsl.json`.

## Dot 2 (05/10): may lat MUA -> BAN, khong de LLM lat
`nhan/guong_dsl.py` (test `test_guong_dsl.py`, 6 ca): lat phep so sanh, doi hang cua chi bao co khoang (RSI 30 -> 70, IBS 0,2 -> 0,8, zscore -2 -> +2),
doi kenh cao <-> thap (Donchian: ca cot high <-> low), GIU NGUYEN dieu kien khong co huong (ADX, ATR, lich). Gap kenh khong ro tren / duoi (Keltner,
Bollinger, Ichimoku) hoac chi bao chua biet lat -> tra None, khong doan. Model re chi soan ban MUA (dot 2: 11/12 qua cu phap, ~30 d); ban BAN do may lat:
**19 ban MUA + 13 ban BAN** trong `reports/deepseek/dsl_cmt/` (6 ban MUA khong lat duoc, cho Claude / may nha lam tay). **10 / 23 cum la cum CHUA CO trong kho** (vi du
PHA_VO + SUC_MANH_XU_HUONG, DAO_DONG + SUC_MANH_XU_HUONG) - day moi la gia tri that cua dot nay: lap vao cho trong cua kho, khong them ban sao.
Cac ban nay van la BAN NHAP: chua vao `config/co_che_dsl.json` (chi phien GHI / may nha duoc sua `config/*`), chua chay tren gia.
