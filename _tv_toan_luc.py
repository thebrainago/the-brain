# -*- coding: utf-8 -*-
"""Hoi TradingView bang TOAN BO tu khoa he thong pho thong, roi boc.

Nut that do duoc 03/09/2026: `TV_SO_TRUY_VAN_MOI_LUOT = 3` — TradingView moi
duoc hoi 15 tu khoa tu truoc den nay. Moi tu khoa mang ve ~31 bai, 39% co ma
mo. 27/30 ten he thong pho thong CHUA bao gio duoc hoi.
"""
import sys, json, time
sys.path.insert(0, '.')
from tru import seeker as SK
from nhan import muc_tieu as MT, boc_llm as BL, ngu_phap as NP, du_lieu as DU, so as SO

if __name__ == "__main__":
    def ghi(*a): print(*a, flush=True)
    t0 = time.time()
    truoc_tl = dict(SO.mot("SELECT COUNT(*) n FROM tai_lieu WHERE nguon='tradingview_pine'"))["n"]
    truoc_cc = len(NP.doc_kho())
    ghi(f"truoc: {truoc_tl} bai tradingview, {truoc_cc} co che")

    # Noi tran truy van CHO RIENG luot nay (khong sua file cau hinh).
    SK.TV_SO_TRUY_VAN_MOI_LUOT = 40
    tk = list(MT.HE_THONG_PHO_THONG) + list(MT.TU_KHOA_THEO_MA["US500CASH"])
    ghi(f"hoi {len(tk)} tu khoa (tran nang 3 -> 40 cho luot nay)")

    tong = 0
    for vong in range(3):
        ds = SK.n_tradingview_pine(tk)
        moi = SK.luu_tai_lieu("tradingview_pine", ds)
        tong += moi
        ghi(f"  vong {vong+1}: lay ve {len(ds)}, moi {moi}  ({time.time()-t0:.0f}s)")
        if moi == 0:
            break

    sau_tl = dict(SO.mot("SELECT COUNT(*) n FROM tai_lieu WHERE nguon='tradingview_pine'"))["n"]
    co_ma = dict(SO.mot("SELECT COUNT(*) n FROM tai_lieu t JOIN noi_dung nd "
                        "ON nd.tai_lieu_id=t.id WHERE t.nguon='tradingview_pine'"))["n"]
    ghi(f"  -> tradingview: {truoc_tl} -> {sau_tl} bai, {co_ma} co ban doc (ma Pine)")

    ghi(f"\n-- BOC -- ({time.time()-t0:.0f}s)")
    df = DU.nap('US500CASH', 'H4')
    r = BL.boc(gioi_han=400, luong=8, ghi_kho=True, df_kiem=df, in_ra=ghi)
    ghi(json.dumps(r, ensure_ascii=False, indent=1))
    ghi(f"\nKHO CO CHE: {truoc_cc} -> {len(NP.doc_kho())}   tong {time.time()-t0:.0f}s")
