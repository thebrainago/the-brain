# -*- coding: utf-8 -*-
"""slot_tester.py - NHIEU LAN TESTER, moi lan mot terminal RIENG.

## Vi sao

`ngan_sach.py` ghi `TESTER = 1` va goi do la "rang buoc VAT LY". Do 16/09/2026
(`b ho-so` muc 11.7): may nay co **6 ban cai MT5** va **8 thu muc du lieu
terminal** rieng - tuc rang buoc nam o MA NGUON chu khong o may. Bon cho ghim
cung:

    1. `chay_tester_kho` ghi de cung mot `MQL5/Experts/<TEN_EA>.mq5`, cung
       mot `.ini`, cung mot `.xml`, trong MOT thu muc du lieu (`XM_DATA`).
    2. `duong_dan.mt5_exe` tra MOT duong dan, khong nhan tham so.
    3. `khoa_tester` la khoa toan cuc mot slot.
    4. `ngan_sach.TESTER = 1`.

File nay go (2) va (3): mot SLOT la bo `(exe, thu_muc_du_lieu, hau_to_ten)`,
moi slot mot khoa rieng, va khi cap slot thi dat `BRAIN_MT5` / `BRAIN_MT5_DATA`
de tien trinh con doc dung ban cua slot do.

## CHUA GO (1) - va do la ly do van de TESTER = 1

Chung nao `chay_tester_kho` chua nhan `slot` de doi ten file dau ra, hai slot
van ghi de len nhau NEU chung dung chung mot thu muc du lieu. File nay khong
tu y nang tran; xem `nen_nang_tran()`.

## KIEM CHUNG TRUOC KHI TIN

Hai slot chi duoc coi la dung khi:

    a. Cung mot cau hinh chay tren slot 1 va slot 2 -> ket qua Y HET.
    b. Hai cau hinh khac nhau chay CUNG LUC -> moi ket qua khop voi lan chay rieng.

Chua co (a) va (b) thi `TESTER` phai giu nguyen 1. `b slot kiem` lam viec do.

Chay:  python -m nhan.slot_tester        xem trang thai cac slot
       b slot                            (duong chay that)
"""
from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

from nhan import khoa_tester as KT                                # noqa: E402

TEP = LAB / "config" / "slot_tester.json"


class KhongConSlot(RuntimeError):
    """Het slot ranh. Khong phai loi cua phep thu - la 'cho luot'."""


class Slot:
    """Mot lan tester: mot exe, mot thu muc du lieu, mot hau to ten file."""

    def __init__(self, ten: str, exe: str, du_lieu: str, hau_to: str = "",
                 ghi_chu: str = ""):
        self.ten = ten
        self.exe = Path(exe)
        self.du_lieu = Path(du_lieu)
        self.hau_to = hau_to
        self.ghi_chu = ghi_chu

    # -- ten file dau ra, tach theo slot ---------------------------------
    def ten_ea(self, goc: str) -> str:
        return goc + self.hau_to

    def tep(self, ten: str, duoi: str) -> Path:
        return self.du_lieu / (ten + self.hau_to + duoi)

    def san_sang(self) -> tuple[bool, str]:
        if not self.exe.exists():
            return False, "khong thay exe: %s" % self.exe
        if not self.du_lieu.exists():
            return False, "khong thay thu muc du lieu: %s" % self.du_lieu
        n = len(list(self.du_lieu.glob("bases/*/history/*")))
        if not n:
            return False, "thu muc du lieu KHONG co lich su gia (chua dang nhap?)"
        return True, "%d ma co lich su" % n

    def to_dict(self) -> dict:
        ok, ly_do = self.san_sang()
        k = KT.dang_giu(self.ten if self.ten != "mac_dinh" else None)
        return {"ten": self.ten, "exe": str(self.exe), "du_lieu": str(self.du_lieu),
                "hau_to": self.hau_to, "san_sang": ok, "ly_do": ly_do,
                "dang_giu": k, "ghi_chu": self.ghi_chu}

    @property
    def _ten_khoa(self) -> str | None:
        """Slot dau tien giu TEN KHOA CU, de khong bo roi khoa dang giu."""
        return None if self.ten == "mac_dinh" else self.ten


