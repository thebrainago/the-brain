# -*- coding: utf-8 -*-
"""san_sang_vps.py - HE DA CHUYEN LEN VPS DUOC CHUA.

Chu du an 12/09/2026: *"he thong se duoc chuyen len vps de chay 24/7 cam nhieu
thang nhung can xong he thong cho chuan da"*.

## VI SAO PHAI CO BO KIEM, KHONG PHAI MOT DANH SACH TRONG DAU

Chuyen may la luc moi thu "chi chay tren may nay" lo ra cung mot luc, va tren
VPS thi **khong co ai ngoi canh de thay**. Mot thu vien thieu tren may nha thi
ta thay ngay; thieu tren VPS luc 3 gio sang thi he nam im den sang hom sau -
neu EVO chua noi duoc ra ngoai thi khong ai biet.

Nen file nay chia ra BON MUC, va muc nao cung phai TRA LOI DUOC bang do dac:

    DA SAN SANG   do duoc, dat
    PHAI MANG     thu phai chep theo, kem dung luong
    PHAI CAI      phu thuoc phai cai tren may moi
    CAN NGUOI     viec khong tu lam duoc - phai co chu du an

## BA THU KHONG CHEP DUOC, PHAI LAM LAI TREN VPS

  1. **Phien Telegram** (`config/telethon_*.session`) gan voi thiet bi; dem sang
     may khac thuong bi doi dang nhap lai.
  2. **Phien trinh duyet CDP** - `doc_trinh_duyet` muon cookie tu Chrome dang
     mo. Tren VPS phai chay Chrome headless rieng.
  3. **Terminal MT5** - phai cai va dang nhap tai khoan tren chinh VPS. Va nho
     rang chi co MOT terminal (`nhan/khoa_tester.py`), nen mot viec tester treo
     tren VPS se chan ca lan do y het o day.

Chay:  python -m nhan.san_sang_vps
"""
from __future__ import annotations

import collections
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

BAO_CAO = LAB / "reports" / "SAN_SANG_VPS.md"
#: Thu muc khong tinh: nhat ky, ban luu, ma da nghi huu. `archive` va
#: `browser_backup_*` la KHO LUU - ma trong do khong chay nua, dem no vao lam
#: con so "phai sua truoc khi chuyen VPS" phong len ma khong ai sua.
BO_QUA = ("nhat_ky", "backups", "__pycache__", "nghi_huu", ".git",
          "archive", "browser_backup")

#: Thu vien Python phai co, kem viec no phuc vu. Thieu cai nao thi mat DUNG
#: nhanh do, khong phai mat ca he - nen bao cao phai noi ro mat gi.
THU_VIEN = {
    "numpy": "moi phep tinh", "pandas": "moi phep tinh",
    "MetaTrader5": "keo du lieu + Strategy Tester",
    "psutil": "do CPU cho bo dieu toc",
    "requests": "moi duong mang", "pyarrow": "doc/ghi parquet",
    "playwright": "doc trang chan bot", "telethon": "thu thap Telegram",
    "pymupdf": "doc PDF", "sklearn": "mimic - truy nguoc lich su giao dich",
    "langchain_core": "vong tu chay qwen", "openai": "goi LLM",
}

#: Bien moi truong co the dat de doi hanh vi. Khong bat buoc - deu co mac dinh -
#: nhung tren VPS thi API key la thu phai dat.
BIEN_QUAN_TRONG = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "ANTHROPIC_API_KEY",
                   "DEEPSEEK_API_KEY", "QWEN_CPU")


#: Dau hieu mot dong chi la DUONG LUI, khong phai nguon duy nhat.
_LUI = (" or Path(", "or Path(r", "_tu_bien", "ung_vien", "mac_dinh")


