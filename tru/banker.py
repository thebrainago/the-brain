# -*- coding: utf-8 -*-
"""banker.py - TRU BANKER. Vi mo cap nhat lien tuc + phan tich sat sao.

Khac ban cu (`lab/banker.py` viet brief roi thoi): o day moi seri vi mo duoc
LUU VAO SO theo thoi gian.

## LOI DA SUA 20/09/2026 - CAU "POINT-IN-TIME" O TREN TUNG LA MOT LOI KHAI

Doan nay truoc viet: *"nen sau nay tra loi duoc cau hoi 'luc do ta biet gi'
(point-in-time) chu khong phai lay ban moi nhat ap nguoc cho qua khu"*.

**Cau do SAI voi chinh ma nguon ben duoi no.** Bang la
`vi_mo(seri, ngay, gia_tri, PRIMARY KEY(seri, ngay))` va `ngay` lay thang tu
cot dau CSV cua FRED - tuc **NGAY CUA SO LIEU**, khong phai ngay ta biet no.
Ba hau qua, ca ba im lang:

1. **Nhin truoc theo DO TRE CONG BO.** CPI thang 3 duoc FRED ghi `ngay =
   2026-03-01` nhung phai giua thang 4 moi cong bo. Mot cau hoi "ngay
   2026-03-15 ta biet gi" se tra ve so CPI thang 3 - **nhin truoc mot thang**.
   Voi World Bank (nam mot lan) do tre la **hang nam**.
2. **Khong co chieu BAN (vintage).** Mot con so bi sua lai khong luu o dau ca.
3. **`INSERT OR IGNORE` NUOT ban sua.** Lan tai dau tien thang; nhung "lan
   dau" la luc nao thi khong ghi o dau. Hai may chay cung ma nguon o hai thoi
   diem khac nhau se co hai `nao.db` khac nhau **ma khong gi noi ra**.

Nay: bang `vi_mo_ban` giu ca chieu `ngay_biet`, va `gia_tri_biet_luc()` la
duong DUY NHAT duoc dung cho cau hoi point-in-time. Seri chua khai do tre thi
no tra `CHUA_DO_DUOC` - **khong doan**.

Nguon (deu mien phi, khong can khoa):
  - FRED (fred.stlouisfed.org/graph/fredgraph.csv) : lai suat, duong cong,
    lam phat, that nghiep, dieu kien tai chinh.
  - CFTC COT (publicreporting.cftc.gov)            : vi the dau co.
  - exchangerate/open.er-api                       : ty gia VND.

Ba muc phan tich, tach bach:
  1. SO LIEU  - so that, co ngay, co nguon.
  2. CHE DO   - phan loai co quy tac (khong phai cam nhan): duong cong, xu huong
                lai suat, do bien dong, dieu kien tin dung.
  3. HAM Y    - chi noi cai gi SUY RA DUOC tu 1 va 2. Khong du doan.

Nguyen tac: BANKER khong duoc tao tin hieu giao dich. No cung cap LOP BOI CANH
cho QUANTLAB dang ky gia thuyet co dieu kien che do. Chi ap lop tin hieu CO
NGHIA voi tai san do (CLAUDE.md muc 10).
"""
from __future__ import annotations

import io
import json
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nhan import so as SO

TRU = "BANKER"
REPORTS = Path(__file__).resolve().parent.parent / "reports"

