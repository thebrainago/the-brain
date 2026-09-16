# -*- coding: utf-8 -*-
"""GOP RO CO HA DUOC MDE KHONG — do bang CUNG DON VI voi bang MDE don le.

Bang MDE ngay 23/08 chi ra: voi chi so va vang, rang buoc la PHAT HIEN (MDE gap
11-15 lan chi phi), khong phai chi phi. Cach duy nhat de ha MDE ma khong noi
nguong la TANG LUC, va cach re nhat de tang luc la gop nhieu tai san cung lop.

Nhung so cai da ghi mot ket qua nguoc chieu (22/08): *"gop 12 chi so chi ha
nguong 0,535 -> 0,511"*. Do la do bang **Sharpe** qua `gop_lop.mde_gop`. Script
nay do lai bang **bps moi lenh** de dat canh bang MDE don le, va do them TUONG
QUAN thuc te + so tai san hieu dung - vi do moi la thu quyet dinh gop co an thua
khong.

PHEP DO (giong nhau cho ca hai nhanh, nen so sanh duoc):
  1. Cay edge delta bps vao TUNG chuoi (giu tin hieu, bu tru drift).
  2. Sinh tin hieu co che, chay qua engine voi chi phi that -> chuoi loi suat.
  3. Nhanh DON: lay mot tai san. Nhanh GOP: gop deu loi suat cua k tai san.
  4. Nguong bac bo lay tu CHINH phan phoi null (delta = 0): phan vi 95.
     Tu hieu chuan, nen khong phu thuoc vao noi tai cua cong.
  5. Ty le phat hien = ty le cua so vuot nguong do.

Chay: python chay_gop_vs_don.py [--so-lan 200] [--nhanh]
Ra:   reports/GOP_VS_DON.json + .md
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nhan import do_luc as DLUC
from nhan import do_luong as DO
from nhan import du_lieu as DL
from nhan import mau as MAU
from nhan import mo_phong as MP
from nhan import nha_may_null as NM
from nhan import pham_vi as PV
from nhan import sang_loc as SL
from nhan import so as SO

LAB = Path(__file__).resolve().parent
#: Luoi delta MIN o dau thap: gop chi co the ha MDE trong vung ma nhanh
#: don CHUA phat hien duoc. Luoi tho (buoc 5 bps) lam ca hai nhanh bao hoa
#: 100% cung mot muc va "gop khong an thua" tro thanh mot ket luan gia.
DELTA = (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 20.0)
MAU_CAY = "ibs_bat_day"
THAM_SO = {"nguong": 0.2}
CUA_SO = 1500


def _kho_lop(lop: str, khung: str = "D1", toi_da: int = 10) -> list[str]:
    ra = []
    for ma in PV.kho_du_bar(khung, toi_thieu=CUA_SO + 200):
        try:
            if PV.loai_cua(ma) == lop:
                ra.append(ma)
        except Exception:
            continue
    return sorted(ra)[:toi_da]


def _nap_het(cac_ma: list[str], khung: str) -> dict:
    """Nap, roi CHI GIU nhom nam tren CUNG MOT LUOI GIO.

    Do that: 82 cap FX trong kho D1 nam tren HAI luoi khac nhau - nhom cua san
    dong nen luc 00:00, nhom Yahoo dong luc 21:00 UTC. Gop hai nhom do la cong
    loi suat cua hai ngay khac nhau. `du_lieu.chuan_hoa_index` chi go NHAN
    timezone, no khong quy doi that - va tai lieu cua chinh ham do ghi ro
    "KHONG duoc dung neu hai nguon nam tren luoi gio KHAC nhau".
    """
    tho = {}
    for ma in cac_ma:
        try:
            d = DL.nap(ma, khung)
        except Exception:
            continue
        if d is not None and len(d) > CUA_SO + 200:
            tho[ma] = d
    if not tho:
        return {}
    nhom = {}
    for ma, d in tho.items():
        khoa = frozenset(DL.chuan_hoa_index(d.index).hour)
        nhom.setdefault(khoa, {})[ma] = d
    lon_nhat = max(nhom.values(), key=len)
    return lon_nhat


def _loi_suat_co_che(df, ma, khung, delta, cp):
    """Cay edge -> sinh tin hieu -> chay engine -> chuoi loi suat theo index."""
    d2, _ = NM.cay_edge_vao_gia(df, delta)
    th = MAU.sinh(MAU_CAY, d2, THAM_SO)
    kq = MP.chay(d2, th, cp, ma=ma, khung=khung)
    if kq.loi is None or len(kq.loi) == 0:
        return None
    return pd.Series(np.asarray(kq.loi, dtype=float), index=kq.index)


def _sharpe(x: np.ndarray, khung: str) -> float:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if x.size < 30 or float(np.std(x)) < 1e-15:
        return 0.0
    moc = SL._bar_moi_nam(khung)
    return float(np.sqrt(moc) * np.mean(x) / np.std(x))


def _mot_cua_so(bang: dict, khung: str, cp_theo_ma: dict, delta: float,
                dau: int) -> dict:
    """Mot cua so thoi gian -> {sharpe_don_tung_ma, sharpe_gop, rho}."""
    chuoi = {}
    for ma, df in bang.items():
        phan = df.iloc[dau:dau + CUA_SO]
        if len(phan) < CUA_SO:
            continue
        s = _loi_suat_co_che(phan, ma, khung, delta, cp_theo_ma[ma])
        if s is not None:
            chuoi[ma] = s
    if len(chuoi) < 2:
        return {}
    # Cac chuoi den tu nhieu nguon: mot so co timezone, mot so khong. Ghep thang
    # thi pandas nem "Cannot compare tz-naive and tz-aware timestamps".
    # `du_lieu.chuan_hoa_index` da co san cho viec nay - va no chi dung khi cac
    # nguon nam CUNG LUOI GIO, nen kiem truoc bang `cung_luoi_gio`.
    if not DL.cung_luoi_gio([s.index for s in chuoi.values()]):
        return {}
    chuoi = {ma: s.set_axis(DL.chuan_hoa_index(s.index))
             for ma, s in chuoi.items()}
    khung_bang = pd.concat(chuoi, axis=1).dropna(how="all").fillna(0.0)
    gop = khung_bang.mean(axis=1).to_numpy()
    # Tuong quan trung binh giua cac chan - quyet dinh gop an thua bao nhieu.
    tq = khung_bang.corr().to_numpy()
    tren = tq[np.triu_indices_from(tq, k=1)]
    rho = float(np.nanmean(tren)) if tren.size else 0.0
    return {"don": {ma: _sharpe(khung_bang[ma].to_numpy(), khung)
                    for ma in khung_bang.columns},
            "gop": _sharpe(gop, khung), "rho": rho, "k": khung_bang.shape[1]}


def do_mot_lop(lop: str = "chi_so_my", khung: str = "D1", so_lan: int = 200) -> dict:
    t0 = time.time()
    cac_ma = _kho_lop(lop, khung)
    bang = _nap_het(cac_ma, khung)
    if len(bang) < 3:
        return {"lop": lop, "loi": f"chi co {len(bang)} tai san du bar"}
    cp = {ma: SL._chi_phi_cua(ma) for ma in bang}
    n_min = min(len(d) for d in bang.values())
    rng = np.random.default_rng(4242)
    moc_dau = [int(rng.integers(0, max(1, n_min - CUA_SO))) for _ in range(so_lan)]

    thu = {str(d): {"don": [], "gop": [], "rho": []} for d in DELTA}
    for delta in DELTA:
        for dau in moc_dau:
            r = _mot_cua_so(bang, khung, cp, delta, dau)
            if not r:
                continue
            thu[str(delta)]["don"].append(float(np.median(list(r["don"].values()))))
            thu[str(delta)]["gop"].append(r["gop"])
            thu[str(delta)]["rho"].append(r["rho"])

    null_don = np.array(thu["0.0"]["don"], dtype=float)
    null_gop = np.array(thu["0.0"]["gop"], dtype=float)
    if null_don.size < 10 or null_gop.size < 10:
        return {"lop": lop, "loi": "khong du cua so chay duoc"}
    # NGUONG BAC BO tu chinh phan phoi null -> tu hieu chuan, 5% duong tinh gia.
    nguong_don = float(np.quantile(null_don, 0.95))
    nguong_gop = float(np.quantile(null_gop, 0.95))

    bangkq = {}
    for delta in DELTA:
        d = str(delta)
        a = np.array(thu[d]["don"], dtype=float)
        b = np.array(thu[d]["gop"], dtype=float)
        bangkq[d] = {
            "don_phat_hien_pct": round(100.0 * float(np.mean(a > nguong_don)), 1),
            "gop_phat_hien_pct": round(100.0 * float(np.mean(b > nguong_gop)), 1),
            "don_sharpe_tv": round(float(np.median(a)), 3),
            "gop_sharpe_tv": round(float(np.median(b)), 3),
        }

    def _mde(khoa):
        for delta in DELTA:
            if bangkq[str(delta)][khoa] >= 80.0:
                return float(delta)
        return None

    rho = float(np.nanmedian(np.array(thu["0.0"]["rho"], dtype=float)))
    k = len(bang)
    return {
        "lop": lop, "khung": khung, "so_tai_san": k, "tai_san": sorted(bang),
        "so_lan": so_lan, "cua_so_bar": CUA_SO,
        "rho_trung_binh": round(rho, 3),
        "k_hieu_dung": round(DLUC.k_hieu_dung(rho, k), 2),
        "nguong_don_sharpe": round(nguong_don, 3),
        "nguong_gop_sharpe": round(nguong_gop, 3),
        "bang": bangkq,
        "MDE_don_bps": _mde("don_phat_hien_pct"),
        "MDE_gop_bps": _mde("gop_phat_hien_pct"),
        "giay": round(time.time() - t0, 1),
    }


def _viet_md(ket: dict) -> None:
    d = ["# GOP RO CO HA DUOC MDE KHONG", f"*{ket['luc']}*", "",
         "Do bang **bps moi lenh** de dat canh duoc bang MDE don le.",
         "Nguong bac bo lay tu chinh phan phoi null (phan vi 95), nen ca hai nhanh",
         "deu co cung muc duong tinh gia 5% - so sanh moi cong bang.", ""]
    for r in ket["lop"]:
        if r.get("loi"):
            d += [f"## {r['lop']} — loi: {r['loi']}", ""]
            continue
        d += [f"## {r['lop']} · {r['khung']} · {r['so_tai_san']} tai san", "",
              f"- Tuong quan trung binh giua cac chan: **{r['rho_trung_binh']}**",
              f"- So tai san HIEU DUNG: **{r['k_hieu_dung']}** trong {r['so_tai_san']}",
              f"- Nguong bac bo (Sharpe): don {r['nguong_don_sharpe']} · gop {r['nguong_gop_sharpe']}",
              "",
              "| delta (bps/lenh) | DON phat hien | GOP phat hien | Sharpe don (tv) | Sharpe gop (tv) |",
              "|---|---|---|---|---|"]
        for k, v in r["bang"].items():
            d.append(f"| {k} | {v['don_phat_hien_pct']} % | **{v['gop_phat_hien_pct']} %** | "
                     f"{v['don_sharpe_tv']} | {v['gop_sharpe_tv']} |")
        md, mg = r["MDE_don_bps"], r["MDE_gop_bps"]
        d += ["", f"**MDE don = {md if md is not None else '> ' + str(max(DELTA))} bps/lenh · "
                  f"MDE gop = {mg if mg is not None else '> ' + str(max(DELTA))} bps/lenh**"]
        if md and mg:
            d.append(f"→ gop ha MDE **{md/mg:.2f} lan**" if mg < md else
                     "→ **gop KHONG ha duoc MDE**")
        d.append("")
    (LAB / "reports" / "GOP_VS_DON.md").write_text("\n".join(d), encoding="utf-8")


def main() -> int:
    so_lan = 200
    if "--so-lan" in sys.argv:
        so_lan = int(sys.argv[sys.argv.index("--so-lan") + 1])
    if "--nhanh" in sys.argv:
        so_lan = 15
    ket = {"luc": SO.bay_gio(), "so_lan": so_lan, "delta": list(DELTA), "lop": []}
    for lop in ("chi_so_my", "vang", "fx"):
        print(f"[{time.strftime('%H:%M:%S')}] {lop} ...", flush=True)
        r = do_mot_lop(lop, "D1", so_lan)
        ket["lop"].append(r)
        print(f"    MDE don={r.get('MDE_don_bps')} gop={r.get('MDE_gop_bps')} "
              f"rho={r.get('rho_trung_binh')} k_hd={r.get('k_hieu_dung')} "
              f"({r.get('giay')}s) {r.get('loi','')}", flush=True)
        (LAB / "reports" / "GOP_VS_DON.json").write_text(
            json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")
    _viet_md(ket)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
