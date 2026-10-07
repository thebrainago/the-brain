# Doi chieu bo .set 'CanCuBo_set' voi lenh that

- Bo .set 'CanCuBo_set' (172 tham so) doi chieu voi 1962 lenh that cua GOLD.i#: KHOP 10, MAU THUAN 2, TAT 100, BI CHE 8, CHUA GAP 7, KHONG DO DUOC 34, KHONG RO 4, khac 7.
- Don vi khoang cach: 1 don vi trong .set = 1 pip cua san (da kiem bang nhieu cap so duoc).
- Khop chac (do tin cao): InpLots, InpTP, InpUseDCA, InpMultiplier, InpOrders2Distance4, InpDistance4 (+4).
- Lot: 1962/1962 lenh dung cong thuc lot_n = lam_tron(0.01 x M(n)^(n-1), 0.01).
- MAU THUAN (tac gia noi X, lenh that cho thay Y): InpMinuteDelayAfterClose (khai 60, tin cay thap), InpMinuteDelayNewDay (khai 120, tin cay cao). Vi du: 1290 lan vao lai: 96% ngan hon 60 phut (ngan nhat 20 giay, trung vi 440 giay); chi co 0 chuoi lo nen khong thu duoc cach hieu 'tre chi sau chuoi lo...
- NUT AN (lenh that co co che ma .set khong co tham so nao dieu khien): Chi mot chieu (chi Buy hoac chi Sell) (mot_chieu), Chi them lenh khi mo nen moi (luoi_theo_nen_moi).
- CHUA GAP (lich su chua toi dieu kien cua tham so): InpMaxBuyOrders, InpMaxSellOrders, InpMaxLots, InpMaxLots2NewCycle, InpUseFilterDCA, InpOrders2EnableFilterDCA (+1).
- Luu y: lenh tester dat tren luoi 10 giay: moi so do thoi gian (tre, nhip) chi chinh xac den khoang do

## Luu y
- lenh tester dat tren luoi 10 giay: moi so do thoi gian (tre, nhip) chi chinh xac den khoang do

## Mau thuan: tac gia noi X, lenh that cho thay Y

| Tham so | Tac gia khai | Do tin | Lenh that cho thay |
|---|---|---|---|
| InpMinuteDelayAfterClose | 60 | thap | 1290 lan vao lai: 96% ngan hon 60 phut (ngan nhat 20 giay, trung vi 440 giay); chi co 0 chuoi lo nen khong thu duoc cach hieu 'tre chi sau chuoi lo' (neu dung cach hieu do thi khong the bac bo) |
| InpMinuteDelayNewDay | 120 | cao | cua so tre 120 phut = 4 o 30 phut dau ngay may chu (00:00-02:00): van co 65 / 1291 chuoi bat dau trong cua so (5.0%), du tinh tre tu 00:00 - cach doc yeu nhat; dau ngay o day: nghi san tu 00:00 den 01:00; tre co the chi ap dung sau mot dieu kien khac chua gap |

## Nut an: co che co trong lenh that, khong tham so nao dieu khien

- **Chi mot chieu (chi Buy hoac chi Sell)** (mot_chieu, do tin cao): 100% chuoi cung mot chieu (mua). Tham so lien quan: InpTypeBuySell=0 (KHONG_RO)
- **Chi them lenh khi mo nen moi** (luoi_theo_nen_moi, do tin thap): 22 cap lenh them lien nhau khong cap nao cung nen 15 phut (ky vong ngau nhien 8 cap, thuc te 0): toi da MOT lenh them moi nen 15 phut; cap (lenh vao, lenh them dau) van cung nen 10 / 16 cap (ky vong 7): luat khong tin.... Tham so lien quan: khong co tham so nao noi toi

## Cong thuc do duoc (khoi co che dang chay)

