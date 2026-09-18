import numpy as np
import pandas as pd

def do(khoa, df, rng):
    """
    Kiểm định: bar có volume và range cùng cao bất thường (z-score > 1.2 so với 20 phiên trước),
    xuất hiện sau một đoạn tăng (close > close 5 phiên trước), thì forward return 10 phiên
    có trung bình âm hơn trung bình toàn mẫu.
    """
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']

    # Biên độ chuẩn hóa theo close trước đó (không dùng thông tin hiện tại)
    range_ = (high - low) / close.shift(1)

    # Rolling mean/std chỉ dùng quá khứ (shift 1 sau rolling)
    vol_mean = volume.rolling(20, min_periods=20).mean().shift(1)
    vol_std = volume.rolling(20, min_periods=20).std().shift(1)
    range_mean = range_.rolling(20, min_periods=20).mean().shift(1)
    range_std = range_.rolling(20, min_periods=20).std().shift(1)

    z_vol = (volume - vol_mean) / vol_std
    z_range = (range_ - range_mean) / range_std

    # Loại bỏ inf/nan do std = 0
    z_vol = z_vol.replace([np.inf, -np.inf], np.nan)
    z_range = z_range.replace([np.inf, -np.inf], np.nan)

    # Đoạn tăng kéo dài: giá đóng cửa hiện tại cao hơn 5 phiên trước
    uptrend = (close > close.shift(5)).fillna(False)

    # Forward return 10 phiên
    fwd = (close.shift(-10) - close) / close

    df_ = pd.DataFrame({
        'fwd': fwd,
        'event': (z_vol > 1.2) & (z_range > 1.2) & uptrend,
        'z_vol': z_vol,
        'z_range': z_range
    })

    df_ = df_.dropna(subset=['fwd', 'z_vol', 'z_range', 'event'])

    if len(df_) < 30:
        return None

    n_event = int(df_['event'].sum())
    if n_event < 30:
        return None

    # Thống kê quan sát
    mean_all = df_['fwd'].mean()
    mean_event_obs = df_.loc[df_['event'], 'fwd'].mean()
    diff_obs = mean_event_obs - mean_all

    # Hoán vị: giữ nguyên số sự kiện, hoán vị nhãn sự kiện trong mẫu
    fwd_vals = df_['fwd'].values
    n = len(df_)
    n_perm = 2000
    diff_perms = np.empty(n_perm)

    for b in range(n_perm):
        idx = rng.choice(n, size=n_event, replace=False)
        diff_perms[b] = fwd_vals[idx].mean() - mean_all

    # p-value một phía (âm hơn)
    p = (np.sum(diff_perms <= diff_obs) + 1) / (n_perm + 1)

    # Thống kê neo vào null
    null_mean = diff_perms.mean()
    null_std = diff_perms.std(ddof=1)
    if null_std == 0:
        return None

    thong_ke = (diff_obs - null_mean) / null_std

    return {
        'thong_ke': float(thong_ke),
        'p': float(p),
        'n': int(n_event),
        'quan_sat_tho': float(diff_obs),
        'null_tb': float(null_mean),
        'null_sd': float(null_std),
        'mean_event': float(mean_event_obs),
        'mean_all': float(mean_all),
        'ghi_chu': "Đã hạ ngưỡng z từ 2 xuống 1.2 để đảm bảo đủ số sự kiện (n>=30). "
                   "Điều kiện 'đoạn tăng kéo dài' được định nghĩa là close > close.shift(5). "
                   "Hoán vị giữ nguyên số sự kiện và tỷ lệ mua-bán (chỉ hoán vị nhãn sự kiện).",
        'de_xuat': "Thử lại với ngưỡng z=2 và gộp nhiều thị trường để tăng mẫu, "
                   "hoặc dùng rolling window 50 để giảm nhiễu."
    }