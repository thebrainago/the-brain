# -*- coding: utf-8 -*-
"""ban_do.py - SINH ban do he thong TU CHINH MA NGUON.

## Vi sao khong viet tay

`BAN_DO.md` viet tay ngay 30/08. Do 12/09: 60 dong, va **khong co mot module nao
trong 11 module moi** (`to_hop`, `suy_nguoc`, `vao_lenh`, `dap_quan_tri`,
`vong_day_du`, `don_mo_coi`, `duong_dan`, `san_sang_vps`, `doc_lenh_tester`...).

Mot ban do loi thoi te hon khong co ban do: nguoi doc tin no, roi dung lai thu
da co (toi lam dung viec do BA LAN trong mot ngay - `uu_tien.py`, `noi_sinh.py`,
va ca mot EVO thu hai).

## CAU HOI CHINH NO TRA LOI

Khong phai "lab co nhung file gi" - `ls` lam duoc. Ma la:

    **Module nay co nam tren mot DUONG CHAY nao khong?**

Do la luat L7 trong `LUAT_GIAM_SAT.md`: *cong cu khong nam tren duong chay thi
bang khong co*. Bang chung da co that: `du_lieu.kiem()` co du 5 bay chat luong
ma khong noi nao doc `dung_duoc`; bay "rau nen hong" dem duoc 154 bar hong cua
GBPZAR tu truoc ma khong ai doc.

Bon DUONG CHAY duoc coi la that:
    b.py             lenh nguoi go
    dieu_phoi.py     5 tru chay 24/7
    qwen/NHIEM_VU.json  bang viec tu chay
    day_viec.py      hang doi viec xay

Module nao khong duoc goi tu bat ky duong nao (truc tiep hoac qua mot module
khac da noi day) thi bi danh **MO COI** - va do la thu dang doc nhat trong ban do.

Chay:  python -m nhan.ban_do          in ra
       python -m nhan.ban_do --ghi    ghi de BAN_DO.md
"""
from __future__ import annotations

import ast
import json
import re
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

TEP = LAB / "BAN_DO.md"
BO_QUA = ("nhat_ky", "backups", "__pycache__", "nghi_huu", ".git", "archive",
          "browser_backup", "reports", "data")

#: Cac cua vao - tu day lan ra thi biet cai gi thuc su duoc chay.
CUA_VAO = ("b.py", "dieu_phoi.py", "day_viec.py", "BAN_GIAO.py", "KET_PHIEN.py")


def _tu_cmd() -> set[str]:
    """Cua vao nam trong `.cmd`/`.bat` o goc lab.

    Ban dau toi bo qua lop nay va ban do bao ca goi `qwen/` la MO COI - trong
    khi `q.cmd` goi thang `-m qwen.chay`. Mot ban do bao nham nhu the con te
    hon ban do cu: no khien nguoi doc xoa thu dang chay.
    """
    ra = set()
    for p in list(LAB.glob("*.cmd")) + list(LAB.glob("*.bat")):
        try:
            vb = p.read_text(encoding="utf-8-sig", errors="ignore")
        except Exception:
            continue
        for m in re.findall(r"-m\s+([\w.]+)", vb):
            ra.add(m.replace(".", "/") + ".py")
        for m in re.findall(r"([\w_]+\.py)", vb):
            ra.add(m)
    return ra


def _cac_file() -> list[Path]:
    return [p for p in sorted(LAB.rglob("*.py"))
            if not any(x in str(p) for x in BO_QUA)]


def _mo_ta(p: Path) -> str:
    """Dong dau cua docstring - moi module trong lab deu tu khai no lam gi."""
    try:
        cay = ast.parse(p.read_text(encoding="utf-8-sig", errors="ignore"))
    except Exception:
        return ""
    d = ast.get_docstring(cay) or ""
    dong = d.strip().splitlines()
    if not dong:
        return ""
    t = dong[0].strip()
    return re.sub(r"^[\w./\\]+\.py\s*[-–]\s*", "", t)[:96]


def _khoa(p: Path) -> str:
    return str(p.relative_to(LAB)).replace("\\", "/")


