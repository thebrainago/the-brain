# -*- coding: utf-8 -*-
"""nc_mo_xe.py - MO XE LENH va TIM QUY LUAT: hoc luat vao lenh tu lenh dung/lenh sai, co null hieu chuan.

## CAU HOI CUA CHU DU AN (25/09/2026)

*"Tai sao co nhieu AI tu trade tu hoc hoi tu lenh dung lenh sai ma con ra duoc
quy tac vao lenh, ma chung ta co san mot bo cong cu cuc manh chi di tim kiem
nhung thu san co?"*

Tra loi bang do dac: truoc file nay, The Brain KHONG CO khau nao nhin vao tung
lenh. Engine tra ve danh sach lenh (`dap_quan_tri.dap` -> `lenh`), cong tra ve
PASS/FAIL, va tru NGHI chi doc lai **dem PASS/FAIL theo ho**. Khong ai hoi:
*lenh thang khac lenh thua o dau luc vao lenh?* Tuc vong hoc bi dut dung cho
nhung "AI tu hoc" kia co.

## HAI CONG CU

`mo_xe_lenh`  Cho mot he da chay: tach lenh, lay NGU CANH tai bar tin hieu
              (`nc_dac_trung`), tim DIEU KIEN tach lenh thang khoi lenh thua ->
              bo loc de xuat (dieu kien DSL, them vao `vao` la chay duoc ngay).
              Kem phan tich MFE/MAE -> goi y luat QUAN TRI (SL/TP/hue/trailing/
              thoat theo bar) cho `dap_quan_tri`.
`tim_quy_luat` Khong can he nao: nhan moi bar la mot "lenh tiem nang" giu h bar,
              tim dieu kien lam loi suat h bar toi LECH khoi 0 sau chi phi. Day
              la "noi sinh" cua so do: tu chinh lich su cua ma, khong doi tai lieu.

## VI SAO PHAI CO NULL - va null nao

Do 26 dac trung x 13 nguong x 2 chieu x 4 chan troi + ghep doi la ~3.000 phep
thu trong MOT lan goi. Cuc dai cua 3.000 phep thu tren nhieu trang luon "dep".
Nen diem cua luat tot nhat duoc so voi PHAN PHOI CUC DAI cua CHINH QUY TRINH DO
chay lai tren nhan da bi pha lien ket:

- bar: XOAY VONG chuoi loi suat so voi dac trung (giu tu tuong quan va cum bien
  dong cua ca hai - dung null da dung trong `suy_nguoc`: "null phai giu CUM").
- lenh: xoay vong khi du lenh (>= 80), hoan vi khi it.

`p_null` cua moi luat = ti le lan null co cuc dai >= diem luat do. Da tinh ca
viec DO TIM tren moi dac trung/nguong/chan troi, nen khong can Bonferroni them.
Day la NHAN CANH BAO theo LUAT SO 0, khong phai cong chan - nhung la nhan quan
trong nhat: luat co p_null 0,40 thi 40% cac chuoi ngau nhien cung "tim ra" luat
dep bang no.

## CAI KHONG DUOC LAM VOI KET QUA O DAY

Loc lenh HAU KIEM tren chinh doan kham pha luon dep hon that (chon tren chinh
du lieu do). Mot bo loc chi co gia tri khi CHAY LAI he co them dieu kien do
tren doan `xac_nhan` - viec cua `nc_thi_nghiem.danh_gia`. Ket qua o day la DE
XUAT gia thuyet, khong phai ket luan.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import nc_dac_trung as DT
else:
    from . import nc_dac_trung as DT

#: Muc phan vi dat nguong. Duoi day nhieu (0,05-0,2) vi dieu kien "hiem" (IBS
#: rat thap, cu soc lon) la noi co che quay ve song - bo mat duoi la bo mat edge.
MUC_Q = (0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95)
ROI_RAC_TOI_DA = 24          # dac trung <= 24 gia tri nguyen -> them dieu kien "=="
TOP_GHEP = 6                 # so luat don dung de ghep doi
LENH_TOI_THIEU = 30


def _lam_tron(x: float, so_chu_so: int = 4) -> float:
    if not np.isfinite(x) or x == 0:
        return float(x)
    return float(round(x, so_chu_so - 1 - int(math.floor(math.log10(abs(x))))))


# ============================================================ KHONG GIAN
class _KhongGian:
    """Moi dieu kien don (dac trung, phep, nguong) va phep cong don nhanh tren chung.

    Tach khoi thong ke de null chay DUNG quy trinh tim kiem nhu that - chi doi Y.
    """

    def __init__(self, X: np.ndarray, ten: list[str]):
        self.N = X.shape[0]
        self.ten = list(ten)
        self.khoi: list[dict] = []
        self.dk: list[tuple] = []           # (i_dac_trung, phep, nguong)
        for f in range(X.shape[1]):
            x = X[:, f]
            v = np.flatnonzero(np.isfinite(x))
            if len(v) < LENH_TOI_THIEU:
                continue
            xv = x[v]
            o = np.argsort(xv, kind="mergesort")
            xs = xv[o]
            uniq = np.unique(xs)
            roi_rac = len(uniq) <= ROI_RAC_TOI_DA and np.allclose(uniq, np.round(uniq))
            nguong = sorted({_lam_tron(float(q)) for q in np.quantile(xs, MUC_Q)})
            nguong = [t for t in nguong if xs[0] < t <= xs[-1]]
            k = np.searchsorted(xs, nguong, side="left")
            b = {"f": f, "v": v, "o": o, "nv": len(v), "k": k, "d0": len(self.dk)}
            for t in nguong:
                self.dk.append((f, "<", t))
            for t in nguong:
                self.dk.append((f, ">=", t))
            b["d_bang"] = None
            if roi_rac and len(uniq) > 2:
                b["ma"] = np.searchsorted(uniq, xv)
                b["uniq"] = uniq
                b["d_bang"] = len(self.dk)
                for u in uniq:
                    self.dk.append((f, "==", float(u)))
            self.khoi.append(b)
        self.D = len(self.dk)

    def tong(self, Y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Y (N x C) -> (so phan tu n[D], tong S[D x C]) cua moi dieu kien don."""
        C = Y.shape[1]
        n = np.zeros(self.D)
        S = np.zeros((self.D, C))
        for b in self.khoi:
            Yv = Y[b["v"]]
            Ys = Yv[b["o"]]
            cs = np.vstack([np.zeros((1, C)), np.cumsum(Ys, axis=0)])
            k = b["k"]
            m = len(k)
            d0 = b["d0"]
            n[d0:d0 + m] = k
            S[d0:d0 + m] = cs[k]
            n[d0 + m:d0 + 2 * m] = b["nv"] - k
            S[d0 + m:d0 + 2 * m] = cs[-1] - cs[k]
            if b["d_bang"] is not None:
                u = len(b["uniq"])
                dd = b["d_bang"]
                n[dd:dd + u] = np.bincount(b["ma"], minlength=u)
                for c in range(C):
                    S[dd:dd + u, c] = np.bincount(b["ma"], weights=Yv[:, c], minlength=u)
        return n, S

    def mat_na(self, X: np.ndarray, d: int) -> np.ndarray:
        f, phep, t = self.dk[d]
        x = X[:, f]
        with np.errstate(invalid="ignore"):
            if phep == "<":
                m = x < t
            elif phep == ">=":
                m = x >= t
            else:
                m = x == t
        return m & np.isfinite(x)

    def mo_ta(self, d: int) -> str:
        f, phep, t = self.dk[d]
        return "%s %s %s" % (self.ten[f], phep, _lam_tron(t))

    def dsl(self, d: int) -> dict | None:
        """Dieu kien DSL; None neu cot khong phai dac trung cua `nc_dac_trung` (vd bang tu dung)."""
        f, phep, t = self.dk[d]
        if self.ten[f] not in DT.DAC_TRUNG:
            return None
        return DT.dieu_kien(self.ten[f], phep, t)


