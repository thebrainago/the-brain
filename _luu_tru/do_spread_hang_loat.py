# -*- coding: utf-8 -*-
"""do_spread_hang_loat.py - DO SPREAD THAT CHO CA BE MAT, MOT LAN NOI SAN.

## VI SAO CO FILE NAY (06/09/2026)

Luat bat bien cua du an: `chi_phi.do_tin == "KHAI"` thi **khong bao gio PASS**.
Do 06/09 tren kho 194 bang gia:

    da do spread          44
    CHUA do, nhung CO tren san   122   <- day la nut that
    khong co tren san nao         28   (chuoi YH_/ETF_, khong giao dich duoc)

**122 symbol trong be mat do duoc ngay ma chua ai do.** Ban giao 05/09 ghi nut
that la "chi phi do duoc", va de xuat viet EA ghi spread. Nhung ha tang da co
san tu 16/08: `chi_phi.do_spread_tu_bar_mt5()` doc cot `spread` THAT cua bar H1
- chinh no da nang `XM_US100CASH` len PASS ngay 05/09. Khong thieu cong cu,
thieu mot luot chay. Dung ho benh [[noi-day-truoc-khi-xay-them]].

## VI SAO KHONG GOI THANG `bao_dam_spread` TRONG MOT VONG LAP

`do_spread_tu_bar_mt5` lap qua `SAN_UU_TIEN` = [XM, Exness, FXCE, Ultima] va
goi `mt5.initialize(path=...)` cho TUNG san, TUNG symbol. FXCE va Ultima khong
mo tren may nay, nen `initialize` di KHOI CHAY terminal roi cho - do that:
3 symbol khong xong trong 300 giay. Nhan len 122 symbol thi khong bao gio ve.

Va API Python cua MT5 chi giu MOT ket noi mot luc, nen doi san la doi ca tien
trinh terminal. Cach dung: **chon mot san, noi mot lan, quet het**.

XM la san mac dinh vi do la san du an se giao dich that
([[ban-do-chi-phi-lien-san]]: FXCE + Exness la may chu demo/trial, chenh 5,5
diem %/nam - so cua chung khong dung duoc de ket luan chi phi).

## BAN GHI SINH RA GIONG HET `do_spread_tu_bar_mt5`

Cung khoa, cung don vi (ty le tren gia, tuc dung "bps theo gia hien tai" cua
AGENTS muc 7), cung cho luu (`config/chi_phi_do.json` -> `_spread_bar_mt5`).
Neu khac di thi ban do duoc o day se khong duoc `bao_dam_spread` doc lai.

    python do_spread_hang_loat.py            # bao cao, KHONG ghi
    python do_spread_hang_loat.py --that     # ghi vao chi_phi_do.json
    python do_spread_hang_loat.py --that --san Exness
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nhan import chi_phi as CP        # noqa: E402
from nhan import du_lieu as DL        # noqa: E402

#: Duoi nguong nay thi ban do khong dang tin - cung nguong cua
#: `do_spread_tu_bar_mt5`, khong duoc noi long rieng o day.
TOI_THIEU_BAR = 300
SO_BAR = 6000


def _ten_tren_san(san: str, pn: str) -> str | None:
    """Ten symbol cua `san` ung voi phoi nhiem `pn`. Doc tu bang `_theo_san` da
    quet san - KHONG doan tu ten tho ([[do-phi-qua-dem-ba-cai-bay]]: tra cuu
    ten tho lang le lay phi cua may chu demo)."""
    for ten in (CP._doc_luu().get("_theo_san", {}).get(san) or {}):
        if CP.chuan_hoa_phoi_nhiem(ten) == pn:
            return ten
    return None


def _do_mot(mt5, ten_san: str, san: str) -> dict | None:
    """Mot symbol -> ban ghi spread, hoac None. Khong shutdown - nguoi goi giu
    ket noi cho ca luot."""
    r = None
    for _ in range(4):        # goi dau sau symbol_select hay thieu bar
        mt5.symbol_select(ten_san, True)
        r = mt5.copy_rates_from_pos(ten_san, mt5.TIMEFRAME_H1, 0, SO_BAR)
        if r is not None and len(r) >= 500:
            break
        time.sleep(1.0)
    if r is None or len(r) < 500:
        return None
    si = mt5.symbol_info(ten_san)
    pt = float(si.point) if si else None
    if not pt:
        return None

    d = pd.DataFrame(r)
    d["time"] = pd.to_datetime(d["time"], unit="s")
    gia = float(np.nanmedian(d["close"].to_numpy()))
    if not np.isfinite(gia) or gia <= 0:
        return None
    s = d["spread"].to_numpy(dtype=float)
    tot = (s > 0) & np.isfinite(s)
    gio = d["time"].dt.hour.to_numpy()
    dow = d["time"].dt.dayofweek.to_numpy()
    # Bo cuoi tuan va gio giao ca: [[bay-do-luong-mt5-xm]] - spread cuoi tuan
    # bi thoi 2-6 lan, lay vao la bao mot con so khong ai phai tra.
    dung = tot & (dow < 5) & ~np.isin(gio, list(CP.GIO_LOAI))
    if dung.sum() < TOI_THIEU_BAR:
        dung = tot
    if dung.sum() < TOI_THIEU_BAR:
        return None

    theo_gio = {}
    for g in range(24):
        m = dung & (gio == g)
        if m.sum() >= 50:
            theo_gio[int(g)] = float(np.median(s[m])) * pt / gia
    return {
        "chung": float(np.median(s[dung])) * pt / gia,
        "theo_gio": theo_gio,
        "san": san, "symbol": ten_san, "so_bar": int(dung.sum()),
        "tu": str(d["time"].min())[:16], "den": str(d["time"].max())[:16],
        "do_luc": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def chay(san: str = "XM", that: bool = False, in_ra=print) -> dict:
    try:
        import MetaTrader5 as mt5
    except Exception as e:
        in_ra("khong nap duoc MetaTrader5: %s" % e)
        return {"chua_do": True}

    dd = CP.TERMINAL.get(san)
    if not dd or not Path(dd).exists():
        in_ra("khong thay terminal cua san %s" % san)
        return {"chua_do": True}

    ma = sorted({k[0] if isinstance(k, tuple) else k for k in DL.kho()})
    can = []
    for m in ma:
        pn = CP.chuan_hoa_phoi_nhiem(m)
        if CP._spread_da_luu(m):
            continue
        ten = _ten_tren_san(san, pn)
        if ten:
            can.append((m, pn, ten))
    in_ra("be mat %d ma · CHUA do va co tren %s: %d" % (len(ma), san, len(can)))
    if not can:
        return {"can": 0}

    if not mt5.initialize(path=dd):
        in_ra("khong noi duoc terminal %s: %s" % (san, mt5.last_error()))
        return {"chua_do": True}

    # Ten trong `_theo_san` da bi `.upper()` khi luu, nhung MT5 PHAN BIET HOA
    # THUONG va tra None khong bao loi. Doi chieu mot lan cho ca luot.
    that_ten = {s.name.upper(): s.name for s in (mt5.symbols_get() or [])}
    in_ra("terminal %s: %d symbol" % (san, len(that_ten)))

    xong, hong, t0 = [], [], time.time()
    try:
        for i, (m, pn, ten) in enumerate(can, 1):
            ten = that_ten.get(ten.upper(), ten)
            try:
                r = _do_mot(mt5, ten, san)
            except Exception as e:
                r = None
                hong.append((m, "%s: %s" % (type(e).__name__, str(e)[:60])))
            if r is None:
                if not hong or hong[-1][0] != m:
                    hong.append((m, "khong du bar hoac khong co spread"))
                continue
            xong.append((m, r))
            if that:
                CP._luu_spread(m, r)
            if i % 10 == 0 or i == len(can):
                in_ra("  %3d/%d  (%.0fs)  vua xong %-10s %.4f bps"
                      % (i, len(can), time.time() - t0, m, r["chung"] * 1e4))
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass

    in_ra("")
    in_ra("DO DUOC: %d · khong do duoc: %d · %.0f giay"
          % (len(xong), len(hong), time.time() - t0))
    if xong:
        v = sorted(xong, key=lambda x: x[1]["chung"])
        in_ra("re nhat : " + ", ".join("%s %.2f" % (m, r["chung"] * 1e4) for m, r in v[:8]))
        in_ra("dat nhat: " + ", ".join("%s %.1f" % (m, r["chung"] * 1e4) for m, r in v[-8:]))
    for m, ly in hong[:12]:
        in_ra("  khong do duoc %-12s %s" % (m, ly))
    if not that:
        in_ra("")
        in_ra("  (chay lai voi --that de ghi vao config/chi_phi_do.json)")
    return {"do_duoc": len(xong), "hong": len(hong)}


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    s = "XM"
    if "--san" in sys.argv:
        s = sys.argv[sys.argv.index("--san") + 1]
    chay(san=s, that="--that" in sys.argv)
