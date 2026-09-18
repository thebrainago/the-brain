import numpy as np
import pandas as pd
import brain_co_che as bc


def _is_loai(r, loai):
    val = r['loai']
    if val is None:
        return False
    try:
        if pd.isna(val):
            return False
    except (TypeError, ValueError):
        pass
    s = str(val).strip().lower()
    if loai == 'cao':
        return s in ('1', '1.0', 'up', 'high', 'peak', 'dinh')
    return s in ('-1', '-1.0', 'down', 'low', 'bottom', 'day')


def do(khoa, df, rng):
    # Mac dinh: chan song 3xATR
    ch = bc.chan_song(df)
    if ch is None or len(ch) < 3:
        return None

    ch = ch.sort_values('vi_tri').reset_index(drop=True)

    events = []
    for i in range(1, len(ch) - 1):
        prev = ch.iloc[i - 1]
        cur = ch.iloc[i]
        nxt = ch.iloc[i + 1]

        # Chi xet: chan tang (low -> high) va chan giam tiep theo (high -> low)
        if not (_is_loai(prev, 'thap') and _is_loai(cur, 'cao') and _is_loai(nxt, 'thap')):
            continue

        L = int(prev['vi_tri'])
        H = int(cur['vi_tri'])
        N = int(nxt['vi_tri'])
        if not (L < H < N):
            continue

        up_amp = float(cur['gia']) - float(prev['gia'])
        down_amp = float(cur['gia']) - float(nxt['gia'])
        if up_amp <= 0 or down_amp <= 0:
            continue

        # Can it nhat 3 phien de chia 1/3
        n_up = H - L
        if n_up < 3:
            continue

        low_price = float(prev['gia'])
        high_price = float(cur['gia'])
        if low_price >= high_price:
            continue

        # Dung running max cua high de biet chan tang dat 50% bien do tu khi nao
        highs = df['high'].to_numpy(dtype=float)[L:H + 1]
        run_max = np.maximum.accumulate(highs)
        frac = (run_max - low_price) / (high_price - low_price)

        idx = np.where(frac >= 0.5)[0]
        if len(idx) == 0:
            continue

        t_star = L + int(idx[0])
        third = n_up // 3
        first_end = L + third
        last_start = H - third

        # Nhom som: dat 50% trong 1/3 dau cua chan tang
        # Nhom muon: dat 50% trong 1/3 cuoi cua chan tang
        if t_star <= first_end:
            group = 0  # som
        elif t_star >= last_start:
            group = 1  # muon
        else:
            continue

        # Outcome: chan giam tiep theo co bien do lon hon chan tang khong
        outcome = 1.0 if down_amp > up_amp else 0.0
        events.append((group, outcome))

    if len(events) < 30:
        return None

    labels = np.array([e[0] for e in events], dtype=int)
    outcomes = np.array([e[1] for e in events], dtype=float)

    late_mask = labels == 1
    early_mask = labels == 0
    n_late = int(late_mask.sum())
    n_early = int(early_mask.sum())
    if n_late < 5 or n_early < 5:
        return None

    rate_late = float(outcomes[late_mask].mean())
    rate_early = float(outcomes[early_mask].mean())
    obs = rate_late - rate_early

    # Hoan vi nhan som/muon, giu nguyen so luong moi nhom va outcome
    n_perm = 2000
    null = np.empty(n_perm, dtype=float)
    for b in range(n_perm):
        perm_labels = rng.permutation(labels)
        rl = outcomes[perm_labels == 1].mean()
        re = outcomes[perm_labels == 0].mean()
        null[b] = rl - re

    sd = float(null.std(ddof=0))
    if sd == 0:
        return None

    # Mot phia: ung ho "muon > som"
    p = float((np.sum(null >= obs) + 1) / (n_perm + 1))
    thong_ke = float((obs - null.mean()) / sd)

    return {
        'thong_ke': thong_ke,
        'p': p,
        'n': len(events),
        'quan_sat_tho': float(obs),
        'null_tb': float(null.mean()),
        'null_sd': sd,
        'ty_le_muon': rate_late,
        'ty_le_som': rate_early,
        'n_muon': n_late,
        'n_som': n_early,
        'de_xuat': 'Ghep dieu kien: ty le chan giam lon hon chan tang tang khi toc do tang tap trung ve cuoi chan; co the ket hop voi bien dong thap hoac pha dinh gan nhat.',
        'ghi_chu': (
            'Dung bc.chan_song(df) mac dinh (3xATR). '
            'Phan loai som/muon bang vi tri dau tien running high dat >=50% bien do chan tang: '
            '1/3 dau = som, 1/3 cuoi = muon. '
            'Outcome = 1 neu chan giam tiep theo co bien do lon hon chan tang do. '
            'Hoan vi nhan som/muon 2000 lan, giu so luong moi nhom va outcome. '
            'p mot phia cho gia thuyet ty_le_muon > ty_le_som.'
        ),
    }