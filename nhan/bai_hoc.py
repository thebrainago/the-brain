# -*- coding: utf-8 -*-
"""bai_hoc.py - SO BAI HOC: he tu tra loi duoc "cai nay da thu chua".

## Van de no giai

`hethong.txt` neu dich danh mot module: *"bo tong ket de rut ra chien luoc, neu
co co che nao tim ra huong di moi lap tuc ghi lai va phan tich... tim ra huong
di nen tranh huong khong nen tiep tuc"*. Do 11/09/2026: grep toan bo `nhan/`,
`tru/`, `qwen/` ra **0 file**.

Chuc nang do dang song o hai cho, ca hai deu ngoai tam voi cua he:
  - 130 file memory cua Claude - nam trong profile nguoi dung, KHONG trong repo.
    Mat phien la mat, va `evolution.py` khong bao gio doc duoc.
  - `NHAT_KY.md` / cac `BAO_CAO_*.md` - van xuoi, khong tra cuu duoc bang may.

Va 1.255 dong FAIL trong `ket_qua` thi khong ai hoi lai bao gio: he san sang
dang ky lai mot gia thuyet cung ho da chet ba lan, vi khong co cho nao de hoi.

## Ba loai the, khong tron

    bay_do_luong      mot phep do tung noi doi. VI DU LA BAT BUOC.
    huong_nen_tranh   mot huong da di va da am. Phai co BANG CHUNG (so, khong loi van).
    huong_dang_mo     mot huong co dau hieu nhung chua ket luan.
    quy_tac_nguoi_dung  chu du an da chot. Khong duoc suy dien lai.
    su_that_tai_san   mot su that do duoc ve mot ma / mot lop tai san.

## Ranh gioi

Module nay KHONG phan xet. No khong noi "gia thuyet nay se that bai" - no tra ve
nhung the LIEN QUAN va de nguoi (hoac cong) quyet dinh. Mot so cai co tri nho
nhung khong co quyen phu quyet; nham lan hai thu do la cach nhanh nhat de mot he
ngung hoc cai moi.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import so as SO
else:
    from . import so as SO

LOAI = ("bay_do_luong", "huong_nen_tranh", "huong_dang_mo",
        "quy_tac_nguoi_dung", "su_that_tai_san")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS bai_hoc(
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  ma        TEXT UNIQUE,
  loai      TEXT NOT NULL,
  tieu_de   TEXT NOT NULL,
  noi_dung  TEXT NOT NULL,
  bang_chung TEXT,
  ngay      TEXT,
  nguon     TEXT,
  tu_khoa   TEXT,
  lien_quan TEXT
);
CREATE INDEX IF NOT EXISTS ix_bai_hoc_loai ON bai_hoc(loai);
"""

#: Tu qua pho bien de phan biet the nay voi the kia. Bo truoc khi lam khoa tim.
_RONG = set("""va la cua co khong mot trong khi nay do cho den tu voi nhu ra vao
the nen thi ma cai bi duoc phai se da dang cung hon rat chi con neu hay tren
duoi theo the_nao sau truoc lai cac nhung moi tat ca the_he
the a an and are as at be but by for from has have in is it its of on or that
this to was were will with not no be been we you they he she our your their
""".split())


def _khoi_tao() -> None:
    with SO.ket_noi() as cn:
        cn.executescript(_SCHEMA)


def _khoa(s: str) -> set[str]:
    """Tu khoa cua mot doan - bo dau tieng Viet va tu rong."""
    s = s.lower()
    for a, b in (("àáảãạăằắẳẵặâầấẩẫậ", "a"), ("èéẻẽẹêềếểễệ", "e"),
                 ("ìíỉĩị", "i"), ("òóỏõọôồốổỗộơờớởỡợ", "o"),
                 ("ùúủũụưừứửữự", "u"), ("ỳýỷỹỵ", "y"), ("đ", "d")):
        for c in a:
            s = s.replace(c, b)
    return {t for t in re.findall(r"[a-z0-9_]{3,}", s) if t not in _RONG}