def duong_dan_go_cung(chi_that: bool = True) -> list[tuple[str, str, int]]:
    """Duong dan tuyet doi go cung - thu se gay khi doi may.

    ## Vi sao phai PHAN LOAI, khong chi dem

    Ban dau ham nay dem moi lan mot duong tuyet doi xuat hien. Con so ra 26,
    toi sua 33 cho, do lai van ra 28 - vi no dem ca:
      * dong LUI VE MAC DINH co chu y (`_tu_bien(...) or Path(r"C:\\...")`) -
        thu do la dung, no chi chay khi bien moi truong va phep do deu that bai;
      * chuoi trong DOCSTRING cua chinh bo va (`_va_duong_dan.py` giai thich no
        thay cai gi);
      * mau vi du (`C:\\...\\lab`).

    Mot bo kiem keu oan thi nguoi ta ngung doc no - va do la cach mot canh bao
    that bi bo qua. Nen `chi_that=True` chi dem cho NGUY: duong la NGUON DUY
    NHAT, khong co duong lui, khong nam trong chu thich.
    """
    mau = re.compile(r'["\']([A-Za-z]:[\\/][^"\']{6,90})["\']')
    dem: collections.Counter = collections.Counter()
    o_dau: dict[str, str] = {}
    for p in LAB.rglob("*.py"):
        if any(x in str(p) for x in BO_QUA):
            continue
        try:
            dong = p.read_text(encoding="utf-8-sig", errors="ignore").splitlines()
        except Exception:
            continue
        trong_doc = False
        for l in dong:
            if l.count('"""') % 2:
                trong_doc = not trong_doc
                continue
            m = mau.findall(l)
            if not m:
                continue
            if chi_that:
                if trong_doc or l.lstrip().startswith("#"):
                    continue
                if any(t in l for t in _LUI):
                    continue
                if "..." in l:                       # mau vi du
                    continue
            for x in m:
                dem[x] += 1
                o_dau.setdefault(x, p.name)
    return [(d, o_dau[d], n) for d, n in dem.most_common()]


def thu_vien_thieu() -> list[tuple[str, str]]:
    return [(m, ghi) for m, ghi in THU_VIEN.items()
            if importlib.util.find_spec(m) is None]


def dung_luong() -> dict:
    """Thu phai chep sang VPS, kem dung luong (GB)."""
    ra = {}
    for t in ("data", "reports", "config", "kho", "nap_tay", "qwen"):
        d = LAB / t
        if d.exists():
            ra[t] = round(sum(f.stat().st_size for f in d.rglob("*")
                              if f.is_file()) / 1e9, 3)
    for f in LAB.glob("*.db"):
        ra[f.name] = round(f.stat().st_size / 1e9, 3)
    return ra


def phu_thuoc_may_nay() -> list[dict]:
    """Thu KHONG chep duoc - phai lam lai tren VPS."""
    ra = []
    ss = list((LAB / "config").glob("*.session"))
    ra.append({"ten": "phien Telegram", "co": bool(ss),
               "chi_tiet": ", ".join(p.name for p in ss) or "chua co",
               "lam_gi": "dang nhap lai telethon tren VPS (`b tele`)"})
    try:
        from qwen import mo_hinh as MH
        ra.append({"ten": "kho khoa cc-switch", "co": MH.CC_SWITCH_DB.exists(),
                   "chi_tiet": str(MH.CC_SWITCH_DB),
                   "lam_gi": "chep file .db nay sang VPS, hoac dat "
                             "OPENAI_API_KEY/OPENAI_BASE_URL truc tiep"})
    except Exception as e:
        ra.append({"ten": "kho khoa cc-switch", "co": False,
                   "chi_tiet": "%s" % e, "lam_gi": "dat OPENAI_API_KEY"})
    try:
        import MetaTrader5 as mt5   # noqa: F401
        co_mt5 = True
    except Exception:
        co_mt5 = False
    ra.append({"ten": "terminal MT5 + tai khoan", "co": co_mt5,
               "chi_tiet": "goi duoc thu vien" if co_mt5 else "khong goi duoc",
               "lam_gi": "cai MT5 tren VPS, dang nhap tai khoan, va nho CHI CO "
                         "MOT terminal - mot viec tester treo se chan ca lan"})
    ra.append({"ten": "Chrome + CDP cho doc_trinh_duyet", "co": None,
               "chi_tiet": "chi biet khi chay that",
               "lam_gi": "chay Chrome headless rieng tren VPS (`b trinh-duyet`)"})
    return ra


