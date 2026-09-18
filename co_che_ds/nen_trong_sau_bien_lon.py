import numpy as np
import pandas as pd


def do(khoa, df, rng):
    n = len(df)
    if n < 30:
        return None

    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    rng_arr = high - low

    # mean(range) cua 20 phien truoc do, tinh tai bar i
    prev_mean = pd.Series(rng_arr).rolling(20).mean().shift(1).to_numpy()

    # j la phien inside, i = j - 1 la phien expansion
    j_arr = np.arange(21, n - 1)
    if j_arr.size < 30:
        return None

    i = j_arr - 1

    expansion = rng_arr[i] >= 2.0 * prev_mean[i]
    inside = (high[j_arr] < high[i]) & (low[j_arr] > low[i])
    success = rng_arr[j_arr + 1] < rng_arr[j_arr]

    # Test chat hon: chi xet cac phien inside.
    # Su kien = co phien truoc do la expansion lon.
    # Dieu nay tranh nham lan do ban than nến inside da co xac suat nen cao.
    sample_mask = inside
    sample_range = rng_arr[j_arr[sample_mask]]
    sample_success = success[sample_mask].astype(np.int8)
    sample_event = expansion[sample_mask]

    n_events = int(sample_event.sum())
    if n_events < 30:
        return None

    obs = float(sample_success[sample_event].mean())
    S = int(sample_event.size)
    n_perm = 2000

    # Hoan vi co dieu kien theo nhom phan vi cua range[j] (bien do nến inside)
    # de kiem soat volatility clustering (luat 4).
    def null_dist():
        edges = np.quantile(sample_range, np.linspace(0, 1, 6))
        edges = np.unique(edges)

        if len(edges) >= 3:
            strata = np.digitize(sample_range, edges[1:-1])
            n_strata = int(strata.max()) + 1
            event_counts = np.bincount(strata[sample_event], minlength=n_strata)

            pos_by_strata = []
            success_by_strata = []
            for s in range(n_strata):
                pos_s = np.where(strata == s)[0]
                pos_by_strata.append(pos_s)
                success_by_strata.append(sample_success[pos_s])

            null = np.empty(n_perm, dtype=float)
            for b in range(n_perm):
                total = 0
                for s in range(n_strata):
                    k = int(event_counts[s])
                    if k == 0:
                        continue
                    pos_s = pos_by_strata[s]
                    y_s = success_by_strata[s]
                    if pos_s.size == k:
                        total += int(y_s.sum())
                    else:
                        chosen = rng.choice(pos_s.size, size=k, replace=False)
                        total += int(y_s[chosen].sum())
                null[b] = total / n_events

            if np.unique(null).size >= 2:
                return null

        # fallback: hoan vi toan cuc, van giu nguyen so su kien
        null = np.empty(n_perm, dtype=float)
        for b in range(n_perm):
            chosen = rng.choice(S, size=n_events, replace=False)
            null[b] = float(sample_success[chosen].mean())
        return null

    null = null_dist()
    null_tb = float(null.mean())
    null_sd = float(null.std(ddof=1)) if null.size > 1 else 0.0

    if null_sd < 1e-15:
        thong_ke = 0.0
        p = 1.0
    else:
        thong_ke = (obs - null_tb) / null_sd
        p = float((1 + np.sum(null >= obs)) / (1 + n_perm))

    if S > n_events:
        success_non_event = float(sample_success[~sample_event].mean())
    else:
        success_non_event = float("nan")

    ghi_chu = (
        "Định nghĩa chặt hơn câu gốc: xét riêng các phiên inside "
        "(high[j] < high[i], low[j] > low[i]); sự kiện là phiên i = j-1 có "
        "range >= 2 * mean(range 20 phiên trước). Dự báo range[j+1] < range[j]. "
        "Không dùng thông tin j+1 để chọn sự kiện. "
        "Hoán vị có điều kiện: giữ nguyên số sự kiện, hoán vị vị trí sự kiện "
        "trong 5 nhóm phân vị của range[j] để kiểm soát volatility clustering. "
        "p một phía; thong_ke dương = ủng hộ khẳng định. "
        "Không có vị thế long/short nên không hoán vị tỷ lệ mua-bán."
    )
    de_xuat = (
        "Thử thêm điều kiện volume của nến inside thấp hơn trung bình 20 phiên: "
        "sau quét biên độ lớn + inside + volume khô, xác suất nén tiếp theo có thể cao hơn nữa."
    )

    return {
        "thong_ke": float(thong_ke),
        "p": float(p),
        "n": n_events,
        "quan_sat_tho": obs,
        "null_tb": null_tb,
        "null_sd": null_sd,
        "n_inside": S,
        "n_eligible": int(j_arr.size),
        "success_non_event": success_non_event,
        "ghi_chu": ghi_chu,
        "de_xuat": de_xuat,
    }