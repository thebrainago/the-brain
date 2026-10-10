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
import bisect
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

#: Quy tac doc (DONG BANG trong tai_lieu/VONG_LAP.md truoc khi chay): xem `so_voi_nhieu_cum` ; cac hang so con lai cua R2 o khoi "mot o -> mot con so"
NHIEU_CHENH_TOI_THIEU = 0.10    # chenh toi thieu so voi nhieu (cung y nghia voi vong_lap.SO_SANH_CHENH_TOI_THIEU)
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


def _ung_vien_va_kq(muc: list[tuple]) -> tuple[list[dict], dict]:
    """`muc` = [(chuoi, ten_mau, muc_mau)] -> (ung_vien, kq) theo dang `vong_lap.so_sanh_nhom` nhan: o tot nhat cua moi luot quet la mot ung vien
    (lop = hinh dang), o ngau nhien cua luot quet CAO_NGUYEN la ung vien NGAU_NHIEN ghep cap (cha = ung vien do)."""
    uv, kq = [], {}
    for r, mau, m in muc:
        if "xn_tot" not in m:
            continue
        i = "%s:%d:%s" % (r["kb"], r["hat"], mau)
        uv.append({"id": i, "lop": m["hinh"], "ty_le": m.get("ty_le_o_co_lai") or 0.0, "ma": r["ma"], "khung": KHUNG})
        kq[i] = {"ket_luan": m["xn_tot"]["kl"], "phien_ban_engine": r.get("engine", 4), "luc": ""}
        if "xn_ngau" in m and m["hinh"] == "CAO_NGUYEN":
            uv.append({"id": i + ":ngau", "lop": "NGAU_NHIEN", "cha": i, "ty_le": 0.0, "ma": r["ma"], "khung": KHUNG})
            kq[i + ":ngau"] = {"ket_luan": m["xn_ngau"]["kl"], "phien_ban_engine": r.get("engine", 4), "luc": ""}
    return uv, kq


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
    uv, kq = _ung_vien_va_kq([(r, mau, m) for r, m in muc])
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
    cac luot quet duoc xep CAO_NGUYEN (cung nhom voi 'cao' cua vong lap that). Cung cong thuc voi `qua_o` (mot nguon cho ca hai phia)."""
    def lay(m):
        if chi_cao and m.get("hinh") != "CAO_NGUYEN":
            return None
        return qua_o(m.get(khoa), "qua_hon_moc" if hon_moc else "qua")
    return lay


# ----------------------------------------------------------------------------------------------- mot o -> mot con so trong [0, 1] (R2)

#: nhom (cung nghia voi `vong_lap.nhom_cua`): cao = o tot nhat cua luot quet CAO_NGUYEN ; doi = o tot nhat cua luot quet KHAC ; ngau = o ngau nhien ghep cap
NHOM = ("cao", "doi", "ngau")
#: thuoc do: qua = QUA ngoai mau ; qua_hon_moc = QUA VA hon mua-giu/ban-giu ; duyet = QUA VA maxDD < tran cua chu du an ; calmar = phan vi calmar so voi nhieu
THUOC_DO = ("qua", "qua_hon_moc", "duyet", "calmar")
THUOC_DO_NHI_PHAN = ("qua", "qua_hon_moc", "duyet")
CALMAR_TRAN = 1.0e6              # calmar cua o co lai ma khong co drawdown nao: tran huu han (de xep hang va ghi JSON)
CHAY = float("-inf")             # calmar cua o chay tai khoan: thap nhat, phan vi 0

#: R2 (DONG BANG trong tai_lieu/VONG_LAP.md muc 8.3, khong doi sau khi nhin so that)
CUM_TOI_THIEU = 8                # so thi truong toi thieu truoc khi dam doc
CUM_KL_TOI_THIEU = 3             # ket luan duoc toi thieu cua MOT thi truong (hoac MOT chuoi nhieu) de co con so cua no
NHIEU_CHUOI_TOI_THIEU = 30       # chuoi nhieu toi thieu de lam phan phoi nhieu
RUT_LAN = 20_000
RUT_HAT = 20_261_010
NHIEU_ALPHA = 0.05               # mot phia


def o_cua_nhom(m: dict, nhom: str):
    """Muc ket qua ngoai mau (`xn_*`) cua `nhom` trong MOT muc mau cua chuoi; None neu muc nay khong thuoc nhom / khong co o do."""
    if nhom not in NHOM:
        raise ValueError("nhom phai la mot trong %s" % (NHOM,))
    hinh = m.get("hinh")
    if nhom == "ngau":
        return m.get("xn_ngau") if hinh == "CAO_NGUYEN" else None
    x = m.get("xn_tot")
    if not x or hinh == "CHUA_DO_DUOC":
        return None
    return x if (hinh == "CAO_NGUYEN") == (nhom == "cao") else None


def qua_o(x: dict | None, thuoc_do: str = "qua"):
    """1.0 / 0.0 / None cua MOT o cho thuoc do nhi phan. None = khong ket luan duoc (KHONG_DO_DUOC), hoac khong do duoc o thuoc do nay: o 'QUA'
    ma thieu hon_moc / maxDD (ket qua cua ma cu khong in hon_moc_pct) thi khong the noi 'hon' hay 'khong hon' -> bo, KHONG dem la 0."""
    if not x or x.get("kl") not in ("QUA", "RUOT"):
        return None
    if thuoc_do not in THUOC_DO_NHI_PHAN:
        raise ValueError("thuoc do nhi phan phai la mot trong %s" % (THUOC_DO_NHI_PHAN,))
    if x["kl"] == "RUOT":
        return 0.0
    if thuoc_do == "qua":
        return 1.0
    if thuoc_do == "qua_hon_moc":
        h = x.get("hon_moc")
        return None if h is None else (1.0 if h > 0 else 0.0)
    dd = x.get("dd")                                                  # duyet: maxDD duoi tran cua chu du an (mot nguon: cham_diem.TRAN_SUT_GIAM)
    if dd is None:
        return None
    from nhan import cham_diem as CD
    return 1.0 if abs(float(dd)) < CD.TRAN_SUT_GIAM else 0.0


def calmar_cua(x: dict | None):
    """Calmar ngoai mau cua mot o = ln / |maxDD| (cung cong thuc `luoi.chi_so`). `CHAY` (-inf) khi chay tai khoan ; None khi khong ket luan
    duoc hoac thieu so. Khong co drawdown nao: co lai -> CALMAR_TRAN, khong lai -> 0."""
    if not x or x.get("kl") not in ("QUA", "RUOT"):
        return None
    if x.get("chay"):
        return CHAY
    ln, dd = x.get("ln"), x.get("dd")
    if ln is None or dd is None:
        return None
    ln, dd = float(ln), abs(float(dd))
    if not (math.isfinite(ln) and math.isfinite(dd)):
        return None
    if dd < 1e-9:
        return CALMAR_TRAN if ln > 0 else 0.0
    return max(-CALMAR_TRAN, min(CALMAR_TRAN, ln / dd))


def tao_ecdf(calmars) -> dict | None:
    """Phan phoi calmar cua mot (engine, nhom, mau) tren chuoi nhieu: {n, n_chay, gia_tri (sap tang, KHONG gom o chay tai khoan)}."""
    xs = [c for c in calmars if c is not None]
    if not xs:
        return None
    return {"n": len(xs), "n_chay": sum(1 for c in xs if c == CHAY), "gia_tri": sorted(round(c, 4) for c in xs if c != CHAY)}


def phan_vi_trong(ecdf: dict | None, c) -> float | None:
    """Phan vi (0..1) cua calmar `c` trong `ecdf`: phan vi TRUNG DIEM khi bang nhau ; chay tai khoan = 0 ; None khi thieu ecdf / calmar."""
    if not ecdf or c is None or not ecdf.get("n"):
        return None
    if c == CHAY:
        return 0.0
    gt = ecdf["gia_tri"]
    v = round(float(c), 4)
    thap, cao = bisect.bisect_left(gt, v), bisect.bisect_right(gt, v)
    return (ecdf["n_chay"] + thap + 0.5 * (cao - thap)) / ecdf["n"]


def gia_tri_o(x: dict | None, thuoc_do: str, ecdf: dict | None = None):
    """Con so trong [0, 1] cua MOT o theo `thuoc_do` ; 'calmar' can `ecdf` cua dung (engine, nhom, mau)."""
    if thuoc_do == "calmar":
        return phan_vi_trong(ecdf, calmar_cua(x))
    return qua_o(x, thuoc_do)


def tb_o(cac_o: list[dict], thuoc_do: str, ecdf_theo_mau: dict | None = None, toi_thieu: int = CUM_KL_TOI_THIEU):
    """(trung binh, so o do duoc) cua `gia_tri_o` tren `cac_o` (moi o la dict xn_* kem khoa 'mau') ; trung binh = None khi < `toi_thieu` o do duoc."""
    v = []
    for o in cac_o:
        g = gia_tri_o(o, thuoc_do, (ecdf_theo_mau or {}).get(o.get("mau")))
        if g is not None:
            v.append(g)
    return (float(np.mean(v)) if len(v) >= toi_thieu else None), len(v)


def _o_cua_chuoi(r: dict, nhom: str, mau_ten) -> list[dict]:
    ra = []
    for t in mau_ten:
        m = (r.get("mau") or {}).get(t)
        x = o_cua_nhom(m, nhom) if m else None
        if x is not None:
            ra.append(dict(x, mau=t))
    return ra


def ecdf_nhieu(rows: list[dict], mau_ten) -> dict:
    """{nhom: {mau: ecdf}} tu cac chuoi cua MOT kich ban x engine."""
    ra: dict = {}
    for nhom in NHOM:
        d = {}
        for t in mau_ten:
            e = tao_ecdf([calmar_cua(o_cua_nhom(r["mau"][t], nhom)) for r in rows if t in (r.get("mau") or {}) and o_cua_nhom(r["mau"][t], nhom)])
            if e:
                d[t] = e
        ra[nhom] = d
    return ra


def nhieu_theo_chuoi(rows: list[dict], mau_ten, nhom: str, thuoc_do: str, ecdf_theo_mau: dict | None = None) -> list[float]:
    """Mot con so MOI CHUOI (trung binh cac o cua nhom ma chuoi do ket luan duoc, can >= CUM_KL_TOI_THIEU o): la cac 'thi truong gia' cua R2."""
    xs = []
    for r in rows:
        tb, _ = tb_o(_o_cua_chuoi(r, nhom, mau_ten), thuoc_do, ecdf_theo_mau)
        if tb is not None:
            xs.append(tb)
    return xs


def _tom_xs(xs: list[float]) -> dict:
    return {"n": len(xs), "tb": round(float(np.mean(xs)), 4) if xs else None,
            "sd": round(float(np.std(xs, ddof=1)), 4) if len(xs) > 1 else None, "xs": [round(float(x), 4) for x in xs]}


def _nhieu_theo_mau(rows: list[dict], mau_ten) -> dict:
    """Ty le nhi phan theo MAU (gop o cua moi chuoi): nhieu mong doi cua mot ket qua that CO CAU MAU nhu vay (chan doan lech co cau mau)."""
    ra: dict = {}
    for nhom in NHOM:
        for td in THUOC_DO_NHI_PHAN:
            d = {}
            for t in mau_ten:
                v = [qua_o(o_cua_nhom(r["mau"][t], nhom), td) for r in rows if t in (r.get("mau") or {}) and o_cua_nhom(r["mau"][t], nhom)]
                v = [x for x in v if x is not None]
                if v:
                    d[t] = {"tb": round(float(np.mean(v)), 4), "n": len(v)}
            ra.setdefault(nhom, {})[td] = d
    return ra


def _hop_chinh(dong: list[dict]):
    """Cac chuoi hop le cua cau hinh DONG NHAT NHIEU NHAT (v, so_bar, toi_da_o) + cau hinh do. Chuoi loi / khong co mau bi bo."""
    hop = [r for r in dong if r.get("mau") and not r.get("loi")]
    cau_hinh: dict = {}
    for r in hop:
        k = (r.get("v"), r.get("so_bar"), r.get("toi_da_o"))
        cau_hinh[k] = cau_hinh.get(k, 0) + 1
    chinh = max(cau_hinh, key=cau_hinh.get) if cau_hinh else None
    return [r for r in hop if (r.get("v"), r.get("so_bar"), r.get("toi_da_o")) == chinh], chinh


def _cac_chuoi(hop: list[dict], kb: str, kbar: str) -> list[dict]:
    return [r for r in hop if r["kb"] == kb and r.get("khop_bar", "duong_di") == kbar]


def _mau_co(rows: list[dict]) -> list[str]:
    return [m for m in MAU if any(m in r["mau"] for r in rows)]


def tong_ket(dong: list[dict]) -> dict:
    """Tong hop cac ban ghi chuoi (moi dong = mot chuoi) thanh bang tham chieu theo kich ban x engine x mau."""
    hop, chinh = _hop_chinh(dong)
    # phan phoi calmar cua NHIEU theo engine: chuan phan vi cho MOI kich ban cung engine (kich ban co loi the thi calmar cao hon nhieu -> phan vi > 0,5)
    ecdf_chuan: dict = {}
    for kbar in KHOP_BAR:
        rows = _cac_chuoi(hop, "NHIEU", kbar)
        if rows:
            ecdf_chuan[ENGINE_CUA[kbar]] = ecdf_nhieu(rows, _mau_co(rows))
    ra_kb: dict = {}
    for kb in KICH_BAN:
        for kbar in KHOP_BAR:
            rows = _cac_chuoi(hop, kb, kbar)
            if not rows:
                continue
            mau_ten = _mau_co(rows)
            ecdf = ecdf_chuan.get(ENGINE_CUA[kbar]) or {}
            ra_kb["%s@e%d" % (kb, ENGINE_CUA[kbar])] = {
                "nhieu": {nhom: {td: _tom_xs(nhieu_theo_chuoi(rows, mau_ten, nhom, td, ecdf.get(nhom))) for td in THUOC_DO} for nhom in NHOM},
                **({"ecdf": ecdf_chuan[ENGINE_CUA[kbar]], "theo_mau": _nhieu_theo_mau(rows, mau_ten)} if kb == "NHIEU" else {}),
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


# ----------------------------------------------------------------------------------------------- doc ket qua THAT so voi nhieu (quy tac R2)

def doc_tham_chieu(duong: Path | str | None = None) -> dict | None:
    """Tong ket da luu (`--ra`.json), None neu chua chay / hong."""
    try:
        d = json.loads(Path(duong or TEP_TONG_KET).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return d if isinstance(d, dict) and d.get("kich_ban") else None


def so_voi_nhieu_cum(gia_tri_cum: dict[str, float], xs_nhieu: list[float], thuoc_do: str = "qua") -> dict:
    """QUY TAC R2 (dong bang truoc khi doc ket qua that nao: `tai_lieu/VONG_LAP.md` muc 8.3).

    Don vi doc lap la THI TRUONG (khong phai o, khong phai luot quet): `gia_tri_cum` = {thi truong: con so trong [0, 1]}, `xs_nhieu` = con so cua
    tung CHUOI NHIEU cung engine/nhom/thuoc do (la 'thi truong gia'). T = trung binh cac thi truong ; phan phoi nhieu cua T = trung binh cua M
    con so rut co hoan lai tu `xs_nhieu` (M = so thi truong, RUT_LAN lan, hat co dinh).

    * `CHUA_DU` neu < 8 thi truong hoac < 30 chuoi nhieu.
    * `BAO_HOA` neu thuoc do nhi phan va nhieu TRUNG BINH da >= 90%: khong con phan biet -> doc cot 'qua VA hon mua-giu' hoac 'calmar'.
    * `VUOT_NHIEU` neu p mot phia <= 0,05 VA T hon trung binh nhieu >= 0,10 ; `DUOI_NHIEU` doi xung ; con lai `NGANG_NHIEU`.
    Luon kem `mde` = (1,645 + 0,84) x sd(chuoi nhieu) / can(M): chenh nho nhat thay duoc voi luc 80% ; `du_luc` = mde <= 0,10 (neu khong,
    'ngang' chi la 'khong du thi truong de thay'). NHAN canh bao cho nhan GIU, khong phai cong chan."""
    if thuoc_do not in THUOC_DO:
        raise ValueError("thuoc_do phai la mot trong %s" % (THUOC_DO,))
    ra = {"thuoc_do": thuoc_do, "n_cum": len(gia_tri_cum), "n_chuoi_nhieu": len(xs_nhieu)}
    if len(gia_tri_cum) < CUM_TOI_THIEU:
        return dict(ra, ket_luan="CHUA_DU", ly_do="moi co %d thi truong du so lieu (< %d)" % (len(gia_tri_cum), CUM_TOI_THIEU))
    if len(xs_nhieu) < NHIEU_CHUOI_TOI_THIEU:
        return dict(ra, ket_luan="CHUA_DU", ly_do="moi co %d chuoi nhieu (< %d)" % (len(xs_nhieu), NHIEU_CHUOI_TOI_THIEU))
    gt = np.asarray([float(v) for v in gia_tri_cum.values()], float)
    xs = np.sort(np.asarray([float(v) for v in xs_nhieu], float))          # sap xep: ket qua chi phu thuoc TAP chuoi nhieu, khong phu thuoc thu tu ghi tep
    m = len(gt)
    that, nhieu, sd = float(gt.mean()), float(xs.mean()), float(xs.std(ddof=1))
    rut = np.random.default_rng(RUT_HAT).choice(xs, size=(RUT_LAN, m), replace=True).mean(axis=1)
    p_vuot = (1 + int(np.sum(rut >= that - 1e-12))) / (RUT_LAN + 1)
    p_duoi = (1 + int(np.sum(rut <= that + 1e-12))) / (RUT_LAN + 1)
    mde = (1.645 + 0.84) * sd / math.sqrt(m)
    ra.update(that=round(that, 4), nhieu=round(nhieu, 4), chenh=round(that - nhieu, 4), sd_nhieu=round(sd, 4), mde=round(mde, 4),
              du_luc=bool(mde <= NHIEU_CHENH_TOI_THIEU), p_vuot=round(p_vuot, 5), p_duoi=round(p_duoi, 5),
              khoang_nhieu=[round(float(np.percentile(rut, 2.5)), 4), round(float(np.percentile(rut, 97.5)), 4)])
    if thuoc_do in THUOC_DO_NHI_PHAN and nhieu >= NHIEU_BAO_HOA:
        return dict(ra, ket_luan="BAO_HOA", ly_do="nhieu da dat %s o thuoc do nay: doc cot 'qua VA hon mua-giu/ban-giu' hoac 'calmar'" % _pc(nhieu))
    if p_vuot <= NHIEU_ALPHA and that - nhieu >= NHIEU_CHENH_TOI_THIEU:
        return dict(ra, ket_luan="VUOT_NHIEU")
    if p_duoi <= NHIEU_ALPHA and nhieu - that >= NHIEU_CHENH_TOI_THIEU:
        return dict(ra, ket_luan="DUOI_NHIEU")
    return dict(ra, ket_luan="NGANG_NHIEU")


def doc_that_voi_nhieu(cac_o: list[dict], tham_chieu: dict | None, engine: int, nhom: str = "cao", thuoc_do: str = "qua") -> dict:
    """Doc cac o THAT (cua MOT engine) theo R2 so voi `NHIEU@e<engine>` trong `tham_chieu` (= `doc_tham_chieu()`). Moi o = {cum: thi truong,
    mau: che_do_kieu_lot, kl, ln, dd, chay, hon_moc, nhom}. KHONG so engine 3 voi engine 4. Thi truong < 3 ket luan duoc bi bo (`cum_bo`)."""
    ra0 = {"engine": int(engine), "nhom": nhom, "thuoc_do": thuoc_do}
    ks = ((tham_chieu or {}).get("kich_ban") or {}).get("NHIEU@e%d" % int(engine))
    tc = (((ks or {}).get("nhieu") or {}).get(nhom) or {}).get(thuoc_do)
    if not tc or not tc.get("xs"):
        return dict(ra0, n_cum=0, n_chuoi_nhieu=0, ket_luan="CHUA_DU", ly_do="chua co doi chung nhieu cho engine %d / nhom %s" % (int(engine), nhom))
    ecdf = (ks.get("ecdf") or {}).get(nhom) or {}
    theo_cum: dict = {}
    for o in cac_o:
        if o.get("nhom", nhom) == nhom:
            theo_cum.setdefault(o["cum"], []).append(o)
    gt: dict = {}
    for c, lst in theo_cum.items():
        tb, _ = tb_o(lst, thuoc_do, ecdf)
        if tb is not None:
            gt[c] = tb
    ra = so_voi_nhieu_cum(gt, tc["xs"], thuoc_do)
    ra.update(ra0, so_o=sum(len(v) for v in theo_cum.values()), cum_bo=sorted(c for c in theo_cum if c not in gt))
    tm = (((ks.get("theo_mau") or {}).get(nhom) or {}).get(thuoc_do)) if thuoc_do in THUOC_DO_NHI_PHAN else None
    if tm and gt and "nhieu" in ra:                  # co cau mau cua ket qua that lech co cau mau cua nhieu -> so sanh 'tao' tren thuoc do nhi phan
        mix = []
        for c in gt:
            v = [tm[o["mau"]]["tb"] for o in theo_cum[c] if o.get("mau") in tm and gia_tri_o(o, thuoc_do) is not None]
            if v:
                mix.append(float(np.mean(v)))
        if len(mix) == len(gt):
            ra["nhieu_cung_co_cau_mau"] = round(float(np.mean(mix)), 4)
            if abs(ra["nhieu_cung_co_cau_mau"] - ra["nhieu"]) >= 0.05:
                ra["canh_bao"] = ("co cau mau cua ket qua that lech co cau mau cua nhieu: nhieu cung co cau mau la %s (khong phai %s) - doc them cot calmar"
                                  % (_pc(ra["nhieu_cung_co_cau_mau"]), _pc(ra["nhieu"])))
    return ra


def doc_that_theo_engine(cac_o: list[dict], tham_chieu: dict | None, nhom: str = "cao", thuoc_dos=THUOC_DO) -> dict:
    """{engine: {thuoc_do: ket qua R2}} - tach theo engine cua tung ket qua that (ma cu = 3 ; ma moi = 4)."""
    ra: dict = {}
    for e in sorted({int(o.get("engine") or 3) for o in cac_o}):
        lst = [o for o in cac_o if int(o.get("engine") or 3) == e and o.get("nhom", nhom) == nhom]
        if lst:
            ra[e] = {td: doc_that_voi_nhieu(lst, tham_chieu, e, nhom, td) for td in thuoc_dos}
    return ra


def cac_o_that(ung_vien: list[dict], kq: dict[str, dict]) -> list[dict]:
    """Ket qua THAT cua vong lap (`vong_lap.kq_cung_thuoc_do`: ung vien + ket qua) -> cac o cua R2. 'Chay tai khoan' lay tu ly do (ma cu ghi
    'chay tai khoan o lot thu', ma moi ghi 'CHAY TAI KHOAN ...')."""
    from nhan import vong_lap as VL
    ra = []
    for u in ung_vien:
        r = kq.get(u["id"])
        if not r:
            continue
        ts = u.get("tham_so") or {}
        che_do, kieu = u.get("che_do") or ts.get("che_do"), u.get("kieu_lot") or ts.get("kieu_lot") or "phang"
        ra.append({"cum": u["ma"], "mau": "%s_%s" % (che_do, kieu), "nhom": VL.nhom_cua(u), "kl": r.get("ket_luan"),
                   "ln": r.get("loi_suat_nam_pct"), "dd": r.get("maxdd_pct"), "hon_moc": r.get("hon_moc_pct"),
                   "chay": "chay tai khoan" in str(r.get("ly_do") or "").lower(), "engine": r.get("phien_ban_engine") or VL.ENGINE_CU})
    return ra


def chenh_voi_nhieu(tk: dict, khoa: str, nhom: str = "cao", thuoc_do: str = "qua") -> dict | None:
    """DO NHAY cua phep do: kich ban `khoa` (vd 'DAO_DONG@e4') co thuoc do cao hon NHIEU cung engine bao nhieu? (chenh trung binh theo chuoi,
    z kieu Welch). Neu chang KIEM nhay thi chenh > 0 va tang theo lieu loi the ; None khi thieu."""
    ks = (tk.get("kich_ban") or {}).get(khoa)
    ref = (tk.get("kich_ban") or {}).get("NHIEU@e%d" % int(ks["engine"])) if ks else None
    if not ks or not ref:
        return None
    a, b = ks["nhieu"][nhom][thuoc_do], ref["nhieu"][nhom][thuoc_do]
    if a["tb"] is None or b["tb"] is None or a["n"] < 2 or b["n"] < 2:
        return None
    se = math.sqrt(a["sd"] ** 2 / a["n"] + b["sd"] ** 2 / b["n"])
    d = a["tb"] - b["tb"]
    return {"chenh": round(d, 4), "z": round(d / se, 2) if se > 0 else None, "n": a["n"], "n_nhieu": b["n"]}


def kich_thuoc_phep_thu(dong: list[dict], kb: str = "NHIEU", khop_bar: str = "duong_di", so_don_vi: int = 12, lan: int = 500) -> dict | None:
    """KICH THUOC THAT cua `vong_lap.so_sanh_nhom` (McNemar ghep cap + Fisher): phep thu do coi moi o la doc lap nhung cac o cua mot thi truong
    chung MOT duong gia. Lay ngau nhien `so_don_vi` chuoi NHIEU (= 'thi truong' that cua may nha), chay CHINH `so_sanh_nhom` tren moi o cua chung,
    lap `lan` lan: tren du lieu khong co loi the, ty le ket luan 'HON' phai ~ <= 5%. Neu > 10% thi chi doc `so_sanh_nhom` theo nguong thuc nghiem
    (`chenh_p95`). None khi it hon `so_don_vi` chuoi."""
    from nhan import vong_lap as VL
    hop, _ = _hop_chinh(dong)
    rows = _cac_chuoi(hop, kb, khop_bar)
    if len(rows) < so_don_vi or so_don_vi < 1 or lan < 1:
        return None
    rng = np.random.default_rng(RUT_HAT)
    dem = {"cao_vs_ngau": {"HON": 0, "KEM": 0, "NGANG": 0, "CHUA_DU": 0}, "cao_vs_doi": {"HON": 0, "KEM": 0, "NGANG": 0, "CHUA_DU": 0}}
    chenh: dict = {"cao_vs_ngau": [], "cao_vs_doi": []}
    cap = {"cao_vs_ngau": [], "cao_vs_doi": []}
    for _ in range(int(lan)):
        chon = rng.choice(len(rows), size=int(so_don_vi), replace=False)
        uv, kq = _ung_vien_va_kq([(rows[int(i)], t, m) for i in chon for t, m in rows[int(i)]["mau"].items()])
        ss = VL.so_sanh_nhom(uv, kq)
        for k in dem:
            dem[k][ss[k]["ket_luan"]] += 1
            if ss[k]["chenh"] is not None:
                chenh[k].append(float(ss[k]["chenh"]))
            cap[k].append(ss[k]["cap"] if k == "cao_vs_ngau" else min(ss[k]["n_cao"], ss[k]["n_doi"]))
    ra = {"kich_ban": kb, "khop_bar": khop_bar, "engine": ENGINE_CUA[khop_bar], "so_don_vi": int(so_don_vi), "lan": int(lan), "n_chuoi_nhieu": len(rows)}
    for k in dem:
        ch = np.asarray(chenh[k], float)
        ra[k] = {"dem": dem[k], "ty_le_hon": round(dem[k]["HON"] / lan, 4), "ty_le_kem": round(dem[k]["KEM"] / lan, 4),
                 "ty_le_chua_du": round(dem[k]["CHUA_DU"] / lan, 4), "so_cap_tb": round(float(np.mean(cap[k])), 1),
                 "chenh_p05": round(float(np.percentile(ch, 5)), 4) if len(ch) else None,
                 "chenh_p95": round(float(np.percentile(ch, 95)), 4) if len(ch) else None,
                 "doc_theo_thuc_nghiem": bool(dem[k]["HON"] / lan > 0.10 or dem[k]["KEM"] / lan > 0.10)}
    return ra


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
