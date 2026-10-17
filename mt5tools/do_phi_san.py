# -*- coding: utf-8 -*-
"""do_phi_san.py - DO PHI THAT tren DUNG tai khoan chu du an dang dang nhap (Exness cent, XM micro, hay bat ky san MT5 nao).
Tong quat hoa mt5tools/phi_xm.py (17/10/2026). Khong dung mat khau: gan vao terminal DANG dang nhap.

Do nhung thu can cho cach danh cua chu du an (khong SL, TP nho 5-6 gia, DCA, gong, hedge):
- tai khoan: tien te (USC = cent), don bay, margin_mode (hedging hay netting), muc margin call / stop out
- moi ma: lot min/buoc, hop dong, TIEN MOI 1 GIA o lot min, margin lot min, margin_hedged (hedge co mat margin khong),
  stops_level/freeze_level (dat TP sat gia duoc khong), swap mua/ban RA TIEN moi dem o lot min, ngay x3
- spread theo GIO tu tick that (p50/p90/p99), gian luc doi ngay (23h-01h server) so voi trung vi, spread gio dau tuan
- khoang trong cuoi tuan (gap thu Sau -> thu Hai) tu bar H1 - quan trong khi gong lenh khong SL
- spread so voi TP: spread_gia / tp_gia (mac dinh 5 gia)
- LICH SU LENH THAT cua tai khoan (neu co): hoa hong/lot/chieu, swap da tra, thoi gian giu, ti le dong lai -> cach anh xu li lenh
CHUA do: gian luc tin (NFP/CPI) - API Python khong co lich kinh te; xem p99 theo gio.

Chay (may nha, Windows, terminal da dang nhap):
  python mt5tools/do_phi_san.py "C:\\...\\terminal64.exe" [--ra reports/phi_san] [--ngay-tick 14] [--tp-gia 5] [--ngay-lich-su 365]
Ra: reports/phi_san/<server>/{tai_khoan.json, ma.csv, spread_gio.csv, ma_san.json, lich_su_tom_tat.csv, lenh_cua_anh.csv}
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

TIEN_TE = {"USD", "EUR", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD", "SEK", "NOK", "DKK", "PLN", "HUF", "CZK", "TRY", "ZAR",
           "MXN", "SGD", "HKD", "CNH", "XAU", "XAG", "XPT", "XPD"}
# ten goc -> cac ten san hay dung (da bo ky tu khong phai chu/so, viet hoa)
BI_DANH = {
    "US500": ["US500", "SPX500", "SP500", "USA500", "US500CASH"], "US100": ["US100", "USTEC", "NAS100", "NSDQ100", "US100CASH"],
    "US30": ["US30", "DJ30", "WS30", "US30CASH"], "GER40": ["GER40", "DE40", "DE30", "GER30", "DAX40", "GER40CASH"],
    "UK100": ["UK100", "FTSE100", "UK100CASH"], "JP225": ["JP225", "JPN225", "NI225", "JP225CASH"],
    "FRA40": ["FRA40", "FR40", "F40", "FRA40CASH"], "EU50": ["EU50", "STOXX50", "EUSTX50", "EU50CASH"],
    "XAUUSD": ["XAUUSD", "GOLD"], "XAGUSD": ["XAGUSD", "SILVER"], "USOIL": ["USOIL", "XTIUSD", "WTI", "OIL", "OILCASH", "CL"],
    "UKOIL": ["UKOIL", "XBRUSD", "BRENT", "BRENTCASH"], "BTCUSD": ["BTCUSD", "BITCOIN"],
}
_NGUOC = {b: g for g, ds in BI_DANH.items() for b in ds}
HAU_TO = ["MICRO", "CASH", "MINI", "PRO", "ECN", "RAW", "STD", "ZERO", "I", "C", "M", "Z", "X", "P", "R", "E"]
SWAP_MODE = {0: "DISABLED", 1: "POINTS", 2: "BASE_CCY", 3: "MARGIN_CCY", 4: "DEPOSIT_CCY", 5: "INTEREST_CURRENT",
             6: "INTEREST_OPEN", 7: "REOPEN_CURRENT", 8: "REOPEN_BID"}
MARGIN_MODE = {0: "RETAIL_NETTING", 1: "EXCHANGE", 2: "RETAIL_HEDGING"}
LY_DO_DONG = {0: "tay_may_tinh", 1: "dien_thoai", 2: "web", 3: "EA", 4: "SL", 5: "TP", 6: "STOP_OUT", 7: "rollover", 8: "vmargin", 9: "split"}
THU = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]


def _la_fx(u: str) -> bool:
    return len(u) == 6 and u[:3] in TIEN_TE and u[3:] in TIEN_TE


def ten_goc(sym: str) -> str | None:
    """'EURUSDc' -> 'EURUSD', 'GOLD.i#' -> 'XAUUSD', 'US500Cash#' -> 'US500', 'USTECm' -> 'US100'. Khong nhan ra -> None."""
    u = re.sub(r"[^A-Z0-9]", "", sym.upper())
    for _ in range(3):
        if _la_fx(u):
            return u
        if u in _NGUOC:
            return _NGUOC[u]
        for h in HAU_TO:
            if u.endswith(h) and len(u) > len(h) and (_la_fx(u[:-len(h)]) or u[:-len(h)] in _NGUOC or u[:-len(h)].endswith(tuple(HAU_TO))):
                u = u[:-len(h)]
                break
        else:
            return None
    return u if (_la_fx(u) or u in _NGUOC) else None


def tien_moi_gia(tick_value: float, tick_size: float, lot: float) -> float | None:
    """Tien (tien te tai khoan) khi gia chay 1,0 don vi gia voi `lot` lot."""
    return lot * tick_value / tick_size if tick_size else None


def swap_tien_dem(mode: int, swap: float, lot: float, point: float, tick_value: float, tick_size: float, gia: float) -> float | None:
    """Swap RA TIEN tien te tai khoan cho 1 dem o `lot` lot. None = khong quy doi duoc (doc lich su lenh that)."""
    if mode == 0:
        return 0.0
    tg = tien_moi_gia(tick_value, tick_size, 1.0)
    if tg is None:
        return None
    if mode in (1, 7, 8):        # diem
        return swap * point * tg * lot
    if mode == 4:                # tien te tai khoan, moi lot
        return swap * lot
    if mode in (5, 6):           # lai suat %/nam tren gia tri hop dong
        return gia * tg * lot * swap / 100.0 / 360.0
    return None                  # 2/3 (tien co so/margin) va mode la (vd 9 cua FXCE)


def phan_vi(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    s = sorted(xs); k = (len(s) - 1) * q; i = int(k)
    return s[i] if i + 1 >= len(s) else s[i] + (s[i + 1] - s[i]) * (k - i)


def _tg(x: float) -> datetime:
    """Thoi gian MT5 (gio SERVER ma hoa nhu UTC) -> datetime gio server."""
    return datetime.fromtimestamp(int(x), timezone.utc).replace(tzinfo=None)


def spread_theo_gio(gio, spread_gia) -> dict:
    """{gio: (n, p50, p90, p99)} tu tick (gio server, spread theo don vi gia). Nhan list hoac mang numpy."""
    import numpy as np
    gio = np.asarray(gio, dtype=int); sp = np.asarray(spread_gia, dtype=float); out = {}
    for h in np.unique(gio):
        v = sp[gio == h]
        out[int(h)] = (int(len(v)), *(float(x) for x in np.quantile(v, [.5, .9, .99])))
    return out


def gian_doi_ngay(bang: dict, gio_doi=(23, 0, 1)) -> float | None:
    """Ti le p90 spread quanh gio doi ngay / trung vi p50 ca ngay. > 3 = khong vao/chot lenh gio do."""
    p50 = [v[1] for v in bang.values() if v[1]]
    goc = phan_vi(p50, .5)
    quanh = [bang[h][2] for h in gio_doi if h in bang and bang[h][2]]
    return round(max(quanh) / goc, 2) if goc and quanh else None


def gap_cuoi_tuan(thoi_gian: list[int], mo: list[float], dong: list[float], gio_trong: float = 40.0) -> list[float]:
    """|mo dau tuan - dong cuoi tuan truoc| (don vi gia) moi lan bar H1 cach nhau > gio_trong gio."""
    out = []
    for i in range(1, len(thoi_gian)):
        if (thoi_gian[i] - thoi_gian[i - 1]) / 3600.0 > gio_trong:
            out.append(abs(mo[i] - dong[i - 1]))
    return out


def tom_tat_lich_su(deals: list[dict]) -> tuple[list[dict], list[dict]]:
    """deals: dict co time, type(0 mua/1 ban), entry(0 vao/1 ra/2 dao/3 out_by), volume, price, commission, swap, fee, profit,
    symbol, position_id, reason. Tra (tom_tat moi ma, lenh moi vi the)."""
    vt: dict[int, dict] = {}
    for d in sorted(deals, key=lambda x: x["time"]):
        if d.get("type") not in (0, 1) or not d.get("symbol"):
            continue
        p = vt.setdefault(d["position_id"], {"symbol": d["symbol"], "chieu": None, "lot": 0.0, "mo": None, "dong": None,
                                             "loi": 0.0, "swap": 0.0, "hoa_hong": 0.0, "phi": 0.0, "ly_do_dong": None, "so_lan_vao": 0})
        if d.get("entry") == 0:
            p["chieu"] = p["chieu"] or ("mua" if d["type"] == 0 else "ban"); p["lot"] += d["volume"]; p["so_lan_vao"] += 1
            if p["mo"] is None:
                p["mo"] = d["time"]
        else:
            p["dong"] = d["time"]; p["ly_do_dong"] = LY_DO_DONG.get(d.get("reason"), d.get("reason"))
        p["loi"] += d.get("profit", 0.0); p["swap"] += d.get("swap", 0.0); p["hoa_hong"] += d.get("commission", 0.0); p["phi"] += d.get("fee", 0.0)
    lenh = []
    for pid, p in vt.items():
        if p["mo"] is None:
            continue
        gio = round((p["dong"] - p["mo"]) / 3600.0, 2) if p["dong"] else None
        lenh.append({"vi_the": pid, **{k: p[k] for k in ("symbol", "chieu", "so_lan_vao")}, "lot": round(p["lot"], 4),
                     "mo": _tg(p["mo"]).strftime("%Y-%m-%d %H:%M"),
                     "dong": _tg(p["dong"]).strftime("%Y-%m-%d %H:%M") if p["dong"] else "",
                     "gio_giu": gio, "loi": round(p["loi"], 2), "swap": round(p["swap"], 2), "hoa_hong": round(p["hoa_hong"], 2),
                     "phi": round(p["phi"], 2), "rong": round(p["loi"] + p["swap"] + p["hoa_hong"] + p["phi"], 2), "ly_do_dong": p["ly_do_dong"]})
    tom = []
    for sym in sorted({x["symbol"] for x in lenh}):
        ds = [x for x in lenh if x["symbol"] == sym]; dong = [x for x in ds if x["dong"]]
        lot = sum(x["lot"] for x in ds)
        tom.append({"symbol": sym, "so_vi_the": len(ds), "da_dong": len(dong), "lot_tong": round(lot, 4),
                    "hoa_hong_moi_lot_chieu": round(sum(x["hoa_hong"] for x in ds) / lot / 2, 4) if lot else None,
                    "swap_tong": round(sum(x["swap"] for x in ds), 2), "rong_tong": round(sum(x["rong"] for x in ds), 2),
                    "ti_le_dong_loi": round(sum(x["rong"] > 0 for x in dong) / len(dong), 3) if dong else None,
                    "gio_giu_trung_vi": phan_vi([x["gio_giu"] for x in dong], .5),
                    "gio_giu_p90": phan_vi([x["gio_giu"] for x in dong], .9),
                    "lo_lon_nhat": min((x["rong"] for x in dong), default=None),
                    "dong_boi": json.dumps({k: sum(x["ly_do_dong"] == k for x in dong) for k in {x["ly_do_dong"] for x in dong}}, ensure_ascii=False)})
    return tom, lenh


def _ghi_csv(p: Path, rows: list[dict]) -> None:
    if not rows:
        return
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("terminal"); ap.add_argument("--ra", default="reports/phi_san")
    ap.add_argument("--ngay-tick", type=int, default=14); ap.add_argument("--tp-gia", type=float, default=5.0)
    ap.add_argument("--ngay-lich-su", type=int, default=365); ap.add_argument("--chi", default="", help="chi do cac ten goc nay, phay")
    a = ap.parse_args()
    import MetaTrader5 as mt5  # chi co tren Windows
    import numpy as np
    assert mt5.initialize(path=a.terminal), mt5.last_error()
    ai = mt5.account_info()
    ra = Path(a.ra) / re.sub(r"[^A-Za-z0-9._-]", "_", ai.server); ra.mkdir(parents=True, exist_ok=True)
    tk = {"server": ai.server, "company": ai.company, "tien_te": ai.currency, "don_bay": ai.leverage,
          "trade_mode": {0: "DEMO", 1: "CONTEST", 2: "REAL"}.get(ai.trade_mode, ai.trade_mode),
          "margin_mode": MARGIN_MODE.get(ai.margin_mode, ai.margin_mode), "so_mode": "PERCENT" if ai.margin_so_mode == 0 else "MONEY",
          "margin_call": ai.margin_so_call, "stop_out": ai.margin_so_so, "lenh_cho_toi_da": ai.limit_orders,
          "do_luc": datetime.now().isoformat(timespec="seconds"), "ghi_chu": "tien te USC = tai khoan CENT (1 USD = 100 USC)"}
    (ra / "tai_khoan.json").write_text(json.dumps(tk, ensure_ascii=False, indent=1), encoding="utf-8")
    print("TAI KHOAN", json.dumps(tk, ensure_ascii=False))
    chi = {x.strip().upper() for x in a.chi.split(",") if x.strip()}
    ma_san: dict[str, list[str]] = {}
    for s in mt5.symbols_get():
        g = ten_goc(s.name)
        if g and (not chi or g in chi):
            ma_san.setdefault(g, []).append(s.name)
    rows, gio_rows, chon = [], [], {}
    for g, ds in sorted(ma_san.items()):
        for name in ds:
            mt5.symbol_select(name, True)
        infos = [i for i in (mt5.symbol_info(n) for n in ds) if i is not None]
        if not infos:
            continue
        i = sorted(infos, key=lambda z: (z.trade_mode != 4, -z.time))[0]   # uu tien ma giao dich day du, co tick moi nhat
        chon[g] = {"symbol": i.name, "cac_ten": ds, "lot_min": i.volume_min, "buoc_lot": i.volume_step, "chu_so": i.digits,
                   "tien_moi_gia_1lot": tien_moi_gia(i.trade_tick_value, i.trade_tick_size, 1.0)}
        gia = (i.bid + i.ask) / 2 if i.bid else None
        tg = tien_moi_gia(i.trade_tick_value, i.trade_tick_size, i.volume_min)
        r = {"goc": g, "symbol": i.name, "trade_mode": i.trade_mode, "chu_so": i.digits, "point": i.point, "hop_dong": i.trade_contract_size,
             "lot_min": i.volume_min, "buoc_lot": i.volume_step, "lot_max": i.volume_max,
             "tien_moi_1_gia_lot_min": round(tg, 6) if tg else None,
             "tien_TP_lot_min": round(tg * a.tp_gia, 4) if tg else None,
             "stops_level_gia": i.trade_stops_level * i.point, "freeze_level_gia": i.trade_freeze_level * i.point,
             "swap_mode": SWAP_MODE.get(i.swap_mode, i.swap_mode), "swap_mua": i.swap_long, "swap_ban": i.swap_short,
             "ngay_x3": THU[(i.swap_rollover3days - 1) % 7] if 0 <= i.swap_rollover3days < 7 else i.swap_rollover3days,
             "tien_te_loi": i.currency_profit, "tien_te_margin": i.currency_margin, "margin_hedged": i.margin_hedged,
             "gia": gia, "spread_gia_luc_do": round(i.ask - i.bid, 6) if i.bid else None}
        for chieu, sw in (("mua", i.swap_long), ("ban", i.swap_short)):
            v = swap_tien_dem(i.swap_mode, sw, i.volume_min, i.point, i.trade_tick_value, i.trade_tick_size, gia or 0.0)
            r["swap_tien_dem_%s_lot_min" % chieu] = round(v, 6) if v is not None else None
        try:
            r["margin_lot_min"] = mt5.order_calc_margin(mt5.ORDER_TYPE_BUY, i.name, i.volume_min, i.ask)
        except Exception:
            r["margin_lot_min"] = None
        t = mt5.copy_ticks_range(i.name, datetime.now() - timedelta(days=a.ngay_tick), datetime.now() + timedelta(days=1), mt5.COPY_TICKS_INFO)
        if t is not None and len(t):
            m = (t["ask"] > 0) & (t["bid"] > 0)
            tt = t["time"][m].astype(np.int64); sp = (t["ask"] - t["bid"])[m].astype(float)
            if len(sp):
                gio = (tt // 3600) % 24; thu = ((tt // 86400) + 3) % 7     # 01/01/1970 la thu Nam -> T2 = 0
                bang = spread_theo_gio(gio, sp)
                for h, (n, p50, p90, p99) in bang.items():
                    gio_rows.append({"goc": g, "symbol": i.name, "gio_server": h, "n_tick": n, "p50_gia": p50, "p90_gia": p90, "p99_gia": p99})
                q50, q90, q99 = (float(x) for x in np.quantile(sp, [.5, .9, .99]))
                r.update(tick_n=int(len(sp)), tick_tu=_tg(tt[0]).strftime("%Y-%m-%d"),
                         spread_p50_gia=q50, spread_p90_gia=q90, spread_p99_gia=q99, gian_doi_ngay_x=gian_doi_ngay(bang))
                if gia and q50:
                    r["spread_p50_bps"] = round(q50 / gia * 1e4, 3)
                r["spread_chiem_TP_pct"] = round(100 * q50 / a.tp_gia, 2)
                dau = (thu == 0) & (gio <= 1)
                if dau.any():
                    r["spread_p90_gia_dau_tuan"] = float(np.quantile(sp[dau], .9))
        b = mt5.copy_rates_from_pos(i.name, mt5.TIMEFRAME_H1, 0, 60000)
        if b is not None and len(b):
            r["H1_tu"] = _tg(b[0]["time"]).strftime("%Y-%m-%d")
            gp = gap_cuoi_tuan([int(x) for x in b["time"]], [float(x) for x in b["open"]], [float(x) for x in b["close"]])
            if gp:
                r.update(gap_cuoi_tuan_p50_gia=phan_vi(gp, .5), gap_cuoi_tuan_p90_gia=phan_vi(gp, .9), gap_cuoi_tuan_max_gia=max(gp), so_cuoi_tuan=len(gp))
            sb = [float(x) * i.point for x in b["spread"][-24 * 250:] if x > 0]
            r["H1_spread_bar_p50_gia_1nam"] = phan_vi(sb, .5)
        rows.append(r); print("ok", g, i.name, r.get("spread_p50_gia"), r.get("gian_doi_ngay_x"), r.get("swap_mode"), flush=True)
    _ghi_csv(ra / "ma.csv", rows); _ghi_csv(ra / "spread_gio.csv", gio_rows)
    (ra / "ma_san.json").write_text(json.dumps({"server": ai.server, "tien_te": ai.currency, "ma": chon}, ensure_ascii=False, indent=1), encoding="utf-8")
    ds = mt5.history_deals_get(datetime.now() - timedelta(days=a.ngay_lich_su), datetime.now() + timedelta(days=1))
    if ds:
        deals = [{k: getattr(d, k) for k in ("time", "type", "entry", "volume", "price", "commission", "swap", "fee", "profit", "symbol", "position_id", "reason")} for d in ds]
        tom, lenh = tom_tat_lich_su(deals)
        _ghi_csv(ra / "lich_su_tom_tat.csv", tom); _ghi_csv(ra / "lenh_cua_anh.csv", lenh)
        print("LICH SU: %d deal, %d vi the" % (len(deals), len(lenh)))
    else:
        print("LICH SU: khong co lenh trong %d ngay (hoa hong that = CHUA_DO_DUOC tren tai khoan nay)" % a.ngay_lich_su)
    mt5.shutdown()
    print("XONG ->", ra)


if __name__ == "__main__":
    sys.exit(main())
