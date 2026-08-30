# -*- coding: utf-8 -*-
"""
chay_lab.py - Phong lab quet he thong giao dich 24/7, dieu khien bang DeepSeek
==============================================================================
Vong lap: QUET nguon -> RUT CO CHE bang DeepSeek -> XEP UU TIEN -> ghi thu vien
-> sinh cau hinh kiem chung cho bo mo phong M1 co san.

Chay mot vong :  python chay_lab.py --vong 1
Chay 24/7     :  python chay_lab.py --lien-tuc --nghi 1800

Can bien moi truong:  DEEPSEEK_API_KEY
    setx DEEPSEEK_API_KEY "sk-..."      (mo lai PowerShell sau khi dat)
"""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import time
from pathlib import Path
from urllib.parse import quote

import requests

R = Path(__file__).parent
DB = R / "thu_vien.db"
MA = R / "ma_tai_ve"
PROMPT = (R / "LAB_MASTER_PROMPT.md").read_text(encoding="utf-8")
API = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
UA = {"User-Agent": "Mozilla/5.0 (research lab)"}


# ----------------------------------------------------------------- kho
def mo_db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS muc(
        id TEXT PRIMARY KEY, nguon TEXT, ten TEXT, url TEXT, ngay REAL,
        da_rut INTEGER DEFAULT 0)""")
    con.execute("""CREATE TABLE IF NOT EXISTS co_che(
        id INTEGER PRIMARY KEY AUTOINCREMENT, muc_id TEXT, ten TEXT, loai TEXT,
        vao_lenh TEXT, quan_ly TEXT, thoat TEXT, dang_chu_y TEXT,
        kiem_duoc INTEGER, diem INTEGER, phan_quyet TEXT DEFAULT 'CHUA_KIEM',
        ket_qua REAL, json TEXT)""")
    con.commit()
    return con


def bam(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


# -------------------------------------------------------------- nguon
def nguon_mql5(so=20):
    """MQL5 CodeBase — ma nguon mo, loc EA truoc roi den chi bao."""
    ra = []
    for muc in ("expert-advisors", "indicators"):
        u = f"https://www.mql5.com/en/code/mt5/{muc}"
        try:
            h = requests.get(u, headers=UA, timeout=30).text
        except Exception as e:
            print(f"    mql5 loi: {e}")
            continue
        for m in re.finditer(r'href="(/en/code/\d+)"[^>]*>([^<]{5,120})<', h):
            ra.append({"nguon": "mql5", "url": "https://www.mql5.com" + m.group(1),
                       "ten": m.group(2).strip()})
            if len(ra) >= so:
                return ra
    return ra


def nguon_github(so=20):
    """GitHub — uu tien repo co sao, tim EA/chi bao/grid."""
    ra = []
    for q in ("metatrader5 expert advisor", "mql5 grid ea",
              "pine script strategy mean reversion", "forex martingale ea"):
        u = ("https://api.github.com/search/repositories?q="
             + quote(q) + "&sort=stars&per_page=8")
        try:
            j = requests.get(u, headers=UA, timeout=30).json()
        except Exception as e:
            print(f"    github loi: {e}")
            continue
        for it in j.get("items", []):
            ra.append({"nguon": "github", "url": it["html_url"],
                       "ten": f"{it['full_name']} ({it.get('stargazers_count',0)}*)"})
            if len(ra) >= so:
                return ra
        time.sleep(2)
    return ra


def lay_noi_dung(url):
    try:
        h = requests.get(url, headers=UA, timeout=40).text
    except Exception:
        return ""
    h = re.sub(r"<script.*?</script>", " ", h, flags=re.S)
    h = re.sub(r"<style.*?</style>", " ", h, flags=re.S)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", h)[:24000]


# ----------------------------------------------------------- deepseek
def hoi(noi_dung, he_thong=PROMPT, model="deepseek-chat", nhiet=0.2):
    if not KEY:
        raise RuntimeError("Chua co DEEPSEEK_API_KEY. Chay: setx DEEPSEEK_API_KEY \"sk-...\"")
    r = requests.post(API, timeout=180, headers={
        "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        json={"model": model, "temperature": nhiet, "messages": [
            {"role": "system", "content": he_thong},
            {"role": "user", "content": noi_dung}]})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def rut_co_che(ten, url, van_ban):
    y = hoi(f"""BUOC 2 — RUT CO CHE.

