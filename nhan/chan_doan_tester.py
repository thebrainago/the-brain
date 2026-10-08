# -*- coding: utf-8 -*-
"""chan_doan_tester.py - VI SAO tester "khong ra bao cao": gom bang chung cua DUNG lan chay do (08/10/2026).

## Vi sao co file nay

Do 08/10/2026: 20 don `hieu_chuan_luoi` / `ea_tho` chet voi cung MOT cau "tester khong ra bao cao" - cai thi sau 92-95 giay
(terminal tu thoat), cai thi sau 1.000-4.000 giay - va khong ai biet vi sao. `ea_tho._chay_voi_slot` co doc log agent nhung
(1) lay file log MOI NHAT cua CA MAY (4 slot chay cung luc -> thuong la log cua slot khac) va (2) `chay()` / `nua_tester()`
BO log do khi hong. Nguoi phai doan: terminal mat dang nhap? thieu lich su M1 cua ma (EURCAD thi co, AUDCAD / NZDCAD thi
khong)? thieu `Include`? het bo nho? Moi lan doan sai la mot luot cho gio TESTER - thu khan hiem nhat cua he (ngan sach
`TESTER = 1` la rang buoc vat ly).

## File nay chi DOC (khong sua gi trong terminal) va tra ve

- `kiem_slot`  : kiem re (ms) cua MOT thu muc du lieu terminal: `MQL5\\Include\\Trade\\Trade.mqh`, tep lich su M1
                 `bases\\<may chu>\\history\\<MA>\\<nam>.hcc` cho tung nam cua cua so, dong dang nhap cuoi trong nhat ky terminal.
- `thu_thap`   : SAU khi hong - duoi cac log MOI HON luc bat dau chay (nhat ky terminal, tester chinh, tung agent, nhat ky EA)
                 cua DUNG slot nay + tien do mo phong (ngay mo phong cuoi trong log agent / ca cua so).
- `tom_tat`    : mot dong ngan (<= 700 ky tu) cho `ly_do`, nhan dau vet o DAU dong (dau ra `cau_loi.dau_vet` chi cat 240 ky tu).

## Gioi han (noi that)

Ten tep / thu muc cua MT5 o day lay tu hieu biet ve cau truc thu muc, CHUA doi chieu voi log that cua may nha (cloud khong
co MT5). Vi vay: KHONG CHAN gi dua tren ket qua nay (chi in ra), moi cau chu trong log duoc giu NGUYEN VAN (da bo cot ma),
va nhan dau vet chi la goi y (dung bieu thuc rong). Nhan sai thi dong log goc van nam ngay canh de nguoi doc tu phan.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

SO_DONG_MOI_LOG = 6                                 # moi file log lay chung nay dong CUOI
TOI_DA_KY_TU_DONG = 170
TOI_DA_KY_TU_TOM_TAT = 700
DOC_TOI_DA_BYTE = 96 * 1024                         # chi doc DUOI file (log agent co the vai chuc MB)
DUNG_SAI_GIAY = 5.0                                 # file log duoc coi la "cua lan chay nay" neu mtime >= bat_dau - ngay nay

#: (nhan, bieu thuc) - THU TU = muc nghiem trong: khop dau tien thang. Chi la GOI Y, dong log goc luon di kem.
NHAN_LOG = (
    ("chua_dang_nhap", r"authoriz\w* .*(?:fail|invalid|denied|reject)|invalid account|account .*(?:disabled|expired)|"
                       r"wrong (?:password|login)|not authorized"),
    ("mat_ket_noi", r"no connection|connection (?:lost|closed|refused|failed|timed out)|disconnected|"
                    r"not synchroni[sz]ed|synchroni[sz]ation .*fail"),
    ("thieu_lich_su", r"no history|cannot generate history|0 ticks, 0 bars|history .*(?:not found|unavailable|not available)|"
                      r"not enough history|history is not (?:synchroni[sz]ed|loaded)"),
    ("khong_nap_ea", r"cannot load|failed to load|(?:expert|file) .*not found|cannot open|can't open"),
    ("ea_tu_choi", r"oninit .*(?:non-zero|fail)|initialization failed|init_failed|critical error|stopped because"),
    ("het_bo_nho", r"out of memory|not enough memory|memory allocation"),
    ("agent_chet", r"agent .*(?:stopped|terminated|crashed|lost|unavailable)|local agent .*(?:fail|error)"),
)
_RX_NHAN = [(n, re.compile(rx, re.I)) for n, rx in NHAN_LOG]
_RX_MOC = re.compile(r"^(\d{4})\.(\d{2})\.(\d{2})[ T](\d{2}):(\d{2}):(\d{2})")
_RX_DANG_NHAP = re.compile(r"authori[sz]|connect|synchroni[sz]|login|disconnect", re.I)
#: Repo la PUBLIC: so tai khoan trong nhat ky terminal (`'12345678': authorization ... failed`) va dia chi IP may chu KHONG ra ngoai.
_RX_SO_TK = re.compile(r"'\d{5,}'|\blogin\W{0,3}\d{5,}", re.I)
_RX_IP = re.compile(r"\b(?!127\.0\.0\.1\b)\d{1,3}(?:\.\d{1,3}){3}\b")


# ============================================================ 1. DOC LOG (chi doc DUOI)
def _giai_ma(b: bytes, dau: bytes) -> str:
    if dau == b"\xff\xfe":
        return b.decode("utf-16-le", errors="ignore")
    if dau == b"\xfe\xff":
        return b.decode("utf-16-be", errors="ignore")
    if b[:400].count(b"\x00") > len(b[:400]) // 4:        # UTF-16 khong BOM
        return b.decode("utf-16-le", errors="ignore")
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("cp1252", errors="ignore")


def _chuan_hoa(dong: str) -> str:
    """Dong log MT5 `MA\\t0\\t12:01:02.123\\tCore 1\\tnoi dung` -> `12:01:02 Core 1 noi dung` (bo hai cot ma)."""
    d = dong.replace("\r", "").rstrip("\n")
    p = d.split("\t")
    if len(p) >= 4 and p[1].strip().isdigit():
        d = "%s %s %s" % (p[2][:8], p[3].strip(), " ".join(x.strip() for x in p[4:]))
    else:
        d = " ".join(x.strip() for x in p)
    d = re.sub(r"\s+", " ", d).strip()
    d = _RX_IP.sub("<ip>", _RX_SO_TK.sub("<tk>", d))
    return d[:TOI_DA_KY_TU_DONG]


def doc_text(p, toi_da_byte: int = DOC_TOI_DA_BYTE) -> str:
    """Van ban cua file log, CHI `toi_da_byte` byte CUOI (UTF-16 / UTF-8). Dong dau co the bi cat giua. Loi doc -> '' (khong nem)."""
    try:
        with open(p, "rb") as f:
            dau = f.read(2)
            f.seek(0, 2)
            n = f.tell()
            u16 = dau in (b"\xff\xfe", b"\xfe\xff")
            dau_van = 2 if u16 else 0
            bat = max(dau_van, n - toi_da_byte)
            if u16 and bat % 2:
                bat += 1                                   # giu can le chan: UTF-16 la cap byte
            f.seek(bat)
            b = f.read()
    except OSError:
        return ""
    van = _giai_ma(b, dau)
    return van.split("\n", 1)[-1] if bat > dau_van else van


def doc_duoi(p, so_dong: int = SO_DONG_MOI_LOG, toi_da_byte: int = DOC_TOI_DA_BYTE) -> list[str]:
    """`so_dong` dong CUOI cua file log, da chuan hoa. Khong doc ca file. Loi doc -> [] (khong nem)."""
    ra = [_chuan_hoa(x) for x in doc_text(p, toi_da_byte).split("\n") if x.strip()]
    return [x for x in ra if x][-so_dong:]


# ============================================================ 2. TIM LOG CUA DUNG SLOT
def thu_muc_log(du_lieu, home=None) -> list[tuple[str, Path]]:
    """[(loai, thu_muc_logs)] cua slot co thu muc du lieu `du_lieu`. Hai kieu bo cuc cua MT5:
    - THUONG: tester o `%APPDATA%\\MetaQuotes\\Tester\\<ten thu muc du lieu>\\` (cung ma bam voi thu muc du lieu terminal)
    - PORTABLE (`/portable`): tester nam NGAY TRONG thu muc terminal, `<du_lieu>\\Tester\\`
    Chi liet ke thu muc CO THAT."""
    du_lieu = Path(du_lieu)
    home = Path(home) if home else Path.home()
    ra: list[tuple[str, Path]] = [("terminal", du_lieu / "logs"), ("ea", du_lieu / "MQL5" / "Logs")]
    for g in (du_lieu / "Tester", home / "AppData" / "Roaming" / "MetaQuotes" / "Tester" / du_lieu.name):
        ra.append(("tester", g / "logs"))
        try:
            ags = sorted(g.glob("Agent-*"))
        except OSError:
            ags = []
        for ag in ags:
            ra.append(("agent:" + ag.name.replace("Agent-127.0.0.1-", "a").replace("Agent-", ""), ag / "logs"))
    return [(k, d) for k, d in ra if d.is_dir()]


def _log_moi_nhat(thu: Path) -> Path | None:
    try:
        fs = [f for f in thu.glob("*.log") if f.is_file()]
        return max(fs, key=lambda f: f.stat().st_mtime) if fs else None
    except OSError:
        return None


# ============================================================ 3. KIEM SLOT (re, truoc / sau khi chay)
def _mb(p: Path) -> float | None:
    try:
        return round(p.stat().st_size / 1024 ** 2, 1)
    except OSError:
        return None


def _nam_cua_so(tu: str | None, den: str | None) -> list[int]:
    def _nam(s):
        m = re.match(r"\s*(\d{4})", str(s or ""))
        return int(m.group(1)) if m else None
    a, b = _nam(tu), _nam(den)
    if a is None or b is None or b < a or b - a > 40:
        return []
    return list(range(a, b + 1))


def kiem_slot(du_lieu, ma: str | None = None, tu: str | None = None, den: str | None = None) -> dict:
    """Kiem RE mot thu muc du lieu terminal. Khong nem. {"include_trade": bool, "lich_su_m1": {...}|None, "dang_nhap": str|None}"""
    du_lieu = Path(du_lieu)
    ra: dict = {"include_trade": (du_lieu / "MQL5" / "Include" / "Trade" / "Trade.mqh").is_file(),
                "lich_su_m1": None, "dang_nhap": None}
    try:
        if ma and not re.search(r"[*?\[\]/\\]", ma):
            nam = _nam_cua_so(tu, den)
            thu_ma = [d for d in du_lieu.glob("bases/*/history/%s" % ma) if d.is_dir()]
            kq: dict = {"co_thu_muc": bool(thu_ma), "nam": {}, "tep_mau": []}
            for y in nam:
                mb = [_mb(d / ("%d.hcc" % y)) for d in thu_ma]
                mb = [x for x in mb if x is not None]
                kq["nam"][str(y)] = max(mb) if mb else None
            if thu_ma:
                kq["tep_mau"] = sorted(x.name for x in thu_ma[0].iterdir())[:6]
            ra["lich_su_m1"] = kq
        nk = _log_moi_nhat(du_lieu / "logs")
        if nk:
            dong = [x for x in doc_duoi(nk, so_dong=60) if _RX_DANG_NHAP.search(x)]
            ra["dang_nhap"] = dong[-1] if dong else None
    except OSError:
        pass
    return ra


# ============================================================ 4. NHAN DAU VET + TIEN DO
def nhan_dau_vet(dong: list[str]) -> tuple[str, str] | None:
    """(nhan, dong_goc) cua dau vet NGHIEM TRONG NHAT (theo thu tu `NHAN_LOG`); trong cung nhan lay dong CUOI cung. None neu khong thay."""
    dong = list(dong or [])
    for nhan, rx in _RX_NHAN:
        khop = [d for d in dong if rx.search(d)]
        if khop:
            return nhan, khop[-1]
    return None


def _moc(dong: str):
    """Thoi diem MO PHONG o dau noi dung dong log agent (`... Core 1 2019.03.04 10:15:00 noi dung`) -> (y, m, d) hoac None."""
    m = re.search(r"Core \d+ (\d{4})\.(\d{2})\.(\d{2}) \d{2}:\d{2}:\d{2}", dong)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def tien_do(dong: list[str], tu: str | None, den: str | None) -> dict | None:
    """Ngay mo phong cuoi trong cac dong log agent va % cua cua so [tu, den]. None neu khong thay moc nao."""
    import datetime as dt

    def _ngay(s):
        m = re.match(r"\s*(\d{4})\D(\d{2})\D(\d{2})", str(s or ""))
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None
    try:
        a, b = _ngay(tu), _ngay(den)
    except ValueError:
        return None
    mocs = [x for x in (_moc(d) for d in dong) if x]
    if not mocs:
        return None
    try:
        cuoi = max(dt.date(*x) for x in mocs)
    except ValueError:
        return None
    ra = {"ngay_mo_phong_cuoi": cuoi.strftime("%Y.%m.%d")}
    if a and b and b > a:
        ra["phan_tram"] = int(max(0.0, min(1.0, (cuoi - a).days / (b - a).days)) * 100)
    return ra


def log_agent_slot(du_lieu, bat_dau: float, home=None, toi_da_byte: int = 512 * 1024) -> str:
    """Van ban log agent MOI NHAT (moi hon luc `bat_dau`) cua DUNG slot nay - '' neu khong co. Thay cho 'log agent moi nhat cua CA MAY'
    (4 slot chay cung luc thi hay la log cua slot khac -> `dau_hieu_hong` doc nham)."""
    moi: list[tuple[float, Path]] = []
    for loai, thu in thu_muc_log(du_lieu, home):
        if not loai.startswith("agent"):
            continue
        f = _log_moi_nhat(thu)
        try:
            if f is not None and f.stat().st_mtime >= bat_dau - DUNG_SAI_GIAY:
                moi.append((f.stat().st_mtime, f))
        except OSError:
            continue
    return doc_text(max(moi)[1], toi_da_byte) if moi else ""


def ghi_chi_tiet(cd: dict, thu_muc, ten_slot: str = "") -> str | None:
    """Ghi bang chung DAY DU ra `<thu_muc>/<gio>_<slot>.json` (de nguoi o may nha mo ra xem). Tra ten file, hoac None neu khong ghi duoc."""
    import json
    try:
        thu_muc = Path(thu_muc)
        thu_muc.mkdir(parents=True, exist_ok=True)
        ten = "%s_%s.json" % (time.strftime("%Y%m%d-%H%M%S"), re.sub(r"[^A-Za-z0-9_.-]", "_", ten_slot or "slot")[:20])
        (thu_muc / ten).write_text(json.dumps(cd, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        return ten
    except (OSError, TypeError, ValueError):
        return None


# ============================================================ 5. THU THAP + TOM TAT
def thu_thap(du_lieu, bat_dau: float, *, ma: str | None = None, tu: str | None = None, den: str | None = None,
             khung: str | None = None, home=None, giay: float | None = None) -> dict:
    """Bang chung SAU KHI tester khong ra bao cao. KHONG BAO GIO nem (chan doan khong duoc lam hong them viec da hong).
    -> {"nhan","dong_chinh","log":[{"loai","tep","dong":[...]}],"cu":[loai...],"slot":kiem_slot,"tien_do":..,"giay":..}"""
    ra: dict = {"nhan": None, "dong_chinh": None, "log": [], "cu": [], "slot": None, "tien_do": None, "giay": giay,
                "ma": ma, "khung": khung}
    try:
        ra["slot"] = kiem_slot(du_lieu, ma, tu, den)
        dong_agent: list[str] = []
        tat_ca: list[str] = []
        for loai, thu in thu_muc_log(du_lieu, home):
            f = _log_moi_nhat(thu)
            if f is None:
                continue
            try:
                moi = f.stat().st_mtime >= bat_dau - DUNG_SAI_GIAY
            except OSError:
                continue
            if not moi:
                ra["cu"].append(loai)
                continue
            dong = doc_duoi(f, so_dong=SO_DONG_MOI_LOG if not loai.startswith("agent") else 40)
            if loai.startswith("agent"):
                dong_agent += dong
                dong = dong[-SO_DONG_MOI_LOG:]
            tat_ca += dong
            ra["log"].append({"loai": loai, "tep": f.name, "dong": dong})
        nv = nhan_dau_vet(tat_ca)
        if nv:
            ra["nhan"], ra["dong_chinh"] = nv
        ra["tien_do"] = tien_do(dong_agent, tu, den)
    except Exception as e:                           # noqa: BLE001
        ra["loi_chan_doan"] = "%s: %s" % (type(e).__name__, str(e)[:120])
    return ra


def _co_gi(cd: dict) -> bool:
    """Chan doan co gi DANG KE de gan vao ket qua (khong lam day ket qua bang truong rong)."""
    return bool(cd and (cd.get("log") or cd.get("nhan") or cd.get("tien_do") or cd.get("slot") or cd.get("loi_chan_doan")))


def tom_tat(cd: dict, goc: str = "tester khong ra bao cao", ten_slot: str | None = None) -> str:
    """Mot dong cho `ly_do`. Nhan dau vet va dong log chinh o DAU (dau ra cua `cau_loi.dau_vet` bi cat 240 ky tu)."""
    if not cd:
        return goc
    kq = goc
    if cd.get("giay"):
        kq += " sau %ds" % int(cd["giay"])
    if cd.get("nhan"):
        kq += " [tester:%s]" % cd["nhan"]
        if cd.get("dong_chinh"):
            kq += " " + cd["dong_chinh"][:TOI_DA_KY_TU_DONG]
    ph: list[str] = []
    sl = cd.get("slot") or {}
    if sl:
        mot = ["Trade.mqh=%s" % ("co" if sl.get("include_trade") else "THIEU")]
        ls = sl.get("lich_su_m1")
        if ls is not None:
            if not ls.get("co_thu_muc"):
                mot.append("lich su %s: KHONG co thu muc" % (cd.get("ma") or "?"))
            else:
                mot.append("M1 %s: %s" % (cd.get("ma") or "?", " ".join(
                    "%s=%s" % (n, ("%sMB" % v) if v is not None else "THIEU") for n, v in sorted(ls.get("nam", {}).items()))
                    or "tep " + ",".join(ls.get("tep_mau") or ["?"])))
        ph.append("slot%s %s" % ((" " + ten_slot) if ten_slot else "", ", ".join(mot)))
        if sl.get("dang_nhap"):
            ph.append("nhat ky terminal: " + sl["dang_nhap"][:TOI_DA_KY_TU_DONG])
    td = cd.get("tien_do")
    if td:
        ph.append("mo phong toi %s%s" % (td["ngay_mo_phong_cuoi"],
                                           (" (%d%% cua so)" % td["phan_tram"]) if "phan_tram" in td else ""))
    elif cd.get("log"):
        ph.append("agent khong in moc mo phong nao")
    if cd.get("log"):
        ph.append("log moi: " + ", ".join("%s %dd" % (x["loai"], len(x["dong"])) for x in cd["log"]))
        cuoi = [x for x in cd["log"] if x["dong"]]
        if cuoi and not cd.get("nhan"):
            ph.append("dong cuoi %s: %s" % (cuoi[-1]["loai"], cuoi[-1]["dong"][-1]))
    elif cd.get("cu"):
        ph.append("khong co log nao moi hon luc chay (cu: %s)" % ",".join(cd["cu"]))
    else:
        ph.append("khong thay thu muc log nao cua slot")
    if cd.get("loi_chan_doan"):
        ph.append("chan doan loi: " + cd["loi_chan_doan"])
    ra = kq + (" | " + " | ".join(ph) if ph else "")
    return ra[:TOI_DA_KY_TU_TOM_TAT]


if __name__ == "__main__":                          # python -m nhan.chan_doan_tester <thu_muc_du_lieu> [MA] [tu] [den]
    import json
    import sys
    if len(sys.argv) < 2:
        raise SystemExit("dung: python -m nhan.chan_doan_tester <thu_muc_du_lieu_terminal> [MA] [tu YYYY.MM.DD] [den YYYY.MM.DD] [so_gio_gan_day]")
    gio = float(sys.argv[5]) if len(sys.argv) > 5 else 3.0
    cd = thu_thap(sys.argv[1], time.time() - gio * 3600, ma=sys.argv[2] if len(sys.argv) > 2 else None,
                  tu=sys.argv[3] if len(sys.argv) > 3 else None, den=sys.argv[4] if len(sys.argv) > 4 else None)
    print(tom_tat(cd))
    print(json.dumps(cd, ensure_ascii=False, indent=1))
