# NGUON NGOAI CUA CHU DU AN -> THE -> KIEM CHUNG (06/10/2026)

Chu du an gui anh chup bai viet / bot (TikTok, Deep Market Insight...): *"cai toi muon la he thong tim duoc nhung kien thuc va chien luoc nhu nay, ve kiem chung va toi uu"*.
Day la duong dung: **nguon ngoai -> THE (co che kinh te + du lieu can + cach thu) -> thu bang cong cu nc -> ket qua vao so tay**. Moi nguon chu du an gui = mot the o day.
Loi nhan: nhieu thang qua lam rong ha tang (hang doi, engine, cong cu) nhieu hon lam THE tu nguon that. Tu nay moi nguon gui vao la co the + job trong ngay.

## THE 1 - End-of-Day Reversal (Baltussen, Da, Soebhag; co phieu My 1993-2019)
- Y tuong: co phieu giam sau tu dong cua hom qua den truoc dong cua 30 phut (ROD3 = dem + gio dau + giua ngay) thi 30 phut cuoi bat tang; tang manh thi bi ban. Mua 10% thua nhat (dong gop ~85% loi), ban khong 10% thang nhat (~15%), dong het cuoi phien. Tac gia: ~17,3%/nam, t > 10, truoc phi.
- Co che kinh te (tac gia): (1) ca nhan mua duoi sang / bat day chieu; (2) phe ban khong rut lui vi rui ro qua dem. Va tiep dien cuoi phien do market maker gamma hedging + ETF don bay tai can bang.
- Rao can tac gia noi: khop lenh thi truong an loi (spread + phi short cuoi phien).
- CHUA THU DUOC TRONG LAB: can mat cat ngang nhieu co phieu theo phut. Lab chi co CFD chi so / FX / hang hoa, khong co lat cat co phieu.
- Ban chuyen the thu duoc (chuoi thoi gian, mot san pham): chi so US500/US100 co the, M30: loi suat tu dong cua hom qua den truoc 30 phut cuoi du doan dau loi suat 30 phut cuoi? Can them dac trung `ret_tu_dong_cua` (loi suat cong don tu bar dong cua phien truoc). TRANG THAI: chua co dac trung; tac gia chinh bao TS nhin ~2,8 bps - nho, de bi spread an. Uu tien THAP cho den khi chu du an cho biet co du lieu co phieu CFD / nguon phut.
- Hanh dong can chu du an: cho biet XM co CFD co phieu My khong va co muon thu rong khong.

## THE 2 - Bot DCA mot chieu XAUUSD M5 (video TikTok, Zilloo Quyen)
- Mo ta bot: chi vao MOT chieu (mua hoac ban, chu chon xu huong truoc khi bat), nhoi DCA khi gia di nguoc, cat khi am toi da ~20-30% tai khoan, chot ky vong ~+30% tai khoan hoac tuy chinh, khong tu dao chieu.
- Day dung la lop luoi mot chieu cua `luoi.py` (che_do mua | ban, kieu_lot phang/cong, buoc, tp, tran_tang).
- Job: `viec/cho/50-nn-dca-vang-M5.json`, `51-nn-dca-vang-M15.json` (`quet_luoi`, mua + ban rieng, 100 o, uu_tien 3 = chay truoc don CMT / hang hoa). Can ma vang that tren may nha (tam dung XAUUSDM; sai ten thi bao CHUA_DO_DUOC).
- Cau hoi mo cho phien nha: bot chi vao ma "xac dinh xu huong truoc" - phan dinh huong la do tay. Thu 3 ban: chi mua, chi ban, va mua khi gia > SMA lon (loc xu huong).
- Canh bao: don vi `buoc` / `tp` tinh bang pip; voi vang 1 pip ~ 0,1 giá (nhin `ho_so_symbol`), nen luoi buoc 30-150 co the qua nho/lon. Phien nha kiem don vi truoc khi tin ket qua.

## THE 3 - Kiem soat hoi quy Fama-MacBeth (bai chua)
Ban chat la cach tac gia loai bo giai thich khac (size, volume, illiquidity, volatility, mispricing). Khong phai chien luoc. Chi dung lam tieu chuan phan bien: ket qua ban chuyen the phai song sau khi kiem soat bien dong.
