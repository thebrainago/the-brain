# -*- coding: utf-8 -*-
"""suy_nguoc.py - SUY NGUOC: truoc mot cu di manh thi CO DAU HIEU GI.

Muc "Quantlab noi sinh" trong `SO_DO_HE_THONG.txt`:

    "Dao sau vao 1 cap tai san hoac tai san bang phuong phap suy nguoc, vi du
     nhu truoc 1 cu tang hay giam cua tai san A se co dau hieu gi, truoc 1 doan
     gia chay thang 1 trend se co dau hieu gi,... Nghia la quantlab phai tim
     duoc logic va tien hanh nghien cuu de tim edge"

Moi module khac di THUAN: co mot luat -> thu xem no ra tien khong. File nay di
NGUOC: lay KET CUC truoc (cu tang manh, doan trend), roi hoi **nhung bar ngay
truoc do khac gi voi bar binh thuong**.

KHONG PHAI `noi_sinh.py`. Hai file cung thuoc muc "Quantlab noi sinh" cua so do
nhung lam hai viec khac han:
    `noi_sinh.py`   SINH co che moi, lay NGUONG tu phan vi that cua chinh chuoi
    `suy_nguoc.py`  (file nay) di tu KET CUC ve DAU HIEU - khong sinh co che nao,
                    no tra loi "co cai gi bao truoc khong", va cau tra loi
                    "khong co gi" cung la mot cau tra loi dung.

## BA CHO DE HONG, VA CACH CHAN

**1. Su kien nhin ve TUONG LAI, dau hieu thi KHONG DUOC.** Su kien duoc dinh
nghia bang loi suat K bar TOI - dung, vi do la thu ta muon du bao. Nhung moi
DAU HIEU phai tinh duoc tai chinh bar do bang du lieu da dong. O day moi dau
hieu chi dung `close/high/low` den het bar `i`, va co mot bai kiem rieng cho
dieu do (`test_noi_sinh`).

**2. Null phai giu CUM.** Su kien khong rai deu - cu tang manh don cuc vao vai
giai doan. Xao tron nhan su kien mot cach doc lap se pha cum do va cho ra mot
null qua de, tuc cai gi cung thanh "phat hien". O day null la **XOAY VONG** mat
na su kien: giu nguyen ca hinh dang cum lan chuoi dau hieu, chi pha su khop
thoi gian giua hai cai.

**3. Mot tai san khong noi len gi.** Voi 10 dau hieu x 3 loai su kien = 30 phep
thu moi tai san, cai "manh nhat" tren MOT ma gan nhu chac chan la cuc tri ngau
nhien. Bo loc that o day la **DONG THUAN DA TAI SAN**: mot dau hieu dung tren
20/24 ma la mot quy luat; dung tren 1 ma la mot con so.

Chay:  python -m nhan.suy_nguoc [MA] [KHUNG]
       python -m nhan.suy_nguoc quet [KHUNG] [so_tien_trinh]
Ra:    reports/NOI_SINH.json
"""
from __future__ import annotations

import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

KHO = LAB / "reports" / "SUY_NGUOC.json"

#: Chan troi cua SU KIEN (so bar toi).
K_TOI = 10
#: Phan vi de goi la "cu di manh".
PHAN_VI = 90.0
#: So lan xoay vong de dung null.
SO_XOAY = 400
HAT = 20260912
BAR_TOI_THIEU = 800
#: Duoi so su kien nay thi khong ket luan gi.
SU_KIEN_TOI_THIEU = 30


