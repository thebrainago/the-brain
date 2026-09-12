# -*- coding: utf-8 -*-
"""ho_so_tuong_quan.py - TUONG QUAN LIEN MA va DO ON DINH cua no.

Muc Q3 cua `KE_HOACH_HOAN_THIEN.md`. Chu du an yeu cau trong `SO_DO_HE_THONG.txt`:

    "tinh tuong quan ( tuong quan am. tuong quan duong)"

## MOT CON SO TUONG QUAN KHONG DU - PHAI CO DO ON DINH

Tuong quan toan mau la mot TRUNG BINH. Hai cap co cung he so 0,6 nhung mot cap
giu 0,6 suot 20 nam con cap kia dao tu -0,3 len 0,9 la hai thu khac han nhau, va
chi cap thu nhat dung duoc de ghep danh muc.

Nen moi cap o day co BA con so:
    r_toan_mau   he so tren toan giai doan chung
    r_on_dinh    ty le cua so 1 nam GIU NGUYEN DAU voi r_toan_mau
    r_bien_do    do lech chuan cua tuong quan truot 1 nam

Mot cap `r = 0,7` nhung `on_dinh = 0,55` thi thuc te la mot dong xu.

## CAI BAY DA SAP TRONG CHINH DU AN (AGENTS.md muc 51)

    "Giong khung THOI GIAN truoc khi lay chi so theo vi tri. BTC bat dau 2014,
     ETH 2017, VNM 2009 - dung chi so cua chuoi nay cat chuoi kia la lech hang
     gia, khong bao loi."

Nen o day moi cap deu `concat(axis=1).dropna()` TRUOC khi tinh, va so bar chung
duoc bao ra. Cap nao chong lan duoi `BAR_CHUNG_TOI_THIEU` thi khong tinh.

## DUNG DE LAM GI

Hai viec, va chung nguoc nhau:
  GHEP     tim cap tuong quan THAP/AM va ON DINH -> hai chan bu nhau
  TRANH    tim cap tuong quan CAO -> dung chay hai he tren ca hai, do la mot he
           voi don bay gap doi ma tuong nhu hai

Chay:  python -m nhan.ho_so_tuong_quan [KHUNG] [so_ma]
Ra:    reports/HO_SO_TUONG_QUAN.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

def kho_cua(khung: str) -> Path:
    """Moi KHUNG mot file. Dung chung mot file thi lan chay sau xoa lan truoc."""
    return LAB / "reports" / ("HO_SO_TUONG_QUAN_%s.json" % khung.upper())


KHO = kho_cua("D1")   # giu ten cu cho ma da tro toi

#: Duoi so bar CHUNG nay thi khong tinh cho cap do.
BAR_CHUNG_TOI_THIEU = 500
#: Cua so do on dinh, tinh bang bar (D1: 252 ~ mot nam).
CUA_SO = 252
#: Nguong goi la "cao" / "am" khi xep loai.
CAO, AM = 0.7, -0.3
#: Mot cua so goi la "giu nguyen" neu tuong quan truot cach r toan mau duoi nguong nay.
LECH_CHO_PHEP = 0.2

#: Ma tien te ba chu de tach cap FX. Chi can du de bat CHUNG CHAN - khong can
#: day du the gioi.
TIEN_TE = {"EUR", "USD", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD", "SEK", "NOK",
           "DKK", "PLN", "CZK", "HUF", "TRY", "ZAR", "MXN", "SGD", "HKD", "CNH",
           "ILS", "RUB", "BRL", "CLP", "COP", "ARS", "GEL", "XAU", "XAG"}


#: Dong tien NEO CUNG vao dong tien khac -> ve mat rui ro chung LA dong tien do.
#: Bang chung do duoc 12/09 tren chinh bang nay: AUDHKD|AUDUSD = +0,969 va
#: DKKSEK|EURSEK = +0,963. Neu khong quy ve, "cap am nhat" se toan la
#: X/HKD so voi USD/Y - tuc van la mot cuoc danh cuoc vao USD, lat nguoc ve.
#: SGD/CNH la tha noi CO QUAN LY, khong neo cung -> KHONG cho vao day.
NEO = {"HKD": "USD", "DKK": "EUR"}


def _chan_tien(ma: str) -> tuple[str, str] | None:
    """'EURGBP' -> ('EUR','GBP'). None neu khong phai cap FX 6 chu."""
    t = ma.upper()
    for tien_to in ("XM_", "YH_", "TS_"):
        if t.startswith(tien_to):
            t = t[len(tien_to):]
    if len(t) != 6:
        return None
    a, b = t[:3], t[3:]
    if a not in TIEN_TE or b not in TIEN_TE:
        return None
    return (NEO.get(a, a), NEO.get(b, b))


def quan_he_co_hoc(ma_a: str, ma_b: str) -> str:
    """Hai ma co lien he SO HOC khong? -> "" neu khong.

    VI SAO CAN (do 12/09): mười cap "am nhat" trong lan quet dau deu la nghich
    dao co hoc chu khong phai da dang hoa:
        EURGBP | GBPDKK  r = -0,982   GBP la ve SAU o cai nay, ve TRUOC o cai kia
        CHFDKK | EURCHF  r = -0,983   CHF tuong tu
    Ghep hai cai do khong bu rui ro cho nhau - no DONG bot vi the. Mot bang xep
    hang "ung vien ghep" ma dan dau la cac cap nhu vay thi vo dung.
    """
    ca, cb = _chan_tien(ma_a), _chan_tien(ma_b)
    if not ca or not cb:
        return ""
    chung = set(ca) & set(cb)
    if not chung:
        return ""
    t = sorted(chung)[0]
    # Cung vi tri (deu la ve truoc, hoac deu la ve sau) -> tuong quan DUONG co hoc
    if (ca[0] == cb[0]) or (ca[1] == cb[1]):
        return "chung %s cung ve" % t
    return "chung %s NGUOC ve" % t


#: Ma -> so bar co gia <= 0 (o hong lich su). Do trong `bang_loi_suat`.
_GIA_XAU: dict[str, int] = {}


#: Cac ten khac nhau cua CUNG mot thu. Khoa = ten chuan.
BI_DANH = {
    "US500":  {"US500", "US500CASH", "US500M", "SP500", "SPY", "SPX", "US500_SEP26",
               "US500_DEC26", "SP500_DAILY"},
    "US100":  {"US100", "US100CASH", "NASDAQ", "QQQ", "NDX", "US100_SEP26",
               "US100_DEC26"},
    "US30":   {"US30", "US30CASH", "DOW", "DIA", "US30_SEP26", "US30_DEC26"},
    "GOLD":   {"GOLD", "XAUUSD", "GLD", "GOLD_SEP26", "GOLD_DEC26"},
    "SILVER": {"SILVER", "XAGUSD", "SLV"},
    "GER40":  {"GER40", "GER40CASH", "DAX", "GER40_SEP26"},
    "UK100":  {"UK100", "UK100CASH", "FTSE100", "UK100_SEP26"},
    "JP225":  {"JP225", "JP225CASH", "NIKKEI", "JP225_SEP26"},
    "OIL":    {"OIL", "OILMn", "USOIL", "WTI", "CRUDOIL", "USO"},
}
_VE_CHUAN = {t: chuan for chuan, bo in BI_DANH.items() for t in bo}


def ten_chuan(ma: str) -> str:
    """'XM_US500_SEP26' -> 'US500'. Ten khong biet thi tra ve chinh no (da bo
    tien to nha cung cap)."""
    t = ma.upper()
    for tien_to in ("XM_", "YH_", "TS_"):
        if t.startswith(tien_to):
            t = t[len(tien_to):]
    return _VE_CHUAN.get(t, t)


def trung_cong_cu(ma_a: str, ma_b: str) -> bool:
    """Hai ma co phai CUNG mot cong cu duoi hai cai ten khong?

    VI SAO CAN (do 12/09): mười cap "tuong quan cao nhat" cua lan quet dau la
        US500CASH | XM_US500CASH      r = 1,000
        XM_US100CASH | XM_US100_SEP26 r = 0,998
        SP500 | TS_SPY                r = 0,993
    Day khong phai PHAT HIEN - do la cung mot chi so duoi hai ma, hoac cash so
    voi futures cua chinh no. De chung trong bang "tuong quan cao" thi bang do
    chi noi lai chinh cach dat ten kho du lieu.
    """
    return ten_chuan(ma_a) == ten_chuan(ma_b)


def bang_loi_suat(cac_ma: list[str], khung: str = "D1") -> pd.DataFrame:
    """Gom loi suat log cua nhieu ma ve MOT bang da gong hang ngay.

    `concat(axis=1)` roi de NaN - khong dropna o day, vi dropna toan bang se cat
    theo ma NGAN NHAT. Viec gong hang lam theo TUNG CAP trong `tinh`.
    """
    from nhan import du_lieu as DL
    cot = {}
    for ma in cac_ma:
        try:
            df = DL.nap(ma, khung)
        except Exception:
            continue
        if len(df) < BAR_CHUNG_TOI_THIEU:
            continue
        idx = pd.DatetimeIndex(df.index)
        if idx.tz is not None:
            idx = idx.tz_convert("UTC").tz_localize(None)
        c = df["close"].to_numpy(float)
        # log(gia <= 0) = -inf/nan va numpy chi canh bao roi di tiep. Gia <= 0
        # khong ton tai that - no la o hong trong lich su - nen bo O DO thay vi
        # de nan lan sang loi suat cua bar KE TIEP qua .diff().
        xau = ~(c > 0)
        if xau.any():
            _GIA_XAU[ma] = int(xau.sum())
            c = c.copy(); c[xau] = np.nan
        s = pd.Series(np.log(c), index=idx.normalize())
        s = s[~s.index.duplicated(keep="last")].diff()
        cot[ma] = s
    return pd.DataFrame(cot)


def mot_cap(a: pd.Series, b: pd.Series) -> dict | None:
    """Tuong quan + do on dinh cua MOT cap. None neu khong du bar chung."""
    d = pd.concat([a, b], axis=1).dropna()
    if len(d) < BAR_CHUNG_TOI_THIEU:
        return None
    x, y = d.iloc[:, 0], d.iloc[:, 1]
    r = float(x.corr(y))
    if not np.isfinite(r):
        return None
    tr = x.rolling(CUA_SO).corr(y).dropna()
    if len(tr) < 50:
        return {"r": round(r, 4), "bar_chung": len(d), "on_dinh": None,
                "bien_do": None}
    # ON DINH = ty le cua so nam GAN r toan mau, khong phai "cung dau".
    # Ban dau toi dung "cung dau" va no tra 1,000 cho GAN NHU MOI cap - voi
    # r = 0,98 thi cua so nao cung duong, nen thuoc do khong phan biet duoc gi.
    gan = float(np.mean(np.abs(tr.to_numpy() - r) <= LECH_CHO_PHEP))
    return {"r": round(r, 4), "bar_chung": len(d),
            "on_dinh": round(gan, 4),
            "bien_do": round(float(tr.std()), 4),
            "r_min": round(float(tr.min()), 4),
            "r_max": round(float(tr.max()), 4)}


def tinh(cac_ma: list[str], khung: str = "D1", in_ra=print) -> dict:
    t0 = time.time()
    bang = bang_loi_suat(cac_ma, khung)
    ten = list(bang.columns)
    if in_ra:
        in_ra("gom %d/%d ma · %d hang" % (len(ten), len(cac_ma), len(bang)))
    cap = {}
    for i in range(len(ten)):
        for j in range(i + 1, len(ten)):
            r = mot_cap(bang[ten[i]], bang[ten[j]])
            if r:
                if trung_cong_cu(ten[i], ten[j]):
                    r["trung"] = True
                qh = quan_he_co_hoc(ten[i], ten[j])
                if qh:
                    r["co_hoc"] = qh
                cap["%s|%s" % (ten[i], ten[j])] = r
    if in_ra:
        in_ra("tinh %d cap trong %.0fs" % (len(cap), time.time() - t0))

    # --- ho so TUNG MA: ban than no tuong quan the nao voi phan con lai
    ho_so = {}
    for m in ten:
        cua_no = [(k.replace(m, "").strip("|"), v) for k, v in cap.items()
                  if k.startswith(m + "|") or k.endswith("|" + m)]
        if not cua_no:
            continue
        rs = [v["r"] for _, v in cua_no]
        on = [v["on_dinh"] for _, v in cua_no if v.get("on_dinh") is not None]
        duong = sorted(cua_no, key=lambda kv: -kv[1]["r"])[:3]
        am = sorted(cua_no, key=lambda kv: kv[1]["r"])[:3]
        ho_so[m] = {
            "so_cap": len(cua_no),
            "r_trung_vi": round(float(np.median(rs)), 4),
            "r_tuyet_doi_trung_vi": round(float(np.median(np.abs(rs))), 4),
            "on_dinh_trung_vi": round(float(np.median(on)), 4) if on else None,
            "cao_nhat": [{"voi": k, **v} for k, v in duong],
            "am_nhat": [{"voi": k, **v} for k, v in am],
            "so_cap_cao": int(sum(1 for r in rs if r >= CAO)),
            "so_cap_am": int(sum(1 for r in rs if r <= AM)),
        }
    ket = {"khung": khung, "so_ma": len(ten), "so_cap": len(cap),
           "cua_so_on_dinh": CUA_SO, "ho_so": ho_so,
           "gia_xau": dict(_GIA_XAU),
           "cap": dict(sorted(cap.items(), key=lambda kv: -abs(kv[1]["r"]))[:400]),
           "giay": round(time.time() - t0, 1)}
    kho = kho_cua(khung)
    kho.parent.mkdir(exist_ok=True)
    kho.write_text(json.dumps(ket, ensure_ascii=False, indent=1, default=float),
                   encoding="utf-8")
    ket["tep"] = str(kho)
    if in_ra:
        _in_tom_tat(ket, in_ra, cap)
    return ket


def _in_tom_tat(ket: dict, in_ra=print, cap: dict | None = None) -> None:
    cap = ket["cap"] if cap is None else cap
    if ket.get("gia_xau"):
        in_ra("  gia <= 0 (o hong lich su, da bo): %s"
              % ", ".join("%s x%d" % (m, n) for m, n in ket["gia_xau"].items()))
    on = [v["on_dinh"] for v in cap.values() if v.get("on_dinh") is not None]
    in_ra("\n%d cap · on dinh trung vi %.3f" % (ket["so_cap"], float(np.median(on)) if on else 0))
    cao_tat = [(k, v) for k, v in cap.items() if v["r"] >= CAO]
    cao = [(k, v) for k, v in cao_tat if not v.get("trung")]
    in_ra("  cap cao bi loai vi TRUNG CONG CU: %d/%d"
          % (len(cao_tat) - len(cao), len(cao_tat)))
    # UNG VIEN GHEP phai LOAI quan he co hoc: chung mot dong tien thi tuong quan
    # den tu so hoc, khong phai tu hai nguon rui ro khac nhau.
    am_tat = [(k, v) for k, v in cap.items() if v["r"] <= AM]
    am = [(k, v) for k, v in am_tat if not v.get("co_hoc")]
    in_ra("  cap am bi loai vi QUAN HE CO HOC: %d/%d"
          % (len(am_tat) - len(am), len(am_tat)))
    in_ra("  cap TUONG QUAN CAO (>= %.1f): %d   <- dung chay hai he tren ca hai"
          % (CAO, len(cao)))
    in_ra("  cap TUONG QUAN AM  (<= %.1f): %d   <- ung vien GHEP" % (AM, len(am)))

    in_ra("\n10 cap CAO nhat (r · on dinh · bien do · bar chung):")
    for k, v in sorted(cao, key=lambda kv: -kv[1]["r"])[:10]:
        in_ra("  %-30s %+.3f  %s  %s  %d"
              % (k, v["r"],
                 ("%.2f" % v["on_dinh"]) if v.get("on_dinh") is not None else "  - ",
                 ("%.3f" % v["bien_do"]) if v.get("bien_do") is not None else "  -  ",
                 v["bar_chung"]))
    in_ra("\n10 cap AM nhat - ung vien ghep:")
    for k, v in sorted(am, key=lambda kv: kv[1]["r"])[:10]:
        in_ra("  %-30s %+.3f  %s  %s  %d"
              % (k, v["r"],
                 ("%.2f" % v["on_dinh"]) if v.get("on_dinh") is not None else "  - ",
                 ("%.3f" % v["bien_do"]) if v.get("bien_do") is not None else "  -  ",
                 v["bar_chung"]))
    in_ra("\n-> %s" % KHO)


def doc(khung: str = "D1") -> dict:
    try:
        return json.loads(kho_cua(khung).read_text(encoding="utf-8"))
    except Exception:
        return {}


def main(argv: list[str]) -> int:
    from nhan import ho_so_symbol as HSS
    khung = argv[0] if argv else "D1"
    gh = int(argv[1]) if len(argv) > 1 else 0
    hs = HSS.doc()
    if isinstance(hs, dict):
        hs = list(hs.values())
    ma = sorted({str(x.get("ma")) for x in hs if isinstance(x, dict) and x.get("ma")})
    if gh:
        ma = ma[:gh]
    tinh(ma, khung)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
