# HƯỚNG DẪN CHO CLAUDE CODE — Dự án Research SP500

## BỐI CẢNH
Đây là dự án nghiên cứu định lượng tìm chiến lược giao dịch cho SP500 (symbol US500M qua Exness/MT5).
Mục tiêu hiện tại: (1) fetch lại data SẠCH từ MT5, (2) đọc + dọn gọn toàn bộ code cũ (nhiều bản vá chồng chéo), áp logic mới đã chốt.

## NGUYÊN TẮC BẮT BUỘC KHI SỬA/VIẾT CODE BACKTEST
Mọi code backtest PHẢI tuân thủ (đây là bài học đắt giá, không được bỏ qua):

1. **ENTRY tại OPEN[i+1], KHÔNG phải close[i].**
   - Tín hiệu tính từ close[i] chỉ BIẾT khi bar i đã đóng → sớm nhất vào được ở open bar kế tiếp.
   - Vào tại close[i] = LOOK-AHEAD BIAS = kết quả đẹp giả.

2. **COST THẬT đầy đủ, KHÔNG dùng cost giả định 2đ:**
   - spread thật (đọc từ MT5, US500M ~5-8đ tùy giờ)
   - slippage (~1đ)
   - SWAP QUA ĐÊM: tính theo số đêm giữ lệnh (số bar giữ / số bar mỗi ngày). Setup giữ nhiều ngày bị phạt swap nặng.

3. **BỘ LỌC LOẠI SỚM (áp TRƯỚC placebo, bỏ ngay để tiết kiệm thời gian):**
   - Tần suất < 2 lệnh/tuần → BỎ
   - Lãi trung bình < 5 điểm/lệnh (sau cost) → BỎ
   - R:R xấu / TP quá ngắn so với SL (breakeven WR > 70%) → BỎ

4. **TIE-BREAK TP/SL cùng bar:** khi 1 bar chạm cả TP lẫn SL, dùng open bar đó để đoán cái nào chạm trước (gần TP hơn → TP trước). KHÔNG mặc định lấy SL.

5. **Robustness sau bộ lọc:** placebo ≥95%, walk-forward dương ≥3/4 quý (hoặc ≥8/11 năm nếu data dài), bỏ 2 năm tốt nhất vẫn dương, outlier top10% < 45%.

## QUY TRÌNH 2 TẦNG
- Python (placebo/robustness + cost đầy đủ) = sàng lọc sơ bộ, tìm "đánh cái gì".
- MT5 single-run (Optimization=Disabled) = kiểm "đánh có trơn không" trên thực thi thật.
- TUYỆT ĐỐI KHÔNG dùng MT5 optimization chọn tham số (= curve-fitting).

## KẾT LUẬN ĐÃ CHỐT (không cần tìm lại)
- SP500 là momentum thuần. Mean-reversion chết (Hurst 0,51). Seasonality không tradeable.
- SHORT không có edge (drift lên).
- Setup B (Pullback H4: Tenkan>Kijun + RSI<40) ~+0,177R sau cost — edge thật nhưng mỏng, ít lệnh.
- Setup A (Pivot Breakout) đã CHẾT (biên mỏng, cost giết).

## YÊU CẦU DỌN CODE
- Nhiều file là bản vá chồng lên nhau (đuôi .bak, _patch, _timeout...). Cần gộp lại, xóa bản thừa.
- Ưu tiên single-file, multiprocessing (máy có 20 luồng), parquet, comment tiếng Việt.
- Trước khi xóa file nào, LIỆT KÊ cho tôi duyệt. Không tự xóa hàng loạt.

## PHONG CÁCH
- Trả lời tiếng Việt.
- Giải thích ngắn gọn, đi thẳng vấn đề.
- Khi sửa code: nói rõ sửa gì, vì sao, KHÔNG tự ý đổi logic ngoài yêu cầu.

---

## CAP NHAT 2026-07-27 — QUY TRINH DA DUOC DONG GOI

Da mo xong SP500 va chuan hoa thanh khuon dung lai duoc. **Doc `QUY_TRINH_MO_TAI_SAN.md`
truoc khi mo bat ky tai san moi** — trong do co 8 CAI BAY da sap that (spread tuyet doi,
quen lai tien mat, swap=0, lich su tai tao, tham so mac dinh, placebo bat drift doi lot edge,
diem mua vu in-sample, fetch MT5 lam day o dia).

