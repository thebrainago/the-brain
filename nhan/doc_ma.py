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
_GIA = {"close": "close", "open": "open", "high": "high", "low": "low"}

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

#: `ten = <loi goi chi bao>` - bat ca Pine (`ema(close,89)`, `ta.ema(...)`) lan
#: MQL (`iMA(...)`, `iRSI(...)`).
_GAN_CB = re.compile(
    rf"^[ \t]*({_TEN})[ \t]*=[ \t]*((?:ta\.)?{_TEN}[ \t]*\([^\n]*)", re.M)

#: So sanh hai ve. Chan `==` va `!=` (khong phai phep cua ngu phap) va chan `=>`.
_SS = re.compile(
    rf"({_TEN}(?:\[\d+\])?|{_SO})[ \t]*(>=|<=|>|<)[ \t]*({_TEN}(?:\[\d+\])?|{_SO})")

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


def _toan_hang(tu: str, vi_tri: int, bang: list,
               bang_bt: list | None = None, sau: int = 0) -> dict | None:
    """Mot ve cua phep so sanh -> toan hang ngu phap, hoac None neu khong dich duoc."""
    tu = (tu or "").strip()
    # `x[k]` la NHIN LUI k bar. Ban dau ham nay CAT BO hau to do, va do la mot
    # loi lam hong nghia: `close > highest(high,34)` (khong co do tre) khong bao
    # gio dung, vi `highest` gom ca nen hien tai - cong bao "kich hoat 0,000%".
    # Ma pha vo that luon viet `highest(high,34)[1]`. Cung ho loi voi quy tac
    # `Open[i+1]` cua du an: mat do tre la doi hoan toan y nghia.
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
    r"strategy\.(entry|order)[ \t]*\(([^\n]*)", re.M)
#: Gan mot bien BOOL: `ten = <bieu thuc co so sanh hoac ket noi>`.
_GAN_BOOL = re.compile(rf"^[ \t]*({_TEN})[ \t]*=[ \t]*([^\n]+)$", re.M)


def _bang_bool(vb: str) -> list[tuple[int, str, str]]:
    """(vi tri, ten, bieu thuc) cho moi bien duoc gan mot bieu thuc."""
    return [(m.start(), m.group(1), m.group(2).strip())
            for m in _GAN_BOOL.finditer(vb)]


def _tach_va(bt: str) -> list[str]:
    """Tach mot bieu thuc theo `and` o MUC NGOAI CUNG."""
    ra, sau, muc = [], 0, 0
    i = 0
    while i < len(bt):
        c = bt[i]
        if c in "([":
            muc += 1
        elif c in ")]":
            muc -= 1
        elif muc == 0 and bt.startswith("and", i) and \
                (i == 0 or not bt[i - 1].isalnum()) and \
                (i + 3 >= len(bt) or not bt[i + 3].isalnum()):
            ra.append(bt[sau:i])
            sau = i + 3
            i += 2
        i += 1
    ra.append(bt[sau:])
    return [_boc_ngoac(x.strip()) for x in ra if x.strip()]


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
        if " or " in f" {ve} ":
            ho.append(ve[:60])          # `or` khong dien dat duoc bang danh sach VA
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

    if not vb or "strategy.entry" not in vb:
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
        doi = m.group(2)
        chieu = -1 if ("strategy.short" in doi or re.search(r",\s*false", doi)) else 1
        guard, vi = None, m.start()
        mw = re.search(r"when\s*=\s*([^,)\n]+)", doi)
        if mw:
            guard = mw.group(1).strip()
        else:
            # lui tim khoi `if (...)` gan nhat phia tren
            i = max(k for k, x in enumerate(dau_dong) if x <= m.start())
            for j in range(i, max(-1, i - 12), -1):
                mi = re.match(r"^[ \t]*if[ \t]*\(?([^\n{]+?)\)?[ \t]*$", L[j].rstrip())
                if mi:
                    guard, vi = mi.group(1).strip(), dau_dong[j]
                    break
        if not guard:
            ho.append("khong tim duoc guard cua strategy.entry")
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
