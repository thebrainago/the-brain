import numpy as np
import pandas as pd
import brain_co_che as bc

MIN_EVENTS = 30
N_PERM = 2000
ZIGZAG_HE_SO = 1.5


def _field(s, key, default=None):
    try:
        return s[key]
    except Exception:
        return default


def _pos(df, v):
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, (float, np.floating)) and float(v).is_integer():
        return int(v)
    try:
        return df.index.get_loc(v)
    except Exception:
        return int(v)


def _huong(s):
    h = _field(s, "huong")
    if h is None:
        return 0
    if isinstance(h, str):
        hl = h.lower().strip()
        if hl in ("up", "u", "+", "1", "tang", "tăng", "len", "lên"):
            return 1
        if hl in ("down", "d", "-", "-1", "giam", "giảm", "xuong", "xuống"):
            return -1
        if hl and hl[0] in ("u", "t", "l", "+"):
            return 1
        return -1
    try:
        val = float(h)
        if np.isnan(val):
            return 0
        return 1 if val > 0 else -1
    except Exception:
        return 0


def _duration(df, s):
    dur = _field(s, "thoi_luong")
    if dur is not None:
        try:
            if not pd.isna(dur):
                return float(dur)
        except Exception:
            pass
    start = _pos(df, _field(s, "tu"))
    end = _pos(df, _field(s, "den"))
    return float(abs(end - start) + 1)


def _vol_avg(df, s):
    start = _pos(df, _field(s, "tu"))
    end = _pos(df, _field(s, "den"))
    if end < start:
        return np.nan
    return float(np.mean(df["volume"].iloc[start:end + 1]))


def _perm_stats(cond, outcome, huong, rng, n_perm=N_PERM):
    n = len(cond)
    stats = np.empty(n_perm)
    groups = np.unique(huong)

    for b in range(n_perm):
        pcond = np.zeros(n, dtype=bool)
        for g in groups:
            idx = np.where(huong == g)[0]
            k = int(cond[idx].sum())
            if k > 0:
                chosen = rng.choice(idx, size=k, replace=False)
                pcond[chosen] = True
        stats[b] = outcome[pcond].mean()

    return stats


def do(khoa, df, rng):
    try:
        ch = bc.chan_song(df, he_so=ZIGZAG_HE_SO)
    except Exception:
        ch = None

    if ch is None or len(ch) < 4:
        return None

    doan = bc.cac_doan(df, ch)
    if doan is None or len(doan) < 6:
        return None

    segs = []
    for _, s in doan.iterrows():
        start = _pos(df, _field(s, "tu"))
        end = _pos(df, _field(s, "den"))
        if end <= start:
            continue
        h = _huong(s)
        if h == 0:
            continue
        dur = _duration(df, s)
        if not np.isfinite(dur) or dur <= 0:
            continue
        segs.append({
            "tu": start,
            "den": end,
            "huong": h,
            "thoi_luong": dur,
        })

    if len(segs) < 7:
        return None

    vol_avgs = [_vol_avg(df, s) for s in segs]

    # Mỗi ứng viên là một bộ ba chân cùng hướng:
    # D_before, U1, X1, U2, X2, U3, D_after
    candidates = []
    for i in range(1, len(segs) - 5):
        s_before = segs[i - 1]
        s1 = segs[i]
        x1 = segs[i + 1]
        s2 = segs[i + 2]
        x2 = segs[i + 3]
        s3 = segs[i + 4]
        s_after = segs[i + 5]

        h = s1["huong"]
        if s2["huong"] != h or s3["huong"] != h:
            continue
        if x1["huong"] != -h or x2["huong"] != -h:
            continue
        if s_before["huong"] != -h or s_after["huong"] != -h:
            continue

        v1 = vol_avgs[i]
        v2 = vol_avgs[i + 2]
        v3 = vol_avgs[i + 4]
        if not (np.isfinite(v1) and np.isfinite(v2) and np.isfinite(v3)):
            continue

        dieu_kien = bool((v2 < v1) and (v2 < v3))
        ket_qua = bool(s_after["thoi_luong"] < s_before["thoi_luong"])

        candidates.append((h, dieu_kien, ket_qua))

    if len(candidates) == 0:
        return None

    huong = np.array([c[0] for c in candidates], dtype=int)
    cond = np.array([c[1] for c in candidates], dtype=bool)
    outcome = np.array([c[2] for c in candidates], dtype=bool)

    n_ev = int(cond.sum())
    if n_ev < MIN_EVENTS:
        return None

    quan_sat_tho = float(outcome[cond].mean())
    perm_stats = _perm_stats(cond, outcome, huong, rng)
    perm_stats = perm_stats[np.isfinite(perm_stats)]

    if len(perm_stats) == 0:
        return None

    null_tb = float(np.mean(perm_stats))
    null_sd = float(np.std(perm_stats, ddof=1)) if len(perm_stats) > 1 else 0.0
    p = float((np.sum(perm_stats >= quan_sat_tho) + 1.0) / (len(perm_stats) + 1.0))

    if null_sd > 0:
        thong_ke = (quan_sat_tho - null_tb) / null_sd
    else:
        thong_ke = 0.0

    ghi_chu = (
        f"Zigzag ha nguong xuong he_so={ZIGZAG_HE_SO} de du mau; chan nho hon va nhieu hon."
        " Su kien: bo ba chan cung huong U1,U2,U3 lien tiep, dieu kien V(U2) < V(U1) va V(U2) < V(U3),"
        " V la trung binh volume moi phien trong chan. "
        "So sanh thoi_luong chan dieu chinh ngay sau U3 va ngay truoc U1. "
        "Hoan vi nhan 'dieu kien V thap' trong tung nhom huong, giu nguyen so su kien va ty le up/down;"
        " p la p mot phia. thong_ke duong = ung ho khang dinh."
    )

    return {
        "thong_ke": float(thong_ke),
        "p": p,
        "n": n_ev,
        "quan_sat_tho": quan_sat_tho,
        "null_tb": null_tb,
        "null_sd": null_sd,
        "n_candidate": int(len(candidates)),
        "n_perm": N_PERM,
        "ghi_chu": ghi_chu,
    }