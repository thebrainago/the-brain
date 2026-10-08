# -*- coding: utf-8 -*-
"""luoi.py - MO PHONG LUOI/DCA CO TRACH NHIEM, dung duoc lai cho moi cap.

Chu du an 05/09/2026: *"Neu la audcad thi gio cau tim he thong, tinh chinh thong
so cho ra cai tot nhat di. Day chinh la cai toi muon ve quantlab => phat hien ra
tiem nang => backtest thi nghiem ra thong so => he thong"*.

Tiem nang den tu `luan_nguoc`: 13/19 tai khoan DCA song >= 2 nam tren bang xep
hang mql5 danh AUDCAD (nen 28%, p = 0,00035).

## VI SAO KHONG DUNG LAI `ultima_luoi_backtest.py`

Ban do co luat DAY DU va dung, nhung hai cho khong dung duoc:
  1. No chay tren **D1**. Bo nho du an: *"D1 thoi loi suat 11,7 lan"* - luoi bat
     tang theo duong di TRONG bar, ma bar D1 giau het duong di do.
  2. No uoc von = dinh lo treo cua hai ro cong lai, roi lay lai/von lam loi
     suat. Do la mot con SO, khong phai mot duong von: khong co margin call,
     khong co sut giam theo thoi gian, khong biet bao gio chay tai khoan.

## LUAT MO PHONG - khai bao TRUOC khi chay, khong doi giua chung

  1. Khung M15/M5/M1, gia OHLC. **Hai mo hinh khop lenh trong mot bar** (`ThamSo.khop_bar`, xem muc "HAI MO HINH BAR" cuoi
     docstring): `duong_di` (MAC DINH tu 08/10/2026) di tung nen theo duong O->L->H->C (nen xanh) / O->H->L->C (nen do) va khop MOI
     lenh o GIA NGUONG cua no; `cuc_tri` (ban cu) xu ly BAT LOI TRUOC roi chot o CUC TRI cua nen - gia dinh "than trong" nhung sai
     huong voi tia lenh (xem muc do lech).
  2. `che_do`: `mua` (chi ro mua), `ban`, hoac `hai_chieu` (hai ro doc lap).
  3. **Lot PHANG** moi tang. KHONG nhan lot. Martingale da bi kho du an bac bo:
     Lottery Mode x1,3 bien +54.354 thanh -1.550 voi DD 94,4%.
  4. Them mot tang khi gia di nguoc `buoc` pip so voi tang GAN NHAT.
  5. Dong CA RO khi gia cham gia trung binh +/- `tp` pip.
  6. `tran_tang`: cham tran thi NGUNG them tang (van giu, van cho TP). Day la
     tham so quan trong nhat cua lop nay - no la thu duy nhat chan duoi.
  7. **Khong cat lo**, nhung CO stop-out: equity <= `muc_stopout` x margin thi
     dong het va ghi CHAY. Do la cach tai khoan that chet, phai mo phong.
  8. Chi phi: spread THAT tung bar (cot `spread` cua M5/M15 AUDCAD co that -
     `do_tin=SAN`) tru moi lan mo; phi qua dem theo SO DEM x SO VI THE x CHIEU.
     AUDCAD bat doi xung manh: giu MUA -0,263%/nam (ta DUOC tra), giu BAN
     +3,853%/nam. Bo qua cho nay la thoi lai cua luoi hai chieu.
  9. Lai KHONG tai dau tu (lot phang) -> loi suat tinh tren VON, va von la
     tham so, khong phai ket qua.

## DON VI

Tinh het bang **dong tien BAO GIA** (CAD voi AUDCAD). Loi suat la ty so nen
khong phu thuoc quy doi - tranh han cai bay "doi dong tien tai khoan".
1 pip = 0,0001. Voi 0,01 lot: 1 pip = 0,01 x 100.000 x 0,0001 = 1,0 don vi bao gia.

## QUY CACH THEO MA (03/10/2026)

Truoc ngay nay pip / hop dong / point / phi qua dem nam CUNG trong `_mot_ro` va `chay`, nen engine chi dung duoc cho
AUDCAD. Ma khac bi chan o `nc_thi_nghiem.danh_gia_luoi` - trong khi 18/31 nguoi thang song >= 2 nam tren MQL5 la luoi/DCA
va dung o USDCHF / AUDCHF / USDCAD / EURUSD... (`tai_lieu/NGUON_NGUOI_THANG.md`). Nay hang so nam trong `QuyCach`:

  - `chay(df, ts, von)` KHONG truyen `qc` = `QC_AUDCAD` = hang so cu: ket qua y het tung bit (golden trong
    `test_luoi_quy_cach.py`, sinh tu ban TRUOC khi sua).
  - Ma khac: `quy_cach_cho(ma, gia, cp)`. Lop FX chuan (7 dong tien G7-ish, 5 chu so) lay phi qua dem + spread tu MO HINH
    CHI PHI do duoc (`cp`), nen `do_tin` di theo. Cap JPY, vang: hinh hoc hop dong phai DO TU `symbol_info` roi ghi vao
    `config/luoi_quy_cach.json` (`da_doi_chieu: true`) - chua ghi thi tu choi, khong doan. Chi so, crypto, exotic, micro:
    chua ho tro.
  - Phi KHONG bao gio doc tu file ghi de: chi pip / hop_dong / point / spread_du_phong / von_quy_doi.

CHUA hieu chuan voi MT5 tester o bat ky ma nao (`LuoiDoiXung.mq5` da mat cung VPS 02/10): xep hang va hinh dang dung duoc,
con lai tuyet doi phai chay tester cung bo tham so truoc khi tin. O muc "lot cham tran DD 80%" ket qua bat bien theo co
hop dong va lot; cai that su co the sai la dinh nghia pip, doi spread -> gia (point), va swap - ca ba nam o day.

## HAI MO HINH BAR (08/10/2026) - vi sao co `khop_bar`

Chu du an hoi tai sao 24 gio / hang nghin phep thu chi ra mot he lai 13%/nam DD > 30%. Mot nguyen nhan CO BANG CHUNG o day
(so lieu day du, cach doc va gioi han: `reports/lech_engine_EURCAD.md`):

  1. VOI MT5 TESTER (125 o hieu chuan EURCAD / AUDCAD / NZDCAD, engine ban 3 = `cuc_tri` vs tester model 0): o `tia_lenh=True` (68 o)
     engine cao hon tester o 50/68 o; o co tester >= +1%/nam (32 o) ty le engine/tester TRUNG VI x2,2 (M15 x3,2; cao nhat x16); o khong
     tia (57 o): bo phan swap engine thi ~ tester (chenh trung vi +0,0 diem/nam). 15 o xep dau theo engine DEU la o tia lenh: engine
     +40..+154 %/nam, tester -33..+53 %/nam (cua so ~6 thang quy ra nam), engine cao hon tester o 15/15; thu hang hai ben van tuong
     quan (Spearman 0,79) nhung top-15 chi trung 8/15. Quet tham so xep hang bang engine nay CHON DUNG loai o hong nhat.
  2. VOI CHINH EA (`ea_LuoiDayDu.mq5` chay tren san gia C++, cung mot duong gia, chuoi tick min `paso` = 1e-6 gia; 12 cau hinh x 4 thu tu
     cao/thap trong bar): `cuc_tri` lac quan +12..+55% o cau hinh chot theo tien / tia lenh (chot_tien +37, chot_tien_tia +31..+37,
     chot_tien_tia_cho_lui +20..+55, chot_tien_cho_lui +12..+27, tn5 +14..+15); `duong_di` nam trong +-5% o thu tu THEO NEN (thu tu ma
     mo hinh gia dinh) o ca 12 cau hinh.
  3. TREN DU LIEU TONG HOP (random walk, khong chi phi, ky vong that = 0; `python -m nhan.kiem_do_phan_giai`, 16 hat x 2 ngay, don vi
     bao gia, lech GHEP DOI so voi chay tung tick) sai lech cua mo hinh tang theo cap bar (k = 60 / 300 / 900 tick ~ M1 / M5 / M15):
         cau hinh        cuc_tri                    duong_di (sai so chuan 1-3, nhan_lot 16-32)
         tia             +11 / +58 / +184           +1 / +1 / -7
         chot_tien       +14 / +47 / +111           -0,2 / -1 / -8
         tia_cho_lui     +7 / +33 / +93             +1 / +2 / +1,5
         cho_lui         +0,6 / +8,5 / +22          0 / -1 / -3
         nhan_lot        +32 / +407 / +613          -10 / -14 / -54
         khong_tia       0 / +3,5 / +18             0 / -0,4 / -2
     Cau hinh khong tia lenh gan nhu khong lech o khung nho; tia lenh, chot theo tien va lot nhan (cung la loai ma xep hang chon dau
     bang) lech nhieu nhat va lech THEO KHUNG, nen chay M15 de "nhanh" la dung cai khung mo hinh sai nhat.

  `cuc_tri` (ban cu, `_mot_ro`): moi bar xu ly theo thu tu CO DINH "them tang theo low -> tia cap o HIGH -> TP so voi high". Hai loi:
    (a) mot tia cap duoc chot o CUC TRI cua bar chu khong o gia nguong cua no (cap co lai >= bien_cap pip se bi ghi lai o muc
        high - tang them hang chuc pip), va toi 999 cap/bar; spread cua tia bi tru hai lan;
    (b) thu tu trong bar luon la thuan loi: tang hap thu duoc mot cu nhun nguoc roi chot o dinh, bar nao cung vay.
    Hai thu cong lai tao ra loi nhuan tu khong khi do phan giai bar thap (bar M15 gom ~900 tick).
  `duong_di` (MAC DINH): moi bar di tren duong O -> L -> H -> C neu nen xanh (C >= O, ke ca doji), O -> H -> L -> C neu nen do - duong NGAN
    NHAT qua ca hai cuc tri (chenh lech quang duong giua hai thu tu = 2(O-C)). Tren moi doan don dieu: doan NGUOC chieu ro them tang
    (khop o moc, hoac o gia dau doan neu nhay gia vuot moc); doan THUAN chieu chot tia / TP o GIA NGUONG, nhieu lan lien tiep trong cung
    doan (ro chot xong mo lai ngay o gia chot, noi tiep tu gia khop). Spread tinh MOT lan luc mo lenh (khong tinh them o tia, giong EA
    va tester); lo treo = lo noi lon nhat TREN CA DUONG chu khong chi o low. Cham dung moc (<= `EPS_CHAM_PIP` = 1e-6 pip) la khop,
    nhu EA / tester: khong de nhieu double 1e-16 quyet dinh co khop hay khong.
  Chi `hieu_chuan_luoi` duoc chon `cuc_tri` (de do lech); duong nghien cuu cua AI chi nhan `duong_di` (`MO_HINH_BAR_NGHIEN_CUU`).

  CON THIEU (khong duoc bao la da hieu chuan):
    (a) THU TU CAO/THAP TRONG BAR: bar OHLC khong cho biet low hay high den truoc; `duong_di` dung mau nen. Khi EA chay theo thu tu khac
        (thap truoc / cao truoc / xen ke), cau hinh cho-gia-lui bi `duong_di` danh gia THAP hon EA 12-33% (cho_lui -33 / -29 / -32,
        tia_cho_lui -23 / -32 / -19, chot_tien_tia_cho_lui -24 / -16 / -12, buoc_co -17 / -17 / -15, chot_tien_cho_lui -4 .. -15)
        va cau hinh chi-ban (ban_cong) -14,7% o 2/4 thu tu; cac cau hinh con lai (mua_phang, hai_nhan_buoc, tn5, chot_tien,
        chot_tien_tia, buoc_thu) lech <= 7%. Lech am = engine BI QUAN, tuc la an toan cho xep hang, nhung co the loai nham o thang.
        Tren du lieu that M15 do bien do nen lon, nen xep hang xong van phai qua tester (hoac M1).
    (b) SWAP: tester bao 0,00 o ca 125 o, engine tinh trung vi -4,4 %/nam (121/125 o am, thap nhat -32) - chua doi chieu duoc, chua
        biet tester khong tinh hay cach doc bao cao bi sai.
    (c) cau truc tick that, open bar that (engine suy open = close bar truoc kep vao [low, high]); gap thuan chieu vao bar do rong 0
        hoan chot tia / TP sang bar sau.
    (d) luoi thap phan: chuoi tick thua (`paso` = 1e-5 = 1 point) sinh nhieu luong tu hoa (cung mot cau hinh lech vai % tuy
        hat) - dung 1e-6 (xem `test_ea_luoi_day_du.py`).
  Chay lai 125 o hieu chuan bang `hieu_chuan_luoi` voi `chi_engine=true` de do phan con lai bang engine moi (khong can tester lai).
  Test: `test_luoi_duong_di.py` (hinh hoc khop lenh, tu nhat tren doan tick, khong lech theo khung, MC), `test_luoi_nhan.py`,
  `test_ea_luoi_day_du.py` (engine vs EA tren cung duong gia).
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from nhan import chi_phi as CP
from nhan import luoi_nhan as LN

LAB = Path(__file__).resolve().parent.parent
#: Hinh hoc hop dong DO TAY cho ma ngoai lop FX chuan (cap JPY, vang...). Chi pip / hop_dong / point / ...; PHI khong o day.
FILE_QUY_CACH = LAB / "config" / "luoi_quy_cach.json"
_TEN_FILE = "config/luoi_quy_cach.json"

PIP = 1e-4                  # = QC_AUDCAD.pip (giu cho ma cu)
HOP_DONG = 100_000.0        # = QC_AUDCAD.hop_dong


@dataclass
class ThamSo:
    buoc: float = 60.0          # pip, khoang cach giua cac tang
    tp: float = 40.0            # pip, TP tinh tu gia trung binh
    tran_tang: int = 20         # toi da bao nhieu tang moi ro
    che_do: str = "hai_chieu"   # mua | ban | hai_chieu
    lot: float = 0.01
    muc_stopout: float = 0.5    # equity <= 0,5 x margin -> chay
    don_bay: float = 100.0
    #: Sau khi mot ro chot TP, KHONG mo lai L1 ngay tai do ma cho gia LUI
    #: `cho_lui` pip nguoc chieu roi moi vao. 0 = mo lai ngay (ban goc).
    #: Bo nho `eurcad-entry-cho-lui`: tren tester MT5 THAT, luat nay nang
    #: EURCAD tu 7,9% len 12,1%/nam VA giam sut giam - va no lat nguoc ket
    #: luan cua ban Python truoc do rang "entry vo dung".
    cho_lui: float = 0.0
    #: TANG LOT THEO TANG - chu du an cho phep 05/09: *"Cho phep tang lot, cho
    #: phep dca. Chi can tinh sao ra con so rui ro vua phai van duoc"*.
    #: `phang` = lot deu (ban goc, an toan nhat).
    #: `nhan`  = lot_i = lot * he_so^(i-1)      (nhan luy thua - martingale)
    #: `cong`  = lot_i = lot * (1 + he_so*(i-1)) (tang tuyen tinh - hien hon)
    #: Kho du an da bac bo martingale MOT LAN roi: Lottery Mode x1,3 tren LOT
    #: bien +54.354 thanh -1.550 voi DD 94,4%. Nhung do la martingale sau khi
    #: THUA MOT LENH, khac han tang lot theo TANG LUOI (o day gia da di nguoc
    #: that va tang moi co gia tot hon). Hai thu khac nhau nen phai do lai,
    #: khong duoc suy tu ket qua kia.
    kieu_lot: str = "phang"
    he_so_lot: float = 1.0

    # ---- CO CHE THAT cua EA luoi, boc tu `LuoiDoiXung.mq5` cua du an ----
    # Chu du an 05/09: *"Co rat nhieu con EA co kha nang hedging va tia lenh.
    # No dung cac lenh buy sell stop, chot tia lenh va nhieu co che. Chu khong
    # phai moi dca thuan"*. Dung - va ban dau cua file nay chi co DCA thuan,
    # ngheo hon chinh cai du an da boc duoc tu EA that.
    #
    #: TIA LENH (`BatChotCap`/`BienCapPip`): ghep lenh SAU NHAT voi lenh DAU
    #: TIEN, dong ca cap khi tong lai cua cap >= `bien_cap` pip. Cat ngan thang
    #: ladder ma khong phai cho ca ro ve hoa von. `cap_moi_bar` = 1 la tia THAT
    #: tung phan; 999 la dong day chuyen (khac han nhau).
    tia_lenh: bool = False
    bien_cap: float = 4.0
    cap_moi_bar: int = 999
    #: CHOT CA RO THEO TIEN (`ChotTien_0v01`) thay vi theo pip tu gia trung
    #: binh. Khac nhau khi ro co nhieu tang: TP pip co dinh cho ro 10 tang an
    #: gap 10 lan ro 1 tang, con chot theo tien thi khong.
    #: DON VI: TIEN bao gia tren 0,01 lot (nguong that = chot_tien * lot/0,01), KHONG
    #: phai pip. Cap FX chuan cung thang do voi AUDCAD; cap JPY (1 pip = 0,01 gia) cung
    #: so pip ra so tien gan x100 nen chot_tien phai nhan len tuong ung.
    chot_tien: float = 0.0
    #: DUNG LO TOAN CUC (`DungLo_0v01`): dong SACH ca hai ro khi lo noi cong lai
    #: vuot nguong. Day la thu bien "khong cat lo" thanh "cat lo co tran" - va
    #: no la co che doi han hinh dang duoi rui ro.
    #: !! CHUA CAI DAT (03/10/2026 ra soat): `_mot_ro` chay hai ro ROI NHAU nen khong thay lo noi cong
    #: hai chieu; truong nay khai bao tu truoc nhung khong duoc doc o dau ca. `chay` TU CHOI gia tri != 0
    #: (xem `CHUA_CAI_DAT`) de khong ai tuong luoi da co cat lo trong khi ket qua y het 0.
    dung_lo_tong: float = 0.0
    #: BUOC GIAN DAN (`HeSoBuoc`/`BuocTranPip`): khoang cach tang thu k =
    #: buoc * he_so_buoc^(k-1), chan tren `buoc_tran`. >1 = gian dan (song lau
    #: hon trong xu huong), <1 = day dan.
    he_so_buoc: float = 1.0
    buoc_tran: float = 400.0
    #: MO HINH KHOP LENH TRONG MOT BAR (08/10/2026, xem "HAI MO HINH BAR" o dau file). Day KHONG phai tham so chien luoc ma la lua
    #: chon cach mo phong; EA that chay theo tick nen khong co input tuong ung (`ea_gia_lap.KHONG_CO_TRONG_EA`).
    #: `duong_di` = di duong O-L-H-C / O-H-L-C, khop o gia nguong (mac dinh)
    #: `cuc_tri`  = ban cu: bat loi truoc, chot o cuc tri cua bar. LAC QUAN voi tia lenh (x2,5-x7 so voi tester); chi giu de
    #:             tai lap so cu va lam moc so sanh.
    khop_bar: str = "duong_di"

    # ---- CO CHE THOAT + LOC GIO (08/10/2026): de TAI LAP nguoi thang da boc tu lich su lenh that (`reports/boc_<id>_XAUUSD.json`: 36-62% ro
    # dong LO, vao lenh dung vao vai gio nhat dinh). MAC DINH 0 = TAT, ket qua cu GIU NGUYEN TUNG BIT. Chi mo hinh `duong_di` (`cuc_tri` tu
    # choi, xem `TINH_NANG_DUONG_DI`). Cac so gio can cot thoi gian cua bar (`DuLieuChay.tg`), khong can cot open.
    #: CAT LO CA RO theo PIP: dong het ro khi gia di nguoc >= `cat_lo_pip` pip so voi gia trung binh CO TRONG SO cua ro (tinh lai sau moi
    #: tang). Khop o dung moc cat (nhay gia thi o gia nhay). 0 = khong cat.
    cat_lo_pip: float = 0.0
    #: CAT LO CA RO theo TIEN: dong het ro khi lo noi >= nguong. DON VI nhu `chot_tien`: tien bao gia tren 0,01 lot goc (nguong that =
    #: cat_lo_tien * lot/0,01). Dat ca hai thi muc nao gan gia trung binh hon cat truoc. 0 = khong cat.
    cat_lo_tien: float = 0.0
    #: THOAT THEO THOI GIAN (gio): dong het ro o GIA MO cua bar dau tien cach luc mo ro >= `thoat_gio` gio (luc mo = gio mo cua bar chua
    #: lenh dau). 0 = khong thoat theo gio.
    thoat_gio: float = 0.0
    #: NGHI sau mot lan cat lo / thoat gio (gio): chua mo ro MOI cho den `nghi_gio` gio sau luc do. 0 = vao lai ngay. Chot loi (TP, tia) khong nghi.
    nghi_gio: float = 0.0
    #: LOC GIO VAO LENH: chi MO RO MOI khi gio trong ngay cua cot thoi gian du lieu (gio may chu) nam trong [gio_vao_tu, gio_vao_den);
    #: tu > den = qua nua dem (22 -> 4). tu == den = TAT. Khong chan them tang cua ro dang mo, khong chan chot / cat.
    #: Can khung <= H1 (khung ngay: moi bar mo luc 00:00). Lam tron den giay.
    gio_vao_tu: float = 0.0
    gio_vao_den: float = 0.0


#: Cac truong chi mo hinh `duong_di` co (mo hinh `cuc_tri` cu khong cai dat): dat != 0 o `cuc_tri` bi TU CHOI (khong am tham bo qua).
TINH_NANG_DUONG_DI = ("cat_lo_pip", "cat_lo_tien", "thoat_gio", "nghi_gio", "gio_vao_tu", "gio_vao_den")


def tinh_nang_duong_di_dang_bat(ts) -> list[str]:
    """Ten cac truong cua `TINH_NANG_DUONG_DI` dang != 0 trong `ts` (ThamSo hoac dict)."""
    lay = ts.get if isinstance(ts, dict) else (lambda k, d=0: getattr(ts, k, d))
    return [k for k in TINH_NANG_DUONG_DI if lay(k, 0)]


def _giay(gio) -> float:
    """So gio -> so giay NGUYEN (lam tron nua len, `floor(x*3600 + 0.5)`: y het nhan C va EA) de `1.1` gio khong lech vi nhi phan."""
    return float(math.floor(float(gio) * 3600.0 + 0.5))


def cau_hinh_gio(ts) -> tuple[float, float, float, float]:
    """(thoat_s, nghi_s, gio_tu_s, gio_den_s): bon tinh nang gio cua `ts` (ThamSo hoac dict) quy ra GIAY NGUYEN. Ham DUY NHAT dinh nghia
    "tinh nang nao dang bat" cho engine Python, nhan C va nguoi goi: thoat_s > 0 / nghi_s > 0 / (gio_tu_s != gio_den_s)."""
    lay = ts.get if isinstance(ts, dict) else (lambda k, d=0: getattr(ts, k, d))
    return (_giay(lay("thoat_gio", 0)), _giay(lay("nghi_gio", 0)), _giay(lay("gio_vao_tu", 0)), _giay(lay("gio_vao_den", 0)))


def can_cot_thoi_gian(ts) -> bool:
    """`ts` dung tinh nang nao can cot thoi gian cua bar (`DuLieuChay.tg`)? Cat lo thuan (pip / tien) khong can. Gia tri khong huu han
    (ngoai mien) tra True de nguoi goi di tiep den buoc kiem mien `mien_duong_di` va bi tu choi o do."""
    try:
        thoat_s, nghi_s, tu_s, den_s = cau_hinh_gio(ts)
    except (TypeError, ValueError, OverflowError):
        return True
    return thoat_s > 0 or nghi_s > 0 or tu_s != den_s


#: Khung lon hon nay (giay giua hai bar lien tiep, trung vi) thi loc gio vao lenh vo nghia: tu choi thay vi am tham ra ket qua sai.
KHUNG_TOI_DA_LOC_GIO_GIAY = 3600.0


#: Gia tri hop le cua `ThamSo.khop_bar`.
MO_HINH_BAR = ("cuc_tri", "duong_di")
#: Mo hinh bar DUOC PHEP o DUONG NGHIEN CUU cua AI (thu_luoi / quet_luoi / niem_phong_luoi / xac_nhan trong `nc_thi_nghiem`).
#: `cuc_tri` chi con de DO LECH (`hieu_chuan_luoi`, test, doi chieu EA): no lac quan +15..+40% so voi EA tren cung duong gia va
#: x2,5-x7 so voi tester o cac o tia lenh M15 - xep hang hay niem phong bang no la lap lai dung loi "hang nghin phep thu chon ra
#: he ao" (muc HAI MO HINH BAR). Them mo hinh moi vao day SAU KHI no co bang chung nho EA / tester, khong truoc.
MO_HINH_BAR_NGHIEN_CUU = ("duong_di",)


def kiem_khop_bar(ts) -> str:
    """Tra `ts.khop_bar` neu hop le, ValueError neu khong (khong doan: ten sai se am tham chay mo hinh sai)."""
    kb = ts.khop_bar
    if not isinstance(kb, str) or kb not in MO_HINH_BAR:
        raise ValueError("ThamSo.khop_bar phai la mot trong %s, nhan %r" % (MO_HINH_BAR, kb))
    return kb


@dataclass
class KetQuaLuoi:
    lai_rong: float = 0.0
    lai_gop: float = 0.0
    phi_spread: float = 0.0
    phi_swap: float = 0.0
    so_ro: int = 0                   # so ro dong bang CHOT LOI (TP); ro bi cat lo / thoat gio dem rieng o duoi
    so_lenh: int = 0
    tang_max: int = 0
    #: So ro dong bang CAT LO (`cat_lo_pip` / `cat_lo_tien`) va bang THOAT GIO (`thoat_gio`). 0 khi hai tinh nang tat.
    so_cat: int = 0
    so_gio: int = 0
    lo_treo_dinh: float = 0.0        # don vi bao gia
    chay: bool = False
    bar_chay: int | None = None
    so_nam: float = 0.0
    duong_equity: np.ndarray | None = field(default=None, repr=False)
    #: Margin TINH (cung con so voi kiem stop-out, xap xi UOC CAO: tang_max x notional / don_bay) o lot cua chinh lan chay.
    #: notional = margin * ThamSo.don_bay. `niem_phong_luoi` dung no de chan don bay dinh khi chot lot.
    margin: float = 0.0
    #: DataFrame lenh mo phong (chi co khi `chay(..., ghi_lenh=True)`): mo, dong, chieu, lot, gia_mo, gia_dong, tang, ro,
    #: ly_do. Lenh chua dong den het du lieu co `dong` = NaT. Cung luoc do voi lich su lenh that (`nhan/boc_lich_su`).
    lenh: object | None = field(default=None, repr=False)


#: Truong cua `ThamSo` da khai bao nhung engine KHONG doc. Dat != 0 cho ket qua y het 0 (khong loi, khong canh bao)
#: - dung kieu loi "bo phan co ton tai nhung khong nam tren duong chay". Them ten vao day khi khai bao truoc cai dat.
CHUA_CAI_DAT = ("dung_lo_tong",)


def tham_so_chua_cai_dat(ts) -> list[str]:
    """Ten cac truong `ts` (ThamSo hoac dict) dang dat != 0 ma engine chua cai dat."""
    lay = ts.get if isinstance(ts, dict) else (lambda k, d=0: getattr(ts, k, d))
    return [k for k in CHUA_CAI_DAT if lay(k, 0)]


# ------------------------------------------------------------------ QUY CACH THEO MA
@dataclass(frozen=True)
class QuyCach:
    """Hang so KINH TE cua MOT ma. Mac dinh cua dataclass = AUDCAD cu (`QC_AUDCAD`).

      pip, point       kich thuoc pip; point cua cot `spread` (bar MT5 tinh spread bang POINT)
      hop_dong         don vi co so tren 1,0 lot
      phi_nam_mua/ban  phi qua dem, ty le/nam tren notional, theo CHIEU (am = duoc tra)
      spread_du_phong  spread (don vi GIA) khi bar khong co cot `spread`, hoac bar spread = 0
      von_quy_doi      von nguoi dung (dong tai khoan) x he so nay = von tinh bang dong BAO GIA (chi danh_gia_luoi dung)
      do_tin           DO | SAN | KHAI - cung nghia voi `MoHinhChiPhi.do_tin`
      da_doi_chieu     pip/hop_dong/point da doi chieu voi `symbol_info` (FX chuan: true theo lop; JPY/vang: ghi tay)
    """
    ma: str = "AUDCAD"
    pip: float = 1e-4
    hop_dong: float = 100_000.0
    point: float = 1e-5
    phi_nam_mua: float = -0.00263
    phi_nam_ban: float = 0.03853
    spread_du_phong: float = 2e-4
    von_quy_doi: float = 1.0
    do_tin: str = "SAN"
    da_doi_chieu: bool = True
    nguon: str = ""


#: Hang so cu cua luoi.py - DUNG NGUYEN, vi ket qua AUDCAD cua lab (holdout +13,26%/nam) den tu day.
QC_AUDCAD = QuyCach(ma="AUDCAD", nguon="hang so cu cua luoi.py: phi qua dem AUDCAD (mua -0,263%/nam, ban +3,853%/nam), "
                                      "point 1e-5, spread du phong 2 pip")

_TIEN_TE = frozenset({"USD", "EUR", "GBP", "AUD", "NZD", "CAD", "CHF"})
_KIM_LOAI = frozenset({"XAUUSD", "XAGUSD"})
#: Mac dinh hinh hoc theo LOP. Chi lop da biet chac moi co; kim loai / ma la khong co -> phai do.
_MAC_DINH_LOP = {"fx_chuan": {"pip": 1e-4, "hop_dong": 100_000.0, "point": 1e-5},
                 "fx_jpy": {"pip": 1e-2, "hop_dong": 100_000.0, "point": 1e-3}}
_NGUON_LOP = {"fx_chuan": "lop FX chuan 5 chu so (pip 1e-4, hop dong 100.000, point 1e-5)",
              "fx_jpy": "lop FX cap JPY (pip 0,01, hop dong 100.000, point 1e-3)"}
_KHOA_GHI_DE = ("pip", "hop_dong", "point", "spread_du_phong", "von_quy_doi", "da_doi_chieu", "nguon")
_SO_DUONG = ("pip", "hop_dong", "point", "spread_du_phong", "von_quy_doi")


def lop_quy_cach(ma: str) -> str:
    """audcad | tong_hop | fx_chuan | fx_jpy | kim_loai | khong_ho_tro - chi theo TEN, khong doc du lieu.

    `AUDCAD` khop theo doan chuoi nhu ban cu (`XM_AUDCAD`, `AUDCADM`...). Ten san/hau to di qua `chuan_hoa_phoi_nhiem`
    (mot nguon su that ve ten symbol cua du an); phan con lai phai la dung 6 chu cai cua hai dong tien biet.
    """
    m = str(ma).upper().strip()
    if m.startswith("TONG_HOP_"):
        return "tong_hop"
    if "AUDCAD" in m:
        return "audcad"
    if "MICRO" in m:
        return "khong_ho_tro"                  # hop dong 1.000, khong phai 100.000
    g = CP.chuan_hoa_phoi_nhiem(m)
    if len(g) != 6 or not g.isalpha():
        return "khong_ho_tro"
    if g in _KIM_LOAI:
        return "kim_loai"
    co_so, bao_gia = g[:3], g[3:]
    if co_so not in _TIEN_TE or co_so == bao_gia:
        return "khong_ho_tro"
    if bao_gia in _TIEN_TE:
        return "fx_chuan"
    return "fx_jpy" if bao_gia == "JPY" else "khong_ho_tro"


def _doc_ghi_de() -> tuple[dict, str]:
    """(bang theo MA VIET HOA, loi). File hong -> ({}, ly do): ma FX chuan khong bi anh huong."""
    try:
        txt = FILE_QUY_CACH.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return {}, ""
    except OSError as e:
        return {}, "khong doc duoc %s: %s" % (_TEN_FILE, e)
    try:
        d = json.loads(txt)
    except ValueError as e:
        return {}, "%s khong phai JSON hop le: %s" % (_TEN_FILE, e)
    if not isinstance(d, dict):
        return {}, "%s phai la mot object {MA: {...}}" % _TEN_FILE
    return {str(k).upper(): v for k, v in d.items()}, ""


def quy_cach_cho(ma: str, gia_dien_hinh: float | None = None, cp=None) -> tuple["QuyCach | None", str]:
    """(QuyCach, "") hoac (None, ly do tu choi). `cp` = `MoHinhChiPhi` cua chinh doan se chay.

    AUDCAD / TONG_HOP: `QC_AUDCAD`, KHONG doc `cp` (giu nguyen ket qua cu). Ma khac: pip/hop_dong/point theo LOP (hoac
    ghi de da doi chieu), phi qua dem + spread tu `cp` kem `do_tin`; khong co `cp` -> phi KHAI BAO theo lop.
    """
    m = str(ma).upper().strip()
    lop = lop_quy_cach(m)
    if lop in ("audcad", "tong_hop"):
        return QC_AUDCAD, ""
    bang, loi_file = _doc_ghi_de()
    gd = bang.get(m, bang.get(CP.chuan_hoa_phoi_nhiem(m)))
    luu_y = (" (luu y: %s)" % loi_file) if loi_file else ""
    base = dict(_MAC_DINH_LOP.get(lop, {}))
    da_doi = lop == "fx_chuan"
    nguon = _NGUON_LOP.get(lop, "")
    sp_tay, von_qd = None, 1.0
    if gd is None:
        if lop == "khong_ho_tro":
            return None, ("%s: chua ho tro cho luoi (chi cap FX chuan 5 chu so; chi so/crypto/exotic/micro co hop dong "
                          "va phi khac). Muon thu: ghi pip/hop_dong/point do tu symbol_info vao %s%s"
                          % (m, _TEN_FILE, luu_y))
        if not da_doi:
            return None, ("%s (%s): pip/hop_dong/point CHUA doi chieu voi symbol_info - may nha do roi ghi "
                          '{"%s": {"pip": .., "hop_dong": .., "point": .., "da_doi_chieu": true}} vao %s%s'
                          % (m, lop, m, _TEN_FILE, luu_y))
    else:
        if not isinstance(gd, dict):
            return None, "%s: muc trong %s phai la object" % (m, _TEN_FILE)
        la = sorted(set(gd) - set(_KHOA_GHI_DE))
        if la:
            return None, ("%s: khoa la %s trong %s (hop le: %s). Phi qua dem/spread luon lay tu mo hinh chi phi "
                          "do duoc, khong ghi tay" % (m, la, _TEN_FILE, ", ".join(_KHOA_GHI_DE)))
        for k in _SO_DUONG:
            if k not in gd:
                continue
            try:
                v = float(gd[k])
            except (TypeError, ValueError):
                v = float("nan")
            if not (math.isfinite(v) and v > 0):
                return None, "%s: %s trong %s phai la so duong, nhan %r" % (m, k, _TEN_FILE, gd[k])
            if k == "spread_du_phong":
                sp_tay = v
            elif k == "von_quy_doi":
                von_qd = v
            else:
                base[k] = v
        da_doi = bool(gd.get("da_doi_chieu", da_doi))
        nguon = str(gd.get("nguon") or "ghi de trong " + _TEN_FILE)
        thieu = [k for k in ("pip", "hop_dong", "point") if k not in base]
        if thieu:
            return None, "%s: thieu %s trong %s" % (m, ", ".join(thieu), _TEN_FILE)
        if not da_doi:
            return None, ("%s: da_doi_chieu = false trong %s - chua doi chieu voi symbol_info nen khong chay"
                          % (m, _TEN_FILE))
    if cp is not None:
        pm, pb, do_tin = float(cp.phi_nam_mua), float(cp.phi_nam_ban), str(cp.do_tin)
        sp_cp = float(getattr(cp, "spread_frac_chung", 0.0) or 0.0) * float(gia_dien_hinh or 0.0)
        nguon_phi = "phi + spread tu mo hinh chi phi (do_tin=%s)" % do_tin
    else:
        lt = {"fx_chuan": "fx", "fx_jpy": "fx", "kim_loai": "vang"}.get(lop) or CP._loai_tai_san(m)
        q = CP.PHI_QUAN_SAT[lt]
        pm, pb, do_tin, sp_cp = float(q["phi_nam_mua"]), float(q["phi_nam_ban"]), "KHAI", 0.0
        nguon_phi = "phi KHAI BAO theo lop '%s' (chua co mo hinh chi phi do duoc)" % lt
    sp = sp_tay if sp_tay else (sp_cp if sp_cp > 0 else 2.0 * base["pip"])
    return QuyCach(ma=m, pip=base["pip"], hop_dong=base["hop_dong"], point=base["point"], phi_nam_mua=pm,
                   phi_nam_ban=pb, spread_du_phong=sp, von_quy_doi=von_qd, do_tin=do_tin, da_doi_chieu=True,
                   nguon="%s; %s" % (nguon, nguon_phi)), ""


#: Tang MOI KHI engine doi SO LIEU ra (khong tinh khi chi doi cach tinh, vd nhan C): di vao van tay cua `thu_luoi` de so tay
#: khong tai dung ket qua cua ban engine cu. 1 = ban dau · 2 = sua lech mot nac khoang cach gian dan (1ba9023) ·
#: 3 = bar 0 chi tru spread lenh dau (03/10/2026) · 4 = mo hinh bar `duong_di` thanh MAC DINH (08/10/2026): tia lenh khop o gia
#: nguong thay vi cuc tri nen ket qua cac cau hinh tia lenh thap hon nhieu; ket qua cu = `khop_bar="cuc_tri"` (van chay duoc).
PHIEN_BAN_ENGINE = 4


def khoa_quy_cach(qc: QuyCach) -> str:
    """Dau van tay cac so lam doi ket qua - dua vao van tay thi nghiem de KHONG lay lai ket qua cu khi phi doi."""
    d = {k: getattr(qc, k) for k in ("pip", "hop_dong", "point", "phi_nam_mua", "phi_nam_ban", "spread_du_phong",
                                     "von_quy_doi", "do_tin")}
    return hashlib.sha1(json.dumps(d, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _mot_ro(hi, lo, cl, spread_gia, dem, chieu: int, ts: ThamSo, qc: QuyCach | None = None,
            ghi: list | None = None):
    """Mo phong MOT ro. Tra (lai_cong_don_theo_bar, lo_treo_theo_bar, thong ke).

    `ghi` (list) bat che do GHI LENH: moi lenh mo/dong duoc them vao list nhu mot tuple
    `("mo", bar, gia, lot, id, tang, ro)` / `("dong", bar, gia, id, ly_do)` (ly_do `tp` hoac `tia`).
    Chi them dong ghi, KHONG doi so nao - `ghi=None` cho ket qua y het ban truoc khi co tham so nay.

    `lai_cong_don_theo_bar` la lai DA CHOT tich luy (rong phi) den tung bar.
    `lo_treo_theo_bar` la lo chua chot cua cac tang dang mo tai bar do.
    Tach hai cai nay ra vi equity = von + lai_chot - lo_treo, va chi co cach
    do moi kiem duoc margin call.
    """
    bat = tinh_nang_duong_di_dang_bat(ts)
    if bat:
        raise ValueError("khop_bar='cuc_tri' (ban cu) khong cai dat %s - chi mo hinh 'duong_di' co cat lo / thoat gio / loc gio" % bat)
    qc = qc or QC_AUDCAD
    pip, hop = qc.pip, qc.hop_dong
    n = len(cl)
    gia_pip = ts.lot * hop * pip               # gia tri 1 pip cua 1 tang
    b = ts.buoc * pip
    t = ts.tp * pip
    # phi qua dem: ty le/nam tren notional, theo chieu
    ty_le = qc.phi_nam_mua if chieu > 0 else qc.phi_nam_ban
    notional_1 = ts.lot * hop                  # tinh bang dong CO SO
    def _lot(k: int) -> float:
        """Lot cua tang thu k (0-based)."""
        if ts.kieu_lot == "nhan":
            return ts.lot * (ts.he_so_lot ** k)
        if ts.kieu_lot == "cong":
            return ts.lot * (1.0 + ts.he_so_lot * k)
        return ts.lot

    def _buoc(k: int) -> float:
        """Khoang cach tu tang k den tang k+1 (pip, k tinh tu 0), co gian dan va tran. Goi voi `so_tang - 1`:
        khoang cach DAU TIEN = `buoc` (truoc 03/10/2026 goi nham `so_tang` -> khoang dau = buoc * he_so_buoc)."""
        if ts.he_so_buoc == 1.0:
            return ts.buoc
        return min(ts.buoc * (ts.he_so_buoc ** k), ts.buoc_tran)

    # (gia, lot) - lot GAN VAO LENH luc mo. Truoc 05/09 day la list gia va lot
    # duoc tra bang `_lot(vi_tri_trong_list)`; khi TIA LENH cat hai dau thi cac
    # tang con lai bi DANH SO LAI va lot cua chung doi ngam. Loi do thoi ket
    # qua len vi no am tham bo di dung nhung tang lot to nhat.
    vao = [(cl[0], _lot(0))]
    if ghi is not None:
        vao_id, n_id, ro_hien = [0], 1, 0           # id lenh song SONG SONG voi `vao`; ro_hien = so ro dang chay
        ghi.append(("mo", 0, float(cl[0]), float(_lot(0)), 0, 0, 0))
    cho = 0.0          # != 0: dang CHO gia lui toi muc nay moi mo L1
    lai = 0.0
    phi_sp = 0.0
    phi_sw = 0.0
    so_ro = so_lenh = so_cap = 0
    so_tang = 1          # bao nhieu tang DA MO cua ro hien tai (khong tut khi tia)
    tang_max = 1
    lai_arr = np.empty(n)
    treo_arr = np.empty(n)
    # phi mo lenh dau
    phi_sp += spread_gia[0] * ts.lot * hop
    phi_sp_bar0 = phi_sp        # chi phi DA PHAT SINH luc bar 0 (khong phai tong spread ca chuoi - xem cuoi ham)
    so_lenh += 1
    tong_lot = ts.lot
    for i in range(1, n):
        # ---- 0. dang CHO gia lui de mo L1 ----
        if cho:
            if (lo[i] <= cho) if chieu > 0 else (hi[i] >= cho):
                vao = [(cho, _lot(0))]
                if ghi is not None:
                    ro_hien += 1
                    vao_id = [n_id]
                    ghi.append(("mo", i, float(cho), float(_lot(0)), n_id, 0, ro_hien))
                    n_id += 1
                so_lenh += 1
                phi_sp += spread_gia[i] * _lot(0) * hop
                cho = 0.0
            else:
                lai_arr[i] = lai - phi_sp - phi_sw
                treo_arr[i] = 0.0
                continue
        # ---- 1. BAT LOI TRUOC: them tang ----
        if len(vao) < ts.tran_tang:
            moc = vao[-1][0] - chieu * _buoc(so_tang - 1) * pip
            while (lo[i] <= moc if chieu > 0 else hi[i] >= moc):
                phi_sp += spread_gia[i] * _lot(so_tang) * hop
                vao.append((moc, _lot(so_tang)))
                if ghi is not None:
                    vao_id.append(n_id)
                    ghi.append(("mo", i, float(moc), float(_lot(so_tang)), n_id, so_tang, ro_hien))
                    n_id += 1
                so_tang += 1
                so_lenh += 1
                if len(vao) >= ts.tran_tang:
                    break
                moc = moc - chieu * _buoc(so_tang - 1) * pip
        if not vao:
            lai_arr[i] = lai - phi_sp - phi_sw
            treo_arr[i] = 0.0
            continue
        if len(vao) > tang_max:
            tang_max = len(vao)
        # ---- 2. phi qua dem cho cac tang dang mo ----
        tong_lot = sum(l for _g, l in vao)
        if dem[i]:
            phi_sw += tong_lot * hop * ty_le * dem[i] / 365.0 * cl[i]
        # ---- 3. lo treo sau nhat trong bar ----
        xau = lo[i] if chieu > 0 else hi[i]
        treo = 0.0
        for g, l in vao:
            d = chieu * (g - xau)
            if d > 0:
                treo += d * l
        treo_arr[i] = treo * hop
        # ---- 4. TP tu gia trung binh ----
        # ---- 3b. TIA LENH: ghep tang SAU NHAT voi tang DAU TIEN ----
        if ts.tia_lenh and len(vao) >= 2:
            tot = hi[i] if chieu > 0 else lo[i]
            da = 0
            while len(vao) >= 2 and da < ts.cap_moi_bar:
                (g_dau, l_dau), (g_cuoi, l_cuoi) = vao[0], vao[-1]
                lai_cap = (chieu * (tot - g_cuoi) * l_cuoi
                           + chieu * (tot - g_dau) * l_dau) * hop
                if lai_cap < ts.bien_cap * pip * (l_dau + l_cuoi) * hop:
                    break
                lai += lai_cap
                phi_sp += spread_gia[i] * (l_dau + l_cuoi) * hop
                so_cap += 1
                da += 1
                if ghi is not None:
                    ghi.append(("dong", i, float(tot), vao_id[0], "tia"))
                    ghi.append(("dong", i, float(tot), vao_id[-1], "tia"))
                    vao_id = vao_id[1:-1]
                vao = vao[1:-1]
            if not vao:
                # tia het ca ro -> mo lai mot lenh moi, ladder ve 0
                so_tang = 1
                vao = [(cl[i], _lot(0))]
                if ghi is not None:
                    ro_hien += 1
                    vao_id = [n_id]
                    ghi.append(("mo", i, float(cl[i]), float(_lot(0)), n_id, 0, ro_hien))
                    n_id += 1
                so_lenh += 1
                phi_sp += spread_gia[i] * _lot(0) * hop
            tong_lot = sum(l for _g, l in vao)
        # gia trung binh CO TRONG SO LOT - do la ca co che cua DCA: tang sau
        # lot to hon keo gia trung binh ve gan gia hien tai nhanh hon.
        tb = sum(l * g for g, l in vao) / tong_lot
        if ts.chot_tien > 0:
            # chot khi LAI NOI cua ro >= nguong tien (quy ve 0,01 lot goc)
            tot = hi[i] if chieu > 0 else lo[i]
            lai_noi = sum(chieu * (tot - g) * l for g, l in vao) * hop
            nguong = ts.chot_tien * (ts.lot / 0.01)
            mtp = tot if lai_noi >= nguong else None
            cham = mtp is not None
            loi_chot = lai_noi
        else:
            mtp = tb + chieu * t
            cham = (hi[i] >= mtp) if chieu > 0 else (lo[i] <= mtp)
            loi_chot = tong_lot * hop * t
        if cham:
            lai += loi_chot
            so_ro += 1
            if ghi is not None:
                for k_id in vao_id:
                    ghi.append(("dong", i, float(mtp), k_id, "tp"))
            treo_arr[i] = 0.0
            so_tang = 1
            if ts.cho_lui > 0:
                # khong mo lai ngay: dat moc cho gia lui `cho_lui` pip
                cho = mtp - chieu * ts.cho_lui * pip
                vao = []
                if ghi is not None:
                    vao_id = []
            else:
                vao = [(mtp, _lot(0))]
                if ghi is not None:
                    ro_hien += 1
                    vao_id = [n_id]
                    ghi.append(("mo", i, float(mtp), float(_lot(0)), n_id, 0, ro_hien))
                    n_id += 1
                so_lenh += 1
                phi_sp += spread_gia[i] * _lot(0) * hop
        lai_arr[i] = lai - phi_sp - phi_sw
    # Bar 0 = lai chot 0 tru chi phi da tra DEN bar 0 (spread lenh dau), cung quy uoc `lai_arr[i]` o tren. Truoc 03/10/2026 day
    # la `-phi_sp` SAU vong lap = TONG spread ca chuoi: equity[0] = von - tong spread, mot diem dau gia o rat thap. No khong
    # doi lai rong, nhung khi nhan he so lot k (`nc_thi_nghiem._he_so_lot_tai_tran`) diem do bien thanh "tai khoan chet o
    # k = von / tong spread" -> chan k nhan tao, phat cac cau hinh giao dich nhieu khi xep theo loi_suat_o_tran_pct.
    lai_arr[0] = -phi_sp_bar0
    treo_arr[0] = 0.0
    return lai_arr, treo_arr, {
        "lai_gop": lai, "phi_spread": phi_sp, "phi_swap": phi_sw,
        "so_ro": so_ro, "so_lenh": so_lenh, "tang_max": tang_max,
        "so_cap": so_cap, "con_mo": len(vao), "so_cat": 0, "so_gio": 0}       # `cuc_tri` khong co cat lo / thoat gio: cung khoa voi `duong_di`


#: Dung sai so hoc cua phep "gia da CHAM moc" cua `duong_di`, tinh bang PIP. EA / tester khop lenh khi gia cham DUNG moc (`bid <= muc`),
#: nhung moc = gia khop -/+ buoc * pip la phep double nen sai ~1e-16 se quyet dinh "cham hay khong" (vd 0,900445 - 0,0016 ra
#: 0,8988449999999999 trong khi gia that 0,898845 nam tren luoi 1e-6): lenh khop lech mot tick o cac o cham dung moc - rat hay gap
#: o du lieu mau 1 phut (bien do nen ~10 diem). 1e-6 pip la nho hon mot buoc gia that (1 diem = 0,1 pip) 1e5 lan nhung lon hon sai so
#: double cua moi cap gia / pip thuc te (<= 1e-9 pip). GIU KHOP `EPS_CHAM_PIP` trong `luoi_nhan.c` (test_luoi_nhan::test_dung_sai_cham_moc_c_bang_python kiem bang nhau).
EPS_CHAM_PIP = 1e-6

#: Chan so vong chot / tia trong MOT doan don dieu. Voi tp > 0 va gia huu han so vong <= do dai doan / nguong chot, nen so nay chi
#: chan truong hop suy bien (nguong chot nho hon buoc nhay cua double) de khong treo may. Qua ngan sach -> RuntimeError.
TOI_DA_VONG_DOAN = 1_000_000


def mien_duong_di(ts: ThamSo, qc: QuyCach) -> str:
    """Ly do `duong_di` tu choi bo tham so / quy cach nay ("" = chap nhan). MOT nguon cho ban Python (nem ValueError) lan nhan C
    (`luoi_nhan.kha_dung` -> de Python lo): hai ben phai tu choi y het nhau, khong ben nao tu doan.

    `tp > 0` la dieu kien TIEN QUYET: ro chot xong mo lai ngay o gia chot, nen tp <= 0 se chot di chot lai mai tai cung mot gia
    (ban `cuc_tri` moi bar chi chot toi da mot lan nen khong vuong loi nay)."""
    try:
        so = {"lot": ts.lot, "buoc": ts.buoc, "tp": ts.tp, "tran_tang": ts.tran_tang, "he_so_lot": ts.he_so_lot,
              "he_so_buoc": ts.he_so_buoc, "buoc_tran": ts.buoc_tran, "cho_lui": ts.cho_lui, "bien_cap": ts.bien_cap,
              "cap_moi_bar": ts.cap_moi_bar, "chot_tien": ts.chot_tien, "hop_dong": qc.hop_dong, "pip": qc.pip,
              "phi_nam_mua": qc.phi_nam_mua, "phi_nam_ban": qc.phi_nam_ban,
              "cat_lo_pip": ts.cat_lo_pip, "cat_lo_tien": ts.cat_lo_tien, "thoat_gio": ts.thoat_gio, "nghi_gio": ts.nghi_gio,
              "gio_vao_tu": ts.gio_vao_tu, "gio_vao_den": ts.gio_vao_den}
        for k, v in so.items():
            if isinstance(v, bool) or not isinstance(v, (int, float, np.integer, np.floating)) or not math.isfinite(float(v)):
                return "%s phai la so huu han, nhan %r" % (k, v)
        if not (float(ts.lot) > 0 and float(ts.buoc) > 0 and float(ts.tp) > 0 and float(ts.tran_tang) >= 1
                and float(qc.pip) > 0 and float(qc.hop_dong) > 0 and float(ts.he_so_buoc) > 0):
            return "lot, buoc, tp, he_so_buoc, pip, hop_dong phai > 0 va tran_tang >= 1"
        if not (float(ts.cho_lui) >= 0 and float(ts.buoc_tran) >= 0 and float(ts.he_so_lot) >= 0 and float(ts.chot_tien) >= 0):
            return "cho_lui, buoc_tran, he_so_lot, chot_tien khong duoc am"
        if not (float(ts.cat_lo_pip) >= 0 and float(ts.cat_lo_tien) >= 0 and float(ts.thoat_gio) >= 0 and float(ts.nghi_gio) >= 0):
            return "cat_lo_pip, cat_lo_tien, thoat_gio, nghi_gio khong duoc am"
        if not (float(ts.thoat_gio) <= 1e6 and float(ts.nghi_gio) <= 1e6):
            return "thoat_gio, nghi_gio toi da 1.000.000 gio"
        if not (0 <= float(ts.gio_vao_tu) <= 24 and 0 <= float(ts.gio_vao_den) <= 24):
            return "gio_vao_tu, gio_vao_den phai nam trong [0, 24]"
    except Exception as e:                                       # noqa: BLE001 - thuoc tinh thieu / kieu la: de tu choi, khong nem loi la
        return "bo tham so khong doc duoc: %r" % (e,)
    return ""


def _mot_ro_duong(hi, lo, cl, spread_gia, dem, chieu: int, ts: ThamSo, qc: QuyCach | None = None,
                  ghi: list | None = None, tg=None):
    """Mo phong MOT ro theo mo hinh `duong_di` (`ThamSo.khop_bar == "duong_di"`). Cung chu ky va cung kieu tra ve voi `_mot_ro`:
    (lai_cong_don_theo_bar, lo_treo_theo_bar, thong ke), `ghi` ghi lenh cung dang tuple.

    Moi bar (i >= 1) di tren duong `o -> x -> y -> cl[i]` voi `o` = dong cua bar truoc kep vao [low, high] (du lieu chua co cot open):
    nen xanh (cl >= o) `x,y = low,high`; nen do `x,y = high,low`. Moi doan la mot nhat cat thang, nen moi su kien co GIA NGUONG ro:
      - doan NGUOC chieu ro (`lui`): ro CHO gia lui (`cho_lui`) mo L1 o muc cho; them tang o dung moc luoi. Nhay gia vuot moc ->
        khop o gia dau doan (gia dau tien co the khop), khong o moc.
      - doan THUAN chieu ro (`len_`): tia cap (tang dau + tang cuoi) chot khi gia TRUNG BINH CO TRONG SO cua cap dat `bien_cap` pip
        lai, ca ro chot khi gia dat TP (trung binh + tp pip, hoac lai noi >= `chot_tien`). Su kien nao cham truoc theo chieu di
        thi xu ly truoc (bang nhau: tia truoc TP). Ro chot xong mo lai L1 NGAY o gia chot (hoac cho lui) roi tiep tuc di cung
        doan, nen mot nen chay manh chot duoc nhieu ro. Moi tia tinh vao `cap_moi_bar` cua BAR (khong phai cua doan).
    Spread tru MOT lan khi mo moi lenh (khong tru them luc dong: giong EA va tester). Phi qua dem: tong lot con mo luc het bar.
    `lo_treo_theo_bar[i]` = lo noi LON NHAT tren ca duong cua bar (truoc khi chot), khac `_mot_ro` chi do o low.

    CO CHE THOAT + LOC GIO (08/10/2026; MAC DINH TAT - khi tat ket qua y het ban truoc khi co chung, test_luoi_quy_cach giu nguyen):
      - CAT LO CA RO (`cat_lo_pip` / `cat_lo_tien`): tren doan NGUOC chieu, moc cat nam canh moc them tang; moc nao nam TRUOC theo chieu di thi
        xu ly truoc (so gia khop that: bang nhau -> cat truoc; nhay gia vuot ca hai -> cat, khong them tang, giong EA kiem cat truoc them
        tang). Cat xong ro rong; ro moi mo o gia cat neu duoc phep (khong cho lui). `so_cat` dem cac ro nay, tien lo vao `lai_gop`.
        KHONG can kiem cat lai sau khi tia cap (khong bao gio cat ngay o gia tia): tang cuoi q_r chi mo duoc khi moc cat cua ro luc do
        (q_1..q_{r-1}) nam DUOI gia mo q_r, tuc K > A - q_r; bo hai lenh dau / cuoi thi gia trung binh con lai A' < A (q_1 cao nhat) va
        K' >= K (cat theo tien: it lot hon -> khoang cat rong hon) nen moc cat moi A' - K' < q_r < gia tia. `test_luoi_thoat_gio`
        giu dung tinh chat nay tren ca nghin kich ban ngau nhien.
      - THOAT GIO (`thoat_gio`): dau moi bar, ro song >= thoat_gio thi dong o GIA MO bar (`so_gio`).
      - NGHI (`nghi_gio`) + LOC GIO (`gio_vao_tu/den`) chi chan viec MO RO MOI (sau chot loi, sau cat / thoat gio, dau bar khi ro rong), khong
        chan them tang. Khong duoc mo thi ro rong cho den dau bar ke tiep duoc phep, mo o gia mo bar. Nghi dem tu gio MO CUA BAR co cat.
      Gio = `tg[i]` = giay epoch cua gio mo bar (mang cung do dai chuoi gia; bat buoc khi dung thoat_gio / nghi_gio / loc gio).
      `lo_treo_theo_bar[i]` cua bar co cat / thoat gio LO: lo noi truoc luc cat da nam trong lai da chot nen KHONG tinh hai lan - phan lo
      noi cua ro cu duoc doi sang goc lai-da-chot-sau-cat (xem `dong_het`).

    Du lieu / tham so ngoai mien (NaN, inf, tp <= 0, ...) -> ValueError (khong chay am tham). Moi phep cong la tuan tu tung phan tu
    (khong `sum()`), de nhan C khop TUNG BIT tren moi phien ban Python."""
    qc = qc or QC_AUDCAD
    if chieu not in (1, -1):
        raise ValueError("chieu phai la +1 hoac -1, nhan %r" % (chieu,))
    ly_do = mien_duong_di(ts, qc)
    if ly_do:
        raise ValueError("khop_bar='duong_di': " + ly_do)
    mang = [np.asarray(a, dtype=float) for a in (hi, lo, cl, spread_gia, dem)]
    n = len(mang[2])
    if n < 1 or any(a.ndim != 1 or len(a) != n for a in mang):
        raise ValueError("hi, lo, cl, spread, dem phai cung do dai >= 1 (1 chieu)")
    if not all(np.isfinite(a).all() for a in mang):
        raise ValueError("khop_bar='duong_di': hi/lo/cl/spread/dem co NaN hoac inf")
    hi, lo, cl, spread_gia, dem = (a.tolist() for a in mang)
    thoat_s, nghi_s, gio_tu_s, gio_den_s = cau_hinh_gio(ts)
    loc_gio = gio_tu_s != gio_den_s
    dung_tg = thoat_s > 0 or nghi_s > 0 or loc_gio
    if dung_tg:
        if tg is None:
            raise ValueError("khop_bar='duong_di': thoat_gio / nghi_gio / gio_vao_* can cot thoi gian cua bar (tham so `tg`)")
        tg_a = np.asarray(tg, dtype=float)
        if tg_a.ndim != 1 or len(tg_a) != n or not np.isfinite(tg_a).all():
            raise ValueError("khop_bar='duong_di': tg phai la mang 1 chieu huu han, cung do dai voi chuoi gia")
        tg = tg_a.tolist()
    pip, hop = float(qc.pip), float(qc.hop_dong)
    lot_ts, buoc_ts, he_lot, he_buoc = float(ts.lot), float(ts.buoc), float(ts.he_so_lot), float(ts.he_so_buoc)
    buoc_tran, cho_lui, bien_cap = float(ts.buoc_tran), float(ts.cho_lui), float(ts.bien_cap)
    cap_moi_bar, chot_tien, tran = float(ts.cap_moi_bar), float(ts.chot_tien), float(ts.tran_tang)
    kieu, tia = ts.kieu_lot, bool(ts.tia_lenh)
    s = chieu
    t = float(ts.tp) * pip
    eps = EPS_CHAM_PIP * pip                                     # dung sai "cham moc" (xem EPS_CHAM_PIP)
    ty_le = qc.phi_nam_mua if chieu > 0 else qc.phi_nam_ban
    nguong_tien = chot_tien * (lot_ts / 0.01)                    # chot theo tien: quy ve 0,01 lot goc (y het `_mot_ro`)
    cat_pip, cat_tien = float(ts.cat_lo_pip), float(ts.cat_lo_tien)
    cat_bat = cat_pip > 0 or cat_tien > 0
    nguong_cat = cat_tien * (lot_ts / 0.01)                      # cat lo theo tien: cung don vi voi chot_tien

    def _lot(k: int) -> float:
        if kieu == "nhan":
            return lot_ts * (he_lot ** k)
        if kieu == "cong":
            return lot_ts * (1.0 + he_lot * k)
        return lot_ts

    def _buoc(k: int) -> float:
        if he_buoc == 1.0:
            return buoc_ts
        v = buoc_ts * (he_buoc ** k)
        return buoc_tran if buoc_tran < v else v                  # min(v, buoc_tran)

    lai_arr = np.empty(n)
    treo_arr = np.empty(n)
    vao: list = []                                                # (gia, lot) - lot GAN vao lenh luc mo
    vid: list = []                                                # id lenh, song song voi `vao`
    n_id, ro_hien = 0, -1
    cho = 0.0                                                     # != 0: dang CHO gia lui toi muc nay moi mo L1
    lai = phi_sp = phi_sw = 0.0
    so_ro = so_cap = so_cat = so_gio = 0
    so_lenh = 0
    so_tang = 1                                                   # so tang DA MO cua ro hien tai (khong tut khi tia)
    tang_max = 0
    da_bar = 0                                                    # so tia da lam trong bar dang xu ly
    t_mo = 0.0                                                    # gio mo (bar) cua ro hien tai (chi dung khi dung_tg)
    nghi_den = -math.inf                                          # khong mo ro MOI truoc moc gio nay (sau cat lo / thoat gio)
    r_dau = 0.0                                                   # lai rong da chot luc DAU bar dang xu ly
    treo_bar = 0.0                                                # lo noi lon nhat da thay trong bar dang xu ly

    def cho_phep_mo(i: int) -> bool:
        """Duoc mo RO MOI o bar `i` khong: het thoi gian nghi VA gio mo bar nam trong cua so vao lenh. Tinh nang gio tat -> luon duoc."""
        if not dung_tg:
            return True
        t = tg[i]
        if t < nghi_den:
            return False
        if loc_gio:
            sec = math.fmod(t, 86400.0)                           # fmod (khong phai %): y het nhan C voi moi dau cua t
            if sec < 0.0:
                sec += 86400.0
            if gio_tu_s < gio_den_s:
                return gio_tu_s <= sec < gio_den_s
            return sec >= gio_tu_s or sec < gio_den_s             # cua so qua nua dem
        return True

    if cho_phep_mo(0):                                            # bar 0 = lenh dau o gia dong (neu cua so gio dang dong: ro rong, cho bar sau)
        vao = [(cl[0], _lot(0))]
        vid = [0]
        n_id, ro_hien = 1, 0
        if ghi is not None:
            ghi.append(("mo", 0, float(cl[0]), float(_lot(0)), 0, 0, 0))
        so_lenh = 1
        tang_max = 1
        phi_sp += spread_gia[0] * lot_ts * hop                    # NB: lot_ts (khong phai lot tang 0) - y het `_mot_ro`
        if dung_tg:
            t_mo = tg[0]
    phi_sp_bar0 = phi_sp

    def mo_lenh(i: int, gia: float, k: int, moi_ro: bool) -> None:
        nonlocal phi_sp, so_lenh, n_id, ro_hien, vao, vid, t_mo
        lk = _lot(k)
        phi_sp += spread_gia[i] * lk * hop
        so_lenh += 1
        if moi_ro:
            ro_hien += 1
            vao = [(gia, lk)]
            vid = [n_id]
            if dung_tg:
                t_mo = tg[i]
        else:
            vao.append((gia, lk))
            vid.append(n_id)
        if ghi is not None:
            ghi.append(("mo", i, float(gia), float(lk), n_id, k, ro_hien))
        n_id += 1

    def thu_mo_lai(i: int, e: float) -> None:
        """Mo L1 cua ro MOI o gia `e` neu duoc phep (het nghi + gio mo bar `i` trong cua so); khong thi ro rong, cho bar ke tiep duoc phep."""
        nonlocal so_tang, tang_max
        so_tang = 1
        if cho_phep_mo(i):
            mo_lenh(i, e, 0, True)
            if tang_max < 1:
                tang_max = 1

    def dong_het(i: int, e: float, ma: int) -> None:
        """Dong NGUYEN ro hien tai o gia `e`: ma 2 = CAT LO, ma 3 = THOAT GIO. Lai / lo vao `lai`; ro rong, het cho lui; bat dau nghi tu bar `i`.

        `treo_bar` (lo noi lon nhat da thay trong bar) duoc DOI GOC: phan lo noi do ro vua dong da la lo da chot, tinh them la hai lan.
        Lo noi cu thanh `max(0, lo_noi + (lai_da_chot_bay_gio - lai_da_chot_dau_bar))` - bang 0 voi mot cu cat don thuan, con lai phan hom
        truoc cua lo noi da duoc cac khoan lai chot trong bar bu vao. Chi ap dung khi cu thoat nay LO RONG trong bar (lai chot giam)."""
        nonlocal lai, vao, vid, so_tang, cho, so_cat, so_gio, nghi_den, treo_bar
        acc = 0.0
        for g, lt in vao:
            acc += s * (e - g) * lt
        lai += acc * hop
        if ma == 2:
            so_cat += 1
        else:
            so_gio += 1
        if ghi is not None:
            ly = "cat" if ma == 2 else "gio"
            for k_id in vid:
                ghi.append(("dong", i, float(e), k_id, ly))
        vao = []
        vid = []
        so_tang = 1
        cho = 0.0                                                 # cat / thoat gio: khong cho lui (ro moi vao lai o gia hien tai)
        if nghi_s > 0:
            nghi_den = tg[i] + nghi_s
        d_lai = (lai - phi_sp - phi_sw) - r_dau
        if d_lai < 0.0:
            treo_bar = treo_bar + d_lai
            if treo_bar < 0.0:
                treo_bar = 0.0

    def moc_cat() -> float:
        """Moc gia ma ro `vao` (khong rong) bi CAT LO: gia trung binh co trong so lui `khoang` ve phia nguoc chieu ro; `khoang` = muc gan
        gia trung binh hon trong (cat_lo_pip, cat_lo_tien / (hop * tong lot))."""
        tong = 0.0
        sw = 0.0
        for g, lt in vao:
            tong += lt
            sw += lt * g
        tb = sw / tong
        kc = math.inf
        if cat_pip > 0:
            kc = cat_pip * pip
        if cat_tien > 0:
            k2 = nguong_cat / (hop * tong)
            if k2 < kc:
                kc = k2
        return tb - s * kc

    def lui(i: int, a: float, b: float) -> None:
        """Doan NGUOC chieu ro tu `a` den `b` (a == b: nhay gia luc mo nen). Moi vong: tang ke tiep HOAC cat lo (neu bat), cai nao khop
        truoc theo chieu di (xem docstring chinh); het su kien trong doan thi dung."""
        nonlocal cho, so_tang, tang_max
        if cho != 0.0:
            if s * (cho - b) < -eps:
                return                                            # chua lui toi muc cho
            if not cho_phep_mo(i):
                return                                            # ngoai cua so gio / dang nghi: giu muc cho, chua vao
            g = cho if s * (cho - a) <= 0 else a
            mo_lenh(i, g, 0, True)
            so_tang = 1
            cho = 0.0
            a = g
        vong = 0
        while vao:
            co_them = len(vao) < tran
            if not co_them and not cat_bat:
                break
            moc = 0.0
            if co_them:
                moc = vao[-1][0] - s * _buoc(so_tang - 1) * pip     # moc ke tiep tinh tu GIA KHOP THAT (EA: tu BID mo cua tang sau cung)
            cat_truoc = False
            mcut = 0.0
            if cat_bat:
                mcut = moc_cat()
                if co_them:
                    e_cat = mcut if s * (mcut - a) <= 0 else a        # gia khop that cua tung su kien (nhay gia -> gia hien tai)
                    e_them = moc if s * (moc - a) <= 0 else a
                    cat_truoc = s * e_cat >= s * e_them               # bang nhau: cat truoc
                else:
                    cat_truoc = True
            if cat_truoc:
                if s * (mcut - b) < -eps:
                    break                                         # chua toi moc cat
            elif s * (moc - b) < -eps:
                break                                             # chua toi moc them tang
            vong += 1                                             # chi dem su kien THAT SU xay ra (y het nhan C)
            if vong > TOI_DA_VONG_DOAN:
                raise RuntimeError("khop_bar='duong_di': qua %d tang / lan cat trong mot doan (buoc luoi suy bien)" % TOI_DA_VONG_DOAN)
            if cat_truoc:
                e = mcut if s * (mcut - a) <= 0 else a
                dong_het(i, e, 2)
                thu_mo_lai(i, e)
                a = e
            else:
                g = moc if s * (moc - a) <= 0 else a
                mo_lenh(i, g, so_tang, False)
                so_tang += 1
                if len(vao) > tang_max:
                    tang_max = len(vao)
        if len(vao) > tang_max:
            tang_max = len(vao)

    def len_(i: int, a: float, b: float) -> None:
        """Doan THUAN chieu ro tu `a` den `b`: tia cap + chot ro, moi cai o gia nguong cua no."""
        nonlocal lai, phi_sp, so_ro, so_cap, so_tang, cho, vao, vid, da_bar
        p = a
        vong = 0
        while vao:
            vong += 1
            if vong > TOI_DA_VONG_DOAN:
                raise RuntimeError("khop_bar='duong_di': qua %d lan chot / tia trong mot doan (nguong chot suy bien)" % TOI_DA_VONG_DOAN)
            tong = 0.0
            sw = 0.0
            for g, lt in vao:
                tong += lt
                sw += lt * g
            tb = sw / tong
            if chot_tien > 0:
                mtp = tb + s * nguong_tien / (hop * tong)
            else:
                mtp = tb + s * t
            la_tia = False
            ps = 0.0
            if tia and len(vao) >= 2 and da_bar < cap_moi_bar:
                g_d, l_d = vao[0]
                g_c, l_c = vao[-1]
                ps = (g_c * l_c + g_d * l_d) / (l_c + l_d) + s * bien_cap * pip
                la_tia = s * ps <= s * mtp                        # bang nhau: tia truoc TP
            g_ev = ps if la_tia else mtp
            if s * (g_ev - b) > eps:
                break                                             # chua toi trong doan nay
            e = g_ev if s * (g_ev - p) >= 0 else p                # nguong da bi vuot luc dau doan (gia da doi) -> khop o gia hien tai
            p = e
            if la_tia:
                g_d, l_d = vao[0]
                g_c, l_c = vao[-1]
                lai += (s * (e - g_c) * l_c + s * (e - g_d) * l_d) * hop
                so_cap += 1
                da_bar += 1
                if ghi is not None:
                    ghi.append(("dong", i, float(e), vid[0], "tia"))
                    ghi.append(("dong", i, float(e), vid[-1], "tia"))
                vao = vao[1:-1]
                vid = vid[1:-1]
                if not vao:
                    thu_mo_lai(i, e)                              # tia het ca ro -> mo lai mot lenh moi, ladder ve 0 (neu duoc phep)
            else:
                acc = 0.0
                for g, lt in vao:
                    acc += s * (e - g) * lt
                lai += acc * hop
                so_ro += 1
                if ghi is not None:
                    for k_id in vid:
                        ghi.append(("dong", i, float(e), k_id, "tp"))
                so_tang = 1
                vao = []                                          # ro da chot: phai rong TRUOC khi thu mo lai (cua so gio dong -> khong mo, ro van rong)
                vid = []
                if cho_lui > 0:
                    cho = e - s * cho_lui * pip                   # khong mo lai ngay: cho gia lui
                else:
                    thu_mo_lai(i, e)

    def treo_tai(gia: float) -> float:
        """Lo noi (duong) cua cac tang dang mo neu gia hien tai la `gia`."""
        acc = 0.0
        for g, lt in vao:
            d = s * (g - gia)
            if d > 0:
                acc += d * lt
        return acc * hop

    for i in range(1, n):
        hi_i, lo_i, cl_i = hi[i], lo[i], cl[i]
        o = cl[i - 1]                                             # gia mo ~ dong bar truoc (chua co cot open), kep vao [low, high]
        if o < lo_i:
            o = lo_i
        if o > hi_i:
            o = hi_i
        x, y = (lo_i, hi_i) if cl_i >= o else (hi_i, lo_i)       # nen xanh: xuong low truoc; nen do: len high truoc
        da_bar = 0
        r_dau = lai - phi_sp - phi_sw
        treo_bar = 0.0
        if thoat_s > 0 and vao and tg[i] - t_mo >= thoat_s:
            dong_het(i, o, 3)                                     # thoat theo gio: dong het o GIA MO bar
        if not vao and cho == 0.0:
            thu_mo_lai(i, o)                                      # ro rong (cua so gio / dang nghi o bar truoc): vao lan dau o gia mo bar
        lui(i, o, o)                                              # nhay gia luc mo nen: tang / cho lui / moc cat da bi vuot ngay luc mo
        f = treo_tai(o)
        if f > treo_bar:
            treo_bar = f
        a = o
        for b in (x, y, cl_i):
            d = s * (b - a)
            if d < 0:
                lui(i, a, b)
            elif d > 0:
                len_(i, a, b)
            f = treo_tai(b)
            if f > treo_bar:
                treo_bar = f
            a = b
        if vao and dem[i] != 0.0:
            tl = 0.0
            for _g, lt in vao:
                tl += lt
            phi_sw += tl * hop * ty_le * dem[i] / 365.0 * cl_i
        lai_arr[i] = lai - phi_sp - phi_sw
        treo_arr[i] = treo_bar
    # Bar 0 = lai chot 0 tru spread lenh dau (cung quy uoc `_mot_ro`, sua 03/10/2026)
    lai_arr[0] = -phi_sp_bar0
    treo_arr[0] = 0.0
    return lai_arr, treo_arr, {
        "lai_gop": lai, "phi_spread": phi_sp, "phi_swap": phi_sw,
        "so_ro": so_ro, "so_lenh": so_lenh, "tang_max": tang_max,
        "so_cap": so_cap, "con_mo": len(vao), "so_cat": so_cat, "so_gio": so_gio}


def mot_ro_chuan(hi, lo, cl, spread_gia, dem, chieu: int, ts: ThamSo, qc: QuyCach | None = None,
                 ghi: list | None = None, tg=None):
    """Ban Python CHUAN cua mo hinh `ts.khop_bar` (khong qua nhan C). Dung cho du phong, test va doi chieu.
    `tg` = giay epoch cua gio mo tung bar (chi `duong_di`, bat buoc khi dung thoat_gio / nghi_gio / gio_vao_*)."""
    if kiem_khop_bar(ts) == "duong_di":
        return _mot_ro_duong(hi, lo, cl, spread_gia, dem, chieu, ts, qc, ghi, tg)
    return _mot_ro(hi, lo, cl, spread_gia, dem, chieu, ts, qc, ghi)


def _mot_ro_nhanh(hi, lo, cl, spread_gia, dem, chieu: int, ts: ThamSo, qc: QuyCach | None = None,
                  ghi: list | None = None, tg=None):
    """Mo hinh `ts.khop_bar` qua NHAN C (`nhan/luoi_nhan.py`, nhanh hon ~130 lan, nha GIL) khi dung duoc; khong thi ban Python chuan
    (`mot_ro_chuan`: `_mot_ro` hoac `_mot_ro_duong`).

    Ket qua KHONG doi so nao: nhan C duoc tu kiem voi ban Python truoc khi dung va khop tung bit tren 3.11/3.12/3.13
    (`test_luoi_nhan.py`). `LUOI_NHAN=py` ep chay Python. Ban Python van la CHUAN - muon doi hanh vi thi sua no truoc."""
    r = LN.mot_ro(hi, lo, cl, spread_gia, dem, chieu, ts, qc, ghi, tg)
    if r is not None:
        return r
    return mot_ro_chuan(hi, lo, cl, spread_gia, dem, chieu, ts, qc, ghi, tg)


def _bang_lenh(nhat_ky: dict, idx, qc: QuyCach):
    """Nhat ky `_mot_ro` (theo chieu) -> DataFrame lenh. `ro` la khoa DUY NHAT: chan 2*so_ro (+1 neu ban)."""
    import pandas as pd
    hang = []
    for chieu, ev in nhat_ky.items():
        mo = {}
        for e in ev:
            if e[0] == "mo":
                _t, bar, gia, lot, ma_id, tang, ro = e
                mo[ma_id] = dict(mo=idx[bar], dong=pd.NaT, chieu=chieu, lot=lot, gia_mo=gia, gia_dong=np.nan,
                                 tang=tang, ro=2 * ro + (0 if chieu > 0 else 1), ly_do="")
            else:
                _t, bar, gia, ma_id, ly_do = e
                mo[ma_id].update(dong=idx[bar], gia_dong=gia, ly_do=ly_do)
        hang.extend(mo.values())
    cot = ["mo", "dong", "chieu", "lot", "gia_mo", "gia_dong", "tang", "ro", "ly_do"]
    if not hang:
        return pd.DataFrame(columns=cot)
    d = pd.DataFrame(hang, columns=cot).sort_values(["mo", "ro", "tang"], kind="stable").reset_index(drop=True)
    d.attrs["pip"] = qc.pip
    return d


@dataclass(frozen=True)
class DuLieuChay:
    """Mang numpy cua MOT chuoi + MOT quy cach, dung chung cho nhieu lan `chay_mang` (quet tham so). Chi doc: `chay_mang` va
    nhan C khong ghi len no, nen nhieu luong dung chung duoc."""
    hi: np.ndarray
    lo: np.ndarray
    cl: np.ndarray
    sp: np.ndarray                  # spread theo GIA (cot POINT x point; bar bang 0 thay bang trung vi)
    dem: np.ndarray                 # so dem qua dem giua hai bar lien tiep (ngay)
    idx: object                     # chi so thoi gian cua khung (pandas DatetimeIndex)
    qc: QuyCach
    #: Giay epoch cua gio mo tung bar (float64, cung do dai) - cho thoat_gio / nghi_gio / gio_vao_*. Gio trong ngay = gio cua cot thoi gian
    #: du lieu (lab: gio may chu). Dat SAU `qc` va co mac dinh de cho dung `DuLieuChay(hi, lo, cl, sp, dem, idx, qc)` cu van chay.
    tg: object = None


def chuan_bi(df, qc: QuyCach | None = None) -> DuLieuChay:
    """Doi khung du lieu thanh mang numpy mot lan (spread, qua dem). `chay` = `chuan_bi` + `chay_mang`: cung mot duong tinh,
    nen quet N cau hinh chi tra chi phi nay mot lan thay vi N lan (~9 ms / 190.000 bar moi lan)."""
    qc = qc or QC_AUDCAD
    hi = df["high"].to_numpy(float)
    lo = df["low"].to_numpy(float)
    cl = df["close"].to_numpy(float)
    if "spread" in df.columns:
        # cot spread la POINT (AUDCAD / FX 5 chu so: 1e-5; cap JPY: 1e-3)
        sp = df["spread"].to_numpy(float) * qc.point
        sp = np.where(sp > 0, sp, np.nanmedian(sp[sp > 0]) if (sp > 0).any() else qc.spread_du_phong)
    else:
        sp = np.full(len(df), qc.spread_du_phong)
    idx = df.index
    dem = np.zeros(len(df))
    dem[1:] = np.diff(idx.values).astype("timedelta64[s]").astype(float) / 86400.0
    return DuLieuChay(hi, lo, cl, sp, dem, idx, qc, thoi_gian_giay(idx))


def thoi_gian_giay(idx) -> np.ndarray:
    """Chi so thoi gian pandas -> giay epoch (float64) cua tung bar. Chi so co mui gio thi lay gio UTC cua `.values` (lab dung chi so
    khong mui gio = gio may chu)."""
    return np.asarray(idx.values).astype("datetime64[s]").astype(np.int64).astype(float)


def chay(df, ts: ThamSo, von: float, qc: QuyCach | None = None, ghi_lenh: bool = False) -> KetQuaLuoi:
    """Mo phong day du tren mot khung du lieu. `von` bang dong BAO GIA. `qc` None = AUDCAD cu.

    `ghi_lenh=True`: them `KetQuaLuoi.lenh` (danh sach lenh mo phong). Khong doi bat ky con so nao khac."""
    chua = tham_so_chua_cai_dat(ts)
    if chua:
        raise ValueError("tham so %s da khai bao nhung luoi.py CHUA cai dat: dat != 0 se bi bo qua am tham" % chua)
    return chay_mang(chuan_bi(df, qc), ts, von, ghi_lenh)


def chay_mang(dl: DuLieuChay, ts: ThamSo, von: float, ghi_lenh: bool = False) -> KetQuaLuoi:
    """Phan con lai cua `chay` tren mang da chuan bi - tung bit nhu `chay(df, ts, von, qc)`."""
    chua = tham_so_chua_cai_dat(ts)
    if chua:
        raise ValueError("tham so %s da khai bao nhung luoi.py CHUA cai dat: dat != 0 se bi bo qua am tham" % chua)
    qc, hi, lo, cl, sp, dem, idx = dl.qc, dl.hi, dl.lo, dl.cl, dl.sp, dl.dem, dl.idx
    kiem_khop_bar(ts)                                   # ten mo hinh bar sai -> ValueError ngay, khong am tham chay mo hinh khac
    tg = getattr(dl, "tg", None)
    if can_cot_thoi_gian(ts):
        if tg is None:
            raise ValueError("thoat_gio / nghi_gio / gio_vao_* can cot thoi gian cua bar (DuLieuChay.tg) - dung `chuan_bi`")
        thoat_s, nghi_s, gio_tu_s, gio_den_s = cau_hinh_gio(ts)
        if gio_tu_s != gio_den_s and len(tg) > 1:
            khoang = np.diff(np.asarray(tg, float))
            khoang = khoang[khoang > 0]
            if khoang.size and float(np.median(khoang)) > KHUNG_TOI_DA_LOC_GIO_GIAY:
                raise ValueError("loc gio vao lenh (gio_vao_tu/den) can khung <= H1: bar cach nhau trung vi %.0f giay" % float(np.median(khoang)))

    chieus = {"mua": (1,), "ban": (-1,), "hai_chieu": (1, -1)}[ts.che_do]
    lais, treos, tks, nhat_ky = [], [], [], {}
    for c in chieus:
        ghi = nhat_ky.setdefault(c, []) if ghi_lenh else None
        a, b, k = _mot_ro_nhanh(hi, lo, cl, sp, dem, c, ts, qc, ghi, tg)
        lais.append(a)
        treos.append(b)
        tks.append(k)
    lai = np.sum(lais, axis=0)
    treo = np.sum(treos, axis=0)

    equity = von + lai - treo
    # margin: so tang dang mo x notional / don bay. Xap xi bang tang_max de
    # khong phai luu so tang tung bar - THAN TRONG vi margin bi uoc CAO.
    def _lot_k(k):
        if ts.kieu_lot == "nhan":
            return ts.lot * (ts.he_so_lot ** k)
        if ts.kieu_lot == "cong":
            return ts.lot * (1.0 + ts.he_so_lot * k)
        return ts.lot
    lot_tong = sum(sum(_lot_k(j) for j in range(k["tang_max"])) for k in tks)
    margin = lot_tong * qc.hop_dong * float(np.mean(cl)) / ts.don_bay
    chay_o = np.flatnonzero(equity <= ts.muc_stopout * margin)
    bar_chay = int(chay_o[0]) if len(chay_o) else None
    if bar_chay is not None:
        equity = equity.copy()
        equity[bar_chay:] = 0.0

    so_nam = max((idx[-1] - idx[0]).days / 365.25, 1e-9)
    return KetQuaLuoi(
        lai_rong=float(lai[-1]),
        lai_gop=sum(k["lai_gop"] for k in tks),
        phi_spread=sum(k["phi_spread"] for k in tks),
        phi_swap=sum(k["phi_swap"] for k in tks),
        so_ro=sum(k["so_ro"] for k in tks),
        so_lenh=sum(k["so_lenh"] for k in tks),
        tang_max=max(k["tang_max"] for k in tks),
        so_cat=sum(k.get("so_cat", 0) for k in tks),
        so_gio=sum(k.get("so_gio", 0) for k in tks),
        lo_treo_dinh=float(np.max(treo)),
        chay=bar_chay is not None, bar_chay=bar_chay,
        so_nam=so_nam, duong_equity=equity, margin=float(margin),
        lenh=_bang_lenh(nhat_ky, idx, qc) if ghi_lenh else None)


def chi_so(kq: KetQuaLuoi, von: float) -> dict:
    """Chi so doc duoc tu duong von. CAGR tren VON, khong tai dau tu."""
    e = kq.duong_equity
    dinh = np.maximum.accumulate(e)
    dd = float(np.min(np.where(dinh > 0, e / np.maximum(dinh, 1e-9) - 1.0, -1.0)))
    lai_nam = kq.lai_rong / kq.so_nam
    return {
        "loi_suat_nam_pct": lai_nam / von * 100.0,
        "maxdd_pct": dd * 100.0,
        "lo_treo_dinh_pct_von": kq.lo_treo_dinh / von * 100.0,
        "ro_nam": kq.so_ro / kq.so_nam,
        "lenh_nam": kq.so_lenh / kq.so_nam,
        "tang_max": kq.tang_max,
        "chay": kq.chay,
        "phi_tren_lai_gop_pct": (
            (kq.phi_spread + kq.phi_swap) / kq.lai_gop * 100.0
            if kq.lai_gop > 0 else float("nan")),
        "calmar": (lai_nam / von) / abs(dd) if dd < 0 else float("inf"),
    }
