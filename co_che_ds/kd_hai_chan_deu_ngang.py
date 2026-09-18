import numpy as np
import brain_co_che as bc


def _sign_arr(huong):
    signs = []
    for x in huong:
        if isinstance(x, str):
            s = x.strip().lower()
            if s in ("1", "1.0", "up", "buy", "bull", "long"):
                signs.append(1.0)
            elif s in ("-1", "-1.0", "down", "sell", "bear", "short"):
                signs.append(-1.0)
            else:
                try:
                    v = float(s)
                    signs.append(1.0 if v > 0 else -1.0)
                except ValueError:
                    signs.append(np.nan)
        else:
            try:
                v = float(x)
                signs.append(1.0 if v > 0 else -1.0)
            except (TypeError, ValueError):
                signs.append(np.nan)
    return np.array(signs, dtype=float)


def _events(seg):
    if seg is None or len(seg) < 4:
        return []

    need = {"do_dai", "thoi_luong", "huong"}
    if not need.issubset(set(seg.columns)):
        return []

    amp = np.abs(seg["do_dai"].to_numpy(dtype=float))
    dur = seg["thoi_luong"].to_numpy(dtype=float)
    signs = _sign_arr(seg["huong"].to_numpy())

    if "biet_tai" in seg.columns:
        times = seg["biet_tai"].to_numpy()
    elif "xac_nhan" in seg.columns:
        times = seg["xac_nhan"].to_numpy()
    else:
        times = np.arange(len(seg))

    evs = []
    for i in range(len(seg) - 2):
        s0, s1, s2 = signs[i], signs[i + 1], signs[i + 2]
        if np.isnan(s0) or np.isnan(s1) or np.isnan(s2):
            continue
        if s0 != s2 or s1 == s2:
            continue

        a0 = amp[i]
        a2 = amp[i + 2]
        d = dur[i + 1]

        if not (np.isfinite(a0) and np.isfinite(a2) and np.isfinite(d)):
            continue
        if a0 <= 0 or a2 <= 0 or d <= 0:
            continue

        diff_ratio = abs(a0 - a2) / max(a0, a2)
        label = 1 if diff_ratio <= 0.10 else 0
        evs.append((times[i + 2], label, float(d), float(diff_ratio)))

    return evs


def _lay_du_lieu(df):
    for he_so in (3.0, 2.5, 2.0, 1.5, 1.2):
        try:
            ch = bc.chan_song(df, he_so=he_so)
            if ch is None or len(ch) < 5:
                continue
            seg = bc.cac_doan(df, ch)
            evs = _events(seg)
            if len(evs) < 60:
                continue

            n1 = sum(e[1] == 1 for e in evs)
            n0 = len(evs) - n1
            if min(n1, n0) < 30:
                continue

            return evs, he_so
        except Exception:
            continue

    return None, None


def do(khoa, df, rng):
    try:
        evs, he_so = _lay_du_lieu(df)
        if evs is None or len(evs) < 60:
            return None

        durations = np.array([e[2] for e in evs], dtype=float)
        labels = np.array([e[1] for e in evs], dtype=int)

        n = len(evs)
        n1 = int(labels.sum())
        n0 = n - n1
        if min(n1, n0) < 30:
            return None

        obs = durations[labels == 1].mean() - durations[labels == 0].mean()

        pool = np.concatenate(
            (np.ones(n1, dtype=int), np.zeros(n0, dtype=int))
        )

        R = 2000
        perm_stats = np.empty(R)
        for r in range(R):
            perm_labels = pool[rng.permutation(n)]
            perm_stats[r] = (
                durations[perm_labels == 1].mean()
                - durations[perm_labels == 0].mean()
            )

        null_mean = perm_stats.mean()
        null_sd = perm_stats.std(ddof=1)
        if null_sd == 0 or not np.isfinite(null_sd):
            return None

        thong_ke = (obs - null_mean) / null_sd
        p = (1 + np.sum(perm_stats >= obs)) / (R + 1.0)

        return {
            "thong_ke": float(thong_ke),
            "p": float(p),
            "n": int(n),
            "quan_sat_tho": float(obs),
            "null_tb": float(null_mean),
            "null_sd": float(null_sd),
            "n_can_bang": int(n1),
            "n_khong_can_bang": int(n0),
            "he_so_zigzag": he_so,
            "ghi_chu": (
                "Su kien: ba chan lien tiep A-B-C, A va C cung huong, B nguoc huong. "
                "Do dai hai chan cung huong la do_dai(cua A va C); can bang neu "
                "|A-C|/max(A,C) <= 10%. Outcome la so nen cua chan xen giua B. "
                "Khong nhin tuong lai: su kien duoc gan moc tai biet_tai cua chan C, "
                "tuc thoi diem swing cuoi duoc xac nhan. "
                "Hoan vi 2000 lan nhan can_bang/khong_can_bang giua cac su kien, "
                "giu nguyen so su kien moi nhom va thoi diem su kien. "
                "p la p mot phia: trung binh duration nhom can bang > nhom khong can bang. "
                "Khong chia cho ATR vi outcome la so nen, khong phai do lon gia; "
                "luat 4 khong ap dung truc tiep."
            ),
        }
    except Exception:
        return None