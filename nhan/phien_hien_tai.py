# -*- coding: utf-8 -*-
"""phien_hien_tai.py - BAN GIAO PHIEN: mot file ngan (~1,5k token) thay cho viec doc lai lich su chat va tai lieu dai.

## Vi sao (02/10/2026)
Do that (`b token`): moi goi API doc lai TOAN BO ngu canh (TB 443k token/goi o phien cloud), nen chi phi nam o do dai phien, khong o
tung tin nhan. Cach re nhat la mo PHIEN MOI sau moi moc - nhung chi dam lam vay khi phien moi vao lai duoc ngay, khong phai doc lai
lich su chat (hang tram nghin token) hay 5-6 tai lieu dai (`BAN_GIAO_HE_THONG.md` ~13k token, `HO_SO_HE_THONG.md` ~11k...).

`tai_lieu/PHIEN_HIEN_TAI.md` gom hai khoi, ranh gioi bang dong chu thich HTML:
  AUTO  may do: nhanh, commit, thu, may, don, kho gia, so cai. `b tiep --ghi` lam moi; khong ai chep tay (chep tay thi lech).
  TAY   phien CHI HUY viet: quyet dinh con hieu luc, dang o dau, viec ke tiep, DUNG LAM LAI. Lam moi KHONG dong vao khoi nay.

    b tiep                in ban giao (AUTO moi do luc nay + khoi TAY trong file)
    b tiep --ghi          ghi lai file (cap nhat AUTO, giu nguyen TAY) - chay truoc khi dong phien / sau moi moc
    b tiep --chi-muc      muc luc tai lieu: ~token + dong dau, xep theo co - de mo DUNG cai can, doc DUNG doan (sed -n 'a,bp')
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
FILE = LAB / "tai_lieu" / "PHIEN_HIEN_TAI.md"
A0, A1 = "<!-- AUTO:BAT_DAU -->", "<!-- AUTO:HET -->"
T0, T1 = "<!-- TAY:BAT_DAU -->", "<!-- TAY:HET -->"
K_KY_TU = 3.2
MAU_TAY = """## Quyet dinh cua chu du an con hieu luc
- (chua co)

## Dang o dau
- (chua co)

## Viec ke tiep (thu tu)
1. (chua co)

