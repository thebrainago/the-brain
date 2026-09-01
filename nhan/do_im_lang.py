# -*- coding: utf-8 -*-
"""do_im_lang.py - TIM TANG NAO DANG CAM MA KHONG AI BIET.

VI SAO CO FILE NAY (chu du an neu ra 01/09/2026): "he ngay cang do so la dieu
dang mung nhung so nhat la gio no bug hoac bo sot ma khong biet tai dau".

Noi so do co can cu. Trong MOT ngay lam viec, day la nhung loi tim duoc, va
chung co CUNG MOT HINH DANG:

  EVO tim GitHub          -> bao "khong co gi"   (that ra 18 ket qua, doc sai ten truong)
  331 tai lieu blog       -> truy ra 0           (so nguon ghi `rss_x`, tai lieu ghi `x`)
  NGHI                    -> im 16 ngay          (bi `skipped` vi duong LLM tat)
  ban doc MQL5            -> 35 tai lieu         (that ra la thanh dieu huong cua trang)
  thuoc do nang suat      -> 0/237               (do mot ham LEGACY khong ai goi)
  bieu thuc chinh quy     -> khong bao gio khop  (ky tu `\\b` thanh backspace)

KHONG cai nao nem ngoai le. KHONG cai nao ghi log do. Moi cai deu tra ve **mot
so 0 trong giong mot cau tra loi** - va cai nguy hiem la so 0 do DOC DUOC:
"nguon nay khong co gi", "kho nay khong co chien luoc", "khong co edge".

NGUYEN TAC CUA MODULE NAY:

    Mot tang co DAU VAO ma KHONG CO DAU RA thi khong phai ket qua - do la
    mot cau hoi. Phan biet ba trang thai, dung gop lam mot:
      CAM     - co dau vao, dau ra = 0. NGHI NGO, phai xem.
      NGHI    - dau vao = 0. Khong co gi de lam, khong phai loi.
      TUT     - tung ra nhieu, nay ra it hon han. Hoi quy.

Module nay KHONG sua gi. No chi doc so va chi cho: dau vao bao nhieu, dau ra bao
nhieu, va tang nao dang nuot.
"""
from __future__ import annotations

from nhan import so as SO

#: Mot tang cua day chuyen: (ten, cau dem DAU VAO, cau dem DAU RA, nguong).
#: `nguong` = dau vao phai lon hon bao nhieu thi "dau ra = 0" moi dang ngo.
#: Dat thap se bao dong gia luc kho con moi; dat cao se bo sot.
TANG: list[tuple[str, str, str, int]] = [
    ("doc toan van",
     "SELECT COUNT(*) n FROM tai_lieu WHERE url LIKE 'http%'",
     "SELECT COUNT(*) n FROM noi_dung WHERE kieu != 'khong_doc_duoc'", 50),
    ("ban doc -> artifact",
     "SELECT COUNT(*) n FROM noi_dung WHERE so_ky_tu > 400",
     "SELECT COUNT(*) n FROM artifact WHERE artifact_type='document'", 50),
    ("artifact -> ung vien",
     "SELECT COUNT(*) n FROM artifact WHERE artifact_type='document'",
     "SELECT COUNT(*) n FROM artifact WHERE artifact_type='candidate'", 50),
    ("ung vien -> hang doi",
     "SELECT COUNT(*) n FROM artifact WHERE artifact_type='candidate'",
     "SELECT COUNT(*) n FROM candidate_queue", 20),
    ("hang doi -> viec",
     "SELECT COUNT(*) n FROM candidate_queue",
     "SELECT COUNT(*) n FROM viec WHERE loai='kham_pha_theo_mau'", 20),
    ("viec -> gia thuyet",
     "SELECT COUNT(*) n FROM viec WHERE trang_thai='XONG'",
     "SELECT COUNT(*) n FROM gia_thuyet", 20),
    ("gia thuyet -> phan quyet",
     "SELECT COUNT(*) n FROM gia_thuyet",
     "SELECT COUNT(*) n FROM ket_qua", 20),
    ("ban doc -> thanh phan",
     "SELECT COUNT(*) n FROM noi_dung WHERE so_ky_tu > 400",
     "SELECT COUNT(*) n FROM thanh_phan", 50),
    ("de xuat -> co che",
     "SELECT COUNT(*) n FROM de_xuat",
     "SELECT COUNT(*) n FROM de_xuat WHERE nhan=1", 10),
]


