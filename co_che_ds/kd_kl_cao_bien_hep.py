import numpy as np
import pandas as pd


def do(khoa, df, rng):
    vol = df['volume'].to_numpy(dtype=float)
    high = df['high'].to_numpy(dtype=float)
    low = df['low'].to_numpy(dtype=float)
    n = len(df)

    if n < 22:
        return None

    amp = high - low

    # MA20 cua 20 phien TRUOC do, khong tinh phien hien tai.
    vol_ma = df['volume'].rolling(20, min_periods=20).mean().shift(1).to_numpy(dtype=float)
    amp_ma = pd.Series(amp).rolling(20, min_periods=20).mean().shift(1).to_numpy(dtype=float)

    idx = np.arange(n)

    # Phien i hop le neu co du 20 phien qua khu, con phien i+1 de tinh ket cuc.
    next_ok = np.full(n, False)
    next_ok[:-1] = np.isfinite(vol[1:])

    valid = (
        (idx >= 20)
        & (idx < n - 1)
        & next_ok
        & np.isfinite(vol)
        & np.isfinite(amp)
        & np.isfinite(vol_ma)
        & np.isfinite(amp_ma)
        & (vol_ma > 0)
        & (amp_ma > 0)
        & (amp >= 0)
    )

    # Su kien: volume >= 2*MA20(volume) va high-low <= 0.5*MA20(high-low)
    signal = valid & (vol >= 2.0 * vol_ma) & (amp <= 0.5 * amp_ma)
    event_idx = np.flatnonzero(signal)
    n_event = event_idx.size

    if n_event < 30:
        return None

    # Ket cuc: volume phien ke tiep thap hon volume phien tin hieu.
    obs = float(np.mean(vol[event_idx + 1] < vol[event_idx]))

    candidate_idx = np.flatnonzero(valid)
    n_perm = 2000
    perm_stats = np.empty(n_perm, dtype=float)

    for b in range(n_perm):
        s = rng.choice(candidate_idx, size=n_event, replace=False)
        perm_stats[b] = np.mean(vol[s + 1] < vol[s])

    null_mean = float(perm_stats.mean())
    null_sd = float(perm_stats.std(ddof=1))

    if null_sd > 0:
        thong_ke = (obs - null_mean) / null_sd
    else:
        thong_ke = 0.0

    # Hoan vi 1 phia: ngau nhien gan nhan "su kien" len cac ngay hop le,
    # giu nguyen so su kien va ty le nen cua toan bo mau.
    p = float((np.sum(perm_stats >= obs) + 1.0) / (n_perm + 1.0))

    return {
        "thong_ke": thong_ke,
        "p": p,
        "n": int(n_event),
        "quan_sat_tho": obs,
        "null_tb": null_mean,
        "null_sd": null_sd,
        "dieu_kien": "volume >= 2*MA20(volume) va high-low <= 0.5*MA20(high-low), MA20 tinh tren 20 phien truoc do",
        "ket_cuc": "volume phien ke tiep < volume phien tin hieu",
        "ghi_chu": "Hoan vi gan nhan su kien tren cac ngay hop le, giu nguyen so su kien. thong_ke = (quan_sat - null_tb)/null_sd, duong ung ho khang dinh.",
    }