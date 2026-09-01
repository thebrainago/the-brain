# -*- coding: utf-8 -*-
"""quy_doi_tham_so.py - DOI TAI SAN THI THAM SO PHAI DOI THEO.

VI SAO CO FILE NAY (do that 01/09/2026).

Chay `GDS Renko Fast Demo EA` tren EURUSDmicro voi tham so MAC DINH cua tac gia:
30,8 trieu tick, 9.208 bar, va **0 lenh**. Khong phai bot hong, cung khong phai
tester hong. Tac gia khai `InpFastBrickSize = 21.0  // Renko brick size in price
units`, va 21 don vi gia la hop ly cho vang (~2.600) hay chi so (~5.900) nhung
EURUSD chi ~1,08 - vien gach Renko lon gap hai muoi lan toan bo bien do cap tien
te, nen khong bao gio hinh thanh mot vien nao.

Bai hoc tong quat: **tham so mac dinh cua mot bot gan chat voi tai san no duoc
viet cho**. Bung nguyen sang tai san khac la mot trong hai ket cuc, va ca hai
deu vo nghia: khong lenh nao, hoac lenh day dac o muc nhieu.

CACH LAM O DAY - va vi sao khong dung ty le GIA:

  Quy doi theo ty le gia (21 x 1,08/2600) nghe hop ly nhung sai o cho quan
  trong: cai quyet dinh mot vien gach co hinh thanh khong la BIEN DONG, khong
  phai muc gia. Hai tai san cung gia 100 co the co bien do ngay khac nhau muoi
  lan. Nen o day quy doi theo **ATR**: giu nguyen SO LAN ATR ma tac gia da chon.

      k        = gia_tri_goc / ATR(tai san goc)
      gia_tri_moi = k x ATR(tai san dich)

  `k` la dai luong KHONG THU NGUYEN, va do dung la thu tac gia thuc su chon khi
  ho go so 21 - ho chon "vien gach bang chung nay nhieu lan bien dong thuong
  ngay", chu khong chon "21 dola".

PHAN LOAI DON VI. Khong doan tu con so ma doc CHU THICH cua chinh tac gia
(`// Renko brick size in price units`, `// Take profit in fast bricks`,
`// Maximum holding time`). Cai gi khong doc duoc thi tra `khong_ro` va KHONG
quy doi - de nguyen va bao ra, chu khong nhan bua roi im lang.
"""
from __future__ import annotations

import re

#: Tu khoa trong TEN hoac CHU THICH -> don vi. Xet theo thu tu; cai dung truoc
#: thang, vi "take profit in fast bricks" vua co "profit" vua co "bricks".
_DAU_HIEU: list[tuple[str, tuple[str, ...]]] = [
    # KHONG THU NGUYEN - la mot BOI SO cua thu khac, doi tai san khong doi
    ("boi_so", ("in bricks", "in fast bricks", "in slow bricks", "as fraction",
                "fraction of", "multiple of", "in atr", "atr multiple",
                "ratio", "factor", "multiplier")),
    # SO LAN / SO BAR / THOI GIAN - dem, khong phai gia
    # "bricks required" / "bricks to wait" la DEM so vien, khac han "brick SIZE"
    # la mot muc gia. Do that: `InpEntryRunBricks = 1` bi xep nham thanh `gia`
    # chi vi ten chua "brick", va quy doi no se bien "cho 1 vien" thanh mot so
    # thap phan vo nghia.
    ("dem", ("period", "bars", "candles", "count", "number of", "minutes",
             "hours", "days", "lookback", "shift", "magic", "slippage limit",
             "bricks required", "bricks to wait", "bricks after")),
    # PHAN TRAM
    ("phan_tram", ("percent", "%", "pct", "risk per", "of balance",
                   "of equity")),
    # DIEM / PIP - thu nguyen gia nhung theo don vi point cua san
    ("diem", ("in points", "points", "pips", "pip")),
    # DON VI GIA - phai quy doi
    ("gia", ("price units", "in price", "price distance", "brick size",
             "in dollars", "in currency", "absolute price")),
    # KHOI LUONG
    ("lot", ("lot", "volume", "lots")),
]

#: Ten bien goi y don vi khi chu thich im lang.
_TEN_GOI_Y: list[tuple[str, tuple[str, ...]]] = [
    ("dem", ("period", "bars", "minutes", "hours", "days", "count", "magic",
             "maxtrades", "cooldown", "hold", "runbricks", "bricks")),
    ("phan_tram", ("percent", "pct", "risk")),
    ("diem", ("points", "pips", "pip", "distance", "step", "sl", "tp",
              "stoploss", "takeprofit", "trail")),
    # CHI `bricksize`, khong phai `brick` tran: `EntryRunBricks` la so vien.
    ("gia", ("bricksize", "pricestep", "gridprice", "pricedistance")),
    ("lot", ("lot", "volume")),
]


