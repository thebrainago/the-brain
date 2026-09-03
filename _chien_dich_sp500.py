# -*- coding: utf-8 -*-
"""Chien dich san theo muc tieu cho US500CASH — 03/09/2026."""
import sys
sys.path.insert(0, '.')
from nhan import muc_tieu as MT

if __name__ == "__main__":
    def ghi(*a):
        print(*a, flush=True)
    r = MT.chien_dich("US500CASH", ngan_sach_san=1500, ngan_sach_boc=900, in_ra=ghi)
    ghi("\n=== TONG KET ===")
    ghi(f"tai lieu moi : {r['san']['tai_lieu_moi']}")
    ghi(f"nguon chay   : {r['san']['nguon_chay']}")
    ghi(f"co che       : {r['co_che_truoc']} -> {r['co_che_sau']} (+{r['co_che_them']})")
    ghi(f"nguon bo qua vi loi: {r['san']['nguon_bo_qua_vi_loi']}")
