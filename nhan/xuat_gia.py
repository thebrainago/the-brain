# -*- coding: utf-8 -*-
"""xuat_gia.py - XUAT gia cua vai cap ra file nho de cloud chay duoc `quet_luoi` (chu du an duyet 05/10/2026).

`b xuat-gia AUDCAD,NZDCAD M15 [--thu-muc DIR] [--tu NAM|NGAY] [--den NAM|NGAY]` (chay o MAY NHA, noi co `data/`):
  1. `du_lieu.nap(ma, khung)` -> OHLC + tick_volume + spread, gio nhu trong kho (gio may chu MT5 gan nhan UTC).
  2. Ghi `<thu-muc>/<MA>_<KHUNG>.csv.gz` (khong cua so) hoac `<MA>_<KHUNG>_<tu>_<den>.csv.gz` (co cua so, tu / den dang YYYYMMDD)
     + `MANIFEST.json` (so bar, tu-den, sha256).
  3. SAO LUU truoc: moi file cung duoc chep vao `../sao_luu_gia/<ngay>/` (NGOAI git) de neu phai go khoi repo
     (ban quyen nha moi gioi) thi con ban goc. Chi du lieu gia cua vai cap; KHONG tick, KHONG thong tin tai khoan.

`--tu 2018` = tu 2018-01-01 ; `--tu 2018-07-01` = tu ngay do ; `--den 2018-12-31` = DEN HET ngay do (gom ca ngay) ; `--den 2018` = den het 31/12/2018.

## NOI GHI MAC DINH = HOP THU CUA BO CHAY (sua 09/10/2026)
May nha chay bo chay voi HOP THU RIENG (`b cau cai`); bo chay chi `git add` cac duong trong `DUOC_DAY` CUA HOP THU. File xuat vao
`lab/du_lieu_gia/` thi nam lai may nha va cloud khong bao gio thay (don `xuat-gia-4-cap-M15` 05/10 se chet theo cach do, khong ai bao loi).
Nen mac dinh ghi vao `<hop thu>/du_lieu_gia/` neu co hop thu rieng; khong co (che do in-place) thi `lab/du_lieu_gia/`.

## TRAN DUNG LUONG (repo PUBLIC, mot file lo tay se o lai lich su git mai mai)
Moi file toi da `TRAN_BYTE_MOI_FILE`, moi lenh toi da `TRAN_BYTE_MOI_LENH`; vuot thi KHONG ghi (ValueError, file tam bi bo).
Muon nhieu hon thi chia cua so nho hon (vd mot nam M1 / mot cap ~ 4 MB).

`doc(ma, khung, thu_muc, tu=None, den=None)` doc lai MOT file (cot open high low close tick_volume spread, index thoi gian);
`doc_het(ma, khung, thu_muc, tu, den)` GHEP moi file cua cap do (cac cua so lien nhau) roi cat theo [tu, den].
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import pandas as pd

GOC = Path(__file__).resolve().parent.parent
MAC_DINH = GOC / "du_lieu_gia"
COT = ["open", "high", "low", "close", "tick_volume", "spread"]

#: Tran dung luong (byte). M1 ~ 11 byte / bar nen 12 MB ~ 1,05 trieu bar ~ 2,8 nam M1 mot cap.
TRAN_BYTE_MOI_FILE = 12_000_000
TRAN_BYTE_MOI_LENH = 40_000_000

_NGAY = re.compile(r"^(\d{4})(?:-(\d{2})-(\d{2}))?$")


def thu_muc_mac_dinh() -> Path:
    """Noi DAY DUOC LEN GIT: `<hop thu rieng>/du_lieu_gia` neu may da `b cau cai`, khong thi `lab/du_lieu_gia`.
    Khong doc duoc cau hinh cau noi (vd chay ngoai he) -> `MAC_DINH`."""
    try:
        from qwen import cau_git as CG
        return Path(CG.MAILBOX) / "du_lieu_gia"
    except Exception:                                   # noqa: BLE001
        return MAC_DINH


def _ghi_gz(dich: Path, van_ban: str) -> None:
    """Ghi gzip CO DINH: khong ten goc, khong mtime -> cung du lieu ra cung byte (xuat lai khong them mot ban sao vao lich su git)."""
    with open(dich, "wb") as fh:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fh, compresslevel=9, mtime=0) as gz:
            gz.write(van_ban.encode("utf-8"))


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def doc_ngay(s: str | None, cuoi: bool = False) -> pd.Timestamp | None:
    """'YYYY' | 'YYYY-MM-DD' | None -> Timestamp (00:00). `cuoi=True`: moc CUOI (loai tru) = 00:00 cua NGAY SAU
    (nam: 1/1 nam sau), de `den` bao gom tron ngay cuoi. Sai dinh dang / ngay khong co that -> ValueError."""
    if s is None or s == "":
        return None
    m = _NGAY.match(str(s).strip())
    if not m:
        raise ValueError("ngay phai la YYYY hoac YYYY-MM-DD: %r" % (s,))
    nam, thang, ngay = int(m.group(1)), m.group(2), m.group(3)
    try:
        if thang is None:
            t = pd.Timestamp(year=nam, month=1, day=1)
            return t + pd.DateOffset(years=1) if cuoi else t
        t = pd.Timestamp(year=nam, month=int(thang), day=int(ngay))
    except ValueError as e:
        raise ValueError("ngay khong co that: %r (%s)" % (s, e)) from None
    return t + pd.Timedelta(days=1) if cuoi else t


def _la_cua_so(tu: str | None, den: str | None) -> bool:
    """Co cua so thi file mang ten cua so. Chi `--tu NAM` (cach cu) giu ten cu `<MA>_<KHUNG>.csv.gz`.
    Sai dinh dang ngay -> ValueError (khong de roi vao AttributeError)."""
    a, b = doc_ngay(tu), doc_ngay(den)
    return b is not None or (a is not None and "-" in str(tu))


def _the_cua_so(tu: str | None, den: str | None) -> str:
    """`YYYYMMDD_YYYYMMDD` (ngay dau, ngay cuoi GOM); thieu mot dau thi `dau` / `cuoi`."""
    a, b = doc_ngay(tu), doc_ngay(den, cuoi=True)
    return "%s_%s" % ("dau" if a is None else a.strftime("%Y%m%d"),
                      "cuoi" if b is None else (b - pd.Timedelta(days=1)).strftime("%Y%m%d"))


def ten_tep(ma: str, khung: str, tu: str | None = None, den: str | None = None) -> str:
    """`AUDCAD_M1.csv.gz` hoac `AUDCAD_M1_20180701_20181231.csv.gz` (xem `_la_cua_so`)."""
    if _la_cua_so(tu, den):
        return "%s_%s_%s.csv.gz" % (ma, khung, _the_cua_so(tu, den))
    return "%s_%s.csv.gz" % (ma, khung)


def _cat(df: pd.DataFrame, tu: str | None, den: str | None) -> pd.DataFrame:
    """Cat [tu, den] (den gom ca ngay cuoi). Index da KHONG co mui gio."""
    a, b = doc_ngay(tu), doc_ngay(den, cuoi=True)
    if a is not None:
        df = df[df.index >= a]
    if b is not None:
        df = df[df.index < b]
    return df


def ghi(df: pd.DataFrame, ma: str, khung: str, thu_muc: Path | None = None, sao_luu: Path | None = None,
        tu: str | None = None, den: str | None = None, tran_byte: int = TRAN_BYTE_MOI_FILE) -> dict:
    """Ghi MOT cap. Tra dong manifest. `sao_luu=None` -> `../sao_luu_gia/<hom nay>/`. `tu` / `den` chi dat TEN cua so va
    cat df (df da duoc cat thi cat lai khong doi gi). Vuot `tran_byte` -> ValueError va KHONG de lai file nao."""
    thu_muc = Path(thu_muc) if thu_muc else thu_muc_mac_dinh()
    thu_muc.mkdir(parents=True, exist_ok=True)
    cot = [c for c in COT if c in df.columns]
    if not {"open", "high", "low", "close"} <= set(cot):
        raise ValueError("thieu cot OHLC: %s" % list(df.columns))
    d = df[cot].copy()
    d.index = pd.to_datetime(d.index)
    if d.index.tz is not None:
        d.index = d.index.tz_convert("UTC").tz_localize(None)
    d.index.name = "time"
    d = _cat(d, tu, den)
    if not len(d):
        raise ValueError("%s %s: khong con bar nao trong cua so %s..%s" % (ma, khung, tu, den))
    f = thu_muc / ten_tep(ma, khung, tu, den)
    tam = f.with_name(f.name + ".tam")                  # `du_lieu_gia/**/*.tam` nam trong .gitignore
    try:
        _ghi_gz(tam, d.to_csv(float_format="%.6g"))
        byte = tam.stat().st_size
        if byte > tran_byte:
            raise ValueError("%s: %.1f MB vuot tran %.1f MB moi file - chia cua so nho hon (repo la public)"
                             % (f.name, byte / 1e6, tran_byte / 1e6))
        os.replace(tam, f)
    finally:
        if tam.exists():
            tam.unlink()
    sl = Path(sao_luu) if sao_luu else GOC.parent / "sao_luu_gia" / date.today().isoformat()
    sl.mkdir(parents=True, exist_ok=True)
    shutil.copy2(f, sl / f.name)
    ra = {"ma": ma, "khung": khung, "so_bar": int(len(d)), "tu": str(d.index.min()), "den": str(d.index.max()),
          "byte": f.stat().st_size, "sha256": _sha(f), "tep": f.name}
    if _la_cua_so(tu, den):
        ra["yeu_cau_tu"], ra["yeu_cau_den"] = tu, den
    return ra


def _khoa(m: dict) -> str:
    return m["tep"][:-len(".csv.gz")] if m.get("tep") else "%s_%s" % (m["ma"], m["khung"])


def doc(ma: str, khung: str = "M15", thu_muc: Path | None = None,
        tu: str | None = None, den: str | None = None) -> pd.DataFrame:
    """Doc MOT file. Co `den` hoac `tu` day du ngay -> file cua so do (cung ten voi luc ghi); khong thi file khong cua so."""
    f = (Path(thu_muc) if thu_muc else thu_muc_mac_dinh()) / ten_tep(ma, khung, tu, den)
    return pd.read_csv(f, index_col="time", parse_dates=True)


def doc_het(ma: str, khung: str = "M15", thu_muc: Path | None = None,
            tu: str | None = None, den: str | None = None) -> pd.DataFrame:
    """GHEP moi file `<MA>_<KHUNG>*.csv.gz` trong thu muc (cac cua so khac nhau cua cung mot cap), bo trung (giu ban sau),
    sap theo thoi gian, cat [tu, den]. Khong co file nao -> FileNotFoundError."""
    th = Path(thu_muc) if thu_muc else thu_muc_mac_dinh()
    cac = sorted(p for p in th.glob("%s_%s*.csv.gz" % (ma, khung))
                 if re.fullmatch(r"%s_%s(_(\d{8}|dau)_(\d{8}|cuoi))?\.csv\.gz" % (re.escape(ma), re.escape(khung)), p.name))
    if not cac:
        raise FileNotFoundError("khong co file gia nao cho %s %s o %s" % (ma, khung, th))
    d = pd.concat([pd.read_csv(p, index_col="time", parse_dates=True) for p in cac])
    d = d[~d.index.duplicated(keep="last")].sort_index()
    return _cat(d, tu, den)


def _ghi_so_khai(thu_muc: Path, m: dict) -> None:
    """Gop MOT dong vao `MANIFEST.json` (thay nguyen tu). Goi sau MOI cap: hong giua chung thi tep da ghi van co dong khai."""
    p = Path(thu_muc) / "MANIFEST.json"
    cu = json.loads(p.read_text("utf-8")) if p.exists() else {}
    cu[_khoa(m)] = m
    tam = p.with_name(p.name + ".tam")
    tam.write_text(json.dumps(cu, ensure_ascii=False, indent=1), "utf-8")
    os.replace(tam, p)


def chay(cac_ma: list[str], khung: str = "M15", thu_muc: Path | None = None,
         tu: str | None = None, den: str | None = None) -> list[dict]:
    from nhan import du_lieu
    doc_ngay(tu), doc_ngay(den)                         # sai dinh dang thi dung TRUOC khi nap bat ky ma nao
    thu_muc = Path(thu_muc) if thu_muc else thu_muc_mac_dinh()
    mf, tong = [], 0
    for ma in cac_ma:
        df = du_lieu.nap(ma, khung)                    # cat cua so o `ghi` (nap(tu=...) so sanh sai khi index co mui gio)
        m = ghi(df, ma, khung, thu_muc, tu=tu, den=den)
        da_sua = getattr(du_lieu, "_DA_SUA", {}).get((ma.upper(), khung.upper()))
        if da_sua:
            m["da_sua_bar"] = json.loads(json.dumps(da_sua, default=str))
        _ghi_so_khai(thu_muc, m)
        mf.append(m)
        tong += m["byte"]
        print("%s %s: %d bar %s -> %s, %.1f MB" % (ma, khung, m["so_bar"], m["tu"][:10], m["den"][:10], m["byte"] / 1e6))
        if tong > TRAN_BYTE_MOI_LENH:
            raise ValueError("tong %.1f MB vuot tran %.1f MB moi lenh - dung o %s, chia lam nhieu lenh (repo la public)"
                             % (tong / 1e6, TRAN_BYTE_MOI_LENH / 1e6, ma))
    return mf


def main_cli(a: list[str] | None = None) -> None:
    a = list(sys.argv[1:] if a is None else a)
    if not a:
        sys.exit(__doc__)
    co_gia_tri = ("--thu-muc", "--tu", "--den")
    th = Path(a[a.index("--thu-muc") + 1]) if "--thu-muc" in a else None
    tu = a[a.index("--tu") + 1] if "--tu" in a else None
    den = a[a.index("--den") + 1] if "--den" in a else None
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in co_gia_tri)]
    chay(pos[0].split(","), pos[1] if len(pos) > 1 else "M15", th, tu, den)


if __name__ == "__main__":
    main_cli()
