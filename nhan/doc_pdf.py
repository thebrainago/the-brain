# -*- coding: utf-8 -*-
"""doc_pdf.py - PDF -> van ban, co OCR cho trang la ANH.

VI SAO CO FILE NAY.

04/09/2026 lay ve 17 PDF chien luoc tu kenh Telegram, va chu du an noi: *"he
thong nay cuc ki ro den the roi ma van khong loc ra thi la ta sai"*. Do lai thi
ong dung, nhung cho sai KHONG phai bo loc:

    Giao dich thuat toan chuyen sau #2 : 46 trang, 39 anh, 3.074 ky tu
    GIAO DICH THUAT TOAN CHUYEN SAU b1 : 34 trang, 52 anh, 3.439 ky tu
    AI vs con nguoi                    : 16 trang, 24 anh, 1.558 ky tu

**~67 ky tu mot trang.** Day la slide xuat thanh ANH; lop van ban gan nhu rong.
`boc_llm._diem_luat` cham dung cai no duoc dua, va no chua bao gio duoc dua noi
dung that. Tai lieu **khong bi loai - no chua tung duoc doc**. Do la ho loi
"ket luan am phai phan biet CHUA DO", va sua bo loc se khong bao gio cham toi.

CHON ENGINE - da do, khong doan:

  - **Windows.Media.Ocr** (thu dau tien vi `lab/darwinex_ocr.py` da dinh dung):
    may nay chi co **en-US**. Khong doc duoc tieng Viet co dau. Va `_ocr.ps1`
    ma module do goi thi **khong ton tai**.
  - **Tesseract**: `pytesseract` da cai nhung **khong co ban nhi phan** nao
    tren may, va con phai them `vie.traineddata`.
  - **EasyOCR** (chon): da cai san cung `torch 2.13`, ho tro `vi`, khong can
    cai them gi. Do that tren mot trang slide: doc dung dau tieng Viet
    ("Y tuong giao dich", "Giau di cac thong so chinh xac & tinh chinh can
    thiet"), **14,2 giay/trang** tren CPU 10 luong.

QUY TAC: **KHONG OCR trang da co chu.** Lop van ban that luon tot hon OCR (khong
sai chinh ta, giu duoc bang bieu). Chi trang mong hon `SAN_CHU_MOI_TRANG` moi
dua qua OCR. Nho vay mot PDF binh thuong khong ton mot giay OCR nao.
"""
from __future__ import annotations

import time
from pathlib import Path

from nhan import so as SO

#: Duoi muc nay thi coi nhu trang KHONG co lop van ban -> OCR.
#: 200 ky tu la khoang mot doan van ngan; slide-anh do duoc ~67.
SAN_CHU_MOI_TRANG = 200

#: DPI khi dung trang thanh anh.
#:
#: DA DOI 200 -> 150 sau khi DO (04/09/2026, 3 trang slide, may ranh):
#:     DPI 200: 14,4 s/trang -> 656 ky tu
#:     DPI 150:  9,4 s/trang -> 637 ky tu
#:     DPI 110:  5,3 s/trang -> 615 ky tu
#: Toc do ti le nghich voi DPI dung nhu du doan, nhung SO CHU thi gan nhu khong
#: doi (-3% khi ha xuong 150). Tuc DPI 200 dang tra gap ruoi thoi gian de doc
#: them 3% chu - mot doi doan te.
DPI = 150

#: Tran ky tu mot tai lieu ghi vao kho.
TRAN_KY_TU = 200_000

#: Ngon ngu OCR. `vi` keo theo bo Latin nen tieng Anh xen ke van doc duoc.
NGON_NGU = ("vi", "en")

