# -*- coding: utf-8 -*-
"""seeker_theo_doi.py - SEEKER: theo doi ca nhan / nhom chat luong.

Giong nhu "Theo doi" tren mang xa hoi: sau khi cong dong quet ra duoc cac ca nhan /
nhom / kenh chat luong, module nay GIU LAI ho so (bang `theo_doi`) roi QUET LAI
HANG NGAY de nha tieng bai moi / chien luoc moi tu ho so do, dua vao duong ong
(bang `muc` + task scout) de BRAIN rut co che.

Chay:
  python seeker_theo_doi.py --xem                 ; danh sach ho so dang theo doi
  python seeker_theo_doi.py --duyet              ; tu cong_dong, de cu/tu dong them ho so tot vao theo doi
  python seeker_theo_doi.py --them 'url|ten|loai|truy_cap'   ; them ho so bang tay
  python seeker_theo_doi.py --quet               ; quet lai TAT CA ho so de co bai moi (hang ngay)
  python seeker_theo_doi.py --quet 'ten'         ; quet rieng 1 ho so (theo ten chua trong ten/url)
  python seeker_theo_doi.py --chay-ca            ; duyet ROI quet (dung cho lich hang ngay)

Truy cap duoc (lay bai moi):  web, youtube(RSS), reddit(submitted.json), telegram(telethon).
Khong lay duoc tu dang nhap (facebook/x/instagram/tiktok/discord) -> ghi chu, can ban do tay.
"""
import re
import sqlite3
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent
DB_PATH = LAB / "thu_vien.db"

# Loai cong dong mang y nghia "ca nhan/nhom chat luong" -> uu tien dua vao theo doi
CAO_SIGNAL = {"trader_huyen_thoai", "trader_dang_dai", "trader_top", "nguoi_thang_1pct",
              "nguoi_loi_nhuan", "quy_giao_dich", "cho_phuong_phap", "cho_tin_hieu",
              "cong_dong_nghien_cuu"}
# Loai nay chi la dien dan rong -> khong tu dong theo doi (de nguoi dung duyet)
TRUNG_LAP = {"dien_dan"}

DDL = """
CREATE TABLE IF NOT EXISTS theo_doi(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loai TEXT, ten TEXT, url TEXT, truy_cap TEXT,
    diem REAL DEFAULT 0, so_bai_tot INTEGER DEFAULT 0,
    lan_them REAL, lan_quet_cuoi REAL DEFAULT 0,
    trang_thai TEXT DEFAULT 'THEO_DOI', ghi_chu TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS bai_theo_doi(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ho_so_id INTEGER, khoa TEXT, ten TEXT, url TEXT, diem REAL DEFAULT 0, luc REAL,
    UNIQUE(ho_so_id, khoa));
"""

# ------------------------------------------------------------- ket noi
def mo_db():
    con = sqlite3.connect(str(DB_PATH))
    con.executescript(DDL)
    con.commit()
    return con


def _ve_truy_cap(url):
    u = (url or "").lower()
    if "youtube" in u or "youtu.be" in u: return "youtube"
    if "reddit" in u: return "reddit"
    if "t.me" in u or ("telegram" in u): return "telegram"
    if "facebook" in u or "fb.com" in u: return "facebook"
    if "x.com" in u or "/twitter" in u: return "x"
    if "instagram" in u: return "instagram"
    if "tiktok" in u: return "tiktok"
    if "discord" in u: return "discord"
    if "warpcast" in u or "threads.net" in u: return "web"
    return "web"


def _bam(s):
    import hashlib
    return hashlib.sha1((s or "").encode("utf-8")).hexdigest()[:16]


# ------------------------------------------------------------- them + xem
def them(con, url, ten=None, loai="trader_top", truy_cap=None, ghi_chu=""):
    url = (url or "").strip()
    if not url:
        return 0
    truy_cap = truy_cap or _ve_truy_cap(url)
    ten = ten or url
    row = con.execute("SELECT id FROM theo_doi WHERE url=?", (url,)).fetchone()
    if row:
        con.execute("UPDATE theo_doi SET lan_them=?, ghi_chu=? WHERE id=?",
                    (time.time(), ghi_chu or "cap nhat", row[0]))
        con.commit()
        return 1
    con.execute("""INSERT INTO theo_doi(loai,ten,url,truy_cap,diem,lan_them,ghi_chu)
                   VALUES(?,?,?,?,?,?,?)""",
                (loai, ten[:160], url, truy_cap, 8.0, time.time(), ghi_chu or "tay/duyet"))
    con.commit()
    return 1


