# -*- coding: utf-8 -*-
"""evo.py - THE EVO: giam sat hieu suat tung module, cat nghia, de xuat.

Tru thu BA trong `SO_DO_HE_THONG.txt`:

    "Day la module tong quan, giam sat hieu suat cua tung module ben tren de tim
     ra van de => Bao cao va cat nghia van de + de xuat giai phap de gui cho AI
     giam sat tim cach sua"

## MOT THUOC DO XAU HON KHONG CO THUOC DO

Trong MOT phien (12/09/2026) bo do cua chinh du an nay bao sai BA lan:

    "9 nguon SEEKER la ma chet"     -> chung duoc goi GIAN TIEP qua `NGUON[ma]`
    "567 ung vien bi ket"           -> bang do la NHAT KY chi-ghi-them, dung thiet ke
    "43 co che nem KhungThieuGio"   -> toi chay chung tren D1 trong khi he da
                                       chuan hoa H1 tu lau

Ca ba lan deu cung mot kieu: **doan kien truc thay vi doc quy uoc he da chot**.
Nen file nay co mot rang buoc cung hon binh thuong:

  * Moi chi so phai phan biet ba trang thai: **TOT · XAU · CHUA_DO**. Khong co
    du lieu thi noi "chua do", KHONG duoc quy ve "xau" (memory
    `ket-luan-am-phai-phan-biet-chua-do`).
  * Moi ket luan "xau" phai kem BANG CHUNG DEM DUOC, khong duoc la suy dien.
  * Moi de xuat phai la mot LENH CHAY DUOC, khong phai mot loi khuyen.

## CO HAI "EVO" - DAY LA CAI NAO

Do 12/09/2026, sau khi da viet xong file nay: `tru/evolution.py` **DA LA MOT
EVO** (1.365 dong). Toi khong kiem truoc khi xay - lan thu BA trong mot ngay
mac loi do (`uu_tien.py`, `noi_sinh.py`, roi cai nay). Chung KHONG trung nhau,
nhung ranh gioi phai duoc viet ra, khong thi se co cai thu ba:

    tru/evolution.py   suc khoe DAY CHUYEN nghien cuu: FDR, ty le null lot,
                       luc cua cong, watchdog, dia. Chay trong `dieu_phoi`
                       moi 900 giay. **Va no la noi DUY NHAT duoc ghi van de**
                       (`bao_van_de_gop` khu trung lap theo NOI DUNG).

    nhan/evo.py        (file nay) suc khoe TUNG MODULE: kho co che, tuoi tung
                       ho so, hang doi viec, tien trinh mo coi. Kem CAT NGHIA
                       va DE XUAT CHAY DUOC, va bao ra Telegram khi tap van de
                       DOI. Chay tay (`b evo`) hoac theo bang viec qwen.

Mot cai hoi "day chuyen co chay khong", cai kia hoi "module nao dang cu/hong".

## DOC GI

Chi doc thu da co san - khong chay lai phep do nao, khong ton CPU:
    so SQLite      nhip do cua tung khau (tai lieu, boc, ung vien, ket qua)
    reports/*.json san pham moi module de lai, kem thoi gian
    config/*.json  kho co che, hang doi viec

Chay:  python -m nhan.evo            bao cao
       python -m nhan.evo --ghi      bao cao + ghi van de vao so
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

BAO_CAO = LAB / "reports" / "EVO_SUC_KHOE.md"

TOT, XAU, CHUA_DO = "TOT", "XAU", "CHUA_DO"


def _mot(cau: str, mac_dinh=None):
    try:
        from nhan import so as SO
        r = SO.mot(cau)
        return list(r.values())[0] if r else mac_dinh
    except Exception:
        return mac_dinh


def _tuoi_tep(p: Path) -> float | None:
    """So gio ke tu lan ghi cuoi. None neu chua co tep."""
    try:
        return (time.time() - p.stat().st_mtime) / 3600.0
    except Exception:
        return None


def _chi_so(ten: str, mo_ta: str, gia_tri, trang_thai: str,
            bang_chung: str = "", de_xuat: str = "") -> dict:
    return {"ten": ten, "mo_ta": mo_ta, "gia_tri": gia_tri,
            "trang_thai": trang_thai, "bang_chung": bang_chung,
            "de_xuat": de_xuat}


# ------------------------------------------------------------------- SEEKER
def suc_khoe_seeker() -> list[dict]:
    ra = []
    tl = _mot("SELECT COUNT(*) AS c FROM tai_lieu")
    nd = _mot("SELECT COUNT(*) AS c FROM noi_dung")
    if tl is None:
        ra.append(_chi_so("seeker.ton_kho", "tai lieu da thu thap", None, CHUA_DO,
                          "khong doc duoc bang tai_lieu"))
    else:
        ty = (nd or 0) / max(tl, 1)
        ra.append(_chi_so(
            "seeker.ty_le_doc", "tai lieu da LAY DUOC TOAN VAN", round(ty, 3),
            TOT if ty >= 0.5 else XAU,
            "%d/%d tai lieu co ban van" % (nd or 0, tl),
            "" if ty >= 0.5 else
            "python -m nhan.day_chuyen boc   # lay toan van cho phan con lai"))

    # Nguon nao khong ra gi. KHONG goi la "nguon chet" neu no CHUA TUNG chay -
    # do la hai chuyen khac nhau.
    try:
        from nhan import so as SO
        rows = SO.nhieu(
            "SELECT n.ma AS ma, COUNT(t.id) AS so_tl FROM nguon n "
            "LEFT JOIN tai_lieu t ON t.nguon = n.ma GROUP BY n.ma")
        rong = [r["ma"] for r in rows if (r["so_tl"] or 0) == 0]
        ra.append(_chi_so(
            "seeker.nguon_rong", "nguon chua mang ve tai lieu nao",
            len(rong), TOT if len(rong) <= 3 else XAU,
            "rong: %s" % ", ".join(sorted(rong)[:10]),
            "python -m nhan.kham_pha_nguon   # do lai tung nguon, tach 'chan' "
            "khoi 'chua chay'" if len(rong) > 3 else ""))
    except Exception:
        ra.append(_chi_so("seeker.nguon_rong", "nguon chua ra gi", None, CHUA_DO,
                          "khong doc duoc bang nguon"))
    return ra


# ----------------------------------------------------------------- QUANTLAB
#: Ho so nao chay bang lenh gi. Khong doan tu ten - `to_hop` va `suy_nguoc`
#: khong theo khuon `nhan.ho_so_*`, va mot de xuat chay sai lenh thi vo dung.
_LENH_CHAY = {
    "song": "python -m nhan.ho_so_song quet D1 10",
    "mua_vu": "python -m nhan.ho_so_mua_vu quet D1 10",
    "tuong_quan": "python -m nhan.ho_so_tuong_quan D1",
    "suy_nguoc": "python -m nhan.suy_nguoc quet D1 10",
    "to_hop": "python -m nhan.to_hop D1 H4 --tien-trinh 10",
}


def suc_khoe_quantlab() -> list[dict]:
    ra = []
    try:
        from nhan import ngu_phap as NP
        kho = NP.doc_kho()
        co_co_che = sum(1 for s in kho if str(s.get("co_che") or "").strip())
        ty = co_co_che / max(len(kho), 1)
        ra.append(_chi_so(
            "quantlab.kho_co_che", "co che trong kho", len(kho),
            TOT if len(kho) >= 500 else XAU,
            "%d co che, %d (%.0f%%) co truong `co_che` giai thich"
            % (len(kho), co_co_che, ty * 100)))
    except Exception as e:
        ra.append(_chi_so("quantlab.kho_co_che", "co che trong kho", None,
                          CHUA_DO, "khong doc duoc kho: %s" % e))

    # HO SO TAI SAN: bon ho so Q1-Q3 co con moi khong
    for ten, tep, gio in (("song", "HO_SO_SONG.json", 24 * 14),
                          ("mua_vu", "HO_SO_MUA_VU.json", 24 * 14),
                          ("tuong_quan", "HO_SO_TUONG_QUAN_D1.json", 24 * 14),
                          ("suy_nguoc", "SUY_NGUOC.json", 24 * 14),
                          ("to_hop", "TO_HOP.json", 24 * 7)):
        t = _tuoi_tep(LAB / "reports" / tep)
        if t is None:
            ra.append(_chi_so("quantlab.ho_so_%s" % ten, "ho so %s" % ten, None,
                              CHUA_DO, "chua co %s" % tep,
                              _LENH_CHAY.get(ten, "python -m nhan.ho_so_%s quet D1" % ten)))
        else:
            ra.append(_chi_so(
                "quantlab.ho_so_%s" % ten, "tuoi ho so %s (gio)" % ten,
                round(t, 1), TOT if t <= gio else XAU,
                "%s ghi lan cuoi cach day %.0f gio" % (tep, t),
                "" if t <= gio else _LENH_CHAY.get(
                    ten, "python -m nhan.ho_so_%s quet D1" % ten)))

    # DUONG RA TIEN: co bao nhieu ket qua da cham cong, va bao nhieu qua
    kq = _mot("SELECT COUNT(*) AS c FROM ket_qua")
    if kq is None:
        ra.append(_chi_so("quantlab.ket_qua", "ket qua da cham", None, CHUA_DO,
                          "khong doc duoc bang ket_qua"))
    else:
        ra.append(_chi_so("quantlab.ket_qua", "ket qua da cham cong", kq,
                          TOT if kq > 0 else XAU, "%d dong trong ket_qua" % kq))
    return ra


# --------------------------------------------------------------------- EVO
def suc_khoe_evo() -> list[dict]:
    ra = []
    # DEM DUNG TRANG THAI THAT. Ban cu hoi `trang_thai != 'DONG'`, nhung quy
    # uoc cua `tru/evolution.py` la **MO / DA_SUA** - khong co 'DONG' nao ca.
    # Nen 78 van de DA SUA bi dem la "chua dong" va chi so nay bao XAU vinh
    # vien: 91 mo trong khi that ra 13. Mot bo giam sat keu oan thi nguoi ta
    # tat no di, va do la cach mat ca bo giam sat.
    vd = _mot("SELECT COUNT(*) AS c FROM van_de WHERE trang_thai = 'MO'")
    da = _mot("SELECT COUNT(*) AS c FROM van_de WHERE trang_thai = 'DA_SUA'")
    ra.append(_chi_so("evo.van_de_mo", "van de con MO", vd,
                      TOT if (vd or 0) <= 30 else XAU,
                      "%s MO / %s da sua" % (vd, da)) if vd is not None else
              _chi_so("evo.van_de_mo", "van de con MO", None, CHUA_DO, ""))
    bh = _mot("SELECT COUNT(*) AS c FROM bai_hoc")
    ra.append(_chi_so("evo.bai_hoc", "bai hoc da rut", bh,
                      TOT if (bh or 0) >= 50 else XAU,
                      "%s the bai hoc" % bh) if bh is not None else
              _chi_so("evo.bai_hoc", "bai hoc da rut", None, CHUA_DO, ""))
    # FINDER: `san_cong_cu` la Finder da co (memory `finder-da-ton-tai-la-san-cong-cu`)
    # Ten tep DOC TU CHINH module, khong doan. Ban cu doan
    # `reports/SAN_CONG_CU.json` trong khi `san_cong_cu.KHO` la
    # `reports/cong_cu.json`, nen chi so nay bao CHUA_DO vinh vien - mot cach
    # lang le de mat mot phep do ma van tuong minh dang giam sat.
    try:
        from nhan import san_cong_cu as _SCC
        _kho = Path(_SCC.KHO)
    except Exception:
        _kho = LAB / "reports" / "cong_cu.json"
    t = _tuoi_tep(_kho)
    ra.append(_chi_so("evo.finder", "tuoi kho cong cu (gio)",
                      None if t is None else round(t, 1),
                      CHUA_DO if t is None else (TOT if t <= 24 * 30 else XAU),
                      "san_cong_cu = Finder cua so do",
                      "python b.py san" if (t is None or t > 24 * 30) else ""))
    return ra


def suc_khoe_dia() -> list[dict]:
    """DIA CON CHO KHONG - va so cua chinh `nao.db`.

    Them 12/09/2026 sau khi mot buoi toi mat sach vi dieu nay: o C con **177 MB**
    tren 120 GB, va hau qua KHONG hien ra nhu mot loi dia. No hien ra nhu:

        684 file chi bao boc xong -> 0 co che moi
        `xao_ma_llm` chay 221 giay -> XONG rc=0, kho van 2.554
        `xao_hoc_thuat` chay 222 giay -> XONG rc=0, kho van 2.554

    Ba viec bao "xong" va khong ai biet gi. Loi that nam sau hai lop: SQLite nem
    `database or disk is full`, cac ham boc bat Exception roi tra ve rong, va
    `day_viec` cham theo MA THOAT nen thay rc=0.

    Do la ho benh `ket-luan-am-phai-phan-biet-CHUA-DO` o dang te nhat: khong
    phai mot phep do bao sai, ma la CA MOT BUOI chay khong.

    Nguong: canh bao duoi 5 GB, vi mot lan chay `to_hop` + pool 10 tien trinh
    an vai GB file tam - do that trong cung phien: dung tien trinh xong thi
    dia tu 177 MB nhay len 6,4 GB.
    """
    ra = []
    try:
        import shutil
        t, d, r = shutil.disk_usage(str(LAB))
        gb = r / (1024 ** 3)
        ra.append(_chi_so(
            "dia.con_trong", "dung luong con trong (GB)", round(gb, 1),
            TOT if gb >= 5 else XAU,
            "%.1f GB trong / %.0f GB tong (%.0f%% da dung)"
            % (gb, t / (1024 ** 3), 100.0 * d / max(t, 1)),
            "" if gb >= 5 else
            "python -m nhan.don_mo_coi --don   # tien trinh treo giu file tam; "
            "roi don AppData neu van thieu"))
    except Exception as e:
        ra.append(_chi_so("dia.con_trong", "dung luong con trong", None, CHUA_DO,
                          "%s: %s" % (type(e).__name__, e)))
    try:
        mb = (LAB / "nao.db").stat().st_size / (1024 ** 2)
        ra.append(_chi_so(
            "dia.nao_db", "kich thuoc nao.db (MB)", round(mb),
            TOT if mb < 3000 else XAU,
            "bang `noi_dung` (toan van tai lieu) chiem phan lon - do la du lieu "
            "THAT, khong phai rac; muon giam thi nen cot `ban_van`, dung xoa"))
    except Exception:
        pass

    # WAL - thu phinh LANG LE va an gap doi dia.
    #
    # Do 12/09/2026: `nao.db` 1,4 GB va `nao.db-wal` CUNG 1,4 GB. WAL chi duoc
    # gop vao db khi co mot checkpoint chay tron; tien trinh bi giet giua chung
    # (qua han, Ctrl-C, may day) thi no o lai va lan sau ghi tiep vao do. Khong
    # ai nhin file `-wal` nen no lon den luc dia day, roi moi khau ghi that bai
    # AM - dung chuoi da lam mat mot buoi toi.
    #
    # `PRAGMA wal_checkpoint(TRUNCATE)` chi chay duoc khi KHONG con ket noi nao
    # khac dang mo (tra ve (1,-1,-1) = BUSY neu con), nen de xuat kem lenh dung
    # tien trinh truoc.
    try:
        w = (LAB / "nao.db-wal").stat().st_size / (1024 ** 2)
        ra.append(_chi_so(
            "dia.wal", "nao.db-wal (MB)", round(w),
            TOT if w < 500 else XAU,
            "WAL chua duoc gop vao db. No phinh lang le va an gap doi dia.",
            "" if w < 500 else
            "python -m nhan.don_mo_coi --don && python -m nhan.gop_wal"))
    except FileNotFoundError:
        ra.append(_chi_so("dia.wal", "nao.db-wal (MB)", 0, TOT,
                          "khong co WAL ton dong"))
    except Exception:
        pass
    return ra


def suc_khoe_thong_luong() -> list[dict]:
    """TANG NAO DANG CAM - `nhan/do_im_lang.py`.

    Noi vao EVO 12/09 sau khi ban do cho thay module nay MO COI. No tra loi noi
    so ma chu du an neu ra 01/09: *"he ngay cang do so la dieu dang mung nhung
    so nhat la gio no bug hoac bo sot ma khong biet tai dau"*.

    Cai no bat duoc la mot so 0 DOC DUOC nhu mot cau tra loi: "nguon nay khong
    co gi", "kho nay khong co chien luoc". Trong MOT ngay da co sau lan nhu vay,
    khong cai nao nem ngoai le, khong cai nao ghi log.
    """
    ra = []
    try:
        from nhan import do_im_lang as DI
        k = DI.quet()
        tang = k.get("tang") or []
        cam = [t for t in tang if t.get("trang_thai") == "CAM"]
        ra.append(_chi_so(
            "thong_luong.tang_cam", "tang co dau vao ma KHONG co dau ra",
            len(cam), XAU if cam else TOT,
            "; ".join("%s: %s vao -> 0 ra" % (t["tang"], t["vao"])
                      for t in cam[:3]) or "%d tang deu co dau ra" % len(tang),
            "b im-lang de xem vi sao tung tang cam" if cam else ""))
        # Nut that: tang co ty le ra/vao thap nhat trong so cac tang DANG CHAY.
        chay = [t for t in tang if t.get("trang_thai") == "CHAY"
                and t.get("ty_le") is not None]
        if chay:
            it = min(chay, key=lambda t: t["ty_le"])
            ra.append(_chi_so(
                "thong_luong.nut_that", "tang hep nhat cua day chuyen",
                "%s %.1f%%" % (it["tang"], 100 * it["ty_le"]), TOT,
                "%d vao -> %d ra. Day la cho dang gioi han san luong ca he - "
                "noi rong cho khac khong lam tang dau ra."
                % (it["vao"], it["ra"])))
    except Exception as e:
        ra.append(_chi_so("thong_luong.doc_duoc", "do duoc thong luong khong",
                          None, CHUA_DO, "%s: %s" % (type(e).__name__, e)))
    return ra


def suc_khoe_phanh() -> list[dict]:
    """Cai PHANH co duoc noi khong - `nhan/han_muc.py`.

    Them 12/09 sau khi ban do sinh tu ma nguon cho thay `han_muc.py` MO COI.
    No la kill-switch: tran sut giam, tran lenh/ngay, tran phoi nhiem. Hien
    khong ai goi `duoc_vao_lenh` vi he chua danh lenh that - do la BINH THUONG,
    khong phai loi.

    Nhung khi he bat dau co lenh that (nhat la luc cam VPS chay nhieu thang),
    mot cai phanh chua noi la thu nguy hiem nhat trong ca lab. Nen EVO canh
    dung mot dieu: **co he dang chay ma chua khai han muc khong**. Im lang cho
    toi dung luc do moi len tieng.
    """
    ra = []
    try:
        from nhan import han_muc as HM
        from nhan import so as SO
        HM._khoi_tao()
        chay = [r["ma"] for r in
                SO.nhieu("SELECT ma FROM he_chay WHERE trang_thai <> 'DUNG'")]
        thieu = [m for m in chay if not HM.cua(m)]
        if not chay:
            ra.append(_chi_so(
                "phanh.he_chay", "he dang chay lenh that", 0, TOT,
                "chua he nao danh lenh that - phanh chua can, dung la khong co van de"))
        elif thieu:
            ra.append(_chi_so(
                "phanh.chua_khai", "he chay MA CHUA khai han muc", len(thieu), XAU,
                "he: %s" % ", ".join(thieu[:6]),
                "b phanh <he> --dd 20 --lenh 10 --phoi-nhiem 1.0"))
        else:
            ra.append(_chi_so(
                "phanh.chua_khai", "he chay MA CHUA khai han muc", 0, TOT,
                "%d/%d he da khai han muc" % (len(chay), len(chay))))
        # Chi so nay phai LUON duoc sinh, ke ca khi khong co ngat nao. Mot chi
        # so chi xuat hien luc co van de thi khong ai biet no ton tai, va bang
        # `CAT_NGHIA` cua no khong doi chieu duoc voi ket qua do that.
        k = HM.quet()
        ra.append(_chi_so(
            "phanh.vua_ngat", "he bi NGAT trong lan quet nay",
            k.get("so_ngat", 0), XAU if k.get("so_ngat") else TOT,
            "; ".join("%s: %s" % (x["he"], x["ly_do"])
                      for x in (k.get("da_ngat") or [])[:3])
            or "chua he nao vuot tran",
            "ngat phai co NGUOI mo lai: `b phanh-mo <he>`"
            if k.get("so_ngat") else ""))
    except Exception as e:
        ra.append(_chi_so("phanh.doc_duoc", "doc duoc so han muc khong",
                          None, CHUA_DO, "%s: %s" % (type(e).__name__, e)))
    return ra


def suc_khoe_may() -> list[dict]:
    """Tien trinh mo coi - thu lam he TU TE LIET ma khong bao gi.

    Do 12/09/2026: 24 worker mo coi an **19,5/20 loi** trong hon 20 phut. Bo
    dieu toc cua qwen thay CPU 100% nen tu choi phong viec - dung thiet ke - va
    he nam im voi bang viec day. Khong loi, khong canh bao.
    """
    try:
        from nhan import don_mo_coi as DMC
        k = DMC.quet()
    except Exception as e:
        return [_chi_so("may.mo_coi", "tien trinh mo coi", None, CHUA_DO,
                        "khong quet duoc: %s" % e)]
    if k.get("loi"):
        return [_chi_so("may.mo_coi", "tien trinh mo coi", None, CHUA_DO,
                        k["loi"])]
    n, cpu = len(k["mo_coi"]), k["cpu_mo_coi"]
    return [_chi_so(
        "may.mo_coi", "tien trinh mo coi dang an CPU", n,
        TOT if cpu < 20 else XAU,
        "%d tien trinh, %.0f%% CPU" % (n, cpu),
        "python -m nhan.don_mo_coi --don" if cpu >= 20 else "")]


# -------------------------------------------------------------- HANG DOI XAY
def suc_khoe_hang_doi() -> list[dict]:
    try:
        import day_viec as DV
        so = DV.doc()
    except Exception as e:
        return [_chi_so("xay.hang_doi", "hang doi viec xay", None, CHUA_DO,
                        "khong doc duoc: %s" % e)]
    v = so.get("viec") or []
    dem = {}
    for x in v:
        dem[x["trang_thai"]] = dem.get(x["trang_thai"], 0) + 1
    hong = dem.get("loi", 0) + dem.get("qua_han", 0)
    ra = [_chi_so("xay.hang_doi", "viec trong hang doi", len(v),
                  TOT if v else CHUA_DO, str(dem))]
    ra.append(_chi_so(
        "xay.viec_hong", "viec loi / qua han", hong,
        TOT if hong == 0 else XAU,
        ", ".join("%s(%s)" % (x["ma"], x["trang_thai"]) for x in v
                  if x["trang_thai"] in ("loi", "qua_han"))[:200],
        "xem nhat_ky/day_viec/<ma>.log roi `python day_viec.py --lam-lai <ma>`"
        if hong else ""))
    return ra


# ------------------------------------------------------------------ TONG HOP
#: Cat nghia: dau hieu -> nguyen nhan thuong gap. Viet ra tuong minh de ai cung
#: doi chieu duoc, chu khong de mot mo heuristic trong dau mot ham.
CAT_NGHIA = {
    "dia.con_trong": "Dia day KHONG hien ra nhu loi dia. No hien ra nhu 'boc "
                     "684 file -> 0 co che', 'viec XONG rc=0 ma kho khong doi'. "
                     "SQLite nem 'disk is full', ham boc bat Exception roi tra "
                     "rong, hang doi cham theo ma thoat nen thay rc=0. Kiem dia "
                     "TRUOC khi tin bat ky ket qua rong nao.",
    "thong_luong.tang_cam": "Mot tang co dau vao ma khong co dau ra nao. Gan nhu "
                            "luon la doc sai ten truong / lech quy uoc ma / bo "
                            "doc chua tung duoc goi - KHONG phai 'nguon khong co "
                            "gi'. Chay `b im-lang` de biet vi sao tung tang cam.",
    "phanh.chua_khai": "Co he dang danh lenh that ma khong co tran sut giam / "
                       "tran lenh ngay / tran phoi nhiem. `han_muc.duoc_vao_lenh` "
                       "tra False khi chua khai - nhung chi khi CO AI GOI no. "
                       "Phai khai han muc TRUOC khi he chay tiep.",
    "phanh.vua_ngat": "Mot he vuot tran va da bi ngat. Theo thiet ke, ngat thi "
                      "PHAI CO NGUOI mo lai - tu mo lai sau X phut la bien cai "
                      "phanh thanh cai cham tre.",
    "seeker.ty_le_doc": "Tai lieu vao kho nhung khau LAY TOAN VAN khong theo kip. "
                        "Thuong la hang doi doc bi URL chet chiem cho (da xay ra: "
                        "406 URL TradingView chet lam bao 'het ton kho').",
    "seeker.nguon_rong": "Nguon co the bi CHAN tren may nay, hoac bo doc cua no "
                         "chua tung duoc goi. Hai chuyen khac han nhau - phai do "
                         "tung nguon truoc khi goi la 'nguon chet'.",
    "quantlab.kho_co_che": "Kho co che khong lon them: khau BOC khong ra hang, "
                           "hoac nguon dang doc khong chua luat (do 12/09: 24.244 "
                           "cau bai bao -> 4 dieu kien).",
    "quantlab.ket_qua": "Co che co nhung khong ai cham cong - duong tu kho den "
                        "cong bi dut.",
    "evo.van_de_mo": "Van de mo don lai: dang ghi nhan nhanh hon dang dong.",
    "evo.finder": "Finder lau khong san - kho cong cu ngoai dang cu dan.",
    "quantlab.ho_so_song": "Ho so song cu - dac tinh tai san co the da doi.",
    "quantlab.ho_so_mua_vu": "Ho so mua vu cu.",
    "quantlab.ho_so_tuong_quan": "Ho so tuong quan cu - phep TIA cua `to_hop` "
                                 "dua vao no, cu thi tia sai.",
    "quantlab.ho_so_suy_nguoc": "Chua/lau chua chay suy nguoc - khong biet co "
                                "dau hieu nao bao truoc khong.",
    "quantlab.ho_so_to_hop": "Bang to hop cu - ket luan 'khong co gi' co the da "
                             "duoc do trong mot the he cong khac.",
    "may.mo_coi": "Tien trinh mo coi an het CPU -> bo dieu toc cua qwen tu "
                  "choi phong viec -> he nam im voi bang viec day. Khong loi, "
                  "khong canh bao. Nguon goc thuong la `nohup ... &`: cha thoat "
                  "nhung Pool de lai worker, va Pool SINH LAI khi con chet nen "
                  "phai giet CA CAY tu goc.",
    "xay.viec_hong": "Mot viec xay hong. Hang doi tuan tu KHONG dung lai o loi, "
                     "nen viec sau van chay - phai doc log de biet cai gi hong.",
}


def do_het() -> dict:
    chi_so = (suc_khoe_seeker() + suc_khoe_quantlab() + suc_khoe_evo()
              + suc_khoe_hang_doi() + suc_khoe_may() + suc_khoe_phanh()
              + suc_khoe_thong_luong() + suc_khoe_dia())
    for c in chi_so:
        if c["trang_thai"] == XAU:
            c["cat_nghia"] = CAT_NGHIA.get(c["ten"], "")
    dem = {}
    for c in chi_so:
        dem[c["trang_thai"]] = dem.get(c["trang_thai"], 0) + 1
    return {"luc": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "chi_so": chi_so, "dem": dem}


def bao_cao(ket: dict | None = None, in_ra=print, ghi_so: bool = False) -> str:
    ket = ket or do_het()
    d = ["# EVO - SUC KHOE HE THONG", "", "*%s*" % ket["luc"], "",
         "TOT %d · XAU %d · CHUA DO %d"
         % (ket["dem"].get(TOT, 0), ket["dem"].get(XAU, 0),
            ket["dem"].get(CHUA_DO, 0)),
         "",
         "`CHUA_DO` khong phai `XAU`. Mot chi so khong do duoc thi noi la khong",
         "do duoc - quy no ve 'xau' la cach mot bo giam sat tu bia ra van de.", "",
         "| chi so | gia tri | trang thai | bang chung |",
         "|---|---:|---|---|"]
    for c in ket["chi_so"]:
        d.append("| `%s` | %s | %s | %s |"
                 % (c["ten"], c["gia_tri"], c["trang_thai"],
                    (c["bang_chung"] or "")[:90]))
    xau = [c for c in ket["chi_so"] if c["trang_thai"] == XAU]
    if xau:
        d += ["", "## Van de + cat nghia + de xuat", ""]
        for c in xau:
            d += ["### `%s` — %s" % (c["ten"], c["mo_ta"]), "",
                  "**Do duoc:** %s" % (c["bang_chung"] or c["gia_tri"]), ""]
            if c.get("cat_nghia"):
                d += ["**Cat nghia:** %s" % c["cat_nghia"], ""]
            if c.get("de_xuat"):
                d += ["**De xuat (chay duoc):**", "", "```", c["de_xuat"], "```", ""]
            else:
                d += ["**De xuat:** chua co lenh san - can nguoi quyet dinh.", ""]
    else:
        d += ["", "Khong chi so nao o muc XAU.", ""]
    chua = [c for c in ket["chi_so"] if c["trang_thai"] == CHUA_DO]
    if chua:
        d += ["## Chua do duoc (KHONG phai ket luan am)", ""]
        for c in chua:
            d.append("- `%s`: %s" % (c["ten"], c["bang_chung"] or "khong co du lieu"))
        d.append("")
    vb = "\n".join(d) + "\n"
    BAO_CAO.parent.mkdir(exist_ok=True)
    BAO_CAO.write_text(vb, encoding="utf-8")
    if in_ra:
        in_ra(vb)
        in_ra("-> %s" % BAO_CAO)
    if ghi_so:
        ghi_van_de(xau, in_ra=in_ra)
    return vb


def ghi_van_de(xau: list[dict], in_ra=print) -> int:
    """Ghi cac chi so XAU vao so `van_de`. Khong ghi trung tieu de dang mo."""
    try:
        from nhan import so as SO
    except Exception:
        return 0
    # DUNG `tru/evolution.bao_van_de_gop`, KHONG tu viet INSERT.
    #
    # Hai lan sai o day trong mot ngay:
    #   1. Toi viet INSERT theo mot so do TU NGHI RA (`tieu_de`, `noi_dung`,
    #      `luc`) trong khi bang that la (ma, muc, mo_ta, bang_chung,
    #      hanh_dong, trang_thai, phat_hien_luc). Loi bi `except` nuot va EVO in
    #      "ghi 0 van de moi" - doc nhu ket qua binh thuong.
    #   2. Sua so do xong van con sai CHO LON HON: `tru/evolution.py` DA CO
    #      `bao_van_de_gop` voi khu trung lap theo NOI DUNG (`ma_chuan_van_de`),
    #      va ghi chu cua no noi ro vi sao can: "do la ly do so van de phinh tu
    #      3 chuyen len 12 dong". Tu viet INSERT la dung lai chinh cai benh do.
    try:
        from tru import evolution as TEVO
    except Exception as e:
        if in_ra:
            in_ra("khong nap duoc tru/evolution de ghi van de: %s" % e)
        return 0
    them = 0
    for c in xau:
        if c["ten"] in CHI_SO_TU_CHIEU:
            continue        # mot thuoc do khong duoc lam thay doi thu no do
        try:
            _ma, tinh_trang = TEVO.bao_van_de_gop(
                "VUA", "EVO/%s: %s" % (c["ten"], c["mo_ta"]),
                {"chi_so": c["ten"], "gia_tri": c.get("gia_tri"),
                 "bang_chung": str(c.get("bang_chung") or "")[:500],
                 "cat_nghia": c.get("cat_nghia", ""),
                 "de_xuat": c.get("de_xuat", "")})
            if tinh_trang == "MOI":
                them += 1
        except Exception as e:
            if in_ra:
                in_ra("khong ghi duoc van de '%s': %s" % (c["ten"], e))
    # DONG van de da het hieu luc - dung ham chung voi duong supervisor.
    # Truoc 13/09 duong nay chi biet MO: o C len 30,8 GB ma `dia_thap` van
    # nam trong so, va mot so van de chi dai ra thi khong ai doc no nua.
    try:
        dong = TEVO.dong_van_de_het_hieu_luc()
        dong += dong_van_de_theo_chi_so(in_ra=None)
        if dong and in_ra:
            in_ra("dong %d van de da het hieu luc: %s"
                  % (len(dong), ", ".join(dong[:6])))
    except Exception as e:
        if in_ra:
            in_ra("khong dong duoc van de cu: %s" % repr(e)[:100])
    if in_ra:
        in_ra("ghi %d van de moi vao so" % them)
    return them


#: Chi so TU CHIEU - do chinh so van de - nen KHONG duoc sinh ra van de.
#:
#: `evo.van_de_mo` dem so van de dang mo. Neu no duoc phep ghi mot van de khi
#: vuot nguong thi no tu nuoi minh: nhieu van de -> XAU -> ghi them mot van de
#: -> van nhieu. Do 13/09: ban ghi cua no la `gia_tri: 90, so_lan_tai_phat: 8`.
#: Mot thuoc do khong duoc lam thay doi thu no dang do.
CHI_SO_TU_CHIEU = {"evo.van_de_mo"}

#: Van de do LLM chan doan ma KHONG tai phat sau bay nhieu ngay thi dong.
#: LLM chan doan lai MOI LUOT, nen khong tai phat la mot PHEP DO chu khong
#: phai mot su im lang. Dat 2 ngay: du de mot su co that keo qua mot dem
#: khong bi dong oan, va du ngan de so khong phinh.
NGAY_KHONG_TAI_PHAT = 2


def dong_van_de_theo_chi_so(in_ra=print) -> list:
    """Dong van de do LLM/EVO ghi ma CHI SO goc cua no nay da TOT.

    ## VI SAO CAN THEM CAI NAY

    `tru/evolution.dong_van_de_het_hieu_luc` chi dong duoc cai nam trong
    `EVO_TU_QUAN` (danh sach ma co dinh). Van de do LLM chan doan mang ma sinh
    (`llm_e502b66769`, `vd_tick_test_bi_khoa`) khong nam trong danh sach do,
    nen **khong co duong dong nao** - chung tich lai vinh vien.

    Do 13/09: 7/23 van de con mo la loai nay, trong do it nhat hai cai da het
    tu lau (`vd_tick_test_bi_khoa` = "dia duoi nguong an toan" trong khi dia
    da 30,8 GB; `EVO/xay.viec_hong` trong khi chi so do dang TOT).

    May man la chung CO ghi `chi_so` trong bang chung. Nen dong duoc bang
    chinh phep do goc: chi so nay TOT -> van de sinh ra tu no het hieu luc.
    """
    import json as _json
    try:
        from nhan import so as SO
    except Exception:
        return []
    from datetime import datetime as _dt
    hien = {c["ten"]: c["trang_thai"] for c in do_het()["chi_so"]}
    nay = _dt.now()
    da_dong = []
    for m in SO.van_de_mo():
        bc = m.get("bang_chung")
        if isinstance(bc, str):
            try:
                bc = _json.loads(bc)
            except Exception:
                bc = {}
        bc = bc or {}
        ten = bc.get("chi_so")
        if ten and hien.get(ten) == TOT:
            SO.dong_van_de(m["ma"], "chi so `%s` da TOT tro lai" % ten)
            da_dong.append(m["ma"])
            if in_ra:
                in_ra("  dong %s (chi so %s da TOT)" % (m["ma"], ten))
            continue
        # KHONG TAI PHAT = bang chung. Van de do LLM chan doan khong ghi
        # `chi_so` thi khong dong theo chi so duoc - nhung LLM chan doan LAI
        # moi luot, nen viec no KHONG con neu ra la mot phep do, khong phai
        # mot su im lang. Do 13/09: `vd_tick_test_bi_khoa` ("dia duoi nguong")
        # nam trong so trong khi dia da 30,8 GB, va khong co duong nao dong.
        if not m["ma"].startswith(("llm_", "vd_")):
            continue
        gan = bc.get("lan_gan_nhat") or m.get("phat_hien_luc")
        if not gan:
            continue
        try:
            tuoi = (nay - _dt.strptime(str(gan)[:19], "%Y-%m-%d %H:%M:%S")).days
        except Exception:
            continue
        if tuoi >= NGAY_KHONG_TAI_PHAT:
            SO.dong_van_de(m["ma"], "khong tai phat %d ngay" % tuoi)
            da_dong.append(m["ma"])
            if in_ra:
                in_ra("  dong %s (khong tai phat %d ngay)" % (m["ma"], tuoi))
    return da_dong


#: Nho lan bao xa gan nhat, de khong gui lap.
DAU_VET_XA = LAB / "reports" / "_evo_da_bao.json"


def bao_xa(ket: dict | None = None, luon: bool = False, in_ra=print) -> dict:
    """Gui cac chi so XAU ra Telegram. Chi gui khi TAP VAN DE DOI.

    ## Vi sao phai co dieu kien "doi"

    Chu du an 12/09/2026: he se len **VPS chay 24/7 nhieu thang**. Mot bo giam
    sat gui cung mot dong moi gio trong ba thang la 2.160 tin nhan giong het
    nhau - va den tin thu ba nguoi ta tat thong bao, tuc bo giam sat tu lam
    minh vo hinh.

    Nen: so TAP TEN chi so dang XAU voi lan truoc. Doi thi gui, khong doi thi im.
    `luon=True` de ep gui (dung khi thu cau).

    Va mot chieu nua it ai nghi toi: khi van de duoc SUA XONG cung phai bao -
    khong thi nguoi ta khong biet la da yen.
    """
    ket = ket or do_het()
    nay = sorted(c["ten"] for c in ket["chi_so"] if c["trang_thai"] == XAU)
    cu = []
    try:
        cu = sorted(json.loads(DAU_VET_XA.read_text(encoding="utf-8")).get("xau", []))
    except Exception:
        pass
    if nay == cu and not luon:
        in_ra("EVO: tap van de khong doi (%d muc) - khong gui" % len(nay))
        return {"gui": False, "xau": nay}

    moi = [x for x in nay if x not in cu]
    da_het = [x for x in cu if x not in nay]
    dong = ["THE BRAIN / EVO  %s" % ket["luc"],
            "TOT %d | XAU %d | CHUA DO %d"
            % (ket["dem"].get(TOT, 0), ket["dem"].get(XAU, 0),
               ket["dem"].get(CHUA_DO, 0))]
    tra = {c["ten"]: c for c in ket["chi_so"]}
    for t in moi:
        c = tra.get(t, {})
        dong.append("MOI XAU: %s - %s" % (t, (c.get("bang_chung") or "")[:90]))
        if c.get("de_xuat"):
            dong.append("   chay: %s" % c["de_xuat"][:90])
    for t in da_het:
        dong.append("DA HET: %s" % t)
    if not moi and not da_het:
        dong.append("(bao theo yeu cau, tap van de khong doi)")
    vb = "\n".join(dong)

    ok = False
    try:
        import importlib.util
        sp = importlib.util.spec_from_file_location(
            "_dkx", LAB / "dieu_khien_xa.py")
        m = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(m)
        ok = bool(m.gui(vb))
    except Exception as e:
        in_ra("EVO: khong gui duoc: %s: %s" % (type(e).__name__, e))
    if not ok:
        # Im lang o day la cach te nhat: tren VPS se khong ai biet EVO dang co
        # gang bao ma khong bao duoc.
        in_ra("EVO: CHUA GUI DUOC. Thuong la `chat_id` = 0 trong "
              "config/tele_bridge.json - cau Telegram chi bat duoc chat_id sau "
              "khi chu du an nhan cho bot mot lan. Chay `b xa` roi nhan gi do.")
    if ok:
        DAU_VET_XA.parent.mkdir(exist_ok=True)
        DAU_VET_XA.write_text(json.dumps({"xau": nay, "luc": ket["luc"]},
                                         ensure_ascii=False), encoding="utf-8")
        in_ra("EVO: da gui %d muc moi, %d muc da het" % (len(moi), len(da_het)))
    return {"gui": ok, "xau": nay, "moi": moi, "da_het": da_het, "van": vb}


def main(argv: list[str]) -> int:
    ket = do_het()
    bao_cao(ket, ghi_so="--ghi" in argv)
    if "--xa" in argv:
        bao_xa(ket, luon="--ep" in argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