def do_thi() -> dict:
    """{file: set(file duoc no goi)}. Doc `import` + goi lenh trong chuoi."""
    fs = _cac_file()
    ten_theo_mo_dun: dict[str, str] = {}
    for p in fs:
        k = _khoa(p)
        ten_theo_mo_dun[k[:-3].replace("/", ".")] = k
    tap_khoa = {_khoa(q) for q in fs}      # dung MOT lan, khong trong vong lap
    canh: dict[str, set] = {}
    for p in fs:
        k = _khoa(p)
        canh[k] = set()
        try:
            vb = p.read_text(encoding="utf-8-sig", errors="ignore")
        except Exception:
            continue
        # import nhan.X / from nhan import X / from . import X
        for m in re.findall(r"(?:from|import)\s+((?:nhan|tru|qwen)[\w.]*)", vb):
            if m in ten_theo_mo_dun:
                canh[k].add(ten_theo_mo_dun[m])
        for goi, tap in (("nhan", "nhan"), ("tru", "tru"), ("qwen", "qwen")):
            for m in re.findall(r"from\s+%s\s+import\s+\(?([\w, ]+)" % goi, vb):
                for t in re.split(r"[,\s]+", m):
                    ung = "%s.%s" % (tap, t.strip())
                    if t.strip() and ung in ten_theo_mo_dun:
                        canh[k].add(ten_theo_mo_dun[ung])
        # `from . import X` - import TUONG DOI, giai nghia theo thu muc cua
        # chinh file. Bo qua khau nay thi ca goi `qwen/` bao MO COI trong khi
        # `q.cmd` dang chay no hang ngay: bo do mu cho ra AM TINH GIA, khong
        # phai thuc te am - dung ho benh voi `bo-do-nhin-truoc-mu-voi-co-che-thua`.
        thu_muc = k.rsplit("/", 1)[0] if "/" in k else ""
        if thu_muc:
            for m in re.findall(r"from\s+\.\s+import\s+\(?([\w, ]+)", vb):
                for t in re.split(r"[,\s]+", m):
                    ung = "%s/%s.py" % (thu_muc, t.strip())
                    if t.strip() and ung in tap_khoa:
                        canh[k].add(ung)
            for m in re.findall(r"from\s+\.([\w]+)\s+import", vb):
                ung = "%s/%s.py" % (thu_muc, m)
                if ung in tap_khoa:
                    canh[k].add(ung)
        # goi qua dong lenh: "-m", "nhan.X"  hoac  "X.py"
        for m in re.findall(r'["\']((?:nhan|tru|qwen)\.[\w.]+)["\']', vb):
            if m in ten_theo_mo_dun:
                canh[k].add(ten_theo_mo_dun[m])
        # `"X.py"` co the la file goc lab HOAC mot file trong goi, vi `b.py`
        # ghep duong bang `LAB / "nhan" / "X.py"` - chuoi trong ma chi con
        # `"X.py"`. Khong thu ca dang co tien to goi thi moi lenh `b` goi mot
        # module trong `nhan/` deu bi bao MO COI. Day la lan MU THU BA cua bo
        # do nay trong mot phien (sau `.cmd` va `from . import`) - dung ly do
        # de co luat L16: bo do ket luan "khong co" phai thay duoc cai CO.
        for m in re.findall(r'["\']([\w_]+\.py)["\']', vb):
            for ung in (m, "nhan/" + m, "tru/" + m, "qwen/" + m):
                if ung in tap_khoa:
                    canh[k].add(ung)
    return canh


def _tu_bang_qwen() -> set[str]:
    """File duoc bang viec qwen goi."""
    ra = set()
    try:
        d = json.loads((LAB / "qwen" / "NHIEM_VU.json")
                       .read_text(encoding="utf-8-sig"))
        ds = d["viec"] if isinstance(d, dict) else d
        for v in ds:
            for t in (v.get("lenh") or []):
                t = str(t)
                if t.endswith(".py"):
                    ra.add(t)
                elif t.startswith(("nhan.", "tru.", "qwen.")):
                    ra.add(t.replace(".", "/") + ".py")
    except Exception:
        pass
    return ra


def voi_toi_duoc() -> tuple[set[str], dict]:
    """Tap file VOI TOI DUOC tu cac cua vao (lan theo do thi goi)."""
    canh = do_thi()
    goc = {c for c in CUA_VAO if c in canh} | _tu_bang_qwen() | _tu_cmd()
    goc |= {k for k in canh if k.startswith("tru/")}     # tru chay trong dieu phoi
    toi = set()
    hang = list(goc)
    while hang:
        k = hang.pop()
        if k in toi or k not in canh:
            continue
        toi.add(k)
        hang.extend(canh[k] - toi)
    return toi, canh


