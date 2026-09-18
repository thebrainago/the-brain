import numpy as np
import pandas as pd

try:
    import brain_co_che as bc
except Exception:
    bc = None


def _atr(df: pd.DataFrame, n: int = 14) -> np.ndarray:
    """Layer ATR: ưu tiên dùng brain_co_che, nếu không thì tự tính Wilder."""
    if bc is not None and hasattr(bc, 'atr'):
        try:
            return np.asarray(bc.atr(df, n)).ravel()
        except Exception:
            pass

    h = df['high'].to_numpy(dtype=float)
    l = df['low'].to_numpy(dtype=float)
    c = df['close'].to_numpy(dtype=float)

    tr = np.maximum(h[1:] - l[1:],
                    np.maximum(np.abs(h[1:] - c[:-1]),
                               np.abs(l[1:] - c[:-1])))
    tr = np.concatenate([[np.nan], tr])

    atr = np.full(len(df), np.nan)
    if len(df) >= n + 1:
        atr[n] = np.nanmean(tr[1:n + 1])
        for i in range(n + 1, len(df)):
            atr[i] = (atr[i - 1] * (n - 1) + tr[i]) / n

    return pd.Series(atr).bfill().ffill().to_numpy()


def _leg_features(tu: int, den: int,
                  high: np.ndarray, low: np.ndarray,
                  vol: np.ndarray, atr: np.ndarray,
                  vol_ma: np.ndarray, min_len: int = 3):
    """Đặc trưng nội tại của một chân: biên độ/ATR có giảm, volume/vol_MA có tăng.

    Luật 4: biên độ được chia cho ATR tại chính bar đó; volume chia cho MA volume.
    """
    if den - tu < min_len:
        return None

    a = tu + 1          # bỏ bar swing gốc, tránh lẫn với chân trước
    b = den             # giữ bar swing cuối
    if b - a + 1 < min_len:
        return None

    rng = high[a:b + 1] - low[a:b + 1]
    vr = vol[a:b + 1]
    atr_seg = atr[a:b + 1]
    ma_seg = vol_ma[a:b + 1]

    if not np.all(np.isfinite(rng)) or not np.all(np.isfinite(vr)):
        return None
    if not np.all(np.isfinite(atr_seg)) or np.any(atr_seg <= 0):
        return None
    if not np.all(np.isfinite(ma_seg)) or np.any(ma_seg <= 0):
        return None

    rel_amp = rng / np.maximum(atr_seg, 1e-12)
    rel_vol = vr / np.maximum(ma_seg, 1e-12)

    t = np.arange(len(rel_amp), dtype=float)
    t = t - t.mean()

    slope_amp = np.polyfit(t, rel_amp, 1)[0]
    slope_vol = np.polyfit(t, rel_vol, 1)[0]

    # Chuẩn hóa theo mean để slope có ý nghĩa "thay đổi tương đối mỗi bar"
    mean_amp = rel_amp.mean()
    mean_vol = rel_vol.mean()
    if mean_amp > 1e-12:
        slope_amp = slope_amp / mean_amp
    if mean_vol > 1e-12:
        slope_vol = slope_vol / mean_vol

    return float(slope_amp), float(slope_vol)


