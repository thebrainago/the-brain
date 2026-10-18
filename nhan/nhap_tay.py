# -*- coding: utf-8 -*-
"""nhap_tay.py - THU MUC NHAP TAY cua chu du an (18/10/2026).

Trang bi chan (Cloudflare, captcha, can dang nhap, render JS) thi KHONG vuot: chu du an tu mo bang Chrome cua minh, roi luu
vao thu muc nhap tay (vd tren may nha `E:\\brain2_nhap\\`). Cac loai nhan duoc:
  - EA / chi bao / thu vien: .mq4 .mq5 .mqh (va .ex4/.ex5 chi co ban bien dich -> chay thang MT5);
  - bo thong so: .set (gan voi EA cung ten neu co);
  - statement / bao cao tester: .htm .html (MT4 statement, MT5 report) -> danh sach lenh + dau hieu xu li lenh;
  - trang HTML luu tu trinh duyet -> tach khoi ma MQL (OnTick/OnInit) neu co, khong thi ghi la mo ta;
  - Python / Pine: .py .pine .txt (Pine) -> duong LLM.
Ham o day CHI DOC VAN BAN, khong bao gio chay ma nhap vao. Ma cua nguoi khac khong vao git: ban tach ra ghi vao
`data/nhap_tay/_tach/` (git bo qua). Thu muc cau hinh: bien moi truong BRAIN_NHAP_TAY (nhieu thu muc cach nhau `;`), neu
khong co thi `thu_muc_nhap_tay` trong config/ong_dan.json.
"""
from __future__ import annotations

import hashlib
import html as H
import json
import os
import re
from pathlib import Path

import pandas as pd

GOC = Path(__file__).resolve().parent.parent
TACH = GOC / "data" / "nhap_tay" / "_tach"
DUOI = {".mq4": "MQL4", ".mq5": "MQL5", ".mqh": "MQL5", ".ex4": "MQL4_EX", ".ex5": "MQL5_EX", ".set": "SET",
        ".htm": "HTML", ".html": "HTML", ".py": "Python", ".pine": "TradingView", ".txt": "TXT", ".csv": "CSV",
        ".zip": "ZIP"}
TRAN_BYTE = 20 * 1024 * 1024
_TG = r"(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}(?::\d{2})?)"


#: Thu muc nhap tay mac dinh. `data/seeker_da_nguon/nhap_tay/<nguon>/<id>.<duoi>` la quy uoc cua tac vu Seeker da nguon
#: (reports/URL_BI_CHAN.md) - o day CHI DOC, khong ghi vao do.
MAC_DINH = ["E:\\brain2_nhap", "data/nhap_tay", "data/seeker_da_nguon/nhap_tay"]


def thu_muc(cfg: dict | None = None) -> list[Path]:
    """Danh sach thu muc nhap tay dang ton tai (env BRAIN_NHAP_TAY > config)."""
    env = os.environ.get("BRAIN_NHAP_TAY")
    ds = env.split(";") if env else list((cfg or {}).get("thu_muc_nhap_tay") or MAC_DINH)
    ra = []
    for x in ds:
        x = x.strip()
        if not x:
            continue
        p = Path(x)
        if not p.is_absolute():
            p = GOC / p
        if p.exists() and p.is_dir():
            ra.append(p)
    return ra


def doc_vb(b: bytes) -> str:
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return b.decode("utf-16", errors="ignore")
    if len(b) > 8 and b[1:8:2] == b"\x00\x00\x00\x00":
        return b.decode("utf-16-le", errors="ignore")
    return b.decode("utf-8", errors="ignore")


def doc_set(vb: str) -> dict:
    """.set MT4/MT5 -> {ten: gia tri dau} (bo phan ||start||step||stop||Y)."""
    d = {}
    for dong in vb.splitlines():
        dong = dong.strip()
        if not dong or dong.startswith(";") or "=" not in dong:
            continue
        k, v = dong.split("=", 1)
        d[k.strip()] = v.split("||")[0].strip()
    return d


def _o(row: str) -> list[str]:
    return [H.unescape(re.sub(r"<[^>]+>", "", c)).strip().replace("\xa0", " ")
            for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S | re.I)]


def _so(x: str) -> float | None:
    try:
        return float(str(x).split("/")[0].replace(" ", ""))
    except ValueError:
        return None


def _tg(x: str):
    return pd.to_datetime(str(x).replace(".", "-", 2), errors="coerce")


