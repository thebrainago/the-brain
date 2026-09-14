# -*- coding: utf-8 -*-
"""pmg_quet.py - PHEU CUA PMG: G1 -> G2 -> G3, va SO DEM PHEP THU.

## Hinh dang cua pheu (dac ta muc 5 va 8.5)

    G0  pmg_g0.py      o nao co bat doi xung that       <- chay TRUOC, re nhat
    G1  pmg.kiem_g1    loai cau hinh vo nghiem          <- khong ton CPU
    G2  file nay       backtest full cost + cong phan giai
    G3  file nay       placebo: gia dao dau · xao khoi · GBM cung sigma
    G4  file nay       walk-forward ba giai doan
    G5  pmg_g0.fdr_bh  Bonferroni trong o + FDR-BH giua cac o
    G6  MT5 single-run                                  <- KHONG o day (TESTER=1)

Luat cua dac ta ma file nay thuc thi, chu khong chi ghi lai:

  - **Chi o SONG sau G0 moi duoc cap CPU.** `quet()` tu choi o da nam trong so
    loai tru vinh vien, va tu choi o chua chay G0.
  - **Moi cau hinh da chay deu dem vao bo dem phep thu, KE CA cau bi loai o G1.**
    Neu khong, so phep thu bao cao o G5 se nho hon su that va FDR se de dai.
  - **Kich thuoc luoi engine phai prereg TRUOC** cho tung o: `LUOI_PREREG`.
  - **Hau nghiem thi danh co.** O mo ra sau khi da xem ket qua o khac -> `post_hoc`
    va khong duoc tinh vao PASS (dac ta muc 8.5).

## G3 la buoc quan trong nhat voi ho bot nay

Dac ta noi thang: engine khong co entry nen no **cuc de an drift**. Mot luoi
`WITH` tren mot tai san co drift len se lai ma khong can bat cu bat doi xung nao.
Ba ban placebo tra loi dung cau do:

    dao dau    gia doi dau loi suat  -> giet drift, giu moi tinh chat khac
    xao khoi   block shuffle         -> giet tu tuong quan, giu cum bien dong
    GBM        cung sigma            -> giet ca hai, giu mot minh bien dong

Cau hinh nao khong tach khoi CA BA thi khong phai co che.

**Mot sai lech da biet, va no nghieng VE PHIA THAN TRONG:** ca ba ban dung lai
bar voi `open[i] = close[i-1]`, tuc **khong con KHE GIA**. Khe giet ro `AGAINST`
(muc 8.4 goi day la che do chet cua co che), nen placebo khong khe se chay TOT
HON mot cach gia tao, va ban that phai vuot qua mot cai moc cao hon muc dang
phai vuot. Sai lech theo huong nay chap nhan duoc; huong nguoc lai thi khong.
"""
from __future__ import annotations

import itertools
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))
    from nhan import pmg as PMG
    from nhan import pmg_engine as PE
    from nhan import pmg_g0 as G0
else:
    from . import pmg as PMG
    from . import pmg_engine as PE
    from . import pmg_g0 as G0

RA = LAB / "reports"
BO_DEM = RA / "PMG_BO_DEM_PHEP_THU.json"
KET_QUA = RA / "PMG_QUET.json"

#: Luoi engine PREREG. Doi bang nay = doi gia thuyet, va so phep thu doi theo -
#: nen no nam mot cho, co ten, va duoc ghi vao ket qua cua moi lan quet.
#: `h` PHAI la tap con cua `pmg_g0.CAC_H`. Neu khong, `quet` tra cuu huong cua
#: muc h do trong bang G0 va khong thay gi -> bo lang le ca cau hinh, va bao cao
#: se noi "G1 giu 0" ma khong ai biet vi sao. (Sap dung 14/09 voi h=1.0.)
LUOI_PREREG = {
    "h":          (0.5, 0.8, 1.2, 2.0, 3.0),
    "size_mode":  ("flat", "linear", "geometric", "inverse"),
    "tp_dist":    (0.5, 1.0, 2.0),
    "max_legs":   (6, 12),
    "step_mode":  ("fixed",),
    "tp_mode":    ("avg_plus",),
    "anchor_mode": ("static",),
}
TEN_LUOI = "prereg_v1_2026_09_14"

#: So ung vien dau bang duoc cap G3 (placebo) + G4 (walk-forward) + do bat bien.
#: Xem `quet` de biet vi sao con so nay KHONG lam nhe di hieu chinh da phep thu.
SO_DUA_VAO_G3 = 20


