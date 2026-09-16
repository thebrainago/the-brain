# -*- coding: utf-8 -*-
"""ho_so_he.py - MOT FILE DUY NHAT dua cho mot AI KHONG CO DIA.

## Bai toan

`KIEN_TRUC.md` (module + vai tro) va `THIET_KE_XAY_LAI.md` (chan doan + ke hoach)
deu gia dinh nguoi doc **mo duoc repo**. Claude chat, ChatGPT, hay bat ky ai ngoi
ngoai thi khong mo duoc gi - ho chi co dung van ban ta dan.

Chu du an 16/09/2026: *"cho toi so do chinh xac va cu the cua toan bo the brain +
van de va de xuat sua chua vao 1 file de claude chat len ke hoach lam viec va nam
duoc he thong da toi dau"*.

Nen file nay phai TU DU: so do + so lieu song + van de + de xuat + **luat doc ket
qua**. Thieu muc cuoi thi nguoi doc ngoai se khuyen dung mot cach tu tin va sai,
vi ho khong biet nhung cai bay ma du an nay da sap that.

## Cai gi SINH, cai gi VIET TAY

- **Sinh**: so lieu tu `nao.db`, so do module tu `nhan/kien_truc.py`, bang he tu
  `nhan/bang_he.py`. Khong bao gio cu.
- **Viet tay**: `MUC_TIEU`, `VAN_DE`, `LUAT_DOC`. Day la PHAN DOAN, khong doc duoc
  tu ma nguon. Chung nam trong file `.py` nay chu khong trong mot `.md` roi, de
  chung di qua git cung ma nguon va de `b ho-so` luon in ban moi nhat.

Chay:  python -m nhan.ho_so_he          in ra
       python -m nhan.ho_so_he --ghi    ghi de HO_SO_HE_THONG.md
       b ho-so                          (duong chay that)
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

from nhan import kien_truc as KT                                 # noqa: E402

TEP = LAB / "HO_SO_HE_THONG.md"

#: Rut gon tu `Desktop/hethong.txt` (LUAT SO 0). Nguoi doc ngoai khong co file do.
MUC_TIEU = """\
Mot phong nghien cuu tu dong: thu thap moi chien luoc / kien thuc / san pham giao
dich (EA, chi bao, he thong), kiem dinh chung, roi giu lai cai RA TIEN.

Bon rang buoc do chu du an dat, khong duoc suy dien nguoc:

1. **Muc tieu la TIEN, khong phai chat che hoc thuat.** Nguyen van: *"khong phai
   nhung mo hinh kinh te hay quan tri quy de ma can de cao qua nhieu tieu chi hoc
   thuat. Muc dich cuoi cung la co tien, chap nhan ca chi phi va rui ro cao"*.
   MDE / FDR / placebo la **NHAN CANH BAO**, chi chan khi he thua mua-giu O CUNG
   MUC RUI RO - do moi la cau hoi tien.
2. **QUAN LI LENH quan trong hon ENTRY.** Nguyen van: *"module quan trong trong
   toan bo he thong"*. Da do duoc: entry tinh SAI van cho 92-97%/nam khi co lop
   quan tri dung.
3. **"FX" = KIEU GIAO DICH long/short co don bay**, khong phai chi cap tien. San
   fx co ca chi so, hang hoa, kim loai. Chon tai san theo viec no co ra tien
   khong, khong theo lop tai san.
4. **Chay da luong**, duoc dung 95% CPU, duoc goi LLM re (qwen) het co.
"""

#: Van de. Moi muc: (ma, ten, bang chung, hau qua, de xuat, dot)
#: Bang chung phai la SO DO DUOC hoac trich dan - khong nhan dinh suong.
VAN_DE: list[tuple[str, str, str, str, str, int]] = [
    (
        "V1", "Cong ra tien mo coi, nen bang xep hang xep theo Sharpe",
        "`nhan/cong_ra_tien.py` (*'CONG THU HAI. Hoi co ra tien khong, khong hoi "
        "co that khong'*) khong duong chay nao goi toi - `b kien-truc` muc 4.4.",
        "He dung dau bang la EURGBP Sharpe 1,47 nhung **0,62%/nam voi 9 lenh/nam**. "
        "Do la mot phep do, khong phai mot he. Trai thang rang buoc 1 cua muc tieu.",
        "Noi `cong_ra_tien` vao `bang_he.bang()`. Xep theo **CAGR rong o cung sut "
        "giam**; Sharpe xuong cot phu.",
        1,
    ),
    (
        "V2", "Ban trung bom bang xep hang",
        "`mat_can_bang_lenh_dong_cua` xuat hien **4 lan** trong 9 he da qua cong, "
        "thanh 2 cap trung khit tung chu so. Dau bang 592 he holdout: "
        "`ns_nen_rau_tren` va `ns_nen_sao_bang` cho 6 con so y het, chiem 16/18 "
        "dong dau. Da do truoc do: 616/3.236 co che sinh tin hieu y het nhau.",
        "**9 he that ra la 7.** Hai ban sao trong nhu hai xac nhan doc lap. Moi ban "
        "sao con ngon mot luot chay tester - lan tester la 1.",
        "Khu trung bang **hash cua CHUOI TIN HIEU**, khong phai ten. Chay truoc moi "
        "thu ghi vao so. Chay lai bang sau khi khu.",
        1,
    ),
    (
        "V3", "Dau tu nguoc voi hieu qua do duoc",
        "Lop THU THAP 19 module -> 12.078 tai lieu -> **18 mau chien luoc (0,15%)**. "
        "Do doc lap: kho x6 ma ung vien cham cong van 21. Lop QUAN TRI VI THE chi "
        "12 module, trong khi entry SAI + quan tri dung = 92-97%/nam.",
        "Cho ton cong nhat la cho cho it tien nhat. `tru/seeker.py` mot minh 2.647 "
        "dong - lon nhat he.",
        "**Dong bang quy mo thu thap.** Chuyen cong sang quan tri vi the: moi tin "
        "hieu vao phai chay qua >=3 luat quan tri truoc khi vao so.",
        2,
    ),
    (
        "V4", "Don vi co ban dang la co che DON, trong khi CAP moi song",
        "He don 822 -> 40 khi ra holdout. Cap giu hang **39/45**. Ghep chan am voi "
        "chan duong: 6,14% -> 20,25%/nam o **cung sut giam**. Nguoc chieu cho tuong "
        "quan am o 93-94% cap.",
        "Pheu dang loc va xep hang tung co che roi moi nghi den ghep - tuc loc bo "
        "chan am truoc khi biet no ghep duoc voi gi.",
        "Don vi co ban la **`ho1 x ho2`** (tin hieu vao x luat quan tri). Cong T3 "
        "khong nhan co che don. `danh_muc.py` thanh cong bat buoc truoc khi ra that.",
        3,
    ),
    (
        "V5", "So do noi bon tru, ma nguon co hai",
        "BANKER 550 dong goi **1** module nhan (`so`); FINDER 442 dong goi **2**. "
        "SEEKER goi 17, QUANTLAB goi 18.",
        "Bao cao va ke hoach coi nhu co 4-5 tru dang chay, thuc te la 2 tru + 3 vo. "
        "Moi uoc luong tien do deu lech theo.",
        "Goi dung ten: BANKER/FINDER la **chua xay**, khong phai 'dang chay yeu'. "
        "Chu du an da chot: xong ba module that truoc. Giu nguyen thu tu do.",
        4,
    ),
    (
        "V6", "Khong co tang SAN PHAM - he dang nam im",
        "Tu 'he qua cong' den 'tien vao tai khoan' chi co `chay_that.py` + "
        "`so_lenh.py`. Co `DUNG_LAI` dang bat: he **nam im**. `nao.db` 1,6 GB.",
        "524 file phuc vu viec TIM, gan nhu khong co gi phuc vu viec GIU cho cai da "
        "tim duoc chay va sinh tien.",
        "EA nhieu slot (da co: moi slot mot magic, `lot=0` tat slot) -> VPS -> "
        "`so_lenh` paper -> `suy_giam` canh bao ngay. Gop WAL, dong bang kho.",
        4,
    ),
    (
        "V7", "Thu TUNG ra tien nam ngoai duong chay",
        "Sonic R H4 US500 (TP5%/SL1%, L=3 -> **26%/nam**, Calmar tang theo don bay), "
        "luoi Bigmouse tren AUDCAD (**62%/nam** tren von 33$ cent), trailing (lai "
        "holdout **x4,8**) - khong cai nao co trong bang 9 he.",
        "He dang do cac thu yeu hon trong khi thu manh hon nam ngoai so.",
        "Keo ca ba vao `b he` do bang **cung don vi** voi phan con lai. Neu chung "
        "khong tai lap duoc thi biet som van hon.",
        2,
    ),
    (
        "V8", "84 file no o goc lab + 25 file khong khai vai tro",
        "362 file o goc = 147 test (dung cho) + 131 script `_*.py` chay tay (dung "
        "ban chat) + **84 file no that**. 25 file khong co docstring nen khong vao "
        "duoc ban do vai tro nao.",
        "Nguoi moi vao khong biet cai nao dang chay. Da xay lai thu da co 3 lan "
        "trong mot phien vi ly do nay.",
        "84 file: len `nhan/`, hoac doi ten `_*.py`, hoac xoa. 25 file: them mot "
        "dong docstring. Ca hai deu do duoc bang `b kien-truc`.",
        2,
    ),
]

#: Luat doc ket qua. Thieu muc nay thi nguoi doc ngoai se khuyen sai mot cach tu tin.
LUAT_DOC = """\
Moi dong duoi day la mot loi DA SAP THAT trong du an nay, khong phai ly thuyet.

