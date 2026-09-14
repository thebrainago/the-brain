# -*- coding: utf-8 -*-
"""_vao_lan_nhanh.py - KIEM BON LUAT roi dua he du dieu kien vao LAN NHANH.

## Vi sao

Ban giao 13/09 muc 11 dung mot module `nhan/uu_tien.py` co trong so do tu dau va
**chua bao gio chay mot lan nao**. Sang 14/09 da cam hai lan vao no, nhung van
chua he nao duoc dua vao - tuc lai dung ho loi so 1: *bo phan co ton tai, luat co
viet ra, nhung no khong nam tren duong chay*.

File nay la buoc con thieu. No KHONG quyet dinh gi moi - chi do dung bon luat da
viet san trong `uu_tien.du_dieu_kien_lan_nhanh` va dua he dat vao.

## Bon luat (nguyen van ban giao muc 11)

    1. da qua holdout THAT (nua sau chua he bi cham luc chon), va
    2. hon moc `max(mua-giu, ban-giu, tien mat)` o CUNG RUI RO, va
    3. chi phi `do_tin = SAN` (do duoc, khong phai khai), va
    4. chay duoc that: du von, lot toi thieu khong kep, so lenh du de khong may rui

Luat 1 o day do bang cat 60/40 CUA CHINH FILE NAY, va phai noi ro mot han che:
cac he nay da qua `cong.py` truoc do, nen khong the khang dinh nua sau "chua he
bi cham". Day la holdout CUA TOI, khong phai holdout nguyen thuy. Ghi ra de phien
sau khong doc no manh hon su that.

Chay:  python _vao_lan_nhanh.py            (chi DO, khong ghi)
       python _vao_lan_nhanh.py --ghi      (do xong thi dua vao lan)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import chi_phi as CP          # noqa: E402
from nhan import dap_quan_tri as DQ     # noqa: E402
from nhan import du_lieu as DU          # noqa: E402
from nhan import uu_tien as UT          # noqa: E402
from nhan import vao_lenh as VL         # noqa: E402
import _qt_tren_he_that as T            # noqa: E402

#: So lenh toi thieu o NUA SAU de khong phai may rui. Khong phai nguong hoc
#: thuat - chi la "du de mot cu may man khong lam nen ca ket qua".
LENH_TOI_THIEU_HD = 30


def do_mot_he(he: dict) -> dict:
    ma, khung = he["ma"], he["khung"]
    ten = f"{ma}.{khung}.{he['template']}"
    d: dict = {"ten": ten, "ma": ma, "khung": khung, "template": he["template"]}
    try:
        df = DU.nap(ma, khung)
    except Exception as e:
        return {**d, "bo": f"khong nap duoc: {repr(e)[:40]}"}
    th = T.tin_hieu_cua(he, df, in_ra=lambda *a: None)
    if th is None:
        return {**d, "bo": "khong dung lai duoc tin hieu"}
    giu = int(he["tham_so"].get("giu", 20) or 20)
    luat = {"thoat_bar": giu}
    cat = int(len(df) * 0.6)

    # --- don bay lay tu TOAN BO mau, khong tu nua sau (tranh ngoai suy)
    cp = CP.tu_du_lieu(ma, df)
    r_h = DQ.dap(df, th, luat, giu_toi_da=max(giu, 120))
    if r_h["so_lenh"] < 15:
        return {**d, "bo": f"ca mau chi {r_h['so_lenh']} lenh"}
    kq_h = VL.tinh_tien(df, r_h, cp, ma=ma, khung=khung)
    L = VL.quy_ve_dd(kq_h.loi_tho, r_h["_phi"], VL.so_nam_cua(df))["L"]
    d["do_tin_chi_phi"] = cp.do_tin
    d["spread_bps"] = round(cp.spread_frac_chung * 1e4, 3)
    d["don_bay"] = round(L or 0, 3)
    if not L:
        return {**d, "bo": "chay tai khoan o moi don bay"}

    # --- nua sau, chay o dung don bay do
    dh = df.iloc[cat:]
    cp2 = CP.tu_du_lieu(ma, dh)
    r = DQ.dap(dh, th[cat:], luat, giu_toi_da=max(giu, 120))
    kq = VL.tinh_tien(dh, r, cp2, ma=ma, khung=khung)
    ra = np.expm1(np.asarray(kq.loi_tho, float))
    ph = np.asarray(r["_phi"], float)
    song = 1.0 + L * ra - L * ph
    nam = VL.so_nam_cua(dh)
    d["so_lenh_hd"] = r["so_lenh"]
    d["lenh_tuan_hd"] = round(r["so_lenh"] / (nam * 52), 3)
    if np.any(song <= 0):
        return {**d, "bo": "chay tai khoan o nua sau"}
    von = np.cumprod(song)
    d["lai_nam_hd"] = round(float(von[-1] ** (1 / nam) - 1) * 100, 3)
    d["sut_giam_hd"] = round(float(1 - (von / np.maximum.accumulate(von)).min()) * 100, 2)
    # moc: max(mua-giu, ban-giu, tien mat) o CUNG ngan sach rui ro
    d["moc_hd"] = round(VL.moc_dd20(dh, cp2, ma=ma, khung=khung) * 100, 3)
    d["hon_moc"] = round(d["lai_nam_hd"] - d["moc_hd"], 3)

    # --- bon luat
    d["qua_holdout_that"] = bool(d["lai_nam_hd"] > 0)
    d["hon_moc_cung_rui_ro"] = bool(d["hon_moc"] > 0)
    d["chay_duoc_that"] = bool(d["so_lenh_hd"] >= LENH_TOI_THIEU_HD and (L or 0) <= 10)
    ok, thieu = UT.du_dieu_kien_lan_nhanh(d)
    d["dat"] = ok
    d["thieu"] = thieu
    return d


def main() -> int:
    ghi = "--ghi" in sys.argv
    print("KIEM BON LUAT VAO LAN NHANH (ban giao 13/09 muc 11)\n")
    ds = [do_mot_he(h) for h in T.he_da_qua_cong()]
    ds = [x for x in ds if "bo" not in x or x.get("lai_nam_hd") is not None]
    print(f"{'he':<40}{'lai hd':>8}{'moc':>8}{'hon moc':>9}{'sut giam':>10}"
          f"{'lenh':>6}{'L':>6}{'chi phi':>9}  ket luan")
    print("-" * 118)
    for x in sorted(ds, key=lambda y: -(y.get("hon_moc") or -99)):
        if "bo" in x:
            print(f"{x['ten'][:40]:<40}{'':>56}  BO: {x['bo']}")
            continue
        kl = "DAT" if x["dat"] else "thieu: " + "; ".join(t.split("(")[0] for t in x["thieu"])
        print(f"{x['ten'][:40]:<40}{x['lai_nam_hd']:>7.2f}%{x['moc_hd']:>7.2f}%"
              f"{x['hon_moc']:>8.2f}%{x['sut_giam_hd']:>9.2f}%{x['so_lenh_hd']:>6}"
              f"{x['don_bay']:>6.2f}{x['do_tin_chi_phi']:>9}  {kl[:44]}")

    dat = [x for x in ds if x.get("dat")]
    print(f"\n{len(dat)}/{len(ds)} he DAT ca bon luat")
    if not ghi:
        print("\n(chi DO - them `--ghi` de dua vao lan nhanh)")
        return 0
    for x in sorted(dat, key=lambda y: -y["hon_moc"]):
        r = UT.them_viec_lan(
            x["ten"], "nhanh",
            mo_ta=(f"lai {x['lai_nam_hd']:.2f}%/nam o nua sau · sut giam "
                   f"{x['sut_giam_hd']:.1f}% · hon moc {x['hon_moc']:.2f}% · "
                   f"{x['so_lenh_hd']} lenh · don bay {x['don_bay']:.2f}"),
            nguon="nao.db/ket_qua + holdout 60/40 cua _vao_lan_nhanh.py",
            qua_holdout_that=x["qua_holdout_that"],
            hon_moc_cung_rui_ro=x["hon_moc_cung_rui_ro"],
            do_tin_chi_phi=x["do_tin_chi_phi"],
            chay_duoc_that=x["chay_duoc_that"])
        print(f"  {x['ten'][:50]:<52}{'VAO LAN' if r['nhan'] else 'KHONG: ' + r['ly_do'][0][:40]}")
    print()
    UT.bang_lan()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
