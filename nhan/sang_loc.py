# -*- coding: utf-8 -*-
"""sang_loc.py - PHEU BON VONG: V0 van tay -> V1 re -> V2 kinh te -> V3 phan chung.

Ban dau (DS, 23/08) co dung khung bon vong nhung DO NHAM DOI TUONG: moi vong deu
goi `MP.mua_giu(df, cp)` roi do chinh MUA-GIU, khong he sinh tin hieu cua co che.
Hau qua: moi ung vien tren cung mot tai san nhan y het mot phan quyet, va phan
quyet do khong lien quan gi toi co che dang xet. Bo test van xanh vi khong bai
nao chay duong that.

Ban nay do DUNG THU: sinh tin hieu bang `nhan/mau.py`, chay qua `nhan/mo_phong.py`
voi chi phi that, roi so voi mua-giu tren CUNG chuoi.

BA LUAT CUA PHEU (xem `ds/2308/04_VONG_TEST.md`):

1. **Chi V4 tieu ngan sach thong ke.** V0-V3 chi ton CPU, nen duoc phep chay
   rong. Module nay DUNG LAI truoc V4 va tra `SAN_SANG_V4` - viec dong bang ke
   hoach va cham holdout la cua `nhan/cong.py` qua duong `xac_nhan` da co.
   Viet lai cong o day la tao ra cong thu hai, va hai cong thi khong bao gio
   dong y voi nhau.

2. **Ba gia tri, khong phai hai.** `NHAN` / `LOAI` / `CHUA_DU_LUC`. Gop cai thu
   ba vao "loai" la cach nem mat chien luoc tot ma khong ai biet: vong kham pha
   22/08 co 692 ung vien bi chan vi THIEU LUC, doc thanh "692 cai khong co edge"
   la doc sai hoan toan.

3. **So sanh bang LAI TREN PHOI NHIEM, khong bang tong lai.** Mot he chi o
   trong thi truong 5% thoi gian khong the co tong lai bang mua-giu, nhung lai
   tren mot don vi phoi nhiem co the gap nhieu lan - va phoi nhiem la thu nhan
   len duoc bang don bay, con edge thi khong.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import (do_luong as DO, do_luc as DLUC, du_lieu as DL,
                      mau as MAU, mo_phong as MP, so as SO)
else:
    from . import (do_luong as DO, do_luc as DLUC, du_lieu as DL,
                   mau as MAU, mo_phong as MP, so as SO)

LAB = Path(__file__).resolve().parent.parent
TIEU_CHI_FILE = LAB / "config" / "tieu_chi.json"

NHAN = "NHAN"
LOAI = "LOAI"
CHUA_DU_LUC = "CHUA_DU_LUC"
SAN_SANG_V4 = "SAN_SANG_V4"
#: Khong du luc TREN MOT TAI SAN, nhung phep thu phan chung noi co che song o
#: CA LOP -> con mot duong nua truoc khi bo: kiem tren RO.
#:
#: Do that 23/08 (200 cua so, `chay_gop_vs_don.py`): voi chi so My, gop 9 tai
#: san ha MDE tu 3,0 xuong **1,5 bps/lenh**. Nhung voi vang va FX thi gop KHONG
#: ha duoc gi, va o FX no con lam TE DI o vung giua (delta 2 bps: don 74% so voi
#: gop 62,5%). Ly do: gop chi mua duoc luc khi co che that su song o da so chan;
#: gop them nhung chan co che khong song chi them nhieu.
#:
#: Nen dieu kien leo thang la `pham_vi == CO_CO_CHE`, khong phai "cu thieu luc
#: thi gop". Do la khac biet giua mot buoc leo thang co ly do va mot buoc thu
#: lai cho may man.
NEN_GOP = "NEN_GOP"

#: Ly do truot co nghia "chua DO DUOC", khong phai "khong co edge".
#:
#: Phan biet nay quyet dinh mot ung vien co duoc leo thang sang duong GOP hay
#: khong. `sharpe_am` va `thua_mua_giu_tren_phoi_nhiem` la cau tra loi THAT ve
#: co che - gop them chan chi lam loang. Con "it lenh qua de ket luan" thi
#: khong noi gi ve co che ca, va do dung la thu ma gop ca lop chua duoc.
LY_DO_THIEU_LUC = frozenset({
    "thieu_lenh_de_ket_luan", "khong_du_bar", "qua_it_lenh",
})


#: Bo dem trong bo nho. Moi lan LOAI deu ghi lai - day la cach duy nhat de sau
#: nay tra loi duoc "neu noi tieu chi X thi bao nhieu thu song lai" bang mot
#: truy van, thay vi chay lai tat ca.
BI_LOAI: list[dict] = []
CHO_THEM_DU_LIEU: list[dict] = []

MAC_DINH = {
    "phien_ban": "2026-08-23",
    "v1": {"kich_hoat_min": 0.002, "kich_hoat_max": 0.98, "so_lenh_min": 30,
           "so_bar_min": 1500},
    "v2": {"lai_tren_phoi_nhiem_min": 1.0, "sharpe_min": 0.0,
           "lenh_moi_thang_min": 1.0, "ty_le_bar_lon_nhat_max": 0.40,
           "so_lenh_du_luc": 100,
           # Tan suat toi thieu THEO HO. Nguong chung 1 lenh/thang loai oan ca
           # ho `lich`: turn-of-month vao 12 lan/nam la DUNG BAN CHAT co che,
           # khong phai khiem khuyet. Do that tren US500CASH D1: cuoi_thang cho
           # 0,81 lenh/thang va bi loai vi tan suat - trong khi ly do THAT de
           # loai no la lai tren phoi nhiem 0,23. Loai dung thu nhung sai ly do
           # thi lan sau noi nguong se noi nham cho.
           "lenh_moi_thang_min_theo_ho": {"lich": 0.4, "vi_mo": 0.2,
                                          "phien": 2.0}},
    "v3": {"cach_biet_nhom_min": 0.2, "so_doan_duong_min": 2, "so_doan": 3},
}


def khoa_la(ngoai: dict, chuan: dict | None = None) -> list[str]:
    """Khoa co trong file cau hinh nhung KHONG co trong `MAC_DINH`.

    Vi sao phai co: `_doc_tieu_chi` gop file ngoai de len mac dinh, nen mot khoa
    go sai ten van duoc nhan - va no khong dieu khien gi ca. Do 24/08 tren
    `config/tieu_chi.json` dang dung: 5 nut CHET.

        v2.ty_le_lenh_lon_nhat_max   ma doc `ty_le_bar_lon_nhat_max` (LENH/BAR)
        v3.placebo_min               khong cho nao doc; nguong placebo that
                                     nam trong `cong.san_p_placebo`
        v3.cach_biet_nhom_min        chi ton tai trong MAC_DINH, khong ai doc
        v0.van_tay_spec              ca muc v0/v4 khong duoc doc
        v4.xem_nhan_cong_py

    Nut chet nguy hiem hon nut sai gia tri: van nut ma khong co gi doi, nen
    nguoi van tin la minh da noi/siet tieu chi.
    """
    chuan = chuan if chuan is not None else MAC_DINH
    la: list[str] = []
    for k, v in (ngoai or {}).items():
        if k == "phien_ban":
            continue
        if k not in chuan:
            la.append(k)
            continue
        if isinstance(v, dict) and isinstance(chuan.get(k), dict):
            la += [f"{k}.{x}" for x in v if x not in chuan[k]]
    return sorted(la)


def _doc_tieu_chi() -> dict:
    tc = json.loads(json.dumps(MAC_DINH))
    la: list[str] = []
    if TIEU_CHI_FILE.exists():
        try:
            ngoai = json.loads(TIEU_CHI_FILE.read_text(encoding="utf-8-sig"))
            la = khoa_la(ngoai)
            for k, v in ngoai.items():
                if isinstance(v, dict) and isinstance(tc.get(k), dict):
                    tc[k].update(v)
                else:
                    tc[k] = v
        except Exception:
            pass
    # Khong nem loi: pheu chay 24/7, mot cau hinh la khong duoc lam dung day
    # chuyen. Nhung phai de lai dau vet doc duoc.
    tc["_khoa_la"] = la
    if la:
        import warnings
        warnings.warn(f"tieu_chi.json co khoa khong duoc doc: {la}", stacklevel=2)
    return tc


TC = _doc_tieu_chi()
PHIEN_BAN = TC.get("phien_ban", "khong_ro")


def _ghi_loai(nhan, vong, tieu_chi, gia_tri, nguong):
    BI_LOAI.append({"nhan": nhan, "vong": vong, "tieu_chi": tieu_chi,
                    "gia_tri": gia_tri, "nguong": nguong,
                    "phien_ban": PHIEN_BAN})


def _ghi_cho_them(nhan, vong, ly_do, can_gi=""):
    CHO_THEM_DU_LIEU.append({"nhan": nhan, "vong": vong, "ly_do": ly_do,
                             "can_gi": can_gi})


def xoa_bo_dem() -> None:
    BI_LOAI.clear()
    CHO_THEM_DU_LIEU.clear()


def lay_bo_dem() -> list[dict]:
    return list(BI_LOAI)


def lay_cho_them() -> list[dict]:
    return list(CHO_THEM_DU_LIEU)


def _ket(kl, vong, ly_do, **them):
    return dict(ket_luan=kl, vong=vong, ly_do=ly_do, phien_ban=PHIEN_BAN, **them)


# ------------------------------------------------------------------ V0
def van_tay_phep_thu(ten_mau: str, tham_so: dict, ma: str, khung: str) -> str:
    """Danh tinh cua MOT PHEP THU. Trung nghia la da chay roi, khong phai
    'da nam trong hang doi' - hai thu do khac han nhau.

    Ban dau V0 hoi `candidate_queue` xem van tay co trong do khong. Nhung moi
    ung vien di qua pheu deu duoc RUT RA TU chinh hang doi do, nen dieu kien
    luon dung va V0 loai sach 100% dau vao that.
    """
    khoa = json.dumps({"mau": ten_mau, "tham_so": tham_so or {},
                       "ma": ma, "khung": khung}, sort_keys=True)
    return SO.van_tay(khoa)


def v0_van_tay(ten_mau, tham_so, ma, khung, da_chay: set | None = None):
    vt = van_tay_phep_thu(ten_mau, tham_so, ma, khung)
    if da_chay is not None and vt in da_chay:
        _ghi_loai(vt, "V0", "trung_phep_thu", vt[:12], "da_chay")
        return LOAI, "trung_phep_thu", vt
    gt_ma = f"{ma}.{khung}.{ten_mau}." + (
        "_".join(f"{k}{v}" for k, v in (tham_so or {}).items()) or "mac_dinh")
    if SO.mot("SELECT id FROM ket_qua WHERE gt_ma=? AND superseded_by IS NULL",
              gt_ma):
        _ghi_loai(vt, "V0", "da_co_ket_qua", gt_ma[:40], "khong chay lai")
        return LOAI, "da_co_ket_qua", vt
    return NHAN, "", vt


# ------------------------------------------------------------------ V1
def v1_sang_re(nhan, ten_mau, tham_so, ma, khung, df):
    """Cai nay co phai mot chien luoc khong? Chua tinh chi phi, chua tinh lai."""
    v1 = TC["v1"]
    n = len(df)
    if n < v1["so_bar_min"]:
        _ghi_cho_them(nhan, "V1", "khong_du_bar", f"{n}/{v1['so_bar_min']} bar")
        return CHUA_DU_LUC, "khong_du_bar", {}

    try:
        th = MAU.sinh(ten_mau, df, tham_so or {})
    except Exception as e:
        _ghi_loai(nhan, "V1", "sinh_tin_hieu_loi", f"{type(e).__name__}", "chay duoc")
        return LOAI, f"sinh_tin_hieu_loi: {str(e)[:60]}", {}

    th = np.asarray(th, dtype=float)
    if th.size != n or not np.isfinite(th).all():
        _ghi_loai(nhan, "V1", "tin_hieu_hong", f"size={th.size}", f"size={n}, huu han")
        return LOAI, "tin_hieu_hong", {}

    kich_hoat = float(np.mean(np.abs(th) > 1e-12))
    so_doi = int(np.count_nonzero(np.diff(np.sign(th)) != 0))
    do = {"kich_hoat": round(kich_hoat, 4), "so_doi_vi_the": so_doi, "so_bar": n}

    if kich_hoat < v1["kich_hoat_min"]:
        _ghi_loai(nhan, "V1", "kich_hoat_qua_thap", kich_hoat, v1["kich_hoat_min"])
        return LOAI, "kich_hoat_qua_thap", do
    if kich_hoat > v1["kich_hoat_max"]:
        # Kich hoat gan 100% = mua-giu tra hinh, khong phai co che.
        _ghi_loai(nhan, "V1", "mua_giu_tra_hinh", kich_hoat, v1["kich_hoat_max"])
        return LOAI, "mua_giu_tra_hinh", do
    if so_doi < v1["so_lenh_min"]:
        _ghi_cho_them(nhan, "V1", "qua_it_lenh",
                      f"{so_doi}/{v1['so_lenh_min']} lan doi vi the")
        return CHUA_DU_LUC, "qua_it_lenh", do
    return NHAN, "", do


# ------------------------------------------------------------------ V2
def v2_sang_kinh_te(nhan, ten_mau, tham_so, ma, khung, df, cp):
    """No song qua chi phi that khong? So voi mua-giu tren CUNG chuoi."""
    v2 = TC["v2"]
    try:
        th = MAU.sinh(ten_mau, df, tham_so or {})
        kq = MP.chay(df, th, cp, ma=ma, khung=khung)
        bh = MP.mua_giu(df, cp, ma=ma, khung=khung)
    except Exception as e:
        _ghi_cho_them(nhan, "V2", "khong_chay_duoc", f"{type(e).__name__}: {str(e)[:60]}")
        return CHUA_DU_LUC, "khong_chay_duoc", {}

    if kq.loi is None or len(kq.loi) == 0:
        _ghi_cho_them(nhan, "V2", "khong_co_loi_suat", "")
        return CHUA_DU_LUC, "khong_co_loi_suat", {}

    cs = DO.chi_so(kq.loi, kq.index, kq.vi_the)
    cs_bh = DO.chi_so(bh.loi, bh.index)
    nam = max(len(df) / _bar_moi_nam(khung), 1e-9)

    # LAI TREN PHOI NHIEM - xem luat 3 o dau file.
    lai = float(np.sum(kq.loi))
    lai_bh = float(np.sum(bh.loi))
    pn = float(getattr(kq, "phoi_nhiem", 0.0) or 0.0)
    pn_bh = float(getattr(bh, "phoi_nhiem", 0.0) or 0.0) or 1.0
    ty_le = (lai / pn) / (lai_bh / pn_bh) if pn > 0 and lai_bh > 0 else (
        float("inf") if pn > 0 and lai > 0 and lai_bh <= 0 else 0.0)

    do = {"sharpe": cs.get("sharpe"), "sharpe_mua_giu": cs_bh.get("sharpe"),
          "lai_tren_phoi_nhiem": round(ty_le, 3) if np.isfinite(ty_le) else None,
          "so_lenh": kq.so_lenh, "lenh_moi_thang": round(kq.so_lenh / (nam * 12), 2),
          "phoi_nhiem": round(pn, 4)}

    if kq.so_lenh < v2["so_lenh_du_luc"]:
        _ghi_cho_them(nhan, "V2", "thieu_lenh_de_ket_luan",
                      f"{kq.so_lenh}/{v2['so_lenh_du_luc']} lenh")
        return CHUA_DU_LUC, "thieu_lenh_de_ket_luan", do

    ho_mau = (MAU.MAU.get(ten_mau) or {}).get("ho") or "khac"
    nguong_ts = (v2.get("lenh_moi_thang_min_theo_ho") or {}).get(
        ho_mau, v2["lenh_moi_thang_min"])
    do["ho"] = ho_mau
    if do["lenh_moi_thang"] < nguong_ts:
        _ghi_loai(nhan, "V2", "tan_suat", do["lenh_moi_thang"], nguong_ts)
        return LOAI, "tan_suat_qua_thap", do

    if ty_le < v2["lai_tren_phoi_nhiem_min"]:
        _ghi_loai(nhan, "V2", "lai_tren_phoi_nhiem", do["lai_tren_phoi_nhiem"],
                  v2["lai_tren_phoi_nhiem_min"])
        return LOAI, "thua_mua_giu_tren_phoi_nhiem", do

    if (cs.get("sharpe") or -9) < v2["sharpe_min"]:
        _ghi_loai(nhan, "V2", "sharpe", cs.get("sharpe"), v2["sharpe_min"])
        return LOAI, "sharpe_am", do

    # Le thuoc mot bar: bar lai nhat chiem bao nhieu phan tong lai duong.
    duong = kq.loi[kq.loi > 0]
    if duong.size and float(np.sum(duong)) > 0:
        ty_bar = float(np.max(duong) / np.sum(duong))
        do["ty_le_bar_lon_nhat"] = round(ty_bar, 3)
        if ty_bar > v2["ty_le_bar_lon_nhat_max"]:
            _ghi_loai(nhan, "V2", "le_thuoc_mot_bar", ty_bar,
                      v2["ty_le_bar_lon_nhat_max"])
            return LOAI, "le_thuoc_mot_bar", do

    # NHAY CHI PHI: nhan doi chi phi ma doi dau thi khong duoc di tiep khi chi
    # phi moi chi la KHAI BAO. Bang chi phi mac dinh chi la du phong.
    try:
        cp2 = _nhan_doi_chi_phi(cp)
        kq2 = MP.chay(df, th, cp2, ma=ma, khung=khung)
        lai2 = float(np.sum(kq2.loi))
        do["nhay_chi_phi"] = bool(lai > 0 >= lai2)
        if do["nhay_chi_phi"] and str(getattr(cp, "do_tin", "KHAI")) == "KHAI":
            _ghi_cho_them(nhan, "V2", "nhay_chi_phi_ma_chi_phi_chua_do",
                          "can do spread that truoc khi ket luan")
            return CHUA_DU_LUC, "nhay_chi_phi_ma_chi_phi_chua_do", do
    except Exception:
        pass

    return NHAN, "", do


def _bar_moi_nam(khung: str) -> float:
    return {"M1": 372000, "M5": 74400, "M15": 24800, "M30": 12400,
            "H1": 6200, "H4": 1550, "D1": 252, "W1": 52}.get(str(khung).upper(), 252)


def _nhan_doi_chi_phi(cp):
    """Nhan doi moi thanh phan chi phi. Dung `bien_the()` co san cua
    `MoHinhChiPhi` chu khong deepcopy - lop do da co duong nhan ban dung."""
    doi = {}
    for t in ("spread_frac_chung", "truot_gia_frac", "phi_nam_mua", "phi_nam_ban"):
        try:
            doi[t] = float(getattr(cp, t, 0.0)) * 2.0
        except Exception:
            pass
    if getattr(cp, "spread_frac_theo_gio", None):
        doi["spread_frac_theo_gio"] = {k: v * 2.0
                                       for k, v in cp.spread_frac_theo_gio.items()}
    try:
        return cp.bien_the(**doi)
    except Exception:
        from nhan import chi_phi as CP
        return CP.MoHinhChiPhi(ma=getattr(cp, "ma", ""), do_tin="KHAI", **doi)


# ------------------------------------------------------------------ V3
#: Ket qua phep thu phan chung, do mot lan moi mau moi tien trinh. Phep thu
#: nay quet ca ro tai san nen dat; nhung no chi phu thuoc MAU va KHO DU LIEU,
#: khong phu thuoc ung vien, nen dem lai la dung.
_DEM_PHAM_VI: dict = {}


def pham_vi_cua(ten_mau: str) -> dict:
    """Phep thu phan chung THAT cho mot mau: co che chay o lop tai san no
    tuyen bo, va KHONG chay o lop doi chung.

    Truoc day `v3_phan_chung` chi nhan ket qua nay tu ngoai vao (QUANTLAB
    truyen). Chay pheu doc lap - vi du trong nha may null/luc - thi phan quan
    trong nhat cua V3 bi bo qua im lang.
    """
    if ten_mau in _DEM_PHAM_VI:
        return _DEM_PHAM_VI[ten_mau]
    try:
        from nhan import pham_vi as PV
        ho = (MAU.MAU.get(ten_mau) or {}).get("ho") or "khac"
        khung = PV.khung_cua_ho(ho)
        _DEM_PHAM_VI[ten_mau] = PV.kiem_pham_vi(ten_mau, khung)
    except Exception as e:
        _DEM_PHAM_VI[ten_mau] = {"loi": f"{type(e).__name__}: {str(e)[:80]}"}
    return _DEM_PHAM_VI[ten_mau]


def v3_phan_chung(nhan, ten_mau, tham_so, ma, khung, df, cp, pham_vi=None,
                  sharpe=None, tu_do_pham_vi=False):
    """No la co che, hay chi la dac tinh chung cua gia?

    Phep thu phan chung that nam o `nhan/pham_vi.kiem_pham_vi` va da chay trong
    `quantlab`. O day nhan ket qua do tu ngoai vao (tranh vong lap import) va
    chi lam them phan on dinh theo thoi gian.
    """
    v3 = TC["v3"]
    do = {}

    if pham_vi is None and tu_do_pham_vi:
        pham_vi = pham_vi_cua(ten_mau)
    if pham_vi:
        kl_pv = pham_vi.get("ket_luan")
        do["pham_vi"] = kl_pv
        do["ly_do_pham_vi"] = str(pham_vi.get("ly_do"))[:120]
        if kl_pv == "CHUA_DU_MAU":
            _ghi_cho_them(nhan, "V3", "pham_vi_chua_du_mau", do["ly_do_pham_vi"])
            return CHUA_DU_LUC, "pham_vi_chua_du_mau", do
        if kl_pv in ("KHONG_PHAN_BIET", "KHONG_CO_CO_CHE"):
            _ghi_loai(nhan, "V3", "pham_vi", kl_pv, "CO_CO_CHE")
            return LOAI, f"pham_vi_{str(kl_pv).lower()}", do

    try:
        # PHAI truyen Sharpe do duoc o V2. Truyen None thi `du_luc_de_kiem`
        # khong co gi de so voi MDE va tra ve "khong du luc" cho MOI ung vien -
        # tuc V3 chan sach dau vao ma nhin nhu mot ket luan.
        luc = DLUC.du_luc_de_kiem(sharpe, ma, khung)
        do["du_luc"] = bool(luc.get("du_luc", True))
        if not do["du_luc"]:
            # LEO THANG THAY VI BO. Neu phep thu phan chung da noi co che song o
            # ca lop thi thieu luc tren MOT tai san chua phai cau tra loi cuoi.
            if str(do.get("pham_vi")) == "CO_CO_CHE":
                _ghi_cho_them(nhan, "V3", "thieu_luc_don_le_nen_gop",
                              f"pham_vi=CO_CO_CHE; kiem tren ro lop "
                              f"'{(MAU.MAU.get(ten_mau) or {}).get('ho')}'")
                return NEN_GOP, "thieu_luc_don_le_nhung_co_co_che", do
            _ghi_cho_them(nhan, "V3", "thieu_luc", str(luc.get("ly_do"))[:100])
            return CHUA_DU_LUC, "thieu_luc", do
    except Exception:
        pass

    # On dinh theo thoi gian: chia N doan, chay CO CHE tren tung doan.
    try:
        k = int(v3.get("so_doan", 3))
        buoc = len(df) // k
        diem = []
        for i in range(k):
            d = df.iloc[i * buoc:] if i == k - 1 else df.iloc[i * buoc:(i + 1) * buoc]
            if len(d) < 200:
                continue
            th = MAU.sinh(ten_mau, d, tham_so or {})
            r = MP.chay(d, th, cp, ma=ma, khung=khung)
            if r.loi is not None and len(r.loi):
                diem.append(DO.chi_so(r.loi, r.index, r.vi_the).get("sharpe") or 0.0)
        do["sharpe_tung_doan"] = [round(x, 3) for x in diem]
        so_duong = sum(1 for x in diem if x > 0)
        if len(diem) >= 2 and so_duong < int(v3["so_doan_duong_min"]):
            _ghi_loai(nhan, "V3", "on_dinh_thoi_gian", so_duong,
                      v3["so_doan_duong_min"])
            return LOAI, "khong_on_dinh_theo_thoi_gian", do
    except Exception as e:
        _ghi_cho_them(nhan, "V3", "khong_do_duoc_on_dinh", str(e)[:80])
        return CHUA_DU_LUC, "khong_do_duoc_on_dinh", do

    return NHAN, "", do


# ------------------------------------------------------------------ PHEU
def chay_pheu(ten_mau: str, tham_so: dict | None, ma: str, khung: str,
              df=None, cp=None, pham_vi: dict | None = None,
              da_chay: set | None = None, tu_do_pham_vi: bool = False,
              cham_holdout: bool = False) -> dict:
    """Chay het V0-V3 cho MOT phep thu. Dung truoc V4 - xem luat 1 o dau file.

    KHONG truyen `df` -> tu nap va **chi lay nua TRAIN** (`hai_nua(df, 0.6)`).

    Sua 24/08/2026. Luat 1 o dau file noi ro "viec dong bang ke hoach va cham
    holdout la cua `nhan/cong.py`", nhung ham nay lai nap CA CHUOI khi caller
    khong truyen `df` - va `chay_pheu_ung_vien` cua QUANTLAB dung dung duong do.
    Tuc ung vien duoc SANG LOC tren du lieu co chua holdout, roi duoc XAC NHAN
    tren chinh holdout do.

    Do tac dong trong ngay tren ca 107 ung vien dang xep hang: **4/107 doi phan
    quyet**, va ca bon deu la `LOAI -> CHUA_DU_LUC` (mat bar nen thieu luc),
    khong cai nao tu bi loai thanh song. Ket luan cu vi the khong bi lat, nhung
    ro ri phai dong lai truoc khi co ket qua duong tinh dau tien - luc do moi
    khong con cach nao noi duoc no sach hay khong.

    `cham_holdout=True` danh cho phep DO DAC co y chay tren ca chuoi (hieu chuan
    cong, nha may null). Duong do van co the truyen thang `df`.
    """
    tham_so = tham_so or {}
    if ten_mau not in MAU.MAU:
        return _ket(LOAI, "V0", "mau_khong_co_trong_thu_vien")

    kl, ly_do, vt = v0_van_tay(ten_mau, tham_so, ma, khung, da_chay)
    if kl != NHAN:
        return _ket(kl, "V0", ly_do, van_tay=vt)

    if df is None:
        try:
            df = DL.nap(ma, khung)
            if not cham_holdout:
                df = DL.hai_nua(df, 0.6)[0]
        except Exception as e:
            _ghi_cho_them(vt, "V1", "khong_nap_duoc_du_lieu", f"{ma}.{khung}")
            return _ket(CHUA_DU_LUC, "V1", f"khong_nap_duoc_du_lieu: {str(e)[:50]}",
                        van_tay=vt)
    if cp is None:
        cp = _chi_phi_cua(ma)

    do_tong = {}
    for ten_vong, ham, doi_so in (
            ("V1", v1_sang_re, (vt, ten_mau, tham_so, ma, khung, df)),
            ("V2", v2_sang_kinh_te, (vt, ten_mau, tham_so, ma, khung, df, cp)),
            ("V3", v3_phan_chung, None),   # doi so dung o duoi, can Sharpe cua V2
    ):
        if ten_vong == "V3":
            doi_so = (vt, ten_mau, tham_so, ma, khung, df, cp, pham_vi,
                      do_tong.get("sharpe"), tu_do_pham_vi)
        kl, ly_do, do = ham(*doi_so)
        do_tong.update(do or {})
        if kl != NHAN:
            # LEO THANG SOM SANG DUONG GOP.
            #
            # Nhan NEN_GOP truoc day chi duoc gan BEN TRONG V3, nhung san so
            # lenh toi thieu giet co che THUA LENH ngay o V2 - va "thua lenh
            # tren tung tai san, day lenh khi gop ca lop" chinh la ho so ma
            # duong GOP sinh ra de xu ly. Ket qua: pheu tu chan mot lop co che
            # khoi con duong danh cho no.
            #
            # Do that 30/08/2026 tren be mat D1, va no chan dung 2 trong 3 co
            # che co tin hieu that:
            #   rsi_dao_chieu  pham_vi=CO_CO_CHE, 121/122 o chet o V1/V2 -> 0 NEN_GOP
            #   stoch_qua_ban  pham_vi=CO_CO_CHE, 122/122 o chet o V1/V2 -> 0 NEN_GOP
            #   ibs_bat_day    o toi duoc V3     ->            26 NEN_GOP
            #
            # Chi leo thang khi THIEU LUC, khong khi THIEU EDGE: `sharpe_am`,
            # `thua_mua_giu_tren_phoi_nhiem`, `le_thuoc_mot_bar` la nhung cau
            # tra loi THAT ve co che va khong duoc gop de cuu.
            #
            # Day la thay doi NHAN, khong phai thay doi QUYET DINH: NEN_GOP la
            # nhan cua tang kham pha, khong tieu mot suat FDR nao. Suat chi bi
            # tieu khi `quantlab.xac_nhan_gop` chay.
            if (kl == CHUA_DU_LUC and ly_do in LY_DO_THIEU_LUC
                    and str((pham_vi or {}).get("ket_luan")) == "CO_CO_CHE"):
                _ghi_cho_them(vt, ten_vong, "thieu_luc_don_le_nen_gop",
                              f"{ly_do}; pham_vi=CO_CO_CHE")
                return _ket(NEN_GOP, ten_vong, "thieu_luc_don_le_nhung_co_co_che",
                            van_tay=vt, do=do_tong)
            return _ket(kl, ten_vong, ly_do, van_tay=vt, do=do_tong)

    return _ket(SAN_SANG_V4, "V3", "", van_tay=vt, do=do_tong)


def _chi_phi_cua(ma: str):
    """Chi phi DO DUOC neu co; khong co thi lay bang mac dinh theo lop tai san.

    Bang mac dinh lay tu `2308/04_VONG_TEST.md` muc 2 - deu la so DO THAT tren
    terminal cua du an, khong phai gia dinh. Nhung van danh dau `do_tin='KHAI'`
    de V2 biet ma than trong khi ket qua nhay theo chi phi.
    """
    from nhan import chi_phi as CP
    # Duong DUNG: `CP.tu_du_lieu` do spread tu chinh cot `spread` cua bar va
    # tra swap that theo `swap_mode`. Bang mac dinh chi la du phong khi tai san
    # do chua co so do.
    # Do chi phi tren khung CO SPREAD THAT, khong nhat thiet la D1: ban D1 dai
    # nhat cua mot ma thuong khong co cot spread (xem `du_lieu.khung_do_spread`).
    for khung_cp in (DL.khung_do_spread(ma), "D1"):
        if not khung_cp:
            continue
        try:
            c = CP.tu_du_lieu(ma, DL.nap(ma, khung_cp))
            if c is not None and str(getattr(c, "do_tin", "KHAI")) != "KHAI":
                return c
        except Exception:
            continue
    lop = _lop_cua(ma)
    # spread MOT CHIEU theo frac cua gia; phi giu theo ty le/nam
    bang = {
        "chi_so": (0.9e-4 / 2, 0.05),
        "vang": (0.7e-4 / 2, 0.075),
        # Hang hoa: XM do duoc phi qua dem **0,00%/nam** tren OILCASH/NGASCASH.
        # KHONG dat 0 o day. Swap 0 tren CFD dung hop dong tuong lai khong phai
        # la mien phi - chi phi giu nam trong DUONG CONG hop dong va hien ra o
        # buoc noi khi dao han (memory `xm-co-futures-cfd`). Chua do duoc buoc
        # do nen lay tam bang chi so va de `do_tin='KHAI'` chan cua PASS.
        "hang_hoa": (0.9e-4 / 2, 0.05),
        "fx_major": (0.9e-4 / 2, 0.02),
        "fx_cheo": (3.5e-4 / 2, 0.02),
    }
    sp, phi = bang.get(lop, bang["fx_cheo"])
    return CP.MoHinhChiPhi(ma=ma, spread_frac_chung=sp, truot_gia_frac=sp * 0.5,
                           phi_nam_mua=phi, phi_nam_ban=phi, do_tin="KHAI",
                           nguon="bang_mac_dinh_2308")


#: Phoi nhiem thuoc lop CHI SO CO PHIEU. Doi chieu bang TEN PHOI NHIEM
#: (`chi_phi.chuan_hoa_phoi_nhiem`), khong bang chuoi con cua ten file.
LOP_CHI_SO = {
    "US500", "US100", "US30", "US2000", "US400", "GER40", "UK100", "FRA40",
    "EU50", "JP225", "AUS200", "HK50", "SWI20", "SPA35", "NETH25", "CA60",
    "IT40", "SA40", "NOR25", "SE30", "CHINA50", "CHN50", "TAIWAN", "KOSPI",
    "SENSEX", "BOVESPA", "IN50",
}
#: Kim loai quy - phi qua dem rieng, khong chung voi hang hoa.
LOP_KIM_LOAI = {"XAUUSD", "XAGUSD", "XAUEUR", "XAUAUD", "XAUGBP", "XAUCHF",
                "XAUJPY", "XAGEUR", "XAGAUD"}
#: Nang luong + nong san.
LOP_HANG_HOA = {"USOIL", "UKOIL", "NGAS", "DONG", "NGO", "DAUTUONG",
                "CORN", "SBEAN", "WHEAT", "HGCOP", "COFFE", "COCOA", "SUGAR",
                "COTTO"}
_FX_MAJOR = {"EURUSD", "USDJPY", "GBPUSD", "USDCHF", "AUDUSD", "USDCAD",
             "NZDUSD"}


def _lop_cua(ma: str) -> str:
    """Lop tai san cua `ma`, doi chieu theo PHOI NHIEM chu khong theo ten file.

    Ban cu do chuoi con trong ten (`"US500" in m`, `"NAS" in m`) va bo sot ca
    mot mang. Do 24/08 tren be mat D1 (122 ma) - moi ma duoi day bi xep vao
    `fx_cheo`, tuc an spread 3,5 bps khu hoi va phi giu 2%/nam:

        SP500, XM_US100CASH, XM_US2000CASH, XM_AUS200CASH,
        YH_DOWJONES, YH_EUSTOXX50, YH_HANGSENG, YH_IBEX35, YH_AEX,
        YH_RUSSELL2000, YH_SENSEX, YH_SMI, YH_TAIWAN, YH_TSX, YH_BOVESPA
        (chi so, dung ra ~0,45 bps va ~5%/nam)
        XM_SILVER, YH_BAC, YH_DAUWTI, YH_DONG, YH_KHIDOT, YH_NGO, YH_DAUTUONG
        (kim loai / hang hoa - truoc day khong co lop nao)

    Chieu sai KHONG dong nhat: spread bi tinh THUA ~3,9 lan con phi giu bi tinh
    THIEU 2,5 lan. Voi co che giu lau (phi giu ap dao - xem memory
    `sp500-final-system`) thi tong chi phi bi tinh THIEU, tuc cong DE HON no
    tuong; voi co che giu ngan thi nguoc lai.
    """
    from nhan import chi_phi as CP
    pn = CP.chuan_hoa_phoi_nhiem(str(ma))
    if pn in LOP_CHI_SO:
        return "chi_so"
    if pn in LOP_KIM_LOAI or pn.startswith("XAU") or pn.startswith("XAG"):
        return "vang"
    if pn in LOP_HANG_HOA:
        return "hang_hoa"
    if pn in _FX_MAJOR:
        return "fx_major"
    return "fx_cheo"


if __name__ == "__main__":
    import pprint
    xoa_bo_dem()
    pprint.pprint(chay_pheu("ibs_bat_day", {"nguong": 0.2}, "US500CASH", "D1"))
    pprint.pprint(lay_bo_dem())
    pprint.pprint(lay_cho_them())
