# -*- coding: utf-8 -*-
"""tinh_trang.py - In tinh trang hien tai de biet dang lam viec toi dau."""
import sys


if __name__ == "__main__":
    # Bo than script vao chot nay: truoc day chi can import module la
    # chay het ca bai quet/ghi bao cao, ke ca khi nguoi goi chi muon
    # dung mot ham trong file.

    sys.path.insert(0, r"C:\Users\SV STORE\Downloads\Research SP500\lab")
    from nhan import so as SO
    from nhan import doc_trinh_duyet as DT

    print("CDP trinh duyet:", DT.cdp_dang_chay())
    print("tai_lieu:", SO.mot("SELECT COUNT(*) n FROM tai_lieu")["n"])
    bat = SO.nhieu("SELECT ma, thu_hoach FROM nguon WHERE trang_thai=? ORDER BY uu_tien, ma", "BAT")
    print("nguon BAT (%d):" % len(bat))
    for r in bat:
        print("   - %-16s thu_hoach=%s" % (r["ma"], r["thu_hoach"]))
    print()
    print("Ho so lam viec tiep:  lab/GHI_NHO_LAM_VIEC.md")
    print("Lenh tiep:            TIEP_TUC.cmd   (mo terminal, go: TIEP_TUC)")

