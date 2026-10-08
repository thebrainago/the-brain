# -*- coding: utf-8 -*-
"""giam_sat_may_nha.py - CLOUD GIAM SAT may nha sau `git pull`, KHONG LLM, in gon (chu du an 07/10/2026: bao cao dinh ky de may van hanh dung).

Doc `viec/may/*.json` (nhip tim), `viec/cho`, `viec/dang`, `viec/xong` va in: bo chay nao song / chet, so gio viec con lai, don ket,
don xong that vs xong-gia (ma thoat 0 nhung dong cuoi la loi), loi lap lai. Cuoi cung in `HANH_DONG:` goi y viec cloud phai lam.
Dung: python -m nhan.giam_sat_may_nha [--phut-ngung 30]
"""
from __future__ import annotations

import collections
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
VIEC = LAB / "viec"
LOI = re.compile(r"(Traceback|FileNotFoundError|KeyError|Error:|error \d+|CHUA_DO_DUOC|het slot|khong co du lieu)", re.I)


def _doc(f: Path) -> dict:
    try:
        return json.loads(f.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def nhip_tim(ngung_phut: float = 30.0, bay_gio: float | None = None) -> list[dict]:
    t = bay_gio or time.time()
    ra = []
    for f in sorted((VIEC / "may").glob("*.json")):
        d = _doc(f)
        try:
            tuoi = (datetime.fromtimestamp(t) - datetime.fromisoformat(d.get("luc", ""))).total_seconds() / 60
        except Exception:
            tuoi = 1e9
        ra.append({"ten": d.get("ten", f.stem), "tuoi_phut": round(tuoi), "song": tuoi <= ngung_phut,
                   "den": d.get("den"), "dang_chay": d.get("dang_chay"), "ly_do_den": d.get("ly_do_den")})
    return ra


def xong_gia(d: dict) -> str | None:
    """Don co trang_thai DAT nhung noi dung la loi -> ly do ngan, nguoc lai None."""
    if d.get("trang_thai") != "DAT":
        return None
    dong = "\n".join((d.get("bang_chung") or {}).get("dong_cuoi") or [])
    m = LOI.search(dong)
    return m.group(0) if m else None


def _nhom(d: dict) -> str:
    """Nhom don de uoc thoi gian: sweep theo KHUNG+kieu (M5 nang gap ~40 lan H1), con lai theo lan."""
    import re
    m = re.match(r"22\d+-\w+-(M5|M15|M30|H1)-(ha|mu|ba)-", d.get("ma", ""))
    if m:
        return "sweep-%s-%s" % (m.group(1), m.group(2))
    if "hc-luoi" in d.get("ma", ""):
        return "hieu-chuan-MT5"
    return str(d.get("lan") or "NHE").upper()


def lich_su_giay() -> dict[str, float]:
    """Thoi gian CHAY THAT trung binh (giay) theo nhom, tu viec/xong (bang_chung.giay). Thay cho han_phut*0.3 (sai ~100 lan)."""
    tong: dict[str, list[float]] = {}
    for f in (VIEC / "xong").glob("*.json"):
        d = _doc(f)
        g = (d.get("bang_chung") or {}).get("giay")
        if g is not None:
            tong.setdefault(_nhom(d), []).append(float(g))
    return {k: sum(v) / len(v) for k, v in tong.items() if v}


def tong_hop(ngung_phut: float = 30.0, bay_gio: float | None = None) -> dict:
    t = bay_gio or time.time()
    tim = nhip_tim(ngung_phut, t)
    cho = [f for f in (VIEC / "cho").glob("*.json") if not (VIEC / "xong" / f.name).exists()]
    gio_con = 0.0
    ls = lich_su_giay()
    giay_lan: dict[str, float] = {}
    theo_lan: dict[str, int] = {}
    for f in cho:
        d = _doc(f)
        lan = str(d.get("lan") or "NHE").upper()
        g = ls.get(_nhom(d), ls.get(lan, 60.0))           # giay chay that theo lich su (khong dung han_phut)
        giay_lan[lan] = giay_lan.get(lan, 0.0) + g
        gio_con += g / 3600.0
        theo_lan[lan] = theo_lan.get(lan, 0) + 1
    xong = sorted((VIEC / "xong").glob("*.json"), key=lambda f: f.stat().st_mtime)
    gan = [f for f in xong if t - f.stat().st_mtime < 3600]
    tt: dict[str, int] = {}
    gia = []
    for f in gan:
        d = _doc(f)
        tt[d.get("trang_thai", "?")] = tt.get(d.get("trang_thai", "?"), 0) + 1
        ly = xong_gia(d)
        if ly:
            gia.append((f.stem, ly))
    ket = []
    for f in (VIEC / "dang").glob("*.json"):
        d = _doc(f)
        if (VIEC / "xong" / f.name).exists() or not (VIEC / "cho" / f.name).exists():
            continue
        if t - f.stat().st_mtime > 3 * 3600:
            ket.append(f.stem)
    song = sum(1 for x in tim if x["song"])
    # GIO DONG HO (08/10/2026): `gio_viec_con` o tren la gio-LOI cong don; may chay song song nen cho that = gio-loi / so cho chay.
    # TESTER 4 slot, cac lan khac chia cho so bo chay song. Lan nao dai nhat quyet dinh.
    suc = {"TESTER": 4.0}
    gio_dong_ho = max([v / 3600.0 / suc.get(l, float(max(1, song))) for l, v in giay_lan.items()] or [0.0])
    try:
        from qwen import cau_loi as CL                       # xong-gia TOAN BO viec/xong (khong chi 1 gio): dem theo nhom
        gia_nhom = dict(collections.Counter(x["nhom"] for x in CL.quet_ket_qua(VIEC / "xong")))
    except Exception:
        gia_nhom = {}
    return {"nhip_tim": tim, "con_cho": len(cho), "theo_lan": theo_lan, "gio_viec_con": round(gio_con, 1), "gio_dong_ho": round(gio_dong_ho, 1),
            "gio_tuong_doi": {k: round(v / 3600, 1) for k, v in giay_lan.items()},
            "xong_1h": tt, "xong_gia_1h": gia, "xong_gia_nhom": gia_nhom, "dang_ket": ket[:10]}


def hanh_dong(k: dict) -> list[str]:
    ra = []
    chet = [x["ten"] for x in k["nhip_tim"] if not x["song"]]
    if chet and len(chet) == len(k["nhip_tim"]):
        ra.append("TAT CA bo chay mat nhip tim -> may nha tat / mat mang; bao chu du an NEU keo dai > 3h (bat may la quyen ho)")
    elif chet:
        ra.append("bo chay chet: %s -> nhac may nha khoi dong lai bo do" % ",".join(chet))
    gio = k.get("gio_dong_ho", k["gio_viec_con"])           # gio DONG HO (khong phai gio-loi cong don)
    if gio < 12:
        ra.append("hang doi chi con ~%.0f gio dong ho -> giao them >= 20 don (uu tien don do duoc, khong cache)" % gio)
    gn = k.get("xong_gia_nhom") or {}
    if gn.get("sua_duoc"):
        ra.append("%d don 'DAT' gia SUA DUOC (thieu thu vien / het dia / tester ban) -> chay `python -m qwen.cau_loi dua-lai` roi push" % gn["sua_duoc"])
    if gn.get("can_chan_doan"):
        ra.append("%d don tester chet / bien dich hong -> nho nha mo log tester (khong dua lai mu)" % gn["can_chan_doan"])
    if gn.get("khong_chay_lai"):
        ra.append("%d don thieu du lieu gia / ngoai doan -> sua DON (doi ma hoac xuat gia tu MT5), khong chay lai y het" % gn["khong_chay_lai"])
    if k["xong_gia_1h"]:
        ra.append("%d don 'DAT' that ra loi -> xem + sua + giao lai: %s" % (len(k["xong_gia_1h"]), ", ".join(m for m, _ in k["xong_gia_1h"][:5])))
    if k["dang_ket"]:
        ra.append("phieu nhan viec treo > 3h: %s" % ",".join(k["dang_ket"][:5]))
    vang = [x for x in k["nhip_tim"] if x["den"] in ("VANG", "DO")]
    if vang:
        ra.append("den %s o %d bo (%s)" % (vang[0]["den"], len(vang), (vang[0]["ly_do_den"] or "")[:80]))
    return ra or ["khong co viec cho cloud - im lang, khong bao"]


def main(argv: list[str]) -> int:
    ngung = float(argv[argv.index("--phut-ngung") + 1]) if "--phut-ngung" in argv else 30.0
    k = tong_hop(ngung)
    song = sum(1 for x in k["nhip_tim"] if x["song"])
    print("bo chay song %d/%d | con cho %d don (~%s gio dong ho, %s gio-loi) %s | xong 1h %s" % (
        song, len(k["nhip_tim"]), k["con_cho"], k["gio_dong_ho"], k["gio_viec_con"], k["theo_lan"], k["xong_1h"]))
    for ten, ly in k["xong_gia_1h"][:8]:
        print("  XONG-GIA %-40s %s" % (ten, ly))
    for h in hanh_dong(k):
        print("HANH_DONG:", h)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
