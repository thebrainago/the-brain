# -*- coding: utf-8 -*-
"""quet_loi_ra.py - MOT TIN HIEU CHUA PHAI MOT CHIEN LUOC.

## VAN DE (do tren kho 06/09/2026)

`config/co_che_dsl.json` giu 540 co che. Trong do:

    khong co dieu kien RA        447 / 540
    rut tu file .mq5, khong RA   225
    trong 225 do, `giu` = 1      218

218 co che dang duoc kiem dinh voi DUNG MOT loi ra: *giu mot nen roi thoat*.
Khong ai chon con so 1 do ca - no la mac dinh cua `sinh_tu_spec` khi ban goc
khong noi gi ve loi ra. Ma ban goc **khong the** noi gi: 190/389 file ma la
CHI BAO, chung ve mui ten len bieu do va khong dat lenh, nen khong co lenh nao
de doc thoi diem thoat.

Nen "co che X am tinh" trong so cai hien khong phan biet duoc hai dieu:
  (a) tin hieu X khong co gia tri, va
  (b) tin hieu X co gia tri o chan troi 5 nen, va ta chi tung do no o 1 nen.
Dung hinh dang loi [[ket-luan-am-phai-phan-biet-chua-do]].

## CACH LAM: DO TRUOC, THEM VAO KHO SAU

Khong nhoi 5 bien the cua moi co che vao kho roi de pheu tu loc - lam vay la
nhan be mat len 5 lan de doi lay phan lon la ban sao suy bien, va chinh ban
giao 05/09 da ket luan "them co che khong lam tang so phat hien".

O day chi DO: moi co che chi-co-duong-vao duoc chay lai o 5 chan troi giu
(1/3/5/10/20 nen) tren toan bo tai san CO CHI PHI DO DUOC, va ta doc ra chan
troi nao lam no song. Chi (co che, giu) nao thang ban goc moi dang duoc de
xuat vao kho.

## HAI CHAN TROI DAC BIET

`ra_nguoc`: nhieu file .mq5 cho ca hai chieu (mua va ban). Cap do la loi ra TU
NHIEN nhat cua mot chi bao mui ten - "giu cho toi khi co mui ten nguoc" - va
no khong dien duoc bang `giu` vi do khong phai so nen co dinh. Bien the nay
lay `vao` cua ban doi lam `ra`.

## TAI SAN: CHI CAI DO DUOC CHI PHI

75/126 chuoi D1 co `do_tin` DO/SAN sau khi do spread hang loat (06/09). Quet
ho loi ra tren chuoi KHAI la lang phi: dieu 7 cua cong khong bao gio cho chung
PASS, nen mot chan troi "thang" o do khong doi thanh tien duoc.

Chay:
    python quet_loi_ra.py                 # 225 co che .mq5, D1, tai san do duoc
    python quet_loi_ra.py --het           # ca 447 co che khong co RA
    python quet_loi_ra.py --khung H4
"""
from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

LAB = Path(__file__).resolve().parent

#: Chan troi giu (so nen). 20 la tran: xa hon nua thi mot tin hieu vao bat ky
#: cung thanh "mua va giu tra hinh" tren chuoi co drift, va V2 se loai vi ly do
#: do chu khong vi tin hieu.
HO_GIU = (1, 3, 5, 10, 20)
SO_TIEN_TRINH = 8


# ------------------------------------------------------------- CHON CO CHE
def cac_ban_doi(kho: list[dict]) -> dict:
    """`ten` -> spec CHIEU NGUOC cung nguon. Chi nhan khi nguon la MOT file/URL
    cu the va o do dung mot cap doi xung - hai chieu, moi chieu mot ban."""
    theo_nguon = defaultdict(list)
    for c in kho:
        n = str(c.get("nguon") or "")
        if n:
            theo_nguon[n].append(c)
    ra = {}
    for ds in theo_nguon.values():
        mua = [c for c in ds if int(c.get("chieu", 1) or 1) > 0]
        ban = [c for c in ds if int(c.get("chieu", 1) or 1) < 0]
        if len(mua) == 1 and len(ban) == 1:
            ra[mua[0]["ten"]] = ban[0]
            ra[ban[0]["ten"]] = mua[0]
    return ra


