# TOC DO TEST - do duoc gi, chua do gi, lam gi o may nha

*Cloud, 03/10/2026. Chu du an hoi: "toi uu toc do test bang cach toi uu may toi / dung nen tang, ngon ngu khac".*

## Ket luan

1. Phan tang toc nam o ENGINE (Python -> C): **xong, khop tung bit, do duoc.** Quet 54 o tham so tren 190.000 bar mat 0,6 giay thay vi 31 giay.
2. MT5 tester van la TRONG TAI cuoi (tick that, phi that, lenh that) - khong engine nao thay duoc. Chi cho no chay o DA CHOT (Model=0/4).
3. Nghen that gio nam o **MT5 (mot terminal, so giay/lan chua do)** va o **so gia thuyet doc lap**, khong con o engine. Nhanh hon KHONG tao them edge:
   no chi tao them phep thu -> them chon loc. Vi vay moi o cua `quet_luoi` van la MOT phep thu (`so_phep_thu` vao so tay), tran 1.000 o / goi.
4. Khong chuyen sang numba / vectorbt / Rust / GPU / nen tang khac luc nay (bang duoi).
5. Viec dau tien o may nha la DO (muc 4), khong phai cai them gi.

## 1. Do duoc (cloud Linux, 4 vCPU dung chung, chuoi TONG HOP 190.000 bar M15)

| Phep do | Truoc | Sau | He so |
|---|---|---|---|
| Nhan C vs Python tren engine `luoi._mot_ro` | | | x134 |
| Mot lan `thu_luoi` (danh gia 1 o, ca `_he_so_lot_tai_tran`) | 1.547 ms | 18 ms | x86 |
| `quet_luoi` 54 o, 1 luong | 31,2 s (578 ms/o, Python) | 0,62 s (11,6 ms/o, C) | x50 |
| `quet_luoi` 54 o, 2 / 4 luong (C) | | 0,39 / 0,35 s | x80 / x89 |

- Nhan C khop Python **tung bit** (so lenh, so ro, bar, id, tang trung khit; lai/maxDD cung bit tren Python 3.11/3.12/3.13), 100% dong ma duoc test, ASan sach.
  `quet_luoi` o tot nhat ra y het `thu_luoi` mot o (so lenh 28.003, he so lot 412,237, loi suat 52.975,46 - so cua du lieu TONG HOP, **chi THOI GIAN co nghia**).
- Them luong chi nhanh them 1,6x (2 luong) va 1,8x (4 luong): moi o da qua nho (~12 ms) nen phan Python (dung bang, doc ket qua) chiem phan lon, va may cloud
  con chay viec khac. May nha 10 nhan co the khac - do lai (muc 4).

## 2. CHUA do (can may nha)

- Windows / Python 3.14 / dich bang zig hoac MSVC: toc do va tu kiem khop.
- **Giay moi lan chay MT5 tester** (Model=0 va Model=4, 1 nam M15/M1). `ea_tho_quet` / `ea_tho_chay` ghi cot `giay` moi lan - day la con so DAU TIEN.
- `quet_luoi` tren bar that (so lenh that co the nhieu hon -> thoi gian khac); `thu_luoi` tron goi tren du lieu that (gom nap parquet + chi phi).
- Hai terminal MT5 chay cung luc co nhanh gap doi khong (slot 2, `SLOT_TESTER.md`).

## 3. Pheu va bang quyet dinh

```
Tang 1 LOC REN   quet_luoi (C, chi kham_pha, hang tram o / vai giay)   -> doc HINH DANG (CAO_NGUYEN / CAI_GAI / HON_HOP / KHONG_CO_LAI) = NHAN
Tang 2 XAC NHAN  thu_luoi tren o chon (xac_nhan, 1 phep thu)            -> o tot nhat cua quet chi la mot LUA CHON, chua phai phep do
Tang 3 TRONG TAI MT5 tester Model=0/4 chi cho o da qua tang 2           -> EA tham chieu / ea_tho_chay
Niem phong MOT lan, luat cu (lai sau phi + maxDD < 80%, phi do duoc)
```

