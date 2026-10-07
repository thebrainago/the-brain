# Doi chieu bo .set 'VamGe_set' voi lenh that

- Bo .set 'VamGe_set' (190 tham so) doi chieu voi 3114 lenh that cua GOLD.i#: KHOP 20, MAU THUAN 4, TAT 82, BI CHE 1, CHUA GAP 10, KHONG DO DUOC 59, KHONG RO 7, khac 7.
- Don vi khoang cach: 1 don vi trong .set = 1 pip cua san (da kiem bang nhieu cap so duoc).
- Khop chac (do tin cao): InpLots, InpTP, InpUseDCA, InpMultiplier, InpUseChangeMultiplier, InpOrders2NewMultiplier (+7).
- Lot: 3114/3114 lenh dung cong thuc lot_n = lam_tron(0.01 x M(n)^(n-1), 0.01).
- MAU THUAN (tac gia noi X, lenh that cho thay Y): InpMinuteDelayAfterClose (khai 60, tin cay cao), InpPlus (khai 0.01, tin cay vua), InpDistanceMulti (khai 1.2, tin cay thap), InpMinuteDelayNewDay (khai 120, tin cay vua). Vi du: 1196 lan vao lai: 61% ngan hon 60 phut (ngan nhat 20 giay, trung vi 2660 giay); sau chuoi LO (66 lan): 68% ngan hon - tre khong thuc thi ke ca sau ...
- NUT AN (lenh that co co che ma .set khong co tham so nao dieu khien): Chi them lenh khi mo nen moi (luoi_theo_nen_moi).
- CHUA GAP (lich su chua toi dieu kien cua tham so): InpMaxBuyOrders, InpMaxSellOrders, InpOrders2NewMultiplier3, InpNewMultiplier3, InpOrders2NewMultiplier4, InpNewMultiplier4 (+4).
- Luu y: lenh tester dat tren luoi 10 giay: moi so do thoi gian (tre, nhip) chi chinh xac den khoang do

## Luu y
- lenh tester dat tren luoi 10 giay: moi so do thoi gian (tre, nhip) chi chinh xac den khoang do

## Mau thuan: tac gia noi X, lenh that cho thay Y

| Tham so | Tac gia khai | Do tin | Lenh that cho thay |
|---|---|---|---|
| InpMinuteDelayAfterClose | 60 | cao | 1196 lan vao lai: 61% ngan hon 60 phut (ngan nhat 20 giay, trung vi 2660 giay); sau chuoi LO (66 lan): 68% ngan hon - tre khong thuc thi ke ca sau chuoi lo |
| InpPlus | 0.01 | vua | tac gia khai cong them 0.01 lot moi lenh nhung lot do duoc KHONG cong them - cong thuc khong cong khop 3114/3114 lenh (co the chi bat o che do CoeffMode khac) |
| InpDistanceMulti | 1.2 | thap | tac gia khai he so 1.2 nhung buoc do duoc phang theo bac tren 14 bac du mau - khong thay tac dung (co the he so chi bat o che do khac, vd DCAMODE, hoac chi sau tang cuoi: bac sau nhat do duoc 15 chua qua tang cuoi (lenh 20)) |
| InpMinuteDelayNewDay | 120 | vua | cua so tre 120 phut = 4 o 30 phut dau ngay may chu (00:00-02:00): van co 56 / 1198 chuoi bat dau trong cua so (4.7%), du tinh tre tu 00:00 - cach doc yeu nhat; dau ngay o day: nghi san tu 00:00 den 01:00; tre co the chi ap dung sau mot dieu kien khac chua gap |

## Nut an: co che co trong lenh that, khong tham so nao dieu khien

- **Chi them lenh khi mo nen moi** (luoi_theo_nen_moi, do tin cao): 469 cap lenh them lien nhau khong cap nao cung nen 15 phut (ky vong ngau nhien 178 cap, thuc te 0): toi da MOT lenh them moi nen 15 phut; cap (lenh vao, lenh them dau) van cung nen 437 / 575 cap (ky vong 431): luat kh.... Tham so lien quan: khong co tham so nao noi toi

