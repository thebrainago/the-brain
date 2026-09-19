# -*- coding: utf-8 -*-
"""doc_ma.py - DOC MA NGUON THANH NHIEU KHAI BAO CO CHE.

VI SAO CO FILE NAY (chu du an chot 01/09/2026).

Do phieu chuyen doi ngay 01/09 cho thay cho sup khong nam o khau doc ma o khau
BIEN DICH:

    1.905 ban doc -> 376 ung vien -> 460 viec, nhung chi **43 mau rieng biet**
    -> 3 gia thuyet truy nguyen duoc ve tai lieu.

Ba nguyen nhan, deu do duoc:

  1. `bien_dich_ung_vien.do_khop` la bo NHAN DIEN tu khoa, khong phai bo TRICH
     XUAT. Mot tai lieu chi thanh ung vien bang cach goi ten mot mau DA CO trong
     thu vien; theo cau tao no khong bao gio them duoc mot kieu danh moi.
     375/376 ung vien tro vao mau da ton tai.
  2. `TRAN_MOI_TAI_LIEU = 2` - tran cung 2 mau moi tai lieu.
  3. Duong trich co che bi TAT cho ma nguon:
     `if che_do == "van_xuoi" and loai_ban_doc not in ("ma_nguon", ...)`.
     Tuc 247 ban doc MA NGUON - EA MQL5 va Pine, nguon dac nhat, suat ra ung
     vien cao nhat (20,2% so voi 11,9% cua bai bao) - chi duoc so khop tu khoa.

Muc 3 duoc tat ngay 23/08 vi mot ly do DUNG: chu thich markdown trong repo de ra
hai co che sai (`mua_rsi30_tren_70`, `mua_rsi14_tren_30`). Nhung cai duoc tat la
bo doc VAN XUOI; con chinh doan MA thi chua ai doc. Hai thu khac han nhau: van
xuoi noi "mua khi RSI thap" (mo ho o dung cho quan trong nhat), con ma viet
`rsi(close,14) < 30` (khong mo ho gi).

File nay la bo doc MA. No khong doan nghia tu tieng nguoi - no doc ky hieu:

    ma89 = ema(close, 89)        -> bang ky hieu: ma89 = {chi_bao ema, n 89}
    longCond = close > ma89      -> dieu kien: gia.close > ema(89)
    -> khai bao co che day du theo `nhan/ngu_phap.py`

Va no tra ve NHIEU khai bao cho MOT file, dung nhu chu du an noi: mot EA hay mot
Pine script tuong duong nhieu kieu danh. Moi dieu kien so sanh doc lap la mot
kieu danh rieng, de cong tu cham diem tung cai - thay vi gop ca file thanh mot
cai nhan `rsi_dao_chieu` roi chay lai dung luoi tham so cu.

RANH GIOI KHONG DOI (giong `ma_nguon.py` va `thu_hoi_thanh_phan.py`):
**khong bao gio chay ma tai ve**. O day chi doc van ban bang bieu thuc chinh
quy. Dau ra la DU LIEU (khai bao theo ngu phap da kiem duyet), khong phai ma.
Quyen nhan hay tu choi van thuoc `ngu_phap.them_co_che` - no chay ty le kich
hoat va phep cat nhin truoc truoc khi cho vao kho.
"""
from __future__ import annotations

import re

from nhan import thu_hoi_thanh_phan as TP

#: Phep so sanh trong ma -> phep cua ngu phap.
_PHEP = {">": ">", ">=": ">=", "<": "<", "<=": "<="}

#: Ho co che suy tu chi bao. Khong doan duoc thi `khac` - cong van xet binh
#: thuong, chi la khong duoc gom nhom cung ho.
_HO = {
    "rsi": "quay_ve_trung_binh", "ibs": "quay_ve_trung_binh",
    "zscore": "quay_ve_trung_binh", "phan_vi": "quay_ve_trung_binh",
    "ema": "xu_huong", "sma": "xu_huong", "tb": "xu_huong",
    "cao_nhat": "pha_vo", "thap_nhat": "pha_vo",
    "atr": "bien_dong", "do_lech": "bien_dong", "bien_do": "bien_dong",
    "gio": "phien", "ngay_trong_tuan": "lich", "ngay_trong_thang": "lich",
    "thang": "lich", "khoi_luong": "dong_tien",
}

#: Ten cot gia viet trong ma -> toan hang gia cua ngu phap.
_GIA = {"close": "close", "open": "open", "high": "high", "low": "low",
        # --- MQL5 (them 05/09) ---
        "bid": "close", "ask": "close",
        "iclose": "close", "iopen": "open", "ihigh": "high", "ilow": "low",
        "close[0]": "close", "price": "close", "last": "close",
        "currentprice": "close", "gia": "close"}

#: HAM CHI BAO cua MQL5 -> chi bao DSL. `iMA(sym,tf,n,shift,method,price)`:
#: doi so 5 la phuong phap (MODE_SMA=0, MODE_EMA=1) - lay `n` o doi so 3.
_HAM_MQL5 = {
    "irsi": ("rsi", 2), "iatr": ("atr", 2), "icci": ("cci", 2),
    "iadx": ("adx", 2), "imomentum": ("dong_luong", 2),
    "istdev": ("do_lech", 2), "ihighest": ("cao_nhat", 3),
    "ilowest": ("thap_nhat", 3), "ibands": ("bollinger", 2),
    "imacd": ("macd", 2), "istochastic": ("stochastic", 2),
    "iobv": ("obv", None), "ima": ("sma", 2), "iema": ("ema", 2),
}
#: `iMA(...)` voi MODE_EMA o doi so phuong phap -> ema thay vi sma.
_RX_HAM_MQL5 = re.compile(r"^(i[A-Za-z]+)[ \t]*\((.*)\)$", re.S)


def _tu_ham_mql5(tu: str) -> dict | None:
    """`iRSI(_Symbol,PERIOD_H1,14,PRICE_CLOSE)` -> {chi_bao: rsi, n: 14}."""
    m = _RX_HAM_MQL5.match(tu.strip())
    if not m:
        return None
    ten = m.group(1).lower()
    if ten not in _HAM_MQL5:
        return None
    cb, vt_n = _HAM_MQL5[ten]
    doi = [d.strip() for d in m.group(2).split(",")]
    if cb == "sma" and any("MODE_EMA" in d or "MODE_SMMA" in d for d in doi):
        cb = "ema"
    if vt_n is None:
        return {"chi_bao": cb}
    n = None
    if vt_n < len(doi):
        try:
            n = int(float(doi[vt_n]))
        except ValueError:
            n = None
    if n is None or n <= 0:
        return None                 # chu ky la BIEN -> khong chot duoc, bo
    ra = {"chi_bao": cb, "n": n}
    if cb in ("cao_nhat", "thap_nhat"):
        ra["cua"] = {"chi_bao": "gia",
                     "cot": "high" if cb == "cao_nhat" else "low"}
    return ra

#: Toan tu CUA SO: tinh tren mot toan hang khac, bat buoc co truong `cua`.
_CAN_CUA = {"cao_nhat", "thap_nhat", "tb", "do_lech", "zscore", "phan_vi",
            "doi", "doi_pct", "tre", "tuyet_doi"}
_CUA_MAC_DINH = {"cao_nhat": "high", "thap_nhat": "low"}

#: Chi bao co THANG DO BI CHAN (0-100, 0-1, gio, thang...) - so sanh voi mot
#: hang so la co nghia.
_CO_CHAN = {"rsi", "ibs", "phan_vi", "zscore", "gio", "ngay_trong_tuan",
            "ngay_trong_thang", "thang", "doi_pct"}

#: Chi bao o THANG DO GIA - so sanh voi mot hang so tran la vo nghia: `input(1.5)`
#: cua mot he so nhan bi doc thanh nguong gia. Do that tren Sonic R: sinh ra
#: `open < 2` va `ema34_high < 1.5`, ca hai kich hoat 100% so bar.
_THANG_GIA = {"gia", "ema", "sma", "cao_nhat", "thap_nhat", "atr", "do_lech",
              "bien_do", "than_nen", "tb", "khoi_luong"}

