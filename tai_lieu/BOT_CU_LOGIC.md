# BOT CU CUA CHU DU AN - LOGIC CON LAI TRONG REPO (03/10/2026)

May nha cai lai Windows, mat sach file cua ba bot cu: **BigMouse, DCA Am Duong, BlackDragon**. Chu du an: *"mat roi, con logic thi may ra tim duoc thoi,
cai toi can la logic chu khong quan trong file"*. Theo `CLAUDE.md` (LAM LAI TU DAU) ket qua cu cua cac bot nay la **boi canh / nguon sinh gia thuyet, khong phai bang chung**.

**CAP NHAT 03/10 chieu (chu du an):** *"bot cu khong con gi dau, toi cung chua chay bao gio"* -> khong co tai khoan nao tung chay ba bot nay, tuc la **KHONG co lich su lenh de lay**. Muc 1 (lich su tai khoan / mat khau investor) va muc 3 (Windows.old, o E:, Saved Messages) o duoi **HET Y NGHIA**: dung hoi so tai khoan, dung xin mat khau investor, dung quet o dia cho ba bot nay.
Con lai: logic da co trong bang tren + muc 2 (nguon goc: tac gia / clip / nhom, neu chu du an con nho) + muc 4 (mua / tai lai neu la san pham co ten). Moi thu thu duoc la **NGUON SINH GIA THUYET** (di qua `b nc`), khong phai bang chung.

## Repo con nho gi (tim trong ma nguon + tai lieu, khong doan)

| Bot | Logic con trong repo | Con thieu |
|---|---|---|
| **BigMouse** (T91 BigMouse / T95 HedgingCover), luoi tren AUDCAD | `mo_phong_v2.py` (khai bao dau file): mo CA HAI chieu, Buy va Sell cach nhau mot khoang · he so nhan lot THEO NHOM (2,0 cho 4 lenh dau roi 1,6) · cat hoa bat theo SO LENH (`Solenh_KichhoatCatHoa`) · chot ca ro theo TIEN (`Target_Exit_All`), dung lo theo TIEN (`Max_CutLoss_All`). He nen `_thu_quan_tri.py`: luoi AUDCAD cau hinh BigMouse `.set` that + dung lo 400 + hedge 3 tang / 0,5 | file `.set` that va ban `.ex4/.ex5` (nhat ky 05/09 co ghi da boc `.set` that, commit `c62bfc7` - KHONG con trong lich su git nay). Con so cu (62%/nam von 33$ cent; 121,6%/nam von can 1.010$) la so CU, chua tai lap duoc. `THE_BRAIN.md` ghi BigMouse tung "pha san -19.970$" tren backtest dai (nhan lot) - tieu chi duyet moi (25/09) khong con chan martingale, chi can lai sau phi + maxDD < 80% |
| **DCA Am Duong** (V20.8, tac gia DongDongTV) | loc Supertrend + loc KHOANG CACH gia-Supertrend (`mo_phong_v2.py`) · lot ban dau 0,05 (`Lot_BatDaub/s`) · chot/lo TOAN CHUOI theo tien (`tpAll_Money = 1000`, `useTSCloseAll`) (`reports/chuyen_giao/2026-08-13/CLAUDE.md` muc 37). Luat da moi tu clip 12 phut cua tac gia (`LAB_MASTER_PROMPT.md`) | danh sach input day du (nam trong muc "Dau vao" cua bao cao `.htm` cua tester - da mat). Ket qua test cu: **am** (`HANDOFF.md`: "DCA Am Duong am 100%") nen khong phai he ra tien da kiem chung. "Session V3" la bot KHAC cua cung tac gia |
| **BlackDragon** | **khong co dau vet nao** trong ma, tai lieu, nhat ky, lich su git (cac cho co chu "Dragon" la he Sonic R) | tat ca |

## Cach lay lai LOGIC (muc 1 va 3 DA HET Y NGHIA tu 03/10 chieu - xem cap nhat o tren)

1. **Lich su lenh cua chinh tai khoan da chay ba bot** - san van giu neu tai khoan con. Co 2 duong, deu chi DOC: (a) mat khau INVESTOR (chi xem) -> `b link them` o may nha roi
   `b link tai-khoan-xem`; (b) trong MT5: tab Lich su tai khoan -> chuot phai -> Toan bo lich su -> Bao cao -> HTML, tha tep vao `du_lieu_cao/tha_vao/` roi `b link thu-muc`.
   Sau do `b nc cc boc_lich_su` giai ra luat (vao lenh, nap them, chot, cat) - dung chuoi "LAY lich su lenh -> HIEU luat -> LAM LAI" cua du an.
2. **Noi chu du an lay ba bot** (nhom Telegram / Zalo / clip / nguoi ban): tac gia thuong tu noi tham so trong clip hoac tin nhan; dua link vao `b link them`.
3. **Cac cho co the con file** (chi tim, khong chay): thu muc `C:\Windows.old` (neu chua don; DUNG chay "Don dia" cho den khi xem xong), o E:, "Saved Messages" Telegram, thu / Drive.
   Tim theo ten bot va duoi `.set .ex4 .ex5 .mq4 .mq5 .htm`. File la chi duoc LIET KE, khong chay.
4. Mua lai / tai lai tu MQL5 Market hoac noi ban dau (neu la san pham co ten).

## Can chu du an tra loi (con MOT cau)

* **Lay ba bot o dau** (nhom nao, tac gia nao, clip nao)? Con link khong? Day la nguon DUY NHAT con lai de lay them logic (tham so cua tac gia, clip huong dan). Da tra loi 03/10: tai khoan / mat khau investor / lich su lenh = khong co; bot nao co lai that = chua tung chay.