def chon(kho: list[dict], het: bool = False) -> list[dict]:
    ds = [c for c in kho if not (c.get("ra") or [])]
    if not het:
        ds = [c for c in ds if str(c.get("nguon") or "").endswith(".mq5")]
    return ds


def bien_the(spec: dict, ban_doi: dict | None) -> list[tuple[str, dict]]:
    """Mot co che -> ho loi ra cua no. Ten bien the mang HAU TO doc duoc."""
    goc = int(spec.get("giu", 1) or 1)
    ra = []
    for g in HO_GIU:
        ra.append((spec["ten"] + "@giu%d" % g, dict(spec, giu=g)))
    if goc not in HO_GIU:
        ra.append((spec["ten"] + "@giu%d" % goc, dict(spec, giu=goc)))
    if ban_doi and (ban_doi.get("vao") or []):
        ra.append((spec["ten"] + "@ra_nguoc",
                   dict(spec, giu=1, ra=list(ban_doi["vao"]))))
    return ra


# --------------------------------------------------------------- CHAY MOT O
def _mot_bien_the(doi_so):
    """Mot bien the x moi tai san. Ham muc GOC de Pool pickle duoc."""
    ten, spec, khung, cac_ma = doi_so
    import sys as _s
    from pathlib import Path as _P
    _s.path.insert(0, str(_P(__file__).resolve().parent))
    from nhan import mau as MAU
    from nhan import ngu_phap as NP
    from nhan import sang_loc as SL

    # Dang ky bien the vao thu vien mau CUA TIEN TRINH CON. Di dung duong ma
    # `nap_vao_mau` di, khong co duong tat: cung closure, cung `ho`, nen V3
    # phan chung va bang chi phi ap y het co che that.
    def _ham(df, _s=spec, **ts):
        return NP.sinh_tu_spec(NP.ap_tham_so(_s, ts) if ts else _s, df)

    MAU.MAU[ten] = {"ham": _ham, "ho": spec.get("ho", "khac"),
                    "co_che": spec.get("co_che", ""), "luoi": [{}], "dsl": True}

    SL.xoa_bo_dem()
    try:
        pv = SL.pham_vi_cua(ten)
    except Exception as e:
        pv = {"ket_luan": "LOI", "ly_do": "%s: %s" % (type(e).__name__, str(e)[:60])}
    o = {}
    for ma in cac_ma:
        try:
            r = SL.chay_pheu(ten, {}, ma, khung, pham_vi=pv, da_chay=None)
        except Exception as e:
            r = {"ket_luan": "LOI", "vong": "?",
                 "ly_do": "%s: %s" % (type(e).__name__, str(e)[:60]), "do": {}}
        d = r.get("do") or {}
        o[ma] = {"ket_luan": r.get("ket_luan"), "vong": r.get("vong"),
                 "ly_do": str(r.get("ly_do"))[:80], "sharpe": d.get("sharpe"),
                 "sharpe_mua_giu": d.get("sharpe_mua_giu"),
                 "so_lenh": d.get("so_lenh")}
    return {"bien_the": ten, "goc": spec["ten"], "giu": spec.get("giu", 1),
            "co_ra": bool(spec.get("ra")), "o": o}


def tai_san_do_duoc(khung: str) -> list[str]:
    """Chuoi co `do_tin` DO/SAN. Xem docstring dau file."""
    from nhan import chi_phi as CP
    from nhan import du_lieu as DL
    from nhan import pham_vi as PV
    ra = []
    for ma in PV.kho_du_bar(khung):
        try:
            if CP.tu_du_lieu(ma, DL.nap(ma, khung)).do_tin in ("DO", "SAN"):
                ra.append(ma)
        except Exception:
            continue
    return ra