def duyet_tu_cong_dong(con, toi_thieu_lan=2):
    """Tu bang cong_dong, tu dong them vao theo doi nhung url xuat hien nhieu
    lan hoac thuoc loai 'chat luong cao'. Tra so ho so moi them."""
    rows = con.execute("SELECT loai,ten,url,ngon_ngu,truy_cap FROM cong_dong").fetchall()
    dem = {}
    for loai, ten, url, nn, tc in rows:
        if not url:
            continue
        # bo dien dan rong (duyet tay) + nhung duong khong phai ho so ca nhan
        if loai in TRUNG_LAP:
            continue
        e = dem.setdefault(url, {"loai": loai, "ten": ten, "truy_cap": tc or _ve_truy_cap(url), "dem": 0})
        e["dem"] += 1
    them_moi = 0
    for url, e in dem.items():
        diem = e["dem"]
        if e["loai"] in CAO_SIGNAL:
            diem += 3
        if e["dem"] < toi_thieu_lan and e["loai"] not in CAO_SIGNAL:
            continue  # roi rac, loai trung binh -> de nguoi dung duyet tay
        try:
            them(con, url, e["ten"], e["loai"], e["truy_cap"],
                 ghi_chu=f"tu dong (xuat hien {e['dem']} lan, loai {e['loai']})")
            them_moi += 1
        except Exception:
            pass
    return them_moi


def xem(con):
    print("=== THEO DOI (SEEKER) ===")
    rows = con.execute("""SELECT id,loai,ten,url,truy_cap,diem,so_bai_tot,lan_quet_cuoi,trang_thai,ghi_chu
        FROM theo_doi ORDER BY diem DESC, lan_them""").fetchall()
    if not rows:
        print("  (chua co ai duoc theo doi - chay --duyet hoac --them)")
        return
    for (i, loai, ten, url, tc, diem, so_bai, lan_quet, tt, gc) in rows:
        last = time.strftime("%m-%d %H:%M", time.localtime(lan_quet)) if lan_quet else "chua"
        print(f"  #{i:<4} diem={diem:<4} bai={so_bai:<3} {tt:<8} {tc:<8} lan-quet={last}")
        print(f"        {ten[:70]}")
        print(f"        {url[:90]}  ({gc[:60]})")


# ------------------------------------------------------------- lay bai moi
def _lay_toc():
    import toc_do
    return toc_do


def _bai_web(url, han=8):
    """Generic web: lay link + tieu de tu trang ho so."""
    td = _lay_toc()
    r = td.lay(url, nguon="theo_doi", timeout=25)
    if r is None:
        return []
    text = getattr(r, "text", "") or ""
    out = []
    seen = set()
    for m in re.finditer(r'<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', text, re.S):
        u = m.group(1).strip()
        t = re.sub(r"<[^>]+>", " ", m.group(2)).strip()
        t = re.sub(r"\s+", " ", t)[:120]
        if not t or not u.startswith("http"):
            continue
        if u in seen:
            continue
        seen.add(u)
        out.append({"khoa": u, "ten": t, "url": u})
        if len(out) >= han:
            break
    return out