def so_o_luoi(luoi=None) -> int:
    luoi = luoi or LUOI_PREREG
    n = 1
    for v in luoi.values():
        n *= len(v)
    return n


#: Phoi nhiem DINH (tong lot khi luoi quet het) cua moi cau hinh, theo equity.
#: Xem `sinh_cau_hinh` de biet vi sao con so nay phai CO DINH GIUA CAC CAU HINH.
DON_BAY_DINH_MUC_TIEU = 1.0


def sinh_cau_hinh(ma: str, phien: str, atr_tf: str, direction: str,
                  luoi=None, don_bay_dinh: float = DON_BAY_DINH_MUC_TIEU, **co_dinh):
    """Sinh moi cau hinh cua luoi prereg cho MOT o. Khu trung bang van tay.

    **Chuan hoa phoi nhiem la phan quan trong nhat cua ham nay.** Dac ta muc 1.4
    hoi thang: *"neu flat khong thang thi moi ham tang size chi la don bay tra
    hinh"* - va muc 7.3 doi mot bang so sanh bon ham SIZE o cung `h*`. Bang do
    chi tra loi duoc cau hoi neu bon ham duoc chay o **CUNG PHOI NHIEM DINH**.

    Neu de nguyen `phoi_nhiem_1 = 1.0` cho ca bon thi `geometric r=2, n=12` co
    tong lot 4.095 con `flat n=12` co 12 - tuc dang so mot cau hinh don bay 341
    lan voi mot cau hinh don bay 1 lan, roi ket luan ve "hinh dang ham size".
    Do la dung cai bay ma dac ta canh bao. Nen o day `phoi_nhiem_1` duoc chia
    nguoc: `don_bay_dinh / sum(q_k)`. Sau chuan hoa, chenh lech giua bon ham chi
    con la HINH DANG phan bo, khong con la quy mo.

    (Do 14/09 tren EURGBP M5: khong chuan hoa thi `flat` chay tai khoan o -98%;
    day khong phai ket luan ve co che, la ket luan ve co lot.)
    """
    luoi = luoi or LUOI_PREREG
    khoa = list(luoi)
    thay = set()
    for gia_tri in itertools.product(*(luoi[k] for k in khoa)):
        d = dict(zip(khoa, gia_tri))
        q = PMG.trong_so_size(d.get("size_mode", "flat"),
                              d.get("max_legs", 10), d.get("size_r", 2.0))
        cf = PMG.CauHinh(ma=ma, phien=phien, atr_tf=atr_tf, direction=direction,
                         phoi_nhiem_1=don_bay_dinh / float(q.sum()), **d, **co_dinh)
        vt = cf.van_tay()
        if vt in thay:
            continue
        thay.add(vt)
        yield cf


# ------------------------------------------------------------ BO DEM PHEP THU
def dem(them: int = 0, nhan: str = "") -> dict:
    """Bo dem phep thu tich luy. `them=0` chi doc."""
    d = {"tong": 0, "theo_nhan": {}}
    if BO_DEM.exists():
        try:
            d = json.loads(BO_DEM.read_text(encoding="utf-8"))
        except Exception:
            pass
    if them:
        d["tong"] = d.get("tong", 0) + them
        d.setdefault("theo_nhan", {})
        d["theo_nhan"][nhan] = d["theo_nhan"].get(nhan, 0) + them
        d["cap_nhat"] = time.strftime("%Y-%m-%d %H:%M:%S")
        RA.mkdir(parents=True, exist_ok=True)
        BO_DEM.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d


# ---------------------------------------------------------------- G3 PLACEBO
def _gia_dao_dau(df):
    """Gia doi dau loi suat. Giet DRIFT, giu moi tinh chat khac cua tung nen.

    Phan hay sai: khong duoc doi cho hai cot `high`/`low` roi nhan ti le - lam
    vay ra `high < low`, tuc nen am, va moi so sau do vo nghia. Phai PHAN CHIEU
    hinh hoc cua tung nen: rau tren cua ban that thanh rau duoi cua ban dao, do
    theo TI LE so voi than nen, roi dung lai quanh open/close moi.
    """
    import pandas as pd
    o = np.asarray(df["open"], float)
    h = np.asarray(df["high"], float)
    l = np.asarray(df["low"], float)
    c = np.asarray(df["close"], float)
    tren = h / np.maximum(o, c) - 1.0          # rau tren, theo ti le
    duoi = 1.0 - l / np.minimum(o, c)          # rau duoi
    moi_c = c[0] * np.exp(np.cumsum(-np.diff(np.log(c), prepend=np.log(c[0]))))
    moi_o = np.r_[o[0], moi_c[:-1]]
    tran, san = np.maximum(moi_o, moi_c), np.minimum(moi_o, moi_c)
    return pd.DataFrame({"open": moi_o, "high": tran * (1.0 + duoi),
                         "low": san * (1.0 - tren), "close": moi_c}, index=df.index)