def _mac_dinh() -> dict:
    """Cau hinh MOT slot, suy tu ban MT5 dang dung duoc nhat.

    Khong co file cau hinh thi he phai chay Y NHU TRUOC - mot slot, ten khoa
    cu. Mot module moi ma lam doi hanh vi ngay khi duoc them vao la mot cach
    chac chan de khong ai dam them gi nua.
    """
    try:
        from chay_tester_z5 import XM_EXE, XM_DATA
        exe, dl = str(XM_EXE), str(XM_DATA)
    except Exception:
        from nhan import duong_dan as DD
        exe = str(DD.mt5_exe() or "")
        dl = str(DD.mt5_du_lieu() or "")
    return {"_doc_truoc": [
        "Moi slot = mot terminal RIENG (exe + thu muc du lieu rieng).",
        "Hai slot dung CHUNG thu muc du lieu la SAI: chung ghi de .mq5/.ini/.xml",
        "cua nhau va KHONG AI BAO LOI.",
        "Them slot xong PHAI chay `b slot kiem` truoc khi nang TESTER."],
        "slots": [{"ten": "mac_dinh", "exe": exe, "du_lieu": dl, "hau_to": "",
                   "ghi_chu": "ban dang dung tu truoc 16/09"}]}


def doc() -> list[Slot]:
    if not TEP.exists():
        # Qua `ghi_an_toan`: hai phien cung khoi dong se cung thay file chua co
        # va cung sinh ban mac dinh. Ghi thang thi ban sau de len ban truoc -
        # vo hai o day (hai ban giong nhau) nhung se khong con vo hai khi ai do
        # them slot vao dung luc do.
        from nhan import ghi_an_toan as GAT
        GAT.sua_json(TEP, lambda cu: cu or _mac_dinh())
    d = json.loads(TEP.read_text(encoding="utf-8-sig"))
    return [Slot(**{k: v for k, v in s.items() if k in
                    ("ten", "exe", "du_lieu", "hau_to", "ghi_chu")})
            for s in d.get("slots", [])]


def trung_thu_muc(ds: list[Slot] | None = None) -> list[str]:
    """Slot nao dung chung thu muc du lieu -> ghi de nhau. Phai RONG."""
    ds = ds if ds is not None else doc()
    thay: dict[str, str] = {}
    xau = []
    for s in ds:
        k = str(s.du_lieu).lower() + "|" + s.hau_to
        if k in thay:
            xau.append("%s dung chung (thu_muc, hau_to) voi %s" % (s.ten, thay[k]))
        thay[k] = s.ten
    return xau


def nen_nang_tran() -> tuple[bool, str]:
    """Co duoc phep dat `ngan_sach.TESTER > 1` chua?

    Ba dieu kien, thieu mot la KHONG. Ham nay co chu dich la bi quan: ha tran
    xuong 1 khi chua chac con re hon nhieu so voi hai ket qua ghi de nhau ma
    khong ai bao loi.
    """
    ds = doc()
    ok = [s for s in ds if s.san_sang()[0]]
    if len(ok) < 2:
        return False, "chi co %d slot san sang" % len(ok)
    xau = trung_thu_muc(ds)
    if xau:
        return False, "slot dung chung thu muc: " + "; ".join(xau)
    bb = LAB / "reports" / "slot_kiem_chung.json"
    if not bb.exists():
        return False, "chua co bang chung kiem chung (chay `b slot kiem`)"
    try:
        d = json.loads(bb.read_text(encoding="utf-8"))
    except Exception:
        return False, "bang chung kiem chung doc khong duoc"
    if not (d.get("giong_nhau") and d.get("song_song_khop")):
        return False, "kiem chung CHUA DAT: %s" % d.get("ghi_chu", "")
    return True, "%d slot san sang va da kiem chung" % len(ok)


@contextmanager
def cap(viec: str, cho_giay: float = 0.0):
    """Cap mot slot RANH va giu khoa cua no trong khoi `with`.

    Dat `BRAIN_MT5` / `BRAIN_MT5_DATA` trong moi truong de tien trinh con
    (`duong_dan.mt5_exe`, `mt5_du_lieu`) doc dung ban cua slot.
    """
    ds = [s for s in doc() if s.san_sang()[0]]
    if not ds:
        raise KhongConSlot("khong slot nao san sang - xem `b slot`")
    cuoi = None
    for s in ds:
        r = KT.thu_lay(viec, s._ten_khoa)
        if not r["duoc"]:
            cuoi = r["ly_do"]
            continue
        cu_exe = os.environ.get("BRAIN_MT5")
        cu_dl = os.environ.get("BRAIN_MT5_DATA")
        os.environ["BRAIN_MT5"] = str(s.exe)
        os.environ["BRAIN_MT5_DATA"] = str(s.du_lieu)
        try:
            yield s
        finally:
            KT.tra(s._ten_khoa)
            for k, v in (("BRAIN_MT5", cu_exe), ("BRAIN_MT5_DATA", cu_dl)):
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        return
    raise KT.TesterDangBan(
        "het slot ranh (%d slot deu dang chay). %s" % (len(ds), cuoi or ""))


