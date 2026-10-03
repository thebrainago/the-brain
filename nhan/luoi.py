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

  1. Khung M15/M5/M1, gia OHLC. Trong MOT bar xu ly **BAT LOI TRUOC**: them
     tang truoc, xet TP sau. Neu mot bar cham ca hai thi coi nhu bi them tang
     truoc roi moi chot - gia dinh THAN TRONG.
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
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from nhan import chi_phi as CP

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


@dataclass
class KetQuaLuoi:
    lai_rong: float = 0.0
    lai_gop: float = 0.0
    phi_spread: float = 0.0
    phi_swap: float = 0.0
    so_ro: int = 0
    so_lenh: int = 0
    tang_max: int = 0
    lo_treo_dinh: float = 0.0        # don vi bao gia
    chay: bool = False
    bar_chay: int | None = None
    so_nam: float = 0.0
    duong_equity: np.ndarray | None = field(default=None, repr=False)
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
    lai_arr[0] = -phi_sp
    treo_arr[0] = 0.0
    return lai_arr, treo_arr, {
        "lai_gop": lai, "phi_spread": phi_sp, "phi_swap": phi_sw,
        "so_ro": so_ro, "so_lenh": so_lenh, "tang_max": tang_max,
        "so_cap": so_cap, "con_mo": len(vao)}


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


def chay(df, ts: ThamSo, von: float, qc: QuyCach | None = None, ghi_lenh: bool = False) -> KetQuaLuoi:
    """Mo phong day du tren mot khung du lieu. `von` bang dong BAO GIA. `qc` None = AUDCAD cu.

    `ghi_lenh=True`: them `KetQuaLuoi.lenh` (danh sach lenh mo phong). Khong doi bat ky con so nao khac."""
    chua = tham_so_chua_cai_dat(ts)
    if chua:
        raise ValueError("tham so %s da khai bao nhung luoi.py CHUA cai dat: dat != 0 se bi bo qua am tham" % chua)
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

    chieus = {"mua": (1,), "ban": (-1,), "hai_chieu": (1, -1)}[ts.che_do]
    lais, treos, tks, nhat_ky = [], [], [], {}
    for c in chieus:
        ghi = nhat_ky.setdefault(c, []) if ghi_lenh else None
        a, b, k = _mot_ro(hi, lo, cl, sp, dem, c, ts, qc, ghi)
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
        lo_treo_dinh=float(np.max(treo)),
        chay=bar_chay is not None, bar_chay=bar_chay,
        so_nam=so_nam, duong_equity=equity,
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
