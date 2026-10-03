# RA SOAT KIEN TRUC 03/10/2026

> Phien cloud, may nha tat (khong MT5, khong `data/`, khong `nao.db`). Moi so duoi day DO LUC VIET tren ma nguon, 22 EA that
> trong repo (`mau_thu/` 10 file + `reports/ea/kho.json` 12 file) va so cai git. Cai gi can may nha thi ghi **CHUA DO**.
> Chu du an hoi: *"nhanh tim kiem rat don gian: tren mql5 va myfxbook co nhieu link cong khai da co hieu qua -> boc tach logic
> -> tao thanh chien luoc -> backtest roi tinh chinh. Y tuong nay da co trong he thong ma chua phat huy duoc"*.

## 1. Tra loi ngan

Y tuong dung va **da co** - nhung nam thanh BA MANH khong noi voi nhau. Moi manh do duoc la thay cho no ro o dau:

| | Manh | Nam o | Ro o dau (do 03/10) |
|---|---|---|---|
| A | Ho so tin hieu cong khai -> **kieu danh** | `tin_hieu_mql5`, `dau_chan`, `luan_dau_chan` | Chay duoc, ra dau moi that (AUDCAD luoi/DCA, holdout +13,26%/nam). Nhung **khong khoi phuc duoc dieu kien VAO**: duong tai + MFE/MAE chi noi *khi nao* vao, khong noi *vi sao* (chinh docstring `tin_hieu_mql5`). **Myfxbook khong co adapter**: chi la mot dong "trang chu" trong `NGUON_TRINH_DUYET` (ghi chu: `SSLError khi bat tay`); danh sach lenh cua trader khong bao gio duoc lay. MQL5 Signals cung vay: seed la trang chu, can Chrome CDP (dang TAT). |
| B | File EA cong khai -> **boc logic** -> DSL -> backtest | `doc_ma`, `boc_llm`, `ngu_phap` + pheu | Cho hep nhat: **12.078 tai lieu -> 285 co che (2,4%) -> 18 mau (0,15%)**. Tren 22 EA that: 44 diem vao lenh, ra **7 co che**, tat ca tu **3/22 EA**. Bai do `mau_thu/do_moc.py` (10 file): 0 (18/09) -> **2/22 = 9,1%** (03/10); 12 file `kho.json`: 5/22. **8 EA breakout khoang gia / ORB** (loai don gian nhat; 6 trong `mau_thu/`, 2 trong `kho.json`) ra **0**. Ly do: dieu kien vao nam trong BIEN TRUNG GIAN va TRANG THAI (`Tradesinfo.initup`, `lowrange/highrange`, `hedgeprice`, `PositionSelect`) ma DSL "vao theo dong bar" khong co. |
| C | Chay **thang** EA tren MT5 roi tinh chinh | `ea_tu_dong.py` (01/09) | **Mo coi** den 03/10: khong biet EA nao la chien luoc (**5/12 EA mau la cong cu**: replay, dong ro, dong ho, giam sat spread, bang tay), khong biet chay ma/khung nao (tung dat EA co phieu AAPL len EURUSD), khong doc bao cao thanh so, khong co doan du lieu / niem phong. |

**Duong chinh cua nc di nguoc so do.** So do dong 38/55/60: *"co file mql5/ea thi dung luon · backtest LUON file co san truoc · tat ca
phai test tren phan mem trade"*. Code: co che -> DSL -> engine Python -> niem phong -> xuat `.mq5` ra tester **o cuoi**. Manh B bi ep chui
qua cai pheu hep nhat (2,4%) truoc khi duoc cham, con manh C - rong nhat va dung y chu du an - bi bo. Day la loi **thu tu**, khong phai loi
mot module.

## 2. Da sua 03/10 (commit `f58e662`): LAN EA THO - dua manh C ve vi tri dau tien

