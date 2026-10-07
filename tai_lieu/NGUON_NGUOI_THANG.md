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
   nghen la engine luoi `nhan/luoi.py` (truoc chi chay AUDCAD): **DA MO 03/10** cho cap FX chuan; JPY / vang cho quy cach do that (muc 4B).
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
| ~~ma top-3 theo nhan cu~~ (SAI: 19/31 nhan sai, xem muc ngay duoi) | khong dung nua |
| MA THAT (bang Distribution cua trang): ma chinh theo so lenh | XAUUSD 8 · EURUSD 5 · USDJPY 3 · BTCUSD 3 · AUDCAD 3 · GBPUSD 2 · 7 ma moi ma 1 |
| ma chiem >= 10% so lenh cua ho so | XAUUSD 12 · AUDCAD 8 · EURUSD 7 · USDJPY 7 · AUDNZD 5 · NZDCAD 4 · USDCHF 1 · AUDCHF 0 |
| ho so NHIEU MA (ma chinh < 60% lenh) / THUAN MOT MA (>= 95%) | 20 / 10 |
| ho so co >= 2 trong 3 ma AUDCAD-NZDCAD-AUDNZD (moi ma >= 10%) | 5: 1059619, 1975768, 2184802, 1627034, 2220467 |

Doc (DA SUA theo ma that, 03/10 toi): (a) "nhieu he co lai san" **dung** nhung nguoi thang song >= 2 nam chi ~8% danh sach da la top theo tang truong; (b) **VANG la ma so 1** (12/31 ho so co >= 10% lenh), roi tam giac **AUDCAD-NZDCAD-AUDNZD** (5/31) va nhom USD lon (EURUSD / USDJPY / GBPUSD, thuong nam trong danh muc nhieu ma). Cau "gan het la luoi/DCA tren cap bien dong thap" KHONG co bang chung: chi 1/31 la AUDCAD thuan (2023752) va AUDCHF khong co mat (0/31; con so 5 truoc do la loi nhan); (c) **2/3 ho so la DANH MUC NHIEU MA** nhung engine luoi chay MOT ma moi lan (`ghep_danh_muc` chi ghep he DSL, khong ghep luoi) - muon dung lai kieu danh muc thi can ham ghep luoi nhieu ma (CHUA lam; chi lam khi mot chan luoi don le da co DAT, dung luat "chua co DAT thi khong mo engine moi"); (d) quy cach: cap FX chuan (pip 1e-4, hop dong 100.000) chay tu 03/10 (muc 4B); vang + USDJPY da co quy cach do that (`config/luoi_quy_cach.json`, 03/10 toi, khop `symbol_info` XM demo).
Han che trung thuc: ca 400 deu tang truong > 0 va khong ho so nao co DD cong bo >= 80% (danh sach da loc/xep san) -> hai dieu kien do khong phan biet duoc gi, chi TUOI SONG la thuoc loc that; va KHONG tinh duoc ti le co lai cua "mot signal bat ky";
`dd_pct` la so trang cong bo (chua doi chieu cach tinh); ho giau quy tac nen day la nguon GIA THUYET, khong phai bang chung (LAM LAI TU DAU).

**KET QUA THAT 03/10 toi (may nha chay `b link ho-so-symbol`, thu aac2): 31/31 ho so doc duoc, nhan cu SAI o 19/31.** Nguyen nhan: `_quet_signal_mql5._RX_SYM` dem moi chu hoa 6 ky tu trong CA TRANG HTML, lay 3 ma nhieu nhat - bo sot ten san khong theo mau 6 chu cai (`GOLD#`, `XAUUSDm`...) va de ma hiem (vai lenh) len nhan. Vi du con 2196457 (nhan cu USDCHF) thuc ra la **vang 1549 lenh**, USDCHF 2 lenh. Cach sua: `nhan/link_nguon.phan_bo_symbol` + `chuan_symbol` doc bang Distribution THAT. Ket qua day du (ma chinh + 6 ma dau moi ho so) nam trong `viec/xong/link-ho-so-symbol.json` -> `bang_chung.tep_moi` (runner mang theo noi dung bao cao TRONG file ket qua, khong tao `reports/nguoi_thang_symbol.json` o cloud - khong phai mat file). Dac diem thang: 10 ho so thuan mot ma (>= 95% lenh), 20 ho so nhieu ma; so lenh/ngay (tong cac ma liet ke / ngay song): thap nhat 0,18 · trung vi 1,4 · cao nhat 7,3 - khong ai la scalp tan suat cao, nhieu ho so ~1 lenh/ngay. `day_du = false` o ca 31: bang Distribution chi liet ke ma dau, ty le lenh la tren cac dong hien ra.