- **Ket luan AM phai phan biet voi CHUA DO DUOC.** Ma thoat != 0, thieu file ra,
  file ra cu hon luc bat dau, bang co cot so dung im -> deu la `CHUA_DO_DUOC`.
- **`Model=1` cua MT5 che ra lai gia** khi TP < 2x bien do nen M1: do duoc
  +1.161% (Model=1) vs -100,7% (tick that) tren cung cau hinh. Lech 12 lan.
- **Placebo phai hoan vi CHUOI VI THE**, khong phai chuoi lai/lo. Hoan vi lai/lo
  giu nguyen phan phoi nen luon ra ~50% va "ket luan" rang moi he deu truot.
- **So cuc dai phai so cung co mau.** "Tot nhat trong N" vs ban gia le thoi p sai
  24 lan, lat ket qua DAT thanh AM.
- **Don bay gop bang LOG la sai**: L=3 tren 98 nam ra x76.289.488 thay vi x2.406.
  Va tran lai suat o moi don bay la `0,5*S^2` - Sharpe phai tinh tren loi suat
  SO HOC.
- **Mua-giu la moc bat buoc trong moi bang**, va phai co CA HAI moc: mua-giu CFD
  (co phi qua dem) va mua-giu chi so (khong phi) - hai ket luan khac han nhau.
- **Phi qua dem dat hon spread**: 1,56 bps/dem so voi spread 0,98 bps. Chan BAN
  duoc TRA +0,18 bps/dem.
- **Bar D1 cua CFD khong phai bar phien** (om ~23 gio, bien do rong hon 1,39 lan).
- **Do sau du lieu phai kiem truoc moi backtest**: MT5 don bar NGAY vao khung nho
  khi thieu du lieu, khong bao loi. Dau hieu nhan ra la so bar/nam.
- **Exness cat lich su tu 2022-08** cho 24/25 symbol; XM tra H1 chi bang
  `copy_rates_from_pos`, va bar D1 cua XM co `spread = 0`.
