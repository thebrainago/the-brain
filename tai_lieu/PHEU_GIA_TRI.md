# PHEU GIA TRI (06/10/2026) - tim nhung thu DANG RA TIEN, boc co che, suy ra phuong phap, hoc nguoc ve nguon

Chu du an: *"nguon chat luong, hut nhieu du lieu, nhieu thu ra tien; boc tach co che that thong minh, suy luan ra phuong phap, dao nguoc lich su, loc cai gi ra doanh thu; the thi khong can - khi nao chay co lai la duoc"*.
Cac manh da co khong thay: `vuon_nguon` (do suat nguon), `seeker` (hut), `boc_llm` / `boc_ma_llm` / `boc_lich_su` (boc), `ngu_phap` + `nc_cong_cu` (thu). Thieu: **thuoc do TIEN noi ca day chuyen**. Do do nguon cu xep theo "ung vien / 100 bai", khong theo "he CO LAI".

## Mat phang moi: `nhan/pheu_gia_tri.py` (+ `test_pheu_gia_tri.py`, 5 + 1 test)
1. **chan_doan** - LLM re doc MOT tai lieu -> JSON co cau truc (co che kinh te, loi nhuan cong bo co/khong sau phi + ngoai mau, dau hieu do, du lieu can) + **suy_ra**: cung CO CHE do con tra tien o dau (tai san / khung / chieu), moi cho kem ly do va cach bac bo bang so. May kiem tu vung kin, sua toi da 2 vong. LLM nhan kem **dieu lab da biet** (`reports/pheu_gia_tri/bai_hoc_nen.md`) va bai hoc tu ket qua that.
2. **diem_dang_tien** (MAY cham, khong LLM): 100 x tin cay bang chung x kha thi tren du lieu lab x moi (chua bao hoa) x ben vung. Loi qua dep ma khong ngoai mau / khong phi = tru diem; khong thu duoc tren lab ma khong co cho chuyen sang tai san lab co = 0.
3. **so cai** `reports/pheu_gia_tri/so.jsonl` (chan_doan + ket_qua DAT/AM/CHUA_DO_DUOC theo tung phuong phap).
4. **hoc nguoc**: `xep_nguon` xep nguon theo SUAT TIEN = (he DAT+1)/(he da thu+10) (nguon moi khong bi 0 vinh vien, he chua thu khong phat nguon); `bai_hoc` ty le DAT theo (loai co che x lop tai san) -> vao loi nhac lan sau; `xep_viec` phuong phap chua thu xep theo diem x suat nguon.
5. **ra viec**: `viec_luoi` doi phuong phap quan li lenh thanh don `quet_luoi` (mua / ban rieng). Phuong phap dang tin hieu van can buoc bien ra DSL (chua noi, xem duoi).

## Lan chay 1 (nguon chu du an gui)
- Bai End-of-Day Reversal: diem **13,6/100** - co che cau truc (phe ban khong rut lui + ETF/gamma cuoi phien) nhung loi cong bo TRUOC phi, trong mau. Suy ra 3 cho: chi so (ETF rebalance cuoi phien), FX (phan bien: co dao chieu o gio 16:00 NY khong), hang hoa (dong cua san COMEX/NYMEX). Moi cho co cach bac bo bang so.
- Bot DCA vang: diem **3,5/100** - khong co lich su, quang cao. Suy ra DCA tren vang M15 / AUDCAD (da co don) / chi so H1 (them 1 don: `61-pgt-us500cash-H1`) kem canh bao bo neu maxDD > 80%.
- Bai hoc cho phien sau: lan dau LLM gan "khong co co che" cho DCA vi khong co ly thuyet; da sua loi nhac (quan li lenh la co che hop le theo tieu chi duyet cua chu du an). Kiem tra hai chieu: diem cao CHUA nghia ra tien, chi nghia dang thu truoc.

## Chua noi (xep theo gia tri)
1. **Hut thang vao `chan_doan`**: tai lieu trong `nao.db` (mat khi cai lai may) -> thu hoach lai o may nha, moi ban doc di qua `chan_doan` (nhanh: ~vai xu / tai lieu). Cloud khong cham duoc nguon do.
2. **Bien -> DSL tu dong** cho phuong phap tin hieu (tuong tu `chay_dsl_cmt3`, co may kiem `kiem_khai_bao` + trung thuy ho).
3. **Thu hoach ket qua**: cong cu `nc cc` ghi vao so tay `nc.db` o may nha; can doc lai theo `gt_id` -> `ghi_ket_qua` (chua noi, can xem schema so tay).
4. **Dung `xep_nguon` chia ngan sach** trong `vuon_nguon` (hien chia theo ung vien): giu san tham do de nguon khong bi giet oan.
5. Nguon dang anh / video (TikTok, FB): nguoi gui anh -> chu chep vao `chan_doan` (da lam tay hom nay); tu dong can OCR / video-to-text (moc rieng).

## Ranh gioi (chu du an 06/10/2026)
- **Ly thuyet / tin hieu -> chien luoc** (bai bao, `suy_ra` dang tin hieu) = viec cua **HEPHAESTUS** (de co che, rai luoi tham so, ghep nut), lam DAI HAN; `pheu_gia_tri` chi giao `suy_ra` cho Hephaestus, khong tu bien ra DSL.
- **UU TIEN HIEN TAI**: nguon da co EA / tin hieu **dang ra tien** (MQL5, Myfxbook): chay nguyen file EA, keo lich su nguoi thang ve boc luat -> `NGUON_NGUOI_THANG.md`. Cloud khong toi duoc mql5 / myfxbook (do 06/10: HTTP 000), nen hai buoc nay chay o MAY NHA (phien LLM co Chrome da dang nhap): thu tu viec o `reports/uu_tien_ho_so_mql5.md`.
