# -*- coding: utf-8 -*-
"""luoi_nhan.py - NHAN C cho engine luoi (`luoi._mot_ro` va `luoi._mot_ro_duong`, chon theo `ThamSo.khop_bar`): tu dich, nap
bang ctypes, tu kiem, DU PHONG Python.

Vi sao: chu du an hoi cach tang toc do test (03/10/2026). `_mot_ro` do duoc 2,8-7,9 us/bar: mot lan chay 190.000 bar M15 ~ 0,5-1,3
giay, quet 1.000 to hop ~ 20 phut tren mot nhan. Ban C cung phep tinh nhanh hon ~2 bac do lon, va ctypes NHA GIL nen quet duoc
da luong (ThreadPoolExecutor) ma khong can tien trinh phu.

Nguyen tac (giu lai, dung bo):
  1. Ban Python (`luoi.mot_ro_chuan`: `_mot_ro` cho `cuc_tri`, `_mot_ro_duong` cho `duong_di`) la CHUAN va van la duong du phong. Nhan C
     chi duoc dung khi (a) dich duoc, (b) TU KIEM khop ban Python tren cac kich ban co dinh cua chinh Python dang chay, CA HAI
     mo hinh bar, (c) tham so nam trong mien da kiem. Khong dat mot trong ba -> Python, im lang ve ket qua (KHONG doi so), chi ghi
     ly do vao `trang_thai()`.
  2. Khop TUNG BIT khi co the (cung thu tu phep tinh, cung kieu cong cua `sum()` theo phien ban Python: >= 3.12 cong bu Neumaier
     tren float thuan - chi `cuc_tri`; `duong_di` cong tuan tu moi noi). Khac biet con lai chi co the den tu libm khac nhau cua
     `pow` (Windows/zig) - tu kiem cho phep sai so 1e-9 NHUNG buoc chuoi lenh (so ro, so lenh, bar, id, tang) phai TRUNG KHIT.
  3. Khong sua hanh vi cua engine o day. Muon doi hanh vi: sua ban Python truoc, dich lai `luoi_nhan.c` sau, chay test_luoi_nhan +
     test_luoi_duong_di.

Bien moi truong:
  LUOI_NHAN=py|c|auto   py = khong bao gio dung C; c = bat buoc C (loi neu khong co); auto (mac dinh) = C neu dung duoc
  LUOI_NHAN_CC="..."    lenh bien dich rieng (vd `zig cc`, `gcc`); mac dinh tu tim cc/gcc/clang/zig/ziglang/cl
  LUOI_NHAN_CACHE=dir   thu muc cache .so/.dll (mac dinh: ngoai repo, theo nguoi dung)

May nha Windows khong co trinh bien dich: `pip install ziglang` (khoang 80 MB, mot lan) la du - `python -m ziglang cc` duoc tu tim.
Xem lai: `python -m nhan.luoi_nhan` (trang thai + tu kiem), `python -m nhan.luoi_nhan do` (do toc do).
"""
from __future__ import annotations

import ctypes
import hashlib
import importlib.util
import inspect
import json
import math
import os
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import numpy as np

PHIEN_BAN = 5                      # = LUOI_NHAN_PHIEN_BAN trong luoi_nhan.c (3: them mo hinh `duong_di`, tham so P_MO_HINH; 4: dung sai cham moc;
                                   #   5: co che thoat + loc gio: cat lo ca ro, thoat gio, nghi, cua so gio vao lenh; them con tro `tg`, 6 tham so, 2 thong ke)
NGUON_C = Path(__file__).with_name("luoi_nhan.c")

#: Thu tu KHOP enum P_* trong luoi_nhan.c
_TEN_P = ("lot", "hop", "pip", "buoc", "tp", "tran", "kieu", "he_lot", "he_buoc", "buoc_tran", "cho_lui", "tia",
          "bien_cap", "cap_moi_bar", "chot_tien", "ty_le", "kahan", "mo_hinh",
          "cat_pip", "cat_tien", "thoat_gio", "nghi_gio", "gio_vao_tu", "gio_vao_den")
_KIEU = {"nhan": 1.0, "cong": 2.0}  # con lai (phang / la) = 0.0, y het `_lot` Python
#: Truong `ThamSo` / `QuyCach` ma nhan C DOC = nhung truong `luoi._mot_ro` / `luoi._mot_ro_duong` / `luoi.chay_mang` doc. `test_luoi_nhan`
#: quet nguon cac ham do: them truong moi vao engine ma quen nhan C thi test do (neu khong, C tinh THIEU im lang - dung loai bo
#: phan "ton tai nhung khong chay"). `khop_bar` di vao C qua `P_MO_HINH`.
TRUONG_TS = ("lot", "buoc", "tp", "tran_tang", "kieu_lot", "he_so_lot", "he_so_buoc", "buoc_tran", "cho_lui", "tia_lenh",
             "bien_cap", "cap_moi_bar", "chot_tien", "khop_bar",
             "cat_lo_pip", "cat_lo_tien", "thoat_gio", "nghi_gio", "gio_vao_tu", "gio_vao_den")
MO_HINH_C = {"cuc_tri": 0.0, "duong_di": 1.0}                 # = gia tri p[P_MO_HINH] trong luoi_nhan.c
TRUONG_QC = ("hop_dong", "pip", "phi_nam_mua", "phi_nam_ban")
_GHI_COT = 8
_LY_DO_DONG = ("tp", "tia", "cat", "gio")       # = ma `ly_do` cua su kien dong trong luoi_nhan.c (0 tp, 1 tia, 2 cat lo, 3 thoat gio)
_SO_STATS = 10                      # lai_gop, phi_spread, phi_swap, so_ro, so_lenh, tang_max, so_cap, con_mo, so_cat, so_gio
_TRAN_TOI_DA = 1_000_000            # tran_tang lon hon: de Python lo (khong ai chay that o day)

_khoa = threading.RLock()
_lib = None
_xong = False                       # da thu nap xong (thanh cong hay khong)
_tt = {"da_thu": False, "san_sang": False, "ly_do": "chua thu", "trinh_bien": None, "duong_dan": None,
       "giay_dich": 0.0, "giay_tu_kiem": 0.0, "nguon": None}


# ------------------------------------------------------------------ CHE DO / THU MUC
def che_do() -> str:
    v = os.environ.get("LUOI_NHAN", "auto").strip().lower()
    return v if v in ("py", "c", "auto") else "auto"


def _thu_muc_cache() -> Path:
    e = os.environ.get("LUOI_NHAN_CACHE")
    if e:
        return Path(e)
    if os.name == "nt":
        goc = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    else:
        goc = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(goc) / "the-brain" / "luoi_nhan"


def _duoi_thu_vien() -> str:
    return ".dll" if sys.platform == "win32" else (".dylib" if sys.platform == "darwin" else ".so")


def _dau_py() -> str:
    """Nhan phien ban Python trong marker tu kiem: oracle phu thuoc vao Python (sum() >= 3.12 cong bu)."""
    return "%s%d%d" % (sys.implementation.name, sys.version_info[0], sys.version_info[1])


# ------------------------------------------------------------------ DICH
def _ung_vien_trinh_bien() -> list:
    """[(ten, [lenh...], ho)] theo thu tu thu; ho = 'gcc' (gcc/clang/zig cung cu phap) | 'msvc'."""
    ds = []
    env = os.environ.get("LUOI_NHAN_CC")
    if env:
        ds.append(("env", shlex.split(env, posix=(os.name != "nt")), "gcc"))
    for ten in ("cc", "gcc", "clang"):
        p = shutil.which(ten)
        if p:
            ds.append((ten, [p], "gcc"))
    z = shutil.which("zig")
    if z:
        ds.append(("zig", [z, "cc"], "gcc"))
    try:
        if importlib.util.find_spec("ziglang") is not None:
            ds.append(("ziglang", [sys.executable, "-m", "ziglang", "cc"], "gcc"))
    except Exception:
        pass
    cl = shutil.which("cl")
    if cl:
        ds.append(("cl", [cl], "msvc"))
    return ds


def _lenh_dich(tien_to, ho, ra: Path, thu_muc_obj: Path) -> list:
    if ho == "msvc":
        return tien_to + ["/nologo", "/O2", "/LD", "/fp:precise", "/Fo" + str(thu_muc_obj) + os.sep,
                          "/Fe:" + str(ra), str(NGUON_C)]
    # KHONG -ffast-math, KHONG fma: `-ffp-contract=off` la bat buoc de khop Python tung bit
    c = tien_to + ["-O2", "-std=c99", "-shared", "-ffp-contract=off", "-fno-fast-math"]
    if sys.platform != "win32":
        c += ["-fPIC"]
    c += ["-o", str(ra), str(NGUON_C)]
    if sys.platform != "win32":
        c += ["-lm"]
    return c


