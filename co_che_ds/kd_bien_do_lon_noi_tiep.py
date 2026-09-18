import numpy as np
import pandas as pd


def do(khoa, df, rng):
    W = 100
    N_PERM = 2000

    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    bd = high - low
    n = len(bd)

    # top20[t] = 1 nếu biên độ phiên t thuộc nhóm 20% lớn nhất
    # trong cửa sổ 100 phiên kết thúc tại t.
    s = pd.Series(bd)
    q = s.rolling(W, min_periods=W).quantile(0.8, interpolation="higher").to_numpy()
    top20 = np.zeros(n, dtype=bool)
    ok = ~np.isnan(q)
    top20[ok] = bd[ok] >= q[ok]

    # Sự kiện xảy ra ở phiên t, outcome là top20[t+1].
    # t phải có top20[t] và top20[t+1] đều hợp lệ.
    t = np.arange(W - 1, n - 1)
    if len(t) < 2:
        return None

    E = top20[t]
    O = top20[t + 1]

    m = int(E.sum())
    if m < 30:
        return None

    p_obs = float(O[E].mean())
    base = float(O.mean())

    # Hoán vị ngày xảy ra sự kiện, giữ nguyên số sự kiện m.
    # Cả quan sát lẫn hoán vị đều chia cho m.
    nulls = np.empty(N_PERM, dtype=float)
    n_valid = len(E)

    for b in range(N_PERM):
        idx = rng.permutation(n_valid)[:m]
        nulls[b] = float(O[idx].mean())

    null_tb = float(nulls.mean())
    null_sd = float(nulls.std(ddof=0))
    if null_sd == 0:
        null_sd = 1e-12

    thong_ke = (p_obs - null_tb) / null_sd
    p_value = float((np.sum(nulls >= p_obs) + 1) / (N_PERM + 1))

    return {
        "thong_ke": thong_ke,
        "p": p_value,
        "n": m,
        "quan_sat_tho": p_obs,
        "null_tb": null_tb,
        "null_sd": null_sd,
        "base": base,
        "event_rate": float(m / n_valid),
        "ghi_chu": (
            "Top20 theo phân vị 0.8 cuộn 100 phiên, tức là đã neo theo biến động "
            "cục bộ nên không cần chia ATR thêm. Sự kiện E_t chỉ dùng thông tin "
            "đến close_t; outcome là top20_{t+1}, biết sau close_{t+1}. Hoán vị "
            "xáo nhãn ngày sự kiện, giữ nguyên số sự kiện m, và cả hai vế đều chia "
            "cho cùng mẫu số m."
        ),
        "de_xuat": (
            "Thử điều kiện chặt hơn: top20 hôm nay kết hợp với volume cao bất thường "
            "để xem xác suất top20 phiên sau có tăng tiếp không."
        ),
    }