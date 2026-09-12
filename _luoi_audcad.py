# -*- coding: utf-8 -*-
"""AUDCAD: tu TIEM NANG -> THI NGHIEM THAM SO -> HE THONG.

Vong QuantLab chu du an mo ta 05/09. Tiem nang den tu `_luan_nguoc.py`:
13/19 tai khoan DCA song >= 2 nam tren bang xep hang mql5 danh AUDCAD
(nen 28%, nhi thuc mot phia p = 0,00035).

## HAM MUC TIEU - va vi sao KHONG phai loi suat

Voi lot PHANG va khong tai dau tu, loi suat/nam ty le thuan voi `lot/von`. Nen
"loi suat" cua mot cau hinh la mot con so **tuy y**: cu ha von xuong la no tang.
Xep hang theo no la xep hang theo mot lua chon cua chinh minh.

Thu KHONG tuy y la **lai mot nam tren mot don vi LO TREO DINH** -
`hieu_qua = lai_nam / lo_treo_dinh`. Lo treo dinh la von that su bi kep de
chay duoc cau hinh do. Sau khi chon duoc cau hinh co `hieu_qua` cao nhat, moi
scale `lot` len cho lo treo dinh cham dung NGAN SACH SUT GIAM cua chu du an.

Ho so do duoc tu 13 tai khoan song lau: chiu lo treo toi **33% von**, muc tai
dinh ~21%, ~8 lenh/tuan, giu ~1 ngay, PF ~1,56. Dung 33% lam ngan sach.

## HAI CHANG

  CHANG 1 tren TRAIN (60% dau) - quet toan bo luoi tham so.
  CHANG 2 tren HOLDOUT (40% cuoi) - chi cau hinh dan dau chang 1.

## KHAI BAO TRUOC

Luat mo phong day du o `nhan/luoi.py` (bat loi truoc, lot phang, khong cat lo,
co stop-out, spread that tung bar, phi qua dem theo chieu). Khong doi luat giua
chung. Khung M15 de quet; cau hinh dan dau se duoc kiem lai tren M5 va M1 de
DO thien lech do phan giai (bo nho: D1 thoi loi suat 11,7 lan).
"""
from __future__ import annotations

import itertools
import json
import os
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")

MA = "AUDCAD"
KHUNG = os.environ.get("KHUNG", "M15")
VON = 10_000.0
NGAN_SACH_TREO = 0.33          # ho so do duoc tu 13 tai khoan song >= 2 nam
SO_LUONG = int(os.environ.get("LUONG", "16"))
RA = "reports/luoi_audcad.json"

BUOC = (25, 40, 60, 90, 130)
TP_TY = (0.67, 1.0, 1.5)
TRAN = (5, 8, 10, 15, 20, 30)
CHE_DO = ("mua", "hai_chieu")
#: Truc LOT - chu du an cho phep 05/09. Do 21 cau hinh tham do: nhan lot chi
#: an khi TRAN TANG chat; nhan 1,3 o tran 20/40 thi CHAY tai khoan.
LOT = (("phang", 1.0), ("cong", 0.5), ("cong", 1.0), ("nhan", 1.15), ("nhan", 1.3))


def _mot(cfg) -> dict | None:
    import warnings as w
    w.filterwarnings("ignore")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from nhan import du_lieu as DL
    from nhan import luoi as L

    buoc, tp_ty, tran, che, (kieu_lot, he_so) = cfg
    d = DL.nap(MA, KHUNG)
    tr, _ho = DL.hai_nua(d, 0.6)
    ts = L.ThamSo(buoc=float(buoc), tp=float(buoc) * tp_ty, tran_tang=int(tran),
                  che_do=che, kieu_lot=kieu_lot, he_so_lot=he_so)
    try:
        kq = L.chay(tr, ts, VON)
        c = L.chi_so(kq, VON)
    except Exception:
        return None
    treo = kq.lo_treo_dinh
    lai_nam = kq.lai_rong / kq.so_nam
    return {
        "buoc": buoc, "tp_ty": tp_ty, "tp": buoc * tp_ty, "tran": tran,
        "che_do": che, "kieu_lot": kieu_lot, "he_so_lot": he_so,
        # HAM MUC TIEU: lai mot nam tren mot don vi lo treo dinh
        "hieu_qua": (lai_nam / treo) if treo > 0 else None,
        "lai_nam": lai_nam, "lo_treo_dinh": treo,
        "loi_suat_nam_pct": c["loi_suat_nam_pct"],
        "maxdd_pct": c["maxdd_pct"], "ro_nam": c["ro_nam"],
        "lenh_nam": c["lenh_nam"], "tang_max": c["tang_max"],
        "chay": c["chay"], "phi_tren_lai_gop_pct": c["phi_tren_lai_gop_pct"],
    }


