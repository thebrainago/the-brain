# -*- coding: utf-8 -*-
r"""LUỒNG A - NGUỒN DARWINEX (module mới, chỉ tạo file).

Hai nguồn dữ liệu KHÔNG cần API/login:
1. lay_portfolio_ocr()  : chụp màn hình cửa sổ Chrome Darwinex (chạy _chup_darwinex.ps1)
                          rồi Windows OCR (_ocr.ps1), parse các chỉ số portfolio,
                          ghi reports/darwinex_portfolio.json + lưu ảnh png.
2. lay_darwin_cong_khai(): gọi endpoint công khai của trang backtest Darwinex
                          POST /api/filters/products/all (chỉ cần cookie XSRF-Token,
                          không cần đăng nhập) để lấy danh sách DARWIN,
                          ghi reports/darwinex_darwins.json.

Chạy: C:\Users\SV STORE\AppData\Local\Python\bin\python.exe darwinex_ocr.py
"""
import json
import pathlib
import re
import subprocess
import sys
import time

LAB = pathlib.Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
REPORTS = LAB / "reports"
CHUP_PS1 = LAB / "_chup_darwinex.ps1"
OCR_PS1 = LAB / "_ocr.ps1"
SCREEN_PNG = REPORTS / "screen.png"
PORTFOLIO_JSON = REPORTS / "darwinex_portfolio.json"
PORTFOLIO_PNG = REPORTS / "darwinex_portfolio.png"
DARWINS_JSON = REPORTS / "darwinex_darwins.json"

BASE = "https://www.darwinex.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
TIMEOUT = 60
RETRY = 3

# --- HTTP helpers (requests, fallback urllib) --------------------------------
try:
    import requests
    _REQUESTS = True
except ImportError:
    _REQUESTS = False
    import urllib.request
    import urllib.parse
    import ssl


def _http_get(url, headers=None, timeout=TIMEOUT, session=None):
    last = None
    for _ in range(RETRY):
        try:
            if _REQUESTS:
                r = (session or requests).get(url, headers=headers, timeout=timeout)
                return r.status_code, r.content, r.headers
            req = urllib.request.Request(url, headers=headers or {"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout,
                                        context=ssl.create_default_context()) as res:
                return res.status, res.read(), dict(res.headers)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2)
    raise last


def _http_post_json(url, payload, headers=None, timeout=TIMEOUT, session=None):
    last = None
    for _ in range(RETRY):
        try:
            if _REQUESTS:
                r = (session or requests).post(url, json=payload, headers=headers, timeout=timeout)
                return r.status_code, r.content, r.headers
            data = json.dumps(payload).encode("utf-8")
            h = dict(headers or {})
            h.setdefault("Content-Type", "application/json")
            h.setdefault("User-Agent", UA)
            req = urllib.request.Request(url, data=data, headers=h, method="POST")
            with urllib.request.urlopen(req, timeout=timeout,
                                        context=ssl.create_default_context()) as res:
                return res.status, res.read(), dict(res.headers)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2)
    raise last


def _run_ps(script):
    """Chay script powershell, tra ve stdout."""
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-File", str(script)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    return proc.stdout, proc.stderr


# --- 1) OCR PORFOLIO ---------------------------------------------------------
def _parse_portfolio(text):
    """Parse OCR text -> dict cac chi so portfolio."""
    out = {"raw_ocr_lines": [l for l in text.splitlines() if l.strip()], "metrics": {}}
    text_l = text.lower()
    # alias: label -> khoa chuan
    aliases = {
        "equity": "equity",
        "available": "available",
        "invested": "invested",
        "darwin": "darwin",
        "leverage": "leverage",
        "drawdown": "drawdown",
        "balance": "balance",
        "profit": "profit",
        "free margin": "free_margin",
        "margin": "margin",
    }
    num_re = re.compile(r"([\$€£]?\s?[0-9][0-9.,]*%?|[0-9]+\s*[:]\s*[0-9]+)")
    for alias, key in aliases.items():
        for m in re.finditer(re.escape(alias), text_l):
            window = text_l[m.end():m.end() + 40]
            mm = num_re.search(window)
            if mm:
                out["metrics"][key] = mm.group(1).strip()
                break
    # nhung so tien dau tien trong dong chua "equity"
    eq = re.search(r"equity[^\n]{0,60}?([\$€£]?\s?[0-9][0-9.,]*)", text_l)
    if eq:
        out["metrics"]["equity"] = eq.group(1).strip()
    return out


