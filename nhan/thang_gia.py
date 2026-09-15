# -*- coding: utf-8 -*-
"""thang_gia.py - NGUONG TINH BANG DON VI GIA la mot loi CAM LANG.

## Chuyen bat duoc 15/09/2026

Chay 61 co che dung `than_nen` qua MT5 tester tren AUDCADmicro H4: **13 co che
ra dung 0 lenh**. Bai hoc hom truoc noi "mot dong 0 lenh thi di doc ma MQL5",
nen toi doc - va ban Python cung ban **0 tin hieu**. Khong phai loi dich.

Cai hong nam trong chinh LOI KHAI:

    ty_le_than_nen:  than_nen > 0.5

`than_nen` la `close - open`, **don vi GIA**. Con `0.5` la mot so tran. Do tren
nam chuoi:

    EURUSD.H1      gia TB      1,17   ty le kich hoat 0,000
    AUDCAD.H4      gia TB      0,95   ty le kich hoat 0,000
    USDJPY.H1      gia TB    110,88   ty le kich hoat 0,005
    XAUUSD.H1      gia TB  1.313,92   ty le kich hoat 0,364
    US500Cash.D1   gia TB  2.753,05   ty le kich hoat 0,532

Ty le kich hoat di tu 0,000 den 0,532 **chi theo muc gia cua tai san**, khong
theo hanh vi gia. Cai ten (`ty_le_than_nen` - TY LE) noi tac gia dinh viet
`than_nen / bien_do`, mot so 0..1; con loi khai lai so THAN NEN TRAN voi 0,5.

## Vi sao no song sot duoc lau nhu vay

`ngu_phap.MA_DO_THEM = (("XAUUSD","H1"), ("EURUSD","H1"))` - cua vao kho do ty
le kich hoat tren hai chuoi roi **lay cai do duoc**. Tren XAUUSD no ra 0,364,
mot con so hoan toan khoe manh. Co che vao kho, mang theo mot con so
`_ty_le_kich_hoat` dep, roi ra **0 lenh tren moi cap FX** mai mai - va moi lan
nhu vay chi hien ra la mot dong 0 trong bang tester, lan giua nhung dong that.

Cung ho loi voi moi thu khac: **he im lang khi sai**, va con so no in ra binh
thuong. [[luat-khong-nam-tren-duong-chay]]

## Bo do o day lam gi

`do_theo_thang(spec)` chay chinh co che do tren NAM chuoi trai dai bon bac gia
(1 -> 100 -> 1.000 -> 3.000) va tra ve ty le kich hoat tung chuoi. Tu do:

  PHU_THUOC_THANG_GIA  chet o chuoi gia thap, song o chuoi gia cao (hoac nguoc
                       lai) - loi khai co hang so don vi gia. KHONG dung duoc
                       da tai san; phai chuan hoa truoc khi noi bat cu dieu gi.
  CHET_MOI_NOI         khong kich hoat o dau ca - loi khai vo nghia.
  ON_DINH              ty le tuong duong nhau qua cac bac gia: loi khai khong
                       dinh don vi.

Dung o hai cho:
  - `chay_tester_kho`: truoc khi dot mot luot boot terminal, noi ro co che nao
    se ra 0 lenh VI LOI KHAI chu khong phai vi thi truong.
  - cua vao kho (`ngu_phap.them_co_che`): mot con so do tren MOT chuoi khong
    du de ket luan co che song.
"""
from __future__ import annotations

import json
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
KHO = LAB / "config" / "thang_gia.json"

#: Sau chuoi trai dai BON BAC GIA - **CUNG MOT KHUNG H1**.
#:
#: Ban do dau tien tron khung (AUDCAD H4, US500Cash D1) va no lam hong chinh
#: phep thu: `buy_liquidity_sweep_ob_reversal` kich hoat 0,16-0,23 tren bon
#: chuoi H1/H4 va 0,000 tren US500Cash **D1** - bi xep la "chet o gia cao",
#: trong khi cai khac nhau that su la KHUNG. Mot bo do muon quy ket cho THANG
#: GIA thi moi thu khac phai giu nguyen. Nay ca sau deu H1, va co ba cap cung
#: bac gia (EURUSD/AUDCAD/GBPUSD ~1) de tach "chet vi thang gia" khoi "chet vi
#: cap nay".
CHUOI_DO = (("EURUSD", "H1"), ("AUDCAD", "H1"), ("GBPUSD", "H1"),
            ("USDJPY", "H1"), ("XAUUSD", "H1"), ("US500Cash", "H1"))

