import numpy as np
import pandas as pd

def do(khoa, df, rng):
    """
    Kiểm định tương tác: hiệu ứng của sự kiện 'quét đỉnh/đáy 20 phiên rồi đóng cửa trở lại'
    có phụ thuộc vào chế độ thị trường hay không.

    Định nghĩa sự kiện:
      - Quét đỉnh: high[i] vượt max(high[i-20..i-1]) nhưng close[i] < max đó.
      - Quét đáy:  low[i]  thấp hơn min(low[i-20..i-1])  nhưng close[i] > min đó.
    Tín hiệu: quét đỉnh → short, quét đáy → long, giữ 1 ngày.
    Hiệu ứng: return có dấu chia cho std_ret20 (biến động 20 phiên) để chuẩn hóa.

    Chia thành 4 chế độ nhị phân:
      - vol_high: std_ret20 > std_ret200 (biến động tăng)
      - above_sma200: close > SMA200
      - far_from_sma: |close-SMA200|/SMA200 > 5%
      - wide_bar: (high-low) > ATR20 (bar quét rộng)

    Thống kê: max(|diff|) trong các biến, diff = mean(effect|True) - mean(effect|False).
    Null: hoán vị nhãn của từng biến (giữ nguyên số sự kiện mỗi nhóm).
    Hình phạt cho việc chia ô: chỉ dùng tối đa 4 biến, loại biến có nhóm <5 quan sát,
    và lấy max của các |diff| → phân phối null tự rộng hơn khi nhiều biến.
    """
    # Cần ít nhất 220 phiên để có SMA200, std_ret200 và rolling 20
    if len(df) < 220:
        return None

    close = df['close']
    high = df['high']
    low = df['low']

    # Rolling std của daily return
    ret = close.pct_change()
    std_ret20 = ret.rolling(20).std()
    std_ret200 = ret.rolling(200).std()

    # SMA200
    sma200 = close.rolling(200).mean()

    # ATR20 (dùng high-low)
    atr20 = (high - low).rolling(20).mean()

    # Đỉnh/đáy 20 phiên trước (không gồm hiện tại)
    prev_high20 = high.shift(1).rolling(20).max()
    prev_low20 = low.shift(1).rolling(20).min()

    # Điều kiện sự kiện
    sweep_high = (high > prev_high20) & (close < prev_high20)
    sweep_low = (low < prev_low20) & (close > prev_low20)
    event_mask = (sweep_high | sweep_low).fillna(False)

    event_idx = np.flatnonzero(event_mask.to_numpy())

    if len(event_idx) < 30:
        return None

    effects = []
    vol_high_list = []
    above_sma200_list = []
    far_from_sma_list = []
    wide_bar_list = []

    for i in event_idx:
        if i + 1 >= len(df):
            continue

        # Xác định loại sự kiện: ưu tiên quét đỉnh nếu cả hai xảy ra (hiếm)
        if sweep_high.iloc[i]:
            eff = (close.iloc[i] - close.iloc[i+1]) / close.iloc[i]  # short
        else:
            eff = (close.iloc[i+1] - close.iloc[i]) / close.iloc[i]  # long

        sig = std_ret20.iloc[i]
        if pd.isna(sig) or sig == 0:
            continue
        eff_norm = eff / sig

        # Biến chế độ
        if pd.isna(std_ret200.iloc[i]):
            continue
        vol_high = std_ret20.iloc[i] > std_ret200.iloc[i]

        if pd.isna(sma200.iloc[i]) or sma200.iloc[i] == 0:
            continue
        above_sma200 = close.iloc[i] > sma200.iloc[i]
        far_from_sma = abs(close.iloc[i] - sma200.iloc[i]) / sma200.iloc[i] > 0.05

        if pd.isna(atr20.iloc[i]) or atr20.iloc[i] == 0:
            continue
        wide_bar = (high.iloc[i] - low.iloc[i]) / atr20.iloc[i] > 1.0

        effects.append(eff_norm)
        vol_high_list.append(vol_high)
        above_sma200_list.append(above_sma200)
        far_from_sma_list.append(far_from_sma)
        wide_bar_list.append(wide_bar)

    if len(effects) < 30:
        return None

    events = pd.DataFrame({
        'effect': effects,
        'vol_high': vol_high_list,
        'above_sma200': above_sma200_list,
        'far_from_sma': far_from_sma_list,
        'wide_bar': wide_bar_list
    })

    # Chỉ giữ biến có đủ số quan sát mỗi nhóm
    valid_vars = []
    for var in ['vol_high', 'above_sma200', 'far_from_sma', 'wide_bar']:
        n_true = int(events[var].sum())
        n_false = len(events) - n_true
        if n_true >= 5 and n_false >= 5:
            valid_vars.append(var)

    if len(valid_vars) == 0:
        return None

    def compute_max_diff(df_events, vars_list):
        max_diff = 0.0
        for var in vars_list:
            true_mean = df_events.loc[df_events[var], 'effect'].mean()
            false_mean = df_events.loc[~df_events[var], 'effect'].mean()
            diff = abs(true_mean - false_mean)
            if diff > max_diff:
                max_diff = diff
        return max_diff

    obs_max_diff = compute_max_diff(events, valid_vars)

    # Hoán vị: hoán vị nhãn mỗi biến độc lập, giữ nguyên số sự kiện mỗi nhóm
    B = 2000
    perm_max_diffs = np.empty(B)

    for b in range(B):
        perm_events = events.copy()
        for var in valid_vars:
            perm_events[var] = rng.permutation(events[var].to_numpy())
        perm_max_diffs[b] = compute_max_diff(perm_events, valid_vars)

    null_mean = float(perm_max_diffs.mean())
    null_std = float(perm_max_diffs.std())
    if null_std == 0:
        return None

    thong_ke = (obs_max_diff - null_mean) / null_std
    p = float((1 + np.sum(perm_max_diffs >= obs_max_diff)) / (B + 1))

    return {
        'thong_ke': thong_ke,
        'p': p,
        'n': len(events),
        'quan_sat_tho': float(obs_max_diff),
        'null_tb': null_mean,
        'null_sd': null_std,
        'so_bien': len(valid_vars),
        'bien_hop_le': ','.join(valid_vars),
        'ghi_chu': 'Hình phạt chia ô: chỉ tối đa 4 biến nhị phân, loại biến có nhóm <5 quan sát, lấy max |diff|; null hoán vị từng biến độc lập.'
    }