import numpy as np
import pandas as pd
import brain_co_che as bc


def _map_huong(x):
    """Chuẩn hoá hướng về 'up' hoặc 'down'."""
    if x is None:
        return None
    if isinstance(x, (int, float, np.integer, np.floating)):
        if x > 0:
            return 'up'
        if x < 0:
            return 'down'
        return None
    if isinstance(x, str):
        s = x.strip().lower()
        if not s:
            return None
        if s in ('up', 'tang', 'len', 'u', 'bull', 'long', 'mua', 'tăng', 'l'):
            return 'up'
        if s in ('down', 'giam', 'xuong', 'd', 'bear', 'short', 'ban', 'giảm', 's'):
            return 'down'
        if s in ('1', '+1'):
            return 'up'
        if s in ('-1',):
            return 'down'
        if s.startswith(('up', 'tang', 'len', 'bull', 'long', 'mua', 'u', 'l')):
            return 'up'
        if s.startswith(('down', 'giam', 'xuong', 'bear', 'short', 'ban', 'd', 's')):
            return 'down'
    return None


def _get_col(row, col):
    """Lấy giá trị cột nếu tồn tại, tránh lỗi khi row là dict hoặc Series."""
    try:
        val = row[col]
        if val is None:
            return None
        if isinstance(val, float) and np.isnan(val):
            return None
        return val
    except (KeyError, TypeError, IndexError):
        return None


def _pos(df, val):
    """Chuyển một mốc thời gian thành vị trí số nguyên trong df."""
    if val is None:
        return None
    if isinstance(val, (int, np.integer)):
        return int(val)
    try:
        return df.index.get_loc(val)
    except (KeyError, TypeError):
        return None


def _start_pos(row, df):
    """Vị trí bắt đầu của đoạn, ưu tiên cột 'tu', fallback 'vi_tri'."""
    for col in ('tu', 'vi_tri'):
        val = _get_col(row, col)
        if val is not None:
            p = _pos(df, val)
            if p is not None:
                return p
    return None


def _get_direction(row, df):
    """Xác định hướng đoạn từ cột huong/loai, fallback bằng giá đóng cửa."""
    h = _get_col(row, 'huong')
    if h is None:
        h = _get_col(row, 'loai')
    d = _map_huong(h)
    if d is not None:
        return d

    tu = _start_pos(row, df)
    den_pos = None
    for col in ('den',):
        val = _get_col(row, col)
        if val is not None:
            den_pos = _pos(df, val)
            break
    if tu is not None and den_pos is not None:
        if 0 <= tu < len(df) and 0 <= den_pos < len(df):
            try:
                if df['close'].iloc[den_pos] > df['close'].iloc[tu]:
                    return 'up'
                return 'down'
            except (IndexError, KeyError):
                return None
    return None


def _get_duration(row, df):
    """Lấy thời lượng đoạn: ưu tiên thoi_luong, rồi do_dai, cuối cùng là khoảng cách bar."""
    # thoi_luong
    val = _get_col(row, 'thoi_luong')
    if val is not None:
        if isinstance(val, pd.Timedelta):
            return val.total_seconds() / 86400.0
        try:
            f = float(val)
            if not np.isnan(f):
                return f
        except (TypeError, ValueError):
            pass

    # do_dai
    val = _get_col(row, 'do_dai')
    if val is not None:
        try:
            f = float(val)
            if not np.isnan(f):
                return f
        except (TypeError, ValueError):
            pass

    # fallback: den - tu
    tu = _start_pos(row, df)
    den = None
    for col in ('den',):
        v = _get_col(row, col)
        if v is not None:
            den = _pos(df, v)
            break
    if tu is not None and den is not None:
        return float(abs(den - tu))
    return np.nan


def _get_atr_series(atr, df):
    """Chuẩn hoá atr thành Series hoặc ndarray 1 chiều."""
    if atr is None:
        return None
    if isinstance(atr, pd.DataFrame):
        if len(atr.columns) > 0:
            return atr.iloc[:, 0]
        return None
    if isinstance(atr, pd.Series):
        return atr
    if isinstance(atr, np.ndarray):
        if atr.ndim == 2 and atr.shape[1] == 1:
            return atr[:, 0]
        return atr
    return None


def _atr_at(atr, pos):
    """Lấy ATR tại vị trí pos."""
    if atr is None:
        return np.nan
    try:
        if isinstance(atr, np.ndarray):
            if 0 <= pos < len(atr):
                return float(atr[pos])
            return np.nan
        # pandas Series
        return float(atr.iloc[pos])
    except (IndexError, KeyError, TypeError):
        return np.nan


