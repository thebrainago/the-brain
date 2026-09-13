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
