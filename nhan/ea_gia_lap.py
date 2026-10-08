# -*- coding: utf-8 -*-
"""ea_gia_lap.py - CHAY CHINH MA .mq5 cua mot EA tren SAN GIA (`nhan/ea_gia_lap.cpp`), khong can MT5.

Vi sao co: EA viet o cloud (`ea_LuoiDayDu.mq5`) khong co MetaEditor / tester o day, ma may nha chi bat rat ngan vi tien dien -
EA phai dung y NGAY LAN DAU ra tester. Thay vi port tay sang Python (mot ban dich thu hai co the dung trong khi file .mq5 sai), vo C++
bien dich CHINH van ban .mq5 (bo `#property` / `#include`, giu nguyen so dong) cung lop gia lap API MQL5 + san gia hedging theo tung tick:
moi tick -> TP may chu (MUA dong khi Bid >= TP, BAN dong khi Ask <= TP) -> `OnTick()`. MUA khop o ASK, BAN khop o BID.

NO TRA LOI: "logic EA co dung y khong" - so lenh, gia mo, lot, tia, TP co khop engine `nhan/luoi.py` tren cung duong gia khong;
cu phap C++ cua file (+ viec EA co gan gia tri cho `input` - MQL5 cam - bang lan bien dich `input` = const).
NO KHONG TRA LOI: "MT5 that se cho gi" (cu phap rieng cua MQL5, `CTrade` that, tick that, spread that, swap, margin) - viec do cua
tester o may nha (`tai_lieu/LAN_EA_THO.md`, 5 diem chua hieu chuan).

Dung:  exe = bien_dich("ea_LuoiDayDu.mq5");  tk = tick_tu_bar(df, "thap_truoc");  kq = chay(exe, tk, 10000, {"InpStepPips": 21, ...})

DOI CHIEU VOI ENGINE (`doi_chieu`): moi tick = mot bar cho `luoi.chay` (engine thay DUNG duong gia ma EA thay) -> hai ben khop
TUNG LENH (tick mo / tick dong, chieu, lot, gia mo +-1 buoc) voi moi cau hinh da thu (lot phang / nhan / cong, buoc gian / co,
tia lenh, cho lui, chot tien, hai chieu). LAI khop sau hai khoan da biet (xem `KetQuaDoiChieu`):
  1. engine tru spread luc MO cua MOI lenh, ke ca lenh chua dong - so du MT5 chua ghi no -> `lai_ea` tru `spread_con_mo`;
  2. engine tru THEM mot spread khi dong cap tia (`luoi.py` `phi_sp += spread * (l_dau + l_cuoi)`) - EA / MT5 khong co phi do.
KHAC voi chay tren bar OHLC that (`do_lech_bar`): engine dong cap tia / chot_tien o gia TOT NHAT cua bar, EA dong o gia vua cham
nguong - tren nen M15 gia lap engine cao hon EA ~16% o tn5 (tai lieu: `tai_lieu/LAN_EA_THO.md` muc EA luoi day du).
"""
from __future__ import annotations

import dataclasses
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from nhan import ea_tho as EA

NGUON_CPP = Path(__file__).with_name("ea_gia_lap.cpp")
TEN_BIEN_DICH = ("c++", "g++", "clang++")
POINT = 1e-5