# FRED: ghi chu cu o day noi "bi chan tu mang nay (ConnectionReset, kiem 15/08)"
# va vi the 12 seri FRED nam trong so KHONG CO DUONG LAY NAO - dang ky roi de
# do, 0 diem du lieu, khong ai bao loi. Do lai 01/09/2026: FRED tra **HTTP 200,
# 209 KB, du lieu den 2026-08-31**. Ghi chu cu da sai, va cai gia phai tra
# khong phai mot nguon thieu ma la CA XUONG SONG VI MO: BANKER chay bang proxy
# Yahoo (^TNX, HYG) thay cho so that (T10Y2Y, BAMLH0A0HYM2), va chi co 2 nam
# lich su thay vi hang chuc nam.
# Bai hoc: mot ket luan "nguon nay bi chan" phai co NGAY DO va phai do lai,
# khong duoc thanh vinh vien.
# Nguon deu da thu THAT va tra 200: FRED, Yahoo chart API, ECB Data API, World Bank.
# Seri: ma noi bo -> (nguon, ma nguon, ten, chu ky giay, y nghia)
SERI = {
    "LS10Y":  ("yahoo", "^TNX", "Loi suat My 10 nam", 43200, "gia von dai han"),
    "LS3M":   ("yahoo", "^IRX", "Tin phieu My 13 tuan", 43200, "lai suat ngan han"),
    "LS5Y":   ("yahoo", "^FVX", "Loi suat My 5 nam", 43200, "ky vong trung han"),
    "LS30Y":  ("yahoo", "^TYX", "Loi suat My 30 nam", 43200, "ky vong rat dai han"),
    "VIX":    ("yahoo", "^VIX", "VIX 30 ngay", 21600, "do so hai co phieu"),
    "VIX3M":  ("yahoo", "^VIX3M", "VIX 3 thang", 21600, "cau truc ky han bien dong"),
    "USD":    ("yahoo", "DX-Y.NYB", "Chi so dola", 43200, "suc manh dola"),
    "HYG":    ("yahoo", "HYG", "ETF trai phieu rac", 43200, "khau vi rui ro tin dung"),
    "LQD":    ("yahoo", "LQD", "ETF trai phieu hang dau tu", 43200, "moc so voi HYG"),
    "TLT":    ("yahoo", "TLT", "ETF trai phieu dai han", 43200, "do dai ky han"),
    "DAU":    ("yahoo", "CL=F", "Dau WTI", 43200, "lam phat dau vao"),
    "VANG":   ("yahoo", "GC=F", "Vang", 43200, "cau tru an"),
    "SP500":  ("yahoo", "^GSPC", "S&P 500", 21600, "tai san rui ro moc"),
    "EURUSD_ECB": ("ecb", "D.USD.EUR.SP00.A", "EURUSD tham chieu ECB", 86400,
                   "ty gia chinh thuc, doc lap voi san"),

    # FRED - so THAT thay cho proxy, va lich su dai hon Yahoo hang chuc nam.
    "T10Y2Y": ("fred", "T10Y2Y", "Chenh 10Y-2Y", 43200,
               "duong cong lai suat, do THANG chu khong tinh tu hai proxy"),
    "T10Y3M": ("fred", "T10Y3M", "Chenh 10Y-3M", 43200,
               "ban duong cong duoc nghien cuu nhieu nhat ve bao suy thoai"),
    "DGS10":  ("fred", "DGS10", "Loi suat 10 nam (FRED)", 43200, "moc doi chieu ^TNX"),
    "DGS2":   ("fred", "DGS2", "Loi suat 2 nam", 43200, "dau ngan cua duong cong"),
    "DFF":    ("fred", "DFF", "Lai suat quy lien bang thuc te", 43200,
               "lap truong chinh sach - Yahoo khong co"),
    "CPIAUCSL": ("fred", "CPIAUCSL", "CPI My", 86400, "lam phat thuc do"),
    "UNRATE": ("fred", "UNRATE", "That nghiep My", 86400, "sat suc khoe lao dong"),
    "NFCI":   ("fred", "NFCI", "Dieu kien tai chinh Chicago Fed", 86400,
               "do that chat tai chinh tong hop"),
    "WALCL":  ("fred", "WALCL", "Bang can doi Fed", 86400, "thanh khoan he thong"),
    "BAMLH0A0HYM2": ("fred", "BAMLH0A0HYM2", "Chenh loi suat trai phieu rac", 43200,
                     "gia rui ro tin dung THAT, thay cho gia ETF HYG"),
    "DTWEXBGS": ("fred", "DTWEXBGS", "Chi so dola dien rong", 43200,
                 "ro rong hon DXY (DXY nang ve EUR)"),
    "VIXCLS": ("fred", "VIXCLS", "VIX (FRED)", 43200, "moc doi chieu ^VIX"),
}
# Chi so quoc gia (World Bank) - nam mot lan, cho phan vi mo Viet Nam
WB = {
    "VN_CPI":  ("VN", "FP.CPI.TOTL.ZG", "Lam phat Viet Nam (%/nam)"),
    "VN_GDP":  ("VN", "NY.GDP.MKTP.KD.ZG", "Tang truong GDP Viet Nam (%/nam)"),
    "VN_TYGIA": ("VN", "PA.NUS.FCRF", "Ty gia VND/USD trung binh nam"),
}

#: DO TRE CONG BO: tu NGAY CUA SO LIEU den ngay ta THAT SU biet no, tinh bang
#: ngay lich. Day la thu bien mot chuoi vi mo thanh dung hay thanh nhin truoc.
#:
#: Quy uoc BAO THU: khi khong chac, khai SO LON HON. Khai thua mot tuan chi lam
#: mat mot tuan du lieu; khai thieu mot tuan la nhin truoc mot tuan, va no
#: khong lo ra o bat ky bang so nao.
#:
#: Seri KHONG co trong bang nay thi `gia_tri_biet_luc` tra `CHUA_DO_DUOC`. Do
#: la co y: mot mac dinh `0` se lang le bien moi seri moi thanh mot nguon nhin
#: truoc, va `0` trong y het mot con so da can nhac.
DO_TRE_NGAY = {
    # --- Gia thi truong: biet NGAY TRONG NGAY. Khong bao gio bi sua lai. ---
    **{k: 0 for k in ("LS10Y", "LS3M", "LS5Y", "LS30Y", "VIX", "VIX3M", "USD",
                      "HYG", "LQD", "TLT", "DAU", "VANG", "SP500")},
    "EURUSD_ECB": 1,          # ty gia tham chieu ECB chot ~16:00 CET, dang ngay sau

    # --- FRED theo NGAY: cong bo ngay lam viec ke tiep, gan nhu khong sua. ---
    **{k: 1 for k in ("DGS10", "DGS2", "DFF", "T10Y2Y", "T10Y3M", "VIXCLS",
                      "BAMLH0A0HYM2", "DTWEXBGS")},

    # --- FRED theo TUAN ---
    "WALCL": 8,               # bang can doi chot thu Tu, ra thu Nam tuan sau
    "NFCI": 10,               # chi so tuan, cong bo tre va CO SUA LAI

    # --- FRED theo THANG: FRED ghi `ngay` la DAU KY, nen do tre tinh tu do ---
    "CPIAUCSL": 45,           # CPI thang M ra giua thang M+1; ban dieu chinh
                              # mua vu con bi sua lai HANG NAM
    "UNRATE": 40,             # bao cao viec lam ra thu Sau dau thang M+1

    # --- World Bank: nam mot lan, va do tre la HANG NAM ---
    **{k: 400 for k in ("VN_CPI", "VN_GDP", "VN_TYGIA")},
}

# Daily market series may legitimately stop over a weekend/holiday, but a value
# older than one week must not silently drive a current regime label. World Bank
# series are annual, so they use a separate freshness window.
TUOI_TOI_DA_NGAY = 7
TUOI_TOI_DA_WB_NGAY = 550

#: Seri cong bo theo THANG/TUAN khong the do bang nguong 7 ngay cua seri ngay:
#: CPI thang 8 ra giua thang 9, nen no se LUON bi danh "oi" va lang le bi loai
#: khoi moi phan loai che do. Nguong phai khop tan suat cong bo, neu khong thi
#: "khong co du lieu" va "du lieu cu" bi gop lam mot lan nua.
TUOI_TOI_DA_RIENG = {
    "CPIAUCSL": 60,   # thang, cong bo tre ~2 tuan
    "UNRATE": 60,     # thang
    "WALCL": 21,      # tuan
    "NFCI": 21,       # tuan
    "BAMLH0A0HYM2": 10,
    "DTWEXBGS": 10,
}


