# -*- coding: utf-8 -*-
"""_pmg_quet_rong.py - QUET RONG ho PMG: moi cach dat luoi x moi khung gio x moi hang.

## Vi sao co file nay

Lan quet 14/09 chi thu **120 cach dat luoi tren 3 loai hang, mot khung gio duy
nhat** - tuc mot goc rat nho cua de bai. Ket luan "gan nhu bang khong" rut ra tu
do la ket luan ve **cai goc do**, khong phai ve ca ho chien luoc.

File nay mo het:

    hang        moi ma co du lieu min (M1/M5) va qua duoc cong G0
    khung gio   ALL + 8 bucket phien
    thang do    ATR M15 / H1 / H4
    cach dat    h x buoc x co lenh x chot lai x cat lo x goc luoi x tai vu trang

va chay SONG SONG, gom viec theo (ma, khung) de moi tien trinh chi doc du lieu
MOT LAN - do la nut that da do duoc cua du an (14/15 thoi gian mot o la doc lai
file, khong phai tinh toan).

## Con so de doc ket qua

`lai_nam_dd20` - lai moi nam khi nang don bay den khi sut giam dat 20%. Moi cau
hinh deu quy ve cung mot ngan sach dau don nen so duoc voi nhau **bang tien**.
Lai tho khong so duoc: 2%/nam voi sut giam 2% hon han 8%/nam voi sut giam 30%.

Chay:  python _pmg_quet_rong.py --g0            (chay cong G0 rong truoc)
       python _pmg_quet_rong.py --quet          (quet engine tren o con song)
       python _pmg_quet_rong.py --bang          (in bang xep hang)
"""
from __future__ import annotations

import os

# PHAI DAT TRUOC KHI `import numpy`. Windows dung `spawn` nen moi tien trinh con
# import lai file nay tu dau - do la ly do dat o day chay duoc cho ca tien trinh con.
#
# Vi sao: numpy/BLAS tu mo NHIEU LUONG moi tien trinh. Mo 10 tien trinh con tuong
# la 10/20 luong = 50% CPU, thuc te an het 20 luong = 98%. Do 14/09, chu du an
# dang choi game phai cat ngang hai lan. Cai chot "cho khi qua tran" khong cuu duoc
# vi mot cau hinh chay lien 5 giay het cong suat roi moi den luot kiem tra.
for _k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_k, "1")

import itertools
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import pmg as PMG
from nhan import pmg_engine as PE
from nhan import pmg_g0 as G0
from nhan import pmg_quet as PQ
from nhan import tran_cpu as TC

RA = LAB / "reports"
BANG_RONG = RA / "PMG_QUET_RONG.json"
G0_RONG = RA / "PMG_G0_RONG.json"

# --------------------------------------------------------------- KHONG GIAN
#: Hang: moi ma co du lieu min du de mo phong luoi. Do 14/09 tu `du_lieu.kho()`.
HANG = ["AUDCAD", "AUDCHF", "AUDNZD", "EURCAD", "EURGBP", "EURNZD", "GBPCAD",
        "NZDCAD", "XAUUSDM", "US500CASH", "XM_US500CASH", "XM_US100CASH", "US500M"]

KHUNG_CHAY = "M5"
CAC_ATR_TF = ["M15", "H1", "H4"]
CAC_PHIEN = ["ALL"] + list(PMG.PHIEN) + ["WEEKEND_EDGE"]

#: BA VONG, khong phai mot. Luoi day du la ~75.000 cach dat x 13 hang x 3 thang
#: do = qua lon de thu mot luot (12+ gio may). Nen chia:
#:
#:   vong 1 THO   mo 4 truc quan trong nhat, chay het hang - tim VUNG co tien
#:   vong 2 SAU   chi o vung song sot, mo not 4 truc con lai
#:   vong 3 GIO   chi o cau hinh song sot, mo 8 khung gio trong ngay
#:
#: Cach nay vua nhanh hon vua dung luat cua du an: moi vong phai khai bao truoc
#: co bao nhieu phep thu, va o mo ra SAU khi da xem ket qua o khac thi danh dau
#: hau nghiem.
LUOI = {
    1: {   # THO - 120 cach dat moi o
        "h":            (0.5, 0.8, 1.2, 2.0, 3.0),
        "size_mode":    ("flat", "linear", "geometric", "inverse"),
        "tp_mode":      ("avg_plus", "trail", "money"),
        "max_legs":     (6, 12),
    },
    2: {   # SAU - mo not cac truc con lai
        "h":            (0.5, 0.8, 1.2, 2.0, 3.0),
        "size_mode":    ("flat", "linear", "geometric", "inverse"),
        "tp_mode":      ("avg_plus", "trail", "money"),
        "max_legs":     (6, 12, 24),
        "tp_dist":      (0.5, 1.0, 2.0),
        "step_mode":    ("fixed", "expanding", "vol_adaptive"),
        "anchor_mode":  ("static", "trailing"),
        "max_basket_dd": (0.01, 0.03, 0.08),
    },
}
LUOI_RONG = LUOI[1]


