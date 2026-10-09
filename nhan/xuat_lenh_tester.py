# -*- coding: utf-8 -*-
"""xuat_lenh_tester.py - dua BANG LENH CUA TESTER (su that MT5) len git de cloud so TUNG LENH voi engine (chu du an duyet 09/10/2026).

Vi sao: `hieu_chuan_luoi` luu moi o tester thanh `reports/hieu_chuan/<khoa16>_lenh.csv.gz` o MAY NHA va file do khong vao git.
Cloud (Linux) chi thay cac con so tong (lai / DD / so lenh) nen biet engine LECH nhung khong biet lech o LENH nao (gia vao, gia ra,
gio, lot, vi sao dong). Co bang lenh nay + gia M1 (`b xuat-gia MA M1 --tu .. --den ..`) cloud chay lai engine tren Linux voi nhieu
phuong an mo phong va so TUNG LENH voi MT5 that - ma khong can may nha ban tester them lan nao.

`b xuat-lenh` (chay o MAY NHA; khong tham so):
  1. Doc moi `reports/hieu_chuan/<16 hex>_lenh.csv.gz` o lab. Hong / thieu cot / thoi gian sai -> bo qua, GHI LY DO (khong chet ca lo).
  2. Ghi `<hop thu>/du_lieu_gia/mau_tester/<khoa16>_lenh.csv.gz` (gzip CO DINH: cung noi dung ra cung byte) + `MANIFEST.json`
     (so lenh, ngay dau/cuoi, tong lai, sha256). Hop thu: bo chay chi `git add` duong trong `DUOC_DAY` CUA HOP THU (xem `xuat_gia`).
  3. Khong co bang nao -> FileNotFoundError (khong "thanh cong" rong). Vuot tran dung luong -> ValueError va KHONG ghi gi
     (repo PUBLIC).

Day la bang lenh cua CHINH EA luoi cua ta (`ea_LuoiDayDu.mq5`) chay tren tester MT5 cua ta - khong phai bot cua nguoi khac.
Ghep o-thi-nghiem voi bang lenh: bao cao `reports/hieu_chuan/*.json` (da o git) ghi `tester.bang_lenh` = duong dan toi tung file.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import re
import sys
import zlib
from pathlib import Path

import pandas as pd

from nhan import xuat_gia as XG

GOC = Path(__file__).resolve().parent.parent
THU_NGUON = GOC / "reports" / "hieu_chuan"

#: Mot o ~ 100-1000 lenh x ~30 byte nen xa tran nay; vuot = file khong phai bang lenh (hoac tester dien).
TRAN_BYTE_MOI_FILE = 3_000_000
TRAN_BYTE_MOI_LENH = 12_000_000

COT_BAT_BUOC = ("mo", "dong", "chieu", "lot", "gia_mo", "gia_dong", "lai")
_TEN = re.compile(r"^([0-9a-f]{16})_lenh\.csv\.gz$")


def thu_muc_mac_dinh() -> Path:
    """`<hop thu>/du_lieu_gia/mau_tester` (cung cho voi file gia, de bo chay day len git)."""
    return XG.thu_muc_mac_dinh() / "mau_tester"


def doc_van_ban(p: Path) -> str:
    """Giai nen mot bang lenh thanh van ban CSV. File gz hong -> OSError / EOFError (nguoi goi bao ly do)."""
    with gzip.open(p, "rb") as fh:
        return fh.read().decode("utf-8")


def kiem_bang(van_ban: str) -> dict:
    """Doc thu bang lenh va tra `{so_lenh, mo_dau, mo_cuoi, lai_tong, swap_tong}`. Thieu cot / thoi gian khong doc duoc / so khong
    phai so -> ValueError (de bo qua ro ly do, khong dua file rac len repo public). Bang rong (0 lenh) la HOP LE: tester khong vao lenh."""
    df = pd.read_csv(io.StringIO(van_ban))
    thieu = [c for c in COT_BAT_BUOC if c not in df.columns]
    if thieu:
        raise ValueError("thieu cot %s (co %s)" % (thieu, list(df.columns)))
    if not len(df):
        return {"so_lenh": 0, "mo_dau": None, "mo_cuoi": None, "lai_tong": 0.0, "swap_tong": 0.0}
    mo = pd.to_datetime(df["mo"], errors="coerce")
    if mo.isna().any():
        raise ValueError("cot mo co %d gia tri khong phai thoi gian" % int(mo.isna().sum()))
    for c in ("chieu", "lot", "gia_mo", "gia_dong", "lai"):
        v = pd.to_numeric(df[c], errors="coerce")
        if c == "gia_dong":
            v = v[df["dong"].notna()]                         # lenh con treo cuoi ky co the chua co gia dong
        if v.isna().any():
            raise ValueError("cot %s co %d gia tri khong phai so" % (c, int(v.isna().sum())))
    sw = pd.to_numeric(df["swap"], errors="coerce").fillna(0.0) if "swap" in df.columns else pd.Series([0.0])
    return {"so_lenh": int(len(df)), "mo_dau": str(mo.min()), "mo_cuoi": str(mo.max()),
            "lai_tong": round(float(pd.to_numeric(df["lai"], errors="coerce").sum()), 4), "swap_tong": round(float(sw.sum()), 4)}


def _gz_co_dinh(van_ban: str) -> bytes:
    bo = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=bo, compresslevel=9, mtime=0) as gz:
        gz.write(van_ban.encode("utf-8"))
    return bo.getvalue()


def chay(nguon: Path | None = None, thu_muc: Path | None = None,
         tran_file: int = TRAN_BYTE_MOI_FILE, tran_lenh: int = TRAN_BYTE_MOI_LENH) -> dict:
    """Xuat het bang lenh o `nguon` (mac dinh `reports/hieu_chuan` cua lab). Tra `{"da_xuat": {khoa: dong manifest}, "bo_qua": {ten: ly do},
    "byte": tong}`. TAT CA HOAC KHONG: tong vuot `tran_lenh` thi raise truoc khi ghi bat ky file nao."""
    nguon = Path(nguon) if nguon else THU_NGUON
    thu_muc = Path(thu_muc) if thu_muc else thu_muc_mac_dinh()
    cac = sorted(p for p in nguon.glob("*_lenh.csv.gz") if _TEN.match(p.name)) if nguon.is_dir() else []
    if not cac:
        raise FileNotFoundError("khong co bang lenh tester nao (<16 hex>_lenh.csv.gz) o %s" % nguon)
    cho_ghi, bo_qua, tong = {}, {}, 0
    for p in cac:
        khoa = _TEN.match(p.name).group(1)
        try:
            vb = doc_van_ban(p)
            kq = kiem_bang(vb)
        except (OSError, EOFError, ValueError, zlib.error) as e:        # ValueError gom loi UTF-8 va loi doc CSV cua pandas
            bo_qua[p.name] = ("%s: %s" % (type(e).__name__, e))[:200]
            continue
        gz = _gz_co_dinh(vb)
        if len(gz) > tran_file:
            bo_qua[p.name] = "%.1f MB vuot tran %.1f MB moi file" % (len(gz) / 1e6, tran_file / 1e6)
            continue
        tong += len(gz)
        dong = dict(kq, tep=p.name, byte=len(gz), sha256=hashlib.sha256(gz).hexdigest()[:16])
        cho_ghi[khoa] = (gz, dong)
    if tong > tran_lenh:
        raise ValueError("tong %.1f MB vuot tran %.1f MB moi lenh - KHONG ghi gi (repo la public)" % (tong / 1e6, tran_lenh / 1e6))
    if not cho_ghi:
        raise ValueError("%d file o %s nhung khong file nao dung dinh dang: %s" % (len(cac), nguon, json.dumps(bo_qua, ensure_ascii=False)[:600]))
    thu_muc.mkdir(parents=True, exist_ok=True)
    for khoa, (gz, dong) in cho_ghi.items():
        dich = thu_muc / dong["tep"]
        if dich.exists() and dich.read_bytes() == gz:
            continue                                          # cung noi dung: khong ghi lai (khong them mot ban sao vao lich su git)
        tam = dich.with_name(dich.name + ".tam")              # `du_lieu_gia/**/*.tam` nam trong .gitignore
        try:
            tam.write_bytes(gz)
            os.replace(tam, dich)
        finally:
            if tam.exists():
                tam.unlink()
    _ghi_so_khai(thu_muc, {k: v[1] for k, v in cho_ghi.items()})
    return {"da_xuat": {k: v[1] for k, v in cho_ghi.items()}, "bo_qua": bo_qua, "byte": tong}


def _ghi_so_khai(thu_muc: Path, dong: dict) -> None:
    """Gop cac dong vao `MANIFEST.json` (thay nguyen tu; dong cu cua khoa khac duoc giu)."""
    p = Path(thu_muc) / "MANIFEST.json"
    cu = json.loads(p.read_text("utf-8")) if p.exists() else {}
    cu.update(dong)
    tam = p.with_name(p.name + ".tam")
    tam.write_text(json.dumps(cu, ensure_ascii=False, indent=1, sort_keys=True), "utf-8")
    os.replace(tam, p)


def doc(khoa: str, thu_muc: Path | None = None) -> pd.DataFrame:
    """Doc lai MOT bang lenh da xuat (cot mo / dong thanh thoi gian)."""
    f = (Path(thu_muc) if thu_muc else thu_muc_mac_dinh()) / ("%s_lenh.csv.gz" % khoa[:16])
    return pd.read_csv(f, parse_dates=["mo", "dong"])


def main_cli(a: list[str] | None = None) -> None:
    a = list(sys.argv[1:] if a is None else a)
    co_gia_tri = ("--nguon", "--thu-muc")
    for i, x in enumerate(a):
        if x.startswith("--") and x not in co_gia_tri:
            sys.exit(__doc__)
        if x in co_gia_tri and i + 1 >= len(a):
            sys.exit("%s can mot gia tri\n\n%s" % (x, __doc__))
    nguon = Path(a[a.index("--nguon") + 1]) if "--nguon" in a else None
    th = Path(a[a.index("--thu-muc") + 1]) if "--thu-muc" in a else None
    kq = chay(nguon, th)
    n_lenh = sum(v["so_lenh"] for v in kq["da_xuat"].values())
    print("xuat %d bang lenh tester (%d lenh, %.2f MB) -> %s ; bo qua %d"
          % (len(kq["da_xuat"]), n_lenh, kq["byte"] / 1e6, th or thu_muc_mac_dinh(), len(kq["bo_qua"])))
    for ten, ly in list(kq["bo_qua"].items())[:20]:
        print("  bo qua %s: %s" % (ten, ly))


if __name__ == "__main__":
    main_cli()