def can_nguoi() -> list[dict]:
    """Viec he KHONG tu lam duoc."""
    ra = []
    cid = None
    try:
        cid = json.loads((LAB / "config" / "tele_bridge.json")
                         .read_text(encoding="utf-8-sig")).get("chat_id")
    except Exception:
        pass
    ra.append({
        "viec": "Bat duong bao EVO ra Telegram",
        "xong": bool(cid),
        "vi_sao": "chay nhieu thang khong nguoi truc thi EVO phai TU NOI RA; "
                  "`chat_id` hien la %s" % cid,
        "lam_the_nao": "chay `b xa` roi nhan cho bot mot tin bat ky - cau se "
                       "bat lay chat_id va ghi vao config"})
    try:
        from qwen import mo_hinh as MH
        d = MH.kiem() if hasattr(MH, "kiem") else {}
        het_quota = "quota" in json.dumps(d, ensure_ascii=False).lower()
    except Exception:
        het_quota = None
    ra.append({
        "viec": "Nap quota cho duong LLM",
        "xong": (het_quota is False),
        "vi_sao": "qwen chay duoc nhung tai khoan AI Box am quota -> moi loi goi "
                  "tra 403",
        "lam_the_nao": "nap tien, hoac dat OPENAI_API_KEY cua nha cung cap khac"})
    ra.append({
        "viec": "Chon cach he tu khoi dong lai sau khi VPS reboot",
        "xong": None,
        "vi_sao": "memory `24-7-chet-vi-lease-windows`: Task Scheduler tung bi "
                  "Access denied tren may nay",
        "lam_the_nao": "quyet dinh: Task Scheduler / dich vu Windows / "
                       "`dieu_phoi.py` chay duoi mot phien dang nhap giu mai"})
    return ra


def do_het() -> dict:
    return {"duong_go_cung": duong_dan_go_cung(),
            "thu_vien_thieu": thu_vien_thieu(),
            "dung_luong": dung_luong(),
            "phu_thuoc_may_nay": phu_thuoc_may_nay(),
            "can_nguoi": can_nguoi(),
            "bien_moi_truong": {k: bool(os.environ.get(k))
                                for k in BIEN_QUAN_TRONG}}


def bao_cao(ket: dict | None = None, in_ra=print) -> str:
    ket = ket or do_het()
    tong_gb = sum(v for v in ket["dung_luong"].values())
    d = ["# SAN SANG VPS", "",
         "Dich: **VPS chay 24/7 nhieu thang** (chu du an chot 12/09/2026).", "",
         "## 1. DA SAN SANG", ""]
    go = ket["duong_go_cung"]
    d.append("- duong dan tuyet doi go cung trong ma nguon: **%d** %s"
             % (len(go), "(ma da di dong duoc)" if len(go) <= 1 else
                "<- PHAI SUA truoc khi chuyen"))
    for duong, tep, n in go[:5]:
        d.append("  - `%s` (%s, %dx)" % (duong, tep, n))
    thieu = ket["thu_vien_thieu"]
    d.append("- thu vien Python: %s"
             % ("du het" if not thieu else "**thieu %d**" % len(thieu)))
    d += ["", "## 2. PHAI MANG THEO", "",
          "Tong **%.2f GB**:" % tong_gb, ""]
    for k, v in sorted(ket["dung_luong"].items(), key=lambda kv: -kv[1]):
        if v >= 0.001:
            d.append("- `%s` — %.2f GB" % (k, v))
    d += ["", "## 3. PHAI CAI / LAM LAI TREN VPS", ""]
    for x in ket["phu_thuoc_may_nay"]:
        dau = {True: "co san", False: "**THIEU**", None: "chua biet"}[x["co"]]
        d += ["### %s — %s" % (x["ten"], dau), "",
              "%s" % x["chi_tiet"], "", "→ %s" % x["lam_gi"], ""]
    if thieu:
        d += ["### Thu vien con thieu", ""]
        for m, ghi in thieu:
            d.append("- `%s` — mat: %s" % (m, ghi))
        d.append("")
    d += ["## 4. CAN CHU DU AN", ""]
    for x in ket["can_nguoi"]:
        dau = {True: "xong", False: "**CHUA**", None: "chua quyet"}[x["xong"]]
        d += ["### %s — %s" % (x["viec"], dau), "",
              "*Vi sao:* %s" % x["vi_sao"], "",
              "*Lam the nao:* %s" % x["lam_the_nao"], ""]
    bien = ket["bien_moi_truong"]
    d += ["## Bien moi truong", "",
          "Deu co mac dinh nen khong bat buoc, tru API key:", ""]
    for k, v in bien.items():
        d.append("- `%s` — %s" % (k, "da dat" if v else "chua dat"))
    vb = "\n".join(d) + "\n"
    BAO_CAO.parent.mkdir(exist_ok=True)
    BAO_CAO.write_text(vb, encoding="utf-8")
    if in_ra:
        in_ra(vb)
        in_ra("-> %s" % BAO_CAO)
    return vb


def main(argv: list[str]) -> int:
    bao_cao()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