**Con mau 2023752 (AUDCAD 100%, 2337 lenh / 1137 ngay, cong bo 2023 +27,59% · 2024 +47,16%):** tab *Trading history* cua MQL5 chi hien "To see trades in realtime, please log in or register" -> **lich su lenh tung lenh CAN DANG NHAP MQL5** (khong co trong HTML, khong co XHR khi chua dang nhap; Chrome 154 ma hoa cookie gan voi ung dung nen khong chep duoc phien dang nhap cua chu du an). Co dang nhap thi moi bam `b link tham-do ... --cdp`. Khong dang nhap thi chi con so tong hop cong khai - dung de HIEU CHUAN luoi tren M1 that (so lenh/ngay, tang truong nam), khong phai de chep lenh.

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
   **Cong cu da co (03/10): `b nc cc boc_lich_su`** (`nhan/boc_lich_su.py`) - nhan bang lenh (tep CSV/HTML cua tab History), tra buoc / he so lot / TP / gio lech
   va dieu kien vao; kiem bang du lieu cai san dap an, CHUA bang lich su that. Khi co bang lenh that dau tien: chay no truoc, doc ket qua boc, roi moi `thu_luoi`.
3. Thu: `thu_luoi` tren `kham_pha`, `xac_nhan` (qua `b nc cc`, vao so tay).
- **Cua nghen = engine - DA MO 03/10** (`nhan/luoi.py`: `QuyCach`, `quy_cach_cho`). AUDCAD / TONG_HOP giu NGUYEN tung con so (test hoi quy, so vang
  tao tu ma cu). Cap FX chuan (pip 1e-4, hop dong 100.000: USDCHF, AUDCHF, AUDNZD, USDCAD, EURUSD, GBPAUD, EURGBP...) lay phi qua dem + spread tu
  mo hinh chi phi cua CHINH doan do; `do_tin = KHAI` chi la nhan (cong niem phong van ha KHAI xuong CHUA_DO_DUOC). JPY / vang chi chay khi may nha
  ghi quy cach do tu `symbol_info` vao `config/luoi_quy_cach.json` (khoa theo ma; chi pip / hop_dong / point / spread_du_phong / von_quy_doi /
  da_doi_chieu / nguon - phi KHONG ghi de duoc). Chi so / crypto / exotic / micro: tu choi kem ly do. Moi ma moi mang canh bao "luoi.py CHUA doi
  chieu voi MT5 tester": doc nhu XEP HANG va hinh dang, chua phai loi that. `chot_tien` la TIEN (don vi tien bao gia tren 0,01 lot), khong phai pip:
  cap JPY gan x100 so voi cap FX chuan.
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
| cloud - XONG 03/10 | `luoi.py` nhan quy cach theo ma; AUDCAD **giu nguyen tung con so** | `test_luoi_quy_cach.py` (51 test: hoi quy AUDCAD tung bit, bat bien theo ti le gia / pip / point / lot / von, ca tinh tay, `thu_luoi` qua so tay); kiem dot bien: hang so AUDCAD con sot -> test bat |
| cloud - XONG 03/10 | sua loi CU `luoi._mot_ro` (+ nhan C): `lai_arr[0]` nay = `-(spread lenh dau)`, truoc la `-TONG spread ca chuoi` -> `equity[0] = von - tong spread`. **`lai_rong` khong doi, golden 7/7 khong doi mot bit**; doi o hai cho: (1) von sat muc stop-out bi bao chay o bar 0 du chua lo gi; (2) he so lot o tran DD (`_he_so_lot_tai_tran`) bi chan nhan tao o k = von / tong spread (do tren chuoi tong hop: 71,5 / 19,3 / 8,4 / 249,8, nay 1000 / 492 / 931 / 1000 = do SUT GIAM quyet dinh) -> cau hinh giao dich nhieu truoc day bi phat theo so lenh khi xep theo `loi_suat_o_tran_pct`. Chua co dong so tay nao bi anh huong (sau khi lam lai tu dau khong con dong `luoi` nao). Van tay `thu_luoi` nay gom `luoi.PHIEN_BAN_ENGINE` (=3) de lan doi engine sau khong tai dung ket qua cu | `test_luoi_quy_cach.py` muc 9 (4 ca, FAIL tren ban cu), `test_he_so_lot_tran.py` (3 ca, FAIL tren ban cu), 2 ban dot bien nhan C `bar0_*` |
| cloud - XONG 03/10 | **boc tham so + dieu kien vao tu LICH SU LENH**: `nhan/boc_lich_su.py`, cong cu nc `boc_lich_su` (buoc, he so lot, TP, gio lech, dieu kien vao suy nguoc tu bang lenh; AI co the doi chieu voi bar that qua cac tool co san) | 45 test: 38 tren du lieu cai san dap an + 7 tren dinh dang export MQL5 that. Chay tren lich su THAT dau tien 03/10 khuya (con 2023752, muc 11); chua co phep do lai tren du lieu cua ta |
| cloud - XONG 03/10 | **nhan C cho engine luoi** (`nhan/luoi_nhan.c` + `.py`, ctypes, du phong Python): x134 tren engine, khop tung bit voi Python (3.11/3.12/3.13), ASan sach; sau khi go diem nghen thu hai (`_he_so_lot_tai_tran` ranh gioi Pareto, ban cu 80 lan chia doi) mot lan danh gia luoi tren 190.000 bar: **1547 ms -> 18 ms (x86)** | `test_luoi_nhan.py` (116 test), `test_he_so_lot_tran.py` (62 test); chi tiet + lenh o `TOC_DO_TEST.md` |
| cloud - XONG 03/10 | **quet tham so luoi trong MOT goi**: cong cu nc `quet_luoi` (`nc_thi_nghiem.quet_luoi`; `luoi.chuan_bi` + `luoi.chay_mang` tach tu `luoi.chay`, bit-y-het): ca luoi (tich Descartes, <= 6 truc, <= 40 gia tri / truc, <= 1.000 o / goi, vuot thi lay mau theo `hat`) chay da luong tren **kham_pha**; moi o la MOT phep thu; doc hinh dang CAO_NGUYEN / CAI_GAI / HON_HOP / KHONG_CO_LAI la NHAN; o tot nhat chi la LUA CHON -> tiep bang `thu_luoi` tren xac_nhan. Do: 54 o x 190.000 bar (du lieu tong hop) 31,2 s Python -> 0,62 s C (11,6 ms / o) | `test_quet_luoi.py` (61 test, dot bien diet 3/4 mutant song duoc, con 1 mutant tuong duong); o tot nhat khop `thu_luoi` mot o tung con so. **Chua chay tren bar that** |
| nha | lay bang lenh cua 31 ID (tab History: ghi URL AJAX + luu 1 trang fixture), 1 trang / 3-5 giay | file fixture trong repo, cloud viet adapter |
| nha (sau khi co XM demo + `b khoi-phuc`) | do chi phi that USDCHF / AUDCHF / AUDNZD / USDCAD / EURUSD / XAUUSD / USDJPY (spread, swap mua/ban, hop dong, digits, point) | `do_tin = SAN` cho cac ma do; XAUUSD / USDJPY: ghi `config/luoi_quy_cach.json` (da_doi_chieu: true) -> `thu_luoi` chay duoc |
| cloud - XONG 03/10 | `LuoiDoiXung.mq5` da MAT (VPS het 02/10, khong co trong git) -> viet lai EA tham chieu toi thieu `ea_LuoiThamChieu.mq5` (goc repo; lam DUNG nhung gi `luoi._mot_ro` mo phong, khong them gi). CHUA bien dich bang MetaEditor (cloud khong co), chi qua g++/clang++ voi stub; `ea_tho.phan_loai` ra CHIEN_LUOC, khong THIEU_TEP, doc dung 8 input (kieu int/double); luoi tham so de xuat chi dung `InpStepPips` / `InpTpPips` | do cheo LOGIC EA (port Python tung tick) voi `luoi.chay` (theo bar) tren cung duong gia tick gia lap, 8 seed, spread khop: lai EA/luoi = 0,96-0,99 (SE ~0,015), so lenh va so ro cung 0,96-0,99; phi spread moi lenh khop (seed 1: 272 lenh x 0,15 tien/lenh = 40,8 cua EA; luoi 267 lenh = 40,05). **Day KHONG phai hieu chuan voi MT5**: chi chung minh quy uoc TP/spread/dem tang cua EA va cua luoi khop nhau tren duong gia gia lap |
| nha | hieu chuan `luoi.py` vs tester MT5 (diem cuoi cua dong tren): bien dich `ea_LuoiThamChieu.mq5` bang MetaEditor F7 (loi cu phap thi sua ngay va commit), chay `b nc cc ea_tho_chay` va `b nc cc thu_luoi` cung ma / cung doan (lenh mau nam trong dau file EA) tren AUDCAD roi USDCHF | chenh lech lai %/nam, maxDD, so lenh, so ro ghi vao dong nay; neu lech > 10% thi sua `luoi.py` truoc khi tin bat ky ma ngoai AUDCAD |

