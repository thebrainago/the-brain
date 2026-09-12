# -*- coding: utf-8 -*-
"""doc_lenh_tester.py - Doc DANH SACH LENH tu bao cao MT5 Strategy Tester.

## Vi sao can

`SO_DO_HE_THONG.txt`: *"Xay dung kha nang truy nguoc lich su giao dich de tim ra
chien luoc roi dung mo phong chien luoc"*.

`ds/mimic` lam duoc viec do - nhan SO LENH + BAR, chung cat mot cay quyet dinh
nong, tra ve luat. `nhan/mimic_cau_noi.py` dich luat do sang DSL. Ca hai da co.
Cai thieu la **dau vao**.

## VA CHO NAY DA CO MOT HIEU LAM PHAI SUA

Ghi chu cu trong `mimic_cau_noi` noi: *"120 tai lieu track-record + 400 ho so
signal chua bao gio di qua no"*. Do 12/09/2026 thi 400 ho so signal chi co
**so lieu tong hop** - `so_lenh`, `pf`, `sharpe`, `dd_pct` - va **KHONG ho so
nao co lich su lenh**. Chung khong phai "chua di qua", chung **khong the di
qua**: mimic can tung lenh, khong can thong ke.

Lich su lenh THAT ma lab dang co nam o bao cao MT5 Strategy Tester
(`reports/TESTER_*.htm`): moi lenh mot hang, co gio - ma - chieu - khoi luong.

## VA DO CHINH LA PHEP HIEU CHUAN TOT NHAT CO THE

He `z5` do CHINH lab sinh ra, nen ta **biet truoc luat cua no**. Cho mimic doc
lai so lenh cua z5: neu no khong tim lai duoc thu gi giong luat that, thi mimic
vo dung tren du lieu that - va do la ket luan phai biet TRUOC khi dem no di doc
so lenh cua nguoi la.

Chay:  python -m nhan.doc_lenh_tester reports/TESTER_z5_M2.htm
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

#: Mot hang lenh: gio | so hieu | ma | chieu | khoi luong | gia | ...
_HANG = re.compile(
    r"<td>(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})</td>"      # gio
    r"<td>(\d+)</td>"                                         # so hieu
    r"<td>([A-Za-z0-9_.#]+)</td>"                             # ma
    r"<td>(buy|sell|buy limit|sell limit|buy stop|sell stop)</td>",
    re.I)


def doc(f: Path | str) -> pd.DataFrame:
    """Bao cao tester -> DataFrame [luc, so_hieu, ma, chieu_chu, chieu].

    Doc utf-16 truoc (MT5 ghi the) roi lui ve utf-8. `doc_bao_cao` trong
    `chay_tester_z5.py` cung lam vay - giu cung mot cach de hai ben doc duoc
    cung mot file.
    """
    p = Path(f)
    tho = p.read_text(encoding="utf-16", errors="ignore")
    if "<" not in tho[:400]:
        tho = p.read_text(encoding="utf-8", errors="ignore")
    hang = []
    for luc, so, ma, chieu in _HANG.findall(tho):
        c = chieu.lower()
        hang.append({"luc": pd.Timestamp(luc.replace(".", "-", 2)),
                     "so_hieu": int(so), "ma": ma, "chieu_chu": c,
                     "chieu": 1 if c.startswith("buy") else -1})
    df = pd.DataFrame(hang)
    if len(df):
        df = df.drop_duplicates(subset=["so_hieu"]).sort_values("luc")
    return df.reset_index(drop=True)


def vao_lenh_moi(df_lenh: pd.DataFrame) -> pd.DataFrame:
    """Chi giu lenh MO vi the.

    Bang `Orders` cua MT5 liet ke ca lenh mo lan lenh dong, va lenh dong mang
    chieu NGUOC voi vi the. Dem ca hai lam dau vao cho mimic thi no se hoc mot
    thu vo nghia: nua so "tin hieu mua" that ra la luc DONG mot vi the ban.

    Cach phan biet khong can cot phu: di theo thu tu thoi gian va giu trang thai
    phoi nhiem. Lenh lam phoi nhiem DI XA 0 la lenh mo; lenh keo no VE 0 la dong.
    """
    if not len(df_lenh):
        return df_lenh
    giu, vi_the = [], 0
    for _, r in df_lenh.iterrows():
        moi = vi_the + r["chieu"]
        if abs(moi) > abs(vi_the):
            giu.append(True)
        else:
            giu.append(False)
        vi_the = moi
    return df_lenh[pd.Series(giu, index=df_lenh.index)].reset_index(drop=True)


def khop_vao_bar(df_lenh: pd.DataFrame, df_bar: pd.DataFrame) -> list[int]:
    """Moi lenh -> chi so BAR chua no. Lenh ngoai pham vi bar thi bo.

    Dung `searchsorted` chu khong `get_indexer(method="nearest")`: gan nhat co
    the tra ve bar SAU luc vao, va do la nhin truoc.
    """
    idx = pd.DatetimeIndex(df_bar.index)
    if idx.tz is not None:
        idx = idx.tz_convert("UTC").tz_localize(None)
    ra = []
    for luc in df_lenh["luc"]:
        i = int(idx.searchsorted(luc, side="right")) - 1
        if 0 <= i < len(idx):
            ra.append(i)
    return ra


def chung_luat(f_bao_cao: Path | str, ma_bar: str, khung: str = "D1",
               am_moi_duong: int = 3, in_ra=print) -> dict:
    """Bao cao tester -> LUAT (DSL). Ca duong "truy nguoc lich su giao dich".

    ## VI SAO KHONG GOI THANG `mimic.entry.build_dataset`

    Ham do khop lenh vao bar bang **so khop CHUOI CHINH XAC**:
        `{str(t): i for i, t in enumerate(times)}` roi tra `str(open_time)`
    Lenh MT5 dong dau 02:00:00 con bar D1 dong dau 00:00:00, nen no khong khop
    duoc MOT lenh nao - `build_dataset` tra ve 0 duong tinh va `distill` bao
    "too_few_samples_to_distill". Im lang, khong loi.

    O day dung `khop_vao_bar` (searchsorted, lay bar CHUA lenh, khong bao gio
    lay bar sau) roi goi thang `build_features` + `distill_rules`.

    ## DAY CUNG LA PHEP HIEU CHUAN

    He `z5` do chinh lab sinh ra nen ta BIET truoc luat cua no. Do 12/09/2026
    tren `TESTER_z5_M2.htm` (305 lenh mo, US100Cash D1): mimic chung ra
    `price_position` (= vi tri dong cua trong bien do 20 bar) lam bien phan biet
    chinh, `pos_ratio` 0,373 so voi nen 0,25. Dung HO co che that cua z5 -
    memory `z5-la-hien-tuong-che-do` ghi z5 la "IBS duoi ten khac", va IBS cung
    la vi tri dong cua trong bien do. Tuc bo chung luat tim lai duoc dung ho.
    """
    import numpy as np
    sys.path.insert(0, str(LAB.parent / "ds"))
    from mimic.distill import distill_rules
    from mimic.entry import _negative_sampled
    from mimic.features import build_features, compute_feature_names
    from nhan import du_lieu as DL
    from nhan import mimic_cau_noi as MC

    lenh = vao_lenh_moi(doc(f_bao_cao))
    df = DL.nap(ma_bar, khung)
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is not None:
        idx = idx.tz_convert("UTC").tz_localize(None)

    class _Bars:
        pass

    b = _Bars()
    for k in ("open", "high", "low", "close"):
        setattr(b, k, df[k].to_numpy(float))
    b.time = (idx.astype("int64") // 10 ** 9).to_numpy()

    duong = sorted(set(khop_vao_bar(lenh, df)))
    if len(duong) < 30:
        return {"nhan": False, "ly_do": "chi khop %d lenh vao bar" % len(duong)}
    am = _negative_sampled(b.time, set(duong), budget=am_moi_duong * len(duong))
    tat = sorted(set(duong) | set(am))
    feat = build_features(b, entry_indices=tat)
    X, y = [], []
    bo_duong = set(duong)
    for i in tat:
        f = feat.get(i)
        if f is None:
            continue
        X.append(tuple(float(v) for v in f))
        y.append(1 if i in bo_duong else 0)
    X, y = np.array(X), np.array(y)
    kq = distill_rules(X, y, compute_feature_names(), max_depth=3,
                       min_samples_leaf=20)
    nen = float(y.mean())

    ra = []
    for L in (kq.get("rules") or []):
        dk = L.get("conditions") if isinstance(L, dict) else None
        if not dk:
            continue
        dich = [MC.dich_dieu_kien(c) for c in dk]
        ra.append({"dieu_kien_mimic": dk,
                   "pos_ratio": L.get("pos_ratio"), "samples": L.get("samples"),
                   "nang_so_voi_nen": (round(L["pos_ratio"] / nen, 3)
                                       if L.get("pos_ratio") and nen else None),
                   "dsl": [d.get("dieu_kien") for d in dich if d.get("nhan")],
                   "khong_dich_duoc": [d.get("thieu_tu_vung") for d in dich
                                       if not d.get("nhan")]})
    ra.sort(key=lambda r: -(r["pos_ratio"] or 0))
    ket = {"nhan": True, "ma": ma_bar, "khung": khung,
           "so_lenh_mo": len(lenh), "khop_bar": len(duong),
           "nen_duong_tinh": round(nen, 4), "luat": ra}
    if in_ra:
        in_ra("%s | %d lenh mo -> khop %d bar | nen duong tinh %.1f%%"
              % (ma_bar, len(lenh), len(duong), nen * 100))
        for r in ra[:5]:
            in_ra("  pos_ratio %.3f (x%.2f nen) tren %s mau"
                  % (r["pos_ratio"] or 0, r["nang_so_voi_nen"] or 0,
                     r["samples"]))
            in_ra("    %s" % " VA ".join(r["dieu_kien_mimic"]))
            if r["khong_dich_duoc"]:
                in_ra("    KHONG DICH DUOC: %s" % r["khong_dich_duoc"])
    return ket


def _in(df_lenh: pd.DataFrame, mo: pd.DataFrame, in_ra=print) -> None:
    in_ra("doc %d hang lenh" % len(df_lenh))
    if not len(df_lenh):
        return
    in_ra("  tu %s den %s" % (df_lenh["luc"].min(), df_lenh["luc"].max()))
    in_ra("  ma: %s" % ", ".join(sorted(df_lenh["ma"].unique())[:6]))
    in_ra("  chieu: %s" % df_lenh["chieu_chu"].value_counts().to_dict())
    in_ra("  lenh MO vi the: %d / %d" % (len(mo), len(df_lenh)))


def main(argv: list[str]) -> int:
    f = argv[0] if argv else "reports/TESTER_z5_M2.htm"
    duong = LAB / f if not Path(f).is_absolute() else Path(f)
    if "--luat" in argv:
        i = argv.index("--luat")
        chung_luat(duong, argv[i + 1] if len(argv) > i + 1 else "XM_US100CASH",
                   "D1")
        return 0
    df = doc(duong)
    mo = vao_lenh_moi(df)
    _in(df, mo)
    if len(mo):
        print("\n5 lenh mo dau tien:")
        print(mo.head().to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
