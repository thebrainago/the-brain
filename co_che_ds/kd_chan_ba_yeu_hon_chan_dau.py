import numpy as np
import pandas as pd
import brain_co_che as bc

HE_SO = 2.0          # ha nguong de du mau, ghi ro trong ghi_chu
N_PERM = 2000
MIN_N = 30
MIN_GROUP = 5


def _pos(df, x):
    """Chuyen vi tri tu cac cot tu/den thanh index integer."""
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, float) and np.isfinite(x) and float(x).is_integer():
        return int(x)
    return int(df.index.get_loc(x))


def _huong(x):
    """Doc cot huong dang so hoac chu."""
    if isinstance(x, (int, float, np.integer, np.floating)):
        return 1 if float(x) > 0 else -1 if float(x) < 0 else 0
    s = str(x).strip().lower()
    if s in ("up", "1", "+1", "uptrend"):
        return 1
    if s in ("down", "-1", "downtrend"):
        return -1
    return 0


def do(khoa, df, rng):
    ch = bc.chan_song(df, he_so=HE_SO)
    if ch is None or len(ch) < 8:
        return None

    doan = bc.cac_doan(df, ch)
    if doan is None or len(doan) < 8:
        return None

    try:
        doan = doan.sort_values("tu")
    except Exception:
        pass
    doan = doan.reset_index(drop=True)

    atr_df = bc.atr(df, 14)
    if isinstance(atr_df, pd.DataFrame):
        atr = atr_df.iloc[:, 0].astype(float)
    else:
        atr = pd.Series(atr_df, index=df.index).astype(float)

    n = len(doan)
    huong = np.zeros(n, dtype=int)
    norm_len = np.full(n, np.nan)
    thoi_luong = np.full(n, np.nan)
    dir_pos = {1: [], -1: []}

    for i in range(n):
        r = doan.iloc[i]
        h = _huong(r["huong"])
        huong[i] = h
        if h == 0:
            continue
        dir_pos[h].append(i)

        try:
            tu = _pos(df, r["tu"])
            den = _pos(df, r["den"])
            dd = float(r["do_dai"])
            tl = float(r["thoi_luong"])
            if tu >= den or not np.isfinite(dd) or not np.isfinite(tl):
                continue
            a = float(atr.iloc[tu])
            if not np.isfinite(a) or a <= 1e-12:
                continue
            norm_len[i] = abs(dd) / a
            thoi_luong[i] = tl
        except Exception:
            continue

    events = []

    for d in (1, -1):
        pos = dir_pos[d]
        if len(pos) < 3:
            continue

        # Moi cum: ba con song cung huong gan nhau nhat (i_first, i_giua, i_third)
        # i_first = pos[k-2], i_third = pos[k]
        for k in range(2, len(pos)):
            i_first = pos[k - 2]
            i_third = pos[k]

            # Con song dao chieu ngay sau con song thu ba
            i_rev = i_third + 1
            if i_rev >= n:
                continue
            if huong[i_rev] != -d:
                continue

            len1 = norm_len[i_first]
            len3 = norm_len[i_third]
            dur = thoi_luong[i_rev]

            if not np.isfinite(len1) or not np.isfinite(len3) or not np.isfinite(dur):
                continue
            if len1 <= 0 or len3 <= 0:
                continue
            if abs(len3 - len1) < 1e-12:
                continue

            label = 1 if len3 < len1 else 0
            events.append((label, float(dur), d))

    if len(events) < MIN_N:
        return None

    labels = np.array([e[0] for e in events], dtype=int)
    durs = np.array([e[1] for e in events], dtype=float)
    strata = np.array([1 if e[2] == 1 else 0 for e in events], dtype=int)

    n_short = int(labels.sum())
    n_long = int(len(labels) - n_short)
    if n_short < MIN_GROUP or n_long < MIN_GROUP:
        return None

    obs = durs[labels == 1].mean() - durs[labels == 0].mean()
    if not np.isfinite(obs):
        return None

    nulls = np.empty(N_PERM)
    for b in range(N_PERM):
        perm_labels = labels.copy()
        for s in np.unique(strata):
            idx = np.where(strata == s)[0]
            if len(idx) > 1:
                perm_labels[idx] = rng.permutation(labels[idx])

        mean_short = durs[perm_labels == 1].mean()
        mean_long = durs[perm_labels == 0].mean()
        if np.isfinite(mean_short) and np.isfinite(mean_long):
            nulls[b] = mean_short - mean_long
        else:
            nulls[b] = 0.0

    null_tb = float(np.mean(nulls))
    null_sd = float(np.std(nulls, ddof=1))
    if not np.isfinite(null_sd) or null_sd <= 1e-12:
        return None

    thong_ke = (obs - null_tb) / null_sd
    p = float((np.sum(np.abs(nulls) >= abs(obs)) + 1.0) / (N_PERM + 1.0))

    return {
        "thong_ke": thong_ke,
        "p": p,
        "n": len(events),
        "quan_sat_tho": float(obs),
        "null_tb": null_tb,
        "null_sd": null_sd,
        "n_short": n_short,
        "n_long": n_long,
        "he_so": HE_SO,
        "ghi_chu": (
            "Ha nguong chan_song xuong 2.0 ATR de du mau. "
            "Do dai gia cac con song duoc chuan hoa bang ATR14 tai diem bat dau song "
            "(tuan thu luat 4). Hoan vi nhan cum trong tung phan lop huong up/down "
            "de giu so su kien, ty le short/long va phoi nhiem theo huong. "
            "Doi voi du lieu lich su, bo tim chan co the ve lai khi co bar moi, "
            "nen ket qua phan anh cac cum da hoan tat."
        ),
    }