import numpy as np
import pandas as pd
import brain_co_che as bc

def _tao_su_kien(doan, step=1):
    if doan is None or len(doan) < 5:
        return None
    d = doan.reset_index(drop=True).copy()
    if 'huong' not in d.columns:
        if 'do_dai' not in d.columns:
            return None
        d['huong'] = np.sign(d['do_dai']).astype(float)
    if 'thoi_luong' not in d.columns:
        if 'tu' in d.columns and 'den' in d.columns:
            if np.issubdtype(d['den'].dtype, np.datetime64):
                d['thoi_luong'] = (d['den'] - d['tu']).dt.days
            else:
                d['thoi_luong'] = (d['den'] - d['tu']).abs()
        else:
            return None
    if 'do_dai' not in d.columns:
        return None

    ds = []
    n = len(d)
    i = 0
    while i + 4 < n:
        seg = d.iloc[i:i+5]
        h = seg['huong'].values
        if (h[0] == h[2] == h[4]) and (h[1] != h[0]) and (h[3] != h[0]):
            len_first = abs(seg['do_dai'].values[0])
            len_last = abs(seg['do_dai'].values[4])
            dur_first = seg['thoi_luong'].values[0]
            dur_mid = seg['thoi_luong'].values[2]

            if isinstance(dur_first, (np.timedelta64, pd.Timedelta)):
                dur_first = dur_first / np.timedelta64(1, 'D')
            if isinstance(dur_mid, (np.timedelta64, pd.Timedelta)):
                dur_mid = dur_mid / np.timedelta64(1, 'D')

            dur_first = float(dur_first)
            dur_mid = float(dur_mid)

            if (np.isfinite(len_first) and np.isfinite(len_last) and
                np.isfinite(dur_first) and np.isfinite(dur_mid) and
                len_first > 0 and dur_first > 0):
                cond = bool(dur_mid > 1.5 * dur_first)
                outcome = bool(0.8 * len_first <= len_last <= 1.2 * len_first)
                ds.append({'cond': cond, 'outcome': outcome, 'huong': h[0]})
        i += step

    if len(ds) < 5:
        return None
    return pd.DataFrame(ds)


def do(khoa, df, rng):
    he_so_list = [3.0, 2.5, 2.0, 1.5, 1.2, 1.0, 0.8]
    best = None

    for hs in he_so_list:
        try:
            ch = bc.chan_song(df, he_so=hs)
            doan = bc.cac_doan(df, ch)
        except Exception:
            continue

        if doan is None or len(doan) < 5:
            continue

        for step in [5, 4, 3, 2, 1]:
            evs = _tao_su_kien(doan, step=step)
            if evs is None:
                continue
            n_cond = int(evs['cond'].sum())
            n_noncond = int((~evs['cond']).sum())
            if len(evs) >= 30 and n_cond >= 5 and n_noncond >= 5:
                best = (evs, hs, step)
                break

        if best is not None:
            break

    if best is None:
        return None

    events, hs, step = best

    outcome = events['outcome'].values.astype(bool)
    cond = events['cond'].values.astype(bool)
    huong = events['huong'].values
    n = len(events)
    n_cond = int(cond.sum())
    n_noncond = n - n_cond

    ty_le_cond = outcome[cond].mean()
    ty_le_noncond = outcome[~cond].mean()
    obs_diff = ty_le_cond - ty_le_noncond

    if np.isnan(obs_diff):
        return None

    n_perm = 2000
    null_diffs = np.empty(n_perm)
    huong_vals = np.unique(huong)

    for k in range(n_perm):
        perm_cond = cond.copy()
        for h_val in huong_vals:
            idx = huong == h_val
            perm_cond[idx] = rng.permutation(cond[idx])

        p1 = outcome[perm_cond].mean()
        p0 = outcome[~perm_cond].mean()
        null_diffs[k] = p1 - p0

    p_value = (np.sum(np.abs(null_diffs) >= np.abs(obs_diff)) + 1) / (n_perm + 1)
    null_tb = float(null_diffs.mean())
    null_sd = float(null_diffs.std(ddof=1))

    if null_sd == 0:
        return None

    thong_ke = (obs_diff - null_tb) / null_sd

    return {
        'thong_ke': thong_ke,
        'p': float(p_value),
        'n': n,
        'quan_sat_tho': float(obs_diff),
        'null_tb': null_tb,
        'null_sd': null_sd,
        'n_cond': n_cond,
        'n_noncond': n_noncond,
        'ty_le_cond': float(ty_le_cond),
        'ty_le_noncond': float(ty_le_noncond),
        'he_so': hs,
        'step': step,
        'ghi_chu': (
            f'Sự kiện: chuỗi 5 đoạn zigzag liên tiếp, ba đoạn i, i+2, i+4 cùng hướng. '
            f'Điều kiện: thoi_luong(i+2) > 1.5 * thoi_luong(i). '
            f'Outcome: abs(do_dai(i+4)) trong [0.8, 1.2] * abs(do_dai(i)). '
            f'Hoán vị nhãn điều kiện, phân tầng theo hướng up/down, giữ nguyên outcome, '
            f'số sự kiện và số điều kiện trong mỗi hướng. '
            f'Zigzag he_so={hs}, bước lấy mẫu step={step}. '
            f'Thống kê dương = tỷ lệ outcome ở nhóm có điều kiện cao hơn -> ủng hộ khẳng định.'
        )
    }