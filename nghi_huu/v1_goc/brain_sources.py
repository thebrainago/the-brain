# -*- coding: utf-8 -*-
"""
brain_sources.py - THU THAP CHIEN LUOC TU CAC NGUON HOP LE cho The Brain
=====================================================================================
NGUYEN TAC CHON NGUON (quan trong hon danh sach nguon):

  UU TIEN 1 - HOC THUAT (arXiv q-fin, SSRN): chien luoc o day di kem **co che kinh te** va
  thuong co kiem chung out-of-sample/da thi truong. Do dung la thu ma so dang ky cua The Brain
  BAT BUOC phai co (`ly_do_kinh_te`). Mot bai q-fin tot gia tri hon 1000 script an danh.

  UU TIEN 2 - GITHUB repo co GIAY PHEP RO: doc duoc code that, biet ai viet, dung duoc hop phap.

  KHONG CAO: TradingView va MQL5 CodeBase. Dieu khoan hai noi cam thu thap tu dong va ho chan
  chu dong (da gap 403 khi thu). Thay vao do: thu muc `nap_tay/` - chu du an tu lay ve hop le
  (nhu da lam voi pineturtle.txt) roi tha vao, The Brain doc binh thuong.

VI SAO KHONG CAO CANG NHIEU CANG TOT (bang chung tu chinh du an nay, 27/07/2026):
  - 914 phep thu tren 152 tai san -> 0 song sot o cost that.
  - 45 to hop Sonic R -> 0 song sot.
  - 30 phep thu dau tien cua The Brain -> 0 qua FDR.
  Nut that KHONG phai thieu y tuong, ma la y tuong khong song noi qua cost. Cao them 50.000
  script chi lam MAU SO cua FDR phinh len -> lam KHO hon cho chinh nhung y tuong tot.

CLI:
  python brain_sources.py arxiv --tu-khoa "momentum" "mean reversion" --so 15
  python brain_sources.py github --tu-khoa "pine script strategy" --so 20
  python brain_sources.py nap-tay              # liet ke file trong nap_tay/
Xuat: reports/BRAIN_nguon.parquet + reports/BRAIN_nguon.md
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
REPORTS = HERE / "reports"
NAP_TAY = HERE / "nap_tay"
REPORTS.mkdir(exist_ok=True)
NAP_TAY.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (research; contact: local)"}
FILE_NGUON = REPORTS / "BRAIN_nguon.parquet"


def _ctx():
    """SSL context dung chung cho moi request. Python cai qua Windows Store thieu bo chung chi
    goc -> arxiv bao CERTIFICATE_VERIFY_FAILED. Dung certifi neu co (dung cach), KHONG tat
    kiem tra chung chi."""
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=_ctx()) as r:
        return r.read().decode("utf-8", errors="replace")


def arxiv(tu_khoa, so=15):
    """arXiv co API CONG KHAI danh cho truy cap tu dong - dung dung muc dich, khong phai cao len."""
    ra = []
    # Chuyen muc: KHONG duoc chi lay q-fin.TR. Do la "Trading and Market Microstructure",
    # trong khi van chuong thuc nghiem ve lat cat ngang loi suat / du bao loi suat nam o
    # q-fin.ST (Statistical Finance) va q-fin.PM (Portfolio Management). Loc hep khien
    # "cross-section of returns" chi ra DUNG 1 bai - do la loi truy van, khong phai
    # arXiv khong co bai.
    CAT = "(cat:q-fin.TR OR cat:q-fin.ST OR cat:q-fin.PM OR cat:q-fin.GN)"
    for tk in tu_khoa:
        q = urllib.parse.quote(f'{CAT} AND abs:"{tk}"')
        url = (f"http://export.arxiv.org/api/query?search_query={q}"
               f"&max_results={so}&sortBy=submittedDate&sortOrder=descending")
        xml = None
        for lan in range(3):          # may chu arXiv hay het gio, thu lai la duoc
            try:
                xml = _get(url, timeout=90)
                break
            except Exception as e:
                if lan == 2:
                    print(f"  [LOI arxiv] {tk}: {str(e)[:60]}")
                else:
                    time.sleep(8)
        if xml is None:
            continue
        for m in re.finditer(r"<entry>(.*?)</entry>", xml, re.S):
            e = m.group(1)
            def _lay(tag):
                x = re.search(rf"<{tag}>(.*?)</{tag}>", e, re.S)
                return re.sub(r"\s+", " ", x.group(1)).strip() if x else ""
            ra.append({"nguon": "arXiv", "tu_khoa": tk, "ten": _lay("title"),
                       "tac_gia": "; ".join(re.findall(r"<name>(.*?)</name>", e))[:120],
                       "ngay": _lay("published")[:10], "link": _lay("id"),
                       "tom_tat": _lay("summary")[:600], "giay_phep": "arXiv (doc tu do)",
                       "sao": None})
        time.sleep(3)          # ton trong may chu arXiv
    return ra


def github(tu_khoa, so=20):
    """GitHub Search API cong khai (60 request/gio khong can dang nhap). CHI lay repo CO giay phep."""
    ra = []
    for tk in tu_khoa:
        q = urllib.parse.quote(tk)
        url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page={so}"
        try:
            js = json.loads(_get(url))
        except Exception as e:
            print(f"  [LOI github] {tk}: {str(e)[:60]}")
            continue
        for it in js.get("items", []):
            gp = (it.get("license") or {}).get("spdx_id")
            if not gp or gp == "NOASSERTION":
                continue          # khong ro giay phep -> khong dung
            ra.append({"nguon": "GitHub", "tu_khoa": tk, "ten": it["full_name"],
                       "tac_gia": it["owner"]["login"], "ngay": it["created_at"][:10],
                       "link": it["html_url"], "tom_tat": (it.get("description") or "")[:400],
                       "giay_phep": gp, "sao": it.get("stargazers_count")})
        time.sleep(3)
    return ra


def nap_tay():
    """File chu du an tu lay ve hop le roi tha vao nap_tay/ (vd pineturtle.txt)."""
    ra = []
    for fp in sorted(NAP_TAY.glob("*")):
        if fp.is_file():
            ra.append({"nguon": "nap tay", "tu_khoa": "", "ten": fp.name, "tac_gia": "(chu du an nap)",
                       "ngay": datetime.fromtimestamp(fp.stat().st_mtime).date().isoformat(),
                       "link": str(fp), "tom_tat": f"{fp.stat().st_size/1024:.1f} KB",
                       "giay_phep": "(tu xac nhan)", "sao": None})
    return ra


def luu(rows):
    if not rows:
        print("Khong thu duoc gi."); return
    df = pd.DataFrame(rows)
    if FILE_NGUON.exists():
        df = pd.concat([pd.read_parquet(FILE_NGUON), df], ignore_index=True)
    df = df.drop_duplicates(subset=["nguon", "link"], keep="last").reset_index(drop=True)
    df.to_parquet(FILE_NGUON, index=False)
    md = ["# THE BRAIN - kho nguon chien luoc", "",
          f"Cap nhat {datetime.now():%Y-%m-%d %H:%M}. **{len(df)} muc** tu "
          f"{df['nguon'].nunique()} nguon.", "",
          "> Day moi la DANH SACH UNG VIEN. Muon vao so dang ky (`brain_strategies.py`) thi phai "
          "co du: quy tac cu the + tham so cua tac gia + **ly do kinh te**. Khong du -> khong nap.", ""]
    for ng, nhom in df.groupby("nguon"):
        md += [f"## {ng} ({len(nhom)})", ""]
        for _, r in nhom.sort_values("ngay", ascending=False).head(40).iterrows():
            sao = f" ⭐{int(r['sao'])}" if pd.notna(r["sao"]) else ""
            md += [f"- **{r['ten']}**{sao} — {r['tac_gia']} ({r['ngay']}, {r['giay_phep']})",
                   f"  {str(r['tom_tat'])[:300]}", f"  <{r['link']}>", ""]
    (REPORTS / "BRAIN_nguon.md").write_text("\n".join(md), encoding="utf-8")
    print(f"{len(df)} muc -> reports/BRAIN_nguon.md")


# ---------------------------------------------------------------------------
# TU KHOA - sua 09/08/2026 sau khi do duoc ty le trung
# ---------------------------------------------------------------------------
# Bo tu khoa cu ("momentum", "mean reversion", "trading strategy", "market anomaly")
# keo ve 28 bai, DeepSeek doc va BO QUA 25/25 muc dau. Ly do khong phai no kho tinh:
#   - "momentum" va "mean reversion" la DUNG HAI HO du an da dot 12,17 trieu to hop
#     va dong so. 17/28 bai chac chan bi loai ngay tu dau.
#   - "trading strategy" keo ve bai LY THUYET (no-arbitrage, Cantor diagonalization)
#     va bai RL toi uu hoa - khong bai nao chua khang dinh do duoc bang OHLCV.
# Tuc dang cau o dung hai cai ao da can.
#
# Bo moi nham vao van chuong THUC NGHIEM co khang dinh nguyen tu, va uu tien nhung
# thu do duoc bang DUNG cai ta co: 28 thi truong x OHLCV ngay x ~30 nam.
# Chu y "overnight return": ta co open va close, ma phan ra qua dem / trong phien la
# mot trong nhung quy luat thuc nghiem ben nhat da cong bo - va du an CHUA HE cham toi.
TU_KHOA_ARXIV = [
    "overnight return",              # co open+close -> do duoc ngay, chua ai trong du an cham
    "intraday reversal",
    "return predictability",
    "cross-section of returns",      # 28 thi truong CHINH LA mot lat cat ngang
    "lead-lag effect",               # quan he GIUA cac thi truong - chieu chua dung
    "seasonality in returns",
    "limits to arbitrage",
    "volatility risk premium",
    "market anomaly",                # tu khoa cu duy nhat dung loai
]
# GitHub: giu tu khoa cong cu (chung vao so CONG NGHE, khong sinh khang dinh - va do la
# dung vai tro cua chung), them hai tu khoa co the sinh khang dinh that.
TU_KHOA_GITHUB = [
    "pine script strategy", "mql5 expert advisor",
    "algorithmic trading strategy backtest",
    "empirical asset pricing", "market anomalies replication",
]


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="lenh", required=True)
    a = sub.add_parser("arxiv"); a.add_argument("--tu-khoa", nargs="*", default=TU_KHOA_ARXIV)
    a.add_argument("--so", type=int, default=15); a.set_defaults(fn=lambda x: luu(arxiv(x.tu_khoa, x.so)))
    g = sub.add_parser("github"); g.add_argument("--tu-khoa", nargs="*", default=TU_KHOA_GITHUB)
    g.add_argument("--so", type=int, default=20); g.set_defaults(fn=lambda x: luu(github(x.tu_khoa, x.so)))
    n = sub.add_parser("nap-tay"); n.set_defaults(fn=lambda x: luu(nap_tay()))
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