def _gia_xao_khoi(df, hat=4242, khoi=None):
    """Block shuffle: giet tu tuong quan, GIU cum bien dong."""
    import pandas as pd
    rng = np.random.default_rng(hat)
    c = np.asarray(df["close"], float)
    lr = np.diff(np.log(c))
    n = len(lr)
    k = khoi or max(10, int(round(n ** (1 / 3))))
    nb = int(np.ceil(n / k))
    dau = rng.integers(0, max(1, n - k), size=nb)
    idx = (dau[:, None] + np.arange(k)[None, :]).reshape(-1)[:n]
    moi = c[0] * np.exp(np.cumsum(lr[np.clip(idx, 0, n - 1)]))
    moi = np.r_[c[0], moi]
    return _bar_tu_gia(moi, df, rng)


def _gia_gbm(df, hat=4242):
    """GBM cung sigma, KHONG drift, khong cum bien dong."""
    import pandas as pd
    rng = np.random.default_rng(hat + 7)
    c = np.asarray(df["close"], float)
    lr = np.diff(np.log(c))
    moi = c[0] * np.exp(np.cumsum(rng.normal(0.0, float(np.std(lr)), len(lr))))
    return _bar_tu_gia(np.r_[c[0], moi], df, rng)


def _bar_tu_gia(gia, df_mau, rng):
    """Dung lai OHLC tu chuoi close, giu ti le rau/than CUA CHINH tai san do.

    Khong duoc lay bar mau nguyen xi: bien do nen la thu quyet dinh so lan cham
    luoi, nen placebo phai giu no giong that, con thu tu thi phai bi pha.
    """
    import pandas as pd
    c = np.asarray(gia, float)[:len(df_mau)]
    o = np.r_[c[0], c[:-1]]
    ban_do = ((df_mau["high"] - df_mau["low"])
              / df_mau["close"].replace(0, np.nan)).to_numpy()
    ban_do = np.nan_to_num(ban_do[:len(c)], nan=0.0)
    nua = c * ban_do / 2.0
    giua = (o + c) / 2.0
    return pd.DataFrame({"open": o, "high": np.maximum(np.maximum(o, c), giua + nua),
                         "low": np.minimum(np.minimum(o, c), giua - nua),
                         "close": c}, index=df_mau.index[:len(c)])


BAN_PLACEBO = {"dao_dau": _gia_dao_dau, "xao_khoi": _gia_xao_khoi, "gbm": _gia_gbm}


def g3_placebo(df, cf, cp=None, atr_arr=None) -> dict:
    """Chay cau hinh tren ba ban gia gia. Tra ve lai that vs lai tren tung ban."""
    that = PE.mo_phong(df, cf, cp, atr_arr)
    ra = {"that": that.get("lai_tong", 0.0), "ban": {}}
    for ten, ham in BAN_PLACEBO.items():
        dg = ham(df)
        try:
            a = PE.atr_khung(dg, cf.atr_tf, cf.atr_period)
        except Exception:
            a = None
        r = PE.mo_phong(dg, cf, cp, a)
        ra["ban"][ten] = r.get("lai_tong", 0.0)
    ra["tach_khoi_moi_ban"] = all(ra["that"] > v for v in ra["ban"].values())
    ra["kem_nhat_hon"] = ra["that"] - max(ra["ban"].values())
    return ra


# ------------------------------------------------------------------- G4 WF
def g4_walk_forward(df, cf, cp=None, so_doan: int = 3) -> dict:
    """Chia lam `so_doan` giai doan lien tiep, chay rieng tung doan."""
    n = len(df)
    cat = [int(n * i / so_doan) for i in range(so_doan + 1)]
    lai = []
    for i in range(so_doan):
        d = df.iloc[cat[i]:cat[i + 1]]
        if len(d) < cf.atr_period + 50:
            lai.append(None)
            continue
        try:
            a = PE.atr_khung(d, cf.atr_tf, cf.atr_period)
        except Exception:
            a = None
        lai.append(PE.mo_phong(d, cf, cp, a).get("lai_tong"))
    co = [x for x in lai if x is not None]
    return {"lai_tung_doan": lai,
            "so_doan_duong": sum(1 for x in co if x > 0),
            "so_doan_do_duoc": len(co),
            "on_dinh": bool(co) and all(x > 0 for x in co)}