## Cong thuc do duoc (khoi co che dang chay)

- **Buoc theo bac (doi buoc o moc so lenh)** (luoi_buoc_theo_bac, do tin cao): do duoc [buoc_bac_1=10.3 pip, buoc_bac_2=15.4 pip, moc_doi_buoc_1=4 lenh]; .set khop [InpDistance0=10.0, InpOrders2Distance1=5, InpDistance1=15.0, InpDistance2=15.0, InpDistance3=15.0]
- **Chi them lenh khi mo nen moi** (luoi_theo_nen_moi, do tin cao): do duoc [toi_da_lenh_moi_nen_phut=15 phut]; .set khop [khong co]
- **Mo lenh doi ung sau N lenh (hedge khi sau)** (lenh_doi_ung_sau_n_lenh, do tin vua): do duoc [so_lenh_kich_hoat=16 lenh, ty_lot_so_voi_lenh_chu_moi=1 ty_le]; .set khop [InpUseHedging=true, InpOrders2Hedging=15, InpUseLotsDCA2Hedging=true]
- **He so lot doi theo bac** (lot_nhan_theo_bac, do tin vua): do duoc [he_so_bac_1=1 he_so, he_so_bac_2=1.2 he_so, moc_doi_he_so_1=10 lenh, he_so_bac_3=1.1 he_so, moc_doi_he_so_2=20 lenh]; .set khop [InpUseChangeMultiplier=true, InpOrders2NewMultiplier=10, InpNewMultiplier=1.2, InpOrders2NewMultiplier2=20, InpNewMultiplier2=1.1]
- **TP ca chuoi tu gia trung binh** (tp_chuoi_tu_gia_tb, do tin cao): do duoc [tp_pip_chuoi_1=10.1 pip, tp_pip_chuoi_2-4=20 pip, tp_pip_chuoi_5-9=20.1 pip, tp_pip_chuoi_10+=20.2 pip]; .set khop [InpTP=10.0, InpTPDCA=20.0]

Lot: 3114/3114 lenh dung cong thuc lot_n = lam_tron(0.01 x M(n)^(n-1), 0.01) (chuoi sau nhat 25 lenh).

## Tung tham so (theo thu tu trong .set)

