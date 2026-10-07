# -*- coding: utf-8 -*-
"""khoi_phuc.py - CHAN DOAN MAY: may nay con gi, thieu gi, thieu cai nao la MAT THAT.

Vi sao co (02/10/2026): may nha cai lai Windows. Ma nguon con day du tren GitHub, nhung nhung
thu nam NGOAI git mat theo o C: tru khi con ban sao: kho gia `data/`, `nao.db`, khoa API, MT5,
cc-switch, va ca `ds/` (git rieng, KHONG co repo tren GitHub). Truoc khi lam bat cu viec gi phai
biet MAY NAY dang thieu gi - va quan trong hon: o dau do CON ban sao.

    b khoi-phuc            in bang + "BUOC TIEP"
    b khoi-phuc --json     cho may doc

Chi DOC. Khong bao gio in noi dung file bi mat - chi "co" / "khong".
`san_sang_vps.py` tra loi cau KHAC (MA da chuyen may duoc chua); file nay do CHINH MAY.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nhan import duong_dan as DP

LAB = DP.LAB
GOI_BAT_BUOC = ("numpy", "pandas", "scipy", "requests", "psutil", "pyarrow")
GOI_TUY_CHON = ("MetaTrader5", "playwright", "statsmodels", "pypdf")
#: thu muc luu tru ngoai o C: ma `duong_dan.py` biet (F: tu 12/09/2026) - quet them vai o cung ten
O_LUU = "TheBrain_luu"
FILE_BI_MAT = ("config/api_keys.json", "config/gh_token.txt", "config/passview.json")


def _dong(nhom: str, ten: str, ok: bool | None, chi_tiet: str = "", sua: str = "",
          mat_that: bool = False) -> dict:
    """ok: True = co · False = thieu · None = khong ap dung / tuy chon. mat_that = khong tai tao duoc tu git."""
    return {"nhom": nhom, "ten": ten, "ok": ok, "chi_tiet": chi_tiet, "sua": sua, "mat_that": mat_that}


def _git(*doi: str, goc: Path | None = None) -> str:
    try:
        r = subprocess.run(["git", *doi], cwd=str(goc or LAB), capture_output=True, text=True,
                           timeout=20, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def _gb(n: float) -> str:
    return "%.2f GB" % (n / 1e9)


def _parquet(thu_muc: Path) -> tuple[int, float]:
    try:
        f = [p for p in thu_muc.glob("*.parquet")]
        return len(f), sum(p.stat().st_size for p in f)
    except OSError:
        return 0, 0.0


def kiem_moi_truong() -> list[dict]:
    d = []
    v = sys.version_info
    d.append(_dong("cong cu", "python", v >= (3, 10), "%d.%d.%d (%s)" % (v[0], v[1], v[2], sys.executable),
                   "winget install --id Python.Python.3.12 -e"))
    d.append(_dong("cong cu", "git", shutil.which("git") is not None, shutil.which("git") or "",
                   "winget install --id Git.Git -e"))
    d.append(_dong("cong cu", "claude (Claude Code)", shutil.which("claude") is not None,
                   shutil.which("claude") or "", "irm https://claude.ai/install.ps1 | iex   (PowerShell)"))
    for g in GOI_BAT_BUOC:
        d.append(_dong("goi python", g, importlib.util.find_spec(g) is not None, "",
                       "python -m pip install -r requirements.txt"))
    for g in GOI_TUY_CHON:
        co = importlib.util.find_spec(g) is not None
        d.append(_dong("goi python", g + " (tuy chon)", co or None,
                       "" if co else "chi can cho nhanh MT5 / SEEKER / thong ke nang cao"))
    return d


def kiem_ma() -> list[dict]:
    nhanh = _git("rev-parse", "--abbrev-ref", "HEAD")
    if not nhanh:
        return [_dong("ma nguon", "kho git (thu muc nay)", False, "thu muc nay khong phai kho git",
                      "git clone https://github.com/thebrainago/the-brain.git lab")]
    sua = len([x for x in _git("status", "--porcelain", "--untracked-files=no").splitlines() if x.strip()])
    return [_dong("ma nguon", "nhanh + commit", True,
                  "%s @ %s%s" % (nhanh, _git("rev-parse", "--short", "HEAD"),
                                 ("  (+%d file dang sua)" % sua) if sua else ""))]


def kiem_du_lieu() -> list[dict]:
    d = []
    kho, cache = DP.kho_gia(), DP.cache_khung()
    n, b = _parquet(kho)
    d.append(_dong("du lieu", "kho gia data/", n > 0, "%s: %d bang .parquet, %s" % (kho, n, _gb(b)),
                   "tim ban sao (muc 2 tai_lieu/KHOI_PHUC_MAY_NHA.md) hoac dung lai tu MT5", mat_that=True))
    nc, bc = _parquet(cache)
    d.append(_dong("du lieu", "cache data_khung/", True if nc else None,
                   "%s: %d bang, %s (cache - tai tao duoc tu data/)" % (cache, nc, _gb(bc))))
    for ten in ("nao.db", "nc.db"):
        p = DP.so_dang(ten)
        kich = p.stat().st_size if p.exists() else 0
        # nao.db that nang ~1,6 GB; file vai chuc KB = DB moi khoi tao (test / lan chay dau), khong phai du lieu cu
        co = kich >= (1_000_000 if ten == "nao.db" else 1)
        d.append(_dong("du lieu", ten, co, ("%s, %s" % (p, _gb(kich))) if kich else str(p),
                       "so FDR / ung vien / tai lieu da doc nam o day - mat thi dem phep thu lam lai tu 0"
                       if ten == "nao.db" else "so tay nha nghien cuu - tao lai bang `b nc`",
                       mat_that=(ten == "nao.db")))
    # bi mat: chi hoi co hay khong
    for f in FILE_BI_MAT:
        co = (LAB / f).exists()
        d.append(_dong("bi mat", f, co, "co" if co else "khong",
                       "tao lai tren may nay - KHONG dan khoa vao chat", mat_that=True))
    return d


def kiem_may_khac(he_thong: Path | None = None) -> list[dict]:
    """Noi CON ban sao sau khi cai lai Windows: Windows.old, o luu tru ngoai C:, ds/."""
    d = []
    goc_he = he_thong if he_thong is not None else Path(os.environ.get("SystemDrive", "C:") + os.sep)
    wo = goc_he / "Windows.old"
    ket = []
    try:
        if wo.exists():
            for nd in sorted((wo / "Users").glob("*")):
                lab = nd / "Downloads" / "Research SP500" / "lab"
                ket.append("%s%s" % (lab, "  (CO nao.db %s)" % _gb((lab / "nao.db").stat().st_size)
                                     if (lab / "nao.db").exists() else ""))
    except OSError:
        pass
    d.append(_dong("ban sao con lai", "Windows.old", True if wo.exists() else None,
                   ("CO - COPY NGAY, Windows tu xoa sau ~10 ngay: " + "; ".join(ket)) if wo.exists()
                   else "khong co (ban cai sach hoac da bi don)"))
    luu = []
    for chu in "DEFGH":
        p = Path("%s:/%s" % (chu, O_LUU))
        try:
            if p.exists():
                luu.append(str(p))
        except OSError:
            pass
    d.append(_dong("ban sao con lai", O_LUU + " (o D..H)", True if luu else None,
                   ("CO: " + ", ".join(luu) + " - nhan/duong_dan.py tu nhan F:") if luu
                   else "khong thay"))
    ds = DP.GOC / "ds"
    n_ds = _git("rev-list", "--count", "HEAD", goc=ds) if (ds / ".git").exists() else ""
    d.append(_dong("ban sao con lai", "ds/ (git rieng, KHONG co tren GitHub)", ds.is_dir(),
                   ("%s - %s commit" % (ds, n_ds)) if n_ds else str(ds),
                   "56 commit / 799 test cua kho DeepSeek: chi con neu tim duoc ban sao", mat_that=True))
    return d


def kiem_mt5() -> list[dict]:
    exe, du_lieu = DP.mt5_exe(), DP.mt5_du_lieu()
    return [_dong("mt5", "terminal64.exe", exe is not None, str(exe or ""),
                  "cai XM MT5 + mo tai khoan DEMO (may chu XMGlobal-MT5 10)", mat_that=False),
            _dong("mt5", "thu muc du lieu MT5", du_lieu is not None, str(du_lieu or ""),
                  "tu sinh sau lan chay MT5 dau tien")]


def kiem_kenh() -> list[dict]:
    d = []
    cho = len(list((LAB / "viec" / "cho").glob("*.json"))) if (LAB / "viec" / "cho").is_dir() else 0
    d.append(_dong("kenh cloud<->may", "viec/cho (don dang xep hang)", True if cho else None,
                   "%d don" % cho))
    try:
        from qwen import mo_hinh as QM
        cc = QM.tu_cc_switch(os.environ.get("THO_PROVIDER", "deepseek"))
        co = bool(cc.get("khoa") and cc.get("base_url"))
    except Exception:
        co = False
    d.append(_dong("kenh cloud<->may", "cc-switch: provider DeepSeek", True if co else None,
                   "co" if co else "chua co - chi can khi dung tho model re (b nc tho)"))
    return d


def chan_doan(he_thong: Path | None = None) -> list[dict]:
    return (kiem_moi_truong() + kiem_ma() + kiem_may_khac(he_thong) + kiem_du_lieu()
            + kiem_mt5() + kiem_kenh())


def buoc_tiep(ds_: list[dict]) -> list[str]:
    """Danh sach viec, theo thu tu: cai nao co HAN va khong lam lai duoc thi len dau."""
    def thieu(ten: str) -> bool:
        return any(x["ten"].startswith(ten) and x["ok"] is False for x in ds_)

    def co(ten: str) -> bool:
        return any(x["ten"].startswith(ten) and x["ok"] is True for x in ds_)
    b = []
    if co("Windows.old"):
        b.append("COPY Windows.old\\Users\\<ten>\\Downloads\\Research SP500 sang o khac TRUOC (Windows tu xoa "
                 "sau ~10 ngay; dung chay Disk Cleanup muc 'Previous Windows installation').")
    if co(O_LUU):
        b.append("Kho gia con o %s: giu nguyen, nhan/duong_dan.py tu nhan." % O_LUU)
    if thieu("kho git"):
        b.append("Thu muc nay khong phai kho git: git clone https://github.com/thebrainago/the-brain.git lab")
    for t in ("python", "git", "claude"):
        if thieu(t):
            b.append("Cai %s: %s" % (t, next(x["sua"] for x in ds_ if x["ten"].startswith(t))))
    if any(x["nhom"] == "goi python" and x["ok"] is False for x in ds_):
        b.append("python -m pip install -r requirements.txt   (trong .venv cua repo)")
    if thieu("terminal64"):
        b.append("Cai XM MT5 va mo tai khoan DEMO (may chu XMGlobal-MT5 10).")
    if thieu("kho gia"):
        b.append("Kho gia mat: tim ban sao (Windows.old, o ngoai, Drive) hoac dung lai tu MT5 - "
                 "tai_lieu/KHOI_PHUC_MAY_NHA.md muc 6.")
    if thieu("nao.db"):
        b.append("nao.db mat: dem phep thu (so FDR) bat dau lai tu 0 - doc muc 7 KHOI_PHUC_MAY_NHA.md "
                 "truoc khi tin bat ky p-value nao.")
    if thieu("ds/"):
        b.append("ds/ khong con: tim ban sao (no khong co tren GitHub); lab chi can no o 2 cho "
                 "(nhan/doc_lenh_tester.py, test_mimic_ban_do.py).")
    if any(x["nhom"] == "bi mat" and x["ok"] is False for x in ds_):
        b.append("Tao lai file khoa trong config/ (api_keys.json, gh_token.txt...) - nhap bang tay, "
                 "KHONG dan khoa vao chat.")
    return b or ["Khong thieu gi dang ke. Chay `b vao`, `b nc`, roi `b test`."]


def bao_cao(ds_: list[dict] | None = None) -> str:
    ds_ = ds_ if ds_ is not None else chan_doan()
    ra, nhom = [], None
    for x in ds_:
        if x["nhom"] != nhom:
            nhom = x["nhom"]
            ra.append("\n[%s]" % nhom)
        the = {True: "CO   ", False: "THIEU", None: "  -  "}[x["ok"]]
        ra.append("  %s %-40s %s" % (the, x["ten"], x["chi_tiet"]))
    ra.append("\nBUOC TIEP")
    ra += ["  %d. %s" % (i, s) for i, s in enumerate(buoc_tiep(ds_), 1)]
    return "\n".join(ra).lstrip("\n")


def main(argv: list[str]) -> int:
    ds_ = chan_doan()
    if "--json" in argv:
        print(json.dumps({"kiem": ds_, "buoc_tiep": buoc_tiep(ds_)}, ensure_ascii=False, indent=1))
    else:
        print(bao_cao(ds_))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
