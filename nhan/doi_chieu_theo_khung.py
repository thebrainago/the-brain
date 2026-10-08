# -*- coding: utf-8 -*-
"""doi_chieu_theo_khung.py - engine <-> MT5 theo KHUNG va theo MUC DD (cloud doc viec/xong, khong LLM, khong du lieu gia).
Tra loi (chu du an 08/10): (1) cung dau bao nhieu, engine lac quan may lan, nguong loai som khi engine lo / lai it;
(2) khung nho (M5...) co hieu suat tot khong: so cap engine-vs-MT5 theo khung. Chay: python3 -m nhan.doi_chieu_theo_khung"""
import glob, json, statistics as S
from collections import defaultdict
from nhan.doi_chieu_mo_phong import _RE


def doc():
    rows = []
    for f in glob.glob("viec/xong/*hc-luoi-*.json"):
        d = json.load(open(f, encoding="utf-8")); b = d.get("bang_chung", {})
        m = _RE.search("".join(b.get("dong_cuoi") or []))
        if not m:
            continue
        e, mt, de, dm = map(float, m.groups())
        try:
            s = json.loads((b.get("lenh") or [])[5])
        except Exception:
            s = {}
        rows.append(dict(e=e, m=mt, de=de, dm=dm, k=s.get("khung") or "?", ma=s.get("ma")))
    return rows


def main():
    rows = doc()
    print("n", len(rows))
    khung = defaultdict(list)
    for r in rows:
        khung[r["k"]].append(r)
    for k, g in sorted(khung.items()):
        pos = [r for r in g if r["e"] > 0 and r["m"] > 0]
        print("%-4s n=%-3d cung dau %d/%d | MT5>0 %d | engine>0 nhung MT5<=0: %d | MT5/engine trung vi %s | DD engine/MT5 trung vi %s" % (
            k, len(g), sum((r["e"] > 0) == (r["m"] > 0) for r in g), len(g), sum(r["m"] > 0 for r in g),
            sum(r["e"] > 0 and r["m"] <= 0 for r in g),
            round(S.median(r["m"] / r["e"] for r in pos), 2) if pos else None,
            round(S.median(r["dm"] / r["de"] for r in g if r["de"] > 1), 2) if any(r["de"] > 1 for r in g) else None))
    print("--- loc theo engine (%/nam): ngay duoi nguong, MT5 lai bao nhieu / lai it")
    for x in (-10, -5, 0, 5, 10, 15, 20):
        g = [r for r in rows if r["e"] <= x]
        print("engine <= %4d: n=%-3d MT5>0 %-3d (cat nham neu MT5 >= 10: %d)" % (x, len(g), sum(r["m"] > 0 for r in g), sum(r["m"] >= 10 for r in g)))
    print("--- dd (engine DD%% -> MT5 DD%%): dung de dat nguong cat som theo von")
    for x in (20, 30, 40, 50, 60, 70):
        g = [r for r in rows if r["de"] >= x]
        print("DD engine >= %d: n=%-3d MT5 DD trung vi %s, MT5 lai>0: %d" % (x, len(g), round(S.median(r["dm"] for r in g), 1) if g else None, sum(r["m"] > 0 for r in g)))


if __name__ == "__main__":
    main()
