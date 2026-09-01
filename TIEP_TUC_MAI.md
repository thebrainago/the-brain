# TIEP TUC NGAY MAI — chot phien 2026-09-01 19:17

Phien 01/09 toi: QUANTLAB nhanh 2,6 lan + BANKER noi lai FRED.

DA LAM
1. TOC DO QUANTLAB - profile truoc, khong doan. Ba diem nong deu khong o cho de nghi:
   - supertrend 14% ca luot (vong lap Python truy tung phan tu mang numpy)
     -> list thuan + 'x != x': nhanh 7 lan, ket qua GIONG HET tung phan tu.
   - mde_cua 17% (cache dia co, nhung phai nap lai du lieu de tinh van tay moi
     tra cache duoc) -> nho trong tien trinh, TTL 300s.
   - toan_hang 30% (tinh lai cung mot rsi14/ema20 hang tram lan tren cung khung)
     -> nho gan theo doi tuong khung, don bang weakref.
   - Quet SONG SONG: tach quet (thuan tinh toan) khoi dang ky (cham so FDR).
     Dang ky O LAI tien trinh cha vi so FDR NHAY THU TU (LORD giam 1/j^1.6).
   DO DUOC, cung 150 giay: 8.400 -> 12.810 -> 21.982 to hop = 2,6 lan.
   So tien trinh: 1->2 duoc 1,47x nhung 4->10 chi them 1,18x. MAY NGHET BANG
   THONG BO NHO, khong nghet CPU. => VPS nhieu nhan hon KHONG cho nhieu hon bao
   nhieu; muon cay that thi chay NHIEU MAY DOC LAP, moi may mot mang tai san.

2. BANKER - FRED bi bo roi 17 ngay vi USER-AGENT CUA CHINH TA. FRED tra 200 khi
   khong gui UA va treo het timeout khi gui UA Chrome; _tai gan cung UA cho moi
   dia chi va nuot ngoai le -> 'khong tai duoc' -> ma nguon ghi 'FRED bi chan tu
   mang nay'. Vi mo 7.262 -> 100.054 diem, lich su tu 1976. Che do 6 -> 10.

3. dieu_phoi/evolution: phan biet MAY TAT voi HE CHET (truoc gan cung
   'khong_xac_dinh' va dem gio chu du an tat may thanh gio he chet). Cat gian
   doan ve trong cua so 7 ngay. ty_le_song nay kem mau so gio_do_duoc.

4. do_im_lang: nguon cam nay noi kem VI SAO. Tra 39 tai lieu ve dung khoa nguon.

5. nhan/so.py: chot chan 'mot gia thuyet cham holdout MOT lan' chuyen tu 4 CHO
   GOI ve CHO GHI (ghi_ket_qua nem ChamLaiHoldout).

LAT NGUOC MOT KET LUAN CUA CHINH PHIEN NAY
Sang toi de nghi 'bat buoc do LUC truoc khi dang ky phep thu' nhu viec so 0.
Profile mot luot that cho thay CONG DO DA CO VA DANG CHAY: mot luot quet 8.400
to hop -> 1.622 ung vien -> 1.589 bi loai vi thieu luc (98%) -> dang ky 0.
Phe u KHONG con tieu ngan sach FDR cho phep thu vo vong. De xuat do la THUA.

=> RANG BUOC THAT khong phai CPU va khong phai ngan sach FDR, ma la MDE: gan
   nhu moi ung vien deu co Sharpe kham pha thap hon muc nho nhat ma du lieu
   hien co phan xu duoc. Tang toc do chi lam quet duoc NHIEU HON, khong lam ha
   MDE. Muon co san luong that thi phai HA MDE: du lieu dai hon, cong cu chi
   phi thap hon, hoac gop lop (da thu: chi ha 0,535 -> 0,511).

VIEC TIEP THEO
1. Huong chinh: HA MDE, khong phai tang CPU. Xem lai kho du lieu dai va lop
   chi phi thap truoc khi mua them may.
