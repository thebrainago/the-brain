# -*- coding: utf-8 -*-
"""lo_mot_gio.py - LO VIEC TU CHAY, khong can nguoi ngoi may.

Chu du an het token toi 12:10 ngay 01/09 va giao may chay tiep trong mot tieng.

CHON VIEC THEO DON BAY DA DO DUOC SANG NAY, khong phai theo cam giac:

  - Pine la nguon co suat rut co che CAO NHAT: 56 script lay duoc ma -> 11 cai ra
    co che, trung binh **4,9 kieu danh moi file co ra**. MQL5 thi bo doc regex ra
    0/7 (gioi han kien truc, phai chay tester). Nen gio may ranh thi do vao Pine.
  - Trong kho da co ~1.660 ban doc CHUA AI BOC. Chay lai bo rut tren toan kho
    khong ton mot lan tai trang nao.

KHONG LAM O DAY, co y:
  - Khong chay tester MT5: no doi dong terminal, va lo nay chay nen khong nen tu
    dong giet tien trinh cua nguoi dung khi khong ai ngoi may.
  - Khong dang ky gia thuyet, khong cham holdout: moi thu o day dung o muc THU
    VIEN CO CHE (`ngu_phap.them_co_che`), khong tieu mot suat FDR nao.

Chay:  python lo_mot_gio.py [--phut 60]
Nhat ky: reports/LO_MOT_GIO.log  ·  Ket qua: reports/LO_MOT_GIO.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

RA_JSON = LAB / "reports" / "LO_MOT_GIO.json"

#: Tu khoa hoi o search TradingView. Rong ve CO CHE chu khong ve ten chi bao, de
#: khong keo ve mot ro bien the cua cung mot thu.
TU_KHOA = [
    # co che
    "mean reversion", "breakout", "momentum", "trend following", "scalping",
    "swing trading", "pullback", "range trading", "volatility", "session",
    "opening range", "gap", "reversal", "divergence", "support resistance",
    "moving average cross", "bollinger", "rsi", "atr stop", "donchian",
    "ichimoku", "vwap", "order block", "supply demand", "market structure",
    "seasonality", "day of week", "overnight", "carry", "pairs trading",
    # them 01/09 luot hai: mo rong sau khi cong khu trung theo dieu kien da co,
    # nen chay lai khong con de ra ban trung.
    "keltner", "supertrend", "parabolic sar", "adx trend", "stochastic",
    "macd strategy", "cci", "williams", "money flow", "obv", "accumulation",
    "volume profile", "fair value gap", "liquidity sweep", "break of structure",
    "engulfing", "pin bar", "inside bar", "harmonic", "fibonacci retracement",
    "pivot point", "camarilla", "murrey math", "regression channel",
    "standard deviation channel", "zscore", "hurst", "kalman filter",
    "hidden markov", "machine learning", "neural", "grid trading", "martingale",
    "hedging", "arbitrage", "statistical arbitrage", "cointegration",
    "risk parity", "portfolio rotation", "relative strength", "sector rotation",
    "gap and go", "opening drive", "closing auction", "turn of month",
    "pre market", "news trading", "economic calendar", "interest rate",
    "yield curve", "vix", "term structure", "put call ratio", "open interest",
    "commitment of traders", "smart money", "wyckoff", "elliott wave",
    "renko strategy", "heikin ashi", "point and figure", "tick chart",
]


def _log(f, s: str) -> None:
    d = f"{time.strftime('%H:%M:%S')}  {s}"
    print(d, flush=True)
    f.write(d + "\n")
    f.flush()


def phase_pine(f, han: float, bao: dict) -> None:
    """Gom Pine tu o search, rut co che, cho qua cong ngu phap."""
    from tru import seeker as S
    from nhan import doc_ma as DM, du_lieu as DL, ngu_phap as NP
    NP.nap_vao_mau()
    df = DL.nap("EURGBP", "H4")
    S._ghi_con_tro("tradingview_pine", {})
    kho: dict[str, dict] = {}
    # CHUA THOI GIAN CHO KHAU RUT. Ban dau khau GOM duoc chay toi `han`, nen khi
    # ngan sach ngan thi no an het gio va vong rut thoat ngay o dieu kien dau -
    # do that: 18 script gom duoc, 0 khai bao rut ra. Gom chi duoc dung 40%.
    han_gom = time.time() + (han - time.time()) * 0.40
    for i in range(0, len(TU_KHOA), 3):
        if time.time() > han_gom:
            break
        try:
            for d in S.n_tradingview_pine(TU_KHOA[i:i + 3]):
                if d.get("_pine"):
                    kho[d["url"]] = d
        except Exception as e:
            _log(f, f"  [pine] loi thu thap: {type(e).__name__}: {str(e)[:80]}")
        _log(f, f"  [pine] da hoi {min(i + 3, len(TU_KHOA))}/{len(TU_KHOA)} tu khoa "
                f"· {len(kho)} script co ma")
    bao["pine_script"] = len(kho)

    # luu vao so de lan sau khong tai lai
    try:
        S.luu_tai_lieu("tradingview_pine", list(kho.values()))
    except Exception as e:
        _log(f, f"  [pine] loi luu so: {type(e).__name__}")

    nhan, thu, tu_choi = 0, 0, {}
    for u, d in kho.items():
        if time.time() > han:
            break
        try:
            ds = DM.doc_ma(d["_pine"], "pine", nguon=u,
                           tien_to=DM.re.sub(r"[^a-z0-9]+", "_",
                                             d["tieu_de"][7:].lower())[:20] or "tv")
        except Exception:
            continue
        for spec in ds:
            thu += 1
            try:
                r = NP.them_co_che(dict(spec), df)
            except Exception as e:
                tu_choi[type(e).__name__] = tu_choi.get(type(e).__name__, 0) + 1
                continue
            if r.get("nhan"):
                nhan += 1
            else:
                k = "; ".join(r.get("ly_do") or [])[:60]
                tu_choi[k] = tu_choi.get(k, 0) + 1
    bao.update({"pine_khai_bao_thu": thu, "pine_co_che_nhan": nhan,
                "pine_ly_do_tu_choi": dict(sorted(tu_choi.items(),
                                                  key=lambda x: -x[1])[:12])})
    _log(f, f"  [pine] {thu} khai bao thu · **{nhan} co che vao thu vien**")


def phase_thu_hoi(f, han: float, bao: dict) -> None:
    """Chay bo thu hoi thanh phan tren TOAN BO ban doc da co. Khong tai gi moi."""
    from nhan import so as SO, thu_hoi_thanh_phan as TH
    rs = SO.nhieu("SELECT nd.van_ban, nd.url, t.tieu_de, t.nguon FROM noi_dung nd "
                  "LEFT JOIN tai_lieu t ON t.id = nd.tai_lieu_id "
                  "WHERE nd.so_ky_tu > 400")
    moi, n = 0, 0
    for r in rs:
        if time.time() > han:
            break
        n += 1
        try:
            moi += TH.thu_hoi(r["tieu_de"] or "", r["van_ban"] or "",
                              r["url"] or "", r["nguon"] or "")["moi"]
        except Exception:
            continue
    bao.update({"thu_hoi_ban_doc": n, "thu_hoi_thanh_phan_moi": moi,
                "toan_hang_con_thieu": [
                    {"chi_bao": x["chi_bao"], "tong_lan": x["tong_lan"]}
                    for x in TH.toan_hang_con_thieu(15)]})
    _log(f, f"  [thu hoi] quet {n} ban doc · {moi} thanh phan moi")


def phase_doc_ma_kho(f, han: float, bao: dict) -> None:
    """Chay bo doc ma tren ban doc MA NGUON da co trong kho."""
    from nhan import doc_ma as DM, du_lieu as DL, ngu_phap as NP, so as SO
    NP.nap_vao_mau()
    df = DL.nap("EURGBP", "H4")
    rs = SO.nhieu("SELECT nd.van_ban, nd.url, t.tieu_de FROM noi_dung nd "
                  "LEFT JOIN tai_lieu t ON t.id = nd.tai_lieu_id "
                  "WHERE nd.kieu IN ('ma_nguon','khac') AND nd.so_ky_tu > 400")
    nhan, thu, n = 0, 0, 0
    for r in rs:
        if time.time() > han:
            break
        n += 1
        try:
            ds = DM.doc_ma(r["van_ban"] or "", nguon=r["url"] or "",
                           tien_to=DM.re.sub(r"[^a-z0-9]+", "_",
                                             (r["tieu_de"] or "kho").lower())[:20] or "kho")
        except Exception:
            continue
        for spec in ds:
            thu += 1
            try:
                if NP.them_co_che(dict(spec), df).get("nhan"):
                    nhan += 1
            except Exception:
                continue
    bao.update({"kho_ban_doc_quet": n, "kho_khai_bao_thu": thu,
                "kho_co_che_nhan": nhan})
    _log(f, f"  [doc ma kho] quet {n} ban doc · {thu} khai bao · **{nhan} nhan**")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phut", type=float, default=60)
    a = ap.parse_args()
    het = time.time() + a.phut * 60
    bao: dict = {"bat_dau": time.strftime("%Y-%m-%d %H:%M:%S"), "phut": a.phut}
    nk = LAB / "reports" / "LO_MOT_GIO.log"
    nk.parent.mkdir(parents=True, exist_ok=True)
    with nk.open("a", encoding="utf-8") as f:
        _log(f, f"=== LO MOT GIO bat dau, han {a.phut:.0f} phut ===")
        from nhan import ngu_phap as NP
        bao["co_che_truoc"] = len(NP.doc_kho())
        for ten, ham, phan in (("PINE", phase_pine, 0.55),
                               ("THU HOI", phase_thu_hoi, 0.75),
                               ("DOC MA KHO", phase_doc_ma_kho, 1.0)):
            if time.time() >= het:
                break
            _log(f, f"--- {ten} ---")
            moc = time.time() + (het - time.time()) * (
                phan if phan < 1 else 1.0)
            try:
                ham(f, min(moc, het), bao)
            except Exception as e:
                _log(f, f"  [{ten}] NEM: {type(e).__name__}: {str(e)[:120]}")
        bao["co_che_sau"] = len(NP.doc_kho())
        bao["xong"] = time.strftime("%Y-%m-%d %H:%M:%S")
        _log(f, f"=== XONG. Thu vien co che: {bao['co_che_truoc']} -> "
                f"{bao['co_che_sau']} ===")
    RA_JSON.write_text(json.dumps(bao, ensure_ascii=False, indent=1),
                       encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
