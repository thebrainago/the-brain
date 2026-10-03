# NGUON NGUOI CHIEN THANG - khai thac he CO LAI SAN truoc (03/10/2026)

> Chu du an hoi (03/10, phien cloud): he lon, nhieu file, cam giac di duong vong; myfxbook / mql5 / darwinex da co nhieu he thong
> co lai san -> tim them noi co nguoi thang va khai thac truoc; neu kho tu dong thi keo he dat chuan ve cho AI boc tach / phan tich
> nguoc lich su; strategy TradingView thi dung tester cua no; phan nang dung cTrader cho nhe va nhanh.
> Phien cloud: khong MT5, khong `data/`, khong `nao.db`; ra duoc GitHub, **khong** ra duoc mql5 / myfxbook / fxblue / darwinex /
> collective2 / ctrader / tradingview / zulutrade / etoro / forexfactory (do 03/10: 16/17 host thu bi chan). So cai gi "CHUA DO" = can may nha.

## 1. Tra loi ngan

Dung huong, va so do cua chinh anh da ghi san (dong 35-41, 55-60). Thu tu khai thac, tu re/nhanh den dat/cham:

1. **Chay NGUYEN file cong khai tren MT5** (lan EA tho, da xay `nhan/ea_tho.py`). Khong boc logic. Cho den khi quet >= 30 EA that.
2. **Keo LICH SU cua nguoi thang ve, AI suy nguoc** - dung cho he CHI co ho so khong co ma. Da co **31 ung vien** (muc 2). Cua
   nghen that: engine luoi `nhan/luoi.py` chi chay AUDCAD -> **mo cho cac ma anh em truoc** (muc 4B).
3. **Cap (EA, tin hieu song)**: trang Market cua EA thuong ghi link tin hieu song cua chinh tac gia -> chay ban demo trong tester
   cung khoang thoi gian -> so duong von tester vs song = **thuoc do mo phong cua chinh ta**.
4. **TradingView = nguon MA, khong phai tester** (muc 5). **cTrader = chua** - do 1 lan khi tester that su nghen (muc 6).
5. **Khong mo them nguon / engine moi** truoc khi (1) va (2) ra it nhat MOT `DAT` o xac_nhan (muc 7).

## 2. DO THAT tren 400 ho so MQL5 signal da boc (`reports/LUAN_DAU_CHAN.json`, boc 25/09 truoc khi mat may)

Tieu chi cua chu du an: co lai + maxDD < 80%, them tuoi song de loai may rui.

| Dieu kien | So ho so / 400 |
|---|---|
| song >= 1 nam, tang truong > 0, DD cong bo < 80% | **94** |
| song >= 2 nam, tang truong > 0, DD cong bo < 80% | **31** (7,8%) |
| trong 31 do: luoi/DCA · khong ro · gong lo · xu huong · scalp | **18** · 11 · 1 · 1 · 0 |
| ma xuat hien trong top-3 ma cua 31 ho so | AUDCAD 15 · XAUUSD 9 · USDCHF 7 · AUDCHF 5 · USDJPY 4 · EURUSD 4 · AUDNZD 3 |
| rieng 18 luoi/DCA | AUDCAD 12 · USDCHF 5 · AUDCHF 4 · XAUUSD 3 · USDCAD 2 · EURUSD 2 |

Doc: (a) "nhieu he co lai san" **dung** nhung nguoi thang song >= 2 nam chi ~8% danh sach da la top theo tang truong; (b) ho **gan het
la luoi/DCA tren cap da bien dong thap** (AUDCAD va hang xom cua no) - chinh la loai ket qua tot nhat cua lab (AUDCAD, `thu_luoi`) nen
AUDCAD khong phai ngau nhien; (c) hang xom USDCHF / AUDCHF / AUDNZD / USDCAD / EURUSD **cung quy cach** (pip 1e-4, hop dong 100.000)
nhung `luoi.py` GHIM phi qua dem + point cua AUDCAD nen khong chay duoc.
Han che trung thuc: ca 400 deu tang truong > 0 va khong ho so nao co DD cong bo >= 80% (danh sach da loc/xep san) -> hai dieu kien do khong phan biet duoc gi, chi TUOI SONG la thuoc loc that; va KHONG tinh duoc ti le co lai cua "mot signal bat ky";
`dd_pct` la so trang cong bo (chua doi chieu cach tinh); ho giau quy tac nen day la nguon GIA THUYET, khong phai bang chung (LAM LAI TU DAU).

