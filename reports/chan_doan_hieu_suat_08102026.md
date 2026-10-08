# Chan doan hieu suat 08/10/2026 - "24h, hang nghin phep thu, chi ra 1 he lai 13%, DD > 30%"

Cau hoi cua chu du an: hieu suat nay co chap nhan duoc khong, van de that nam o dau, sua the nao.

## Ket luan ngan
1. **Chua chap nhan duoc, va con so 13% chua dang tin hoan toan.** Do la CLMCA D_V1 (+13,45%/nam, maxDD 34,9%, 589 lenh, PF 1,27) o mot muc lot tuy y,
   chi phi con "khai", Model 0 (khong phai tick that). Luat duyet cua chu du an (co lai sau phi + maxDD < 80%) cho phep tang lot - chua kiem.
2. **"Hang nghin phep thu" phan lon la quet luoi tren thuoc do hong.** ~1.250 / ~1.500 phep thu la quet luoi tren ~12 cap; thuoc do cu (`khop_bar=cuc_tri`)
   bao "co lai" o gan nhu MOI o tham so (vd 2.973/3.000) nen khong phan biet duoc tot / xau. Doi chieu 120 o voi MT5 tester that: 109 LECH / 11 KHOP,
   engine cu phong dai trung vi x2,2, toi x16.
3. **Thuoc do that (MT5 tester) gan nhu chet.** 24 don tester chet o giay ~95 (thieu `Include\Trade\Trade.mqh` trong slot), nhieu don bao "DAT" gia (thoat 0 nhung in loi).
4. **Quet dien dan khong sau.** Cac don "quet sau" chay 0,3 giay vi ma cu chi doc trang 1 roi bao xong.
5. **Ma moi khong toi duoc may nha.** Lab nha o 44b3b23d (tre ~275 commit), khong tu cap nhat duoc; 21/22 bo chay ngung nhip tim tu ~20:00-20:30 gio nha (luc cuoi bai: ca 22 deu ngung - may nha dang nghi, binh thuong); du lieu gia chi co 14 ma
   (AUDCAD AUDCHF AUDNZD EURCAD EURGBP EURUSD GBPAUD NZDCAD SP500_CO_TUC_DO US500CASH USDCAD USDCHF USDJPY XAUUSD) nen 31 don dau / ga / duong / lua mi / XAUUSDM thanh "khong co du lieu".
6. Xep hang hepha la chon trong-mau giua <= 1.074 cau hinh, khong kiem soat da so sanh: la goi y, khong phai bang chung.

## Da sua (trong ma, da push; CHUA chay o nha)
- Engine luoi: mo hinh bar `duong_di` mac dinh (`PHIEN_BAN_ENGINE = 4`), loi nhan C cung; ban cu `cuc_tri` van chon duoc de doi chung. (a6acc76d)
- Bo chay: giet CA CAY tien trinh khi het han (bo chay cu treo vo han vi tien trinh mo coi giu pipe), phan loai "DAT gia", ly do tester chet lay tu log tester.
- Quet dien dan: tu tim trang ke, ghi that bai trung thuc (khong bao "xong" khi khong doc duoc). (57b38765)
- Nhan kha nang suy ra tu ma dang chay (`ma-0810`, `engineN`, `dien-dan-v2`): don can ma moi chi bo chay co ma moi nhan; ket qua luoi ghi dau engine, so tay khong xep hang ket qua engine cu.
- Monitor: tuoi nhip tim tinh dung mui gio (truoc day bao nham 19/22 bo chay con song); dem rieng don cho ma moi; `dua_lai` tim don theo ma. (430e776e)
- Hang doi: 135 don dung (120 do lai o hieu chuan bang engine moi, 12 doi chung `cuc_tri`, cai pandas, do + quet sau dien dan), gate theo ma moi. Thu `NHA-HOI-PHUC-08102026` gui nha.

## Chua sua / can nguoi
- Mot phien Claude o may nha phai lam thu `20261008-094857-6bd4` + `NHA-HOI-PHUC-08102026` (khoang 5-10 phut); sau do bo chay tu cap nhat.
- Tester: Trade.mqh trong tung slot; ban chinh CLMCA (ten o lot) de thu tang lot theo luat maxDD < 80%.
- Du lieu: them ma (bac, dau, khi, chi so) can dua duoc len / nap tu MT5; dua gia len repo cong khai can chu du an cho phep tung cap (hien chi 4 cap M15 tu 2018).
- Mo rong luoi/EA cho nguoi thang (cat lo ca gio, loc gio, lot theo tang) - chua viet.

## Kiem lai
`python3 -m nhan.giam_sat_may_nha` (bo chay song / don cho ma moi), `python3 b.py cau lay` (cot ma lab), do lai o hieu chuan: `viec/xong/6*-hcE4-*` + `reports/hieu_chuan/*_e4.json`.
