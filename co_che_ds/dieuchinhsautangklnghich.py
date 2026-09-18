import numpy as np
import pandas as pd

try:
    import brain_co_che as bc
except Exception:
    bc = None


def _pos(df, v):
    """Chuyen vi_tri/xac_nhan (int hoac nhan) sang vi tri nguyen trong df."""
    if v is None:
        return None
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        if np.isnan(v):
            return None
        if float(v).is_integer():
            return int(v)
    try:
        loc = df.index.get_loc(v)
        if isinstance(loc, slice):
            return loc.start
        if isinstance(loc, np.ndarray):
            return int(loc[0]) if len(loc) else None
        return int(loc)
    except Exception:
        return None


def _loai_sign(v):
    """Nhan dien loai chan: 1 = dinh, -1 = day, 0 = khong ro."""
    if isinstance(v, str):
        s = v.strip().lower().replace("đ", "d").replace("á", "a")
        if s in ("dinh", "d", "high", "h", "peak", "p", "top", "up", "bull", "tang", "1", "+1"):
            return 1
        if s in ("day", "n", "low", "l", "trough", "tr", "bottom", "b", "down", "bear", "giam", "-1"):
            return -1
        try:
            x = float(v)
            return 1 if x > 0 else -1 if x < 0 else 0
        except Exception:
            return 0
    try:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return 0
        if v > 0:
            return 1
        if v < 0:
            return -1
    except Exception:
        pass
    return 0


def _atr(df, n=14):
    """Lay ATR tu brain_co_che, neu loi thi tu tinh Wilder de khong chet."""
    if bc is not None:
        try:
            a = bc.atr(df, n)
            if a is not None:
                return a
        except Exception:
            pass
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False).mean()


def _atr_value(atr_s, df, pos):
    if atr_s is None or pos is None:
        return np.nan
    try:
        if isinstance(atr_s, pd.DataFrame):
            atr_s = atr_s.iloc[:, 0]
        if pos < 0 or pos >= len(atr_s):
            return np.nan
        v = atr_s.iloc[pos]
        return float(v)
    except Exception:
        return np.nan


def _swings(df, he_so):
    if bc is None:
        return None
    try:
        if he_so is None:
            ch = bc.chan_song(df)
        else:
            ch = bc.chan_song(df, he_so=he_so)
    except TypeError:
        ch = bc.chan_song(df)
    except Exception:
        return None
    if ch is None or len(ch) == 0:
        return None
    for col in ("vi_tri", "xac_nhan", "gia", "loai"):
        if col not in ch.columns:
            return None
    return ch.sort_values("vi_tri").reset_index(drop=True)


def _build_events(df):
    atr_s = _atr(df, 14)
    ch = _swings(df, 3.0)
    if ch is None or len(ch) < 3:
        return [], []

    xs = []
    ys = []

    for i in range(len(ch) - 2):
        a, b, c = ch.iloc[i], ch.iloc[i + 1], ch.iloc[i + 2]

        if _loai_sign(a["loai"]) != -1:
            continue
        if _loai_sign(b["loai"]) != 1:
            continue
        if _loai_sign(c["loai"]) != -1:
            continue

        p0 = _pos(df, a["vi_tri"])
        p1 = _pos(df, b["vi_tri"])
        p2 = _pos(df, c["vi_tri"])
        px = _pos(df, b["xac_nhan"])

        if p0 is None or p1 is None or p2 is None or px is None:
            continue
        if p0 < 0 or p1 >= len(df) or p2 >= len(df) or px >= len(df):
            continue
        if p0 >= p1 or p1 >= p2:
            continue
        if px < p1:
            # xac_nhan khong duoc truoc chinh dinh
            continue

        try:
            gia_a = float(a["gia"]) if pd.notna(a["gia"]) else float(df.iloc[p0]["low"])
            gia_b = float(b["gia"]) if pd.notna(b["gia"]) else float(df.iloc[p1]["high"])
            gia_c = float(c["gia"]) if pd.notna(c["gia"]) else float(df.iloc[p2]["low"])
        except Exception:
            continue

        up_range = gia_b - gia_a
        corr_range = gia_b - gia_c
        if up_range <= 0 or corr_range <= 0:
            continue

        w = df.iloc[p0:p1 + 1]
        red_vol = float(w.loc[w["close"] < w["open"], "volume"].sum())
        green_vol = float(w.loc[w["close"] > w["open"], "volume"].sum())

        # Dieu kien cua khang dinh: tong KL phien do > tong KL phien xanh
        condition = red_vol > green_vol

        # Luat 4: chia cho bien dong tu nhien tai diem xac nhan dinh
        atr_val = _atr_value(atr_s, df, px)
        if not np.isfinite(atr_val) or atr_val <= 1e-12:
            continue

        # Thuc do: muc do dieu chinh sau do vuot qua bien do chan tang,
        # chuan hoa bang ATR.
        y = (corr_range - up_range) / atr_val

        xs.append(bool(condition))
        ys.append(float(y))

    return xs, ys


def do(khoa, df, rng):
    """Do khang dinh:
    Khi mot chan tang co tong khoi luong phien do > tong khoi luong phien xanh,
    thi chan dieu chinh ngay sau do co bien do lon hon chan tang do.
    """
    xs, ys = _build_events(df)

    if len(ys) < 30:
        return None

    x = np.asarray(xs, dtype=bool)
    y = np.asarray(ys, dtype=float)
    n = len(y)
    n_true = int(x.sum())
    n_false = n - n_true

    if n_true < 5 or n_false < 5:
        return None

    y_true = y[x]
    y_false = y[~x]
    quan_sat_tho = float(y_true.mean() - y_false.mean())

    n_perm = 2000
    null = np.empty(n_perm)
    for k in range(n_perm):
        xp = rng.permutation(x)
        null[k] = float(y[xp].mean() - y[~xp].mean())

    null_tb = float(null.mean())
    null_sd = float(null.std(ddof=1))
    if null_sd <= 1e-12:
        return None

    thong_ke = (quan_sat_tho - null_tb) / null_sd
    p = float((1 + int((null >= quan_sat_tho).sum())) / (n_perm + 1))

    return {
        "thong_ke": thong_ke,
        "p": p,
        "n": n,
        "quan_sat_tho": quan_sat_tho,
        "null_tb": null_tb,
        "null_sd": null_sd,
        "n_dieu_kien": n_true,
        "n_chung": n_false,
        "mean_dieu_kien": float(y_true.mean()),
        "mean_chung": float(y_false.mean()),
        "ghi_chu": (
            "Chan tang = doan tu day len dinh trong bc.chan_song(nguong 3xATR). "
            "Dieu kien: tong KL phien close<open trong chan tang > tong KL phien close>open. "
            "Thuc do = (bien_do_chan_dieu_chinh - bien_do_chan_tang) / ATR(14) tai xac_nhan dinh. "
            "Duong thong_ke ung ho khang dinh. "
            "p mot phia tu hoan vi nhan dieu kien, giu nguyen so su kien va ty le dieu kien."
        ),
        "de_xuat": (
            "Neu khang dinh nay song sot, thu ghep them dieu kien 'chan tang truoc do pha dinh cu' "
            "de loc cac nhom phan phoi trong uptrend."
        ),
    }