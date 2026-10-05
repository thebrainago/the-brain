# NHANH HANG HOA (chu du an 05/10/2026) - lam duoc o CLOUD, khong can may nha

Ly do: gia NGAY hang hoa la du lieu cong khai (Stooq / FRED), khong can MT5. Ma: `nhan/hang_hoa.py` (+ `test_hang_hoa.py`, 5 ca hai chieu: co mua vu / chu ky that thi bat, khong co thi tu choi).
**Dang bi chan**: mang cloud tu choi stooq.com va fred.stlouisfed.org (403 o proxy). Chu du an mo "Network access" cua moi truong cloud, them ten mien duoc phep:
`stooq.com`, `fred.stlouisfed.org`, `www.eia.gov`, `publicreporting.cftc.gov`, `www.cftc.gov`, `query1.finance.yahoo.com` (du phong). Mo xong: `python3 -c "from nhan import hang_hoa as H; [H.tai(t) for t in H.HANG_HOA]"`.

## Thu tu lam (khi co gia)
1. Tai 12 hang hoa ngay (dau, khi tu nhien, vang, bac, dong, ngo, lua mi, dau tuong, ca phe, duong, bong, dau nhien lieu), toi thieu 15 nam.
2. `mua_vu_ngay` + `chu_ky` tung ma: cho cai nao TRA LOI "co chu ky" (khong phai cai nao cung tim ra thang dep nhat). Tin cay khi >= 70% so nam cung dau + hoan vi p<0,05.
3. Cac kieu dac biet chu du an hoi: **IBS** (`ibs_ngay`, mua IBS<0,2 giu 1 ngay), **mua theo lich du lieu kinh te** (ton kho dau EIA thu Tu, bao cao COT, CPI -> vang), **chi so hoa kim/dau** (ti le dau/khi, vang/bac).
4. Chuoi chien luoc co chu ky ro (khi tu nhien mua dong, nong san theo mua vu trong): ghi thanh khai bao DSL (`ngu_phap`, chi bao `thang`/`ngay_trong_thang` da co) roi `thu_co_che` tren doan kham_pha.
5. Co DAT o ngay -> chuyen sang CFD tuong ung tren MT5 (XTIUSD, XNGUSD, XAUUSD...) bang viec cho may nha; phi san CFD do o may nha.
Bay: Stooq la hop dong NOI (khoang cuon khong phai loi nhuan - chi dung loi suat log ngay); null hoan vi da gom cuc tri cua ~24 cua so; 12 hang hoa x nhieu phep = dem vao FDR cua so tay.

## Dot nhap HANG HOA (05/10): 20 y tuong (Claude mo rong) -> 20 ban + 20 doi chung/lat -> job may nha
`reports/deepseek/chay_dsl_hh.py` -> `reports/deepseek/dsl_hh/` (+ `meta.json` tai san/khung). Y tuong: khi tu nhien mua dong / ban xuan, dau mua lai xe + IBS + thu Tu ton kho EIA,
vang / bac IBS + mua vu cuoi nam + dau nam, nen bien dong pha vo, nong san theo vu (ngo, lua mi, dau tuong), ca phe / duong xu huong, phien My / London (H1).
**Loi tim thay khi Claude doc mau**: DSL danh so `ngay_trong_tuan` 0 = thu Hai -> thu Tu = 2 (prompt dau toi ghi 3, LLM theo; da sua); hai y tuong goc la BAN phai soan chieu -1 chu khong lat tu ban MUA.
Cac job `viec/cho/2xx-hh-*` chay `thu_co_che` tren CFD XTIUSD / XBRUSD / XNGUSD / XAUUSD / XAGUSD ...; ma nao may nha khong co du lieu se tra CHUA_DO_DUOC (khong phai AM).