**Mo tai san moi = 2 viec:** khai bao ho so trong `asset_profile.py` roi chay
`python run_asset.py --asset <khoa>`.

### Chuan MOI bat buoc (bo sung cho muc "NGUYEN TAC" o tren)
6. **Diem so theo lich phai POINT-IN-TIME.** Bang `MONTHLY_SCORE` gan cung truoc day duoc rut
   ra tu chinh giai doan backtest -> IC bi thoi GAP DOI (+0,057 -> +0,029), keo Sharpe he thong
   tu 0,76 xuong 0,59. Dung `asset_profile.season_scores_pit()`. Mac dinh cua `system_final`
   gio la point-in-time; `--season-cung` chi de doi chieu ban cu.
7. **Spread phai la BPS THEO GIA HIEN TAI**, khong phai so diem tuyet doi ap cho ca lich su.
8. **Phi qua dem la thu quyet dinh, khong phai spread.** Bat buoc tinh theo so dem THAT +
   lai suat thuc te tung ngay. Benchmark phai co CA HAI: Buy&Hold CFD (co phi) va Buy&Hold
   chi so (khong phi) — hai ket luan khac han nhau.
9. **Placebo phai giu nguyen phoi nhiem** (hoan vi khoi vi the), khong sinh tin hieu ngau nhien
   moi — neu khong se khong bat duoc "drift doi lot edge" (usdars Sharpe 1,75 / placebo 0%).
10. **Chi ap lop tin hieu CO NGHIA voi tai san do.** Duong cong lai suat + ETF flow co phieu
    chi dieu khien chi so co phieu. Khai bao trong `asset_profile.PROFILES[...]['cac_lop']`.

### CAP NHAT 2026-07-28 — TANG 2 DA CHAY, VA NO LAT NGUOC MOT SO KET LUAN
Doc `TANG2_MT5_KET_QUA.md` + `SETUP_1_2_LENH_TUAN.md`. Nhung gi thay doi:
11. **Spread that cua CFD chi so la ~0,6-0,8 bps, KHONG phai 9 bps.** Do tren 168 lenh khop
    that trong Strategy Tester (XM US500Cash) va doi chieu voi trung binh cot `spread` cua 6
    nam bar D1 - hai cach cho cung ket qua (0,78 vs 0,755 bps). Gia dinh 6+1 diem cu la
    **than trong gap 12 lan**, va no phat nang nhat dung cac chien luoc doi vi the nhieu.
    => Moi ket luan dang "X chet vi cost" tu truoc 28/07 phai chay lai truoc khi tin.
12. **He thong dung gio la V6 (IBS<0,2 VA bias>0, giu 1 ngay), KHONG phai V7.** Danh muc deu
    trong so 3 chi so My tren MT5 that: CAGR 8,64% / Sharpe 0,95 / maxDD -11,5% / Calmar 0,75
    / ~1 lenh/tuan. V7 la kem nhat trong 3 bien the (Sharpe 0,49).
13. **Phi qua dem la chi phi quyet dinh, va XM thu no bang SO TUYET DOI** (-1,17 USD/lot/dem
    cho US500Cash) nen ty le %/nam GIAM khi chi so tang: 14,7%/nam o muc index 2.900 nhung
    6,0%/nam o muc 7.100. **Strategy Tester ap muc swap CUA HOM NAY cho ca lich su** - do la
    ly do duy nhat khien MT5 kem Python o giai doan 2019-2021. Tu 2022 hai ben khop nhau
    trong 8,9%.
14. **KHONG duoc mo hinh phi qua dem bang `swap_tuyet_doi * 365 / gia_tung_ngay`** - do la
    chinh cai bay o muc 13, va toi da tu mac lai no ngay 28/07 (ra 38,8%/nam cho nam 2011).
    Phai mo hinh theo CO CHE: lai suat thuc te tung ngay + markup, markup hieu chinh tu quan
    sat hom nay (swap hom nay - lai suat hom nay).