#: Truong `luoi.ThamSo` -> input cua `ea_LuoiDayDu.mq5`. Test `test_ea_luoi_day_du` bat truong moi cua engine ma chua co o day
#: (kieu loi "bo phan co ton tai nhung khong nam tren duong chay").
BANG_TEN = {
    "lot": "InpLot", "buoc": "InpStepPips", "tp": "InpTpPips", "tran_tang": "InpMaxLevels", "che_do": "InpMode",
    "he_so_lot": "InpLotMult", "kieu_lot": "InpLotKind", "he_so_buoc": "InpStepMult", "buoc_tran": "InpStepCap",
    "tia_lenh": "InpSpark", "bien_cap": "InpSparkPips", "cap_moi_bar": "InpSparkPerBar", "cho_lui": "InpWaitBack",
    "chot_tien": "InpTakeMoney",
}
#: Truong engine KHONG co input tuong ung, va ly do: la thu cua TAI KHOAN / san, hoac engine chua cai dat.
KHONG_CO_TRONG_EA = {
    "muc_stopout": "stop-out la cua nha mo gioi (engine mo phong chet tai khoan)",
    "don_bay": "don bay la cua tai khoan; EA khong dat",
    "dung_lo_tong": "engine CHUA cai dat (luoi.CHUA_CAI_DAT) nen EA cung khong",
    "khop_bar": "chi la CACH MO PHONG bar cua engine (luoi.MO_HINH_BAR); EA chay theo tick that nen khong co input",
}
_CHE_DO = {"mua": 0, "ban": 1, "hai_chieu": 2}
_KIEU_LOT = {"phang": 0, "nhan": 1, "cong": 2}


class LoiBienDich(RuntimeError):
    """g++ khong bien dich duoc: `args[0]` la dau ra loi (dong trong van ban EA = dong trong file .mq5)."""


def tham_so_ea_tu_luoi(ts) -> dict:
    """`luoi.ThamSo` (hoac dict cung ten truong) -> tham_so cho `ea_LuoiDayDu.mq5`. Truong la -> ValueError, KHONG bo qua im lang;
    `dung_lo_tong != 0` -> ValueError (engine cung tu choi)."""
    d = dataclasses.asdict(ts) if dataclasses.is_dataclass(ts) else dict(ts)
    ra = {}
    for k, v in d.items():
        if k in KHONG_CO_TRONG_EA:
            if k == "dung_lo_tong" and v:
                raise ValueError("dung_lo_tong != 0: luoi.py chua cai dat nen EA cung khong co")
            continue
        if k not in BANG_TEN:
            raise ValueError("truong ThamSo '%s' chua co input trong EA (them vao BANG_TEN va EA truoc)" % k)
        if k == "che_do":
            v = _CHE_DO[v]
        elif k == "kieu_lot":
            v = _KIEU_LOT[v]
        elif k == "tia_lenh":
            v = 1 if v else 0
        ra[BANG_TEN[k]] = v
    return ra


# ------------------------------------------------------------------ bien dich
def trinh_bien_dich() -> str | None:
    env = os.environ.get("EA_GIA_LAP_CXX")
    for ten in ([env] if env else []) + list(TEN_BIEN_DICH):
        p = shutil.which(ten)
        if p:
            return p
    return None


_PP = re.compile(r"^\s*#\s*(property|include)\b(.*)$")


def bo_property(ma: str) -> str:
    """Bo `#property` va `#include <Trade/Trade.mqh>` (thay bang dong trong de GIU so dong). Include khac -> ValueError."""
    ra = []
    for dong in ma.splitlines():
        m = _PP.match(dong)
        if m:
            if m.group(1) == "include" and "Trade/Trade.mqh" not in m.group(2):
                raise ValueError("EA co #include la (%s): san gia chi co Trade/Trade.mqh" % m.group(2).strip())
            ra.append("")
        else:
            ra.append(dong)
    return "\n".join(ra) + "\n"


