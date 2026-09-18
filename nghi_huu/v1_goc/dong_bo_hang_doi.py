# -*- coding: utf-8 -*-
"""Dong bo hang doi voi thuc te truoc khi bat vong lap 24/7.

Ly do: mot so viec da duoc lam TAY ngoai vong lap (4 khang dinh Elliott chay thang
bang brain_co_che.py sang 09/08), va mot so viec chu du an da quyet dinh bo. Neu
khong dong bo thi vong lap se chay lai het - moi lan quet 28 thi truong, phi thi gio
va lam nghen nhung viec chua ai lam.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
HANG_DOI = HERE / "reports" / "BRAIN_hang_doi.parquet"

# Da chay tay bang brain_co_che.py --tat-ca, ket qua trong reports/BRAIN_CO_CHE.md
DA_LAM_TAY = {
    "elliott_cong_repaint": "28/28 thi truong, ve lai 93,9% - DA_DONG_SO ca chum dem song",
    "elliott_luan_phien": "6/7 nhom, z +0,83, p=0,125 - yeu, DANG_SANG",
    "elliott_song3_khong_ngan_nhat": "7/7 nhom, z +0,38, p=0,0156 - nhat quan nhung ti hon",
    "elliott_bat_doi_xung_5_3": "khong do duoc o D1 - thieu do phan giai, khong phai am tinh",
}

# Chu du an quyet dinh bo 09/08
BO = {
    "Ultima": "chu du an bo - khong mo terminal",
    "FXCE": "chu du an bo - khong mo terminal",
}


def main():
    hd = pd.read_parquet(HANG_DOI)
    n_doi = 0

    for mt, kq in DA_LAM_TAY.items():
        m = (hd["muc_tieu"] == mt) & (hd["loai"] == "sang")
        if m.any():
            hd.loc[m, "trang_thai"] = "xong"
            hd.loc[m, "ket_qua"] = kq
            hd.loc[m, "luc_cuoi"] = datetime.now().isoformat(timespec="seconds")
            n_doi += int(m.sum())

    for mt, ly_do in BO.items():
        m = (hd["muc_tieu"] == mt) & (hd["loai"] == "chi_phi")
        if m.any():
            hd.loc[m, "trang_thai"] = "bo"
            hd.loc[m, "ket_qua"] = ly_do
            n_doi += int(m.sum())

    hd.to_parquet(HANG_DOI, index=False)

    print(f"Cap nhat {n_doi} viec.\n")
    print("CON LAI TRONG HANG DOI:")
    con = hd[hd["trang_thai"].isin(["cho", "loi"])].sort_values("uu_tien", ascending=False)
    for _, r in con.iterrows():
        can_mang = r["loai"] in ("nguon", "cong_nghe")
        print(f"  [{r['uu_tien']:>3}] {r['loai']:<10} {r['muc_tieu']:<24} "
              f"{'<- LAY TU MANG' if can_mang else ''}")
    print(f"\nTong {len(con)} viec cho, trong do "
          f"{int(con['loai'].isin(['nguon','cong_nghe']).sum())} viec lay du lieu tu mang.")


if __name__ == "__main__":
    main()
