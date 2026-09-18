import numpy as np
import pandas as pd
import brain_co_che as bc


def _tao_rows(df, he_so):
    try:
        ch = bc.chan_song(df, he_so=he_so)
    except TypeError:
        try:
            ch = bc.chan_song(df)
        except Exception:
            return None
    except Exception:
        return None

    if ch is None or len(ch) < 3:
        return None

    try:
        legs = bc.cac_doan(df, ch)
    except Exception:
        return None

    if legs is None or len(legs) < 2:
        return None

    o = df['open'].to_numpy(dtype=float)
    c = df['close'].to_numpy(dtype=float)
    h = df['high'].to_numpy(dtype=float)
    l = df['low'].to_numpy(dtype=float)

    atr_ser = bc.atr(df, 14)
    atr_arr = np.asarray(atr_ser, dtype=float).ravel()

    body = np.abs(c - o)
    day_range = h - l
    small = (body < 0.1 * day_range) & (day_range > 0)

    tu_arr = pd.to_numeric(legs['tu'], errors='coerce').to_numpy(dtype=float)
    den_arr = pd.to_numeric(legs['den'], errors='coerce').to_numpy(dtype=float)
    biet_arr = pd.to_numeric(legs['biet_tai'], errors='coerce').to_numpy(dtype=float)

    rows = []

    for i in range(len(legs)):
        a = tu_arr[i]
        b = den_arr[i]
        j = biet_arr[i]

        if not (np.isfinite(a) and np.isfinite(b) and np.isfinite(j)):
            continue

        a = int(a)
        b = int(b)
        j = int(j)

        lo = min(a, b)
        hi = max(a, b)

        if lo < 0 or hi >= len(h) or hi - lo + 1 < 2:
            continue

        n_candles = hi - lo + 1
        n_small = int(small[lo:hi + 1].sum())
        frac_nen_nho = n_small / n_candles

        amp = float(h[lo:hi + 1].max() - l[lo:hi + 1].min())

        if j < 0 or j >= len(atr_arr):
            continue

        atr_val = float(atr_arr[j])
        if not np.isfinite(atr_val) or atr_val <= 0:
            continue

        rows.append({
            'amp': amp,
            'atr': atr_val,
            'frac_nen_nho': frac_nen_nho,
            'comp': frac_nen_nho > 1.0 / 3.0,
        })

    return rows


def do(khoa, df, rng):
    rows = None
    used_he_so = None

    # Ha nguong chi khi can du so mau, khong chon theo ket qua.
    for he_so in (3.0, 2.5, 2.0, 1.75, 1.5, 1.25, 1.0):
        r = _tao_rows(df, he_so)
        if not r:
            continue

        comp = np.array([x['comp'] for x in r], dtype=bool)
        if len(comp) < 2:
            continue

        pair_events = int(comp[:-1].sum())
        if pair_events >= 30:
            rows = r
            used_he_so = he_so
            break

    if rows is None or used_he_so is None:
        return None

    comp = np.array([x['comp'] for x in rows], dtype=bool)
    amp = np.array([x['amp'] for x in rows], dtype=float)
    atr = np.array([x['atr'] for x in rows], dtype=float)

    if len(amp) < 2:
        return None

    # d_i = muc vuot bien do cua chan sau so voi chan truoc,
    # chia cho ATR tai thoi diem biet chan hien tai.
    d = (amp[1:] - amp[:-1]) / atr[:-1]

    mask = comp[:-1]
    n_events = int(mask.sum())
    n_pairs = len(d)

    if n_events < 30 or n_events == n_pairs or n_pairs < 30:
        return None

    obs = float(d[mask].mean())

    n_perm = 2000
    perm_means = np.empty(n_perm, dtype=float)

    for b in range(n_perm):
        idx = rng.permutation(n_pairs)[:n_events]
        perm_means[b] = float(d[idx].mean())

    null_tb = float(perm_means.mean())
    null_sd = float(perm_means.std(ddof=1)) if n_perm > 1 else 0.0

    if null_sd > 0:
        thong_ke = (obs - null_tb) / null_sd
    else:
        thong_ke = 0.0

    p = (1.0 + float(np.sum(perm_means >= obs))) / (n_perm + 1.0)

    return {
        "thong_ke": float(thong_ke),
        "p": float(p),
        "n": int(n_events),
        "quan_sat_tho": float(obs),
        "null_tb": null_tb,
        "null_sd": null_sd,
        "he_so": float(used_he_so),
        "n_pairs": int(n_pairs),
        "ghi_chu": (
            "Bien do chan song = max(high) - min(low) giua hai diem song. "
            "Dieu kien nen: phan so nen co |close-open| < 0.1*(high-low) trong chan > 1/3. "
            "Thong ke = (amp_next - amp_cur)/ATR_cur, ATR_cur lay tai bar xac nhan cua chan hien tai. "
            "Hoan vi nhan 'nen' tren cac vi tri chan co chan sau, giu nguyen so su kien va giu nguyen chuoi d; "
            "p mot phia, H1: bien do chan sau lon hon chan truoc. "
            "Da chon he_so=" + str(used_he_so) + " theo so mau >=30, khong theo ket qua."
        ),
        "de_xuat": (
            "Thu phan tang theo muc nen (ty le nen nho >40%, >50%) de xem "
            "nen sau co bu bien do manh hon khong."
        ),
    }