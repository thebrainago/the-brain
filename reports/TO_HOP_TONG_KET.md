# TONG KET TO HOP

*2938 o chang 2 / 72 ma / khung D1 / 9573 giay*

Xep hang bang `cagr_dd20`: lai %/nam khi quy ca hai ve cung ngan sach
sut giam 20%. `hon_moc` = thang **max(mua-giu, ban-giu, tien mat)**.

## DOC BANG NAY NHU THE NAO

Chang 1 da CHON top 200 o theo chinh `cagr_dd20`, roi chang 2 mo rong
dung nhung o do. Nen con so `hon_moc` o day **bi thoi len boi chinh phep
chon** - no khong phai ti le thanh cong cua mot lan quet mu.

Cai bang nay tra loi duoc, va chi tra loi duoc, mot cau: *voi nhung o da
co ve co gi, thi doi CAU TRUC hay doi LUAT lam ket qua thay doi ra sao*.
Do la dung cau hoi chu du an dat ra cho module quan li lenh. Muon biet
ti le thanh cong THAT thi phai doc chang 1 (chua chon), hoac chay lai
tren holdout.

## Theo CAU TRUC VAO LENH

| cau truc vao lenh | o | dd20 trung vi | tot nhat | ti le duong | hon moc |
|---|---:|---:|---:|---:|---:|
| thi_truong | 1781 | 3.217 | 35.321 | 89% | 1441 |
| dca_deu | 199 | 3.156 | 16.926 | 94% | 174 |
| tt_hedge | 196 | 2.589 | 53.442 | 85% | 150 |
| dca_von | 199 | 2.353 | 19.544 | 92% | 166 |
| nhanh | 200 | 0.990 | 33.569 | 66% | 116 |
| hai_dau_oco | 181 | -0.713 | 8.286 | 27% | 24 |
| hai_dau_giu | 182 | -0.746 | 10.404 | 25% | 23 |

**NEN DI**: thi_truong (trung vi 3.217, 1590/1781 o duong)

**NEN TRANH**: hai_dau_giu (trung vi -0.746, chi 46/182 o duong)

## Theo LUAT QUAN TRI

| luat quan tri | o | dd20 trung vi | tot nhat | ti le duong | hon moc |
|---|---:|---:|---:|---:|---:|
| sl2_tp4 | 200 | 3.424 | 20.246 | 92% | 165 |
| sl2_tp4_chot1 | 200 | 3.280 | 19.554 | 92% | 161 |
| khong_gi | 183 | 3.206 | 32.699 | 94% | 166 |
| sl3_trail2 | 198 | 3.091 | 32.699 | 92% | 172 |
| sl2_tp6_hue2_trail2 | 200 | 2.911 | 20.246 | 90% | 160 |
| sl2_tp4_hue1 | 200 | 2.721 | 20.246 | 88% | 155 |
| sl2_trail1 | 200 | 2.171 | 18.977 | 84% | 144 |
| - | 1357 | 2.096 | 53.442 | 71% | 852 |
| chot_nhanh_sl1_tp1 | 200 | 1.350 | 35.321 | 71% | 119 |

**NEN DI**: sl2_tp4 (trung vi 3.424, 184/200 o duong)

**NEN TRANH**: chot_nhanh_sl1_tp1 (trung vi 1.350, chi 142/200 o duong)

## Theo HO CO CHE

| ho co che | o | dd20 trung vi | tot nhat | ti le duong | hon moc |
|---|---:|---:|---:|---:|---:|
| dong_tien | 14 | 3.196 | 5.722 | 86% | 11 |
| pha_vo | 255 | 3.057 | 15.353 | 88% | 193 |
| quay_ve_trung_binh | 1252 | 3.028 | 53.442 | 80% | 896 |
| bien_dong | 220 | 2.858 | 19.544 | 80% | 164 |
| xu_huong | 1154 | 1.970 | 18.233 | 78% | 795 |
| lich | 43 | 1.805 | 9.628 | 86% | 35 |

**NEN DI**: dong_tien (trung vi 3.196, 11/14 o duong)

**NEN TRANH**: lich (trung vi 1.805, chi 36/43 o duong)

## Theo TAI SAN

| tai san | o | dd20 trung vi | tot nhat | ti le duong | hon moc |
|---|---:|---:|---:|---:|---:|
| US500M | 116 | 13.965 | 53.442 | 100% | 98 |
| XM_US2000CASH | 120 | 8.611 | 21.422 | 90% | 104 |
| XM_US30CASH | 120 | 7.871 | 14.786 | 87% | 94 |
| XM_XAUEUR | 114 | 7.859 | 19.631 | 94% | 86 |
| XM_JP225CASH | 119 | 5.669 | 19.544 | 92% | 52 |
| DE40 | 120 | 4.259 | 10.746 | 94% | 100 |
| EURCAD | 15 | 4.203 | 6.028 | 87% | 13 |
| USDCHF | 60 | 3.414 | 6.700 | 87% | 52 |
| XM_FRA40CASH | 120 | 3.160 | 9.137 | 86% | 101 |
| GBPNOK | 26 | 2.899 | 8.533 | 96% | 25 |
| XAUUSD | 120 | 2.742 | 7.991 | 92% | 94 |
| XM_GBPUSD | 120 | 2.699 | 6.300 | 85% | 102 |

**NEN DI**: US500M (trung vi 13.965, 116/116 o duong)

**NEN TRANH**: XAUAUDM (trung vi -4.513, chi 3/12 o duong)

## CHANG 4 - HOLDOUT (chang quyet dinh)

Chon tren 60% dau, DO tren 40% sau. Ba chang tren deu chon tren
chinh so chung do, nen chi bang nay noi duoc co gi that hay khong.

