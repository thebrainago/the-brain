# -*- coding: utf-8 -*-
"""Quet nhieu mql5 signal -> ho so PHONG CACH, roi nhom lai.

Muc 5 cua ban giao 04/09: *"Quet 50-100 mql5 signal dung ho so phong cach,
nhom lai xem co nhom nao giu ngan / cat sach / tai deu khong"*.

VI SAO LOP NGUON NAY KHAC. Luat manh ma cong khai thi da bi an mat - dieu do
dung. Nhung mot tai khoan ban tin hieu buoc phai cong khai duong von, muc tai
va MFE/MAE de nguoi ta dam mua. Ho giau duoc QUY TAC, khong giau duoc DAU CHAN.

SAN PHAM la ho so, KHONG phai co che. Duong tai noi ho vao LUC NAO, khong noi
VI SAO. Ho so thu hep khong gian tim kiem cho `noi_sinh` chu khong tu sinh luat.

BA THUOC DO ma ban giao hoi, dinh nghia cho ro truoc khi do:
  giu ngan : `Avg holding time` trang cong bo, doi ve phut.
  cat sach : ty le |MAE| / MFE tren cac ngay co ca hai. Nho = cat som, khong
             de lo chay. (Don vi risk-json khong phai % von - xem
             `tin_hieu_mql5.rui_ro_json` - nen chi dung lam TY SO, khong ra tien.)
  tai deu  : do lech chuan cua muc tai chia trung binh muc tai. Nho = vao lenh
             deu tay; lon = co nhoi/gong.

Ket qua -> reports/signal_ho_so.json
"""
from __future__ import annotations

import json
import re
import sys
import time
import warnings

sys.path.insert(0, r"C:\Users\SV STORE\Downloads\Research SP500\lab")
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

import numpy as np
import requests

from nhan import tin_hieu_mql5 as TH

RA = "reports/signal_ho_so.json"
SO_TRANG = 6
TRAN = 120       # du cho "50-100 signal" ma ban giao hoi, khong cao hon
NGHI = 0.6

_RX_O = re.compile(
    r'<div class="s-data-columns__label">([^<]{2,40})</div>\s*'
    r'<div class="s-data-columns__value[^"]*"[^>]*>(.{0,80}?)</div>', re.S)
_RX_SYM = re.compile(r"\b([A-Z]{6}|XAU[A-Z]{3}|XAG[A-Z]{3})\b")


def _o_thong_so(html: str) -> dict:
    ra = {}
    for m in _RX_O.finditer(html):
        ra[m.group(1).strip().rstrip(":")] = re.sub(r"<[^>]+>", "",
                                                    m.group(2)).strip()
    return ra


def _phut(s: str | None) -> float | None:
    """'59 minutes' / '2 hours' / '3 days' -> phut."""
    if not s:
        return None
    m = re.search(r"([\d.]+)\s*(minute|hour|day|week|month)", s, re.I)
    if not m:
        return None
    he = {"minute": 1, "hour": 60, "day": 1440, "week": 10080, "month": 43200}
    return float(m.group(1)) * he[m.group(2).lower()]


def _so(s: str | None) -> float | None:
    if not s:
        return None
    m = re.search(r"(-?[\d]+(?:[\s,]\d{3})*(?:\.\d+)?)", s.replace("\xa0", " "))
    return float(m.group(1).replace(",", "").replace(" ", "")) if m else None


def mot(sid: int) -> dict | None:
    try:
        r = TH._lay(f"{TH.GOC}/en/signals/{sid}")
        if r.status_code != 200:
            return None
        h = r.text
    except Exception:
        return None

    o = _o_thong_so(h)
    if not o.get("Trades"):
        return None
    loi_suat, tang = TH.duong_von(h)
    m = TH.phan_loai_mang(h)
    tai = m["tai"][:, 1] if "tai" in m else np.array([])
    tai_co = tai[tai > 0]

    rr = TH.rui_ro_json(sid)
    time.sleep(NGHI)
    cat = None
    if rr:
        cap = [(abs(x["mae"]), x["mfe"]) for x in rr if x["mfe"] > 0 and x["mae"] < 0]
        if len(cap) >= 5:
            cat = float(np.median([a / b for a, b in cap]))

    ten = re.search(r"<title>([^<]+)</title>", h)
    sym = [s for s, _ in
           sorted({s: h.count(s) for s in set(_RX_SYM.findall(h))}.items(),
                  key=lambda kv: -kv[1])][:3]

    dd = None
    for k in ("By Equity", "By Balance", "Maximal"):
        if o.get(k):
            v = re.search(r"([\d.]+)%", o[k])
            if v:
                dd = float(v.group(1))
                break

    return {
        "id": sid,
        "ten": (ten.group(1)[:90] if ten else None),
        "symbol": sym,
        "so_lenh": _so(o.get("Trades")),
        "tuan": _so(o.get("Trades per week")),
        "giu_phut": _phut(o.get("Avg holding time")),
        # "426 (67.51%)" - so dau la SO LENH thang, ty le nam trong ngoac.
        "thang_pct": (lambda m: float(m.group(1)) if m else None)(
            re.search(r"\(([\d.]+)%\)", o.get("Profit Trades") or "")),
        "pf": _so(o.get("Profit Factor")),
        "sharpe": _so(o.get("Sharpe Ratio")),
        "tai_dinh_pct": _so(o.get("Max deposit load")),
        "dd_pct": dd,
        "tang_truong_pct": tang,
        "so_buoc_von": int(len(loi_suat)),
        "cat_sach": (round(cat, 3) if cat is not None else None),
        "tai_deu": (round(float(tai_co.std() / tai_co.mean()), 3)
                    if len(tai_co) > 5 and tai_co.mean() > 0 else None),
        "tai_trung_vi_pct": (round(float(np.median(tai_co)) * 100, 3)
                             if len(tai_co) else None),
    }


