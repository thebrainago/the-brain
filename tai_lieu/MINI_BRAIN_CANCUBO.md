# MINI-BRAIN CANCUBO - ban thu nho cua The Brain chay tren Linux, mo xe MOT con bot (09/10/2026)

Y chu du an (09/10/2026, nguyen van, khong dau): *"gio chinh tren Linux nay hay van hanh ban thu nho cua toan bo the brain. Bao gom cac buoc
cao du lieu boc tach co che roi kiem nghiem va tinh chinh. Khong can so luong chi can chat luong de toi uu quy trinh va nang cao hieu suat.
Cac buoc nao ma can du lieu ngoai bao cho toi de may nha chay. Ta co the chi can mo xe 1 vai con bot ... hay thu ki tren gia lap va mt5
(co the cho may nha chay mt5 roi cat du lieu sang) nham so sanh va tim ra quy luat backtest"*.

Con bot duoc chon: **CanCuBo = CCBSN v2.6 + bo `.set` "Can Cu Bo 10K 2.7"** (vang XM `GOLD.i#`, hop den) - bot song sot DUY NHAT cua kho
(`KHO_CO_CHE_BOT.md`), da co 2 lich su lenh that tren tester: `kp` (kham pha, 1.291 chuoi / 1.962 lenh) va `xn` (xac nhan, 955 chuoi / 1.467 lenh).

## 1. Day chuyen cua ban thu nho (TIM -> LAY -> HIEU -> LAM LAI -> THU -> CHINH)

| buoc | trang thai | bang chung / vi sao |
|---|---|---|
| LAY lich su lenh | **XONG** (khong can cao web) | `reports/fixture/tester_cancubo_{kp,xn}_deals.csv.gz` + `.set` (`ccbsn26_cancubo10k27.set.txt`) da nam trong git |
| HIEU co che | **XONG, khop tuyet doi 2.246/2.246 chuoi** | `python3 -m nhan.ea_cancubo_lai kiem`: sai so lot 0, sai so SL lon nhat 0,05 pip (xem muc 2) |
| LAM LAI thanh EA cua ta | **XONG** (`ea_CanCuBoLai.mq5`, bien dich that tren san gia C++) | `vong-kin`: EA chay tren duong gia TOI THIEU suy tu chinh cac chuoi that -> tai tao 2.244/2.244 chuoi (2 chuoi thoat tay bi loai), moi bo dem lech = 0 |
| THU tren gia M1 that + may thu MT5 | **CHUA** - cho may nha | Linux KHONG co gia M1 vang (khong tick, khong M1) va khong co MT5; 5 don da xep san cho may nha (muc 5) |
| CHINH | **CHUA** - sau buoc THU | chi tinh chinh khi biet sai so den tu "dung lai sai" hay "mo hinh backtest sai" |

Phan chua lam KHONG phai vi quen: no can **gia M1 vang that + MT5 tester**, hai thu chi may nha co. Con dung cu da san sang va da kiem tren
du lieu co dap an biet truoc (muc 4), nen khi gia ve chi can chay lenh o muc 6.

## 2. Co che CanCuBo - do duoc tu lenh that (1 pip = 0,1 USD, hop dong 100 oz)
- **Chi MUA**; mot chuoi tai mot luc; lenh dau mo o giay :00 cua mot nen M1 (1.290/1.291 chuoi `kp`, 955/955 `xn`; mot chuoi o giay :30).
- **DCA**: mo lenh them khi **ask <= gia mo cua lenh mo SAU CUNG - 100 pip**; `lot_n = round(0,01 * 1,05^(n-1), 2)` (0 sai so tren 3.429 lenh).
- **MOT TP chung** cho ca chuoi = gia binh quan co trong so lot + **100 pip (1 lenh) hoac 200 pip (>= 2 lenh)**; khop DUNG muc TP / SL (khong truot gia).
- **MOT SL truot chung**: kich hoat khi (bid - gia binh quan) >= 30 pip; khi do SL = gia tb + (15 + 2 * floor((loi_pip - 30) / 2)) pip. SL lech lon nhat
  0,050 pip so voi lenh that. Chuoi `kp`: thoat bang sl 1.249 / tp 41 / tay 1; `xn`: sl 902 / tp 52 / tay 1; chuoi sau nhat 19-20 lenh.
- Gia binh quan lam tron nua-len theo point nguyen. Swap = 0, commission = 0 trong bao cao tester (swap THAT cua XM khong co trong tester - xem `PHIEN_HIEN_TAI.md`).
- **Tin hieu mo chuoi moi: CHUA hieu** (`InpIndiMode=8`, `InpTFSignal=1`, nhom Ichimoku 9/26/52 trong `.set`; thoi gian cho `MinuteDelayAfterClose=60`,
  `MinuteDelayNewDay=120` nhung lenh that cho thay dang khac, xem `reports/ho_so_bot_that_20261004.md`). EA dung lai **phat lai** gio mo chuoi cua bot goc
  (mang `G_VAO`) - tach "dung lai QUAN LI LENH" (da xong) khoi "tim TIN HIEU VAO" (cau hoi mo, muc 7).

