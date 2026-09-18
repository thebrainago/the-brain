import numpy as np
import pandas as pd
import brain_co_che as bc

# ---------- helpers ----------
def _to_int_pos(df, value):
    """Chuyển value (label hoặc position) về vị trí số nguyên trong df, hoặc None."""
    if value is None:
        return None
    # Nếu value là int, coi là position (an toàn hơn cho index không phải RangeIndex)
    if isinstance(value, (int, np.integer)):
        v = int(value)
        if 0 <= v < len(df):
            return v
        # Nếu ngoài khoảng, thử coi là label
        try:
            if v in df.index:
                return df.index.get_loc(v)
        except Exception:
            pass
        return None
    # Nếu không phải int, coi là label
    try:
        if value in df.index:
            return df.index.get_loc(value)
    except Exception:
        pass
    # Thử ép int
    try:
        v = int(value)
        if 0 <= v < len(df):
            return v
    except Exception:
        pass
    return None

def _atr_series(df, period=14):
    try:
        return bc.atr(df, period)
    except Exception:
        high = df['high']
        low = df['low']
        close = df['close']
        prev_close = close.shift(1)
        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs()
        ], axis=1).max(axis=1)
        return tr.rolling(period).mean()

def _dir_value(x):
    if isinstance(x, str):
        return 1 if x.lower().startswith('u') else -1
    try:
        return 1 if float(x) > 0 else -1
    except Exception:
        return 1

# ---------- main ----------
def do(khoa, df, rng):
    ch = bc.chan_song(df)
    if ch is None or len(ch) < 6:
        return None

    # Build segments
    doan = None
    try:
        doan = bc.cac_doan(df, ch)
    except Exception:
        doan = None

    if doan is None or len(doan) < 6:
        # Manual build from ch
        rows = []
        for i in range(len(ch) - 1):
            a = ch.iloc[i]
            b = ch.iloc[i+1]
            pos_a = _to_int_pos(df, a['vi_tri'])
            pos_b = _to_int_pos(df, b['vi_tri'])
            pos_xn = _to_int_pos(df, b['xac_nhan'])
            if pos_a is None or pos_b is None or pos_xn is None:
                continue
            gia_a = a['gia']
            gia_b = b['gia']
            do_dai = abs(float(gia_b) - float(gia_a))
            huong = 1 if gia_b > gia_a else -1
            rows.append({
                'tu': a['vi_tri'],
                'den': b['vi_tri'],
                'biet_tai': b['xac_nhan'],
                'do_dai': do_dai,
                'huong': huong,
                'pos_biet': pos_xn
            })
        if len(rows) < 6:
            return None
        doan = pd.DataFrame(rows)

    # Ensure pos_biet column
    if 'pos_biet' not in doan.columns:
        doan['pos_biet'] = doan['biet_tai'].apply(lambda v: _to_int_pos(df, v))

    # Compute normalized length
    atr = _atr_series(df, 14)
    len_norms = []
    for _, row in doan.iterrows():
        pos = row.get('pos_biet')
        if pos is None:
            len_norms.append(np.nan)
            continue
        try:
            a_val = atr.iloc[pos]
        except Exception:
            a_val = np.nan
        if a_val is not None and a_val > 0 and not np.isnan(a_val):
            len_norms.append(abs(row['do_dai']) / a_val)
        else:
            len_norms.append(np.nan)
    doan['len_norm'] = len_norms

    doan_valid = doan.dropna(subset=['len_norm']).reset_index(drop=True)
    if len(doan_valid) < 6:
        return None

    # Direction
    doan_valid['dir'] = doan_valid['huong'].apply(_dir_value)

    # Tìm cặp với ngưỡng percentile giảm dần, yêu cầu tối thiểu 10 cặp
    pairs = []
    threshold = None
    pct = None
    for p in [90, 85, 80, 75, 70, 65, 60, 55, 50]:
        thr = np.percentile(doan_valid['len_norm'], p)
        long_idx = doan_valid.index[doan_valid['len_norm'] > thr].tolist()
        cand = []
        for i in long_idx:
            if i + 2 < len(doan_valid) and doan_valid['dir'][i] == doan_valid['dir'][i+2]:
                cand.append(i)
        if len(cand) >= 10:
            pairs = cand
            threshold = thr
            pct = p
            break

    if len(pairs) < 10:
        return None

    # ---- Phần 1: độ dài chân cùng chiều kế tiếp ----
    obs_len_sau = doan_valid['len_norm'].iloc[[i+2 for i in pairs]].values
    obs_mean_len = np.mean(obs_len_sau)

    R = 2000
    n = len(pairs)
    all_i = list(range(len(doan_valid) - 2))
    if len(all_i) < n:
        return None

    null_means = np.empty(R)
    for k in range(R):
        chosen = rng.choice(all_i, size=n, replace=False)
        null_means[k] = np.mean(doan_valid['len_norm'].iloc[chosen + 2].values)

    null_mean = np.mean(null_means)
    null_sd = np.std(null_means, ddof=1)
    if null_sd == 0:
        return None

    thong_ke = (obs_mean_len - null_mean) / null_sd
    p_value = (np.sum(null_means <= obs_mean_len) + 1) / (R + 1)

    result = {
        'thong_ke': thong_ke,
        'p': p_value,
        'n': n,
        'quan_sat_tho': obs_mean_len,
        'null_tb': null_mean,
        'null_sd': null_sd,
        'threshold': threshold,
        'pct': pct,
        'ghi_chu': (
            f'len_norm = |do_dai|/ATR(14) tại biet_tai. '
            f'Chân dài được định nghĩa là len_norm > percentile {pct} của toàn bộ chân. '
            'So sánh độ dài chân cùng chiều kế tiếp (i+2) với null hoán vị '
            '(chọn i ngẫu nhiên, giữ nguyên cấu trúc i+2). '
            'thong_ke âm = chân sau ngắn hơn null (ủng hộ hồi quy trung bình). '
            'p là một phía trái. '
            f'Lưu ý: mẫu nhỏ ({n} cặp), kết quả cần thận trọng.'
        )
    }

    # ---- Phần 2: lợi suất 10 phiên sau khi xác nhận ----
    valid_pos = []
    for i in pairs:
        pos = doan_valid['pos_biet'][i]
        if pos is not None and pos + 10 < len(df):
            valid_pos.append(pos)

    if len(valid_pos) >= 10:
        obs_rets = []
        for pos in valid_pos:
            obs_rets.append(df['close'].iloc[pos + 10] / df['close'].iloc[pos] - 1)
        obs_mean_ret = np.mean(obs_rets)

        possible_starts = list(range(len(df) - 10))
        if len(possible_starts) >= len(valid_pos):
            null_rets = np.empty(R)
            for k in range(R):
                starts = rng.choice(possible_starts, size=len(valid_pos), replace=False)
                null_rets[k] = np.mean(
                    df['close'].iloc[starts + 10].values / df['close'].iloc[starts].values - 1
                )
            ret_null_mean = np.mean(null_rets)
            ret_null_sd = np.std(null_rets, ddof=1)
            if ret_null_sd > 0:
                ret_stat = (obs_mean_ret - ret_null_mean) / ret_null_sd
                ret_p = (np.sum(null_rets <= obs_mean_ret) + 1) / (R + 1)
                result.update({
                    'ret_obs': obs_mean_ret,
                    'ret_null_tb': ret_null_mean,
                    'ret_null_sd': ret_null_sd,
                    'ret_thong_ke': ret_stat,
                    'ret_p': ret_p,
                    'ret_n': len(valid_pos)
                })

    return result