# PHONG LAB QUET HE THONG GIAO DICH 24/7

Tu dong hoa dung con duong da tao ra he EURCAD: **quet nguon ngoai -> rut co che ->
test that tren MT5 -> hoan thien**. DeepSeek lam bo nao ngon ngu (re, hop treo VPS),
Python lam phan co hoc (cao + chay tester + do + luu).

## KIEN TRUC (vi sao chia vai nhu vay)
LLM khong tu chay MT5 hay tai file duoc. Nen:

    ┌─────────────── Python orchestrator (lab.py) ───────────────┐
    │  CAO nguon → [DeepSeek B1 phan loai] → [DeepSeek B2 rut]    │
    │      → luu SQLite → loc diem≥8 → [DeepSeek B3 sinh tham so] │
    │      → CHAY MT5 tester THAT → [DeepSeek B4 phan quyet]      │
    │      → neu THAT: kiem cheo cap + walk-forward → cap nhat moc│
    └────────────────────────────────────────────────────────────┘

DeepSeek chi tra JSON o 4 diem (B1-B4). Toan bo cao/test/do/luu la Python.
System prompt cua DeepSeek = `PROMPT_DEEPSEEK.md` (co PLAYBOOK ULTIMA + thang diem +
8 cai bay). File nay lab.py tu nap.

## NGUON DAU VAO
| nguon | tu dong? | cach |
|---|---|---|
| MQL5 CodeBase | CO | scrape HTML, uu tien EA co ma nguon |
| GitHub | CO | API search, loc theo sao |
| Forex Factory / BabyPips | CO | scrape khu Trading Systems |
| YouTube (clip tac gia bot) | CO neu co `yt-dlp` | lay phu de lam van ban |
| **Facebook / TikTok / trang dong** | **ban tu dong** | login+chong bot nen KHONG cao tu dong duoc. Nguoi dung DAN link+noi dung vao `hang_doi_thu_cong.txt` (cach nhau `---`), lab tu doc va phan tich. Con nguoi lay du lieu, lab phan tich. |
| **Passview tai khoan that** | rieng | investor pw TU NGUYEN cua chu tk. Dung `soi_tk_ultima.py` (da co) do nguoc luat. Day la CHANG 0 gia tri nhat. |

Them tu khoa/nguon: sua `cao_mql5/github/forum/youtube` trong `lab.py`.

## CAI DAT (tren VPS treo cung bot)
VPS nhe la du — lab chi goi API + chay tester tuan tu, khong ton GPU.
```
pip install requests yt-dlp
setx DEEPSEEK_API_KEY "sk-..."      # mo lai terminal sau lenh nay
```
Sua trong `lab.py` neu duong dan khac may:
- `MT5` / `MT5_DATA` : terminal MetaTrader 5 co du lieu M1 (mac dinh la terminal
  MetaQuotes co 13 nam EURCAD M1).
- EA `LuoiDoiXung.ex5` phai da bien dich trong terminal do.

## CHAY
```
python lab.py --kho                 # che do KHO: chi cao+luu, KHONG ton API (kiem duong ong)
python lab.py --vong 1              # mot vong day du (co goi DeepSeek + tester)
python lab.py --lien-tuc --nghi 1800   # 24/7, nghi 30 phut giua cac vong
```
Treo 24/7 tren VPS (chay nen, tu bat lai neu tat):
```
# Windows: dung Task Scheduler goi:  pythonw lab.py --lien-tuc --nghi 1800
# hoac vong PowerShell:
while($true){ python lab.py --vong 1; Start-Sleep 1800 }
```

## THU VIEN (ket qua tich luy)
SQLite `thu_vien.db`:
- `muc`     : nguon da cao (chong trung bang hash URL)
- `co_che`  : co che da rut + diem + phan_quyet (THAT/AO/KHONG_ANH_XA/CHUA_RO) + PF/lai/DD
- `moc`     : cau hinh tot nhat hien tai (khoi tao = EURCAD ema50-2atr, PF 1,71)

Xem nhanh:
```
python -c "import sqlite3;c=sqlite3.connect('thu_vien.db');
[print(r) for r in c.execute('select ten,diem,phan_quyet,pf from co_che order by diem desc limit 20')]"
```

## AN TOAN / PHAP LY (ghi trong prompt, va lab tuan theo)
- Chi cao nguon CONG KHAI. Khong truy cap tai khoan khong duoc phep.
- Investor pw chi dung khi chu tk tu nguyen cong khai (nhu cach do nguoc Ultima).
- Chi doc MA NGUON (.mq5/.mqh/.pine/.py), khong chay binary la khong ro nguon.

## THANG DIEM (0-12, DeepSeek cham o B2)
- moi so voi thu vien (0-3)
- kiem duoc bang OHLC (0-3)
- hop tai san co du lieu M1 (0-3)
- co bang chung song: tai khoan that/review/thoi gian ton tai (0-3)
Chi co che >= 8 vao hang doi kiem chung. Phan quyet THAT chi khi PF>=1,15 VA duong
>=2 cap VA duong ca hai nua giai doan (CHANG 5 cua playbook).

## MO RONG TIEP (khi co che khong anh xa duoc vao EA khung)
B3 tra `anh_xa_duoc=false` + `can_input_moi` -> orchestrator ghi vao `co_che.phan_quyet
='KHONG_ANH_XA'`. Day la hang doi cho pha VIET EA MOI: dua mo ta do cho mot phien
Claude Code (hoac DeepSeek-coder) sinh EA moi, bien dich, roi dua tro lai vong test.
