# -*- coding: utf-8 -*-
"""luan_dau_chan.py - 400 HO SO SIGNAL -> KIEU CHIEN LUOC. Noi hai manh mo coi.

## Dong so do nay phuc vu

    "Tim kiem cac trader cac he thong giao dich co lich su giao dich nhu mql5
     signal, cac bang xep hang, cac quy, myfxbook,..."
    "Tu chien luoc co lich su se suy nguoc de tim ra phuong phap trade"

Hai module lam viec do deu MO COI cho toi 12/09/2026 (ban do sinh tu ma nguon):

    nhan/tin_hieu_mql5.py   tai + boc ho so tu trang signal
    nhan/dau_chan.py        dac trung -> KIEU chien luoc + thuoc do rieng tung kieu

Va `reports/signal_ho_so.json` da co **400 ho so boc san** nam do tu truoc.
Ba manh nam canh nhau ma khong ai noi - dung hinh dang luat L7.

## VI SAO PHAN LOAI TRUOC KHI CHAM

`dau_chan` khong cham Sharpe, va do la chu y. Mot he luoi/DCA co hinh dang loi
suat khac han mot he xu huong: ty le thang cao, lai nho, thua hiem va rat lon.
Voi hinh dang do, Sharpe khong phai thuoc do dung - cau hoi dung la **song bao
lau** va **rut kip khong**. Nen phai biet no thuoc KIEU nao truoc da.

Ket qua da co that tu duong nay: luan nguoc 400 signal ra **AUDCAD** (13/19 tai
khoan DCA song >= 2 nam, nen 28%, p = 0,00035) - xem [[luan-nguoc-400-signal-audcad]].

## KHONG TAI GI O DAY

File nay doc ho so DA BOC. Khau tai/boc la viec cua `tin_hieu_mql5` va no can
mang; tach ra de phan phan tich chay duoc ca khi khong co mang.

Chay:  python -m nhan.luan_dau_chan
       python -m nhan.luan_dau_chan --kieu luoi_dca
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

HO_SO = LAB / "reports" / "signal_ho_so.json"
SO = LAB / "reports" / "LUAN_DAU_CHAN.json"


def doc_ho_so() -> list[dict]:
    try:
        d = json.loads(HO_SO.read_text(encoding="utf-8"))
    except Exception:
        return []
    return d if isinstance(d, list) else list(d.values())


def phan_loai_het(in_ra=print) -> dict:
    """400 ho so -> kieu chien luoc, kem BANG TAI SAN theo tung kieu."""
    from nhan import dau_chan as DC
    ds = doc_ho_so()
    if not ds:
        return {"bo": "chua co %s" % HO_SO.name}

    ra = []
    for h in ds:
        if not isinstance(h, dict):
            continue
        kieu, ly_do = DC.phan_loai(h)
        ra.append({"id": h.get("id"), "ten": str(h.get("ten"))[:40],
                   "kieu": kieu, "ly_do": ly_do,
                   "symbol": h.get("symbol") or [],
                   "song_ngay": h.get("song_ngay"), "dd_pct": h.get("dd_pct"),
                   "tang_truong_pct": h.get("tang_truong_pct"),
                   "so_lenh": h.get("so_lenh")})

    dem = Counter(x["kieu"] for x in ra)
    in_ra("LUAN NGUOC %d HO SO SIGNAL -> KIEU CHIEN LUOC" % len(ra))
    in_ra("")
    for kieu, n in dem.most_common():
        in_ra("  %-10s %4d  (%.0f%%)" % (kieu, n, 100.0 * n / len(ra)))
    if dem.get("khong_ro"):
        in_ra("")
        in_ra("  `khong_ro` KHONG phai 'khong co kieu' - la THIEU DAC TRUNG de")
        in_ra("  phan. Dem no vao mau so cua bat ky ty le nao la sai.")

    # Tai san theo tung kieu - day moi la thu hanh dong duoc: kieu nao song
    # tren tai san nao.
    in_ra("")
    for kieu in [k for k, _ in dem.most_common() if k != "khong_ro"]:
        cac = [x for x in ra if x["kieu"] == kieu]
        sym = Counter(s for x in cac for s in (x["symbol"] or [])
                      if isinstance(s, str))
        if not sym:
            continue
        in_ra("  %-10s tai san hay gap: %s" % (
            kieu, ", ".join("%s %d" % kv for kv in sym.most_common(6))))
    SO.parent.mkdir(exist_ok=True)
    SO.write_text(json.dumps({"dem": dict(dem), "bang": ra},
                             ensure_ascii=False, indent=1, default=str),
                  encoding="utf-8")
    return {"so": len(ra), "dem": dict(dem)}


def theo_kieu(kieu: str = "luoi_dca", tran: int = 20, in_ra=print) -> dict:
    """Cac tai khoan thuoc mot kieu, xep theo SONG BAO LAU.

    Thuoc do co y: voi lop luoi/DCA thi Sharpe khong noi len dieu gi, cau hoi
    la no song duoc bao lau truoc khi gap cu lam no chet.
    """
    from nhan import dau_chan as DC
    ds = [h for h in doc_ho_so() if isinstance(h, dict)]
    cac = [h for h in ds if DC.phan_loai(h)[0] == kieu]
    cac.sort(key=lambda h: -(h.get("song_ngay") or 0))
    in_ra("KIEU `%s`: %d/%d tai khoan" % (kieu, len(cac), len(ds)))
    in_ra("")
    in_ra("  %-26s %7s %7s %8s %8s  %s"
          % ("ten", "song(ng)", "dd%", "tang%", "so lenh", "symbol"))
    for h in cac[:tran]:
        in_ra("  %-26s %7s %7s %8s %8s  %s"
              % (str(h.get("ten"))[:26], h.get("song_ngay"), h.get("dd_pct"),
                 h.get("tang_truong_pct"), h.get("so_lenh"),
                 ",".join((h.get("symbol") or [])[:3])))
    return {"kieu": kieu, "so": len(cac)}


def lam_moi(cac_id=None, in_ra=print) -> dict:
    """Tai lai ho so tu trang signal (`tin_hieu_mql5`). CAN MANG.

    Tach khoi `phan_loai_het` co y: khau phan tich phai chay duoc ca khi khong
    co mang, con khau tai thi khong. Gop hai lai thi mot lan mat mang se lam
    ca duong luan nguoc im lang - dung benh `duong-llm-tat-lang-le`.
    """
    from nhan import tin_hieu_mql5 as TM
    ds = doc_ho_so()
    ids = list(cac_id or [h.get("id") for h in ds if isinstance(h, dict)])
    if not ids:
        return {"bo": "khong co id nao de lam moi"}
    ok, hong = 0, []
    for sid in ids:
        try:
            TM.rui_ro_json(int(sid))
            ok += 1
        except Exception as e:
            hong.append("%s: %s" % (sid, str(e)[:50]))
    in_ra("lam moi %d/%d ho so" % (ok, len(ids)))
    if hong:
        in_ra("  %d ho so khong tai duoc (mang? trang doi?):" % len(hong))
        for h in hong[:5]:
            in_ra("    %s" % h)
    return {"tong": len(ids), "ok": ok, "hong": len(hong)}


def main(argv: list[str]) -> int:
    if "--lam-moi" in argv:
        lam_moi()
        return 0
    if "--kieu" in argv:
        theo_kieu(argv[argv.index("--kieu") + 1])
    else:
        phan_loai_het()
        print("-> %s" % SO)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
