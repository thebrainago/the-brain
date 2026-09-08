# -*- coding: utf-8 -*-
"""cong.py - CHAM KET QUA BANG CODE. Day la thu giu qwen khoi noi doi.

## Vi sao cong khong duoc giao cho LLM

Da do 08/09/2026: LLM dien truong `co_che` cho 48 khai bao, bo tham dinh bac 41,
rong cuu duoc 3. Ti le nay khong dung duoc cho mot cong. Nen phan cong o day
la: **qwen doc va viet; code cham va chan.**

## Ba trang thai, khong phai hai

    DAT            phep do vuot nguong, va do duoc la do THAT
    AM             phep do chay duoc va khong vuot nguong
    CHUA_DO_DUOC   chua co du lieu de noi dat hay am

Trang thai thu ba la trang thai QUAN TRONG NHAT cua du an nay. Lich su lab day
nhung lan mot khau HONG doc y het mot ket qua am:

  - 406 URL chet chiem hang doi -> lan boc bao "het ton kho" khi con 4.560 tai lieu
  - het quota API -> hoi_json tra {'loi':...} -> me boc chay 2 GIAY, bao "0/20 co che"
  - lech ten provider -> moi loi goi tra "thieu OPENAI_API_KEY" -> doc nhu am
  - da_quet=0 bao thanh "khong bo nao thang"

Nen o day: ma thoat != 0, khong co file ra, hay bang ket qua co cac dong GIONG
HET NHAU -> deu la CHUA_DO_DUOC, tuyet doi khong phai AM.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import cau_hinh as CH

DAT, AM, CHUA = "DAT", "AM", "CHUA_DO_DUOC"


def _doc_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _cac_dong(d) -> list:
    """Rut ra danh sach dong ket qua tu mot JSON hinh dang bat ky."""
    if isinstance(d, list):
        return [x for x in d if isinstance(x, dict)]
    if isinstance(d, dict):
        for k in ("dong", "rows", "ket_qua", "bang", "chan", "cap", "ds", "muc"):
            v = d.get(k)
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
        v = [x for x in d.values() if isinstance(x, dict)]
        if len(v) >= 3:
            return v
    return []


# ---------------------------------------------------------------- kiem chung
def dong_giong_het_nhau(dong: list) -> tuple[bool, str]:
    """BAY SO 1 cua du an: cot ket qua giong het nhau = tham so khong vao duoc he.

    Da la dau hieu chung cua 3 loi khac nhau trong MOT phien (07/09). Kiem no
    tren MOI bang, tu dong, khong doi ai nho.
    """
    if len(dong) < 4:
        return False, "chi %d dong, chua du de xet" % len(dong)
    so = {}
    for k in dong[0]:
        gt = [d.get(k) for d in dong]
        if all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in gt):
            so[k] = len(set(gt))
    if not so:
        return False, "khong co cot so nao de xet"
    chet = [k for k, n in so.items() if n <= 1]
    # Nguong 70%: mot bang KET QUA that van co the co mot cot hang so hop le
    # (lot, von ban dau, so nam). Bay that la khi PHAN LON cot so dung im -
    # do la luc tham so khong vao duoc he. Chan o 1 cot thi bao dong gia lien tuc,
    # va mot cong keu oan mai thi nguoi ta tat no.
    can = 1 if len(so) == 1 else -(-7 * len(so) // 10)
    if len(chet) >= can:
        return True, "%d/%d cot so chi co MOT gia tri (%s) tren %d dong" % (
            len(chet), len(so), ", ".join(chet[:5]), len(dong))
    return False, "cot so bien thien binh thuong (%s)" % (
        ", ".join("%s:%d" % (k, n) for k, n in list(so.items())[:4]))


def dem_chan_ban(d) -> int:
    """Dem chan DUONG co chieu BAN trong mot file ket qua chan."""
    n = 0
    for x in _cac_dong(d):
        chieu = x.get("chieu", x.get("huong"))
        if chieu in (-1, "-1", "ban", "sell", "SELL"):
            lai = x.get("lai", x.get("loi_nhuan", x.get("pnl", x.get("lai_train"))))
            if lai is None or (isinstance(lai, (int, float)) and lai > 0):
                n += 1
    return n


def so_lenh_nho_nhat(d):
    ds = []
    for x in _cac_dong(d):
        for k in ("lenh", "so_lenh", "trades", "n_lenh"):
            if isinstance(x.get(k), (int, float)):
                ds.append(int(x[k]))
                break
    return min(ds) if ds else None


# ---------------------------------------------------------------- cham
def cham(viec: dict, ma_thoat: int, bat_dau: float, log_duoi: str,
         so_tay=None) -> dict:
    """Cham mot viec vua chay xong. Tra {ket, vi_sao, so}."""
    ra = {"ket": CHUA, "vi_sao": "", "so": {}}
    spec = viec.get("cong") or {}

    if ma_thoat != 0:
        ra["vi_sao"] = ("tien trinh thoat ma %s - day la HONG, khong phai ket qua am. "
                        "Duoi log: %s" % (ma_thoat, (log_duoi or "")[-400:]))
        return ra

    files = spec.get("file")
    files = [files] if isinstance(files, str) else list(files or [])
    dat_file = []
    for f in files:
        p = CH.LAB / f
        if not p.exists():
            ra["vi_sao"] = "khong co file ra %s du tien trinh thoat 0 -> CHUA DO DUOC" % f
            return ra
        if p.stat().st_mtime < bat_dau - 5:
            ra["vi_sao"] = ("file %s CU hon luc bat dau (%s) - lan chay nay khong "
                            "ghi gi. Doc no la doc ket qua cu." % (
                                f, time.strftime("%H:%M", time.localtime(p.stat().st_mtime))))
            return ra
        dat_file.append(p)

    d = _doc_json(dat_file[0]) if dat_file else None
    dong = _cac_dong(d) if d is not None else []
    ra["so"]["so_dong"] = len(dong)

    if dong:
        giong, ly_do = dong_giong_het_nhau(dong)
        ra["so"]["dong_giong_nhau"] = giong
        if giong:
            ra["vi_sao"] = ("BAY SO 1: %s. Tham so khong vao duoc he -> CHUA DO DUOC, "
                            "khong duoc ghi la am." % ly_do)
            return ra

    kieu = spec.get("kieu", "chay_duoc")

    if kieu == "chay_duoc":
        ra.update(ket=DAT, vi_sao="chay xong, ma thoat 0" +
                  (", file ra co %d dong" % len(dong) if dong else ""))
        return ra

    if kieu == "khong_rong":
        n = int(spec.get("toi_thieu", 1))
        if len(dong) >= n:
            ra.update(ket=DAT, vi_sao="file ra co %d dong (>= %d)" % (len(dong), n))
        else:
            ra.update(ket=AM, vi_sao="file ra chi %d dong (can >= %d)" % (len(dong), n))
        return ra

    if kieu == "chan_ban_tang":
        moc_ten = spec.get("moc", "chan_ban_" + viec["ma"])
        cu = (so_tay.moc(moc_ten) if so_tay else None)
        moi = dem_chan_ban(d)
        ra["so"].update(chan_ban=moi, chan_ban_truoc=cu)
        if so_tay:
            so_tay.dat_moc(moc_ten, moi)
        if cu is None:
            ra.update(ket=CHUA, vi_sao="lan dau do tren ma nay: %d chan ban duong. "
                                       "Da dat moc, lan sau so sanh duoc." % moi)
        elif moi > cu:
            ra.update(ket=DAT, vi_sao="chan ban duong %d -> %d (TANG)" % (cu, moi))
        else:
            ra.update(ket=AM, vi_sao="chan ban duong %d -> %d (khong tang) - "
                                     "nut that CHUA go duoc" % (cu, moi))
        return ra

    if kieu == "so_lenh_du":
        n = int(spec.get("toi_thieu", 25))
        m = so_lenh_nho_nhat(d)
        ra["so"]["lenh_nho_nhat"] = m
        if m is None:
            ra.update(ket=CHUA, vi_sao="file ra khong co cot so lenh - khong cham duoc. "
                                       "Moi bang so cua du an nay PHAI co so lenh.")
        elif m >= n:
            ra.update(ket=DAT, vi_sao="dong it lenh nhat co %d lenh (>= %d)" % (m, n))
        else:
            ra.update(ket=AM, vi_sao="dong it lenh nhat chi %d lenh (< %d) - "
                                     "chua du de ket luan" % (m, n))
        return ra

    if kieu == "truong_vuot":
        truong, nguong = spec["truong"], float(spec["nguong"])
        gt = [x.get(truong) for x in dong if isinstance(x.get(truong), (int, float))]
        ra["so"].update(truong=truong, cao_nhat=max(gt) if gt else None, nguong=nguong)
        if not gt:
            ra.update(ket=CHUA, vi_sao="khong dong nao co truong %s" % truong)
        elif max(gt) > nguong:
            ra.update(ket=DAT, vi_sao="%s cao nhat %.4g > nguong %.4g (%d/%d dong dat)"
                      % (truong, max(gt), nguong, sum(1 for x in gt if x > nguong), len(gt)))
        else:
            ra.update(ket=AM, vi_sao="%s cao nhat chi %.4g <= nguong %.4g tren %d dong"
                      % (truong, max(gt), nguong, len(gt)))
        return ra

    if kieu == "dem_dong_dat":
        truong, phep = spec["truong"], spec.get("phep", "<=")
        nguong, can = float(spec["nguong"]), int(spec.get("toi_thieu", 1))
        gt = [x for x in dong if isinstance(x.get(truong), (int, float))]
        hop = {"<=": lambda a: a <= nguong, "<": lambda a: a < nguong,
               ">=": lambda a: a >= nguong, ">": lambda a: a > nguong}[phep]
        dat = [x for x in gt if hop(x[truong])]
        ra["so"].update(co_truong=len(gt), dat=len(dat), can=can)
        if not gt:
            ra.update(ket=CHUA, vi_sao="khong dong nao co truong %s - cong khong "
                                       "chay duoc, dung doc thanh am" % truong)
        elif len(dat) >= can:
            ra.update(ket=DAT, vi_sao="%d/%d dong co %s %s %.4g (can >= %d)"
                      % (len(dat), len(gt), truong, phep, nguong, can))
        else:
            ra.update(ket=AM, vi_sao="chi %d/%d dong co %s %s %.4g (can >= %d)"
                      % (len(dat), len(gt), truong, phep, nguong, can))
        return ra

    if kieu == "trong_log":
        tu = spec.get("tu") or []
        thay = [t for t in tu if t.lower() in (log_duoi or "").lower()]
        if thay:
            ra.update(ket=DAT, vi_sao="log co: %s" % ", ".join(thay))
        else:
            ra.update(ket=AM, vi_sao="log khong co dau hieu nao trong %s" % (tu,))
        return ra

    if kieu == "khong_trong_log":
        # Cho viec ma IM LANG moi la dat: bo test, bo linter, kiem mang.
        tu = spec.get("tu") or []
        thay = [t for t in tu if t.lower() in (log_duoi or "").lower()]
        if not (log_duoi or "").strip():
            ra.update(ket=CHUA, vi_sao="log RONG - viec khong in gi thi khong cham "
                                       "duoc, dung doc thanh dat")
        elif thay:
            ra.update(ket=AM, vi_sao="log co dau hieu hong: %s" % ", ".join(thay))
        else:
            ra.update(ket=DAT, vi_sao="log khong co dau hieu nao trong %s" % (tu,))
        return ra

    ra["vi_sao"] = "kieu cong %s chua cai dat -> khong dam cham" % kieu
    return ra
