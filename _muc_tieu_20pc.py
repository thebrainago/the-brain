# -*- coding: utf-8 -*-
"""25 ung vien co dat MUC TIEU CHU DU AN khong: >=20%/nam, DD <= 60%?

Khac han cau hoi cua cong ("co thang mua-giu ve Sharpe/Calmar khong").
Chay o nhieu muc don bay, tren TRAIN, khong cham holdout.
"""
import sys, json, warnings
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

import numpy as np
from nhan import bien_don_bay as B, chi_phi as CP, da_thoi_dai as DT
from nhan import du_lieu as DU, ngu_phap as NP
from pathlib import Path

MUC_CAGR, MUC_DD = 0.20, 0.60
DON_BAY = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)

ds = json.load(open("train_25.json", encoding="utf-8"))
kho = {c.get("ten"): c for c in NP.doc_kho()}
print(f"muc tieu: CAGR >= {MUC_CAGR:.0%}/nam, maxDD <= {MUC_DD:.0%}")
print(f"tran ly thuyet: CAGR_max = 0,5*Sharpe^2 -> can Sharpe >= "
      f"{(2*MUC_CAGR)**0.5:.3f}\n")

ket = []
for u in ds:
    spec = kho.get(u["ten"])
    if not spec:
        continue
    ma, khung = u["ma"], u["khung"]
    cua = DT.cac_cua_so_sach(ma, khung)
    if not cua:
        continue
    d_full = max(cua, key=lambda c: c["so_bar"])["df"]
    tr, _ = DU.hai_nua(d_full, 0.6)
    try:
        vi_the = NP.sinh_tu_spec(spec, tr)
        cp = CP.tu_du_lieu(ma, tr)
        cp = cp[0] if isinstance(cp, tuple) else cp
        hang, _ = B.do_bien(tr, np.asarray(vi_the, float), cp,
                            cac_don_bay=DON_BAY, co_tuc=False,
                            ma=ma, khung=khung, da_dich=False)
    except Exception:
        continue
    dat = [h for h in hang
           if (h.get("cagr") or 0) >= MUC_CAGR and abs(h.get("maxdd") or 1) <= MUC_DD]
    tot = max(dat, key=lambda h: h["cagr"]) if dat else None
    ket.append({"ten": u["ten"], "ma": ma, "sharpe_train": u["sharpe_train"],
                "dat": bool(dat),
                "tot_nhat": ({"L": tot["don_bay"], "cagr": round(tot["cagr"], 4),
                              "dd": round(tot["maxdd"], 4),
                              "sharpe": round(tot.get("sharpe") or 0, 3)}
                             if tot else None),
                "hang": [{"L": h["don_bay"], "cagr": round(h.get("cagr") or 0, 4),
                          "dd": round(h.get("maxdd") or 0, 4)} for h in hang]})

json.dump(ket, open("muc_tieu_25.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
dat = [k for k in ket if k["dat"]]
print(f"=== {len(dat)}/{len(ket)} DAT MUC TIEU (>=20%/nam, DD<=60%) ===\n")
for k in sorted(dat, key=lambda z: -(z["tot_nhat"]["cagr"])):
    t = k["tot_nhat"]
    print(f"  CAGR {t['cagr']:>7.2%}  DD {t['dd']:>7.2%}  L={t['L']:.0f}  "
          f"sharpe {k['sharpe_train']:.3f}  {k['ten'][:32]}")
if not dat:
    print("  khong cai nao. Bang day du o muc_tieu_25.json")
    for k in ket[:5]:
        print(f"  {k['ten'][:30]:30s} " +
              " | ".join(f"L{h['L']:.0f}: {h['cagr']:.1%}/DD{h['dd']:.0%}"
                         for h in k["hang"]))
