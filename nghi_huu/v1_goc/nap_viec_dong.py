# -*- coding: utf-8 -*-
"""
nap_viec_dong.py - BO SINH VIEC, thay cho danh sach co dinh
=====================================================================================
Van de tim ra 09/08: `brain_vong_lap.nap_viec_mac_dinh()` gieo dung 25 viec roi thoi.
No chi nap lai KHI SANG NGAY, ma nap lai dung danh sach cu - trung id nen bi khu het.
Chay xong 25 viec la hang doi can VINH VIEN, trong khi ngoai kia con hang nam tai lieu.

File nay sinh viec TU TRANG THAI, khong tu danh sach:
  1. moi tai lieu CHUA AI DOC trong so NGUON/CONG NGHE  -> mot viec doc
  2. moi tu khoa arXiv                                   -> viec lay TRANG KE TIEP
  3. moi khang dinh chua tra loi trong so                -> mot viec sang
  4. tu khoa MOI rut ra tu tieu de cac bai da lay        -> viec lay nguon
  5. moi kho GitHub dang cho                             -> viec keo ve

Nho vay hang doi tu day len moi lan chay, va no het khi va chi khi khong con gi de doc.

  python nap_viec_dong.py            # sinh viec roi in ra
  python nap_viec_dong.py --xem      # chi xem se sinh gi, khong ghi
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
REPORTS = HERE / "reports"
HANG_DOI = REPORTS / "BRAIN_hang_doi.parquet"
DA_DOC = REPORTS / "ds" / "_da_doc_nguon.json"

COT = ["id", "loai", "muc_tieu", "tham_so", "uu_tien", "trang_thai",
       "lan_chay", "luc_cuoi", "ket_qua", "ghi_chu"]


def viec(loai, muc_tieu, tham_so=None, uu_tien=50, ghi_chu=""):
    return {"id": f"{loai}:{muc_tieu}:{json.dumps(tham_so or {}, sort_keys=True)}",
            "loai": loai, "muc_tieu": muc_tieu,
            "tham_so": json.dumps(tham_so or {}, ensure_ascii=False),
            "uu_tien": uu_tien, "trang_thai": "cho", "lan_chay": 0,
            "luc_cuoi": "", "ket_qua": "", "ghi_chu": ghi_chu}


def _doc(f):
    return pd.read_parquet(f) if Path(f).exists() else pd.DataFrame()


# --- 1. Tai lieu chua ai doc -------------------------------------------------

def viec_doc_tai_lieu():
    da = set()
    if DA_DOC.exists():
        try:
            da = set(json.loads(DA_DOC.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            pass
    ra = []
    for f in ("BRAIN_nguon.parquet", "BRAIN_cong_nghe.parquet"):
        d = _doc(REPORTS / f)
        for _, r in d.iterrows():
            khoa = f"{r.get('nguon','')}|{r.get('ten','')}"[:200]
            if khoa in da:
                continue
            ra.append(viec("doc_nguon", khoa[:90], {"nguon": str(r.get("nguon", ""))},
                           72, "rut khang dinh tu tai lieu"))
    return ra


# --- 2. Phan trang arXiv -----------------------------------------------------

def viec_them_trang():
    """Moi tu khoa da dung -> lay trang ke tiep. arXiv co hang nghin bai moi tu khoa,
    ta moi lay 15 dau tien roi khong bao gio quay lai."""
    d = _doc(REPORTS / "BRAIN_nguon.parquet")
    if d.empty:
        return []
    ra = []
    for tk, nhom in d[d["nguon"] == "arXiv"].groupby("tu_khoa"):
        da_co = len(nhom)
        # moi lan nhay them 25 bai
        ra.append(viec("nguon", "arxiv_them", {"tu_khoa": str(tk), "bo_qua": int(da_co)},
                       66, f"da co {da_co} bai voi tu khoa nay, lay tiep"))
    return ra


# --- 3. Khang dinh chua tra loi ---------------------------------------------

def viec_sang_khang_dinh():
    f = REPORTS / "BRAIN_khang_dinh.parquet"
    if not f.exists():
        return []
    d = pd.read_parquet(f)
    cho = d[d["trang_thai"].isin(["CHUA_TEST", "DANG_SANG"])]
    return [viec("sang", str(r["ma"]).lower(), {"tap": "sang"}, 58,
                 str(r.get("phat_bieu", ""))[:80]) for _, r in cho.iterrows()]


# --- 4. Tu khoa moi rut tu tieu de da lay ------------------------------------

DUNG = set("""the a an of and or for with from in on to by using via toward towards
new novel study analysis approach model models method methods based data evidence
we our this that these those is are be can do does how what why when which more
than into over under between during about across against among""".split())

DA_DUNG = {"overnight return", "intraday reversal", "return predictability",
           "cross-section of returns", "lead-lag effect", "seasonality in returns",
           "limits to arbitrage", "volatility risk premium", "market anomaly",
           "momentum", "mean reversion", "trading strategy"}


def viec_tu_khoa_moi(so=6):
    """Rut cum tu HAI CHU hay gap trong tieu de cac bai da lay, bo cum da dung.
    Day la cach de tu khoa TU LON LEN thay vi dung yen o chin cai ban dau."""
    d = _doc(REPORTS / "BRAIN_nguon.parquet")
    if d.empty:
        return []
    dem = Counter()
    for t in d["ten"].astype(str):
        tu = [w for w in re.findall(r"[a-z]+", t.lower()) if len(w) > 3 and w not in DUNG]
        for a, b in zip(tu, tu[1:]):
            dem[f"{a} {b}"] += 1
    moi = [(c, n) for c, n in dem.most_common(60)
           if n >= 3 and c not in DA_DUNG
           and not any(x in c for x in ("momentum", "mean revers", "trading strat"))]
    return [viec("nguon", "arxiv_tu_khoa_moi", {"tu_khoa": c}, 62,
                 f"rut tu tieu de, xuat hien {n} lan") for c, n in moi[:so]]


# --- 5. Kho GitHub dang cho ---------------------------------------------------

KHO_CHO = [
    ("QuantConnect/Lean", ["Algorithm.CSharp/"], [".cs"], "hang tram thuat toan mau C#"),
    ("jesse-ai/jesse", ["strategies"], [".py"], "khung crypto, chien luoc mau"),
    ("robcarver17/pysystemtrade", ["systems", "examples"], [".py"], "he thong CTA cua Rob Carver"),
    ("polakowo/vectorbt", ["examples"], [".py"], "vi du chien luoc vector hoa"),
    ("hudson-and-thames/mlfinlab", [""], [".py"], "ky thuat tu sach Lopez de Prado"),
]


def viec_kho_moi():
    ra = []
    for repo, loc, duoi, mo in KHO_CHO:
        thu_muc = HERE / "nap_tay" / repo.replace("/", "__")
        if thu_muc.exists():
            continue
        ra.append(viec("keo_kho", repo, {"loc": loc, "duoi": duoi}, 68, mo))
    return ra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xem", action="store_true")
    a = ap.parse_args()

    nhom = {
        "doc tai lieu chua ai doc": viec_doc_tai_lieu(),
        "lay them trang arXiv": viec_them_trang(),
        "sang khang dinh chua tra loi": viec_sang_khang_dinh(),
        "tu khoa moi rut tu tieu de": viec_tu_khoa_moi(),
        "keo kho GitHub moi": viec_kho_moi(),
    }

    cu = _doc(HANG_DOI)
    da_co = set(cu["id"]) if len(cu) else set()
    tat_ca, moi = [], 0
    for ten, ds in nhom.items():
        n = sum(1 for v in ds if v["id"] not in da_co)
        print(f"  {ten:<34} sinh {len(ds):>4}  |  moi {n:>4}")
        tat_ca += ds
        moi += n
        if ten == "tu khoa moi rut tu tieu de":
            for v in ds:
                print(f"       + {json.loads(v['tham_so']).get('tu_khoa')}  ({v['ghi_chu']})")

    if a.xem:
        print(f"\n(chi xem) tong {moi} viec moi")
        return

    them = pd.DataFrame([v for v in tat_ca if v["id"] not in da_co])
    if them.empty:
        print("\nkhong co viec moi")
        return
    gop = pd.concat([cu, them], ignore_index=True) if len(cu) else them
    gop = gop.drop_duplicates(subset=["id"], keep="first").reset_index(drop=True)
    gop.to_parquet(HANG_DOI, index=False)
    print(f"\nThem {moi} viec. Hang doi: {len(gop)} tong, "
          f"{int((gop['trang_thai'] == 'cho').sum())} dang cho.")


if __name__ == "__main__":
    main()