def them(ma: str, loai: str, tieu_de: str, noi_dung: str,
         bang_chung: str = "", ngay: str = "", nguon: str = "",
         lien_quan: list[str] | None = None) -> dict:
    """Them mot the. Tra `{nhan, ly_do}` - KHONG nem loi len nguoi goi.

    Hai chot, ca hai deu tu bai hoc cu:
      - `huong_nen_tranh` va `bay_do_luong` PHAI co bang chung. Mot the "huong X
        khong an" ma khong kem so do se thanh mot dieu cam khong ai kiem lai
        duoc - va he se ngung thu X mai mai vi mot cau noi.
      - `ma` la khoa duy nhat: ghi de thay vi nhan doi, de chay lai bo nhap
        khong sinh 3 ban cua cung mot the.
    """
    _khoi_tao()
    if loai not in LOAI:
        return {"nhan": False, "ly_do": [f"loai khong biet: {loai!r}; phai la {LOAI}"]}
    if loai in ("huong_nen_tranh", "bay_do_luong") and not bang_chung.strip():
        return {"nhan": False, "ly_do": [
            f"the loai {loai!r} phai co `bang_chung` - mot con so hoac mot phep do. "
            f"Khong co thi day la mot y kien, khong phai mot bai hoc."]}
    if len(noi_dung.strip()) < 20:
        return {"nhan": False, "ly_do": ["`noi_dung` qua ngan de tra cuu lai duoc"]}

    tu = " ".join(sorted(_khoa(f"{tieu_de} {noi_dung} {bang_chung}")))
    with SO.ket_noi() as cn:
        cn.execute(
            "INSERT INTO bai_hoc(ma,loai,tieu_de,noi_dung,bang_chung,ngay,nguon,"
            "tu_khoa,lien_quan) VALUES(?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(ma) DO UPDATE SET loai=excluded.loai,tieu_de=excluded.tieu_de,"
            "noi_dung=excluded.noi_dung,bang_chung=excluded.bang_chung,"
            "ngay=excluded.ngay,nguon=excluded.nguon,tu_khoa=excluded.tu_khoa,"
            "lien_quan=excluded.lien_quan",
            (ma, loai, tieu_de, noi_dung, bang_chung, ngay, nguon, tu,
             json.dumps(lien_quan or [], ensure_ascii=False)))
    return {"nhan": True, "ly_do": []}


def tra(cau_hoi: str, so_the: int = 5, loai: str | None = None) -> list[dict]:
    """Tra cuu the lien quan. Xep theo so tu khoa trung, khong theo thu tu them.

    Day la ham `b da-thu` goi. No tra ve THE, khong tra ve phan xet.
    """
    _khoi_tao()
    kh = _khoa(cau_hoi)
    if not kh:
        return []
    with SO.ket_noi() as cn:
        q = "SELECT * FROM bai_hoc"
        ts: tuple = ()
        if loai:
            q += " WHERE loai = ?"
            ts = (loai,)
        dong = cn.execute(q, ts).fetchall()
    # IDF: mot tu hiem dang gia hon mot tu pho bien. Khong co no thi "chi so"
    # (co trong gan nua so the) keo ngang voi "swap" (co trong ba the) - do that
    # 11/09: cau hoi "phi qua dem CFD chi so" cho the IBS len TRUOC the phi qua
    # dem, chi vi the IBS ngan hon.
    from math import log
    df: dict[str, int] = {}
    for d in dong:
        for t in set((d["tu_khoa"] or "").split()):
            df[t] = df.get(t, 0) + 1
    N = max(len(dong), 1)

    ra = []
    for d in dong:
        t = set((d["tu_khoa"] or "").split())
        chung = kh & t
        if not chung:
            continue
        # Chia cho can bac hai so tu cua the: the DAI khong duoc thiet chi vi dai.
        diem = sum(log(1 + N / (1 + df.get(w, 0))) for w in chung) / max(len(t), 1) ** 0.5
        ra.append({"ma": d["ma"], "loai": d["loai"], "tieu_de": d["tieu_de"],
                   "noi_dung": d["noi_dung"], "bang_chung": d["bang_chung"],
                   "ngay": d["ngay"], "nguon": d["nguon"],
                   "diem": round(diem, 4),
                   "tu_chung": sorted(chung, key=lambda w: df.get(w, 0))[:8]})
    ra.sort(key=lambda x: -x["diem"])
    return ra[:so_the]


def lien_quan(gia_thuyet: dict, so_the: int = 3) -> list[dict]:
    """The lien quan toi MOT gia thuyet sap dang ky.

    `quantlab` goi ham nay TRUOC khi dang ky. No khong chan - no chi dua ra
    nhung lan truoc he da di huong nay, de cai gi lap lai thi lap lai CO Y THUC.
    """
    phan = [str(gia_thuyet.get(k, "")) for k in
            ("ho", "co_che", "ten", "template", "tai_san", "khung")]
    return tra(" ".join(p for p in phan if p), so_the=so_the)


def dem() -> dict:
    _khoi_tao()
    with SO.ket_noi() as cn:
        t = cn.execute("SELECT count(*) c FROM bai_hoc").fetchone()["c"]
        theo = {r["loai"]: r["c"] for r in
                cn.execute("SELECT loai, count(*) c FROM bai_hoc GROUP BY loai")}
    return {"tong": t, "theo_loai": theo}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for t in tra(" ".join(sys.argv[1:])):
            print(f"[{t['loai']}] {t['tieu_de']}  (diem {t['diem']})")
            print(f"   {t['noi_dung'][:200]}")
            if t["bang_chung"]:
                print(f"   bang chung: {t['bang_chung'][:160]}")
    else:
        print(json.dumps(dem(), ensure_ascii=False))
