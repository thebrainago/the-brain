import numpy as np
import pandas as pd  # noqa: F401  (thuong duoc dung boi bc)
import brain_co_che as bc


def do(khoa, df, rng):
    # ------------------------------------------------------------
    # 1. Dung bo tim chan/doan co san, khong tu viet de tranh nhin truoc
    # ------------------------------------------------------------
    ch = bc.chan_song(df)  # mac dinh nguong 3xATR
    if ch is None or len(ch) < 3:
        return None

    doan = bc.cac_doan(df, ch)
    if doan is None or len(doan) < 40:
        return None

    df_len = len(df)
    close = df['close'].values

    # ------------------------------------------------------------
    # 2. Loc cac doan co du 5 phien sau, va co ATR tai diem xac nhan
    # ------------------------------------------------------------
    try:
        biet_tai = doan['biet_tai'].values.astype(int)
    except Exception:
        return None

    valid = (biet_tai + 5 < df_len) & (biet_tai >= 14)
    doan = doan[valid].copy()
    if len(doan) < 40:
        return None

    biet_tai = doan['biet_tai'].values.astype(int)

    # ------------------------------------------------------------
    # 3. Xac dinh huong cua doan (giam = True)
    # ------------------------------------------------------------
    huong = doan['huong'].values
    if huong.dtype.kind in 'USO':  # string/object
        huong_str = np.array([str(h).strip().lower() for h in huong])
        is_giam = np.isin(huong_str, ['down', 'giam', 'd', '-1', '0', 'sell'])
    else:
        is_giam = huong.astype(float) < 0

    # Neu cot huong khong dung, thu suy ra tu gia tai hai chan
    if is_giam.sum() == 0 or (~is_giam).sum() == 0:
        try:
            tu = doan['tu'].values.astype(int)
            den = doan['den'].values.astype(int)
            is_giam = close[den] < close[tu]
        except Exception:
            return None

    if is_giam.sum() == 0 or (~is_giam).sum() == 0:
        return None

    # ------------------------------------------------------------
    # 4. Do bien dong 5 phien sau da chuan hoa theo bien do chan (luat 4)
    # ------------------------------------------------------------
    try:
        bien_do = np.abs(doan['do_dai'].values.astype(float))
    except Exception:
        return None
    if np.any(bien_do <= 0):
        return None

    # Bien dong = trung binh |close[i] - close[i-1]| trong 5 phien sau xac nhan
    idx = biet_tai[:, None] + np.arange(0, 6)          # 6 moc de co 5 cua so
    vals = close[idx]
    bien_dong = np.abs(np.diff(vals, axis=1)).sum(axis=1) / 5.0

    # Chuan hoa theo bien do cua chan (luat 4)
    bien_dong_chuan = bien_dong / bien_do

    # ------------------------------------------------------------
    # 5. Loc "bien do lon" bang ATR tai diem xac nhan; ha dan nguong
    #    chi theo SO MAU, khong theo ket qua
    # ------------------------------------------------------------
    try:
        atr_vals = bc.atr(df, 14).to_numpy().ravel()
    except Exception:
        atr_vals = np.asarray(bc.atr(df, 14)).ravel()

    atr_tai = atr_vals[biet_tai]

    he_so_chon = None
    values, labels, bien_do_used = None, None, None

    for he_so in [1.5, 1.0, 0.75, 0.5, 0.25]:
        mask = (
            np.isfinite(bien_dong_chuan)
            & np.isfinite(atr_tai)
            & (bien_do >= he_so * atr_tai)
        )
        if mask.sum() < 30:
            continue
        n_giam = int(is_giam[mask].sum())
        n_tang = int((~is_giam[mask]).sum())
        if n_giam >= 30 and n_tang >= 30:
            he_so_chon = he_so
            values = bien_dong_chuan[mask]
            labels = is_giam[mask]
            bien_do_used = bien_do[mask]
            break

    # Neu van khong du, thu khong loc nguong (cac chan tu chan_song da la "lon")
    if he_so_chon is None:
        mask = np.isfinite(bien_dong_chuan)
        if mask.sum() < 30:
            return None
        n_giam = int(is_giam[mask].sum())
        n_tang = int((~is_giam[mask]).sum())
        if n_giam >= 30 and n_tang >= 30:
            he_so_chon = 0.0
            values = bien_dong_chuan[mask]
            labels = is_giam[mask]
            bien_do_used = bien_do[mask]
        else:
            return None

    # ------------------------------------------------------------
    # 6. Thong ke quan sat: trung binh(nhom giam) - trung binh(nhom tang)
    # ------------------------------------------------------------
    quan_sat = values[labels].mean() - values[~labels].mean()

    # ------------------------------------------------------------
    # 7. Hoan vi: giu nguyen so su kien va ty le giam/tang (luat 2)
    # ------------------------------------------------------------
    n_perm = 2000
    n = len(values)
    perm_diffs = np.empty(n_perm)

    for i in range(n_perm):
        idx_perm = rng.permutation(n)
        perm_labels = labels[idx_perm]  # cung so True/giam
        perm_diff = values[perm_labels].mean() - values[~perm_labels].mean()
        perm_diffs[i] = perm_diff

    null_tb = float(perm_diffs.mean())
    null_sd = float(perm_diffs.std())
    if null_sd == 0:
        return None

    # Neu quan sat duong -> ung ho khang dinh
    thong_ke = (quan_sat - null_tb) / null_sd
    p = float((1 + np.sum(np.abs(perm_diffs) >= np.abs(quan_sat))) / (n_perm + 1))

    # ------------------------------------------------------------
    # 8. Dong goi ket qua
    # ------------------------------------------------------------
    n_giam = int(labels.sum())
    n_tang = int((~labels).sum())

    ghi_chu = (
        f"Doan lay tu bc.chan_song mac dinh (3xATR). "
        f"Bien dong 5 phien sau = trung binh |close[i]-close[i-1]| tu biet_tai+1 den biet_tai+5, "
        f"chia cho do_dai cua chan (luat 4). "
        f"Loc theo nguong do_dai >= {he_so_chon}*ATR(biet_tai); ha nguong chi theo so mau, khong theo ket qua. "
        f"Hoan vi nhan giam/tang 2000 lan, giu nguyen so luong moi nhom. "
        f"thong_ke duong = ung ho khang dinh (bien dong sau chan giam cao hon chan tang)."
    )
    if he_so_chon == 0.0:
        ghi_chu = ghi_chu.replace(
            f"Loc theo nguong do_dai >= 0.0*ATR(biet_tai); ",
            "Khong loc them theo ATR; "
        )

    res = {
        'thong_ke': float(thong_ke),
        'p': p,
        'n': n,
        'quan_sat_tho': float(quan_sat),
        'null_tb': null_tb,
        'null_sd': null_sd,
        'n_giam': n_giam,
        'n_tang': n_tang,
        'bien_do_tb_giam': float(bien_do_used[labels].mean()),
        'bien_do_tb_tang': float(bien_do_used[~labels].mean()),
        'bien_dong_tb_giam': float(values[labels].mean()),
        'bien_dong_tb_tang': float(values[~labels].mean()),
        'he_so_nguong': he_so_chon,
        'ghi_chu': ghi_chu,
    }

    if p < 0.05:
        res['de_xuat'] = (
            "Bien dong sau chan giam co ve cao hon chan tang cung bien do; "
            "co the dung lam tin hieu canh bao risk khi gap pha vo xuong."
        )

    return res