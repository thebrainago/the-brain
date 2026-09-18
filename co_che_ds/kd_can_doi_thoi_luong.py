import numpy as np
import pandas as pd


def do(khoa, df, rng):
    try:
        import brain_co_che as bc
    except Exception:
        return None

    try:
        ch = bc.chan_song(df)
        if ch is None or len(ch) < 4:
            return None
        legs = bc.cac_doan(df, ch)
        if legs is None or len(legs) < 3:
            return None
    except Exception:
        return None

    legs = legs.reset_index(drop=True)

    try:
        tu = pd.to_numeric(legs["tu"], errors="coerce").to_numpy(dtype=float)
        den = pd.to_numeric(legs["den"], errors="coerce").to_numpy(dtype=float)
        dur = pd.to_numeric(legs["thoi_luong"], errors="coerce").to_numpy(dtype=float)
        amp = pd.to_numeric(legs["do_dai"], errors="coerce").to_numpy(dtype=float)
        bt = pd.to_numeric(legs["biet_tai"], errors="coerce").to_numpy(dtype=float)
    except Exception:
        return None

    huong = None
    if "huong" in legs.columns:
        try:
            huong = pd.to_numeric(legs["huong"], errors="coerce").to_numpy(dtype=float)
        except Exception:
            huong = None
        if huong is not None and not np.any(np.isfinite(huong)):
            huong = None

    try:
        atr = bc.atr(df, 14)
        if atr is None:
            return None
        if isinstance(atr, pd.DataFrame):
            atr = atr.iloc[:, 0]
        if not isinstance(atr, pd.Series):
            atr = pd.Series(atr, index=df.index)
        atr = atr.reindex(df.index)
    except Exception:
        return None

    n_legs = len(legs)
    events = []

    for i in range(1, n_legs - 1):
        # Ba chan lien tiep: dieu chinh -> day -> dieu chinh
        if not (den[i - 1] == tu[i] and den[i] == tu[i + 1]):
            continue

        if huong is not None:
            h0, h1, h2 = huong[i - 1], huong[i], huong[i + 1]
            if not (np.isfinite(h0) and np.isfinite(h1) and np.isfinite(h2)):
                continue
            if not (h1 == -h0 and h2 == h0):
                continue

        d_left = dur[i - 1]
        d_right = dur[i + 1]
        a = amp[i]
        t_mid = bt[i]
        t_event = bt[i + 1]

        if not (
            np.isfinite(d_left)
            and np.isfinite(d_right)
            and np.isfinite(a)
            and np.isfinite(t_mid)
            and np.isfinite(t_event)
        ):
            continue

        if d_left <= 0 or d_right <= 0 or a <= 0:
            continue

        try:
            vol = atr.iloc[int(t_mid)]
        except Exception:
            continue

        if not np.isfinite(vol) or vol <= 0:
            continue

        # Lenh nhau khong qua 20% so voi chan ngan hon
        similar = abs(d_left - d_right) <= 0.2 * min(d_left, d_right)

        events.append((float(t_event), a / vol, bool(similar)))

    if len(events) < 30:
        return None

    events = np.array(
        events, dtype=[("t", float), ("amp", float), ("sim", bool)]
    )
    amps = events["amp"]
    labels = events["sim"].astype(int)

    n_sim = int(labels.sum())
    n_diff = len(events) - n_sim
    if n_sim < 10 or n_diff < 10:
        return None

    obs = amps[labels == 1].mean() - amps[labels == 0].mean()
    if not np.isfinite(obs):
        return None

    rng_local = rng if rng is not None else np.random.default_rng()

    n_perm = 2000
    perm_stats = np.empty(n_perm, dtype=float)

    for b in range(n_perm):
        lab = rng_local.permutation(labels)
        m_sim = amps[lab == 1].mean()
        m_diff = amps[lab == 0].mean()
        perm_stats[b] = m_sim - m_diff

    null_tb = float(perm_stats.mean())
    null_sd = float(perm_stats.std(ddof=1))

    if null_sd == 0:
        thong_ke = 0.0
    else:
        thong_ke = float((obs - null_tb) / null_sd)

    p = float((np.sum(perm_stats >= obs) + 1) / (n_perm + 1))

    return {
        "thong_ke": thong_ke,
        "p": p,
        "n": int(len(events)),
        "quan_sat_tho": float(obs),
        "null_tb": null_tb,
        "null_sd": null_sd,
        "n_sim": n_sim,
        "n_diff": n_diff,
        "khoa": khoa,
        "ghi_chu": (
            "Do bien do chan day chia ATR(14) tai thoi diem xac nhan chan day. "
            "Hai chan dieu chinh 'giong nhau' neu |d1-d2| <= 0.2*min(d1,d2). "
            "Hoan vi xao nhan similar/different giu nguyen so su kien moi nhom. "
            "Duong = ung ho khang dinh (chan day co bien do lon hon khi hai chan "
            "dieu chinh co thoi luong gan nhau)."
        ),
        "de_xuat": (
            "Thu ghep dieu kien huong cua chan day so voi xuat huong dai han "
            "hoac phan vi ATR de loc bot nhieu."
        ),
    }