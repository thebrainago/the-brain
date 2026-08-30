# -*- coding: utf-8 -*-
"""Do LUC cua cong: edge nho nhat ma he con nhin thay duoc.

MOT KET LUAN AM TINH KHONG KEM CON SO NAY THI KHONG DOC DUOC. "Khong tim thay
edge" co the co nghia la thi truong rong, ma cung co the co nghia la thuoc do
qua tho. Hai truong hop do doi hoi hai hanh dong nguoc nhau, va phan biet chung
la viec cua module nay.

Do that ngay 21/08/2026. Tren du lieu SAN (ngan):

    EURCAD  H4   5,4 nam holdout  ->  can Sharpe 1,39
    US500M  D1   2,6 nam          ->  can Sharpe 1,54
    XAUUSDM D1   5,0 nam          ->  can Sharpe 1,26

Tren chuoi chi so DAI va SACH (open that, xem `du_lieu.kiem`):

    YH_NASDAQ D1  22,2 nam  ->  can Sharpe 0,54
    YH_NIKKEI D1  22,6 nam  ->  can Sharpe 0,65
    YH_DAX    D1  15,4 nam  ->  can Sharpe 0,74

Ty le bam sat 1/sqrt(T). Edge THAT cua FX/chi so sau phi nam o 0,3-0,8. Nghia
la: tren du lieu san, he KHONG THE thay duoc edge co thuc - do la ly do 346 gia
thuyet deu FAIL, va no KHAC HAN voi "thi truong khong co gi". Tren chuoi dai thi
thay duoc, nhung chuoi dai la chi so KHONG MUA DUOC nen chi tra loi duoc cau
"co co che khong", khong tra loi duoc "giao dich duoc khong".

=> Kien truc dung la HAI CHANG: chuoi dai de PHAT HIEN co che, chuoi san de
CHUNG NHAN giao dich duoc.

CACH DO. Cay mot tin hieu biet truoc dau loi suat nhung chi dung `p` phan tram
so lan, roi tang dan `p` cho toi khi cong cho qua. `p` la mot num xoay do chinh
xac lien tuc, nen no do duoc DUONG CONG LUC chu khong chi mot diem.

CACH LAM TANG LUC (theo thu tu de lam truoc):
  1. Gop nhieu tai san cho CUNG mot co che - xem `nhan/pham_vi.py`. Nhung PHAI
     tinh theo k HIEU DUNG, khong phai k danh nghia: gop chi mua duoc luc den
     muc cac tai san doc lap. Do that tren kho hien co (21/08/2026):
         chi so My  k= 4  rho 0,447 -> k hieu dung 1,71 -> loi the 1,31x
         FX         k=11  rho 0,218 -> k hieu dung 3,46 -> loi the 1,86x
         vang       k= 5  rho 0,859 -> k hieu dung 1,13 -> loi the 1,06x
         tat ca     k=20  rho 0,203 -> k hieu dung 4,12 -> loi the 2,03x
     Tuc gop TAT CA 20 tai san chi ha nguong tu 1,57 xuong ~0,77 - chua den muc
     0,3-0,5 la cho edge that nam. Va gop 5 cap vang thi gan nhu khong duoc gi.
  2. Keo dai lich su (D1 di duoc xa hon H4 rat nhieu).
  3. Cuoi cung moi den noi long nguong - va noi long thi phai chap nhan ty le
     duong tinh gia cao hon, do bang null factory.
"""
from __future__ import annotations

import json
import os
import math
from pathlib import Path

import numpy as np

from nhan import chi_phi as CP
from nhan import cong as CONG
from nhan import du_lieu as DL
from nhan import mo_phong as MP
from nhan import so as SO

LAB_REPORTS = Path(__file__).resolve().parent.parent / "reports"

#: Cac muc do chinh xac de do. 0,50 = khong co edge.
THANG_P = (0.50, 0.52, 0.54, 0.55, 0.56, 0.565, 0.57, 0.575,
           0.58, 0.59, 0.60, 0.62, 0.65, 0.70)