def _bai_youtube(url, han=10):
    """Tai nguoi dung youtube /@handle hoac /channel/... qua RSS feed."""
    td = _lay_toc()
    rss = None
    m = re.search(r"youtube\.com/channel/([\w-]+)", url)
    if m:
        rss = "https://www.youtube.com/feeds/videos.xml?channel_id=" + m.group(1)
    else:
        # /@handle hoac /c/... -> lay trang de tim channel_id (meta)
        try:
            r = td.lay(url, nguon="theo_doi", timeout=25)
            if r is None:
                return []
            txt = getattr(r, "text", "") or ""
            cm = re.search(r'"channelId"\s*:\s*"([\w-]+)"', txt) or \
                 re.search(r'channel_id=([\w-]+)', txt) or \
                 re.search(r'/(?:channel)/([\w-]+)', txt)
            if cm:
                rss = "https://www.youtube.com/feeds/videos.xml?channel_id=" + cm.group(1)
        except Exception:
            return []
    if not rss:
        return []
    r = td.lay(rss, nguon="theo_doi", timeout=25)
    if r is None:
        return []
    text = getattr(r, "text", "") or ""
    ent = re.findall(r"<entry>(.*?)</entry>", text, re.S)
    out = []
    for e in ent[:han]:
        tt = (re.search(r"<title>(.*?)</title>", e, re.S) or [None, ""])[1]
        ten = re.sub(r"<[^>]+>", "", tt or "").strip()
        pub = (re.search(r"<published>(.*?)</published>", e, re.S) or [None, ""])[1]
        if not ten:
            continue
        vid = re.search(r"<yt:videoId>(.*?)</yt:videoId>", e, re.S) or re.search(r"<(?:yt:)?videoId>(.*?)</(?:yt:)?videoId>", e, re.S)
        tu = "https://www.youtube.com/watch?v=" + vid.group(1) if vid else ""
        out.append({"khoa": (pub[:10] or "") + "|" + ten[:60], "ten": ten, "url": tu})
    return out


def _bai_reddit(url, han=10):
    """User reddit: /user/<u>/submitted.json (JSON API co the bi 403 -> de nguon khac)."""
    td = _lay_toc()
    u = (url.rstrip("/") + "/submitted.json").replace("/submitted.json/submitted.json", "/submitted.json")
    hdr = {"User-Agent": "Mozilla/5.0 (research-brain)"}
    r = td.lay(u, nguon="theo_doi", headers=hdr, timeout=25)
    if r is None:
        return []
    try:
        j = r.json()
        ch = j.get("data", {}).get("children", [])
    except Exception:
        return []
    out = []
    for c in ch[:han]:
        d = c.get("data", {})
        t = d.get("title", "")
        if not t:
            continue
        perma = "https://www.reddit.com" + (d.get("permalink") or "")
        out.append({"khoa": d.get("id") or t[:40], "ten": t[:140], "url": perma})
    return out


def _bai_telegram(url, ten, han=8):
    """Doc kenh telegram da dang nhap (telethon). Can session co san."""
    import asyncio
    import telethon_ban as tb
    ref = url
    if "t.me/" in (url or ""):
        ref = url.split("t.me/", 1)[1].split("/", 1)[0]
    try:
        ds = asyncio.run(tb._doc_kenh(ref or ten, so=han))
    except Exception:
        return []
    out = []
    for m in ds:
        txt = (m.get("text") or "").strip() if isinstance(m, dict) else str(m)
        if not txt:
            continue
        out.append({"khoa": txt[:60], "ten": txt[:140], "url": ""})
    return out


def _lay_bai_moi(url, ten, truy_cap, han=8):
    if truy_cap == "youtube":
        return _bai_youtube(url, han)
    if truy_cap == "reddit":
        return _bai_reddit(url, han)
    if truy_cap == "telegram":
        return _bai_telegram(url, ten, han)
    if truy_cap == "web":
        return _bai_web(url, han)
    # facebook/x/instagram/tiktok/discord -> can dang nhap
    return []


def _dua_vao_pipeline(con, ten, url, nguon):
    """Ghi bai moi vao bang `muc` + tao task scout de BRAIN rut co che."""
    if not url:
        return False
    try:
        import bo_nao
    except Exception:
        bo_nao = None
    mid = _bam(url)
    nguon_td = "theo_doi:" + (nguon or "")[:40]
    con.execute("INSERT OR IGNORE INTO muc(id,nguon,ten,url,ngay,da_xu) VALUES(?,?,?,?,?,0)",
                (mid, nguon_td, ten[:200], url, time.time()))
    con.commit()
    if bo_nao is not None:
        bo_nao.tao_task(con, "scout", {"ten": ten[:160], "url": url, "van_ban": ""},
                        muc_id=mid, uu_tien=bo_nao.UU_TIEN_TANG["scout"])
    return True