_TEN = r"[A-Za-z_][A-Za-z0-9_]*"
_SO = r"[-+]?\d+(?:\.\d+)?"

#: TU KHOA KIEU o dau mot khai bao bien C/MQL5: `bool up = ...`, `double ma =
#: ...`, `input int Chu_ky = 14;`. Vi sao day la mot LOP loi chu khong phai mot
#: cho: ca `_GAN_BOOL` lan `_GAN` cua `thu_hoi_thanh_phan` deu viet cho Pine,
#: noi bien khong co kieu (`ma89 = ema(close,89)`). Gap MQL5 thi ca hai truot
#: SACH, bang ky hieu rong, va moi bien trung gian thanh mot dinh danh tran ma
#: `_no_dieu_kien` khong truy nguoc duoc. Do 18/09/2026 tren 10 file .mq5 mau:
#: 22 diem vao lenh -> 0 co che, va day la nguyen nhan hang dau.
_KIEU_C = (r"(?:(?:static|const|extern|input|sinput|virtual)[ \t]+)*"
           r"(?:bool|char|uchar|short|ushort|int|uint|long|ulong|float|double"
           r"|datetime|color|string)[ \t]+")

#: TRUONG GIA cua `MqlRates` - dang viet gia pho bien nhat cua MQL5:
#: `rates[0].close`. Chi nhan khi co CHI SO (`[k]`) va truong thuoc bang nay;
#: `Tradesinfo.initup` (co trang thai cua EA, khong co chi so) van bi tu choi.
_TRUONG_GIA = {"open": "open", "high": "high", "low": "low", "close": "close"}

#: Mot ve cua phep so sanh: ten (co the co `[k]` va `.truong`), hoac so.
_VE = rf"{_TEN}(?:\[\d+\])?(?:\.{_TEN})?|{_SO}"

#: `ten = <loi goi chi bao>` - bat ca Pine (`ema(close,89)`, `ta.ema(...)`) lan
#: MQL (`iMA(...)`, `iRSI(...)`).
_GAN_CB = re.compile(
    rf"^[ \t]*(?:{_KIEU_C})?({_TEN})[ \t]*=[ \t]*"
    rf"((?:ta\.)?{_TEN}[ \t]*\([^\n]*)", re.M)

#: So sanh hai ve. Chan `==` va `!=` (khong phai phep cua ngu phap) va chan `=>`.
_SS = re.compile(rf"({_VE})[ \t]*(>=|<=|>|<)[ \t]*({_VE})")

#: `crossover(a, b)` / `crossunder(a, b)` cua Pine, va ban `ta.` cua v5.
_CHEO = re.compile(rf"(?:ta\.)?(crossover|crossunder)[ \t]*\(([^,]+),([^)]+)\)")


#: Khai bao input CUA TAC GIA. Pine: `n = input(34, minval=2, maxval=200)`.
#: MQL5: `input int InpPeriod = 14; // mo ta`.
_INPUT_PINE = re.compile(
    rf"^[ \t]*({_TEN})[ \t]*=[ \t]*"
    rf"input(?:\.[a-z]+)?[ \t]*\(([^)\n]*)\)", re.M)
_INPUT_MQL = re.compile(
    rf"^[ \t]*(?:extern|input)[ \t]+[A-Za-z_]\w*[ \t]+({_TEN})"
    rf"[ \t]*=[ \t]*({_SO})[ \t]*;", re.M)
_MINMAX = re.compile(rf"(minval|maxval|step)[ \t]*=[ \t]*({_SO})")


def _chuan_hoa(vb: str) -> str:
    """Chuan hoa xuong dong ve LF va bo chu thich duoi dong.

    Vi sao can, va no la mot LOP loi chu khong phai mot cho: file Pine tai ve
    dung CRLF, nen moi bieu thuc chinh quy ket bang [ tab]*$ deu truot -
    `price = close<CR>` khong khop `(open|high|low|close)[ tab]*$`. Ca mot
    chien luoc Bollinger + RSI rot chi vi mot ky tu CR, va trieu chung nhin tu
    ngoai chi la "khong dich duoc crossover(source, BBlower)".

    Chu thich duoi dong cung phai bo truoc khi phan tich so hoc:
    `BBmult = 2 // input(2.0, ...)` co dau `//` ma bo tach hang tu se doc nham
    thanh phep chia.
    """
    vb = (vb or '').replace(chr(13) + chr(10), chr(10)).replace(chr(13), chr(10))
    return re.sub(r'[ \t]*//[^\n]*', '', vb)


def rut_input(vb: str) -> dict:
    """Ten bien -> {gia_tri, min, max} theo dung khai bao cua TAC GIA.

    Vi sao dang gia: chinh nguoi viet bot da noi bien nay chay trong khoang nao.
    Do la mot mien quet CO NGUON GOC, khac han mot luoi ta tu bia ra - va lay no
    khong phai chay mot dong ma nao cua ho.
    """
    vb = _chuan_hoa(vb)

    ra: dict[str, dict] = {}
    for m in _INPUT_PINE.finditer(vb):
        doi = m.group(2)
        so = re.search(rf"(?:defval[ \t]*=[ \t]*)?({_SO})", doi)
        if not so:
            continue
        d = {"gia_tri": float(so.group(1))}
        for mm in _MINMAX.finditer(doi):
            d[{"minval": "min", "maxval": "max",
               "step": "buoc"}[mm.group(1)]] = float(mm.group(2))
        ra[m.group(1)] = d
    for m in _INPUT_MQL.finditer(vb):
        ra.setdefault(m.group(1), {"gia_tri": float(m.group(2))})
    return ra


def _luoi_quanh(n: float, khai: dict | None) -> list[int]:
    """Ba diem quanh gia tri tac gia dung, chan trong mien tac gia khai.

    Ba chu khong nhieu hon: moi diem them la mot suat FDR. Muc dich khong phai
    do tim gia tri tot nhat - do la viec cua tang kham pha - ma la biet hinh
    dang quanh diem tac gia chon (cao nguyen hay cai gai).
    """
    khai = khai or {}
    lo = khai.get("min", 2.0)
    hi = khai.get("max", 1e9)
    ra = []
    for x in (n / 2.0, n, n * 2.0):
        v = int(round(max(lo, min(hi, x))))
        if v >= 2 and v not in ra:
            ra.append(v)
    return sorted(ra)


def _tach_tam_nguyen(bt: str) -> list[tuple[str, str]]:
    """`a ? b : c ? d : e` -> [(a,b), (c,d), ("", e)]. Tach o MUC NGOAI CUNG."""
    ra, con = [], bt.strip()
    while True:
        muc, vt = 0, -1
        for i, c in enumerate(con):
            if c in "([":
                muc += 1
            elif c in ")]":
                muc -= 1
            elif c == "?" and muc == 0:
                vt = i
                break
        if vt < 0:
            ra.append(("", con.strip()))
            return ra
        dk = con[:vt]
        # tim dau `:` NGANG CAP voi dau `?` nay
        muc, vt2 = 0, -1
        for i in range(vt + 1, len(con)):
            c = con[i]
            if c in "([":
                muc += 1
            elif c in ")]":
                muc -= 1
            elif c == ":" and muc == 0:
                vt2 = i
                break
        if vt2 < 0:
            ra.append((dk.strip(), con[vt + 1:].strip()))
            return ra
        ra.append((dk.strip(), con[vt + 1:vt2].strip()))
        con = con[vt2 + 1:]


def _bo_tu_tham_chieu(dk: str, ten: str) -> str:
    """Bo cac ve `ten[1] > 0` khoi dieu kien - chung la GUARD TRANG THAI.

    `crossunder(fast, slow) and direction[1] > 0 ? -1` nghia la "lat xuong khi co
    crossunder, va luc do dang len". `trang_thai_lat` da GIU trang thai san nen
    ve `direction[1] > 0` la thua; giu no lai thi khong dich duoc (mot toan hang
    tu tham chieu) va ca bien mat.
    """
    giu = [v for v in _tach_va(dk)
           if not re.search(rf"\b{re.escape(ten)}\s*\[", v)]
    return " and ".join(giu)