def _khoa_dich(ho: str) -> str:
    """Khoa cache: noi dung nguon + ho trinh bien dich (co dich khac nhau) + nen tang. Doi nguon -> dich lai, khong dung nham ban cu."""
    h = hashlib.sha256()
    h.update(NGUON_C.read_bytes())
    h.update(("|%s|%s|%s|%d" % (ho, sys.platform, platform.machine(), PHIEN_BAN)).encode())
    return h.hexdigest()[:16]


def _dich(ten, tien_to, ho, dich_den: Path):
    """Dich nguyen tu (ghi ra thu muc tam roi doi ten). Tra (ok, thong bao)."""
    dich_den.parent.mkdir(parents=True, exist_ok=True)
    tam = Path(tempfile.mkdtemp(prefix="ln_", dir=str(dich_den.parent)))
    try:
        ra = tam / ("luoi_nhan" + _duoi_thu_vien())
        lenh = _lenh_dich(tien_to, ho, ra, tam)
        try:
            r = subprocess.run(lenh, capture_output=True, text=True, timeout=180)
        except Exception as e:
            return False, "%s: %s" % (ten, e)
        if r.returncode != 0 or not ra.exists():
            return False, "%s loi dich (ma %s): %s" % (ten, r.returncode, (r.stderr or r.stdout or "").strip()[:400])
        try:
            os.replace(str(ra), str(dich_den))
        except OSError:
            if not dich_den.exists():                           # tien trinh khac vua dat ban dich xuong (Windows khoa .dll dang nap)
                raise
        return True, "ok"
    finally:
        shutil.rmtree(tam, ignore_errors=True)


def _nap_dll(duong_dan: Path):
    lib = ctypes.CDLL(str(duong_dan))
    lib.luoi_nhan_phien_ban.restype = ctypes.c_int32
    lib.luoi_nhan_so_tham_so.restype = ctypes.c_int32
    if lib.luoi_nhan_phien_ban() != PHIEN_BAN or lib.luoi_nhan_so_tham_so() != len(_TEN_P):
        raise RuntimeError("ABI nhan C khong khop luoi_nhan.py (phien ban %s, so tham so %s)"
                           % (lib.luoi_nhan_phien_ban(), lib.luoi_nhan_so_tham_so()))
    vp = ctypes.c_void_p
    lib.luoi_mot_ro.restype = ctypes.c_int32
    lib.luoi_mot_ro.argtypes = [vp, vp, vp, vp, vp, vp, ctypes.c_int64, ctypes.c_int32, vp, vp, vp, vp, ctypes.c_int32, vp,
                                ctypes.c_int64, ctypes.POINTER(ctypes.c_int64)]       # hi lo cl spread dem tg n chieu p lai treo stats ghi_bat ghi cap n_ghi
    return lib


# ------------------------------------------------------------------ GOI NHAN (khong qua kiem tra che do)
def _kahan(ts) -> bool:
    """`sum()` Python >= 3.12 chi cong BU khi MOI phan tu la float thuan; np.float64 -> cong tuan tu (giong <= 3.11)."""
    if sys.version_info < (3, 12):
        return False
    if type(ts.lot) is not float:
        return False
    return ts.kieu_lot not in _KIEU or type(ts.he_so_lot) in (float, int)


def _dong_goi(ts, qc, chieu: int) -> np.ndarray:
    ty_le = qc.phi_nam_mua if chieu > 0 else qc.phi_nam_ban
    v = {"lot": ts.lot, "hop": qc.hop_dong, "pip": qc.pip, "buoc": ts.buoc, "tp": ts.tp, "tran": ts.tran_tang,
         "kieu": _KIEU.get(ts.kieu_lot, 0.0), "he_lot": ts.he_so_lot, "he_buoc": ts.he_so_buoc, "buoc_tran": ts.buoc_tran,
         "cho_lui": ts.cho_lui, "tia": 1.0 if ts.tia_lenh else 0.0, "bien_cap": ts.bien_cap, "cap_moi_bar": ts.cap_moi_bar,
         "chot_tien": ts.chot_tien, "ty_le": ty_le, "kahan": 1.0 if _kahan(ts) else 0.0,
         "mo_hinh": MO_HINH_C[ts.khop_bar],
         "cat_pip": ts.cat_lo_pip, "cat_tien": ts.cat_lo_tien, "thoat_gio": ts.thoat_gio, "nghi_gio": ts.nghi_gio,
         "gio_vao_tu": ts.gio_vao_tu, "gio_vao_den": ts.gio_vao_den}
    return np.array([float(v[k]) for k in _TEN_P], dtype=np.float64)


def kha_dung(ts, qc) -> bool:
    """Tham so nam trong mien da kiem cua nhan C. Ngoai mien (so la, am, vo han...) -> Python lo, y het ngu nghia cu.

    `np.float32` / `np.float16` BI LOAI: voi NumPy 2 (NEP 50) `np.float32(0.5) * 0.1` van la float32, Python se tinh do chinh xac
    thap con C tinh double -> khong the khop. `np.float64` la con cua `float` nen van qua."""
    try:
        so = [ts.lot, ts.buoc, ts.tp, ts.tran_tang, ts.he_so_lot, ts.he_so_buoc, ts.buoc_tran, ts.cho_lui, ts.bien_cap,
              ts.cap_moi_bar, ts.chot_tien, qc.hop_dong, qc.pip, qc.phi_nam_mua, qc.phi_nam_ban]
        if not all(isinstance(x, (int, float, np.integer)) and not isinstance(x, bool) and math.isfinite(x) for x in so):
            return False
        if not (ts.lot > 0 and ts.buoc > 0 and 1 <= ts.tran_tang <= _TRAN_TOI_DA and qc.pip > 0 and qc.hop_dong > 0
                and ts.cho_lui >= 0 and ts.buoc_tran >= 0 and ts.he_so_lot >= 0 and ts.he_so_buoc > 0):
            return False
        # Luy thua `he ** k`: voi float Python goi libm pow (C cung vay, khop bit). Voi so NGUYEN Python tinh chinh xac (np.int64
        # thi tran im lang) con C tinh pow(double) -> chi cho phep khi he == 1 (luy thua luon 1)
        if ts.kieu_lot == "nhan" and not isinstance(ts.he_so_lot, float) and ts.he_so_lot != 1:
            return False
        if not isinstance(ts.he_so_buoc, float) and ts.he_so_buoc != 1:
            return False
        return True
    except Exception:
        return False


def _goi(lib, hi, lo, cl, sp, dem, chieu: int, p: np.ndarray, ghi: bool, tg=None):
    """Goi nhan C mot lan. Tra (lai, treo, stats_array, events | None) hoac None neu nhan bao loi.
    `tg` = ndarray float64 lien tuc (giay epoch gio mo tung bar) hoac None (con tro NULL: nhan C chi doc khi tinh nang gio bat)."""
    n = len(cl)
    lai = np.empty(n)
    treo = np.empty(n)
    st = np.zeros(_SO_STATS)
    so_ghi = ctypes.c_int64(0)

    def gi(a):
        return a.ctypes.data

    ptr_tg = None if tg is None else gi(tg)
    if not ghi:
        rc = lib.luoi_mot_ro(gi(hi), gi(lo), gi(cl), gi(sp), gi(dem), ptr_tg, n, chieu, gi(p), gi(lai), gi(treo), gi(st), 0, None, 0,
                             ctypes.byref(so_ghi))
        return None if rc != 0 else (lai, treo, st, None)
    cap = 4096
    while True:
        buf = np.empty((cap, _GHI_COT))
        rc = lib.luoi_mot_ro(gi(hi), gi(lo), gi(cl), gi(sp), gi(dem), ptr_tg, n, chieu, gi(p), gi(lai), gi(treo), gi(st), 1, gi(buf),
                             cap, ctypes.byref(so_ghi))
        if rc != 0:
            return None
        if so_ghi.value <= cap:
            break
        cap = int(so_ghi.value) + 16            # bo dem thieu: chay lai (deterministic) voi bo dem du
    ev = []
    for r in buf[:so_ghi.value].tolist():
        if r[0] == 0.0:
            ev.append(("mo", int(r[1]), r[2], r[3], int(r[4]), int(r[5]), int(r[6])))
        else:
            ev.append(("dong", int(r[1]), r[2], int(r[4]), _LY_DO_DONG[int(r[7])]))
    return lai, treo, st, ev


def _thong_ke(st: np.ndarray) -> dict:
    return {"lai_gop": float(st[0]), "phi_spread": float(st[1]), "phi_swap": float(st[2]), "so_ro": int(st[3]),
            "so_lenh": int(st[4]), "tang_max": int(st[5]), "so_cap": int(st[6]), "con_mo": int(st[7]),
            "so_cat": int(st[8]), "so_gio": int(st[9])}


