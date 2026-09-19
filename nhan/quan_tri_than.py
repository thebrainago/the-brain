# -*- coding: utf-8 -*-
"""quan_tri_than.py - BOC QUAN TRI LENH TU THAN HAM, khong tu ten input.

Chu du an 18/09/2026: *"Nó còn làm được hơn nữa. Nhưng cách tỉa lệnh cần tinh
vi hơn - cần tìm các EA có khả năng tỉa lệnh để rút lõi phần quản lý lệnh."*

## VI SAO KHONG DU KHI CHI CO `quan_tri.py`

`quan_tri.boc_mot` doc **ten cac `input`** roi anh xa sang nut van cua
`mo_phong_v2`. Cach do chi thay duoc phan tac gia CHO NGUOI DUNG CHINH. Do
ngay 19/09/2026 tren 10 file `.mq5` trong `mau_thu/`:

    boc duoc 5/10 file, va moi file chi ra **DUNG MOT** nut van.

Mot nut thi `quan_tri.loc` gat het (dieu kien 1: phai >= 2 nut chay duoc). Tuc
ca bo mau ra **khong co che nao dung duoc**, trong khi doc bang mat thi
`EA Snippets_Breakout_Breakout2.mq5` co han mot co che chot lenh hoan chinh:

    if(peakwin>=45 && profits<(peakwin*0.9))   CloseAll();   // ROT DINH LAI
    if(profits<=-120)                          CloseAll();   // dung lo ca ro

Do la **trailing tren lai CA RO** - dung ho voi `tia_lenh`, thu da bien AUDCAD
tu +0,66%/nam thanh +13,26%/nam. Va no vo hinh voi bo boc theo ten input vi ca
ba con so 45 · 0,9 · 120 deu **viet cung trong ma**, khong co `input` nao het.

## RANH GIOI (giong `doc_ma.py` va `ma_nguon.py`)

**Khong bao gio chay ma tai ve.** O day chi doc van ban bang bieu thuc chinh
quy. Dau ra la DU LIEU - mot bang nut van - khong phai ma.

## BA CHO DE NHAN BUA, deu da co test chan

1. **Dong da chu thich.** Ban goc de day `//if(postotal==2&&peakwin>=25...)` -
   do la nhung ban tac gia DA BO. Dem chung la doc ra mot EA chua tung chay.
2. **Nguong khong phai hang so.** `profits <= -InpMaxLoss` thi gia tri nam o
   input, khong duoc doan. Khong doc duoc thi bo, khong dien bua.
3. **So sanh khong dan toi dong ro.** `if(profits>=200) Print(...)` khong phai
   lenh chot. Phai truy dung toi mot ham CO dong vi the moi tinh.

## DON VI - doc ky truoc khi so hai EA voi nhau

`chot_tien` / `dung_lo` / `_chot_lui_tu` la **TIEN TAI KHOAN**, nen chung chi
co nghia cung voi LOT ma EA chay. Hai EA cung dat `dung_lo=120` nhung mot cai
chay 0,01 lot con cai kia 1,0 lot la hai co che khac han nhau. Bo boc tra ve
`lot_goc` khi doc duoc, de ben dung con quy doi.

`hedge_tu` la **DIEM** (`_Point`), khong phai pip: tren ma 5 chu so 300 diem =
30 pip. Quy doi thuoc ve ben dung, vi so chu so phu thuoc symbol.

## NUT CO TIEN TO `_` LA CHUA MO PHONG DUOC

`mo_phong_v2` chua co nut cho "rot dinh lai ca ro" (`_chot_lui_*`) va cho tia
mot phan vi the (`_tia_*`). Van boc ra va danh dau, dung nhu `quan_tri.py` da
lam voi `trailing`: **biet dang bo lo gi con hon bo im lang**.
"""
from __future__ import annotations

import re

_TEN = r"[A-Za-z_][A-Za-z0-9_]*"
_SO = r"[-+]?\d+(?:\.\d+)?"

#: Ham dong CA RO: lap tren `PositionsTotal()` va goi mot ham dong vi the.
_DONG_VI_THE = re.compile(r"PositionClose[ \t]*\(|OrderClose[ \t]*\(")
_LAP_RO = re.compile(r"PositionsTotal[ \t]*\(")

#: Than ham cong don `POSITION_PROFIT` -> ham tra ve LAI CA RO.
_CONG_LAI = re.compile(r"\+=[^\n;]*POSITION_PROFIT")

#: `peak = MathMax(peak, lai)` - bien theo DINH cua lai ro.
_DINH = re.compile(rf"({_TEN})[ \t]*=[ \t]*MathMax[ \t]*\([ \t]*(\1)[ \t]*,[ \t]*({_TEN})")

