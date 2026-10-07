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

## EA LUOI DAY DU `ea_LuoiDayDu.mq5` (04/10/2026) - EA cua ta, chay duoc khai bao tn5
`ea_LuoiThamChieu.mq5` chi lam luoi toi thieu. Khai bao tot nhat cua du an (tn5: AUDCAD M15, buoc 21 x1,2, TP 9, tran 9, lot CONG 0,25, TIA LENH bien 5)
can them lot cong, buoc gian dan, tia lenh, cho lui, chot theo tien: file nay co DU moi truong cua `luoi.ThamSo` (bang ten `nhan/ea_gia_lap.BANG_TEN`;
test `test_bang_ten_phu_het_truong_thamso` do khi ai them truong vao `ThamSo` ma EA chua co input). Bo tham so cu cua `ea_LuoiThamChieu` chay y nguyen.

**Cach chay (may nha, SAU hieu chuan diem 4 / B1)**: `b nc cc ea_tho_chay '{"ea":"ea_LuoiDayDu.mq5","ma":"AUDCAD","khung":"M15","doan":"kham_pha","gt_id":N,
"tham_so":{...}}'` voi `tham_so = ea_gia_lap.tham_so_ea_tu_luoi(ThamSo(...))` (vi du tn5: InpLot 0,04 InpStepPips 21 InpStepMult 1,2 InpTpPips 9 InpMaxLevels 9 InpMode 2
InpLotKind 2 InpLotMult 0,25 InpSpark 1 InpSparkPips 5). **Chon InpLot sao cho lot x he la boi cua buoc lot** (0,04 voi cong 0,25): EA lam tron lot theo buoc lot
cua san, engine thi khong; neu khong, khong con khop tung lenh. Doi chieu: cung `ma`/`khung`/`doan` chay `thu_luoi` voi `ThamSo` tuong ung.

**Da kiem (cloud, khong can MT5)**: `nhan/ea_gia_lap.py` + `ea_gia_lap.cpp` bien dich CHINH van ban `.mq5` (bo `#property`, `#include` thay bang stub MQL5, `input` thanh
const) bang g++/clang++ va chay tren duong TICK voi san gia lap (hedging; `netting=True` de kiem EA tu choi). `test_ea_luoi_day_du.py` (47 test, ~25 giay):
bang ten, cu phap nghiem (-Wall, loi tro dung dong .mq5), 10 kich ban TAY (so tien tinh bang tay truoc, khong chep dau ra san gia), 12 cau hinh x 8 duong gia
doi chieu TUNG LENH voi `luoi.chay` (moi tick la mot bar, khong phi qua dem), 8 DOT BIEN (sua co chu dich ma EA -> bo so sanh phai bao lech), do khoang cach bar<->tick.
Bo do rong 04/10: 12 cau hinh x 80 duong gia, khop DUNG chieu / lot / gia mo / tick mo+dong (tru 1 tick o `chot_tien_tia*` va `buoc_co`, do muc luoi le).

**Quan he lai (do duoc, khong phai uoc luong)**: `lai_ea = so du - von - spread cua lenh con mo`. `lai_engine + phi_tia_kep - lai_ea = lech_explicada` voi `phi_tia_kep` =
spread engine tru THEM khi dong cap tia, `lech_explicada` = chenh gia tung lenh (engine mo / dong o muc luoi chinh xac, EA o tick dau vuot muc). Phan con lai `lech_con_lai`
<= 3e-12 o moi cau hinh / duong gia (spread khong doi). Spread doi giua cac tick = ngoai pham vi do nay (tester that moi cho thay).