#: Verdict duoc coi la "cong da cho qua".
QUA = ("PASS", "UNG_VIEN", "NGHI_NHIN_TRUOC", "CO_CO_CHE")
#: Hat co dinh de ket qua lap lai duoc.
HAT = 4242
#: Nhung dieu kien noi ve KHA NANG GIAO DICH, khong noi ve co che co that hay
#: khong. Chuoi nghien cuu (chi so Yahoo 20-56 nam) luon truot nhom nay vi
#: khong mua duoc nen khong do duoc chi phi that.
DIEU_KIEN_GIAO_DICH = ("7_chi_phi_do_duoc",)

#: Dieu kien noi ve NGAN SACH con lai, khong noi ve suc manh cua phep kiem.
#:
#: Phai loai khoi phep do MDE, vi hai ly do:
#:  1. MDE la tinh chat cua PHEP KIEM (co bao nhieu du lieu, nhieu bao nhieu),
#:     khong phai cua so suat FDR con lai. Cung mot chien luoc do hom nay va do
#:     sau 200 phep thu khac se ra hai con so khac nhau neu tinh ca dieu kien 10.
#:  2. Ban than viec DO cung tieu suat: sau 109 lan do, ho `do_luc` tut nguong
#:     ve 2,09e-05, nen chinh cong cu do lam xau ket qua cua no. Da thay that.
#: Nguong FDR hien tai duoc bao rieng o `nguong_fdr_hien_tai`.
DIEU_KIEN_NGAN_SACH = ("10_qua_fdr_online",)


def _mot_muc(phan, cp, bh, p: float, ma: str, khung: str, hat: int = HAT,
             che_do: str = "giao_dich") -> dict:
    """Cay tin hieu do chinh xac `p` roi cho cong phan xu."""
    r = MP._loi_suat_tien(phan)
    dau = np.sign(r)
    dau[dau == 0] = 1.0
    rng = np.random.default_rng(hat)
    # `p` la DO CHINH XAC, khong phai "ty le lan duoc mach nuoc": dung khi biet
    # con lai boc ngau nhien thi do chinh xac that la p + (1-p)/2.
    v = np.where(rng.random(len(phan)) < p, dau, -dau)
    kq = MP.chay(phan, v, cp, ma=ma, khung=khung, da_dich=True)
    # `ghi_so=False`: day la ORACLE TONG HOP (tin hieu biet truoc voi do chinh
    # xac `p`), khong phai mot gia thuyet ve thi truong. No phai gap DUNG cai
    # nguong ma mot phep thu that se gap - nen van tinh LORD tai vi tri j - nhung
    # khong duoc chiem suat trong so.
    kt = CONG.xet(phan, kq, bh, cp, gt_ma=f"LUC.{ma}.{khung}.{len(phan)}.p{p}.h{hat}",
                  ho="do_luc", da_dang_ky=True, tren_holdout=True, che_do=che_do,
                  ghi_so=False)
    ss = kt["so_sanh"]
    dk = kt["dieu_kien"]
    # Chuoi nghien cuu (chi so Yahoo) khong giao dich duoc nen chi phi chi la
    # KHAI BAO, va `7_chi_phi_do_duoc` luon truot -> khong bao gio PASS. Do la
    # dung: khong ai mua duoc YH_NIKKEI. Nhung cau hoi o tang KHAM PHA la "co
    # co che khong", khac cau hoi o tang chung nhan la "giao dich duoc khong".
    # Vi vay do rieng hai chieu.
    bo_qua = set(DIEU_KIEN_GIAO_DICH) | set(DIEU_KIEN_NGAN_SACH)
    qua_thong_ke = all(v for k, v in dk.items() if k not in bo_qua)
    return {
        "p": p, "verdict": kt["verdict"], "qua": kt["verdict"] in QUA,
        "qua_thong_ke": bool(qua_thong_ke),
        "sharpe": ss["he"].get("sharpe"),
        "alpha_nam_pct": ss["alpha_vs_mua_giu"].get("alpha_nam_pct"),
        "t_alpha": ss["alpha_vs_mua_giu"].get("t_alpha"),
        "truot": [k for k, x in kt["dieu_kien"].items() if not x][:3],
    }


