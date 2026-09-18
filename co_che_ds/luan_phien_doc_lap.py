def do(khoa, df, rng):
    """
    Kiểm định khẳng định: 'hai đợt điều chỉnh liên tiếp có hình dạng đối lập (nhọn <-> phẳng)'.
    Định nghĩa độ dốc của một đợt điều chỉnh là |(giá cuối - giá đầu) / thời lượng| chia cho ATR trung bình
    trong đoạn đó, để loại bỏ ảnh hưởng của volatility clustering.
    Thống kê: tương quan Pearson giữa độ dốc tuyệt đối của các cặp đoạn liên tiếp.
    Nếu khẳng định đúng, tương quan phải âm (đối lập).
    """
    import numpy as np
    import pandas as pd
    try:
        from brain_co_che import chan_song, cac_doan, atr
    except ImportError:
        return None

    # Lấy danh sách các đợt điều chỉnh (các đoạn nối hai chân)
    ch = chan_song(df)
    doan = cac_doan(df, ch)
    if doan is None or len(doan) < 2:
        return None

    # Lấy các cột cần thiết
    tu = doan['tu'].values.astype(int)
    den = doan['den'].values.astype(int)
    close = df['close'].values
    atr_vals = atr(df, 14).values

    slopes = []
    for i in range(len(tu)):
        t = tu[i]
        d = den[i]
        if d <= t:
            continue
        length = d - t
        if length < 2:  # bỏ các đoạn quá ngắn
            continue
        p_start = close[t]
        p_end = close[d]
        slope_raw = (p_end - p_start) / length
        # ATR trung bình trên đoạn (bao gồm cả hai đầu)
        atr_segment = atr_vals[t:d+1]
        atr_mean = np.nanmean(atr_segment)
        if atr_mean == 0 or np.isnan(atr_mean):
            continue
        slope_norm = slope_raw / atr_mean
        slopes.append(abs(slope_norm))

    if len(slopes) < 30:  # mẫu quá nhỏ
        return None

    abs_slopes = np.array(slopes)
    n = len(abs_slopes)

    # Tương quan quan sát giữa các cặp liên tiếp
    X = abs_slopes[:-1]
    Y = abs_slopes[1:]
    if len(X) < 2 or np.std(X) == 0 or np.std(Y) == 0:
        return None
    rho_obs = np.corrcoef(X, Y)[0, 1]

    # Hoán vị: shuffle toàn bộ chuỗi abs_slopes, giữ nguyên số cặp và phân phối từng giá trị
    n_perm = 2000
    count = 0
    nulls = np.empty(n_perm)
    for i in range(n_perm):
        perm = rng.permutation(abs_slopes)
        Xp = perm[:-1]
        Yp = perm[1:]
        if np.std(Xp) == 0 or np.std(Yp) == 0:
            rho_perm = 0.0
        else:
            rho_perm = np.corrcoef(Xp, Yp)[0, 1]
        nulls[i] = rho_perm
        if rho_perm <= rho_obs:  # một phía: tương quan âm
            count += 1

    p_value = (count + 1) / (n_perm + 1)  # +1 để tránh p=0
    mean_null = np.mean(nulls)
    std_null = np.std(nulls)
    if std_null == 0:
        thong_ke = 0.0
    else:
        thong_ke = (rho_obs - mean_null) / std_null

    return {
        'thong_ke': thong_ke,
        'p': p_value,
        'n': n,
        'quan_sat_tho': rho_obs,
        'null_tb': mean_null,
        'null_sd': std_null,
        'de_xuat': "Độ dốc đã chuẩn hóa theo ATR để loại bỏ ảnh hưởng volatility clustering; tương quan âm giữa các cặp liên tiếp ủng hộ khẳng định."
    }