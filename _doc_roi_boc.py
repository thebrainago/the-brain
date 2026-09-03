# -*- coding: utf-8 -*-
"""DOC TOAN VAN roi BOC — noi nốt chặng bị thiếu giữa san va boc (03/09/2026).

`muc_tieu.san*` ghi vao bang `tai_lieu`. `boc_llm.ung_vien` doc tu bang
`noi_dung`. Giua hai bang la `seeker.doc_toan_van` — neu khong chay thi tai
lieu moi san ve nam ngoai tam voi cua bo boc, va bao cao se noi "0 co che"
trong khi that ra chua ai mo bai nao ra.
"""
import sys, json, time
sys.path.insert(0, '.')
from tru import seeker as SK
from nhan import boc_llm as BL, ngu_phap as NP, du_lieu as DU, so as SO

if __name__ == "__main__":
    def ghi(*a): print(*a, flush=True)
    t0 = time.time()
    chua = dict(SO.mot(
        "SELECT COUNT(*) n FROM tai_lieu t LEFT JOIN noi_dung n ON n.tai_lieu_id=t.id "
        "WHERE n.id IS NULL"))["n"]
    ghi(f"tai lieu CHUA co ban doc: {chua}")

    ghi("-- DOC TOAN VAN --")
    tong = 0
    for vong in range(6):
        r = SK.doc_toan_van(gioi_han=60, ngan_sach_giay=240)
        n = r.get("doc_duoc", 0)
        tong += n
        ghi(f"  vong {vong+1}: doc duoc {n}, that bai {r.get('that_bai',0)} "
            f"({time.time()-t0:.0f}s)")
        if n == 0:
            break
    ghi(f"  -> tong doc duoc {tong} ban ({time.time()-t0:.0f}s)")

    ghi("-- BOC --")
    truoc = len(NP.doc_kho())
    df = DU.nap('US500CASH', 'H4')
    r = BL.boc(gioi_han=200, luong=8, ghi_kho=True, df_kiem=df, in_ra=ghi)
    ghi(json.dumps(r, ensure_ascii=False, indent=1))
    ghi(f"KHO CO CHE: {truoc} -> {len(NP.doc_kho())}")
