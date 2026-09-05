# -*- coding: utf-8 -*-
"""6 he DAT MUC TIEU chu du an (>=20%/nam, DD<=60%) -> dang ky + cham holdout.

Muc 2 cua ban giao 04/09. Hai rang buoc cua ban giao, giu nguyen o day:

  - **Goi thang `quantlab.xac_nhan`**, khong tu viet lai vong cham diem. Ba loi
    cua phien 04/09 (da_dich=True, san_p_placebo lam nguong, gop log bang (1+r))
    deu sinh ra tu viec tu dung lai thu he da co.
  - **Dung MOT lan.** `xac_nhan` bo qua gia thuyet da co ket qua chua bi
    superseded, nen chay lai file nay khong cham holdout lan hai.

CANH BAO PHAI DOC KEM KET QUA: ca 6 deu tren YH_NASDAQ, deu L=2, va deu la ho
xu_huong (EMA / MACD / Ichimoku / RSI>55). Rat co the day la MOT hien tuong
("mua chi so co drift manh khi no tren duong trung binh") mac sau ao khac nhau,
chu khong phai 6 phat hien. 6 slot dang ky, 1 don vi thong tin.

YH_NASDAQ la chuoi NGOAI (khong mua duoc). Nen ket cuc mong doi cao nhat o day
la `CO_CO_CHE` chu khong phai `PASS`; muon thanh he giao dich duoc thi phai qua
chang hai `quantlab.bac_cau_san`.
"""
from __future__ import annotations

import json
import sys
import warnings

sys.path.insert(0, r"C:\Users\SV STORE\Downloads\Research SP500\lab")
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

from nhan import du_lieu as DL
from nhan import ngu_phap as NP
from nhan import so as SO
from tru import quantlab as QL

NGUON = "reports/muc_tieu_25.json"


def cac_he_dat() -> list[dict]:
    return [k for k in json.load(open(NGUON, encoding="utf-8")) if k["dat"]]


def cua_so_holdout(ma: str, khung: str) -> tuple[str, int, int]:
    """Cua so TRAIN dung y het `quantlab._nap` - khong duoc tu chia lai."""
    df = DL.nap(ma, khung)
    if DL.nguon_tai_san(ma) == "ngoai":
        df = DL.cat_theo_chat_luong(df, ma)[0]
    train, hold = DL.hai_nua(df, 0.6)
    return QL._cua_so(df), len(train), len(hold)


def chay() -> None:
    he = cac_he_dat()
    NP.nap_vao_mau()
    kho = {c.get("ten"): c for c in NP.doc_kho()}
    print("=" * 78)
    print("DANG KY %d HE DAT MUC TIEU ROI CHAM HOLDOUT DUNG MOT LAN" % len(he))
    print("=" * 78)

    ket = []
    for k in he:
        ten, ma, khung = k["ten"], k["ma"], k.get("khung", "D1")
        spec = kho.get(ten)
        if not spec:
            print("  [BO QUA] %s - khong con trong kho co che" % ten)
            continue
        ts = NP.tham_so_cua(spec)
        cs, n_tr, n_ho = cua_so_holdout(ma, khung)
        gt_ma = "%s.%s.%s.MUCTIEU" % (ma, khung, ten)

        cu = SO.mot("SELECT id FROM ket_qua WHERE gt_ma=? AND superseded_by IS NULL",
                    gt_ma)
        SO.dang_ky_gia_thuyet(
            ma=gt_ma, co_che=spec.get("co_che", ""), template=ten, tham_so=ts,
            tai_san=ma, khung=khung, cua_so=cs, ho=spec.get("ho", "khac"),
            nguon="muc_tieu_20pc", tru_sinh="QUANTLAB",
            ghi_chu="dat muc tieu chu du an: L=%.0f CAGR %.2f%% DD %.1f%% "
                    "(do tren TRAIN)" % (k["tot_nhat"]["L"],
                                         k["tot_nhat"]["cagr"] * 100,
                                         k["tot_nhat"]["dd"] * 100),
            so_phep_thu=len(json.load(open(NGUON, encoding="utf-8"))))
        if cu:
            print("  [DA CHAM] %s - holdout da dung, khong cham lai" % gt_ma)
            continue
        print("\n  >> %s  (train %d bar / holdout %d bar)" % (gt_ma, n_tr, n_ho))
        r = QL.xac_nhan(gt_ma)
        ket.append(r)
        print("     verdict : %s" % r.get("verdict"))
        for x in (r.get("ly_do") or [])[:3]:
            print("       - %s" % str(x)[:110])
        cs_he, bh = r.get("chi_so") or {}, r.get("mua_giu") or {}
        if cs_he:
            print("     he      : sharpe %.3f  cagr %.2f%%  dd %.1f%%"
                  % (cs_he.get("sharpe") or 0, (cs_he.get("cagr") or 0) * 100,
                     (cs_he.get("maxdd") or 0) * 100))
        if bh:
            print("     mua-giu : sharpe %.3f  cagr %.2f%%  dd %.1f%%"
                  % (bh.get("sharpe") or 0, (bh.get("cagr") or 0) * 100,
                     (bh.get("maxdd") or 0) * 100))
        al = r.get("alpha") or {}
        print("     alpha   : %.2f%%/nam  t=%.2f  placebo p=%s"
              % (al.get("alpha_nam_pct") or 0, al.get("t_alpha") or 0,
                 r.get("placebo")))

    print()
    print("=" * 78)
    dem: dict[str, int] = {}
    for r in ket:
        dem[r.get("verdict", "?")] = dem.get(r.get("verdict", "?"), 0) + 1
    print("KET: " + ("  ".join("%s=%d" % kv for kv in sorted(dem.items()))
                     or "khong cham cai nao (deu da co ket qua)"))
    json.dump(ket, open("reports/muc_tieu_holdout.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("chi tiet -> reports/muc_tieu_holdout.json")


if __name__ == "__main__":
    chay()
