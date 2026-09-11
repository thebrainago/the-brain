# -*- coding: utf-8 -*-
"""_luong2_qwen.py - LUONG 2: qwen doc toan van + boc co che, sau khi Seeker xong.

Phan vai (08/09/2026): qwen ganh KHOI LUONG (doc 6.658 tai lieu + 389 .mq5),
Claude giu khung ngu phap va cong. Ly do khong giao cong cho may: do duoc
`co_che` LLM dien 48 -> tham dinh bac 41 -> rong cuu 3 [[co-che-khong-dien-duoc-bang-may]].

`boc_llm.boc` da goi `bo_qua_han_muc=True` + 8 luong nen phanh `cach_nhau_giay=600`
trong config KHONG ap cho duong nay - do la phanh cho SEEKER chay nen.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

CHU_DE_TU = {
    "QUAN_TRI_LENH": ("straddle", "pending order", "buy stop", "sell stop", "grid",
                      "trailing", "breakeven", "hedge", "recovery", "basket",
                      "partial close", "order management"),
    "GANN": ("gann", "square of nine", "square of 9"),
    "DAO_CHIEU": ("divergence", "regression channel", "z-score", "zscore",
                  "standard deviation channel", "mean reversion"),
    "LEAD_LAG": ("lead lag", "lead-lag", "cointegration", "pairs trading",
                 "correlation", "intermarket", "spread trading"),
}


def main() -> int:
    from nhan import boc_llm as BL
    from nhan import doc_song_song as DS
    from nhan import du_lieu as DU
    from nhan import ngu_phap as NP
    from nhan import so as SO

    t0 = time.time()
    truoc = NP.doc_kho()
    print("=== LUONG 2 (qwen): DOC + BOC ===")
    print("co che truoc: %d" % len(truoc), flush=True)

    print("\n-- 2a. doc toan van song song --", flush=True)
    d = DS.doc(gioi_han=600, luong=12)
    print("   doc duoc %s/%s (%s s/ban)" % (d.get("doc_duoc"), d.get("tai_lieu"),
                                            d.get("giay_moi_ban")), flush=True)

    print("\n-- 2b. qwen boc co che --", flush=True)
    df = DU.nap("US500CASH", "H4")
    b = BL.boc(gioi_han=300, luong=8, ghi_kho=True, df_kiem=df)
    print("   %r" % ({k: v for k, v in (b or {}).items() if k != "chi_tiet"},),
          flush=True)

    sau = NP.doc_kho()
    print("\n   kho co che: %d -> %d (+%d)" % (len(truoc), len(sau),
                                               len(sau) - len(truoc)), flush=True)

    # Cai moi co cham vao bon gia thuyet khong? Do tren TEN + NGUON cua spec moi.
    ten_cu = {s.get("ten") for s in truoc}
    moi = [s for s in sau if s.get("ten") not in ten_cu]
    print("\n=== BON GIA THUYET: co che MOI cham vao ===", flush=True)
    import json as _j
    for cd, tu in CHU_DE_TU.items():
        hit = [s for s in moi
               if any(t in _j.dumps(s, ensure_ascii=False).lower() for t in tu)]
        print("  %-14s %d/%d co che moi" % (cd, len(hit), len(moi)))
        for s in hit[:6]:
            print("       - %s  [%s]" % (s.get("ten"), s.get("ho")))

    print("\n=== XONG %.0fs ===" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
