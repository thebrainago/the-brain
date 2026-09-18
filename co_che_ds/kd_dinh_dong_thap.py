import numpy as np
import pandas as pd
import brain_co_che as bc


def _pos(df, x):
    """Chuyen mot nhan (timestamp hoac vi tri int) sang vi tri int trong df."""
    if isinstance(x, (int, np.integer)):
        return int(x)

    try:
        loc = df.index.get_loc(x)
        if isinstance(loc, slice):
            return loc.start
        if isinstance(loc, np.ndarray):
            return int(loc[0])
        return int(loc)
    except Exception:
        return int(np.where(df.index == x)[0][0])


def _atr_val(atr_s, pos):
    """Lay gia tri ATR tai vi tri int; ho tro Series/DataFrame/ndarray."""
    if atr_s is None:
        return float("nan")

    if isinstance(atr_s, pd.DataFrame):
        if "atr" in atr_s.columns:
            atr_s = atr_s["atr"]
        else:
            atr_s = atr_s.iloc[:, 0]

    if isinstance(atr_s, pd.Series):
        try:
            return float(atr_s.iloc[pos])
        except Exception:
            return float(atr_s.loc[pos])

    return float(atr_s[pos])


def _collect_events(df, hs, atr_s):
    """Thu thap cac bo ba chan: len - xuong - len.

    Su kien:
      - co mot chan giam ket thuc tai day;
      - phiên tao day la bar o down['den'];
      - dieu kien: close(day) nam nua tren pham vi phiên;
      - outcome: do dai chan tang sau > do dai chan tang truoc.

    Do dai cac chan duoc chia cho ATR14 tai diem bat dau cua chan tang,
    de khu nhieu volatility clustering (luat 4).
    """
    ch = bc.chan_song(df, he_so=hs)
    if ch is None or len(ch) < 3:
        return None

    sg = bc.cac_doan(df, ch)
    if sg is None or len(sg) < 2:
        return None

    pivot_price = {}
    for r in ch.itertuples(index=False):
        p = _pos(df, r.vi_tri)
        pivot_price[p] = float(r.gia)

    segments = []
    for r in sg.itertuples(index=False):
        tu = _pos(df, r.tu)
        den = _pos(df, r.den)
        if tu == den:
            continue

        try:
            biet_tai = _pos(df, r.biet_tai)
        except Exception:
            biet_tai = None

        if tu in pivot_price and den in pivot_price:
            length = abs(pivot_price[den] - pivot_price[tu])
            direc = 1 if pivot_price[den] > pivot_price[tu] else -1
        else:
            try:
                length = abs(float(r.do_dai))
                direc = 1 if float(r.do_dai) > 0 else -1
            except Exception:
                continue

        if length <= 0:
            continue

        segments.append({
            "tu": tu,
            "den": den,
            "biet_tai": biet_tai,
            "dirn": direc,
            "length": length,
        })

    if len(segments) < 3:
        return None

    segments.sort(key=lambda s: s["tu"])

    cond_list = []
    succ_list = []

    for j in range(1, len(segments) - 1):
        down = segments[j]
        if down["dirn"] != -1:
            continue

        prev = segments[j - 1]
        nxt = segments[j + 1]

        if prev["dirn"] != 1 or nxt["dirn"] != 1:
            continue

        low_pos = down["den"]

        # Chan tang sau phai bat dau dung tai day cua chan giam.
        if low_pos != nxt["tu"]:
            continue

        bar = df.iloc[low_pos]
        mid = (float(bar["high"]) + float(bar["low"])) * 0.5
        cond = float(bar["close"]) > mid

        a_prev = _atr_val(atr_s, prev["tu"])
        a_next = _atr_val(atr_s, nxt["tu"])
        if not np.isfinite(a_prev) or a_prev <= 0:
            continue
        if not np.isfinite(a_next) or a_next <= 0:
            continue

        norm_prev = prev["length"] / a_prev
        norm_next = nxt["length"] / a_next
        if norm_prev <= 0 or norm_next <= 0:
            continue

        succ = norm_next > norm_prev
        cond_list.append(bool(cond))
        succ_list.append(bool(succ))

    if len(cond_list) < 10:
        return None

    return {
        "cond": np.asarray(cond_list, dtype=bool),
        "succ": np.asarray(succ_list, dtype=bool),
    }