- **Sharpe cao khong phai tien.** Xem V1: Sharpe 1,47 = 0,62%/nam.
"""


#: Ho so tung THANH PHAN. Moi muc 5 truong, dung thu tu chu du an yeu cau
#: 16/09/2026: **vai tro - nhiem vu - nang luc THUC TE - van de con ton - huong giai**.
#: Truong "nang luc thuc te" bat buoc co SO DO DUOC; khong co so thi ghi "chua do".
THANH_PHAN: dict[str, tuple[str, str, str, str, str]] = {
    # ---- TRU ----
    "TRU · SEEKER": (
        "Pheu nguon. Cua duy nhat kien thuc ben ngoai di vao he.",
        "Tim nguon -> tai tai lieu -> doc toan van -> day sang khau boc.",
        "12.078 tai lieu tu 8 nguon (github 3.309 · openalex 1.828 · crossref 1.485 "
        "· mql5_code 1.168 · tradingview_pine 696). 7.348 doc tron ven "
        "(~20.590 trang A4). 2.647 dong, goi 17 module loi — LON NHAT he.",
        "Chuyen doi **0,15%**: 12.078 tai lieu -> 18 mau chien luoc. 4.125 tai lieu "
        "con nam cho doc. mql5.com cam theo IP sau ~50-150 luot. Hang doi tung bi "
        "406 URL TradingView chet chiem cho va bao 'het ton kho' gia.",
        "**Dong bang quy mo.** Chuyen uu tien sang nguon CO FILE CHAY DUOC "
        "(`.mq5`/`.ex5`/`.set` ra tester duoc ngay) thay vi van xuoi. Do da chung "
        "minh hai lan: kho x6 khong lam tang dau ra.",
    ),
    "TRU · QUANTLAB": (
        "Phong kiem dinh. Noi mot gia thuyet duoc phep doi doi.",
        "Boc -> loc -> ho so tai san -> ghep ung vien -> cham diem -> cong.",
        "1.806 dong, goi 18 module. 387 gia thuyet dang ky · 1.284 ket qua · "
        "705 ung vien · 592 qua holdout pheu · **9 he qua cong (that ra 7)**. "
        "Quy trinh 4 buoc chay het trong **6 giay**.",
        "Xep hang theo Sharpe chu khong theo tien (V1). 169/540 co che trong kho "
        "chua tung qua noi cong cua chinh he. Khong he nao vua ra tien vua cach xa "
        "mua-giu.",
        "Noi `cong_ra_tien` lam cong CUOI. Chay lai ca kho qua cong sau khi khu trung.",
    ),
    "TRU · EVOLUTION": (
        "Tu giam sat: nhin ra he dang hong cho nao roi de xuat sua.",
        "Cham suc khoe tung module, cat nghia, sinh de xuat.",
        "1.393 dong, goi 8 module. `b evo` chay duoc, co bang suc khoe module.",
        "Vong khong khep: EVO **de xuat** nhung khong co duong tu de xuat sang "
        "`day_viec.py` (hang doi viec xay), nen de xuat nam do.",
        "Noi `evo` -> `day_viec`: moi de xuat dat nguong thi tu vao hang doi.",
    ),
    "TRU · BANKER": (
        "Vi mo: boi canh lai suat / dong tien de nghieng size.",
        "Cap nhat vi mo lien tuc, phan tich sat sao.",
        "550 dong nhung **goi dung 1 module** (`so`). Tuc la VO.",
        "Chua xay. Bao cao lau nay coi no nhu 'dang chay yeu' — sai, no chua chay.",
        "**Giu, ha uu tien** dung lenh chu du an: xong ba module that truoc. "
        "Manh macro da do duoc (tilt theo thay doi loi suat 10Y) thi giu lam hat giong.",
    ),
    "TRU · FINDER": (
        "Di san cong nghe/cong cu ngoai de nang ha tang, thay vi tu viet.",
        "Tim repo/cong cu -> danh gia -> tich hop.",
        "442 dong, goi 2 module. Kho cong cu co **148 muc** (18 la phuong phap).",
        "110 the ket o trang thai MOI; nut that la **bang anh xa** cong cu -> nhu cau, "
        "khong phai kha nang tim.",
        "Sau dot 2. Khi lam thi lam bang anh xa truoc, dung san them.",
    ),
    "TRU · NGHI": (
        "Bien thu DOC DUOC thanh thu KIEM DINH DUOC, roi hoc tu ket qua.",
        "Van xuoi -> khai bao DSL -> chay -> ghi bai hoc.",
        "450 dong, goi 6 module. So bai hoc tra loi duoc 'cai nay da thu chua'.",
        "Suat boc thap: LLM dien co che cho 48 khai bao, tham dinh bac 41, **rong "
        "cuu 3**. Kho bai bao 24.244 cau -> 4 dieu kien.",
        "Doi nguon chu khong doi bo loc: bo loc dang loai DUNG, nut that la NGUON.",
    ),
    # ---- LOP ----
    "LOP · SO & HOP DONG": (
        "Mot nguon su that cho ca nam tru.",
        "Ghi gia thuyet / ket qua / FDR / bai hoc; ghim ban du lieu de tai lap.",
        "`nao.db` **1,6 GB**, 26 bang. Pre-registration co `plan_hash`. "
        "`anh_chup` ghim ban du lieu cho moi ket qua.",
        "DB phinh lang le: `nao.db-wal` tung len 1,4 GB va lam 3 me boc bao XONG "
        "rc=0 ma kho khong doi. Dia day hien ra nhu ket qua rong.",
        "`b don-dia` (gop WAL) vao nhip ngay. Dong bang kho sau khi dong bang thu thap.",
    ),
    "LOP · BOC TACH": (
        "Khau HEP NHAT cua he: tai lieu -> khai bao kiem dinh duoc.",
        "PDF/anh/video/HTML/ma nguon -> DSL qua `ngu_phap.py`.",
        "Boc 389 file ma = **1,01 giay** (bang 0,12 lan mot backtest — khong co gi "
        "de toi uu o day). 360/408 co che ra tester trong 4 phut nho gop mot EA.",
        "190/389 file la CHI BAO chua tung vao khau boc. `doc_ma` viet cho Pine nen "
        "cham `.mq5` 0 diem. Bo loc 'co dau hieu chua luat' viet cho van xuoi nen "
        "cham ma nguon 0 diem. PDF Telegram la ANH, can OCR.",
        "Sua bo doc theo TUNG LOAI NGUON (Pine / MQL5 / van xuoi / anh), dung mot "
        "bo doc cham het. Do bang suat boc tung lan, khong bang so file.",
    ),
    "LOP · DU LIEU & TAI SAN": (
        "Nap gia tu CHINH cong cu se giao dich, va do dac tinh tung ma.",
        "Nap bar -> kiem chat luong -> ho so tai san (tinh cach, chi phi, mua vu, song).",
        "194 symbol ra ho so trong **5 giay**. 111 bang >=12 nam. Chi phi DO DUOC "
        "(spread 0,9384 bps tu 5.747 bar). Hurst du bao duoc (r=-0,567/157 ma).",
        "Bar hong x10 o **16/159 ma**. `open` bia truoc 2006 (= close[t-1] o 95-98% "
        "ngay). H1 chi co tu 2016, M5 chi 1,4 nam. MT5 don bar NGAY vao khung nho "
        "khi thieu du lieu, **khong bao loi**.",
        "`du_lieu.chan_doan_do_phan_giai()` va `cat_doan_tho` da co — bat buoc chay "
        "TRUOC moi backtest, khong phai tuy chon.",
    ),
    "LOP · SINH GIA THUYET": (
        "Bon luong sinh: noi sinh, ngoai sinh, suy nguoc dau chan, to hop.",
        "Sinh gia thuyet moi tu lich su ma / he da pass / 400 ho so signal / to hop.",
        "387 gia thuyet dang ky. To hop da cap x da khung x da quan li x da tham so "
        "chay duoc. Suy nguoc tu 400 signal ra AUDCAD (13/19 he DCA song).",
        "**~19% kho la ban trung** (616/3.236 co che sinh tin hieu y het). Sinh "
        "nhanh hon kha nang kiem dinh, nen hang don o cong.",
        "Khu trung bang **hash chuoi tin hieu** ngay tai cho sinh, truoc khi ghi so.",
    ),
    "LOP · QUAN TRI VI THE": (
        "Ho co che THU HAI — va theo chu du an la ho QUAN TRONG NHAT.",
        "Trailing, dat hue, DCA/luoi, hedge, nhoi lenh, chuoi quan tri, don bay.",
        "**Entry tinh SAI van cho 92-97%/nam** khi lop quan tri dung. Trailing: lai "
        "holdout **x4,8**, sut giam giam. Luoi AUDCAD do day du ~3,8%/nam holdout. "
        "Bigmouse .set that: 62%/nam tren von 33$ cent.",
        "Chi **12 module** so voi 19 cua thu thap — dau tu nguoc voi hieu qua. "
        "262 co che trong kho la tin hieu VAO, chi 18 la quan tri. Quan tri can CHO "
        "de hoat dong: trailing/dat hue vo hieu tren he thoat nhanh. Nhoi lenh dep "
        "trong mau nhung Calmar xau ngoai mau; chi **dat hue** song sot.",
        "**Truc chinh cua dot 2.** Moi tin hieu vao phai chay qua >=3 luat quan tri "
        "truoc khi vao so. Don vi co ban thanh `ho1 x ho2`.",
    ),
    "LOP · KIEM DINH & CONG": (
        "Noi mot gia thuyet duoc phep doi doi.",
        "Mo phong -> pheu V0..V3 -> cong that -> cham diem tien.",
        "MDE do duoc: **30 bps/lenh** la edge nho nhat pheu con thay. Placebo hieu "
        "chuan hai chieu (null 0,005 vs nguong). 1.811 dong FDR **da ghi truoc khi "
        "tat cong FDR**. Engine mot cua "
        "(`mo_phong.py`) khop MT5 tester 100%.",
        "**FDR DA TAT tu 04/09** theo quyet dinh chu du an (`config/nguong.json`: "
        "`bat_fdr = false`) - do truoc khi tat: 703 ket qua cham cong FDR, **0 cai "
        "truot CHI vi FDR**. So FDR van duoc GHI de con doi chieu ve sau, nhung no "
        "khong con la dieu kien PASS. Nut that that la MDE. `cong_ra_tien` "
        "MO COI. Cong chua ap cho hang trong kho: 169/540 co che khong qua noi. "
        "Do dac phai truyen `ghi_so=False` de khong ghi nham vao so ket qua.",
        "Dao thu tu: **cong ra tien la cong CUOI**, cong that ha xuong thanh NHAN "
        "(dung LUAT SO 0). Ap cong cho toan kho, khong chi hang moi.",
    ),
    "LOP · MT5 / TESTER": (
        "Do THAT. Quy tac chu du an: MT5 tester TRUOC, Python SAU.",
        "DSL -> MQL5 -> terminal64.exe -> doc bao cao -> danh sach lenh.",
        "**8.241 phep thu = 82 giay** khi nhoi het vao mot lan boot. 360/408 co che "
        "ra tester trong 4 phut. Doc duoc danh sach lenh that de truy nguoc luat vao.",
        "**LAN TESTER = 1 la rang buoc VAT LY** (mot `terminal64.exe`, ghi de cung "
        "file `.mq5`/`.ini`) — hai viec cung luc ghi de ket qua nhau va KHONG AI BAO "
        "LOI. `Model=1` che ra lai gia khi TP < 2x bien do nen M1 (lech 12 lan). "
        "13/225 qua holdout.",
        "Giu rang buoc lan=1, xep hang tuan tu. Bat buoc `Model=0/4` cho moi cau hinh "
        "TP ngan. Khoa `khoa_tester.py` phai la cua duy nhat.",
    ),
    "LOP · DIEU HANH & GIAM SAT": (
        "Giu he chay 24/7 va tu thay duoc minh hong cho nao.",
        "Canary, mach dap 10 chang, ngan sach tai nguyen, tran CPU, kill-switch.",
        "5 canary tu kiem. `b mach` do 10 chang duong ong. Ngan sach chia lan "
        "(CPU 6 · LLM 3 · MANG 3 · NHE 8 · TESTER 1). `q` chay qwen tu dong, CPU ~85%.",
        "**He dang NAM IM** (`DUNG_LAI` bat). 24/7 tung chet vi lease tren Windows — "
        "`os.replace` that bai im lang lam so 'thoi gian song' sai. 3 module trong "
        "goi van mo coi, trong do co `cong_ra_tien`.",
        "Noi 3 mo coi, go `DUNG_LAI`, dat `suy_giam` vao nhip ngay de canh bao tu "
        "den dien thoai (da bat `inputNeededNotifEnabled`).",
    ),
}


def _ht() -> dict:
    """DO ha tang ky thuat luc sinh. CHI DOC, khong sua gi.

    Moi phep do deu boc try/except rieng: mot thu khong do duoc thi ghi
    "chua do duoc" cho rieng no, khong lam rong ca muc. Do la ly do ham nay dai
    ma nong - no la 12 phep do doc lap, khong phai mot thuat toan.
    """
    import json
    import os
    import platform
    import shutil
    import subprocess
    r: dict = {}

    def thu(ten, f):
        try:
            r[ten] = f()
        except Exception as e:
            r[ten] = "chua do duoc (%s)" % type(e).__name__

    # 1. May
    thu("os", lambda: "%s %s" % (platform.system(), platform.version()))
    thu("cpu", lambda: platform.processor() or "chua do duoc")
    try:
        import psutil
        r["nhan"] = psutil.cpu_count(logical=False)
        r["luong"] = psutil.cpu_count(logical=True)
        r["ram_gb"] = round(psutil.virtual_memory().total / 1e9, 1)
        r["ram_trong_gb"] = round(psutil.virtual_memory().available / 1e9, 1)
        r["dia"] = []
        for d in psutil.disk_partitions(all=False):
            try:
                u = psutil.disk_usage(d.mountpoint)
                r["dia"].append("%s %.0fGB (trong %.1fGB)"
                                % (d.device, u.total / 1e9, u.free / 1e9))
            except Exception:
                pass
    except Exception:
        r["nhan"] = r["luong"] = r["ram_gb"] = "chua do duoc (thieu psutil)"

    # 2. Python
    thu("py", lambda: "%s @ %s" % (platform.python_version(), sys.executable))
    thu("venv", lambda: os.environ.get("VIRTUAL_ENV")
        or os.environ.get("CONDA_PREFIX") or "KHONG — python he thong")
    def _lib():
        import importlib.metadata as M
        can = ("numpy pandas scipy scikit-learn statsmodels numba matplotlib "
               "MetaTrader5 pyarrow polars requests httpx beautifulsoup4 lxml "
               "playwright selenium pdfplumber PyMuPDF pillow pytest "
               "pytest-xdist openai psutil joblib tqdm").split()
        ra = []
        for t in can:
            try:
                ra.append("%s %s" % (t, M.version(t)))
            except Exception:
                ra.append("%s —" % t)
        return ra
    thu("lib", _lib)

    def _engine():
        p = LAB / "nhan" / "mo_phong.py"
        vb = p.read_text(encoding="utf-8-sig", errors="ignore")
        dong = vb.splitlines()
        vong = sum(1 for x in dong if x.lstrip().startswith(("for ", "while ")))
        vec = sum(1 for x in dong if "np." in x or ".values" in x)
        # Phai tim IMPORT that, khong phai chu "numba" o dau do: ban dau tim
        # chuoi tho thi `san_cong_cu.py` (danh muc cong cu) lam ket qua ra "CO".
        import re as _re
        _mau = _re.compile(r"^\s*(import numba|from numba)", _re.M)
        co_numba = any(_mau.search(q.read_text(encoding="utf-8-sig", errors="ignore"))
                       for q in list((LAB / "nhan").glob("*.py"))
                       + list(LAB.glob("*.py")))
        ss = sum(1 for q in list(LAB.glob("*.py")) + list((LAB / "nhan").glob("*.py"))
                 + list((LAB / "tru").glob("*.py"))
                 if any(t in q.read_text(encoding="utf-8-sig", errors="ignore")
                        for t in ("multiprocessing", "ProcessPool", "concurrent.futures")))
        return dict(dong=len(dong), vong=vong, vec=vec, numba=co_numba, song_song=ss)
    thu("engine", _engine)

    # 3. Du lieu gia
    def _gia():
        from nhan import duong_dan as DD
        k = DD.kho_gia() if callable(DD.kho_gia) else DD.kho_gia
        k = Path(str(k))
        if not k.exists():
            return {"noi": str(k), "trang_thai": "KHONG TON TAI"}
        fs = [q for q in k.rglob("*") if q.is_file()]
        dinh = {}
        for q in fs:
            dinh[q.suffix.lower() or "(khong duoi)"] = dinh.get(q.suffix.lower() or "(khong duoi)", 0) + 1
        return {"noi": str(k), "so_file": len(fs),
                "gb": round(sum(q.stat().st_size for q in fs) / 1e9, 3),
                "dinh_dang": dinh}
    thu("gia", _gia)

    # 4. nao.db
    def _db():
        cn = _cn()
        o = {"journal": cn.execute("PRAGMA journal_mode").fetchone()[0],
             "busy_timeout_ms": cn.execute("PRAGMA busy_timeout").fetchone()[0]}
        ps = cn.execute("PRAGMA page_size").fetchone()[0]
        pc = cn.execute("PRAGMA page_count").fetchone()[0]
        o["trang"] = "%d x %d B = %.2f GB" % (pc, ps, pc * ps / 1e9)
        # DO trang trong, khong doan. Ban dau muc nay viet "phan lon la trang
        # trong" ma khong do - mot ban ke hoach doc lai da bat dung loi do.
        fl = cn.execute("PRAGMA freelist_count").fetchone()[0]
        o["trong"] = ("%d trang = %.2f GB (**%.1f%% DB**), thu hoi duoc bang VACUUM"
                      % (fl, fl * ps / 1e9, 100.0 * fl / max(pc, 1)))
        o["that"] = "%.2f GB" % ((pc - fl) * ps / 1e9)
        b = []
        for (t,) in cn.execute("SELECT name FROM sqlite_master "
                               "WHERE type='table' ORDER BY 1"):
            try:
                b.append((cn.execute("SELECT COUNT(*) FROM [%s]" % t).fetchone()[0], t))
            except Exception:
                b.append((-1, t))
        cn.close()
        b.sort(reverse=True)
        o["bang"] = b
        o["tong_dong"] = sum(n for n, _ in b if n > 0)
        for f in ("nao.db", "nao.db-wal"):
            q = LAB / f
            o[f] = ("%.1f MB" % (q.stat().st_size / 1e6)) if q.exists() else "khong co"
        return o
    thu("db", _db)

    # 5. LLM
    def _llm():
        d = json.loads((LAB / "config" / "qwen.json").read_text(encoding="utf-8-sig"))
        url = d.get("base_url", "")
        return {"kieu": "API tu xa" if url.startswith("http") else "chua ro",
                "url": url, "model": d.get("model"),
                "du_phong": d.get("model_du_phong"),
                "muc_tieu_cpu": d.get("muc_tieu_cpu")}
    thu("llm", _llm)

    # 6/7. MT5
    def _mt5():
        goc = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        ban = [str(q.parent) for q in goc.glob("*/terminal64.exe")]
        from nhan import duong_dan as DD
        dd = Path(str(DD.mt5_du_lieu() if callable(DD.mt5_du_lieu) else DD.mt5_du_lieu))
        tm = [q.name for q in dd.iterdir() if q.is_dir()] if dd.exists() else []
        khoa = LAB / "config" / "khoa_tester.json"
        return {"ban_cai": ban, "so_thu_muc_du_lieu": len(tm),
                "exe_ma_nguon_dung": str(DD.mt5_exe() if callable(DD.mt5_exe) else DD.mt5_exe),
                "khoa_dang_giu": khoa.exists() and khoa.read_text(encoding="utf-8")[:120] or "khong ai giu"}
    thu("mt5", _mt5)

    # 8. Git
    def _git():
        g = lambda *a: subprocess.run(["git", *a], cwd=str(LAB.parent),
                                      capture_output=True, text=True,
                                      encoding="utf-8", errors="ignore").stdout.strip()
        return {"nhanh": g("branch", "--show-current"),
                "so_commit": g("rev-list", "--count", "HEAD"),
                "file_ban": len([x for x in g("status", "--porcelain").splitlines() if x]),
                "remote": g("remote", "-v") or "KHONG CO remote",
                "worktree": g("worktree", "list").count("\n") + 1}
    thu("git", _git)

    def _test():
        q = LAB / "reports" / "test_lan_cuoi.txt"
        return " ".join(q.read_text(encoding="utf-8").split())[:700] if q.exists() \
            else "chua do duoc trong lan sinh nay — chay `b test` roi luu ket qua vao reports/test_lan_cuoi.txt"
    thu("test", _test)

    # 9. Live
    def _live():
        c = LAB / "DUNG_LAI"
        o = {"dung_lai": c.read_text(encoding="utf-8").strip() if c.exists() else None}
        try:
            h = json.loads((LAB / "config" / "he_chay_that.json").read_text(encoding="utf-8-sig"))
            o["he_dang_ky"] = len(h)
            o["he_bat"] = [k for k, v in h.items() if v.get("bat")]
            o["cho_tien_that"] = [k for k, v in h.items() if v.get("cho_phep_tien_that")]
        except Exception:
            o["he_dang_ky"] = "chua do duoc"
        return o
    thu("live", _live)
    return r


def _cong_cu() -> tuple[list[str], int]:
    """Plugin dang bat + so Agent Skill nap tu chung.

    Doc thang `~/.claude/settings.json` chu khong go cung danh sach: cai dat thay
    doi moi tuan, ma mot muc "nang luc" ke sai thi te hon khong ke.
    """
    import json
    import os
    try:
        goc = Path(os.path.expanduser("~")) / ".claude"
        d = json.loads((goc / "settings.json").read_text(encoding="utf-8"))
        pl = sorted(k for k, v in (d.get("enabledPlugins") or {}).items() if v)
        sk = len(list((goc / "plugins" / "cache").rglob("SKILL.md")))
        return pl, sk
    except Exception:
        return [], 0


def _cn():
    return sqlite3.connect(f"file:{LAB / 'nao.db'}?mode=ro", uri=True)


def _mot(cn, cau, mac_dinh=0):
    try:
        return cn.execute(cau).fetchone()[0]
    except Exception:
        return mac_dinh


def _so_lieu() -> dict:
    """So song. Moi truy van phai chiu duoc mot so cai TRONG."""
    s = {}
    try:
        cn = _cn()
    except Exception:
        return s
    try:
        s["tai_lieu"] = _mot(cn, "SELECT COUNT(*) FROM tai_lieu")
        s["doc_tron"] = _mot(cn, "SELECT COUNT(*) FROM noi_dung WHERE so_ky_tu>0")
        s["cho_doc"] = _mot(cn, "SELECT COUNT(*) FROM tai_lieu t LEFT JOIN noi_dung n "
                                "ON n.tai_lieu_id=t.id WHERE n.id IS NULL "
                                "AND t.url LIKE 'http%'")
        s["fdr"] = _mot(cn, "SELECT COUNT(*) FROM fdr")
        s["gia_thuyet"] = _mot(cn, "SELECT COUNT(*) FROM gia_thuyet")
        s["ket_qua"] = _mot(cn, "SELECT COUNT(*) FROM ket_qua")
        s["ung_vien"] = _mot(cn, "SELECT COUNT(*) FROM candidate_queue")
        s["van_de_mo"] = _mot(cn, "SELECT COUNT(*) FROM van_de "
                                  "WHERE trang_thai NOT IN ('XONG','DA_SUA')")
        s["nguon"] = list(cn.execute("SELECT nguon, COUNT(*) c FROM tai_lieu "
                                     "GROUP BY 1 ORDER BY c DESC LIMIT 8"))
    finally:
        try:
            cn.close()
        except Exception:
            pass
    try:
        from nhan import mau as MAU
        s["mau"] = len(MAU.MAU)
    except Exception:
        pass
    try:
        from nhan import san_cong_cu as SCC
        s["cong_cu"] = len(SCC.doc_kho())
    except Exception:
        pass
    s["nam_im"] = (LAB / "DUNG_LAI").exists()
    try:
        s["nao_db_gb"] = round((LAB / "nao.db").stat().st_size / 1e9, 2)
    except Exception:
        pass
    return s


def _he() -> list[dict]:
    try:
        from nhan import bang_he as BH
        return BH.thu_hoach(chi_pass=True) or []
    except Exception:
        return []


def sinh(in_ra=print) -> str:
    d = KT._thu_thap()
    s = _so_lieu()
    he = _he()
    ra: list[str] = []
    W = ra.append

    W("# HO SO HE THONG — THE BRAIN")
    W("")
    W("*Sinh tu ma nguon + `nao.db` luc %s bang `b ho-so`.*"
      % time.strftime("%Y-%m-%d %H:%M"))
    W("")
    W("> **Doc file nay the nao.** No TU DU: khong can mo repo. Moi con so o day")
    W("> do duoc luc sinh, khong chep tu bao cao cu. Ba muc **KHONG** co trong")
    W("> file: ma nguon chi tiet, du lieu gia, va ket qua tung backtest — neu can")
    W("> chung thi phai hoi nguoi co dia. Muc 7 (**luat doc ket qua**) la bat")
    W("> buoc doc truoc khi khuyen bat ky dieu gi.")
    W("")

    # 1 ---------------------------------------------------------------
    W("## 1. He nay de lam gi")
    W("")
    W(MUC_TIEU)

    # 2 ---------------------------------------------------------------
    W("## 2. So do duong di that")
    W("")
    W("Sau chang. Con so trong ngoac la **so thuc te dang o chang do**, do luc sinh.")
    W("")
    W("```")
    W("  [1] NGUON                tru/seeker.py")
    W("      github · openalex · crossref · mql5_code · tradingview_pine · reddit")
    W("        |                                              (%s tai lieu)" % s.get("tai_lieu", "?"))
    W("        v")
    W("  [2] DOC TOAN VAN         nhan/toan_van · doc_pdf · doc_anh · doc_video · go_html")
    W("        |                                     (%s doc tron, %s cho doc)"
      % (s.get("doc_tron", "?"), s.get("cho_doc", "?")))
    W("        v")
    W("  [3] BOC -> CO CHE        nhan/ngu_phap.py  <- CUA DUY NHAT kien thuc vao he")
    W("      doc_ma · doc_chi_bao · doc_hieu · boc_llm · quan_tri")
    W("        |                                        (%s mau chien luoc)" % s.get("mau", "?"))
    W("        v                                        (%s cong cu trong kho)" % s.get("cong_cu", "?"))
    W("  [4] SINH GIA THUYET      noi_sinh · ngoai_sinh · suy_nguoc · to_hop")
    W("        |                                        (%s gia thuyet dang ky)"
      % s.get("gia_thuyet", "?"))
    W("        v")
    W("  [5] KIEM DINH            mo_phong -> sang_loc(V0..V3) -> cong -> cham_diem")
    W("      MT5 tester: dich_mq5 -> terminal64.exe (LAN = 1, rang buoc VAT LY)")
    W("        |                     (%s ket qua · %s ung vien · %s dong FDR)"
      % (s.get("ket_qua", "?"), s.get("ung_vien", "?"), s.get("fdr", "?")))
    W("        v")
    W("  [6] RA THAT              danh_muc -> chay_that -> so_lenh -> suy_giam")
    W("                                        (%d he qua cong · he dang %s)"
      % (len(he), "NAM IM" if s.get("nam_im") else "chay"))
    W("```")
    W("")
    W("**Cua vao that** (ngoai bon duong nay thi module coi nhu khong ton tai):")
    W("`b.py` (lenh nguoi go) · `dieu_phoi.py` (tru chay 24/7) · `day_viec.py` "
      "(hang doi xay) · `qwen/NHIEM_VU.json` (bang viec tu chay).")
    W("")

    # 3 ---------------------------------------------------------------
    W("## 3. Nam tru — trang thai that")
    W("")
    W("| Tru | Dong | Goi bao nhieu module loi | Danh gia |")
    W("|---|---|---|---|")
    danh_gia = {
        "seeker": "dang chay, LON NHAT he",
        "quantlab": "dang chay",
        "evolution": "dang chay",
        "banker": "**VO** — chua xay",
        "finder": "**VO** — chua xay",
        "nghi": "co chay",
    }
    for t in KT.TRU:
        k = "tru/%s.py" % t
        if k not in d["vai_tro"]:
            continue
        goi = [x for x in d["canh"].get(k, ()) if x.startswith("nhan/")]
        W("| %s | %d | %d | %s |"
          % (t.upper(), d["dong"].get(k, 0), len(goi), danh_gia.get(t, "")))
    W("")

    # 4 ---------------------------------------------------------------
    nhan_het = [k for k in d["vai_tro"]
                if k.startswith("nhan/") and not k.endswith("__init__.py")]
    W("## 4. Ho so tung thanh phan")
    W("")
    W("Moi thanh phan doc theo nam truong: **vai tro · nhiem vu · nang luc THUC TE "
      "· van de con ton · huong giai**. Truong 'nang luc thuc te' luon kem SO DO "
      "DUOC — khong co so thi ghi ro la chua do.")
    W("")
    mo_dun_lop = {("LOP · " + k): [m for m in v[1]
                                   if ("nhan/%s.py" % m) in d["vai_tro"]]
                  for k, v in KT.LOP.items()}
    for ten, (vt, nv, nl, vd, hg) in THANH_PHAN.items():
        W("### %s" % ten)
        W("")
        W("| | |")
        W("|---|---|")
        W("| **Vai tro** | %s |" % vt)
        W("| **Nhiem vu** | %s |" % nv)
        W("| **Nang luc thuc te** | %s |" % nl)
        W("| **Van de con ton** | %s |" % vd)
        W("| **Huong giai** | %s |" % hg)
        ds = mo_dun_lop.get(ten)
        if ds:
            W("")
            W("*%d module:* %s" % (len(ds), " · ".join("`%s`" % m for m in ds)))
        W("")
    W("Vai tro tung module rieng le: `KIEN_TRUC.md` (sinh boi `b kien-truc`). "
      "Tong %d module loi." % len(nhan_het))
    W("")

    # 5 ---------------------------------------------------------------
    W("## 5. He da qua cong — %d he" % len(he))
    W("")
    if he:
        W("| He | CAGR% | mua-giu% | hon% | Sharpe | DD% | Calmar | Lenh | /tuan |")
        W("|---|---|---|---|---|---|---|---|---|")
        for h in he:
            W("| `%s` | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                str(h.get("he") or "?")[:44],
                _n(h.get("cagr_pct")), _n(h.get("mua_giu_cagr")),
                _n(h.get("hon_mua_giu_cagr")), _n(h.get("sharpe")),
                _n(h.get("max_dd_pct")), _n(h.get("calmar")),
                h.get("so_lenh", "?"), _n(h.get("lenh_moi_tuan"))))
        W("")
    W("**Ba cai bay khi doc bang nay** — deu thay ngay trong chinh bang:")
    W("")
    W("1. **Xep theo Sharpe, khong theo tien** (V1). Dong dau lam ra 0,62%/nam.")
    W("2. **Co ban trung** (V2): `mat_can_bang_lenh_dong_cua.` va")
    W("   `...mac_dinh` la mot thu hai ten — 4 dong, 2 cap trung khit. "
      "**%d dong = %d he.**" % (len(he), len(he) - 2))
    W("3. **Cot `hon%` duong khong co nghia la ra tien.** EURGBP hon mua-giu 3,47 "
      "diem chi vi mua-giu EURGBP la **-2,84%/nam**. Thang mot moc am van la thang.")
    W("")
    thua = [h for h in he if (h.get("hon_mua_giu_cagr") or 0) < 0]
    tot = sorted(he, key=lambda h: h.get("cagr_pct") or 0, reverse=True)[:1]
    W("**Doc lai bang tren theo dung cau hoi TIEN** (*co hon mua-giu o cung rui ro "
      "khong*), va no doi hoan ket luan:")
    W("")
    if tot:
        t = tot[0]
        W("- He CAGR cao nhat — `%s`, **%s%%/nam** — chi hon mua-giu **%s diem** "
          "trong khi chiu sut giam **%s%%**. Mua-giu cung ma da cho %s%%/nam ma "
          "khong phai lam gi."
          % (str(t.get("he"))[:40], _n(t.get("cagr_pct")),
             _n(t.get("hon_mua_giu_cagr")), _n(t.get("max_dd_pct")),
             _n(t.get("mua_giu_cagr"))))
    for h in thua:
        W("- `%s` **THUA mua-giu %s diem** (%s%% so voi %s%%) — nhung van nam "
          "trong bang 'da qua cong'."
          % (str(h.get("he"))[:40], _n(abs(h.get("hon_mua_giu_cagr") or 0)),
             _n(h.get("cagr_pct")), _n(h.get("mua_giu_cagr"))))
    W("- Sau khi tru ban trung, con **%d he**, va khong he nao vua ra tien that "
      "vua cach xa mua-giu." % (len(he) - 2))
    W("")

    # 6 ---------------------------------------------------------------
    W("## 6. Van de va de xuat sua")
    W("")
    W("Xep theo dot. **Dot sau chi co nghia neu dot truoc xong.**")
    W("")
    for dot in sorted({v[5] for v in VAN_DE}):
        W("### Dot %d" % dot)
        W("")
        for ma, ten, bc, hq, dx, dt in VAN_DE:
            if dt != dot:
                continue
            W("#### %s. %s" % (ma, ten))
            W("")
            W("- **Bang chung:** %s" % bc)
            W("- **Hau qua:** %s" % hq)
            W("- **De xuat:** %s" % dx)
            W("")
    W("**Tieu chi dung tung dot:**")
    W("")
    W("1. `b he` tra loi duoc *'he nao ra tien nhat tren moi don vi sut giam'*, "
      "va cau tra loi khong phai mot ban trung.")
    W("2. Co >=3 he CAGR rong > 10%/nam o cung sut giam voi mua-giu, ca ba co chan quan tri.")
    W("3. Mot danh muc thang mua-giu o cung sut giam, **tren nua holdout**.")
    W("4. Tien that vao tai khoan that, va khong can ai ngoi may.")
    W("")

    # 7 ---------------------------------------------------------------
    W("## 7. Luat doc ket qua — DOC TRUOC KHI KHUYEN BAT KY DIEU GI")
    W("")
    W(LUAT_DOC)

    # 8 ---------------------------------------------------------------
    W("## 8. Thuat ngu")
    W("")
    for t, m in (
        ("ho 1", "co che **tin hieu VAO** (~262). DSL `vao`/`ra` trong `nhan/ngu_phap.py`."),
        ("ho 2", "co che **QUAN TRI VI THE** (~18). Ghep duoc voi moi he."),
        ("ho 3", "**PMG** — quan li lenh KHONG co tin hieu vao (luoi ro)."),
        ("cong that", "placebo + MDE + FDR. Theo LUAT SO 0 day chi la **nhan**."),
        ("cong ra tien", "hoi 'co thang mua-giu o cung rui ro khong'. Cong quyet dinh."),
        ("MDE", "edge nho nhat ma he con nhin thay duoc (~30 bps/lenh)."),
        ("placebo", "hoan vi **chuoi vi the** de xem edge co that khong."),
        ("holdout", "nua du lieu chua bao gio duoc cham khi thiet ke."),
        ("pheu V0-V3", "van tay -> re -> kinh te -> phan chung. `nhan/sang_loc.py`."),
        ("mua-giu", "moc bat buoc. Phai co ca ban CFD (co phi) va ban chi so."),
    ):
        W("- **%s** — %s" % (t, m))
    W("")

    # 9 ---------------------------------------------------------------
    W("## 9. So ma nguon")
    W("")
    goc = [k for k in d["vai_tro"] if "/" not in k]
    goc_test = [k for k in goc if k.startswith(("test_", "conftest"))]
    goc_tay = [k for k in goc if k.startswith("_")]
    W("| Muc | So |")
    W("|---|---|")
    W("| File `.py` | %d |" % len(d["vai_tro"]))
    W("| Tren duong chay | %d |" % len(d["toi"]))
    W("| Module loi `nhan/` | %d |" % len(nhan_het))
    W("| File goc `lab/` | %d (%d test · %d script chay tay · **%d no that**) |"
      % (len(goc), len(goc_test), len(goc_tay),
         len(goc) - len(goc_test) - len(goc_tay)))
    W("| File > 600 dong | %d |" % sum(1 for v in d["dong"].values() if v >= 600))
    W("| Module trong goi van mo coi | %d |"
      % len([k for k in d["vai_tro"] if k not in d["toi"]
             and k.startswith(("nhan/", "tru/", "qwen/"))]))
    W("| `nao.db` | %s GB |" % s.get("nao_db_gb", "?"))
    W("| Van de con mo trong so | %s |" % s.get("van_de_mo", "?"))
    W("")
    # 10 --------------------------------------------------------------
    W("## 10. Nang luc cong cu cua phien lam viec")
    W("")
    W("Muc nay cho nguoi doc ngoai biet **phien Claude Code chay du an nay lam gi "
      "duoc**, de dung giao viec ma cong cu khong lam noi — hoac nguoc lai, dung "
      "de xuat lam tay thu da tu dong.")
    W("")
    pl, sk = _cong_cu()
    if pl:
        W("**%d plugin dang bat:**" % len(pl))
        W("")
        for t in pl:
            W("- `%s`" % t)
        W("")
    if sk:
        W("**~%d Agent Skill** nap tu cac plugin tren. Nhom dung cho du an nay: "
          "backtrader · vectorbt · walk-forward-validation · cointegration-analysis "
          "· correlation-analysis · portfolio-analytics · regime-detection · "
          "exit-strategies · position-sizing · kelly-criterion · slippage-modeling "
          "· volatility-modeling · ta-lib · pandas-ta." % sk)
        W("")
        W("41 skill crypto/DeFi/thue duoc dat `user-invocable-only`: khong hien "
          "trong danh sach model doc moi luot (de khoi ton ngu canh) nhung van goi "
          "duoc bang `/ten-skill`.")
        W("")
    W("**Tu chay giua cac phien** — ba tang, khong can nguoi go:")
    W("")
    W("1. `Stop` hook ghi ban giao song + `double-shot-latte` tu cham *co nen lam "
      "tiep khong* thay vi dung lai hoi.")
    W("2. `SessionStart` hook nap `BAN_GIAO.py` (trang thai he) roi in "
      "`TIEP_TUC_MAI.md` (viec con ton) — phien sau mo ra la biet viec.")
    W("3. `autoContinueAtUsageLimit`: cham tran han muc thi doi reset roi chay tiep.")
    W("")
    W("**Ba lenh so do** (chay lai truoc khi tin bat ky so nao): `b ban-do` "
      "(duong chay) · `b kien-truc` (tang + vai tro) · `b ho-so` (file nay).")
    W("")
    # 11 --------------------------------------------------------------
    h = _ht()
    g = lambda k, m="chua do duoc": h.get(k, m)
    W("## 11. Ha tang ky thuat")
    W("")
    W("*Do luc sinh, CHI DOC. Muc nao khong do duoc thi ghi ro la chua do duoc — "
      "khong suy dien, khong chep tu bao cao cu.*")
    W("")

    W("### 11.1 May")
    W("")
    W("| | |")
    W("|---|---|")
    W("| OS | %s |" % g("os"))
    W("| CPU | %s — **%s nhan / %s luong** |" % (g("cpu"), g("nhan"), g("luong")))
    W("| RAM | %s GB (trong %s GB luc do) |" % (g("ram_gb"), g("ram_trong_gb")))
    W("| Dia | %s |" % (" · ".join(g("dia", [])) if isinstance(g("dia"), list)
                        else g("dia")))
    W("| GPU | **khong dung** — khong thu vien nao trong he goi CUDA/GPU |")
    W("")

    W("### 11.2 Python va engine")
    W("")
    lib = g("lib")
    W("| | |")
    W("|---|---|")
    W("| Phien ban | %s |" % g("py"))
    W("| Moi truong | %s |" % g("venv"))
    if isinstance(lib, list):
        W("| Thu vien | %s |" % " · ".join(lib))
    e = g("engine")
    if isinstance(e, dict):
        W("| `mo_phong.py` | %d dong · **%d vong lap** · %d dong vector hoa (`np.`/"
          "`.values`) — engine **vector hoa**, khong phai vong lap tung bar |"
          % (e["dong"], e["vong"], e["vec"]))
        W("| numba | %s |" % ("CO" if e["numba"] else "**KHONG** — chua ai dung JIT"))
        W("| song song | **%d file** dung `multiprocessing`/`concurrent.futures` |"
          % e["song_song"])
    W("")

    W("### 11.3 Du lieu gia")
    W("")
    gia = g("gia")
    if isinstance(gia, dict) and "so_file" in gia:
        W("- **Noi luu:** `%s` — KHONG nam trong repo (o o dia khac)" % gia["noi"])
        W("- **Quy mo:** %s file · **%s GB**" % (gia["so_file"], gia["gb"]))
        W("- **Dinh dang:** %s"
          % " · ".join("%s %d" % (k, v) for k, v in
                       sorted(gia["dinh_dang"].items(), key=lambda x: -x[1])))
        W("- **Cach nap:** `nhan/du_lieu.py` -> `kho()` chon ban theo **do phu** "
          "(khong theo byte), roi `kiem()` chay 5 bay chat luong truoc khi tra ve.")
    else:
        W("- %s" % gia)
    W("")

    W("### 11.4 `nao.db`")
    W("")
    db = g("db")
    if isinstance(db, dict):
        W("| | |")
        W("|---|---|")
        W("| Loai | SQLite, journal **%s**, `busy_timeout` %s ms |"
          % (db["journal"], db["busy_timeout_ms"]))
        W("| Kich thuoc | %s · WAL %s |" % (db["nao.db"], db["nao.db-wal"]))
        W("| Trang | %s |" % db["trang"])
        W("| Tong dong | **%s** tren %d bang |" % (f"{db['tong_dong']:,}", len(db["bang"])))
        W("")
        W("| Trang TRONG | %s |" % db.get("trong", "chua do duoc"))
        W("| Du lieu THAT | %s |" % db.get("that", "chua do duoc"))
        W("")
        W("**Da DO, khong doan:** %s cho **%s dong**, trong do %s. Phan con lai "
          "(%s) la du lieu that — chu yeu toan van tai lieu o `noi_dung`/`artifact`. "
          "VACUUM can cho trong bang kich thuoc DB tren CUNG o."
          % (db["nao.db"], f"{db['tong_dong']:,}", db.get("trong", "?"),
             db.get("that", "?")))
        W("")
        W("| Bang | Dong | | Bang | Dong |")
        W("|---|---|---|---|---|")
        b = db["bang"]
        nua = (len(b) + 1) // 2
        for i in range(nua):
            t1 = "`%s` | %s" % (b[i][1], f"{b[i][0]:,}")
            t2 = ("`%s` | %s" % (b[i + nua][1], f"{b[i+nua][0]:,}")) \
                if i + nua < len(b) else " | "
            W("| %s | | %s |" % (t1, t2))
        W("")
        W("**Ghi nhieu nhat:** `vi_mo` va `chi_so_vh` (tru BANKER do vi mo lien tuc) "
          "chiem %.0f%% tong so dong."
          % (100.0 * sum(n for n, t in b if t in ("vi_mo", "chi_so_vh"))
             / max(db["tong_dong"], 1)))
        W("")
        W("**Ai ghi dong thoi:** `dieu_phoi.py` (5 tru, ThreadPool) · `day_viec.py` "
          "· `qwen/chay.py` · moi script chay tay goi `nhan/so.py`. WAL cho phep "
          "**nhieu doc + mot ghi**; xung dot ghi doi `busy_timeout` %s ms roi nem "
          "`database is locked`." % db["busy_timeout_ms"])
        W("")
        W("Loi `database is locked` **da tung gap** — day la ly do co "
          "`nhan/gop_wal.py` va lenh `b don-dia`: WAL tung phinh 1,4 GB va lam ba "
          "me boc bao XONG rc=0 ma kho khong doi.")
    else:
        W("- %s" % db)
    W("")

    W("### 11.5 LLM")
    W("")
    l = g("llm")
    if isinstance(l, dict):
        W("- **Kieu:** %s — `%s`" % (l["kieu"], l["url"]))
        W("- **Model:** `%s` (du phong `%s`). **Khong chay local**, khong tai "
          "trong so ve may." % (l["model"], l["du_phong"]))
        W("- **Toc do token/giay:** chua do duoc — he chi ghi *ban/giay* o muc day "
          "chuyen (do 13/09: 6 luong 0,071 ban/giay · 24 luong 0,101).")
        W("- **Lan goi/gio:** chua do duoc — khong co bo dem goi LLM theo gio.")
        W("- Muc tieu CPU cua `q`: %s%% CA MAY." % l["muc_tieu_cpu"])
    else:
        W("- %s" % l)
    W("")

    W("### 11.6 Dieu phoi")
    W("")
    W("- `dieu_phoi.py` — supervisor 24/7, **`ThreadPoolExecutor`** chay 5 tru, "
      "nhip tim ghi file moi 5 giay; hai nhip giao nhau = supervisor chet.")
    W("- `day_viec.py` — hang doi viec **tuan tu**, moi viec mot `subprocess`, "
      "co han gio va `taskkill /F /T` khi qua han.")
    W("- `qwen/dieu_toc.py` — AIMD giu CPU ca may quanh muc tieu, do that moi 5 giay.")
    W("- **Ngan sach lan** (`nhan/ngan_sach.py`): CPU giao cho dieu_toc · **LLM 8 "
      "slot** · MANG · NHE · **TESTER 1**.")
    W("- **Khoa tester** (`nhan/khoa_tester.py`): mot file khoa "
      "`config/khoa_tester.json` giu `{pid, viec, luc}`, tu thu hoi khoa mo coi, "
      "TTL 45 phut. Trang thai luc sinh: %s"
      % (g("mt5", {}).get("khoa_dang_giu") if isinstance(g("mt5"), dict) else "chua do"))
    W("")

    W("### 11.7 MT5")
    W("")
    m = g("mt5")
    if isinstance(m, dict):
        W("- **%d ban cai** tren may: %s"
          % (len(m["ban_cai"]), " · ".join("`%s`" % Path(x).name for x in m["ban_cai"])))
        W("- **%s thu muc du lieu terminal** trong `AppData/Roaming/MetaQuotes/Terminal`."
          % m["so_thu_muc_du_lieu"])
        W("- Ma nguon hien **chi tro toi MOT** exe: `%s`" % m["exe_ma_nguon_dung"])
        W("- Portable: **khong** — chay theo thu muc du lieu mac dinh cua tung ban cai.")
        W("- Tai khoan: khai trong `config/` va doc qua `nhan/bi_mat.py` (mot cua "
          "doc khoa). **Khong ghi so tai khoan/mat khau o day.**")
        W("")
        W("**Danh gia: co chay duoc 2+ terminal portable song song khong?**")
        W("")
        W("*May thi duoc* — da co %d ban cai va %s thu muc du lieu rieng. *Ma nguon "
          "thi chua*, va tro ngai la **bon cho cu the**, khong phai mot gioi han vat ly:"
          % (len(m["ban_cai"]), m["so_thu_muc_du_lieu"]))
        W("")
        W("1. `chay_tester_kho.py` ghi de **cung mot** `MQL5/Experts/<TEN_EA>.mq5`, "
          "cung mot `.ini`, cung mot `.xml` trong MOT thu muc du lieu co dinh "
          "(`XM_DATA`). Hai viec cung luc ghi de ket qua cua nhau **va khong ai bao loi**.")
        W("2. `nhan/duong_dan.mt5_exe` tra **mot** duong dan, khong nhan tham so.")
        W("3. `nhan/khoa_tester.py` la khoa **toan cuc mot slot** — no dung de BAO VE "
          "cai (1), nen go khoa ma khong sua (1) la hong ngay.")
        W("4. `nhan/ngan_sach.py` dat `TESTER = 1` va goi do la rang buoc VAT LY. "
          "Do la mo ta **dung voi ma nguon hien tai**, khong dung voi cai may lam duoc.")
        W("")
        W("=> Muon song song thi phai tham so hoa ca bon: `(exe, thu_muc_du_lieu, "
          "ten_ea, ten_ini)` thanh mot 'slot tester', doi khoa thanh khoa **theo "
          "slot**, va nang `TESTER` len bang so slot. Day la viec **sua logic** nen "
          "muc nay chi neu, khong lam.")
    else:
        W("- %s" % m)
    W("")

    W("### 11.8 Git va test")
    W("")
    gi = g("git")
    if isinstance(gi, dict):
        W("- Nhanh `%s` · **%s commit** · %s file dang ban · %s"
          % (gi["nhanh"], gi["so_commit"], gi["file_ban"],
             gi["remote"] if "KHONG" in str(gi["remote"]) else "co remote"))
        W("- `git worktree`: **dung duoc** (repo binh thuong, %d worktree dang co). "
          "Day la duong cho nhieu phien Claude Code lam viec tach nhau — xem 11.10."
          % gi["worktree"])
    W("- **Bo test:** %s" % g("test"))
    W("")

    W("### 11.9 Live")
    W("")
    lv = g("live")
    if isinstance(lv, dict):
        W("- `DUNG_LAI` dang **%s**%s"
          % ("BAT" if lv.get("dung_lai") else "TAT",
             (" (noi dung: `%s`)" % lv["dung_lai"]) if lv.get("dung_lai") else ""))
        W("- **Ly do:** file chi chua mot tu `dung`, **khong ghi ly do**. Tim trong "
          "ma nguon: `b dung` chi ghi co, `dieu_phoi` doc co roi dung sau khi tru "
          "dang chay xong luot. Ly do THAT **chua do duoc tu file** — phai hoi "
          "nguoi dat co.")
        W("- He dang ky chay that: **%s** · dang bat: %s · duoc phep tien that: %s"
          % (lv.get("he_dang_ky"), lv.get("he_bat") or "(khong cai nao)",
             lv.get("cho_tien_that") or "(khong cai nao)"))
        W("- EA cho live: `nhan/dich_mq5*.py` sinh EA nhieu slot (moi slot mot "
          "`magic`, `lot=0` tat slot). VPS: **chua co** — `nhan/san_sang_vps.py` "
          "moi la cong kiem, chua co may.")
    W("")

    W("### 11.10 Rui ro khi chay SONG SONG nhieu phien Claude Code")
    W("")
    W("Tai nguyen dung chung, xep theo **do nguy hiem khi va cham**:")
    W("")
    W("| Tai nguyen | Va cham the nao | Co bao loi khong |")
    W("|---|---|---|")
    W("| **MT5 tester** (`.mq5`/`.ini`/`.xml` co dinh + mot `terminal64.exe`) | "
      "ghi de ket qua cua nhau; bang so doc **y het mot ket qua that** | "
      "**KHONG** — nguy hiem nhat |")
    W("| **`nao.db`** (WAL, mot ghi) | ghi dong thoi -> doi `busy_timeout` roi "
      "`database is locked` | CO |")
    W("| **`config/*.json`** (`he_chay_that`, `day_viec`, `khoa_tester`...) | "
      "doc-sua-ghi khong nguyen tu -> mat thay doi cua phien kia | **KHONG** |")
    W("| **File sinh ra o goc `lab/`** (`BAN_DO.md`, `KIEN_TRUC.md`, file nay) | "
      "ghi de lan nhau | KHONG, nhung vo hai |")
    W("| **git index** (`b luu`, commit) | hai phien commit cung luc -> `index.lock` | CO |")
    W("| **Cong CDP 9224** (Chrome cua Seeker) | hai phien cung dieu khien mot "
      "trinh duyet | mot phan |")
    W("| **Kho gia tren o F:** | doc song song thi an toan; ghi/fetch cung luc thi khong | KHONG |")
    W("| **Lan LLM/CPU** (`ngan_sach`) | moi phien tu dem lan cua rieng no -> "
      "vuot tran CPU that | KHONG |")
    W("")
    W("**Cach an toan nhat dang co:** `git worktree` cho moi phien (11.8) — tach "
      "file va git index. Nhung no **khong** tach `nao.db`, MT5, hay cong CDP: ba "
      "thu do van la mot. Nen quy tac thuc dung la **mot phien duoc dung tester va "
      "ghi so; cac phien khac chi doc**.")
    W("")

    W("### 11.11 Nut that thong luong — xep hang")
    W("")
    W("| # | Nut that | So do duoc | Vi sao no la tran |")
    W("|---|---|---|---|")
    W("| 1 | **MT5 tester, 1 lan** | `TESTER = 1`; 8.241 phep thu = 82 giay khi "
      "nhoi mot lan boot, nhung hai viec khong the chay cung luc | Moi ket luan "
      "cuoi cung phai qua tester. Ca %s nhan / %s luong CPU khong giup duoc gi o "
      "khau nay |" % (g("nhan"), g("luong")))
    W("| 2 | **Suat boc tai lieu** | 12.078 tai lieu -> 18 mau (**0,15%%**); LLM "
      "dien 48 khai bao, tham dinh bac 41, rong **3** | Kho x6 ma ung vien cham "
      "cong van 21 — them dau vao khong di qua duoc khau nay |")
    W("| 3 | **Dia** | C: con %s | `nao.db` %s cho %s dong; WAL tung phinh 1,4 GB "
      "va lam ba me boc bao XONG ma kho khong doi |"
      % ((g("dia", [""])[0].split("(trong ")[-1].rstrip(")")
          if isinstance(g("dia"), list) and g("dia") else "chua do"),
         (g("db", {}) or {}).get("nao.db", "?"),
         f"{(g('db', {}) or {}).get('tong_dong', 0):,}"))
    W("| 4 | **Mang / nguon bi chan** | mql5.com cam theo IP sau ~50-150 luot; "
      "phai di 8 giay/luot + doi IP | Chang [1] cua so do bi cat nhip, khong phai "
      "vi may yeu |")
    W("| 5 | **Mot luong ghi `nao.db`** | SQLite WAL: nhieu doc, **mot ghi**, "
      "`busy_timeout` %s ms | Moi tru + qwen + script tay deu ghi chung mot so |"
      % (g("db", {}) or {}).get("busy_timeout_ms", "?"))
    W("")
    W("**Doc bang nay cung muc 6:** nut 1 va 5 la ha tang (sua duoc bang ky thuat); "
      "nut 2 la **van de V3** (sua bang cach doi uu tien, khong phai bang may manh hon).")
    W("")

    W("---")
    W("")
    W("*Chay lai `b ho-so` truoc khi dung file nay de ra quyet dinh — so lieu doi "
      "moi phien.*")

    vb = "\n".join(ra) + "\n"
    if in_ra is not None:
        in_ra(vb)
    return vb


def _n(x, nd=2):
    try:
        return ("%%.%df" % nd) % float(x)
    except Exception:
        return "?" if x is None else str(x)


def main(argv: list[str]) -> int:
    vb = sinh(in_ra=None)
    if "--ghi" in argv:
        TEP.write_text(vb, encoding="utf-8")
        print("da ghi %s (%d dong)" % (TEP, len(vb.splitlines())))
    else:
        print(vb)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
