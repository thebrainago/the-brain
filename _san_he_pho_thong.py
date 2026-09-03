# -*- coding: utf-8 -*-
"""San 30 he thong giao dich pho thong theo TEN, roi boc luon (03/09/2026)."""
import sys, json
sys.path.insert(0, '.')
from nhan import muc_tieu as MT, boc_llm as BL, ngu_phap as NP, du_lieu as DU, so as SO

if __name__ == "__main__":
    def ghi(*a): print(*a, flush=True)
    truoc_tl = dict(SO.mot("SELECT COUNT(*) n FROM tai_lieu"))["n"]
    truoc_cc = len(NP.doc_kho())
    ghi(f"kho truoc: {truoc_tl} tai lieu, {truoc_cc} co che")
    ghi("-- SAN THEO TEN HE THONG --")
    s = MT.san_he_pho_thong(ngan_sach_giay=1500, in_ra=ghi)
    ghi(f"   -> {s['tai_lieu_moi']} tai lieu moi ({s['giay']}s)")
    n = dict(SO.mot("SELECT COUNT(*) n FROM tai_lieu WHERE LOWER(tieu_de) LIKE '%sonic%' "
                    "OR LOWER(url) LIKE '%sonic%'"))["n"]
    ghi(f"   tai lieu co 'sonic' o tieu de/url: {n}")
    ghi("-- BOC --")
    df = DU.nap('US500CASH', 'H4')
    r = BL.boc(gioi_han=150, luong=8, ghi_kho=True, df_kiem=df, in_ra=ghi)
    ghi(json.dumps(r, ensure_ascii=False, indent=1))
    ghi(f"KHO CO CHE: {truoc_cc} -> {len(NP.doc_kho())}")