# ------------------------------------------------------------------ DAU HIEU
def dau_hieu(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Cac dau hieu do tai bar i, CHI dung du lieu den het bar i.

    Moi chuoi tra ve dai bang df. NaN o dau la binh thuong (chua du cua so).
    """
    o = df["open"].to_numpy(float)
    h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float)
    c = df["close"].to_numpy(float)
    n = len(df)
    s = pd.Series(c)

    tr = np.maximum(h - l, np.maximum(np.abs(h - np.roll(c, 1)),
                                      np.abs(l - np.roll(c, 1))))
    tr[0] = h[0] - l[0]
    atr5 = pd.Series(tr).rolling(5).mean().to_numpy()
    atr20 = pd.Series(tr).rolling(20).mean().to_numpy()
    tb20 = s.rolling(20).mean().to_numpy()
    cao20 = pd.Series(h).rolling(20).max().to_numpy()
    thap20 = pd.Series(l).rolling(20).min().to_numpy()
    r = np.r_[np.nan, np.diff(np.log(np.maximum(c, 1e-12)))]

    with np.errstate(divide="ignore", invalid="ignore"):
        d = {
            # bien dong dang NEN hay DAN? < 1 la nen lai
            "nen_bien_dong": atr5 / atr20,
            # bien do cua chinh nen nay, chuan hoa
            "bien_do_nen": (h - l) / atr20,
            # dong cua o dau bien do ngay
            "ibs": (c - l) / np.maximum(h - l, 1e-12),
            # vi tri trong bien do 20 bar
            "vi_tri_20": (c - thap20) / np.maximum(cao20 - thap20, 1e-12),
            # cach trung binh bao nhieu ATR
            "xa_tb20": (c - tb20) / np.maximum(atr20, 1e-12),
            # do doc 20 bar, chuan hoa theo ATR
            "doc_20": (c - np.roll(c, 20)) / np.maximum(atr20, 1e-12),
            # than nen so voi ca bien do: nen dac hay nen rau
            "than_tren_bien": np.abs(c - o) / np.maximum(h - l, 1e-12),
        }
    d["doc_20"][:20] = np.nan

    # chuoi bar cung chieu lien tiep (dem nguoc tu bar i)
    dau = np.sign(c - o)
    chuoi = np.zeros(n)
    for i in range(1, n):
        chuoi[i] = chuoi[i - 1] + dau[i] if dau[i] == dau[i - 1] else dau[i]
    d["chuoi_cung_chieu"] = chuoi

    # tu tuong quan bac 1 cua loi suat trong 20 bar gan nhat
    ac = np.full(n, np.nan)
    for i in range(40, n):
        x = r[i - 19:i + 1]
        y = r[i - 20:i]
        if np.all(np.isfinite(x)) and np.all(np.isfinite(y)) and x.std() > 0 and y.std() > 0:
            ac[i] = float(np.corrcoef(x, y)[0, 1])
    d["ac1_20"] = ac

    # bien dong THUC HIEN 20 bar, chuan hoa boi bien dong 60 bar
    bd20 = pd.Series(r).rolling(20).std().to_numpy()
    bd60 = pd.Series(r).rolling(60).std().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        d["bd20_tren_bd60"] = bd20 / bd60
    return d


# ------------------------------------------------------------------ SU KIEN
def su_kien(df: pd.DataFrame, k_toi: int = K_TOI,
            phan_vi: float = PHAN_VI) -> dict[str, np.ndarray]:
    """Mat na su kien tai bar i = "trong k_toi bar TOI co chuyen gi".

    Su kien duoc phep nhin ve tuong lai - do la KET CUC ta muon du bao. Dau
    hieu thi khong.
    """
    c = df["close"].to_numpy(float)
    n = len(df)
    toi = np.full(n, np.nan)
    toi[:n - k_toi] = np.log(np.maximum(c[k_toi:], 1e-12)
                             / np.maximum(c[:n - k_toi], 1e-12))

    # hieu suat huong di: |tong| / tong|buoc| trong k_toi bar toi
    r = np.r_[np.nan, np.diff(np.log(np.maximum(c, 1e-12)))]
    tong_abs = pd.Series(np.abs(r)).rolling(k_toi).sum().shift(-k_toi).to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        hieu_suat = np.abs(toi) / np.maximum(tong_abs, 1e-12)

    tot = np.isfinite(toi)
    if tot.sum() < 50:
        return {}
    cao = np.nanpercentile(toi[tot], phan_vi)
    thap = np.nanpercentile(toi[tot], 100 - phan_vi)
    nguong_hs = np.nanpercentile(hieu_suat[np.isfinite(hieu_suat)], phan_vi)
    return {
        "cu_tang": tot & (toi >= cao),
        "cu_giam": tot & (toi <= thap),
        "chay_thang": np.isfinite(hieu_suat) & (hieu_suat >= nguong_hs),
    }


# -------------------------------------------------------------------- DO
def _xoay_null(mat_na: np.ndarray, x: np.ndarray, so_xoay: int,
               rng: np.random.Generator) -> np.ndarray:
    """Null bang XOAY VONG mat na su kien. Giu cum, pha su khop thoi gian."""
    n = len(mat_na)
    ra = np.empty(so_xoay)
    for j in range(so_xoay):
        k = int(rng.integers(1, n))
        ra[j] = np.nanmean(x[np.roll(mat_na, k)])
    return ra


def do_mot(df: pd.DataFrame, k_toi: int = K_TOI, so_xoay: int = SO_XOAY,
           hat: int = HAT) -> dict:
    dh = dau_hieu(df)
    sk = su_kien(df, k_toi)
    if not sk:
        return {"loi": "khong du bar de dinh nghia su kien"}
    rng = np.random.default_rng(hat)
    ra = {}
    for ten_sk, mat_na in sk.items():
        if int(mat_na.sum()) < SU_KIEN_TOI_THIEU:
            continue
        cua_no = {}
        for ten_dh, x in dh.items():
            tot = np.isfinite(x)
            mn = mat_na & tot
            if mn.sum() < SU_KIEN_TOI_THIEU:
                continue
            tb_sk = float(np.nanmean(x[mn]))
            tb_chung = float(np.nanmean(x[tot]))
            sd = float(np.nanstd(x[tot]))
            if not np.isfinite(sd) or sd <= 0:
                continue
            null = _xoay_null(mat_na & tot, np.where(tot, x, np.nan),
                              so_xoay, rng)
            null = null[np.isfinite(null)]
            if len(null) < 50:
                continue
            # p HAI PHIA tren chinh null xoay vong
            tv = float(np.median(null))
            vuot = (np.sum(null >= tb_sk) if tb_sk >= tv
                    else np.sum(null <= tb_sk))
            p = float((vuot + 1) / (len(null) + 1))
            cua_no[ten_dh] = {
                "tb_su_kien": round(tb_sk, 4),
                "tb_chung": round(tb_chung, 4),
                "lech_chuan": round((tb_sk - tb_chung) / sd, 4),
                "p_xoay": round(p, 4),
                "so_su_kien": int(mn.sum())}
        ra[ten_sk] = cua_no
    return ra


def quet_mot(ma: str, khung: str = "D1") -> dict:
    from nhan import du_lieu as DL
    try:
        df = DL.nap(ma, khung)
    except Exception as e:
        return {"ma": ma, "loi": "%s: %s" % (type(e).__name__, e)}
    if len(df) < BAR_TOI_THIEU:
        return {"ma": ma, "loi": "chi %d bar" % len(df)}
    d = do_mot(df)
    d["ma"], d["khung"], d["bar"] = ma, khung, len(df)
    return d


def _mot(args):
    return quet_mot(*args)


#: Manh den dau moi goi la "co dau hieu". |lech_chuan| - khong dung p lam nguong
#: chinh: voi 400 lan xoay, p nho nhat co the la 1/401, va nhieu dau hieu se
#: cham san do cung luc. Do LON cua chenh lech moi la thu hanh dong duoc.
NGUONG_LECH = 0.20
NGUONG_P = 0.05
#: p cua phep thu DAU GOP de goi la dong thuan that.
NGUONG_P_GOP = 0.001


def p_dau_gop(cung_dau: int, so_ma: int) -> float:
    """p mot phia cua phep thu nhi thuc tren DAU, gia thiet null 50/50.

    VI SAO CAN (12/09/2026): nguong `dat` o tren doi TUNG MA phai dat y nghia
    rieng, va luc cua mot ma la rat yeu - tot nhat chi 54/154 ma dat. Nhin cot
    do thi ket luan la "khong co gi".

    Nhung cot CUNG DAU noi khac han: `bien_do_nen` truoc `cu_tang` cung dau o
    **88% cua 154 ma**. Moi ma mot phep thu yeu, nhung 136/154 cung huong thi
    phep thu GOP rat manh. Do la dung cach doc mot bang da tai san: suc manh
    nam o su LAP LAI, khong o tung o.

    CANH BAO PHAI DOC KEM: cac ma KHONG doc lap (307 cap co |r| >= 0,7 tren D1).
    p nay la CHAN DUOI lac quan. `so_ma_doc_lap` uoc luong so ma thuc su doc
    lap de doi chieu.
    """
    from math import lgamma, log, exp
    n, k = int(so_ma), int(cung_dau)
    if n <= 0 or k <= 0:
        return 1.0
    # Cong trong KHONG GIAN LOG. Tinh thang bang `comb` roi chia 2**n thi voi
    # n = 154 ket qua tran so duoi ve dung 0,0 - va "p = 0" la mot con so sai,
    # no noi "khong the xay ra" thay vi "nho hon muc bieu dien duoc".
    def _log_c(n_, i_):
        return lgamma(n_ + 1) - lgamma(i_ + 1) - lgamma(n_ - i_ + 1)

    cac = [_log_c(n, i) - n * log(2.0) for i in range(k, n + 1)]
    m = max(cac)
    log_duoi = m + log(sum(exp(x - m) for x in cac))
    log_p = log(2.0) + log_duoi
    return max(exp(log_p), 1e-300) if log_p > -690 else 1e-300


def so_ma_doc_lap(khung: str = "D1") -> int | None:
    """Uoc luong so ma DOC LAP, doc tu ho so tuong quan da co.

    Khong co ho so thi tra None - khong doan. Cach uoc: tru di moi ma bi mot ma
    khac giai thich gan het (|r| >= 0,7).
    """
    try:
        from nhan import ho_so_tuong_quan as TQ
        d = TQ.doc(khung)
        cap = d.get("cap") or {}
        ho = d.get("ho_so") or {}
        if not ho:
            return None
        bi_giai_thich = set()
        for k, v in cap.items():
            if abs(float(v.get("r", 0))) < 0.7 or "|" not in k:
                continue
            a, b = k.split("|", 1)
            if a not in bi_giai_thich:
                bi_giai_thich.add(b)
        return max(len(ho) - len(bi_giai_thich), 1)
    except Exception:
        return None


def quet(cac_ma=None, khung: str = "D1", so_tien_trinh: int = 10,
         in_ra=print) -> dict:
    from nhan import ho_so_symbol as HSS
    if cac_ma is None:
        hs = HSS.doc()
        if isinstance(hs, dict):
            hs = list(hs.values())
        cac_ma = sorted({str(x.get("ma")) for x in hs
                         if isinstance(x, dict) and x.get("ma")})
    t0 = time.time()
    with Pool(so_tien_trinh) as pool:
        kq = pool.map(_mot, [(m, khung) for m in cac_ma], chunksize=1)
    tot = [k for k in kq if "loi" not in k]
    in_ra("quet %d/%d ma trong %.0fs" % (len(tot), len(cac_ma), time.time() - t0))

    # DONG THUAN DA TAI SAN - bo loc that
    gop: dict[tuple, list] = {}
    for k in tot:
        for ten_sk, cua_no in k.items():
            if not isinstance(cua_no, dict):
                continue
            for ten_dh, v in cua_no.items():
                if not isinstance(v, dict):
                    continue
                gop.setdefault((ten_sk, ten_dh), []).append(v)
    bang = []
    for (sk, dh), ds in gop.items():
        lech = np.array([x["lech_chuan"] for x in ds])
        dat = [x for x in ds
               if abs(x["lech_chuan"]) >= NGUONG_LECH and x["p_xoay"] <= NGUONG_P]
        cung_dau = int(max(np.sum(lech > 0), np.sum(lech < 0)))
        bang.append({
            "su_kien": sk, "dau_hieu": dh, "so_ma": len(ds),
            "lech_trung_vi": round(float(np.median(lech)), 4),
            "dat": len(dat), "cung_dau": cung_dau,
            "ty_le_cung_dau": round(cung_dau / max(len(ds), 1), 3),
            "p_dau_gop": p_dau_gop(cung_dau, len(ds)),
            "so_ma_doc_lap": so_ma_doc_lap(khung)})
    bang.sort(key=lambda d: (d["p_dau_gop"], -abs(d["lech_trung_vi"])))

    ket = {"khung": khung, "so_ma": len(tot), "k_toi": K_TOI,
           "giay": round(time.time() - t0, 1), "bang": bang,
           "chi_tiet": {k["ma"]: k for k in tot[:60]}}
    KHO.parent.mkdir(exist_ok=True)
    KHO.write_text(json.dumps(ket, ensure_ascii=False, indent=1, default=float),
                   encoding="utf-8")
    _in(ket, in_ra)
    return ket


def _in(ket: dict, in_ra=print) -> None:
    in_ra("")
    in_ra("DAU HIEU TRUOC SU KIEN - %d ma, khung %s, chan troi %d bar"
          % (ket["so_ma"], ket["khung"], ket["k_toi"]))
    in_ra("%-13s %-18s %5s %9s %6s %9s %12s"
          % ("SU KIEN", "DAU HIEU", "MA", "LECH TV", "DAT", "CUNG DAU", "p DAU GOP"))
    for d in ket["bang"][:22]:
        in_ra("%-13s %-18s %5d %9.3f %6d %8.0f%% %12.2e"
              % (d["su_kien"], d["dau_hieu"], d["so_ma"], d["lech_trung_vi"],
                 d["dat"], d["ty_le_cung_dau"] * 100, d["p_dau_gop"]))
    doc_lap = next((d.get("so_ma_doc_lap") for d in ket["bang"]), None)
    manh = [d for d in ket["bang"] if d["p_dau_gop"] <= NGUONG_P_GOP]
    in_ra("")
    if manh:
        in_ra("DAU HIEU DONG THUAN DA TAI SAN (p dau gop <= %g):" % NGUONG_P_GOP)
        for d in manh[:10]:
            in_ra("  truoc %-12s thi %-18s %s %.3f do lech chuan"
                  % (d["su_kien"], d["dau_hieu"],
                     "CAO hon" if d["lech_trung_vi"] > 0 else "THAP hon",
                     abs(d["lech_trung_vi"])))
            in_ra("      %d/%d ma cung dau, %d ma dat rieng le"
                  % (d["cung_dau"], d["so_ma"], d["dat"]))
        in_ra("")
        in_ra("  DOC KEM: cac ma KHONG doc lap nen p tren la CHAN DUOI lac quan."
              + ("" if doc_lap is None else
                 " Uoc so ma doc lap: ~%d." % doc_lap))
        in_ra("  Va do lech chi vai phan tram do lech chuan - do la mot XU HUONG")
        in_ra("  co that, khong phai mot tin hieu giao dich duoc ngay.")
    else:
        in_ra("KHONG dau hieu nao dong thuan tren da tai san. Do la ket qua - "
              "no noi rang cac 'dau hieu bao truoc' o day khong chung.")
    in_ra("")
    in_ra("-> %s" % KHO)


def doc() -> dict:
    try:
        return json.loads(KHO.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main(argv: list[str]) -> int:
    if argv and argv[0] == "quet":
        quet(khung=argv[1] if len(argv) > 1 else "D1",
             so_tien_trinh=int(argv[2]) if len(argv) > 2 else 10)
        return 0
    ma = argv[0] if argv else "EURUSD"
    khung = argv[1] if len(argv) > 1 else "D1"
    print(json.dumps(quet_mot(ma, khung), ensure_ascii=False, indent=1,
                     default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