| Tham so | Khai | Ket qua | Do tin | Do duoc | Ly do |
|---|---|---|---|---|---|
| InpCombine | false | KHONG_LIEN_QUAN | vua |  | ma so dinh danh / hien thi tren bieu do: khong anh huong lenh |
| InpMagicID | 9196 | KHONG_LIEN_QUAN | vua |  | ma so dinh danh / hien thi tren bieu do: khong anh huong lenh |
| InpLots | 0.01 | KHOP | cao | 0.01 lot | lot lenh dau cua chuoi do duoc 0.01 = khai |
| InpTP | 10.0 | KHOP | cao | 10.1 pip | bien chot loi do duoc 10.1 pip, khai 10 pip (lech +0.10 pip = khoang 1 tick: lenh dong boi EA dong CHAM mot tick) |
| InpSL | 0.0 | TAT | vua |  | khai 0 = khong dat SL co dinh |
| InpTypeBuySell | 0 | KHONG_RO | thap | 0.504 ty le mua | khai TypeBuySell = 0; lich su: mua 50% / ban 50% (hai bo cung khai 0 co the cho hai hanh vi khac nhau: tham so nay khong quyet dinh mot minh) |
| InpShowTP | false | KHONG_LIEN_QUAN | vua |  | ma so dinh danh / hien thi tren bieu do: khong anh huong lenh |
| InpDelayAfterSLTP | 0 | TAT | vua |  | khai 0: khong co tre sau khi dong theo SL / TP |
| InpMaxBuyOrders | 100 | CHUA_GAP | thap | 25 lenh | chuoi mua sau nhat 25 lenh chua cham tran 100 |
| InpMaxSellOrders | 100 | CHUA_GAP | thap | 17 lenh | chuoi ban sau nhat 17 lenh chua cham tran 100 |
| InpMaxSpread | 6.0 | KHONG_DO_DUOC | vua |  | spread luc vao lenh khong nam trong bang deals (can chuoi spread / tick); lenh bi chan vi spread khong hien ra trong lich su |
| InpMaxLots | 2.3 | KHONG_RO | thap | 2.21 lot | tong lot mo dinh 2.21 lot (gom lenh bao hiem) gan tran 2.3 lot (96%): lenh dang ke tiep cua chuoi sau nhat co the da bi tran chan; lich su khong cho thay lenh bi tu choi |
| InpMaxLots2NewCycle | false | KHONG_DO_DUOC | thap |  | can biet luc cham tran de thay hanh vi |
| InpDelayOrder | 2 | KHONG_DO_DUOC | vua |  | khai 2 giay nhung bao cao tester dat lenh tren luoi 10 giay: khoang vai giay khong do duoc |
| InpUseLottery | false | TAT | vua |  | khai tat |
| InpMultiplierLottery | 2.0 | TAT | vua |  | cong UseLottery tat: khong co hieu luc |
| InpMinuteDelayAfterClose | 60 | MAU_THUAN | cao | 2660 giay | 1196 lan vao lai: 61% ngan hon 60 phut (ngan nhat 20 giay, trung vi 2660 giay); sau chuoi LO (66 lan): 68% ngan hon - tre khong thuc thi ke ca sau chuoi lo |
| InpMoneySL2Reset | 0.0 | TAT | vua |  | khai 0: khong dat lai lot / TP khi cat lo |
| InpUseDCA | true | KHOP | cao | 25 lenh | lich su co chuoi them lenh toi 25 lenh |
| InpUseFilterDCA | false | TAT | vua |  | khai tat loc DCA |
| InpOrders2EnableFilterDCA | 25 | TAT | vua |  | cong UseFilterDCA tat: khong co hieu luc |
| InpDCAMODE | 1 | KHONG_RO | thap |  | che do tinh he so / DCA (1): cong thuc lot va buoc do duoc da khop nen ban khong thay che do khac biet; chua tach duoc |
| InpCoeffMode | 0 | KHONG_RO | thap |  | che do tinh he so / DCA (0): cong thuc lot va buoc do duoc da khop nen ban khong thay che do khac biet; chua tach duoc |
| InpMultiplier | 1.0 | KHOP | cao | 1 he_so | he so 1,0 (lot phang): lot tung lenh o bac 2-10: 1809/1809 khop cong thuc lam_tron(lot_dau x 1^(n-1)) |
| InpUseChangeMultiplier | true | KHOP | cao |  | doi he so theo bac: lot tung lenh o bac 11-20: 102/102 khop cong thuc lam_tron(lot_dau x 1.2^(n-1)) |
| InpOrders2NewMultiplier | 10 | KHOP | cao | 11 lenh | moc doi he so 1 -> 1.2 (lenh dau cua tang la lenh thu 11): lot tung lenh o bac 11-20: 102/102 khop cong thuc lam_tron(lot_dau x 1.2^(n-1)) |
| InpNewMultiplier | 1.2 | KHOP | cao | 1.2 he_so | lot tung lenh o bac 11-20: 102/102 khop cong thuc lam_tron(lot_dau x 1.2^(n-1)) |
| InpOrders2NewMultiplier2 | 20 | KHOP | thap | 21 lenh | moc doi he so 1.2 -> 1.1 (lenh dau cua tang la lenh thu 21): lot tung lenh o bac 21-30: 5/5 khop cong thuc lam_tron(lot_dau x 1.1^(n-1)) |
| InpNewMultiplier2 | 1.1 | KHOP | thap | 1.1 he_so | lot tung lenh o bac 21-30: 5/5 khop cong thuc lam_tron(lot_dau x 1.1^(n-1)) |
| InpOrders2NewMultiplier3 | 30 | CHUA_GAP | thap |  | moc doi he so 1.1 -> 1.05 (lenh dau cua tang la lenh thu 31): khong co lenh nao o bac 31-40 |
| InpNewMultiplier3 | 1.05 | CHUA_GAP | thap |  | khong co lenh nao o bac 31-40 |
| InpOrders2NewMultiplier4 | 40 | CHUA_GAP | thap |  | moc doi he so 1.05 -> 1.06 (lenh dau cua tang la lenh thu 41): khong co lenh nao o bac 41-50 |
| InpNewMultiplier4 | 1.06 | CHUA_GAP | thap |  | khong co lenh nao o bac 41-50 |
| InpOrders2NewMultiplier5 | 50 | CHUA_GAP | thap |  | moc doi he so 1.06 -> 1.03 (lenh dau cua tang la lenh thu 51): khong co lenh nao o bac 51+ |
| InpNewMultiplier5 | 1.03 | CHUA_GAP | thap |  | khong co lenh nao o bac 51+ |
| InpPlus | 0.01 | MAU_THUAN | vua | 0 lot | tac gia khai cong them 0.01 lot moi lenh nhung lot do duoc KHONG cong them - cong thuc khong cong khop 3114/3114 lenh (co the chi bat o che do CoeffMode khac) |
| InpDistanceMulti | 1.2 | MAU_THUAN | thap |  | tac gia khai he so 1.2 nhung buoc do duoc phang theo bac tren 14 bac du mau - khong thay tac dung (co the he so chi bat o che do khac, vd DCAMODE, hoac chi sau tang cuoi: bac sau nhat do duoc 15 chua qua tang cuoi (lenh 20)) |
| InpDistance0 | 10.0 | KHOP | cao | 10.3 pip | buoc do duoc (p10 theo bac, bac 2-4, 1320 lenh them) trung vi 10.3 pip, khai 10 pip: 100% lenh trong cua so |
| InpSingleTP | 0.0 | TAT | thap |  | khai 0 (thuong = khong dung TP rieng cho lenh don) |
| InpTPDCA | 20.0 | KHOP | cao | 20.1 pip | moi nhom do sau (10+, 2-4, 5-9) dong o 20.2/20/20.1 pip, khai 20 pip |
| InpOrders2Distance1 | 5 | KHOP | cao | 5 lenh | buoc bac 4 = 10.2 pip (khai truoc moc 10), bac 5 = 15.5 pip (khai sau moc 15); moc doi o lenh thu 5 |
| InpDistance1 | 15.0 | KHOP | cao | 15.4 pip | buoc do duoc (p10 theo bac, bac 5-9, 450 lenh them) trung vi 15.4 pip, khai 15 pip: 100% lenh trong cua so |
| InpOrders2Distance2 | 10 | KHONG_DO_DUOC | vua |  | khoang cach hai ben moc bang nhau (15 va 15 pip): doi tang khong de lai dau vet trong buoc |
| InpDistance2 | 15.0 | KHOP | cao | 15.8 pip | buoc do duoc (p10 theo bac, bac 10-14, 118 lenh them) trung vi 15.8 pip, khai 15 pip: 100% lenh trong cua so |
| InpOrders2Distance3 | 15 | KHONG_DO_DUOC | vua |  | khoang cach hai ben moc bang nhau (15 va 15 pip): doi tang khong de lai dau vet trong buoc |
| InpDistance3 | 15.0 | KHOP | thap | 15.6 pip | buoc do duoc (p10 theo bac, bac 15, 9 lenh them) trung vi 15.6 pip, khai 15 pip: 100% lenh trong cua so |
| InpOrders2Distance4 | 20 | KHONG_DO_DUOC | vua |  | khoang cach hai ben moc bang nhau (15 va 15 pip): doi tang khong de lai dau vet trong buoc |
| InpDistance4 | 15.0 | CHUA_GAP | thap |  | InpDistance4 = 15 pip ap dung tu lenh thu 20; chua co bac nao (>= 8 chuoi) o do sau do de do |
| InpUseChangeTPDCA | false | TAT | vua |  | khai tat doi TP khi lo |
| InpPerLoss2ChangeTP | -20.0 | TAT | vua |  | cong UseChangeTPDCA tat: tham so nay khong co hieu luc |
| InpMoneyLoss2ChangeTP | -12000.0 | TAT | vua |  | cong UseChangeTPDCA tat: tham so nay khong co hieu luc |
| InpTPDCAChange | 10.0 | TAT | vua |  | cong UseChangeTPDCA tat: tham so nay khong co hieu luc |
| InpUseOpenOpp | false | TAT | vua |  | khai tat mo lenh doi chieu (OpenOpp) |
| InpOrders2OpenOpp | 12 | TAT | vua |  | cong UseOpenOpp tat: khong co hieu luc |
| InpPerLotsOpp | 15.0 | TAT | vua |  | cong UseOpenOpp tat: khong co hieu luc |
| InpLotsOpp | 0.01 | TAT | vua |  | cong UseOpenOpp tat: khong co hieu luc |
| InpUseSniper | true | KHONG_RO | thap |  | cong bat; lich su chua du de biet tia co chay hay khong |
| InpSniperAll | false | TAT | vua |  | cong InpUseAllSniper tat: khong co hieu luc |
| InpOrders2StartSniper | 20 | CHUA_GAP | thap |  | tia bat dau tu lenh 20 nhung lich su chi kiem duoc tia den do sau 15 lenh (it chuoi dai de thu) |
| InpOrders2StartSniper2 | 15 | KHONG_RO | thap |  | moc 15 nam trong do sau kiem duoc (15 lenh) nhung chua ket luan duoc tia co chay hay khong |
| InpFirstOrdersSniper | 2 | KHONG_DO_DUOC | thap |  | nhom tia chua thay hoat dong trong lich su nen khong do duoc tung tham so |
| InpLastOrdersSniper | 0 | KHONG_DO_DUOC | thap |  | nhom tia chua thay hoat dong trong lich su nen khong do duoc tung tham so |
| InpPercentSniper | 10.0 | KHONG_DO_DUOC | thap |  | nhom tia chua thay hoat dong trong lich su nen khong do duoc tung tham so |
| InpMoneySniperFull | 10.0 | KHONG_DO_DUOC | thap |  | nhom tia chua thay hoat dong trong lich su nen khong do duoc tung tham so |
| InpTPSniper | 5.0 | KHONG_DO_DUOC | thap |  | nhom tia chua thay hoat dong trong lich su nen khong do duoc tung tham so |
| InpMuliSniper | 1.15 | KHONG_DO_DUOC | thap |  | nhom tia chua thay hoat dong trong lich su nen khong do duoc tung tham so |
| InpUseSniperPartial | false | TAT | vua |  | khai tat |
| InpPerLoss2SniperPartial | -30.0 | TAT | vua |  | cong InpUseSniperPartial tat: khong co hieu luc |
| InpOrders2StartSniperPartial | 20 | TAT | vua |  | cong InpUseSniperPartial tat: khong co hieu luc |
| InpPerLotsSniperPartial | 30.0 | TAT | vua |  | cong InpUseSniperPartial tat: khong co hieu luc |
| InpPerSniperPartial | 20.0 | TAT | vua |  | cong InpUseSniperPartial tat: khong co hieu luc |
| InpMoneySniperPartial | 10.0 | TAT | vua |  | cong InpUseSniperPartial tat: khong co hieu luc |
| InpLastOrdersSniperPartial | 3 | TAT | vua |  | cong InpUseSniperPartial tat: khong co hieu luc |
| InpUseAllSniper | false | TAT | vua |  | khai tat |
| InpUseMagicFilter | false | KHONG_LIEN_QUAN | vua |  | ma so dinh danh / hien thi tren bieu do: khong anh huong lenh |
| InpAllOrders2ActiveAllSniper | 25 | TAT | vua |  | cong InpUseAllSniper tat: khong co hieu luc |
| InpFirstOrders2AllSniper | 1 | TAT | vua |  | cong InpUseAllSniper tat: khong co hieu luc |
| InpLastOrders2AllSniper | 5 | TAT | vua |  | cong InpUseAllSniper tat: khong co hieu luc |
| InpMoneyProfitAllSniper | 10.0 | TAT | vua |  | cong InpUseAllSniper tat: khong co hieu luc |
| InpUseAllProfitToday2AllSniper | false | TAT | vua |  | cong InpUseAllSniper tat: khong co hieu luc |
| InpUsePartialSniper | false | TAT | vua |  | cong InpUseSniperPartial tat: khong co hieu luc |
| InpMinLotsSniper | 0.1 | KHONG_DO_DUOC | thap |  | nhom tia chua thay hoat dong trong lich su nen khong do duoc tung tham so |
| InpMinPerLotsSniper | 35.0 | TAT | vua |  | cong InpUseSniperPartial tat: khong co hieu luc |
| InpUseBalanceLot | false | TAT | vua |  | khai tat UseBalanceLot |
| InpAddBLLMode | 1 | TAT | thap |  | suy tu ten: nhom BLL phu thuoc UseBalanceLot (dang tat) |
| InpDiffLots2EnableBLL | 6.0 | TAT | thap |  | suy tu ten: nhom BLL phu thuoc UseBalanceLot (dang tat) |
| InpDiffLots2DisableBLL | 2.0 | TAT | thap |  | suy tu ten: nhom BLL phu thuoc UseBalanceLot (dang tat) |
| InpAddLotsBLL | 0.1 | TAT | thap |  | suy tu ten: nhom BLL phu thuoc UseBalanceLot (dang tat) |
| InpDelayTimeBLL | 120 | KHONG_DO_DUOC | thap |  | tre cua che do BLL: chua co phep do rieng |
| InpUseHedgingZone | false | TAT | vua |  | khai tat vung bao hiem |
| InpOrders2HedgingZone | 20 | TAT | vua |  | cong UseHedgingZone tat: khong co hieu luc |
| InpHedgingZoneMultiplier | 2.0 | TAT | vua |  | cong UseHedgingZone tat: khong co hieu luc |
| InpZoneHedgingPips | 35.0 | TAT | vua |  | cong UseHedgingZone tat: khong co hieu luc |
| InpMoneyTPALLHedgingZone | 1000.0 | TAT | vua |  | cong UseHedgingZone tat: khong co hieu luc |
| InpPipsTPAllHedgingZone | 50.0 | TAT | vua |  | cong UseHedgingZone tat: khong co hieu luc |
| InpOrders2EnableMoneyTPAllHZ | 26 | TAT | vua |  | cong UseHedgingZone tat: khong co hieu luc |
| InpNewMoneyTPAllHZ | 100.0 | TAT | vua |  | cong UseHedgingZone tat: khong co hieu luc |
| InpMaxLotsHedgingZone | 20.0 | TAT | vua |  | cong UseHedgingZone tat: khong co hieu luc |
| InpUseHedging | true | KHOP | vua |  | lich su co lenh bao hiem (hedge) di kem chuoi |
| InpOrders2Hedging | 15 | KHOP | vua | 16 lenh | lenh bao hiem dau tien xuat hien khi chuoi co 16 lenh; khai Orders2Hedging = 15 (lech +1: EA bat hedge khi so lenh VUOT moc) |
| InpPerLoss2Hedging | -25.0 | KHONG_DO_DUOC | thap |  | gia tri nay (nguong lo / ty le / TP khi co hedge) can duong gia hoac chi hien khi co du chuoi bao hiem; lich su co 19 chuoi |
| InpUseLotsDCA2Hedging | true | KHOP | vua | 1 ty le | lot lenh bao hiem / lot lenh them moi nhat cua chuoi = 1 |
| InpPerLotsHedging | 20.0 | BI_CHE | vua |  | UseLotsDCA2Hedging bat: lot bao hiem theo lenh DCA, bo qua phan tram lot |
| InpTPHedging | 0.0 | KHONG_DO_DUOC | thap |  | gia tri nay (nguong lo / ty le / TP khi co hedge) can duong gia hoac chi hien khi co du chuoi bao hiem; lich su co 19 chuoi |
| InpTPAllWhenHedging | 150.0 | KHONG_DO_DUOC | thap |  | gia tri nay (nguong lo / ty le / TP khi co hedge) can duong gia hoac chi hien khi co du chuoi bao hiem; lich su co 19 chuoi |
| InpStopSniperWhenHedging | true | KHONG_DO_DUOC | thap |  | chi co tac dung khi vua co tia vua co hedge cung luc; lich su chua co chuoi nhu vay du nhieu |
| InpResetLots | 0.1 | TAT | vua |  | MoneySL2Reset = 0: nhom dat lai khong co hieu luc |
| InpMultiplierReset | 1.2 | TAT | vua |  | MoneySL2Reset = 0: nhom dat lai khong co hieu luc |
| InpTPReset | 5.0 | TAT | vua |  | MoneySL2Reset = 0: nhom dat lai khong co hieu luc |
| MoneyTPAllAcc | 0.0 | TAT | vua |  | khai 0 = khong dung muc tieu / cat lo nay |
| MoneySLAllAcc | 0.0 | TAT | vua |  | khai 0 = khong dung muc tieu / cat lo nay |
| MoneyTPAll | 0.0 | TAT | vua |  | khai 0 = khong dung muc tieu / cat lo nay |
| MoneySLAll | 0.0 | TAT | vua |  | khai 0 = khong dung muc tieu / cat lo nay |
| MoneyTPBuy | 0.0 | TAT | vua |  | khai 0 = khong dung muc tieu / cat lo nay |
| MoneySLBuy | 0.0 | TAT | vua |  | khai 0 = khong dung muc tieu / cat lo nay |
| MoneyTPSell | 0.0 | TAT | vua |  | khai 0 = khong dung muc tieu / cat lo nay |
| MoneySLSell | 0.0 | TAT | vua |  | khai 0 = khong dung muc tieu / cat lo nay |
| MoneyTPAllDCASignalStep | 0.0 | TAT | vua |  | khai 0 = khong dung muc tieu / cat lo nay |
| InpDailyMoneyTPTarget | 0.0 | TAT | vua |  | khai 0 = khong dung muc tieu / cat lo nay |
| InpDailyMoneySLTarget | 0.0 | TAT | vua |  | khai 0 = khong dung muc tieu / cat lo nay |
| InpDailyPerTPTarget | 0.0 | TAT | vua |  | khai 0 = khong dung muc tieu / cat lo nay |
| InpDailyPerSLTarget | 0.0 | TAT | vua |  | khai 0 = khong dung muc tieu / cat lo nay |
| InpMinuteDelayNewDay | 120 | MAU_THUAN | vua | 0.0467 ty le | cua so tre 120 phut = 4 o 30 phut dau ngay may chu (00:00-02:00): van co 56 / 1198 chuoi bat dau trong cua so (4.7%), du tinh tre tu 00:00 - cach doc yeu nhat; dau ngay o day: nghi san tu 00:00 den 01:00; tre co the chi ap dung sau mot d... |
| InpUseTrailing | true | KHONG_RO | thap |  | co cum dong gan muc khoa loi nhung khong chac day la trailing |
| InpTrailingStart | 15.0 | KHONG_DO_DUOC | vua |  | muc lai de BAT trailing khong de lai dau vet trong lenh da dong (chuoi dong o muc khoa >= khoa dau); can duong gia de thay |
| InpTrailingStep | 5.0 | KHONG_DO_DUOC | thap |  | lich su khong cho do duoc buoc nhich cua khoa loi |
| InpInitialSLTrailing | 2.0 | KHOP | thap | 2 pip | muc khoa loi do duoc 2 pip, khai 2 pip (khoi trailing chi o muc khong_ro: coi la gia thuyet) |
| InpShowLineStartTrailing | false | KHONG_LIEN_QUAN | vua |  | ma so dinh danh / hien thi tren bieu do: khong anh huong lenh |
| InpUseTradingTime | false | TAT | vua |  | khai tat loc gio: khong co gio nao bi cam |
| InpUseTime1 | true | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpStartTime1 | 08:30 | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpEndTime1 | 12:30 | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpUseTime2 | true | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpStartTime2 | 14:30 | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpEndTime2 | 18:30 | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpUseTime3 | true | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpStartTime3 | 20:30 | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpEndTime3 | 23:30 | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpUseTime4 | true | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpStartTime4 | 02:30 | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpEndTime4 | 05:30 | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpDCAOutTime | true | TAT | thap |  | suy tu ten: tuy chon cho phep DCA ngoai gio; cong loc gio tat nen khong co hieu luc |
| InpIndiMode | 7 | KHONG_DO_DUOC | vua |  | che do chi bao vao lenh (7): khong the biet chi bao nao dang chay neu khong co duong gia cung thoi gian |
| InpTFSignal | 2 | KHOP | cao | 2 phut | chuoi chi bat dau o dau nen 2 phut (100% so chuoi); ngau nhien se trung 17% |
| InpUseEMAFilter | true | KHONG_DO_DUOC | thap |  | loc EMA can duong gia de kiem; lich su lenh khong cho thay |
| InpTFEMAFilter | 10 | KHONG_DO_DUOC | thap |  | gia tri rieng cua loc EMA can duong gia de kiem |
| InpEMA1 | 34 | KHONG_DO_DUOC | thap |  | gia tri rieng cua loc EMA can duong gia de kiem |
| InpEMA2 | 89 | KHONG_DO_DUOC | thap |  | gia tri rieng cua loc EMA can duong gia de kiem |
| InpMaxDistacneEMA | 500.0 | KHONG_DO_DUOC | thap |  | gia tri rieng cua loc EMA can duong gia de kiem |
| InpUseMACDFilter | false | TAT | thap |  | khai tat loc MACD (khong the kiem nguoc lai: bo loc chi chan lenh, khong de lai dau vet) |
| InpTFMACDFilter | 0 | TAT | thap |  | cong loc MACD tat: tham so khong co hieu luc |
| InpFastEMAMACD | 30 | TAT | thap |  | cong loc MACD tat: tham so khong co hieu luc |
| InpSlowEMAMACD | 50 | TAT | thap |  | cong loc MACD tat: tham so khong co hieu luc |
| InpSMAMACD | 5 | TAT | thap |  | cong loc MACD tat: tham so khong co hieu luc |
| InpAppliedPriceMACD | 6 | TAT | thap |  | cong loc MACD tat: tham so khong co hieu luc |
| InpCCIPeriod | 14 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpCCIPrice | 1 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpOverBoughtCCI | 100.0 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpOverSoldCCI | -100.0 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpStochKPeriod | 5 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpStochDPeriod | 3 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpStochSlowing | 3 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpStochMAMethod | 0 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpStochPrice | 0 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpOverBoughtStoch | 80.0 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpOverSoldStoch | 20.0 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpMomentumPeriod | 14 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpMomentumPrice | 1 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpOverBoughtMomen | 100.45 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpOverSoldMomen | 99.45 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpPeriodsIndiST | 21 | KHONG_DO_DUOC | thap |  | tham so chi bao SuperTrend cua tin hieu vao lenh (khong phai khoang cach luoi); can duong gia de kiem |
| InpMultiplierIndiST | 3.0 | KHONG_DO_DUOC | thap |  | tham so chi bao SuperTrend cua tin hieu vao lenh (khong phai khoang cach luoi); can duong gia de kiem |
| InpUTBOT_Nbr_Periods | 10 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpUTBOT_Multiplier | 1.0 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpUTBOT_ShowArrows | true | KHONG_LIEN_QUAN | vua |  | ma so dinh danh / hien thi tren bieu do: khong anh huong lenh |
| InpUTBOT_ArrowDist | 20 | KHONG_LIEN_QUAN | vua |  | ma so dinh danh / hien thi tren bieu do: khong anh huong lenh |
| InpNameIndiOutside | Nhap ten indi | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpBuyBuffer | 0 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpSellBuffer | 1 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpBarSignal | 1 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpRSIPeriod | 14 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpRSIApplyPrice | 1 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpRSIOverBought | 75.0 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpRSIOverSold | 25.0 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpIchiTenkan | 9 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpIchiKijun | 26 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpIchiSenkou | 52 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpBBPeriod | 20 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpBBDeviations | 2.0 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpBBPrice | 1 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |

Dem: KHOP 20, MAU_THUAN 4, TAT 82, BI_CHE 1, CHUA_GAP 10, KHONG_DO_DUOC 59, KHONG_RO 7, KHONG_LIEN_QUAN 7
