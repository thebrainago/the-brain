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
    # PHU THUOC THANG DO -> phai so voi PHAN VI TRUOT cua chinh no.
    #
    # Do 12/09/2026 tren EURUSD: nguong `atr14 < 0,003472` (phan vi 20 cua
    # TRAIN) kich hoat 1.719 lan o TRAIN va **0 lan o HOLDOUT** - trung vi ATR
    # holdout la 0,00927, nam tren ca phan vi 20 cua train. Bay co che "song
    # sot" that ra khong vao lenh nao, va bao cao dem chung la "giu dau 9/10".
    #
    # Mot nguong TUYET DOI tren dai luong phu thuoc thang do chi dung trong
    # dung che do bien dong da lay no. `phan_vi` truot thi chuyen duoc.
    {"chi_bao": "phan_vi", "cua": {"chi_bao": "than_nen"}, "n": 250},
    {"chi_bao": "phan_vi", "cua": {"chi_bao": "bien_do"}, "n": 250},
    {"chi_bao": "doi_pct", "cua": {"chi_bao": "gia", "cot": "close"}, "n": 1},
    {"chi_bao": "doi_pct", "cua": {"chi_bao": "gia", "cot": "close"}, "n": 5},
    {"chi_bao": "phan_vi", "cua": {"chi_bao": "atr", "n": 14}, "n": 250},
    {"chi_bao": "adx", "n": 14},
    {"chi_bao": "cci", "cot": "close", "n": 20},
    {"chi_bao": "stochastic", "n": 14},
    {"chi_bao": "phan_vi", "cua": {"chi_bao": "dong_luong", "cot": "close",
                                  "n": 10}, "n": 250},
    {"chi_bao": "phan_vi", "cua": {"chi_bao": "atr", "n": 14}, "n": 250},
    {"chi_bao": "phan_vi", "cua": {"chi_bao": "bien_do"}, "n": 100},
    # CAC DANG NEN - dong "Cac dang nen khac nhau" cua so do, them 12/09/2026.
    # Chi lay cac mau LIEN TUC o day: mau roi rac (nhan_chim/trong/ngoai/ba_nen
    # chi khac 0 o 2-14% bar) thi phan vi vo nghia - chung duoc sinh rieng o
    # `sinh_mau_nen`.
    {"chi_bao": "mau_nen", "mau": "doji"},
    {"chi_bao": "mau_nen", "mau": "bua"},
    {"chi_bao": "mau_nen", "mau": "sao_bang"},
    {"chi_bao": "mau_nen", "mau": "nen_dac"},
    {"chi_bao": "mau_nen", "mau": "rau_duoi"},
    {"chi_bao": "mau_nen", "mau": "rau_tren"},
    # NAM CHI BAO THEM 12/09/2026 - 72 co che trong kho nhac ten chung ma ngu
    # phap khong noi duoc. Chi lay dang KHONG PHU THUOC THANG DO (xem ghi chu o
    # tren): `%b`, `vi tri trong kenh`, `khoang cach chia ATR`, `than chia bien
    # do`. Dang gia tri tho (duong keltner, kijun, chikou) khong vao day - nguong
    # tuyet doi cua chung khong chuyen duoc sang tai san khac.
    {"chi_bao": "keltner", "n": 20, "k": 2.0, "lay": "phan_tram_b"},
    {"chi_bao": "donchian", "n": 20, "lay": "vi_tri"},
    {"chi_bao": "donchian", "n": 55, "lay": "vi_tri"},
    {"chi_bao": "supertrend", "n": 10, "k": 3.0, "lay": "khoang_cach"},
    {"chi_bao": "heiken", "lay": "than"},
]

#: Mau nen ROI RAC: chi khac 0 o mot phan nho so bar, nen dung phan vi la sai.
#: Chung duoc dung truc tiep: `mau_nen(nhan_chim) > 0` da la mot dieu kien day du.
MAU_NEN_ROI_RAC = ("nhan_chim", "trong", "ngoai", "ba_nen")

#: Chi bao ROI RAC (chi nhan vai gia tri) - phan vi vo nghia, dung truc tiep.
CHI_BAO_ROI_RAC = ({"chi_bao": "supertrend", "n": 10, "k": 3.0, "lay": "chieu"},
                   {"chi_bao": "heiken", "lay": "chieu"})