# ================================================================ TACH LENH
def _atr_mang(df: pd.DataFrame, n: int = 14) -> np.ndarray:
    h, l, c = (df[k].to_numpy(float) for k in ("high", "low", "close"))
    cp = np.concatenate(([c[0]], c[:-1]))
    tr = np.maximum(h - l, np.maximum(np.abs(h - cp), np.abs(l - cp)))
    return pd.Series(tr).ewm(alpha=1.0 / n, adjust=False).mean().to_numpy()


def tach_lenh(df: pd.DataFrame, vi_the, loi_tho, loi, lenh_dap: list | None = None
              ) -> pd.DataFrame:
    """Danh sach lenh RONG PHI tu mot lan chay engine tren `df`.

    Hai nguon:
      - `lenh_dap` (tu `dap_quan_tri.dap`): lenh co bar vao/ra chinh xac, ke ca
        bar thoat giua chung o gia SL/TP (bar do `vi_the` = 0 nhung van co lai lo).
      - `vi_the` (tu `mo_phong.chay`): mot lenh = mot doan lien tuc cung dau.
        Phi thoat tinh o bar SAU doan (engine tru phi o bar vi the doi), nen
        phai cong vao dung lenh - bo qua thi moi lenh dep hon that mot spread.

    Cot: vao, ra, tin_hieu (bar biet tin hieu = vao-1), chieu, loi (log, rong),
    loi_tho, so_bar, mfe/mae (ti le, mfe >= 0 >= mae), mfe_atr/mae_atr (theo
    ATR tai bar tin hieu), bar_mfe, luc_vao.
    """
    v = np.nan_to_num(np.asarray(vi_the, float))
    lt = np.nan_to_num(np.asarray(loi_tho, float))
    lr = np.nan_to_num(np.asarray(loi, float))
    phi = lt - lr
    n = len(v)
    o = df["open"].to_numpy(float)
    h = df["high"].to_numpy(float)
    lo = df["low"].to_numpy(float)
    atr = _atr_mang(df)
    doan: list[tuple[int, int, int, float, float]] = []
    if lenh_dap is not None:
        for x in lenh_dap:
            i, j = int(x["vao"]), int(x["ra"])
            if i <= 0 or i >= n:
                continue
            j = min(max(j, i), n - 1)
            doan.append((i, j, int(x["chieu"]), float(np.sum(lr[i:j + 1])),
                         float(np.sum(lt[i:j + 1]))))
    else:
        i = 0
        while i < n:
            if abs(v[i]) < 1e-12:
                i += 1
                continue
            dau = np.sign(v[i])
            j = i
            while j + 1 < n and abs(v[j + 1]) > 1e-12 and np.sign(v[j + 1]) == dau:
                j += 1
            if i == 0:          # khong co bar tin hieu truoc do -> bo
                i = j + 1
                continue
            vao_chia = 1.0
            if abs(v[i - 1]) > 1e-12:          # lat chieu: phi cua bar i la hai chan
                vao_chia = abs(v[i]) / (abs(v[i]) + abs(v[i - 1]))
            phi_ra = 0.0
            if j + 1 < n:
                phi_ra = phi[j + 1]
                if abs(v[j + 1]) > 1e-12:
                    phi_ra *= abs(v[j]) / (abs(v[j]) + abs(v[j + 1]))
            rong = (float(np.sum(lt[i:j + 1])) - phi[i] * vao_chia
                    - float(np.sum(phi[i + 1:j + 1])) - phi_ra)
            doan.append((i, j, int(dau), rong, float(np.sum(lt[i:j + 1]))))
            i = j + 1
    ra = []
    for i, j, dau, rong, tho in doan:
        g = o[i]
        cao, thap = float(np.max(h[i:j + 1])), float(np.min(lo[i:j + 1]))
        if dau > 0:
            mfe, mae = cao / g - 1.0, thap / g - 1.0
            bar_mfe = int(np.argmax(h[i:j + 1]))
        else:
            mfe, mae = 1.0 - thap / g, 1.0 - cao / g
            bar_mfe = int(np.argmin(lo[i:j + 1]))
        a = atr[i - 1] / g if atr[i - 1] > 0 else np.nan
        ra.append({"vao": i, "ra": j, "tin_hieu": i - 1, "chieu": dau,
                   "loi": rong, "loi_tho": tho, "so_bar": j - i + 1,
                   "mfe": mfe, "mae": mae,
                   "mfe_atr": mfe / a if a and np.isfinite(a) else np.nan,
                   "mae_atr": mae / a if a and np.isfinite(a) else np.nan,
                   "bar_mfe": bar_mfe, "luc_vao": df.index[i]})
    return pd.DataFrame(ra)


