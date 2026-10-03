# LINK CUA CHU DU AN -> LICH SU LENH (`b link`) - 03/10/2026

Chu du an: *"co rat nhieu group co rat nhieu bot giao dich co lai ma ta chua cao duoc du toi co link dan, can khai thac phan nay sau"*.
Day la NUA DAU cua day chuyen B (`NGUON_NGUOI_THANG.md`): **link -> biet no la gi -> lay lich su lenh -> (cloud) boc luat -> lam lai thanh EA cua ta**.
Khong mo them nguon / engine moi: day la lam rong DUONG B da co, de lay duoc lich su lenh cua cac bot da chay co lai.

## Da lam / chua lam (noi that)

| Phan | Trang thai |
|---|---|
| Phan loai link (mql5, myfxbook, fxblue, tradingview, telegram, facebook, ...), RIENG hay CONG KHAI, cach lay | xong, co test (`nhan/link_nguon.py`) |
| Ke hoach cao + nhip lich su (gian cach theo ten mien, robots.txt, lui khi bi chan, nho trang thai) | xong, co test |
| Tham do trang (HTTP khong cookie / Chrome cua chu du an), nap thu muc tha vao, nap tin nhan, thu hoach bang tai khoan XEM, chia se tom tat | xong, co test (`nhan/link_chay.py`, 83 test) |
| **Chay tren TRANG THAT** | **CHUA**. Cloud khong toi duoc mql5.com / myfxbook / t.me. Lan chay dau o nha se cho thay cau truc trang that; bo doc rieng tung trang viet SAU do |
| Telegram nhom kin (liet ke nhom da vao, doc tep dinh kem) | **CHUA** - cho chu du an cho biet cac nhom nam o dau (xem duoi) |
| Facebook / Zalo / Discord / WhatsApp | KHONG tu dong (vi pham dieu khoan, rui ro khoa tai khoan): chu du an dan chu hoac luu trang |

## Cach dung o may nha (moi buoc tu dung o do neu hong)

```
git pull
python b.py link                         ke hoach: bao nhieu link, nen tang nao, lay bang cach nao (KHONG goi mang)
python b.py link them "<link hoac ca tin nhan dan nguyen>"     vao link_rieng.txt (khong len git) + tai khoan xem neu co
python b.py link tham-do https://mql5.com/signals/<id>         thu MOT link cong khai (xem OK / bi chan / robots)
python b.py link chay --toi-da 12        tham do MAU (it link, cham, moi nen tang toi da 2 link / luot)
python b.py link chay --cdp              them link can dang nhap: dung Chrome da dang nhap san cua chu du an (CDP)
python b.py link thu-muc                 nap du_lieu_cao/tha_vao/ (bao cao lich su .htm/.csv, Telegram result.json, zip)
python b.py link tai-khoan-xem           thu hoach lich su bang tai khoan XEM (investor) da luu - can MT5 o may nha
python b.py link bao-cao                 in lai ba bao cao gan nhat
```

Chu du an chi can: (1) dua link / tin nhan, (2) luu tay cac bao cao lich su vao `du_lieu_cao/tha_vao/` neu trang khong cho may doc,
(3) dang nhap Chrome mot lan neu muon doc trang can dang nhap. Phien cloud chi ra don cac lenh an toan (`ke-hoach`, `chay`, `tham-do` voi ten mien cong khai
da duyet, `thu-muc`, `bao-cao`, `chia-se`); `them`, `tai-khoan-xem`, `--cdp` chi chu du an chay tay.

## Mot link duoc lay bang cach nao

| Cach | Dung cho | Ghi chu |
|---|---|---|
| `http` | trang cong khai khong can dang nhap | khong cookie, UA trung thuc (khong gia nguoi), khong bao gio theo chuyen huong ra ngoai ten mien |
| `cdp` | trang can dang nhap (Chrome cua chu du an) | chi doc ten cac goi du lieu va bam tab lich su; chua thu o may that |
| `telethon` | tin nhan / tep trong nhom Telegram | can dang nhap Telegram mot lan o nha - chua viet |
| `thu_cong` | Facebook, Zalo, Discord, WhatsApp, kho tep | chu du an luu trang / dan chu vao `du_lieu_cao/tha_vao/` |

## Cac luat cung (repo nay la PUBLIC)

* **Link rieng KHONG vao git**: link moi vao nhom, nhom Facebook, kho tep, link co token / user:pass. `link_rieng.txt` va `du_lieu_cao/` nam trong `.gitignore`.
  Bao cao di len git / ve cloud chi co **ma bam + nen tang + loai trang + so dem** (khong URL rieng, khong ten tep, khong mat khau).
* **Khong ne chan, khong gia nguoi**: gap 429 / 403 / captcha / Cloudflare -> DUNG ten mien do va bao chu du an; khong doi UA/IP, khong thu lai dap.
  robots.txt cam -> khong cao. Moi ten mien co gian cach rieng, thu lai theo cap so nhan.
* **Khong tu tai file thuc thi** (.exe / .ex4 / .ex5 / .zip la). File `.ex4/.ex5` chu du an tha vao chi duoc LIET KE (ten, kich thuoc, ma bam), khong chay.
* **Mat khau investor** (chi doc) nam o `config/passview.json` (ngoai git), khong vao thu, khong vao bao cao; loi MT5 co chua so tai khoan duoc che truoc khi ghi.
* Lich su lenh cua nguoi thang co **sai lech nguoi song sot**: chi la GIA THUYET de phat lai va thu tren gia that cua ta, khong phai bang chung.

## Dau ra

`reports/link_nguon_ke_hoach.{md,json}` · `reports/link_chay_ket_qua.{md,json}` · `reports/link_nap_ket_qua.md` · `reports/link_tai_khoan_xem.json`
(tat ca an toan de len git). Lenh that o `du_lieu_cao/lenh/` (ngoai git) -> `python b.py nc cc boc_lich_su '<json>'` giai ra luat vao / nap them / chot / cat.

## Viec tiep theo (sau lan chay dau o nha)

1. Doc `reports/link_chay_ket_qua.md`: link nao OK / bi chan / can dang nhap -> cloud viet bo doc that cho trang co lenh (MQL5 signals tab History, Myfxbook, FX Blue).
2. Chu du an cho biet cac nhom o dau (Telegram / Zalo / Facebook / Discord) -> chi viet them phan Telegram neu dung la Telegram.
3. Lich su lenh vao `boc_lich_su` -> `thu_luoi` tren doan kham pha -> xac nhan MOT lan (khong them nguon neu chua co `DAT` o xac_nhan).
