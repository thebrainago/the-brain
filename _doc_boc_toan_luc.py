# -*- coding: utf-8 -*-
"""DOC song song (uu tien nguon ma) roi BOC — toan luc (03/09/2026)."""
import sys, json, time
sys.path.insert(0, '.')
from nhan import doc_song_song as DS, boc_llm as BL, ngu_phap as NP, du_lieu as DU

if __name__ == "__main__":
    def ghi(*a): print(*a, flush=True)
    t0 = time.time()
    ghi("-- DOC SONG SONG --")
    r1 = DS.doc(gioi_han=500, luong=12, in_ra=ghi)
    ghi(json.dumps(r1, ensure_ascii=False, indent=1))
    ghi(f"\n-- BOC -- ({time.time()-t0:.0f}s)")
    truoc = len(NP.doc_kho())
    df = DU.nap('US500CASH', 'H4')
    r2 = BL.boc(gioi_han=300, luong=8, ghi_kho=True, df_kiem=df, in_ra=ghi)
    ghi(json.dumps(r2, ensure_ascii=False, indent=1))
    ghi(f"\nKHO CO CHE: {truoc} -> {len(NP.doc_kho())}   tong {time.time()-t0:.0f}s")
