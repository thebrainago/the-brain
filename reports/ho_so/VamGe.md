# Ho so co che cua bot 'VamGe' (do tu lenh that)

- Mau: 3114 lenh GOLD.i# thanh 1198 chuoi, 2018-02-02 den 2021-10-01 (do tin ghep lenh: 1.0). Da tach 19 lenh bao hiem (hedge) ra khoi so lieu.
- Them lenh, luoi, lot - Buoc theo bac (doi buoc o moc so lenh) [cao]: buoc doi 1 lan theo bac: bac 2-4: ~10.3; bac 5-17: ~15.4 pip (dung sai 12%) / Chi them lenh khi mo nen moi [cao]: 469 cap lenh them lien nhau khong cap nao cung nen 15 phut (ky vong ngau nhien 178 cap, thuc te 0): toi da... / Mo lenh doi ung sau N lenh (hedge khi sau) [vua]: lenh mang nhan rieng (ccbsn free/dethayhuan/#/hs, ccbsn free/dethayhuan/#/hb): 19 lenh (0.6%), moi lenh mo... / He so lot doi theo bac [vua]: lot lenh thu k = lot dau x he so_bac^(k-1), MU dem tu lenh dau chuoi, he so doi 2 lan theo bac (lam tron gan...
- Thoat va bao ve - TP ca chuoi tu gia trung binh [cao]: thoat ca chuoi cach gia trung binh mot khoang toi thieu co dinh: chuoi 1 lenh: bien duoi 10.1 pip (91% chuoi...
- Khong thay (da do, co tiep xuc): Vao ngay, khong cho tin hieu, Danh theo xu huong (trend-following), Chi mot chieu (chi Buy hoac chi Sell), Luoi gian cach deu, Buoc gian dan theo he so, Gia hoi thi nhoi them lenh, keo TP lai gan, Moi lan co tin hieu la them mot lenh, Nhoi them khi dang lai (pyramiding).... Chua ket luan duoc: Cho gia lui roi moi vao lai (khoi CUA TA), Hai chuoi Buy va Sell chay doc lap, Chap nhan hoa von khi chuoi dai, Keo SL ve hoa von khi da co lai, Trailing stop ca chuoi, Loc ngay / thu / lich.
- Lich su lenh khong cho do 19 khoi (can duong gia / .set / ma nguon): Nguoi vao lenh dau, bot lo phan sau, Vao khi RSI ngan han qua ban, Vao theo 'tam gia' = gia mo cua ngay, Doc tin hieu tu chi bao ben ngoai, Vao theo duong trung binh (MA / EMA), Lenh stop doi ung (hedging bang lenh cho).... Canh bao: lich su co luoi tick 10 giay (bao cao tester Model 0/1): moi bang chung o muc GIAY la do bo mo phong, khong phai nhip that cua EA

## Mau

- 3114 lenh GOLD.i# (19 lenh bao hiem tach rieng), 1198 chuoi, 2018-02-02 den 2021-10-01; luoi thoi gian cua lich su 10.0 giay

## Co che DANG CHAY trong lenh that (5 khoi)

| Khoi | Nhom | Do tin | Lenh that cho thay |
|---|---|---|---|
| Buoc theo bac (doi buoc o moc so lenh) (luoi_buoc_theo_bac) | TANG | cao | buoc doi 1 lan theo bac: bac 2-4: ~10.3; bac 5-17: ~15.4 pip (dung sai 12%) |
| Chi them lenh khi mo nen moi (luoi_theo_nen_moi) | TANG | cao | 469 cap lenh them lien nhau khong cap nao cung nen 15 phut (ky vong ngau nhien 178 cap, thuc te 0): toi da MOT lenh them moi nen 15 phut; cap (lenh vao, lenh them dau) van cung nen 437 / 575 cap (ky vong 431): luat khong tinh lenh vao |
| Mo lenh doi ung sau N lenh (hedge khi sau) (lenh_doi_ung_sau_n_lenh) | TANG | vua | lenh mang nhan rieng (ccbsn free/dethayhuan/#/hs, ccbsn free/dethayhuan/#/hb): 19 lenh (0.6%), moi lenh mo khi chuoi nguoc chieu dang mo (lop chu dao chi 1%) va chuoi do da co >= 16 lenh (trung vi 17); 100% mo cung giay voi lenh chu moi nhat; lot bang lot lenh chu moi nhat o 100% (guong lot DCA) |
| He so lot doi theo bac (lot_nhan_theo_bac) | LOT | vua | lot lenh thu k = lot dau x he so_bac^(k-1), MU dem tu lenh dau chuoi, he so doi 2 lan theo bac (lam tron gan nhat tung lenh): bac 2-10: x1 (khoang tuong thich 0.93..1.05); bac 11-20: x1.2 (khoang tuong thich 1.20..1.20); bac 21-25: x1.1 (khoang tuong thich 1.10..1.10) |
| TP ca chuoi tu gia trung binh (tp_chuoi_tu_gia_tb) | THOAT | cao | thoat ca chuoi cach gia trung binh mot khoang toi thieu co dinh: chuoi 1 lenh: bien duoi 10.1 pip (91% chuoi nam trong [L, 2L], 11% tai dung L); chuoi 2-4 lenh: bien duoi 20.0 pip (80% chuoi nam trong [L, 2L], 8% tai dung L); chuoi 5-9 lenh: bien duoi 20.1 pip (78% chuoi nam trong [L, 2L], 8% tai dung L); chuoi 10+... |

## Chua ket luan duoc (co tiep xuc nhung bang chung khong du)

- **Cho gia lui roi moi vao lai (khoi CUA TA)** (vao_lai_sau_cho_lui): chuoi moi khong mo ngay (80% sau 10380 giay) va cung khong co khoang lui gia co dinh (rcv 9.41): co the vao theo tin hieu - xem dieu_kien_vao (can du lieu gia)
- **Hai chuoi Buy va Sell chay doc lap** (hai_chieu_doc_lap): co ca hai chieu (mua 50%) nhung chi 0.2% thoi gian cung mo: luan phien theo tin hieu hoac khong doc lap
- **Chap nhan hoa von khi chuoi dai** (thoat_hoa_von_khi_chuoi_dai): 19% chuoi 5-9 lenh dong gan gia trung binh (/x/ <= 5.0 pip); 87% cua chung la chuoi BAN (chung 50%); chuoi 2-4 lenh: 14% - khong thay bac nhay o mot do sau co dinh
- **Keo SL ve hoa von khi da co lai** (keo_sl_hoa_von_khi_co_lai): 116 chuoi (17% chuoi >= 2 lenh) thoat o CANH TREN sac ~ 2.0 pip so voi gia trung binh (chi 0 chuoi nam tren canh, trong khi bien TP 20.0 pip), duoi mem toi -8.1 pip (gia nhay qua muc khoa khi EA dong bang lenh thi truong); 88% la chuoi BAN (ca nhom 50%). Du...
- **Trailing stop ca chuoi** (trailing_stop_chuoi): 116 chuoi (17% chuoi >= 2 lenh) thoat o CANH TREN sac ~ 2.0 pip so voi gia trung binh (chi 0 chuoi nam tren canh, trong khi bien TP 20.0 pip), duoi mem toi -8.1 pip (gia nhay qua muc khoa khi EA dong bang lenh thi truong); 88% la chuoi BAN (ca nhom 50%). Du...
- **Loc ngay / thu / lich** (loc_ngay_thu_lich): khong thay thu nao trong tuan bi bo (moi thu co lenh deu co chuoi bat dau); 102% chuoi nam trong 2 gio dau ngay so voi muc trung binh: khong thay tre dau ngay; lich ngay le / dau - cuoi thang chua do duoc (can lich su nhieu nam)

## Khong thay (da do, co tiep xuc, do tin vua tro len)

- Vao ngay, khong cho tin hieu; Danh theo xu huong (trend-following); Chi mot chieu (chi Buy hoac chi Sell); Luoi gian cach deu; Buoc gian dan theo he so; Gia hoi thi nhoi them lenh, keo TP lai gan; Moi lan co tin hieu la them mot lenh; Nhoi them khi dang lai (pyramiding); Lot phang; Lot tang cong; Lot nhan theo he so; Tong lot mot chieu gap doi chieu kia; Lot theo day Fibonacci; Nhan lot sau moi lan cat lo (martingale lenh don); Lot tu dong theo von; TP ca chuoi theo tien; Thoat khi trung binh duong va RSI vuot nguong; Doi TP khi chuoi dang lo; Tia cap: ghep lenh sau nhat voi lenh dau (khoi CUA TA); Tia N lenh khi chuoi dai; Cat lo theo tien (chuoi / tai khoan); Loc gio giao dich

## Lich su lenh KHONG cho do duoc (19 khoi: can duong gia / .set / ma nguon)

- Nguoi vao lenh dau, bot lo phan sau; Vao khi RSI ngan han qua ban; Vao theo 'tam gia' = gia mo cua ngay; Doc tin hieu tu chi bao ben ngoai; Vao theo duong trung binh (MA / EMA); Lenh stop doi ung (hedging bang lenh cho); Gong lenh dang lai de can lenh am; Tran lot; Tran so lenh cua chuoi; TP rieng tung lenh; TP treo len (TP dich dan); All Sniper: dong tat ca khi lai X USD sau N lenh; SL co dinh tung lenh; Loc spread; Loc tin tuc; Loc ADX / ATR (do manh xu huong, do bien dong); Loc sideway bang nen; Loc bao bien dong; Loc DCA tu lenh thu N

## Tham so do duoc

| Tham so | Gia tri | Don vi | Khoi | Ghi chu |
|---|---|---|---|---|
| so_lenh_kich_hoat | 16 | lenh | lenh_doi_ung_sau_n_lenh | chuoi chu da co so lenh nay khi hedge dau tien mo (lech 1 la cach dem; xem khop_knob) |
| ty_lot_so_voi_lenh_chu_moi | 1.0 | ty_le | lenh_doi_ung_sau_n_lenh | lot hedge = lot lenh chu moi nhat (khop 100% lenh) |
| khung_tin_hieu_phut | 2 | phut | vao_chi_bao_ngoai | khung nen ma entry chi kiem khi mo nen moi (khung lon nhat khop; khop moi khung nho hon no) |
| toi_da_lenh_moi_nen_phut | 15 | phut | luoi_theo_nen_moi | khong co hai lenh them lien nhau cua mot chuoi trong cung mot nen khung nay (nen cua bieu do chay EA) |
| buoc_bac_1 | 10.3 | pip | luoi_buoc_theo_bac | bac 2..4 (phan vi 10%; trung vi 12.7) |
| buoc_bac_2 | 15.4 | pip | luoi_buoc_theo_bac | bac 5..17 (phan vi 10%; trung vi 18.3) |
| moc_doi_buoc_1 | 4 | lenh | luoi_buoc_theo_bac | lenh thu 5 la lenh dau cua bac buoc moi (lech 1 la cach dem) |
| he_so_bac_1 | 1.0 | he_so | lot_nhan_theo_bac | bac 2..10, khoang tuong thich 0.926..1.046 (chon so tron nhat); lot lenh thu k = lot dau x he so^(k-1) (mu dem tu lenh dau chuoi) |
| he_so_bac_2 | 1.2 | he_so | lot_nhan_theo_bac | bac 11..20, khoang tuong thich 1.200..1.200 (chon so tron nhat); lot lenh thu k = lot dau x he so^(k-1) (mu dem tu lenh dau chuoi) |
| moc_doi_he_so_1 | 10 | lenh | lot_nhan_theo_bac | lenh thu 11 la lenh dau cua bac he so moi (lech 1 la cach dem) |
| he_so_bac_3 | 1.1 | he_so | lot_nhan_theo_bac | bac 21..25, khoang tuong thich 1.098..1.101 (chon so tron nhat); lot lenh thu k = lot dau x he so^(k-1) (mu dem tu lenh dau chuoi) |
| moc_doi_he_so_2 | 20 | lenh | lot_nhan_theo_bac | lenh thu 21 la lenh dau cua bac he so moi (lech 1 la cach dem) |
| tp_pip_chuoi_1 | 10.1 | pip | tp_chuoi_tu_gia_tb | bien duoi sac cua khoang cach thoat, chuoi 1 lenh (n=524, do phan giai gia 0.10 pip; EA dong bang lenh thi truong thuong cho bien cao hon khai bao mot nac gia) |
| tp_pip_chuoi_2-4 | 20.0 | pip | tp_chuoi_tu_gia_tb | bien duoi sac cua khoang cach thoat, chuoi 2-4 lenh (n=515, do phan giai gia 0.10 pip; EA dong bang lenh thi truong thuong cho bien cao hon khai bao mot nac... |
| tp_pip_chuoi_5-9 | 20.1 | pip | tp_chuoi_tu_gia_tb | bien duoi sac cua khoang cach thoat, chuoi 5-9 lenh (n=120, do phan giai gia 0.10 pip; EA dong bang lenh thi truong thuong cho bien cao hon khai bao mot nac... |
| tp_pip_chuoi_10+ | 20.2 | pip | tp_chuoi_tu_gia_tb | bien duoi sac cua khoang cach thoat, chuoi 10+ lenh (n=39, do phan giai gia 0.10 pip; EA dong bang lenh thi truong thuong cho bien cao hon khai bao mot nac gia) |
| khoa_loi_pip | 2.0 | pip | trailing_stop_chuoi | canh tren sac cua cum thoat duoi bien TP (chuoi >= 2 lenh), duoi mem phia duoi; khop 'initial SL' / khoa dau neu .set khai |

## Luu y

- lich su co luoi tick 10 giay (bao cao tester Model 0/1): moi bang chung o muc GIAY la do bo mo phong, khong phai nhip that cua EA