def doc_lenh_html(vb: str) -> pd.DataFrame:
    """Statement / report -> lenh VAO [luc, het, ma, chieu, lot] (het = luc dong neu biet). Ho tro:
    MT5 report (Deals: Time | Deal | Symbol | Type | Direction | Volume ...; out khop FIFO theo chieu, kieu hedging),
    MT4 statement (Ticket | Open Time | Type | Size | Item | Price | S/L | T/P | Close Time ...). Khong nhan ra -> rong."""
    hang, mo = [], {}
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", vb, re.S | re.I):
        c = _o(row)
        if len(c) < 6:
            continue
        if re.fullmatch(_TG, c[0]) and len(c) >= 7 and c[3].lower() in ("buy", "sell") and c[4].lower() in ("in", "out", "inout"):
            ch = 1 if c[3].lower() == "buy" else -1
            lot = _so(c[5]) or 0.0
            if c[4].lower() in ("in", "inout"):
                hang.append({"luc": _tg(c[0]), "het": pd.NaT, "ma": c[2], "chieu": ch, "lot": lot})
                mo.setdefault((c[2], ch), []).append([len(hang) - 1, lot])
            if c[4].lower() in ("out", "inout"):
                con = lot                       # deal out chieu `ch` dong vi the chieu nguoc lai, FIFO
                q = mo.get((c[2], -ch), [])
                while con > 1e-9 and q:
                    k, l = q[0]
                    d = min(con, l)
                    con -= d
                    q[0][1] -= d
                    if q[0][1] <= 1e-9:
                        hang[k]["het"] = _tg(c[0])
                        q.pop(0)
            continue
        if re.fullmatch(r"\d+", c[0]) and re.fullmatch(_TG, c[1]) and c[2].lower() in ("buy", "sell"):
            het = _tg(c[8]) if len(c) > 8 and re.fullmatch(_TG, c[8]) else pd.NaT
            hang.append({"luc": _tg(c[1]), "het": het, "ma": c[4], "chieu": 1 if c[2].lower() == "buy" else -1,
                         "lot": _so(c[3])})
    if not hang:
        return pd.DataFrame(columns=["luc", "het", "ma", "chieu", "lot"])
    df = pd.DataFrame(hang)
    return df.dropna(subset=["luc"]).sort_values("luc").reset_index(drop=True)


def doc_lenh_csv(vb: str) -> pd.DataFrame:
    """Lich su lenh xuat CSV (MQL5 Signals Export, Myfxbook, FX Blue, ...) -> [luc, het, ma, chieu, lot]. Doan cot theo ten."""
    import io
    try:
        df = pd.read_csv(io.StringIO(vb), sep=None, engine="python")
    except Exception:
        return pd.DataFrame(columns=["luc", "het", "ma", "chieu", "lot"])
    cot = {c: str(c).strip().lower() for c in df.columns}
    tg = [c for c, l in cot.items() if ("time" in l or "date" in l) and "duration" not in l]
    kieu = None
    for c in df.columns:
        v = df[c].astype(str).str.strip().str.lower()
        if len(v) and (v.str.startswith("buy") | v.str.startswith("sell")).mean() >= 0.5:
            kieu = c
            break
    ma = next((c for c, l in cot.items() if any(k in l for k in ("symbol", "item", "instrument"))), None)
    lot = next((c for c, l in cot.items() if any(k in l for k in ("volume", "lot", "size", "units"))), None)
    if not tg or kieu is None or ma is None:
        return pd.DataFrame(columns=["luc", "het", "ma", "chieu", "lot"])
    v = df[kieu].astype(str).str.strip().str.lower()
    df = df[v.str.startswith("buy") | v.str.startswith("sell")]
    v = v.loc[df.index]
    ra = pd.DataFrame({"luc": pd.to_datetime(df[tg[0]].astype(str).str.replace(".", "-", n=2, regex=False), errors="coerce"),
                       "het": pd.to_datetime(df[tg[1]].astype(str).str.replace(".", "-", n=2, regex=False), errors="coerce")
                       if len(tg) > 1 else pd.NaT,
                       "ma": df[ma].astype(str), "chieu": v.map(lambda x: 1 if x.startswith("buy") else -1),
                       "lot": pd.to_numeric(df[lot], errors="coerce") if lot else None})
    return ra.dropna(subset=["luc"]).sort_values("luc").reset_index(drop=True)


def ma_goc(sym: str) -> str:
    """AUDCADmicro / EURUSDc / XAUUSD# -> AUDCAD / EURUSD / XAUUSD."""
    m = re.match(r"([A-Za-z]{6})", sym or "")
    return m.group(1).upper() if m else (sym or "").upper()