# ------------------------------------------------------------------ TU KIEM
def _kich_ban_tu_kiem():
    """Chuoi gia + qua dem CO DINH (seed co dinh): gia luoi 5 chu so (de va cham dung moc), co spread, co qua dem."""
    rng = np.random.default_rng(20261003)
    n = 900
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = 0.985 * x[i - 1] + rng.normal(0.0, 0.0011)
    cl = np.round(0.9 + x, 5)
    op = np.concatenate([[cl[0]], cl[:-1]])
    hi = np.round(np.maximum(op, cl) + np.abs(rng.normal(0.0, 0.0006, n)), 5)
    lo = np.round(np.minimum(op, cl) - np.abs(rng.normal(0.0, 0.0006, n)), 5)
    sp = np.round(0.00008 + 0.00004 * rng.random(n), 5)
    dem = np.zeros(n)
    dem[96::96] = 1.0
    dem[480::480] = 3.0
    return hi, lo, cl, sp, dem


_CA_TU_KIEM = (
    dict(buoc=20.0, tp=15.0, tran_tang=8),
    dict(buoc=25.0, tp=20.0, tran_tang=6, kieu_lot="nhan", he_so_lot=1.3),
    dict(buoc=18.0, tp=12.0, tran_tang=10, kieu_lot="cong", he_so_lot=0.5),
    dict(buoc=15.0, tp=10.0, tran_tang=9, tia_lenh=True, bien_cap=3.0, cap_moi_bar=1),
    dict(buoc=15.0, tp=30.0, tran_tang=12, tia_lenh=True, bien_cap=2.0, cap_moi_bar=999),
    dict(buoc=20.0, tp=15.0, tran_tang=8, cho_lui=10.0),
    dict(buoc=20.0, tp=15.0, tran_tang=8, chot_tien=2.0),
    dict(buoc=12.0, tp=15.0, tran_tang=14, he_so_buoc=1.2, buoc_tran=40.0),
    dict(buoc=14.0, tp=12.0, tran_tang=10, kieu_lot="nhan", he_so_lot=1.15, tia_lenh=True, bien_cap=2.5, cap_moi_bar=2,
         cho_lui=6.0, he_so_buoc=1.1, buoc_tran=60.0),
)


def _tg_tu_kiem(n: int) -> np.ndarray:
    """Giay epoch gio mo bar cua chuoi `_kich_ban_tu_kiem` (khung M15, bat dau 22:13:20 de gio trong ngay khong tron gio)."""
    return 1_700_000_000.0 + 900.0 * np.arange(n, dtype=np.float64)


#: CHI `duong_di` (co che thoat + loc gio, ABI 5). Chay tren cung chuoi gia voi `_tg_tu_kiem`, ca hai chieu, co ghi lenh. `_tu_kiem` doi hoi
#: tong so lan cat / thoat gio du lon de bo kiem khong "trong".
_CA_TU_KIEM_THOAT = (
    dict(buoc=20.0, tp=15.0, tran_tang=8, cat_lo_pip=45.0),
    dict(buoc=20.0, tp=15.0, tran_tang=8, cat_lo_tien=2.0),
    dict(buoc=25.0, tp=20.0, tran_tang=6, kieu_lot="nhan", he_so_lot=1.3, cat_lo_pip=60.0, cat_lo_tien=1.5),
    dict(buoc=15.0, tp=10.0, tran_tang=9, tia_lenh=True, bien_cap=3.0, cap_moi_bar=1, cat_lo_pip=40.0),
    dict(buoc=15.0, tp=30.0, tran_tang=12, tia_lenh=True, bien_cap=2.0, cap_moi_bar=999, kieu_lot="nhan", he_so_lot=1.4, cat_lo_tien=1.0),
    dict(buoc=20.0, tp=15.0, tran_tang=8, cho_lui=10.0, cat_lo_pip=50.0),
    dict(buoc=20.0, tp=15.0, tran_tang=8, chot_tien=2.0, cat_lo_pip=70.0, nghi_gio=1.0),
    dict(buoc=20.0, tp=15.0, tran_tang=8, thoat_gio=5.0),
    dict(buoc=20.0, tp=15.0, tran_tang=8, thoat_gio=2.0, nghi_gio=1.5, cat_lo_pip=60.0),
    dict(buoc=20.0, tp=15.0, tran_tang=8, gio_vao_tu=1.0, gio_vao_den=7.0),
    dict(buoc=20.0, tp=15.0, tran_tang=8, gio_vao_tu=22.0, gio_vao_den=5.5, cat_lo_pip=80.0),
    dict(buoc=14.0, tp=12.0, tran_tang=10, kieu_lot="nhan", he_so_lot=1.15, tia_lenh=True, bien_cap=2.5, cap_moi_bar=2,
         cho_lui=6.0, he_so_buoc=1.1, buoc_tran=60.0, cat_lo_pip=55.0, thoat_gio=8.0, nghi_gio=0.5, gio_vao_tu=20.0, gio_vao_den=11.0),
    dict(buoc=18.0, tp=12.0, tran_tang=10, kieu_lot="cong", he_so_lot=0.5, cat_lo_tien=0.8, gio_vao_tu=3.3, gio_vao_den=17.1, nghi_gio=0.75),
)


# Ca BIEN. Gia ngau nhien (du lam tron 5 chu so) gan nhu KHONG BAO GIO cham dung mot moc, nen loi `<` / `<=` (va `>` / `>=`) o moc
# do lot qua ca tu kiem lan test ngau nhien (do bang dot bien 03/10: 3 / 9 ban dot bien song sot). Gia nhi phan (1 + k/1024) la
# so chinh xac trong double: bar cham DUNG moc khop lenh / cho lui / chot tien / TP / tia. Pip = 2^-10, 1 lot = 1024 don vi, khong
# spread, khong qua dem -> moi phep tinh deu chinh xac, so BANG tung bit tren moi nen tang.
# (ten, tham so, cac bar (hi, lo, cl) tinh bang so pip tu gia 1.0, (so_ro, so_lenh, so_cap) ma Python PHAI ra)
_P_BIEN = 2.0 ** -10
_CA_BIEN = (
    # high cua bar k cham dung TP +25 pip: dong, mo lai o gia TP -> 6 vong
    ("tp_bang", dict(buoc=40.0, tp=25.0, tran_tang=4, lot=1.0),
     [(0, 0, 0)] + [(25 * k, 25 * (k - 1), 25 * k) for k in range(1, 7)], (6, 7, 0)),
    # low cua bar cham dung tung moc luoi (-40 pip): mo du 4 lenh, KHONG co lenh thu 5 (tran tang)
    ("khop_bang", dict(buoc=40.0, tp=1000.0, tran_tang=4, lot=1.0),
     [(0, 0, 0), (0, -40, -40), (-40, -80, -80), (-80, -120, -120), (-120, -120, -120)], (0, 4, 0)),
    # sau khi dong o +25, cho lui 10 pip: low cua bar 2 cham dung moc 15 -> mo lai
    ("cho_lui_bang", dict(buoc=40.0, tp=25.0, tran_tang=4, lot=1.0, cho_lui=10.0),
     [(0, 0, 0), (25, 0, 0), (25, 15, 15), (40, 15, 40), (40, 30, 30)], (2, 3, 0)),
    # lai noi tang dung 25 = chot_tien (0,25 * lot/0,01): chot ca ro
    ("chot_tien_bang", dict(buoc=40.0, tp=1000.0, tran_tang=4, lot=1.0, chot_tien=0.25),
     [(0, 0, 0), (25, 0, 0), (25, 0, 25), (50, 25, 50)], (2, 3, 0)),
    # lai cua cap dau-cuoi dung bang bien_cap * pip * (lot dau + lot cuoi) * hop: PHAI tia
    ("tia_bang", dict(buoc=4.0, tp=1000.0, tran_tang=6, lot=1.0, tia_lenh=True, bien_cap=4.0, cap_moi_bar=1),
     [(0, 0, 0), (2, -4, 0), (2, -4, 0)], (0, 5, 2)),
)


#: Khoang HUT (pip) cua cac ca `*_hut_eps`: 2^-17 = 7,6e-6 pip = 7,6 lan `luoi.EPS_CHAM_PIP`. Phai LON hon dung sai (test_luoi_nhan kiem), va la luy thua cua 2
#: de gia nhi phan van chinh xac.
_HUT = 2.0 ** -17


