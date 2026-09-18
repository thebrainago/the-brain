import numpy as np
import pandas as pd
try:
    from brain_co_che import chan_song, cac_doan, atr
except ImportError:
    # fallback nếu không import được (chỉ để chạy thử, không dùng trong hệ thống)
    chan_song = cac_doan = atr = None

def do(khoa, df, rng):
    """
    Kiểm định: nếu chân đẩy có tốc độ > 1.5 lần chân điều chỉnh liền trước,
    thì chân điều chỉnh tiếp theo có biên độ lớn hơn chân điều chỉnh trước đó.
    """
    if chan_song is None or cac_doan is None or atr is None:
        return None

    # Lấy các chân sóng và các đoạn nối
    ch = chan_song(df)
    doan = cac_doan(df, ch)
    if len(doan) < 4:
        return None

    # Tính ATR để chuẩn hoá biên độ
    atr_series = atr(df, 14)
    
    def get_atr(pos):
        """Lấy giá trị ATR tại vị trí pos (có thể là index label hoặc vị trí số)."""
        try:
            return atr_series.iloc[pos]
        except (IndexError, KeyError):
            try:
                return atr_series.loc[pos]
            except:
                return np.nan

    # Trích các cột cần thiết
    huong = doan['huong'].values
    do_dai = doan['do_dai'].values
    thoi_luong = doan['thoi_luong'].values
    tu = doan['tu'].values  # vị trí bắt đầu mỗi đoạn

    records = []  # (delta, is_cond)
    n = len(doan)

    for i in range(n - 3):
        # Điều kiện cấu trúc: B (i+1) và D (i+3) cùng hướng, C (i+2) ngược hướng
        if not (huong[i] == huong[i+2] and huong[i+1] == -huong[i] and huong[i+3] == huong[i+1]):
            continue

        # B = i+1 (điều chỉnh), C = i+2 (đẩy), D = i+3 (điều chỉnh sau)
        toc_B = do_dai[i+1] / max(thoi_luong[i+1], 1)
        toc_C = do_dai[i+2] / max(thoi_luong[i+2], 1)
        is_cond = toc_C > 1.5 * toc_B

        # Chuẩn hoá delta theo ATR tại thời điểm D bắt đầu
        atr_D = get_atr(tu[i+3])
        if atr_D is None or atr_D == 0 or np.isnan(atr_D):
            continue
        delta = (do_dai[i+3] - do_dai[i+1]) / atr_D
        records.append((delta, is_cond))

    if len(records) < 30:
        return None

    deltas = np.array([r[0] for r in records])
    cond_mask = np.array([r[1] for r in records])
    n_cond = int(cond_mask.sum())
    if n_cond < 30:
        return None

    # Thống kê quan sát: trung bình delta của các trường hợp có điều kiện
    obs_mean = deltas[cond_mask].mean()

    # Hoán vị: giữ nguyên số lượng có điều kiện, trộn nhãn trên các bộ ba
    n_perm = 2000
    null_means = np.empty(n_perm)
    for k in range(n_perm):
        perm_mask = rng.permutation(cond_mask)  # giữ nguyên số True
        null_means[k] = deltas[perm_mask].mean()

    null_tb = null_means.mean()
    null_sd = null_means.std(ddof=1)
    if null_sd == 0:
        return None

    # p-value một phía (khẳng định: delta > 0)
    p = (np.sum(null_means >= obs_mean) + 1) / (n_perm + 1)
    thong_ke = (obs_mean - null_tb) / null_sd

    return {
        'thong_ke': thong_ke,
        'p': p,
        'n': n_cond,
        'quan_sat_tho': obs_mean,
        'null_tb': null_tb,
        'null_sd': null_sd,
        'de_xuat': None
    }