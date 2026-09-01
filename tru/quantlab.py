# -*- coding: utf-8 -*-
"""Quantlab V2: two isolated research lanes sharing only validated primitives.

``candidate_validation`` consumes sourced CandidateArtifacts and never invents
an asset/timeframe scope. ``autonomous_discovery`` owns template search and its
own batch/family namespace. Both lanes freeze a full QuantPlan before a result
window is touched.

The historical 60/40 holdout has already been inspected adaptively. It remains
useful for exploratory diagnostics, but this module never emits PASS from it.
Positive results wait for genuinely forward data.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nhan import nen as NEN
from nhan import (canary as CANARY, chi_phi as CP, cong as CONG, do_luc as DLUC,
                  do_luong as DO, du_lieu as DL, mau as MAU, mo_phong as MP,
                  ngu_phap as NP, quant_plan as QP, so as SO)

TRU = "QUANTLAB"
LANE_CANDIDATE = "candidate_validation"
LANE_AUTONOMOUS = "autonomous_discovery"
LEGACY_HOLDOUT_STATUS = "exposed_legacy"
# Toi da bao nhieu ung vien mot cap (tai san, khung) duoc dang ky moi luot quet.
# Truoc 16/08 khong co han: mot lan quet dang ky het moi thu thang mua-giu tren
# train, va vi tat ca deu vao cung mot ho FDR nen ung vien thu 291 gap nguong
# 0,00001 - khong the qua du no dung. Chon cai TOT NHAT roi dung lai thi ngan
# sach thong ke dung vao cho dang dung.
TOI_DA_DANG_KY_MOI_CAP = 3
REPORTS = Path(__file__).resolve().parent.parent / "reports"
PLAN_DIR = REPORTS / "quant_plans"
PHEU_CURSOR = REPORTS / "pheu_cursor.json"
CANDIDATE_CURSOR = REPORTS / "quantlab_candidate_cursor.json"
AUTONOMOUS_PROGRESS = REPORTS / "quantlab_autonomous_progress.json"
# Uu tien tai san CO cot spread that (do duoc chi phi) roi moi den phan con lai.
UU_TIEN_TAI_SAN = ["EURCAD", "GBPCAD", "AUDNZD", "EURGBP", "AUDCAD", "AUDCHF",
                   "EURNZD", "NZDCAD", "XAUUSDM", "US500M", "US500CASH"]
KHUNG_QUET = ["H1", "H4", "D1"]
SO_BAR_TOI_THIEU = 1500

# ---------------------------------------------------------- BE MAT KHAM PHA
#: Ngoai danh sach uu tien, mo rong be mat theo DO DAI LICH SU chu khong theo
#: ten. Ly do thuan tuy thong ke - nguong Sharpe nho nhat con NHIN THAY duoc ty
#: le nghich voi can bac hai so nam holdout (do that trong `nhan/do_luc.py`):
#:
#:     US500M    D1   2,6 nam -> 1,54        YH_DAX     D1  15,4 nam -> 0,74
#:     EURCAD    H4   5,4 nam -> 1,39        YH_NIKKEI  D1  22,6 nam -> 0,65
#:                                           YH_NASDAQ  D1  22,2 nam -> 0,54
#:
#: Moi tai san them vao deu an mot suat ngan sach FDR, nen suat do phai tieu o
#: cho co nhieu LUC nhat: chuoi dai nhat. Mot Sharpe 0,7 co that ton tai o day
#: la KHONG THE THAY tren 5 nam EURCAD nhung THAY DUOC tren 22 nam NASDAQ.
TOI_THIEU_NAM_MO_RONG = 12.0
#: Tran tong so tai san mo rong. Khong duoc bo tran nay de "quet ca 189 bang":
#: do la CAU TAI SAN (`nhan/pham_vi.py` dong 7-12), va cai tot nhat trong 189 x
#: 3 khung se dep du thi truong khong co gi ca.
TRAN_MO_RONG = 18
#: ... va tran theo LOP tai san, neu khong thi 6 chuoi dai nhat deu la chi so
#: co phieu va nhom doi chung cua phep thu phan chung khong con ai.
TRAN_MOI_LOP = 6
#: Tran THAP hon cho lop chi dong vai NHOM DOI CHUNG - lop khong xuat hien trong
#: bat ky `PHAM_VI[...]["hop"]` nao. Chung can co mat de phan chung, nhung khong
#: can nhieu: moi slot chung chiem la mot slot khong danh cho chuoi co the mang
#: co che that. Do that 22/08: 5 chuoi hang hoa chiem 5/18 suat mo rong, day
#: XAUUSD (20,8 nam, MUA DUOC) ra ngoai trong khi vang uu tien XAUUSDM chi co
#: 8,7 nam va MDE cua no la None o ca H1 lan H4.
TRAN_LOP_DOI_CHUNG = 3


def _lop_doi_chung() -> set[str]:
    """Lop khong duoc ho co che nao khai la `hop` -> chi dung de phan chung."""
    try:
        from nhan import pham_vi as PV
        co_the_mang = {l for k in PV.PHAM_VI.values() for l in (k.get("hop") or [])}
        return {l for l in PV.LOAI if l not in co_the_mang}
    except Exception:
        return set()


def _tai_san_kha_dung() -> list[str]:
    """Uu tien (mua duoc, chi phi do duoc) TRUOC, roi den chuoi DAI nhat.

    Ban truoc 22/08 loc bo sung bang `m.endswith("_D1_XM")` tren KHOA cua kho -
    nhung khoa da bi cat duoi ten file roi (`AUDJPY_D1_xm.parquet` -> khoa
    `AUDJPY`), nen dieu kien do KHONG BAO GIO dung. Ket qua: `them` luon rong va
    ca he chi nhin thay 11 tai san uu tien, trong khi kho co 80 bang OHLC >= 12
    nam. Day la ly do nguong phat hien ket o 1,39 thay vi 0,54.
    """
    ds = DL.bang_ohlc()
    ra = [m for m in UU_TIEN_TAI_SAN if m in ds]
    # Xep hang theo so nam DUNG DUOC, khong phai so nam co trong file. Do dat
    # hon (phai nap that) nen chi do cho ung vien da qua nguong tho.
    diem: dict[str, float] = {}
    for m, v in ds.items():
        if m in ra or v["uoc_so_nam"] < TOI_THIEU_NAM_MO_RONG:
            continue
        if v["nguon"] == "ngoai":
            diem[m] = float(DL.nam_dung_duoc(m, v["khung_goc"]).get("nam") or 0.0)
        else:
            diem[m] = float(v["uoc_so_nam"])
    theo_lop: dict[str, int] = {}
    them: list[str] = []
    for m, _n in sorted(diem.items(), key=lambda x: (-x[1], x[0])):
        if diem[m] < TOI_THIEU_NAM_MO_RONG:
            continue
        lop = CP._loai_tai_san(m)
        tran_lop = TRAN_LOP_DOI_CHUNG if lop in _lop_doi_chung() else TRAN_MOI_LOP
        if theo_lop.get(lop, 0) >= tran_lop:
            continue
        theo_lop[lop] = theo_lop.get(lop, 0) + 1
        them.append(m)
        if len(them) >= TRAN_MO_RONG:
            break
    return ra + them


#: Bao nhieu tai san SAN + bao nhieu chuoi NGHIEN CUU khi quet mot mau.
#: Mot mau x mot tai san x mot khung = mot dang ky = mot suat FDR, nen con so
#: nay la ngan sach thong ke chu khong phai tham so hieu nang.
QUET_MAU_SAN = 6
QUET_MAU_NGHIEN_CUU = 4


def _tai_san_quet_mau() -> list[str]:
    """Tai san dung khi quet MOT mau (dau ra cua SEEKER/NGHI).

    Phai co ca hai lan: chi lay 6 tai san dau nhu ban cu thi mot mau lay tu tai
    lieu chi bao gio duoc thu tren 5 nam FX - tuc chi thay duoc co che nao co
    Sharpe > 1,39, va gan nhu moi co che that deu nam duoi nguong do.
    """
    ds = _tai_san_kha_dung()
    san = [m for m in ds if DL.nguon_tai_san(m) == "san"][:QUET_MAU_SAN]
    ngc = [m for m in ds if DL.nguon_tai_san(m) == "ngoai"][:QUET_MAU_NGHIEN_CUU]
    return san + ngc


def _khung_cua(ma: str) -> list[str]:
    """Khung quet duoc cua mot tai san. KHONG hoi khung nho hon du lieu goc.

    80% be mat moi la bang D1; hoi H1/H4 tren chung thi `DL.nap` nem ValueError
    ("khong noi suy nguoc") va vong quet dot 2/3 luot vao ngoai le.
    """
    goc = (DL.kho().get(ma.upper()) or {}).get("khung_goc", "?")
    if goc not in DL.PHUT_KHUNG:
        return []
    return [k for k in KHUNG_QUET if DL.PHUT_KHUNG[k] >= DL.PHUT_KHUNG[goc]]


def _che_do(cp) -> str:
    """`giao_dich` neu chi phi DO DUOC, nguoc lai `nghien_cuu`.

    Khong phai mot cong tac tay: no la HE QUA cua `cp.do_tin`. Chuoi nao do
    duoc chi phi thi phai tra loi cau "co giao dich duoc khong" (va co the
    PASS); chuoi nao khong do duoc thi cau do khong tra loi duoc, chi con cau
    "co CO CHE khong" (tran la CO_CO_CHE).

    Doi chieu voi ban truoc: chuoi khong do duoc chi phi truot dieu kien 7 ->
    khong chay placebo -> FDR nhan p=1 -> truot luon dieu kien 5 va 10. Ba dieu
    kien truot tu MOT goc, va he tra ve FAIL nhu the da kiem dinh xong. Tuc 56
    nam NIKKEI truoc day chi sinh ra mot dong FAIL vo nghia.
    """
    return "giao_dich" if getattr(cp, "do_tin", "KHAI") in ("DO", "SAN") else "nghien_cuu"


def _ho_fdr(ho: str, che_do: str) -> str:
    """Ten ho FDR. Hai che do KHONG duoc nam chung mot chuoi quyet dinh.

    Cung ly do voi `@cp{THE_HE}`: mot chuoi 56 nam khong mua duoc va mot chuoi
    5 nam mua duoc tra loi HAI CAU HOI khac nhau. Tron chung thi ngan sach FDR
    cua cau hoi giao dich duoc bi chuoi nghien cuu tieu mat.
    """
    return f"{ho}@cp{CP.THE_HE}" + ("@nghien_cuu" if che_do == "nghien_cuu" else "")


def _cua_so(df) -> str:
    return f"{str(df.index[0])[:10]}..{str(df.index[-1])[:10]}"


# Bo nho dem trong MOT luot chay: nap parquet + do chi phi la viec giong nhau
# cho moi gia thuyet tren cung mot cap. Truoc 16/08 mot luot xac nhan 17 gia
# thuyet co the nap lai cung mot file 17 lan.
_DEM_DU_LIEU: dict = {}
_DATA_RELEASES: dict[tuple[str, str], str] = {}


def _nap(ma: str, khung: str):
    """(df, train, holdout, cp_train, cp_holdout) - tinh mot lan moi cap.

    Voi chuoi nguon NGOAI (chi so, khong mua duoc) thi CAT ve doan co open THAT
    truoc khi chia train/holdout. Bat buoc, khong phai tuy chon: SP500 co 98,6
    nam nhung 1967-1999 la gia bia, va chia 60/40 tren ca chuoi thi holdout roi
    tron vao vung bia. Cat truoc roi moi chia - nguoc lai thi khong sua duoc.

    Chuoi nguon SAN khong cat: bao gia lien tuc 24/5 co `open[i]==close[i-1]` o
    20-60% mot cach hop le, va nguong 0,60 chay ngay giua cai hump do (do that
    2018-2019 tren MOI cap FX cua kho: 0,54-0,62; cac nam khac 0,20-0,35), nen
    cat theo no la cat theo mot con so ngau nhien chu khong theo chat luong.
    """
    k = (ma, khung)
    if k not in _DEM_DU_LIEU:
        df = DL.nap(ma, khung)
        if DL.nguon_tai_san(ma) == "ngoai":
            df = DL.cat_theo_chat_luong(df, ma)[0]
        train, hold = DL.hai_nua(df, 0.6)
        _DEM_DU_LIEU[k] = (df, train, hold,
                           CP.tu_du_lieu(ma, train), CP.tu_du_lieu(ma, hold))
        if len(_DEM_DU_LIEU) > 12:
            _DEM_DU_LIEU.pop(next(iter(_DEM_DU_LIEU)))
    return _DEM_DU_LIEU[k]


# ------------------------------------------------------------- TANG KHAM PHA
def kham_pha(ma: str, khung: str, gioi_han_to_hop: int = 0) -> dict:
    """Quet mau x tham so tren TRAIN. Khong sinh p-value chinh thuc.
    Cai nao thang mua-giu -> dang ky gia thuyet + xep hang xac nhan."""
    df, train, _h, cp, _cph = _nap(ma, khung)
    bc = DL.kiem(df, ma)
    if not bc["dung_duoc"] or len(df) < SO_BAR_TOI_THIEU:
        return {"ma": ma, "khung": khung, "bo_qua": bc.get("canh_bao", ["qua ngan"])}
    che_do = _che_do(cp)

    # BO QUA SOM cap khong phan xu duoc gi. `mde is None` nghia la khong muc do
    # chinh xac nao (toi 0,70 - tuc doan dung dau loi suat 70% so bar) vuot duoc
    # cong tren cap nay. Quet no la dot CPU de sinh ra nhung ung vien chac chan
    # bi cong kha thi chan ngay sau do. Do that 22/08: 5/57 cap roi vao day, het
    # la H1 cua FX/vang - noi chi phi moi bar an het edge.
    try:
        m_luc = DLUC.mde_cua(ma, khung)
    except Exception:
        m_luc = {"mde": 0.0}
    if m_luc.get("mde") is None:
        SO.ghi_chi_so("kham_pha_bo_qua_vo_luc", 1.0,
                      {"tai_san": ma, "khung": khung, "so_bar": m_luc.get("so_bar")})
        return {"ma": ma, "khung": khung, "che_do": che_do, "mde": None,
                "bo_qua": [f"khong muc nao trong thang do chinh xac vuot duoc cong "
                           f"tren {ma} {khung} - cap nay khong phan xu duoc bat ky "
                           f"edge nao, quet no la dot CPU"]}

    bh = MP.mua_giu(train, cp, ma=ma, khung=khung)
    m_bh = DO.chi_so(bh.loi, bh.index)

    to_hop = MAU.tat_ca_to_hop()
    if gioi_han_to_hop:
        to_hop = to_hop[:gioi_han_to_hop]

    ung_vien, da_quet = [], 0
    for ten, ts in to_hop:
        try:
            th = MAU.sinh(ten, train, ts)
            kq = MP.chay(train, th, cp, ma=ma, khung=khung)
            m = DO.chi_so(kq.loi, kq.index, kq.vi_the)
            da_quet += 1
        except Exception:
            continue
        if kq.so_lenh < CONG.nguong()["so_lenh_toi_thieu"]:
            continue
        # sang tho: phai thang mua-giu CA loi suat LAN sharpe ngay o train
        if (m.get("tong_lai_pct") or -1e9) > (m_bh.get("tong_lai_pct") or 0) and \
           (m.get("sharpe") or -9) > (m_bh.get("sharpe") or 0):
            ung_vien.append({"mau": ten, "tham_so": ts, "chi_so": m,
                             "ho": MAU.MAU[ten]["ho"], "co_che": MAU.MAU[ten]["co_che"]})

    # CHON LOC TRUOC KHI DANG KY. Moi dang ky an mot suat ngan sach thong ke,
    # nen dang ky het = tu lam nghen chinh minh (xem TOI_DA_DANG_KY_MOI_CAP).
    ung_vien.sort(key=lambda u: -(u["chi_so"].get("sharpe") or -9))
    tong_ung_vien = len(ung_vien)

    # CONG KHA THI (chot 22/08). Truoc khi tieu mot suat FDR, hoi: cap nay co
    # DO DUOC thu nay khong? Ung vien co Sharpe kham pha thap hon MDE cua chinh
    # cap do se FAIL o confirmation du gia thuyet dung hay sai - va van an mot
    # suat, lam cao nguong cho moi phep thu sau (LORD giam theo 1/j^1.6).
    #
    # Khong phai lenh cam theo lop tai san: ung vien FX du manh van di tiep.
    # Va la bai kiem DE - Sharpe kham pha da la con so duoc chon loc (tot nhat
    # trong ~65 to hop) nen no lac quan; truot bai de thi khong qua duoc bai kho.
    thieu_luc = []
    du_luc = []
    for u in ung_vien:
        try:
            kt_luc = DLUC.du_luc_de_kiem(u["chi_so"].get("sharpe"), ma, khung)
        except Exception as e:
            kt_luc = {"du_luc": True, "ly_do": f"khong do duoc MDE: {type(e).__name__}"}
        if kt_luc.get("du_luc"):
            du_luc.append(u)
        else:
            thieu_luc.append({"mau": u["mau"], **{k: kt_luc[k] for k in
                                                  ("mde", "sharpe", "ly_do")
                                                  if k in kt_luc}})
    ung_vien = du_luc[:TOI_DA_DANG_KY_MOI_CAP]

    # dang ky + xep hang xac nhan
    dang_ky = 0
    for u in ung_vien:
        ma_gt = f"{ma}.{khung}.{u['mau']}." + "_".join(f"{k}{v}" for k, v in u["tham_so"].items())
        gid, ph = SO.dang_ky_gia_thuyet(
            ma=ma_gt, co_che=u["co_che"], template=u["mau"], tham_so=u["tham_so"],
            tai_san=ma, khung=khung, cua_so=_cua_so(df), ho=u["ho"],
            nguon="kham_pha", tru_sinh=TRU,
            ghi_chu=f"[{che_do}] train sharpe {u['chi_so'].get('sharpe')} "
                    f"vs mua-giu {m_bh.get('sharpe')}")
        # DA CO KET QUA thi thoi. Truoc 16/08 moi vong quet lai dat lai viec xac
        # nhan cho chinh nhung gia thuyet da chay -> 1.103 dong ket qua cho 275
        # gia thuyet. Do khong phai kiem dinh lai, do la NHIN LAI CUNG MOT
        # HOLDOUT nhieu lan; holdout mat tinh "chua tung dung" ngay tu lan hai.
        if SO.mot("SELECT id FROM ket_qua WHERE gt_ma=? AND superseded_by IS NULL", ma_gt):
            continue
        if SO.them_viec(TRU, "xac_nhan", {"gt_ma": ma_gt}, uu_tien=3):
            dang_ky += 1

    if thieu_luc:
        # KHONG duoc im lang. "Bo qua vi thieu luc" la mot ket luan CO NOI DUNG:
        # no noi rang cap nay khong do duoc thu do, chu khong noi rang thu do
        # khong ton tai. Ghi ra so de dem duoc, va de biet dang bo lo bao nhieu.
        SO.ghi_chi_so("kham_pha_thieu_luc", float(len(thieu_luc)),
                      {"tai_san": ma, "khung": khung, "chi_tiet": thieu_luc[:5]})
    return {"ma": ma, "khung": khung, "da_quet": da_quet,
            "ung_vien": tong_ung_vien, "da_chon": len(ung_vien),
            "dang_ky_moi": dang_ky, "che_do": che_do,
            "thieu_luc": len(thieu_luc), "chi_tiet_thieu_luc": thieu_luc[:5],
            "mde": (thieu_luc[0]["mde"] if thieu_luc else
                    (DLUC.mde_cua(ma, khung).get("mde") if du_luc else None)),
            "cua_so": _cua_so(df), "so_bar": len(df),
            "mua_giu_train": m_bh, "chi_phi_do_tin": cp.do_tin}


#: TRAN HANG DOI KHAM PHA. Vuot tran thi NGUNG rut ung vien - va con tro
#: KHONG tien, nen khong ung vien nao bi mat, chung chi doi.
#:
#: Vi sao can: tu 23/08 co HAI lan dau vao (feed + trinh duyet) va mot bo tu
#: tim nguon moi. Ba cai do sinh ung vien nhanh hon nhieu so voi toc do
#: QUANTLAB tieu thu (mot co che quet het kho tai san mat 3-14 giay). Khong co
#: van nay thi hang doi phinh vo han va do dai hang doi - thong tin quan trong
#: nhat ve suc khoe day chuyen - bien thanh mot con so vo nghia.
TRAN_HANG_DOI_KHAM_PHA = 250

#: Han ngach cho nhanh NGOAI (SEEKER/doc ma). Dat THAP hon tran chung de nhanh
#: NOI SINH (NGHI) luon con cho: no de xuat 3-6 co che moi 90 phut, con nhanh
#: ngoai co the day vao hang chuc cai mot luc.
TRAN_NGOAI_DANG_CHO = max(4, int(TRAN_HANG_DOI_KHAM_PHA * 0.6))

#: Chuoi dung de KIEM mot khai bao co che moi (ty le kich hoat + phep cat
#: nhin truoc). Do mot lan moi tien trinh.
_DF_KIEM: list = []


def _df_kiem():
    """Mot chuoi D1 du dai de kiem khai bao. D1 chu khong phai H4: phep cat
    nhin truoc can >= 300 bar va mot lich su dai lam bay nhay ro hon."""
    if _DF_KIEM:
        return _DF_KIEM[0]
    for ma in ("US500CASH", "SP500_DAILY", "EURCAD", "AUDNZD", "XAUUSD"):
        try:
            d = DL.nap(ma, "D1")
        except Exception:
            continue
        if d is not None and len(d) > 1500:
            _DF_KIEM.append(d)
            return d
    _DF_KIEM.append(None)
    return None


def _uu_tien_ung_vien(uv, muc) -> int:
    """Uu tien 1..9 (nho = lam truoc), theo GIA TRI KY VONG chu khong theo thu tu den.

    Hai thu quyet dinh:
      - ung vien mang KHAI BAO co che cu the (`dsl`) dang gia hon ung vien chi
        NHAC TEN mot mau da co - cai truoc la mot luat doc duoc, cai sau la mot
        goi y quet lai thu vien;
      - nguon co SUAT cao (do bang `nhan/vuon_nguon.py`) dang tin hon.
    Khong co buoc nay thi hang doi la FIFO thuan, va mot dot 100 ung vien tu
    mot nguon suat 0 se day moi thu khac ra sau.
    """
    md = uv.metadata or {}
    uu = 5
    if md.get("dsl"):
        uu -= 2
    try:
        from nhan import vuon_nguon as VN
        from urllib.parse import urlparse
        khoa = VN.khoa_nha_xuat_ban(urlparse(str(md.get("nguon_url") or "")).netloc)
        tk = VN.thong_ke_nguon()
        cao = sorted((d["suat"] for d in tk.values()), reverse=True)
        nguong = cao[max(0, len(cao) // 3)] if cao else 0
        for ma, d in tk.items():
            if khoa and khoa in ma and d["suat"] >= nguong:
                uu -= 1
                break
    except Exception:
        pass
    return max(1, min(9, uu if uu != 5 else int(muc.get("priority") or 5)))


def _thuan(x):
    """mappingproxy/tuple long nhau -> dict/list thuan, de ghi JSON duoc."""
    from collections.abc import Mapping, Sequence
    if isinstance(x, Mapping):
        return {str(k): _thuan(v) for k, v in x.items()}
    if isinstance(x, Sequence) and not isinstance(x, (str, bytes)):
        return [_thuan(v) for v in x]
    return x


def _dang_ky_dsl(uv):
    """Ung vien mang khai bao -> (ten_mau da dang ky | None, ly_do).

    BA CUA phai qua, khong duoc bo cua nao:
      1. cu phap (`kiem_khai_bao`);
      2. ty le kich hoat trong khoang dung duoc - qua thap thi khong bao gio du
         lenh de kiem dinh, qua cao thi la mua-giu tra hinh;
      3. PHEP CAT: tin hieu tai bar t phai khong doi khi biet them bar sau t.
    Ca ba do `nhan/ngu_phap.them_co_che` thuc hien tren du lieu THAT.
    """
    # `hop_dong` tra artifact BAT BIEN: metadata la `mappingproxy` va cac
    # nhanh con la mappingproxy/tuple. `isinstance(x, dict)` la FALSE voi
    # mappingproxy, va `json.dumps` cua `luu_kho` cung nem no ra - nen phai
    # doi ve kieu thuan truoc khi dung. Bay nay im lang: no bao "khong co
    # khai bao" cho mot ung vien dang mang day du khai bao.
    # `candidate_queue` la APPEND-ONLY (co trigger chan xoa) - dung, va vi the
    # nhung ung vien do BAN DOC CU sinh ra van nam do vinh vien. Chan chung o
    # day theo PHIEN BAN bo doc, khong xoa lich su.
    #
    # Ban `doc_hieu` v1 co bon loi doc NGHIA (thuc the HTML cat cau, cau ta ca
    # hai chieu, cau dinh nghia chi bao, va ma nguon di nham duong van xuoi).
    # Bon co che sinh tu do da bi thu hoi ngay 23/08; mot trong so do con "dat"
    # phep thu phan chung voi Sharpe 0,822 - tuc mot ban doc sai KHONG lo ra o
    # ket qua, no che ra mot edge.
    BAN_DOC_TOI_THIEU = 2
    if str(uv.extractor or "") == "doc_hieu":
        try:
            ban = int(str(uv.extractor_version or "0"))
        except ValueError:
            ban = 0
        if ban < BAN_DOC_TOI_THIEU:
            return None, f"ban doc hieu v{ban} da nghi huu (can >= v{BAN_DOC_TOI_THIEU})"

    spec = _thuan((uv.metadata or {}).get("dsl"))
    if not isinstance(spec, dict):
        return None, "khong co khai bao"
    ten = NP.chuan_hoa_ten(str(spec.get("ten") or ""))
    if not ten:
        return None, "ten rong"
    if ten in MAU.MAU:
        return ten, "da co trong thu vien"

    # TRUNG VAN TAY = cung mot luat viet bang cau khac. Khong dang ky them:
    # 12 bai ta cung mot luat la MOT co che voi 12 trich dan, khong phai 12
    # suat ngan sach thong ke.
    vt = (uv.metadata or {}).get("van_tay_co_che")
    if vt:
        for c in NP.doc_kho():
            if c.get("van_tay") == vt:
                NP.nap_vao_mau()
                return (c.get("ten") if c.get("ten") in MAU.MAU else None), \
                       f"trung van tay voi '{c.get('ten')}'"

    df = _df_kiem()
    if df is None:
        return None, "khong co chuoi gia de kiem"
    try:
        r = NP.them_co_che(spec, df)
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:120]}"
    if not r.get("nhan"):
        return None, "; ".join(r.get("ly_do") or [])[:200]
    NP.nap_vao_mau()
    return (ten if ten in MAU.MAU else None), "dang ky moi"


def rut_hang_doi_ung_vien(gioi_han: int = 20) -> dict:
    """Doc `candidate_queue` theo cursor, bien moi ung vien thanh mot viec quet.

    `LANE_CANDIDATE` va `CANDIDATE_CURSOR` da duoc khai bao tu 16/08 nhung khong
    ham nao dung den, nen dau tieu thu cua hang doi bo trong: du co ung vien thi
    cung khong ai lay ra. Ham nay la dau do.

    KHONG tin gi tu noi dung ung vien ngoai TEN MAU, va ten mau phai co san
    trong thu vien. Van ban tu web khong dieu khien duoc gi ngoai viec chon mot
    mau da duoc kiem duyet tu truoc.
    """
    NP.nap_vao_mau()
    tu = 0
    try:
        tu = int(json.loads(CANDIDATE_CURSOR.read_text(encoding="utf-8"))["id"])
    except Exception:
        tu = 0

    bao = {"lane": LANE_CANDIDATE, "da_doc": 0, "xep_viec": 0,
           "mau_la": 0, "trung": 0, "toi": tu, "mau": {}}

    # HAN NGACH THEO NGUON (them 01/09, chu du an chi ra khi NGHI duoc noi lai).
    #
    # QUANTLAB gio co HAI nguon dau vao: NGOAI (SEEKER doc ma/tai lieu) va NOI
    # SINH (NGHI de xuat tu ly le kinh te). Do 01/09: thu vien co 102 co che
    # ngoai so voi 20 noi sinh - lech 5 lan. Neu de tu do thi nguon ngoai chiem
    # gan het ngan sach FDR, va nhanh noi sinh chet doi khong phai vi no te ma vi
    # no cham hon.
    #
    # Hai nguon nay KHONG thay the nhau: mot ben mang ve cai nguoi khac da lam,
    # mot ben hoi "ai dang bi ep phai giao dich". Duong noi sinh la duong duy
    # nhat co the de xuat mot co che CHUA AI VIET, nen bop chet no la tu bit mot
    # huong tim kiem.
    #
    # Cach chan: gioi han so viec DANG CHO cua rieng nhanh NGOAI. Khong dung
    # phanh cung theo ty le - viec cua NGHI it va den thanh dot, mot ty le cung
    # se chan no ngay khi hang doi ngoai vua day.
    dang_cho_ngoai = SO.mot(
        "SELECT COUNT(*) n FROM viec WHERE tru=? AND loai='kham_pha_theo_mau' "
        "AND trang_thai='CHO' AND tham_so LIKE ?", TRU, '%"nguon_tai_lieu": "http%')["n"]
    if dang_cho_ngoai >= TRAN_NGOAI_DANG_CHO:
        bao["han_ngach"] = (
            f"{dang_cho_ngoai} viec tu nguon NGOAI dang cho >= han ngach "
            f"{TRAN_NGOAI_DANG_CHO} - nhuong luot cho nhanh NOI SINH (NGHI)")
        SO.ghi_chi_so("quantlab_han_ngach_ngoai", dang_cho_ngoai, bao)
        return bao

    # AP NGUOC. Kiem TRUOC khi doc hang doi, va thoat ma KHONG ghi con tro.
    dang_cho = SO.mot(
        "SELECT COUNT(*) n FROM viec WHERE tru=? AND loai='kham_pha_theo_mau' "
        "AND trang_thai='CHO'", TRU)["n"]
    if dang_cho >= TRAN_HANG_DOI_KHAM_PHA:
        bao["ap_nguoc"] = (f"{dang_cho} viec kham pha dang cho >= tran "
                           f"{TRAN_HANG_DOI_KHAM_PHA} - ngung rut ung vien")
        SO.ghi_chi_so("quantlab_ap_nguoc", dang_cho, bao)
        return bao
    bao["dang_cho"] = dang_cho
    try:
        hang = SO.doc_candidate_queue(after_id=tu, limit=max(1, min(gioi_han, 1000)))
    except Exception as e:
        bao["loi"] = f"{type(e).__name__}: {str(e)[:100]}"
        return bao

    for muc in hang:
        bao["da_doc"] += 1
        bao["toi"] = muc["id"]
        uv = muc["candidate"]
        ten_mau = str((uv.metadata or {}).get("mau", "")).strip()
        if ten_mau not in MAU.MAU and (uv.metadata or {}).get("dsl"):
            # Ung vien mang theo mot KHAI BAO co che (doc tu van xuoi). Dang ky
            # o day - khong o SEEKER: quyen cho mot co che moi vao thu vien phai
            # nam cung cho voi ngan sach thong ke se tra cho no.
            ten_mau, ly_do = _dang_ky_dsl(uv)
            bao.setdefault("dsl", []).append(
                {"ten": str((uv.metadata or {}).get("mau")), "ket_qua": ly_do})
            if not ten_mau:
                bao["mau_la"] += 1
                continue
        if not ten_mau or ten_mau not in MAU.MAU:
            # Ung vien tro toi mot mau khong co that -> bo, khong tu tao mau.
            bao["mau_la"] += 1
            continue
        nguon = str((uv.metadata or {}).get("nguon_url", "")) or uv.fingerprint[:16]
        # MANG THAM SO CUA TAI LIEU THEO (them 01/09).
        #
        # Truoc day viec chi chua `{"mau": ..., "nguon_tai_lieu": ...}`. Hau qua
        # do duoc: 111 tai lieu ve RSI dao chieu deu xep cung MOT viec tren
        # `rsi_dao_chieu` va chay cung MOT luoi tham so chuan - nguong, bo loc,
        # luat thoat cua tung bot bi vut sach. 460 viec chi phu 43 mau.
        #
        # Nay neo them tham so ma chinh tai lieu do NOI RA. Van la GOI Y cho
        # tang kham pha, khong phai lenh: luoi van quet, chi la co mot diem neo
        # tu ban goc. Va vi tham so vao van tay cua viec nen hai tai lieu noi hai
        # nguong khac nhau khong con gop lam mot.
        tham = {"mau": ten_mau, "nguon_tai_lieu": nguon,
                "ung_vien": uv.fingerprint}
        neo = (uv.metadata or {}).get("tham_so_goc") or {}
        if not neo and (uv.metadata or {}).get("dsl"):
            neo = {k: v for k, v in ((uv.metadata or {}).get("dsl") or {}).items()
                   if k in ("giu", "chieu")}
        if neo:
            # `uv.metadata` co the la `mappingproxy` (khung nhin chi-doc), va no
            # KHONG tuan tu hoa duoc bang json -> `them_viec` nem TypeError va ca
            # luot rut ung vien chet. Ep ve dict thuong, va chi giu gia tri co
            # ban de mot cau truc long sau khong lot qua duoc.
            tham["tham_so_goc"] = {
                str(k): (list(v) if isinstance(v, (list, tuple))
                         else v if isinstance(v, (int, float, str, bool, type(None)))
                         else str(v))
                for k, v in dict(neo).items()}
        if SO.them_viec(TRU, "kham_pha_theo_mau", tham,
                        uu_tien=_uu_tien_ung_vien(uv, muc)):
            bao["xep_viec"] += 1
            bao["mau"][ten_mau] = bao["mau"].get(ten_mau, 0) + 1
        else:
            bao["trung"] += 1

    CANDIDATE_CURSOR.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATE_CURSOR.write_text(json.dumps({"id": int(bao["toi"])}), encoding="utf-8")
    SO.ghi_chi_so("quantlab_ung_vien_rut", bao["xep_viec"], bao)
    return bao


#: Khung chay phep thu phan chung. D1 chu khong phai H4: o H4 kho chi co ~20
#: bang du bar va het la FX broker 13 nam, nen nhom doi chung `chi_so_my` khong
#: bao gio du 3 tai san -> moi phep thu tra CHUA_DU_MAU (tuc khong phep thu nao
#: tung chay that). O D1 co ca chuoi chi so 25-56 nam.
KHUNG_PHAM_VI = "D1"
_DEM_KHO_PHAM_VI: dict[str, list] = {}


def _kho_pham_vi(khung: str = KHUNG_PHAM_VI) -> list[str]:
    """Kho du bar o mot khung. Do mot lan moi khung moi tien trinh."""
    if khung not in _DEM_KHO_PHAM_VI:
        from nhan import pham_vi as PV
        _DEM_KHO_PHAM_VI[khung] = PV.kho_du_bar(khung)
    return _DEM_KHO_PHAM_VI[khung]


#: Ket qua phep thu pham vi trong MOT luot chay. Do lai cho moi lan goi la
#: lang phi: no chi phu thuoc mau va kho du lieu, khong phu thuoc ung vien.
_DEM_PHAM_VI: dict[str, dict] = {}


def _pham_vi_cua(ten_mau: str) -> dict:
    """Phep thu phan chung cho mot mau, o khung MA HO CO CHE DO YEU CAU."""
    if ten_mau not in _DEM_PHAM_VI:
        try:
            from nhan import mau as _MAU, pham_vi as PV
            ho = (_MAU.MAU.get(ten_mau) or {}).get("ho") or "khac"
            khung = PV.khung_cua_ho(ho)
            _DEM_PHAM_VI[ten_mau] = PV.kiem_pham_vi(
                ten_mau, khung, kho=_kho_pham_vi(khung))
        except Exception as e:
            _DEM_PHAM_VI[ten_mau] = {"loi": f"{type(e).__name__}: {str(e)[:80]}"}
    return _DEM_PHAM_VI[ten_mau]


def kham_pha_theo_mau(ten_mau: str, nguon: str = "") -> dict:
    """Quet MOT mau tren toan bo tai san uu tien. Day la dau ra cua SEEKER/NGHI.

    Truoc 16/08 loai viec nay duoc SEEKER xep vao hang doi nhung QUANTLAB
    KHONG CO nhanh xu ly - no roi vao `else` va bi danh dau "loai viec chua ho
    tro". Tuc ca duong ong tu tai lieu sang kiem dinh dut o dung day, im lang.
    """
    NP.nap_vao_mau()
    if ten_mau not in MAU.MAU:
        return {"mau": ten_mau, "loi": "khong co trong thu vien mau"}
    m = MAU.MAU[ten_mau]
    ra = {"mau": ten_mau, "ho": m["ho"], "nguon": nguon, "cap": [], "dang_ky_moi": 0}

    # PHEP THU PHAN CHUNG THEO LOP TAI SAN, chay TRUOC khi dang ky bat ky gia
    # thuyet nao. Mot co che chay deu tot o ca lop da khai la NEN HONG thi khong
    # phai co che - va moi gia thuyet dang ky tu no se an mot suat FDR that.
    # Chan o day re hon nhieu so voi chan o tang xac nhan.
    ra["pham_vi"] = _pham_vi_cua(ten_mau)
    if ra["pham_vi"].get("ket_luan") in ("KHONG_PHAN_BIET", "KHONG_CO_CO_CHE"):
        ra["bo_qua"] = ra["pham_vi"]["ly_do"]
        return ra
    ds = _tai_san_quet_mau()
    for ma in ds:
        for khung in _khung_cua(ma):
            try:
                df, train, _h, cp, _c = _nap(ma, khung)
            except Exception:
                continue
            if len(df) < SO_BAR_TOI_THIEU:
                continue
            bh = MP.mua_giu(train, cp, ma=ma, khung=khung)
            m_bh = DO.chi_so(bh.loi, bh.index)
            tot = None
            # TRUC NEN (them 01/09, chu du an chot: "thu ca cac loai nen nua").
            # Quet Heikin Ashi ben canh nen thuong.
            #
            # RANH GIOI KHONG DOI: nen bien doi CHI de tinh tin hieu; `MP.chay`
            # van nhan `train` la NEN THAT nen khop lenh, chi phi va loi suat
            # deu tinh tren gia mua ban duoc. Gia HA la so ke toan (trung binh
            # OHLC) - khong mot lenh nao khop duoc o do. Vao lenh tai gia HA la
            # che ra lai tu cho khong co, cung ho voi bay `Model=1` (+1.161,5%
            # so voi -100,7% o tick that). Xem `nhan/nen.py`.
            for kieu_nen in NEN.LOAI:
                for ts in (m.get("luoi") or [{}]):
                    try:
                        th = NEN.sinh_tren_nen(
                            lambda d, _t=ts: MAU.sinh(ten_mau, d, _t),
                            train, kieu_nen)
                        kq = MP.chay(train, th, cp, ma=ma, khung=khung)
                    except Exception:
                        continue
                    if kq.so_lenh < CONG.nguong()["so_lenh_toi_thieu"]:
                        continue
                    cs = DO.chi_so(kq.loi, kq.index, kq.vi_the)
                    if (cs.get("sharpe") or -9) > (m_bh.get("sharpe") or 0) and                        (cs.get("tong_lai_pct") or -1e9) > (m_bh.get("tong_lai_pct") or 0) and                        (tot is None or (cs.get("sharpe") or -9) > (tot[2].get("sharpe") or -9)):
                        tot = (ts, kieu_nen, cs)
            if tot is None:
                continue
            ts, kieu_nen, cs = tot
            # Nen di vao TEN gia thuyet chu khong chi vao ghi chu: hai cau hinh
            # khac nen la hai gia thuyet khac nhau va phai ton hai suat FDR rieng.
            if kieu_nen != NEN.THUONG:
                ts = dict(ts, nen=kieu_nen)
            # Cung cong kha thi nhu `kham_pha`: khong tieu suat FDR o cap khong
            # do duoc. Truoc day duong nay dang ky thang, nen mot mau lay tu tai
            # lieu tu dong an 6 suat o 6 cap dau danh sach du cap nao co do duoc
            # hay khong.
            try:
                kt_luc = DLUC.du_luc_de_kiem(cs.get("sharpe"), ma, khung)
            except Exception:
                kt_luc = {"du_luc": True}
            if not kt_luc.get("du_luc"):
                ra.setdefault("thieu_luc", []).append(
                    {"tai_san": ma, "khung": khung, "ly_do": kt_luc.get("ly_do")})
                continue
            ma_gt = f"{ma}.{khung}.{ten_mau}." + ("_".join(f"{k}{v}" for k, v in ts.items())
                                                 or "mac_dinh")
            SO.dang_ky_gia_thuyet(
                ma=ma_gt, co_che=m["co_che"], template=ten_mau, tham_so=ts,
                tai_san=ma, khung=khung, cua_so=_cua_so(df), ho=m["ho"],
                nguon=nguon or "kham_pha_theo_mau", tru_sinh=TRU,
                # SO PHEP THU: ca luoi cua mau nay da duoc quet truoc khi bo
                # tham so `ts` duoc chon. plan_hash KHONG phu con so do (xem
                # `so.dang_ky_gia_thuyet`), nen day la cho duy nhat no duoc luu.
                so_phep_thu=len(m.get("luoi") or [{}]),
                the_he_cong=CONG.THE_HE_CONG,
                ghi_chu=f"train sharpe {cs.get('sharpe')} vs mua-giu {m_bh.get('sharpe')}")
            if SO.mot("SELECT id FROM ket_qua WHERE gt_ma=? AND superseded_by IS NULL", ma_gt):
                continue
            if SO.them_viec(TRU, "xac_nhan", {"gt_ma": ma_gt}, uu_tien=2):
                ra["dang_ky_moi"] += 1
            ra["cap"].append({"tai_san": ma, "khung": khung,
                              "sharpe_train": cs.get("sharpe")})
    return ra


# --------------------------------------------------- DUONG GOP: MOT LOP, MOT SUAT
#: Toi da bao nhieu gia thuyet GOP duoc dang ky moi luot. Moi cai la mot khang
#: dinh "co che X song o lop thi truong Y" va an mot suat FDR. Do 22/08: chi
#: 3/15 mau sinh duoc ung vien gop tren train, nen tran nay hiem khi cham toi -
#: no la phanh cho truong hop thu vien mau phinh to.
TOI_DA_GOP_MOI_LUOT = 5


def kham_pha_gop(ten_mau: str, nguon: str = "") -> dict:
    """TANG KHAM PHA cua duong gop: quet tham so tren RO o TRAIN, roi dang ky.

    Duong nay ton tai vi duong don le da do duoc gioi han cua chinh no: nguong
    phat hien tot nhat cua MOT tai san la 0,535 trong khi co che duy nhat qua
    duoc phep thu phan chung co Sharpe 0,24-0,31. Mot vong kham pha day du
    (492 luot, 22/08) dang ky DUNG 0 gia thuyet va chan 692 ung vien - tat ca
    deu vi thieu luc, khong phai vi thi truong rong.

    Gop khong lam co che manh len; no lam PHEP KIEM manh len. Va ve so hoc thong
    ke day la MOT gia thuyet, khong phai 12.
    """
    from nhan import gop_lop as GL
    NP.nap_vao_mau()
    if ten_mau not in MAU.MAU:
        return {"mau": ten_mau, "loi": "khong co trong thu vien mau"}
    ho = (MAU.MAU[ten_mau].get("ho") or "khac")
    from nhan import pham_vi as PV
    khung = PV.khung_cua_ho(ho)
    # Dung lai bo nho dem kho cua tru: `kho_du_bar` nap thu 119 bang, ~11 giay.
    # Goi lai o moi buoc cua duong gop thi rieng viec liet ke kho da an het thoi
    # gian danh cho backtest.
    q = GL.quet_tham_so_gop(ten_mau, ho=ho, khung=khung, kho=_kho_pham_vi(khung))
    if q.get("loi") or q.get("ket_luan") != "CO_UNG_VIEN":
        return {"mau": ten_mau, "ho": ho, "bo_qua": q.get("ly_do") or q.get("loi"),
                "ket_luan": q.get("ket_luan")}

    lop = "+".join(q["lop"])
    ma_gt = f"GOP.{ten_mau}.{q['khung']}.{lop}." + (
        "_".join(f"{k}{v}" for k, v in q["tham_so"].items()) or "mac_dinh")
    try:
        SO.dang_ky_gia_thuyet(
            ma=ma_gt, co_che=MAU.MAU[ten_mau].get("co_che", ""), template=ten_mau,
            tham_so=q["tham_so"], tai_san=f"RO:{lop}", khung=q["khung"],
            cua_so=q.get("cua_so_train") or "", ho=ho,
            so_phep_thu=q.get("da_quet"), the_he_cong=CONG.THE_HE_CONG,
            nguon=nguon or "kham_pha_gop", tru_sinh=TRU,
            ghi_chu=f"RO {q['so_chan']} chan: {','.join(q['chan'])} | "
                    f"train sharpe {q.get('sharpe_train')}")
    except ValueError as e:
        # plan_hash lech = cua so train doi = la mot gia thuyet KHAC. Khong duoc
        # im lang ghi de len ban cu.
        return {"mau": ten_mau, "ho": ho, "gt": ma_gt,
                "bo_qua": f"plan_hash lech: {str(e)[:90]}"}

    ra = {"mau": ten_mau, "ho": ho, "gt": ma_gt, "lop": lop,
          "tham_so": q["tham_so"], "so_chan": q["so_chan"],
          "sharpe_train": q.get("sharpe_train"), "xep_viec": 0}
    if SO.mot("SELECT id FROM ket_qua WHERE gt_ma=? AND superseded_by IS NULL", ma_gt):
        ra["da_co_ket_qua"] = True
        return ra
    if SO.them_viec(TRU, "xac_nhan_gop", {"gt_ma": ma_gt}, uu_tien=2):
        ra["xep_viec"] = 1
    return ra


def xac_nhan_gop(gt_ma: str) -> dict:
    """Chay gia thuyet GOP da dang ky tren holdout cua ro + cong day du."""
    from nhan import gop_lop as GL
    gt = SO.mot("SELECT * FROM gia_thuyet WHERE ma=?", gt_ma)
    if not gt:
        return {"loi": f"khong tim thay gia thuyet {gt_ma}"}

    # HAM Y NGUYEN. Chay lai cung gia thuyet nay = NHIN LAI CUNG MOT HOLDOUT,
    # va holdout mat tinh "chua tung dung" ngay tu lan hai. Truoc 16/08 duong
    # don le da sap dung day: 1.103 dong ket qua cho 275 gia thuyet.
    cu = SO.mot("SELECT * FROM ket_qua WHERE gt_ma=? AND superseded_by IS NULL "
                "ORDER BY id DESC LIMIT 1", gt_ma)
    if cu:
        return {"gt": gt_ma, "verdict": cu["verdict"], "da_co_tu_truoc": True,
                "ly_do": ["da co ket qua - khong cham lai holdout"]}

    ts = json.loads(gt["tham_so"] or "{}")
    NP.nap_vao_mau()
    kt = GL.xet_gop(gt["template"], ho=gt["ho"], khung=gt["khung"], tham_so=ts,
                    kho=_kho_pham_vi(gt["khung"]), gt_ma=gt_ma, da_dang_ky=True)
    if kt.get("loi") or "so_sanh" not in kt:
        SO.doi_trang_thai_gt(gt_ma, kt.get("verdict") or "KHONG_DU_MAU",
                             str(kt.get("ly_do") or kt.get("loi"))[:200])
        return {"gt": gt_ma, "verdict": kt.get("verdict") or "KHONG_DU_MAU",
                "ly_do": kt.get("ly_do") or kt.get("loi")}

    # Ro co the doi thanh phan neu kho du lieu doi. Khong chan, nhung PHAI ghi:
    # mot ro khac la mot phep kiem khac du plan_hash khong doi.
    chan_gio = (kt.get("ro_hop") or {}).get("chan") or []
    if chan_gio and f"{len(chan_gio)} chan" not in (gt["ghi_chu"] or ""):
        kt.setdefault("canh_bao", []).append(
            f"thanh phan ro khi xac nhan: {','.join(chan_gio)}")

    SO.ghi_ket_qua(gt_ma, kt["so_sanh"], kt["dieu_kien"], kt["verdict"],
                   kt.get("p_placebo"),
                   kt["so_sanh"]["alpha_vs_mua_giu"].get("alpha_nam_pct"),
                   kt["so_sanh"]["alpha_vs_mua_giu"].get("t_alpha"))
    SO.doi_trang_thai_gt(gt_ma, kt["verdict"], "; ".join(map(str, kt["ly_do"][:3])))
    if kt["verdict"] == "PASS":
        SO.ghi_su_kien(TRU, "PASS_GOP", {"gt": gt_ma, "chi_so": kt["so_sanh"]["he"]})
        SO.them_viec(TRU, "mt5_tick", {"gt_ma": gt_ma}, uu_tien=1)
    if kt["verdict"] == "CO_CO_CHE":
        SO.ghi_su_kien(TRU, "CO_CO_CHE_GOP", {"gt": gt_ma})
        SO.them_viec(TRU, "bac_cau_san", {"gt_ma": gt_ma}, uu_tien=2)
    SO.ghi_chi_so("gop_sharpe_ro", float(kt.get("sharpe_ro_hop") or 0.0),
                  {"gt": gt_ma, "cach_biet": kt.get("cach_biet"),
                   "verdict": kt["verdict"]})
    return {"gt": gt_ma, "verdict": kt["verdict"], "che_do": kt.get("che_do"),
            "sharpe_ro": kt.get("sharpe_ro_hop"),
            "sharpe_doi_chung": kt.get("sharpe_ro_doi_chung"),
            "cach_biet": kt.get("cach_biet"),
            "ly_do": [str(x)[:160] for x in kt["ly_do"][:4]]}


# ------------------------------------------------------------ TANG XAC NHAN
def xac_nhan(gt_ma: str) -> dict:
    """Chay gia thuyet DA DANG KY tren HOLDOUT + cong day du."""
    gt = SO.mot("SELECT * FROM gia_thuyet WHERE ma=?", gt_ma)
    if not gt:
        return {"loi": f"khong tim thay gia thuyet {gt_ma}"}
    ma, khung = gt["tai_san"], gt["khung"]
    ts = json.loads(gt["tham_so"] or "{}")

    NP.nap_vao_mau()
    _df, _tr, holdout, _cptr, cp = _nap(ma, khung)
    if len(holdout) < 300:
        SO.doi_trang_thai_gt(gt_ma, "KHONG_DU_HOLDOUT")
        return {"gt": gt_ma, "verdict": "KHONG_DU_HOLDOUT", "so_bar": len(holdout)}

    th = MAU.sinh(gt["template"], holdout, ts)
    kq = MP.chay(holdout, th, cp, ma=ma, khung=khung)
    bh = MP.mua_giu(holdout, cp, ma=ma, khung=khung)

    # Ho FDR gan the he mo hinh chi phi: ket qua do bang hai thuoc do khac nhau
    # khong duoc nam chung mot chuoi quyet dinh (THIET_KE muc 7) - va gan ca
    # CHE DO, vi chuoi nghien cuu tra loi mot cau hoi khac.
    che_do = _che_do(cp)
    ho_fdr = _ho_fdr(gt['ho'] or 'chung', che_do)
    kt = CONG.xet(holdout, kq, bh, cp, gt_ma=gt_ma, ho=ho_fdr,
                  da_dang_ky=True, tren_holdout=True, che_do=che_do)
    SO.ghi_ket_qua(gt_ma, kt["so_sanh"], kt["dieu_kien"], kt["verdict"],
                   (kt.get("placebo") or {}).get("p_xau_nhat"),
                   kt["so_sanh"]["alpha_vs_mua_giu"].get("alpha_nam_pct"),
                   kt["so_sanh"]["alpha_vs_mua_giu"].get("t_alpha"))
    SO.doi_trang_thai_gt(gt_ma, kt["verdict"], "; ".join(kt["ly_do"][:3]))

    if kt["verdict"] == "PASS":
        SO.ghi_su_kien(TRU, "PASS", {"gt": gt_ma, "chi_so": kt["so_sanh"]["he"]})
        SO.them_viec("QUANTLAB", "mt5_tick", {"gt_ma": gt_ma}, uu_tien=1)
    if kt["verdict"] == "CO_CO_CHE":
        # CHANG HAI. Co che tim thay tren chuoi khong mua duoc chua phai ket
        # qua - no la mot GIA THUYET DA DUOC DANG KY cho chuoi mua duoc. Neu
        # khong noi hai chang nay thi tang nghien cuu chi sinh ra bao cao dep.
        SO.ghi_su_kien(TRU, "CO_CO_CHE", {"gt": gt_ma, "chi_so": kt["so_sanh"]["he"]})
        SO.them_viec(TRU, "bac_cau_san", {"gt_ma": gt_ma}, uu_tien=2)
    if kt["verdict"] == "NGHI_NHIN_TRUOC":
        SO.bao_van_de("nghi_nhin_truoc_" + gt_ma, "NANG",
                      f"{gt_ma} cho t_alpha > 5 - nguong hieu chuan tu canary noi day "
                      "phai gia dinh la nhin truoc", kt.get("canh_bao_nang"))
    return {"gt": gt_ma, "verdict": kt["verdict"], "ly_do": kt["ly_do"][:4],
            "che_do": che_do, "ho_fdr": ho_fdr,
            "chi_so": kt["so_sanh"]["he"], "mua_giu": kt["so_sanh"]["mua_giu_net"],
            "alpha": kt["so_sanh"]["alpha_vs_mua_giu"],
            "placebo": (kt.get("placebo") or {}).get("p_xau_nhat")}


# --------------------------------------------------- CHANG HAI: BAC CAU SAN
#: Toi da bao nhieu tai san SAN duoc thu cho mot co che da dat CO_CO_CHE.
TRAN_BAC_CAU = 4


def bac_cau_san(gt_ma: str, tran: int = TRAN_BAC_CAU) -> dict:
    """Co che dat `CO_CO_CHE` tren chuoi DAI -> dang ky lai nguyen van tren
    chuoi SAN cung LOP tai san, de tra loi cau con lai: co giao dich duoc khong.

    Ba dieu bat bien o day:

    1. **Khong doi gi ca.** Cung template, cung tham so. Doi tham so cho hop
       voi tai san moi la fit lai tren chuoi thu hai, va luc do chuoi thu hai
       khong con la bang chung doc lap nua.
    2. **Cung LOP tai san.** Co che tim thay tren chi so co phieu duoc thu tren
       chi so co phieu mua duoc, khong phai tren ty gia cheo. Day chinh la
       khang dinh pham vi ma `nhan/pham_vi.py` bat phai khai truoc.
    3. **Moi tai san bac cau la MOT gia thuyet dang ky rieng**, an mot suat FDR
       cua ho `giao_dich`. Vi vay co tran `TRAN_BAC_CAU`: bac cau sang 20 cap
       roi giu cai nao thang la cau tai san, dung y nghia ma no vua dat duoc.
    """
    gt = SO.mot("SELECT * FROM gia_thuyet WHERE ma=?", gt_ma)
    if not gt:
        return {"loi": f"khong tim thay gia thuyet {gt_ma}"}
    lop = CP._loai_tai_san(gt["tai_san"])
    ts = json.loads(gt["tham_so"] or "{}")
    ra = {"gt_nguon": gt_ma, "lop": lop, "khung": gt["khung"],
          "dang_ky_moi": 0, "da_thu": [], "bo_qua": []}

    dich = []
    for m in _tai_san_kha_dung():
        if m == gt["tai_san"] or DL.nguon_tai_san(m) != "san":
            continue
        if CP._loai_tai_san(m) != lop:
            continue
        if gt["khung"] not in _khung_cua(m):
            ra["bo_qua"].append(f"{m}: khong co khung {gt['khung']}")
            continue
        dich.append(m)
    if not dich:
        # KHONG duoc im lang. "Khong co chuoi mua duoc cung lop" la mot ket
        # luan that su - no noi rang co che nay khong kiem chung duoc bang kho
        # hien co, va do la viec phai di lay du lieu chu khong phai viec bo qua.
        SO.bao_van_de(f"bac_cau_thieu_san_{lop}", "VUA",
                      f"Co che dat CO_CO_CHE tren {gt['tai_san']} ({lop}, khung "
                      f"{gt['khung']}) nhung kho khong co chuoi MUA DUOC cung lop "
                      "o khung do - khong chung nhan giao dich duoc.",
                      {"gt": gt_ma, "lop": lop})
        ra["thieu_tai_san_san"] = True
        return ra

    for m in dich[:tran]:
        try:
            df, _tr, _h, _cptr, _cp = _nap(m, gt["khung"])
        except Exception as e:
            ra["bo_qua"].append(f"{m}: {type(e).__name__}")
            continue
        if len(df) < SO_BAR_TOI_THIEU:
            ra["bo_qua"].append(f"{m}: chi {len(df)} bar")
            continue
        ma_gt = f"{m}.{gt['khung']}.{gt['template']}." + (
            "_".join(f"{k}{v}" for k, v in ts.items()) or "mac_dinh") + ".bac_cau"
        try:
            SO.dang_ky_gia_thuyet(
                ma=ma_gt, co_che=gt["co_che"], template=gt["template"], tham_so=ts,
                tai_san=m, khung=gt["khung"], cua_so=_cua_so(df), ho=gt["ho"],
                nguon=f"bac_cau_tu:{gt_ma}", tru_sinh=TRU,
                ghi_chu=f"chang 2: co che dat CO_CO_CHE tren {gt['tai_san']} "
                        f"({lop}) - thu nguyen van tren chuoi mua duoc")
        except ValueError as e:
            ra["bo_qua"].append(f"{m}: {str(e)[:70]}")
            continue
        ra["da_thu"].append(ma_gt)
        if SO.mot("SELECT id FROM ket_qua WHERE gt_ma=? AND superseded_by IS NULL", ma_gt):
            continue
        if SO.them_viec(TRU, "xac_nhan", {"gt_ma": ma_gt}, uu_tien=2):
            ra["dang_ky_moi"] += 1
    SO.ghi_su_kien(TRU, "bac_cau_san", ra)
    return ra


def xep_hang_mt5_tick(gt_ma: str) -> dict:
    """Gia thuyet da qua cong Python -> vao hang doi kiem dinh tick THAT tren MT5.

    Day la buoc bien "co edge tren giay" thanh "co edge khi khop lenh", va no
    la buoc DUY NHAT co the bac bo ket luan Python (CLAUDE.md muc 40: Model=1
    tung che ra +1.161% cho mot cau hinh that ra -100,7%). Chua tu dong hoa
    duoc nen o day chi ghi ra danh sach cho nguoi, KHONG danh dau la da lam.
    """
    ds = REPORTS / "CHO_KIEM_TICK_MT5.md"
    gt = SO.mot("SELECT * FROM gia_thuyet WHERE ma=?", gt_ma) or {}
    kq = SO.mot("SELECT * FROM ket_qua WHERE gt_ma=? AND superseded_by IS NULL "
                "ORDER BY id DESC LIMIT 1", gt_ma) or {}
    dong = []
    if ds.exists():
        dong = ds.read_text(encoding="utf-8").splitlines()
    else:
        dong = ["# GIA THUYET CHO KIEM DINH TICK THAT TREN MT5", "",
                "> Qua cong Python KHONG phai ket luan cuoi. `Model=1` tung che ra",
                "> +1.161,5% cho mot cau hinh that ra -100,7% (CLAUDE.md muc 40).",
                "> Bat buoc chay `Model=0` hoac `Model=4` khi TP/SL < 2x bien do nen M1.", ""]
    if not any(gt_ma in d for d in dong):
        dong.append(f"- [ ] `{gt_ma}` | ho {gt.get('ho')} | co che: "
                    f"{str(gt.get('co_che'))[:120]} | ghi so luc {SO.bay_gio()}")
        ds.write_text("\n".join(dong), encoding="utf-8")
    SO.bao_van_de("cho_kiem_tick_mt5", "VUA",
                  "Co gia thuyet da qua cong Python dang cho kiem dinh tick that "
                  "tren MT5 - buoc nay chua tu dong hoa duoc",
                  {"danh_sach": "reports/CHO_KIEM_TICK_MT5.md"})
    return {"gt": gt_ma, "da_xep_hang": True, "verdict_python": kq.get("verdict"),
            "danh_sach": "reports/CHO_KIEM_TICK_MT5.md"}


# ------------------------------------------------- SO CHENH LECH CHI PHI
def so_chenh_lech_chi_phi(do_lai: bool = True) -> dict:
    """ALPHA PHEP TRU (THIET_KE muc 1) - loai alpha co gia tri nhat cua ca thiet ke.

    Khong hoi "co tin hieu khong" ma hoi: *neu toi da quyet dinh giu phoi nhiem
    nay, kenh nao re nhat bay gio?*

    Khong can backtest. Khong can placebo. KHONG TON SLOT FDR. Do chac chan cao.
    Ly do ton tai: day chuyen chi biet danh gia thu co hinh dang
    "tin hieu -> backtest -> p-value" se MU truoc thu co hinh dang
    "cung phoi nhiem, kenh nay re hon kenh kia mot khoan co dinh" (signal myopia).
    """
    if do_lai:
        try:
            CP.do_moi_san()
        except Exception as e:
            return {"loi": f"khong do duoc: {type(e).__name__}: {str(e)[:80]}"}
    bang = CP.bang_chenh_lech()
    if not bang:
        return {"loi": "can it nhat 2 san giao dich duoc"}

    dang_ke = [b for b in bang if b["chenh_diem_pct_nam"] >= 1.0 and b["tin_cay"] == "CAO"]
    dong = [
        "# SO CHENH LECH CHI PHI TRIEN KHAI",
        f"*Do luc {SO.bay_gio()} tren cac terminal MT5 dang cai.*", "",
        "> **Day khong phai gia thuyet, day la phep tru.** Khong ton slot ngan sach",
        "> thong ke nao. Khong can backtest, khong can placebo.", "",
        "> **Cach doc:** so la phi giu vi the MUA, %/nam. Duong = ta TRA. Am = ta DUOC",
        "> nhan (carry duong). Cot da neo vao GIA HIEN TAI - voi san thu swap bang so",
        "> TUYET DOI, ty le nay GIAM khi gia tang, nen **dung ap cho ca lich su**",
        "> (CLAUDE.md muc 13-14).", "",
        f"## Chenh lech dang ke ({len(dang_ke)} phoi nhiem >= 1 diem %/nam, do tin CAO)", "",
        "| Phoi nhiem | Kenh re | %/nam | Kenh dat | %/nam | CHENH | Dieu kien de sai |",
        "|---|---|---|---|---|---|---|",
    ]
    for b in dang_ke[:40]:
        dong.append(
            f"| `{b['phoi_nhiem']}` | {b['kenh_re']} | {b['phi_re_pct_nam']:+.2f} | "
            f"{b['kenh_dat']} | {b['phi_dat_pct_nam']:+.2f} | "
            f"**{b['chenh_diem_pct_nam']:+.2f}** | {b['dieu_kien_de_sai'][:60]} |")

    dong += ["", "## Canh bao doc so", "",
             "- `MetaQuotes-Demo` **khong** nam trong bang: do la may chu demo cua chinh",
             "  MetaQuotes, khong mo tai khoan that duoc. De no vao la tu lua - no luon re",
             "  nhat vi khong ai phai kiem tien tren do.",
             "- Chi lay dong `tin_cay=CAO` (swap_mode = POINTS hoac LAI SUAT). Cac mode",
             "  tinh bang TIEN phai quy doi qua contract size + dong tien tai khoan nen",
             "  con sai so; mode 9 (khong co trong tai lieu MT5) lai cang khong chac.",
             "- Hai symbol cung ten chuan hoa **chua chac cung phoi nhiem**: phai doi chieu",
             "  contract size va gio giao dich truoc khi chuyen tien that.",
             "", "## Buoc tiep de bien thanh tien", "",
             "1. Xac minh bang **sao ke tai khoan that** (mo mot lenh nho, giu qua dem,",
             "   doc dung so tien bi tru) - so tu `symbol_info` la bang gia niem yet,",
             "   khong phai bang chung.", "2. Kiem rui ro doi tac + dieu kien rut tien cua",
             "   kenh re truoc khi chuyen.", "3. Dat lai lich do dinh ky: bieu phi doi thi",
             "   ket luan doi."]
    (REPORTS / "SO_CHENH_LECH_CHI_PHI.md").write_text("\n".join(dong), encoding="utf-8")
    (REPORTS / "so_chenh_lech_chi_phi.json").write_text(
        json.dumps(bang, ensure_ascii=False, indent=1), encoding="utf-8")

    SO.ghi_su_kien(TRU, "so_chenh_lech_chi_phi",
                   {"so_phoi_nhiem": len(bang), "dang_ke": len(dang_ke),
                    "lon_nhat": dang_ke[0] if dang_ke else None})
    SO.ghi_chi_so("chenh_lech_lon_nhat_diem",
                  dang_ke[0]["chenh_diem_pct_nam"] if dang_ke else 0.0)
    return {"so_phoi_nhiem_so_sanh": len(bang), "dang_ke": len(dang_ke),
            "top": dang_ke[:5], "bao_cao": "reports/SO_CHENH_LECH_CHI_PHI.md"}


# --------------------------------------------------------- HIEU CHUAN NULL
def hieu_chuan_null(so_ca: int = 12, ma: str | None = None, khung: str = "H4") -> dict:
    """NULL FACTORY - do ty le LOT cua thu KHONG CO EDGE (THIET_KE muc 12).

    Day moi la cach do hieu chuan dung. Do bang phan phoi p cua CAC UNG VIEN
    DA CHON LOC la sai: chung duoc chon vi thang mua-giu tren train, nen p cua
    chung LE RA phai lech thap - lech thap khong chung minh duoc gi.

    Cach sinh null (THIET_KE muc 3): bootstrap khoi tren chinh chuoi vi the cua
    mot chien luoc that, giu nguyen do dai doan giu -> null CUNG CUM THEO CHE DO
    nhu that. Bốc i.i.d. la sai: null khong cum se cap giay chung nhan cho dung
    bay bien-dong-cum-lai.

    Ket qua ghi vao ho FDR RIENG ('null_hieu_chuan') de khong lam ban chuoi
    quyet dinh cua kham pha that.
    """
    import numpy as np
    ds = _tai_san_kha_dung()
    ma = ma or next((m for m in ds if m in DL.kho()), None)
    if not ma:
        return {"loi": "khong co tai san"}
    df = DL.nap(ma, khung)
    _, holdout = DL.hai_nua(df, 0.6)
    if len(holdout) < 500:
        return {"loi": "holdout qua ngan"}
    cp = CP.tu_du_lieu(ma, holdout)
    bh = MP.mua_giu(holdout, cp, ma=ma, khung=khung)

    # lay chuoi vi the that lam khuon cum
    khuon = MP.chay(holdout, MAU.sinh("rsi_dao_chieu", holdout, {"n": 14, "vao": 30, "ra_": 55}),
                    cp, ma=ma, khung=khung).vi_the
    dk = CONG._do_dai_khoi(khuon)

    lot, ket = 0, []
    for i in range(so_ca):
        rng = np.random.default_rng(90000 + i)
        v = CONG.bootstrap_dung(khuon, rng, dk)
        kq = MP.chay(holdout, v, cp, ma=ma, khung=khung, da_dich=True)
        kt = CONG.xet(holdout, kq, bh, cp, gt_ma=f"NULL.{ma}.{khung}.{i}",
                      ho="null_hieu_chuan", da_dang_ky=True, tren_holdout=True)
        qua = kt["verdict"] in ("PASS", "UNG_VIEN", "NGHI_NHIN_TRUOC")
        lot += qua
        ket.append({"ca": i, "verdict": kt["verdict"],
                    "p": (kt.get("placebo") or {}).get("p_xau_nhat")})

    ty_le = lot / max(so_ca, 1)
    muc_tieu = CONG.nguong()["fdr_muc_tieu"]
    SO.ghi_chi_so("null_ty_le_lot", ty_le, {"so_ca": so_ca, "tai_san": ma, "khung": khung})
    SO.ghi_su_kien(TRU, "hieu_chuan_null",
                   {"tai_san": ma, "khung": khung, "so_ca": so_ca, "lot": lot})
    if ty_le > muc_tieu * 2:
        SO.bao_van_de("null_lot_qua_nhieu", "NANG",
                      f"Null factory: {lot}/{so_ca} ca KHONG CO EDGE van lot qua cong "
                      f"({ty_le:.0%} so voi muc tieu {muc_tieu:.0%}) - cong dang san xuat "
                      "phat hien sai, phai siet truoc khi tin bat ky PASS nao", {"ket": ket})
    else:
        SO.dong_van_de("null_lot_qua_nhieu", f"ty le lot {ty_le:.0%} trong muc tieu")
    return {"tai_san": ma, "khung": khung, "so_ca": so_ca, "so_lot": lot,
            "ty_le_lot": round(ty_le, 4), "muc_tieu_fdr": muc_tieu, "chi_tiet": ket}


# -------------------------------------------------------------- THU LUC CONG
def thu_luc_cong(cac_p=(0.50, 0.55, 0.60), ma: str | None = None,
                 khung: str = "H4") -> dict:
    """BAI KIEM LUC - chieu nguoc lai cua null factory.

    Null factory tra loi "cong co cho thu KHONG co edge lot khong". No KHONG
    tra loi duoc cau con lai: *cong co cho thu CO edge di qua khong?* Va hai
    cau do khac han nhau - mot cong TU CHOI TAT CA cho ket qua 0/10 y het mot
    cong hieu chuan tot. Chi co null la doc so lieu nguoc (memory
    `cong-pass-phai-hieu-chuan-hai-chieu`).

    Cach do: tin hieu biet truoc dau loi suat sap toi nhung CHI DUNG `p` phan
    tram so lan, con lai bốc ngau nhien. p = 0,50 khong co edge -> PHAI truot.
    p = 0,60 co edge that va lon -> PHAI qua. Cong nao cho p=0,50 qua thi qua
    xa; cong nao chan p=0,60 thi qua chat va moi ket luan am tinh cua no vo nghia.
    """
    import numpy as np
    ds = _tai_san_kha_dung()
    ma = ma or next((m for m in ds if m in DL.kho()), None)
    if not ma:
        return {"loi": "khong co tai san"}
    _df, _tr, hold, _c, cp = _nap(ma, khung)
    if len(hold) < 500:
        return {"loi": "holdout qua ngan"}
    bh = MP.mua_giu(hold, cp, ma=ma, khung=khung)
    r = MP._loi_suat_tien(hold)
    dau = np.sign(r)
    dau[dau == 0] = 1.0

    ket = []
    for p in cac_p:
        rng = np.random.default_rng(4242)
        # `p` phai la DO CHINH XAC, khong phai "ty le lan duoc mach nuoc".
        # Ban dau (16/08) toi viet: dung khi biet, con lai boc ngau nhien - do
        # chinh xac that thanh p + (1-p)/2, nen p=0,50 ra Sharpe 11,97 va bai
        # kiem bao "cong hong" trong khi cong khong he hong. Sai o thiet ke bai
        # kiem chu khong o thu duoc kiem.
        dung = rng.random(len(hold)) < p
        v = np.where(dung, dau, -dau)
        kq = MP.chay(hold, v, cp, ma=ma, khung=khung, da_dich=True)
        kt = CONG.xet(hold, kq, bh, cp, gt_ma=f"LUC.{ma}.{khung}.p{p}",
                      ho="thu_luc_cong", da_dang_ky=True, tren_holdout=True)
        cs = kt["so_sanh"]["he"]
        ket.append({"p": p, "verdict": kt["verdict"], "sharpe": cs.get("sharpe"),
                    "alpha_nam_pct": kt["so_sanh"]["alpha_vs_mua_giu"].get("alpha_nam_pct"),
                    "truot": [k for k, x in kt["dieu_kien"].items() if not x][:4]})

    qua = lambda v: v in ("PASS", "UNG_VIEN", "NGHI_NHIN_TRUOC")     # noqa: E731
    thap = next((k for k in ket if k["p"] <= 0.5), None)
    cao = next((k for k in ket if k["p"] >= 0.6), None)
    dat = bool(cao and qua(cao["verdict"])) and not (thap and qua(thap["verdict"]))
    SO.ghi_chi_so("cong_co_luc", 1.0 if dat else 0.0,
                  {"tai_san": ma, "khung": khung, "ket": ket})
    SO.ghi_su_kien(TRU, "thu_luc_cong", {"dat": dat, "ket": ket})
    if not dat:
        SO.bao_van_de(
            "cong_khong_co_luc", "NANG",
            "Cong KHONG phan biet duoc co edge voi khong co edge: "
            + "; ".join(f"p={k['p']} -> {k['verdict']}" for k in ket)
            + ". Moi ket luan AM TINH cua day chuyen dang vo nghia cho toi khi sua.",
            {"ket": ket})
    else:
        SO.dong_van_de("cong_khong_co_luc", "cong phan biet duoc hai chieu")
    return {"tai_san": ma, "khung": khung, "dat": dat, "ket": ket}


# ------------------------------------------------------------- MOT LUOT CHAY
def mot_luot(ngan_sach_giay: int = 900) -> dict:
    """Mot luot lam viec cua tru. Duoc dieu phoi goi lai lien tuc."""
    t0 = time.time()
    SO.nhip_tim(TRU, "chay")

    # 1) CANARY TRUOC - khong dat thi khong tinh gi ca
    lanh, bao = CANARY.chay_het(im_lang=True)
    if not lanh:
        SO.bao_van_de("canary_hong", "NANG",
                      "Canary khong dat - engine backtest dang hong. "
                      "Dung toan bo ket qua QUANTLAB cho toi khi sua.", bao)
        SO.nhip_tim(TRU, "dung_vi_canary", bao)
        return {"dung": "canary_hong", "hong": bao["hong"]}
    SO.dong_van_de("canary_hong", "canary da dat lai")

    lam = {"xac_nhan": 0, "kham_pha": 0, "pass": 0, "null": None, "chi_tiet": []}

    # 1b) HIEU CHUAN NULL dinh ky - do ty le lot cua thu khong co edge.
    #     Chay truoc khi xet ung vien that: neu cong dang xa thi biet ngay.
    cuoi = SO.mot("SELECT luc FROM chi_so_vh WHERE ten='null_ty_le_lot' "
                  "ORDER BY id DESC LIMIT 1")
    can_hieu_chuan = True
    if cuoi:
        try:
            from datetime import datetime
            can_hieu_chuan = (time.time() -
                              datetime.strptime(cuoi["luc"], "%Y-%m-%d %H:%M:%S").timestamp()
                              ) > 86400
        except Exception:
            can_hieu_chuan = True
    if can_hieu_chuan:
        try:
            lam["null"] = hieu_chuan_null(so_ca=10)
        except Exception as e:
            lam["null"] = {"loi": f"{type(e).__name__}: {str(e)[:80]}"}
        # HAI CHIEU: do null xong phai do LUC ngay, neu khong thi con so
        # "null lot 0%" khong phan biet duoc voi "cong tu choi tat ca".
        try:
            lam["luc"] = thu_luc_cong()
        except Exception as e:
            lam["luc"] = {"loi": f"{type(e).__name__}: {str(e)[:80]}"}

        # BA CHIEU. Null noi "thu khong co edge co lot khong", luc noi "thu co
        # edge co qua khong". Ca hai deu la cau HOI/DAP nhi phan. Con thieu con
        # so thu ba: edge NHO NHAT ma cong con thay duoc. Khong co no thi moi
        # ket luan am tinh deu khong doc duoc - "khong tim thay" co the la thi
        # truong rong ma cung co the la thuoc do qua tho.
        try:
            from nhan import do_luc as DLUC
            lam["do_nhay"] = DLUC.bao_cao_luc()
        except Exception as e:
            lam["do_nhay"] = {"loi": f"{type(e).__name__}: {str(e)[:80]}"}

    # Co che moi do tru NGHI de xuat -> nap vao thu vien mau truoc khi quet.
    try:
        lam["mau_dsl_nap"] = NP.nap_vao_mau()
    except Exception as e:
        lam["mau_dsl_nap"] = f"loi: {type(e).__name__}: {str(e)[:60]}"

    # 1c) SO CHENH LECH CHI PHI - alpha phep tru, chay moi 12 gio.
    #     Dat TRUOC vong backtest vi no re, chac an, va khong ton slot FDR.
    cuoi_cl = SO.mot("SELECT luc FROM chi_so_vh WHERE ten='chenh_lech_lon_nhat_diem' "
                     "ORDER BY id DESC LIMIT 1")
    can_cl = True
    if cuoi_cl:
        try:
            from datetime import datetime as _dt
            can_cl = (time.time() -
                      _dt.strptime(cuoi_cl["luc"], "%Y-%m-%d %H:%M:%S").timestamp()) > 43200
        except Exception:
            can_cl = True
    if can_cl:
        try:
            lam["chenh_lech_chi_phi"] = so_chenh_lech_chi_phi()
        except Exception as e:
            lam["chenh_lech_chi_phi"] = {"loi": f"{type(e).__name__}: {str(e)[:80]}"}

    # 1d) RUT HANG DOI UNG VIEN cua SEEKER -> bien thanh viec quet theo mau.
    #     Phai chay TRUOC vong lam viec ben duoi, neu khong thi ung vien vua
    #     duoc xep se phai cho tron mot chu ky.
    try:
        lam["ung_vien"] = rut_hang_doi_ung_vien()
    except Exception as e:
        lam["ung_vien"] = {"loi": f"{type(e).__name__}: {str(e)[:80]}"}

    # 2) Uu tien: viec DA XEP HANG (xac nhan gia thuyet da dang ky)
    while time.time() - t0 < ngan_sach_giay * 0.6:
        v = SO.nhan_viec(TRU)
        if not v:
            break
        try:
            # CHAN CHAY LAI XAC NHAN. Xac nhan la HAM Y NGUYEN: chay lai = nhin
            # lai cung mot holdout, va moi lan chay deu TIEU MOT SUAT FDR ke ca
            # khi truot o cong re (`confirmation van tieu thu suat FDR p=1`).
            #
            # Do that 23/08: 4 viec `xac_nhan_gop` nam CHO tu 22/08 trong khi ca
            # 4 gia thuyet DA CO ket qua FAIL cung ngay - viec duoc tao, ham
            # duoc goi thang (khong qua vong lam viec) nen `xong_viec` khong bao
            # gio duoc goi. Bat vong lap len la dot 4 suat FDR cho nhung gia
            # thuyet da biet truot.
            if v["loai"] in ("xac_nhan", "xac_nhan_gop"):
                _gt = (v["tham_so"] or {}).get("gt_ma", "")
                _cu = SO.mot("SELECT verdict, luc FROM ket_qua WHERE gt_ma=? "
                             "AND superseded_by IS NULL ORDER BY id DESC LIMIT 1",
                             _gt) if _gt else None
                if _cu:
                    SO.xong_viec(v["id"], {"bo_qua": "da co ket qua, khong chay lai",
                                           "gt_ma": _gt, "verdict_cu": _cu["verdict"],
                                           "luc_cu": _cu["luc"]})
                    lam["bo_qua_da_co_ket_qua"] = lam.get("bo_qua_da_co_ket_qua", 0) + 1
                    continue

            if v["loai"] == "xac_nhan":
                r = xac_nhan(v["tham_so"]["gt_ma"])
                lam["xac_nhan"] += 1
                lam["pass"] += int(r.get("verdict") == "PASS")
                lam["chi_tiet"].append(r)
                SO.xong_viec(v["id"], r)
            elif v["loai"] == "kham_pha_theo_mau":
                r = kham_pha_theo_mau(v["tham_so"].get("mau", ""),
                                      v["tham_so"].get("nguon_tai_lieu", ""))
                lam.setdefault("theo_mau", 0)
                lam["theo_mau"] += 1
                lam["chi_tiet"].append(r)
                SO.xong_viec(v["id"], r)
            elif v["loai"] == "kham_pha_gop":
                # Nhanh nay TUNG THIEU: `kham_pha_gop` da co ham tu 22/08 nhung
                # vong lam viec khong co case cho no, nen viec xep vao se roi
                # vao `else` va bi danh dau "loai viec chua ho tro" - im lang.
                # Day dung la che do hong da xay ra 16/08 voi `kham_pha_theo_mau`.
                r = kham_pha_gop(v["tham_so"].get("mau", ""),
                                 v["tham_so"].get("nguon_tai_lieu", ""))
                lam["kham_pha_gop"] = lam.get("kham_pha_gop", 0) + 1
                lam["chi_tiet"].append(r)
                SO.xong_viec(v["id"], r)
            elif v["loai"] == "xac_nhan_gop":
                r = xac_nhan_gop(v["tham_so"]["gt_ma"])
                lam.setdefault("xac_nhan_gop", 0)
                lam["xac_nhan_gop"] += 1
                lam["pass"] += int(r.get("verdict") == "PASS")
                lam["chi_tiet"].append(r)
                SO.xong_viec(v["id"], r)
            elif v["loai"] == "bac_cau_san":
                r = bac_cau_san(v["tham_so"].get("gt_ma", ""))
                lam.setdefault("bac_cau", 0)
                lam["bac_cau"] += 1
                lam["chi_tiet"].append(r)
                SO.xong_viec(v["id"], r)
            elif v["loai"] == "mt5_tick":
                # Buoc kiem dinh quyet dinh cuoi cung. Chua tu dong hoa duoc, va
                # dia dang duoi nguong -> KHONG duoc lang le nuot. Ghi ra danh
                # sach cho nguoi, giu nguyen viec o hang doi cua nguoi.
                r = xep_hang_mt5_tick(v["tham_so"].get("gt_ma", ""))
                lam["chi_tiet"].append(r)
                SO.xong_viec(v["id"], r)
            else:
                SO.xong_viec(v["id"], {"bo_qua": f"loai viec chua ho tro: {v['loai']}"})
        except Exception as e:
            SO.xong_viec(v["id"], loi=f"{type(e).__name__}: {e}")

    # 3) Con thoi gian -> KHAM PHA them be mat moi
    ds = _tai_san_kha_dung()
    trang_thai = _doc_tien_do()
    mau_thieu_luc: list[str] = []
    while time.time() - t0 < ngan_sach_giay:
        cap = _cap_ke_tiep(ds, trang_thai)
        if cap is None:
            trang_thai = {"vong": trang_thai.get("vong", 0) + 1, "da_quet": []}
            _luu_tien_do(trang_thai)
            continue
        ma, khung = cap
        try:
            r = kham_pha(ma, khung)
            lam["kham_pha"] += 1
            lam["chi_tiet"].append(r)
            for x in (r.get("chi_tiet_thieu_luc") or []):
                if x.get("sharpe") is not None and x.get("mde"):
                    mau_thieu_luc.append((float(x["sharpe"]) / float(x["mde"]),
                                          x["mau"]))
        except Exception as e:
            r = {"ma": ma, "khung": khung, "loi": f"{type(e).__name__}: {str(e)[:80]}"}
            lam["chi_tiet"].append(r)
        trang_thai.setdefault("da_quet", []).append(f"{ma}|{khung}")
        _luu_tien_do(trang_thai)

    # 3b) DUONG GOP. Chay SAU vong kham pha don le va dung ket qua cua no lam
    #     tin hieu: mau nao co ung vien bi chan vi THIEU LUC nghia la co che do
    #     co dau hieu tren train nhung qua yeu de mot tai san don le phan xu -
    #     do dung la truong hop ma gop sinh ra de giai. Mau khong co dau hieu
    #     nao thi khong dua vao: khong duoc tieu suat FDR cho thu ma khong gi
    #     goi y ca.
    #
    #     Tin hieu lay tu TRAIN nen dung o tang kham pha, khong lam ban holdout.
    #     Xep theo KHOANG CACH TOI NGUONG (sharpe kham pha / MDE cua cap), khong
    #     theo thu tu quet. Lan chay 22/08 lay 5 mau dau tien nhin thay va cho ra
    #     5 lan KHONG_CO_UNG_VIEN - trong khi mau manh nhat cua vong do nam o
    #     cuoi danh sach quet. Thu tu quet la mot chi tiet ky thuat, no khong
    #     duoc quyet dinh ngan sach FDR tieu vao dau.
    lam["gop"] = []
    xep_mau: dict[str, float] = {}
    for ty_le, ten in mau_thieu_luc:
        if ty_le > xep_mau.get(ten, -9):
            xep_mau[ten] = ty_le
    uu_tien_mau = [t for t, _ in sorted(xep_mau.items(), key=lambda x: -x[1])]
    lam["gop_uu_tien"] = [(t, round(xep_mau[t], 3)) for t in uu_tien_mau[:8]]
    for ten_mau in uu_tien_mau[:TOI_DA_GOP_MOI_LUOT]:
        try:
            lam["gop"].append(kham_pha_gop(ten_mau, nguon="thieu_luc_don_le"))
        except Exception as e:
            lam["gop"].append({"mau": ten_mau,
                               "loi": f"{type(e).__name__}: {str(e)[:80]}"})
    # Xac nhan NGAY cho nhung gia thuyet gop vua dang ky. Goi thang chu KHONG
    # keo them mot vong `SO.nhan_viec`: hang doi chung cho moi loai viec, va
    # mot vong lay bua se rut trung viec `xac_nhan` cua duong don le roi phai
    # tu quyet dinh lam gi voi no - hoac lam (ngoai ngan sach) hoac dong lai
    # (mat viec). Ca hai deu sai. Viec da xep van nam nguyen trong hang doi va
    # `xac_nhan_gop` la HAM Y NGUYEN (idempotent) nen luot sau chay lai khong
    # cham holdout lan hai.
    for g in lam["gop"]:
        if not g.get("xep_viec"):
            continue
        try:
            r = xac_nhan_gop(g["gt"])
            lam.setdefault("xac_nhan_gop", 0)
            lam["xac_nhan_gop"] += 1
            lam["pass"] += int(r.get("verdict") == "PASS")
            lam["chi_tiet"].append(r)
        except Exception as e:
            lam["chi_tiet"].append({"gt": g.get("gt"),
                                    "loi": f"{type(e).__name__}: {str(e)[:80]}"})

    # 4) TANG 3 - tinh von va ghep danh muc tu nhung gia thuyet DA QUA cong.
    #    Truoc 21/08 tang nay khong ton tai: he kiem dinh xong roi de day, khong
    #    ai tra loi "bo bao nhieu tien vao moi cai va ghep lai co hon khong".
    try:
        from nhan import danh_muc as DMUC
        lam["danh_muc"] = DMUC.danh_muc_hien_tai("PASS")
    except Exception as e:
        lam["danh_muc"] = {"loi": f"{type(e).__name__}: {str(e)[:80]}"}

    SO.ghi_chi_so("quantlab_xac_nhan", lam["xac_nhan"])
    SO.ghi_chi_so("quantlab_kham_pha", lam["kham_pha"])
    SO.nhip_tim(TRU, "nghi", {k: v for k, v in lam.items() if k != "chi_tiet"})
    return lam


TIEN_DO = Path(__file__).resolve().parent.parent / "reports" / "quantlab_tien_do.json"


def _doc_tien_do() -> dict:
    try:
        return json.loads(TIEN_DO.read_text(encoding="utf-8-sig"))
    except Exception:
        return {"vong": 0, "da_quet": []}


def _luu_tien_do(s: dict) -> None:
    TIEN_DO.parent.mkdir(parents=True, exist_ok=True)
    s["da_quet"] = list(dict.fromkeys(s.get("da_quet", [])))[-500:]
    TIEN_DO.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")


def _cap_ke_tiep(ds, trang_thai):
    """Cap (tai san, khung) chua quet trong vong nay.

    Hoi `_khung_cua` chu khong duyet thang `KHUNG_QUET`: 18 tai san mo rong deu
    la bang D1, va hoi H1/H4 tren chung chi de nhan ValueError roi ghi vao
    `da_quet` nhu da lam xong - tuc hai phan ba vong quet la ngoai le im lang.
    """
    da = set(trang_thai.get("da_quet", []))
    for ma, khung in _thu_tu_quet(ds):
        if f"{ma}|{khung}" not in da:
            return ma, khung
    return None


def _thu_tu_quet(ds) -> list[tuple[str, str]]:
    """Xen ke hai lan thay vi quet het lan nay roi moi den lan kia.

    Duyet tuan tu thi 11 tai san uu tien x 3 khung = 33 cap chay truoc, va vi
    moi cap dang ky toi da 3 gia thuyet nen mot vong quet tieu gan 100 suat FDR
    o lan giao dich - noi nguong phat hien la 1,39 - TRUOC KHI cham vao chuoi
    dai, noi nguong la 0,54. Xen ke thi mot luot CPU ngan van cham duoc ca hai.
    """
    theo_lan: dict[str, list[tuple[str, str]]] = {"san": [], "ngoai": []}
    for ma in ds:
        lan = DL.nguon_tai_san(ma)
        for khung in _khung_cua(ma):
            theo_lan.setdefault(lan, []).append((ma, khung))
    ra: list[tuple[str, str]] = []
    i = 0
    while any(theo_lan.values()):
        for lan in ("san", "ngoai"):
            if i < len(theo_lan[lan]):
                ra.append(theo_lan[lan][i])
        if all(i >= len(v) for v in theo_lan.values()):
            break
        i += 1
    return ra




# ==============================================================
# PHEU SANG V0-V3 (2308). Ham MOI, khong sua ham co san.
#
# Ban dau (DS) goi `SO.doc_candidate_queue(gioi_han=...)` - tham so do khong ton
# tai (chu ky that la `after_id`/`limit`/`route`) nen ham nem TypeError ngay dong
# dau va chua bao gio chay duoc mot lan nao. Bo test van xanh vi khong bai nao
# goi ham nay.
#
# Hai loi nua o cung ham do, deu im lang neu sua moi loi dau:
#   - doc `u["tai_san"]` / `u["fingerprint"]` tu hang doi, nhung hang doi tra
#     `{"id","candidate","priority",...}` va thong tin nam trong
#     `u["candidate"].metadata`;
#   - dung spread ghi cung 0,001 = 10 bps MOT CHIEU, gap ~10 lan so do that
#     (0,7-1,0 bps cho CFD chi so) - du de giet moi ung vien o V2.

def chay_pheu_ung_vien(gioi_han: int = 20, tiep_tuc: bool = True) -> dict:
    """Rut ung vien tu hang doi, cho qua pheu V0-V3, ghi ket qua vao so.

    KHONG dang ky gia thuyet va KHONG cham holdout: cai gi qua duoc V3 thi tra
    ve `SAN_SANG_V4` va di tiep bang duong `kham_pha_theo_mau`/`xac_nhan` da co.
    """
    from nhan import sang_loc as SL
    NP.nap_vao_mau()
    SL.xoa_bo_dem()

    tu = 0
    if tiep_tuc:
        try:
            tu = int(json.loads(PHEU_CURSOR.read_text(encoding="utf-8"))["id"])
        except Exception:
            tu = 0

    bao = {"da_doc": 0, "san_sang_v4": 0, "loai": 0, "chua_du_luc": 0,
           "mau_la": 0, "toi": tu, "theo_vong": {}, "chi_tiet": []}
    try:
        hang = SO.doc_candidate_queue(after_id=tu,
                                      limit=max(1, min(int(gioi_han), 1000)))
    except Exception as e:
        bao["loi"] = f"{type(e).__name__}: {str(e)[:120]}"
        return bao

    for muc in hang:
        bao["da_doc"] += 1
        bao["toi"] = muc["id"]
        uv = muc["candidate"]
        md = uv.metadata or {}
        ten_mau = str(md.get("mau") or "").strip()
        if not ten_mau or ten_mau not in MAU.MAU:
            bao["mau_la"] += 1
            continue

        ma = str(md.get("tai_san") or "").strip() or _tai_san_dai_dien(ten_mau)
        khung = str(md.get("khung") or "").strip() or _khung_cua(ma)[0]
        try:
            # QUANTLAB da co ban dem phep thu phan chung rieng - truyen vao de
            # khong do lai. Chay ngoai QUANTLAB thi `tu_do_pham_vi=True`.
            r = SL.chay_pheu(ten_mau, _thuan(md.get("tham_so")) or {}, ma, khung,
                             pham_vi=_pham_vi_cua(ten_mau))
        except Exception as e:
            bao["chua_du_luc"] += 1
            bao["chi_tiet"].append({"mau": ten_mau, "loi": f"{type(e).__name__}: {str(e)[:80]}"})
            continue

        kl = r["ket_luan"]
        bao["theo_vong"][r["vong"]] = bao["theo_vong"].get(r["vong"], 0) + 1
        if kl == SL.SAN_SANG_V4:
            bao["san_sang_v4"] += 1
        elif kl == SL.LOAI:
            bao["loai"] += 1
        elif kl == SL.NEN_GOP:
            # Thieu luc tren mot tai san nhung phep thu phan chung noi co che
            # song o ca lop -> xep viec kiem tren RO thay vi bo. Duong gop da
            # co san (`kham_pha_gop`); truoc day khong ai xep viec vao no.
            bao["nen_gop"] = bao.get("nen_gop", 0) + 1
            if SO.them_viec(TRU, "kham_pha_gop", {"mau": ten_mau,
                                                  "nguon_tai_lieu": "pheu_v3"},
                            uu_tien=3):
                bao["xep_viec_gop"] = bao.get("xep_viec_gop", 0) + 1
        else:
            bao["chua_du_luc"] += 1
        bao["chi_tiet"].append({"mau": ten_mau, "tai_san": ma, "khung": khung,
                                "ket_luan": kl, "vong": r["vong"],
                                "ly_do": r["ly_do"], "do": r.get("do")})

    PHEU_CURSOR.parent.mkdir(parents=True, exist_ok=True)
    PHEU_CURSOR.write_text(json.dumps({"id": int(bao["toi"])}), encoding="utf-8")
    bao["bi_loai"] = SL.lay_bo_dem()
    bao["cho_them_du_lieu"] = SL.lay_cho_them()
    SO.ghi_chi_so("pheu_san_sang_v4", bao["san_sang_v4"],
                  {k: v for k, v in bao.items() if k != "chi_tiet"})
    return bao


def _tai_san_dai_dien(ten_mau: str) -> str:
    """Tai san de chay pheu khi ung vien khong noi ro. Lay tai san DAI NHAT
    trong lop ma ho co che do tuyen bo - pheu la buoc sang, chua phai buoc
    ket luan, nen mot chuoi dai la du va re."""
    try:
        ho = (MAU.MAU.get(ten_mau) or {}).get("ho") or "khac"
        khung = _khung_cua_ho_an_toan(ho)
        kho = _kho_pham_vi(khung)
        return kho[0] if kho else "US500CASH"
    except Exception:
        return "US500CASH"


def _khung_cua_ho_an_toan(ho: str) -> str:
    try:
        from nhan import pham_vi as PV
        return PV.khung_cua_ho(ho)
    except Exception:
        return KHUNG_PHAM_VI


if __name__ == "__main__":
    SO.khoi_tao()
    ngan = int(sys.argv[sys.argv.index("--giay") + 1]) if "--giay" in sys.argv else 300
    print(json.dumps(mot_luot(ngan), ensure_ascii=False, indent=1, default=str)[:6000])
