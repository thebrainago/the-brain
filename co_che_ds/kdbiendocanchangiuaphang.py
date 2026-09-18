import numpy as np
import pandas as pd

try:
    import brain_co_che as bc
    _chan_song = bc.chan_song
    _atr = bc.atr
except Exception:
    try:
        from brain_co_che import chan_song as _chan_song, atr as _atr
    except Exception:
        _chan_song = None
        _atr = None


def _loc_idx(idx, x):
    """Chuyển một giá trị (int position hoặc label) thành integer position."""
    if isinstance(x, (int, np.integer)):
        return int(x)
    try:
        return idx.get_loc(x)
    except Exception:
        return int(x)


def _goi_chan_song(df, he_so):
    """Gọi bc.chan_song, xử lý trường hợp không hỗ trợ tham số he_so."""
    if _chan_song is None:
        return None
    try:
        return _chan_song(df, he_so=he_so)
    except TypeError:
        try:
            return _chan_song(df)
        except Exception:
            return None
    except Exception:
        return None


def _tinh_doan(df, ch):
    """Tính các đoạn nối giữa các chân sóng: biên độ chuẩn hóa ATR, slope chuẩn hóa."""
    if ch is None or len(ch) < 3:
        return None
    ch = ch.sort_values('vi_tri').reset_index(drop=True)

    atr_series = _atr(df, 14)
    if atr_series is None:
        return None
    atr_arr = atr_series.to_numpy(dtype=float)
    idx = df.index

    pos_raw = ch['vi_tri'].to_numpy()
    gia = ch['gia'].to_numpy(dtype=float)
    xac_raw = ch['xac_nhan'].to_numpy()
    n = len(pos_raw)

    rows = []
    for i in range(n - 1):
        tu = _loc_idx(idx, pos_raw[i])
        den = _loc_idx(idx, pos_raw[i + 1])
        if den <= tu:
            continue
        xac = _loc_idx(idx, xac_raw[i + 1])
        if xac < 0 or xac >= len(atr_arr):
            xac = min(max(xac, 0), len(atr_arr) - 1)

        atr_val = atr_arr[xac]
        if not np.isfinite(atr_val) or atr_val <= 0:
            continue

        do_dai = abs(float(gia[i + 1]) - float(gia[i]))
        if do_dai <= 0:
            continue

        thoi_luong = max(den - tu, 1)
        huong = 1 if gia[i + 1] > gia[i] else -1
        amp_norm = do_dai / atr_val
        slope_norm = amp_norm / thoi_luong

        rows.append({
            'tu': tu,
            'den': den,
            'xac': xac,
            'do_dai': do_dai,
            'thoi_luong': thoi_luong,
            'huong': huong,
            'amp_norm': amp_norm,
            'slope_norm': slope_norm,
        })

    if len(rows) < 4:
        return None
    return pd.DataFrame(rows)


def _lay_records(doan, nguong_can_bang):
    """Xây dựng danh sách (can_bang, slope_B) từ các bộ ba 3 chân liên tiếp."""
    records = []
    n = len(doan)
    for i in range(n - 2):
        A = doan.iloc[i]
        B = doan.iloc[i + 1]
        C = doan.iloc[i + 2]

        if not (A['huong'] == C['huong'] and B['huong'] == -A['huong']):
            continue

        a = float(A['amp_norm'])
        b = float(B['amp_norm'])
        c = float(C['amp_norm'])
        if not (np.isfinite(a) and np.isfinite(b) and np.isfinite(c)):
            continue
        if a <= 0 or c <= 0 or b <= 0:
            continue

        # Hai chân cùng chiều "cân bằng": tỷ lệ lệch không quá ~ e^nguong
        log_ratio = abs(np.log(c / a))
        can_bang = log_ratio <= nguong_can_bang

        slope_b = float(B['slope_norm'])
        if not np.isfinite(slope_b):
            continue

        records.append((can_bang, slope_b))

    return records