**Khac biet con lai voi engine - KHONG phai loi EA (task #48, chua sua, doi so lieu that)**: (a) engine dong cap TIA va chot_tien o gia TOT NHAT cua bar (cao nhat voi lenh mua), EA
tick dong o gia vua cham nguong; (b) engine tru spread HAI lan o lenh tia (luc mo va luc dong), EA mot lan. Tren nen M15 gia lap co bien do that (6 duong x 1500 bar) engine cao hon EA
**~15%** o cau hinh co tia / chot_tien (tn5 +14,7% .. +16,4%; chot_tien_tia +7,9% .. +17,8%), luoi thuan (khong tia) lech +-5%. `test_engine_lac_quan_voi_tia_lenh_khi_chay_tren_bar_ohlc`
ghim so do. **Khi doc ket qua tester: tester la so THAT, `thu_luoi` tn5 la can tren** (ham y: cac con so +13,26%/nam AUDCAD tu `luoi.py` co the lac quan ~15% o phan tia).

**CHUA kiem**: MetaEditor (cu phap rieng cua MQL5 - san gia la C++ nen mot so chuoi chuyen kieu / cu phap C++ chap nhan ma MQL5 co the khong), tester that (tick that, spread doi, swap qua dem, phi,
khoi dong lai giua chung), va 5 diem hieu chuan ben duoi. May nha bien dich F7: loi cu phap thi sua ngay va commit, khong can xin phep.

## HIEU CHUAN truoc khi tin bat ky DAT nao (5 diem CHUA kiem voi may that)
1. **Lenh con MO luc het cua so**: chay EA mau mua-giu (mua tick dau, khong SL/TP) mot cua so ~60 ngay, so lai bao cao voi
   (dong - mo) x lot x co hop dong. Bao cao co tinh lo lai troi khong? Dung roi dat `da_hieu_chuan_lenh_mo: true`
   (chua dat thi `nhan_canh_bao` luon gan nhan "CHUA hieu chuan: lenh con MO luc het cua so...").
2. **Nhan bao cao tieng Viet**: luu 1 bao cao that vao `test_bao_cao_mt5.py` (mau that dau tien). `doc_duoc=False` thi xem `thieu`,
   them nhan vao `nhan_them`. Bay da biet: "Loi nhuan rong" = Gross Profit; lai that = "Tong loi nhuan rong".
3. **Do sau tick that cua XM demo**: ghi `tick_tu`. Cua so nam ngoai tick that -> `ha_tang`, khong ra so.
4. **`_chay_that`** (slot -> bien dich -> tester -> log agent) chua chay lan nao. Chay 1 EA dem duoc, doc truong `log` neu hong. Sau do chay `ea_LuoiDayDu.mq5` (tn5, lot 0,04) cung cua so voi `thu_luoi`: chenh lai la so THAT cua khoang cach engine<->tester (task #48).
5. **Nhanh nhi phan + `bo_set`** chua chay voi MT5 that (logic kiem bang test gia tren Linux). Can xem: (a) MT5 co nap dung `.ex5` copy vao
   `MQL5\Experts\_tu_dong` va `.set` ten kem khong (`.ini` dung `Expert=_tu_dong\<ten>` + `ExpertParameters=<nhan>.set`); (b) bot kiem tra ban quyen
   qua WebRequest (tester chan) co the KHONG vao lenh -> it lenh -> `CHUA_DO_DUOC`, khong phai AM; (c) lenh dau tien nen la `ea_LuoiThamChieu`
   (diem 4) truoc khi chay bot la. Hong thi doc truong `log`, sua ha tang, khong tieu niem phong.

## Gioi han (noi that)
`ea_tu_dong.tai_lo` chi lay van ban `.mq5` CHINH tren trang CodeBase (khong .zip, nghi 3 giay/bai): EA nhieu file mat `.mqh` -> `THIEU_TEP`. Tai goi day du can mot trang CodeBase that cua EA nhieu file lam fixture (cloud khong ra duoc mql5.com) - viec cua may nha, xem thu chi thi 03/10.

Lan nay KHONG boc logic; no do EA nguyen ban. Y nghia: EA nao ra DAT tren xac_nhan la **manh moi co bang chung** cho nhanh
boc tach (doc ma EA do de ra gia thuyet co che) va cho HEPHAESTUS (luoi tham so). EA tien ich (5/12 mau da do) bi bo, khong tinh.
Nhanh nhat tim EA tot: EA ban cong khai co ho so tin hieu con song (MQL5 Signals) - tin hieu AUDCAD luoi/DCA chinh la loai nay.
