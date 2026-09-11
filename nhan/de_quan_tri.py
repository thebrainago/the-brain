# -*- coding: utf-8 -*-
"""de_quan_tri.py - CHEN bo quan tri cua ta vao MOT EA NGOAI, roi do bat/tat.

## Vi sao khong dung EA giam sat rieng

`dich_mq5_qtvt.sinh_ea_giam_sat` tao mot EA doc lap de DE LEN EA khac **khi chay
that**. Ghi chu trong chinh ham do noi ro: *khong backtest duoc cung nhau* - MT5
Strategy Tester chi chay MOT EA moi lan. Nen cong "de len EA ngoai -> so lenh
doi" khong do duoc bang cach cho hai EA chay song song.

Duong do duoc: ta CO MA NGUON. Seeker da tai ve 145 file `.mq5`, trong do 25 la
EA that (co `OnTick` + dat lenh) va 7 file khong phu thuoc thu vien ngoai nao.
Chen khoi quan tri vao chinh ma nguon do, bien dich mot lan, roi chay hai lan:

    QT_MaLuat = 0   quan tri TAT   -> moc
    QT_MaLuat = k   quan tri BAT   -> so voi moc

Cung EA, cung cua so, cung du lieu, cung mot lan bien dich. Chenh lech chi con
mot nguyen nhan.

## Ba cho phai chen, va vi sao khong the it hon

1. **truoc `OnTick`**: khoi quan tri (bien, bang luat, ham `QT_*`)
2. **dau `OnTick`**: goi `QT_Chay()` - quan tri phai chay TRUOC logic cua EA de
   no thay vi the o trang thai dau bar
3. **`OnInit`**: `QT_NapBang()` + `QT_ChonLuat(QT_MaLuat)`

Thieu (3) thi bang luat toan 0 va quan tri IM LANG khong lam gi - dung dang
"bo phan im lang" ma ca phien 11/09 gap nam lan.

## Chot: EA khong co OnInit

Mot so EA chi co `OnTick`. Khi do phai TU them `OnInit` - chen goi vao mot ham
khong ton tai thi bien dich bao loi, con bo qua thi quan tri chet lang le.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(GOC))

_RE_ONTICK = re.compile(r"^\s*void\s+OnTick\s*\(\s*\)\s*", re.M)
_RE_ONINIT = re.compile(r"^\s*int\s+OnInit\s*\(\s*\)\s*", re.M)


class KhongChenDuoc(Exception):
    pass


def _mo_than(s: str, tu: int) -> tuple[int, int]:
    """Vi tri dau `{` va `}` khop cua mot than ham bat dau tim tu `tu`."""
    i = s.find("{", tu)
    if i < 0:
        raise KhongChenDuoc("khong thay than ham")
    sau, j = 1, i + 1
    while j < len(s) and sau:
        if s[j] == "{":
            sau += 1
        elif s[j] == "}":
            sau -= 1
        j += 1
    if sau:
        raise KhongChenDuoc("than ham khong dong")
    return i, j - 1


#: HOP DONG cua `dich_mq5_qtvt.sinh_khoi*`, viet ro trong docstring cua no:
#:   "EA chu phai co `CTrade qt_trade;` va goi `QT_Khoi()` trong OnInit,
#:    `QT_KhopYDinh()` dau OnTick, `QT_MoiNen()` khi co nen moi."
#:
#: Khoi sinh ra la MOT MANH, khong phai mot EA. Lan chen dau tien cua toi goi
#: mot ham `QT_Chay()` khong he ton tai va khong khai `qt_trade` - trinh bien
#: dich bao 5 loi "undeclared identifier". Do la dieu TOT: mot hop dong duoc
#: trinh bien dich kiem thi khong hong im lang duoc.
DAU_KHOI = "#include <Trade" + chr(92) + "Trade.mqh>\nCTrade qt_trade;\n"
GOI_KHOI_TAO = "QT_Khoi(); QT_NapBang(); QT_ChonLuat(QT_MaLuat);"
GOI_MOI_TICK = "QT_DeQuanTri();"

#: Cau noi: gom `QT_KhopYDinh()` (moi tick) va `QT_MoiNen()` (moi nen) vao MOT
#: loi goi, de cho chen o EA ngoai chi la mot dong.
CAU_NOI = """
datetime g_qt_nen_de = 0;
void QT_DeQuanTri()
  {
   QT_KhopYDinh();
   datetime t = (datetime)SeriesInfoInteger(_Symbol, PERIOD_%(khung)s,
                                            SERIES_LASTBAR_DATE);
   if(t == g_qt_nen_de) return;
   g_qt_nen_de = t;
   QT_MoiNen();
  }
