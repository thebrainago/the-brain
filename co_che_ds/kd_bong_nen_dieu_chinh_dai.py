import numpy as np
import pandas as pd

try:
    from scipy.stats import rankdata
    _HAVE_SCIPY = True
except Exception:
    _HAVE_SCIPY = False

N_PERM = 2000
WINDOW = 30
MIN_PERIODS = 8


def _lay_vi_tri(v, df):
    """Chuyen vi_tri (int hoac label) ve vi tri so nguyen trong DataFrame."""
    if v is None:
        return None
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        if np.isnan(v):
            return None
        iv = int(v)
        if abs(v - iv) < 1e-8:
            return iv
        return None
    try:
        loc = df.index.get_loc(v)
        if isinstance(loc, slice):
            return int(loc.start)
        if isinstance(loc, np.ndarray):
            return int(loc[0])
        return int(loc)
    except Exception:
        return None


def _rankdata(a):
    if _HAVE_SCIPY:
        return rankdata(a).astype(float)

    a = np.asarray(a, dtype=float)
    n = len(a)
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(n, dtype=float)
    ranks[order] = np.arange(1, n + 1, dtype=float)

    i = 0
    while i < n:
        j = i
        while j + 1 < n and a[order[j + 1]] == a[order[i]]:
            j += 1
        if j > i:
            avg = (ranks[order[i]] + ranks[order[j]]) / 2.0
            ranks[order[i:j + 1]] = avg
        i = j + 1
    return ranks


def _corr(a, b):
    a = np.asarray(a, dtype=float) - np.mean(a)
    b = np.asarray(b, dtype=float) - np.mean(b)
    denom = np.sqrt(np.sum(a * a) * np.sum(b * b))
    if denom == 0:
        return 0.0
    return float(np.sum(a * b) / denom)


def _thong_ke_neg(x, y):
    """negative Spearman: duong nghia la body/range thap -> thoi luong dai."""
    return -_corr(_rankdata(x), _rankdata(y))


def _perm_test(x, y, dirs, rng):
    ry = _rankdata(y)
    obs = _thong_ke_neg(x, y)
    perms = np.empty(N_PERM)
    uniq = np.unique(dirs)

    for b in range(N_PERM):
        xp = np.array(x, dtype=float, copy=True)
        for d in uniq:
            idx = np.where(dirs == d)[0]
            if len(idx) > 1:
                xp[idx] = rng.permutation(xp[idx])
        perms[b] = -_corr(_rankdata(xp), ry)

    null_tb = float(np.mean(perms))
    null_sd = float(np.std(perms, ddof=1))
    if null_sd <= 0 or not np.isfinite(null_sd):
        return None

    z = (obs - null_tb) / null_sd
    p = (1.0 + np.sum(np.abs(perms) >= np.abs(obs))) / (N_PERM + 1.0)
    return obs, z, p, null_tb, null_sd


def do(khoa, df, rng):
    try:
        import brain_co_che as bc
    except Exception:
        return None

    if df is None or len(df) < 50:
        return None

    try:
        ch = bc.chan_song(df)
        if ch is None or len(ch) < 5:
            return None
    except Exception:
        return None

    if "vi_tri" not in ch.columns or "gia" not in ch.columns:
        return None

    if "xac_nhan" in ch.columns:
        ch = ch.dropna(subset=["xac_nhan"])

    ch = ch.dropna(subset=["vi_tri", "gia"]).reset_index(drop=True)
    if len(ch) < 5:
        return None

    poss = [_lay_vi_tri(v, df) for v in ch["vi_tri"].to_numpy()]
    if any(p is None for p in poss):
        return None

    poss = np.asarray([int(p) for p in poss], dtype=int)
    order = np.argsort(poss, kind="mergesort")
    ch = ch.iloc[order].reset_index(drop=True)
    poss = poss[order]
    gia = ch["gia"].to_numpy(dtype=float)

    n = len(df)
    opens = df["open"].to_numpy(dtype=float)
    highs = df["high"].to_numpy(dtype=float)
    lows = df["low"].to_numpy(dtype=float)
    closes = df["close"].to_numpy(dtype=float)

    tu_list, den_list, dur_list, dir_list, ratio_list = [], [], [], [], []

    for i in range(len(ch) - 1):
        a = poss[i]
        b = poss[i + 1]
        if not (0 <= a < n and 0 <= b < n and b > a):
            continue
        if gia[i + 1] == gia[i]:
            continue

        span = highs[b] - lows[b]
        if span <= 0:
            continue

        # body/range cua nen dao chieu tai chan xung (bar den)
        ratio = abs(closes[b] - opens[b]) / span
        direction = "up" if gia[i + 1] > gia[i] else "down"

        tu_list.append(a)
        den_list.append(b)
        dur_list.append(b - a)
        dir_list.append(direction)
        ratio_list.append(ratio)

    if len(tu_list) < 30:
        return None

    seg = pd.DataFrame({
        "tu": tu_list,
        "den": den_list,
        "dur": dur_list,
        "dir": dir_list,
        "ratio": ratio_list,
    })
    seg = seg.sort_values("tu").reset_index(drop=True)

    # Luat 4: chuan hoa thoi luong theo median truot cua cac doan truoc do
    seg["base"] = seg["dur"].rolling(
        window=WINDOW, min_periods=MIN_PERIODS
    ).median().shift(1)
    seg["rel_dur"] = seg["dur"] / seg["base"]

    if len(seg) < 2:
        return None

    # Ghep cap: chan xung i voi chan dieu chinh i+1
    ev = pd.DataFrame({
        "ratio": seg["ratio"].iloc[:-1].to_numpy(),
        "rel_dur": seg["rel_dur"].iloc[1:].to_numpy(),
        "dir_imp": seg["dir"].iloc[:-1].to_numpy(),
        "dir_corr": seg["dir"].iloc[1:].to_numpy(),
    })

    ev = ev[ev["dir_imp"] != ev["dir_corr"]]
    ev = ev[np.isfinite(ev["ratio"]) & np.isfinite(ev["rel_dur"])]

    if len(ev) < 30:
        return None

    x = ev["ratio"].to_numpy(dtype=float)
    y = ev["rel_dur"].to_numpy(dtype=float)
    dirs = ev["dir_imp"].astype(str).to_numpy()

    res = _perm_test(x, y, dirs, rng)
    if res is None:
        return None

    obs, z, p, null_tb, null_sd = res

    return {
        "thong_ke": z,
        "p": p,
        "n": int(len(ev)),
        "quan_sat_tho": obs,
        "null_tb": null_tb,
        "null_sd": null_sd,
        "spearman_obs": float(-obs),
        "ghi_chu": (
            "Ty le body/range lay tai nen dao chieu cua chan xung (bar den). "
            "Thoi luong chan dieu chinh ke tiep duoc chia cho median truot 30 doan truoc "
            "(chi dung qua khu) de khu volatility clustering. "
            "Thong ke = -Spearman(ratio, rel_dur) nen duong ung ho khang dinh. "
            "Hoan vi 2000 lan, xao tron ratio trong tung huong de giu so su kien va ty le mua-ban; p hai phia. "
            "Tu dung doan tu cac chan da xac nhan, khong dung bc.cac_doan."
        ),
    }