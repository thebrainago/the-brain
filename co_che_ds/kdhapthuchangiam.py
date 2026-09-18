import numpy as np
import pandas as pd

try:
    import brain_co_che as bc
except Exception:
    bc = None


def _build_events(ch, atr, vol_norm):
    if ch is None or len(ch) < 4:
        return []
    if 'xac_nhan' not in ch.columns:
        return []

    ch = ch.copy()
    ch['vi_tri'] = pd.to_numeric(ch['vi_tri'], errors='coerce')
    ch['xac_nhan'] = pd.to_numeric(ch['xac_nhan'], errors='coerce')
    ch['gia'] = pd.to_numeric(ch['gia'], errors='coerce')
    ch = ch.dropna(subset=['vi_tri', 'gia', 'xac_nhan'])
    ch = ch[ch['vi_tri'] >= 0]
    ch = ch.sort_values('vi_tri').reset_index(drop=True)

    if len(ch) < 4:
        return []

    legs = []
    for i in range(len(ch) - 1):
        s = ch.iloc[i]
        e = ch.iloc[i + 1]

        st = int(s['vi_tri'])
        en = int(e['vi_tri'])
        if en <= st:
            continue

        xac_nhan = int(e['xac_nhan'])
        if xac_nhan < en:
            continue

        sg = float(s['gia'])
        eg = float(e['gia'])
        if not (np.isfinite(sg) and np.isfinite(eg)) or eg == sg:
            continue

        atr_m = float(atr.iloc[st:en + 1].mean())
        if not np.isfinite(atr_m) or atr_m <= 0:
            continue

        v_m = float(vol_norm.iloc[st:en + 1].mean())
        if not np.isfinite(v_m):
            continue

        legs.append({
            'start': st,
            'end': en,
            'dir': 1 if eg > sg else -1,
            'range_adj': abs(eg - sg) / atr_m,
            'avg_vol': v_m,
            'biet_tai_end': xac_nhan,
        })

    events = []
    for k in range(len(legs) - 3):
        d1, u1, d2, u2 = legs[k], legs[k + 1], legs[k + 2], legs[k + 3]

        # Dãy cần: giảm -> tăng -> giảm -> tăng
        if d1['dir'] != -1 or u1['dir'] != 1 or d2['dir'] != -1 or u2['dir'] != 1:
            continue

        # D2 phải được xác nhận sau U1
        if u1['biet_tai_end'] > d2['biet_tai_end']:
            continue

        dieu_kien = (d2['avg_vol'] > d1['avg_vol']) and (d2['range_adj'] < d1['range_adj'])
        ket_qua = u2['range_adj'] > u1['range_adj']

        events.append((d2['biet_tai_end'], dieu_kien, ket_qua))

    return events


def do(khoa, df, rng):
    if bc is None or df is None or len(df) < 200:
        return None

    # ATR để chuẩn hoá biên độ (luật 4)
    try:
        atr = bc.atr(df, 14)
        if isinstance(atr, pd.DataFrame):
            atr = atr.iloc[:, 0]
        elif not isinstance(atr, pd.Series):
            atr = pd.Series(np.asarray(atr).ravel(), index=df.index)
        atr = atr.astype(float)
    except Exception:
        atr = (df['high'] - df['low']).rolling(14, min_periods=1).mean()

    # Khối lượng chuẩn hoá: volume / trung bình 20 nến trước đó (tránh drift)
    vol = pd.to_numeric(df['volume'], errors='coerce').fillna(0.0)
    vol_ma = vol.rolling(21, min_periods=1).mean().shift(1)
    vol_norm = vol / vol_ma.replace(0, np.nan)
    vol_norm = vol_norm.fillna(1.0).astype(float)

    events = []
    selected_he_so = None

    # Hạ ngưỡng zigzag dần chỉ để đủ số mẫu, không chọn theo kết quả.
    for he_so in (1.5, 1.2, 1.0):
        try:
            ch = bc.chan_song(df, he_so=he_so)
        except TypeError:
            try:
                ch = bc.chan_song(df)
            except Exception:
                return None
            selected_he_so = 3.0
            events = _build_events(ch, atr, vol_norm)
            break
        except Exception:
            continue

        if ch is None or len(ch) < 4:
            continue

        selected_he_so = he_so
        events = _build_events(ch, atr, vol_norm)
        cnt_cond = sum(1 for _, c, _ in events if c)
        if len(events) >= 30 and cnt_cond >= 30:
            break

    if selected_he_so is None:
        try:
            ch = bc.chan_song(df)
            selected_he_so = 3.0
            events = _build_events(ch, atr, vol_norm)
        except Exception:
            return None

    if len(events) < 30:
        return None

    C = np.array([e[1] for e in events], dtype=bool)
    O = np.array([e[2] for e in events], dtype=bool)

    n_cond = int(C.sum())
    if n_cond < 30:
        return None

    n = len(C)
    o_mean = float(O.mean())
    stat_obs = float(O[C].mean() - o_mean)

    n_perm = 2000
    null_stats = np.empty(n_perm)
    for i in range(n_perm):
        # Hoán vị nhãn điều kiện, giữ nguyên số sự kiện C=1.
        # Không hoán vị outcome -> bảo toàn tỷ lệ nền.
        c_shuf = rng.permutation(C)
        null_stats[i] = O[c_shuf].mean() - o_mean

    null_tb = float(null_stats.mean())
    null_sd = float(null_stats.std(ddof=1))

    if not np.isfinite(null_sd) or null_sd == 0:
        return None

    thong_ke = (stat_obs - null_tb) / null_sd
    p = (1 + int(np.sum(null_stats >= stat_obs))) / (n_perm + 1)  # một phía, dương là ủng hộ

    return {
        'thong_ke': thong_ke,
        'p': float(p),
        'n': n_cond,
        'n_tong': n,
        'n_dieu_kien': n_cond,
        'quan_sat_tho': stat_obs,
        'null_tb': null_tb,
        'null_sd': null_sd,
        'ty_le_dieu_kien': float(O[C].mean()),
        'ty_le_nen': o_mean,
        'nguong_chan': selected_he_so,
        'ghi_chu': (
            'Chân zigzag bằng bc.chan_song; ngưỡng hạ dần 1.5 -> 1.0 xATR chỉ theo số mẫu. '
            'Biên độ mỗi chân chia ATR(14); khối lượng mỗi nến chuẩn hoá bằng volume / MA20 trước đó. '
            'Sự kiện: D2 giảm có vol/nến > D1 giảm trước và range_adj(D2) < range_adj(D1); result: '
            'range_adj(U2) > range_adj(U1). p một phía từ 2000 hoán vị nhãn điều kiện, giữ nguyên số C=1 '
            'và outcome gốc. Dương = ủng hộ khẳng định.'
        ),
    }