#: Lap luan kinh te cho TUNG MAU NEN. Cong `kiem_khai_bao` tu choi mot khai bao
#: khong noi duoc "vi sao co nguoi tra tien cho phoi nhiem nay", va do la chot
#: chan DUNG: mot bo sinh tu dong khong duoc de ra hang loat co che vo danh.
CO_CHE_NEN = {
    ("nhan_chim", "cao"): ("dao_chieu",
        "Than bar trum het than bar truoc va nguoc chieu: ben thua cuoc bi buoc "
        "dong vi the trong mot bar, va lenh dong do la cau mua that."),
    ("nhan_chim", "thap"): ("dao_chieu",
        "Nhan chim chieu giam: ben mua bi quet sach trong mot bar, lenh cat lo "
        "cua ho la nguon cung ban ep."),
    ("bua", "cao"): ("quay_ve_trung_binh",
        "Rau duoi dai ma dong cua ve gan dinh bar: gia da xuong sau roi bi mua "
        "het - dau vet cua mot ben mua lon hap thu nguon cung."),
    ("bua", "thap"): ("quay_ve_trung_binh",
        "Hinh guong cua bua: rau tren dai, gia len cao roi bi ban het."),
    ("sao_bang", "cao"): ("quay_ve_trung_binh",
        "Rau tren dai ma dong cua ve gan day bar: cau mua da can o vung cao, "
        "ai ban vao do duoc tra cong."),
    ("sao_bang", "thap"): ("quay_ve_trung_binh",
        "Nguoc lai: cau mua manh o vung thap sau khi gia bi day xuong."),
    ("doji", "cao"): ("bien_dong",
        "Than gan bang khong voi bien do rong: hai ben can bang sau mot cuoc "
        "giang co - trang thai truoc mot buoc doi che do bien dong."),
    ("trong", "cao"): ("bien_dong",
        "Ca bien do nam gon trong bar truoc: bien do co lai, va phoi nhiem mua "
        "luc bien dong re la mua quyen chon gia re."),
    ("ngoai", "cao"): ("bien_dong",
        "Bar trum ca hai dau bar truoc theo chieu tang: bien do no ra kem huong "
        "ro, ai giu vi the qua do doi duoc tra phan bu rui ro."),
    ("ngoai", "thap"): ("bien_dong",
        "Bar ngoai chieu giam: cung su no bien do nhung ve phia ban."),
    ("ba_nen", "cao"): ("xu_huong",
        "Ba bar tang lien tiep than day: dong lenh mua co to chuc duoc giai "
        "ngan dan chu khong het trong mot bar."),
    ("ba_nen", "thap"): ("xu_huong",
        "Ba bar giam lien tiep than day: mot chuong trinh ban dang chay dan."),
    ("nen_dac", "cao"): ("xu_huong",
        "Than chiem gan het bien do theo chieu tang: khong co giang co, mot ben "
        "kiem soat ca bar."),
    ("nen_dac", "thap"): ("xu_huong",
        "Than dac chieu giam: ben ban kiem soat ca bar."),
    ("rau_duoi", "cao"): ("quay_ve_trung_binh",
        "Rau duoi dai la dau vet cau mua hap thu nguon cung o vung thap."),
    ("rau_tren", "cao"): ("quay_ve_trung_binh",
        "Rau tren dai la dau vet nguon cung chan lai o vung cao."),
}

#: Phan vi lam nguong. Doi xung hai duoi de khong thien ve mot chieu.
PHAN_VI = (0.02, 0.05, 0.10, 0.20, 0.80, 0.90, 0.95, 0.98)

#: Mot nguong phai chon duoc it nhat bay nhieu ti le bar cua TRAIN.
#:
#: Duoi muc nay co HAI cach hong, ca hai deu im lang:
#:   * nguong dung vao BIEN cua mot dai luong bi chan (`ibs > q95` voi q95 = 1,0)
#:     -> khong bar nao dung, ke ca trong TRAIN;
#:   * nguong o duoi cuc hiem -> TRAIN co vai chuc bar nhung HOLDOUT co the
#:     khong co bar nao (do 12/09: `nen_doji @q2`), va khi do phep thu khong
#:     chay duoc chu khong phai ra ket qua am.
#: 2% cung khop voi bo cham diem: duoi 30 lenh thi no da bo ung vien roi.
TY_LE_KICH_HOAT_TOI_THIEU = 0.02

