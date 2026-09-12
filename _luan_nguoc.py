# -*- coding: utf-8 -*-
"""BO LOC LUAN NGUOC - phan kieu chien luoc cua trader top tu dau chan cong khai.

Chu du an 05/09: *"xay bo loc luan nguoc chien luoc cua trader top"* +
*"chap nhan he thong dca, chap nhan DD cao hon"*.

Doc tu file DA LUU (`reports/signal_ho_so.json`), khong cao lai - nen doi
nguong phan loai la chuyen mot giay, khong phai 30 phut.

MOI KIEU CHAM BANG THUOC DO CUA CHINH KIEU DO. Day la thay doi that so voi cach
cu, khong phai cach viet lai:

  `luoi_dca` / `gong_lo`  -> **SONG BAO LAU** + **RUT KIP KHONG**.
      Sharpe cua lop nay vo nghia: hinh dang loi suat la nhieu lai nho + thua
      hiem va rat lon, nen Sharpe do tren doan CHUA CO cu thua se cao gia tao.
      Chinh #2359404 co Sharpe/lenh 0,18 nhung phoi nhiem dinh du de mot ngay
      te nhat cua vang 9,5 nam qua lay 100% tai khoan.
  `scalp` / `xu_huong`    -> loi suat tren mot don vi rui ro van doc duoc.

BA CON SO PHAI DOC KEM MOI KET LUAN:
  1. Thien lech song sot TOAN PHAN - chi thay tai khoan con song.
  2. `song_ngay` - mot he 200 ngay tuoi chua tra loi duoc cau hoi nao ve DCA.
  3. `lo_treo_dinh` - suc chiu lo treo DA THE HIEN, khong phai suc chiu toi da.
"""
from __future__ import annotations

import json
import sys
import warnings

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

import numpy as np

from nhan import dau_chan as DC
from pathlib import Path

NGUON = "reports/signal_ho_so.json"
RA = "reports/luan_nguoc.json"


def _tv(v, k):
    a = [x[k] for x in v if x.get(k) is not None]
    return float(np.median(a)) if a else None


def _f(x, n=2):
    return "-" if x is None else ("%.*f" % (n, x))


def chay() -> None:
    ho = json.load(open(NGUON, encoding="utf-8"))
    for x in ho:
        k, ly_do = DC.phan_loai(x)
        x["kieu"], x["ly_do_kieu"] = k, ly_do
    json.dump(ho, open(RA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("=" * 84)
    print("LUAN NGUOC KIEU CHIEN LUOC - %d ho so" % len(ho))
    print("=" * 84)
    print("Luat phan loai (khai bao truoc khi chay, xet theo thu tu):")
    print("  1 luoi_dca : (nhoi_khi_lo>%.2f HOAC bac_tai>=%d) VA lo_treo>=%.2f "
          "VA thang>=%.0f%%" % (DC.NHOI_KHI_LO, DC.BAC_TAI, DC.LO_TREO, DC.THANG_PCT))
    print("  2 gong_lo  : cat_sach>%.1f VA lo_treo>=%.2f" % (DC.CAT_SACH_GONG, DC.LO_TREO))
    print("  3 scalp    : giu<=%.0f phut VA cat_sach<=1,0" % DC.GIU_SCALP)
    print("  4 xu_huong : giu>=%.0f phut VA cat_sach<=1,0" % DC.GIU_XU_HUONG)
    print("  5 khong_ro : con lai")
    print()

    print("%-11s %5s %8s %8s %8s %8s %8s %8s %8s"
          % ("kieu", "so he", "song(ng)", "tang%", "PF", "thang%", "nhoi", "treo",
             "giu(ph)"))
    for k in DC.KIEU:
        v = [x for x in ho if x["kieu"] == k]
        if not v:
            continue
        print("%-11s %5d %8s %8s %8s %8s %8s %8s %8s"
              % (k, len(v), _f(_tv(v, "song_ngay"), 0),
                 _f(_tv(v, "tang_truong_pct"), 0), _f(_tv(v, "pf")),
                 _f(_tv(v, "thang_pct"), 0), _f(_tv(v, "nhoi_khi_lo"), 3),
                 _f(_tv(v, "lo_treo_dinh"), 3), _f(_tv(v, "giu_phut"), 0)))
    print()

    # ------------------------------------------------ lop DCA: thuoc do rieng
    dca = [x for x in ho if x["kieu"] in ("luoi_dca", "gong_lo")]
    print("--- LOP CHAP NHAN LO TREO (%d he) - cham bang SONG BAO LAU ---" % len(dca))
    if not dca:
        print("  khong he nao khop. Neu mau toan he cat lo thi day la thong tin")
        print("  ve BANG XEP HANG, khong phai ve thi truong.")
    else:
        print("  %-9s %-24s %7s %8s %9s %7s %7s %7s"
              % ("id", "symbol", "song", "tang%", "nhoi", "bac", "treo", "thang%"))
        for x in sorted(dca, key=lambda z: -(z.get("song_ngay") or 0))[:25]:
            print("  %-9d %-24s %7s %8s %9s %7s %7s %7s"
                  % (x["id"], ",".join(x["symbol"])[:24],
                     _f(x.get("song_ngay"), 0), _f(x.get("tang_truong_pct"), 0),
                     _f(x.get("nhoi_khi_lo"), 3), _f(x.get("bac_tai"), 1),
                     _f(x.get("lo_treo_dinh"), 3), _f(x.get("thang_pct"), 0)))
        s = np.array([x["song_ngay"] for x in dca if x.get("song_ngay")], float)
        print()
        print("  tuoi doi: trung vi %.0f ngay (%.1f nam), gia nhat %.0f ngay"
              % (np.median(s), np.median(s) / 365.25, s.max()))
        print("  >> Mot lop song bang cach hiem khi thua thi TUOI DOI la bang")
        print("     chung DUY NHAT co gia tri, va cai duoi 2 nam khong noi gi.")
        gia = [x for x in dca if (x.get("song_ngay") or 0) >= 730]
        print("  he DCA/gong lo song >= 2 nam: %d/%d" % (len(gia), len(dca)))

    # ---------------------------------------------- doi chieu hai lop voi nhau
    print()
    print("--- DOI CHIEU: lop chiu lo treo vs lop cat lo ---")
    cat = [x for x in ho if x["kieu"] in ("scalp", "xu_huong")]
    for ten, v in (("chiu lo treo (dca+gong)", dca), ("cat lo (scalp+xu huong)", cat)):
        if not v:
            continue
        s = [x["song_ngay"] for x in v if x.get("song_ngay")]
        t = [x["tang_truong_pct"] for x in v if x.get("tang_truong_pct") is not None]
        print("  %-26s n=%3d  tuoi trung vi %5.0f ngay  tang truong trung vi %7.0f%%"
              % (ten, len(v), np.median(s) if s else 0, np.median(t) if t else 0))
    print()
    print("  Doc dung: hai cot nay KHONG so sanh duoc ve 'kieu nao tot hon' - ca")
    print("  hai deu chi gom nguoi CON SONG. No chi tra loi: kieu nao TON TAI o")
    print("  quy mo nao, va da song bao lau.")
    print()
    print("chi tiet -> %s" % RA)


if __name__ == "__main__":
    chay()