# Ca BIEN cua mo hinh `duong_di` (cung quy uoc nhi phan nhu tren; KHONG bar nao co dong == mo-kep, tru bar phang, de duong gia cua chieu
# ban dung la guong cua chieu mua: nen doji tinh la nen XANH cho ca hai chieu). Moi ca toi mot DAU BANG cua mot phep so sanh cua ham `lui` / `len_`:
# neu mot ben doi `>` thanh `>=` (hay nguoc lai) thi bo ba (so_ro, so_lenh, so_cap) hoac duong lai doi. Bo ba "mong" duoc suy tay (cung
# kieu voi cac ca tay cua `test_luoi_duong_di.py`) va Python PHAI ra dung no - ca nao ngung cham dung moc thi tu kiem hong ngay.
_CA_BIEN_DUONG = (
    # high cua bar k cham DUNG TP +25 pip: chot, mo lai o gia TP -> 6 vong
    ("tp_bang", dict(buoc=40.0, tp=25.0, tran_tang=4, lot=1.0),
     [(0, 0, 0)] + [(25 * k, 25 * (k - 1), 25 * k) for k in range(1, 7)], (6, 7, 0)),
    # low cua nen do cham DUNG tung moc luoi (-40 pip): mo du 4 lenh, KHONG co lenh thu 5 (tran tang)
    ("khop_bang", dict(buoc=40.0, tp=1000.0, tran_tang=4, lot=1.0),
     [(0, 0, 0), (0, -40, -40), (-40, -80, -80), (-80, -120, -120), (-120, -120, -120)], (0, 4, 0)),
    # chot o +25 roi cho lui 10 pip; bar 4 cham DUNG moc cho (30) -> mo lai
    ("cho_lui_bang", dict(buoc=40.0, tp=25.0, tran_tang=4, lot=1.0, cho_lui=10.0),
     [(0, 0, 0), (25, 0, 5), (25, 15, 20), (40, 15, 40), (40, 30, 30)], (2, 3, 0)),
    # lai noi dung 25 = chot_tien (0,25 * lot/0,01): chot ca ro o gia cham dung
    ("chot_tien_bang", dict(buoc=40.0, tp=1000.0, tran_tang=4, lot=1.0, chot_tien=0.25),
     [(0, 0, 0), (25, 0, 5), (25, 0, 25), (50, 25, 50)], (2, 3, 0)),
    # gia tia cap (+2 pip) dung bang high cua bar: PHAI tia
    ("tia_bang", dict(buoc=4.0, tp=1000.0, tran_tang=6, lot=1.0, tia_lenh=True, bien_cap=4.0, cap_moi_bar=1),
     [(0, 0, 0), (2, -4, 1), (2, -4, 0)], (0, 4, 1)),
    # gia tia == gia TP cung luc: TIA di truoc TP
    ("tia_hoa_tp", dict(buoc=4.0, tp=4.0, tran_tang=6, lot=1.0, tia_lenh=True, bien_cap=4.0, cap_moi_bar=999),
     [(0, 0, 0), (2, -4, 1)], (0, 3, 1)),
    # cap_moi_bar = 1: bar 2 co hai cap cung gia tia -> chi cap dau duoc tia (cap thu hai de bar sau)
    ("cap_moi_bar_bang", dict(buoc=4.0, tp=1000.0, tran_tang=6, lot=1.0, tia_lenh=True, bien_cap=4.0, cap_moi_bar=1),
     [(0, 0, 0), (0, -12, -12), (-2, -12, -2)], (0, 4, 1)),
    # nhay gia luc mo nen vuot HAI moc (-40, -80): chi MOT lenh o gia mo (kep -85), moc ke tiep tinh tu gia khop that (-125)
    ("nhay_gia", dict(buoc=40.0, tp=1000.0, tran_tang=6, lot=1.0),
     [(0, 0, 0), (-85, -90, -90)], (0, 2, 0)),
    # bar PHANG nhay gia vuot moc (-40): khong doan nao co do dai, chi cu "nhay gia luc mo nen" khop duoc lenh, o gia -85 (khong phai -40)
    ("phang_nhay_gia", dict(buoc=40.0, tp=1000.0, tran_tang=6, lot=1.0),
     [(0, 0, 0), (-85, -85, -85)], (0, 2, 0)),
    # chot o +25 roi cho lui 10 pip (moc cho = 15); bar 2 phang o 5 nhay gia VUOT moc cho: mo lai L1 o GIA NHAY (5), khong o moc cho (15)
    ("cho_lui_nhay_gia", dict(buoc=40.0, tp=25.0, tran_tang=4, lot=1.0, cho_lui=10.0),
     [(0, 0, 0), (25, 0, 25), (5, 5, 5)], (1, 2, 0)),
    # --- HUT MOT CHUT (08/10/2026): gia dung cach moc `_HUT` pip (= 7,6 lan dung sai `EPS_CHAM_PIP`) thi KHONG duoc tinh la cham. Hai nua cua
    # dung sai: cac ca tren (cham DUNG) bat ban bo dung sai / sai dau; cac ca nay bat ban dung sai QUA LON (nuot ca khoang hut that).
    ("khop_hut_eps", dict(buoc=40.0, tp=1000.0, tran_tang=4, lot=1.0),
     [(0, 0, 0), (0, -40 + _HUT, -40 + _HUT)], (0, 1, 0)),
    ("tp_hut_eps", dict(buoc=40.0, tp=25.0, tran_tang=4, lot=1.0),
     [(0, 0, 0), (25 - _HUT, 0, 25 - _HUT)], (0, 1, 0)),
    ("cho_lui_hut_eps", dict(buoc=40.0, tp=25.0, tran_tang=4, lot=1.0, cho_lui=10.0),
     [(0, 0, 0), (25, 0, 5), (25, 15, 20), (40, 15, 40), (40, 30 + _HUT, 30 + _HUT)], (2, 2, 0)),
)


