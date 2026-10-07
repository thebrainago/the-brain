# BAI HOC TU CAC LAN CHAY DA TAC TU

## 05/10 - ra soat loi 7 module loi (qwen3.8-flash, ~105 d, 5/7 dat may cham, 2 viec dich_tham_so + chi_phi bi cong 502 vi tep 44-46 KB)
- May cham "tro ham co that" bat duoc bia ten ham NHUNG khong bat duoc bia LY LUAN. Claude doc code that kiem 3 phat hien muc CAO:
  `cham_diem.tu_ket_qua_luoi` (nan lot cong sut giam) - SAI, code da bat `dd is None` va tra CHUA_DO_DUOC; `cong.xet` dieu kien 13 voi spread thieu - SAI, da co `_phi_thieu` + nhan;
  `mo_phong.chay_tpsl` truyen `lai_suat_nam=None` - SAI, tham so tuy chon. **0/3 CAO la loi that.** `luoi._mot_ro chot_tien` (nguong theo ts.lot) - chua kiem (co the that khi kieu_lot khac phang).
- Phan bien cheo (ds-flash) khong cuu duoc: gan "dung" cho phat hien sai (cham_diem nan). Model re doc module dong comment "vi sao" khong hieu bang tac gia.
- Ket luan: dung LLM re RA SOAT LOI tren module da duoc chu thich ky la RA ON. Viec hop hon voi may cham MANH: viet TEST chay duoc (may chay test: dat/hong la su that), tom tat, doi chieu tai lieu <-> code. Rut kinh nghiem -> chuyen sang do do.

## Lan 2 (05/10): viet test bang ds-flash - 4/6 DAT, 69 test chay qua
- the_phuong_phap 12, thu_chuyen 25, do_thong_minh 16, nc_phuong_phap 16 test: Claude doc, chay lai, nhan vao repo (`test_*_llm.py`). Chi phi ~597 d.
- Hong: kiem_the_nhap (NameError KCN sau 3 vong), dich_tham_so (loi mang tren tep 44 KB) - de lan sau, chia nho tep.
- Ket luan: giao viec CO MAY CHAM CHAY THAT (test chay duoc) cho ket qua dang tin; kiem toan bang doc thi nhieu rac.