#: `Tradesinfo.hedgeprice = price - (hedgerange*_Point)` - khoang cach hedge.
_HEDGE = re.compile(
    rf"hedgeprice[ \t]*=[^\n;]*?[-+][ \t]*\(?[ \t]*({_TEN}|{_SO})[ \t]*\*"
    rf"[ \t]*_Point", re.I)

#: `PositionClosePartial(sym, vol*0.5)` - tia mot phan vi the.
_TIA = re.compile(rf"PositionClosePartial[ \t]*\([^;]*?\*[ \t]*({_SO})")

#: Khai bao ham kieu C, de cat than ham.
_HAM = re.compile(rf"^[ \t]*(?:static[ \t]+)?(?:void|int|double|bool|long|datetime"
                  rf"|string|float)[ \t]+({_TEN})[ \t]*\([^;{{]*\)[ \t]*$", re.M)


def _bo_chu_thich(src: str) -> str:
    """Bo chu thich `//` va `/* */`.

    Dong da chu thich la ban tac gia DA BO. `EA Snippets_Breakout_Breakout2`
    de lai bon dong `//if(postotal==N&&peakwin>=...)` - dem chung la doc ra mot
    EA chua tung chay, va la mot bang so hoan toan hop le trong nhin.
    """
    src = re.sub(r"/\*.*?\*/", " ", src or "", flags=re.S)
    return re.sub(r"//[^\n]*", "", src)


def _hang_so(x: str, hang: dict) -> float | None:
    """So tho, hoac mot bien da biet gia tri. Khong biet thi None - khong doan."""
    x = (x or "").strip()
    if re.fullmatch(_SO, x):
        return float(x)
    return hang.get(x)


def _bang_hang(src: str) -> dict:
    """Ten -> gia tri, cho ca `input int N = 300;` lan `int n = N;`."""
    ra: dict[str, float] = {}
    for m in re.finditer(
            rf"^[ \t]*(?:(?:input|sinput|extern|static|const)[ \t]+)*"
            rf"(?:int|double|float|long|uint|ulong|short)[ \t]+({_TEN})[ \t]*=[ \t]*"
            rf"({_TEN}|{_SO})[ \t]*;", src, re.M):
        v = _hang_so(m.group(2), ra)
        if v is not None:
            ra.setdefault(m.group(1), v)
    return ra


def _cac_ham(src: str) -> dict:
    """Ten ham -> than ham (tu dau `{` toi `}` can bang)."""
    ra = {}
    for m in _HAM.finditer(src):
        i = src.find("{", m.end())
        if i < 0:
            continue
        muc, j = 0, i
        while j < len(src):
            if src[j] == "{":
                muc += 1
            elif src[j] == "}":
                muc -= 1
                if muc == 0:
                    break
            j += 1
        ra[m.group(1)] = src[i:j]
    return ra


def boc_than(src: str) -> dict:
    """Ma nguon EA -> nut van quan tri lenh doc tu THAN HAM.

    Tra ve ca bo khung tim duoc (`ham_lai_ro`, `ham_dong_ro`, `bien_lai_ro`,
    `bien_dinh`) chu khong chi `nut_van`: khi mot EA that ra `nut_van` rong,
    bo khung noi ro no rong o CHANG NAO - thieu ham dong ro, hay co ham nhung
    khong nguong nao la hang so. Hai cai do phai sua o hai cho khac nhau.
    """
    src = _bo_chu_thich(src or "")
    hang = _bang_hang(src)
    ham = _cac_ham(src)

    ham_lai = {t for t, b in ham.items() if _CONG_LAI.search(b)}
    ham_dong = {t for t, b in ham.items()
                if _DONG_VI_THE.search(b) and _LAP_RO.search(b)}

    # Bien mang lai ca ro: gan tu mot ham tinh lai ro, hoac tu chinh phep cong don.
    bien_lai = set()
    for t in ham_lai:
        for m in re.finditer(rf"({_TEN})[ \t]*=[ \t]*{re.escape(t)}[ \t]*\(", src):
            bien_lai.add(m.group(1))
    for m in re.finditer(rf"({_TEN})[ \t]*\+=[^\n;]*POSITION_PROFIT", src):
        bien_lai.add(m.group(1))

    bien_dinh = {m.group(1) for m in _DINH.finditer(src)
                 if m.group(3) in bien_lai}

    nut: dict[str, float] = {}
    if hang:
        for k in ("InpLot", "Inp_Lot", "Lots", "LotSize"):
            if k in hang:
                nut["lot_goc"] = hang[k]
                break

    thieu: list[str] = []
    for dk, than in _cac_if(src):
        if not _goi_ham_dong(than, ham_dong):
            continue                      # so sanh khong dan toi dong ro
        _doc_nguong(dk, bien_lai, bien_dinh, hang, nut, thieu)

    # --- khoang cach hedge, doc trong than ham ---
    m = _HEDGE.search(src)
    if m:
        v = _hang_so(m.group(1), hang)
        if v is not None:
            nut["hedge_tu"] = v

    # --- tia mot phan vi the ---
    m = _TIA.search(src)
    if m:
        nut["_tia_ty"] = float(m.group(1))
        for dk, than in _cac_if(src):
            if "PositionClosePartial" not in than:
                continue
            mm = re.search(rf"POSITION_PROFIT[^<>]*>=?[ \t]*({_SO})", dk)
            if mm:
                nut["_tia_tu"] = float(mm.group(1))
            break

    return {"nut_van": nut, "ham_lai_ro": sorted(ham_lai),
            "ham_dong_ro": sorted(ham_dong), "bien_lai_ro": sorted(bien_lai),
            "bien_dinh": sorted(bien_dinh), "thieu": sorted(set(thieu))}


