# LAN EA THO - chay EA cong khai THANG tren MT5 tester (03/10/2026)

Y chu du an: *"tren mql5 va myfxbook co nhieu link cong khai da co hieu qua -> boc tach logic -> tao chien luoc ->
backtest -> tinh chinh"*. So do `hethong.txt` dong 38/55/60: **dung truc tiep file EA, backtest file co san truoc,
moi thu test tren phan mem trade**. Lan nay la duong do. Ma: `nhan/ea_tho.py` (quyet dinh, test duoc tren Linux) +
`nhan/bao_cao_mt5.py` (doc bao cao tester thanh so). Ban rut gon vi sao: `RA_SOAT_KIEN_TRUC_03102026.md`.

## Chay o may nha (MOI phep do qua `b nc cc`, de vao so tay `nc.db`)
```
python ea_tu_dong.py --tai 24                    # tai EA tu MQL5 Code Base -> reports/ea/kho.json (TOC DO THAP: IP bi cam sau ~50-150 request)
b nc cc ea_tho_kham  '{"ea":"kho:3"}'            # thuan, khong tester: CHIEN_LUOC hay TIEN_ICH, ma/khung nham toi, luoi tham so
b nc cc ea_tho_chay  '{"ea":"kho:3","ma":"EURUSD","khung":"H1","doan":"kham_pha"}'
b nc cc ea_tho_quet  '{"eas":["kho:*"],"toi_da_lan":6}'    # phan loai HET truoc, bo cong cu, chay chien luoc o ma/khung nham toi
b nc cc ea_tho_tinh  '{"ea":"kho:3","ma":"EURUSD","khung":"H1"}'   # luoi quanh MAC DINH cua tac gia -> xac_nhan DUNG bo do
```
Cloud giao viec: `b cau giao -- nc cc ea_tho_quet '{"eas":["kho:*"]}'` (danh sach trang da nhan `("nc","cc")` + moi ten
trong `CC.THEO_TEN`, khong can sua whitelist). `ea` = duong dan .mq5 hoac `kho:<so>` / `kho:<mot doan tieu de>`.

## Cau hinh `config/ea_tho.json` (tuy chon; khoa la cac khoa cua `ea_tho.MAC_DINH`)
`model` (4) · `von` (10000) · `don_bay` (100) · `han_giay` (1800) · `chat_luong_toi_thieu_pct` (90) ·
`tick_tu` ("YYYY-MM-DD" ngay som nhat co tick that) · `hau_to_symbol` · `ban_do_symbol` ({"XM_US500CASH":"US500Cash"}) ·
`da_hieu_chuan_lenh_mo` · `nhan_them` ({"so_lenh":"<nhan bao cao tieng Viet>"}) · `tu_nap`.

## Ky luat (cung bo luat cua `nc_thi_nghiem`)
- Doan du lieu lay tu `so_cai/doan.json` (DONG BANG theo ngay) + 1 ngay cach ly. kham_pha va xac_nhan: cung van tay tra lai tu so tay.
- DAT = **co lai sau phi VA maxDD < 80%** (`cham_diem.TRAN_SUT_GIAM`). Martingale / luoi / DCA hop le. Do la "canh bac co ky vong
  duong do duoc", chua phai chan ly. PF > 4 hay lai qua dep = nghi nhin truoc, kiem `nhan_canh_bao`.
- niem_phong: MOT lan cho mot bo (EA, ma, khung, tham so, von, model); toi da 3 lan / dong gia thuyet; can mot xac_nhan DAT dung bo
  tham so do; >= 20 lenh; Model=4 va chat luong lich su >= 90% (chi phi phai DO DUOC). Hong ha tang (khong doc duoc bao cao,
  tester chet, cua so ngoai tick that) = `CHUA_DO_DUOC`, KHONG tieu mot lan mo, khong lo so. EA co phieu (AAPL...) khong duoc dat len FX.

## HIEU CHUAN truoc khi tin bat ky DAT nao (4 diem CHUA kiem voi may that)
1. **Lenh con MO luc het cua so**: chay EA mau mua-giu (mua tick dau, khong SL/TP) mot cua so ~60 ngay, so lai bao cao voi
   (dong - mo) x lot x co hop dong. Bao cao co tinh lo lai troi khong? Dung roi dat `da_hieu_chuan_lenh_mo: true`
   (chua dat thi `nhan_canh_bao` luon gan nhan "CHUA hieu chuan: lenh con MO luc het cua so...").
2. **Nhan bao cao tieng Viet**: luu 1 bao cao that vao `test_bao_cao_mt5.py` (mau that dau tien). `doc_duoc=False` thi xem `thieu`,
   them nhan vao `nhan_them`. Bay da biet: "Loi nhuan rong" = Gross Profit; lai that = "Tong loi nhuan rong".
3. **Do sau tick that cua XM demo**: ghi `tick_tu`. Cua so nam ngoai tick that -> `ha_tang`, khong ra so.
4. **`_chay_that`** (slot -> bien dich -> tester -> log agent) chua chay lan nao. Chay 1 EA dem duoc, doc truong `log` neu hong.

## Gioi han (noi that)
Lan nay KHONG boc logic; no do EA nguyen ban. Y nghia: EA nao ra DAT tren xac_nhan la **manh moi co bang chung** cho nhanh
boc tach (doc ma EA do de ra gia thuyet co che) va cho HEPHAESTUS (luoi tham so). EA tien ich (5/12 mau da do) bi bo, khong tinh.
Nhanh nhat tim EA tot: EA ban cong khai co ho so tin hieu con song (MQL5 Signals) - tin hieu AUDCAD luoi/DCA chinh la loai nay.
