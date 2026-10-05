# -*- coding: utf-8 -*-
"""xuat_gia.py - XUAT gia cua vai cap ra file nho de cloud chay duoc `quet_luoi` (chu du an duyet 05/10/2026).

`b xuat-gia AUDCAD,NZDCAD M15 [--thu-muc DIR] [--tu NAM]` (chay o MAY NHA, noi co `data/`):
  1. `du_lieu.nap(ma, khung)` -> OHLC + tick_volume + spread, gio UTC.
  2. Ghi `<thu-muc>/<MA>_<KHUNG>.csv.gz` (mac dinh `du_lieu_gia/`, trong git) + `MANIFEST.json` (so bar, tu-den, sha256).
  3. SAO LUU truoc: moi file cung duoc chep vao `../sao_luu_gia/<ngay>/` (NGOAI git) de neu phai go khoi repo
     (ban quyen nha moi gioi) thi con ban goc. Chi du lieu gia cua vai cap; KHONG tick, KHONG thong tin tai khoan.
`doc(ma, khung, thu_muc)` doc lai thanh DataFrame (cot open high low close tick_volume spread, index thoi gian UTC).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import date
from pathlib import Path

import pandas as pd

GOC = Path(__file__).resolve().parent.parent
MAC_DINH = GOC / "du_lieu_gia"
COT = ["open", "high", "low", "close", "tick_volume", "spread"]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def ghi(df: pd.DataFrame, ma: str, khung: str, thu_muc: Path = MAC_DINH, sao_luu: Path | None = None) -> dict:
    """Ghi MOT cap. Tra dong manifest. `sao_luu=None` -> `../sao_luu_gia/<hom nay>/`."""
    thu_muc = Path(thu_muc)
    thu_muc.mkdir(parents=True, exist_ok=True)
    cot = [c for c in COT if c in df.columns]
    if not {"open", "high", "low", "close"} <= set(cot):
        raise ValueError("thieu cot OHLC: %s" % list(df.columns))
    d = df[cot].copy()
    d.index = pd.to_datetime(d.index)
    if d.index.tz is not None:
        d.index = d.index.tz_convert("UTC").tz_localize(None)
    d.index.name = "time"
    f = thu_muc / ("%s_%s.csv.gz" % (ma, khung))
    d.to_csv(f, compression="gzip", float_format="%.6g")
    sl = Path(sao_luu) if sao_luu else GOC.parent / "sao_luu_gia" / date.today().isoformat()
    sl.mkdir(parents=True, exist_ok=True)
    shutil.copy2(f, sl / f.name)
    return {"ma": ma, "khung": khung, "so_bar": int(len(d)), "tu": str(d.index.min()), "den": str(d.index.max()),
            "byte": f.stat().st_size, "sha256": _sha(f)}


def doc(ma: str, khung: str = "M15", thu_muc: Path = MAC_DINH) -> pd.DataFrame:
    f = Path(thu_muc) / ("%s_%s.csv.gz" % (ma, khung))
    df = pd.read_csv(f, index_col="time", parse_dates=True)
    return df


def chay(cac_ma: list[str], khung: str = "M15", thu_muc: Path = MAC_DINH, tu: str | None = None) -> list[dict]:
    from nhan import du_lieu
    mf = []
    for ma in cac_ma:
        df = du_lieu.nap(ma, khung, tu=tu)
        mf.append(ghi(df, ma, khung, thu_muc))
        print("%s %s: %d bar %s -> %s, %.1f MB" % (ma, khung, mf[-1]["so_bar"], mf[-1]["tu"][:10], mf[-1]["den"][:10],
                                                  mf[-1]["byte"] / 1e6))
    p = Path(thu_muc) / "MANIFEST.json"
    cu = json.loads(p.read_text("utf-8")) if p.exists() else {}
    for m in mf:
        cu["%s_%s" % (m["ma"], m["khung"])] = m
    p.write_text(json.dumps(cu, ensure_ascii=False, indent=1), "utf-8")
    return mf


def main_cli(a: list[str] | None = None) -> None:
    a = list(sys.argv[1:] if a is None else a)
    if not a:
        sys.exit(__doc__)
    th = Path(a[a.index("--thu-muc") + 1]) if "--thu-muc" in a else MAC_DINH
    tu = a[a.index("--tu") + 1] if "--tu" in a else None
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in ("--thu-muc", "--tu"))]
    chay(pos[0].split(","), pos[1] if len(pos) > 1 else "M15", th, tu)


if __name__ == "__main__":
    main_cli()