def bien_dich(duong_mq5, chi_cu_phap: bool = False, thu_muc=None) -> Path | None:
    """Bien dich EA + san gia -> duong dan file chay (cache theo van tay ma). `chi_cu_phap=True`: bien `input` thanh const va CHI kiem
    cu phap (tra None). Khong co trinh bien dich -> None khong loi (nguoi goi tu bo qua). Loi bien dich -> `LoiBienDich`."""
    cxx = trinh_bien_dich()
    if not cxx:
        return None
    ma = bo_property(Path(duong_mq5).read_text(encoding="utf-8"))
    ten = sorted(EA.input_khai_bao(ma))
    cpp = NGUON_CPP.read_text(encoding="utf-8")
    h = hashlib.sha1((cpp + "\0" + ma + "\0" + cxx + "\0%d" % chi_cu_phap).encode("utf-8")).hexdigest()[:16]
    goc = Path(thu_muc) if thu_muc else Path(tempfile.gettempdir()) / "ea_gia_lap" / h
    goc.mkdir(parents=True, exist_ok=True)
    exe = goc / "ea_gia_lap.exe"
    if not chi_cu_phap and exe.exists():
        return exe
    (goc / "ea_pp.inc").write_text(ma, encoding="utf-8")
    (goc / "registry.inc").write_text("".join("X(%s)\n" % t for t in ten), encoding="utf-8")
    lenh = [cxx, "-std=c++17", "-Wall", "-Wno-unused-function", '-DEA_FILE="%s"' % (goc / "ea_pp.inc").as_posix(),
            '-DREGISTRY_FILE="%s"' % (goc / "registry.inc").as_posix(), str(NGUON_CPP)]
    lenh += ["-DGIA_LAP_CHI_CU_PHAP", "-fsyntax-only"] if chi_cu_phap else ["-O2", "-o", str(exe)]
    p = subprocess.run(lenh, capture_output=True, text=True)
    if p.returncode != 0:
        raise LoiBienDich(p.stderr[-4000:])
    return None if chi_cu_phap else exe


# ------------------------------------------------------------------ duong gia: bar OHLC -> tick
def tick_tu_bar(df: pd.DataFrame, thu_tu="thap_truoc", point: float = POINT, giay_bar: float = 900.0, paso=None) -> dict:
    """Moi bar (open, high, low, close, spread[point]) -> chuoi tick BUOC `paso` (mac dinh = `point`): open -> cuc tri thu nhat ->
    cuc tri thu hai -> close.

    `thu_tu`: 'thap_truoc' (thap roi cao - dung gia dinh BAT LOI TRUOC cua engine voi lenh MUA), 'cao_truoc' (voi lenh BAN),
    'xen_ke' (bar chan thap truoc, bar le cao truoc), 'theo_nen' (nen tang: thap truoc; nen giam: cao truoc).
    Gia bar PHAI nam tren luoi `point`; `paso` nho hon `point` (uoc so nguyen cua nhau) cho chuoi tick MIN hon luoi gia bar.
    Tra dict mang: bid, spread (GIA), time (giay), bar (giay bat dau nen), bar_idx."""
    o, h, l, c = (np.rint(df[k].to_numpy(float) / point).astype(np.int64) for k in ("open", "high", "low", "close"))
    paso = float(paso or point)
    k = int(round(point / paso))
    if k < 1 or abs(k * paso - point) > 1e-12 * point:
        raise ValueError("paso phai la uoc so nguyen cua point (point=%r paso=%r)" % (point, paso))
    sp = df["spread"].to_numpy(float) * point if "spread" in df.columns else np.zeros(len(df))
    t0 = df.index.values.astype("datetime64[s]").astype(np.int64).astype(np.float64)   # an toan voi moi don vi thoi gian (ns / us)
    bid, spr, tm, bar, bidx = [], [], [], [], []

    def nac(a, b):
        n = int(b - a)
        return a + np.sign(n) * np.arange(1, abs(n) + 1) if n else np.empty(0, np.int64)

    for i in range(len(df)):
        if thu_tu == "thap_truoc" or (thu_tu == "xen_ke" and i % 2 == 0) or (thu_tu == "theo_nen" and c[i] >= o[i]):
            p1, p2 = l[i] * k, h[i] * k
        else:
            p1, p2 = h[i] * k, l[i] * k
        pts = np.concatenate([[o[i] * k], nac(o[i] * k, p1), nac(p1, p2), nac(p2, c[i] * k)])
        n = len(pts)
        bid.append(pts * paso)
        spr.append(np.full(n, sp[i]))
        tm.append(t0[i] + np.arange(n) * (giay_bar / n))
        bar.append(np.full(n, t0[i]))
        bidx.append(np.full(n, i, np.int64))
    return dict(bid=np.concatenate(bid), spread=np.concatenate(spr), time=np.concatenate(tm), bar=np.concatenate(bar),
                bar_idx=np.concatenate(bidx))