2. Ba nguon CHAY_SACH_MA_RONG chay tay: etoro, semantic, blog.
3. Bat Chrome CDP roi chay lai fxblue + quantconnect.
4. Dao kho luu tru blog (WordPress /wp-json): ~2.900 bai so voi 331 bai RSS.
5. BANKER con 3/4 phan: hoc giao trinh+CFA, thu thap nhan dinh (Bloomberg/COT/
   BofA), va muc Viet Nam (hien chi co 3 chuoi World Bank theo NAM, qua tho).
   Phan 'du doan tai san' dang bi trụ tu cam - noi luat hay khong la quyet dinh
   cua chu du an.

839 test qua. Da dung sach 24/7, 0 tien trinh mo coi.

## Trang thai do duoc luc chot
> May tu dien phan nay luc `b ket`. **Dung sua tay** — sua thi mai het so sanh
> duoc. Cot "doi" so voi moc 2026-09-01.

| chi so | hom nay | doi |
|---|---:|---:|
| file test (lab) | 63 | +2 |
| ham test (lab) | 840 | +17 |
| file test (ds/) | 82 |  |
| bang gia .parquet | 252 |  |
| dong so FDR | 1799 | +1 |
|   trong do bac bo | 404 |  |
| ung vien xep hang | 555 | +6 |
| ban doc da thu | 3273 | +63 |
| co che trong thu vien | 32 |  |
| van de con mo | 16 | +1 |
|   muc NANG | 5 |  |
| viec dang CHO | 0 |  |
| file .py o goc lab | 141 | +2 |

- co DUNG_LAI: **CO (he dang nam im)**
- viec CHO theo loai: khong con
- commit hom nay:
```
0ea6839 QUANTLAB nhanh 2,6 lan: 3 diem nong + quet song song
abe0ca5 BANKER: noi lai FRED (12 seri chet 17 ngay vi User-Agent cua chinh ta)
abd0f57 ban giao 01/09: dien doan tom tat phien + muc 0 (do luc truoc khi tieu suat FDR)
ce18633 2026-09-01: Phien 01/09 chieu: vá lớp 'số 0 câm' + chuyển chốt chặn chạm holdout về chỗ ghi.
6801d27 do_im_lang: noi ly do cam + chot chan cham lai holdout ve cho ghi
7d96b4a NGHI doc duoc BAN DO cua QUANTLAB, va chia han ngach cho hai nguon dau vao
a55d2dc noi DeepSeek qua cc-switch (khoa da co san tren may), va sua test do
b2afaaf duong Claude cho tri_tue, sua ten nguon blog, va mot bai kiem chan lop loi cua toi
787943d van dia cho tester: tick that an 757 MB/12 gio va tu khoa lai cong cua chinh no
219c2d6 giai quyet hai muc ton: thu hoi ban khong doc duoc, va EVO TAI VE chu khong chi tim
22b2082 doc van xuoi: bo bao dong gia cua bo phan loai cau luat
995129f bo doc lan duoc BIEN CO NHO va CONG TAC CAU HINH
8cfab0f toan tu CO NHO, phan biet strategy/indicator, va soi lai trang dau moi luot
3ecde6e sua bo tim GitHub cua EVO: no van tim duoc, chi la khong ai doc duoc ket qua
73643be duong trung binh lam muot duoc MOT TOAN HANG, khong chi mot cot gia
3bb8f11 them 9 toan hang, chon theo SO LAN do duoc trong ma that
643fb95 doc_ma: dich duoc "so gia voi MUC DUOC TINH RA" - Bollinger, kenh, pivot
fd6ab0e SEEKER dung chuan: doc CHIEN LUOC THAT thay vi nhat manh, va them toan hang tuyen tinh
09396fb doi tai san thi tham so phai doi theo - quy doi bang ATR, khong bang gia
1be22ed mo rong lo thu thap: 30 -> 92 tu khoa co che
33b0128 khu trung co che theo DIEU KIEN, khong chi theo TEN
cebc1b5 lo viec tu chay mot tieng: don vao Pine (suat rut cao nhat) + thu hoi toan kho
9ea7e17 chay song song nhieu MT5: theo doi TUNG cai dat, va bat ban sao LiveUpdate
bb07521 day chuyen EA: tai .mq5 that -> bien dich -> tester (chu du an bo rao an ninh)
dc50b64 lay MIEN QUET cua chinh tac gia tu khai bao input (khong chay ma cua ho)
ffbe998 truc NEN: Heikin Ashi lam TIN HIEU, khop lenh van o gia that
c763beb sua phieu chuyen doi: doc MA thanh nhieu kieu danh, bo tran 2, mang tham so theo
48dfbe6 TradingView lay thang ma Pine, va LOP THU HOI PHAN DUNG DUOC cua he bi loai
3a06591 vd_p_ung_vien_lech_null: DA TACH bang moc null do that
9447451 thuoc do nang suat: do dung duong V2 dang chay, va xep hang doi doc theo no
0888a13 hieu chuan p_placebo bang chuoi null, va dong hai van de NANG da cu
68f0cb4 seeker: phan trang that + con tro bien gioi, va doi thuoc do sang nang suat doc
```
- file dang doi luc chot: **11**

