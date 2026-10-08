# -*- coding: utf-8 -*-
"""kiem_do_phan_giai.py - DO LECH DO PHAN GIAI BAR cua engine luoi (08/10/2026).

Cau hoi: cung MOT duong gia, engine chay tren nen M1 / M5 / M15 cho ket qua khac chay TUNG TICK bao nhieu?

Cach do (khong du lieu that, khong chi phi, khong drift): random walk 1 tick / giay. Tren duong gia khong drift, khong chi phi thi
ky vong ket qua THAT cua moi luat luoi = 0 (khong co canh tranh de an), nen bat ky khoang cach he thong nao giua "chay tren nen" va
"chay tung tick" (cung duong, GHEP DOI theo hat giong) la LECH CUA MO HINH BAR, khong phai canh tranh.
  - MOC (su that): `cuc_tri` chay tren tung tick (moi tick la mot nen suy bien hi = lo = cl). Voi tick nho hon nguong chot / buoc luoi
    nhieu lan thi khong co nhap nhang thu tu, nen mo hinh nao cung ra cung mot ket qua: day la su kien xay ra theo duong gia thang
    tung doan, khop o GIA NGUONG (lenh gioi han).
  - Hai mo hinh duoc do: `cuc_tri` (ban cu) va `duong_di` (mac dinh), tren nen gop k tick (k = 60 / 300 / 900 ~ M1 / M5 / M15).
  - Tu nhat: `duong_di` chay tren tung DOAN tick (nen hi/lo = hai tick lien tiep) phai ra y het MOC (xem `kiem_tu_nhat`).

Ket qua mau (2 ngay x 16 hat, `python -m nhan.kiem_do_phan_giai`): `cuc_tri` lech them ~+11 / +58 / +184 o k = 60 / 300 / 900 voi cau
hinh tia lenh va TANG theo khung (cau hinh khong tia gan nhu khong lech: +0 / +4 / +18); `duong_di` ~ +1 / +1 / -7 (sai so chuan 2-3),
tuc la het lech do phan giai tren du lieu tong hop. KHONG chung minh duoc gi ve swap, cau truc tick that, open that - chi la
phan DO PHAN GIAI BAR.

Dung: `python -m nhan.kiem_do_phan_giai [--ngay 2] [--hat 16] [--k 60,300,900] [--cau-hinh tia,chot_tien]`.
"""
from __future__ import annotations

import argparse
import sys
import time

import numpy as np
import pandas as pd

from nhan import luoi as L

#: Quy cach tong hop: 1 pip = 1e-4, hop dong 100.000, khong phi, khong spread (chi do hinh hoc khop lenh).
QC_TONG_HOP = L.QuyCach(ma="SYN", pip=1e-4, hop_dong=100_000.0, point=1e-5, phi_nam_mua=0.0, phi_nam_ban=0.0,
                        spread_du_phong=0.0, von_quy_doi=1.0, do_tin="SAN")

_GOC = dict(buoc=6.0, tp=5.0, tran_tang=6, che_do="hai_chieu", lot=0.01)
#: Cau hinh mau: cai nao co tia lenh / cho lui / chot theo tien / lot nhan la cai khop lenh trong bar anh huong nhieu nhat.
CAU_HINH_MAU = {
    "khong_tia": dict(_GOC),
    "tia": dict(_GOC, tia_lenh=True, bien_cap=3.0),
    "cho_lui": dict(_GOC, cho_lui=4.0),
    "chot_tien": dict(_GOC, chot_tien=0.4),
    "tia_cho_lui": dict(_GOC, tia_lenh=True, bien_cap=3.0, cho_lui=3.0),
    "nhan_lot": dict(buoc=5.0, tp=4.0, tran_tang=5, che_do="hai_chieu", lot=0.01, kieu_lot="nhan", he_so_lot=1.3,
                     tia_lenh=True, bien_cap=2.0),
}
KHUNG_MAC_DINH = (60, 300, 900)
VON = 1e12                                                    # du lon de khong bao gio stop-out: chi do khop lenh


