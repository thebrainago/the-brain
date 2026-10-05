# Ho so co che do tu LENH THAT - bo CCBSN (VAMGE v3.05 + CanCuBo v2.6) - 04-05/10/2026

Nguon do: 3 tep lich su lenh cua MAY THU MT5 (`reports/fixture/tester_vamge10k_kp_deals.csv.gz`, `tester_cancubo_xn_deals.csv.gz`,
`tester_cancubo_kp_deals.csv.gz`) + 2 bo `.set` cua tac gia (`ccbsn305_vamge10k.set.txt` 190 tham so, `ccbsn26_cancubo10k27.set.txt`
172 tham so). San GOLD.i# (vang, XM). Day la lich su cua may thu, KHONG phai tai khoan that.
Cong cu: `nhan/ho_so_bot.py` (do 52 khoi co che tu lenh) + `nhan/ho_so_set.py` (doi chieu tung tham so `.set` voi so do)
+ `b nc cc ho_so_bot` (dua vao so tay nghien cuu). Bot la hop den (.ex5): moi dieu duoi day la DO tu lenh, khong doc tu ma.

## 0. Doc nhanh (loi thuong)

1. Hai bot cung la "nhoi them lenh khi gia di nguoc" (luoi / DCA) tren vang nhung moi con mot cach: **VAMGE** thoat ca chuoi o 10 pip
   (lenh don) hoac 20 pip (da nhoi), lot phang den lenh 10 roi nhan 1,2 tu lenh 11 va 1,1 tu lenh 21, co hedge khi chuoi >= 16 lenh;
   **CanCuBo** chi MUA, buoc co dinh 100 pip, lot nhan 1,05 moi lenh, thoat bang khoa loi truot cua ca chuoi (15 pip, nhich 2 pip),
   khong chuoi nao lo (0/955).
2. Cong thuc lot do duoc KHOP het: 3114/3114 lenh (VAMGE), 1467/1467 va 1962/1962 (CanCuBo).
3. Moi tham so `.set` duoc xep vao DUNG MOT ket qua: khop / mau thuan / tat / bi che / chua gap / khong do duoc / khong ro. Khong tham
   so nao bi ghi la "tac gia khong dung" chi vi khong do duoc.
4. Co cho tac gia noi mot dang, lenh that cho thay dang khac (muc 4): VAMGE 4 cho, CanCuBo 2 cho. Khong chon ben nao.
5. Co hai co che chay that ma KHONG tham so nao dieu khien (muc 5): "chi nhoi them toi da 1 lenh moi nen 15 phut" (VAMGE) va "chi mua"
   (CanCuBo).
6. Chua do duoc: cach vao lenh dau (can duong gia), hedge sau, tia lenh, tran lot / so lenh (chuoi chua toi muc do) - nam o muc 7.

## 1. Mau

| | VAMGE v3.05 (kham_pha) | CanCuBo v2.6 xac_nhan | CanCuBo v2.6 kham_pha |
|---|---|---|---|
| lenh (da tach lenh bao hiem) | 3114 (+19 hedge) | 1467 | 1962 |
| chuoi (mot chu ky luoi) | 1198 | 955 | 1291 |
| thoi gian | 2018-02-02 .. 2021-10-01 | 2021-10-13 .. 2024-04-05 | 2018-01-02 .. 2021-10-08 |
| luoi thoi gian cua lich su | 10 s | 19,5 s | 10 s |
| tham so `.set` | 190 | 172 | 172 |

Canh bao do tin: moi lenh trong tester nam tren mot LUOI GIAY (10 s hoac 19,5 s), nen moi so o muc giay (tre, khoang cach) chi
tin tu muc ~60 s tro len. Cac so ve gia (pip) khong bi anh huong.
Don vi: 1 don vi khoang cach trong `.set` = 1 pip cua san = 0,1 USD tren vang (do bang 4 nhom so, he so 1 thang tuyet doi).

## 2. Co che do duoc va gia tri tac gia khai (KHOP = lenh that trung khai bao)

**VAMGE** (do tin do cong cu tinh: cao / vua / thap)

