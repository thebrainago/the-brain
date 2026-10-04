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
b nc cc ea_tho_chay  '{"ea":"D:/bot/CLMCA.mq5","ma":"XAUUSD","khung":"M15","gt_id":7,"bo_set":"D:/bot/CLMCA_Gold.set"}'   # .set cua tac gia, NGUYEN VAN
b nc cc ea_tho_chay  '{"ea":"D:/bot/Bot_v3.ex5","ma":"XAUUSD","khung":"M15","gt_id":7,"bo_set":"D:/bot/XAU_M15.set"}'      # EA NHI PHAN (khong ma nguon)
```
Cloud giao viec: `b cau giao -- nc cc ea_tho_quet '{"eas":["kho:*"]}'` (danh sach trang da nhan `("nc","cc")` + moi ten
trong `CC.THEO_TEN`, khong can sua whitelist). `ea` = duong dan `.mq5` | `.ex5` | `kho:<so>` / `kho:<mot doan tieu de>`.

## Cau hinh `config/ea_tho.json` (tuy chon; khoa la cac khoa cua `ea_tho.MAC_DINH`)
`model` (4) · `von` (10000) · `don_bay` (100) · `han_giay` (1800) · `chat_luong_toi_thieu_pct` (90) ·
`tick_tu` ("YYYY-MM-DD" ngay som nhat co tick that) · `hau_to_symbol` · `ban_do_symbol` ({"XM_US500CASH":"US500Cash"}) ·
`da_hieu_chuan_lenh_mo` · `nhan_them` ({"so_lenh":"<nhan bao cao tieng Viet>"}) · `tu_nap` · `tep_san` (["MultiPivots.mqh", "ZigZagPro"]: tep/chi bao EA can ma terminal nay DA CO; khop theo ten khong duoi).

**`THIEU_TEP`**: EA can `.mqh` / chi bao / dll ma may chua co (vd `#include <MultiPivots.mqh>`) bi loai truoc khi chay, khong ton luot tester, khong tao gia thuyet. Tai GOI DAY DU cua tac gia, dat vao thu muc `MQL5` cua terminal, them ten vao `tep_san`, goi lai. Do 22 EA that: 9/16 chien luoc vap rao nay - day la rao lon nhat cua duong chay thang.

## Ky luat (cung bo luat cua `nc_thi_nghiem`)
- Doan du lieu lay tu `so_cai/doan.json` (DONG BANG theo ngay) + 1 ngay cach ly. kham_pha va xac_nhan: cung van tay tra lai tu so tay.
- DAT = **co lai sau phi VA maxDD < 80%** (`cham_diem.TRAN_SUT_GIAM`). Martingale / luoi / DCA hop le. Do la "canh bac co ky vong
  duong do duoc", chua phai chan ly. PF > 4 hay lai qua dep = nghi nhin truoc, kiem `nhan_canh_bao`.
- niem_phong: MOT lan cho mot bo (EA, ma, khung, tham so, von, model); toi da 3 lan / dong gia thuyet; can mot xac_nhan DAT dung bo
  tham so do; >= 20 lenh; Model=4 va chat luong lich su >= 90% (chi phi phai DO DUOC). Hong ha tang (khong doc duoc bao cao,
  tester chet, cua so ngoai tick that) = `CHUA_DO_DUOC`, KHONG tieu mot lan mo, khong lo so. EA co phieu (AAPL...) khong duoc dat len FX.

## `tham_so` BI KIEM, khong bi bo qua im lang (04/10/2026)
MT5 **bo qua im lang** mot khoa `.set` khong phai input cua EA (chay mac dinh, khong bao loi) - nen mot `tham_so` go sai ten
tung chay mac dinh nhung ghi so tay nhu "da thu bo khac". Nay `lap_lenh` tra `CHUA_DO_DUOC` (khong ton luot tester, khong
mot phep thu, khong ghi so tay) khi:
- khoa **khong phai input** cua EA: loi neu ten khoa, danh sach input that cua EA, va **goi y gan giong** (`InpFasst -> InpFast`).
  Input khai sau `//` (comment) khong tinh. EA co `.mqh` / chi bao cua tac gia (`co_input_ngoai`): khong biet het input nen BO buoc nay,
  khoa la chi vao `lenh["khoa_chua_kiem"]` + `nhan_canh_bao`; cac kiem khac van chay;