Muc: {ten}
Nguon: {url}

Noi dung:
\"\"\"{van_ban}\"\"\"

Tra ve DUY NHAT mot mang JSON (khong giai thich, khong markdown) gom cac co che rut
duoc. Neu khong co co che nao dang chu y, tra ve [].
Moi phan tu dung dung so do trong Buoc 2 cua master prompt, THEM truong "diem"
(tong 0-12 theo Buoc 3) va "ly_do_diem".""")
    y = re.sub(r"^```(?:json)?|```$", "", y.strip(), flags=re.M).strip()
    try:
        return json.loads(y)
    except Exception:
        m = re.search(r"\[.*\]", y, re.S)
        return json.loads(m.group(0)) if m else []


# ------------------------------------------------------------- vong
def mot_vong(con, so_muc=12):
    moi = nguon_mql5(so_muc) + nguon_github(so_muc)
    them = 0
    for it in moi:
        i = bam(it["url"])
        if con.execute("SELECT 1 FROM muc WHERE id=?", (i,)).fetchone():
            continue
        con.execute("INSERT INTO muc(id,nguon,ten,url,ngay) VALUES(?,?,?,?,?)",
                    (i, it["nguon"], it["ten"], it["url"], time.time()))
        them += 1
    con.commit()
    print(f"  quet: {len(moi)} muc, {them} moi")

    cho = con.execute("SELECT id,ten,url FROM muc WHERE da_rut=0 LIMIT ?",
                      (so_muc,)).fetchall()
    rut = 0
    for mid, ten, url in cho:
        vb = lay_noi_dung(url)
        if len(vb) < 400:
            con.execute("UPDATE muc SET da_rut=1 WHERE id=?", (mid,))
            continue
        try:
            ds = rut_co_che(ten, url, vb)
        except Exception as e:
            print(f"    rut loi ({ten[:40]}): {e}")
            continue
        for cc in ds:
            con.execute("""INSERT INTO co_che(muc_id,ten,loai,vao_lenh,quan_ly,
                thoat,dang_chu_y,kiem_duoc,diem,json) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                        (mid, cc.get("ten", ten), cc.get("loai", ""),
                         cc.get("vao_lenh", ""), cc.get("quan_ly", ""),
                         cc.get("thoat", ""),
                         json.dumps(cc.get("co_che_dang_chu_y", []), ensure_ascii=False),
                         int(bool(cc.get("kiem_duoc_khong"))), int(cc.get("diem", 0)),
                         json.dumps(cc, ensure_ascii=False)))
            rut += 1
        con.execute("UPDATE muc SET da_rut=1 WHERE id=?", (mid,))
        con.commit()
        time.sleep(1)
    print(f"  rut: {rut} co che tu {len(cho)} muc")

    hd = con.execute("""SELECT ten,loai,diem,quan_ly FROM co_che
        WHERE diem>=8 AND phan_quyet='CHUA_KIEM' ORDER BY diem DESC LIMIT 10""").fetchall()
    print(f"  hang doi kiem chung: {len(hd)} co che >= 8 diem")
    for t, l, d, q in hd:
        print(f"    [{d:>2}] {l:<12} {t[:50]:<52} {q[:60]}")
    return len(hd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vong", type=int, default=1)
    ap.add_argument("--lien-tuc", action="store_true")
    ap.add_argument("--nghi", type=int, default=1800)
    ap.add_argument("--so-muc", type=int, default=12)
    a = ap.parse_args()
    MA.mkdir(exist_ok=True)
    con = mo_db()
    if not KEY:
        print("  !! Chua co DEEPSEEK_API_KEY — chi quet nguon, khong rut duoc co che.")
        print('     setx DEEPSEEK_API_KEY "sk-..."  roi mo lai PowerShell.\n')
    n = 0
    while True:
        n += 1
        print(f"\n=== VONG {n} · {time.strftime('%H:%M:%S')} ===")
        try:
            mot_vong(con, a.so_muc)
        except Exception as e:
            print(f"  vong loi: {e}")
        if not a.lien_tuc and n >= a.vong:
            break
        time.sleep(a.nghi)


if __name__ == "__main__":
    main()
