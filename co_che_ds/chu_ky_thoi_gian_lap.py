import numpy as np
import pandas as pd

def _xac_dinh_dinh(high, window=20):
    """
    Xác định các phiên mà high[i] > max(high[i-window:i]) (chỉ dùng quá khứ).
    Trả về danh sách các chỉ số i.
    """
    peaks = []
    for i in range(window, len(high)):
        # chỉ so sánh với window phiên trước (không gồm i)
        if high[i] > np.max(high[i-window:i]):
            peaks.append(i)
    return np.array(peaks, dtype=int)

def _tinh_S(D):
    """
    Tính S = MAE_naive - MAE_dung_2khoang trên mảng khoảng cách D.
    D là mảng 1D, độ dài N >= 3.
    """
    N = len(D)
    if N < 3:
        return np.nan
    # Dự báo bằng trung bình 2 khoảng trước
    pred2 = (D[:-2] + D[1:-1]) / 2.0
    actual = D[2:]
    mae2 = np.mean(np.abs(actual - pred2))
    # Dự báo bằng trung bình lịch sử (chỉ dùng các khoảng trước đó)
    cumsum = np.cumsum(D)
    k = np.arange(2, N)  # chỉ số của actual (0-based)
    pred_naive = cumsum[k-1] / k  # mean(D[:k])
    mae_naive = np.mean(np.abs(actual - pred_naive))
    return mae_naive - mae2

def do(khoa, df, rng):
    # 1. Xác định các đỉnh 20 phiên
    high = df['high'].values
    idx_peaks = _xac_dinh_dinh(high, window=20)
    if len(idx_peaks) < 2:
        return None  # không đủ đỉnh để có khoảng cách

    # 2. Khoảng cách giữa các đỉnh liên tiếp
    D = np.diff(idx_peaks).astype(float)
    if len(D) < 30:  # luật 5: mẫu quá nhỏ
        return None

    # 3. Thống kê quan sát
    S_obs = _tinh_S(D)
    if np.isnan(S_obs):
        return None

    # 4. Hoán vị (giữ nguyên phân phối biên của D, phá vỡ cấu trúc thời gian)
    n_perm = 2000
    S_perms = np.empty(n_perm)
    for i in range(n_perm):
        D_perm = rng.permutation(D)
        S_perms[i] = _tinh_S(D_perm)
        if np.isnan(S_perms[i]):
            S_perms[i] = 0.0  # không xảy ra vì N>=3

    # 5. Tính p-value và thống kê chuẩn hoá
    mean_null = np.mean(S_perms)
    std_null = np.std(S_perms)
    if std_null == 0:
        return None  # không có biến động, không thể kết luận

    thong_ke = (S_obs - mean_null) / std_null
    p = (np.sum(S_perms >= S_obs) + 1) / (n_perm + 1)  # cộng 1 để tránh p=0

    # 6. Trả về dict
    n = len(D) - 2  # số cặp dự báo
    return {
        'thong_ke': thong_ke,
        'p': p,
        'n': n,
        'quan_sat_tho': S_obs,
        'null_tb': mean_null,
        'null_sd': std_null,
        'mae_naive': np.mean(np.abs(D[2:] - np.cumsum(D)[np.arange(2,len(D))-1] / np.arange(2,len(D)))),
        'mae_2k': np.mean(np.abs(D[2:] - (D[:-2] + D[1:-1])/2)),
        'ghi_chu': (
            "Định nghĩa đỉnh: phiên i có high[i] > max(high[i-20:i]) (chỉ dùng quá khứ). "
            "Khoảng cách là số phiên giữa các đỉnh liên tiếp. "
            "Thống kê S = MAE(naive) - MAE(dùng 2 khoảng trước); S>0 nghĩa là mô hình 2 khoảng tốt hơn. "
            "Hoán vị: xáo trộn toàn bộ chuỗi khoảng cách để phá vỡ cấu trúc thời gian, giữ nguyên phân phối biên. "
            "Luật 4: không chia cho biên độ vì khoảng cách là số phiên, không phải độ lớn giá; tuy nhiên, "
            "volatility clustering có thể ảnh hưởng đến độ dài khoảng cách, nhưng phương pháp hoán vị toàn bộ "
            "đã phần nào kiểm soát điều đó."
        )
    }