## Mot doan doc la hieu ca phien

Phien nay lam QUANTLAB nhanh **2,6 lan** (8.400 -> 21.982 to hop trong cung 150
giay) va noi lai FRED cho BANKER (vi mo 7.262 -> 100.054 diem, lich su tu 1976).
Nhung ket qua quan trong nhat lai la mot ket luan bi LAT NGUOC, va la ket luan
cua chinh toi vai gio truoc do.

Sang nay toi de nghi, va viet len dau ban giao, rang phai "bat buoc do LUC truoc
khi dang ky phep thu" vi hon nua ngan sach FDR da di vao nhung phep thu co
p > 0,5. Chieu profile mot luot THAT thi thay **cong do luc DA CO VA DANG CHAY**:
  8.400 to hop -> 1.622 ung vien -> 1.589 bi loai vi thieu luc (98%) -> DANG KY 0.
Phe u khong con tieu mot suat FDR nao cho phep thu vo vong. De xuat cua toi la
thua, va no thua vi toi doc so LICH SU roi noi ve HIEN TAI.

Dieu do doi huong ca du an mot buoc: rang buoc that khong phai CPU, va cung
khong phai ngan sach thong ke, ma la **MDE**. Gan nhu moi ung vien deu co Sharpe
kham pha thap hon muc nho nhat ma du lieu hien co du suc phan xu. Chay nhanh gap
10 lan chi lam ta quet duoc nhieu hon chu khong ha MDE xuong mot chut nao - tuc
nhan mot so 0 voi mot so lon hon.

Cung vi the, cau tra loi cho "co VPS thi cay nat may duoc khong": do duoc rang
1->2 tien trinh duoc 1,47x nhung 4->10 chi them 1,18x. May nghet BANG THONG BO
NHO chu khong nghet CPU. Mot VPS nhieu nhan hon se khong cho nhieu hon bao
nhieu; muon dung tien mua thong luong that thi phai chay NHIEU MAY DOC LAP, moi
may mot mang tai san rieng.

Bai hoc chung cua ca ngay, gap lai lan thu tu: mot so 0 doc duoc thanh mot cau
tra loi. Hom nay no xuat hien o nguon "khong thu duoc gi" (lech ten khoa), o
FRED "bi chan" (user-agent cua chinh ta), o gio "he chet" (that ra la may tat),
va o chinh cai thuoc do toi viet de bat loai loi do.

## Viec tiep theo, theo thu tu

0. **HUONG CHINH DA DOI: ha MDE, khong phai tang CPU.**
   Toc do da xong (2,6 lan) va no khong giai quyet gi ve san luong: 98% ung vien
   chet o cong do luc. Ba duong ha MDE, xep theo cai da biet:
     - du lieu DAI hon (da do: chuoi D1 dai ha nguong 1,4 -> 0,54)
     - cong cu CHI PHI THAP hon (da do: ban do chi phi lien san chenh 5,5 diem
       %/nam cho cung SP500 - la phep TRU khong ton slot FDR)
     - gop lop (da thu: chi ha 0,535 -> 0,511, khong cuu duoc)
   Truoc khi mua them may hay mo them nguon, tra loi cau nay truoc.

1. **Ba nguon CHAY_SACH_MA_RONG - chay tay xem nuot o dau:** `etoro`,
   `semantic`, `blog`. Hai nguon con lai da ro: `fxblue` + `quantconnect` chi
   doc duoc qua Chrome CDP (`b trinh-duyet`).

