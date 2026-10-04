# -*- coding: utf-8 -*-
"""ho_so_bot.py - HO SO CO CHE cua mot con bot, do tu LICH SU LENH THAT (deals tester MT5 / export MQL5).

Chu du an 04/10/2026: *"moi bot se co chien luoc va cach quan tri cung nhu tinh dac sac khac nhau. Muc tieu cua the brain
la boc tach duoc co che / chien luoc hoac yeu to dac sac cua cac con bot de thu ap dung cheo hoac ket hop them vao cac he
thong va ea sau nay."*

Day la nua "DO" cua `nhan/khoi_co_che.py` (kho 52 khoi = nua "tin truoc khi co so lieu"): moi KHOI co mot ten phep do
(`Khoi.kiem`); module nay co mot ham do cho moi ten (`PHEP_DO`), chay tren bang vi the / lenh do `lenh_tester` doc tu bao cao
tester (hoac `boc_lich_su.chuan_hoa` tu export MQL5) va tra cho TUNG KHOI:

    co / khong / khong_ro / khong_do_duoc     +  do_tin (cao | vua | thap)  +  ly do ngan  +  so lieu

Ba cai khong duoc nham: `khong` = do duoc va khong thay; `khong_ro` = thay mot phan nhung khong ket luan duoc;
`khong_do_duoc` = lich su nay KHONG CHO PHEP do (qua it chuoi, thieu cot, thieu bang Orders...). Mot khoi khong do duoc khong
bao gio duoc ghi la "khong co".

## Quy tac do (doc truoc khi tin bat ky ket luan nao)

* CHUOI (ro) = cac lenh cung chieu mo chong len nhau; lenh mo khi cung chieu da het lenh dang mo la chuoi MOI. LEVEL cua mot
  lenh them = SO LENH CUNG CHIEU DANG MO truc luc no mo (`n_mo`) - chinh la dai luong ma tham so kieu "sau N lenh" cua cac bot
  dung (CCBSN: moc 10/20/30/40/50). Tia lenh lam `n_mo` nho hon so lenh da mo cua chuoi (`tang`): hai dai luong khac nhau.
* Phep do phia MO (lot, buoc, gio, chieu) chi dung gio mo / gia mo / lot -> khong phu thuoc chat luong ghep deal vao-ra.
  Phep do phia THOAT (TP, tia, hoa von) dung cach ghep: `chat_luong.dang_tin_ghep` thap -> ha do tin / khong ket luan.
* Lenh DOI UNG (mo nguoc chieu khi chuoi doi dien da sau) duoc nhan bang BUOC NHAY TAN SUAT: moc do sau `k0` ma duoi no chieu
  nguoc khong bat dau, tu do tro len thi bat dau (so lan bat dau / thoi gian cho). Khong dua vao do tre vao lenh thu k (EA hay
  doi tick sau), khong dua vao lot. Ro doi ung bi LOAI khoi cac bang buoc / lot / thoat cua chuoi chinh.
* Moi bang theo bac (`bang`) luon duoc in: ke ca khi khong ket luan duoc mo hinh, AI van dung duoc BANG de dung lai tung bac.
* Moi so do duoc (`tham_so`) mang don vi + khoi, de `khop_knob` doi voi bo `.set`: gia tri `.set` trung gia tri do (co doi don vi
  point / pip / gia) trong CUNG HO tham so (loc theo ten) la dau hieu ten tham so nao quy dinh hanh vi nao. Mot lan trung la
  GIA THUYET; trung nhieu bo `.set` khac nhau (`khop_knob_nhieu`) moi la bang chung.
* NGUOI THANG / bot song sot la mau chon theo ket qua: ho so nay MO TA co che, khong do loi nhuan (cham diem = `cham_diem`).

Kiem bang du lieu CAI SAN DAP AN: `test_ho_so_bot.py` (bo mo phong bot theo tung tick viet rieng, khong dung chung code voi bo do).
Bang chung chua co: bao cao tester that cua bot that (xem `tai_lieu/KHO_CO_CHE_BOT.md`, muc "do tu deals").
"""
from __future__ import annotations

import dataclasses
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from nhan import boc_lich_su as BL
from nhan import khoi_co_che as KC
from nhan import lenh_tester as LT

PHIEN_BAN = "1"
LAB = Path(__file__).resolve().parent.parent

CO, KHONG, KHONG_RO, KHONG_DO_DUOC = "co", "khong", "khong_ro", "khong_do_duoc"
KET_LUAN = (CO, KHONG, KHONG_RO, KHONG_DO_DUOC)
DO_TIN = ("cao", "vua", "thap")

#: "cung luc" = cung tick (bao cao ghi theo giay)
DUNG_SAI_GIAY = 2.0
#: it chuoi hon nay thi cac phep do ve chuoi chua dang tin
TOI_THIEU_RO = 20
#: so lenh toi thieu de ket luan bat ky dieu gi
TOI_THIEU_LENH = 30
#: ngan thoi gian cho bang do sau (host_k) o phep do doi ung
KMAX = 80
#: sai so tuong doi san khi so hai muc: gia lot / buoc bi lam tron, bar bi luong tu hoa
SAN_SAI_SO = 0.03


# ============================================================== 0. TIEN ICH
def _f(x, nd: int = 4):
    """So an toan cho JSON: NaN / inf -> None, numpy -> python."""
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(x):
        return None
    return round(x, nd)


