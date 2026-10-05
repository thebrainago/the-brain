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
Bang chung that: ba tep deals tester cua CCBSN (`reports/fixture/tester_*_deals.csv.gz`, 04/10/2026) - lot, buoc, thoat, hedge do duoc
KHOP bo .set cua tac gia, va hai khai bao tre trong .set (InpMinuteDelayNewDay / AfterClose) bi du lieu bac bo. Xem
`reports/ho_so_bot_that_20261004.md`.

## Dung

    from nhan import ho_so_bot as HB
    hs = HB.ho_so("tep_bao_cao.htm", ma="GOLD.i#")   # chay MOI phep do -> JSON thuan (~50 KB / 3000 lenh, ~8 giay)
    print("\n".join(hs["bao_cao"]))                  # 3-8 dong loi thuong
    python -m nhan.ho_so_bot <tep> --ma GOLD.i# [--json ra.json] [--gon]

`ho_so()` tra ve `khoi` du 52 khoi cua danh muc (khoi khong do duoc tu lich su lenh van co mat, kem ly do), `tham_so` phang (de doi chieu voi
.set: `nhan/ho_so_set.py`), `van_tay` (dac trung tinh cach cho viec chuyen tai san), `tong_ket` (`phep_do_loi`, `khoi_thieu`, `khoi_la` phai
rong - `kiem_dang_ky()` kiem phan dang ky). Mot phep do bi loi KHONG bi nuot: thanh `khong_do_duoc` + canh bao + ghi vao `phep_do_loi`.
"""
from __future__ import annotations

import dataclasses
import json
import math
import re
import sys
import time
import traceback
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
    if isinstance(x, pd.DataFrame):
        return _json(x.to_dict("records"))
    if isinstance(x, pd.Series):
        return _json(x.to_dict())
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


def _so_tron_nhat(lo: float, hi: float, toi_da_le: int = 3) -> float:
    """So 'tron' nhat nam trong khoang [lo, hi]: it chu so le nhat, hoa thi gan tam nhat.

    Khoang he so tu lot da lam tron chi cho biet cac gia tri TUONG THICH, khong phai gia tri do duoc. Trung diem
    se doc sai: VAMGE o bac 2-10 cho khoang 0.926..1.046 (chua 1.0 = lot phang), trung diem 0.986 nghe nhu
    'giam dan' - sai. Dung lam tham so de thay so vao thi phai la so don gian nhat con tuong thich."""
    if hi < lo:
        lo, hi = hi, lo
    tam = (lo + hi) / 2.0
    for le in range(0, toi_da_le + 1):
        b = 10.0 ** -le
        k0, k1 = math.ceil(lo / b - 1e-9), math.floor(hi / b + 1e-9)
        if k0 <= k1:
            k = min(range(k0, k1 + 1), key=lambda i: abs(i * b - tam)) if k1 - k0 < 2000 else round(tam / b)
            return round(k * b, le)
    return round(tam, toi_da_le)


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
    cache: dict = dataclasses.field(default_factory=dict)   # phan tich dung chung giua cac phep do (khong qua Ctx.loc)

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


def _duoi_nhi_thuc(k: int, n: int, p: float) -> float:
    """P(X >= k), X ~ Nhi thuc(n, p), tinh truc tiep bang math.comb (n nho)."""
    p = min(max(float(p), 1e-9), 1.0 - 1e-9)
    return float(sum(math.comb(n, i) * p ** i * (1.0 - p) ** (n - i) for i in range(int(k), int(n) + 1)))


def _lop_nhan(cm) -> pd.Series:
    """Nhan comment da chuan hoa: chu thuong, moi day chu so (ke ca thap phan) -> '#'."""
    return pd.Series(cm).astype(str).str.strip().str.lower().str.replace(r"\d+(?:[.,]\d+)?", "#", regex=True)


def _nhan_hedge(c: Ctx) -> dict:
    """Bang chung bang NHAN COMMENT (khong can biet ten nhan truoc): mot lop nhan THIEU SO (so -> '#', toi da 20% lenh, >= 3 lenh) ma cac
    lenh cua no (a) >= 90% mo khi chuoi NGUOC chieu dang mo, NHIEU HON han lop chu dao (duoi nhi thuc <= 1e-3, co so >= 2%), va
    (b) luc do chuoi chu da DAI (trung vi host_k >= 3; neu lop chu dao cung hay mo luc do thi >= 2 lan trung vi cua no) la lenh hedge /
    doi ung. Do them: host_k nho nhat (so lenh chu luc hedge dau tien mo, lech 1 so voi khai bao), co mo CUNG GIAY voi lenh chu
    moi nhat khong, lot co BANG lot lenh chu moi nhat khong (guong lot DCA).
    Tra {co_nhan, lop_chu, lop: [...], mask (theo lenh), tong}."""
    if "hedge" in c.cache:
        return c.cache["hedge"]
    o = c.lenh
    n = len(o)
    res = {"co_nhan": False, "lop_chu": None, "lop": [], "mask": np.zeros(n, bool), "tong": None}
    c.cache["hedge"] = res
    if n < TOI_THIEU_LENH or "cm_vao" not in o.columns:
        return res
    lop = _lop_nhan(o["cm_vao"]).to_numpy(object)
    ten, dem = np.unique(lop, return_counts=True)
    o_dem = np.argsort(-dem, kind="stable")
    ten, dem = ten[o_dem], dem[o_dem]
    if len(ten) < 2 or ten[0] == "" or dem[0] < 0.6 * n:
        return res
    res["co_nhan"] = True
    res["lop_chu"] = str(ten[0])
    chu = lop == ten[0]
    hk = o["host_k"].to_numpy(int)
    co_host = chu & (hk >= 1)
    med_chu = float(np.median(hk[co_host])) if co_host.any() else 0.0
    base = float((hk[chu] >= 1).mean())
    t = o["mo_s"].to_numpy(float)
    ch = o["chieu"].to_numpy(int)
    lot = o["lot_vao"].to_numpy(float)
    tien = o["tien"].to_numpy(float)
    L = _cua_so(c)
    moi = {d: (t[chu & (ch == d)], lot[chu & (ch == d)]) for d in (1, -1)}
    gop_cg, gop_lot, gop_idx = [], [], []
    for k, m in zip(ten[1:], dem[1:]):
        if k == "" or m < 3 or m > 0.2 * n:
            continue
        idx = lop == k
        hki = hk[idx]
        ty_ng = float((hki >= 1).mean())
        cg, kl = [], []
        for i in np.where(idx)[0]:
            tt, ll = moi[-ch[i]]
            j = int(np.searchsorted(tt, t[i], side="right")) - 1
            if j < 0:
                continue
            cg.append(bool(t[i] - tt[j] <= L))
            kl.append(bool(abs(lot[i] - ll[j]) <= 0.011))
        td = tien[idx]
        td = td[np.isfinite(td)]
        # hedge neu: (a) gan nhu luon mo khi chuoi nguoc dang mo, NHIEU HON han lop chu dao (kiem dinh nhi thuc, khong phu thuoc co mau),
        # (b) luc do chuoi chu da dai (trung vi >= 3; neu lop chu dao cung hay mo luc chuoi nguoc dang mo thi phai >= 2 lan trung vi cua no)
        p_nhi = _duoi_nhi_thuc(int((hki >= 1).sum()), int(m), max(base, 0.02))
        la = bool(ty_ng >= 0.9 and p_nhi <= 1e-3 and float(np.median(hki)) >= max(3.0, 2.0 * med_chu if base > 0.3 else 0.0))
        r = {"lop": str(k), "n": int(m), "ty": _f(m / n, 4), "ty_nguoc_chuoi": _f(ty_ng, 3), "ty_nguoc_lop_chu": _f(base, 3),
             "host_k_min": int(hki.min()), "host_k_p50": _f(np.median(hki), 1), "host_k_max": int(hki.max()),
             "ty_cung_giay_lenh_chu": _f(float(np.mean(cg)), 3) if cg else None,
             "ty_lot_bang_lenh_chu_moi": _f(float(np.mean(kl)), 3) if kl else None,
             "ty_lai": _f(float((td > 0).mean()), 3) if len(td) else None,
             "tien_trung_vi": _f(float(np.median(td)), 2) if len(td) else None, "p_nhi_thuc": "%.1e" % p_nhi, "la_hedge": la}
        res["lop"].append(r)
        if la:
            res["mask"] |= idx
            gop_cg += cg
            gop_lot += kl
            gop_idx.append(np.where(idx)[0])
    if res["mask"].any():
        hh = hk[res["mask"]]
        res["tong"] = {"n": int(res["mask"].sum()), "ty": _f(res["mask"].mean(), 4), "host_k_min": int(hh.min()),
                       "host_k_p50": _f(np.median(hh), 1), "host_k_max": int(hh.max()),
                       "ty_cung_giay_lenh_chu": _f(float(np.mean(gop_cg)), 3) if gop_cg else None,
                       "ty_lot_bang_lenh_chu_moi": _f(float(np.mean(gop_lot)), 3) if gop_lot else None,
                       "lop": [r["lop"] for r in res["lop"] if r["la_hedge"]]}
    return res


def bo_hedge(c: Ctx) -> Ctx:
    """Ctx khong con lenh hedge nhan ra bang nhan comment (neu co): lot dau / buoc / chuoi cua phan chu khong con bi lenh doi ung lam nhieu.
    Giu nguyen `c` neu khong co. Ctx moi mang `cache['da_bo_hedge']` = so lenh da bo."""
    nh = _nhan_hedge(c)
    if not nh["mask"].any():
        return c
    c2 = c.loc(~nh["mask"])
    c2.cache["da_bo_hedge"] = int(nh["mask"].sum())
    c2.cache["hedge_goc"] = {k: nh[k] for k in ("lop_chu", "lop", "tong")}
    return c2


def _do_doi_ung_nhan(c: Ctx, nh: dict) -> tuple:
    """Doi ung / hedge nhan ra bang NHAN COMMENT (xem `_nhan_hedge`). Tra (ket qua, mat na lenh hedge)."""
    o = c.lenh
    n = len(o)
    ten = ("lenh_doi_ung_sau_n_lenh", "lenh_doi_ung_stop")
    tg = nh["tong"]
    mask = nh["mask"]
    nd = tg["n"]
    co_stop = _do_stop_doi_ung(c)
    dt = _do_tin(nd, 30, 8)
    guong = (tg["ty_lot_bang_lenh_chu_moi"] or 0) >= 0.8
    cung = (tg["ty_cung_giay_lenh_chu"] or 0) >= 0.8
    ly = ("lenh mang nhan rieng (%s): %d lenh (%.1f%%), moi lenh mo khi chuoi nguoc chieu dang mo (lop chu dao chi %.0f%%) va chuoi do da co >= %d lenh "
          "(trung vi %.0f)%s%s"
          % (", ".join(tg["lop"]), nd, 100 * nd / n, 100 * (nh["lop"][0]["ty_nguoc_lop_chu"] or 0), tg["host_k_min"], tg["host_k_p50"],
             "; %.0f%% mo cung giay voi lenh chu moi nhat" % (100 * tg["ty_cung_giay_lenh_chu"]) if cung else "",
             "; lot bang lot lenh chu moi nhat o %.0f%% (guong lot DCA)" % (100 * tg["ty_lot_bang_lenh_chu_moi"]) if guong else ""))
    ts = {"so_lenh_kich_hoat": _tham_so(tg["host_k_min"], "lenh", "lenh_doi_ung_sau_n_lenh",
                                        "chuoi chu da co so lenh nay khi hedge dau tien mo (lech 1 la cach dem; xem khop_knob)")}
    if guong:
        ts["ty_lot_so_voi_lenh_chu_moi"] = _tham_so(1.0, "ty_le", "lenh_doi_ung_sau_n_lenh",
                                                    "lot hedge = lot lenh chu moi nhat (khop %.0f%% lenh)" % (100 * tg["ty_lot_bang_lenh_chu_moi"]))
    so_lieu = {"cach_nhan_ra": "nhan_comment", "nhan_hedge": nh["lop"], "so_lenh_doi_ung": nd, "ty_le_lenh": _f(nd / n, 4),
               "bac_kich_hoat": tg["host_k_min"], "kieu_lot": "guong_lenh_chu_moi_nhat" if guong else "khong_ro"}
    return (_kq(CO, dt, ly, so_lieu, ts, khoi={ten[0]: (CO, dt, ly), ten[1]: co_stop}), mask)


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
    nh = _nhan_hedge(c)
    if nh["mask"].any():
        return _do_doi_ung_nhan(c, nh)
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
               "gap_s_p80": _f(p80, 1), "gap_pip_trung_vi": _f(np.median(gap_pip), 2), "gap_pip_rcv": _f(_rcv(gap_pip), 3),
               # khoang nho nhat dong chuoi cu -> mo chuoi moi cung chieu: thu bang chung cho tham so 'tre sau khi dong' (MinuteDelayAfterClose)
               "gap_s_min": _f(float(gap_s.min()), 1), "gap_s_p05": _f(_q(gap_s, 5), 1), "n_gap_duoi_60s": int((gap_s < 60.0).sum())}
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
        so_lieu["doan_buoc"] = [{"tu": int(dn[0]["tu"]), "den": int(dn[0]["den"]), "pip": _f(v, 2)}]
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
    so_lieu["doan_buoc"] = [{"tu": int(d["tu"]), "den": int(d["den"]), "pip": ts["buoc_bac_%d" % i]["gia_tri"]}
                            for i, d in enumerate(dn, 1)]
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


def _doan_he_so(bac, lo, hi, phu: float = 0.95, tach_duoi: bool = False) -> list[dict]:
    """Chia cac bac thanh it doan nhat sao cho trong moi doan co MOT he so phu >= `phu` cac khoang (tham lam, dai nhat truoc).
    `tach_duoi`: sau do tach duoi bac sau bi nuot vi it mau (xem `_tach_duoi`)."""
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
    return _tach_duoi(bac, lo, hi, doan) if tach_duoi else doan


def _tach_duoi(bac, lo, hi, doan: list[dict], toi_thieu_bac: int = 3) -> list[dict]:
    """Doan cuoi bi 'nuot' vi qua it mau (< 5% tong so: chi vai chuoi di toi do sau): tim DUOI gom >= `toi_thieu_bac` muc bac LIEN
    TIEP ma MOI mau deu nam ngoai he so chung cua doan nhung chung co MOT he so chung phu 100% -> tach thanh doan rieng (n nho nen
    do tin thap). Mot lenh le loi khong tach (can >= 3 muc bac lien tiep thong nhat), nen nhieu le khong sinh ra bac gia."""
    if not doan:
        return doan
    x = doan[-1]
    sel = (bac >= x["tu"]) & (bac <= x["den"])
    if not np.isfinite(x["lo"]) or not np.isfinite(x["hi"]):
        return doan
    diem = (x["lo"] + x["hi"]) / 2.0 if np.isfinite(x["hi"]) else x["lo"]
    trong = (lo <= diem + 1e-9) & (hi >= diem - 1e-9)
    muc = sorted(set(bac[sel].tolist()))
    duoi = []
    for b in reversed(muc):
        s = sel & (bac == b)
        if bool((~trong[s]).all()):
            duoi.append(b)
        else:
            break
    if len(duoi) < toi_thieu_bac:
        return doan
    tu = min(duoi)
    t = sel & (bac >= tu)
    a, b2, cov = _phu_khoang(lo[t], hi[t])
    gia = sel & (bac < tu)
    if cov < 0.999 or not np.isfinite(a) or not gia.any():
        return doan
    a0, b0, cov0 = _phu_khoang(lo[gia], hi[gia])
    moi = dict(x, den=int(max(muc[:muc.index(tu)])), lo=a0, hi=b0, phu=cov0, n=int(gia.sum()))
    duoi_doan = {"tu": int(tu), "den": int(x["den"]), "lo": a, "hi": b2, "phu": cov, "n": int(t.sum())}
    return doan[:-1] + [moi, duoi_doan]


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
    lot0 = them["lot_dau"].to_numpy(float)
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
                            "dn": dn, "xau": any(x["phu"] < 0.95 for x in dn), "bac": bc[ok], "ok": ok, "mu": False,
                            "rong_tong": float(sum(x["hi"] - x["lo"] for x in dn if np.isfinite(x["hi"] - x["lo"])))})
        # LUY THUA TU DAU: lot_k = tron(lot_dau x m_bac^(k-1)), m_bac doi theo bac nhung MU luon dem tu lenh dau chuoi (CCBSN bat
        # `InpUseChangeMultiplier`: lenh 11 nhay x1,2^10 = x6,19; sang tang he so 1,1 o lenh 21 lot TUT 0,32 -> 0,07). Mo hinh 'ti le voi
        # lenh truoc' khong giai thich duoc cai nhay nay (phai gop thanh 'x3..7') nen khong the dung lai dung hanh vi.
        e = np.maximum(bc - 1.0, 1.0)
        for ham in ("lam_tron", "cat_xuong"):
            if ham == "lam_tron":
                ca, cb = (lot - bl / 2 - 1e-9) / lot0, (lot + bl / 2 + 1e-9) / lot0
            else:
                ca, cb = (lot - 1e-9) / lot0, (lot + bl + 1e-9) / lot0
            with np.errstate(all="ignore"):
                lo = np.power(np.maximum(ca, 1e-9), 1.0 / e)
                hi = np.power(np.maximum(cb, 1.0e-9), 1.0 / e)
            ok = (bc >= 2) & np.isfinite(lo) & np.isfinite(hi) & (hi > lo) & (lo > 0) & np.isfinite(lot0) & (lot0 > 0)
            if int(ok.sum()) < 20:
                continue
            a1, b1, cov1 = _phu_khoang(lo[ok], hi[ok])
            dn = _doan_he_so(bc[ok], lo[ok], hi[ok], tach_duoi=True)
            ung.append({"cot_bac": cn, "moc": "lot_dau_luy_thua", "ham": ham, "rong": False, "a": a1, "b": b1, "cov": cov1,
                        "dn": dn, "xau": any(x["phu"] < 0.95 for x in dn), "bac": bc[ok], "ok": ok, "mu": True,
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
    mot_he_so = [u for u in tot if len(u["dn"]) == 1 and not u["mu"]]
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
                                                    "he_so_lot": _tham_so(_f(_so_tron_nhat(nhan_1["a"], nhan_1["b"]), 3), "he_so", "lot_nhan",
                                                                          "khoang tuong thich %.3f..%.3f (chon so tron nhat)" % (nhan_1["a"], nhan_1["b"]))},
                           ghi_ro=("lot_nhan",))
        return ket_qua("lot_cong", dt_base, ly, {"cong_lot": _tham_so(_f(mod, 4), "lot", "lot_cong", "lot lenh sau - lot lenh truoc")})
    if nhan_1 is not None and nhan_1["a"] > 1.0 + 1e-6:
        a, b = nhan_1["a"], nhan_1["b"]
        dt = dt_base if (b - a) <= 0.3 else _ha(dt_base)
        ly = "%s: he so %.2f..%.2f" % (nhan_1["ghi"], a, b)
        if nhan_1["kieu"] == "chuoi" and tich is not None and tich["cov"] >= 0.95:
            ly += "; kieu lam tron mot lan tu lot dau cung khop (%.2f..%.2f)" % (tich["a"], tich["b"])
        return ket_qua("lot_nhan", dt, ly, {"he_so_lot": _tham_so(_f(_so_tron_nhat(a, b), 3), "he_so", "lot_nhan",
                                                           "khoang tuong thich %.3f..%.3f (%s; chon so tron nhat)" % (a, b, nhan_1["kieu"]))})
    if nhieu_doan:
        u = nhieu_doan[0]
        dn = u["dn"]
        ts, mo_ta = {}, []
        for i, x in enumerate(dn, 1):
            mo_ta.append("bac %d-%d: x%s (khoang tuong thich %.2f..%.2f)"
                         % (x["tu"], x["den"], ("%.3f" % _so_tron_nhat(x["lo"], x["hi"])).rstrip("0").rstrip("."), x["lo"], x["hi"]))
            ts["he_so_bac_%d" % i] = _tham_so(_f(_so_tron_nhat(x["lo"], x["hi"]), 3), "he_so", "lot_nhan_theo_bac",
                                              "bac %d..%d, khoang tuong thich %.3f..%.3f (chon so tron nhat)"
                                              % (x["tu"], x["den"], x["lo"], x["hi"]))
            if i >= 2:
                ts["moc_doi_he_so_%d" % (i - 1)] = _tham_so(x["tu"] - 1, "lenh", "lot_nhan_theo_bac",
                                                            "lenh thu %d la lenh dau cua bac he so moi (lech 1 la cach dem)" % x["tu"])
        dt = _ha(dt_base) if min(x["n"] for x in dn) < 10 or u["rong"] else dt_base
        if u["mu"]:
            so_lieu["kieu_he_so"] = "luy_thua_tu_dau"
            for k, v in ts.items():
                if k.startswith("he_so_bac_"):
                    v["ghi_chu"] += "; lot lenh thu k = lot dau x he so^(k-1) (mu dem tu lenh dau chuoi)"
            ly = ("lot lenh thu k = lot dau x he so_bac^(k-1), MU dem tu lenh dau chuoi, he so doi %d lan theo bac (%s): %s"
                  % (len(dn) - 1, _GIAI_THICH_HAM[u["ham"]], "; ".join(mo_ta)))
        else:
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


# ============================================================== 4. THOAT / QUAN LY VI THE (do tren CHUOI DA DONG)
def _khoi_cua(kiem: str) -> tuple:
    """Ten cac KHOI ma phep do `kiem` chiu trach nhiem (theo `khoi_co_che.KHOI_DS`)."""
    return tuple(k.ma for k in KC.KHOI_DS if k.kiem == kiem)


def _tat_ca(kiem: str, kl: str, dt: str, ly: str) -> dict:
    return {m: (kl, dt, ly) for m in _khoi_cua(kiem)}


def _top(khoi: dict) -> tuple[str, str]:
    """Ket luan chung cua mot phep do nhieu khoi: co > khong_ro > khong > khong_do_duoc; do tin = tot nhat trong cac khoi cung ket luan."""
    for kl in (CO, KHONG_RO, KHONG, KHONG_DO_DUOC):
        dts = [v[1] for v in khoi.values() if v[0] == kl]
        if dts:
            return kl, min(dts, key=DO_TIN.index)
    return KHONG_DO_DUOC, "thap"


def _khong_do_duoc(kiem: str, ly: str, so_lieu: dict | None = None) -> dict:
    return _kq(KHONG_DO_DUOC, "thap", ly, so_lieu, khoi=_tat_ca(kiem, KHONG_DO_DUOC, "thap", ly))


def _res_gia(o: pd.DataFrame, pip: float) -> float:
    """Do phan giai gia, don vi pip: so thap phan nho nhat ma moi gia mo / gia dong deu la boi so cua no (vang 0,01 / pip 0,1 = 0,1 pip)."""
    p = np.concatenate([o["gia_mo"].to_numpy(float), o["gia_dong"].to_numpy(float)])
    p = p[np.isfinite(p)]
    if not len(p):
        return 0.1
    p = p[:: max(1, len(p) // 4000)]
    for d in range(0, 9):
        if np.allclose(p, np.round(p, d), atol=1e-9, rtol=0.0):
            return max((10.0 ** -d) / pip, 1e-6)
    return 0.1


def _bien_duoi(x, res: float, ty_dinh: float = 0.08, dau_chat: float = 0.15, rong_min: float = 3.0,
               ty_rong: float = 0.15) -> list[dict]:
    """Cac BIEN DUOI SAC cua mau x: gia tri L ma phia tren co mot dam dong (>= `ty_dinh` mau nam trong [L, L+W]) con ngay duoi L
    gan nhu trong (mau trong [L-W, L) <= `dau_chat` x dam), W = max(rong_min, ty_rong |L|, 3 res). Dam hai phia xuoi nhu cum
    quanh 0 (doi xung) khong qua duoc vi day dong nhu dinh. Tu thap len cao, moi dam chi tinh mot lan. Moi bien:
    {L, w, n_dinh, ty_dinh, n_day, ty_nhon} - `ty_nhon` = ty le mau trong +-1,5 res quanh L so voi dam (1 = TP chinh xac ngay tai gia)."""
    x = np.sort(np.asarray(x, float))
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 15:
        return []
    res = max(float(res), 1e-9)
    ung = np.unique(np.round(x / res) * res)
    out: list[dict] = []
    qua = -np.inf
    for L in ung:
        if L <= qua:
            continue
        w = max(rong_min, ty_rong * abs(L), 3.0 * res)
        i0 = int(np.searchsorted(x, L - res / 2.0, side="left"))
        i1 = int(np.searchsorted(x, L + w, side="right"))
        j0 = int(np.searchsorted(x, L - w, side="left"))
        dinh, day = i1 - i0, i0 - j0
        if dinh >= max(5.0, ty_dinh * n) and day <= dau_chat * dinh:
            nhon = int(np.searchsorted(x, L + 1.5 * res, side="right")) - i0
            out.append({"L": float(L), "w": float(w), "n_dinh": int(dinh), "ty_dinh": dinh / n, "n_day": int(day),
                        "ty_nhon": nhon / dinh})
            qua = L + w
    return out


def _bac_thang(x, L: float, res: float, toi_thieu: int = 30) -> dict | None:
    """Cac gia tri tren san L co nam tren LUOI L + k*s khong (trailing co buoc co dinh)? Tra s LON NHAT khop >= 90% (boi so cua s that
    cung khop it hon) kem ty le khop va ty le khop NGAU NHIEN (2 dung sai / s). Neu qua nua mau nam sat san thi khong xet."""
    y = np.asarray(x, float)
    y = y[np.isfinite(y) & (y >= L - res)] - L
    if len(y) < toi_thieu:
        return None
    tol = 1.5 * res
    if float((y > 2.0 * tol).mean()) < 0.5:
        return None
    for s in (25.0, 20.0, 15.0, 10.0, 8.0, 6.0, 5.0, 4.0, 3.0, 2.5, 2.0, 1.5, 1.0, 0.5):
        if s < 6.0 * res:
            continue
        r = np.abs(y / s - np.round(y / s)) * s
        khop = float((r <= tol).mean())
        ngau = min(1.0, 2.0 * tol / s)
        if khop >= 0.9 and ngau <= 0.4:
            return {"buoc": s, "ty_khop": khop, "ty_ngau_nhien": ngau, "n": int(len(y))}
    return None


_NHOM_SAU = (("1", 1, 1), ("2-4", 2, 4), ("5-9", 5, 9), ("10+", 10, 10 ** 6))


def _lan_rong(v) -> float:
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if len(v) < 2 or abs(float(np.mean(v))) < 1e-12:
        return float("inf")
    return float((v.max() - v.min()) / abs(np.mean(v)))


def _phan_tich_thoat(c: Ctx) -> dict:
    """Phan tich CHUNG phia thoat (cac phep do thoat / hoa von / doi_tp / tia dung chung, tinh MOT lan, giu trong `c.cache`).
    Don vi pip. `x` = khoang cach tu gia vao trung binh cua cum dong cuoi toi gia dong (+ = lai)."""
    if "thoat" in c.cache:
        return c.cache["thoat"]
    ro = c.ro
    d = ro[ro["da_dong"] & np.isfinite(ro["tp_pip"])].copy()
    res = _res_gia(c.lenh, c.pip)
    A: dict = {"n_dong": int(len(d)), "res_pip": res, "du": bool(len(d) >= TOI_THIEU_RO), "nhom": {}, "bien_am": [],
               "muc_tieu": {"loai": "khong_du"}}
    c.cache["thoat"] = A
    if not A["du"]:
        return A
    co_ly = bool(c.chat_luong.get("co_ly_do_ra"))
    A["co_ly_do_ra"] = co_ly
    ly = {k: int(d[col].sum()) for k, col in (("tp", "ly_tp"), ("sl", "ly_sl"), ("stopout", "ly_so"), ("ea", "ly_ea"))}
    A["ly_ra_cum_cuoi"] = ly
    nhieu = d[d["so_lenh"] >= 2]
    A["n_nhieu_lenh"] = int(len(nhieu))
    A["ty_cung_luc_nhieu_lenh"] = (_f(float(((nhieu["so_dot"] == 1) & (nhieu["n_cuoi"] == nhieu["so_lenh"])).mean()), 3)
                                   if len(nhieu) else None)
    for ten, lo, hi in _NHOM_SAU:
        g = d[(d["so_lenh"] >= lo) & (d["so_lenh"] <= hi)]
        rec: dict = {"n": int(len(g)), "bien": [], "tp": None}
        A["nhom"][ten] = rec
        if len(g) < 15:
            continue
        x = g["tp_pip"].to_numpy(float)
        rec.update(p10=_f(_q(x, 10), 2), p50=_f(_q(x, 50), 2), p90=_f(_q(x, 90), 2))
        bien = _bien_duoi(x, res)
        rec["bien"] = [{k: (_f(v, 3) if isinstance(v, float) else v) for k, v in b.items()} for b in bien[:4]]
        duong = [b for b in bien if b["L"] > 0]
        if not duong:
            continue
        b = duong[0]
        L = b["L"]
        if co_ly:
            dung = (g["ly_sl"] >= 1) & (g["ly_tp"] == 0) & (g["ly_ea"] == 0)
            xs = g.loc[dung, "tp_pip"].to_numpy(float)
        else:
            xs = x
        rec["tp"] = {"L": _f(L, 3), "ty_nhon": _f(b["ty_nhon"], 3), "ty_dinh": _f(b["ty_dinh"], 3),
                     "ty_gan": _f(float(((x >= L - res) & (x <= L + max(10.0, L))).mean()), 3),
                     "ty_duoi": _f(float((x < L - b["w"]).mean()), 3),
                     "bac_thang": _bac_thang(xs, L, res) if len(xs) >= 30 else None,
                     "n_bac_thang": int(len(xs))}
    # ---- muc tieu: co dinh theo PIP hay theo TIEN? so tung nhom lot cua chuoi nhieu lenh (neu khong du nhom: moi chuoi)
    duong_ref = [r["tp"]["L"] for r in A["nhom"].values() if r["tp"] and r["tp"]["L"]]
    if duong_ref:
        ref = min(duong_ref)
        for chon, ten in ((d[d["so_lenh"] >= 2], "chuoi_nhieu_lenh"), (d, "moi_chuoi")):
            nhom = []
            for lot, g in chon.groupby(chon["lot_cuoi"].round(4)):
                g = g[g["tp_pip"] > 0.5 * ref]
                if len(g) >= 12:
                    nhom.append({"lot": float(lot), "n": int(len(g)), "p05_pip": float(_q(g["tp_pip"], 5)),
                                 "p05_tien": float(_q(g["tien_cuoi"], 5))})
            if len(nhom) >= 3:
                sp, st = _lan_rong([r["p05_pip"] for r in nhom]), _lan_rong([r["p05_tien"] for r in nhom])
                loai = "pip" if (sp <= 0.25 and st >= 0.6) else "tien" if (st <= 0.25 and sp >= 0.6) else "khong_ro"
                A["muc_tieu"] = {"loai": loai, "lan_rong_pip": _f(sp, 3), "lan_rong_tien": _f(st, 3), "tren": ten,
                                 "nhom_lot": [{k: _f(v, 3) for k, v in r.items()} for r in nhom[:8]]}
                break
    # ---- cum lo: lo tien cua chuoi - co dam o mot gia tri khong?
    am = d[np.isfinite(d["tien"]) & (d["tien"] < 0)]
    A["n_chuoi_am"] = int(len(am))
    if len(am) >= 15:
        b = _bien_duoi(-am["tien"].to_numpy(float), 0.01, ty_dinh=0.25, rong_min=0.05, ty_rong=0.05)
        A["bien_am"] = [{k: (_f(v, 3) if isinstance(v, float) else v) for k, v in x.items()} for x in b[:3]]
    # ---- lat cat theo do sau: ty le chuoi dong GAN GIA TRUNG BINH (|x| nho) / chuoi dong duoi bien TP
    A["gan_hoa_von"] = {}
    for ten, lo, hi in _NHOM_SAU:
        g = d[(d["so_lenh"] >= lo) & (d["so_lenh"] <= hi)]
        if len(g) < 15:
            continue
        L = (A["nhom"][ten]["tp"] or {}).get("L")
        ngu = max(3.0, 0.25 * L) if L else 5.0
        z = g[np.abs(g["tp_pip"]) <= ngu]
        A["gan_hoa_von"][ten] = {"n": int(len(g)), "ngu_pip": _f(ngu, 2), "ty": _f(len(z) / len(g), 3), "n_gan": int(len(z)),
                                 "ty_ban": _f(float((z["chieu"] < 0).mean()), 3) if len(z) >= 5 else None}
    A["ty_ban_chung"] = _f(float((d["chieu"] < 0).mean()), 3)
    # ---- cum thoat DUOI bien TP o chuoi nhieu lenh: co CANH TREN sac (khoa loi / hoa von do EA dong bang lenh thi truong)?
    A["cum_duoi"] = None
    d2 = d[d["so_lenh"] >= 2]
    Ls = [r["tp"]["L"] for t, r in A["nhom"].items() if t != "1" and r.get("tp") and r["tp"]["L"]]
    if len(d2) >= 30 and Ls:
        L2 = min(Ls)
        w2 = max(3.0, 0.15 * L2)
        cl = d2[d2["tp_pip"] < L2 - w2]
        if len(cl) >= 15 and len(cl) >= 0.05 * len(d2):
            x = cl["tp_pip"].to_numpy(float)
            b = _bien_duoi(-x, res, ty_dinh=0.3, rong_min=3.0)
            giu = (cl["dong"] - cl["mo"]).dt.total_seconds().to_numpy(float) / 3600.0
            tpq = d2[d2["tp_pip"] >= L2 - res]
            giu_tp = (tpq["dong"] - tpq["mo"]).dt.total_seconds().to_numpy(float) / 3600.0
            cd = {"n": int(len(cl)), "ty_nhom": _f(len(cl) / len(d2), 3), "tp_pip_nhom": _f(L2, 2), "U_pip": None,
                  "p05": _f(_q(x, 5), 2), "p50": _f(_q(x, 50), 2), "p95": _f(_q(x, 95), 2),
                  "ty_ban": _f(float((cl["chieu"] < 0).mean()), 3), "ty_ban_nhom": _f(float((d2["chieu"] < 0).mean()), 3),
                  "ty_ban_quan_the_tp": _f(float((tpq["chieu"] < 0).mean()), 3) if len(tpq) else None,
                  "gio_giu_p50": _f(_q(giu, 50), 2), "gio_giu_p50_tp": _f(_q(giu_tp, 50), 2) if len(giu_tp) else None,
                  "so_lenh_p50": _f(_q(cl["so_lenh"], 50), 1)}
            if b:
                U = -b[0]["L"]
                cd["U_pip"] = _f(U, 2)
                cd["ty_dinh_U"] = _f(b[0]["ty_dinh"], 3)
                cd["tren_canh_U"] = int((x > U + res).sum())          # chuoi nam TREN canh trong cum (canh sac: ~ 0)
            A["cum_duoi"] = cd
    return A


def _dt_thoat(c: Ctx, n: int, tot: int = 100, vua: int = 40) -> str:
    """Do tin cua phep do thoat: theo so chuoi, ha mot bac neu it lenh ghep vao-ra dang tin (xem `chat_luong`)."""
    dt = _do_tin(n, tot, vua)
    ty = c.chat_luong.get("dang_tin_ghep")
    if ty is not None and ty < 0.9:
        dt = _ha(dt)
    return dt


def _tp_cua(A: dict) -> list[tuple]:
    """[(nhom, L, rec)] cac nhom do sau co bien TP duong, tu nong den sau."""
    return [(ten, r["tp"]["L"], r) for ten, r in A["nhom"].items() if r.get("tp")]


def _do_thoat(c: Ctx) -> dict:
    """THOAT cua chuoi: TP tu gia trung binh (hang so pip), TP theo tien, All Sniper, cat lo theo tien, thoat theo chi bao."""
    A = _phan_tich_thoat(c)
    if not A["du"]:
        return _khong_do_duoc("thoat", "chi %d chuoi da dong (< %d)" % (A["n_dong"], TOI_THIEU_RO))
    n = A["n_dong"]
    dt = _dt_thoat(c, n)
    tpl = _tp_cua(A)
    mt = A["muc_tieu"]
    so_lieu = {"so_chuoi_dong": n, "ty_cung_luc_nhieu_lenh": A["ty_cung_luc_nhieu_lenh"], "ly_ra_cum_cuoi": A["ly_ra_cum_cuoi"],
               "nhom_do_sau": A["nhom"], "muc_tieu": mt, "gan_hoa_von": A["gan_hoa_von"], "chuoi_am": A["n_chuoi_am"]}
    khoi: dict = {}
    ts: dict = {}
    cl = A["ty_cung_luc_nhieu_lenh"]
    chung = cl is None or cl >= 0.9              # chuoi nhieu lenh dong CUNG LUC (khong tia)
    bac_thang = next((r["tp"]["bac_thang"] for _, _, r in tpl if r["tp"]["bac_thang"]), None)
    # ---- tp_chuoi_tu_gia_tb
    if not tpl:
        ly = ("khong thay bien duoi sac cua khoang cach thoat (trung vi theo nhom: %s): khong co TP co dinh tu gia trung binh"
              % ", ".join("%s lenh %s pip" % (t, r.get("p50")) for t, r in A["nhom"].items() if r.get("p50") is not None))
        khoi["tp_chuoi_tu_gia_tb"] = (KHONG, _ha(dt) if n < 60 else dt, ly)
    elif not chung:
        ly = "chuoi nhieu lenh KHONG dong cung luc (%.0f%%): khong phai TP ca chuoi tu gia trung binh" % (100 * (cl or 0))
        khoi["tp_chuoi_tu_gia_tb"] = (KHONG, dt, ly)
    elif bac_thang:
        ly = ("san %.1f pip la TRAILING (cac gia tri tren san nam tren bac thang %.1f pip, khop %.0f%% so voi %.0f%% ngau nhien), "
              "khong phai TP co dinh" % (tpl[0][1], bac_thang["buoc"], 100 * bac_thang["ty_khop"], 100 * bac_thang["ty_ngau_nhien"]))
        khoi["tp_chuoi_tu_gia_tb"] = (KHONG, dt, ly)
    else:
        mo_ta = []
        for ten, L, r in tpl:
            mo_ta.append("chuoi %s lenh: bien duoi %.1f pip (%.0f%% chuoi nam trong [L, 2L], %.0f%% tai dung L)"
                         % (ten, L, 100 * (r["tp"]["ty_gan"] or 0), 100 * (r["tp"]["ty_nhon"] or 0)))
            ts["tp_pip_chuoi_%s" % ten] = _tham_so(_f(L, 2), "pip", "tp_chuoi_tu_gia_tb",
                                                   "bien duoi sac cua khoang cach thoat, chuoi %s lenh (n=%d, do phan giai gia %.2f pip; EA dong bang lenh thi truong thuong cho bien cao hon khai bao mot nac gia)" % (ten, r["n"], A["res_pip"]))
        ly = "thoat ca chuoi cach gia trung binh mot khoang toi thieu co dinh: " + "; ".join(mo_ta)
        if mt["loai"] == "tien":
            khoi["tp_chuoi_tu_gia_tb"] = (KHONG_RO, "thap", ly + "; nhung hang so nam o TIEN, khong o pip (xem tp_chuoi_tien)")
        else:
            khoi["tp_chuoi_tu_gia_tb"] = (CO, dt, ly)
    # ---- tp_chuoi_tien
    if mt["loai"] == "tien":
        ly = ("tien thu toi thieu cua chuoi o moi nhom lot gan nhu bang nhau (lan rong %.2f) trong khi pip thay doi (%.2f): "
              "TP theo tien" % (mt["lan_rong_tien"], mt["lan_rong_pip"]))
        p = [r["p05_tien"] for r in A["muc_tieu"]["nhom_lot"]]
        ts["tp_tien_usd"] = _tham_so(_f(float(np.median(p)), 2), "usd", "tp_chuoi_tien", "phan vi 5 cua tien thu theo nhom lot")
        khoi["tp_chuoi_tien"] = (CO, dt, ly)
    elif mt["loai"] == "pip":
        khoi["tp_chuoi_tien"] = (KHONG, dt, "khoang cach thoat co dinh THEO PIP o moi nhom lot (lan rong %.2f), tien thu thay doi theo lot (%.2f): "
                                 "khong phai TP theo tien" % (mt["lan_rong_pip"], mt["lan_rong_tien"]))
    elif mt["loai"] == "khong_ro":
        khoi["tp_chuoi_tien"] = (KHONG_RO, "thap", "ca pip va tien thu deu thay doi qua cac nhom lot (lan rong %.2f / %.2f)" % (
            mt["lan_rong_pip"], mt["lan_rong_tien"]))
    else:
        ly = "chua du 3 nhom lot (moi nhom >= 12 chuoi) de phan biet TP theo pip va theo tien"
        khoi["tp_chuoi_tien"] = (KHONG_DO_DUOC, "thap", ly)
    # ---- all_sniper: chuoi dai dong cung luc voi tong tien nho co dinh
    sau = c.ro[c.ro["da_dong"] & (c.ro["so_lenh"] >= 10) & np.isfinite(c.ro["tien_cuoi"])]
    if len(sau) < 10:
        khoi["all_sniper"] = (KHONG_DO_DUOC, "thap", "chi %d chuoi >= 10 lenh (< 10): khong du de thay khoi chot-tong-tien sau N lenh" % len(sau))
    else:
        rcv = _rcv(sau["tien_cuoi"].to_numpy(float))
        so_lieu["chuoi_dai_tien_rcv"] = _f(rcv, 3)
        if rcv <= 0.1:
            m = float(np.median(sau["tien_cuoi"]))
            ts["all_sniper_usd"] = _tham_so(_f(m, 2), "usd", "all_sniper", "tien thu trung vi cua chuoi >= 10 lenh")
            khoi["all_sniper"] = (CO, _do_tin(len(sau), 30, 12), "%d chuoi >= 10 lenh dong voi tien thu gan hang so %.2f USD (rcv %.2f)" % (len(sau), m, rcv))
        else:
            n20 = int((sau["so_lenh"] >= 20).sum())
            so_lieu["chuoi_ge20"] = n20
            if n20 < 5:
                khoi["all_sniper"] = (KHONG_DO_DUOC, "thap", "tien thu cua %d chuoi >= 10 lenh khong dam o mot gia tri (rcv %.2f), nhung chi %d chuoi toi 20 lenh "
                                      "(< 5): khoi chot-tong-tien thuong bat dau o lenh thu ~20 nen chua duoc kich hoat du de thay" % (len(sau), rcv, n20))
            else:
                khoi["all_sniper"] = (KHONG, _do_tin(len(sau), 30, 12), "tien thu cua %d chuoi >= 10 lenh (%d chuoi toi 20 lenh) khong dam o mot gia tri (rcv %.2f)" % (len(sau), n20, rcv))
    # ---- cat_lo_theo_tien
    am = A["n_chuoi_am"]
    if am < 15:
        khoi["cat_lo_theo_tien"] = (KHONG_DO_DUOC, "thap", "chi %d chuoi lo (< 15): khong du de thay muc cat lo theo tien" % am)
    elif A["bien_am"] and A["bien_am"][0]["ty_dinh"] >= 0.25:
        b = A["bien_am"][0]
        ts["cat_lo_usd"] = _tham_so(-_f(b["L"], 2), "usd", "cat_lo_theo_tien", "dam lo %d / %d chuoi lo" % (b["n_dinh"], am))
        khoi["cat_lo_theo_tien"] = (CO, _do_tin(am, 30, 15), "%d / %d chuoi lo dong voi lo ~ %.2f USD (bien sac)" % (b["n_dinh"], am, b["L"]))
    else:
        khoi["cat_lo_theo_tien"] = (KHONG, _do_tin(am, 30, 15), "%d chuoi lo, muc lo rai rac (khong co dam o mot gia tri): khong co cat lo co dinh" % am)
    # ---- thoat_rsi_va_tb_duong: khong co cum co dinh va khong co bien -> co the theo chi bao
    if tpl:
        khoi["thoat_rsi_va_tb_duong"] = (KHONG, dt, "thoat o khoang cach co dinh tu gia trung binh, khong phai theo chi bao")
    else:
        ly = "khong co cum thoat co dinh (khong bien duoi sac): co the thoat theo chi bao - can chuoi gia de doi chieu, chua kiem"
        khoi["thoat_rsi_va_tb_duong"] = (KHONG_RO, "thap", ly)
    kq, dt = _top(khoi)
    ly_chung = "; ".join("%s: %s" % (m, v[0]) for m, v in khoi.items())
    return _kq(kq, dt, ly_chung, so_lieu, ts, khoi=khoi)


def _do_hoa_von(c: Ctx) -> dict:
    """Trailing stop ca chuoi, keo SL ve hoa von, thoat hoa von khi chuoi dai."""
    A = _phan_tich_thoat(c)
    if not A["du"]:
        return _khong_do_duoc("hoa_von", "chi %d chuoi da dong (< %d)" % (A["n_dong"], TOI_THIEU_RO))
    n = A["n_dong"]
    dt = _dt_thoat(c, n)
    tpl = _tp_cua(A)
    cl = A["ty_cung_luc_nhieu_lenh"]
    ts: dict = {}
    khoi: dict = {}
    so_lieu = {"gan_hoa_von": A["gan_hoa_von"], "ty_ban_chung": A["ty_ban_chung"], "ly_ra_cum_cuoi": A["ly_ra_cum_cuoi"]}
    bt = [(t, L, r["tp"]["bac_thang"]) for t, L, r in tpl if r["tp"]["bac_thang"]]
    ly_ra = A["ly_ra_cum_cuoi"]
    tong_ly = max(1, sum(ly_ra.values()))
    # ---- trailing_stop_chuoi
    if bt:
        ten, L, b = bt[0]
        ts["trailing_khoa_dau_pip"] = _tham_so(_f(L, 2), "pip", "trailing_stop_chuoi",
                                               "san khoang cach thoat (chuoi %s lenh), bien duoi sac" % ten)
        ts["trailing_buoc_pip"] = _tham_so(_f(b["buoc"], 2), "pip", "trailing_stop_chuoi",
                                           "gia tri thoat nam tren luoi L + k*buoc: khop %.0f%% (ngau nhien %.0f%%)" % (100 * b["ty_khop"], 100 * b["ty_ngau_nhien"]))
        so_lieu["bac_thang"] = b
        rong = bool(len(bt) >= 2 and max(L2 for _, L2, _ in bt) - min(L2 for _, L2, _ in bt) > 0.1 * L)
        ly = ("thoat ca chuoi bang SL keo theo: khoang cach thoat khong bao gio duoi %.1f pip va cac gia tri tren no nam tren bac thang %.1f pip "
              "(khop %.0f%% so voi %.0f%% ngau nhien, %d chuoi)" % (L, b["buoc"], 100 * b["ty_khop"], 100 * b["ty_ngau_nhien"], b["n"]))
        if rong:
            ly += "; CHU Y san khac nhau giua cac nhom do sau"
        dtt = _ha(dt) if rong else dt
        khoi["trailing_stop_chuoi"] = (CO, dtt, ly)
        khoi["keo_sl_hoa_von_khi_co_lai"] = (KHONG_RO, "thap", "san %.1f pip co the la khoa dau cua trailing hoac delta keo SL ve hoa von: khong phan biet tu lenh" % L)
    else:
        tp_ly = ly_ra["tp"] / tong_ly
        if A["co_ly_do_ra"] and tp_ly >= 0.9:
            ly = "%.0f%% cum dong cuoi la [tp]: khong co SL keo theo" % (100 * tp_ly)
            khoi["trailing_stop_chuoi"] = (KHONG, dt, ly)
            khoi["keo_sl_hoa_von_khi_co_lai"] = (KHONG, dt, ly)
        else:
            cd = A.get("cum_duoi")
            if cd and cd.get("U_pip") is not None and cd["tren_canh_U"] <= 0.03 * cd["n"]:
                ly = ("%d chuoi (%.0f%% chuoi >= 2 lenh) thoat o CANH TREN sac ~ %.1f pip so voi gia trung binh (chi %d chuoi nam tren canh, trong khi bien TP %.1f pip), "
                      "duoi mem toi %.1f pip (gia nhay qua muc khoa khi EA dong bang lenh thi truong); %.0f%% la chuoi BAN (ca nhom %.0f%%). "
                      "Dung dang khoa loi / hoa von - deal khong phan biet trailing voi keo SL ve hoa von: doi chieu .set"
                      % (cd["n"], 100 * cd["ty_nhom"], cd["U_pip"], cd["tren_canh_U"], cd["tp_pip_nhom"], cd["p05"], 100 * cd["ty_ban"], 100 * cd["ty_ban_nhom"]))
                ts["khoa_loi_pip"] = _tham_so(cd["U_pip"], "pip", "trailing_stop_chuoi",
                                              "canh tren sac cua cum thoat duoi bien TP (chuoi >= 2 lenh), duoi mem phia duoi; khop 'initial SL' / khoa dau neu .set khai")
                so_lieu["cum_khoa_loi"] = cd
                so_lieu["quan_sat"] = [ly]
                khoi["trailing_stop_chuoi"] = (KHONG_RO, "thap", ly)
                khoi["keo_sl_hoa_von_khi_co_lai"] = (KHONG_RO, "thap", ly)
            else:
                ly = ("khong thay bac thang trong gia tri thoat (%s): neu co trailing thi bang lenh thi truong cua EA, khong nhin thay"
                      % ("ly do ra la [sl]" if (A["co_ly_do_ra"] and ly_ra["sl"] / tong_ly >= 0.5) else "khong co ly do ra tren lenh"))
                khoi["trailing_stop_chuoi"] = (KHONG_RO, "thap", ly)
                khoi["keo_sl_hoa_von_khi_co_lai"] = (KHONG_RO, "thap", ly)
    # ---- thoat_hoa_von_khi_chuoi_dai: ty le chuoi dong gan gia trung binh theo do sau
    gh = A["gan_hoa_von"]
    sau = [(t, r) for t, r in gh.items() if t in ("5-9", "10+") and r["n"] >= 15]
    nong = gh.get("2-4")
    if not sau:
        khoi["thoat_hoa_von_khi_chuoi_dai"] = (KHONG_DO_DUOC, "thap", "chi %d chuoi >= 5 lenh (< 15 moi nhom): khong du de thay thoat hoa von khi chuoi dai"
                                               % sum(r["n"] for t, r in gh.items() if t in ("5-9", "10+")))
    else:
        t, r = max(sau, key=lambda e: e[1]["ty"] or 0)
        if (r["ty"] or 0) >= 0.1:
            nong_ty = (nong or {}).get("ty")
            ban = "; %.0f%% cua chung la chuoi BAN (chung %.0f%%)" % (100 * r["ty_ban"], 100 * (A["ty_ban_chung"] or 0)) if r.get("ty_ban") is not None else ""
            ly = ("%.0f%% chuoi %s lenh dong gan gia trung binh (|x| <= %.1f pip)%s; chuoi 2-4 lenh: %s - khong thay bac nhay o mot do sau co dinh"
                  % (100 * r["ty"], t, r["ngu_pip"], ban, "%.0f%%" % (100 * nong_ty) if nong_ty is not None else "n/a"))
            khoi["thoat_hoa_von_khi_chuoi_dai"] = (KHONG_RO, "thap", ly)
            so_lieu["quan_sat"] = [ly + " (chua co khoi gan ten: bot co luat dong quanh hoa von, can xem bang theo do sau)"]
        else:
            khoi["thoat_hoa_von_khi_chuoi_dai"] = (KHONG, _do_tin(r["n"], 60, 25),
                                                    "%.0f%% chuoi %s lenh dong gan gia trung binh (|x| <= %.1f pip): khong co cum hoa von rieng khi chuoi dai" % (100 * (r["ty"] or 0), t, r["ngu_pip"]))
    kq, dt = _top(khoi)
    return _kq(kq, dt, "; ".join("%s: %s" % (m, v[0]) for m, v in khoi.items()), so_lieu, ts, khoi=khoi)


def _do_doi_tp(c: Ctx) -> dict:
    """TP doi theo do sau cua chuoi (khoi doi_tp_khi_lo): bien duoi cua cac nhom 2-4 / 5-9 / 10+ lenh co giam khong."""
    A = _phan_tich_thoat(c)
    if not A["du"]:
        return _khong_do_duoc("doi_tp", "chi %d chuoi da dong (< %d)" % (A["n_dong"], TOI_THIEU_RO))
    sau = [(t, L, r) for t, L, r in _tp_cua(A) if t != "1"]
    n_sau = sum(A["nhom"][t]["n"] for t in ("5-9", "10+"))
    so_lieu = {"bien_theo_nhom": {t: (r["tp"]["L"] if r.get("tp") else None) for t, r in A["nhom"].items()},
               "n_theo_nhom": {t: r["n"] for t, r in A["nhom"].items()}}
    if len(sau) < 2:
        ly = "chi %d nhom do sau (>= 2 lenh) co bien TP, chuoi >= 5 lenh co %d (< 15): khong du de so TP theo do sau" % (len(sau), n_sau)
        return _kq(KHONG_DO_DUOC, "thap", ly, so_lieu, khoi={"doi_tp_khi_lo": (KHONG_DO_DUOC, "thap", ly)})
    L0 = sau[0][1]
    L1 = sau[-1][1]
    dt = _dt_thoat(c, n_sau, 60, 25)
    if L1 <= 0.8 * L0:
        ly = "bien TP giam theo do sau: %s" % ", ".join("%s lenh %.1f pip" % (t, L) for t, L, _ in sau)
        ts = {"tp_pip_chuoi_sau": _tham_so(_f(L1, 2), "pip", "doi_tp_khi_lo", "bien TP chuoi %s lenh (so voi %.1f o chuoi %s)" % (sau[-1][0], L0, sau[0][0]))}
        return _kq(CO, dt, ly, so_lieu, ts, khoi={"doi_tp_khi_lo": (CO, dt, ly)})
    if abs(L1 - L0) <= 0.1 * max(L0, L1):
        ly = "bien TP khong doi theo do sau (%s)" % ", ".join("%s lenh %.1f pip" % (t, L) for t, L, _ in sau)
        return _kq(KHONG, dt, ly, so_lieu, khoi={"doi_tp_khi_lo": (KHONG, dt, ly)})
    ly = "bien TP doi giua cac nhom do sau nhung khong giam ro (%s)" % ", ".join("%s lenh %.1f pip" % (t, L) for t, L, _ in sau)
    return _kq(KHONG_RO, "thap", ly, so_lieu, khoi={"doi_tp_khi_lo": (KHONG_RO, "thap", ly)})


def _do_sl_tp_tung_lenh(c: Ctx) -> dict:
    """TP / SL gan RIENG tung lenh (ly do ra [tp] / [sl] cua tung lenh) o khoang cach co dinh so voi GIA VAO CUA CHINH LENH DO."""
    ten = ("tp_tung_lenh", "sl_cung")
    if not c.chat_luong.get("co_ly_do_ra"):
        return _khong_do_duoc("sl_tp_tung_lenh", "lenh dong khong mang ly do [tp] / [sl] (EA dong bang lenh thi truong): khong thay TP / SL gan tren lenh")
    o = c.lenh[c.lenh["dong"].notna()].copy()
    o["khoa"] = o["chieu"] * (o["gia_dong"] - o["gia_mo"]) / c.pip
    res = _res_gia(c.lenh, c.pip)
    khoi: dict = {}
    ts: dict = {}
    so_lieu: dict = {}
    # ---- TP: chi xet lenh don (chuoi 1 lenh): TP gan cua lenh don cung la TP cua chuoi
    don = o["ro"].map(o.groupby("ro").size()) == 1
    tp = o[(o["ly_do_ra"] == "tp") & don]["khoa"].to_numpy(float)
    so_lieu["tp_don_n"] = int(len(tp))
    b = _bien_duoi(tp, res, ty_dinh=0.5) if len(tp) >= 15 else []
    duong = [x for x in b if x["L"] > 0]
    if duong and duong[0]["ty_nhon"] >= 0.5:
        L = duong[0]["L"]
        ts["tp_pip"] = _tham_so(_f(L, 2), "pip", "tp_tung_lenh", "%d lenh don dong boi [tp] cach gia vao dung %.1f pip (%.0f%% tai dung gia)" % (len(tp), L, 100 * duong[0]["ty_nhon"]))
        khoi["tp_tung_lenh"] = (CO, _do_tin(len(tp), 40, 15),
                                "%.0f%% trong %d lenh don dong boi [tp] cach gia vao dung %.1f pip (khong phan biet TP lenh va TP chuoi: chuoi 1 lenh)"
                                % (100 * duong[0]["ty_dinh"], len(tp), L))
    elif len(tp) < 15:
        khoi["tp_tung_lenh"] = (KHONG_DO_DUOC, "thap", "chi %d lenh don dong boi [tp] (< 15)" % len(tp))
    else:
        khoi["tp_tung_lenh"] = (KHONG, _do_tin(len(tp), 40, 15), "khoang cach [tp] cua lenh don khong dam o mot gia tri")
    # ---- SL cung: lenh dong boi [sl] LO o khoang cach co dinh
    sl = -o[(o["ly_do_ra"] == "sl") & (o["khoa"] < 0)]["khoa"].to_numpy(float)
    so_lieu["sl_lo_n"] = int(len(sl))
    if len(sl) < 30:
        khoi["sl_cung"] = (KHONG_DO_DUOC, "thap", "chi %d lenh dong boi [sl] o muc lo (< 30)" % len(sl))
    else:
        b = _bien_duoi(sl, res, ty_dinh=0.3)
        if b and b[0]["ty_dinh"] >= 0.3:
            ts["sl_pip"] = _tham_so(_f(b[0]["L"], 2), "pip", "sl_cung", "%d / %d lenh dong boi [sl] lo cach gia vao ~ %.1f pip" % (b[0]["n_dinh"], len(sl), b[0]["L"]))
            khoi["sl_cung"] = (CO, _do_tin(len(sl), 60, 25), "%d / %d lenh lo dong boi [sl] o khoang cach ~ %.1f pip" % (b[0]["n_dinh"], len(sl), b[0]["L"]))
        else:
            khoi["sl_cung"] = (KHONG, _do_tin(len(sl), 60, 25),
                               "%d lenh dong boi [sl] o muc lo, khoang cach rai rac (khong co dam co dinh): SL la cua ca chuoi / trailing, khong gan co dinh tung lenh" % len(sl))
    kq, dt = _top(khoi)
    return _kq(kq, dt, "; ".join("%s: %s" % (m, v[0]) for m, v in khoi.items()), so_lieu, ts, khoi=khoi)


def _do_thoat_tung_phan(c: Ctx) -> dict:
    """Tia: dong MOT PHAN chuoi truoc phan con lai (so dot dong > 1, so lenh dong cung luc < so lenh dang mo)."""
    A = _phan_tich_thoat(c)
    if not A["du"]:
        return _khong_do_duoc("thoat_tung_phan", "chi %d chuoi da dong (< %d)" % (A["n_dong"], TOI_THIEU_RO))
    ro = c.ro[c.ro["da_dong"]]
    nhieu = ro[ro["so_lenh"] >= 2]
    sau = ro[ro["so_lenh"] >= 10]
    nhieu_dot = ro[ro["so_dot"] > 1]
    # do sau KIEM DUOC = so lenh lon nhat ma it nhat 8 chuoi da dong dat toi: tia bat dau o lenh sau hon muc nay chua tung duoc kich hoat
    sl = ro["so_lenh"].to_numpy(int)
    sau_kiem = next((k for k in range(int(sl.max()) if len(sl) else 1, 1, -1) if int((sl >= k).sum()) >= 8), 1)
    so_lieu = {"n_chuoi_nhieu_lenh": int(len(nhieu)), "n_chuoi_ge10": int(len(sau)), "n_chuoi_nhieu_dot_dong": int(len(nhieu_dot)),
               "ty_cung_luc_nhieu_lenh": A["ty_cung_luc_nhieu_lenh"], "do_sau_kiem_duoc_tia": int(sau_kiem)}
    khoi: dict = {}
    if len(nhieu_dot) >= 5:
        ty = float(len(nhieu_dot) / max(len(nhieu), 1))
        ly = "%d chuoi (%.0f%% chuoi nhieu lenh) dong lam nhieu dot: co tia / dong tung phan - xem chi tiet dot dong" % (len(nhieu_dot), 100 * ty)
        for m in _khoi_cua("thoat_tung_phan"):
            khoi[m] = (KHONG_RO, "thap", ly)
        return _kq(KHONG_RO, "thap", ly, so_lieu, khoi=khoi)
    if len(nhieu) < 20:
        return _khong_do_duoc("thoat_tung_phan", "chi %d chuoi nhieu lenh (< 20)" % len(nhieu), so_lieu)
    dt = _do_tin(len(nhieu), 100, 40)
    khoi["tia_cap_sau_dau"] = (KHONG, dt, "%d chuoi nhieu lenh deu dong MOT dot (ca chuoi cung luc): khong co tia cap" % len(nhieu))
    if len(sau) >= 10 and sau_kiem >= 8:
        dt_sau = _do_tin(len(sau), 30, 12)
        if sau_kiem < 20:
            dt_sau = _ha(dt_sau)       # chua tung thay chuoi >= 20 lenh (it nhat 8 chuoi): tia bat dau o lenh 20 van co the ton tai
        khoi["tia_n_lenh_khi_chuoi_dai"] = (KHONG, dt_sau, "%d chuoi >= 10 lenh deu dong mot dot: khong co tia khi chuoi dai (kiem duoc toi do sau %d lenh; "
                                            "tia bat dau o lenh sau hon chua kiem)" % (len(sau), sau_kiem))
    else:
        khoi["tia_n_lenh_khi_chuoi_dai"] = (KHONG_DO_DUOC, "thap", "chi %d chuoi >= 10 lenh va do sau kiem duoc %d lenh: bot co the co tia kich hoat tu lenh thu N (vd 15-20) chua toi do sau do" % (len(sau), sau_kiem))
    kq, dt = _top(khoi)
    return _kq(kq, dt, "; ".join("%s: %s" % (m, v[0]) for m, v in khoi.items()), so_lieu, khoi=khoi)


def _do_chuoi_sau(c: Ctx) -> dict:
    """Tran so lenh cung chieu dang mo (InpMaxBuyOrders...): cao nguyen o do sau lon nhat. Khong bao gio ket 'khong' neu chuoi chua cham tran."""
    ro = c.ro
    n = len(ro)
    ten = "tran_so_lenh"
    if n < TOI_THIEU_RO:
        return _khong_do_duoc("chuoi_sau", "chi %d chuoi (< %d)" % (n, TOI_THIEU_RO))
    sau = ro["n_mo_max"].to_numpy(int)
    dem = pd.Series(sau).value_counts().sort_index()
    N = int(dem.index.max())
    so_lieu = {"do_sau_lon_nhat": N, "so_chuoi_do_sau_do": int(dem.iloc[-1]), "phan_bo_do_sau": {int(k): int(v) for k, v in dem.items() if k >= max(1, N - 6)}}
    truoc = int(dem.get(N - 1, 0))
    if N >= 5 and int(dem.iloc[-1]) >= 3 and int(dem.iloc[-1]) >= truoc:
        dt = _do_tin(int(dem.iloc[-1]), 10, 5)
        ly = "%d chuoi dung dung o do sau %d lenh (nhieu hon hoac bang chuoi sau %d lenh: %d): cao nguyen = tran so lenh" % (int(dem.iloc[-1]), N, N - 1, truoc)
        return _kq(CO, dt, ly, so_lieu, {"tran_so_lenh": _tham_so(N, "lenh", ten, "so lenh cung chieu dang mo toi da (lech 1 la cach dem)")},
                   khoi={ten: (CO, dt, ly)})
    ly = ("chuoi sau nhat %d lenh (%d chuoi), chua thay cao nguyen: bot chua cham tran nao trong lich su nay - tran neu co nam sau hon %d"
          % (N, int(dem.iloc[-1]), N))
    return _kq(KHONG_DO_DUOC, "thap", ly, so_lieu, khoi={ten: (KHONG_DO_DUOC, "thap", ly)})


def _do_rui_ro(c: Ctx) -> dict:
    """Tran lot tong (InpMaxLots): nhieu chuoi cung dung o MOT lot dinh. Khong bao gio ket 'khong' neu chua cham tran."""
    ro = c.ro
    ten = "tran_lot_tong"
    if len(ro) < TOI_THIEU_RO:
        return _khong_do_duoc("rui_ro", "chi %d chuoi (< %d)" % (len(ro), TOI_THIEU_RO))
    dinh = ro["lot_dinh"].round(4)
    m = float(dinh.max())
    k = int((dinh >= m - 1e-9).sum())
    nhom = dinh[dinh < m - 1e-9]
    k2 = float(nhom.max()) if len(nhom) else float("nan")
    so_lieu = {"lot_dinh_lon_nhat": _f(m, 4), "so_chuoi_o_lot_dinh": k, "lot_dinh_ke_tiep": _f(k2, 4)}
    if k >= 3 and (not np.isfinite(k2) or k2 <= 0.97 * m):
        dt = _do_tin(k, 10, 5)
        ly = "%d chuoi dung dung o lot tong %.2f (lot dinh ke tiep %s): cao nguyen = tran lot" % (k, m, "%.2f" % k2 if np.isfinite(k2) else "n/a")
        return _kq(CO, dt, ly, so_lieu, {"tran_lot_tong": _tham_so(_f(m, 4), "lot", ten, "tong lot cung chieu dang mo toi da cua mot chuoi")}, khoi={ten: (CO, dt, ly)})
    ly = "lot tong lon nhat %.2f (%d chuoi), chua thay cao nguyen: bot chua cham tran lot nao - tran neu co lon hon %.2f" % (m, k, m)
    return _kq(KHONG_DO_DUOC, "thap", ly, so_lieu, khoi={ten: (KHONG_DO_DUOC, "thap", ly)})


# ============================================================== 5. GIO / NGAY, NHIP THEM LENH, THEM KHI HOI, GONG DUONG, DIEU KIEN VAO
_KHUNG_NEN = (1, 5, 15, 30, 60)          # phut
#: cac khung nen cua MT5 tu M1 den H4 (phut) dung de tim luat 'moi nen mot lenh'
_KHUNG_MT5 = (1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60, 120, 240)


_B_GIO, _B_THU = "loc_gio_giao_dich", "loc_ngay_thu_lich"
_B_NEN, _B_DCA_N = "luoi_theo_nen_moi", "loc_dca_tu_lenh_n"
_B_XU_HUONG, _B_HOI, _B_TIN_HIEU, _B_NHOI = "vao_theo_xu_huong", "luoi_day_khi_gia_hoi", "them_lenh_theo_tin_hieu", "nhoi_theo_loi"


def _dung_khoi(kiem: str, *ma: str) -> tuple:
    """Danh muc khoi cua phep do `kiem` phai KHOP CHINH XAC voi cac ma ma phep do nay chiu trach nhiem (doi danh muc ma quen sua phep do -> bao ngay)."""
    ten = _khoi_cua(kiem)
    if set(ten) != set(ma):
        raise RuntimeError("phep do %s lech danh muc khoi: %s != %s" % (kiem, sorted(ten), sorted(ma)))
    return ten




def _poisson_duoi(k: int, mu: float) -> float:
    """P(X <= k), X ~ Poisson(mu) (tinh trong khong gian log de khong tran so)."""
    if mu <= 0:
        return 1.0
    lg = [-mu + i * math.log(mu) - math.lgamma(i + 1) for i in range(int(k) + 1)]
    m = max(lg)
    return float(min(1.0, math.exp(m) * sum(math.exp(x - m) for x in lg)))


def _vung_lien_tuc(gio) -> list[tuple[int, int]]:
    """Gom cac gio (0-23) thanh doan lien tiep tren vong tron 24 gio: [(gio_bat_dau, so_gio)]."""
    s = sorted(set(int(h) % 24 for h in gio))
    if not s:
        return []
    if len(s) == 24:
        return [(0, 24)]
    for i in range(len(s)):
        if (s[i] - 1) % 24 not in s:
            s = s[i:] + s[:i]
            break
    ds, cur = [], [s[0]]
    for h in s[1:]:
        if h == (cur[-1] + 1) % 24:
            cur.append(h)
        else:
            ds.append((cur[0], len(cur)))
            cur = [h]
    ds.append((cur[0], len(cur)))
    return ds


def _mo_ta_vung(ds) -> str:
    return ", ".join("%02d:00-%02d:00" % (b, (b + n) % 24) for b, n in ds) or "khong co"


def _do_gio_ngay(c: Ctx) -> dict:
    """Bo loc gio / thu (loc_gio_giao_dich, loc_ngay_thu_lich): gio / thu co lenh DONG (bot dang hoat dong) nhung KHONG bat dau chuoi moi.
    Gio khong co ca lenh mo lan dong la NGHI SAN: khong the phan biet voi bo loc khoa ca viec dong nen khong tinh la bo loc.
    Lich (ngay le, dau - cuoi thang) va tre dau ngay chi do duoc phan thu trong tuan; phan con lai ghi la chua do."""
    o = c.lenh
    ten = _dung_khoi("gio_ngay", _B_GIO, _B_THU)
    dau = o["n_mo"].to_numpy(int) == 0
    n_dau = int(dau.sum())
    if n_dau < 100:
        return _khong_do_duoc("gio_ngay", "chi %d chuoi bat dau (< 100): khong du de thay gio / thu nao bi bo" % n_dau, {"n_chuoi": n_dau})
    dg = o["dong"].dropna()
    h_mo, h_dong = o["mo"].dt.hour.to_numpy(int), dg.dt.hour.to_numpy(int)
    w_mo, w_dong = o["mo"].dt.weekday.to_numpy(int), dg.dt.weekday.to_numpy(int)
    bd = np.bincount(h_mo[dau], minlength=24)
    them = np.bincount(h_mo[~dau], minlength=24)
    dong_h = np.bincount(h_dong, minlength=24)
    song = (bd + them + dong_h) > 0
    tb = n_dau / 24.0
    nghi = [h for h in range(24) if not song[h]]
    cam = [h for h in range(24) if song[h] and bd[h] == 0]
    it = [h for h in range(24) if song[h] and 0 < bd[h] <= 0.1 * tb]
    so_lieu = {"n_chuoi": n_dau, "chuoi_theo_gio": [int(x) for x in bd], "them_theo_gio": [int(x) for x in them],
               "dong_theo_gio": [int(x) for x in dong_h], "gio_nghi_san": nghi}
    ts = {}
    khoi = {}
    # ---------------------------------------------------------------- gio
    if cam and tb >= 7.0:
        dt = "cao" if tb >= 12.0 else "vua"
        ly = ("gio %s: bot van DONG lenh nhung khong bat dau chuoi nao trong khi trung binh moi gio %.0f chuoi (xac suat ngau nhien moi gio ~ %.0e)"
              % (_mo_ta_vung(_vung_lien_tuc(cam)), tb, math.exp(-tb)))
        ts["gio_cam_vao_chuoi"] = _tham_so(cam, "gio", "loc_gio_giao_dich", "gio may chu (gio cua file lich su); chuoi moi KHONG mo trong cac gio nay")
        cho = _vung_lien_tuc([h for h in range(24) if bd[h] > 0])
        if len(cho) == 1:
            ts["gio_mo_tu"] = _tham_so(cho[0][0], "gio", "loc_gio_giao_dich", "gio dau cua doan cho phep mo chuoi moi (gio may chu)")
            ts["gio_mo_den"] = _tham_so((cho[0][0] + cho[0][1]) % 24, "gio", "loc_gio_giao_dich", "gio het doan cho phep (khong tinh gio nay)")
        khoi[_B_GIO] = (CO, dt, ly)
    elif cam or it:
        ly = ("gio %s co it chuoi bat dau (<= 10%% trung binh %.0f) nhung mau %s: chua ket luan duoc co bo loc gio"
              % (_mo_ta_vung(_vung_lien_tuc(cam + it)), tb, "con it (< 7 chuoi / gio)" if tb < 7.0 else "van co chuoi"))
        khoi[_B_GIO] = (KHONG_RO, "thap", ly)
    elif tb >= 10.0:
        ly = ("chuoi bat dau o MOI gio co hoat dong (it nhat %d chuoi / gio, trung binh %.0f)%s"
              % (int(min(bd[h] for h in range(24) if song[h])), tb,
                 "; gio %s khong co ca lenh mo lan dong: nghi san, khong phai bo loc" % _mo_ta_vung(_vung_lien_tuc(nghi)) if nghi else ""))
        khoi[_B_GIO] = (KHONG, _do_tin(n_dau, 600, 240), ly)
    else:
        khoi[_B_GIO] = (KHONG_RO, "thap", "chi %d chuoi (< 240): moi gio ~%.0f chuoi, it de ket luan khong co bo loc gio" % (n_dau, tb))
    # ---------------------------------------------------------------- thu trong tuan
    wd = np.bincount(w_mo[dau], minlength=7)
    wev = np.bincount(np.r_[w_mo, w_dong], minlength=7)
    live = [d for d in range(7) if wev[d] > 0]
    tw = n_dau / max(1, len(live))
    thu_cam = [d for d in live if wd[d] <= 0.05 * tw]
    so_lieu["chuoi_theo_thu"] = [int(x) for x in wd]
    so_lieu["thu_co_lenh"] = live
    # tre dau ngay (tham so kieu 'MinuteDelayNewDay'): do theo GIO DONG HO may chu, KHONG theo 'hoat dong dau tien cua ngay' (neu chinh chuoi la
    # hoat dong dau tien thi tre = 0 mot cach tam thuong, du bot co cho - sai lam cua ban dau, sua 04/10). `chuoi_theo_30_phut` = so chuoi bat dau
    # theo tung o 30 phut cua ngay may chu (48 o); `tre_sau_mo_cua_phut_*` = phut tu luc san mo lai sau doan nghi dai nhat den moi chuoi bat dau.
    # Bot cho X phut thi KHONG chuoi nao bat dau truoc X phut ke tu 00:00 (cach doc yeu nhat): `ho_so_set` dung o nay de bac bo / xac nhan tre.
    t_chuoi = o["mo"][dau]
    phut_ngay = (t_chuoi.dt.hour * 60 + t_chuoi.dt.minute).to_numpy(float)
    so_lieu["chuoi_theo_30_phut"] = [int(x) for x in np.bincount((phut_ngay // 30).astype(int), minlength=48)[:48]]
    if nghi:
        h_nghi = max(_vung_lien_tuc(nghi), key=lambda x: x[1])
        gio_mo = (h_nghi[0] + h_nghi[1]) % 24
        sau_mo = (phut_ngay - 60.0 * gio_mo) % 1440.0
        so_lieu["gio_mo_cua_lai"] = int(gio_mo)
        so_lieu["tre_sau_mo_cua_phut_min"] = _f(float(sau_mo.min()), 1)
        so_lieu["tre_sau_mo_cua_phut_p05"] = _f(_q(sau_mo, 5), 1)
        so_lieu["ty_chuoi_2_gio_dau_sau_mo_cua"] = _f(float((sau_mo < 120.0).mean()), 3)
    # tre dau ngay: ty le chuoi trong 2 gio dau sau vung nghi san so voi muc trung binh
    if nghi:
        h0 = max(_vung_lien_tuc(nghi), key=lambda x: x[1])
        h1 = (h0[0] + h0[1]) % 24
        song_n = max(1, int(song.sum()))
        r2 = float((bd[h1] + bd[(h1 + 1) % 24]) / (2.0 * n_dau / song_n))
        so_lieu["ty_chuoi_2_gio_dau_ngay_so_voi_trung_binh"] = _f(r2, 2)
    else:
        r2 = None
    if thu_cam and tw >= 20.0:
        ly = ("thu %s: bot van hoat dong (co lenh dong) nhung khong bat dau chuoi nao trong khi trung binh moi thu %.0f chuoi"
              % (", ".join("T%d" % (d + 2) if d < 6 else "CN" for d in thu_cam), tw))
        ts["thu_cam_vao_chuoi"] = _tham_so(thu_cam, "thu", "loc_ngay_thu_lich", "0 = thu Hai ... 6 = Chu nhat (gio may chu); chuoi moi khong mo vao cac thu nay")
        khoi[_B_THU] = (CO, "cao" if tw >= 40 else "vua", ly)
    else:
        ly = ("khong thay thu nao trong tuan bi bo (moi thu co lenh deu co chuoi bat dau)%s; lich ngay le / dau - cuoi thang chua do duoc (can lich su nhieu nam)"
              % ("; %.0f%% chuoi nam trong 2 gio dau ngay so voi muc trung binh: %s" % (100 * r2, "khong thay tre dau ngay" if r2 >= 0.5 else "co the co tre dau ngay")
                 if r2 is not None else ""))
        khoi[_B_THU] = (KHONG_RO, "thap", ly) if tw >= 20.0 else (KHONG_RO, "thap", "mau it theo thu (%.0f chuoi / thu): %s" % (tw, ly))
    kl, dt = _top(khoi)
    return _kq(kl, dt, "; ".join("%s: %s" % (m, v[0]) for m, v in khoi.items()), so_lieu, ts, khoi=khoi)


def _can_nen(s, T: int, L: float) -> tuple[int, int, float]:
    """(so su kien roi vao L giay dau cua nen T phut, tong, muc ngau nhien)."""
    s = np.asarray(s, float)
    return int(((s % (T * 60.0)) < L).sum()), int(len(s)), min(1.0, L / (T * 60.0))


def _khung_can_nen(s, L: float) -> tuple[int | None, dict, list]:
    """Khung nen LON NHAT T (cac khung nen cua MT5) ma >= 90% su kien roi vao L giay dau nen va CAO HON HAN ngau nhien (nhi thuc <= 1e-6);
    khung khong do duoc khi muc ngau nhien > 0.7 hoac < 30 su kien. Cac khung thoa phai la UOC cua T (nen long vao nhau): M1 thoa khi M2 thoa.
    Tra ve (T hoac None neu khong co / khong nhat quan, bang theo khung, danh sach khung thoa)."""
    bang, khop_T = {}, []
    for T in _KHUNG_MT5:
        k, m, ng = _can_nen(s, T, L)
        do_duoc = bool(ng <= 0.7 and m >= 30)
        khop = bool(do_duoc and k >= 0.9 * m and _duoi_nhi_thuc(k, m, ng) <= 1e-6)
        bang["%d" % T] = {"ty_can_nen": _f(k / m, 3) if m else None, "ty_ngau_nhien": _f(ng, 3), "do_duoc": do_duoc, "khop": khop}
        if khop:
            khop_T.append(T)
    T = max(khop_T) if khop_T else None
    if T is not None and not all(T % x == 0 for x in khop_T):
        T = None
    return T, bang, khop_T


def _khung_vao(c: Ctx) -> dict:
    """Khung nen ma thoi diem MO CHUOI MOI bam theo (entry chi kiem khi nen moi): xem `_khung_can_nen`, ap len cac lenh vao chuoi."""
    if "khung_vao" in c.cache:
        return c.cache["khung_vao"]
    o = c.lenh
    s = o["mo_s"].to_numpy(float)[o["n_mo"].to_numpy(int) == 0]
    L = _cua_so(c)
    r = {"n": int(len(s)), "cua_so_s": _f(L, 1), "khung": {}, "T": None, "khung_thoa": [], "giay0": None}
    c.cache["khung_vao"] = r
    if len(s) < 30:
        return r
    r["giay0"] = _f(float(((s % 60.0) < 1.0).mean()), 3)
    r["T"], r["khung"], r["khung_thoa"] = _khung_can_nen(s, L)
    return r


def _cap_cung_nen(s, t, B: float) -> tuple[int, float, int]:
    """(so cap cung mot nen B giay, ky vong ngau nhien, so cap cach nhau < B giay). Ky vong: cap cach g < B giay roi cung nen voi xac suat (B - g) / B."""
    g = s - t
    gan = g < B
    esp = float(((B - g[gan]) / B).sum())
    obs = int((np.floor(t[gan] / B) == np.floor(s[gan] / B)).sum())
    return obs, esp, int(gan.sum())


def _do_nhip_them_lenh(c: Ctx) -> dict:
    """Nhip them lenh. (a) lenh them chi mo o DAU nen khung T (>= 90% trong L giay dau nen, cao hon han ngau nhien); hoac
    (b) TOI DA MOT lenh them moi nen T: xet rieng cac cap (lenh them, lenh them ke tiep) cua mot chuoi - cap cach nhau g < T phut roi cung nen
    voi xac suat (T - g) / T; neu ky vong >= 5 cap ma thuc te <= 10% (Poisson <= 1e-3) thi co luat; khung T la khung LON NHAT thoa va moi khung
    thoa phai la uoc cua T (cac nen long vao nhau: M3, M5 thoa khi M15 thoa). Cap (lenh vao, lenh them dau) tach rieng: luat co the khong tinh
    lenh vao. Tester dat tick o giay :00 / :20 / :40 nen khoang cach ngan la 20 / 40 giay chu khong phai nhip that cua EA.
    Khong co cap nao du sat nhau thi KHONG DO DUOC (khong phai 'khong')."""
    o = c.lenh
    ten = _dung_khoi("nhip_them_lenh", _B_NEN, _B_DCA_N)
    nm = o["n_mo"].to_numpy(int)
    th = nm >= 1
    n = int(th.sum())
    ly_n = "bo loc DCA tu lenh N (neu co) chua ro bo loc gi: can duong gia de thay lenh them nao bi chan"
    khoi = {}
    if n < 30:
        ly = "chi %d lenh them vao chuoi (< 30): khong du de thay nhip them lenh" % n
        return _kq(KHONG_DO_DUOC, "thap", ly, {"n_lenh_them": n}, khoi={m: (KHONG_DO_DUOC, "thap", ly) for m in ten})
    S, TT = o["mo_s"].to_numpy(float), o["t_cuoi"].to_numpy(float)
    ok = th & np.isfinite(TT) & (S >= TT)
    s, t = S[ok & (nm >= 2)], TT[ok & (nm >= 2)]            # cap (lenh them, lenh them ke tiep)
    s1, t1 = S[ok & (nm == 1)], TT[ok & (nm == 1)]           # cap (lenh vao, lenh them dau)
    L = _cua_so(c)
    ts = {}
    so_lieu = {"n_lenh_them": n, "n_cap_them_them": int(len(s)), "n_cap_vao_them_dau": int(len(s1)), "cua_so_s": _f(L, 1),
               "can_nen": {}, "mot_nen": {}, "vao_them_dau": {}}
    can, so_lieu["can_nen"], _ = _khung_can_nen(S[th], L)
    khop_T = []
    for T in _KHUNG_MT5:
        obs, esp, ncap = _cap_cung_nen(s, t, T * 60.0) if len(s) else (0, 0.0, 0)
        p = _poisson_duoi(obs, esp) if esp > 0 else 1.0
        khop = bool(esp >= 5.0 and obs <= 0.1 * esp and p <= 1e-3)
        so_lieu["mot_nen"]["%d" % T] = {"cap_sat_nhau": ncap, "ky_vong_cung_nen": _f(esp, 1), "thuc_te_cung_nen": obs, "khop": khop}
        if khop:
            khop_T.append(T)
    mot = max(khop_T) if khop_T else None
    nhat_quan = bool(mot is not None and all(mot % T == 0 for T in khop_T))
    so_lieu["khung_thoa"] = khop_T
    if mot is not None:
        obs1, esp1, nc1 = _cap_cung_nen(s1, t1, mot * 60.0) if len(s1) else (0, 0.0, 0)
        so_lieu["vao_them_dau"] = {"cap_sat_nhau": nc1, "ky_vong_cung_nen": _f(esp1, 1), "thuc_te_cung_nen": obs1}
    if can is not None:
        ly = "%.0f%% lenh them mo trong %.0f giay dau nen %d phut (ngau nhien %.0f%%): chi them khi mo nen moi" % (
            100 * so_lieu["can_nen"]["%d" % can]["ty_can_nen"], L, can, 100 * so_lieu["can_nen"]["%d" % can]["ty_ngau_nhien"])
        ts["khung_them_phut"] = _tham_so(can, "phut", _B_NEN, "lenh them chi mo o dau nen khung nay")
        khoi[_B_NEN] = (CO, _do_tin(n, 100, 40), ly)
    elif mot is not None and nhat_quan:
        mo = so_lieu["mot_nen"]["%d" % mot]
        v = so_lieu["vao_them_dau"]
        ve = ("; cap (lenh vao, lenh them dau) van cung nen %d / %d cap (ky vong %.0f): luat khong tinh lenh vao" % (v["thuc_te_cung_nen"], v["cap_sat_nhau"], v["ky_vong_cung_nen"])
              if v and v["ky_vong_cung_nen"] >= 5.0 and v["thuc_te_cung_nen"] > 0.5 * v["ky_vong_cung_nen"] else "")
        ly = ("%d cap lenh them lien nhau khong cap nao cung nen %d phut (ky vong ngau nhien %.0f cap, thuc te %d): toi da MOT lenh them moi nen %d phut%s"
              % (mo["cap_sat_nhau"], mot, mo["ky_vong_cung_nen"], mo["thuc_te_cung_nen"], mot, ve))
        ts["toi_da_lenh_moi_nen_phut"] = _tham_so(mot, "phut", _B_NEN, "khong co hai lenh them lien nhau cua mot chuoi trong cung mot nen khung nay (nen cua bieu do chay EA)")
        khoi[_B_NEN] = (CO, _do_tin(int(mo["ky_vong_cung_nen"]), 60, 20), ly)
    elif mot is not None:
        khoi[_B_NEN] = (KHONG_RO, "thap", "cac khung thoa luat (%s) khong long vao nhau: khong chot duoc khung nen" % ", ".join("M%d" % T for T in khop_T))
    else:
        chua_do = [T for T in _KHUNG_NEN if so_lieu["mot_nen"]["%d" % T]["ky_vong_cung_nen"] < 5.0]
        so_lieu["khung_chua_do_duoc"] = chua_do
        if not chua_do:
            esp_min = min(so_lieu["mot_nen"]["%d" % T]["ky_vong_cung_nen"] for T in _KHUNG_NEN)
            ly = ("o MOI khung M1 / M5 / M15 / M30 / H1 deu du cap lenh them lien nhau (ky vong cung nen >= %.0f) va thuc te co cap cung nen: "
                  "khong co luat 'moi nen mot lenh them'" % esp_min)
            khoi[_B_NEN] = (KHONG, _do_tin(int(esp_min), 20, 8), ly)
        else:
            ly = ("khung %s phut khong du cap lenh them sat nhau (ky vong cung nen < 5; chi %d cap lien nhau): khong the loai luat 'moi nen mot lenh them' "
                  "o cac khung do (khung %s phut do duoc va khong co luat)"
                  % (", ".join(str(T) for T in chua_do), len(s), ", ".join(str(T) for T in _KHUNG_NEN if T not in chua_do) or "khong co"))
            khoi[_B_NEN] = (KHONG_DO_DUOC, "thap", ly)
    sau = int(nm.max()) + 1
    khoi[_B_DCA_N] = (KHONG_DO_DUOC, "thap", "%s (chuoi sau nhat %d lenh)" % (ly_n, sau))
    kl, dt = _top(khoi)
    return _kq(kl, dt, "; ".join("%s: %s" % (m, v[0]) for m, v in khoi.items()), so_lieu, ts, khoi=khoi)


def _do_them_khi_hoi(c: Ctx) -> dict:
    """Cach THEM lenh vao chuoi: cac lenh them co mo o gia TOT hon lenh truoc (gia da hoi, `buoc_cuoi` < 0), co mo khi chuoi dang LAI
    (gia lenh them nam phia loi so voi gia trung binh), va co mo SAT lenh truoc (it hon nua buoc: them theo tin hieu chu khong theo khoang gia).
    `khong` chi khi du lenh them (>= 30 / 100) de mot hanh vi dang co phai xuat hien; tin hieu vao theo xu huong cua chuoi MOI can duong gia."""
    o = c.lenh
    ten = _dung_khoi("them_khi_hoi", _B_XU_HUONG, _B_HOI, _B_TIN_HIEU, _B_NHOI)
    th = o["n_mo"].to_numpy(int) >= 1
    n = int(th.sum())
    if n < 30:
        return _khong_do_duoc("them_khi_hoi", "chi %d lenh them vao chuoi (< 30): khong du de thay cach them" % n, {"n_lenh_them": n})
    res = _res_gia(o, c.pip)
    bc = o["buoc_cuoi"].to_numpy(float)[th]
    tb = o["tb_cung"].to_numpy(float)[th]
    loi = (o["chieu"].to_numpy(float)[th] * (o["gia_mo"].to_numpy(float)[th] - tb)) / c.pip       # + = chuoi dang lai luc them
    ok = np.isfinite(bc)
    okl = np.isfinite(loi)
    nb, nl = int(ok.sum()), int(okl.sum())
    if nb < 30:
        return _khong_do_duoc("them_khi_hoi", "chi %d lenh them co gia lenh truoc (< 30)" % nb, {"n_lenh_them": n})
    n_hoi = int((bc[ok] < -res).sum())
    ty_hoi = n_hoi / nb
    n_loi = int((loi[okl] > res).sum())
    ty_loi = n_loi / max(1, nl)
    med = float(np.nanmedian(bc[ok][bc[ok] > 0])) if (bc[ok] > 0).any() else float("nan")
    n_sat = int((np.abs(bc[ok]) < 0.5 * med).sum()) if np.isfinite(med) else 0
    ty_sat = n_sat / nb
    so_lieu = {"n_lenh_them": nb, "them_o_gia_tot_hon": n_hoi, "ty_them_o_gia_tot_hon": _f(ty_hoi, 4), "them_khi_chuoi_dang_lai": n_loi,
               "ty_them_khi_chuoi_dang_lai": _f(ty_loi, 4), "buoc_trung_vi_pip": _f(med, 2), "them_sat_lenh_truoc": n_sat,
               "ty_them_sat_lenh_truoc": _f(ty_sat, 4), "buoc_p05_p50_p95": [_f(_q(bc[ok], p), 2) for p in (5, 50, 95)]}
    khoi = {}
    ts = {}
    dt_k = _do_tin(nb, 100, 30)
    if n_hoi >= 10 and ty_hoi >= 0.10:
        ly = "%d / %d lenh them (%.0f%%) mo o gia TOT hon lenh truoc (gia da hoi roi van them)" % (n_hoi, nb, 100 * ty_hoi)
        khoi[_B_HOI] = (CO, _do_tin(n_hoi, 30, 10), ly)
        hoi = -bc[ok][bc[ok] < -res]
        ts["buoc_them_khi_hoi_pip"] = _tham_so(_f(_q(hoi, 10), 2), "pip", _B_HOI, "p10 khoang gia lenh them nam phia loi so voi lenh truoc (p50 %.1f)" % _q(hoi, 50))
    elif ty_hoi >= 0.03:
        khoi[_B_HOI] = (KHONG_RO, "thap", "%d / %d lenh them (%.1f%%) mo o gia tot hon lenh truoc: it, chua ket luan" % (n_hoi, nb, 100 * ty_hoi))
    else:
        khoi[_B_HOI] = (KHONG, dt_k, "%d / %d lenh them mo o gia tot hon lenh truoc: luoi them khi gia di NGUOC, khong them khi gia hoi" % (n_hoi, nb))
    if ty_hoi >= 0.5:
        khoi[_B_XU_HUONG] = (CO, dt_k, "%.0f%% lenh them mo o gia tot hon lenh truoc: them theo chieu loi (xu huong)" % (100 * ty_hoi))
    elif ty_hoi < 0.10:
        khoi[_B_XU_HUONG] = (KHONG, _ha(dt_k), "chi %.1f%% lenh them theo chieu loi: luoi them nguoc xu huong; huong chuoi MOI so voi xu huong chua do duoc (can duong gia)" % (100 * ty_hoi))
    else:
        khoi[_B_XU_HUONG] = (KHONG_RO, "thap", "%.0f%% lenh them theo chieu loi: lan lon, chua ket luan" % (100 * ty_hoi))
    if n_loi >= 10 and ty_loi >= 0.10:
        khoi[_B_NHOI] = (CO, _do_tin(n_loi, 30, 10), "%d / %d lenh them (%.0f%%) mo luc chuoi dang LAI (nhoi theo loi)" % (n_loi, nl, 100 * ty_loi))
    elif ty_loi >= 0.03:
        khoi[_B_NHOI] = (KHONG_RO, "thap", "%d / %d lenh them mo luc chuoi dang lai: it, chua ket luan" % (n_loi, nl))
    else:
        khoi[_B_NHOI] = (KHONG, dt_k, "%d / %d lenh them mo luc chuoi dang lai: chuoi chi duoc them khi dang LO" % (n_loi, nl))
    if not np.isfinite(med):
        khoi[_B_TIN_HIEU] = (KHONG_RO, "thap", "khong lenh them nao mo o phia LO so voi lenh truoc: khong co buoc trung vi de so")
    elif n_sat >= 10 and n_sat >= 0.2 * nb:
        khoi[_B_TIN_HIEU] = (CO, _do_tin(n_sat, 30, 10),
                             "%d / %d lenh them (%.0f%%) mo SAT lenh truoc (< nua buoc trung vi %.1f pip): them theo tin hieu / dot lenh, khong theo khoang gia"
                             % (n_sat, nb, 100 * ty_sat, med))
    elif ty_sat <= 0.03:
        khoi[_B_TIN_HIEU] = (KHONG, dt_k, "chi %.1f%% lenh them mo sat lenh truoc (< nua buoc trung vi %.1f pip): them theo khoang gia (luoi), khong theo dot tin hieu" % (100 * ty_sat, med))
    else:
        khoi[_B_TIN_HIEU] = (KHONG_RO, "thap", "%.0f%% lenh them mo sat lenh truoc: lan lon, chua ket luan" % (100 * ty_sat))
    kl, dt = _top(khoi)
    return _kq(kl, dt, "; ".join("%s: %s" % (m, v[0]) for m, v in khoi.items()), so_lieu, ts, khoi=khoi)


def _do_gong_duong(c: Ctx) -> dict:
    """Gong lenh dang lai de can lenh am: can biet LUC NAO lenh dang lai (duong gia theo thoi gian); deal chi cho gia dong -> khong do duoc."""
    ten = _khoi_cua("gong_duong")
    ly = ("lich su lenh chi cho gia dong, khong cho lenh nao dang lai o thoi diem nao: khong the thay lenh duong bi GIU trong khi dang lai "
          "(can duong gia theo thoi gian de dung lai lai-lo tung lenh)")
    return _kq(KHONG_DO_DUOC, "thap", ly, {}, khoi={m: (KHONG_DO_DUOC, "thap", ly) for m in ten})


def _do_dieu_kien_vao(c: Ctx) -> dict:
    """Dieu kien VAO (RSI qua ban, tam gia ngay, MA): can DUONG GIA truoc thoi diem vao, deal khong co -> khong do duoc. Do duoc o day:
    chuoi moi co bam dau nen khung nao khong (khung tin hieu), de doi chieu voi tham so khung cua .set."""
    ten = _khoi_cua("dieu_kien_vao")
    kv = _khung_vao(c)
    ts = {}
    them = ""
    if kv["T"] is not None:
        k = kv["khung"]["%d" % kv["T"]]
        them = (" Do duoc: chuoi moi chi mo o dau nen %d phut (%.0f%% chuoi trong %.0f giay dau nen, ngau nhien %.0f%%)."
                % (kv["T"], 100 * k["ty_can_nen"], kv["cua_so_s"], 100 * k["ty_ngau_nhien"]))
        ts["khung_tin_hieu_phut"] = _tham_so(kv["T"], "phut", "vao_chi_bao_ngoai",
                                             "khung nen ma entry chi kiem khi mo nen moi (khung lon nhat khop; khop moi khung nho hon no)")
    ly = ("tin hieu vao (RSI / tam gia / MA) can DUONG GIA truoc thoi diem vao: lich su lenh chi cho thoi diem va chieu vao, khong cho gia truoc do.%s"
          % them)
    return _kq(KHONG_DO_DUOC, "thap", ly, {"khung_vao": kv}, ts, khoi={m: (KHONG_DO_DUOC, "thap", ly) for m in ten})


# ============================================================== 6. DIEU PHOI: ho_so()
#: khoi ma lich su lenh KHONG BAO GIO cho do duoc (`Khoi.kiem is None`) - ly do bang loi thuong. Day la "khong the biet", khong phai "khong co".
KHOI_CHUA_DO = {
    "vao_tay_roi_dca": "lich su khong ghi ai dat lenh dau (nguoi hay bot); chi tach duoc khi hai nhom lenh co ma magic / ghi chu khac nhau",
    "vao_chi_bao_ngoai": "tin hieu cua chi bao ngoai can duong gia truoc luc vao; lich su lenh chi cho gio va chieu (dieu_kien_vao chi do duoc khung nen)",
    "tp_treo_len": "viec dich TP khi them lenh nam trong lich su SUA lenh; deal chi ghi gia dong cuoi cung",
    "loc_spread": "lich su lenh khong ghi spread luc do; chi tester co ghi lai spread tung tick moi doi chieu duoc",
    "loc_tin_tuc": "can lich tin tuc theo gio de doi chieu; lich su lenh chi cho thay lenh nao mo luc nao",
    "loc_adx_atr": "ADX / ATR can duong gia truoc luc vao; deal khong co",
    "loc_sideway_nen": "nhan ra sideway can duong gia nen truoc luc vao; deal khong co",
    "loc_bao_bien_dong": "bao bien dong can duong gia trong vai phut truoc luc vao; deal khong co",
}


def _do_lot_sau_lo(c: Ctx) -> tuple:
    """Khoi `lot_nhan_sau_sl` (martingale don: lot lenh dau cua chuoi TANG sau mot chuoi LO, ve goc sau chuoi lai). Do tren chuoi lien tiep:
    chuoi i duoc xep theo ket qua chuoi DONG gan nhat truoc luc no mo. Can du chuoi sau lo (>= 8) va sau lai (>= 8) moi ket luan; khong co
    chuoi lo (bot nhu CanCuBo: 0 chuoi am) -> khong_do_duoc, khong phai 'khong co'. Tra (ket_luan, do_tin, ly_do, tham_so, so_lieu)."""
    ro = c.ro
    d = ro[ro["da_dong"].astype(bool) & np.isfinite(ro["tien"].to_numpy(float))]
    if len(d) < 20:
        return KHONG_DO_DUOC, "thap", "chi %d chuoi da dong (< 20)" % len(d), {}, {}
    t_mo = pd.to_datetime(ro["mo"]).to_numpy("datetime64[ns]").astype("int64") / 1e9
    d = d.assign(_dong=pd.to_datetime(d["dong"]).to_numpy("datetime64[ns]").astype("int64") / 1e9).sort_values("_dong", kind="stable")
    td = d["_dong"].to_numpy(float)
    lo_d = (d["tien"].to_numpy(float) < 0)
    lot_d = d["lot_dau"].to_numpy(float)
    j = np.searchsorted(td, t_mo, side="right") - 1
    ok = j >= 0
    lot_i = ro["lot_dau"].to_numpy(float)[ok]
    truoc_lo = lo_d[j[ok]]
    lot_truoc = lot_d[j[ok]]
    n_lo, n_lai = int(truoc_lo.sum()), int((~truoc_lo).sum())
    so_lieu = {"n_chuoi_sau_lo": n_lo, "n_chuoi_sau_lai": n_lai, "so_chuoi_lo": int(lo_d.sum())}
    if n_lo < 8 or n_lai < 8:
        ly = ("chi %d chuoi mo ngay sau mot chuoi LO (can >= 8, co %d chuoi lo trong %d): chua kiem duoc lot dau co tang sau lo hay khong"
              % (n_lo, int(lo_d.sum()), len(d)) if n_lo < 8 else
              "chi %d chuoi mo sau chuoi LAI (can >= 8)" % n_lai)
        return KHONG_DO_DUOC, "thap", ly, {}, so_lieu
    goc = float(np.median(lot_i[~truoc_lo]))
    r_lo, r_lai = lot_i[truoc_lo] / goc, lot_i[~truoc_lo] / goc
    ty_tang_lo = float((r_lo >= 1.3).mean())
    ty_goc_lai = float((np.abs(r_lai - 1.0) <= 0.05).mean())
    ty_dung_lo = float((np.abs(r_lo - 1.0) <= 0.05).mean())
    ty_ke = lot_i[truoc_lo] / np.where(lot_truoc[truoc_lo] > 0, lot_truoc[truoc_lo], np.nan)
    ty_ke = ty_ke[np.isfinite(ty_ke) & (lot_truoc[truoc_lo] > goc * 1.05)]
    so_lieu.update(lot_goc=_f(goc, 4), ty_tang_sau_lo=_f(ty_tang_lo, 3), ty_ve_goc_sau_lai=_f(ty_goc_lai, 3),
                   ty_khong_doi_sau_lo=_f(ty_dung_lo, 3), r_sau_lo_trung_vi=_f(np.median(r_lo), 3), r_sau_lo_max=_f(r_lo.max(), 2),
                   lot_dau_khac_nhau=int(len(set(np.round(lot_i, 4)))))
    dt = _do_tin(min(n_lo, n_lai), 30, 12)
    if float(np.median(r_lo)) >= 1.4 and ty_tang_lo >= 0.7 and ty_goc_lai >= 0.8:
        ts = {}
        if len(ty_ke) >= 5:
            ts["he_so_lot_sau_lo"] = _tham_so(_f(np.median(ty_ke), 3), "he_so", "lot_nhan_sau_sl",
                                              "lot dau chuoi nay / lot dau chuoi lo ngay truoc no (khi chuoi truoc da tang lot)")
        ts["lot_goc_sau_lai"] = _tham_so(_f(goc, 4), "lot", "lot_nhan_sau_sl", "lot dau chuoi khi chuoi truoc LAI")
        return (CO, dt, "lot dau tang sau chuoi lo (trung vi x%.2f, %.0f%% chuoi sau lo tang >= 1,3 lan) va ve goc %.0f%% sau chuoi lai: martingale don"
                % (float(np.median(r_lo)), 100 * ty_tang_lo, 100 * ty_goc_lai), ts, so_lieu)
    if ty_dung_lo >= 0.9:
        return (KHONG, dt, "lot dau chuoi khong doi sau chuoi lo (%.0f%% trong %d chuoi sau lo bang lot goc)" % (100 * ty_dung_lo, n_lo), {}, so_lieu)
    return (KHONG_RO, "thap", "lot dau co doi (%d gia tri) nhung khong theo kieu 'tang sau lo, ve goc sau lai' (tang sau lo %.0f%%, ve goc sau lai %.0f%%)"
            % (so_lieu["lot_dau_khac_nhau"], 100 * ty_tang_lo, 100 * ty_goc_lai), {}, so_lieu)


def _phep_lot_theo_bac(c: Ctx) -> dict:
    """Phep do `lot_theo_bac` day du 7 khoi: 6 khoi lot THEO BAC trong chuoi (`_do_lot_theo_bac`) + khoi lot THEO KET QUA chuoi truoc."""
    r = _do_lot_theo_bac(c)
    kl, dt, ly, ts, sl = _do_lot_sau_lo(c)
    r["khoi"]["lot_nhan_sau_sl"] = (kl, dt, ly)
    r["tham_so"].update(ts)
    r["so_lieu"]["lot_sau_lo"] = sl
    r["ket_luan"], r["do_tin"] = _top(r["khoi"]) if r["ket_luan"] == KHONG_DO_DUOC else (r["ket_luan"], r["do_tin"])
    return r


def _phep_doi_ung(c: Ctx) -> dict:
    return _do_doi_ung(c)[0]


#: moi TEN `kiem` cua danh muc khoi -> ham do (Ctx -> ket qua `_kq`). `ho_so()` chay doi_ung TRUOC (tren lich su goc) roi bo lenh bao hiem
#: khoi lich su cho cac phep do con lai: lenh bao hiem sao chep lot cua lenh chu, lam nhieu moi bang buoc / lot / thoat.
PHEP_DO = {
    "doi_ung": _phep_doi_ung,
    "huong": _do_huong,
    "vao_lai": _do_vao_lai,
    "dieu_kien_vao": _do_dieu_kien_vao,
    "them_khi_hoi": _do_them_khi_hoi,
    "nhip_them_lenh": _do_nhip_them_lenh,
    "buoc_theo_bac": _do_buoc,
    "lot_theo_bac": _phep_lot_theo_bac,
    "lot_theo_von": _do_lot_theo_von,
    "rui_ro": _do_rui_ro,
    "chuoi_sau": _do_chuoi_sau,
    "thoat": _do_thoat,
    "sl_tp_tung_lenh": _do_sl_tp_tung_lenh,
    "doi_tp": _do_doi_tp,
    "thoat_tung_phan": _do_thoat_tung_phan,
    "hoa_von": _do_hoa_von,
    "gio_ngay": _do_gio_ngay,
    "gong_duong": _do_gong_duong,
}


def kiem_dang_ky() -> list[str]:
    """Lech giua PHEP_DO / KHOI_CHUA_DO va danh muc `khoi_co_che` (them khoi ma quen them phep do -> bao ngay). `[]` = khop."""
    loi: list[str] = []
    ten_kiem = {k.kiem for k in KC.KHOI_DS if k.kiem}
    chua = {k.ma for k in KC.KHOI_DS if not k.kiem}
    loi += ["danh muc co phep do '%s' ma PHEP_DO khong co" % t for t in sorted(ten_kiem - set(PHEP_DO))]
    loi += ["PHEP_DO co '%s' ma khong khoi nao dung" % t for t in sorted(set(PHEP_DO) - ten_kiem)]
    loi += ["khoi '%s' chua co phep do ma KHOI_CHUA_DO khong giai thich" % m for m in sorted(chua - set(KHOI_CHUA_DO))]
    loi += ["KHOI_CHUA_DO co '%s' ma khoi nay da co phep do / khong co trong danh muc" % m for m in sorted(set(KHOI_CHUA_DO) - chua)]
    return loi


def _mo_ta_loi(e: BaseException) -> str:
    fr = traceback.extract_tb(e.__traceback__)
    cho = "%s:%d" % (Path(fr[-1].filename).name, fr[-1].lineno) if fr else "?"
    return "%s: %s (%s)" % (type(e).__name__, " ".join(str(e).split())[:160], cho)


def _chay_phep_do(kiem: str, ham, c: Ctx, loi: dict, giay: dict) -> dict:
    """Chay MOT phep do; ngoai le KHONG duoc nuot im: thanh `khong_do_duoc` + ghi vao `loi` (de len `tong_ket.phep_do_loi`)."""
    t0 = time.time()
    try:
        r = ham(c)
        if not (isinstance(r, dict) and r.get("ket_luan") in KET_LUAN and isinstance(r.get("khoi"), dict)):
            raise TypeError("phep do tra ket qua sai dang (%s)" % type(r).__name__)
    except Exception as e:
        loi[kiem] = _mo_ta_loi(e)
        r = _khong_do_duoc(kiem, "phep do bi LOI (khong co nghia la bot khong co co che nay): %s" % loi[kiem])
    giay[kiem] = round(time.time() - t0, 2)
    return r


def _cat(s, n: int = 170) -> str:
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "..."


def _gt(ts: dict, ten: str):
    d = ts.get(ten)
    return d.get("gia_tri") if isinstance(d, dict) else None


def _van_tay(c: Ctx, phep: dict, ts: dict) -> dict:
    """Dau van tay tinh cach (muc 6.3 cua tai_lieu/CHUYEN_BOT_SANG_TAI_SAN_KHAC.md), chi do tu lich su lenh. Don vi pip la CUA TAI SAN NAY:
    khi so sanh giua hai tai san phai chia cho bien do nen A (do tren may nha, can duong gia). Moi nhom co the rong (None) khi lich su khong cho do."""
    o, ro = c.lenh, c.ro
    vt: dict = {"ma": c.ma, "pip": c.pip}
    ngay = max(1.0, (o["mo"].max() - o["mo"].min()).total_seconds() / 86400.0)
    vt["nhip"] = {"so_ngay": _f(ngay, 1), "chuoi_moi_ngay": _f(len(ro) / ngay, 3), "lenh_moi_ngay": _f(len(o) / ngay, 3),
                  "khung_tin_hieu_phut": _gt(ts, "khung_tin_hieu_phut")}
    ty_mua = float((ro["chieu"] == 1).mean())
    ca_hai = c.thoi_gian["ca_hai"] / c.thoi_gian["co_lenh"] if c.thoi_gian.get("co_lenh") else None
    vt["huong"] = {"ty_mua": _f(ty_mua, 3), "kieu": "chi_mua" if ty_mua >= 0.99 else "chi_ban" if ty_mua <= 0.01 else "hai_chieu",
                   "ty_thoi_gian_ca_hai_chieu": _f(ca_hai, 4)}
    sl = ro["so_lenh"].to_numpy(int)
    vt["chuoi_sau"] = {"trung_vi": _f(np.median(sl), 1), "p90": _f(_q(sl, 90), 1), "max": int(sl.max())}
    nhieu = ro[ro["so_lenh"] >= 2].copy()
    nhieu["gia_cuoi"] = nhieu["ro"].map(o.groupby("ro")["gia_mo"].last())   # gia mo cua lenh them SAU CUNG (o da xep theo gio mo)
    if len(nhieu) >= 5:
        dsau = np.abs(nhieu["gia_cuoi"].to_numpy(float) - nhieu["gia_dau"].to_numpy(float)) / c.pip
        vt["do_sau_pip"] = {"n": int(len(nhieu)), "trung_vi": _f(np.median(dsau), 1), "p90": _f(_q(dsau, 90), 1), "max": _f(dsau.max(), 1)}
    else:
        vt["do_sau_pip"] = None
    dong = ro[ro["da_dong"].astype(bool)]
    if len(dong) >= 5:
        gio = (pd.to_datetime(dong["dong"]) - pd.to_datetime(dong["mo"])).dt.total_seconds().to_numpy(float) / 3600.0
        vt["giu_gio"] = {"n": int(len(dong)), "trung_vi": _f(np.median(gio), 2), "p90": _f(_q(gio, 90), 2)}
        tien = dong["tien"].to_numpy(float)
        tien = tien[np.isfinite(tien)]
        lai, lo = tien[tien > 0], -tien[tien < 0]
        vt["lai_lo"] = {"ty_chuoi_lai": _f(float((tien > 0).mean()), 3), "lai_tb": _f(lai.mean() if len(lai) else None, 2),
                        "lo_tb": _f(lo.mean() if len(lo) else None, 2),
                        "ty_lai_lo": _f(lai.mean() / lo.mean(), 3) if len(lai) and len(lo) else None, "so_chuoi_lo": int(len(lo))}
    else:
        vt["giu_gio"] = None
        vt["lai_lo"] = None
    tong_lenh = max(int(ro["so_lenh"].sum()), 1)
    vt["ty_le_ly_ra"] = {k: _f(int(ro[col].sum()) / tong_lenh, 3) for k, col in (("tp", "ly_tp"), ("sl", "ly_sl"), ("stopout", "ly_so"), ("ea", "ly_ea"))}
    buoc = phep["buoc_theo_bac"]["so_lieu"].get("doan_buoc")
    vt["buoc_pip"] = ({"doan": buoc, "dan_ty_le": _f(buoc[-1]["pip"] / buoc[0]["pip"], 3) if buoc[0]["pip"] else None}
                      if buoc else None)
    vt["buoc_trung_vi_pip"] = phep["them_khi_hoi"]["so_lieu"].get("buoc_trung_vi_pip")
    tl = []
    for b in range(1, 31):
        m = (o["bac"] == b).to_numpy()
        if int(m.sum()) < 5:
            continue
        r = (o.loc[m, "lot_vao"] / o.loc[m, "lot_dau"]).to_numpy(float)
        tl.append({"bac": b, "n": int(m.sum()), "ty_lot": _f(np.median(r), 3)})
    vt["tien_trinh_lot"] = tl
    vt["lot_dinh_max"] = _f(ro["lot_dinh"].max(), 2)
    vt["rui_ro_von_pct"] = None
    if c.hop_dong and len(nhieu) >= 5:
        lo_noi = (nhieu["lot_tong"].to_numpy(float) * np.abs(nhieu["gia_cuoi"].to_numpy(float) - nhieu["gia_tb"].to_numpy(float))
                  * float(c.hop_dong))
        von = nhieu["bal_dau"].to_numpy(float)
        ok = np.isfinite(lo_noi) & np.isfinite(von) & (von > 0)
        if ok.sum() >= 5:
            pc = 100.0 * lo_noi[ok] / von[ok]
            vt["rui_ro_von_pct"] = {"trung_vi": _f(np.median(pc), 2), "p90": _f(_q(pc, 90), 2), "max": _f(pc.max(), 2),
                                    "ghi_chu": "lo noi o lenh them CUOI cua chuoi / so du luc bat dau chuoi (khong tinh spread, swap)"}
    return vt


def ho_so(v, ma: str | None = None, pip: float | None = None, hop_dong: float | None = None, von_dau: float | None = None,
          khung_phut: float | None = None, ten: str | None = None) -> dict:
    """HO SO CO CHE day du cua mot bot tu lich su lenh: chay MOI phep do, tra ve JSON thuan (khong DataFrame / numpy).

    `v` = duong dan tep bao cao tester (.htm / .csv / .csv.gz), bang vi the, bang lenh chuan hoa, hoac `Ctx`. Thu tu: doi ung do tren lich
    su GOC -> bo lenh bao hiem -> moi phep do con lai tren lich su da bo. Khoa tra ve: `mau`, `phep_do` (tung phep do + so lieu + bang),
    `khoi` (du 52 khoi cua danh muc: co / khong / khong_ro / khong_do_duoc + do_tin + ly do), `tham_so` (moi so do duoc, kem don vi + khoi,
    de `ho_so_set.khop_knob` doi voi .set), `van_tay`, `tong_ket` (co ca `phep_do_loi`, `khoi_thieu`, `khoi_la` - ba cai phai rong),
    `canh_bao`, `bao_cao` (3-8 dong loi thuong)."""
    t0 = time.time()
    c = v if isinstance(v, Ctx) else chuan_bi(v, ma=ma, pip=pip, hop_dong=hop_dong, von_dau=von_dau, khung_phut=khung_phut)
    canh_bao = list(c.canh_bao)
    loi: dict[str, str] = {}
    giay: dict[str, float] = {}
    phep: dict[str, dict] = {}
    mask = None
    t1 = time.time()
    try:
        phep["doi_ung"], mask = _do_doi_ung(c)
    except Exception as e:
        loi["doi_ung"] = _mo_ta_loi(e)
        phep["doi_ung"] = _khong_do_duoc("doi_ung", "phep do bi LOI (khong co nghia la bot khong co lenh doi ung): %s" % loi["doi_ung"])
    giay["doi_ung"] = round(time.time() - t1, 2)
    c.doi_ung = phep["doi_ung"]
    n_bo = int(mask.sum()) if mask is not None else 0
    c2 = c
    if n_bo:
        try:
            c2 = c.loc(~mask)
        except Exception as e:
            canh_bao.append("khong bo duoc %d lenh doi ung khoi lich su (%s): cac phep do khac chay tren lich su CO lenh bao hiem" % (n_bo, _mo_ta_loi(e)))
            n_bo = 0
    for kiem, ham in PHEP_DO.items():
        if kiem != "doi_ung":
            phep[kiem] = _chay_phep_do(kiem, ham, c2, loi, giay)
    if c.tick_s >= 5.0:
        canh_bao.append("lich su co luoi tick %.0f giay (bao cao tester Model 0/1): moi bang chung o muc GIAY la do bo mo phong, khong phai nhip that "
                        "cua EA" % c.tick_s)
    for kiem in loi:
        canh_bao.append("phep do %s bi loi -> khong_do_duoc (khong phai 'khong co'): %s" % (kiem, loi[kiem]))
    # --- khoi: du 52 khoi, ke ca khoi khong co phep do
    khoi: dict[str, dict] = {}
    khoi_thieu: list[str] = []
    for k in KC.KHOI_DS:
        if not k.kiem:
            khoi[k.ma] = {"nhom": k.nhom, "ten": k.ten, "phep_do": None, "ket_luan": KHONG_DO_DUOC, "do_tin": "thap",
                          "ly_do": KHOI_CHUA_DO.get(k.ma, "chua co phep do")}
            continue
        e = phep[k.kiem]["khoi"].get(k.ma)
        if e is None:
            khoi_thieu.append(k.ma)
            e = (KHONG_DO_DUOC, "thap", "phep do %s khong tra ket qua cho khoi nay (loi dang ky phep do)" % k.kiem)
        khoi[k.ma] = {"nhom": k.nhom, "ten": k.ten, "phep_do": k.kiem, "ket_luan": e[0], "do_tin": e[1], "ly_do": e[2]}
    khoi_la = sorted("%s/%s" % (kiem, m) for kiem, r in phep.items() for m in r["khoi"] if m not in khoi or khoi[m]["phep_do"] != kiem)
    # --- tham so phang
    ts: dict[str, dict] = {}
    for kiem, r in phep.items():
        for ten_ts, d in r["tham_so"].items():
            if ten_ts in ts:
                canh_bao.append("tham so '%s' do hai lan (%s va %s): giu ban dau" % (ten_ts, ts[ten_ts]["phep_do"], kiem))
                continue
            ts[ten_ts] = {**d, "phep_do": kiem}
    try:
        vt = _van_tay(c2, phep, ts)
    except Exception as e:
        vt = None
        canh_bao.append("van tay bi loi: %s" % _mo_ta_loi(e))
    mau = {"ma": c.ma, "pip": c.pip, "hop_dong": _f(c.hop_dong, 2), "von_dau": _f(c.von_dau, 2), "tick_s": _f(c.tick_s, 1),
           "so_lenh_goc": int(len(c.lenh)), "so_lenh_doi_ung_bo": n_bo, "so_lenh": int(len(c2.lenh)), "so_chuoi": int(len(c2.ro)),
           "tu": str(c.lenh["mo"].min())[:10], "den": str(c.lenh["mo"].max())[:10],
           "chat_luong": {k: c.chat_luong.get(k) for k in ("trang_thai", "dang_tin_ghep", "co_order", "co_ly_do_ra", "ngay")}}
    hs = {"phien_ban": PHIEN_BAN, "ten": ten, "mau": mau,
          "phep_do": {kiem: {"ket_luan": r["ket_luan"], "do_tin": r["do_tin"], "ly_do": r["ly_do"], "so_lieu": r["so_lieu"],
                             "tham_so": r["tham_so"], "bang": r["bang"], "giay": giay.get(kiem)} for kiem, r in phep.items()},
          "khoi": khoi, "tham_so": ts, "van_tay": vt,
          "tong_ket": {**{kl: {m: v_["do_tin"] for m, v_ in khoi.items() if v_["ket_luan"] == kl} for kl in KET_LUAN},
                       "so_khoi": len(khoi), "phep_do_loi": loi, "khoi_thieu": khoi_thieu, "khoi_la": khoi_la,
                       "giay": round(time.time() - t0, 1)},
          "canh_bao": canh_bao}
    hs = _json(hs)
    hs["bao_cao"] = tom_tat_thuong(hs)
    return hs


_NHOM_DONG = (("Vao lenh va loc", ("VAO", "LOC")), ("Them lenh, luoi, lot", ("TANG", "LOT")), ("Thoat va bao ve", ("THOAT", "BAO_VE")))


def tom_tat_thuong(hs: dict) -> list[str]:
    """3-8 dong loi thuong (ASCII) cho chu du an: bot nay lam gi, cai gi KHONG thay, cai gi lich su nay khong cho biet."""
    m = hs["mau"]
    dong = ["Mau: %d lenh %s thanh %d chuoi, %s den %s (do tin ghep lenh: %s)." % (
        m["so_lenh"], m["ma"], m["so_chuoi"], m["tu"], m["den"], (m["chat_luong"] or {}).get("dang_tin_ghep"))]
    if m["so_lenh_doi_ung_bo"]:
        dong[0] += " Da tach %d lenh bao hiem (hedge) ra khoi so lieu." % m["so_lenh_doi_ung_bo"]
    co = {}
    for ma, v in hs["khoi"].items():
        if v["ket_luan"] == CO:
            co.setdefault(v["nhom"], []).append("%s [%s]: %s" % (v["ten"], v["do_tin"], _cat(v["ly_do"], 110)))
    for ten_dong, nhom in _NHOM_DONG:
        mot = [x for n in nhom for x in co.get(n, [])]
        if mot:
            dong.append("%s - %s" % (ten_dong, " | ".join(mot)))
    khong = ["%s" % v["ten"] for v in hs["khoi"].values() if v["ket_luan"] == KHONG and v["do_tin"] in ("cao", "vua")]
    ro = ["%s" % v["ten"] for v in hs["khoi"].values() if v["ket_luan"] == KHONG_RO]
    if khong or ro:
        dong.append("Khong thay (da do, co tiep xuc): %s. Chua ket luan duoc: %s." % (
            ", ".join(khong[:8]) + ("..." if len(khong) > 8 else "") if khong else "-",
            ", ".join(ro[:6]) + ("..." if len(ro) > 6 else "") if ro else "-"))
    kdd = [v["ten"] for v in hs["khoi"].values() if v["ket_luan"] == KHONG_DO_DUOC]
    tail = "Lich su lenh khong cho do %d khoi (can duong gia / .set / ma nguon): %s." % (len(kdd), ", ".join(kdd[:6]) + ("..." if len(kdd) > 6 else ""))
    if hs["canh_bao"]:
        tail += " Canh bao: %s" % _cat(hs["canh_bao"][0], 160)
    dong.append(tail)
    return dong[:8]


def gon(hs: dict) -> dict:
    """Ban gon (~1 KB) de in / de nho: ket luan khoi (tru khong_do_duoc) + moi tham so do duoc."""
    return {"mau": {k: hs["mau"][k] for k in ("ma", "so_lenh", "so_chuoi", "tu", "den")},
            "khoi": {ma: "%s/%s" % (v["ket_luan"], v["do_tin"]) for ma, v in hs["khoi"].items() if v["ket_luan"] != KHONG_DO_DUOC},
            "tham_so": {k: v["gia_tri"] for k, v in hs["tham_so"].items()},
            "khong_do_duoc": sum(1 for v in hs["khoi"].values() if v["ket_luan"] == KHONG_DO_DUOC),
            "loi": hs["tong_ket"]["phep_do_loi"], "canh_bao": len(hs["canh_bao"])}


def main(argv: list[str] | None = None) -> int:
    """`python -m nhan.ho_so_bot <tep> [--ma MA] [--json TEP] [--gon]`: in ban tom tat loi thuong; `--json` luu ho so day du."""
    import argparse
    ap = argparse.ArgumentParser(prog="ho_so_bot", description="ho so co che bot tu lich su lenh")
    ap.add_argument("tep")
    ap.add_argument("--ma")
    ap.add_argument("--json", help="luu ho so day du ra tep JSON (UTF-8)")
    ap.add_argument("--gon", action="store_true", help="in ban gon thay vi tom tat")
    a = ap.parse_args(argv)
    hs = ho_so(a.tep, ma=a.ma)
    if a.json:
        Path(a.json).write_text(json.dumps(hs, ensure_ascii=True, indent=1), encoding="utf-8")
    print(json.dumps(gon(hs), ensure_ascii=True, indent=1) if a.gon else "\n".join(hs["bao_cao"]))
    return 1 if (hs["tong_ket"]["phep_do_loi"] or hs["tong_ket"]["khoi_thieu"] or hs["tong_ket"]["khoi_la"]) else 0


if __name__ == "__main__":
    sys.exit(main())
