# -*- coding: utf-8 -*-
"""_quet_quan_tri_python.py - DO HO QUAN TRI bang PYTHON, khong can MT5.

## VI SAO CO FILE NAY

13/09/2026 MT5 khong dang nhap duoc (`Authorization failed` - mat khau MT5
khac mat khau website XM), nen ban do `b bench-qt` nam cho. Module quan tri la
thu so do goi la quan trong nhat toan he thong; de no dung cho mot cu bam
chuot la sai.

Va quy tac cua du an von la vay: **Python test tho de loc, tester la trong
tai**. Lam nguoc thu tu chi vi tester tien tay thi khi tester hong la ca day
chuyen hong.

## KHAC GI BAN DO MT5

    MT5 `b bench-qt`      11 ho, 3 ma, moc = luoi an toan cua chinh EA
    Python file nay       6 ho, HANG CHUC ma, moc = max(mua-giu, ban-giu, tien)

Python chi lam duoc ho MOT VI THE (`dap_quan_tri.dap` mo mot vi the mot luc):
moc · tp_co_dinh · dat_hue · trailing · hue_trailing · tia. Nam ho con lai
(hedge, luoi_dca, stop_2_dau, tt_stop_doi, thoi_gian) can mo phong nhieu vi
the - do la viec cua tester.

Nhung sau ho nay dung la cho phat hien manh nhat cua ban do MT5 nam: `dat_hue`
hon moc CA LAI LAN SUT GIAM o 9/9 luot. File nay kiem lai dieu do tren nhieu
ma hon han, va bang mot MOC KHO HON (`moc_dd20` = max mua-giu/ban-giu/tien
mat, quy ve cung ngan sach sut giam).

## ENGINE VAO CO DINH

Donchian(20) pha dinh/day - giong het ban do MT5, va cung vi cung mot ly do:
neu engine vao doi theo ho thi chenh lech doc duoc khong con mot nguyen nhan.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import dap_quan_tri as DQ   # noqa: E402
from nhan import du_lieu as DU        # noqa: E402

#: LUOI AN TOAN giong ban do MT5: SL cung 3 ATR + tran 120 nen.
SL_CUNG = 3.0
GIU_TOI_DA = 120

#: Sau ho, moi ho mot luoi do lon. Ten trung voi ban do MT5 de doi chieu duoc.
def bo_luat() -> dict:
    ra = {"moc": {"sl_atr": SL_CUNG}}
    for x in (0.5, 1.0, 1.5, 2.0, 2.5):
        ra["tp_co_dinh|%.1f" % x] = {"sl_atr": SL_CUNG, "tp_atr": x}
        ra["dat_hue|%.1f" % x] = {"sl_atr": SL_CUNG, "hue_tu_atr": x}
        ra["tia|%.1f" % x] = {"sl_atr": SL_CUNG, "chot_phan": x}
        for y in (0.5, 1.0, 1.5, 2.0, 2.5):
            ra["trailing|%.1f|%.1f" % (x, y)] = {
                "sl_atr": SL_CUNG, "trail_tu_atr": x, "trail_buoc": y}
            ra["hue_trailing|%.1f|%.1f" % (x, y)] = {
                "sl_atr": SL_CUNG, "hue_tu_atr": x,
                "trail_tu_atr": x, "trail_buoc": y}
    return ra


def tin_hieu_donchian(df, n: int = 20) -> np.ndarray:
    """Pha dinh n nen -> +1, thung day -> -1. KHONG nhin truoc: chi dung bar
    da dong, va `dap` vao lenh o open[i+1]."""
    h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float)
    c = df["close"].to_numpy(float)
    ra = np.zeros(len(df))
    for i in range(n + 1, len(df)):
        dinh = h[i - n:i].max()
        day = l[i - n:i].min()
        if c[i] > dinh:
            ra[i] = 1.0
        elif c[i] < day:
            ra[i] = -1.0
    return ra


def _ho(ten: str) -> str:
    return ten.split("|")[0]


#: Ma bi bo qua va VI SAO. Mot ma bo qua khong duoc bien mat im lang: neu the
#: thi "quet 60 ma" la mot con so sai, va ty le tinh tren no cung sai.
BO_QUA: dict = {}

#: Cot bat buoc. Do 13/09: mot so bang gia trong kho chi co `close` (chuoi
#: chi so, khong phai bar OHLC) -> `KeyError: 'high'` lam sap ca luot quet.
COT_CAN = ("open", "high", "low", "close")


def mot_ma(ma: str, khung: str, in_ra=print) -> list:
    try:
        df = DU.nap(ma, khung)
    except Exception as e:
        BO_QUA[ma] = "khong nap duoc: %s" % repr(e)[:50]
        return []
    if df is None:
        BO_QUA[ma] = "nap ra None"
        return []
    thieu = [c for c in COT_CAN if c not in df.columns]
    if thieu:
        BO_QUA[ma] = "thieu cot %s (chuoi chi so, khong phai bar OHLC)" % thieu
        return []
    if len(df) < 800:
        BO_QUA[ma] = "chi %d bar (< 800)" % len(df)
        return []
    th = tin_hieu_donchian(df)
    if abs(th).sum() < 30:
        BO_QUA[ma] = "engine vao chi kich hoat %d lan" % int(abs(th).sum())
        return []
    try:
        return DQ.so_luat(df, th, ma, khung, bo_luat(), giu_toi_da=GIU_TOI_DA)
    except Exception as e:
        BO_QUA[ma] = "so_luat loi: %s" % repr(e)[:60]
        return []


def tong_hop(ds: list) -> dict:
    """Gop theo HO: cuc dai, trung vi, ty le o hon moc -> cao nguyen hay cai gai."""
    theo_ma = {}
    for r in ds:
        theo_ma.setdefault((r["ma"], r["khung"]), []).append(r)

    ho_dem = {}
    for khoa, rs in theo_ma.items():
        moc = next((x for x in rs if x["luat"] == "moc"), None)
        if not moc:
            continue
        for r in rs:
            h = _ho(r["luat"])
            if h == "moc":
                continue
            d = ho_dem.setdefault(h, {"o": 0, "hon_moc_noi_bo": 0,
                                      "hon_mua_giu": 0, "ma": set()})
            d["o"] += 1
            d["ma"].add(khoa[0])
            if r["cagr_dd20"] > moc["cagr_dd20"]:
                d["hon_moc_noi_bo"] += 1
            if r["hon_moc"]:
                d["hon_mua_giu"] += 1
    for h, d in ho_dem.items():
        d["so_ma"] = len(d.pop("ma"))
        d["ty_le_hon_moc"] = round(d["hon_moc_noi_bo"] / max(d["o"], 1), 3)
        d["ty_le_hon_mua_giu"] = round(d["hon_mua_giu"] / max(d["o"], 1), 3)
        d["hinh_dang"] = ("cao_nguyen" if d["ty_le_hon_moc"] >= 0.6 else
                          "cai_gai" if d["ty_le_hon_moc"] <= 0.2 else "lo_cho")
    return dict(sorted(ho_dem.items(), key=lambda x: -x[1]["ty_le_hon_moc"]))


def main() -> int:
    def lay(c, md):
        return sys.argv[sys.argv.index(c) + 1] if c in sys.argv else md
    khung = lay("--khung", "D1")
    so_ma = int(lay("--so-ma", "25"))

    # CHON MA CO DU LIEU CUA KHUNG DANG HOI, khong lay N ma dau bang chu cai.
    #
    # Do 13/09: lay 80 ma dau -> 72 cai la cap exotic chi co nguon D1, va
    # `du_lieu` TU CHOI tao H4 tu bar ngay ("khong noi suy nguoc" - chot chan
    # dung). Ket qua la mot bang H4 dung tren 8 ma, de doc nham thanh "H4
    # thieu du lieu" trong khi EURUSD H4 co 43.996 bar.
    #
    # `--ma` de chi dinh tay; khong thi tu loc theo so bar cua chinh khung do.
    chi_dinh = lay("--ma", "")
    if chi_dinh:
        ma_co = [x.strip() for x in chi_dinh.split(",") if x.strip()]
    else:
        kho = DU.kho()
        tat = sorted({(k[0] if isinstance(k, tuple) else str(k).split("|")[0])
                      for k in kho})
        ma_co = []
        for m in tat:
            if len(ma_co) >= so_ma:
                break
            try:
                d = DU.nap(m, khung)
            except Exception:
                continue
            if d is not None and len(d) >= 2000:
                ma_co.append(m)
    print("%d ma, khung %s, %d bo luat" % (len(ma_co), khung, len(bo_luat())),
          flush=True)

    t0 = time.time()
    ds = []
    for i, ma in enumerate(ma_co, 1):
        r = mot_ma(ma, khung)
        ds += r
        if r:
            print("  %2d/%d %-12s %3d dong  (%.0f phut)"
                  % (i, len(ma_co), ma, len(r), (time.time() - t0) / 60),
                  flush=True)

    import collections
    ly_do = collections.Counter(v.split(":")[0].split("(")[0].strip()
                                for v in BO_QUA.values())
    ra = {"khung": khung, "so_ma_thu": len(ma_co),
          "so_ma_do_duoc": len(ma_co) - len(BO_QUA),
          "so_ma_bo_qua": len(BO_QUA), "ly_do_bo_qua": dict(ly_do),
          "bo_qua": BO_QUA, "so_dong": len(ds),
          "giay": round(time.time() - t0, 1), "ho": tong_hop(ds),
          "chi_tiet": sorted(ds, key=lambda x: -x["cagr_dd20"])[:120]}
    (LAB / "reports" / ("QUAN_TRI_PYTHON_%s.json" % khung)).write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")

    print("\n%d/%d ma DO DUOC, %d bo qua: %s"
          % (ra["so_ma_do_duoc"], len(ma_co), len(BO_QUA), dict(ly_do)))
    print("\n%-14s %6s %6s %8s %10s %12s  %s"
          % ("ho", "so_ma", "so_o", "o>moc", "hinh", "o>mua-giu", ""))
    for h, d in ra["ho"].items():
        print("%-14s %6d %6d %7.0f%% %10s %11.0f%%"
              % (h, d["so_ma"], d["o"], 100 * d["ty_le_hon_moc"],
                 d["hinh_dang"], 100 * d["ty_le_hon_mua_giu"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
