# -*- coding: utf-8 -*-
"""GOP LOP - kiem dinh MOT co che tren CA MOT LOP TAI SAN, ton MOT suat FDR.

VI SAO PHAI CO MODULE NAY. Do that ngay 22/08/2026, sau khi be mat kham pha da
duoc mo rong va cong kha thi da duoc lap:

    * nguong phat hien tot nhat cua MOT tai san don le: 0,535 (YH_NASDAQ D1)
      o lan nghien cuu, 0,590 (USDJPY D1) o lan giao dich;
    * co che DUY NHAT qua duoc phep thu phan chung (`nhan/pham_vi.py`) la
      `ibs_bat_day`, voi Sharpe trung vi tren lop chi so co phieu la **0,313**.

Hai con so do khong gap nhau. Mot vong kham pha day du dang ky dung 3 gia thuyet
va chan 292 ung vien vi thieu luc - dung, vi tren MOT tai san thi 0,313 that su
khong phan biet duoc voi 0. Neu chi co duong nay thi co che that ton tai van se
khong bao gio duoc chung nhan, va he se bao "khong tim thay gi" mai mai.

DUONG RA, va no la duong DUY NHAT khong phai noi long nguong:

    Gop k tai san CUNG LOP cho CUNG mot co che. Nhieu doc lap giam theo
    sqrt(k_hieu_dung), tin hieu thi khong. `nhan/do_luc.py` da do rho that:
        chi so My  k= 4  rho 0,447 -> k hieu dung 1,71 -> loi the 1,31x
        FX         k=11  rho 0,218 -> k hieu dung 3,46 -> loi the 1,86x
        tat ca     k=20  rho 0,203 -> k hieu dung 4,12 -> loi the 2,03x

    Ve THONG KE day la MOT gia thuyet ("co che X song o lop thi truong Y"),
    khong phai k gia thuyet. No ton DUNG MOT suat FDR.

BON BAT BIEN, moi cai chan mot cach tu lua da biet:

1. **Trong so KHONG duoc nhin ve tuong lai.** Moi moc thoi gian chia deu cho
   nhung tai san CO DU LIEU TAI MOC DO. Chia deu cho "cac tai san co mat trong
   ca ky" la loi song sot: no biet truoc cai nao se ton tai.

2. **Moc so sanh la mua-giu CUA CHINH RO DO**, gop cung cach, co phi. Mot danh
   muc khong hon mua-giu thi no khong phai thanh tuu (`danh_muc.py` nguyen tac 3).

3. **Do tin chi phi cua ro = do tin TE NHAT trong ro.** Mot ro co mot chan la
   chuoi khong mua duoc thi ca ro khong mua duoc. Khong duoc lay trung binh.

4. **Phai co nhom doi chung.** Gop lam tang luc cho CA co che that lan bay:
   neu ro `khong_hop` cung sang len tuong duong thi thu vua do duoc la mot dac
   tinh chung cua gia, khong phai co che. Vi vay `xet_gop` luon do ca hai ro va
   bao `cach_biet`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhan import chi_phi as CP
from nhan import cong as CONG
from nhan import do_luong as DO
from nhan import du_lieu as DL
from nhan import mau as MAU
from nhan import mo_phong as MP
from nhan import pham_vi as PV
from nhan import so as SO

#: Toi thieu bao nhieu chan thi mot ro moi co nghia. Duoi muc nay thi "gop"
#: chi la doi ten cua mot phep thu don le.
TOI_THIEU_CHAN = 3
#: Toi da bao nhieu chan. Khong phai gioi han hieu nang: them chan thu 20 gan
#: nhu khong them luc (rho 0,2 -> k hieu dung 4,1) nhung lam thoi gian chay
#: tuyen tinh, va lam ro phu thuoc vao nhung tai san rat mong.
TOI_DA_CHAN = 12
#: Chan phai co it nhat bay nhieu bar holdout moi duoc tinh vao ro.
TOI_THIEU_BAR = 400

#: Thang do chinh xac de do MDE cua RO. MIN hon `do_luc.THANG_P` o vung sat 0,5.
#:
#: Ly do la do phan giai, va no da lam sai so do dau tien: tren mot tai san don
#: le, buoc 0,52 -> 0,54 doi Sharpe khoang 0,3; tren ro 12 chan, cung buoc do
#: doi Sharpe tu 0,374 len 1,587. Nguong bao ra la Sharpe cua diem luoi DAU
#: TIEN vuot cong, nen luoi tho lam nguong bi THOI LEN 4 lan - va mot MDE bi
#: thoi len se lam moi ket luan am tinh trong ve "khong the ket luan" trong khi
#: that ra ket luan duoc.
THANG_P_GOP = (0.500, 0.505, 0.510, 0.5125, 0.515, 0.5175, 0.520, 0.5225,
               0.525, 0.5275, 0.530, 0.535, 0.540, 0.550, 0.560, 0.580, 0.600)


class _Chan:
    """Mot chan cua ro: chuoi loi suat rong cua co che tren mot tai san."""

    __slots__ = ("ma", "khung", "loi", "loi_bh", "vi_the", "index", "so_lenh",
                 "do_tin", "che_do", "phoi_nhiem")

    def __init__(self, ma, khung, loi, loi_bh, index, so_lenh, do_tin, phoi_nhiem,
                 vi_the=None):
        self.ma, self.khung = ma, khung
        self.loi, self.loi_bh, self.index = loi, loi_bh, index
        self.vi_the = vi_the if vi_the is not None else np.zeros(len(loi))
        self.so_lenh, self.do_tin, self.phoi_nhiem = so_lenh, do_tin, phoi_nhiem


def _lich_holdout(ma: str, khung: str):
    """Index holdout cua mot tai san. Chi doc LICH, khong chay backtest nao."""
    try:
        df = DL.nap(ma, khung)
        if DL.nguon_tai_san(ma) == "ngoai":
            df = DL.cat_theo_chat_luong(df, ma)[0]
        h = DL.hai_nua(df, 0.6)[1]
        if len(h) < TOI_THIEU_BAR:
            return None
        return DL.chuan_hoa_index(h.index)
    except Exception:
        return None


def chon_chan(cac_ma: list[str], khung: str, tran: int = TOI_DA_CHAN) -> dict:
    """Chon chan cho ro theo CONG SUAT TINH TRUOC TU LICH DU LIEU.

    VI SAO KHONG DUNG `pham_vi.tai_san_theo_loai`: ham do lay trai deu theo TEN
    de nhom doi chung khoi thanh mot ro AUD - dung cho phep thu phan chung,
    nhung sai cho ro gop. Do that 22/08 tren lop chi so co phieu:

        lay trai deu  -> cua so 2012-09..2026-08 (14,0 nam), tb 6,81 chan
        chon theo lich -> cua so 2004-05..2026-08 (22,3 nam), tb 5,86 chan

    Luc cua phep kiem ty le 1/sqrt(T x k_hieu_dung), nen "so BAR-CHAN" (tong so
    bar co mat cua moi chan trong cua so chung) la dai luong phai toi da hoa:
    95,3 nghin so voi 130,7 nghin - hon 1,37 lan.

    **Tieu chi nay chi doc LICH CO DU LIEU, khong doc mot con so loi suat nao**,
    nen no khong phai la chon theo ket qua. Do la dieu kien de no hop le.

    Cach chon: xep ung vien theo moc bat dau holdout (som truoc), roi quet k tu
    `TOI_THIEU_CHAN` den `tran`, moi k tinh so bar-chan cua tap k ung vien som
    nhat, lay k tot nhat. Tat dinh.
    """
    lich = {}
    for m in cac_ma:
        idx = _lich_holdout(m, khung)
        if idx is not None:
            lich[m] = idx
    if len(lich) < TOI_THIEU_CHAN:
        return {"chan": list(lich), "ly_do": f"chi {len(lich)} ung vien co holdout"}

    def _diem(tap):
        """(so bar-chan, so moc) cua mot tap chan. Chi doc lich."""
        bang = pd.concat({m: pd.Series(1, index=lich[m]) for m in tap},
                         axis=1, sort=True)
        du = bang.notna().sum(axis=1) >= TOI_THIEU_CHAN
        n = int(du.sum())
        return (int(bang[du].notna().sum().sum()) if n else 0), n

    # THAM LAM THEO DONG GOP BIEN, khong phai theo moc bat dau.
    #
    # Xep theo moc bat dau roi lay k dau tien nghe hop ly nhung om ca CHAN CHET:
    # holdout cua SP500 la 1948-1959 (vi `cat_theo_chat_luong` giu doan sach DAI
    # NHAT, ma cua SP500 la 1927-1959 chu khong phai 2007+), nen no khong chong
    # lan mot ngay nao voi cac chan hien dai - chiem mot suat va dong gop 0.
    # Tham lam theo dong gop bien khong the chon nham nhu vay.
    tot, quet = None, []
    chon: list[str] = []
    con = sorted(lich)
    while con and len(chon) < min(tran, len(lich)):
        tot_buoc = None
        for m in con:
            tap = chon + [m]
            if len(tap) < TOI_THIEU_CHAN:
                # Chua du chan de dinh nghia cua so -> uu tien chan phu rong.
                d = (len(lich[m]), 0)
            else:
                d = _diem(tap)
            if tot_buoc is None or d[0] > tot_buoc[1][0]:
                tot_buoc = (m, d)
        if tot_buoc is None:
            break
        m, (bar_chan, so_moc) = tot_buoc
        chon.append(m)
        con.remove(m)
        if len(chon) >= TOI_THIEU_CHAN and so_moc >= TOI_THIEU_BAR:
            quet.append({"k": len(chon), "so_moc": so_moc, "bar_chan": bar_chan})
            if tot is None or bar_chan > tot["bar_chan"]:
                tot = {"k": len(chon), "chan": list(chon),
                       "bar_chan": bar_chan, "so_moc": so_moc}
    if tot is None:
        return {"chan": sorted(lich, key=lambda m: lich[m][0])[:tran],
                "ly_do": "khong tap nao du moc, lay theo moc bat dau"}
    return {"chan": sorted(tot["chan"]), "k": tot["k"],
            "bar_chan": tot["bar_chan"], "so_moc": tot["so_moc"], "quet": quet}


def _mot_chan(ten_mau: str, ma: str, khung: str, tham_so: dict,
              tren_holdout: bool = True) -> _Chan | None:
    """Chay co che tren mot tai san, tra chuoi loi suat rong + mua-giu cua no."""
    try:
        df = DL.nap(ma, khung)
        if DL.nguon_tai_san(ma) == "ngoai":
            df = DL.cat_theo_chat_luong(df, ma)[0]
    except Exception:
        return None
    train, hold = DL.hai_nua(df, 0.6)
    phan = hold if tren_holdout else train
    if len(phan) < TOI_THIEU_BAR:
        return None
    try:
        cp = CP.tu_du_lieu(ma, phan)
        kq = MP.chay(phan, MAU.sinh(ten_mau, phan, tham_so), cp, ma=ma, khung=khung)
        bh = MP.mua_giu(phan, cp, ma=ma, khung=khung)
    except Exception:
        return None
    return _Chan(ma, khung, np.asarray(kq.loi, float), np.asarray(bh.loi, float),
                 phan.index, int(kq.so_lenh or 0), cp.do_tin,
                 float(kq.phoi_nhiem or 0.0), np.asarray(kq.vi_the, float))


def _gong(cac_chan: list[_Chan], lay: str) -> pd.DataFrame:
    """Gong cac chuoi ve cung moc thoi gian. `lay` = 'loi' hoac 'loi_bh'.

    `dropna(how="all")` roi KHONG fillna: o NaN nghia la "tai san nay chua ton
    tai / khong giao dich moc nay", va no phai giu nguyen la NaN de buoc trong
    so bo qua no. Doi NaN thanh 0 la ngam bao "co mat va hoa von" - tuc pha
    loang do lech chuan cua ro bang nhung o khong co thuc.
    """
    bang = {c.ma: pd.Series(getattr(c, lay), index=DL.chuan_hoa_index(c.index))
            for c in cac_chan}
    # `sort=True` ro rang: pandas 4 bo mac dinh nay va se de index KHONG sap
    # xep neu khong noi. Chuoi loi suat khong sap theo thoi gian thi moi phep
    # tinh sau do - phi qua dem theo so dem, sut giam luy ke - deu sai im lang.
    return pd.concat(bang, axis=1, sort=True).dropna(how="all")


def khung_gia(loi_ro: np.ndarray, index) -> pd.DataFrame:
    """Dung mot khung OHLC gia lap co open[i]->open[i+1] DUNG BANG `loi_ro`.

    Vi sao can: `cong.placebo` khong nhan chuoi loi suat, no nhan `df` va chay
    lai `MP.chay` tren do de dung null "cung phoi nhiem, khong co ky nang".
    Truyen mot khung chi co cot `close` thi no nem KeyError o giua duong - sau
    khi da chay het backtest that. Da sap that 22/08.

    `_loi_suat_tien` doc log(open[i+1]/open[i]) va dat bar cuoi = 0, nen dung
    lai gia bang tich luy tu chinh chuoi loi suat cua RO thi placebo chay tren
    dung chuoi ma ta dang xet.
    """
    x = np.asarray(loi_ro, dtype=float)
    o = np.empty(len(x))
    o[0] = 1.0
    if len(x) > 1:
        o[1:] = np.exp(np.cumsum(x[:-1]))
    return pd.DataFrame({"open": o, "high": o, "low": o, "close": o}, index=index)


def gop_deu(bang: pd.DataFrame) -> np.ndarray:
    """Loi suat cua ro chia deu theo tung moc, chi tren cac chan CO MAT.

    Day la cho de sinh loi song sot nhat: neu chia cho SO CHAN CUA CA KY thi
    nhung moc chi co 2/12 chan se bi chia cho 12, tuc ro bi lam nhat mot cach
    gia tao o dau ky. Con neu bo cac moc khong du chan thi ta da chon cua so
    theo cai gi CO du lieu ve sau - do la biet truoc.
    """
    return bang.mean(axis=1, skipna=True).to_numpy(dtype=float)


def _ro(ten_mau: str, cac_ma: list[str], khung: str, tham_so: dict,
        tren_holdout: bool = True) -> dict:
    """Dung mot ro: chay tung chan roi gop deu."""
    chan = [c for c in (_mot_chan(ten_mau, m, khung, tham_so, tren_holdout)
                        for m in cac_ma[:TOI_DA_CHAN]) if c is not None]
    if len(chan) < TOI_THIEU_CHAN:
        # Khoa loi KHONG duoc dat ten `loi`: trong module nay `loi` la CHUOI LOI
        # SUAT (mang numpy), va `if ro.get("loi")` tren mot mang nem ValueError.
        # Hai nghia cua tu "loi" da va nhau ngay lan chay dau tien.
        return {"khong_dung_duoc": f"chi dung duoc {len(chan)} chan, "
                                   f"can >= {TOI_THIEU_CHAN}",
                "so_chan": len(chan)}
    b_he = _gong(chan, "loi")
    b_bh = _gong(chan, "loi_bh")

    # CHI GIU DOAN CO DU CHAN. Do that lan chay dau: ro 9 chi so co trung vi
    # dung 1 chan mot moc (mean 3,18, max 9). Ly do la moi chan co holdout
    # RIENG - holdout cua NASDAQ bat dau ~2004 con cua IBEX35 ~2012 - nen hop
    # cua chung keo dai 28,9 nam ma nua dau chi co mot chan. Mot "ro" nhu vay
    # khong gop duoc gi: no la mot phep thu don le doi ten, va no thua huong
    # nhieu cua tai san don le dung o cho ma ta dang tuyen bo la da giam nhieu.
    #
    # Cat theo SO CHAN CO MAT la dieu kien ve DU LIEU CO SAN, biet truoc tu
    # lich, khong doc mot con so loi suat nao - nen khong phai chon cua so theo
    # ket qua.
    du = b_he.notna().sum(axis=1) >= TOI_THIEU_CHAN
    if int(du.sum()) < TOI_THIEU_BAR:
        return {"khong_dung_duoc": f"chi {int(du.sum())} moc co >= "
                                   f"{TOI_THIEU_CHAN} chan cung luc",
                "so_chan": len(chan)}
    # KHONG duoc viet `b_he, b_bh = b_he[du], b_bh.reindex(b_he.index)`: ve
    # phai duoc tinh HET truoc khi gan, nen `b_he.index` o do van la index CU
    # (chua cat) va ro mua-giu giu nguyen 8.112 bar trong khi ro he con 3.634.
    # Moc so sanh do tren mot cua so khac voi he la loi lech hang gia im lang -
    # da sap that ngay lan chay thu hai cua module nay.
    b_he = b_he[du]
    b_bh = b_bh.reindex(b_he.index)
    b_vt = _gong(chan, "vi_the").reindex(b_he.index)
    return {
        "so_chan": len(chan),
        "chan": [c.ma for c in chan],
        "index": b_he.index,
        "cua_so": f"{str(b_he.index[0])[:10]}..{str(b_he.index[-1])[:10]}",
        "chan_trung_binh_moi_moc": round(float(b_he.notna().sum(axis=1).mean()), 2),
        "loi": gop_deu(b_he),
        "loi_bh": gop_deu(b_bh),
        "vi_the": gop_deu(b_vt),
        "so_lenh": int(sum(c.so_lenh for c in chan)),
        # BAT BIEN 3: do tin cua ro = te nhat trong ro.
        "do_tin": ("KHAI" if any(c.do_tin == "KHAI" for c in chan)
                   else ("DO" if all(c.do_tin == "DO" for c in chan) else "SAN")),
        "phoi_nhiem": float(np.mean([c.phoi_nhiem for c in chan])),
        "so_chan_theo_moc": b_he.notna().sum(axis=1).describe().to_dict(),
    }


class _KetQuaGop(MP.KetQua):
    """Ket qua cua RO, dung lai dung kieu `mo_phong.KetQua`.

    KE THUA chu khong dung mot lop rong giong giong: `do_luong.so_sanh` doc
    `chi_phi_spread`/`chi_phi_truot`/`chi_phi_giu`, va mot lop tu che thieu
    dung ba truong do se nem AttributeError o giua duong cong - sau khi da chay
    het backtest. Ke thua thi moi truong tuong lai cua `KetQua` co mac dinh san.

    Chi phi cua ro deu bang 0 o day, va do la DUNG: chi phi da duoc tru trong
    tung chan roi. Gop lai mot lan nua la tinh hai lan.
    """

    def __init__(self, loi, index, vi_the, so_lenh, phoi_nhiem,
                 chi_phi_spread=0.0, chi_phi_truot=0.0, chi_phi_giu=0.0):
        super().__init__(
            ma="RO", khung="", index=index, vi_the=vi_the, loi=loi,
            loi_tho=loi, r=None, chi_phi_spread=chi_phi_spread,
            chi_phi_truot=chi_phi_truot, chi_phi_giu=chi_phi_giu,
            so_lan_doi=0, so_lenh=so_lenh, phoi_nhiem=phoi_nhiem, canh_bao=[])


def xet_gop(ten_mau: str, ho: str | None = None, khung: str | None = None,
            tham_so: dict | None = None, kho: list[str] | None = None,
            gt_ma: str | None = None, da_dang_ky: bool = False,
            tran: int = TOI_DA_CHAN) -> dict:
    """Kiem dinh mot co che tren ro `hop` va ro doi chung, ton MOT suat FDR.

    Tra dict co `verdict` (tu `cong.xet` tren ro `hop`), `cach_biet` giua hai ro
    va toan bo so lieu de doc lai.
    """
    if ten_mau not in MAU.MAU:
        return {"mau": ten_mau, "loi": "khong co trong thu vien mau"}
    m = MAU.MAU[ten_mau]
    ho = ho or (m.get("ho") or "khac")
    khai = PV.PHAM_VI.get(ho)
    if not khai:
        return {"mau": ten_mau, "ho": ho, "loi": f"ho '{ho}' chua khai pham vi"}
    khung = khung or PV.khung_cua_ho(ho)
    tham_so = tham_so if tham_so is not None else ((m.get("luoi") or [{}])[0])
    kho = kho if kho is not None else PV.kho_du_bar(khung)

    # Chan cua ro CHINH chon theo cong suat (xem `chon_chan`). Nhom DOI CHUNG
    # van lay trai deu theo `pham_vi`: no khong can dai, no can DAI DIEN cho lop.
    ung_vien_hop = [m for m in sorted(kho) if PV.loai_cua(m) in khai["hop"]]
    _c = chon_chan(ung_vien_hop, khung, tran)
    nhom_hop = _c["chan"]
    ra_chon = {k: v for k, v in _c.items() if k != "quet"}
    nhom_khong = PV.tai_san_theo_loai(khai["khong_hop"], tran, kho)

    ra: dict = {"mau": ten_mau, "ho": ho, "khung": khung, "tham_so": tham_so,
                "lop_hop": khai["hop"], "lop_doi_chung": khai["khong_hop"],
                "chon_chan": ra_chon, "ly_do_pham_vi": khai["ly_do"]}

    ro_hop = _ro(ten_mau, nhom_hop, khung, tham_so)
    if ro_hop.get("khong_dung_duoc"):
        ra["ket_luan"] = "CHUA_DU_MAU"
        ra["verdict"] = "CHUA_DU_MAU"
        ra["ly_do"] = f"ro hop: {ro_hop['khong_dung_duoc']}"
        return ra
    ra["ro_hop"] = {k: v for k, v in ro_hop.items()
                    if k not in ("index", "loi", "loi_bh")}

    # Chi so cua hai ro, de doc va de so sanh - chua phai phan quyet.
    cs_hop = DO.chi_so(ro_hop["loi"], ro_hop["index"])
    ra["sharpe_ro_hop"] = cs_hop.get("sharpe")

    ro_khong = _ro(ten_mau, nhom_khong, khung, tham_so) if nhom_khong else None
    if ro_khong and not ro_khong.get("khong_dung_duoc"):
        cs_khong = DO.chi_so(ro_khong["loi"], ro_khong["index"])
        ra["sharpe_ro_doi_chung"] = cs_khong.get("sharpe")
        ra["so_chan_doi_chung"] = ro_khong["so_chan"]
        ra["cach_biet"] = round(float((cs_hop.get("sharpe") or 0.0) -
                                      (cs_khong.get("sharpe") or 0.0)), 4)
    else:
        ra["sharpe_ro_doi_chung"] = None
        ra["cach_biet"] = None
        if nhom_khong:
            ra["doi_chung_khong_do_duoc"] = (ro_khong or {}).get("khong_dung_duoc")

    # ------------------------------------------------------------------ CONG
    # Chi phi cua RO: dung mo hinh cua mot chan dai dien nhung ep `do_tin` ve
    # muc te nhat cua ro (bat bien 3). `cong.xet` chi doc `do_tin` va `canh_bao`
    # tu doi tuong nay, cac con so chi phi da nam trong chuoi loi suat roi.
    cp_ro = CP.MoHinhChiPhi(
        ma=f"RO:{'+'.join(khai['hop'])}", spread_frac_theo_gio={},
        spread_frac_chung=0.0, truot_gia_frac=0.0,
        phi_nam_mua=0.0, phi_nam_ban=0.0, do_tin=ro_hop["do_tin"],
        nguon=f"ro {ro_hop['so_chan']} chan, chi phi da tru trong tung chan",
        do_luc=SO.bay_gio(),
        canh_bao=[f"chi phi da tru o tung chan; do_tin cua ro = te nhat trong "
                  f"{ro_hop['so_chan']} chan"])

    n = len(ro_hop["loi"])
    kq_he = _KetQuaGop(ro_hop["loi"], ro_hop["index"], ro_hop["vi_the"],
                       ro_hop["so_lenh"], ro_hop["phoi_nhiem"])
    kq_bh = _KetQuaGop(ro_hop["loi_bh"], ro_hop["index"],
                       np.ones(n), ro_hop["so_chan"], 1.0)

    che_do = "giao_dich" if ro_hop["do_tin"] in ("DO", "SAN") else "nghien_cuu"
    ma_gt = gt_ma or f"GOP.{ten_mau}.{khung}.{'+'.join(khai['hop'])}"
    # Khung gia cua RO, dung tu chuoi loi suat MUA-GIU cua ro. Placebo se chay
    # `MP.chay` tren khung nay voi chuoi vi the da hoan vi, tuc null la "cung
    # nhip vao/ra, khong co ky nang chon thoi diem".
    #
    # Xap xi phai ghi ro: loi suat that cua ro la trung binh cua (vi_the_i x
    # r_i) tung chan, con o day null tinh (trung binh vi_the) x (trung binh r).
    # Hai so nay chi bang nhau khi vi the va loi suat khong dong bien GIUA cac
    # chan. Null vi vay hoi DE hon thuc te mot chut - sai so than trong dung
    # chieu (kho qua cong hon), khong phai chieu nguoc lai.
    df_ro = khung_gia(ro_hop["loi_bh"], ro_hop["index"])
    kt = CONG.xet(df_ro, kq_he, kq_bh, cp_ro, gt_ma=ma_gt,
                  ho=f"gop_{ho}@cp{CP.THE_HE}" +
                     ("@nghien_cuu" if che_do == "nghien_cuu" else ""),
                  da_dang_ky=da_dang_ky, tren_holdout=True, che_do=che_do)

    ra["che_do"] = che_do
    ra["verdict"] = kt["verdict"]
    ra["ly_do"] = kt["ly_do"][:5]
    ra["dieu_kien"] = kt["dieu_kien"]
    ra["so_sanh"] = kt["so_sanh"]
    ra["p_placebo"] = (kt.get("placebo") or {}).get("p_xau_nhat")
    ra["p_alpha"] = kt.get("p_alpha")

    # BAT BIEN 4: qua cong ma KHONG tach khoi doi chung thi khong phai co che.
    if ra["verdict"] in ("PASS", "CO_CO_CHE", "UNG_VIEN") and \
            ra.get("cach_biet") is not None and \
            ra["cach_biet"] < PV.CACH_BIET_TOI_THIEU:
        ra["verdict_truoc_phan_chung"] = ra["verdict"]
        ra["verdict"] = "KHONG_PHAN_BIET"
        ra["ly_do"] = list(ra["ly_do"]) + [
            f"ro hop {ra['sharpe_ro_hop']} vs ro doi chung "
            f"{ra['sharpe_ro_doi_chung']}: cach biet {ra['cach_biet']} < "
            f"{PV.CACH_BIET_TOI_THIEU}. Gop lam TANG LUC cho ca co che that lan "
            "bay; ro doi chung sang len tuong duong nghia la thu do duoc la mot "
            "dac tinh chung cua gia."]
    return ra


def quet_tham_so_gop(ten_mau: str, ho: str | None = None, khung: str | None = None,
                     kho: list[str] | None = None, tran: int = TOI_DA_CHAN) -> dict:
    """TANG KHAM PHA cua duong gop: chon MOT bo tham so cho CA RO, tren TRAIN.

    Vi sao mot bo tham so cho ca ro chu khong phai moi chan mot bo: neu moi chan
    duoc chon tham so rieng thi ta da fit 12 lan roi bao la mot gia thuyet. Mot
    bo duy nhat cho ca lop moi dung voi cau dang hoi - "co che nay song o loai
    thi truong nay" - va moi la MOT gia thuyet.

    Chay tren TRAIN. Khong cham holdout, khong sinh p-value, khong ton suat FDR.
    """
    if ten_mau not in MAU.MAU:
        return {"mau": ten_mau, "loi": "khong co trong thu vien mau"}
    m = MAU.MAU[ten_mau]
    ho = ho or (m.get("ho") or "khac")
    khai = PV.PHAM_VI.get(ho)
    if not khai:
        return {"mau": ten_mau, "ho": ho, "loi": f"ho '{ho}' chua khai pham vi"}
    khung = khung or PV.khung_cua_ho(ho)
    kho = kho if kho is not None else PV.kho_du_bar(khung)
    nhom = chon_chan([m for m in sorted(kho) if PV.loai_cua(m) in khai["hop"]],
                     khung, tran)["chan"]

    ra = {"mau": ten_mau, "ho": ho, "khung": khung, "lop": khai["hop"],
          "da_quet": 0, "diem": []}
    tot = None
    for ts in (m.get("luoi") or [{}]):
        ro = _ro(ten_mau, nhom, khung, ts, tren_holdout=False)
        if ro.get("khong_dung_duoc"):
            continue
        cs = DO.chi_so(ro["loi"], ro["index"])
        cs_bh = DO.chi_so(ro["loi_bh"], ro["index"])
        ra["da_quet"] += 1
        ra["diem"].append({"tham_so": ts, "sharpe": cs.get("sharpe"),
                           "sharpe_mua_giu": cs_bh.get("sharpe"),
                           "so_chan": ro["so_chan"], "cua_so": ro.get("cua_so")})
        # Sang tho GIONG tang kham pha don le: phai thang mua-giu CA loi suat
        # LAN sharpe ngay tren train.
        if (cs.get("tong_lai_pct") or -1e9) <= (cs_bh.get("tong_lai_pct") or 0):
            continue
        if (cs.get("sharpe") or -9) <= (cs_bh.get("sharpe") or 0):
            continue
        if tot is None or (cs.get("sharpe") or -9) > (tot[1].get("sharpe") or -9):
            tot = (ts, cs, ro)
    if tot is None:
        ra["ket_luan"] = "KHONG_CO_UNG_VIEN"
        ra["ly_do"] = ("khong bo tham so nao thang mua-giu cua RO tren train "
                       "(ca loi suat lan sharpe)")
        return ra
    ts, cs, ro = tot
    ra["ket_luan"] = "CO_UNG_VIEN"
    ra["tham_so"] = ts
    ra["sharpe_train"] = cs.get("sharpe")
    ra["so_chan"] = ro["so_chan"]
    ra["chan"] = ro["chan"]
    ra["cua_so_train"] = ro.get("cua_so")
    return ra


def mde_gop(ho: str, khung: str | None = None, kho: list[str] | None = None,
            tran: int = TOI_DA_CHAN, thang_p=None, hat: int = 4242) -> dict:
    """Sharpe nho nhat ma phep kiem GOP con nhin thay duoc.

    Cung cach do voi `do_luc.duong_cong_luc` nhung tren RO: cay vao MOI chan mot
    tin hieu doan dung dau loi suat `p` phan tram so bar, gop lai roi cho cong
    phan xu. `p` nho nhat vuot duoc cong cho ta nguong cua ro.

    Khong co con so nay thi mot ket qua gop AM TINH khong doc duoc: "ro cho
    Sharpe 0,158 va truot cong" co the nghia la co che khong co that, ma cung
    co the nghia la ro nay khong thay duoc gi duoi 0,4.
    """
    from nhan import do_luc as DLUC
    khai = PV.PHAM_VI.get(ho)
    if not khai:
        return {"ho": ho, "loi": f"ho '{ho}' chua khai pham vi"}
    khung = khung or PV.khung_cua_ho(ho)
    kho = kho if kho is not None else PV.kho_du_bar(khung)
    nhom = chon_chan([m for m in sorted(kho) if PV.loai_cua(m) in khai["hop"]],
                     khung, tran)["chan"]
    thang_p = thang_p or THANG_P_GOP

    # Nap mot lan, dung lai cho moi muc p.
    nap = []
    for m in nhom:
        try:
            df = DL.nap(m, khung)
            if DL.nguon_tai_san(m) == "ngoai":
                df = DL.cat_theo_chat_luong(df, m)[0]
            phan = DL.hai_nua(df, 0.6)[1]
            if len(phan) < TOI_THIEU_BAR:
                continue
            nap.append((m, phan, CP.tu_du_lieu(m, phan)))
        except Exception:
            continue
    if len(nap) < TOI_THIEU_CHAN:
        return {"ho": ho, "khung": khung, "mde_gop": None,
                "loi": f"chi nap duoc {len(nap)} chan"}

    do_tin = ("KHAI" if any(cp.do_tin == "KHAI" for _m, _p, cp in nap)
              else ("DO" if all(cp.do_tin == "DO" for _m, _p, cp in nap) else "SAN"))
    che_do = "giao_dich" if do_tin in ("DO", "SAN") else "nghien_cuu"

    diem, nguong = [], None
    for p in sorted(thang_p):
        chan = []
        for i, (m, phan, cp) in enumerate(nap):
            r = MP._loi_suat_tien(phan)
            dau = np.sign(r)
            dau[dau == 0] = 1.0
            rng = np.random.default_rng(hat + i)
            v = np.where(rng.random(len(phan)) < p, dau, -dau)
            kq = MP.chay(phan, v, cp, ma=m, khung=khung, da_dich=True)
            bh = MP.mua_giu(phan, cp, ma=m, khung=khung)
            chan.append(_Chan(m, khung, np.asarray(kq.loi, float),
                              np.asarray(bh.loi, float), phan.index,
                              int(kq.so_lenh or 0), cp.do_tin,
                              float(kq.phoi_nhiem or 0.0),
                              np.asarray(kq.vi_the, float)))
        b_he = _gong(chan, "loi")
        b_bh = _gong(chan, "loi_bh")
        du = b_he.notna().sum(axis=1) >= TOI_THIEU_CHAN
        b_he = b_he[du]
        b_bh = b_bh.reindex(b_he.index)
        if len(b_he) < TOI_THIEU_BAR:
            continue
        loi, loi_bh = gop_deu(b_he), gop_deu(b_bh)
        vt = gop_deu(_gong(chan, "vi_the").reindex(b_he.index))
        n = len(loi)
        pn = float(np.mean([c.phoi_nhiem for c in chan]))
        kq_he = _KetQuaGop(loi, b_he.index, vt,
                           int(sum(c.so_lenh for c in chan)), pn)
        kq_bh = _KetQuaGop(loi_bh, b_he.index, np.ones(n), len(chan), 1.0)
        cp_ro = CP.MoHinhChiPhi(ma="RO", do_tin=do_tin, nguon="ro do luc",
                                do_luc=SO.bay_gio(), canh_bao=[])
        df_ro = khung_gia(loi_bh, b_he.index)
        kt = CONG.xet(df_ro, kq_he, kq_bh, cp_ro, gt_ma=f"LUCGOP.{ho}.{khung}.p{p}",
                      ho="do_luc_gop", da_dang_ky=True, tren_holdout=True,
                      che_do=che_do)
        # Bo dieu kien noi ve KHA NANG GIAO DICH va NGAN SACH - giong `do_luc`,
        # va vi cung mot ly do: MDE la tinh chat cua phep kiem, khong phai cua
        # so suat FDR con lai.
        bo = set(DLUC.DIEU_KIEN_GIAO_DICH) | set(DLUC.DIEU_KIEN_NGAN_SACH)
        qua_tk = all(v for k, v in kt["dieu_kien"].items() if k not in bo)
        sh = kt["so_sanh"]["he"].get("sharpe")
        diem.append({"p": p, "sharpe": sh, "verdict": kt["verdict"],
                     "qua_thong_ke": bool(qua_tk)})
        if qua_tk and nguong is None:
            nguong = {"p": p, "sharpe": sh,
                      "alpha_nam_pct": kt["so_sanh"]["alpha_vs_mua_giu"].get("alpha_nam_pct")}
    return {"ho": ho, "khung": khung, "so_chan": len(nap), "che_do": che_do,
            "chan": [m for m, _p, _c in nap], "diem": diem,
            "mde_gop": (nguong or {}).get("sharpe"),
            "alpha_nho_nhat_thay_duoc": (nguong or {}).get("alpha_nam_pct"),
            "ly_do_neu_khong_dat": None if nguong else
            "khong muc nao trong thang do chinh xac vuot duoc cong tren ro nay"}


if __name__ == "__main__":
    import json
    import sys
    ten = sys.argv[1] if len(sys.argv) > 1 else "ibs_bat_day"
    r = xet_gop(ten)
    print(json.dumps({k: v for k, v in r.items() if k != "so_sanh"},
                     ensure_ascii=False, indent=1, default=str)[:4000])