#: Nguong phai cach BIEN cua phan phoi it nhat bay nhieu phan cua bien do.
#: Dai luong bi chan (ibs, diem mau nen, than Heikin-Ashi deu nam trong mot
#: khoang dong) co phan vi cuc bien nam sat bien, va cai cham bien thuong la
#: DI THUONG DU LIEU chu khong phai trang thai thi truong.
LE_BIEN_TOI_THIEU = 0.05

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
    ("keltner", "cao"): ("bien_dong",
        "Gia nam o mep tren dai Keltner - dai do rong theo BIEN DO THAT chu "
        "khong theo do lech chuan, nen mep tren la noi rui ro bien dong duoc "
        "tra cong cao nhat."),
    ("keltner", "thap"): ("quay_ve_trung_binh",
        "Gia rot xuong duoi dai Keltner: ban qua da so voi bien do that cua "
        "chinh tai san do, va nguoi hap thu nguon cung duoc chiet khau."),
    ("donchian", "cao"): ("pha_vo",
        "Gia o dinh kenh n bar: lenh cho mua tren dinh va lenh cat lo cua ben "
        "ban nam cung mot cho, nen khi cham thi ca hai cung day mot chieu."),
    ("donchian", "thap"): ("pha_vo",
        "Gia o day kenh n bar: lenh cat lo cua ben mua bi quet, tao nguon cung "
        "ban ep trong mot khoang gia hep."),
    ("supertrend", "cao"): ("xu_huong",
        "Gia cach duong Supertrend nhieu ATR ve phia tren: xu huong dang duoc "
        "nuoi bang dong lenh mua lien tuc, va duong bien chot lai phia sau."),
    ("supertrend", "thap"): ("xu_huong",
        "Gia cach duong Supertrend nhieu ATR ve phia duoi: chuong trinh ban "
        "dang chay va duong bien chot lai phia tren."),
    ("heiken", "cao"): ("xu_huong",
        "Than nen Heikin-Ashi chiem gan het bien do theo chieu tang - HA lam "
        "muot nhieu trong bar nen than day o day la dau hieu ap luc mot chieu "
        "keo dai qua nhieu bar, khong phai mot cu nhay le."),
    ("heiken", "thap"): ("xu_huong",
        "Than HA day chieu giam: ap luc ban keo dai qua nhieu bar."),
    ("adx", "thap"): ("quay_ve_trung_binh",
        "Xu huong yeu la che do di ngang, noi gia dao quanh trung binh va nguoi "
        "cung cap thanh khoan o ca hai phia deu duoc tra cong."),
}


def _co_che_cua(th, cao):
    """(ho, cau co che) cho mot toan hang o mot chieu nguong. None = chua khai."""
    cb = str(th.get("chi_bao", "")).lower()
    if cb == "mau_nen":
        # Moi MAU NEN mot lap luan rieng - gop chung thanh mot dong "mau nen"
        # thi cong `kiem_khai_bao` nhan mot cau vo nghia cho ca muoi mau.
        return CO_CHE_NEN.get((str(th.get("mau", "")).lower(),
                               "cao" if cao else "thap"))
    return CO_CHE_CUA.get((cb, "cao" if cao else "thap"))