> Luu y khi doi chieu `thu_luoi` voi du lieu KHONG co cot spread (spread = 0): `luoi` roi ve `QuyCach.spread_du_phong` (2 pip) nen se tru nhieu hon EA zero-spread, lai EA trong nhu cao hon 1,07-1,34 lan. Day la hang so du phong, khong phai sai lech mo hinh bar (tat du phong thi chenh chi con vai phan tram: 8 seed ra 0,99). Doi chieu that phai dung bar co spread that.
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

## 11. Lich su lenh THAT dau tien: con 2023752 (AUDCAD, 03/10 khuya)

Nguon: export chinh thuc MQL5 `/en/signals/2023752/export/positions` (nha lay bang trinh duyet AI da dang nhap). `boc_lich_su` nay doc dung tep that
(truoc do tieu de TRUNG TEN Time/Price/Volume lam mat gio dong + gia dong cua CA lich su mot cach im lang; them cot Commission/Swap; dong Balance = nap/rut).
Ket qua: 2327 lenh dong (0,01 lot 2201 / 0,02 99 / 0,03 23 / 0,04 4), 1701 ro, 2023-08-02 -> 2026-10-02, hai chieu, 15 dong Balance.

| Dieu do duoc | So |
|---|---|
| Lai gop - hoa hong - swap = **lai rong** | 928,93 - 196,22 - 38,58 = **+694,13 USD** (phi an 25% lai gop; hoa hong 0,08 / lenh 0,01 lot) |
| Nap / rut | +500 dau, 13 lan rut 50, 1 dong -0,02 -> -650,02 tong; **so du cuoi uoc 544,11** (= 500 - 650,02 + 694,13) |
| Ro thua | 15 / 1701 ro (tong -21,29); lenh thua lon nhat -16,91; 80% lenh thang |
| Lai theo do sau ro | ro 1 lenh = 61% lai (1340 ro, 1 ro thua); ro 4+ lenh: 60 ro, 14 thua - cho thua nam o do sau |
| MQL5 cong bo (khong doc duoc tu danh sach lenh dong) | maxDD 41,57% (equity, gom lo treo) - duoi tran 80% cua chu du an |

