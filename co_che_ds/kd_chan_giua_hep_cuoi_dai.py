import numpy as np
import pandas as pd
import brain_co_che as bc

def do(khoa, df, rng):
    # ---------- 1. Lấy các chân zigzag với ngưỡng thấp hơn để đủ mẫu ----------
    ch = bc.chan_song(df, he_so=1.5)
    if ch is None or len(ch) < 5:
        return None

    ch = ch.dropna(subset=['vi_tri', 'xac_nhan', 'gia']).copy()
    if len(ch) < 5:
        return None

    # Chuyển vi_tri / xac_nhan về vị trí số nguyên trong df
    def _to_pos(v):
        if isinstance(v, (int, np.integer)):
            return int(v)
        if isinstance(v, float) and float(v).is_integer():
            return int(v)
        try:
            pos = df.index.get_loc(v)
            if isinstance(pos, slice):
                return int(pos.start)
            if isinstance(pos, np.ndarray):
                return int(pos[0]) if len(pos) else int(v)
            return int(pos)
        except Exception:
            return int(v)

    ch['vi_tri'] = ch['vi_tri'].map(_to_pos)
    ch['xac_nhan'] = ch['xac_nhan'].map(_to_pos)
    ch = ch.sort_values('vi_tri').reset_index(drop=True)

    vi_tri = ch['vi_tri'].to_numpy(dtype=int)
    gia = ch['gia'].to_numpy(dtype=float)
    xac_nhan = ch['xac_nhan'].to_numpy(dtype=int)

    # Mỗi đoạn nối hai chân liên tiếp
    tu = vi_tri[:-1]
    den = vi_tri[1:]
    gia_tu = gia[:-1]
    gia_den = gia[1:]
    bien_do = np.abs(gia_den - gia_tu)
    huong = np.sign(gia_den - gia_tu)
    thoi_luong = den - tu
    xac_nhan_doan = xac_nhan[1:]

    mask = (bien_do > 0) & (huong != 0) & (thoi_luong > 0)
    if mask.sum() < 3:
        return None

    doan = pd.DataFrame({
        'tu': tu[mask],
        'den': den[mask],
        'bien_do': bien_do[mask],
        'huong': huong[mask],
        'thoi_luong': thoi_luong[mask],
        'xac_nhan': xac_nhan_doan[mask],
    })

    # ---------- 2. Tạo các bộ ba chân cùng hướng liên tiếp ----------
    def bo_ba_theo_huong(seg):
        seg = seg.reset_index(drop=True)
        if len(seg) < 3:
            return None
        A = seg.iloc[:-2].reset_index(drop=True)
        B = seg.iloc[1:-1].reset_index(drop=True)
        C = seg.iloc[2:].reset_index(drop=True)
        return pd.DataFrame({
            'bien_do_A': A['bien_do'].to_numpy(),
            'bien_do_B': B['bien_do'].to_numpy(),
            'bien_do_C': C['bien_do'].to_numpy(),
            'thoi_luong_A': A['thoi_luong'].to_numpy(),
            'thoi_luong_C': C['thoi_luong'].to_numpy(),
            'xac_nhan_C': C['xac_nhan'].to_numpy(),
            'huong': A['huong'].to_numpy(),
        })

    up = bo_ba_theo_huong(doan[doan['huong'] == 1])
    down = bo_ba_theo_huong(doan[doan['huong'] == -1])

    parts = [x for x in [up, down] if x is not None]
    if not parts:
        return None

    all_bb = pd.concat(parts, ignore_index=True)
    if len(all_bb) < 30:
        return None

    # Điều kiện: chân giữa có biên độ nhỏ hơn cả hai chân kia
    event = (all_bb['bien_do_B'] < all_bb['bien_do_A']) & (all_bb['bien_do_B'] < all_bb['bien_do_C'])

    # Thước đo: log(TL/BD của chân 3) - log(TL/BD của chân 1)
    # = thời lượng trên mỗi đơn vị biên độ; dương = chân 3 chậm hơn chân 1
    tl_A_chuan = all_bb['thoi_luong_A'] / all_bb['bien_do_A']
    tl_C_chuan = all_bb['thoi_luong_C'] / all_bb['bien_do_C']
    delta = np.log(tl_C_chuan) - np.log(tl_A_chuan)

    # Lọc các giá trị không hợp lệ
    finite = np.isfinite(delta)
    all_bb = all_bb[finite].reset_index(drop=True)
    delta = delta[finite].to_numpy(dtype=float)
    event = event[finite].to_numpy(dtype=bool)
    huong_arr = all_bb['huong'].to_numpy(dtype=int)

    n_ev = int(event.sum())
    n_non = int((~event).sum())
    if n_ev < 30 or n_non < 30:
        return None

    # ---------- 3. Thống kê quan sát ----------
    obs_stat = delta[event].mean() - delta[~event].mean()

    # ---------- 4. Hoán vị giữ phôi nhiễm ----------
    # Giữ nguyên số sự kiện và tỷ lệ up/down bằng cách hoán vị nhãn trong từng hướng
    n_perm = 2000
    up_idx = np.where(huong_arr == 1)[0]
    down_idx = np.where(huong_arr == -1)[0]
    n_ev_up = int(event[up_idx].sum())
    n_ev_down = int(event[down_idx].sum())

    perm_stats = np.empty(n_perm)
    for b in range(n_perm):
        perm_label = np.zeros(len(delta), dtype=bool)
        if n_ev_up > 0:
            chosen = rng.choice(up_idx, size=n_ev_up, replace=False)
            perm_label[chosen] = True
        if n_ev_down > 0:
            chosen = rng.choice(down_idx, size=n_ev_down, replace=False)
            perm_label[chosen] = True
        perm_stats[b] = delta[perm_label].mean() - delta[~perm_label].mean()

    # p-value hoán vị hai phía, cộng 1 để tránh p = 0
    count = int((np.abs(perm_stats) >= np.abs(obs_stat)).sum())
    p = (count + 1) / (n_perm + 1)

    null_tb = float(perm_stats.mean())
    null_sd = float(perm_stats.std(ddof=1))
    if null_sd > 0:
        thong_ke = (obs_stat - null_tb) / null_sd
    else:
        thong_ke = 0.0

    return {
        'thong_ke': float(thong_ke),
        'p': float(p),
        'n': int(n_ev),
        'quan_sat_tho': float(obs_stat),
        'null_tb': null_tb,
        'null_sd': null_sd,
        'n_bo_ba': int(len(delta)),
        'trung_binh_delta_event': float(delta[event].mean()),
        'trung_binh_delta_non_event': float(delta[~event].mean()),
        'ghi_chu': (
            'Dung bc.chan_song(he_so=1.5). '
            'Do luong = log(TL/BD cua chan thu 3) - log(TL/BD cua chan thu 1), '
            'tuc thoi luong tren mot don vi bien do. Duong = chan thu ba cham hon chan thu nhat. '
            'thong_ke = mean(delta_event) - mean(delta_non_event), chuan hoa theo phan phoi hoan vi. '
            'p la p hoan vi hai phia, giu nguyen so su kien va ty le up/down.'
        ),
        'de_xuat': (
            'Thu ghep dieu kien: chan giua nho nam o cuoi mot chuoi nhieu chan cung huong '
            '(vi du tu doan thu 5 tro di) de xem hieu ung nen co manh hon khong.'
        ),
    }