`nhan/ea_tho.py` + `nhan/bao_cao_mt5.py` + 4 cong cu `b nc cc ea_tho_kham|chay|quet|tinh` (huong dan: `LAN_EA_THO.md`).
Quyet dinh bang code thuan (test duoc tren Linux, 46 test, may tester gia): phan loai CHIEN_LUOC/TIEN_ICH theo do thi goi tu `OnTick`,
chon ma/khung tu bang chung (thieu thi **bo qua**, khong thay the), luoi tham so nho quanh MAC DINH cua tac gia, cua so ngay lay tu
`so_cai/doan.json`, cong **co lai sau phi + maxDD < 80%**, niem phong MOT lan (toi da 3 lan / dong gia thuyet), hong ha tang
**khong** tieu mot lan mo va **khong** lo so.

**CHUA kiem voi may that** (xem `LAN_EA_THO.md` muc HIEU CHUAN): lenh mo cuoi cua so, nhan bao cao tieng Viet ngoai 8 nhan da biet,
do sau tick that cua XM demo, va chinh `_chay_that`. Cho den khi hieu chuan xong, moi `DAT` mang nhan "CHUA hieu chuan".
Cloud **khong the** backtest bat ky thu gi that: khong co gia, khong co MT5.

## 3. Doi chieu so do -> ma (so do la SAN, khong phai TRAN)

| So do | Yeu cau | Ma | Trang thai |
|---|---|---|---|
| dong 35 | tim trader/he thong co lich su: mql5 signal, bang xep hang, quy, myfxbook | `tin_hieu_mql5` (trang signal cong khai, duong tai + MFE/MAE) · `n_fxblue`, `n_etoro` | **MOT PHAN**: MQL5 co; Myfxbook / Collective2 / ZuluTrade / Darwinex chi la trang chu (can CDP), khong co ho so/lenh |
| dong 38 | file mql5/c++ EA thi dung luon | `ea_tho` (moi) · `ea_tu_dong` (cu, mo coi) | **XAY 03/10**, cho hieu chuan nha |
| dong 39 | van ban/video/hinh -> co che | `doc_ma`, `boc_llm`, `doc_chi_bao`, `doc_video_cuc_bo` | Co, nhung ra 2,4%; `doc_video_cuc_bo` mo coi |
| dong 41, 58 | tu lich su suy nguoc ra phuong phap, dung mo phong | `dau_chan`, `luan_dau_chan` (ho so phong cach) | **MOT PHAN**: khong co bo khoi phuc vao-lenh; chua co bo doc danh sach lenh (Myfxbook / MQL5 history) |
| dong 51-52 | quan li lenh quan trong hon entry; tim va boc co che quan li | `quan_tri.py` (18), `pmg*`, `mo_xe_lenh`, `chuoi_quan_tri` | Co. Nhung EA that giu quan li o dang **luoi hoi phuc / gio / hedge co 46 input** (Sniper Gold Hybrid Recovery) - DSL khong boc duoc, `ea_tho` chay nguyen ban |
| dong 55 | backtest file co san truoc | - | **THIEU** trong duong nc den khi co `ea_tho` |
| dong 56 | kiem dinh chi bao dang mui ten / co entry | `doc_chi_bao` (190/389 artifact la chi bao: 49%) | Co (boc dieu kien ve mui ten); khong chay thang chi bao qua `iCustom` |
| dong 57 | co che moi -> dung file chien luoc -> backtest | `xuat_mq5` sau niem phong | Dung nhung **cuoi** duong |
| dong 59 | da cap / da khung / da phuong phap quan li | `thu_luoi`, `quet`, `ea_tho.chon_ma_khung` (<= 3 ung vien co bang chung) | Co |
| dong 60 | tat ca test tren phan mem trade | nc: engine Python truoc, MT5 sau | **Nguoc** (chu dich: MT5 la 1 slot vat ly); `ea_tho` luon MT5 |
| dong 64, 66 | noi sinh; luong uu tien | `tim_quy_luat`, `uu_tien.py`, `b nc hoi` | Co |
| dong 68-69 | EVO giam sat; FINDER | `tru/evolution.py` (1393 dong), `tru/finder.py` (442 dong) | Co - **chua ra soat tac dung** dem nay |