| Co che | Lenh that cho thay | `.set` khai | do tin |
|---|---|---|---|
| lot dau chuoi | 0,01 | InpLots 0,01 | cao |
| lot theo bac | lot_n = lam_tron(0,01 x M(n)^(n-1), 2); M = 1,0 (lenh 1-10), 1,2 (11-20), 1,1 (21-25) | InpMultiplier 1,0; NewMultiplier 1,2 tu Orders2NewMultiplier 10; 1,1 tu 20 | cao (102/102 lenh bac 11-20), thap (5/5 bac 21+) |
| buoc | ~10,3 pip (lenh 2-4), ~15,4 pip (lenh 5-17) | Distance0 10; Distance1 15 tu Orders2Distance1 5 | cao |
| thoat | ca chuoi cach gia trung binh >= 10 pip (chuoi 1 lenh) hoac >= 20 pip (chuoi >= 2 lenh) | InpTP 10; InpTPDCA 20 | cao |
| hedge | 19 lenh nhan HS / HB; mo khi chuoi da co >= 16 lenh; lot hedge = lot lenh nhoi moi nhat (100%); cung giay voi lenh chu | UseHedging, Orders2Hedging 15 (EA bat khi VUOT moc: lech +1), UseLotsDCA2Hedging | vua |
| khung vao | chuoi chi bat dau o dau nen 2 phut (100% chuoi; ngau nhien chi 17%) | InpTFSignal 2 | cao |
| khoa loi | ~2 pip (chi 17% chuoi >= 2 lenh, 88% la chuoi BAN) | InpInitialSLTrailing 2 | thap, la gia thuyet |
| chuoi tuan tu | moi luc chi mot chuoi (hai chieu cung mo chi 0,2% thoi gian) | - | vua |

**CanCuBo** (v2.6; xac_nhan)

| Co che | Lenh that cho thay | `.set` khai | do tin |
|---|---|---|---|
| lot | lot_n = lam_tron(0,01 x 1,05^(n-1), 2): 1467/1467 | InpMultiplier 1,05 | cao |
| buoc | ~100,6 pip moi bac (khong doi) | Distance4 100 (4 tang buoc nhung ca 4 moc deu = 1 nen chi tang cuoi co hieu luc) | cao |
| thoat | 96% lenh dong bang khoa loi truot cua chuoi ('sl'), 4% bang 'tp'; khoa dau 15 pip, buoc nhich 2 pip; 0/955 chuoi lo | InpInitialSLTrailing 15; InpTrailingStep 2; InpTP 100 | cao |
| huong | 100% lenh MUA | InpTypeBuySell 0 (khong quyet dinh mot minh, muc 5) | thap |
| khung vao | chuoi chi bat dau o dau nen 1 phut (100%; ngau nhien 65%) | InpTFSignal 1 | vua |

Loi chuoi CanCuBo o lot goc 0,01: p10 1,5 / trung vi 3,0 / p90 10,0 USD. Con so 10,0 la lenh don chot 100 pip (= 10 USD) - TRUNG voi
`MoneyTPAllAcc` = 10 nen KHONG tach duoc hai co che (muc 8, sua sai 2).

## 3. Doi chieu `.set` - so dem

| Ket qua | VAMGE (190) | CanCuBo (172) | y nghia |
|---|---|---|---|
| KHOP | 20 | 10 | khai bao = lenh that |
| MAU_THUAN | 4 | 2 | tac gia noi X, lenh that (co dieu kien de thay X) cho thay Y |
| TAT | 82 | 100 | tac gia tat, lenh that khong co gi nguoc lai |
| BI_CHE | 1 | 8 | tham so co that nhung bi tham so khac che |
| CHUA_GAP | 10 | 7 | dieu kien chua bao gio toi (vd tia tu lenh 20, chuoi sau nhat 17-25) |
| KHONG_DO_DUOC | 59 | 34 | lich su lenh khong cho do (can duong gia, spread, tin tuc...) |
| KHONG_RO | 7 | 4 | thay mot phan, khong ket luan |
| KHONG_LIEN_QUAN | 7 | 7 | ma so, hien thi, chu thich |

CanCuBo: hai lan chay (xac_nhan 2021-10..2024-04 va kham_pha 2018-01..2021-10, cung `.set`) ra CUNG so dem tung loai; chi hai dong
doi do tin (tre dau ngay vua -> cao; khung vao vua -> cao). Khi khong co bang lenh (chi co ho so) cac so cua VAMGE doi
CHUA_GAP 12 / KHONG_DO_DUOC 58 / KHONG_RO 6 (thay vi 10 / 59 / 7) vi chua kiem tung lenh.

## 4. MAU THUAN: tac gia noi X, lenh that cho thay Y (khong chon ben nao)

Cach doc de hieu: day KHONG co nghia tac gia noi doi. Co ba kha nang: (a) tham so chi co hieu luc o che do khac cua EA, (b) may thu khong
ap dung no, (c) EA bo qua no. Ba kha nang khong tach duoc bang lich su lenh.

