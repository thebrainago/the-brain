# TIEP TUC NGAY MAI — chot phien 2026-09-06 16:31

do ho loi ra 182.550 o -> SAN_SANG_V4 = 0 (chan troi khong phai nut that); sua duong LLM chet; ap cong kiem_khai_bao cho 169 co che da o trong kho

## Trang thai do duoc luc chot
> May tu dien phan nay luc `b ket`. **Dung sua tay** — sua thi mai het so sanh
> duoc. Cot "doi" so voi moc 2026-09-05.

| chi so | hom nay | doi |
|---|---:|---:|
| file test (lab) | 87 | +9 |
| ham test (lab) | 1207 | +106 |
| file test (ds/) | 82 |  |
| bang gia .parquet | 269 |  |
| dong so FDR | 1807 |  |
|   trong do bac bo | 406 |  |
| ung vien xep hang | 567 |  |
| ban doc da thu | 6658 |  |
| co che trong thu vien | 32 |  |
| van de con mo | 12 |  |
|   muc NANG | 3 |  |
| viec dang CHO | 2 |  |
| file .py o goc lab | 214 | +13 |

- co DUNG_LAI: **CO (he dang nam im)**
- viec CHO theo loai: bac_cau_san=1, mt5_tick=1
- commit hom nay:
```
b1888ff 2026-09-06: bao cao phien + anh chup be mat truoc khi don kho
315aea2 do ho loi ra: 182.550 o, SAN_SANG_V4 = 0 - chan troi khong phai nut that
3ac77c9 cong chua tung ap cho hang da o trong kho: 169/540 co che khong qua noi
91c2b49 do spread that cho ca be mat: 44 -> 86 ma giao dich duoc
924c789 cong ngu phap: bi danh chi bao, phep ==, va chan dieu kien hien nhien
```
- file dang doi luc chot: **1**

## Mot doan doc la hieu ca phien

(dien tay: phien nay tim ra dieu gi, cai gi lat nguoc ket luan cu)

## Viec tiep theo, theo thu tu

Chu du an chot thu tu nay cuoi phien 05/09, sau khi doc ket luan "boc tach het
la nut that":

1. **CHAY EA DO CHI PHI TRUOC** (uu tien cao nhat). Ly do chu du an dua ra: EA
   la thu **da duoc chuan hoa**, thay tham so duoc, chay da cap duoc, va la thu
   duy nhat chay tren TICK THAT. `nhan/tien_ich_xet.py` da loc ra tu 58 file
   tien ich: `RealCostSpreadP95LoggerMT5.mq5` (ghi spread that ra file),
   `RoundTripCostReconcilerMT5.mq5` (xuat CSV doi chieu chi phi),
   `spread_lister_current-min-max.mq5`. Muc tieu: nang `do_tin` KHAI -> DO cho
   them symbol. **Day la thu mo khoa cong**; khong co no thi moi thu sau deu
   dung o "canh bac co ky vong duong", chua phai phat hien.

2. **Boc loi ra chuan cho 34 chi bao MUI TEN** roi quet. Mui ten la tin hieu
   vao nhung khong co loi ra. Boc bang: giu N nen (1/3/5/10/20) · SL/TP theo ATR
   (1x/2x/3x) · thoat khi co mui ten nguoc. Mot tin hieu -> mot ho nho chien
   luoc, va biet duoc tin hieu do CAN loi ra nao. Dung lai co che `giu` da co.
   **Bay rieng cua lop nay: REPAINT** - chi bao ve lai mui ten trong qua khu se
   thanh nhin truoc va de ra edge gia rat dep. `kiem_khong_nhin_truoc` la cong
   quan trong nhat cua lan nay, khong phai thu tuc.

3. **Sinh ho gia thuyet chuan cho chi bao THUONG** (34 file kenh/band + con lai).
   Mot chi bao la mot CON SO, chua phai chien luoc. Moi chi bao sinh: vuot nguong
   tuyet doi · cat mot muc · cat trung binh cua chinh no · **phan vi / z-score
   cua chinh no** (quan trong nhat: chay duoc tren moi tai san, con nguong tuyet
   doi thi khong - bai hoc `close >= 4428.1`) · dung lam BO LOC CHE DO cho tin
   hieu khac. Ngu phap da co `zscore`/`phan_vi`, va `luoi_goc` giu dai tham so
   cua chinh tac gia nen khong phai bia luoi.