def barra_tu_tick(tk: dict, point: float = POINT, nhieu: float = 1e-9) -> pd.DataFrame:
    """MOI TICK = MOT BAR (open = close = bid; high = bid + nhieu, low = bid - nhieu) de `luoi.chay` nhin DUNG duong gia ma EA thay:
    khong con khoang mu trong bar (thu tu cao / thap, mo lai o gia dong bar, TP tinh o cao nhat). Day la cach doi chieu logic
    EA <-> engine ma khong lan voi chuyen "bar OHLC khac tick" (chuyen sau do rieng).

    `nhieu`: MT5 va EA tinh cham DUNG muc (bid = TP, bid = moc tang) la TRUNG; engine so sanh so thuc nen nhieu dau phay dong
    (0,89879999 < 0,8988) co the bo sot. Nong cao / thap them `nhieu` (mac dinh 1e-9: nho hon moi buoc tick 1e-6 den 1e-3 lan) de hai ben cung quy tac."""
    b = np.asarray(tk["bid"], float)
    idx = pd.to_datetime(np.rint(np.asarray(tk["time"], float) * 1e6).astype(np.int64), unit="us")
    return pd.DataFrame(dict(open=b, high=b + nhieu, low=b - nhieu, close=b, spread=np.asarray(tk["spread"], float) / point),
                        index=idx)


def ghi_tick(duong, tk: dict) -> None:
    n = len(tk["bid"])
    with open(duong, "wb") as f:
        np.array([n], np.int64).tofile(f)
        for k in ("bid", "spread", "time", "bar"):
            np.asarray(tk[k], np.float64).tofile(f)


# ------------------------------------------------------------------ chay
def chay(exe, tk: dict, von: float, tham_so: dict | None = None, netting: bool = False, thu_muc=None,
         han_giay: int = 300, digits: int | None = None) -> dict:
    """Chay EA tren chuoi tick. Tra {'ok', 'ma_thoat', 'kq' (dict so tu RES), 'lenh' (DataFrame), 'log' (list dong LOG), 'loi'}.
    `kq`: n_mo, n_dong, n_tp, n_ea, balance, equity, con_mo, lot_con_mo, spread_con_mo, max_open, max_lot_open, max_dd_pct..."""
    tm = Path(thu_muc) if thu_muc else Path(tempfile.mkdtemp(prefix="ea_gia_lap_run_"))
    try:
        tm.mkdir(parents=True, exist_ok=True)
        f_tick, f_csv = tm / "ticks.bin", tm / "lenh.csv"
        ghi_tick(f_tick, tk)
        lenh = [str(exe), str(f_tick), str(f_csv), repr(float(von))]
        if netting:
            lenh.append("--netting")
        if digits is not None:
            lenh.append("--digits=%d" % digits)
        for k, v in (tham_so or {}).items():
            lenh.append("%s=%r" % (k, float(v)))
        p = subprocess.run(lenh, capture_output=True, text=True, timeout=han_giay)
        kq, log = {}, []
        for dong in p.stdout.splitlines():
            if dong.startswith("RES "):
                _r, k, v = dong.split(" ", 2)
                kq[k] = float(v)
            elif dong.startswith("LOG "):
                log.append(dong[4:])
        df = pd.read_csv(f_csv) if f_csv.exists() and f_csv.stat().st_size else pd.DataFrame()
    finally:
        if not thu_muc:          # thu muc tam do chinh ham nay tao: chuoi tick o paso 1e-6 nang ~12 MB / lan chay, de lai la day dia (08/10: 2482 thu muc = 29 GB)
            shutil.rmtree(tm, ignore_errors=True)
    return dict(ok=p.returncode == 0 and kq.get("init_ok") == 1.0, ma_thoat=p.returncode, kq=kq, lenh=df, log=log,
                loi=p.stderr[-2000:])


