# -*- coding: utf-8 -*-
"""GitHub toan luc: san chien luoc le -> doc song song -> boc (03/09/2026)."""
import sys, json, time
sys.path.insert(0, '.')
from tru import seeker as SK
from nhan import muc_tieu as MT, doc_song_song as DS, boc_llm as BL
from nhan import ngu_phap as NP, du_lieu as DU, so as SO

if __name__ == "__main__":
    def ghi(*a): print(*a, flush=True)
    t0 = time.time()
    tl0 = dict(SO.mot("SELECT COUNT(*) n FROM tai_lieu WHERE nguon='github'"))["n"]
    cc0 = len(NP.doc_kho())
    ghi(f"truoc: {tl0} repo github, {cc0} co che")

    tk = list(MT.HE_THONG_PHO_THONG) + list(MT.TU_KHOA_THEO_MA["US500CASH"])
    ghi(f"\n-- SAN GITHUB: {len(tk)} tu khoa x 5 ngon ngu x 3 cach xep --")
    with MT.NoiTran(50):
        tong = 0
        for vong in range(3):
            ds = SK.n_github(tk)
            moi = SK.luu_tai_lieu("github", ds)
            tong += moi
            ghi(f"  vong {vong+1}: lay ve {len(ds)}, moi {moi}  ({time.time()-t0:.0f}s)")
            if len(ds) == 0:
                break
    tl1 = dict(SO.mot("SELECT COUNT(*) n FROM tai_lieu WHERE nguon='github'"))["n"]
    ghi(f"   -> github: {tl0} -> {tl1} repo")

    ghi(f"\n-- DOC SONG SONG (chi github) -- ({time.time()-t0:.0f}s)")
    r1 = DS.doc(gioi_han=400, luong=12, chi_nguon=["github"], in_ra=ghi)
    ghi(json.dumps({k: v for k, v in r1.items() if k != 'theo_nguon'}, ensure_ascii=False))

    ghi(f"\n-- BOC -- ({time.time()-t0:.0f}s)")
    df = DU.nap('US500CASH', 'H4')
    r2 = BL.boc(gioi_han=250, luong=8, ghi_kho=True, df_kiem=df, in_ra=ghi)
    ghi(json.dumps(r2, ensure_ascii=False, indent=1))
    ghi(f"\nKHO CO CHE: {cc0} -> {len(NP.doc_kho())}   tong {time.time()-t0:.0f}s")