def _nguong_fdr(family: str) -> float | None:
    """Nguong LORD ke tiep cua mot ho - de doc kem MDE, khong tron vao no."""
    try:
        epoch = CONG.ho_fdr(family)
        n = SO.mot("SELECT COUNT(*) n FROM fdr WHERE ho=?", epoch)["n"]
        return round(CONG.nguong_lord(int(n) + 1), 9)
    except Exception:
        return None


def duong_cong_luc(ma: str = "EURCAD", khung: str = "H4",
                   thang_p=THANG_P, hat: int = HAT) -> dict:
    """Do duong cong luc tren holdout cua mot tai san."""
    try:
        df = DL.nap(ma, khung)
        if DL.nguon_tai_san(ma) == "ngoai":
            # Cung phep cat voi `quantlab._nap`. Do MDE tren doan co gia bia
            # cho ra mot con so khong ai dung duoc: no la MDE cua chuoi khac.
            df = DL.cat_theo_chat_luong(df, ma)[0]
    except Exception as e:
        return {"loi": f"khong nap duoc {ma} {khung}: {type(e).__name__}"}
    _train, hold = DL.hai_nua(df, 0.6)
    if len(hold) < 500:
        return {"loi": f"holdout chi {len(hold)} bar"}
    cp = CP.tu_du_lieu(ma, hold)
    bh = MP.mua_giu(hold, cp, ma=ma, khung=khung)

    # Chuoi khong mua duoc (chi so Yahoo) chi tra loi duoc cau "co co che
    # khong", nen do o che do nghien cuu; con lai do o che do giao dich.
    do_duoc = getattr(cp, "do_tin", None) in ("DO", "SAN")
    che_do = "giao_dich" if do_duoc else "nghien_cuu"

    diem = []
    nguong = None
    for p in sorted(thang_p):
        d = _mot_muc(hold, cp, bh, p, ma, khung, hat, che_do=che_do)
        diem.append(d)
        # Dung `qua_thong_ke`: MDE khong duoc phu thuoc vao ngan sach con lai.
        if d["qua_thong_ke"] and nguong is None:
            nguong = d

    bar_nam = CP.hinh_hoc(hold.index)[0] if hasattr(CP, "hinh_hoc") else None
    return {
        "tai_san": ma, "khung": khung, "so_bar": len(hold),
        "diem": diem,
        "nguong": nguong,
        "sharpe_nho_nhat_thay_duoc": nguong["sharpe"] if nguong else None,
        "alpha_nho_nhat_thay_duoc": nguong["alpha_nam_pct"] if nguong else None,
        # Nguong o tang KHAM PHA: bo qua dieu kien kha nang giao dich.
        "sharpe_nho_nhat_thay_co_che": nguong["sharpe"] if nguong else None,
        "che_do": che_do,
        "chi_phi_do_duoc": do_duoc,
        # `nguong` do bang `qua_thong_ke`, tuc DA loai dieu kien kha nang giao
        # dich va dieu kien ngan sach. Vi vay `nguong is None` chi con MOT nghia:
        # luc qua thap. Ban truoc o day co mot nhanh ba re toi `nguong_tk` -
        # bien khong ton tai - nen ham NEM NameError o dung nhung cap yeu nhat,
        # tuc dung nhung cap ma cau tra loi "khong do duoc" la thong tin quan
        # trong nhat. Loi im o duong ngoai le.
        "ly_do_neu_khong_dat": None if nguong else (
            f"khong muc nao trong thang p (toi {max(thang_p):.3f}) vuot duoc "
            f"cong o che do '{che_do}' - {len(hold)} bar la qua it de do"),
        "bar_moi_nam": bar_nam,
        # Bao rieng: ngoai suc manh phep kiem, ung vien con phai vuot nguong FDR
        # hien tai cua ho no. Do la mot rang buoc KHAC, va no thay doi theo so
        # phep thu da tieu.
        "nguong_fdr_hien_tai": _nguong_fdr("do_luc"),
    }