## Dung lam lai (da thu / da quyet)
- (chua co)
"""
TIEU_DE = "# PHIEN HIEN TAI - doc DAU TIEN thay cho lich su chat / tai lieu dai\n\n" \
          "> Khoi AUTO do may lam moi (`b tiep --ghi`); khoi TAY do phien chi huy viet, cap nhat sau moi moc. Tai lieu day du: `b tiep --chi-muc`.\n"


def _git(goc: Path, *a: str) -> str:
    from qwen import cau_git as CG
    ma, ra, _ = CG._git(*a, goc=goc, han=30.0)
    return ra.strip() if ma == 0 else ""


def _bat_buoc(f, mac_dinh="?"):
    try:
        return f()
    except Exception as e:                                   # noqa: BLE001 - ban giao khong duoc chet vi mot muc hong
        return "%s (%s)" % (mac_dinh, type(e).__name__)


def _nhanh_va_sha(goc: Path) -> str:
    nh = _git(goc, "rev-parse", "--abbrev-ref", "HEAD") or "?"
    sha = _git(goc, "rev-parse", "--short", "HEAD") or "?"
    sua = len([x for x in _git(goc, "status", "--porcelain").splitlines() if x.strip()])
    lech = _git(goc, "rev-list", "--left-right", "--count", "HEAD...origin/%s" % nh)
    if lech and len(lech.split()) == 2:
        a, b = lech.split()
        so_voi = "so voi origin/%s: +%s/-%s" % (nh, a, b)
    else:
        so_voi = "chua co origin/%s trong ban sao (b cau lay / git fetch)" % nh
    return "- Nhanh %s @ %s · %s · %s" % (nh, sha, "sach" if not sua else "%d file sua/chua theo doi" % sua, so_voi)


def _commit_gan_day(goc: Path, n: int = 5) -> str:
    """N commit gan day, BO commit thu/ket qua may (rac: moi lan nhan tin la mot commit)."""
    ds = [d for d in _git(goc, "log", "-60", "--format=%h %s").splitlines()
          if not re.match(r"^\w+ (thu (cloud|nha|may)|may( nha)?[: ]|cau-may)", d)][:n]
    return "- Commit gan day:\n" + "\n".join("  · " + d[:90] for d in ds) if ds else "- Commit gan day: (khong doc duoc git)"


def _thu(goc: Path, bay_gio: float) -> str:
    from qwen import cau_thu as CTH
    ben = CTH.ben_mac_dinh()
    ds = CTH.tat_ca(goc)
    han = bay_gio - 86400
    dem = {}
    for d in ds:
        try:
            if time.mktime(time.strptime(str(d["luc"]), "%Y-%m-%dT%H:%M:%S")) >= han:
                k = "%s->%s" % (d["tu"], d["den"])
                dem[k] = dem.get(k, 0) + 1
        except (ValueError, OverflowError):
            pass
    chua_doc = len(CTH.doc_moi(ben, goc))
    dong = "- Thu: phien nay la `%s`, chua doc %d · 24h qua: %s" % (ben, chua_doc, ", ".join("%s %d" % kv for kv in sorted(dem.items())) or "khong co")
    if ds:
        m = ds[-1]
        dong += "\n  · moi nhat %s->%s (gio may gui %s): %s" % (m["tu"], m["den"], m["luc"], (m.get("chu_de") or m["noi_dung"][:50]).replace("\n", " ")[:60])
    return dong


def _may(goc: Path) -> str:
    from qwen import cau_may as CM
    ds = CM.doc_may(goc)
    if not ds:
        return "- May: chua may nao bao nhip tim (chua `b cau cai` / `b cau chay`)"
    return "- May:\n" + "\n".join("  · %s %s ma=%s nhip %s (gio may)" % (d.get("ten"), d.get("trang_thai"), d.get("phien_ban_ma"), d.get("luc")) for d in ds)


def _don(goc: Path) -> str:
    import json
    v = goc / "viec"

    def dem(t):
        return len(list((v / t).glob("*.json"))) if (v / t).is_dir() else 0
    kq: dict = {}
    for p in (v / "xong").glob("*.json") if (v / "xong").is_dir() else []:
        try:
            tt = json.loads(p.read_text(encoding="utf-8-sig")).get("trang_thai", "?")
        except (OSError, ValueError):
            tt = "?"
        kq[tt] = kq.get(tt, 0) + 1
    return "- Don: cho %d · dang %d · xong %d (%s)" % (dem("cho"), dem("dang"), dem("xong"), " · ".join("%s %d" % kv for kv in sorted(kq.items())) or "chua co ket qua")


def _du_lieu(goc: Path) -> str:
    try:
        from nhan import duong_dan as DD
        kho = DD.kho_gia()
        n = len(list(kho.glob("*.parquet"))) if kho.is_dir() else 0
        d_kho = "kho gia %s: %d file .parquet" % (kho, n)
    except Exception as e:                                   # noqa: BLE001
        d_kho = "kho gia khong xac dinh (%s)" % type(e).__name__
    doan = (goc / "so_cai" / "doan.json").exists()
    nc = goc / "so_cai" / "nc"
    fs = [p for p in nc.glob("*") if p.is_file()] if nc.is_dir() else []
    return "- Du lieu: %s · so_cai/doan.json %s · so_cai/nc %d file %d KB" % (
        d_kho, "CO" if doan else "CHUA CO (tao o lan nap() dau, PHAI commit+push ngay)", len(fs), sum(p.stat().st_size for p in fs) // 1024)


def auto(goc: Path | None = None, bay_gio: float | None = None) -> str:
    goc = Path(goc or LAB)
    bay_gio = bay_gio or time.time()
    from qwen import cau_git as CG
    muc = [
        "## Trang thai (may do luc %s UTC) - `b tiep --ghi` de lam moi" % time.strftime("%Y-%m-%d %H:%M", time.gmtime(bay_gio)),
        _bat_buoc(lambda: _nhanh_va_sha(goc)),
        _bat_buoc(lambda: _commit_gan_day(goc)),
        _bat_buoc(lambda: _thu(goc, bay_gio)),
        _bat_buoc(lambda: _may(goc)),
        _bat_buoc(lambda: _don(goc)),
        _bat_buoc(lambda: _du_lieu(goc)),
        "- Cau hinh: config/cau.json %s" % ("CO (may nha)" if CG.CAU_HINH.exists() else "khong co (phien cloud)"),
    ]
    return "\n".join(muc)


def doc_tay(van: str) -> str | None:
    i, j = van.find(T0), van.find(T1)
    return van[i + len(T0):j].strip("\n") if i != -1 and j > i else None


def dung(goc: Path | None = None, file: Path | None = None, bay_gio: float | None = None) -> str:
    """Noi dung day du: AUTO moi + TAY hien co (hoac mau neu chua co)."""
    f = Path(file or FILE)
    cu = f.read_text(encoding="utf-8") if f.exists() else ""
    tay = doc_tay(cu) or MAU_TAY.strip("\n")
    return "%s\n%s\n%s\n%s\n\n%s\n%s\n%s\n" % (TIEU_DE, A0, auto(goc, bay_gio), A1, T0, tay, T1)


def ghi(goc: Path | None = None, file: Path | None = None, bay_gio: float | None = None) -> dict:
    f = Path(file or FILE)
    van = dung(goc, f, bay_gio)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(van, encoding="utf-8")
    return {"file": str(f), "ky_tu": len(van), "token_uoc": int(len(van) / K_KY_TU), "co_tay": T0 in van}


def chi_muc(goc: Path | None = None, top: int = 15) -> list[dict]:
    goc = Path(goc or LAB)
    ds = list(goc.glob("*.md")) + list((goc / "tai_lieu").glob("*.md")) + list((goc / "qwen").glob("*.md"))
    ra = []
    for p in ds:
        try:
            van = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        dau = next((x.strip() for x in van.splitlines() if x.lstrip().startswith("#")), "")
        ra.append({"file": str(p.relative_to(goc)).replace("\\", "/"), "token": int(len(van) / K_KY_TU), "dau": re.sub(r"^#+\s*", "", dau)[:80]})
    ra.sort(key=lambda x: -x["token"])
    return ra[:top]


def main(argv: list[str]) -> int:
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
    if "--chi-muc" in argv:
        for x in chi_muc():
            print("~%6d token  %-44s %s" % (x["token"], x["file"], x["dau"]))
        print("Mo DUNG doan can: grep -n '<tu khoa>' <file> roi sed -n 'a,bp' <file>. Dung doc ca file dai.")
        return 0
    if "--ghi" in argv:
        r = ghi()
        print("da ghi %s (~%d token; khoi TAY %s)" % (r["file"], r["token_uoc"], "giu nguyen" if r["co_tay"] else "MAU - hay viet"))
        return 0
    print(dung())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
