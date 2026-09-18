import numpy as np
import pandas as pd
import brain_co_che as bc

def _normalize_direction(h):
    """Chuyển hướng đoạn về +1 (tăng) hoặc -1 (giảm)."""
    if isinstance(h, str):
        return 1 if h.lower() in ['up', 'tăng', 'tang', 'bull'] else -1
    else:
        return 1 if h > 0 else -1

def do(khoa, df, rng):
    # 1. Lấy các chân và đoạn
    ch = bc.chan_song(df)
    doan = bc.cac_doan(df, ch)
    if doan is None or len(doan) < 4:
        return None

    # Sắp xếp theo thời gian bắt đầu
    doan = doan.sort_values('tu').reset_index(drop=True)

    # 2. Tính ATR và chuẩn hoá biên độ
    atr_series = bc.atr(df, 14)
    if atr_series is None:
        return None

    # Lấy ATR tại vị trí tu (chỉ số hàng)
    tu_idx = doan['tu'].values.astype(int)
    atr_values = np.asarray(atr_series.iloc[tu_idx].values, dtype=float)

    do_dai = doan['do_dai'].values.astype(float)
    # Tránh chia 0 hoặc NaN
    valid_mask = (atr_values > 0) & (do_dai > 0) & np.isfinite(atr_values) & np.isfinite(do_dai)
    if not np.all(valid_mask):
        # Có thể loại bỏ các dòng không hợp lệ, nhưng để đơn giản ta ép về NaN và drop
        doan = doan[valid_mask].reset_index(drop=True)
        do_dai = doan['do_dai'].values.astype(float)
        tu_idx = doan['tu'].values.astype(int)
        atr_values = np.asarray(atr_series.iloc[tu_idx].values, dtype=float)
        if len(doan) < 4:
            return None

    bien_do_chuan = do_dai / atr_values

    # 3. Xây dựng các bộ 4 đoạn liên tiếp thoả điều kiện
    huong = np.array([_normalize_direction(h) for h in doan['huong'].values])
    diffs = []

    for i in range(len(doan) - 3):
        # Kiểm tra cấu trúc: [điều chỉnh, đẩy, điều chỉnh, đẩy] hoặc [đẩy, điều chỉnh, đẩy, điều chỉnh]
        # nhưng luôn có: h0 == h2, h1 == h3, h0 != h1
        if (huong[i] == huong[i+2]) and (huong[i+1] == huong[i+3]) and (huong[i] != huong[i+1]):
            # Điều kiện: chân đẩy thứ hai (i+2) gấp đôi chân đẩy thứ nhất (i)
            if bien_do_chuan[i+2] >= 2.0 * bien_do_chuan[i]:
                diff = bien_do_chuan[i+3] - bien_do_chuan[i+1]
                diffs.append(diff)

    n = len(diffs)
    if n < 30:  # luật 5
        return None

    diffs = np.array(diffs, dtype=float)
    mean_obs = diffs.mean()

    # 4. Hoán vị: đảo dấu ngẫu nhiên cho từng cặp (giữ nguyên cấu trúc cặp)
    B = 2000
    null_means = np.empty(B)
    for b in range(B):
        signs = rng.choice([-1, 1], size=n)
        null_means[b] = (signs * diffs).mean()

    null_tb = null_means.mean()
    null_sd = null_means.std(ddof=1)
    if null_sd == 0:
        return None

    # p-value một phía (khẳng định "lớn hơn")
    p = (np.sum(null_means >= mean_obs) + 1) / (B + 1)

    # Thống kê chuẩn hoá theo luật 3
    thong_ke = (mean_obs - null_tb) / null_sd

    return {
        'thong_ke': thong_ke,
        'p': p,
        'n': n,
        'quan_sat_tho': mean_obs,
        'null_tb': null_tb,
        'null_sd': null_sd,
        'de_xuat': 'Khẳng định: khi chân đẩy sau gấp đôi chân đẩy trước, chân điều chỉnh sau có biên độ chuẩn hoá lớn hơn chân điều chỉnh trước. Phép đo dùng diff của biên độ chuẩn hoá (chia ATR).'
    }