## 3. Quy luat BACKTEST thay trong lenh that (MOI chi tu deals, **chua kiem voi gia M1 that**)
Dem giay thoat / DCA cua 2.246 chuoi that (Model 1 = "1 minute OHLC" cua MT5 tester):
- SL: giay :40 = 1.888 | :20 = 211 | :00 = 28 | :59 = 24. DCA: :40 = 1.035 | :20 = 129 | :00 = 18 | :59 = 1.
- Tuc la may thu Model 1 chia moi nen M1 thanh **4 tick o giay 0 / 20 / 40 / 59**; cho mua, ao thap (low) o :40 voi nen giam va o :20 voi nen tang -> thu tu tick
  **theo CHIEU nen** (tang: O-L-H-C, giam: O-H-L-C). Kiem tren lenh that chi cho thay *tuong thich*, khong chung minh.
- **Mua khop o ASK = bid + spread**; TP / SL (phia may chu) khop DUNG muc cua no (lenh that: lech 0,05 pip). San gia kiem TP truoc SL khi hai cai cung nam trong mot tick (quy uoc cua san, chua do duoc tu lenh that).
- 5 luat tick duoc bo san kiem: `theo_nen`, `nguoc_nen`, `thap_truoc`, `cao_truoc`, `xen_ke` (`ea_gia_lap.THU_TU_NEN`; `nguoc_nen` them 09/10, doi thu cua `theo_nen`).
  Ket luan chi duoc `RO` khi luat tot nhat khop >= 99% su kien VA moi phep so voi 4 luat con lai co p <= 1e-6 (kiem dau nhi thuc, mot phia).

## 4. Bo dung cu va DO TIN CAY (khong co du lieu ngoai van kiem duoc)
`nhan/so_ea_voi_tester.py` (~800 dong) + `test_so_ea_voi_tester.py` (126 bai, 33 giay). Cac ham: `kiem_luat_tick` (tung su kien hop le theo luat tick nao, 4 ket luan
RO / CHUA_RO / KHONG_KHOP / CHUA_DO_DUOC), `do_lech_gio` (quet +-6 gio de bat lech gio / DST giua kho gia va tester), `quet_mo_phong` (luoi luat x ratchet),
`so_ba_chieu` + `chan_doan` (lenh goc <-> mo phong <-> tester MT5: tach "dung lai sai" khoi "mo hinh backtest sai"), `chay_tester` (CHI may nha), `tu_kiem`.
- **Tu kiem tren gia tong hop co dap an** (`python3 -m nhan.so_ea_voi_tester tu-kiem`; hoac `b nc cc so_ea_voi_tester '{"che_do":"tu_kiem","ngay":120,"seed":1}'`, ~19 giay):
  sinh 120 ngay vang, chay EA that tren tung luat tick -> **chon DUNG luat that 4/4**, cung (luat that, ratchet=1) la cap duy nhat khop o buoc quet. Do phan giai:
  cap kho nhat (`cao_truoc` vs `theo_nen`) can ~107 chuoi ~ 78 ngay giao dich (1,38 chuoi / ngay) => moi cua so don dat o muc 5 (185 va 211 chuoi) du suc.
- **Kiem dot bien** (sua co y ma nguon, moi dot bien phai lam it nhat mot bai hong): module so sanh 68 dot bien -> 65 bi bat + 3 chung minh la tuong duong; EA dung lai 94 dot bien
  -> 89 bi bat + 5 tuong duong. Qua do bo sung 5 bai (cham TP dung muc, dinh SL chi tinh sau lenh cuoi, bien cua so chuoi, dem `kem_hon` trong kiem dau, hoa khi quet lech gio).
- **LOI THAT tim va sua**: `chuoi_tu_vi_the` dung moc "mo mai" nam 9999 cho lenh chua dong - tran so nguyen nano-giay (thanh nam 1815) nen chuoi dang mo nhieu lenh o cuoi cua so
  bi chia thanh nhieu chuoi 1 lenh `het_gio`. Nay dung 2200-01-01; co bai hoi quy. (Sua tren so tay thi MOI so cua cuoi cua so deu lech - rat kho thay bang mat.)