def thong_ke_lenh(loi: np.ndarray) -> dict:
    """So lenh, ti le thang, TB thang/thua (bps), ky vong, t theo lenh."""
    y = np.asarray(loi, float)
    y = y[np.isfinite(y)]
    n = len(y)
    if n == 0:
        return {"so_lenh": 0}
    thang, thua = y[y > 0], y[y <= 0]
    sd = float(np.std(y, ddof=1)) if n > 1 else float("nan")
    return {
        "so_lenh": n,
        "ty_le_thang": round(float(len(thang) / n), 3),
        "tb_thang_bps": round(float(np.mean(thang)) * 1e4, 2) if len(thang) else None,
        "tb_thua_bps": round(float(np.mean(thua)) * 1e4, 2) if len(thua) else None,
        "ky_vong_bps": round(float(np.mean(y)) * 1e4, 2),
        "t_lenh": round(float(np.mean(y) / sd * np.sqrt(n)), 2) if sd and sd > 0 else None,
        "rr": round(float(np.mean(thang) / abs(np.mean(thua))), 3)
        if len(thang) and len(thua) and np.mean(thua) < 0 else None,
    }


# ============================================================= TIM LUAT
def _t(n, s1, s2):
    """t = TB / sd * sqrt(n), vector hoa; NaN khi n < 3."""
    with np.errstate(invalid="ignore", divide="ignore"):
        tb = s1 / n
        var = (s2 - s1 * s1 / n) / (n - 1)
        t = tb / np.sqrt(var) * np.sqrt(n)
    t[(n < 3) | ~np.isfinite(t)] = np.nan
    return t