def _trang_thai_tu_tam_nguyen(ten: str, bt: str, vi_tri: int, bang: list,
                              bang_bt: list) -> dict | None:
    """Bien TU THAM CHIEU viet bang tam nguyen long -> toan hang `trang_thai_lat`.

    Dang that trong ma (do 01/09 tren kho Pine, 12 bien co dang nay):

        direction = na(direction[1]) ? 1
                  : crossunder(fast, slow) and direction[1] > 0 ? -1
                  : crossover(fast, slow) and direction[1] < 0 ? 1
                  : direction[1]

    Day chinh la `trang_thai_lat`: nhanh cho ra +1 la dieu kien LEN, nhanh cho ra
    -1 la dieu kien XUONG, nhanh `x[1]` la "giu nguyen". Bo doc chi can nhan ra
    hinh dang do - toan tu da co tu truoc.
    """
    if not re.search(rf"\b{re.escape(ten)}\s*\[", bt):
        return None                       # khong tu tham chieu -> khong co nho
    len_dk, xuong_dk = None, None
    for dk, gt in _tach_tam_nguyen(bt):
        g = gt.strip()
        if not dk or f"{ten}[" in g:
            continue                      # nhanh mac dinh / giu nguyen
        if re.search(rf"\bna\s*\(\s*{re.escape(ten)}\s*\[", dk):
            continue                      # nhanh khoi tao
        sach = _bo_tu_tham_chieu(dk, ten)
        if not sach:
            continue
        if re.fullmatch(r"[+]?1(?:\.0+)?", g) and len_dk is None:
            len_dk = sach
        elif re.fullmatch(r"-1(?:\.0+)?", g) and xuong_dk is None:
            xuong_dk = sach
    if not len_dk or not xuong_dk:
        return None
    a, ha = _no_dieu_kien(len_dk, vi_tri, bang, bang_bt)
    b, hb = _no_dieu_kien(xuong_dk, vi_tri, bang, bang_bt)
    if ha or hb or len(a) != 1 or len(b) != 1:
        return None                       # dich duoc CA HAI thi moi nhan
    return {"chi_bao": "trang_thai_lat", "len": a[0], "xuong": b[0]}


def _chon_nhanh_cau_hinh(bt: str, vi_tri: int, bang_bt: list) -> str | None:
    """`x = co_bat ? A : B` voi `co_bat = input(true)` -> tra ve `A`.

    Day KHONG phai tin hieu ma la mot cong tac cau hinh cua tac gia: 59/71 bieu
    thuc tam nguyen trong kho Pine thuoc dang nay (`use_longer_average`,
    `no_repainting`, `show_highlight`). Giu nguyen ca bieu thuc thi khong dich
    duoc; chon dung nhanh ung voi gia tri MAC DINH cua ho thi doc tiep duoc, va
    do dung la cau hinh ho phat hanh.
    """
    nhanh = _tach_tam_nguyen(bt)
    if len(nhanh) != 2 or not nhanh[0][0]:
        return None
    dk = nhanh[0][0].strip()
    if not re.fullmatch(_TEN, dk):
        return None
    gt = None
    for pos, ten, bt2 in bang_bt:
        if pos >= vi_tri:
            break
        if ten == dk:
            gt = bt2
    if gt is None:
        return None
    m = re.match(r"input(?:\.bool)?\s*\(\s*(true|false)\b", gt.strip(), re.I)
    if not m:
        return None
    return nhanh[0][1] if m.group(1).lower() == "true" else nhanh[1][1]


#: `CopyRates(sym,tf,bat_dau,so_bar,mang)` va ho hang cua no. Nhom 4 la so bar
#: duoc chep, nhom 5 la ten mang nhan.
_CHEP = re.compile(
    rf"\b(CopyRates|CopyHigh|CopyLow|CopyClose|CopyOpen|CopyBuffer)[ \t]*\("
    rf"([^;]*?)\)")
_AS_SERIES = re.compile(rf"\bArraySetAsSeries[ \t]*\([ \t]*({_TEN})[ \t]*,"
                        rf"[ \t]*true[ \t]*\)", re.I)
_COT_CHEP = {"CopyHigh": "high", "CopyLow": "low",
             "CopyClose": "close", "CopyOpen": "open"}


def _bang_mang(vb: str, bang_so: list) -> list[tuple[int, str, dict]]:
    """Mang do `Copy*` do day -> mo ta du de doc `mang[k]` ve mot toan hang.

    HAI THU PHAI CO CUNG LUC, thieu mot la sai:

      1. **Mang nhan gi.** `CopyBuffer(MaHandle,...,MaValues)` lam `MaValues`
         thanh chinh chi bao cua `MaHandle`; `CopyRates(...,current)` lam
         `current[k].close` thanh gia dong cua. Day la cach MQL5 doc chi bao -
         khong dich duoc thi mot EA MQL5 dien hinh khong ra duoc gi.
      2. **CHIEU CUA CHI SO.** Mac dinh mang MQL5 KHONG phai chuoi thoi gian:
         `mang[0]` la bar CU NHAT trong doan vua chep, khong phai bar hien tai.
         Chi khi co `ArraySetAsSeries(mang,true)` thi `[0]` moi la bar moi nhat.
         Doc nham chieu la doi han do tre - dung cai bay `Open[i+1]` cua du an,
         va no IM LANG: bang so van ra, chi la ra cua mot co che khac.

    Nen: khong biet chieu VA khong biet so bar thi tra `_so_bar=None` va
    `_toan_hang` TU CHOI, thay vi doan mot do tre.
    """
    chuoi = {m.group(1) for m in _AS_SERIES.finditer(vb)}
    ra = []
    for m in _CHEP.finditer(vb):
        ds = [x.strip() for x in m.group(2).split(",")]
        if len(ds) < 5:
            continue
        ten = re.sub(r"\[\s*\]$", "", ds[4]).strip()
        if not re.fullmatch(_TEN, ten):
            continue
        n = _giai_so(ds[3], m.start(), bang_so)
        d = {"_mang": True, "_chuoi": ten in chuoi,
             "_so_bar": int(n) if n is not None and n > 0 else None}
        ham = m.group(1)
        if ham == "CopyBuffer":
            d["_goc"] = ds[0]                  # ten handle, giai sau
        elif ham == "CopyRates":
            d["_truong"] = True                # phai viet `mang[k].close`
        else:
            d["cot"] = _COT_CHEP[ham]
        ra.append((m.start(), ten, d))
    return ra


def _giai_so(x: str, vi_tri: int, bang_so: list) -> float | None:
    """So tho, hoac lan gan GAN NHAT TRUOC `vi_tri` cua mot bien so."""
    x = x.strip()
    if re.fullmatch(_SO, x):
        return float(x)
    gt = None
    for pos, ten, v in bang_so:
        if pos >= vi_tri:
            break
        if ten == x:
            gt = v
    return gt


