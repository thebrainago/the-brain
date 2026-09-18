import numpy as np
import pandas as pd


def do(khoa, df, rng):
    if df is None or len(df) < 253:
        return None
    if not df.index.is_monotonic_increasing:
        df = df.sort_index()

    ca = (df["high"] - df["low"]).to_numpy()
    close = df["close"].to_numpy()
    open_ = df["open"].to_numpy()
    n = len(df)

    # Nhan gan tai close i: high-low[i] thuoc nhom 10% lon nhat
    # trong cua so 252 phien ket thuc tai i.
    WINDOW = 252
    roll_q = pd.Series(ca).rolling(WINDOW, min_periods=WINDOW).quantile(0.9).to_numpy()

    sign = np.zeros(n, dtype=int)
    sign[close > open_] = 1
    sign[close < open_] = -1

    idx = np.flatnonzero(
        (ca >= roll_q)
        & (sign != 0)
        & (np.arange(n) < n - 1)
        & (ca > 0)
        & (np.isfinite(ca))
        & (np.isfinite(roll_q))
    )

    if idx.size < 60:
        return None

    labels = sign[idx]

    # Luat 4: chia cho bien do duong nhien cua phien hien tai.
    outcome = ca[idx + 1] / ca[idx]

    keep = np.isfinite(outcome)
    labels = labels[keep]
    outcome = outcome[keep]

    n_down = int(np.sum(labels == -1))
    n_up = int(np.sum(labels == 1))

    if n_down < 30 or n_up < 30:
        return None

    down_mean = float(outcome[labels == -1].mean())
    up_mean = float(outcome[labels == 1].mean())
    obs = down_mean - up_mean

    n_perm = 2000
    perms = np.empty(n_perm)
    for b in range(n_perm):
        perm_labels = rng.permutation(labels)
        down_mask = perm_labels == -1
        perms[b] = outcome[down_mask].mean() - outcome[~down_mask].mean()

    null_tb = float(perms.mean())
    null_sd = float(perms.std(ddof=1)) if n_perm > 1 else 0.0

    if null_sd == 0:
        return None

    thong_ke = (obs - null_tb) / null_sd
    p = float((1 + np.sum(perms >= obs)) / (n_perm + 1))

    return {
        "thong_ke": float(thong_ke),
        "p": p,
        "n": int(labels.size),
        "n_down": n_down,
        "n_up": n_up,
        "n_perm": n_perm,
        "quan_sat_tho": float(obs),
        "tb_down": down_mean,
        "tb_up": up_mean,
        "null_tb": null_tb,
        "null_sd": null_sd,
        "ghi_chu": (
            "Su kien: phien i co close<open (giam) hoac close>open (tang), "
            "va high-low[i] >= phan vi 90% cua chinh no trong cua so 252 phien ket thuc tai i. "
            "Nhan gan tai close i, khong ve lai khi co bar moi. "
            "Do luong: high-low[i+1] / high-low[i] (chia bien do duong nhien theo luat 4). "
            "Thong ke = mean_down - mean_up; duong = ung ho khang dinh. "
            "Hoan vi chi dao nhan giam/tang giua cac su kien da co, giu nguyen so su kien moi nhom "
            "va giu nguyen vector outcome tuong ung voi ngay su kien. "
            "Ca quan sat va hoan vi dung cung n_down/n_up (cung mau so). p la mot phia."
        ),
        "de_xuat": (
            "Ghep dieu kien voi ATR(14) dang tren trung binh 252 hoac volume dot bien "
            "de xem ap luc giam co tap trung vao cac dot thanh ly khong."
        ),
    }