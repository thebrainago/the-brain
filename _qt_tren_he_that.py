# -*- coding: utf-8 -*-
"""_qt_tren_he_that.py - GAN 11 HO QUAN TRI LENH LEN CHINH CAC HE DA QUA CONG.

## Vi sao doi bo do

Bang 11 ho chay 14/09 tren 61 ma cho mot ket qua ma thu hang la phan it quan
trong nhat. Cot dang doc la SUT GIAM: **moi ho deu 44-96%**. Do khong phai tinh
chat cua quan tri lenh - do la tinh chat cua **engine vao** ma bench dung
(Donchian pha dinh + SL 3 ATR, khong co co lenh theo rui ro). Ca cai bang chi
tra loi duoc *"quan tri nao it te nhat tren mot engine te"*.

Chu du an da noi dung dieu do trong ban giao 13/09 muc 4.B'.2: bench gan quan tri
len mot engine vao **CO DINH** roi hoi "them quan tri thi doi gi".

Cau hoi that cua module quan li lenh la:

    **Gan vao mot he DA CO EDGE thi tien doi the nao?**

Va du an co san chin he da qua cong that. File nay gan 11 ho len chung.

## Bien doc lap duy nhat la BO LUAT QUAN TRI

Tin hieu vao, tai san, khung, chi phi, ngan sach sut giam - giu nguyen het. Moc
so sanh la **chinh he do voi luat thoat goc cua no** (`giu N bar`), khong phai
mua-giu; vi cau hoi la "them quan tri thi doi gi", khong phai "co hon mua-giu
khong" (cau do he da tra loi luc qua cong).

Chay:  python _qt_tren_he_that.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import dap_quan_tri as DQ     # noqa: E402
from nhan import du_lieu as DU          # noqa: E402
from nhan import mau as MAU             # noqa: E402
from nhan import ngu_phap as NP         # noqa: E402
from nhan import quan_tri_nhieu as QN   # noqa: E402
from _quet_quan_tri_python import (      # noqa: E402
    SL_CUNG, GIU_TOI_DA, NGUONG_SUT_GIAM_DOC_DUOC, _chi_phi_do_duoc)


def he_da_qua_cong() -> list[dict]:
    """Chin he trong `nao.db/ket_qua` co verdict PASS, khu trung theo (ma,khung,co che)."""
    from nhan import so as SO
    rs = SO.nhieu(
        # `g.ma` la TEN GIA THUYET (US500CASH.D1.mean_reversion_z5.giu500...),
        # khong phai ma tai san. Ma tai san nam o `g.tai_san`. Nham cot nay thi
        # `du_lieu.nap` nem FileNotFoundError cho ca chin he.
        "SELECT k.gt_ma, k.verdict, g.tai_san, g.khung, g.template, g.tham_so "
        "FROM ket_qua k JOIN gia_thuyet g ON g.ma = k.gt_ma "
        "WHERE k.verdict = 'PASS' ORDER BY k.id DESC")
    thay, ra = set(), []
    for r in rs:
        ts = json.loads(r["tham_so"]) if isinstance(r["tham_so"], str) else (r["tham_so"] or {})
        khoa = (r["tai_san"], r["khung"], r["template"], json.dumps(ts, sort_keys=True))
        if khoa in thay or not r["tai_san"]:
            continue
        thay.add(khoa)
        ra.append({"ma": r["tai_san"], "khung": r["khung"],
                   "template": r["template"], "tham_so": ts, "gt_ma": r["gt_ma"]})
    return ra


def tin_hieu_cua(he: dict, df, in_ra=print) -> np.ndarray | None:
    """Dung lai tin hieu VAO cua he. Ba duong, va thu tu giua chung co li do.

    Ba cho de sai, ca ba da sap trong mot buoi:

    1. `nap_vao_mau()` phai goi TRUOC khi doc `MAU`. Khong goi thi bang chi co 18
       mau go tay va moi co che DSL deu bi ket luan "khong dung lai duoc".
    2. Sau khi goi, `MAU[ten]` **khong phai spec, cung khong phai ham** - no la
       mot BOC NGOAI `{co_che, dsl, ham, ho, luoi, nguon, tham_so_tam}`. Cua dung
       de goi la `MAU.sinh(ten, df, tham_so)`.
    3. Spec THO trong kho la ban mau voi tham so mac dinh; tham so cua he (dang
       phang: `vao0_trai_n`, `ra0_phai_hang`, `giu`) phai dat nguoc vao bang
       `ngu_phap.ap_tham_so`.

    Va cai bay chung cua ca ba: khi sai, `sinh_tu_spec` **khong nem ngoai le** -
    no tra ve mot mang TOAN 0. Khong canh bao nao, chi la "he nay khong co tin
    hieu". Do that: US500CASH.D1.mean_reversion_z5 ra 0 kich hoat trong khi he
    that co 197 lenh. Nen o day moi duong deu bao ro no da thu gi.
    """
    t, ts = he["template"], he["tham_so"]
    try:
        NP.nap_vao_mau()
    except Exception as e:
        in_ra(f"     nap_vao_mau loi: {repr(e)[:60]}")

    def _ok(th, nhan):
        if th is None:
            return None
        th = np.nan_to_num(np.asarray(th, float).reshape(-1), nan=0.0)
        n = int(np.sum(np.abs(th) > 0))
        if n < 15:
            in_ra(f"     {nhan}: chi {n} kich hoat")
            return None
        return th

    # 1. KHO THO truoc - day la duong `to_hop` dung, nen ket qua doi chieu duoc.
    can = NP.chuan_hoa_ten(t)
    for spec in NP.doc_kho():
        if NP.chuan_hoa_ten(spec.get("ten", "")) != can:
            continue
        try:
            th = _ok(NP.sinh_tu_spec(NP.ap_tham_so(spec, ts) if ts else spec, df),
                     f"kho[{t}]")
            if th is not None:
                return th
        except Exception as e:
            in_ra(f"     kho[{t}] loi: {repr(e)[:70]}")
        break

    # 2. MAU qua dung cua cua no
    if t in MAU.MAU:
        try:
            th = _ok(MAU.sinh(t, df, ts), f"MAU.sinh({t})")
            if th is not None:
                return th
        except Exception as e:
            in_ra(f"     MAU.sinh({t}) loi: {repr(e)[:70]}")
        try:
            dsl = (MAU.MAU[t] or {}).get("dsl")
            if isinstance(dsl, dict):
                th = _ok(NP.sinh_tu_spec(NP.ap_tham_so(dsl, ts) if ts else dsl, df),
                         f"MAU[{t}].dsl")
                if th is not None:
                    return th
        except Exception as e:
            in_ra(f"     MAU[{t}].dsl loi: {repr(e)[:70]}")

    in_ra(f"     khong dung lai duoc `{t}` bang duong nao")
    return None


def bo_luat_11_ho(giu_goc: int) -> dict:
    """11 ho + MOC = chinh he do voi luat thoat goc (`giu` bar), khong quan tri."""
    ra: dict = {"moc_he_goc": {"thoat_bar": giu_goc}}
    for x in (0.5, 1.0, 2.0):
        ra["tp_co_dinh|%.1f" % x] = {"sl_atr": SL_CUNG, "tp_atr": x}
        ra["dat_hue|%.1f" % x] = {"sl_atr": SL_CUNG, "hue_tu_atr": x}
        ra["tia|%.1f" % x] = {"sl_atr": SL_CUNG, "chot_phan": x}
        for y in (0.5, 1.0, 2.0):
            ra["trailing|%.1f|%.1f" % (x, y)] = {
                "sl_atr": SL_CUNG, "trail_tu_atr": x, "trail_buoc": y}
            ra["hue_trailing|%.1f|%.1f" % (x, y)] = {
                "sl_atr": SL_CUNG, "hue_tu_atr": x, "trail_tu_atr": x,
                "trail_buoc": y}
    ra.update(QN.bo_luat())
    return ra


def _ho(ten: str) -> str:
    return ten.split("|")[0]


def mot_he(he: dict, in_ra=print) -> list[dict]:
    ma, khung = he["ma"], he["khung"]
    try:
        df = DU.nap(ma, khung)
    except Exception as e:
        in_ra(f"  {ma}.{khung}: khong nap duoc ({repr(e)[:40]})")
        return []
    ok, vi_sao = _chi_phi_do_duoc(ma, df)
    if not ok:
        in_ra(f"  {ma}.{khung}: {vi_sao}")
        return []
    in_ra(f"  {ma}.{khung}.{he['template']}")
    th = tin_hieu_cua(he, df, in_ra)
    if th is None:
        return []
    giu_goc = int(he["tham_so"].get("giu", 20) or 20)
    try:
        ds = DQ.so_luat(df, th, ma, khung, bo_luat_11_ho(giu_goc),
                        giu_toi_da=max(giu_goc, GIU_TOI_DA))
    except Exception as e:
        in_ra(f"  {ma}.{khung}: so_luat loi {repr(e)[:60]}")
        return []
    for r in ds:
        r["he"] = f"{ma}.{khung}.{he['template']}"
        r["ho"] = _ho(r["luat"])
    in_ra(f"  {ma}.{khung}.{he['template']:<28} {len(ds):>3} o  "
          f"(tin hieu kich hoat {int(abs(th).sum())} lan)")
    return ds


def main() -> int:
    t0 = time.time()
    cac_he = he_da_qua_cong()
    print(f"{len(cac_he)} he da qua cong (da khu trung)\n")
    ds = []
    for he in cac_he:
        ds.extend(mot_he(he))
    if not ds:
        print("khong he nao dung lai duoc")
        return 1

    # ---- gop theo HO, moc la chinh he goc cua TUNG he
    theo_he: dict = {}
    for r in ds:
        theo_he.setdefault(r["he"], []).append(r)
    ho_dem: dict = {}
    for he_ten, rs in theo_he.items():
        moc = next((x for x in rs if x["luat"] == "moc_he_goc"), None)
        if not moc:
            continue
        for r in rs:
            if r["luat"] == "moc_he_goc":
                continue
            d = ho_dem.setdefault(r["ho"], {"o": 0, "hon": 0, "sach": 0,
                                            "hon_sach": 0, "cuc_doan": 0,
                                            "dd": [], "loi": []})
            d["o"] += 1
            dd = abs(r.get("maxdd_pct", 0.0))
            d["dd"].append(dd)
            d["loi"].append(r["cagr_dd20"] - moc["cagr_dd20"])
            if dd > NGUONG_SUT_GIAM_DOC_DUOC:
                d["cuc_doan"] += 1
            else:
                d["sach"] += 1
                if r["cagr_dd20"] > moc["cagr_dd20"]:
                    d["hon_sach"] += 1
            if r["cagr_dd20"] > moc["cagr_dd20"]:
                d["hon"] += 1

    print()
    print("=" * 100)
    print("GAN 11 HO LEN HE DA CO EDGE — moc la CHINH he do, khong quan tri")
    print("=" * 100)
    print(f"{'cach quan lenh':<15}{'so o':>6}{'sut giam':>10}{'cuc doan':>10}"
          f"{'o>he goc':>10}{'loi/nam them':>14}{'tot nhat':>10}")
    print("-" * 100)
    hang = []
    for h, d in ho_dem.items():
        dd = sorted(d["dd"]) or [0.0]
        loi_sach = sorted(d["loi"])
        hang.append((d["hon_sach"] / max(d["sach"], 1), h, d, dd, loi_sach))
    for ty, h, d, dd, loi in sorted(hang, reverse=True):
        print(f"{h:<15}{d['o']:>6}{dd[len(dd)//2]:>9.0f}%"
              f"{100*d['cuc_doan']/max(d['o'],1):>9.0f}%{100*ty:>9.0f}%"
              f"{np.median(loi):>13.2f}%{max(loi):>9.2f}%")
    print()
    print("  'loi/nam them' = lai/nam o cung sut giam 20%, TRU chinh he goc.")
    print("  Duong nghia la them quan tri thi he do ra them tien.")

    ra = {"so_he": len(cac_he), "so_o": len(ds),
          "giay": round(time.time() - t0, 1),
          "ho": {h: {k: (v if not isinstance(v, list) else
                         {"trung_vi": round(float(np.median(v)), 3),
                          "tot_nhat": round(float(max(v)), 3),
                          "te_nhat": round(float(min(v)), 3)})
                     for k, v in d.items()} for h, d in ho_dem.items()},
          "chi_tiet": sorted(ds, key=lambda x: -x["cagr_dd20"])[:150]}
    (LAB / "reports" / "QT_TREN_HE_THAT.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n-> reports/QT_TREN_HE_THAT.json ({ra['giay']:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
