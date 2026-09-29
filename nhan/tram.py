# -*- coding: utf-8 -*-
"""tram.py - TRAM MAY NHA: keo viec tu GitHub, chay lenh `b` trong DANH SACH TRANG, day ket qua ve.

Vi sao co (chu du an duyet 29/09/2026): phien Claude tren cloud chay trong container, KHONG voi toi
may nha. Nen may nha phai tu KEO viec ve; kenh chung la kho GitHub. Khong mo cong nao vao may nha,
khong chay lenh tuy y, khong dung tien that.

    cloud (Claude)  nghien cuu, viet ma, GIAO viec (`b tram giao`), doc ket qua, quyet xac nhan/niem phong
    tram (may nha)  du lieu that, MT5 tester, nao.db that - chay lenh TRANG, day ket qua (`b tram chay`)
    tho (model re)  kham pha tren doan kham_pha (`b nc tho`) - nhan/nc_tho.py

Hop thu = mot ban clone RIENG cua kho, chi de dong bo `tram/viec/<id>.json` (cloud ghi) va
`tram/ket_qua/<id>.json` (tram ghi). Lenh chay trong thu muc lab THAT (du lieu, config, MT5 o do).

    b tram cai URL NHANH   (may nha) tao hop thu + config/tram.json, in lenh Task Scheduler
    b tram chay            (may nha) MOT luot: keo -> chay viec moi -> day. Task Scheduler 5 phut/lan
    b tram giao LENH...    (cloud) tao file viec trong kho dang lam - roi commit + push nhu thuong
    b tram doc [ID]        (cloud) doc ket qua da keo ve
    b tram kiem LENH...    kiem mot lenh co qua danh sach trang khong (khong chay)

Dung khan: file `TRAM_DUNG` trong thu muc lab (tai may) hoac `tram/DUNG` tren nhanh hop thu (tu xa).
"""
from __future__ import annotations

import json
import os
import platform
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
CAU_HINH = LAB / "config" / "tram.json"
DUNG_TAI_MAY = LAB / "TRAM_DUNG"
HAN_MAC_DINH, HAN_TOI_DA = 7200, 43200          # giay
DUOI_LOG_DONG, TEP_TOI_DA, TONG_TEP_TOI_DA = 200, 40_000, 300_000
_ID = re.compile(r"^\d{8}-\d{6}-[0-9a-f]{4}$")
_MA = re.compile(r"^[A-Z0-9][A-Z0-9_.]{1,31}$")
_KHUNG = {"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"}


# ------------------------------------------------------------ DANH SACH TRANG
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


#: lenh -> danh sach O (ham kiem, bat_buoc). Chi nhung lenh nay chay duoc - them lenh = sua MA, co
#: review, khong phai sua mot file viec. Ky luat nghien cuu (niem phong mot lan, dem phep thu) nam
#: TRONG cong cu, nen `nc cc` mo toan bo 16 cong cu la an toan.
DANH_SACH_TRANG: dict[tuple, list] = {
    ("tram", "ping"): [],
    ("nc", "so-tay"): [],
    ("nc", "kiem"): [(_so(0, 100), False)],
    ("nc", "bot"): [(_so(1, 10), False)],
    ("nc", "tu-lai"): [(_MA.match, True), (lambda s: s in _KHUNG, False),
                       (lambda s: s == "--khong-niem-phong", False)],
    ("nc", "tho"): [(lambda s: s in ("--vong", "--cong-cu"), False), (_so(1, 200), False),
                    (lambda s: s in ("--vong", "--cong-cu"), False), (_so(1, 200), False)],
    ("nc", "cc"): [(_cong_cu, True), (_json_obj, False)],
    ("test",): [],
    ("vao",): [],
    ("ban-do",): [],
    ("kien-truc",): [],
}


def kiem_lenh(lenh) -> str | None:
    """None = qua danh sach trang; chuoi = ly do tu choi."""
    if not isinstance(lenh, list) or not lenh or not all(isinstance(x, str) for x in lenh):
        return "lenh phai la danh sach chuoi khong rong"
    if sum(len(x) for x in lenh) > 30_000:
        return "lenh qua dai"
    khoa = next((k for k in sorted(DANH_SACH_TRANG, key=len, reverse=True)
                 if tuple(lenh[:len(k)]) == k), None)
    if khoa is None:
        return "khong co trong danh sach trang: %s" % " ".join(lenh[:3])
    con, o = lenh[len(khoa):], DANH_SACH_TRANG[khoa]
    if len(con) > len(o):
        return "thua doi so: %s" % con[len(o):]
    for i, (kiem, bat_buoc) in enumerate(o):
        if i >= len(con):
            if bat_buoc:
                return "thieu doi so thu %d" % (i + 1)
            continue
        if not kiem(con[i]):
            return "doi so thu %d khong hop le: %r" % (i + 1, con[i][:80])
    return None


