# -*- coding: utf-8 -*-
"""Pham vi ap dung cua tung ho co che - va phep thu phan chung di kem.

VAN DE. Kho du lieu co 189 bang (171 FX, 12 chi so My, 6 vang) nhung
`kham_pha_theo_mau` chi quet 6 tai san dau tien. Khong gian tim kiem hep den
muc da can kiet: 346 gia thuyet, t_alpha trung vi -0,46.

CACH SAI de mo rong: quet ca 189 bang roi giu cai nao thang. Do la CAU TAI SAN.
Voi 189 x 3 khung x 3 diem luoi = 1.701 phep thu, cai tot nhat se dep du thi
truong khong co gi ca; va neu moi cai deu cham confirmation thi ngan sach FDR
chay sach trong mot luot.

CACH DUNG o day, va no la mot bai thu MANH HON chu khong yeu hon:

  Mot co che khong phai la "mot con so tren mot cap tien". No la mot khang dinh
  ve LOAI THI TRUONG. Neu "quay ve trung binh" that su ton tai vi co ben bi ep
  ban, thi no phai xuat hien tren CA NHOM tai san co co che do - va phai VANG
  MAT o nhom khong co. Vi vay:

    * khai truoc nhom NEN CHAY (`hop`) va nhom NEN HONG (`khong_hop`);
    * chay tren ca hai nhom;
    * ket luan chi duoc coi la co che khi nhom `hop` duong VA tach khoi nhom
      `khong_hop`.

  Mot co che "thang" deu ca o nhom da khai la nen hong thi do khong phai co
  che, do la fit - va phep thu nay bat duoc dieu do, con quet rong khong bat duoc.

  Ve thong ke, day la MOT gia thuyet (mot suat FDR) thay vi 1.701 suat.
"""
from __future__ import annotations

import numpy as np

from nhan import chi_phi as CP
from nhan import do_luong as DO
from nhan import du_lieu as DL
from nhan import mau as MAU
from nhan import mo_phong as MP

#: Loai tai san ma `chi_phi._loai_tai_san` sinh ra.
#: `hang_hoa` them 22/08 (dau, khi, dong, ngo, dau tuong - 5 chuoi Yahoo 26 nam).
#: Chua ho co che nao khai no la `hop`, nen no chi dong vai NHOM DOI CHUNG -
#: dung nhu vay: mot co che "quay ve trung binh cua chi so co phieu" ma cung
#: thang tren ngo va khi dot thi do khong phai co che.
LOAI = ("fx", "chi_so_my", "vang", "hang_hoa")

#: Khai bao TRUOC: ho co che nao song o loai thi truong nao.
#: Moi dong deu co ly do co che, khong phai ket qua backtest.
PHAM_VI: dict[str, dict] = {
    "quay_ve_trung_binh": {
        "hop": ["chi_so_my"],
        "khong_hop": ["fx"],
        "ly_do": "Can mot ben bi ep ban theo lich trinh (quy vol-target, margin "
                 "call) roi mua lai. Chi so co phieu co nhom do; ty gia cheo thi "
                 "khong ai bi ep dong vi the vi ly do phi gia.",
    },
    "xu_huong": {
        "hop": ["chi_so_my", "vang"],
        "khong_hop": ["fx"],
        "ly_do": "Can drift ben vung song qua chi phi. Chi so co phieu co drift "
                 "loi nhuan doanh nghiep; ty gia cheo la tro choi tong bang khong.",
    },
    "pha_vo": {
        "khung": "H4",
        "hop": ["chi_so_my", "vang"],
        "khong_hop": ["fx"],
        "ly_do": "Can bien dong gian no va nguoi mua duoi. Thi truong co san khop "
                 "tap trung moi co hieu ung do.",
    },
    "lich": {
        "hop": ["chi_so_my"],
        "khong_hop": ["vang"],
        "ly_do": "Dong tien theo lich la dong tien dinh che: luong huu cuoi thang, "
                 "tai can bang quy. Vang khong co lich dong tien nhu vay.",
    },
    "phien": {
        "khung": "H4",
        "hop": ["chi_so_my", "vang"],
        "khong_hop": ["fx"],
        "ly_do": "Can phien giao dich phan biet duoc (mo/dong cua san). FX chay "
                 "lien tuc 24/5 nen ranh gioi phien mo ho.",
    },
    "dong_tien": {
        "hop": ["chi_so_my"],
        "khong_hop": ["fx"],
        "ly_do": "ETF don bay, quy tuong ho, mua lai co phieu quy - deu la dong "
                 "tien cua thi truong co phieu.",
    },
    "bien_dong": {
        "hop": ["chi_so_my"],
        "khong_hop": ["fx"],
        "ly_do": "Phi bao hiem bien dong ton tai o noi co thi truong quyen chon "
                 "sau va nguoi mua bao hiem co he thong.",
    },
    "vi_mo": {
        "hop": ["fx", "vang"],
        "khong_hop": [],
        "ly_do": "Cong bo vi mo (lai suat, viec lam, lam phat) dinh gia lai ky "
                 "vong lai suat, va do chinh la thu quyet dinh ty gia lan gia "
                 "vang. Khong khai nhom doi chung vi gan nhu moi lop tai san "
                 "deu phan ung voi vi mo o muc do nao do.",
    },
}

