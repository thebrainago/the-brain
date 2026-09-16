# GOI G2-B — GHI `nao.db` AN TOAN · 16/09/2026

**Noi ngan:** khong chon A hay B, vi **chua do duoc** cai can de chon. Nhung do
duoc hai lo hong CO THAT va sua ca hai.

## Do truoc khi sua

| Do | Ket qua |
|---|---|
| `busy_timeout` | 30.000 ms — **co dat** |
| So cho trong lab thu lai khi gap `database is locked` | **0** (quet ca cay) |
| Ham ghi dung autocommit (`isolation_level=None`) | **tat ca** |
| Cho ghi theo LO trong mot giao dich | **khong co** |
| `wal_checkpoint` duoc goi o duong ghi | **khong** |

Nghia la: SQLite tu doi 30 giay roi **nem loi**, nguoi goi khong bat. Mot me
dai co the chet o dong ghi cuoi sau khi da chay xong phan nang. Va ghi N dong
la N giao dich = N lan tranh khoa.

## Vi sao CHUA chon giua A va B

**Huong A** (tach `vi_mo` + `chi_so_vh` sang DB rieng) nham vao 73% so dong.
Nhung do 16/09: hai bang do do **BANKER** ghi, ma BANKER la **VO** — 550 dong
goi dung 1 module (`b ho-so` muc 3). Tach mot bang ma tru ghi no khong chay thi
khong giam tranh khoa nao hom nay.

**Huong B** (hang doi + mot tien trinh ghi) dung 24+ cho goi `ket_noi()` trong
`so.py` va 11 cho trong `seeker.py`. Do la thay doi lon, va no chua duoc bien
minh: **he dang `DUNG_LAI`, chua do duoc lan tranh khoa that nao.**

Chon A hay B can mot phep do chi lay duoc khi **he chay that**: bao nhieu lan
`database is locked` moi gio, o bang nao, do tru nao. Ghi vao `chi_so_vh` bang
`SO.ghi_chi_so("khoa_ban", ...)` roi doc lai sau mot tuan chay.

=> Ket luan: **CHUA_DO_DUOC**, khong phai "khong can".

## Da sua gi (cai ca hai huong deu can)

1. **`SO.thu_lai(ham, ...)`** — thu lai khi khoa ban, cho nhan doi 0,2s -> 3,2s,
   toi da 6 lan. `mot()` / `nhieu()` / `chay()` deu di qua no.
2. **`SO.ghi_lo()`** — ghi nhieu dong trong MOT giao dich, mo bang
   `BEGIN IMMEDIATE` (lay khoa ghi ngay thay vi nang cap giua chung - do la
   cach sinh `database is locked` kinh dien). Hong giua chung thi `ROLLBACK`.
3. **`SO.diem_tra_wal()`** — checkpoint co ten goi duoc. `nao.db-wal` tung
   phinh 1,4 GB va lam ba me boc bao XONG rc=0 trong khi kho khong doi.

## Cho de nhat, va la cho quan trong nhat

`_ban(e)` chi coi **dung hai chuoi** la "cho luot": `database is locked` va
`database is busy`, **va** phai dung kieu `sqlite3.OperationalError`.

Bat rong hon — vi du moi `OperationalError` — se nuot ca loi that: sai cot,
sai kieu, DB hong. Roi thu lai sau lan, that bai, va bao **sai nguyen nhan**.
Do dung kieu hong ma du an nay da dinh nhieu lan: ket luan am ma that ra la
CHUA_DO_DUOC.

## Rui ro con lai

- Chua co cho nao trong lab GOI `ghi_lo()`. No moi la cong cu, chua thay duong
  ghi cu. Buoc sau: doi cac vong `for ... cn.execute(INSERT)` sang `ghi_lo()`.
- `diem_tra_wal()` chua vao nhip ngay (`b don-dia` van la lenh tay).
- Chua do duoc so lan khoa ban that -> chua chon duoc A/B (xem tren).

## Test

`test_so_ghi_lo.py` — 8 bai, pass het:
- **5 tien trinh ghi cung luc -> du 250 dong, 5 nhan, khong loi khoa** (dung
  phep thu ma bang ke hoach doi)
- lo hong giua chung thi **lui het**, khong de lai nua chung
- nhan ra `database is locked` / `is busy`
- **loi that khong bi nuot**: `no such column` va `ValueError` khong duoc coi
  la khoa ban
- thu lai roi thanh cong (3 lan) · loi that nem NGAY (1 lan, khong lap 6)

Hoi quy: `-k "so_sach or so_cai or anh_chup or fdr or hang_doi or bang_he or slot"`
-> **94 passed**.
