# -*- coding: utf-8 -*-
"""
lab.py - Phong lab quet he thong giao dich 24/7, DeepSeek lam bo nao
=====================================================================
Kien truc phan vai (LLM khong tu chay MT5 duoc):
    DeepSeek (ngon ngu) : doc code -> rut co che -> sinh tham so -> doc ket qua tinh chinh
    Python  (co hoc)    : cao nguon -> chay MT5 tester -> do -> luu thu vien

VONG LAP (mot vong):
    1. CAO   cac nguon cong khai (MQL5 CodeBase, GitHub, TradingView) -> muc moi
    2. RUT   goi DeepSeek B1 (phan loai) + B2 (rut co che) -> luu co che vao SQLite
    3. XEP   loc co che diem >= NGUONG vao hang doi kiem chung
    4. SINH  goi DeepSeek B3 -> anh xa co che thanh cau hinh .set cua EA LuoiDoiXung
    5. TEST  chay MT5 Strategy Tester THAT cho tung cau hinh (toan bo lich su, Model=1)
    6. DOC   goi DeepSeek B4 -> phan quyet THAT/AO + sinh buoc tinh chinh
    7. GHI   cap nhat thu vien; neu THAT -> chay kiem cheo cap khac + walk-forward

Cai dat:
    pip install requests
    setx DEEPSEEK_API_KEY "sk-..."   (mo lai PowerShell)
Chay mot vong :  python lab.py --vong 1
Chay 24/7     :  python lab.py --lien-tuc --nghi 1800
Che do KHO (khong ton API, chi cao + luu, de kiem duong ong):  python lab.py --kho

Xem PROMPT_DEEPSEEK.md (system prompt) va README_LAB.md (cach cam may chu).
"""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import time
from pathlib import Path
from urllib.parse import quote

import requests

# --------------------------------------------------------------- cau hinh
LAB = Path(__file__).parent
DU_AN = LAB.parent
DB = LAB / "thu_vien.db"
PROMPT = (LAB / "PROMPT_DEEPSEEK.md").read_text(encoding="utf-8")
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API = "https://api.deepseek.com/chat/completions"
UA = {"User-Agent": "Mozilla/5.0 (quant research lab)"}
NGUONG_DIEM = 8

# MT5 (dung terminal MetaQuotes co du lieu M1 sau)
# Duong MT5 doc qua `nhan.duong_dan`: bien BRAIN_MT5 -> cac cho cai thong
# thuong -> mac dinh. Go cung o day thi he gay ngay khi chuyen VPS, va dich do
# da duoc chu du an chot 12/09/2026.
from nhan.duong_dan import mt5_exe as _mt5_exe

MT5 = _mt5_exe() or Path(r"C:\Program Files\MetaTrader 5\terminal64.exe")
MT5_DATA = Path(r"C:\Users\SV STORE\AppData\Roaming\MetaQuotes\Terminal"
                r"\D0E8209F77C8CF37AD8BF550E51FF075")
EA = "LuoiDoiXung"
CAP_CHINH = "EURCAD"
CAP_KIEM_CHEO = ["NZDCAD", "EURGBP"]
TU, DEN, NAM = "2013.03.01", "2026.07.31", 13.42
VON = 20000.0
EA_INPUT_MAC_DINH = dict(
    LotCoSo=0.01, BuocPip=30.0, HeSoBuoc=1.0, BuocTranPip=400.0, TP_Pip=20.0,
    TangToiDa=60, HeSoLot1=1.0, NhomDau=4, HeSoLot2=1.0, LotToiDa=20.0,
    LocEntry=0, EMA_ChuKy=50, LechATR=2.0, ChoLuiPip=10.0, ChoToiDaNen=120,
    BatChotCap="true", BienCapPip=4.0, ChotTien_0v01=2.5, DungLo_0v01=4000.0,
    MagicMua=770001, MagicBan=770002, TruotToiDa=20, ChoPhepGiaoDich="true")


