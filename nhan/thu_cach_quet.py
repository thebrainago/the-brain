# -*- coding: utf-8 -*-
"""thu_cach_quet.py - SO SANH cac cach quet luoi tren du lieu DA QUET (khong mo rong, khong ghi so tay).

Chu du an 07/10/2026: "thu cac cach quet tren nhung ket qua da quet de xem cai nao toi uu nhat".
Do 07/10 tren 703 don: 84,6% o co lai => quet day khong phan biet duoc o tot / xau. Cau hoi o day: cach nao TIM LAI
dung vung tot (top-K o) voi it phep tinh nhat?

Lam gi: lay vai don quet cu (viec/cho/220*.json, cung luoi + che_do), chay DAY DU luoi tren kham_pha MOT lan (chuan),
roi mo phong tung cach tren BANG chuan do (khong tinh lai) va do:
  chi_phi  so phep tinh tuong duong 1 o chay tren toan doan (o chay tren 1/3 doan tinh 1/3)
  top_k    ti le top-K o that nam trong tap da tinh (K = 10 va 50)
  hang     hang (trong luoi day du) cua o tot nhat ma cach do tim ra
  lai_oc   sai lech tuyet doi cua ti le "co lai" uoc luong so voi that (cao nguyen)
Cac cach: ngau nhien 10/20/30% · thua-roi-min (moi truc lay xen ke, tinh min lan can top-M) · hai tang 1/3 doan
(qua neu co lai tren 1/3 dau; hoac top 30%) · cat som (chi dem ti le o 'chay tai khoan': tran tren tiet kiem).

KHONG ghi nc.db, khong dung van tay thi nghiem, khong cham xac_nhan: chi doan kham_pha va chi la do cach quet.
Tinh logic (so_sanh) la ham thuan -> test khong can du lieu gia.
"""
from __future__ import annotations

import itertools
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

GOC = Path(__file__).resolve().parent.parent
K_LIST = (10, 50)


def _diem(r: dict) -> float:
    """Diem xep hang cua mot o: loi suat o tran DD80 neu co lai, nguoc lai -inf."""
    if not r or "loi" in r or not r.get("co_lai") or r.get("loi_suat_o_tran_pct") is None:
        return -math.inf
    return float(r["loi_suat_o_tran_pct"])


def _top_phan_tram(d: np.ndarray, p: float) -> np.ndarray:
    """Mat na True cho p*n o diem cao nhat (khong dung quantile: -inf lam quantile thanh nan)."""
    m = np.zeros(len(d), bool)
    m[np.argsort(-d, kind="stable")[: max(1, int(len(d) * p))]] = True
    return m


def _toa_do(dai: list[int]) -> list[tuple]:
    return list(itertools.product(*[range(n) for n in dai]))


