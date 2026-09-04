# -*- coding: utf-8 -*-
"""da_thoi_dai.py - CHAY MOT CO CHE TREN MOI CUA SO DU LIEU SACH, khong chi mot.

VI SAO. Do 04/09/2026, va no la con so lon nhat tim duoc trong ca phien:

    SP500 D1 co **24.754 nen** (98,6 nam). He dang dung **3.404**.

Duong di cua viec cat:
    `do_luc._nap_da_cat` -> `du_lieu.cat_theo_chat_luong(...)[0]`
        -> `doan_dai_nhat(cua_so_open_that)`  -> lay MOT cua so: 1928-1961
    roi `hai_nua(..., 0.6)[1]`                -> lay 40% lam holdout
    => 8.508 * 0,4 = 3.404 nen.

Cat theo chat luong la DUNG - `open` cua SP500 la BIA o phan lon chuoi
(open[i] == close[i-1] o 39,9% bar toan chuoi), va backtest tren gia bia thi vo
nghia. Nhung `doan_dai_nhat` vut di nhung cua so sach KHAC:

    cua so open THAT cua SP500: [1928-1961] [1988] [2007-2011] [2014-2026]
    dang dung:                  [1928-1961]
    vut di:                                  [1988] [2007-2011] [2014-2026]

Gop het cua so sach lai duoc ~13.000 nen thay vi 8.508. MDE ti le nghich voi
can bac hai do dai, nen do la **0,81 -> ~0,42** - dung khoang cach giua "khong
chung minh noi gi" va "chung minh duoc mot edge Sharpe 0,5".

CACH GOP - va day la cho de sai nhat:

  **KHONG noi cac cua so thanh mot chuoi gia.** Noi 1961-12-29 vao 2007-01-03
  tao ra mot buoc nhay gia gia tao, va bar dau tien cua cua so sau se sinh mot
  loi suat khong co that - thuong la loi suat LON NHAT trong ca chuoi, tuc no
  se chi phoi moi thong ke.

  Cach dung: **chay RIENG tung cua so roi gop THONG KE** (meta-analysis). Loi
  suat khong bao gio bat qua ranh gioi thoi dai. Sharpe gop tinh theo trong so
  so nen, va do lech chuan cua Sharpe gop giam theo can bac hai tong so nen -
  chinh la cai loi ta muon.

VA MOT LOI THE THU HAI, quan trong khong kem: chay tren nhieu thoi dai cho
**phep kiem thoi dai mien phi**. Mot co che song ca o 1928-1961 lan 2014-2026
dang tin hon han mot co che khop 13 nam lien mach - hai thoi dai do khac nhau
ve che do lai suat, vi cau truc, phi giao dich, va thanh phan nguoi tham gia.
Neu no chi song o mot thoi dai, ta biet ngay do la hien tuong cua thoi ky do
(dung ho voi ghi nho "IBS la hien tuong cua mot thoi ky").
"""
from __future__ import annotations

import numpy as np

from nhan import du_lieu as DU

#: Cua so ngan hon nay thi thong ke vo nghia - bo, khong gop.
SAN_BAR = 400


def cac_cua_so_sach(ma: str, khung: str = "D1",
                    san_bar: int = SAN_BAR) -> list[dict]:
    """MOI cua so co `open` that, khong chi cua so dai nhat.

    Tra danh sach `{tu, den, df, so_bar}` theo thu tu thoi gian.
    """
    df = DU.nap(ma, khung)
    if df is None or len(df) < san_bar:
        return []
    bc = DU.kiem(df, ma)
    cua_so = bc.get("cua_so_open_that") or []
    if not cua_so:
        # Chuoi khong co van de open bia -> ca chuoi la mot cua so.
        return [{"tu": int(df.index[0].year), "den": int(df.index[-1].year),
                 "df": df, "so_bar": len(df)}]
    ra = []
    for tu, den in cua_so:
        d = df[(df.index.year >= tu) & (df.index.year <= den)]
        if len(d) >= san_bar:
            ra.append({"tu": int(tu), "den": int(den), "df": d,
                       "so_bar": int(len(d))})
    return ra


