# -*- coding: utf-8 -*-
"""nen_tang.py - MA NGUON CHIEN LUOC TU CAC NEN TANG GIAO DICH KHAC.

VI SAO. Chu du an 04/09/2026: *"hay build them ngach cho ctrader di, con nen
tang giao dich gi nua thi quet het not"*.

DO TRUOC KHI XAY: doi chieu 22 nen tang voi bang `nguon` cua he.

    DA CO   : MQL4/5, TradingView (Pine), QuantConnect/LEAN
    CHUA CO : cTrader, NinjaTrader, TradeStation, MultiCharts, ProRealTime,
              Sierra Chart, AmiBroker, Zorro, Wealth-Lab, Quantower,
              Jesse, Hummingbot, Freqtrade, Backtrader, vectorbt
              -> **19 nen tang, 0 nguon**

DUONG VAO - da do tung cai 04/09, khong doan:

  1. **GitHub la duong pho quat.** Gan nhu moi nen tang deu co chien luoc duoc
     day len GitHub, va `api.github.com/search` vao duoc tu may nay. Tru luong
     do duoc (so repo khop truy van):
         freqtrade 316 | backtrader 258 | ninjatrader 18 | easylanguage 6
         ctrader 5 | amibroker 3 | prorealtime 1 | zorro 0
     Chenh nhau **300 lan**, nen chia thoi luong deu cho 19 nen tang la sai.

  2. **cTrader Store (`ctrader.com/algos/cbots/`) VAO DUOC nhung KHONG cho ma
     nguon.** Trang tra ve 40 san pham trong `__NEXT_DATA__` voi cac truong
     `profitFactor`, `maxDrawdownPercent`, `monthlyRoiPercent`, `userCount`.
     Do la mot nguon **HIEU SUAT** (cung loai voi mql5_signals), khong phai
     nguon LUAT. Hai thu do khong duoc tron: mot ben cho ta co che de kiem
     dinh, mot ben cho ta loi khoe cua nguoi khac.

  3. Trang rieng cua NinjaTrader/ProRealCode tra 404 o duong doan - chua tim ra
     duong that. Ghi vao `CHUA_TIM_RA_DUONG` thay vi im lang.

RANG BUOC AN TOAN - y het `nhan/ma_nguon.py`, khong noi long:
  1. KHONG BAO GIO chay ma tai ve. Doc nhu van ban.
  2. Chi anh xa vao mau CO SAN qua `nhan/bien_dich_ung_vien.py`.
  3. Co tran kich thuoc.
  4. Provenance day du qua `hop_dong.CodeArtifact`.
"""
from __future__ import annotations

import time

from nhan import hop_dong as HD
from nhan import so as SO

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TheBrainResearch/0.1"
GH = "https://api.github.com"

#: Tran mot file. Tren muc nay gan nhu chac chan la thu vien dinh kem.
TRAN_BYTE = 400_000
SAN_BYTE = 400