def so_sanh(diem: np.ndarray, co_lai: np.ndarray, chay: np.ndarray, dai: list[int],
            diem_1_3: np.ndarray | None = None, co_lai_1_3: np.ndarray | None = None,
            hat: int = 0, lan_ngau_nhien: int = 20) -> dict:
    """`diem`, `co_lai`, `chay`: bang chuan theo thu tu `_toa_do(dai)` (chu so cuoi doi nhanh nhat).
    `diem_1_3`, `co_lai_1_3`: cung o chay tren 1/3 doan dau (None = bo qua cach hai tang)."""
    n = len(diem)
    toa = _toa_do(dai)
    assert len(toa) == n, "bang khong khop luoi"
    thu_tu = np.argsort(-diem, kind="stable")
    hang = np.empty(n, int)
    hang[thu_tu] = np.arange(n)
    that_top = {k: set(thu_tu[:k].tolist()) for k in K_LIST if k <= n}
    ti_le_that = float(co_lai.mean())

    def do(tap: set, chi_phi: float) -> dict:
        tap_l = sorted(tap)
        ra = {"chi_phi": round(chi_phi, 1), "ti_le_chi_phi": round(chi_phi / n, 3), "so_o": len(tap_l)}
        for k, t in that_top.items():
            ra["top%d" % k] = round(len(t & tap) / len(t), 3)
        ra["hang_tot_nhat_tim_duoc"] = int(hang[tap_l].min()) if tap_l else None
        ra["sai_lech_ti_le_co_lai"] = round(abs(float(co_lai[tap_l].mean()) - ti_le_that), 3) if tap_l else None
        return ra

    kq = {"so_o": n, "ti_le_co_lai_that": round(ti_le_that, 3), "ti_le_chay_tai_khoan": round(float(chay.mean()), 3),
          "toan_bo": do(set(range(n)), float(n))}

    rng = np.random.default_rng(hat)
    for p in (0.10, 0.20, 0.30):
        acc = []
        for _ in range(lan_ngau_nhien):
            tap = set(rng.choice(n, size=max(1, int(n * p)), replace=False).tolist())
            acc.append(do(tap, float(len(tap))))
        kq["ngau_nhien_%d%%" % round(p * 100)] = {
            k: (round(float(np.mean([a[k] for a in acc if a[k] is not None])), 3)) for k in acc[0]}

    # thua-roi-min: moi truc lay chi so chan (va chi so cuoi), tinh lan can +-1 cua top-M o thua
    chi_so = {t: i for i, t in enumerate(toa)}
    for buoc in (2, 3):                              # buoc 2 = chi so chan (che do thua_roi_min); buoc 3 = thua hon nua
        thua = [i for i, t in enumerate(toa) if all(c % buoc == 0 or c == d - 1 for c, d in zip(t, dai))]
        for m in (5, 10, 20):
            top_m = sorted(thua, key=lambda i: -diem[i])[:m]
            tap = set(thua)
            for i in top_m:
                if diem[i] == -math.inf:
                    continue
                lan = [range(max(0, c - buoc + 1), min(d, c + buoc)) for c, d in zip(toa[i], dai)]
                tap.update(chi_so[t] for t in itertools.product(*lan))
            kq["thua_roi_min_top%d" % m if buoc == 2 else "thua3_roi_min_top%d" % m] = do(tap, float(len(tap)))

    if diem_1_3 is not None:
        for ten, giu in (("hai_tang_co_lai_1_3", co_lai_1_3.astype(bool)),
                         ("hai_tang_top30_1_3", _top_phan_tram(diem_1_3, 0.30))):
            tap = set(np.flatnonzero(giu).tolist())
            kq[ten] = do(tap, n / 3.0 + len(tap))
    return kq


def tong_hop(cac: list[dict]) -> dict:
    """Trung binh cac chi so cua tung cach tren nhieu don."""
    cach = [k for k in cac[0] if isinstance(cac[0][k], dict) and "chi_phi" in cac[0][k]]
    ra = {}
    for c in cach:
        cs = [x[c] for x in cac if c in x]
        ra[c] = {k: round(float(np.mean([v[k] for v in cs if v.get(k) is not None])), 3) for k in cs[0] if k != "so_o"}
    return ra


def _doc_don(tep: Path):
    d = json.load(open(tep, encoding="utf-8"))
    lenh = d.get("lenh") or (d.get("bang_chung") or {}).get("lenh") or []
    if len(lenh) < 6 or lenh[2:5] != ["nc", "cc", "quet_luoi"]:
        return None
    return json.loads(lenh[5]), tep.stem


def chon_don(toi_da: int = 6) -> list:
    """Vai don dai dien: theo khung, moi khung 2 don khac (ma, che_do); M5 chi 1 (chay lau)."""
    mau, dem, thay = [], {}, set()
    for tep in sorted((GOC / "viec" / "xong").glob("220*.json")):
        x = _doc_don(tep)
        if x is None:
            continue
        spec, ten = x
        khoa = (spec["ma"], spec["khung"])
        if khoa in thay or sorted(spec.get("luoi", {})) != ["buoc", "cho_lui", "tp", "tran_tang"]:
            continue
        kh = spec["khung"]
        if dem.get(kh, 0) >= (1 if kh == "M5" else 2):
            continue
        thay.add(khoa)
        dem[kh] = dem.get(kh, 0) + 1
        mau.append((spec, ten))
        if len(mau) >= toi_da:
            break
    return mau