**592/2248 he thang moc o holdout.**

Tieu chi: hai nua deu thang moc CUA CHINH NO, va ti le
`hold/train` nam trong [0.33, 3.0] (hai nua cung co).

| ma | khung | co che | cau truc | luat | dd20 train | dd20 HOLD | ti le | moc hold |
|---|---|---|---|---|---:|---:|---:|---:|
| US500M | D1 | ns_nen_rau_tren_>_q98_giu1 | thi_truong | - | 23.78 | **67.47** | 2.84 | 14.90 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu1 | thi_truong | - | 23.78 | **67.47** | 2.84 | 14.90 |
| US500M | D1 | ns_nen_rau_tren_>_q98_giu2 | tt_hedge | - | 57.57 | **48.72** | 0.85 | 14.90 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu2 | tt_hedge | - | 57.57 | **48.72** | 0.85 | 14.90 |
| US500M | D1 | ns_nen_rau_tren_>_q98_giu2 | thi_truong | - | 27.86 | **48.10** | 1.73 | 14.90 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu2 | thi_truong | - | 27.86 | **48.10** | 1.73 | 14.90 |
| US500M | D1 | ns_nen_rau_tren_>_q98_giu2 | thi_truong | khong_gi | 27.20 | **44.50** | 1.64 | 14.90 |
| US500M | D1 | ns_nen_rau_tren_>_q98_giu2 | thi_truong | sl3_trail2 | 27.20 | **44.50** | 1.64 | 14.90 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu2 | thi_truong | khong_gi | 27.20 | **44.50** | 1.64 | 14.90 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu2 | thi_truong | sl3_trail2 | 27.20 | **44.50** | 1.64 | 14.90 |
| US500M | D1 | ns_nen_rau_tren_>_q98_giu2 | thi_truong | sl2_tp4 | 19.66 | **44.50** | 2.26 | 14.90 |
| US500M | D1 | ns_nen_rau_tren_>_q98_giu2 | thi_truong | sl2_tp6_hue2_trail2 | 19.66 | **44.50** | 2.26 | 14.90 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu2 | thi_truong | sl2_tp4 | 19.66 | **44.50** | 2.26 | 14.90 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu2 | thi_truong | sl2_tp6_hue2_trail2 | 19.66 | **44.50** | 2.26 | 14.90 |
| US500M | D1 | ns_nen_rau_tren_>_q98_giu2 | thi_truong | sl2_tp4_chot1 | 19.00 | **42.64** | 2.24 | 14.90 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu2 | thi_truong | sl2_tp4_chot1 | 19.00 | **42.64** | 2.24 | 14.90 |
| US500M | D1 | ns_nen_rau_tren_>_q95_giu1 | thi_truong | - | 24.45 | **40.52** | 1.66 | 14.90 |
| US500M | D1 | ns_nen_sao_bang_>_q95_giu1 | thi_truong | - | 24.45 | **40.52** | 1.66 | 14.90 |
| US500M | D1 | ns_nen_rau_tren_>_q98_giu2 | thi_truong | sl2_tp4_hue1 | 19.66 | **39.39** | 2.00 | 14.90 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu2 | thi_truong | sl2_tp4_hue1 | 19.66 | **39.39** | 2.00 | 14.90 |

## Cai duy nhat dang theo tiep

2094/2938 o thang duoc moc. 

| ma | khung | co che | cau truc | luat | dd20 | moc |
|---|---|---|---|---|---:|---:|
| US500M | D1 | ns_nen_rau_tren_>_q98_giu2 | tt_hedge | - | 53.442 | 4.555 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu2 | tt_hedge | - | 53.442 | 4.555 |
| US500M | D1 | ns_nen_rau_tren_>_q98_giu1 | thi_truong | chot_nhanh_sl1_tp1 | 35.321 | 4.555 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu1 | thi_truong | chot_nhanh_sl1_tp1 | 35.321 | 4.555 |
| US500M | D1 | ns_nen_rau_tren_>_q98_giu1 | thi_truong | - | 33.569 | 4.555 |
| US500M | D1 | ns_nen_rau_tren_>_q98_giu1 | nhanh | - | 33.569 | 4.555 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu1 | thi_truong | - | 33.569 | 4.555 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu1 | nhanh | - | 33.569 | 4.555 |
| US500M | D1 | ns_nen_rau_tren_>_q98_giu1 | thi_truong | khong_gi | 32.699 | 4.555 |
| US500M | D1 | ns_nen_rau_tren_>_q98_giu1 | thi_truong | sl3_trail2 | 32.699 | 4.555 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu1 | thi_truong | khong_gi | 32.699 | 4.555 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu1 | thi_truong | sl3_trail2 | 32.699 | 4.555 |
| US500M | D1 | ns_nen_rau_tren_>_q98_giu10 | thi_truong | - | 31.376 | 4.555 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu10 | thi_truong | - | 31.376 | 4.555 |
| US500M | D1 | ns_nen_rau_tren_>_q98_giu1 | tt_hedge | - | 28.926 | 4.555 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu1 | tt_hedge | - | 28.926 | 4.555 |
| US500M | D1 | ns_nen_rau_tren_>_q98_giu2 | thi_truong | - | 27.435 | 4.555 |
| US500M | D1 | ns_nen_sao_bang_>_q98_giu2 | thi_truong | - | 27.435 | 4.555 |
| US500M | D1 | ns_nen_rau_tren_>_q95_giu10 | thi_truong | - | 26.983 | 4.555 |
| US500M | D1 | ns_nen_sao_bang_>_q95_giu10 | thi_truong | - | 26.983 | 4.555 |
