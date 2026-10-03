# -*- coding: utf-8 -*-
"""nc_bot_hoc.py - DAU TRUONG cho "bot tu hoc": moi con bot hoc tang cuong phai thi o day truoc.

Sinh ra 29/09/2026 tu mot quang cao chu du an gui (FatBoy Studio: "Bot dang hoc. Dong do la luc no
sai" - bang log Step 98.4xx, Buy/Sell/Hold, Entry/Final/SL/TP, TIMEOUT, Reward, Avg(1000) ~ +7,9).
Chu du an hoi: co dang di sau khong, hay cu di loi cu. Tra loi bang SO, tren chuoi BIET TRUOC DAP AN
(`nc_du_lieu.KICH_BAN`), khong bang y kien.

## Con bot (dung kieu quang cao)

    trang thai  26 dac trung `nc_dac_trung` (+ 10 loi suat gan nhat / do lech chuan - bien the A)
    hanh dong   Hold · Buy/Sell giu toi da 1 bar · Buy/Sell giu toi da 5 bar
    lenh        vao o gia mo bar sau (tin hieu biet tai dong cua), TP/SL = 2 ATR, het gio = TIMEOUT
    thuong      lai lo bps SAU phi khu hoi (spread + truot gia cua mo hinh chi phi)
    hoc         Q-learning, mang MLP numpy, epsilon-greedy, 100.000 buoc tai diem NGAU NHIEN cua doan
                kham pha - dung cach quang cao sinh "Avg(1000)"
    A           mang 64-64, co cua so gia tho, khong dung som - dung kieu quang cao
    B           "bot can than": 26 dac trung, mang 16-16, phat trong so, dung som tren 20% cuoi
                cua kham pha (khong cham doan xac nhan / niem phong)
    thi         chinh sach tham lam, lenh KHONG chong nhau; DAT = >= 20 lenh va lai sau phi > 0;
                giao thuc nhu AI: chi mo niem phong khi xac nhan DAT

## Do 29/09 (25 chuoi, H4, `b nc bot 5`) - xem `reports/NC_BOT_HOC.md`

- Avg(1000) luc hoc DUONG tren NHIEU THUAN: A +21..+28 bps, B +10..+16 bps; t trong mau 27-32 (A).
  Con so quang cao khoe (+7,9) la thu mot con bot sinh ra tren du lieu khong co gi.
- Edge that (15 chuoi): A 1/15, B 5/15 (chi LOC); loi cu (tu lai, khong biet truoc) 9/15, gia thuyet
  co chu dich 10/10 tren edge manh/yeu (`reports/NC_HIEU_CHUAN.md`).
- Bao dong gia qua giao thuc (10 chuoi khong edge): 0 ca hai ben.

Doc: bot khong lua nguoi qua giao thuc ba doan - no chi rat it khi tim ra gi. Bot B tim ra LOC (mau
nhieu bar, theo che do bien dong) 5/5 voi 1-3 bps/lenh; `mo_xe_lenh` tim DUNG bo loc cua LOC 5/5 va
he loc lai 10-24 bps/lenh tren xac nhan o 4/5 chuoi. Vai tro hop ly cua ML: MAY GOI Y dieu kien cho `mo_xe_lenh`
/ `thu_co_che`, khong phai con duong chinh.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nhan import nc_dac_trung as DT, nc_du_lieu as NDL

LAB = Path(__file__).resolve().parent.parent
H = (1, 5)                 # thoi gian giu toi da (bar) cua hai loai lenh
K_TP, K_SL = 2.0, 2.0      # TP / SL theo ATR 14
KICH_BAN_DAU = ("NHIEU", "BETA", "HOI_QUY", "HOI_QUY_YEU", "LOC")


def thuong_theo_bar(df: pd.DataFrame, cp, atr: np.ndarray) -> tuple[np.ndarray, list]:
    """R[t, j] = lai lo bps SAU phi neu tai dong cua bar t chon hanh dong j (vao o gia mo t+1)."""
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    n = len(df)
    phi = 2 * (cp.spread_mang(df.index) + cp.truot_gia_frac)       # khu hoi, phan cua gia
    A = [(s, hh) for hh in H for s in (1, -1)]
    R = np.full((n, len(A)), np.nan)
    for t in range(n - max(H) - 2):
        e = o[t + 1]
        if not np.isfinite(atr[t]):
            continue
        for j, (s, hh) in enumerate(A):
            tp, sl = e + s * K_TP * atr[t], e - s * K_SL * atr[t]
            x = c[t + hh]
            for u in range(t + 1, t + hh + 1):
                if (l[u] <= sl) if s > 0 else (h[u] >= sl):
                    x = sl                     # ca TP va SL trong mot nen -> tinh SL (than trong)
                    break
                if (h[u] >= tp) if s > 0 else (l[u] <= tp):
                    x = tp
                    break
            R[t, j] = (s * (x / e - 1.0) - phi[t]) * 1e4
    return R, A


def chuan_bi(ma: str, khung: str = "H4"):
    df = NDL.nap(ma, khung)
    cp = NDL.chi_phi(ma, df)
    c = df["close"].to_numpy(float)
    h, l = df["high"].to_numpy(float), df["low"].to_numpy(float)
    n = len(df)
    lr = np.diff(np.log(c), prepend=np.nan)
    sd = pd.Series(lr).rolling(100, min_periods=20).std().to_numpy()
    cua_so = np.full((n, 10), np.nan)
    for k in range(10):
        cua_so[k:, k] = lr[:n - k] / sd[k:] if k else lr / sd
    tr = np.maximum(h - l, np.maximum(abs(h - np.roll(c, 1)), abs(l - np.roll(c, 1))))
    atr = pd.Series(tr).rolling(14, min_periods=14).mean().to_numpy()
    F = np.column_stack([DT.tinh(df).to_numpy(float), cua_so])
    R, A = thuong_theo_bar(df, cp, atr)
    return df, F, R, A


class MLP:
    """Mang 2 lop an ReLU, Adam, loss Huber tren hanh dong DA CHON (Q-learning mot buoc)."""

    def __init__(self, d: int, k: int, h: int = 64, seed: int = 0, lr: float = 1e-3, wd: float = 0.0):
        g = np.random.default_rng(seed)
        self.p = [g.normal(0, np.sqrt(2 / d), (d, h)), np.zeros(h),
                  g.normal(0, np.sqrt(2 / h), (h, h)), np.zeros(h),
                  g.normal(0, np.sqrt(1 / h), (h, k)), np.zeros(k)]
        self.m = [np.zeros_like(w) for w in self.p]
        self.v = [np.zeros_like(w) for w in self.p]
        self.lr, self.t, self.wd = lr, 0, wd

    def f(self, X):
        W1, b1, W2, b2, W3, b3 = self.p
        z1 = X @ W1 + b1
        a1 = np.maximum(z1, 0)
        z2 = a1 @ W2 + b2
        a2 = np.maximum(z2, 0)
        return a2 @ W3 + b3, (X, z1, a1, z2, a2)

    def hoc(self, X, a, r):
        q, (X, z1, a1, z2, a2) = self.f(X)
        g = np.zeros_like(q)
        i = np.arange(len(a))
        g[i, a] = np.clip(q[i, a] - r, -1, 1) / len(a)
        W1, b1, W2, b2, W3, b3 = self.p
        dW3, db3 = a2.T @ g, g.sum(0)
        d2 = (g @ W3.T) * (z2 > 0)
        dW2, db2 = a1.T @ d2, d2.sum(0)
        d1 = (d2 @ W2.T) * (z1 > 0)
        dW1, db1 = X.T @ d1, d1.sum(0)
        self.t += 1
        for w, dw, m, v in zip(self.p, (dW1, db1, dW2, db2, dW3, db3), self.m, self.v):
            m *= 0.9
            m += 0.1 * dw
            v *= 0.999
            v += 0.001 * dw * dw
            w -= self.lr * (m / (1 - 0.9 ** self.t)) / (np.sqrt(v / (1 - 0.999 ** self.t)) + 1e-8)
            if self.wd:
                w -= self.lr * self.wd * w


def _di_bo(q: np.ndarray, R: np.ndarray, A: list, chi_so, ok) -> list:
    """Chinh sach tham lam, lenh KHONG chong nhau: dang dung ngoai thi hoi Q; Q > 0 thi vao."""
    ds, u = [], 0
    while u < len(chi_so):
        t = chi_so[u]
        if ok[t] and q[u].max() > 0:
            j = int(np.argmax(q[u]))
            ds.append((R[t, j], A[j][0]))
            u += A[j][1] + 1
        else:
            u += 1
    return ds


def hoc(ma: str, bien_the: str = "A", buoc: int = 100_000, hat: int = 0, khung: str = "H4") -> dict:
    """Huan luyen mot bot tren kham pha roi thi tren ca ba doan. -> so lieu, khong phan quyet cua AI."""
    df, F, R, A = chuan_bi(ma, khung)
    if bien_the == "B":
        F = F[:, :F.shape[1] - 10]
    n = len(df)
    a_kp, b_kp = NDL.chi_so_doan(n, "kham_pha")
    mu = np.nanmean(F[a_kp:b_kp], 0)
    sd = np.nanstd(F[a_kp:b_kp], 0) + 1e-9
    Xs = np.clip(np.nan_to_num((F - mu) / sd), -5, 5)
    ok = np.isfinite(R).all(1) & np.isfinite(F).all(1)
    T = np.array([t for t in range(a_kp, b_kp - max(H) - 1) if ok[t]])
    g = np.random.default_rng(hat)
    if bien_the == "B":
        cat = int(len(T) * 0.8)
        T, T_dung = T[:cat], T[cat:]
        net = MLP(Xs.shape[1], len(A), h=16, seed=hat, wd=1e-2)
    else:
        T_dung = None
        net = MLP(Xs.shape[1], len(A), seed=hat)
    tot_p, tot_d = None, -1e18
    Sx = np.empty((buoc, Xs.shape[1]))
    Sa = np.empty(buoc, int)
    Sr = np.empty(buoc)
    m, gan, log = 0, [], []
    for st in range(buoc):
        eps = max(0.05, 1.0 - st / (0.3 * buoc))
        t = T[g.integers(len(T))]
        if g.random() < eps:
            a = int(g.integers(len(A) + 1)) - 1                   # -1 = Hold
        else:
            q = net.f(Xs[t][None])[0][0]
            a = int(np.argmax(q)) if q.max() > 0 else -1
        r = 0.0 if a < 0 else float(R[t, a])
        gan.append(r)
        if a >= 0:
            Sx[m], Sa[m], Sr[m] = Xs[t], a, r / 50.0
            m += 1
        if m >= 256 and st % 8 == 0:
            j = g.integers(m, size=64)
            net.hoc(Sx[j], Sa[j], Sr[j])
        if (st + 1) % max(1, buoc // 5) == 0:
            log.append(round(float(np.mean(gan[-1000:])), 2))
        if T_dung is not None and (st + 1) % max(1, buoc // 20) == 0 and st > 0.3 * buoc:
            ds = _di_bo(net.f(Xs[T_dung])[0] * 50.0, R, A, T_dung, ok)
            d = float(sum(x for x, _ in ds))
            if d > tot_d:
                tot_d, tot_p = d, [w.copy() for w in net.p]
    if tot_p is not None:
        net.p = tot_p
    q_all = net.f(Xs)[0] * 50.0

    def thi(doan: str) -> dict:
        a0, a1 = NDL.chi_so_doan(n, doan)
        cs = np.arange(a0, a1 - max(H) - 1)
        ds = _di_bo(q_all[cs], R, A, cs, ok)
        x = np.array([v for v, _ in ds])
        tb = float(x.mean()) if len(x) else 0.0
        tt = float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 and x.std() > 0 else 0.0
        return {"lenh": len(x), "tb_bps": round(tb, 2), "t": round(tt, 2),
                "ty_le_mua": round(sum(s > 0 for _, s in ds) / max(len(ds), 1), 2),
                "dat": bool(len(x) >= 20 and tb > 0)}
    ra = {"ma": ma, "bien_the": bien_the, "buoc": buoc, "avg1000_hoc": log,
          "kham_pha": thi("kham_pha"), "xac_nhan": thi("xac_nhan"), "niem_phong": thi("niem_phong")}
    ra["dat_giao_thuc"] = bool(ra["xac_nhan"]["dat"] and ra["niem_phong"]["dat"])
    return ra


def dau_truong(so_hat: int = 5, buoc: int = 100_000, loi_cu: bool = True, ghi_bao_cao: bool = True,
               in_ra=print) -> dict:
    """Hai bien the bot + (tuy chon) loi cu `nc_tu_lai` tren CUNG cac chuoi co dap an."""
    from nhan import nc_so_tay as ST, nc_tu_lai as TL
    t0 = time.time()
    bot, cu = [], []
    for kb in KICH_BAN_DAU:
        for hat in range(1, so_hat + 1):
            ma = "TONG_HOP_%s_%d" % (kb, hat)
            for bt in ("A", "B"):
                r = hoc(ma, bt, buoc, hat)
                r["kb"] = kb
                bot.append(r)
                in_ra("%s %s hoc %s | xn %s | np %s | %.0fs" % (
                    bt, ma, r["avg1000_hoc"][-1:], r["xac_nhan"]["tb_bps"], r["niem_phong"]["tb_bps"],
                    time.time() - t0))
    if loi_cu:
        db_cu = ST.DB
        ST.DB = Path(tempfile.mkdtemp(prefix="nc_bot_hoc_")) / "nc.db"
        try:
            for kb in KICH_BAN_DAU:
                for hat in range(1, so_hat + 1):
                    ma = "TONG_HOP_%s_%d" % (kb, hat)
                    r = TL.chay(ma, "H4", in_ra=lambda *a: None)
                    d = {"kb": kb, "ma": ma, "ket_cuc": TL._ket_cuc(r["ket"])}
                    if kb == "LOC":
                        h = TL.hoc_tu_lenh((ma,))[0]
                        d["hoc_tu_lenh"] = {"bo_loc": h.get("bo_loc"), "p": h.get("p_null"),
                                            "dung": h["dung"], "kv_loc_xn": h.get("kv_loc_xn")}
                    cu.append(d)
                    in_ra("loi cu %s %s" % (ma, d["ket_cuc"]))
        finally:
            ST.DB = db_cu
    tom = {"so_hat": so_hat, "buoc": buoc, "bot": bot, "loi_cu": cu}
    if ghi_bao_cao:
        tom["bao_cao"] = _bao_cao(tom)
    return tom


def _bao_cao(tom: dict) -> str:
    bot, cu, n = tom["bot"], tom["loi_cu"], tom["so_hat"]

    def dem(bt, kb):
        return sum(r["dat_giao_thuc"] for r in bot if r["bien_the"] == bt and r["kb"] == kb)

    def hoc_min_max(bt, kb):
        v = [r["avg1000_hoc"][-1] for r in bot if r["bien_the"] == bt and r["kb"] == kb]
        return "%+.1f..%+.1f" % (min(v), max(v)) if v else "-"

    L = ["# DAU TRUONG BOT TU HOC - chuoi co dap an",
         "", "*%s · `b nc bot %d` (nhan/nc_bot_hoc.dau_truong), %d buoc hoc moi bot*"
         % (time.strftime("%Y-%m-%d %H:%M:%S"), n, tom["buoc"]), "",
         "Bot kieu quang cao (A) va bot can than (B) hoc tren kham pha, thi tren xac nhan -> niem "
         "phong (chi mo niem phong khi xac nhan DAT). DAT = >= 20 lenh va lai sau phi > 0. So la so "
         "chuoi DAT tren %d hat moi kich ban." % n, "",
         "| kich ban | edge that | bot A | bot B | loi cu (tu lai, khong biet truoc) | Avg(1000) luc hoc A | "
         "Avg(1000) luc hoc B |", "|---|---|---:|---:|---:|---|---|"]
    for kb in KICH_BAN_DAU:
        c = [d for d in cu if d["kb"] == kb]
        cu_s = ("%d/%d" % (sum(d["ket_cuc"] == "DAT" for d in c), len(c))) if c else "-"
        if kb == "LOC" and c:
            cu_s += " (mo xe lenh tim dung bo loc %d/%d)" % (
                sum(bool(d.get("hoc_tu_lenh", {}).get("p") is not None and d["hoc_tu_lenh"]["p"] <= 0.05)
                    for d in c), len(c))
        L.append("| %s | %s | %d/%d | %d/%d | %s | %s | %s |" % (
            kb, "co" if NDL.CO_EDGE_SAU_PHI[kb] else "KHONG", dem("A", kb), n, dem("B", kb), n, cu_s,
            hoc_min_max("A", kb), hoc_min_max("B", kb)))
    L += ["", "## Tung lan chay", "",
          "| bot | chuoi | Avg(1000) cuoi | t kham pha | xac nhan bps (lenh) | niem phong bps (lenh) | "
          "ti le mua np | DAT |", "|---|---|---:|---:|---:|---:|---:|---|"]
    for r in bot:
        L.append("| %s | %s | %s | %s | %s (%d) | %s (%d) | %s | %s |" % (
            r["bien_the"], r["ma"], r["avg1000_hoc"][-1] if r["avg1000_hoc"] else "-",
            r["kham_pha"]["t"], r["xac_nhan"]["tb_bps"], r["xac_nhan"]["lenh"],
            r["niem_phong"]["tb_bps"], r["niem_phong"]["lenh"], r["niem_phong"]["ty_le_mua"],
            "DAT" if r["dat_giao_thuc"] else "-"))
    L += ["", "Doc: Avg(1000) luc hoc - con so quang cao khoe - duong ca tren NHIEU THUAN. No do viec "
          "bot nho du lieu da thay, khong do edge. Chi cot DAT (xac nhan roi niem phong) la cau tra "
          "loi."]
    f = LAB / "reports" / "NC_BOT_HOC.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("\n".join(L) + "\n", encoding="utf-8")
    return str(f.relative_to(LAB))


def main(argv: list[str]) -> int:
    if argv and argv[0] in ("-h", "--help"):
        print("python -m nhan.nc_bot_hoc [SO_HAT=5] [--khong-loi-cu]  # dau truong bot tu hoc")
        return 0
    so_hat = int(argv[0]) if argv and argv[0].isdigit() else 5
    r = dau_truong(so_hat, loi_cu="--khong-loi-cu" not in argv)
    print(r.get("bao_cao"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