- **Chi mot chieu (chi Buy hoac chi Sell)** (mot_chieu, do tin cao): do duoc [chieu=mua chieu]; .set khop [khong co]
- **Luoi gian cach deu** (luoi_gian_cach_deu, do tin cao): do duoc [buoc_pip=101 pip]; .set khop [InpOrders2Distance4=1, InpDistance4=100.0]
- **Chi them lenh khi mo nen moi** (luoi_theo_nen_moi, do tin thap): do duoc [toi_da_lenh_moi_nen_phut=15 phut]; .set khop [khong co]
- **Lot nhan theo he so** (lot_nhan, do tin cao): do duoc [he_so_lot=1.05 he_so]; .set khop [InpMultiplier=1.05]
- **TP rieng tung lenh** (tp_tung_lenh, do tin cao): do duoc [tp_pip=100 pip]; .set khop [InpTP=100.0]
- **Trailing stop ca chuoi** (trailing_stop_chuoi, do tin cao): do duoc [trailing_khoa_dau_pip=15 pip, trailing_buoc_pip=2 pip]; .set khop [InpUseTrailing=true, InpTrailingStep=2.0, InpInitialSLTrailing=15.0]

Lot: 1962/1962 lenh dung cong thuc lot_n = lam_tron(0.01 x M(n)^(n-1), 0.01) (chuoi sau nhat 19 lenh).

## Tung tham so (theo thu tu trong .set)