## 3. Ban do nguon - moi nguon cho GI

| Nguon | Cho gi | Ma? | Lich su lenh? | Vao he o dau | Kho tu dong |
|---|---|---|---|---|---|
| **MQL5 Market** | EA co danh gia; **ban demo chay duoc trong tester (chi tester)**; nhieu EA ghi link tin hieu song cua tac gia (vd product 179526 -> signals/2377929; theo ket qua tim kiem, cloud chua mo duoc trang) | `.ex5` (khong doc ma; chay den + do) | qua tin hieu | `ea_tho` (can ho tro `.ex5` - chua lam) | ha: tai demo bang terminal |
| **MQL5 CodeBase** | EA mien phi, nguon day du | `.mq5` 1 file (thieu `.mqh`) | khong | `ea_tho` (da co) | trung binh: IP bi cam sau ~50-150 request |
| **MQL5 Signals** (MT5 + MT4) | duong von, muc tai, MFE/MAE; bang lenh **chua kiem** | khong | co the (tab History) | `tin_hieu_mql5` (kieu) + CAU NOI THIEU: bang lenh | trung binh (toc do thap) |
| **GitHub** | du an MQL5 DAY DU (co `.mqh`) | co | khong | seeker `github` (da co; thu tu doc thu 6 trong `doc_song_song.UU_TIEN_NGUON`) | de - cloud ra duoc |
| **Myfxbook** | tai khoan xac minh, he AutoTrade "da kiem toan"; trang cong khai; CSV/API chi cho CHU tai khoan | khong | co (trang) | **chua co adapter** (ma cu chi con trong `nghi_huu/`) | chua do: co the can trinh duyet that |
| **FX Blue** | trang thong ke cong khai, co API lay lich su; tich hop ca cTrader | khong | co the | chua co | trung binh - **kiem bang 1 fixture** |
| **Darwinex** | DARWIN Info API: quote + diem cua MOI DARWIN, can token (khong co lich su lenh) | khong | khong | chua co | de (API chinh thuc); dung de XEP HANG, quote la chuoi chuan hoa rui ro, khong phai tien that |
| **cTrader Copy** | thong ke + lich su giao dich ben trong cTrader, link thong ke cong khai | khong | co (trong app) | chua co | kho |
| **Collective2 / ZuluTrade / eToro / DupliTrade** | ho so xac minh go-forward; fill data thuong sau dang nhap | khong | mot phan | chua co | kho, chua do: uu tien thap |
| **TradingView** | Pine open-source (ma ngan, de dich) nhung CHI backtest, khong co ho so song | co | khong | seeker `tradingview_pine` (da co; DAU danh sach `UU_TIEN_NGUON`) | khong co API tester (muc 5) |
| **cTrader Algo store** | ~500 cBot (co free); khong ro bao nhieu cai kem nguon | mot so | khong | chua co | kho |

Diem then chot: **chi he MQL5 (Signals <-> Market <-> CodeBase) cho phep ghep CA ho so song LAN file EA** - va no la MT5 nen chay dung tester
cua ta. Cac nen tang con lai chi them HO SO (de suy nguoc), khong them FILE. Vi vay dung dan ngan sach ra nhieu nen tang.

## 4. Thu tu khai thac - moi buoc co cai do va diem dung

**A. Chay nguyen file (`ea_tho`)** - da co ma, cho may nha. Buoc 0: 4 diem hieu chuan trong `LAN_EA_THO.md`. Do: so EA quet, so `DAT`
o xac_nhan, so `THIEU_TEP`. **Dung / doi nguon (khong doi cong cu)** neu qua 30 EA quet that ma khong cai nao `DAT` o xac_nhan.
*Tuy chon, chua lam:* nhan `.ex5` demo cua Market (bo qua bien dich, chi can ma/khung); lam sau khi lan nay chay that 1 EA va hieu chuan xong,
vi them nhanh chua kiem chi lam tang be mat chua do.

**B. Lich su -> luoi/DCA (suy nguoc)**
1. Lay: 31 ID (muc 2; danh sach trong thu giao may nha) - bang lenh neu trang co, khong co thi chi duong von + MFE/MAE (da co `dau_chan`).
2. Boc: tu chuoi lenh suy **buoc, he so lot, TP ro, che do** (day la tham so `ThamSo` cua `luoi.py`); vao-lenh lan dau dung `tim_quy_luat` / `mo_xe_lenh`
   voi nhan "co vao lenh" thay "thang/thua". Chi lam khi co MOT bang lenh that - khong thiet ke cho du lieu tuong tuong.
