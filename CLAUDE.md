# CLAUDE.md — lab/ (THE BRAIN)

File nay tu nap moi khi doc file trong `lab/`. Muc dich: dung mat 15 phut dau
phien de tim lai luat. Ban day du van o `../AGENTS.md`.

## Vao phien / ket phien
```
b vao              trang thai song + ban giao hom qua  (~2 giay)
b ket "tom tat"    chot ngay: git commit + sinh TIEP_TUC_MAI.md moi
b                  menu day du
```
Python **duy nhat**: `C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe`.
Khong dung `WindowsApps\python.exe`. `b.cmd` da tro dung san.

## Bo cuc (30/08/2026 — da gop mot dau moi)
```
Research SP500/          <- kho git chinh (mo 30/08)
  lab/     nhan/  hat nhan dung chung: so, du_lieu, chi_phi, mo_phong, cong, mau...
           tru/   5 tru: seeker, quantlab, nghi, banker, evolution
           dieu_phoi.py  MOT supervisor, nao.db MOT so cai
  ds/      kho DeepSeek — GIU GIT RIENG (56 commit, 799 test).
           datalake, primitives, probes, schemas (card), gates G0-G7, mimic
  data/    parquet gia (ngoai git)
```
`ds/` truoc 30/08 nam o `Downloads/Promt cho DS`. Da chuyen vao. Duong dan cung
trong `ds/browser/*` va `lab/BROWSER_SCAN*.bat` da sua theo.

## Luat khong duoc pha (rut gon — ban day du: ../AGENTS.md muc 3)
- **Canary truoc, ket qua sau.** Canary hong -> dung tru, khong tinh p-value nao.
- **Chi phi phai DO DUOC.** `cp.do_tin` la `KHAI` thi **khong bao gio PASS**.
- **Pre-registration.** Phai co `plan_hash` truoc khi cham holdout. Doi ke hoach
  sau khi cham du lieu = gia thuyet KHAC.
- **Xac nhan la HAM Y NGUYEN.** Chay lai cung gia thuyet = nhin lai cung holdout.
- **`t_alpha > 5` = nghi nhin truoc** cho toi khi chung minh nguoc lai.
- **Nhieu PASS trong mot ngay la tin hieu HONG**, khong phai tin vui.
- **Hieu chuan cong phai HAI CHIEU**: `null_ty_le_lot` + `thu_luc_cong`. Mot cong
  tu choi TAT CA cho so lieu y het mot cong tot.
- **Kien thuc moi chi vao he qua `nhan/ngu_phap.py`** — khong `exec` ma LLM sinh.
- **Ket luan am tinh phai kem MDE** (`do_luc.luc_hai_chang` / `gop_lop.mde_gop`).
- **Do dac khong duoc chiem suat FDR**: truyen `ghi_so=False`.

## Bay da sap that — kiem TRUOC khi tin so
- `kho()` chon ban theo **do phu**, khong theo byte. Them file vao `data/` co the
  doi ban duoc chon cua ca mot ma.
- **Open bia**: nguong theo NGUON (`san` 0,60 / `ngoai` 0,20), khong theo ten ma.
- **Spread do tu bar D1 la chan tren** — H1 thap hon ~39% (do that tren EURCAD).
- **Model=1 cua MT5 noi doi** khi TP < 2x bien do nen M1. Phai chay Model=0/4.
- `swap_mode` co ba nhom cong thuc; mode 9 khong co trong API MT5 nhung FXCE tra ve.
- Tra cuu phi theo ten symbol tho -> lang le lay phi `MetaQuotes-Demo`.

## Sua code
- **Co git roi**: sua thang, `b luu "..."` de chot, `b lui <file>` de tra lai.
  **Dung copy tay vao `backups/`** (da phinh 247 MB) — do la thoi quen truoc git.
- `b test` = 8 tien trinh, ~2,5 phut / 321 test. `b test1` khi nghi song song sai.
- `b tim <tu>` tim trong ma nguon, khong loi nhoi ket qua tu data/reports.