def _cac_cau_hinh(ma, phien, atr_tf, direction, don_bay_dinh=1.0, luoi=None):
    luoi = luoi or LUOI_RONG
    khoa = list(luoi)
    thay = set()
    for gia_tri in itertools.product(*(luoi[k] for k in khoa)):
        mac = {"tp_dist": 1.0, "step_mode": "fixed", "anchor_mode": "static",
               "max_basket_dd": 0.03}
        mac.update(dict(zip(khoa, gia_tri)))
        q = PMG.trong_so_size(mac["size_mode"], mac["max_legs"], 2.0)
        cf = PMG.CauHinh(ma=ma, phien=phien, atr_tf=atr_tf, direction=direction,
                         time_stop_bar=240, hard_sl_atr=6.0,
                         step_g=1.3 if mac["step_mode"] == "expanding" else 1.0,
                         phoi_nhiem_1=don_bay_dinh / float(q.sum()), **mac)
        vt = cf.van_tay()
        if vt in thay:
            continue
        thay.add(vt)
        yield cf


# ------------------------------------------------------------------ CONG G0
def _g0_mot_ma(args) -> list[dict]:
    TC.ha_uu_tien_minh()
    ma, khung, cac_atr_tf, cac_phien, so_null = args
    from nhan import du_lieu as DL
    ra = []
    try:
        df = DL.nap(ma, khung)
    except Exception as ex:
        return [{"ma": ma, "trang_thai": "CHUA_DO_DUOC", "ly_do": str(ex)[:90]}]
    if len(df) < 3000:
        return [{"ma": ma, "trang_thai": "CHUA_DO_DUOC",
                 "ly_do": f"chi {len(df)} bar {khung}"}]
    buc = PMG.bucket_phien(df.index)
    gia_het = np.asarray(df["close"], float)
    bien_do = float(np.median(df["high"] - df["low"]))
    for atr_tf in cac_atr_tf:
        try:
            atr_tv = float(np.nanmedian(PE.atr_khung(df, atr_tf, 14)))
        except Exception:
            continue
        for phien in cac_phien:
            TC.cho_neu_qua()          # nhuong may cho nguoi dung, xem nhan/tran_cpu.py
            gia = gia_het if phien == "ALL" else gia_het[buc == phien]
            if len(gia) < 3000:
                continue
            for h in G0.CAC_H:
                r = G0.do_mot_o(gia, h, atr_tv, so_null)
                r.update({"ma": ma, "khung": khung, "atr_tf": atr_tf, "h": h,
                          "phien": phien, "so_bar": int(len(gia)),
                          "atr_trung_vi": atr_tv, "bien_do_nen": bien_do,
                          "buoc_tren_bien_do": h * atr_tv / bien_do if bien_do else 0.0})
                ra.append(r)
    return ra