def _bang_ky_hieu(vb: str) -> list[tuple[int, str, dict]]:
    """(vi tri, ten bien, toan hang) cho moi bien duoc gan bang mot chi bao.

    Theo VI TRI chu khong phai tu dien phang, cung ly do nhu `_bang_bien` cua
    `thu_hoi_thanh_phan`: mot file tai ve thuong ghep nhieu script, va cung mot
    ten bien mang y nghia khac nhau o moi ban.
    """
    bang_so = TP._bang_bien(vb)
    ra = []
    for m in _GAN_CB.finditer(vb):
        ten, biu = m.group(1), m.group(2)
        # Rut dung mot loi goi chi bao tu ve phai, dung chinh bo rut da co.
        con = TP.rut_pine(biu[:400]) or TP.rut_mql(biu[:400])
        if not con:
            continue
        t = con[0]
        if not t.get("tham_so"):
            # Chu ky co the la bien khai o cho khac trong file.
            ds = TP._tach_doi_so(TP._khoi_ngoac(biu, biu.index("(")))
            t = dict(t, tham_so=TP._so_dau(ds, 1, m.start(), bang_so))
        ra.append((m.start(), ten, t))
    # HAI DANG BIEN RAT PHO BIEN ma ban dau bo doc bo qua - va bo qua chung thi
    # moi dieu kien dang `crossover(vrsi, RSIoverSold)` deu rot:
    #   1. BIEN SO   : `RSIoverSold = input(30)`  -> mot hang so
    #   2. BI DANH GIA: `source = close`          -> chinh cot gia do
    da = {t[1] for t in ra}
    for pos, ten, v in bang_so:
        if ten not in da:
            ra.append((pos, ten, {"hang": float(v), "_thang": 1}))
    for m in re.finditer(rf"^[ 	]*({_TEN})[ 	]*=[ 	]*(open|high|low|close)[ 	]*$",
                         vb, re.M):
        if m.group(1) not in da:
            ra.append((m.start(), m.group(1),
                       {"chi_bao": "gia", "cot": m.group(2), "_thang": 1}))
    # MANG do `Copy*` do day. Dang ky o vi tri LOI GOI chu khong o cho khai bao
    # mang: `_toan_hang_goc` lay lan gan gan nhat TRUOC cho dung, va mang chi
    # co noi dung sau khi `Copy*` chay.
    for pos, ten, d in _bang_mang(vb, bang_so):
        if "_goc" in d:
            # `CopyBuffer(MaHandle,...)` -> tra ve dung chi bao cua handle do.
            goc = None
            for p2, t2, v2 in ra:
                if p2 < pos and t2 == d["_goc"]:
                    goc = v2
            if goc is None:
                continue                       # khong biet handle la chi bao gi
            d = dict(d, _goc=goc)
        ra.append((pos, ten, d))
    ra.sort(key=lambda x: x[0])
    return ra


def _tach_cong_tru(bt: str) -> list[tuple[float, str]]:
    """Tach mot bieu thuc theo `+`/`-` o MUC NGOAI CUNG. Tra (dau, hang tu).

    Bo qua dau o vi tri MO DAU (do la dau am cua so hang dau) va dau ngay sau
    mot toan tu khac (`a * -2`), de khong cat nham thanh hai hang tu.
    """
    ra, sau, muc, dau = [], 0, 0, 1.0
    for i, c in enumerate(bt):
        if c in "([":
            muc += 1
        elif c in ")]":
            muc -= 1
        elif muc == 0 and c in "+-" and i > 0:
            truoc = bt[:i].rstrip()
            if truoc and truoc[-1] not in "+-*/(,<>=":
                ra.append((dau, bt[sau:i]))
                dau = 1.0 if c == "+" else -1.0
                sau = i + 1
    ra.append((dau, bt[sau:]))
    return [(d, t.strip()) for d, t in ra if t.strip()]


def _hang_tu(bt: str, vi_tri: int, bang: list, bang_bt: list,
             sau: int) -> tuple[float, dict] | None:
    """Mot hang tu -> (he so, toan hang). Chi chap nhan dang TUYEN TINH.

    `2 * dev`, `dev * 2`, `dev / 2`, `dev` deu duoc; `a * b` voi ca hai la chuoi
    gia tri thi KHONG - do la phep nhan hai chuoi, khong con tuyen tinh va khong
    dien dat duoc bang `tuyen_tinh`.

    He so co the la mot BIEN (`mult = input(2.0)`), khong chi mot so tho. Bang
    ky hieu da chua san bien so duoi dang `{"hang": v}` nen chi can hoi no.
    """
    he_so, toan = 1.0, None
    phan = re.split(r"([*/])", bt)
    dau_chia = False
    for k, p in enumerate(phan):
        p = p.strip()
        if p in ("*", "/"):
            dau_chia = (p == "/")
            continue
        p = _boc_ngoac(p)
        if not p:
            continue
        t = _toan_hang(p, vi_tri, bang, bang_bt, sau + 1)
        if t is None and re.match(rf"^(?:ta[.])?{_TEN}[ 	]*[(]", p):
            # LOI GOI VIET THANG trong bieu thuc: `mult * stdev(source, length)`.
            # Khong xu ly thi moi ban Bollinger deu rot, vi `dev` luon duoc viet
            # dang nay chu khong gan qua mot bien chi bao rieng.
            con = TP.rut_pine(p) or TP.rut_mql(p)
            if con:
                c0 = con[0]
                if not c0.get("tham_so"):
                    # Chu ky la mot BIEN (`stdev(source, length)` voi
                    # `length = input(20)`). Bo rut chi nhin trong dung chuoi loi
                    # goi nen khong thay; giai bang BANG KY HIEU - noi da co san
                    # bien so duoi dang {"hang": v}.
                    ds2 = TP._tach_doi_so(TP._khoi_ngoac(p, p.index("(")))
                    for a in ds2:
                        ta = _toan_hang(a.strip(), vi_tri, bang, bang_bt, sau + 1)
                        if ta and "hang" in ta and float(ta["hang"]) >= 1:
                            c0 = dict(c0, tham_so=[float(ta["hang"])])
                            break
                t = _tu_thanh_phan(c0)
        if t is None:
            return None
        if "hang" in t:                       # la mot HE SO, khong phai chuoi
            v = float(t["hang"])
            if dau_chia and v == 0:
                return None
            he_so = he_so / v if dau_chia else he_so * v
            continue
        if toan is not None:
            return None                       # nhan hai chuoi -> khong tuyen tinh
        toan = t
    if toan is None:
        return None
    return he_so, toan


def _tuyen_tinh(bt: str, vi_tri: int, bang: list, bang_bt: list,
                sau: int) -> dict | None:
    """Bieu thuc so hoc -> toan hang `tuyen_tinh` cua ngu phap.

    Vi sao can: chien luoc Pine that gan nhu luon so gia voi mot MUC DUOC TINH
    RA - `BBlower = basis - mult * dev`, kenh Keltner, pivot. Khong dich duoc
    dang nay thi 17/18 chien luoc trong kho deu rot o buoc dich, va do dung la
    cho bo doc dung lai truoc khi co ham nay.
    """
    hang = _tach_cong_tru(bt)
    # Mot hang tu VAN hop le neu no co he so (`mult * stdev(...)`) - do la dang
    # `dev` cua moi ban Bollinger. Chi bo khi ca bieu thuc la mot dinh danh tran,
    # vi luc do duong khac da lo roi va vao day se de quy vo tan.
    if len(hang) == 1 and re.fullmatch(_TEN, bt.strip()):
        return None
    ds, hs, cong = [], [], 0.0
    for dau, ht in hang:
        p = _boc_ngoac(ht)
        if re.fullmatch(_SO, p):
            cong += dau * float(p)
            continue
        r = _hang_tu(p, vi_tri, bang, bang_bt, sau)
        if r is None:
            return None                 # mot hang tu khong dich duoc -> bo CA
        h, t = r
        ds.append(t)
        hs.append(dau * h)
    if not ds:
        return None
    d = {"chi_bao": "tuyen_tinh", "toan_hang": ds, "he_so": hs}
    if cong:
        d["cong_them"] = cong
    return d


#: `mang[k]` hoac `mang[k].truong` - hai dang doc mot mang MQL5.
_O_MANG = re.compile(rf"^({_TEN})\[(\d+)\](?:\.({_TEN}))?$")


def _tu_mang(tu: str, vi_tri: int, bang: list) -> dict | None:
    """`MaValues[0]` / `current[1].close` -> toan hang. `{}` = co nhan, phai bo.

    Tra ba thu khac nhau, va phan biet chung la quan trong:
      `None` - khong phai o cua mot mang da biet, de duong khac doc tiep.
      `{}`   - DUNG la mang do `Copy*` do, nhung khong suy duoc do tre (khong
               `ArraySetAsSeries` va so bar khong phai hang so). Tu choi han
               chu khong doan: doan sai chieu la doi co che ma khong bao loi.
      dict   - toan hang that.
    """
    m = _O_MANG.match(tu.strip())
    if not m:
        return None
    ten, k, truong = m.group(1), int(m.group(2)), m.group(3)
    d = None
    for pos, t, v in bang:
        if pos >= vi_tri:
            break
        if t == ten and v.get("_mang"):
            d = v
    if d is None:
        return None
    # CHIEU CUA CHI SO - xem `_bang_mang`.
    if d["_chuoi"]:
        tre = k
    elif d["_so_bar"] is not None:
        tre = d["_so_bar"] - 1 - k             # [0] la bar CU NHAT cua doan chep
    else:
        return {}
    if tre < 0:
        return {}
    if d.get("_truong"):                       # MqlRates: bat buoc co truong
        if truong is None or truong.lower() not in _TRUONG_GIA:
            return {}
        goc = {"chi_bao": "gia", "cot": _TRUONG_GIA[truong.lower()]}
    elif truong is not None:
        return {}                              # mang so ma lai doc truong
    elif "cot" in d:
        goc = {"chi_bao": "gia", "cot": d["cot"]}
    else:
        goc = _tu_thanh_phan(d["_goc"])
        if goc is None:
            return {}
    return goc if tre == 0 else {"chi_bao": "tre", "cua": goc, "n": tre}


