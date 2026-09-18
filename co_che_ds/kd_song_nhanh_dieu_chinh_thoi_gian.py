import numpy as np
import pandas as pd

try:
    import brain_co_che as bc
except Exception:
    bc = None

N_PERM = 2000
HE_SO = 1.5
ATR_LEN = 14


def _to_pos(df, x):
    """Chuyen vi_tri / xac_nhan ve vi tri integer trong df."""
    if x is None:
        raise ValueError("null swing position")

    if isinstance(x, (float, np.floating)):
        if np.isfinite(x) and float(x).is_integer():
            x = int(x)
        else:
            raise ValueError("non-integer swing position")

    if isinstance(x, (int, np.integer)):
        try:
            return int(df.index.get_loc(x))
        except (KeyError, TypeError, ValueError):
            return int(x)

    return int(df.index.get_loc(x))


def _atr_val(atr, pos):
    try:
        if hasattr(atr, "iloc"):
            return float(atr.iloc[pos])
        return float(atr[pos])
    except Exception:
        return float("nan")


def _atr_series(df, period=ATR_LEN):
    if bc is not None:
        try:
            a = bc.atr(df, period)
            if a is not None:
                return a
        except Exception:
            pass

    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)

    prev_close = np.empty_like(close)
    prev_close[0] = close[0]
    prev_close[1:] = close[:-1]

    tr = np.maximum(
        high - low,
        np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)),
    )

    atr = np.empty_like(tr)
    atr[0] = tr[0]
    alpha = 1.0 / period
    for i in range(1, len(tr)):
        atr[i] = atr[i - 1] + alpha * (tr[i] - atr[i - 1])

    return pd.Series(atr, index=df.index)


def _extract(df):
    if bc is None:
        return []

    try:
        ch = bc.chan_song(df, he_so=HE_SO)
    except TypeError:
        ch = bc.chan_song(df)
    except Exception:
        return []

    if ch is None or len(ch) < 4:
        return []

    try:
        poss = np.array([_to_pos(df, v) for v in ch["vi_tri"]], dtype=int)
        confs = np.array([_to_pos(df, v) for v in ch["xac_nhan"]], dtype=int)
        prices = np.asarray(ch["gia"], dtype=float)
    except Exception:
        return []

    ok = np.isfinite(prices) & (poss >= 0) & (confs >= 0)
    poss = poss[ok]
    confs = confs[ok]
    prices = prices[ok]

    if len(poss) < 4:
        return []

    order = np.argsort(poss, kind="stable")
    poss = poss[order]
    confs = confs[order]
    prices = prices[order]

    atr = _atr_series(df, ATR_LEN)

    segments = []
    for i in range(len(poss) - 1):
        start_pos = poss[i]
        end_pos = poss[i + 1]
        dur = max(1, end_pos - start_pos)
        amp = abs(float(prices[i + 1]) - float(prices[i]))
        is_up = float(prices[i + 1]) > float(prices[i])

        # Chuan hoa toc do bang ATR ngay tai dinh that su cua song tang,
        # tuc la truoc khi nhịp dieu chinh bat dau.
        a = _atr_val(atr, end_pos)
        speed = amp / dur
        if np.isfinite(a) and a > 0:
            speed = speed / a

        segments.append(
            {
                "up": bool(is_up),
                "end_pos": end_pos,
                "end_conf": confs[i + 1],
                "end_price": float(prices[i + 1]),
                "dur": dur,
                "amp": amp,
                "speed": float(speed),
            }
        )

    eligible = []

    for s in range(1, len(segments) - 1):
        if not segments[s]["up"]:
            continue
        if segments[s + 1]["up"]:
            continue
        if s < 2 or not segments[s - 2]["up"]:
            continue

        cur = segments[s]
        down = segments[s + 1]
        prev = segments[s - 2]

        if not (np.isfinite(cur["speed"]) and np.isfinite(prev["speed"]) and prev["speed"] > 0):
            continue

        # Doan sau phai la doan giam thuc su.
        if down["end_price"] >= cur["end_price"]:
            continue

        # Dieu kien phai duoc xac nhan truoc khi ket cuc (day dieu chinh) duoc xac nhan.
        if cur["end_conf"] >= down["end_conf"]:
            continue

        accel = cur["speed"] >= 2.0 * prev["speed"]

        time_pull = (down["dur"] > 0.5 * cur["dur"]) and (down["amp"] < 0.5 * cur["amp"])

        eligible.append({"accel": bool(accel), "time": bool(time_pull)})

    return eligible


def do(khoa, df, rng):
    eligible = _extract(df)

    if len(eligible) < 30:
        return None

    accel = np.array([e["accel"] for e in eligible], dtype=bool)
    time = np.array([e["time"] for e in eligible], dtype=bool)

    n_acc = int(accel.sum())
    if n_acc < 30:
        return None

    obs = float(time[accel].mean())

    perm = np.empty(N_PERM, dtype=float)
    for b in range(N_PERM):
        accel_shuf = rng.permutation(accel)
        perm[b] = float(time[accel_shuf].mean())

    null_mean = float(perm.mean())
    null_sd = float(perm.std(ddof=1)) if N_PERM > 1 else 0.0

    if null_sd < 1e-12:
        thong_ke = 0.0
        p = 1.0
    else:
        # Duong = ung ho khang dinh: xac suat time-pullback cao hon null.
        thong_ke = (obs - null_mean) / null_sd
        p = float((1 + np.sum(perm >= obs)) / (1 + N_PERM))

    return {
        "thong_ke": float(thong_ke),
        "p": float(p),
        "n": n_acc,
        "quan_sat_tho": obs,
        "null_tb": null_mean,
        "null_sd": null_sd,
        "n_up_hop_le": int(len(eligible)),
        "n_acc": n_acc,
        "n_time_pullback_trong_nhanh": int(time[accel].sum()),
        "ty_le_time_pullback_chung": float(time.mean()),
        "ghi_chu": (
            f"Chan song voi he_so={HE_SO}; toc do = bien do / thoi luong / ATR(14) "
            "tai dinh that su cua song tang (khong dung thong tin sau dinh). "
            "Chi giu mau khi dinh duoc xac nhan truoc khi day dieu chinh duoc xac nhan, "
            "de dieu kien co truoc khi biet ket cuc. "
            "Hoan vi nhan 'toc do gap doi', giu nguyen so su kien va ty le time-pullback. "
            "p la hoan vi mot phia (cao hon); thong_ke duong ung ho khang dinh."
        ),
    }