# ------------------------------------------------------------------ doi chieu EA <-> engine luoi.py
@dataclasses.dataclass
class KetQuaDoiChieu:
    """`eng` / `ea`: lenh hai ben da xep CUNG thu tu (tick mo, chieu, thu tu mo). `eng` co `i_mo`, `i_dong` (chi so tick, -1 = chua dong);
    `ea` co `chieu` (+1 mua / -1 ban), `bid_mo` (BID luc mo, doc tu comment). `trang_thai`: 'khop' hoac loai lech dau tien."""
    eng: pd.DataFrame
    ea: pd.DataFrame
    lai_engine: float          # luoi.chay(...).lai_rong
    lai_ea: float              # so du - von - spread cua lenh dang mo (so du chua ghi spread cua lenh chua dong)
    phi_tia_kep: float         # spread engine tru THEM khi dong cap tia - EA khong co; lai_engine + phi_tia_kep ~ lai_ea.
    #                            Chi co o `khop_bar="cuc_tri"` (ban cu tru spread HAI lan); `duong_di` tinh MOT lan nhu EA -> 0
    lech_explicada: float      # phan `lech_lai` GIAI THICH duoc bang chenh GIA tung lenh (engine dong / mo o muc luoi le giua hai tick)
    so_khop: int
    trang_thai: str
    chi_tiet: str
    kq_ea: dict
    log_ea: list
    n_tick: int

    @property
    def lech_lai(self) -> float:
        """lai engine (da cong lai spread tia kep) - lai EA: 0 khi hai ben cung mot duong gia va cung luat."""
        return self.lai_engine + self.phi_tia_kep - self.lai_ea

    @property
    def lech_con_lai(self) -> float:
        """`lech_lai` tru phan chenh gia tung lenh giai thich duoc: ~0 (1e-9) khi lenh khop va spread khong doi. Khac 0 la co mot
        khoan CHI PHI hai ben tinh khac nhau (spread, phi, lot) - khong the dung du chenh gia."""
        return self.lech_lai - self.lech_explicada


def so_lenh(eng: pd.DataFrame, ea: pd.DataFrame, paso: float, tol_tick: int = 1, tol_gia: float = 2.0):
    """So lenh-theo-lenh (da xep cung thu tu): chieu + lot PHAI y het; gia mo trong `tol_gia` buoc; tick mo / tick dong trong `tol_tick`;
    lenh mot ben da dong ben kia chua dong la lech. Tra (so lenh khop lien tiep tu dau, trang_thai, chi_tiet)."""
    n = min(len(eng), len(ea))
    for k in range(n):
        e, a = eng.iloc[k], ea.iloc[k]
        if int(e.chieu) != int(a.chieu) or abs(e.lot - a.vol) > 1e-9:
            return k, "lech_chieu_lot", "lenh %d: engine %+d x %.2f | EA %+d x %.2f" % (k, e.chieu, e.lot, a.chieu, a.vol)
        if abs(e.gia_mo - a.bid_mo) > tol_gia * paso * (1.0 + 1e-6):                    # dem tuong doi: bien dung sai khong phu thuoc nhieu dau phay dong
            return k, "lech_gia", "lenh %d: gia mo engine %.8f | EA %.8f" % (k, e.gia_mo, a.bid_mo)
        if abs(int(e.i_mo) - int(a.tick_mo)) > tol_tick:
            return k, "lech_tick_mo", "lenh %d: tick mo engine %d | EA %d" % (k, e.i_mo, a.tick_mo)
        dong_e, dong_a = int(e.i_dong) >= 0, a.ly_do != "open"
        if dong_e != dong_a or (dong_e and abs(int(e.i_dong) - int(a.tick_dong)) > tol_tick):
            return k, "lech_dong", "lenh %d: dong engine %s | EA %s" % (
                k, e.i_dong if dong_e else "-", int(a.tick_dong) if dong_a else "-")
    if len(eng) != len(ea):
        return n, "lech_so_lenh", "engine %d lenh | EA %d lenh" % (len(eng), len(ea))
    return n, "khop", ""