def phan_loai(ten: str, chu_thich: str = "", kieu: str = "") -> str:
    """Don vi cua mot input: gia | diem | phan_tram | boi_so | dem | lot | khong_ro.

    Doc CHU THICH truoc, ten sau. `int` thi gan nhu chac chan la mot bo dem chu
    khong phai mot muc gia, nen dung lam chan cuoi.
    """
    ct = (chu_thich or "").lower()
    for don_vi, tu in _DAU_HIEU:
        if any(t in ct for t in tu):
            return don_vi
    t = re.sub(r"[^a-z]", "", (ten or "").lower())
    for don_vi, tu in _TEN_GOI_Y:
        if any(x in t for x in tu):
            return don_vi
    if (kieu or "").lower() in ("int", "uint", "long", "ulong", "datetime"):
        return "dem"
    return "khong_ro"


def rut_khai_bao(ma: str) -> list[dict]:
    """Input cua EA kem KIEU va CHU THICH - ba thu can de biet don vi.

    `doc_ma.rut_input` chi lay ten va gia tri; o day can ca chu thich, vi chinh
    chu thich moi noi don vi.
    """
    ra = []
    for m in re.finditer(
            r"^[ \t]*(?:input|extern)[ \t]+(\w+)[ \t]+(\w+)[ \t]*=[ \t]*"
            r"([^;]+);[ \t]*(?://[ \t]*(.*))?$", ma or "", re.M):
        kieu, ten, gt, ct = m.group(1), m.group(2), m.group(3).strip(), m.group(4) or ""
        try:
            v = float(gt)
        except ValueError:
            continue                       # true/false, chuoi, enum - khong quy doi
        ra.append({"ten": ten, "kieu": kieu, "gia_tri": v,
                   "chu_thich": ct.strip(),
                   "don_vi": phan_loai(ten, ct, kieu)})
    return ra


def quy_doi(khai: list[dict], atr_goc: float, atr_dich: float,
            diem_goc: float | None = None,
            diem_dich: float | None = None) -> dict:
    """Doi bo tham so tu tai san goc sang tai san dich.

    Chi dong vao hai don vi CO THU NGUYEN GIA:
      `gia`  -> nhan ty le ATR (giu nguyen so lan ATR ma tac gia chon)
      `diem` -> nhan ty le point cua hai san neu biet, khong thi ty le ATR

    Moi thu khac giu NGUYEN. `boi_so`, `dem`, `phan_tram`, `lot` khong co thu
    nguyen gia nen doi chung la lam hong y dinh cua tac gia. `khong_ro` cung giu
    nguyen - va duoc bao ra de nguoi kiem, chu khong doan.
    """
    if not atr_goc or not atr_dich or atr_goc <= 0 or atr_dich <= 0:
        raise ValueError("atr_goc va atr_dich phai duong")
    ty_atr = atr_dich / atr_goc
    ty_diem = ((diem_dich / diem_goc)
               if (diem_goc and diem_dich and diem_goc > 0) else ty_atr)
    moi, doi, giu, ngo = {}, [], [], []
    for k in khai:
        v, dv = k["gia_tri"], k["don_vi"]
        if dv == "gia":
            nv = v * ty_atr
        elif dv == "diem":
            nv = v * ty_diem
        else:
            nv = v
            (ngo if dv == "khong_ro" else giu).append(k["ten"])
        if nv != v:
            doi.append({"ten": k["ten"], "cu": v, "moi": round(nv, 6),
                        "don_vi": dv, "chu_thich": k["chu_thich"][:60]})
        moi[k["ten"]] = nv
    return {"tham_so": moi, "ty_le_atr": round(ty_atr, 6),
            "ty_le_diem": round(ty_diem, 6), "da_doi": doi,
            "giu_nguyen": giu, "khong_ro": ngo}


def atr_cua(ma: str, khung: str = "H1", n: int = 14) -> float | None:
    """ATR trung vi cua mot tai san, doc tu kho du lieu cua chinh du an."""
    try:
        from nhan import du_lieu as DL, mau as MAU
        df = DL.nap(ma, khung)
        if df is None or len(df) < n * 3:
            return None
        return float(MAU.atr(df, n).median())
    except Exception:
        return None