0. **CAN CHU DU AN GAT: do LUC truoc khi dang ky phep thu.**
   Hien moi gia thuyet vao pheu deu tieu mot suat FDR, ke ca gia thuyet ma du
   lieu hien co khong the nao phat hien duoc. Ket qua do duoc: hon nua ngan
   sach da di vao phep thu co p > 0,5.
   De xuat: tinh MDE truoc: neu edge nho nhat co the phat hien lon hon bat ky
   edge hop ly cua gia thuyet do thi **do thoai mai nhung truyen `ghi_so=False`**
   — khong tieu suat. Ha tang da co san (`do_luc.luc_hai_chang`,
   `gop_lop.mde_gop`, `nhan/mde.py`), chi chua bat buoc tren moi duong.
   Day la thay doi lon nhat dang cho, va no doi hanh vi cua ca pheu nen khong
   tu lam.

1. **Ba nguon CHAY_SACH_MA_RONG — chay tay xem nuot o dau:** `etoro`,
   `semantic`, `blog`. (`b` -> hoac goi thang ham trong `tru/seeker.py`.)
   Hai nguon con lai da ro: `fxblue` + `quantconnect` chi doc duoc qua Chrome
   CDP, bat trinh duyet len roi chay lai (`b trinh-duyet`).

-2. **CHAY TIEP luot 2500 null** (bi cat khi tat may toi 31/08, moi xong 2/23):
   ```
   b hinh-dang --ma $(doc reports/_shortlist_hinh_dang.txt) --null 2500 --tran-o 81 --ra sau2500 --tiep
   ```
   (hoac chay lai dung lenh PowerShell trong BAN_GIAO_SONG.md). Moi ung vien
   ~2.000 giay; 21 cai con lai ~2 gio tren 6 luong. Hai ket qua dau da co:
   `EURGBP.D1.cuoi_thang.truoc1_sau4` p=0,0728 va `truoc2_sau2` p=0,0504 —
   **ca hai deu KHONG qua nguong Bonferroni** (0,05/115 = 0,00043), tuc luot sau
   dang xac nhan ket luan am cua luot truoc chu khong lat nguoc no.

-1. **SUA DO SAU QUET CUA SEEKER — day la lo hong lon nhat dang mo.**
   Chu du an nghi ngo va do lai thi DUNG: `tru/seeker.py::n_mql5_code` chi goi
   DUNG HAI URL (`/en/code/mt5/experts` va `/en/code/mt5/indicators`), **trang 1,
   khong phan trang**, roi cat con 30 link. Ca kho MQL5 Code Base thu ve duoc
   **35 tai lieu**; TradingView 101. Khong nguon nao can ca — he doc di doc lai
   trang dau nen tu lan hai tro di khong thay gi moi, va bao "vong lap rong 84%".
   Chan doan cu cua EVO ("chu ky nguon qua day") la SAI.
   Phai lam: phan trang that cho MQL5 (4 danh muc x nhieu trang) va TradingView,
   cong mot CON TRO BIEN GIOI ghi da quet toi trang nao de moi luot di TIEP.
   Va doi thuoc do cua SEEKER tu "so tai lieu" sang **"so co che duoc cong chap
   nhan tren 100 bai"** — nang suat doc hien la ~1% va da co lan AM (mot ban doc
   sai che ra edge Sharpe 0,822, 4 co che phai thu hoi).

-0. **EVO: phien kham hang ngay** (chu du an da nhat tri). Dau ra khong phai
   danh sach ma la BENH AN CO THU TU: moi van de kem bang chung du de bat tay
   sua (file nao, dong nao, so do nao sai), phan loai "lam sai KET LUAN" hay
   "chi lam cham may", xep theo cau hoi duy nhat: *khong sua thi ket luan nao
   cua du an dang sai?*. Chia viec dut khoat: EVO tu sua phan may moc (nguon
   chet, tien trinh chet, don o dia, noi day mot ham chua ai goi); phan dong
   vao CONG / SO FDR / CHI PHI / NGU PHAP thi CHI nguoi (Claude trong phien)
   duoc sua — mot AI vua ra de vua cham bai vua sua thuoc do la cach nhanh nhat
   de co mot he tu khen minh. Gan luon phan DON DEP vao phien kham nay (xoay
   vong log 7 ngay, nen van ban, xoa cache trinh duyet, canh bao o dia thap).