3. Thu: `thu_luoi` tren `kham_pha`, `xac_nhan` (qua `b nc cc`, vao so tay).
- **Cua nghen = engine** (viec 3 muc 8.2 `NHA_NGHIEN_CUU.md`): `luoi.py` nhan MO HINH CHI PHI theo ma. Thu tu: hang xom cung quy cach truoc
  (USDCHF, AUDCHF, AUDNZD, USDCAD, EURUSD, GBPAUD, EURGBP), roi XAUUSD / cap JPY (quy cach khac: pip, hop dong, point - can doi chieu `symbol_info` that).
- **Ro ri phai chan**: lich su cua trader nam gan het trong doan xac_nhan / niem_phong. Gia thuyet tu do chi la GIA THUYET; thu tren kham_pha
  (ngoai thoi gian cua ho) va tien cu; khong dung chinh bar cua ho de "xac nhan".

**C. Cap (EA, tin hieu song) = thuoc do**: chon EA co ban free/demo + link tin hieu song >= 1 nam; chay tester cung khoang, **cung bo tham so**
(ban free co the khoa lot co dinh - quy ve loi suat %, khong so tien). Do: duong von tester tai hien duong von song bao nhieu phan tram.
Ket qua nay quyet dinh co nen tin `DAT` cua tester hay khong - day la dang "chi phi phai DO DUOC" o muc he thong.

**D. Do do ben cua bang xep hang**: chup lai ~94 ho so (song >= 1 nam, lai, DD < 80%) moi tuan x 8 tuan, toc do thap. Do: sau 4 / 8 tuan bao nhieu %
van lai va DD < 80%, so voi 306 ho so con lai. Cho biet **dang tin bang xep hang den dau** truoc khi dau tu them vao no.

## 5. TradingView

- **Khong co API chay tester** (khong chinh thuc). Dieu khoan cho phep hien thi, cam dung phi hien thi; xuat CSV lenh chi o goi tra phi. Tu dong hoa
  qua trinh duyet = dung diem cam + de vo.
- Chi la **backtest**, khong co ho so song; nguoi dang chon duong von dep nhat de dang (lech chon cuc manh), nhieu script repaint.
- Pine chay cuc bo da co (PyneCore, pynescript, PineTS) nhung **moi, do trung thuc voi TradingView chua do**; cong chinh khong the dua tren no.
- Ket luan: **dung lam nguon ma/y tuong** (da dung dau `doc_song_song.UU_TIEN_NGUON`); ma Pine ngan nen de dich sang DSL hon EA. Neu muon, chu du an tu mo tester xem 3-5 chien
  luoc chot (nhin them, khong phai cong).

## 6. cTrader

Theo ket qua tim kiem (cloud khong vao duoc `help.ctrader.com`, **chua doc tai lieu goc**): co `cTrader CLI`, anh Docker `ghcr.io/spotware/ctrader-console`,
lenh `backtest` va `optimize`, du lieu tick tu server / M1 tu server / **M1 tu file CSV cuc bo** / H1, bao cao HTML hoac JSON, chay duoc tren Linux khong can mo ung dung.
- Co the: chay song song (khong bi cai "mot terminal64.exe" cua MT5), chay tren VPS Linux, C# de AI viet hon MQL5.
- Chua biet / chua do: toc do that so voi MT5 va so voi engine Python cua ta; co can dang nhap tai khoan broker cTrader de lay tick khong; do trung thuc tick.
- Chi phi doi: **MOI EA cong khai la MQL5, khong phai C#** -> khong "chay nguyen file" duoc, phai dich lai (lenh lech hanh vi); `ea_tho`, `bao_cao_mt5`,
  `xuat_mq5`, XM demo, 4 diem hieu chuan deu viet cho MT5. Them mot engine thu ba khi chua chay duoc EA nao tren MT5 that la dung kieu "di duong vong" ma anh tru.
- **Quyet dinh: chua.** Diem kich hoat: sau 1 tuan lan EA tho chay that, neu hang cho tester > ~6 gio/ngay VA viec can chay hang loat, thi lam MOT spike: cung mot cBot/
  EA don gian, do giay/lan chay tren MT5 vs cTrader CLI Docker. Khong co so do thi khong doi.