UA_TRINH_DUYET = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def _tai(url: str, timeout: int = 30) -> str | None:
    """Tai mot URL. Thu KHONG User-Agent truoc, co UA sau.

    LOI DA SAP (do 01/09/2026) - va no la loi TU GAY RA, khong phai loi mang:
    ham nay tung gan cung UA trinh duyet cho MOI dia chi. Voi FRED thi UA do
    lam yeu cau treo den het timeout:
        khong UA  -> HTTP 200, 209 KB, du lieu den 2026-08-31
        co UA     -> ReadTimeout sau 20-30 giay
    Vi `_tai` nuot moi ngoai le va tra `None`, trieu chung nhin tu ngoai chi la
    "khong tai duoc". Ket luan duoc ghi vao ma nguon la **"FRED bi chan tu mang
    nay"** va ton tai tu 15/08 den 01/09, khien 12 seri vi mo nam chet trong so
    va BANKER phai chay bang proxy Yahoo.

    Bai hoc chung: truoc khi ket luan "nguon X chan ta", phai thu bo chinh nhung
    thu TA them vao yeu cau. Mot cai chan do minh tu dung len trong khong the
    phan biet duoc voi mot cai chan that.
    """
    try:
        import requests
    except Exception:
        return None
    for headers in ({}, {"User-Agent": UA_TRINH_DUYET}):
        try:
            r = requests.get(url, timeout=timeout, headers=headers)
            if r.status_code == 200 and r.text:
                return r.text
        except Exception:
            continue
    return None


def _tu_fred(ma_nguon: str) -> list[tuple[str, float]]:
    """FRED CSV -> [(ngay, gia tri)]. Do lai 01/09/2026: HTTP 200, den 2026-08-31.

    FRED danh dau ky khong co so bang dau cham. Bo qua chung chu KHONG doi thanh
    0: mot ngay le khong phai mot ngay lai suat bang khong.
    """
    txt = _tai(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={ma_nguon}")
    if not txt:
        return []
    ra: list[tuple[str, float]] = []
    for dong in txt.splitlines()[1:]:
        phan = dong.split(",")
        if len(phan) < 2:
            continue
        ngay, gt = phan[0].strip(), phan[1].strip()
        if not ngay or gt in ("", "."):
            continue
        try:
            ra.append((ngay, float(gt)))
        except ValueError:
            continue
    return ra


def _tu_yahoo(ma_nguon: str, khoang: str = "2y") -> list[tuple[str, float]]:
    """Yahoo chart API -> [(ngay, gia tri)]. Da kiem that: tra 200."""
    u = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ma_nguon}"
         f"?range={khoang}&interval=1d")
    txt = _tai(u)
    if not txt:
        return []
    try:
        j = json.loads(txt)
        kq = j["chart"]["result"][0]
        moc = kq["timestamp"]
        gia = kq["indicators"]["quote"][0]["close"]
        ra = []
        for t, g in zip(moc, gia):
            if g is None:
                continue
            ra.append((time.strftime("%Y-%m-%d", time.gmtime(t)), float(g)))
        return ra
    except Exception:
        return []


def _tu_ecb(khoa: str) -> list[tuple[str, float]]:
    u = (f"https://data-api.ecb.europa.eu/service/data/EXR/{khoa}"
         f"?lastNObservations=500&format=csvdata")
    txt = _tai(u)
    if not txt:
        return []
    ra = []
    try:
        import csv
        for d in csv.DictReader(io.StringIO(txt)):
            ng, gt = d.get("TIME_PERIOD"), d.get("OBS_VALUE")
            if ng and gt:
                ra.append((ng[:10], float(gt)))
    except Exception:
        return []
    return ra


def _tu_worldbank(nuoc: str, chi_so: str) -> list[tuple[str, float]]:
    u = (f"https://api.worldbank.org/v2/country/{nuoc}/indicator/{chi_so}"
         f"?format=json&per_page=100")
    txt = _tai(u)
    if not txt:
        return []
    try:
        j = json.loads(txt)
        ra = []
        for d in (j[1] or []):
            if d.get("value") is not None:
                ra.append((f"{d['date']}-12-31", float(d["value"])))
        return ra
    except Exception:
        return []


def _luu_seri(ma: str, ten: str, nguon: str, chu_ky: int, y_nghia: str,
              diem: list[tuple[str, float]]) -> dict:
    if not diem:
        SO.chay("INSERT INTO vi_mo_seri(ma,ten,nguon,chu_ky_giay,lan_cuoi,ghi_chu) "
                "VALUES(?,?,?,?,0,'LOI TAI') ON CONFLICT(ma) DO UPDATE SET ghi_chu='LOI TAI'",
                ma, ten, nguon, chu_ky)
        return {"ma": ma, "loi": "khong tai duoc"}
    with SO.ket_noi() as cn:
        cn.execute("BEGIN")
        for ngay, gt in diem:
            cn.execute("INSERT OR IGNORE INTO vi_mo(seri,ngay,gia_tri) VALUES(?,?,?)",
                       (ma, ngay, gt))
        cn.execute("COMMIT")
    n = SO.mot("SELECT COUNT(*) n FROM vi_mo WHERE seri=?", ma)["n"]
    SO.chay("INSERT INTO vi_mo_seri(ma,ten,nguon,chu_ky_giay,lan_cuoi,so_diem,ghi_chu) "
            "VALUES(?,?,?,?,?,?,?) ON CONFLICT(ma) DO UPDATE SET lan_cuoi=excluded.lan_cuoi, "
            "so_diem=excluded.so_diem, ghi_chu=excluded.ghi_chu",
            ma, ten, nguon, chu_ky, time.time(), n, y_nghia)
    return {"ma": ma, "so_diem": n}


