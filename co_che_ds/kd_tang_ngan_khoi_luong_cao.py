import numpy as np
import pandas as pd
import brain_co_che as bc


def do(khoa, df, rng):
    if rng is None:
        rng = np.random.default_rng()
    elif not isinstance(rng, np.random.Generator):
        rng = np.random.default_rng(rng)

    close = df["close"].to_numpy(dtype=float)
    volume = df["volume"].to_numpy(dtype=float)

    try:
        atr_s = bc.atr(df, 14)
        if isinstance(atr_s, pd.DataFrame):
            atr_s = atr_s.iloc[:, 0]
        atr_arr = atr_s.ffill().to_numpy(dtype=float)
    except Exception:
        atr_arr = np.full(len(df), np.nan)

    def to_pos(x):
        if x is None:
            return -1
        try:
            if pd.isna(x):
                return -1
        except Exception:
            pass
        if isinstance(x, (int, np.integer)):
            return int(x)
        if isinstance(x, (float, np.floating)) and np.isfinite(x) and float(x).is_integer():
            return int(x)
        try:
            return int(df.index.get_loc(x))
        except Exception:
            try:
                return int(x)
            except Exception:
                return -1

    for he_so in (3.0, 2.0, 1.5, 1.0):
        try:
            ch = bc.chan_song(df, he_so=he_so)
        except Exception:
            continue
        if ch is None or len(ch) < 4:
            continue

        ch = ch.copy()
        ch["_pos"] = ch["vi_tri"].map(to_pos)
        ch = ch[ch["_pos"] >= 0]
        ch = ch.drop_duplicates("_pos").sort_values("_pos").reset_index(drop=True)
        ch["_gia"] = pd.to_numeric(ch["gia"], errors="coerce")
        m = ch["_gia"].isna()
        if m.any():
            ch.loc[m, "_gia"] = close[ch.loc[m, "_pos"].to_numpy(dtype=int)]

        price_map = dict(zip(ch["_pos"].to_numpy(), ch["_gia"].to_numpy()))

        def decode_point(x):
            p = to_pos(x)
            if p in price_map:
                return p, float(price_map[p])
            # Truong hop `tu` / `den` la chi so dong trong bang ch
            try:
                idx = int(x)
                if 0 <= idx < len(ch):
                    rp = int(ch.iloc[idx]["_pos"])
                    if rp in price_map:
                        return rp, float(price_map[rp])
            except Exception:
                pass
            return -1, np.nan

        try:
            seg = bc.cac_doan(df, ch)
        except Exception:
            continue
        if seg is None or len(seg) < 3:
            continue

        seg = seg.copy()

        tu_info = seg["tu"].map(decode_point)
        den_info = seg["den"].map(decode_point)

        seg["_tu"] = [x[0] for x in tu_info]
        seg["_den"] = [x[0] for x in den_info]
        seg["_gia_tu"] = [x[1] for x in tu_info]
        seg["_gia_den"] = [x[1] for x in den_info]

        seg = seg[
            (seg["_tu"] >= 0)
            & (seg["_den"] >= 0)
            & (seg["_tu"] < len(df))
            & (seg["_den"] < len(df))
            & (seg["_den"] > seg["_tu"])
            & np.isfinite(seg["_gia_tu"])
            & np.isfinite(seg["_gia_den"])
        ]
        if len(seg) < 3:
            continue

        seg["_huong"] = np.sign(
            seg["_gia_den"].to_numpy(dtype=float)
            - seg["_gia_tu"].to_numpy(dtype=float)
        )
        seg = seg[seg["_huong"] != 0]
        if len(seg) < 3:
            continue

        seg = seg.sort_values("_tu").reset_index(drop=True)

        ups = []
        for k, row in seg.iterrows():
            if row["_huong"] <= 0:
                continue
            i0 = int(row["_tu"])
            i1 = int(row["_den"])
            if i1 >= len(df):
                continue

            vol_sum = float(np.nansum(volume[i0 : i1 + 1]))
            span = float(row["_gia_den"] - row["_gia_tu"])

            atr0 = atr_arr[i0] if i0 < len(atr_arr) and np.isfinite(atr_arr[i0]) and atr_arr[i0] > 1e-12 else np.nan
            if not np.isfinite(atr0) or atr0 <= 0:
                atr0 = max(float(close[i0]) * 0.01, 1e-12)

            span_norm = span / atr0
            ups.append(
                {
                    "stt": k,
                    "tu": i0,
                    "den": i1,
                    "gia_tu": float(row["_gia_tu"]),
                    "gia_den": float(row["_gia_den"]),
                    "vol": vol_sum,
                    "span_norm": span_norm,
                }
            )

        if len(ups) < 3:
            continue

        X = []
        Y = []

        for j in range(1, len(ups)):
            prev = ups[j - 1]
            curr = ups[j]

            # Hai chan tang phai lien ke trong chuoi zigzag
            if curr["stt"] - prev["stt"] != 2:
                continue

            if curr["stt"] + 1 >= len(seg):
                continue

            nxt = seg.iloc[curr["stt"] + 1]
            if nxt["_huong"] >= 0:
                continue
            if int(nxt["_tu"]) != int(curr["den"]):
                continue
            if int(nxt["_den"]) >= len(df):
                continue

            cond = (curr["vol"] > prev["vol"]) and (
                curr["span_norm"] < prev["span_norm"]
            )

            # "Dong cua cua chan dieu chinh" = gia close tai bar tao day cua song dieu chinh
            outcome = float(close[int(nxt["_den"])]) < float(curr["gia_tu"])

            X.append(bool(cond))
            Y.append(bool(outcome))

        if len(X) < 30:
            continue

        Xa = np.asarray(X, dtype=bool)
        Ya = np.asarray(Y, dtype=bool)
        n = len(Xa)
        n_pos = int(Xa.sum())
        n_neg = n - n_pos

        if n_pos < 30 or n_neg < 10:
            continue

        obs = float(np.mean(Ya[Xa]) - np.mean(Ya))

        n_perm = 2000
        perms = np.empty(n_perm)
        for b in range(n_perm):
            Xp = rng.permutation(Xa)
            perms[b] = np.mean(Ya[Xp]) - np.mean(Ya)

        null_tb = float(np.mean(perms))
        null_sd = float(np.std(perms, ddof=1))
        if not np.isfinite(null_sd) or null_sd <= 0:
            continue

        thong_ke = (obs - null_tb) / null_sd

        if obs >= 0:
            p = float((np.sum(perms >= obs) + 1) / (n_perm + 1))
        else:
            p = float((np.sum(perms <= obs) + 1) / (n_perm + 1))

        return {
            "thong_ke": thong_ke,
            "p": p,
            "n": int(n),
            "quan_sat_tho": obs,
            "null_tb": null_tb,
            "null_sd": null_sd,
            "n_dieu_kien": int(n_pos),
            "xac_suat_dieu_kien": float(np.mean(Ya[Xa])),
            "xac_suat_nen": float(np.mean(Ya)),
            "nguong_chan": he_so,
            "ghi_chu": (
                "Dinh nghia: chan tang moi co tong volume cao hon VA bien do gia chuan hoa "
                "(span/ATR14 tai diem bat dau) ngan hon chan tang truoc. "
                "Bien so: close cua bar tao day cua chan dieu chinh tiep theo < gia diem bat dau chan tang do. "
                "p tu hoan vi nhan dieu kien giua cac bo ba song, giu nguyen so su kien va ty le nen. "
                f"He so zigzag da chon: {he_so}. thong_ke duong = ung ho khang dinh."
            ),
            "de_xuat": (
                "Co the thu ghep them dieu kien che do bien dong thap (std 20 ngay duoi phan vi 30%) "
                "de xem hieu ung co manh hon khong."
            ),
        }

    return None