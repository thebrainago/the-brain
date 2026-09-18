import numpy as np
import pandas as pd


def _fractal_swings(df, right):
    h = df['high'].to_numpy(dtype=float)
    l = df['low'].to_numpy(dtype=float)
    n = len(df)
    rows = []

    for i in range(right, n - right):
        left_h = h[i - right:i]
        right_h = h[i + 1:i + right + 1]
        if h[i] > left_h.max() and h[i] > right_h.max():
            rows.append((i, i + right, h[i], 'dinh'))

        left_l = l[i - right:i]
        right_l = l[i + 1:i + right + 1]
        if l[i] < left_l.min() and l[i] < right_l.min():
            rows.append((i, i + right, l[i], 'day'))

    if not rows:
        return None

    sw = pd.DataFrame(rows, columns=['vi_tri', 'xac_nhan', 'gia', 'loai'])
    sw = sw.sort_values('vi_tri').reset_index(drop=True)
    sw = sw.drop_duplicates(subset='vi_tri', keep='first')

    # Đảm bảo đỉnh/day xen kẽ. Nếu cùng loại liên tiếp, giữ cái đầu tiên.
    filtered = []
    for _, r in sw.iterrows():
        if not filtered or r['loai'] != filtered[-1]['loai']:
            filtered.append(r)

    if len(filtered) < 4:
        return None

    return pd.DataFrame(filtered).reset_index(drop=True)


def _lay_cap(ch):
    ch = ch.copy()
    for col in ['vi_tri', 'xac_nhan', 'gia']:
        ch[col] = pd.to_numeric(ch[col], errors='coerce')
    ch = ch.dropna(subset=['vi_tri', 'xac_nhan', 'gia'])
    if len(ch) < 4:
        return None, None

    ch['vi_tri'] = ch['vi_tri'].astype(int)
    ch['xac_nhan'] = ch['xac_nhan'].astype(int)
    ch = ch.sort_values('vi_tri').reset_index(drop=True)

    if 'loai' in ch.columns:
        loai = ch['loai'].astype(str).str.lower()
        highs = ch[loai.isin(['dinh', 'peak', 'high', 'swing_high', 'đỉnh'])].copy()
        lows = ch[loai.isin(['day', 'trough', 'low', 'swing_low', 'đáy'])].copy()
        if len(highs) >= 2 and len(lows) >= 1:
            return highs.reset_index(drop=True), lows.reset_index(drop=True)

    # Fallback: tự phân loại đỉnh/day từ danh sách swing.
    g = ch['gia'].to_numpy(dtype=float)
    types = []
    for i in range(len(ch)):
        if i == 0:
            typ = 'day' if g[1] > g[0] else 'dinh'
        elif i == len(ch) - 1:
            typ = 'day' if g[-2] > g[-1] else 'dinh'
        else:
            if g[i] >= g[i - 1] and g[i] >= g[i + 1]:
                typ = 'dinh'
            elif g[i] <= g[i - 1] and g[i] <= g[i + 1]:
                typ = 'day'
            else:
                typ = None
        types.append(typ)

    ch['loai_fb'] = types
    highs = ch[ch['loai_fb'] == 'dinh'].copy()
    lows = ch[ch['loai_fb'] == 'day'].copy()

    if len(highs) >= 2 and len(lows) >= 1:
        return highs.reset_index(drop=True), lows.reset_index(drop=True)

    return None, None


