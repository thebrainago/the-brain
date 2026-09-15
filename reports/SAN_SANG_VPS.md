# SAN SANG VPS

Dich: **VPS chay 24/7 nhieu thang** (chu du an chot 12/09/2026).

## 1. DA SAN SANG

- duong dan tuyet doi go cung trong ma nguon: **27** <- PHAI SUA truoc khi chuyen
  - `C:\Users\SV STORE\Downloads\Research SP500\lab` (chup_darwinex.py, 10x)
  - `C:\Program Files\XM MT5\terminal64.exe` (chay_tester_z5.py, 5x)
  - `C:\Users\SV STORE\Downloads\Research SP500` (cross_pair_quet.py, 4x)
  - `C:\Users\SV STORE\AppData\Roaming\MetaQuotes\Terminal` (ea_tu_dong.py, 4x)
  - `C:\Program Files\MetaTrader 5\terminal64.exe` (mt5_chay_ichimoku.py, 4x)
- thu vien Python: du het

## 2. PHAI MANG THEO

Tong **1.76 GB**:

- `nao.db` — 1.59 GB
- `reports` — 0.08 GB
- `data` — 0.07 GB
- `config` — 0.01 GB
- `thu_vien.db` — 0.00 GB

## 3. PHAI CAI / LAM LAI TREN VPS

### phien Telegram — co san

telethon_thebrain.session

→ dang nhap lai telethon tren VPS (`b tele`)

### kho khoa cc-switch — co san

C:\Users\SV STORE\.cc-switch\cc-switch.db

→ chep file .db nay sang VPS, hoac dat OPENAI_API_KEY/OPENAI_BASE_URL truc tiep

### terminal MT5 + tai khoan — co san

goi duoc thu vien

→ cai MT5 tren VPS, dang nhap tai khoan, va nho CHI CO MOT terminal - mot viec tester treo se chan ca lan

### Chrome + CDP cho doc_trinh_duyet — chua biet

chi biet khi chay that

→ chay Chrome headless rieng tren VPS (`b trinh-duyet`)

## 4. CAN CHU DU AN

### Bat duong bao EVO ra Telegram — **CHUA**

*Vi sao:* chay nhieu thang khong nguoi truc thi EVO phai TU NOI RA; `chat_id` hien la 0

*Lam the nao:* chay `b xa` roi nhan cho bot mot tin bat ky - cau se bat lay chat_id va ghi vao config

### Nap quota cho duong LLM — xong

*Vi sao:* qwen chay duoc nhung tai khoan AI Box am quota -> moi loi goi tra 403

*Lam the nao:* nap tien, hoac dat OPENAI_API_KEY cua nha cung cap khac

### Chon cach he tu khoi dong lai sau khi VPS reboot — chua quyet

*Vi sao:* memory `24-7-chet-vi-lease-windows`: Task Scheduler tung bi Access denied tren may nay

*Lam the nao:* quyet dinh: Task Scheduler / dich vu Windows / `dieu_phoi.py` chay duoi mot phien dang nhap giu mai

## Bien moi truong

Deu co mac dinh nen khong bat buoc, tru API key:

- `OPENAI_API_KEY` — chua dat
- `OPENAI_BASE_URL` — chua dat
- `ANTHROPIC_API_KEY` — chua dat
- `DEEPSEEK_API_KEY` — chua dat
- `QWEN_CPU` — chua dat
