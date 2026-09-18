# -*- coding: utf-8 -*-
"""
brain_chi_phi.py - DO CHI PHI THAT THEO SAN (viec uu tien 100 cua brain_vong_lap.py)
=====================================================================================
VI SAO DAY LA VIEC DAU TIEN, TRUOC MOI THU KHAC:

  Day KHONG phai gia thuyet, no la PHEP TRU. Khong can du doan gi, khong ton mot slot
  ngan sach thong ke nao, va no ra tien ngay tren moi vi the dai dang giu.

  Da phat hien tu truoc ma CHUA TIEU: XM futures CFD co swap = 0, mua-giu re hon cash
  CFD 1,2-2,7%/nam. Do la tien tu do tren moi vi the dai, khong doi lay rui ro nao.

  Va chuan so 8 cua du an: "phi qua dem la thu quyet dinh, khong phai spread". Do dung
  no la viec co gia tri cao nhat tren moi don vi cong bo ra.

=====================================================================================
BAY DA SAP - MA HOA HET VAO DAY DE KHONG SAP LAI
=====================================================================================
 1. KIEM LOAI TAI KHOAN TRUOC (chuan 20). So lot chi dung tren tai khoan MICRO.
    - XM     : kiem bang `EURUSD.trade_contract_size` (1.000 = Micro, 100.000 = chuan)
    - Exness : kiem bang `account_info().currency` (USC = cent). contract_size KHONG doi.
    Dat 4,4 lot tren von 200 USD o tai khoan chuan = don bay 547x thay vi 5,52x.

 2. KHONG mo hinh phi qua dem bang `swap_tuyet_doi * 365 / gia` (chuan 14). Do la bay
    da tu mac lai ngay 28/07 (ra 38,8%/nam cho nam 2011). Swap tuyet doi thi %/nam GIAM
    khi gia tang -> phai neo vao GIA HIEN TAI va noi ro dieu do.

 3. Bar D1 cua XM co `spread = 0` toan bo. Chi H1/M1 moi co spread THAT (chuan 46).
    Exness thi M5 co. -> doc spread tu bar H1, khong doc tu D1.

 4. Spread doc tu `symbol_info_tick` vao CUOI TUAN bi thoi 2-6 lan (chuan 47).
    NZDCAD tick 22,9 pip nhung that 3,9. -> canh bao neu chay ngoai gio giao dich.

 5. Lan goi `copy_rates_*` DAU sau `symbol_select` tra THIEU bar, khong bao loi (chuan 45).
    -> thu lai 4 lan x 1,5 giay.

 6. XM phai dung `copy_rates_from_pos`, KHONG phai `copy_rates_range` (chuan 46).

CLI:
  python brain_chi_phi.py                    # do tat ca symbol quan tam
  python brain_chi_phi.py --symbol US500Cash
  python brain_chi_phi.py --lop              # so sanh cash vs futures cung tai san co so
"""
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
REPORTS = HERE / "reports"
REPORTS.mkdir(exist_ok=True)
RA_MD = REPORTS / "BRAIN_CHI_PHI.md"

# Cac lop cong cu cho CUNG mot tai san co so. Day la cho tien nam: cung phoi nhiem
# kinh te nhung phi giu khac han nhau.
LOP_CUNG_TAI_SAN = {
    "SP500":  ["US500Cash", "US500", "SP500", "US500m", "USTEC100Cash"],
    "VANG":   ["GOLD", "XAUUSD", "XAUUSDm", "GOLDbrent"],
    "DAU":    ["OILCash", "USOIL", "WTI", "XTIUSD"],
    "DAX":    ["GER40Cash", "DE40", "GER30"],
    "NASDAQ": ["US100Cash", "NAS100", "USTEC"],
}

# Ten enum swap cua MT5 - cach tinh khac han nhau, doc nham la sai het
TEN_SWAP_MODE = {
    0: "TAT (khong thu swap)",
    1: "DIEM (points)",
    2: "TIEN te cua symbol",
    3: "TIEN te ky quy",
    4: "TIEN te tai khoan",
    5: "LAI SUAT theo gia hien tai (%/nam)",
    6: "LAI SUAT theo gia mo (%/nam)",
    7: "mo lai theo gia hien tai",
    8: "mo lai theo gia bid",
}
THU = {0: "CN", 1: "T2", 2: "T3", 3: "T4", 4: "T5", 5: "T6", 6: "T7"}


