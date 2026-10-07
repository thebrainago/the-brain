# THE BRAIN

Phong nghien cuu tu dong cho giao dich: thu thap chien luoc tu moi nguon,
boc tach thanh co che, kiem dinh, va giu lai cai KIEM RA TIEN.

> **Doc truoc khi lam bat cu viec gi:**
> 1. `SO_DO_HE_THONG.txt` — so do goc cua chu du an (LUAT SO 0). Day la nguon
>    cau truc duy nhat. Ke hoach nao khong co trong so do thi khong phai viec.
> 2. `CLAUDE.md` — luat lam viec, cac bay da dinh, quy uoc bao cao.
> 3. `KIEN_TRUC.md` muc 0 — ban do thu muc; muc 1 — bon cua vao that.

## He nay gom gi

| Tang | Cho | Vai tro |
|---|---|---|
| **Nha nghien cuu** | `nhan/nc_*.py` · `b nc` | **AI nam quyen nghien cuu** (tu 25/09/2026): doc so tay, dat gia thuyet, thi nghiem, hoc tu lenh dung/sai. Xem `tai_lieu/NHA_NGHIEN_CUU.md` |
| Tru | `tru/` | SEEKER (thu thap) · QUANTLAB (nghien cuu) · EVOLUTION (giam sat) · BANKER · FINDER · NGHI |
| Thu vien | `nhan/` | 132 module: du lieu, cong kiem dinh, MT5/tester, quan tri vi the, ngu phap DSL... |
| Cua vao | `b.py` · `dieu_phoi.py` · `day_viec.py` · `qwen/NHIEM_VU.json` · `BAN_GIAO.py` | Module khong duoc goi tu mot trong bon duong nay thi *bang khong co* |

`b.py` la lenh nguoi go — 41 lenh con. `python b.py` de xem danh sach.
Bat dau o day: `python b.py nc` (ho so nghien cuu) va `python b.py nc cc` (bo cong cu).
Hai lenh nen chay truoc khi xay them:

```
python b.py ban-do      # module nao con MO COI, dung xay trung
python b.py kien-truc   # module nao co VAI TRO gi, thuoc lop nao
```

## Cai KHONG chay duoc o day

Repo nay chi co MA NGUON. Nhung thu sau nam tren may cua chu du an va
**khong the dua len cloud**:

- **MT5 Strategy Tester** — app Windows. Quy tac cua du an: *tester TRUOC,
  Python SAU*. Moi con so hieu suat phai do bang tester that.
- **`nao.db`** (~1,6 GB) — kho tri thuc + du lieu vi mo.
- **`data/`, `data_khung/`** — du lieu gia da nap.
- **`.browser_darwinex/`** — ho so trinh duyet rieng cua Seeker (co phien
  dang nhap). Khong bao gio commit.

Nghia la: **thiet ke, viet module, doc ma, lap ke hoach thi lam o day duoc.
DO thi phai ve may.** Dung ket luan mot co che "chay duoc" khi chua qua tester.

## Vong lam viec giua cloud va may

```
cloud: viet module  ->  push
may  : git pull  ->  chay tester/nap du lieu  ->  push ket qua (.md/.json)
cloud: doc ket qua  ->  viet tiep
```

## Cai da hoc duoc (dung lam lai)

Nhung bay nay da tra gia mot lan roi, `CLAUDE.md` ghi day du:

- Ket qua AM phai phan biet **"da do va am"** voi **"chua do"** — hai cai khac nhau.
- Cong kiem dinh phai hieu chuan **hai chieu**: placebo phai truot, va he that phai qua.
- Bo do nhin truoc (`da_dich=True`) mu voi co che THUA — luc cua no ti le voi tan suat kich.
- Chuyen thu muc nao thi grep `GOC.parent` / `LAB.parent` trong `nhan/` truoc:
  vai module TU TAO LAI thu muc rong thay vi bao loi.

## Chay

```
pip install -r requirements.txt
python b.py            # xem lenh
python -m pytest -q    # bo test (155 file, chay lau)
```
