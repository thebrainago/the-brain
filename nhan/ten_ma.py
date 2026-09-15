# -*- coding: utf-8 -*-
"""ten_ma.py - MOT nguon su that cho cau hoi "ma nay CO tren terminal khong".

## Vi sao co file nay

15/09/2026: mot luot tester `--ma AUDCAD --khung H4` chay het mot lan boot
terminal roi tra ve `khong thay bang ket qua`. Ly do that nam trong log MT5,
mot dong, rat ro:

    Tester  symbol AUDCAD not exist

Tai khoan dang dang nhap la `XMGlobal-MT5 10` va no chi co ma `...micro`.
`AUDCAD` tran chi ton tai duoi server CU `XMGlobal-MT5 17` (tai khoan da hong
tu 14/09). Ca hai deu nam trong `bases/`, nen moi cong kiem theo kieu "gop het
bases lai" deu tra loi CO - dung khi may chu that su khong co.

Ba cho hong cong lai, va **khong cho nao bao loi**:

1. `chay_bench_quan_tri.goi_y_ma` co san tu 13/09 (chinh no tim ra
   `XAUUSD -> GOLD`) nhung **chi duoc goi trong chinh file do**. Duong chay
   chinh - `chay_tester_kho.py` - khong bao gio thay no.
2. Cong kiem gop TAT CA bases nen khong phan biet duoc may chu dang dung voi
   may chu cu. Kho lich su cua mot tai khoan da chet van tra loi "CO".
3. `DAU_HIEU_HONG` co `unknown symbol` nhung MT5 that su in `not exist` va
   `cannot select symbol in market watch`. Bang dau hieu khong khop mot ky tu
   nao voi cai may that su in ra.

Xem [[luat-khong-nam-tren-duong-chay]], [[luat-do-phai-thay-duoc-cai-co]].

## KHONG CHAN, CHI CANH BAO

Thieu thu muc lich su KHAC voi khong co ma: `US500Cash` ngay 13/09 la ma hoan
toan hop le ma chua co lich su, chi vi chua ai yeu cau no bao gio - va nguoi
yeu cau dau tien chinh la luot tester bi chan. Chi phi mot luot chay thua la
~60 giay; chi phi mot lan chan oan la ca mot ma khong bao gio duoc do.

Nen mac dinh la CANH BAO kem goi y ten dung, khong phai chan. Chi khi co kho
ma DAY DU (`lam_moi_kho_ma()` doc thang tu terminal) thi "khong co ma" moi la
ket luan chac, va luc do `kiem_ten` tra `trang_thai="KHONG_CO"`.
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
KHO_MA = LAB / "config" / "ma_may_chu.json"

#: Ten khac nhau cho cung mot tai san giua cac san. Khong doan duoc bang chuoi:
#: `XAUUSD` va `GOLD` khong chung mot ky tu nao. Chuyen tu
#: `chay_bench_quan_tri.BI_DANH` ve day de ca hai duong chay dung chung.
BI_DANH = {
    "XAUUSD": ["GOLD", "GOLDmicro"], "XAGUSD": ["SILVER", "SILVERmicro"],
    "SPX500": ["US500Cash"], "NAS100": ["US100Cash"],
    "DE40": ["GER40Cash"], "DAX": ["GER40Cash"],
}

#: Duoi ma XM hay gan them. `AUDCAD` tren tai khoan micro la `AUDCADmicro`.
DUOI = ("micro", "Cash", ".a", "m")


def _xm_data() -> Path:
    from chay_tester_z5 import XM_DATA
    return XM_DATA


def may_chu(xm_data: Path | None = None) -> str:
    """Server dang dang nhap, doc tu `config/common.ini` (1 mili giay).

    Day la cau tra loi duy nhat dung cho "ma nay co tren MAY CHU NAO": gop het
    `bases/` lai thi mot tai khoan da chet van con kho lich su cua no.
    """
    d = Path(xm_data) if xm_data else _xm_data()
    f = d / "config" / "common.ini"
    if not f.exists():
        return ""
    for bo_ma in ("utf-16", "utf-8", "cp1252"):
        try:
            van = f.read_text(encoding=bo_ma, errors="ignore")
        except (UnicodeDecodeError, UnicodeError):
            continue
        m = re.search(r"^\s*Server\s*=\s*(.+?)\s*$", van, re.M)
        if m:
            return m.group(1)
    return ""


def kho_ma(server: str = "") -> list:
    """Kho ma DAY DU da doc tu terminal (neu tung chay `lam_moi_kho_ma`)."""
    if not KHO_MA.exists():
        return []
    try:
        d = json.loads(KHO_MA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    sv = server or may_chu()
    return list(d.get(sv) or [])


def ma_co_lich_su(server: str = "", xm_data: Path | None = None) -> list:
    """Ma CO THU MUC LICH SU, chi trong base cua may chu dang dung.

    Khong gop cac base khac: do la cho hong 15/09.
    """
    d = Path(xm_data) if xm_data else _xm_data()
    sv = server or may_chu(d)
    goc = d / "bases" / sv if sv else None
    if goc is None or not goc.exists():
        return []
    return sorted({p.name for p in (goc / "history").glob("*") if p.is_dir()})


def ma_moi_base(xm_data: Path | None = None) -> dict:
    """Ma theo TUNG base - de noi ro 'co, nhung o may chu KHAC'."""
    d = Path(xm_data) if xm_data else _xm_data()
    ra = {}
    for b in sorted((d / "bases").glob("*")):
        h = b / "history"
        if not h.is_dir():
            continue
        ma = sorted({p.name for p in h.glob("*") if p.is_dir()})
        if ma:
            ra[b.name] = ma
    return ra


def goi_y_ma(symbol: str, n: int = 6, server: str = "",
             xm_data: Path | None = None) -> list:
    """Ten ma gan dung. BI DANH -> them DUOI -> chuoi con -> do giong nhau."""
    co = kho_ma(server) or ma_co_lich_su(server, xm_data)
    if not co:
        co = sorted({m for v in ma_moi_base(xm_data).values() for m in v})
    ra = [x for x in BI_DANH.get(symbol.upper(), []) if x in co]
    for h in DUOI:                       # AUDCAD -> AUDCADmicro
        t = symbol + h
        if t in co and t not in ra:
            ra.append(t)
    kh = symbol.upper().replace("CASH", "").replace("MICRO", "")
    for cat in (kh, kh[:4], kh[:3]):
        if len(ra) >= n or len(cat) < 3:
            break
        ra += [x for x in co if cat in x.upper() and x not in ra]
    ra += [x for x in difflib.get_close_matches(symbol, co, n=n, cutoff=0.5)
           if x not in ra]
    return ra[:n]


def kiem_ten(symbol: str, xm_data: Path | None = None) -> dict:
    """Ba trang thai, khong phai hai.

    CO               - ma co mat (kho ma day du, hoac da co lich su)
    KHONG_CO         - co kho ma DAY DU cua may chu nay va ma KHONG trong do
    NGHI_NGO         - chua co lich su o may chu nay, nhung co o may chu KHAC
                       (hoac chua kiem duoc). Khong chan - chi canh bao.
    """
    d = Path(xm_data) if xm_data else _xm_data()
    sv = may_chu(d)
    day_du = kho_ma(sv)
    if day_du:
        if symbol in day_du:
            return {"trang_thai": "CO", "may_chu": sv, "nguon": "kho_ma"}
        return {"trang_thai": "KHONG_CO", "may_chu": sv, "nguon": "kho_ma",
                "goi_y": goi_y_ma(symbol, server=sv, xm_data=d),
                "ly_do": "khong co ma `%s` tren may chu `%s`" % (symbol, sv)}
    ls = ma_co_lich_su(sv, d)
    if symbol in ls:
        return {"trang_thai": "CO", "may_chu": sv, "nguon": "lich_su"}
    o_dau = [b for b, ma in ma_moi_base(d).items() if symbol in ma and b != sv]
    return {
        "trang_thai": "NGHI_NGO", "may_chu": sv, "nguon": "lich_su",
        "goi_y": goi_y_ma(symbol, server=sv, xm_data=d),
        "o_may_chu_khac": o_dau,
        "ly_do": ("`%s` chua co lich su tren may chu dang dung (`%s`)%s"
                  % (symbol, sv or "?",
                     " - no chi co o: " + ", ".join(o_dau) if o_dau else "")),
    }


def canh_bao(symbol: str, xm_data: Path | None = None) -> list:
    """Cac dong PHAI IN RA TRUOC khi dot mot luot boot terminal."""
    k = kiem_ten(symbol, xm_data)
    if k["trang_thai"] == "CO":
        return []
    dau = "MA KHONG CO" if k["trang_thai"] == "KHONG_CO" else "CANH BAO TEN MA"
    ra = ["%s: %s" % (dau, k["ly_do"])]
    if k.get("goi_y"):
        ra.append("   y ban dinh noi la: %s" % ", ".join(k["goi_y"]))
    if k["trang_thai"] == "NGHI_NGO":
        ra.append("   van chay tiep (thieu lich su KHAC voi khong co ma), "
                  "nhung neu ra 0 lenh thi doc dong tren truoc.")
    return ra


def lam_moi_kho_ma(server: str = "") -> dict:
    """Doc DANH SACH MA THAT tu terminal va cache lai.

    Chi sau khi co file nay thi "khong co ma" moi la ket luan chac. Ham nay mo
    terminal nen phai GIU KHOA TESTER - may chi co mot `terminal64.exe`.
    """
    from nhan import khoa_tester as KT
    with KT.giu("ten_ma.lam_moi_kho_ma"):
        import MetaTrader5 as mt5
        if not mt5.initialize():
            return {"loi": "khong initialize duoc MT5: %s" % (mt5.last_error(),)}
        try:
            tk = mt5.account_info()
            sv = server or (tk.server if tk else may_chu())
            ten = sorted(s.name for s in (mt5.symbols_get() or []))
        finally:
            mt5.shutdown()
    d = {}
    if KHO_MA.exists():
        try:
            d = json.loads(KHO_MA.read_text(encoding="utf-8"))
        except ValueError:
            d = {}
    d[sv] = ten
    KHO_MA.parent.mkdir(parents=True, exist_ok=True)
    KHO_MA.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    return {"may_chu": sv, "so_ma": len(ten)}


if __name__ == "__main__":
    import sys
    if "--lam-moi" in sys.argv:
        print(lam_moi_kho_ma())
    else:
        _sv = may_chu()
        print("may chu dang dung :", _sv or "(khong doc duoc)")
        print("kho ma day du     :", len(kho_ma(_sv)) or
              "CHUA CO (chay `python -m nhan.ten_ma --lam-moi`)")
        print("ma co lich su     :", ", ".join(ma_co_lich_su(_sv)) or "(rong)")
        for _a in sys.argv[1:]:
            if not _a.startswith("-"):
                print("\n%s -> %s" % (_a, kiem_ten(_a)))
