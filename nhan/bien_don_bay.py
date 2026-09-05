# -*- coding: utf-8 -*-
"""bien_don_bay.py - BIEN DON BAY. Don bay bao nhieu, va no tra ve duoc gi.

Cau hoi cua chu du an 03/09/2026: "toi uu nhip tang va don bay de huong toi
20-30 %/nam tren US500CASH".

Cau tra loi khong nam o viec thu tung muc don bay. No la mot dang thuc:

    CAGR(L) ~ L*(muy + co_tuc - tai_tro) - 0,5*L^2*sigma^2

    -> L toi uu   = (muy + co_tuc - tai_tro) / sigma^2 = S / sigma
    -> CAGR toi da = 0,5 * S^2          voi S la SHARPE SAU PHI TAI TRO

Dieu nay co mot he qua ma khong bao nhieu don bay cuu duoc:
**tran lai suat cua mot he chi phu thuoc vao SHARPE cua no, khong phu thuoc
vao viec ta san sang vay bao nhieu.** Don bay chi dua ta DOC THEO duong cong
den dinh roi keo nguoc xuong. Muon 25 %/nam thi phai co S ~ 0,71 o don bay
toan Kelly (sut giam ~ -95%, khong ai ngoi duoc), hoac S ~ 0,82 o nua Kelly.

Nen quy trinh dung la NGUOC voi truc giac:
  1. do S sau phi that,
  2. suy ra tran,
  3. neu tran < muc tieu thi KHONG co muc don bay nao dat duoc - phai sua
     CO CHE chu khong sua don bay.

`0,5*S^2` la chan TREN ly thuyet (gia dinh loi suat i.i.d. chuan). Loi suat
that co duoi beo va tu tuong quan, nen so do CON LAC QUAN. Ham `do_bien()`
chay engine that de lay so thuc te.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import chi_phi as CP
from . import do_luong as DL
from . import mo_phong as MP
from . import tai_tro as TT


# --------------------------------------------------------------- DANG THUC
def tran_cagr(sharpe: float, phan_kelly: float = 1.0) -> float:
    """CAGR toi da dat duoc o BAT KY don bay nao, voi mot Sharpe cho truoc."""
    k = float(phan_kelly)
    return float(sharpe) ** 2 * (k - 0.5 * k * k)


def sharpe_can(muc_tieu: float, phan_kelly: float = 1.0) -> float:
    """Sharpe toi thieu de mot muc tieu CAGR la KHA THI (o don bay tot nhat)."""
    k = float(phan_kelly)
    he = k - 0.5 * k * k
    if he <= 0:
        return float("inf")
    return float(np.sqrt(muc_tieu / he))


def don_bay_kelly(sharpe: float, sigma: float, phan_kelly: float = 1.0) -> float:
    """Don bay toi uu = S/sigma, nhan phan Kelly muon dung."""
    return float(phan_kelly) * float(sharpe) / float(sigma)


# ------------------------------------------------------------------- DO THAT
def _chi_so(kq: MP.KetQua) -> dict:
    v = kq.von
    idx = kq.index
    nam = max((idx[-1] - idx[0]).days / 365.25, 1e-9)
    bar_nam = DL.bar_moi_nam(idx)
    loi = np.nan_to_num(kq.loi)
    if kq.chay_tai_khoan or v[-1] <= 0:
        cagr = -1.0
    else:
        cagr = float(v[-1] ** (1.0 / nam) - 1.0)
    # SHARPE PHAI TINH TREN LOI SUAT SO HOC, khong phai log. Kelly va tran
    # 0,5*S^2 deu dinh nghia tren muy SO HOC; muy_log = muy_so_hoc - 0,5*sigma^2
    # nen dung log se HA THAP tran. Do that 03/09/2026 tren chuoi i.i.d.:
    # tran do duoc 25,5% nhung cong thuc voi Sharpe log chi bao 20,2%.
    sh = np.expm1(loi)
    sd = float(np.std(sh, ddof=1))
    vol = sd * np.sqrt(bar_nam)
    sharpe = float(np.mean(sh) / sd * np.sqrt(bar_nam)) if sd > 0 else 0.0
    sd_log = float(np.std(loi, ddof=1))
    sharpe_log = float(np.mean(loi) / sd_log * np.sqrt(bar_nam)) if sd_log > 0 else 0.0
    dinh = np.maximum.accumulate(np.maximum(v, 1e-300))
    dd = float((v / dinh - 1.0).min())
    return {"cagr": cagr, "vol": vol, "sharpe": sharpe, "sharpe_log": sharpe_log,
            "maxdd": dd,
            "calmar": (cagr / abs(dd)) if dd < 0 else float("inf"),
            "chay": bool(kq.chay_tai_khoan), "ngay_chay": kq.ngay_chay,
            "phoi_nhiem": kq.phoi_nhiem}


def do_bien(df: pd.DataFrame, tin_hieu, cp: CP.MoHinhChiPhi,
            cac_don_bay=(1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0),
            co_tuc: bool = True, ma: str = "", khung: str = "D1",
            da_dich: bool = False) -> tuple[list[dict], str]:
    """Chay engine that o tung muc don bay. Tra (cac hang, do_tin).

    `co_tuc=True`: cong dieu chinh co tum vao loi suat tai san (dung cho CFD
    chi so CASH, noi san tra co tuc rieng cho lenh mua). Voi FX -> de False.
    """
    idx = df.index
    ls, t1 = TT.lai_suat_nam(idx)
    do_tin = t1
    d = df
    if co_tuc:
        ct, t2 = TT.co_tuc_nam(idx)
        do_tin = "DO" if (t1 == "DO" and t2 == "DO") else "KHAI"
        ngay = CP.hinh_hoc(idx)[0]
        # cong co tuc vao GIA: dung mot chuoi "tong loi suat" tong hop
        he = np.exp(np.cumsum(ct * ngay / 365.0))
        d = df.copy()
        for c in ("open", "high", "low", "close"):
            if c in d.columns:
                d[c] = d[c].to_numpy(float) * he
    ra = []
    for L in cac_don_bay:
        kq = MP.chay(d, tin_hieu, cp, lai_suat_nam=ls, ma=ma, khung=khung,
                     da_dich=da_dich, don_bay=float(L), gop="so_hoc")
        h = _chi_so(kq)
        h["don_bay"] = float(L)
        ra.append(h)
    return ra, do_tin


# ------------------------------------------------ LUAT VON ("giao dich linh hoat")
#: Bao nhieu bar nghi sau khi cham chan sut giam. Mot thang giao dich.
NGHI_SAU_CHAN = 21
#: Bao nhieu bar mot ky rut lai. Mot quy giao dich.
BAR_MOI_KY = 63


def ap_luat_von(loi_log, so_nam: float, chan_dd: float | None = None,
                rut_ky: float = 0.0, nghi_bar: int = NGHI_SAU_CHAN,
                bar_moi_ky: int = BAR_MOI_KY) -> dict:
    """Ap luat quan tri VON len chuoi loi suat cua he. Khong doi tin hieu.

    Chu du an 04/09: *"neu he ra tien ta se nhay ra truoc khi sap hoac dung lai
    da cashout"*. Y do chi do duoc khi no la LUAT, nen o day co dung hai luat:

      `chan_dd`  thoat het khi tai khoan sut qua X% tu dinh, nghi `nghi_bar`
                 bar roi vao lai. Dat lai dinh khi thoat - neu khong thi
                 tai khoan cham chan mot lan roi thoat lien tuc mai.
      `rut_ky`   moi `bar_moi_ky` bar, rut ra tui `rut_ky` phan cua lai vuot
                 von goc. Tien ra khoi tai khoan nen **sut giam tren VON CA
                 NHAN khac han sut giam tren TAI KHOAN** - do la ca diem cua no.

    `loi_log` la chuoi loi suat LOG cua `mo_phong.KetQua.loi`. Phai `expm1` ve
    so hoc truoc khi gop bang `(1+r)`: gop log truc tiep la loi da ghi trong
    bo nho du an ("don bay gop log la SAI") va no thoi ket qua len nhieu lan.

    KHONG lam: bom von ngoai vao cuu tai khoan. Do khong phai luat giao dich,
    do la chuyen lo giao dich thanh lo doi song.
    """
    r = np.expm1(np.nan_to_num(np.asarray(loi_log, float)))
    tk, tui, goc = 1.0, 0.0, 1.0
    # BA cai dinh khac nhau, va lan dau viet chi co hai nen ket qua doc sai
    # (do 05/09). `dinh_lam_viec` BI DAT LAI moi lan cham chan - phai vay,
    # neu khong thi cham mot lan la thoat lien tuc mai. Nhung dung chinh no de
    # bao sut giam thi con so ra la "sut giam KE TU LAN DAT LAI GAN NHAT", va
    # no lam luat chan trong nhu cat sut giam tu -54% xuong -32% trong khi
    # duong von khong he doi. Sut giam THAT phai do tren dinh khong dat lai.
    dinh_lam_viec = dinh_tk = dinh_tong = 1.0
    dd_tk = dd_tong = 0.0
    nghi = 0
    so_lan_chan = 0
    for i in range(len(r)):
        if nghi > 0:
            nghi -= 1
        else:
            tk *= (1.0 + r[i])
        if tk <= 0:
            return {"vo": True, "so_lan_chan": so_lan_chan}
        dinh_lam_viec = max(dinh_lam_viec, tk)
        dinh_tk = max(dinh_tk, tk)
        dd_tk = min(dd_tk, tk / dinh_tk - 1.0)
        tong = tk + tui
        dinh_tong = max(dinh_tong, tong)
        dd_tong = min(dd_tong, tong / dinh_tong - 1.0)
        if chan_dd is not None and nghi == 0                 and (tk / dinh_lam_viec - 1.0) <= -chan_dd:
            nghi = nghi_bar
            dinh_lam_viec = tk
            so_lan_chan += 1
        if rut_ky > 0 and i and i % bar_moi_ky == 0 and tk > goc:
            lay = (tk - goc) * rut_ky
            tk -= lay
            tui += lay
    tong = tk + tui
    return {"vo": False, "tai_khoan_cuoi": round(tk, 4),
            "da_rut": round(tui, 4), "tong_cuoi": round(tong, 4),
            "cagr": round(tong ** (1.0 / so_nam) - 1.0, 4) if so_nam > 0 else None,
            "dd_tai_khoan": round(dd_tk, 4), "dd_von_ca_nhan": round(dd_tong, 4),
            "so_lan_chan": so_lan_chan}