def quet(khung: str = "D1", het: bool = False,
         so_tien_trinh: int = SO_TIEN_TRINH, gioi_han: int = 0) -> dict:
    from nhan import ngu_phap as NP
    t0 = time.time()
    kho = NP.doc_kho()
    doi = cac_ban_doi(kho)
    goc = chon(kho, het)
    if gioi_han:
        goc = goc[:gioi_han]
    cac_ma = tai_san_do_duoc(khung)

    viec = []
    for spec in goc:
        for ten, s in bien_the(spec, doi.get(spec["ten"])):
            viec.append((ten, s, khung, cac_ma))
    print("%d co che -> %d bien the x %d tai san = %d o"
          % (len(goc), len(viec), len(cac_ma), len(viec) * len(cac_ma)),
          flush=True)

    ket = []
    if so_tien_trinh <= 1:
        for v in viec:
            ket.append(_mot_bien_the(v))
    else:
        import multiprocessing as mp
        with mp.Pool(min(so_tien_trinh, len(viec))) as pool:
            for i, r in enumerate(pool.imap_unordered(_mot_bien_the, viec), 1):
                ket.append(r)
                if i % 50 == 0:
                    print("[%s] %d/%d" % (time.strftime("%H:%M:%S"), i, len(viec)),
                          flush=True)
    return {"khung": khung, "so_co_che": len(goc), "so_bien_the": len(viec),
            "ma": cac_ma, "ket": ket, "giay": round(time.time() - t0, 1)}


# ----------------------------------------------------------------- BAO CAO
SONG = ("NEN_GOP", "SAN_SANG_V4")


def _diem(r: dict) -> tuple:
    """(so o song, sharpe cao nhat). Dem o SONG truoc: mot sharpe cao tren mot
    tai san la ngau nhien, con song tren nhieu tai san moi la hinh dang."""
    song = sum(1 for v in r["o"].values() if v["ket_luan"] in SONG)
    sh = [v["sharpe"] for v in r["o"].values()
          if v["ket_luan"] in SONG and v["sharpe"] is not None]
    return song, (round(max(sh), 3) if sh else 0.0)


def tong_hop(ra: dict) -> dict:
    theo_goc = defaultdict(list)
    for r in ra["ket"]:
        theo_goc[r["goc"]].append(r)

    bang, doi_chan_troi, dem_giu = [], 0, defaultdict(int)
    for goc, ds in theo_goc.items():
        cham = sorted(ds, key=lambda r: (-_diem(r)[0], -_diem(r)[1]))
        tot = cham[0]
        nen1 = next((r for r in ds if r["giu"] == 1 and not r["co_ra"]), None)
        d_tot = _diem(tot)
        d_nen1 = _diem(nen1) if nen1 else (0, 0.0)
        if tot["bien_the"] != (nen1 or {}).get("bien_the") and d_tot[0] > d_nen1[0]:
            doi_chan_troi += 1
        dem_giu["ra_nguoc" if tot["co_ra"] else "giu%d" % tot["giu"]] += 1
        bang.append({"co_che": goc, "tot_nhat": tot["bien_the"],
                     "o_song": d_tot[0], "sharpe": d_tot[1],
                     "o_song_giu1": d_nen1[0], "sharpe_giu1": d_nen1[1]})
    bang.sort(key=lambda x: (-x["o_song"], -x["sharpe"]))
    return {"bang": bang, "doi_chan_troi": doi_chan_troi,
            "chan_troi_thang": dict(sorted(dem_giu.items(),
                                           key=lambda kv: -kv[1]))}


def main() -> int:
    khung = "D1"
    if "--khung" in sys.argv:
        khung = sys.argv[sys.argv.index("--khung") + 1]
    n = SO_TIEN_TRINH
    if "--tien-trinh" in sys.argv:
        n = int(sys.argv[sys.argv.index("--tien-trinh") + 1])
    gh = 0
    if "--gioi-han" in sys.argv:
        gh = int(sys.argv[sys.argv.index("--gioi-han") + 1])

    ra = quet(khung, het="--het" in sys.argv, so_tien_trinh=n, gioi_han=gh)
    ra["tong_hop"] = tong_hop(ra)
    f = LAB / "reports" / ("LOI_RA_%s.json" % khung)
    f.write_text(json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")

    th = ra["tong_hop"]
    print("\n%d co che, %d bien the, %ss"
          % (ra["so_co_che"], ra["so_bien_the"], ra["giay"]))
    print("chan troi thang:", th["chan_troi_thang"])
    print("doi chan troi lam SONG THEM: %d co che" % th["doi_chan_troi"])
    print("\n%-40s %-16s %4s %7s %7s"
          % ("co che", "tot nhat", "o", "sharpe", "(giu1)"))
    for d in th["bang"][:25]:
        hau = d["tot_nhat"].split("@")[-1]
        print("%-40s %-16s %4d %7.3f %7d"
              % (d["co_che"][:40], hau, d["o_song"], d["sharpe"],
                 d["o_song_giu1"]))
    print("\n-> %s" % f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
