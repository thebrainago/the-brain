# -*- coding: utf-8 -*-
"""cong.py - CONG PASS. Noi duy nhat mot gia thuyet duoc phep doi doi.

Thay cho `lab/quant/kiem_dinh.py` cu, vi cong cu chi doi:
    ok_edge = edge > 0 and pf > 1.0 and sharpe > 0
tuc mot chien luoc MUA-GIU TRA HINH van qua duoc.

Cong nay theo THIET_KE_DAY_CHUYEN muc 2:
  1. net_return  > mua_giu_net
  2. net_sharpe  > mua_giu_net   (khong phai do lieu cao hon)
  3. net_calmar  > mua_giu_net   (khong phai do om sut giam lon hon)
  4. alpha_vs_mua_giu > 0, p <= nguong, sai so chuan NEWEY-WEST
     -> day la thu chan DON BAY TRA HINH: mua-giu phoi nhiem day thi
        alpha ~ 0 theo cau tao, du tong lai rat dep.
  5. placebo_p <= nguong, lay p XAU NHAT trong >= 5 hat
  6. pre_registered = true; neu khong -> toi da la EXPLORATORY, KHONG BAO GIO PASS

Siet them khi phoi nhiem trung binh > 95%: alpha p va placebo p <= 0,01, va
phai co it nhat mot giai doan con duong. (Ly do: co che VIX tung co IC +0,106
duong o ca 5 giai doan con nhung placebo 10,2% - vi size trung binh 98-99%
nen no gan nhu chinh la mua-giu.)

Bo sung cua ban nay: mo hinh chi phi `do_tin='KHAI'` (chua do tu du lieu hoac
tu san) KHONG BAO GIO PASS - vi day dung la loi da giet ban cu.
"""
from __future__ import annotations

import json
import hashlib
import math
import sys
from pathlib import Path
from urllib.parse import quote

import numpy as np
from scipy import stats

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import do_luong as DO, mo_phong as MP, so as SO, du_lieu as DL
else:
    from . import do_luong as DO, mo_phong as MP, so as SO, du_lieu as DL

LAB = Path(__file__).resolve().parent.parent
NGUONG_FILE = LAB / "config" / "nguong.json"

MAC_DINH = {
    "p_alpha": 0.05,
    "p_placebo": 0.05,
    "p_siet": 0.01,             # khi phoi nhiem > 95%
    "phoi_nhiem_siet": 0.95,
    "so_hat_placebo": 5,
    "n_bootstrap": 199,
    "so_lenh_toi_thieu": 30,
    # --- TANG 2 KINH TE (chu du an dua vao 18/09/2026, tu tong ket SP500) ---
    # Sinh ra de giet MARTINGALE TRA HINH: tp=0,1xATR / sl=4,0xATR cho rr=0,025
    # va winrate 100% tren 15-20 lenh. Bonferroni KHONG bat duoc, vi breakeven
    # winrate cua rr=0,025 la 97,6% nen 100% vuot qua ngon lanh. Dung toan hoc,
    # vo gia tri kinh te. Tren SP500 no da sinh ra 2.081 ung vien kieu nay.
    "rr_thuc_te_toi_thieu": 0.2,     # MIN_RR: lai TB lenh thang / lo TB lenh thua
    "edge_tren_spread_toi_thieu": 3.0,  # MIN_EDGE_MULT: lai rong >= 3x chi phi spread

    "fdr_muc_tieu": 0.10,
    # So lan mot gia thuyet duoc phep DA NHIN holdout truoc lan nay ma van con
    # co the PASS. 0 = chi lan nhin DAU TIEN moi chung nhan duoc. Xem
    # `so.phoi_nhiem_holdout`.
    "lan_nhin_holdout_truoc_do_toi_da": 0,
    "_ghi_chu": "Ba con so cua THIET_KE muc 11 chua duoc chu du an khai bao. "
                "Dang dung mac dinh hoc thuat 0,05 - la MAC DINH, khong phai chan ly. "
                "Khai bao 'gia_tri_mot_chien_luoc_tot_nam', "
                "'thiet_hai_mot_chien_luoc_vo_dung_nam', 'xac_suat_tien_nghiem' "
                "de he tu suy ra nguong.",
}


#: DIEU KIEN CHI LA NHAN CANH BAO, KHONG CHAN. Quyet dinh cua chu du an 11/09:
#:
#:   "khong phai nhung mo hinh kinh te hay quan tri quy de ma can de cao qua
#:    nhieu tieu chi hoc thuat hay cac chi tieu chat che. Muc dich cuoi cung la
#:    co tien chap nhan ca chi phi va rui ro cao"
#:
#: Ranh gioi khong tuy tien: cai gi noi ve TIEN va ve TINH DUNG cua con so thi
#: van chan (thang moc, phi do duoc, du lenh, khong an khe gia dao ngay). Cai gi
#: chi noi "chua du bang chung theo chuan hoc thuat" thi ha xuong nhan.
NHAN_MEM = {
    "4_alpha_duong_co_y_nghia": "alpha khong dat muc y nghia thong ke",
    "5_placebo": "placebo yeu - co the la ngau nhien",
    "6_dang_ky_truoc": "khong dang ky truoc - rui ro tu lua minh khi quet rong",
    "9_siet_phoi_nhiem_cao": "phoi nhiem cao ma chua chung minh duoc bu rui ro",
    "10_qua_fdr_online": "khong qua nguong FDR online",
}
#: Cai VAN CHAN. Liet ke tuong minh de them mot dieu kien moi khong tu dong roi
#: vao ben nao ma khong ai quyet dinh.
CHAN_CUNG = ("1_loi_hon_mua_giu", "2_sharpe_hon_mua_giu", "3_calmar_hon_mua_giu",
             "7_chi_phi_do_duoc", "8_du_lenh", "11_khong_an_khe_dao_ngay")


def che_do_cong() -> str:
    """'nhan' (mac dinh) = cac tieu chi hoc thuat chi dan nhan. 'chan' = ban cu.

    Doi bang `"che_do_cong": "chan"` trong config/nguong.json. Ban cu duoc giu
    nguyen ven chu khong xoa: so `verdict_chan` van duoc tinh va ghi trong moi
    phan quyet, nen bat ky luc nao cung doi chieu duoc hai cach doc.
    """
    return str(nguong().get("che_do_cong", "nhan")).lower()


def nguong() -> dict:
    n = dict(MAC_DINH)
    if NGUONG_FILE.exists():
        try:
            n.update(json.loads(NGUONG_FILE.read_text(encoding="utf-8-sig")))
        except Exception:
            pass
    # Neu chu du an da khai bao 3 con so -> suy ra nguong tu ham mat mat.
    V = n.get("gia_tri_mot_chien_luoc_tot_nam")
    C = n.get("thiet_hai_mot_chien_luoc_vo_dung_nam")
    pi = n.get("xac_suat_tien_nghiem")
    if V and C and pi:
        # Can bang ky vong: chap nhan khi  pi*V*(1-beta) > (1-pi)*C*alpha
        # -> alpha < pi*V/((1-pi)*C) * (1-beta), lay (1-beta)=0,5 thu than trong.
        a = float(pi) * float(V) / max((1.0 - float(pi)) * float(C), 1e-9) * 0.5
        a = float(min(0.20, max(0.001, a)))
        n["p_alpha"] = n["p_placebo"] = round(a, 4)
        n["p_siet"] = round(a / 5.0, 5)
        n["_suy_ra_tu"] = {"V": V, "C": C, "pi": pi}
    return n


