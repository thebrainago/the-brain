import numpy as np
import pandas as pd
import brain_co_che as bc


def _atr_tai(atr, pos):
    pos = int(pos)
    if pos < 0 or pos >= len(atr):
        return np.nan
    for j in range(pos, -1, -1):
        v = atr[j]
        if np.isfinite(v) and v > 0:
            return float(v)
    return np.nan


def do(khoa, df, rng):
    try:
        ch = bc.chan_song(df, he_so=1.5)
    except TypeError:
        ch = bc.chan_song(df)

    if ch is None or len(ch) < 8:
        return None

    try:
        atr_series = bc.atr(df, 14)
    except Exception:
        return None

    if atr_series is None:
        return None

    if isinstance(atr_series, pd.DataFrame):
        atr_series = atr_series.iloc[:, 0]
    atr = atr_series.to_numpy(dtype=float)

    ch = ch.sort_values(["xac_nhan", "vi_tri"]).reset_index(drop=True)

    legs = []
    prev = None

    for _, r in ch.iterrows():
        try:
            xac = int(r["xac_nhan"])
            pos = int(r["vi_tri"])
            gia = float(r["gia"])
        except (KeyError, ValueError, TypeError):
            continue

        if not (0 <= pos < len(df)) or not (0 <= xac < len(df)):
            continue

        if prev is not None:
            ppos, pgia = prev
            if pos != ppos and gia != pgia:
                direction = 1 if gia > pgia else -1
                n_candle = abs(pos - ppos) + 1
                raw_range = abs(gia - pgia)
                denom = _atr_tai(atr, pos)
                if np.isfinite(denom):
                    legs.append({
                        "dir": direction,
                        "n": n_candle,
                        "range": raw_range / denom,
                        "xac": xac,
                    })

        prev = (pos, gia)

    if len(legs) < 6:
        return None

    events = []

    for i in range(len(legs) - 3):
        if (
            legs[i]["dir"] == 1
            and legs[i + 1]["dir"] == -1
            and legs[i + 2]["dir"] == 1
            and legs[i + 3]["dir"] == -1
        ):
            up1, down1, up2, down2 = (
                legs[i],
                legs[i + 1],
                legs[i + 2],
                legs[i + 3],
            )

            qual = (up2["n"] > up1["n"]) and (up2["range"] <= up1["range"])
            out = down2["n"] < down1["n"]
            events.append((qual, out))

    if len(events) < 10:
        return None

    qual = np.array([e[0] for e in events], dtype=bool)
    out = np.array([e[1] for e in events], dtype=float)

    n_q = int(qual.sum())
    n_nq = int((~qual).sum())

    if n_q < 30 or n_nq < 30:
        return None

    obs = float(out[qual].mean() - out[~qual].mean())

    n_perm = 2000
    perm_stats = np.empty(n_perm)

    for k in range(n_perm):
        q_perm = rng.permutation(qual)
        perm_stats[k] = float(out[q_perm].mean() - out[~q_perm].mean())

    null_mean = float(perm_stats.mean())
    null_sd = float(perm_stats.std(ddof=1))

    if not np.isfinite(null_sd) or null_sd <= 1e-12:
        return None

    thong_ke = (obs - null_mean) / null_sd

    # Một phía: chỉ ủng hộ khẳng định khi diff quan sát > diff hoán vị.
    p = float((np.sum(perm_stats >= obs) + 1) / (n_perm + 1))

    return {
        "thong_ke": float(thong_ke),
        "p": p,
        "n": n_q,
        "quan_sat_tho": obs,
        "null_tb": null_mean,
        "null_sd": null_sd,
        "so_su_kien": len(events),
        "so_thoa_dieu_kien": n_q,
        "ty_le_down2_ngan_hon": float(out[qual].mean()),
        "ty_le_nen": float(out.mean()),
        "he_so_swing": 1.5,
        "ghi_chu": (
            "Dùng swing 1.5xATR để có đủ mẫu. Mỗi sự kiện là bộ Up1-Down1-Up2-Down2; "
            "điều kiện: nến(Up2) > nến(Up1) và range/ATR(Up2) <= range/ATR(Up1); "
            "outcome: nến(Down2) < nến(Down1). Biên độ chuẩn hoá bằng ATR(14) tại đỉnh "
            "của chân, không dùng ATR tại xac_nhan để tránh lộ thông tin nhịp điều chỉnh. "
            "Hoán vị giữ nguyên số sự kiện, số sự kiện thoả điều kiện và tỉ lệ outcome. "
            "p là p một phía (phải), thong_ke neo về null."
        ),
        "de_xuat": (
            "Thử kết hợp điều kiện này với trạng thái ATR thấp hoặc vùng kháng cự để tạo "
            "bộ lọc thoát lệnh sớm khi giá tăng nhiều phiên nhưng không mở rộng biên độ."
        ),
    }