def doi_chieu(exe, ts, df: pd.DataFrame, paso: float = 1e-6, thu_tu: str = "theo_nen", von: float = 10000.0,
              digits: int = 8, qc=None, tol_tick: int = 1, tol_gia: float = 2.0, han_giay: int = 300) -> KetQuaDoiChieu:
    """Chay CUNG mot duong gia qua EA that (`exe`) va qua `luoi.chay` (tick-bar, khong phi qua dem) roi so tung lenh.

    `df`: bar OHLC (+ cot `spread` theo POINT) chi de SINH duong gia; `paso` < point (1e-6 voi gia 5 chu so) cho chuoi tick min
    hon luoi gia bar (it dong gia dung dung muc), `digits=8` de lam tron TP cua EA khong doi quyet dinh. `ts`: `luoi.ThamSo` voi LOT LA
    BOI SO BUOC LOT (0,04 voi cong 0,25) - EA lam tron lot, engine thi khong."""
    from nhan import luoi as L
    qc = qc or L.QuyCach(phi_nam_mua=0.0, phi_nam_ban=0.0)
    tk = tick_tu_bar(df, thu_tu, point=qc.point, paso=paso)
    bt = barra_tu_tick(tk, point=qc.point)
    kq = L.chay(bt, ts, von, qc=qc, ghi_lenh=True)
    ps = tham_so_ea_tu_luoi(ts)
    ps["InpPipSize"] = qc.pip
    r = chay(exe, tk, von, ps, digits=digits, han_giay=han_giay)
    if not r["ok"]:
        raise RuntimeError("EA khong chay duoc: %s %s" % (r["loi"], r["log"][-3:]))
    eng = kq.lenh.copy()
    eng["i_mo"] = bt.index.get_indexer(eng.mo)
    eng["i_dong"] = [bt.index.get_loc(x) if x == x else -1 for x in eng.dong]
    ea = r["lenh"].copy()
    ea["chieu"] = np.where(ea.type == 0, 1, -1)
    ea["bid_mo"] = [float(c[3:]) for c in ea.comment]
    ea = ea.sort_values(["tick_mo", "chieu", "ticket"], kind="stable").reset_index(drop=True)
    eng = eng.sort_values(["i_mo", "chieu", "tang"], kind="stable").reset_index(drop=True)
    sp = bt["spread"].to_numpy(float) * qc.point
    tia = eng[eng.ly_do == "tia"]
    phi_tia_kep = (float((tia.lot.to_numpy() * qc.hop_dong * sp[tia.i_dong.to_numpy()]).sum())
                   if len(tia) and ts.khop_bar == "cuc_tri" else 0.0)
    k = r["kq"]
    so_khop, trang_thai, chi_tiet = so_lenh(eng, ea, paso, tol_tick, tol_gia)
    return KetQuaDoiChieu(eng=eng, ea=ea, lai_engine=float(kq.lai_rong), lai_ea=k["balance"] - von - k["spread_con_mo"],
                          phi_tia_kep=phi_tia_kep, lech_explicada=_lech_explicada(eng, ea, tk, qc.hop_dong), so_khop=so_khop,
                          trang_thai=trang_thai, chi_tiet=chi_tiet, kq_ea=k, log_ea=r["log"], n_tick=len(tk["bid"]))


