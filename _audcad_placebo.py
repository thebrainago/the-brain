# -*- coding: utf-8 -*-
"""_audcad_placebo.py - 8 cum AUDCAD co edge THAT hay chi la o trong thi truong?

Chu du an 15/09/2026: *"khong con gi nghien cuu hay can lam nua a? neu co thi
hay trien khai luon."* Cai con lai quan trong nhat truoc khi danh live: PLACEBO.

## Cau hoi placebo tra loi

Moi cum lai +X% tren holdout. Nhung X do den tu TIMING (vao dung luc RSI cham
cuc tri = edge that) hay chi vi O TRONG THI TRUONG (phoi nhiem, bat ky luc nao
cung the)? Neu la cai sau thi 27%/nam la ao giac.

## NULL DUNG: HOAN VI CHUOI VI THE, khong sinh tin hieu moi

[[v6-doi-chieu-dung-cach]] va bai hoc da chot: **placebo phai hoan vi CHUOI VI
THE, khong phai chuoi lai/lo**. Hoan vi lai/lo giu nguyen phan phoi nen luon ra
~50% - no se "ket luan" moi he deu truot.

O day: giu nguyen chuoi loi suat GIA, HOAN VI theo KHOI cac vi the (giu nguyen
ty le o trong thi truong va cau truc tu tuong quan cua vi the, chi tach TIMING
khoi gia). Neu lai that nam trong top 5% cua phan phoi null -> timing that su
mang thong tin -> edge that.

Khoi = do dai giu lenh trung binh cua cum (de khong pha vo cau truc "vao roi
giu N bar").

Chay:  python _audcad_placebo.py [--n 2000]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

_KHUNG = (sys.argv[sys.argv.index("--khung")+1] if "--khung" in sys.argv else "H4")
_MA = (sys.argv[sys.argv.index("--ma")+1] if "--ma" in sys.argv else "AUDCAD")
TU, DEN = "2021-03-19", "2026-07-29"
#: Chi phi mot vong (vao+ra) theo bps - spread AUDCAD ~1 bps + truot. Dung de
#: null va that CUNG chiu, khong lam lech phep so sanh.
CHI_PHI_BPS = 1.5


def _pnl(pos: np.ndarray, ret: np.ndarray) -> float:
    """Lai tich luy: vi the bar t huong loi suat gia bar t+1, tru chi phi khi
    vi the DOI (mo/dong/dao)."""
    n = min(len(pos), len(ret) - 1)
    lai = float(np.sum(pos[:n] * ret[1:n + 1]))
    doi = np.abs(np.diff(np.concatenate([[0.0], pos[:n]])))
    phi = float(np.sum(doi) * CHI_PHI_BPS * 1e-4)
    return lai - phi


def _khoi_hoan_vi(pos: np.ndarray, khoi: int, rng) -> np.ndarray:
    """Cat pos thanh cac khoi do dai `khoi`, xao thu tu khoi. Giu nguyen NOI
    DUNG tung khoi (cau truc vao-giu-ra) nhung tach no khoi vi tri thoi gian."""
    n = len(pos)
    k = max(1, int(khoi))
    cac = [pos[i:i + k] for i in range(0, n, k)]
    rng.shuffle(cac)
    ra = np.concatenate(cac)
    return ra[:n]


def main() -> int:
    from nhan import du_lieu as DL
    from nhan import ngu_phap as NP

    n_null = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 2000
    d = json.loads((LAB / "reports" / ("CUM_%s_%s.json" % (_MA,_KHUNG))).read_text(encoding="utf-8"))
    ten = [c["dai_dien"] for c in d["cum"]]
    kho = {c.get("ten"): c for c in NP.doc_kho()}
    df = DL.nap(_MA, _KHUNG, tu=TU, den=DEN)
    c = df["close"].to_numpy(float)
    ret = np.concatenate([[0.0], np.diff(np.log(c))])   # loi suat log tung bar
    rng = np.random.default_rng(0)

    print("=" * 74)
    print("PLACEBO 8 CUM AUDCAD H4 (holdout, %d null moi cum)" % n_null)
    print("=" * 74)
    print("Null = HOAN VI KHOI chuoi vi the (giu phoi nhiem, tach timing).")
    print("p = ty le null >= that. p nho -> timing mang thong tin -> edge that.\n")

    print("%-42s %9s %8s %8s %s" % ("cum", "lai that", "null tv", "p", ""))
    print("-" * 74)
    ps, pos_ds = [], []
    for t in ten:
        spec = kho.get(t)
        if spec is None:
            continue
        pos = np.nan_to_num(np.asarray(NP.sinh_tu_spec(spec, df), float))
        pos_ds.append(pos)
        that = _pnl(pos, ret)
        # do dai giu trung binh -> kich thuoc khoi
        trong = (np.abs(pos) > 0).astype(int)
        doi = np.sum(np.abs(np.diff(trong)))
        giu_tb = max(2, int(trong.sum() / max(doi / 2, 1)))
        null = np.array([_pnl(_khoi_hoan_vi(pos, giu_tb, rng), ret)
                         for _ in range(n_null)])
        p = float(np.mean(null >= that))
        ps.append(p)
        print("%-42s %+9.4f %+8.4f %8.4f %s"
              % (t[:42], that, float(np.median(null)), p,
                 "<- edge" if p < 0.05 else ""))

    # --- DANH MUC: cong deu 8 cum, placebo tren tong ---
    n = min(len(x) for x in pos_ds)
    tong_pos = np.sum([x[:n] for x in pos_ds], axis=0)
    that_dm = _pnl(tong_pos, ret)
    giu_dm = max(2, int((np.abs(tong_pos) > 0).sum() /
                        max(np.sum(np.abs(np.diff((np.abs(tong_pos) > 0).astype(int)))) / 2, 1)))
    # Null danh muc: hoan vi DONG BO ca 8 chuoi cung mot cach xao (giu tuong
    # quan giua cac cum), roi cong. Do la null dung cho danh muc.
    null_dm = []
    for _ in range(n_null):
        r2 = np.random.default_rng(rng.integers(1 << 30))
        idx = None
        s = np.zeros(n)
        # xao KHOI dong bo: cung hoan vi cho moi cum
        k = giu_dm
        cac_i = list(range(0, n, k))
        r2.shuffle(cac_i)
        for x in pos_ds:
            xn = x[:n]
            gh = np.concatenate([xn[i:i + k] for i in cac_i])[:n]
            s = s + gh
        null_dm.append(_pnl(s, ret))
    null_dm = np.array(null_dm)
    p_dm = float(np.mean(null_dm >= that_dm))

    print("-" * 74)
    print("%-42s %+9.4f %+8.4f %8.4f %s"
          % ("*** DANH MUC (8 cum) ***", that_dm, float(np.median(null_dm)),
             p_dm, "<- EDGE" if p_dm < 0.05 else "<- KHONG qua"))
    dat = sum(1 for p in ps if p < 0.05)
    print("\n%d/%d cum qua placebo (p<0,05). Danh muc p = %.4f."
          % (dat, len(ps), p_dm))
    if p_dm >= 0.05:
        print("=> DANH MUC KHONG qua placebo: lai den tu O TRONG THI TRUONG,")
        print("   khong tu timing. 27%/nam la ao giac - DUNG danh live.")
    elif dat < len(ps) / 2:
        print("=> Danh muc qua nhung <1/2 cum qua rieng: edge tap trung o vai")
        print("   cum, phan con lai la phoi nhiem. Chi giu cum qua placebo.")
    else:
        print("=> Phan lon cum co timing that su mang thong tin. Edge co that,")
        print("   trong pham vi mot tai san mot khung mot cua so.")

    ra = LAB / "reports" / ("PLACEBO_%s_%s.json" % (_MA,_KHUNG))
    ra.write_text(json.dumps(
        {"n_null": n_null, "p_danh_muc": p_dm, "cum_qua": dat, "so_cum": len(ps),
         "p_tung_cum": {t: p for t, p in zip(ten, ps)}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n-> %s" % ra.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
