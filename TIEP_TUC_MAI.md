# TIEP TUC NGAY MAI — chot phien 2026-08-31 19:25

hieu chuan HINH DANG bang chuoi null: cong cu + 12 test, va luot chay dem 368 gia thuyet x 100 null dang chay

## Trang thai do duoc luc chot
> May tu dien phan nay luc `b ket`. **Dung sua tay** — sua thi mai het so sanh
> duoc. Cot "doi" so voi moc 2026-08-30.

| chi so | hom nay | doi |
|---|---:|---:|
| file test (lab) | 49 | +3 |
| ham test (lab) | 656 | +93 |
| file test (ds/) | 82 |  |
| bang gia .parquet | 252 |  |
| dong so FDR | 1794 | +17 |
|   trong do bac bo | 404 | +1 |
| ung vien xep hang | 327 | +136 |
| ban doc da thu | 2481 | +52 |
| co che trong thu vien | 32 |  |
| van de con mo | 22 | -5 |
|   muc NANG | 10 | -6 |
| viec dang CHO | 0 | -104 |
| file .py o goc lab | 122 | +6 |

- co DUNG_LAI: **KHONG (he dang chay)**
- viec CHO theo loai: khong con
- commit hom nay:
```
f1d5d2a hieu chuan HINH DANG: cung luoi lan can chay tren chuoi NULL sinh tu chinh no
f3ba6e6 dieu_phoi: canh bao cham lease dung >= chu khong phai ==
0b499d3 nhap tru EVO: mot phat hien = mot van de, va so van de day duoc truy van san
754734c EVO: mot phat hien = mot van de, va so van de day duoc truy van san
e705e99 do_on_dinh: edge la CAO NGUYEN hay CAI GAI — va ung vien PASS duy nhat la SUON DOC
fd6d401 24/7: nguyen nhan goc — dua lease vao os.replace lam supervisor chet moi 4-5 phut
785fc31 24/7: supervisor phai khai bao cai chet cua minh (bit cho 'khong ro nguyen nhan')
8cb430b cong 11 gac duoc khung NGAY: do khe theo THU khi chuoi chi co mot gio
f37eadf cham lai 361 gia thuyet duoi the he cong 5: 83 diem mu da dong, va no lo ra mot PASS
```
- file dang doi luc chot: **23**

## Mot doan doc la hieu ca phien

(dien tay: phien nay tim ra dieu gi, cai gi lat nguoc ket luan cu)

## Viec tiep theo, theo thu tu

-1. **DOC TRUOC: `reports/HINH_DANG_VS_NULL.md`** — luot chay dem 31/08
   (368 gia thuyet x 100 chuoi null x luoi lan can 81 o) da xong hoac dang do.
   Cau hoi no tra loi: **hinh dang cua ung vien that co khac hinh dang cua cung
   luoi do tren chuoi NGAU NHIEN khong?** Doc theo thu tu:
   - dong tong ket dau bao cao: co bao nhieu ung vien dat `p <= 0,05`. Neu 0/N
     thi "cao nguyen" khong phai bang chung ve co che - no la hinh dang cua mot
     be mat tron, va `do_on_dinh` khong duoc dung lam ly do tin mot ung vien.
   - cot `null p95 alpha`: chuoi null cho alpha bao nhieu la binh thuong. Ung
     vien nao co alpha tam THAP HON con so do la da bi null vuot mat.
   - `AUDCAD.H4.rsi_dao_chieu` (ung vien PASS duy nhat, hinh dang CAO NGUYEN)
     phai duoc nhin rieng: luot thu 8 null cho p = 0,111 = dung san do phan giai.
   - Neu tien trinh chet giua chung: `b hinh-dang --het --null 100 --tran-o 81
     --tiep` chay tiep tu cho dang do (JSON ghi lai sau MOI ung vien).
   - Luot thu voi 8 null luu o `reports/HINH_DANG_VS_NULL_thu_8null.md`.

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