def _toan_hang(tu: str, vi_tri: int, bang: list,
               bang_bt: list | None = None, sau: int = 0) -> dict | None:
    """Mot ve cua phep so sanh -> toan hang ngu phap, hoac None neu khong dich duoc."""
    tu = (tu or "").strip()
    # `x[k]` la NHIN LUI k bar. Ban dau ham nay CAT BO hau to do, va do la mot
    # loi lam hong nghia: `close > highest(high,34)` (khong co do tre) khong bao
    # gio dung, vi `highest` gom ca nen hien tai - cong bao "kich hoat 0,000%".
    # Ma pha vo that luon viet `highest(high,34)[1]`. Cung ho loi voi quy tac
    # `Open[i+1]` cua du an: mat do tre la doi hoan toan y nghia.
    # MANG MQL5 (`MaValues[0]`, `current[0].close`) - phai xet TRUOC hau to
    # `[k]` chung, vi chieu chi so cua mang MQL5 phu thuoc ArraySetAsSeries chu
    # khong mac nhien la nhin lui k bar.
    t_mang = _tu_mang(tu, vi_tri, bang)
    if t_mang is not None:
        return t_mang if t_mang != {} else None

    tre = 0
    m_tre = re.search(r"\[(\d+)\]$", tu)
    if m_tre:
        tre = int(m_tre.group(1))
        tu = tu[:m_tre.start()]
    if not tu:
        return None
    goc = _toan_hang_goc(tu, vi_tri, bang, bang_bt, sau)
    if goc is None or tre <= 0:
        return goc
    if "hang" in goc:
        return goc                             # hang so tre van la chinh no
    return {"chi_bao": "tre", "cua": goc, "n": tre}


def _toan_hang_goc(tu: str, vi_tri: int, bang: list,
                   bang_bt: list | None = None, sau: int = 0) -> dict | None:
    if re.fullmatch(_SO, tu):
        return {"hang": float(tu)}
    k = tu.lower()
    if k in _GIA:
        return {"chi_bao": "gia", "cot": _GIA[k]}
    # ham chi bao MQL5 viet thang trong dieu kien
    hm = _tu_ham_mql5(tu)
    if hm is not None:
        return hm
    # bien tro toi mot chi bao: lay lan gan GAN NHAT TRUOC vi tri dung
    gt = None
    for pos, ten, t in bang:
        if pos >= vi_tri:
            break
        if ten == tu:
            gt = t
    if gt is None:
        # Bien co the duoc gan bang mot BIEU THUC SO HOC (`BBlower = basis -
        # mult * dev`). Truoc khi bo cuoc, thu no bieu thuc do ra toan hang
        # `tuyen_tinh`. Gioi han do sau de mot file co vong tham chieu khong
        # lam treo bo doc.
        if bang_bt and sau < 5:
            dn = None
            for pos, ten, bt2 in bang_bt:
                if pos >= vi_tri:
                    break
                if ten == tu:
                    dn = (pos, bt2)
            if dn is not None:
                # THU TU QUAN TRONG: trang thai co nho truoc, vi mot bieu thuc
                # tam nguyen tu tham chieu cung "trong nhu" mot to hop tuyen
                # tinh neu chi nhin dau `+`/`-`.
                t = _trang_thai_tu_tam_nguyen(tu, dn[1], dn[0], bang, bang_bt)
                if t is not None:
                    return t
                # CONG TAC CAU HINH: `x = co_bat ? A : B` voi `co_bat =
                # input(true)`. Do la mot lua chon cua tac gia, khong phai tin
                # hieu - chon dung nhanh ho de mac dinh roi doc tiep.
                nhanh = _chon_nhanh_cau_hinh(dn[1], dn[0], bang_bt)
                if nhanh is not None and nhanh != dn[1]:
                    t = _toan_hang(nhanh, dn[0], bang, bang_bt, sau + 1)
                    if t is not None:
                        return t
                t = _tuyen_tinh(dn[1], dn[0], bang, bang_bt, sau + 1)
                if t is not None:
                    return t
        return None
    return _tu_thanh_phan(gt)


def _tu_thanh_phan(gt: dict) -> dict | None:
    """Mot thanh phan cua `thu_hoi_thanh_phan` -> toan hang ngu phap."""
    if "hang" in gt or gt.get("_thang"):
        return {k: v for k, v in gt.items() if not k.startswith("_")}
    ok, _ = TP.dien_dat_duoc(gt)
    if not ok:
        return None
    d = {"chi_bao": gt["chi_bao"]}
    if gt.get("tham_so"):
        d["n"] = int(gt["tham_so"][0])
    elif gt["chi_bao"] not in ("ibs", "bien_do", "than_nen", "khoi_luong"):
        return None                            # thieu chu ky -> khong dung duoc
    if gt.get("cot") and gt["chi_bao"] in ("ema", "sma", "gia"):
        d["cot"] = gt["cot"]
    if gt["chi_bao"] in _CAN_CUA:
        # `cao_nhat`/`thap_nhat`/`tb`/... la toan tu CUA SO: chung tinh tren mot
        # toan hang khac chu khong tu co chuoi gia tri. Thieu `cua` thi ngu phap
        # nem `KeyError: chi bao 'cao_nhat' khong biet, va khong co truong 'cua'`
        # - da sap that khi doc Donchian cua Sonic R.
        d["cua"] = {"chi_bao": "gia",
                    "cot": gt.get("cot") or _CUA_MAC_DINH.get(gt["chi_bao"], "close")}
    return d


def _ho_cua(dk: dict) -> str:
    """Ho cua mot dieu kien, NHIN XUYEN qua cac toan tu boc ngoai.

    `tre` (va cac toan tu cua so khac) chi la lop boc: ho thuc su nam o toan
    hang ben trong. Khong boc thi `close > cao_nhat(55) tre 1` - dieu kien pha
    vo dien hinh - bi xep ho `khac` roi bi loai, tuc bo doc vut dung cai no vua
    cong suc giu lai do tre cho.
    """
    for ben in ("trai", "phai"):
        for cb in _cac_chi_bao(dk.get(ben) or {}):
            if cb in _HO:
                return _HO[cb]
    return "khac"


def _cac_chi_bao(t: dict, sau: int = 0) -> list[str]:
    """Moi ten chi bao xuat hien trong mot toan hang, ke ca long ben trong.

    Phai nhin XUYEN QUA `tuyen_tinh` va `cua`: mot dai Bollinger duoc viet
    `tuyen_tinh([tb, do_lech])`, va neu chi doc `chi_bao` o lop ngoai thi ho ra
    `khac` - ma `khac` khong khai duoc pham vi nen khong vao duoc thu vien. Tuc
    dung cai co che ta vua cong suc dich ra lai bi bo o cua cuoi.
    """
    if not isinstance(t, dict) or sau > 6:
        return []
    ra = []
    cb = t.get("chi_bao")
    if cb and cb not in ("tuyen_tinh", "tre", "tuyet_doi"):
        ra.append(cb)
    for x in (t.get("toan_hang") or []):
        ra += _cac_chi_bao(x, sau + 1)
    if isinstance(t.get("cua"), dict):
        ra += _cac_chi_bao(t["cua"], sau + 1)
    # Toan tu CO NHO giu chi bao trong hai DIEU KIEN con (`len`/`xuong`/`khi`),
    # khong phai trong `toan_hang` hay `cua`. Khong nhin vao day thi mot co che
    # supertrend ra ho `khac` - ma `khac` khong khai duoc pham vi nen bi bo o cua
    # cuoi. Cung ho loi da sap voi `tuyen_tinh`: dich ra duoc roi lai vut di.
    for khoa in ("len", "xuong", "khi"):
        d = t.get(khoa)
        if isinstance(d, dict):
            for ben in ("trai", "phai"):
                if isinstance(d.get(ben), dict):
                    ra += _cac_chi_bao(d[ben], sau + 1)
    return ra