def quet_theo_doi(con, loc=None, han_post=8):
    """Quet lai cac ho so dang THEO_DOI. loc: chuoi khop trong ten/url (None = all).
    Tra (ds_bai_moi_them, ds_loi)."""
    if loc:
        q = "SELECT id,loai,ten,url,truy_cap FROM theo_doi WHERE trang_thai='THEO_DOI' AND (ten LIKE ? OR url LIKE ?)"
        rows = con.execute(q, ("%" + loc + "%", "%" + loc + "%")).fetchall()
    else:
        rows = con.execute("SELECT id,loai,ten,url,truy_cap FROM theo_doi WHERE trang_thai='THEO_DOI'").fetchall()
    bai_moi = []
    loi = []
    for (id2, loai, ten, url, tc) in rows:
        try:
            ds_bai = _lay_bai_moi(url, ten, tc, han_post)
        except Exception as e:
            con.execute("UPDATE theo_doi SET ghi_chu=?, lan_quet_cuoi=? WHERE id=?",
                        ("loi " + str(e)[:80], time.time(), id2))
            con.commit()
            loi.append((id2, ten, str(e)[:50]))
            continue
        them = 0
        for b in ds_bai:
            khoa = b["khoa"]
            if con.execute("SELECT 1 FROM bai_theo_doi WHERE ho_so_id=? AND khoa=?",
                           (id2, khoa)).fetchone():
                continue
            con.execute("INSERT INTO bai_theo_doi(ho_so_id,khoa,ten,url,luc) VALUES(?,?,?,?,?)",
                        (id2, khoa, b["ten"][:200], (b.get("url") or "")[:300], time.time()))
            con.execute("UPDATE theo_doi SET so_bai_tot=so_bai_tot+1 WHERE id=?", (id2,))
            them += 1
            try:
                _dua_vao_pipeline(con, b["ten"], b.get("url") or url, ten)
            except Exception:
                pass
        con.execute("UPDATE theo_doi SET lan_quet_cuoi=? WHERE id=?", (time.time(), id2))
        con.commit()
        if them or not ds_bai:
            bai_moi.append((id2, ten, them))
    return bai_moi, loi


def chay_ca():
    """duyet tu cong dong ROI quet lai (dung cho lich quan_li_quet hang ngay)."""
    con = mo_db()
    n = duyet_tu_cong_dong(con)
    bai_moi, loi = quet_theo_doi(con)
    return n, bai_moi, loi


# ------------------------------------------------------------- CLI
def main():
    import sys
    con = mo_db()
    args = sys.argv[1:]
    if "--them" in args:
        s = args[args.index("--them") + 1]
        p = s.split("|")
        url = p[0].strip()
        ten = p[1].strip() if len(p) > 1 and p[1].strip() else None
        loai = p[2].strip() if len(p) > 2 and p[2].strip() else "trader_top"
        tc = p[3].strip() if len(p) > 3 and p[3].strip() else None
        n = them(con, url, ten, loai, tc)
        print(f"Them {n} ho so -> theo doi. Xem: --xem")
        return
    if "--duyet" in args:
        n = duyet_tu_cong_dong(con)
        print(f"Tu cong dong: tu dong them {n} ho so Good vao theo doi.")
        xem(con)
        return
    if "--quet" in args:
        loc = None
        if args.index("--quet") + 1 < len(args):
            v = args[args.index("--quet") + 1]
            if not v.startswith("--"):
                loc = v
        bai_moi, loi = quet_theo_doi(con, loc)
        print(f"Quet lai xong. {len(bai_moi)} ho so, bai moi tong: {sum(t for _,_,t in bai_moi)}")
        for i, ten, t in bai_moi:
            print(f"  #{i} {ten[:60]}: +{t} bai moi")
        if loi:
            print("Loi (can xu ly):")
            for i, ten, e in loi:
                print(f"  #{i} {ten[:40]}: {e}")
        return
    if "--chay-ca" in args:
        n, bai_moi, loi = chay_ca()
        print(f"chay-ca: duyet {n} | quet {len(bai_moi)} | bai moi {sum(t for _,_,t in bai_moi)} | loi {len(loi)}")
        return
    xem(con)


if __name__ == "__main__":
    main()