#: Khung mac dinh cua phep thu. D1 vi kho co chuoi chi so 25-56 nam o khung do.
KHUNG_MAC_DINH = "D1"


def khung_cua_ho(ho: str) -> str:
    """Khung phai do MOT ho co che, khai theo CO CHE chu khong theo tien.

    Mot co che phien (`phien`) hay pha vo trong ngay (`pha_vo`) KHONG DO DUOC
    tren bar ngay: bar ngay khong co gio mo cua, va mot lan pha vo trong ngay
    hien thanh mot cai bong. Do that 22/08: chay ca 15 mau o D1 thi 5 mau thuoc
    hai ho nay deu tra `CHUA_DU_MAU` - khong phai vi thi truong rong ma vi cau
    hoi bi dat sai khung.
    """
    return (PHAM_VI.get(ho) or {}).get("khung") or KHUNG_MAC_DINH


#: Toi da bao nhieu tai san moi nhom trong mot lan kiem, de mot luot con ket thuc.
TRAN_MOI_NHOM = 12
#: Toi thieu bao nhieu tai san moi nhom thi ket luan moi co nghia.
TOI_THIEU_MOI_NHOM = 3
#: Nhom `hop` phai vuot nhom `khong_hop` it nhat bay nhieu (don vi: Sharpe).
CACH_BIET_TOI_THIEU = 0.20


def loai_cua(ma: str) -> str:
    return CP._loai_tai_san(ma)


def tai_san_theo_loai(cac_loai: list[str], tran: int = TRAN_MOI_NHOM,
                      kho: list[str] | None = None) -> list[str]:
    """Tai san trong kho thuoc cac loai da cho, LAY TRAI DEU va tat dinh.

    Khong duoc lay `[:tran]` cua danh sach da sap xep: 171 cap FX sap theo ten
    thi 12 cai dau deu la AUD... (AUDCAD, AUDCHF, AUDDKK, ...). Do la mot ro
    cac cap AUD, khong phai mot mau dai dien cua lop FX - va nhom doi chung
    khong dai dien thi phep thu phan chung mat y nghia.
    """
    ds = sorted(kho if kho is not None else DL.kho())
    hop_le = [m for m in ds if loai_cua(m) in cac_loai]
    if tran <= 0 or len(hop_le) <= tran:
        return hop_le
    buoc = len(hop_le) / tran
    return [hop_le[int(i * buoc)] for i in range(tran)]


