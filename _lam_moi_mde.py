# -*- coding: utf-8 -*-
"""_lam_moi_mde.py - TINH LAI CA BANG MDE BANG MA HIEN TAI.

Vi sao can (do 12/09/2026): van tay cache MDE la
`so_bar|do_tin_chi_phi|...|cp3` - no KHONG chua phien ban ma. `nhan/do_luc.py`
sua lan cuoi 01/09, nhung **83/156 muc duoc do TRUOC do** (22/08: 26 · 24/08: 10
· 30/08: 42 · 31/08: 5). Van tay khong doi nen chung khong bao gio bi tinh lai.

Da kiem mot ca: `NZDHUF|D1` cache ghi 0,120 (do 30/08); tinh lai bang ma hien
tai ra **0,356** - lech 3x, cung van tay. MDE la rang buoc dang siet ca he
(`tat-fdr-va-nut-that-mde`), nen mot nua bang do ma cu sinh ra la dieu phai sua.

MDE TAT DINH: da chay `mde_cua(lam_moi=True)` ba lan lien tiep tren NZDHUF va
hai lan tren SP500, ket qua giong het tung chu so (HAT=4242). Nen moi khac biet
o day la do MA DOI, khong phai do nhieu.

Chay:  python _lam_moi_mde.py [--that]     (khong co --that thi chi DO, khong ghi)
Ra:    reports/LAM_MOI_MDE.json
"""
from __future__ import annotations

import json
import math
import statistics
import sys
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import do_luc as DL  # noqa: E402

RA = GOC / "reports" / "LAM_MOI_MDE.json"


def main(argv: list[str]) -> int:
    that = "--that" in argv
    cu = DL._doc_mde_cache()
    khoa = [k for k, v in cu.items() if isinstance(v, dict) and v.get("mde")]
    print(f"muc co MDE: {len(khoa)}  |  che do: {'GHI THAT' if that else 'chi DO, khong ghi'}")

    doi, y_nguyen, hong = [], 0, []
    t0 = time.time()
    for i, k in enumerate(khoa, 1):
        ma, _, khung = k.partition("|")
        v_cu = cu[k]
        try:
            v_moi = DL.mde_cua(ma, khung, lam_moi=True)
        except Exception as e:
            hong.append({"khoa": k, "loi": f"{type(e).__name__}: {e}"})
            continue
        m_cu, m_moi = v_cu.get("mde"), v_moi.get("mde")
        if m_moi is None:
            hong.append({"khoa": k, "loi": "tra ve khong co mde"})
            continue
        if abs(float(m_moi) - float(m_cu)) < 1e-9:
            y_nguyen += 1
        else:
            doi.append({"khoa": k, "cu": m_cu, "moi": m_moi,
                        "ty_le": round(float(m_moi) / max(float(m_cu), 1e-9), 3),
                        "do_luc_cu": v_cu.get("do_luc"),
                        "che_do": v_cu.get("che_do")})
        if i % 20 == 0:
            print(f"  ... {i}/{len(khoa)}  ({time.time()-t0:.0f}s)", flush=True)

    doi.sort(key=lambda r: -abs(math.log(max(r["ty_le"], 1e-9))))
    ket = {"so_muc": len(khoa), "y_nguyen": y_nguyen, "doi": doi, "hong": hong,
           "ghi_that": that, "giay": round(time.time() - t0, 1)}
    RA.parent.mkdir(exist_ok=True)
    RA.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\ny nguyen : {y_nguyen}")
    print(f"DOI      : {len(doi)}")
    print(f"hong     : {len(hong)}")
    if doi:
        ty = [r["ty_le"] for r in doi]
        print(f"ty le moi/cu: trung vi {statistics.median(ty):.3f} "
              f"(min {min(ty):.3f} max {max(ty):.3f})")
        print(f"\n{'khoa':26s} {'cu':>7s} {'moi':>7s} {'ty le':>7s}  do luc cu")
        for r in doi[:20]:
            print(f"{r['khoa']:26s} {r['cu']:7.3f} {r['moi']:7.3f} "
                  f"{r['ty_le']:7.3f}  {str(r['do_luc_cu'])[:10]}")
    print(f"\n-> {RA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
