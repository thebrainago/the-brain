import numpy as np
from scipy.stats import rankdata
import brain_co_che as bc


def do(khoa, df, rng):
    # Hạ ngưỡng zigzag để có đủ mẫu; dùng he_so=1.0 thay vì mặc định 3.0.
    try:
        ch = bc.chan_song(df, he_so=1.0)
    except TypeError:
        ch = bc.chan_song(df)

    if ch is None or len(ch) < 10:
        return None

    ch = ch.sort_values('vi_tri').reset_index(drop=True)
    pos = ch['vi_tri'].to_numpy(dtype=int)
    xac = ch['xac_nhan'].to_numpy(dtype=int)
    gia = ch['gia'].to_numpy(dtype=float)

    if len(pos) < 8:
        return None

    # Đặc trưng từng chân sóng (leg) nối hai swing point liên tiếp.
    A = np.abs(np.diff(gia))                # biên độ giá
    D = np.diff(pos).astype(float)          # thời lượng (số bar giữa 2 swing point)
    H = np.sign(np.diff(gia))               # hướng: +1 lên, -1 xuống

    # Tổng khối lượng từng chân, dùng cumsum để nhanh.
    vol = df['volume'].to_numpy(dtype=float)
    cumvol = np.concatenate([[0.0], np.cumsum(vol)])
    n_leg = len(pos) - 1
    V = np.empty(n_leg)
    for j in range(n_leg):
        s = int(pos[j])
        e = int(pos[j + 1])
        if e < s:
            return None
        V[j] = cumvol[e + 1] - cumvol[s]

    open_vals = df['open'].to_numpy(dtype=float)
    events = []

    # Sự kiện: L[i] và L[i+2] cùng hướng, L[i+1] ngược hướng.
    # Event_time = xac_nhan của S[i+3] (đỉnh/đáy thứ hai cùng hướng).
    for i in range(n_leg - 3):
        if H[i] == 0 or H[i + 1] == 0 or H[i + 2] == 0:
            continue
        if not (H[i] == H[i + 2] and H[i + 1] == -H[i]):
            continue
        if A[i] <= 0 or A[i + 2] <= 0:
            continue

        # "Biên độ gần bằng nhau": định nghĩa rộng [0.5, 2.0] để đủ mẫu.
        r_amp = A[i + 2] / A[i]
        if r_amp < 0.5 or r_amp > 2.0:
            continue

        V1 = V[i]
        V2 = V[i + 2]
        if V1 <= 0 or V2 <= 0:
            continue

        event_time = int(xac[i + 3])
        if event_time + 1 >= len(df):
            continue

        # Outcome đo HOÀN TOÀN SAU khi biết tín hiệu:
        # giá vào = open của bar sau event_time; tìm swing ngược chiều đầu tiên
        # có vi_tri > event_time (không dùng đỉnh/đáy trong quá khứ).
        out_k = None
        for k in range(i + 4, len(pos)):
            if pos[k] > event_time + 1:
                if (H[i] > 0 and gia[k] < gia[i + 3]) or (H[i] < 0 and gia[k] > gia[i + 3]):
                    out_k = k
                    break
        if out_k is None:
            continue

        A_base = 0.5 * (A[i] + A[i + 2])
        D_base = 0.5 * (D[i] + D[i + 2])
        if A_base <= 0 or D_base <= 0:
            continue

        start_price = open_vals[event_time + 1]
        end_price = gia[out_k]
        amp_forward = abs(end_price - start_price)
        dur_forward = float(pos[out_k] - (event_time + 1))
        if amp_forward <= 0 or dur_forward <= 0:
            continue

        # X > 0 khi chân sau có tổng khối lượng thấp hơn chân trước.
        log_vol_ratio = float(np.log(V2 / V1))
        events.append((log_vol_ratio, A_base, D_base, amp_forward, dur_forward, float(H[i])))

    if len(events) < 30:
        return None

    arr = np.asarray(events, dtype=float)
    X = -arr[:, 0]               # -log(V2/V1): dương = khối lượng thấp hơn
    A_base = arr[:, 1]
    D_base = arr[:, 2]
    amp_f = arr[:, 3]
    dur_f = arr[:, 4]
    dirs = arr[:, 5].astype(int)

    if np.std(X, ddof=1) == 0:
        return None

    log_amp = np.log(amp_f / A_base)
    log_dur = np.log(dur_f / D_base)
    if not np.all(np.isfinite(log_amp)) or not np.all(np.isfinite(log_dur)):
        return None

    std_amp = np.std(log_amp, ddof=1)
    std_dur = np.std(log_dur, ddof=1)
    if std_amp == 0 or std_dur == 0:
        return None

    z_amp = (log_amp - log_amp.mean()) / std_amp
    z_dur = (log_dur - log_dur.mean()) / std_dur

    # S càng cao = biên độ càng nhỏ + thời lượng càng dài.
    S = -z_amp + z_dur
    if not np.all(np.isfinite(S)):
        return None

    rank_S = rankdata(S)
    rank_X = rankdata(X)
    T_obs = float(np.corrcoef(rank_X, rank_S)[0, 1])
    if not np.isfinite(T_obs):
        return None

    n_perm = 2000
    perms = np.empty(n_perm)

    def _perm_stat(Xp, rank_S_ref):
        rx = rankdata(Xp)
        return float(np.corrcoef(rx, rank_S_ref)[0, 1])

    # Hoán vị X trong từng nhóm cùng hướng để giữ số sự kiện và tỷ lệ up/down.
    for b in range(n_perm):
        Xp = X.copy()
        for g in np.unique(dirs):
            idx = np.where(dirs == g)[0]
            if len(idx) > 1:
                vals = Xp[idx].copy()
                Xp[idx] = rng.permutation(vals)
        perms[b] = _perm_stat(Xp, rank_S)

    null_mean = float(perms.mean())
    null_sd = float(perms.std(ddof=1))
    if null_sd == 0 or not np.isfinite(null_sd):
        return None

    thong_ke = (T_obs - null_mean) / null_sd
    p = float((1 + int(np.sum(perms >= T_obs))) / (n_perm + 1))

    n_cond_loose = int(np.sum(X > 0))  # số sự kiện có khối lượng chân sau thấp hơn hẳn

    return {
        'thong_ke': thong_ke,
        'p': p,
        'n': int(len(S)),
        'quan_sat_tho': T_obs,
        'null_tb': null_mean,
        'null_sd': null_sd,
        'n_khoi_luong_thap_hon': n_cond_loose,
        'n_up': int(np.sum(dirs == 1)),
        'n_down': int(np.sum(dirs == -1)),
        'de_xuat': 'Ghep them dieu kien: hieu ung ro hon khi X < -0.2 (khoi luong thap ro rang) va bien do hai chan truoc trong [0.8, 1.25].',
        'ghi_chu': (
            'Zigzag he_so=1.0 de du mau; "bien do gan bang nhau" = ty le A2/A1 trong [0.5, 2.0]. '
            'Su kien: L[i] va L[i+2] cung huong, L[i+1] nguoc. Event_time = xac_nhan cua S[i+3]; '
            'outcome do tu open[event_time+1] den swing nguoc chieu dau tien co vi_tri sau entry, khong nhin tuong lai. '
            'Bien dieu kien lien tuc X = -log(V2/V1), duong khi chan sau khoi luong thap hon. '
            'S = -z(log(amp_out/A_base)) + z(log(dur_out/D_base)); A_base/D_base la trung binh hai chan cung huong. '
            'Thong ke = Spearman(X, S) duong = ung ho khang dinh. '
            'Hoan vi X trong nhom cung huong, giu so su kien va ty le up/down. p mot phia.'
        ),
    }