def _ten_toan_hang(t: dict) -> str:
    if t.get("chi_bao") == "tre":
        return _ten_toan_hang(t.get("cua") or {}) + f"_tre{int(t.get('n', 1))}"
    if "hang" in t:
        s = f"{t['hang']:g}".replace("-", "am").replace(".", "_")
        return s
    cb = t.get("chi_bao", "x")
    if cb == "gia":
        return t.get("cot", "close")
    p = cb + (str(int(t["n"])) if t.get("n") else "")
    return p + (("_" + t["cot"]) if t.get("cot") else "")


_TEN_PHEP = {">": "tren", ">=": "tren", "<": "duoi", "<=": "duoi",
             "cheo_len": "cheo_len", "cheo_xuong": "cheo_xuong"}


def _hop_thang_do(trai: dict, phai: dict) -> bool:
    """Hai ve co cung thang do khong.

    Hai hang so: vo nghia. Mot hang so doi voi mot chi bao o THANG DO GIA: cung
    vo nghia, va day la nguon rac chinh - `input(1.5)` cua mot he so nhan bi doc
    thanh nguong gia. Chi bao co thang do bi chan (rsi 0-100, gio 0-23...) thi
    so voi hang so la dung.
    """
    ch = [t for t in (trai, phai) if "hang" in t]
    if len(ch) == 2:
        return False
    if not ch:
        return True
    kia = phai if "hang" in trai else trai
    while kia.get("chi_bao") == "tre":
        kia = kia.get("cua") or {}
    return kia.get("chi_bao") not in _THANG_GIA


def _dieu_kien(vb: str, bang: list) -> list[dict]:
    """Moi so sanh dich duoc = MOT dieu kien vao. Gop trung."""
    ra, da = [], set()
    for m in _SS.finditer(vb):
        trai = _toan_hang(m.group(1), m.start(), bang)
        phai = _toan_hang(m.group(3), m.start(), bang)
        if not trai or not phai:
            continue
        if not _hop_thang_do(trai, phai):
            continue
        d = {"trai": trai, "phep": _PHEP[m.group(2)], "phai": phai}
        khoa = repr(sorted(d.items(), key=str))
        if khoa in da:
            continue
        da.add(khoa)
        ra.append(dict(d, _trich=m.group(0)[:80]))
    for m in _CHEO.finditer(vb):
        trai = _toan_hang(m.group(2), m.start(), bang)
        phai = _toan_hang(m.group(3), m.start(), bang)
        if not trai or not phai:
            continue
        phep = "cheo_len" if m.group(1) == "crossover" else "cheo_xuong"
        d = {"trai": trai, "phep": phep, "phai": phai}
        khoa = repr(sorted(d.items(), key=str))
        if khoa in da:
            continue
        da.add(khoa)
        ra.append(dict(d, _trich=m.group(0)[:80]))
    return ra


def _luoi_tu_dieu_kien(dk: dict, khai: dict) -> dict:
    """Chu ky trong dieu kien -> luoi quet, chan theo minval/maxval cua tac gia."""
    ra = {}
    for ben in ("trai", "phai"):
        t = dk.get(ben) or {}
        while isinstance(t, dict) and t.get("chi_bao") in ("tre", "tuyet_doi"):
            t = t.get("cua") or {}
        n = (t or {}).get("n")
        if not n:
            continue
        # Khai bao nao co gia tri dung bang `n` thi mien cua no ap cho `n`.
        k = next((v for v in khai.values() if v.get("gia_tri") == float(n)), None)
        # Khoa theo VE, khong theo ten chi bao: mot dieu kien nhu
        # `ema34_low < ema89_close` co hai ve CUNG la `ema`, va khoa theo ten thi
        # chu ky 34 bi 89 ghi de - mat dung mot nua dieu kien.
        ra[f"{ben}_{t.get('chi_bao')}"] = _luoi_quanh(float(n), k)
    return ra


#: `strategy.entry(..., strategy.long)` / `... , true)` / `..., when = <dk>`.
_VAO_LENH = re.compile(
    r"strategy\.(?P<pine>entry|order)[ \t]*\((?P<doi_p>[^\n]*)"
    r"|(?P<obj>\w+)\.(?P<mql>Buy|Sell)[ \t]*\((?P<doi_m>[^\n]*)"
    r"|(?P<ham>OrderSend|PositionOpen)[ \t]*\((?P<doi_o>[^\n]*)", re.M)
#: Guard chi noi DANG DI NHANH NAO, khong noi vi sao vao lenh. Do 05/09:
#: `type == ORDER_TYPE_BUY` (7 file) · `type==POSITION_TYPE_BUY` (6) ·
#: `orderType == ORDER_TYPE_BUY` (4) · `direction>0` (3) · `isBuy` (3).
_LA_PHAN_NHANH = re.compile(
    r"ORDER_TYPE_(BUY|SELL)|POSITION_TYPE_(BUY|SELL)|\bis[_]?Buy\b|\bis[_]?Sell\b"
    r"|\bdirection\s*[<>=]|\bdir\s*[<>=]|\btype\s*==|\bcmd\s*==",
    re.I)

#: Khai bao ham kieu C: `void Ten(...)` / `bool Ten(...)` / `void Ten(...) {`.
_KHAI_HAM = re.compile(
    r"^[ \t]*(?:static[ \t]+)?(?:void|bool|int|double|long|string|datetime)"
    r"[ \t]+(\w+)[ \t]*\(", re.M)


def _ham_bao(vb: str, vi_tri: int) -> str | None:
    """Ten ham chua vi tri `vi_tri`. Lay khai bao ham GAN NHAT phia tren."""
    ten = None
    for m in _KHAI_HAM.finditer(vb):
        if m.start() > vi_tri:
            break
        ten = m.group(1)
    return ten


def _cho_goi(vb: str, ten_ham: str, tru_vi_tri: int) -> list[int]:
    """Vi tri cac cho GOI `ten_ham(` - tru chinh cho khai bao."""
    ra = []
    for m in re.finditer(r"\b" + re.escape(ten_ham) + r"[ \t]*\(", vb):
        if abs(m.start() - tru_vi_tri) < 4:
            continue
        dong = vb[max(0, m.start() - 200):m.start()]
        if re.search(r"(?:void|bool|int|double|long|string|datetime)[ \t]+$", dong):
            continue                      # do la khai bao, khong phai loi goi
        ra.append(m.start())
    return ra


#: `if` la KIEM LOI cua chinh lenh vao, khong phai dieu kien vao.
_LA_KIEM_LOI = re.compile(
    r"OrderSend|PositionOpen|\.(Buy|Sell)[ \t]*\(|GetLastError|ResultRetcode"
    r"|IsStopped|!\s*\w+\.(Buy|Sell)")

#: Gan mot bien BOOL: `ten = <bieu thuc co so sanh hoac ket noi>`.
_GAN_BOOL = re.compile(
    rf"^[ \t]*(?:{_KIEU_C})?({_TEN})[ \t]*=[ \t]*([^\n]+)$", re.M)

#: Khai bao NHIEU bien tren mot dong: `double price=0, sl=0, tp=0;`. Phai cat o
#: dau phay MUC NGOAI CUNG, khong thi `price` mang bieu thuc `0, sl=0, tp=0`.
_KHAI_TIEP = re.compile(rf",[ \t]*({_TEN})[ \t]*=[ \t]*")