15. **Da dang hoa do tren bar chi so TIEN MAT khong song sot khi giao dich bang CFD 24h.**
    Tuong quan V6 nikkei-sp500 la 0,17 tren bar Yahoo (phien noi dia) nhung **0,58** tren bar
    CFD cua XM (bar D1 chay 00:00-23:59, trum ca phien My). Moi phep tinh da dang hoa phai
    dung du lieu CUA CHINH cong cu se giao dich.
16. **IBS bat day chi song tren chi so co phieu.** Da thu V5 tren GOLD/XAUEUR/SILVER + 5 cap
    FX voi chi phi that cua XM: khong cai nao dat nguong (Sharpe > 0,5 VA placebo >= 95 VA
    thang mua-giu). Vang co spread re nhu chi so (0,70 bps) nhung phi qua dem 7,5%/nam.
17. **Vao lenh cang SOM cang tot.** Lenh cho tai gia mo bar co ty le khop 97,6% (duoc gia tot
    hon gan nhu moi lan) nhung lam CAGR tut 8,10% -> 6,31%: khop muon trong ngay lam hut phan
    dau nhip hoi. Edge cua IBS nam don o DAU PHIEN, khong nam o muc gia.

### Ket luan da chot THEM (khong can tim lai)
- SP500 khung NGAY la **mean-revert**: VIX cao = mua, dong tien risk-on don dap = ban,
  IBS<0.2 (dong cua o 20% duoi bien do ngay) = mua. Ca ba deu doi dau so voi truc quan thong thuong.
- **IBS bat day chi song o chi so chau My** (sp500/dow/nasdaq/russell/bovespa). Chau Au bang 0
  hoac AM (dax 0,05 / ftse -0,18 / eustoxx -0,32). Hang hoa ~0. Forex: 655 phep thu, 0 song sot.
- ~~He thong tot nhat hien tai: **V7**~~ **-> DA THAY, xem muc 12 o tren.** V7 chi con dung lam
  moc doi chieu. Ban dung la **V6**, danh muc 3 chi so My.
- **Vol targeting KHONG cai thien** (Sharpe 0,59 -> 0,54, truot placebo 86,7%): no cat size dung
  luc IBS khai hoa. Da test, khong can thu lai.
