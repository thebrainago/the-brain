import numpy as np
import brain_co_che as bc

def tinh_tu_ch(df, ch, n_min, rng, he_so):
    if ch is None or len(ch) < 4 or 'vi_tri' not in ch.columns:
        return None

    ch = ch.sort_values('vi_tri').reset_index(drop=True)
    vi_tri = ch['vi_tri'].values

    vt = []
    for v in vi_tri:
        try:
            if isinstance(v, (int, np.integer)):
                vt.append(int(v))
            else:
                vt.append(df.index.get_loc(v))
        except Exception:
            vt.append(-1)
    vt = np.array(vt)

    ratios = []
    n_list = []

    for i in range(len(vt) - 1):
        t = vt[i]
        d = vt[i + 1]
        if t < 0 or d < 0 or d - t < n_min:
            continue

        start = t + 1
        end = d + 1
        if end <= start or end > len(df):
            continue

        seg = df.iloc[start:end]
        if len(seg) < 3:
            continue

        total_range = (seg['high'] - seg['low']).sum()
        if total_range <= 0:
            continue

        first3 = seg.iloc[:3]
        first3_range = (first3['high'] - first3['low']).sum()

        ratios.append(first3_range / total_range)
        n_list.append(d - t)

    if len(ratios) < 30:
        return None

    ratios = np.array(ratios)
    n_arr = np.array(n_list)

    n_cao = n_arr[ratios > 0.5]
    n_thap = n_arr[ratios < 0.3]

    if len(n_cao) < 30 or len(n_thap) < 30:
        return None

    diff_obs = np.mean(n_thap) - np.mean(n_cao)
    values = np.concatenate([n_cao, n_thap])
    labels = np.array([0] * len(n_cao) + [1] * len(n_thap))

    n_perm = 2000
    perm_diffs = np.empty(n_perm)
    for b in range(n_perm):
        perm_labels = rng.permutation(labels)
        mean_thap = values[perm_labels == 1].mean()
        mean_cao = values[perm_labels == 0].mean()
        perm_diffs[b] = mean_thap - mean_cao

    if diff_obs >= 0:
        p = (1 + np.sum(perm_diffs >= diff_obs)) / (n_perm + 1)
    else:
        p = (1 + np.sum(perm_diffs <= diff_obs)) / (n_perm + 1)

    null_mean = perm_diffs.mean()
    null_std = perm_diffs.std(ddof=1)
    if null_std == 0:
        return None

    thong_ke = (diff_obs - null_mean) / null_std

    res = {
        'thong_ke': float(thong_ke),
        'p': float(p),
        'n': int(len(values)),
        'quan_sat_tho': float(diff_obs),
        'null_tb': float(null_mean),
        'null_sd': float(null_std),
        'n_cao': int(len(n_cao)),
        'n_thap': int(len(n_thap)),
        'nguong_chan': he_so if he_so is not None else 'default',
        'n_min': n_min,
        'ghi_chu': (
            "Dùng bc.chan_song, chân là đoạn giữa hai swing point liên tiếp theo vi_tri. "
            "vi_tri có thể vẽ lại, nhưng đây là đo lường cấu trúc chứ không phải tín hiệu giao dịch. "
            "Tỷ lệ = tổng high-low 3 nến đầu sau swing trước / tổng high-low cả chân. "
            "Nhóm cao: tỷ lệ > 0.5; nhóm thấp: tỷ lệ < 0.3. "
            "Thống kê diff = mean(n_thấp) - mean(n_cao); dương ủng hộ khẳng định. "
            "Hoán vị trộn nhãn, giữ nguyên số lượng mỗi nhóm. "
            f"he_so={he_so if he_so is not None else 'default'}, n_min={n_min}."
        ),
        'de_xuat': None,
    }

    if p < 0.05 and thong_ke > 0:
        res['de_xuat'] = (
            "Chân có 3 nến đầu chiếm >50% biên độ tổng thường ngắn hơn đáng kể "
            "so với chân có tỷ lệ <30%; có thể kết hợp làm tín hiệu thoái lui nhanh."
        )

    return res


def do(khoa, df, rng):
    configs = [
        (None, 6),
        (1.5, 6),
        (None, 4),
        (1.5, 4),
        (1.5, 3),
        (None, 3),
    ]

    for he_so, n_min in configs:
        try:
            if he_so is None:
                ch = bc.chan_song(df)
            else:
                ch = bc.chan_song(df, he_so=he_so)

            res = tinh_tu_ch(df, ch, n_min, rng, he_so)
            if res is not None:
                return res
        except Exception:
            continue

    return None