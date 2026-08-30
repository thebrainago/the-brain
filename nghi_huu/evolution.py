# -*- coding: utf-8 -*-
"""evolution.py - TRU EVOLUTION: lien tuc lam he thong tot hon.
   - Quet du lieu da luu (muc, cong_dong) de TRICH keyword/khai niem/ten moi.
   - Bo sung vao keyword bank (keywords_nguon.bo_sung) -> bank tu lon.
   - Ghi de xuat cai tien vao bang de_xuat_cai_tien (tru Banker/Seeker/Optimizer).
   - Quet github de tim giai phap cho van de da biet (tim_giai_phap tu bo_nao).

Chay:
  python evolution.py            : chay 1 vong evolution + luu
  python evolution.py --xem      : chi in, khong luu
"""
import sys, time, json, pathlib, re
import bo_nao
import keywords_nguon as kw

LAB = pathlib.Path(__file__).parent
CAC_NGUON_DOC = ("kham_pha", "telegram", "youtube", "reddit", "mql5")


STOP = set("THE AND FOR NOT YOU ARE WAS THIS THAT ALL ANY BUT CAN HOW AVAIC:/Users/SV STORE/Downloads/Research SP500/labLE JOINS "
           "ACTION ACTUALLY ADVANCED ANALYSIS APPLICATION BEST CHECK CLICK CLOSE CODE COM "
           "CONTACT CONTINUE CONTENT CURRENT DAY DEMO DOWN DOWNLOAD EACH END ENTRY EVER "
           "FILES FIRST FOLLOW FREE FROM GOOD HAVE HELP HIGH IMAGE INFO INVEST JOINS LEFT "
           "LEVEL LIKE LINK LOOK LOT LOW MAKE MANY MAY MORE MUCH NAME NEED NEWS NEXT OLD "
           "ONE ONLY OPEN OTHER OUR OVER PART PLEASE PRICE READ RIGHT SAVE SEE SHARE SOON "
           "TAKE THAN THEM THEN THERE THESE THING THIS TIME TOOLS TRADE TRADING TRUE USE "
           "USED VERY VIEW WANT WHAT WHEN WHERE WHICH WITH WILL WOULD YEAR YOUR ZONE".split())


def _trich_all_caps(text):
    """Trich cac cum ky tu in hoa (thuong la thuat ngu/ma - NFP, CPI, XAUUSD...)."""
    out = set()
    for m in re.finditer(r"\b[A-Z]{3,}\b", text or ""):
        t = m.group(0)
        if t not in STOP:
            out.add(t)
    return out


def _trich_handle(text):
    out = set()
    for m in re.finditer(r"@([A-Za-z0-9_]{3,})", text or ""):
        out.add(m.group(1))
    return out


def _trich_ten_hoa(text):
    """Trich cum 2-4 tu viet hoa chu cai dau (ten rieng / ten hieu)."""
    out = set()
    for m in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b", text or ""):
        out.add(m.group(1))
    return out


def mo_rong_keyword(con, gioi_han=400):
    """Quet cac muc co noi dung de trich keyword moi, bo sung vao bank.
    Tra (them_vi_mo, them_cong_dong, them_dang_doi)."""
    rows = con.execute(
        "SELECT nguon, COALESCE(ten,'') || ' ' || COALESCE((SELECT van_ban FROM noi_dung n "
        "WHERE n.muc_id=m.id LIMIT 1),'') AS txt FROM muc m "
        "WHERE nguon IN (%s) ORDER BY ngay DESC LIMIT ?" %
        ",".join("?" * len(CAC_NGUON_DOC)),
        list(CAC_NGUON_DOC) + [gioi_han]).fetchall()
    vi_mo, cong_dong, dang_doi = set(), set(), set()
    for nguon, txt in rows:
        vi_mo |= _trich_all_caps(txt)
        cong_dong |= _trich_handle(txt)
        dang_doi |= _trich_ten_hoa(txt)
    # them vao bank
    n1 = kw.bo_sung("vi_mo", "en", sorted(vi_mo))
    n2 = kw.bo_sung("cong_dong", "en", ["@" + h for h in sorted(cong_dong)])
    n3 = kw.bo_sung("dang_doi", "en", sorted(dang_doi))
    return (n1, n2, n3)


def de_xuat_cai_tien(con, noi_dung):
    """Ghi 1 de xuat cai tien vao bang de_xuat_cai_tien (se khong trung)."""
    con.execute(
        "INSERT OR IGNORE INTO de_xuat_cai_tien(van_de, nguyen_nhan, phuong_phap, "
        "nguon, muc_do, trang_thai, tao_luc) VALUES(?,?,?,?,?,?,?)",
        (noi_dung["van_de"], noi_dung.get("nguyen_nhan", ""),
         noi_dung.get("phuong_phap", ""), noi_dung.get("nguon", "evolution"),
         noi_dung.get("muc_do", 2), "MOI", time.time()))
    con.commit()


def main():
    con = bo_nao.mo_db()
    n1, n2, n3 = mo_rong_keyword(con)
    print(f"Evolution keyword: them vi_mo={n1}, cong_dong={n2}, dang_doi={n3}")
    print("Thong ke bo sung hien tai:", kw.thong_ke_bo_sung())
    if "--xem" in sys.argv:
        return
    # ghi de xuat: neu co the bo sung thi mo ta viec cai thien
    if n1 + n2 + n3:
        de_xuat_cai_tien(con, {
            "van_de": "Keyword bank can mo rong theo du lieu moi",
            "nguyen_nhan": "The gioi giao dich va ten nguoi/kenh thay doi lien tuc",
            "phuong_phap": "Evolution tu dong trich tu khoa moi tu muc/cong_dong va gop vao keywords_nguon",
            "nguon": "evolution", "muc_do": 1,
        })
        print("Da ghi de xuat cai tien vao DB.")
    print("XONG evolution.")


if __name__ == "__main__":
    main()
