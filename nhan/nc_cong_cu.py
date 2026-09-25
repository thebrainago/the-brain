# -*- coding: utf-8 -*-
"""nc_cong_cu.py - BO CONG CU cua nha nghien cuu AI: MOT danh sach, ba cach goi (Claude API, Claude Code, nguoi).

Chu du an 25/09/2026: *"The Brain la cong cu va cac phuong an cho cau. Phan
thuc thi chinh va suy luan chinh phai do AI nam quyen."*

File nay la cho cau noi do thanh MA. Moi cong cu la mot phep do cua lab (chay
he, quet, mo xe lenh, tim quy luat, niem phong...) co ten, mo ta noi RO KHI NAO
goi, va JSON schema. Cung mot danh sach phuc vu:

    Claude API       `nc_tac_tu.chay_vong` gui `SCHEMA_API` lam `tools`
    Claude Code      `python b.py nc cc <ten> '<json>'` (hoac `@file.json`)
    nguoi / script   `goi(ten, dau_vao)`

Nen AI nao ngoi ghe nha nghien cuu - mot vong API 24/7, mot phien Claude Code
dang chat voi chu du an, hay may tu lai khi het token - deu dung DUNG bo do
va DUNG so tay. Khong co duong tat nao ghi ket qua ma khong qua day.

Cong cu KHONG quyet dinh nghien cuu gi. Cong cu do, cham DAT/AM/CHUA_DO_DUOC
bang code, ghi so tay. AI quyet dinh.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Callable

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nhan import (nc_dac_trung as DT, nc_du_lieu as NDL, nc_so_tay as ST,
                  nc_thi_nghiem as TN)

LAB = Path(__file__).resolve().parent.parent
THU_MUC_EA = LAB / "reports" / "nc_ea"
HANG_DOI_TESTER = LAB / "reports" / "nc_hang_doi_tester.jsonl"
YEU_CAU_SEEKER = LAB / "reports" / "nc_yeu_cau_seeker.jsonl"
GIOI_HAN_KY_TU = 9000

_SPEC = {"type": "object", "description": (
    "Khai bao DSL cua ngu phap co che: {ten, co_che (MOT CAU >= 25 ky tu: ai tra tien "
    "va vi sao), ho, chieu (1 mua / -1 ban), giu (so bar), vao: [dieu kien VA], ra: "
    "[dieu kien HOAC]}. Xem hien chuong muc NGU PHAP.")}
_QT = {"type": "object", "description": (
    "Luat quan tri vi the cho dap_quan_tri (tuy chon): sl_atr, tp_atr, hue_tu_atr, "
    "trail_tu_atr, trail_buoc, thoat_bar, chot_phan. Vd {\"sl_atr\": 2, \"tp_atr\": 3}.")}
_MA = {"type": "string", "description": "Ma tai san, vd AUDCAD, XM_US500CASH, TONG_HOP_LOC_1"}
_KHUNG = {"type": "string", "description": "Khung: M15, M30, H1, H4, D1 ..."}
_GT = {"type": "integer", "description": "id gia thuyet trong so tay (de dem phep thu theo dong)"}


def _tuong_doi(p: Path) -> str:
    """Duong dan tuong doi voi lab neu nam trong lab (bao cao doc duoc tren moi may)."""
    try:
        return str(Path(p).resolve().relative_to(LAB))
    except ValueError:
        return str(p)


def _cc(ten: str, mo_ta: str, thuoc_tinh: dict, bat_buoc: list, ham: Callable) -> dict:
    return {"ten": ten, "mo_ta": mo_ta,
            "schema": {"type": "object", "properties": thuoc_tinh, "required": bat_buoc},
            "ham": ham}


# ------------------------------------------------------------- CAI DAT
def _xem_so_tay(so_dong: int = 12, **_) -> dict:
    return {"so_tay": ST.tom_tat_md(int(so_dong))}


def _danh_sach(**_) -> dict:
    return {"tai_san": NDL.danh_sach(), "dac_trung": DT.mo_ta(),
            "doan": {k: "%d%%-%d%%" % (a * 100, b * 100) for k, (a, b) in NDL.DOAN.items()}}


def _ghi_gia_thuyet(cau: str = "", vi_sao: str = "", ho: str = "", pham_vi=None,
                    cha: int | None = None, uu_tien: float | None = None,
                    gt_id: int | None = None, trang_thai: str | None = None,
                    ket_luan: str | None = None, nguon: str = "ai", **_) -> dict:
    if gt_id is not None:
        return {"gia_thuyet": ST.cap_nhat_gia_thuyet(int(gt_id), trang_thai, ket_luan, uu_tien)}
    if len(cau.strip()) < 15 or len(vi_sao.strip()) < 15:
        raise ValueError("gia thuyet can `cau` (phat bieu kiem duoc) va `vi_sao` (ai tra "
                         "tien / co che) - moi cai >= 15 ky tu")
    i = ST.them_gia_thuyet(cau, vi_sao, ho, pham_vi, cha, nguon,
                           0.5 if uu_tien is None else float(uu_tien))
    return {"gt_id": i}


def _ghi_hieu_biet(cau: str = "", do_tin: float = 0.5, bang_chung: list | None = None,
                   pham_vi=None, bac: int | None = None, ly_do: str = "", **_) -> dict:
    if bac is not None:
        ST.bac_hieu_biet(int(bac), ly_do or "bi bac", bang_chung)
        return {"da_bac": int(bac)}
    if len(cau.strip()) < 15:
        raise ValueError("hieu biet can mot cau >= 15 ky tu")
    return {"hb_id": ST.them_hieu_biet(cau, do_tin, bang_chung, pham_vi)}


def _ghi_cau_hoi(cau: str = "", vi_sao: str = "", uu_tien: float = 0.5,
                 dong: int | None = None, tra_loi: str = "", trang_thai: str = "XONG",
                 gt_id: int | None = None, nguon: str = "ai", **_) -> dict:
    if dong is not None:
        ST.dong_cau_hoi(int(dong), tra_loi or "-", trang_thai)
        return {"da_dong": int(dong), "trang_thai": trang_thai}
    if len(cau.strip()) < 10:
        raise ValueError("cau hoi can >= 10 ky tu")
    return {"ch_id": ST.them_cau_hoi(cau, vi_sao, uu_tien, nguon, gt_id)}


def _xuat_mq5(ten: str, khung: str, cac: list, **_) -> dict:
    """Chi xuat khai bao DA DAT niem phong, tren ma that. Ghi .mq5 + mot dong hang doi tester."""
    from nhan import dich_mq5 as DM
    specs, ma_list, loi, don_bay = [], set(), [], {}
    for c in cac:
        ma = str(c.get("ma", "")).upper()
        if NDL.la_tong_hop(ma):
            loi.append("%s la chuoi TONG HOP - chi de hieu chuan, khong bao gio ra tester" % ma)
            continue
        s = TN.chuan_hoa_spec(c["spec"])
        vt = ST.van_tay("niem_phong", ma, str(khung).upper(),
                        {k: s[k] for k in ("vao", "ra", "chieu", "giu")},
                        TN.chuan_hoa_quan_tri(c.get("quan_tri")))
        np_ = ST.mot("SELECT trang_thai, ket_qua FROM niem_phong WHERE van_tay=?", vt)
        if np_.get("trang_thai") != "DAT":
            loi.append("%s/%s: chua DAT niem phong (%s) - xuat truoc la de tester nhin doan "
                       "niem phong" % (ma, s["ten"], np_.get("trang_thai") or "chua mo"))
            continue
        if c.get("quan_tri"):
            loi.append("%s: luat quan tri chua co duong dich MQL5 trong ban nay (dich_mq5_qtvt "
                       "can noi) - xuat phan VAO, ghi chu quan tri vao hang doi" % s["ten"])
        specs.append(s)
        ma_list.add(ma)
        try:     # don bay niem phong da CHOT truoc khi mo - tester phai chay dung muc do
            ck = (json.loads(np_.get("ket_qua") or "{}").get("tien") or {}).get("o_don_bay_cam_ket")
        except Exception:
            ck = None
        don_bay["%s/%s" % (ma, s["ten"])] = ck
    if not specs:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": loi or ["khong co khai bao nao"]}
    nguon, dat = DM.sinh_ea(specs, ten=ten, khung=str(khung).upper())
    THU_MUC_EA.mkdir(parents=True, exist_ok=True)
    f = THU_MUC_EA / ("%s.mq5" % ten)
    f.write_text(nguon, encoding="utf-8")
    HANG_DOI_TESTER.parent.mkdir(parents=True, exist_ok=True)
    with HANG_DOI_TESTER.open("a", encoding="utf-8") as g:
        g.write(json.dumps({"luc": ST.bay_gio(), "ea": _tuong_doi(f), "khung": khung,
                            "ma": sorted(ma_list), "co_che": [s["ten"] for s in dat],
                            "quan_tri": [c.get("quan_tri") for c in cac],
                            "don_bay_cam_ket": don_bay, "tran_dd_pct": TN.DD_TRAN * 100,
                            "trang_thai": "CHO_TESTER"}, ensure_ascii=False) + "\n")
    return {"trang_thai": "DAT", "ea": _tuong_doi(f), "so_co_che": len(dat),
            "canh_bao": loi, "don_bay_cam_ket": don_bay,
            "buoc_tiep": "may chu du an: chay tester (Model=4) cho hang doi "
                         "reports/nc_hang_doi_tester.jsonl, lot theo don_bay_cam_ket; DAT that "
                         "= co lai va maxDD < %.0f%% trong tester" % (TN.DD_TRAN * 100)}


def _yeu_cau_seeker(chu_de: str, tu_khoa: list, vi_sao: str = "", **_) -> dict:
    YEU_CAU_SEEKER.parent.mkdir(parents=True, exist_ok=True)
    with YEU_CAU_SEEKER.open("a", encoding="utf-8") as g:
        g.write(json.dumps({"luc": ST.bay_gio(), "chu_de": chu_de, "tu_khoa": tu_khoa[:30],
                            "vi_sao": vi_sao, "trang_thai": "CHO"}, ensure_ascii=False) + "\n")
    return {"da_xep": len(tu_khoa[:30]), "file": _tuong_doi(YEU_CAU_SEEKER)}


CONG_CU: list[dict] = [
    _cc("xem_so_tay",
        "Doc HO SO NGHIEN CUU: cau hoi mo (nguoi dat xep truoc), gia thuyet dang song, thi "
        "nghiem tot nhat, hieu biet co bang chung, phep thu da tieu theo ma. Goi o DAU moi chu "
        "ky neu ho so trong loi nhac da cu, va truoc khi mo mot huong moi de khong dao lai.",
        {"so_dong": {"type": "integer", "description": "so dong moi muc (mac dinh 12)"}}, [],
        _xem_so_tay),
    _cc("danh_sach_du_lieu",
        "Liet ke tai san co du lieu (so nam, co spread khong), bon chuoi TONG_HOP co dap an "
        "(chi de hieu chuan), va danh sach DAC TRUNG dung trong dieu kien. Goi khi chua biet "
        "ma nao dung duoc.", {}, [], _danh_sach),
    _cc("ho_so_tai_san",
        "Tinh cach cua (ma, khung) tren doan kham pha: tu tuong quan, ti so phuong sai (hoi quy "
        "hay quan tinh), cum bien dong, mua vu theo thu/thang/gio (t-stat), chi phi so voi bien "
        "do bar, moc mua-giu. Goi TRUOC khi dat gia thuyet tren mot ma moi.",
        {"ma": _MA, "khung": _KHUNG}, ["ma", "khung"],
        lambda ma, khung, vong_id=None, **_: TN.ho_so(ma, khung, vong_id=vong_id)),
    _cc("tim_quy_luat",
        "NOI SINH: tim dieu kien (1-2 dac trung) lam loi suat h bar toi lech khoi 0 SAU CHI "
        "PHI, tren doan kham pha, co null xoay vong hieu chuan ca qua trinh do tim (p_null). "
        "Tra ve luat kem `spec` DSL chay duoc ngay. Goi khi muon AI tu tim luat vao lenh tu du "
        "lieu thay vi tu tai lieu. Luat p_null > 0,1 = nhieu cung de ra.",
        {"ma": _MA, "khung": _KHUNG,
         "chan_troi": {"type": "array", "items": {"type": "integer"},
                       "description": "so bar giu (mac dinh [1,3,5,10])"},
         "so_null": {"type": "integer", "description": "so lan null (mac dinh 200)"},
         "dac_trung": {"type": "array", "items": {"type": "string"},
                       "description": "chi dung cac dac trung nay (tuy chon)"},
         "gt_id": _GT}, ["ma", "khung"],
        lambda ma, khung, chan_troi=(1, 3, 5, 10), so_null=200, dac_trung=None, gt_id=None,
        vong_id=None, **_: TN.tim_quy_luat(ma, khung, chan_troi, so_null, dac_trung, gt_id, vong_id)),
    _cc("thu_co_che",
        "Chay MOT he (khai bao DSL + luat quan tri tuy chon) tren doan KHAM PHA voi chi phi that. "
        "DAT = CO LAI sau moi phi (tieu chi chu du an: co lai + maxDD < 80%, phuong phap nao "
        "cung duoc). Tra ve lenh (so lenh, ti le thang, rr, ky vong bps, t), TIEN (CAGR tot nhat "
        "voi maxDD < 80% va don bay do), nhan_canh_bao (hon moc, kieu martingale, duoi lo - "
        "khong chan), theo nam. Chay y het lan nua thi tra ket qua cu.",
        {"ma": _MA, "khung": _KHUNG, "spec": _SPEC, "quan_tri": _QT, "gt_id": _GT},
        ["ma", "khung", "spec"],
        lambda ma, khung, spec, quan_tri=None, gt_id=None, vong_id=None, **_:
        TN.danh_gia(ma, khung, spec, quan_tri, "kham_pha", gt_id, vong_id)),
    _cc("quet_tham_so",
        "Quet luoi tham so cua mot he tren kham pha va doc HINH DANG: CAO_NGUYEN (nhieu o lan "
        "can cung CO LAI - dang tin) hay CAI_GAI (mot o dep le loi - cuc dai ngau nhien). `luoi` = "
        "{duong_dan_tham_so: [gia tri]} (duong dan nhu vao0_phai_hang, vao0_trai_n, giu; them "
        "tien to qt. cho luat quan tri, vd qt.sl_atr). Bo trong -> luoi tu dong. Moi o la mot "
        "phep thu - quet co chu dich, khong quet cho co.",
        {"ma": _MA, "khung": _KHUNG, "spec": _SPEC, "quan_tri": _QT,
         "luoi": {"type": "object", "description": "{tham_so: [gia tri,...]}"},
         "toi_da_o": {"type": "integer", "description": "tran so o (mac dinh 150)"}, "gt_id": _GT},
        ["ma", "khung", "spec"],
        lambda ma, khung, spec, quan_tri=None, luoi=None, toi_da_o=150, gt_id=None,
        vong_id=None, **_: TN.quet(ma, khung, spec, luoi, quan_tri, "kham_pha", gt_id, vong_id,
                                   int(toi_da_o))),
    _cc("mo_xe_lenh",
        "HOC TU LENH DUNG/LENH SAI: chay he tren kham pha, tach tung lenh, so ngu canh tai bar "
        "tin hieu cua lenh thang va lenh thua -> bo loc de xuat (kem spec_de_xuat da gan dieu "
        "kien) voi p_null; va MFE/MAE -> goi y luat quan tri (SL/hue/trailing/thoat bar). Goi "
        "khi mot he co y tuong dung nhung ky vong yeu/am, hoac truoc khi tinh chinh quan tri.",
        {"ma": _MA, "khung": _KHUNG, "spec": _SPEC, "quan_tri": _QT,
         "so_null": {"type": "integer", "description": "so lan null (mac dinh 200)"}, "gt_id": _GT},
        ["ma", "khung", "spec"],
        lambda ma, khung, spec, quan_tri=None, so_null=200, gt_id=None, vong_id=None, **_:
        TN.mo_xe(ma, khung, spec, quan_tri, int(so_null), gt_id, vong_id)),
    _cc("thu_luoi",
        "He LUOI khong can tin hieu vao (nhan/luoi.py - engine cua ket qua AUDCAD +13,26%/nam "
        "holdout voi TIA LENH). tham_so: buoc, tp, tran_tang, che_do (mua|ban|hai_chieu), lot, "
        "cho_lui, kieu_lot (phang|cong|nhan), he_so_lot, tia_lenh, bien_cap, cap_moi_bar, "
        "chot_tien, dung_lo_tong, he_so_buoc, buoc_tran. Martingale/DCA hop le (chu du an). "
        "DAT = co lai sau phi, khong chay tai khoan o lot dang thu. Tra he so lot cham tran "
        "maxDD 80% (tinh CHINH XAC tren duong equity) va LO TREO o lot do. Chi AUDCAD (phi qua "
        "dem dang ghim) + TONG_HOP. Dung khung M15/M5: luoi song bang duong di trong bar.",
        {"ma": _MA, "khung": _KHUNG, "tham_so": {"type": "object"},
         "doan": {"type": "string", "enum": ["kham_pha", "xac_nhan"]},
         "von": {"type": "number", "description": "von bang dong bao gia (mac dinh 10000)"},
         "gt_id": _GT}, ["ma", "khung"],
        lambda ma, khung, tham_so=None, doan="kham_pha", von=10000.0, gt_id=None, vong_id=None,
        **_: TN.danh_gia_luoi(ma, khung, tham_so, doan, float(von), gt_id, vong_id)),
    _cc("xac_nhan",
        "Chay mot he DA CHON tren doan XAC NHAN (60%-80%, chua dung toi luc kham pha). So lan "
        "nhin bi dem theo dong gia thuyet. Chi goi cho bien the ban da chot tren kham pha - "
        "khong dung de do tim.",
        {"ma": _MA, "khung": _KHUNG, "spec": _SPEC, "quan_tri": _QT, "gt_id": _GT},
        ["ma", "khung", "spec", "gt_id"],
        lambda ma, khung, spec, gt_id, quan_tri=None, vong_id=None, **_:
        TN.danh_gia(ma, khung, spec, quan_tri, "xac_nhan", gt_id, vong_id)),
    _cc("niem_phong",
        "PHEP THU CUOI: mo doan NIEM PHONG (20% cuoi) cho MOT khai bao da dong bang. Moi khai "
        "bao chi mo mot lan; moi dong gia thuyet toi da 3 lan. Chan: CO LAI sau phi, chi phi do "
        "duoc, >= 20 lenh, va maxDD < 80% o DON BAY CAM KET (chot tren kham pha + xac nhan truoc "
        "khi mo). Nhan: hon moc, tang 2, duoi lo, so phep thu, Sharpe giam phat, cong that. "
        "Chi goi khi he da qua xac_nhan va ban san sang chap nhan ket qua.",
        {"ma": _MA, "khung": _KHUNG, "spec": _SPEC, "quan_tri": _QT, "gt_id": _GT},
        ["ma", "khung", "spec", "gt_id"],
        lambda ma, khung, spec, gt_id, quan_tri=None, vong_id=None, **_:
        TN.niem_phong(ma, khung, spec, quan_tri, gt_id, vong_id)),
    _cc("ghep_danh_muc",
        "Ghep 2-8 he (co the khac ma/khung) cung rui ro, do tuong quan ngay va TIEN cua ca ro "
        "(CAGR tot nhat voi maxDD < 80%). Goi khi da co vai chan song rieng le - chan am nhung "
        "nguoc pha cung co the lam ro tot len.",
        {"chan": {"type": "array", "items": {"type": "object"},
                  "description": "[{ma, khung, spec, quan_tri?}]"},
         "doan": {"type": "string", "enum": ["kham_pha", "xac_nhan"]}}, ["chan"],
        lambda chan, doan="kham_pha", vong_id=None, **_: TN.ghep_danh_muc(chan, doan, vong_id)),
    _cc("ghi_gia_thuyet",
        "Ghi gia thuyet MOI (cau, vi_sao = ai tra tien, ho, pham_vi, cha) -> gt_id; HOAC cap nhat "
        "mot gia thuyet (gt_id + trang_thai MO/DANG_THU/TRIEN_VONG/BAC_BO + ket_luan). Moi huong "
        "nghien cuu phai co gia thuyet de phep thu duoc dem theo dong.",
        {"cau": {"type": "string"}, "vi_sao": {"type": "string"}, "ho": {"type": "string"},
         "pham_vi": {"type": "object"}, "cha": _GT, "uu_tien": {"type": "number"},
         "gt_id": _GT, "trang_thai": {"type": "string"}, "ket_luan": {"type": "string"}}, [],
        _ghi_gia_thuyet),
    _cc("ghi_hieu_biet",
        "Ghi mot dieu DA HOC DUOC (do_tin 0..1, bang_chung = danh sach tn_id). Khong co bang "
        "chung thi do tin bi kep <= 0,3. Hoac bac mot hieu biet cu (bac = hb_id, ly_do). Goi "
        "cuoi moi phat hien hoac moi lan mot ket qua lat nguoc dieu cu.",
        {"cau": {"type": "string"}, "do_tin": {"type": "number"},
         "bang_chung": {"type": "array", "items": {"type": "integer"}},
         "pham_vi": {"type": "object"}, "bac": {"type": "integer"}, "ly_do": {"type": "string"}},
        [], _ghi_hieu_biet),
    _cc("ghi_cau_hoi",
        "Them cau hoi vao CHUONG TRINH NGHIEN CUU (cau, vi_sao, uu_tien) - hoac dong cau hoi "
        "(dong = ch_id, tra_loi, trang_thai XONG/BO). Cuoi moi chu ky: dong cau da tra loi, mo "
        "cau moi dang gia nhat.",
        {"cau": {"type": "string"}, "vi_sao": {"type": "string"}, "uu_tien": {"type": "number"},
         "dong": {"type": "integer"}, "tra_loi": {"type": "string"},
         "trang_thai": {"type": "string"}, "gt_id": _GT}, [], _ghi_cau_hoi),
    _cc("xuat_mq5",
        "Xuat cac khai bao DA DAT niem phong (ma that) thanh MOT EA .mq5 + xep hang doi MT5 "
        "tester tren may chu du an. Buoc bat buoc truoc demo: MT5 tester moi la do that.",
        {"ten": {"type": "string"}, "khung": _KHUNG,
         "cac": {"type": "array", "items": {"type": "object"},
                 "description": "[{ma, spec, quan_tri?}]"}}, ["ten", "khung", "cac"], _xuat_mq5),
    _cc("yeu_cau_seeker",
        "Nho SEEKER di tim tai lieu/ma nguon cho mot chu de cu the (tu khoa da ngon ngu). Goi khi "
        "mot huong can y tuong ma du lieu chua goi y duoc - vd mot kieu quan tri lenh chua co.",
        {"chu_de": {"type": "string"}, "tu_khoa": {"type": "array", "items": {"type": "string"}},
         "vi_sao": {"type": "string"}}, ["chu_de", "tu_khoa"], _yeu_cau_seeker),
]
THEO_TEN = {c["ten"]: c for c in CONG_CU}
#: Cong cu chi GHI so tay (khong do gi) - van duoc goi khi het ngan sach chu ky.
CONG_CU_GHI = ("ghi_gia_thuyet", "ghi_hieu_biet", "ghi_cau_hoi", "xem_so_tay")


def schema_api() -> list[dict]:
    """Danh sach `tools` cho Claude Messages API (thu tu co dinh - giu cache prompt)."""
    return [{"name": c["ten"], "description": c["mo_ta"], "input_schema": c["schema"]}
            for c in CONG_CU]


def _gon(x: Any, gioi_han: int = GIOI_HAN_KY_TU) -> str:
    """JSON gon cho ngu canh LLM. Qua dai thi cat danh sach dai truoc, roi cat chuoi."""
    s = json.dumps(x, ensure_ascii=False, default=str, separators=(",", ":"))
    if len(s) <= gioi_han:
        return s

    def _cat(o, sau=0):
        if isinstance(o, dict):
            return {k: _cat(v, sau + 1) for k, v in o.items()}
        if isinstance(o, list):
            return [_cat(v, sau + 1) for v in o[:6]] + (["... %d muc nua" % (len(o) - 6)]
                                                        if len(o) > 6 else [])
        if isinstance(o, str) and len(o) > 600:
            return o[:600] + "..."
        return o
    s = json.dumps(_cat(x), ensure_ascii=False, default=str, separators=(",", ":"))
    return s if len(s) <= gioi_han else s[:gioi_han] + "...[cat]"


def goi(ten: str, dau_vao: dict | None = None, vong_id: int | None = None) -> dict:
    """Goi mot cong cu. Loi -> {'loi': ...} (tac tu doc duoc, khong vo vong lap)."""
    c = THEO_TEN.get(ten)
    if c is None:
        return {"loi": "khong co cong cu '%s'. Co: %s" % (ten, ", ".join(THEO_TEN))}
    dv = dict(dau_vao or {})
    thieu = [k for k in c["schema"].get("required", []) if k not in dv]
    if thieu:
        return {"loi": "thieu tham so bat buoc %s cho '%s'" % (thieu, ten)}
    la = [k for k in dv if k not in c["schema"]["properties"]]
    if la:
        return {"loi": "tham so khong co trong schema cua '%s': %s" % (ten, la)}
    t0 = time.time()
    try:
        kq = c["ham"](vong_id=vong_id, **dv)
    except TN.LoiKhaiBao as e:
        kq = {"trang_thai": "CHUA_DO_DUOC", "ly_do": "khai bao sai: %s" % e}
    except NDL.DoanNiemPhong as e:
        kq = {"loi": str(e)}
    except (ValueError, KeyError, TypeError) as e:
        kq = {"loi": "%s: %s" % (type(e).__name__, str(e)[:400])}
    except Exception as e:  # loi that cua engine: tra ve kem dau vet ngan
        kq = {"loi": "%s: %s" % (type(e).__name__, str(e)[:300]),
              "dau_vet": traceback.format_exc().splitlines()[-4:]}
    if isinstance(kq, dict):
        kq.setdefault("_giay", round(time.time() - t0, 2))
    return kq


def main(argv: list[str]) -> int:
    """`python -m nhan.nc_cong_cu` liet ke; `... <ten> '<json>'` hoac `... <ten> @file.json` goi."""
    if not argv or argv[0] in ("-h", "--help", "ds"):
        for c in CONG_CU:
            print("%-18s %s" % (c["ten"], c["mo_ta"][:150]))
        print("\nGoi: python b.py nc cc <ten> '<json>'   (hoac @file.json)")
        return 0
    ten = argv[0]
    tho = " ".join(argv[1:]).strip() or "{}"
    if tho.startswith("@"):
        tho = Path(tho[1:]).read_text(encoding="utf-8-sig")
    try:
        dv = json.loads(tho)
    except json.JSONDecodeError as e:
        print(json.dumps({"loi": "JSON dau vao hong: %s" % e}, ensure_ascii=False))
        return 2
    # `nc_tac_tu.chay_claude_code` dat NC_VONG_ID cho tien trinh `claude -p`, nen moi
    # thi nghiem Claude Code chay trong mot chu ky duoc gan dung chu ky do trong so tay.
    vid = os.environ.get("NC_VONG_ID")
    kq = goi(ten, dv, vong_id=int(vid) if vid and vid.isdigit() else None)
    if ten == "xem_so_tay" and "so_tay" in kq:
        print(kq["so_tay"])
    else:
        print(json.dumps(kq, ensure_ascii=False, indent=1, default=str))
    return 0 if not (isinstance(kq, dict) and kq.get("loi")) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