def nap_seri(ma: str, ep: bool = False) -> dict:
    """Nap mot seri vao bang vi_mo. CHI-THEM, khong ghi de qua khu -> sau nay
    tra loi duoc 'luc do ta biet gi' (point-in-time)."""
    if ma not in SERI:
        return {"ma": ma, "loi": "khong khai bao"}
    nguon, ma_nguon, ten, chu_ky, y_nghia = SERI[ma]
    cu = SO.mot("SELECT * FROM vi_mo_seri WHERE ma=?", ma)
    if cu and not ep and (time.time() - (cu["lan_cuoi"] or 0)) < chu_ky:
        return {"ma": ma, "bo_qua": "chua den ky"}
    # Bang tra, KHONG dung if/else hai nhanh: mot nguon thu ba (fred) se lang le
    # roi vao nhanh `else` va tra ve rong ma khong ai bao gi - dung hinh dang loi
    # da lam 12 seri FRED nam chet trong so.
    LAY = {"yahoo": _tu_yahoo, "ecb": _tu_ecb, "fred": _tu_fred}
    if nguon not in LAY:
        return {"ma": ma, "loi": f"nguon '{nguon}' chua co duong lay"}
    diem = LAY[nguon](ma_nguon)
    return _luu_seri(ma, ten, nguon, chu_ky, y_nghia, diem)


def nap_quoc_gia(ep: bool = False) -> list[dict]:
    ra = []
    for ma, (nuoc, chi_so, ten) in WB.items():
        cu = SO.mot("SELECT * FROM vi_mo_seri WHERE ma=?", ma)
        if cu and not ep and (time.time() - (cu["lan_cuoi"] or 0)) < 604800:
            continue
        ra.append(_luu_seri(ma, ten, "worldbank", 604800, "vi mo quoc gia",
                            _tu_worldbank(nuoc, chi_so)))
    return ra


def gan_nhat(ma: str, n: int = 1) -> list[dict]:
    return SO.nhieu("SELECT ngay,gia_tri FROM vi_mo WHERE seri=? ORDER BY ngay DESC LIMIT ?",
                    ma, n)


def _doc_ngay(s: str) -> date | None:
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _tuoi_ngay(s: str, hom_nay: date | None = None) -> int | None:
    d = _doc_ngay(s)
    return ((hom_nay or date.today()) - d).days if d else None


def _nguong_tuoi(ma: str) -> int:
    if ma in TUOI_TOI_DA_RIENG:
        return TUOI_TOI_DA_RIENG[ma]
    return TUOI_TOI_DA_WB_NGAY if ma.startswith("VN_") else TUOI_TOI_DA_NGAY


def _cap_cung_ngay(ma_a: str, ma_b: str, ngay_toi_da: str | None = None) -> dict | None:
    """Lay hai seri tai cung MOT ngay, khong ghep hai moc gan nhat khac nhau."""
    dieu_kien = "AND a.ngay<=?" if ngay_toi_da else ""
    tham_so = (ma_a, ma_b, ngay_toi_da) if ngay_toi_da else (ma_a, ma_b)
    return SO.mot(
        "SELECT a.ngay, a.gia_tri gia_a, b.gia_tri gia_b "
        "FROM vi_mo a JOIN vi_mo b ON b.ngay=a.ngay "
        "WHERE a.seri=? AND b.seri=? " + dieu_kien + " ORDER BY a.ngay DESC LIMIT 1",
        *tham_so)


def _doi(ma: str, so_ngay: int) -> float | None:
    """Thay doi so voi `so_ngay` truoc MOC MOI NHAT cua chinh seri."""
    m = SO.mot("SELECT ngay,gia_tri FROM vi_mo WHERE seri=? ORDER BY ngay DESC LIMIT 1", ma)
    if not m or not _doc_ngay(m["ngay"]):
        return None
    moc = (_doc_ngay(m["ngay"]) - timedelta(days=so_ngay)).strftime("%Y-%m-%d")
    c = SO.mot("SELECT gia_tri FROM vi_mo WHERE seri=? AND ngay<=? ORDER BY ngay DESC LIMIT 1",
               ma, moc)
    if not c:
        return None
    return float(m["gia_tri"]) - float(c["gia_tri"])