### CAP NHAT 2026-07-29 — BA QUY TAC MOI (deu tu loi da mac trong phien nay)
18. **Co file `.ex5` chay duoc + mot tai khoan song thi DUNG DICH NGUOC THAM SO.** Cho no
    chay trong Strategy Tester roi doc log. Toi da dot gan mot phien de doan quy uoc pip cua
    bot DongDongTV; hai cach doc cho P/L 22 nam la **-53.000** va **+10.900.000**, khong file
    `.set` nao phan xu duoc. Mot dong log (`vTP=1723.862` cho lenh ban `1728.862` voi
    `ChainTPPip=500`) giai quyet ngay: 1 pip = 0,01. Dung `dung_tester.py` (viet `.ini` + `.set`
    roi goi `terminal64.exe /config:`; phai dong terminal truoc vi MT5 khong cho 2 tien trinh
    dung chung thu muc du lieu). **Kem theo:** file `.set` trong `MQL5\Profiles\Tester\` la ban
    TU LUU cua nguoi dung, khong phai ban khuyen nghi — ban that nam trong file `.rar` tai ve.
    Va may nay co **5 thu muc du lieu MT5**, phai quet het truoc khi ket luan "khong tim thay".
19. **PLACEBO PHAI HOAN VI CHUOI VI THE, KHONG PHAI CHUOI LAI/LO.** Hoan vi chinh chuoi lai/lo
    giu nguyen phan phoi nen luon ra ~50% — no se "ket luan" sai rang moi he thong deu truot
    placebo. Toi da mac dung loi nay ngay 29/07 va suyt bao cao rang V6 truot. Sau khi sua:
    100%. (Day la muc 9 o tren, viet lai cho ro vi doc muc 9 khong du de tranh loi.)
20. **KIEM LOAI TAI KHOAN TRUOC LENH THAT DAU TIEN** — `kiem_tk_xm_hien_tai.py`. So lot chi
    dung tren tai khoan MICRO (contract chi so 0,01). Tai khoan XM dang dang nhap (420568985)
    la CHUAN: dat 4,4 + 2,8 lot tren von 200 USD ra **don bay 547x** thay vi 5,52x. Cach kiem
    khac nhau tung san: **XM** kiem bang `EURUSD.trade_contract_size` (1.000 = Micro);
    **Exness** kiem bang `account_info().currency` (USC = cent, contract_size KHONG doi).

### CAP NHAT 2026-07-29 (toi) — KHUNG NGAN: DO XONG, KET QUA AM TINH
21. **KHONG CO TINH LIEN TUC sau nen day manh** (`nhoi_lenh_do_co_che.py`, US500M M1
    2,26 trieu bar 6,6 nam). Loi suat K bar ke tiep NHAN DAU nen kich hoat:
    M1 K=1 chi +0,01..+0,14 bps roi AM tu K=3; M5 am gan nhu moi o (top 1% bien do:
    -0,69 / -1,47 / -2,05 / -3,54 bps o K=1/3/5/30). **Sau nen manh gia QUAY DAU,
    khong di tiep** - khop voi ket luan SP500 khung ngay la mean-revert. Moc chi phi
    1,6 bps khu hoi; so momentum tot nhat (+0,14 bps) van nho hon chi phi 11 lan.
22. **Nhoi lenh theo chieu + chot khi tong lai (usePyramid/DCA duong): 18/18 cau hinh
    deu AM**, trung binh -11 den -17 bps/su kien. Ty le thang len toi 77,7% di kem
    trung binh -16,92 bps va lenh te nhat -1.939,9 bps. Lan thu TU du an gap hinh dang
    "ty le thang cao + ky vong am + duoi trai day" (gong lo V6, TP 0,5%, DCA DongDongTV).
23. **KHONG THE lam order flow (delta / big trade) tren CFD** - da kiem ca XM lan Exness,
    ca 4 symbol (`kiem_du_lieu_orderflow.py`): `volume = 0`, `volume_real = 0`,
    `session_deals = 0`, va **100% tick chi la doi BID/ASK, khong co co phan loai
    ben mua/ban**. CFD khong co san khop lenh nen khong co tape. Moi chi bao "delta"
    tren chart MT5 CFD deu tinh tu so tick tang/giam = ham cua chinh gia, khong mang
    thong tin moi. Order flow that chi co tren **futures CME (ES/MES)** + thue data
    CME + nen tang (Sierra/ATAS/Jigsaw) + moi gioi futures.

- **magnetic** chi nen chay ban rut gon 53/169 moc — 90/169 moc la bien the pivot trung lap,
  va phan vi 90 cua avg_R giong nhau o moi moc (xep hang chi la cuc tri ngau nhien).

### CAP NHAT 2026-07-31 — BOT SESSION TRADING V3 DA BI QUET TREN 21 THI TRUONG
Bao cao: `reports/BAO_CAO_SESSION_DA_THI_TRUONG.md`. Script `quet_session_bot.py`.
24. **Setup A (Pivot Breakout) chet tren gan nhu moi thi truong, khong phai chi SP500.**
    520 lan chay tester that (21 thi truong x luoi tc_RR 1-5 x tc_StopDistance 50-350,
    2020-2026): **12/21 thi truong khong co noi MOT o duong**. US500m 0/20 va ca 5 bien the
    co che deu 0/20. Lot co dinh cho ky vong ~0 -> khong co edge, risk 2% chi phong to so 0.
25. **Cho bot "co lai" (XAUUSD 20/20, USDJPY 20/20, ETH, JP225) deu vo ra khi chay TUNG NAM.**
    Vang: 4 nam 2020-2023 chi +2.211 voi DD 42,7%, 93% lai nam o 2024+. USDJPY: bo nam 2025
    thi con +724/4 nam. GBPUSD voi tham so GOC la 1/5 nam duong (-6.544) - con so +10.569
    chi ton tai o dung o SD=250. **Luon chay tung nam truoc khi tin mot bang tong.**
### CAP NHAT 2026-07-31 (toi) — DONG DONG DA XONG, VA BON QUY TAC MOI
Bao cao: `reports/BAO_CAO_2026_07_31.md` (thay the `BAO_CAO_SESSION_DA_THI_TRUONG.md`).
27. **KIEM LICH SU SYMBOL TRUOC MOI BANG SO SANH DA THI TRUONG** —
    `kiem_lich_su_symbol.py`. Exness chi co bar tu **2022-08-01** cho 24/25 symbol;
    RIENG XAUUSDm co tu 2018-12. Lenh `FromDate=2020.01.01` chay cho tat ca -> vang
    duoc 6,5 nam con moi thu khac 3,9 nam, va **tester khong bao loi gi**. Dau hieu
    nhan ra la SO LENH. Bang "21 thi truong" cu dinh dung loi nay.
28. **HOAN VI THU TU LENH LA PHEP THU VO NGHIA voi lai kep ty le co dinh.** Tich
    `prod(1 + risk*R)` giao hoan -> ket cuc KHONG doi du xao tron kieu gi, chi duong
    di doi. Muon do bat dinh phai **lay mau CO HOAN LAI theo KHOI** (khoi 60 lenh giu
    cum che do). Hoan vi chi con dung de do phan phoi SUT GIAM.
29. **PF 0,1 khong phai con so cua thi truong** — he thong te that cung chi 0,7-0,9.
    PF duoi 0,3 hau nhu luon la ao giac do lai kep tren edge am: tai khoan chet som
    -> it lenh -> PF suy sup. Chay lai voi **lot co dinh** truoc khi ket luan. Da sap:
    XAUEURm PF 0,12 (435 lenh) -> lot co dinh thanh PF 0,73 (815 lenh).
30. **Hoi "ky vong co khac 0 khong" TRUOC khi ban ve tham so.** Session V3 tren vang:
    +0,0497R/lenh nhung **t = 1,714, p = 0,087, KHONG dat** - va do la truoc hieu chinh
    420 phep thu. Can 2.126 lenh (~8,5 nam) moi du, ta chi co 6,5 nam. Moi bang lai
    theo risk% deu dung tren nen nay. **Mua-giu vang co Calmar 0,56 so voi 0,38-0,47
    cua bot o moi muc risk**, va Calmar bot GIAM khi tang risk -> khong co muc toi uu.

### CAP NHAT 2026-08-01 — FILE .SET CUA CHU BOT, VA 3 NAM NGOAI MAU
Bao cao: `reports/BAO_CAO_2026_08_01.md`.
31. **DOC KY FILE .SET NGUOI DUNG DUA TRUOC KHI CHAY BAT KY BANG NAO.** Ban cua chu
    bot Session V3 bat `u_LotteryMode=true, lotteryMultiplier=1.3` — 820 pass cua hai
    phien truoc deu chay voi lottery TAT, tuc **khong bang nao la bang cua cau hinh
    nguoi dung dang chay**. Lottery Mode = **martingale tren LOT** (sau thua x1,170;
    sau thang x0,881; khong doi diem vao — 2.356 lenh trung 100% ngay, trung ca so
    lenh thang 1.000/2.356). Von cent 20.000, 2017-2026: tat = **+54.354 / DD 30%**;
    bat x1,3 = **-1.550 / DD 94,4%**; x1,5 tro len = **DD > 100% (am vao tien san)**.
    Thua o **10/10 o** cua luoi risk% x lottery. `maxTrades` KHONG phai phanh chuoi —
    no la gioi han TONG so lenh ca doi chay (dat 8 thi bot danh dung 8 lenh roi ngung).
32. **KIEM DO SAU LICH SU BANG `copy_rates_range` VOI MOC RAT XA + DEM BAR MOI NAM.**
    `copy_rates_from_pos` va cache parquet cua du an cat mat 3 nam: XAUUSDm that ra co
    M5 tu **2017-01-03** (khong phai 2020-01 nhu bao cao 31/07 ghi). Va MT5 **don bar
    NGAY vao yeu cau khung M5** cho giai doan khong co du lieu phut — 2014-2016 ra dung
    ~310 bar/nam, khong bao loi. Dau hieu nhan ra la so bar/nam.
33. **Bar M5 cua MT5 co cot `spread` THAT tung bar** (don vi POINT). Het phai gia dinh
    chi phi. Vang: trung vi 0,16-0,30 USD/oz on dinh suot 2017-2026 — spread vang on
    dinh theo SO TUYET DOI chu khong theo bps (ngoai le voi quy tac 7).
34. **Ngoai mau 2017-2019 lam YEU edge vang chu khong cung co**: ky vong +0,0221R
    (t=0,49) so voi +0,0533R trong mau; ca 9,5 nam / 2.330 lenh van **p = 0,069**.
    Diem cong that: edge duong o **CA HAI chieu mua va ban** (+0,054R / +0,034R) nen
    khong phai drift cua vang doi lot; va bot dong het 23:00 nen khong mat phi qua dem.
    Gio 04:00 xep thu **7/24** ngoai mau (1/24 trong mau) — khong phai gio duoc chon.
35. **XAUUSD hon XAUEUR/XAUGBP/XAUAUD gan nhu HOAN TOAN vi spread.** Cung cua so
    2022-08→2026-06, cho spread = 0 thi bon cap gan bang nhau (+0,083 / +0,081 /
    +0,061 / +0,051 R). Spread that an mat 0,021R (XAUUSD) so voi 0,30-0,53R (ba cap
    cheo) vi spread rong gap 16-23 lan trong khi khoang cach SL tuong duong.
    Exness **KHONG CO XAUCAD/XAUCHF/XAUJPY** — chi 4 cap vang.

36. **DOI DONG TIEN TAI KHOAN KHONG CHO THEM VON — va con lam hong EA.** Cong thuc
    lot chia so du cho khoang cach SL tinh BANG DONG TIEN TAI KHOAN, hai ve nhan cung
    he so ty gia nen triet tieu: 200 USD nap vao cent USD/AUD/NZD/EUR/JPY deu ra
    **cung 0,2901 lot**. Loi the cent that su chi la **bo san min lot** (do min tu
    3,4% xuong 0,034% rui ro/lenh tren 200 USD), va o 20.000-30.000 cent lot trung vi
    da cach min lot **29-65 lan**, 0-0,1% lenh bi kep -> **khong con gi de tan dung**.
    Do tester that: ba tai khoan phi-USD deu cho lot trung vi **dung bang min lot
    0,01** (bao USD 0,370) va ty le lot so voi ban USD **giong het nhau o ca ba** du
    ty gia khac han -> khong phai chuyen quy doi, ma la EA roi ve duong du phong.
    Cung 200 USD: USD +126,1% / AUD +71,6% / EUR +70,7% / JPY +71,5%.
    **EA DongDongTV viet cho tai khoan USD.**

37. **HAI BOT DONGDONGTV CO THAM SO KHAC HAN NHAU — dung lan.** "Lot ban dau 0,05"
    va "chot loi/lo TOAN CHUOI theo tien" (`Lot_BatDaub/s=0.05`, `tpAll_Money=1000`,
    `useTSCloseAll`) la cua **DCA Am Duong V20.8**, KHONG phai Session V3. Goi
    `Session Trading V3.0.rar` **khong co file `.set` nao cua nha phat hanh** — chi
    `.ex5` + `HDSD.txt` (chi co link Tiktok/Zalo/IB, khong mot dong ve tham so) +
    2 anh huong dan them WebRequest. Ban `.set` nguoi dung co la ban TU LUU (ghi cho
    V2). Danh sach input day du cua EA doc o muc **"Dau vao"** trong bao cao `.htm`
    cua tester — MT5 liet ke het, tin duoc; rut chuoi tu `.ex5` khong ra gi vi file
    da nen.
38. **Session V3 CO cat het theo gio (`s1_time_Close`) va no LAI, khong phai cho chay
    mau.** 2.330 lenh: TP 19,5% (+1,955R) · SL 43,1% (-1,041R) · **cat theo gio 37,4%
    (+0,299R, dong gop +260R trong tong +103R)**. Trong nhom bi cat: 64,1% dang lai
    (+0,654R), 35,9% dang lo (-0,336R), **lo nang nhat -0,896R** — khong the lo hon
    SL. Noi cua so giu lenh khong giet edge (12h +0,0442R -> 24h +0,0545R) nhung
    **KHONG hanh dong duoc**: `s1_time_Close` la gio trong ngay, dat lenh 04:00 server
    nen noi het co cung chi ~13h.
39. **Bot yeu cau WebRequest toi `https://script.google.com`** (+ anh cua nha phat
    hanh tick ca "Allow DLL imports"). Khong co thi bot khong chay. Tuc EA goi ra
    ngoai moi phien — can internet on dinh tren VPS, va nha phat hanh nhin thay tai
    khoan dang chay.

