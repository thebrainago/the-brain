# -*- coding: utf-8 -*-
"""_placebo_quan_tri.py - 5/42 LUAT TRAILING QUA CA HAI NUA LA THAT HAY LA DAM NHIEU?

Viec so 1 cua khoi 7 (`config/ke_hoach_xay.json`).

VI SAO CAN. `_thu_quan_tri.py` do duoc: 42 luat quan tri dap len he nen (luoi
AUDCAD Bigmouse), **11 hon o train · 8 hon o holdout · 5 hon CA HAI**, va ca 5
deu la trailing voi bien do lon (hon_ho +1.437 den +3.870 USD/nam).

Nhung neu hai cong doc lap thi ky vong qua ca hai la 0,26 x 0,19 x 42 = **2,1**
luat. Quan sat 5 - chi **2,4 lan** ky vong ngau nhien. Khong du de tin bang so
dem. Con so dang tin hon la BIEN DO, nhung bien do cung can mot dam de so.

NULL. Voi MOI luat that, giu nguyen **ten nut** cua no, thay **gia tri** bang
gia tri boc lai tu chinh kho gia tri cua nut do (gom tu ca 42 luat). Nhu vay:

  - phan bo gia tri tung nut GIU NGUYEN -> khong so sanh trailing_tu=1 voi
    trailing_tu=100.000
  - hinh dang bo nut GIU NGUYEN -> luat chi co `trailing_tu` van chi co mot nut
  - chi pha duy nhat mot thu: **su ket hop cu the** ma tac gia EA da chon

Neu cac gia tri that khong dac biet, ti le "hon ca hai" cua ban gia se bang ti
le that. Neu that su co gi do, ban that phai noi len khoi dam.

HAI CHIEU. Bo do nay chi co nghia neu no BIET NOI KHONG. Ban gia dung bang kho
gia tri that nen neu no ra 0% thi chinh no hong - in ra ca hai ti le de thay.

Chay:  python _placebo_quan_tri.py [so_ban_gia]     (mac dinh 200)
Ra:    reports/PLACEBO_QUAN_TRI.json
"""
from __future__ import annotations

import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

import numpy as np  # noqa: E402

import _thu_quan_tri as TQ  # noqa: E402

RA = GOC / "reports" / "PLACEBO_QUAN_TRI.json"
NGUON = GOC / "reports" / "xet_quan_tri.json"
HAT = 20260912


