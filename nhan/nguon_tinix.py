# -*- coding: utf-8 -*-
"""nguon_tinix.py - repo.tinix.ai -> ung vien cong cu cho FINDER.

VI SAO. Chu du an dua nguon nay 04/09/2026 kem dinh nghia lai FINDER:
*"Finder toi muon la di tim nhung du an nay => tich hop vao he thong chung ta
co"*. Tuc Finder khong san "y tuong", no san DU AN CHAY DUOC.

`repo.tinix.ai` la mot chi muc du an nguon mo (ban tieng Viet + tieng Anh), va
no KHAC hai duong san hien co cua `san_cong_cu`:

  - `tim_github`  : tim theo TU KHOA ta nghi ra. Chi thay cai ta da biet de hoi.
  - `tim_dien_dan`: tim theo bai viet nguoi ta ban.
  - `tinix`       : mot dong CHAY QUA, do nguoi khac loc san. Thay duoc cai ta
                    KHONG BIET de hoi - va do la dung cho ma "tu tim nguon moi
                    ngoai danh sach co dinh" con thieu.

DO 04/09/2026: trang `/vi` tra ve 30 du an co cau truc DAY DU trong RSC payload
cua Next.js (`fullName`, `description`, `sourceUrl`, `primaryLanguage`,
`license`, `topics`, `sourceUpdatedAt`). Khong can doan tu slug, khong can goi
GitHub API mot lan nua cho sieu du lieu co ban.

Ngay trong 30 du an dau tien da co `LiquidGiraffe8/Metatrader-5-Plus-Edge` va
`NousResearch/hermes-agent` - hai thu khop truc tiep viec dang lam. Do la bang
chung cua luan diem tren: dong chay qua thay duoc cai truy van khong thay.

KHONG LAM O DAY: khong cham diem, khong quyet dinh tich hop, khong tai ma ve.
Module nay chi bien mot trang web thanh ban ghi ung vien. `tru/finder.py` cham,
va NGUOI quyet dinh.
"""
from __future__ import annotations

import json
import re
import time

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

GOC = "https://repo.tinix.ai"

#: Trang co danh sach du an. `/vi` la dong thinh hanh; `/vi/categories` la muc
#: luc theo chu de. Them trang moi vao day chu dung viet ham moi.
TRANG = ("/vi", "/vi/categories")

#: Khoa RSC chua mang du an. Tinix dung Next.js App Router, nen du lieu nam
#: trong `self.__next_f.push([1,"...json da escape..."])` chu khong o
#: `__NEXT_DATA__`. Ta tim MANG theo ten khoa roi can bang ngoac.
KHOA_MANG = ("initialProjects", "projects", "items")


def _lay(duong: str, timeout: int = 30) -> str:
    import requests
    r = requests.get(GOC + duong if duong.startswith("/") else duong,
                     timeout=timeout, headers={"User-Agent": UA})
    r.raise_for_status()
    return r.text


def _go_escape(t: str) -> str:
    """RSC nhet JSON vao trong mot chuoi JS, nen moi dau nhay bi escape mot lop.

    Bo lop do bang `json.loads` tren chinh doan chuoi thi an toan hon la thay
    the `\\"` bang `"` bang tay (chuoi that co the chua `\\\\"`).
    """
    return t.replace('\\"', '"').replace("\\\\", "\\").replace("\\n", "\n")


def _mang_sau(t: str, i: int) -> str | None:
    """Cat mot mang JSON bat dau tai `i` bang cach can bang ngoac vuong."""
    if i < 0 or i >= len(t) or t[i] != "[":
        return None
    sau = 0
    trong_chuoi = False
    thoat = False
    for j in range(i, len(t)):
        c = t[j]
        if thoat:
            thoat = False
            continue
        if c == "\\":
            thoat = True
            continue
        if c == '"':
            trong_chuoi = not trong_chuoi
            continue
        if trong_chuoi:
            continue
        if c == "[":
            sau += 1
        elif c == "]":
            sau -= 1
            if sau == 0:
                return t[i:j + 1]
    return None


def _du_an_trong(t: str) -> list[dict]:
    """Rut moi mang du an trong mot trang. Chap nhan im lang khi khong co."""
    tho = _go_escape(t)
    ra: list[dict] = []
    for khoa in KHOA_MANG:
        for m in re.finditer(r'"%s"\s*:\s*' % re.escape(khoa), tho):
            j = tho.find("[", m.end())
            if j < 0 or j - m.end() > 3:
                continue
            doan = _mang_sau(tho, j)
            if not doan:
                continue
            try:
                ds = json.loads(doan)
            except Exception:
                continue
            if isinstance(ds, list):
                ra.extend(d for d in ds if isinstance(d, dict) and d.get("fullName"))
    return ra