### CAP NHAT 2026-08-01 (toi) — `Model=1` CHE RA LAI GIA. BAY LON NHAT TU TRUOC DEN NAY
40. **`Model=1` ("1 minute OHLC") KHONG DUNG DUOC khi TP/SL nho hon bien do nen M1.**
    No gia dinh mot duong di O->H->L->C trong moi nen M1, nen TP nam gon trong nen
    se luon duoc "khop" o chan thuan loi. Do duoc bang cau hinh scalping cua DCA Am
    Duong (TP chuoi 50 pip = **0,50 USD/oz**, giu lenh trung binh 41 phut), cung cau
    hinh cung cua so 2024-2026:
      Model=1 (1 min OHLC)      -> **+1.161,5%** · PF 1,71 · 11.140 lenh
      Model=0 (every tick)      -> **-100,7%**  · PF 0,57 ·  1.487 lenh (chay tk)
      Model=4 (tick THAT)       -> **-100,7%**  · PF 0,57 ·  1.487 lenh (y het M0)
    Hai mo hinh tick khop nhau tuyet doi va lech Model=1 **12 lan**. Ket luan "DCA
    chet" cua bao cao 31/07 VAN DUNG, nhung suyt bi lat nguoc boi mot so gia.
    **Quy tac: neu TP hoac SL < ~2x bien do nen M1 cua tai san do thi BAT BUOC chay
    lai Model=0 hoac Model=4 truoc khi tin bat ky con so nao.**
    Session V3 khong dinh bay nay (SL = bien do 4h phien A, trung vi 6,89 USD/oz ca
    ky va 29,11 tu 2025, gap hang chuc lan nen M1) — nhung van phai kiem, khong duoc
    suy dien.