def phan_loai_che_do() -> dict:
    """CHE DO theo QUY TAC, khong theo cam nhan. Moi nhan co dieu kien viet ra."""
    ra: dict = {"luc": SO.bay_gio(), "che_do": {}, "so_lieu": {}, "thieu": [],
                "stale": []}

    def lay(ma):
        r = gan_nhat(ma)
        if r:
            tuoi = _tuoi_ngay(r[0]["ngay"])
            stale = tuoi is None or tuoi > _nguong_tuoi(ma)
            ra["so_lieu"][ma] = {"ngay": r[0]["ngay"], "gia_tri": r[0]["gia_tri"],
                                  "tuoi_ngay": tuoi, "stale": stale}
            if stale:
                ra["stale"].append(ma)
                return None
            return float(r[0]["gia_tri"])
        ra["thieu"].append(ma)
        return None

    def cap(ma_a, ma_b, ten):
        r = _cap_cung_ngay(ma_a, ma_b)
        if not r:
            ra["thieu"].append(ten)
            return None
        tuoi = _tuoi_ngay(r["ngay"])
        stale = tuoi is None or tuoi > max(_nguong_tuoi(ma_a), _nguong_tuoi(ma_b))
        ra["so_lieu"][ten] = {"ngay": r["ngay"], "gia_a": r["gia_a"],
                               "gia_b": r["gia_b"], "tuoi_ngay": tuoi,
                               "stale": stale}
        if stale:
            ra["stale"].append(ten)
            return None
        return float(r["gia_a"]), float(r["gia_b"]), r["ngay"]

    ls10, ls3m = lay("LS10Y"), lay("LS3M")
    vix, vix3m = lay("VIX"), lay("VIX3M")
    usd, hyg, lqd = lay("USD"), lay("HYG"), lay("LQD")

    # Moi phep ket hop bat buoc dung cung ngay quan sat.
    duong_cong = cap("LS10Y", "LS3M", "LS10Y/LS3M")
    if duong_cong:
        cong = duong_cong[0] - duong_cong[1]
        ra["so_lieu"]["duong_cong_10y_3m"] = round(cong, 3)
        ra["che_do"]["duong_cong"] = {
            "nhan": "DAO NGUOC" if cong < 0 else ("PHANG" if cong < 0.5 else "DOC"),
            "gia_tri": round(cong, 3), "quy_tac": "10y-3m < 0 = dao nguoc; < 0,5 = phang",
            "ngay": duong_cong[2],
            "y_nghia": "dao nguoc di truoc suy thoai 6-18 thang; day la BOI CANH, "
                       "khong phai tin hieu vao lenh"}

    d90 = _doi("LS10Y", 90)
    if d90 is not None:
        ra["che_do"]["xu_huong_lai_suat"] = {
            "nhan": "TANG" if d90 > 0.25 else ("GIAM" if d90 < -0.25 else "DI NGANG"),
            "gia_tri": round(d90, 3), "doi_90_ngay_diem": round(d90, 3),
            "quy_tac": "|doi loi suat 10y trong 90 ngay| > 0,25 diem",
            "y_nghia": "lop vi mo DUY NHAT tung vuot mua-giu qua 64 nam trong du an nay la "
                       "nghieng size theo THAY DOI loi suat 10y (memory macro-tilt-lead)"}
    if vix is not None:
        ra["che_do"]["bien_dong"] = {
            "nhan": "CAO" if vix > 25 else ("THAP" if vix < 15 else "BINH THUONG"),
            "gia_tri": vix, "quy_tac": "VIX > 25 cao, < 15 thap",
            "y_nghia": "tren SP500 khung ngay: VIX cao = MUA (nguoc truc quan thong thuong)"}
    vix_term = cap("VIX3M", "VIX", "VIX3M/VIX")
    if vix_term and vix_term[1] > 0:
        ty = vix_term[0] / vix_term[1]
        ra["che_do"]["cau_truc_ky_han_vix"] = {
            "nhan": "NGHICH DAO (cang)" if ty < 1.0 else "BINH THUONG",
            "gia_tri": round(ty, 3), "quy_tac": "VIX3M/VIX < 1",
            "ngay": vix_term[2],
            "y_nghia": "co che 01 cua du an tung AM TINH (IC +0,106 nhung placebo 10,2%) "
                       "- dung dung lam tin hieu, chi doc lam boi canh"}
    tin_dung = cap("HYG", "LQD", "HYG/LQD")
    if tin_dung and tin_dung[1] > 0:
        r = tin_dung[0] / tin_dung[1]
        moc_ngay = (_doc_ngay(tin_dung[2]) - timedelta(days=90)).strftime("%Y-%m-%d")
        moc = _cap_cung_ngay("HYG", "LQD", moc_ngay)
        doi = (r / (float(moc["gia_a"]) / float(moc["gia_b"])) - 1) \
            if (moc and moc["gia_b"]) else None
        ra["che_do"]["tin_dung"] = {
            "nhan": ("CANG" if doi < -0.02 else ("DE" if doi > 0.02 else "BINH THUONG"))
                    if doi is not None else "?",
            "gia_tri": round(r, 4), "doi_90_ngay_pct": round(doi * 100, 2) if doi is not None else None,
            "ngay": tin_dung[2],
            "quy_tac": "ty le HYG/LQD giam > 2% trong 90 ngay = tin dung cang",
            "y_nghia": "PROXY tu gia hai ETF, khong phai chenh loi suat. No lan ca "
                       "rui ro ky han va dong tien vao ETF, nen co the lech voi "
                       "`tin_dung_that` (BAMLH0A0HYM2) - luc lech thi tin ban THAT"}
    # ---- BON CHE DO CHI CO KHI CO FRED (nap lai 01/09, truoc do 12 seri nam chet)
    # Ca bon deu do LAP TRUONG CHINH SACH / DIEU KIEN TIEN TE, tuc thu ma gia
    # tai san tren Yahoo khong noi ra duoc.
    dff = lay("DFF")
    if dff is not None:
        d180 = _doi("DFF", 180)
        if d180 is not None:
            ra["che_do"]["chinh_sach_tien_te"] = {
                "nhan": "THAT CHAT" if d180 > 0.25 else ("NOI LONG" if d180 < -0.25
                                                         else "GIU NGUYEN"),
                "gia_tri": dff, "doi_180_ngay_diem": round(d180, 3),
                "quy_tac": "|doi lai suat quy lien bang trong 180 ngay| > 0,25 diem",
                "y_nghia": "lap truong Fed. BOI CANH cho gia thuyet co dieu kien, "
                           "khong phai tin hieu vao lenh"}

    nfci = lay("NFCI")
    if nfci is not None:
        ra["che_do"]["dieu_kien_tai_chinh"] = {
            "nhan": "CHAT HON TRUNG BINH" if nfci > 0 else "LONG HON TRUNG BINH",
            "gia_tri": nfci,
            "quy_tac": "NFCI > 0 = chat hon trung binh lich su (chi so da chuan hoa)",
            "y_nghia": "chi so tong hop 105 bien cua Chicago Fed - do dieu kien tai "
                       "chinh TONG THE, khong suy ra tu gia mot tai san nao"}

    walcl = _doi("WALCL", 90)
    if walcl is not None:
        moc = gan_nhat("WALCL")
        muc = float(moc[0]["gia_tri"]) if moc else None
        pct = (walcl / (muc - walcl) * 100) if muc and (muc - walcl) else None
        ra["che_do"]["thanh_khoan"] = {
            "nhan": ("BOM VAO" if pct > 1 else ("RUT RA" if pct < -1 else "DI NGANG"))
                    if pct is not None else "?",
            "gia_tri": muc, "doi_90_ngay_pct": round(pct, 2) if pct is not None else None,
            "quy_tac": "|doi bang can doi Fed trong 90 ngay| > 1%",
            "y_nghia": "thanh khoan he thong. Doc lam boi canh cho tai san rui ro"}

    # Chenh loi suat trai phieu rac THAT, thay cho ty le gia hai ETF. Giu ca hai:
    # neu hai ben noi nguoc nhau thi do la thong tin, khong phai loi.
    hy = lay("BAMLH0A0HYM2")
    if hy is not None:
        dhy = _doi("BAMLH0A0HYM2", 90)
        ra["che_do"]["tin_dung_that"] = {
            "nhan": ("CANG" if dhy > 0.5 else ("DE" if dhy < -0.5 else "BINH THUONG"))
                    if dhy is not None else "?",
            "gia_tri": hy, "doi_90_ngay_diem": round(dhy, 3) if dhy is not None else None,
            "quy_tac": "chenh loi suat HY - kho bac; doi > 0,5 diem trong 90 ngay",
            "y_nghia": "gia rui ro tin dung do THANG. Ban `tin_dung` (HYG/LQD) la "
                       "proxy tu gia ETF, giu lai de doi chieu"}

    if usd is not None:
        du = _doi("USD", 90)
        ra["che_do"]["dola"] = {
            "nhan": "MANH LEN" if (du or 0) > 1 else ("YEU DI" if (du or 0) < -1 else "ON DINH"),
            "gia_tri": usd, "quy_tac": "|doi chi so dola 90 ngay| > 1 diem",
            "doi_90_ngay": round(du, 3) if du is not None else None,
            "y_nghia": "DXY nang ve EUR (~58%). Dola manh len thuong siet tai san "
                       "rui ro va hang hoa. Doi chieu voi DTWEXBGS (ro rong hon) "
                       "truoc khi ket luan ve suc manh dola noi chung"}

    for ma in ("VN_CPI", "VN_GDP", "VN_TYGIA"):
        lay(ma)
    return ra


