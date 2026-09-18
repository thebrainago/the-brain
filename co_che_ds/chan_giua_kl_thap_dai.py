import numpy as np
import pandas as pd
import brain_co_che as bc


def _has(r, key):
    try:
        return key in r.index
    except AttributeError:
        return key in r


def _pos(df, value):
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)) and np.isfinite(value) and float(value).is_integer():
        return int(value)
    if isinstance(value, pd.Timestamp):
        loc = df.index.get_loc(value)
    else:
        try:
            loc = df.index.get_loc(pd.Timestamp(value))
        except Exception:
            return int(value)
    if isinstance(loc, slice):
        return int(loc.start)
    if isinstance(loc, np.ndarray):
        return int(loc[0])
    return int(loc)


def _huong(x):
    if isinstance(x, str):
        s = x.strip().lower()
        if s in ("up", "1", "buy", "long", "tang", "duong"):
            return 1
        if s in ("down", "-1", "sell", "short", "giam", "am"):
            return -1
        return int(x)
    return int(x)


def _base_volume(df, pos, win=20):
    if pos <= 0:
        return None
    start = max(0, pos - win)
    seg = df["volume"].iloc[start:pos]
    if len(seg) == 0:
        return None
    med = float(seg.median())
    if not np.isfinite(med) or med <= 0:
        pre = df["volume"].iloc[:pos]
        if len(pre) == 0:
            return None
        med = float(pre.median())
    if not np.isfinite(med) or med <= 0:
        return None
    return med


def _leg_info(df, r, atr_s):
    try:
        tu = _pos(df, r["tu"])
        den = _pos(df, r["den"])
        if den < tu:
            return None

        h = _huong(r["huong"])
        if h not in (1, -1):
            return None

        if _has(r, "thoi_luong"):
            try:
                dur = int(r["thoi_luong"])
            except Exception:
                dur = None
        else:
            dur = None
        if dur is None or dur < 1:
            dur = max(den - tu, 1)

        leg = df.iloc[tu:den + 1]
        if len(leg) == 0:
            return None

        avg_v = float(leg["volume"].astype(float).mean())
        if not np.isfinite(avg_v) or avg_v <= 0:
            return None

        # Bien do gia cua chan
        if _has(r, "do_dai"):
            try:
                dd = float(r["do_dai"])
                if not np.isfinite(dd) or dd <= 0:
                    dd = float(leg["high"].max() - leg["low"].min())
                do_dai = abs(dd)
            except Exception:
                do_dai = float(leg["high"].max() - leg["low"].min())
        else:
            do_dai = float(leg["high"].max() - leg["low"].min())

        if not np.isfinite(do_dai) or do_dai <= 0:
            return None

        # ATR tai thoi diem bat dau chan
        atr_val = np.nan
        if atr_s is not None:
            try:
                val = atr_s.iloc[tu] if hasattr(atr_s, "iloc") else atr_s[tu]
                if isinstance(val, pd.Series):
                    val = val.iloc[0]
                atr_val = float(val)
            except Exception:
                atr_val = np.nan

        # Thoi luong chuan hoa theo bien do tu nhien:
        # do thi gian tren mot don vi bien dong (ATR).
        if np.isfinite(atr_val) and atr_val > 0:
            norm_dur = dur * atr_val / do_dai
        else:
            norm_dur = dur / do_dai

        base_v = _base_volume(df, tu)
        if base_v is None or base_v <= 0:
            return None

        rel_v = avg_v / base_v

        return {
            "tu": tu,
            "den": den,
            "dir": h,
            "dur": dur,
            "norm_dur": norm_dur,
            "rel_v": rel_v,
        }
    except Exception:
        return None


def _make_triples(legs):
    triples = []
    for d in (1, -1):
        arr = [x for x in legs if x["dir"] == d]
        arr.sort(key=lambda x: (x["tu"], x["den"]))

        i = 0
        while i + 2 < len(arr):
            a, b, c = arr[i], arr[i + 1], arr[i + 2]

            # Bao dam khong overlap giua cac chan cung huong
            if b["tu"] > a["den"] and c["tu"] > b["den"]:
                A = (b["rel_v"] < a["rel_v"]) and (b["rel_v"] < c["rel_v"])
                B = (b["norm_dur"] > a["norm_dur"]) and (b["norm_dur"] > c["norm_dur"])
                triples.append((A, B, d))

            i += 3

    return triples


def do(khoa, df, rng):
    try:
        atr_s = bc.atr(df, 14)
    except Exception:
        atr_s = None

    best_triples = None
    best_he_so = None

    # Chon nguong theo so mau truoc khi test, khong theo ket qua.
    for he_so in [3.0, 2.5, 2.0, 1.5, 1.2, 1.0]:
        try:
            ch = bc.chan_song(df, he_so=he_so)
            if ch is None or len(ch) < 4:
                continue

            segs = bc.cac_doan(df, ch)
            if segs is None or len(segs) < 4:
                continue

            legs = []
            for _, r in segs.iterrows():
                info = _leg_info(df, r, atr_s)
                if info is not None:
                    legs.append(info)

            triples = _make_triples(legs)
            if len(triples) < 30:
                continue

            A = np.array([t[0] for t in triples], dtype=bool)
            n_A = int(A.sum())

            if n_A >= 30:
                best_triples = triples
                best_he_so = he_so
                break
        except Exception:
            continue

    if best_triples is None:
        return None

    A = np.array([t[0] for t in best_triples], dtype=bool)
    B = np.array([t[1] for t in best_triples], dtype=bool)
    group = np.array([0 if t[2] == 1 else 1 for t in best_triples], dtype=int)

    n_A = int(A.sum())
    n_B = int(B.sum())
    n_triples = len(best_triples)

    obs = float(B[A].mean())

    n_perm = 2000
    nulls = np.empty(n_perm, dtype=float)

    for k in range(n_perm):
        A_perm = A.copy()
        for g in np.unique(group):
            idx = np.where(group == g)[0]
            if len(idx) > 1:
                A_perm[idx] = A[idx][rng.permutation(len(idx))]
        nulls[k] = float(B[A_perm].mean())

    null_tb = float(nulls.mean())
    null_sd = float(nulls.std(ddof=1))

    if null_sd > 0:
        thong_ke = (obs - null_tb) / null_sd
    else:
        thong_ke = 0.0

    # Mot phia: khang dinh noi "cao hon muc ngau nhien"
    p = float((np.sum(nulls >= obs) + 1) / (n_perm + 1))

    return {
        "thong_ke": thong_ke,
        "p": p,
        "n": n_A,
        "quan_sat_tho": obs,
        "null_tb": null_tb,
        "null_sd": null_sd,
        "n_triples": n_triples,
        "n_A": n_A,
        "n_B": n_B,
        "he_so": best_he_so,
        "ghi_chu": (
            "Dinh nghia ba chan cung chieu: ba song cung huong lien tiep trong "
            "danh sach song zigzag, lay khong trung lap theo bo ba. "
            "Khoi luong trung binh phien duoc chuan hoa theo median volume 20 phien "
            "truoc chan de tranh volume drift; thoi luong duoc chuan hoa theo "
            "bien do gia / ATR de tranh volatility clustering (luat 4). "
            "Hoan vi nhan A trong tung huong, giu nguyen so su kien va ty le up/down. "
            "p la p-value mot phia (phai). Bo ba chan co the ve lai khi co bar moi."
        ),
        "de_xuat": (
            "Neu ket qua duong, thu tiep dieu kien: chi giu cac bo ba co ca ba chan "
            "cung nam tren cung mot phia cua ATR (song day) de tach hieu ung khoi song dieu chinh."
        ),
    }