def chay() -> None:
    from nhan import du_lieu as DL

    d = DL.nap(MA, KHUNG)
    tr, ho = DL.hai_nua(d, 0.6)
    cfgs = list(itertools.product(BUOC, TP_TY, TRAN, CHE_DO, LOT))
    print("=" * 88)
    print("LUOI AUDCAD - chang 1: quet %d cau hinh tren TRAIN" % len(cfgs))
    print("=" * 88)
    print("khung %s | train %s -> %s (%d bar) | holdout %s -> %s (%d bar)"
          % (KHUNG, tr.index[0].date(), tr.index[-1].date(), len(tr),
             ho.index[0].date(), ho.index[-1].date(), len(ho)))
    print("ham muc tieu: lai_nam / lo_treo_dinh  (KHONG phai loi suat - loi suat")
    print("ty le thuan lot/von nen la con so tuy y)")
    print()

    t0 = time.time()
    ket, xong = [], 0
    with ProcessPoolExecutor(max_workers=SO_LUONG) as ex:
        fu = {ex.submit(_mot, c): c for c in cfgs}
        for f in as_completed(fu):
            xong += 1
            r = f.result()
            if r:
                ket.append(r)
            if xong % 40 == 0:
                print("  ... %d/%d (%.0fs)" % (xong, len(cfgs), time.time() - t0))

    song = [k for k in ket if not k["chay"] and k["hieu_qua"] is not None
            and k["lai_nam"] > 0]
    song.sort(key=lambda k: -k["hieu_qua"])
    json.dump(ket, open(RA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print()
    print("da chay %d | co lai va khong chay: %d" % (len(ket), len(song)))
    print()
    print("--- 20 CAU HINH DAN DAU theo hieu qua (TRAIN) ---")
    print("  %-5s %-5s %-4s %-10s %-6s %-5s %8s %9s %9s %7s"
          % ("buoc", "TP", "tran", "che do", "lot", "he so", "hieu qua",
             "lai/nam", "treo dinh", "ro/nam"))
    for k in song[:20]:
        print("  %-5.0f %-5.0f %-4d %-10s %-6s %-5.2f %8.3f %9.1f %9.1f %7.1f"
              % (k["buoc"], k["tp"], k["tran"], k["che_do"], k["kieu_lot"],
                 k["he_so_lot"], k["hieu_qua"], k["lai_nam"],
                 k["lo_treo_dinh"], k["ro_nam"]))
    print()
    print("--- SCALE LEN NGAN SACH LO TREO %.0f%% VON ---" % (NGAN_SACH_TREO * 100))
    print("  (lot phang -> lai va lo treo cung ty le thuan lot; he so = ngan sach/treo)")
    print("  %-5s %-5s %-4s %-10s %-6s %-5s %8s %11s %12s"
          % ("buoc", "TP", "tran", "che do", "lot", "he so", "he so x",
             "lot L1", "loi suat/nam"))
    for k in song[:15]:
        hs = (NGAN_SACH_TREO * VON) / k["lo_treo_dinh"]
        print("  %-5.0f %-5.0f %-4d %-10s %-6s %-5.2f %8.2f %11.4f %11.2f%%"
              % (k["buoc"], k["tp"], k["tran"], k["che_do"], k["kieu_lot"],
                 k["he_so_lot"], hs, 0.01 * hs, k["loi_suat_nam_pct"] * hs))
    print()
    print("chi tiet -> %s" % RA)


if __name__ == "__main__":
    chay()