def _do_mot(ten_mau: str, ma: str, khung: str, tham_so: dict,
            tren_holdout: bool = True) -> dict | None:
    """Sharpe cua mot mau tren mot tai san. None = khong do duoc."""
    try:
        df = DL.nap(ma, khung)
        if DL.nguon_tai_san(ma) == "ngoai":
            # Cat phan open bia TRUOC khi chia. Nhom doi chung do tren gia bia
            # thi cach biet giua hai nhom la cach biet giua hai chat luong du
            # lieu, khong phai giua hai loai thi truong.
            df = DL.cat_theo_chat_luong(df, ma)[0]
    except Exception:
        return None
    train, hold = DL.hai_nua(df, 0.6)
    phan = hold if tren_holdout else train
    if len(phan) < 500:
        return None
    try:
        cp = CP.tu_du_lieu(ma, phan)
        kq = MP.chay(phan, MAU.sinh(ten_mau, phan, tham_so), cp, ma=ma, khung=khung)
    except Exception:
        return None
    if kq.so_lenh < 20:
        return None
    cs = DO.chi_so(kq.loi, phan.index, kq.vi_the)
    return {"tai_san": ma, "loai": loai_cua(ma), "so_lenh": kq.so_lenh,
            "sharpe": cs.get("sharpe"), "tong_lai_pct": cs.get("tong_lai_pct")}


def kiem_pham_vi(ten_mau: str, khung: str | None = None, tham_so: dict | None = None,
                 tran: int = TRAN_MOI_NHOM, kho: list[str] | None = None,
                 do_ham=None) -> dict:
    """Chay mot mau tren nhom NEN CHAY va nhom NEN HONG, roi phan xu.

    Day la MOT gia thuyet: "co che nay song o loai thi truong X va vang mat o
    loai Y". Khong phai N gia thuyet cho N tai san.
    """
    if ten_mau not in MAU.MAU:
        return {"mau": ten_mau, "loi": "khong co trong thu vien mau"}
    m = MAU.MAU[ten_mau]
    ho = m.get("ho") or "khac"
    khai = PHAM_VI.get(ho)
    if not khai:
        return {"mau": ten_mau, "ho": ho, "loi": f"ho '{ho}' chua khai pham vi"}

    if khung is None:
        khung = khung_cua_ho(ho)
    if kho is None:
        kho = kho_du_bar(khung)
    tham_so = tham_so if tham_so is not None else ((m.get("luoi") or [{}])[0])
    nhom_hop = tai_san_theo_loai(khai["hop"], tran, kho)
    nhom_khong = tai_san_theo_loai(khai["khong_hop"], tran, kho)

    # `do_ham` tiem duoc de test chay tren tai san gia, khong phai kho that.
    do = do_ham or _do_mot
    do_hop = [r for r in (do(ten_mau, ma, khung, tham_so) for ma in nhom_hop) if r]
    do_khong = [r for r in (do(ten_mau, ma, khung, tham_so) for ma in nhom_khong) if r]

    ra = {
        "mau": ten_mau, "ho": ho, "khung": khung, "tham_so": tham_so,
        "ly_do_pham_vi": khai["ly_do"],
        "nhom_hop": {"loai": khai["hop"], "n": len(do_hop), "chi_tiet": do_hop},
        "nhom_khong_hop": {"loai": khai["khong_hop"], "n": len(do_khong),
                           "chi_tiet": do_khong},
    }

    if len(do_hop) < TOI_THIEU_MOI_NHOM:
        ra["ket_luan"] = "CHUA_DU_MAU"
        ra["ly_do"] = (f"chi do duoc {len(do_hop)} tai san o nhom hop, "
                       f"can >= {TOI_THIEU_MOI_NHOM}")
        return ra

    tv_hop = float(np.median([r["sharpe"] or 0.0 for r in do_hop]))
    ra["sharpe_trung_vi_hop"] = round(tv_hop, 4)

    if not khai["khong_hop"]:
        ra["sharpe_trung_vi_khong_hop"] = None
        ra["cach_biet"] = None
        ra["ket_luan"] = "CO_CO_CHE" if tv_hop > 0 else "KHONG_CO_CO_CHE"
        ra["ly_do"] = "khong khai nhom doi chung - chi ket luan duoc mot chieu"
        return ra

    if len(do_khong) < TOI_THIEU_MOI_NHOM:
        ra["ket_luan"] = "CHUA_DU_MAU"
        ra["ly_do"] = f"nhom doi chung chi co {len(do_khong)} tai san"
        return ra

    tv_khong = float(np.median([r["sharpe"] or 0.0 for r in do_khong]))
    cach_biet = tv_hop - tv_khong
    ra["sharpe_trung_vi_khong_hop"] = round(tv_khong, 4)
    ra["cach_biet"] = round(cach_biet, 4)

    if tv_hop <= 0:
        ra["ket_luan"] = "KHONG_CO_CO_CHE"
        ra["ly_do"] = f"nhom hop khong duong (trung vi Sharpe {tv_hop:.3f})"
    elif cach_biet < CACH_BIET_TOI_THIEU:
        # Day la phat hien quan trong nhat cua bai thu nay.
        ra["ket_luan"] = "KHONG_PHAN_BIET"
        ra["ly_do"] = (
            f"chay tot ca o nhom da khai la NEN HONG (hop {tv_hop:.3f} vs "
            f"khong_hop {tv_khong:.3f}, cach biet {cach_biet:.3f} < "
            f"{CACH_BIET_TOI_THIEU}). Mot co che dung o moi loai thi truong "
            "thuong la mot dac tinh chung cua gia, khong phai co che.")
    else:
        ra["ket_luan"] = "CO_CO_CHE"
        ra["ly_do"] = (f"nhom hop {tv_hop:.3f} vuot nhom doi chung "
                       f"{tv_khong:.3f} dung {cach_biet:.3f}")
    return ra