def dau_hieu_lenh(df: pd.DataFrame) -> dict:
    """Suy ky thuat xu li lenh TU DANH SACH LENH (SUY TU STATEMENT, khong phai so do). Lenh chua biet luc dong coi nhu
    con mo 24 h.
    - dca / luoi: cung luc co >= 3 lenh cung chieu cung ma dang mo;
    - martingale: trong mot chuoi chong do, lot lenh sau > lot lenh truoc;
    - hedge: cung luc co lenh mua va lenh ban cung ma dang mo."""
    ra = {"so_lenh_vao": int(len(df)), "ma": sorted({ma_goc(x) for x in df["ma"]}) if len(df) else [], "ky_thuat": []}
    if not len(df):
        return ra
    het = df["het"].where(df["het"].notna(), df["luc"] + pd.Timedelta(hours=24))
    chong_max, mg, hedge = 1, False, False
    for _, g in df.assign(het_tinh=het, ma_g=df["ma"].map(ma_goc)).groupby("ma_g"):
        g = g.sort_values("luc")
        rows = list(g.itertuples())
        for i, r in enumerate(rows):
            dang = [x for x in rows[:i] if x.het_tinh > r.luc]
            cung = [x for x in dang if x.chieu == r.chieu]
            chong_max = max(chong_max, len(cung) + 1)
            if cung and r.lot and cung[-1].lot and r.lot > cung[-1].lot * 1.05:
                mg = True
            if any(x.chieu != r.chieu for x in dang):
                hedge = True
    ra["chong_cung_chieu_max"] = int(chong_max)
    if chong_max >= 3:
        ra["ky_thuat"].append("dca")
    if mg:
        ra["ky_thuat"].append("martingale")
    if hedge:
        ra["ky_thuat"].append("hedge")
    return ra


def tach_ma_html(vb: str) -> str:
    """Khoi ma MQL trong trang HTML luu tay (<pre>, <code>, <textarea>) co OnTick/OnInit/OnCalculate -> van ban ma."""
    khoi = re.findall(r"<(pre|code|textarea)[^>]*>(.*?)</\1>", vb, re.S | re.I)
    tot = ""
    for _, k in khoi:
        t = H.unescape(re.sub(r"<[^>]+>", "", k))
        if re.search(r"\bOn(Tick|Init|Calculate|Start)\s*\(", t) and len(t) > len(tot):
            tot = t
    return tot