VAMGE
- `InpMinuteDelayAfterClose` = 60: sau khi dong chuoi, lenh moi mo lai trung vi sau ~44 phut, 61% con ngan hon 60 phut (ngan nhat 20 giay),
  ke ca sau chuoi LO (68% ngan hon). Nghia la "doi 60 phut sau khi dong" khong the hien trong lenh. Do tin cao.
- `InpMinuteDelayNewDay` = 120: van co 56/1198 chuoi (4,7%) bat dau trong 2 gio dau ngay may chu, bang khoang 102% muc trung binh cua
  mot khung 2 gio: khong thay tre dau ngay (gio 00:00-01:00 may chu la gio san nghi, khong co ca lenh dong). Do tin vua.
- `InpPlus` = 0,01 ("cong them 0,01 lot moi lenh"): cong thuc lot khop 3114/3114 lenh KHONG co phan cong them. Do tin vua.
- `InpDistanceMulti` = 1,2: buoc phang theo bac tren 14 bac, khong thay no keo gian. Do tin thap.

CanCuBo
- `InpMinuteDelayAfterClose` = 60: 97% lan vao lai ngan hon 60 phut (trung vi 440 giay, ngan nhat 20 giay). Do tin thap vi CanCuBo khong co
  chuoi lo nen khong thu duoc cach hieu "chi tre sau chuoi lo".
- `InpMinuteDelayNewDay` = 120: 33/955 chuoi (3,5%) bat dau trong 2 gio dau ngay (kham_pha: 65/1291, 5,0%): khong thay tre.

Neu chuyen bot sang tai san khac: KHONG cai "doi 60 phut" vao ban sao cua ta (lenh that khong lam vay).

## 5. CO CHE AN: lenh that lam, khong tham so `.set` nao dieu khien

- VAMGE: "chi nhoi them khi mo nen moi" - 469 cap lenh nhoi them lien nhau, KHONG cap nao nam trong cung mot nen 15 phut (ky vong ngau
  nhien 178 cap, thuc te 0). Nghia la toi da MOT lenh nhoi them moi nen 15 phut. Con so 15 la khung ma phep do tim ra, KHONG phai
  `InpTFSignal` (= 2); co the do la khung bieu do cua may thu - chua kiem. Cap (lenh vao, lenh nhoi dau tien) van co the cung nen:
  luat khong tinh lenh vao. Khoi: `luoi_theo_nen_moi`. CanCuBo kham_pha cung co dau vet (22 cap, 0 cap cung nen, ky vong 8; do tin
  thap) - co the cung mot ho EA.
- CanCuBo: "chi mot chieu" - 100% lenh MUA du `InpTypeBuySell` = 0 (cung gia tri 0 o VAMGE cho 50% mua / 50% ban). Gia tri 0 khong quyet
  dinh mot minh: con mot yeu to khac (che do `DCAMODE` / `CoeffMode`, tin hieu vao).
- Hai tham so `InpDCAMODE` = 1 va `InpCoeffMode` = 0 cung nhom nay (chua tach duoc che do khac biet vi lot va buoc da khop).

## 6. So sanh hai bo `.set` (hai bot khac nhau, cung ho tham so)

172 tham so co o ca hai bo. Chi **4** tham so thay doi dong thoi voi hanh vi doi (doi khai bao keo theo doi lenh that, ca hai khop):
`InpTP` (10 vs 100 pip; cao), `InpMultiplier` (1,0 vs 1,05; cao), `InpInitialSLTrailing` (2 vs 15 pip; thap), `InpTFSignal` (2 vs 1 phut; vua).
**2** tham so cung khai nhung hanh vi khac (con yeu to khac): `InpTypeBuySell`, `InpMinuteDelayAfterClose`. Khong co tham so nao
khac khai bao ma cung hanh vi. 166 tham so con lai chua du so do de so sanh (mot ben chua do duoc).
Bay khoi co che co o mot bot nhung khong co o bot kia (vd VAMGE co hedge + lot theo bac + TP chuoi; CanCuBo co mot chieu + buoc co dinh).
Day la "thi nghiem tu nhien": doc nhieu `.set` cua CUNG MOT bot (CLMCA co 5 `.set`) se tach duoc tung tham so.

## 7. KHONG do duoc tu lich su lenh (can duong gia / `.set` / ma nguon)

- Cach vao lenh dau (chi bao nao, nguong nao): can duong gia M1-M2. Hien chi biet **khung** (VAMGE nen 2 phut, CanCuBo nen 1 phut).
- Hedge sau 16 lenh chi co 19 lenh o VAMGE: co du de khop lot / so lenh, khong du de ket luan dong hedge (khi nao thoat).
- Tia lenh (sniper), loc DCA tu lenh 25, tran 100 lenh, tran lot 2,3: chuoi chua bao gio toi muc do (VAMGE: dinh 2,21 lot gom hedge =
  96% tran 2,3 nen **khong ro** tran co chan lenh ke tiep hay khong).
