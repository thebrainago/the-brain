# -*- coding: utf-8 -*-
"""chuoi_quan_tri.py - NOI BA MANH QUAN TRI VI THE THANH MOT DUONG CHAY.

## Lo hong nay va

Chu du an viet trong `SO_DO_HE_THONG.txt`, ve dung module nay:

    "Rieng muc nay can chu y vi no la module quan trong trong toan bo he thong...
     viec su dung ky thuat quan li lenh tot con hon viec co 1 entry tot"
    "He quan li lenh nay co the quan tri doc lap hoac lam 1 bo quy tac de tich
     hop vao nhung he thong khac (test thu tung phuong phap quan li lenh khac
     nhau) de xem hieu qua cung nhu ket qua thay doi ra sao"

Ba manh de lam dung viec do da co tu 07-09/09, va **ca ba deu MO COI** - ban do
sinh tu ma nguon (`nhan/ban_do.py`) tim ra ngay 12/09:

    nhan/quan_tri_dsl.py    ngon ngu khai bao   (75 khai bao trong kho)
    nhan/dich_mq5_qtvt.py   khai bao -> MQL5
    nhan/de_quan_tri.py     chen khoi MQL5 vao EA NGOAI

Ba manh roi thi khong ai chay duoc chuoi. Day la luat L7: *cong cu khong nam
tren duong chay thi bang khong co* - va lan nay no an mat dung cai module ma
chu du an goi la quan trong nhat.

## BON KHAU

    1 KHO     doc 75 khai bao quan tri da boc, xep theo LOP (don / ro)
    2 DICH    mot khai bao -> khoi MQL5 (`sinh_khoi`)
    3 CHEN    khoi do -> vao ma nguon mot EA co san (`chen`)
    4 DOI     sinh CAP file: ban GOC va ban CO QUAN TRI, de tester do bat/tat

Khau 4 la khau tra loi cau hoi cua so do - *"hieu qua thay doi ra sao"*. Khong
co no thi chi biet "chen duoc", khong biet "chen co loi khong".

## KHONG TU CHAY TESTER

Mot `terminal64.exe` la rang buoc VAT LY (`nhan/khoa_tester.py`). File nay chi
SINH RA cap file .mq5; viec dua vao tester di theo duong da co
(`chay_tester_kho.py`), khong mo duong thu hai.

Chay:  python -m nhan.chuoi_quan_tri --kho
       python -m nhan.chuoi_quan_tri --dich 3
       python -m nhan.chuoi_quan_tri --cap <duong/dan/EA.mq5> --khai-bao 3
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

RA = LAB / "reports" / "quan_tri_cap"


def kho(in_ra=print) -> list[dict]:
    """75 khai bao quan tri da boc, xep theo lop va dau hieu."""
    from nhan import quan_tri_dsl as QD
    ds = QD.doc_kho()
    dem_lop: dict[str, int] = {}
    dem_dh: dict[str, int] = {}
    for x in ds:
        dem_lop[x.get("lop") or "?"] = dem_lop.get(x.get("lop") or "?", 0) + 1
        for d in (x.get("dau_hieu") or []):
            dem_dh[d] = dem_dh.get(d, 0) + 1
    if in_ra:
        in_ra("KHO KHAI BAO QUAN TRI VI THE: %d" % len(ds))
        in_ra("  theo lop:     %s"
              % ", ".join("%s %d" % kv for kv in sorted(dem_lop.items())))
        in_ra("  theo dau hieu: %s"
              % ", ".join("%s %d" % kv
                          for kv in sorted(dem_dh.items(), key=lambda z: -z[1])))
        in_ra("")
        for i, x in enumerate(ds[:20]):
            in_ra("  %3d %-34s %-4s %s" % (i, str(x.get("ten"))[:34],
                                           x.get("lop") or "-",
                                           ",".join(x.get("dau_hieu") or [])))
        if len(ds) > 20:
            in_ra("  ... con %d khai bao nua" % (len(ds) - 20))
    return ds


def _atr_cua(ma: str, khung: str = "D1") -> tuple[float, float]:
    """(ATR trung vi, gia mot diem) cua tai san dich.

    `quan_tri_dsl.sang_atr` khong the goi luc BOC vi no can du lieu cua tai san
    DICH - do la ly do khau nay tach ra. Bo qua no thi 43/75 khai bao bao
    "con so chua quy ve ATR" va bi dem nham la "khong dich duoc".
    """
    import numpy as np
    from nhan import du_lieu as DL
    df = DL.cat_theo_chat_luong(DL.nap(ma, khung), ma)[0]
    h, l, c = (df["high"].to_numpy(float), df["low"].to_numpy(float),
               df["close"].to_numpy(float))
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.roll(c, 1)),
                                      np.abs(l - np.roll(c, 1))))
    tr[0] = h[0] - l[0]
    atr = float(np.median(tr[-500:] if len(tr) > 500 else tr))
    # gia mot "diem" theo quy uoc MT5: 5 chu so thi 1 pip = 10 diem.
    gia = float(np.median(c))
    diem = 0.0001 if gia < 20 else (0.01 if gia < 1000 else 0.1)
    return atr, diem


def dich(chi_so: int = 0, khung: str = "D1", ma: str = "US500CASH",
         in_ra=print) -> str:
    """Khai bao thu `chi_so` -> khoi MQL5, ĐÃ quy don vi ve ATR cua `ma`."""
    from nhan import dich_mq5_qtvt as DQ
    from nhan import quan_tri_dsl as QD
    ds = kho(in_ra=None)
    if not 0 <= chi_so < len(ds):
        raise IndexError("chi co %d khai bao (0..%d)" % (len(ds), len(ds) - 1))
    atr, diem = _atr_cua(ma, khung)
    spec = QD.sang_atr(ds[chi_so], atr, diem)
    src = DQ.sinh_khoi(spec, khung=khung)
    if in_ra:
        in_ra("# khai bao %d: %s  (quy theo ATR %s %s = %.5f)"
              % (chi_so, ds[chi_so].get("ten"), ma, khung, atr))
        in_ra(src)
    return src


def dich_het(khung: str = "D1", ma: str = "US500CASH",
             in_ra=print) -> dict:
    """Bao nhieu trong 75 khai bao DICH DUOC sang MQL5, va cai nao khong - vi sao.

    Do TUNG CHANG thay vi doan nut that ([[pheu-nguon-do-tung-chang]]). Con so
    "75 khai bao quan tri" khong co nghia gi neu phan lon khong ra duoc MQL5;
    va ly do tu choi moi la thu doc duoc - `dich_mq5_qtvt` tu choi dich
    'nhoi khong tran' vi do la cong thuc chay tai khoan, khong phai vi no hong.
    """
    from nhan import dich_mq5_qtvt as DQ
    from nhan import quan_tri_dsl as QD
    ds = kho(in_ra=None)
    atr, diem = _atr_cua(ma, khung)
    ok, tu_choi = [], {}
    for i, x in enumerate(ds):
        try:
            DQ.sinh_khoi(QD.sang_atr(x, atr, diem), khung=khung)
            ok.append(i)
        except Exception as e:
            ly = str(e)[:70]
            tu_choi.setdefault(ly, []).append(i)
    if in_ra:
        in_ra("DICH SANG MQL5 (quy theo ATR %s %s = %.5f): %d/%d khai bao"
              % (ma, khung, atr, len(ok), len(ds)))
        for ly, cac in sorted(tu_choi.items(), key=lambda z: -len(z[1])):
            in_ra("  %3d  %s" % (len(cac), ly))
        if ok:
            in_ra("")
            in_ra("  dich duoc, vi du: %s"
                  % ", ".join(str(ds[i].get("ten"))[:22] for i in ok[:5]))
    return {"tong": len(ds), "dich_duoc": ok,
            "tu_choi": {k: len(v) for k, v in tu_choi.items()}}


def cap_doi_chieu(duong_ea: str, chi_so: int = 0, khung: str = "D1",
                  in_ra=print) -> dict:
    """Sinh CAP file: ban GOC va ban CO QUAN TRI cua cung mot EA.

    Cap nay la thu tester can de tra loi *"hieu qua thay doi ra sao"*. Sinh cap
    chu khong sua tai cho: mot ban sua de len ban goc thi het doi chieu duoc, va
    khong ai chung minh duoc phan chenh lech den tu quan tri hay tu thu khac.
    """
    from nhan import de_quan_tri as DQT
    p = Path(duong_ea)
    src = p.read_text(encoding="utf-8-sig", errors="ignore")
    khoi = dich(chi_so, khung=khung, in_ra=None)
    moi = DQT.chen(src, khoi, khung=khung)

    RA.mkdir(parents=True, exist_ok=True)
    goc = RA / ("%s_GOC.mq5" % p.stem)
    co = RA / ("%s_QT%d.mq5" % (p.stem, chi_so))
    goc.write_text(src, encoding="utf-8")
    co.write_text(moi, encoding="utf-8")

    thieu = DQT.kiem_da_chen(moi)
    ket = {"ea": p.name, "khai_bao": chi_so, "goc": str(goc), "co_quan_tri":
           str(co), "them_dong": len(moi.splitlines()) - len(src.splitlines()),
           "kiem": thieu}
    if in_ra:
        in_ra("GOC        %s" % goc)
        in_ra("CO QUAN TRI %s  (+%d dong)" % (co, ket["them_dong"]))
        if thieu:
            in_ra("  CANH BAO: %s" % "; ".join(map(str, thieu)))
        else:
            in_ra("  kiem chen: dat")
        in_ra("")
        in_ra("  Buoc sau: dua CA HAI file vao tester bang duong da co")
        in_ra("  (`chay_tester_kho.py`) roi so ket qua - file nay KHONG tu mo")
        in_ra("  terminal64.exe (mot ban la rang buoc vat ly).")
    return ket


def main(argv: list[str]) -> int:
    if "--dich-het" in argv:
        dich_het()
        return 0
    if "--dich" in argv:
        dich(int(argv[argv.index("--dich") + 1]))
        return 0
    if "--cap" in argv:
        i = 0
        if "--khai-bao" in argv:
            i = int(argv[argv.index("--khai-bao") + 1])
        k = cap_doi_chieu(argv[argv.index("--cap") + 1], i)
        print(json.dumps(k, ensure_ascii=False, indent=1))
        return 0
    kho()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
