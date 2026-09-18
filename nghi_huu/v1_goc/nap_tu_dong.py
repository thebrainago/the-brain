# -*- coding: utf-8 -*-
"""
nap_tu_dong.py — NGUOI DOC VA TAI, MAY LAM PHAN CON LAI
=====================================================================================
Van de: chu du an muon mot dong chay chien luoc tu MQL5 CodeBase va TradingView. Hai
trang nay cam thu thap tu dong trong dieu khoan, nen KHONG viet bot gia lam nguoi de
vuot rao. Nhung chu du an la NGUOI THAT va co quyen doc, tai binh thuong.

Cho tac that su khong nam o viec bam chuot. Sang 09/08 co 162 tai lieu da thu thap
nam khong vi KHONG CO GI DOC CHUNG. File nay vá đúng chỗ đó.

CACH DUNG:
  1. Ban duyet CodeBase NGAY TRONG MetaEditor (client chinh thuc cua nha cung cap),
     bam tai cai nao thay dang. File tu roi vao MQL5\\Experts hoac Indicators.
     Hoac ban tai bang trinh duyet nhu binh thuong -> file roi vao Downloads.
  2. File nay thay file moi la tu:
       - go ra khoi .zip/.rar neu can
       - loc bo thu vien chuan cua MetaQuotes (khong phai chien luoc)
       - phan loai co che, bat martingale / repaint / grid
       - TRA SO KHANG DINH: cai nao rut ve ho da dong so thi loai ngay
       - cai nao con lai -> day vao hang ung vien cho vong tu sinh do
  3. Ban khong phai lam gi them.

  python nap_tu_dong.py --quet-mot-lan     # quet het cai dang co roi thoi
  python nap_tu_dong.py --theo-doi         # chay lien tuc, 30 giay quet mot lan
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import time
import zipfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
NAP_TAY = HERE / "nap_tay" / "tu_dong"
REPORTS = HERE / "reports"
SO_DA_NAP = REPORTS / "ds" / "_da_nap_tu_dong.json"
BAO_CAO = REPORTS / "BRAIN_NAP_TU_DONG.md"
NAP_TAY.mkdir(parents=True, exist_ok=True)
(REPORTS / "ds").mkdir(parents=True, exist_ok=True)

DUOI = {".mq5", ".mq4", ".mqh", ".pine", ".txt", ".cs"}   # bo .py: quet Downloads se
                                                          # vo phai code cua chinh du an
NEN = {".zip"}


def cac_thu_muc_theo_doi():
    """Downloads + moi thu muc MQL5 cua moi terminal MT5 tren may."""
    ds = [Path.home() / "Downloads", HERE / "nap_tay"]
    goc = Path(os.environ.get("APPDATA", "")) / "MetaQuotes" / "Terminal"
    if goc.exists():
        for t in goc.iterdir():
            for con in ("Experts", "Indicators", "Scripts", "Files"):
                p = t / "MQL5" / con
                if p.exists():
                    ds.append(p)
    return [d for d in ds if d.exists()]


# Thu vien chuan di kem MT5 - KHONG phai chien luoc, bo qua het.
CHUAN = re.compile(
    r"(\\Include\\|/Include/|\\Examples\\|/Examples/|Copyright 2000-20\d\d, MetaQuotes)",
    re.I)
TEN_CHUAN = {"ExpertMACD", "ExpertMAMA", "ExpertMAPSAR", "MACD Sample", "MovingAverages",
             "Custom Moving Average", "ZigZag", "Heiken Ashi", "ExpertMAPSARSizeOptimized"}

# Ho da dong so cua du an: 35.932 + 12,17 trieu to hop -> 0 song sot.
# Tra so TRUOC khi test, dung nguyen tac cua brain_khang_dinh.py.
DA_DONG = {
    "xu huong / momentum": [r"\bma[_ ]?cross", r"moving average", r"\bmacd\b", r"\bema\b",
                            r"\bsma\b", r"supertrend", r"parabolic", r"\badx\b",
                            r"ichimoku", r"trend[ _]?follow", r"momentum"],
    "moc gia / cau truc": [r"fibonacci", r"\bfibo\b", r"pivot", r"support.{0,3}resistance",
                           r"\bs/r\b", r"order.?block", r"supply.{0,3}demand",
                           r"volume.?profile", r"\bpoc\b", r"breakout"],
}
# Nhung ho CHUA dong - day moi la thu dang doc
CON_MO = {
    "vi cau truc / thanh khoan": [r"order.?flow", r"\bdelta\b", r"liquidity", r"footprint"],
    "quan he cheo": [r"correlation", r"pair.?trad", r"cointegrat", r"spread.?trad",
                     r"inter.?market", r"lead.?lag", r"relative.?strength"],
    "che do / thong ke": [r"regime", r"hidden markov", r"\bhmm\b", r"kalman",
                          r"mean.?revers", r"ornstein", r"hurst"],
    "dong tien / vi the": [r"\bcot\b", r"commitment", r"positioning", r"open.?interest",
                           r"\bfunding\b", r"carry"],
    "su kien / lich": [r"news", r"earnings", r"economic.?calendar", r"seasonal",
                       r"event.?driven", r"rollover"],
}
# Dau hieu nguy hiem - danh nhan, khong phai lenh xoa
NGUY = {
    "martingale": [r"martingal", r"lot.{0,12}(multipl|\*\s*[12]\.)", r"double.{0,8}lot",
                   r"recovery.{0,6}(factor|lot)"],
    "luoi (grid)": [r"\bgrid\b", r"grid.?level", r"grid.?step"],
    "nhoi lenh": [r"pyramid", r"averaging.?down", r"\bdca\b", r"add.?position"],
    "nghi ve lai": [r"repaint", r"zigzag", r"future.?bar", r"look.?ahead"],
    "khong cat lo": [r"ignore.?sl", r"no.?stop.?loss", r"stoploss\s*=\s*0"],
}


def _tai(p, mac_dinh):
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return mac_dinh


def bam(f):
    return hashlib.sha1(f.read_bytes()).hexdigest()[:16]


def go_nen(f, dich):
    ra = []
    try:
        with zipfile.ZipFile(f) as z:
            for ten in z.namelist():
                if Path(ten).suffix.lower() in DUOI:
                    d = dich / f"{f.stem}__{Path(ten).name}"
                    d.write_bytes(z.read(ten))
                    ra.append(d)
    except Exception:
        pass
    return ra


def phan_tich(f):
    """Doc THAN MA NGUON, phan loai co che, tra so khang dinh."""
    try:
        noi = f.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if len(noi) < 300:
        return None
    thap = noi.lower()

    dong, mo, nguy = [], [], []
    for nhom, mau in DA_DONG.items():
        if any(re.search(m, thap) for m in mau):
            dong.append(nhom)
    for nhom, mau in CON_MO.items():
        if any(re.search(m, thap) for m in mau):
            mo.append(nhom)
    for nhan, mau in NGUY.items():
        if any(re.search(m, thap) for m in mau):
            nguy.append(nhan)

    # Rut mo ta cua tac gia neu co
    mt = re.search(r'#property description\s+"([^"]+)"', noi)
    mo_ta = mt.group(1) if mt else ""
    if not mo_ta:
        c = re.search(r"//\|\s*(.{20,120}?)\s*\|", noi)
        mo_ta = c.group(1) if c else ""

    return {"ten": f.name, "duong_dan": str(f), "byte": len(noi),
            "mo_ta": mo_ta[:200], "ho_da_dong": dong, "ho_con_mo": mo, "canh_bao": nguy,
            # Chi DANG DOC neu co ho con mo, HOAC khong rut duoc ve ho nao (co the la moi)
            "dang_doc": bool(mo) or (not dong and not mo)}


def quet_mot_lan(in_ra=True):
    da = _tai(SO_DA_NAP, {})
    moi, dang_doc = [], []

    # Thu muc du an nam BEN TRONG Downloads, nen rglob quet luon ca code cua chinh minh
    # (440 file, gan het la .py cua du an). Loai tru toan bo cay du an, tru nap_tay/.
    tu_minh = HERE.resolve()
    nap_tay_goc = (HERE / "nap_tay").resolve()

    for tm in cac_thu_muc_theo_doi():
        for f in tm.rglob("*"):
            if not f.is_file():
                continue
            fr = f.resolve()
            if tu_minh in fr.parents and nap_tay_goc not in fr.parents and fr.parent != nap_tay_goc:
                continue
            d = f.suffix.lower()
            if d not in DUOI and d not in NEN:
                continue
            if CHUAN.search(str(f)) or f.stem in TEN_CHUAN:
                continue
            if f.stat().st_size > 3_000_000:
                continue
            try:
                h = bam(f)
            except OSError:
                continue
            if h in da:
                continue

            tep = go_nen(f, NAP_TAY) if d in NEN else [f]
            for t in tep:
                if t.suffix.lower() not in DUOI:
                    continue
                kq = phan_tich(t)
                if not kq:
                    continue
                if t.parent != NAP_TAY:
                    dich = NAP_TAY / t.name
                    if not dich.exists():
                        try:
                            shutil.copy2(t, dich)
                        except OSError:
                            pass
                da[h] = {"ten": t.name, "luc": datetime.now().isoformat(timespec="seconds"),
                         **{k: kq[k] for k in ("ho_da_dong", "ho_con_mo", "canh_bao",
                                               "dang_doc", "mo_ta")}}
                moi.append(kq)
                if kq["dang_doc"]:
                    dang_doc.append(kq)

    SO_DA_NAP.write_text(json.dumps(da, ensure_ascii=False, indent=1), encoding="utf-8")

    if in_ra and moi:
        print(f"\n{len(moi)} file moi | {len(dang_doc)} dang doc ky")
        for k in moi[:40]:
            cd = f"  [{' + '.join(k['canh_bao'])}]" if k["canh_bao"] else ""
            if k["ho_da_dong"] and not k["ho_con_mo"]:
                print(f"  LOAI  {k['ten'][:44]:<44} <- {', '.join(k['ho_da_dong'])}{cd}")
            else:
                mo = ", ".join(k["ho_con_mo"]) or "chua ro ho"
                print(f"  DOC   {k['ten'][:44]:<44} <- {mo}{cd}")
    elif in_ra:
        print("khong co file moi")

    if moi:
        viet_bao_cao(da)
    return moi, dang_doc


def viet_bao_cao(da):
    muc = list(da.values())
    doc = [m for m in muc if m.get("dang_doc")]
    md = ["# NAP TU DONG — nguoi doc va tai, may boc tach", "",
          f"*Cap nhat {datetime.now():%Y-%m-%d %H:%M}. {len(muc)} file da nap, "
          f"{len(doc)} dang doc ky.*", "",
          "> Nguon: thu muc Downloads + MQL5 cua moi terminal MT5 tren may. Ban duyet va",
          "> tai bang tay (MetaEditor hoac trinh duyet); file nay lo phan doc, phan loai,",
          "> tra so khang dinh va day vao hang cho do. Khong cao trang nao.", "",
          "## Dang doc ky (khong rut ve ho da dong so)", "",
          "| file | ho | canh bao | mo ta |", "|---|---|---|---|"]
    for m in doc[:80]:
        md.append(f"| `{m['ten']}` | {', '.join(m.get('ho_con_mo', [])) or '?'} | "
                  f"{', '.join(m.get('canh_bao', [])) or '-'} | {m.get('mo_ta','')[:90]} |")
    loai = [m for m in muc if not m.get("dang_doc")]
    md += ["", f"## Da loai vi rut ve ho dong so ({len(loai)})", "",
           "| file | ho da dong | canh bao |", "|---|---|---|"]
    for m in loai[:80]:
        md.append(f"| `{m['ten']}` | {', '.join(m.get('ho_da_dong', []))} | "
                  f"{', '.join(m.get('canh_bao', [])) or '-'} |")
    BAO_CAO.write_text("\n".join(md), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quet-mot-lan", action="store_true")
    ap.add_argument("--theo-doi", action="store_true")
    ap.add_argument("--nhip", type=int, default=30)
    a = ap.parse_args()

    if a.theo_doi:
        print("Theo doi: " + " | ".join(str(d) for d in cac_thu_muc_theo_doi()))
        print(f"Quet moi {a.nhip}s. Ctrl+C de dung.\n")
        while True:
            try:
                quet_mot_lan()
            except Exception as e:
                print(f"  loi: {str(e)[:100]}")
            time.sleep(a.nhip)
    else:
        quet_mot_lan()
        print(f"\n-> {BAO_CAO}")


if __name__ == "__main__":
    main()