def chay_g0_rong(hang=None, luong: int = 0, so_null: int = 200) -> dict:
    from concurrent.futures import ProcessPoolExecutor, as_completed
    hang = hang or HANG
    luong = luong or TC.so_luong_goi_y()
    print(f"tran CPU {TC.tran():.0f}% -> mo {luong} tien trinh")
    t0 = time.time()
    viec = [(ma, KHUNG_CHAY, CAC_ATR_TF, CAC_PHIEN, so_null) for ma in hang]
    o_het = []
    with ProcessPoolExecutor(max_workers=luong) as ex:
        fu = {ex.submit(_g0_mot_ma, v): v[0] for v in viec}
        for f in as_completed(fu):
            r = f.result()
            o_het.extend(r)
            print(f"  G0 xong {fu[f]:16s} {len(r):5d} o   "
                  f"({time.time()-t0:.0f}s)", flush=True)

    do_duoc = [r for r in o_het if r.get("trang_thai") == "DO_DUOC"]
    dat = G0.fdr_bh([r["p"] for r in do_duoc], G0.MUC_FDR)
    for r, d in zip(do_duoc, dat):
        r["qua_fdr"] = bool(d)
        r["ket_luan"] = r["huong_de_xuat"] if d else "LOAI"
    for r in o_het:
        r.setdefault("qua_fdr", False)
        r.setdefault("ket_luan", "CHUA_DO_DUOC")
    bang = {"luc": time.strftime("%Y-%m-%d %H:%M:%S"), "giay": round(time.time() - t0, 1),
            "khung_chay": KHUNG_CHAY, "muc_fdr": G0.MUC_FDR, "so_null": so_null,
            "so_o": len(o_het), "so_o_do_duoc": len(do_duoc),
            "so_o_song": sum(1 for r in o_het if r.get("qua_fdr")), "o": o_het}
    RA.mkdir(parents=True, exist_ok=True)
    G0_RONG.write_text(json.dumps(bang, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nG0 RONG: {bang['so_o_song']}/{bang['so_o']} o song "
          f"({bang['so_o_do_duoc']} o do duoc) trong {bang['giay']}s")
    return bang


# ---------------------------------------------------------------- QUET ENGINE
def _quet_mot_nhom(args) -> list[dict]:
    """Mot nhom = mot (ma, atr_tf). Doc du lieu MOT LAN cho ca nhom."""
    TC.ha_uu_tien_minh()
    ma, atr_tf, cac_o = args     # cac_o = [(phien, h, direction), ...]
    from nhan import du_lieu as DL
    from nhan import chi_phi as CP
    try:
        df = DL.nap(ma, KHUNG_CHAY)
        cp = CP.tu_du_lieu(ma, df)
        atr_arr = PE.atr_khung(df, atr_tf, 14)
    except Exception as ex:
        return [{"ma": ma, "loi": str(ex)[:120]}]
    atr_frac = float(np.nanmedian(atr_arr) / np.median(df["close"]))
    cho_phep = {(p, h): d for p, h, d in cac_o}
    ket, bo_g1 = [], 0
    for phien in sorted({p for p, _, _ in cac_o}):
        for cf in _cac_cau_hinh(ma, phien, atr_tf, "AGAINST"):
            for d in ("WITH", "AGAINST"):
                if cho_phep.get((phien, cf.h)) != d:
                    continue
                c = replace(cf, direction=d)
                k = PMG.kiem_g1(c, cp.spread_frac_chung, cp.truot_gia_frac, atr_frac)
                if not k["kha_thi"]:
                    bo_g1 += 1
                    continue
                TC.cho_neu_qua()
                r = PE.mo_phong(df, c, cp, atr_arr, giu_duong_cong=True)
                r.pop("duong_cong", None)
                r["phien"] = phien
                r["direction"] = d
                ket.append(r)
    PQ.dem(len(ket) + bo_g1, f"rong/{ma}/{atr_tf}")
    return ket


def chay_quet_rong(luong: int = 0, gioi_han_nhom: int = 0) -> dict:
    from concurrent.futures import ProcessPoolExecutor, as_completed
    luong = luong or TC.so_luong_goi_y()
    print(f"tran CPU {TC.tran():.0f}% -> mo {luong} tien trinh")
    if not G0_RONG.exists():
        print("chua co G0 rong - chay `--g0` truoc")
        return {}
    g0 = json.loads(G0_RONG.read_text(encoding="utf-8"))
    song = [r for r in g0["o"] if r.get("qua_fdr")]
    nhom: dict[tuple, list] = {}
    for r in song:
        nhom.setdefault((r["ma"], r["atr_tf"]), []).append(
            (r["phien"], r["h"], r["ket_luan"]))
    viec = [(ma, tf, o) for (ma, tf), o in nhom.items()]
    viec.sort(key=lambda v: -len(v[2]))
    if gioi_han_nhom:
        viec = viec[:gioi_han_nhom]
    tong_o = sum(len(v[2]) for v in viec)
    print(f"{len(viec)} nhom (ma x thang do) · {tong_o} o song sau G0 · "
          f"moi o toi da {len(list(_cac_cau_hinh('X','ALL','H1','AGAINST')))} cach dat luoi")

    t0 = time.time()
    ket = []
    with ProcessPoolExecutor(max_workers=luong) as ex:
        fu = {ex.submit(_quet_mot_nhom, v): v for v in viec}
        xong = 0
        for f in as_completed(fu):
            r = f.result()
            ket.extend(r)
            xong += 1
            ma, tf, o = fu[f]
            print(f"  [{xong}/{len(viec)}] {ma:14s} ATR {tf:3s} -> {len(r):5d} ket qua "
                  f"({time.time()-t0:.0f}s)", flush=True)

    du = [r for r in ket if r.get("trang_thai") == "DU"]
    du.sort(key=lambda r: -(r.get("lai_nam_dd20") or -9))
    bang = {"luc": time.strftime("%Y-%m-%d %H:%M:%S"), "giay": round(time.time() - t0, 1),
            "so_chay": len(ket), "so_do_duoc": len(du),
            "bo_dem_phep_thu": PQ.dem()["tong"],
            "ket_qua": du[:4000]}
    RA.mkdir(parents=True, exist_ok=True)
    BANG_RONG.write_text(json.dumps(bang, ensure_ascii=False, indent=1, default=str),
                         encoding="utf-8")
    print(f"\nQUET RONG: chay {len(ket)} · do duoc {len(du)} · {bang['giay']}s")
    return bang


def in_bang(n: int = 30) -> None:
    """Bang xep hang BANG TIEN, viet cho nguoi doc chu khong cho may."""
    if not BANG_RONG.exists():
        print("chua co ket qua - chay `--quet` truoc")
        return
    b = json.loads(BANG_RONG.read_text(encoding="utf-8"))
    kq = b["ket_qua"]
    print()
    print("=" * 100)
    print("XEP HANG THEO TIEN - lai moi nam neu chap nhan sut giam toi da 20%")
    print("=" * 100)
    print(f"da thu {b['so_chay']} cach dat luoi · {b['so_do_duoc']} cach do duoc · "
          f"{b['giay']:.0f} giay")
    print()
    if not kq:
        print("  khong cach nao do duoc")
        return
    duong = [r for r in kq if (r.get("lai_nam_dd20") or 0) > 0]
    print(f"  co lai : {len(duong)}/{len(kq)} cach ({len(duong)/len(kq)*100:.1f}%)")
    v = sorted((r.get("lai_nam_dd20") or 0) for r in kq)
    print(f"  o giua : {v[len(v)//2]*100:+.2f}%/nam   "
          f"(neu quanh 0 thi ca ho nay khong co gi, du cai dau bang dep den may)")
    print(f"  tot nhat: {v[-1]*100:+.2f}%/nam")
    print()
    print(f"{'lai/nam':>9} {'sut giam':>9} {'don bay':>8} {'lenh/tuan':>10} "
          f"{'hang':<14} {'thang do':>9} {'gio':<13} {'chieu':<8} cach dat")
    print("-" * 130)
    for r in kq[:n]:
        o = r.get("o") or ["", "", ""]
        ten = r.get("ma", "")
        # cat phan dau da hien o cot rieng, giu phan mo ta cach dat luoi
        cach = ten.split("-", 5)[-1] if ten.count("-") >= 5 else ten
        print(f"{(r.get('lai_nam_dd20') or 0)*100:8.2f}% "
              f"{r.get('dd_max', 0)*100:8.2f}% "
              f"{r.get('don_bay_can_dd20', 0):8.1f} "
              f"{r.get('ro_moi_nam', 0)/52:10.1f} "
              f"{o[0]:<14} {r.get('atr_tf', ''):>9} {o[1]:<13} "
              f"{r.get('direction', ''):<8} {cach[:46]}")
    print()
    print("chieu: WITH = nhoi THEO da chay · AGAINST = nhoi NGUOC, mua khi roi")
    print("don bay: so lan von phai nhan len de sut giam cham 20%. Cao qua thi "
          "thuc te khong dat duoc.")


def theo_hang(b=None) -> None:
    """Tom tat theo TUNG LOAI HANG - cai nao dang dao sau, cai nao bo."""
    if b is None:
        if not BANG_RONG.exists():
            return
        b = json.loads(BANG_RONG.read_text(encoding="utf-8"))
    gom: dict[str, list] = {}
    for r in b["ket_qua"]:
        gom.setdefault((r.get("o") or [""])[0], []).append(r.get("lai_nam_dd20") or 0)
    print()
    print(f"{'hang':<16}{'so cach thu':>12}{'o giua':>10}{'tot nhat':>11}"
          f"{'ty le co lai':>14}")
    print("-" * 64)
    for ma, v in sorted(gom.items(), key=lambda x: -max(x[1])):
        v = sorted(v)
        print(f"{ma:<16}{len(v):>12}{v[len(v)//2]*100:>9.2f}%{v[-1]*100:>10.2f}%"
              f"{sum(1 for x in v if x > 0)/len(v)*100:>13.1f}%")


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--g0" in a:
        chay_g0_rong(luong=int(next((x.split("=")[1] for x in a if x.startswith("--luong=")), 0)))
    if "--quet" in a:
        chay_quet_rong(luong=int(next((x.split("=")[1] for x in a if x.startswith("--luong=")), 0)),
                       gioi_han_nhom=int(next((x.split("=")[1] for x in a
                                               if x.startswith("--nhom=")), 0)))
    if "--bang" in a or not a:
        in_bang(int(next((x.split("=")[1] for x in a if x.startswith("--n=")), 30)))
        theo_hang()
