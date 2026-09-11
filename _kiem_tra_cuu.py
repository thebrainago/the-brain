# -*- coding: utf-8 -*-
"""_kiem_tra_cuu.py - CONG NGHIEM THU cua so bai hoc: 20 cau hoi that.

Mot so tri nho chi co gia tri neu HOI LAI DUOC. Dem so the la phep do sai: mot
so 1.000 the ma khong tra ra cai dang can thi vo dung, con mot so 50 the tra
dung thi da doi duoc hanh vi.

20 cau duoi day la nhung cau ma mot phien lam viec THAT se hoi - moi cau lay tu
mot bai hoc du an da tra gia de co. `cho` la tu khoa phai xuat hien trong the
tra ve (tieu de + noi dung + bang chung, da bo dau).

Day KHONG phai bai kiem cua `bai_hoc.py` - do la `test_bai_hoc.py`. Day la bai
kiem cua NOI DUNG so: so co du thu de tra loi cong viec hang ngay khong.

Chay:  python _kiem_tra_cuu.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import bai_hoc as BH  # noqa: E402

RA = GOC / "reports" / "KIEM_TRA_CUU.json"

#: (cau hoi, mot trong cac tu nay phai co trong the tra ve)
CAU_HOI: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Model=1 cua MT5 tester co tin duoc khong",
     ("model=1", "1 minute ohlc", "tick that")),
    ("phi qua dem tinh the nao cho dung",
     ("swap", "lai suat", "qua dem")),
    ("placebo hoan vi cai gi moi dung",
     ("hoan vi", "vi the", "chuoi lai")),
    ("vao lenh o close hay open bar ke tiep",
     ("open[i+1]", "open bar", "look-ahead", "nhin truoc")),
    ("IBS bat day co song tren forex khong",
     ("ibs", "chi so co phieu", "chau my")),
    ("spread that cua CFD chi so la bao nhieu",
     ("bps", "spread")),
    ("tai khoan cent co giup giam von can khong",
     ("cent", "min lot", "chia 100")),
    ("FDR co tung loai duoc gia thuyet nao khong",
     ("fdr", "lord", "nguong")),
    ("khung nho M5 co du du lieu de backtest khong",
     ("m5", "khung nho", "bar", "2016")),
    ("don bay cao co lam tang CAGR mai khong",
     ("don bay", "sharpe", "0,5*s^2", "tran")),
    ("ghep hai he thi chon chan nao",
     ("nguoc chieu", "ghep", "tuong quan")),
    ("trailing stop co cai thien he khong",
     ("trailing", "dat hue", "quan tri")),
    ("luoi khong SL co an toan khong",
     ("luoi", "sl", "martingale", "dca")),
    ("co nen tin bang xep hang he don khong",
     ("holdout", "xep hang", "nhieu")),
    ("MT5 co tra du bar khi goi lan dau khong",
     ("copy_rates", "thieu bar", "from_pos")),
    ("open truoc 2006 co dung duoc khong",
     ("open", "close[t-1]", "bia")),
    ("bar D1 cua CFD co phai bar phien khong",
     ("d1", "phien", "cfd")),
    ("order flow tren CFD do duoc khong",
     ("order flow", "volume", "tape", "cme")),
    ("mua-giu co phai moc so sanh dung khong",
     ("mua-giu", "mua giu", "buy&hold", "moc")),
    ("LLM dien co che duoc khong",
     ("llm", "co che", "tham dinh", "48")),
)


def _bo_dau(s: str) -> str:
    s = s.lower()
    for a, b in (("àáảãạăằắẳẵặâầấẩẫậ", "a"), ("èéẻẽẹêềếểễệ", "e"),
                 ("ìíỉĩị", "i"), ("òóỏõọôồốổỗộơờớởỡợ", "o"),
                 ("ùúủũụưừứửữự", "u"), ("ỳýỷỹỵ", "y"), ("đ", "d")):
        for c in a:
            s = s.replace(c, b)
    return re.sub(r"\s+", " ", s)


#: HIEU CHUAN CHIEU NGUOC. Mot bo kiem chi biet noi "dat" thi cho so lieu y het
#: mot bo kiem tot - day la luat da ghi trong hien phap du an ("cong PASS phai
#: hieu chuan hai chieu"). Nhung cau duoi day KHONG co trong so; neu chung cung
#: "dat" thi tu khoa mong doi cua toi qua long, khong phai so qua gioi.
CAU_VO_NGHIA: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("cong thuc lam banh mi bo toi", ("banh mi", "bo toi", "lo nuong")),
    ("cach thay dau xe may Honda", ("dong co xe may", "honda", "bugi")),
    ("lich thi dau giai bong da Ngoai hang Anh", ("bong da", "ngoai hang", "lich thi dau")),
    ("trieu chung cam cum mua dong", ("cam cum", "so mui", "ho sot")),
)


def _khop(tu: str, vb: str) -> bool:
    """Khop theo RANH GIOI TU. Chuoi con thi qua long: sau khi bo dau tieng
    Viet, "trieu chung" nam gon trong "2,26 trieu bar ... chung", va bo do se
    bao mot cau hoi ve cam cum la "tra dung"."""
    return re.search(r"\b" + re.escape(_bo_dau(tu)) + r"\b", vb) is not None


def chay(so_the: int = 5) -> dict:
    dat, truot = 0, []
    chi_tiet = []
    for cau, cho in CAU_HOI:
        the = BH.tra(cau, so_the=so_the)
        vb = _bo_dau(" ".join(
            f"{t['tieu_de']} {t['noi_dung']} {t['bang_chung'] or ''}" for t in the))
        trung = [k for k in cho if _khop(k, vb)]
        ok = bool(trung)
        dat += ok
        chi_tiet.append({"cau": cau, "dat": ok, "trung": trung,
                         "the": [t["tieu_de"][:80] for t in the[:3]]})
        if not ok:
            truot.append((cau, cho, [t["tieu_de"][:70] for t in the[:3]]))

    # chieu nguoc
    gia_dat = 0
    for cau, cho in CAU_VO_NGHIA:
        the = BH.tra(cau, so_the=so_the)
        vb = _bo_dau(" ".join(
            f"{t['tieu_de']} {t['noi_dung']} {t['bang_chung'] or ''}" for t in the))
        if any(_khop(k, vb) for k in cho):
            gia_dat += 1

    ket = {"so_cau": len(CAU_HOI), "dat": dat, "so_the_moi_cau": so_the,
           "ty_le": round(dat / len(CAU_HOI), 4),
           "vo_nghia_so_cau": len(CAU_VO_NGHIA), "vo_nghia_GIA_DAT": gia_dat,
           "chi_tiet": chi_tiet}
    RA.parent.mkdir(exist_ok=True)
    RA.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"tra dung {dat}/{len(CAU_HOI)}  (top {so_the} the moi cau)")
    print(f"chieu nguoc: {gia_dat}/{len(CAU_VO_NGHIA)} cau VO NGHIA cung 'dat'"
          + ("  <-- tu khoa mong doi qua long, con so tren KHONG tin duoc"
             if gia_dat else "  (dat: bo do biet noi khong)"))
    if truot:
        print(f"\nTRUOT {len(truot)}:")
        for cau, cho, the in truot:
            print(f"  ? {cau}")
            print(f"      cho mot trong: {cho}")
            for t in the:
                print(f"      ra: {t}")
    print(f"\n-> {RA}")
    return ket


if __name__ == "__main__":
    chay(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
