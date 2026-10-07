# -*- coding: utf-8 -*-
"""do_thong_minh.py - DO THONG MINH (buoc S1, `tai_lieu/CHUYEN_BOT_SANG_TAI_SAN_KHAC.md` muc 9): tim tham so tot cua mot
bot luoi o thi truong MOI bang vai tram phep do thay vi ca vung luoi.

Cau hoi cua chu du an 04/10/2026: *"ta se do het cac thong so hay co cach nao do thong minh dua tren dac diem bot?"*.
Tra loi: KHONG do het. Cac buoc, theo thu tu:
  0  UNG VIEN   `dich_tham_so.cac_cach_dich` cho <= 9 tham so ung vien (moi cai la mot gia thuyet co ten)
  1  DO UNG VIEN do tung ung vien tren doan kham_pha (ham do do nguoi goi dua vao, module nay khong chay engine)
  2  LUOI THU GON quanh vai ung vien tot nhat: nhan buoc x {0,5 .. 2}, nhan ti le tp/buoc x {0,6 .. 1,6},
                nhan so tang x {0,5 .. 2} (mac dinh 5 x 3 x 3 = 45 o moi ung vien)
  3  CAO NGUYEN  diem cua mot o = TRUNG VI cua chinh no va cac o lien ke (+-1 theo tung truc): khong chon dinh nhon do nhieu
  4  THU HEP     luoi min 3 x 3 x 3 quanh o cao nguyen tot nhat, toi da 2 vong, dung khi cai thien duoi 3 %
Luon giu NGUYEN phong cach cua bot (che do, kieu lot, he so lot, he so buoc, tia lenh...): module chi doi KHOANG CACH va SO TANG,
vi chuyen mot bot sang thi truong khac la doi can chinh, khong doi co che (muon doi co che: dung the phuong phap khac).

Moi o do duoc la MOT PHEP THU: `ke_hoach` tinh san so phep thu toi da va dau van tay ke hoach (`plan_hash`) TRUOC khi do,
de ghi vao so tay nhu mot lan dang ky; `KetQuaTim.so_phep_thu` la so o that su da do (khong dem o trung).

Diem cang cao cang tot, -100 = chay tai khoan: module khong thay doi thang diem. Nguoi goi chiu trach nhiem de diem do
KHONG lot ra ngoai doan kham_pha (xac_nhan / niem_phong khong bao gio vao day).
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from dataclasses import dataclass, field, replace

import numpy as np

from nhan import dich_tham_so as DT
from nhan import luoi as LU

PHIEN_BAN = 1

#: luoi thu gon (nhan len gia tri cua ung vien)
HE_SO_BUOC = (0.5, 0.7, 1.0, 1.4, 2.0)
HE_SO_TP = (0.6, 1.0, 1.6)
HE_SO_TAM = (0.5, 1.0, 2.0)
#: so ung vien tot nhat duoc phong to thanh luoi thu gon, so vong thu hep toi da, he so cua luoi thu hep tung vong
SO_UNG_VIEN_TOT = 3
SO_VONG_THU_HEP = 2
HE_SO_THU_HEP = (1.25, 1.12)
#: dung thu hep khi diem cao nguyen tot nhat tang duoi muc nay (ti le tuong doi)
NGUONG_CAI_THIEN = 0.03
#: so o dua len tester nhieu nhat (muc 9.1 cua thiet ke)
TOI_DA_LEN_TESTER = 12
#: truong ThamSo la KHOANG CACH gia (pip): nhan cung mot he so khi doi co buoc (cung lop KC_BUOC / KC_TP cua dich_tham_so)
TRUONG_KHOANG_CACH = ("buoc", "tp", "cho_lui", "bien_cap", "buoc_tran")


def _khoa(ts) -> tuple:
    return dataclasses.astuple(ts)


def san_tu_thi_truong(tt) -> float:
    """San khoang cach (pip) cho mot thi truong: `max(2 A, 3 C)` - cung hai hang so voi `dich_tham_so` (phan giai va chi phi)."""
    return max(DT.NGUONG_PHAN_GIAI * tt.A, DT.SAN_CHI_PHI * tt.C) / tt.pip


def ap_san(ts, san_buoc: float = 0.0, san_tp: float = 0.0):
    """Nang buoc va tp len san (pip); khong dung vao truong nao khac. San <= 0 = khong ap."""
    nb = max(ts.buoc, san_buoc) if san_buoc > 0 else ts.buoc
    nt = max(ts.tp, san_tp) if san_tp > 0 else ts.tp
    if nb == ts.buoc and nt == ts.tp:
        return ts
    return replace(ts, buoc=nb, tp=nt)


def bien_the(goc, f_buoc: float, f_tp: float, f_tam: float, san_buoc: float = 0.0, san_tp: float = 0.0):
    """Mot o quanh `goc`: moi khoang cach x f_buoc (tp them x f_tp), so tang x f_tam (lam tron, >= 2), roi ap san."""
    if not all(math.isfinite(x) and x > 0 for x in (f_buoc, f_tp, f_tam)):
        raise ValueError("he so phai la so duong huu han")
    kw = {t: getattr(goc, t) * f_buoc for t in TRUONG_KHOANG_CACH}
    kw["tp"] = goc.tp * f_buoc * f_tp
    kw["tran_tang"] = int(min(DT.TOI_DA_TANG, max(2, round(goc.tran_tang * f_tam))))
    return ap_san(replace(goc, **kw), san_buoc, san_tp)


# ------------------------------------------------------------------------------------------------------ luoi cuc bo
@dataclass
class LuoiCucBo:
    """Luoi 3 truc (buoc, ti le tp/buoc, so tang) quanh mot o goc. `o[i][j][k]` la ThamSo; o bi ap san co the TRUNG nhau (dung chung diem)."""
    goc: object
    he_buoc: tuple
    he_tp: tuple
    he_tam: tuple
    o: list = field(default_factory=list, repr=False)

    def kich_thuoc(self) -> tuple:
        return (len(self.he_buoc), len(self.he_tp), len(self.he_tam))

    def cac_o(self) -> list:
        return [x for a in self.o for b in a for x in b]


def dung_luoi(goc, he_buoc=HE_SO_BUOC, he_tp=HE_SO_TP, he_tam=HE_SO_TAM, san_buoc: float = 0.0, san_tp: float = 0.0) -> LuoiCucBo:
    lc = LuoiCucBo(goc=goc, he_buoc=tuple(he_buoc), he_tp=tuple(he_tp), he_tam=tuple(he_tam))
    lc.o = [[[bien_the(goc, fb, ft, fm, san_buoc, san_tp) for fm in lc.he_tam] for ft in lc.he_tp] for fb in lc.he_buoc]
    return lc


def cao_nguyen_mang(d: np.ndarray) -> np.ndarray:
    """Diem cao nguyen cua mang 3 truc: trung vi cua o va cac o lien ke (+-1 theo tung truc, o nao ra ngoai hoac thieu thi bo).
    Thuan tuy, khong gi khac: mot dinh nhon bi hai ben hat xuong, mot doi rong giu nguyen do cao."""
    d = np.asarray(d, float)
    if d.ndim != 3:
        raise ValueError("can mang 3 truc")
    ra = np.full_like(d, np.nan)
    for idx in np.ndindex(*d.shape):
        if not np.isfinite(d[idx]):
            continue                        # o thieu (NaN, vd bi san loai) khong co diem va khong keo o khac
        v = [d[idx]]
        for ax in range(3):
            for dh in (-1, 1):
                j = list(idx)
                j[ax] += dh
                if 0 <= j[ax] < d.shape[ax] and np.isfinite(d[tuple(j)]):
                    v.append(d[tuple(j)])
        ra[idx] = float(np.median(v))
    return ra


# ------------------------------------------------------------------------------------------------------ ke hoach
def ke_hoach(so_ung_vien: int, so_tot: int = SO_UNG_VIEN_TOT, so_vong: int = SO_VONG_THU_HEP, he_buoc=HE_SO_BUOC, he_tp=HE_SO_TP,
             he_tam=HE_SO_TAM) -> dict:
    """So phep thu TOI DA va dau van tay ke hoach (tinh truoc khi do; thuc te thap hon vi o trung, o bi ap san trung nhau)."""
    o_luoi = len(he_buoc) * len(he_tp) * len(he_tam)
    o_thu_hep = 27
    toi_da = int(so_ung_vien) + int(so_tot) * o_luoi + int(so_vong) * o_thu_hep
    cau_hinh = {"phien_ban": PHIEN_BAN, "so_ung_vien": int(so_ung_vien), "so_tot": int(so_tot), "so_vong": int(so_vong),
                "he_buoc": list(he_buoc), "he_tp": list(he_tp), "he_tam": list(he_tam), "he_so_thu_hep": list(HE_SO_THU_HEP),
                "nguong_cai_thien": NGUONG_CAI_THIEN}
    vt = hashlib.sha256(json.dumps(cau_hinh, sort_keys=True).encode("ascii")).hexdigest()[:16]
    return {"so_phep_thu_toi_da": toi_da, "plan_hash": vt, "cau_hinh": cau_hinh}


# ------------------------------------------------------------------------------------------------------ ket qua
@dataclass
class KetQuaTim:
    """Ket qua `tim`: `top` = cac o xep theo diem cao nguyen (cao truoc); moi phan tu {tham_so, diem, cao_nguyen, nguon}."""
    top: list = field(default_factory=list)
    so_phep_thu: int = 0
    plan_hash: str = ""
    lich_su: list = field(default_factory=list)
    ly_do_dung: str = ""
    #: MOI o da do (khong trung): {tham_so, diem, nguon} - de kiem toan va de so chon dinh nhon (diem tho) voi chon cao nguyen
    cac_o: list = field(default_factory=list, repr=False)

    @property
    def tot_nhat(self):
        return self.top[0]["tham_so"] if self.top else None

    def to_dict(self) -> dict:
        return {"so_phep_thu": self.so_phep_thu, "plan_hash": self.plan_hash, "ly_do_dung": self.ly_do_dung, "lich_su": self.lich_su,
                "top": [{"tham_so": dataclasses.asdict(t["tham_so"]), "diem": t["diem"], "cao_nguyen": t["cao_nguyen"],
                         "nguon": t["nguon"]} for t in self.top]}


# ------------------------------------------------------------------------------------------------------ tim
def tim(ung_vien: list, danh_gia, san_buoc: float = 0.0, san_tp: float = 0.0, so_tot: int = SO_UNG_VIEN_TOT,
        so_vong: int = SO_VONG_THU_HEP, he_buoc=HE_SO_BUOC, he_tp=HE_SO_TP, he_tam=HE_SO_TAM, toi_da_top: int = TOI_DA_LEN_TESTER,
        ngan_sach: int | None = None) -> KetQuaTim:
    """Tim tham so tot quanh cac `ung_vien` (list `luoi.ThamSo`) bang `danh_gia(list[ThamSo]) -> list[float]`.

    `san_buoc`, `san_tp` (pip): ap cho moi o (chong di duoi nguong phan giai / chi phi). `ngan_sach`: so o do toi da (None = theo
    ke hoach); het ngan sach thi dung o buoc dang do (khong do dang do) va ghi ly do. Khong do lai o da do (cung ThamSo)."""
    if not ung_vien:
        raise ValueError("can it nhat mot ung vien")
    kh = ke_hoach(len(ung_vien), so_tot, so_vong, he_buoc, he_tp, he_tam)
    kq = KetQuaTim(plan_hash=kh["plan_hash"])
    tran = int(ngan_sach) if ngan_sach is not None else None
    da_do: dict = {}
    nguon: dict = {}
    mau: dict = {}

    def do(cac: list, nhan: str) -> bool:
        moi, thay = [], set()
        for ts in cac:
            k = _khoa(ts)
            if k not in da_do and k not in thay:
                thay.add(k)
                moi.append(ts)
        if tran is not None and len(da_do) + len(moi) > tran:
            return False
        if moi:
            diem = [float(x) for x in danh_gia(moi)]
            if len(diem) != len(moi):
                raise ValueError("danh_gia tra %d diem cho %d o" % (len(diem), len(moi)))
            for ts, x in zip(moi, diem):
                da_do[_khoa(ts)] = x
                nguon[_khoa(ts)] = nhan
                mau[_khoa(ts)] = ts
        return True

    def diem_cua(ts) -> float:
        return da_do[_khoa(ts)]

    # 0-1  ung vien
    uv = []
    thay = set()
    for ts in ung_vien:
        t2 = ap_san(ts, san_buoc, san_tp)
        if _khoa(t2) not in thay:
            thay.add(_khoa(t2))
            uv.append(t2)
    if not do(uv, "ung_vien"):
        kq.ly_do_dung = "het ngan sach ngay o buoc ung vien"
        kq.so_phep_thu = len(da_do)
        return kq
    kq.lich_su.append({"buoc": "ung_vien", "so_phep_thu": len(da_do), "tot_nhat": float(max(diem_cua(t) for t in uv))})

    # 2-3  luoi thu gon quanh cac ung vien tot nhat (khac nhau)
    xep = sorted(range(len(uv)), key=lambda i: (-diem_cua(uv[i]), i))
    goc_tot = [uv[i] for i in xep[:max(1, int(so_tot))]]
    luoi_tat_ca = []
    for g in goc_tot:
        lc = dung_luoi(g, he_buoc, he_tp, he_tam, san_buoc, san_tp)
        if not do(lc.cac_o(), "luoi_thu_gon"):
            kq.ly_do_dung = "het ngan sach o luoi thu gon"
            break
        luoi_tat_ca.append(lc)

    def cao_nguyen_cua(lc: LuoiCucBo) -> np.ndarray:
        d = np.empty(lc.kich_thuoc())
        for i, a in enumerate(lc.o):
            for j, b in enumerate(a):
                for k, ts in enumerate(b):
                    d[i, j, k] = diem_cua(ts)
        return cao_nguyen_mang(d)

    def tot_nhat_cao_nguyen() -> tuple:
        best = None
        for lc in luoi_tat_ca:
            cn = cao_nguyen_cua(lc)
            for (i, j, k), v in np.ndenumerate(cn):
                ts = lc.o[i][j][k]
                kk = (v, diem_cua(ts))
                if best is None or kk > best[0]:
                    best = (kk, ts)
        return best

    gan = tot_nhat_cao_nguyen() if luoi_tat_ca else None
    if gan is not None:
        kq.lich_su.append({"buoc": "luoi_thu_gon", "so_phep_thu": len(da_do), "tot_nhat_cao_nguyen": float(gan[0][0])})
    # 4  thu hep
    if gan is not None and not kq.ly_do_dung:
        for r in range(max(0, int(so_vong))):
            f = HE_SO_THU_HEP[min(r, len(HE_SO_THU_HEP) - 1)]
            lc = dung_luoi(gan[1], (1.0 / f, 1.0, f), (1.0 / f, 1.0, f), (1.0 / f, 1.0, f), san_buoc, san_tp)
            if not do(lc.cac_o(), "thu_hep_%d" % (r + 1)):
                kq.ly_do_dung = "het ngan sach o vong thu hep %d" % (r + 1)
                break
            luoi_tat_ca.append(lc)
            moi = tot_nhat_cao_nguyen()
            tang = (moi[0][0] - gan[0][0]) / max(abs(gan[0][0]), 1e-9)
            kq.lich_su.append({"buoc": "thu_hep_%d" % (r + 1), "so_phep_thu": len(da_do), "tot_nhat_cao_nguyen": float(moi[0][0])})
            gan_cu, gan = gan, moi
            if tang < NGUONG_CAI_THIEN:
                kq.ly_do_dung = "cai thien duoi %.0f%% o vong %d" % (NGUONG_CAI_THIEN * 100, r + 1)
                break
    if not kq.ly_do_dung:
        kq.ly_do_dung = "het ke hoach"

    # ket qua: moi o (khong trung) voi diem cao nguyen cua luoi chua no (lay gia tri tot nhat neu o nam o nhieu luoi), + ung vien
    tot = {}
    for lc in luoi_tat_ca:
        cn = cao_nguyen_cua(lc)
        for (i, j, k), v in np.ndenumerate(cn):
            ts = lc.o[i][j][k]
            if _khoa(ts) not in tot or v > tot[_khoa(ts)]["cao_nguyen"]:
                tot[_khoa(ts)] = {"tham_so": ts, "diem": diem_cua(ts), "cao_nguyen": float(v), "nguon": nguon[_khoa(ts)]}
    for ts in uv:
        if _khoa(ts) not in tot:
            tot[_khoa(ts)] = {"tham_so": ts, "diem": diem_cua(ts), "cao_nguyen": diem_cua(ts), "nguon": "ung_vien"}
    kq.top = sorted(tot.values(), key=lambda t: (-t["cao_nguyen"], -t["diem"]))[:max(1, int(toi_da_top))]
    kq.so_phep_thu = len(da_do)
    kq.cac_o = [{"tham_so": mau[k], "diem": da_do[k], "nguon": nguon[k]} for k in da_do]
    return kq