def _dem(sql: str) -> int | None:
    """Dem, hoac None neu KHONG DO DUOC. `None` khac han `0`."""
    try:
        r = SO.mot(sql)
        # SO.mot tra ve DICT, nen list(r)[0] lay TEN COT chu khong lay gia
        # tri - dung cai bay so-0-cam-lang ma file nay sinh ra de bat.
        return int(r["n"]) if r else 0
    except Exception:
        return None


def do_mot_tang(ten: str, sql_vao: str, sql_ra: str, nguong: int) -> dict:
    vao, ra = _dem(sql_vao), _dem(sql_ra)
    if vao is None or ra is None:
        # Khong do duoc thi noi la khong do duoc. Day chinh la cai bay ma module
        # nay sinh ra de tranh: mot cau truy van hong tra 0 va bi doc thanh
        # "tang nay khong ra gi".
        return {"tang": ten, "vao": vao, "ra": ra, "trang_thai": "KHONG_DO_DUOC"}
    if vao <= nguong:
        tt = "NGHI"                       # chua du dau vao de ket luan gi
    elif ra == 0:
        tt = "CAM"                        # co dau vao ma khong ra gi -> nghi ngo
    else:
        tt = "CHAY"
    return {"tang": ten, "vao": vao, "ra": ra, "trang_thai": tt,
            "ty_le": round(ra / vao, 4) if vao else None}


def quet() -> dict:
    """Quet toan day chuyen. Tra ve danh sach tang + nhung tang dang CAM."""
    ds = [do_mot_tang(*t) for t in TANG]
    cam = [d for d in ds if d["trang_thai"] == "CAM"]
    hong = [d for d in ds if d["trang_thai"] == "KHONG_DO_DUOC"]
    return {"tang": ds, "cam": cam, "khong_do_duoc": hong,
            "so_cam": len(cam), "so_hong": len(hong)}


def nguon_cam(nguong: int = 3) -> list[dict]:
    """Nguon da chay >= `nguong` lan ma chua ve mot tai lieu nao.

    Khac `nguon_khong_thu_hoach` cua EVO o mot cho quan trong: o day doi chieu
    voi bang `tai_lieu` THAT chu khong doc cot `thu_hoach` cua chinh bang
    `nguon`. Hai so do tung LECH NHAU - so nguon ghi da thu 60 tai lieu trong
    khi truy `tai_lieu` ra 0, vi hai ben ghi ten nguon khac nhau. Mot bo dem tu
    bao cao ve chinh no thi khong bat duoc loi cua chinh no.
    """
    try:
        ds = SO.nhieu(
            "SELECT n.ma, n.so_lan, n.thu_hoach, "
            "  (SELECT COUNT(*) FROM tai_lieu t WHERE t.nguon = n.ma) that "
            "FROM nguon n WHERE n.trang_thai='BAT' AND n.so_lan >= ? "
            "  AND (SELECT COUNT(*) FROM tai_lieu t WHERE t.nguon = n.ma) = 0 "
            "ORDER BY n.so_lan DESC", nguong)
        return [{**r, **_vi_sao_cam(r["ma"])} for r in ds]
    except Exception:
        return []