def chay() -> None:
    ids: list[int] = []
    for t in range(1, SO_TRANG + 1):
        moi = TH.danh_sach_id(t)
        print("  trang %d: %d id" % (t, len(moi)))
        ids.extend(x for x in moi if x not in ids)
        time.sleep(NGHI)
    ids = ids[:TRAN]
    print("tong id duy nhat (cat con %d): %d" % (TRAN, len(ids)))

    ho, hong = [], 0
    for i, sid in enumerate(ids, 1):
        r = mot(sid)
        if r is None:
            hong += 1
        else:
            ho.append(r)
        if i % 10 == 0:
            print("  ... %d/%d (%d doc duoc, %d hong)" % (i, len(ids), len(ho), hong))
        time.sleep(NGHI)

    json.dump(ho, open(RA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n%d ho so -> %s\n" % (len(ho), RA))
    nhom(ho)


def nhom(ho: list[dict]) -> None:
    def co(k):
        return [x for x in ho if x.get(k) is not None]

    print("=" * 78)
    print("PHAN BO BA THUOC DO")
    for k, ten, don in (("giu_phut", "giu ngan (phut)", ""),
                        ("cat_sach", "cat sach (|MAE|/MFE)", ""),
                        ("tai_deu", "tai deu (lech/TB)", "")):
        v = np.array([x[k] for x in co(k)], float)
        if not len(v):
            print("  %-24s: khong do duoc cai nao" % ten)
            continue
        print("  %-24s: n=%3d  bp25 %8.2f  trung vi %8.2f  bp75 %8.2f"
              % (ten, len(v), np.percentile(v, 25), np.median(v),
                 np.percentile(v, 75)))

    du = [x for x in ho if x.get("giu_phut") is not None
          and x.get("cat_sach") is not None and x.get("tai_deu") is not None]
    print("\n  do du CA BA thuoc do: %d/%d" % (len(du), len(ho)))
    if len(du) < 8:
        print("  qua it de nhom.")
        return

    g = np.array([x["giu_phut"] for x in du], float)
    c = np.array([x["cat_sach"] for x in du], float)
    t = np.array([x["tai_deu"] for x in du], float)
    chon = ((g <= np.median(g)) & (c <= np.median(c)) & (t <= np.median(t)))
    print("  NHOM 'giu ngan + cat sach + tai deu' (ca ba duoi trung vi): %d he"
          % int(chon.sum()))
    print()
    print("  %-8s %-30s %7s %8s %7s %7s %7s %8s"
          % ("id", "symbol", "giu_ph", "cat", "tai_deu", "pf", "sharpe", "tang%"))
    for x in sorted([d for d, k in zip(du, chon) if k],
                    key=lambda z: -(z.get("tang_truong_pct") or -9))[:20]:
        print("  %-8d %-30s %7.0f %8.2f %7.2f %7s %7s %8s"
              % (x["id"], ",".join(x["symbol"])[:30], x["giu_phut"],
                 x["cat_sach"], x["tai_deu"], x["pf"], x["sharpe"],
                 (round(x["tang_truong_pct"], 1)
                  if x["tang_truong_pct"] is not None else "-")))
    print()
    print("  LUU Y: day la ho so cua tai khoan CON SONG tren bang xep hang cong")
    print("  khai - thien lech song sot toan phan. Khong duoc doc nhu 'phong cach")
    print("  nay lam ra tien'; chi doc nhu 'phong cach nay ton tai va do duoc'.")


if __name__ == "__main__":
    chay()