# ------------------------------------------------------------------- QUET
def quet(ma: str, khung: str = "M5", atr_tf: str = "H1", phien: str = "ALL",
         direction: str | None = None, luoi=None, bat_g0: bool = True,
         post_hoc: bool = False, gioi_han: int = 0, in_ra=print) -> dict:
    """Chay ca pheu cho MOT o. `direction=None` -> lay huong tu bang G0."""
    from nhan import du_lieu as DL
    from nhan import chi_phi as CP
    t0 = time.time()
    luoi = luoi or LUOI_PREREG

    # --- G0: o nay co duoc cap CPU khong
    huong_g0, g0_ghi = None, ""
    if bat_g0:
        bang = _doc_bang_g0()
        o_g0 = [r for r in (bang.get("o") or [])
                if r["ma"] == ma and r["phien"] == phien and r["atr_tf"] == atr_tf]
        if not o_g0:
            return {"trang_thai": "CHUA_DO_DUOC",
                    "ly_do": f"chua chay G0 cho ({ma}, {phien}, {atr_tf}) - "
                             f"chay `b pmg g0` truoc; dac ta cam cap CPU cho o chua qua G0"}
        song = [r for r in o_g0 if r.get("qua_fdr")]
        if not song:
            return {"trang_thai": "LOAI_O_G0", "ly_do": "khong h nao qua FDR o o nay",
                    "ma": ma, "phien": phien, "atr_tf": atr_tf}
        huong_g0 = {r["h"]: r["ket_luan"] for r in song}
        g0_ghi = f"{len(song)}/{len(o_g0)} muc h qua G0"

    df = DL.nap(ma, khung)
    cp = CP.tu_du_lieu(ma, df)
    try:
        atr_arr = PE.atr_khung(df, atr_tf, 14)
    except Exception as ex:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": f"ATR {atr_tf}: {ex}"}
    atr_frac = float(np.nanmedian(atr_arr) / np.median(df["close"]))

    cac_cf, bo_g1 = [], []
    for d in (("WITH", "AGAINST") if direction is None else (direction,)):
        for cf in sinh_cau_hinh(ma, phien, atr_tf, d, luoi):
            if huong_g0 is not None:
                # chi chay huong ma G0 cho phep, o dung muc h do
                if huong_g0.get(cf.h) != d:
                    continue
            if G0.da_bi_loai(ma, phien, atr_tf, cf.h, d):
                continue
            k = PMG.kiem_g1(cf, cp.spread_frac_chung, cp.truot_gia_frac, atr_frac)
            (cac_cf if k["kha_thi"] else bo_g1).append((cf, k))
    # moi cau hinh DA XET deu dem vao so phep thu, ke ca cai bi loai o G1
    dem(len(cac_cf) + len(bo_g1), f"{ma}/{phien}/{atr_tf}")
    if gioi_han:
        cac_cf = cac_cf[:gioi_han]

    in_ra(f"  {ma} {khung} ATR({atr_tf}) {phien}: {g0_ghi}; "
          f"G1 giu {len(cac_cf)} / bo {len(bo_g1)} / luoi prereg {so_o_luoi(luoi)} o")

    # --- G2: chay HET, re. Mot lan mo phong.
    ket = []
    for cf, k in cac_cf:
        r = PE.mo_phong(df, cf, cp, atr_arr)
        r["g1"] = {"d_be_atr": k["d_be_atr"], "don_bay_dinh": k["don_bay_dinh"]}
        ket.append(r)

    # --- G3 + G4: DAT gap 6 lan G2 (3 ban placebo + 3 doan walk-forward), nen chi
    # chay cho UNG VIEN DAU BANG. Do 14/09: chay G3 cho moi cau hinh co lai lam
    # mot o AUDCAD M5 (1,0 trieu bar x 120 cau hinh) tu ~11 phut thanh hon mot gio.
    #
    # Viec chon top N o day la mot phep chon HAU NGHIEM, va no KHONG duoc phep
    # lam nhe di hieu chinh da phep thu: ca 120 cau hinh van dem vao bo dem o tren,
    # va FDR o G5 van chay tren toan bo con so do. Cat bot o day chi de tiet kiem
    # CPU, khong de tiet kiem hinh phat thong ke.
    ung = [r for r in ket if r.get("trang_thai") == "DU" and r.get("lai_tong", 0) > 0]
    ung.sort(key=lambda r: -r["lai_tong"])
    theo_vt = {r["van_tay"]: cf for (cf, _), r in zip(cac_cf, ket)}
    for r in ung[:SO_DUA_VAO_G3]:
        cf = theo_vt[r["van_tay"]]
        r["g3"] = g3_placebo(df, cf, cp, atr_arr)
        r["g4"] = g4_walk_forward(df, cf, cp)
        r["bat_bien"] = {k: v for k, v in PE.do_bat_bien(df, cf, cp, atr_arr).items()
                         if k not in ("bi_quan", "lac_quan")}

    du = [r for r in ket if r.get("trang_thai") == "DU"]
    song = [r for r in du if r.get("lai_tong", 0) > 0
            and r.get("g3", {}).get("tach_khoi_moi_ban")
            and r.get("g4", {}).get("on_dinh")
            and r.get("bat_bien", {}).get("dung_duoc")
            # phai DUONG o ban THAN TRONG, khong phai o ban dep hon trong hai ban
            and r.get("bat_bien", {}).get("lai_than_trong", -1) > 0]
    ra = {
        "ma": ma, "khung": khung, "atr_tf": atr_tf, "phien": phien,
        "post_hoc": post_hoc,
        "ten_luoi": TEN_LUOI, "luoi": {k: list(v) for k, v in luoi.items()},
        "so_o_luoi_prereg": so_o_luoi(luoi),
        "so_chay": len(ket), "so_bo_g1": len(bo_g1),
        "so_do_duoc": len(du), "so_song": len(song),
        "so_vao_g3": min(SO_DUA_VAO_G3, sum(1 for r in du if r.get("lai_tong", 0) > 0)),
        "do_tin_chi_phi": cp.do_tin,
        "spread_bps": cp.spread_frac_chung * 1e4,
        "giay": round(time.time() - t0, 1),
        "bo_dem_phep_thu": dem()["tong"],
        "ket_qua": sorted(ket, key=lambda r: -r.get("lai_tong", -9)),
        "ly_do_bo_g1": _gom_ly_do(bo_g1),
    }
    if post_hoc:
        ra["canh_bao"] = ("o HAU NGHIEM - khong duoc tinh vao PASS, chi sinh gia "
                          "thuyet cho vong prereg sau (dac ta muc 8.5)")
    return ra


