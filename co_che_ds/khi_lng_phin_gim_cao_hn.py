import numpy as np
import pandas as pd


def _thong_ke_quan_sat(bin_data):
    """bin_data: list of (dir_array, vol_array, vol_sum, n_down)."""
    t = 0.0
    wsum = 0.0
    for d0, v, vsum, nd in bin_data:
        nu = len(d0) - nd
        if nd == 0 or nu == 0:
            continue
        w = nd if nd < nu else nu
        s_down = v[d0 < 0].sum()
        s_up = vsum - s_down
        t += w * (s_down / nd - s_up / nu)
        wsum += w
    return t / wsum if wsum > 0 else np.nan


def do(khoa, df, rng):
    df = df.copy()

    # Không dùng phiên có volume = 0
    df = df[df["volume"] > 0]

    # Volume chuẩn hoá: log(volume / median volume 20 phiên trước)
    # rolling().median() rồi shift(1) => không nhìn tương lai.
    trailing_med = df["volume"].rolling(20, min_periods=10).median().shift(1)
    trailing_med = trailing_med.replace(0, np.nan)
    df["vol_norm"] = np.log(df["volume"] / trailing_med)

    # |return| từ mở cửa đến đóng cửa
    open_ = df["open"].replace(0, np.nan)
    ret = df["close"] / open_ - 1.0
    ret = ret.replace([np.inf, -np.inf], np.nan)
    df["ret"] = ret
    df["absret"] = ret.abs()

    df = df.dropna(subset=["ret", "vol_norm"])
    df = df[np.isfinite(df["vol_norm"]) & np.isfinite(df["absret"])]

    df["dir"] = np.sign(df["ret"]).astype(int)
    df = df[df["dir"] != 0]

    if len(df) < 30:
        return None

    up_n = int((df["dir"] > 0).sum())
    down_n = int((df["dir"] < 0).sum())
    if up_n < 30 or down_n < 30:
        return None

    # Chia thành các nhóm có |return| tương đương.
    # Đây chỉ là biến điều kiện để so sánh cùng mức độ dịch chuyển giá,
    # không phải ngưỡng sinh tín hiệu giao dịch.
    try:
        bin_ids, _ = pd.qcut(
            df["absret"], q=10, labels=False, retbins=True, duplicates="drop"
        )
    except Exception:
        return None

    bin_ids = np.asarray(bin_ids).astype(int)
    unique_bins = np.unique(bin_ids)
    if len(unique_bins) < 2:
        return None

    dirs = df["dir"].to_numpy()
    vols = df["vol_norm"].to_numpy(dtype=float)

    bin_indices = [np.where(bin_ids == b)[0] for b in unique_bins]
    bin_data = []
    for idx in bin_indices:
        d0 = dirs[idx]
        v = vols[idx]
        nd = int((d0 < 0).sum())
        if nd > 0 and len(d0) - nd > 0:
            bin_data.append((d0, v, float(v.sum()), nd))

    if len(bin_data) < 2:
        return None

    obs = _thong_ke_quan_sat(bin_data)
    if not np.isfinite(obs):
        return None

    N_PERM = 2000
    nulls = np.empty(N_PERM)

    for k in range(N_PERM):
        t = 0.0
        wsum = 0.0
        for d0, v, vsum, nd in bin_data:
            nu = len(d0) - nd
            w = nd if nd < nu else nu

            # Hoán vị nhãn down/up trong cùng bin => giữ số sự kiện
            # và tỷ lệ mua-bán trong từng nhóm |return|.
            d_shuf = rng.permutation(d0)
            s_down = v[d_shuf < 0].sum()
            s_up = vsum - s_down

            t += w * (s_down / nd - s_up / nu)
            wsum += w

        if wsum > 0:
            nulls[k] = t / wsum
        else:
            nulls[k] = np.nan

    nulls = nulls[np.isfinite(nulls)]
    if len(nulls) < 100:
        return None

    null_tb = float(np.mean(nulls))
    null_sd = float(np.std(nulls, ddof=1))
    if null_sd == 0:
        return None

    z = (obs - null_tb) / null_sd
    # Một phía: down > up
    p = float((1 + int(np.sum(nulls >= obs))) / (len(nulls) + 1))

    return {
        "khoa": khoa,
        "thong_ke": z,
        "p": p,
        "n": int(len(df)),
        "quan_sat_tho": obs,
        "null_tb": null_tb,
        "null_sd": null_sd,
        "up_n": up_n,
        "down_n": down_n,
        "up_vol_tb": float(np.mean(vols[dirs > 0])),
        "down_vol_tb": float(np.mean(vols[dirs < 0])),
        "ghi_chu": (
            "Volume chuẩn hoá = log(volume / median volume 20 phiên trước, "
            "chỉ dùng quá khứ). So sánh trong từng bin |return mở-đóng|; "
            "thống kê là trung bình có trọng số của (down_vol - up_vol) theo bin. "
            "Hoán vị nhãn down/up trong từng bin, giữ số lượng và tỷ lệ mỗi bin, 2000 lần. "
            "p một phía (down > up); thống kê dương ủng hộ khẳng định. "
            "qcut dùng toàn chuỗi chỉ để định nghĩa bin so sánh, không phải ngưỡng sinh lệnh."
        ),
        "de_xuat": (
            "Nếu hiệu ứng đúng, thử kết hợp điều kiện ATR thấp: "
            "bất đối xứng thanh khoản khi giảm có thể mạnh hơn trong chế độ biến động thấp."
        ),
    }