import numpy as np
import pandas as pd
import brain_co_che as bc

def do(khoa, df, rng):
    """
    Kiểm định: trong 3 chân cùng chiều liên tiếp, xác suất chân giữa là ngắn nhất
    có tập trung ở một chế độ cụ thể (biến động cao/thấp, xu thế, chân đầu dài/ngắn).
    Thống kê = max |chênh lệch tỷ lệ min giữa hai nhóm| của 3 biến chế độ.
    p-value từ hoán vị giữ nguyên số lượng sự kiện (min) toàn cục.
    """
    try:
        # ---------- Lấy các đoạn (swing) ----------
        ch = bc.chan_song(df)
        if ch is None:
            return None

        doan = bc.cac_doan(df, ch)
        if doan is None or not isinstance(doan, pd.DataFrame) or len(doan) < 3:
            return None

        # Kiểm tra các cột cần thiết, có thể fallback từ 'den'
        if 'biet_tai' not in doan.columns:
            if 'den' in doan.columns:
                doan['biet_tai'] = doan['den']
            else:
                return None

        if 'do_dai' not in doan.columns or 'huong' not in doan.columns:
            return None

        # ---------- Chuyển biet_tai sang vị trí index ----------
        def to_pos(val):
            # Nếu là số (int hoặc float nguyên)
            if isinstance(val, (int, np.integer)) or (
                isinstance(val, float) and np.isfinite(val) and val.is_integer()
            ):
                pos = int(val)
                if 0 <= pos < len(df):
                    return pos
                return None
            # Nếu là nhãn (Timestamp, string, ...)
            try:
                return df.index.get_loc(pd.Timestamp(val))
            except (KeyError, TypeError):
                return None

        doan['pos'] = doan['biet_tai'].apply(to_pos)
        doan = doan[doan['pos'].notna()].reset_index(drop=True)
        if len(doan) < 3:
            return None

        # ---------- Chuẩn hóa hướng ----------
        if doan['huong'].dtype == bool:
            doan['huong_num'] = doan['huong'].astype(int) * 2 - 1  # True->1, False->-1
        elif doan['huong'].dtype == object:
            doan['huong_num'] = np.where(
                doan['huong'].astype(str).str.lower().str.startswith('up'), 1, -1
            )
        else:
            doan['huong_num'] = np.sign(doan['huong'])

        # Lọc các đoạn có biên độ dương
        doan = doan[doan['do_dai'] > 0].reset_index(drop=True)
        if len(doan) < 3:
            return None

        # ---------- Tự tính ATR và SMA200 (tránh lỗi alignment) ----------
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        prev_close = np.roll(close, 1)
        prev_close[0] = close[0]
        tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
        atr_arr = pd.Series(tr).rolling(14).mean().values
        sma_arr = pd.Series(close).rolling(200).mean().values

        # ---------- Xây dựng các bộ ba cùng hướng liên tiếp ----------
        records = []
        for huong in [1, -1]:
            sub = doan[doan['huong_num'] == huong].sort_values('pos').reset_index(drop=True)
            if len(sub) < 3:
                continue

            for i in range(len(sub) - 2):
                d1 = sub.loc[i, 'do_dai']
                d2 = sub.loc[i + 1, 'do_dai']
                d3 = sub.loc[i + 2, 'do_dai']

                # Bỏ tie (chân giữa không xác định rõ min)
                if d2 == d1 or d2 == d3:
                    continue

                min_flag = 1 if (d2 < d1 and d2 < d3) else 0

                # Thời điểm bộ ba hoàn thành = pos của đoạn thứ ba
                pos3 = int(sub.loc[i + 2, 'pos'])
                atr_t = atr_arr[pos3]
                if np.isnan(atr_t):
                    continue
                close_t = close[pos3]
                sma_t = sma_arr[pos3]
                if np.isnan(sma_t):
                    continue
                trend = 1 if close_t > sma_t else 0

                # Chân đầu dài/ngắn: d1 / ATR tại thời điểm chân đầu hoàn thành
                pos1 = int(sub.loc[i, 'pos'])
                atr_head = atr_arr[pos1]
                if np.isnan(atr_head) or atr_head <= 0:
                    continue
                long_head = 1 if (d1 / atr_head) >= 1.0 else 0

                records.append({
                    'min': min_flag,
                    'atr': atr_t,
                    'trend': trend,
                    'long_head': long_head,
                    'huong': huong
                })

        if len(records) < 30:
            return None

        data = pd.DataFrame(records)

        # ---------- Chia nhóm theo chế độ ----------
        atr_med = data['atr'].median()
        data['vol_group'] = (data['atr'] > atr_med).astype(int)
        data['trend_group'] = data['trend'].astype(int)
        data['long_head_group'] = data['long_head'].astype(int)

        def max_abs_diff():
            diffs = []
            for col in ['vol_group', 'trend_group', 'long_head_group']:
                p1 = data.loc[data[col] == 1, 'min'].mean()
                p0 = data.loc[data[col] == 0, 'min'].mean()
                diffs.append(abs(p1 - p0))
            return max(diffs)

        obs = max_abs_diff()

        # ---------- Hoán vị (giữ số lượng min toàn cục) ----------
        n_perm = 2000
        n_total = len(data)
        n_min = int(data['min'].sum())
        null_diffs = []

        for _ in range(n_perm):
            perm = rng.permutation(n_total)
            perm_min = (np.arange(n_total) < n_min).astype(int)[perm]
            data['min_perm'] = perm_min
            diffs = []
            for col in ['vol_group', 'trend_group', 'long_head_group']:
                p1 = data.loc[data[col] == 1, 'min_perm'].mean()
                p0 = data.loc[data[col] == 0, 'min_perm'].mean()
                diffs.append(abs(p1 - p0))
            null_diffs.append(max(diffs))

        null_diffs = np.array(null_diffs)
        null_mean = null_diffs.mean()
        null_std = null_diffs.std()
        if null_std == 0:
            return None

        p_value = (np.sum(null_diffs >= obs) + 1) / (n_perm + 1)
        thong_ke = (obs - null_mean) / null_std

        # ---------- Chi tiết cho báo cáo ----------
        diff_vol = abs(
            data.loc[data['vol_group'] == 1, 'min'].mean() -
            data.loc[data['vol_group'] == 0, 'min'].mean()
        )
        diff_trend = abs(
            data.loc[data['trend_group'] == 1, 'min'].mean() -
            data.loc[data['trend_group'] == 0, 'min'].mean()
        )
        diff_long_head = abs(
            data.loc[data['long_head_group'] == 1, 'min'].mean() -
            data.loc[data['long_head_group'] == 0, 'min'].mean()
        )

        return {
            'thong_ke': thong_ke,
            'p': p_value,
            'n': n_total,
            'quan_sat_tho': obs,
            'null_tb': null_mean,
            'null_sd': null_std,
            'diff_vol': diff_vol,
            'diff_trend': diff_trend,
            'diff_long_head': diff_long_head,
            'ty_le_min': data['min'].mean(),
            'ghi_chu': (
                "Dùng bc.cac_doan, bộ ba cùng hướng liên tiếp. Bỏ tie. "
                "Chế độ: vol (ATR > median toàn chuỗi), trend (giá > SMA200), "
                "long_head (d1/ATR_head >=1). Thống kê = max |diff| giữa tỷ lệ min "
                "của hai nhóm. Hoán vị giữ số lượng min toàn cục."
            )
        }
    except Exception:
        return None