**Sua mot con so sai trong thu nha 051a**: "gross 779 / rong ~544 / lo lon nhat -50" cong nham 15 dong Balance vao cot Profit. 544 la SO DU CUOI, -50 la mot lan RUT TIEN.

**Tac gia DOI cai dat giua chung** (`doi_tham_so`, theo quy): TP cua ro 1 lenh **4,1 pip** (2023Q3-2024Q2) -> **6,2** (2024Q4-2025Q1) -> **7,6** (tu 2025Q3, bien p25-p75 chi 7,5-7,9);
buoc tang 1 -> 2: 16 -> 21-22 pip. Suy tham so tren TOAN lich su cho con so TRUNG BINH cua ba che do (TP "khong ro", buoc CV 0,47) = khong cai dat nao ca: dung `tu`.
Cai dat HIEN TAI (tu 2025-07-01, `boc_lich_su ... "tu":"2025-07-01"`): hai chieu, lot 0,01 co dinh (tang 3: 0,02), TP 7,6 pip (do tin vua), buoc ~21 pip (he so ~1,2, CV 0,64 - buoc co ve dong),
tia lenh (cat cap) bien ~5 pip, tran tang quan sat 5 (toan lich su 9). Vao lenh: nen M5 moi, dom 15-18h gio may chu - **la gia thuyet, chua do** (can bar trong cua so cua con = xac_nhan / niem_phong, KHONG dung de tim luat).