## 5. Don dang cho may nha (viec/cho, uu_tien 0, 5 don, TOAN BO nam trong doan kham_pha cua `XAUUSD|M15` - khong cham xac_nhan)
| don | lan | lam gi | ra gi |
|---|---|---|---|
| `00-sev-1-xuat-gia-vang-m1-2020` | NHE (30 phut) | `b xuat-gia XAUUSD M1 --tu 2020-01-01 --den 2020-12-31` | `du_lieu_gia/XAUUSD_M1_20200101_20201231.csv.gz` (~4 MB) |
| `00-sev-2a/2b-tester-m1/m0-2020-03-04` | TESTER (90 phut) | EA dung lai tren MT5 tester, cua so 2020-03-01..04-30 (~185 chuoi), Model 1 / Model 0, ratchet 1 | `du_lieu_gia/so_ea_voi_tester/tester_m<M>_r1_20200301_20200430.csv.gz` + `reports/so_ea_voi_tester/*.json` |
| `00-sev-3a/3b-tester-m1/m0-2020-07-08` | TESTER (90 phut) | nhu tren, cua so 2020-07-01..08-31 (~211 chuoi) | tuong tu |

Vi sao 2020: 703 chuoi that + hai lan doi gio My (08/03 va 01/11) -> du suc thong ke va bat duoc lech gio kho <-> tester. Cua so 2020-03..04 chua lan doi gio 08/03; cua so 2020-07..08 la mua he
thuan (khong doi gio) -> hai bang chung doc lap, va neu lech gio xuat hien chi o cua so thu nhat thi la loi DST.
**Moi don gan the `so-ea-v1`** (`qwen/cau_git.tag_ma` them the nay khi `nhan/so_ea_voi_tester.py` co ham `chay_tester`) nen may nha chay MA CU **khong nhan** don, khong loi, khong ton luot;
don tu hoat dong sau khi nha nap ma moi (thu `20261008-165737-eea9` buoc A-F + `20261008-094857-6bd4`). Cua so 2020 chi chay duoc **Model 1 / Model 0**
(Model 0 = moi tick do MT5 TU SINH tu nen M1; Model 4 = tick that nhung XM chi co tick that tu `tick_tu = 2024-02-01`, `config/ea_tho.json`) -> **khong dung Model 4**.
Tong khoi luong len git: ~4 MB (gia) + vai chuc KB (bang chuoi + json), trong tran 12 MB / file va 40 MB / lenh cua `xuat_gia`.

## 6. Khi du lieu ve (cloud, KHONG can MT5)
```
git pull --no-rebase origin claude/autonomous-trading-system-rzzt7h
python3 -m nhan.so_ea_voi_tester luat --thu-muc du_lieu_gia --tu 2020-01-01 --den 2020-12-31      # luat tick + lech gio tren deals that (khong can tester)
python3 -m nhan.so_ea_voi_tester so   --thu-muc du_lieu_gia --tu 2020-03-01 --den 2020-04-30 \
        --tester tester_m1_r1_20200301_20200430.csv.gz --ghi                                      # 3 chieu: goc <-> mo phong <-> tester
b nc cc so_ea_voi_tester '{"che_do":"so","tu":"2020-03-01","den":"2020-04-30","tester":"tester_m1_r1_20200301_20200430.csv.gz"}'   # cung viec nhung ghi so tay (DAT/AM; CHUA_DO_DUOC KHONG ghi)
```
Cach doc: `luat` => ket luan `RO` mot luat tick = may thu Model 1 dung luat do (khong chi "tuong thich"); `KHONG_KHOP` (< 90% su kien hop le o MOI luat) => sai gia / sai gio, **chua** ket luan
ve luat (chay `do_lech_gio` truoc). `so` => `chan_doan` neu lech nam o mo phong thi sua `ea_gia_lap` (luat tick, khop theo spread), neu lech nam o tester so voi bot goc thi do
la khac biet dung lai / tin hieu vao. Tat ca ket qua phan biet `CHUA_DO_DUOC` voi `AM`.

## 7. Cau hoi mo va cach tra loi (co du lieu moi biet)
1. **Luat 4 tick chinh xac khong?** (gio :0/20/40/59, thu tu theo chieu nen) - `luat` tren gia M1 that 2020 (703 chuoi) tra loi duoc; neu `CHUA_RO` thi can them cua so.
2. **Ratchet hay follow?** SL chi doi len (ratchet) hay bam gia xuong lai - hai luat chi khac nhau o vai chuoi; don tester co `ratchet=1`; muon ket luan can them 2 don `ratchet=0`.
3. **Trailing tinh tren bid hay gia khac?** Cung don tren, chi hon khi gia M1 co spread that.
4. **Tin hieu vao** (`InpIndiMode=8`; Ichimoku 9/26/52 tren khung M1?) - thu dung gio mo chuoi that lam NHAN, quet luat Ichimoku tren gia M1 xem luat nao tai tao >= 99% gio mo; truoc het can gia.
5. **Mo hinh tester nao sinh ra deals goc?** `KHO_CO_CHE_BOT.md` ghi Model 1 (thu nha 60fa). `luat` cho biet lenh goc khop luat tick nao: khop `theo_nen` la dau hieu Model 1; khop luat khac thi phai xem lai
   ghi chep do (khong tu doan).