#: Bo nho dem MDE tren dia. Do MDE mot cap mat ~10 giay (14 muc p x mot lan
#: backtest + placebo moi muc), va ket qua chi doi khi DU LIEU doi.
MDE_CACHE = LAB_REPORTS / "mde_cap.json"


def _doc_mde_cache() -> dict:
    try:
        return json.loads(MDE_CACHE.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _ghi_mde_cache(khoa: str, muc: dict) -> None:
    """Them MOT muc vao cache, GOP va ghi NGUYEN TU.

    BAY DA SAP THAT 30/08/2026 khi bat quet song song 8 tien trinh. Ban cu goi
    thang `MDE_CACHE.write_text(json.dumps(cache))`, va cai do hong hai duong:

      1. **Mat muc.** Tien trinh A doc cache, them muc cua no, ghi de ca file.
         Tien trinh B doc TRUOC luc A ghi, them muc cua no, ghi de ca file ->
         muc cua A bien mat.
      2. **Doc trung cua so ghi.** `write_text` thang len file dang duoc doc tao
         mot cua so vai chuc mili giay trong do file KHONG phai JSON hop le;
         `_doc_mde_cache` nuot ngoai le va tra `{}` -> ca bang MDE coi nhu rong
         va moi cap bi do lai.

    Trieu chung do duoc: cung mot vong quet chay tuan tu va song song cho Sharpe
    lech o chu so thu ba (0,006 vs 0,007) tren mot o. Phan quyet khong doi lan
    do, nhung mot duong ong tat dinh thi khong duoc lech gi ca.

    Cach sua giong het `chi_phi._ghi_cau_hinh` - noi du an DA sua dung loi nay
    tu 15/08 nhung khong ai mang sang day.
    """
    try:
        MDE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        # DOC LAI ngay truoc khi ghi: gop muc cua minh vao ban MOI NHAT tren dia,
        # khong ghi de bang ban da doc tu dau ham.
        cache = _doc_mde_cache()
        cache[khoa] = muc
        tam = MDE_CACHE.with_suffix(f".json.tam{os.getpid()}")
        tam.write_text(json.dumps(cache, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        os.replace(tam, MDE_CACHE)      # doi ten tren cung o dia la nguyen tu
    except Exception:
        pass


def mde_cua(ma: str, khung: str, lam_moi: bool = False) -> dict:
    """MDE cua mot cap (tai san, khung): Sharpe nho nhat cong con nhin thay.

    Co cache tren dia, xa theo SO BAR - so bar doi nghia la du lieu doi nghia la
    phep kiem doi. Tra `{"mde": float|None, "so_bar": int, "che_do": str}`.

    `mde = None` co nghia RIENG BIET voi `mde` lon: no la "khong muc nao trong
    thang do chinh xac vuot duoc cong", tuc cap nay khong phan xu duoc bat ky
    edge nao. Hai truong hop deu la thieu luc nhung cai sau la tuyet doi.
    """
    ma, khung = ma.upper(), khung.upper()
    khoa = f"{ma}|{khung}"
    cache = _doc_mde_cache()
    try:
        hold = DL.hai_nua(_nap_da_cat(ma, khung), 0.6)[1]
        so_bar = len(hold)
        cp = CP.tu_du_lieu(ma, hold)
    except Exception as e:
        return {"ma": ma, "khung": khung, "mde": None, "so_bar": 0,
                "loi": f"{type(e).__name__}: {str(e)[:60]}"}
    # Van tay phai gom CA du lieu LAN mo hinh chi phi. MDE la nguong tren Sharpe
    # RONG, nen do mot lan roi giu ban cu sau khi do lai spread la tra ve con so
    # cua mot the gioi khac. Da suyt sap 22/08: do spread bar H1 cho EURUSD/
    # USDJPY/GBPUSD xong, `do_tin` nhay KHAI -> SAN, nhung cache khoa theo so
    # bar nen van tra MDE cu.
    van_tay = (f"{so_bar}|{cp.do_tin}|{round(cp.spread_frac_chung * 1e6)}"
               f"|{round(cp.phi_nam_mua, 5)}|{round(cp.phi_nam_ban, 5)}|cp{CP.THE_HE}")
    cu = cache.get(khoa)
    if cu and not lam_moi and cu.get("van_tay") == van_tay:
        return cu
    r = duong_cong_luc(ma, khung)
    ra = {"ma": ma, "khung": khung, "so_bar": so_bar, "van_tay": van_tay,
          "mde": r.get("sharpe_nho_nhat_thay_duoc"),
          "che_do": r.get("che_do"), "chi_phi_do_tin": cp.do_tin,
          "spread_bps": round(cp.spread_frac_chung * 1e4, 3),
          "loi": r.get("loi"), "do_luc": SO.bay_gio()}
    _ghi_mde_cache(khoa, ra)
    return ra


def _nap_da_cat(ma: str, khung: str):
    df = DL.nap(ma, khung)
    if DL.nguon_tai_san(ma) == "ngoai":
        df = DL.cat_theo_chat_luong(df, ma)[0]
    return df


def du_luc_de_kiem(sharpe_ung_vien, ma: str, khung: str) -> dict:
    """Ung vien nay co dang mot suat FDR tren cap nay khong?

    QUY TAC (chot 22/08/2026): mot ung vien co Sharpe tren tap kham pha THAP HON
    MDE cua chinh cap do thi confirmation KHONG THE phan xu duoc no - no se FAIL
    du gia thuyet dung hay sai. Chay no van ton mot suat ngan sach FDR, va suat
    do lam CAO NGUONG cho moi phep thu sau (LORD giam theo 1/j^1.6).

    Day khong phai lenh cam theo lop tai san ("FX vo vong"). No la phep kiem
    KHA THI theo tung ung vien: mot ung vien FX du manh van di tiep binh thuong.

    Va no than trong dung chieu: Sharpe tren tap kham pha la con so DA duoc chon
    loc (tot nhat trong ~65 to hop) nen no LAC QUAN. Doi hoi no vuot MDE la mot
    bai kiem DE - thu nao truot bai de nay thi chac chan khong qua duoc bai kho.
    """
    m = mde_cua(ma, khung)
    mde = m.get("mde")
    s = None if sharpe_ung_vien is None else float(sharpe_ung_vien)
    if mde is None:
        return {"du_luc": False, "mde": None, "sharpe": s,
                "ly_do": f"{ma} {khung}: khong muc nao trong thang do chinh xac "
                         f"vuot duoc cong ({m.get('so_bar')} bar holdout) - cap "
                         f"nay khong phan xu duoc bat ky edge nao"}
    if s is None:
        return {"du_luc": False, "mde": mde, "sharpe": None,
                "ly_do": "ung vien khong co Sharpe"}
    if s < mde:
        return {"du_luc": False, "mde": mde, "sharpe": s,
                "ly_do": f"Sharpe kham pha {s:.3f} < MDE {mde:.3f} cua {ma} "
                         f"{khung} - confirmation se FAIL du dung hay sai"}
    return {"du_luc": True, "mde": mde, "sharpe": s,
            "ly_do": f"Sharpe kham pha {s:.3f} >= MDE {mde:.3f}"}


def luc_theo_do_dai(ma: str = "EURCAD", khung: str = "H4",
                    cac_phan=(0.25, 0.5, 1.0), hat: int = HAT) -> dict:
    """Nguong phat hien thay doi the nao khi du lieu dai ra.

    Ly thuyet noi nguong ~ 1/sqrt(T). Do that de biet co dung khong, va de
    ngoai suy "can bao nhieu nam de thay mot edge Sharpe X".
    """
    try:
        df = DL.nap(ma, khung)
    except Exception as e:
        return {"loi": f"khong nap duoc {ma} {khung}: {type(e).__name__}"}
    _train, hold_full = DL.hai_nua(df, 0.6)
    ra = []
    for phan in sorted(cac_phan):
        h = hold_full.iloc[-int(len(hold_full) * phan):]
        if len(h) < 400:
            continue
        cp = CP.tu_du_lieu(ma, h)
        bh = MP.mua_giu(h, cp, ma=ma, khung=khung)
        nguong = None
        for p in sorted(THANG_P):
            d = _mot_muc(h, cp, bh, p, ma, khung, hat)
            if d["qua"]:
                nguong = d
                break
        ra.append({"phan": phan, "so_bar": len(h),
                   "sharpe_can": nguong["sharpe"] if nguong else None,
                   "alpha_can_pct": nguong["alpha_nam_pct"] if nguong else None,
                   "p_can": nguong["p"] if nguong else None})
    return {"tai_san": ma, "khung": khung, "muc": ra,
            "ghi_chu": "sharpe_can la edge NHO NHAT con nhin thay duoc o do dai do"}


def nam_can_de_thay(sharpe_muc_tieu: float, moc: dict | None = None) -> float | None:
    """Can bao nhieu nam du lieu de nhin thay mot edge Sharpe cho truoc.

    Dung quy luat 1/sqrt(T) neo vao mot moc da do. `moc` mac dinh la phep do
    ngay 21/08/2026 tren EURCAD H4: 5,5 nam -> nguong Sharpe 1,39.
    """
    moc = moc or {"nam": 5.5, "sharpe": 1.39}
    if sharpe_muc_tieu <= 0:
        return None
    return float(moc["nam"] * (moc["sharpe"] / sharpe_muc_tieu) ** 2)


def k_hieu_dung(rho_trung_binh: float, k: int) -> float:
    """So tai san DOC LAP tuong duong khi k tai san co tuong quan rho.

    Cong thuc hieu ung thiet ke: k_hd = k / (1 + (k-1)*rho).
    Gop tai san chi mua duoc luc DEN MUC chung doc lap. Bo qua rho la mot cach
    tu lua rat de mac: 5 cap vang co rho 0,859 nen gop ca nam chi bang 1,13 cai.
    """
    k = max(1, int(k))
    rho = min(0.999, max(0.0, float(rho_trung_binh)))
    return float(k / (1.0 + (k - 1) * rho))


def loi_the_khi_gop(k_tai_san: int, moc_sharpe: float = 1.39,
                    rho_trung_binh: float | None = None) -> float:
    """Nguong ha xuong con bao nhieu khi gop k tai san.

    PHAI truyen `rho_trung_binh` da DO, dung de mac dinh 0. Do that ngay
    21/08/2026 tren kho hien co:

        chi so My  k= 4  rho 0,447 -> k hieu dung 1,71 -> loi the 1,31x
        FX         k=11  rho 0,218 -> k hieu dung 3,46 -> loi the 1,86x
        vang       k= 5  rho 0,859 -> k hieu dung 1,13 -> loi the 1,06x
        tat ca     k=20  rho 0,203 -> k hieu dung 4,12 -> loi the 2,03x

    Bo qua rho se cho "gop 9 tai san -> Sharpe 0,46" trong khi so that la 0,77.
    """
    if rho_trung_binh is None:
        rho_trung_binh = 0.0
    return float(moc_sharpe / math.sqrt(k_hieu_dung(rho_trung_binh, k_tai_san)))


def do_rho_thuc_te(cac_loai: list[str], khung: str = "H4",
                   tran: int = 20) -> dict:
    """Do tuong quan trung binh THAT giua cac tai san cung mot lop."""
    import pandas as pd
    from nhan import pham_vi as PV
    kho = PV.kho_du_bar(khung)
    chuoi = {}
    for ma in PV.tai_san_theo_loai(cac_loai, tran, kho):
        try:
            df = DL.nap(ma, khung)
        except Exception:
            continue
        s = df["close"].pct_change()
        s.index = DL.chuan_hoa_index(s.index)
        chuoi[ma] = s
    if len(chuoi) < 2:
        return {"k": len(chuoi), "rho": None, "k_hieu_dung": float(len(chuoi))}
    bang = pd.concat(chuoi, axis=1, sort=True).dropna()
    tq = bang.corr().to_numpy()
    ngoai = tq[np.triu_indices(len(tq), 1)]
    rho = float(np.mean(np.abs(ngoai)))
    k = len(tq)
    return {"k": k, "rho": round(rho, 4), "so_bar_chung": len(bang),
            "k_hieu_dung": round(k_hieu_dung(rho, k), 3),
            "loi_the": round(math.sqrt(k_hieu_dung(rho, k)), 3),
            "tai_san": list(bang.columns)}


#: Cap (tai san, khung) do LUC cua tung chang. Khong duoc gop lam mot con so:
#: hai chang co hai do dai lich su khac han nhau nen co hai nguong khac han.
#: Chon cai TOT NHAT cua moi chang - do la nang luc that su cua day chuyen; do
#: tren cai te nhat roi bao "he khong thay duoc gi" la tu ha thap minh.
CAP_DO_LUC = {
    "nghien_cuu": [("YH_NASDAQ", "D1"), ("YH_NIKKEI", "D1"), ("YH_DAX", "D1")],
    # Cap nay doi ngay 22/08 sau khi do spread bar H1 tu XM cho ba chuoi FX dai:
    # `do_tin` nhay KHAI -> SAN, tuc chung tu lan nghien cuu sang lan giao dich,
    # va nguong chang giao dich tut tu 1,261 (XAUUSDM D1) xuong 0,590 (USDJPY
    # D1). Day la lan dau tang chung nhan co the cap giay cho mot edge nam trong
    # khoang 0,3-0,8 - khoang ma edge THAT cua FX/chi so sau phi thuong nam.
    "giao_dich": [("USDJPY", "D1"), ("USDJPY", "H4"), ("EURUSD", "D1"),
                  ("GBPUSD", "D1"), ("US500CASH", "D1"), ("XAUUSDM", "D1")],
}


def luc_hai_chang(cap: dict | None = None) -> dict:
    """Nguong phat hien TOT NHAT cua tung chang, va khoang cach giua hai chang.

    Vi sao phai co ham nay: mot con so `sharpe_nho_nhat_thay_duoc` duy nhat da
    tro thanh vo nghia ke tu khi be mat co ca chuoi 5 nam lan chuoi 56 nam. Do
    tren EURCAD H4 (1,39) roi ket luan "he khong du luc" la sai; do tren
    YH_NASDAQ D1 (0,54) roi ket luan "he du luc de chung nhan giao dich" cung
    sai. Ca hai deu dung - cho DUNG CHANG cua no.
    """
    cap = cap or CAP_DO_LUC
    ra: dict = {"chang": {}}
    for che_do, ds in cap.items():
        tot = None
        for ma, khung in ds:
            r = duong_cong_luc(ma, khung)
            n = r.get("sharpe_nho_nhat_thay_duoc")
            if n is None:
                continue
            if tot is None or float(n) < float(tot["nguong"]):
                tot = {"tai_san": ma, "khung": khung, "nguong": float(n),
                       "alpha_pct_nam": r.get("alpha_nho_nhat_thay_duoc")}
        ra["chang"][che_do] = tot
    a = (ra["chang"].get("nghien_cuu") or {}).get("nguong")
    b = (ra["chang"].get("giao_dich") or {}).get("nguong")
    if a and b:
        ra["khoang_cach"] = round(b - a, 3)
        ra["y_nghia"] = (
            f"Chuoi dai thay duoc edge tu Sharpe {a}; chuoi mua duoc chi thay tu "
            f"{b}. Moi co che nam GIUA hai so nay la thu ma he PHAT HIEN duoc "
            f"nhung CHUA CHUNG NHAN duoc - do la hang doi bac cau, khong phai "
            f"ket luan am tinh.")
    return ra


def bao_cao_luc(ma: str = "EURCAD", khung: str = "H4") -> dict:
    """Goi tron: duong cong luc + luc theo do dai + ngoai suy, va ghi so cai."""
    cong = duong_cong_luc(ma, khung)
    if cong.get("loi"):
        return cong
    dai = luc_theo_do_dai(ma, khung)
    nguong = cong.get("sharpe_nho_nhat_thay_duoc")
    ra = {
        "tai_san": ma, "khung": khung,
        "sharpe_nho_nhat_thay_duoc": nguong,
        "alpha_nho_nhat_thay_duoc": cong.get("alpha_nho_nhat_thay_duoc"),
        "theo_do_dai": dai.get("muc"),
        "nam_can_cho_sharpe_0_5": nam_can_de_thay(0.5),
        "nam_can_cho_sharpe_0_8": nam_can_de_thay(0.8),
    }
    # Loi the khi gop phai dua tren rho DA DO, khong duoc gia dinh doc lap.
    for ten, loai in (("chi_so_my", ["chi_so_my"]), ("fx", ["fx"]),
                      ("tat_ca", ["chi_so_my", "fx", "vang"])):
        do = do_rho_thuc_te(loai, khung)
        ra[f"gop_{ten}"] = do
        if nguong and do.get("loi_the"):
            ra[f"nguong_khi_gop_{ten}"] = round(float(nguong) / do["loi_the"], 3)
    # LUC cua CA DAY CHUYEN, khong phai luc tren mot cap. Tu khi be mat kham
    # pha co chuoi 25-56 nam, do luc tren mot cap FX 5 nam roi bao "he thieu
    # luc" la ket luan ve cap do chu khong phai ve he.
    try:
        ra["hai_chang"] = luc_hai_chang()
    except Exception as e:
        ra["hai_chang"] = {"loi": f"{type(e).__name__}: {str(e)[:80]}"}
    tot_nhat = None
    for _cd, v in (ra["hai_chang"].get("chang") or {}).items():
        if v and (tot_nhat is None or v["nguong"] < tot_nhat["nguong"]):
            tot_nhat = v
    if nguong:
        SO.ghi_chi_so("sharpe_nho_nhat_thay_duoc", float(nguong), ra)
    if tot_nhat:
        SO.ghi_chi_so("sharpe_nho_nhat_thay_duoc_tot_nhat", tot_nhat["nguong"],
                      {"tren": tot_nhat, "hai_chang": ra["hai_chang"]})
        if tot_nhat["nguong"] > 1.0:
            SO.bao_van_de(
                "cong_thieu_luc", "VUA",
                f"Cho TOT NHAT cua ca be mat ({tot_nhat['tai_san']} "
                f"{tot_nhat['khung']}) van chi thay duoc edge tu Sharpe "
                f"{tot_nhat['nguong']}. Edge THAT cua FX/chi so sau phi thuong "
                f"nam o 0,3-0,8, nen moi ket luan am tinh chi co nghia 'khong "
                f"co edge LON', khong co nghia 'khong co edge'.", ra)
        else:
            SO.dong_van_de(
                "cong_thieu_luc",
                f"nguong tot nhat da ve {tot_nhat['nguong']} tren "
                f"{tot_nhat['tai_san']} {tot_nhat['khung']} - chuoi dai da vao "
                f"be mat kham pha. Chang giao dich van o "
                f"{(ra['hai_chang'].get('chang', {}).get('giao_dich') or {}).get('nguong')}.")
    return ra


if __name__ == "__main__":
    import pprint
    pprint.pprint(bao_cao_luc())
