# -*- coding: utf-8 -*-
"""_quet_song_moc.py - QUET DA CAP x DA KHUNG x DA THONG SO cho co che song+moc.

Muc "QUANTLAB chien luoc" cua `SO_DO_HE_THONG.txt`:
    "tat ca moi chien luoc can test da cap / da khung / da phuong phap quan li /
     da thong so input"

## VI SAO CAN QUET, chu khong phai sua tay

`quy_luat_song` do duoc BON quy luat dat 15/15 o (3 ma x 5 khung M15..D1).
Co che dau tien ghep tu chung (zscore -1,0 · giu 5 bar · AUDCAD H1) thi:

    phi = 0   CAGR +0,65%  Sharpe 0,237   <- edge CO THAT
    co phi    CAGR -3,25%  Sharpe -1,123  <- chi phi an het

Tuc khong phai "quy luat sai" ma la **loi moi lenh nho hon phi moi lenh**. Ba
duong ra, va ca ba deu la THONG SO chu khong phai y tuong moi:

  1. vao SAU hon (zscore am hon) -> it lenh hon, moi lenh day hon
  2. giu LAU hon                 -> it vong quay hon
  3. tai san/khung RE hon        -> chi so CFD spread ~0,94 bps vs cap cheo FX

Nen quet ca ba truc cung luc va hoi mot cau duy nhat: **o nao NET duong VA hon
mua-giu o cung sut giam**.

## CHON THEO TIEN, KHONG THEO SHARPE

Theo so do: "muc dich cuoi cung la co tien chap nhan ca chi phi va rui ro cao".
Nen cot quyet dinh la `cagr_khop_dd` - CAGR khi nang don bay len CUNG sut giam
voi mua-giu. Sharpe van in ra nhung khong dung de loai.

Chay:  python _quet_song_moc.py [so_tien_trinh]
Ra:    reports/QUET_SONG_MOC.json
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

RA = LAB / "reports" / "QUET_SONG_MOC.json"

MA = ["AUDCAD", "EURUSD", "GBPUSD", "EURGBP", "USDJPY", "XAUUSD",
      "XM_US500CASH", "XM_US100CASH"]
KHUNG = ["H1", "H4", "D1"]
Z = [-1.0, -1.5, -2.0, -2.5]
GIU = [5, 20, 60, 120]
#: Khoang cach toi moc, tinh bang ATR. Nho = phai rat gan moc moi vao.
KC_ATR = [0.5, 1.0, 2.0]


def spec(chieu: int, z: float, giu: int, kc: float) -> dict:
    moc = {"chi_bao": "moc_ky", "ky": "thang", "lay": "dong_truoc"}
    return {
        "ten": "song_moc_z%.1f_g%d_k%.1f_%s" % (z, giu, kc, "mua" if chieu > 0 else "ban"),
        "ho": "quay_ve_trung_binh", "chieu": chieu, "giu": giu,
        "co_che": ("Ghep bon quy luat song do duoc 12/09 (15/15 o tren 3 ma x 5 khung): "
                   "hoi ket thuc gan moc dong thang truoc, song so le nhau, bien do cum. "
                   "Ben bi ep dieu chinh vi the quanh moc thang la ben tra tien."),
        "vao": [
            {"trai": {"chi_bao": "zscore", "n": 20,
                      "cua": {"chi_bao": "gia", "cot": "close"}},
             "phep": "<" if chieu > 0 else ">",
             "phai": {"hang": z if chieu > 0 else -z}},
            {"trai": {"chi_bao": "tuyet_doi", "cua": {
                "chi_bao": "tuyen_tinh",
                "toan_hang": [{"chi_bao": "gia", "cot": "close"}, moc],
                "he_so": [1.0, -1.0]}},
             "phep": "<", "phai": {"chi_bao": "tuyen_tinh",
                                   "toan_hang": [{"chi_bao": "atr", "n": 14}],
                                   "he_so": [kc]}}],
        "ra": []}


def _mot(args) -> list[dict]:
    ma, khung = args
    from nhan import bien_don_bay as B
    from nhan import chi_phi as CP
    from nhan import du_lieu as DL
    from nhan import mo_phong as MP
    from nhan import ngu_phap as NP
    try:
        df = DL.nap(ma, khung)
    except Exception as e:
        return [{"ma": ma, "khung": khung, "loi": str(e)[:60]}]
    if len(df) < 500:
        return [{"ma": ma, "khung": khung, "loi": "chi %d bar" % len(df)}]
    c = CP.tu_du_lieu(ma, df)
    cp = c[0] if isinstance(c, tuple) else c
    bh = B._chi_so(MP.mua_giu(df, cp, ma=ma, khung=khung))
    ra = []
    for z in Z:
        for giu in GIU:
            for kc in KC_ATR:
                try:
                    v = np.zeros(len(df))
                    for ch in (1, -1):
                        v = v + np.asarray(NP.sinh_tu_spec(spec(ch, z, giu, kc), df), float)
                    v = np.clip(v, -1.0, 1.0)
                    kh = float(np.mean(np.abs(v) > 0))
                    if kh < 0.002:
                        continue
                    kq = MP.chay(df, v, cp, ma=ma, khung=khung, don_bay=1.0, gop="so_hoc")
                    h = B._chi_so(kq)
                    L = abs(bh["maxdd"]) / max(abs(h["maxdd"]), 1e-9)
                    ra.append({
                        "ma": ma, "khung": khung, "z": z, "giu": giu, "kc_atr": kc,
                        "cagr_pct": round(h["cagr"] * 100, 3),
                        "sharpe": round(h["sharpe"], 3),
                        "maxdd_pct": round(h["maxdd"] * 100, 2),
                        "so_lenh": int(kq.so_lenh), "kich_hoat": round(kh, 4),
                        "L_khop_dd": round(L, 2),
                        "cagr_khop_dd": round(h["cagr"] * 100 * L, 3),
                        "bh_cagr_pct": round(bh["cagr"] * 100, 3),
                        "bh_sharpe": round(bh["sharpe"], 3),
                        "hon_mua_giu": bool(h["cagr"] * L > bh["cagr"]
                                            and h["sharpe"] > bh["sharpe"]),
                    })
                except Exception:
                    continue
    return ra


def main(argv: list[str]) -> int:
    from concurrent.futures import ProcessPoolExecutor
    n_tt = int(argv[0]) if argv else 10
    viec = [(m, k) for m in MA for k in KHUNG]
    print("quet %d ma x %d khung x %d z x %d giu x %d kc = %d o | %d tien trinh"
          % (len(MA), len(KHUNG), len(Z), len(GIU), len(KC_ATR),
             len(viec) * len(Z) * len(GIU) * len(KC_ATR), n_tt))
    t0 = time.time()
    ket = []
    with ProcessPoolExecutor(max_workers=n_tt) as ex:
        for r in ex.map(_mot, viec):
            ket.extend(r)
    ok = [r for r in ket if "loi" not in r]
    hon = [r for r in ok if r["hon_mua_giu"]]
    duong = [r for r in ok if r["cagr_pct"] > 0]
    print("\n%d o chay duoc / %.0fs · NET duong %d · HON mua-giu %d"
          % (len(ok), time.time() - t0, len(duong), len(hon)))
    hon.sort(key=lambda r: -r["cagr_khop_dd"])
    if hon:
        print("\n%-14s %-5s %6s %5s %6s %9s %8s %7s %10s %9s"
              % ("ma", "khung", "z", "giu", "kcATR", "CAGR%", "Sharpe", "lenh",
                 "CAGR@ddBH", "BH CAGR%"))
        for r in hon[:25]:
            print("%-14s %-5s %6.1f %5d %6.1f %9.2f %8.3f %7d %10.2f %9.2f"
                  % (r["ma"], r["khung"], r["z"], r["giu"], r["kc_atr"],
                     r["cagr_pct"], r["sharpe"], r["so_lenh"],
                     r["cagr_khop_dd"], r["bh_cagr_pct"]))
    else:
        print("  khong o nao hon mua-giu.")
        duong.sort(key=lambda r: -r["cagr_pct"])
        print("\n  10 o NET duong tot nhat (van thua mua-giu):")
        for r in duong[:10]:
            print("    %-14s %-5s z%.1f giu%-4d kc%.1f  CAGR %6.2f%% vs BH %6.2f%%  lenh %d"
                  % (r["ma"], r["khung"], r["z"], r["giu"], r["kc_atr"],
                     r["cagr_pct"], r["bh_cagr_pct"], r["so_lenh"]))
    RA.parent.mkdir(exist_ok=True)
    RA.write_text(json.dumps({"so_o": len(ok), "net_duong": len(duong),
                              "hon_mua_giu": len(hon), "giay": round(time.time() - t0, 1),
                              "ket": ok}, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    print("\n-> %s" % RA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
