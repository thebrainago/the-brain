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
