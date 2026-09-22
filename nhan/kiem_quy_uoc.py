# -*- coding: utf-8 -*-
"""kiem_quy_uoc.py - CHUYEN VIEC DOC DIFF THANH MOT PHEP DO.

Chu du an 19/09/2026 hoi: *"co the ra lenh cho no va xay quy trinh chat hon de
tiet kiem chi phi khong"*.

Co, va cho tiet kiem khong nam o loi nhac dai hon. No nam o day.

## VI SAO

Sau ba don hang giao cho mo hinh re, toi bat DI BAT LAI cung mot nhom loi:

    don 1   chu thich tieng Anh · cau `co_che` khong noi duoc ai tra tien
    don 2   NHAN BUA (`X > BIEN*_Point` nao cung la trailing) · chu co dau
    don 3   xep sai `ho` · chep nguyen luan diem cua khuon khac sang

Doc diff de bat nhung thu nay la viec lap lai, va viec lap lai thi khong nen
tra tien cho mot mo hinh manh. Moi lan bat duoc mot LOP loi bang mat, phep dung
la bien no thanh mot phep kiem - de lan sau khong ai phai doc cho do nua.

Day cung la dung luat cua `qwen/cong.py`: **cong phai la code, khong phai y
kien.** Tuyen do truoc nay chi ap cho ket qua do luong; file nay keo no sang ca
quy uoc viet ma.

## CAI GI KIEM DUOC VA CAI GI KHONG

Kiem duoc (o day):
  * chu thich co DAU THANH - kho viet tieng Viet khong dau;
  * hai co che khac nhau dung CHUNG mot cau `co_che`;
  * `ho` khai khong khop NHOM toan hang that su dung;
  * cau `co_che` qua ngan hoac chi liet ke lai tham so.

KHONG kiem duoc, va dung la khong nen gia vo:
  * mot cau `co_che` co that su noi duoc ai tra tien khong;
  * mot bo boc co dang NHAN BUA khong.
Hai thu do van phai doc bang mat. Nhung chung it hon han khi bon thu tren da
duoc may loc truoc.
"""
from __future__ import annotations

import re

#: Nguyen am co dau thanh tieng Viet. Kho quy uoc viet KHONG DAU.
_CO_DAU = re.compile(
    "[À-ÃÈ-ÊÌÍÒ-ÕÙÚÝ"
    "à-ãè-êìíò-õùúý"
    "ĂăĐđĨĩŨũƠơƯư"
    "Ạ-ỹ]")

#: Do dai toi thieu cua mot cau `co_che` de con la mot LUAN DIEM.
#: `ngu_phap.kiem_khai_bao` doi 25; o day siet hon vi day la ma TU SINH, noi
#: mot cau 25 ky tu gan nhu chac chan la mot nhan chu khong phai mot lap luan.
DAI_TOI_THIEU = 60

#: Dau hieu cau `co_che` chi dang liet ke lai tham so thay vi noi ly do.
_LIET_KE = re.compile(r"\b(tham so|param|n\s*=|chu ky\s*=|nguong\s*=)", re.I)


def dong_co_dau(vb: str) -> list[tuple[int, str]]:
    """(so dong, noi dung) cho moi dong CHU THICH co dau thanh."""
    ra = []
    for i, l in enumerate(vb.splitlines(), 1):
        s = l.strip()
        if not (s.startswith("#") or s.startswith('"""') or s.startswith("'''")):
            continue
        if _CO_DAU.search(l):
            ra.append((i, s[:70]))
    return ra


def co_che_trung(specs: list[dict], dai: int = 70) -> list[tuple[str, list]]:
    """Cac cau `co_che` duoc dung o NHIEU khuon khac nhau.

    Hai khuon chung mot luan diem la hai phep thu tra tien FDR HAI LAN cho mot
    cau hoi. Neu chung that su khac nhau thi phai noi duoc khac o dau; neu
    khong noi duoc thi chung la mot.
    """
    theo: dict[str, set] = {}
    for s in specs:
        theo.setdefault(str(s.get("co_che", ""))[:dai],
                        set()).add(str(s.get("khuon", "")))
    return [(k, sorted(v)) for k, v in sorted(theo.items()) if len(v) > 1]


def co_che_yeu(specs: list[dict]) -> list[tuple[str, str]]:
    """(ten, ly do) cho moi co che co cau `co_che` khong dat."""
    ra = []
    for s in specs:
        c = str(s.get("co_che", ""))
        if len(c) < DAI_TOI_THIEU:
            ra.append((s.get("ten", ""), "cau qua ngan (%d < %d)"
                       % (len(c), DAI_TOI_THIEU)))
        elif _LIET_KE.search(c):
            ra.append((s.get("ten", ""), "liet ke tham so thay vi noi ly do"))
    return ra


#: NHOM toan hang -> cac `ho` hop le voi no. Mot `ho` khai lech voi nhom that
#: su dung lam bang phan tich theo ho tro thanh vo nghia.
_HO_HOP = {
    "do_cang": {"quay_ve_trung_binh", "bien_dong"},
    "bien_dong": {"bien_dong"},
    "lich": {"lich", "phien"},
    "dong_tien": {"dong_tien"},
}


def ho_lech_nhom(specs: list[dict], nhom_cua) -> list[tuple[str, str, str]]:
    """(ten, ho khai, nhom that) cho moi co che xep `ho` khong khop von tu.

    Chi xet khi CA cac ve deu thuoc mot nhom - mot co che ghep qua ho thi `ho`
    cua no la mot lua chon, khong phai mot suy ra.
    """
    ra = []
    for s in specs:
        nh = {nhom_cua(d.get("trai") or {}) for d in (s.get("vao") or [])}
        if len(nh) != 1:
            continue
        n = nh.pop()
        hop = _HO_HOP.get(n)
        if hop and s.get("ho") not in hop:
            ra.append((s.get("ten", ""), str(s.get("ho")), n))
    return ra