## 4. Giai phau pheu (vi sao 2,4%)

- 12.078 tai lieu / 8 nguon: github 3.309 · openalex 1.828 · crossref 1.485 · **mql5_code 1.168 (9,7%)** · tradingview_pine 696 · ...
  Hoc thuat (openalex + crossref) = 3.313 = **27,4%** so tai lieu, gan nhu **0 co che** (30/08: openalex 6% ra artifact, arxiv 0,8%,
  co che 0/414). Da ha uu_tien tu 30/08 - nhung van la 1/4 kho.
- **mql5_code chi 9,7% kho nhung la nguon DUY NHAT mang EA nguyen file** (vao + ra + quan li). No o `uu_tien` 2, duoi github /
  lean_algo / tradingview_pine (1); mql5.com cam IP sau ~50-150 request; **cloud khong ra duoc mql5.com / myfxbook.com** (proxy 403) nen
  viec lay phai o may nha, toc do thap. 4.125 tai lieu con cho doc.
- Moi thu tren la **vao qua cong boc bang regex/DSL**: 22 EA that -> 7 co che. Trong 12 EA `kho.json`, 5 la cong cu (khong co vao-lenh
  tu dong) - loai dung, khong phai that bai cua bo boc. Con lai: breakout khoang gia / ORB (8 EA), luoi hoi phuc (Sniper Gold Hybrid),
  Renko, ONNX (HybridMicrostructure). Mo rong regex khong dua ti le len nhieu: cai thieu la **trang thai** (khoang gia dau phien, co theo
  ngay, dem vi the, lenh cho, last-fill), khong thieu bieu thuc.
- So pheu (12.078 / 285 / 18 / 4.125) la so **truoc 02/10**, lay tu `HO_SO_HE_THONG` va nhat ky; `nao.db` da mat khi cai lai may nha,
  kho se dung lai tu dau - dung so nay lam moc xu huong, khong phai trang thai song.
- Hieu: **chay thang EA** (manh C) bo qua hoan toan cai pheu nay cho moi EA co `OnTick`. Boc logic van can, nhung nen la buoc SAU khi mot
  EA da co bang chung tren tester (doc EA do de ra gia thuyet co che / luoi cho HEPHAESTUS), khong phai cua vao.

## 5. Vai tro module nho (ban do sinh tu ma nguon: `b ban-do`, `b kien-truc`)

- 605 file `.py` · 228 tren duong chay · **20 mo coi that, 19 nam trong `_luu_tru/` (kho cu)** · 1 mo coi song: `nhan/kiem_quy_uoc`
  (co test, chua co cua vao); `nhan/doc_video_cuc_bo` chi script chay tay goi (ha tang hop le). Vet 12/09 (31 mo coi, ke ca kill-switch
  `han_muc`) **da sach**.
- 152 module `nhan/` · 4 module chua xep lop **da xep 03/10** (`ghi_an_toan`, `ho_so_he` -> DIEU HANH; `slot_tester` -> MT5;
  `kiem_quy_uoc` -> KIEM DINH). Hai module moi (`ea_tho`, `bao_cao_mt5`) vao lop NHA NGHIEN CUU.
- Goc `lab/` con **396 file roi**: 196 test (dung cho) · 132 `_*.py` chay tay (de yen / xoa) · **68 no that** (len `nhan/`, doi ten
  `_*.py` hoac xoa). 17 file khong co docstring (11 trong `_luu_tru/`). 43 file > 600 dong: `tru/seeker.py` 2647,
  `nhan/ngu_phap.py` 2359, `nhan/hephaestus.py` 2359, `tru/quantlab.py` 1813, `nhan/san_cong_cu.py` 1600, `b.py` 1458.
- **Khong don dep dem nay**: khong co gi trong so do do mat vi no, va don khi may nha chua khoi phuc se lam diff `b test` mat y nghia.
  Viec rieng, khi co thoi gian: di chuyen 68 file no vao `nhan/` hoac `_luu_tru/`.
