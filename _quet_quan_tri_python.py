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
    Python file nay       11 ho, HANG CHUC ma, moc = max(mua-giu, ban-giu, tien)

**CAP NHAT 14/09/2026: da du 11 ho.** Truoc do file nay chi lam duoc sau ho mot
vi the (moc · tp_co_dinh · dat_hue · trailing · hue_trailing · tia), con nam ho
nhieu vi the (hedge · luoi_dca · stop_2_dau · tt_stop_doi · thoi_gian) phai cho
tester. `nhan/quan_tri_nhieu.py` mo phong duoc chung bang Python, di chung mot
duong tinh tien, nen bang nay gio day du va doi chieu duoc voi ban do MT5.

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
from nhan import quan_tri_nhieu as QN  # noqa: E402

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
    # NAM HO NHIEU VI THE (14/09/2026). Truoc do file nay chi lam duoc 6/11 ho
    # va nam ho con lai treo vao MT5 tester - tuc treo vao mot cu bam chuot.
    # `quan_tri_nhieu.dap_nhieu` mo phong duoc chung bang Python; tu day bang
    # nay la bang DAY DU 11 ho, doi chieu duoc voi ban do MT5.
    ra.update(QN.bo_luat())
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


#: Sut giam THAT (truoc khi quy ve ngan sach 20%) ma tren do con so `cagr_dd20`
#: KHONG con doc duoc.
#:
#: Vi sao phai co nguong nay - do 14/09/2026:
#:
#:   ho `luoi_dca` dung dau bang voi 81% o "hon moc" va hinh dang "cao nguyen".
#:   Nhung sut giam THAT cua no la **trung vi 95,9%, te nhat 100,0%**, va 45/65
#:   o tren 90%. `cagr_dd20` quy ve 20% bang cach chia don bay xuong 0,12 roi
#:   bao "17,6%/nam".
#:
#:   Phep quy do chi dung khi duong von con GIONG chinh no sau khi thu nho. Voi
#:   mot duong da di sat 0, no la ngoai suy tu MOT lan suyt chet: duoi cai duoi
#:   ma mau chua thay, giam don bay 8 lan khong cuu duoc. Va ho khac chi kem
#:   `luoi_dca` **1 diem %/nam** trong khi sut giam that chi 28%.
#:
#: Nen: o nao vuot nguong nay van duoc tinh, nhung bi GAN CO va bao cao rieng.
NGUONG_SUT_GIAM_DOC_DUOC = 60.0


#: Ma bi bo qua va VI SAO. Mot ma bo qua khong duoc bien mat im lang: neu the
#: thi "quet 60 ma" la mot con so sai, va ty le tinh tren no cung sai.
BO_QUA: dict = {}

#: Cot bat buoc. Do 13/09: mot so bang gia trong kho chi co `close` (chuoi
#: chi so, khong phai bar OHLC) -> `KeyError: 'high'` lam sap ca luot quet.
COT_CAN = ("open", "high", "low", "close")


#: Ma phai co CHI PHI DO DUOC moi duoc vao bang. Khong phai de "chat che" - de
#: bang khong bi cap chet chiem dau.
#:
#: Co che cua bay (da ghi trong ban giao 13/09 muc 3.2, va `to_hop` da chan):
#: ma khong co nguon phi = san khong bao gia lien tuc = cap neo (DKK neo EUR),
#: cap chet (EURRUR), cap mong. Chung BIEN DONG RAT THAP, ma `cagr_dd20` quy moi
#: thu ve cung ngan sach sut giam 20% nen **phat don bay khong lo cho chuoi it
#: bien dong**. Ket qua: bang thuong cho su thieu hieu biet.
#:
#: Do 14/09 khi chua co chan nay: 12 dong dau bang deu la EURRUB / EURRUR.
DOI_CHI_PHI_DO_DUOC = True


