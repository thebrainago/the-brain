import numpy as np
import pandas as pd


def do(khoa, df, rng):
    if df is None or len(df) < 101:
        return None

    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    vol = df["volume"].to_numpy(dtype=float)
    ranges = high - low

    # Ngưỡng 90th percentile của 100 phiên TRƯỚC phiên i (không gồm phiên i).
    # rolling(100).quantile tại i-1 lấy range[i-100..i-1], shift(1) để khớp với i.
    q = (
        pd.Series(ranges)
        .rolling(100, min_periods=100)
        .quantile(0.9)
        .shift(1)
        .to_numpy()
    )

    # Trung bình khối lượng 20 phiên trước phiên i: volume[i-20..i-1].
    base = (
        pd.Series(vol)
        .rolling(20, min_periods=20)
        .mean()
        .shift(1)
        .to_numpy()
    )

    # Khối lượng phiên ngay sau phiên i.
    next_vol = np.full(len(vol), np.nan)
    if len(vol) > 1:
        next_vol[:-1] = vol[1:]

    # Biến nhị phân: volume sau có thấp hơn trung bình 20 phiên trước không?
    lower = next_vol < base

    # Chỉ giữ các ngày có đủ dữ liệu cho cả sự kiện lẫn outcome.
    valid = (
        np.isfinite(ranges)
        & np.isfinite(q)
        & np.isfinite(base)
        & np.isfinite(next_vol)
    )

    idx = np.where(valid)[0]
    if len(idx) == 0:
        return None

    event = valid & (ranges > q)
    e = event[idx]
    y = lower[idx].astype(float)

    n_event = int(e.sum())
    if n_event < 30:
        return None

    # Thống kê quan sát: tỷ lệ "volume sau thấp hơn baseline" trong các phiên biên độ lớn.
    obs = float(y[e].mean())

    # Null: gán ngẫu nhiên nhãn sự kiện cho các ngày đủ điều kiện,
    # giữ nguyên số sự kiện và outcome của từng ngày.
    null_tb = float(y.mean())

    n_perm = 2000
    L = len(y)
    perm_means = np.empty(n_perm)

    for b in range(n_perm):
        sel = rng.choice(L, size=n_event, replace=False)
        perm_means[b] = y[sel].mean()

    null_sd = float(perm_means.std(ddof=1))

    if null_sd == 0:
        z = 0.0
        p = 1.0
    else:
        z = (obs - null_tb) / null_sd
        # Một phía: dương ủng hộ khẳng định.
        p = float((np.sum(perm_means >= obs) + 1) / (n_perm + 1))

    return {
        "thong_ke": z,
        "p": p,
        "n": n_event,
        "quan_sat_tho": obs,
        "null_tb": null_tb,
        "null_sd": null_sd,
        "ty_le_thap_hon": obs,
        "ghi_chu": (
            "Sự kiện: range_i > percentile-90 của range[i-100..i-1]. "
            "Outcome: volume[i+1] < trung bình volume[i-20..i-1]. "
            "Thống kê là tỷ lệ outcome có lợi trong các sự kiện; so sánh với tỷ lệ nền "
            "(null_tb) qua hoán vị nhãn sự kiện, giữ nguyên số sự kiện và outcome đi kèm. "
            "Dương = ủng hộ khẳng định; p là p một phía."
        ),
        "de_xuat": (
            "Thử kết hợp với ATR thấp trước phiên biên độ lớn để tách hiệu ứng "
            "volatility clustering khỏi hiệu ứng hấp thụ thanh khoản."
        ),
    }