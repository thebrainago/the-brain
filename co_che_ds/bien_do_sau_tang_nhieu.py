import numpy as np
import pandas as pd
import brain_co_che as bc


def _la_up(x):
    if isinstance(x, str):
        return x.strip().lower() in ("up", "len", "tang", "+", "1", "+1", "1.0")
    try:
        return bool(x > 0)
    except Exception:
        return False


def _tinh_events(df, he_so):
    try:
        ch = bc.chan_song(df, he_so=he_so)
    except TypeError:
        ch = bc.chan_song(df)

    if ch is None or len(ch) < 2:
        return None

    seg = bc.cac_doan(df, ch)
    if seg is None or len(seg) < 2:
        return None

    seg = seg.sort_values("tu").reset_index(drop=True)

    h = df["high"].to_numpy(dtype=float)
    l = df["low"].to_numpy(dtype=float)
    c = df["close"].to_numpy(dtype=float)
    amp = h - l
    nbar = len(df)

    up_avg = []
    down_avg = []
    noisy = []

    for i in range(len(seg) - 1):
        s0 = seg.iloc[i]
        s1 = seg.iloc[i + 1]

        if not _la_up(s0["huong"]):
            continue
        if _la_up(s1["huong"]):
            continue

        tu = int(s0["tu"])
        den = int(s0["den"])
        tu2 = int(s1["tu"])
        den2 = int(s1["den"])

        if tu2 != den:
            continue
        if not (0 <= tu < den < nbar and den <= den2 < nbar):
            continue

        up_amp = float(amp[tu:den + 1].sum())
        up_len = den - tu + 1
        up_net = float(c[den] - c[tu])

        if up_net <= 0 or up_amp <= 0:
            continue

        down_amp = float(amp[den:den2 + 1].sum())
        down_len = den2 - den + 1

        if down_len <= 0 or down_amp <= 0:
            continue

        ua = up_amp / up_len
        da = down_amp / down_len

        if ua <= 0 or da <= 0:
            continue

        up_avg.append(ua)
        down_avg.append(da)
        noisy.append(up_net < up_amp / 3.0)

    if len(up_avg) < 30:
        return None

    return (
        np.array(up_avg, dtype=float),
        np.array(down_avg, dtype=float),
        np.array(noisy, dtype=bool),
    )


def do(khoa, df, rng):
    ev = None
    nguong = 3.0

    for he_so in (3.0, 1.5):
        ev = _tinh_events(df, he_so)
        if ev is not None:
            nguong = he_so
            break

    if ev is None:
        return None

    up_avg, down_avg, noisy = ev
    n_noisy = int(noisy.sum())
    n_ctrl = int((~noisy).sum())

    if n_noisy < 30 or n_ctrl < 10:
        return None

    log_ratio = np.log(down_avg / up_avg)
    obs = float(log_ratio[noisy].mean() - log_ratio[~noisy].mean())

    n_perm = 2000
    perm_stats = np.empty(n_perm)
    idx_noisy = noisy
    idx_ctrl = ~noisy

    for b in range(n_perm):
        d_perm = rng.permutation(down_avg)
        lr_perm = np.log(d_perm / up_avg)
        perm_stats[b] = lr_perm[idx_noisy].mean() - lr_perm[idx_ctrl].mean()

    null_tb = float(perm_stats.mean())
    null_sd = float(perm_stats.std(ddof=1))

    if not np.isfinite(null_sd) or null_sd <= 1e-12:
        return None

    thong_ke = (obs - null_tb) / null_sd
    p = float((1 + np.sum(perm_stats >= obs)) / (1 + n_perm))

    return {
        "thong_ke": float(thong_ke),
        "p": p,
        "n": int(len(up_avg)),
        "quan_sat_tho": obs,
        "null_tb": null_tb,
        "null_sd": null_sd,
        "n_noisy": n_noisy,
        "n_ctrl": n_ctrl,
        "mean_log_ratio_noisy": float(log_ratio[noisy].mean()),
        "mean_log_ratio_ctrl": float(log_ratio[~noisy].mean()),
        "ty_le_down_up_noisy": float(np.exp(log_ratio[noisy].mean())),
        "nguong_chan_song": nguong,
        "ghi_chu": (
            "Thước đo: log(tb_range_chan_giam / tb_range_chan_tang). "
            "Sự kiện = chân tăng có close cuối > close đầu và mức tăng ròng < 1/3 tổng(high-low); "
            "nhóm đối chứng = chân tăng dương còn lại. "
            "Thống kê quan sát = mean(log_ratio, nhiễu) - mean(log_ratio, đối chứng). "
            "Hoán vị giữ cố định nhãn nhiễu (số sự kiện nhiễu không đổi) và trộn ngẫu nhiên các chân giảm "
            "đi kèm; điều này phá móc thời gian nhưng giữ nguyên phân phối biên độ của cả hai phía. "
            "p là hoán vị một phía (dương = ủng hộ khẳng định). "
            "Nhận dạng chân dùng zigzag có xác nhận sau, nên là mô tả thống kê, không phải tín hiệu tại đỉnh/đáy. "
            "Biên độ dùng dạng log tỉ số nên tự chuẩn hóa; nếu nguồn chân bị hạ ngưỡng để đủ mẫu, ghi ở nguong_chan_song."
        ),
        "de_xuat": (
            "Thử tách theo độ dốc chân tăng (trên/dưới trung vị) hoặc theo trạng thái ATR đang tăng/giảm, "
            "vì 'nhiễu' có thể chỉ có ý nghĩa trong một chế độ thị trường."
        ),
    }