def duong_gia(seed: int, ngay: float, sigma_pip: float = 0.25, gia0: float = 1.45) -> np.ndarray:
    """Random walk thuan, MOT tick moi giay (sigma 0,25 pip/tick ~ 73 pip/ngay, nhu cap FX thuong). Tra mang (n + 1,)."""
    rng = np.random.default_rng(seed)
    n = int(round(ngay * 86400))
    return gia0 + np.concatenate([[0.0], np.cumsum(rng.normal(0.0, sigma_pip * 1e-4, n))])


def nen_diem(p: np.ndarray):
    """MOC su that: moi tick la mot nen suy bien (hi = lo = cl)."""
    return p, p, p


def nen_doan(p: np.ndarray):
    """Moi nen la mot DOAN thang giua hai tick lien tiep (hi/lo = hai dau mut), nen mo = dong bar truoc nam trong nen: duong di
    khong co khoang trong. Nen 0 la diem xuat phat."""
    hi = np.concatenate([[p[0]], np.maximum(p[:-1], p[1:])])
    lo = np.concatenate([[p[0]], np.minimum(p[:-1], p[1:])])
    return hi, lo, np.concatenate([[p[0]], p[1:]])


def gop(p: np.ndarray, k: int):
    """Gop k tick thanh mot nen hi/lo/cl (nhu nen that: khoang gia KHONG gom tick dong cua nen truoc). Nen DAU va nen CUOI la diem suy
    bien de moi do phan giai bat dau o CUNG gia p[0] va tinh MTM cuoi tai CUNG gia. Bo phan du khong tron nen."""
    n = (len(p) - 1) // k
    if n < 1:
        raise ValueError("chuoi gia ngan hon mot nen (k = %d)" % k)
    m = p[1:1 + n * k].reshape(n, k)
    cuoi = m[-1, -1]
    return (np.concatenate([[p[0]], m.max(1), [cuoi]]), np.concatenate([[p[0]], m.min(1), [cuoi]]),
            np.concatenate([[p[0]], m[:, -1], [cuoi]]))


def mtm(hi, lo, cl, gian_cach_giay: float, ts: L.ThamSo) -> float:
    """Lai chot + lo noi o cuoi chuoi (don vi bao gia), tren QC_TONG_HOP. `gian_cach_giay` chi dung de dat truc thoi gian (khong
    co swap nen khong anh huong ket qua)."""
    n = len(cl)
    t0 = pd.Timestamp("2024-01-01")
    idx = pd.DatetimeIndex([t0, t0 + pd.Timedelta(seconds=gian_cach_giay * max(n - 1, 1))])
    dl = L.DuLieuChay(np.asarray(hi, float), np.asarray(lo, float), np.asarray(cl, float), np.zeros(n), np.zeros(n), idx,
                      QC_TONG_HOP)
    kq = L.chay_mang(dl, ts, VON)
    return float(kq.duong_equity[-1] - VON)


def _ts(kw: dict, mo_hinh: str) -> L.ThamSo:
    return L.ThamSo(**kw, khop_bar=mo_hinh)


def moc_tick(kw: dict, p: np.ndarray) -> float:
    """MTM cua `cuc_tri` chay tung tick (su that)."""
    return mtm(*nen_diem(p), 1, _ts(kw, "cuc_tri"))


def lech_ghep_doi(kw: dict, seeds, ngay: float, ks=KHUNG_MAC_DINH, mo_hinh=("cuc_tri", "duong_di")) -> dict:
    """Voi tung hat giong: duong gia moi, MOC (tick), roi voi moi mo hinh va moi k: MTM(nen k) - MOC. Tra:
    {"moc": mang, (mo_hinh, k): mang chenh lech theo hat giong, "tu_nhat": mang (duong_di tren doan tick - MOC)}."""
    ra: dict = {"moc": [], "tu_nhat": []}
    for mh in mo_hinh:
        for k in ks:
            ra[(mh, k)] = []
    for s in seeds:
        p = duong_gia(s, ngay)
        moc = moc_tick(kw, p)
        ra["moc"].append(moc)
        ra["tu_nhat"].append(mtm(*nen_doan(p), 1, _ts(kw, "duong_di")) - moc)
        for k in ks:
            bar = gop(p, k)
            for mh in mo_hinh:
                ra[(mh, k)].append(mtm(*bar, k, _ts(kw, mh)) - moc)
    return {k: np.asarray(v, float) for k, v in ra.items()}


