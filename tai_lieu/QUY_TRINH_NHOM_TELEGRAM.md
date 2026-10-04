# QUY TRINH NHOM / KENH TELEGRAM -> EA (nha viet 04/10/2026, chu du an duyet 4 nhom dau)

Muc dich: nhom Telegram co nhieu bot EA -> vao, theo doi, liet ke bot, tai file, doc logic -> dua vao day chuyen "LAN EA THO" (`LAN_EA_THO.md`).
Repo PUBLIC: KHONG ghi so dien thoai, ma dang nhap, mat khau, ID/investor cua nguoi khac, tep tho cua nhom. Tep tho chi o `du_lieu_cao/telegram/<nhom>/` (gitignore).

## A. Cach vao (da chay that 04/10)
1. Chrome THAT Profile 3 (khong CDP9224, khong ban sao ho so: mat dang nhap, xem CLAUDE.md "LAY DU LIEU TU TRANG CAN DANG NHAP"): `web.telegram.org/k/`.
2. Dang nhap bang so dien thoai cua chu du an: Telegram gui ma 5 so vao app Telegram cua chu du an -> CHI chu du an doc duoc, hoi 1 lan. Phien luu trong Profile 3, lan sau khong hoi lai. Neu co mat khau 2 lop: hoi chu du an. Dung bam "Yes it's me / No" o canh bao thiet bi moi (la thiet bi cua chu du an, bam nham co the ngat phien).
3. Thao tac bang pyautogui + pyperclip (dan, KHONG go phim; go phim rot ky tu). Chup man hinh `pyautogui.screenshot` roi doc.
4. Mo nhom: dung o TIM KIEM ben trai (click -> dan ten @ -> chon ket qua "Global search"). Dan URL `#@ten` + F5 khong on dinh (nhieu lan khong doi trang). Link rieng `t.me/c/<id>/<post>` KHONG mo duoc neu chua la thanh vien -> can link moi `t.me/+...`: xin chu du an.
5. Theo doi: nhom dien dan = menu ⋮ -> "Join Group"; kenh = nut SUBSCRIBE; nhom thuong = nut JOIN. Chi tham gia nhom chu du an da duyet; KHONG nhan tin, KHONG tha cam xuc, KHONG nhan rieng.

## B. Cau truc thuong gap
- Nhom dien dan (forum) = nhieu CHU DE (topic): KHO BOT / KHO CODE MQ4 / KHO INDICATOR / KHO COPYTRADE / HOI DAP / HUONG DAN CAI. Bot nam o KHO BOT va KHO CODE; hoi dap o chu de rieng (co bot tra loi).
- Tin dang file: "Forwarded from <tac gia>" + file (.ex5/.ex4 / .zip / .set) + mo ta (tinh nang, backtest tu bao).
- Kenh thuong mai (khoa hoc, tin hieu) khong co bot de lay: ghi nguon, chuyen sang.

## C. Phan loai file (thu tu uu tien)
1. `.mq5`/`.mq4` hoac `.zip` chua ma nguon: DOC LOGIC, dua vao `ea_tu_dong.tai_lo` / `ea_tho_*` (uu tien so 1). Kiem giay phep (MIT/GPL ghi o dau tep), sha256 (neu co `SHA256SUMS`).
2. `.set` di kem: tham so da chon cua tac gia -> chay tester voi tung bo (dang ky la gia thuyet moi, khong phai bang chung).
3. `.ex5`/`.ex4` bien dich: KHONG doc duoc logic. Chi chay tren tester / tai khoan DEMO, tat "Allow DLL imports", khong bao gio tai khoan that. Kiem kich thuoc / ten, dua vao hang doi sau.
4. Indicator / phan mem thuong mai (ATAS, Bookmap, Sierra, NT8...): thuong la ban CRACK -> BO QUA (ban quyen), chi ghi y tuong.
5. Tin dang ID + mat khau investor cua nguoi khac: KHONG dung de dang nhap, KHONG ghi vao repo (chi bao so luong de chu du an biet).

## D. Quet an toan truoc khi tin (ma nguon)
`grep -n -i "#import\|WebRequest\|\.dll\|ShellExecute\|Socket\|ACCOUNT_LOGIN\|license\|martingale\|grid"` + doc dau tep. Co `FileOpen` chi de ghi log/state la binh thuong; co DLL/WebRequest/Socket/kiem so tai khoan = dung, hoi cloud.

## E. Ghi lai (moi bot MOT dong)
nhom / chu de / ten / loai tep / kich thuoc / tac gia (ten hien thi, khong lien he rieng) / ngay dang / mo ta tinh nang / BAO CAO CUA TAC GIA (PF, DD, giai doan: chi la TUYEN BO, khong phai bang chung) / giay phep / co ma nguon? / co .set? / duong dan tep / sha256.

## F. De xuat toi uu (cloud quyet) - quet bang MAY doc, khong bang chup man hinh
Doc bang chup man hinh cham va ton token (moi man hinh ~3k token, nhom lon hang nghin tin). Hai cach co cau truc:
- (1) Telegram Desktop `Export chat history` (JSON + media, loc theo loai tep): can cai Telegram Desktop + dang nhap them 1 lan (ma tu chu du an) - chay mot lan cho tung nhom.
- (2) Telethon (da co `telethon_ban.py`, `config/telethon_thebrain.session`): can `api_id/api_hash` tu my.telegram.org (chu du an lay 1 lan) + 1 ma dang nhap. Doc tin + tai tep co loc (`.mq5/.mq4/.zip/.set`), nhip cham, chi nhom chu du an da duyet. Day la cach nen lam cho >10 nhom (chu du an noi cac nhom khac se den).
Ca hai van phai giu: duyet tung nhom, khong tu join hang loat, khong dang tin, bao cao chi dem + ma bam, tep tho vao `du_lieu_cao/telegram/<nhom>/`.

## G. Ket qua 4 link dau (04/10, xem `reports/telegram_khao_sat_20261004.md`)
Vao + theo doi duoc 3/4; link rieng `t.me/c/...` can link moi. Tep da tai: CLMCA.zip (MIT, co ma nguon + 5 .set, XAUUSD M15, SL cung, khong martingale/grid) - ung vien dau tien cho LAN EA THO; Scalp_m5_break_fix.ex5 (bien dich).