"""


def chen(ma_ea: str, khoi_qt: str, khung: str = "D1",
         goi_moi_tick: str = GOI_MOI_TICK,
         goi_khoi_tao: str = GOI_KHOI_TAO) -> str:
    """Chen khoi quan tri vao ma nguon mot EA. Tra ma moi."""
    m = _RE_ONTICK.search(ma_ea)
    if not m:
        raise KhongChenDuoc("khong tim thay `void OnTick()` - day khong phai EA")

    # 1. khoi quan tri dat NGAY TRUOC OnTick (sau moi #include va input cua EA)
    dau = "" if "CTrade qt_trade;" in ma_ea else DAU_KHOI
    ra = (ma_ea[:m.start()] + "\n" + dau + khoi_qt + "\n"
          + (CAU_NOI % {"khung": khung}) + "\n" + ma_ea[m.start():])

    # 2. goi quan tri o DAU OnTick
    m = _RE_ONTICK.search(ra)
    i, _ = _mo_than(ra, m.end())
    ra = ra[:i + 1] + "\n   " + goi_moi_tick + "\n" + ra[i + 1:]

    # 3. khoi tao bang luat
    mi = _RE_ONINIT.search(ra)
    if mi:
        i, _ = _mo_than(ra, mi.end())
        ra = ra[:i + 1] + "\n   " + goi_khoi_tao + "\n" + ra[i + 1:]
    else:
        # EA khong co OnInit -> TU THEM. Bo qua thi bang luat toan 0 va quan tri
        # im lang khong lam gi.
        m = _RE_ONTICK.search(ra)
        them = ("\nint OnInit()\n  {\n   " + goi_khoi_tao +
                "\n   return(INIT_SUCCEEDED);\n  }\n")
        ra = ra[:m.start()] + them + ra[m.start():]
    return ra


def chen_tu_spec(ma_ea: str, specs: list[dict], khung: str = "D1",
                 magic: int = 0, lot_goc: float = 0.1) -> tuple[str, list[dict]]:
    """Chen kho luat quan tri vao EA ngoai. -> (ma moi, luat da nap).

    `sinh_khoi_nhieu` tra ve CA danh sach luat da nap, va con so do phai di kem
    ma: `QT_MaLuat = k` chi co nghia khi biet k tro toi luat nao. Vut no di la
    cach nhanh nhat de doc mot bang ket qua ma khong biet dong nao la luat gi.
    """
    from nhan import dich_mq5_qtvt as Q
    khoi, luat = Q.sinh_khoi_nhieu(specs, khung=khung, magic=magic,
                                   lot_goc=lot_goc)
    return chen(ma_ea, khoi, khung=khung), luat


def kiem_da_chen(ma: str) -> list[str]:
    """Bien dich XONG khong co nghia la quan tri DANG CHAY. Kiem ba cho."""
    loi = []
    if GOI_MOI_TICK not in ma:
        loi.append("khong goi %s - quan tri khong bao gio chay" % GOI_MOI_TICK)
    if "QT_Khoi()" not in ma:
        loi.append("khong goi QT_Khoi() - khoi quan tri chua khoi tao")
    if "CTrade qt_trade;" not in ma:
        loi.append("thieu `CTrade qt_trade;` - khoi quan tri khong dat duoc lenh")
    if "QT_NapBang()" not in ma:
        loi.append("khong goi QT_NapBang() - bang luat toan 0, quan tri im lang")
    if "QT_ChonLuat" not in ma:
        loi.append("khong goi QT_ChonLuat - luon chay luat 0 (= tat)")
    m = _RE_ONTICK.search(ma)
    if m:
        i, j = _mo_than(ma, m.end())
        than = ma[i:j]
        if GOI_MOI_TICK in than:
            truoc = than.index(GOI_MOI_TICK)
            if len(than[:truoc].strip(" \n{")) > 4:
                loi.append("QT_Chay() khong o DAU OnTick - quan tri thay vi the "
                           "SAU khi EA da doi no trong chinh tick nay")
    return loi


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("go: python -m nhan.de_quan_tri <duong dan .mq5>")
        raise SystemExit(2)
    p = Path(sys.argv[1])
    ma = p.read_text(encoding="utf-8", errors="ignore")
    from nhan import quan_tri_dsl as QT
    kho = [c for c in QT.doc_kho() if not QT.kiem_khai_bao(c)][:12]
    moi, luat = chen_tu_spec(ma, kho, khung="D1", magic=20260911)
    loi = kiem_da_chen(moi)
    ra = GOC / "reports" / ("DE_QT_" + p.stem[:40] + ".mq5")
    ra.parent.mkdir(exist_ok=True)
    ra.write_text(moi, encoding="utf-8")
    print(json.dumps({"ea": p.name, "luat_nap": len(luat),
                      "byte_truoc": len(ma), "byte_sau": len(moi),
                      "loi_chen": loi, "ra": str(ra)},
                     ensure_ascii=False, indent=1))
