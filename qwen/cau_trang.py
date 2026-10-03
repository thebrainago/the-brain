# -*- coding: utf-8 -*-
"""cau_trang.py - DANH SACH TRANG cho don hang cua cau noi hai may.

## Vi sao (02/10/2026)

`viec/cho/*.json` mang lenh THAT se chay tren may chu du an khi `q` hay `b cau chay` keo ve. Truoc day
`chay_don` chay BAT KY `lenh` nao. Mot don sai - do phien cloud bi lua boi noi dung ben ngoai, hay do ai do
day duoc len nhanh - la chay ma tuy y tren may co khoa API, du lieu va MT5.

Moi don nay phai qua `kiem_lenh()`:
  1. lenh bat dau bang `{py}` (khong bao gio chay file thuc thi tuy y)
  2. phan con lai khop MOT trong cac HINH khai bao o duoi: `b.py <lenh b>`, `-m pytest ...`, `-m <module>`,
     `<script>.py ...`, hoac ping
  3. khong khop -> KHONG chay: ket qua `CHUA_DO_DUOC` + ly do. Chu du an co the DUYET dung don do tren may
     (`b cau duyet <ma>`); ban ghi duyet gan voi VAN TAY cua lenh - doi mot ky tu la mat hieu luc.

## Gioi han (noi that)

Danh sach nam trong ma nen no chan LOI va LENH BI TIEM vao phien cloud. No KHONG chan ke da day duoc len nhanh
(ho sua duoc ca file nay). Cho do: kho private + xac thuc hai lop cho tai khoan GitHub.

Ky luat nghien cuu (niem phong mot lan, dem phep thu) nam TRONG cong cu, nen cho `b nc cc <cong cu>` chay la an
toan; viec them lenh moi = sua MA o day (co review), khong phai sua mot file don.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
DUYET = GOC / "config" / "cau_duyet.json"      # may-cuc-bo, bi gitignore: cloud KHONG ghi duoc vao day

_MA = re.compile(r"^[A-Z0-9][A-Z0-9_.]{1,31}$")
_KHUNG = {"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"}
_BIEU_THUC = re.compile(r"^[A-Za-z0-9_ ()]{1,200}$")                 # cho `-k` / `-m` cua pytest
_FILE_TEST = re.compile(r"^test_[A-Za-z0-9_]+\.py(::[A-Za-z0-9_]+){0,2}$")
_TB = {"short", "no", "line", "auto", "long"}
PING = ["-c", "print('CAU NOI SONG')"]


def _so(lo: int, hi: int):
    return lambda s: s.isdigit() and lo <= int(s) <= hi


def _json_obj(s: str) -> bool:
    try:
        return len(s) <= 20_000 and isinstance(json.loads(s), dict)
    except Exception:
        return False


def _cong_cu(s: str) -> bool:
    from nhan import nc_cong_cu as CC
    return s in CC.THEO_TEN


def _van_ban(lo: int, hi: int):
    """Mot dong chu thuong (cau hoi / y tuong): in duoc, mot dong, do dai lo..hi. Khong phai co (`--...`)."""
    return lambda s: lo <= len(s) <= hi and s.isprintable() and not s.startswith("-")


def _thuc01(s: str) -> bool:
    try:
        return 0.0 <= float(s) <= 1.0
    except ValueError:
        return False


def _khung(s: str) -> bool:
    return s in _KHUNG


def _ma_hex10(s: str) -> bool:
    return re.fullmatch(r"[0-9a-f]{10}", s) is not None


def _url_cho_tham_do(s: str) -> bool:
    """Link CONG KHAI duoc tham do qua don: https + ten mien da duyet, khong rieng (`link_nguon.cho_tham_do`)."""
    from nhan import link_nguon as LN
    return len(s) <= 400 and s.isprintable() and LN.cho_tham_do(s)[0]


class Hinh:
    """Mot hinh lenh: `pos` = [(ham_kiem, bat_buoc)...] theo thu tu; `co` = {"--co": ham_kiem | None (co khong gia tri)}."""

    def __init__(self, pos=(), co=None):
        self.pos, self.co = list(pos), dict(co or {})

    def kiem(self, con: list[str]) -> str | None:
        vi_tri, i = 0, 0
        gap = set()
        while i < len(con):
            a = con[i]
            if a.startswith("--"):
                if a not in self.co:
                    return "co khong duoc phep: %s" % a[:60]
                if a in gap:
                    return "co lap lai: %s" % a
                gap.add(a)
                if self.co[a] is not None:
                    i += 1
                    if i >= len(con) or not self.co[a](con[i]):
                        return "gia tri khong hop le cho %s" % a
            else:
                if vi_tri >= len(self.pos):
                    return "thua doi so: %r" % a[:60]
                if not self.pos[vi_tri][0](a):
                    return "doi so thu %d khong hop le: %r" % (vi_tri + 1, a[:80])
                vi_tri += 1
            i += 1
        for j, (_, bat_buoc) in enumerate(self.pos):
            if bat_buoc and j >= vi_tri:
                return "thieu doi so thu %d" % (j + 1)
        return None


#: `b.py <lenh>` - khoa la bo ten lenh (dai nhat khop truoc)
LENH_B: dict[tuple, Hinh] = {
    ("nc", "so-tay"): Hinh(),
    ("nc", "kiem"): Hinh([(_so(0, 100), False)]),
    ("nc", "bot"): Hinh([(_so(1, 10), False)]),
    ("nc", "tu-lai"): Hinh([(_MA.match, True), (_khung, False)], {"--khong-niem-phong": None}),
    ("nc", "tho"): Hinh(co={"--vong": _so(1, 200), "--cong-cu": _so(1, 200)}),
    ("nc", "cc"): Hinh([(_cong_cu, True), (_json_obj, False)]),
    ("nc", "hoi"): Hinh([(_van_ban(10, 800), True), (_thuc01, False)]),     # cau hoi cua CHU DU AN vao so tay (nguon 'nguoi')
    ("hepha", "do"): Hinh(),
    ("hepha", "duc"): Hinh([(_so(1, 5000), False)]),
    ("hepha", "nap"): Hinh([(_so(1, 5000), False)], {"--that": None}),
    ("hepha", "qt"): Hinh([(_so(1, 5000), False)], {"--ma": _MA.match, "--khung": _khung, "--ghep": None}),
    ("cau", "tu-kiem"): Hinh(),
    ("test",): Hinh(),
    ("vao",): Hinh(),
    ("ban-do",): Hinh(),
    ("kien-truc",): Hinh(),
    ("khoi-phuc",): Hinh(co={"--json": None}),
    # nhan/may_nha.py: quet + do + ket luan may nha. CHI DOC, tru `do` (file tam xoa ngay). Khong co `ap-dung`:
    # moi de xuat (pagefile, ke hoach dien) chi IN RA, chu du an tu lam.
    ("may", "quet"): Hinh(),
    ("may", "mau"): Hinh(co={"--nang": None}),
    ("may", "bao-cao"): Hinh(),
    ("may", "do"): Hinh(co={"--nhanh": None, "--ep": None, "--toi-da": _so(1, 64)}),
    ("may", "giam-sat"): Hinh([(_so(1, 180), False), (_so(5, 300), False)]),
    # link chu du an (03/10/2026): chi cac lenh KHONG dung khoa / dang nhap cua chu du an. Khong co `them` / `nap-van-ban`
    # (ghi vao link_rieng.txt rieng), `tai-khoan-xem` (mat khau investor), `--cdp` (Chrome da dang nhap), `telegram-*` (phien Telegram)
    ("link", "ke-hoach"): Hinh(),
    ("link", "chay"): Hinh(co={"--toi-da": _so(1, 40), "--theo-nen": _so(1, 10), "--lai": None}),
    ("link", "tham-do"): Hinh([(_url_cho_tham_do, True)]),
    ("link", "thu-muc"): Hinh(co={"--toi-thieu": _so(1, 100_000)}),
    ("link", "bao-cao"): Hinh(),
    ("link", "chia-se"): Hinh([(_ma_hex10, True)]),
    ("link", "ho-so-symbol"): Hinh(co={"--song": _so(30, 100_000), "--toi-da": _so(1, 60)}),
}
#: `-m <module> ...`
MODULE_M: dict[str, Hinh] = {
    "tru.banker": Hinh(co={"--nhin-truoc": None, "--ep": None}),
}
#: `<script>.py ...` o goc lab
SCRIPT: dict[str, Hinh] = {
    "do_spread_hai_ban.py": Hinh([(_MA.match, True)]),
    "noi_sinh_chay_that.py": Hinh([(_MA.match, True), (_khung, True)]),
}


def _pytest(con: list[str]) -> str | None:
    i = 0
    while i < len(con):
        a = con[i]
        if a in ("-q", "-x", "-rf"):
            pass
        elif a.startswith("--tb="):
            if a[5:] not in _TB:
                return "--tb khong hop le"
        elif a == "-p":
            i += 1
            if i >= len(con) or con[i] != "no:cacheprovider":
                return "chi cho `-p no:cacheprovider`"
        elif a in ("-k", "-m"):
            i += 1
            if i >= len(con) or not _BIEU_THUC.match(con[i]):
                return "bieu thuc %s khong hop le" % a
        elif _FILE_TEST.match(a):
            pass
        else:
            return "doi so pytest khong duoc phep: %r" % a[:60]
        i += 1
    return None


def kiem_lenh(lenh) -> str | None:
    """None = qua danh sach trang · chuoi = ly do tu choi."""
    if not isinstance(lenh, list) or not lenh or not all(isinstance(x, str) for x in lenh):
        return "lenh phai la danh sach chuoi khong rong"
    if sum(len(x) for x in lenh) > 30_000:
        return "lenh qua dai"
    if lenh[0] != "{py}":
        return "lenh phai bat dau bang {py} (khong chay file thuc thi tuy y): %r" % lenh[0][:60]
    con = lenh[1:]
    if con == PING:
        return None
    if not con:
        return "thieu lenh sau {py}"
    if con[0] == "-m":
        if len(con) < 2:
            return "thieu ten module sau -m"
        if con[1] == "pytest":
            return _pytest(con[2:])
        if con[1] in MODULE_M:
            return MODULE_M[con[1]].kiem(con[2:])
        return "module khong co trong danh sach trang: %r" % con[1][:60]
    if con[0] in SCRIPT:
        return SCRIPT[con[0]].kiem(con[1:])
    if con[0] == "b.py":
        b = con[1:]
        khoa = next((k for k in sorted(LENH_B, key=len, reverse=True) if tuple(b[:len(k)]) == k), None)
        if khoa is None:
            return "lenh b khong co trong danh sach trang: %s" % " ".join(b[:3])
        return LENH_B[khoa].kiem(b[len(khoa):])
    return "khong co trong danh sach trang: %s" % " ".join(con[:3])[:80]


# ------------------------------------------------------------------ DUYET TAY (tren may)
def van_tay(lenh) -> str:
    return hashlib.sha256(json.dumps(list(lenh), ensure_ascii=False).encode("utf-8")).hexdigest()[:20]


def _doc_duyet(duong: Path) -> dict:
    try:
        d = json.loads(duong.read_text(encoding="utf-8-sig"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def da_duyet(lenh, duong: Path | None = None) -> bool:
    """Chu du an da duyet DUNG lenh nay (van tay khop) tren may nay chua."""
    return isinstance(lenh, list) and van_tay(lenh) in _doc_duyet(duong or DUYET)


def duyet(lenh, ma: str, duong: Path | None = None) -> str:
    """Ghi ban duyet cho dung lenh nay. Tra van tay."""
    p = duong or DUYET
    d = _doc_duyet(p)
    vt = van_tay(lenh)
    d[vt] = {"ma": ma, "luc": time.strftime("%Y-%m-%d %H:%M:%S"), "lenh": list(lenh)}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return vt


def cho_phep(lenh, duong: Path | None = None) -> tuple[bool, str]:
    """(duoc chay?, ly do). Qua danh sach trang HOAC da duoc chu du an duyet dung lenh."""
    loi = kiem_lenh(lenh)
    if loi is None:
        return True, ""
    if da_duyet(lenh, duong):
        return True, "da duoc chu du an duyet tren may (van tay %s)" % van_tay(lenh)
    return False, loi