def main(argv: list[str]) -> int:
    so_ban = int(argv[0]) if argv else 200
    that = json.loads(NGUON.read_text(encoding="utf-8"))
    that = [r for r in that if "loi" not in r and r.get("nut")]
    print(f"luat that doc duoc: {len(that)}")

    # Kho gia tri theo TUNG nut, gom tu ca 42 luat.
    kho = defaultdict(list)
    for r in that:
        for k, v in r["nut"].items():
            kho[k].append(float(v))
    print("kho gia tri moi nut:")
    for k, v in sorted(kho.items()):
        print(f"  {k:16s} n={len(v):3d}  {min(v):g} .. {max(v):g}")

    d5 = TQ.DL.nap("AUDCAD", "M5")
    sm = float(np.nanmedian(d5["spread"].to_numpy(float)))
    tr, ho = TQ.DL.hai_nua(d5, 0.6)
    Dtr, Dho = TQ._mk(tr, sm), TQ._mk(ho, sm)
    m_tr = TQ.MV.mo_phong(Dtr, **TQ.NEN)
    m_ho = TQ.MV.mo_phong(Dho, **TQ.NEN)
    print(f"\nhe NEN: train {m_tr['lai_nam']:.0f}$/nam · holdout {m_ho['lai_nam']:.0f}$/nam")

    # Moc THAT, tinh lai tu chinh file de khong tin mot con so cheo tay.
    that_ca_hai = [r for r in that if r["hon_tr"] > 0 and r["hon_ho"] > 0]
    ty_le_that = len(that_ca_hai) / len(that)
    bien_do_that = sorted((r["hon_ho"] for r in that_ca_hai), reverse=True)
    print(f"THAT   : hon ca hai {len(that_ca_hai)}/{len(that)} = {ty_le_that:.1%}"
          f" · hon_ho lon nhat {bien_do_that[0]:+.0f}$" if bien_do_that else "")

    r = random.Random(HAT)
    ban_gia, t0 = [], time.time()
    for i in range(so_ban):
        mau = that[i % len(that)]
        nut = {k: r.choice(kho[k]) for k in mau["nut"]}
        try:
            a = TQ.MV.mo_phong(Dtr, **{**TQ.NEN, **nut})
            b = TQ.MV.mo_phong(Dho, **{**TQ.NEN, **nut})
        except Exception:
            continue
        ban_gia.append({"nut": nut,
                        "hon_tr": float(a["lai_nam"]) - float(m_tr["lai_nam"]),
                        "hon_ho": float(b["lai_nam"]) - float(m_ho["lai_nam"])})
        if (i + 1) % 25 == 0:
            n_ok = sum(1 for x in ban_gia if x["hon_tr"] > 0 and x["hon_ho"] > 0)
            print(f"  ... {i+1}/{so_ban}  hon ca hai {n_ok}/{len(ban_gia)}"
                  f"  ({time.time()-t0:.0f}s)", flush=True)

    gia_ca_hai = [x for x in ban_gia if x["hon_tr"] > 0 and x["hon_ho"] > 0]
    ty_le_gia = len(gia_ca_hai) / max(len(ban_gia), 1)
    moc = bien_do_that[0] if bien_do_that else float("inf")

    # SO CUNG CO MAU - khong so MOT CUC DAI voi TUNG BAN LE.
    #
    # Ban dau viet: dem bao nhieu ban gia LE dat >= moc -> 9/400 -> p = 0,0249
    # "DAT". SAI. `moc` la CAI TOT NHAT TRONG 40 ban that, tuc mot cuc dai; dem
    # ban gia le la dem tung rut don. Cung ho loi voi viec chay 40 phep thu roi
    # bao p cua cai tot nhat ma khong hieu chinh.
    #
    # Phep so dung: rut 40 ban gia (co hoan lai), lay MAX, lap nhieu lan, roi hoi
    # moc that nam o dau trong phan bo max do. Doi han: p 0,0249 -> 0,5924, va
    # moc that (+3.870$) nam DUOI trung vi cua phan bo max gia (+4.385$).
    rb = random.Random(HAT + 1)
    N_BOOT = 20000
    max_gia = sorted(max(rb.choice(ban_gia)["hon_ho"] for _ in range(len(that)))
                     for _ in range(N_BOOT))
    p_bien_do = (sum(1 for m in max_gia if m >= moc) + 1) / (N_BOOT + 1)

    # Tieu chi DEM cung phai so cung co mau, khong dat hai ty le tho canh nhau.
    vuot_dem = sum(
        1 for _ in range(N_BOOT)
        if sum(1 for _ in range(len(that)) if rb.random() < ty_le_gia)
        >= len(that_ca_hai))
    p_dem = (vuot_dem + 1) / (N_BOOT + 1)

    ket = {"so_that": len(that), "that_hon_ca_hai": len(that_ca_hai),
           "ty_le_that": round(ty_le_that, 4),
           "so_ban_gia": len(ban_gia), "gia_hon_ca_hai": len(gia_ca_hai),
           "ty_le_gia": round(ty_le_gia, 4),
           "bien_do_that_lon_nhat": moc,
           "p_bien_do": round(p_bien_do, 4), "p_dem": round(p_dem, 4),
           "phan_vi_max_gia": {"50%": max_gia[N_BOOT // 2],
                               "90%": max_gia[int(0.90 * N_BOOT)],
                               "95%": max_gia[int(0.95 * N_BOOT)]},
           "giay": round(time.time() - t0, 1)}
    RA.parent.mkdir(exist_ok=True)
    RA.write_text(json.dumps({**ket, "ban_gia": ban_gia}, ensure_ascii=False,
                             indent=1, default=float), encoding="utf-8")

    print("\n" + "=" * 72)
    print(f"THAT    hon ca hai {len(that_ca_hai):3d}/{len(that):3d} = {ty_le_that:6.1%}")
    print(f"BAN GIA hon ca hai {len(gia_ca_hai):3d}/{len(ban_gia):3d} = {ty_le_gia:6.1%}")
    if ty_le_gia <= 0:
        print("  !! ban gia ra 0% - kiem lai bo do truoc khi mung, no dung KHO GIA TRI THAT")
    print(f"\nDEM      p = {p_dem:.4f}   P(>= {len(that_ca_hai)} trong {len(that)} "
          f"| ti le gia {ty_le_gia:.1%})")
    print(f"BIEN DO  p = {p_bien_do:.4f}   ban that tot nhat {moc:+.0f}$/nam so voi "
          f"phan bo MAX-cua-{len(that)} ban gia")
    print(f"         max ban gia: 50% {max_gia[N_BOOT//2]:+.0f}$ · "
          f"90% {max_gia[int(.9*N_BOOT)]:+.0f}$ · 95% {max_gia[int(.95*N_BOOT)]:+.0f}$")
    print("PHAN QUYET:", "DAT - ban that noi len khoi dam"
          if (p_bien_do <= 0.05 and p_dem <= 0.05)
          else "KHONG DAT - nam trong dam")
    print(f"\n-> {RA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
