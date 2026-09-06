# -*- coding: utf-8 -*-
"""_boc_lai_vung.py - BOC LAI HO VUNG BANG NGU PHAP DA CO NGUYEN THUY `vung`.

## VI SAO CHAY LAI DUNG NHOM NAY

Truoc 06/09/2026 ngu phap chi noi duoc so sanh THEO TUNG NEN. Mot khoang trong
gia (FVG), mot order block, mot vung cung cau la VAT THE song qua nhieu nen - co
bien tren, bien duoi, chet khi bi lap day. Bo boc khong dien duoc dieu do, nen
no lam dieu te nhat co the: dien `hang: 0` vao cho nguong khong doc duoc. Ket
qua la ca ho tro thanh dieu kien hien nhien (`low < 0`, `close > 0`), va bo chan
moi ngay 06/09 bat dung chung.

Nay ngu phap co `vung`. Nhom nay dang duoc boc lai voi CUNG bo tim vung, CUNG
cong, chi khac mot dieu: loi nhac gio mo ta duoc thu ma truoc day khong mo ta
duoc.

## KHONG QUET CA KHO

Chay lai 389 file la lang phi: 334 file khong thuoc ho vung, va ban boc cu cua
chung khong sai vi thieu `vung`. Chi chay tren file co dau hieu VUNG - vua re
vua cho mot phep do sach: **suat boc cua rieng ho nay, truoc va sau khi co
nguyen thuy**.

Chay: python _boc_lai_vung.py [--that] [--gioi-han N]
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

LAB = Path(__file__).resolve().parent

#: Dau hieu HO VUNG. Bat theo TEN file hoac theo mat do tu khoa trong ma - mot
#: file ten trung tinh (`SNR.mq5`) van co the la ca mot bo do vung cung cau.
RX_VUNG = re.compile(
    r"(?i)\b(fvg|fair.?value.?gap|order.?block|orderblock|imbalance|liquidity|"
    r"sweep|supply.?demand|smc|market.?structure|bos|choch|orb|opening.?range|"
    r"zone|support.?resistance|s\&r|snr|demand|supply)")


#: Chi dan CHEN THEM vao ban tom tat ngu phap cho rieng lop file nay.
#:
#: Do 06/09/2026: ban tom tat DA liet ke nguyen thuy `vung`, nhung luot dau cho
#: **0/9 khai bao dung no**. Ly do khong phai mo hinh yeu: loi nhac cua
#: `doc_chi_bao` ket bang mot VI DU tra ve chi co dang `{"trai","phep","phai"}`,
#: va mo hinh bam vi du chu khong bam ban tham chieu. Dung ho benh voi "cong doi
#: truong `co_che` ma loi nhac chua bao gio xin" (ban giao 05/09).
CHI_DAN = """

== LUU Y RIENG CHO LO FILE NAY ==
File nay thuoc ho VUNG (FVG / order block / cung cau / thanh khoan / ORB /
khang cu ho tro). Neu ma nguon VE MOT HOP hoac ghi nho MOT MUC GIA roi cho gia
quay lai cham vao, thi do la mot VUNG - PHAI dung dang `dk_vung` o tren, khong
duoc ep no thanh so sanh tung nen.

Dau hieu nhan ra trong ma: `ObjectCreate(...OBJ_RECTANGLE...)`, mot mang luu
`zoneTop[]`/`zoneBottom[]`, mot bien nho lai `lastHigh`/`obLow` roi so sanh o
cac nen SAU, mot vong lap `for(j=i; j<i+N; j++)` de xem gia co cham lai khong.

Neu ban ep mot vung thanh dieu kien tung nen thi ket qua se la mot ve LUON DUNG
(vd `close > 0`) va he se loai no. Tha tra ve "khong_dien_dat_duoc" con hon.

Trong lo nay, mot khai bao DAT thuong co hinh:
  {"ten": "...", "co_che": "...", "ho": "pha_vo", "chieu": 1, "giu": 5,
   "vao": [ <dk_vung>, <dk thuong neu co them bo loc> ]}