def ham_y(che_do: dict) -> list[str]:
    """CHI noi cai suy ra duoc. Khong du doan gia."""
    ra = []
    cd = che_do.get("che_do", {})
    if cd.get("duong_cong", {}).get("nhan") == "DAO NGUOC":
        ra.append("Duong cong dao nguoc: chi phi giu vi the mua dai han cao hon binh thuong "
                  "(phi qua dem theo lai suat ngan han) - anh huong TRUC TIEP toi chi phi, "
                  "khong phai toi huong gia.")
    xh = cd.get("xu_huong_lai_suat", {})
    if xh.get("nhan") in ("TANG", "GIAM"):
        ra.append(f"Loi suat 10y {xh['nhan'].lower()} {abs(xh['doi_90_ngay_diem'])} diem trong 90 ngay "
                  "-> lop nghieng size theo thay doi loi suat dang co tin hieu; "
                  "day la lop DUY NHAT tung vuot mua-giu qua 64 nam trong du an.")
    bd = cd.get("bien_dong", {})
    if bd.get("nhan") == "CAO":
        ra.append(f"VIX {bd['gia_tri']} > 25: tren khung ngay SP500 day la vung MUA theo "
                  "ket luan da chot, khong phai vung tranh.")
    if cd.get("tin_dung", {}).get("nhan") == "CANG":
        ra.append("Chenh lech tin dung cang: rui ro doi tac cua san CFD tang - "
                  "lien quan toi so chenh lech chi phi trien khai, khong chi toi gia.")
    if not ra:
        ra.append("Khong che do nao vuot nguong quy tac. Khong co ham y nao dang bao.")
    return ra


def mot_luot(ep: bool = False) -> dict:
    SO.nhip_tim(TRU, "chay")
    ket = {"nap": [], "loi": 0}
    for ma in SERI:
        r = nap_seri(ma, ep=ep)
        ket["nap"].append(r)
        ket["loi"] += int("loi" in r)
    ket["nap"] += nap_quoc_gia(ep=ep)

    cd = phan_loai_che_do()
    cd["ham_y"] = ham_y(cd)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "banker_che_do.json").write_text(
        json.dumps(cd, ensure_ascii=False, indent=1), encoding="utf-8")

    dong = ["# BANKER - BOI CANH VI MO", f"*Cap nhat {cd['luc']}*", ""]
    dong.append("## Che do (theo quy tac, khong theo cam nhan)")
    dong.append("| Truc | Nhan | Gia tri | Quy tac |")
    dong.append("|---|---|---|---|")
    for k, v in cd["che_do"].items():
        dong.append(f"| {k} | **{v['nhan']}** | {v.get('gia_tri')} | {v.get('quy_tac','')} |")
    dong += ["", "## Ham y (chi cai suy ra duoc)"]
    dong += [f"- {x}" for x in cd["ham_y"]]
    if cd["thieu"]:
        dong += ["", f"> Thieu seri: {', '.join(cd['thieu'])} - chua tai duoc."]
    if cd["stale"]:
        dong += ["", f"> Du lieu stale, KHONG dung gan nhan: {', '.join(cd['stale'])}."]
    (REPORTS / "BANKER.md").write_text("\n".join(dong), encoding="utf-8")

    SO.ghi_su_kien(TRU, "che_do", {"che_do": {k: v["nhan"] for k, v in cd["che_do"].items()}})
    SO.ghi_chi_so("banker_so_seri", len([r for r in ket["nap"] if "so_diem" in r]))
    SO.nhip_tim(TRU, "nghi", {"seri_loi": ket["loi"], "che_do": len(cd["che_do"])})
    if ket["loi"] >= len(SERI) // 2:
        SO.bao_van_de("banker_mat_nguon", "VUA",
                      f"{ket['loi']}/{len(SERI)} seri FRED khong tai duoc - kiem mang/proxy",
                      {"chi_tiet": ket["nap"][:5]})
    else:
        SO.dong_van_de("banker_mat_nguon", "tai lai duoc")
    return {"seri_ok": len(SERI) - ket["loi"], "seri_loi": ket["loi"],
            "che_do": {k: v["nhan"] for k, v in cd["che_do"].items()},
            "ham_y": cd["ham_y"]}