6. **Lech gio / DST** giua kho gia (UTC gan nhan) va tester (gio may chu XM) - `do_lech_gio` tu bat; neu ra 0 gio chenh thi bo qua.
7. **`spread` trong M1 la gi** (spread cuoi nen / lon nhat / trung binh?) - quyet dinh gia mua ask = bid + spread, so voi gia khop that.
Khi 1-3 co ket luan: so sanh EA dung lai tren san C++ (mo phong) voi tester MT5 -> viec "chinh" cuoi cung la dua mo phong ve sat tester nhat (chu du an: "toi uu cach mo phong de khop MT5").

## 8. Bay da gap (de khong lap lai)
- Khong goi `ke_hoach` / `chuan_cua_so` voi khung **M1** (se dong bang mot doan M1 moi ngoai y muon); dung "M15" va truyen `cua_so_tay`. Thu tu kiem: ngay -> cua so >= 14 ngay -> nam trong kham_pha.
- Cua so < 14 ngay bi chan ("qua ngan"); ~1,38 chuoi / ngay nghia la it nhat ~107 chuoi (~78 ngay giao dich) moi phan biet noi cap luat kho nhat.
- CLAUDE.md canh bao **Model 1 noi doi** khi TP < 2x bien do nen M1. CanCuBo co TP 100-200 pip (= 10-20 USD), lon hon nhieu bien do mot nen M1 vang thuong gap nen it nguy co, nhung SL truot buoc 2 pip (0,2 USD)
  nho hon bien do nen => van phai doi chung bang Model 0 (hai don `2b`, `3b`).
- File xuat gia khong nam trong `<hop thu>/du_lieu_gia/` thi KHONG BAO GIO len git (runner chi `git add` DUOC_DAY) - don `xuat-gia` phai ghi vao hop thu (da sua 09/10).
- `nc.db` la file cuc bo (gitignore) va mat khi phien cloud het; ket qua can GIU nam o tai lieu nay, `PHIEN_HIEN_TAI.md` va `viec/xong/*.json` -> `so_cai/nc/*.jsonl` (chi may nha ghi).
- Lenh `tester` / `chay_tester` CHI chay duoc o may nha (can MT5); tren Linux no tra `CHUA_DO_DUOC` ro ly do, khong bao gio `AM`.

## 9. Lenh nhanh
```
python3 -m nhan.ea_cancubo_lai kiem            # co che do tren 2.246 chuoi that (kp + xn)
python3 -m nhan.ea_cancubo_lai vong-kin        # EA dung lai chay tren duong gia toi thieu -> tai tao 2.244/2.244
python3 -m nhan.so_ea_voi_tester tu-kiem       # dung cu tu kiem tren gia tong hop co dap an (19 giay)
python3 -m pytest test_so_ea_voi_tester.py test_ea_cancubo_lai.py -q      # 126 + 71 bai
```

## 10. DOI HUONG (chu du an 09/10 toi) - doc truoc khi chay tiep muc 5-6
Chu du an: *"Ta chi gia lap khi nao khong co san file mql5 thoi; con neu co roi thi viec can la backtest dang optimize de tim ra input tot nhat + thu them cac co che quan li von hoac lenh ben ngoai vao."*
- Tai lieu nay la duong **KHONG CO FILE** (dung lai bot tu lenh that, kiem luat backtest). Bot da co `.mq5`/`.ex5` + `.set` (CCBSN, CLMCA) thi di duong **MT5 OPTIMIZE** (`Optimization=1`, nhieu bo tham so MOT lan), khong dung lai bang gia lap.
- Hien `nhan/ea_tho.py` (`tinh`) moi chay tung bo MOT lan MT5 (toi da 7 bo) -> can cong cu `ea_tho_toi_uu` (de xuat chi tiet: `PHIEN_HIEN_TAI.md`, muc 'DOI HUONG 09/10 toi').
- Lop quan li von / lenh ben ngoai chi gan duoc vao EA CO MA NGUON (tester chi chay MOT EA): `ea_CanCuBoLai.mq5` (khop 2.244/2.244 chuoi) la cho gan lop ngoai cho CanCuBo; `.ex5` hop den thi chi toi uu tham so cua chinh no.
- 5 don `00-sev-*` o muc 5 van dung de doi chieu EA dung lai voi tester that (can truoc khi gan lop ngoai), nhung khong con la uu tien so 1.
