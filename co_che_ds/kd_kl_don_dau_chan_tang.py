import numpy as np
import math
import brain_co_che as bc


def _doan_toa_do(doan, ch):
    tu = doan['tu'].to_numpy(dtype=int)
    den = doan['den'].to_numpy(dtype=int)
    vt = ch['vi_tri'].to_numpy(dtype=int)
    gia = ch['gia'].to_numpy(dtype=float)

    if len(tu) == 0:
        return tu, den, vt, gia

    # Neu tu/den la chi so dong lien tiep trong ch
    if den.max() < len(ch) and np.all((den - tu) == 1):
        return vt[tu], vt[den], vt, gia

    # Nguoc lai, tu/den da la vi tri that trong df
    return tu, den, vt, gia


def _volume_condition(df, s, e):
    s = int(s)
    e = int(e)
    L = e - s + 1

    if L < 4:
        return False
    if s < 0 or e >= len(df):
        return False

    seg = df.iloc[s:e + 1]
    vol = seg['volume'].to_numpy(dtype=float)
    total = float(np.nansum(vol))

    if total <= 0 or not np.isfinite(total):
        return False

    nua_dau = int(math.ceil(L / 2))
    return float(np.nansum(vol[:nua_dau])) / total > 0.70


def _norm_amp(df, atr, s, e):
    s = int(s)
    e = int(e)

    if s < 0 or e >= len(df) or s > e:
        return np.nan

    seg = df.iloc[s:e + 1]
    high = seg['high'].to_numpy(dtype=float)
    low = seg['low'].to_numpy(dtype=float)
    amp = float(np.nanmax(high) - np.nanmin(low))

    nat = float(atr[s])
    if not np.isfinite(amp) or not np.isfinite(nat) or amp <= 0 or nat <= 0:
        return np.nan

    return amp / nat


def _lay_mau(df, atr, he_so):
    try:
        ch = bc.chan_song(df, he_so=he_so)
        if ch is None or len(ch) < 5:
            return None

        ch = ch.reset_index(drop=True)
        doan = bc.cac_doan(df, ch)

        if doan is None or len(doan) < 3:
            return None
    except Exception:
        return None

    tu_pos, den_pos, vt, gia_arr = _doan_toa_do(doan, ch)
    pos_to_gia = dict(zip(vt, gia_arr))

    y = []
    ev = []

    for i in range(1, len(doan) - 1):
        # Chan giua phai la chan tang
        tu0 = int(tu_pos[i])
        den0 = int(den_pos[i])

        if tu0 >= den0:
            continue

        p0 = pos_to_gia.get(tu0)
        p1 = pos_to_gia.get(den0)

        if p0 is None or p1 is None:
            continue
        if not (np.isfinite(p0) and np.isfinite(p1)):
            continue
        if p1 <= p0:
            continue

        # Chan truoc phai la chan giam
        tup = int(tu_pos[i - 1])
        denp = int(den_pos[i - 1])

        if tup >= denp:
            continue

        p0p = pos_to_gia.get(tup)
        p1p = pos_to_gia.get(denp)

        if p0p is None or p1p is None:
            continue
        if not (np.isfinite(p0p) and np.isfinite(p1p)):
            continue
        if p1p >= p0p:
            continue

        # Chan sau phai la chan giam
        tun = int(tu_pos[i + 1])
        denn = int(den_pos[i + 1])

        if tun >= denn:
            continue

        p0n = pos_to_gia.get(tun)
        p1n = pos_to_gia.get(denn)

        if p0n is None or p1n is None:
            continue
        if not (np.isfinite(p0n) and np.isfinite(p1n)):
            continue
        if p1n >= p0n:
            continue

        # Cac doan phai dung chung dinh/day
        if denp != tu0 or den0 != tun:
            continue

        cond = _volume_condition(df, tu0, den0)

        amp_prev = _norm_amp(df, atr, tup, denp)
        amp_next = _norm_amp(df, atr, tun, denn)

        if not np.isfinite(amp_prev) or not np.isfinite(amp_next):
            continue

        y.append(float(amp_next - amp_prev))
        ev.append(bool(cond))

    if len(y) < 30:
        return None

    y = np.asarray(y, dtype=float)
    ev = np.asarray(ev, dtype=bool)

    if ev.sum() < 30 or (~ev).sum() < 5:
        return None

    return y, ev, he_so


def do(khoa, df, rng):
    atr_raw = bc.atr(df, 14)

    if hasattr(atr_raw, "to_numpy"):
        atr = atr_raw.to_numpy(dtype=float).ravel()
    else:
        atr = np.asarray(atr_raw, dtype=float).ravel()

    if len(atr) != len(df):
        return None

    mau = None

    for he_so in [3.0, 2.0, 1.5, 1.2, 1.0]:
        mau = _lay_mau(df, atr, he_so)
        if mau is not None:
            break

    if mau is None:
        return None

    y, ev, nguong = mau
    n = len(y)
    k = int(ev.sum())

    if k < 30 or n - k < 5:
        return None

    obs = float(y[ev].mean() - y[~ev].mean())

    n_perm = 2000
    null_stats = np.empty(n_perm, dtype=float)

    for b in range(n_perm):
        idx = rng.permutation(n)
        mask = np.zeros(n, dtype=bool)
        mask[idx[:k]] = True
        null_stats[b] = float(y[mask].mean() - y[~mask].mean())

    null_tb = float(null_stats.mean())
    null_sd = float(null_stats.std(ddof=1))

    if null_sd <= 0 or not np.isfinite(null_sd):
        return None

    thong_ke = float((obs - null_tb) / null_sd)
    p = float((1 + int(np.sum(null_stats >= obs))) / (n_perm + 1))

    return {
        "thong_ke": thong_ke,
        "p": p,
        "n": k,
        "quan_sat_tho": obs,
        "null_tb": null_tb,
        "null_sd": null_sd,
        "nguong_chan": nguong,
        "ghi_chu": (
            f"Zigzag nguong={nguong}xATR. "
            "Nua dau = ceil(L/2) phien. "
            "Bien do chuan hoa = range(high-low)/ATR(14) tai diem bat dau chan giam. "
            "p mot phia (duoi phai); hoan vi nhan su kien, giu nguyen so su kien, "
            "khong hoan vi loi suat."
        ),
    }