def lay_portfolio_ocr():
    """Chup man hinh Chrome Darwinex + OCR windows, parse chi so portfolio."""
    REPORTS.mkdir(parents=True, exist_ok=True)
    result = {"nguon": "darwinex_portfolio_ocr", "thoi_gian": time.strftime("%Y-%m-%d %H:%M:%S")}
    # 1) chup man hinh
    try:
        out, err = _run_ps(CHUP_PS1)
        result["chup_log"] = (out + err).strip()
    except Exception as e:  # noqa: BLE001
        result["chup_log"] = "LOI chup: " + str(e)
    # luu ban sao png
    if SCREEN_PNG.exists():
        try:
            import shutil
            shutil.copyfile(SCREEN_PNG, PORTFOLIO_PNG)
            result["png"] = str(PORTFOLIO_PNG)
        except Exception as e:  # noqa: BLE001
            result["png"] = "LOI luu png: " + str(e)
    # 2) OCR
    try:
        out, err = _run_ps(OCR_PS1)
        result["ocr_log"] = (err or "").strip()
        ocr_text = out or ""
        result["ocr_len"] = len(ocr_text)
        parsed = _parse_portfolio(ocr_text)
        result.update(parsed)
        if "metrics" in parsed: result["co_du_lieu"] = bool(parsed["metrics"])
        # ghi raw text ke ben png
        (REPORTS / "darwinex_portfolio_ocr.txt").write_text(ocr_text, encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        result["ocr_log"] = "LOI OCR: " + str(e)
        result["co_du_lieu"] = False
    PORTFOLIO_JSON.write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result


# --- 2) DARWIN CONG KHAI -----------------------------------------------------
def _xsrf_session():
    """Doc XSRF-Token cookie tu trang backtest (khong can dang nhap)."""
    if _REQUESTS:
        s = requests.Session()
        s.headers["User-Agent"] = UA
        s.get(BASE + "/darwins-backtest", timeout=TIMEOUT)
        raw = s.cookies.get("XSRF-TOKEN")
        dec = requests.utils.unquote(raw or "")
        return s, dec
    # fallback urllib
    import http.cookiejar
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.open(BASE + "/darwins-backtest", timeout=TIMEOUT)
    dec = ""
    for c in jar:
        if c.name == "XSRF-TOKEN":
            dec = urllib.parse.unquote(c.value)
    return opener, dec


def _fetch_darwins(s, xsrf, page, size=50):
    url = BASE + "/api/filters/products/all"
    payload = {
        "combineWithFav": False, "customIDs": None, "predefinedIDs": None,
        "page": page, "size": size, "orderField": "tsscore",
        "order": "DESC", "period": "2Y"}
    headers = {
        "User-Agent": UA,
        "X-XSRF-TOKEN": xsrf,
        "X-Requested-With": "XMLHttpRequest",
        "Referer": BASE + "/darwins-backtest",
        "Origin": BASE,
    }
    st, body, _ = _http_post_json(url, payload, headers=headers, session=s)
    if st != 200:
        raise RuntimeError(f"filters/products/all tra enum {st}")
    return json.loads(body.decode("utf-8")) if isinstance(body, bytes) else json.loads(body)


def _shortname(product_name):
    return product_name.split(".")[0]


def lay_darwin_cong_khai(gioi_han_trang=20, size=50, lay_chi_tiet=False):
    """Quet danh sach DARWIN cong khai -> luu reports/darwinex_darwins.json."""
    REPORTS.mkdir(parents=True, exist_ok=True)
    s, xsrf = _xsrf_session()
    danh_sach = []
    last = None
    for page in range(gioi_han_trang):
        try:
            items = _fetch_darwins(s, xsrf, page, size=size)
        except Exception as e:  # noqa: BLE001
            last = str(e)
            break
        if not items:
            break
        for it in items:
            name = it.get("productName", "")
            danh_sach.append({
                "productName": name,
                "darwin": _shortname(name),
                "url": f"{BASE}/darwin/{_shortname(name)}",
                "rankingPosition": it.get("rankingPosition"),
                "currentInvestment": it.get("currentInvestment"),
                "investorsByPeriod": it.get("investorsByPeriod"),
                "returnByPeriod": it.get("returnByPeriod"),
                "drawDownByPeriod": it.get("drawDownByPeriod"),
                "period": it.get("period"),
                "firstQuoteDate": it.get("firstQuoteDate"),
                "dscore": it.get("dscore"),
            })
        if len(items) < size:
            break
        time.sleep(0.4)
    # chi tiet tung DARWIN (risk/type) - tuy chon, de tranh spam mac dinh tat
    if lay_chi_tiet:
        for row in danh_sach:
            try:
                st, body, _ = _http_get(BASE + "/api/products/productname/name/history?shortname=" + urllib_quote(row["darwin"]), session=s)
                if st == 200:
                    arr = json.loads(body.decode("utf-8"))
                    if arr:
                        row["risk"] = arr[0].get("risk")
                        row["type"] = arr[0].get("type")
            except Exception:  # noqa: BLE001
                pass
            time.sleep(0.3)
    ket_qua = {
        "nguon": "darwinex_public_api",
        "thoi_gian": time.strftime("%Y-%m-%d %H:%M:%S"),
        "so_darwin": len(danh_sach),
        "trang_duyet": f"{BASE}/darwins-backtest",
        "endpoint": BASE + "/api/filters/products/all",
        "ghi_chu": last or "OK",
        "darwins": danh_sach,
    }
    DARWINS_JSON.write_text(
        json.dumps(ket_qua, ensure_ascii=False, indent=1), encoding="utf-8")
    return ket_qua


def urllib_quote(v):
    try:
        import urllib.parse
        return urllib.parse.quote(v)
    except Exception:  # noqa: BLE001
        return v


# --- MAIN --------------------------------------------------------------------
def main():
    print("=== LUONG A - NGUON DARWINEX ===")
    print(">> Tai danh sach DARWIN cong khai...")
    try:
        kq = lay_darwin_cong_khai()
        print(f"   LAY {kq['so_darwin']} DARWIN -> {DARWINS_JSON}")
        for row in kq.get("darwins", [])[:5]:
            print(f"   - {row['darwin']:8s} | ROI {row['returnByPeriod']:.1f}% | "
                  f"DD {row['drawDownByPeriod']:.1f}% | DS {row['dscore']:.1f} | "
                  f"{row['investorsByPeriod']} NDT | {row['url']}")
    except Exception as e:  # noqa: BLE001
        print("   LOI quet DARWIN cong khai:", e)

    print(">> OCR portfolio (chup + doc man hinh)...")
    try:
        p = lay_portfolio_ocr()
        print(f"   OCR len={p.get('ocr_len')} | co_du_lieu={p.get('co_du_lieu')}")
        print("   metrics:", json.dumps(p.get("metrics", {}), ensure_ascii=False))
        print(f"   -> {PORTFOLIO_JSON} | png={p.get('png')}")
    except Exception as e:  # noqa: BLE001
        print("   LOI OCR portfolio:", e)

    print("=== XONG ===")


if __name__ == "__main__":
    main()





