# -*- coding: utf-8 -*-
"""dap_quan_tri.py - DAP MOT BO LUAT QUAN TRI LEN MOT TIN HIEU VAO BAT KY.

Muc quan trong nhat cua QUANTLAB theo `SO_DO_HE_THONG.txt`:

    "Rieng muc nay can chu y vi no la module quan trong trong toan bo he thong.
     Hien nay xu huong thi truong ngay cang bien dong manh nen viec su dung ky
     thuat quan li lenh tot con hon viec co 1 entry tot... He quan li lenh nay
     co the quan tri doc lap hoac lam 1 bo quy tac de tich hop vao nhung he
     thong khac (tet thu tung phuong phap quan li lenh khac nhau) de xem hieu
     qua cung nhu ket qua thay doi ra sao"

## LO HONG DA CO TRUOC FILE NAY

Lab co `quan_tri.py` (BOC luat tu ma .mq5) va `quan_tri_dsl.py` (DINH DANG khai
bao + quy doi ATR). Ca hai deu khong CHAY duoc luat len mot tin hieu. Bo mo phong
duy nhat co quan tri nam trong `mo_phong_v2.py` va no viet rieng cho LUOI.

Ket qua: kho 1.420 co che deu la tin hieu VAO, **0 cai co truong quan tri**, va
hai ho khong the ghep. File nay la cay cau do.

## MOT VONG TIEN, KHONG NHIN TRUOC

Vi the mo tai `open[i+1]` sau khi tin hieu xuat hien o `close[i]` - luat so 1 cua
du an. Trong moi bar sau do, kiem cham SL/TP bang `high`/`low` cua CHINH bar do.

**TIE-BREAK khi mot bar cham CA HAI**: dung `open` cua bar do de doan cai nao den
truoc (gan `open` hon thi cham truoc). Mac dinh lay SL la SAI - no lam moi he co
TP gan trong nhu te hon thuc te, va do la quy tac da chot trong CLAUDE.md muc 4.

## SAU LUAT, DUNG DUOC DOC LAP HOAC CHONG NHAU

    sl_atr        cat lo o X lan ATR
    tp_atr        chot loi o X lan ATR
    hue_tu_atr    lai duoc X ATR thi keo SL ve gia vao (dat hue)
    trail_tu_atr  lai duoc X ATR thi bat trailing
    trail_buoc    trailing giu cach dinh Y ATR
    thoat_bar     thoat sau N bar du chua cham gi
    chot_phan     chot mot nua khi lai X ATR (con lai chay tiep)

Khong luat nao BAT BUOC. `dap(...)` voi dict rong = giu nguyen hanh vi "vao roi
giu N bar" de doi chieu - va do chinh la moc de tra loi cau hoi cua chu du an:
**ket qua thay doi ra sao khi them quan tri**.

Chay:  python -m nhan.dap_quan_tri
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

#: Ten cac nut quan tri. Dung de kiem khai bao va de liet ke trong bao cao.
NUT = ("sl_atr", "tp_atr", "hue_tu_atr", "trail_tu_atr", "trail_buoc",
       "thoat_bar", "chot_phan")


def vi_the_co(vi_the: np.ndarray, b: int) -> float:
    """Ti trong con lai o bar b (doc tu chinh chuoi vi the, da tinh `chot_phan`)."""
    return abs(float(vi_the[b]))


def _atr(df: pd.DataFrame, n: int = 14) -> np.ndarray:
    h, l, c = (df["high"].to_numpy(float), df["low"].to_numpy(float),
               df["close"].to_numpy(float))
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.roll(c, 1)),
                                      np.abs(l - np.roll(c, 1))))
    tr[0] = h[0] - l[0]
    return pd.Series(tr).ewm(alpha=1.0 / n, adjust=False).mean().to_numpy()


def dap(df: pd.DataFrame, tin_hieu: np.ndarray, luat: dict | None = None,
        giu_toi_da: int = 500, atr_n: int = 14) -> dict:
    """Chay `tin_hieu` qua bo luat quan tri. -> {vi_the, lenh, ...}

    `tin_hieu[i]` = phoi nhiem mong muon BIET tai close[i]; vao lenh o bar i+1.
    Tra ve `vi_the` dai bang df de dua thang vao `mo_phong.chay`.
    """
    luat = dict(luat or {})
    xau = [k for k in luat if k not in NUT]
    if xau:
        raise KeyError("nut quan tri khong biet: %s (co: %s)"
                       % (xau, ", ".join(NUT)))

    o = df["open"].to_numpy(float)
    h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float)
    c = df["close"].to_numpy(float)
    atr = _atr(df, atr_n)
    n = len(df)
    th = np.asarray(tin_hieu, float)

    vi_the = np.zeros(n)
    # Ba chuoi de tinh tien theo OPEN-TO-OPEN. Xem ghi chu "MOT BAR TRE" o duoi.
    loi_tho = np.zeros(n)
    khoi = np.zeros(n)
    lenh = []
    i = 0
    while i < n - 1:
        if abs(th[i]) < 1e-12:
            i += 1
            continue
        chieu = 1.0 if th[i] > 0 else -1.0
        vao_i = i + 1                      # VAO O OPEN BAR KE TIEP
        gia_vao = o[vao_i]
        a = atr[vao_i]
        if not np.isfinite(a) or a <= 0:
            i += 1
            continue

        sl = gia_vao - chieu * luat["sl_atr"] * a if "sl_atr" in luat else None
        tp = gia_vao + chieu * luat["tp_atr"] * a if "tp_atr" in luat else None
        da_hue = False
        da_chot_phan = False
        co = 1.0                            # ti trong vi the con lai
        dinh = gia_vao                      # gia tot nhat da dat duoc
        tran_bar = int(luat.get("thoat_bar", giu_toi_da))
        j = vao_i
        ly_do = "het_bar"
        while j < n and (j - vao_i) < tran_bar:
            vi_the[j] = chieu * co
            lai_atr = chieu * (c[j] - gia_vao) / a

            # --- dat hue: keo SL ve gia vao
            if (not da_hue) and "hue_tu_atr" in luat and lai_atr >= luat["hue_tu_atr"]:
                sl = gia_vao
                da_hue = True

            # --- chot mot phan
            if (not da_chot_phan) and "chot_phan" in luat and lai_atr >= luat["chot_phan"]:
                co = 0.5
                da_chot_phan = True

            # --- trailing
            dinh = max(dinh, h[j]) if chieu > 0 else min(dinh, l[j])
            if "trail_tu_atr" in luat and lai_atr >= luat["trail_tu_atr"]:
                b = float(luat.get("trail_buoc", 1.0)) * a
                moi = dinh - chieu * b
                sl = moi if sl is None else (max(sl, moi) if chieu > 0 else min(sl, moi))

            # --- cham SL / TP trong bar j+1
            if j + 1 >= n:
                j += 1
                break
            k = j + 1
            cham_sl = sl is not None and ((l[k] <= sl) if chieu > 0 else (h[k] >= sl))
            cham_tp = tp is not None and ((h[k] >= tp) if chieu > 0 else (l[k] <= tp))
            if cham_sl and cham_tp:
                # TIE-BREAK bang `open` cua bar do - CLAUDE.md muc 4.
                # Mac dinh lay SL la SAI: no lam moi he TP gan trong te hon that.
                ly_do = "tp" if abs(o[k] - tp) <= abs(o[k] - sl) else "sl"
                j = k
                break
            if cham_sl:
                ly_do = "sl"
                j = k
                break
            if cham_tp:
                ly_do = "tp"
                j = k
                break
            j += 1
        else:
            ly_do = "het_gio"
        # --- TINH TIEN OPEN-TO-OPEN cho chan vua dong
        ra_i = int(min(j, n - 1))
        gia_ra = (tp if ly_do == "tp" else sl if ly_do == "sl" else o[ra_i])
        if gia_ra is None:
            gia_ra = o[ra_i]
        khoi[vao_i] += 1.0
        khoi[ra_i] += co
        for b in range(vao_i, ra_i):
            g0 = gia_vao if b == vao_i else o[b]
            g1 = o[b + 1] if b + 1 < n else o[b]
            loi_tho[b] += chieu * vi_the_co(vi_the, b) * np.log(
                max(g1, 1e-12) / max(g0, 1e-12))
        if ra_i > vao_i:
            g0 = o[ra_i]
            loi_tho[ra_i] += chieu * co * np.log(
                max(gia_ra, 1e-12) / max(g0, 1e-12))
        lenh.append({"vao": int(vao_i), "ra": ra_i,
                     "chieu": int(chieu), "bar": int(min(j, n - 1) - vao_i),
                     "ly_do": ly_do, "co_cuoi": co})
        i = max(j, vao_i + 1)

    dem = {}
    for x in lenh:
        dem[x["ly_do"]] = dem.get(x["ly_do"], 0) + 1
    return {"vi_the": vi_the, "loi_tho": loi_tho, "khoi_luong": khoi,
            "dai": np.maximum(vi_the, 0.0), "ngan": np.maximum(-vi_the, 0.0),
            "so_lenh": len(lenh), "ly_do": dem,
            "bar_trung_vi": float(np.median([x["bar"] for x in lenh])) if lenh else 0.0,
            "lenh": lenh}


#: Bo luat de doi chieu. Moi cai mot Y TUONG, khong phai mot luoi tham so -
#: muc dich la tra loi "them quan tri thi doi gi", khong phai tim so dep nhat.
BO_LUAT = {
    "khong_gi": {},
    "sl2_tp4": {"sl_atr": 2.0, "tp_atr": 4.0},
    "sl2_tp4_hue1": {"sl_atr": 2.0, "tp_atr": 4.0, "hue_tu_atr": 1.0},
    "sl2_trail1": {"sl_atr": 2.0, "trail_tu_atr": 1.0, "trail_buoc": 1.0},
    "sl3_trail2": {"sl_atr": 3.0, "trail_tu_atr": 2.0, "trail_buoc": 2.0},
    "sl2_tp4_chot1": {"sl_atr": 2.0, "tp_atr": 4.0, "chot_phan": 1.0},
    "sl2_tp6_hue2_trail2": {"sl_atr": 2.0, "tp_atr": 6.0, "hue_tu_atr": 2.0,
                            "trail_tu_atr": 2.0, "trail_buoc": 2.0},
    "chot_nhanh_sl1_tp1": {"sl_atr": 1.0, "tp_atr": 1.0},
}


# ------------------------------------------------------- SO TIEN GIUA CAC LUAT
NGAN_SACH_DD = 20.0

# ------------------------------------------------- CHAN QUAN TRI BAT BUOC (G3-A)
#
# So do cua chu du an: *"quan li lenh tot con hon viec co 1 entry tot - module
# quan trong trong toan bo he thong"*. Do 16/09 (`b ho-so`): 262 co che trong
# kho la tin hieu VAO, chi 18 la quan tri; lop THU THAP co 19 module con lop
# QUAN TRI VI THE chi 12. Dau tu dang nguoc voi hieu qua do duoc: entry tinh
# SAI ma co lop quan tri dung van cho 92-97%/nam.
#
# Nen tu day mot tin hieu vao **khong duoc ghi so mot minh**. No phai di kem it
# nhat BA bo luat quan tri, trong do bat buoc co:
#
#   - DAT HUE (`hue_tu_atr`) - luat DUY NHAT song sot ngoai mau (do: trailing
#     -68%, nhoi lenh dep trong mau nhung Calmar xau ngoai mau)
#   - TRAILING (`trail_tu_atr`) - lai holdout x4,8 khi co CHO de chay

#: Ba bo luat toi thieu. Deu nam trong `BO_LUAT` nen khong sinh them engine.
BO_BAT_BUOC = ("sl2_tp4_hue1", "sl2_trail1", "sl2_tp6_hue2_trail2")

#: Duoi nguong nay thi trailing/dat hue KHONG CO CHO de hoat dong.
#:
#: Khong phai con so tuy y: `trail_tu_atr = 1.0` doi gia di 1 ATR **roi** hoi
#: lai moi cat. Mot lenh giu 1-2 bar thi ca hai viec do khong kip xay ra, nen
#: ket qua khong phai "trailing khong an thua" ma la **CHUA DO DUOC** - dung
#: cai phan biet ma luat doc ket qua doi.
BAR_TOI_THIEU_CHO_TRAIL = 3


def _co_nut(luat, nut: str) -> bool:
    return isinstance(luat, dict) and float(luat.get(nut) or 0) > 0


def luat_co_cho(bar_trung_vi: float | None, ten: str, luat=None) -> tuple[bool, str]:
    """Bo luat nay co CHO de hoat dong tren he giu lenh ngan nhu vay khong?"""
    luat = BO_LUAT.get(ten, {}) if luat is None else luat
    can_cho = _co_nut(luat, "trail_tu_atr") or _co_nut(luat, "hue_tu_atr")
    if not can_cho:
        return True, ""
    if bar_trung_vi is None:
        return True, ""
    if bar_trung_vi < BAR_TOI_THIEU_CHO_TRAIL:
        return False, ("giu trung vi %.1f bar < %d - trailing/dat hue khong kip "
                       "kich hoat" % (bar_trung_vi, BAR_TOI_THIEU_CHO_TRAIL))
    return True, ""


def du_chan_quan_tri(ds: list[dict]) -> dict:
    """CONG: bo ket qua nay da du chan quan tri de duoc ghi so chua?

    Tra ve `{dat, ly_do, da_chay, co_hue, co_trail, thieu_cho}` - khong chi
    True/False, vi "thieu cho" va "chua chay" la hai ket luan khac nhau va
    tron chung lai la dung cai bay `CHUA_DO_DUOC` vs `AM`.
    """
    chay = [d for d in ds if d.get("luat") and d.get("luat") != "khong_gi"]
    hue = [d for d in chay if _co_nut(BO_LUAT.get(d["luat"]), "hue_tu_atr")]
    trail = [d for d in chay if _co_nut(BO_LUAT.get(d["luat"]), "trail_tu_atr")]
    thieu_cho = []
    for d in chay:
        ok, ly = luat_co_cho(d.get("bar_tv"), d["luat"])
        if not ok:
            thieu_cho.append({"luat": d["luat"], "ly_do": ly})
    ly_do = []
    if len(chay) < 3:
        ly_do.append("moi chay %d bo luat, can >= 3" % len(chay))
    if not hue:
        ly_do.append("thieu DAT HUE (`hue_tu_atr`) - luat duy nhat song ngoai mau")
    if not trail:
        ly_do.append("thieu TRAILING (`trail_tu_atr`)")
    return {"dat": not ly_do, "ly_do": ly_do, "da_chay": len(chay),
            "co_hue": len(hue), "co_trail": len(trail),
            "thieu_cho": thieu_cho}


def so_luat(df, tin_hieu, ma, khung, bo_luat=None, giu_toi_da=20) -> list[dict]:
    """Chay TUNG bo luat tren CUNG mot tin hieu roi so bang TIEN.

    Day la cau hoi chu du an dat ra: "tet thu tung phuong phap quan li lenh khac
    nhau de xem hieu qua cung nhu ket qua thay doi ra sao". Bien doc lap duy nhat
    la BO LUAT - tin hieu vao, tai san, khung, chi phi deu giu nguyen.

    Moi dong quy ve CUNG ngan sach sut giam de so duoc voi nhau va voi moc.
    Moc = max(mua-giu, ban-giu, tien mat) - xem ghi chu o `_quet_song_moc`.
    """
    from nhan import bien_don_bay as B
    from nhan import chi_phi as CP
    from nhan import mo_phong as MP
    c = CP.tu_du_lieu(ma, df)
    cp = c[0] if isinstance(c, tuple) else c
    from nhan import vao_lenh as _VL
    moc = _VL.moc_dd20(df, cp, ma, khung)
    ra = []
    for ten, luat in (bo_luat or BO_LUAT).items():
        # Mot bo luat co the la (a) dict nut cua ho MOT vi the, hoac (b) cap
        # `(ten_ho, tham_so)` cua ho NHIEU vi the. Hai engine khac nhau nhung
        # tu day tro xuong di CHUNG mot duong tinh tien - do la ly do
        # `quan_tri_nhieu.dap_nhieu` xuat dung ba mang ma `tinh_tien` doc.
        if isinstance(luat, tuple):
            from nhan import quan_tri_nhieu as QN
            r = QN.dap_nhieu(df, tin_hieu, luat[0], luat[1],
                             giu_toi_da=max(giu_toi_da, QN.GIU_TOI_DA))
        else:
            r = dap(df, tin_hieu, luat, giu_toi_da=giu_toi_da)
        if r["so_lenh"] < 15:
            continue
        # Bo luat can CHO ma he nay thoat qua nhanh -> ghi nhan la CHUA DO
        # DUOC, khong phai chay roi bao ket qua kem. Xem `luat_co_cho`.
        co_cho, ly_thieu_cho = luat_co_cho(r.get("bar_trung_vi"), ten, luat)
        # KHONG dung MP.chay: no dich them mot bar nen vi the an loi suat cua
        # bar i+2 thay vi i+1 (do duoc 12/09/2026 bang chuoi dung san). Bo tinh
        # tien cua `vao_lenh` vao o open[i+1] va an tu dung do.
        from nhan import vao_lenh as VL
        kq = VL.tinh_tien(df, r, cp, ma=ma, khung=khung)
        h = B._chi_so(kq)
        q = VL.quy_ve_dd(kq.loi_tho, r["_phi"], VL.so_nam_cua(df))
        dd20 = 0.0 if q["chet"] or q["cagr"] is None else q["cagr"] * 100.0
        ra.append({"ma": ma, "khung": khung, "luat": ten,
                   "so_lenh": r["so_lenh"], "bar_tv": r["bar_trung_vi"],
                   "cagr_pct": round(h["cagr"] * 100, 3),
                   "sharpe": round(h["sharpe"], 3),
                   "maxdd_pct": round(h["maxdd"] * 100, 2),
                   "cagr_dd20": round(dd20, 3),
                   "don_bay_quy": None if q["L"] is None else round(q["L"], 4),
                   "chet_tai_khoan": bool(q["chet"]),
                   "moc_dd20": round(moc * 100, 3),
                   "hon_moc": bool(dd20 > moc * 100),
                   "co_cho": co_cho, "ly_do_thieu_cho": ly_thieu_cho,
                   "ly_do": r["ly_do"]})
    return ra


def main(argv: list[str]) -> int:
    from nhan import du_lieu as DL
    from nhan import ngu_phap as NP
    ma = argv[0] if argv else "XM_US30CASH"
    khung = argv[1] if len(argv) > 1 else "H4"
    df = DL.nap(ma, khung)
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
    th = np.clip(th, -1.0, 1.0)
    print("%s %s · %d bar · tin hieu kich hoat %.1f%%"
          % (ma, khung, len(df), 100 * np.mean(np.abs(th) > 0)))
    print("\n%-22s %7s %9s %s" % ("bo luat", "lenh", "bar tv", "ly do thoat"))
    print("-" * 70)
    for ten, luat in BO_LUAT.items():
        r = dap(df, th, luat, giu_toi_da=20)
        print("%-22s %7d %9.1f %s"
              % (ten, r["so_lenh"], r["bar_trung_vi"],
                 json.dumps(r["ly_do"], ensure_ascii=False)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
