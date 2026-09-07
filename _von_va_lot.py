# -*- coding: utf-8 -*-
"""_von_va_lot.py - VON BAO NHIEU THI VAO LOT BAO NHIEU. Va von nao thi CHET.

Chu du an 07/09/2026: *"Cho toi cac muc entry bao nhieu lot de tinh toan von cho
de nhe. 10% cua 1000usd khac 30% cua 100usd."*

Dung, va moi con so cua phien nay deu dang o **von 10.000 USD**. "Lot 8,0" khong
co nghia gi neu khong noi von.

## QUY TAC QUY DOI, VA CHO NO GAY

Tester chay **lot CO DINH** (khong lai kep), nen lai va sut giam deu **ti le
tuyen tinh voi lot**. Suy ra:

    mot cau hinh (lot L, von 10.000) == (lot L x k, von 10.000 x k)
    -> cung %/nam, cung sut giam %

Nen voi von V thi lot tuong duong la `L x V / 10.000`. **Nhung phep quy doi do
gay o hai cho, va ca hai deu lam von nho chet:**

1. **Lot toi thieu.** `US100Cash` co min lot **0,1**. Cau hinh lot 8,0 tren von
   10.000 quy ve von 200 USD la lot 0,16 - lam tron xuong 0,1 la **hut 37,5%**,
   lam tron len 0,2 la **doi 25% rui ro**. O von 100 USD thi lot 0,08 **khong
   dat duoc** - he KHONG chay duoc, khong phai "chay nho hon".
2. **Buoc lot.** Cung ly do, chi tho hon: lot phai la boi cua `volume_step`.

Do la ly do mot he "26%/nam" co the hoan toan khong chay duoc o von 200 USD,
va bang nay noi thang dieu do thay vi de nguoi doc tu nhan len roi hong.

## KHONG DUOC LAM

- **Khong nhan %/nam len khi lam tron lot xuong.** Bang duoi bao ca `lot ly
  thuyet` lan `lot chay duoc`, va `%/nam that` sau khi lam tron.
- **Khong bo qua ky quy.** Lot lon tren von nho co the du dieu kien lot nhung
  khong du ky quy -> lenh bi tu choi, va tester se ghi it lenh hon ma khong bao
  loi [[tester-cfd-chi-so-3-bay]].
- **Tai khoan CENT / MICRO chia 100** [[cent-chia-100-von-can]]
  [[xm-micro-contract-size]]: moi con so von o day la **USD CHUAN**. Tren tai
  khoan Micro (XM CO chia 100 cho chi so - support XM xac nhan) hoac cent thi
  **hop dong nho di 100 lan**, nen dong "von 10.000" doc thanh **100 USD THAT**
  voi cung con lot do. Do la loi ich THAT duy nhat cua cent/micro
  [[don-vi-tai-khoan-khong-cho-them-von]]: no khong cho them von, no **bo san
  lot toi thieu** - dung cai dang giet von nho o bang duoi.

  Ba dieu kien phai kiem truoc khi tin dong do: (1) san co tai khoan Micro/cent
  CO chi so nay khong; (2) lich su co du tu 2016 khong - Exness chi co bar tu
  2022-08 [[exness-lich-su-cat-2022-08]]; (3) spread/swap cua tai khoan do co
  bang tai khoan da do khong. Tai khoan XM dang dang nhap (420568985) la
  **CHUAN**, khong phai Micro.

Chay: python _von_va_lot.py [SYMBOL]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

LAB = Path(__file__).resolve().parent
BC = LAB / "reports"
MA = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"
VON_GOC = 10000.0
VON = [100, 200, 500, 1000, 2000, 5000, 10000, 20000]

#: Du phong khi khong hoi duoc MT5 (tester dang chiem terminal). Con so cua
#: US100Cash da do 06/09 va ghi trong `_z5_don_bay.py`.
DU_PHONG = {"volume_min": 0.1, "volume_step": 0.1, "contract": 1.0,
            "gia": 24000.0, "don_bay": 500}


def ho_so(ma: str) -> dict:
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            si = mt5.symbol_info(ma)
            tk = mt5.account_info()
            if si is not None:
                d = {"volume_min": float(si.volume_min),
                     "volume_step": float(si.volume_step),
                     "contract": float(si.trade_contract_size),
                     "gia": float(si.ask or si.bid or DU_PHONG["gia"]),
                     "don_bay": int(tk.leverage) if tk else 500}
                mt5.shutdown()
                return d
            mt5.shutdown()
    except Exception as e:
        print("(khong hoi duoc MT5: %s - dung so du phong)" % e)
    return dict(DU_PHONG)


def lam_tron(lot: float, hs: dict) -> float:
    b = hs["volume_step"]
    return round(int(lot / b + 1e-9) * b, 4)


def bang(ten: str, lots: list[float], pct_nam: float, dd_pct: float,
         lenh: int, hs: dict, nam: float = 10.16) -> dict:
    print("\n=== %s" % ten)
    print("   cau hinh goc (von %d USD): lot %s | %.2f%%/nam | sut giam %.2f%% "
          "| %d lenh (%.0f lenh/nam)"
          % (VON_GOC, "/".join("%.1f" % x for x in lots), pct_nam, dd_pct, lenh,
             lenh / nam))
    print("%8s %9s %20s %20s %8s %10s %10s"
          % ("von USD", "= micro", "lot ly thuyet", "lot CHAY DUOC", "%/nam",
             "sutgiam $", "ky quy $"))
    hang = []
    for v in VON:
        k = v / VON_GOC
        ly = [x * k for x in lots]
        that = [lam_tron(x, hs) for x in ly]
        chay = all(x >= hs["volume_min"] - 1e-9 for x, y in zip(that, ly)
                   if y > 0)
        # %/nam that: lot bi lam tron xuong thi lai giam theo dung ti le lot.
        ty = (sum(that) / sum(ly)) if sum(ly) > 0 else 0.0
        pn = ((1 + pct_nam / 100) ** 1 - 1) * 100 * ty if ty else 0.0
        # Lai KHONG ti le hoan toan tuyen tinh voi %/nam (vi %/nam la gop), nen
        # quy ve TIEN roi gop lai moi dung.
        tien = (((1 + pct_nam / 100) ** nam) - 1) * VON_GOC * ty
        pn = (((v * 1.0 + tien * k) / v) ** (1 / nam) - 1) * 100 if v > 0 else 0
        ky_quy = sum(that) * hs["contract"] * hs["gia"] / max(1, hs["don_bay"])
        d = {"von": v, "lot_ly_thuyet": [round(x, 3) for x in ly],
             "lot_chay_duoc": that, "chay_duoc": chay,
             "pct_nam": round(pn, 2) if chay else None,
             "sut_giam_usd": round(dd_pct / 100 * v, 2),
             "ky_quy_usd": round(ky_quy, 2),
             "hut_do_lam_tron_pct": round((1 - ty) * 100, 1)}
        hang.append(d)
        print("%8d %9.2f %20s %20s %8s %10.2f %10.2f%s"
              % (v, v / 100.0, "/".join("%.3f" % x for x in ly),
                 "/".join("%.2f" % x for x in that) if chay else "KHONG DAT MIN",
                 ("%7.2f%%" % pn) if chay else "     --",
                 dd_pct / 100 * v, ky_quy,
                 ("   hut %.0f%% do lam tron" % ((1 - ty) * 100))
                 if chay and ty < 0.97 else ""))
    return {"ten": ten, "lot_goc": lots, "pct_nam_goc": pct_nam,
            "dd_pct": dd_pct, "lenh": lenh, "hang": hang}


def main() -> int:
    hs = ho_so(MA)
    print("%s: min lot %.2f | buoc %.2f | contract %.0f | gia ~%.0f | don bay 1:%d"
          % (MA, hs["volume_min"], hs["volume_step"], hs["contract"], hs["gia"],
             hs["don_bay"]))

    ds = []
    # Doc thang tu bao cao cua phien - khong go tay lai con so.
    f = BC / ("BOBA_RA_TIEN_%s.json" % MA)
    if f.exists():
        for r in json.load(open(f, encoding="utf-8")):
            x = r.get("ba_chan")
            if not x:
                continue
            ds.append((" + ".join(t[:22] for t in r["bo"]),
                       [v for v in x["lot"][1:] if v > 0] or x["lot"][1:],
                       x["pct_nam"], x["dd"], x["lenh"]))
    f = BC / ("DEM_D_RA_TIEN_%s.json" % MA)
    if f.exists():
        for r in json.load(open(f, encoding="utf-8")):
            g = r.get("ghep") or {}
            for nhan in ("dinh", "dd20", "dd_chu_du_an"):
                x = g.get(nhan) if isinstance(g, dict) else None
                if not x:
                    continue
                ds.append(("%s + %s [%s]" % (r["a"][:20], r["b"][:20], nhan),
                           [v for v in x["lot"][1:] if v > 0],
                           x["pct_nam"], x["dd"], x["lenh"]))
    if not ds:
        print("chua co bao cao ra tien cho %s" % MA)
        return 1

    #: Sap theo %/nam nhung CHI lay cau hinh co so lenh du de ket luan
    #: [[tieu-chi-he-thong-doi-xep-hang]]: bang xep hang phai co SO LENH.
    ds = [d for d in ds if d[4] >= 50]
    ds.sort(key=lambda d: -d[2])
    ra = [bang(*d, hs=hs) for d in ds[:6]]
    (BC / ("VON_VA_LOT_%s.json" % MA)).write_text(
        json.dumps({"symbol": MA, "ho_so": hs, "von_goc": VON_GOC, "bang": ra},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n-> reports/VON_VA_LOT_%s.json" % MA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
