# -*- coding: utf-8 -*-
"""pmg_g0.py - CONG G0 cua PMG. Do TINH CHAT QUA TRINH GIA truoc khi viet engine.

## Vi sao cong nay dung TRUOC moi thu

Dac ta muc 0 va muc 6: engine PMG khong co tin hieu vao, nen duoi random walk ky
vong cua no bang dung `-chi phi`. Suy ra no chi sinh loi neu **qua trinh gia co
bat doi xung that o dung timescale cua buoc luoi**. Cau hoi do tra loi duoc bang
mot thong ke re tien, khong can engine:

    ER(h) = |P_cuoi - P_dau| / sum|dP|      do tren cua so chua trung binh N bac luoi

    ER thuc > null  ->  co trend persistence o scale do  ->  chi `WITH` dang test
    ER thuc < null  ->  hoi quy ve trung binh            ->  chi `AGAINST` dang test
    khong khac null ->  **loai ca (tai san x scale) khoi toan bo ho PMG**

Bang nay cat >80% khong gian tham so truoc khi ton mot giay backtest, va no la co
che duy nhat giu cho tong so phep kiem o G5 khong no tung (dac ta muc 8.5).

## Hai thu de lam sai o day, da chan san

1. **Cua so phai theo BAC LUOI, khong theo so bar.** `h` la mot khoang cach gia,
   nen cua so phai dai vua du de gia di het ~N bac. Lay mot so bar co dinh cho moi
   `h` thi ER cua `h` nho va `h` lon khong so duoc voi nhau - va bang nhiet se do
   dung cai do chu khong do thi truong. `_cua_so_cho_h` do so bar can bang chinh
   chuoi.
2. **Null phai giu cum bien dong MA van giet duoc chieu huong.** Hai cach hien
   nhien deu sai va ca hai da duoc do: hoan vi tung bar pha vol clustering; block
   bootstrap thi giu luon **trung binh cua khoi** - dung cai ma ER do. Null mac
   dinh o day la **dao dau ngau nhien** (`_null_dao_dau`): giu nguyen `|dP|` tung
   vi tri nen mau so cua ER khong doi mot chut nao, chi giet chieu. Xem docstring
   cua ham do de biet hai lan sai truoc no.

## So loai tru (dac ta muc 8.6)

Moi o chet ghi mot dong. Phan biet ro:
  - chet o **G0** = ket luan ve THI TRUONG, ben vung, dong vinh vien
  - chet o **G3** = ket luan ve ENGINE, mo lai duoc neu engine doi
Hai loai khong duoc tron; `ghi_loai_tru` bat khai bao `cong` nen khong tron duoc.

Chay:  python -m nhan.pmg_g0 --ma US500CASH --khung M5
       python -m nhan.pmg_g0 --bang
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))
    from nhan import pmg as PMG
    from nhan import pmg_engine as PE
else:
    from . import pmg as PMG
    from . import pmg_engine as PE

RA = LAB / "reports"
SO_LOAI_TRU = RA / "PMG_SO_LOAI_TRU.json"
BANG_G0 = RA / "PMG_G0.json"

#: so bac luoi ma mot cua so ER phai chua. Nho qua thi ER nhieu; lon qua thi moi
#: cua so trum ca mot che do thi truong khac nhau va ER ve gan 0 voi moi tai san.
BAC_MOI_CUA_SO = 10
SO_NULL = 200
HAT = 4242
MUC_FDR = 0.10


def _er(gia: np.ndarray) -> float:
    """Efficiency Ratio cua mot doan gia."""
    d = np.abs(np.diff(gia))
    t = d.sum()
    return abs(gia[-1] - gia[0]) / t if t > 0 else np.nan


def _er_cac_cua_so(gia: np.ndarray, L: int) -> np.ndarray:
    """ER tren cac cua so KHONG chong nhau do dai L. Vector hoa."""
    m = len(gia) // L
    if m < 3:
        return np.array([])
    g = gia[:m * L].reshape(m, L)
    d = np.abs(np.diff(g, axis=1)).sum(axis=1)
    net = np.abs(g[:, -1] - g[:, 0])
    with np.errstate(divide="ignore", invalid="ignore"):
        er = np.where(d > 0, net / d, np.nan)
    return er[np.isfinite(er)]


def _cua_so_cho_h(gia: np.ndarray, buoc: float) -> int:
    """So bar sao cho quang duong trung binh cua cua so ~ BAC_MOI_CUA_SO * buoc.

    Do bang chinh chuoi thay vi doan: quang duong moi bar = trung vi |dP|.
    """
    d = np.abs(np.diff(gia))
    tv = float(np.median(d[d > 0])) if (d > 0).any() else 0.0
    if tv <= 0:
        return 0
    return max(4, int(round(BAC_MOI_CUA_SO * buoc / tv)))


def _null_block(r: np.ndarray, so: int, hat: int = HAT, khoi: int | None = None) -> np.ndarray:
    """Block bootstrap CO XAO TRONG KHOI - giu cum bien dong, giet tu tuong quan.

    Doan nay da sai mot lan va lan sai do dang duoc ghi lai, vi no la cai bay
    chung cua moi phep thu "co tu tuong quan khong":

        Block bootstrap THUAN lay nguyen ca khoi, nen no giu luon **tu tuong quan
        ben trong khoi**. Tuc null mang dung cai tinh chat ma ta dang di do.
        Do 14/09 tren chuoi AR(-0.35) dung san: ER thuc 0,0717 vs ER null 0,0708
        - gan nhu bang nhau, va G0 ket luan sai chieu (bao WITH cho mot chuoi hoi
        quy ro rang). Null nuot mat tin hieu.

    Nen o day: lay khoi de giu MUC bien dong cuc bo (cum bien dong song), roi
    **hoan vi ben trong tung khoi** de giet tu tuong quan. Khoi phai dai it nhat
    bang cua so ER, neu khong tu tuong quan tam xa hon khoi van song sot.
    """
    rng = np.random.default_rng(hat)
    n = len(r)
    blk = int(khoi or max(20, int(round(n ** (1 / 3)))))
    blk = max(5, min(blk, max(5, n // 4)))
    nb = int(np.ceil(n / blk))
    dau = rng.integers(0, max(1, n - blk), size=(so, nb))
    idx = (dau[:, :, None] + np.arange(blk)[None, None, :])       # (so, nb, blk)
    mau = r[np.clip(idx, 0, n - 1)]
    # hoan vi trong tung khoi
    thu_tu = rng.random(mau.shape).argsort(axis=2)
    mau = np.take_along_axis(mau, thu_tu, axis=2)
    return mau.reshape(so, -1)[:, :n]


def _null_dao_dau(r: np.ndarray, so: int, hat: int = HAT, khoi=None) -> np.ndarray:
    """NULL MAC DINH: giu nguyen |r| dung cho cua no, chi DAO DAU ngau nhien.

    Day la null dung cho ER, va li do thi dang sau hai lan lam sai truoc no:

      lan 1 - block bootstrap THUAN: giu nguyen ca khoi nen giu luon tu tuong
              quan ben trong khoi. Null mang dung tinh chat dang di do.
      lan 2 - block bootstrap CO XAO TRONG KHOI: giet duoc tu tuong quan (ac1 tu
              0,60 xuong 0,03 - da do) nhung **van giu TRUNG BINH cua khoi**. Ma
              trung binh khoi chinh la `|P_cuoi - P_dau|` cua cua so ER khi khoi
              dai bang cua so. Do 14/09 tren chuoi AR(0,6) dung san: ER thuc
              0,2011 vs ER null 0,2006 - null nuot tron tin hieu lan thu hai.

    Dao dau giai ca hai cung luc, va giai chinh xac chu khong xap xi:

        MAU SO cua ER la sum|dP| - dao dau KHONG doi no mot chut nao, nen cum
        bien dong duoc giu nguyen ven *dung tung vi tri thoi gian*, khong phai
        "giu gan giong" nhu block bootstrap.
        TU SO la |sum dP| - dao dau giet sach moi chieu huong o MOI tam xa.

    Tuc phep thu tro thanh dung mot cau hoi: *voi dung duong bien dong nay, cai
    thu tu dau ma thi truong da di co cho ra net move khac voi ngau nhien khong?*
    """
    rng = np.random.default_rng(hat + 3)
    dau = rng.integers(0, 2, size=(so, len(r))) * 2 - 1
    return r[None, :] * dau


def _null_gbm(r: np.ndarray, so: int, hat: int = HAT) -> np.ndarray:
    """GBM cung sigma - khong co cum bien dong, la ban doi chieu."""
    rng = np.random.default_rng(hat + 1)
    return rng.normal(0.0, float(np.std(r)), size=(so, len(r)))


NULL = {"dao_dau": _null_dao_dau, "block": _null_block, "gbm": _null_gbm}


def do_mot_o(gia: np.ndarray, h_atr: float, atr_tv: float, so_null: int = SO_NULL,
             hat: int = HAT, kieu_null: str = "dao_dau") -> dict:
    """ER thuc vs null cho MOT o (mot tai san x mot h x mot phien).

    `gia` la chuoi gia (mot chieu), `h_atr` boi so ATR, `atr_tv` ATR trung vi.
    """
    buoc = h_atr * atr_tv
    L = _cua_so_cho_h(gia, buoc)
    if L <= 0 or len(gia) < L * 6:
        return {"trang_thai": "CHUA_DO_DUOC",
                "ly_do": f"can >= {L*6} bar cho cua so {L}, chi co {len(gia)}"}
    er_thuc = _er_cac_cua_so(gia, L)
    if len(er_thuc) < 10:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": f"chi {len(er_thuc)} cua so"}
    tv_thuc = float(np.median(er_thuc))

    lr = np.diff(np.log(gia))
    lr = lr[np.isfinite(lr)]
    if kieu_null not in NULL:
        raise ValueError(f"kieu_null la gi: {kieu_null} (co: {sorted(NULL)})")
    # SINH TUNG CHUOI MOT, khong sinh ca ma tran (so_null, n).
    # Voi EURGBP M5 (1,0 trieu bar) x 200 null thi ma tran do la 1,6 GB va tien
    # trinh treo im lang - khong bao loi, chi la khong bao gio xong. Lo mo hinh
    # nay lap lai o moi cho "vector hoa cho nhanh" tren chuoi khung nho.
    g0 = float(gia[0])
    tv_null = np.empty(so_null)
    for i in range(so_null):
        mau_i = (NULL[kieu_null](lr, 1, hat + i * 7919, khoi=max(20, L))
                 if kieu_null == "block" else NULL[kieu_null](lr, 1, hat + i * 7919))[0]
        gn = g0 * np.exp(np.cumsum(mau_i))
        e = _er_cac_cua_so(gn, L)
        tv_null[i] = np.median(e) if len(e) else np.nan
    tv_null = tv_null[np.isfinite(tv_null)]
    if len(tv_null) < so_null * 0.5:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "null sinh khong du"}

    tren = float((tv_null >= tv_thuc).mean())
    duoi = float((tv_null <= tv_thuc).mean())
    p = min(1.0, 2.0 * min(tren, duoi))
    return {
        "trang_thai": "DO_DUOC",
        "er_thuc": tv_thuc,
        "er_null_tv": float(np.median(tv_null)),
        "er_null_do_lech": float(np.std(tv_null)),
        "z": ((tv_thuc - float(np.median(tv_null))) / float(np.std(tv_null))
              if np.std(tv_null) > 0 else 0.0),
        "p": p,
        "so_cua_so": int(len(er_thuc)),
        "bar_moi_cua_so": int(L),
        "kieu_null": kieu_null,
        # huong CHI la de xuat; quyen phan xu thuoc ve FDR o `chay_bang`
        "huong_de_xuat": "WITH" if tv_thuc > float(np.median(tv_null)) else "AGAINST",
    }


def fdr_bh(cac_p: list[float], muc: float = MUC_FDR) -> list[bool]:
    """Benjamini-Hochberg. Tra ve mang bool CUNG THU TU voi dau vao."""
    n = len(cac_p)
    if n == 0:
        return []
    thu_tu = np.argsort(cac_p)
    p = np.asarray(cac_p, float)[thu_tu]
    nguong = muc * (np.arange(1, n + 1) / n)
    duoi = p <= nguong
    k = np.max(np.nonzero(duoi)[0]) + 1 if duoi.any() else 0
    ra = np.zeros(n, bool)
    if k:
        ra[thu_tu[:k]] = True
    return ra.tolist()


# ------------------------------------------------------------------ BANG NHIET
CAC_H = (0.1, 0.2, 0.3, 0.5, 0.8, 1.2, 2.0, 3.0)


def chay_bang(cac_ma: list[str], khung: str = "M5", atr_tf: str = "H1",
              cac_h=CAC_H, cac_phien=("ALL",), so_null: int = SO_NULL,
              in_ra=print) -> dict:
    """Ban do nhiet ER(tai san, h, phien) + phan xu FDR-BH tren TOAN BO o.

    Day la dau ra so 1 cua dac ta (muc 7.1): *"vung nao cua khong gian tham so
    con song sau G0"*.
    """
    from nhan import du_lieu as DL
    t0 = time.time()
    o_het = []
    for ma in cac_ma:
        try:
            df = DL.nap(ma, khung)
        except Exception as ex:
            in_ra(f"  {ma:16s} BO QUA: {ex}")
            continue
        if len(df) < 500:
            in_ra(f"  {ma:16s} BO QUA: chi {len(df)} bar {khung}")
            continue
        try:
            a = PE.atr_khung(df, atr_tf, 14)
        except Exception as ex:
            in_ra(f"  {ma:16s} BO QUA: ATR {atr_tf}: {ex}")
            continue
        atr_tv = float(np.nanmedian(a))
        bien_do = float(np.median(df["high"] - df["low"]))
        buc = PMG.bucket_phien(df.index)
        gia_het = np.asarray(df["close"], float)
        for phien in cac_phien:
            if phien == "ALL":
                gia = gia_het
            else:
                gia = gia_het[buc == phien]
                if len(gia) < 500:
                    continue
            for h in cac_h:
                r = do_mot_o(gia, h, atr_tv, so_null)
                r.update({"ma": ma, "khung": khung, "atr_tf": atr_tf, "h": h,
                          "phien": phien, "so_bar": int(len(gia)),
                          "atr_trung_vi": atr_tv, "bien_do_nen": bien_do,
                          "buoc_tren_bien_do": h * atr_tv / bien_do if bien_do else 0.0})
                o_het.append(r)
        in_ra(f"  {ma:16s} {khung} {len(df):>8} bar  ATR({atr_tf}) {atr_tv:.5f}  "
              f"bien do nen {bien_do:.5f}")

    do_duoc = [r for r in o_het if r["trang_thai"] == "DO_DUOC"]
    dat = fdr_bh([r["p"] for r in do_duoc], MUC_FDR)
    for r, d in zip(do_duoc, dat):
        r["qua_fdr"] = bool(d)
        r["ket_luan"] = r["huong_de_xuat"] if d else "LOAI"
    for r in o_het:
        r.setdefault("qua_fdr", False)
        r.setdefault("ket_luan", "CHUA_DO_DUOC")

    bang = {
        "luc": time.strftime("%Y-%m-%d %H:%M:%S"),
        "giay": round(time.time() - t0, 1),
        "khung_chay": khung, "atr_tf": atr_tf,
        "muc_fdr": MUC_FDR, "so_null": so_null, "bac_moi_cua_so": BAC_MOI_CUA_SO,
        "so_o": len(o_het),
        "so_o_do_duoc": len(do_duoc),
        "so_o_song": sum(1 for r in o_het if r.get("qua_fdr")),
        "o": o_het,
    }
    RA.mkdir(parents=True, exist_ok=True)
    BANG_G0.write_text(json.dumps(bang, ensure_ascii=False, indent=1), encoding="utf-8")
    return bang


def in_bang(bang: dict, in_ra=print) -> None:
    """Ban do nhiet doc duoc: hang = tai san x phien, cot = h."""
    o = bang["o"]
    if not o:
        in_ra("khong co o nao")
        return
    cac_h = sorted({r["h"] for r in o})
    khoa = sorted({(r["ma"], r["phien"]) for r in o})
    in_ra("")
    in_ra(f"BAN DO G0 — ER thuc so voi null   ({bang['khung_chay']}, "
          f"ATR {bang['atr_tf']}, FDR-BH {bang['muc_fdr']:.0%}, "
          f"{bang['so_null']} chuoi null)")
    in_ra("  W = trend persistence (chi WITH dang test) · A = hoi quy (chi AGAINST)")
    in_ra("  .  = khong khac null -> LOAI o nay khoi ho PMG · ?  = chua do duoc")
    in_ra("  in HOA = qua FDR; in thuong = huong de xuat nhung KHONG qua FDR")
    in_ra("")
    # Cot `qua FDR` khong thua. Phan biet `A` voi `a` bang mat, tren mot bang 8 cot,
    # la thao tac de sai - va no da sai that ngay 14/09: toi doc `w` thanh `W` roi
    # viet vao bao cao rang US100 co trend persistence qua FDR, trong khi no 0/8.
    # Mot con so dem ben canh thi khong doc nham duoc.
    in_ra(f"{'tai san / phien':<26}" + "".join(f"{h:>7g}" for h in cac_h)
          + f"{'qua FDR':>10}")
    hang_het = []
    for ma, ph in khoa:
        hang = f"{ma + ('' if ph == 'ALL' else ' ' + ph):<26}"
        dem_qua = 0
        for h in cac_h:
            r = next((x for x in o if x["ma"] == ma and x["phien"] == ph
                      and x["h"] == h), None)
            if r is None or r["trang_thai"] != "DO_DUOC":
                k = "?"
            elif r["qua_fdr"]:
                k = "W" if r["ket_luan"] == "WITH" else "A"
                dem_qua += 1
            else:
                k = "w" if r["huong_de_xuat"] == "WITH" else "a"
            hang += f"{k:>7}"
        hang_het.append((dem_qua, f"{hang}{dem_qua:>6}/{len(cac_h)}"))
    for _, hang in sorted(hang_het, key=lambda x: -x[0]):
        in_ra(hang)
    in_ra("")
    in_ra(f"  {bang['so_o_song']}/{bang['so_o']} o song qua FDR · "
          f"{bang['so_o_do_duoc']} o do duoc · {bang['giay']}s")


# ----------------------------------------------------------------- SO LOAI TRU
def ghi_loai_tru(dong: dict) -> None:
    """Mot o chet = mot dong. `cong` BAT BUOC va phai la G0 hoac G3+.

    Vi sao bat buoc: chet o G0 la ket luan ve THI TRUONG (dong vinh vien duoc),
    chet o G3 la ket luan ve ENGINE (mo lai duoc khi engine doi). Tron hai loai
    nay lai thi so loai tru mat gia tri - no se hoac chan nham mot huong con song,
    hoac mo lai mot huong da chet han.
    """
    can = {"ma", "phien", "atr_tf", "h", "direction", "cong", "thong_ke", "gia_tri"}
    thieu = can - set(dong)
    if thieu:
        raise ValueError(f"dong loai tru thieu truong: {sorted(thieu)}")
    if dong["cong"] not in ("G0", "G1", "G2", "G3", "G4", "G5", "G6"):
        raise ValueError(f"cong khong hop le: {dong['cong']}")
    dong["vinh_vien"] = (dong["cong"] == "G0")
    dong.setdefault("luc", time.strftime("%Y-%m-%d %H:%M:%S"))
    so = doc_loai_tru()
    so.append(dong)
    RA.mkdir(parents=True, exist_ok=True)
    SO_LOAI_TRU.write_text(json.dumps(so, ensure_ascii=False, indent=1), encoding="utf-8")


def doc_loai_tru() -> list[dict]:
    if not SO_LOAI_TRU.exists():
        return []
    try:
        return json.loads(SO_LOAI_TRU.read_text(encoding="utf-8"))
    except Exception:
        return []


def da_bi_loai(ma: str, phien: str, atr_tf: str, h: float,
               direction: str = "") -> dict | None:
    """O nay da bi dong VINH VIEN chua? Chi `G0` moi chan duoc."""
    for d in doc_loai_tru():
        if not d.get("vinh_vien"):
            continue
        if (d["ma"] == ma and d["phien"] == phien and d["atr_tf"] == atr_tf
                and abs(float(d["h"]) - float(h)) < 1e-9
                and (not direction or not d["direction"] or d["direction"] == direction)):
            return d
    return None


def nap_ket_qua_vao_so(bang: dict, in_ra=print) -> int:
    """Moi o LOAI trong bang G0 -> mot dong trong so loai tru. Tra ve so dong them."""
    them = 0
    for r in bang["o"]:
        if r.get("ket_luan") != "LOAI":
            continue
        if da_bi_loai(r["ma"], r["phien"], r["atr_tf"], r["h"]):
            continue
        ghi_loai_tru({
            "ma": r["ma"], "phien": r["phien"], "atr_tf": r["atr_tf"], "h": r["h"],
            "direction": "", "cong": "G0", "thong_ke": "ER trung vi vs null",
            "gia_tri": {"er_thuc": r["er_thuc"], "er_null_tv": r["er_null_tv"],
                        "z": r["z"], "p": r["p"]},
            "khoang_du_lieu": f"{r['so_bar']} bar {r['khung']}",
            "ghi_chu": "khong khac null -> ca ho PMG khong co gi de khai thac o scale nay",
        })
        them += 1
    in_ra(f"so loai tru: them {them} dong (tong {len(doc_loai_tru())})")
    return them


def _cli(argv: list[str]) -> int:
    import argparse
    p = argparse.ArgumentParser(prog="pmg_g0")
    p.add_argument("--ma", nargs="*", default=["US500CASH", "XM_US500CASH",
                                               "XM_US100CASH", "XAUUSDM", "EURGBP"])
    p.add_argument("--khung", default="M5")
    p.add_argument("--atr-tf", default="H1")
    p.add_argument("--phien", nargs="*", default=["ALL"])
    p.add_argument("--null", type=int, default=SO_NULL)
    p.add_argument("--ghi-so", action="store_true", help="nap o LOAI vao so loai tru")
    a = p.parse_args(argv)
    b = chay_bang(a.ma, a.khung, a.atr_tf, CAC_H, tuple(a.phien), a.null)
    in_bang(b)
    if a.ghi_so:
        nap_ket_qua_vao_so(b)
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