def _lech_explicada(eng: pd.DataFrame, ea: pd.DataFrame, tk: dict, hop: float) -> float:
    """Chenh lai (theo BID) giua engine va EA chi do GIA tung lenh khac nhau: engine mo / dong o MUC LUOI (co the le, giua hai tick),
    EA o tick dau tien vuot muc do. Chi tinh lenh DA DONG o ca hai ben (lenh lech dong da la `trang_thai` khac 'khop')."""
    n = min(len(eng), len(ea))
    if not n:
        return 0.0
    e, a = eng.iloc[:n], ea.iloc[:n]
    dong = (e.i_dong.to_numpy() >= 0) & (a.ly_do.to_numpy() != "open")
    if not dong.any():
        return 0.0
    td = a.tick_dong.to_numpy()[dong].astype(int)
    ban = a.type.to_numpy()[dong] == 1                        # BAN dong o ASK: tru spread de ve BID
    bid_dong_a = a.close.to_numpy()[dong] - np.where(ban, np.asarray(tk["spread"], float)[td], 0.0)
    chenh = ((e.gia_dong.to_numpy()[dong] - e.gia_mo.to_numpy()[dong]) - (bid_dong_a - a.bid_mo.to_numpy()[dong]))
    return float((e.chieu.to_numpy()[dong] * e.lot.to_numpy()[dong] * hop * chenh).sum())


def do_lech_bar(exe, ts, df: pd.DataFrame, thu_tu=("theo_nen", "thap_truoc", "cao_truoc"), paso: float | None = None,
                von: float = 10000.0, digits: int | None = None, qc=None, han_giay: int = 600) -> list:
    """DO LECH MO HINH BAR: engine chay tren bar OHLC THAT (nhu `thu_luoi`) so voi EA chay tren tick sinh tu CHINH cac bar do theo tung
    thu tu duong gia. Day la phep do 'engine lac quan / than trong bao nhieu so voi mot EA tick' - khong thay the tester that (tick that,
    spread doi, swap) nhung la can tren: engine va EA cung nhin MOT chuoi bar. Tra danh sach dict moi thu tu duong gia:
    thu_tu, lai_engine, lai_ea (tru phi lenh con mo), lech, lech_pct, so_lenh_engine, so_lenh_ea, n_tick."""
    from nhan import luoi as L
    qc = qc or L.QuyCach(phi_nam_mua=0.0, phi_nam_ban=0.0)
    kq = L.chay(df, ts, von, qc=qc, ghi_lenh=False)
    ps = tham_so_ea_tu_luoi(ts)
    ps["InpPipSize"] = qc.pip
    if digits is None:
        digits = int(round(-np.log10(qc.point)))
    out = []
    for tt in ([thu_tu] if isinstance(thu_tu, str) else thu_tu):
        tk = tick_tu_bar(df, tt, point=qc.point, paso=paso)
        # Engine vao lenh dau o CLOSE cua bar 0 (`vao = [(cl[0], ...)]`), EA vao o tick dau tien. Neu EA chay tu open bar 0 thi hai ben bat dau
        # o hai gia khac nhau: voi cau hinh it lenh / phu thuoc duong (cho_lui) hai ro lech pha mai mai - do 08/10/2026: lech -13% .. -37% chi
        # vi lech pha, bien mat khi cat bar 0 (lech < 1%). Cat tick bar 0 -> EA bat dau o open bar 1 = close bar 0 = diem vao dau cua engine.
        giu = np.asarray(tk["bar_idx"]) >= 1
        tk = {k: np.asarray(v)[giu] for k, v in tk.items()}
        r = chay(exe, tk, von, ps, digits=digits, han_giay=han_giay)
        if not r["ok"]:
            raise RuntimeError("EA khong chay duoc: %s %s" % (r["loi"], r["log"][-3:]))
        k = r["kq"]
        lai_ea = k["balance"] - von - k["spread_con_mo"]
        out.append(dict(thu_tu=tt, lai_engine=float(kq.lai_rong), lai_ea=lai_ea, lech=float(kq.lai_rong) - lai_ea,
                        lech_pct=100.0 * (float(kq.lai_rong) - lai_ea) / abs(lai_ea) if lai_ea else float("nan"),
                        so_lenh_engine=int(kq.so_lenh), so_lenh_ea=int(k["n_mo"]), n_tick=len(tk["bid"])))
    return out
