# -*- coding: utf-8 -*-
"""bang_he.py - BANG CAC HE DA QUA CONG. Mat xich cuoi cung, va no dang thieu.

## VI SAO CO FILE NAY

Chu du an 13/09/2026: *"Tong the he thong dang chua lam duoc gi kia."*

Di dem thi khong dung han: he **co** san pham - 9 he rieng biet da qua cong,
trong do `XM_US100CASH.D1.mean_rev` cho CAGR 14,05% / Sharpe 1,16 / sut giam
13,5%. Nhung khong mot cho nao trong he tra loi duoc cau hoi **"hien co may
he da qua cong, moi cai dang bao nhieu"**. No nam rai trong `nao.db`, lan
giua 1.284 dong ket qua, co ca ban trung (15 dong = 9 he).

Mot phong nghien cuu ma khong ai doc duoc danh muc san pham cua no thi nhin
tu ngoai dung la "chua lam duoc gi" - va cai nhin do khong sai, vi khong ai
DUNG duoc thu khong thay.

## BA DIEU BANG NAY PHAI NOI, KHONG DUOC THIEU

  1. **So voi MUA-GIU**, khong chi so tuyet doi. Mot he 8,26%/nam nghe hay
     cho toi khi biet mua-giu cung ma cho 9,97%. Cot `hon_mua_giu` la cot
     quan trong nhat bang.
  2. **Cong nao TRUOT**. Do 13/09: 1/15 dong PASS duoc cap nhan trong khi
     `5_placebo` va `4_alpha_duong_co_y_nghia` deu `false`. Mot dong PASS co
     cong truot phai hien ra, khong duoc gop chung voi PASS sach.
  3. **Tuoi**. Mot he qua cong ba thang truoc, tren the he cong da doi, thi
     khong con la mot phat hien - no la mot ghi chep lich su.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(GOC))

from nhan import so as SO  # noqa: E402


def _js(x):
    if isinstance(x, str):
        try:
            return json.loads(x)
        except Exception:
            return {}
    return x or {}


def thu_hoach(chi_pass: bool = True) -> list[dict]:
    """Moi he DA QUA CONG, khu trung, kem so tien va cong nao truot."""
    dk = "WHERE verdict LIKE '%PASS%'" if chi_pass else ""
    rs = SO.nhieu("SELECT id, gt_ma, luc, chi_so, cong, verdict, alpha, "
                  "t_alpha, p_placebo FROM ket_qua %s ORDER BY id DESC" % dk)
    theo_he: dict = {}
    for r in rs:
        ma = str(r["gt_ma"] or "")
        if ma in theo_he:          # da co ban MOI hon (ORDER BY id DESC)
            theo_he[ma]["so_lan_cham"] += 1
            continue
        ci = _js(r["chi_so"])
        he = ci.get("he") or {}
        mg = ci.get("mua_giu_net") or ci.get("mua_giu") or {}
        # SO LENH nam o nhanh `hoat_dong`, khong o `he`. Khong lay dung cho
        # thi cot nay toan `?`, va so lenh la con so quyet dinh mot he co
        # THAT khong: luat cua du an loai thang he duoi 2 lenh/tuan, va
        # `dap_quan_tri.so_luat` bo qua ban co duoi 15 lenh.
        hd = ci.get("hoat_dong") or {}
        cp = ci.get("chi_phi") or {}
        cong = _js(r["cong"])
        truot = sorted(k for k, v in cong.items() if v is False)
        theo_he[ma] = {
            "he": ma, "luc": r["luc"], "so_lan_cham": 1,
            "cagr_pct": he.get("cagr_pct"), "sharpe": he.get("sharpe"),
            "calmar": he.get("calmar"), "max_dd_pct": he.get("max_dd_pct"),
            "so_lenh": hd.get("so_lenh"), "so_nam": he.get("so_nam"),
            "lenh_moi_tuan": hd.get("lenh_moi_tuan"),
            "chi_phi_pct": cp.get("tong_pct"),
            "phi_qua_dem_ty_trong": cp.get("phi_qua_dem_ty_trong"),
            "phoi_nhiem": he.get("phoi_nhiem"),
            "mua_giu_cagr": mg.get("cagr_pct"),
            "mua_giu_sharpe": mg.get("sharpe"),
            "alpha": r["alpha"], "t_alpha": r["t_alpha"],
            "cong_truot": truot, "sach": not truot,
        }
    ra = list(theo_he.values())
    for d in ra:
        c, m = d.get("cagr_pct"), d.get("mua_giu_cagr")
        d["hon_mua_giu_cagr"] = (None if c is None or m is None
                                 else round(c - m, 3))
        s, sm = d.get("sharpe"), d.get("mua_giu_sharpe")
        d["hon_mua_giu_sharpe"] = (None if s is None or sm is None
                                   else round(s - sm, 3))
    ra.sort(key=lambda d: (-(d["sharpe"] or -9), -(d["cagr_pct"] or -9)))
    return ra


def bang(in_ra=print, chi_pass: bool = True) -> dict:
    ds = thu_hoach(chi_pass)
    sach = [d for d in ds if d["sach"]]
    hon = [d for d in sach if (d.get("hon_mua_giu_sharpe") or -9) > 0]
    in_ra("=" * 96)
    in_ra("HE DA QUA CONG: %d he  ·  %d sach (khong cong nao truot)  ·  "
          "%d hon MUA-GIU ve Sharpe" % (len(ds), len(sach), len(hon)))
    in_ra("=" * 96)
    in_ra("%-40s %7s %7s %7s %8s %7s %6s %7s"
          % ("he", "CAGR%", "Sharpe", "Calmar", "DD%", "d.Shrp", "lenh",
             "l/tuan"))
    for d in ds:
        dau = "  " if d["sach"] else "! "
        in_ra("%s%-38s %7s %7s %7s %8s %7s %6s %7s"
              % (dau, d["he"][:38],
                 _n(d["cagr_pct"]), _n(d["sharpe"]), _n(d["calmar"]),
                 _n(d["max_dd_pct"]), _n(d["hon_mua_giu_sharpe"]),
                 d["so_lenh"] if d["so_lenh"] is not None else "?",
                 _n(d.get("lenh_moi_tuan"))))
        if not d["sach"]:
            in_ra("      ! cong TRUOT: %s" % ", ".join(d["cong_truot"]))
    in_ra("")
    in_ra("dau `!` = duoc cap nhan PASS nhung co cong TRUOT - dung doc chung "
          "voi cac dong con lai")
    in_ra("cot `d.Shrp` = Sharpe cua he TRU Sharpe mua-giu cung ma. Am nghia "
          "la mua-giu tot hon.")
    ra = {"so_he": len(ds), "so_sach": len(sach), "so_hon_mua_giu": len(hon),
          "he": ds}
    (GOC / "reports" / "BANG_HE.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    return ra


def _n(x, nd=2):
    return "?" if x is None else ("%.*f" % (nd, x))


if __name__ == "__main__":
    bang(chi_pass="--het" not in sys.argv)
