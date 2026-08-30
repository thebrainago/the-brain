# -*- coding: utf-8 -*-
"""san_cong_cu.py - DI SAN CONG CU CO SAN, thay vi tu viet lai tu dau.

VI SAO CO FILE NAY (chu du an chot 30/08/2026).

EVOLUTION cho toi hom nay chi lam mot nua viec cua no: **do suc khoe day chuyen
va tu sua nhung viec da khai bao**. Nua con lai chua ai lam: **di tim nhung du
an va cong cu da co san ngoai kia de tich hop vao he**.

Hai vi du chu du an dua ra, va ca hai deu dung:

  - `hoainama8/convertOCR` - doi PDF sang Markdown/JSON/HTML. Khau doc bai viet
    cua ta dang thieu dung thu do.
  - `coding-kitties/investing-algorithm-framework` - 2.022 sao, Apache-2.0,
    con hoat dong. Co HAI engine backtest (vector + su kien), 50+ chi so, sweep
    tham so, kiem dinh nhieu cua so (rolling/anchored/holdout/walk-forward),
    Monte Carlo permutation, bao cao HTML, ket noi san qua CCXT.

RANH GIOI PHAI GIU. Khung do manh hon `lab` o BAN THI NGHIEM, nhung no **khong
co lop chong tu lua minh** cua du an nay: khong kiem soat FDR tren ca chuong
trinh nghien cuu, khong dang ky truoc bang plan hash, khong so cai chi-them,
khong do MDE, khong canary tu chung minh la nhay, khong xuat xu chi phi
(`do_tin` DO/SAN/KHAI). Permutation test tren MOT chien luoc **khong phai** la
kiem soat sai lech khi thu hang tram gia thuyet.

Nen quy tac tich hop la mot chieu:

    Cong cu ngoai duoc lam BAN THI NGHIEM (engine, bao cao, nap du lieu).
    Cong cu ngoai KHONG BAO GIO lam ONG TOA (cong PASS, FDR, dang ky truoc).

Va: mot cong cu tim duoc la UNG VIEN, khong phai mot quyet dinh tich hop. No di
vao so nhu moi thu khac, va nguoi doc no.

Chay:
    python nhan/san_cong_cu.py            mot luot san theo NHU_CAU
    python nhan/san_cong_cu.py --xem      xem kho cong cu da tim duoc
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import so as SO
else:
    from . import so as SO

LAB = Path(__file__).resolve().parent.parent
KHO = LAB / "reports" / "cong_cu.json"

#: Giay nghi giua hai lan goi API. GitHub search khong khoa cho **10 lan/phut**.
NGHI_GIAY = 7.0

#: Giay phep dung duoc — cong cu se nam TRONG ma nguon cua du an.
GIAY_PHEP_OK = {"MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "ISC",
                "MPL-2.0", "Unlicense", "0BSD"}
#: Giay phep LAY NHIEM: dung trong du an kin thi rang buoc phai mo nguon theo.
GIAY_PHEP_LAY_NHIEM = {"GPL-3.0", "GPL-2.0", "AGPL-3.0", "LGPL-3.0"}

#: NHU CAU — cho ta DANG THIEU, viet ro truoc khi di tim.
#:
#: `cam_vao` la noi ma nao cua cong cu se duoc GOI TU. Neu mot cong cu chi de
#: doi chieu tu ben ngoai (chay rieng, so ket qua bang tay) thi `cam_vao` phai
#: la "KHONG cam vao dau ca" va dat ten dich vao `doi_chieu_voi`. Phan biet nay
#: khong phai chu nghia hinh thuc: `test_san_cong_cu` chan bat ky nhu cau nao
#: khai `cam_vao` tro toi ong toa (cong / do_luc / so / quant_plan / canary).
#:
#: Viet nhu cau truoc roi moi tim la co y: tim truoc roi moi nghi ra ly do can
#: no thi lan nao cung "tim thay thu huu ich", va do la mot dang tu lua minh
#: khac. Moi muc phai noi ro NO CAM VAO DAU va CAI GI NO KHONG DUOC THAY.
NHU_CAU = {
    "doc_pdf": {
        "vi_sao": "275 tai lieu la lien ket doi.org va 133 la arXiv PDF. "
                  "`toan_van.tu_arxiv` chi boc duoc arXiv; PDF nha xuat ban thi khong.",
        "cam_vao": "nhan/toan_van.py - them mot bo boc PDF",
        "khong_duoc_thay": "khong lien quan den cong PASS",
        "truy_van": ["pdf to markdown converter",
                     "pdf text extraction layout language:python"],
        "sao_toi_thieu": 200,
    },
    "engine_backtest": {
        "vi_sao": "engine cua ta chay dung nhung it tinh nang (khong co bao cao, "
                  "khong co sweep san, mot engine duy nhat).",
        "cam_vao": "co the lam BAN THI NGHIEM song song de doi chieu ket qua",
        "khong_duoc_thay": "TUYET DOI khong thay nhan/cong.py, nhan/do_luc.py, "
                           "nhan/so.py - do la ong toa, khong phai ban thi nghiem",
        "truy_van": ["quantitative trading backtesting framework language:python",
                     "vectorized backtesting engine language:python"],
        "sao_toi_thieu": 300,
    },
    "kiem_dinh_thong_ke": {
        "vi_sao": "FDR/LORD, deflated Sharpe, reality check cua ta tu viet. "
                  "Ban da duoc nhieu nguoi doc thi dang tin hon.",
        "cam_vao": "KHONG cam vao dau ca - chay ngoai, doc lap",
        "doi_chieu_voi": "nhan/cong.py",
        "khong_duoc_thay": "chi DOI CHIEU tu ben ngoai: hai ban tinh doc lap cung "
                           "mot con so roi so ket qua. Khong mot dong nao cua no "
                           "duoc goi tu duong quyet dinh.",
        "truy_van": ["multiple hypothesis testing false discovery rate language:python",
                     "deflated sharpe ratio probability backtest overfitting"],
        "sao_toi_thieu": 100,
    },
    "thu_thap_web": {
        "vi_sao": "reddit bi chan DNS tren may nay; nhieu nguon can dang nhap.",
        "cam_vao": "nhan/doc_trinh_duyet.py",
        "khong_duoc_thay": "khong lien quan den cong PASS",
        "truy_van": ["playwright scraping anti detection stealth language:python"],
        "sao_toi_thieu": 300,
    },
    "doc_ma_chien_luoc": {
        "vi_sao": "12/18 chien luoc .mq5 da tai ve khong co template tuong ung. "
                  "Bo phan tich ma co the rut duoc luat vao/ra.",
        "cam_vao": "nhan/ma_nguon.py + nhan/ngu_phap.py",
        "khong_duoc_thay": "ngu phap co che - kien thuc moi chi vao bang KHAI BAO",
        "truy_van": ["mql5 expert advisor parser", "pine script parser language:python"],
        "sao_toi_thieu": 30,
    },
}

#: Cong cu do chu du an chi thang. Vao kho khong qua API.
GIEO_TAY = [
    {"full_name": "hoainama8/convertOCR", "nhu_cau": "doc_pdf",
     "ghi_chu": "chu du an chi 30/08. Server Go, PDF -> md/json/html/docx/csv. "
                "OCR can cgo. Dung duoc nhu dich vu ngoai tien trinh."},
    {"full_name": "coding-kitties/investing-algorithm-framework",
     "nhu_cau": "engine_backtest",
     "ghi_chu": "chu du an chi 30/08. 2.022 sao, Apache-2.0. Hai engine "
                "(vector + su kien), 50+ chi so, sweep, kiem dinh nhieu cua so, "
                "Monte Carlo permutation, bao cao HTML, CCXT. "
                "KHONG co FDR chuong trinh / dang ky truoc / MDE / canary."},
]


# =============================================================== NHAT DOC DUONG
#: DAU HIEU cua mot cong cu nang cap duoc, tim NGAY TRONG van ban SEEKER da doc.
#:
#: Day moi la duong chinh, khong phai `tim_github`. Ly do: SEEKER **da** di qua
#: hang nghin kho ma va bai viet de san chien luoc. Thu khong phai chien luoc
#: thi hien bi bo di - trong khi `bien_dich_ung_vien.loai_ma_nguon` do duoc
#: 24/08 rang **34/52 file .mq5 la `tien_ich` hoac `chi_bao`**, tuc phan lon
#: nhung gi cham vao deu khong phai chien luoc. Trong so do co nhung thu nang
#: cap duoc chinh cai may nay.
#:
#: Nhat doc duong thi khong ton mot lan tai trang nao: van ban da nam trong so.
#:
#: KHOP THEO CUM CO RANH GIOI TU, khong khop chuoi tho. Da sap that tren chinh
#: kho nay: `rsi` khop trong **Ve-rsi-on** -> 117/156 tai lieu "co RSI".
DAU_HIEU = {
    "doc_pdf": [r"pdf\s+to\s+markdown", r"extract\s+text\s+from\s+pdf",
                r"\bpdfplumber\b", r"\bpymupdf\b", r"\bpdfminer\b",
                r"\blayout\s+aware\s+pdf\b", r"\bdocling\b"],
    "engine_backtest": [r"\bbacktest(?:ing)?\s+engine\b",
                        r"\bvectori[sz]ed\s+backtest", r"\bevent[- ]driven\s+backtest",
                        r"\bwalk[- ]forward\s+(?:analysis|optimi[sz]ation)\b"],
    "kiem_dinh_thong_ke": [r"\bfalse\s+discovery\s+rate\b", r"\bdeflated\s+sharpe\b",
                           r"\bmultiple\s+(?:hypothesis\s+)?testing\b",
                           r"\bpurged\s+(?:k[- ]fold|cross[- ]validation)\b",
                           r"\bcombinatorial\s+purged\b",
                           r"\bprobability\s+of\s+backtest\s+overfitting\b",
                           r"\breality\s+check\b", r"\bwhite'?s\s+reality\b",
                           r"\bbenjamini[- ]hochberg\b"],
    "thu_thap_web": [r"\bundetected[- ]chromedriver\b", r"\bplaywright[- ]stealth\b",
                     r"\banti[- ]?bot\s+detection\b", r"\bcloudflare\s+bypass\b"],
    "doc_ma_chien_luoc": [r"\bmql[45]\s+parser\b", r"\bpine\s*script\s+parser\b",
                          r"\bstrategy\s+(?:rule\s+)?extraction\b",
                          r"\bast\s+(?:based\s+)?(?:parser|analysis)\b"],
}

#: Van canh BAT BUOC quanh cum khop. Mot bai sinh hoc noi "reality check" khong
#: phai la cong cu kiem dinh. Cung nguyen tac voi `bien_dich_ung_vien`: chu
#: `strateg` da bi loai khoi danh sach van canh vi qua chung.
VAN_CANH = re.compile(
    r"(python|library|package|framework|repo|toolkit|module|pip install|"
    r"import |github|open[- ]source|cli|api|implementation)", re.I)

#: Khong nhat lai chinh minh, va khong nhat nhung thu da la chien luoc.
BO_QUA_URL = re.compile(r"(investing-algorithm-framework|/lab/|Research%20SP500)", re.I)

CUA_SO_VAN_CANH = 400


def xet_van_ban(tieu_de: str, van_ban: str, url: str = "",
                nguon: str = "") -> list[dict]:
    """Van ban nay co chua mot CONG CU nang cap duoc khong?

    Tra ve danh sach ung vien, moi ung vien kem **trich dan nguyen van + vi tri
    ky tu** - cung hop dong bang chung ma `CandidateArtifact` doi. Khong co
    trich dan thi khong co ung vien.

    Day KHONG phai ung vien chien luoc: no khong vao `candidate_queue`, khong
    tieu mot suat FDR nao, va khong bao gio tu dong duoc tich hop.
    """
    if not van_ban or len(van_ban) < 200:
        return []
    if url and BO_QUA_URL.search(url):
        return []
    ra: list[dict] = []
    da_co: set[str] = set()
    for nhu_cau, cac_mau in DAU_HIEU.items():
        for mau in cac_mau:
            m = re.search(mau, van_ban, re.I)
            if not m:
                continue
            i = m.start()
            quanh = van_ban[max(0, i - CUA_SO_VAN_CANH): i + CUA_SO_VAN_CANH]
            if not VAN_CANH.search(quanh):
                continue
            if nhu_cau in da_co:
                continue
            da_co.add(nhu_cau)
            ra.append({
                "nhu_cau": nhu_cau, "cum_khop": m.group(0),
                "vi_tri": i, "trich_dan": quanh.strip()[:360],
                "tieu_de": (tieu_de or "")[:160], "url": url, "nguon": nguon,
                "thay_luc": SO.bay_gio(), "trang_thai": "MOI",
                "nguon_phat_hien": "nhat_doc_duong",
            })
    return ra


def nhat_tu_ban_doc(tieu_de: str, van_ban: str, url: str = "",
                    nguon: str = "") -> int:
    """Xet mot ban doc va cat ung vien vao kho. Tra so ung vien MOI."""
    uv = xet_van_ban(tieu_de, van_ban, url, nguon)
    if not uv:
        return 0
    kho = doc_kho()
    them = 0
    for u in uv:
        khoa = f"doc:{u['nhu_cau']}:{url or tieu_de}"
        if khoa in kho:
            continue
        kho[khoa] = u
        them += 1
    if them:
        luu_kho(kho)
    return them


def quet_lai_thu_vien(gioi_han: int = 0, im_lang: bool = False) -> dict:
    """Nhat lai tren TOAN BO ban doc da co trong so.

    Chay mot lan sau khi them dau hieu moi: kho da co san hang tram ban doc,
    khong can tai lai gi.
    """
    cau = ("SELECT n.tieu_de_url, n.van_ban, n.url, n.nguon FROM ("
           "SELECT t.tieu_de AS tieu_de_url, n.van_ban, n.url, t.nguon "
           "FROM noi_dung n JOIN tai_lieu t ON t.id = n.tai_lieu_id "
           "WHERE n.so_ky_tu > 200) n")
    if gioi_han:
        cau += f" LIMIT {int(gioi_han)}"
    ds = SO.nhieu(cau)
    them, co = 0, 0
    for r in ds:
        n = nhat_tu_ban_doc(r["tieu_de_url"], r["van_ban"], r["url"], r["nguon"])
        them += n
        co += bool(n)
    if not im_lang:
        print(f"quet {len(ds)} ban doc -> {them} ung vien cong cu tu {co} ban")
    return {"ban_doc": len(ds), "ung_vien_moi": them, "ban_co_ung_vien": co}


# --------------------------------------------------------------------- KHO
def doc_kho() -> dict:
    try:
        return json.loads(KHO.read_text(encoding="utf-8"))
    except Exception:
        return {}


def luu_kho(d: dict) -> None:
    KHO.parent.mkdir(exist_ok=True)
    tam = KHO.with_suffix(".json.tam")
    tam.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tam.replace(KHO)


# ------------------------------------------------------------------- CHAM DIEM
def _tuoi_ngay(iso: str | None) -> float:
    if not iso:
        return 9_999.0
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - t).days
    except Exception:
        return 9_999.0


def cham_diem(r: dict) -> dict:
    """Diem 0-100. Khong phai phan xu — chi de xep thu tu cho NGUOI doc.

    Bon truc, moi truc toi da 25: dung nguoi (sao), con song (lan day cuoi),
    dung duoc (giay phep), va co ai kiem khong (issue/fork).
    """
    sao = int(r.get("stargazers_count") or 0)
    tuoi = _tuoi_ngay(r.get("pushed_at"))
    gp = ((r.get("license") or {}).get("spdx_id")) or "?"

    d_sao = min(25.0, 25.0 * (min(sao, 5000) / 5000) ** 0.45)
    d_song = 25.0 if tuoi <= 90 else 18.0 if tuoi <= 365 else 8.0 if tuoi <= 730 else 0.0
    d_gp = 25.0 if gp in GIAY_PHEP_OK else 10.0 if gp in GIAY_PHEP_LAY_NHIEM else 3.0
    d_cong = min(25.0, 25.0 * (min(int(r.get("forks_count") or 0), 400) / 400) ** 0.5)

    canh = []
    if gp in GIAY_PHEP_LAY_NHIEM:
        canh.append(f"giay phep {gp} LAY NHIEM - dung trong du an kin phai mo nguon theo")
    if gp == "?":
        canh.append("KHONG khai giay phep - khong duoc dua vao ma nguon du an")
    if tuoi > 730:
        canh.append(f"lan day cuoi {int(tuoi)} ngay truoc - co the da bo")
    return {"diem": round(d_sao + d_song + d_gp + d_cong, 1),
            "sao": sao, "tuoi_ngay": int(tuoi), "giay_phep": gp,
            "canh_bao": canh}


# ---------------------------------------------------------------------- TIM
def tim_github(truy_van: str, sao_toi_thieu: int = 100, so_luong: int = 8) -> list[dict]:
    import requests
    q = f"{truy_van} stars:>{sao_toi_thieu}"
    try:
        r = requests.get("https://api.github.com/search/repositories",
                         params={"q": q, "sort": "stars", "per_page": so_luong},
                         headers={"Accept": "application/vnd.github+json"}, timeout=25)
    except Exception as e:
        return [{"loi": f"{type(e).__name__}: {str(e)[:80]}"}]
    if r.status_code != 200:
        return [{"loi": f"HTTP {r.status_code}", "con_lai":
                 r.headers.get("x-ratelimit-remaining")}]
    return r.json().get("items", []) or []


def _gon(r: dict, nhu_cau: str, truy_van: str) -> dict:
    d = cham_diem(r)
    return {
        "full_name": r.get("full_name"), "url": r.get("html_url"),
        "mo_ta": (r.get("description") or "")[:220],
        "ngon_ngu": r.get("language"), "nhu_cau": nhu_cau, "truy_van": truy_van,
        "thay_luc": SO.bay_gio(), "trang_thai": "MOI", **d,
    }


# ------------------------------------------------------------------ MOT LUOT
def mot_luot(gioi_han_truy_van: int = 5, im_lang: bool = False) -> dict:
    """San mot luot. Ton it nhat co the: GitHub search khong khoa cho 10 lan/phut."""
    kho = doc_kho()

    for g in GIEO_TAY:
        if g["full_name"] not in kho:
            kho[g["full_name"]] = {
                "full_name": g["full_name"],
                "url": f"https://github.com/{g['full_name']}",
                "nhu_cau": g["nhu_cau"], "truy_van": "chu du an chi",
                "mo_ta": g["ghi_chu"], "thay_luc": SO.bay_gio(),
                "trang_thai": "MOI", "diem": None, "nguon": "nguoi_chi"}

    viec = [(k, tv) for k, v in NHU_CAU.items() for tv in v["truy_van"]]
    da_lam = {v.get("truy_van") for v in kho.values()}
    viec = [x for x in viec if x[1] not in da_lam][:gioi_han_truy_van]

    moi, loi = 0, 0
    for i, (nhu_cau, tv) in enumerate(viec):
        if i:
            time.sleep(NGHI_GIAY)
        ds = tim_github(tv, NHU_CAU[nhu_cau]["sao_toi_thieu"])
        if ds and "loi" in ds[0]:
            loi += 1
            if not im_lang:
                print(f"  [LOI ] {tv[:52]:52s} {ds[0]['loi']}")
            continue
        them = 0
        for r in ds:
            ten = r.get("full_name")
            if not ten or ten in kho:
                continue
            kho[ten] = _gon(r, nhu_cau, tv)
            them += 1
        moi += them
        if not im_lang:
            print(f"  [{them:2d} moi] {tv[:52]:52s} ({len(ds)} ket qua)")

    luu_kho(kho)

    cao = sorted((v for v in kho.values()
                  if v.get("trang_thai") == "MOI" and (v.get("diem") or 0) >= 70),
                 key=lambda v: -(v.get("diem") or 0))
    if cao:
        try:
            SO.bao_van_de(
                "cong_cu_dang_xem", "VUA",
                f"{len(cao)} cong cu ngoai diem >=70 dang cho nguoi xem tich hop. "
                f"Cao nhat: {cao[0]['full_name']} ({cao[0]['diem']}). "
                f"Quy tac: cong cu ngoai lam BAN THI NGHIEM, khong bao gio lam ONG TOA.",
                bang_chung={"top": [{"ten": c["full_name"], "diem": c["diem"],
                                     "nhu_cau": c["nhu_cau"]} for c in cao[:8]]})
        except Exception:
            pass
    return {"tim_them": moi, "loi": loi, "tong_kho": len(kho),
            "diem_cao": len(cao)}


def xem(toi_da: int = 25) -> None:
    kho = doc_kho()
    if not kho:
        print("kho cong cu rong - chay `python nhan/san_cong_cu.py` truoc")
        return
    ds = sorted(kho.values(), key=lambda v: -(v.get("diem") or 0))
    print(f"KHO CONG CU: {len(kho)} muc\n")
    for v in ds[:toi_da]:
        d = v.get("diem")
        print(f"  {(f'{d:5.1f}' if d is not None else '  -  ')}  "
              f"{str(v.get('nhu_cau')):20s} {v['full_name']}")
        if v.get("mo_ta"):
            print(f"           {v['mo_ta'][:100]}")
        for c in v.get("canh_bao", []):
            print(f"           /!\\ {c}")


if __name__ == "__main__":
    if "--xem" in sys.argv:
        xem()
    else:
        print(json.dumps(mot_luot(), ensure_ascii=False, indent=1))
