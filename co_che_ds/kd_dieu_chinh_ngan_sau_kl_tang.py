import numpy as np
import pandas as pd
import brain_co_che as bc

def do(khoa, df, rng):
    """
    Đo khẳng định: khi một chân đẩy có khối lượng tăng dần (slope > 0),
    thì chân điều chỉnh tiếp theo có biên độ và thời lượng nhỏ hơn
    so với khi chân đẩy có khối lượng giảm dần.

    Thống kê: hiệu trung bình của S = (biên độ pull / biên độ push) + (thời lượng pull / thời lượng push)
    giữa nhóm không tăng (slope <= 0) và nhóm tăng (slope > 0).
    Dương = ủng hộ khẳng định.
    """
    # Lấy các chân sóng
    ch = bc.chan_song(df)
    if ch is None or len(ch) < 3:
        return None

    # Sắp xếp theo vị trí thực
    ch = ch.sort_values('vi_tri').reset_index(drop=True)
    pos = ch['vi_tri'].values
    gia = ch['gia'].values
    xac = ch['xac_nhan'].values

    # Xây dựng danh sách các đoạn (segment) nối hai chân liên tiếp
    segments = []
    for i in range(len(pos) - 1):
        start = pos[i]
        end = pos[i+1]
        if end <= start:
            continue
        do_dai = gia[i+1] - gia[i]          # có dấu
        thoi_luong = end - start            # số bar từ start đến end
        huong = 1 if do_dai > 0 else -1
        segments.append({
            'start': start,
            'end': end,
            'do_dai': do_dai,
            'thoi_luong': thoi_luong,
            'huong': huong,
            'xac_nhan_end': xac[i+1]
        })

    if len(segments) < 2:
        return None

    # Tìm các cặp push-pull: push là đoạn có biên độ lớn hơn và xuất hiện trước pull
    pairs = []
    for i in range(len(segments) - 1):
        seg_i = segments[i]
        seg_j = segments[i+1]
        # Ngược hướng
        if seg_i['huong'] * seg_j['huong'] >= 0:
            continue
        # Push phải lớn hơn pull và nằm trước
        if abs(seg_i['do_dai']) > abs(seg_j['do_dai']):
            pairs.append((seg_i, seg_j))

    if len(pairs) < 30:
        return None

    S_list = []
    vol_up_list = []

    for push, pull in pairs:
        # Tính hệ số góc của volume trong đoạn push
        start_push = push['start']
        end_push = push['end']
        # Giới hạn trong phạm vi df
        if start_push < 0:
            start_push = 0
        if end_push >= len(df):
            end_push = len(df) - 1
        if end_push - start_push < 2:
            continue
        vol = df['volume'].iloc[start_push:end_push+1].values
        if len(vol) < 2:
            continue
        x = np.arange(len(vol))
        try:
            slope = np.polyfit(x, vol, 1)[0]
        except:
            continue
        vol_up = slope > 0

        # Tính S – tổng tỷ lệ biên độ và thời lượng của pull so với push
        do_dai_push = abs(push['do_dai'])
        do_dai_pull = abs(pull['do_dai'])
        thoi_luong_push = push['thoi_luong']
        thoi_luong_pull = pull['thoi_luong']
        if do_dai_push == 0 or thoi_luong_push == 0:
            continue
        norm_bien_do = do_dai_pull / do_dai_push
        norm_thoi_luong = thoi_luong_pull / thoi_luong_push
        S = norm_bien_do + norm_thoi_luong

        S_list.append(S)
        vol_up_list.append(vol_up)

    S = np.array(S_list)
    vol_up = np.array(vol_up_list, dtype=bool)

    if len(S) < 30:
        return None

    # Thống kê quan sát
    mean_S_tang = S[vol_up].mean() if vol_up.any() else 0.0
    mean_S_giam = S[~vol_up].mean() if (~vol_up).any() else 0.0
    observed = mean_S_giam - mean_S_tang  # dương nếu nhóm tăng có S nhỏ hơn

    # Hoán vị (giữ nguyên số lượng nhóm tăng)
    n_perm = 2000
    perm_stats = np.empty(n_perm)
    n_up = vol_up.sum()
    S_vals = S.copy()
    for i in range(n_perm):
        perm_labels = np.zeros(len(S_vals), dtype=bool)
        perm_labels[:n_up] = True
        rng.shuffle(perm_labels)
        mean_tang_perm = S_vals[perm_labels].mean()
        mean_giam_perm = S_vals[~perm_labels].mean()
        perm_stats[i] = mean_giam_perm - mean_tang_perm

    # p-value một phía (observed >= perm)
    p = (np.sum(perm_stats >= observed) + 1) / (n_perm + 1)

    null_tb = perm_stats.mean()
    null_sd = perm_stats.std()
    if null_sd == 0:
        thong_ke = 0.0
    else:
        thong_ke = (observed - null_tb) / null_sd

    return {
        'thong_ke': float(thong_ke),
        'p': float(p),
        'n': int(len(S)),
        'quan_sat_tho': float(observed),
        'null_tb': float(null_tb),
        'null_sd': float(null_sd),
        'de_xuat': 'Có thể thử chuẩn hóa biên độ pull bằng ATR thay vì tỷ lệ với push để ổn định hơn.'
    }