4. **Xay nguyen thuy `vung` cho FVG / order block / ORB** (dat nhat, mo khoa
   nhieu nhat). Kho dang giu **14 dinh nghia FVG doc lap, 19 order block, 23 cau
   truc/BOS, 13 thanh khoan, 6 ORB** - chua ai so chung voi nhau bao gio. Y cua
   chu du an: tach **DINH NGHIA VUNG** khoi **CACH GIAO DICH VUNG**, giu wrapper
   co dinh roi thay 14 dinh nghia FVG vao -> biet dinh nghia nao chat luong hon.
   Do la ghep he thong that, khong phai nhoi tin hieu.
   Ngu phap hien chi noi duoc so sanh THEO TUNG NEN; mot vung thi CO TRANG THAI:
   `{tao: [dieu kien i-2..i], dinh/day: bieu thuc, huy: dieu kien, song: N nen}`
   + tin hieu `gia cham vung` / `gia bat khoi vung`. **Mot nguyen thuy nay mo
   khoa ca 5 ho (~75 file) dang nam chet.**

**Nguyen tac ghep, chu du an chot:** KHONG ghep tin hieu voi tin hieu (nhan so
phep thu ma tien khong den tu do). Ghep dung la **tin hieu x lop QUAN TRI**
(46 spec ho 2) - cho da co so chung minh: entry tinh SAI van cho 92-97%/nam khi
co lop luoi.

### Vuong mac con lai cua khau boc (chua sua)

- **Cong dang loai ~115 co che chi vi MOT chuoi thu.** `them_co_che` tu choi khi
  kich hoat < 0,2%, nhung no chi thu tren `XM_US100CASH H1`. Tin hieu mui ten
  von la su kien hiem. Luat "chi loai khi suy bien tren TAT CA tai san" da duoc
  ap cho `loc_co_che` nhung QUEN ap cho cong vao kho. Sua cho nay co the tra lai
  mot phan trong 115 cai. **Viec re nhat, lam truoc muc 2.**
- 97/190 file chi bao la loai VE VAT THE - ngu phap chua noi duoc (xem muc 4).
- Bo chan "gia so voi hang so tuyet doi" chi bat mot hinh dang;
  `aapl_call_breakout_above_322_50` van lot vao be mat.
- `test_hien_phap` DO: 7 module cua phien sang chua co test (`cong_ra_tien`,
  `da_thoi_dai`, `dau_chan`, `day_chuyen_quantlab`, `ho_so_symbol`,
  `tin_hieu_mql5`, `tinh_cach`). `test_banker_fred` DO: thieu che do
  `chinh_sach_tien_te`, chua truy.
- 14 file chi bao con `CHUA_DO` (may chu tra HTTP 500), chay lai la duoc.

### Duong LLM (moi tu 05/09)

Khoa goi nap moi nam trong cc-switch profile **"AiBox goi moi (qwen3.7-flash)"**
(tab Codex). `config/tri_tue.json` tro toi no bang `cc_switch_provider="aibox
goi moi"`. Model mac dinh `qwen3.7-flash`, tu dong doi sang `qwen3.6-flash` cho
file tra rong (`doc_chi_bao.MODEL_TANG_1/2`). Gia do duoc: ~160 don vi moi khai
bao giu duoc - RE NHAT trong 8 model da thu. Profile `DeepSeek` tro
`api.deepseek.com` KHONG dung duoc (khoa la khoa ai-box, khong phai DeepSeek
chinh chu).

## KHONG DUOC QUEN (bo sung 03/09)
- `b mang` TRUOC khi san bat cu thu gi.
- **Lam "giong nguoi" qua tay thi phan tac dung**: `requests.get` tran 4/4 =
  200; phien giu cookie + Referer 4/4 = 403.
- `thu_thap` ghi vao bang `artifact`, KHONG vao `tai_lieu`.
- Payload artifact LONG mot tang: ma o `payload["payload"]["content"]`.
- `Accept-Encoding: br` khi khong co brotli -> HTTP 200 nhung `r.text` RAC.