41. **`Nen_CloseOnSPTFlip` la cong tac cat lo cua DCA, va ban `.set` trong `.rar` de
    `false`.** Toan bo 480 pass DCA cua bao cao 31/07 chay voi co che cat lo TAT.
    Clip 11/06/2026 cua nha phat hanh noi ro "khi dao trend thi cat lo luon". Bat len
    o Model=1 cho +1.396,8% — nhung do la so gia (muc 40). O tick that van chay tai
    khoan. **Luon liet ke cong tac nao trong `.set` dang TAT ma tai lieu/clip noi la
    PHAI BAT.**
42. **Tai lieu that cua bot khong nam trong goi `.rar` ma nam trong CLIP YOUTUBE.**
    `HDSD.txt` chi co link Tiktok/Zalo/IB. Ba clip da doc (luu o `reports/clip_ddtv/`):
    - `N7LgiYPwALo` 26/05/2026 "SETTING CHUAN ... SESSION TRADING V2.0" — nguon chuan
      cho Session. Xac nhan tu mieng tac gia: lottery = **tang lot sau moi lan SL**
      x1,3; `maxTrades` = **gioi han tong so lenh ca doi** ("de 10 thi chay 10 ngay
      roi dung"); risk 2%; RR 1:2; StopDistance mac dinh; phien 2 tat.
    - `g-Hdpbu9aVo` 03/07/2026 "CACH TRADE CHO NGUOI BAN RON" — DCA, khop dung file
      `20.8_trade theo nen h1.set` trong `.rar` (0 tham so khac). Quy tac lot:
      **0,01 lot moi 1.000 cent**.
    - `_ctjZJe2pKs` 11/06/2026 "TRADE SIEU SCALPING H1" — DCA nhung TP 50 pip,
      lot 0,02 moi 1.000 cent, bat cat lo khi dao trend. Set file chi co tren Telegram.
43. **Lap luan "RR 1:2 chi can 34% thang la co lai" cua tac gia bo qua lenh THOAT
    GIUA CHUNG.** No gia dinh moi lenh ket thuc o +2R hoac -1R. That te chi 62,6%
    lam vay: 0,424x2 - 0,576x1 = **+0,272R** theo cach tinh do, nhung do that la
    **+0,044R** (nho hon 6 lan) vi 37,4% lenh bi cat theo gio o trung binh +0,299R.
44. **Chay lai DCA dung quy tac lot cua tac gia (0,01/1.000 cent) thi chay sach o
    MOI muc von**: 5.000 -> -100,5% · 10.000 -> -100,5% · 20.000 -> -106,7% ·
    30.000 -> -105,4% (DD > 100% = am vao tien san). Bao cao 31/07 chay lot 0,05 tren
    von 20.000 = chi bang **1/4** muc tac gia khuyen nghi, va da chet san.

### CAP NHAT 2026-08-02 — QUET 28 CAP FX x 26,5 NAM, VA 4 BAY DO LUONG MOI
Bao cao: `reports/BAO_CAO_ULTIMA_2026_08_02.md` phan 2.
45. **Lan goi `copy_rates_*` DAU sau `symbol_select` tra THIEU bar, khong bao loi.**
    Ra 26/31 cap "khong co du lieu"; them vong thu lai 4 lan x 1,5 giay -> du 28/28.
46. **XM CO tra bar H1 — phai goi `copy_rates_from_pos`, KHONG phai `copy_rates_range`.**
    Ghi chu cu "XM khong tra H1" la sai vi goi sai ham. Va **bar D1 cua XM co
    `spread = 0` toan bo, chi H1/M1 moi co spread THAT** (khac Exness, ben do M5 co).
    Doc nham cot spread cua D1 lam NZDCAD nhay tu hang 28 len hang 11.
47. **Spread doc tu `symbol_info_tick` vao CUOI TUAN bi thoi 2-6 lan.** NZDCAD tick
    22,9 pip nhung that 3,9; EURUSD 7,3 vs 1,9. Kiem thu trong tuan truoc khi tin.
48. **Rau nen HONG trong lich su che ra ca so dep lan so xau.** Phan biet bang GIA DONG
    CUA: rau hong thi close ve nguyen cho cu trong cung bar. Nguong
    `low < min(open,close)*0,90`. CADCHF 100,00% -> 42,56% sau khi cat; nhung 2015-01-15
    (SNB bo neo), 2008-10 (giai chap JPY), 2016-06-24 (Brexit) la THAT, phai GIU.
49. **Luoi khong SL: ham muc tieu la `quang_duong/MAE_max²`, khong phai `min(MAE_max)`.**
    Cap cang hien thi luoi cang it lenh cang it lai. Tuong quan hang MAE-max vs loi suat
    chi -0,717. Va **noi buoc luoi khong cai thien gi**: TP co dinh thi von ∝ 1/S va lai
    ∝ 1/S triet tieu nhau; TP ti le buoc thi gioi han la luoi con 1 lenh = het la luoi.
50. **Neo ve LAI vao tai khoan THAT, dung mo hinh ly tuong.** "Moi lan xuyen 1 tang =
    1 TP" cho 3.000 lenh/nam/cap trong khi tai khoan that co 366 — thoi 8 lan.
51. **Giong khung THOI GIAN truoc khi lay chi so theo vi tri.** BTC bat dau 2014, ETH
    2017, VNM 2009 — dung chi so cua chuoi nay cat chuoi kia la lech hang gia, khong
    bao loi. Phai `pd.concat({...}, axis=1).dropna()` roi moi `.to_numpy()`.
52. **Mau "cung pha chu ky" cua halving 2020 gan het BAT DAU DUNG DAY** (BTC 16.625)
    -> sut giam DCA ra 5,6%, trong khi do tren 66 cua so bat ky la **23,7% trung vi /
    44,6% xau nhat**. Chenh 4 lan. Khi mau nho thi DIEM VAO cua mau tro thanh "ket qua".
    Luon doi chieu voi mau day du truoc khi bao mot con so rui ro.
53. **Chi phi CO DINH quyet dinh o quy mo nho, khong phai loi suat.** Chan giao dich
    V6+vang lai 9,9%/nam nhung o muc von 6-18tr thi VPS (5,1tr/3,25 nam) LON HON toan
    bo lai gop -> lai rong AM. Phan bo 10-20% "thu cho biet" la phuong an te nhat.
    Luon tinh chi phi co dinh theo % LAI, khong theo % von.

26. **Ba bay ky thuat khi lai tester bang dong lenh** (chi tiet o memory `mt5-tester-dong-lenh`):
    `Report=` tuyet doi bi lo di khong bao loi (phai tuong doi, file ra o thu muc DU LIEU);
    `terminal64.exe /config:` khong chan (phai poll process); bao cao .htm tieng Viet goi
    **Gross Profit** la "Loi nhuan rong", loi that la "**Tong** loi nhuan rong" (sai 13,5 lan).
