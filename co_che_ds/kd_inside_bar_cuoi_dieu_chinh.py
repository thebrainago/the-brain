import numpy as np
import brain_co_che as bc


def _mfe_forward(s, e, d, close, high, low):
    """MFE theo huong chan day, tinh tu close[bar xac nhan] den bar xac nhan tiep theo."""
    if e <= s:
        return np.nan
    start = s + 1
    end = e
    if start > end:
        return 0.0
    if d > 0:
        return float(max(0.0, high[start:end + 1].max() - close[s]))
    else:
        return float(max(0.0, close[s] - low[start:end + 1].min()))


def do(khoa, df, rng):
    ch = bc.chan_song(df)
    if ch is None or len(ch) < 6:
        return None

    vitri = np.asarray(ch["vi_tri"], dtype=int)
    xacnhan = np.asarray(ch["xac_nhan"], dtype=int)
    gia = np.asarray(ch["gia"], dtype=float)

    close = np.asarray(df["close"], dtype=float)
    high = np.asarray(df["high"], dtype=float)
    low = np.asarray(df["low"], dtype=float)

    dirs = np.sign(gia[1:] - gia[:-1]).astype(int)
    if len(dirs) < 3:
        return None

    leg_mfe = np.full(len(dirs), np.nan)
    for q in range(len(dirs)):
        leg_mfe[q] = _mfe_forward(
            xacnhan[q], xacnhan[q + 1], dirs[q], close, high, low
        )

    events = []

    for p in range(len(dirs) - 2):
        d = dirs[p]
        if d == 0:
            continue
        if dirs[p + 1] != -d or dirs[p + 2] != d:
            continue
        if not np.isfinite(leg_mfe[p]) or not np.isfinite(leg_mfe[p + 2]):
            continue

        # Bar cuoi cua chan dieu chinh la swing that su; da nam trong qua khu
        # khi swing duoc xac nhan.
        t = vitri[p + 2]
        if t <= 0 or t >= len(df):
            continue

        inside = bool((high[t] < high[t - 1]) and (low[t] > low[t - 1]))

        # Trung binh MFE cua toi da 5 chan day cung huong gan nhat truoc do.
        vals = []
        cnt = 0
        for q in range(p, -1, -1):
            if dirs[q] == d and np.isfinite(leg_mfe[q]):
                vals.append(float(leg_mfe[q]))
                cnt += 1
                if cnt >= 5:
                    break
        if len(vals) == 0:
            continue

        mean_prev = float(np.mean(vals))
        next_mfe = float(leg_mfe[p + 2])
        outcome = 1 if next_mfe > mean_prev else 0

        events.append((inside, outcome))

    if len(events) < 30:
        return None

    inside_arr = np.array([e[0] for e in events], dtype=bool)
    out_arr = np.array([e[1] for e in events], dtype=float)

    n_inside = int(inside_arr.sum())
    n_outside = int((~inside_arr).sum())
    if n_inside < 5 or n_outside < 5:
        return None

    n_perm = 2000
    obs_diff = float(out_arr[inside_arr].mean() - out_arr[~inside_arr].mean())

    perm_diffs = np.empty(n_perm, dtype=float)
    for b in range(n_perm):
        lab = inside_arr[rng.permutation(len(events))]
        perm_diffs[b] = out_arr[lab].mean() - out_arr[~lab].mean()

    null_tb = float(np.mean(perm_diffs))
    null_sd = float(np.std(perm_diffs, ddof=1))
    if null_sd == 0:
        return None

    thong_ke = (obs_diff - null_tb) / null_sd
    p_value = float((np.sum(perm_diffs >= obs_diff) + 1) / (n_perm + 1))

    if not np.isfinite(thong_ke) or not np.isfinite(p_value):
        return None

    return {
        "thong_ke": thong_ke,
        "p": p_value,
        "n": len(events),
        "quan_sat_tho": obs_diff,
        "null_tb": null_tb,
        "null_sd": null_sd,
        "n_inside": n_inside,
        "n_khong_inside": n_outside,
        "ghi_chu": (
            "Dung bc.chan_song. MFE tinh tu close(bar xac nhan cuoi dieu chinh) "
            "den bar xac nhan cuoi chan day tiep theo, theo huong chan day, "
            "de tranh nhin truoc. inside kiem tra tai vi_tri cua swing cuoi dieu chinh "
            "(da biet o thoi diem xac nhan). Bien do so voi trung binh MFE cua toi da "
            "5 chan day cung huong gan nhat truoc do, nen da tu chuan hoa theo bien dong "
            "dia phuong."
        ),
        "de_xuat": (
            "Thu ghep dieu kien inside bar voi ATR thap hoac vi tri gan moc 52 tuan."
        ),
    }