# Bang tai san - tong hop 5 ho so (D1)

Sinh boi `nhan/ho_so_tai_san.sinh_bang_md()`. KHONG do them gi moi - chi gop lai 5 module da chay san. Doc cot `do_phu` va `(tin)` truoc khi tin bat ky con so nao trong hang.

## Tom tat do phu / do tin (159 ma, tinh lai luc sinh bang)

- Mua vu: 72 dong (ma|phep) co `dat=true`; 32 trong so co spread THAT (DO/SAN) de xet chi phi; chi **22** vua dat=true vua song qua CHINH spread cua no - tren ma: CHFHUF, EURCZK, EURMXN, EURUSD, EURZAR, GBPHUF, GBPMXN, GBPSEK, GBPUSD, GBPZAR, SP500, US500M, USDJPY, XAUUSD, XM_USDCAD, YH_DAX, YH_GBPUSD, YH_NASDAQ. (0 dong M3 bi HA ve CHUA_DO_DUOC vi khong xac dinh chac chan duoc nhan thu - xem `thu_da_sua`, sua 13/09/2026; khong con dong nao 'dat=true' mang canh bao lech nhan ma khong bi chan.)
- Tuong quan D1: 45/158 ma co doi tac AM+ON DINH de ghep chan nguoc; 128/158 co doi tac DUONG manh+on dinh (trung rui ro voi mot ma khac); 59/158 gan doc lap voi ca kho (r tuyet doi trung vi < 0,05)
- Song H4: 27/159 ma co zigzag do duoc (con lai CHUA_DO_DUOC vi du lieu goc chi co D1); 26/159 du tin cay (n>=200 cap day/hoi)
- Do phu ca 5 nguon cung luc: 157/159 ma