def chay_don(spec: dict, luong: int = 0) -> dict:
    """Chay day du luoi tren kham_pha (va tren 1/3 dau) roi so sanh cac cach. Can du lieu gia + nhan C."""
    from nhan import luoi as LU
    from nhan import nc_thi_nghiem as TN
    ma, khung, co_dinh, luoi = spec["ma"], spec["khung"], dict(spec.get("co_dinh", {})), spec["luoi"]
    von = float(spec.get("von", 10000))
    pre, a = TN.NDL.cat_doan(TN.NDL.nap(ma, khung), "kham_pha")
    seg = pre.iloc[a:]
    cp = TN.NDL.chi_phi(ma, pre)
    qc, ly = LU.quy_cach_cho(ma, None, None)
    if LU.lop_quy_cach(ma) not in ("audcad", "tong_hop"):
        qc, ly = LU.quy_cach_cho(ma, float(np.nanmedian(seg["close"].to_numpy(float))), cp)
    if qc is None:
        raise RuntimeError(ly)
    von_q = von * qc.von_quy_doi
    moc = round(TN._moc(ma, khung, "kham_pha", seg, cp) * 100, 2)
    dl, dl3 = LU.chuan_bi(seg, qc), LU.chuan_bi(seg.iloc[: len(seg) // 3], qc)
    khoa = list(luoi)
    dai = [len(luoi[k]) for k in khoa]
    cac_o = [dict(zip(khoa, (luoi[k][j] for k, j in zip(khoa, t)))) for t in _toa_do(dai)]
    luong = luong or TN._luong_quet_luoi()

    def bang(dl_):
        with ThreadPoolExecutor(max_workers=luong) as ex:
            return list(ex.map(lambda o: TN._o_luoi(dl_, co_dinh, o, von_q, moc), cac_o))

    t0 = time.time()
    b, t_day = bang(dl), time.time() - t0
    t0 = time.time()
    b3, t_3 = bang(dl3), time.time() - t0
    arr = lambda r, f: np.array([f(x) for x in r])           # noqa: E731
    kq = so_sanh(arr(b, _diem), arr(b, lambda x: bool(x.get("co_lai"))), arr(b, lambda x: bool(x.get("chay"))), dai,
                 arr(b3, _diem), arr(b3, lambda x: bool(x.get("co_lai"))))
    kq["giay_day_du"], kq["giay_1_3"] = round(t_day, 1), round(t_3, 1)
    kq["ty_le_giay_1_3_so_day_du"] = round(t_3 / t_day, 3) if t_day else None
    kq["ma"], kq["khung"], kq["che_do"] = ma, khung, co_dinh.get("che_do")
    return kq


def main(argv=None) -> int:
    toi_da = int((argv or sys.argv[1:] or ["6"])[0])
    cac, loi = [], []
    for spec, ten in chon_don(toi_da):
        try:
            r = chay_don(spec)
            r["don"] = ten
            cac.append(r)
            print("xong", ten, "co_lai_that", r["ti_le_co_lai_that"], "giay", r["giay_day_du"], flush=True)
        except Exception as e:                                                # noqa: BLE001
            loi.append({"don": ten, "loi": "%s: %s" % (type(e).__name__, str(e)[:200])})
            print("LOI", ten, loi[-1]["loi"], flush=True)
    ra = {"cac_don": cac, "loi": loi, "tong_hop": tong_hop(cac) if cac else None}
    (GOC / "reports").mkdir(exist_ok=True)
    (GOC / "reports" / "thu_cach_quet.json").write_text(json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    if cac:
        print("TONG HOP (trung binh %d don; chi_phi = ti le so voi quet day du)" % len(cac))
        for c, v in ra["tong_hop"].items():
            print("%-26s chi_phi %.3f  top10 %.2f  top50 %.2f  hang_tot_nhat %.1f  lech_co_lai %.3f" % (
                c, v["ti_le_chi_phi"], v.get("top10", 0), v.get("top50", 0), v.get("hang_tot_nhat_tim_duoc", -1),
                v.get("sai_lech_ti_le_co_lai", -1)))
    return 0 if cac else 1


if __name__ == "__main__":
    raise SystemExit(main())
