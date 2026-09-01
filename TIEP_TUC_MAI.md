# TIEP TUC NGAY MAI — chot phien 2026-09-01 23:31

Phien 01/09 khuya: dong 6/16 van de. Sua goc o TANG DU LIEU (bar NGAY deo nhan bar gio tren 5 ma; bar D1 CFD khong phai bar phien), SO SACH FDR (cot gt_ma chua hai khong gian khoa nen moi doi soat tu 17/08 lang le rong; bat bien khop_ba_tang do sai chieu), PHOI NHIEM HOLDOUT (mot PASS o lan nhin thu 10), va NGU PHAP (bang con thieu giau dung ba toan hang can nhat). Bo test tung bom 60 dong rac vao so cai that - da don va da co conftest canh. BANKER de sau theo yeu cau, nen hieu_chuan_v6 chua ket duoc.

## Trang thai do duoc luc chot
> May tu dien phan nay luc `b ket`. **Dung sua tay** — sua thi mai het so sanh
> duoc. Cot "doi" so voi moc 2026-09-01.

| chi so | hom nay | doi |
|---|---:|---:|
| file test (lab) | 67 | +4 |
| ham test (lab) | 892 | +52 |
| file test (ds/) | 82 |  |
| bang gia .parquet | 252 |  |
| dong so FDR | 1799 |  |
|   trong do bac bo | 404 |  |
| ung vien xep hang | 555 |  |
| ban doc da thu | 3273 |  |
| co che trong thu vien | 32 |  |
| van de con mo | 10 | -6 |
|   muc NANG | 2 | -3 |
| viec dang CHO | 0 |  |
| file .py o goc lab | 146 | +5 |

- co DUNG_LAI: **CO (he dang nam im)**
- viec CHO theo loai: khong con
- commit hom nay:
```
b7ecaeb Ngu phap: bang "toan hang con thieu" da giau dung nhung cai can nhat
3a6b853 Phoi nhiem holdout tich luy: mot PASS o lan nhin thu 10 khong phai mot PASS
f416fa4 So sach FDR: cot gt_ma chua hai khong gian khoa, va bat bien do sai chieu
68e08d8 Tang du lieu: cat doan bar NGAY deo nhan bar gio, va bar theo PHIEN
a0ea502 ban giao 01/09 toi: doan tom tat + muc 0 (huong doi sang ha MDE)
5f3d2e3 2026-09-01: Phien 01/09 toi: QUANTLAB nhanh 2,6 lan + BANKER noi lai FRED.
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
- file dang doi luc chot: **5**

## Mot doan doc la hieu ca phien

Phien nay khong tim ra edge nao. No di go 16 van de con mo va phat hien ra rang
**phan lon chung khong phai van de nghien cuu ma la DUNG CU DO BI HONG** — va
moi cai hong deu hong theo cung mot kieu: mot con so duoc bao cao ma khong ai
kiem lai xem no con dung khong.

  - `khung_that()` lay TRUNG VI ca chuoi, nen 5 ma co doan dau la bar NGAY deo
    nhan bar gio van qua cua (EURUSD/USDJPY 28 nam, US500CASH 5 nam).
  - `fdr.gt_ma` chua HAI khong gian khoa; 0/1124 hang moi khop bang gia_thuyet,
    nen moi phep doi soat tu 17/08 lang le tra ve rong ma khong bao loi.
  - `khop_ba_tang` do sai chieu: no bao do vi 96 gia thuyet FAIL o cong re,
    dung nhu THIET KE, trong khi hai huong nguy hiem that thi khong ai do.
  - `_DIEN_DAT_DUOC` la ban chep tay lech ca hai chieu, nen bang "toan hang con
    thieu" giau dung ba toan hang duoc dung nhieu nhat.
  - bo test bom 60 dong rac vao so cai THAT, moi lan `b test` them ~10 dong.

Cai LAT NGUOC: `quant_pass_quarantine_v2` khong phai "8 ket qua cho retest". Con
mot cai song, va no PASS o **lan nhin thu 10** vao cung mot holdout. Tung buoc
hop le — nguong LORD tut 1,3e-4 -> 5,0e-6 qua bon lan chay trong ho `@cp2`, roi
mo hinh chi phi doi the he 2->3 nen ho tach thanh `@cp3`, `j` ve 1 va nguong noi
**gap 2.600 lan**. Tach ho theo the he chi phi la DUNG THIET KE muc 7. Cai thieu
la khong ai dem TONG so lan nhin holdout xuyen the he: do duoc **3,39 lan moi
gia thuyet**, va 3 gia thuyet di tu FAIL sang PASS qua cac lan cham lai.

## Viec tiep theo, theo thu tu

-1. **KIEM LAI MOI KET LUAN H1/H4 TRUOC 01/09.** Cache khung da bump sang `v2`
   va 5 ma bi cat doan dau (EURUSD/USDJPY 1971-1998, GBPUSD 1993-1998,
   US500CASH 2011-2015, XAUUSDM 2014-2016). Ba trong so do la cap FX duoc quet
   nhieu nhat cua du an. Chua do xem so nao doi.

0. **`hieu_chuan_v6` DANG BI CHAN, va no chan boi mot quyet dinh chu khong boi
   ky thuat.** Dieu kien dau cua V6 la `bias > 0`, ma bias = 0,25 vi mo + 0,10
   VIX + 0,25 mua vu — deu la du lieu BANKER. Chu du an da noi de BANKER sau,
   nen phan nay dung o day. Lop bias da viet xong va cat o
   `archive/vi_mo_CHO_BANKER.py` (doc thang tu bang `vi_mo` trong nao.db, khong
   them nguon moi). Hai dieu kien con lai cua van de do da lam duoc:
   danh muc 3 chi so My, va bar theo PHIEN (`du_lieu.nap_phien` — do duoc: bar
   D1 CFD rong hon bar phien tien mat 1,39 lan, IBS hai ben chi tuong quan
   0,866, 98 ngay kich hoat theo phien ma khong theo D1).

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
