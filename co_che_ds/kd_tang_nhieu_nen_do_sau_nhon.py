def do(khoa, df, rng):
    import numpy as np
    import pandas as pd

    try:
        import brain_co_che as bc
    except Exception:
        return None

    def _pos(x):
        if isinstance(x, (int, np.integer)):
            return int(x)
        if isinstance(x, (float, np.floating)):
            if np.isfinite(x) and float(x).is_integer():
                return int(x)
        try:
            return df.index.get_loc(x)
        except Exception:
            return -1

    def _get_ch(he):
        try:
            ch = bc.chan_song(df, he_so=he)
        except TypeError:
            try:
                ch = bc.chan_song(df, he)
            except Exception:
                ch = bc.chan_song(df)
        except Exception:
            try:
                ch = bc.chan_song(df)
            except Exception:
                return None
        if ch is None or len(ch) < 5:
            return None
        try:
            ch = ch.sort_values("vi_tri").reset_index(drop=True)
        except Exception:
            return None
        return ch

    # ATR dùng để chuẩn hoá độ sâu theo luật 4.
    try:
        atr_raw = bc.atr(df, 14)
    except Exception:
        return None
    if atr_raw is None:
        return None

    if isinstance(atr_raw, pd.Series):
        atr = atr_raw.astype(float)
    else:
        atr = pd.Series(np.asarray(atr_raw).ravel(), index=df.index).astype(float)
    atr = atr.ffill().bfill()

    def _build(he):
        ch = _get_ch(he)
        if ch is None:
            return None

        # Tự dựng các đoạn nối hai swing liên tiếp từ chan_song.
        # Chỉ giữ đoạn khi cả hai đầu swing đều đã được xác nhận.
        legs = []
        for i in range(len(ch) - 1):
            tu = _pos(ch.at[i, "vi_tri"])
            den = _pos(ch.at[i + 1, "vi_tri"])
            bt1 = _pos(ch.at[i, "xac_nhan"])
            bt2 = _pos(ch.at[i + 1, "xac_nhan"])
            if min(tu, den, bt1, bt2) < 0:
                continue
            if max(tu, den, bt1, bt2) >= len(df):
                continue
            if tu > den:
                continue
            if tu == den:
                continue

            # Hướng đoạn: so sánh giá swing, hoặc fallback bằng close.
            try:
                p0 = float(ch.at[i, "gia"])
                p1 = float(ch.at[i + 1, "gia"])
                direction = 1 if p1 >= p0 else -1
            except Exception:
                direction = 1 if df.iloc[den]["close"] >= df.iloc[tu]["close"] else -1

            legs.append({"tu": tu, "den": den, "dir": direction})

        if len(legs) < 4:
            return None

        # Tất cả chân giảm: dùng để tính trung vị "thời lượng" và "độ sâu chuẩn hoá".
        records = []
        for j, lg in enumerate(legs):
            if lg["dir"] >= 0:
                continue

            tu = lg["tu"]
            den = lg["den"]
            dur = den - tu + 1

            try:
                depth = abs(float(df.iloc[tu]["high"] - df.iloc[den]["low"]))
                av = float(atr.iloc[tu])
            except Exception:
                continue

            if not np.isfinite(depth) or not np.isfinite(av) or av <= 0:
                continue

            norm_depth = depth / av

            # Sự kiện: chân tăng ngay trước có số nến đỏ > số nến xanh.
            has_prev_up = False
            cond = False
            if j > 0 and legs[j - 1]["dir"] > 0 and legs[j - 1]["den"] == tu:
                has_prev_up = True
                u_tu = legs[j - 1]["tu"]
                u_den = legs[j - 1]["den"]
                seg = df.iloc[u_tu:u_den + 1]
                red = int((seg["close"] < seg["open"]).sum())
                green = int((seg["close"] > seg["open"]).sum())
                cond = red > green

            records.append((dur, norm_depth, cond, has_prev_up))

        if len(records) < 4:
            return None

        durs = np.array([r[0] for r in records], dtype=float)
        nds = np.array([r[1] for r in records], dtype=float)

        med_dur = float(np.median(durs))
        med_nd = float(np.median(nds))

        # "Nhọn" = ít phiên hơn trung vị và sâu hơn trung vị (đã chuẩn hoá ATR).
        sharp = (durs < med_dur) & (nds > med_nd)

        cond_all = np.array([r[2] for r in records], dtype=bool)
        eligible = np.array([r[3] for r in records], dtype=bool)

        if eligible.sum() < 4:
            return None

        cond_e = cond_all[eligible]
        sharp_e = sharp[eligible]

        n_events = int(cond_e.sum())
        if n_events < 30:
            return None

        observed = float(np.mean(sharp_e[cond_e]))

        return cond_e, sharp_e, observed, he

    he_candidates = (3.0, 2.5, 2.0, 1.5, 1.2, 1.0, 0.8, 0.6, 0.5)
    data = None
    he_used = None

    for he in he_candidates:
        data = _build(he)
        if data is not None:
            he_used = he
            break

    if data is None:
        return None

    cond_e, sharp_e, observed, _ = data
    n_events = int(cond_e.sum())
    n_eligible = int(len(cond_e))
    sharp_base = float(np.mean(sharp_e))

    n_perm = 2000
    perm_share = np.empty(n_perm, dtype=float)

    for b in range(n_perm):
        perm_cond = rng.permutation(cond_e)
        perm_share[b] = np.mean(sharp_e[perm_cond])

    null_mean = float(perm_share.mean())
    null_sd = float(perm_share.std(ddof=1))

    if null_sd > 0:
        thong_ke = (observed - null_mean) / null_sd
    else:
        thong_ke = 0.0

    # Một phía: xác suất "nhọn" cao hơn ngẫu nhiên.
    p = float((1 + np.sum(perm_share >= observed)) / (1 + n_perm))

    ghi_chu = (
        "Tự dựng đoạn từ chan_song bằng vi_tri/xac_nhan; hạ ngưỡng he_so "
        f"chỉ để đủ >=30 sự kiện (he_so={he_used:g}). "
        "Sự kiện: chân tăng có số nến đóng dưới mở > số nến đóng trên mở. "
        "Kết cục: chân giảm ngay sau đó nhọn = thời lượng < trung vị và độ sâu/ATR14 "
        "> trung vị. Hoán vị nhãn sự kiện giữ nguyên số sự kiện; p một phía."
    )

    return {
        "thong_ke": thong_ke,
        "p": p,
        "n": n_events,
        "quan_sat_tho": observed,
        "null_tb": null_mean,
        "null_sd": null_sd,
        "n_eligible": n_eligible,
        "sharp_base_rate": sharp_base,
        "he_so_chan": he_used,
        "ghi_chu": ghi_chu,
    }