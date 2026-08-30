# -*- coding: utf-8 -*-
"""banker.py - Tru "Banker" (vi mo): lay du lieu kinh te tu FRED (lai suat,
chi so USD, VIX...), phan tich che do regime don gian, ghi vao bang macro_brief
de lam nguyen lieu cho vai 'banker' cua bo_nao.

Chay:
  python banker.py --xem-lich   : in lich su macro_brief gan day
  python banker.py              : chay 1 luot cap nhat macro_brief
"""
import sys, time, json, pathlib
import toc_do

LAB = pathlib.Path(__file__).parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

API_KEYS = LAB / "config" / "api_keys.json"

# Bo seri FRED quan tam: DGS10 (10y), DFF (fed funds), DTWEXBGS (chi so USD),
# VIXCLS (chi so VIX - so ru). Moi seri: huong "tang" = that chat / so ru.
SERI = {
    "DGS10":    {"ten": "Lai suat trai phieu 10y", "tang": "risk_off"},
    "DFF":      {"ten": "Lai suat quy lien bang FED", "tang": "risk_off"},
    "DTWEXBGS": {"ten": "Chi so USD rong", "tang": "risk_off"},
    "VIXCLS":   {"ten": "Chi so VIX (so ru)", "tang": "risk_off"},
}


COT_URL = "https://www.cftc.gov/dea/newcot/deafut.txt"
# Seri VIET NAM (FRED): them de loai tru theo doi vi mo VN. DEXVNUS = ty gia
# VND/USD (dong tien VN yeu di khi gia tri tang = so VND doi 1 USD lon len).
SERI_VN = {
    "DEXVNUS": {"ten": "Ty gia VND/USD", "tang": "vnd_gia_tang"},
}   # Legacy: Futures Only (hien hanh)
COT_MARKET = "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE"
# Chi so cot trong file legacy (0-based, theo bang "Variable Names for Legacy" cua CFTC)
# 8,9 = Noncommercial Long/Short (spec); 11,12 = Commercial Long/Short (hedge);
# 38,39 = Change trong Noncommercial Long/Short (1 tuan).
COT_COL = {"oi": 7, "ncl": 8, "ncs": 9, "cml": 11, "cms": 12,
           "chg_ncl": 38, "chg_ncs": 39}


def _fred_key():
    if API_KEYS.exists():
        try:
            return json.loads(API_KEYS.read_text(encoding="utf-8")).get("fred", "")
        except Exception:
            return ""
    return ""


def lay_fred(seri="DGS10", limit=90):
    """Lay du lieu seri FRED qua API. Tra ve danh sach (date, value) sap theo
    thoi gian tang dan, loai bo mau khong co gia tri ('.'). Dung toc_do."""
    key = _fred_key()
    if not key:
        raise RuntimeError("Khong co FRED key trong config/api_keys.json")
    ds = []
    # retry 3 lan vi mang chap chon
    for thu in range(3):
        r = toc_do.lay(
            "https://api.stlouisfed.org/fred/series/observations",
            nguon="fred",
            params={"series_id": seri, "api_key": key, "file_type": "json",
                    "sort_order": "desc", "limit": limit},
            timeout=40)
        if r is not None:
            data = r.json()
            for o in data.get("observations", []):
                v = o.get("value", "")
                if v not in ("", "."):
                    try:
                        ds.append((o["date"], float(v)))
                    except Exception:
                        pass
            ds.reverse()  # tang dan theo ngay
            return ds
        time.sleep(3)
    raise RuntimeError(f"LOI mang khi lay FRED {seri}")