## 7. CAT BOT - nhung thu da thay la duong vong (so do that, truoc 02/10)

- Gom tai lieu hoc thuat (openalex + crossref chiem 27,4% so tai lieu) cho ~0 co che: **giam ngan sach**, chi lay khi AI yeu cau (`b nc cc yeu_cau_seeker`).
- Pheu regex/DSL: 12.078 tai lieu -> 285 co che (2,4%) -> 18 mau (0,15%). **Khong them tu vung DSL** truoc khi lan A / B ra bang chung (da ghi o `RA_SOAT_KIEN_TRUC` muc 7, viec cloud 3).
- Mo them nguon moi / engine thu ba / thu tu dong hoa trinh duyet: chi sau khi A hoac B ra it nhat 1 `DAT` o xac_nhan.
- Script `_*.py` roi: da cam o LUAT SO 1 - moi phep do vao so tay qua `b nc cc`.

## 8. Ky luat va dieu khoan

- Chay ban demo Market trong tester la dung muc dich cua demo; **khong dich nguoc `.ex5`** (trai dieu khoan, va khong can - chay den roi do).
- Lay du lieu: 1 trang / 3-5 giay, khong song song, dung khi bi 403/429; repo la PUBLIC -> khong dua khoa / token / so lieu rieng len.
- Moi con so tu nguon ngoai la GIA THUYET; vao so tay co `nguon`; niem phong theo luat cu (MOT lan, can lai + maxDD < 80%, chi phi DO DUOC).

## 9. Viec ke tiep

| Ai | Viec | Xong khi |
|---|---|---|
| cloud (lam ngay) | `luoi.py` nhan mo hinh chi phi theo ma (hang xom cung quy cach truoc); AUDCAD **giu nguyen tung con so** | test hoi quy AUDCAD y het + test hop dong cho ma moi; `thu_luoi` het chan ma |
| nha | lay bang lenh cua 31 ID (tab History: ghi URL AJAX + luu 1 trang fixture), 1 trang / 3-5 giay | file fixture trong repo, cloud viet adapter |
| nha (sau khi co XM demo + `b khoi-phuc`) | do chi phi that USDCHF / AUDCHF / AUDNZD / USDCAD / EURUSD / XAUUSD / USDJPY (spread, swap mua/ban, hop dong, point) | `do_tin = SAN` cho cac ma do; `thu_luoi` chay duoc |
| cloud roi nha | hieu chuan `luoi.py` vs tester MT5: `LuoiDoiXung.mq5` da MAT (VPS het 02/10, khong co trong git) -> cloud viet EA tham chieu toi thieu mot file, nha bien dich + chay tren 1 ma moi | chenh lech lai/DD duoc ghi |
| nha | cap C: 1 EA Market co ban free + tin hieu song; chay tester cung khoang | so tai hien duoc ghi vao `LAN_EA_THO.md` |
| nha | ban D: chup lai 94 ho so moi tuan | bang ben vung sau 4 / 8 tuan |

## 10. Nguon tham khao (tim kiem 03/10/2026, cloud khong vao duoc trang goc)

- cTrader CLI: https://help.ctrader.com/ctrader-cli/ · https://help.ctrader.com/ctrader-cli/cbots/ · https://help.ctrader.com/ctrader-algo/backtesting-and-optimizing-cbots/
- cTrader Copy / thong ke cong khai: https://help.ctrader.com/ctrader-copy/account-and-strategy-page/ · https://help.ctrader.com/ctrader-mobile-ios/stats-to-share/
- MQL5 Market demo chi chay trong tester: https://www.mql5.com/en/forum/513229 · vi du EA co link tin hieu song: https://www.mql5.com/en/market/product/179526
- Darwinex API: https://darwinex.com/algorithmic-trading/darwin-api · https://help.darwinex.com/api-walkthrough
- FX Blue + cTrader: https://www.spotware.com/integrations/fx-blue-live
- TradingView xuat du lieu chien luoc: https://www.tradingview.com/support/solutions/43000613680/ · khong co API chinh thuc: https://blog.traderspost.io/article/tradingview-api
- Pine cuc bo: https://pynescript.readthedocs.io/ · https://gittrend.io/repo/PyneSys/pynecore
- Collective2 (track go-forward): https://www.wealth-lab.com/a/BuildNotesB40C2
