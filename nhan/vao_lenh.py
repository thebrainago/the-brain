# -*- coding: utf-8 -*-
"""vao_lenh.py - CAU TRUC VAO LENH nhieu chan. Nua con thieu cua module quan tri.

Muc Q4 cua `KE_HOACH_HOAN_THIEN.md`. Chu du an viet trong `SO_DO_HE_THONG.txt`:

    "module nay nghien cuu atr, trailingstop, hedging, buy sell stop 2 dau,
     1 dau danh lenh thi truong va lenh stop hedge doi dien o dau doi dien,
     dca, dca tinh toan von, hoac danh nhanh chot nhanh"

`dap_quan_tri.py` lam nua SAU cua cau do (SL/TP/trailing/dat hue - nhung gi xay ra
SAU khi da vao). File nay lam nua TRUOC: **hinh dang cua chinh cai vao lenh**.
Do la thu `dap_quan_tri` khong the bieu dien, vi no gia dinh MOT vi the mot luc,
con o day mot tin hieu co the sinh ra hai chan song song nguoc chieu nhau.

## BA LOI PHAI TRANH, CA BA DEU DA DO DUOC TRONG DU AN

**1. Hedge khong duoc mien phi.** `mo_phong.chay` thu phi theo `|diff(v)|` voi `v`
la phoi nhiem RONG. Mo dong thoi mot chan mua va mot chan ban thi `v` khong doi
-> he thu 0 dong spread cho hai lenh that, va phi qua dem cung tinh tren v=0
trong khi ngoai doi tra ca hai chan. Neu khong sua thi CANG HEDGE CANG LAI, va
moi ket luan cua module nay se la ao. O day phi tinh tren KHOI LUONG GOP.

**2. Lenh cho khong duoc lam ngo khe gia.** Mot lenh buy stop dat o `muc` ma bar
sau MO O TREN `muc` thi khop o `open`, khong phai o `muc`. Bo qua dieu do la tang
khong cho he mot muc gia tot hon thuc te o dung nhung bar bien dong nhat - tuc o
dung cho cau truc nay song bang.

**3. DCA phong to von KHONG phai la DCA.** Memory `lottery-mode-session-v3`: nhan
lot sau moi lan thua (x1,3) bien +54.354 / DD 30% thanh -1.550 / **DD 94,4%**.
Nen o day moi bac thang deu chia sao cho TONG phoi nhiem khi day du thang van
bang 1,0 - giong het mot lenh thi truong don. Co vay thi so sanh moi co nghia:
cung mot muc rui ro toi da, hinh dang nao ra tien hon.

## VA MOT LOI NUA - CUA CHINH FILE `dap_quan_tri.py`, DO DUOC 12/09/2026

`dap()` tinh SL/TP tu `open[i+1]` nhung tra ve `vi_the[i+1]`, roi `mo_phong.chay`
DICH THEM MOT BAR nua (`v[1:] = th[:-1]`). Ket qua: vi the that su an loi suat cua
bar **i+2**. Do bang chuoi dung san (nhay +9,3% o bar 5, tin hieu bar 3, giu 1
bar): he an dung cu nhay cua bar 5 trong khi phan dung cua no la -0,14% cua bar 4.

Nen file nay KHONG di qua `mo_phong.chay`. No tu tinh tien theo loi suat
**OPEN-TO-OPEN** giong `mo_phong.chay_tpsl` - vao o `open[j]` thi an tu `open[j]`,
khong nhan khe gia truoc luc vao, khong mat bar nao.

## BAY CAU TRUC

    thi_truong    vao thi truong o open[i+1]                  (moc doi chieu)
    hai_dau_oco   buy stop tren + sell stop duoi, ai khop truoc thi huy cai kia
    hai_dau_giu   nhu tren nhung KHONG huy - khop ca hai thi thanh hedge
    tt_hedge      lenh thi truong + stop nguoc chieu lam hedge o dau doi dien
    dca_deu       vao dan deu moi khi gia di nguoc mot buoc ATR
    dca_von       vao dan voi trong so TANG DAN, tong van bang 1,0
    nhanh         vao thi truong, TP = SL = nho, ra ngay

`hai_dau_*` KHONG dung chieu cua tin hieu - tin hieu chi la LUC DAT LENH. Do la
dung ban chat cua cau truc do: no cuoc vao "sap co mot cu di manh", khong cuoc vao
huong nao.

Chay:  python -m nhan.vao_lenh [MA] [KHUNG]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

CAU_TRUC = ("thi_truong", "hai_dau_oco", "hai_dau_giu", "tt_hedge",
            "dca_deu", "dca_von", "nhanh")

#: Tham so mac dinh. Moi cai mot Y TUONG chu khong phai mot luoi tham so - muc
#: dich la tra loi "hinh dang nao ra tien", khong phai tim so dep nhat.
MAC_DINH = {
    "k_dat": 0.5,        # khoang cach dat lenh cho, tinh bang ATR
    "han_bar": 5,        # lenh cho song may bar roi huy
    "sl_atr": 2.0,
    "tp_atr": 4.0,
    "d_hedge": 1.0,      # khoang cach dat chan hedge doi dien
    "buoc_dca": 1.0,     # moi buoc DCA cach nhau may ATR
    "so_nac": 3,         # so bac thang DCA
    "he_so_von": 1.5,    # bac sau nang hon bac truoc bao nhieu lan (dca_von)
    "sl_nhanh": 0.5,
    "tp_nhanh": 0.5,
}


def _atr(df: pd.DataFrame, n: int = 14) -> np.ndarray:
    h, l, c = (df["high"].to_numpy(float), df["low"].to_numpy(float),
               df["close"].to_numpy(float))
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.roll(c, 1)),
                                      np.abs(l - np.roll(c, 1))))
    tr[0] = h[0] - l[0]
    return pd.Series(tr).ewm(alpha=1.0 / n, adjust=False).mean().to_numpy()


def _khop_stop(chieu: float, muc: float, o: float, h: float, l: float):
    """Lenh STOP co khop trong bar nay khong, va khop o GIA NAO.

    Khe gia: bar mo o ngoai muc thi khop o `open`, khong phai o `muc`. Bo qua
    dieu nay la tu tang cho he mot muc gia tot hon thuc te o dung nhung bar
    bien dong manh nhat - noi cau truc breakout song bang.
    """
    if chieu > 0:
        if o >= muc:
            return o
        return muc if h >= muc else None
    if o <= muc:
        return o
    return muc if l <= muc else None


def _khop_limit(chieu: float, muc: float, o: float, h: float, l: float):
    """Lenh LIMIT co khop khong, va o gia nao.

    DCA mua them o gia THAP HON la lenh LIMIT chu khong phai STOP. Neu dung
    `_khop_stop` cho no thi dieu kien `high >= muc` voi `muc` nam DUOI gia hien
    tai luon dung -> moi bac thang khop het ngay bar dau, va "DCA" bien thanh
    "vao het mot lan" ma khong bao gi.
    Khe gia co loi cho limit: mo o duoi muc mua thi khop o `open` (re hon).
    """
    if chieu > 0:
        if o <= muc:
            return o
        return muc if l <= muc else None
    if o >= muc:
        return o
    return muc if h >= muc else None


def _trong_so_nac(cau_truc: str, so_nac: int, he_so: float) -> np.ndarray:
    """Trong so tung bac thang, TONG = 1,0.

    Rang buoc tong = 1 la co y (xem muc 3 o dau file): DCA khong duoc phep tro
    thanh "phong to von" roi thang moc thi truong nho phoi nhiem lon hon.
    """
    if cau_truc == "dca_von":
        w = np.array([he_so ** k for k in range(so_nac)], float)
    else:
        w = np.ones(so_nac, float)
    return w / w.sum()


def dap_cau_truc(df: pd.DataFrame, tin_hieu, cau_truc: str = "thi_truong",
                 tham: dict | None = None, giu_toi_da: int = 60,
                 atr_n: int = 14) -> dict:
    """Chay mot cau truc vao lenh len mot tin hieu. -> cac chuoi de tinh tien.

    Tra ve:
        loi_tho[j]   loi suat GOP cua moi chan song trong bar j (open-to-open)
        khoi_luong[j] tong khoi luong MO + DONG trong bar j  (de tinh spread)
        dai[j], ngan[j]  tong phoi nhiem mua / ban giu trong bar j (de tinh phi giu)
        vi_the[j]    phoi nhiem RONG = dai - ngan  (chi de bao cao)
    """
    if cau_truc not in CAU_TRUC:
        raise ValueError("cau truc khong biet: %s (co: %s)"
                         % (cau_truc, ", ".join(CAU_TRUC)))
    t = dict(MAC_DINH); t.update(tham or {})
    xau = [k for k in (tham or {}) if k not in MAC_DINH]
    if xau:
        raise KeyError("tham so khong biet: %s" % xau)

    o = df["open"].to_numpy(float)
    h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float)
    atr = _atr(df, atr_n)
    n = len(df)
    th = np.nan_to_num(np.asarray(tin_hieu, float).reshape(-1), nan=0.0)
    if len(th) != n:
        raise ValueError("tin hieu dai %d nhung du lieu %d bar" % (len(th), n))

    loi_tho = np.zeros(n)
    khoi = np.zeros(n)
    dai = np.zeros(n)
    ngan = np.zeros(n)
    lenh: list[dict] = []
    so_su_kien = 0

    i = 0
    while i < n - 2:
        if abs(th[i]) < 1e-12:
            i += 1
            continue
        vao_i = i + 1
        a = atr[vao_i]
        if not np.isfinite(a) or a <= 0:
            i += 1
            continue
        chieu_th = 1.0 if th[i] > 0 else -1.0
        so_su_kien += 1

        cho: list[dict] = []       # lenh cho: {chieu, muc, co, huy_bar, oco}
        song: list[dict] = []      # chan dang mo: {chieu, gia, co, sl, tp, bar}
        w = _trong_so_nac(cau_truc, int(t["so_nac"]), float(t["he_so_von"]))

        if cau_truc in ("thi_truong", "nhanh"):
            sl_k = t["sl_nhanh"] if cau_truc == "nhanh" else t["sl_atr"]
            tp_k = t["tp_nhanh"] if cau_truc == "nhanh" else t["tp_atr"]
            song.append({"chieu": chieu_th, "gia": o[vao_i], "co": 1.0,
                         "sl": o[vao_i] - chieu_th * sl_k * a,
                         "tp": o[vao_i] + chieu_th * tp_k * a,
                         "bar": vao_i, "moi": True})
        elif cau_truc in ("hai_dau_oco", "hai_dau_giu"):
            # Khong dung chieu tin hieu: cuoc vao "sap co cu di manh".
            tren = h[i] + t["k_dat"] * a
            duoi = l[i] - t["k_dat"] * a
            for ch, muc in ((1.0, tren), (-1.0, duoi)):
                cho.append({"chieu": ch, "muc": muc, "co": 1.0, "loai": "stop",
                            "huy_bar": vao_i + int(t["han_bar"]),
                            "oco": cau_truc == "hai_dau_oco"})
        elif cau_truc == "tt_hedge":
            song.append({"chieu": chieu_th, "gia": o[vao_i], "co": 1.0,
                         "sl": None,     # KHONG cat lo - chan hedge thay vai tro do
                         "tp": o[vao_i] + chieu_th * t["tp_atr"] * a,
                         "bar": vao_i, "moi": True})
            cho.append({"chieu": -chieu_th, "loai": "stop",
                        "muc": o[vao_i] - chieu_th * t["d_hedge"] * a,
                        "co": 1.0, "huy_bar": vao_i + giu_toi_da, "oco": False})
        else:   # dca_deu / dca_von
            song.append({"chieu": chieu_th, "gia": o[vao_i], "co": float(w[0]),
                         "sl": None,
                         "tp": o[vao_i] + chieu_th * t["tp_atr"] * a,
                         "bar": vao_i, "moi": True})
            for k in range(1, int(t["so_nac"])):
                cho.append({"chieu": chieu_th, "loai": "limit",
                            "muc": o[vao_i] - chieu_th * k * t["buoc_dca"] * a,
                            "co": float(w[k]),
                            "huy_bar": vao_i + giu_toi_da, "oco": False})

        # giu_toi_da = SO BAR duoc giu, nen bar cuoi la vao_i + giu_toi_da - 1.
        # `dap_quan_tri` dung dung nghia do (`(j - vao_i) < tran_bar`); lech mot
        # bar o day thi hai ho khong so voi nhau duoc.
        het = min(vao_i + giu_toi_da - 1, n - 1)
        j = vao_i
        while j <= het:
            gia_dau = {}          # id(chan) -> gia bat dau tinh trong bar j
            for ch in song:
                gia_dau[id(ch)] = ch["gia"] if ch.pop("moi", False) else o[j]

            # --- 1) LENH CHO KHOP (sau bar dat lenh moi co hieu luc)
            if True:
                khop = []
                for p in cho:
                    if j > p["huy_bar"]:
                        continue
                    ham = _khop_limit if p["loai"] == "limit" else _khop_stop
                    g = ham(p["chieu"], p["muc"], o[j], h[j], l[j])
                    if g is not None:
                        khop.append((abs(o[j] - p["muc"]), p, g))
                # hai lenh cung khop trong mot bar: cai GAN OPEN hon den truoc
                khop.sort(key=lambda x: x[0])
                for _, p, g in khop:
                    if p not in cho:
                        continue          # da bi OCO huy o vong truoc
                    if p.get("oco"):
                        cho[:] = [x for x in cho if not x.get("oco")]
                    else:
                        cho.remove(p)
                    sl_k, tp_k = t["sl_atr"], t["tp_atr"]
                    song.append({"chieu": p["chieu"], "gia": g, "co": p["co"],
                                 "sl": (g - p["chieu"] * sl_k * a
                                        if cau_truc != "tt_hedge" else None),
                                 "tp": g + p["chieu"] * tp_k * a,
                                 "bar": j})
                    gia_dau[id(song[-1])] = g
                    khoi[j] += p["co"]
                cho[:] = [p for p in cho if j <= p["huy_bar"]]

            # --- 2) CHAN THOAT (chi kiem tu bar SAU bar vao, nhu dap_quan_tri)
            con = []
            for ch in song:
                if ch["bar"] >= j:
                    con.append(ch)
                    continue
                c_sl = ch["sl"] is not None and (
                    (l[j] <= ch["sl"]) if ch["chieu"] > 0 else (h[j] >= ch["sl"]))
                c_tp = ch["tp"] is not None and (
                    (h[j] >= ch["tp"]) if ch["chieu"] > 0 else (l[j] <= ch["tp"]))
                gia_ra = None
                if c_sl and c_tp:
                    # TIE-BREAK bang open cua chinh bar do - CLAUDE.md muc 4.
                    gia_ra = (ch["tp"] if abs(o[j] - ch["tp"]) <= abs(o[j] - ch["sl"])
                              else ch["sl"])
                elif c_tp:
                    gia_ra = ch["tp"]
                elif c_sl:
                    gia_ra = ch["sl"]
                elif j == het and j + 1 < n:
                    gia_ra = o[j + 1]
                if gia_ra is None:
                    con.append(ch)
                    continue
                g0 = gia_dau[id(ch)]
                loi_tho[j] += ch["chieu"] * ch["co"] * np.log(max(gia_ra, 1e-12)
                                                              / max(g0, 1e-12))
                khoi[j] += ch["co"]
                lenh.append({"vao": int(ch["bar"]), "ra": int(j),
                             "chieu": int(ch["chieu"]), "co": round(ch["co"], 4),
                             "ly_do": ("tp" if gia_ra == ch["tp"] else
                                       "sl" if gia_ra == ch["sl"] else "het_gio")})
                if id(ch) in gia_dau:
                    gia_dau.pop(id(ch))
            song = con

            # --- 3) CHAN CON SONG: an loi suat den OPEN bar ke tiep
            if j + 1 < n:
                for ch in song:
                    g0 = gia_dau.get(id(ch), o[j])
                    loi_tho[j] += ch["chieu"] * ch["co"] * np.log(
                        max(o[j + 1], 1e-12) / max(g0, 1e-12))
                    if ch["chieu"] > 0:
                        dai[j] += ch["co"]
                    else:
                        ngan[j] += ch["co"]
            j += 1
            if not song and not cho:
                break

        # Chan nao con mo o day la do het cua so: dong o open bar ke tiep.
        #
        # PHAI GHI VAO SO LENH. Truoc 12/09/2026 cho nay chi cong khoi luong roi
        # thoi, nen voi `giu_toi_da = 1` KHONG lenh nao duoc ghi (chan mo o bar
        # cuoi cua so thi vong lap thoat truoc khi kiem thoat). `so_cau_truc` lai
        # loc `so_lenh < 15` -> **moi co che khai `giu = 1` bi loai sach**, va do
        # la 885/1460 co che cua kho (60,6%). Lo hong im lang: khong loi, chi la
        # hai phan ba khong gian bien mat khoi moi bang xep hang.
        for ch in song:
            khoi[min(j, n - 1)] += ch["co"]
            lenh.append({"vao": int(ch["bar"]), "ra": int(min(j, n - 1)),
                         "chieu": int(ch["chieu"]), "co": round(ch["co"], 4),
                         "ly_do": "het_cua_so"})
        i = max(j, vao_i + 1)

    vi_the = dai - ngan
    return {"loi_tho": np.nan_to_num(loi_tho, nan=0.0, posinf=0.0, neginf=0.0),
            "khoi_luong": khoi, "dai": dai, "ngan": ngan, "vi_the": vi_the,
            "so_lenh": len(lenh), "so_su_kien": so_su_kien, "lenh": lenh,
            "phoi_nhiem_gop": float(np.mean(dai + ngan))}


# --------------------------------------------------------------- TINH RA TIEN
def phi_mang(df: pd.DataFrame, r: dict, cp):
    """(spread, truot gia, phi giu) theo tung bar. Tinh tren GOP, khong tren RONG."""
    idx = df.index
    return (r["khoi_luong"] * cp.spread_mang(idx),
            r["khoi_luong"] * cp.truot_gia_frac,
            cp.phi_giu_mang(idx, r["dai"], None)
            + cp.phi_giu_mang(idx, -r["ngan"], None))


def tinh_tien(df: pd.DataFrame, r: dict, cp, ma: str = "", khung: str = ""):
    """Bien ket qua cau truc thanh `mo_phong.KetQua` de dung chung bo chi so.

    Phi tinh tren GOP, khong tren RONG:
      spread  = khoi luong MO + DONG that su (chan hedge tra ca hai lan)
      phi giu = phi cua chan mua CONG phi cua chan ban, tinh rieng
    """
    from nhan import mo_phong as MP
    idx = df.index
    phi_sp, phi_tr, phi_gi = phi_mang(df, r, cp)
    loi = r["loi_tho"] - phi_sp - phi_tr - phi_gi
    # Giu lai chuoi phi de `quy_ve_dd` chay lai duoc o don bay khac (phi nhan
    # theo don bay vi spread thu tren khoi luong). Dat vao chinh `r` chu khong
    # vao KetQua: KetQua la dataclass dung chung, khong nen phinh vi mot nguoi goi.
    r["_phi"] = phi_sp + phi_tr + phi_gi
    return MP.KetQua(
        ma=ma, khung=khung, index=idx, vi_the=r["vi_the"], loi=loi,
        loi_tho=r["loi_tho"], r=MP._loi_suat_tien(df),
        chi_phi_spread=float(np.nansum(phi_sp)),
        chi_phi_truot=float(np.nansum(phi_tr)),
        chi_phi_giu=float(np.nansum(phi_gi)),
        so_lan_doi=int(np.sum(r["khoi_luong"] > 1e-12)),
        so_lenh=r["so_lenh"],
        phoi_nhiem=float(np.mean(np.abs(r["vi_the"]))),
        canh_bao=list(cp.canh_bao))


NGAN_SACH_DD = 20.0


def moc_dd20(df: pd.DataFrame, cp, ma: str = "", khung: str = "D1") -> float:
    """Moc = max(mua-giu, ban-giu, tien mat), quy ve dd20 BANG CUNG MOT PHEP.

    Vi sao co ham rieng: 12/09/2026 toi doi cach quy cua HE sang chay lai o don
    bay that (`quy_ve_dd`) nhung de MOC o cong thuc nhan tuyen tinh cu. Hai ben
    khac don vi, va HE duoc loi - ti le "thang moc" o holdout vot len 29/35, mot
    con so khong tin duoc. Cung ho loi voi `so-cuc-dai-phai-so-cung-co-mau`.

    Voi he long/short thi lay MOT MINH mua-giu lam moc la sai (da sua 11/09):
    ban-giu khong phai anh guong cua mua-giu vi phi qua dem bat doi xung.

    KHONG TRUNG voi `cong_ra_tien.mua_giu_khop_dd`: ham do chi mua-giu va la
    MOT PHAN CUA CONG (di kem nguong MUC_CAGR/TRAN_DD/MIN_LENH/MIN_NAM); ham
    nay la MOC cua pheu, rong hon (co ban-giu + tien mat) va khong co nguong.
    Chi tiet o docstring dau `nhan/cong_ra_tien.py`.
    """
    from nhan import mo_phong as MP
    nam = so_nam_cua(df)
    ra = [0.0]
    for v in (1.0, -1.0):
        kq = MP.chay(df, np.full(len(df), v), cp, ma=ma, khung=khung,
                     don_bay=1.0, gop="so_hoc")
        phi = np.asarray(kq.loi_tho, float) - np.asarray(kq.loi, float)
        q = quy_ve_dd(kq.loi_tho, np.maximum(phi, 0.0), nam)
        if not q["chet"] and q["cagr"] is not None:
            ra.append(q["cagr"])
    return max(ra)


def so_nam_cua(df: pd.DataFrame) -> float:
    """So nam THAT cua chuoi, doc tu chi muc thoi gian."""
    idx = pd.DatetimeIndex(df.index)
    return max((idx[-1] - idx[0]).days / 365.25, 1e-9)


def _sut_giam(von: np.ndarray) -> float:
    dinh = np.maximum.accumulate(von)
    return float(np.max(1.0 - von / np.maximum(dinh, 1e-12)))


def quy_ve_dd(loi_log: np.ndarray, phi: np.ndarray, so_nam: float,
              dd_muc_tieu: float = NGAN_SACH_DD / 100.0,
              L_toi_da: float = 10.0) -> dict:
    """Quy mot he ve DUNG muc sut giam muc tieu bang cach CHAY LAI o don bay do.

    ## VI SAO KHONG NHAN TUYEN TINH

    Cach cu: `cagr_dd20 = cagr * (20 / maxdd)`. No gia dinh lai va sut giam deu
    ti le thuan voi don bay. Ca hai gia dinh do deu sai, va sai NANG NHAT o dung
    cho no duoc dung nhieu nhat - nhung he sut giam sau:

        GBPZAR `chot_nhanh_sl1_tp1`:  CAGR 591%/nam,  maxDD **-99,38%**
        -> nhan tuyen tinh cho 119%/nam o "dd20", va no LOT vao top bang xep hang

    maxDD -99,38% khong phai mot con so de chia - **do la mot tai khoan da chet**.
    Nhan cho 0,2 roi goi no la "he 20% sut giam" la mo ta mot he chua tung ton
    tai. Memory `don-bay-gop-log-sai`: gop kieu log lam bien mat ca luc can bien
    dong lan kha nang chay tai khoan, va tren 98 nam SP500 no cho von cuoi gap
    76 TRIEU lan su that.

    ## CACH DUNG

    Chay lai chuoi o don bay L voi gop SO HOC (`1 + L*r - L*phi`), do sut giam
    THAT o do, roi chia doi de tim L cho ra dung `dd_muc_tieu`. Phi nhan theo L
    vi spread thu tren khoi luong. He nao chay tai khoan o moi L > 0 thi tra ve
    `chet=True` chu khong tra mot con so.
    """
    ra = np.expm1(np.asarray(loi_log, float))
    ph = np.asarray(phi, float)
    nam = max(float(so_nam), 1e-9)

    def thu(L: float):
        song = 1.0 + L * ra - L * ph
        if np.any(song <= 0.0):
            return None                      # chay tai khoan o muc don bay nay
        von = np.cumprod(song)
        return _sut_giam(von), float(von[-1] ** (1.0 / nam) - 1.0)

    tren = thu(L_toi_da)
    if tren is not None and tren[0] <= dd_muc_tieu:
        return {"L": L_toi_da, "dd": tren[0], "cagr": tren[1], "chet": False,
                "cham_tran_L": True}
    lo, hi = 1e-4, L_toi_da
    d0 = thu(lo)
    if d0 is None:
        return {"L": None, "dd": None, "cagr": None, "chet": True,
                "cham_tran_L": False}
    if d0[0] > dd_muc_tieu:
        # ngay o don bay gan 0 van vuot muc sut giam -> khong quy duoc
        return {"L": lo, "dd": d0[0], "cagr": d0[1], "chet": False,
                "cham_tran_L": False, "khong_quy_duoc": True}
    for _ in range(60):
        giua = 0.5 * (lo + hi)
        r = thu(giua)
        if r is None or r[0] > dd_muc_tieu:
            hi = giua
        else:
            lo = giua
    r = thu(lo)
    return {"L": lo, "dd": r[0], "cagr": r[1], "chet": False,
            "cham_tran_L": False}


def so_cau_truc(df, tin_hieu, ma, khung, cac=None, giu_toi_da=60,
                tham: dict | None = None) -> list[dict]:
    """Chay TUNG cau truc tren CUNG mot tin hieu roi so bang TIEN o cung sut giam.

    Bien doc lap duy nhat la HINH DANG VAO LENH. Moc = max(mua-giu, ban-giu,
    tien mat) - voi he long/short thi chi lay mua-giu la SAI, da sua 11/09.
    """
    from nhan import bien_don_bay as B
    from nhan import chi_phi as CP
    from nhan import mo_phong as MP
    c = CP.tu_du_lieu(ma, df)
    cp = c[0] if isinstance(c, tuple) else c
    moc = moc_dd20(df, cp, ma, khung)
    ra = []
    for ten in (cac or CAU_TRUC):
        r = dap_cau_truc(df, tin_hieu, ten, tham, giu_toi_da=giu_toi_da)
        if r["so_lenh"] < 15:
            continue
        kq = tinh_tien(df, r, cp, ma=ma, khung=khung)
        hh = B._chi_so(kq)
        q = quy_ve_dd(kq.loi_tho, r["_phi"], so_nam_cua(df))
        dd20 = 0.0 if q["chet"] or q["cagr"] is None else q["cagr"] * 100.0
        dem = {}
        for x in r["lenh"]:
            dem[x["ly_do"]] = dem.get(x["ly_do"], 0) + 1
        ra.append({"ma": ma, "khung": khung, "cau_truc": ten,
                   # `so_nam` phai di THEO DONG. Thieu no thi `cham_diem` lay
                   # tong so lenh lam "lenh/nam" va moi dong deu vuot nguong
                   # 20 lenh/nam mot cach gia - cung ho benh voi
                   # `h.get("so_lenh")` tra None hom nay.
                   "so_nam": round(so_nam_cua(df), 2),
                   "su_kien": r["so_su_kien"], "so_chan": r["so_lenh"],
                   "gop_tb": round(r["phoi_nhiem_gop"], 4),
                   "cagr_pct": round(hh["cagr"] * 100, 3),
                   "sharpe": round(hh["sharpe"], 3),
                   "maxdd_pct": round(hh["maxdd"] * 100, 2),
                   "cagr_dd20": round(dd20, 3),
                   "don_bay_quy": None if q["L"] is None else round(q["L"], 4),
                   "chet_tai_khoan": bool(q["chet"]),
                   "moc_dd20": round(moc * 100, 3),
                   "hon_moc": bool(dd20 > moc * 100),
                   "phi_pct": round((kq.chi_phi_spread + kq.chi_phi_truot
                                     + kq.chi_phi_giu) * 100, 3),
                   "ly_do": dem})
    return ra


def main(argv: list[str]) -> int:
    from nhan import du_lieu as DL
    ma = argv[0] if argv else "EURUSD"
    khung = argv[1] if len(argv) > 1 else "D1"
    df = DL.nap(ma, khung)
    # Tin hieu doi chieu: nen trong ngoai (bien do lon hon bar truoc) - mot LUC
    # chu khong phai mot huong, dung voi cau truc hai dau.
    bd = (df["high"] - df["low"]).to_numpy(float)
    th = np.where(bd > pd.Series(bd).rolling(20).quantile(0.8).to_numpy(),
                  np.sign(df["close"].to_numpy(float) - df["open"].to_numpy(float)),
                  0.0)
    bang = so_cau_truc(df, th, ma, khung)
    print("%-13s %6s %6s %8s %9s %9s %9s %8s" %
          ("CAU TRUC", "SUKIEN", "CHAN", "SHARPE", "CAGR%", "DD%", "DD20%", "PHI%"))
    for d in sorted(bang, key=lambda x: -x["cagr_dd20"]):
        print("%-13s %6d %6d %8.3f %9.3f %9.2f %9.3f %8.3f%s"
              % (d["cau_truc"], d["su_kien"], d["so_chan"], d["sharpe"],
                 d["cagr_pct"], d["maxdd_pct"], d["cagr_dd20"], d["phi_pct"],
                 "  <- hon moc" if d["hon_moc"] else ""))
    if bang:
        print("\nmoc (max mua-giu/ban-giu/tien mat) o dd20: %.3f%%"
              % bang[0]["moc_dd20"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
