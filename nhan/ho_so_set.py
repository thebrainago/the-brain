# -*- coding: utf-8 -*-
"""ho_so_set.py - DOI CHIEU bo .set cua tac gia voi HO SO CO CHE do tu LENH THAT (`nhan/ho_so_bot.py`).

Chu du an 04/10/2026: moi bot co chien luoc va cach quan tri khac nhau; muc tieu cua the brain la boc tach duoc co che / yeu to
dac sac cua tung con bot de ap dung cheo. `ho_so_bot` do co che tu lich su lenh (khong can biet tac gia noi gi); module nay dat
bo .set (loi tac gia noi) canh so do do, de biet: tham so nao THAT SU quyet dinh hanh vi nao, tac gia noi gi ma lenh that
khong lam (MAU THUAN), va lenh that lam gi ma .set khong co tham so nao dieu khien (NUT AN).

## Moi tham so cua .set vao DUNG MOT trong muoi ket qua (`KET_QUA`)

    KHOP             khai bao va lenh that trung nhau. Mot lan trung la GIA THUYET; nhieu bo .set cua cung mot bot trung
                     (doi khai bao keo theo doi hanh vi) moi la bang chung: `so_sanh_bo_set`
    MAU_THUAN        tac gia noi X, lenh that cho thay Y, o cho lenh that CO DIEU KIEN de thay X (khong phai chua toi)
    TAT              khai tat (cong tat / gia tri 0) va lenh that khong co gi nguoc lai
    BI_CHE           tham so co that nhung bi tham so khac che (vd cac tang buoc cung moc: chi tang cuoi co hieu luc)
    CHUA_GAP         tham so quy dinh mot dieu kien ma lich su chua bao gio toi (vd tia tu lenh 20, chuoi sau nhat 15)
    KHONG_DO_DUOC    lich su lenh KHONG cho do (can duong gia / spread, hoac chi hien ra khi co su kien khac)
    KHONG_RO         thay mot phan nhung khong ket luan duoc
    CHUA_DOI_CHIEU   ten goi y mot khoi co che nhung module chua co bo doi chieu cho tham so nay (them sau, khong doan)
    KHONG_PHAN_LOAI  ten khong co trong bang quy tac (khong doan bua)
    KHONG_LIEN_QUAN  ma so / hien thi / chu thich

Mot tham so khong do duoc KHONG BAO GIO duoc ghi la "tac gia khong dung": TAT chi khi tac gia khai tat, MAU_THUAN chi khi lich
su CO DIEU KIEN de thay (chuoi du sau, du lenh, du gio) ma khong thay.

## Quy tac (rut tu CCBSN v2.6 / v3.05 tren 3 tep deals tester that, 04/10/2026)

* DON VI: khoang cach trong .set nhan voi MOT he so chung cho ca ho tham so (`he_so_don_vi`: 1 = pip cua san, 10 = point) - uoc
  luong tu cac cap khoang cach co the so, khong doan tung tham so. CCBSN tren vang: he so 1 (1 pip = 0,1 USD).
* TANG BUOC: buoc cua lenh thu b dung tang cuoi cung co `Orders2DistanceK <= b` (lenh DAU CUA TANG = dung moc); cac tang cung moc:
  tang co so thu tu lon hon che tang nho; `Distance0` chi dung khi moc >= 2. Do bang p10 cua buoc theo bac (trung vi bi keo len boi
  tick qua muc kich hoat).
* TANG LOT: lot lenh thu n = lam tron(lot dau x M(n)^(n-1), 2) - MU TINH TU LENH DAU; M(n) doi tai `Orders2NewMultiplierK`: lenh DAU
  CUA TANG = moc + 1 (khac buoc!). Co `c` (bang lenh) thi kiem TUNG lenh, khong co thi doi voi khoang he so cua `ho_so`.
* DOI UNG (hedge): so lenh kich hoat do duoc = `Orders2Hedging` + 1 (cach dem); lot lenh doi ung = lot lenh them moi nhat khi
  `UseLotsDCA2Hedging`.
* THOAT: lenh dong bang EA (khong phai TP may chu) cho bien = gia tri khai + 1 tick; TP may chu = dung gia tri khai.
* TRE KHAI BAO (`MinuteDelayNewDay` ...): do theo GIO DONG HO may chu (o 30 phut cua ngay), cach doc YEU NHAT = tinh tu 00:00. Tre
  sau lenh dong (`MinuteDelayAfterClose`): do bang khoang cach tu luc chuoi truoc dong den chuoi moi, moi chieu.
* Mot ten tham so chi la GOI Y (`khoi_co_che.loai_tu_ten_tham_so`); ket qua dua tren so do duoc, khong dua tren ten.

## Dung

    from nhan import ho_so_set as HS
    r = HS.doi_chieu_tep("reports/fixture/tester_vamge10k_kp_deals.csv.gz", "reports/fixture/ccbsn305_vamge10k.set.txt", ma="GOLD.i#")
    print("\n".join(r["tom_tat"]))          # <= 8 dong loi thuong
    r["mau_thuan"], r["nut_an"], r["cong_thuc"]
    python -m nhan.ho_so_set <deals> <bo.set> --ma GOLD.i# [--json ra.json] [--md ra.md]
    HS.so_sanh_bo_set([("A", r_a), ("B", r_b)])   # nhieu bo .set cua cung mot bot: doi khai bao co keo theo doi hanh vi khong
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import sys
import tempfile
import traceback
import unicodedata
from pathlib import Path

import numpy as np

from nhan import ea_tho as ET
from nhan import khoi_co_che as KC

PHIEN_BAN = 1

KHOP = "KHOP"
MAU_THUAN = "MAU_THUAN"
TAT = "TAT"
BI_CHE = "BI_CHE"
CHUA_GAP = "CHUA_GAP"
KHONG_DO_DUOC = "KHONG_DO_DUOC"
KHONG_RO = "KHONG_RO"
KHONG_PHAN_LOAI = "KHONG_PHAN_LOAI"
KHONG_LIEN_QUAN = "KHONG_LIEN_QUAN"
CHUA_DOI_CHIEU = "CHUA_DOI_CHIEU"
KET_QUA = (KHOP, MAU_THUAN, TAT, BI_CHE, CHUA_GAP, KHONG_DO_DUOC, KHONG_RO, CHUA_DOI_CHIEU, KHONG_PHAN_LOAI, KHONG_LIEN_QUAN)
DO_TIN = ("thap", "vua", "cao")

#: he so don vi ung vien (khoang cach .set x he so = pip cua san); 1,0 dung dau de hoa thi thang
HE_SO_UNG_VIEN = (1.0, 10.0, 0.1, 100.0, 0.01)
#: so chuoi toi thieu o mot dong de dem la co bang chung (p10 theo bac)
MAU_TOI_THIEU = 8


def _j(x):
    """JSON thuan: numpy -> python, nan / inf -> None."""
    if isinstance(x, dict):
        return {str(k): _j(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return [_j(v) for v in x]
    if isinstance(x, (str, bool)) or x is None:
        return x
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if isinstance(x, int):
        return x
    if hasattr(x, "item"):
        try:
            return _j(x.item())
        except Exception:
            return str(x)
    return str(x)


def _chuan(ten: str) -> str:
    """'InpOrders2Distance1' -> 'orders2distance1' (bo tien to Inp, chu thuong)."""
    return re.sub(r"^Inp(?=[A-Z0-9_])", "", ten.strip()).lower()


def _so(v):
    try:
        x = float(str(v).strip())
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _bool(v):
    s = str(v).strip().lower()
    if s in ("true", "1"):
        return True
    if s in ("false", "0"):
        return False
    return None


def _gio(v):
    """'08:30' -> so phut ke tu 00:00 (None neu khong phai gio)."""
    m = re.fullmatch(r"\s*(\d{1,2}):(\d{2})(?::\d{2})?\s*", str(v))
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    return h * 60 + mi if h < 24 and mi < 60 else None


_TF_MA = {"M1": 1, "M2": 2, "M3": 3, "M4": 4, "M5": 5, "M6": 6, "M10": 10, "M12": 12, "M15": 15, "M20": 20, "M30": 30,
          "H1": 60, "H2": 120, "H3": 180, "H4": 240, "H6": 360, "H8": 480, "H12": 720, "D1": 1440, "W1": 10080, "MN1": 43200}


def tf_phut(v):
    """Gia tri enum khung thoi gian cua .set -> phut. 0 (= khung cua bieu do) hoac gia tri la -> None.
    Quy uoc MT5: 1..30 = phut; 16385.. = gio (gia tri - 16384) x 60 (D1 = 16408); W1 = 32769; MN1 = 49153."""
    s = str(v).strip().upper().replace("PERIOD_", "")
    if s in _TF_MA:
        return _TF_MA[s]
    x = _so(s)
    if x is None or x != int(x):
        return None
    x = int(x)
    if 1 <= x <= 30:
        return x
    if 16385 <= x <= 16408:
        return (x - 16384) * 60
    if x == 32769:
        return 10080
    if x == 49153:
        return 43200
    return None


def _dung_sai(x, ab, ty):
    return max(ab, ty * abs(x))


def _gan(do, khai, ab, ty):
    """do (measured) co nam trong dung sai quanh khai (khai bao da nhan he so don vi)?"""
    return abs(do - khai) <= _dung_sai(khai, ab, ty)


def _gon_so(x, n=3):
    """So ngan gon cho van ban: 10.0 -> '10', 15.4 -> '15.4'."""
    if x is None:
        return "?"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    if float(x) == int(x) and abs(x) < 1e9:
        return str(int(x))
    return ("%." + str(n) + "g") % x


# ---------------------------------------------------------------------------------------------------------------- doc .set
def doc_set(nguon, ten: str | None = None) -> dict:
    """Doc bo .set cua tac gia: duong dan (`.set`, `.set.txt`, `.txt`) HOAC van ban .set. Tra {ten, khoa, n, sha, van_ban}.

    Dung lai `ea_tho.doc_set` (moi kiem tra an toan: ten khoa sach, khong trung khoa, khong khoa nhay cam / token, bo hau to
    toi uu `||...`, bo dong ghi chu) bang cach chep ra tep tam `<ten>.set`: `.set.txt` (tep chu duoc Windows doi duoi) va van ban
    deu doc duoc. Loi -> ValueError / OSError (khong in noi dung dong sai)."""
    thu_muc = tempfile.mkdtemp(prefix="hs_set_")
    try:
        if isinstance(nguon, (bytes, bytearray)):
            nguon = bytes(nguon).decode("utf-8", "replace")
        la_van_ban = isinstance(nguon, str) and ("\n" in nguon or "\r" in nguon)
        if la_van_ban:
            ten_tep = re.sub(r"[^A-Za-z0-9_.-]", "_", (ten or "bo_set"))[:40]
            p = Path(thu_muc) / (ten_tep + ".set")
            p.write_text(nguon, encoding="utf-8")
        else:
            goc = Path(str(nguon))
            ten_tep = re.sub(r"[^A-Za-z0-9_.-]", "_", (ten or re.sub(r"(?i)(\.txt)?(\.set)?(\.txt)?$", "", goc.name)) or "bo_set")[:40]
            p = Path(thu_muc) / (ten_tep + ".set")
            shutil.copyfile(goc, p)
        r = ET.doc_set(p)
        r["ten"] = ten_tep
        return r
    finally:
        shutil.rmtree(thu_muc, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------------------- bo thu thap
_BO_DO: list = []


def _bo_do(fn):
    """Dang ky mot bo doi chieu (chay theo thu tu khai bao; dong dau tien ghi cho mot tham so la dong thang)."""
    _BO_DO.append((fn.__name__.lstrip("_"), fn))
    return fn


class _Bo:
    """Gom: bo .set (khoa chuan hoa), ho so do, bang lenh (tuy chon), he so don vi va cac dong ket qua."""

    def __init__(self, khoa: dict, hs: dict, c=None, f: float = 1.0):
        self.khoa = {str(k): str(v) for k, v in khoa.items()}
        self.ten: dict[str, str] = {}       # chuan -> ten goc
        self.v: dict[str, str] = {}         # chuan -> gia tri (chuoi)
        self.canh_bao: list[str] = []
        for t, val in self.khoa.items():
            n = _chuan(t)
            if n in self.ten:
                self.canh_bao.append("hai khoa cung ten chuan '%s': %s va %s (giu khoa dau)" % (n, self.ten[n], t))
                continue
            self.ten[n] = t
            self.v[n] = val
        self.hs, self.c, self.f = hs, c, f
        self.hang: dict[str, dict] = {}
        self.giai_thich: dict[str, list[str]] = {}
        self.loi: list[str] = []
        self.lop = ""
        self.kiem_lot = None
        self.ghi_chu: dict = {}

    # ---- doc gia tri .set
    def co(self, n):
        return n in self.v

    def so(self, n, mac_dinh=None):
        x = _so(self.v.get(n))
        return mac_dinh if x is None else x

    def bat(self, n):
        return _bool(self.v[n]) if n in self.v else None

    def khac_het(self, regex):
        """Cac ten chuan khop regex va chua co dong ket qua."""
        return [n for n in self.v if n not in self.hang and re.search(regex, n)]

    # ---- doc so do
    def phep(self, ten):
        return (self.hs.get("phep_do") or {}).get(ten) or {}

    def sl(self, ten):
        return self.phep(ten).get("so_lieu") or {}

    def khoi(self, ma):
        return (self.hs.get("khoi") or {}).get(ma) or {}

    def kl(self, ma):
        return self.khoi(ma).get("ket_luan", "khong_do_duoc")

    def dt(self, ma):
        return self.khoi(ma).get("do_tin", "thap")

    def ts(self, ten):
        e = (self.hs.get("tham_so") or {}).get(ten)
        return e.get("gia_tri") if e else None

    # ---- ghi ket qua
    def ghi(self, n, kq, khoi="", do=None, don_vi="", do_tin="vua", ly_do="", nguon="", lop=None, ghi_de=False):
        if n not in self.v:
            return
        if n in self.hang and not ghi_de:
            return
        assert kq in KET_QUA, kq
        if do_tin not in DO_TIN:
            do_tin = "vua"
        self.hang[n] = {"ten": self.ten[n], "khai": self.v[n], "lop": lop or self.lop, "khoi": khoi, "ket_qua": kq,
                        "do": do, "don_vi": don_vi, "do_tin": do_tin, "ly_do": ly_do, "nguon_do": nguon}
        if kq == KHOP and khoi:
            for b in ([khoi] if isinstance(khoi, str) else list(khoi)):
                self.giai_thich.setdefault(b, []).append(self.ten[n])

    def ghi_ds(self, ds, kq, **kw):
        for n in ds:
            self.ghi(n, kq, **kw)


def _ty(a, b):
    return (a / b) if b else 0.0


def _do_tin_tu_mau(n_mau, ty_khop=1.0):
    """Do tin cua mot phep trung theo so mau va ty le khop."""
    if ty_khop >= 0.9 and n_mau >= 100:
        return "cao"
    if ty_khop >= 0.8 and n_mau >= 30:
        return "vua"
    return "thap"


def _chay_bo_do(bo: _Bo, ten, fn):
    try:
        fn(bo)
    except Exception as e:      # mot bo hong khong duoc lam mat het - nhung phai THAY DUOC (khong nuot)
        dong = traceback.extract_tb(e.__traceback__)[-1]
        bo.loi.append("%s: %s: %s (dong %d)" % (ten, type(e).__name__, str(e)[:140], dong.lineno))


# ---------------------------------------------------------------------------------------------------------------- don vi
def _trong_cua_so(p, x):
    """Buoc do (p10 theo bac) co nam trong cua so quanh khoang cach khai bao `x` khong? Cua so KHONG doi xung: buoc do khong the nho
    hon khai bao nhieu (chi nho hon chut vi lech ask / bid) nhung lon hon duoc (tick nhay qua muc kich hoat, tester cach tick 10-20 giay)."""
    return x - max(0.5, 0.03 * x) <= p <= x + max(1.0, 0.07 * x)


def _hang_buoc(bo: "_Bo"):
    """[(bac, n, p10)] cua cac bac du mau (n >= MAU_TOI_THIEU) trong bang buoc theo bac cua ho so."""
    out = []
    for r in bo.sl("buoc_theo_bac").get("bang") or []:
        try:
            b, n, p = int(r["bac"]), int(r["n"]), r.get("p10")
        except (KeyError, TypeError, ValueError):
            continue
        if p is None or n < MAU_TOI_THIEU:
            continue
        out.append((b, n, float(p)))
    return out


def _tier_khai(bo: "_Bo"):
    """(Distance0, [(moc, so_thu_tu, khoang)]) sap theo (moc, so thu tu): tang SAU thang tang truoc khi cung moc."""
    d0 = bo.so("distance0")
    tiers = []
    for n in bo.v:
        m = re.fullmatch(r"distance([1-9]\d*)", n)
        if not m:
            continue
        i = int(m.group(1))
        thr, dist = bo.so("orders2distance%d" % i), bo.so(n)
        if thr is not None and dist is not None:
            tiers.append((thr, i, dist))
    tiers.sort()
    return d0, tiers


def _buoc_khai(b, d0, tiers, off=0):
    """(id tang, khoang) cua buoc cho lenh thu b (b >= 2): tang cuoi co moc <= b + off; khong co thi Distance0 (id 0)."""
    cur = (0, d0) if d0 is not None else None
    for thr, i, dist in tiers:
        if thr <= b + off:
            cur = (i, dist)
    return cur


def _lich_buoc(d0, tiers, off):
    """Cac doan [b_dau, b_cuoi, id_tang, khoang] cua lich buoc theo bac b = 2..300."""
    doan = []
    for b in range(2, 301):
        t = _buoc_khai(b, d0, tiers, off)
        if t is None:
            continue
        if doan and doan[-1][2] == t[0]:
            doan[-1][1] = b
        else:
            doan.append([b, b, t[0], t[1]])
    return doan


def _bang_chung_tang(rows, d0, tiers, off, f):
    """{id tang: [(bac, n, p10, trong_cua_so)]} theo lich khai bao da nhan he so don vi f."""
    ev: dict = {}
    for b, n, p in rows:
        t = _buoc_khai(b, d0, tiers, off)
        if t is not None:
            ev.setdefault(t[0], []).append((b, n, p, _trong_cua_so(p, t[1] * f)))
    return ev


def _cap_tp(bo: "_Bo"):
    """[(ten nhom, khai, do)] cac cap TP / trailing co the so (dung de uoc luong he so don vi). Do bang pip cua san."""
    out = []
    tp_do = bo.ts("tp_pip")
    if tp_do is None:
        tp_do = bo.ts("tp_pip_chuoi_1")
    if bo.so("tp") and tp_do:
        out.append(("tp", bo.so("tp"), float(tp_do)))
    chuoi = [float(v["gia_tri"]) for k, v in (bo.hs.get("tham_so") or {}).items()
             if k.startswith("tp_pip_chuoi_") and k != "tp_pip_chuoi_1" and v.get("gia_tri") is not None]
    if bo.so("tpdca") and chuoi:
        out.append(("tpdca", bo.so("tpdca"), float(np.median(chuoi))))
    sl_do = bo.ts("trailing_khoa_dau_pip")
    if sl_do is None:
        sl_do = bo.ts("khoa_loi_pip")
    if bo.so("initialsltrailing") and sl_do:
        out.append(("khoa_dau", bo.so("initialsltrailing"), float(sl_do)))
    if bo.so("trailingstep") and bo.ts("trailing_buoc_pip"):
        out.append(("buoc_trailing", bo.so("trailingstep"), float(bo.ts("trailing_buoc_pip"))))
    return out


def uoc_luong_don_vi(bo: "_Bo") -> dict:
    """He so don vi chung cua ho tham so khoang cach (`khoang .set` x he so = pip cua san): thu cac ung vien, cham theo ty le o buoc
    theo bac khop (theo so mau) + moi cap TP / trailing khop; hoa thi lay he so NHO NHAT trong danh sach (1,0 truoc). Khong gia dinh
    san - nhung khong co cap nao de so thi tra 1,0 kem `chac = False`."""
    d0, tiers = _tier_khai(bo)
    rows = _hang_buoc(bo)
    cap = _cap_tp(bo)
    best = None
    diem_tat = {}
    for f in HE_SO_UNG_VIEN:
        d = {}
        if rows and (d0 is not None or tiers):
            tot = sum(n for _, n, _ in rows)
            ok = 0
            for b, n, p in rows:
                t = _buoc_khai(b, d0, tiers, 0)
                if t is not None and _trong_cua_so(p, t[1] * f):
                    ok += n
            d["buoc"] = ok / tot if tot else 0.0
        for ten, khai, do in cap:
            d[ten] = 1.0 if _gan(do, khai * f, 0.4, 0.03) else 0.0
        s = sum(d.values())
        diem_tat[f] = round(s, 3)
        if best is None or s > best[1] + 1e-9:
            best = (f, s, d)
    n_nhom = len(best[2]) if best else 0
    if not n_nhom:
        return {"he_so": 1.0, "chac": False, "diem": diem_tat,
                "ly_do": "khong co cap khoang cach / TP / trailing nao so duoc voi ho so: giu he so 1 (1 don vi .set = 1 pip cua san)"}
    f, s, d = best
    hai = max([v for k, v in diem_tat.items() if k != f] or [0.0])
    chac = s >= 0.8 * n_nhom and s - hai >= 0.5
    return {"he_so": f, "chac": bool(chac), "diem": diem_tat,
            "ly_do": "he so %s: diem %s / %d nhom (%s); he so khac tot nhat %s" % (
                _gon_so(f), _gon_so(round(s, 2)), n_nhom, ", ".join("%s %s" % (k, _gon_so(round(v, 2))) for k, v in d.items()),
                _gon_so(round(hai, 2)))}


# ---------------------------------------------------------------------------------------------------------------- buoc luoi
def _sum_n(l):
    return sum(x[1] for x in l)


def _xu_tang(tid, dist, ev, doan, f, ten_tang):
    """Ket qua cua MOT tang khoang cach: (kq, do, do_tin, ly_do) hoac None neu tang bi che (khong bao gio duoc chon)."""
    chay = [d for d in doan if d[2] == tid]
    if not chay:
        return None
    s = chay[0][0]
    l = ev.get(tid, [])
    khai = dist * f
    if not l:
        return (CHUA_GAP, None, "thap",
                "%s = %s pip ap dung tu lenh thu %d; chua co bac nao (>= %d chuoi) o do sau do de do" % (ten_tang, _gon_so(khai), s, MAU_TOI_THIEU))
    tot = _sum_n(l)
    ok = sum(x[1] for x in l if x[3])
    fr = ok / tot if tot else 0.0
    do = float(np.median([x[2] for x in l]))
    bacs = "%d-%d" % (min(x[0] for x in l), max(x[0] for x in l)) if len(l) > 1 else "%d" % l[0][0]
    ly = "buoc do duoc (p10 theo bac, bac %s, %d lenh them) trung vi %s pip, khai %s pip: %.0f%% lenh trong cua so" % (
        bacs, tot, _gon_so(do), _gon_so(khai), 100 * fr)
    if fr >= 0.8:
        return (KHOP, do, _do_tin_tu_mau(tot, fr), ly)
    if fr < 0.5:
        return (MAU_THUAN, do, "vua" if tot >= 30 else "thap", ly)
    return (KHONG_RO, do, "thap", ly)


def _ly_do_che(tid, d0, tiers, off):
    if tid == 0:
        thr_min = min((t[0] for t in tiers), default=None)
        return ("moc nho nhat Orders2Distance = %s (<= 2 + lech): tang co hieu luc ngay tu lenh 2 nen Distance0 khong bao gio duoc dung"
                % _gon_so(thr_min))
    mine = next(t for t in tiers if t[1] == tid)
    w = _buoc_khai(max(2, int(math.ceil(mine[0]))), d0, tiers, off)
    return ("moc Orders2Distance%d = %s trung hoac nho hon moc tang khac: tang %s (so thu tu lon hon, thang) co hieu luc tu cung lenh nen "
            "tang nay khong bao gio duoc dung" % (tid, _gon_so(mine[0]), w[0] if w else "?"))


def _gan_nhat_hang(rows_theo_bac, b, huong, tam=3):
    """Hang du mau gan bac b nhat theo `huong` (-1 truoc, +1 sau, 0 chinh no) trong `tam` bac; None neu khong co."""
    if huong == 0:
        return (b,) + rows_theo_bac[b] if b in rows_theo_bac else None
    for k in range(0 if huong > 0 else 1, tam + 1):
        bb = b + huong * k
        if bb in rows_theo_bac:
            return (bb,) + rows_theo_bac[bb]
    return None


@_bo_do
def _buoc(bo: "_Bo"):
    bo.lop = "luoi"
    d0, tiers = _tier_khai(bo)
    rows = _hang_buoc(bo)
    f = bo.f
    bac_max = max((b for b, _, _ in rows), default=0)
    if bo.kl("luoi_gian_cach_deu") == "co" and bo.kl("luoi_buoc_theo_bac") != "co":
        khoi_tang = "luoi_gian_cach_deu"        # buoc deu o moi bac: cac tang cung moc chi con MOT khoang cach hieu luc
    else:
        khoi_tang = "luoi_buoc_theo_bac" if len(tiers) else "luoi_gian_cach_deu"
    if d0 is None and not tiers:
        _buoc_don(bo, rows, f)
        _buoc_nhan(bo, rows)
        return
    tot = sum(n for _, n, _ in rows)
    chon = (-1.0, 0)
    for off in (0, 1, -1):
        ev = _bang_chung_tang(rows, d0, tiers, off, f)
        ok = sum(x[1] for l in ev.values() for x in l if x[3])
        fr = ok / tot if tot else 0.0
        if fr > chon[0] + 1e-9:
            chon = (fr, off)
    frac_chung, off = chon
    bo.ghi_chu["buoc"] = {"ty_khop_chung": round(frac_chung, 3), "lech_moc": off, "n_hang": len(rows), "bac_sau_nhat": bac_max,
                          "tang": [{"id": t[1], "moc": t[0], "khoang": t[2]} for t in tiers], "distance0": d0}
    ev = _bang_chung_tang(rows, d0, tiers, off, f)
    doan = _lich_buoc(d0, tiers, off)
    theo_bac = {b: (n, p) for b, n, p in rows}
    ket_tang: dict = {}
    # --- khoang cach cua tung tang (id 0 = Distance0)
    ds_tang = ([(0, "distance0", d0)] if d0 is not None else []) + [(i, "distance%d" % i, dist) for _, i, dist in tiers]
    for tid, ten, dist in ds_tang:
        r = _xu_tang(tid, dist, ev, doan, f, bo.ten.get(ten, ten))
        if r is None:
            bo.ghi(ten, BI_CHE, khoi=khoi_tang, do_tin="vua", ly_do=_ly_do_che(tid, d0, tiers, off))
            ket_tang[tid] = None
            continue
        kq, do, dt, ly = r
        ket_tang[tid] = r
        khoi = khoi_tang
        bo.ghi(ten, kq, khoi=khoi, do=do, don_vi="pip", do_tin=dt, ly_do=ly, nguon="buoc_theo_bac.bang[p10]")
    # --- moc doi tang
    for thr, i, dist in tiers:
        ten = "orders2distance%d" % i
        run = next((d for d in doan if d[2] == i), None)
        if run is None:
            bo.ghi(ten, BI_CHE, khoi=khoi_tang, do_tin="vua", ly_do=_ly_do_che(i, d0, tiers, off))
            continue
        idx = doan.index(run)
        s = run[0]
        if idx == 0:
            r = ket_tang.get(i)
            if r is None:
                continue
            kq, do, dt, ly = r
            bo.ghi(ten, kq if kq != MAU_THUAN else MAU_THUAN, khoi=khoi_tang, do=None, do_tin=dt,
                   ly_do="moc %s <= 2: tang %d co hieu luc ngay tu lenh 2 (khong co tang truoc de so sanh); %s" % (_gon_so(thr), i, ly),
                   nguon="buoc_theo_bac.bang[p10]")
            continue
        prev = doan[idx - 1]
        d_prev, d_new = prev[3] * f, run[3] * f
        if abs(d_prev - d_new) <= max(0.5, 0.03 * d_new):
            bo.ghi(ten, KHONG_DO_DUOC, khoi=khoi_tang, do_tin="vua",
                   ly_do="khoang cach hai ben moc bang nhau (%s va %s pip): doi tang khong de lai dau vet trong buoc" % (
                       _gon_so(d_prev), _gon_so(d_new)))
            continue
        if s > bac_max:
            bo.ghi(ten, CHUA_GAP, khoi=khoi_tang, do_tin="thap",
                   ly_do="tang doi o lenh thu %d; bac sau nhat co du chuoi de do la %d" % (s, bac_max))
            continue
        truoc = _gan_nhat_hang(theo_bac, s, -1)
        sau = _gan_nhat_hang(theo_bac, s, 0) or _gan_nhat_hang(theo_bac, s, +1)
        if truoc is None or sau is None:
            bo.ghi(ten, KHONG_RO, khoi=khoi_tang, do_tin="thap",
                   ly_do="thieu bac du mau o mot ben moc %d (can >= %d chuoi moi ben)" % (s, MAU_TOI_THIEU))
            continue
        ok_t = _trong_cua_so(truoc[2], d_prev)
        ok_s = _trong_cua_so(sau[2], d_new)
        n_min = min(truoc[1], sau[1])
        ly = "buoc bac %d = %s pip (khai truoc moc %s), bac %d = %s pip (khai sau moc %s); moc doi o lenh thu %d%s" % (
            truoc[0], _gon_so(truoc[2]), _gon_so(d_prev), sau[0], _gon_so(sau[2]), _gon_so(d_new), s,
            ("; lech %+d so voi khai bao (cach dem)" % off) if off else "")
        if ok_t and ok_s:
            bo.ghi(ten, KHOP, khoi=khoi_tang, do=float(s), don_vi="lenh", do_tin="cao" if n_min >= 30 else "vua" if n_min >= MAU_TOI_THIEU else "thap",
                   ly_do=ly, nguon="buoc_theo_bac.bang[p10]")
        else:
            bo.ghi(ten, MAU_THUAN, khoi=khoi_tang, do=float(s), don_vi="lenh", do_tin="vua" if n_min >= 30 else "thap", ly_do=ly,
                   nguon="buoc_theo_bac.bang[p10]")
    _buoc_nhan(bo, rows)


def _buoc_don(bo: "_Bo", rows, f):
    """Bo .set chi co MOT khoang cach (ten chung: distance, step, ...): so voi buoc do chung."""
    for n in [n for n in bo.v if re.fullmatch(r"(distance|step|gridstep|pipstep|stepgrid|pipsstep|levelstep|spacing)", n)]:
        x = bo.so(n)
        if x is None:
            continue
        if not rows:
            bo.ghi(n, KHONG_DO_DUOC, khoi="luoi_gian_cach_deu", do_tin="thap", ly_do="ho so khong co bac nao du mau de do buoc")
            continue
        tot = sum(r[1] for r in rows)
        ok = sum(r[1] for r in rows if _trong_cua_so(r[2], x * f))
        fr = ok / tot if tot else 0.0
        do = float(np.median([r[2] for r in rows]))
        ly = "buoc do duoc trung vi %s pip tren %d lenh them, khai %s pip: %.0f%% trong cua so" % (_gon_so(do), tot, _gon_so(x * f), 100 * fr)
        bo.ghi(n, KHOP if fr >= 0.8 else MAU_THUAN if fr < 0.5 else KHONG_RO, khoi="luoi_gian_cach_deu", do=do, don_vi="pip",
               do_tin=_do_tin_tu_mau(tot, fr) if fr >= 0.8 else "vua" if tot >= 30 else "thap", ly_do=ly, nguon="buoc_theo_bac.bang[p10]")


def _buoc_nhan(bo: "_Bo", rows):
    """`DistanceMulti`: he so gian buoc. Neu khai khac 1 ma buoc do duoc PHANG thi ghi MAU_THUAN (co the chi bat o che do khac)."""
    n = "distancemulti"
    if n not in bo.v:
        return
    m = bo.so(n)
    if m is None:
        return
    if abs(m - 1.0) < 1e-9:
        bo.ghi(n, TAT, khoi="luoi_buoc_gian_dan", do_tin="vua", ly_do="he so 1,0 = khong gian buoc (trung tinh)")
        return
    kl, dt = bo.kl("luoi_buoc_gian_dan"), bo.dt("luoi_buoc_gian_dan")
    so_bac = len(rows)
    if kl == "co":
        bo.ghi(n, KHOP, khoi="luoi_buoc_gian_dan", do_tin=dt, ly_do="ho so thay buoc gian theo bac (khoi luoi_buoc_gian_dan co)")
    elif kl == "khong" and so_bac >= 3:
        _, tiers = _tier_khai(bo)
        bac_max = max((b for b, _, _ in rows), default=0)
        thr_cuoi = max((t[0] for t in tiers), default=None)
        chua_toi = thr_cuoi is not None and bac_max <= thr_cuoi
        bo.ghi(n, MAU_THUAN, khoi="luoi_buoc_gian_dan", do_tin="vua" if (dt == "cao" and not chua_toi) else "thap",
               ly_do="tac gia khai he so %s nhung buoc do duoc phang theo bac tren %d bac du mau - khong thay tac dung (co the he so chi bat o "
                     "che do khac, vd DCAMODE, hoac chi sau tang cuoi%s)" % (
                         _gon_so(m), so_bac, (": bac sau nhat do duoc %d chua qua tang cuoi (lenh %s)" % (bac_max, _gon_so(thr_cuoi))) if chua_toi
                         else " chua toi"))
    else:
        bo.ghi(n, KHONG_RO, khoi="luoi_buoc_gian_dan", do_tin="thap", ly_do="khong du bac de ket luan buoc co gian hay khong")


# ---------------------------------------------------------------------------------------------------------------- lot
def _lot_tang(bo: "_Bo"):
    """[(moc, he_so_moi, ten_moc, ten_he_so)] sap theo moc: Orders2NewMultiplier, ...2, ...3 (cap voi NewMultiplier, ...2, ...3)."""
    tiers = []
    for suf in [""] + [str(i) for i in range(2, 13)]:
        tn, mn = "orders2newmultiplier" + suf, "newmultiplier" + suf
        thr, m = bo.so(tn), bo.so(mn)
        if thr is not None and m is not None:
            tiers.append((thr, m, tn, mn))
    tiers.sort(key=lambda t: (t[0], t[2]))
    return tiers


def _he_so_n(n, base, doi, tiers):
    """He so nhan ap dung cho lenh thu n: co doi he so thi lay tang cuoi co moc < n (lenh DAU cua tang = moc + 1)."""
    m = base
    if doi:
        for thr, mm, _, _ in tiers:
            if n > thr:
                m = mm
    return m


def _lam_tron_lot(x, q):
    return round(math.floor(x / q + 0.5 + 1e-9) * q, 8)


def _lot_dau_do(bo: "_Bo"):
    """Lot lenh DAU cua chuoi do duoc: tu bang lenh neu co, khong thi tu hang dau cua bang lot theo bac."""
    if bo.c is not None:
        try:
            L = bo.c.lenh
            v = L.loc[L["bac_tang"] == 1, "lot"].round(4)
            if len(v):
                return float(v.mode().iloc[0])
        except Exception:
            pass
    b = bo.sl("lot_theo_bac").get("bang") or []
    if b and b[0].get("r0"):
        return round(float(b[0]["lot"]) / float(b[0]["r0"]), 4)
    return None


def _kiem_lot(bo: "_Bo", lots, base, doi, tiers):
    """Kiem TUNG lenh: lot = lam_tron(lot_dau x M(n)^(n-1)). Can bang lenh (`bo.c`); tra None neu khong co."""
    if bo.c is None:
        return None
    from nhan import ho_so_bot as HB
    L = HB.bo_hedge(bo.c).lenh
    n = L["bac_tang"].to_numpy(int)
    lot = L["lot"].to_numpy(float)
    q = float(bo.sl("lot_theo_bac").get("buoc_lot") or 0.01)
    pred = np.array([_lam_tron_lot(lots * _he_so_n(int(k), base, doi, tiers) ** (int(k) - 1), q) for k in n])
    ok = np.abs(pred - lot) < q / 2 + 1e-9
    sai = [(int(n[i]), float(lot[i]), float(pred[i])) for i in np.where(~ok)[0][:5]]
    return {"n": n, "ok": ok, "khop": int(ok.sum()), "tong": int(len(ok)), "ty": float(ok.mean()) if len(ok) else 0.0,
            "n_sau_nhat": int(n.max()) if len(n) else 0, "lech_mau": sai, "lot_buoc": q}


def _khoang_lot(base, doi, tiers):
    """[(a, b, he_so, ten_he_so, ten_moc)]: n thuoc [a, b] dung he so do; b = None la khong gioi han."""
    if not doi or not tiers:
        return [(2, None, base, "multiplier", None)]
    out = [(2, int(tiers[0][0]), base, "multiplier", None)]
    for k, (thr, m, tn, mn) in enumerate(tiers):
        hi = int(tiers[k + 1][0]) if k + 1 < len(tiers) else None
        out.append((int(thr) + 1, hi, m, mn, tn))
    return out


def _xu_khoang_lot(bo: "_Bo", kt, a, b, m, base_lot):
    """(kq, do_tin, ly_do, so lenh) cho mot khoang lenh [a, b]: kiem chinh xac (co bang lenh) hoac theo khoang he so cua ho so."""
    if kt is not None:
        n = kt["n"]
        mask = (n >= a) & ((n <= b) if b is not None else True)
        tong = int(mask.sum())
        if tong == 0:
            return (CHUA_GAP, "thap", "khong co lenh nao o bac %d%s" % (a, ("-%d" % b) if b else "+"), 0)
        khop = int(kt["ok"][mask].sum())
        fr = khop / tong
        ly = "lot tung lenh o bac %d%s: %d/%d khop cong thuc lam_tron(lot_dau x %s^(n-1))" % (a, ("-%d" % b) if b else "+", khop, tong, _gon_so(m))
        if fr >= 0.98:
            return (KHOP, "cao" if tong >= 100 else "vua" if tong >= 30 else "thap", ly, tong)
        if fr < 0.8:
            return (MAU_THUAN, "vua" if tong >= 30 else "thap", ly, tong)
        return (KHONG_RO, "thap", ly, tong)
    seg = [s for s in (bo.sl("lot_theo_bac").get("doan_he_so") or []) if s["den"] >= a and (b is None or s["tu"] <= b)]
    if not seg:
        return (CHUA_GAP, "thap", "ho so khong co doan he so nao o bac %d%s" % (a, ("-%d" % b) if b else "+"), 0)
    s = max(seg, key=lambda s: s.get("n", 0))
    rong = s["hi"] - s["lo"]
    ly = "khoang he so phu hop voi lot lam tron o bac %d-%d: [%s, %s] (%d lenh), khai %s" % (s["tu"], s["den"], _gon_so(s["lo"]), _gon_so(s["hi"]), s.get("n", 0), _gon_so(m))
    if s["lo"] - 0.003 <= m <= s["hi"] + 0.003:
        dt = "cao" if rong <= 0.02 else "vua" if rong <= 0.12 else "thap"
        return (KHOP, "vua" if dt == "cao" else dt, ly, s.get("n", 0))
    return (MAU_THUAN, "vua" if s.get("n", 0) >= 30 and rong <= 0.12 else "thap", ly, s.get("n", 0))


@_bo_do
def _lot(bo: "_Bo"):
    bo.lop = "lot"
    lots = bo.so("lots")
    base = bo.so("multiplier")
    doi = bo.bat("usechangemultiplier")
    tiers = _lot_tang(bo)
    lot_do = _lot_dau_do(bo)
    q = float(bo.sl("lot_theo_bac").get("buoc_lot") or 0.01)
    if lots is not None:
        if lot_do is None:
            bo.ghi("lots", KHONG_DO_DUOC, khoi="lot_phang", do_tin="thap", ly_do="ho so khong co lot lenh dau")
        elif abs(lot_do - lots) < q / 2 + 1e-9:
            bo.ghi("lots", KHOP, khoi="lot_phang", do=lot_do, don_vi="lot", do_tin="cao", ly_do="lot lenh dau cua chuoi do duoc %s = khai" % _gon_so(lot_do),
                   nguon="lot_theo_bac.bang[r0]")
        else:
            bo.ghi("lots", MAU_THUAN, khoi="lot_phang", do=lot_do, don_vi="lot", do_tin="vua",
                   ly_do="lot lenh dau do duoc %s, khai %s (co the dung lot theo von hoac che do lot khac)" % (_gon_so(lot_do), _gon_so(lots)))
    if base is None or lots is None:
        return
    che_do_khoi = "lot_nhan_theo_bac" if (doi and tiers) else "lot_nhan"
    kt = _kiem_lot(bo, lots, base, bool(doi), tiers)
    if kt is not None:
        bo.kiem_lot = {"khop": kt["khop"], "tong": kt["tong"], "ty": round(kt["ty"], 4), "n_sau_nhat": kt["n_sau_nhat"],
                       "lech_mau": kt["lech_mau"], "doi_he_so": bool(doi),
                       "cong_thuc": "lot_n = lam_tron(%s x M(n)^(n-1), %s)" % (_gon_so(lots), _gon_so(q))}
    khoang = _khoang_lot(base, bool(doi), tiers)
    kq_k: dict = {}
    for a, b, m, ten_m, ten_moc in khoang:
        kq_k[ten_m] = _xu_khoang_lot(bo, kt, a, b, m, lots)
    # --- he so co so
    r = kq_k["multiplier"]
    ly = r[2]
    if abs(base - 1.0) < 1e-9 and r[0] == KHOP:
        ly = "he so 1,0 (lot phang): " + ly
    bo.ghi("multiplier", r[0], khoi=("lot_nhan" if abs(base - 1.0) > 1e-9 else "lot_phang") if che_do_khoi == "lot_nhan" else
           ("lot_nhan_theo_bac" if abs(base - 1.0) > 1e-9 else "lot_phang"),
           do=base if r[0] == KHOP else None, don_vi="he_so", do_tin=r[1], ly_do=ly,
           nguon="kiem tung lenh" if kt is not None else "lot_theo_bac.doan_he_so")
    # --- cong tat doi he so + cac tang
    if doi is None and tiers:
        bo.ghi("usechangemultiplier", KHONG_RO, khoi="lot_nhan_theo_bac", do_tin="thap", ly_do="khong co khoa UseChangeMultiplier trong bo .set")
    if doi is False:
        bo.ghi("usechangemultiplier", TAT, khoi="lot_nhan_theo_bac", do_tin="vua", ly_do="tat doi he so: moi lenh dung mot he so %s" % _gon_so(base))
        for _, _, tn, mn in tiers:
            bo.ghi(tn, TAT, khoi="lot_nhan_theo_bac", do_tin="vua", ly_do="cong UseChangeMultiplier tat: moc doi he so khong co hieu luc")
            bo.ghi(mn, TAT, khoi="lot_nhan_theo_bac", do_tin="vua", ly_do="cong UseChangeMultiplier tat: he so moi khong co hieu luc")
    elif doi is True and tiers:
        r1 = kq_k.get(tiers[0][3]) or kq_k.get("multiplier")
        sau_nhat = (kt["n_sau_nhat"] if kt is not None else bo.sl("lot_theo_bac").get("bac_sau_nhat") or 0)
        if sau_nhat <= tiers[0][0]:
            bo.ghi("usechangemultiplier", CHUA_GAP, khoi="lot_nhan_theo_bac", do_tin="thap",
                   ly_do="chuoi sau nhat %d lenh chua toi moc doi he so dau tien (%s)" % (sau_nhat, _gon_so(tiers[0][0])))
        elif r1 is not None:
            bo.ghi("usechangemultiplier", r1[0] if r1[0] in (KHOP, MAU_THUAN) else KHONG_RO, khoi="lot_nhan_theo_bac", do_tin=r1[1],
                   ly_do="doi he so theo bac: " + r1[2], nguon="kiem tung lenh" if kt is not None else "lot_theo_bac.doan_he_so")
    prev_m = base
    for k, (thr, m, tn, mn) in enumerate(tiers):
        if doi is False:
            prev_m = m
            continue
        r = kq_k.get(mn)
        if r is not None and doi is True:
            bo.ghi(mn, r[0], khoi="lot_nhan_theo_bac", do=m if r[0] == KHOP else None, don_vi="he_so", do_tin=r[1], ly_do=r[2],
                   nguon="kiem tung lenh" if kt is not None else "lot_theo_bac.doan_he_so")
            if abs(m - prev_m) < 1e-9:
                bo.ghi(tn, KHONG_DO_DUOC, khoi="lot_nhan_theo_bac", do_tin="vua",
                       ly_do="he so hai ben moc bang nhau (%s): doi moc khong de lai dau vet trong lot" % _gon_so(m))
            else:
                bo.ghi(tn, r[0], khoi="lot_nhan_theo_bac", do=float(thr + 1) if r[0] == KHOP else None, don_vi="lenh", do_tin=r[1],
                       ly_do="moc doi he so %s -> %s (lenh dau cua tang la lenh thu %d): %s" % (_gon_so(prev_m), _gon_so(m), thr + 1, r[2]),
                       nguon="kiem tung lenh" if kt is not None else "lot_theo_bac.doan_he_so")
        prev_m = m
    # --- cong them lot moi lenh
    plus = bo.so("plus")
    if plus is not None:
        if abs(plus) < 1e-12:
            bo.ghi("plus", TAT, khoi="lot_cong", do_tin="vua", ly_do="khai 0: khong cong them lot moi lenh")
        else:
            tong_ok = kt is not None and kt["ty"] >= 0.99
            kl = bo.kl("lot_cong")
            if tong_ok or kl == "khong":
                bo.ghi("plus", MAU_THUAN, khoi="lot_cong", do=0.0, don_vi="lot", do_tin="vua" if tong_ok else "thap",
                       ly_do="tac gia khai cong them %s lot moi lenh nhung lot do duoc KHONG cong them%s (co the chi bat o che do CoeffMode khac)" % (
                           _gon_so(plus), (" - cong thuc khong cong khop %d/%d lenh" % (kt["khop"], kt["tong"])) if kt is not None else ""))
            elif kl == "co":
                bo.ghi("plus", KHOP, khoi="lot_cong", do_tin=bo.dt("lot_cong"), ly_do="ho so thay lot cong them theo bac")
            else:
                bo.ghi("plus", KHONG_RO, khoi="lot_cong", do_tin="thap", ly_do="khong du de ket luan lot co cong them hay khong")


# ---------------------------------------------------------------------------------------------------------------- TP / thoat
def _khoi_cua_ts(bo: "_Bo", ten, mac_dinh):
    e = (bo.hs.get("tham_so") or {}).get(ten) or {}
    return e.get("khoi") or mac_dinh


def _tp_chuoi(bo: "_Bo"):
    """[(ten tham so, gia tri)] cac muc TP cua chuoi >= 2 lenh do duoc (tp_pip_chuoi_2-4, 5-9, 10+...), khong gom muc chuoi 1 lenh."""
    out = []
    for k, e in (bo.hs.get("tham_so") or {}).items():
        if k.startswith("tp_pip_chuoi_") and k != "tp_pip_chuoi_1" and e.get("gia_tri") is not None:
            out.append((k, float(e["gia_tri"])))
    return sorted(out)


@_bo_do
def _tp(bo: "_Bo"):
    bo.lop = "thoat"
    f = bo.f
    tp_don = bo.ts("tp_pip")
    ten_tp_don = "tp_pip"
    if tp_don is None:
        tp_don, ten_tp_don = bo.ts("tp_pip_chuoi_1"), "tp_pip_chuoi_1"
    chuoi = _tp_chuoi(bo)
    # --- TP cua lenh don / chuoi 1 lenh
    x = bo.so("tp")
    if x is not None:
        khoi = _khoi_cua_ts(bo, ten_tp_don, "tp_tung_lenh")
        if x == 0:
            bo.ghi("tp", TAT if tp_don is None else MAU_THUAN, khoi=khoi, do_tin="vua",
                   ly_do="khai 0 = khong dat TP co dinh" + ("" if tp_don is None else "; nhung lich su co lenh dong o muc TP %s pip" % _gon_so(tp_don)))
        elif tp_don is None:
            bo.ghi("tp", KHONG_DO_DUOC, khoi=khoi, do_tin="thap", ly_do="khong thay lenh don / chuoi 1 lenh nao dong o muc TP co dinh")
        elif _gan(tp_don, x * f, 0.4, 0.03):
            bo.ghi("tp", KHOP, khoi=khoi, do=tp_don, don_vi="pip", do_tin=bo.dt(khoi) if bo.dt(khoi) in DO_TIN else "vua",
                   ly_do="bien chot loi do duoc %s pip, khai %s pip (lech %+.2f pip = khoang 1 tick: lenh dong boi EA dong CHAM mot tick)" % (
                       _gon_so(tp_don), _gon_so(x * f), tp_don - x * f), nguon=ten_tp_don)
        else:
            bo.ghi("tp", MAU_THUAN, khoi=khoi, do=tp_don, don_vi="pip", do_tin="vua",
                   ly_do="khai TP %s pip nhung lenh dong o %s pip (kiem he so don vi %s)" % (_gon_so(x * f), _gon_so(tp_don), _gon_so(f)), nguon=ten_tp_don)
    # --- TP cua chuoi nhieu lenh (tinh tu gia trung binh)
    x = bo.so("tpdca")
    if x is not None:
        khoi = "tp_chuoi_tu_gia_tb"
        if x == 0:
            bo.ghi("tpdca", TAT if not chuoi else MAU_THUAN, khoi=khoi, do_tin="vua", ly_do="khai 0 = khong dat TP chuoi DCA")
        elif not chuoi:
            bo.ghi("tpdca", CHUA_GAP, khoi=khoi, do_tin="thap",
                   ly_do="khong co chuoi >= 2 lenh nao dong o muc TP co dinh (chuoi dai deu dong bang co che khac: khoa loi / EA)")
        else:
            khop = [(k, v) for k, v in chuoi if _gan(v, x * f, 0.4, 0.03)]
            if len(khop) == len(chuoi):
                bo.ghi("tpdca", KHOP, khoi=khoi, do=float(np.median([v for _, v in chuoi])), don_vi="pip", do_tin=bo.dt(khoi),
                       ly_do="moi nhom do sau (%s) dong o %s pip, khai %s pip" % (", ".join(k.replace("tp_pip_chuoi_", "") for k, _ in chuoi),
                                                                                    "/".join(_gon_so(v) for _, v in chuoi), _gon_so(x * f)),
                       nguon="tp_pip_chuoi_*")
            elif not khop:
                bo.ghi("tpdca", MAU_THUAN, khoi=khoi, do=float(np.median([v for _, v in chuoi])), don_vi="pip", do_tin="vua",
                       ly_do="khai TP chuoi %s pip nhung chuoi nhieu lenh dong o %s pip" % (_gon_so(x * f), "/".join(_gon_so(v) for _, v in chuoi)),
                       nguon="tp_pip_chuoi_*")
            else:
                bo.ghi("tpdca", KHONG_RO, khoi=khoi, do_tin="thap",
                       ly_do="chi %d / %d nhom do sau dong o muc khai %s pip" % (len(khop), len(chuoi), _gon_so(x * f)))
    # --- TP don le (SingleTP): 0 = khong dung
    x = bo.so("singletp")
    if x is not None:
        if x == 0:
            bo.ghi("singletp", TAT, khoi="tp_tung_lenh", do_tin="thap", ly_do="khai 0 (thuong = khong dung TP rieng cho lenh don)")
        elif tp_don is not None and _gan(tp_don, x * f, 0.4, 0.03):
            bo.ghi("singletp", KHOP, khoi=_khoi_cua_ts(bo, ten_tp_don, "tp_tung_lenh"), do=tp_don, don_vi="pip", do_tin="thap",
                   ly_do="bien chot loi lenh don %s pip = khai (nhung InpTP cung co the giai thich - khong tach duoc)" % _gon_so(tp_don))
        else:
            bo.ghi("singletp", KHONG_RO, khoi="tp_tung_lenh", do_tin="thap", ly_do="khong doi chieu duoc voi muc TP lenh don do duoc")
    # --- doi TP khi chuoi lo (nhom ChangeTP)
    cong = bo.bat("usechangetpdca")
    kl, dt = bo.kl("doi_tp_khi_lo"), bo.dt("doi_tp_khi_lo")
    phu_thuoc = [n for n in ("tpdcachange", "moneyloss2changetp", "perloss2changetp") if n in bo.v]
    if cong is False:
        bo.ghi("usechangetpdca", TAT if kl != "co" else MAU_THUAN, khoi="doi_tp_khi_lo", do_tin="vua",
               ly_do="khai tat doi TP khi lo" + ("; nhung lich su thay TP doi theo muc lo" if kl == "co" else ""))
        for n in phu_thuoc:
            bo.ghi(n, TAT, khoi="doi_tp_khi_lo", do_tin="vua", ly_do="cong UseChangeTPDCA tat: tham so nay khong co hieu luc")
    elif cong is True:
        if kl == "co":
            bo.ghi("usechangetpdca", KHOP, khoi="doi_tp_khi_lo", do_tin=dt, ly_do="lich su thay TP chuoi doi khi chuoi lo")
        elif kl == "khong" and dt != "thap":
            bo.ghi("usechangetpdca", MAU_THUAN, khoi="doi_tp_khi_lo", do_tin="vua" if dt == "cao" else "thap",
                   ly_do="khai bat doi TP khi lo nhung TP chuoi KHONG doi theo muc lo tren lich su co chuoi lo")
        else:
            bo.ghi("usechangetpdca", KHONG_RO, khoi="doi_tp_khi_lo", do_tin="thap", ly_do="khong du chuoi lo de biet TP co doi hay khong")
        for n in phu_thuoc:
            bo.ghi(n, KHONG_DO_DUOC, khoi="doi_tp_khi_lo", do_tin="thap", ly_do="gia tri rieng le cua nhom doi TP khong tach duoc tu lich su lenh")


# ---------------------------------------------------------------------------------------------------------------- trailing
@_bo_do
def _trailing(bo: "_Bo"):
    bo.lop = "thoat"
    f = bo.f
    khoi = "trailing_stop_chuoi"
    kl, dt = bo.kl(khoi), bo.dt(khoi)
    bat = bo.bat("usetrailing")
    khoa = bo.ts("trailing_khoa_dau_pip")
    ten_khoa = "trailing_khoa_dau_pip"
    if khoa is None:
        khoa, ten_khoa = bo.ts("khoa_loi_pip"), "khoa_loi_pip"
    buoc = bo.ts("trailing_buoc_pip")
    if bat is True:
        if kl == "co":
            bo.ghi("usetrailing", KHOP, khoi=khoi, do_tin=dt, ly_do="chuoi dong theo khoa loi truot (trailing) o muc co dinh")
        elif kl == "khong_ro":
            bo.ghi("usetrailing", KHONG_RO, khoi=khoi, do_tin="thap", ly_do="co cum dong gan muc khoa loi nhung khong chac day la trailing")
        elif kl == "khong" and dt != "thap":
            bo.ghi("usetrailing", MAU_THUAN, khoi=khoi, do_tin="vua" if dt == "cao" else "thap",
                   ly_do="khai bat trailing nhung khong thay chuoi nao dong theo khoa loi truot")
        else:
            bo.ghi("usetrailing", KHONG_DO_DUOC, khoi=khoi, do_tin="thap", ly_do="lich su khong du de biet trailing co chay hay khong")
    elif bat is False:
        bo.ghi("usetrailing", MAU_THUAN if kl == "co" else TAT, khoi=khoi, do_tin="vua",
               ly_do="khai tat trailing" + ("; nhung lenh that dong theo khoa loi truot (co the do tham so khac)" if kl == "co" else ""))
    # khoang khoa dau (SL ban dau khi bat trailing)
    x = bo.so("initialsltrailing")
    if x is not None and "initialsltrailing" not in bo.hang:
        if bat is False:
            bo.ghi("initialsltrailing", TAT, khoi=khoi, do_tin="vua", ly_do="cong UseTrailing tat: khong co hieu luc")
        elif khoa is None:
            bo.ghi("initialsltrailing", KHONG_DO_DUOC, khoi=khoi, do_tin="thap", ly_do="lich su khong cho thay muc khoa loi cua chuoi")
        elif _gan(khoa, x * f, 0.5, 0.05):
            bo.ghi("initialsltrailing", KHOP, khoi=khoi, do=khoa, don_vi="pip", do_tin="thap" if kl == "khong_ro" else dt,
                   ly_do="muc khoa loi do duoc %s pip, khai %s pip%s" % (
                       _gon_so(khoa), _gon_so(x * f), " (khoi trailing chi o muc khong_ro: coi la gia thuyet)" if kl == "khong_ro" else ""), nguon=ten_khoa)
        else:
            bo.ghi("initialsltrailing", MAU_THUAN, khoi=khoi, do=khoa, don_vi="pip", do_tin="vua" if kl == "co" else "thap",
                   ly_do="khai khoa loi %s pip nhung chuoi dong o khoang %s pip" % (_gon_so(x * f), _gon_so(khoa)), nguon=ten_khoa)
    x = bo.so("trailingstep")
    if x is not None:
        if bat is False:
            bo.ghi("trailingstep", TAT, khoi=khoi, do_tin="vua", ly_do="cong UseTrailing tat: khong co hieu luc")
        elif buoc is None:
            bo.ghi("trailingstep", KHONG_DO_DUOC, khoi=khoi, do_tin="thap", ly_do="lich su khong cho do duoc buoc nhich cua khoa loi")
        elif _gan(buoc, x * f, 0.5, 0.05):
            bo.ghi("trailingstep", KHOP, khoi=khoi, do=buoc, don_vi="pip", do_tin=dt, ly_do="buoc nhich khoa loi do duoc %s pip, khai %s pip" % (
                _gon_so(buoc), _gon_so(x * f)), nguon="trailing_buoc_pip")
        else:
            bo.ghi("trailingstep", MAU_THUAN, khoi=khoi, do=buoc, don_vi="pip", do_tin="vua",
                   ly_do="khai buoc nhich %s pip nhung do duoc %s pip" % (_gon_so(x * f), _gon_so(buoc)), nguon="trailing_buoc_pip")
    x = bo.so("trailingstart")
    if x is not None:
        if bat is False:
            bo.ghi("trailingstart", TAT, khoi=khoi, do_tin="vua", ly_do="cong UseTrailing tat: khong co hieu luc")
        else:
            bo.ghi("trailingstart", KHONG_DO_DUOC, khoi=khoi, do_tin="vua",
                   ly_do="muc lai de BAT trailing khong de lai dau vet trong lenh da dong (chuoi dong o muc khoa >= khoa dau); can duong gia de thay")


# ---------------------------------------------------------------------------------------------------------------- doi ung (hedge)
_NHOM_HEDGE_PHU = ("perloss2hedging", "tphedging", "tpallwhenhedging", "hedgingzonemultiplier", "maxlotshedgingzone", "moneytpallhedgingzone",
                   "pipstpallhedgingzone", "zonehedgingpips", "newmoneytpallhz", "orders2enablemoneytpallhz")


@_bo_do
def _doi_ung(bo: "_Bo"):
    bo.lop = "doi_ung"
    khoi = "lenh_doi_ung_sau_n_lenh"
    kl, dt = bo.kl(khoi), bo.dt(khoi)
    bat = bo.bat("usehedging")
    zone = bo.bat("usehedgingzone")
    opp = bo.bat("useopenopp")
    sau_nhat = bo.sl("chuoi_sau").get("do_sau_lon_nhat")
    kich_hoat = bo.ts("so_lenh_kich_hoat")
    if kich_hoat is None:
        kich_hoat = bo.sl("doi_ung").get("bac_kich_hoat")
    ty_lot = bo.ts("ty_lot_so_voi_lenh_chu_moi")
    x = bo.so("orders2hedging")
    thr = (x + 1) if x is not None else None
    if bat is True:
        if kl == "co":
            bo.ghi("usehedging", KHOP, khoi=khoi, do_tin=dt, ly_do="lich su co lenh bao hiem (hedge) di kem chuoi")
        elif thr is not None and sau_nhat is not None and sau_nhat < thr:
            bo.ghi("usehedging", CHUA_GAP, khoi=khoi, do_tin="thap",
                   ly_do="hedge bat tu lenh %s nhung chuoi sau nhat chi %s lenh" % (_gon_so(thr), _gon_so(sau_nhat)))
        elif kl == "khong" and dt != "thap":
            bo.ghi("usehedging", MAU_THUAN, khoi=khoi, do_tin="vua" if dt == "cao" else "thap",
                   ly_do="khai bat hedge, chuoi sau toi %s lenh (> moc %s) ma KHONG thay lenh bao hiem nao" % (_gon_so(sau_nhat), _gon_so(thr)))
        else:
            bo.ghi("usehedging", KHONG_RO, khoi=khoi, do_tin="thap", ly_do="khong du de ket luan hedge co chay hay khong")
    elif bat is False:
        if kl == "co" and not zone and not opp:
            bo.ghi("usehedging", MAU_THUAN, khoi=khoi, do_tin="vua",
                   ly_do="khai tat moi cong bao hiem nhung lich su co lenh doi ung (kiem lai: day co dung la bo .set da chay?)")
        else:
            bo.ghi("usehedging", TAT, khoi=khoi, do_tin="vua" if kl != "co" else "thap",
                   ly_do="khai tat hedge" + ("" if kl != "co" else "; lenh doi ung do duoc co the do cong khac (zone / OpenOpp) bat"))
    # moc kich hoat
    if x is not None:
        if bat is False:
            bo.ghi("orders2hedging", TAT, khoi=khoi, do_tin="vua", ly_do="cong UseHedging tat: khong co hieu luc")
        elif kich_hoat is not None:
            lech = float(kich_hoat) - x
            ly = "lenh bao hiem dau tien xuat hien khi chuoi co %s lenh; khai Orders2Hedging = %s (lech %+g: EA bat hedge khi so lenh VUOT moc)" % (
                _gon_so(kich_hoat), _gon_so(x), lech)
            if lech in (0.0, 1.0):
                bo.ghi("orders2hedging", KHOP, khoi=khoi, do=float(kich_hoat), don_vi="lenh", do_tin=dt if kl == "co" else "thap", ly_do=ly,
                       nguon="doi_ung.bac_kich_hoat")
            else:
                bo.ghi("orders2hedging", MAU_THUAN, khoi=khoi, do=float(kich_hoat), don_vi="lenh", do_tin="vua" if dt == "cao" else "thap",
                       ly_do=ly, nguon="doi_ung.bac_kich_hoat")
        elif sau_nhat is not None and sau_nhat < thr:
            bo.ghi("orders2hedging", CHUA_GAP, khoi=khoi, do_tin="thap", ly_do="chuoi sau nhat %s lenh chua toi moc %s" % (_gon_so(sau_nhat), _gon_so(thr)))
        else:
            bo.ghi("orders2hedging", KHONG_DO_DUOC, khoi=khoi, do_tin="thap", ly_do="khong do duoc moc kich hoat hedge tu lich su")
    # lot bao hiem
    lot_dca = bo.bat("uselotsdca2hedging")
    if lot_dca is not None:
        if bat is False:
            bo.ghi("uselotsdca2hedging", TAT, khoi=khoi, do_tin="vua", ly_do="cong UseHedging tat: khong co hieu luc")
        elif ty_lot is None:
            bo.ghi("uselotsdca2hedging", KHONG_DO_DUOC, khoi=khoi, do_tin="thap", ly_do="khong co lenh bao hiem de do ty le lot")
        else:
            gan1 = abs(float(ty_lot) - 1.0) <= 0.05
            ly = "lot lenh bao hiem / lot lenh them moi nhat cua chuoi = %s" % _gon_so(ty_lot)
            if lot_dca:
                bo.ghi("uselotsdca2hedging", KHOP if gan1 else MAU_THUAN, khoi=khoi, do=float(ty_lot), don_vi="ty le", do_tin="vua" if kl == "co" else "thap",
                       ly_do=ly + ("" if gan1 else " (khai lay lot theo lenh DCA)"), nguon="doi_ung.ty_lot")
            else:
                bo.ghi("uselotsdca2hedging", KHONG_RO, khoi=khoi, do=float(ty_lot), don_vi="ty le", do_tin="thap",
                       ly_do=ly + "; khai tat nhung chua doi chieu duoc voi PerLotsHedging")
        if "perlotshedging" in bo.v:
            if lot_dca:
                bo.ghi("perlotshedging", BI_CHE, khoi=khoi, do_tin="vua", ly_do="UseLotsDCA2Hedging bat: lot bao hiem theo lenh DCA, bo qua phan tram lot")
            elif bat is False:
                bo.ghi("perlotshedging", TAT, khoi=khoi, do_tin="vua", ly_do="cong UseHedging tat: khong co hieu luc")
    # nhom con lai
    for n in _NHOM_HEDGE_PHU:
        if n not in bo.v or n in bo.hang:
            continue
        if bat is False and not zone and not opp:
            bo.ghi(n, TAT, khoi=khoi, do_tin="vua", ly_do="khong cong bao hiem nao bat: tham so khong co hieu luc")
        elif n in ("newmoneytpallhz", "orders2enablemoneytpallhz", "hedgingzonemultiplier", "maxlotshedgingzone", "moneytpallhedgingzone",
                   "pipstpallhedgingzone", "zonehedgingpips", "orders2hedgingzone") and zone is False:
            bo.ghi(n, TAT, khoi=khoi, do_tin="vua", ly_do="cong UseHedgingZone tat: khong co hieu luc")
        else:
            bo.ghi(n, KHONG_DO_DUOC, khoi=khoi, do_tin="thap",
                   ly_do="gia tri nay (nguong lo / ty le / TP khi co hedge) can duong gia hoac chi hien khi co du chuoi bao hiem; lich su co %s chuoi" % (
                       _gon_so(bo.sl("doi_ung").get("so_lenh_doi_ung") or 0)))
    if zone is False and "usehedgingzone" in bo.v:
        bo.ghi("usehedgingzone", TAT, khoi=khoi, do_tin="vua", ly_do="khai tat vung bao hiem")
        for n in bo.khac_het(r"(hedgingzone|hz$)"):
            bo.ghi(n, TAT, khoi=khoi, do_tin="vua", ly_do="cong UseHedgingZone tat: khong co hieu luc")
    if opp is False and "useopenopp" in bo.v:
        bo.ghi("useopenopp", TAT, khoi=khoi, do_tin="vua", ly_do="khai tat mo lenh doi chieu (OpenOpp)")
        for n in bo.khac_het(r"(openopp|lotsopp)"):
            bo.ghi(n, TAT, khoi=khoi, do_tin="vua", ly_do="cong UseOpenOpp tat: khong co hieu luc")
    if zone is True and "usehedgingzone" in bo.v:
        bo.ghi("usehedgingzone", KHONG_RO, khoi=khoi, do_tin="thap", ly_do="bat vung bao hiem: chua tach duoc voi hedge thuong trong lich su")
    if opp is True and "useopenopp" in bo.v:
        bo.ghi("useopenopp", KHONG_RO, khoi=khoi, do_tin="thap", ly_do="bat mo lenh doi chieu: chua tach duoc voi hedge thuong trong lich su")


# ---------------------------------------------------------------------------------------------------------------- tia lenh (sniper)
_NGUONG_SNIPER = ("orders2startsniper", "orders2startsniper2", "orders2startsniperpartial", "allorders2activeallsniper")


def _nhom_sniper(n: str) -> str:
    if "partial" in n or n.startswith("minperlots"):
        return "mot_phan"
    if "allsniper" in n or n.startswith(("allorders2active", "firstorders2all", "lastorders2all", "moneyprofitall", "useallprofit")) or n == "sniperall":
        return "tat_ca"
    return "day_du"


@_bo_do
def _sniper(bo: "_Bo"):
    bo.lop = "tia_lenh"
    thanh_vien = [n for n in bo.v if "sniper" in n or n.startswith(("allorders2active", "firstorders2all", "lastorders2all", "moneyprofitall", "useallprofit"))]
    if not thanh_vien:
        return
    chu = {"day_du": "usesniper", "mot_phan": next((m for m in ("usesniperpartial", "usepartialsniper") if m in bo.v), "usesniperpartial"),
           "tat_ca": next((m for m in ("useallsniper", "sniperall") if m in bo.v), "useallsniper")}
    gia_tri_chu = {g: bo.bat(m) if m in bo.v else None for g, m in chu.items()}
    kl_tia, dt_tia = bo.kl("tia_n_lenh_khi_chuoi_dai"), bo.dt("tia_n_lenh_khi_chuoi_dai")
    kl_all, dt_all = bo.kl("all_sniper"), bo.dt("all_sniper")
    dsk = bo.sl("thoat_tung_phan").get("do_sau_kiem_duoc_tia")
    if dsk is None:
        dsk = bo.sl("chuoi_sau").get("do_sau_lon_nhat")
    cuoi = {}
    # --- cac nguong (moc so lenh bat dau tia)
    for n in [n for n in thanh_vien if n in _NGUONG_SNIPER]:
        g = _nhom_sniper(n)
        x = bo.so(n)
        if x is None:
            continue
        khoi = "all_sniper" if g == "tat_ca" else "tia_n_lenh_khi_chuoi_dai"
        kl, dt = (kl_all, dt_all) if g == "tat_ca" else (kl_tia, dt_tia)
        if gia_tri_chu[g] is False:
            bo.ghi(n, TAT, khoi=khoi, do_tin="vua", ly_do="cong %s tat: khong co hieu luc" % bo.ten.get(chu[g], chu[g]))
            continue
        if dsk is not None and x > dsk:
            r = (CHUA_GAP, "thap", "tia bat dau tu lenh %s nhung lich su chi kiem duoc tia den do sau %s lenh (it chuoi dai de thu)" % (_gon_so(x), _gon_so(dsk)))
        elif kl == "co":
            r = (KHOP, dt, "lich su co chuoi dong tung phan (tia) tu do sau gan moc %s" % _gon_so(x))
        elif kl == "khong" and dt == "cao":
            r = (MAU_THUAN, "vua", "khai tia tu lenh %s (lich su co chuoi sau toi %s lenh) nhung khong thay lenh nao bi tia" % (_gon_so(x), _gon_so(dsk)))
        else:
            r = (KHONG_RO, "thap", "moc %s nam trong do sau kiem duoc (%s lenh) nhung chua ket luan duoc tia co chay hay khong" % (_gon_so(x), _gon_so(dsk)))
        bo.ghi(n, r[0], khoi=khoi, do_tin=r[1], ly_do=r[2], nguon="thoat_tung_phan.do_sau_kiem_duoc_tia")
        cuoi.setdefault(g, []).append(r[0])
    # --- cong tong cua tung nhom
    for g, m in chu.items():
        if m not in bo.v:
            continue
        khoi = "all_sniper" if g == "tat_ca" else "tia_n_lenh_khi_chuoi_dai"
        kl, dt = (kl_all, dt_all) if g == "tat_ca" else (kl_tia, dt_tia)
        v = gia_tri_chu[g]
        if v is False:
            nho = kl == "co" and not any(gia_tri_chu[h] for h in gia_tri_chu if h != g)
            bo.ghi(m, MAU_THUAN if nho else TAT, khoi=khoi, do_tin="vua",
                   ly_do="khai tat" + ("; nhung lich su co lenh tia (khong cong tia nao khac bat)" if nho else ""))
        elif v is True:
            ds = cuoi.get(g, [])
            if kl == "co":
                bo.ghi(m, KHOP, khoi=khoi, do_tin=dt, ly_do="lich su co lenh dong tung phan / tia lenh")
            elif ds and all(k == CHUA_GAP for k in ds):
                bo.ghi(m, CHUA_GAP, khoi=khoi, do_tin="thap", ly_do="cong bat nhung moc tia chua bao gio toi trong lich su")
            elif kl == "khong" and dt == "cao" and any(k == MAU_THUAN for k in ds):
                bo.ghi(m, MAU_THUAN, khoi=khoi, do_tin="vua", ly_do="khai bat tia, chuoi du dai ma khong co lenh nao bi tia")
            else:
                bo.ghi(m, KHONG_RO, khoi=khoi, do_tin="thap", ly_do="cong bat; lich su chua du de biet tia co chay hay khong")
    # --- thanh vien con lai
    for n in thanh_vien:
        if n in bo.hang or n == "stopsniperwhenhedging":
            continue
        g = _nhom_sniper(n)
        khoi = "all_sniper" if g == "tat_ca" else "tia_n_lenh_khi_chuoi_dai"
        kl = kl_all if g == "tat_ca" else kl_tia
        if gia_tri_chu[g] is False:
            bo.ghi(n, TAT, khoi=khoi, do_tin="vua", ly_do="cong %s tat: khong co hieu luc" % bo.ten.get(chu[g], chu[g]))
        elif gia_tri_chu[g] is True and kl != "co":
            bo.ghi(n, KHONG_DO_DUOC, khoi=khoi, do_tin="thap", ly_do="nhom tia chua thay hoat dong trong lich su nen khong do duoc tung tham so")
        elif gia_tri_chu[g] is True:
            bo.ghi(n, KHONG_RO, khoi=khoi, do_tin="thap", ly_do="co tia nhung gia tri rieng cua tham so nay chua tach duoc")
        else:
            bo.ghi(n, KHONG_RO, khoi=khoi, do_tin="thap", ly_do="khong co khoa cong cua nhom (UseSniper...) trong bo .set")
    # --- dung tia khi co hedge
    if "stopsniperwhenhedging" in bo.v:
        sn_on = any(gia_tri_chu[g] for g in gia_tri_chu)
        hedge_on = bo.bat("usehedging")
        if hedge_on is False or not sn_on:
            bo.ghi("stopsniperwhenhedging", TAT, khoi="tia_n_lenh_khi_chuoi_dai", do_tin="vua", ly_do="cong tia hoac cong hedge tat: khong co hieu luc")
        else:
            bo.ghi("stopsniperwhenhedging", KHONG_DO_DUOC, khoi="tia_n_lenh_khi_chuoi_dai", do_tin="thap",
                   ly_do="chi co tac dung khi vua co tia vua co hedge cung luc; lich su chua co chuoi nhu vay du nhieu")


# ---------------------------------------------------------------------------------------------------------------- gio giao dich
def _cua_so_gio(bo: "_Bo"):
    """[(phut_bat_dau, phut_ket_thuc)] cac cua so bat (UseTimeK = true) co gio doc duoc."""
    out = []
    for k in range(1, 9):
        s, e = bo.v.get("starttime%d" % k), bo.v.get("endtime%d" % k)
        if s is None or e is None:
            continue
        bat = bo.bat("usetime%d" % k)
        if bat is False:
            continue
        a, b = _gio(s), _gio(e)
        if a is not None and b is not None:
            out.append((a, b))
    return out


def _trong_gio(phut: float, cua_so) -> bool:
    for a, b in cua_so:
        if a == b:
            return True
        if a < b and a <= phut < b:
            return True
        if a > b and (phut >= a or phut < b):
            return True
    return False


@_bo_do
def _loc_gio(bo: "_Bo"):
    bo.lop = "gio"
    khoi = "loc_gio_giao_dich"
    kl, dt = bo.kl(khoi), bo.dt(khoi)
    bat = bo.bat("usetradingtime")
    ten_ks = [n for n in bo.v if re.fullmatch(r"(usetime|starttime|endtime)\d+", n)]
    if bat is False:
        if "usetradingtime" in bo.v:
            bo.ghi("usetradingtime", MAU_THUAN if kl == "co" else TAT, khoi=khoi, do_tin="vua" if kl != "co" else "thap",
                   ly_do="khai tat loc gio" + ("; nhung lich su cho thay chuoi chi mo trong mot so gio" if kl == "co" else ": khong co gio nao bi cam"))
        for n in ten_ks:
            bo.ghi(n, TAT, khoi=khoi, do_tin="vua", ly_do="cong UseTradingTime tat: cua so gio khong co hieu luc")
        if "dcaouttime" in bo.v:
            bo.ghi("dcaouttime", TAT, khoi=khoi, do_tin="thap", ly_do="suy tu ten: tuy chon cho phep DCA ngoai gio; cong loc gio tat nen khong co hieu luc")
        return
    cs = _cua_so_gio(bo)
    chuoi = bo.sl("gio_ngay").get("chuoi_theo_30_phut")
    hieu_luc = bat is True or (bat is None and bool(cs))      # khong co khoa cong: cac cua so UseTimeK tu la cong tat
    if hieu_luc and cs and chuoi and len(chuoi) == 48:
        tong = float(sum(chuoi))
        ngoai = float(sum(n for k, n in enumerate(chuoi) if not _trong_gio(30 * k + 15, cs)))
        trong = tong - ngoai
        ty = ngoai / tong if tong else 0.0
        ly = "%d / %d chuoi bat dau NGOAI cac cua so gio da khai (%s)" % (int(ngoai), int(tong), ", ".join("%02d:%02d-%02d:%02d" % (a // 60, a % 60, b // 60, b % 60) for a, b in cs))
        if ty <= 0.01 and trong >= 30:
            r = (KHOP, "cao" if tong >= 100 else "vua")
        elif ty > 0.05:
            r = (MAU_THUAN, "cao" if tong >= 100 else "vua")
        else:
            r = (KHONG_RO, "thap")
        bo.ghi("usetradingtime", r[0], khoi=khoi, do=float(ty), don_vi="ty le", do_tin=r[1], ly_do=ly, nguon="gio_ngay.chuoi_theo_30_phut")
        for n in ten_ks:
            bo.ghi(n, r[0], khoi=khoi, do_tin=r[1], ly_do="cung ket qua cua nhom gio: " + ly, nguon="gio_ngay.chuoi_theo_30_phut")
    elif hieu_luc:
        bo.ghi("usetradingtime", KHONG_DO_DUOC, khoi=khoi, do_tin="thap", ly_do="khong doc duoc cua so gio nao hoac ho so khong co phan bo gio")
        for n in ten_ks:
            bo.ghi(n, KHONG_DO_DUOC, khoi=khoi, do_tin="thap", ly_do="khong doc duoc cua so gio hoac ho so khong co phan bo gio")
    if "dcaouttime" in bo.v and "dcaouttime" not in bo.hang:
        bo.ghi("dcaouttime", KHONG_DO_DUOC, khoi=khoi, do_tin="thap", ly_do="chi co nghia khi loc gio bat; chua do duoc rieng")


# ---------------------------------------------------------------------------------------------------------------- tre
def _gap_sau_chuoi(bo: "_Bo"):
    """{'lai': mang, 'lo': mang} khoang (giay) tu luc chuoi truoc dong den luc chuoi moi CUNG CHIEU mo, tach theo chuoi truoc LAI / LO.
    Dung lich su da bo hedge (giong cac phep do cua ho so). None neu khong co bang lenh."""
    if bo.c is None:
        return None
    from nhan import ho_so_bot as HB
    ro = HB.bo_hedge(bo.c).ro
    lai, lo = [], []
    for d in (1, -1):
        r = ro[ro["chieu"] == d].sort_values("mo")
        if len(r) < 2:
            continue
        mo = r["mo"].to_numpy("datetime64[ns]")
        dong = r["dong"].to_numpy("datetime64[ns]")
        tien = r["tien"].to_numpy(float)
        for i in range(1, len(r)):
            if np.isnat(dong[i - 1]) or np.isnat(mo[i]) or not np.isfinite(tien[i - 1]):
                continue
            g = float((mo[i] - dong[i - 1]) / np.timedelta64(1, "s"))
            (lai if tien[i - 1] > 0 else lo).append(g)
    return {"lai": np.asarray(lai, float), "lo": np.asarray(lo, float)}


def _tre_sau_dong(bo: "_Bo"):
    x = bo.so("minutedelayafterclose")
    if x is None:
        return
    khoi = "loc_gio_giao_dich"
    if x == 0:
        bo.ghi("minutedelayafterclose", TAT, khoi=khoi, do_tin="vua", ly_do="khai 0: khong tre sau khi dong chuoi")
        return
    sec = x * 60.0
    tick = float((bo.hs.get("mau") or {}).get("tick_s") or 1.0)
    ngay = sec - 2 * max(tick, 1.0)           # luoi tick cua tester co the lam khoang cach ngan di ~2 tick
    vl = bo.sl("vao_lai")
    n = int(vl.get("so_lan_vao_lai") or 0)
    if n < 20:
        bo.ghi("minutedelayafterclose", KHONG_DO_DUOC, khoi=khoi, do_tin="thap", ly_do="chi %d lan vao lai (< 20): khong du de do khoang cach" % n)
        return
    g = _gap_sau_chuoi(bo)
    if g is None:
        med, mn = vl.get("gap_s_trung_vi"), vl.get("gap_s_min")
        ly = "khoang tu luc chuoi cu dong den chuoi moi cung chieu mo: ngan nhat %s giay, trung vi %s giay (%d lan); khai tre %s phut = %s giay" % (
            _gon_so(mn), _gon_so(med), n, _gon_so(x), _gon_so(sec))
        if mn is not None and mn >= ngay:
            bo.ghi("minutedelayafterclose", KHOP, khoi=khoi, do=float(mn), don_vi="giay", do_tin="vua", ly_do=ly, nguon="vao_lai.gap_s_min")
        elif med is not None and med < sec:
            bo.ghi("minutedelayafterclose", MAU_THUAN, khoi=khoi, do=float(med), don_vi="giay", do_tin="thap",
                   ly_do=ly + "; chua tach theo chuoi lo / lai (tre co the chi ap dung sau chuoi lo) - can bang lenh de ket luan chac hon", nguon="vao_lai.gap_s_trung_vi")
        else:
            bo.ghi("minutedelayafterclose", KHONG_RO, khoi=khoi, do_tin="thap", ly_do=ly, nguon="vao_lai.gap_s_min")
        return
    lai, lo = g["lai"], g["lo"]
    tat_ca = np.concatenate([lai, lo])
    vi_pham = float((tat_ca < ngay).mean()) if len(tat_ca) else 0.0
    ly = "%d lan vao lai: %.0f%% ngan hon %s phut (ngan nhat %s giay, trung vi %s giay)" % (
        len(tat_ca), 100 * vi_pham, _gon_so(x), _gon_so(float(tat_ca.min())), _gon_so(float(np.median(tat_ca))))
    bo.ghi_chu["tre_sau_dong"] = {"n_lai": int(len(lai)), "n_lo": int(len(lo)), "vi_pham_chung": round(vi_pham, 4),
                                  "vi_pham_sau_lo": round(float((lo < ngay).mean()), 4) if len(lo) else None,
                                  "vi_pham_sau_lai": round(float((lai < ngay).mean()), 4) if len(lai) else None}
    if vi_pham <= 0.02:
        bo.ghi("minutedelayafterclose", KHOP, khoi=khoi, do=float(np.median(tat_ca)), don_vi="giay", do_tin="cao" if len(tat_ca) >= 100 else "vua",
               ly_do=ly + ": moi lan vao lai deu cach chuoi cu dong >= tre khai bao", nguon="ro.dong -> ro.mo (bang lenh)")
        return
    if len(lo) >= 8:
        vp_lo = float((lo < ngay).mean())
        vp_lai = float((lai < ngay).mean()) if len(lai) >= 8 else None
        ly += "; sau chuoi LO (%d lan): %.0f%% ngan hon" % (len(lo), 100 * vp_lo)
        if vp_lo <= 0.05 and vp_lai is not None and vp_lai > 0.5:
            bo.ghi("minutedelayafterclose", KHOP, khoi=khoi, do=float(np.median(lo)), don_vi="giay", do_tin="vua",
                   ly_do=ly + " - tre CHI duoc thuc thi sau chuoi lo (sau chuoi lai chuoi moi mo som hon: khai bao 'sau khi dong' hep hon ten goi)",
                   nguon="ro.dong -> ro.mo (bang lenh)")
        elif vp_lo > 0.5:
            bo.ghi("minutedelayafterclose", MAU_THUAN, khoi=khoi, do=float(np.median(tat_ca)), don_vi="giay", do_tin="cao" if len(tat_ca) >= 100 else "vua",
                   ly_do=ly + " - tre khong thuc thi ke ca sau chuoi lo", nguon="ro.dong -> ro.mo (bang lenh)")
        else:
            bo.ghi("minutedelayafterclose", KHONG_RO, khoi=khoi, do_tin="thap", ly_do=ly, nguon="ro.dong -> ro.mo (bang lenh)")
        return
    if vi_pham > 0.5:
        bo.ghi("minutedelayafterclose", MAU_THUAN, khoi=khoi, do=float(np.median(tat_ca)), don_vi="giay", do_tin="thap" if len(lo) < 8 else "vua",
               ly_do=ly + "; chi co %d chuoi lo nen khong thu duoc cach hieu 'tre chi sau chuoi lo' (neu dung cach hieu do thi khong the bac bo)" % len(lo),
               nguon="ro.dong -> ro.mo (bang lenh)")
    else:
        bo.ghi("minutedelayafterclose", KHONG_RO, khoi=khoi, do_tin="thap", ly_do=ly)


def _tre_ngay_moi(bo: "_Bo"):
    x = bo.so("minutedelaynewday")
    if x is None:
        return
    khoi = "loc_gio_giao_dich"
    if x == 0:
        bo.ghi("minutedelaynewday", TAT, khoi=khoi, do_tin="vua", ly_do="khai 0: khong tre dau ngay")
        return
    gn = bo.sl("gio_ngay")
    ch = gn.get("chuoi_theo_30_phut")
    if not ch or len(ch) != 48:
        bo.ghi("minutedelaynewday", KHONG_DO_DUOC, khoi=khoi, do_tin="thap", ly_do="ho so khong co phan bo chuoi theo gio trong ngay")
        return
    m = int(math.ceil(x / 30.0))
    tong = float(sum(ch))
    n_00 = float(sum(ch[:m]))
    mo_lai = gn.get("gio_mo_cua_lai")
    mo_lai = 0 if mo_lai is None else int(mo_lai)
    n_mo = float(sum(ch[(2 * mo_lai + k) % 48] for k in range(m)))
    n_sau = float(sum(ch[(2 * mo_lai + m + k) % 48] for k in range(m)))
    cau = "cua so tre %d phut = %d o 30 phut dau ngay may chu (00:00-%02d:%02d)" % (x, m, (m * 30) // 60, (m * 30) % 60)
    if n_00 >= max(3.0, 0.01 * tong):
        ty = n_00 / tong if tong else 0.0
        bo.ghi("minutedelaynewday", MAU_THUAN, khoi=khoi, do=float(ty), don_vi="ty le", do_tin="cao" if ty >= 0.05 else "vua",
               ly_do="%s: van co %d / %d chuoi bat dau trong cua so (%.1f%%), du tinh tre tu 00:00 - cach doc yeu nhat; dau ngay o day: nghi san tu 00:00 den %02d:00" % (
                   cau, int(n_00), int(tong), 100 * ty, mo_lai) + "; tre co the chi ap dung sau mot dieu kien khac chua gap", nguon="gio_ngay.chuoi_theo_30_phut")
    elif n_mo > 0:
        bo.ghi("minutedelaynewday", KHONG_RO, khoi=khoi, do_tin="thap",
               ly_do="%s: khong chuoi nao truoc %02d:00 (san dong) nhung %d chuoi bat dau trong %d o ke tu luc mo cua lai - mau thuan neu tre tinh tu luc mo cua, "
                     "khong mau thuan neu tinh tu 00:00" % (cau, mo_lai, int(n_mo), m), nguon="gio_ngay.chuoi_theo_30_phut")
    else:
        dt = "vua" if n_sau >= 30 else "thap"
        bo.ghi("minutedelaynewday", KHOP, khoi=khoi, do_tin=dt,
               ly_do="%s: khong chuoi nao bat dau trong cua so tre (ke ca tinh tu luc mo cua lai); %d chuoi ngay sau cua so" % (cau, int(n_sau)),
               nguon="gio_ngay.chuoi_theo_30_phut")


@_bo_do
def _tre(bo: "_Bo"):
    bo.lop = "tre"
    _tre_ngay_moi(bo)
    _tre_sau_dong(bo)
    mau_tick = float((bo.hs.get("mau") or {}).get("tick_s") or 0.0)
    for n, ten in (("delayorder", "tre giua hai lenh"), ("delayaftersltp", "tre sau khi dong theo SL / TP"),
                   ("delaytimebll", "tre cua che do BLL")):
        x = bo.so(n)
        if x is None or n in bo.hang:
            continue
        if x == 0:
            bo.ghi(n, TAT, khoi="loc_gio_giao_dich", do_tin="vua", ly_do="khai 0: khong co %s" % ten)
        elif n == "delayorder" and mau_tick >= 5:
            bo.ghi(n, KHONG_DO_DUOC, khoi="loc_gio_giao_dich", do_tin="vua",
                   ly_do="khai %s giay nhung bao cao tester dat lenh tren luoi %s giay: khoang vai giay khong do duoc" % (_gon_so(x), _gon_so(mau_tick)))
        else:
            bo.ghi(n, KHONG_DO_DUOC, khoi="loc_gio_giao_dich", do_tin="thap", ly_do="%s: chua co phep do rieng" % ten)
    # che do BLL (can bang lot?) - suy tu ten: cong UseBalanceLot
    bll = [n for n in bo.v if n in ("addbllmode", "addlotsbll", "delaytimebll", "difflots2disablebll", "difflots2enablebll", "usebalancelot")]
    if bll:
        v = bo.bat("usebalancelot")
        if v is False:
            for n in bll:
                bo.ghi(n, TAT, khoi="", do_tin="thap" if n != "usebalancelot" else "vua",
                       ly_do="khai tat UseBalanceLot" if n == "usebalancelot" else "suy tu ten: nhom BLL phu thuoc UseBalanceLot (dang tat)")
        else:
            for n in bll:
                bo.ghi(n, KHONG_DO_DUOC if n != "usebalancelot" else KHONG_RO, khoi="", do_tin="thap",
                       ly_do="che do BLL chua duoc phan tich (chua co khoi co che tuong ung trong danh muc)")


# ---------------------------------------------------------------------------------------------------------------- vao lenh
_RX_EMA = r"^(ema\d*|tfemafilter|maxdist\w*ema|emafilter\w*|emaperiod\w*)$"
_RX_MACD = r"^(tfmacdfilter|fastemamacd|slowemamacd|smamacd|appliedpricemacd|macd\w*)$"


@_bo_do
def _vao(bo: "_Bo"):
    bo.lop = "vao"
    khoi = "vao_chi_bao_ngoai"
    # --- khung tin hieu: chuoi chi bat dau o dau nen cua khung do?
    if "tfsignal" in bo.v:
        tf = tf_phut(bo.v["tfsignal"])
        km = bo.ts("khung_tin_hieu_phut")
        ev = (((bo.sl("dieu_kien_vao").get("khung_vao") or {}).get("khung")) or {}).get(str(tf)) if tf else None
        if tf is None or tf == 0:
            bo.ghi("tfsignal", KHONG_RO, khoi=khoi, do_tin="thap",
                   ly_do="gia tri %s = khung cua bieu do (hoac gia tri la): khong biet khung that cua lan chay" % bo.v["tfsignal"])
        elif km is None:
            bo.ghi("tfsignal", KHONG_DO_DUOC, khoi=khoi, do_tin="thap", ly_do="khai khung tin hieu %d phut; ho so khong do duoc nhip mo chuoi" % tf)
        elif abs(float(km) - tf) < 1e-9:
            chac = bool(ev and ev.get("do_duoc") and ev.get("khop") and (ev.get("ty_ngau_nhien") is not None and ev["ty_ngau_nhien"] <= 0.35))
            ly = "chuoi chi bat dau o dau nen %d phut (100%% so chuoi)" % tf
            if ev and ev.get("ty_ngau_nhien") is not None:
                ly += "; ngau nhien se trung %.0f%%" % (100 * ev["ty_ngau_nhien"])
            bo.ghi("tfsignal", KHOP, khoi=khoi, do=float(km), don_vi="phut", do_tin="cao" if chac else "vua", ly_do=ly, nguon="khung_tin_hieu_phut")
        elif float(km) > tf:
            bo.ghi("tfsignal", KHONG_RO, khoi=khoi, do=float(km), don_vi="phut", do_tin="thap",
                   ly_do="chuoi bat dau theo nhip %s phut, lon hon khung tin hieu khai %d phut: tin hieu co the con thua hon dieu kien khac" % (_gon_so(km), tf))
        else:
            bo.ghi("tfsignal", MAU_THUAN, khoi=khoi, do=float(km), don_vi="phut", do_tin="vua",
                   ly_do="khai khung tin hieu %d phut nhung chuoi bat dau o nhip %s phut (nho hon) - khong the do tin hieu cua khung %d phut" % (tf, _gon_so(km), tf),
                   nguon="khung_tin_hieu_phut")
    # --- bo loc ngoai (EMA / MACD): khai tat thi khong kiem duoc nguoc lai
    for chu, rx, ten in (("useemafilter", _RX_EMA, "loc EMA"), ("usemacdfilter", _RX_MACD, "loc MACD")):
        if chu not in bo.v:
            continue
        v = bo.bat(chu)
        phu = [n for n in bo.v if n != chu and re.search(rx, n)]
        if v is False:
            bo.ghi(chu, TAT, khoi="vao_theo_ma", do_tin="thap", ly_do="khai tat %s (khong the kiem nguoc lai: bo loc chi chan lenh, khong de lai dau vet)" % ten)
            for n in phu:
                bo.ghi(n, TAT, khoi="vao_theo_ma", do_tin="thap", ly_do="cong %s tat: tham so khong co hieu luc" % ten)
        elif v is True:
            bo.ghi(chu, KHONG_DO_DUOC, khoi="vao_theo_ma", do_tin="thap", ly_do="%s can duong gia de kiem; lich su lenh khong cho thay" % ten)
            for n in phu:
                bo.ghi(n, KHONG_DO_DUOC, khoi="vao_theo_ma", do_tin="thap", ly_do="gia tri rieng cua %s can duong gia de kiem" % ten)
    # --- chi bao SuperTrend (ten 'dist' de nham voi khoang cach luoi)
    for n in [n for n in bo.v if n in ("periodsindist", "multiplierindist")]:
        bo.ghi(n, KHONG_DO_DUOC, khoi=khoi, do_tin="thap",
               ly_do="tham so chi bao SuperTrend cua tin hieu vao lenh (khong phai khoang cach luoi); can duong gia de kiem")
    # --- che do chi bao
    if "indimode" in bo.v:
        bo.ghi("indimode", KHONG_DO_DUOC, khoi=khoi, do_tin="vua",
               ly_do="che do chi bao vao lenh (%s): khong the biet chi bao nao dang chay neu khong co duong gia cung thoi gian" % bo.v["indimode"])
    # --- huong lenh
    if "typebuysell" in bo.v:
        ty = bo.sl("huong").get("ty_mua")
        ly = "khai TypeBuySell = %s; lich su: mua %.0f%% / ban %.0f%% (hai bo cung khai 0 co the cho hai hanh vi khac nhau: tham so nay khong quyet dinh mot minh)" % (
            bo.v["typebuysell"], 100 * (ty or 0), 100 * (1 - (ty or 0))) if ty is not None else \
            "khai TypeBuySell = %s; ho so khong cho ty le mua / ban" % bo.v["typebuysell"]
        bo.ghi("typebuysell", KHONG_RO, khoi="mot_chieu", do=float(ty) if ty is not None else None, don_vi="ty le mua", do_tin="thap", ly_do=ly,
               nguon="huong.ty_mua")


# ---------------------------------------------------------------------------------------------------------------- tran lenh / lot / loc
def _sau_theo_chieu(bo: "_Bo"):
    """{1: sau nhat chieu mua, -1: sau nhat chieu ban}; thieu bang lenh thi khong co khoa chieu nao ({0: do sau chung})."""
    if bo.c is not None:
        try:
            from nhan import ho_so_bot as HB
            ro = HB.bo_hedge(bo.c).ro
            col = "n_mo_max" if "n_mo_max" in ro.columns else "so_lenh"
            return {int(d): int(ro.loc[ro["chieu"] == d, col].max()) for d in (1, -1) if (ro["chieu"] == d).any()}
        except Exception:
            pass
    s = bo.sl("chuoi_sau").get("do_sau_lon_nhat")
    return {0: int(s)} if s is not None else {}


def _dinh_lot_goc(bo: "_Bo"):
    """Dinh tong lot dang mo tinh tren bang lenh GOC (gom lenh bao hiem, dong truoc mo cung giay); None neu khong co bang lenh."""
    if bo.c is None:
        return None
    try:
        a = bo.c.lenh[["mo_s", "dong_s", "lot"]].dropna().to_numpy(float)
    except Exception:
        return None
    ev = [(m, 1, l) for m, d, l in a] + [(d, 0, -l) for m, d, l in a]
    ev.sort(key=lambda x: (x[0], x[1]))
    cur = pk = 0.0
    for _, _, dl in ev:
        cur += dl
        pk = max(pk, cur)
    return round(pk, 4)


@_bo_do
def _tran(bo: "_Bo"):
    bo.lop = "tran"
    sau = _sau_theo_chieu(bo)
    sau_chung = bo.sl("chuoi_sau").get("do_sau_lon_nhat")
    # --- tran so lenh moi chieu
    for n, d, ten in (("maxbuyorders", 1, "mua"), ("maxsellorders", -1, "ban")):
        x = bo.so(n)
        if x is None:
            continue
        if 0 not in sau and sau and d not in sau:
            bo.ghi(n, CHUA_GAP, khoi="tran_so_lenh", do_tin="vua", ly_do="khong co lenh %s nao trong lich su" % ten)
            continue
        theo_chieu = d in sau
        s = sau.get(d, sau.get(0))
        if s is None:
            bo.ghi(n, KHONG_DO_DUOC, khoi="tran_so_lenh", do_tin="thap", ly_do="ho so khong cho do sau chuoi")
        elif not theo_chieu and s >= x:
            bo.ghi(n, KHONG_RO, khoi="tran_so_lenh", do=float(s), don_vi="lenh", do_tin="thap",
                   ly_do="khai toi da %s lenh %s; co chuoi %s lenh nhung khong tach duoc theo chieu (can bang lenh): chuoi do co the la chieu kia" % (
                       _gon_so(x), ten, _gon_so(s)), nguon="chuoi_sau")
        elif s > x:
            bo.ghi(n, MAU_THUAN, khoi="tran_so_lenh", do=float(s), don_vi="lenh", do_tin="vua",
                   ly_do="khai toi da %s lenh %s nhung co chuoi %s lenh (da bo lenh bao hiem)" % (_gon_so(x), ten, _gon_so(s)), nguon="chuoi_sau")
        elif s == x:
            bo.ghi(n, KHOP, khoi="tran_so_lenh", do=float(s), don_vi="lenh", do_tin="thap",
                   ly_do="chuoi sau nhat chinh bang tran %s lenh (tran co the dang chan chuoi)" % _gon_so(x), nguon="chuoi_sau")
        else:
            bo.ghi(n, CHUA_GAP, khoi="tran_so_lenh", do=float(s), don_vi="lenh", do_tin="thap",
                   ly_do=("chuoi %s sau nhat %s lenh chua cham tran %s" % (ten, _gon_so(s), _gon_so(x))) if theo_chieu else
                         ("chuoi sau nhat (khong tach theo chieu) %s lenh chua cham tran %s lenh %s" % (_gon_so(s), _gon_so(x), ten)), nguon="chuoi_sau")
    # --- tran tong lot
    x = bo.so("maxlots")
    dinh = bo.sl("rui_ro").get("lot_dinh_lon_nhat")
    dinh_goc = _dinh_lot_goc(bo)
    gom_hedge = ""
    if dinh_goc is not None and (dinh is None or dinh_goc > dinh + 1e-9):
        dinh, gom_hedge = dinh_goc, " (gom lenh bao hiem)"
    if x is not None:
        if dinh is None:
            bo.ghi("maxlots", KHONG_DO_DUOC, khoi="tran_lot_tong", do_tin="thap", ly_do="ho so khong cho tong lot mo dinh")
        elif dinh > x * 1.02:
            bo.ghi("maxlots", MAU_THUAN, khoi="tran_lot_tong", do=float(dinh), don_vi="lot", do_tin="vua",
                   ly_do="khai tran %s lot nhung tong lot mo dinh dat %s lot%s (tran co the tinh theo chieu / chu ky, khong phai tong)" % (
                       _gon_so(x), _gon_so(dinh), gom_hedge), nguon="rui_ro.lot_dinh_lon_nhat")
        elif dinh >= 0.95 * x:
            bo.ghi("maxlots", KHONG_RO, khoi="tran_lot_tong", do=float(dinh), don_vi="lot", do_tin="thap",
                   ly_do="tong lot mo dinh %s lot%s gan tran %s lot (%.0f%%): lenh dang ke tiep cua chuoi sau nhat co the da bi tran chan; "
                         "lich su khong cho thay lenh bi tu choi" % (_gon_so(dinh), gom_hedge, _gon_so(x), 100 * dinh / x), nguon="rui_ro.lot_dinh_lon_nhat")
        else:
            bo.ghi("maxlots", CHUA_GAP, khoi="tran_lot_tong", do=float(dinh), don_vi="lot", do_tin="thap",
                   ly_do="tong lot mo dinh %s lot%s chua toi tran %s lot (%.0f%%)" % (_gon_so(dinh), gom_hedge, _gon_so(x), 100 * dinh / x),
                   nguon="rui_ro.lot_dinh_lon_nhat")
    if "maxlots2newcycle" in bo.v:
        r = bo.hang.get("maxlots")
        if r is not None and r["ket_qua"] == CHUA_GAP:
            bo.ghi("maxlots2newcycle", CHUA_GAP, khoi="tran_lot_tong", do_tin="thap", ly_do="tran lot chua bao gio cham nen che do 'sang chu ky moi' chua duoc dung")
        else:
            bo.ghi("maxlots2newcycle", KHONG_DO_DUOC, khoi="tran_lot_tong", do_tin="thap", ly_do="can biet luc cham tran de thay hanh vi")
    # --- spread toi da
    if "maxspread" in bo.v:
        bo.ghi("maxspread", KHONG_DO_DUOC, khoi="loc_spread", do_tin="vua",
               ly_do="spread luc vao lenh khong nam trong bang deals (can chuoi spread / tick); lenh bi chan vi spread khong hien ra trong lich su")
    # --- loc DCA tu lenh thu N
    cong = bo.bat("usefilterdca")
    thr = bo.so("orders2enablefilterdca")
    if cong is False:
        bo.ghi("usefilterdca", TAT, khoi="loc_dca_tu_lenh_n", do_tin="vua", ly_do="khai tat loc DCA")
        bo.ghi("orders2enablefilterdca", TAT, khoi="loc_dca_tu_lenh_n", do_tin="vua", ly_do="cong UseFilterDCA tat: khong co hieu luc")
    elif cong is True:
        if thr is not None and sau_chung is not None and thr > sau_chung:
            bo.ghi("usefilterdca", CHUA_GAP, khoi="loc_dca_tu_lenh_n", do_tin="thap",
                   ly_do="loc bat tu lenh %s nhung chuoi sau nhat %s lenh" % (_gon_so(thr), _gon_so(sau_chung)))
            bo.ghi("orders2enablefilterdca", CHUA_GAP, khoi="loc_dca_tu_lenh_n", do_tin="thap",
                   ly_do="chuoi sau nhat %s lenh chua toi moc %s" % (_gon_so(sau_chung), _gon_so(thr)))
        else:
            bo.ghi("usefilterdca", KHONG_DO_DUOC, khoi="loc_dca_tu_lenh_n", do_tin="thap", ly_do="loc theo dieu kien gia / chi bao: can duong gia de kiem")
            bo.ghi("orders2enablefilterdca", KHONG_DO_DUOC, khoi="loc_dca_tu_lenh_n", do_tin="thap", ly_do="loc theo dieu kien gia / chi bao: can duong gia de kiem")


# ---------------------------------------------------------------------------------------------------------------- tien / SL / muc tieu ngay
@_bo_do
def _tien(bo: "_Bo"):
    bo.lop = "tien"
    mau = bo.hs.get("mau") or {}
    pip, hd = mau.get("pip"), mau.get("hop_dong")
    lot_dau = _lot_dau_do(bo)
    tp_don = bo.ts("tp_pip")
    if tp_don is None:
        tp_don = bo.ts("tp_pip_chuoi_1")
    usd = None
    if pip and hd and lot_dau and tp_don:
        usd = float(tp_don) * float(pip) * float(hd) * float(lot_dau)
    # --- SL cung
    x = bo.so("sl")
    if x is not None:
        kl, dt = bo.kl("sl_cung"), bo.dt("sl_cung")
        if x == 0:
            bo.ghi("sl", TAT if kl != "co" else MAU_THUAN, khoi="sl_cung", do_tin="vua", ly_do="khai 0 = khong dat SL co dinh" + ("; nhung lich su co SL co dinh" if kl == "co" else ""))
        elif kl == "co":
            bo.ghi("sl", KHOP, khoi="sl_cung", do_tin=dt, ly_do="lich su co lenh cat lo o khoang cach co dinh")
        elif kl == "khong" and dt == "cao" and bo.sl("chuoi_sau").get("do_sau_lon_nhat"):
            bo.ghi("sl", MAU_THUAN, khoi="sl_cung", do_tin="vua", ly_do="khai SL %s nhung khong thay lenh nao cat lo o khoang cach co dinh" % _gon_so(x))
        else:
            bo.ghi("sl", KHONG_DO_DUOC, khoi="sl_cung", do_tin="thap", ly_do="khong du de biet SL co dinh co duoc dat khong")
    # --- cac muc tieu / cat lo theo tien (moneytp*, moneysl*, dailymoney*, dailyper*)
    for n in [n for n in bo.v if re.match(r"^(moneytp|moneyprofit|moneysl|dailymoney|dailyper|newmoney)", n) and n not in bo.hang]:
        x = bo.so(n)
        if x is None:
            continue
        if re.match(r"^moneysl2reset", n) or n in ("resetlots", "multiplierreset", "tpreset"):
            continue
        if x == 0:
            bo.ghi(n, TAT, khoi="", do_tin="vua", ly_do="khai 0 = khong dung muc tieu / cat lo nay")
            continue
        if n.startswith("moneytp"):
            kl, dt = bo.kl("tp_chuoi_tien"), bo.dt("tp_chuoi_tien")
            if kl == "co":
                bo.ghi(n, KHOP, khoi="tp_chuoi_tien", do_tin=dt, ly_do="chuoi dong o lai tien co dinh")
            elif usd is not None and abs(usd - x) <= 0.05 * x:
                bo.ghi(n, KHONG_RO, khoi="tp_chuoi_tien", do=usd, don_vi="tien", do_tin="thap",
                       ly_do="khai %s tien trung voi muc TP %s pip cua lenh don o lot %s (= %s tien): hai co che trung nhau, khong tach duoc" % (
                           _gon_so(x), _gon_so(tp_don), _gon_so(lot_dau), _gon_so(round(usd, 2))))
            else:
                bo.ghi(n, KHONG_DO_DUOC, khoi="tp_chuoi_tien", do_tin="thap", ly_do="chuoi khong dong o lai tien co dinh (da do); khai co the chi ap dung cho ca tai khoan")
        elif n.startswith("moneysl"):
            kl, dt = bo.kl("cat_lo_theo_tien"), bo.dt("cat_lo_theo_tien")
            if kl == "co":
                bo.ghi(n, KHOP, khoi="cat_lo_theo_tien", do_tin=dt, ly_do="lich su co chuoi cat lo o muc lo tien co dinh")
            else:
                bo.ghi(n, KHONG_DO_DUOC, khoi="cat_lo_theo_tien", do_tin="thap",
                       ly_do="khong thay chuoi nao cat lo theo muc tien; neu chua chuoi nao lo toi muc do thi chua kiem duoc")
        else:
            bo.ghi(n, KHONG_DO_DUOC, khoi="", do_tin="thap", ly_do="muc tieu theo ngay can duong von / thoi gian trong ngay de kiem")
    # --- dat lai khi cat lo
    if "moneysl2reset" in bo.v:
        x = bo.so("moneysl2reset")
        if x == 0:
            bo.ghi("moneysl2reset", TAT, khoi="", do_tin="vua", ly_do="khai 0: khong dat lai lot / TP khi cat lo")
            for n in bo.khac_het(r"^(resetlots|multiplierreset|tpreset)$"):
                bo.ghi(n, TAT, khoi="", do_tin="vua", ly_do="MoneySL2Reset = 0: nhom dat lai khong co hieu luc")
        else:
            bo.ghi("moneysl2reset", KHONG_DO_DUOC, khoi="", do_tin="thap", ly_do="can chuoi cat lo de thay dat lai; chua kiem duoc")


# ---------------------------------------------------------------------------------------------------------------- nhom con lai
@_bo_do
def _khac(bo: "_Bo"):
    bo.lop = "khac"
    sau = bo.sl("chuoi_sau").get("do_sau_lon_nhat")
    # --- DCA bat / tat
    v = bo.bat("usedca")
    if v is not None:
        if v and sau is not None and sau >= 2:
            bo.ghi("usedca", KHOP, khoi="", do=float(sau), don_vi="lenh", do_tin="cao", ly_do="lich su co chuoi them lenh toi %s lenh" % _gon_so(sau))
        elif v and sau is not None:
            bo.ghi("usedca", MAU_THUAN, khoi="", do_tin="vua", ly_do="khai bat DCA nhung moi chuoi chi co 1 lenh")
        elif v is False and sau is not None and sau >= 2:
            bo.ghi("usedca", MAU_THUAN, khoi="", do_tin="vua", ly_do="khai tat DCA nhung lich su co chuoi them lenh toi %s lenh" % _gon_so(sau))
        elif v is False:
            bo.ghi("usedca", TAT, khoi="", do_tin="vua", ly_do="khai tat DCA va lich su khong co chuoi them lenh")
    for n in ("dcamode", "coeffmode"):
        if n in bo.v:
            ok = bo.kiem_lot is not None and bo.kiem_lot.get("ty", 0) >= 0.99
            bo.ghi(n, KHONG_RO, khoi="", do_tin="thap",
                   ly_do="che do tinh he so / DCA (%s): cong thuc lot va buoc do duoc da khop nen ban khong thay che do khac biet; chua tach duoc" % bo.v[n]
                   if ok else "che do tinh he so / DCA (%s): chua co phep do rieng" % bo.v[n])
    # --- xo so (lottery)
    v = bo.bat("uselottery")
    if v is False:
        bo.ghi("uselottery", TAT, khoi="", do_tin="vua", ly_do="khai tat")
        for n in bo.khac_het(r"lottery"):
            bo.ghi(n, TAT, khoi="", do_tin="vua", ly_do="cong UseLottery tat: khong co hieu luc")
    elif v is True:
        bo.ghi("uselottery", KHONG_DO_DUOC, khoi="", do_tin="thap", ly_do="co che 'xo so' (lot / he so bat thuong) chua co phep do")
        for n in bo.khac_het(r"lottery"):
            bo.ghi(n, KHONG_DO_DUOC, khoi="", do_tin="thap", ly_do="gia tri rieng cua che do xo so khong tach duoc")
    # --- cac khoa chi dinh / hien thi (khong anh huong giao dich)
    for n in bo.khac_het(r"^(magicid|combine|usemagicfilter|show\w*|\w*showarrows|\w*arrowdist|\w*arrows?)$"):
        bo.ghi(n, KHONG_LIEN_QUAN, khoi="", do_tin="vua", ly_do="ma so dinh danh / hien thi tren bieu do: khong anh huong lenh")


# ---------------------------------------------------------------------------------------------------------------- du phong
@_bo_do
def _du(bo: "_Bo"):
    """Moi khoa con lai: co chi bao vao -> khong do duoc; co goi y khoi -> chua doi chieu; khong co goi y -> khong phan loai."""
    bo.lop = "khac"
    for n in [n for n in bo.v if n not in bo.hang]:
        goi_y = tuple(KC.loai_tu_ten_tham_so(bo.ten[n]))
        if any(str(g).startswith("vao_") for g in goi_y):
            bo.ghi(n, KHONG_DO_DUOC, khoi=goi_y[0], do_tin="vua", lop="vao",
                   ly_do="tham so chi bao / dieu kien vao lenh: can duong gia cung thoi gian de kiem (lich su lenh chi cho thay lenh vao luc nao)")
        elif goi_y:
            bo.ghi(n, CHUA_DOI_CHIEU, khoi=goi_y[0], do_tin="thap",
                   ly_do="ten goi y khoi %s nhung chua co bo doi chieu cho tham so nay (khong doan)" % ", ".join(str(g) for g in goi_y))
        else:
            bo.ghi(n, KHONG_PHAN_LOAI, khoi="", do_tin="thap", ly_do="ten khong co trong bang quy tac (khong doan bua)")


# ---------------------------------------------------------------------------------------------------------------- doi chieu
def _ds_khoi(k) -> list:
    if not k:
        return []
    return [str(k)] if isinstance(k, str) else [str(x) for x in k]


def _dem(rows) -> dict:
    d = {k: 0 for k in KET_QUA}
    for h in rows:
        d[h["ket_qua"]] += 1
    d["tong"] = len(rows)
    return d


def _doc_bo_set(bo_set, ten=None) -> dict:
    """Nhan: ket qua `doc_set` / `ea_tho.doc_set` (co 'khoa'), duong dan tep, hoac van ban .set."""
    if isinstance(bo_set, dict) and "khoa" in bo_set:
        khoa = {str(k): str(v) for k, v in bo_set["khoa"].items()}
        return {"ten": str(ten or bo_set.get("ten") or "bo_set"), "khoa": khoa, "n": int(bo_set.get("n", len(khoa))), "sha": str(bo_set.get("sha", ""))}
    r = doc_set(bo_set, ten)
    return {"ten": r["ten"], "khoa": {str(k): str(v) for k, v in r["khoa"].items()}, "n": int(r.get("n", len(r["khoa"]))), "sha": str(r.get("sha", ""))}


def _ten_ds(rows, toi_da=6) -> str:
    ten = [h["ten"] for h in rows]
    return ", ".join(ten[:toi_da]) + (" (+%d)" % (len(ten) - toi_da) if len(ten) > toi_da else "")


def _cat(s, n) -> str:
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 3] + "..."


def doi_chieu(hs: dict, bo_set, c=None, he_so_don_vi: float | None = None, ten: str | None = None) -> dict:
    """Doi chieu mot bo .set voi ho so co che (`ho_so_bot.ho_so`). `c` (bang lenh, tuy chon) cho phep kiem TUNG lenh (lot, tran lenh,
    tre sau lenh dong) thay vi chi doc cac con so tom tat cua ho so.

    Tra dict JSON thuan: bo_set, mau, don_vi, tham_so (DUNG MOT dong cho moi khoa .set, theo thu tu trong .set), dem, mau_thuan,
    nut_an, cong_thuc, khoi (theo bo, cho so_sanh_bo_set), kiem_lot, ghi_chu, canh_bao, loi, tom_tat."""
    s = _doc_bo_set(bo_set, ten)
    bo = _Bo(s["khoa"], hs, c, 1.0)
    if he_so_don_vi is not None:
        f = float(he_so_don_vi)
        if not (f > 0 and math.isfinite(f)):
            raise ValueError("he_so_don_vi phai la so duong huu han")
        dv = {"he_so": f, "chac": True, "diem": {}, "ly_do": "nguoi goi dat he so don vi = %s" % _gon_so(f)}
    else:
        try:
            dv = uoc_luong_don_vi(bo)
        except Exception as e:
            dv = {"he_so": 1.0, "chac": False, "diem": {}, "ly_do": "loi uoc luong don vi (%s): giu he so 1" % type(e).__name__}
            bo.loi.append("uoc_luong_don_vi: %s: %s" % (type(e).__name__, str(e)[:140]))
    bo.f = float(dv["he_so"])
    for ten_bo, fn in _BO_DO:
        _chay_bo_do(bo, ten_bo, fn)

    # ---- moi khoa .set DUNG MOT dong
    rows: list[dict] = []
    for t in s["khoa"]:
        n = _chuan(t)
        h = bo.hang.get(n) if bo.ten.get(n) == t else None
        if h is None:
            if bo.ten.get(n) not in (None, t):
                ly = "hai khoa cung ten chuan '%s' (da giu khoa '%s'): khoa nay khong duoc doi chieu" % (n, bo.ten.get(n))
            else:
                ly = "khong co bo doi chieu nao xu ly khoa nay (loi module)"
                bo.loi.append("khong_dong: khoa '%s' khong co dong ket qua" % t)
            h = {"ten": t, "khai": s["khoa"][t], "lop": "khac", "khoi": "", "ket_qua": KHONG_PHAN_LOAI, "do": None, "don_vi": "",
                 "do_tin": "thap", "ly_do": ly, "nguon_do": ""}
        h = dict(h)
        kd = _ds_khoi(h.get("khoi"))
        h["khoi"] = kd[0] if kd else ""
        if len(kd) > 1:
            h["khoi_phu"] = kd[1:]
        h["_kd"] = kd
        rows.append(h)
    dem = _dem(rows)

    # ---- khoi -> cac dong .set noi toi khoi do
    theo_khoi: dict[str, list] = {}
    for h in rows:
        for b in h["_kd"]:
            theo_khoi.setdefault(b, []).append({"ten": h["ten"], "khai": h["khai"], "ket_qua": h["ket_qua"], "do_tin": h["do_tin"]})
    khoi_hs = hs.get("khoi") or {}
    ts_hs = hs.get("tham_so") or {}

    mau_thuan = [{"ten": h["ten"], "khai": h["khai"], "do": h["do"], "do_tin": h["do_tin"], "khoi": h["khoi"], "ly_do": h["ly_do"]}
                 for h in rows if h["ket_qua"] == MAU_THUAN]
    nut_an, cong_thuc, khoi_bo = [], [], {}
    for ma, k in khoi_hs.items():
        lq = theo_khoi.get(ma, [])
        if k.get("ket_luan") in ("co", "khong") or lq:
            khoi_bo[ma] = {"ket_luan": k.get("ket_luan"), "do_tin": k.get("do_tin"), "ten": k.get("ten"), "tham_so_set": lq}
        if k.get("ket_luan") != "co":
            continue
        co_lai = ma in bo.giai_thich
        ts_do = {nm: {"gia_tri": e.get("gia_tri"), "don_vi": e.get("don_vi")} for nm, e in ts_hs.items() if e.get("khoi") == ma}
        cong_thuc.append({"khoi": ma, "ten": k.get("ten"), "nhom": k.get("nhom"), "do_tin": k.get("do_tin"), "ly_do": k.get("ly_do"),
                          "tham_so_do": ts_do, "tham_so_set": lq, "co_khop": co_lai})
        if not co_lai:
            nut_an.append({"khoi": ma, "ten": k.get("ten"), "nhom": k.get("nhom"), "do_tin": k.get("do_tin"), "ly_do": k.get("ly_do"),
                           "tham_so_lien_quan": lq})

    # ---- canh bao
    canh_bao = list(bo.canh_bao)
    quyet = dem[KHOP] + dem[MAU_THUAN]
    if quyet >= 5 and dem[MAU_THUAN] / quyet >= 0.4:
        canh_bao.append("MAU THUAN chiem %d/%d tham so da quyet dinh: kiem tra bo .set nay co dung la bo da chay tren lich su lenh khong "
                        "(khac phien ban EA, khac bo .set, don vi khoang cach)" % (dem[MAU_THUAN], quyet))
    if dem[KHOP] == 0:
        canh_bao.append("khong co tham so nao KHOP: kiem tra tep lenh va bo .set co cung mot bot khong")
    if not dv.get("chac"):
        canh_bao.append("he so don vi khoang cach (%s) khong chac: %s" % (_gon_so(dv["he_so"]), dv.get("ly_do", "")))
    if c is None:
        canh_bao.append("khong co bang lenh: lot kiem theo khoang he so, tran lenh theo do sau chung, tre sau lenh dong theo ho so (kem tin cay hon)")
    tick_s = (hs.get("mau") or {}).get("tick_s")
    if tick_s is not None and tick_s >= 5:
        canh_bao.append("lenh tester dat tren luoi %s giay: moi so do thoi gian (tre, nhip) chi chinh xac den khoang do" % _gon_so(tick_s))

    kiem_lot = bo.kiem_lot
    tom_tat = _tom_tat(s, hs, rows, dem, dv, mau_thuan, nut_an, kiem_lot, bo.loi, canh_bao)
    for h in rows:
        h.pop("_kd", None)
    kq = {"phien_ban": PHIEN_BAN,
          "bo_set": {"ten": s["ten"], "n": s["n"], "sha": s["sha"]},
          "mau": hs.get("mau"),
          "don_vi": {"he_so": dv["he_so"], "chac": bool(dv.get("chac")), "ly_do": dv.get("ly_do", ""), "diem": dv.get("diem", {})},
          "tham_so": rows, "dem": dem, "mau_thuan": mau_thuan, "nut_an": nut_an, "cong_thuc": cong_thuc, "khoi": khoi_bo,
          "kiem_lot": kiem_lot, "ghi_chu": bo.ghi_chu, "canh_bao": canh_bao, "loi": list(bo.loi), "tom_tat": tom_tat}
    return _j(kq)


def _tom_tat(s, hs, rows, dem, dv, mau_thuan, nut_an, kiem_lot, loi, canh_bao) -> list:
    """Toi da 8 dong loi thuong, dong quan trong dung truoc."""
    mau = hs.get("mau") or {}
    L = ["Bo .set '%s' (%d tham so) doi chieu voi %s lenh that cua %s: KHOP %d, MAU THUAN %d, TAT %d, BI CHE %d, CHUA GAP %d, "
         "KHONG DO DUOC %d, KHONG RO %d, khac %d." % (
             s["ten"], dem["tong"], _gon_so(mau.get("so_lenh")), mau.get("ma", "?"), dem[KHOP], dem[MAU_THUAN], dem[TAT], dem[BI_CHE], dem[CHUA_GAP],
             dem[KHONG_DO_DUOC], dem[KHONG_RO], dem[KHONG_PHAN_LOAI] + dem[KHONG_LIEN_QUAN] + dem[CHUA_DOI_CHIEU])]
    L.append("Don vi khoang cach: 1 don vi trong .set = %s pip cua san (%s)." % (
        _gon_so(dv["he_so"]), "da kiem bang nhieu cap so duoc" if dv.get("chac") else "chua chac: khong du cap khoang cach de so"))
    chac = [h for h in rows if h["ket_qua"] == KHOP and h["do_tin"] == "cao"]
    L.append(("Khop chac (do tin cao): %s." % _ten_ds(chac)) if chac else "Khong co tham so nao khop o do tin cao.")
    if kiem_lot:
        L.append("Lot: %d/%d lenh dung cong thuc %s." % (kiem_lot["khop"], kiem_lot["tong"], kiem_lot.get("cong_thuc", "")))
    if mau_thuan:
        ds = ", ".join("%s (khai %s, tin cay %s)" % (m["ten"], _cat(m["khai"], 12), m["do_tin"]) for m in mau_thuan[:4]) + (" (+%d)" % (len(mau_thuan) - 4) if len(mau_thuan) > 4 else "")
        L.append("MAU THUAN (tac gia noi X, lenh that cho thay Y): %s. Vi du: %s" % (ds, _cat(mau_thuan[0]["ly_do"], 150)))
    if nut_an:
        L.append("NUT AN (lenh that co co che ma .set khong co tham so nao dieu khien): %s." % ", ".join(
            "%s (%s)" % (n["ten"] or n["khoi"], n["khoi"]) for n in nut_an[:5]))
    cg = [h for h in rows if h["ket_qua"] == CHUA_GAP]
    if cg:
        L.append("CHUA GAP (lich su chua toi dieu kien cua tham so): %s." % _ten_ds(cg))
    if loi:
        L.append("LOI: %d bo doi chieu hong (xem 'loi'): %s" % (len(loi), _cat(loi[0], 120)))
    elif canh_bao:
        L.append("Luu y: %s" % _cat(canh_bao[0], 200))
    return L[:8]


def doi_chieu_tep(deals, bo_set, ma=None, pip=None, hop_dong=None, von_dau=None, khung_phut=None, ten=None, he_so_don_vi=None) -> dict:
    """Mot lenh: doc tep lenh (deals), do ho so co che, doi chieu voi bo .set (duong dan hoac van ban). Tra nhu `doi_chieu`."""
    from nhan import ho_so_bot as HB
    c = HB.chuan_bi(deals, ma=ma, pip=pip, hop_dong=hop_dong, von_dau=von_dau, khung_phut=khung_phut)
    hs = HB.ho_so(c)
    return doi_chieu(hs, bo_set, c=c, he_so_don_vi=he_so_don_vi, ten=ten)


# ---------------------------------------------------------------------------------------------------------------- nhieu bo .set
def _so_hoc(x):
    try:
        v = float(str(x).strip())
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _khac_khai(a, b) -> bool:
    x, y = _so_hoc(a), _so_hoc(b)
    if x is not None and y is not None:
        return abs(x - y) > 1e-9
    return str(a).strip().lower() != str(b).strip().lower()


_SO_SANH_DUOC = (KHOP, MAU_THUAN, KHONG_RO)
_DON_VI_TY_LE = ("ty le", "ty le mua")
_THU_TU_TIN = {"thap": 0, "vua": 1, "cao": 2}


def _la_cong_tac(khai) -> bool:
    return isinstance(khai, bool) or (isinstance(khai, str) and khai.strip().lower() in ("true", "false"))


def so_sanh_bo_set(ds, dung_sai: float = 0.03, dung_sai_ty_le: float = 0.10) -> dict:
    """Nhieu bo .set (cua cung mot bot, hoac cung ho EA): doi KHAI BAO co keo theo doi HANH VI khong? `ds` = [(ten, ket qua doi_chieu)].

    Chi so sanh dong co SO DO la chinh dai luong cua tham so (khong so cong tac, khong so do phu nhu do sau chuoi, khong so ty le
    tren mau nho): moi dong phai co ket qua KHOP / MAU_THUAN / KHONG_RO va `do` la so; ty le chi coi la khac khi lech > dung_sai_ty_le.
      bang_chung        khai bao khac nhau, hanh vi do duoc khac nhau, moi dong deu KHOP: tham so nay THAT SU dieu khien hanh vi do
      khong_quyet_dinh  khai bao GIONG nhau nhung hanh vi khac: con yeu to khac quyet dinh (ban .set / phien ban / khoi an)
      khong_tac_dung    khai bao khac nhau nhung hanh vi y het va khong dong nao KHOP: tham so khong co tac dung nhin thay
      chua_du           con lai: cong tac (xem khoi_doi), thieu so do, chua cham ngung, ...  (kem `vi_sao`)
    Theo khoi co che: `khoi_doi` = khoi co o bo nay, khong o bo kia, kem cac tham so .set noi toi khoi (cong tat / khoi tao).
    Moi muc co `do_tin` = muc thap nhat trong cac dong."""
    ds = [(str(t), r) for t, r in ds]
    gom: dict[str, list] = {}
    for ten_bo, r in ds:
        for h in r.get("tham_so") or []:
            gom.setdefault(_chuan(h["ten"]), []).append((ten_bo, h))
    out = {"bo": [t for t, _ in ds], "bang_chung": [], "khong_quyet_dinh": [], "khong_tac_dung": [], "chua_du": [], "khoi_doi": []}
    for n, ls in gom.items():
        if len(ls) < 2:
            continue
        cac_bo = [{"bo": t, "khai": h["khai"], "do": h.get("do"), "ket_qua": h["ket_qua"], "khoi": h.get("khoi", ""), "do_tin": h.get("do_tin", "")}
                  for t, h in ls]
        e = {"tham_so": ls[0][1]["ten"], "cac_bo": cac_bo}
        tin = [_THU_TU_TIN.get(h.get("do_tin"), 0) for _, h in ls]
        e["do_tin"] = {v: k for k, v in _THU_TU_TIN.items()}[min(tin)]
        vi_sao = None
        if any(h["ket_qua"] not in _SO_SANH_DUOC for _, h in ls):
            kq = sorted({h["ket_qua"] for _, h in ls if h["ket_qua"] not in _SO_SANH_DUOC})
            vi_sao = "co bo chua co so do cua chinh tham so nay (%s)" % ", ".join(kq)
        elif any(_la_cong_tac(h["khai"]) for _, h in ls):
            vi_sao = "la cong tac: so do (neu co) la dai luong phu, xem khoi_doi"
        else:
            do = [h.get("do") for _, h in ls]
            if not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in do):
                vi_sao = "thieu so do dang so o it nhat mot bo"
        if vi_sao:
            e["vi_sao"] = vi_sao
            out["chua_du"].append(e)
            continue
        khai_khac = any(_khac_khai(ls[0][1]["khai"], h["khai"]) for _, h in ls[1:])
        do = [h.get("do") for _, h in ls]
        if all((h.get("don_vi") or "") in _DON_VI_TY_LE for _, h in ls):
            do_khac = (max(do) - min(do)) > dung_sai_ty_le
        else:
            do_khac = (max(do) - min(do)) > max(1e-9, dung_sai * max(abs(x) for x in do))
        moi_khop = all(h["ket_qua"] == KHOP for _, h in ls)
        if khai_khac and do_khac and moi_khop:
            e["y_nghia"] = "doi khai bao keo theo doi hanh vi do duoc, moi dong deu khop: tham so nay dieu khien hanh vi do"
            out["bang_chung"].append(e)
        elif (not khai_khac) and do_khac:
            e["y_nghia"] = "khai bao giong nhau nhung hanh vi do duoc khac: con yeu to khac quyet dinh"
            out["khong_quyet_dinh"].append(e)
        elif khai_khac and (not do_khac) and not moi_khop:
            e["y_nghia"] = "khai bao khac nhau nhung hanh vi y het: tham so khong co tac dung nhin thay (bi che hoac tat)"
            out["khong_tac_dung"].append(e)
        else:
            e["vi_sao"] = "khai bao va hanh vi cung doi nhung khong dong deu KHOP, hoac khong doi gi ca"
            out["chua_du"].append(e)
    # ---- theo khoi
    ma_khoi = []
    for _, r in ds:
        for m in (r.get("khoi") or {}):
            if m not in ma_khoi:
                ma_khoi.append(m)
    for m in ma_khoi:
        kl = [(t, (r.get("khoi") or {}).get(m)) for t, r in ds]
        co = [t for t, k in kl if k and k.get("ket_luan") == "co"]
        khong = [t for t, k in kl if k and k.get("ket_luan") == "khong"]
        if co and khong:
            out["khoi_doi"].append({"khoi": m, "ten": next((k.get("ten") for _, k in kl if k and k.get("ten")), None), "co_o": co, "khong_o": khong,
                                    "tham_so_theo_bo": {t: (k.get("tham_so_set") if k else []) for t, k in kl}})
    L = ["%d bo .set; %d tham so co o >= 2 bo: bang chung %d, khong quyet dinh %d, khong tac dung %d, chua du %d; %d khoi co che doi giua cac bo." % (
        len(ds), sum(1 for ls in gom.values() if len(ls) >= 2), len(out["bang_chung"]), len(out["khong_quyet_dinh"]), len(out["khong_tac_dung"]),
        len(out["chua_du"]), len(out["khoi_doi"]))]
    if out["bang_chung"]:
        L.append("Bang chung (doi khai bao -> doi hanh vi, khop): %s." % ", ".join("%s (tin cay %s)" % (e["tham_so"], e["do_tin"]) for e in out["bang_chung"][:8]))
    if out["khong_quyet_dinh"]:
        L.append("Khong quyet dinh (cung khai, khac hanh vi): %s." % ", ".join("%s (tin cay %s)" % (e["tham_so"], e["do_tin"]) for e in out["khong_quyet_dinh"][:8]))
    if out["khong_tac_dung"]:
        L.append("Khong tac dung (khac khai, cung hanh vi): %s." % ", ".join("%s (tin cay %s)" % (e["tham_so"], e["do_tin"]) for e in out["khong_tac_dung"][:8]))
    if out["khoi_doi"]:
        L.append("Khoi co o bo nay khong o bo kia: %s." % ", ".join("%s (co o %s)" % (k["khoi"], "/".join(k["co_o"])) for k in out["khoi_doi"][:8]))
    out["tom_tat"] = L[:8]
    return _j(out)


# ---------------------------------------------------------------------------------------------------------------- bao cao
def _ascii(s) -> str:
    """Bo dau tieng Viet de bao cao Markdown luon ASCII (gia tri .set cua tac gia co the co dau)."""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.replace("\u0111", "d").replace("\u0110", "D").encode("ascii", "replace").decode("ascii")


def _o(x) -> str:
    return " ".join(str(x).replace("|", "/").split())


def bao_cao_md(r: dict, toi_da_dong: int = 400) -> str:
    """Bao cao Markdown (ASCII): tom tat, mau thuan, nut an, cong thuc do duoc, bang tung tham so."""
    b = r.get("bo_set") or {}
    L = ["# Doi chieu bo .set '%s' voi lenh that" % b.get("ten", "?"), ""]
    L += ["- " + t for t in r.get("tom_tat", [])]
    if r.get("canh_bao"):
        L += ["", "## Luu y"] + ["- " + _o(t) for t in r["canh_bao"]]
    if r.get("loi"):
        L += ["", "## Loi (bo doi chieu hong)"] + ["- " + _o(t) for t in r["loi"]]
    L += ["", "## Mau thuan: tac gia noi X, lenh that cho thay Y", ""]
    if r.get("mau_thuan"):
        L += ["| Tham so | Tac gia khai | Do tin | Lenh that cho thay |", "|---|---|---|---|"]
        L += ["| %s | %s | %s | %s |" % (_o(m["ten"]), _o(m["khai"]), m["do_tin"], _cat(_o(m["ly_do"]), 260)) for m in r["mau_thuan"]]
    else:
        L.append("(khong co)")
    L += ["", "## Nut an: co che co trong lenh that, khong tham so nao dieu khien", ""]
    if r.get("nut_an"):
        for n in r["nut_an"]:
            lq = ", ".join("%s=%s (%s)" % (x["ten"], _cat(x["khai"], 12), x["ket_qua"]) for x in n["tham_so_lien_quan"]) or "khong co tham so nao noi toi"
            L.append("- **%s** (%s, do tin %s): %s. Tham so lien quan: %s" % (n.get("ten") or n["khoi"], n["khoi"], n["do_tin"], _cat(_o(n["ly_do"]), 220), lq))
    else:
        L.append("(khong co)")
    L += ["", "## Cong thuc do duoc (khoi co che dang chay)", ""]
    for k in r.get("cong_thuc", []):
        ts = ", ".join("%s=%s%s" % (nm, _gon_so(e["gia_tri"]) if isinstance(e.get("gia_tri"), (int, float)) else e.get("gia_tri"),
                                     (" " + e["don_vi"]) if e.get("don_vi") else "") for nm, e in (k.get("tham_so_do") or {}).items())
        st = ", ".join("%s=%s" % (x["ten"], _cat(x["khai"], 12)) for x in k.get("tham_so_set", []) if x["ket_qua"] == KHOP)
        L.append("- **%s** (%s, do tin %s): do duoc [%s]; .set khop [%s]" % (k.get("ten") or k["khoi"], k["khoi"], k["do_tin"], ts or "-", st or "khong co"))
    if r.get("kiem_lot"):
        kl = r["kiem_lot"]
        L += ["", "Lot: %d/%d lenh dung cong thuc %s (chuoi sau nhat %s lenh)." % (kl["khop"], kl["tong"], kl.get("cong_thuc", ""), kl.get("n_sau_nhat"))]
    L += ["", "## Tung tham so (theo thu tu trong .set)", "", "| Tham so | Khai | Ket qua | Do tin | Do duoc | Ly do |", "|---|---|---|---|---|---|"]
    for h in (r.get("tham_so") or [])[:toi_da_dong]:
        do = "" if h.get("do") is None else "%s %s" % (_gon_so(h["do"]) if isinstance(h["do"], (int, float)) else h["do"], h.get("don_vi", ""))
        L.append("| %s | %s | %s | %s | %s | %s |" % (_o(h["ten"]), _cat(_o(h["khai"]), 24), h["ket_qua"], h["do_tin"], _o(do), _cat(_o(h["ly_do"]), 240)))
    d = r.get("dem") or {}
    L += ["", "Dem: " + ", ".join("%s %d" % (k, d.get(k, 0)) for k in KET_QUA if d.get(k)), ""]
    return _ascii("\n".join(L))


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Doi chieu bo .set cua tac gia voi co che do tu lenh that (ho_so_bot)")
    ap.add_argument("deals", help="tep lenh tester (deals .csv/.csv.gz/.html/.xlsx)")
    ap.add_argument("bo_set", help="tep .set (hoac .set.txt)")
    ap.add_argument("--ma", default=None, help="ma san, vd GOLD.i#")
    ap.add_argument("--pip", type=float, default=None)
    ap.add_argument("--hop-dong", type=float, default=None)
    ap.add_argument("--von", type=float, default=None)
    ap.add_argument("--khung-phut", type=float, default=None)
    ap.add_argument("--he-so-don-vi", type=float, default=None, help="ghi de he so don vi (1 = pip, 10 = point)")
    ap.add_argument("--json", default=None, help="ghi ket qua JSON")
    ap.add_argument("--md", default=None, help="ghi bao cao Markdown")
    ap.add_argument("--gon", action="store_true", help="chi in tom tat")
    a = ap.parse_args(argv)
    r = doi_chieu_tep(a.deals, a.bo_set, ma=a.ma, pip=a.pip, hop_dong=a.hop_dong, von_dau=a.von, khung_phut=a.khung_phut,
                      he_so_don_vi=a.he_so_don_vi)
    if a.json:
        Path(a.json).write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.md:
        Path(a.md).write_text(bao_cao_md(r), encoding="utf-8")
    print("\n".join(r["tom_tat"]))
    if not a.gon:
        for h in r["tham_so"]:
            print("%-26s %-12s %-16s %-5s %s" % (h["ten"][:26], _cat(h["khai"], 12), h["ket_qua"], h["do_tin"], _cat(h["ly_do"], 90)))
    return 1 if r["loi"] else 0


if __name__ == "__main__":
    sys.exit(main())
