# -*- coding: utf-8 -*-
"""Chay ban NGHIEM THU cua nha may luc + nha may null, ra BANG MDE.

Ban thu 23/08 chi chay 20 cua so tren MOT cap (US500CASH D1) va cho MDE = 30
bps/lenh. Ban nay chay 200 cua so tren nhieu cap de:
  - co khoang tin cay cho tung con so,
  - biet MDE doi the nao theo TAI SAN va KHUNG.

Chay: python chay_bang_mde.py [--so-lan 200] [--nhanh]
Ket qua: reports/BANG_MDE.json + reports/BANG_MDE.md
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nhan import nha_may_null as NM
from nhan import so as SO

LAB = Path(__file__).resolve().parent
CAP = [
    ("US500CASH", "D1"), ("XM_US30CASH", "D1"), ("YH_NASDAQ", "D1"),
    ("XAUUSD", "D1"), ("EURCAD", "D1"), ("EURCAD", "H4"),
    # Hai ma nay vao duoc be mat tu 24/08: truoc do `kho()` chon ban M5 nen
    # chung chi co 367 bar D1 - duoi nguong 1.500 cua `duong_cong_luc`.
    ("XM_US500CASH", "D1"), ("XM_US100CASH", "D1"),
]
# Luoi day hon ban 23/08 (0/5/10/20/30/50/80). Ly do: sau khi sua bo nap, MDE
# cua nhom chi so tut xuong quanh 10-20 bps va luoi cu khong doc duoc buoc do -
# no chi noi duoc "20 hay 30", trong khi cau hoi la "co xuong duoi chi phi khong".
DELTA = (0.0, 2.0, 5.0, 8.0, 10.0, 15.0, 20.0, 30.0, 50.0)


def _khoang_tin_cay(p_pct: float, n: int) -> tuple[float, float]:
    """Khoang Wilson 95% cho mot ty le. Dung Wilson chu khong dung sai so chuan
    thong thuong: o bien 0% va 100% - dung noi ta hay o nhat - sai so chuan cho
    khoang rong bang 0, tuc bao 'chac chan tuyet doi' tu mot mau huu han."""
    if n <= 0:
        return (0.0, 0.0)
    p = p_pct / 100.0
    z = 1.96
    d = 1 + z * z / n
    tam = (p + z * z / (2 * n)) / d
    nua = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (round(100 * max(0.0, tam - nua), 1), round(100 * min(1.0, tam + nua), 1))


def mot_cap(ma: str, khung: str, so_lan: int) -> dict:
    t0 = time.time()
    ra = {"tai_san": ma, "khung": khung, "so_lan": so_lan}
    try:
        luc = NM.duong_cong_luc(ma, khung, cac_delta=DELTA, so_lan=so_lan)
    except Exception as e:
        return {**ra, "loi": f"{type(e).__name__}: {str(e)[:100]}"}
    if luc.get("loi"):
        return {**ra, "loi": luc["loi"]}

    for d, o in luc["bang"].items():
        o["khoang_95"] = _khoang_tin_cay(o["ty_le_phat_hien_pct"], so_lan)
    ra["luc"] = luc
    ra["MDE_bps"] = luc["MDE_bps_moi_lenh"]
    ra["duong_tinh_gia_pct"] = luc["duong_tinh_gia_pct"]

    # Nha may null: chieu con lai cua bai kiem hai chieu.
    try:
        ra["null"] = NM.null_day_du(ma, khung, so_chuoi=so_lan)
    except Exception as e:
        ra["null"] = {"loi": f"{type(e).__name__}: {str(e)[:80]}"}
    ra["giay"] = round(time.time() - t0, 1)
    return ra


def main() -> int:
    so_lan = 200
    if "--so-lan" in sys.argv:
        so_lan = int(sys.argv[sys.argv.index("--so-lan") + 1])
    if "--nhanh" in sys.argv:
        so_lan = 20
    cap = CAP[:2] if "--nhanh" in sys.argv else CAP

    ket = {"luc": SO.bay_gio(), "so_lan": so_lan, "delta": list(DELTA), "cap": []}
    for ma, khung in cap:
        print(f"[{time.strftime('%H:%M:%S')}] {ma} {khung} ...", flush=True)
        r = mot_cap(ma, khung, so_lan)
        ket["cap"].append(r)
        print(f"    MDE={r.get('MDE_bps')} duong_tinh_gia={r.get('duong_tinh_gia_pct')}%"
              f" ({r.get('giay')}s) {r.get('loi','')}", flush=True)
        (LAB / "reports" / "BANG_MDE.json").write_text(
            json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")

    _viet_md(ket)
    return 0


def _viet_md(ket: dict) -> None:
    d = ["# BANG MDE — edge nho nhat pheu con thay duoc", f"*{ket['luc']}*", "",
         f"- So cua so moi muc: **{ket['so_lan']}**",
         f"- Muc delta quet: {ket['delta']} (bps moi lenh)",
         "- Co che cay: `ibs_bat_day` (IBS < 0,2)",
         "- MDE = delta nho nhat dat >= 80% phat hien", "",
         "## Bang tong", "",
         "| Tai san | Khung | MDE (bps/lenh) | Duong tinh gia (delta=0) | Null lot cao nhat |",
         "|---|---|---|---|---|"]
    for c in ket["cap"]:
        if c.get("loi"):
            d.append(f"| {c['tai_san']} | {c['khung']} | — | — | loi: {c['loi'][:40]} |")
            continue
        nl = c.get("null", {}).get("ty_le_lot_cao_nhat_pct")
        mde = c.get("MDE_bps")
        d.append(f"| {c['tai_san']} | {c['khung']} | "
                 f"{mde if mde is not None else '> ' + str(max(ket['delta']))} | "
                 f"{c.get('duong_tinh_gia_pct')} % | {nl if nl is not None else '—'} % |")
    d += ["", "## Duong cong luc tung cap", ""]
    for c in ket["cap"]:
        if c.get("loi"):
            continue
        d += [f"### {c['tai_san']} · {c['khung']}", "",
              "| delta (bps) | phat hien | khoang 95% | dung o vong |", "|---|---|---|---|"]
        for k, v in c["luc"]["bang"].items():
            kt = v.get("khoang_95", ("", ""))
            d.append(f"| {k} | {v['ty_le_phat_hien_pct']} % | "
                     f"{kt[0]}–{kt[1]} % | {v['dung_o_vong']} |")
        d.append("")
    (LAB / "reports" / "BANG_MDE.md").write_text("\n".join(d), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