def _ten(t: dict) -> str:
    """Ten doc duoc cho mot toan hang."""
    cb = t.get("chi_bao", "?")
    n = t.get("n")
    cua = t.get("cua")
    goc = f"{cb}{n if n else ''}"
    if cb == "mau_nen":
        goc = "nen_%s" % t.get("mau", "?")
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
    ra = {}
    for p in phan_vi:
        q = float(np.quantile(s, p))
        # BO NGUONG SUY BIEN. Voi mot dai luong BI CHAN (ibs trong [0,1], diem
        # mau nen trong [-1,1]), phan vi cuc bien roi dung vao bien: `ibs > q95`
        # voi q95 = 1,0 thi **khong bar nao dung**, ke ca trong chinh TRAIN.
        # Do 12/09/2026: 6 toan hang sinh ra dieu kien chet kieu nay
        # (ibs@q95, nen_doji@q95, nen_bua@q5, nen_sao_bang@q5, rau_duoi@q5,
        # rau_tren@q5). Chung khong bao loi - chung chi lam ra co che khong bao
        # gio kich hoat, va nhung co che do chiem cho trong moi bang xep hang.
        cao = float(np.mean(s > q))
        thap = float(np.mean(s < q))
        ben = cao if p >= 0.5 else thap
        if ben < TY_LE_KICH_HOAT_TOI_THIEU:
            continue
        # BO NGUONG SAT BIEN. Voi mot dai luong BI CHAN, phan vi cuc bien cua
        # TRAIN co the nam sat bien - va cai cham bien do thuong la mot DI
        # THUONG cua du lieu chu khong phai mot trang thai thi truong.
        #
        # Do 12/09/2026: `heiken than` (nam trong [-1, 1]) tren EURUSD D1
        #     TRAIN   min -1,0000  q2 -0,9881   -> 145 bar
        #     HOLDOUT min -0,8927  cung nguong  -> **0 bar**
        # Nen than HA = -1,0000 nghia la nen lap kin bien do, tuc bar KHONG CO
        # RAU - dau vet cua high/low duoc CHE tu open/close (`du_lieu` BAY 6).
        # TRAIN con 2% bar nhu vay, HOLDOUT khong con cai nao. Nguong sinh ra tu
        # do khong phai mot luat, la mot cai bay.
        bien = float(s.max() - s.min())
        if bien > 0:
            gan_bien = min(abs(q - s.min()), abs(s.max() - q)) / bien
            if gan_bien < LE_BIEN_TOI_THIEU:
                continue
        ra[p] = q
    return ra


