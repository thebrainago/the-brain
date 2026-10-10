# -*- coding: utf-8 -*-
"""DOI CHUNG NHIEU cho chang KIEM cua vong lap (10/10/2026): "cao nguyen + kiem ngoai mau" tren du lieu CHI CO NHIEU cho ra bao nhieu % 'qua'?

## Vi sao (chu du an: vong lap phai DO duoc tung chang)

May nha dang tra ve ~1.000 ket qua kiem ngoai mau. Mot ty le 'qua' (vd 60%) khong noi gi neu khong biet **tren du lieu khong co loi the
nao ca** ty le do la bao nhieu: lenh luoi / martingale co lech am (nhieu lai nho, hiem khi lo lon) nen xac suat 'co lai va khong chay tai khoan'
tren ~1,7 nam ngoai mau co the cao du KHONG co loi the. Nhan GIU (qua o >= 3 thi truong, >= 50% cua >= 5 ket qua) chi co nghia khi ty le nen
thap hon nhieu.

Module nay chay **chinh duong ong that** (khong viet lai): `nc_thi_nghiem.quet_luoi` (trong mau, cung 9 mau che_do x kieu_lot, cung luoi tham so,
cung engine, cung cach xep CAO_NGUYEN) -> o tot nhat -> `danh_gia_luoi` tren xac_nhan -> o ngau nhien cung luoi (`vong_lap.sinh_ngau_nhien`) ->
cung phep so sanh (`vong_lap.so_sanh_nhom`) -- nhung tren chuoi TONG_HOP co DAP AN: khong loi the (NHIEU, ba muc bien dong), chi co beta (BETA),
quan tinh (XU_HUONG), va ba muc co thanh phan HOI QUY that (DAO_DONG_RAT_YEU / _YEU / DAO_DONG) de biet phep do co NHAY khong.

Ngoai ra moi (chuoi, mau) do them mot MAU o ngau nhien (`so_o_chan_doan`) ca trong mau lan ngoai mau: P(qua ngoai mau | o co lai trong mau) co khac
P(qua | o khong lai) khong? Neu khong, "co lai trong mau" khong du bao gi tren chuoi nay.

## Hai engine

May nha DANG chay ma cu = engine 3 = `khop_bar="cuc_tri"` (lac quan 15-55% o tia lenh); ma moi = engine 4 = `duong_di`. Duong nghien cuu cua lab TU CHOI
`cuc_tri` (de AI khong xep hang bang mo hinh lac quan), nen o DAY cong do duoc go rieng trong tien trinh con va CHI cho chuoi TONG_HOP (khong bao
gio cho ma that) -- chi de biet 1.000 ket qua kiem tu may nha doc nhu the nao. Ket qua that engine 3 chi so voi `NHIEU@e3`, engine 4 voi `NHIEU@e4`.

## Gioi han (nhin ro)

* Chuoi gia (AUDCAD-like, H1, ~9%/nam, spread 1,5 pip, hang so qua dem cua `QC_AUDCAD`): la THUOC DO CO DAP AN cho **co che cua phep do**, khong
  phai mo phong mot thi truong. May nha quet M5/M15/M30/H1 tren 12 thi truong; day moi la khung H1, bien dong 6-12%/nam. Nhieu that tu thi truong
  that (thay the block-bootstrap / dao dau tren chuoi that) can du lieu o may nha: chua lam.
* Cac o cua mot luoi chay tren CUNG MOT duong gia nen tuong quan manh: don vi doc lap la **chuoi gia**, khong phai o. Khoang tin cay gop o day tinh
  theo so chuoi; cac mau cua cung mot chuoi cung tuong quan nen duoc lay trung binh trong chuoi truoc khi gop.
* Khong ghi so tay that: moi tien trinh con dat `NC_DB` / `NC_SO_CAI` ve thu muc tam, `NC_DONG_BANG=0`. Khong cat doan niem_phong cua chuoi nao.
* Ket qua la NHAN canh bao cho nhan GIU, khong phai cong chan (CLAUDE.md: tieu chi duyet la co lai + maxDD < 80%).

Chay: `python3 -m nhan.doi_chung_nhieu --kich-ban NHIEU --so-chuoi 100 --luong 4` ; tong ket lai tu tep: `--tong-ket`.
Ke hoach DONG BANG truoc khi chay + cach doc: `tai_lieu/VONG_LAP.md` muc "Doi chung nhieu".
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import math
import multiprocessing
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

PHIEN_BAN = 1
KHUNG = "H1"
SO_BAR = 54_600                 # 8,75 nam H1: kham_pha 5,25 nam ; xac_nhan 1,75 nam ; niem_phong 1,75 nam (KHONG BAO GIO mo o day)
VON = 10_000.0
TOI_DA_O = 1000                 # san xuat dung 3.000 (xem `kiem_do_trung_thuc`); 1.000 du doc hinh dang va re hon ~3 lan
SO_O_CHAN_DOAN = 150
O_CHAN_DOAN_TOI_THIEU = 5       # moi nhom (co lai / khong lai) can >= 5 o ket luan duoc trong MOT chuoi de tinh chenh cua chuoi do
KHOP_BAR = ("duong_di", "cuc_tri")      # engine 4 ; engine 3 (may nha dang chay ma cu)
ENGINE_CUA = {"duong_di": 4, "cuc_tri": 3}
CHAN_VR = (12, 48, 144, 288)    # chan troi (bar) do variance ratio: loi the hoi quy cham chi hien o chan dai (VR48 cua nua doi 288 gan nhu = 1)
TEP_TONG_KET = LAB / "reports" / "vong_lap" / "doi_chung_nhieu.json"

#: Quy tac doc (DONG BANG trong tai_lieu/VONG_LAP.md truoc khi chay): xem `so_voi_nhieu`
NHIEU_N_TOI_THIEU = 20          # ket qua that ket luan duoc toi thieu truoc khi dam noi 'vuot' / 'duoi' nhieu
NHIEU_CHENH_TOI_THIEU = 0.10    # chenh ty le qua toi thieu so voi nhieu (cung y nghia voi vong_lap.SO_SANH_CHENH_TOI_THIEU)
NHIEU_BAO_HOA = 0.90            # nhieu cung dat >= 90% 'qua': tieu chi QUA khong con phan biet -> doi sang 'qua VA hon mua-giu / ban-giu'

#: Kich ban -> mo ta. `NHIEU_THAP/CAO` = CUNG duong gia cua NHIEU, nhan do bien dong (ghep cap voi NHIEU).
KICH_BAN = {
    "NHIEU": "di bo ngau nhien co cum bien dong (GARCH), khong troi, khong loi the - tham chieu chinh",
    "NHIEU_THAP": "nhu NHIEU, bien dong x0,65 (~5,9%/nam) - cap tien it bien dong",
    "NHIEU_CAO": "nhu NHIEU, bien dong x1,35 (~12%/nam) - cap tien nhieu bien dong",
    "BETA": "nhu NHIEU nhung troi +6%/nam (kieu chi so): he nghieng mua 'co lai' nho beta",
    "XU_HUONG": "quan tinh bac 1 (he so 0,07): luoi nguoc xu huong bi pha",
    "DAO_DONG_RAT_YEU": "hoi quy quanh neo troi, nua doi 288 bar (12 ngay), 10% phuong sai bar: rat yeu",
    "DAO_DONG_YEU": "hoi quy quanh neo troi, nua doi 144 bar (6 ngay), 30% phuong sai bar: yeu",
    "DAO_DONG": "hoi quy quanh neo troi, nua doi 48 bar (2 ngay), 60% phuong sai bar: ro",
}
#: dap an: "khong_co" = khong loi the ; "troi" = chi co beta ; "co_hoi_quy" = co thanh phan hoi quy that (chua noi duoc sau phi la bao nhieu)
LOAI = {"NHIEU": "khong_co", "NHIEU_THAP": "khong_co", "NHIEU_CAO": "khong_co", "XU_HUONG": "khong_co", "BETA": "troi",
        "DAO_DONG_RAT_YEU": "co_hoi_quy", "DAO_DONG_YEU": "co_hoi_quy", "DAO_DONG": "co_hoi_quy"}
#: (nua doi theo bar, ty le phuong sai bar den tu thanh phan hoi quy)
DAO_DONG = {"DAO_DONG_RAT_YEU": (288.0, 0.10), "DAO_DONG_YEU": (144.0, 0.30), "DAO_DONG": (48.0, 0.60)}
HE_SO_BIEN_DONG = {"NHIEU_THAP": 0.65, "NHIEU_CAO": 1.35}

# Hai luoi that cua cac luot quet may nha (do 10/10/2026 tren viec/xong: 1.247 luot quet, 9 mau che_do x kieu_lot, ~96-180 luot moi mau)
_LUOI_PHANG = {"buoc": [8, 10, 12, 16, 20, 24, 30, 36, 45, 60, 80, 100], "cho_lui": [0, 3, 6, 10],
               "tp": [6, 8, 10, 13, 16, 20, 26, 34, 45, 60], "tran_tang": [4, 5, 6, 7, 8, 10, 12, 15]}
_LUOI_NHAN = dict(_LUOI_PHANG, he_so_lot=[0.1, 0.2, 0.3, 0.5, 0.8, 1.2])


def _mau(che_do: str, kieu_lot: str) -> tuple[dict, dict]:
    return ({"che_do": che_do, "kieu_lot": kieu_lot, "lot": 0.01}, _LUOI_PHANG if kieu_lot == "phang" else _LUOI_NHAN)


MAU = {"%s_%s" % (c, k): _mau(c, k) for c in ("mua", "ban", "hai_chieu") for k in ("phang", "cong", "nhan")}
MAU_TEN = tuple(MAU)


# ----------------------------------------------------------------------------------------------- sinh chuoi gia

def _ndl():
    from nhan import nc_du_lieu as NDL
    return NDL


def sinh_dao_dong(hat: int, so_bar: int = SO_BAR, nua_doi: float = 48.0, q: float = 0.6, khung: str = KHUNG, ten: str = "DAO_DONG"):
    """Chuoi OHLC co thanh phan HOI QUY: log gia = neo (di bo ngau nhien) + x, x la AR(1) nua doi `nua_doi` bar chiem `q` phuong sai moi bar.
    Cung do bien dong bar va cung cum bien dong GARCH voi `nc_du_lieu.tong_hop`. Day la loi the ma luoi tham so KHAI THAC duoc (gia dao dong
    quanh mot muc) - dap an dung cho phep do, khong phai mot thi truong."""
    NDL = _ndl()
    import pandas as pd
    n = int(so_bar)
    rng = np.random.default_rng(NDL._hat_kich_ban(str(ten), int(hat)))
    s_bar = 0.09 / math.sqrt(NDL.BAR_MOI_NAM[khung])
    a_g, b_g = 0.06, 0.92
    w_g = s_bar ** 2 * (1.0 - a_g - b_g)
    phi = 0.5 ** (1.0 / float(nua_doi))
    q = float(q)
    sq, sm = math.sqrt(q), math.sqrt(1.0 - q)
    z = rng.standard_normal((n, 2))
    c = np.empty(n)
    s_t = np.empty(n)
    m = x = r_truoc = 0.0
    var = s_bar ** 2
    for t in range(n):
        var = w_g + a_g * r_truoc * r_truoc + b_g * var
        s = math.sqrt(var)
        dm = s * sm * z[t, 0]
        x_moi = phi * x + s * sq * z[t, 1]
        r_truoc = dm + (x_moi - x)
        m += dm
        x = x_moi
        c[t] = m + x
        s_t[t] = s
    o = np.concatenate(([0.0], c[:-1]))                          # khong co khe gia giua hai bar (nhu `tong_hop`)
    k = np.arange(1, 9) / 8.0
    w = np.cumsum(rng.standard_normal((n, 8)), axis=1) / math.sqrt(8.0) * s_t[:, None]
    cau = w - k[None, :] * w[:, -1:]                              # cau Brown: noi o -> c, bien do trong bar = bien dong cua bar
    duong = o[:, None] + (c - o)[:, None] * k[None, :] + cau
    h = np.maximum(o, duong.max(axis=1))
    lo = np.minimum(o, duong.min(axis=1))
    sp = np.clip(15.0 + rng.normal(0.0, 2.0, n), 8.0, 30.0).round()
    df = pd.DataFrame({"open": np.exp(o), "high": np.exp(h), "low": np.exp(lo), "close": np.exp(c),
                       "tick_volume": np.full(n, 1000.0), "spread": sp}, index=NDL._chi_muc(n, khung))
    df.index.name = "time"
    df.attrs["tong_hop"] = {"kich_ban": str(ten), "hat": int(hat), "do_manh": 1.0, "nua_doi": float(nua_doi), "q": q,
                            "dap_an": KICH_BAN.get(str(ten), "hoi quy")}
    return df


def doi_bien_dong(df, he_so: float):
    """Cung duong gia, bien dong x`he_so`: nhan log(gia / gia mo dau) -> giu thu tu open/high/low/close va goc gia. Spread (diem) giu nguyen."""
    ra = df.copy()
    p0 = float(df["open"].iloc[0])
    for cot in ("open", "high", "low", "close"):
        ra[cot] = p0 * np.exp(float(he_so) * np.log(df[cot].to_numpy(float) / p0))
    ra.attrs = dict(df.attrs, he_so_bien_dong=float(he_so))
    return ra


def sinh_chuoi(kb: str, hat: int, so_bar: int = SO_BAR, khung: str = KHUNG):
    kb = str(kb).upper()
    if kb in DAO_DONG:
        nua_doi, q = DAO_DONG[kb]
        return sinh_dao_dong(hat, so_bar, nua_doi, q, khung, ten=kb)
    if kb in HE_SO_BIEN_DONG:
        return doi_bien_dong(_ndl().tong_hop("NHIEU", hat=int(hat), so_bar=int(so_bar), khung=khung), HE_SO_BIEN_DONG[kb])
    if kb in ("NHIEU", "BETA", "XU_HUONG"):
        return _ndl().tong_hop(kb, hat=int(hat), so_bar=int(so_bar), khung=khung)
    raise KeyError("kich ban '%s' khong co (co: %s)" % (kb, ", ".join(KICH_BAN)))


def ten_chuoi(kb: str, hat: int) -> str:
    return "TONG_HOP_%s_%d" % (str(kb).upper(), int(hat))


def ty_so_phuong_sai(dong: np.ndarray, k: int) -> float:
    """Variance ratio VR(k) = Var(loi suat k bar) / (k * Var(loi suat 1 bar)) tren log gia dong cua. ~1 = di bo ngau nhien, < 1 = hoi quy."""
    c = np.log(np.asarray(dong, float))
    r1 = np.diff(c)
    rk = c[k:] - c[:-k]
    return float(np.var(rk, ddof=1) / (k * np.var(r1, ddof=1)))


# ----------------------------------------------------------------------------------------------- mot chuoi

def _kl(trang_thai: str | None) -> str:
    return {"DAT": "QUA", "AM": "RUOT"}.get(str(trang_thai), "KHONG_DO_DUOC")


def _xn(TN, ma: str, khung: str, ts: dict) -> dict:
    """Kiem ngoai mau bang CHINH `danh_gia_luoi` (ham ma `nc cc thu_luoi` goi): QUA = DAT, RUOT = AM, con lai KHONG_DO_DUOC."""
    r = TN.danh_gia_luoi(ma, khung, ts, "xac_nhan", VON)
    tien = r.get("tien") or {}
    ra = {"kl": _kl(r.get("trang_thai")), "ln": tien.get("loi_suat_nam_pct"), "dd": tien.get("maxdd_pct"),
          "o_tran": tien.get("loi_suat_o_tran_pct"), "hon_moc": tien.get("hon_moc_pct"),
          "so_lenh": (r.get("lenh") or {}).get("so_lenh"), "chay": "CHAY TAI KHOAN" in str(r.get("ly_do") or "")}
    if ra["kl"] == "KHONG_DO_DUOC":
        ra["ly_do"] = str(r.get("ly_do") or "")[:100]
    return ra


def _chan_doan(TN, luoi: dict, co_dinh: dict, dl_is, dl_oos, von_q: float, moc_oos: float, so_o: int, hat: int) -> dict:
    """Bang 3x4 tren `so_o` o ngau nhien cua luoi (MOI o chay ca trong mau lan ngoai mau, cung ham `_o_luoi` voi `quet_luoi`):
    hang = trang thai trong mau (lai / khong_lai / khong_do_duoc), cot = ngoai mau [QUA, RUOT, KHONG_DO_DUOC, QUA_HON_MOC]. Tieu chi QUA/RUOT/
    KHONG_DO_DUOC ngoai mau y het `danh_gia_luoi`: chay tai khoan = RUOT ; < LENH_TOI_THIEU lenh = KHONG_DO_DUOC ; lai > 0 = QUA."""
    rng = np.random.default_rng(1_000_003 + int(hat))
    khoa = sorted(luoi)
    bang = {"lai": [0, 0, 0, 0], "khong_lai": [0, 0, 0, 0], "khong_do_duoc": [0, 0, 0, 0]}
    loi = 0
    for _ in range(int(so_o)):
        o = {k: luoi[k][int(rng.integers(len(luoi[k])))] for k in khoa}
        a = TN._o_luoi(dl_is, co_dinh, o, von_q, 0.0)
        b = TN._o_luoi(dl_oos, co_dinh, o, von_q, moc_oos)
        if "loi" in a or "loi" in b:
            loi += 1
            continue
        h = ("lai" if a["co_lai"] else "khong_lai") if a["so_lenh"] >= TN.LENH_TOI_THIEU else "khong_do_duoc"
        if b["chay"]:
            j = 1
        elif b["so_lenh"] < TN.LENH_TOI_THIEU:
            j = 2
        else:
            j = 0 if b["loi_suat_nam_pct"] > 0 else 1
        bang[h][j] += 1
        if j == 0 and b.get("hon_moc_pct") is not None and b["hon_moc_pct"] > 0:
            bang[h][3] += 1
    return {"bang": bang, "loi": loi, "so_o": int(so_o)}


def _chay_mau(TN, VL, ma: str, khung: str, ten: str, khop_bar: str, toi_da_o: int, so_o_cd: int, ngu_canh: dict, hat: int) -> dict:
    co_dinh, luoi = MAU[ten]
    co_dinh = dict(co_dinh)
    if khop_bar != "duong_di":
        co_dinh["khop_bar"] = khop_bar                  # mac dinh engine 4 de TRONG: y het mau san xuat
    t0 = time.time()
    r = TN.quet_luoi(ma, khung, dict(co_dinh), {k: list(v) for k, v in luoi.items()}, VON, toi_da_o=int(toi_da_o))
    ra = {"hinh": r.get("hinh_dang") or "CHUA_DO_DUOC", "so_o": r.get("so_o"), "so_o_do_duoc": r.get("so_o_do_duoc"),
          "so_o_chay_tai_khoan": r.get("so_o_chay_tai_khoan"), "giay_quet": round(time.time() - t0, 2),
          "ty_le_o_co_lai": r.get("ty_le_o_co_lai"), "hang_xom": (r.get("hang_xom") or {}).get("ty_le_co_lai")}
    if r.get("hinh_dang") is None:
        ra["ly_do"] = str(r.get("ly_do") or "")[:140]
        return ra
    tot, ts = r.get("o_tot_nhat"), r.get("tham_so_day_du")
    if tot and ts:
        ra["tot"] = {"tham_so": {k: ts[k] for k in sorted(luoi)}, "o_tran_trong_mau": tot.get("loi_suat_o_tran_pct"),
                     "ln_trong_mau": tot.get("loi_suat_nam_pct")}
        ra["xn_tot"] = _xn(TN, ma, khung, ts)
        u = {"id": VL.id_ung_vien(ma, khung, ts), "ma": ma, "khung": khung, "luoi": luoi, "co_dinh": co_dinh, "von": VON}
        g = VL.sinh_ngau_nhien(u)
        if g:
            ra["xn_ngau"] = _xn(TN, ma, khung, g["tham_so"])
    ra["chan_doan"] = _chan_doan(TN, luoi, co_dinh, ngu_canh["dl_is"], ngu_canh["dl_oos"], ngu_canh["von_q"], ngu_canh["moc_oos"],
                                 so_o_cd, hat)
    return ra


def chay_chuoi(kb: str, hat: int, khop_bar: str = "duong_di", mau_ten=MAU_TEN, toi_da_o: int = TOI_DA_O, so_o_cd: int = SO_O_CHAN_DOAN,
               so_bar: int = SO_BAR, khung: str = KHUNG) -> dict:
    """MOT chuoi gia -> mot ban ghi (moi mau mot muc). Phai goi trong tien trinh da dat NC_DB / NC_SO_CAI (xem `_khoi_tao`) hoac da tro
    `nc_so_tay.DB` sang so tam (test)."""
    from nhan import nc_thi_nghiem as TN, luoi as LU, vong_lap as VL
    NDL = _ndl()
    if khop_bar not in KHOP_BAR:
        raise ValueError("khop_bar phai la mot trong %s" % (KHOP_BAR,))
    t0 = time.time()
    kb = str(kb).upper()
    df = sinh_chuoi(kb, hat, so_bar, khung)
    ma = ten_chuoi(kb, hat)
    t_gen = time.time() - t0
    NDL.dang_ky_tong_hop(ma, khung, df)
    goc_cong = TN._loi_mo_hinh_bar
    if khop_bar == "cuc_tri":              # CHI chuoi TONG_HOP (dang_ky_tong_hop da chan ma that), CHI trong lan goi nay; tra lai o `finally`
        TN._loi_mo_hinh_bar = lambda gia_tri: None
    try:
        pre_is, a_is = NDL.cat_doan(df, "kham_pha")
        pre_oos, a_oos = NDL.cat_doan(df, "xac_nhan")                  # KHONG BAO GIO cat niem_phong
        seg_is, seg_oos = pre_is.iloc[a_is:], pre_oos.iloc[a_oos:]
        qc, ly = LU.quy_cach_cho(ma, None, None)
        if qc is None:
            raise RuntimeError(ly)
        cp = NDL.chi_phi(ma, pre_oos)
        ngu_canh = {"dl_is": LU.chuan_bi(seg_is, qc), "dl_oos": LU.chuan_bi(seg_oos, qc), "von_q": VON * qc.von_quy_doi,
                    "moc_oos": round(TN._moc(ma, khung, "xac_nhan", seg_oos, cp) * 100, 2)}
        c = df["close"].to_numpy(float)
        o0 = float(df["open"].iloc[0])
        b_is, b_oos = len(pre_is), len(pre_oos)
        ra = {"v": PHIEN_BAN, "kb": kb, "hat": int(hat), "khop_bar": khop_bar, "engine": ENGINE_CUA[khop_bar], "ma": ma, "so_bar": int(so_bar),
              "toi_da_o": int(toi_da_o),
              "troi_is_pct": round(100.0 * math.log(c[b_is - 1] / o0), 2),
              "troi_oos_pct": round(100.0 * math.log(c[b_oos - 1] / c[a_oos - 1]), 2),
              "moc_oos_pct": ngu_canh["moc_oos"],
              "vr": {str(k): round(ty_so_phuong_sai(c[:b_is], k), 3) for k in CHAN_VR},       # chi tren doan kham_pha
              "mau": {}}
        for ten in mau_ten:
            ra["mau"][ten] = _chay_mau(TN, VL, ma, khung, ten, khop_bar, toi_da_o, so_o_cd, ngu_canh, int(hat))
        ra["giay"] = round(time.time() - t0, 1)
        ra["giay_sinh_chuoi"] = round(t_gen, 1)
        return ra
    finally:
        TN._loi_mo_hinh_bar = goc_cong
        NDL.quen_tong_hop(ma)


def _khoi_tao(thu_muc: str) -> None:
    """Tien trinh con (spawn): moi tien trinh MOT so tay tam va MOT so cai tam; KHONG BAO GIO cham nc.db / so_cai that."""
    pid = os.getpid()
    os.environ["NC_DB"] = os.path.join(thu_muc, "nc_%d.db" % pid)
    os.environ["NC_SO_CAI"] = os.path.join(thu_muc, "so_cai_%d" % pid)
    os.environ["NC_QUET_LUONG"] = "1"
    os.environ["NC_DONG_BANG"] = "0"
    if "nhan.nc_so_tay" in sys.modules:                              # NC_DB doc luc import: da import truoc thi vo nghia
        raise RuntimeError("nc_so_tay da duoc import truoc khi dat NC_DB - phai chay trong tien trinh spawn moi")


def _viec(args: tuple) -> dict:
    kb, hat, khop_bar, mau_ten, toi_da_o, so_o_cd, so_bar = args
    try:
        return chay_chuoi(kb, hat, khop_bar, mau_ten, toi_da_o, so_o_cd, so_bar)
    except Exception as e:                                           # mot chuoi hong khong lam hong ca dot: ghi lai va di tiep
        return {"v": PHIEN_BAN, "kb": kb, "hat": int(hat), "khop_bar": khop_bar, "so_bar": int(so_bar), "toi_da_o": int(toi_da_o),
                "loi": "%s: %s" % (type(e).__name__, str(e)[:200]), "mau": {}}


# ----------------------------------------------------------------------------------------------- tong ket

def _ty(k: int, n: int):
    return round(k / n, 4) if n else None


def _wilson(k: int, n: int):
    from nhan import vong_lap as VL
    return VL.khoang_wilson(k, n)


def phan_vi(xs: list[float], qs=(10, 25, 50, 75, 90)) -> list[float] | None:
    return [round(float(v), 2) for v in np.percentile(np.asarray(xs, float), qs)] if xs else None


def _dem_kl(muc: list[dict]) -> dict:
    """Dem QUA/RUOT cua mot nhom o (moi o = mot chuoi, doc lap). KHONG_DO_DUOC bi bo khoi ty le (nhu `vong_lap`) nhung van duoc dem rieng."""
    qua = sum(1 for x in muc if x.get("kl") == "QUA")
    ruot = sum(1 for x in muc if x.get("kl") == "RUOT")
    n = qua + ruot
    hm = sum(1 for x in muc if x.get("kl") == "QUA" and (x.get("hon_moc") or 0) > 0)
    ot = [x["o_tran"] for x in muc if x.get("kl") in ("QUA", "RUOT") and x.get("o_tran") is not None]
    return {"n": n, "qua": qua, "ty_le": _ty(qua, n), "khoang_tin_cay": _wilson(qua, n), "khong_do_duoc": len(muc) - n,
            "qua_hon_moc": hm, "ty_le_hon_moc": _ty(hm, n), "khoang_hon_moc": _wilson(hm, n), "o_tran_phan_vi": phan_vi(ot)}


def _tb_ci(xs: list[float], gioi: tuple[float, float] = (0.0, 1.0)) -> dict:
    """Trung binh va khoang tin cay 95% (chuan) cua danh sach so - moi so la MOT chuoi (don vi doc lap). `gioi` = mien cua con so: ty le
    nam trong [0, 1], CHENH hai ty le trong [-1, 1] (cat o 0 se bien chenh am thanh khoang tin cay vo nghia)."""
    if not xs:
        return {"n_chuoi": 0, "tb": None, "ci95": None}
    n, tb = len(xs), float(np.mean(xs))
    if n < 2:
        return {"n_chuoi": n, "tb": round(tb, 4), "ci95": None}
    se = float(np.std(xs, ddof=1)) / math.sqrt(n)
    return {"n_chuoi": n, "tb": round(tb, 4), "ci95": [round(max(gioi[0], tb - 1.96 * se), 4), round(min(gioi[1], tb + 1.96 * se), 4)]}


def _chan_doan_gop(muc: list[dict]) -> dict | None:
    """Gop bang chan doan THEO CHUOI: moi chuoi dong gop mot ty le (khong gop o) -> khoang tin cay theo so chuoi."""
    p_chung, p_lai, p_khong, chenh, p_hm = [], [], [], [], []
    for m in muc:
        cd = m.get("chan_doan")
        if not cd:
            continue
        b = cd["bang"]
        t = [sum(b[h][j] for h in b) for j in range(4)]
        if t[0] + t[1] >= 10:
            p_chung.append(t[0] / (t[0] + t[1]))
            p_hm.append(t[3] / (t[0] + t[1]))
        pl = b["lai"][0] / (b["lai"][0] + b["lai"][1]) if b["lai"][0] + b["lai"][1] >= O_CHAN_DOAN_TOI_THIEU else None
        pk = b["khong_lai"][0] / (b["khong_lai"][0] + b["khong_lai"][1]) if b["khong_lai"][0] + b["khong_lai"][1] >= O_CHAN_DOAN_TOI_THIEU else None
        if pl is not None:
            p_lai.append(pl)
        if pk is not None:
            p_khong.append(pk)
        if pl is not None and pk is not None:
            chenh.append(pl - pk)
    if not p_chung:
        return None
    return {"qua_moi_o": _tb_ci(p_chung), "qua_hon_moc_moi_o": _tb_ci(p_hm), "qua_neu_co_lai_trong_mau": _tb_ci(p_lai),
            "qua_neu_khong_lai_trong_mau": _tb_ci(p_khong), "chenh_co_lai_tru_khong_lai": _tb_ci(chenh, (-1.0, 1.0))}


def _tong_ket_mau(dong: list[dict], mau: str) -> dict:
    from nhan import vong_lap as VL
    muc = [(r, r["mau"][mau]) for r in dong if mau in r.get("mau", {})]
    hinh: dict = {}
    for _, m in muc:
        hinh[m["hinh"]] = hinh.get(m["hinh"], 0) + 1
    n = len(muc)
    n_do = n - hinh.get("CHUA_DO_DUOC", 0)
    cao = [(r, m) for r, m in muc if m["hinh"] == "CAO_NGUYEN" and "xn_tot" in m]
    doi = [(r, m) for r, m in muc if m["hinh"] in ("CAI_GAI", "HON_HOP") and "xn_tot" in m]
    ra = {"n_chuoi": n, "n_do_duoc": n_do, "hinh_dang": hinh, "ty_le_cao_nguyen": _ty(hinh.get("CAO_NGUYEN", 0), n_do),
          "khoang_cao_nguyen": _wilson(hinh.get("CAO_NGUYEN", 0), n_do),
          "cao": _dem_kl([m["xn_tot"] for _, m in cao]), "doi": _dem_kl([m["xn_tot"] for _, m in doi]),
          "ngau_cua_cao": _dem_kl([m["xn_ngau"] for _, m in cao if "xn_ngau" in m]),
          "ngau_moi_luot_quet": _dem_kl([m["xn_ngau"] for _, m in muc if "xn_ngau" in m]),
          "o_tot_nhat_moi_luot_quet": _dem_kl([m["xn_tot"] for _, m in muc if "xn_tot" in m])}
    # duong gia ngoai mau tang hay giam quyet dinh 'qua' den dau? (beta)
    ra["cao_theo_huong_ngoai_mau"] = {"oos_tang": _dem_kl([m["xn_tot"] for r, m in cao if r["troi_oos_pct"] > 0]),
                                      "oos_giam": _dem_kl([m["xn_tot"] for r, m in cao if r["troi_oos_pct"] <= 0])}
    # o tot nhat cua luot quet: o_tran trong mau -> ngoai mau (winner's curse)
    cap = [(m["tot"]["o_tran_trong_mau"], m["xn_tot"]["o_tran"]) for _, m in muc
           if "tot" in m and m["tot"].get("o_tran_trong_mau") is not None and m["xn_tot"].get("o_tran") is not None
           and m["xn_tot"]["kl"] in ("QUA", "RUOT")]
    ra["o_tran_o_tot_nhat"] = {"n": len(cap), "trong_mau_phan_vi": phan_vi([a for a, _ in cap]), "ngoai_mau_phan_vi": phan_vi([b for _, b in cap])}
    # cung phep so sanh san xuat tren du lieu nhieu
    uv, kq = [], {}
    for r, m in muc:
        if "xn_tot" not in m:
            continue
        i = "%s:%d:%s" % (r["kb"], r["hat"], mau)
        uv.append({"id": i, "lop": m["hinh"], "ty_le": m.get("ty_le_o_co_lai") or 0.0, "ma": r["ma"], "khung": KHUNG})
        kq[i] = {"ket_luan": m["xn_tot"]["kl"], "phien_ban_engine": r.get("engine", 4), "luc": ""}
        if "xn_ngau" in m and m["hinh"] == "CAO_NGUYEN":
            uv.append({"id": i + ":ngau", "lop": "NGAU_NHIEN", "cha": i, "ty_le": 0.0, "ma": r["ma"], "khung": KHUNG})
            kq[i + ":ngau"] = {"ket_luan": m["xn_ngau"]["kl"], "phien_ban_engine": r.get("engine", 4), "luc": ""}
    ss = VL.so_sanh_nhom(uv, kq) if uv else {}
    ra["so_sanh"] = {k: ss.get(k) for k in ("cao_vs_ngau", "cao_vs_doi")}
    ra["chan_doan"] = _chan_doan_gop([m for _, m in muc])
    return ra


def _gop_theo_chuoi(dong: list[dict], mau_ten: list[str], lay) -> dict:
    """Mot con so GOP moi chuoi (trung binh qua cac mau ma chuoi do ket luan duoc) -> trung binh + khoang tin cay theo SO CHUOI. Cac mau
    cua cung mot chuoi tuong quan nen KHONG gop o/mau thang vao mot ty le."""
    xs = []
    for r in dong:
        v = [lay(r["mau"][m]) for m in mau_ten if m in r.get("mau", {})]
        v = [x for x in v if x is not None]
        if v:
            xs.append(float(np.mean(v)))
    return _tb_ci(xs)


def _la_cao(m: dict):
    if m.get("hinh") == "CHUA_DO_DUOC":
        return None
    return 1.0 if m.get("hinh") == "CAO_NGUYEN" else 0.0


def _qua_cua(khoa: str, hon_moc: bool = False, chi_cao: bool = False):
    """QUA (hoac QUA VA hon mua-giu / ban-giu) cua o `khoa` trong mot muc mau: 1/0, None khi khong ket luan duoc. `chi_cao`: chi tinh
    cac luot quet duoc xep CAO_NGUYEN (cung nhom voi 'cao' cua vong lap that)."""
    def lay(m):
        if chi_cao and m.get("hinh") != "CAO_NGUYEN":
            return None
        x = m.get(khoa)
        if not x or x.get("kl") not in ("QUA", "RUOT"):
            return None
        return 1.0 if (x["kl"] == "QUA" and (not hon_moc or (x.get("hon_moc") or 0) > 0)) else 0.0
    return lay


def tong_ket(dong: list[dict]) -> dict:
    """Tong hop cac ban ghi chuoi (moi dong = mot chuoi) thanh bang tham chieu theo kich ban x engine x mau."""
    hop = [r for r in dong if r.get("mau") and not r.get("loi")]
    cau_hinh: dict = {}
    for r in hop:
        k = (r.get("v"), r.get("so_bar"), r.get("toi_da_o"))
        cau_hinh[k] = cau_hinh.get(k, 0) + 1
    chinh = max(cau_hinh, key=cau_hinh.get) if cau_hinh else None
    hop = [r for r in hop if (r.get("v"), r.get("so_bar"), r.get("toi_da_o")) == chinh]
    ra_kb: dict = {}
    for kb in KICH_BAN:
        for kbar in KHOP_BAR:
            rows = [r for r in hop if r["kb"] == kb and r.get("khop_bar", "duong_di") == kbar]
            if not rows:
                continue
            mau_ten = [m for m in MAU if any(m in r["mau"] for r in rows)]
            ra_kb["%s@e%d" % (kb, ENGINE_CUA[kbar])] = {
                "kich_ban": kb, "khop_bar": kbar, "engine": ENGINE_CUA[kbar], "loai": LOAI[kb], "mo_ta": KICH_BAN[kb], "so_chuoi": len(rows),
                "troi_is_pct_tb": round(float(np.mean([r["troi_is_pct"] for r in rows])), 2),
                "troi_oos_pct_tb": round(float(np.mean([r["troi_oos_pct"] for r in rows])), 2),
                "vr_tb": {str(k): round(float(np.mean([r["vr"][str(k)] for r in rows])), 3) for k in CHAN_VR},
                "gop": {"ty_le_cao_nguyen": _gop_theo_chuoi(rows, mau_ten, _la_cao),
                        "qua_o_tot_nhat": _gop_theo_chuoi(rows, mau_ten, _qua_cua("xn_tot")),
                        "qua_cao_nguyen": _gop_theo_chuoi(rows, mau_ten, _qua_cua("xn_tot", chi_cao=True)),
                        "qua_o_ngau": _gop_theo_chuoi(rows, mau_ten, _qua_cua("xn_ngau")),
                        "qua_hon_moc_o_tot_nhat": _gop_theo_chuoi(rows, mau_ten, _qua_cua("xn_tot", hon_moc=True)),
                        "qua_hon_moc_cao_nguyen": _gop_theo_chuoi(rows, mau_ten, _qua_cua("xn_tot", hon_moc=True, chi_cao=True)),
                        "qua_hon_moc_o_ngau": _gop_theo_chuoi(rows, mau_ten, _qua_cua("xn_ngau", hon_moc=True))},
                "mau": {m: _tong_ket_mau(rows, m) for m in mau_ten}}
    hong = sum(1 for r in dong if r.get("loi"))
    return {"phien_ban": PHIEN_BAN, "khung": KHUNG,
            "cau_hinh": {"v": chinh[0], "so_bar": chinh[1], "toi_da_o": chinh[2]} if chinh else None,
            "so_chuoi_hong": hong, "so_chuoi_khac_cau_hinh": len(dong) - hong - len(hop),
            "kich_ban": ra_kb, "tom_tat": tom_tat_loi_thuong(ra_kb)}


def _pc(x) -> str:
    return "?" if x is None else "%.0f%%" % (100.0 * x)


def tom_tat_loi_thuong(kb: dict) -> list[str]:
    """Vai dong BANG LOI THUONG (khong thuat ngu) tu cac con so gop; chi mo ta so, khong ket luan thay so."""
    ra = []
    for khoa, v in kb.items():
        if v["kich_ban"] != "NHIEU":
            continue
        g = v["gop"]
        ra.append("%s (%d chuoi gia chi co nhieu, engine %d): %s luot quet bi xep 'cao nguyen'; o tot nhat cua luot quet van 'qua' kiem ngoai mau "
                  "%s (o chon bua cung luoi: %s; qua VA hon mua-giu/ban-giu: %s)." % (
                      khoa, v["so_chuoi"], v["engine"], _pc(g["ty_le_cao_nguyen"]["tb"]), _pc(g["qua_o_tot_nhat"]["tb"]),
                      _pc(g["qua_o_ngau"]["tb"]), _pc(g["qua_hon_moc_o_tot_nhat"]["tb"])))
    for khoa, v in kb.items():
        if v["loai"] == "co_hoi_quy":
            ra.append("%s (%d chuoi, co thanh phan hoi quy that, VR48=%.2f VR144=%.2f): o tot nhat 'qua' %s." % (
                khoa, v["so_chuoi"], v["vr_tb"]["48"], v["vr_tb"]["144"], _pc(v["gop"]["qua_o_tot_nhat"]["tb"])))
    return ra


# ----------------------------------------------------------------------------------------------- doc ket qua that so voi nhieu (quy tac R1)

def doc_tham_chieu(duong: Path | str | None = None) -> dict | None:
    """Tong ket da luu (`--ra`.json), None neu chua chay / hong."""
    try:
        d = json.loads(Path(duong or TEP_TONG_KET).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return d if isinstance(d, dict) and d.get("kich_ban") else None


def _nhieu_tham_chieu(tc: dict | None, engine: int, mau: str | None, hon_moc: bool):
    """(ty_le, khoang_tin_cay, so_don_vi_doc_lap) cua nhom 'cao nguyen' tren chuoi NHIEU cung engine; None khi thieu."""
    ks = ((tc or {}).get("kich_ban") or {}).get("NHIEU@e%d" % int(engine))
    if not ks:
        return None
    if mau:
        d = (ks.get("mau") or {}).get(mau, {}).get("cao")
        if not d:
            return None
        ty, kt, n = (d["ty_le_hon_moc"], d["khoang_hon_moc"], d["n"]) if hon_moc else (d["ty_le"], d["khoang_tin_cay"], d["n"])
    else:
        d = ks["gop"].get("qua_hon_moc_cao_nguyen" if hon_moc else "qua_cao_nguyen")
        if not d:
            return None
        ty, kt, n = d["tb"], d["ci95"], d["n_chuoi"]
    if ty is None or not kt or n < 2:
        return None
    return float(ty), [float(kt[0]), float(kt[1])], int(n)


def so_voi_nhieu(qua: int, n: int, tham_chieu: dict | None, engine: int, mau: str | None = None, hon_moc: bool = False) -> dict:
    """Ket qua THAT (`qua` trong `n` ket luan duoc, nhom 'cao nguyen', engine `engine`) so voi chuoi NHIEU cung engine. QUY TAC R1 (dong bang
    truoc khi co ket qua that nao, `tai_lieu/VONG_LAP.md`):

    * `CHUA_DU` neu n < 20, hoac chua co tham chieu NHIEU cung engine (khong so engine 3 voi engine 4).
    * `BAO_HOA` neu nhieu cung dat >= 90% va dang so theo 'qua': tieu chi khong con phan biet -> goi lai voi `hon_moc=True`
      (qua VA hon mua-giu/ban-giu).
    * `VUOT_NHIEU` neu can duoi Wilson cua ket qua that > can tren khoang tin cay cua nhieu VA chenh >= 10 diem.
    * `DUOI_NHIEU` neu can tren Wilson cua that < can duoi khoang tin cay cua nhieu VA chenh >= 10 diem (am hon ca nhieu: co loi the nguoc?).
    * con lai `NGANG_NHIEU` (kem MDE ngu y: n that va so chuoi nhieu nam trong ra).

    `mau` = None so voi con so GOP (trung binh theo chuoi, khoang tin cay theo so chuoi); `mau="mua_phang"`... so tung mau.
    Day la NHAN canh bao cho nhan GIU, khong phai cong chan."""
    ra = {"tieu_chi": "qua_hon_moc" if hon_moc else "qua", "engine": int(engine), "mau": mau, "n_thuc": int(n)}
    nh = _nhieu_tham_chieu(tham_chieu, engine, mau, hon_moc)
    if n < NHIEU_N_TOI_THIEU:
        return dict(ra, ket_luan="CHUA_DU", ly_do="moi co %d ket qua that ket luan duoc (< %d)" % (n, NHIEU_N_TOI_THIEU))
    if nh is None:
        return dict(ra, ket_luan="CHUA_DU", ly_do="chua co doi chung nhieu cho engine %d%s" % (int(engine), " / mau %s" % mau if mau else ""))
    ty_n, (lo_n, hi_n), so_chuoi = nh
    thuc = qua / n
    kt = _wilson(int(qua), int(n))
    ra.update(thuc=round(thuc, 4), khoang_thuc=kt, nhieu=round(ty_n, 4), khoang_nhieu=[lo_n, hi_n], n_chuoi_nhieu=so_chuoi)
    if not hon_moc and ty_n >= NHIEU_BAO_HOA:
        return dict(ra, ket_luan="BAO_HOA", ly_do="nhieu da dat %s 'qua': doi sang tieu chi qua VA hon mua-giu/ban-giu" % _pc(ty_n))
    if kt[0] > hi_n and thuc - ty_n >= NHIEU_CHENH_TOI_THIEU:
        return dict(ra, ket_luan="VUOT_NHIEU")
    if kt[1] < lo_n and ty_n - thuc >= NHIEU_CHENH_TOI_THIEU:
        return dict(ra, ket_luan="DUOI_NHIEU")
    return dict(ra, ket_luan="NGANG_NHIEU")


# ----------------------------------------------------------------------------------------------- doc / ghi tep

def doc_dong(duong: Path) -> list[dict]:
    ra = []
    if duong.exists():
        for d in duong.read_text(encoding="utf-8").splitlines():
            d = d.strip()
            if d:
                try:
                    ra.append(json.loads(d))
                except ValueError:
                    continue
    return ra


def _khoa_xong(r: dict) -> tuple:
    return (r["kb"], int(r["hat"]), r.get("khop_bar", "duong_di"), r.get("so_bar"), r.get("toi_da_o"), r.get("v"))


def da_xong(dong: list[dict]) -> set[tuple]:
    return {_khoa_xong(r) for r in dong if r.get("mau") and not r.get("loi")}


def chay(kich_ban=("NHIEU",), so_chuoi: int = 100, hat_tu: int = 1, mau_ten=MAU_TEN, khop_bar=("duong_di",), luong: int = 4,
         toi_da_o: int = TOI_DA_O, so_o_cd: int = SO_O_CHAN_DOAN, so_bar: int = SO_BAR, tep: Path | None = None, im: bool = False) -> list[dict]:
    """Chay (hoac chay tiep) cac chuoi (kich ban, hat, engine) chua co trong `tep`; moi chuoi xong la ghi NGAY mot dong (an toan khi bi ngat)."""
    tep = Path(tep) if tep else None
    cu = doc_dong(tep) if tep else []
    xong = da_xong(cu)
    viec = [(kb, h, kbar, tuple(mau_ten), int(toi_da_o), int(so_o_cd), int(so_bar))
            for h in range(hat_tu, hat_tu + so_chuoi) for kb in kich_ban for kbar in khop_bar
            if (kb, h, kbar, int(so_bar), int(toi_da_o), PHIEN_BAN) not in xong]
    moi: list[dict] = []
    if not viec:
        return cu
    for bien in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ.setdefault(bien, "1")                              # song song o muc CHUOI, khong de moi tien trinh con tranh nhau nhan CPU
    thu_muc = tempfile.mkdtemp(prefix="doi_chung_nhieu_")
    t0 = time.time()
    try:
        ctx = multiprocessing.get_context("spawn")
        with cf.ProcessPoolExecutor(max_workers=max(1, int(luong)), mp_context=ctx, initializer=_khoi_tao, initargs=(thu_muc,)) as ex:
            fs = [ex.submit(_viec, v) for v in viec]
            f_ghi = open(tep, "a", encoding="utf-8") if tep else None
            try:
                for i, f in enumerate(cf.as_completed(fs), 1):
                    r = f.result()
                    moi.append(r)
                    if f_ghi:
                        f_ghi.write(json.dumps(r, ensure_ascii=True, sort_keys=True) + "\n")
                        f_ghi.flush()
                    if not im and (i % 5 == 0 or i == len(fs) or r.get("loi")):
                        print("  %d/%d chuoi (%.0f giay)%s" % (i, len(fs), time.time() - t0, "  LOI " + r["loi"] if r.get("loi") else ""), flush=True)
            finally:
                if f_ghi:
                    f_ghi.close()
    finally:
        shutil.rmtree(thu_muc, ignore_errors=True)
    return cu + moi


def kiem_do_trung_thuc(so_chuoi: int = 12, mau_ten=("mua_phang", "ban_phang"), luong: int = 4, hat_tu: int = 9001) -> dict:
    """Cung chuoi NHIEU, cung mau: quet 1.000 o so voi 3.000 o (cua san xuat) - hinh dang va ty le qua co doi khong? Khong ghi vao tep chinh."""
    a = chay(("NHIEU",), so_chuoi, hat_tu, mau_ten, ("duong_di",), luong, 1000, 60, im=True)
    b = chay(("NHIEU",), so_chuoi, hat_tu, mau_ten, ("duong_di",), luong, 3000, 60, im=True)
    ra = {}
    for ten in mau_ten:
        for nhan, rows in (("1000", a), ("3000", b)):
            ra.setdefault(ten, {})[nhan] = {k: v for k, v in _tong_ket_mau([r for r in rows if r.get("mau") and not r.get("loi")], ten).items()
                                           if k in ("hinh_dang", "cao", "o_tot_nhat_moi_luot_quet", "ngau_moi_luot_quet")}
    return ra


def in_tong_ket(tk: dict) -> None:
    for d in tk.get("tom_tat") or []:
        print(d)
    if tk.get("so_chuoi_hong") or tk.get("so_chuoi_khac_cau_hinh"):
        print("(bo qua: %d chuoi loi, %d chuoi khac cau hinh -> dung --ra khac cho cau hinh khac)" % (
            tk.get("so_chuoi_hong", 0), tk.get("so_chuoi_khac_cau_hinh", 0)))
    for khoa, v in tk["kich_ban"].items():
        g = v["gop"]
        print("\n== %s (%s; %d chuoi; troi trong mau %+.1f%% ngoai mau %+.1f%%; VR %s)" % (
            khoa, v["loai"], v["so_chuoi"], v["troi_is_pct_tb"], v["troi_oos_pct_tb"],
            "/".join("%d:%.2f" % (k, v["vr_tb"][str(k)]) for k in CHAN_VR)))
        print("   GOP theo chuoi: cao nguyen %s | o tot nhat qua %s %s | o ngau qua %s | qua+hon moc: tot nhat %s, ngau %s" % (
            _pc(g["ty_le_cao_nguyen"]["tb"]), _pc(g["qua_o_tot_nhat"]["tb"]), g["qua_o_tot_nhat"]["ci95"], _pc(g["qua_o_ngau"]["tb"]),
            _pc(g["qua_hon_moc_o_tot_nhat"]["tb"]), _pc(g["qua_hon_moc_o_ngau"]["tb"])))
        for ten, m in v["mau"].items():
            c, t, n = m["cao"], m["o_tot_nhat_moi_luot_quet"], m["ngau_moi_luot_quet"]
            ch = ((m.get("chan_doan") or {}).get("chenh_co_lai_tru_khong_lai") or {})
            print("  %-16s cao nguyen %4s (%3d/%3d) | tot nhat qua %4s (n=%3d) hon moc %4s | cao qua %4s (n=%3d) | ngau qua %4s | "
                  "co lai-khong lai (trong mau) %s" % (
                      ten, _pc(m["ty_le_cao_nguyen"]), m["hinh_dang"].get("CAO_NGUYEN", 0), m["n_do_duoc"], _pc(t["ty_le"]), t["n"],
                      _pc(t["ty_le_hon_moc"]), _pc(c["ty_le"]), c["n"], _pc(n["ty_le"]),
                      "%+.2f %s" % (ch["tb"], ch["ci95"]) if ch.get("tb") is not None else "?"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Doi chung nhieu cho chang KIEM (xem docstring)")
    ap.add_argument("--kich-ban", default="NHIEU", help="danh sach, phan cach dau phay (hoac TAT_CA): %s" % ",".join(KICH_BAN))
    ap.add_argument("--khop-bar", default="duong_di", help="duong_di (engine 4) ; cuc_tri (engine 3, may nha dang chay) ; hoac ca hai cach dau phay")
    ap.add_argument("--so-chuoi", type=int, default=100)
    ap.add_argument("--hat-tu", type=int, default=1)
    ap.add_argument("--mau", default=",".join(MAU_TEN), help="co: %s" % ",".join(MAU_TEN))
    ap.add_argument("--luong", type=int, default=4)
    ap.add_argument("--toi-da-o", type=int, default=TOI_DA_O)
    ap.add_argument("--so-o-chan-doan", type=int, default=SO_O_CHAN_DOAN)
    ap.add_argument("--so-bar", type=int, default=SO_BAR)
    ap.add_argument("--ra", default=str(TEP_TONG_KET.with_suffix("")), help="tien to tep: <ra>.jsonl va <ra>.json")
    ap.add_argument("--tong-ket", action="store_true", help="khong chay gi, chi tong ket tu tep .jsonl")
    ap.add_argument("--kiem-trung-thuc", action="store_true", help="so 1.000 o voi 3.000 o tren cung chuoi (mac dinh 12 chuoi, 2 mau)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    ra = Path(a.ra)
    ra.parent.mkdir(parents=True, exist_ok=True)
    kb = list(KICH_BAN) if a.kich_ban.upper() == "TAT_CA" else [x.strip().upper() for x in a.kich_ban.split(",") if x.strip()]
    mau = [x.strip() for x in a.mau.split(",") if x.strip()]
    kbar = [x.strip() for x in a.khop_bar.split(",") if x.strip()]
    loi = [x for x in kb if x not in KICH_BAN] + [x for x in mau if x not in MAU] + [x for x in kbar if x not in KHOP_BAR]
    if loi:
        print("khong biet: %s" % loi, file=sys.stderr)
        return 2
    if a.kiem_trung_thuc:
        print(json.dumps(kiem_do_trung_thuc(luong=a.luong), ensure_ascii=False, indent=1))
        return 0
    jsonl = ra.with_suffix(".jsonl")
    if a.tong_ket:
        dong = doc_dong(jsonl)
    else:
        dong = chay(kb, a.so_chuoi, a.hat_tu, mau, kbar, a.luong, a.toi_da_o, a.so_o_chan_doan, a.so_bar, tep=jsonl)
    tk = tong_ket(dong)
    ra.with_suffix(".json").write_text(json.dumps(tk, ensure_ascii=True, indent=1, sort_keys=True), encoding="utf-8")
    if a.json:
        print(json.dumps(tk, ensure_ascii=False, indent=1))
    else:
        in_tong_ket(tk)
    return 0


if __name__ == "__main__":
    sys.exit(main())
