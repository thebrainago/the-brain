import numpy as np
import pandas as pd
import brain_co_che as bc


def _build_events(ch, df, atr_arr):
    """Tao cac su kien: 2 nhip dieu chinh quanh 1 song day (doan giua lon nhat)."""
    try:
        vi = ch["vi_tri"].to_numpy().astype(int)
        gia = ch["gia"].to_numpy().astype(float)
        xac = ch["xac_nhan"].reset_index(drop=True)
    except Exception:
        return []

    volume = df["volume"].to_numpy(dtype=float)
    n_swing = len(vi)

    seg_vol = []
    seg_amp = []
    seg_dur = []
    seg_dir = []

    for k in range(n_swing - 1):
        p1 = int(vi[k])
        p2 = int(vi[k + 1])

        if p2 <= p1 or p1 < 0 or p2 >= len(volume):
            continue

        # Khong dung doan cuoi neu dinh/day chua duoc xac nhan.
        try:
            if pd.isna(xac.iloc[k + 1]):
                continue
        except Exception:
            pass

        n_bars = p2 - p1
        vol_slice = volume[p1 + 1:p2 + 1]
        atr_slice = atr_arr[p1 + 1:p2 + 1]

        if n_bars < 1 or vol_slice.size < 1 or atr_slice.size < 1:
            continue

        avg_vol = float(vol_slice.mean())
        ambient_atr = float(atr_slice.mean())

        if not (np.isfinite(avg_vol) and np.isfinite(ambient_atr)):
            continue
        if ambient_atr <= 0:
            continue

        bien_do = abs(float(gia[k + 1]) - float(gia[k])) / ambient_atr
        if not np.isfinite(bien_do):
            continue

        seg_vol.append(avg_vol)
        seg_amp.append(bien_do)
        seg_dur.append(int(n_bars))
        seg_dir.append(1 if gia[k + 1] > gia[k] else -1)

    m = len(seg_vol)
    events = []
    j = 0

    while j <= m - 3:
        # Doan giua la song day, hai ben la dieu chinh.
        ok_direction = (
            seg_dir[j] != seg_dir[j + 1]
            and seg_dir[j] == seg_dir[j + 2]
        )
        ok_impulse = (
            seg_amp[j + 1] > seg_amp[j]
            and seg_amp[j + 1] > seg_amp[j + 2]
        )

        if not (ok_direction and ok_impulse):
            j += 1
            continue

        vol1, vol2 = seg_vol[j], seg_vol[j + 2]
        if vol1 == vol2:
            j += 1
            continue

        # Phang: dai hon va bien do hep hon nhip thu nhat.
        flat = int(
            seg_dur[j + 2] > seg_dur[j]
            and seg_amp[j + 2] < seg_amp[j]
        )

        # Nhom 1: khoi luong trung binh moi nen giam.
        group = int(vol2 < vol1)

        events.append((group, flat))
        j += 3  # khong lay overlap de tranh phu thuoc qua lon

    return events


def do(khoa, df, rng):
    try:
        atr_raw = bc.atr(df, 14)
    except Exception:
        return None

    if atr_raw is None:
        return None

    if isinstance(atr_raw, pd.DataFrame):
        atr_raw = atr_raw.iloc[:, 0]

    atr_arr = atr_raw.to_numpy(dtype=float)
    if len(atr_arr) != len(df):
        return None

    events = None
    he_so_da_dung = None

    # Ha nguong chi de du mau, khong chon theo ket qua.
    for he_so in (3.0, 2.0, 1.5):
        try:
            ch = bc.chan_song(df, he_so=he_so)
        except Exception:
            ch = None

        if ch is None or len(ch) < 7:
            continue

        ch = ch.sort_values("vi_tri").reset_index(drop=True)
        ev = _build_events(ch, df, atr_arr)

        if len(ev) < 30:
            continue

        group = np.array([g for g, _ in ev], dtype=int)
        n_giam = int(group.sum())
        n_tang = len(ev) - n_giam

        if min(n_giam, n_tang) < 10:
            continue

        events = ev
        he_so_da_dung = he_so
        break

    if events is None:
        return None

    group = np.array([g for g, _ in events], dtype=int)
    flat = np.array([f for _, f in events], dtype=int)
    n = len(events)

    p_flat_giam = float(flat[group == 1].mean())
    p_flat_tang = float(flat[group == 0].mean())
    obs = p_flat_giam - p_flat_tang

    n_perm = 2000
    null = np.empty(n_perm)

    for i in range(n_perm):
        g_perm = rng.permutation(group)
        null[i] = flat[g_perm == 1].mean() - flat[g_perm == 0].mean()

    null_tb = float(null.mean())
    null_sd = float(null.std(ddof=1))

    if null_sd <= 1e-12:
        return None

    thong_ke = (obs - null_tb) / null_sd
    p = float((np.sum(null >= obs - 1e-12) + 1) / (n_perm + 1))

    return {
        "thong_ke": float(thong_ke),
        "p": p,
        "n": int(n),
        "quan_sat_tho": float(obs),
        "null_tb": null_tb,
        "null_sd": null_sd,
        "p_flat_giam": p_flat_giam,
        "p_flat_tang": p_flat_tang,
        "n_giam": int(group.sum()),
        "n_tang": int(n - group.sum()),
        "he_so": he_so_da_dung,
        "ghi_chu": (
            "Su kien: bo ba doan swing lien tiep, doan giua co bien do/ATR lon nhat "
            "duoc coi la song day, hai doan ben la nhip dieu chinh 1 va 2. "
            "Phang = thoi luong nhip 2 > nhip 1 VA bien do chuan hoa ATR nhip 2 < nhip 1. "
            "Nhom giam = khoi luong trung binh moi nen cua nhip 2 < nhip 1. "
            "Hoan vi gan lai nhan giam/tang giu so su kien moi nhom; p mot phia. "
            "Nguong swing duoc ha chi theo so mau."
        ),
    }