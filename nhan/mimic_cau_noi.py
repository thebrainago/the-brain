# -*- coding: utf-8 -*-
"""mimic_cau_noi.py - NOI `ds/mimic` VAO DUONG CHAY CHINH.

## Van de

`hethong.txt`: *"Xay dung kha nang truy nguoc lich su giao dich de tim ra chien
luoc roi dung mo phong chien luoc"* va *"Tu chien luoc co lich su se suy nguoc
de tim ra phuong phap trade"*.

`ds/mimic` da lam dung viec do: nhan so lenh + bar, chung cat ra mot cay quyet
dinh nong, tra ve luat dang `"rsi_14 <= 30.0000"`. Nhung no nam trong `ds/` -
mot kho GIT RIENG, khong gian import rieng (`from mimic.entry import ...`) - va
KHONG mot file nao trong `lab/nhan` hay `lab/tru` goi toi no. Do 11/09/2026:
120 tai lieu track-record + 400 ho so signal chua bao gio di qua no.

Mot module lam dung viec ma khong ai goi thi bang khong co.

## Cai kho THAT: tu vung

mimic co 7 dac trung. Doi chieu voi `nhan/ngu_phap.py`:

    rsi_14          -> {"chi_bao": "rsi", "n": 14}            KHOP HAN
    atr_14          -> {"chi_bao": "atr", "n": 14}            KHOP HAN
    hour            -> {"chi_bao": "gio"}                     KHOP HAN
    momentum_5/20   -> {"chi_bao": "doi_pct", "n": 5/20}      KHOP HAN
    price_position  -> (close - thap_nhat20) / (cao_nhat20 - thap_nhat20)
    dist_ma200_atr  -> (close - sma200) / sma200

Hai cai cuoi la BIEU THUC, khong phai mot toan hang. Ngu phap co `tuyen_tinh`
nhung viet chung se long ba tang va khong doi chieu lai duoc bang mat.

**Khong bia mot toan hang gan dung de ep cho khop.** Mot luat mimic doc sai con
te hon khong doc: no vao so nhu mot gia thuyet that, an mot suat FDR, va khi
truot thi ket luan "huong suy nguoc khong an" - trong khi cai truot la ban dich.
Hai dac trung do duoc ghi vao HANG DOI TU VUNG de khoi 1B nham.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(GOC))
    from nhan import so as SO
else:
    from . import so as SO

DS = GOC.parent / "ds"

#: dac trung mimic -> toan hang ngu phap. `None` = CHUA dien dat duoc.
BAN_DO: dict[str, dict | None] = {
    "rsi_14": {"chi_bao": "rsi", "n": 14},
    "atr_14": {"chi_bao": "atr", "n": 14},
    "hour": {"chi_bao": "gio"},
    "momentum_5": {"chi_bao": "doi_pct", "n": 5,
                   "cua": {"chi_bao": "gia", "cot": "close"}},
    "momentum_20": {"chi_bao": "doi_pct", "n": 20,
                    "cua": {"chi_bao": "gia", "cot": "close"}},
    "price_position": {"chi_bao": "stochastic", "n": 20},
    "dist_ma200_atr": {"chi_bao": "lech_tb",
                       "cua": {"chi_bao": "gia", "cot": "close"}, "n": 200},
}

_DK = re.compile(r"^\s*([a-z0-9_]+)\s*(<=|>=|<|>)\s*(-?\d+(?:\.\d+)?)\s*$", re.I)


def co_mimic() -> bool:
    return (DS / "mimic" / "pipeline.py").exists()


#: Nguong cua mimic va cua DSL co the khac THANG DO du cung mot dai luong.
#: `price_position` cua mimic nam trong [0, 1]; `stochastic` cua DSL la cung
#: cong thuc nhung NHAN 100. Dich ma quen he so nay thi `price_position <= 0,2`
#: thanh `stochastic <= 0,2` - mot dieu kien gan nhu khong bao gio dung, va no
#: se im lang bien moi luat hoc duoc thanh mot luat chet.
HE_SO_NGUONG = {"price_position": 100.0}


def dich_dieu_kien(dk: str) -> dict:
    """Mot chuoi luat mimic -> mot dieu kien DSL. -> {nhan, dieu_kien, ly_do}"""
    m = _DK.match(dk or "")
    if not m:
        return {"nhan": False, "ly_do": f"khong doc duoc dang luat: {dk!r}"}
    ten, phep, nguong = m.group(1), m.group(2), float(m.group(3))
    if ten not in BAN_DO:
        return {"nhan": False, "ly_do": f"dac trung la: {ten!r}",
                "thieu_tu_vung": ten}
    trai = BAN_DO[ten]
    if trai is None:
        return {"nhan": False,
                "ly_do": f"dac trung {ten!r} la BIEU THUC, ngu phap chua noi gon duoc",
                "thieu_tu_vung": ten}
    nguong *= HE_SO_NGUONG.get(ten, 1.0)
    return {"nhan": True, "ly_do": "",
            "dieu_kien": {"trai": dict(trai), "phep": phep,
                          "phai": {"hang": nguong}}}


def dich_luat(luat: dict, chieu: int = 1, ten: str = "",
              nguon: str = "") -> dict:
    """Mot `rule` cua mimic (`{conditions, pos_ratio, samples}`) -> spec DSL."""
    dk, thieu = [], []
    for c in luat.get("conditions") or []:
        r = dich_dieu_kien(c)
        if r["nhan"]:
            dk.append(r["dieu_kien"])
        else:
            thieu.append(r.get("thieu_tu_vung") or c)
    if not dk:
        return {"nhan": False, "ly_do": ["khong dieu kien nao dich duoc"],
                "thieu_tu_vung": thieu}
    if thieu:
        # Dich MOT PHAN la dich SAI: luat con lai long hon luat goc, nen no se
        # kich hoat nhieu hon han va moi con so deu khong con noi ve luat cua
        # trader nua.
        return {"nhan": False,
                "ly_do": [f"moi dich duoc {len(dk)}/{len(dk) + len(thieu)} dieu kien; "
                          f"dich mot phan lam luat LONG HON luat goc"],
                "thieu_tu_vung": thieu}
    from . import doc_hieu as DH
    return {"nhan": True, "ly_do": [], "thieu_tu_vung": [],
            "spec": {"ten": ten or DH.dat_ten(dk, chieu),
                     "ho": DH.suy_ho(dk, chieu), "chieu": chieu, "giu": 1,
                     "vao": dk, "ra": [],
                     "co_che": (f"Suy nguoc tu so lenh that bang ds/mimic "
                                f"(pos_ratio {luat.get('pos_ratio')}, "
                                f"{luat.get('samples')} mau). Nguoi ta tra tien cho "
                                f"phoi nhiem nay vi da co nguoi giao dich no that."),
                     "nguon": nguon}}


def ghi_tu_vung_thieu(thieu: list[str], nguon: str = "mimic") -> int:
    """Dac trung mimic chua dien dat duoc -> hang doi tu vung cua khoi 1B."""
    n = 0
    for t in set(thieu):
        SO.ghi_chi_so("mimic_thieu_tu_vung", 1.0,
                      {"dac_trung": t, "nguon": nguon})
        n += 1
    return n


def dich_the(the: dict, chieu: int = 1, nguon: str = "",
             nguong_pos: float = 0.5) -> dict:
    """Ca mot MimicCard/ket qua distill -> cac spec dich duoc."""
    luat = the.get("rules") or the.get("luat") or []
    ra, hong, thieu = [], [], []
    for i, l in enumerate(luat):
        if float(l.get("pos_ratio") or 0) < nguong_pos:
            continue
        r = dich_luat(l, chieu=chieu, nguon=nguon)
        if r["nhan"]:
            ra.append(r["spec"])
        else:
            hong.append({"luat": l.get("conditions"), "ly_do": r["ly_do"][0]})
            thieu += r.get("thieu_tu_vung") or []
    if thieu:
        ghi_tu_vung_thieu(thieu, nguon)
    return {"spec": ra, "khong_dich_duoc": hong,
            "thieu_tu_vung": sorted(set(thieu))}


def dang_ky(kq: dict) -> dict:
    """Dua spec dich duoc qua cong `them_co_che`."""
    from . import ngu_phap as NP
    nhan, tu_choi = 0, []
    for s in kq.get("spec") or []:
        try:
            r = NP.them_co_che(s)
        except Exception as e:
            r = {"nhan": False, "ly_do": [f"{type(e).__name__}: {e}"]}
        if r.get("nhan"):
            nhan += 1
        else:
            tu_choi.append({"ten": s.get("ten"), "ly_do": (r.get("ly_do") or [""])[0]})
    return {"nhan": nhan, "tu_choi": tu_choi}


if __name__ == "__main__":
    print(json.dumps({
        "co_mimic": co_mimic(),
        "dac_trung_khop": [k for k, v in BAN_DO.items() if v],
        "dac_trung_CHUA_noi_duoc": [k for k, v in BAN_DO.items() if v is None],
    }, ensure_ascii=False, indent=1))
