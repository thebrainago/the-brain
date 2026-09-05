# -*- coding: utf-8 -*-
"""nap_lai_ban_tho.py - DUA BAN THO DA BOC QUA CONG, KHONG GOI LAI LLM.

Vi sao ton tai: `chay_that` cua ca hai duong boc ghi ban tho (`reports/
*_tho.json`) NGAY sau khi goi API, TRUOC buoc kiem. Nen khi cong tu choi ca me
vi mot ly do sua duoc trong vai phut - do 05/09: 80/80 khai bao bi tu choi vi
thieu truong `co_che`, ra `them vao kho: 0` du 64/82 file da ra co che - thi
khong can goi lai API. Chi can nap lai ban tho.

Mot me lan chien luoc ton ~9 phut goi API; nap lai ban tho ton 3 giay.

    python nap_lai_ban_tho.py                 # bao cao, KHONG ghi
    python nap_lai_ban_tho.py --that          # ghi vao kho
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nhan import boc_ma_llm as BM        # noqa: E402
from nhan import loc_co_che as LCC       # noqa: E402
from nhan import ngu_phap as NP          # noqa: E402

LAB = Path(__file__).resolve().parent

#: Ban tho -> lan sinh ra no. Dung de danh dau `nguon_lan` cua co che.
BAN_THO = {
    "reports/boc_ma_llm_tho.json": "chien_luoc",
    "reports/doc_chi_bao_tho.json": "chi_bao",
}


def nap(that: bool = False, in_ra=print) -> dict:
    df = LCC.df_kiem_chuan()
    if df is None:
        in_ra("khong nap duoc chuoi kiem - dung lai, khong ha cong")
        return {"chua_do": True}

    tong = {"khai_bao": 0, "qua_kiem": 0, "them": 0}
    tu_choi = Counter()
    for duong, lan in BAN_THO.items():
        p = LAB / duong
        if not p.exists():
            in_ra("  bo qua %s (chua co)" % duong)
            continue
        tho = json.loads(p.read_text(encoding="utf-8"))
        cd = sum(1 for k in tho if k.get("chua_do"))
        cc_tong, giu_tong = 0, []
        for k in tho:
            cc = k.get("co_che") or []
            if not isinstance(cc, list):
                continue
            cc_tong += len(cc)
            g, _ = BM.kiem_va_giu(cc, nguon=k.get("ten", ""))
            for c in g:
                c["nguon_lan"] = lan
            giu_tong += g
        in_ra("%-34s %3d file (%d chua do) · %3d khai bao · %3d qua kiem"
              % (duong, len(tho), cd, cc_tong, len(giu_tong)))
        tong["khai_bao"] += cc_tong
        tong["qua_kiem"] += len(giu_tong)
        if not that:
            continue
        for c in giu_tong:
            r = NP.them_co_che(c, df)
            if r.get("nhan"):
                tong["them"] += 1
            else:
                tu_choi[str((r.get("ly_do") or ["?"])[0])[:52]] += 1

    in_ra("")
    in_ra("khai bao: %d · qua kiem khai bao: %d · THEM VAO KHO: %d"
          % (tong["khai_bao"], tong["qua_kiem"], tong["them"]))
    for k, v in tu_choi.most_common(8):
        in_ra("  cong tu choi %3d: %s" % (v, k))
    if not that:
        in_ra("  (chay lai voi --that de ghi)")
    return tong


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    nap(that="--that" in sys.argv)
