# Ho so co che cua bot 'CanCuBo' (do tu lenh that)

- Mau: 1962 lenh GOLD.i# thanh 1291 chuoi, 2018-01-02 den 2021-10-08 (do tin ghep lenh: 1.0).
- Them lenh, luoi, lot - Chi mot chieu (chi Buy hoac chi Sell) [cao]: 100% chuoi cung mot chieu (mua) / Luoi gian cach deu [cao]: buoc gan nhu khong doi qua 16 bac (~100.7 pip, lech <= 6%) / Chi them lenh khi mo nen moi [thap]: 22 cap lenh them lien nhau khong cap nao cung nen 15 phut (ky vong ngau nhien 8 cap, thuc te 0): toi da MOT... / Lot nhan theo he so [cao]: lot lenh thu k = lot dau x he so^(k-1), lam tron MOT lan (gan nhat): he so 1.05..1.05
- Thoat va bao ve - TP rieng tung lenh [cao]: 100% trong 41 lenh don dong boi [tp] cach gia vao dung 100.0 pip (khong phan biet TP lenh va TP chuoi: chuoi... / Trailing stop ca chuoi [cao]: thoat ca chuoi bang SL keo theo: khoang cach thoat khong bao gio duoi 15.0 pip va cac gia tri tren no nam...
- Khong thay (da do, co tiep xuc): Vao ngay, khong cho tin hieu, Danh theo xu huong (trend-following), Hai chuoi Buy va Sell chay doc lap, Buoc gian dan theo he so, Buoc theo bac (doi buoc o moc so lenh), Gia hoi thi nhoi them lenh, keo TP lai gan, Moi lan co tin hieu la them mot lenh, Nhoi them khi dang lai (pyramiding).... Chua ket luan duoc: Cho gia lui roi moi vao lai (khoi CUA TA), Keo SL ve hoa von khi da co lai, Loc ngay / thu / lich.
- Lich su lenh khong cho do 18 khoi (can duong gia / .set / ma nguon): Nguoi vao lenh dau, bot lo phan sau, Vao khi RSI ngan han qua ban, Vao theo 'tam gia' = gia mo cua ngay, Doc tin hieu tu chi bao ben ngoai, Vao theo duong trung binh (MA / EMA), Gong lenh dang lai de can lenh am.... Canh bao: lich su co luoi tick 10 giay (bao cao tester Model 0/1): moi bang chung o muc GIAY la do bo mo phong, khong phai nhip that cua EA

## Mau

- 1962 lenh GOLD.i# (0 lenh bao hiem tach rieng), 1291 chuoi, 2018-01-02 den 2021-10-08; luoi thoi gian cua lich su 10.0 giay

## Co che DANG CHAY trong lenh that (6 khoi)

| Khoi | Nhom | Do tin | Lenh that cho thay |
|---|---|---|---|
| Chi mot chieu (chi Buy hoac chi Sell) (mot_chieu) | TANG | cao | 100% chuoi cung mot chieu (mua) |
| Luoi gian cach deu (luoi_gian_cach_deu) | TANG | cao | buoc gan nhu khong doi qua 16 bac (~100.7 pip, lech <= 6%) |
| Chi them lenh khi mo nen moi (luoi_theo_nen_moi) | TANG | thap | 22 cap lenh them lien nhau khong cap nao cung nen 15 phut (ky vong ngau nhien 8 cap, thuc te 0): toi da MOT lenh them moi nen 15 phut; cap (lenh vao, lenh them dau) van cung nen 10 / 16 cap (ky vong 7): luat khong tinh lenh vao |
| Lot nhan theo he so (lot_nhan) | LOT | cao | lot lenh thu k = lot dau x he so^(k-1), lam tron MOT lan (gan nhat): he so 1.05..1.05 |
| TP rieng tung lenh (tp_tung_lenh) | THOAT | cao | 100% trong 41 lenh don dong boi [tp] cach gia vao dung 100.0 pip (khong phan biet TP lenh va TP chuoi: chuoi 1 lenh) |
| Trailing stop ca chuoi (trailing_stop_chuoi) | BAO_VE | cao | thoat ca chuoi bang SL keo theo: khoang cach thoat khong bao gio duoi 15.0 pip va cac gia tri tren no nam tren bac thang 2.0 pip (khop 100% so voi 15% ngau nhien, 939 chuoi) |

## Chua ket luan duoc (co tiep xuc nhung bang chung khong du)

- **Cho gia lui roi moi vao lai (khoi CUA TA)** (vao_lai_sau_cho_lui): chuoi moi khong mo ngay (80% sau 1460 giay) va cung khong co khoang lui gia co dinh (rcv 13.16): co the vao theo tin hieu - xem dieu_kien_vao (can du lieu gia)
- **Keo SL ve hoa von khi da co lai** (keo_sl_hoa_von_khi_co_lai): san 15.0 pip co the la khoa dau cua trailing hoac delta keo SL ve hoa von: khong phan biet tu lenh
- **Loc ngay / thu / lich** (loc_ngay_thu_lich): khong thay thu nao trong tuan bi bo (moi thu co lenh deu co chuoi bat dau); 77% chuoi nam trong 2 gio dau ngay so voi muc trung binh: khong thay tre dau ngay; lich ngay le / dau - cuoi thang chua do duoc (can lich su nhieu nam)

## Khong thay (da do, co tiep xuc, do tin vua tro len)

- Vao ngay, khong cho tin hieu; Danh theo xu huong (trend-following); Hai chuoi Buy va Sell chay doc lap; Buoc gian dan theo he so; Buoc theo bac (doi buoc o moc so lenh); Gia hoi thi nhoi them lenh, keo TP lai gan; Moi lan co tin hieu la them mot lenh; Nhoi them khi dang lai (pyramiding); Lenh stop doi ung (hedging bang lenh cho); Mo lenh doi ung sau N lenh (hedge khi sau); Lot phang; Lot tang cong; He so lot doi theo bac; Tong lot mot chieu gap doi chieu kia; Lot theo day Fibonacci; Lot tu dong theo von; TP ca chuoi tu gia trung binh; TP ca chuoi theo tien; Thoat khi trung binh duong va RSI vuot nguong; Doi TP khi chuoi dang lo; Tia cap: ghep lenh sau nhat voi lenh dau (khoi CUA TA); SL co dinh tung lenh; Chap nhan hoa von khi chuoi dai; Loc gio giao dich

## Lich su lenh KHONG cho do duoc (18 khoi: can duong gia / .set / ma nguon)

- Nguoi vao lenh dau, bot lo phan sau; Vao khi RSI ngan han qua ban; Vao theo 'tam gia' = gia mo cua ngay; Doc tin hieu tu chi bao ben ngoai; Vao theo duong trung binh (MA / EMA); Gong lenh dang lai de can lenh am; Nhan lot sau moi lan cat lo (martingale lenh don); Tran lot; Tran so lenh cua chuoi; TP treo len (TP dich dan); All Sniper: dong tat ca khi lai X USD sau N lenh; Cat lo theo tien (chuoi / tai khoan); Loc spread; Loc tin tuc; Loc ADX / ATR (do manh xu huong, do bien dong); Loc sideway bang nen; Loc bao bien dong; Loc DCA tu lenh thu N

## Tham so do duoc

| Tham so | Gia tri | Don vi | Khoi | Ghi chu |
|---|---|---|---|---|
| chieu | mua | chieu | mot_chieu |  |
| khung_tin_hieu_phut | 1 | phut | vao_chi_bao_ngoai | khung nen ma entry chi kiem khi mo nen moi (khung lon nhat khop; khop moi khung nho hon no) |
| toi_da_lenh_moi_nen_phut | 15 | phut | luoi_theo_nen_moi | khong co hai lenh them lien nhau cua mot chuoi trong cung mot nen khung nay (nen cua bieu do chay EA) |
| buoc_pip | 100.7 | pip | luoi_gian_cach_deu | phan vi 10% cua buoc nghich (uoc luong gia tri cai; trung vi 106.5 gom phan vuot nguong do tick thua) |
| he_so_lot | 1.05 | he_so | lot_nhan | khoang tuong thich 1.046..1.052 (tich; chon so tron nhat) |
| tp_pip | 100.0 | pip | tp_tung_lenh | 41 lenh don dong boi [tp] cach gia vao dung 100.0 pip (100% tai dung gia) |
| trailing_khoa_dau_pip | 15.0 | pip | trailing_stop_chuoi | san khoang cach thoat (chuoi 1 lenh), bien duoi sac |
| trailing_buoc_pip | 2.0 | pip | trailing_stop_chuoi | gia tri thoat nam tren luoi L + k*buoc: khop 100% (ngau nhien 15%) |

## Luu y

- lich su co luoi tick 10 giay (bao cao tester Model 0/1): moi bang chung o muc GIAY la do bo mo phong, khong phai nhip that cua EA