def sinh(in_ra=print) -> str:
    """Hai loai MO COI, va tron chung lai thi ban do vo dung.

    Lan sinh dau ra 211 mo coi. Nhung 85 trong so do la `_*.py` o goc lab -
    script chay TAY mot lan cho mot cau hoi cu the (`_ghep_h4.py`,
    `_mo_xe_z5.py`...). Chung mo coi la DUNG BAN CHAT, khong phai lo hong.
    De chung chung bang voi `nhan/cham_diem.py` thi 34 dong that bi 177 dong
    nhieu che mat - va mot ban do khong ai doc thi bang khong co ban do.
    """
    toi, canh = voi_toi_duoc()
    fs = _cac_file()

    # BA bac, khong phai hai. Mot module chi duoc script chay tay goi la HA TANG
    # hop le (`doc_anh` cho `darwinex_ocr.py`, `doc_pdf` cho khau doc...), khong
    # phai lo hong. Gop no chung voi thu that su khong ai goi thi lai che mat
    # dung cai can doc - cung ly do da tach `_*.py` ra o tren.
    tay_khoa = {k for k, _ in []}
    mo_coi, tren_duong, tay = [], [], []
    for p in fs:
        k = _khoa(p)
        if k.startswith("test_") or "/test_" in k:
            continue
        if k in toi:
            tren_duong.append((k, _mo_ta(p)))
        elif "/" not in k or k.rsplit("/", 1)[1].startswith("_"):
            tay.append((k, _mo_ta(p)))          # script chay tay - binh thuong
            tay_khoa.add(k)
        else:
            mo_coi.append((k, _mo_ta(p)))

    goi_boi_tay = set()
    for k in tay_khoa:
        goi_boi_tay |= canh.get(k, set())
    ha_tang = [(k, m) for k, m in mo_coi if k in goi_boi_tay]
    mo_coi = [(k, m) for k, m in mo_coi if k not in goi_boi_tay]

    # `quant/` la KHO CU (12-15/08/2026), truoc lan tai cau truc lab. Vai file
    # trong do van duoc goi (`cham_lai_the_he.py` co import), so con lai la co
    # che thu nghiem doi cu. Tach ra de khong ai tuong phai di noi chung vao -
    # viec dung voi chung la XEM CO GI DANG LAY roi don, khong phai noi day.
    kho_cu = [(k, m) for k, m in mo_coi if k.startswith("quant/")]
    mo_coi = [(k, m) for k, m in mo_coi if not k.startswith("quant/")]

    d = ["# BAN DO HE THONG — sinh tu ma nguon", "",
         "*%s · %d file .py · %d tren duong chay · **%d MO COI THAT** · "
         "%d ha tang · %d kho cu `quant/` · %d script chay tay*"
         % (time.strftime("%Y-%m-%d %H:%M"), len(fs), len(tren_duong),
            len(mo_coi), len(ha_tang), len(kho_cu), len(tay)), "",
         "Sinh boi `python -m nhan.ban_do --ghi`. **Dung sua tay** - ban viet",
         "tay ngay 30/08 da loi thoi 13 ngay va bo sot 11 module, va mot ban do",
         "loi thoi lam nguoi doc dung lai thu da co.", "",
         "## Ba tru theo so do cua chu du an", ""]
    for tru, ten in (("tru/seeker.py", "SEEKER"),
                     ("tru/quantlab.py", "QUANTLAB"),
                     ("tru/evolution.py", "EVO")):
        p = LAB / tru
        if p.exists():
            d.append("- **%s** `%s` — %s" % (ten, tru, _mo_ta(p)))
    d += ["", "## MODULE MO COI — khong duong chay nao goi toi", "",
          "Luat L7: *cong cu khong nam tren duong chay thi bang khong co*.",
          "Day la module trong goi (`nhan/`, `tru/`, `qwen/`), khong phai script",
          "chay tay - nen moi dong o day hoac (a) can noi vao mot cua vao,",
          "hoac (b) la ha tang cho thu chua xay xong.", ""]
    if mo_coi:
        for k, m in sorted(mo_coi):
            d.append("- `%s` — %s" % (k, m or "(khong co docstring)"))
    else:
        d.append("- (khong co)")
    if kho_cu:
        d += ["", "## Kho cu `quant/` — %d file" % len(kho_cu), "",
              "Tu 12-15/08/2026, truoc lan tai cau truc lab. Viec dung voi chung",
              "la XEM CO GI DANG LAY roi don di, khong phai noi vao duong chay.",
              ""]
        d.append("`" + "` · `".join(k.split("/")[-1][:-3]
                                    for k, _ in sorted(kho_cu)) + "`")
    d += ["", "## Ha tang cho script chay tay — %d module" % len(ha_tang), "",
          "Khong cua vao nao goi THANG, nhung mot script chay tay co goi. Do la",
          "thu vien hop le, khong phai lo hong - de chung chung voi muc tren thi",
          "lai che mat dung cai can doc.", ""]
    for k, m in sorted(ha_tang):
        d.append("- `%s` — %s" % (k, m or ""))
    d += ["", "## Script chay tay (`_*.py` va file goc lab) — %d file" % len(tay),
          "",
          "Mo coi la DUNG ban chat: moi cai tra loi mot cau hoi cu the mot lan.",
          "Liet ke gon de khong che mat muc tren.", ""]
    d.append("`" + "` · `".join(k.rsplit("/", 1)[-1][:-3]
                                for k, _ in sorted(tay)) + "`")
    d += ["", "## Tren duong chay", ""]
    for goi in ("nhan/", "tru/", "qwen/", ""):
        nhom = [(k, m) for k, m in tren_duong
                if (k.startswith(goi) if goi else "/" not in k)]
        if not nhom:
            continue
        d += ["### %s" % (goi or "goc lab"), ""]
        for k, m in sorted(nhom):
            d.append("- `%s` — %s" % (k, m or ""))
        d.append("")
    vb = "\n".join(d) + "\n"
    if in_ra:
        in_ra("%d file · %d tren duong chay · %d MO COI"
              % (len(fs), len(tren_duong), len(mo_coi)))
        for k, m in sorted(mo_coi)[:20]:
            in_ra("  MO COI  %-34s %s" % (k, (m or "")[:50]))
    return vb


def main(argv: list[str]) -> int:
    vb = sinh()
    if "--ghi" in argv:
        TEP.write_text(vb, encoding="utf-8")
        print("\n-> %s" % TEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