# ------------------------------------------------------------------ CLOUD
def giao(lenh: list, vi_sao: str = "", han_giay: int = HAN_MAC_DINH, goc: Path = LAB) -> Path:
    """Tao `tram/viec/<id>.json` trong kho dang lam. Lenh ngoai danh sach trang bi tu choi NGAY tai day."""
    loi = kiem_lenh(lenh)
    if loi:
        raise ValueError(loi)
    han = int(min(max(int(han_giay), 60), HAN_TOI_DA))
    i = time.strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(2)
    f = goc / "tram" / "viec" / (i + ".json")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"id": i, "lenh": lenh, "vi_sao": vi_sao[:500], "han_giay": han,
                             "luc": time.strftime("%Y-%m-%d %H:%M:%S")}, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    return f


def doc(id_: str | None = None, goc: Path = LAB) -> list[dict]:
    d = goc / "tram" / "ket_qua"
    ra = []
    for f in sorted(d.glob("*.json")) if d.exists() else []:
        if id_ and f.stem != id_:
            continue
        try:
            ra.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:
            ra.append({"id": f.stem, "trang_thai": "HONG", "loi": str(e)[:200]})
    return ra


# --------------------------------------------------------------- MAY NHA
def cau_hinh() -> dict:
    c = {"hop_thu": str(LAB.parent / "tram_hop_thu"), "nhanh": "", "tom_tat_re": True}
    if CAU_HINH.exists():
        try:
            c.update(json.loads(CAU_HINH.read_text(encoding="utf-8-sig")))
        except Exception:
            pass
    c["hop_thu"] = os.environ.get("TRAM_HOP_THU", c["hop_thu"])
    c["nhanh"] = os.environ.get("TRAM_NHANH", c["nhanh"])
    return c