#: Duoi nguong nay coi nhu KHONG kich hoat. Giong `ngu_phap.TY_LE_IT_KHO`.
SAN = 0.002

#: Ben kia phai SONG RO thi chenh lech moi la mot ket luan.
#:
#: Thu nghiem dau tien bo qua nguong nay va bat oan ngay
#: `pine_golden_cross_mua_sma50...`: no kich hoat 0,003 · 0,003 · 0,003 · 0,003
#: · 0,0019 - mot co che THUA THOT dao qua dao lai quanh `SAN`, khong phai mot
#: co che dinh don vi gia. Chenh lech chi doc duoc khi mot ben that su song.
TRAN_SONG = 0.02

_CACHE: dict = {}


def chuoi(lam_moi: bool = False) -> list:
    """Nap (mot lan) nam chuoi do, kem muc gia trung vi cua tung chuoi."""
    if lam_moi:
        _CACHE.clear()
    if not _CACHE:
        from nhan import du_lieu as DL
        ds = []
        for ma, khung in CHUOI_DO:
            try:
                df = DL.nap(ma, khung)
            except Exception:
                continue
            if df is None or len(df) < 500:
                continue
            ds.append((f"{ma}.{khung}", df, float(df["close"].median())))
        ds.sort(key=lambda x: x[2])
        _CACHE["ds"] = ds
    return _CACHE.get("ds") or []


def do_theo_thang(spec: dict, ds: list | None = None) -> dict:
    """Ty le kich hoat cua mot co che tren tung bac gia."""
    import numpy as np
    from nhan import ngu_phap as NP
    ds = ds if ds is not None else chuoi()
    ra = {}
    for ten, df, gia in ds:
        try:
            th = np.asarray(NP.sinh_tu_spec(spec, df))
            ra[ten] = float(np.mean(np.abs(th) > 1e-12))
        except Exception:
            ra[ten] = None          # KHONG DO DUOC, khac voi 0
    return ra


def xep_loai(ty_le: dict) -> str:
    """ON_DINH · PHU_THUOC_THANG_GIA · CHET_MOI_NOI · CHUA_DO_DUOC.

    Phep thu la: sap cac chuoi theo MUC GIA, roi hoi "cac chuoi gia thap co
    chet trong khi chuoi gia cao thi song khong" (hoac nguoc lai). Do la dau
    van tay cua mot hang so don vi gia trong loi khai - khong the giai thich
    bang hanh vi thi truong, vi EURUSD va US500 khong he giong nhau ve hanh vi
    theo cach don dieu nhu vay.
    """
    v = [ty_le.get(t) for t, _, _ in chuoi()]
    co = [x for x in v if x is not None]
    if len(co) < 3:
        return "CHUA_DO_DUOC"
    if max(co) < SAN:
        return "CHET_MOI_NOI"
    if max(co) < TRAN_SONG:
        return "THUA_THOT"          # chua ben nao song ro - chua ket luan duoc
    # `v` da theo thu tu gia tang dan (`chuoi()` sap theo gia).
    song = [x is not None and x >= SAN for x in v]
    chet = [x is not None and x < SAN for x in v]
    # BA chuoi dau cung mot bac gia (~1). Doi CA BA cung chet moi ket luan la
    # thang gia: mot cap don le chet la chuyen cua cap do, khong phai cua thang.
    if all(chet[:3]) and all(song[-2:]):
        return "PHU_THUOC_THANG_GIA"     # chet o gia THAP, song o gia CAO
    if all(chet[-2:]) and all(song[:3]):
        return "PHU_THUOC_THANG_GIA"     # chet o gia CAO, song o gia THAP
    return "ON_DINH"