| Tham so | Khai | Ket qua | Do tin | Do duoc | Ly do |
|---|---|---|---|---|---|
| InpCombine | false | KHONG_LIEN_QUAN | vua |  | ma so dinh danh / hien thi tren bieu do: khong anh huong lenh |
| InpMagicID | 712 | KHONG_LIEN_QUAN | vua |  | ma so dinh danh / hien thi tren bieu do: khong anh huong lenh |
| InpLots | 0.01 | KHOP | cao | 0.01 lot | lot lenh dau cua chuoi do duoc 0.01 = khai |
| InpTP | 100.0 | KHOP | cao | 100 pip | bien chot loi do duoc 100 pip, khai 100 pip (lech +0.00 pip = khoang 1 tick: lenh dong boi EA dong CHAM mot tick) |
| InpSL | 0.0 | TAT | vua |  | khai 0 = khong dat SL co dinh |
| InpTypeBuySell | 0 | KHONG_RO | thap | 1 ty le mua | khai TypeBuySell = 0; lich su: mua 100% / ban 0% (hai bo cung khai 0 co the cho hai hanh vi khac nhau: tham so nay khong quyet dinh mot minh) |
| InpShowTP | true | KHONG_LIEN_QUAN | vua |  | ma so dinh danh / hien thi tren bieu do: khong anh huong lenh |
| InpDelayAfterSLTP | 0 | TAT | vua |  | khai 0: khong co tre sau khi dong theo SL / TP |
| InpMaxBuyOrders | 100 | CHUA_GAP | thap | 19 lenh | chuoi mua sau nhat 19 lenh chua cham tran 100 |
| InpMaxSellOrders | 100 | CHUA_GAP | vua |  | khong co lenh ban nao trong lich su |
| InpMaxSpread | 300.0 | KHONG_DO_DUOC | vua |  | spread luc vao lenh khong nam trong bang deals (can chuoi spread / tick); lenh bi chan vi spread khong hien ra trong lich su |
| InpMaxLots | 2.3 | CHUA_GAP | thap | 0.29 lot | tong lot mo dinh 0.29 lot chua toi tran 2.3 lot (13%) |
| InpMaxLots2NewCycle | true | CHUA_GAP | thap |  | tran lot chua bao gio cham nen che do 'sang chu ky moi' chua duoc dung |
| InpDelayOrder | 2 | KHONG_DO_DUOC | vua |  | khai 2 giay nhung bao cao tester dat lenh tren luoi 10 giay: khoang vai giay khong do duoc |
| InpUseLottery | false | TAT | vua |  | khai tat |
| InpMultiplierLottery | 2.0 | TAT | vua |  | cong UseLottery tat: khong co hieu luc |
| InpMinuteDelayAfterClose | 60 | MAU_THUAN | thap | 440 giay | 1290 lan vao lai: 96% ngan hon 60 phut (ngan nhat 20 giay, trung vi 440 giay); chi co 0 chuoi lo nen khong thu duoc cach hieu 'tre chi sau chuoi lo' (neu dung cach hieu do thi khong the bac bo) |
| InpMoneySL2Reset | 0.0 | TAT | vua |  | khai 0: khong dat lai lot / TP khi cat lo |
| InpUseDCA | true | KHOP | cao | 19 lenh | lich su co chuoi them lenh toi 19 lenh |
| InpUseFilterDCA | true | CHUA_GAP | thap |  | loc bat tu lenh 25 nhung chuoi sau nhat 19 lenh |
| InpOrders2EnableFilterDCA | 25 | CHUA_GAP | thap |  | chuoi sau nhat 19 lenh chua toi moc 25 |
| InpDCAMODE | 1 | KHONG_RO | thap |  | che do tinh he so / DCA (1): cong thuc lot va buoc do duoc da khop nen ban khong thay che do khac biet; chua tach duoc |
| InpCoeffMode | 0 | KHONG_RO | thap |  | che do tinh he so / DCA (0): cong thuc lot va buoc do duoc da khop nen ban khong thay che do khac biet; chua tach duoc |
| InpMultiplier | 1.05 | KHOP | cao | 1.05 he_so | lot tung lenh o bac 2+: 671/671 khop cong thuc lam_tron(lot_dau x 1.05^(n-1)) |
| InpUseChangeMultiplier | false | TAT | vua |  | tat doi he so: moi lenh dung mot he so 1.05 |
| InpOrders2NewMultiplier | 10 | TAT | vua |  | cong UseChangeMultiplier tat: moc doi he so khong co hieu luc |
| InpNewMultiplier | 1.0 | TAT | vua |  | cong UseChangeMultiplier tat: he so moi khong co hieu luc |
| InpOrders2NewMultiplier2 | 20 | TAT | vua |  | cong UseChangeMultiplier tat: moc doi he so khong co hieu luc |
| InpNewMultiplier2 | 1.0 | TAT | vua |  | cong UseChangeMultiplier tat: he so moi khong co hieu luc |
| InpOrders2NewMultiplier3 | 30 | TAT | vua |  | cong UseChangeMultiplier tat: moc doi he so khong co hieu luc |
| InpNewMultiplier3 | 1.0 | TAT | vua |  | cong UseChangeMultiplier tat: he so moi khong co hieu luc |
| InpOrders2NewMultiplier4 | 40 | TAT | vua |  | cong UseChangeMultiplier tat: moc doi he so khong co hieu luc |
| InpNewMultiplier4 | 1.0 | TAT | vua |  | cong UseChangeMultiplier tat: he so moi khong co hieu luc |
| InpOrders2NewMultiplier5 | 50 | TAT | vua |  | cong UseChangeMultiplier tat: moc doi he so khong co hieu luc |
| InpNewMultiplier5 | 1.0 | TAT | vua |  | cong UseChangeMultiplier tat: he so moi khong co hieu luc |
| InpPlus | 0.0 | TAT | vua |  | khai 0: khong cong them lot moi lenh |
| InpDistanceMulti | 1.0 | TAT | vua |  | he so 1,0 = khong gian buoc (trung tinh) |
| InpDistance0 | 10.0 | BI_CHE | vua |  | moc nho nhat Orders2Distance = 1 (<= 2 + lech): tang co hieu luc ngay tu lenh 2 nen Distance0 khong bao gio duoc dung |
| InpSingleTP | 0.0 | TAT | thap |  | khai 0 (thuong = khong dung TP rieng cho lenh don) |
| InpTPDCA | 200.0 | CHUA_GAP | thap |  | khong co chuoi >= 2 lenh nao dong o muc TP co dinh (chuoi dai deu dong bang co che khac: khoa loi / EA) |
| InpOrders2Distance1 | 1 | BI_CHE | vua |  | moc Orders2Distance1 = 1 trung hoac nho hon moc tang khac: tang 4 (so thu tu lon hon, thang) co hieu luc tu cung lenh nen tang nay khong bao gio duoc dung |
| InpDistance1 | 60.0 | BI_CHE | vua |  | moc Orders2Distance1 = 1 trung hoac nho hon moc tang khac: tang 4 (so thu tu lon hon, thang) co hieu luc tu cung lenh nen tang nay khong bao gio duoc dung |
| InpOrders2Distance2 | 1 | BI_CHE | vua |  | moc Orders2Distance2 = 1 trung hoac nho hon moc tang khac: tang 4 (so thu tu lon hon, thang) co hieu luc tu cung lenh nen tang nay khong bao gio duoc dung |
| InpDistance2 | 70.0 | BI_CHE | vua |  | moc Orders2Distance2 = 1 trung hoac nho hon moc tang khac: tang 4 (so thu tu lon hon, thang) co hieu luc tu cung lenh nen tang nay khong bao gio duoc dung |
| InpOrders2Distance3 | 1 | BI_CHE | vua |  | moc Orders2Distance3 = 1 trung hoac nho hon moc tang khac: tang 4 (so thu tu lon hon, thang) co hieu luc tu cung lenh nen tang nay khong bao gio duoc dung |
| InpDistance3 | 80.0 | BI_CHE | vua |  | moc Orders2Distance3 = 1 trung hoac nho hon moc tang khac: tang 4 (so thu tu lon hon, thang) co hieu luc tu cung lenh nen tang nay khong bao gio duoc dung |
| InpOrders2Distance4 | 1 | KHOP | cao |  | moc 1 <= 2: tang 4 co hieu luc ngay tu lenh 2 (khong co tang truoc de so sanh); buoc do duoc (p10 theo bac, bac 2-11, 637 lenh them) trung vi 101 pip, khai 100 pip: 100% lenh trong cua so |
| InpDistance4 | 100.0 | KHOP | cao | 101 pip | buoc do duoc (p10 theo bac, bac 2-11, 637 lenh them) trung vi 101 pip, khai 100 pip: 100% lenh trong cua so |
| InpUseChangeTPDCA | false | TAT | vua |  | khai tat doi TP khi lo |
| InpPerLoss2ChangeTP | -20.0 | TAT | vua |  | cong UseChangeTPDCA tat: tham so nay khong co hieu luc |
| InpMoneyLoss2ChangeTP | -12000.0 | TAT | vua |  | cong UseChangeTPDCA tat: tham so nay khong co hieu luc |
| InpTPDCAChange | 10.0 | TAT | vua |  | cong UseChangeTPDCA tat: tham so nay khong co hieu luc |
| InpUseOpenOpp | false | TAT | vua |  | khai tat mo lenh doi chieu (OpenOpp) |
| InpOrders2OpenOpp | 12 | TAT | vua |  | cong UseOpenOpp tat: khong co hieu luc |
| InpPerLotsOpp | 15.0 | TAT | vua |  | cong UseOpenOpp tat: khong co hieu luc |
| InpLotsOpp | 0.01 | TAT | vua |  | cong UseOpenOpp tat: khong co hieu luc |
| InpUseSniper | false | TAT | vua |  | khai tat |
| InpOrders2StartSniper | 5 | TAT | vua |  | cong InpUseSniper tat: khong co hieu luc |
| InpOrders2StartSniper2 | 7 | TAT | vua |  | cong InpUseSniper tat: khong co hieu luc |
| InpFirstOrdersSniper | 1 | TAT | vua |  | cong InpUseSniper tat: khong co hieu luc |
| InpLastOrdersSniper | 0 | TAT | vua |  | cong InpUseSniper tat: khong co hieu luc |
| InpPercentSniper | 5.0 | TAT | vua |  | cong InpUseSniper tat: khong co hieu luc |
| InpMoneySniperFull | 5.0 | TAT | vua |  | cong InpUseSniper tat: khong co hieu luc |
| InpTPSniper | 5.0 | TAT | vua |  | cong InpUseSniper tat: khong co hieu luc |
| InpMuliSniper | 1.0 | TAT | vua |  | cong InpUseSniper tat: khong co hieu luc |
| InpUseSniperPartial | false | TAT | vua |  | khai tat |
| InpPerLoss2SniperPartial | -30.0 | TAT | vua |  | cong InpUseSniperPartial tat: khong co hieu luc |
| InpOrders2StartSniperPartial | 20 | TAT | vua |  | cong InpUseSniperPartial tat: khong co hieu luc |
| InpPerLotsSniperPartial | 30.0 | TAT | vua |  | cong InpUseSniperPartial tat: khong co hieu luc |
| InpPerSniperPartial | 20.0 | TAT | vua |  | cong InpUseSniperPartial tat: khong co hieu luc |
| InpMoneySniperPartial | 10.0 | TAT | vua |  | cong InpUseSniperPartial tat: khong co hieu luc |
| InpLastOrdersSniperPartial | 3 | TAT | vua |  | cong InpUseSniperPartial tat: khong co hieu luc |
| InpUseAllSniper | false | TAT | vua |  | khai tat |
| InpUseMagicFilter | true | KHONG_LIEN_QUAN | vua |  | ma so dinh danh / hien thi tren bieu do: khong anh huong lenh |
| InpAllOrders2ActiveAllSniper | 55 | TAT | vua |  | cong InpUseAllSniper tat: khong co hieu luc |
| InpFirstOrders2AllSniper | 1 | TAT | vua |  | cong InpUseAllSniper tat: khong co hieu luc |
| InpLastOrders2AllSniper | 10 | TAT | vua |  | cong InpUseAllSniper tat: khong co hieu luc |
| InpMoneyProfitAllSniper | 10.0 | TAT | vua |  | cong InpUseAllSniper tat: khong co hieu luc |
| InpUseAllProfitToday2AllSniper | false | TAT | vua |  | cong InpUseAllSniper tat: khong co hieu luc |
| InpUseHedgingZone | false | TAT | vua |  | khai tat vung bao hiem |
| InpOrders2HedgingZone | 20 | TAT | vua |  | cong UseHedgingZone tat: khong co hieu luc |
| InpHedgingZoneMultiplier | 2.0 | TAT | vua |  | khong cong bao hiem nao bat: tham so khong co hieu luc |
| InpZoneHedgingPips | 35.0 | TAT | vua |  | khong cong bao hiem nao bat: tham so khong co hieu luc |
| InpMoneyTPALLHedgingZone | 1000.0 | TAT | vua |  | khong cong bao hiem nao bat: tham so khong co hieu luc |
| InpPipsTPAllHedgingZone | 50.0 | TAT | vua |  | khong cong bao hiem nao bat: tham so khong co hieu luc |
| InpMaxLotsHedgingZone | 20.0 | TAT | vua |  | khong cong bao hiem nao bat: tham so khong co hieu luc |
| InpUseHedging | false | TAT | vua |  | khai tat hedge |
| InpOrders2Hedging | 15 | TAT | vua |  | cong UseHedging tat: khong co hieu luc |
| InpPerLoss2Hedging | -25.0 | TAT | vua |  | khong cong bao hiem nao bat: tham so khong co hieu luc |
| InpUseLotsDCA2Hedging | true | TAT | vua |  | cong UseHedging tat: khong co hieu luc |
| InpPerLotsHedging | 20.0 | BI_CHE | vua |  | UseLotsDCA2Hedging bat: lot bao hiem theo lenh DCA, bo qua phan tram lot |
| InpTPHedging | 0.0 | TAT | vua |  | khong cong bao hiem nao bat: tham so khong co hieu luc |
| InpTPAllWhenHedging | 150.0 | TAT | vua |  | khong cong bao hiem nao bat: tham so khong co hieu luc |
| InpStopSniperWhenHedging | true | TAT | vua |  | cong tia hoac cong hedge tat: khong co hieu luc |
| InpResetLots | 0.01 | TAT | vua |  | MoneySL2Reset = 0: nhom dat lai khong co hieu luc |
| InpMultiplierReset | 1.0 | TAT | vua |  | MoneySL2Reset = 0: nhom dat lai khong co hieu luc |
| InpTPReset | 5.0 | TAT | vua |  | MoneySL2Reset = 0: nhom dat lai khong co hieu luc |
| MoneyTPAllAcc | 10.0 | KHONG_RO | thap | 10 tien | khai 10 tien trung voi muc TP 100 pip cua lenh don o lot 0.01 (= 10 tien): hai co che trung nhau, khong tach duoc |
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
| InpMinuteDelayNewDay | 120 | MAU_THUAN | cao | 0.0503 ty le | cua so tre 120 phut = 4 o 30 phut dau ngay may chu (00:00-02:00): van co 65 / 1291 chuoi bat dau trong cua so (5.0%), du tinh tre tu 00:00 - cach doc yeu nhat; dau ngay o day: nghi san tu 00:00 den 01:00; tre co the chi ap dung sau mot d... |
| InpUseTrailing | true | KHOP | cao |  | chuoi dong theo khoa loi truot (trailing) o muc co dinh |
| InpTrailingStart | 30.0 | KHONG_DO_DUOC | vua |  | muc lai de BAT trailing khong de lai dau vet trong lenh da dong (chuoi dong o muc khoa >= khoa dau); can duong gia de thay |
| InpTrailingStep | 2.0 | KHOP | cao | 2 pip | buoc nhich khoa loi do duoc 2 pip, khai 2 pip |
| InpInitialSLTrailing | 15.0 | KHOP | cao | 15 pip | muc khoa loi do duoc 15 pip, khai 15 pip |
| InpShowLineStartTrailing | true | KHONG_LIEN_QUAN | vua |  | ma so dinh danh / hien thi tren bieu do: khong anh huong lenh |
| InpUseTradingTime | false | TAT | vua |  | khai tat loc gio: khong co gio nao bi cam |
| InpUseTime1 | true | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpStartTime1 | 05:30 | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpEndTime1 | 13:00 | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpUseTime2 | true | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpStartTime2 | 14:00 | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpEndTime2 | 16:00 | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpUseTime3 | true | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpStartTime3 | 21:00 | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpEndTime3 | 23:00 | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpUseTime4 | true | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpStartTime4 | 01:00 | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpEndTime4 | 03:30 | TAT | vua |  | cong UseTradingTime tat: cua so gio khong co hieu luc |
| InpDCAOutTime | true | TAT | thap |  | suy tu ten: tuy chon cho phep DCA ngoai gio; cong loc gio tat nen khong co hieu luc |
| InpIndiMode | 8 | KHONG_DO_DUOC | vua |  | che do chi bao vao lenh (8): khong the biet chi bao nao dang chay neu khong co duong gia cung thoi gian |
| InpTFSignal | 1 | KHOP | cao | 1 phut | chuoi chi bat dau o dau nen 1 phut (100% so chuoi); ngau nhien se trung 33% |
| InpUseEMAFilter | false | TAT | thap |  | khai tat loc EMA (khong the kiem nguoc lai: bo loc chi chan lenh, khong de lai dau vet) |
| InpTFEMAFilter | 0 | TAT | thap |  | cong loc EMA tat: tham so khong co hieu luc |
| InpEMA1 | 34 | TAT | thap |  | cong loc EMA tat: tham so khong co hieu luc |
| InpEMA2 | 89 | TAT | thap |  | cong loc EMA tat: tham so khong co hieu luc |
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
| InpStochKPeriod | 7 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpStochDPeriod | 1 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpStochSlowing | 2 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpStochMAMethod | 0 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpStochPrice | 0 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpOverBoughtStoch | 100.0 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
| InpOverSoldStoch | 12.0 | KHONG_DO_DUOC | vua |  | tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao) |
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

Dem: KHOP 10, MAU_THUAN 2, TAT 100, BI_CHE 8, CHUA_GAP 7, KHONG_DO_DUOC 34, KHONG_RO 4, KHONG_LIEN_QUAN 7