# Ca BIEN cua CO CHE THOAT + LOC GIO (08/10/2026; cung quy uoc nhi phan, pip = 2^-10, 1 lot = 1024 don vi; moi gia tri tren luoi 2^-10 nen moi
# phep tinh chinh xac). Moi ca co them cot thoi gian `tg` (giay epoch gio mo bar) va bo ba mong doi thanh NAM so:
# (so_ro, so_lenh, so_cap, so_cat, so_gio) - SUY TAY tu luat (docstring `luoi._mot_ro_duong`), khong chay engine roi chep lai. Moi ca toi mot DAU BANG:
# doi `<` thanh `<=` (hay `>=` thanh `>`) o dung phep so sanh do thi bo nam so doi.
_CA_BIEN_THOAT = (
    # --- CAT LO ---
    # L1 o 0, cat 60 pip, buoc 40. Nen do roi toi -80: them L2 o -40 (moc them -40 truoc moc cat -60), roi moc them tang ke tiep (-80) TRUNG moc cat
    # (trung binh -20 - 60 = -80): bang nhau thi CAT truoc -> khong mo L3, dong 2 lenh lo 120 pip, mo lai L1 o -80 (3 lenh, 1 cat).
    ("cat_hoa_them", dict(buoc=40.0, tp=1000.0, tran_tang=4, lot=1.0, cat_lo_pip=60.0),
     [(0, 0, 0), (0, -80, -80)], [0.0, 900.0], (0, 3, 0, 1, 0)),
    # y het nhung day chi toi -80 + 2^-17 pip (hut mot chut): chua cham moc cat -> khong cat (2 lenh)
    ("cat_hut_eps", dict(buoc=40.0, tp=1000.0, tran_tang=4, lot=1.0, cat_lo_pip=60.0),
     [(0, 0, 0), (0, -80 + _HUT, -80 + _HUT)], [0.0, 900.0], (0, 2, 0, 0, 0)),
    # nen 2 mo cua o -90 (nhay gia vuot ca moc them -40 lan moc cat -60): cat TRUOC them tang (EA kiem cat truoc) o gia nhay -90, mo lai o -90
    ("cat_nhay_gia", dict(buoc=40.0, tp=1000.0, tran_tang=6, lot=1.0, cat_lo_pip=60.0),
     [(0, 0, 0), (0, -30, -30), (-90, -90, -90)], [0.0, 900.0, 1800.0], (0, 2, 0, 1, 0)),
    # cat 10 pip < buoc 40: moc cat luon truoc moc them. Roi -80: cat o -10, -20, ..., -80 (8 lan), moi lan mo lai o gia cat -> 9 lenh
    ("cat_day_chuyen", dict(buoc=40.0, tp=1000.0, tran_tang=6, lot=1.0, cat_lo_pip=10.0),
     [(0, 0, 0), (0, -80, -80)], [0.0, 900.0], (0, 9, 0, 8, 0)),
    # --- THOAT THEO GIO ---
    # thoat 1 gio = 3600 s; bar 4 cach luc mo ro (bar 0) DUNG 3600 s -> thoat o gia mo bar 4, mo lai (2 lenh, 1 thoat)
    ("thoat_bang", dict(buoc=40.0, tp=1000.0, tran_tang=4, lot=1.0, thoat_gio=1.0),
     [(0, 0, 0)] * 5, [0.0, 900.0, 1800.0, 2700.0, 3600.0], (0, 2, 0, 0, 1)),
    # ro CHOT TP o bar 2 va mo ro moi (luc mo = 1800 s): den bar 5 (4500 s) moi 2700 s < 3600 -> CHUA thoat. (Quen dat lai luc mo thi thoat o bar 4.)
    ("thoat_ro_moi", dict(buoc=40.0, tp=25.0, tran_tang=4, lot=1.0, thoat_gio=1.0),
     [(0, 0, 0), (0, 0, 0), (25, 0, 25), (25, 25, 25), (25, 25, 25), (25, 25, 25)], [0.0, 900.0, 1800.0, 2700.0, 3600.0, 4500.0],
     (1, 2, 0, 0, 0)),
    # --- NGHI sau cat lo ---
    # bar 1 nhay xuong -100: cat o -100 (1800 s nghi -> khong mo lai truoc 900 + 1800 = 2700 s); bar 2 (1800 s) con nghi; bar 3 (2700 s) DUNG het nghi -> vao
    ("nghi_bang", dict(buoc=40.0, tp=1000.0, tran_tang=4, lot=1.0, cat_lo_pip=60.0, nghi_gio=0.5),
     [(0, 0, 0), (-100, -100, -100), (-100, -100, -100), (-100, -100, -100)], [0.0, 900.0, 1800.0, 2700.0], (0, 2, 0, 1, 0)),
    # --- LOC GIO VAO LENH ---
    # cua so [1h, 2h): bar 0..3 (0..2700 s) ngoai cua so -> khong co ro; bar 4 (3600 s = 1h DUNG) trong cua so -> vao o gia mo bar
    ("gio_tu_bang", dict(buoc=40.0, tp=1000.0, tran_tang=4, lot=1.0, gio_vao_tu=1.0, gio_vao_den=2.0),
     [(0, 0, 0)] * 5, [0.0, 900.0, 1800.0, 2700.0, 3600.0], (0, 1, 0, 0, 0)),
    # cua so [0,5h; 1h): vao o bar 2 (1800 s), chot TP o bar 3 (2700 s, trong cua so: mo lai), chot TP o bar 4 (3600 s = 1h DUNG: het cua so) -> khong mo lai
    ("gio_den_bang", dict(buoc=40.0, tp=25.0, tran_tang=4, lot=1.0, gio_vao_tu=0.5, gio_vao_den=1.0),
     [(0, 0, 0), (0, 0, 0), (0, 0, 0), (25, 0, 25), (50, 25, 50)], [0.0, 900.0, 1800.0, 2700.0, 3600.0], (2, 2, 0, 0, 0)),
    # cua so qua nua dem [22h, 4h): bar 0 luc 21:00 ngoai; bar 1 luc 22:00 DUNG -> vao
    ("gio_dem_tu_bang", dict(buoc=40.0, tp=1000.0, tran_tang=4, lot=1.0, gio_vao_tu=22.0, gio_vao_den=4.0),
     [(0, 0, 0)] * 2, [864000.0 + 75600.0, 864000.0 + 79200.0], (0, 1, 0, 0, 0)),
    # cung cua so: bar 0 luc 02:00 trong -> vao; bar 1 luc 03:00 chot TP + mo lai; bar 2 luc 04:00 DUNG hoi het cua so: chot TP, khong mo lai
    ("gio_dem_den_bang", dict(buoc=40.0, tp=25.0, tran_tang=4, lot=1.0, gio_vao_tu=22.0, gio_vao_den=4.0),
     [(0, 0, 0), (25, 0, 25), (50, 25, 50)], [864000.0 + 7200.0, 864000.0 + 10800.0, 864000.0 + 14400.0], (2, 2, 0, 0, 0)),
    # --- GIO THAP PHAN -> GIAY: 4,1 h = 14760 s nhung 4.1 * 3600 = 14759.999999999998 trong double (do 08/10/2026; 3,3 h thi PHEP NHAN RA DUNG 11880.0, khong
    # kiem duoc gi): bo "+ 0,5" thi cat mat 1 giay. Khe giua cac bar chi 1 giay de DUNG MOT BAR nam o 14759 s / 14760 s: ban sai ra so lenh / so thoat
    # khac. Moc ngay = 864000 s (10 ngay tron, 00:00).
    # thoat 4,1 h: bar 1 cach luc mo ro 14759 s < 14760 -> CHUA thoat (ban cat-cut: 14759 >= 14759 thoat luon)
    ("thoat_thap_phan_chua_du", dict(buoc=40.0, tp=1000.0, tran_tang=4, lot=1.0, thoat_gio=4.1),
     [(0, 0, 0)] * 2, [0.0, 14759.0], (0, 1, 0, 0, 0)),
    # ... dung 14760 s -> thoat o gia mo bar, mo lai
    ("thoat_thap_phan_dung", dict(buoc=40.0, tp=1000.0, tran_tang=4, lot=1.0, thoat_gio=4.1),
     [(0, 0, 0)] * 2, [0.0, 14760.0], (0, 2, 0, 0, 1)),
    # nghi 4,1 h sau cat lo: bar 1 (900 s) cat o -20, nghi toi 900 + 14760 = 15660 s; bar 2 luc 15659 s con nghi -> KHONG vao lai (ban cat-cut: nghi toi 15659 -> vao)
    ("nghi_thap_phan", dict(buoc=40.0, tp=1000.0, tran_tang=4, lot=1.0, cat_lo_pip=20.0, nghi_gio=4.1),
     [(0, 0, 0), (0, -30, -30), (-30, -30, -30)], [0.0, 900.0, 15659.0], (0, 1, 0, 1, 0)),
    # cua so [4,1 h; 17,1 h): hai bar luc 14758 s va 14759 s deu NGOAI cua so (14760 s moi vao) -> khong co ro (ban cat-cut: 14759 s da vao)
    ("gio_tu_thap_phan", dict(buoc=40.0, tp=1000.0, tran_tang=4, lot=1.0, gio_vao_tu=4.1, gio_vao_den=17.1),
     [(0, 0, 0)] * 2, [864000.0 + 14758.0, 864000.0 + 14759.0], (0, 0, 0, 0, 0)),
    # cua so [0 h; 4,1 h): bar 0 luc 14759 s con TRONG cua so (het luc 14760 s) -> vao o bar 0 (ban cat-cut: 14759 s da het cua so -> khong vao)
    ("gio_den_thap_phan", dict(buoc=40.0, tp=1000.0, tran_tang=4, lot=1.0, gio_vao_tu=0.0, gio_vao_den=4.1),
     [(0, 0, 0)] * 2, [864000.0 + 14759.0, 864000.0 + 14760.0], (0, 1, 0, 0, 0)),
)


# Ca BIEN THAP PHAN cua `duong_di` (08/10/2026): gia 5 chu so THAT (pip = 1e-4) va moc cham DUNG tren luoi 1e-5, nhung moc tinh bang double
# (`gia - buoc * pip`, `trung binh + tp * pip`, `gia chot - cho_lui * pip`) lech ~1 ulp ve phia KHONG cham (vd 0,85 - 16 * 0,0001 ra
# 0,8483999999999999 < 0,8484 = low cua bar). Gia nhi phan o tren khong bao gio co nhieu nay nen KHONG bat duoc dung sai `EPS_CHAM_PIP`: bo no
# di thi EA / tester van khop lenh o cac o nay con engine bo lo (dung cai da gay lech mot tick o du lieu M1). Tim bang quet toan khoang gia
# 0,85..0,95; `test_luoi_nhan.py` kiem moi ca la CO nhieu that (tat dung sai di thi ra ket qua khac).
# (ten, chieu, tham so, cac bar (hi, lo, cl) tinh bang TICK 1e-5 tuyet doi, (so_ro, so_lenh, so_cap) ma Python PHAI ra)
_CA_BIEN_THAP_PHAN = (
    # mua: low cua bar 1 = 0,84840 = L1 (0,85000) - 16 pip: PHAI khop tang 2
    ("khop_mua", +1, dict(buoc=16.0, tp=1000.0, tran_tang=4, lot=0.01),
     [(85000, 85000, 85000), (85000, 84840, 84840)], (0, 2, 0)),
    # ban: high cua bar 1 = 0,85200 = L1 (0,85040) + 16 pip
    ("khop_ban", -1, dict(buoc=16.0, tp=1000.0, tran_tang=4, lot=0.01),
     [(85040, 85040, 85040), (85200, 85040, 85200)], (0, 2, 0)),
    # mua: high cua bar 1 = L1 (0,86240) + 10 pip; lot 0,07 lam gia trung binh (0,07 * g) / 0,07 lech 1 ulp: PHAI chot ro roi mo lai
    ("tp_mua", +1, dict(buoc=1000.0, tp=10.0, tran_tang=4, lot=0.07),
     [(86240, 86240, 86240), (86340, 86240, 86340)], (1, 2, 0)),
    ("tp_ban", -1, dict(buoc=1000.0, tp=10.0, tran_tang=4, lot=0.07),
     [(85030, 85030, 85030), (85030, 84930, 84930)], (1, 2, 0)),
    # mua: chot o 0,85160 (= 0,85010 + 15 pip), cho lui 8 pip -> moc cho 0,85080; low cua bar 2 cham DUNG moc do: PHAI mo lai L1
    ("cho_lui_mua", +1, dict(buoc=1000.0, tp=15.0, tran_tang=4, lot=0.01, cho_lui=8.0),
     [(85010, 85010, 85010), (85160, 85010, 85160), (85120, 85080, 85080)], (1, 2, 0)),
    ("cho_lui_ban", -1, dict(buoc=1000.0, tp=15.0, tran_tang=4, lot=0.01, cho_lui=8.0),
     [(85000, 85000, 85000), (85000, 84850, 84850), (84930, 84880, 84930)], (1, 2, 0)),
)