def _cat_khai_bao(bt: str) -> list[tuple[str, str]]:
    """`0, sl=0, tp=price+5;` -> [("", "0"), ("sl","0"), ("tp","price+5")].

    Tra ve hang tu DAU voi ten rong (no thuoc bien da bat o ngoai), roi tung
    khai bao tiep theo. Cat o MUC NGOAI CUNG: `MathMax(a, b)` co dau phay ben
    trong ngoac va cat o do la lam hong bieu thuc.
    """
    bt = bt.strip().rstrip(";").strip()
    ra, sau, ten, muc = [], 0, "", 0
    i = 0
    while i < len(bt):
        c = bt[i]
        if c in "([":
            muc += 1
        elif c in ")]":
            muc -= 1
        elif c == "," and muc == 0:
            m = _KHAI_TIEP.match(bt, i)
            if m:
                ra.append((ten, bt[sau:i].strip()))
                ten, sau = m.group(1), m.end()
                i = m.end()
                continue
        i += 1
    ra.append((ten, bt[sau:].strip()))
    return [(t, b) for t, b in ra if b]


def _bang_bool(vb: str) -> list[tuple[int, str, str]]:
    """(vi tri, ten, bieu thuc) cho moi bien duoc gan mot bieu thuc.

    Hai khau de mat ma deu do MQL5 viet kieu C:

      1. **Dau `;` cuoi dong.** `_no_dieu_kien` doi phep so sanh `fullmatch` ca
         ve; con mot dau `;` thi `a > b;` khong bao gio khop, va ca co che roi
         vao `chua_dien_dat_duoc` voi ly do nhin nhu mot bieu thuc hop le.
      2. **Nhieu bien mot dong.** `double price=0, sl=0, tp=0;` - khong cat thi
         `price` mang bieu thuc `0, sl=0, tp=0` con `sl`/`tp` bien mat.
    """
    ra = []
    for m in _GAN_BOOL.finditer(vb):
        for k, (ten, bt) in enumerate(_cat_khai_bao(m.group(2))):
            ra.append((m.start(), ten or m.group(1), bt))
    return ra


def _tach_va(bt: str) -> list[str]:
    """Tach mot bieu thuc theo `and` HOAC `&&` o MUC NGOAI CUNG.

    `&&` phai ngang hang voi `and`: MQL5 va Pine v6 deu viet kieu C. Chi biet
    `and` thi `upbreakout && current[0].close < MaValues[0]` di nguyen khoi vao
    `_SS`, khong fullmatch duoc phep so sanh nao, va ca co che bi bo.
    """
    ra, sau, muc = [], 0, 0
    i = 0
    while i < len(bt):
        c = bt[i]
        if c in "([":
            muc += 1
        elif c in ")]":
            muc -= 1
        elif muc == 0 and bt.startswith("&&", i):
            ra.append(bt[sau:i])
            sau = i + 2
            i += 1
        elif muc == 0 and bt.startswith("and", i) and \
                (i == 0 or not bt[i - 1].isalnum()) and \
                (i + 3 >= len(bt) or not bt[i + 3].isalnum()):
            ra.append(bt[sau:i])
            sau = i + 3
            i += 2
        i += 1
    ra.append(bt[sau:])
    return [_boc_ngoac(x.strip()) for x in ra if x.strip()]


#: Dao chieu mot phep so sanh, de dich `!(a < b)`. `cheo_len`/`cheo_xuong`
#: KHONG co trong bang: phu dinh mot phep cat KHONG phai phep cat nguoc lai
#: (`!crossover` dung ca luc hai duong khong cat nhau), nen gap thi tu choi.
_DAO_PHEP = {">": "<=", ">=": "<", "<": ">=", "<=": ">"}


def _boc_ngoac(s: str) -> str:
    """Bo cap ngoac BAO NGOAI, va chi khi no that su bao ngoai.

    `.strip("()")` mu lam hong lay: no cat dau `)` cuoi cua
    `crossover(source, BBlower)` thanh `crossover(source, BBlower`, va sau do
    khong regex nao khop duoc nua. Do that: moi dieu kien crossover trong kho
    Pine deu rot o day.
    """
    s = s.strip()
    while len(s) > 1 and s[0] == "(" and s[-1] == ")":
        muc = 0
        for i, c in enumerate(s):
            if c == "(":
                muc += 1
            elif c == ")":
                muc -= 1
                if muc == 0 and i < len(s) - 1:
                    return s          # ngoac dau dong lai giua chung -> khong bao ngoai
        s = s[1:-1].strip()
    return s


def _no_dieu_kien(bt: str, vi_tri: int, bang_cb: list, bang_bl: list,
                  sau: int = 0) -> tuple[list[dict], list[str]]:
    """Bieu thuc guard -> danh sach dieu kien DSL. Tra (dieu kien, phan khong dich duoc).

    De quy: mot ve co the la mot BIEN tro toi mot bieu thuc khac
    (`trade_entry = fractal_trend and fractal_breakout`), nen phai no ra toi khi
    cham day la mot phep so sanh.
    """
    if sau > 5:
        return [], [bt[:60]]
    dk, ho = [], []
    for ve in _tach_va(bt):
        ve = ve.strip().rstrip(";").strip()
        if not ve:
            continue
        if " or " in f" {ve} " or "||" in ve:
            ho.append(ve[:60])          # `or` khong dien dat duoc bang danh sach VA
            continue
        # PHU DINH. Bo dau `!` rui doc tiep la doi han y nghia, nen phai dao
        # phep so sanh. Chi lam khi ve trong no ra DUNG MOT dieu kien: `!(a &&
        # b)` la `!a || !b` - mot phep HOAC, khong xep duoc vao danh sach VA.
        if ve.startswith("!") and not ve.startswith("!="):
            d2, h2 = _no_dieu_kien(_boc_ngoac(ve[1:].strip()), vi_tri,
                                   bang_cb, bang_bl, sau + 1)
            if not h2 and len(d2) == 1 and d2[0]["phep"] in _DAO_PHEP:
                dk.append(dict(d2[0], phep=_DAO_PHEP[d2[0]["phep"]]))
            else:
                ho.append(ve[:60])
            continue
        m = _SS.fullmatch(ve) or _SS.search(ve)
        if m and m.group(0).strip() == ve:
            trai = _toan_hang(m.group(1), vi_tri, bang_cb, bang_bl)
            phai = _toan_hang(m.group(3), vi_tri, bang_cb, bang_bl)
            if trai and phai and _hop_thang_do(trai, phai):
                dk.append({"trai": trai, "phep": _PHEP[m.group(2)], "phai": phai})
            else:
                ho.append(ve[:60])
            continue
        mc = _CHEO.fullmatch(ve) or _CHEO.search(ve)
        if mc and mc.group(0).strip() == ve:
            trai = _toan_hang(mc.group(2), vi_tri, bang_cb, bang_bl)
            phai = _toan_hang(mc.group(3), vi_tri, bang_cb, bang_bl)
            if trai and phai:
                dk.append({"trai": trai,
                           "phep": "cheo_len" if mc.group(1) == "crossover"
                                   else "cheo_xuong", "phai": phai})
            else:
                ho.append(ve[:60])
            continue
        # mot BIEN -> tim dinh nghia gan nhat TRUOC vi tri dung
        if re.fullmatch(_TEN, ve):
            dn = None
            for pos, ten, bt2 in bang_bl:
                if pos >= vi_tri:
                    break
                if ten == ve:
                    dn = (pos, bt2)
            if dn is not None:
                d2, h2 = _no_dieu_kien(dn[1], dn[0], bang_cb, bang_bl, sau + 1)
                dk += d2
                ho += h2
                continue
        ho.append(ve[:60])
    return dk, ho