def gop_sharpe(muc: list[dict]) -> dict:
    """Gop Sharpe cua nhieu thoi dai theo trong so SO NEN.

    Sharpe gop = tong(sharpe_i * n_i) / tong(n_i). Sai so chuan cua Sharpe xap
    xi sqrt(1/n), nen gop N thoi dai lam sai so giam theo sqrt(tong n) - do la
    ly do ky thuat cua ca file nay.
    """
    muc = [m for m in muc if m.get("sharpe") is not None and m.get("so_bar")]
    if not muc:
        return {"sharpe_gop": None, "so_bar": 0, "so_thoi_dai": 0}
    n = np.array([m["so_bar"] for m in muc], dtype=float)
    s = np.array([m["sharpe"] for m in muc], dtype=float)
    tong = float(n.sum())
    gop = float((s * n).sum() / tong)
    return {"sharpe_gop": round(gop, 4),
            "so_bar": int(tong),
            "so_thoi_dai": len(muc),
            "sharpe_tung_thoi_dai": [round(float(x), 4) for x in s],
            # Sai so chuan xap xi cua Sharpe gop.
            "sai_so_chuan": round(float(np.sqrt(1.0 / tong)), 5),
            # Do dong thuan: bao nhieu thoi dai cung dau voi Sharpe gop.
            "cung_dau": int(np.sum(np.sign(s) == np.sign(gop))),
            "dong_thuan": round(float(np.mean(np.sign(s) == np.sign(gop))), 3)}


def chay_co_che(spec: dict, ma: str, khung: str = "D1", cp=None,
                san_bar: int = SAN_BAR) -> dict:
    """Chay mot co che DSL tren TUNG cua so sach, roi gop thong ke.

    Tra `{thoi_dai: [...], gop: {...}}`. `thoi_dai` giu ket qua rieng tung cua
    so de nhin duoc co che co song qua nhieu thoi ky khong.
    """
    from nhan import bien_don_bay as B
    from nhan import chi_phi as CP
    from nhan import ngu_phap as NP

    ra = []
    for cs in cac_cua_so_sach(ma, khung, san_bar):
        d = cs["df"]
        try:
            vi_the = NP.sinh_tu_spec(spec, d)
        except Exception as e:
            ra.append({"tu": cs["tu"], "den": cs["den"], "so_bar": cs["so_bar"],
                       "loi": f"{type(e).__name__}: {str(e)[:70]}"})
            continue
        if vi_the is None or not np.any(np.asarray(vi_the) != 0):
            ra.append({"tu": cs["tu"], "den": cs["den"], "so_bar": cs["so_bar"],
                       "bo_qua": "khong co vi the nao"})
            continue
        c = cp
        if c is None:
            c = CP.tu_du_lieu(ma, d)
            c = c[0] if isinstance(c, tuple) else c
        try:
            # `da_dich=False` BAT BUOC. Docstring cua `mo_phong.chay` noi ro:
            # *"da_dich=True chi dung cho CANARY"*. Tin hieu tu
            # `ngu_phap.sinh_tu_spec` tinh tai CLOSE cua bar i, nen engine PHAI
            # dich sang bar i+1; truyen True la bo buoc dich do = nhin truoc.
            #
            # DA SAP THAT 04/09/2026: ban dau toi truyen `da_dich=True` va quet
            # ra 351/1169 phep do "vuot MDE", Sharpe len toi **5,813** cho
            # `2nentang_buy` ("mua khi 2 nen tang lien tiep") tren SP500 D1.
            # Mot luat tam thuong khong the cho Sharpe 5,8 tren 15.763 nen -
            # do la dau hieu duy nhat can de biet ket qua la rac. Dung luat so 1
            # cua CLAUDE.md, va la bai hoc dat nhat cua du an.
            kq = B.do_bien(d, np.asarray(vi_the, dtype=float), c,
                           cac_don_bay=(1.0,), co_tuc=False,
                           ma=ma, khung=khung, da_dich=False)[0][0]
        except Exception as e:
            ra.append({"tu": cs["tu"], "den": cs["den"], "so_bar": cs["so_bar"],
                       "loi": f"{type(e).__name__}: {str(e)[:70]}"})
            continue
        ra.append({"tu": cs["tu"], "den": cs["den"], "so_bar": cs["so_bar"],
                   "sharpe": kq.get("sharpe"), "cagr": kq.get("cagr"),
                   "maxdd": kq.get("maxdd"), "calmar": kq.get("calmar")})
    return {"ma": ma, "khung": khung, "thoi_dai": ra, "gop": gop_sharpe(ra)}


def loi_the_do_dai(ma: str, khung: str = "D1") -> dict:
    """Gop het cua so sach thi duoc them bao nhieu do nhay so voi lay MOT cua so?

    Tra ca hai so + he so giam MDE (~sqrt(ty le so nen)).
    """
    cs = cac_cua_so_sach(ma, khung)
    if not cs:
        return {"ma": ma, "khung": khung, "cua_so": 0}
    tong = sum(c["so_bar"] for c in cs)
    dai_nhat = max(c["so_bar"] for c in cs)
    return {"ma": ma, "khung": khung, "cua_so": len(cs),
            "bar_neu_lay_mot": dai_nhat, "bar_neu_gop_het": tong,
            "he_so_bar": round(tong / max(dai_nhat, 1), 2),
            "he_so_giam_mde": round((tong / max(dai_nhat, 1)) ** 0.5, 2),
            "chi_tiet": [{"tu": c["tu"], "den": c["den"], "bar": c["so_bar"]}
                         for c in cs]}
