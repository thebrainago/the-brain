# -*- coding: utf-8 -*-
"""BO DOC MU O DAU? Suat `doc_ma` theo NGON NGU, tren TOAN BO ban doc ma nguon.

Do 03/09/2026: `doc_ma` chay 452 ban ma nguon trong duoi 1 giay (1 ms/ban) va
444/452 khong ra gi. 16 co che moi deu tu `tradingview_pine`.
=> Nut that KHONG phai toc do, KHONG phai chan nhip 600s, KHONG phai nguon it.
   Nut that la BO DOC chi hieu duoc mot lat rat mong nhung gi no doc.

File nay do suat theo tung ngon ngu de biet nen xay bo doc nao TRUOC.

Ghi chu ve BO NHAN DIEN: ban dau `ta\\.` nam trong nhom pine va no khop ca
"beta.", "delta." trong van xuoi -> 605 ban tu github/arxiv bi gan nham la
Pine. Moi mau duoi day phai la mau CHI xuat hien trong ngon ngu do.
"""
from __future__ import annotations

import re
import sys
import warnings
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")

from nhan import doc_ma as DM      # noqa: E402
from nhan import ngu_phap as NP    # noqa: E402
from nhan import so as SO          # noqa: E402

DAU_VAN = [
    ("pine", re.compile(
        r"//@version\s*=|\b(study|indicator|strategy)\s*\(\s*[\"']|"
        r"\bplotshape\s*\(|\bstrategy\.(entry|close|exit)\b|"
        r"\bta\.(sma|ema|rsi|crossover|crossunder|atr|highest|lowest)\s*\(")),
    ("mql", re.compile(
        r"#property\s+\w|\bOnTick\s*\(|\bOnCalculate\s*\(|\biCustom\s*\(|"
        r"\bCTrade\b|\bMqlRates\b|\b(extern|input)\s+(double|int|bool|string)\s+\w")),
    ("python", re.compile(
        r"^\s*(import|from)\s+\w+|^\s*def\s+\w+\s*\(|\bbacktrader\b|"
        r"\bQCAlgorithm\b|^\s*self\.\w+\s*=", re.M)),
    ("cpp_java", re.compile(
        r"^\s*#include\s*[<\"]|\b(public|private)\s+(static\s+)?(class|void|int)\b",
        re.M)),
    ("js", re.compile(
        r"^\s*function\s+\w+\s*\(|=>\s*\{|^\s*const\s+\w+\s*=|"
        r"\brequire\s*\(\s*[\"']", re.M)),
]


def ngon_ngu(vb: str) -> str:
    for ten, rx in DAU_VAN:
        if rx.search(vb or ""):
            return ten
    return "khong_ro"


def main(gioi_han=5000):
    ds = SO.nhieu(
        "SELECT n.van_ban, n.so_ky_tu, t.nguon, t.url "
        "FROM noi_dung n LEFT JOIN tai_lieu t ON t.id = n.tai_lieu_id "
        "WHERE n.so_ky_tu > 500 AND n.kieu = 'ma_nguon' LIMIT ?", gioi_han) or []
    print(f"=== SUAT `doc_ma` — {len(ds)} ban doc MA NGUON (toan bo) ===")

    dem, ra = Counter(), defaultdict(int)
    ky_tu, nguon = defaultdict(int), defaultdict(Counter)
    for r in ds:
        d = dict(r)
        vb = d["van_ban"] or ""
        nn = ngon_ngu(vb)
        dem[nn] += 1
        ky_tu[nn] += d["so_ky_tu"] or 0
        nguon[nn][d.get("nguon") or "?"] += 1
        try:
            kq = DM.doc_chien_luoc(vb, nguon=d.get("url") or "", tien_to="ma")
        except Exception:
            continue
        cc = [c for c in ((kq or {}).get("co_che") or []) if not NP.kiem_khai_bao(c)]
        ra[nn] += len(cc)

    print(f"\n{'ngon ngu':<12}{'so ban':>8}{'trieu ky tu':>13}{'co che':>9}"
          f"{'suat/100 ban':>14}")
    print("-" * 58)
    for nn, n in dem.most_common():
        print(f"{nn:<12}{n:>8}{ky_tu[nn]/1e6:>13.2f}{ra[nn]:>9}"
              f"{ra[nn]/max(n,1)*100:>13.1f}%")
    tn, tc = sum(dem.values()), sum(ra.values())
    print("-" * 58)
    print(f"{'TONG':<12}{tn:>8}{sum(ky_tu.values())/1e6:>13.2f}{tc:>9}"
          f"{tc/max(tn,1)*100:>13.1f}%")

    print("\n-- NGON NGU BO DOC HIEU KEM/KHONG HIEU, xep theo so ban --")
    for nn, n in sorted(dem.items(), key=lambda x: -x[1]):
        if ra[nn] / max(n, 1) >= 0.05:
            continue
        top = ", ".join(f"{k}({v})" for k, v in nguon[nn].most_common(3))
        print(f"   {nn:<12}{n:>5} ban  {ky_tu[nn]/1e6:>6.2f} tr ky tu  "
              f"ra {ra[nn]:>3} co che   tu: {top}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5000)