-0b. **Ba van de muc NANG lam hong KET LUAN — sua truoc khi do them cai gi:**
   `vd_p_ung_vien_lech_null` (phan phoi p cua ung vien khong phai phan phoi
   null), `vd_cong_loai_sach_fdr` (cong loai ca 8 gia thuyet da vuot FDR),
   `vd_null_qua_nho` (nha may null qua nho de ket luan). Thuoc con cong thi do
   gi cung phi.

0. **Bat he 24/7** (`b chay`). Chu du an muon xay chac truoc, va buoc nay tieu
   suat FDR vinh vien nen chi bat khi co nguoi ngoi may.
1. **`auto_follow` tu join nhom.** Ma da co san (346 dong: X, subreddit, kenh
   Telegram, YouTube, TradingView) va chua ai goi. No thao tac tren TAI KHOAN
   THAT — de chu du an bam nut. Da kiem: x/facebook/youtube/mql5 DA dang nhap,
   tiktok va reddit chua.
2. **O dia con 14 GB** — EVO da bao (`dia_thap`). Duoi 15 GB thi buoc kiem tick
   MT5 bi khoa, tuc he tu chan buoc quyet dinh cua chinh no. Phan du an chi
   chiem 4,5 GB (backups 344 MB / ho so Chrome 1,7 GB / data 769 MB /
   reports 1,4 GB) — cho can don nam ngoai du an.
3. **`quant_plan.py` van chua ai goi.** `quantlab` import ma khong dung ham nao;
   dang ky that di qua `so.dang_ky_gia_thuyet` voi plan_hash **khong phu LUAT
   QUYET DINH lan KHONG GIAN TIM KIEM**. Doi the he cong hoac noi rong luoi deu
   khong lam doi hash. Sua doi ca danh tinh gia thuyet lan chuoi FDR.
4. **Doc ky 4 kho vua nhat** de DOI CHIEU voi cong (khong thay): `zipline`
   (20.041 sao, slippage model), `oos-lab` (haircut Sharpe), `deflated-alpha`,
   `skill-backtest-overfit` (Minimum Track Record).
5. **455 bai con cho doc toan van**, va **220 ban `khong_doc_duoc`** (gan het la
   `doi.org` — tuong phi that).
6. **Facebook con mong** (10 bai): trang tim kiem cua no gan nhu khong tra link
   bai, khac X. Can cach khac.
7. Muc cu con nguyen: `vuon_nguon.mot_luot_tim` (~100 ten chua thu),
   103 viec `kham_pha_theo_mau` dang cho, `bao_dam_spread` cho nhom chi so.

## Khong duoc quen (bo sung cho ban 23/08)

- **`kho()` chon ban theo DO PHU, khong theo byte.** Them mot file vao `data/`
  co the doi ban duoc chon cua ca mot ma. Cache mang ten file nguon nen no tu
  het han — nhung ket qua backtest cu thi khong.
- **Mot ma co ban `san` thi ban `ngoai` cung ten bi loai.** Do la cai chan
  `us500cash_daily` (thuc ra la Yahoo ^GSPC) khoi ma US500CASH (CFD).
- **Cung muc gia KHONG co nghia la cung chuoi.** Ba file `*_daily_dai` lech gia
  0,24-0,36% nhung tuong quan loi suat ngay chi 0,08-0,14.
- **Chi phi do o khung RIENG** (`du_lieu.khung_do_spread`), khong phai khung
  chay backtest: ban D1 dai nhat thuong khong co cot spread.
- **Do dac phai goi `ghi_so=False`.** Bat ky duong nao goi
  `cong.xet(tren_holdout=True)` tren du lieu tong hop deu phai truyen co nay.
- **`chay_pheu` khong truyen `df` = chi co TRAIN.** Muon ca chuoi thi noi ro
  `cham_holdout=True`.
- **Bo test cham duong FDR phai dat `SO.DB` sang CSDL tam.**
- **`CTrade trade;` co trong MOI tien ich quan ly lenh.** Ranh gioi chien luoc /
  tien ich la **MO VI THE MOI** (`bien_dich_ung_vien.loai_ma_nguon`).