# Moi SAN mot terminal rieng. BAT BUOC tro dung duong dan, neu khong ca 4 viec deu do
# CUNG MOT terminal va ban do chi phi giua cac san khong thanh (da mac dung loi nay).
# mt5.initialize() khong tham so = bam vao terminal nao dang chay -> vo dung o day.
TERMINAL = {
    "XM":        r"C:\Program Files\XM MT5\terminal64.exe",
    "Exness":    r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
    "Ultima":    r"C:\Program Files\Ultima Markets MT5 Terminal\terminal64.exe",
    "FXCE":      r"C:\Program Files\FXCE MT5 Terminal\terminal64.exe",
    "MetaQuotes": r"C:\Program Files\MetaTrader 5\terminal64.exe",
}


def _mt5(san=None):
    """Ket noi terminal CUA DUNG SAN do. Tai khoan phai da luu dang nhap san trong terminal."""
    try:
        import MetaTrader5 as mt5
    except ImportError:
        return None, "chua cai MetaTrader5: pip install MetaTrader5"

    duong_dan = TERMINAL.get(san)
    if duong_dan and Path(duong_dan).exists():
        ok = mt5.initialize(path=duong_dan, timeout=60_000)
    elif duong_dan:
        return None, f"khong thay terminal cua {san}: {duong_dan}"
    else:
        ok = mt5.initialize()          # khong chi dinh san -> terminal nao cung duoc

    if not ok:
        return None, f"khong ket noi duoc terminal {san or ''}: {mt5.last_error()}"
    return mt5, None


def kiem_loai_tai_khoan(mt5):
    """CHUAN 20: kiem loai tai khoan TRUOC moi phep do. Moi san kiem mot kieu."""
    tk = mt5.account_info()
    if tk is None:
        return {"loi": "khong doc duoc account_info"}

    ra = {"dang_nhap": tk.login, "may_chu": tk.server, "don_vi": tk.currency,
          "don_bay": tk.leverage, "so_du": tk.balance, "cong_ty": tk.company}

    # Exness: cent nhan biet bang currency = USC (contract_size KHONG doi)
    ra["la_cent"] = str(tk.currency).upper() in ("USC", "USDC", "EURC")

    # XM: micro nhan biet bang EURUSD contract size
    si = mt5.symbol_info("EURUSD") or mt5.symbol_info("EURUSDm")
    if si:
        ra["eurusd_contract"] = si.trade_contract_size
        ra["la_micro"] = si.trade_contract_size <= 10_000
    else:
        ra["eurusd_contract"] = None
        ra["la_micro"] = None

    ra["loai"] = ("CENT" if ra["la_cent"] else
                  "MICRO" if ra["la_micro"] else
                  "CHUAN" if ra["la_micro"] is False else "KHONG RO")
    return ra


