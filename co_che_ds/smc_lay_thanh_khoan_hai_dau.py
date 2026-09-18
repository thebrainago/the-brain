import numpy as np
import pandas as pd

def do(khoa, df, rng):
    """
    Kiểm tra khẳng định: sau khi giá quét qua đáy 20 phiên rồi đóng cửa trở lại trên đáy đó,
    trong 5 phiên tiếp theo giá tăng (và ngược lại với đỉnh).

    Sửa so với phiên bản trước:
    - Vào lệnh tại open của phiên sau tín hiệu (open[i+1]), không phải close[i], tránh nhìn tương lai.
    - Thống kê là trung bình có dấu của lợi suất chuẩn hóa, không phải tổng, để so sánh được giữa các thị trường.
    - Hoán vị chọn ngẫu nhiên đúng số ngày sự kiện từ tất cả các ngày hợp lệ, giữ nguyên số lượng long/short,
      kiểm tra liệu ngày quét có đặc biệt hơn ngày thường không.
    """
    df = df.copy()

    # Đáy / đỉnh 20 phiên trước (không bao gồm phiên hiện tại)
    df['low_20'] = df['low'].rolling(20).min().shift(1)
    df['high_20'] = df['high'].rolling(20).max().shift(1)

    # Lợi suất 5 phiên từ open[i+1] đến open[i+6]
    df['open_next'] = df['open'].shift(-1)   # open[i+1]
    df['open_far']  = df['open'].shift(-6)   # open[i+6]
    df['ret_open'] = np.log(df['open_far'] / df['open_next'])

    # Volatility: std của log-return 20 phiên, nhân sqrt(5) để tương ứng 5 phiên
    df['log_ret'] = np.log(df['close']).diff()
    df['vol'] = df['log_ret'].rolling(20).std() * np.sqrt(5)

    # Chuẩn hóa lợi suất theo volatility
    df['ret_chuan'] = np.where(df['vol'] > 0, df['ret_open'] / df['vol'], np.nan)

    # Sự kiện
    cond_dday = (df['low'] < df['low_20']) & (df['close'] > df['low_20'])
    cond_dinh = (df['high'] > df['high_20']) & (df['close'] < df['high_20'])

    df['ind'] = 0
    df.loc[cond_dday, 'ind'] = 1
    df.loc[cond_dinh, 'ind'] = -1

    # Các phiên có đủ dữ liệu
    mask_full = (df['ret_chuan'].notna() & df['low_20'].notna() &
                 df['high_20'].notna() & df['open_next'].notna() & df['open_far'].notna())
    if mask_full.sum() < 30:
        return None

    # Giữ nguyên trục thời gian thật (chỉ số trên df)
    positions = np.where(mask_full)[0]
    ret = df['ret_chuan'].values[positions]
    ind = df['ind'].values[positions]

    n_events = np.sum(ind != 0)
    if n_events < 30:
        return None

    n_long = np.sum(ind == 1)
    n_short = np.sum(ind == -1)

    # Thống kê quan sát: trung bình có dấu
    obs = np.mean(ind * ret)

    n_perm = 2000
    n_total = len(positions)
    count = 0

    for _ in range(n_perm):
        # Chọn ngẫu nhiên đúng n_events ngày từ tất cả các ngày hợp lệ
        chosen = rng.choice(n_total, size=n_events, replace=False)
        # Gán nhãn: giữ nguyên số lượng +1 và -1
        labels = np.array([1] * n_long + [-1] * n_short)
        rng.shuffle(labels)
        perm_stat = np.mean(labels * ret[chosen])
        if perm_stat >= obs:
            count += 1

    p_value = (count + 1) / (n_perm + 1)

    return {
        'thong_ke': float(obs),
        'p': float(p_value),
        'n': int(n_events),
        'ghi_chu': None
    }