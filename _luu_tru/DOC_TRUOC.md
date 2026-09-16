# `_luu_tru/` — script mo coi, giu lai chu khong xoa

Chuyen vao day ngay 16/09/2026 (goi G3-D). Dieu kien de mot file vao day, **du
ca ba**:

1. `b kien-truc` xep no vao nhom **no that** (khong phai `test_*`, khong phai
   `_*.py` chay tay);
2. **mo coi** — khong duong chay nao (`b.py`, `dieu_phoi.py`, `day_viec.py`,
   `qwen/NHIEM_VU.json`, `.cmd`/`.bat`) toi duoc;
3. **khong file `.py` nao import**, va khong tai lieu nao ngoai cac ban **liet
   ke tu sinh** (`BAN_DO.md`, `KIEN_TRUC.md`, `INVENTORY_THE_BRAIN.md`,
   `nhat_ky/`, ban giao cu) nhac den.

**Khong xoa file nao.** Git giu ca lich su lan buoc di chuyen: `git log
--follow _luu_tru/<ten>.py` doc duoc het, va `git mv` nguoc lai la xong.

Can dung lai mot file o day thi **dung khoi phuc nguyen xi**: doc no truoc, doi
chieu `b kien-truc` xem viec do da co module nao lam roi chua. Ly do chuyen
phan lon chung vao day la trung viec voi `nhan/` — vi du `nguon_telegram.py`
so voi `nhan/telegram.py`, `nguon_kham_pha.py` so voi `nhan/kham_pha_nguon.py`.
