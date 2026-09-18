def do(khoa, df, rng):
    import numpy as np
    import pandas as pd

    if len(df) < 30:
        return None

    high = df['high']
    low = df['low']
    close = df['close']
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()

    def build_pivots(atr_series, factor):
        threshold = factor * atr_series
        n = len(df)
        pivots = []  # (index, price)
        pivot_idx = 0
        pivot_price = close.iloc[0]
        direction = 0  # 0: chưa xác định, 1: tăng, -1: giảm
        extreme_idx = 0
        extreme_price = pivot_price

        for i in range(1, n):
            if direction == 0:
                if close.iloc[i] > pivot_price + threshold.iloc[i]:
                    direction = 1
                    extreme_idx = i
                    extreme_price = high.iloc[i]
                elif close.iloc[i] < pivot_price - threshold.iloc[i]:
                    direction = -1
                    extreme_idx = i
                    extreme_price = low.iloc[i]
            elif direction == 1:
                if high.iloc[i] > extreme_price:
                    extreme_price = high.iloc[i]
                    extreme_idx = i
                elif low.iloc[i] < extreme_price - threshold.iloc[i]:
                    pivots.append((extreme_idx, extreme_price))
                    direction = -1
                    extreme_idx = i
                    extreme_price = low.iloc[i]
            else:  # direction == -1
                if low.iloc[i] < extreme_price:
                    extreme_price = low.iloc[i]
                    extreme_idx = i
                elif high.iloc[i] > extreme_price + threshold.iloc[i]:
                    pivots.append((extreme_idx, extreme_price))
                    direction = 1
                    extreme_idx = i
                    extreme_price = high.iloc[i]

        # Thêm điểm cực trị cuối cùng nếu chưa có
        if len(pivots) == 0 or pivots[-1][0] != extreme_idx:
            pivots.append((extreme_idx, extreme_price))
        # Thêm điểm bắt đầu (index 0) vào đầu danh sách
        pivots.insert(0, (0, pivot_price))
        return pivots

    # Thử các ngưỡng khác nhau để có đủ số chân (M >= 75)
    factors = [3.0, 2.0, 1.5, 1.0, 0.75, 0.5, 0.25, 0.1]
    best_pivots = None
    best_M = 0
    chosen_factor = None

    for f in factors:
        pivots = build_pivots(atr, f)
        M = len(pivots) - 1
        if M >= 75:
            best_pivots = pivots
            best_M = M
            chosen_factor = f
            break

    if best_pivots is None:
        return {
            'thong_ke': None,
            'p': None,
            'n': 0,
            'ghi_chu': f'Không đủ số chân (M < 75) với mọi ngưỡng thử, không thể đo được.'
        }

    pivots = best_pivots
    M = best_M
    pivot_idx = [p[0] for p in pivots]

    # Tạo danh sách sự kiện cho chân 3 và chân 5
    events_3 = []
    events_5 = []

    # Bội số của 3: k = 3,6,9,...
    for k in range(3, M + 1, 3):
        idx = pivot_idx[k]
        if idx + 10 >= len(df):
            continue
        ret = close.iloc[idx + 10] / close.iloc[idx] - 1
        atr_val = atr.iloc[idx]
        if atr_val > 0:
            ret_scaled = ret * close.iloc[idx] / atr_val  # chuẩn hoá theo ATR
        else:
            ret_scaled = np.nan
        if not np.isnan(ret_scaled):
            events_3.append((idx, ret_scaled))

    # Bội số của 5: k = 5,10,15,...
    for k in range(5, M + 1, 5):
        idx = pivot_idx[k]
        if idx + 10 >= len(df):
            continue
        ret = close.iloc[idx + 10] / close.iloc[idx] - 1
        atr_val = atr.iloc[idx]
        if atr_val > 0:
            ret_scaled = ret * close.iloc[idx] / atr_val
        else:
            ret_scaled = np.nan
        if not np.isnan(ret_scaled):
            events_5.append((idx, ret_scaled))

    # Loại bỏ các ngày trùng lặp giữa hai nhóm
    set_3 = {idx for idx, _ in events_3}
    set_5 = {idx for idx, _ in events_5}
    common = set_3 & set_5
    if common:
        events_3 = [(idx, ret) for idx, ret in events_3 if idx not in common]
        events_5 = [(idx, ret) for idx, ret in events_5 if idx not in common]

    ret_3 = np.array([ret for _, ret in events_3])
    ret_5 = np.array([ret for _, ret in events_5])

    if len(ret_3) < 15 or len(ret_5) < 15:
        return {
            'thong_ke': None,
            'p': None,
            'n': len(ret_3) + len(ret_5),
            'ghi_chu': f'Số sự kiện không đủ: ret_3={len(ret_3)}, ret_5={len(ret_5)} sau khi loại trùng. Không thể đo.'
        }

    # Thống kê quan sát: hiệu trung bình
    obs = ret_5.mean() - ret_3.mean()

    # Hoán vị giữ nguyên số lượng mỗi nhóm
    combined = np.concatenate([ret_3, ret_5])
    n3 = len(ret_3)
    n5 = len(ret_5)
    n_perm = 2000
    perm_diffs = np.empty(n_perm)

    for b in range(n_perm):
        perm = rng.permutation(combined)
        perm_3 = perm[:n3]
        perm_5 = perm[n3:]
        perm_diffs[b] = perm_5.mean() - perm_3.mean()

    null_mean = perm_diffs.mean()
    null_std = perm_diffs.std()
    if null_std > 0:
        thong_ke = (obs - null_mean) / null_std
    else:
        thong_ke = 0.0
    p = (np.abs(perm_diffs) >= np.abs(obs)).mean()

    ghi_chu = (f"Đã dùng ngưỡng zigzag = {chosen_factor}*ATR để có đủ sự kiện (M={M}). "
               f"Nhóm 3 chân: {len(ret_3)}, nhóm 5 chân: {len(ret_5)}. "
               f"Lợi suất 10 phiên được chuẩn hoá theo ATR.")
    if chosen_factor != 3.0:
        ghi_chu += " Lưu ý: khác với ngưỡng 3*ATR gốc."

    return {
        'thong_ke': thong_ke,
        'p': p,
        'n': len(ret_3) + len(ret_5),
        'quan_sat_tho': obs,
        'null_tb': null_mean,
        'null_sd': null_std,
        'ghi_chu': ghi_chu,
        'de_xuat': None
    }