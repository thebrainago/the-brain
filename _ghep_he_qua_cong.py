# -*- coding: utf-8 -*-
"""_ghep_he_qua_cong.py - GHEP cac he/quan tri thanh danh muc, do o CUNG RUI RO.

## Vi sao huong nay

Moi thu do rieng le hom nay deu ra ~0 hoac am: 11 ho quan tri tren he co edge
(moi ho am o trung vi), PMG luoi khong entry (~0), trailing tren vang (chet o
nua sau). Con mot huong chua dung toi, va no la huong chinh du an DO DUOC la
manh nhat:

    ban giao 13/09 muc 8.6: "ghep co che (chan mua + chan ban) - **do duoc la
    song tot nhat**: he don qua holdout 822->40, cap ghep giu hang 39/45; 129
    co che am dao chieu thanh 38 duong"
    va muc 10: "ghep chan AM re hon ghep chan manh - 6,14% -> 20,25%/nam o
    CUNG sut giam"

Li do toan hoc: sut giam KHONG cong tuyen tinh. Hai chan moi chan sut giam 10%
nhung lech pha thi ghep lai sut giam < 20%, trong khi lai thi cong du. Quy ve
cung ngan sach rui ro, cai chenh do bien thanh tien.

## Cach lam - KHONG mo phong lai

Giu CHUOI LOI SUAT theo bar cua tung chan roi cong vector. Mot cap la mot phep
cong, khong phai mot lan backtest. Nho vay do duoc hang nghin cap trong vai giay.

## Hai chot khong duoc bo

1. **Cung luoi thoi gian, NHUNG KHONG DUOC LAM THO.** Cac chan o khac tai san va
   khac khung (AUDCAD H4, US500CASH D1...) nen phai dua ve mot luoi chung. Cam
   gop ve NGAY roi moi do: gop lam mat cac cu sut TRONG ngay, sut giam do duoc
   nho di, va phep quy ve "cung 20% sut giam" phat don bay lon hon su that.

   Do 14/09, cung he AUDCAD.H4.rsi_dao_chieu, cung ky 2021-03..2026-07:
       do tren bar H4 goc   L = 1,99   CAGR@dd20 =  -2,01%
       gop ve NGAY roi do   L = 6,09   CAGR@dd20 = +20,66%
   Chenh 22 diem %/nam, va toan bo tu mot buoc resample.

   Nen: dua het ve UNION CUA MOC THOI GIAN GOC (reindex + dien 0), giu nguyen
   do phan giai cua tung chan.
2. **Cat 60/40 truoc khi chon.** Chon cap tren toan bo mau roi khoe so la tu lua:
   voi N chan co N*(N-1)/2 cap, cuc dai ngau nhien rat dep. Chon tren nua dau,
   bao cao nua sau.

Chay:  python _ghep_he_qua_cong.py
"""
from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import chi_phi as CP          # noqa: E402
from nhan import dap_quan_tri as DQ     # noqa: E402
from nhan import du_lieu as DU          # noqa: E402
from nhan import vao_lenh as VL         # noqa: E402
import _qt_tren_he_that as T            # noqa: E402
from _quet_quan_tri_python import SL_CUNG, GIU_TOI_DA  # noqa: E402

NGAN_SACH_DD = 0.20


def _luoi_chan(giu_goc: int) -> dict:
    """Moc goc + mot so lop quan tri. Moi cai la mot CHAN co the ghep."""
    ra = {"goc": {"thoat_bar": giu_goc}}
    for x in (1.0, 2.0):
        ra["tp%.0f" % x] = {"sl_atr": SL_CUNG, "tp_atr": x}
        ra["trail%.0f" % x] = {"sl_atr": SL_CUNG, "trail_tu_atr": x, "trail_buoc": x}
    ra["hue1"] = {"sl_atr": SL_CUNG, "hue_tu_atr": 1.0}
    return ra


def cac_chan(in_ra=print) -> dict[str, pd.Series]:
    """-> {ten chan: chuoi loi suat NGAY (rong, da tru phi)}"""
    ra: dict[str, pd.Series] = {}
    for he in T.he_da_qua_cong():
        ma, khung = he["ma"], he["khung"]
        try:
            df = DU.nap(ma, khung)
        except Exception:
            continue
        th = T.tin_hieu_cua(he, df, in_ra=lambda *a: None)
        if th is None:
            continue
        cp = CP.tu_du_lieu(ma, df)
        c = cp[0] if isinstance(cp, tuple) else cp
        giu = int(he["tham_so"].get("giu", 20) or 20)
        for nhan, luat in _luoi_chan(giu).items():
            try:
                r = DQ.dap(df, th, luat, giu_toi_da=max(giu, GIU_TOI_DA))
                if r["so_lenh"] < 15:
                    continue
                kq = VL.tinh_tien(df, r, c, ma=ma, khung=khung)
            except Exception:
                continue
            # loi suat RONG theo bar -> gop ve NGAY. Khong gop thi cong nham
            # chuoi H4 voi chuoi D1.
            #
            # `kq.loi` la LOI SUAT LOG. Cong log trong mot ngay thi dung (log
            # cong duoc), nhung sau do phai DOI SANG LOI SUAT THUONG truoc khi
            # nhan don bay: don bay tac dong len loi suat THUC, khong len log.
            # Bo buoc doi nay thi `cumprod(1 + L*log_r)` sai dan theo L - o L=5
            # no thoi ket qua len nhieu lan. Chinh la bay "don bay gop bang log
            # la SAI" da ghi trong so tay du an.
            s = pd.Series(np.asarray(kq.loi, float), index=df.index)
            s = np.expm1(s[np.isfinite(s)])      # log -> loi suat thuong
            if s.abs().sum() <= 0:
                continue
            ra[f"{ma}.{khung}.{he['template']}|{nhan}"] = s
        in_ra(f"  {ma}.{khung}.{he['template']}: {sum(1 for k in ra if k.startswith(ma))} chan")
    return ra