#: Dung bo PHAT HIEN cua RapidOCR thay cho CRAFT cua EasyOCR.
#:
#: VI SAO. Chu du an hoi "lau vay sao?" ve moc ~100 phut, va cau hoi do dung -
#: toi da NHAN con so 14,2 s/trang ma chua he hoi thoi gian di dau. Do ra:
#:
#:     tach EasyOCR: phat hien 8,1 s | nhan dang 0,6 s
#:
#: **93% thoi gian la bo PHAT HIEN chu (CRAFT), khong phai nhan dang.** Nen moi
#: no luc toi uu bo nhan dang deu vo nghia, va cach dung la thay bo phat hien.
#:
#: Do tiep tren cung 4 trang:
#:     EasyOCR  DPI 200 : 14,4 s/trang |  656 ky tu | dau tieng Viet DUNG
#:     EasyOCR  DPI 110 :  5,3 s/trang |  908 ky tu | dau DUNG
#:     RapidOCR DPI 150 :  2,0 s/trang |  962 ky tu | **MAT SACH DAU**
#:                        ("DICH THUAT TOAN", "strc manh", "phu de")
#:     GHEP (mac dinh)  :  3,9 s/trang |  990 ky tu | dau gan dung
#:
#: RapidOCR nhanh vi bo nhan dang mac dinh cua no la PP-OCRv4 tieng Trung+Anh -
#: no khong biet dau tieng Viet, va do khong phai thu sua duoc bang tham so.
#: Nen lay bo PHAT HIEN cua no (DBNet/ONNX, nhanh) va giu bo NHAN DANG tieng
#: Viet cua EasyOCR. Ket qua: **nhanh 3,7 lan, va ra NHIEU chu hon ca hai**.
#:
#: `False` de quay ve EasyOCR thuan neu ban ONNX co van de.
GHEP_PHAT_HIEN = True

_READER = None
_RAPID = None


def _reader():
    """Nap model MOT lan cho ca tien trinh - nap lai moi trang la 3,3s/trang."""
    global _READER
    if _READER is None:
        import easyocr
        _READER = easyocr.Reader(list(NGON_NGU), gpu=False, verbose=False)
    return _READER


def _rapid():
    global _RAPID
    if _RAPID is None:
        from rapidocr_onnxruntime import RapidOCR
        _RAPID = RapidOCR()
    return _RAPID


def _hop_chu(img) -> list[list[int]]:
    """Vi tri cac khoi chu, do RapidOCR tim. Tra `[x0, x1, y0, y1]`."""
    kq, _ = _rapid()(img)
    ra = []
    for muc in (kq or []):
        box = muc[0] if isinstance(muc[0], (list, tuple)) else muc
        xs = [q[0] for q in box]
        ys = [q[1] for q in box]
        ra.append([int(min(xs)), int(max(xs)), int(min(ys)), int(max(ys))])
    return ra


def _ocr_anh(img) -> str:
    """Mot anh -> van ban. Ghep hai engine neu bat, khong thi EasyOCR thuan."""
    if GHEP_PHAT_HIEN:
        try:
            hop = _hop_chu(img)
            if not hop:
                return ""
            kq = _reader().recognize(img, horizontal_list=hop, free_list=[],
                                     detail=1)
            return "\n".join(k[1] for k in kq)
        except Exception:
            pass  # ONNX hong thi roi ve duong cu, khong lam hong ca luot quet
    kq = _reader().readtext(img, detail=1, paragraph=True)
    return "\n".join(k[1] for k in kq)


def doc_mot_trang(trang, ocr: bool = True) -> tuple[str, str]:
    """Mot trang -> (van ban, cach lay). `cach` la 'chu' hoac 'ocr'."""
    vb = trang.get_text() or ""
    if len(vb.strip()) >= SAN_CHU_MOI_TRANG or not ocr:
        return vb, "chu"
    import numpy as np
    pix = trang.get_pixmap(dpi=DPI)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = img[:, :, :3]
    try:
        ra = _ocr_anh(img)
    except Exception:
        return vb, "chu"
    # OCR chi THAY lop chu khi no doc duoc NHIEU HON. Mot trang chi co logo se
    # cho OCR ra vai ky tu rac, va de nguyen lop chu goc thi honest hon.
    return (ra, "ocr") if len(ra.strip()) > len(vb.strip()) else (vb, "chu")


def doc_file(duong: Path | str, ocr: bool = True, tran_trang: int | None = None,
             in_ra=None) -> dict:
    """Mot PDF -> van ban day du + thong ke tung cach lay."""
    import pymupdf
    duong = Path(duong)
    t0 = time.time()
    try:
        d = pymupdf.open(duong)
    except Exception as e:
        return {"file": duong.name, "loi": f"{type(e).__name__}: {str(e)[:80]}"}
    phan, dem = [], {"chu": 0, "ocr": 0}
    n = len(d) if tran_trang is None else min(len(d), tran_trang)
    for i in range(n):
        vb, cach = doc_mot_trang(d[i], ocr=ocr)
        dem[cach] += 1
        if vb.strip():
            phan.append(vb)
        if in_ra and (i + 1) % 10 == 0:
            in_ra(f"    {duong.name[:40]}: {i+1}/{n} trang "
                  f"({time.time()-t0:.0f}s)")
    d.close()
    vb = "\n\n".join(phan)[:TRAN_KY_TU]
    return {"file": duong.name, "duong": str(duong), "trang": n,
            "trang_chu": dem["chu"], "trang_ocr": dem["ocr"],
            "ky_tu": len(vb), "van_ban": vb,
            "giay": round(time.time() - t0, 1)}