**Cach thu dung ky luat** (nguoi thang chon theo KET QUA -> chi tham so la gia thuyet): (1) `quet_luoi` M15 **kham_pha 2018-01-02 -> 2023-07-02** = hoan toan TRUOC khi con bat dau (2023-07-26) = bang chung DOC LAP
ve viec cai dat co ban chat hay chi gap may; quanh buoc 14-26, TP 6-14 (phi XM > phi cua con nen TP quet rong hon), chon theo HINH DANG cao nguyen; (2) MOT o tren `xac_nhan` (khoang con dang song: khong doc lap, chi
chung minh LAM LAI duoc); (3) NIEM PHONG: `niem_phong` nhan khai bao DSL vao/ra; he LUOI co duong rieng **`niem_phong_luoi`** (04/10/2026: lot chot bang chinh engine tren kham_pha + xac_nhan, mo MOT lan, DAT = co lai sau phi + maxDD < 80% + >= 20 lenh; `b nc cc niem_phong_luoi`). Nho: ca xac_nhan lan niem_phong cua con 2023752 deu chong len doi song that cua no (tu 2023-07-26) nen DAT chi la LAM LAI, truyen `ghi_chu` noi ro. **Khong dung `xac_nhan` / niem phong de hieu chuan.**
Chi phi can `do_tin` khac KHAI. Thu #8 (`viec/thu/`) co lenh cu the.

## BO SUNG 06/10/2026 - CHO EA / CHIEN LUOC NGOAI MQL5+MYFXBOOK
May doc: `config/nguon_cho_ea.json` (26 nguon, co `mo`: tu_dong / may_nha / tay, `gia_tri`, `uu_tien`). Chua cho nao chay tren trang that (cloud khong ra duoc); lan dau: `b link tham-do` o may nha (6 don `link-tham-do-cho-*`).
Thu tu dao: (1) FX Blue + Darwinex + Myfxbook autotrade + MT4 signals (lich su lenh / track record that) · (2) GitHub MQL5 + MQL5 CodeBase (ma EA mo -> `ea_tho_quet`) · (3) TradingView Pine, SignalStart, Telegram EA · (4) ForexFactory trade explorer / thread he thong · (5) Collective2, ZuluTrade, cTrader · sau cung: Reddit, QuantPedia (gia thuyet cho HEPHAESTUS), cho EA tra phi (CHI lay ten he thong, so tu khai khong tin).
Quy tac: lich su lenh THAT > track record kiem toan > ma nguon mo > mo ta chu. Tin hieu luoi/DCA song >= 2 nam tren cap tuong quan (AUDCAD & anh em) di truoc.