# ------------------------------------------------------- PLACEBO: BOOTSTRAP KHOI
def _do_dai_khoi(v: np.ndarray) -> int:
    """Do dai khoi trung binh = do dai doan giu vi the trung binh.
    Bootstrap phai giu duoc CUM THEO CHE DO, neu khong no se cap giay chung
    nhan cho dung bay bien-dong-cum-lai (THIET_KE muc 3)."""
    khac0 = np.abs(v) > 1e-12
    if not khac0.any():
        return 10
    doi = np.diff(khac0.astype(int))
    vao = np.sum(doi == 1) + (1 if khac0[0] else 0)
    if vao <= 0:
        return 10
    return int(max(2, min(len(v) // 10, round(khac0.sum() / vao))))


def bootstrap_dung(v: np.ndarray, rng: np.random.Generator, dai_khoi: int) -> np.ndarray:
    """Stationary bootstrap (Politis-Romano) tren CHUOI VI THE.
    Do dai khoi ngau nhien ~ Hinh hoc(1/dai_khoi), noi vong tron."""
    n = len(v)
    p = 1.0 / max(dai_khoi, 1)
    ra = np.empty(n)
    i = 0
    while i < n:
        bd = rng.integers(0, n)
        dai = min(rng.geometric(p), n - i)
        vt = (bd + np.arange(dai)) % n
        ra[i:i + dai] = v[vt]
        i += dai
    return ra


def lai_theo_lenh(vi_the, loi):
    """Gop chuoi loi THEO BAR thanh loi THEO LENH.

    `KetQua.loi` la loi tung bar (`v * r - phi`), khong phai tung lenh. Muon do
    R:R THUC TE thi phai gop lai: moi doan `vi_the` khong doi la mot lenh.

    Do nay khac tp/sl KHAI BAO o cho no la cai da xay ra that - ke ca khi lenh
    thoat bang timeout chu khong cham tp/sl nao.
    """
    import numpy as _np
    v = _np.asarray(vi_the, dtype=float)
    l = _np.asarray(loi, dtype=float)
    if v.size == 0 or l.size == 0:
        return _np.array([])
    n = min(v.size, l.size)
    v, l = v[:n], l[:n]
    ra, dang, tich = [], None, 0.0
    for i in range(n):
        if v[i] != dang:
            if dang not in (None, 0.0):
                ra.append(tich)
            dang, tich = v[i], 0.0
        if v[i] != 0.0:
            tich += l[i]
    if dang not in (None, 0.0):
        ra.append(tich)
    return _np.array(ra, dtype=float)


def rr_thuc_te(vi_the, loi) -> float:
    """Lai TB cua lenh THANG chia |lo TB cua lenh THUA|. 0 = khong do duoc."""
    import numpy as _np
    x = lai_theo_lenh(vi_the, loi)
    if x.size == 0:
        return 0.0
    thang, thua = x[x > 0], x[x < 0]
    if thang.size == 0:
        return 0.0
    if thua.size == 0:
        return float("inf")          # chua tung thua - de dieu kien khac xet
    return float(_np.mean(thang) / abs(_np.mean(thua)))


def kiem_ks(v_that: np.ndarray, v_gia: np.ndarray) -> float:
    """KS-test: phan phoi khoang cach giua cac lan vao lenh cua null phai
    KHONG phan biet duoc voi that. p thap = null sinh sai."""
    def khoang(v):
        k = np.flatnonzero(np.diff((np.abs(v) > 1e-12).astype(int)) == 1)
        return np.diff(k) if len(k) > 2 else np.array([1.0])
    a, b = khoang(v_that), khoang(v_gia)
    if len(a) < 5 or len(b) < 5:
        return 1.0
    try:
        return float(stats.ks_2samp(a, b).pvalue)
    except Exception:
        return 1.0


def null_quay_vong(v: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """NULL QUAY VONG - giu NGUYEN chuoi vi the, chi doi diem bat dau.

    Vi sao them null nay (16/08): bootstrap khoi bi KS-test bac bo tren PHAN LON
    ung vien that (`ks_p_min = 0,0000` do tren US500M H1), va khi bi bac bo thi
    `cong.xet` danh truot dieu kien 5 - tuc chien luoc bi loai vi CHAT LUONG CUA
    NULL, khong phai vi khong co edge. Do la mot cong tu choi vi ly do sai.

    Quay vong khong the bi KS bac bo THEO CAU TAO: no giu y nguyen phoi nhiem,
    do dai tung doan giu, so lan vao lenh va phan phoi khoang cach giua cac lan
    vao. Thu duy nhat no pha la SU TRUNG KHOP giua thoi diem va gia - dung cai
    ta muon kiem. Day la phep kiem hoan vi CHINH XAC duoi gia thiet bat bien
    theo dich vong tron, khong phai xap xi.
    """
    n = len(v)
    if n < 3:
        return v.copy()
    return np.roll(v, int(rng.integers(1, n)))


# Nguong "chac chan truot" cua tang 1. p > muc nay thi du co chay them 900 luot
# nua cung khong the ve duoi 0,05 -> dung som, danh thoi gian cho ung vien khac.
P_DUNG_SOM = 0.30


def placebo(df, kq_he, cp, n_boot: int | None = None, so_hat: int | None = None,
            lai_suat=None, dung_som: bool = True) -> dict:
    """p-value placebo, HAI NULL + HAI TANG.

    Null:  quay vong (chinh xac, khong the bi KS bac bo) + bootstrap khoi
           (Politis-Romano, giu cum che do). Lay p XAU NHAT trong tat ca.
           Mot hat khong du: verdict cua du an tung doi theo hat (95,8% voi hat
           11 so voi 94,8% voi hat 13).

    Tang:  tang 1 chay 99 luot quay vong. p > 0,30 -> dung ngay, khong ung vien
           nao tu do quay lai duoi 0,05 duoc. Tang 2 moi chay day du.
           Do 16/08: mot lan placebo day du la 995 luot backtest; ~90% ung vien
           chet ngay tang 1, nen buoc nay mot minh cat ~80% cong do.
    """
    n = nguong()
    n_boot = n_boot or n["n_bootstrap"]
    so_hat = so_hat or n["so_hat_placebo"]
    v = kq_he.vi_the
    that = float(np.nansum(kq_he.loi))
    dk = _do_dai_khoi(v)

    def _mot_hat(sinh, hat: int, so_luot: int):
        rng = np.random.default_rng(1000 + hat * 7919)
        vuot, v_cuoi = 0, None
        for _ in range(so_luot):
            vg = sinh(v, rng)
            kg = MP.chay(df, vg, cp, lai_suat, da_dich=True)
            if float(np.nansum(kg.loi)) >= that:
                vuot += 1
            v_cuoi = vg
        return (vuot + 1) / (so_luot + 1), v_cuoi

    _qv = lambda x, r: null_quay_vong(x, r)                    # noqa: E731
    _bs = lambda x, r: bootstrap_dung(x, r, dk)                # noqa: E731

    # --- TANG 1: sang re bang null quay vong -----------------------------
    p1, _ = _mot_hat(_qv, 0, 99)
    if dung_som and p1 > P_DUNG_SOM:
        return {"p_xau_nhat": round(float(p1), 4), "p_tot_nhat": round(float(p1), 4),
                "p_tung_hat": [round(p1, 4)], "do_dai_khoi": dk,
                "ks_p_min": None, "null_hop_le": True,
                "n_bootstrap": 99, "so_hat": 1, "tang": 1,
                "dung_som": f"p={p1:.3f} > {P_DUNG_SOM} o tang 1 - khong the ve duoi nguong"}

    # --- TANG 2: day du, hai null ----------------------------------------
    ps, ks, chi_tiet = [p1], [], {"quay_vong": [round(p1, 4)], "bootstrap": []}
    for hat in range(1, max(so_hat // 2, 1) + 1):
        p, _ = _mot_hat(_qv, hat, n_boot)
        ps.append(p)
        chi_tiet["quay_vong"].append(round(p, 4))
    for hat in range(so_hat // 2 + 1, so_hat + 1):
        p, v_cuoi = _mot_hat(_bs, hat, n_boot)
        ps.append(p)
        chi_tiet["bootstrap"].append(round(p, 4))
        if v_cuoi is not None:
            ks.append(kiem_ks(v, v_cuoi))

    # KS chi phan xu null BOOTSTRAP. Null quay vong dung theo cau tao, nen
    # bootstrap hong khong duoc phep giet ca phep kiem nua - chi bi loai bo.
    bs_hop_le = bool(ks and min(ks) > 0.01)
    if ks and not bs_hop_le:
        ps = ps[:len(chi_tiet["quay_vong"])]     # bo phan bootstrap khoi ket luan
    return {
        "p_xau_nhat": round(float(max(ps)), 4),
        "p_tot_nhat": round(float(min(ps)), 4),
        "p_tung_hat": [round(x, 4) for x in ps],
        "p_theo_null": chi_tiet,
        "do_dai_khoi": dk,
        "ks_p_min": round(float(min(ks)), 4) if ks else None,
        "bootstrap_hop_le": bs_hop_le if ks else None,
        "null_hop_le": True,          # luon co it nhat null quay vong hop le
        "n_bootstrap": n_boot, "so_hat": len(ps), "tang": 2,
    }


# ---------------------------------------------------------------- FDR ONLINE
def ky_hien_tai() -> str:
    """Quy hien tai, chi de bao cao legacy; KHONG con tao epoch FDR.

    FDR V2 khong tu nap lai ngan sach theo lich. Mot data release hoac luat
    quyet dinh moi phai duoc khai bao ro trong epoch.
    """
    import datetime as _d
    h = _d.date.today()
    return f"{h.year}Q{(h.month - 1) // 3 + 1}"


# THE HE CUA CHINH CAI CONG. Tang len khi doi LUAT QUYET DINH (khong phai doi
# nguong). Ket qua cua hai the he cong khac nhau khong nam chung mot chuoi
# quyet dinh duoc - y het ly do `chi_phi.THE_HE` phai tach chuoi.
#   1 (15/08): placebo chay cho MOI ung vien; ho FDR tich luy vinh vien.
#   2 (16/08): cong RE chay truoc, placebo chi chay cho ung vien da qua het
#              cong re; suat FDR gan theo GIA THUYET chu khong theo lan chay;
#              them null quay vong ben canh bootstrap khoi.
#   3 (16/08): epoch khai bao lane/family/data release/generation, khong reset
#              theo lich; dinh danh bang economic plan hash; moi plan cham
#              confirmation tieu dung dung mot suat, ke ca khi truot cong re.
#   4 (21/08): chuoi FDR chi nhan p_alpha (lien tuc). Placebo van la dieu kien
#              BAT BUOC nhung khong con vao so hoc FDR: p cua no co san
#              1/(n_boot+1)=0,005 trong khi nguong LORD tut duoi muc do tu phep
#              thu thu 4, nen `max(p_alpha, p_placebo)` khoa cung cong lai
#              vinh vien. 346 phan quyet FAIL cua the he 3 sinh ra tu loi nay
#              va KHONG duoc dung lam bang chung "khong co edge".
THE_HE_CONG = 5


def san_p_placebo(n_bootstrap: int | None = None) -> float:
    """p nho nhat ma placebo CO THE tra ve, do so hoan vi quyet dinh.

    Mot phep kiem hoan vi n lan khong bao gio tra duoc p duoi 1/(n+1). Dua con
    so co san do vao mot nguong giam dan la tu khoa cong lai.
    """
    n = int(n_bootstrap if n_bootstrap is not None else nguong()["n_bootstrap"])
    # 0 hoan vi = khong phan giai duoc gi ca -> san la 1,0, khong phai 0,5.
    return 1.0 / (max(n, 0) + 1)


def nguong_lord(j: int, muc_tieu: float | None = None) -> float:
    """Nguong alpha cua LORD tai phep thu thu `j` khi CHUA co reject nao.

    Tach ra thanh ham rieng de bai kiem doi chieu duoc no voi `san_p_placebo()`
    - do la phep so sanh da lo ra loi khoa cong.
    """
    mt = float(muc_tieu if muc_tieu is not None else nguong()["fdr_muc_tieu"])
    gam = lambda k: 1.0 / ((k + 1) ** 1.6)   # noqa: E731
    chuan = sum(gam(k) for k in range(1, 5001))
    return gam(max(1, int(j))) / chuan * (mt * 0.5)


def _phan_epoch(ten: str, gia_tri) -> str:
    """Chuan hoa mot thanh phan epoch thanh chuoi doc duoc va khong nhap nhang."""
    s = str(gia_tri).strip() if gia_tri is not None else ""
    if not s:
        raise ValueError(f"FDR V2 bat buoc khai bao {ten}")
    return quote(s, safe="._-@")


def tao_epoch_fdr(lane: str, family: str, data_release: str,
                  decision_generation: int | str = THE_HE_CONG) -> str:
    """Tao khoa epoch bat bien, khong phu thuoc ngay/quy hien tai.

    Cung mot epoch nghia la cung luong tim kiem, ho kinh te, ban phat hanh du
    lieu va luat quyet dinh. Doi bat ky thanh phan nao tao mot chuoi FDR moi co
    chu y; khong co reset ngam theo lich.
    """
    return (
        "fdr-v2"
        f"|lane={_phan_epoch('lane', lane)}"
        f"|family={_phan_epoch('family', family)}"
        f"|data_release={_phan_epoch('data_release', data_release)}"
        f"|decision_generation={_phan_epoch('decision_generation', decision_generation)}"
    )


#: Ho FDR la DUNG CU DO, khong phai kham pha. Chung dung chung mot so cai voi
#: gia thuyet that nhung khong bao gio sinh ra mot khang dinh nao.
#:
#: VI SAO PHAI PHAN LOAI (do 01/09/2026). So cai co 1.799 hang FDR, trong do
#: **1.019 hang (57%) la `do_luc`** - du lieu con lai tu truoc khi
#: `do_luc` chuyen sang `ghi_so=False` ngay 24/08. Bleeding da dung, nhung moi
#: bang tong ke tu do van cong chung vao: bao cao noi "fdr_tong_tho = 687" ben
#: canh "fdr_tong = 275" va tang chan doan khong the giai thich duoc 687 la gi,
#: nen no mo van de `vd_so_sach_khong_khop`. Do khong phai loi so sach - do la
#: hai DON VI khac nhau bi in canh nhau ma khong noi ro.
#:
#: LORD khong bi anh huong: `j` dem theo `WHERE ho=?` nen moi epoch tu tinh
#: suat cua no; ho do dac khong lam chat nguong cua ho kham pha. Cai bi hong
#: chi la BAO CAO - va mot bao cao khong doc duoc thi khong ai kiem duoc gi.
HO_DO_DAC = ("do_luc", "do_mde", "do_mde2", "null_hieu_chuan", "thu_luc_cong",
             "test_che_do", "hieu_chuan_v6")


def phan_epoch_ra(epoch: str) -> dict:
    """Tach mot khoa epoch nguoc lai thanh cac thanh phan. Khoa cu -> {}."""
    if not str(epoch or "").startswith("fdr-v2|"):
        return {}
    ra = {}
    for phan in str(epoch).split("|")[1:]:
        if "=" in phan:
            k, v = phan.split("=", 1)
            ra[k] = v
    return ra


def la_ho_do_dac(epoch: str) -> bool:
    """Epoch nay la dung cu do hay la duong kham pha that?

    Nhan dien theo `family`, khong theo chuoi con cua ca khoa: mot ho that ten
    `xu_huong@do_luc_thap` khong duoc lang le bi xep thanh dung cu do.
    """
    family = phan_epoch_ra(epoch).get("family") or str(epoch or "")
    goc = family.split("@")[0].split("#")[0]
    return goc in HO_DO_DAC


def ho_fdr(ho: str) -> str:
    """Adapter khoa ho cu, khong con reset theo quy.

    Loi goi moi nen dung :func:`tao_epoch_fdr` va khai bao du bon thanh phan.
    Adapter nay co dinh lane/data release legacy de code cu khong bi gay, nhung
    ket qua phai duoc bao cao la thieu provenance du lieu.
    """
    return tao_epoch_fdr("legacy", ho, "LEGACY_UNSPECIFIED", THE_HE_CONG)


def _p_bao_thu(p) -> tuple[float, bool]:
    """Tra p hop le; p thieu/hong duoc thay bang 1 de khong tao reject gia."""
    try:
        p_float = float(p)
    except (TypeError, ValueError):
        return 1.0, True
    if not math.isfinite(p_float) or not 0.0 <= p_float <= 1.0:
        return 1.0, True
    return p_float, False


def lord_v2(p: float | None, economic_plan_hash: str, *, lane: str,
            family: str, data_release: str,
            decision_generation: int | str = THE_HE_CONG,
            muc_tieu: float | None = None, ghi_so: bool = True,
            gt_ma_nguon: str | None = None) -> dict:
    """LORD cho mot chuoi quyet dinh duoc khai bao ro.

    ``economic_plan_hash`` la danh tinh cua phep thu trong epoch. Goi lai cung
    plan chi tra ve quyet dinh dau tien va tham chieu dong cu; khong sua p,
    nguong hay bac_bo. Ham nay kiem soat so cai quyet dinh cua he thong, nhung
    khong bien p-value adaptive/ro ri holdout thanh p-value hop le.
    """
    plan_hash = str(economic_plan_hash or "").strip()
    if not plan_hash:
        raise ValueError("FDR V2 bat buoc economic_plan_hash/plan_hash")
    epoch = tao_epoch_fdr(lane, family, data_release, decision_generation)
    mt = float(muc_tieu if muc_tieu is not None else nguong()["fdr_muc_tieu"])
    if not math.isfinite(mt) or not 0.0 < mt < 1.0:
        raise ValueError("fdr_muc_tieu phai nam trong (0, 1)")
    p_dung, da_thay_p = _p_bao_thu(p)

    # SELECT duplicate + cap so thu tu + INSERT la mot critical section. Neu
    # khong, hai worker co the cung cap suat cho mot economic plan.
    with SO.ket_noi() as cn:
        cn.execute("BEGIN IMMEDIATE")
        try:
            cu = [dict(r) for r in cn.execute(
                "SELECT id,luc,p,nguong,bac_bo,tai_nguyen FROM fdr "
                "WHERE ho=? ORDER BY id", (epoch,))]
            if cu and any(abs(float(r["tai_nguyen"]) - mt) > 1e-12 for r in cu):
                raise ValueError(
                    "khong duoc doi fdr_muc_tieu trong cung epoch; "
                    "hay tang decision_generation")

            da_co = cn.execute(
                "SELECT id,luc,p,nguong,bac_bo,tai_nguyen FROM fdr "
                "WHERE ho=? AND gt_ma=? ORDER BY id LIMIT 1",
                (epoch, plan_hash)).fetchone()
            if da_co:
                cn.execute("COMMIT")
                r = dict(da_co)
                return {
                    "nguong_fdr": round(float(r["nguong"]), 6),
                    "bac_bo": bool(r["bac_bo"]),
                    "thu_tu_trong_ho": next(
                        i for i, row in enumerate(cu, 1) if row["id"] == r["id"]),
                    "ho": epoch, "epoch": epoch, "chay_lai": True,
                    "duplicate": True, "fdr_id": int(r["id"]),
                    "tham_chieu_quyet_dinh": int(r["id"]),
                    "luc_quyet_dinh_dau": r["luc"],
                    "economic_plan_hash": plan_hash,
                    "p_su_dung": float(r["p"]), "p_de_nghi_lan_nay": p_dung,
                    "p_khac_lan_dau": abs(float(r["p"]) - p_dung) > 1e-12,
                    "p_da_thay_bang_1": bool(da_thay_p),
                    "so_da_bac_bo": sum(1 for row in cu if row["bac_bo"]),
                    "muc_tieu": mt, "da_ghi_so": False,
                }

            j = len(cu) + 1
            gam = lambda k: 1.0 / ((k + 1) ** 1.6)  # noqa: E731
            chuan = sum(gam(k) for k in range(1, 5001))
            W0 = mt * 0.5
            b0 = mt - W0
            a = gam(j) / chuan * W0
            tau = [i + 1 for i, r in enumerate(cu) if r["bac_bo"]]
            for t in tau:
                if j - t >= 1:
                    a += gam(j - t) / chuan * b0
            bac_bo = bool(p_dung <= a)
            if ghi_so:
                # `gt_ma` la plan_hash (danh tinh phep thu trong epoch);
                # `gt_ma_nguon` la ma gia thuyet, de doi soat duoc voi bang
                # `ket_qua`. Truoc 01/09 chi co cot dau, va moi phep doi soat
                # ba tang lang le tra ve rong cho moi hang sau 17/08.
                cur = cn.execute(
                    "INSERT INTO fdr(luc,ho,gt_ma,p,nguong,bac_bo,tai_nguyen,gt_ma_nguon) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    (SO.bay_gio(), epoch, plan_hash, p_dung, float(a),
                     int(bac_bo), mt, gt_ma_nguon))
                fdr_id = int(cur.lastrowid)
            else:
                # DO THU, KHONG GHI SO. Van tinh dung nguong ma phep thu nay se
                # gap (vi tri j, cac reject truoc do), nhung khong chiem suat.
                fdr_id = None
            cn.execute("COMMIT")
        except Exception:
            cn.execute("ROLLBACK")
            raise

    return {
        "nguong_fdr": round(a, 6), "bac_bo": bac_bo,
        "thu_tu_trong_ho": j, "ho": epoch, "epoch": epoch,
        "chay_lai": False, "duplicate": False, "fdr_id": fdr_id,
        "da_ghi_so": bool(ghi_so),
        "tham_chieu_quyet_dinh": fdr_id,
        "economic_plan_hash": plan_hash, "p_su_dung": p_dung,
        "p_da_thay_bang_1": bool(da_thay_p),
        "so_da_bac_bo": len(tau), "muc_tieu": mt,
    }


def _plan_hash_legacy(gt_ma: str) -> tuple[str, str]:
    """Tim plan_hash cua loi goi cu; fallback duoc danh dau ro trong ket qua."""
    ma = str(gt_ma or "").strip()
    if not ma:
        raise ValueError("confirmation bat buoc co gt_ma hoac economic_plan_hash")
    if len(ma) in (40, 64) and all(c in "0123456789abcdefABCDEF" for c in ma):
        return ma.lower(), "doi_so_la_plan_hash"
    r = SO.mot("SELECT plan_hash FROM gia_thuyet WHERE ma=?", ma)
    if r and r.get("plan_hash"):
        return str(r["plan_hash"]), "gia_thuyet.plan_hash"
    # Chi de code cu khong gay. Day KHONG phai economic identity da kiem chung.
    return "legacy-" + hashlib.sha256(ma.encode("utf-8")).hexdigest(), "bam_gt_ma_legacy"


def lord(p: float, ho: str, gt_ma: str, muc_tieu: float | None = None,
         ghi_so: bool = True) -> dict:
    """Adapter LORD cu; giu tuong thich nhung gan nhan provenance legacy."""
    plan_hash, nguon_dinh_danh = _plan_hash_legacy(gt_ma)
    ra = lord_v2(
        p, plan_hash, lane="legacy", family=ho,
        data_release="LEGACY_UNSPECIFIED", decision_generation=THE_HE_CONG,
        muc_tieu=muc_tieu, ghi_so=ghi_so, gt_ma_nguon=gt_ma or None)
    ra["legacy_adapter"] = True
    ra["identity_source"] = nguon_dinh_danh
    ra["gt_ma_legacy"] = gt_ma
    return ra


# ---------------------------------------------------------------------- CONG
def he_so_khop_rui_ro(loi_he, loi_bh) -> tuple[float | None, str]:
    """He so dua HE ve dung muc rui ro cua MOC. Tra (k, ghi_chu).

    VI SAO CAN. Cong 1 so TONG LAI cua he voi mua-giu. Nhung mot he chon loc
    chi o trong thi truong 16-18% thoi gian con moc o 100%: do khong phai so
    cung don vi, va tren tai san co xu huong tang thi cong 1 tro thanh BAT KHA
    voi moi co che chon loc. Do that 30/08/2026 tren US500M.D1 — chan IBS cua
    V6 dat Sharpe 0,992 va Calmar 0,961 (moc 0,885 / 0,756), qua cong 2 va 3,
    chet o cong 1 vi 33,2% < 48,5%.

    Cau hoi dung: *cung mot muc rui ro thi ben nao lai hon?*

    `k = min(k_bien_dong, k_sut_giam)` — he KHONG duoc phep chiu rui ro hon moc
    o BAT KY thuoc do nao trong hai. Lay min chu khong lay rieng bien dong la
    co y: mot he co bien dong thap nhung duoi trai day (lai deu, thua tham)
    se duoc bien dong cho phep nhan len rat cao, va chinh dang do la dang du an
    nay da gap bon lan (gong lo V6, TP 0,5%, DCA DongDongTV, nhoi lenh).

    Moi thanh phan chi phi deu TUYEN TINH theo phoi nhiem (spread ~ |dv|, phi
    qua dem ~ |v|, lai gop ~ v) nen nhan chuoi loi suat rong voi k cho dung
    ket qua chay lai engine voi `don_bay=k` — da doi chieu that: 77,64% ca hai
    cach. Nho vay khong phai chay lai backtest.

    Tra k=None khi khong khop duoc: chuoi qua ngan, bien dong 0, hoac **don
    bay lam chay tai khoan** (co bar nao do 1+k*r <= 0). Truong hop cuoi quan
    trong: mot he khong the nhan len ma khong pha san thi khong duoc huong loi
    the cua phep nhan do.
    """
    a = np.asarray(loi_he, dtype=float); a = a[np.isfinite(a)]
    b = np.asarray(loi_bh, dtype=float); b = b[np.isfinite(b)]
    if len(a) < 30 or len(b) < 30:
        return None, "chuoi qua ngan de khop rui ro"
    sa, sb = a.std(ddof=1), b.std(ddof=1)
    if not (sa > 0 and sb > 0):
        return None, "bien dong bang 0 - khong khop duoc"
    k = float(sb / sa)

    def _dd(r):
        e = np.cumprod(1.0 + r)
        return float((e / np.maximum.accumulate(e) - 1.0).min())

    dd_a, dd_b = _dd(a), _dd(b)
    if dd_a < 0:
        k = min(k, float(abs(dd_b) / abs(dd_a)))
    if k <= 0:
        return None, "he so khong duong"
    if float((1.0 + k * a).min()) <= 0.0:
        return None, f"don bay {k:.2f}x lam chay tai khoan - khong khop duoc"
    return k, f"khop rui ro k={k:.3f}x (bien dong va sut giam, lay muc chat hon)"


def khong_co_phan_bu_rui_ro(kq_bh) -> bool:
    """Moc mua-giu cua tai san nay co mang phan bu rui ro khong?

    Tren FX, giu mot cap tien te khong duoc tra gi: giu EURCAD 8 nam ra Sharpe
    -0,02. Vi vay `max(bh, 0)` lam cong 1-2-3 gan nhu CHO KHONG o do.

    Do tren so cai 30/08/2026: qua cong 1 la **37,4% tren FX** so voi **0,4%
    tren chi so** — cung mot cong, de hon 90 lan. Va 79% gia thuyet dang la FX,
    tuc ngan sach FDR tu chay ve noi cong de nhat.

    Khi moc khong mang thong tin thi ba cong so-voi-moc cung khong mang thong
    tin, nen ganh nang phai chuyen sang cong THONG KE: siet nguong p.
    """
    sh = getattr(kq_bh, "sharpe", None)
    if sh is None:
        try:
            r = np.asarray(kq_bh.loi, dtype=float); r = r[np.isfinite(r)]
            sh = float(r.mean() / r.std(ddof=1) * np.sqrt(252)) if len(r) > 30 else None
        except Exception:
            return False
    return sh is not None and sh <= 0.20


def xet(df, kq_he, kq_bh, cp, gt_ma: str = "", ho: str = "chung",
        da_dang_ky: bool = False, tren_holdout: bool = False,
        lai_suat=None, chay_placebo: bool = True,
        economic_plan_hash: str | None = None, lane: str | None = None,
        family: str | None = None, data_release: str | None = None,
        decision_generation: int | str = THE_HE_CONG,
        che_do: str = "giao_dich", ghi_so: bool = True,
        du_lieu_moi: bool = False) -> dict:
    """Chay day du cong. Tra ve dict co ``verdict`` va ``ly_do``.

    ``che_do``:
      * ``"giao_dich"`` (mac dinh) - hoi "co giao dich duoc khong". Doi chi phi
        DO DUOC. Day la che do duy nhat co the tra ``PASS``.
      * ``"nghien_cuu"`` - hoi "co CO CHE khong". Dung cho chuoi khong mua duoc
        (chi so Yahoo 20-56 nam). Chi phi chi la khai bao nen dieu kien 7 khong
        con la dieu kien CHAN; no van duoc ghi lai va verdict cao nhat chi la
        ``CO_CO_CHE``, khong bao gio ``PASS``.

    Vi sao can tach: dieu kien 7 truot lam `da_truot_re` khong rong, nen placebo
    KHONG chay, nen FDR nhan p=1 va dieu kien 5 va 10 cung truot theo. Ba dieu
    kien truot deu tu MOT goc. Ket qua la 22 nam NIKKEI khong do duoc gi ca, ke
    ca voi tin hieu do chinh xac 85% (Sharpe 9,0).

    Loi goi confirmation moi nen truyen ``economic_plan_hash``, ``lane``,
    ``family`` va ``data_release``. Neu khong, adapter ``gt_ma``/``ho`` duoc
    dung de code cu tiep tuc chay, nhung provenance FDR se mang nhan legacy.
    """
    n = nguong()
    ss = DO.so_sanh(kq_he, kq_bh)
    he, bh = ss["he"], ss["mua_giu_net"]
    al = ss["alpha_vs_mua_giu"]

    phoi_nhiem = he.get("phoi_nhiem", 0.0) or 0.0
    # Siet nguong p khi (a) phoi nhiem gan 100% - alpha de lan voi drift; hoac
    # (b) moc khong mang phan bu rui ro, luc do ba cong so-voi-moc khong loc
    # duoc gi va ganh nang phai roi sang cong thong ke.
    moc_rong = khong_co_phan_bu_rui_ro(kq_bh)
    siet = (phoi_nhiem > n["phoi_nhiem_siet"]) or moc_rong
    p_can = n["p_siet"] if siet else n["p_alpha"]
    p_can_pl = n["p_siet"] if siet else n["p_placebo"]

    dk: dict[str, bool] = {}
    ly_do: list[str] = []

    def _sanh(a, b):
        return (a is not None) and (b is not None) and (a > b)

    # Moc la mua-giu, NHUNG co san tuyet doi 0. Ly do: tren FX, mua-giu khong co
    # phan bu rui ro - giu EURCAD 8 nam ra Sharpe -0,02. "Thang mua-giu" o day
    # gan nhu cho khong. San 0 khong giet V6 (Sharpe 0,95 do tren MT5 that).
    #
    # THE HE 5 (30/08/2026): cong 1 so o muc RUI RO BANG NHAU. Xem
    # `he_so_khop_rui_ro`. Khong khop duoc thi quay ve so tho - khong khop duoc
    # KHONG duoc thanh mot cach de qua cong de hon.
    # `getattr` co chu y: mot vai duong goi (va bo test) dua vao moc khong mang
    # chuoi loi suat. Thieu so lieu thi LUI VE so tho, khong duoc vo - va cung
    # khong duoc am tham thanh mot duong de qua cong de hon.
    _loi_he = getattr(kq_he, "loi", None)
    _loi_bh = getattr(kq_bh, "loi", None)
    if _loi_he is None or _loi_bh is None:
        k_khop, ghi_chu_khop = None, "moc khong mang chuoi loi suat"
    else:
        k_khop, ghi_chu_khop = he_so_khop_rui_ro(_loi_he, _loi_bh)
    lai_khop = he.get("tong_lai_pct")
    if k_khop is not None:
        _a = np.asarray(_loi_he, dtype=float); _a = _a[np.isfinite(_a)]
        lai_khop = float((np.prod(1.0 + k_khop * _a) - 1.0) * 100.0)
        ly_do.append(ghi_chu_khop + f" -> lai khop {lai_khop:.2f}% "
                     f"(tho {he.get('tong_lai_pct')}%)")
    else:
        ly_do.append("KHONG khop rui ro duoc (" + ghi_chu_khop + ") - so lai tho")
    dk["1_loi_hon_mua_giu"] = _sanh(lai_khop, max(bh.get("tong_lai_pct") or 0, 0.0))
    dk["2_sharpe_hon_mua_giu"] = _sanh(he.get("sharpe"), max(bh.get("sharpe") or 0, 0.0))
    dk["3_calmar_hon_mua_giu"] = _sanh(he.get("calmar"), max(bh.get("calmar") or 0, 0.0))

    t_al = al.get("t_alpha")
    a_al = al.get("alpha_nam_pct")
    bac_tu_do = max(he.get("so_bar", 100) - 2, 1)
    p_al = float(2 * (1 - stats.t.cdf(abs(t_al), bac_tu_do))) if t_al is not None else None
    dk["4_alpha_duong_co_y_nghia"] = bool(
        a_al is not None and a_al > 0 and p_al is not None and p_al <= p_can)

    dk["6_dang_ky_truoc"] = bool(da_dang_ky)

    # dieu kien bo sung cua ban nay
    chi_phi_do_duoc = cp.do_tin in ("DO", "SAN")
    if che_do == "nghien_cuu":
        # Ghi lai su that, nhung khong dung no lam cong chan: chuoi nghien cuu
        # khong mua duoc nen khong the do chi phi that, va do khong phai ly do
        # de khong tra loi duoc cau hoi "co co che khong".
        ra_them_nghien_cuu = not chi_phi_do_duoc
        if ra_them_nghien_cuu:
            ly_do.append(f"che do nghien cuu: chi phi do_tin={cp.do_tin} chi la "
                         "khai bao - ket luan chi noi ve CO CHE, khong noi ve "
                         "kha nang giao dich")
    else:
        dk["7_chi_phi_do_duoc"] = chi_phi_do_duoc
        if not dk["7_chi_phi_do_duoc"]:
            ly_do.append(f"mo hinh chi phi do_tin={cp.do_tin} (chua do tu du lieu/san)")
    dk["8_du_lenh"] = (kq_he.so_lenh or 0) >= n["so_lenh_toi_thieu"]

    # ---- TANG 2 KINH TE: chan martingale tra hinh -------------------------
    try:
        _rr = rr_thuc_te(kq_he.vi_the, kq_he.loi)
    except Exception:
        _rr = 0.0
    dk["12_rr_thuc_te"] = _rr >= n["rr_thuc_te_toi_thieu"]
    if not dk["12_rr_thuc_te"]:
        ly_do.append("rr thuc te %.3f < %.2f - lai TB mot lenh thang qua nho so "
                     "voi lo TB mot lenh thua (dang martingale tra hinh)"
                     % (_rr, n["rr_thuc_te_toi_thieu"]))

    try:
        import numpy as _np
        _lai_rong = float(_np.nansum(kq_he.loi))
        _phi_sp = float(abs(kq_he.chi_phi_spread or 0.0))
    except Exception:
        _lai_rong = _phi_sp = 0.0
    dk["13_edge_vuot_spread"] = (_phi_sp <= 0) or (
        _lai_rong >= n["edge_tren_spread_toi_thieu"] * _phi_sp)
    if not dk["13_edge_vuot_spread"]:
        ly_do.append("lai rong %.4f < %.1fx chi phi spread %.4f - edge mong so "
                     "voi chi phi, dung loai edge song duoc ngoai doi"
                     % (_lai_rong, n["edge_tren_spread_toi_thieu"], _phi_sp))

    # ---- 11: khong duoc song bang KHE GIA o moc dao ngay ------------------
    # Do 30/08/2026: tren FX H4 cua kho nay, bar 00:00 MO THAP gia tao roi hoi
    # trong than bar (khe -3,16 bps o EURGBP, -2,47 EURCAD, -4,61 AUDCAD; moi
    # gio khac ~0). Om dung bar do = mua o gia mo BIA, ban o gia dong THAT:
    # +5,78 bps/ngay ~ 14%/nam hien vat thuan. Mot ung vien
    # (EURGBP.H4.mua_qua_dem) dat t_alpha = 14,52 va di het cong re nho dung
    # cai do - khong mot cong nao trong 10 cong cu nhin thay.
    #
    # Chan CHINH XAC chu khong chan ca nguon: chi loai khi chien luoc DON
    # phoi nhiem vao gio bi nhiem. Mot co che vo tinh nam gio do bang muc
    # trung binh thi khong an them gi.
    dk["11_khong_an_khe_dao_ngay"] = True
    try:
        _kh = DL.khe_gio_bat_thuong(df)
        # Truc thoi gian phai lay dung cai ma phep do da dung: tren khung ngay
        # `khe_gio_bat_thuong` nhom theo THU, khong theo gio (chi co mot gio).
        _ten_o = "gio" if _kh.get("theo", "gio") == "gio" else "thu"
        if _kh["do_duoc"] and _kh["gio"]:
            _v = np.abs(np.nan_to_num(np.asarray(kq_he.vi_the, dtype=float)))
            _g = np.asarray(df.index.hour if _ten_o == "gio" else df.index.dayofweek)
            _m = np.isin(_g, _kh["gio"])
            if _m.any() and (~_m).any():
                _trong, _ngoai = float(_v[_m].mean()), float(_v[~_m].mean())
                if _trong > 0 and _trong > 1.25 * max(_ngoai, 1e-9):
                    dk["11_khong_an_khe_dao_ngay"] = False
                    ly_do.append(
                        f"phoi nhiem don vao {_ten_o} co khe dao ngay {_kh['gio']} "
                        f"({_trong:.2f} so voi {_ngoai:.2f} o {_ten_o} khac; khe "
                        f"{ {g: round(_kh['khe_bps'][g], 2) for g in _kh['gio']} } bps) "
                        "- dang song bang bao gia luc dao ngay, khong bang co che")
                else:
                    ly_do.append(f"co {_ten_o} khe dao ngay {_kh['gio']} nhung phoi "
                                 f"nhiem khong don vao do ({_trong:.2f} vs {_ngoai:.2f})")
        elif not _kh["do_duoc"]:
            ly_do.append("chua do duoc khe theo thoi gian (qua it bar hoac chi mot o) "
                         "- KHONG ket luan la sach")
    except Exception as _e:
        ly_do.append(f"khong do duoc khe dao ngay: {type(_e).__name__}")

    giai_doan = DO.hieu_qua_giai_doan(kq_he.loi, kq_he.index, k=4)
    if siet:
        co_duong = any((g.get("cagr_pct") or -1) > 0 for g in giai_doan)
        dk["9_siet_phoi_nhiem_cao"] = co_duong
        if moc_rong:
            ly_do.append("moc mua-giu khong co phan bu rui ro (Sharpe <= 0,20) "
                         f"-> ba cong so-voi-moc khong loc duoc gi, siet p ve {p_can}")
        if phoi_nhiem > n["phoi_nhiem_siet"]:
            ly_do.append(f"phoi nhiem {phoi_nhiem:.1%} > {n['phoi_nhiem_siet']:.0%} "
                         f"-> siet nguong p ve {p_can}")

    # ------------------------------------------------------------------
    # Placebo van chi chay sau cac cong re de tranh lang phi CPU. Khac V2 cu,
    # cong re KHONG duoc phep lam bien mat mot plan khoi chuoi FDR: neu plan da
    # cham confirmation ma truot truoc placebo, no van tieu dung mot suat p=1.
    #
    # Truoc do placebo (995 luot backtest, 88 giay) chay cho MOI ung vien, ke
    # ca ung vien da truot dieu kien 1 vi lai thap hon mua-giu. Hai hau qua,
    # ca hai deu do that tren so cai:
    #   - Toc do: 94% ngan sach CPU cua QUANTLAB do vao ung vien da chet.
    # Placebo la de PHAN XU thu con song, khong phai de kham nghiem tu thi.
    da_truot_re = [k for k, v in dk.items() if not v]
    pl, kq_fdr = None, None
    p_hop_thanh_fdr = 1.0
    if not chay_placebo:
        dk["5_placebo"] = False
        ly_do.append("chua chay placebo")
    elif da_truot_re:
        dk["5_placebo"] = False
        ly_do.append("khong chay placebo: da truot cong re hon (" +
                     ", ".join(da_truot_re) + ") - confirmation van tieu thu suat FDR p=1")
    else:
        pl = placebo(df, kq_he, cp, lai_suat=lai_suat)
        dk["5_placebo"] = bool(pl["p_xau_nhat"] <= p_can_pl)
        if pl.get("null_hop_le") is False:
            ly_do.append("ca hai null deu khong hop le - placebo khong dang tin")
            dk["5_placebo"] = False
        if pl.get("bootstrap_hop_le") is False:
            ly_do.append("null bootstrap bi KS bac bo -> chi ket luan bang null quay vong")

        # Cong PASS van la GIAO cua alpha va placebo - dieu do khong doi, no
        # nam o `dk["5_placebo"]` ngay tren.
        #
        # Nhung p dua vao CHUOI FDR thi chi duoc la p_alpha. Ly do la do phan
        # giai, khong phai do triet ly:
        #
        #   placebo chay n_bootstrap hoan vi -> p nho nhat no CO THE tra la
        #   1/(n+1) = 1/200 = 0,005. Con nguong LORD giam theo 1/j^1.6 va tut
        #   xuong duoi 0,005 ngay tu PHEP THU THU 4.
        #
        # Vi vay `max(p_alpha, p_placebo)` >= 0,005 > nguong, tuc tu phep thu
        # thu tu tro di KHONG GI CO THE QUA, bat ke edge manh den dau. Do do
        # bai kiem luc (`thu_luc_cong`) bao DAT=False: mot tin hieu do chinh
        # xac 60% cho Sharpe 2,97 va alpha +19,9%/nam van bi chan, va chan boi
        # dung mot dieu kien la `10_qua_fdr_online`. 346 phan quyet FAIL truoc
        # 21/08/2026 deu sinh ra tu day.
        #
        # p_alpha la thong ke lien tuc nen co the xuong tuy y sau, hop voi mot
        # nguong giam dan. Placebo van chan duoc ung vien xau, chi thoi dong
        # vai tro trong SO HOC cua FDR.
        p_alpha_hop_le, thay_alpha = _p_bao_thu(p_al)
        p_placebo_hop_le, thay_placebo = _p_bao_thu(pl.get("p_xau_nhat"))
        null_hong = pl.get("null_hop_le") is False
        if not thay_alpha and not thay_placebo and not null_hong:
            # Placebo truot -> plan van tieu mot suat, nhung voi p=1: khong duoc
            # cap reject cho thu ma placebo da bac bo.
            p_hop_thanh_fdr = p_alpha_hop_le if dk["5_placebo"] else 1.0

    if tren_holdout:
        # `ghi_so=False` danh cho DO DAC (do luc, hieu chuan cong, nha may null):
        # do la phep thu tren mot ORACLE tong hop da biet dap an, khong phai mot
        # quyet dinh ve thi truong. Truoc 24/08 no van ghi so: mot vong quet be
        # mat viet **~80 dong FDR moi phut** vao ho `do_luc` (do that: 174 dong
        # trong 2 phut), tuc bo do dac tu lam hong chinh cai thuoc no dang doc -
        # va lam ban so quyet dinh cua he thong.
        if economic_plan_hash is not None:
            kq_fdr = lord_v2(
                p_hop_thanh_fdr, economic_plan_hash,
                lane=lane, family=family, data_release=data_release,
                decision_generation=decision_generation, ghi_so=ghi_so,
                gt_ma_nguon=gt_ma or None)
        else:
            kq_fdr = lord(p_hop_thanh_fdr, ho, gt_ma, ghi_so=ghi_so)
        # ---------------------------------------------------------------
        # CONG FDR: TAT theo quyet dinh cua chu du an 04/09/2026.
        #
        # Lap luan cua ho: *"o thi truong nay khong ai di share mieng banh minh
        # co ca, ta dang tim kiem nhung manh vun. Toi xay mot cai pheu lon het
        # co de dao ca mot bai bien lay mot hat vang, thi cau di add cai tieu
        # chuan khong phu hop vao"*.
        #
        # SO DO DUOC TRUOC KHI TAT - ghi lai de sau nay khong ai doc nham day
        # la mot loi:
        #
        #   703 ket qua co cham cong FDR
        #     0  truot CHI vi FDR
        #     0  qua het moi chan khac roi chet o FDR
        #
        # Tuc **FDR chua tung loai mot ung vien nao du tieu chuan**. Cai giet la
        # placebo (98,0%), alpha khong co y nghia (97,8%), va MDE. Nen tat no
        # KHONG mo them mot he nao - do la mot phep bo thu vo hai, khong phai
        # mot phep noi long nguy hiem.
        #
        # VA MOT LOI THAT DA TIM RA, la ly do chu du an dung: he tinh tien FDR
        # **58,8 lan cho MOT y tuong** (294 phep thu trong ho
        # `quay_ve_trung_binh@cp2` chi la 5 y tuong nhan luoi tham so x tai san
        # x khung). Nguong vi vay sup tu 0,012929 (j=1) xuong 0,000004 (j=294) -
        # **3.200 lan**. Chuan cho "mot y tuong, nhieu bien the" la hieu chinh
        # best-of-N (White Reality Check / Hansen SPA): mot suat, null rong hon.
        # Tinh N suat doc lap la sai ve phuong phap, khong chi ve khau vi.
        #
        # BAT LAI: dat `"bat_fdr": true` trong config/nguong.json. So FDR van
        # duoc ghi binh thuong (`lord_v2` van chay), chi la ket qua cua no
        # khong con la mot dieu kien PASS - nen khi nao muon danh gia lai thi
        # du lieu van con nguyen.
        _bat_fdr = bool(nguong().get("bat_fdr", False))
        if _bat_fdr:
            dk["10_qua_fdr_online"] = bool(kq_fdr["bac_bo"])
        if _bat_fdr and not kq_fdr["bac_bo"]:
            ly_do.append(
                f"p_hop_thanh={p_hop_thanh_fdr} khong qua nguong FDR online "
                f"{kq_fdr['nguong_fdr']:.5f} (phep thu thu {kq_fdr['thu_tu_trong_ho']} "
                f"cua epoch '{kq_fdr['ho']}')")

    # --- CHAN CUNG hay NHAN CANH BAO (xem NHAN_MEM o dau file)
    cd_cong = che_do_cong()
    qua_het_chan = all(dk.values())
    if cd_cong == "nhan":
        thieu = [k for k in dk if k not in NHAN_MEM and k not in CHAN_CUNG]
        if thieu:
            raise KeyError("dieu kien chua phan loai chan/nhan: %s" % thieu)
        qua_het = all(v for k, v in dk.items() if k not in NHAN_MEM)
    else:
        qua_het = qua_het_chan
    nhan = [NHAN_MEM[k] for k, v in dk.items() if k in NHAN_MEM and not v]

    if qua_het and che_do == "nghien_cuu":
        # Tran cua che do nghien cuu. Khong bao gio PASS: chua ai chung minh
        # duoc rang thu nay giao dich duoc.
        verdict = "CO_CO_CHE"
        ly_do.append("qua het cong o che do nghien cuu - moi noi duoc ve CO CHE, "
                     "can chuoi giao dich duoc + chi phi DO DUOC de chung nhan")
    elif qua_het and not da_dang_ky and cd_cong != "nhan":
        verdict = "EXPLORATORY"
        ly_do.append("qua het cong nhung KHONG dang ky truoc -> khong bao gio PASS")
    elif qua_het and not tren_holdout:
        verdict = "UNG_VIEN"
        ly_do.append("qua cong tren tap kham pha - can xac nhan tren holdout")
    elif qua_het:
        verdict = "PASS"
    else:
        verdict = "FAIL"
        ly_do += [f"truot: {k}" for k, v in dk.items() if not v]

    # Ban cu tinh song song de khong mat dau vet: doc `verdict_chan` la biet
    # ung vien nay co qua duoc cong hoc thuat hay khong, du che do nao dang bat.
    if qua_het_chan and che_do == "nghien_cuu":
        v_chan = "CO_CO_CHE"
    elif qua_het_chan and not da_dang_ky:
        v_chan = "EXPLORATORY"
    elif qua_het_chan and not tren_holdout:
        v_chan = "UNG_VIEN"
    elif qua_het_chan:
        v_chan = "PASS"
    else:
        v_chan = "FAIL"
    if nhan:
        ly_do += ["NHAN: " + x for x in nhan]

    ra = {
        "verdict": verdict, "dieu_kien": dk, "ly_do": ly_do,
        "nhan": nhan, "verdict_chan": v_chan, "che_do_cong": cd_cong,
        "so_sanh": ss, "placebo": pl, "giai_doan": giai_doan,
        "da_chay_placebo": pl is not None,
        "truot_cong_re": da_truot_re,
        "p_alpha": round(p_al, 5) if p_al is not None else None,
        "p_hop_thanh_fdr": p_hop_thanh_fdr if tren_holdout else None,
        "nguong_dung": {"p_alpha": p_can, "p_placebo": p_can_pl, "siet": siet},
        "chi_phi_do_tin": cp.do_tin, "chi_phi_canh_bao": cp.canh_bao,
    }

    # PHOI NHIEM HOLDOUT TICH LUY (them 01/09/2026).
    #
    # FDR dem suat theo HO, va ho duoc phep tach khi doi cau truc mo hinh chi
    # phi - dung theo THIET_KE muc 7. Nhung khi ho tach thi `j` ve 1 va nguong
    # LORD nhay tu 5,0e-6 len 0,0129 (**noi gap 2.600 lan**), trong khi HOLDOUT
    # van la holdout cu: no khong duoc lam moi theo mo hinh chi phi.
    #
    # Do tren so cai: 375 gia thuyet / 1.272 lan cham = 3,39 lan moi gia thuyet;
    # mot gia thuyet cham 10 lan; 3 gia thuyet di tu FAIL sang PASS qua cac lan
    # cham lai - ca ba deu trong ro cach ly. Tung buoc deu hop le, cai thieu la
    # khong ai dem TONG so lan nhin.
    #
    # Ha xuong UNG_VIEN chu khong FAIL: gia thuyet do co the that, chi la CHUA
    # duoc xac nhan - va xac nhan doi du lieu chua ai nhin, khong phai mot lan
    # nhin lai nua. `du_lieu_moi=True` la cua de lai cho truong hop holdout that
    # su dai ra; no phai duoc KHAI, khong duoc tu suy.
    if tren_holdout and gt_ma and not du_lieu_moi:
        try:
            lan_truoc = SO.phoi_nhiem_holdout(gt_ma)
        except Exception:
            lan_truoc = 0
        ra["lan_nhin_holdout_truoc_do"] = lan_truoc
        if lan_truoc > n["lan_nhin_holdout_truoc_do_toi_da"] and ra["verdict"] == "PASS":
            ra["verdict"] = "UNG_VIEN"
            ly_do.append(
                f"gia thuyet nay da nhin holdout {lan_truoc} lan truoc lan nay. "
                "Mot PASS o lan nhin lai khong phai mot xac nhan (ho FDR da tach "
                "theo the he chi phi nen `j` ve 1, nhung holdout thi khong moi "
                "lai). Can du lieu chua ai nhin; neu holdout that su dai ra thi "
                "khai `du_lieu_moi=True`.")

    # DAU HIEU NHIN TRUOC: hieu chuan tu canary (THIET_KE muc 12b)
    if t_al is not None and t_al > 5:
        ra["canh_bao_nang"] = (
            f"t_alpha = {t_al:+.2f} > 5. Tren tap sang nay, LECH MOT BAR tang t trung vi "
            "tu -0,74 len +10,05. Phai gia dinh CO NHIN TRUOC cho toi khi chung minh nguoc lai.")
        if verdict in ("PASS", "UNG_VIEN"):
            ra["verdict"] = "NGHI_NHIN_TRUOC"

    if kq_fdr:
        ra["fdr"] = kq_fdr
    return ra


if __name__ == "__main__":
    print(json.dumps(nguong(), ensure_ascii=False, indent=1))