def do(khoa, df, rng):
    """
    Kiểm định: Khi chân giảm có thời lượng (chuẩn hoá theo ATR) dài hơn chân tăng trước,
    thì chân tăng tiếp theo có thời lượng ngắn hơn chân tăng trước với xác suất cao hơn ngẫu nhiên.
    """
    try:
        # 1. ATR(14)
        atr_raw = bc.atr(df, 14)
        atr = _get_atr_series(atr_raw, df)
        if atr is None or len(atr) == 0:
            return None

        # 2. Chân và đoạn
        ch = bc.chan_song(df)
        if ch is None or len(ch) < 4:
            return None
        doan = bc.cac_doan(df, ch)
        if doan is None or len(doan) < 3:
            return None

        # 3. Sắp xếp theo thời gian
        if 'tu' in doan.columns:
            doan = doan.sort_values('tu').reset_index(drop=True)
        elif 'vi_tri' in doan.columns:
            doan = doan.sort_values('vi_tri').reset_index(drop=True)
        else:
            return None

        # 4. Gom các bộ ba U1 -> D -> U2
        triples = []
        for i in range(len(doan) - 2):
            u1 = doan.iloc[i]
            d = doan.iloc[i + 1]
            u2 = doan.iloc[i + 2]

            if _get_direction(u1, df) != 'up':
                continue
            if _get_direction(d, df) != 'down':
                continue
            if _get_direction(u2, df) != 'up':
                continue

            dur_u1 = _get_duration(u1, df)
            dur_d = _get_duration(d, df)
            dur_u2 = _get_duration(u2, df)
            if any(np.isnan(x) for x in (dur_u1, dur_d, dur_u2)):
                continue

            p_u1 = _start_pos(u1, df)
            p_d = _start_pos(d, df)
            p_u2 = _start_pos(u2, df)
            if p_u1 is None or p_d is None or p_u2 is None:
                continue

            atr_u1 = _atr_at(atr, p_u1)
            atr_d = _atr_at(atr, p_d)
            atr_u2 = _atr_at(atr, p_u2)
            if any(np.isnan(x) or x == 0 for x in (atr_u1, atr_d, atr_u2)):
                continue

            # Luật 4: chuẩn hoá theo biến động nhiễu ATR
            dur_u1_n = dur_u1 / atr_u1
            dur_d_n = dur_d / atr_d
            dur_u2_n = dur_u2 / atr_u2

            triples.append((dur_u1_n, dur_d_n, dur_u2_n))

        if len(triples) < 30:
            return None

        # 5. Tính tỷ lệ có điều kiện
        dur_u1 = np.array([t[0] for t in triples])
        dur_d = np.array([t[1] for t in triples])
        dur_u2 = np.array([t[2] for t in triples])

        cond = dur_d > dur_u1
        event = dur_u2 < dur_u1

        n1 = int(cond.sum())
        n0 = int((~cond).sum())
        if n1 < 30 or n0 == 0:
            return None

        p1 = event[cond].mean()
        p0 = event[~cond].mean()
        diff_obs = p1 - p0

        # 6. Hoán vị: giữ nguyên mảng điều kiện, chỉ trộn nhãn sự kiện
        n_perm = 2000
        diffs = np.empty(n_perm)
        for b in range(n_perm):
            event_perm = rng.permutation(event)
            diffs[b] = event_perm[cond].mean() - event_perm[~cond].mean()

        mean_null = diffs.mean()
        sd_null = diffs.std(ddof=1)
        if sd_null == 0:
            return None

        # 7. Neo thống kê vào null (luật 3)
        thong_ke = (diff_obs - mean_null) / sd_null
        p = (np.sum(diffs >= diff_obs) + 1) / (n_perm + 1)

        return {
            'thong_ke': float(thong_ke),
            'p': float(p),
            'n': n1,
            'quan_sat_tho': float(diff_obs),
            'null_tb': float(mean_null),
            'null_sd': float(sd_null),
            'p1': float(p1),
            'p0': float(p0),
            'n1': n1,
            'n0': n0,
            'ghi_chu': 'Thoi luong doan duoc lay tu thoi_luong/do_dai hoac khoang cach bar. '
                       'Chuan hoa ATR(14) tai diem bat dau doan. Dieu kien: D dai hon U1. '
                       'Su kien: U2 ngan hon U1. Hoan vi giu nguyen day dieu kien, tron nhan su kien.',
            'de_xuat': 'Có thể ghép với điều kiện biến động thấp (ATR thấp) để tăng tín hiệu.'
        }
    except Exception:
        return None