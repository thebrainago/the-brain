"""S1 giai doan 2: thu QUY TRINH TIM tham so tren the gioi nhan tao (thong minh vs ngau nhien vs do het).

Cau hoi cua chu du an (04/10/2026): "do het cac thong so, hay co cach do thong minh dua tren dac diem bot?". Giai doan 1 (`thu_chuyen`) do
QUY TAC DICH (khong do them gi). O day do QUY TRINH TIM: xuat phat tu cac cach dich cua `dich_tham_so`, di tiep bang engine tren MOT duong
quan sat that ngan (2 nam), roi chon (mu, hoac top-k qua mot duong kiem moi = mo phong tester). Moi quy trinh duoc cham tren tap B (duong doc
lap, cung tap voi dap an cua the gioi dich) va so voi dap an, o NGAN SACH NGANG:

  B0 chep so; T0 cach dich mac dinh; B1 chi doi bien do; SMART (`do_thong_minh.tim`, xep theo CAO NGUYEN); SMARTRAW (cung cac o, xep theo
  diem tho); SMART_S (ngan sach nho = chi mot luoi cuc bo); FULL_RAW / FULL_PLAT (do het luoi cua dap an); RAND (ngau nhien tren luoi dap
  an); RANDT (ngau nhien quanh cac cach dich); RAND_S / RANDT_S (ngan sach nho)

Ung vien khoi dau cua SMART / RANDT = T0 (neu ap duoc) + cac cach dich co so `DT.cac_cach_dich(lot="giu")` (lot cua the gioi nhan tao do
cong chot sau, nen khong chia theo ngan sach rui ro: lot nho nhat 0,01 khong chia nua duoc).
Moi quy trinh tim cho top-k (k = 1: chon mu; k = 4, 12: top-k duoc xep lai tren mot duong kiem moi). Cong xac nhan mo phong "co lai sau phi +
maxDD < 80 %" tren mot duong xac nhan moi voi lot chot tren duong tim (nhu niem phong luoi). Hai the gioi NHIEU (random walk, khong co co hoi)
do ti le "dat gia".

GIOI HAN PHAI DOC TRUOC (ghi vao bao cao): khong gian o chi co BA truc (buoc, ti le tp, so tang) nen ngau nhien o ngan sach ngang phu duoc
mot phan lon khong gian - EA that co 8-15 dau vao, noi do loi the cua tim thong minh LON HON phep do nay (day la can duoi, khong phai uoc
luong); ket qua noi ve CO CHE tim tren the gioi nhan tao co dap an, KHONG noi ve loi nhuan that. Nguong la NHAN canh bao, khong phai cong chan.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
import time
import zlib
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from nhan import dich_tham_so as DT
from nhan import do_thong_minh as DM
from nhan import luoi as LU
from nhan import thu_chuyen as T

PHIEN_BAN_GD2 = 1
SO_HAT_GD2 = 12
SO_HAT_NHIEU = 24
SO_NAM_QUAN_SAT_GD2 = 2.0
TOP_K_THU = (1, 4, 12)
SO_O_LUOI_CUC_BO = len(DM.HE_SO_BUOC) * len(DM.HE_SO_TP) * len(DM.HE_SO_TAM)
SO_LENH_TOI_THIEU = 20

#: moi quy trinh co mot ten goc (xem docstring); ten day du = "<goc>_<k>"
QUY_TRINH_TIM = ("SMART", "SMARTRAW", "SMART_S", "FULL_RAW", "FULL_PLAT", "RAND", "RANDT", "RAND_S", "RANDT_S")
CAC_CHUAN = ("B0", "T0", "B1")
NGAN_SACH_DAY_DU = ("SMART", "SMARTRAW", "RAND", "RANDT")
NGAN_SACH_NHO = ("SMART_S", "RAND_S", "RANDT_S")
#: cac cap so sanh DONG BANG (a, cac b, muc ngan sach): thong minh vs ngau nhien o ngan sach ngang, vs ba chuan khong ton phep thu
#: (T0 = chi dich bang quy tac mac dinh cua giai doan 1; B1 = giu khoang cach tren do thi; B0 = chep nguyen tham so). Chuan khong co duoi _k.
CAP_SO_SANH = (("SMART", ("RANDT", "RAND", "FULL_PLAT", "FULL_RAW", "SMARTRAW", "T0", "B1", "B0"), "day_du"),
               ("SMART_S", ("RANDT_S", "RAND_S", "T0"), "nho"))

#: hai the gioi KHONG co co hoi (random walk khop bien do ngan han): dem ti le "dat gia" (loai L5 = NHIEU)
BO_KICH_BAN_NHIEU = (
    T.KichBan("N0", "L5", T.GOC, T.GOC.doi(hoi_quy=False), mo_ta="random walk, khong hoi quy, chi phi nhu goc (khong co co hoi that)"),
    T.KichBan("N0_re", "L5", T.GOC, T.GOC.doi(hoi_quy=False, chi_phi_pip=3.0),
              mo_ta="random walk, chi phi 3 pip (re hon 3 lan): nhieu co hoi 'dat gia' hon"),
)

NGUONG_GD2 = {
    "phien_ban": 1,
    "thong_minh_so_voi_ngau_nhien": 0.8,        # trung vi hoi tiec SMART_k <= 0,8 x RANDT_k (ngan sach ngang)
    "thang_khi": "can tren khoang tin cay 95 % (bootstrap 2000 lan, phan tang theo kich ban x phong cach) cua hieu cap doi (SMART_k - RANDT_k) < 0",
    "dat_gia_sau_xac_nhan": 0.05,
    "dat_gia_truoc_xac_nhan": 0.25,
    "so_hat": SO_HAT_GD2,
    "so_hat_nhieu": SO_HAT_NHIEU,
    "so_nam_quan_sat": SO_NAM_QUAN_SAT_GD2,
    "top_k": list(TOP_K_THU),
    "ngan_sach_ngang": "RAND, RANDT (va RAND_S, RANDT_S) do DUNG so o ma SMART (SMART_S) da do; FULL do het luoi cua dap an",
    "gop": "moi kich ban co dap an tru Z0, ca hai phong cach; Z0 tinh rieng (kiem 'tim co lam hong so dung khong'); N0* tinh rieng (khong co dap an)",
}


# ------------------------------------------------------------------------------------------------------ ham nho
def tach_ten_bien_the(ten: str) -> tuple:
    """Nguoc cua `thu_chuyen.ten_bien_the`: 'A_ref|w=0.5|tam=I6|san=0' -> ('A_ref', 0.5, 'I6', 0.0)."""
    p = str(ten).split("|")
    if len(p) != 4 or not p[1].startswith("w=") or not p[2].startswith("tam=") or not p[3].startswith("san="):
        raise ValueError("ten bien the sai dang: %r" % (ten,))
    quy_mo, tam = p[0], p[2][4:]
    try:
        w, san = float(p[1][2:]), float(p[3][4:])
    except ValueError:
        raise ValueError("ten bien the sai dang: %r" % (ten,))
    if quy_mo not in T.KIEU_QUY_MO or tam not in T.TAM_THU or not (0.0 <= w <= 1.0) or not (san >= 0.0):
        raise ValueError("ten bien the khong hop le: %r" % (ten,))
    return quy_mo, w, tam, san


def chon_top_khac_nhau(cn: np.ndarray, k: int) -> list:
    """`k` o diem cao nhat cua mang 3 truc, khong hai o nao KE NHAU (chi so lech <= 1 o ca ba truc): chong lay 12 o cua cung mot doi."""
    d = np.array(cn, float)
    ra = []
    while len(ra) < int(k) and np.isfinite(d).any():
        idx = np.unravel_index(int(np.nanargmax(d)), d.shape)
        ra.append(tuple(int(i) for i in idx))
        d[tuple(slice(max(0, i - 1), i + 2) for i in idx)] = np.nan
    return ra


def tuong_quan_hang(x, y) -> float | None:
    """He so Spearman cua hai day (chi cac cap huu han); None neu < 5 cap hoac mot day khong doi."""
    from scipy.stats import rankdata
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    if int(ok.sum()) < 5:
        return None
    rx, ry = rankdata(x[ok]), rankdata(y[ok])
    if float(np.std(rx)) == 0.0 or float(np.std(ry)) == 0.0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def can_tren_clopper_pearson(so_dat: int, so_mau: int, muc: float = 0.95) -> float | None:
    """Can tren MOT PHIA cua ti le that khi quan sat `so_dat` / `so_mau` (Clopper-Pearson): 'khong co bang chung ti le cao hon con so nay'."""
    from scipy.stats import beta
    if so_mau <= 0:
        return None
    if so_dat >= so_mau:
        return 1.0
    return float(beta.ppf(muc, so_dat + 1, so_mau - so_dat))


def cong_xac_nhan(ts, dl_tim, dl_xn, von: float = T.VON, don_bay_toi_da: float = T.DON_BAY_TOI_DA) -> dict:
    """Mo phong cong 'co lai sau phi + maxDD < 80 %' o MOT duong xac nhan MOI. Lot chot tren duong TIM (he so lot k cham maxDD 80 %, khong qua
    tran don bay), roi chay CHINH tham so do tren duong xac nhan voi lot x k (duong equity co gian tuyen tinh nhu `thu_chuyen.diem_o`).
      dat_kham_pha = co lai o duong tim + du lenh + chot duoc lot (chua xac nhan)
      dat          = dat_kham_pha VA o duong xac nhan: co lai, maxDD < 80 %, du lenh, khong chay tai khoan"""
    from nhan import nc_thi_nghiem as NT
    ra = {"dat_kham_pha": False, "dat": False, "k": None, "lai_tong": None, "maxdd": None, "ly_do": ""}
    kq = LU.chay_mang(dl_tim, ts, von)
    if kq.chay:
        ra["ly_do"] = "chay_tai_khoan_o_duong_tim"
        return ra
    if int(kq.so_lenh) < SO_LENH_TOI_THIEU:
        ra["ly_do"] = "it_lenh_o_duong_tim"
        return ra
    if float(LU.chi_so(kq, von)["loi_suat_nam_pct"]) <= 0:
        ra["ly_do"] = "khong_co_lai_o_duong_tim"
        return ra
    kd = NT._he_so_lot_tai_tran(np.asarray(kq.duong_equity, float), von)
    if not kd:
        ra["ly_do"] = "khong_chot_duoc_lot"
        return ra
    notional = kq.margin * ts.don_bay
    kl = don_bay_toi_da * von / notional if notional > 0 else float("inf")
    k = float(min(kd, kl))
    ra["k"] = k
    ra["dat_kham_pha"] = True
    kx = LU.chay_mang(dl_xn, ts, von)
    if kx.chay:
        ra["ly_do"] = "chay_tai_khoan_o_duong_xac_nhan"
        return ra
    if int(kx.so_lenh) < SO_LENH_TOI_THIEU:
        ra["ly_do"] = "it_lenh_o_duong_xac_nhan"
        return ra
    e = np.asarray(kx.duong_equity, float)
    v = von + k * (e - von)
    if len(v) < 2 or not np.all(np.isfinite(v)) or float(v.min()) <= 0:
        ra["ly_do"] = "von_am_o_duong_xac_nhan"
        return ra
    dd = float(np.max(1.0 - v / np.maximum.accumulate(v)))
    lai = float(v[-1] / von - 1.0)
    ra["lai_tong"], ra["maxdd"] = lai, dd
    ra["dat"] = bool(lai > 0 and dd < 0.8)
    if not ra["dat"]:
        ra["ly_do"] = "lo_o_duong_xac_nhan" if lai <= 0 else "maxdd_tu_80_phan_tram"
    return ra


def _o_ngau_nhien_gan(tam_ts: list, n: int, rng, san: float, da_co: set) -> list:
    """`n` o MOI (khong trung `da_co`) lay ngau nhien quanh cac o goc `tam_ts`: moi khoang cach nhan he so log-deu trong khoang cua luoi cuc bo
    cua `do_thong_minh` (buoc 0,5..2; ti le tp 0,6..1,6; so tang 0,5..2). Co tran so lan thu (khong lap vo han)."""
    ra, thu = [], 0
    lo = (min(DM.HE_SO_BUOC), min(DM.HE_SO_TP), min(DM.HE_SO_TAM))
    hi = (max(DM.HE_SO_BUOC), max(DM.HE_SO_TP), max(DM.HE_SO_TAM))
    while len(ra) < n and thu < 60 * max(1, n):
        thu += 1
        goc = tam_ts[int(rng.integers(len(tam_ts)))]
        f = [math.exp(rng.uniform(math.log(a), math.log(b))) for a, b in zip(lo, hi)]
        ts = DM.bien_the(goc, f[0], f[1], f[2], san, san)
        k = DM._khoa(ts)
        if k in da_co:
            continue
        da_co.add(k)
        ra.append(ts)
    return ra


def _nho_nho(danh_gia):
    """Boc `danh_gia(list ThamSo)->list diem` bang bo nho theo ThamSo: cung mot o tren cung mot duong chi do MOT lan (diem khong doi)."""
    nho: dict = {}

    def f(cac: list) -> list:
        can, thay = [], set()
        for ts in cac:
            k = DM._khoa(ts)
            if k not in nho and k not in thay:
                thay.add(k)
                can.append(ts)
        if can:
            d = [float(x) for x in danh_gia(can)]
            if len(d) != len(can):
                raise ValueError("danh_gia tra %d diem cho %d o" % (len(d), len(can)))
            for ts, x in zip(can, d):
                nho[DM._khoa(ts)] = x
        return [nho[DM._khoa(ts)] for ts in cac]
    return f


# ------------------------------------------------------------------------------------------------------ mot hat quan sat
def so_sanh_quy_trinh(kieu, ung_vien: list, ts_b0, ts_t0, ts_b1, san_pip: float, danh_gia_tim, danh_gia_kiem, danh_gia_b, cong, rng,
                      diem_b_dap_an: float | None, be_mat_dap_an=None, top_k=TOP_K_THU, so_tot: int = DM.SO_UNG_VIEN_TOT,
                      so_vong: int = DM.SO_VONG_THU_HEP) -> dict:
    """MOT hat quan sat: chay tat ca quy trinh tim va tra bang so sanh. Ham THUAN (khong tu sinh duong gia): moi viec do deu qua ham duoc truyen vao.
      danh_gia_tim(list ThamSo)->list diem   engine tren duong quan sat (cai quy trinh tim duoc phep dung)
      danh_gia_kiem(list ThamSo)->list diem  MOT duong moi (mo phong tester: xep hang top-k theo duong nay)
      danh_gia_b(list ThamSo)->list diem     trung binh tren tap B (chi de CHAM, khong ai duoc dung de chon)
      cong(list ThamSo)->list dict           cong xac nhan tren duong moi (`dat_kham_pha`, `dat`)
    Quy trinh: xem docstring module. `ung_vien` rong -> bat dau tu `ts_b0` (chep). Ngan sach: SMART/SMART_S do so o ma `do_thong_minh.tim` do
    (toi da / chi mot luoi cuc bo); RAND, RANDT, RAND_S, RANDT_S do DUNG so o tuong ung; FULL do het luoi cua dap an. Cung mot o tren cung
    mot duong chi ton engine MOT lan (bo nho) nhung moi quy trinh van tu dem so o rieng cua no."""
    san = float(san_pip)
    top_k = tuple(int(k) for k in top_k)
    kmax = max(top_k)
    dg = _nho_nho(danh_gia_tim)
    # ---- ung vien (da ap san)
    uv, thay = [], set()
    for ts in (ung_vien or [ts_b0]):
        t2 = DM.ap_san(ts, san, san)
        if DM._khoa(t2) not in thay:
            thay.add(DM._khoa(t2))
            uv.append(t2)
    # ---- FULL: do het luoi cua dap an tren duong quan sat
    cac, chi = T.luoi_o_dap_an(kieu, san)
    d_full = np.array(dg(cac), float) if cac else np.zeros(0)
    arr = np.full((len(T.BUOC), len(T.TY_LE_TP), len(T.TANG)), np.nan)
    o_cua = {}
    for (ib, ir, it), x, ts in zip(chi, d_full, cac):
        arr[ib, ir, it] = x
        o_cua[(ib, ir, it)] = ts
    cn = DM.cao_nguyen_mang(arr) if cac else arr
    rho = None
    if be_mat_dap_an is not None and cac:
        bm = np.asarray(be_mat_dap_an, float)
        rho = tuong_quan_hang(d_full, [bm[i] for i in chi])
    xep, ngan_sach = {}, {}
    xep["FULL_RAW"] = [cac[j] for j in np.argsort(-d_full, kind="stable")[:kmax]] if cac else []
    xep["FULL_PLAT"] = [o_cua[i] for i in chon_top_khac_nhau(cn, kmax)] if cac else []
    ngan_sach["FULL_RAW"] = ngan_sach["FULL_PLAT"] = len(cac)
    # ---- SMART day du va nho (+ SMARTRAW tren cung cac o)
    kq = DM.tim(uv, dg, san, san, so_tot=so_tot, so_vong=so_vong)
    n_day_du = int(kq.so_phep_thu)
    xep["SMART"] = [t["tham_so"] for t in kq.top[:kmax]]
    xep["SMARTRAW"] = [o["tham_so"] for o in sorted(kq.cac_o, key=lambda o: -float(o["diem"]))[:kmax]]
    kq_s = DM.tim(uv, dg, san, san, so_tot=so_tot, so_vong=so_vong, ngan_sach=len(uv) + SO_O_LUOI_CUC_BO - 1)
    n_nho = int(kq_s.so_phep_thu)
    xep["SMART_S"] = [t["tham_so"] for t in kq_s.top[:kmax]]
    ngan_sach["SMART"] = ngan_sach["SMARTRAW"] = n_day_du
    ngan_sach["SMART_S"] = n_nho
    # ---- RANDT: o ngau nhien quanh cac cach dich tot nhat theo diem (cung thong tin ma SMART co khi chon tam)
    diem_uv = dg(uv)
    tam_ts = [uv[i] for i in sorted(range(len(uv)), key=lambda i: (-diem_uv[i], i))[:max(1, int(so_tot))]]
    for ten, n in (("RANDT", n_day_du), ("RANDT_S", n_nho)):
        co = set(DM._khoa(t) for t in uv)
        moi = _o_ngau_nhien_gan(tam_ts, max(0, n - len(uv)), rng, san, co)
        tat = list(uv) + moi
        d = dg(tat)
        xep[ten] = [tat[j] for j in sorted(range(len(tat)), key=lambda j: (-d[j], j))[:kmax]]
        ngan_sach[ten] = len(tat)
    # ---- RAND: ngau nhien tren luoi dap an (khong ton them engine: diem lay tu lan do het)
    for ten, n in (("RAND", n_day_du), ("RAND_S", n_nho)):
        if cac:
            j = rng.permutation(len(cac))[:min(n, len(cac))].tolist()
            j = sorted(j, key=lambda a: (-d_full[a], a))[:kmax]
            xep[ten] = [cac[a] for a in j]
            ngan_sach[ten] = min(n, len(cac))
        else:
            xep[ten] = []
            ngan_sach[ten] = 0
    # ---- chon cuoi cung moi quy trinh x k
    chon = {"B0": (ts_b0, 0, "B0"), "T0": (ts_t0, 0, "T0"), "B1": (ts_b1, 0, "B1")}
    for ten in QUY_TRINH_TIM:
        ds = xep[ten]
        for k in top_k:
            if not ds:
                continue
            cac_k = ds[:k]
            if len(cac_k) == 1:
                chon["%s_%d" % (ten, k)] = (cac_k[0], 0, ten)
            else:
                sk = [float(x) for x in danh_gia_kiem(cac_k)]
                chon["%s_%d" % (ten, k)] = (cac_k[int(np.argmax(sk))], len(cac_k), ten)
    # ---- cham tren tap B + cong xac nhan (moi o khac nhau cham MOT lan)
    khac, vitri = [], {}
    for ten, (ts, _, _) in chon.items():
        if ts is not None and DM._khoa(ts) not in vitri:
            vitri[DM._khoa(ts)] = len(khac)
            khac.append(ts)
    diem_b = [float(x) for x in danh_gia_b(khac)] if khac else []
    gate = list(cong(khac)) if khac else []
    ra = {}
    for ten, (ts, so_kiem, goc_ten) in chon.items():
        if ts is None:
            ra[ten] = {"ap_duoc": False}
            continue
        x = diem_b[vitri[DM._khoa(ts)]]
        g = gate[vitri[DM._khoa(ts)]]
        ra[ten] = {"ap_duoc": True, "buoc": ts.buoc, "tp": ts.tp, "tang": ts.tran_tang, "diem_b": x,
                   "hoi_tiec": T.hoi_tuong_doi(diem_b_dap_an, x) if diem_b_dap_an is not None else None,
                   "duoi_phan_giai": bool(min(ts.buoc, ts.tp) < san), "so_phep_thu": int(ngan_sach.get(goc_ten, 0)), "so_kiem": int(so_kiem),
                   "dat_kham_pha": bool(g.get("dat_kham_pha")), "dat_xac_nhan": bool(g.get("dat")), "k_lot": g.get("k"),
                   "ly_do_gate": g.get("ly_do", "")}
    return {"quy_trinh": ra, "ngan_sach": ngan_sach, "rho_xep_hang_full": rho, "so_o_luoi_dap_an": len(cac),
            "smart_ly_do_dung": kq.ly_do_dung, "smart_lich_su": kq.lich_su, "smart_s_ly_do_dung": kq_s.ly_do_dung}


# ------------------------------------------------------------------------------------------------------ chay that (engine + the gioi nhan tao)
def doc_dap_an(duong_dan: str) -> "T.DapAn":
    """Doc lai `DapAn` tu tep `dapan_*.json` giai doan 1 (be mat diem + o tot nhat + diem B): khong tinh lai dap an."""
    with open(duong_dan, encoding="utf-8") as f:
        d = json.load(f)

    def so(x):
        return float(x) if x is not None else float("nan")
    return T.DapAn(tg=T.TheGioi(**d["the_gioi"]), kieu=T.Kieu(**d["kieu"]), san_pip=so(d["san_pip"]), be_mat=np.array(d["be_mat"], dtype=float),
                   tot_nhat=LU.ThamSo(**d["tot_nhat"]), diem_cao_nguyen=so(d.get("diem_cao_nguyen")), diem_b=so(d.get("diem_b")),
                   a_nen_pip=so(d.get("a_nen_pip")))


def giai_doan_2(kb: "T.KichBan", kieu, da_nguon: "T.DapAn", da_dich: "T.DapAn | None", bien_the_mac_dinh: str, so_hat: int = SO_HAT_GD2,
                so_nam_qs: float = SO_NAM_QUAN_SAT_GD2, so_duong_b: int = T.SO_DUONG_DAP_AN, so_nam_b: float = T.SO_NAM_DUONG,
                luong: int | None = None, log=None) -> dict:
    """Mot (kich ban, phong cach): `so_hat` lan quan sat doc lap (moi lan: duong nguon + duong dich + duong kiem + duong xac nhan, moi duong `so_nam_qs`
    nam); cach dich mac dinh = `bien_the_mac_dinh` (ket qua giai doan 1). `da_dich` None (the gioi khong co co hoi) -> khong tinh hoi tiec."""
    luong = luong or T.luong_mac_dinh()
    quy_mo, w, tam, san_cf = tach_ten_bien_the(bien_the_mac_dinh)
    ts_nguon = da_nguon.tot_nhat
    tap_b = T.dung_duong(kb.dich, "B", so_duong_b, so_nam_b)
    diem_b_da = None if da_dich is None else da_dich.diem_b
    be_mat = None if da_dich is None else da_dich.be_mat
    hat_ra = []
    for s in range(int(so_hat)):
        t0 = time.time()
        obs_n = T._cho_quan_sat(kb.nguon, "g2_nguon", so_nam_qs, s)
        obs_d = T._cho_quan_sat(kb.dich, "g2_dich", so_nam_qs, s)
        dl_tim = LU.chuan_bi(obs_d, T.QUY_CACH)
        dl_kiem = LU.chuan_bi(T._cho_quan_sat(kb.dich, "g2_kiem", so_nam_qs, s), T.QUY_CACH)
        dl_xn = LU.chuan_bi(T._cho_quan_sat(kb.dich, "g2_xn", so_nam_qs, s), T.QUY_CACH)
        hs = T.ho_so_chuoi(LU.chuan_bi(obs_n, T.QUY_CACH), ts_nguon)
        gio_giu, tang_tc = hs["gio_giu_phut"], hs["tang_p90"]
        a_nen = T.bien_do_nen_pip(obs_d)
        san_pip = max(DT.NGUONG_PHAN_GIAI * a_nen, san_cf * kb.dich.chi_phi_pip)
        ly_do = []
        ts_t0, uv = None, []
        try:
            tt_n = T.thi_truong_do_duoc(obs_n, kb.khung_nguon, quy_mo, kb.nguon, gio_giu)
            tt_d = T.thi_truong_do_duoc(obs_d, kb.khung_dich, quy_mo, kb.dich, gio_giu)
            kqd = T.dich_theo_quy_tac(ts_nguon, tt_n, tt_d, w, tam, san_cf, gio_giu, tang_tc)
            ly_do = list(kqd.ly_do)
            if kqd.trang_thai == DT.OK:
                ts_t0 = kqd.tham_so
            with T.san_chi_phi_tam(san_cf):
                uv = [k.tham_so for k in DT.cac_cach_dich(ts_nguon, tt_n, tt_d, gio_giu, tang_tc, lot="giu")
                      if k.trang_thai == DT.OK and k.tham_so is not None]
            if ts_t0 is not None:                         # tim kiem bat dau tu cach dich mac dinh (T0) + cac cach dich co so
                uv = [ts_t0] + uv
        except ValueError as e:
            ly_do = [str(e)]
        ts_b1 = None
        try:
            tt1n = T.thi_truong_do_duoc(obs_n, kb.khung_nguon, "A_chart", kb.nguon, gio_giu)
            tt1d = T.thi_truong_do_duoc(obs_d, kb.khung_dich, "A_chart", kb.dich, gio_giu)
            k1 = T.dich_theo_quy_tac(ts_nguon, tt1n, tt1d, 0.0, "giu", 0.0, gio_giu, tang_tc)
            ts_b1 = k1.tham_so if k1.trang_thai == DT.OK else None
        except ValueError:
            ts_b1 = None
        rng = np.random.default_rng(zlib.crc32(("g2|%s|%s|%d" % (kb.ten, kieu.ten, s)).encode("ascii")))

        def dg_tim(cells, _dl=dl_tim):
            return [float(x) for x in T.diem_tren_cac_duong([_dl], cells, luong)[:, 0]]

        def dg_kiem(cells, _dl=dl_kiem):
            return [float(x) for x in T.diem_tren_cac_duong([_dl], cells, luong)[:, 0]]

        def dg_b(cells):
            return [float(x) for x in T.diem_tb(tap_b, cells, luong)]

        def cong(cells, _a=dl_tim, _b=dl_xn):
            def f(ts):
                try:
                    return cong_xac_nhan(ts, _a, _b)
                except Exception as e:                       # loi engine khong lam hong ca hat
                    return {"dat_kham_pha": False, "dat": False, "k": None, "ly_do": "loi_engine: %s" % type(e).__name__}
            with ThreadPoolExecutor(max_workers=luong) as ex:
                return list(ex.map(f, cells))

        r = so_sanh_quy_trinh(kieu, uv, ts_nguon, ts_t0, ts_b1, san_pip, dg_tim, dg_kiem, dg_b, cong, rng, diem_b_da, be_mat)
        r.update({"hat": s, "san_pip": san_pip, "a_nen_pip": a_nen, "so_cach_dich": len(uv), "ly_do_dich": ly_do, "ho_so_nguon": hs,
                  "ung_vien_dau": [[ts.buoc, ts.tp, ts.tran_tang] for ts in uv],
                  "tham_so_t0": None if ts_t0 is None else [ts_t0.buoc, ts_t0.tp, ts_t0.tran_tang],
                  "thoi_gian_giay": round(time.time() - t0, 1)})
        hat_ra.append(r)
        if log:
            log("  hat %d/%d %.0fs: SMART %d o, SMART_S %d o, FULL %d o" % (s + 1, so_hat, time.time() - t0, r["ngan_sach"]["SMART"],
                                                                         r["ngan_sach"]["SMART_S"], r["so_o_luoi_dap_an"]))
    return {"kich_ban": kb.ten, "loai": kb.loai, "kieu": kieu.ten, "bien_the_mac_dinh": bien_the_mac_dinh, "so_hat": int(so_hat),
            "so_nam_qs": so_nam_qs, "nguon": dataclasses.asdict(kb.nguon), "dich": dataclasses.asdict(kb.dich), "khung_nguon": kb.khung_nguon,
            "khung_dich": kb.khung_dich,
            "dap_an_dich": None if da_dich is None else {"buoc": da_dich.tot_nhat.buoc, "tp": da_dich.tot_nhat.tp, "tang": da_dich.tot_nhat.tran_tang,
                                                          "diem_b": da_dich.diem_b, "san_phan_giai_pip": da_dich.san_pip},
            "dap_an_nguon": {"buoc": ts_nguon.buoc, "tp": ts_nguon.tp, "tang": ts_nguon.tran_tang}, "hat_ket_qua": hat_ra}


def ke_hoach_s2(bien_the_mac_dinh: str) -> dict:
    """Cau hinh dong bang cua giai doan 2 (+ dau van tay). `bien_the_mac_dinh` la KET QUA giai doan 1 nen nam trong van tay."""
    tach_ten_bien_the(bien_the_mac_dinh)
    ch = {"phien_ban_gd2": PHIEN_BAN_GD2, "nguong": NGUONG_GD2, "bien_the_mac_dinh": bien_the_mac_dinh, "quy_trinh": list(QUY_TRINH_TIM),
          "chuan": list(CAC_CHUAN), "top_k": list(TOP_K_THU),
          "cap_so_sanh": [[a, list(bs), muc] for a, bs, muc in CAP_SO_SANH],
          "ung_vien_tim": "T0 (neu ap duoc) + DT.cac_cach_dich(lot=giu), moi ung vien qua DM.ap_san(san_pip)",
          "kich_ban_nhieu": [dataclasses.asdict(k) for k in BO_KICH_BAN_NHIEU], "he_so_buoc": list(DM.HE_SO_BUOC), "he_so_tp": list(DM.HE_SO_TP),
          "he_so_tam": list(DM.HE_SO_TAM), "so_tot": DM.SO_UNG_VIEN_TOT, "so_vong": DM.SO_VONG_THU_HEP,
          "ke_hoach_do_thong_minh": DM.ke_hoach(5)["plan_hash"], "van_tay_gd1": T.ke_hoach_s1()["plan_hash"]}
    h = hashlib.sha256(json.dumps(T._json_an_toan(ch), sort_keys=True).encode("ascii")).hexdigest()[:16]
    return {"plan_hash": h, "cau_hinh": ch}


def chay_giai_doan_2(thu_muc_p1: str, thu_muc_ra: str, ten_kich_ban=None, ten_kieu=("phang", "geo"), so_hat: int = SO_HAT_GD2,
                     so_hat_nhieu: int = SO_HAT_NHIEU, so_nam_qs: float = SO_NAM_QUAN_SAT_GD2, bien_the_mac_dinh: str | None = None,
                     luong: int | None = None, log=print) -> None:
    """Chay giai doan 2 cho cac kich ban cua giai doan 1 (doc dap an tu `thu_muc_p1/dapan_*.json`) + hai the gioi NHIEU; ghi
    `thu_muc_ra/p2_<ten>_<kieu>.json`. `bien_the_mac_dinh` None = lay tu `tong_hop_giai_doan_1` (quy tac da dong bang). Da co tep thi bo qua."""
    if bien_the_mac_dinh is None:
        tong = T.tong_hop_giai_doan_1(T.doc_giai_doan_1(thu_muc_p1))
        bien_the_mac_dinh = (tong.get("mac_dinh") or {}).get("ten")
        if not bien_the_mac_dinh:
            raise ValueError("chua co bien the mac dinh tu giai doan 1 (thieu ket qua?)")
    tach_ten_bien_the(bien_the_mac_dinh)
    kh = ke_hoach_s2(bien_the_mac_dinh)
    T.ghi_json(os.path.join(thu_muc_ra, "ke_hoach_s2.json"), kh)
    log("giai doan 2: bien the mac dinh %s, plan_hash %s" % (bien_the_mac_dinh, kh["plan_hash"]))
    tat_ca = list(T.BO_KICH_BAN) + list(BO_KICH_BAN_NHIEU)
    chon = list(ten_kich_ban or [k.ten for k in tat_ca])
    for kn in ten_kieu:
        kieu = T.KIEU[kn]
        da_goc = doc_dap_an(os.path.join(thu_muc_p1, "dapan_goc_%s.json" % kn))
        for ten in chon:
            kb = next((k for k in tat_ca if k.ten == ten), None)
            if kb is None:
                raise KeyError(ten)
            f = os.path.join(thu_muc_ra, "p2_%s_%s.json" % (ten, kn))
            if os.path.exists(f):
                log("[%s] %s: da co, bo qua" % (kn, ten))
                continue
            t0 = time.time()
            if kb.loai == "L5":
                da_dich = None
            elif kb.dich == kb.nguon:
                da_dich = da_goc
            else:
                da_dich = doc_dap_an(os.path.join(thu_muc_p1, "dapan_%s_%s.json" % (ten, kn)))
            r = giai_doan_2(kb, kieu, da_goc, da_dich, bien_the_mac_dinh, so_hat_nhieu if kb.loai == "L5" else so_hat, so_nam_qs, luong=luong,
                            log=log)
            T.ghi_json(f, r)
            log("[%s] %s xong %.0fs" % (kn, ten, time.time() - t0))


# ------------------------------------------------------------------------------------------------------ tong hop
def doc_giai_doan_2(thu_muc: str) -> list:
    """Doc cac tep `p2_*.json` trong `thu_muc` (sap theo ten)."""
    ra = []
    for ten in sorted(os.listdir(thu_muc)):
        if ten.startswith("p2_") and ten.endswith(".json"):
            with open(os.path.join(thu_muc, ten), encoding="utf-8") as f:
                ra.append(json.load(f))
    return ra


def _phan_vi(xs, q):
    xs = [x for x in xs if x is not None and math.isfinite(x)]
    return float(np.quantile(xs, q)) if xs else None


def _thong_ke_hoi_tiec(xs) -> dict:
    xs = [x for x in xs if x is not None and math.isfinite(x)]
    if not xs:
        return {"n": 0}
    return {"n": len(xs), "trung_vi": float(np.median(xs)), "trung_binh": float(np.mean(xs)), "p90": _phan_vi(xs, 0.9),
            "ty_le_tot": float(np.mean([x <= 0.15 for x in xs])), "ty_le_te": float(np.mean([x > 0.5 for x in xs]))}


def _hieu_cap_doi(du_lieu: dict, ten_a: str, ten_b: str):
    """Hieu (hoi tiec a - hoi tiec b) theo CAP CUNG HAT, nhom theo tang (kich ban|kieu). Bo cap neu mot ben khong ap duoc / khong co hoi tiec."""
    tang: dict = {}
    for khoa_tang, hat_list in du_lieu.items():
        for qt in hat_list:
            a, b = qt.get(ten_a), qt.get(ten_b)
            if not a or not b or not a.get("ap_duoc") or not b.get("ap_duoc"):
                continue
            ha, hb = a.get("hoi_tiec"), b.get("hoi_tiec")
            if ha is None or hb is None or not math.isfinite(ha) or not math.isfinite(hb):
                continue
            tang.setdefault(khoa_tang, []).append((float(ha), float(hb)))
    return tang


def bootstrap_phan_tang(tang: dict, so_lan: int = 2000, hat: int = 20261005) -> dict:
    """Trung binh cac tang (moi tang mot trong so ngang) cua hieu cap doi; khoang tin cay 95 % bootstrap (lay lai cap TRONG tung tang)."""
    ten = sorted(tang)
    if not ten:
        return {"n_tang": 0, "n_cap": 0}
    d = {t: np.array([a - b for a, b in tang[t]], float) for t in ten}
    ha = {t: np.array([a for a, _ in tang[t]], float) for t in ten}
    hb = {t: np.array([b for _, b in tang[t]], float) for t in ten}
    tb = float(np.mean([d[t].mean() for t in ten]))
    rng = np.random.default_rng(int(hat))
    mau = np.empty(int(so_lan))
    for i in range(int(so_lan)):
        v = []
        for t in ten:
            j = rng.integers(0, len(d[t]), len(d[t]))
            v.append(d[t][j].mean())
        mau[i] = float(np.mean(v))
    tung_tang = {t: float(d[t].mean()) for t in ten}
    tv_a = float(np.median(np.concatenate([ha[t] for t in ten])))
    tv_b = float(np.median(np.concatenate([hb[t] for t in ten])))
    return {"n_tang": len(ten), "n_cap": int(sum(len(d[t]) for t in ten)), "hieu_trung_binh": tb, "ci95_duoi": float(np.quantile(mau, 0.025)),
            "ci95_tren": float(np.quantile(mau, 0.975)), "trung_vi_a": tv_a, "trung_vi_b": tv_b,
            "ty_so_trung_vi": (tv_a / tv_b) if tv_b > 0 else None, "so_tang_a_tot_hon": int(sum(1 for v in tung_tang.values() if v < 0)),
            "tung_tang": tung_tang}


def tong_hop_giai_doan_2(ket_qua: list, bo_qua_kich_ban=("Z0",), so_lan_bootstrap: int = 2000) -> dict:
    """Gop ket qua giai doan 2. Tap CHINH = cac kich ban co dap an tru `bo_qua_kich_ban` (L1..L4); Z0 tinh rieng ('tim co lam hong so dung khong');
    kich ban loai L5 (nhieu) chi dung de dem ti le dat gia. Moi quy trinh: thong ke hoi tiec (trung vi / trung binh / p90 / ti le tot / ti le te),
    ngan sach, ti le DAT (suc manh o the gioi co co hoi; dat gia o the gioi nhieu); so sanh cap doi thong minh vs ngau nhien o ngan sach ngang."""
    chinh, z0, nhieu = {}, {}, {}
    for r in ket_qua:
        khoa_tang = "%s|%s" % (r["kich_ban"], r["kieu"])
        if r["loai"] == "L5":
            dich = nhieu
        elif r["kich_ban"] in bo_qua_kich_ban:
            dich = z0
        elif r["loai"] in ("L1", "L2", "L3", "L4"):
            dich = chinh
        else:
            continue
        dich[khoa_tang] = [h["quy_trinh"] for h in r["hat_ket_qua"]]
    ten_quy_trinh = sorted({t for tap in (chinh, z0, nhieu) for hs in tap.values() for qt in hs for t in qt})

    def gom(tap: dict, ten: str) -> dict:
        hang = [qt[ten] for hs in tap.values() for qt in hs if ten in qt]
        co = [h for h in hang if h.get("ap_duoc")]
        ra = _thong_ke_hoi_tiec([h.get("hoi_tiec") for h in co])
        ra.update({"so_hang": len(hang), "khong_ap_duoc": len(hang) - len(co),
                   "ty_le_duoi_phan_giai": float(np.mean([bool(h.get("duoi_phan_giai")) for h in co])) if co else None,
                   "so_phep_thu_trung_vi": _phan_vi([h.get("so_phep_thu") for h in co], 0.5),
                   "so_kiem_trung_vi": _phan_vi([h.get("so_kiem") for h in co], 0.5)})
        if co:
            so_kp = int(sum(bool(h.get("dat_kham_pha")) for h in co))
            so_xn = int(sum(bool(h.get("dat_xac_nhan")) for h in co))
            ra.update({"dat_kham_pha": so_kp, "dat_xac_nhan": so_xn, "so_mau_gate": len(co),
                       "ty_le_dat_kham_pha": so_kp / len(co), "ty_le_dat_xac_nhan": so_xn / len(co),
                       "can_tren_dat_kham_pha": can_tren_clopper_pearson(so_kp, len(co)),
                       "can_tren_dat_xac_nhan": can_tren_clopper_pearson(so_xn, len(co))})
        return ra

    ra = {"theo_quy_trinh": {t: gom(chinh, t) for t in ten_quy_trinh}, "z0": {t: gom(z0, t) for t in ten_quy_trinh},
          "nhieu": {t: gom(nhieu, t) for t in ten_quy_trinh},
          "nhieu_theo_the_gioi": {k: {t: gom({k: v}, t) for t in ten_quy_trinh} for k, v in sorted(nhieu.items())}}
    # theo loai (trung vi hoi tiec) - de thay quy trinh nao hong o loai nao
    theo_loai: dict = {}
    for loai in ("L1", "L2", "L3", "L4"):
        tap = {"%s|%s" % (r["kich_ban"], r["kieu"]): [h["quy_trinh"] for h in r["hat_ket_qua"]]
               for r in ket_qua if r["loai"] == loai and r["kich_ban"] not in bo_qua_kich_ban}
        if tap:
            theo_loai[loai] = {t: gom(tap, t).get("trung_vi") for t in ten_quy_trinh}
    ra["theo_loai"] = theo_loai
    # so sanh cap doi: thong minh vs ngau nhien o ngan sach ngang (tap chinh)
    cap_so_sanh = []
    ten_k = sorted({t.rsplit("_", 1)[1] for t in ten_quy_trinh if t.rsplit("_", 1)[-1].isdigit()}, key=int)
    for k in ten_k:
        for a, bs, muc in CAP_SO_SANH:
            for b in bs:
                ten_b = b if b in CAC_CHUAN else "%s_%s" % (b, k)
                tang = _hieu_cap_doi(chinh, "%s_%s" % (a, k), ten_b)
                if not tang:
                    continue
                bt = bootstrap_phan_tang(tang, so_lan_bootstrap)
                bt.update({"k": int(k), "a": a, "b": b, "ngan_sach": muc,
                           "thong_minh_thang": bool(bt.get("ci95_tren") is not None and bt["ci95_tren"] < 0),
                           "dat_nguong_08": bool(bt.get("ty_so_trung_vi") is not None and bt["ty_so_trung_vi"] <= NGUONG_GD2["thong_minh_so_voi_ngau_nhien"])})
                cap_so_sanh.append(bt)
    ra["so_sanh_cap_doi"] = cap_so_sanh
    # xep hang: do tin cay cua mot duong ngan (Spearman, trung vi theo kich ban)
    rho: dict = {}
    for r in ket_qua:
        if r["loai"] == "L5":
            continue
        v = _phan_vi([h.get("rho_xep_hang_full") for h in r["hat_ket_qua"]], 0.5)
        rho["%s|%s" % (r["kich_ban"], r["kieu"])] = v
    ra["rho_xep_hang"] = rho
    ra["rho_trung_vi"] = _phan_vi(list(rho.values()), 0.5)
    ra["so_kich_ban"] = {"chinh": len(chinh), "z0": len(z0), "nhieu": len(nhieu)}
    return ra


def main(argv=None) -> int:
    import argparse
    import sys
    ap = argparse.ArgumentParser(description="S1 giai doan 2: thu quy trinh tim tham so tren the gioi nhan tao")
    sub = ap.add_subparsers(dest="lenh", required=True)
    p = sub.add_parser("p2", help="chay giai doan 2 (can dapan_*.json cua giai doan 1)")
    p.add_argument("--p1", required=True)
    p.add_argument("--ra", required=True)
    p.add_argument("--kich-ban", default="")
    p.add_argument("--kieu", default="phang,geo")
    p.add_argument("--so-hat", type=int, default=SO_HAT_GD2)
    p.add_argument("--so-hat-nhieu", type=int, default=SO_HAT_NHIEU)
    p.add_argument("--so-nam", type=float, default=SO_NAM_QUAN_SAT_GD2)
    p.add_argument("--bien-the", default="")
    t = sub.add_parser("tong-hop", help="gop cac tep p2_*.json va in JSON")
    t.add_argument("--ra", required=True)
    t.add_argument("--ghi", default="")
    a = ap.parse_args(argv)
    if a.lenh == "p2":
        os.makedirs(a.ra, exist_ok=True)
        chay_giai_doan_2(a.p1, a.ra, [x for x in a.kich_ban.split(",") if x] or None, tuple(x for x in a.kieu.split(",") if x), a.so_hat,
                         a.so_hat_nhieu, a.so_nam, a.bien_the or None, log=lambda s: print(s, flush=True))
        return 0
    tong = tong_hop_giai_doan_2(doc_giai_doan_2(a.ra))
    if a.ghi:
        T.ghi_json(a.ghi, tong)
    else:
        json.dump(T._json_an_toan(tong), sys.stdout, ensure_ascii=True, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