- Vai tro trung lap can biet: `ea_tho` (EA nguyen ban, MT5) va `nc_thi_nghiem` (co che DSL, engine Python) **dung chung so tay, doan,
  van tay, niem phong** nhung khong dung chung code - co y: hai nguon so khac nhau khong nen lan trong mot van tay.

## 6. Nen test Linux (de may nha so)

`reports/test_fail_linux.txt`: `pytest -n 4 --dist loadfile` = **2684 pass / 117 fail / 47 skip**. 77 ID fail ca khi chay noi tiep (phan
lon do moi truong: thieu gia, thieu `nao.db`, ten repo `the-brain` != `lab`, thieu bs4, duong `C:/`; ~40 ca he qua cua so lieu rong),
37 ID chi hong khi **song song** (tranh chap tai nguyen). May nha chay `b test`, lay danh sach fail, **ca nao khong co trong file nay = loi
that** (da biet 1, da sua: `khoa_tien_trinh` pid 1). Ba ca da xac nhan co san truoc tay (`git stash`): hai ca `test_ea_tu_dong::VanDia`
(`statvfs('C:/')`), mot ca `test_kien_truc::test_moi_thu_muc_that_deu_da_duoc_khai` (thu muc `the-brain/`).

## 7. Ke hoach theo thu tu

**May nha (khi bat, ~5 gio nua):**
1. Khoi phuc theo `KHOI_PHUC_MAY_NHA.md` (data, `b khoi-phuc`, dong bang `so_cai/doan.json` + COMMIT/PUSH ngay).
2. **Hieu chuan EA tho** (4 diem, `LAN_EA_THO.md`) - cho EA mua-giu mau 60 ngay; luu 1 bao cao that vao `test_bao_cao_mt5.py`.
3. `ea_tho_quet` tren `reports/ea/kho.json` (12 EA, ~7 chien luoc): cho ra **DAT/AM that dau tien** cua manh C. Dem rate-limited.
4. Lay **it** fixture voi toc do thap (tranh cam IP): mot trang lich su signal MQL5, mot trang he thong cong khai Myfxbook, mot trang
   Market cua EA AUDCAD DCA con song. Cloud viet bo doc offline tu fixture; khong cao hang loat truoc khi co parser.
5. Lich 5 phut (`b cau chay`), `b test` -> diff voi nen Linux, bo xuat M1 cua XM demo.

**Cloud (khong can may nha):**
1. Bo doc danh sach lenh / duong tai (offline, co canary tong hop) -> khoi phuc vao-lenh tu **lich su Myfxbook / MQL5** cho truong hop
   ho so co giao dich dong/mo ro (dong 41/58). Chi lam SAU khi co fixture that.
2. **Chi bao mui ten chay thang tren tester**: 190/389 artifact (49%) la chi bao va khong cai nao duoc chay - chi duoc doc chu
   (`doc_chi_bao`, khong module nao sinh EA boc `iCustom`/`CopyBuffer`). EA boc + `ea_tho` se do duoc ca chi bao ve lai (tester la
   thuoc do trung thuc voi repaint). Xay sau khi `ea_tho` qua hieu chuan.
3. Quyet dinh mo rong DSL bang bang chung (khoang-gia-dau-phien, trang thai theo ngay, dem vi the): chi neu so `mau_thu/do_moc.py` va
   ket qua `ea_tho` cho thay manh B dang mat gia tri; neu khong, de HEPHAESTUS lam bien the tu cac EA da DAT.
4. Dich chuyen ngan sach Seeker (mql5_code len `uu_tien` 1, them trang trader cho MQL5 Signals/Myfxbook) - **doi do duoc so lan bi cam
   IP tren moi luot quet tai nha**, khong chinh mu.

**Khong lam:** cao them tai lieu hoc thuat de tim co che · mo rong regex boc khi chua co trang thai · tin DAT nao cua EA tho truoc
hieu chuan · cham niem phong nhieu lan de "vot" ket qua (cap 3/dong gia thuyet).