| ma | do_phu | tinh_cach(hurst) | ATR%/bar | spread bps(tin) | phi/nam mua-ban% | so nam | mua vu | song day/hoi%(n,tin) | ghep tot nhat |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 5/5 | XU_HUONG(0.60) | 0.686 | 1.63(SAN) | 2.46/-0.45 | 55.6 | M1:10bps(OK) | 1.45/0.88(n=2325,DU) | - |
| GBPUSD | 5/5 | TRUNG_TINH(0.57) | 0.750 | 1.56(SAN) | 0.99/1.10 | 33.2 | M3:6bps(OK) | 1.41/0.85(n=2319,DU) | - |
| US500M | 5/5 | HOI_QUY(0.55) | 1.255 | 0.94(SAN) | 5.76/-0.67 | 6.6 | M3:30bps(OK) | 2.43/1.41(n=557,DU) | - |
| USDJPY | 5/5 | XU_HUONG(0.60) | 0.637 | 1.33(SAN) | -0.48/6.79 | 55.6 | M3:4bps(OK) | 1.56/0.96(n=2286,DU) | - |
| XAUUSD | 5/5 | TRUNG_TINH(0.60) | 1.319 | 0.69(SAN) | 7.06/-0.91 | 22.1 | M3:14bps(OK) | 2.53/1.52(n=1932,DU) | - |
| CHFHUF | 4/5 | HOI_QUY(0.56) | 0.862 | 13.13(SAN) | 0.00/0.00 | 9.1 | M3:18bps(OK) | - | EURCHF(r=-0.63) |
| EURCZK | 4/5 | HOI_QUY(0.54) | 0.372 | 5.60(SAN) | 5.81/0.00 | 11.6 | M3:18bps(OK) | - | - |
| EURMXN | 4/5 | HOI_QUY(0.53) | 1.010 | 5.65(SAN) | 4.90/0.00 | 9.4 | M3:24bps(OK) | - | - |
| EURZAR | 4/5 | TRUNG_TINH(0.57) | 1.233 | 10.16(SAN) | 8.41/-0.75 | 10.7 | M3:24bps(OK) | - | - |
| GBPHUF | 4/5 | HOI_QUY(0.53) | 0.916 | 12.03(SAN) | 22.60/17.19 | 9.1 | M3:21bps(OK) | - | EURGBP(r=-0.62) |
| GBPMXN | 4/5 | HOI_QUY(0.58) | 1.015 | 5.65(SAN) | 3.70/0.00 | 8.7 | M3:32bps(OK) | - | - |
| GBPSEK | 4/5 | HOI_QUY(0.56) | 0.844 | 10.36(SAN) | 0.71/4.85 | 11.6 | M3:13bps(OK) | - | EURGBP(r=-0.68) |
| GBPZAR | 4/5 | HOI_QUY(0.55) | 1.301 | 20.77(SAN) | 3.24/0.00 | 11.0 | M3:21bps(OK) | - | - |
| SP500 | 4/5 | TRUNG_TINH(0.58) | 0.549 | 0.94(SAN) | 5.76/-0.67 | 34.0 | M1:14bps(OK); M2:9bps(OK); M3:14bps(OK) | - | - |
| XM_USDCAD | 4/5 | TRUNG_TINH(0.58) | 0.675 | 1.43(SAN) | -0.26/2.60 | 20.6 | M2:5bps(OK) | - | XM_AUDUSD(r=-0.69) |
| YH_DAX | 4/5 | TRUNG_TINH(0.58) | 1.307 | 0.95(SAN) | 4.79/0.32 | 38.6 | M1:23bps(OK); M2:8bps(OK) | - | - |
| YH_GBPUSD | 4/5 | TRUNG_TINH(0.59) | 0.796 | 1.56(SAN) | 0.99/1.10 | 18.6 | M3:7bps(OK) | - | - |
| YH_NASDAQ | 4/5 | XU_HUONG(0.63) | 0.957 | 0.94(SAN) | 5.81/-0.66 | 55.5 | M2:7bps(OK); M3:18bps(OK) | - | - |
| EURCAD | 5/5 | TRUNG_TINH(0.57) | 0.769 | 1.70(SAN) | 1.57/1.44 | 25.3 | khong | 1.20/0.76(n=1124,DU) | - |
| EURNZD | 5/5 | TRUNG_TINH(0.58) | 0.871 | 2.26(SAN) | 2.16/1.17 | 26.3 | khong | 1.49/0.90(n=1030,DU) | NZDCHF(r=-0.79) |
| GBPCAD | 5/5 | TRUNG_TINH(0.57) | 0.770 | 2.48(SAN) | -0.26/3.20 | 25.1 | khong | 1.28/0.80(n=1110,DU) | - |
| NZDCAD | 5/5 | TRUNG_TINH(0.59) | 0.867 | 4.36(SAN) | 1.35/1.80 | 25.2 | khong | 1.49/0.92(n=1086,DU) | EURNZD(r=-0.59) |
| US500CASH | 5/5 | HOI_QUY(0.55) | 1.057 | 2.54(SAN) | 5.76/-0.67 | 15.0 | khong | 2.21/1.25(n=862,DU) | - |
| XAUAUDM | 5/5 | TRUNG_TINH(0.57) | 1.092 | 124.43(SAN) | 5.31/0.00 | 3.9 | khong | 2.38/1.46(n=351,DU) | - |
| XAUEURM | 5/5 | TRUNG_TINH(0.56) | 1.088 | 148.32(SAN) | 8.15/-0.94 | 3.9 | khong | 2.41/1.43(n=344,DU) | - |
| XAUGBPM | 5/5 | TRUNG_TINH(0.56) | 1.112 | 173.60(SAN) | 4.46/0.00 | 3.9 | khong | 2.53/1.52(n=343,DU) | - |
| XAUUSDM | 5/5 | TRUNG_TINH(0.60) | 1.070 | 12.03(SAN) | 7.06/-0.91 | 12.5 | khong | 2.23/1.38(n=832,DU) | - |
| XM_AUS200CASH | 5/5 | HOI_QUY(0.56) | 1.080 | 3.76(SAN) | 7.64/-1.41 | 12.3 | khong | 2.08/1.24(n=819,DU) | - |
| XM_EU50CASH | 5/5 | HOI_QUY(0.57) | 1.379 | 6.38(SAN) | 5.31/0.34 | 15.8 | khong | 2.77/1.63(n=714,DU) | - |
| XM_FRA40CASH | 5/5 | HOI_QUY(0.56) | 1.303 | 3.42(SAN) | 5.43/0.34 | 15.2 | khong | 3.00/1.75(n=615,DU) | - |
| XM_GER40CASH | 5/5 | TRUNG_TINH(0.57) | 1.345 | 1.22(SAN) | 4.79/0.32 | 15.1 | khong | 2.45/1.50(n=876,DU) | - |
| XM_JP225CASH | 5/5 | TRUNG_TINH(0.58) | 1.566 | 0.04(SAN) | 2.52/0.83 | 16.0 | khong | 3.15/1.90(n=870,DU) | - |
| XM_UK100CASH | 5/5 | HOI_QUY(0.54) | 1.082 | 2.12(SAN) | 6.85/-0.74 | 15.1 | khong | 1.98/1.24(n=875,DU) | - |
| XM_US100CASH | 5/5 | HOI_QUY(0.56) | 1.386 | 0.94(SAN) | 5.81/-0.66 | 14.9 | khong | 3.30/1.81(n=114,MONG) | - |
| XM_US30CASH | 5/5 | TRUNG_TINH(0.57) | 1.037 | 1.12(SAN) | 5.80/-0.66 | 15.1 | khong | 2.06/1.23(n=897,DU) | - |
| XM_US500CASH | 5/5 | HOI_QUY(0.55) | 1.055 | 2.53(SAN) | 5.76/-0.67 | 15.1 | khong | 2.20/1.24(n=877,DU) | - |
| AUDCAD | 5/5 | HOI_QUY(0.56) | 0.755 | 1.00(KHAI) | -0.26/3.85 | 33.2 | khong | 1.31/0.83(n=1099,DU) | - |
| AUDCHF | 5/5 | HOI_QUY(0.57) | 0.959 | 1.00(KHAI) | -2.72/6.05 | 33.2 | khong | 1.60/1.02(n=1103,DU) | CHFNOK(r=-0.65) |
| AUDJPY | 4/5 | HOI_QUY(0.59) | 1.112 | 2.82(SAN) | -1.29/5.40 | 33.2 | khong | - | - |
| AUDNZD | 5/5 | HOI_QUY(0.58) | 0.639 | 1.00(KHAI) | 0.34/3.84 | 33.3 | M3:6bps(?) | 1.02/0.62(n=1038,DU) | - |
| CADCHF | 4/5 | HOI_QUY(0.56) | 0.890 | 6.98(SAN) | -0.95/4.01 | 33.2 | khong | - | CHFSGD(r=-0.75) |
| CADJPY | 4/5 | HOI_QUY(0.58) | 0.923 | 3.53(SAN) | 0.34/3.63 | 25.0 | khong | - | - |
| DE40 | 4/5 | TRUNG_TINH(0.58) | 1.334 | 0.95(SAN) | 4.79/0.32 | 14.0 | khong | - | - |
| EURAUD | 4/5 | HOI_QUY(0.58) | 0.769 | 1.68(SAN) | 3.53/-0.40 | 24.8 | khong | - | XM_AUDUSD(r=-0.70) |
| EURDKK | 4/5 | HOI_QUY(0.47) | 0.040 | 5.73(SAN) | 2.33/3.24 | 10.7 | M3:1bps(kem) | - | - |
| EURGBP | 5/5 | HOI_QUY(0.55) | 0.668 | 1.00(KHAI) | 2.84/-0.19 | 33.2 | khong | 1.07/0.67(n=1149,DU) | GBPDKK(r=-0.98) |
| EURHKD | 4/5 | TRUNG_TINH(0.58) | 0.699 | 6.29(SAN) | 2.70/2.81 | 18.9 | khong | - | - |
| EURHUF | 4/5 | HOI_QUY(0.55) | 0.624 | 14.17(SAN) | 7.86/0.95 | 11.6 | M3:13bps(kem) | - | - |
| EURNOK | 4/5 | HOI_QUY(0.56) | 0.765 | 12.13(SAN) | 4.72/0.91 | 13.3 | khong | - | NOKJPY(r=-0.76) |
| EURPLN | 4/5 | HOI_QUY(0.56) | 0.527 | 17.68(SAN) | 4.39/1.25 | 11.6 | M3:10bps(kem) | - | - |
| EURSEK | 4/5 | HOI_QUY(0.54) | 0.600 | 9.16(SAN) | 2.22/3.38 | 13.4 | M3:7bps(kem) | - | SEKJPY(r=-0.62) |
| EURTRY | 4/5 | XU_HUONG(0.60) | 1.042 | 16.06(SAN) | 42.87/-3.53 | 16.2 | M3:14bps(kem) | - | - |
| GBPAUD | 4/5 | TRUNG_TINH(0.58) | 0.833 | 1.52(SAN) | 2.10/1.04 | 25.2 | khong | - | - |
| GBPNOK | 4/5 | HOI_QUY(0.55) | 0.947 | 13.37(SAN) | 3.28/2.60 | 11.6 | M3:13bps(kem) | - | NOKJPY(r=-0.68) |
| GBPNZD | 4/5 | TRUNG_TINH(0.58) | 0.901 | 2.56(SAN) | 0.39/3.22 | 26.6 | khong | - | NZDCAD(r=-0.58) |
| GBPPLN | 4/5 | HOI_QUY(0.55) | 0.815 | 98.52(SAN) | 0.39/0.41 | 11.6 | M3:12bps(kem) | - | EURGBP(r=-0.73) |
| GBPSGD | 4/5 | HOI_QUY(0.56) | 0.620 | 19.45(SAN) | 0.01/6.45 | 13.4 | M3:12bps(kem) | - | EURGBP(r=-0.68) |
| NZDCHF | 4/5 | HOI_QUY(0.56) | 0.946 | 5.39(SAN) | -1.13/4.21 | 25.7 | khong | - | EURNZD(r=-0.79) |
| NZDJPY | 4/5 | TRUNG_TINH(0.58) | 1.042 | 3.65(SAN) | 0.58/4.58 | 25.8 | khong | - | - |
| NZDSGD | 4/5 | HOI_QUY(0.57) | 0.860 | 38.81(SAN) | 1.85/4.50 | 18.9 | M3:9bps(kem) | - | USDCAD(r=-0.51) |
| SGDJPY | 4/5 | HOI_QUY(0.56) | 0.770 | 18.93(SAN) | 2.75/2.75 | 18.9 | M3:12bps(kem) | - | - |
| USDCHF | 4/5 | TRUNG_TINH(0.58) | 0.782 | 1.94(SAN) | -1.76/6.07 | 24.9 | khong | - | - |
| XM_AUDUSD | 4/5 | TRUNG_TINH(0.59) | 0.928 | 2.12(SAN) | 0.73/1.85 | 20.6 | khong | - | EURAUD(r=-0.70) |
| XM_EURUSD | 4/5 | TRUNG_TINH(0.58) | 0.704 | 1.35(SAN) | 2.46/-0.45 | 20.6 | khong | - | XM_USDCAD(r=-0.51) |
| XM_GBPUSD | 4/5 | TRUNG_TINH(0.58) | 0.732 | 1.34(SAN) | 0.99/1.10 | 20.6 | khong | - | XM_USDCAD(r=-0.50) |
| XM_GOLD | 4/5 | TRUNG_TINH(0.59) | 1.341 | 2.25(SAN) | 7.06/-0.91 | 20.6 | khong | - | - |
| XM_SILVER | 4/5 | TRUNG_TINH(0.60) | 2.428 | 17.52(SAN) | 11.58/-1.74 | 20.6 | khong | - | - |
| XM_US2000CASH | 4/5 | TRUNG_TINH(0.62) | 1.791 | 3.20(SAN) | 6.42/-0.24 | 8.9 | khong | - | - |
| XM_USDCHF | 4/5 | TRUNG_TINH(0.59) | 0.745 | 1.98(SAN) | -1.76/6.07 | 20.6 | khong | - | - |
| XM_XAUEUR | 4/5 | HOI_QUY(0.56) | 1.111 | 2.10(SAN) | 8.15/-0.94 | 8.9 | khong | - | - |
| YH_EURUSD | 4/5 | HOI_QUY(0.56) | 0.756 | 1.63(SAN) | 2.46/-0.45 | 18.6 | khong | - | - |
| YH_USDJPY | 4/5 | TRUNG_TINH(0.58) | 0.786 | 1.33(SAN) | -0.48/6.79 | 19.6 | khong | - | - |
| YH_VANG | 4/5 | TRUNG_TINH(0.58) | 1.017 | 0.69(SAN) | 7.06/-0.91 | 25.9 | khong | - | - |
| AUDHKD | 4/5 | - | 0.932 | 1.00(KHAI) | 1.50/1.50 | 7.1 | khong | - | USDCAD(r=-0.75) |
| AUDHUF | 4/5 | HOI_QUY(0.55) | 0.963 | 1.00(KHAI) | 0.00/0.00 | 8.9 | M3:29bps(?) | - | - |
| AUDNOK | 4/5 | HOI_QUY(0.55) | 0.977 | 1.00(KHAI) | 0.45/0.69 | 6.9 | khong | - | NOKJPY(r=-0.60) |
| AUDPLN | 4/5 | TRUNG_TINH(0.59) | 1.033 | 1.00(KHAI) | 0.00/3.88 | 6.9 | M3:34bps(?) | - | - |
| AUDSEK | 4/5 | TRUNG_TINH(0.59) | 0.810 | 1.00(KHAI) | 0.00/3.03 | 6.9 | khong | - | - |
| AUDSGD | 4/5 | TRUNG_TINH(0.60) | 0.686 | 1.00(KHAI) | 0.00/3.37 | 6.9 | M3:11bps(?) | - | USDCAD(r=-0.63) |
| AUDUSD | 4/5 | HOI_QUY(0.58) | 0.937 | 1.00(KHAI) | 0.73/1.85 | 33.2 | khong | - | - |
| AUDZAR | 4/5 | HOI_QUY(0.53) | 1.234 | 1.00(KHAI) | 6.17/0.00 | 8.8 | khong | - | - |
| CADMXN | 4/5 | TRUNG_TINH(0.58) | 0.775 | 1.00(KHAI) | 6.69/0.00 | 12.3 | khong | - | - |
| CADSGD | 4/5 | - | 0.463 | 1.00(KHAI) | 1.50/1.50 | 3.4 | khong | - | USDCAD(r=-0.52) |
| CHFDKK | 4/5 | HOI_QUY(0.56) | 0.462 | 1.00(KHAI) | 2.57/0.00 | 6.9 | khong | - | EURCHF(r=-0.98) |
| CHFJPY | 4/5 | TRUNG_TINH(0.58) | 0.905 | 1.00(KHAI) | 2.99/1.10 | 34.4 | khong | - | - |
| CHFMXN | 4/5 | TRUNG_TINH(0.58) | 0.991 | 1.00(KHAI) | 7.78/0.00 | 7.7 | khong | - | - |
| CHFNOK | 4/5 | TRUNG_TINH(0.58) | 1.004 | 1.00(KHAI) | 4.95/0.00 | 6.9 | khong | - | NOKJPY(r=-0.79) |
| CHFPLN | 4/5 | TRUNG_TINH(0.59) | 0.805 | 1.00(KHAI) | 4.42/0.00 | 6.9 | khong | - | EURCHF(r=-0.70) |
| CHFSEK | 4/5 | - | 0.801 | 1.00(KHAI) | 2.45/0.00 | 3.4 | M3:17bps(?) | - | SEKJPY(r=-0.60) |
| CHFSGD | 4/5 | HOI_QUY(0.56) | 0.594 | 1.00(KHAI) | 5.13/1.07 | 6.9 | khong | - | CADCHF(r=-0.75) |
| DKKSEK | 4/5 | - | 0.671 | 1.00(KHAI) | 1.50/1.50 | 3.4 | khong | - | SEKJPY(r=-0.55) |
| EURCHF | 4/5 | HOI_QUY(0.56) | 0.452 | 1.00(KHAI) | -0.38/4.46 | 33.2 | khong | - | CHFDKK(r=-0.98) |
| EURCNH | 4/5 | - | 0.507 | 1.00(KHAI) | 1.50/1.50 | 3.4 | khong | - | - |
| EURILS | 4/5 | HOI_QUY(0.56) | 0.894 | 1.00(KHAI) | 1.50/1.50 | 13.9 | M3:28bps(?) | - | - |
| EURJPY | 4/5 | TRUNG_TINH(0.57) | 0.869 | 1.00(KHAI) | 1.12/4.03 | 33.2 | khong | - | - |
| EURRUB | 4/5 | TRUNG_TINH(0.60) | 1.170 | 1.00(KHAI) | 1.50/1.50 | 11.6 | khong | - | - |
| EURRUR | 4/5 | TRUNG_TINH(0.62) | 1.015 | 1.00(KHAI) | 1.50/1.50 | 18.9 | khong | - | - |
| EURSGD | 4/5 | HOI_QUY(0.51) | 0.474 | 1.00(KHAI) | 1.69/5.17 | 6.9 | M3:6bps(?) | - | - |
| GBPCHF | 4/5 | HOI_QUY(0.58) | 0.766 | 1.00(KHAI) | -1.79/5.93 | 33.3 | khong | - | CHFSGD(r=-0.58) |
| GBPCZK | 4/5 | - | 0.586 | 1.00(KHAI) | 5.95/1.46 | 3.4 | M3:15bps(?) | - | EURGBP(r=-0.76) |
| GBPDKK | 4/5 | HOI_QUY(0.54) | 0.553 | 1.00(KHAI) | 0.85/4.73 | 6.9 | M3:11bps(?) | - | EURGBP(r=-0.98) |
| GBPHKD | 4/5 | - | 0.632 | 1.00(KHAI) | 1.50/1.50 | 3.4 | khong | - | USDCAD(r=-0.56) |
| GBPJPY | 4/5 | TRUNG_TINH(0.58) | 0.943 | 1.00(KHAI) | -0.52/6.82 | 33.3 | khong | - | - |
| GBPTRY | 4/5 | - | 1.151 | 1.00(KHAI) | 6.03/1.36 | 3.4 | M3:35bps(?) | - | - |
| HKDJPY | 4/5 | TRUNG_TINH(0.59) | 0.686 | 1.00(KHAI) | 0.00/2.34 | 6.8 | M3:13bps(?) | - | SGDHKD(r=-0.62) |
| MXNJPY | 4/5 | TRUNG_TINH(0.59) | 1.155 | 1.00(KHAI) | 0.00/81.73 | 5.8 | M3:33bps(?) | - | - |
| NOKJPY | 4/5 | TRUNG_TINH(0.58) | 1.216 | 1.00(KHAI) | 0.00/28.44 | 6.9 | M3:19bps(?) | - | CHFNOK(r=-0.79) |
| NOKSEK | 4/5 | TRUNG_TINH(0.61) | 0.962 | 1.00(KHAI) | 0.00/15.69 | 6.9 | M3:15bps(?) | - | EURNOK(r=-0.74) |
| NZDDKK | 4/5 | - | 0.665 | 1.00(KHAI) | 0.00/2.69 | 3.4 | khong | - | - |
| NZDHUF | 4/5 | TRUNG_TINH(0.57) | 1.066 | 1.00(KHAI) | 23.65/17.74 | 8.9 | M3:26bps(?) | - | - |
| NZDMXN | 4/5 | TRUNG_TINH(0.60) | 0.980 | 1.00(KHAI) | 8.12/0.00 | 7.7 | M3:26bps(?) | - | - |
| NZDSEK | 4/5 | - | 0.865 | 1.00(KHAI) | 0.00/2.86 | 3.4 | khong | - | - |
| NZDUSD | 4/5 | TRUNG_TINH(0.59) | 0.984 | 1.00(KHAI) | 2.38/0.00 | 32.5 | khong | - | - |
| PLNJPY | 4/5 | TRUNG_TINH(0.60) | 1.037 | 1.00(KHAI) | 0.00/10.15 | 6.9 | M3:23bps(?) | - | - |
| SEKJPY | 4/5 | HOI_QUY(0.55) | 1.085 | 1.00(KHAI) | 0.00/15.89 | 6.9 | M3:17bps(?) | - | EURSEK(r=-0.62) |
| SEKNOK | 4/5 | HOI_QUY(0.55) | 1.284 | 1.00(KHAI) | 1.50/1.50 | 5.5 | M3:58bps(?) | - | - |
| SGDHKD | 4/5 | - | 0.426 | 1.00(KHAI) | 2.48/0.00 | 3.4 | khong | - | USDCAD(r=-0.64) |
| TRYJPY | 4/5 | XU_HUONG(0.63) | 1.475 | 1.00(KHAI) | 0.00/0.00 | 6.9 | M3:36bps(?) | - | - |
| TS_BTC | 4/5 | XU_HUONG(0.61) | 3.389 | 1.00(KHAI) | 1.50/1.50 | 11.9 | khong | - | - |
| TS_ETH | 4/5 | XU_HUONG(0.61) | 4.637 | 1.00(KHAI) | 1.50/1.50 | 8.7 | khong | - | - |
| TS_GLD | 4/5 | TRUNG_TINH(0.59) | 1.090 | 1.00(KHAI) | 1.50/1.50 | 20.0 | khong | - | - |
| TS_QQQ | 4/5 | HOI_QUY(0.56) | 1.397 | 1.00(KHAI) | 5.50/-0.50 | 20.0 | khong | - | - |
| TS_SPY | 4/5 | HOI_QUY(0.55) | 1.078 | 1.00(KHAI) | 5.50/-0.50 | 20.0 | khong | - | - |
| TS_VNM | 4/5 | XU_HUONG(0.60) | 1.527 | 1.00(KHAI) | 1.50/1.50 | 17.0 | M3:25bps(?) | - | - |
| USDARS | 4/5 | XU_HUONG(0.61) | 0.319 | 1.00(KHAI) | 0.00/0.00 | 9.0 | khong | - | - |
| USDCAD | 4/5 | TRUNG_TINH(0.58) | 0.626 | 1.00(KHAI) | -0.26/2.60 | 33.2 | M2:3bps(?) | - | AUDHKD(r=-0.75) |
| USDCLP | 4/5 | TRUNG_TINH(0.59) | 0.804 | 1.00(KHAI) | 0.00/0.00 | 13.1 | M3:17bps(?) | - | - |
| USDCOP | 4/5 | - | 0.987 | 1.00(KHAI) | 0.00/0.00 | 3.0 | khong | - | - |
| XM_HK50CASH | 4/5 | - | 1.202 | 1.00(KHAI) | 5.67/0.40 | 14.8 | khong | - | - |
| XM_US100_SEP26 | 4/5 | TRUNG_TINH(0.57) | 1.542 | 1.00(KHAI) | 5.50/-0.50 | 10.2 | khong | - | - |
| XM_US30_SEP26 | 4/5 | TRUNG_TINH(0.59) | 1.081 | 1.00(KHAI) | 5.50/-0.50 | 10.2 | khong | - | - |
| XM_US500_SEP26 | 4/5 | TRUNG_TINH(0.58) | 1.099 | 1.00(KHAI) | 5.50/-0.50 | 10.2 | khong | - | - |
| YH_AEX | 4/5 | TRUNG_TINH(0.58) | 1.209 | 1.00(KHAI) | 4.95/0.33 | 33.8 | M2:7bps(?) | - | - |
| YH_ASX200 | 4/5 | TRUNG_TINH(0.57) | 0.562 | 1.00(KHAI) | 7.64/-1.41 | 8.1 | khong | - | - |
| YH_AUDUSD | 4/5 | TRUNG_TINH(0.60) | 0.996 | 1.00(KHAI) | 0.73/1.85 | 18.6 | khong | - | YH_USDCAD(r=-0.69) |
| YH_BAC | 4/5 | TRUNG_TINH(0.57) | 1.494 | 1.00(KHAI) | 11.58/-1.74 | 25.9 | khong | - | - |
| YH_BOVESPA | 4/5 | - | 2.380 | 1.00(KHAI) | 5.50/-0.50 | 4.0 | M2:17bps(?); M3:23bps(?) | - | - |
| YH_CAC40 | 4/5 | TRUNG_TINH(0.57) | 1.386 | 1.00(KHAI) | 5.43/0.34 | 36.5 | M2:8bps(?) | - | - |
| YH_DAUTUONG | 4/5 | TRUNG_TINH(0.59) | 1.507 | 1.00(KHAI) | 9.00/1.00 | 25.9 | M1:35bps(?) | - | - |
| YH_DAUWTI | 4/5 | HOI_QUY(0.58) | 2.903 | 1.00(KHAI) | 0.00/41.68 | 26.0 | khong | - | - |
| YH_DONG | 4/5 | TRUNG_TINH(0.58) | 1.563 | 1.00(KHAI) | 9.00/1.00 | 25.9 | khong | - | - |
| YH_DOWJONES | 4/5 | HOI_QUY(0.55) | 1.143 | 1.00(KHAI) | 5.80/-0.66 | 20.0 | khong | - | - |
| YH_EUSTOXX50 | 4/5 | HOI_QUY(0.57) | 1.343 | 1.00(KHAI) | 5.31/0.34 | 19.4 | khong | - | - |
| YH_FTSE100 | 4/5 | TRUNG_TINH(0.57) | 0.933 | 1.00(KHAI) | 6.85/-0.74 | 8.0 | M2:9bps(?) | - | - |
| YH_HANGSENG | 4/5 | TRUNG_TINH(0.60) | 1.509 | 1.00(KHAI) | 5.67/0.40 | 34.6 | M2:11bps(?); M3:17bps(?) | - | - |
| YH_IBEX35 | 4/5 | TRUNG_TINH(0.58) | 1.420 | 1.00(KHAI) | 3.77/3.72 | 24.6 | khong | - | - |
| YH_KHIDOT | 4/5 | HOI_QUY(0.59) | 4.342 | 1.00(KHAI) | 0.00/0.00 | 25.9 | khong | - | - |
| YH_KOSPI | 4/5 | TRUNG_TINH(0.59) | 1.467 | 1.00(KHAI) | 5.50/-0.50 | 29.7 | M2:12bps(?) | - | - |
| YH_NGO | 4/5 | XU_HUONG(0.60) | 2.569 | 1.00(KHAI) | 9.00/1.00 | 8.0 | M1:46bps(?) | - | - |
| YH_NIKKEI | 4/5 | TRUNG_TINH(0.58) | 1.089 | 1.00(KHAI) | 2.52/0.83 | 56.6 | khong | - | - |
| YH_RUSSELL2000 | 4/5 | HOI_QUY(0.57) | 1.436 | 1.00(KHAI) | 6.42/-0.24 | 19.6 | M2:10bps(?) | - | - |
| YH_SENSEX | 4/5 | XU_HUONG(0.60) | 1.361 | 1.00(KHAI) | 5.50/-0.50 | 29.1 | M2:18bps(?) | - | - |
| YH_SMI | 4/5 | TRUNG_TINH(0.58) | 1.082 | 1.00(KHAI) | 2.98/3.16 | 35.8 | M2:9bps(?) | - | - |
| YH_TAIWAN | 4/5 | XU_HUONG(0.61) | 1.273 | 1.00(KHAI) | 6.47/-0.28 | 29.1 | M3:16bps(?) | - | - |
| YH_TSX | 4/5 | XU_HUONG(0.62) | 0.779 | 1.00(KHAI) | 5.12/0.68 | 33.0 | M1:16bps(?); M2:9bps(?); M3:10bps(?) | - | - |
| YH_USDCAD | 4/5 | TRUNG_TINH(0.57) | 0.681 | 1.00(KHAI) | -0.26/2.60 | 17.6 | khong | - | YH_AUDUSD(r=-0.69) |
| YH_USDCHF | 4/5 | HOI_QUY(0.58) | 0.773 | 1.00(KHAI) | -1.76/6.07 | 17.6 | khong | - | - |
| AUDTHB | 3/5 | - | 0.937 | 1.00(KHAI) | 1.50/1.50 | 2.9 | khong | - | USDCAD(r=-0.53) |
| USDCNH | 2/5 | - | 0.255 | 1.00(KHAI) | 0.38/5.43 | 1.6 | khong | - | - |