def _qc_thap_phan():
    """Quy cach cua `_CA_BIEN_THAP_PHAN`: pip 1e-4, 1 lot = 100000 don vi, khong phi nam."""
    from nhan import luoi as LU
    return LU.QuyCach(ma="NP10", pip=1e-4, hop_dong=100_000.0, point=1e-5, phi_nam_mua=0.0, phi_nam_ban=0.0)


def _chuoi_thap_phan(bars):
    """(hi, lo, cl, spread, dem) tu cac bar tinh bang tick 1e-5 (so nguyen / 1e5 = so double GAN NHAT voi so thap phan, y het du lieu 5 chu so doc tu file)."""
    a = np.array(bars, dtype=float) / 1e5
    n = len(a)
    return (np.ascontiguousarray(a[:, 0]), np.ascontiguousarray(a[:, 1]), np.ascontiguousarray(a[:, 2]),   # cot cua mang 2 chieu la LAT; `_goi` can lien tuc
            np.zeros(n), np.zeros(n))

def _qc_bien():
    """Quy cach nhi phan cho ca bien: pip = 2^-10, 1 lot = 1024 don vi, khong phi nam."""
    from nhan import luoi as LU
    return LU.QuyCach(ma="NP", pip=_P_BIEN, hop_dong=1024.0, point=_P_BIEN, phi_nam_mua=0.0, phi_nam_ban=0.0)


def _chuoi_bien(bars, chieu: int):
    """Chuoi gia nhi phan cho ca bien. Chieu ban = guong qua 1.0 (chinh xac, vi gia nhi phan)."""
    a = np.array(bars, dtype=float)
    hi, lo, cl = (1.0 + a[:, k] * _P_BIEN for k in range(3))
    if chieu < 0:
        hi, lo, cl = 2.0 - lo, 2.0 - hi, 2.0 - cl
    n = len(cl)
    return hi, lo, cl, np.zeros(n), np.zeros(n)


def _su_kien_khop(x, y, rtol: float, atol: float) -> bool:
    """Hai su kien ghi lenh: loai, bar, id, tang, ro, ly_do TRUNG KHIT; gia va lot theo dung sai."""
    if x[0] != y[0] or x[1] != y[1]:
        return False
    if x[0] == "mo":              # ("mo", bar, gia, lot, id, tang, ro)
        return x[4:] == y[4:] and _gan(x[2], y[2], rtol, atol) and _gan(x[3], y[3], rtol, atol)
    return x[3:] == y[3:] and _gan(x[2], y[2], rtol, atol)   # ("dong", bar, gia, id, ly_do)


def _gan(x: float, y: float, rtol: float, atol: float) -> bool:
    """x ~ y theo dung sai; hai NaN coi la BANG (du lieu co NaN thi ca hai ban phai ra NaN o dung cho)."""
    if x != x and y != y:
        return True
    return math.isclose(x, y, rel_tol=rtol, abs_tol=atol)


def _lech_max(x: np.ndarray, y: np.ndarray) -> float:
    d = np.abs(np.asarray(x, float) - np.asarray(y, float))
    d = d[np.isfinite(d)]
    return float(d.max()) if d.size else float("nan")


def so_sanh_ket_qua(a, b, rtol: float = 1e-9, atol: float = 1e-9):
    """So `(lai, treo, stats, ghi)` cua Python va C. Tra (ok, mo ta). Chuoi lenh + so nguyen phai TRUNG KHIT; so thuc theo dung sai
    (NaN o cung vi tri coi la bang)."""
    la, ta, sa, ga = a
    lb, tb, sb, gb = b
    for ten in ("so_ro", "so_lenh", "tang_max", "so_cap", "con_mo", "so_cat", "so_gio"):
        if int(sa.get(ten, 0)) != int(sb.get(ten, 0)):
            return False, "%s: py=%s c=%s" % (ten, sa.get(ten, 0), sb.get(ten, 0))
    if not (np.allclose(la, lb, rtol=rtol, atol=atol, equal_nan=True)
            and np.allclose(ta, tb, rtol=rtol, atol=atol, equal_nan=True)):
        return False, "duong lai/treo lech (max %.3g)" % max(_lech_max(la, lb), _lech_max(ta, tb))
    for ten in ("lai_gop", "phi_spread", "phi_swap"):
        if not _gan(float(sa[ten]), float(sb[ten]), rtol, atol):
            return False, "%s: py=%r c=%r" % (ten, sa[ten], sb[ten])
    if ga is not None or gb is not None:
        if ga is None or gb is None or len(ga) != len(gb):
            return False, "so su kien ghi lenh: py=%s c=%s" % (None if ga is None else len(ga), None if gb is None else len(gb))
        for k, (x, y) in enumerate(zip(ga, gb)):
            if not _su_kien_khop(x, y, rtol, atol):
                return False, "su kien %d khac: py=%r c=%r" % (k, x, y)
    return True, "ok"