#: Vi sao mot nguon cam. Thu tu quan trong: cai DAU danh trung thi dung lai.
#: Muc dich khong phai phan loai cho dep - ma la tach **CAM VI HONG** khoi
#: **CAM VI HA TANG DANG TAT**. Hai cai nay doi hoi hai hanh dong khac han
#: nhau, va gop chung lai la cach nhanh nhat de mot loi that bi chim trong
#: mot dong canh bao quen thuoc.
def _vi_sao_cam(ma: str) -> dict:
    from nhan import toan_van as TV
    r = SO.mot("SELECT url, so_loi, loi_lien_tuc, ghi_chu FROM nguon WHERE ma=?", ma)
    url = (r["url"] if r else "") or ""
    loi = (r["so_loi"] if r else 0) or 0

    # 1. Co ai di lay no khong? Kho nguon va danh sach ham thu thap la HAI
    #    danh sach roi nhau; mot ma nam trong kho ma khong ham nao nhan thi
    #    no se "chay" mai mai tren giay to.
    if not _co_nguoi_lay(ma):
        return {"vi_sao": "KHONG_AI_LAY",
                "lam_gi": "kho nguon co ma nay nhung khong ham thu thap nao nhan"}

    # 2. Mien can trinh duyet ma trinh duyet dang tat -> khong phai loi cua nguon.
    #    Nhan ra bang HAI dau: nam trong kho chi-doc-qua-trinh-duyet, hoac ten
    #    mien thuoc danh sach bat buoc. Chi tra ten mien se bo sot etoro.com.
    try:
        from tru import seeker as _S
        qua_td = ma in getattr(_S, "NGUON_TRINH_DUYET", {})
    except Exception:
        qua_td = False
    if qua_td or (url and TV.can_trinh_duyet(url)):
        from nhan import doc_trinh_duyet as DTD
        song = False
        try:
            song = bool(DTD.dang_chay())
        except Exception:
            song = False
        if not song:
            return {"vi_sao": "CHO_TRINH_DUYET",
                    "lam_gi": "mien nay bat buoc qua Chrome CDP; CDP dang TAT"}
        return {"vi_sao": "TRINH_DUYET_BAT_MA_VAN_TRONG",
                "lam_gi": "CDP dang chay ma van khong ra tai lieu - phai xem that"}

    if loi:
        return {"vi_sao": "LOI_MANG", "lam_gi": f"{loi} loi, ghi chu: {(r['ghi_chu'] or '')[:80]}"}
    return {"vi_sao": "CHAY_SACH_MA_RONG",
            "lam_gi": "khong loi, khong tai lieu - dang ngo nhat, phai chay tay"}


def _co_nguoi_lay(ma: str) -> bool:
    """Ma nguon nay co ham thu thap nao nhan khong?"""
    try:
        from tru import seeker as S
        from nhan import nguon_bai_viet as NBV
    except Exception:
        return True                      # khong kiem duoc thi dung buoc toi
    # SEEKER co HAI kho roi nhau: `NGUON` (12, doc thang) va `NGUON_TRINH_DUYET`
    # (25, chi doc qua Chrome CDP). Chi tra mot kho se ket luan nham rang nguon
    # khong co ai lay - dung cai loi ma file nay sinh ra de bat.
    if ma in getattr(S, "NGUON", {}) or ma in getattr(S, "NGUON_TRINH_DUYET", {}):
        return True
    goc = ma.split("_", 1)[1] if ma.startswith(("rss_", "trang_")) else ma
    return goc in NBV.tat_ca_feed() or goc in NBV.TRANG


def bao_cao() -> str:
    q = quet()
    d = ["# Do im lang - tang nao dang cam", ""]
    d += ["| Tang | Vao | Ra | Ty le | Trang thai |", "|---|---:|---:|---:|---|"]
    for x in q["tang"]:
        d.append(f"| {x['tang']} | {x['vao']} | {x['ra']} | "
                 f"{x.get('ty_le')} | {x['trang_thai']} |")
    nc = nguon_cam()
    if nc:
        d += ["", "## Nguon da chay ma chua ve mot tai lieu nao", ""]
        for r in nc:
            d.append(f"- `{r['ma']}`: chay {r['so_lan']} lan · so ghi thu "
                     f"{r['thu_hoach']} · dem THAT trong `tai_lieu`: {r['that']} "
                     f"· **{r.get('vi_sao', '?')}** - {r.get('lam_gi', '')}")
        d.append("")
        d.append("> `thu_hoach` va cot THAT lech nhau la dau hieu hai ben ghi "
                 "ten nguon khac nhau - da sap that 01/09.")
    return "\n".join(d)