# ===================================================================== DIEM THOI GIAN
def do_tre_cua(seri: str) -> int | None:
    """Do tre cong bo cua mot seri, hay `None` neu chua khai.

    `None` KHONG duoc doc thanh 0. Xem `DO_TRE_NGAY`.
    """
    return DO_TRE_NGAY.get(seri)


def ngay_biet_cua(seri: str, ngay: str) -> str | None:
    """Ngay ta THAT SU biet mot so lieu. `None` = chua khai do tre."""
    d = _doc_ngay(ngay)
    tre = do_tre_cua(seri)
    if d is None or tre is None:
        return None
    return (d + timedelta(days=int(tre))).strftime("%Y-%m-%d")


def gia_tri_biet_luc(seri: str, moc: str) -> dict:
    """Gia tri MOI NHAT ma ta da biet tinh den `moc`. Duong DUY NHAT cho
    cau hoi point-in-time.

    Tra mot dict LUON co `trang_thai`:
      `DAT`           co so, kem `ngay` (ngay so lieu) va `ngay_biet`.
      `AM`            khai bao du nhung khong co diem nao du cu de da biet.
      `CHUA_DO_DUOC`  seri chua khai do tre, hay `moc` khong doc duoc.

    ## VI SAO KHONG CO NHANH "MAC DINH 0 NGAY"

    Mot mac dinh nhu vay se lang le bien moi seri moi thanh nguon nhin truoc,
    va cai gia khong lo ra o dau: bang so van day, p-value van tinh duoc, chi
    co ket luan la sai. Tu choi tra loi la ton mot seri; doan la ton ca ket
    luan.
    """
    if _doc_ngay(moc) is None:
        return {"seri": seri, "trang_thai": "CHUA_DO_DUOC",
                "ly_do": "moc khong doc duoc: %r" % (moc,)}
    tre = do_tre_cua(seri)
    if tre is None:
        return {"seri": seri, "trang_thai": "CHUA_DO_DUOC",
                "ly_do": "seri '%s' chua khai DO_TRE_NGAY - khong biet luc nao "
                         "thi ta biet so nay, nen khong tra loi point-in-time "
                         "duoc" % seri}
    # Loc bang NGAY SO LIEU + do tre <= moc. Lam trong SQL bang `date()` de
    # khong phai keo ca seri ve bo nho.
    r = SO.mot(
        "SELECT ngay, gia_tri FROM vi_mo WHERE seri=? "
        "AND date(ngay, ?) <= date(?) ORDER BY ngay DESC LIMIT 1",
        seri, "+%d days" % int(tre), moc[:10])
    if not r:
        return {"seri": seri, "trang_thai": "AM", "do_tre_ngay": int(tre),
                "ly_do": "khong diem nao da duoc cong bo truoc %s" % moc[:10]}
    return {"seri": seri, "trang_thai": "DAT", "ngay": r["ngay"],
            "gia_tri": r["gia_tri"], "do_tre_ngay": int(tre),
            "ngay_biet": ngay_biet_cua(seri, r["ngay"]), "uoc_tinh": True}


def do_nhin_truoc(seri: str, moc: str) -> dict:
    """DO bang so cai nhin truoc ma phep doc ngay tho gay ra.

    Bien mot loi khai thanh mot CON SO: so sanh "gia tri CUA ngay <= moc"
    (phep doc cu) voi "gia tri ta DA BIET tinh den moc" (phep doc dung). Lech
    bao nhieu ngay, va co lech ca gia tri khong.

    Dung de kiem: neu ham nay tra `lech_ngay = 0` cho MOI seri thi hoac du
    lieu khong co do tre nao, hoac phep do dang hong - chu khong phai "bang
    cu von da dung".
    """
    tho = SO.mot("SELECT ngay, gia_tri FROM vi_mo WHERE seri=? AND ngay<=? "
                 "ORDER BY ngay DESC LIMIT 1", seri, moc[:10])
    dung = gia_tri_biet_luc(seri, moc)
    if not tho:
        return {"seri": seri, "trang_thai": "CHUA_DO_DUOC",
                "ly_do": "khong co diem nao <= %s" % moc[:10]}
    if dung["trang_thai"] != "DAT":
        return {"seri": seri, "trang_thai": dung["trang_thai"],
                "ly_do": dung.get("ly_do"), "tho_thay": tho["ngay"]}
    a, b = _doc_ngay(tho["ngay"]), _doc_ngay(dung["ngay"])
    return {"seri": seri, "trang_thai": "DAT",
            "tho_thay": tho["ngay"], "dung_ra_thay": dung["ngay"],
            "lech_ngay": (a - b).days if a and b else None,
            "lech_gia_tri": (None if tho["gia_tri"] is None
                             or dung["gia_tri"] is None
                             else round(tho["gia_tri"] - dung["gia_tri"], 6))}


def seri_chua_khai_do_tre() -> list[str]:
    """Seri da khai trong `SERI`/`WB` ma chua co do tre. Phai LUON rong.

    Them mot seri moi ma quen khai do tre thi no khong hong ngay - no chi
    lang le tu choi moi cau hoi point-in-time ve chinh no. Bai kiem goi ham
    nay de cho do lo ra luc them, chu khong phai vai thang sau.
    """
    return sorted(k for k in list(SERI) + list(WB) if k not in DO_TRE_NGAY)