def _tu_kiem(lib):
    """Chay nhan C va ban Python chuan (`luoi.mot_ro_chuan`) tren cung kich ban co dinh, CA HAI mo hinh bar, ca hai chieu, co ghi lenh.
    Tra (ok, mo ta)."""
    from nhan import luoi as LU
    hi, lo, cl, sp, dem = _kich_ban_tu_kiem()
    qc = LU.QC_AUDCAD
    tong_ev = {}
    for mh in LU.MO_HINH_BAR:
        tong_ev[mh] = 0
        for k, kw in enumerate(_CA_TU_KIEM):
            ts = LU.ThamSo(**kw, khop_bar=mh)
            for chieu in (1, -1):
                ev: list = []
                lai, treo, tk = LU.mot_ro_chuan(hi, lo, cl, sp, dem, chieu, ts, qc, ev)
                r = _goi(lib, hi, lo, cl, sp, dem, chieu, _dong_goi(ts, qc, chieu), True)
                if r is None:
                    return False, "nhan C bao loi o %s ca %d chieu %+d" % (mh, k, chieu)
                ok, mo_ta = so_sanh_ket_qua((lai, treo, tk, ev), (r[0], r[1], _thong_ke(r[2]), r[3]))
                if not ok:
                    return False, "%s ca %d chieu %+d: %s" % (mh, k, chieu, mo_ta)
                tong_ev[mh] += len(ev)
        if tong_ev[mh] < 200:
            return False, "kich ban tu kiem qua thua o %s (%d su kien) - khong du tin cay" % (mh, tong_ev[mh])
    tg = _tg_tu_kiem(len(cl))
    so_cat = so_gio = su_kien_thoat = 0
    for k, kw in enumerate(_CA_TU_KIEM_THOAT):                            # co che thoat + loc gio: chi `duong_di`, tren cung chuoi gia + cot gio
        ts = LU.ThamSo(**kw, khop_bar="duong_di")
        for chieu in (1, -1):
            ev = []
            lai, treo, tk = LU.mot_ro_chuan(hi, lo, cl, sp, dem, chieu, ts, qc, ev, tg)
            r = _goi(lib, hi, lo, cl, sp, dem, chieu, _dong_goi(ts, qc, chieu), True, tg)
            if r is None:
                return False, "nhan C bao loi o ca thoat %d chieu %+d" % (k, chieu)
            ok, mo_ta = so_sanh_ket_qua((lai, treo, tk, ev), (r[0], r[1], _thong_ke(r[2]), r[3]))
            if not ok:
                return False, "ca thoat %d chieu %+d: %s" % (k, chieu, mo_ta)
            so_cat += int(tk["so_cat"])
            so_gio += int(tk["so_gio"])
            su_kien_thoat += len(ev)
    if so_cat < 100 or so_gio < 20:                     # bo kiem khong cham toi cat lo / thoat gio thi khong chung minh gi
        return False, "kich ban tu kiem co che thoat qua thua (%d cat, %d thoat gio) - khong du tin cay" % (so_cat, so_gio)
    qc_bien = _qc_bien()
    for ten, kw, bars, tg_s, mong in _CA_BIEN_THOAT:
        ts = LU.ThamSo(**kw, khop_bar="duong_di")
        tg_a = np.asarray(tg_s, dtype=np.float64)
        for chieu in (1, -1):
            hi, lo, cl, sp, dem = _chuoi_bien(bars, chieu)
            ev = []
            lai, treo, tk = LU.mot_ro_chuan(hi, lo, cl, sp, dem, chieu, ts, qc_bien, ev, tg_a)
            thuc = (int(tk["so_ro"]), int(tk["so_lenh"]), int(tk["so_cap"]), int(tk["so_cat"]), int(tk["so_gio"]))
            if thuc != mong:                                                # Python doi nghia: ca nay khong con cham dung moc
                return False, "ca bien thoat %s chieu %+d: Python ra %s, ky vong %s" % (ten, chieu, thuc, mong)
            r = _goi(lib, hi, lo, cl, sp, dem, chieu, _dong_goi(ts, qc_bien, chieu), True, tg_a)
            if r is None:
                return False, "nhan C bao loi o ca bien thoat %s chieu %+d" % (ten, chieu)
            ok, mo_ta = so_sanh_ket_qua((lai, treo, tk, ev), (r[0], r[1], _thong_ke(r[2]), r[3]), 0.0, 0.0)
            if not ok:
                return False, "ca bien thoat %s chieu %+d: %s" % (ten, chieu, mo_ta)
    for mh, bang in (("cuc_tri", _CA_BIEN), ("duong_di", _CA_BIEN_DUONG)):
        for ten, kw, bars, mong in bang:
            ts = LU.ThamSo(**kw, khop_bar=mh)
            for chieu in (1, -1):
                hi, lo, cl, sp, dem = _chuoi_bien(bars, chieu)
                ev = []
                lai, treo, tk = LU.mot_ro_chuan(hi, lo, cl, sp, dem, chieu, ts, qc_bien, ev)
                thuc = (int(tk["so_ro"]), int(tk["so_lenh"]), int(tk["so_cap"]))
                if thuc != mong:                # Python doi nghia: ca nay khong con cham dung moc -> khong con gia tri kiem
                    return False, "ca bien %s/%s chieu %+d: Python ra %s, ky vong %s" % (mh, ten, chieu, thuc, mong)
                r = _goi(lib, hi, lo, cl, sp, dem, chieu, _dong_goi(ts, qc_bien, chieu), True)
                if r is None:
                    return False, "nhan C bao loi o ca bien %s/%s chieu %+d" % (mh, ten, chieu)
                ok, mo_ta = so_sanh_ket_qua((lai, treo, tk, ev), (r[0], r[1], _thong_ke(r[2]), r[3]), 0.0, 0.0)   # chinh xac: khong dung sai
                if not ok:
                    return False, "ca bien %s/%s chieu %+d: %s" % (mh, ten, chieu, mo_ta)
    qc_tp = _qc_thap_phan()
    for ten, chieu, kw, bars, mong in _CA_BIEN_THAP_PHAN:                # gia thap phan: dung sai cham moc (chi `duong_di` co)
        ts = LU.ThamSo(**kw, khop_bar="duong_di")
        hi, lo, cl, sp, dem = _chuoi_thap_phan(bars)
        ev = []
        lai, treo, tk = LU.mot_ro_chuan(hi, lo, cl, sp, dem, chieu, ts, qc_tp, ev)
        thuc = (int(tk["so_ro"]), int(tk["so_lenh"]), int(tk["so_cap"]))
        if thuc != mong:
            return False, "ca thap phan %s: Python ra %s, ky vong %s" % (ten, thuc, mong)
        r = _goi(lib, hi, lo, cl, sp, dem, chieu, _dong_goi(ts, qc_tp, chieu), True)
        if r is None:
            return False, "nhan C bao loi o ca thap phan %s" % ten
        ok, mo_ta = so_sanh_ket_qua((lai, treo, tk, ev), (r[0], r[1], _thong_ke(r[2]), r[3]), 0.0, 0.0)
        if not ok:
            return False, "ca thap phan %s: %s" % (ten, mo_ta)
    return True, "khop %d ca x 2 mo hinh x 2 chieu (%s su kien) + %d ca thoat (%d cat, %d thoat gio) + %d ca bien (+%d thoat) + %d ca thap phan" % (
        len(_CA_TU_KIEM), "/".join(str(tong_ev[m]) for m in LU.MO_HINH_BAR), len(_CA_TU_KIEM_THOAT), so_cat, so_gio,
        len(_CA_BIEN) + len(_CA_BIEN_DUONG), len(_CA_BIEN_THOAT), len(_CA_BIEN_THAP_PHAN))


def _dau_ban_kiem() -> str:
    """Van tay cua CHINH BO TU KIEM (bang ca + ma cac ham kiem), nam trong ten marker 'da kiem': them / sua mot ca bien thi marker cu het gia tri.
    Thieu cai nay thi nhan da dich + da kiem bang bo cu se BO QUA ca moi - bo kiem moi khong bao gio chay tren may da co cache (08/10/2026:
    phat hien khi them ca thap phan cua `EPS_CHAM_PIP` ma khong doi nguon .c)."""
    h = hashlib.sha256()
    for ten in ("_CA_TU_KIEM", "_CA_TU_KIEM_THOAT", "_CA_BIEN", "_CA_BIEN_DUONG", "_CA_BIEN_THOAT", "_CA_BIEN_THAP_PHAN", "_HUT"):
        h.update(repr(globals()[ten]).encode())
    for f in (_tu_kiem, _kich_ban_tu_kiem, _tg_tu_kiem, _chuoi_bien, _chuoi_thap_phan, _qc_bien, _qc_thap_phan, so_sanh_ket_qua, _su_kien_khop):
        try:
            h.update(inspect.getsource(f).encode())
        except (OSError, TypeError):                              # khong doc duoc ma nguon (chi co .pyc): van tay chi con bang ca
            h.update(b"?")
    return h.hexdigest()[:8]


# ------------------------------------------------------------------ NAP (mot lan moi tien trinh)
def _kiem_va_nhan(lib, marker: Path, ten: str, thu_vien: Path, loi: list) -> bool:
    """Neu `lib` chua co marker cho Python nay thi tu kiem. Dat `_lib` / `_tt` khi dat. Khong dat thi ghi `loi`, xoa ban lech."""
    global _lib
    if marker.exists():
        _lib = lib
        _tt.update(san_sang=True, ly_do="ok (da kiem truoc do)", trinh_bien=ten, duong_dan=str(thu_vien))
        return True
    t1 = time.perf_counter()
    ok, mo_ta = _tu_kiem(lib)
    _tt["giay_tu_kiem"] = round(time.perf_counter() - t1, 3)
    if ok:
        try:
            marker.write_text(mo_ta + "\n", encoding="utf-8")
        except OSError:
            pass
        _lib = lib
        _tt.update(san_sang=True, ly_do="ok (%s)" % mo_ta, trinh_bien=ten, duong_dan=str(thu_vien))
        return True
    loi.append("%s: TU KIEM KHONG KHOP - %s" % (ten, mo_ta))
    try:
        thu_vien.unlink()                       # khong tin ban nay nua: de khong ai dung nham ban lech
    except OSError:
        pass
    return False