def kho_du_bar(khung: str = "D1", toi_thieu: int = 1500) -> list[str]:
    """Chi nhung tai san THAT SU co du bar SACH o khung nay.

    Kho co 189 bang nhung chi ~20 bang du bar o H4; so 189 la ke trong. Lay
    nham ca ke trong thi nhom doi chung day tai san khong do duoc va phep thu
    tra ve CHUA_DU_MAU ma khong noi vi sao.

    Ba bo loc, moi bo loc mot ly do:
      * `du_ohlc` - VIX chi co cot `vix_close`, ETF_* chi co `close`. Loc o muc
        SCHEMA nen khong ton mot lan nap nao.
      * khung goc - hoi H4 tren bang D1 la yeu cau noi suy nguoc; `DL.nap` nem
        ValueError va truoc day moi bang D1 deu di qua duong ngoai le do.
      * so bar SAU KHI CAT phan open bia - dem bar tho thi YH_FTSE100 (10.764
        bar, 34/43 nam la gia bia) van "du bar".

    Mac dinh doi tu H4 sang **D1** ngay 22/08: o H4 chi co ~20 bang du bar va
    het la FX broker 13 nam, nen nhom doi chung `chi_so_my` khong bao gio du 3
    tai san -> moi phep thu phan chung tra CHUA_DU_MAU. O D1 kho co ca chuoi
    chi so 25-56 nam.
    """
    ra = []
    for m, v in sorted(DL.bang_ohlc().items()):      # da loai futures
        # `khung_min` chu khong phai `khung_goc`: mot ma co the co ban M5 ngan
        # va ban D1 dai (XM_US500CASH). Hoi ban to nhat thi loai nham ca ma.
        kg = v.get("khung_min", v["khung_goc"])
        if kg not in DL.PHUT_KHUNG:
            continue
        if DL.PHUT_KHUNG[kg] > DL.PHUT_KHUNG[khung]:
            continue
        try:
            df = DL.nap(m, khung)
            if v["nguon"] == "ngoai":
                df = DL.cat_theo_chat_luong(df, m)[0]
            if len(df) >= toi_thieu:
                ra.append(m)
        except Exception:
            continue
    return ra


def quet_pham_vi(khung: str = "D1", cac_mau: list[str] | None = None,
                 tran: int = TRAN_MOI_NHOM, kho: list[str] | None = None) -> list[dict]:
    """Chay `kiem_pham_vi` cho nhieu mau, xep theo cach biet giam dan."""
    ten = cac_mau if cac_mau is not None else sorted(MAU.MAU)
    dung = kho if kho is not None else kho_du_bar(khung)
    ra = [kiem_pham_vi(t, khung, tran=tran, kho=dung) for t in ten]
    return sorted(ra, key=lambda r: -(r.get("cach_biet") or -9))