def _quet_lenh(kg: _KhongGian, X: np.ndarray, y: np.ndarray, n_min: float,
               bo_min: float, top: int = TOP_GHEP) -> list[tuple]:
    """Mot luot tim bo loc tren lenh. -> [(diem, [d...], n, s1, s2)] giam dan."""
    Y = np.column_stack([y, y * y])
    n, S = kg.tong(Y)
    N = len(y)
    hop = (n >= n_min) & ((N - n) >= bo_min)
    t = _t(n, S[:, 0], S[:, 1])
    t[~hop] = np.nan
    ds: list[tuple] = []
    thu_tu = np.argsort(-np.nan_to_num(t, nan=-np.inf))
    da_f = set()
    don = []
    for d in thu_tu:
        if not np.isfinite(t[d]):
            break
        ds.append((float(t[d]), [int(d)], float(n[d]), float(S[d, 0]), float(S[d, 1])))
        f = kg.dk[d][0]
        if f not in da_f and len(don) < top:
            da_f.add(f)
            don.append(int(d))
    for a in range(len(don)):
        ma = kg.mat_na(X, don[a])
        for b in range(a + 1, len(don)):
            m = ma & kg.mat_na(X, don[b])
            nn = float(m.sum())
            if nn < n_min or (N - nn) < bo_min:
                continue
            s1, s2 = float(y[m].sum()), float((y[m] ** 2).sum())
            tt = _t(np.array([nn]), np.array([s1]), np.array([s2]))[0]
            if np.isfinite(tt):
                ds.append((float(tt), [don[a], don[b]], nn, s1, s2))
    ds.sort(key=lambda z: -z[0])
    return ds


