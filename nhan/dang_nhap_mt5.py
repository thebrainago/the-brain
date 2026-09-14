# -*- coding: utf-8 -*-
"""dang_nhap_mt5.py - TU DANG NHAP MT5, de tester chay duoc khi khong co nguoi.

Chu du an 13/09/2026: *"Luu luon vao, sau nay toi khong o day cau tu dang nhap
duoc."*

## VI SAO CAN

Ngay 13/09 toi xoa nham thu muc du lieu cua XM MT5 khi don dia. MT5 dung lai
duoc thu muc do nhung **`accounts.dat` di theo** - va tu do moi viec tester bi
chan cho toi khi co NGUOI ngoi vao bam File -> Login. Mot he duoc thiet ke de
chay hang thang tren VPS ma phai cho mot cu bam chuot thi no khong chay hang
thang duoc.

## KHOA CAT O DAU

`config/tai_khoan.json` - da nam trong `.gitignore` tu truoc (`**/tai_khoan.json`,
dong 23) va **chua tung vao lich su git** (da kiem: 0 commit cham vao no). Do
la cho lab danh san cho khoa; dung tu mo cho moi.

KHONG in mat khau ra log, khong ghi no vao `reports/`, khong dua vao thong bao
loi. Ham nay chi bao DA DANG NHAP DUOC hay KHONG va vi sao.

## VI SAO THU NHIEU SERVER

Ten server cua XM doi theo thoi gian (`XMGlobal-MT5 3/5/10/17`...). Tai lieu cu
cua lab ghi hai ten, va ca hai co the da cu. Nen thu lan luot roi GHI LAI cai
nao chay duoc - lan sau khong phai mo lai.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(GOC))

KHO = GOC / "config" / "tai_khoan.json"

#: Duong dan terminal cua tung san. Trung voi `nhan/chi_phi.py`.
EXE = {
    "XM": r"C:\Program Files\XM MT5\terminal64.exe",
    "Exness": r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
    "FXCE": r"C:\Program Files\FXCE MT5 Terminal\terminal64.exe",
    "Ultima": r"C:\Program Files\Ultima Markets MT5 Terminal\terminal64.exe",
}


def _doc() -> dict:
    try:
        return json.loads(KHO.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _ghi(d: dict) -> None:
    KHO.parent.mkdir(parents=True, exist_ok=True)
    KHO.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def luu(san: str, login: int, mat_khau: str, servers: list[str]) -> None:
    """Cat khoa cua mot san. `servers` xep theo thu tu se thu."""
    d = _doc()
    d.setdefault("mt5", {})[san] = {
        "login": int(login), "mat_khau": mat_khau,
        "servers": list(servers), "server_chay_duoc": None,
    }
    _ghi(d)


def khoa(san: str = "XM") -> dict:
    return (_doc().get("mt5") or {}).get(san) or {}


def dang_nhap(san: str = "XM", cho_giay: int = 25, in_ra=print) -> dict:
    """Dang nhap MT5 cua `san`. Tra {dat, server, login, ly_do}.

    Thu `server_chay_duoc` TRUOC (neu da biet), roi den danh sach. Thanh cong
    thi GHI LAI server do - lan sau chi mot lan thu.
    """
    k = khoa(san)
    if not k.get("login") or not k.get("mat_khau"):
        return {"dat": False, "ly_do": "chua co khoa cho san %s trong "
                                       "config/tai_khoan.json" % san}
    exe = EXE.get(san)
    if not exe or not Path(exe).exists():
        return {"dat": False, "ly_do": "khong thay terminal64 cua %s" % san}
    try:
        import MetaTrader5 as mt5
    except ImportError:
        return {"dat": False, "ly_do": "thieu goi MetaTrader5"}

    ds = [k.get("server_chay_duoc")] + list(k.get("servers") or [])
    da_thu = []
    for sv in [x for x in ds if x]:
        if sv in da_thu:
            continue
        da_thu.append(sv)
        ok = mt5.initialize(path=exe, login=int(k["login"]),
                            password=k["mat_khau"], server=sv,
                            timeout=cho_giay * 1000)
        if ok:
            a = mt5.account_info()
            mt5.shutdown()
            d = _doc()
            d["mt5"][san]["server_chay_duoc"] = sv
            _ghi(d)
            if in_ra:
                in_ra("dang nhap %s duoc: %s @ %s" % (san, k["login"], sv))
            return {"dat": True, "server": sv, "login": k["login"],
                    "cong_ty": getattr(a, "company", ""),
                    "so_du": getattr(a, "balance", None)}
        loi = mt5.last_error()
        mt5.shutdown()
        if in_ra:
            in_ra("  %s -> %s" % (sv, loi))
        # HAI LOI NAY DOI HAI HANH DONG NGUOC NHAU - dung gop.
        #
        #   -6  Authorization failed : server CO THAT, ket noi toi duoc, va
        #       may chu TU CHOI cap tai khoan/mat khau. Thu them server khac
        #       la vo ich, va con lam hong trang thai terminal (do 13/09: sau
        #       lan -6 dau tien, 7 lan thu tiep deu ra IPC timeout). Phai
        #       DUNG va bao NGUOI.
        #   -10005 IPC timeout : terminal khong tra loi - van de ky thuat,
        #       thu server khac hoac chay lai thi duoc.
        if loi and loi[0] == -6:
            return {"dat": False, "server": sv, "ma_loi": -6,
                    "can_nguoi": True,
                    "ly_do": "server `%s` DUNG va ket noi duoc, nhung XM tu "
                             "choi tai khoan %s - sai mat khau, hoac tai "
                             "khoan demo da het han (XM xoa demo sau ~90 ngay "
                             "khong dung). Thu server khac khong giai quyet "
                             "duoc gi." % (sv, k["login"])}
    return {"dat": False, "da_thu": da_thu,
            "ly_do": "khong server nao dang nhap duoc - toan IPC timeout, tuc "
                     "terminal khong tra loi. Dong het terminal64.exe roi thu "
                     "lai; neu van vay thi ten server co the da doi."}


def san_sang(san: str = "XM", in_ra=print) -> bool:
    """MT5 da dang nhap chua; chua thi TU dang nhap. Dung truoc moi luot tester."""
    try:
        import MetaTrader5 as mt5
    except ImportError:
        return False
    if mt5.initialize(timeout=15000):
        a = mt5.account_info()
        mt5.shutdown()
        if a and getattr(a, "login", 0):
            return True
    return bool(dang_nhap(san, in_ra=in_ra).get("dat"))


if __name__ == "__main__":
    san = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") \
        else "XM"
    print(json.dumps({k: v for k, v in dang_nhap(san).items()
                      if k != "mat_khau"}, ensure_ascii=False, indent=1))


# ==================================================== MO DUNG SAN, KHONG DOAN
#
#: Dau hieu nhan ra tung san tu `account_info().company`.
DAU_HIEU_SAN = {
    "XM": ("trading point", "xm "),
    "Exness": ("exness",),
    "FXCE": ("fxce",),
    "Ultima": ("ultima",),
}


class SaiSan(RuntimeError):
    """Da noi duoc voi MT5 nhung KHONG phai san minh hoi."""


def _dung_san(san: str, cong_ty: str, server: str) -> bool:
    t = ((cong_ty or "") + " " + (server or "")).lower()
    return any(d in t for d in DAU_HIEU_SAN.get(san, (san.lower(),)))


import contextlib as _ctx


@_ctx.contextmanager
def mo(san: str = "XM", cho_giay: int = 60, dong_cai_khac: bool = True,
       in_ra=print):
    """Mo MT5 CUA DUNG SAN `san`, dam bao khong noi nham terminal khac.

    ## CAI BAY DO DUOC 13/09/2026

    `mt5.initialize(path=X)` **khong bao dam** ban dang noi voi ban cai X.
    `path` chi dung de KHOI DONG mot terminal khi chua co cai nao chay; neu
    da co mot terminal dang chay thi API gan vao CAI DO, bat ke duong dan.

    Do that: truyen `path` cua XM Global MT5, va API tra ve

        tai khoan: 263579653 | Exness-MT5Real37 | Exness Technologies Ltd
        TONG SO MA SAN CUNG CAP: 43   (nhom `Cent`, hau to `c`)

    tuc toan bo so lieu la cua Exness cent. Khong mot thong bao nao canh bao.
    Moi phep do chi phi / danh sach ma / lich su cua lab deu co the lang le
    lay tu SAI SAN theo duong nay - va ket qua van "hop ly" nen khong ai nghi.

    Nen ham nay: dong terminal khac -> mo dung ban cai -> **KIEM LAI
    `account_info()` co dung san khong**, sai thi nem `SaiSan`.
    """
    import subprocess
    import time as _t
    import MetaTrader5 as mt5

    exe = EXE.get(san)
    if not exe or not Path(exe).exists():
        raise SaiSan("khong thay terminal64 cua %s" % san)

    if dong_cai_khac:
        try:
            import psutil
            for p in psutil.process_iter(["name", "exe"]):
                if (p.info.get("name") or "").lower() != "terminal64.exe":
                    continue
                if (p.info.get("exe") or "").lower() != str(exe).lower():
                    p.kill()
        except Exception:
            # KHONG duoc goi lenh giet tien trinh cua Windows thang o day
            # (bo quet cua `test_khoa_tester` bat dung chuoi do, co chu y).
            # `khoa_tester.dong_terminal` la CUA DUY NHAT de giet terminal: no
            # nem `TesterDangBan` neu mot tien trinh KHAC dang chay tester.
            # Giet thang thi luot tester cua ho doc file ket qua CU hoac RONG
            # **va khong ai bao loi** - TESTER = 1 la rang buoc VAT LI.
            from nhan import khoa_tester as _KT
            _KT.dong_terminal(f"dang_nhap_mt5.mo({san})")
        _t.sleep(3)

    k = khoa(san)
    tham = {"path": str(exe), "timeout": cho_giay * 1000}
    if k.get("login") and k.get("mat_khau"):
        sv = k.get("server_chay_duoc") or (k.get("servers") or [""])[0]
        tham.update(login=int(k["login"]), password=k["mat_khau"], server=sv)
    if not mt5.initialize(**tham):
        raise SaiSan("khong mo duoc MT5 cua %s: %s" % (san, mt5.last_error()))

    a = mt5.account_info()
    cong_ty = getattr(a, "company", "") if a else ""
    server = getattr(a, "server", "") if a else ""
    if not _dung_san(san, cong_ty, server):
        mt5.shutdown()
        raise SaiSan("hoi %s nhung dang noi voi `%s` / `%s` - API gan vao mot "
                     "terminal khac dang chay" % (san, cong_ty, server))
    if in_ra:
        in_ra("MT5 %s: %s @ %s" % (san, getattr(a, "login", "?"), server))
    try:
        yield mt5
    finally:
        mt5.shutdown()


def ma_cua_san(san: str = "XM", in_ra=print) -> dict:
    """Danh sach ma THAT cua mot san, kem nhom va so ma dang chon."""
    import collections
    with mo(san, in_ra=in_ra) as mt5:
        s = mt5.symbols_get() or []
        nhom = collections.Counter(
            (x.path.split(chr(92))[0] if x.path else "?") for x in s)
        return {"san": san, "so_ma": len(s),
                "dang_chon": sum(1 for x in s if x.visible),
                "nhom": dict(nhom.most_common(15)),
                "ten": sorted(x.name for x in s)}
