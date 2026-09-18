import numpy as np
import pandas as pd


def do(khoa, df, rng):
    # ---- Thước đo: z-score của log(volume) so với 20 phiên trước ----
    vol = df['volume'].to_numpy(dtype=float)
    if len(vol) < 40:
        return None

    with np.errstate(divide='ignore', invalid='ignore'):
        log_vol = np.log(vol)
    s = pd.Series(log_vol)

    # mean/std của 20 phiên liền trước, không gồm phiên hiện tại
    ma = s.rolling(20).mean().shift(1).to_numpy()
    sd = s.rolling(20).std().shift(1).to_numpy()

    with np.errstate(divide='ignore', invalid='ignore'):
        z = (log_vol - ma) / sd

    valid = np.isfinite(z)
    valid_idx = np.where(valid)[0]
    z_arr = z[valid]
    N = len(z_arr)
    if N < 30:
        return None

    # ---- Sự kiện: phiên giao dịch cuối cùng của mỗi tháng ----
    month = df.index.to_period('M')
    last = df.groupby(month).tail(1)
    pos = df.index.get_indexer(last.index)

    pos_in_arr = np.searchsorted(valid_idx, pos)
    keep = (pos_in_arr < N) & (valid_idx[pos_in_arr] == pos)
    pos_valid = pos_in_arr[keep]
    n = len(pos_valid)
    if n < 30:
        return None

    obs = z_arr[pos_valid].mean()

    # ---- Hoán vị giữ phối nhiễm: circular shift toàn bộ vị trí cuối tháng ----
    B = 2000
    if N < 2:
        return None

    null_means = np.empty(B)
    for i in range(B):
        d = int(rng.integers(1, N))
        null_means[i] = z_arr[(pos_valid + d) % N].mean()

    null_mean = null_means.mean()
    null_sd = null_means.std(ddof=1)
    if not np.isfinite(null_sd) or null_sd <= 1e-15:
        return None

    thong_ke = (obs - null_mean) / null_sd
    p = (1.0 + np.sum(null_means >= obs)) / (B + 1.0)

    return {
        'thong_ke': float(thong_ke),
        'p': float(p),
        'n': int(n),
        'quan_sat_tho': float(obs),
        'null_tb': float(null_mean),
        'null_sd': float(null_sd),
        'de_xuat': ('Có thể kiểm tra tiếp nếu hiệu ứng cuối tháng mạnh hơn '
                    'vào tháng cuối quý (window dressing của quỹ) hoặc ở các '
                    'thị trường có nhiều quỹ đầu tư lớn.'),
        'ghi_chu': (
            'Thước đo: z = (log(volume) - mean_20_truoc) / std_20_truoc, '
            'trong đó mean_20_truoc và std_20_truoc tính trên 20 phiên liền trước (shift 1). '
            'z dương = volume cao hơn trung bình 20 phiên trước, theo đơn vị độ lệch chuẩn. '
            'Đã chuẩn hóa theo std_20 để giảm ảnh hưởng của volatility clustering (luật 4). '
            'Hoán vị: dịch chuyển vòng tròn toàn bộ danh sách vị trí cuối tháng đi một lượng phiên '
            'ngẫu nhiên, giữ nguyên số sự kiện và khoảng cách tương đối giữa chúng. '
            'p là p một phía (phải).'
        ),
    }