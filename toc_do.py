# -*- coding: utf-8 -*-
"""toc_do.py - Bo dem tan so quet (rate limiter) chong spam/block tung nguon.
Moi nguon co: ngu (giay giua 2 yeu cau), gioi_han_gio, gioi_han_phut,
doi_429 (giay cho khi bi 429/403). Neu vuot -> cho tu dong (khong thuc su spam).
"""
import json, time, random, threading
from pathlib import Path

CFG = Path(__file__).parent / "config" / "tan_so_quet.json"

MAC_DINH = {
    "github":         {"ngu": 2.0, "gioi_han_gio": 50,  "gioi_han_phut": 8,  "doi_429": 600},
    "github_search":  {"ngu": 7.0, "gioi_han_gio": 28,  "gioi_han_phut": 5,  "doi_429": 600},
    "mql5":           {"ngu": 2.0, "gioi_han_gio": 120, "gioi_han_phut": 20, "doi_429": 300},
    "arxiv":          {"ngu": 3.0, "gioi_han_gio": 900, "gioi_han_phut": 40, "doi_429": 120},
    "huggingface":    {"ngu": 5.0, "gioi_han_gio": 500, "gioi_han_phut": 30, "doi_429": 300},
    "reddit":         {"ngu": 7.0, "gioi_han_gio": 30,  "gioi_han_phut": 5,  "doi_429": 600},
    "web":            {"ngu": 2.0, "gioi_han_gio": 300, "gioi_han_phut": 30, "doi_429": 300},
    "wccta":          {"ngu": 15.0,"gioi_han_gio": 60,  "gioi_han_phut": 8,  "doi_429": 600},
    "prop":           {"ngu": 20.0,"gioi_han_gio": 40,  "gioi_han_phut": 6,  "doi_429": 600},
    "browser":        {"ngu": 30.0,"gioi_han_gio": 40,  "gioi_han_phut": 6,  "doi_429": 300},
}


def _tai_cfg():
    if CFG.exists():
        try:
            c = json.loads(CFG.read_text(encoding="utf-8"))
            for k in MAC_DINH:
                c.setdefault(k, MAC_DINH[k])
            return c
        except Exception:
            pass
    return dict(MAC_DINH)


class TocDo:
    """Dieu khien toc do quet theo nguon. Dung chung 1 doi tuong cho toan bo."""
    def __init__(self):
        self.cfg = _tai_cfg()
        self._lock = threading.Lock()
        self._last = {}          # nguon -> thoi diem yeu cau gan nhat
        self._gio = {}           # nguon -> [thoi diem, ...] trong 1 gio
        self._phut = {}          # nguon -> [thoi diem, ...] trong 1 phut
        self._doi_den = {}       # nguon -> thoi diem duoc quay lai (backoff)

    def _thong_tin(self, nguon):
        return self.cfg.get(nguon, MAC_DINH["web"])

    def cho(self, nguon):
        """Cho den khi hop le; tra ve so giay da cho. Khong bao gio spam."""
        tt = self._thong_tin(nguon)
        now = time.time()
        with self._lock:
            # backoff 429
            if self._doi_den.get(nguon, 0) > now:
                cho = self._doi_den[nguon] - now
                self._doi_den[nguon] = now + cho + 1
                time.sleep(cho)
                return cho
            # min interval
            kc = tt["ngu"] - (now - self._last.get(nguon, 0))
            if kc > 0:
                time.sleep(kc + random.uniform(0, 0.4))
            self._last[nguon] = time.time()
            # window caps
            now = time.time()
            self._gio.setdefault(nguon, []); self._phut.setdefault(nguon, [])
            self._gio[nguon] = [t for t in self._gio[nguon] if now - t < 3600]
            self._phut[nguon] = [t for t in self._phut[nguon] if now - t < 60]
            gh = tt.get("gioi_han_gio", 10**9); gp = tt.get("gioi_han_phut", 10**9)
            if len(self._gio[nguon]) >= gh or len(self._phut[nguon]) >= gp:
                # dung cho khi het hanh trang: cho qua gio/phut
                wait = 3600 - (now - self._gio[nguon][0]) if len(self._gio[nguon]) >= gh else 60 - (now - self._phut[nguon][0])
                time.sleep(max(wait, 1))
                now = time.time()
            self._gio[nguon].append(time.time())
            self._phut[nguon].append(time.time())
            return 0.0

    def doi_429(self, nguon):
        """Khi gap 429/403: set backoff."""
        tt = self._thong_tin(nguon)
        with self._lock:
            self._doi_den[nguon] = time.time() + tt.get("doi_429", 300)

    def thong_ke(self):
        return {k: {"last": round(self._last.get(k, 0), 1) if k in self._last else None,
                    "trong_gio": len(self._gio.get(k, []))} for k in self.cfg}


TOC_DO = TocDo()


def lay(url, nguon="web", headers=None, timeout=30, **kw):
    """Yeu cau GET di qua bo dem toc do. Tra None neu bi chan/loi."""
    import requests
    TOC_DO.cho(nguon)
    try:
        r = requests.get(url, headers=headers, timeout=timeout, **kw)
        if r.status_code in (429, 403):
            TOC_DO.doi_429(nguon)
            return None
        r.raise_for_status()
        return r
    except Exception:
        return None