- Loc spread / tin tuc / ADX / ATR / gio: lich su khong co spread, khong co lich tin.
- 19 khoi can du lieu ngoai (xem `HB.kiem_dang_ky()` va muc "Lich su lenh KHONG cho do" cua ho so).

## 8. Sua sai trong qua trinh (de khong lap lai)

1. **Don vi**: tung ghi nham `Distance0=10` <-> 10 USD. Dung: 1 don vi `.set` = 1 pip = 0,1 USD; `Distance0=10` = 1,0 USD, `Distance4=100` = 10 USD.
   Moi khop tham so phai dung MOT he so don vi chung cho ca ho `.set` (do bang nhieu cap so).
2. **"p90 = 10,00 = MoneyTPAllAcc"** la trung hop: lenh don lot 0,01 chot 100 pip = 10 USD. Khong du de noi bot chot theo tien.
3. **"149 cap lenh lien tiep cach nhau < 60 giay"** la nhan tao cua luoi giay tester, khong phai nhip that cua EA.
4. **`he_so_bac_1` = 0,986** (VAMGE, lot bac 2-10): la TRUNG DIEM cua khoang he so tuong thich 0,926..1,046 sinh tu lot da lam tron,
   khong phai gia tri do. Se doc nham thanh "giam dan". Da sua (05/10): ho so nay nay bao SO TRON NHAT trong khoang (1,0 = lot phang;
   CanCuBo 1,051 / 1,049 thanh 1,05 = dung khai bao). Khoang van duoc ghi o `ghi_chu`.
5. **Cach do "tre dau ngay"** ban dau khong dua vao gio dong ho cua may chu nen sai; da sua o commit 67c43df (do theo gio dong ho
   tuyet doi, o 30 phut cua ngay). Khong dung cac truong cu `tre_dau_ngay_phut_min` / `p05` neu thay trong ho so cu.

## 9. Y nghia cho viec chuyen bot sang tai san / khung khac (tai_lieu/CHUYEN_BOT_SANG_TAI_SAN_KHAC.md)

Moi khoi co che co mat trong lenh that tra ve `cong_thuc` (tham so da do + don vi + tham so `.set` tuong ung + co khop hay khong).
Do la HAT GIONG cua "the phuong phap" dung lai duoc: vi du the VAMGE = {lot theo bac [1,0 / 1,2 / 1,1; moc 10 / 20], buoc theo bac
[10 -> 15 pip; moc 5], thoat ca chuoi [10 / 20 pip], hedge sao chep lot sau 16 lenh, vao theo nen 2 phut, toi da 1 lenh them / nen 15
phut}. Thu cho tai san khac phai doi cac tham so khoang cach (pip) theo bien do cua tai san do (khong giu so pip) va giu nguyen cac
ty le / so dem (he so lot, moc theo bac). Phan nay (S0-S5) con la viec lam tiep, khong co ket qua nao trong bao cao nay noi rang
chuyen sang tai san khac se co lai.

## 10. Con lai, de lam tiep

- May nha chay `b nc cc ho_so_bot` tren cac tep that (bao cao ra `reports/ho_so/`), co the them cac bo `.set` khac cua CLMCA de
  doc cheo.
- Bien the doc DUONG GIA de do dieu kien vao lenh (muc 7).
- Thi nghiem xac nhan "mot lenh them moi nen": chay `.set` VAMGE tren nen 5 phut / 1 gio.
- Bao cao nay KHONG noi bot co lai: day la hieu CO CHE, khong phai bang chung loi nhuan.

## 11. Tai lai

    python3 -m nhan.ho_so_set reports/fixture/tester_vamge10k_kp_deals.csv.gz reports/fixture/ccbsn305_vamge10k.set.txt --ma 'GOLD.i#' --md ra.md
    python3 b.py nc cc ho_so_bot '{"lenh":"reports/fixture/tester_vamge10k_kp_deals.csv.gz","bo_set":"reports/fixture/ccbsn305_vamge10k.set.txt","ma":"GOLD.i#","ten":"vamge","them":[{"lenh":"reports/fixture/tester_cancubo_xn_deals.csv.gz","bo_set":"reports/fixture/ccbsn26_cancubo10k27.set.txt","ten":"cancubo","ma":"GOLD.i#"}]}'

(Chay thang tren may nha vi `b nc cc` ghi mot dong vao so tay nc.db.)