def _json(x):
    """Doi numpy / pandas / set thanh kieu JSON thuan (khoa dict thanh chuoi)."""
    if isinstance(x, dict):
        return {str(k): _json(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_json(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return _f(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, (pd.Timestamp,)):
        return str(x)[:19]
    if isinstance(x, (set, frozenset)):
        return sorted(_json(v) for v in x)
    if x is pd.NaT:
        return None
    return x


def _rcv(x) -> float:
    """He so bien thien ben vung = 0,7413 * IQR / |trung vi|. Hang so (ke ca rai theo luoi lam tron) -> 0."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return float("inf")
    q1, q2, q3 = np.percentile(x, [25, 50, 75])
    if abs(q2) < 1e-12:
        return float("inf") if q3 - q1 > 1e-12 else 0.0
    return float(0.7413 * (q3 - q1) / abs(q2))


def _do_tin(n: int, tot: int = 30, vua: int = 12) -> str:
    return "cao" if n >= tot else "vua" if n >= vua else "thap"


def _ha(do_tin: str, bac: int = 1) -> str:
    i = DO_TIN.index(do_tin)
    return DO_TIN[min(len(DO_TIN) - 1, i + bac)]


def _tin_thap_hon(a: str, b: str) -> str:
    return DO_TIN[max(DO_TIN.index(a), DO_TIN.index(b))]


def _q(x, p):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(np.percentile(x, p)) if len(x) else float("nan")


# ============================================================== 1. NAP DU LIEU -> NGU CANH
@dataclass
class Ctx:
    """Moi thu cac phep do can: lenh (moi LENH mot dong) + dac trung luc mo + bang chuoi."""
    lenh: pd.DataFrame
    ro: pd.DataFrame
    pip: float
    ma: str
    hop_dong: float | None
    von_dau: float | None
    khung_phut: float | None
    tick_s: float
    chat_luong: dict
    canh_bao: list
    phoi: np.ndarray            # thoi gian (giay) chieu nay trong, chieu kia dang mo `k` lenh (chi so k)
    thoi_gian: dict             # tong thoi gian co lenh / ca hai chieu cung mo
    o_goc: pd.DataFrame | None = None      # lenh truoc khi quet (de dung lai khi loc lenh doi ung)
    attrs: dict = dataclasses.field(default_factory=dict)
    doi_ung: dict | None = None            # ket qua phep do doi ung (neu da chay)

    def loc(self, giu: np.ndarray) -> "Ctx":
        """Ctx moi chi gom cac lenh `giu` (mang bool theo `lenh`): quet lai de n_mo / host_k / chuoi tinh dung khi bo lenh doi ung."""
        o = self.o_goc.loc[self.lenh.index[np.asarray(giu, bool)]]
        c = _dung_ctx(o.reset_index(drop=True), self.attrs, self.ma, self.pip, self.hop_dong, self.von_dau, self.khung_phut,
                      list(self.canh_bao))
        c.doi_ung = self.doi_ung
        return c


def _chuan_ma(s) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(s).upper())


def _uoc_tick_s(o: pd.DataFrame) -> float:
    """Khoang giay giua hai tick lien tiep cua bo mo phong: neu moi moc gio roi vao <= 8 gia tri giay-trong-phut (>= 200 moc) la
    luoi tick (Model 1 / OHLC): lay khoang cach trung vi giua cac gia tri do; nguoc lai (tick that) 1 giay."""
    t = np.concatenate([o["mo"].to_numpy("datetime64[ns]").astype("int64") / 1e9,
                        o["dong"].dropna().to_numpy("datetime64[ns]").astype("int64") / 1e9]) if len(o) else np.array([])
    if len(t) < 200:
        return 1.0
    s = np.unique(np.round(t % 60.0))
    if len(s) > 8:
        return 1.0
    if len(s) == 1:
        return 60.0
    gap = np.diff(np.r_[s, s[0] + 60.0])
    return float(max(1.0, np.median(gap)))


def _quet(o: pd.DataFrame) -> dict:
    """Quet su kien theo thoi gian (dong truoc mo khi cung giay, tru dong cua chinh lenh vua mo): moi lenh nhan
    `n_mo` (lenh cung chieu dang mo truoc no), `host_k` (lenh nguoc chieu dang mo), tong lot dang mo, gia lenh gan nhat / xau nhat,
    ro, tang; cong don thoi gian 'chieu nay trong, chieu kia dang mo k lenh' (phep do doi ung) va thoi gian co lenh."""
    n = len(o)
    mo = o["mo"].to_numpy("datetime64[ns]").astype("int64") / 1e9
    dg = o["dong"].to_numpy("datetime64[ns]")
    dong = np.where(np.isnat(dg), np.inf, dg.astype("int64") / 1e9)
    chieu = o["chieu"].to_numpy(int)
    lot = o["lot_vao"].to_numpy(float)
    gia = o["gia_mo"].to_numpy(float)
    ev = [(mo[i], 1, i) for i in range(n)]
    ev += [(dong[i], 0 if dong[i] > mo[i] else 2, i) for i in range(n) if np.isfinite(dong[i])]
    ev.sort(key=lambda e: (e[0], e[1], e[2]))
    nan = np.full(n, np.nan)
    n_mo = np.zeros(n, int)
    host_k = np.zeros(n, int)
    lot_cung, host_lot, host_tb, host_lag = nan.copy(), nan.copy(), nan.copy(), nan.copy()
    tb_cung = nan.copy()
    p_cuoi, t_cuoi, p_xau = nan.copy(), nan.copy(), nan.copy()
    lot_prev, gia_prev, t_prev_ro = nan.copy(), nan.copy(), nan.copy()
    lot_ref = nan.copy()
    ro = np.zeros(n, int)
    tang = np.zeros(n, int)
    phoi = np.zeros(KMAX + 1)
    t_ca_hai = t_mot = 0.0
    t_dir = {1: 0.0, -1: 0.0}
    act = {1: [], -1: []}
    cur_ro = {1: -1, -1: -1}
    dem_tang = {1: 0, -1: 0}
    last = {1: (np.nan, np.nan, np.nan), -1: (np.nan, np.nan, np.nan)}
    next_ro = 0
    t_truoc = None
    for t, k, i in ev:
        if t_truoc is not None and t > t_truoc:
            dt = t - t_truoc
            nb, ns = len(act[1]), len(act[-1])
            if nb and ns:
                t_ca_hai += dt
            if nb or ns:
                t_mot += dt
            for d in (1, -1):
                if act[d]:
                    t_dir[d] += dt
                if not act[d] and act[-d]:
                    phoi[min(len(act[-d]), KMAX)] += dt
        t_truoc = t
        c = int(chieu[i])
        if k != 1:                                            # dong
            try:
                act[c].remove(i)
            except ValueError:
                pass
            continue
        own, host = act[c], act[-c]
        n_mo[i], host_k[i] = len(own), len(host)
        if own:
            lot_cung[i] = sum(lot[j] for j in own)
            tb_cung[i] = sum(lot[j] * gia[j] for j in own) / lot_cung[i]
            ref = own[-1]
            p_cuoi[i], t_cuoi[i], lot_ref[i] = gia[ref], mo[ref], lot[ref]
            p_xau[i] = min(gia[j] for j in own) if c > 0 else max(gia[j] for j in own)
        if host:
            hl = sum(lot[j] for j in host)
            host_lot[i] = hl
            host_tb[i] = sum(lot[j] * gia[j] for j in host) / hl
            host_lag[i] = t - mo[host[-1]]
        if not own:
            cur_ro[c], next_ro, dem_tang[c] = next_ro, next_ro + 1, 0
        ro[i], tang[i] = cur_ro[c], dem_tang[c]
        if dem_tang[c] > 0:
            lot_prev[i], gia_prev[i], t_prev_ro[i] = last[c]
        dem_tang[c] += 1
        last[c] = (lot[i], gia[i], t)
        own.append(i)
    cuoi = max(float(mo.max()), float(dong[np.isfinite(dong)].max()) if np.isfinite(dong).any() else float(mo.max())) if n else 0.0
    khoang = cuoi - float(mo.min()) if n else 0.0
    return {"n_mo": n_mo, "host_k": host_k, "lot_cung": lot_cung, "host_lot": host_lot, "host_tb": host_tb, "tb_cung": tb_cung,
            "host_lag": host_lag, "p_cuoi": p_cuoi, "t_cuoi": t_cuoi, "p_xau": p_xau, "lot_prev": lot_prev,
            "gia_prev": gia_prev, "t_prev_ro": t_prev_ro, "lot_ref": lot_ref, "ro": ro, "tang": tang, "phoi": phoi,
            "thoi_gian": {"co_lenh": t_mot, "ca_hai": t_ca_hai, "mua": t_dir[1], "ban": t_dir[-1], "khoang": khoang},
            "mo_s": mo, "dong_s": dong}


def _so_du_luc_mo(o: pd.DataFrame, von_dau: float | None, nap_rut: list | None) -> np.ndarray:
    """So du luc mo tung lenh = von dau + tong tien da chot (dong <= luc mo) + nap/rut sau ngay dau. NaN neu khong biet von dau."""
    n = len(o)
    if not von_dau or n == 0:
        return np.full(n, np.nan)
    mo = o["mo"].to_numpy("datetime64[ns]").astype("int64") / 1e9
    dg = o["dong"].to_numpy("datetime64[ns]")
    ok = ~np.isnat(dg) & np.isfinite(o["tien"].to_numpy(float))
    td = dg[ok].astype("int64") / 1e9
    tien = o["tien"].to_numpy(float)[ok]
    ord_ = np.argsort(td, kind="stable")
    td, cs = td[ord_], np.cumsum(tien[ord_])
    idx = np.searchsorted(td, mo, side="right") - 1
    bal = von_dau + np.where(idx >= 0, cs[np.clip(idx, 0, None)], 0.0)
    for t, x in (nap_rut or [])[1:]:
        ts = pd.Timestamp(t).value / 1e9
        bal = bal + np.where(mo >= ts, float(x), 0.0)
    return bal


def _bang_ro(o: pd.DataFrame, pip: float) -> pd.DataFrame:
    """Mot dong / chuoi: chieu, mo, dong, so_lenh, lot_dau, lot_tong, lot_dinh, n_mo_max, host_k_dau, tien, va voi chuoi da dong:
    `dot_cuoi` = cac lenh dong trong DUNG_SAI_GIAY cua lenh dong sau cung: n_cuoi, tien_cuoi, tp_gia / tp_pip (so voi gia mo trung
    binh CUA NHOM CUOI), ly_do (tp / sl / stopout / ea) cua nhom cuoi, so_dot (so dot dong)."""
    hang = []
    for r, g in o.groupby("ro", sort=True):
        chieu = int(g["chieu"].iat[0])
        lot = g["lot_vao"].to_numpy(float)
        gm = g["gia_mo"].to_numpy(float)
        da_dong = bool(g["dong"].notna().all())
        h = {"ro": int(r), "chieu": chieu, "mo": g["mo"].min(), "so_lenh": int(len(g)),
             "lot_dau": float(lot[0]), "lot_tong": float(lot.sum()), "gia_dau": float(gm[0]),
             "gia_tb": float((gm * lot).sum() / lot.sum()),
             "lot_dinh": float((g["lot_cung"].fillna(0.0) + g["lot_vao"]).max()),
             "n_mo_max": int(g["n_mo"].max()) + 1, "host_k_dau": int(g["host_k"].iat[0]),
             "host_lot_dau": float(g["host_lot"].iat[0]) if pd.notna(g["host_lot"].iat[0]) else np.nan,
             "host_lag_dau": float(g["host_lag"].iat[0]) if pd.notna(g["host_lag"].iat[0]) else np.nan,
             "bal_dau": float(g["bal"].iat[0]) if "bal" in g.columns and pd.notna(g["bal"].iat[0]) else np.nan,
             "da_dong": da_dong, "dong": g["dong"].max() if da_dong else pd.NaT,
             "tien": float(g["tien"].sum()) if da_dong and g["tien"].notna().all() else np.nan}
        if da_dong:
            t = g["dong"].to_numpy("datetime64[ns]").astype("int64") / 1e9
            cuoi = t >= t.max() - DUNG_SAI_GIAY
            lc, mc = lot[cuoi], gm[cuoi]
            gd = g["gia_dong"].to_numpy(float)[cuoi]
            gia_dong_tb = float((gd * lc).sum() / lc.sum())
            gia_mo_tb = float((mc * lc).sum() / lc.sum())
            tp_gia = chieu * (gia_dong_tb - gia_mo_tb)
            tien_c = g["tien"].to_numpy(float)[cuoi]
            ly = g["ly_do_ra"].to_numpy(object)[cuoi] if "ly_do_ra" in g.columns else np.array([""] * int(cuoi.sum()))
            ts = np.sort(t)
            h.update(n_cuoi=int(cuoi.sum()), lot_cuoi=float(lc.sum()), gia_dong_tb=gia_dong_tb, gia_mo_cuoi=gia_mo_tb,
                     tp_gia=tp_gia, tp_pip=tp_gia / pip, tien_cuoi=float(np.nansum(tien_c)) if np.isfinite(tien_c).any() else np.nan,
                     so_dot=int(1 + (np.diff(ts) > DUNG_SAI_GIAY).sum()) if len(ts) > 1 else 1,
                     ly_tp=int((ly == "tp").sum()), ly_sl=int((ly == "sl").sum()), ly_so=int((ly == "stopout").sum()),
                     ly_ea=int((ly == "ea").sum()))
        else:
            h.update(n_cuoi=0, lot_cuoi=np.nan, gia_dong_tb=np.nan, gia_mo_cuoi=np.nan, tp_gia=np.nan, tp_pip=np.nan,
                     tien_cuoi=np.nan, so_dot=0, ly_tp=0, ly_sl=0, ly_so=0, ly_ea=0)
        hang.append(h)
    return pd.DataFrame(hang)


def _chat_luong(o: pd.DataFrame, ro: pd.DataFrame, attrs: dict, canh_bao: list) -> dict:
    n = len(o)
    ghep = attrs.get("ghep") or {}
    tong_ghep = sum(ghep.values()) or 0
    tin = sum(ghep.get(k, 0) for k in ("ma_vi_the", "don", "loi", "loi_gan", "cung_gia"))
    ty_tin = (tin / tong_ghep) if tong_ghep else None
    ks = attrs.get("kiem_so_du") or {}
    co_order = bool((o["kieu_vao"].astype(str) != "").any()) if "kieu_vao" in o.columns else False
    ly = o["ly_do_ra"].astype(str) if "ly_do_ra" in o.columns else pd.Series([""] * n)
    dong = o["dong"].notna()
    ty_ly = float((ly[dong].isin(["tp", "sl", "stopout"])).mean()) if dong.any() else 0.0
    span = (o["mo"].max() - o["mo"].min()).total_seconds() / 86400.0 if n else 0.0
    q = {"n_lenh": int(n), "n_ro": int(len(ro)), "n_dong": int(dong.sum()), "ngay": round(span, 1),
         "dang_tin_ghep": _f(ty_tin, 3), "ghep": dict(ghep) if ghep else None, "mo_coi": attrs.get("mo_coi"),
         "ty_le_sai_so_du": ks.get("ty_le_sai"), "co_order": co_order, "co_ly_do_ra": bool(ty_ly > 0.02),
         "ty_le_ly_do_ra_biet": _f(ty_ly, 3), "von_dau": attrs.get("von_dau")}
    ly_do = []
    if n < TOI_THIEU_LENH:
        ly_do.append("chi %d lenh (< %d)" % (n, TOI_THIEU_LENH))
    if len(ro) < 5:
        ly_do.append("chi %d chuoi" % len(ro))
    q["trang_thai"] = "CHUA_DO_DUOC" if ly_do else "DAT"
    q["ly_do"] = ly_do
    if ty_tin is not None and ty_tin < 0.9:
        canh_bao.append("chi %.0f%% lenh ghep vao-ra dang tin (con lai doan FIFO): cac phep do phia THOAT ha do tin" % (100 * ty_tin))
    if ks.get("ty_le_sai") and ks["ty_le_sai"] > 0.02:
        canh_bao.append("cot so du lech o %.1f%% dong: doc bao cao co the sai" % (100 * ks["ty_le_sai"]))
    return q


def _dung_ctx(o: pd.DataFrame, attrs: dict, ma_ten: str, pip: float, hd: float | None, von_dau: float | None,
              khung_phut: float | None, canh_bao: list) -> Ctx:
    """Tu bang lenh (mot ma, da sap theo gio mo, co cot `tien`) dung moi cot dac trung + bang chuoi + chat luong."""
    o = o.copy()
    q = _quet(o)
    for k in ("n_mo", "host_k", "lot_cung", "host_lot", "host_tb", "host_lag", "p_cuoi", "t_cuoi", "p_xau", "lot_prev",
              "gia_prev", "t_prev_ro", "lot_ref", "ro", "tang", "tb_cung"):
        o[k] = q[k]
    o["mo_s"] = q["mo_s"]
    o["dong_s"] = q["dong_s"]
    o["buoc_cuoi"] = o["chieu"] * (o["p_cuoi"] - o["gia_mo"]) / pip          # + = gia di NGUOC chieu lenh truoc khi them (pip)
    o["buoc_xau"] = o["chieu"] * (o["p_xau"] - o["gia_mo"]) / pip
    o["gap_s"] = q["mo_s"] - o["t_cuoi"]
    o["ty_lot"] = o["lot_vao"] / o["lot_prev"]
    o["bal"] = _so_du_luc_mo(o, von_dau, attrs.get("nap_rut"))
    o["bac"] = o["n_mo"] + 1                    # bac = so lenh cung chieu dang mo SAU khi lenh nay mo
    o["bac_tang"] = o["tang"] + 1               # bac theo so lenh da them vao chuoi (khong tru lenh da dong tia)
    o["lot_dau"] = o.groupby("ro")["lot_vao"].transform("first")
    ro = _bang_ro(o, pip)
    cl = _chat_luong(o, ro, attrs, canh_bao)
    tick_s = _uoc_tick_s(o)
    return Ctx(lenh=o, ro=ro, pip=pip, ma=ma_ten, hop_dong=hd, von_dau=von_dau, khung_phut=khung_phut, tick_s=tick_s,
               chat_luong=cl, canh_bao=canh_bao, phoi=q["phoi"], thoi_gian=q["thoi_gian"], o_goc=o.drop(columns=[
                   c for c in o.columns if c in _COT_QUET]), attrs=attrs)


_COT_QUET = ("n_mo", "host_k", "lot_cung", "host_lot", "host_tb", "host_lag", "p_cuoi", "t_cuoi", "p_xau", "lot_prev", "gia_prev",
             "t_prev_ro", "lot_ref", "ro", "tang", "tb_cung", "mo_s", "dong_s", "buoc_cuoi", "buoc_xau", "gap_s", "ty_lot", "bal",
             "lot_dau", "bac", "bac_tang")


def chuan_bi(v, ma: str | None = None, pip: float | None = None, hop_dong: float | None = None,
             von_dau: float | None = None, khung_phut: float | None = None) -> Ctx:
    """Bang vi the (`lenh_tester.ghep_vi_the` / `vi_the_tu_tep`) hoac bang lenh chuan (`boc_lich_su.chuan_hoa`) hoac duong dan
    tep bao cao -> Ctx. Chi mot MA moi lan (nhieu ma: chon ma nhieu lenh nhat va canh bao - buoc theo pip khac nhau giua cac ma)."""
    canh_bao: list[str] = []
    if isinstance(v, (str, Path)):
        v = LT.vi_the_tu_tep(v)
    attrs = dict(getattr(v, "attrs", None) or {})
    if "deal_vao" in v.columns:
        o = LT.gop_theo_lenh(v).copy()
    else:
        o = BL.chuan_hoa(v).copy()
        attrs = {**attrs, **o.attrs}
        o["deal_vao"] = np.arange(1, len(o) + 1)
        o["lot_vao"] = o["lot"]
        o["so_lan_dong"] = o["dong"].notna().astype(int)
        for c in ("cm_vao", "cm_ra", "ly_do_ra", "kieu_vao"):
            if c not in o.columns:
                o[c] = ""
        o["gio_dat"] = pd.NaT
    if o.empty:
        raise ValueError("lich su rong")
    o["lot_vao"] = o["lot_vao"].where(o["lot_vao"] > 0, o["lot"]).astype(float)
    cm = o["ma"].map(_chuan_ma)
    dem = cm.value_counts()
    chon = _chuan_ma(ma) if ma else dem.index[0]
    if chon not in set(dem.index):
        raise ValueError("lich su khong co ma %s (co: %s)" % (ma, ", ".join(list(dem.index)[:6])))
    if len(dem) > 1 and not ma:
        canh_bao.append("lich su co %d ma (%s): chi do ma %s (nhieu lenh nhat); buoc / lot cua cac ma khac nhau khong gop duoc"
                        % (len(dem), ", ".join(list(dem.index)[:5]), chon))
    o = o[cm == chon].copy()
    ma_ten = str(o["ma"].iat[0])
    o["mo"] = pd.to_datetime(o["mo"])
    o["dong"] = pd.to_datetime(o["dong"])
    o = o.sort_values(["mo", "deal_vao"], kind="stable").reset_index(drop=True)
    if pip is None:
        pip = attrs.get("pip")
        if isinstance(pip, dict):
            pip = pip.get(ma_ten)
    pip = float(pip) if pip else BL.doan_pip(ma_ten, float(o["gia_mo"].median()))
    hd = hop_dong
    if hd is None:
        h = attrs.get("hop_dong")
        hd = h.get(ma_ten) if isinstance(h, dict) else h
    hd = float(hd) if hd else None
    for c in ("loi", "hoa_hong", "swap"):
        if c not in o.columns:
            o[c] = np.nan
    tien = o["loi"].astype(float).copy()
    if tien.isna().all() and hd:
        tien = o["chieu"] * (o["gia_dong"] - o["gia_mo"]) * o["lot_vao"] * hd
    o["tien"] = tien + o["hoa_hong"].astype(float).fillna(0.0) + o["swap"].astype(float).fillna(0.0)
    o.loc[o["dong"].isna(), "tien"] = np.nan
    if von_dau is None:
        von_dau = attrs.get("von_dau")
    return _dung_ctx(o, attrs, ma_ten, pip, hd, von_dau, khung_phut, canh_bao)


# ============================================================== 2. DUNG CU CHUNG
def _kq(ket_luan: str, do_tin: str, ly_do: str, so_lieu: dict | None = None, tham_so: dict | None = None,
        khoi: dict | None = None, bang=None) -> dict:
    """Ket qua mot phep do. `khoi` = {ma_khoi: (ket_luan, do_tin, ly_do)} cho TUNG khoi cua danh muc ma phep do nay kiem."""
    assert ket_luan in KET_LUAN and do_tin in DO_TIN, (ket_luan, do_tin)
    return {"ket_luan": ket_luan, "do_tin": do_tin, "ly_do": ly_do, "so_lieu": so_lieu or {}, "tham_so": tham_so or {},
            "khoi": khoi or {}, "bang": bang}


def _tham_so(gia_tri, don_vi: str, khoi: str, ghi_chu: str = "") -> dict:
    return {"gia_tri": gia_tri, "don_vi": don_vi, "khoi": khoi, "ghi_chu": ghi_chu}


def _tb_bac(bac: np.ndarray, val: np.ndarray, toi_thieu: int = 3, kmax: int = 200) -> pd.DataFrame:
    """Bang theo bac: so mau, trung vi, he so bien thien ben vung, phan vi 10 / 90."""
    hang = []
    bac = np.asarray(bac)
    val = np.asarray(val, float)
    for k in sorted(set(bac.tolist())):
        if k > kmax:
            break
        x = val[bac == k]
        x = x[np.isfinite(x)]
        if len(x) < toi_thieu:
            continue
        hang.append({"bac": int(k), "n": int(len(x)), "trung_vi": float(np.median(x)), "rcv": _rcv(x),
                     "p10": _q(x, 10), "p90": _q(x, 90)})
    return pd.DataFrame(hang, columns=["bac", "n", "trung_vi", "rcv", "p10", "p90"])


def _phan_doan(bac, gia_tri, tol: float = 0.05, ngoai_le: float = 0.12, log: bool = True) -> list[dict]:
    """Chia day (bac, gia_tri) thanh it doan LIEN TIEP nhat sao cho trong moi doan moi gia tri lech trung vi cua doan <= `tol` (ti le;
    toi da `ngoai_le` ti le so bac trong doan duoc lech - bac hiem bi nhieu). Hoa le (cung so doan): chon tong lech nho nhat. Dung de
    tim 'bac doi gia tri o chi so lenh co dinh' (buoc, he so lot, TP...)."""
    bac = np.asarray(bac, int)
    x = np.asarray(gia_tri, float)
    m = len(x)
    if m == 0:
        return []
    y = np.log(np.maximum(x, 1e-12)) if log else x
    nguong = np.log1p(tol) if log else tol

    def hop_le(i: int, j: int):
        seg = y[i:j + 1]
        tv = float(np.median(seg))
        lech = np.abs(seg - tv)
        if log:
            vuot = lech > nguong
        else:
            vuot = lech > max(nguong * abs(tv), 1e-12)
        if vuot.sum() > int(ngoai_le * len(seg)):
            return None
        return float(np.minimum(lech, 10.0).sum()), tv

    inf = (10 ** 9, 0.0)
    best = [inf] * (m + 1)
    best[0] = (0, 0.0)
    prev = [-1] * (m + 1)
    tvs = [0.0] * (m + 1)
    for j in range(m):
        for i in range(j + 1):
            if best[i][0] >= 10 ** 9:
                continue
            h = hop_le(i, j)
            if h is None:
                continue
            ung = (best[i][0] + 1, best[i][1] + h[0])
            if ung < best[j + 1]:
                best[j + 1], prev[j + 1], tvs[j + 1] = ung, i, h[1]
    doan = []
    j = m
    while j > 0:
        i = prev[j]
        seg = x[i:j]
        doan.append({"tu": int(bac[i]), "den": int(bac[j - 1]), "so_bac": int(j - i), "gia_tri": float(np.exp(tvs[j]) if log else tvs[j])})
        j = i
    return doan[::-1]


def _ty_le_lech(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1e-12)


# ============================================================== 3. CAC PHEP DO
# ---- 3.1 doi_ung: lenh nguoc chieu mo ngay sau lenh thu N cua chuoi doi dien
SHIFTS = (45.0, 90.0, 180.0, 360.0, 720.0, 1500.0)
#: "vao ngay": phan lon chuoi moi mo trong ngan nay sau khi chuoi cu dong (tick tha, thi truong vang tick thua)
GAP_NGAY_S = 20.0


def _cua_so(c: Ctx) -> float:
    """Giay: 'cung luc' = trong cua so nay (2 tick, toi thieu 5 giay)."""
    return max(2.0 * c.tick_s, 5.0)


def _ung_vien_doi_ung(bang: pd.DataFrame, cn: str, cf: str, cz: str, tran_truoc: float = 0.35, toi_thieu: int = 8,
                      ty_toi_thieu: float = 0.0):
    """(N, cac bac kich hoat, 'moi bac') : bac nho nhat >= 2 co f >= 0,5 va hon null >= 0,4 (>= `toi_thieu` lenh chu; voi lat cat
    'chieu kia dang trong' phai chiem >= `ty_toi_thieu` cac lenh chu o bac do: luoi hai chieu luon co lenh phia kia, chi con vai %
    luc chieu kia trong va khi do no cung sap mo lai - khong phai doi ung). 'moi bac' = truoc N van co f cao."""
    cand = [int(r["bac"]) for r in bang.to_dict("records")
            if r["bac"] >= 2 and r[cn] >= toi_thieu and r[cn] >= ty_toi_thieu * r["n"]
            and r[cf] >= 0.5 and r[cf] - r[cz] >= 0.4]
    if not cand:
        return None, [], False
    N = min(cand)
    truoc = bang[(bang["bac"] >= 2) & (bang["bac"] < N) & (bang[cn] >= 5)]
    return N, cand, bool(len(truoc) and (truoc[cf] > tran_truoc).any())


def _do_doi_ung(c: Ctx) -> tuple[dict, np.ndarray | None]:
    """Voi moi lenh chu thu k: co lenh NGUOC chieu mo trong `L` giay sau no khong (f_k), so voi cua so DICH khoi (+-45..1500 giay,
    cung do rong) lam null. Hai lat cat: (a) CHI cac lenh chu luc do chieu kia DANG TRONG (host_k = 0) - nhan ra lenh bao hiem tren bot
    mot chieu va ca bot hai chieu luc chieu kia tam trong; (b) moi lenh chu - cho luoi hai chieu luon co lenh phia kia.
    Bac N = bac nho nhat >= 2 co f >= 0,5, hon null >= 0,4, truoc do f <= 0,35. Lenh doi ung = lenh nguoc chieu rot vao cua so cua
    cac lenh chu o bac kich hoat. Tra (ket qua, mat na lenh doi ung hoac None)."""
    o = c.lenh
    n = len(o)
    ten = ("lenh_doi_ung_sau_n_lenh", "lenh_doi_ung_stop")
    t = o["mo_s"].to_numpy(float)
    ch = o["chieu"].to_numpy(int)
    k = o["n_mo"].to_numpy(int) + 1
    ex = o["host_k"].to_numpy(int) == 0
    L = _cua_so(c)
    if n < TOI_THIEU_LENH or not (set(ch.tolist()) == {1, -1}):
        ly = "chi %d lenh" % n if n < TOI_THIEU_LENH else "lich su chi co mot chieu lenh: khong co gi de doi ung"
        kl = KHONG_DO_DUOC if n < TOI_THIEU_LENH else KHONG
        dt = "thap" if kl == KHONG_DO_DUOC else "cao"
        return _kq(kl, dt, ly, khoi={x: (kl, dt, ly) for x in ten}), None
    tb = {d: np.sort(t[ch == d]) for d in (1, -1)}
    hit = np.zeros(n, bool)
    null = np.zeros(n)
    for d in (1, -1):
        idx = ch == d
        tt = t[idx]
        so = tb[-d]

        def co(delta: float) -> np.ndarray:
            return np.searchsorted(so, tt + delta + L, side="right") - np.searchsorted(so, tt + delta, side="left") > 0
        hit[idx] = co(0.0)
        acc = np.zeros(len(tt))
        for sh in SHIFTS:
            acc += co(sh) + co(-sh - L)
        null[idx] = acc / (2 * len(SHIFTS))
    hang = []
    for kk in sorted(set(k.tolist())):
        s_all = k == kk
        s_ex = s_all & ex
        if s_all.sum() < 5:
            continue
        hang.append({"bac": int(kk), "n": int(s_all.sum()), "f": float(hit[s_all].mean()), "null": float(null[s_all].mean()),
                     "n_ex": int(s_ex.sum()), "f_ex": float(hit[s_ex].mean()) if s_ex.any() else float("nan"),
                     "null_ex": float(null[s_ex].mean()) if s_ex.any() else float("nan")})
    bang = pd.DataFrame(hang, columns=["bac", "n", "f", "null", "n_ex", "f_ex", "null_ex"])
    k_sau = int(bang["bac"].max()) if len(bang) else 0
    so_lieu = {"cua_so_s": L, "bac_sau_nhat_du_mau": k_sau, "bang": bang.round(3).to_dict("records")[:45]}
    co_stop = _do_stop_doi_ung(c)
    khoi_ung = lambda r: {"lenh_doi_ung_sau_n_lenh": r, "lenh_doi_ung_stop": co_stop}
    # ---- chon lat cat
    N, cand, moi_bac = _ung_vien_doi_ung(bang, "n_ex", "f_ex", "null_ex", ty_toi_thieu=0.5)
    lat = "chi_luc_chieu_kia_trong"
    if N is None:
        N, cand, moi_bac = _ung_vien_doi_ung(bang, "n", "f", "null")
        lat = "moi_lenh"
    if N is None:
        if k_sau >= 14 and not len(bang[(bang["bac"] >= 2) & (bang["f"] >= 0.3)]):
            kl, dt, ly = KHONG, "vua", "khong thay lenh nguoc chieu nao mo ngay sau lenh chu o bac 2..%d (du mau)" % k_sau
        elif k_sau < 14:
            kl, dt, ly = KHONG_RO, "thap", ("khong thay doi ung nhung chuoi chi sau toi bac %d: chua toi bac kich hoat co the "
                                           "(CCBSN 5-12 can >= 14)" % k_sau)
        else:
            kl, dt, ly = KHONG_RO, "thap", "co dau hieu mo ho o bac thap (f 0,3-0,5), khong du ro de goi la doi ung"
        r = (kl, dt, ly)
        return _kq(kl, dt, ly, so_lieu, khoi=khoi_ung(r)), None
    row = bang[bang["bac"] == N].iloc[0]
    if moi_bac:
        ly = ("lenh nguoc chieu xuat hien o nhieu bac thap truoc bac N=%d: giong luoi hai phia dong thoi, khong phai doi ung sau N" % N)
        return _kq(KHONG_RO, "thap", ly, so_lieu, khoi=khoi_ung((KHONG_RO, "thap", ly))), None
    # ---- lenh doi ung = lenh nguoc chieu trong cua so sau lenh chu o bac kich hoat
    mask = np.zeros(n, bool)
    chu_cua = {}
    cho = np.where(np.isin(k, cand) & (ex if lat == "chi_luc_chieu_kia_trong" else True))[0]
    chi_so = {d: np.where(ch == d)[0] for d in (1, -1)}
    mo_theo = {d: t[chi_so[d]] for d in (1, -1)}
    for i in cho:
        d_ng = -ch[i]
        lo = np.searchsorted(mo_theo[d_ng], t[i], side="left")
        hi = np.searchsorted(mo_theo[d_ng], t[i] + L, side="right")
        for j in chi_so[d_ng][lo:hi]:
            if not mask[j]:
                mask[j] = True
                chu_cua[int(j)] = int(i)
                break
    n_dt = int(mask.sum())
    lot = o.loc[mask, "lot_vao"].to_numpy(float)
    host_lot = o.loc[mask, "host_lot"].to_numpy(float)
    ty = lot / host_lot
    ty = ty[np.isfinite(ty)]
    ro_chu = o["ro"].to_numpy(int)
    dong_ro = o.groupby("ro")["dong_s"].max()
    ket_cung = []
    for j, i in chu_cua.items():
        dj = o["dong_s"].iat[j]
        dr = dong_ro.get(ro_chu[i], np.inf)
        if np.isfinite(dj) and np.isfinite(dr):
            ket_cung.append(abs(dj - dr) <= max(L, 2 * DUNG_SAI_GIAY))
    ro_toi_N = int((c.ro["n_mo_max"] >= N).sum())
    ty_ket = float(np.mean(ket_cung)) if ket_cung else float("nan")
    lot_rcv = _rcv(lot)
    kieu_lot = ("co_dinh" if (len(lot) >= 10 and lot_rcv <= 0.05) else
                "theo_ty_le_chuoi" if (len(ty) >= 10 and _rcv(ty) <= 0.05 and lot_rcv > 0.05) else "khong_ro")
    so_lieu.update(bac_kich_hoat=N, cac_bac=cand, lat_cat=lat, so_lenh_doi_ung=n_dt, ty_le_lenh=_f(n_dt / n, 4),
                   so_chuoi_toi_bac_N=ro_toi_N, doi_ung_moi_chuoi=_f(n_dt / max(ro_toi_N, 1), 2),
                   lot_trung_vi=_f(np.median(lot)), lot_rcv=_f(lot_rcv), lot_khac_nhau=int(len(set(np.round(lot, 4)))),
                   ty_lot_host_trung_vi=_f(np.median(ty)) if len(ty) else None, ty_lot_host_rcv=_f(_rcv(ty)) if len(ty) else None,
                   kieu_lot=kieu_lot, dong_cung_chuoi=_f(ty_ket, 3))
    f_col, z_col, n_col = ("f_ex", "null_ex", "n_ex") if lat == "chi_luc_chieu_kia_trong" else ("f", "null", "n")
    m_N = int(row[n_col])
    dt = _do_tin(m_N, 20, 8)
    ly = ("doi ung mo dung khi chuoi cung chieu dat %d lenh (%d / %d lenh chu bac %d co lenh nguoc ngay sau; null %.0f%%)"
          % (N, round(float(row[f_col]) * m_N), m_N, N, 100 * float(row[z_col])))
    ts = {"so_lenh_kich_hoat": _tham_so(N, "lenh", "lenh_doi_ung_sau_n_lenh",
                                        "chuoi cung chieu dat so lenh nay (lech 1 la cach dem; xem khop_knob)"),
          "lot_doi_ung": _tham_so(_f(np.median(lot)), "lot", "lenh_doi_ung_sau_n_lenh", "lot cua lenh nguoc chieu (%s)" % kieu_lot)}
    if kieu_lot == "theo_ty_le_chuoi":
        ts["ty_lot_doi_ung"] = _tham_so(_f(np.median(ty)), "ty_le", "lenh_doi_ung_sau_n_lenh", "lot doi ung / tong lot chuoi chu")
    return (_kq(CO, dt, ly, so_lieu, ts, khoi=khoi_ung((CO, dt, ly)), bang=bang), mask)


def _do_stop_doi_ung(c: Ctx) -> tuple:
    o = c.lenh
    if not c.chat_luong["co_order"]:
        return (KHONG_DO_DUOC, "thap", "thieu bang Orders: khong biet lenh vao bang lenh cho (stop) hay lenh thi truong")
    kv = o["kieu_vao"].astype(str)
    ty = float((kv == "cho_stop").mean())
    if ty < 0.02:
        return (KHONG, "cao", "khong lenh nao vao bang lenh cho STOP (%.1f%%)" % (100 * ty))
    st = o[kv == "cho_stop"]
    ch = st["chieu"].to_numpy(int)
    luan_phien = float((ch[1:] != ch[:-1]).mean()) if len(ch) > 1 else 0.0
    if ty >= 0.5 and luan_phien >= 0.7:
        return (CO, _do_tin(len(st), 30, 12), "%.0f%% lenh vao bang STOP, chieu luan phien %.0f%%" % (100 * ty, 100 * luan_phien))
    return (KHONG_RO, "thap", "%.0f%% lenh vao bang STOP nhung chieu khong luan phien (%.0f%%)" % (100 * ty, 100 * luan_phien))


# ---- 3.2 huong: hai chieu doc lap / mot chieu
def _do_huong(c: Ctx) -> dict:
    ro = c.ro
    n = len(ro)
    khoi_ten = ("hai_chieu_doc_lap", "mot_chieu")
    if n < TOI_THIEU_RO:
        ly = "chi %d chuoi chinh (< %d)" % (n, TOI_THIEU_RO)
        return _kq(KHONG_DO_DUOC, "thap", ly, khoi={x: (KHONG_DO_DUOC, "thap", ly) for x in khoi_ten})
    tg = c.thoi_gian
    nmua = int((ro["chieu"] > 0).sum())
    ty_mua = nmua / n
    ca_hai = tg["ca_hai"] / max(tg["co_lenh"], 1.0)
    p_obs = float((ro["host_k_dau"] > 0).mean())
    p_exp = []
    for td, tk in ((tg["mua"], tg["ban"]), (tg["ban"], tg["mua"])):
        den = tg["khoang"] - td
        if den > 0:
            p_exp.append((tk - tg["ca_hai"]) / den)
    p_exp = float(np.mean(p_exp)) if p_exp else float("nan")
    so_lieu = {"so_chuoi": n, "ty_mua": _f(ty_mua, 3), "ty_thoi_gian_ca_hai": _f(ca_hai, 3),
               "ty_chuoi_vao_khi_chieu_kia_mo": _f(p_obs, 3), "ty_ky_vong_neu_doc_lap": _f(p_exp, 3)}
    dt = _do_tin(n, 60, 25)
    if ty_mua >= 0.95 or ty_mua <= 0.05:
        ly = "%.0f%% chuoi cung mot chieu (%s)" % (100 * max(ty_mua, 1 - ty_mua), "mua" if ty_mua > 0.5 else "ban")
        return _kq(CO, dt, ly, so_lieu, {"chieu": _tham_so("mua" if ty_mua > 0.5 else "ban", "chieu", "mot_chieu")},
                   khoi={"mot_chieu": (CO, dt, ly), "hai_chieu_doc_lap": (KHONG, dt, ly)})
    if min(ty_mua, 1 - ty_mua) >= 0.2 and ca_hai >= 0.05:
        ly = ("mua %.0f%% / ban %.0f%% so chuoi; %.0f%% thoi gian co lenh la ca hai chieu cung mo"
              % (100 * ty_mua, 100 * (1 - ty_mua), 100 * ca_hai))
        if math.isfinite(p_exp) and abs(p_obs - p_exp) > 0.3:
            ly += "; CHU Y chuoi bat dau khong doc lap voi chieu kia (%.0f%% vs ky vong %.0f%%)" % (100 * p_obs, 100 * p_exp)
            dt = _ha(dt)
        return _kq(CO, dt, ly, so_lieu, {"chieu": _tham_so("hai_chieu", "chieu", "hai_chieu_doc_lap")},
                   khoi={"hai_chieu_doc_lap": (CO, dt, ly), "mot_chieu": (KHONG, dt, ly)})
    ly = ("co ca hai chieu (mua %.0f%%) nhung chi %.1f%% thoi gian cung mo: luan phien theo tin hieu hoac khong doc lap"
          % (100 * ty_mua, 100 * ca_hai))
    return _kq(KHONG_RO, "thap", ly, so_lieu, khoi={"hai_chieu_doc_lap": (KHONG_RO, "thap", ly), "mot_chieu": (KHONG, "vua", ly)})


# ---- 3.3 vao_lai: vao ngay hay cho gia lui
def _do_vao_lai(c: Ctx) -> dict:
    ro = c.ro
    khoi_ten = ("vao_ngay_lap_tuc", "vao_lai_sau_cho_lui")
    gap_s, gap_pip = [], []
    for d in (1, -1):
        r = ro[(ro["chieu"] == d)].sort_values("mo")
        if len(r) < 2:
            continue
        dong = r["dong"].to_numpy("datetime64[ns]")
        mo = r["mo"].to_numpy("datetime64[ns]")
        gdong = r["gia_dong_tb"].to_numpy(float)
        gdau = r["gia_dau"].to_numpy(float)
        for i in range(1, len(r)):
            if np.isnat(dong[i - 1]) or not np.isfinite(gdong[i - 1]):
                continue
            gap_s.append((mo[i] - dong[i - 1]) / np.timedelta64(1, "s"))
            gap_pip.append(d * (gdong[i - 1] - gdau[i]) / c.pip)
    gap_s, gap_pip = np.asarray(gap_s, float), np.asarray(gap_pip, float)
    n = len(gap_s)
    if n < 20:
        ly = "chi %d lan vao lai (< 20)" % n
        return _kq(KHONG_DO_DUOC, "thap", ly, khoi={x: (KHONG_DO_DUOC, "thap", ly) for x in khoi_ten})
    ngan = max(_cua_so(c), GAP_NGAY_S)
    ngay = float((gap_s <= ngan).mean())
    p80 = _q(gap_s, 80)
    so_lieu = {"so_lan_vao_lai": n, "ty_vao_trong_gioi_han": _f(ngay, 3), "gioi_han_s": ngan, "gap_s_trung_vi": _f(np.median(gap_s), 1),
               "gap_s_p80": _f(p80, 1), "gap_pip_trung_vi": _f(np.median(gap_pip), 2), "gap_pip_rcv": _f(_rcv(gap_pip), 3)}
    dt = _do_tin(n, 60, 25)
    # (1) khoang lui CO DINH duong: moi lan cho gia lui dung X pip roi moi vao
    ok = gap_pip[gap_s > _cua_so(c)]
    med = float(np.median(ok)) if len(ok) else 0.0
    rcv = _rcv(ok) if len(ok) >= 10 else float("inf")
    if len(ok) >= 20 and med > 0 and rcv <= 0.35 and float(np.quantile(ok, 0.1)) > 0:
        ly = "chuoi moi mo khi gia lui them ~%.1f pip so voi gia dong (do lech nho: %.2f)" % (med, rcv)
        return _kq(CO, dt, ly, so_lieu, {"cho_lui_pip": _tham_so(_f(med, 2), "pip", "vao_lai_sau_cho_lui",
                                                                  "lui nguoc chieu lenh moi so voi gia dong")},
                   khoi={"vao_lai_sau_cho_lui": (CO, dt, ly), "vao_ngay_lap_tuc": (KHONG, dt, ly)})
    # (2) vao ngay: phan lon trong vai tick
    if p80 <= ngan:
        ly = "%.0f%% chuoi moi mo trong %.0f giay sau khi chuoi cu dong; khoang lui ~%.1f pip (khong co dinh)" % (
            100 * ngay, ngan, float(np.median(gap_pip)))
        return _kq(CO, dt, ly, so_lieu, {"tre_vao_lai_s": _tham_so(_f(np.median(gap_s), 1), "giay", "vao_ngay_lap_tuc")},
                   khoi={"vao_ngay_lap_tuc": (CO, dt, ly), "vao_lai_sau_cho_lui": (KHONG, dt, ly)})
    ly = ("chuoi moi khong mo ngay (80%% sau %.0f giay) va cung khong co khoang lui gia co dinh (rcv %.2f): co the vao theo tin hieu - "
          "xem dieu_kien_vao (can du lieu gia)" % (p80, rcv if np.isfinite(rcv) else -1))
    return _kq(KHONG_RO, "thap", ly, so_lieu, khoi={"vao_ngay_lap_tuc": (KHONG, "vua", ly), "vao_lai_sau_cho_lui": (KHONG_RO, "thap", ly)})


# ---- 3.4 buoc_theo_bac: luoi deu / gian dan / doi buoc o moc so lenh
def _sai_so_bac(tb: pd.DataFrame) -> float:
    """Do rong cua dung sai khi so hai muc: nhieu cua trung vi tung bac (rcv / sqrt(n)) nhan 2,5, san 6%, tran 25%."""
    if not len(tb):
        return 0.06
    nhieu = np.median(tb["rcv"].to_numpy(float)[np.isfinite(tb["rcv"].to_numpy(float))] / np.sqrt(tb["n"].to_numpy(float)))
    return float(min(0.25, max(0.06, 2.5 * nhieu))) if np.isfinite(nhieu) else 0.06


def _khop_hinh_hoc(bac, y, tol: float) -> dict | None:
    """y_k = s0 * g^(k - k0) (tuy chon: roi di ngang sau mot bac tran) khop moi bac trong `tol`? g trong [0,7 ; 1,5], |g - 1| >= 2%."""
    bac = np.asarray(bac, float)
    y = np.asarray(y, float)
    m = len(y)
    if m < 4 or (y <= 0).any():
        return None
    ly = np.log(y)
    for p in range(m, 2, -1):
        x = bac[:p]
        A = np.vstack([x - x[0], np.ones(p)]).T
        h, _res, _r, _sv = np.linalg.lstsq(A, ly[:p], rcond=None)
        g = float(np.exp(h[0]))
        if not (0.7 <= g <= 1.5) or abs(g - 1.0) < 0.02:
            continue
        du_doan = np.exp(A @ h)
        lech = np.abs(du_doan / y[:p] - 1.0)
        if p < m:
            tran = float(np.median(y[p:]))
            lech2 = np.abs(tran / y[p:] - 1.0)
            if (lech2 > tol).any() or tran < du_doan[-1] * (1 - tol) or (g > 1 and tran < y[p - 1] * (1 - tol)):
                continue
            tran_bac = int(bac[p])
        else:
            tran, tran_bac = None, None
        if (lech > tol).any():
            continue
        return {"g": g, "s0": float(np.exp(h[1])), "bac0": int(x[0]), "tran": tran,
                "tran_tu_bac": tran_bac, "lech_toi_da": float(lech.max())}
    return None


def _bang_bac_buoc(o: pd.DataFrame, cot_bac: str, cot_buoc: str) -> pd.DataFrame:
    them = o[(o["n_mo"] >= 1) & (o[cot_buoc] > 0)]
    return _tb_bac(them[cot_bac].to_numpy(int), them[cot_buoc].to_numpy(float), toi_thieu=3)


def _do_buoc(c: Ctx) -> dict:
    o = c.lenh
    ten = ("luoi_gian_cach_deu", "luoi_buoc_gian_dan", "luoi_buoc_theo_bac")
    them = o[o["n_mo"] >= 1]
    if len(them) < 40:
        ly = "chi %d lenh them vao chuoi dang mo (< 40)" % len(them)
        return _kq(KHONG_DO_DUOC, "thap", ly, khoi={x: (KHONG_DO_DUOC, "thap", ly) for x in ten})
    ty_thuan = float((them["buoc_cuoi"] <= 0).mean())
    so_lieu = {"so_lenh_them": int(len(them)), "ty_them_o_gia_thuan_chieu": _f(ty_thuan, 3)}
    if ty_thuan > 0.25:
        ly = ("%.0f%% lenh them mo o gia THUAN chieu so voi lenh truoc (khong phai luoi nghich): buoc khong dai dien; xem them_khi_hoi"
              % (100 * ty_thuan))
        return _kq(KHONG_RO, "thap", ly, so_lieu, khoi={x: (KHONG_RO, "thap", ly) for x in ten})
    # chon moc tinh buoc (lenh gan nhat / lenh xau nhat) va cach dem bac (n_mo / tang) cho bang GON nhat
    thu = []
    for cb in ("buoc_cuoi", "buoc_xau"):
        for cl in ("bac", "bac_tang"):
            if cl == "bac_tang" and (o["bac"] == o["bac_tang"]).mean() > 0.97:
                continue
            tb = _bang_bac_buoc(o, cl, cb)
            if len(tb) < 3:
                continue
            tol = _sai_so_bac(tb)
            dn = _phan_doan(tb["bac"], tb["trung_vi"], tol=tol)
            thu.append((len(dn), float(np.median(tb["rcv"])), cb, cl, tb, tol, dn))
    if not thu:
        ly = "khong du bac co >= 3 mau de lap bang buoc (chuoi qua nong hoac qua it chuoi)"
        return _kq(KHONG_DO_DUOC, "thap", ly, so_lieu, khoi={x: (KHONG_DO_DUOC, "thap", ly) for x in ten})
    thu.sort(key=lambda r: (r[0], r[1], r[2] != "buoc_cuoi", r[3] != "bac"))
    nd, _rcv_tb, cb, cl, tb, tol, dn = thu[0]
    n_nghich = int((them[cb] > 0).sum())
    dt = _do_tin(n_nghich, 100, 40)
    if len(tb) < 5:
        dt = _ha(dt)
    k_sau = int(tb["bac"].max())
    nghich = them[them[cb] > 0]

    def p10_doan(tu: int, den: int) -> float:
        x = nghich.loc[(nghich[cl] >= tu) & (nghich[cl] <= den), cb].to_numpy(float)
        return _q(x, 10)
    do_vuot = float(np.nanmedian((tb["trung_vi"] - tb["p10"]).to_numpy(float)[tb["n"].to_numpy(int) >= 8])) if (tb["n"] >= 8).any() else 0.0
    do_vuot = max(0.0, do_vuot) if np.isfinite(do_vuot) else 0.0
    so_lieu.update(moc_buoc=cb, cach_dem_bac=cl, dung_sai=_f(tol, 3), bac_sau_nhat_du_mau=k_sau, so_bac_co_mau=int(len(tb)),
                   do_vuot_nguong_pip=_f(do_vuot, 2),
                   bang=tb.round(2).to_dict("records")[:60], doan=[{k: _f(v, 2) if isinstance(v, float) else v for k, v in d.items()} for d in dn])
    gdan = _khop_hinh_hoc(tb["bac"], tb["trung_vi"], tol) if nd >= 2 else None
    if nd == 1:
        v = p10_doan(dn[0]["tu"], dn[0]["den"])
        tot = ("; chua thay bac sau hon %d: co the con doi buoc o bac sau hon" % k_sau)
        ly = "buoc gan nhu khong doi qua %d bac (~%.1f pip, lech <= %.0f%%)" % (len(tb), v, 100 * tol)
        ts = {"buoc_pip": _tham_so(_f(v, 2), "pip", "luoi_gian_cach_deu",
                                   "phan vi 10%% cua buoc nghich (uoc luong gia tri cai; trung vi %.1f gom phan vuot nguong do tick thua)"
                                   % dn[0]["gia_tri"])}
        return _kq(CO, dt, ly + (tot if k_sau < 12 else ""), so_lieu, ts,
                   khoi={"luoi_gian_cach_deu": (CO, dt, ly), "luoi_buoc_gian_dan": (KHONG, dt, ly), "luoi_buoc_theo_bac": (KHONG, dt, ly)}, bang=tb)
    if gdan is not None:
        tran = ("; roi di ngang tu bac %d o %.1f pip" % (gdan["tran_tu_bac"], gdan["tran"])) if gdan["tran"] else ""
        ly = "buoc tang deu %.1f%%/bac tu %.1f pip%s (khop moi bac, lech <= %.0f%%)" % (100 * (gdan["g"] - 1), gdan["s0"], tran, 100 * tol)
        ts = {"buoc_dau_pip": _tham_so(_f(max(gdan["s0"] - do_vuot, 0.0), 2), "pip", "luoi_buoc_gian_dan",
                                       "buoc truoc lenh thu %d (da tru do vuot nguong %.1f pip)" % (gdan["bac0"], do_vuot)),
              "he_so_buoc": _tham_so(_f(gdan["g"], 3), "he_so", "luoi_buoc_gian_dan", "buoc bac sau / buoc bac truoc")}
        if gdan["tran"]:
            ts["tran_buoc_pip"] = _tham_so(_f(max(gdan["tran"] - do_vuot, 0.0), 2), "pip", "luoi_buoc_gian_dan",
                                           "bac tran tu bac %d" % gdan["tran_tu_bac"])
        return _kq(CO, dt, ly, so_lieu, ts, khoi={"luoi_buoc_gian_dan": (CO, dt, ly), "luoi_gian_cach_deu": (KHONG, dt, ly),
                                                  "luoi_buoc_theo_bac": (KHONG, dt, ly)}, bang=tb)
    ts = {}
    mo_ta = []
    for i, d in enumerate(dn, 1):
        v = p10_doan(d["tu"], d["den"])
        mo_ta.append("bac %d-%d: ~%.1f" % (d["tu"], d["den"], v))
        ts["buoc_bac_%d" % i] = _tham_so(_f(v, 2), "pip", "luoi_buoc_theo_bac",
                                         "bac %d..%d (phan vi 10%%; trung vi %.1f)" % (d["tu"], d["den"], d["gia_tri"]))
        if i >= 2:
            ts["moc_doi_buoc_%d" % (i - 1)] = _tham_so(d["tu"] - 1, "lenh", "luoi_buoc_theo_bac",
                                                       "lenh thu %d la lenh dau cua bac buoc moi (lech 1 la cach dem)" % d["tu"])
    ly = "buoc doi %d lan theo bac: %s pip (dung sai %.0f%%)" % (nd - 1, "; ".join(mo_ta), 100 * tol)
    nho = min(d["so_bac"] for d in dn) < 2
    dt2 = _ha(dt) if nho else dt
    return _kq(CO, dt2, ly, so_lieu, ts, khoi={"luoi_buoc_theo_bac": (CO, dt2, ly), "luoi_gian_cach_deu": (KHONG, dt2, ly),
                                              "luoi_buoc_gian_dan": (KHONG, dt2, ly)}, bang=tb)


# ---- 3.5 lot_theo_bac: phang / cong / nhan / nhan theo bac / tong gap doi / fibo / nhan sau SL
def _buoc_lot(lots) -> float:
    """Buoc lot cua san: 0,01 (chuan san ban le; bot toan lot 0,1 van tinh buoc 0,01 de phep thu CHAT, khong long); chi nho hon neu
    lot quan sat can (0,001 / 0,0001). Buoc that cua tung ma truyen vao `buoc_lot=` khi biet."""
    x = np.asarray(lots, float)
    x = x[np.isfinite(x) & (x > 0)]
    for b in (0.01, 0.001):
        if len(x) and np.all(np.abs(x / b - np.round(x / b)) < 1e-6):
            return b
    return 0.0001


def _phu_khoang(lo, hi) -> tuple[float, float, float]:
    """Diem phu nhieu khoang dong [lo, hi] nhat: (lo, hi) cua vung phu cuc dai dau tien, ty le khoang phu."""
    lo = np.asarray(lo, float)
    hi = np.asarray(hi, float)
    n = len(lo)
    if n == 0:
        return float("nan"), float("nan"), 0.0
    x = np.concatenate([lo, hi])
    d = np.concatenate([np.ones(n, int), -np.ones(n, int)])
    od = np.lexsort((-d, x))                       # cung toa do: dau khoang (+1) truoc cuoi khoang (-1) -> khoang dong
    cum = np.cumsum(d[od])
    k = int(np.argmax(cum))
    b_hi = float(x[od[k + 1]]) if k + 1 < len(od) else float(x[od[k]])
    return float(x[od[k]]), b_hi, float(cum[k]) / n


def _khoang_he_so(lot_ref, lot, bl: float, ham: str = "lam_tron"):
    """Khoang he so m nhat quan voi (lot truoc, lot sau): `lam_tron` / `cat_xuong` = lot sau lam tron tu (lot truoc DA lam tron x m);
    `rong_*` = ca lot truoc cung la ban lam tron cua gia tri that (bat luon kieu 'lam tron mot lan tu lot dau')."""
    lot_ref = np.asarray(lot_ref, float)
    lot = np.asarray(lot, float)
    if ham == "lam_tron":
        return (lot - bl / 2 - 1e-9) / lot_ref, (lot + bl / 2 + 1e-9) / lot_ref
    if ham == "cat_xuong":
        return (lot - 1e-9) / lot_ref, (lot + bl + 1e-9) / lot_ref
    if ham == "rong_lam_tron":
        return (lot - bl / 2 - 1e-9) / (lot_ref + bl / 2), (lot + bl / 2 + 1e-9) / np.maximum(lot_ref - bl / 2, 1e-9)
    return (lot - 1e-9) / (lot_ref + bl), (lot + bl + 1e-9) / np.maximum(lot_ref, 1e-9)


def _doan_he_so(bac, lo, hi, phu: float = 0.95) -> list[dict]:
    """Chia cac bac thanh it doan nhat sao cho trong moi doan co MOT he so phu >= `phu` cac khoang (tham lam, dai nhat truoc)."""
    bac = np.asarray(bac, int)
    lo = np.asarray(lo, float)
    hi = np.asarray(hi, float)
    muc = sorted(set(bac.tolist()))
    doan = []
    i = 0
    while i < len(muc):
        j = i
        tot = None
        while j < len(muc):
            sel = (bac >= muc[i]) & (bac <= muc[j])
            a, b, cov = _phu_khoang(lo[sel], hi[sel])
            # moi bac (>= 5 mau) cung phai nam trong he so chung: tranh bo qua nguyen mot bac vi chi chiem < 5% so dong
            if cov >= phu and np.isfinite(a):
                diem = (a + b) / 2.0 if np.isfinite(b) else a
                lech = False
                for m in muc[i:j + 1]:
                    t = sel & (bac == m)
                    if int(t.sum()) >= 5 and float(((lo[t] <= diem + 1e-9) & (hi[t] >= diem - 1e-9)).mean()) < 0.8:
                        lech = True
                        break
                if not lech:
                    tot = (j, a, b, cov, int(sel.sum()))
                    j += 1
                    continue
            break
        if tot is None:
            sel = bac == muc[i]
            a, b, cov = _phu_khoang(lo[sel], hi[sel])
            tot = (i, a, b, cov, int(sel.sum()))
        doan.append({"tu": int(muc[i]), "den": int(muc[tot[0]]), "lo": tot[1], "hi": tot[2], "phu": tot[3], "n": tot[4]})
        i = tot[0] + 1
    return doan


_HAM_LOT = ("lam_tron", "cat_xuong", "rong_lam_tron", "rong_cat_xuong")
_GIAI_THICH_HAM = {"lam_tron": "lam tron gan nhat tung lenh", "cat_xuong": "cat xuong tung lenh",
                   "rong_lam_tron": "lam tron (khong chac theo chuoi hay theo tich)", "rong_cat_xuong": "cat xuong (khong chac theo chuoi hay theo tich)"}


def _fib(k: int, lech: int = 0) -> int:
    a, b = 1, 1
    for _ in range(k - 1 + lech):
        a, b = b, a + b
    return a


def _ung_vien_lot(them: pd.DataFrame, bl: float) -> list[dict]:
    """Moi ung vien = (cot bac, moc tham chieu, kieu lam tron): cac khoang he so + so doan he so can de giai thich."""
    lot = them["lot_vao"].to_numpy(float)
    prev = them["lot_prev"].to_numpy(float)
    ref = them["lot_ref"].to_numpy(float)
    cot = [("bac", them["bac"].to_numpy(int))]
    bt = them["bac_tang"].to_numpy(int)
    if (bt != cot[0][1]).mean() >= 0.05:
        cot.append(("bac_tang", bt))
    ung = []
    for cn, bc in cot:
        for tenc, rf in (("lenh_vua_mo", prev), ("lenh_con_mo_moi_nhat", ref)):
            for ham in _HAM_LOT:
                lo, hi = _khoang_he_so(rf, lot, bl, ham)
                ok = np.isfinite(lo) & np.isfinite(hi) & (hi > lo) & (lo > 0)
                if int(ok.sum()) < 20:
                    continue
                a1, b1, cov1 = _phu_khoang(lo[ok], hi[ok])
                dn = _doan_he_so(bc[ok], lo[ok], hi[ok])
                ung.append({"cot_bac": cn, "moc": tenc, "ham": ham, "rong": ham.startswith("rong"), "a": a1, "b": b1, "cov": cov1,
                            "dn": dn, "xau": any(x["phu"] < 0.95 for x in dn), "bac": bc[ok], "ok": ok,
                            "rong_tong": float(sum(x["hi"] - x["lo"] for x in dn if np.isfinite(x["hi"] - x["lo"])))})
    return ung


def _he_so_tich(them: pd.DataFrame, bl: float) -> dict | None:
    """He so MOT hang so voi lam tron MOT LAN tu lot dau: lot_k = tron(lot_dau x m^(k-1))."""
    lot = them["lot_vao"].to_numpy(float)
    lot0 = them["lot_dau"].to_numpy(float)
    bk = them["bac_tang"].to_numpy(float)          # thu tu lenh k trong chuoi (k >= 2 voi lenh them)
    sel = bk >= 2
    if int(sel.sum()) < 20:
        return None
    best = None
    for ham in ("lam_tron", "cat_xuong"):
        if ham == "lam_tron":
            ca, cb = (lot[sel] - bl / 2 - 1e-9) / lot0[sel], (lot[sel] + bl / 2 + 1e-9) / lot0[sel]
        else:
            ca, cb = (lot[sel] - 1e-9) / lot0[sel], (lot[sel] + bl + 1e-9) / lot0[sel]
        e = 1.0 / (bk[sel] - 1.0)
        lo_t = np.power(np.maximum(ca, 1e-9), e)
        hi_t = np.power(cb, e)
        a, b, cov = _phu_khoang(lo_t, hi_t)
        if best is None or (cov, -(b - a)) > (best["cov"], -(best["b"] - best["a"])):
            best = {"ham": ham, "a": a, "b": b, "cov": cov}
    return best


def _do_lot_theo_bac(c: Ctx, buoc_lot: float | None = None) -> dict:
    o = c.lenh
    ten = ("lot_phang", "lot_cong", "lot_nhan", "lot_nhan_theo_bac", "lot_tong_gap_doi", "lot_fibo")
    them = o[(o["tang"] >= 1)]
    if len(them) < 40:
        ly = "chi %d lenh them vao chuoi (< 40)" % len(them)
        return _kq(KHONG_DO_DUOC, "thap", ly, khoi={x: (KHONG_DO_DUOC, "thap", ly) for x in ten})
    bl = float(buoc_lot) if buoc_lot else _buoc_lot(o["lot_vao"])
    lot = them["lot_vao"].to_numpy(float)
    lot0 = them["lot_dau"].to_numpy(float)
    prev = them["lot_prev"].to_numpy(float)
    cung = them["lot_cung"].to_numpy(float)
    bac = them["bac"].to_numpy(int)
    bang = (pd.DataFrame({"bac": bac, "lot": lot, "r0": lot / lot0, "q": lot / prev}).groupby("bac")
            .agg(n=("lot", "size"), lot=("lot", "median"), r0=("r0", "median"), q=("q", "median")).reset_index())
    bang = bang[bang["n"] >= 3]
    so_lieu = {"buoc_lot": bl, "so_lenh_them": int(len(them)), "bang": bang.round(3).to_dict("records")[:60],
               "lot_dau_khac_nhau": int(len(set(np.round(o["lot_dau"], 4)))), "bac_sau_nhat": int(bang["bac"].max()) if len(bang) else 0}
    dt_base = _do_tin(len(them), 100, 40)

    def ket_qua(dung: str, dt: str, ly: str, tham_so: dict, dich=KHONG, ghi_ro: tuple = ()) -> dict:
        k = {x: (dich, dt, ly) for x in ten}
        for x in ghi_ro:
            k[x] = (KHONG_RO, "thap", ly)
        k[dung] = (CO, dt, ly)
        return _kq(CO, dt, ly, so_lieu, tham_so, khoi=k, bang=bang)

    # ---- 1. phang
    ty_phang = float((np.abs(lot - lot0) < 1e-9).mean())
    so_lieu["ty_lot_phang"] = _f(ty_phang, 3)
    if ty_phang >= 0.97:
        ghi = "" if bl <= 0.011 and lot0.max() >= 0.1 else "; lot nho (%.2f) nen he so nhan < %.2f van ra cung lot (lam tron)" % (float(np.median(lot0)), 1.5)
        dt = dt_base if not ghi else _ha(dt_base)
        ly = "%.0f%% lenh them co lot bang lot lenh dau%s" % (100 * ty_phang, ghi)
        return ket_qua("lot_phang", dt, ly, {"lot_moi_lenh": _tham_so(_f(np.median(lot0), 4), "lot", "lot_phang", "lot cua moi lenh them")},
                       ghi_ro=("lot_cong", "lot_nhan", "lot_nhan_theo_bac", "lot_fibo", "lot_tong_gap_doi") if ghi else ())
    # ---- 2. tong gap doi: lot lenh moi = tong lot cung chieu dang mo (chuoi nhan doi tong)
    ok_c = np.isfinite(cung) & (cung > 0)
    ty_tong = float((np.abs(lot[ok_c] - cung[ok_c]) <= bl / 2 + 1e-9).mean()) if ok_c.any() else 0.0
    so_lieu["ty_lot_bang_tong_dang_mo"] = _f(ty_tong, 3)
    # ---- 3. cong
    d = lot - prev
    d_ok = np.isfinite(d)
    muc_d = np.round(d[d_ok] / bl) * bl
    mod = float(pd.Series(muc_d).mode().iat[0]) if d_ok.any() else float("nan")
    cong_ty = float((np.abs(d[d_ok] - mod) < bl / 2 + 1e-9).mean()) if d_ok.any() else 0.0
    cong_ok = cong_ty >= 0.95 and mod >= bl - 1e-9
    so_lieu.update(cong_buoc=_f(mod, 4), cong_ty=_f(cong_ty, 3))
    # ---- 4. nhan: ung vien (cot bac x moc x lam tron) + tich mot lan
    ung = _ung_vien_lot(them, bl)
    tich = _he_so_tich(them, bl)
    tot = [u for u in ung if not u["xau"]]
    # uu tien: it doan nhat -> gia thiet HEP truoc (chuoi chinh xac) -> khoang hep
    tot.sort(key=lambda u: (len(u["dn"]), u["rong"], u["rong_tong"], u["cot_bac"] != "bac", u["moc"] != "lenh_vua_mo", u["ham"] != "lam_tron"))
    mot_he_so = [u for u in tot if len(u["dn"]) == 1]
    nhan_1 = None
    if mot_he_so and not mot_he_so[0]["rong"]:
        u = mot_he_so[0]
        nhan_1 = {"a": u["a"], "b": u["b"], "ghi": "lot lenh sau = lot lenh truoc x he so (%s; moc %s)" % (_GIAI_THICH_HAM[u["ham"]], u["moc"]),
                  "kieu": "chuoi"}
    elif tich is not None and tich["cov"] >= 0.95:
        nhan_1 = {"a": tich["a"], "b": tich["b"], "kieu": "tich",
                  "ghi": "lot lenh thu k = lot dau x he so^(k-1), lam tron MOT lan (%s)" % ("gan nhat" if tich["ham"] == "lam_tron" else "xuong")}
    elif mot_he_so:
        u = mot_he_so[0]
        nhan_1 = {"a": u["a"], "b": u["b"], "kieu": "rong",
                  "ghi": "lot lenh sau ~ lot lenh truoc x he so (khong phan biet cach lam tron: %s)" % _GIAI_THICH_HAM[u["ham"]]}
    nhieu_doan = [u for u in tot if 2 <= len(u["dn"]) <= 5 and all(x["den"] > x["tu"] or x["n"] >= 5 for x in u["dn"])]
    best = (mot_he_so[0] if mot_he_so else (nhieu_doan[0] if nhieu_doan else (ung[0] if ung else None)))
    if best is not None:
        so_lieu.update(he_so_moc_tham_chieu=best["moc"], he_so_lam_tron=best["ham"], cot_bac_dung=best["cot_bac"],
                       he_so_nhan_khoang=[_f(best["a"], 3), _f(best["b"], 3)],
                       doan_he_so=[{k: (_f(v, 3) if isinstance(v, float) else v) for k, v in x.items()} for x in best["dn"]])
    if tich is not None:
        so_lieu["he_so_tich_khoang"] = [_f(tich["a"], 3), _f(tich["b"], 3)]
        so_lieu["he_so_tich_phu"] = _f(tich["cov"], 3)
    # ---- 5. fibonacci
    fibo_ok, fibo_lech = False, 0
    k_seq = them["bac_tang"].to_numpy(int)
    if (k_seq >= 6).sum() >= 12:
        for lech in (0, 1):
            ex = np.array([_fib(int(k), lech) for k in k_seq], float) * lot0
            ok_f = np.abs(lot - np.round(ex / bl) * bl) < bl * 0.5 + 1e-9
            if ok_f.mean() >= 0.95:
                fibo_ok, fibo_lech = True, lech
                break
    # ---- ket luan
    if ty_tong >= 0.95 and not (ty_phang >= 0.97):
        ly = "lot lenh moi = tong lot cung chieu dang mo (%.0f%% lenh them): tong lot nhan doi moi lenh" % (100 * ty_tong)
        return ket_qua("lot_tong_gap_doi", dt_base, ly, {"ty_le_tong": _tham_so(1.0, "he_so", "lot_tong_gap_doi", "lot lenh moi / tong lot dang mo")},
                       ghi_ro=("lot_nhan",) if nhan_1 else ())
    if fibo_ok:
        ghi = fibo_ok and nhan_1 is not None and nhan_1["a"] - 0.02 <= 1.618 <= nhan_1["b"] + 0.02
        ly = "lot theo day Fibonacci cua lot dau (%.0f%% lenh them khop, lech chi so %d)" % (100, fibo_lech)
        if ghi:
            ly += "; he so nhan ~1,6 cung khop: khong phan biet"
        return ket_qua("lot_fibo", _ha(dt_base) if ghi else dt_base, ly, {"lot_dau": _tham_so(_f(np.median(lot0), 4), "lot", "lot_fibo", "lot dau chuoi")},
                       ghi_ro=("lot_nhan",) if ghi else ())
    if cong_ok:
        ly = "lot cong deu %.2f moi lenh (%.0f%% lenh them khop)" % (mod, 100 * cong_ty)
        if nhan_1 is not None:
            ly += "; he so nhan %.2f..%.2f cung khop o do sau da thay: khong phan biet cong / nhan" % (nhan_1["a"], nhan_1["b"])
            return ket_qua("lot_cong", "thap", ly, {"cong_lot": _tham_so(_f(mod, 4), "lot", "lot_cong", "lot lenh sau - lot lenh truoc"),
                                                    "he_so_lot": _tham_so(_f((nhan_1["a"] + nhan_1["b"]) / 2, 3), "he_so", "lot_nhan",
                                                                          "khoang %.3f..%.3f" % (nhan_1["a"], nhan_1["b"]))},
                           ghi_ro=("lot_nhan",))
        return ket_qua("lot_cong", dt_base, ly, {"cong_lot": _tham_so(_f(mod, 4), "lot", "lot_cong", "lot lenh sau - lot lenh truoc")})
    if nhan_1 is not None and nhan_1["a"] > 1.0 + 1e-6:
        a, b = nhan_1["a"], nhan_1["b"]
        dt = dt_base if (b - a) <= 0.3 else _ha(dt_base)
        ly = "%s: he so %.2f..%.2f" % (nhan_1["ghi"], a, b)
        if nhan_1["kieu"] == "chuoi" and tich is not None and tich["cov"] >= 0.95:
            ly += "; kieu lam tron mot lan tu lot dau cung khop (%.2f..%.2f)" % (tich["a"], tich["b"])
        return ket_qua("lot_nhan", dt, ly, {"he_so_lot": _tham_so(_f((a + b) / 2, 3), "he_so", "lot_nhan", "khoang %.3f..%.3f (%s)" % (a, b, nhan_1["kieu"]))})
    if nhieu_doan:
        u = nhieu_doan[0]
        dn = u["dn"]
        ts, mo_ta = {}, []
        for i, x in enumerate(dn, 1):
            mo_ta.append("bac %d-%d: x%.2f..%.2f" % (x["tu"], x["den"], x["lo"], x["hi"]))
            ts["he_so_bac_%d" % i] = _tham_so(_f((x["lo"] + x["hi"]) / 2, 3), "he_so", "lot_nhan_theo_bac",
                                              "bac %d..%d, khoang %.3f..%.3f" % (x["tu"], x["den"], x["lo"], x["hi"]))
            if i >= 2:
                ts["moc_doi_he_so_%d" % (i - 1)] = _tham_so(x["tu"] - 1, "lenh", "lot_nhan_theo_bac",
                                                            "lenh thu %d la lenh dau cua bac he so moi (lech 1 la cach dem)" % x["tu"])
        dt = _ha(dt_base) if min(x["n"] for x in dn) < 10 or u["rong"] else dt_base
        ly = "he so lot doi %d lan theo bac (%s): %s" % (len(dn) - 1, _GIAI_THICH_HAM[u["ham"]], "; ".join(mo_ta))
        return ket_qua("lot_nhan_theo_bac", dt, ly, ts)
    cov = ung[0]["cov"] if ung else 0.0
    ly = ("lot khong khop mot quy luat chuan trong khoang du mau (he so nhan phu %.0f%% lenh, cong %.0f%%): xem bang theo bac"
          % (100 * cov, 100 * cong_ty))
    return _kq(KHONG_RO, "thap", ly, so_lieu, khoi={x: (KHONG_RO, "thap", ly) for x in ten}, bang=bang)


# ---- 3.6 lot_theo_von: lot dau cua chuoi tang theo so du
def _do_lot_theo_von(c: Ctx) -> dict:
    ro = c.ro
    ten = ("lot_tu_dong_theo_von",)
    if not np.isfinite(ro["bal_dau"]).any():
        ly = "khong biet so du (thieu von dau / lich su nap rut): khong do duoc"
        return _kq(KHONG_DO_DUOC, "thap", ly, khoi={ten[0]: (KHONG_DO_DUOC, "thap", ly)})
    r = ro[np.isfinite(ro["bal_dau"]) & (ro["bal_dau"] > 0)]
    if len(r) < TOI_THIEU_RO:
        ly = "chi %d chuoi co so du (< %d)" % (len(r), TOI_THIEU_RO)
        return _kq(KHONG_DO_DUOC, "thap", ly, khoi={ten[0]: (KHONG_DO_DUOC, "thap", ly)})
    lot = r["lot_dau"].to_numpy(float)
    bal = r["bal_dau"].to_numpy(float)
    kn = int(len(set(np.round(lot, 4))))
    bien = float(bal.max() / bal.min())
    from scipy.stats import spearmanr
    rho = float(spearmanr(bal, lot).statistic) if kn > 1 else float("nan")
    ty = lot / bal
    so_lieu = {"so_chuoi": int(len(r)), "lot_dau_khac_nhau": kn, "bien_do_so_du": _f(bien, 2), "spearman_lot_so_du": _f(rho, 3),
               "rcv_lot": _f(_rcv(lot), 3), "rcv_lot_tren_so_du": _f(_rcv(ty), 3)}
    if kn == 1:
        if bien >= 1.3:
            ly = "lot dau co dinh %.2f trong khi so du doi %.1f lan: khong tu dong theo von" % (lot[0], bien)
            return _kq(KHONG, _do_tin(len(r), 60, 25), ly, so_lieu, khoi={ten[0]: (KHONG, _do_tin(len(r), 60, 25), ly)})
        ly = "lot dau co dinh nhung so du chi doi %.2f lan: khong du de ket luan" % bien
        return _kq(KHONG_RO, "thap", ly, so_lieu, khoi={ten[0]: (KHONG_RO, "thap", ly)})
    if rho >= 0.6 and _rcv(ty) < _rcv(lot):
        cho = float(np.median(bal / (lot / 0.01)))
        ly = "lot dau tang theo so du (Spearman %.2f); khoang %.0f USD so du cho moi 0,01 lot" % (rho, cho)
        dt = _do_tin(len(r), 60, 25)
        return _kq(CO, dt, ly, so_lieu, {"so_du_moi_001_lot": _tham_so(_f(cho, 0), "USD", ten[0], "so du / (lot dau / 0,01)")},
                   khoi={ten[0]: (CO, dt, ly)})
    ly = "lot dau doi (%d gia tri) nhung khong bam theo so du (Spearman %.2f): co the theo ket qua chuoi truoc (xem lot_nhan_sau_sl)" % (kn, rho)
    return _kq(KHONG_RO, "thap", ly, so_lieu, khoi={ten[0]: (KHONG_RO, "thap", ly)})


# @@FIN@@
