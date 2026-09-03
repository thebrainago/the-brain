# -*- coding: utf-8 -*-
"""SAN TOAN LUC moi nguon + doc song song + boc — mot lenh (03/09/2026)."""
import sys, json, time
sys.path.insert(0, '.')
from nhan import muc_tieu as MT, doc_song_song as DS, boc_llm as BL
from nhan import ngu_phap as NP, du_lieu as DU, so as SO

if __name__ == "__main__":
    def ghi(*a): print(*a, flush=True)
    t0 = time.time()
    tl0 = dict(SO.mot("SELECT COUNT(*) n FROM tai_lieu"))["n"]
    cc0 = len(NP.doc_kho())
    ghi(f"truoc: {tl0} tai lieu, {cc0} co che")

    ghi("\n-- LUONG 1a: san theo TAI SAN (toan luc 40) --")
    a = MT.san("US500CASH", ngan_sach_giay=900, toan_luc=40, in_ra=ghi)
    ghi(f"   -> {a['tai_lieu_moi']} tai lieu moi ({a['giay']}s)")

    ghi("\n-- LUONG 1b: san theo TEN HE THONG (toan luc 40) --")
    with MT.NoiTran(40):
        b = MT.san_he_pho_thong(ngan_sach_giay=900, in_ra=ghi)
    ghi(f"   -> {b['tai_lieu_moi']} tai lieu moi ({b['giay']}s)")

    ghi(f"\n-- DOC SONG SONG -- ({time.time()-t0:.0f}s)")
    r1 = DS.doc(gioi_han=800, luong=12, in_ra=ghi)
    ghi(json.dumps({k: v for k, v in r1.items() if k != 'theo_nguon'},
                   ensure_ascii=False))
    ghi(f"   theo nguon: {r1.get('theo_nguon')}")

    ghi(f"\n-- BOC -- ({time.time()-t0:.0f}s)")
    df = DU.nap('US500CASH', 'H4')
    r2 = BL.boc(gioi_han=400, luong=8, ghi_kho=True, df_kiem=df, in_ra=ghi)
    ghi(json.dumps(r2, ensure_ascii=False, indent=1))

    tl1 = dict(SO.mot("SELECT COUNT(*) n FROM tai_lieu"))["n"]
    ghi(f"\nTAI LIEU: {tl0} -> {tl1}   KHO CO CHE: {cc0} -> {len(NP.doc_kho())}"
        f"   tong {time.time()-t0:.0f}s")