def gop_luoi(chan: dict) -> pd.DataFrame:
    """Dua cac chan ve UNION moc thoi gian goc, KHONG lam tho.

    Reindex + dien 0 (khong co vi the thi loi suat bang 0). Giu nguyen do phan
    giai cua tung chan nen sut giam do duoc van la sut giam THAT.
    """
    idx = None
    for s in chan.values():
        idx = s.index if idx is None else idx.union(s.index)
    idx = idx.sort_values()
    return pd.DataFrame({k: v.reindex(idx).fillna(0.0) for k, v in chan.items()},
                        index=idx)


def _chi_so(v: np.ndarray, so_nam: float, dd_muc: float = NGAN_SACH_DD) -> dict:
    """Nang don bay den khi sut giam cham `dd_muc`, roi hoi lai moi nam bao nhieu."""
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if len(v) < 200 or so_nam <= 0:
        return {"lai_nam": float("nan"), "don_bay": 0.0, "dd": 0.0}

    def thu(L):
        e = np.cumprod(1.0 + L * v)
        if (e <= 0).any():
            return None, 1.0
        return float(e[-1]), float(1.0 - (e / np.maximum.accumulate(e)).min())

    lo, hi = 0.0, 50.0
    for _ in range(36):
        g = (lo + hi) / 2
        if thu(g)[1] > dd_muc:
            hi = g
        else:
            lo = g
    cuoi, dd = thu(lo)
    if cuoi is None or lo <= 1e-9:
        return {"lai_nam": float("nan"), "don_bay": 0.0, "dd": dd}
    return {"lai_nam": cuoi ** (1.0 / so_nam) - 1.0, "don_bay": lo, "dd": dd}


def main() -> int:
    t0 = time.time()
    print("dung cac CHAN tu he da qua cong...")
    chan = cac_chan()
    if len(chan) < 2:
        print("khong du chan de ghep")
        return 1
    bang = pd.DataFrame(chan).fillna(0.0).sort_index()
    print(f"\n{bang.shape[1]} chan · {bang.shape[0]} ngay "
          f"({bang.index[0].date()} .. {bang.index[-1].date()})")

    cat = int(len(bang) * 0.6)
    tr, ho = bang.iloc[:cat], bang.iloc[cat:]
    nam_tr = (tr.index[-1] - tr.index[0]).days / 365.25
    nam_ho = (ho.index[-1] - ho.index[0]).days / 365.25

    don = {c: _chi_so(tr[c].to_numpy(), nam_tr) for c in bang.columns}
    tot_don = sorted(don.items(), key=lambda x: -(x[1]["lai_nam"] or -9))
    print(f"\nCHAN DON tot nhat tren NUA DAU:")
    for c, d in tot_don[:6]:
        h = _chi_so(ho[c].to_numpy(), nam_ho)
        print(f"  {c:<52}{d['lai_nam']*100:>7.2f}%  -> nua sau {h['lai_nam']*100:>7.2f}%")

    # ---- ghep 2 va 3 chan, trong so bang nhau. Chon tren NUA DAU.
    cot = list(bang.columns)
    kq = []
    for k in (2, 3):
        for bo in itertools.combinations(cot, k):
            v = tr[list(bo)].mean(axis=1).to_numpy()
            d = _chi_so(v, nam_tr)
            if np.isfinite(d["lai_nam"]):
                kq.append((d["lai_nam"], bo, d))
    kq.sort(reverse=True, key=lambda x: x[0])
    print(f"\n{len(kq)} to hop 2-3 chan da thu")

    print(f"\n{'':4}{'lai/nam NUA DAU':>16}{'NUA SAU':>12}{'don bay':>9}  cac chan")
    print("-" * 110)
    song = []
    for lai_tr, bo, d in kq[:25]:
        v_ho = ho[list(bo)].mean(axis=1).to_numpy()
        h = _chi_so(v_ho, nam_ho)
        if np.isfinite(h["lai_nam"]) and h["lai_nam"] > 0:
            song.append((h["lai_nam"], lai_tr, bo, h))
        ten = " + ".join(x.split(".")[0] + "." + x.split("|")[-1] for x in bo)
        print(f"{'':4}{lai_tr*100:>15.2f}%{h['lai_nam']*100:>11.2f}%"
              f"{d['don_bay']:>9.2f}  {ten[:70]}")

    print(f"\n{len(song)}/25 to hop dau bang CON DUONG o nua sau")
    if song:
        song.sort(reverse=True)
        print("\nTO HOP DUONG CA HAI NUA:")
        for lai_ho, lai_tr, bo, h in song[:8]:
            print(f"  nua dau {lai_tr*100:>6.2f}%  nua sau {lai_ho*100:>6.2f}%  "
                  f"don bay {h['don_bay']:.2f}  sut giam {h['dd']*100:.1f}%")
            for x in bo:
                print(f"      {x}")

    ra = {"so_chan": bang.shape[1], "so_ngay": bang.shape[0],
          "so_to_hop": len(kq), "giay": round(time.time() - t0, 1),
          "dau_bang": [{"chan": list(bo), "lai_nua_dau": round(l * 100, 3),
                        "don_bay": round(d["don_bay"], 3)} for l, bo, d in kq[:60]]}
    (LAB / "reports" / "GHEP_HE_QUA_CONG.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n-> reports/GHEP_HE_QUA_CONG.json ({ra['giay']:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
