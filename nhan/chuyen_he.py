# -*- coding: utf-8 -*-
"""chuyen_he.py - MANG MOT HE SANG CHO KHAC MA NO VAN LA CHINH NO.

## Ba module, mot cau hoi

So do he thong: *"tat ca moi chien luoc can test da cap / da khung / da phuong
phap quan li lenh / da thong so input"*. Ba module lam ba nua cua viec do, va
**ca ba deu MO COI** cho toi 12/09/2026 (ban do sinh tu ma nguon):

    nhan/doi_khung.py         D1 -> H4/H1: doi CHU KY va NGUONG theo ti le bar
    nhan/ngoai_sinh.py        ma A -> ma B: GIU TY LE KICH HOAT, khong giu so
    nhan/quy_doi_tham_so.py   doi tai san thi tham so (pip/tien) phai doi theo

Ca ba tra loi cung mot cau: *mang he nay sang cho khac thi phai sua gi de no
van la chinh no?* De roi thi moi lan can chuyen, nguoi ta lai lam bang tay.

## CAI KHONG DOI KHI SANG CHO KHAC LA DO HIEM CUA SU KIEN

Day la nguyen tac chung cua ca ba, va no khong hien nhien. `zscore(5) < -1,0`
kich hoat 19,6% so bar tren D1; cung nguong do tren H1 kich hoat khac han vi
nhieu lon hon. Giu CON SO la mat do chon loc; giu TY LE KICH HOAT moi la giu
chinh co che. (`CLAUDE.md`, muc "DOI KHUNG = DOI TAI SAN ve mat phuong phap".)

Quy doi chu ky theo ti le bar la CAN NHUNG KHONG DU - do 07/09: be 36 chan tu
D1 sang khung khac, chi quy doi chu ky, thi W1 12/36 duong · H4 21/36 · H1 6/36.

## HAI DUONG, DUNG LAN

    A. he DA CO  -> khung/tai san khac   -> file nay
    B. tim he MOI ngay tren khung do     -> quet lai tu dau, khong chuyen gi

Duong B khong dinh van de nguong vi no chon lai tu dau. File nay chi lo duong A.

Chay:  python -m nhan.chuyen_he --khung H4
       python -m nhan.chuyen_he --ma XAUUSDM
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

SO = LAB / "reports" / "CHUYEN_HE.json"

#: Lay bao nhieu co che dau bang de thu. Chuyen la phep dat (moi co che phai
#: chay lai tren chuoi dich), nen khong quet ca kho.
TRAN = 15


def _nguon(in_ra=print) -> list[dict]:
    """Co che de chuyen: uu tien cai QUA HOLDOUT, khong co thi lay top."""
    p = LAB / "reports" / "TO_HOP.json"
    if not p.exists():
        return []
    d = json.loads(p.read_text(encoding="utf-8"))
    qua = [r for r in (d.get("holdout") or []) if r.get("qua_holdout")]
    if qua:
        in_ra and in_ra("  nguon: %d co che QUA HOLDOUT" % len(qua))
        return qua[:TRAN]
    top = d.get("top") or []
    in_ra and in_ra("  nguon: 0 qua holdout -> lay %d dong dau bang (yeu hon)"
                    % min(len(top), TRAN))
    return top[:TRAN]


def sang_khung(khung_dich: str = "H4", in_ra=print) -> dict:
    """Chuyen cac co che dang co sang mot khung khac, bao cai nao DAT."""
    from nhan import doi_khung as DK
    from nhan import ngu_phap as NP
    ds = _nguon(in_ra)
    if not ds:
        return {"bo": "chua co TO_HOP.json"}
    # Tra theo `ten`: `to_hop._mot_o` ghi `d["co_che"] = spec.get("ten")`, khong
    # phai van tay. Tra nham khoa thi bao "khong tim thay spec" cho MOI dong va
    # ta lai tuong kho rong - mot am tinh gia nua cung ho voi [[luat-do-phai-thay-duoc-cai-co]].
    kho = {}
    for x in NP.doc_kho():
        if isinstance(x, dict):
            for k in (x.get("ten"), x.get("van_tay")):
                if k:
                    kho.setdefault(k, x)
    ra, thieu = [], 0
    for r in ds:
        spec = kho.get(r.get("co_che"))
        if not isinstance(spec, dict):
            thieu += 1
            continue
        khung_goc = r.get("khung", "D1")
        if khung_goc == khung_dich:
            continue
        # `doi()` tra MOT dict {spec, hs, nguong, kich_hoat} - khong phai cap.
        # Ban dau toi giai nen thanh `moi, bao` va moi dong do voi "not enough
        # values to unpack"; loi do chi nam trong JSON chu khong in ra, nen
        # man hinh van bao "0/1 co che giu duoc" nhu mot ket qua binh thuong.
        # Mot loi bi nuot thanh mot ket luan am - dung ho benh cua ca ngay.
        try:
            k = DK.doi(spec, r["ma"], khung_goc, khung_dich)
        except Exception as e:
            k = {"loi": "%s: %s" % (type(e).__name__, str(e)[:70])}
        if k.get("loi"):
            ra.append({"ma": r["ma"], "co_che": str(r.get("co_che"))[:30],
                       "loi": k["loi"]})
            in_ra("  %-10s %-30s LOI: %s"
                  % (r["ma"], str(r.get("co_che"))[:30], k["loi"]))
            continue
        ok = DK.dat(k)
        ra.append({"ma": r["ma"], "co_che": str(r.get("co_che"))[:30],
                   "tu": khung_goc, "sang": khung_dich, "dat": bool(ok),
                   "hs": k.get("hs"), "kich_hoat": k.get("kich_hoat")})
        in_ra("  %-10s %-30s %s -> %s  (ti le bar x%s)  %s"
              % (r["ma"], str(r.get("co_che"))[:30], khung_goc, khung_dich,
                 k.get("hs"), "DAT" if ok else "lech qua nguong"))
    if thieu:
        in_ra("  %d co che khong tim thay spec trong kho - bo qua" % thieu)
    # BA nhom, khong phai hai. "Thieu du lieu H4" va "doi xong thi lech qua
    # nguong" la hai ket luan khac han nhau: mot cai la CHUA DO DUOC, cai kia
    # moi la ket qua am. Gop chung lai thi bang bao "0/1 giu duoc" va nguoi doc
    # ket luan sai ve co che.
    loi = [x for x in ra if x.get("loi")]
    do_duoc = [x for x in ra if not x.get("loi")]
    dat = [x for x in do_duoc if x.get("dat")]
    in_ra("")
    if do_duoc:
        in_ra("  DO DUOC  %d/%d co che giu duoc ty le kich hoat khi sang %s"
              % (len(dat), len(do_duoc), khung_dich))
        if not dat:
            in_ra("           KHONG co nghia la co che sai.")
            in_ra("           Nghia la no GAN VOI KHUNG goc.")
    if loi:
        in_ra("  CHUA DO  %d co che khong do duoc (thuong la thieu du lieu o"
              % len(loi))
        in_ra("           khung dich) - day KHONG phai ket qua am.")
    return {"khung_dich": khung_dich, "thu": len(ra), "do_duoc": len(do_duoc),
            "dat": len(dat), "chua_do_duoc": len(loi), "thieu_spec": thieu,
            "chi_tiet": ra}


def sang_ma(ma_dich: str, khung_dich: str = "D1", ma_goc: str = "US500CASH",
            in_ra=print) -> dict:
    """Chuyen cac he DA PASS sang mot tai san khac (`ngoai_sinh`).

    Kem khau QUY DOI THAM SO (`quy_doi_tham_so`): mot SL "50 diem" tren
    US500CASH va tren XAUUSDM khong cung nghia gi ca. Chi hai don vi CO THU
    NGUYEN GIA duoc nhan ti le ATR; `boi_so`/`dem`/`phan_tram`/`lot` giu nguyen
    - doi chung la lam hong y dinh cua tac gia.
    """
    from nhan import ngoai_sinh as NS
    from nhan import quy_doi_tham_so as QT
    try:
        k = NS.ung_vien(ma_dich, khung_dich) or {}
    except Exception as e:
        return {"loi": "%s: %s" % (type(e).__name__, str(e)[:120])}
    ds = k.get("ung_vien") or k.get("ds") or []
    in_ra("  %s %s: %d ung vien chuyen duoc" % (ma_dich, khung_dich, len(ds)))
    for x in ds[:10]:
        if isinstance(x, dict):
            in_ra("    %-26s %s" % (str(x.get("template"))[:26],
                                    x.get("tham_so")))

    quy = None
    a_goc, a_dich = QT.atr_cua(ma_goc, khung_dich), QT.atr_cua(ma_dich,
                                                               khung_dich)
    if a_goc and a_dich:
        khai = []
        for x in ds:
            for ten, gt in (x.get("tham_so") or {}).items():
                if isinstance(gt, (int, float)):
                    khai.append({"ten": ten, "gia_tri": float(gt),
                                 "don_vi": QT.phan_loai(ten)})
        if khai:
            try:
                quy = QT.quy_doi(khai, a_goc, a_dich)
                in_ra("")
                in_ra("  QUY DOI THAM SO %s -> %s (ATR %.5f -> %.5f, x%.3f)"
                      % (ma_goc, ma_dich, a_goc, a_dich, a_dich / a_goc))
                for d in (quy.get("khai") or quy.get("ket") or [])[:8]:
                    in_ra("    %s" % d)
                if quy.get("khong_ro"):
                    in_ra("    %d tham so KHONG RO don vi - giu nguyen va bao "
                          "ra de nguoi kiem, khong doan" % len(quy["khong_ro"]))
            except Exception as e:
                in_ra("  khong quy doi duoc: %s" % e)
    else:
        in_ra("  chua do duoc ATR cua %s hoac %s - bo qua khau quy doi"
              % (ma_goc, ma_dich))
    return {"ma_dich": ma_dich, "khung_dich": khung_dich, "so": len(ds),
            "quy_doi": bool(quy)}


def main(argv: list[str]) -> int:
    if "--ma" in argv:
        k = sang_ma(argv[argv.index("--ma") + 1],
                    argv[argv.index("--khung") + 1] if "--khung" in argv
                    else "D1")
    else:
        k = sang_khung(argv[argv.index("--khung") + 1]
                       if "--khung" in argv else "H4")
    SO.parent.mkdir(exist_ok=True)
    SO.write_text(json.dumps(k, ensure_ascii=False, indent=1, default=str),
                  encoding="utf-8")
    print("-> %s" % SO)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