def mot_co_che(spec: dict, ds: list | None = None) -> dict:
    t = do_theo_thang(spec, ds)
    return {"ten": spec.get("ten"), "ho": spec.get("ho"),
            "ty_le": t, "xep_loai": xep_loai(t)}


def kho_xep_loai() -> dict:
    """Ket qua da quet (neu co). `{ten_co_che: {...}}`."""
    if not KHO.exists():
        return {}
    try:
        return json.loads(KHO.read_text(encoding="utf-8")).get("co_che") or {}
    except (OSError, ValueError):
        return {}


def chuoi_gan(ma: str) -> list:
    """Chuoi do nao NOI DUOC ve `ma` nay - chon theo BAC GIA, khong theo ten.

    Ten khong phai la cau tra loi: `EURGBP` khop tien to voi `EURUSD` nhung dieu
    lam co che song hay chet la MUC GIA, va `GBPUSD` (1,51) gan `EURGBP` (0,85)
    hon la `XAUUSD` (1.314) du khong chung ky tu nao. Nen: lay muc gia that cua
    `ma` roi giu cac chuoi trong vong MOT BAC (x10). Khong nap duoc gia thi lui
    ve so khop tien to - van hon la khong noi gi.
    """
    try:
        from nhan import du_lieu as DL
        goc = ma.replace("micro", "").replace("Cash", "")
        gia = float(DL.nap(goc, "H1")["close"].median())
    except Exception:
        t3 = ma[:3].upper()
        return [t for t, _, _ in chuoi() if t.split(".")[0].upper().startswith(t3)]
    return [t for t, _, g in chuoi() if g > 0 and 0.1 <= gia / g <= 10.0]


def canh_bao_cho_ma(ten_co_che: list, ma: str) -> list:
    """Cac dong phai in TRUOC mot luot tester: cai nao se ra 0 lenh VI LOI KHAI.

    Khong chan. Mot co che `PHU_THUOC_THANG_GIA` van co the dang muon chay
    tren dung bac gia cua no; cai phai chan la doc mot dong 0 nhu mot ket qua.
    """
    d = kho_xep_loai()
    if not d:
        return []
    gan_ma = chuoi_gan(ma)
    xau = []
    for t in ten_co_che:
        h = d.get(t)
        if not h:
            continue
        if h["xep_loai"] == "CHET_MOI_NOI":
            xau.append((t, "CHET_MOI_NOI", None))
            continue
        if h["xep_loai"] != "PHU_THUOC_THANG_GIA":
            continue
        gan = [(k, v) for k, v in (h["ty_le"] or {}).items()
               if v is not None and k in gan_ma]
        if gan and max(v for _, v in gan) < SAN:
            xau.append((t, "PHU_THUOC_THANG_GIA", gan[0][0]))
    if not xau:
        return []
    ra = ["%d co che se ra 0 lenh VI LOI KHAI (nguong tinh bang DON VI GIA), "
          "khong phai vi thi truong:" % len(xau)]
    for t, loai, _ in xau[:10]:
        ra.append("     %-46s %s" % (t[:46], loai))
    ra.append("   doc `nhan/thang_gia.py`. Mot dong 0 o day KHONG phai ket qua.")
    return ra


# ============================================================ CHUAN HOA
#
# Cong o tren moi chi BAO. Bao xong thi 75 co che van nam do, chet tren moi cap
# FX - ma FX lai dung la cho ca hai he dang song (AUDCAD.H4, EURGBP.H4) lam
# viec. Vut di thi mat; giu nguyen thi vo dung.
#
# Cach chua khong can them cu phap moi: ngu phap DA CO `tuyen_tinh`, nen mot
# hang so don vi gia viet lai duoc thanh **k lan ATR**:
#
#     than_nen > 0.5            ->   than_nen > k * ATR(14)
#
# `k` chon sao cho giu nguyen **DO HIEM CUA SU KIEN** tren chuoi ma co che von
# da song - dung nguyen tac cua `ngoai_sinh.chuyen` ("giu TY LE KICH HOAT,
# khong giu con so"), chi khac la o day no ap cho mot hang so trong loi khai
# chu khong cho tham so cua mot template.
#
# `ngoai_sinh` KHONG lam thay duoc viec nay: `_lan_can` do lan can theo ti le
# +-60% quanh con so cu, ma tu 0,5 (vang) xuong 0,0009 (AUDCAD) la ba bac do
# lon - khong lan can nao voi toi.