def sinh(df_train: pd.DataFrame, cac_toan_hang=None, cac_giu=CAC_GIU,
         chieu: int = 1, kich_hoat_toi_thieu: float = 0.005,
         kich_hoat_toi_da: float = 0.95) -> list[dict]:
    """Sinh cac khai bao DSL mot dieu kien, nguong lay tu `df_train`.

    `kich_hoat_toi_da` mac dinh 0,95 — KHONG phai 0,60.

    Do la mot loi thiet ke da sua 03/09/2026, do chu du an chi ra: *"neu thi
    truong bull thi ve li ta cang de kiem loi voi trendfollowing va breakout"*.
    Voi tran 0,60, moi co che THEO XU HUONG bi loai ngay tu bo sinh: mot bo loc
    xu huong tren thi truong bo o trong thi truong 70-90% so bar. Hau qua do
    duoc: top-12 noi sinh tren US500CASH.H4 toan `ibs<q10` / `zscore<q5` /
    `stochastic<q2` voi phoi nhiem 1-12% — khong MOT he xu huong nao, nen ket
    luan am cua luot do chua he cham toi trend/breakout.

    Vay cai gi chan "mua-giu doi ten"? KHONG phai tran phoi nhiem — ma la phep
    so voi chinh mua-giu O CUNG MUC RUI RO (`cong.he_so_khop_rui_ro`). Mot co
    che kich hoat 92% so bar ma khong hon duoc mua-giu se rot o do, va do la
    cho dung de no rot. Chan bang tran phoi nhiem la chan NHAM TANG: no loai ca
    thu ta dang di tim.
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
             kich_hoat_toi_da: float = 0.85, toi_da: int = 4000) -> list[dict]:
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

# ------------------------------------------------------ SO TOAN HANG VOI NHAU
#: Cap (nhanh, cham) de so TRUC TIEP voi nhau. Day la dang co che ma `sinh()`
#: KHONG the de ra duoc, va do la mot lo hong cau truc chu khong phai mot tham
#: so dat sai.
#:
#: Phat hien 03/09/2026, sau khi chu du an hoi "ngoai sinh khong kiem duoc
#: chien luoc nao trendfollowing chac?": `sinh()` luon so mot toan hang voi mot
#: HANG SO (nguong phan vi). Nhung mot bo loc xu huong la `close > sma(close,
#: 200)` - TOAN HANG so voi TOAN HANG. Khong co duong nao trong `sinh()` de ra
#: duoc dang do, nen ket luan am cua noi sinh truoc 03/09 khong he cham toi
#: trend/breakout. Nang tran phoi nhiem (0,60 -> 0,95) chi them 16 co che va ca
#: 16 deu la `giu10` - day phoi nhiem len bang cach giu lau, khong phai loc
#: xu huong.
CAP_XU_HUONG = [
    ("close", {"chi_bao": "gia", "cot": "close"},
     "sma200", {"chi_bao": "sma", "cot": "close", "n": 200}),
    ("close", {"chi_bao": "gia", "cot": "close"},
     "sma50", {"chi_bao": "sma", "cot": "close", "n": 50}),
    ("close", {"chi_bao": "gia", "cot": "close"},
     "ema20", {"chi_bao": "ema", "cot": "close", "n": 20}),
    ("sma20", {"chi_bao": "sma", "cot": "close", "n": 20},
     "sma100", {"chi_bao": "sma", "cot": "close", "n": 100}),
    ("sma50", {"chi_bao": "sma", "cot": "close", "n": 50},
     "sma200", {"chi_bao": "sma", "cot": "close", "n": 200}),
    ("ema12", {"chi_bao": "ema", "cot": "close", "n": 12},
     "ema26", {"chi_bao": "ema", "cot": "close", "n": 26}),
    ("close", {"chi_bao": "gia", "cot": "close"},
     "dinh50", {"chi_bao": "cao_nhat", "cua": {"chi_bao": "gia", "cot": "high"},
                "n": 50}),
    ("close", {"chi_bao": "gia", "cot": "close"},
     "day50", {"chi_bao": "thap_nhat", "cua": {"chi_bao": "gia", "cot": "low"},
               "n": 50}),
]

CO_CHE_CAP = {
    ">": ("xu_huong",
          "Gia nam tren duong tham chieu dai han danh dau che do co huong: dong "
          "von vao co to chuc duoc giai ngan dan qua nhieu phien, nen ai di theo "
          "duoc tra phan bu xu huong."),
    "<": ("xu_huong",
          "Gia nam duoi duong tham chieu dai han danh dau che do giam: rui ro "
          "giai chap va ban buoc tang, nen dung ngoai la mot vi the co gia."),
    "cheo_len": ("xu_huong",
                 "Diem cat len la luc che do doi chieu; dong lenh dat theo dieu "
                 "kien do duoc kich hoat cung mot luc va cung day mot huong."),
    "cheo_xuong": ("xu_huong",
                   "Diem cat xuong lam hang loat lenh dung lo va lenh dao chieu "
                   "kich hoat cung luc, day gia tiep theo huong do."),
}


def sinh_xu_huong(df_train: pd.DataFrame, cac_cap=None, cac_giu=(1, 5, 10, 20),
                  chieu: int = 1, kich_hoat_toi_thieu: float = 0.02,
                  kich_hoat_toi_da: float = 0.97) -> list[dict]:
    """Sinh co che THEO XU HUONG: so hai toan hang voi nhau.

    Tran phoi nhiem o day cao (0,97) la CO Y: mot bo loc xu huong tren thi
    truong bo o trong thi truong 70-90% so bar. Cai chan "mua-giu doi ten"
    khong phai tran phoi nhiem ma la phep so voi mua-giu O CUNG MUC RUI RO.
    """
    ra: list[dict] = []
    for ten_a, ta, ten_b, tb in (cac_cap or CAP_XU_HUONG):
        for phep in (">", "<", "cheo_len", "cheo_xuong"):
            ho, cau = CO_CHE_CAP[phep]
            for giu in cac_giu:
                spec = {
                    "ten": f"nsx_{ten_a}_{phep}_{ten_b}_giu{giu}",
                    "ho": ho, "chieu": chieu, "giu": int(giu),
                    "co_che": f"{cau} (do bang {ten_a} {phep} {ten_b})",
                    "nguon": "noi_sinh_xu_huong",
                    "vao": [{"trai": ta, "phep": phep, "phai": tb}],
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
