# -*- coding: utf-8 -*-
"""doc_anh.py - ANH -> VAN BAN, cho anh chup man hinh va PDF dang anh quet.

## Vi sao

`hethong.txt`: *"file dang van ban thi goi AI boc tach co che / chuyen doi video
thanh co che, hinh anh thanh co che"*. Do 11/09/2026: `pytesseract` co trong may
nhung `tesseract.exe` THI KHONG - nen moi loi goi OCR deu nem, va khong mot anh
nao tung duoc doc. Da cai (5.4.0, 11/09).

Nguon anh THAT trong du an, khong phai gia dinh:
  - PDF Telegram la ANH QUET, khong co lop chu [[pdf-telegram-la-anh-can-ocr]]
  - sach Ky Mon / Ly phap o o F: la anh quet
  - anh chup man hinh cai dat EA (bot DongDongTV: 2 anh huong dan WebRequest)
  - bang tham so `.set` chup man hinh trong cac nhom Telegram

## Ranh gioi

Module nay CHI bien anh thanh van ban va ghi vao `noi_dung`. Bien van ban thanh
co che van la cua `doc_hieu` - mot duong, mot bo luat.

## Mot chot quan trong: OCR RAC KHONG DUOC VAO KHO

OCR tren anh xau cho ra chuoi ky tu trong GIONG chu nhung khong phai chu. Neu
de chung vao `noi_dung` thi bo doc se cham chung, hang doi tu vung se day
nhung "cum chua hieu" vo nghia, va ca hai bo do sau do deu nhieu di. `_du_sach`
chan o cua.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(GOC))
    from nhan import so as SO
else:
    from . import so as SO

KIEU = "anh_ocr"

#: Duong cai mac dinh cua ban Windows. `pytesseract` khong tu tim.
DUONG_TESSERACT = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
)
NGON_NGU = "eng+vie"


def co_tesseract() -> str | None:
    d = shutil.which("tesseract")
    if d:
        return d
    for p in DUONG_TESSERACT:
        if Path(p).exists():
            return p
    return None


def _nap():
    import pytesseract
    d = co_tesseract()
    if not d:
        raise RuntimeError(
            "khong thay tesseract.exe. `pytesseract` chi la vo boc - no goi mot "
            "chuong trinh ngoai. Cai: winget install UB-Mannheim.TesseractOCR")
    pytesseract.pytesseract.tesseract_cmd = d
    return pytesseract


#: Ty le ky tu "doc duoc" toi thieu. OCR tren anh xau cho ra chuoi trong giong
#: chu ma khong phai chu ("|_||,-. ~"). Do 11/09: van ban that o day luon > 0,80.
TY_LE_SACH = 0.72
#: Do dai toi thieu. Mot dong ba chu khong dung duoc thanh co che.
DAI_TOI_THIEU = 120


def _du_sach(vb: str) -> tuple[bool, str]:
    vb = (vb or "").strip()
    if len(vb) < DAI_TOI_THIEU:
        return False, f"qua ngan ({len(vb)} ky tu)"
    sach = sum(1 for c in vb if c.isalnum() or c.isspace() or c in ".,:;%()-+/<>=")
    ty = sach / len(vb)
    if ty < TY_LE_SACH:
        return False, f"OCR rac: chi {ty:.0%} ky tu doc duoc (can >= {TY_LE_SACH:.0%})"
    if not re.search(r"[A-Za-z\u00C0-\u1EF9]{4,}", vb):
        return False, "khong co tu nao dai >= 4 chu cai"
    return True, ""


def doc_anh(duong: Path | str, ngon_ngu: str = NGON_NGU) -> dict:
    pt = _nap()
    from PIL import Image
    p = Path(duong)
    try:
        with Image.open(p) as im:
            vb = pt.image_to_string(im, lang=ngon_ngu)
    except Exception as e:
        return {"nhan": False, "ly_do": f"{type(e).__name__}: {str(e)[:120]}"}
    ok, vi = _du_sach(vb)
    if not ok:
        return {"nhan": False, "ly_do": vi, "so_ky_tu": len(vb or "")}
    return {"nhan": True, "ly_do": "", "van_ban": vb.strip(), "cach": "anh"}


def doc_pdf_quet(duong: Path | str, toi_da_trang: int = 20,
                 ngon_ngu: str = NGON_NGU, dpi: int = 200) -> dict:
    """PDF khong co lop chu -> render tung trang roi OCR.

    Dung `pymupdf` de render, KHONG can `poppler`/`pdf2image` (mot phu thuoc
    ngoai nua tren mot may da thieu ffmpeg va tesseract).
    """
    pt = _nap()
    from PIL import Image
    import io
    import pymupdf
    p = Path(duong)
    phan = []
    try:
        with pymupdf.open(p) as d:
            # Neu PDF DA co lop chu thi khong OCR - OCR mot ban da co chu la
            # doi mot ban sach lay mot ban co loi nhan dang.
            chu = "".join((t.get_text() or "") for t in d)[:4000]
            if len(chu.strip()) > 400:
                return {"nhan": True, "van_ban": "".join(t.get_text() for t in d),
                        "cach": "pdf_co_lop_chu", "ly_do": ""}
            for i, trang in enumerate(d):
                if i >= toi_da_trang:
                    break
                pix = trang.get_pixmap(dpi=dpi)
                with Image.open(io.BytesIO(pix.tobytes("png"))) as im:
                    phan.append(pt.image_to_string(im, lang=ngon_ngu))
    except Exception as e:
        return {"nhan": False, "ly_do": f"{type(e).__name__}: {str(e)[:120]}"}
    vb = "\n".join(phan).strip()
    ok, vi = _du_sach(vb)
    if not ok:
        return {"nhan": False, "ly_do": vi, "so_ky_tu": len(vb)}
    return {"nhan": True, "ly_do": "", "van_ban": vb, "cach": "pdf_quet",
            "so_trang": len(phan)}


def doc(duong: Path | str, **kw) -> dict:
    p = Path(duong)
    if p.suffix.lower() == ".pdf":
        return doc_pdf_quet(p, **kw)
    return doc_anh(p, **kw)


def ghi(duong: Path | str, kq: dict) -> bool:
    vb = kq["van_ban"]
    vt = SO.van_tay(KIEU, str(duong), vb[:4000])
    if SO.mot("SELECT id FROM noi_dung WHERE van_tay = ?", vt):
        return False
    with SO.ket_noi() as cn:
        cn.execute(
            "INSERT INTO noi_dung(tai_lieu_id,van_tay,url,kieu,cach,so_ky_tu,"
            "so_ky_tu_goc,van_ban,luc,da_boc) VALUES(NULL,?,?,?,?,?,?,?,?,0)",
            (vt, str(duong), KIEU, kq.get("cach", "anh"), len(vb), len(vb), vb,
             SO.bay_gio()))
    return True


DUOI = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".pdf")


def mot_luot(thu_muc: list[str] | None = None, gioi_han: int = 50) -> dict:
    """Quet cac thu muc co anh/PDF trong du an."""
    tm = [GOC / x for x in (thu_muc or
                            ["ma_tai_ve", "downloaded_codes", "data/telegram",
                             "reports/clip_ddtv", "nap_tay"])]
    dem = {"thu": 0, "ghi_moi": 0, "rac": 0, "loi": 0, "da_co": 0}
    vi_du_rac = []
    for d in tm:
        if not d.exists():
            continue
        for f in sorted(d.rglob("*")):
            if dem["thu"] >= gioi_han:
                break
            if f.suffix.lower() not in DUOI or not f.is_file():
                continue
            if SO.mot("SELECT id FROM noi_dung WHERE url = ? AND kieu = ?",
                      str(f), KIEU):
                dem["da_co"] += 1
                continue
            dem["thu"] += 1
            kq = doc(f)
            if kq["nhan"]:
                dem["ghi_moi"] += 1 if ghi(f, kq) else 0
            elif "rac" in kq["ly_do"] or "qua ngan" in kq["ly_do"] \
                    or "khong co tu nao" in kq["ly_do"]:
                dem["rac"] += 1
                if len(vi_du_rac) < 5:
                    vi_du_rac.append({"file": f.name, "vi": kq["ly_do"]})
            else:
                dem["loi"] += 1
    dem["vi_du_rac"] = vi_du_rac
    return dem


if __name__ == "__main__":
    if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
        r = doc(sys.argv[1])
        print(json.dumps({k: (v[:600] if k == "van_ban" else v)
                          for k, v in r.items()}, ensure_ascii=False, indent=1))
    else:
        print("tesseract:", co_tesseract() or "KHONG THAY")
        print(json.dumps(mot_luot(), ensure_ascii=False, indent=1))