- gia tri **khong phai so huu han** (chuoi, None, NaN, inf, so nguyen khong lo) - `tham_so` chi dua duoc input SO; input chuoi / ten enum /
  ngay xuong tester la viec cua `bo_set`;
- input kieu nguyen / `ENUM_*` / `bool` nhan **so le** (8,5), hoac `bool` ngoai 0 / 1. `True` = 1.
`8` va `8.0` la mot (van tay khong doi so voi nhung thi nghiem da co).

## `bo_set`: chay NGUYEN VAN file `.set` cua tac gia (04/10/2026)
EA nhieu chien luoc chon bang input (CLMCA co 5 `.set`; CCBSN 10 `.set`) khong bieu dien duoc bang `tham_so` so. `bo_set` = duong dan
file `.set`: ghi vao `Profiles\Tester` **nguyen van** (bool, chuoi, ten enum di nguyen, khong dich sang so).
- `doc_set` doc UTF-16 co BOM / UTF-8; bo dong trong, `;` comment, hau to toi uu `||start||step||stop||Y` (chay MOT lan, khong toi uu);
  chi nhan duoi `.set`; `Khoa=GiaTri`, khoa lap / dong sai / ky tu dieu khien / > 200 ky tu / > 500 khoa / > 200 000 byte bi tu choi;
  dong kieu MT4 (`InpFast,F=0`) bi tu choi. **Loi KHONG in noi dung dong sai.**
- **`bo_set` va `tham_so` loai tru nhau** (doi mot input = sua `.set` = mot bo KHAC = mot phep thu khac).
- **Van tay** = sha cua van ban `.set` da lam sach (khoa sap xep): doi ten file / thu tu dong / bo `||...` khong doi van tay, doi MOT gia tri
  (ke ca `true` -> `false`, `8` -> `8.0`) la bo khac. Moi `.set` khac = mot phep thu duoc dem; nhieu `.set` cua mot EA di duoi **CUNG** `gt_id`.
- Khoa trong `.set` ma EA khong khai = `bo_set.khoa_la` + canh bao (MT5 bo qua; co the la `.set` cua ban EA khac). EA co `.mqh`: `doi_chieu: "mot_phan"`.
- **BAO MAT**: van ban `.set` vao so tay roi ra git **CONG KHAI** (`so_cai/nc/*.jsonl`). `doc_set` TU CHOI `.set` co khoa nhay cam
  (token / passw / secret / licen[sc]e / api_key / webhook / credential / investor) mang gia tri khong phai so ngan hay true/false, hoac gia tri
  mang dang khoa that (token Telegram, `sk-`, `ghp_`, `xox`, `AKIA`, `AIza`). Loi chi neu TEN khoa. Xoa gia tri do trong `.set` roi chay lai (la bo khac).
- Niem phong: bo `.set` phai la **dung bo** da qua xac_nhan DAT (cung van tay); bo khac / mac dinh / `tham_so` bi chan, thong bao "CHINH bo".

## EA NHI PHAN (`.ex5`, khong ma nguon) - HOP DEN (04/10/2026)
Nhieu bot tot (CCBSN, Black Dragon, Gold Hunter...) chi co `.ex5`. `ea` = duong toi file `.ex5`; chay duoc **chi voi `bo_set` hoac mac dinh**
(`tham_so` bi tu choi: khong co ma de doi chieu ten input). **Day la hop den**: khong doc luat / input, khong kiem duoc nhin truoc, khoa ban quyen
hay ngay het han - chi do duoc KET QUA tren tester. DAT cua no **chua phai "cua ta"**: muon thanh EA cua ta phai boc luat tu lich su lenh tester roi viet lai
(`boc_lich_su` + `luoi.py`); nhung ket qua hop den la DAP AN de hieu chuan ban viet lai. `ea_tho_kham` tra `NHI_PHAN` (khong chon ma / khung ho);
`ea_tho_quet` bo qua (`bo_qua` loai `NHI_PHAN`); `ea_tho_tinh` tu choi - chay tung `.set` cua tac gia bang `ea_tho_chay(bo_set=...)` duoi cung `gt_id`.

**Dieu kien an toan** (nhanh nhi phan chi COPY file vao terminal cho tester, KHONG thuc thi o ngoai tester):
1. chi `.ex5`: `.ex4` / `.mq4` (MT4 - tester MT5 khong chay duoc), `.zip .rar .7z .exe .msi .dll .bat .cmd .ps1 .vbs .scr .jar .iso .lnk` bi tu choi
   (khong giai nen, khong chay bo cai). Tep 512 byte .. 30 MB; **van ban / HTML / JSON dat ten `.ex5`** (trang bao loi cua Drive / Telegram) bi nhan ra va tu choi.