#: Toan hang mang THU NGUYEN GIA thi do lon cua no ti le voi muc gia. Do,
#: khong doan: mot danh sach ten viet tay se lac hau ngay lan them chi bao sau.
NGUONG_DON_VI_GIA = 0.25     # he so bien thien cua (do lon / muc gia)


def don_vi_gia(t: dict, ds: list | None = None) -> bool:
    """Toan hang nay co THU NGUYEN GIA khong - DO tren cac bac gia."""
    import numpy as np
    from nhan import ngu_phap as NP
    ds = ds if ds is not None else chuoi()
    ty = []
    for _, df, gia in ds:
        try:
            v = np.asarray(NP.toan_hang(df, t), float)
        except Exception:
            continue
        m = float(np.nanmedian(np.abs(v)))
        if not np.isfinite(m) or m <= 0 or gia <= 0:
            continue
        ty.append(m / gia)
    if len(ty) < 3:
        return False
    tb = float(np.mean(ty))
    return tb > 0 and float(np.std(ty)) / tb < NGUONG_DON_VI_GIA


def _atr_trung_vi(df, n: int = 14) -> float:
    import numpy as np
    from nhan import ngu_phap as NP
    v = np.asarray(NP.toan_hang(df, {"chi_bao": "atr", "n": n}), float)
    return float(np.nanmedian(v))


def chuan_hoa(spec: dict, ds: list | None = None, n_atr: int = 14) -> dict | None:
    """Viet lai hang so DON VI GIA thanh `k * ATR(n)`. `None` = khong co gi de sua.

    `k` lay tu chuoi co ty le kich hoat CAO NHAT - chuoi ma co che von da song.
    """
    import copy
    ds = ds if ds is not None else chuoi()
    ty_le = do_theo_thang(spec, ds)
    song = [(v, t) for t, v in ty_le.items() if v is not None]
    if not song:
        return None
    _, ten_song = max(song)
    df_song = next((df for t, df, _ in ds if t == ten_song), None)
    if df_song is None:
        return None
    atr = _atr_trung_vi(df_song, n_atr)
    if not (atr > 0):
        return None

    moi = copy.deepcopy(spec)
    doi = 0
    for khoa in ("vao", "ra"):
        for dk in moi.get(khoa) or []:
            if not isinstance(dk, dict):
                continue
            for ben, kia in (("trai", "phai"), ("phai", "trai")):
                a, b = dk.get(ben), dk.get(kia)
                if not (isinstance(a, dict) and isinstance(b, dict)):
                    continue
                if set(b) != {"hang"}:
                    continue
                c = b.get("hang")
                if not isinstance(c, (int, float)) or c == 0:
                    continue          # `than_nen > 0` khong dinh don vi gia
                if not don_vi_gia(a, ds):
                    continue
                dk[kia] = {"chi_bao": "tuyen_tinh",
                           "toan_hang": [{"chi_bao": "atr", "n": n_atr}],
                           "he_so": [round(float(c) / atr, 6)]}
                doi += 1
    if not doi:
        return None
    moi["ten"] = "%s_atr" % spec.get("ten", "co_che")
    moi["co_che"] = ("%s [CHUAN HOA 15/09/2026: hang so don vi gia doi thanh "
                     "%s x ATR(%d), giu do hiem do tren %s]"
                     % (str(spec.get("co_che", ""))[:400], "k", n_atr, ten_song))
    moi.pop("_ty_le_kich_hoat", None)
    moi.pop("_do_tren", None)
    moi.pop("_ty_le_theo_chuoi", None)
    moi["_chuan_hoa_tu"] = spec.get("ten")
    moi["_so_hang_doi"] = doi
    return moi
