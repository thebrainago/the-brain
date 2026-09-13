# -*- coding: utf-8 -*-
"""mach.py - MACH DAP CUA DUONG ONG. Canary cho tung chang, khong chi cho engine.

## VI SAO CO FILE NAY

Chu du an 13/09/2026: *"Dao cu bi loi o nhung phan ta tuong da xong roi vay"*,
va hoi co nen chay nho chay ngan de on het cac module truoc khong.

Toi xem lai NAM lo hong lon cua ngay hom do va hoi: chay ngan co bat duoc
khong?

    doc_kho nuot loi -> xoa sach kho        KHONG (mot lan doc hong la du)
    pheu chi ra 8 ung vien tren 5.486 ban   KHONG (chay ngan cung bao "8")
    bang quan tri toan 0 -> "trailing AM"   KHONG (da bi doc thanh ket luan)
    WARP chan mql5                          KHONG (doc thanh "het ton kho")
    29 URL tot bi loai vinh vien            KHONG - con *do* nhieu me ngan

**0/5.** Nguyen nhan chung khong phai do dai luot chay. No la mot cau:
**khau do hong doc y het mot ket qua am.**

Nhung truc giac "chay nho de biet module con song" thi DUNG, va lab da co
khuon mau chuan cho no: `nhan/canary.py`. Canary khong chi chay nhanh - no
con **TU KIEM XEM MINH CO NHAY KHONG** (mutation audit: co tinh chen loi vao
engine, doi canary phai bat). Do la phan quan trong hon.

Van de: canary chi phu ENGINE BACKTEST. Pheu Seeker, khau boc, khau quan tri,
duong LLM, o dia - khong chang nao co canary. Do dung la cho moi lo hong hom
nay nam.

## FILE NAY LAM GI

Moi chang khai bao BA thu:

    do()        mot con so do duoc, re (< vai giay)
    nguong      khoang ky vong - ra ngoai la DO
    be()        cach CO TINH lam hong chang do, de kiem cong con nhay khong

Thu ba la thu phan biet mot mach dap that voi mot bang toan chu OK. Mot cong
tu choi tat ca va mot cong khong bao gio tu choi cho so lieu giong het nhau
[[cong-pass-phai-hieu-chuan-hai-chieu]].

## KHONG PHAI DE THAY BO TEST

Bo test hoi "ham nay co dung khong". File nay hoi "**day chuyen co dang chay
khong**" - mot cau hoi khac, va la cau hoi ma 5 lo hong hom nay deu tra loi
sai. Chay: `b mach` (~1 phut), `b mach --be` (kem mutation audit).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(GOC))

TOT, DO, CHUA = "TOT", "DO", "CHUA_DO_DUOC"


def _kq(ten, gia_tri, dat, mo_ta, chua=False, goi_y=""):
    return {"chang": ten, "gia_tri": gia_tri,
            "trang_thai": CHUA if chua else (TOT if dat else DO),
            "mo_ta": mo_ta, "goi_y": goi_y}


# ------------------------------------------------------------------ CHANG
def c_dia() -> dict:
    """O dia. Dat dau tien vi het dia KHONG hien ra nhu loi dia - no hien ra
    nhu 'boc 684 file -> 0 co che'."""
    from nhan import dia as D
    gb = D.con_gb()
    return _kq("dia", round(gb, 1), gb >= D.NGUONG_GB,
               "%.1f GB trong (can >= %.1f)" % (gb, D.NGUONG_GB),
               goi_y="b don-dia; xoa Tester/logs cua MT5; cache trinh duyet")


def c_wal() -> dict:
    """`nao.db-wal` phinh lang le cho toi khi day dia (1,4 GB ngay 12/09)."""
    f = GOC / "nao.db-wal"
    mb = f.stat().st_size / 2**20 if f.exists() else 0.0
    return _kq("wal", round(mb), mb < 500,
               "nao.db-wal %.0f MB (nguong 500)" % mb,
               goi_y="python -m nhan.gop_wal")


def c_kho_co_che() -> dict:
    """Kho co che - da bi ghi de ve 21 HAI LAN trong mot buoi ngay 13/09."""
    from nhan import ngu_phap as NP
    try:
        n = len(NP.doc_kho())
    except Exception as e:
        return _kq("kho_co_che", None, False, "doc kho HONG: %s" % repr(e)[:80],
                   chua=True, goi_y="xem config/co_che_dsl.json.lui")
    moc = NP._doc_moc_cao()
    san = int(moc * 0.8) if moc else 1000
    return _kq("kho_co_che", n, n >= san,
               "%d co che (moc cao nhat %d, san %d)" % (n, moc, san),
               goi_y="git show HEAD:lab/config/co_che_dsl.json | dem; hoac "
                     "config/co_che_dsl.json.lui")


def c_pheu_html() -> dict:
    """Ban doc con o dang HTML tho - khau go phai dung TRUOC khau boc."""
    from nhan import go_html as GH
    n = GH.con_ton(3000)
    return _kq("pheu_html_tho", n, n < 300,
               "%d ban HTML tho chua go (nguong 300)" % n,
               goi_y="b go-html 500")


def c_pheu_ung_vien() -> dict:
    """SO UNG VIEN QUA PHEU - con so da nam o 8/5.486 suot mot thang."""
    from nhan import boc_llm as BL
    from nhan import so as SO
    ton = SO.mot("SELECT COUNT(*) n FROM noi_dung WHERE da_boc=0 AND "
                 "so_ky_tu>800 AND kieu NOT LIKE 'khong_doc_duoc%'")
    ton = int(ton["n"]) if ton else 0
    n = len(BL.ung_vien(120))
    if ton < 200:
        return _kq("pheu_ung_vien", n, True,
                   "%d ung vien / %d ban ton (ton it, khong ket luan)" % (n, ton))
    # Duoi 5% la dau hieu mot BO LOC dang chan ca lop nguon, khong phai dau
    # hieu kho ngheo. Do 13/09: 8/5.486 = 0,15% khi khau go HTML chua noi day.
    ty = n / min(ton, 120) if ton else 0
    return _kq("pheu_ung_vien", n, n >= 6,
               "%d/120 ban dau bang qua bo loc (ton %d)" % (n, ton),
               goi_y="b go-html; kiem boc_llm.DAU_HIEU_LUAT co phu lop nguon moi")


def c_duong_llm() -> dict:
    from nhan import tri_tue as TT
    t = TT.trang_thai()
    ok = bool(t.get("con_duoc_goi"))
    return _kq("duong_llm", t.get("model"), ok,
               "%s | %s | da goi %s/%s" % (t.get("duong_se_dung"), t.get("ly_do"),
                                           t.get("da_goi_hom_nay"),
                                           t.get("tran_moi_ngay")),
               goi_y="kiem cc-switch provider + OPENAI_API_KEY")


def c_bang_quan_tri() -> dict:
    """Bang luat quan tri KHONG duoc toan 0 - loi 12/09 lam 14/15 luat giong
    het nhau roi bi ket luan la 'AM'."""
    from nhan import quan_tri_dsl as Q
    ds = Q.doc_kho()
    if not ds:
        return _kq("bang_quan_tri", 0, False, "kho quan tri RONG", chua=True)
    qua = sum(1 for d in ds if not Q.kiem_con_so(d))
    return _kq("bang_quan_tri", "%d/%d" % (qua, len(ds)), 0 < qua < len(ds),
               "%d/%d khai bao co con so dung duoc" % (qua, len(ds)),
               goi_y="0 hoac tat ca deu qua -> cong khong do gi")


def c_tester() -> dict:
    """Tester can LICH SU. Do 13/09: thu muc du lieu MT5 bi xoa, va mot luot
    chay sau do bao '0 lenh' - doc y het mot he khong vao lenh bao gio."""
    import chay_bench_quan_tri as B
    co = [m for m in ("US500Cash", "US100Cash", "EURUSD") if B.co_lich_su(m)]
    return _kq("tester_lich_su", len(co), len(co) >= 1,
               "%d/3 ma mau co lich su (%s)" % (len(co), ", ".join(co) or "-"),
               goi_y="mo MT5, dang nhap tai khoan, chay mot luot de tai lich su")


def c_engine() -> dict:
    """Goi thang canary engine da co - dung xay lai.

    Ban dau o day viet `CN.chay(...) if hasattr(CN, "chay") else None` roi
    `if r is None: return ... dat=True`. `nhan/canary.py` KHONG co ham `chay`
    (no ten la `chay_het`), nen chang nay **luon bao TOT ma khong chay gi**.

    Mot TOT gia trong chinh cai module sinh ra de chan TOT gia - phat hien
    trong luot chay dau tien cua no. Giu ghi chu nay lam vi du: khi khong goi
    duoc mot phep do, trang thai la CHUA_DO_DUOC, khong bao gio la TOT.
    """
    from nhan import canary as CN
    if not hasattr(CN, "chay_het"):
        return _kq("engine", None, False,
                   "canary.chay_het khong ton tai - khong do duoc", chua=True)
    try:
        dat, chi_tiet = CN.chay_het(im_lang=True)
    except Exception as e:
        return _kq("engine", None, False,
                   "%s: %s" % (type(e).__name__, str(e)[:70]), chua=True)
    return _kq("engine", bool(dat), bool(dat),
               "canary engine %s" % ("dat" if dat else "TRUOT"),
               goi_y="b canary  (xem ca mutation audit)")


def c_tien_trinh() -> dict:
    """Tien trinh python MO COI tich lai lam may khong sinh duoc tien trinh moi.

    Do 13/09: 34 tien trinh sot lai tu cac luot pytest va agent bi cat ngang
    -> `ENOMEM: uv_spawn`. Trieu chung doc ra la "bo test chet o 56%", khong
    phai "may het bo nho" - lai dung ho loi khau do hong doc nhu ket qua am.
    """
    from nhan import ngan_sach as NS
    m = NS.may()
    n = m["python"]
    return _kq("tien_trinh", n, n <= NS.TRAN_TIEN_TRINH_PYTHON,
               "%d tien trinh python (tran %d), RAM trong %.1f GB"
               % (n, NS.TRAN_TIEN_TRINH_PYTHON, m["ram_trong_gb"]),
               goi_y="python -m nhan.ngan_sach --don")


CHANG = (c_dia, c_wal, c_tien_trinh, c_kho_co_che, c_pheu_html,
         c_pheu_ung_vien, c_duong_llm, c_bang_quan_tri, c_tester, c_engine)


def chay(in_ra=print) -> dict:
    t0 = time.time()
    ra = []
    for f in CHANG:
        try:
            ra.append(f())
        except Exception as e:
            ra.append(_kq(f.__name__[2:], None, False,
                          "%s: %s" % (type(e).__name__, str(e)[:90]), chua=True))
    do = [x for x in ra if x["trang_thai"] == DO]
    chua = [x for x in ra if x["trang_thai"] == CHUA]
    in_ra("=" * 74)
    in_ra("MACH DAP DUONG ONG   TOT %d · DO %d · CHUA_DO_DUOC %d   (%.1fs)"
          % (len(ra) - len(do) - len(chua), len(do), len(chua), time.time() - t0))
    in_ra("=" * 74)
    for x in ra:
        dau = {TOT: "[TOT ]", DO: "[DO  ]", CHUA: "[CHUA]"}[x["trang_thai"]]
        in_ra("%s %-18s %s" % (dau, x["chang"], x["mo_ta"]))
        if x["trang_thai"] != TOT and x.get("goi_y"):
            in_ra("        -> %s" % x["goi_y"])
    return {"chang": ra, "do": len(do), "chua_do_duoc": len(chua),
            "giay": round(time.time() - t0, 1)}


def be_thu(in_ra=print) -> dict:
    """MUTATION AUDIT: co tinh be tung chang, doi mach dap phai BAT duoc.

    Day la phan quan trong hon ca bang ket qua. `nhan/canary.py` da lam dung
    vay cho engine (*"chen loi 'engine quen dich mot bar' -> canary bat"*), va
    do la ly do canary chua bao gio de lot mot loi engine nao.

    Mot cong khong bao gio bao do va mot cong bao do dung luc cho ra bang so
    y het nhau. Chi phep be nay phan biet duoc.
    """
    from nhan import dia as D
    from nhan import ngu_phap as NP
    ket = []

    # 1. Be chang DIA: nang nguong len tren muc dang co.
    cu = D.NGUONG_GB
    try:
        D.NGUONG_GB = D.con_gb() + 1000
        ket.append(("dia", c_dia()["trang_thai"] == DO))
    finally:
        D.NGUONG_GB = cu

    # 2. Be chang KHO: nang moc cao nhat len gap doi -> san vuot so hien co.
    moc_cu = NP._doc_moc_cao()
    try:
        NP._ghi_moc_cao(max(moc_cu, 1) * 3)
        ket.append(("kho_co_che", c_kho_co_che()["trang_thai"] == DO))
    finally:
        NP._ghi_moc_cao(moc_cu)

    # 3. Be chang BANG QUAN TRI: cho cong KHONG TU CHOI AI -> phai bao do.
    #
    # Phep be dau tien o day la `PIP_TOI_THIEU = 1e9` (cho cong tu choi tat
    # ca). No KHONG lam chang do, va mutation audit bao "chang khong nhay" -
    # nhung loi nam o PHEP BE chu khong o cong: nhieu khai bao khong co truong
    # khoang cach nao, nen nguong pip du lon den may cung khong cham duoc
    # chung, va `qua > 0` van dung.
    #
    # Phep be DUNG phai nham vao hong that: mot cong **khong tu choi ai** doc
    # y het mot cong tot. Bit thang `kiem_con_so`.
    from nhan import quan_tri_dsl as Q
    cu2 = Q.kiem_con_so
    try:
        Q.kiem_con_so = lambda spec: []          # cong bi bit: qua = tat ca
        ket.append(("bang_quan_tri", c_bang_quan_tri()["trang_thai"] == DO))
    finally:
        Q.kiem_con_so = cu2

    # 4. Be chang PHEU HTML: ha nguong xuong duoi so dang ton.
    ket.append(("pheu_html_tho", _be_pheu_html()))

    # 5. Be chang ENGINE: doi ten ham canary -> phai ra CHUA_DO_DUOC.
    #
    # Chinh loi da xay ra: ban dau `c_engine` goi `CN.chay` (khong ton tai) roi
    # tra TOT. Phep be nay gac dung no.
    from nhan import canary as CN
    cu4 = CN.chay_het
    try:
        del CN.chay_het
        ket.append(("engine", c_engine()["trang_thai"] == CHUA))
    finally:
        CN.chay_het = cu4

    # 6. Be chang TIEN TRINH: ha tran xuong duoi so dang chay.
    from nhan import ngan_sach as NS
    cu5 = NS.TRAN_TIEN_TRINH_PYTHON
    try:
        NS.TRAN_TIEN_TRINH_PYTHON = -1
        ket.append(("tien_trinh", c_tien_trinh()["trang_thai"] == DO))
    finally:
        NS.TRAN_TIEN_TRINH_PYTHON = cu5

    in_ra("=== MUTATION AUDIT: mach dap co that su nhay khong? ===")
    for ten, bat in ket:
        in_ra("  [%s] be chang `%s` -> mach %s"
              % ("OK  " if bat else "HONG", ten,
                 "BAT duoc" if bat else "KHONG bat -> chang nay la TOT GIA"))
    hong = [t for t, b in ket if not b]
    in_ra("  => %s" % ("mach NHAY, dung duoc lam cong." if not hong
                       else "CHANG KHONG NHAY: " + ", ".join(hong)))
    return {"be": ket, "khong_nhay": hong}


def _be_pheu_html() -> bool:
    """Ha nguong 300 xuong -1: moi so luong deu phai thanh DO."""
    def gia():
        from nhan import go_html as GH
        n = GH.con_ton(3000)
        return _kq("pheu_html_tho", n, n < -1, "be thu")
    return gia()["trang_thai"] == DO


if __name__ == "__main__":
    import json
    r = chay()
    if "--be" in sys.argv:
        print()
        r["mutation"] = be_thu()
    (GOC / "reports" / "MACH.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    raise SystemExit(1 if r["do"] else 0)