def _chuan(d: dict) -> dict:
    """Ban ghi tinix -> hinh dang kho cong cu cua `san_cong_cu`."""
    gp = d.get("license") or "?"
    if gp in ("NOASSERTION", "", None):
        gp = "?"
    return {
        "full_name": d.get("fullName"),
        "url": d.get("sourceUrl") or f"https://github.com/{d.get('fullName')}",
        "mo_ta": (d.get("description") or "")[:600],
        "ngon_ngu": d.get("primaryLanguage"),
        "giay_phep": gp,
        "chu_de": d.get("topics") or [],
        "day_cuoi": d.get("sourceUpdatedAt") or d.get("updatedAt"),
        "nguon": "tinix",
        "nguon_phat_hien": GOC + "/vi/project/" + str(d.get("slug") or ""),
    }


def thu_thap(trang=TRANG, nghi_giay: float = 2.0, in_ra=print) -> list[dict]:
    """Doc cac trang chi muc -> danh sach ung vien da chuan hoa, KHONG trung."""
    thay: dict[str, dict] = {}
    for i, tr in enumerate(trang):
        if i:
            time.sleep(nghi_giay)
        try:
            t = _lay(tr)
        except Exception as e:
            in_ra(f"  tinix {tr}: LOI {type(e).__name__}: {str(e)[:80]}")
            continue
        ds = _du_an_trong(t)
        for d in ds:
            c = _chuan(d)
            if c["full_name"]:
                thay.setdefault(c["full_name"], c)
        in_ra(f"  tinix {tr}: {len(ds)} ban ghi")
    return list(thay.values())


#: Tu khoa cho biet mot du an DANG QUAN TAM cua he nay. Dung de LOC BOT truoc
#: khi nem vao kho, vi tinix la dong chay chung: phan lon la app, game, UI.
#:
#: KHONG dung de cham diem - chi de mot du an hoan toan khong lien quan khong
#: chiem cho. `tru/finder.py` moi la cho quyet dinh muc khop.
QUAN_TAM = re.compile(
    r"trading|trader|backtest|quant|forex|metatrader|mt5|mt4|market|finance|"
    r"financial|stock|crypto|indicator|strategy|portfolio|timeseries|"
    r"time-series|scraper|scraping|crawler|crawl|spider|extract|extraction|"
    r"agent|llm|rag|pipeline|etl|dataset|telegram|browser|automation", re.I)


def loc_quan_tam(ds: list[dict]) -> tuple[list[dict], list[dict]]:
    """Tach lam hai: dang quan tam / khong. Tra ca hai de dem duoc ty le."""
    co, khong = [], []
    for d in ds:
        van = " ".join([str(d.get("full_name") or ""), str(d.get("mo_ta") or ""),
                        " ".join(d.get("chu_de") or [])])
        (co if QUAN_TAM.search(van) else khong).append(d)
    return co, khong


def nap_vao_kho(chi_quan_tam: bool = True, in_ra=print) -> dict:
    """Thu thap roi ghi vao kho cong cu cua `san_cong_cu` (khong ghi de ban cu).

    Ban ghi moi mang `trang_thai='MOI'` va `nhu_cau=None`: chua neo vao van de
    nao. `tru/finder.py` se de chung o TAM_HOAN cho toi khi co anh xa - dung
    dieu kien chu du an dat ra ("chi vao the de xuat neu khop >=1 van de").
    """
    from nhan import san_cong_cu as SCC

    ds = thu_thap(in_ra=in_ra)
    co, khong = loc_quan_tam(ds)
    dung = co if chi_quan_tam else ds
    kho = SCC.doc_kho()
    moi = 0
    for d in dung:
        k = d["full_name"]
        if k in kho:
            continue
        kho[k] = {**d, "trang_thai": "MOI", "diem": None, "nhu_cau": None,
                  "loai": "khac", "thay_luc": _bay_gio()}
        moi += 1
    if moi:
        SCC.luu_kho(kho)
    bao = {"lay_ve": len(ds), "quan_tam": len(co), "bo_qua": len(khong),
           "them_moi": moi, "kho_sau": len(kho)}
    in_ra(f"  tinix -> kho: {bao}")
    return bao


def _bay_gio() -> str:
    from nhan import so as SO
    return SO.bay_gio()
