import numpy as np
import pandas as pd

try:
    import brain_co_che as bc
except Exception:
    bc = None


def _build_candidates(df, he_so):
    """Tạo các ứng viên: chân hiện tại i, chân cùng hướng trước i-2,
    chân ngược chiều tiếp theo i+1. Trả về dict hoặc None."""
    if bc is None:
        return None

    ch = bc.chan_song(df, he_so=he_so)
    if ch is None or len(ch) < 5:
        return None

    legs = bc.cac_doan(df, ch)
    if legs is None or len(legs) < 5:
        return None

    n = len(legs)
    amp = np.full(n, np.nan)
    avg_vol = np.full(n, np.nan)
    dur = np.full(n, np.nan)
    direction = np.zeros(n)

    for i in range(n):
        row = legs.iloc[i]
        a = int(row["tu"])
        b = int(row["den"])
        if a >= b:
            continue

        huong = row["huong"]
        if huong > 0:
            mau = df["low"].iloc[a]
            if mau > 0:
                amp[i] = df["high"].iloc[b] / mau - 1.0
            direction[i] = 1
        else:
            mau = df["high"].iloc[a]
            if mau > 0:
                amp[i] = mau / df["low"].iloc[b] - 1.0
            direction[i] = -1

        avg_vol[i] = df["volume"].iloc[a:b + 1].mean()
        tl = row.get("thoi_luong")
        if tl is not None and not pd.isna(tl) and tl > 0:
            dur[i] = float(tl)
        else:
            dur[i] = b - a

    ratios = []
    cur_durs = []
    next_durs = []
    dirs = []
    conds = []

    for i in range(2, n - 1):
        if not np.isfinite(amp[i]) or not np.isfinite(amp[i - 2]):
            continue
        if not np.isfinite(avg_vol[i]) or not np.isfinite(avg_vol[i - 2]):
            continue
        if dur[i] <= 0 or dur[i + 1] <= 0:
            continue

        cur_dur = dur[i]
        next_dur = dur[i + 1]

        # Luat 4: chuan hoa theo thoi luong chan hien tai
        ratio = next_dur / cur_dur

        # Dieu kien cua khang dinh
        cond = (amp[i] > 1.5 * amp[i - 2]) and (avg_vol[i] < avg_vol[i - 2])

        ratios.append(ratio)
        cur_durs.append(cur_dur)
        next_durs.append(next_dur)
        dirs.append(direction[i])
        conds.append(bool(cond))

    if len(ratios) < 30:
        return None

    ratios = np.asarray(ratios, dtype=float)
    cur_durs = np.asarray(cur_durs, dtype=float)
    next_durs = np.asarray(next_durs, dtype=float)
    dirs = np.asarray(dirs, dtype=int)
    conds = np.asarray(conds, dtype=bool)

    return {
        "ratios": ratios,
        "cur_durs": cur_durs,
        "next_durs": next_durs,
        "dirs": dirs,
        "conds": conds,
        "n_T": int(conds.sum()),
        "n_F": int((~conds).sum()),
        "he_so": he_so,
    }


def _perm_test(cand, rng, B=2000):
    ratios = cand["ratios"]
    conds = cand["conds"]
    dirs = cand["dirs"]

    obs = float(np.median(ratios[conds]))

    nulls = np.empty(B)
    for b in range(B):
        pc = conds.copy()
        for d in (1, -1):
            idx = dirs == d
            pc[idx] = rng.permutation(conds[idx])
        nulls[b] = float(np.median(ratios[pc]))

    null_mean = float(np.mean(nulls))
    null_sd = float(np.std(nulls, ddof=1))
    if null_sd <= 1e-12:
        return None

    # One-sided: ty le T thap hon ky vong ngau nhien => ung ho khang dinh
    p = float((1 + np.sum(nulls <= obs)) / (B + 1))
    thong_ke = (null_mean - obs) / null_sd

    return {
        "thong_ke": float(thong_ke),
        "p": p,
        "n": int(cand["n_T"]),
        "quan_sat_tho": obs,
        "null_tb": null_mean,
        "null_sd": null_sd,
        "trung_vi_ty_le_T": obs,
        "trung_vi_ty_le_F": float(np.median(ratios[~conds])),
        "n_T": int(cand["n_T"]),
        "n_F": int(cand["n_F"]),
    }


def do(khoa, df, rng):
    """Do khang dinh:
    Khi chan hien tai co bien do phan tram > 1.5 lan chan cung huong truoc
    nhung khoi luong trung binh moi phien thap hon, thi chan nguoc chieu
    tiep theo co so phien (tuong doi) nho hon ky vong ngau nhien.
    """
    if bc is None:
        return None

    # Chon he_so chan song theo SO MAU, khong theo ket qua
    cand = None
    for hs in (3.0, 2.0, 1.5):
        c = _build_candidates(df, hs)
        if c is not None and c["n_T"] >= 30 and c["n_F"] >= 30:
            cand = c
            break

    if cand is None:
        return None

    res = _perm_test(cand, rng, B=2000)
    if res is None:
        return None

    conds = cand["conds"]
    cur_T = cand["cur_durs"][conds]
    next_T = cand["next_durs"][conds]

    res["trung_vi_so_phien_T_hien_tai"] = float(np.median(cur_T))
    res["trung_vi_so_phien_T_tiep_theo"] = float(np.median(next_T))
    res["he_so_chan_song"] = cand["he_so"]

    res["ghi_chu"] = (
        "Do luong = ty le (so phien chan nguoc tiep theo) / (so phien chan hien tai), "
        "da chuan hoa theo thoi luong chan hien tai de giam tac dong cua volatility clustering. "
        "thong_ke = (null_tb - quan_sat_tho)/null_sd; duong = ty le o nhom dieu kien thap hon ky vong ngau nhien "
        "(ung ho khang dinh). Hoan vi nhan dieu kien trong tung huong chan hien tai, "
        "giu nguyen so su kien T/F. Chon he_so chan song theo so mau (>=30 su kien T)."
    )

    res["de_xuat"] = (
        "Thu ghep them dieu kien ATR thap hoac khoi luong giam lien tuc de loc "
        "nhung con song co dong lenh chu dong mong hon."
    )

    return res