#: `if(<dieu kien>)` - lay ca dieu kien lan doan ma NGAY SAU no.
_IF = re.compile(r"\bif[ \t]*\(")


def _cac_if(src: str) -> list[tuple[str, str]]:
    """(dieu kien, doan than ngay sau) cho moi `if` trong ma."""
    ra = []
    for m in _IF.finditer(src):
        muc, j = 0, m.end() - 1
        while j < len(src):
            if src[j] == "(":
                muc += 1
            elif src[j] == ")":
                muc -= 1
                if muc == 0:
                    break
            j += 1
        dk = src[m.end():j]
        con = src[j + 1:j + 400]
        # Than cua `if`: mot khoi `{...}`, hoac dung mot lenh toi dau `;`.
        k = con.find("{")
        if 0 <= k <= 3:
            ra.append((dk, con[:con.find("}") if "}" in con else len(con)]))
        else:
            ra.append((dk, con[:con.find(";") + 1 if ";" in con else len(con)]))
    return ra


def _goi_ham_dong(than: str, ham_dong: set) -> bool:
    """Doan ma nay co that su dong ca ro khong."""
    if _DONG_VI_THE.search(than):
        return True
    return any(re.search(rf"\b{re.escape(t)}[ \t]*\(", than) for t in ham_dong)


def _doc_nguong(dk: str, bien_lai: set, bien_dinh: set, hang: dict,
                nut: dict, thieu: list) -> None:
    """Mot dieu kien dan toi `dong ca ro` -> nut van tuong ung."""
    # ROT DINH LAI: `dinh >= A && lai < dinh * B`. Phai co CA HAI ve - chi mot
    # ve `lai < dinh*B` thi co che kich hoat ngay tu dong lai dau tien.
    m_vu = re.search(rf"({_TEN})[ \t]*>=?[ \t]*({_TEN}|{_SO})", dk)
    m_lui = re.search(rf"({_TEN})[ \t]*<=?[ \t]*\(?[ \t]*({_TEN})[ \t]*\*"
                      rf"[ \t]*({_TEN}|{_SO})", dk)
    if (m_vu and m_lui and m_vu.group(1) in bien_dinh
            and m_lui.group(1) in bien_lai and m_lui.group(2) in bien_dinh):
        a = _hang_so(m_vu.group(2), hang)
        b = _hang_so(m_lui.group(3), hang)
        if a is not None and b is not None:
            nut.setdefault("_chot_lui_tu", a)
            nut.setdefault("_chot_lui_ty", b)
        else:
            # DOC DUOC CO CHE nhung KHONG doc duoc so. Hai thu nay khac nhau va
            # phai bao khac nhau: im lang o day thi ban quet doc y het "EA nay
            # khong co chot theo dinh lai" - dung cai lan CHUA_DO_DUOC voi AM
            # ma du an da cam. `Breakout5-2-2` la ca nay that: nguong vu trang
            # la `takeprofitamountperstartvolume*GetStartVolume()`, tuc no CO
            # gian theo lot, nen mot hang so o day se la con so sai.
            thieu.append("chot_lui: %s hoac %s khong phai hang so"
                         % (m_vu.group(2), m_lui.group(3)))
        return

    for m in re.finditer(rf"({_TEN})[ \t]*(<=|>=|<|>)[ \t]*({_TEN}|{_SO})", dk):
        if m.group(1) not in bien_lai:
            continue
        v = _hang_so(m.group(3), hang)
        if v is None:
            thieu.append("nguong ca ro: `%s` khong phai hang so" % m.group(3))
            continue                      # nguong nam o mot input - khong doan
        if m.group(2).startswith("<") and v < 0:
            nut.setdefault("dung_lo", abs(v))     # `lai <= -120` la dung lo 120
        elif m.group(2).startswith(">") and v > 0:
            nut.setdefault("chot_tien", v)