def do(khoa, df, rng):
    try:
        atr_s = bc.atr(df, 14)
        if atr_s is None:
            return None

        collected = None
        used_hs = None

        # Chon nguong zigzag theo SO MAU, khong theo ket qua.
        # Ha nguong chi de du so su kien >= 30.
        for hs in [3.0, 2.0, 1.5, 1.2, 1.0, 0.8]:
            col = _collect_events(df, hs, atr_s)
            if col is not None and int(col["cond"].sum()) >= 30:
                collected = col
                used_hs = hs
                break

        if collected is None:
            return None

        cond = collected["cond"]
        succ = collected["succ"]

        n = len(cond)
        n_upper = int(cond.sum())
        n_lower = n - n_upper

        if n_upper < 30:
            return None

        succ_upper = int(succ[cond].sum())
        rate_upper = succ_upper / n_upper
        rate_all = int(succ.sum()) / n
        rate_lower = (
            (int(succ.sum()) - succ_upper) / n_lower if n_lower > 0 else float("nan")
        )

        # Hoan vi: xao nhan dieu kien (nua tren / nua duoi) giua cac su kien.
        # Giu nguyen so su kien, so su kien co dieu kien, va outcome cua tung su kien.
        n_perm = 2000
        null_rates = np.empty(n_perm)

        for b in range(n_perm):
            perm_cond = cond[rng.permutation(n)]
            # Cung mau so: n_upper
            null_rates[b] = succ[perm_cond].sum() / n_upper

        null_tb = float(null_rates.mean())
        null_sd = float(null_rates.std(ddof=1)) if n_perm > 1 else 0.0

        if null_sd > 0:
            thong_ke = (rate_upper - null_tb) / null_sd
        else:
            thong_ke = 0.0

        p = (1 + int(np.sum(null_rates >= rate_upper))) / (n_perm + 1)

        return {
            "thong_ke": float(thong_ke),
            "p": float(p),
            "n": int(n_upper),
            "quan_sat_tho": float(rate_upper),
            "null_tb": null_tb,
            "null_sd": null_sd,
            "he_so": used_hs,
            "n_toan_bo": int(n),
            "n_upper": int(n_upper),
            "n_lower": int(n_lower),
            "ty_le_upper": float(rate_upper),
            "ty_le_lower": float(rate_lower) if n_lower > 0 else None,
            "ty_le_chung": float(rate_all),
            "so_success_upper": int(succ_upper),
            "ghi_chu": (
                f"Su kien la bo ba chan len-xuong-len hoan chinh; phiên tao day la bar "
                f"tai down.den. Dieu kien: close(day) > (high+low)/2. Do dai chan tang "
                f"sau va chan tang truoc duoc chia cho ATR14 tai diem bat dau cua tung "
                f"chan tang de loai bo volatility clustering (luat 4). "
                f"Nguong zigzag he_so={used_hs} duoc chon theo so mau (n_upper>=30), "
                f"khong chon theo ket qua. Hoan vi 2000 lan xao nhan dieu kien giua "
                f"cac su kien, giu nguyen n_upper va n, nen null_tb la ty le chung cua "
                f"mau, khong ep ve 50%. Day la do mo ta tren cac chan da hoan thanh; "
                f"outcome duoc do sau khi chan tang ke tiep hoan tat. Duong = ung ho "
                f"khang dinh."
            ),
            "de_xuat": (
                "Neu p co y nghia, thu ghep them dieu kien loc ATR thap hoac vi tri "
                "cua day trong bieu do de kiem tra xem co can loc manh hon."
            ),
        }

    except Exception:
        return None