def ghi_kho(kq: dict, nguon: str) -> dict:
    """Ghi mot PDF da doc vao `tai_lieu` + `noi_dung`.

    `url` la duong dan file tren dia. Do khong dep bang mot dia chi web, nhung
    no la XUAT XU THAT cua ban ghi nay va tra nguoc lai duoc - dung yeu cau
    provenance cua `nhan/ma_nguon.py`.
    """
    vb = kq.get("van_ban") or ""
    if len(vb.strip()) < 400:
        return {"ghi": False, "ly_do": "duoi 400 ky tu"}
    url = "file:///" + str(kq["duong"]).replace("\\", "/")
    vt = SO.van_tay(url)
    ra = {"ghi": True, "tai_lieu_moi": 0, "ban_doc_moi": 0}
    with SO.ket_noi() as cn:
        cur = cn.execute(
            "INSERT OR IGNORE INTO tai_lieu(van_tay,nguon,loai,tieu_de,url,"
            "tom_tat,tu_khoa,diem,luc) VALUES(?,?,?,?,?,?,?,?,?)",
            (vt, nguon, "pdf", kq["file"][:180], url, vb[:2000], "pdf", 2.5,
             SO.bay_gio()))
        ra["tai_lieu_moi"] = cur.rowcount
        row = cn.execute("SELECT id FROM tai_lieu WHERE van_tay=?",
                         (vt,)).fetchone()
        if not row:
            return {"ghi": False, "ly_do": "khong lay duoc tai_lieu_id"}
        cach = "pdf_ocr" if kq.get("trang_ocr") else "pdf_chu"
        cur2 = cn.execute(
            "INSERT OR IGNORE INTO noi_dung(tai_lieu_id,van_tay,url,kieu,cach,"
            "so_ky_tu,so_ky_tu_goc,van_ban,luc,da_boc) "
            "VALUES(?,?,?,'bai_bao',?,?,?,?,?,0)",
            (row["id"], SO.van_tay("nd", url), url, cach, len(vb), len(vb), vb,
             SO.bay_gio()))
        ra["ban_doc_moi"] = cur2.rowcount
    return ra


def quet_thu_muc(goc: Path | str, nguon_tien_to: str = "pdf",
                 ocr: bool = True, gioi_han: int | None = None,
                 in_ra=print) -> dict:
    """Doc moi PDF trong mot cay thu muc, ghi vao kho, bo qua file da co.

    `nguon` cua tung file lay theo THU MUC CHA - voi kho Telegram thi do la
    ten kenh, nen ban ghi giu duoc no den tu kenh nao.
    """
    goc = Path(goc)
    ds = sorted(goc.rglob("*.pdf"))
    if gioi_han:
        ds = ds[:gioi_han]
    bao = {"file": len(ds), "doc": 0, "ghi": 0, "bo_qua": 0, "loi": 0,
           "trang_chu": 0, "trang_ocr": 0, "ky_tu": 0, "giay": 0.0}
    t0 = time.time()
    for f in ds:
        url = "file:///" + str(f).replace("\\", "/")
        if SO.mot("SELECT id FROM tai_lieu WHERE van_tay=?", SO.van_tay(url)):
            bao["bo_qua"] += 1
            continue
        kq = doc_file(f, ocr=ocr, in_ra=in_ra)
        if kq.get("loi"):
            bao["loi"] += 1
            in_ra(f"  LOI {f.name[:45]}: {kq['loi']}")
            continue
        bao["doc"] += 1
        bao["trang_chu"] += kq["trang_chu"]
        bao["trang_ocr"] += kq["trang_ocr"]
        bao["ky_tu"] += kq["ky_tu"]
        cha = f.parent.name
        g = ghi_kho(kq, f"{nguon_tien_to}_{cha}" if cha else nguon_tien_to)
        if g.get("ghi"):
            bao["ghi"] += g["ban_doc_moi"]
        in_ra(f"  {kq['trang']:>3} trang ({kq['trang_ocr']} OCR) "
              f"{kq['ky_tu']:>7,} ky tu  {kq['giay']:>6.0f}s  {f.name[:45]}")
    bao["giay"] = round(time.time() - t0, 1)
    SO.ghi_chi_so("doc_pdf_ban_doc", float(bao["ghi"]), {"goc": str(goc)})
    in_ra(f"PDF: {bao}")
    return bao