def _thu_nap():
    """Tim / dich / tu kiem nhan C. Dat `_lib` va `_tt`. Goi duoi khoa."""
    _tt.update(da_thu=True, san_sang=False, ly_do="", nguon=str(NGUON_C))
    if not NGUON_C.exists():
        _tt["ly_do"] = "thieu luoi_nhan.c"
        return
    cache = _thu_muc_cache()
    loi: list = []
    # 1. ban da dich san (khoa theo NGUON + ho trinh bien), kiem lai neu chua kiem cho Python nay
    for ho in ("gcc", "msvc"):
        khoa = _khoa_dich(ho)
        thu_vien = cache / ("luoi_nhan_%s%s" % (khoa, _duoi_thu_vien()))
        if not thu_vien.exists():
            continue
        try:
            lib = _nap_dll(thu_vien)
        except Exception as e:                                   # tep hong / ABI cu
            loi.append("%s: nap that bai (%s)" % (thu_vien.name, e))
            try:
                thu_vien.unlink()
            except OSError:
                pass
            continue
        if _kiem_va_nhan(lib, cache / ("luoi_nhan_%s.ok_%s_%s" % (khoa, _dau_py(), _dau_ban_kiem())), "cache", thu_vien, loi):
            return
    # 2. dich moi bang tung trinh bien dich co san
    ung_vien = _ung_vien_trinh_bien()
    if not ung_vien and not loi:
        _tt["ly_do"] = "khong co trinh bien dich (cc/gcc/clang/zig/ziglang/cl) - chay Python"
        return
    for ten, tien_to, ho in ung_vien:
        khoa = _khoa_dich(ho)
        thu_vien = cache / ("luoi_nhan_%s%s" % (khoa, _duoi_thu_vien()))
        t0 = time.perf_counter()
        ok, tb = _dich(ten, tien_to, ho, thu_vien)
        _tt["giay_dich"] = round(time.perf_counter() - t0, 3)
        if not ok:
            loi.append(tb)
            continue
        try:
            lib = _nap_dll(thu_vien)
        except Exception as e:
            loi.append("%s: nap that bai (%s)" % (ten, e))
            continue
        if _kiem_va_nhan(lib, cache / ("luoi_nhan_%s.ok_%s_%s" % (khoa, _dau_py(), _dau_ban_kiem())), ten, thu_vien, loi):
            return
    _tt["ly_do"] = "; ".join(loi) if loi else "khong dung duoc nhan C - chay Python"


def lay_nhan():
    """ctypes lib da nap + da tu kiem, hoac None (chay Python). Thu mot lan moi tien trinh; nhanh va khong khoa o lan sau."""
    global _lib, _xong
    m = che_do()
    if m == "py":
        return None
    if not _xong:
        with _khoa:
            if not _xong:
                try:
                    _thu_nap()
                except Exception as e:                           # khong de nhan C keo chet engine
                    _lib = None
                    _tt.update(da_thu=True, san_sang=False, ly_do="loi bat ngo: %r" % (e,))
                _xong = True
    if _lib is None and m == "c":
        raise RuntimeError("LUOI_NHAN=c nhung nhan C khong dung duoc: %s" % _tt["ly_do"])
    return _lib


def lam_lai():
    """Quen trang thai da nap (dung cho test / sau khi doi bien moi truong)."""
    global _lib, _xong
    with _khoa:
        _lib = None
        _xong = False
        _tt.update(da_thu=False, san_sang=False, ly_do="chua thu", trinh_bien=None, duong_dan=None, giay_dich=0.0,
                   giay_tu_kiem=0.0)


def trang_thai() -> dict:
    """Mo ta nhan C hien tai (thu nap neu chua)."""
    try:
        lay_nhan()
    except RuntimeError:
        pass
    d = dict(_tt)
    d["che_do"] = che_do()
    d["python"] = sys.version.split()[0]
    return d


# ------------------------------------------------------------------ GIAO DIEN CHO luoi.chay
def mot_ro(hi, lo, cl, spread_gia, dem, chieu: int, ts, qc=None, ghi=None, tg=None):
    """Thay the `luoi.mot_ro_chuan` (cung chu ky, cung gia tri tra ve, mo hinh theo `ts.khop_bar`) hoac tra None neu khong dung nhan C duoc.

    None nghia la "hay chay Python": che do py, khong co nhan, tham so ngoai mien da kiem, mang dau vao khong phai ndarray float64.
    Du lieu co NaN / inf: nhan C tu choi (bao loi) -> cung ve None -> ban Python chuan nem ValueError (`duong_di`).
    `tg` = giay epoch gio mo tung bar (ndarray float64, cung do dai chuoi gia): chi can khi `ts` dung thoat_gio / nghi_gio / gio_vao_*;
    thieu hoac sai dang -> None (Python bao ValueError ro rang). Co che thoat + loc gio chi co o `duong_di`: `cuc_tri` + tinh nang bat -> None
    (Python tu choi).
    """
    lib = lay_nhan()
    if lib is None:
        return None
    if qc is None:
        from nhan.luoi import QC_AUDCAD
        qc = QC_AUDCAD
    for a in (hi, lo, cl, spread_gia, dem):
        # np.float64 trong Python cho `sum` cong tuan tu; list float thuan thi KHONG -> khong the khop bit, de Python lo
        if not isinstance(a, np.ndarray) or a.dtype != np.float64 or a.ndim != 1:
            return None
    if not (len(hi) == len(lo) == len(cl) == len(spread_gia) == len(dem)) or len(cl) < 1 or chieu not in (1, -1):
        return None
    if getattr(ts, "khop_bar", None) not in MO_HINH_C:           # ten la -> de Python (mot_ro_chuan) bao ValueError ro rang
        return None
    if not kha_dung(ts, qc):
        return None
    from nhan import luoi as LU
    tg_c = None
    if ts.khop_bar == "duong_di":
        if LU.mien_duong_di(ts, qc):                              # ngoai mien `duong_di` (tp <= 0, ...): Python nem ValueError
            return None
        if LU.can_cot_thoi_gian(ts):
            if not isinstance(tg, np.ndarray) or tg.dtype != np.float64 or tg.ndim != 1 or len(tg) != len(cl):
                return None                                       # thieu / sai dang cot thoi gian: Python bao ValueError
            if not np.isfinite(tg).all():
                return None
            tg_c = np.ascontiguousarray(tg)
    elif LU.tinh_nang_duong_di_dang_bat(ts):                      # `cuc_tri` khong cai dat co che thoat / loc gio: Python tu choi
        return None
    hi, lo, cl, spread_gia, dem = (np.ascontiguousarray(a) for a in (hi, lo, cl, spread_gia, dem))
    r = _goi(lib, hi, lo, cl, spread_gia, dem, int(chieu), _dong_goi(ts, qc, chieu), ghi is not None, tg_c)
    if r is None:
        return None
    lai, treo, st, ev = r
    if ghi is not None:
        ghi.extend(ev)
    return lai, treo, _thong_ke(st)


# ------------------------------------------------------------------ DO TOC DO
def do_toc_do(so_bar: int = 60_000, lap: int = 3) -> dict:
    """Do us/bar cua Python va C tren chuoi gia lap, cho TUNG mo hinh bar (CHUA phai toc do tren du lieu that; de so sanh tuong doi).
    Khoa chinh `python_us_bar` / `c_us_bar` = mo hinh MAC DINH (`duong_di`); `cuc_tri` nam o khoa cung ten."""
    from nhan import luoi as LU
    rng = np.random.default_rng(7)
    n = int(so_bar)
    x = np.cumsum(rng.normal(0.0, 0.0004, n)) * 0.2 + 0.9
    cl = np.round(x, 5)
    hi = np.round(cl + np.abs(rng.normal(0.0, 0.0003, n)), 5)
    lo = np.round(cl - np.abs(rng.normal(0.0, 0.0003, n)), 5)
    sp = np.full(n, 0.0001)
    dem = np.zeros(n)
    dem[96::96] = 1.0
    qc = LU.QC_AUDCAD
    lib = lay_nhan() if che_do() != "py" else None
    out = {"so_bar": n}
    for mh in ("duong_di", "cuc_tri"):
        ts = LU.ThamSo(buoc=30.0, tp=25.0, tran_tang=12, khop_bar=mh)
        t = []
        for _ in range(max(1, lap)):
            t0 = time.perf_counter()
            LU.mot_ro_chuan(hi, lo, cl, sp, dem, 1, ts, qc)
            t.append(time.perf_counter() - t0)
        d = {"python_us_bar": round(min(t) / n * 1e6, 3)}
        if lib is None:
            d["c_us_bar"] = None
            d["ly_do"] = _tt["ly_do"]
        else:
            t = []
            for _ in range(max(1, lap) + 2):
                t0 = time.perf_counter()
                mot_ro(hi, lo, cl, sp, dem, 1, ts, qc)
                t.append(time.perf_counter() - t0)
            d["c_us_bar"] = round(min(t) / n * 1e6, 4)
            d["nhanh_hon_lan"] = round(d["python_us_bar"] / d["c_us_bar"], 1)
        if mh == "duong_di":
            out.update(d)
        else:
            out["cuc_tri"] = d
    return out


def _main(argv):
    lenh = argv[1] if len(argv) > 1 else "trang-thai"
    if lenh in ("do", "bench"):
        print(json.dumps(do_toc_do(int(argv[2]) if len(argv) > 2 else 60_000), ensure_ascii=False, indent=1))
        return 0
    if lenh in ("dich", "lam-lai"):
        lam_lai()
    d = trang_thai()
    print(json.dumps(d, ensure_ascii=False, indent=1))
    return 0 if d.get("san_sang") else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