def phan_tich_che_do(ds):
    """Phan tich don gian tu danh sach gia tri (ds). Tra ve dict:
    hien_tai, trung_binh, xu_huong (tang/giam/on_dinh), va che_do
    (risk_on/risk_off/neutural) dua tren xu huong + so sanh trung binh."""
    if not ds:
        return {"hien_tai": None, "trung_binh": None, "xu_huong": "khong_du_lieu",
                "che_do": "neutural"}
    vals = [float(x) for x in ds]
    hien_tai = vals[-1]
    trung_binh = sum(vals) / len(vals)
    n = max(1, len(vals) // 3)
    gan = sum(vals[-n:]) / n
    xa = sum(vals[:n]) / n
    if xa == 0:
        xu_huong = "on_dinh"
    elif gan > xa * 1.01:
        xu_huong = "tang"
    elif gan < xa * 0.99:
        xu_huong = "giam"
    else:
        xu_huong = "on_dinh"
    # che do: so sanh gia tri hien tai voi trung binh theo xu huong
    if xu_huong == "tang" and hien_tai > trung_binh:
        che_do = "risk_off"
    elif xu_huong == "giam" and hien_tai < trung_binh:
        che_do = "risk_on"
    else:
        che_do = "neutural"
    return {"hien_tai": round(hien_tai, 4), "trung_binh": round(trung_binh, 4),
            "xu_huong": xu_huong, "che_do": che_do}


def _tong_hop_che_do(chi_tiet):
    """Binh chon don gian: dem so seri risk_on vs risk_off."""
    on = sum(1 for v in chi_tiet.values() if v.get("che_do") == "risk_on")
    off = sum(1 for v in chi_tiet.values() if v.get("che_do") == "risk_off")
    if off > on:
        return "risk_off"
    if on > off:
        return "risk_on"
    return "neutural"


def _cot_so(s):
    """Chuyen chuoi CFTC sang float, bo mau rong/'.'."""
    if s is None:
        return 0.0
    s = s.strip()
    if s in ("", "."):
        return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


def lay_cot(timeout=60):
    """Lay bao cao COT (Commitments of Traders) loai Legacy Futures Only tu CFTC
    (file deafut.txt - nguon cong khai on dinh, cap nhat moi thu 6). Tra ve dict
    chi tiet cho COT_MARKET (E-MINI S&P 500): ngay, oi, vi the spec (noncommercial),
    vi the hedge (commercial) va bien dong tuan. Dung toc_do + retry 3 lan."""
    ds = None
    for thu in range(3):
        r = toc_do.lay(COT_URL, nguon="web", timeout=timeout)
        if r is not None:
            ds = r.text
            break
        time.sleep(4)
    if ds is None:
        raise RuntimeError("LOI mang khi lay COT tu CFTC")
    import csv as _csv, io as _io
    for row in _csv.reader(_io.StringIO(ds)):
        if not row:
            continue
        if row[0].strip().upper() == COT_MARKET.upper():
            col = COT_COL
            oi = _cot_so(row[col["oi"]])
            ncl = _cot_so(row[col["ncl"]])
            ncs = _cot_so(row[col["ncs"]])
            cml = _cot_so(row[col["cml"]])
            cms = _cot_so(row[col["cms"]])
            chg_ncl = _cot_so(row[col["chg_ncl"]])
            chg_ncs = _cot_so(row[col["chg_ncs"]])
            return {"ngay": row[2].strip(), "oi": oi,
                    "spec_long": ncl, "spec_short": ncs,
                    "hedge_long": cml, "hedge_short": cms,
                    "chg_spec_long": chg_ncl, "chg_spec_short": chg_ncs}
    raise RuntimeError(f"Khong tim thay thi truong COT: {COT_MARKET}")


def phan_tich_cot(cot):
    """Tong hop COT thanh nhan dinh dinh huong (1-2 dong):
    net spec (% OI) + bien dong tuan -> dong thuan/doi lap."""
    if not cot or not cot.get("oi"):
        return {"nhan": "khong_du_lieu", "note": "COT khong co du lieu"}
    net = cot["spec_long"] - cot["spec_short"]
    net_pct = net / cot["oi"] * 100.0
    chg = (cot.get("chg_spec_long", 0) - cot.get("chg_spec_short", 0))
    # nhan dinh theo muc do dong thuan (long/short) tren % OI
    if net_pct >= 3.0:
        nhan = "dong_thuan_long_dong_duc"
        y = "spec LONG qua dong - canh bao dieu chinh (contrarian)"
    elif net_pct <= -3.0:
        nhan = "dong_thuan_short_dong_duc"
        y = "spec SHORT qua dong - tien nang bat lai (contrarian)"
    else:
        nhan = "trung_tinh"
        y = "spec trung tinh" + (" lech SHORT" if net < 0 else " lech LONG")
    # bien dong tuan
    if chg > 0:
        m = ", tuan nay gia tang vi the LONG"
    elif chg < 0:
        m = ", tuan nay gia tang vi the SHORT"
    else:
        m = ""
    note = (f"E-MINI S&P 500 (ngay {cot['ngay']}): spec net={net:,.0f} "
            f"({net_pct:+.2f}% OI){m}. Nhan: {y}.")
    return {"net": round(net), "net_pct": round(net_pct, 2),
            "chg_tuan": round(chg), "nhan": nhan,
            "note": note, "ngay": cot["ngay"]}


def cap_nhat_macro_brief(con):
    """Lay FRED, phan tich regime theo seri, ghi 1 dong moi vao bang
    macro_brief (id, luc, regime, brief, chi_tiet). Tra ve chuoi tom tat."""
    chi_tiet = {}
    loi = []
    for seri, meta in SERI.items():
        try:
            ds = lay_fred(seri)
            pt = phan_tich_che_do([v for _, v in ds])
            chi_tiet[seri] = {"ten": meta["ten"], "hien_tai": pt["hien_tai"],
                              "trung_binh": pt["trung_binh"],
                              "xu_huong": pt["xu_huong"], "che_do": pt["che_do"]}
        except Exception as e:
            loi.append(f"{seri}: {e}")
            chi_tiet.setdefault(seri, {"ten": meta["ten"], "loi": str(e)[:90]})
    regime = _tong_hop_che_do(chi_tiet)
    on = sum(1 for v in chi_tiet.values() if v.get("che_do") == "risk_on")
    off = sum(1 for v in chi_tiet.values() if v.get("che_do") == "risk_off")
    # VIET NAM macro (tach rieng, khong tham gia vote regime the gioi)
    vn = {}
    vn_loi = []
    for seri, meta in SERI_VN.items():
        try:
            ds = lay_fred(seri)
            pt = phan_tich_che_do([v for _, v in ds])
            vn[seri] = {"ten": meta["ten"], "hien_tai": pt["hien_tai"],
                        "trung_binh": pt["trung_binh"],
                        "xu_huong": pt["xu_huong"]}
        except Exception as e:
            vn_loi.append(f"{seri}: {e}")
            vn.setdefault(seri, {"ten": meta["ten"], "loi": str(e)[:90]})
    chi_tiet["VN"] = vn
    brief = (f"REGIME={regime} (risk_on={on}, risk_off={off}): "
             + "; ".join(f"{k}={chi_tiet[k].get('xu_huong','?')}/{chi_tiet[k].get('che_do','?')}"
                         for k in SERI if "loi" not in chi_tiet.get(k, {})))
    vn_bits = []
    for k, v in vn.items():
        if "loi" in v:
            vn_bits.append(f"VN_{k}=LOI")
        else:
            vn_bits.append(f"VN_{k}={v.get('xu_huong','?')}/{round(v.get('hien_tai') or 0, 2)}")
    if vn_bits:
        brief += " | VN: " + "; ".join(vn_bits)
        if vn_loi:
            brief += " | VN_LOI: " + "; ".join(vn_loi)
    # COT - tich hop nhe vao brief (khong loi thi moi bo sung)
    cot_pt = None
    try:
        cot = lay_cot()
        cot_pt = phan_tich_cot(cot)
        chi_tiet["COT"] = cot_pt
        brief += " | COT: " + cot_pt["note"]
    except Exception as e:
        chi_tiet.setdefault("COT", {"loi": str(e)[:90]})
        brief += " | COT: LOI " + str(e)[:60]
    if loi:
        brief += " | LOI: " + "; ".join(loi)
    # kiem tra schema macro_brief truoc khi ghi
    cot = [r[1] for r in con.execute("PRAGMA table_info(macro_brief)").fetchall()]
    if "regime" not in cot or "brief" not in cot or "chi_tiet" not in cot or "luc" not in cot:
        raise RuntimeError("Thieu cot trong bang macro_brief: " + ",".join(cot))
    con.execute("INSERT INTO macro_brief(luc, regime, brief, chi_tiet) VALUES(?,?,?,?)",
                (time.time(), regime, brief, json.dumps(chi_tiet, ensure_ascii=False)))
    con.commit()
    return brief


def xem_lich(con, n=8):
    rows = con.execute(
        "SELECT luc, regime, brief FROM macro_brief ORDER BY luc DESC LIMIT ?",
        (n,)).fetchall()
    for luc, regime, brief in rows:
        print(f"[{time.strftime('%Y-%m-%d %H:%M', time.localtime(luc))}] "
              f"{regime:10} {brief[:110]}")


def xuat_brief_md(regime, chi_tiet, brief):
    """Xuat brief doc duoc ra lab/reports/banker_brief.md (ngay gio, tung seri,
    regime tong hop, ghi chu COT). Khong bat buoc - lot loi thi bo qua."""
    try:
        import datetime as _dt
        reports = LAB / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        now = _dt.datetime.now()
        lines = []
        lines.append("# Banker Brief - " + now.strftime("%Y-%m-%d %H:%M:%S"))
        lines.append("")
        lines.append("- **Thoi diem:** " + now.strftime("%Y-%m-%d %H:%M:%S") +
                     " (Asia/Saigon)")
        lines.append("- **Regime tong hop:** " + str(regime))
        lines.append("")
        lines.append("## Chi tiet seri FRED")
        lines.append("")
        lines.append("| Seri | Ten | Hien tai | TB | Xu huong | Che do |")
        lines.append("|------|-----|----------|----|----------|--------|")
        for k, v in chi_tiet.items():
            if k == "COT":
                continue
            if "loi" in v:
                lines.append(f"| {k} | {v.get('ten','')} | - | - | LOI | {v['loi']} |")
            else:
                lines.append(f"| {k} | {v.get('ten','')} | {v.get('hien_tai')} "
                             f"| {v.get('trung_binh')} | {v.get('xu_huong')} "
                             f"| {v.get('che_do')} |")
        lines.append("")
        lines.append("## Ghi chu COT")
        lines.append("")
        cot = chi_tiet.get("COT", {})
        if "loi" in cot:
            lines.append("Khong lay duoc COT: " + str(cot["loi"]))
        else:
            lines.append(cot.get("note", ""))
            lines.append("")
            lines.append("- Nhan dinh: `" + cot.get("nhan", "?") + "`")
        lines.append("")
        lines.append("## Brief")
        lines.append("")
        lines.append("```")
        lines.append(brief)
        lines.append("```")
        lines.append("")
        (reports / "banker_brief.md").write_text("\n".join(lines), encoding="utf-8")
        return reports / "banker_brief.md"
    except Exception:
        return None


def xuat_brief_md_from_db(con):
    """Doc dong macro_brief moi nhat roi xuat banker_brief.md."""
    try:
        row = con.execute(
            "SELECT regime, brief, chi_tiet FROM macro_brief "
            "ORDER BY luc DESC LIMIT 1").fetchone()
        if not row:
            return None
        regime, brief, chi_tiet_json = row
        import json as _json
        chi_tiet = _json.loads(chi_tiet_json) if chi_tiet_json else {}
        return xuat_brief_md(regime, chi_tiet, brief)
    except Exception:
        return None

if __name__ == "__main__":
    import bo_nao
    con = bo_nao.mo_db()
    if "--xem-lich" in sys.argv:
        xem_lich(con)
        sys.exit(0)
    print("Banker: cap nhat macro_brief tu FRED + COT ...")
    b = cap_nhat_macro_brief(con)
    print("DA GHI:", b)
    md_path = xuat_brief_md_from_db(con)
    if md_path:
        print("DA XUAT:", md_path)
    xem_lich(con, 3)