#: SO DANG KY NEN TANG. `tru_luong` la so repo do duoc 04/09 - dung de chia
#: thoi luong, khong phai de xep hang gia tri.
NEN_TANG = {
    "freqtrade": {
        "truy_van": "freqtrade strategy", "duoi": (".py",),
        "ngon_ngu": "python", "tru_luong": 316,
        "ghi_chu": "chien luoc Python thuan, dang truc tiep nhat de rut luat. "
                   "freqtrade-strategies 5.433 sao, NostalgiaForInfinity 3.396.",
    },
    "backtrader": {
        "truy_van": "backtrader strategy", "duoi": (".py",),
        "ngon_ngu": "python", "tru_luong": 258,
    },
    "ninjatrader": {
        "truy_van": "ninjatrader ninjascript strategy", "duoi": (".cs",),
        "ngon_ngu": "csharp", "tru_luong": 18,
    },
    "ctrader": {
        "truy_van": "ctrader cbot algo", "duoi": (".cs",),
        "ngon_ngu": "csharp", "tru_luong": 5,
        "ghi_chu": "spotware/ctrader-algo-samples la repo mau CHINH THUC. "
                   "cTrader Store khong cho ma nguon - xem `cua_hang_ctrader`.",
    },
    "easylanguage": {
        "truy_van": "tradestation easylanguage strategy",
        "duoi": (".eld", ".txt", ".el"), "ngon_ngu": "easylanguage",
        "tru_luong": 6,
    },
    "amibroker": {
        "truy_van": "amibroker afl strategy", "duoi": (".afl",),
        "ngon_ngu": "afl", "tru_luong": 3,
    },
    "prorealtime": {
        "truy_van": "prorealtime probuilder strategy", "duoi": (".itf", ".txt"),
        "ngon_ngu": "probuilder", "tru_luong": 1,
    },
    "vectorbt": {
        "truy_van": "vectorbt strategy backtest", "duoi": (".py",),
        "ngon_ngu": "python", "tru_luong": None,
    },
    "jesse": {
        "truy_van": "jesse-ai strategy", "duoi": (".py",),
        "ngon_ngu": "python", "tru_luong": None,
    },
    "hummingbot": {
        "truy_van": "hummingbot strategy", "duoi": (".py",),
        "ngon_ngu": "python", "tru_luong": None,
    },
    "multicharts": {
        "truy_van": "multicharts powerlanguage strategy",
        "duoi": (".pla", ".txt"), "ngon_ngu": "powerlanguage", "tru_luong": None,
    },
    "sierrachart": {
        "truy_van": "sierra chart acsil study", "duoi": (".cpp", ".h"),
        "ngon_ngu": "cpp", "tru_luong": None,
    },
    "quantower": {
        "truy_van": "quantower strategy algo", "duoi": (".cs",),
        "ngon_ngu": "csharp", "tru_luong": None,
    },
    "zorro": {
        "truy_van": "zorro trading lite-c strategy", "duoi": (".c",),
        "ngon_ngu": "lite-c", "tru_luong": 0,
        "ghi_chu": "0 repo do duoc 04/09 - co the nen tang nay khong dung GitHub.",
    },
}

#: Nen tang co trang rieng nhung CHUA TIM RA duong lay ma. Ghi ra de lan sau
#: khong phai do lai tu dau, va de khong ai tuong la da quet roi.
CHUA_TIM_RA_DUONG = {
    "ninjatrader_ecosystem": "ninjatraderecosystem.com - duong /user-app-share-"
                             "download/ tra 404 (04/09)",
    "prorealcode": "prorealcode.com/free-trading-strategies/ tra 404 (04/09)",
    "amibroker_library": "amibroker.com/library/list.php tra 200 nhung chi "
                         "4.555 byte - co the doi duong hoac can tham so",
}


def _gh(duong: str, tham_so: dict | None = None, timeout: int = 30):
    import requests
    r = requests.get(GH + duong, params=tham_so or {}, timeout=timeout,
                     headers={"User-Agent": UA,
                              "Accept": "application/vnd.github+json"})
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    return r.json(), None


def tim_repo(ten: str, so_repo: int = 8) -> tuple[list, str | None]:
    """Repo cua mot nen tang, xep theo sao."""
    c = NEN_TANG.get(ten)
    if not c:
        return [], f"khong co nen tang '{ten}'"
    j, loi = _gh("/search/repositories",
                 {"q": c["truy_van"], "per_page": so_repo, "sort": "stars"})
    if loi:
        return [], loi
    return (j or {}).get("items", []), None


def _file_trong(full_name: str, duoi: tuple, tran: int = 40) -> list[dict]:
    """File khop duoi trong repo, qua Git Trees API (mot lan goi cho ca cay)."""
    j, loi = _gh(f"/repos/{full_name}")
    if loi or not j:
        return []
    nhanh = j.get("default_branch") or "main"
    t, loi = _gh(f"/repos/{full_name}/git/trees/{nhanh}", {"recursive": "1"})
    if loi or not t:
        return []
    ra = []
    for n in (t.get("tree") or []):
        if n.get("type") != "blob":
            continue
        p = str(n.get("path") or "")
        if not p.lower().endswith(tuple(d.lower() for d in duoi)):
            continue
        cx = int(n.get("size") or 0)
        if not (SAN_BYTE <= cx <= TRAN_BYTE):
            continue
        ra.append({"path": p, "sha": n.get("sha"), "so_byte": cx,
                   "nhanh": nhanh})
        if len(ra) >= tran:
            break
    return ra


def _noi_dung(full_name: str, nhanh: str, path: str) -> str | None:
    import requests
    from urllib.parse import quote
    u = (f"https://raw.githubusercontent.com/{full_name}/{nhanh}/"
         f"{quote(path)}")
    try:
        r = requests.get(u, timeout=30, headers={"User-Agent": UA})
    except Exception:
        return None
    if r.status_code != 200 or len(r.text) < SAN_BYTE:
        return None
    return r.text[:TRAN_BYTE]


