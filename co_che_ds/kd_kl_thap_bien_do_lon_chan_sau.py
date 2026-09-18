import numpy as np
import pandas as pd

try:
    import brain_co_che as bc
except Exception:
    bc = None


def _tinh_atr(df, period=14):
    if bc is not None:
        try:
            atr = bc.atr(df, period)
            if isinstance(atr, pd.DataFrame):
                atr = atr.iloc[:, 0]
            if atr is not None:
                if isinstance(atr, pd.Series):
                    return atr.reset_index(drop=True)
                return pd.Series(np.asarray(atr).ravel(), index=df.index)
        except Exception:
            pass

    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period).mean().reset_index(drop=True)


def _xay_events(ch, dfw, atr):
    legs = []

    for i in range(len(ch) - 1):
        s = int(ch["vi_tri"].iloc[i])
        e = int(ch["vi_tri"].iloc[i + 1])

        if e <= s or s >= len(dfw) or e >= len(dfw):
            continue

        p0 = float(ch["gia"].iloc[i])
        p1 = float(ch["gia"].iloc[i + 1])
        direction = 1 if p1 > p0 else (-1 if p1 < p0 else 0)
        if direction == 0:
            continue

        chunk = dfw.iloc[s:e + 1]
        avg_vol = chunk["volume"].mean()
        avg_amp = (chunk["high"] - chunk["low"]).mean()

        if avg_vol <= 0 or avg_amp <= 0:
            continue

        legs.append({
            "start": s,
            "end": e,
            "direction": direction,
            "dur": e - s,
            "avg_vol": avg_vol,
            "avg_amp": avg_amp,
            "net": abs(p1 - p0),
        })

    events = []

    # Hai chan cung chieu lien tiep cach nhau mot chan nguoc.
    # A = chan thu nhat, B = chan thu hai, C = dieu chinh sau B.
    for i in range(len(legs) - 3):
        A = legs[i]
        B = legs[i + 2]
        C = legs[i + 3]

        if A["direction"] != B["direction"]:
            continue
        if C["direction"] != -B["direction"]:
            continue
        if A["end"] >= B["start"] or B["end"] > C["start"]:
            continue
        if B["dur"] <= 0 or C["dur"] <= 0:
            continue

        vol_ratio = B["avg_vol"] / A["avg_vol"]
        amp_ratio = B["avg_amp"] / A["avg_amp"]

        dieu_kien = (vol_ratio < 1.0) and (amp_ratio > 1.0)
        doi_chung = (vol_ratio >= 1.0)

        if not (dieu_kien or doi_chung):
            continue

        atr_start = atr.iloc[C["start"]]
        if not np.isfinite(atr_start) or atr_start <= 0:
            continue

        # Luat 4: do nhon duoc chuan hoa boi bien do tu nhien tai diem bat dau.
        do_nhon = C["net"] / C["dur"] / atr_start

        events.append((dieu_kien, doi_chung, float(do_nhon), int(C["direction"])))

    return events


def _perm_test(y, labels, dirs, rng, n_perm=2000):
    y = np.asarray(y, dtype=float)
    labels = np.asarray(labels, dtype=int)
    dirs = np.asarray(dirs, dtype=int)

    n = len(y)
    n_cond = int((labels == 1).sum())
    n_ctrl = int((labels == 0).sum())

    if n < 30 or n_cond < 10 or n_ctrl < 10:
        return None

    obs = y[labels == 1].mean() - y[labels == 0].mean()
    nulls = np.empty(n_perm)
    dir_vals = np.unique(dirs)

    for b in range(n_perm):
        lab = labels.copy()
        for d in dir_vals:
            idx = np.where(dirs == d)[0]
            if len(idx) > 1:
                lab[idx] = labels[rng.permutation(idx)]
        nulls[b] = y[lab == 1].mean() - y[lab == 0].mean()

    null_tb = float(nulls.mean())
    null_sd = float(nulls.std(ddof=1)) if len(nulls) > 1 else 0.0

    if null_sd <= 0:
        return None

    p = float((np.sum(nulls >= obs) + 1) / (n_perm + 1))
    thong_ke = float((obs - null_tb) / null_sd)

    return {
        "thong_ke": thong_ke,
        "p": p,
        "n": int(n),
        "quan_sat_tho": float(obs),
        "null_tb": null_tb,
        "null_sd": null_sd,
        "n_dieu_kien": n_cond,
        "n_doi_chung": n_ctrl,
        "sharp_tb_dieu_kien": float(y[labels == 1].mean()),
        "sharp_tb_doi_chung": float(y[labels == 0].mean()),
    }


def do(khoa, df, rng):
    if bc is None:
        return None

    dfw = df.reset_index(drop=True).copy()
    for col in ["open", "high", "low", "close", "volume"]:
        if col not in dfw.columns:
            return None

    atr = _tinh_atr(dfw, 14)

    for he_so in [1.5, 1.2, 1.0]:
        he_so_dung = he_so
        try:
            ch = bc.chan_song(dfw, he_so=he_so)
        except TypeError:
            ch = bc.chan_song(dfw)
            he_so_dung = "mac_dinh"

        if ch is None:
            continue

        if not isinstance(ch, pd.DataFrame):
            ch = pd.DataFrame(ch)

        if "vi_tri" not in ch.columns:
            continue

        ch = ch.copy()
        for col in ["vi_tri", "xac_nhan"]:
            if col in ch.columns:
                ch[col] = pd.to_numeric(ch[col], errors="coerce")

        ch = ch.dropna(subset=["vi_tri"])
        if len(ch) < 4:
            continue

        ch = ch.sort_values("vi_tri").reset_index(drop=True)
        ch["vi_tri"] = ch["vi_tri"].astype(int)

        events = _xay_events(ch, dfw, atr)
        if len(events) < 30:
            continue

        y = np.array([e[2] for e in events], dtype=float)
        labels = np.array([1 if e[0] else 0 for e in events], dtype=int)
        dirs = np.array([e[3] for e in events], dtype=int)

        n_cond = int((labels == 1).sum())
        n_ctrl = int((labels == 0).sum())
        if n_cond < 10 or n_ctrl < 10:
            continue

        res = _perm_test(y, labels, dirs, rng)
        if res is None:
            continue

        res["he_so_zigzag"] = he_so_dung
        res["ghi_chu"] = (
            f"Zigzag ha nguong he_so={he_so_dung}; ha nguong theo so mau, khong theo ket qua. "
            "Bien do moi nen = trung binh high-low trong chan; khoi luong moi nen = trung binh volume. "
            "Do nhon cua dieu chinh = |bien dong gia| / thoi_luong / ATR tai diem bat dau dieu chinh. "
            "Nhom dieu kien: chan thu hai co volume moi nen thap hon va bien do moi nen lon hon chan thu nhat. "
            "Nhom doi chung: chan thu hai co volume moi nen cao hon. "
            "p la mot phia, duong = ung ho khang dinh."
        )
        res["de_xuat"] = (
            "Ghep them dieu kien chan thu hai vuot qua dinh/day truoc do "
            "de loc loai song co kha nang can kiet."
        )

        return res

    return None