def _bar_h1(mt5, ten, so=500):
    """CHUAN 45+46: lan goi dau sau symbol_select tra thieu bar -> thu lai.
    Va phai dung from_pos, khong dung range."""
    mt5.symbol_select(ten, True)
    for lan in range(4):
        bars = mt5.copy_rates_from_pos(ten, mt5.TIMEFRAME_H1, 0, so)
        if bars is not None and len(bars) >= min(50, so // 4):
            return pd.DataFrame(bars)
        time.sleep(1.5)
    return None


def do_mot_symbol(mt5, ten, tk):
    """Do day du chi phi giu vi the cua 1 symbol. Tra ve dict hoac None."""
    si = mt5.symbol_info(ten)
    if si is None:
        return None
    if not si.visible:
        mt5.symbol_select(ten, True)
        si = mt5.symbol_info(ten)

    tick = mt5.symbol_info_tick(ten)
    gia = (tick.bid if tick and tick.bid else si.bid) or 0.0
    if not gia:
        return None

    # --- spread THAT tu bar H1 (chuan 3: D1 cua XM co spread = 0) ---
    bars = _bar_h1(mt5, ten)
    spread_bar = np.nan
    if bars is not None and "spread" in bars:
        s = bars["spread"].to_numpy(float)
        s = s[s > 0]
        spread_bar = float(np.median(s)) if len(s) else np.nan

    spread_tick = (tick.ask - tick.bid) / si.point if tick and si.point else np.nan
    # dung spread tu BAR neu co; tick chi de doi chieu (chuan 4: cuoi tuan tick bi thoi)
    spread_diem = spread_bar if spread_bar == spread_bar else spread_tick
    spread_bps = spread_diem * si.point / gia * 1e4 if gia else np.nan

    # --- swap ---
    mode = si.swap_mode
    sl, ss = si.swap_long, si.swap_short
    hop_dong = si.trade_contract_size
    gia_tri_1lot = gia * hop_dong

    # Quy doi ve %/nam. CHUAN 14: KHONG dung cong thuc tuyet_doi*365/gia mot cach mu quang;
    # phai neo vao gia HIEN TAI va noi ro con so nay TROI khi gia doi.
    if mode == 0:
        sw_long_nam = sw_short_nam = 0.0
        cach = "swap TAT"
    elif mode in (5, 6):
        sw_long_nam, sw_short_nam = float(sl), float(ss)     # da la %/nam san
        cach = "san khai bao thang %/nam"
    elif mode == 1:
        # diem/dem -> tien/dem = diem * point * contract
        sw_long_nam = sl * si.point * hop_dong * 365 / gia_tri_1lot * 100 if gia_tri_1lot else np.nan
        sw_short_nam = ss * si.point * hop_dong * 365 / gia_tri_1lot * 100 if gia_tri_1lot else np.nan
        cach = "diem/dem -> %/nam theo GIA HIEN TAI"
    else:
        # tien tuyet doi / lot / dem
        sw_long_nam = sl * 365 / gia_tri_1lot * 100 if gia_tri_1lot else np.nan
        sw_short_nam = ss * 365 / gia_tri_1lot * 100 if gia_tri_1lot else np.nan
        cach = "tien tuyet doi/dem -> %/nam theo GIA HIEN TAI"

    return {
        "symbol": ten, "gia": gia, "hop_dong": hop_dong, "gia_tri_1lot": gia_tri_1lot,
        "spread_diem": spread_diem, "spread_bps": spread_bps,
        "spread_tu_bar": spread_bar == spread_bar,
        "spread_tick_doi_chieu": spread_tick,
        "swap_mode": mode, "swap_mode_ten": TEN_SWAP_MODE.get(mode, str(mode)),
        "swap_long_tho": sl, "swap_short_tho": ss,
        "swap_long_pct_nam": sw_long_nam, "swap_short_pct_nam": sw_short_nam,
        "cach_quy_doi": cach,
        "ngay_x3": THU.get(si.swap_rollover3days, "?"),
        "phi_giu_dai_pct_nam": -sw_long_nam if sw_long_nam == sw_long_nam else np.nan,
    }


def do_chi_phi(muc_tieu="tat_ca", tham_so=None):
    """Giao dien ma brain_vong_lap.py goi.

    `muc_tieu` la TEN SAN (XM/Exness/Ultima/FXCE) -> tro dung terminal cua san do.
    Neu la 'cash_vs_futures' hoac ten symbol thi dung terminal dang chay.
    """
    san = muc_tieu if muc_tieu in TERMINAL else None
    mt5, loi = _mt5(san)
    if mt5 is None:
        print(f"  [chi_phi] {loi}")
        return []

    try:
        tk = kiem_loai_tai_khoan(mt5)
        print(f"  [chi_phi] tai khoan {tk.get('dang_nhap')} @ {tk.get('may_chu')} "
              f"| {tk.get('don_vi')} | loai {tk.get('loai')}")
        if tk.get("loai") == "KHONG RO":
            print("    !!! chua xac dinh duoc loai tai khoan - CHUA duoc dat lenh that")

        ten_ss = [s.name for s in (mt5.symbols_get() or [])]
        if not ten_ss:
            print("  [chi_phi] terminal khong tra ve symbol nao")
            return []

        # chon symbol can do
        if san or muc_tieu == "cash_vs_futures":
            can = [t for ds in LOP_CUNG_TAI_SAN.values() for t in ds if t in ten_ss]
        elif muc_tieu in ten_ss:
            can = [muc_tieu]
        else:
            uu_tien = [t for ds in LOP_CUNG_TAI_SAN.values() for t in ds if t in ten_ss]
            pho_bien = [t for t in ("EURUSD", "XAUUSD", "GBPUSD", "USDJPY", "EURCAD")
                        if t in ten_ss]
            can = uu_tien + pho_bien
            if not can:
                can = ten_ss[:25]     # san la -> lay dai dien

        print(f"  [chi_phi] do {len(can)} symbol...")
        hang = []
        for t in can:
            try:
                d = do_mot_symbol(mt5, t, tk)
            except Exception as e:
                print(f"    {t}: loi {str(e)[:60]}")
                continue
            if not d:
                continue
            hang.append({
                "nguon": f"chi_phi/{tk.get('cong_ty', muc_tieu)}",
                "khoa": f"{tk.get('may_chu')}:{t}:{datetime.now():%Y-%m}",
                "ten": t, "loai": "chi_phi",
                "ngay": datetime.now().date().isoformat(),
                "tac_gia": str(tk.get("may_chu")),
                "tom_tat": (f"spread {d['spread_bps']:.2f} bps | "
                            f"giu dai {d['phi_giu_dai_pct_nam']:+.2f}%/nam | "
                            f"{d['swap_mode_ten']} | x3 {d['ngay_x3']}"),
                **{k: v for k, v in d.items() if k != "symbol"},
                "tk_loai": tk.get("loai"), "tk_don_vi": tk.get("don_vi"),
            })
            print(f"    {t:14} spread {d['spread_bps']:6.2f} bps | "
                  f"giu dai {d['phi_giu_dai_pct_nam']:+7.2f}%/nam | {d['swap_mode_ten']}")

        if hang:
            viet_bao_cao(pd.DataFrame(hang), tk)
        return hang
    finally:
        mt5.shutdown()


def viet_bao_cao(df, tk):
    """Bang xep hang: cung phoi nhiem, lop nao re nhat."""
    md = ["# THE BRAIN - ban do chi phi giu vi the", "",
          f"*Do luc {datetime.now():%Y-%m-%d %H:%M} tren {tk.get('may_chu')} "
          f"({tk.get('cong_ty')}), tai khoan loai **{tk.get('loai')}**, don vi {tk.get('don_vi')}.*", "",
          "> **Day khong phai gia thuyet, day la phep tru.** Khong ton slot ngan sach thong ke nao.",
          "> Chuan so 8: *phi qua dem la chi phi quyet dinh, khong phai spread.*", "",
          "> **Canh bao doc so:** cot `%/nam` neo vao GIA HIEN TAI. Voi san thu swap bang so",
          "> TUYET DOI (mode 2/3/4), ty le nay GIAM khi gia tang - dung ap cho ca lich su.", ""]

    if "phi_giu_dai_pct_nam" in df:
        x = df.sort_values("phi_giu_dai_pct_nam")
        md += ["## Xep hang: giu vi the DAI re nhat truoc", "",
               "| symbol | spread (bps) | phi giu dai (%/nam) | kieu thu swap | ngay x3 |",
               "|---|---|---|---|---|"]
        for _, r in x.iterrows():
            md.append(f"| `{r['ten']}` | {r.get('spread_bps', float('nan')):.2f} | "
                      f"**{r.get('phi_giu_dai_pct_nam', float('nan')):+.2f}** | "
                      f"{r.get('swap_mode_ten','')} | {r.get('ngay_x3','')} |")
        md.append("")

        # cung tai san co so -> chenh lech giua cac lop la TIEN TU DO
        md += ["## Cung tai san co so: chenh lech giua cac lop", "",
               "> Day la cho tien nam. Cung phoi nhiem kinh te, phi giu khac han nhau.", ""]
        co = False
        for nhom, ds in LOP_CUNG_TAI_SAN.items():
            con = df[df["ten"].isin(ds)]
            if len(con) < 2:
                continue
            co = True
            re = con.loc[con["phi_giu_dai_pct_nam"].idxmin()]
            dat = con.loc[con["phi_giu_dai_pct_nam"].idxmax()]
            md += [f"### {nhom}", "",
                   f"- re nhat : `{re['ten']}` {re['phi_giu_dai_pct_nam']:+.2f}%/nam",
                   f"- dat nhat: `{dat['ten']}` {dat['phi_giu_dai_pct_nam']:+.2f}%/nam",
                   f"- **chenh lech: {abs(dat['phi_giu_dai_pct_nam'] - re['phi_giu_dai_pct_nam']):.2f}%/nam**", ""]
        if not co:
            md += ["*(terminal nay khong co du 2 lop cua cung mot tai san co so de so sanh)*", ""]

    RA_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"  -> {RA_MD}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default=None)
    ap.add_argument("--san", default=None, choices=list(TERMINAL),
                    help="do tren terminal cua dung san nay")
    ap.add_argument("--tat-ca-san", action="store_true",
                    help="chay lan luot qua MOI san co terminal tren may")
    ap.add_argument("--lop", action="store_true", help="so sanh cash vs futures")
    a = ap.parse_args()

    if a.tat_ca_san:
        tong = 0
        for s in TERMINAL:
            if not Path(TERMINAL[s]).exists():
                print(f"\n=== {s}: khong cai tren may, bo qua ===")
                continue
            print(f"\n=== {s} ===")
            tong += len(do_chi_phi(s))
            time.sleep(2)          # cho terminal truoc dong han
        print(f"\n-> tong {tong} phep do tren moi san")
    else:
        kq = do_chi_phi(a.san or ("cash_vs_futures" if a.lop else (a.symbol or "tat_ca")))
        print(f"\n-> {len(kq)} phep do")