def thu_thap(ten: str, so_repo: int = 4, so_file_moi_repo: int = 12,
             nghi_giay: float = 1.5, in_ra=print) -> dict:
    """Mot nen tang -> file chien luoc -> bang `artifact` (CodeArtifact)."""
    c = NEN_TANG.get(ten)
    if not c:
        return {"nen_tang": ten, "loi": "khong co trong SO DANG KY"}
    repo, loi = tim_repo(ten, so_repo)
    if loi:
        return {"nen_tang": ten, "loi": loi}
    bao = {"nen_tang": ten, "repo": len(repo), "file_thay": 0,
           "ghi_moi": 0, "da_co": 0, "loi_file": 0}
    for r in repo:
        fn = r.get("full_name")
        gp = ((r.get("license") or {}) or {}).get("spdx_id")
        for f in _file_trong(fn, c["duoi"], so_file_moi_repo):
            bao["file_thay"] += 1
            vb = _noi_dung(fn, f["nhanh"], f["path"])
            time.sleep(nghi_giay)
            if not vb:
                bao["loi_file"] += 1
                continue
            art = HD.CodeArtifact(
                source_id=f"nen_tang:{ten}:{fn}",
                repository_url=r.get("html_url") or f"https://github.com/{fn}",
                revision=f["sha"] or f["nhanh"],
                path=f["path"],
                retrieved_at=SO.bay_gio().replace(" ", "T") + "Z",
                content=vb,
                language=c.get("ngon_ngu"),
                license=gp or "khong khai",
                metadata={"nen_tang": ten, "repo": fn,
                          "sao": r.get("stargazers_count"),
                          "so_byte": f["so_byte"]})
            try:
                _id, moi = SO.them_artifact(art)
                bao["ghi_moi" if moi else "da_co"] += 1
            except Exception:
                bao["loi_file"] += 1
    SO.ghi_chi_so("nen_tang_ghi_moi", float(bao["ghi_moi"]), {"nen_tang": ten})
    in_ra(f"  {ten:<14} {bao['repo']} repo, {bao['file_thay']} file, "
          f"{bao['ghi_moi']} moi, {bao['da_co']} da co")
    return bao


def cua_hang_ctrader(in_ra=print) -> dict:
    """cTrader Store -> siêu du lieu HIEU SUAT (khong co ma nguon).

    Tra `profitFactor`, `maxDrawdownPercent`, `monthlyRoiPercent` do chinh tac
    gia khai. Day la LOI KHOE, khong phai ket qua da kiem dinh - xep cung ro
    voi mql5_signals, khong duoc dung lam co che.
    """
    import json
    import re

    import requests
    try:
        r = requests.get("https://ctrader.com/algos/cbots/", timeout=30,
                         headers={"User-Agent": UA})
        m = re.search(r"__NEXT_DATA__[^>]*>(\{.*?\})</script>", r.text, re.S)
        d = json.loads(m.group(1))
        sp = d["props"]["pageProps"]["initialState"]["product"]["data"]
    except Exception as e:
        return {"loi": f"{type(e).__name__}: {str(e)[:90]}"}
    ra = []
    for p in sp.values():
        ra.append({"ten": p.get("title"), "tac_gia": p.get("userNick"),
                   "nguoi_dung": p.get("userCount"),
                   "pf_khai": p.get("profitFactor"),
                   "dd_khai": p.get("maxDrawdownPercent"),
                   "roi_thang_khai": p.get("monthlyRoiPercent"),
                   "url": f"https://ctrader.com/algos/cbots/{p.get('productId')}/"})
    in_ra(f"  cTrader Store: {len(ra)} cBot (chi sieu du lieu hieu suat)")
    return {"so": len(ra), "muc": ra}


def quet_het(so_repo: int = 3, in_ra=print) -> dict:
    """Quet MOI nen tang trong so dang ky, uu tien theo tru luong do duoc."""
    thu_tu = sorted(NEN_TANG, key=lambda t: -(NEN_TANG[t].get("tru_luong") or 50))
    bao = {"nen_tang": {}, "tong_ghi_moi": 0}
    for t in thu_tu:
        r = thu_thap(t, so_repo=so_repo, in_ra=in_ra)
        bao["nen_tang"][t] = r
        bao["tong_ghi_moi"] += int(r.get("ghi_moi") or 0)
    in_ra(f"NEN TANG: {bao['tong_ghi_moi']} artifact moi")
    return bao