def _git(hop_thu: Path, *args, timeout: int = 180) -> str:
    r = subprocess.run(["git", "-C", str(hop_thu), *args], capture_output=True, text=True,
                       timeout=timeout, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError("git %s: %s" % (" ".join(args[:2]), (r.stderr or r.stdout)[-400:]))
    return r.stdout


def _day(hop_thu: Path, nhanh: str, thong_diep: str, tep: list[str]) -> None:
    _git(hop_thu, "add", *tep)
    if not _git(hop_thu, "status", "--porcelain", *tep).strip():
        return
    _git(hop_thu, "commit", "-q", "-m", thong_diep)
    for i in range(5):
        try:
            _git(hop_thu, "push", "-q", "origin", "HEAD:%s" % nhanh)
            return
        except RuntimeError:
            if i == 4:
                raise
            time.sleep(2 ** (i + 1))
            _git(hop_thu, "pull", "-q", "--rebase", "origin", nhanh)


def cai(url: str, nhanh: str, hop_thu: str | None = None) -> dict:
    """Tao hop thu (ban clone rieng) + config/tram.json. Chay MOT lan tren may nha."""
    ht = Path(hop_thu or cau_hinh()["hop_thu"])
    if not (ht / ".git").exists():
        subprocess.run(["git", "clone", "-q", "--branch", nhanh, "--single-branch", url, str(ht)],
                       check=True, timeout=900)
    _git(ht, "config", "user.name", "tram-may-nha")
    _git(ht, "config", "user.email", "tram@may-nha.local")
    CAU_HINH.parent.mkdir(parents=True, exist_ok=True)
    c = cau_hinh()
    c.update(hop_thu=str(ht), nhanh=nhanh)
    CAU_HINH.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    lich = ('schtasks /Create /SC MINUTE /MO 5 /TN "TheBrain_Tram" /TR "\\"%s\\" tram chay" /F'
            % (LAB / "b.cmd"))
    return {"hop_thu": str(ht), "nhanh": nhanh, "task_scheduler": lich}


def _phien_ban_ma() -> str:
    try:
        h = subprocess.run(["git", "-C", str(LAB), "rev-parse", "--short", "HEAD"], capture_output=True,
                           text=True, timeout=30).stdout.strip()
        ban = subprocess.run(["git", "-C", str(LAB), "status", "--porcelain", "--untracked-files=no"],
                             capture_output=True, text=True, timeout=60).stdout.strip()
        return (h + ("+sua" if ban else "")) if h else "khong phai git"
    except Exception:
        return "khong doc duoc"


def _chay_lenh_that(lenh: list, han: int, log: Path) -> int:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    with log.open("wb") as g:
        return subprocess.run([sys.executable, str(LAB / "b.py"), *lenh], cwd=str(LAB), stdout=g,
                              stderr=subprocess.STDOUT, timeout=han, env=env).returncode


def _tep_moi(tu_luc: float) -> dict:
    ra, tong = {}, 0
    for f in sorted((LAB / "reports").rglob("*")) if (LAB / "reports").exists() else []:
        if (f.is_file() and f.suffix in (".md", ".json", ".jsonl", ".txt", ".csv")
                and f.stat().st_mtime >= tu_luc - 1 and tong < TONG_TEP_TOI_DA):
            try:
                s = f.read_text(encoding="utf-8", errors="replace")[:TEP_TOI_DA]
            except Exception:
                continue
            ra[str(f.relative_to(LAB)).replace("\\", "/")] = s
            tong += len(s)
    return ra


def _mot_viec(v: dict, chay_lenh, thu_muc_log: Path) -> dict:
    ra = {"id": v.get("id"), "lenh": v.get("lenh"), "may": platform.node(),
          "phien_ban_ma": _phien_ban_ma(), "bat_dau": time.strftime("%Y-%m-%d %H:%M:%S")}
    loi = kiem_lenh(v.get("lenh")) or (None if _ID.match(str(v.get("id", ""))) else "id sai dang")
    if loi:
        return dict(ra, trang_thai="TU_CHOI", ly_do=loi)
    lenh = v["lenh"]
    if lenh[:2] == ["tram", "ping"]:
        return dict(ra, trang_thai="XONG", ma_thoat=0, python=sys.version.split()[0],
                    lab=str(LAB), co_mt5=Path(os.environ.get("APPDATA", "")).joinpath(
                        "MetaQuotes").exists())
    han = int(min(max(int(v.get("han_giay") or HAN_MAC_DINH), 60), HAN_TOI_DA))
    log = thu_muc_log / ("%s.log" % v["id"])
    t0 = time.time()
    try:
        ma = chay_lenh(lenh, han, log)
        tt = "XONG" if ma == 0 else "LOI"
    except subprocess.TimeoutExpired:
        ma, tt = None, "HET_GIO"
    dong = log.read_text(encoding="utf-8", errors="replace").splitlines() if log.exists() else []
    ra.update(trang_thai=tt, ma_thoat=ma, giay=round(time.time() - t0, 1),
              ket_thuc=time.strftime("%Y-%m-%d %H:%M:%S"),
              duoi_log=[x[:400] for x in dong[-DUOI_LOG_DONG:]], tep_moi=_tep_moi(t0))
    return ra


def _tom_tat_re(kq: dict) -> str | None:
    """Model GIA RE nen ket qua thanh vai dong cho Claude doc - Claude khong phai doc log tho."""
    try:
        from nhan import nc_tho as THO
        than = json.dumps({k: kq.get(k) for k in ("lenh", "trang_thai", "ma_thoat", "duoi_log")},
                          ensure_ascii=False)[:24_000]
        tep = "\n".join("## %s\n%s" % (k, v[:4000]) for k, v in (kq.get("tep_moi") or {}).items())[:16_000]
        return THO.goi_re(
            "Tom tat ket qua mot lenh chay tren may nghien cuu giao dich, TOI DA 12 dong tieng Viet. "
            "Chep NGUYEN VAN moi con so (lai %, DD, so lenh, trang thai DAT/AM/CHUA_DO_DUOC, loi). "
            "Khong suy dien, khong khuyen nghi. Khong chac thi viet 'xem duoi_log'.\n\n"
            + than + "\n\n" + tep, max_tokens=700)
    except Exception as e:
        return "(khong tom tat duoc: %s)" % str(e)[:160]


def chay(chay_lenh=None, cau_hinh_=None) -> dict:
    """MOT luot tram. Task Scheduler goi 5 phut/lan; luot dang chay thi luot sau thoat ngay."""
    c = cau_hinh_ or cau_hinh()
    ht, nhanh = Path(c["hop_thu"]), c["nhanh"]
    if DUNG_TAI_MAY.exists():
        return {"trang_thai": "DUNG", "ly_do": str(DUNG_TAI_MAY)}
    if not nhanh or not (ht / ".git").exists():
        return {"trang_thai": "CHUA_CAI", "ly_do": "chay `b tram cai URL NHANH` truoc"}
    khoa = ht / ".git" / "tram_khoa.json"
    try:
        if json.loads(khoa.read_text(encoding="utf-8")).get("den_han", 0) > time.time():
            return {"trang_thai": "DANG_BAN"}
    except Exception:
        pass
    khoa.write_text(json.dumps({"pid": os.getpid(), "den_han": time.time() + 900}), encoding="utf-8")
    xong = []
    try:
        _git(ht, "pull", "-q", "--rebase", "origin", nhanh)
        if (ht / "tram" / "DUNG").exists():
            return {"trang_thai": "DUNG", "ly_do": "tram/DUNG tren nhanh %s" % nhanh}
        log_dir = ht / ".git" / "tram_log"
        log_dir.mkdir(exist_ok=True)
        cho = [f for f in sorted((ht / "tram" / "viec").glob("*.json"))
               if not (ht / "tram" / "ket_qua" / f.name).exists()] if (ht / "tram" / "viec").exists() else []
        for f in cho:
            try:
                v = json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:
                v = {"id": f.stem, "lenh": None, "_loi": str(e)}
            han = int(min(max(int(v.get("han_giay") or HAN_MAC_DINH), 60), HAN_TOI_DA))
            khoa.write_text(json.dumps({"pid": os.getpid(), "den_han": time.time() + han + 900}),
                            encoding="utf-8")
            kq = _mot_viec(v, chay_lenh or _chay_lenh_that, log_dir)
            if kq.get("trang_thai") in ("XONG", "LOI", "HET_GIO") and c.get("tom_tat_re", True) \
                    and kq.get("lenh", [None])[:2] != ["tram", "ping"]:
                kq["tom_tat_re"] = _tom_tat_re(kq)
            out = ht / "tram" / "ket_qua" / f.name
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
            (ht / "tram" / "trang_thai.json").write_text(json.dumps(
                {"may": platform.node(), "luc": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "viec_cuoi": f.stem, "con_cho": len(cho) - len(xong) - 1}, ensure_ascii=False),
                encoding="utf-8")
            _day(ht, nhanh, "tram: %s %s" % (f.stem, kq.get("trang_thai")),
                 ["tram/ket_qua/%s" % f.name, "tram/trang_thai.json"])
            xong.append({"id": f.stem, "trang_thai": kq.get("trang_thai")})
        return {"trang_thai": "XONG", "da_chay": xong}
    finally:
        try:
            khoa.unlink()
        except Exception:
            pass


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    lenh, con = argv[0], argv[1:]
    if lenh == "chay":
        r = chay()
        print(json.dumps(r, ensure_ascii=False))
        return 0 if r["trang_thai"] in ("XONG", "DANG_BAN", "DUNG") else 1
    if lenh == "cai":
        if len(con) < 2:
            print("b tram cai URL NHANH [THU_MUC_HOP_THU]")
            return 2
        print(json.dumps(cai(con[0], con[1], con[2] if len(con) > 2 else None), ensure_ascii=False, indent=1))
        return 0
    if lenh == "kiem":
        loi = kiem_lenh(con)
        print("QUA" if loi is None else "TU CHOI: " + loi)
        return 0 if loi is None else 1
    if lenh == "giao":
        vi_sao = ""
        if "--vi-sao" in con:
            i = con.index("--vi-sao")
            vi_sao = " ".join(con[i + 1:i + 2])
            con = con[:i] + con[i + 2:]
        try:
            f = giao(con, vi_sao)
        except ValueError as e:
            print("TU CHOI:", e)
            return 1
        print("da giao %s - commit + push de tram keo ve" % f.relative_to(LAB))
        return 0
    if lenh == "doc":
        for r in doc(con[0] if con else None):
            print("%s %-8s %s" % (r.get("id"), r.get("trang_thai"), " ".join(r.get("lenh") or [])[:80]))
            if con:
                print(r.get("tom_tat_re") or "\n".join((r.get("duoi_log") or [])[-40:]))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