def do(khoa, df, rng):
    if _chan_song is None or _atr is None:
        return None

    # Thử nhiều mức he_so khác nhau; chọn mức đầu tiên đủ số bộ ba.
    # Việc chọn này chỉ dựa trên SỐ MẪU, không dựa trên kết quả.
    cac_he_so = [1.5, 1.2, 1.0, 0.8, 0.6, 0.5]
    # Nới ngưỡng "cân bằng" nếu một bên quá ít mẫu (vẫn là lựa chọn theo số mẫu).
    cac_nguong = [0.25, 0.35, 0.45, 0.60]

    records = None
    he_so_da_dung = None
    nguong_da_dung = None

    for he_so in cac_he_so:
        ch = _goi_chan_song(df, he_so)
        if ch is None or len(ch) < 10:
            continue
        doan = _tinh_doan(df, ch)
        if doan is None or len(doan) < 10:
            continue

        for nguong in cac_nguong:
            rec = _lay_records(doan, nguong)
            if len(rec) >= 30:
                arr = np.array(rec, dtype=bool)  # chỉ để đếm nhóm
                n_cb_tmp = int(arr[:, 0].sum())
                n_lc_tmp = len(rec) - n_cb_tmp
                if n_cb_tmp >= 10 and n_lc_tmp >= 10:
                    records = rec
                    he_so_da_dung = he_so
                    nguong_da_dung = nguong
                    break
        if records is not None:
            break

    if records is None or len(records) < 30:
        return None

    # Tách dữ liệu
    cb_arr = np.array([r[0] for r in records], dtype=bool)
    slope_arr = np.array([r[1] for r in records], dtype=float)
    n = len(records)
    n_cb = int(cb_arr.sum())
    n_lc = n - n_cb

    # Thống kê quan sát: mean(slope nhóm lệch) - mean(slope nhóm cân bằng)
    # Dương = nhóm cân bằng có slope thấp hơn = phẳng hơn => ủng hộ khẳng định.
    obs = float(slope_arr[~cb_arr].mean() - slope_arr[cb_arr].mean())

    # Hoán vị: giữ nguyên số lượng can_bang, hoán vị nhãn giữa các bộ ba.
    n_perm = 2000
    perm_stats = np.empty(n_perm)
    idx_all = np.arange(n)

    for k in range(n_perm):
        perm = rng.permutation(idx_all)
        labels = np.zeros(n, dtype=bool)
        labels[perm[:n_cb]] = True
        perm_stats[k] = slope_arr[~labels].mean() - slope_arr[labels].mean()

    null_tb = float(perm_stats.mean())
    null_sd = float(perm_stats.std(ddof=1))
    if null_sd == 0:
        return None

    thong_ke = (obs - null_tb) / null_sd
    # Một phía: xác suất hoán vị cho diff >= quan sát.
    p = (1 + int(np.sum(perm_stats >= obs))) / (n_perm + 1)

    ghi_chu = (
        f"Zigzag từ bc.chan_song, thử he_so={cac_he_so}, chọn he_so={he_so_da_dung} "
        f"theo tiêu chí đủ mẫu (không theo kết quả). "
        f"Bộ ba = 3 đoạn liên tiếp cùng chiều-ngược-cùng chiều; lấy tất cả bộ ba liên tiếp. "
        f"Biên độ mỗi đoạn chia ATR(14) tại bar xác nhận cuối đoạn (luật 4). "
        f"Cân bằng: |ln(amp_C/amp_A)| <= {nguong_da_dung}. "
        f"Độ phẳng chân giữa đo bằng slope_norm = (amp_B/ATR)/thoi_luong_B; thấp hơn = phẳng hơn. "
        f"thong_ke = (q.sát - null_tb)/null_sd; q.sát = mean(slope_nhóm_lệch) - mean(slope_nhóm_cân_bằng); "
        f"dương = ủng hộ khẳng định. Hoán vị nhãn can_bang giữa các bộ ba, giữ nguyên số can_bang."
    )

    result = {
        'thong_ke': thong_ke,
        'p': p,
        'n': n,
        'quan_sat_tho': obs,
        'null_tb': null_tb,
        'null_sd': null_sd,
        'n_can_bang': n_cb,
        'n_lech': n_lc,
        'slope_trung_binh_can_bang': float(slope_arr[cb_arr].mean()),
        'slope_trung_binh_lech': float(slope_arr[~cb_arr].mean()),
        'he_so_da_dung': he_so_da_dung,
        'nguong_can_bang': nguong_da_dung,
        'ghi_chu': ghi_chu,
    }

    # Gợi ý nếu phát hiện có ý nghĩa
    if thong_ke > 0 and p < 0.05:
        result['de_xuat'] = (
            "Trong zigzag 3 chân, khi hai chân cùng chiều có biên độ cân bằng, "
            "chân giữa có slope thấp hơn (đi ngang hơn). Có thể dùng làm điều kiện lọc "
            "cho chiến lược pullback: kỳ vọng giá điều chỉnh kéo dài và ít sâu hơn."
        )

    return result