def _chi_phi_do_duoc(ma: str, df) -> tuple[bool, str]:
    from nhan import chi_phi as CP
    try:
        c = CP.tu_du_lieu(ma, df)
        cp = c[0] if isinstance(c, tuple) else c
    except Exception as e:
        return False, "khong do duoc chi phi: %s" % repr(e)[:40]
    if cp.do_tin not in ("DO", "SAN"):
        return False, "chi phi KHAI BAO (do_tin=%s) - cap neo/chet/mong" % cp.do_tin
    return True, ""


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
    if DOI_CHI_PHI_DO_DUOC:
        ok, vi_sao = _chi_phi_do_duoc(ma, df)
        if not ok:
            BO_QUA[ma] = vi_sao
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
                                      "hon_mua_giu": 0, "ma": set(),
                                      "cuc_doan": 0, "sut_giam": [],
                                      "o_sach": 0, "hon_moc_sach": 0})
            d["o"] += 1
            d["ma"].add(khoa[0])
            dd = abs(r.get("maxdd_pct", 0.0))
            d["sut_giam"].append(dd)
            cuc_doan = dd > NGUONG_SUT_GIAM_DOC_DUOC
            if cuc_doan:
                d["cuc_doan"] += 1
            else:
                d["o_sach"] += 1
            if r["cagr_dd20"] > moc["cagr_dd20"]:
                d["hon_moc_noi_bo"] += 1
                if not cuc_doan:
                    d["hon_moc_sach"] += 1
            if r["hon_moc"]:
                d["hon_mua_giu"] += 1
    for h, d in ho_dem.items():
        d["so_ma"] = len(d.pop("ma"))
        dd = sorted(d.pop("sut_giam") or [0.0])
        d["sut_giam_that_tv"] = round(dd[len(dd) // 2], 1)
        d["sut_giam_that_te_nhat"] = round(dd[-1], 1)
        d["ty_le_cuc_doan"] = round(d["cuc_doan"] / max(d["o"], 1), 3)
        d["ty_le_hon_moc"] = round(d["hon_moc_noi_bo"] / max(d["o"], 1), 3)
        # Ty le tinh TREN O SACH - do moi la con so duoc phep doc. O cuc doan
        # van duoc dem va bao cao, chi khong duoc chiem cho trong xep hang.
        d["ty_le_hon_moc_sach"] = round(d["hon_moc_sach"] / max(d["o_sach"], 1), 3)
        d["ty_le_hon_mua_giu"] = round(d["hon_mua_giu"] / max(d["o"], 1), 3)
        if d["ty_le_cuc_doan"] >= 0.5:
            # Qua nua so o co sut giam that vuot nguong -> `cagr_dd20` cua ho nay
            # la ngoai suy tu nhung duong von da di sat 0. Khong xep hang.
            d["hinh_dang"] = "KHONG_DOC_DUOC_sut_giam_cuc_doan"
        else:
            d["hinh_dang"] = ("cao_nguyen" if d["ty_le_hon_moc_sach"] >= 0.6 else
                              "cai_gai" if d["ty_le_hon_moc_sach"] <= 0.2 else "lo_cho")
    return dict(sorted(ho_dem.items(),
                       key=lambda x: (x[1]["ty_le_cuc_doan"] >= 0.5,
                                      -x[1]["ty_le_hon_moc_sach"])))


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
    print()
    print("%-15s %6s %9s %8s %11s %11s %10s  %s"
          % ("cach quan lenh", "so o", "sut giam", "te nhat", "o cuc doan",
             "o>moc SACH", "o>mua-giu", "trang thai"))
    print("-" * 97)
    for h, v in ra["ho"].items():
        tt = "KHONG DOC DUOC" if v["hinh_dang"].startswith("KHONG") else v["hinh_dang"]
        print("%-15s %6d %8.0f%% %7.0f%% %10.0f%% %10.0f%% %9.0f%%  %s"
              % (h, v["o"], v["sut_giam_that_tv"], v["sut_giam_that_te_nhat"],
                 100 * v["ty_le_cuc_doan"], 100 * v["ty_le_hon_moc_sach"],
                 100 * v["ty_le_hon_mua_giu"], tt))
    print()
    print("  'sut giam' la sut giam THAT truoc khi quy ve ngan sach 20%.")
    print("  'o>moc SACH' chi tinh tren o co sut giam that < %.0f%%."
          % NGUONG_SUT_GIAM_DOC_DUOC)
    print("  Vuot nguong do thi `cagr_dd20` la ngoai suy tu duong von sat 0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