2. **`Allow DLL imports` phai TAT** o terminal: doc `<thu muc du lieu>/config/common.ini` muc `[Experts]` khoa `AllowDllImport`. BAT, hoac tep co ma khong doc duoc
   -> tu choi **truoc khi copy** (`ha_tang`, `CHUA_DO_DUOC`, khong ton phep thu). Khong co tep / khong co khoa = tat (mac dinh MT5).
3. sha **kiem lai luc copy** (file doi giua luc lap van tay va luc chay -> tu choi); ban copy o `MQL5\Experts\_tu_dong` **xoa ngay sau khi chay** (ke ca khi tester no loi).
4. Chi tren tester / tai khoan DEMO. Khong nhan bo cai dat cua nguoi khac.
5. **Khong bao gio vao git** (repo PUBLIC; ban quyen cua nguoi ban): `.gitignore` chan `*.ex5 *.ex4 *.dll *.exe *.msi *.rar *.7z` (+ zip, + `du_lieu_cao/`). Tep goc chi o may nha.
   So tay chi giu sha + dung luong + van ban `.set`. Ket qua niem phong ghi ro "hop den".

## HIEU CHUAN truoc khi tin bat ky DAT nao (5 diem CHUA kiem voi may that)
1. **Lenh con MO luc het cua so**: chay EA mau mua-giu (mua tick dau, khong SL/TP) mot cua so ~60 ngay, so lai bao cao voi
   (dong - mo) x lot x co hop dong. Bao cao co tinh lo lai troi khong? Dung roi dat `da_hieu_chuan_lenh_mo: true`
   (chua dat thi `nhan_canh_bao` luon gan nhan "CHUA hieu chuan: lenh con MO luc het cua so...").
2. **Nhan bao cao tieng Viet**: luu 1 bao cao that vao `test_bao_cao_mt5.py` (mau that dau tien). `doc_duoc=False` thi xem `thieu`,
   them nhan vao `nhan_them`. Bay da biet: "Loi nhuan rong" = Gross Profit; lai that = "Tong loi nhuan rong".
3. **Do sau tick that cua XM demo**: ghi `tick_tu`. Cua so nam ngoai tick that -> `ha_tang`, khong ra so.
4. **`_chay_that`** (slot -> bien dich -> tester -> log agent) chua chay lan nao. Chay 1 EA dem duoc, doc truong `log` neu hong.
5. **Nhanh nhi phan + `bo_set`** chua chay voi MT5 that (logic kiem bang test gia tren Linux). Can xem: (a) MT5 co nap dung `.ex5` copy vao
   `MQL5\Experts\_tu_dong` va `.set` ten kem khong (`.ini` dung `Expert=_tu_dong\<ten>` + `ExpertParameters=<nhan>.set`); (b) bot kiem tra ban quyen
   qua WebRequest (tester chan) co the KHONG vao lenh -> it lenh -> `CHUA_DO_DUOC`, khong phai AM; (c) lenh dau tien nen la `ea_LuoiThamChieu`
   (diem 4) truoc khi chay bot la. Hong thi doc truong `log`, sua ha tang, khong tieu niem phong.

## Gioi han (noi that)
`ea_tu_dong.tai_lo` chi lay van ban `.mq5` CHINH tren trang CodeBase (khong .zip, nghi 3 giay/bai): EA nhieu file mat `.mqh` -> `THIEU_TEP`. Tai goi day du can mot trang CodeBase that cua EA nhieu file lam fixture (cloud khong ra duoc mql5.com) - viec cua may nha, xem thu chi thi 03/10.

Lan nay KHONG boc logic; no do EA nguyen ban. Y nghia: EA nao ra DAT tren xac_nhan la **manh moi co bang chung** cho nhanh
boc tach (doc ma EA do de ra gia thuyet co che) va cho HEPHAESTUS (luoi tham so). EA tien ich (5/12 mau da do) bi bo, khong tinh.
Nhanh nhat tim EA tot: EA ban cong khai co ho so tin hieu con song (MQL5 Signals) - tin hieu AUDCAD luoi/DCA chinh la loai nay.
