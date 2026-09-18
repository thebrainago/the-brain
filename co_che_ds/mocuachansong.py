import numpy as np
import pandas as pd

try:
    import brain_co_che as bc
except Exception:
    bc = None


def _pos(x, data):
    try:
        v = int(x)
        if 0 <= v < len(data):
            return v
    except Exception:
        pass
    try:
        return data.index.get_loc(x)
    except Exception:
        return -1


def _is_up(h):
    if h is None:
        return False
    s = str(h).strip().lower()
    if s.startswith("u"):
        return True
    return s in ("len", "lên", "tang", "tăng", "uptrend", "1", "1.0", "+1")


def do(khoa, df, rng):
    if bc is None:
        return None

    data = df
    if len(data) < 100:
        return None

    try:
        atr_s = bc.atr(data, 14)

        def atr_at(t):
            if isinstance(atr_s, pd.Series):
                v = atr_s.iloc[t]
            else:
                v = atr_s[t]
            v = float(v)
            return v if np.isfinite(v) else np.nan

    except Exception:
        return None

    def lay_mau(he_so):
        try:
            ch = bc.chan_song(data, he_so=he_so)
            if ch is None or len(ch) == 0:
                return []
            doan = bc.cac_doan(data, ch)
            if doan is None or len(doan) == 0:
                return []
        except Exception:
            return []

        mau = []
        for _, leg in doan.iterrows():
            if not _is_up(leg.get("huong")):
                continue

            tu = _pos(leg.get("tu"), data)
            den = _pos(leg.get("den"), data)

            if tu <= 0 or den <= tu:
                continue

            try:
                open_tu = float(data.iloc[tu]["open"])
                prev_close = float(data.iloc[tu - 1]["close"])
                close_tu = float(data.iloc[tu]["close"])
            except Exception:
                continue

            gap = open_tu - prev_close
            if abs(gap) < 1e-12:
                continue

            atr_tu = atr_at(tu)
            if not np.isfinite(atr_tu) or atr_tu <= 0 or close_tu <= 0:
                continue

            try:
                duration = float(leg.get("thoi_luong", den - tu + 1))
            except Exception:
                duration = float(den - tu + 1)

            if not np.isfinite(duration) or duration <= 0:
                duration = float(den - tu + 1)

            # Luat 4: chuan hoa thoi luong theo bien dong tuong doi tai diem bat dau chan.
            norm_duration = duration / (atr_tu / close_tu)
            mau.append((norm_duration, gap < 0))

        return mau

    candidates = [3.0, 2.5, 2.0, 1.5, 1.0]
    mau = []
    chosen = None

    # Chon nguong theo so mau, khong chon theo ket qua.
    for he_so in candidates:
        mau = lay_mau(he_so)
        if len(mau) < 30:
            continue
        n_adv = sum(1 for _, adv in mau if adv)
        n_same = len(mau) - n_adv
        if n_adv >= 15 and n_same >= 15:
            chosen = he_so
            break

    if chosen is None or len(mau) == 0:
        return None

    dur = np.array([x[0] for x in mau], dtype=float)
    adv = np.array([x[1] for x in mau], dtype=bool)

    n1 = int(adv.sum())
    n0 = int((~adv).sum())
    N = int(len(dur))

    obs = float(dur[adv].mean() - dur[~adv].mean())

    # Hoan vi nhan nhom: giu nguyen so su kien moi nhom va ty le gap-nguoc/gap-cung.
    n_perm = 2000
    rand = rng.random((n_perm, N))
    order = np.argsort(rand, axis=1)
    sel = order < n1

    total = dur.sum()
    perm_sum_sel = (dur[None, :] * sel).sum(axis=1)
    perm_stats = perm_sum_sel / n1 - (total - perm_sum_sel) / n0

    null_tb = float(perm_stats.mean())
    null_sd = float(perm_stats.std(ddof=1))

    if not np.isfinite(null_sd) or null_sd <= 0:
        return None

    thong_ke = (obs - null_tb) / null_sd
    p = float((1 + np.count_nonzero(perm_stats >= obs)) / (1 + n_perm))

    return {
        "thong_ke": thong_ke,
        "p": p,
        "n": N,
        "quan_sat_tho": obs,
        "null_tb": null_tb,
        "null_sd": null_sd,
        "n_gap_nguoc": n1,
        "n_gap_cung": n0,
        "trung_binh_gap_nguoc": float(dur[adv].mean()),
        "trung_binh_gap_cung": float(dur[~adv].mean()),
        "nguong_he_so": float(chosen),
        "ghi_chu": (
            "Dinh nghia: chan tang = doan zigzag huong len; diem bat dau la vi tri chan (tu). "
            "Gap nguoc = open[tu] < close[tu-1]; gap cung = open[tu] > close[tu-1]; bo gap bang 0. "
            "Theo luat 4, thuoc do = thoi_luong / (ATR14/close) tai tu de loai bo volatility clustering. "
            f"Nguong chan he_so={chosen} duoc chon theo du mau (toi thieu 15 moi nhom), khong chon theo ket qua. "
            "Hoan vi gan lai nhan gap/cung giu nguyen so su kien va ti le 2 nhom; p mot phia. "
            "thong_ke duong = ung ho khang dinh."
        ),
        "de_xuat": (
            "Thu them dieu kien bien dong thap (ATR/close thap): luc do short bi mac ket co the "
            "tao hieu ung gap nguoc ro hon."
        ),
    }