def doc_chien_luoc(vb: str, nguon: str = "", tien_to: str = "ma") -> dict:
    """CHIEN LUOC THAT: lan tu `strategy.entry` nguoc ve dieu kien vao.

    Vi sao ham nay ton tai rieng voi `doc_ma`: ban dau bo doc nhat MOI phep so
    sanh trong file, ke ca nhung phep chi dung de VE hay to mau. Ty le rut thi
    cao nhung SAI - Sonic R ra 8 "kieu danh" trong khi ban goc vao lenh khi
    xu huong dung VA gia hoi ve dai VA nen xac nhan. Tam mau roi khong phai ba
    dieu kien ghep: chung kich hoat o nhung luc khac han nhau.

    O day di dung duong cua chuong trinh: tim `strategy.entry`, lay guard cua no
    (`when = ...` hoac khoi `if (...)` bao ngoai), no bien ra toi khi cham day la
    phep so sanh, roi ghep TAT CA lam mot co che.

    Va neu MOT ve khong dich duoc thi BO CA CO CHE, khong bo rieng ve do: bo mot
    ve lam dieu kien LONG hon ban goc - nhieu lenh hon, hanh vi khac - ma van
    mang ten cua tac gia. Do la noi doi. Ve khong dich duoc duoc bao ra o
    `chua_dien_dat_duoc` de biet ngu phap con thieu gi.
    """
    vb = _chuan_hoa(vb)

    if not vb or not _VAO_LENH.search(vb):
        return {"co_che": [], "chua_dien_dat_duoc": [], "so_vao_lenh": 0}
    bang_cb = _bang_ky_hieu(vb)
    bang_bl = _bang_bool(vb)
    khai = rut_input(vb)
    L = vb.splitlines(keepends=True)
    dau_dong = []
    p = 0
    for l in L:
        dau_dong.append(p)
        p += len(l)

    ra, ho, n = [], [], 0
    for m in _VAO_LENH.finditer(vb):
        n += 1
        doi = m.group("doi_p") or m.group("doi_m") or m.group("doi_o") or ""
        if m.group("mql"):
            # MQL5: chieu nam trong TEN HAM, khong nam trong doi so
            chieu = -1 if m.group("mql") == "Sell" else 1
        elif m.group("ham"):
            chieu = -1 if re.search(r"ORDER_TYPE_SELL|\bSELL\b", doi) else 1
        else:
            chieu = -1 if ("strategy.short" in doi
                           or re.search(r",\s*false", doi)) else 1
        guard, vi = None, m.start()
        mw = re.search(r"when\s*=\s*([^,)\n]+)", doi)
        if mw:
            guard = mw.group(1).strip()
        else:
            # lui tim khoi `if (...)` gan nhat phia tren
            i = max(k for k, x in enumerate(dau_dong) if x <= m.start())
            # Cua so 12 dong la du cho Pine (guard sat lenh) nhung KHONG du cho
            # MQL5: giua `if(dieu_kien)` va `trade.Buy()` thuong con tinh lot,
            # SL, TP - do 05/09 thay khoang cach den 30+ dong.
            for j in range(i, max(-1, i - 40), -1):
                # MQL5 hay viet `if(dk) {` tren MOT dong; ban cu doi dong
                # `if` phai ket thuc KHONG co `{` nen truot het file .mq5.
                mi = re.match(r"^[ \t]*if[ \t]*\(?(.+?)\)?[ \t]*\{?[ \t]*$",
                              L[j].rstrip())
                if mi:
                    ung = mi.group(1).strip()
                    # BO QUA `if` la KIEM LOI cua chinh lenh vao. MQL5 viet
                    # `if(!trade.Buy(...))` hoac `if(!OrderSend(req,res))` -
                    # do la xu ly that bai, khong phai dieu kien vao. Lay no
                    # lam guard thi co che sinh ra la `!OrderSend(request,
                    # result)`, vo nghia. Do 05/09: day la ly do hang dau
                    # khien 113 file nhan ra lenh vao ma 0 file ra co che.
                    if _LA_KIEM_LOI.search(ung):
                        continue
                    guard, vi = ung, dau_dong[j]
                    break
        # LAN QUA RANH GIOI HAM. Guard sat lenh chi noi dang di nhanh nao;
        # dieu kien chien luoc nam o cho GOI ham bao lenh vao.
        if guard is None or _LA_PHAN_NHANH.search(guard):
            ten_ham = _ham_bao(vb, m.start())
            tim_duoc = None
            if ten_ham:
                for vt in _cho_goi(vb, ten_ham, m.start())[:6]:
                    k = max(kk for kk, xx in enumerate(dau_dong) if xx <= vt)
                    for j in range(k, max(-1, k - 25), -1):
                        mi2 = re.match(
                            r"^[ \t]*if[ \t]*\(?(.+?)\)?[ \t]*\{?[ \t]*$",
                            L[j].rstrip())
                        if not mi2:
                            continue
                        g2 = mi2.group(1).strip()
                        if _LA_KIEM_LOI.search(g2) or _LA_PHAN_NHANH.search(g2):
                            continue
                        tim_duoc, vi = g2, dau_dong[j]
                        break
                    if tim_duoc:
                        break
            if tim_duoc:
                guard = tim_duoc
        if not guard:
            ho.append("khong tim duoc guard cua lenh vao")
            continue
        dk, h = _no_dieu_kien(guard, vi, bang_cb, bang_bl)
        if h or not dk:
            ho += h or ["guard rong sau khi dich"]
            continue                    # BO CA CO CHE, khong bo rieng ve
        ten = f"{tien_to}_{'mua' if chieu == 1 else 'ban'}_" + "_va_".join(
            f"{_ten_toan_hang(d['trai'])}_{_TEN_PHEP[d['phep']]}_{_ten_toan_hang(d['phai'])}"
            for d in dk[:3])
        ra.append({
            "ten": ten[:60], "ho": _ho_cua(dk[0]), "chieu": chieu, "giu": 1,
            "co_che": (
                f"Chien luoc THAT rut tu `strategy.entry`: vao lenh khi "
                f"{len(dk)} dieu kien cung dung (`{guard[:70]}`). Phoi nhiem duoc "
                f"tra tien khi ben doi ung buoc phai giao dich o dung trang thai "
                f"nay - gia thuyet kiem chinh dieu do."),
            "vao": dk, "nguon": nguon,
            "luoi_goc": {k: v for d in dk
                         for k, v in _luoi_tu_dieu_kien(d, khai).items()},
            "so_dieu_kien": len(dk),
        })
    return {"co_che": ra, "chua_dien_dat_duoc": sorted(set(ho))[:12],
            "so_vao_lenh": n}


def doc_ma(vb: str, ngon_ngu: str = "tu_doan", nguon: str = "",
           tien_to: str = "ma", toi_da: int = 12) -> list[dict]:
    """Mot file ma -> NHIEU khai bao co che theo `nhan/ngu_phap.py`.

    Tra `[]` khi khong dich duoc dieu kien nao - do la ket qua binh thuong va
    pho bien (mot file tien ich quan ly lenh khong co dieu kien vao nao ca).
    """
    vb = _chuan_hoa(vb)

    if not vb:
        return []
    bang = _bang_ky_hieu(vb)
    khai = rut_input(vb)
    ra = []
    for dk in _dieu_kien(vb, bang)[:toi_da]:
        trich = dk.pop("_trich", "")
        ho = _ho_cua(dk)
        # KHONG sinh co che ho `khac`. Day khong phai bo loc chat lam canh: luat
        # cua du an la moi ho phai khai duoc PHAM VI ("chay o lop tai san nao,
        # hong o lop nao, vi sao") - xem `nhan/pham_vi.py` va bai kiem
        # `test_moi_khai_bao_deu_co_ly_do_co_che`. Mot dieu kien nhu
        # `close > open` khong goi ten duoc co che kinh te nao, nen khong co co
        # so de doi hoi mot phep thu phan chung cho no. Dat ten duoc ho truoc da.
        if ho == "khac":
            continue
        ten = f"{tien_to}_{_ten_toan_hang(dk['trai'])}_{_TEN_PHEP[dk['phep']]}_{_ten_toan_hang(dk['phai'])}"
        ra.append({
            "ten": ten[:60],
            "ho": ho,
            "chieu": 1,
            "giu": 1,
            "co_che": (
                f"Rut tu ma nguon that: dieu kien `{trich}`. Phoi nhiem duoc tra "
                f"tien khi ben doi ung buoc phai giao dich o dung trang thai nay - "
                f"gia thuyet nay kiem chinh dieu do, khong kiem cai bot goc."),
            "vao": [dk],
            "nguon": nguon,
            # MIEN QUET CUA CHINH TAC GIA (them 01/09). Khong chay mot dong ma
            # nao cua ho: `input(34, minval=2, maxval=200)` da noi ro bien nay
            # chay trong khoang nao. Tang kham pha lay day lam DIEM NEO thay vi
            # mot luoi ta tu bia.
            "luoi_goc": _luoi_tu_dieu_kien(dk, khai),
        })
    return ra