# ============================================================ GIA TRI CUA BANKER
#
# Cau hoi DUY NHAT quyet dinh tru nay ton tai hay khong:
#
#     Voi CUNG mot co che, loc theo che do vi mo co lam no ra tien hon khong?
#
# Phan tich vi mo la **narrative khong the bac bo**: bat ky dien bien nao cung
# giai thich duoc SAU KHI no xay ra. Mot BANKER chi sinh van ban se LUON trong
# dung va KHONG BAO GIO ra tien. Nen moi luat vi mo phai di qua mot phep so co
# con so, va phep so do phai point-in-time.

#: Loc theo che do LUON lam giam so lenh. It lenh hon thi phuong sai cao hon,
#: nen mot cai "hon" nho tren mot mau nho khong noi len gi. Duoi nguong nay thi
#: ket qua la CHUA_DO_DUOC chu khong phai AM.
TOI_THIEU_BAR_MOI_NHANH = 250


def chuoi_che_do(seri: str, phep: str, nguong: float,
                 lich) -> "pd.Series | None":
    """Chuoi bool POINT-IN-TIME cua mot dieu kien che do, theo lich cua he.

    Moi moc `t` trong `lich` duoc tra loi bang **thu ta biet tai t**, qua
    `gia_tri_biet_luc` - khong phai bang gia tri CUA ngay t. Do la ca ly do
    muc DIEM THOI GIAN ton tai.

    `None` khi seri chua khai do tre: khong doan.
    """
    import pandas as pd

    if do_tre_cua(seri) is None:
        return None
    ra, cuoi = [], None
    for t in lich:
        d = gia_tri_biet_luc(seri, str(t)[:10])
        if d["trang_thai"] == "DAT":
            cuoi = d["gia_tri"]
        if cuoi is None:
            ra.append(False)
            continue
        ra.append(cuoi > nguong if phep == ">" else cuoi < nguong)
    return pd.Series(ra, index=lich, dtype=bool)


def so_co_che_do(loi_suat, che_do) -> dict:
    """So MOT co che chay TU DO voi chinh no chi chay TRONG che do.

    `loi_suat` la chuoi loi suat RONG cua co che theo bar (0 khi khong co vi
    the). `che_do` la chuoi bool cung lich.

    Tra ba trang thai:
      `DAT`           loc che do lam TANG lai tren moi bar co phoi nhiem
      `AM`            do duoc va khong tang
      `CHUA_DO_DUOC`  mot nhanh qua it bar de noi duoc gi

    ## VI SAO SO "LAI TREN MOI BAR CO PHOI NHIEM" CHU KHONG SO TONG LAI

    Loc che do LUON cat bot so lenh, nen tong lai gan nhu luon GIAM - so tong
    thi bo loc nao cung "thua". Cau hoi dung la mot dong von bo ra co duoc tra
    nhieu hon khong, tuc lai chia cho SO BAR THAT SU CAM VI THE.
    """
    import numpy as np

    a = np.asarray(loi_suat, float)
    m = np.asarray(che_do, bool)
    if len(a) != len(m):
        return {"trang_thai": "CHUA_DO_DUOC",
                "ly_do": "lich lech: %d bar loi suat vs %d bar che do"
                         % (len(a), len(m))}
    co = np.abs(a) > 0                       # bar that su co phoi nhiem
    trong, ngoai = co & m, co & ~m
    if trong.sum() < TOI_THIEU_BAR_MOI_NHANH or ngoai.sum() < TOI_THIEU_BAR_MOI_NHANH:
        return {"trang_thai": "CHUA_DO_DUOC",
                "ly_do": "trong che do %d bar, ngoai %d bar - can >= %d moi ben"
                         % (int(trong.sum()), int(ngoai.sum()),
                            TOI_THIEU_BAR_MOI_NHANH),
                "bar_trong": int(trong.sum()), "bar_ngoai": int(ngoai.sum())}
    lai_trong = float(a[trong].mean())
    lai_ngoai = float(a[ngoai].mean())
    lai_chung = float(a[co].mean())
    return {
        "trang_thai": "DAT" if lai_trong > lai_chung else "AM",
        "lai_moi_bar_trong_che_do": round(lai_trong, 8),
        "lai_moi_bar_ngoai_che_do": round(lai_ngoai, 8),
        "lai_moi_bar_khong_loc": round(lai_chung, 8),
        "bar_trong": int(trong.sum()), "bar_ngoai": int(ngoai.sum()),
        # Bao nhieu phan tram so lenh bi bo di de doi lay cai "hon" do. Mot bo
        # loc cat 95% so lenh de tang 3% lai moi bar la mot bo loc da khop vao
        # qua khu, khong phai mot phat hien.
        "ty_le_giu_lenh": round(float(trong.sum()) / max(int(co.sum()), 1), 4),
    }


if __name__ == "__main__":
    # PHAI nam CUOI FILE. Toi tung noi muc DIEM THOI GIAN vao sau khoi nay, va
    # nhu the `python -m tru.banker` se chay `mot_luot()` TRUOC khi cac ham do
    # ton tai - mot `NameError` cho duoc kich hoat, khong lo ra o bai kiem nao
    # vi bai kiem thi `import` chu khong chay `__main__`.
    SO.khoi_tao()
    if "--nhin-truoc" in sys.argv:
        # Do bang so cai nhin truoc cua phep doc tho tren TUNG seri. Chay tren
        # may co du lieu that; cloud khong goi duoc FRED (proxy chan).
        moc = time.strftime("%Y-%m-%d")
        ra = [do_nhin_truoc(k, moc) for k in list(SERI) + list(WB)]
        co = [d for d in ra if d.get("lech_ngay")]
        print(json.dumps({"moc": moc, "so_seri": len(ra),
                          "co_nhin_truoc": len(co),
                          "nang_nhat": sorted(co, key=lambda d: -d["lech_ngay"])[:10],
                          "chua_do_duoc": [d["seri"] for d in ra
                                           if d["trang_thai"] == "CHUA_DO_DUOC"]},
                         ensure_ascii=False, indent=1))
    else:
        print(json.dumps(mot_luot(ep="--ep" in sys.argv), ensure_ascii=False,
                         indent=1))