def bang(in_ra=print) -> dict:
    ds = doc()
    in_ra("=" * 78)
    in_ra("SLOT TESTER — %d slot khai bao" % len(ds))
    in_ra("=" * 78)
    for s in ds:
        d = s.to_dict()
        in_ra("%-10s %-7s %s" % (d["ten"], "SAN SANG" if d["san_sang"] else "HONG",
                                 d["ly_do"]))
        in_ra("           exe : %s" % d["exe"])
        in_ra("           data: %s" % d["du_lieu"])
        if d["dang_giu"]:
            in_ra("           DANG GIU: pid %s (%s)"
                  % (d["dang_giu"].get("pid"), d["dang_giu"].get("viec")))
    xau = trung_thu_muc(ds)
    if xau:
        in_ra("")
        in_ra("!! TRUNG THU MUC — hai slot nay se ghi de nhau:")
        for x in xau:
            in_ra("   - " + x)
    duoc, ly_do = nen_nang_tran()
    in_ra("")
    in_ra("Nang TESTER > 1: %s (%s)" % ("DUOC" if duoc else "CHUA", ly_do))
    if not duoc:
        in_ra("Huong dan them slot: xem `tai_lieu/SLOT_TESTER.md`")
    return {"so_slot": len(ds), "trung": xau, "nang_duoc": duoc, "ly_do": ly_do}


def kiem(in_ra=print) -> int:
    """Kiem dieu kien de nang tran, va noi RO con thieu gi.

    Lenh nay CO Y khong tu chay hai luot tester de so: khi viet no (16/09) may
    moi co MOT thu muc du lieu co lich su that (XM Global, 32 ma / 2,42 GB);
    nam thu muc con lai chi 4-14 ma, khong so duoc voi nhau. Viet mot bo so
    sanh chua bao gio chay duoc tren may nay thi dung la thu ma du an da cam:
    do phai do TREN DUONG CHAY THAT.

    Khi da co slot thu hai that, hai phep thu bat buoc la:
        a. cung mot cau hinh tren slot 1 va slot 2 -> ket qua Y HET
        b. hai cau hinh khac nhau chay CUNG LUC -> moi cai khop voi lan chay rieng
    Ghi ket qua vao `reports/slot_kiem_chung.json` dang
    {"giong_nhau": bool, "song_song_khop": bool, "ghi_chu": "..."} thi
    `nen_nang_tran()` moi mo.
    """
    ds = doc()
    ok = [s for s in ds if s.san_sang()[0]]
    in_ra("=" * 78)
    in_ra("KIEM DIEU KIEN NANG TRAN TESTER")
    in_ra("=" * 78)
    in_ra("1. So slot san sang            : %d %s"
          % (len(ok), "(can >= 2)" if len(ok) < 2 else "OK"))
    xau = trung_thu_muc(ds)
    in_ra("2. Khong trung thu muc du lieu : %s"
          % ("OK" if not xau else "HONG — " + "; ".join(xau)))
    bb = LAB / "reports" / "slot_kiem_chung.json"
    in_ra("3. Bang chung kiem chung       : %s"
          % ("co" if bb.exists() else "CHUA CO (%s)" % bb))
    duoc, ly_do = nen_nang_tran()
    in_ra("")
    in_ra("=> %s (%s)" % ("DUOC NANG" if duoc else "GIU TESTER = 1", ly_do))
    if len(ok) < 2:
        in_ra("")
        in_ra("Chi MOT thu muc du lieu co lich su that. Cac thu muc khac tren may:")
        goc = Path.home() / "AppData" / "Roaming" / "MetaQuotes" / "Terminal"
        for d in sorted(goc.glob("*")):
            if not d.is_dir() or len(d.name) != 32:
                continue
            n = len(list(d.glob("bases/*/history/*")))
            in_ra("   %s..  %3d ma co lich su" % (d.name[:10], n))
        in_ra("")
        in_ra("Cac buoc TAY de co slot 2: xem `tai_lieu/SLOT_TESTER.md`")
    return 0


def main(argv: list[str]) -> int:
    if argv and argv[0] in ("kiem", "k"):
        return kiem()
    bang()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
