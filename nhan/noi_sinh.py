# -*- coding: utf-8 -*-
"""noi_sinh.py - LUONG 3. Tu sinh co che tu CHINH LICH SU cua ma, khong doi nguon ngoai.

Chu du an 03/09/2026: *"1 luong khac se tu tim cach nao test nguoc lich su de
ra duoc chien luoc cho us500cash hieu qua"*.

Khac han hai luong kia:
  - LUONG 1 (`muc_tieu.san`)  : nguoi ta da viet gi ve ma nay?
  - LUONG 2 (`quantlab`)      : nhung thu do co song tren du lieu cua ta khong?
  - LUONG 3 (file nay)        : **quen nguon ngoai di** - ghep co che tu chinh
                                bo tu vung cua ngu phap, va lay NGUONG tu phan
                                phoi that cua chuoi.

DIEM COT YEU - "TEST NGUOC LICH SU" NGHIA LA LAY NGUONG TU DU LIEU.
Mot co che nhap tu ngoai mang theo nguong cua tac gia: `rsi < 30`, `ibs < 0,2`,
`zscore < -2`. Nhung 30 la nguong cua ai, tren tai san nao, khung nao? Tren
US500CASH.H4 thi RSI cham 30 co the la 0,3% so bar - qua hiem de co thong ke,
hoac 12% - qua thuong de co edge.
O day nguong duoc lay tu **PHAN VI THAT cua chinh toan hang tren chinh chuoi
do**: "5% bar co RSI thap nhat" la mot cau hoi tra loi duoc tren moi tai san
va moi khung, con "RSI < 30" thi khong.

BA CHOT CHAN (khong duoc go):
  1. **Nguong lay tren TRAIN, khong lay tren ca chuoi.** Lay phan vi tren ca
     chuoi la nhin truoc: nguong da biet phan phoi cua holdout.
  2. **Moi spec deu qua `kiem_khai_bao` + `kiem_khong_nhin_truoc`** truoc khi
     duoc tra ve. Mot bo sinh tu dong ma khong co hai cai nay se de ra hang
     loat co che nhin truoc, va chung se trong nhu vang.
  3. **KHONG dang ky gia thuyet, KHONG cham FDR.** File nay chi SINH. Moi phep
     thu van phai di qua `cong` nhu co che nhap tu ngoai. Sinh de thi phai loc
     chat - do la ly do `sang_loc` chay ngay trong `mot_luot`.
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from nhan import ngu_phap as NP

#: Toan hang mot ngoi dung lam VE TRAI. Chon theo tieu chi: tinh duoc tren moi
#: khung, khong can doi so la, va co PHAN PHOI lien tuc de lay phan vi.
#: (`gio`/`thang`/`ngay_trong_tuan` khong vao day - chung roi rac, va `gio` con
#: bi chan tren khung khong co gio.)
TOAN_HANG_GOC = [
    {"chi_bao": "ibs"},
    {"chi_bao": "rsi", "cot": "close", "n": 14},
    {"chi_bao": "rsi", "cot": "close", "n": 4},
    {"chi_bao": "zscore", "cua": {"chi_bao": "gia", "cot": "close"}, "n": 20},
    {"chi_bao": "zscore", "cua": {"chi_bao": "gia", "cot": "close"}, "n": 60},
    {"chi_bao": "than_nen"},
    {"chi_bao": "bien_do"},
    {"chi_bao": "doi_pct", "cua": {"chi_bao": "gia", "cot": "close"}, "n": 1},
    {"chi_bao": "doi_pct", "cua": {"chi_bao": "gia", "cot": "close"}, "n": 5},
    {"chi_bao": "atr", "n": 14},
    {"chi_bao": "adx", "n": 14},
    {"chi_bao": "cci", "cot": "close", "n": 20},
    {"chi_bao": "stochastic", "n": 14},
    {"chi_bao": "dong_luong", "cot": "close", "n": 10},
    {"chi_bao": "phan_vi", "cua": {"chi_bao": "atr", "n": 14}, "n": 250},
    {"chi_bao": "phan_vi", "cua": {"chi_bao": "bien_do"}, "n": 100},
]

#: Phan vi lam nguong. Doi xung hai duoi de khong thien ve mot chieu.
PHAN_VI = (0.02, 0.05, 0.10, 0.20, 0.80, 0.90, 0.95, 0.98)

#: So bar giu vi the.
CAC_GIU = (1, 2, 3, 5, 10)


#: Moi toan hang phai khai HO va CAU CO CHE cua no. Cong ngu phap tu choi mot
#: khai bao khong noi duoc "vi sao co nguoi tra tien cho phoi nhiem nay"
#: (`kiem_khai_bao`), va do la chot chan DUNG: mot bo sinh tu dong khong duoc
#: phep de ra hang loat co che vo danh roi bat nguoi khac di tim y nghia sau.
#: Khoa: (ten_chi_bao, "thap" | "cao").
CO_CHE_CUA = {
    ("ibs", "thap"): ("quay_ve_trung_binh",
        "Dong cua o day bien do bar phan anh ban thao cuoi phien; nguoi mua "
        "cung cap thanh khoan cho ho duoc tra cong o bar ke tiep."),
    ("ibs", "cao"): ("xu_huong",
        "Dong cua o dinh bien do bar la dau hieu ben mua con hang cho khop; "
        "phan cau chua khop day tiep sang bar sau."),
    ("rsi", "thap"): ("quay_ve_trung_binh",
        "Chuoi bar giam lien tiep day suc ep ban toi han; ai chiu om vi the "
        "luc do doi duoc tra phan bu va nhan no khi nguoi khac phai ban."),
    ("rsi", "cao"): ("xu_huong",
        "Suc mua ap dao keo dai the hien dong von co to chuc, va dong von do "
        "thuong duoc giai ngan dan chu khong het trong mot bar."),
    ("zscore", "thap"): ("quay_ve_trung_binh",
        "Gia lech xa trung binh xuong duoi thuong do lenh ban buoc phai khop "
        "ngay; ben nhan phia doi dien doi duoc chiet khau va thu lai sau do."),
    ("zscore", "cao"): ("xu_huong",
        "Gia thoat len khoi vung can bang keo theo lenh dong vi the ban va "
        "lenh mua duoi theo, ca hai deu day cung mot chieu."),
    ("cci", "thap"): ("quay_ve_trung_binh",
        "Do lech am manh so voi gia trung binh dien hinh danh dau ban qua da; "
        "nguoi cung cap thanh khoan luc do duoc tra cong."),
    ("cci", "cao"): ("xu_huong",
        "Do lech duong manh so voi gia dien hinh cho thay dong tien dang vao "
        "va no it khi vao het trong mot bar."),
    ("stochastic", "thap"): ("quay_ve_trung_binh",
        "Dong cua nam o day bien do N bar la trang thai ban kiet suc; cau mua "
        "quay lai khi ap luc ban da het."),
    ("stochastic", "cao"): ("xu_huong",
        "Dong cua nam o dinh bien do N bar cho thay ben mua kiem soat, va phan "
        "cau chua khop con day tiep."),
    ("than_nen", "thap"): ("quay_ve_trung_binh",
        "Bar giam than dai la mot dot xa hang gap; nguoi hap thu no doi duoc "
        "tra cong o bar sau."),
    ("than_nen", "cao"): ("xu_huong",
        "Bar tang than dai la dau hieu lenh mua lon dang duoc thuc thi, va no "
        "thuong keo dai qua nhieu bar."),
    ("bien_do", "cao"): ("bien_dong",
        "Bien do bar rong nghia la rui ro cao, va ai giu vi the qua giai doan "
        "do doi duoc tra phan bu rui ro bien dong."),
    ("bien_do", "thap"): ("bien_dong",
        "Bien do co lai la giai doan tich luy truoc khi mot ben pha vo; phoi "
        "nhiem luc do mua duoc bien dong voi gia re."),
    ("atr", "cao"): ("bien_dong",
        "Bien dong thuc te cao keo theo phan bu rui ro cao hon cho ai san sang "
        "giu vi the qua giai doan do."),
    ("atr", "thap"): ("bien_dong",
        "Bien dong thap thuong di truoc giai doan bien dong cao; mua phoi nhiem "
        "luc bien dong dang re la mua quyen chon gia re."),
    ("phan_vi", "cao"): ("bien_dong",
        "Toan hang o phan vi cao cua chinh no trong cua so gan nhat danh dau "
        "che do bien dong cao, noi phan bu rui ro duoc tra day hon."),
    ("phan_vi", "thap"): ("bien_dong",
        "Toan hang o phan vi thap cua chinh no danh dau che do thi truong lang, "
        "noi chi phi giao dich thap va mot edge mong van con song duoc."),
    ("doi_pct", "thap"): ("quay_ve_trung_binh",
        "Mot cu giam manh trong N bar thuong la giai chap bi buoc; ben nhan "
        "hang tu nguoi bi buoc ban duoc tra chiet khau."),
    ("doi_pct", "cao"): ("xu_huong",
        "Mot cu tang manh trong N bar the hien dong von moi vao thi truong, va "
        "dong von do hiem khi ngung ngay lap tuc."),
    ("dong_luong", "thap"): ("quay_ve_trung_binh",
        "Dong luong am manh danh dau ap luc ban da toi han va thuong dao chieu "
        "khi nguoi ban cuoi cung da ban xong."),
    ("dong_luong", "cao"): ("xu_huong",
        "Dong luong duong keo dai the hien dong tien vao lien tuc, va do la co "
        "so lau doi nhat cua phan bu xu huong."),
    ("adx", "cao"): ("xu_huong",
        "Chi so xu huong manh cho biet thi truong dang o che do co huong, noi "
        "phan bu cho viec di theo xu huong duoc tra."),
    ("adx", "thap"): ("quay_ve_trung_binh",
        "Xu huong yeu la che do di ngang, noi gia dao quanh trung binh va nguoi "
        "cung cap thanh khoan o ca hai phia deu duoc tra cong."),
}


def _co_che_cua(th, cao):
    """(ho, cau co che) cho mot toan hang o mot chieu nguong. None = chua khai."""
    return CO_CHE_CUA.get((str(th.get("chi_bao", "")).lower(),
                           "cao" if cao else "thap"))


def _ten(t: dict) -> str:
    """Ten doc duoc cho mot toan hang."""
    cb = t.get("chi_bao", "?")
    n = t.get("n")
    cua = t.get("cua")
    goc = f"{cb}{n if n else ''}"
    if isinstance(cua, dict) and cua.get("chi_bao") != "gia":
        goc += f"_cua_{cua.get('chi_bao')}{cua.get('n') or ''}"
    return goc


def nguong_tu_lich_su(df: pd.DataFrame, toan_hang: dict,
                      phan_vi=PHAN_VI) -> dict[float, float]:
    """Nguong = PHAN VI THAT cua toan hang tren chuoi DUA VAO.

    Nguoi goi phai dua TRAIN, khong dua ca chuoi (chot chan 1). Ham nay khong
    tu cat vi no khong biet ranh gioi holdout cua nguoi goi.
    """
    s = NP.toan_hang(df, toan_hang).to_numpy(dtype=float)
    s = s[np.isfinite(s)]
    if len(s) < 200:
        return {}
    return {p: float(np.quantile(s, p)) for p in phan_vi}


def sinh(df_train: pd.DataFrame, cac_toan_hang=None, cac_giu=CAC_GIU,
         chieu: int = 1, kich_hoat_toi_thieu: float = 0.005,
         kich_hoat_toi_da: float = 0.60) -> list[dict]:
    """Sinh cac khai bao DSL mot dieu kien, nguong lay tu `df_train`.

    Loc ngay tai cho hai dau: co che kich hoat qua hiem (khong du lenh de noi
    gi) va qua thuong (khong con la mot dieu kien, chi la mua-giu doi ten).
    """
    ra: list[dict] = []
    for th in (cac_toan_hang or TOAN_HANG_GOC):
        try:
            ng = nguong_tu_lich_su(df_train, th)
        except Exception:
            continue
        if not ng:
            continue
        ten_th = _ten(th)
        for p, gt in ng.items():
            cao = p > 0.5
            khai = _co_che_cua(th, cao)
            if khai is None:
                continue          # khong khai duoc "vi sao" thi khong sinh
            ho, cau = khai
            phep = ">" if cao else "<"
            for giu in cac_giu:
                spec = {
                    "ten": f"ns_{ten_th}_{phep}_q{int(p * 100)}_giu{giu}",
                    "ho": ho, "chieu": chieu, "giu": int(giu),
                    "co_che": (f"{cau} Nguong lay tu phan vi {p:.0%} cua chinh "
                               f"chuoi tren TRAIN ({gt:.6g})."),
                    "nguon": "noi_sinh",
                    "vao": [{"trai": th, "phep": phep, "phai": {"hang": float(gt)}}],
                    "ra": [],
                }
                if NP.kiem_khai_bao(spec):
                    continue
                try:
                    tin = NP.sinh_tu_spec(spec, df_train)
                except Exception:
                    continue
                kh = float(np.mean(np.abs(np.nan_to_num(tin)) > 0))
                if not (kich_hoat_toi_thieu <= kh <= kich_hoat_toi_da):
                    continue
                ok, _ = NP.kiem_khong_nhin_truoc(spec, df_train)
                if not ok:
                    continue
                spec["_ty_le_kich_hoat"] = round(kh, 4)
                ra.append(spec)
    return ra


def sinh_cap(df_train: pd.DataFrame, cac_toan_hang=None, cac_giu=(1, 3, 5),
             chieu: int = 1, kich_hoat_toi_thieu: float = 0.005,
             kich_hoat_toi_da: float = 0.35, toi_da: int = 4000) -> list[dict]:
    """Ghep HAI dieu kien. Day la thu ca du an chua bao gio thu.

    Ghi chu 03/09/2026: quet 623 cau hinh truoc do deu la co che MOT dieu kien
    (hoac mot khai bao nhap nguyen tu ngoai). Chua co MOT to hop nao duoc thu.
    Khong gian cap lon hon rat nhieu nen no phai di kem `toi_da` va phai qua
    cong nghiem hon - de day chinh la ly do co `sang_loc` va MDE.
    """
    ths = list(cac_toan_hang or TOAN_HANG_GOC)
    ng = {}
    for th in ths:
        try:
            q = nguong_tu_lich_su(df_train, th, phan_vi=(0.05, 0.20, 0.80, 0.95))
        except Exception:
            q = {}
        if q:
            ng[_ten(th)] = (th, q)

    ra: list[dict] = []
    for (ta, (tha, qa)), (tb, (thb, qb)) in itertools.combinations(ng.items(), 2):
        for pa, ga in qa.items():
            for pb, gb in qb.items():
                for giu in cac_giu:
                    if len(ra) >= toi_da:
                        return ra
                    ka = _co_che_cua(tha, pa > 0.5)
                    kb = _co_che_cua(thb, pb > 0.5)
                    if ka is None or kb is None:
                        continue
                    fa = ">" if pa > 0.5 else "<"
                    fb = ">" if pb > 0.5 else "<"
                    # Ho cua mot cap lay theo dieu kien THU NHAT; cau co che
                    # ghep ca hai luan cu de nguoi duyet thay day la gia thuyet
                    # GHEP chu khong phai mot luan cu don.
                    spec = {
                        "ten": f"ns2_{ta}{fa}q{int(pa*100)}_{tb}{fb}q{int(pb*100)}_giu{giu}",
                        "ho": ka[0], "chieu": chieu, "giu": int(giu),
                        "co_che": f"{ka[1]} VA DONG THOI: {kb[1]}",
                        "nguon": "noi_sinh",
                        "vao": [
                            {"trai": tha, "phep": fa, "phai": {"hang": float(ga)}},
                            {"trai": thb, "phep": fb, "phai": {"hang": float(gb)}},
                        ],
                        "ra": [],
                    }
                    if NP.kiem_khai_bao(spec):
                        continue
                    try:
                        tin = NP.sinh_tu_spec(spec, df_train)
                    except Exception:
                        continue
                    kh = float(np.mean(np.abs(np.nan_to_num(tin)) > 0))
                    if not (kich_hoat_toi_thieu <= kh <= kich_hoat_toi_da):
                        continue
                    spec["_ty_le_kich_hoat"] = round(kh, 4)
                    ra.append(spec)
    return ra