def _null(y: np.ndarray, so: int, rng: np.random.Generator, kieu: str):
    N = len(y)
    for _ in range(so):
        if kieu == "xoay":
            k = int(rng.integers(max(1, N // 10), max(2, N - N // 10)))
            yield np.roll(y, k)
        else:
            yield rng.permutation(y)


def mo_xe_lenh(lenh: pd.DataFrame, X_tin_hieu: pd.DataFrame, so_null: int = 200,
               hat: int = 0, giu_toi_thieu: float = 0.25, so_luat: int = 6) -> dict:
    """Tim DIEU KIEN tach lenh thang khoi lenh thua. Xem docstring dau file.

    `lenh`: tu `tach_lenh`. `X_tin_hieu`: dac trung tai bar TIN HIEU cua tung
    lenh (cung thu tu). Tra ve bo loc de xuat + null + phan tich thoat.
    """
    y = lenh["loi"].to_numpy(float) if len(lenh) else np.zeros(0)
    tk = thong_ke_lenh(y)
    ra: dict = {"tong_quan": tk, "luat_loc": [], "thoat": {}, "canh_bao": []}
    if len(y) < LENH_TOI_THIEU:
        ra["trang_thai"] = "CHUA_DO_DUOC"
        ra["canh_bao"].append("chi %d lenh < %d - khong du de mo xe" % (len(y), LENH_TOI_THIEU))
        return ra
    X = X_tin_hieu.to_numpy(float)
    kg = _KhongGian(X, list(X_tin_hieu.columns))
    N = len(y)
    n_min = max(20.0, giu_toi_thieu * N)
    bo_min = max(5.0, 0.05 * N)
    that = _quet_lenh(kg, X, y, n_min, bo_min)
    kieu = "xoay" if N >= 80 else "hoan_vi"
    rng = np.random.default_rng(20260925 + hat)
    cuc_dai = np.array([(_quet_lenh(kg, X, yb, n_min, bo_min)[:1] or [(np.nan,)])[0][0]
                        for yb in _null(y, so_null, rng, kieu)], float)
    cuc_dai = cuc_dai[np.isfinite(cuc_dai)]
    t_goc = tk.get("t_lenh")
    ra["null"] = {"kieu": kieu, "so": int(len(cuc_dai)),
                  "cuc_dai_trung_vi": round(float(np.median(cuc_dai)), 2) if len(cuc_dai) else None,
                  "cuc_dai_p95": round(float(np.quantile(cuc_dai, 0.95)), 2) if len(cuc_dai) else None,
                  "y_nghia": "diem t tot nhat ma CHINH quy trinh nay tim ra khi lien ket "
                             "dac trung-ket qua da bi pha. Luat that phai vuot xa muc nay."}
    da_thay = set()
    for diem, dk, n, s1, s2 in that:
        khoa = tuple(sorted(dk))
        if khoa in da_thay:
            continue
        da_thay.add(khoa)
        m = np.ones(N, bool)
        for d in dk:
            m &= kg.mat_na(X, d)
        tk_giu = thong_ke_lenh(y[m])
        tk_bo = thong_ke_lenh(y[~m])
        p = (1 + int(np.sum(cuc_dai >= diem))) / (1 + len(cuc_dai)) if len(cuc_dai) else None
        ra["luat_loc"].append({
            "dieu_kien": " VA ".join(kg.mo_ta(d) for d in dk),
            "dsl": [kg.dsl(d) for d in dk],
            "giu_lai": round(float(m.mean()), 3),
            "t_goc": t_goc, "t_sau_loc": round(diem, 2),
            "p_null": round(float(p), 4) if p is not None else None,
            "giu": tk_giu, "bo_di": tk_bo,
        })
        if len(ra["luat_loc"]) >= so_luat:
            break
    ra["dac_trung_manh"] = _xep_dac_trung(X_tin_hieu, y)
    ra["thoat"] = phan_tich_thoat(lenh)
    tot = ra["luat_loc"][0] if ra["luat_loc"] else None
    if tot is None:
        ra["trang_thai"] = "AM"
        ra["canh_bao"].append("khong co dieu kien nao giu du lenh ma tach duoc")
    elif tot["p_null"] is not None and tot["p_null"] <= 0.05:
        ra["trang_thai"] = "DAT"
    else:
        ra["trang_thai"] = "AM"
        ra["canh_bao"].append(
            "bo loc tot nhat co p_null %.2f: nhieu trang cung cho ra bo loc dep nhu vay. "
            "Dung tin - hoac chi thu nhu mot gia thuyet yeu tren doan xac_nhan."
            % (tot["p_null"] or 1.0))
    return ra


def _xep_dac_trung(X: pd.DataFrame, y: np.ndarray, top: int = 8) -> list[dict]:
    """Tuong quan HANG (Spearman) giua tung dac trung va loi lenh - de AI doc."""
    ra = []
    ry = pd.Series(y).rank().to_numpy()
    for c in X.columns:
        x = X[c].to_numpy(float)
        m = np.isfinite(x)
        if m.sum() < LENH_TOI_THIEU or np.nanstd(x[m]) == 0:
            continue
        rx = pd.Series(x[m]).rank().to_numpy()
        r = float(np.corrcoef(rx, ry[m])[0, 1])
        if not np.isfinite(r):
            continue
        # tb loi theo ba nhom (thap / giua / cao) de doc duoc HINH DANG, khong chi dau
        q1, q2 = np.quantile(x[m], [1 / 3, 2 / 3])
        nhom = [y[m][x[m] <= q1], y[m][(x[m] > q1) & (x[m] <= q2)], y[m][x[m] > q2]]
        ra.append({"dac_trung": c, "spearman": round(r, 3),
                   "tb_bps_thap_giua_cao": [round(float(np.mean(g)) * 1e4, 1) if len(g) else None
                                            for g in nhom],
                   "nguong_1_3_2_3": [_lam_tron(float(q1)), _lam_tron(float(q2))]})
    ra.sort(key=lambda z: -abs(z["spearman"]))
    return ra[:top]


# ============================================================ THOAT LENH
def phan_tich_thoat(lenh: pd.DataFrame) -> dict:
    """MFE/MAE -> goi y QUAN TRI (SL/TP/hue/trailing/thoat bar) cho `dap_quan_tri`.

    Cau hoi cua tung chi so:
      - MAE cua lenh THANG: lenh thang thuong lui bao xa truoc khi thang? SL dat
        sau muc do thi khong cat nham lenh thang.
      - MFE cua lenh THUA: bao nhieu lenh thua DA TUNG lai >= 1 ATR? Nhieu thi
        dat hue / trailing cuu duoc chung.
      - TRA LAI cua lenh thang: lenh thang tra lai bao nhieu phan dinh lai?
      - BAR TOI MFE: lai dinh thuong den sau may bar -> thoat theo thoi gian.
    Day la GOI Y de thu, khong phai ket luan - moi luat phai chay lai qua engine.
    """
    if len(lenh) < LENH_TOI_THIEU or lenh["mae_atr"].isna().all():
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "khong du lenh / thieu ATR"}
    thang = lenh[lenh["loi"] > 0]
    thua = lenh[lenh["loi"] <= 0]
    ra: dict = {"trang_thai": "DAT", "so_thang": len(thang), "so_thua": len(thua)}
    if len(thang) >= 10:
        mae_t = (-thang["mae_atr"]).clip(lower=0).dropna()
        ra["mae_thang_atr_p80_p90"] = [_lam_tron(float(mae_t.quantile(0.8))),
                                       _lam_tron(float(mae_t.quantile(0.9)))]
        tra = ((thang["mfe"] - thang["loi"].apply(np.expm1)) / thang["mfe"].replace(0, np.nan)).dropna()
        ra["thang_tra_lai_trung_vi"] = round(float(tra.median()), 3) if len(tra) else None
        ra["bar_toi_mfe_thang_trung_vi"] = float(thang["bar_mfe"].median())
    if len(thua) >= 10:
        ra["thua_tung_lai_1atr"] = round(float((thua["mfe_atr"] >= 1.0).mean()), 3)
        ra["mae_thua_atr_trung_vi"] = _lam_tron(float((-thua["mae_atr"]).clip(lower=0).median()))
    ra["so_bar_trung_vi"] = float(lenh["so_bar"].median())
    goi_y = []
    p90 = (ra.get("mae_thang_atr_p80_p90") or [None, None])[1]
    if p90 and p90 > 0:
        sl = _lam_tron(1.1 * p90, 2)
        goi_y.append({"luat": {"sl_atr": sl},
                      "vi_sao": "90%% lenh thang chua tung lui qua %.2f ATR - SL %.2f ATR "
                                "gan nhu khong cat lenh thang" % (p90, sl)})
    if ra.get("thua_tung_lai_1atr", 0) >= 0.25:
        goi_y.append({"luat": {"hue_tu_atr": 1.0, **({"sl_atr": _lam_tron(1.1 * p90, 2)} if p90 else {})},
                      "vi_sao": "%.0f%% lenh thua tung lai >= 1 ATR roi quay dau - dat hue o 1 ATR"
                                % (100 * ra["thua_tung_lai_1atr"])})
    if (ra.get("thang_tra_lai_trung_vi") or 0) >= 0.5:
        goi_y.append({"luat": {"trail_tu_atr": 1.0, "trail_buoc": 1.0,
                               **({"sl_atr": _lam_tron(1.1 * p90, 2)} if p90 else {})},
                      "vi_sao": "lenh thang tra lai trung vi %.0f%% dinh lai - trailing giu lai phan do"
                                % (100 * ra["thang_tra_lai_trung_vi"])})
    bm = ra.get("bar_toi_mfe_thang_trung_vi")
    if bm is not None and ra["so_bar_trung_vi"] > 2 * (bm + 1):
        goi_y.append({"luat": {"thoat_bar": int(max(1, round(2 * (bm + 1))))},
                      "vi_sao": "lenh thang dat dinh sau ~%d bar nhung lenh giu ~%d bar - "
                                "thoat som hon" % (bm + 1, ra["so_bar_trung_vi"])})
    ra["goi_y_quan_tri"] = goi_y
    return ra


# ========================================================== TIM QUY LUAT
def loi_suat_toi(df: pd.DataFrame, chan_troi: tuple = (1, 3, 5, 10)) -> np.ndarray:
    """G[t, k] = log(open[t+1+h_k] / open[t+1]): vao o open sau bar tin hieu t, giu h bar."""
    o = np.log(df["open"].to_numpy(float))
    n = len(o)
    G = np.full((n, len(chan_troi)), np.nan)
    for k, h in enumerate(chan_troi):
        if n > h + 1:
            G[: n - 1 - h, k] = o[1 + h:] - o[1: n - h]
    return G


def _quet_bar(kg: _KhongGian, X: np.ndarray, G: np.ndarray, sd: np.ndarray,
              c_mua: np.ndarray, c_ban: np.ndarray, chan_troi: tuple,
              ty_le_min: float, ty_le_max: float, top: int = TOP_GHEP) -> list[tuple]:
    """Mot luot tim quy luat tren bar. -> [(diem, [d..], k_chan_troi, chieu, n, tb)].

    DIEM CHIA CHO DO LECH CHUAN CUA CHINH TAP CON, khong phai cua ca chuoi. Sua
    25/09/2026 sau khi hieu chuan hai chieu bat duoc: ban dau chia cho `sd` KHONG
    dieu kien, va tren 30 hat NHIEU THUAN ti le p_null <= 0,10 la **26,7%** (phai
    ~10%). Ly do: dac trung bien dong (atr_pv, rong20) du bao DO LON loi suat toi
    (cum GARCH) chu khong du bao CHIEU. Tap con "bien dong cao" co trung binh dao
    dong rong hon, nen diem chia cho sd chung cua no rong hon - trong khi null xoay
    vong pha mat su khop bien dong do, nen null hep hon that. Null qua de = moi
    tap con bien dong cao thanh "phat hien". Chia cho sd cua chinh tap con thi
    phan phoi diem khong con phu thuoc viec tap con do on hay dong.
    """
    N = G.shape[0]
    H = np.asarray(chan_troi, float)
    n, S = kg.tong(np.hstack([G, G * G]))
    S1, S2 = S[:, :G.shape[1]], S[:, G.shape[1]:]
    with np.errstate(invalid="ignore", divide="ignore"):
        tb = S1 / n[:, None]
        sd_c = np.sqrt(np.maximum((S2 - S1 * S1 / n[:, None]) / (n[:, None] - 1), 0.0))
        sd_c = np.where(sd_c > 0, sd_c, np.nan)
        diem_mua = (tb - c_mua[None, :]) / sd_c * np.sqrt(n[:, None] / H[None, :])
        diem_ban = (-tb - c_ban[None, :]) / sd_c * np.sqrt(n[:, None] / H[None, :])
    hop = (n >= ty_le_min * N) & (n <= ty_le_max * N)
    hop2 = hop[:, None] & (n[:, None] / H[None, :] >= 30)
    diem_mua[~hop2] = np.nan
    diem_ban[~hop2] = np.nan
    ung = []
    for chieu, D in ((1, diem_mua), (-1, diem_ban)):
        if np.all(np.isnan(D)):
            continue
        k_tot = np.nanargmax(np.nan_to_num(D, nan=-np.inf), axis=1)
        d_tot = D[np.arange(len(D)), k_tot]
        for d in np.flatnonzero(np.isfinite(d_tot)):
            ung.append((float(d_tot[d]), [int(d)], int(k_tot[d]), chieu, float(n[d]),
                        float(tb[d, k_tot[d]])))
    ung.sort(key=lambda z: -z[0])
    don, da_f = [], set()
    for z in ung:
        f = kg.dk[z[1][0]][0]
        if f not in da_f and len(don) < top:
            da_f.add(f)
            don.append(z)
    for a in range(len(don)):
        ma = kg.mat_na(X, don[a][1][0])
        for b in range(a + 1, len(don)):
            m = ma & kg.mat_na(X, don[b][1][0])
            nn = float(m.sum())
            if nn < ty_le_min * N:
                continue
            tbm = np.nanmean(G[m], axis=0)
            sdm = np.nanstd(G[m], axis=0, ddof=1)
            sdm = np.where(sdm > 0, sdm, np.nan)
            for chieu, c in ((1, c_mua), (-1, c_ban)):
                with np.errstate(invalid="ignore"):
                    dd = (chieu * tbm - c) / sdm * np.sqrt(nn / H)
                dd[nn / H < 30] = np.nan
                if np.all(np.isnan(dd)):
                    continue
                k = int(np.nanargmax(dd))
                ung.append((float(dd[k]), [don[a][1][0], don[b][1][0]], k, chieu, nn,
                            float(tbm[k])))
    ung.sort(key=lambda z: -z[0])
    return ung


def tim_quy_luat(df: pd.DataFrame, X: pd.DataFrame, cp=None, bat_dau: int = 0,
                 chan_troi: tuple = (1, 3, 5, 10), so_null: int = 200, hat: int = 0,
                 ty_le_min: float = 0.01, ty_le_max: float = 0.6, so_luat: int = 8,
                 bar_moi_ngay: float = 1.0) -> dict:
    """Tim DIEU KIEN lam loi suat h bar toi lech khoi 0 SAU CHI PHI. Xem dau file.

    `df`/`X`: tien to du lieu va dac trung (cung chi muc); chi xet bar tin hieu
    tu `bat_dau` tro di (doan dang kham pha) va du h bar phia truoc.
    `cp`: `chi_phi.MoHinhChiPhi` - chi phi khu hoi tru vao TUNG lenh tiem nang.
    """
    G_all = loi_suat_toi(df, chan_troi)
    hmax = max(chan_troi)
    cuoi = len(df) - 1 - hmax
    idx = np.arange(bat_dau, max(bat_dau, cuoi))
    ra: dict = {"chan_troi": list(chan_troi), "canh_bao": [], "luat": []}
    if len(idx) < 300:
        ra["trang_thai"] = "CHUA_DO_DUOC"
        ra["canh_bao"].append("chi %d bar tin hieu < 300" % len(idx))
        return ra
    G = G_all[idx]
    Xm = X.to_numpy(float)[idx]
    if cp is not None:
        mot_chieu = float(np.mean(cp.spread_mang(df.index[idx]))) + float(cp.truot_gia_frac)
        ngay = np.asarray(chan_troi, float) / max(bar_moi_ngay, 1e-9)
        c_mua = 2 * mot_chieu + max(cp.phi_nam_mua, 0.0) * ngay / 365.0
        c_ban = 2 * mot_chieu + max(cp.phi_nam_ban, 0.0) * ngay / 365.0
    else:
        c_mua = c_ban = np.zeros(len(chan_troi))
    sd = np.nanstd(G, axis=0, ddof=1)
    kg = _KhongGian(Xm, list(X.columns))
    that = _quet_bar(kg, Xm, G, sd, c_mua, c_ban, chan_troi, ty_le_min, ty_le_max)
    rng = np.random.default_rng(20260925 + hat)
    N = len(idx)
    cuc_dai = []
    for _ in range(so_null):
        k = int(rng.integers(N // 10, N - N // 10))
        u = _quet_bar(kg, Xm, np.roll(G, k, axis=0), sd, c_mua, c_ban, chan_troi,
                      ty_le_min, ty_le_max)
        if u:
            cuc_dai.append(u[0][0])
    cuc_dai = np.asarray(cuc_dai, float)
    ra["null"] = {"kieu": "xoay_vong", "so": int(len(cuc_dai)),
                  "cuc_dai_trung_vi": round(float(np.median(cuc_dai)), 2) if len(cuc_dai) else None,
                  "cuc_dai_p95": round(float(np.quantile(cuc_dai, 0.95)), 2) if len(cuc_dai) else None}
    ra["chi_phi_khu_hoi_bps"] = {"mua": [round(float(x) * 1e4, 2) for x in c_mua],
                                 "ban": [round(float(x) * 1e4, 2) for x in c_ban]}
    ra["so_bar_tin_hieu"] = int(N)
    da_thay = set()
    for diem, dk, k, chieu, n, tb in that:
        khoa = (tuple(sorted(dk)), chieu)
        if khoa in da_thay:
            continue
        da_thay.add(khoa)
        h = chan_troi[k]
        p = (1 + int(np.sum(cuc_dai >= diem))) / (1 + len(cuc_dai)) if len(cuc_dai) else None
        c = (c_mua if chieu > 0 else c_ban)[k]
        ra["luat"].append({
            "dieu_kien": " VA ".join(kg.mo_ta(d) for d in dk),
            "chieu": chieu, "giu": int(h),
            "ty_le_kich_hoat": round(n / N, 4), "so_lan": int(n),
            "tb_tho_bps": round(chieu * tb * 1e4, 2),
            "tb_rong_bps": round((chieu * tb - c) * 1e4, 2),
            "diem": round(diem, 2),
            "p_null": round(float(p), 4) if p is not None else None,
            "spec": _spec_tu_luat(kg, dk, chieu, h, n / N, (chieu * tb - c) * 1e4),
        })
        if len(ra["luat"]) >= so_luat:
            break
    tot = ra["luat"][0] if ra["luat"] else None
    if tot is None:
        ra["trang_thai"] = "AM"
    elif tot["p_null"] is not None and tot["p_null"] <= 0.05 and tot["tb_rong_bps"] > 0:
        ra["trang_thai"] = "DAT"
    else:
        ra["trang_thai"] = "AM"
        ra["canh_bao"].append("luat tot nhat p_null %s - khong vuot duoc cuc dai cua nhieu"
                              % (tot["p_null"],))
    return ra


def _spec_tu_luat(kg: _KhongGian, dk: list, chieu: int, h: int, ty_le: float,
                  rong_bps: float) -> dict:
    """Luat -> khai bao DSL day du (kiem duoc bang `ngu_phap.kiem_khai_bao`)."""
    nhom = {DT.DAC_TRUNG[kg.ten[kg.dk[d][0]]][2] for d in dk}
    ho = "quay_ve_trung_binh"
    for nh in ("lich", "bien_dong", "dong_tien", "xu_huong", "dong_luong", "kenh", "dao_dong", "nen"):
        if nh in nhom:
            ho = DT.HO_THEO_NHOM[nh]
            break
    ten = "ql_" + "_".join("%s%s" % (kg.ten[kg.dk[d][0]], {"<": "lt", ">=": "ge", "==": "eq"}[kg.dk[d][1]])
                           for d in dk) + "_h%d_%s" % (h, "mua" if chieu > 0 else "ban")
    return {
        "ten": ten[:60],
        "co_che": ("Quy luat do may tim tren doan kham pha: khi %s thi %d bar sau "
                   "loi suat rong ~%.1f bps/lenh (kich hoat %.1f%% so bar). AI PHAI "
                   "viet lai cau nay: ai tra tien cho phoi nhiem nay va vi sao."
                   % (" VA ".join(kg.mo_ta(d) for d in dk), h, rong_bps, 100 * ty_le)),
        "ho": ho, "chieu": int(chieu), "giu": int(h),
        "vao": [kg.dsl(d) for d in dk], "ra": [],
    }


if __name__ == "__main__":
    import json
    import time
    from nhan import nc_du_lieu as NDL
    for ma in ("TONG_HOP_NHIEU_1", "TONG_HOP_HOI_QUY_1"):
        d = NDL.nap(ma, "H4")
        pre, a = NDL.cat_doan(d, "kham_pha")
        X = DT.tinh(pre)
        cp = NDL.chi_phi(ma, pre)
        t0 = time.time()
        r = tim_quy_luat(pre, X, cp, bat_dau=260, so_null=100, bar_moi_ngay=6)
        print(ma, r["trang_thai"], "%.1fs" % (time.time() - t0), json.dumps(r["null"]))
        for l in r["luat"][:4]:
            print("   ", l["dieu_kien"], "chieu", l["chieu"], "h", l["giu"],
                  "rong", l["tb_rong_bps"], "p", l["p_null"], "n", l["so_lan"])