def do(khoa: str, df: pd.DataFrame, rng: np.random.Generator):
    if bc is None or df is None or len(df) < 120:
        return None

    # Hạ ngưỡng từ mặc định 3xATR xuống 2xATR để đủ cỡ mẫu.
    # "Chân" lúc này nhỏ hơn, nhiều hơn nhưng vẫn là chân zigzag có xác nhận.
    try:
        ch = bc.chan_song(df, he_so=2.0)
        if ch is None or len(ch) < 12:
            return None
        doan = bc.cac_doan(df, ch)
    except Exception:
        return None

    if doan is None or len(doan) < 4:
        return None

    try:
        rows = doan.to_dict('records')
    except Exception:
        rows = list(doan)

    n = len(df)
    if n == 0:
        return None

    close = df['close'].to_numpy(dtype=float)
    high = df['high'].to_numpy(dtype=float)
    low = df['low'].to_numpy(dtype=float)
    vol = df['volume'].to_numpy(dtype=float)

    atr = np.asarray(_atr(df, 14)).ravel()
    vol_ma = pd.Series(vol).rolling(50, min_periods=10).mean().to_numpy()
    vol_ma = np.where(np.isfinite(vol_ma), vol_ma, np.nan)

    # --- Gom các đoạn zigzag ---
    raw = []
    for r in rows:
        try:
            tu = int(r['tu'])
            den = int(r['den'])
        except Exception:
            continue

        if not (0 <= tu < den < n):
            continue

        raw.append({
            'tu': tu,
            'den': den,
            'dur': int(den - tu),
            'dir': 1 if close[den] >= close[tu] else -1,
            'has_trend': False,
            'corrective': False,
        })

    if len(raw) < 4:
        return None

    raw = sorted(raw, key=lambda x: x['tu'])

    # --- Phân loại chân điều chỉnh theo xu hướng 200 phiên trước đó ---
    lookback = 200
    for s in raw:
        tu = s['tu']
        if tu < 30:
            continue

        start = max(0, tu - lookback)
        if start >= tu:
            continue

        if close[tu] == close[start]:
            continue

        trend_dir = 1 if close[tu] > close[start] else -1
        s['has_trend'] = True
        s['corrective'] = (s['dir'] == -trend_dir)

    # --- Tính đặc trưng cho các chân điều chỉnh ---
    for s in raw:
        if not s['corrective']:
            continue

        feat = _leg_features(s['tu'], s['den'], high, low, vol, atr, vol_ma)
        if feat is None:
            continue

        s['slope_amp'] = feat[0]
        s['slope_vol'] = feat[1]

    # --- Cặp: chân điều chỉnh hiện tại, chân điều chỉnh liền sau.
    # Muốn gọi là "liền sau" thì giữa chúng phải có đúng một chân khác (chân xu thế).
    pairs = []
    for i in range(len(raw) - 2):
        cur = raw[i]
        mid = raw[i + 1]
        nxt = raw[i + 2]

        if not (cur['has_trend'] and cur['corrective']):
            continue
        if not (nxt['has_trend'] and nxt['corrective']):
            continue
        if not (mid['has_trend'] and not mid['corrective']):
            continue
        if 'slope_amp' not in cur:
            continue

        event = bool(cur['slope_amp'] < 0 and cur['slope_vol'] > 0)
        pairs.append({
            'diff': float(cur['dur'] - nxt['dur']),
            'event': event,
        })

    if len(pairs) < 30:
        return None

    diffs = np.array([p['diff'] for p in pairs], dtype=float)
    ev = np.array([p['event'] for p in pairs], dtype=bool)
    n_ev = int(ev.sum())

    if n_ev < 30:
        return None

    obs = float(diffs[ev].mean())

    # --- Hoán vị nhãn "sự kiện" trên chính bộ cặp.
    # Giữ nguyên số sự kiện, giữ nguyên cấu trúc thời gian; không xáo chính chuỗi lợi nhuận.
    n_perm = 2000
    null_stats = np.empty(n_perm)
    N = len(diffs)
    m = n_ev

    for b in range(n_perm):
        idx = rng.choice(N, size=m, replace=False)
        null_stats[b] = diffs[idx].mean()

    null_tb = float(null_stats.mean())
    null_sd = float(null_stats.std(ddof=1)) if len(null_stats) > 1 else 0.0

    if not np.isfinite(null_sd) or null_sd <= 1e-15:
        return None

    thong_ke = (obs - null_tb) / null_sd
    p = float((1 + np.sum(null_stats >= obs)) / (n_perm + 1))

    return {
        'thong_ke': thong_ke,
        'p': p,
        'n': n_ev,
        'quan_sat_tho': obs,
        'null_tb': null_tb,
        'null_sd': null_sd,
        'n_eligible': N,
        'ghi_chu': (
            "Dùng chan_song(he_so=2.0) -> chân nhỏ hơn mặc định 3xATR. "
            "Chân điều chỉnh = ngược xu hướng 200 phiên; cặp so sánh là chân điều chỉnh hiện tại "
            "và chân điều chỉnh sau đúng một chân xu thế. "
            "Biên độ từng bar chia ATR(14), khối lượng chia MA50 khối lượng; sự kiện = slope biên độ < 0 "
            "và slope khối lượng > 0. "
            "thống kê = trung bình (số phiên chân hiện tại - số phiên chân kế) của các sự kiện; "
            "hoán vị nhãn sự kiện trên các cặp, cùng mẫu số, p một phía. "
            "Zigzag có xác nhận nên mốc chân có thể repaint khi có bar mới."
        ),
    }