# -*- coding: utf-8 -*-
"""TANG 3 - tinh von va ket hop cac gia thuyet da qua cong.

Truoc 21/08/2026 `lab` KHONG co tang nay. SEEKER thu thap, QUANTLAB kiem dinh,
BANKER doc vi mo - va het. Khong module nao tra loi duoc cau hoi cuoi: *co ba
chien luoc qua cong roi thi bo bao nhieu tien vao moi cai, va ghep lai co hon
tung cai rieng khong?*

Bon nguyen tac, ba trong so do la bai hoc da tra gia trong du an nay:

1. **Tuong quan DUOI moi la thu dang so.** Hai chien luoc co tuong quan trung
   binh 0,1 van co the cung sap trong dung tuan ta can chung nhat. Ta gom cum
   theo tuong quan trong thap phan vi xau nhat, khong theo tuong quan chung.

2. **Chi phi CO DINH quyet dinh o quy mo nho.** Da do that: chan giao dich lai
   9,9%/nam nhung o muc von 6-18 trieu thi rieng tien VPS da lon hon toan bo
   lai gop -> lai rong AM. Vi vay module nay LUON bao "can bao nhieu von thi
   chi phi co dinh moi duoi X% loi nhuan ky vong", chu khong chi bao %/nam.

3. **Moc mua-giu la bat buoc va phai co phi.** Mot danh muc khong hon duoc
   mua-giu thi no khong phai thanh tuu, no la mot cach phuc tap de thua.

4. **Khong tu dat lenh.** Module nay tinh va bao cao. Quyet dinh von la cua
   nguoi.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from nhan import chi_phi as CP
from nhan import do_luong as DO
from nhan import du_lieu as DL
from nhan import mau as MAU
from nhan import mo_phong as MP
from nhan import so as SO

#: Phan vi duoi dung de do tuong quan duoi. 0,10 = thap phan vi xau nhat.
PHAN_VI_DUOI = 0.10
#: Hai chien luoc co tuong quan duoi >= muc nay bi coi la CUNG MOT cum rui ro.
NGUONG_CUM = 0.30
#: Tran rui ro cho mot cum. Vuot muc nay thi phai ha ty trong.
TRAN_RUI_RO_CUM = 0.15
#: Chi phi co dinh moi nam (VPS + du lieu), don vi tien tai khoan.
CHI_PHI_CO_DINH_NAM = 1_560_000.0 / 25_000.0     # ~5,1tr/3,25 nam quy ve USD/nam
#: Nguong "chi phi co dinh an bao nhieu phan loi nhuan thi coi la khong dang".
TRAN_CHI_PHI_CO_DINH = 0.20


@dataclass
class ThanhPhan:
    """Mot chien luoc trong danh muc."""
    ma: str
    tai_san: str
    khung: str
    template: str
    ho: str
    loi: np.ndarray = field(repr=False)
    index: pd.DatetimeIndex = field(repr=False)
    chi_so: dict = field(default_factory=dict)

    @property
    def sharpe(self) -> float:
        return float(self.chi_so.get("sharpe") or 0.0)


# ------------------------------------------------------------------ NAP CHUOI

def nap_chuoi(gt_ma: str, tren_holdout: bool = True) -> ThanhPhan | None:
    """Dung lai chuoi loi nhuan cua mot gia thuyet DA DANG KY.

    Khong doc tu bao cao cu: chay lai ke hoach da dong bang tren dung phan vung
    de chuoi va chi so luon khop voi engine hien tai.
    """
    gt = SO.mot("SELECT * FROM gia_thuyet WHERE ma=?", gt_ma)
    if gt is None:
        return None
    import json
    tham_so = json.loads(gt["tham_so"] or "{}")
    try:
        df = DL.nap(gt["tai_san"], gt["khung"])
    except Exception:
        return None
    train, hold = DL.hai_nua(df, 0.6)
    phan = hold if tren_holdout else train
    if len(phan) < 100:
        return None
    cp = CP.tu_du_lieu(gt["tai_san"], phan)
    try:
        tin_hieu = MAU.sinh(gt["template"], phan, tham_so)
    except Exception:
        return None
    kq = MP.chay(phan, tin_hieu, cp, ma=gt["tai_san"], khung=gt["khung"])
    return ThanhPhan(
        ma=gt_ma, tai_san=gt["tai_san"], khung=gt["khung"],
        template=gt["template"], ho=gt["ho"] or "",
        loi=np.asarray(kq.loi, dtype=float), index=phan.index,
        chi_so=DO.chi_so(kq.loi, phan.index, kq.vi_the))


def gong_chuoi(cac_tp: list[ThanhPhan]) -> pd.DataFrame:
    """Gong cac chuoi ve CUNG moc thoi gian.

    Bat buoc: mot chuoi bat dau 2013 va mot chuoi bat dau 2017 ma cat theo vi
    tri thi lech hang gia ma khong bao loi (CLAUDE.md muc 51).
    """
    if not cac_tp:
        return pd.DataFrame()
    # Kho co ca bang tz-naive lan tz=UTC; `pd.concat` hai loai nay nem
    # TypeError. Chuan hoa truoc, va chi khi CUNG luoi gio (xem du_lieu).
    bang = {tp.ma: pd.Series(tp.loi, index=DL.chuan_hoa_index(tp.index))
            for tp in cac_tp}
    return pd.concat(bang, axis=1).dropna(how="all").fillna(0.0)


# --------------------------------------------------------- TUONG QUAN DUOI

def tuong_quan_duoi(bang: pd.DataFrame, phan_vi: float = PHAN_VI_DUOI) -> pd.DataFrame:
    """Do PHU THUOC DUOI: hai chien luoc co hay cung sap trong cung mot ngay.

    Tuong quan trung binh noi rat it ve rui ro chung: cai giet tai khoan la hai
    chien luoc cung am trong cung mot tuan.

    CACH DO SAI ma ban dau toi viet: loc nhung bar co TONG loi nhuan trong thap
    phan vi xau nhat roi tinh corr tren phan do. Do la thien lech collider -
    dieu kien hoa tren mot ham cua chinh hai bien can so se TU CHE ra tuong
    quan. Do that: hai chuoi ngau nhien DOC LAP cho ra 0,685. Mot thuoc do bao
    "moi cap deu tuong quan cao" thi vo dung y nhu mot thuoc do luon bao 0.

    Cach dung o day: moi chuoi tu xet thap phan vi cua RIENG no, roi dem ty le
    cung roi vao duoi. Chuan hoa de doc duoc ngay:
        doc lap  -> ~1,0   (dung bang ngau nhien)
        y het    ->  ~10   (voi phan_vi = 0,10, tuc 1/phan_vi)
    Chia tiep cho 1/phan_vi de dua ve thang [0, 1]: doc lap ~0,10, y het 1,00.
    """
    if bang.empty or bang.shape[1] < 2:
        return pd.DataFrame()
    ten = list(bang.columns)
    X = bang.to_numpy(dtype=float)
    if len(X) < 20:
        return pd.DataFrame(np.eye(len(ten)), index=ten, columns=ten)

    # Moi cot tu xet nguong cua RIENG no - khong dung thong tin cua cot khac.
    nguong = np.quantile(X, phan_vi, axis=0)
    duoi = X <= nguong                       # ma tran bool: bar x chien luoc
    n = len(X)
    ky_vong = phan_vi * phan_vi              # ty le cung duoi neu doc lap
    ra = np.eye(len(ten))
    for i in range(len(ten)):
        for j in range(i + 1, len(ten)):
            cung = float(np.sum(duoi[:, i] & duoi[:, j])) / n
            # cung/ky_vong: 1 = doc lap, 1/phan_vi = trung hoan toan.
            gia_tri = (cung / ky_vong) * phan_vi if ky_vong > 0 else 0.0
            ra[i, j] = ra[j, i] = float(min(1.0, max(0.0, gia_tri)))
    return pd.DataFrame(ra, index=ten, columns=ten)


def gom_cum(tq: pd.DataFrame, nguong: float = NGUONG_CUM) -> list[list[str]]:
    """Gom cac chien luoc co tuong quan duoi cao vao cung mot cum rui ro."""
    if tq.empty:
        return []
    ten = list(tq.columns)
    cha = {t: t for t in ten}

    def goc(x):
        while cha[x] != x:
            cha[x] = cha[cha[x]]
            x = cha[x]
        return x

    for i, a in enumerate(ten):
        for b in ten[i + 1:]:
            if float(tq.loc[a, b]) >= nguong:
                ga, gb = goc(a), goc(b)
                if ga != gb:
                    cha[gb] = ga
    cum: dict[str, list[str]] = {}
    for t in ten:
        cum.setdefault(goc(t), []).append(t)
    return [sorted(v) for v in sorted(cum.values(), key=lambda x: -len(x))]


# ------------------------------------------------------------- PHAN BO VON

def phan_bo(cac_tp: list[ThanhPhan], cum: list[list[str]],
            tran_cum: float = TRAN_RUI_RO_CUM) -> dict[str, float]:
    """Ty trong rui ro moi chien luoc, co tran theo cum.

    Trong mot cum, chia deu - KHONG chia theo Sharpe quan sat duoc. Chia theo
    Sharpe la mot dang tiep tuc toi uu tren cung du lieu da dung de chon, va no
    lam nang tay dung cai may man nhat.
    """
    theo_ma = {tp.ma: tp for tp in cac_tp}
    ty_trong: dict[str, float] = {}
    for nhom in cum:
        song = [m for m in nhom if m in theo_ma]
        if not song:
            continue
        moi_cum = min(tran_cum, 1.0 / max(len(cum), 1))
        for m in song:
            ty_trong[m] = moi_cum / len(song)
    tong = sum(ty_trong.values())
    if tong > 1.0:
        ty_trong = {k: v / tong for k, v in ty_trong.items()}
    return ty_trong


def von_toi_thieu(loi_ky_vong_nam: float,
                  chi_phi_co_dinh: float = CHI_PHI_CO_DINH_NAM,
                  tran: float = TRAN_CHI_PHI_CO_DINH) -> float | None:
    """Von toi thieu de chi phi CO DINH duoi `tran` phan loi nhuan ky vong.

    Da do that trong du an: o muc von 6-18 trieu, rieng tien VPS lon hon toan
    bo lai gop cua mot chan giao dich lai 9,9%/nam. Bao %/nam ma khong bao con
    so nay la bao thieu nua su that.
    """
    if loi_ky_vong_nam <= 0 or tran <= 0:
        return None
    return float(chi_phi_co_dinh / (tran * loi_ky_vong_nam))


# ------------------------------------------------------------------ TONG HOP

def ghep(cac_tp: list[ThanhPhan], *, moc_mua_giu: np.ndarray | None = None,
         index_moc: pd.DatetimeIndex | None = None) -> dict:
    """Ghep danh muc va do no. Luon kem moc mua-giu."""
    if not cac_tp:
        return {"n": 0, "ly_do": "khong co thanh phan nao"}

    bang = gong_chuoi(cac_tp)
    tq = tuong_quan_duoi(bang)
    cum = gom_cum(tq) or [[tp.ma] for tp in cac_tp]
    ty_trong = phan_bo(cac_tp, cum)

    loi_dm = sum(bang[m] * w for m, w in ty_trong.items() if m in bang)
    if isinstance(loi_dm, (int, float)):
        return {"n": len(cac_tp), "ly_do": "khong phan bo duoc ty trong nao"}
    cs = DO.chi_so(loi_dm.to_numpy(), bang.index)

    rieng = {tp.ma: {"sharpe": tp.sharpe,
                     "tong_lai_pct": tp.chi_so.get("tong_lai_pct"),
                     "ty_trong": round(ty_trong.get(tp.ma, 0.0), 4)}
             for tp in cac_tp}
    sharpe_tot_nhat = max((tp.sharpe for tp in cac_tp), default=0.0)

    ra = {
        "n": len(cac_tp),
        "so_cum": len(cum),
        "cum": cum,
        "tuong_quan_duoi_lon_nhat": (
            float(np.max(np.abs(tq.to_numpy() - np.eye(len(tq)))))
            if len(tq) > 1 else 0.0),
        "ty_trong": ty_trong,
        "tong_ty_trong": round(sum(ty_trong.values()), 4),
        "danh_muc": cs,
        "rieng_le": rieng,
        "sharpe_tot_nhat_rieng_le": sharpe_tot_nhat,
        "ghep_co_hon_cai_tot_nhat": bool((cs.get("sharpe") or -9) > sharpe_tot_nhat),
    }

    # Moc mua-giu la BAT BUOC. Thieu no thi con so %/nam khong noi len gi.
    if moc_mua_giu is not None and index_moc is not None:
        moc = DO.chi_so(np.asarray(moc_mua_giu, dtype=float), index_moc)
        ra["mua_giu"] = moc
        ra["hon_mua_giu"] = bool(
            (cs.get("sharpe") or -9) > (moc.get("sharpe") or 0)
            and (cs.get("tong_lai_pct") or -1e9) > (moc.get("tong_lai_pct") or 0))
    else:
        ra["mua_giu"] = None
        ra["hon_mua_giu"] = None
        ra["canh_bao"] = "chua co moc mua-giu - khong ket luan duoc gi ve %/nam"

    cagr = cs.get("cagr_pct")
    if cagr:
        ra["von_toi_thieu_de_dang_chay"] = von_toi_thieu(float(cagr) / 100.0)
    return ra


def tu_gia_thuyet(cac_ma: list[str], tren_holdout: bool = True) -> dict:
    """Ghep danh muc tu danh sach ma gia thuyet da dang ky."""
    cac_tp = [tp for tp in (nap_chuoi(m, tren_holdout) for m in cac_ma) if tp]
    thieu = sorted(set(cac_ma) - {tp.ma for tp in cac_tp})
    ra = ghep(cac_tp)
    ra["khong_nap_duoc"] = thieu
    return ra


def danh_muc_hien_tai(trang_thai: str = "PASS") -> dict:
    """Danh muc tu cac gia thuyet dang o trang thai da cho."""
    ma = [r["ma"] for r in SO.nhieu(
        "SELECT ma FROM gia_thuyet WHERE trang_thai=? ORDER BY dang_ky_luc", trang_thai)]
    if not ma:
        return {"n": 0, "ly_do": f"khong co gia thuyet nao o trang thai {trang_thai}"}
    ra = tu_gia_thuyet(ma)
    SO.ghi_chi_so("danh_muc_n", ra.get("n", 0), {"trang_thai": trang_thai})
    return ra


if __name__ == "__main__":
    import pprint
    pprint.pprint(danh_muc_hien_tai())