| De xuat | Quyet dinh | Ly do |
|---|---|---|
| Nhan C cho engine luoi | **XONG** | muc 1 |
| `quet_luoi` (ca luoi trong MOT goi LLM) | **XONG** | thay vai chuc goi LLM bang 1; moi o dem la 1 phep thu; het gio -> CHUA_DO_DUOC |
| MT5 che do Optimization (cac agent song song tren moi nhan) | DE XUAT, chua lam | cach duy nhat dung het nhan cho MT5. Nhung "o toi uu" la cuc dai chon tren cung du lieu = LUA CHON -> chi de loc, roi chay lai MT5 don + doan xac_nhan. Can: do s/lan truoc; viet bo doc ket qua toi uu (cloud lam duoc khi may nha gui 1 tep mau) |
| Slot 2 (ban cai XM MT5 rieng `656C3515...`) | LAM SAU buoc do | `SLOT_TESTER.md`; chi gap doi neu hai terminal khong chen nhau - do truoc |
| numba / vectorbt / backtrader | KHONG | luoi / martingale phu thuoc DUONG DI (lenh dang mo, TP / stop-out tung bar, lot nhan len); vector hoa khong mo ta duoc. Nhan C da la "numba" cua minh va khop tung bit |
| Rust / GPU | KHONG | C da dua 1 o ve ~12 ms; GPU chi co loi khi quet > 100.000 o, ma moi o la mot phep thu |
| cTrader CLI (Docker, Linux, song song) | CHUA | MOI EA cong khai la MQL5 -> phai dich lai; chi lam MOT spike neu hang cho tester > ~6 gio/ngay (`NGUON_NGUOI_THANG.md` muc 6) |
| TradingView / Pine | KHONG de test | khong co tester ban duoc; chi la nguon ma y tuong |
| Toi uu may nha: loai tru Defender cho thu muc du lieu MT5 + repo, plan "High performance", du lieu MT5 + `data/` tren SSD, EA khong `Print` / khong visual | LAM, nhung de DO | thuong co loi, **chua do tren may nay**: so truoc / sau bang cot `giay`. Dung `b may` (quet + do + den xanh/vang/do + so tai khoan MT5 toi da): `tai_lieu/MAY_NHA_TOI_UU.md` |

## 4. Viec o may nha (theo thu tu; cai nao hong thi dung o do va bao cloud)

```
git pull
pip install ziglang                    # CHI neu khong co trinh bien dich C (mot lan, ~80 MB)
python -m nhan.luoi_nhan trang-thai    # nhan C dung duoc + tu kiem khop; neu khong -> tu dung Python (cham hon, so y het)
python -m nhan.luoi_nhan do 190000     # ghi mili-giay / lan danh gia -> gui cloud (b cau noi)
python -m pytest -q test_luoi_nhan.py test_quet_luoi.py test_luoi_quy_cach.py
```

Sau khi co bar that (`b khoi-phuc`, XM demo): `b nc cc quet_luoi '{"ma":"AUDCAD","khung":"M15","co_dinh":{"tran_tang":12,"tp":10},
"luoi":{"buoc":[8,10,12,15,20,25],"he_so_lot":[1.0,1.1,1.3],"kieu_lot":["nhan"],"che_do":["mua","ban","hai_chieu"]}}'` (vi du; do thoi gian that).
Lan `ea_tho_quet` dau tien: doc cot `giay`, ghi vao muc 1 cua file nay.

## 5. Dieu can nho

- Bien moi truong: `LUOI_NHAN=py|c|auto` (mac dinh auto), `LUOI_NHAN_CACHE`, `LUOI_NHAN_CC`, `NC_QUET_LUONG` (so luong quet, mac dinh min(6, nhan - 2)).
- Doi hanh vi engine: sua `luoi._mot_ro` TRUOC, dich lai `luoi_nhan.c` SAU, chay `test_luoi_nhan.py` (so sanh tung bit). `luoi.PHIEN_BAN_ENGINE` vao van tay -> khong tai dung ket qua cu.
- `quet_luoi` khong co tham so `doan` (chi kham_pha); het gio (`ngan_giay`, mac dinh 900) -> quet do dang = CHUA_DO_DUOC, khong nho lai, khong doc hinh dang.
- Engine luoi CHUA doi chieu voi MT5 tester (xem `NGUON_NGUOI_THANG.md` muc 9): nhanh va khop Python **khong co nghia** la khop MT5.