def _collect_with_swings(sw, df, max_wait=15, H=10):
    highs, lows = _lay_cap(sw)
    if highs is None or lows is None:
        return None

    events = []
    outcomes = []
    vol_ratios = []

    for i in range(1, len(highs)):
        cur = highs.iloc[i]
        prev = highs.iloc[i - 1]

        cur_pos = int(cur['vi_tri'])
        cur_conf = int(cur['xac_nhan'])
        cur_gia = float(cur['gia'])
        prev_gia = float(prev['gia'])

        if cur_gia <= prev_gia:
            continue

        lows_before = lows[lows['vi_tri'] < cur_pos]
        if len(lows_before) == 0:
            continue

        low = lows_before.iloc[-1]
        low_pos = int(low['vi_tri'])
        low_gia = float(low['gia'])

        if low_pos >= cur_pos or low_gia >= cur_gia:
            continue

        leg = cur_gia - low_gia
        if leg <= 0:
            continue

        mid = cur_gia - 0.5 * leg

        avg_vol = df['volume'].iloc[low_pos:cur_pos + 1].mean()
        if not np.isfinite(avg_vol) or avg_vol <= 0:
            continue

        # Bar giảm đầu tiên sau đỉnh.
        t = None
        end_search = min(cur_pos + 1 + max_wait, len(df))
        for k in range(cur_pos + 1, end_search):
            if df['close'].iloc[k] < df['open'].iloc[k]:
                t = k
                break

        if t is None:
            continue

        vol_ratio = float(df['volume'].iloc[t]) / float(avg_vol)
        if not np.isfinite(vol_ratio):
            continue

        known_at = max(int(t), cur_conf)
        if known_at + H >= len(df):
            continue

        future_low = df['low'].iloc[known_at + 1: known_at + H + 1].min()
        if not np.isfinite(future_low):
            continue

        outcome = bool(future_low < mid)   # retrace hơn nửa chân tăng
        event = bool(vol_ratio >= 1.5)     # volume gấp rưỡi KLTB chân tăng

        events.append(event)
        outcomes.append(outcome)
        vol_ratios.append(vol_ratio)

    if len(events) < 30:
        return None

    ev = np.asarray(events, dtype=bool)
    ou = np.asarray(outcomes, dtype=bool)
    n_ev = int(ev.sum())

    if n_ev < 30:
        return None

    return {
        'ev': ev,
        'ou': ou,
        'n_ev': n_ev,
        'n_candidates': len(ev),
        'vol_ratios': np.asarray(vol_ratios, dtype=float),
    }


def do(khoa, df, rng):
    collected = None
    right_used = None

    # Chọn right theo SỐ MẪU, không theo kết quả.
    for right in [4, 3, 2, 1]:
        sw = _fractal_swings(df, right)
        if sw is None:
            continue

        res = _collect_with_swings(sw, df, max_wait=15, H=10)
        if res is not None:
            collected = res
            right_used = right
            break

    if collected is None:
        return None

    events = collected['ev']
    outcomes = collected['ou']
    n_events = collected['n_ev']

    observed = float(outcomes[events].mean())

    n_perm = 2000
    perm_stats = np.empty(n_perm)

    for b in range(n_perm):
        perm_ev = rng.permutation(events)
        perm_stats[b] = float(outcomes[perm_ev].mean())

    null_tb = float(perm_stats.mean())
    null_sd = float(perm_stats.std(ddof=1)) if n_perm > 1 else 0.0

    if null_sd > 0:
        thong_ke = (observed - null_tb) / null_sd
    else:
        thong_ke = 0.0

    p = float((1 + np.sum(perm_stats >= observed)) / (1 + n_perm))

    return {
        'thong_ke': thong_ke,
        'p': p,
        'n': n_events,
        'quan_sat_tho': observed,
        'null_tb': null_tb,
        'null_sd': null_sd,
        'ty_le_nen': float(outcomes.mean()),
        'n_ung_vien': collected['n_candidates'],
        'right_swing': right_used,
        'vol_trung_binh_su_kien': float(collected['vol_ratios'][events].mean()),
        'de_xuat': 'Thu ket hop volume gap doi va do doc chan tang de loc manh hon.',
        'ghi_chu': (
            'Dinh/day swing tu fractal tu viet, KHONG dung bc.chan_song de tranh thieu mau; '
            'dinh i duoc xac nhan tai i+right, right la do nhin sang phai. '
            'Su kien: dinh cao hon dinh swing truoc, bar giam dau tien trong 15 bar sau dinh '
            'co close<open va volume >= 1.5 * KLTB chan tang (tu day swing truoc den dinh). '
            'Outcome: low trong 10 bar sau max(bar giam dau tien, xac_nhan) < mid, tuc retrace > 1/2 chan tang. '
            'Hoan vi shuffle nhan event giua cac ung vien, giu nguyen so event. '
            'Null la ti le retrace > 1/2 trong tap cac dinh cao hon dinh truoc, khong phai 0.5. '
            'Quy uoc thong_ke duong = ung ho khang dinh. '
            'Retracement da chuan hoa theo do dai chan tang; volume da chuan hoa theo KLTB chan tang.'
        ),
    }