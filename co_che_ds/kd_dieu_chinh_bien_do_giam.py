import numpy as np
import pandas as pd
import brain_co_che as bc

def do(khoa, df, rng):
    # Lấy chân sóng và các đoạn nối giữa chúng
    ch = bc.chan_song(df)
    if ch is None or len(ch) < 3:
        return None
    doan = bc.cac_doan(df, ch)
    if doan is None or len(doan) < 3:
        return None

    # ATR(14) để chuẩn hoá biên độ (luật 4)
    atr = bc.atr(df, 14)
    if isinstance(atr, pd.Series):
        atr_arr = atr.values
    else:
        atr_arr = np.asarray(atr)

    # Lấy ATR tại điểm kết thúc đoạn (den)
    if pd.api.types.is_numeric_dtype(doan['den']):
        den_idx = doan['den'].astype(int)
        if den_idx.max() >= len(atr_arr) or den_idx.min() < 0:
            return None
        atr_den = atr_arr[den_idx]
    else:
        # den là nhãn thời gian
        try:
            positions = df.index.get_indexer(doan['den'])
        except Exception:
            return None
        if np.any(positions == -1):
            return None
        atr_den = atr_arr[positions]

    doan = doan.copy()
    doan['atr_den'] = atr_den
    # Biên độ chuẩn hoá: lấy trị tuyệt đối để so sánh độ lớn
    doan['bien_do'] = doan['do_dai'].abs() / doan['atr_den']
    doan = doan.replace([np.inf, -np.inf], np.nan).dropna(subset=['bien_do'])
    if len(doan) < 3:
        return None

    # Tách theo hướng điều chỉnh
    down = doan.loc[doan['huong'] == -1, 'bien_do'].values
    up = doan.loc[doan['huong'] == 1, 'bien_do'].values

    def tinh_y(x):
        """Với vector biên độ cùng hướng, trả về 1 nếu x[i+1] > x[i] và x[i+2] < x[i+1]."""
        x = np.asarray(x, dtype=float)
        if len(x) < 3:
            return np.array([], dtype=float)
        cond = x[1:-1] > x[:-2]   # chân 2 > chân 1
        y = x[2:] < x[1:-1]       # chân 3 < chân 2
        return y[cond].astype(float)

    obs_down = tinh_y(down)
    obs_up = tinh_y(up)

    if len(obs_down) == 0 and len(obs_up) == 0:
        return None
    if len(obs_down) > 0 and len(obs_up) > 0:
        obs_all = np.concatenate([obs_down, obs_up])
    elif len(obs_down) > 0:
        obs_all = obs_down
    else:
        obs_all = obs_up

    N = len(obs_all)
    if N < 30:
        return None

    quan_sat = float(np.mean(obs_all))

    # Hoán vị: trộn thứ tự các chân điều chỉnh trong từng hướng riêng (giữ phổ nhiễm)
    n_perm = 2000
    null_rates = []
    for _ in range(n_perm):
        down_perm = rng.permutation(down) if len(down) > 0 else down
        up_perm = rng.permutation(up) if len(up) > 0 else up

        Y_down = tinh_y(down_perm)
        Y_up = tinh_y(up_perm)

        if len(Y_down) == 0 and len(Y_up) == 0:
            continue
        if len(Y_down) > 0 and len(Y_up) > 0:
            Y_all = np.concatenate([Y_down, Y_up])
        elif len(Y_down) > 0:
            Y_all = Y_down
        else:
            Y_all = Y_up

        if len(Y_all) == 0:
            continue
        null_rates.append(float(np.mean(Y_all)))

    if len(null_rates) < 100:
        return None

    null_rates = np.array(null_rates)
    null_tb = float(np.mean(null_rates))
    null_sd = float(np.std(null_rates))
    if null_sd == 0:
        thong_ke = 0.0
    else:
        thong_ke = (quan_sat - null_tb) / null_sd

    # p-value một phía: tỷ lệ hoán vị có kết quả >= quan sát
    p = (np.sum(null_rates >= quan_sat) + 1) / (len(null_rates) + 1)

    ghi_chu = (
        "Khẳng định: khi hai chân điều chỉnh cùng hướng liên tiếp có biên độ tăng dần "
        "(chân 2 > chân 1, biên độ chuẩn hóa bằng ATR tại điểm kết thúc), thì chân thứ ba "
        "có xác suất co lại (biên độ < chân 2) cao hơn ngẫu nhiên. "
        "Hoán vị: trộn thứ tự các chân điều chỉnh trong từng hướng riêng, giữ nguyên phân phối biên độ, "
        "phá vỡ mối quan hệ tuần tự. p-value một phía từ phân phối hoán vị."
    )

    de_xuat = "Có thể kiểm tra với các ngưỡng tăng dần khác (ví dụ tăng > 1.5 lần) hoặc tách riêng theo hướng."

    return {
        'thong_ke': thong_ke,
        'p': p,
        'n': N,
        'quan_sat_tho': quan_sat,
        'null_tb': null_tb,
        'null_sd': null_sd,
        'ghi_chu': ghi_chu,
        'de_xuat': de_xuat
    }