def _gom_ly_do(bo) -> dict:
    d = {}
    for _, k in bo:
        for l in k["ly_do"]:
            khoa = l.split(":")[0]
            d[khoa] = d.get(khoa, 0) + 1
    return d


def _doc_bang_g0() -> dict:
    if not G0.BANG_G0.exists():
        return {}
    try:
        return json.loads(G0.BANG_G0.read_text(encoding="utf-8"))
    except Exception:
        return {}


def in_ket_qua(r: dict, so_dong: int = 12, in_ra=print) -> None:
    if r.get("trang_thai") in ("CHUA_DO_DUOC", "LOAI_O_G0"):
        in_ra(f"  {r['trang_thai']}: {r['ly_do']}")
        return
    in_ra("")
    in_ra(f"PMG QUET — {r['ma']} {r['khung']} ATR({r['atr_tf']}) phien {r['phien']}")
    in_ra(f"  luoi prereg `{r['ten_luoi']}` {r['so_o_luoi_prereg']} o · "
          f"chay {r['so_chay']} · bo o G1 {r['so_bo_g1']} · "
          f"do duoc {r['so_do_duoc']} · SONG {r['so_song']}")
    in_ra(f"  chi phi: spread {r['spread_bps']:.3f} bps, do_tin={r['do_tin_chi_phi']} · "
          f"bo dem phep thu tich luy {r['bo_dem_phep_thu']}")
    if r["ly_do_bo_g1"]:
        in_ra(f"  G1 bo vi: {r['ly_do_bo_g1']}")
    in_ra("")
    in_ra(f"  {'lai %':>8} {'dd %':>7} {'ro':>6} {'lenh':>6} {'don bay':>8} "
          f"{'swap/lai':>9} {'tt':>13}  cau hinh")
    for x in r["ket_qua"][:so_dong]:
        sw = x.get("swap_tren_lai", 0)
        in_ra(f"  {x.get('lai_tong',0)*100:8.2f} {x.get('dd_max',0)*100:7.2f} "
              f"{x.get('so_ro',0):6d} {x.get('so_lenh',0):6d} "
              f"{x.get('dinh_don_bay',0):8.1f} "
              f"{(sw if sw < 99 else 99):9.2f} {x.get('trang_thai','?'):>13}  "
              f"{x.get('ma','')[:64]}")
