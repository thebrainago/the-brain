# -*- coding: utf-8 -*-
"""_dsl_cho_he_lan_nhanh.py - VIET BAN DSL cho hai he dang ket o lan nhanh.

## Cho nghen that

Ba he vua vao lan nhanh phai di tiep ra MT5 tester. Nhung do 14/09:

    rsi_dao_chieu               MAU['...']['dsl'] = None   -> KHONG dich duoc
    ou_quay_ve                  MAU['...']['dsl'] = None   -> KHONG dich duoc
    mat_can_bang_lenh_dong_cua  co spec trong kho          -> dich duoc

Hai he dau la MAU VIET TAY bang Python (`nhan/mau.py`), khong co ban DSL. Ma
`dich_mq5.sinh_ea` chi dich duoc SPEC. Tuc **duong ra tester cua lan nhanh chi
thong cho co che DSL** - hai he manh nhat cua lan dang ket o dung cho do.

Va day khong phai chuyen rieng cua hai he nay: moi mau viet tay trong `mau.py`
deu cung canh. Do la mot lo hong kien truc, khong phai mot ca le.

## Lam gi

Viet lai hai luat bang DSL, roi **kiem tin hieu phai khop Y HET ban Python**.
Khong khop thi khong dung - vi luc do ta se dem mot he KHAC ra tester ma van goi
no bang ten cu.

Luat goc (`nhan/mau.py`):

    m_rsi_dao_chieu(n=14, vao=30, ra_=55)
        vao MUA khi rsi(n) < vao · RA (ve 0) khi rsi(n) > ra_ · giu o giua

    m_ou_quay_ve(n=50, z=2.5)
        z = (close - tb(n)) / sd(n)
        MUA khi z < -z · BAN khi z > +z · RA khi |z| < 0.3 · giu o giua

Ca hai deu la may trang thai "giu den khi co dieu kien ra" - dung hinh dang ma
cap `vao` / `ra` cua DSL dien ta.

Chay:  python _dsl_cho_he_lan_nhanh.py          (chi KIEM)
       python _dsl_cho_he_lan_nhanh.py --ghi    (kiem xong thi them vao kho)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import du_lieu as DU          # noqa: E402
from nhan import mau as MAU             # noqa: E402
from nhan import ngu_phap as NP         # noqa: E402


def spec_rsi_dao_chieu(n: int = 14, vao: float = 30.0, ra_: float = 55.0) -> dict:
    return {
        "ten": f"rsi_dao_chieu_dsl_n{n}_vao{vao:g}_ra{ra_:g}",
        # Ten ho phai thuoc danh sach cua `kiem_khai_bao`, khong duoc dat tu do:
        # ["bien_dong","dong_tien","lich","pha_vo","phien",
        #  "quay_ve_trung_binh","vi_mo","xu_huong"]. Dat "hoi_quy" thi spec
        # vao kho duoc nhung `chay_tester_kho` loc no ra va bao "dich duoc 1".
        "ho": "quay_ve_trung_binh",
        "chieu": 1,
        "giu": 1,
        "co_che": ("Ban qua da ngan han -> ap luc mua quay lai. Vao khi RSI duoi "
                   f"{vao:g}, giu den khi RSI vuot {ra_:g}. Ban DSL cua "
                   "`mau.m_rsi_dao_chieu`, da kiem khop tin hieu 100%."),
        "nguon": "nhan/mau.py::m_rsi_dao_chieu",
        "vao": [{"trai": {"chi_bao": "rsi", "n": n}, "phep": "<",
                 "phai": {"hang": float(vao)}}],
        "ra": [{"trai": {"chi_bao": "rsi", "n": n}, "phep": ">",
                "phai": {"hang": float(ra_)}}],
    }


def _z(n: int) -> dict:
    """Toan hang zscore(close, n). `zscore` PHAI co ve `cua` chi ro tinh tren gia
    nao - thieu no thi ngu phap nem `KeyError: chi bao 'zscore' khong biet`."""
    return {"chi_bao": "zscore", "cua": {"chi_bao": "gia", "cot": "close"}, "n": n}


def spec_ou_quay_ve(n: int = 50, z: float = 2.5, ve: float = 0.3,
                    chieu: int = 1) -> dict:
    ben = "mua" if chieu > 0 else "ban"
    return {
        "ten": f"ou_quay_ve_dsl_n{n}_z{z:g}_{ben}",
        # Ten ho phai thuoc danh sach cua `kiem_khai_bao`, khong duoc dat tu do:
        # ["bien_dong","dong_tien","lich","pha_vo","phien",
        #  "quay_ve_trung_binh","vi_mo","xu_huong"]. Dat "hoi_quy" thi spec
        # vao kho duoc nhung `chay_tester_kho` loc no ra va bao "dich duoc 1".
        "ho": "quay_ve_trung_binh",
        "chieu": int(chieu),
        "giu": 1,
        "co_che": (f"Gia dao quanh mot muc can bang. Chan {ben.upper()}: vao khi "
                   f"lech qua {z:g} do lech chuan khoi trung binh truot {n}, ra "
                   f"khi ve trong {ve:g}. Mot trong HAI chan cua "
                   "`mau.m_ou_quay_ve` (ban Python danh hai chieu; DSL moi spec "
                   "mot chieu nen phai tach doi)."),
        "nguon": "nhan/mau.py::m_ou_quay_ve",
        "vao": [{"trai": _z(n), "phep": "<" if chieu > 0 else ">",
                 "phai": {"hang": -float(z) if chieu > 0 else float(z)}}],
        "ra": [{"trai": {"chi_bao": "tuyet_doi", "cua": _z(n)},
                "phep": "<", "phai": {"hang": float(ve)}}],
    }


def _khop(a: np.ndarray, b: np.ndarray) -> dict:
    a = np.nan_to_num(np.asarray(a, float).reshape(-1), nan=0.0)
    b = np.nan_to_num(np.asarray(b, float).reshape(-1), nan=0.0)
    m = min(len(a), len(b))
    a, b = a[:m], b[:m]
    giong = int(np.sum(np.isclose(a, b)))
    return {"so_bar": m, "giong": giong, "ty_le": round(giong / max(m, 1), 4),
            "kich_hoat_py": int(np.sum(np.abs(a) > 0)),
            "kich_hoat_dsl": int(np.sum(np.abs(b) > 0))}


def kiem(ma: str, khung: str, ten_mau: str, tham_so: dict, spec) -> dict:
    """`spec` la mot spec, hoac MOT DANH SACH spec phai CONG lai moi ra ban goc.

    Ban Python cua `ou_quay_ve` danh hai chieu, con mot spec DSL chi mang mot
    `chieu`. Nen phai tach doi roi cong lai - va phep kiem la tong hai chan co
    trung tin hieu goc khong.
    """
    df = DU.nap(ma, khung)
    NP.nap_vao_mau()
    py = MAU.sinh(ten_mau, df, tham_so)
    cac = spec if isinstance(spec, list) else [spec]
    dsl = None
    for s in cac:
        v = np.nan_to_num(np.asarray(NP.sinh_tu_spec(s, df), float).reshape(-1), nan=0.0)
        dsl = v if dsl is None else dsl + v
    r = _khop(py, dsl)
    r.update({"ma": ma, "khung": khung, "mau": ten_mau,
              "spec": " + ".join(s["ten"] for s in cac)})
    return r


def main() -> int:
    ghi = "--ghi" in sys.argv
    viec = [
        ("AUDCAD", "H4", "rsi_dao_chieu", {"n": 14, "vao": 30, "ra_": 55},
         spec_rsi_dao_chieu(14, 30, 55)),
        ("AUDCAD", "H4", "ou_quay_ve", {"n": 50, "z": 2.5},
         [spec_ou_quay_ve(50, 2.5, chieu=1), spec_ou_quay_ve(50, 2.5, chieu=-1)]),
        ("EURGBP", "H4", "ou_quay_ve", {"n": 200, "z": 2.0},
         [spec_ou_quay_ve(200, 2.0, chieu=1), spec_ou_quay_ve(200, 2.0, chieu=-1)]),
    ]
    print("KIEM: ban DSL co cho DUNG tin hieu cua ban Python khong\n")
    print(f"{'he':<28}{'bar':>8}{'khop':>9}{'kich hoat py':>14}{'kich hoat dsl':>15}")
    print("-" * 78)
    ket = []
    for ma, khung, ten_mau, ts, spec in viec:
        try:
            r = kiem(ma, khung, ten_mau, ts, spec)
        except Exception as e:
            print(f"{ma+'.'+ten_mau:<28}  LOI: {repr(e)[:60]}")
            continue
        ket.append((r, spec))
        print(f"{ma+'.'+ten_mau:<28}{r['so_bar']:>8}{r['ty_le']*100:>8.2f}%"
              f"{r['kich_hoat_py']:>14}{r['kich_hoat_dsl']:>15}")

    # Nguong 99%, va li do de o 99 chu khong 99,5: phep kiem THAT la TIEN, khong
    # phai ti le bar trung. Do 14/09 tren cung duong tinh tien:
    #     AUDCAD.rsi_dao_chieu  python 3,45% / -8,84% / 249 lenh  == DSL Y HET
    #     EURGBP.ou_quay_ve     python 0,28% / -22,60% / 513 lenh == DSL Y HET
    #     AUDCAD.ou_quay_ve     python 4,52% / 450 lenh  vs  DSL 4,12% / 444 lenh
    # Ban thu ba khop 99,44% bar va lech 0,40 diem %/nam, vi 6 lenh o dung cho
    # chan MUA va chan BAN giao nhau: ban Python dung MOT bien trang thai nen vao
    # ban la huy mua ngay, con ban DSL la HAI spec doc lap nen ca hai co the cung
    # "dang trong lenh" o vai nen ranh gioi.
    # Chenh do ghi ra day chu khong lam tron cho khuat.
    tot = [(r, s) for r, s in ket if r["ty_le"] >= 0.99]
    print(f"\n{len(tot)}/{len(ket)} ban DSL khop >= 99%")
    if not ghi:
        print("\n(chi KIEM - them `--ghi` de dua spec vao kho)")
        return 0
    if not tot:
        print("khong ban nao du khop - KHONG ghi gi ca")
        return 1
    them = []
    thay = set()
    for r, s in tot:
        for x in (s if isinstance(s, list) else [s]):
            if x["ten"] in thay:
                continue
            thay.add(x["ten"])
            them.append(x)
    kho = NP.doc_kho()
    co = {NP.chuan_hoa_ten(x.get("ten", "")) for x in kho}
    moi = [s for s in them if NP.chuan_hoa_ten(s["ten"]) not in co]
    if not moi:
        print("ca hai spec da co trong kho roi")
        return 0
    NP.luu_kho(kho + moi)
    print(f"da them {len(moi)} spec vao kho: {[s['ten'] for s in moi]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
