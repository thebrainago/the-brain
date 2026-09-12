# -*- coding: utf-8 -*-
"""_so_quan_tri.py - THEM QUAN TRI THI KET QUA DOI RA SAO?

Cau hoi nguyen van cua chu du an trong `SO_DO_HE_THONG.txt`:
    "tet thu tung phuong phap quan li lenh khac nhau de xem hieu qua cung nhu
     ket qua thay doi ra sao"

Bien doc lap DUY NHAT la BO LUAT QUAN TRI. Tin hieu vao, tai san, khung, chi phi
deu giu nguyen. Moi dong quy ve cung ngan sach sut giam 20% va so voi moc
max(mua-giu, ban-giu, tien mat) cung quy ve muc do.

Chay:  python _so_quan_tri.py [so_tien_trinh]
Ra:    reports/SO_QUAN_TRI.json
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))
warnings.filterwarnings("ignore")

import numpy as np  # noqa: E402

RA = LAB / "reports" / "SO_QUAN_TRI.json"
MA_KHUNG = [("XM_US30CASH", "H4"), ("XM_US30CASH", "D1"),
            ("XM_US500CASH", "H4"), ("XM_US100CASH", "H4"),
            ("XM_FRA40CASH", "H4"), ("XM_AUS200CASH", "H4"),
            ("XM_JP225CASH", "H4"), ("XM_GER40CASH", "H4"),
            ("AUDCAD", "H4"), ("EURUSD", "H4"), ("GBPUSD", "H4"),
            ("XAUUSD", "H4")]


def _tin_hieu(df):
    from nhan import ngu_phap as NP
    moc = {"chi_bao": "moc_ky", "ky": "thang", "lay": "dong_truoc"}
    th = np.zeros(len(df))
    for ch in (1, -1):
        s = {"ten": "x", "ho": "quay_ve_trung_binh", "chieu": ch, "giu": 1,
             "co_che": "x" * 30,
             "vao": [{"trai": {"chi_bao": "zscore", "n": 20,
                               "cua": {"chi_bao": "gia", "cot": "close"}},
                      "phep": "<" if ch > 0 else ">",
                      "phai": {"hang": -1.0 if ch > 0 else 1.0}},
                     {"trai": {"chi_bao": "tuyet_doi", "cua": {
                         "chi_bao": "tuyen_tinh",
                         "toan_hang": [{"chi_bao": "gia", "cot": "close"}, moc],
                         "he_so": [1.0, -1.0]}},
                      "phep": "<", "phai": {"chi_bao": "atr", "n": 14}}], "ra": []}
        th = th + np.asarray(NP.sinh_tu_spec(s, df), float)
    return np.clip(th, -1.0, 1.0)


def _mot(args):
    ma, khung = args
    from nhan import dap_quan_tri as DQT
    from nhan import du_lieu as DL
    try:
        df = DL.nap(ma, khung)
        if len(df) < 500:
            return []
        return DQT.so_luat(df, _tin_hieu(df), ma, khung, giu_toi_da=20)
    except Exception as e:
        return [{"ma": ma, "khung": khung, "loi": "%s: %s" % (type(e).__name__, str(e)[:60])}]


def main(argv):
    from collections import defaultdict
    from concurrent.futures import ProcessPoolExecutor
    n_tt = int(argv[0]) if argv else 10
    t0 = time.time()
    ket = []
    with ProcessPoolExecutor(max_workers=n_tt) as ex:
        for r in ex.map(_mot, MA_KHUNG):
            ket.extend(r)
    ok = [r for r in ket if "loi" not in r]
    print("%d o / %.0fs" % (len(ok), time.time() - t0))

    theo = defaultdict(list)
    for r in ok:
        theo[r["luat"]].append(r)
    import statistics
    print("\n=== TAC DUNG CUA TUNG BO LUAT (tren %d cap ma-khung) ===" % len(MA_KHUNG))
    print("%-22s %10s %9s %9s %8s %8s"
          % ("bo luat", "CAGR@dd20", "Sharpe tv", "lenh tv", "%hon moc", "%duong"))
    print("-" * 72)
    goc = {}
    for ten, rs in theo.items():
        c = [r["cagr_dd20"] for r in rs]
        goc[ten] = statistics.median(c)
    for ten, rs in sorted(theo.items(), key=lambda kv: -goc[kv[0]]):
        c = [r["cagr_dd20"] for r in rs]
        print("%-22s %10.2f %9.3f %9.0f %7.1f%% %7.1f%%"
              % (ten, statistics.median(c),
                 statistics.median([r["sharpe"] for r in rs]),
                 statistics.median([r["so_lenh"] for r in rs]),
                 100 * sum(1 for r in rs if r["hon_moc"]) / len(rs),
                 100 * sum(1 for x in c if x > 0) / len(c)))
    nen = goc.get("khong_gi", 0.0)
    print("\n>>> MOC DOI CHIEU la `khong_gi` (vao roi giu 20 bar): %.2f%%" % nen)
    tot = [(t, v) for t, v in goc.items() if t != "khong_gi" and v > nen]
    print(">>> bo luat LAM TOT LEN: %d/%d" % (len(tot), len(goc) - 1))
    for t, v in sorted(tot, key=lambda x: -x[1]):
        print("      %-22s %+.2f diem (%.2f so voi %.2f)" % (t, v - nen, v, nen))

    hon = [r for r in ok if r["hon_moc"]]
    hon.sort(key=lambda r: -r["cagr_dd20"])
    print("\n=== 12 O HON MOC, xep theo CAGR@dd20 ===")
    print("%-16s %-5s %-22s %9s %9s %7s %8s"
          % ("ma", "khung", "luat", "CAGR@dd20", "moc@dd20", "lenh", "Sharpe"))
    for r in hon[:12]:
        print("%-16s %-5s %-22s %9.2f %9.2f %7d %8.3f"
              % (r["ma"], r["khung"], r["luat"], r["cagr_dd20"], r["moc_dd20"],
                 r["so_lenh"], r["sharpe"]))
    RA.parent.mkdir(exist_ok=True)
    RA.write_text(json.dumps({"so_o": len(ok), "ket": ok}, ensure_ascii=False,
                             indent=1), encoding="utf-8")
    print("\n-> %s" % RA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
