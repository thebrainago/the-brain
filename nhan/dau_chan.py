# -*- coding: utf-8 -*-
"""dau_chan.py - LUAN NGUOC KIEU CHIEN LUOC tu DAU CHAN CONG KHAI.

Chu du an 05/09/2026: *"xay bo loc luan nguoc chien luoc cua trader top"*, va
kem theo mot doi quan diem: *"chap nhan he thong dca, chap nhan DD cao hon. Con
neu cu tim he single shot ma dat duoc cac tieu chi thi cac to chuc tai chinh ho
da lam truoc roi"*.

LAP LUAN DO DUNG, VA DUNG O CHO CU THE - ghi ra day vi no quyet dinh ca cach
cham diem ben duoi. To chuc tai chinh bi hai rang buoc ma tai khoan ca nhan
KHONG bi:

  1. **Suc chua.** Mot quy khong trien khai duoc chien luoc chi om noi vai chuc
     nghin dollar rui ro. Ta thi duoc.
  2. **Nguong sut giam.** -60% la ket thuc mot quy (nguoi ta rut von), nhung
     khong ket thuc mot tai khoan ca nhan da biet truoc dieu do.

Nen goc con lai la giao cua HAI dieu do - va do dung la noi lop DCA/luoi song.

NHUNG "chap nhan DD cao" KHONG PHAI LA MOT EDGE, va cho nay phai noi thang:
tran loi suat `0,5 * Sharpe^2` van rang buoc (xem bo nho `tran-lai-suat-la-sharpe`).
Chap nhan DD cao chi cho phep DUNG DON BAY CAO HON tren cung mot edge, no khong
tao ra edge. Cai lop DCA that su mua duoc la mot **HINH DANG LOI SUAT KHAC**:
ty le thang cao, lai nho, thua hiem va rat lon. Voi hinh dang do:

    Sharpe KHONG phai thuoc do dung. Cau hoi dung la
    **SONG BAO LAU** va **RUT KIP KHONG**.

Nen module nay khong cham Sharpe. No phan LOAI kieu chien luoc tu dau chan,
roi moi kieu cham bang thuoc do cua chinh kieu do.

DAU VAO la thu KHONG AI GIAU DUOC. Nguoi ban tin hieu giau duoc LUAT, nhung
buoc phai cong khai duong von, muc tai va MFE/MAE de nguoi ta dam mua.

BON DAC TRUNG DO DUOC, khai bao TRUOC khi chay (khong duoc them sau khi nhin
ket qua - do la fit lai bo phan loai tren chinh mau dang phan loai):

  `nhoi_khi_lo`   Spearman(muc tai, do sau lo treo) tren cac diem CO vi the.
                  Duong manh = **cang lo cang nhoi them** = chu ky DCA/luoi.
                  Day la dac trung PHAN BIET manh nhat, vi no doc duoc y do:
                  mot he cat lo khong the co tuong quan duong o day.
  `bac_tai`       So buoc TANG tai roi rac trong mot doan giu vi the (trung vi).
                  >= 2 = co nhoi them lenh, khong phai vao mot phat.
  `lo_treo_dinh`  max (balance - equity)/balance. Suc chiu lo treo.
  `cat_sach`      trung vi |MAE|/MFE theo ngay. > 1 = de lo chay hon lai.

Ba dac trung phu lay thang tu trang: `giu_phut`, `thang_pct`, `so_lenh`.

LUAT PHAN LOAI - khai bao truoc, xet theo THU TU, dung o cai dau tien khop:

  1. `luoi_dca`  (nhoi_khi_lo > 0,30 HOAC bac_tai >= 2) VA lo_treo_dinh >= 0,10
                 VA thang_pct >= 60
  2. `gong_lo`   cat_sach > 1,2 VA lo_treo_dinh >= 0,10   (giu lo nhung KHONG nhoi)
  3. `scalp`     giu_phut <= 120 VA cat_sach <= 1,0
  4. `xu_huong`  giu_phut >= 1440 VA cat_sach <= 1,0
  5. `khong_ro`

THIEN LECH SONG SOT LA TOAN PHAN va khong khu duoc: bang xep hang chi liet ke
tai khoan CON SONG. Nen ket qua doc duoc la *"kieu nay ton tai va do duoc"*,
KHONG PHAI *"kieu nay lam ra tien"*. Muon noi ve ra tien thi phai co ca nhung
tai khoan da chet, va cai do khong cong khai.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

#: Nguong cua luat phan loai. De o day de doc duoc, KHONG de chinh cho vua mau.
NHOI_KHI_LO = 0.30
BAC_TAI = 2
LO_TREO = 0.10
THANG_PCT = 60.0
CAT_SACH_GONG = 1.2
GIU_SCALP = 120.0
GIU_XU_HUONG = 1440.0

KIEU = ("luoi_dca", "gong_lo", "scalp", "xu_huong", "khong_ro")


def _ghep(von: np.ndarray, tai: np.ndarray) -> pd.DataFrame:
    """(ts,balance,equity) + (ts,muc_tai) -> mot bang theo thoi gian.

    Hai chuoi lay mau KHAC nhau (842 vs 713 diem tren #2359404) nen phai ghep
    theo moc gan nhat, khong duoc gia dinh cung do dai.
    """
    v = pd.DataFrame({"ts": von[:, 0], "bal": von[:, 1],
                      "eq": von[:, 2]}).sort_values("ts")
    t = pd.DataFrame({"ts": tai[:, 0], "tai": tai[:, 1]}).sort_values("ts")
    j = pd.merge_asof(t, v, on="ts", direction="nearest", tolerance=3600).dropna()
    j["lo_treo"] = (j["bal"] - j["eq"]) / j["bal"]
    return j


def _bac_tai(tai: np.ndarray) -> float | None:
    """Trung vi so BUOC TANG tai trong mot doan giu vi the lien tuc.

    Vao mot phat roi giu -> 1 buoc. Nhoi them theo luoi/DCA -> nhieu buoc.
    Chi dem buoc tang DANG KE (>5% muc tai hien tai) de khong dem nhieu lam tron.
    """
    doan, cur = [], []
    for x in tai:
        if x > 0:
            cur.append(x)
        elif cur:
            doan.append(cur)
            cur = []
    if cur:
        doan.append(cur)
    bac = []
    for d in doan:
        if len(d) < 2:
            bac.append(1)
            continue
        n = 1
        for i in range(1, len(d)):
            if d[i] > d[i - 1] * 1.05:
                n += 1
        bac.append(n)
    return float(np.median(bac)) if bac else None


def dac_trung(von: np.ndarray | None, tai: np.ndarray | None,
              loi_suat_lenh: np.ndarray | None) -> dict:
    """Bon dac trung do duoc tu dau chan. Thieu du lieu -> None, KHONG phai 0."""
    ra = {"nhoi_khi_lo": None, "bac_tai": None, "lo_treo_dinh": None,
          "lech_trai": None, "so_diem_tai": None, "song_ngay": None}
    if tai is not None and len(tai) > 5:
        ra["bac_tai"] = _bac_tai(tai[:, 1])
        ra["so_diem_tai"] = int((tai[:, 1] > 0).sum())
    if von is not None and len(von) > 5:
        lo = (von[:, 1] - von[:, 2]) / np.maximum(von[:, 1], 1e-9)
        ra["lo_treo_dinh"] = float(np.nanmax(lo))
        ra["song_ngay"] = float((von[-1, 0] - von[0, 0]) / 86400.0)
    if von is not None and tai is not None and len(von) > 5 and len(tai) > 5:
        j = _ghep(von, tai)
        co = j[j["tai"] > 0]
        if len(co) >= 20 and co["tai"].std() > 0 and co["lo_treo"].std() > 0:
            ra["nhoi_khi_lo"] = float(co["tai"].corr(co["lo_treo"], method="spearman"))
    if loi_suat_lenh is not None and len(loi_suat_lenh) >= 30:
        r = np.asarray(loi_suat_lenh, float)
        sd = r.std()
        if sd > 0:
            ra["lech_trai"] = float(((r - r.mean()) ** 3).mean() / sd ** 3)
    return ra


def phan_loai(d: dict) -> tuple[str, str]:
    """(kieu, ly do). Xet theo THU TU khai bao, dung o cai dau tien khop."""
    nhoi = d.get("nhoi_khi_lo")
    bac = d.get("bac_tai")
    treo = d.get("lo_treo_dinh")
    cat = d.get("cat_sach")
    giu = d.get("giu_phut")
    thang = d.get("thang_pct")

    co_nhoi = (nhoi is not None and nhoi > NHOI_KHI_LO) or \
              (bac is not None and bac >= BAC_TAI)
    du_treo = treo is not None and treo >= LO_TREO
    if co_nhoi and du_treo and thang is not None and thang >= THANG_PCT:
        return "luoi_dca", ("nhoi_khi_lo=%s bac_tai=%s lo_treo=%.2f thang=%.0f%%"
                            % (_r(nhoi), _r(bac), treo, thang))
    if cat is not None and cat > CAT_SACH_GONG and du_treo:
        return "gong_lo", "cat_sach=%.2f lo_treo=%.2f (giu lo, khong nhoi)" % (cat, treo)
    if giu is not None and giu <= GIU_SCALP and cat is not None and cat <= 1.0:
        return "scalp", "giu=%.0f phut cat_sach=%.2f" % (giu, cat)
    if giu is not None and giu >= GIU_XU_HUONG and cat is not None and cat <= 1.0:
        return "xu_huong", "giu=%.0f phut cat_sach=%.2f" % (giu, cat)
    thieu = [k for k in ("nhoi_khi_lo", "lo_treo_dinh", "cat_sach", "giu_phut")
             if d.get(k) is None]
    return "khong_ro", ("thieu: " + ",".join(thieu) if thieu else "khong khop luat nao")


def _r(x):
    return "-" if x is None else round(x, 3)