def _sha(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()[:16]


def la_bao_cao(vb: str) -> bool:
    v = vb[:200000]
    return bool(re.search(r"Strategy Tester Report|Closed Transactions|Statement|Báo cáo|Deals", v)) and \
        bool(re.search(r"Profit|Lợi nhuận", v))


def quet(cac_thu_muc: list[Path], da_co: set[str] | None = None) -> list[dict]:
    """Quet thu muc nhap tay -> list THE (dang cua nhan/ong_dan). `da_co`: id the da nhan (bo qua)."""
    da_co = da_co or set()
    tep = []
    for d in cac_thu_muc:
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.suffix.lower() in DUOI and TACH not in p.parents and p.stat().st_size <= TRAN_BYTE:
                tep.append(p)
    theo_ten = {}
    for p in tep:
        theo_ten.setdefault(p.stem.lower(), []).append(p)
    the = []
    TACH.mkdir(parents=True, exist_ok=True)
    # .zip: chi GIAI NEN (khong chay gi) cac file co duoi nhan duoc vao _tach/<sha>/, roi xu li nhu file thuong
    for p in [q for q in tep if q.suffix.lower() == ".zip"]:
        import zipfile
        try:
            d = TACH / ("zip_" + _sha(p.read_bytes()))
            with zipfile.ZipFile(p) as z:
                for nf in z.namelist():
                    q = Path(nf)
                    if q.suffix.lower() in DUOI and q.suffix.lower() != ".zip" and ".." not in q.parts and not q.is_absolute():
                        info = z.getinfo(nf)
                        if info.file_size <= TRAN_BYTE:
                            (d / q).parent.mkdir(parents=True, exist_ok=True)
                            (d / q).write_bytes(z.read(nf))
            tep += [x for x in sorted(d.rglob("*")) if x.is_file()]
        except Exception:
            continue
    tep = [q for q in tep if q.suffix.lower() != ".zip"]
    for p in tep:
        b = p.read_bytes()
        sha = _sha(b)
        tid = "nhap_" + sha
        if tid in da_co:
            continue
        duoi = p.suffix.lower()
        loai_tep = DUOI[duoi]
        mu = re.match(r"(U[0-9a-f]{6})(?:[_\- .]|$)", p.name)       # ma dong trong reports/URL_BI_CHAN.md
        goc = {"id": tid, "ten": "Nhập tay: %s" % p.name, "nguon": {"kho": "nhap_tay", "tep": str(p), "url": ""},
               "nhap_tay": {"tep": str(p), "loai_tep": loai_tep, "sha1": sha, "ma_url": mu.group(1) if mu else None,
                            "ten_goc": p.stem, "nguon_tay": p.parent.name},
               "nhan": ["NHẬP TAY"]}
        if loai_tep in ("MQL4", "MQL5"):
            vb = doc_vb(b)
            goc["nen_tang"] = loai_tep
            sets = [q for q in theo_ten.get(p.stem.lower(), []) if q.suffix.lower() == ".set"]
            if sets:
                goc["set_goc"] = doc_set(doc_vb(sets[0].read_bytes()))
            if not re.search(r"\bOnTick\s*\(", vb):
                goc["loai_kiem_ke"] = "chi_bao" if re.search(r"\bOnCalculate\s*\(", vb) else "thu_vien"
        elif loai_tep in ("MQL4_EX", "MQL5_EX"):
            goc.update(nen_tang=loai_tep.split("_")[0], chi_bien_dich=True, loai_kiem_ke="ea",
                       ghi_chu="chỉ có file biên dịch: chạy thẳng MT5 trên máy nhà")
        elif loai_tep == "SET":
            ten_ea = [q for q in theo_ten.get(p.stem.lower(), []) if q.suffix.lower() in (".mq4", ".mq5", ".ex4", ".ex5")]
            if ten_ea:
                continue                                  # da gan vao the EA cung ten
            goc.update(nen_tang="SET", loai_kiem_ke="tham_so", set_goc=doc_set(doc_vb(b)))
        elif loai_tep == "HTML":
            vb = doc_vb(b)
            if la_bao_cao(vb):
                df = doc_lenh_html(vb)
                dh = dau_hieu_lenh(df)
                f = TACH / ("%s_lenh.csv" % sha)
                df[["luc", "ma", "chieu", "lot"]].to_csv(f, index=False)
                goc.update(nen_tang="STATEMENT", loai_kiem_ke="lich_su_lenh", dau_hieu=dh,
                           quan_tri_goc=dh["ky_thuat"], tin_hieu={"kieu": "lenh_ngoai", "tep": str(f), "ma": dh["ma"], "khoang": {}})
            else:
                ma = tach_ma_html(vb)
                if ma:
                    nt = "MQL4" if re.search(r"\bstart\s*\(|OrderSend\s*\([^)]*,\s*OP_", ma) else "MQL5"
                    f = TACH / ("%s.%s" % (sha, "mq4" if nt == "MQL4" else "mq5"))
                    f.write_text(ma, encoding="utf-8")
                    goc.update(nen_tang=nt, nguon={"kho": "nhap_tay", "tep": str(f), "url": "", "trang_goc": str(p)})
                else:
                    goc.update(nen_tang="HTML", loai_kiem_ke="mo_ta")
        elif loai_tep == "CSV":
            df = doc_lenh_csv(doc_vb(b))
            if len(df):
                dh = dau_hieu_lenh(df)
                f = TACH / ("%s_lenh.csv" % sha)
                df[["luc", "ma", "chieu", "lot"]].to_csv(f, index=False)
                goc.update(nen_tang="STATEMENT", loai_kiem_ke="lich_su_lenh", dau_hieu=dh, quan_tri_goc=dh["ky_thuat"],
                           tin_hieu={"kieu": "lenh_ngoai", "tep": str(f), "ma": dh["ma"], "khoang": {}})
            else:
                goc.update(nen_tang="CSV", loai_kiem_ke="mo_ta")
        elif loai_tep == "Python":
            goc["nen_tang"] = "Python"
        else:  # .pine / .txt
            vb = doc_vb(b)
            goc["nen_tang"] = "TradingView" if (duoi == ".pine" or re.search(r"//@version=\d", vb)) else "TXT"
            if goc["nen_tang"] == "TXT":
                goc["loai_kiem_ke"] = "mo_ta"
        the.append(goc)
    return the


def tin_hieu_lenh_ngoai(th: dict, df: pd.DataFrame, ma: str) -> "np.ndarray":
    """Lenh tu statement -> tin hieu tren nen `df` cua `ma`: lenh luc T -> s[i] o nen co open[i+1] la nen dau >= T."""
    import numpy as np
    s = np.zeros(len(df), int)
    try:
        lenh = pd.read_csv(th["tep"], parse_dates=["luc"])
    except Exception:
        return s
    lenh = lenh[lenh["ma"].map(ma_goc) == ma.upper()]
    if not len(lenh):
        return s
    j = df.index.searchsorted(pd.DatetimeIndex(lenh["luc"]))      # nen dau tien >= T
    for k, ch in zip(j, lenh["chieu"]):
        if 1 <= k < len(df):
            s[k - 1] = int(ch)
    return s