"""


def ds_ho_vung(gioi_han: int = 0) -> list[dict]:
    from nhan import doc_chi_bao as DC
    from nhan import phan_loai_ma as PL
    ra = []
    for d in PL._doc_kho_ma():
        if not (RX_VUNG.search(d["ten"])
                or len(RX_VUNG.findall(d["src"][:20000])) >= 3):
            continue
        if not DC.vung_tin_hieu(d["src"]):
            continue                       # khong khoanh duoc gi -> khong goi LLM
        ra.append(d)
        if gioi_han and len(ra) >= gioi_han:
            break
    return ra


def _dem_vung(cc: list) -> int:
    return sum(1 for c in cc
               for v in (c.get("vao") or []) + (c.get("ra") or [])
               if isinstance(v, dict) and "vung" in v)


def chay(gioi_han: int = 0, that: bool = False, in_ra=print) -> dict:
    from nhan import boc_llm as BL
    from nhan import boc_ma_llm as BM
    from nhan import doc_chi_bao as DC
    from nhan import loc_co_che as LCC
    from nhan import ngu_phap as NP

    ds = ds_ho_vung(gioi_han)
    in_ra("HO VUNG: %d file co dau hieu vung VA khoanh duoc vung tin hieu"
          % len(ds))
    if not ds:
        return {"so_file": 0}

    tom_tat = BL._ngu_phap_tom_tat()
    if "VUNG (" not in tom_tat:
        # Khong co dong nay thi ca luot chi lap lai ban boc cu, va se bao "0 co
        # che moi" - doc y het mot ket qua am that.
        in_ra("  !! ban tom tat ngu phap KHONG co muc VUNG - dung.")
        return {"loi": "tom_tat_thieu_vung"}

    ket = DC._chay(ds, 2, in_ra, tom_tat + CHI_DAN)
    cd = [k for k in ket if k.get("chua_do")]
    if cd and len(cd) == len(ds):
        in_ra("  !! CA ME KHONG GOI DUOC: %s" % cd[0]["vi_sao"])
        return {"so_file": len(ds), "chua_do": len(cd)}

    tho = LAB / "reports" / "BOC_LAI_VUNG_tho.json"
    tho.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")

    tong = sum(len(k["co_che"]) for k in ket)
    co_vung = sum(_dem_vung(k["co_che"]) for k in ket)
    giu, ho = [], []
    for k in ket:
        g, h = BM.kiem_va_giu(k["co_che"], nguon=k["ten"])
        giu += g
        ho += h
    in_ra("")
    in_ra("  file ra co che    : %d/%d" % (sum(1 for k in ket if k["co_che"]), len(ds)))
    in_ra("  khai bao          : %d  (trong do dung VUNG: %d)" % (tong, co_vung))
    in_ra("  qua kiem khai bao : %d" % len(giu))
    if ho:
        in_ra("  bi loai: " + "; ".join(ho[:5]))

    them, tu_choi = 0, Counter()
    if that and giu:
        df_kiem = LCC.df_kiem_chuan()
        if df_kiem is None:
            in_ra("  !! khong nap duoc chuoi kiem - KHONG ghi kho (khong ha cong)")
        else:
            for c in giu:
                c["nguon_lan"] = "vung"
                r = NP.them_co_che(c, df_kiem)
                if r.get("nhan"):
                    them += 1
                else:
                    tu_choi[str(r.get("ly_do", ["?"])[0])[:60]] += 1
            in_ra("  them vao kho      : %d" % them)
            for k, v in tu_choi.most_common(6):
                in_ra("    tu choi %-52s %d" % (k, v))
    elif not that:
        in_ra("\n  (chua ghi - them --that)")

    ra = {"so_file": len(ds), "khai_bao": tong, "dung_vung": co_vung,
          "qua_kiem": len(giu), "them_kho": them,
          "tu_choi": dict(tu_choi)}
    (LAB / "reports" / "BOC_LAI_VUNG.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    return ra


def main() -> int:
    gh = 0
    if "--gioi-han" in sys.argv:
        gh = int(sys.argv[sys.argv.index("--gioi-han") + 1])
    chay(gh, "--that" in sys.argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