# --------------------------------------------------------------- kho SQLite
def mo_db():
    c = sqlite3.connect(DB)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS muc(
        id TEXT PRIMARY KEY, nguon TEXT, ten TEXT, url TEXT, ngay REAL,
        da_xu INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS co_che(
        id INTEGER PRIMARY KEY AUTOINCREMENT, muc_id TEXT, ten TEXT, loai TEXT,
        vao_lenh TEXT, quan_ly TEXT, thoat TEXT, moi TEXT, diem INTEGER,
        json TEXT, phan_quyet TEXT DEFAULT 'CHUA_KIEM',
        pf REAL, loi_nam REAL, dd REAL, da_kiem INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS moc(
        id INTEGER PRIMARY KEY CHECK(id=1), ten TEXT, input TEXT,
        pf REAL, loi_nam REAL, dd REAL, ghi_chu TEXT);
    """)
    c.commit()
    return c


def bam(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------- 1. CAO
def cao_mql5(n=15):
    ra = []
    for muc in ("experts", "indicators"):
        try:
            h = requests.get(f"https://www.mql5.com/en/code/mt5/{muc}",
                             headers=UA, timeout=30).text
        except Exception as e:
            print(f"    mql5 {muc}: {e}")
            continue
        for m in re.finditer(r'href="(/en/code/\d+)"[^>]*>([^<]{5,120})<', h):
            ra.append({"nguon": "mql5", "url": "https://www.mql5.com" + m.group(1),
                       "ten": m.group(2).strip()})
            if len(ra) >= n:
                return ra
    return ra


def cao_github(n=15):
    ra = []
    for q in ("metatrader5 expert advisor", "mql5 grid martingale ea",
              "pine script mean reversion strategy", "forex dca ea"):
        try:
            j = requests.get("https://api.github.com/search/repositories?q="
                             + quote(q) + "&sort=stars&per_page=6",
                             headers=UA, timeout=30).json()
        except Exception as e:
            print(f"    github: {e}")
            continue
        for it in j.get("items", []):
            ra.append({"nguon": "github", "url": it["html_url"],
                       "ten": f"{it['full_name']} ({it.get('stargazers_count',0)}*)"})
        time.sleep(2)
        if len(ra) >= n:
            break
    return ra[:n]


def cao_forum(n=10):
    """Dien dan FX cong khai: Forex Factory (khu Trading Systems), BabyPips."""
    ra = []
    for url, nhan in (("https://www.forexfactory.com/forum/71-trading-systems", "ff"),
                      ("https://forums.babypips.com/c/free-forex-trading-systems/",
                       "babypips")):
        try:
            h = requests.get(url, headers=UA, timeout=30).text
        except Exception as e:
            print(f"    forum {nhan}: {e}")
            continue
        for m in re.finditer(r'href="(https?://[^"]+/(?:showthread|t/)[^"]+)"[^>]*>'
                             r'([^<]{8,120})<', h):
            ra.append({"nguon": f"forum_{nhan}", "url": m.group(1),
                       "ten": m.group(2).strip()})
            if len(ra) >= n:
                return ra
    return ra


def cao_youtube(n=8):
    """Clip tac gia bot (tieng Viet): tim video, lay PHU DE lam van ban.
    Can yt-dlp: pip install yt-dlp. Neu khong co thi bo qua nguon nay."""
    try:
        import yt_dlp  # noqa
    except Exception:
        return []
    ra = []
    tu_khoa = ["EA forex mien phi", "bot trade vang", "chien luoc DCA forex",
               "grid ea backtest"]
    for q in tu_khoa:
        try:
            with __import__("yt_dlp").YoutubeDL(
                    {"quiet": True, "extract_flat": True,
                     "playlistend": 3}) as y:
                r = y.extract_info(f"ytsearch3:{q}", download=False)
            for e in r.get("entries", []):
                ra.append({"nguon": "youtube",
                           "url": f"https://youtube.com/watch?v={e['id']}",
                           "ten": e.get("title", q)})
        except Exception as e:
            print(f"    youtube: {e}")
        if len(ra) >= n:
            break
    return ra[:n]


def nap_thu_cong():
    """FB/TikTok/trang dong khong cao tu dong duoc (login, chong bot). Nguoi dung DAN
    link + noi dung vao file lab/hang_doi_thu_cong.txt (moi muc cach nhau bang '---').
    Day la 'ban tu dong': con nguoi lam phan lay du lieu, lab lam phan phan tich."""
    f = LAB / "hang_doi_thu_cong.txt"
    if not f.exists():
        f.write_text("# DAN link + noi dung tu FB/TikTok/trang khac vao day.\n"
                     "# Moi muc mot khoi, cach nhau bang mot dong ---\n"
                     "# Vi du:\n#   https://facebook.com/... \n#   (noi dung bot,"
                     " tham so, chien luoc...)\n---\n", encoding="utf-8")
        return []
    khoi = [k.strip() for k in f.read_text(encoding="utf-8").split("---")
            if k.strip() and not k.strip().startswith("#")]
    ra = []
    for k in khoi:
        d = k.splitlines()
        url = next((x for x in d if x.startswith("http")), "thu_cong")
        ra.append({"nguon": "thu_cong", "url": url, "ten": d[0][:100],
                   "van_ban_san": k})
    return ra


def lay_van_ban(url):
    try:
        h = requests.get(url, headers=UA, timeout=40).text
    except Exception:
        return ""
    h = re.sub(r"<(script|style).*?</\1>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", h)[:24000]


# --------------------------------------------------------------- 2. DeepSeek
def hoi_ds(noi_dung, temperature=0.2):
    if not KEY:
        raise RuntimeError("Chua co DEEPSEEK_API_KEY")
    r = requests.post(API, timeout=180, headers={
        "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        json={"model": "deepseek-chat", "temperature": temperature, "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": noi_dung}]})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def json_tu(y):
    y = re.sub(r"^```(?:json)?|```$", "", y.strip(), flags=re.M).strip()
    try:
        return json.loads(y)
    except Exception:
        m = re.search(r"[\[{].*[\]}]", y, re.S)
        return json.loads(m.group(0)) if m else None


# --------------------------------------------------------------- 5. MT5 tester
def dong_mt5():
    # Xem ghi chu o `nhan/khoa_tester.dong_terminal` - khong duoc giet thang.
    from nhan import khoa_tester
    khoa_tester.dong_terminal("lab.dong_mt5")


def viet_set(ten, input_ghi_de):
    p = dict(EA_INPUT_MAC_DINH)
    p.update(input_ghi_de)
    d = "".join(f"{k}={v}||{v}||0||0||N\n" for k, v in p.items())
    tp = MT5_DATA / "MQL5" / "Profiles" / "Tester"
    tp.mkdir(parents=True, exist_ok=True)
    (tp / f"{ten}.set").write_text(d, encoding="utf-16")


def chay_tester(ten, symbol=CAP_CHINH, tu=TU, den=DEN):
    ini = MT5_DATA / f"lab_{ten}.ini"
    ini.write_text(f"[Tester]\nExpert={EA}\nExpertParameters={ten}.set\n"
                   f"Symbol={symbol}\nPeriod=M1\nModel=1\nOptimization=0\n"
                   f"FromDate={tu}\nToDate={den}\nDeposit=20000\nCurrency=USD\n"
                   f"Leverage=1:500\nReport=reports\\lab_{ten}\nReplaceReport=1\n"
                   f"ShutdownTerminal=1\nVisual=0\n", encoding="utf-16")
    t0 = time.time()
    subprocess.Popen([str(MT5), f"/config:{ini}"])
    time.sleep(8)
    while "terminal64.exe" in subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
            capture_output=True, text=True).stdout:
        if time.time() - t0 > 2400:
            dong_mt5()
            break
        time.sleep(12)
    return doc_tester(ten)


def doc_tester(ten):
    p = MT5_DATA / "reports" / f"lab_{ten}.htm"
    if not p.exists():
        return None
    t = p.read_text(encoding="utf-16", errors="ignore")
    o = [x.strip() for x in re.sub(r"<[^>]+>", "\n", t).split("\n") if x.strip()]
    khoa = {"Total Net Profit": "loi", "Profit Factor": "pf",
            "Sharpe Ratio": "sharpe", "Equity Drawdown Maximal": "dd",
            "Total Trades": "lenh"}
    r = {}
    for i, x in enumerate(o):
        n = x.rstrip(":").strip()
        if n in khoa and khoa[n] not in r and i + 1 < len(o):
            m = re.search(r"-?[\d\s]+[.,]?\d*", o[i + 1].replace("\xa0", " "))
            if m:
                r[khoa[n]] = float(m.group(0).replace(" ", "").replace(",", ""))
    return r or None


# --------------------------------------------------------------- vong lap
def cao_va_rut(con, kho_mode):
    moi = (cao_mql5() + cao_github() + cao_forum() + cao_youtube()
           + nap_thu_cong())
    them = 0
    for it in moi:
        i = bam(it["url"])
        if con.execute("SELECT 1 FROM muc WHERE id=?", (i,)).fetchone():
            continue
        con.execute("INSERT INTO muc VALUES(?,?,?,?,?,0)",
                    (i, it["nguon"], it["ten"], it["url"], time.time()))
        them += 1
    con.commit()
    print(f"  cao: {len(moi)} muc, {them} moi")
    if kho_mode:
        return 0
    van_ban_san = {bam(it["url"]): it.get("van_ban_san")
                   for it in moi if it.get("van_ban_san")}
    cho = con.execute("SELECT id,ten,url FROM muc WHERE da_xu=0 LIMIT 8").fetchall()
    n_cc = 0
    for mid, ten, url in cho:
        vb = van_ban_san.get(mid) or lay_van_ban(url)
        if len(vb) < 400:
            con.execute("UPDATE muc SET da_xu=1 WHERE id=?", (mid,))
            continue
        try:
            pl = json_tu(hoi_ds(f"B1. PHAN LOAI NGUON.\nTieu de: {ten}\nURL: {url}\n"
                                f"Van ban:\n{vb[:3000]}"))
            if not pl or not pl.get("lien_quan"):
                con.execute("UPDATE muc SET da_xu=1 WHERE id=?", (mid,))
                continue
            ds = json_tu(hoi_ds(f"B2. RUT CO CHE.\nTieu de: {ten}\nNguon: {url}\n"
                                f"Van ban:\n{vb}")) or []
        except Exception as e:
            print(f"    DeepSeek loi ({ten[:35]}): {e}")
            continue
        for cc in ds:
            con.execute("""INSERT INTO co_che(muc_id,ten,loai,vao_lenh,quan_ly,thoat,
                moi,diem,json) VALUES(?,?,?,?,?,?,?,?,?)""",
                        (mid, cc.get("ten", ten), cc.get("loai", ""),
                         cc.get("vao_lenh", ""), cc.get("quan_ly", ""),
                         cc.get("thoat", ""), cc.get("moi_so_voi_thu_vien", ""),
                         int(cc.get("diem", 0)),
                         json.dumps(cc, ensure_ascii=False)))
            n_cc += 1
        con.execute("UPDATE muc SET da_xu=1 WHERE id=?", (mid,))
        con.commit()
        time.sleep(1)
    print(f"  rut: {n_cc} co che tu {len(cho)} muc")
    return n_cc


def kiem_chung(con):
    """Lay co che diem cao chua kiem -> DeepSeek sinh tham so -> chay tester -> phan quyet."""
    hd = con.execute("SELECT id,ten,json FROM co_che WHERE diem>=? AND da_kiem=0 "
                     "ORDER BY diem DESC LIMIT 2", (NGUONG_DIEM,)).fetchall()
    if not hd:
        print("  hang doi kiem chung: rong")
        return
    for cid, ten, js in hd:
        try:
            am = json_tu(hoi_ds(f"B3. SINH THAM SO KIEM CHUNG.\nCo che:\n{js}\n\n"
                                f"EA input mac dinh: {json.dumps(EA_INPUT_MAC_DINH)}"))
        except Exception as e:
            print(f"    B3 loi: {e}")
            continue
        if not am or not am.get("anh_xa_duoc"):
            con.execute("UPDATE co_che SET da_kiem=1, phan_quyet='KHONG_ANH_XA' "
                        "WHERE id=?", (cid,))
            con.commit()
            print(f"    [{ten[:40]}] can EA moi: {am.get('can_input_moi') if am else '?'}")
            continue
        bang = []
        dong_mt5()
        for i, ch in enumerate(am.get("cau_hinh", [])[:4]):
            nhan = f"c{cid}_{i}"
            viet_set(nhan, ch.get("input", {}))
            kq = chay_tester(nhan)
            if kq:
                kq["ten"] = ch.get("ten", nhan)
                kq["nam"] = NAM
                bang.append(kq)
                print(f"    {ch.get('ten',nhan):<20} PF {kq.get('pf')} · "
                      f"lai {kq.get('loi',0):,.0f}$ · DD {kq.get('dd',0):,.0f}$")
        moc = con.execute("SELECT pf,loi_nam,dd FROM moc WHERE id=1").fetchone()
        try:
            pq = json_tu(hoi_ds(f"B4. DOC KET QUA + TINH CHINH.\n"
                                f"Ket qua:\n{json.dumps(bang, ensure_ascii=False)}\n"
                                f"Moc hien tai (pf,loi_nam,dd): {moc}"))
        except Exception as e:
            print(f"    B4 loi: {e}")
            pq = None
        tot = max(bang, key=lambda z: z.get("pf", 0)) if bang else None
        con.execute("UPDATE co_che SET da_kiem=1, phan_quyet=?, pf=?, loi_nam=?, dd=? "
                    "WHERE id=?",
                    (pq.get("phan_quyet", "CHUA_RO") if pq else "CHUA_RO",
                     tot.get("pf") if tot else None,
                     tot.get("loi", 0) / NAM if tot else None,
                     tot.get("dd") if tot else None, cid))
        con.commit()
        print(f"    -> {pq.get('phan_quyet') if pq else '?'}: "
              f"{pq.get('ly_do','') if pq else ''}")
        # cap nhat moc neu vuot va da THAT
        if pq and pq.get("phan_quyet") == "THAT" and tot and moc and \
                tot.get("pf", 0) > (moc[0] or 0):
            con.execute("UPDATE moc SET pf=?, loi_nam=?, dd=?, ghi_chu=? WHERE id=1",
                        (tot["pf"], tot["loi"] / NAM, tot["dd"], ten))
            con.commit()
            print(f"    *** MOC MOI: {ten} PF {tot['pf']} ***")


def mot_vong(con, kho_mode):
    cao_va_rut(con, kho_mode)
    if not kho_mode:
        kiem_chung(con)
    d = con.execute("SELECT COUNT(*), SUM(da_xu) FROM muc").fetchone()
    cc = con.execute("SELECT COUNT(*), SUM(da_kiem) FROM co_che").fetchone()
    that = con.execute("SELECT COUNT(*) FROM co_che WHERE phan_quyet='THAT'").fetchone()
    print(f"  thu vien: {d[0]} muc ({d[1] or 0} da xu) · {cc[0]} co che "
          f"({cc[1] or 0} da kiem) · {that[0]} THAT")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vong", type=int, default=1)
    ap.add_argument("--lien-tuc", action="store_true")
    ap.add_argument("--nghi", type=int, default=1800)
    ap.add_argument("--kho", action="store_true", help="chi cao+luu, khong goi API")
    a = ap.parse_args()
    con = mo_db()
    con.execute("INSERT OR IGNORE INTO moc VALUES(1,'EURCAD ema50-2atr dl4000',"
                "'',1.71,559,3194,'cau hinh thang kiem cheo 02/08')")
    con.commit()
    if not KEY and not a.kho:
        print("  !! chua co DEEPSEEK_API_KEY — chay che do --kho (chi cao).\n"
              '     setx DEEPSEEK_API_KEY "sk-..." roi mo lai PowerShell.')
        a.kho = True
    n = 0
    while True:
        n += 1
        print(f"\n=== VONG {n} · {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
        try:
            mot_vong(con, a.kho)
        except Exception as e:
            print(f"  vong loi: {e}")
        if not a.lien_tuc and n >= a.vong:
            break
        time.sleep(a.nghi)


if __name__ == "__main__":
    main()
