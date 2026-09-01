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
    return ra


def _toan_hang(tu: str, vi_tri: int, bang: list) -> dict | None:
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
    goc = _toan_hang_goc(tu, vi_tri, bang)
    if goc is None or tre <= 0:
        return goc
    if "hang" in goc:
        return goc                             # hang so tre van la chinh no
    return {"chi_bao": "tre", "cua": goc, "n": tre}


def _toan_hang_goc(tu: str, vi_tri: int, bang: list) -> dict | None:
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
        return None
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
        t = dk.get(ben) or {}
        while isinstance(t, dict) and t.get("chi_bao") in ("tre", "tuyet_doi"):
            t = t.get("cua") or {}
        cb = (t or {}).get("chi_bao")
        if cb in _HO:
            return _HO[cb]
    return "khac"


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


def doc_ma(vb: str, ngon_ngu: str = "tu_doan", nguon: str = "",
           tien_to: str = "ma", toi_da: int = 12) -> list[dict]:
    """Mot file ma -> NHIEU khai bao co che theo `nhan/ngu_phap.py`.

    Tra `[]` khi khong dich duoc dieu kien nao - do la ket qua binh thuong va
    pho bien (mot file tien ich quan ly lenh khong co dieu kien vao nao ca).
    """
    if not vb:
        return []
    bang = _bang_ky_hieu(vb)
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
        })
    return ra