def trung_binh_sai_so(x) -> tuple[float, float]:
    """(trung binh, sai so chuan cua trung binh) - sai so chuan = 0 neu chi co 1 mau."""
    x = np.asarray(x, float)
    se = float(x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else 0.0
    return float(x.mean()), se


def kiem_tu_nhat(kw: dict, seeds, ngay: float) -> tuple[float, float]:
    """`duong_di` tren DOAN tick vs MOC `cuc_tri` tren DIEM tick: (trung binh, SE) chenh lech - phai ~ 0 vi hai ben cung mo ta mot duong
    gia thang tung doan (neu lech nhieu thi mot trong hai mo hinh sai o cap tick)."""
    d = lech_ghep_doi(kw, seeds, ngay, ks=(), mo_hinh=())["tu_nhat"]
    return trung_binh_sai_so(d)


def chay_kiem(cau_hinh=None, seeds=range(1, 17), ngay: float = 2, ks=KHUNG_MAC_DINH) -> list[dict]:
    """Chay bo do cho cac cau hinh (mac dinh het CAU_HINH_MAU); moi dong: ten, moc, tu_nhat, lech[mo_hinh][k] = (tb, se)."""
    ds = list(CAU_HINH_MAU) if not cau_hinh else list(cau_hinh)
    ra = []
    for ten in ds:
        if ten not in CAU_HINH_MAU:
            raise ValueError("cau hinh %r khong co (co: %s)" % (ten, ", ".join(CAU_HINH_MAU)))
        d = lech_ghep_doi(CAU_HINH_MAU[ten], list(seeds), ngay, ks)
        ra.append(dict(ten=ten, moc=trung_binh_sai_so(d["moc"]), tu_nhat=trung_binh_sai_so(d["tu_nhat"]),
                       lech={mh: {k: trung_binh_sai_so(d[(mh, k)]) for k in ks} for mh in ("cuc_tri", "duong_di")}))
    return ra


def in_bang(ra: list[dict], ks=KHUNG_MAC_DINH, ra_ngoai=sys.stdout) -> None:
    w = lambda s: print(s, file=ra_ngoai)  # noqa: E731
    w("Lech GHEP DOI so voi chay TUNG TICK (don vi bao gia; ky vong that = 0): trung binh +- sai so chuan cua trung binh")
    w("%-12s %-9s %s" % ("cau hinh", "mo hinh", "  ".join("k=%-4d          " % k for k in ks)))
    for r in ra:
        w("%-12s MOC tick: %+.1f +- %.1f | duong_di tren doan - MOC: %+.2f +- %.2f" % ((r["ten"],) + r["moc"] + r["tu_nhat"]))
        for mh in ("cuc_tri", "duong_di"):
            w("%-12s %-9s %s" % ("", mh, "  ".join("%+8.1f +- %-5.1f" % r["lech"][mh][k] for k in ks)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ngay", type=float, default=2.0, help="so ngay moi duong gia (mac dinh 2)")
    ap.add_argument("--hat", type=int, default=16, help="so duong gia ghep doi (mac dinh 16)")
    ap.add_argument("--k", default=",".join(str(k) for k in KHUNG_MAC_DINH), help="so tick moi nen, cach nhau dau phay")
    ap.add_argument("--cau-hinh", default="", help="ten cau hinh mau, cach nhau dau phay (mac dinh het)")
    a = ap.parse_args(argv)
    ks = tuple(int(x) for x in a.k.split(",") if x.strip())
    ds = [x.strip() for x in a.cau_hinh.split(",") if x.strip()]
    t0 = time.time()
    ra = chay_kiem(ds or None, range(1, a.hat + 1), a.ngay, ks)
    in_bang(ra, ks)
    print("(%.0f giay, %s)" % (time.time() - t0, "nhan C" if L.LN.trang_thai().get("san_sang") else "Python thuan - cham"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
