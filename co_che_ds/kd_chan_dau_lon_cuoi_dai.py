import numpy as np
import pandas as pd
import brain_co_che as bc


def _dir_key(h):
    if h is None:
        return 0
    try:
        if pd.isna(h):
            return 0
    except (TypeError, ValueError):
        pass

    if isinstance(h, str):
        s = h.strip().lower()
        if s in ("up", "len", "duong", "mua", "long", "tang", "tăng", "bull", "1", "1.0", "+1"):
            return 1
        if s in ("down", "xuong", "xuống", "am", "ban", "short", "giam", "giảm", "bear", "-1", "-1.0"):
            return -1
        return 0

    try:
        v = float(h)
        if v > 0:
            return 1
        if v < 0:
            return -1
    except (TypeError, ValueError):
        pass
    return 0


def _legs_sorted(df, ch):
    dd = bc.cac_doan(df, ch)
    if dd is None or len(dd) == 0:
        return []

    dd = dd.copy()

    sort_col = None
    for col in ("biet_tai", "xac_nhan", "den", "tu"):
        if col in dd.columns:
            sort_col = col
            break

    if sort_col is not None:
        try:
            dd = dd.sort_values(sort_col, kind="mergesort")
        except Exception:
            dd = dd.sort_index()
    else:
        dd = dd.sort_index()

    legs = []
    for _, r in dd.iterrows():
        k = _dir_key(r.get("huong"))
        if k == 0:
            continue
        try:
            amp = abs(float(r["do_dai"]))
            dur = abs(float(r["thoi_luong"]))
        except (TypeError, ValueError, KeyError):
            continue
        if not (np.isfinite(amp) and np.isfinite(dur)) or amp <= 0 or dur <= 0:
            continue
        legs.append({"dir": k, "amp": amp, "dur": dur})

    return legs


def _non_overlap_triplets(legs):
    tri = []
    for d in (1, -1):
        seq = [leg for leg in legs if leg["dir"] == d]
        for i in range(0, len(seq) - 2, 3):
            tri.append((seq[i], seq[i + 1], seq[i + 2]))
    return tri


def do(khoa, df, rng):
    ch = bc.chan_song(df)
    legs = _legs_sorted(df, ch)
    tri = _non_overlap_triplets(legs)

    if len(tri) < 30:
        return None

    n = len(tri)
    A = np.zeros(n, dtype=bool)  # dieu kien: chan dau co bien do lon nhat
    B = np.zeros(n, dtype=bool)  # ket cuc: chan cuoi co thoi luong dai nhat

    for i, (a, b, c) in enumerate(tri):
        if a["amp"] > b["amp"] and a["amp"] > c["amp"]:
            A[i] = True
        if c["dur"] > a["dur"] and c["dur"] > b["dur"]:
            B[i] = True

    m_A = int(A.sum())
    m_B = int(B.sum())

    if m_A < 30 or m_B < 30:
        return None

    quan_sat_tho = float((A & B).sum()) / m_A

    n_perm = 2000
    perm_stats = np.empty(n_perm)

    for i in range(n_perm):
        PA = rng.permutation(A)
        perm_stats[i] = float((PA & B).sum()) / m_A

    null_tb = float(perm_stats.mean())
    null_sd = float(perm_stats.std(ddof=1))

    if null_sd == 0 or not np.isfinite(null_sd):
        return None

    thong_ke = (quan_sat_tho - null_tb) / null_sd
    p = float((perm_stats >= quan_sat_tho).mean())

    return {
        "thong_ke": thong_ke,
        "p": p,
        "n": m_A,
        "quan_sat_tho": quan_sat_tho,
        "null_tb": null_tb,
        "null_sd": null_sd,
        "xac_suat_nen": float(B.mean()),
        "so_bo_ba": n,
        "so_dieu_kien": m_A,
        "so_ket_cuc": m_B,
        "ghi_chu": (
            "Bo ba = 3 song cung huong lien tiep, lay khong chong lap rieng cho huong len va xuong; "
            "bo ba duoc chot tai thoi diem song thu ba xac nhan. "
            "Dieu kien: bien do song 1 > song 2 va song 3 (nghiem ngat). "
            "Ket cuc: thoi luong song 3 > song 1 va song 2 (nghiem ngat). "
            "Thong ke la P(ket cuc | dieu kien) so voi nen P(ket cuc), va duoc neo vao phan phoi hoan vi. "
            "Hoan vi nhan dieu kien giua cac bo ba, giu nguyen so bo ba co dieu kien va so bo ba co ket cuc, "
            "nen bao toan phoi nhiem va ty le nen. "
            "Khong dung thong tin sau khi bo ba hoan thanh; khong dat nguong theo thong ke ca chuoi. "
            "Thuc do dung thu hang noi bo trong bo ba nen it bi volatility clustering lam sai lech scale."
        ),
        "de_xuat": (
            "Neu ket qua duong, co the ghep them dieu kien ATR thap hoac xu huong chinh "
            "de kiem tra co che 'nha dau tu vao sau bi ep phai cho dieu chinh' ro hon."
        ),
    }