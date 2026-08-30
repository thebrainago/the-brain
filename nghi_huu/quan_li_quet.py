# -*- coding: utf-8 -*-
"""quan_li_quet.py - LICH QUET 24/7 cho cac nguon. Moi nguon co tan so rieng
(moi_gio). Chay lien tuc, tuan theo toc_do (khong spam). Ghi nhat ky + heartbeat.
Chay:  python quan_li_quet.py            (loop 24/7)
       python quan_li_quet.py --chay github   (chay 1 nguon roi thoat)
"""
import sys, time, json, pathlib, traceback
import toc_do

LAB = pathlib.Path(__file__).parent
STATE = LAB / "reports" / "lich_quet_state.json"
LOG = LAB / "reports" / "quet.log"
HB = LAB / "reports" / "quet_heartbeat.txt"

# ------------------------------------------------------------- cac collector
def _chay_github(so=12):
    import bo_nao
    con = bo_nao.mo_db()
    return f"cao_dan: them {bo_nao.cao_dan(con, so)} muc"

def _chay_quy(so_kenh=12):
    import telethon_ban as tb
    import asyncio, bo_nao
    ds = asyncio.run(tb.quet_quy(so_kenh=so_kenh, so_bai=6))
    con = bo_nao.mo_db()
    n = tb.luu(con, ds)
    return f"quy: doc {len(ds)}, them {n}"


def _chay_telethon(so_kenh=14):
    import telethon_ban as tb
    import asyncio, bo_nao
    ds = asyncio.run(tb.quet(so_kenh=so_kenh, so_bai=8))
    con = bo_nao.mo_db()
    n = tb.luu(con, ds)
    return f"telethon: doc {len(ds)}, them {n}"

def _chay_social():
    import subprocess, socket
    try:
        s_ = socket.create_connection(("127.0.0.1", 9222), timeout=2)
        s_.close()
    except Exception:
        return "social: CDP 9222 khong mo (bo qua - can Chrome .browser_thebrain2)"
    app_py = r"C:\Users\SV STORE\AppData\Local\Python\bin\python.exe"
    lab = pathlib.Path(__file__).parent
    try:
        r = subprocess.run([app_py, str(lab / "doc_cdp.py")], cwd=str(lab),
                           capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=240)
        out = (r.stdout or "").strip().splitlines()
        tong = [l for l in out if l.startswith("QUET duoc")]
        them = [l for l in out if l.startswith("LUU them")]
        return f"social: {tong[0] if tong else '0 bai'} | {them[0] if them else 'khong luu'}"
    except Exception as e:
        return f"social: loi {type(e).__name__}"


def _chay_evolution():
    import evolution as ev
    import bo_nao
    con = bo_nao.mo_db()
    n1, n2, n3 = ev.mo_rong_keyword(con)
    return f"evolution: vi_mo={n1}, cong_dong={n2}, dang_doi={n3}"

def _chay_kham_pha():
    import nguon_kham_pha as nk, importlib
    importlib.reload(nk)
    con = nk.mo_db() if hasattr(nk, "mo_db") else None
    import bo_nao
    con = bo_nao.mo_db()
    ds = nk.kham_pha_telegram(so_kenh=8, posts_moi_kenh=4)
    ds += nk.kham_pha_dan_mang()
    n = nk.luu(con, ds)
    return f"kham_pha: them {n} (tong {len(ds)})"
def _chay_cong_dong(ngon=None):
    import seeker_cong_dong as sc, importlib
    importlib.reload(sc)
    con = sc.mo_db()
    ds = sc.quet(ngon)
    n = sc.luu(con, ds)
    md = sc.ghi_md(con)
    return f"cong_dong: them {n} (tong {len(ds)}) -> {md.name}"

def _chay_mql5(so=12):
    import bo_nao
    con = bo_nao.mo_db()
    ng = bo_nao.cao_mql5(so)
    them = 0
    for it in ng:
        mid = bo_nao.bam(it["url"])
        if con.execute("SELECT 1 FROM muc WHERE id=?", (mid,)).fetchone():
            continue
        con.execute("INSERT OR IGNORE INTO muc VALUES(?,?,?,?,?,0)",
                    (mid, it["nguon"], it["ten"], it["url"], time.time()))
        bo_nao.tao_task(con, "scout", {"ten": it["ten"], "url": it["url"], "van_ban": ""},
                        muc_id=mid, uu_tien=bo_nao.UU_TIEN_TANG["scout"])
        them += 1
    return f"mql5: them {them} scout"

def _chay_youtube(ngon=None):
    import bo_nao, nguon_youtube as ny
    con = bo_nao.mo_db()
    ds = ny.quet(ngon)
    n = ny.luu(con, ds)
    return f"youtube: tim {len(ds)}, them {n}"

def _chay_banker():
    import bo_nao, banker
    con = bo_nao.mo_db()
    brief = banker.cap_nhat_macro_brief(con)
    return f"banker/fred: {brief}"

def _chay_telegram():
    import bo_nao, nguon_telegram as nt
    con = bo_nao.mo_db()
    ds, tb = nt.doc_kenh_cong_khai()
    n = nt.luu(con, ds)
    return f"telegram: doc {len(ds)}, them {n} | {tb[:120]}"

def _chay_reddit(so=25):
    """Reddit qua trinh duyet that (Playwright) - JSON API bi chan 403."""
    import subprocess
    app_py = r"C:\Users\SV STORE\AppData\Local\Python\bin\python.exe"
    lab = pathlib.Path(__file__).parent
    try:
        r = subprocess.run([app_py, str(lab / "nguon_reddit_sim.py")], cwd=str(lab),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=300)
        out = (r.stdout or "").strip().splitlines()
        return out[0] if out else f"reddit-sim: khong output (rc={r.returncode})"
    except Exception as e:
        return f"reddit-sim: loi {type(e).__name__}"


def _chay_dien_dan():
    """Dien dan (futures.io, quant, forexfactory, smartlab, traderviet) qua Playwright."""
    import subprocess
    app_py = r"C:\Users\SV STORE\AppData\Local\Python\bin\python.exe"
    lab = pathlib.Path(__file__).parent
    try:
        r = subprocess.run([app_py, str(lab / "nguon_dien_dan.py")], cwd=str(lab),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=420)
        out = (r.stdout or "").strip().splitlines()
        return out[0] if out else f"dien_dan: khong output (rc={r.returncode})"
    except Exception as e:
        return f"dien_dan: loi {type(e).__name__}"


def _chay_evo_nguon():
    import evo_nguon as en
    b = en.chay_main()
    return f"evo_nguon: bo loc {len(b['nguon'])} nguon"


def _chay_code():
    import bo_nao, nguon_code as nc
    ds, tk = nc.chay_tru()
    con = bo_nao.mo_db()
    n = nc.luu(con, ds)
    return f"code: {len(ds)} repo, them {n} file"


def _chay_darwinex():
    import darwinex_ocr as dx
    kq = dx.lay_darwin_cong_khai()
    msg = f"darwinex: doc {kq.get('so_darwin', 0)} DARWIN"
    if kq.get("ghi_chu") and kq.get("ghi_chu") != "OK":
        msg += " | " + str(kq.get("ghi_chu"))
    return msg


def _chay_theo_doi():
    """Theo doi (SEEKER): duyet tu cong_dong ROI quet lai cac ca nhan/nhom Good, lay bai moi (hang ngay)."""
    import seeker_theo_doi as td
    try:
        n, bai_moi, loi = td.chay_ca()
    except Exception as e:
        return f"theo_doi: loi {type(e).__name__}: {e}"
    tong = sum(t for _, _, t in bai_moi)
    return f"theo_doi: duyet {n} | quet {len(bai_moi)} ho so | {tong} bai moi | loi {len(loi)}"

# ------------------------------------------------------------- lich
LICH = {
    "github":     {"collector": _chay_github, "moi_gio": 2},
    "mql5":       {"collector": _chay_mql5,   "moi_gio": 4},
    "cong_dong":  {"collector": _chay_cong_dong, "moi_gio": 6},
    "wccta":      {"collector": _chay_cong_dong, "moi_gio": 12, "ngon": ["en"]},
    "kham_pha":   {"collector": _chay_kham_pha, "moi_gio": 8},
    "telethon":   {"collector": _chay_telethon, "moi_gio": 4},
    "quy":        {"collector": _chay_quy, "moi_gio": 4},
    "social":     {"collector": _chay_social, "moi_gio": 8},
    "youtube":    {"collector": _chay_youtube, "moi_gio": 6},
    "telegram":   {"collector": _chay_telegram, "moi_gio": 6},
    "banker":     {"collector": _chay_banker, "moi_gio": 12},
    "evolution":  {"collector": _chay_evolution, "moi_gio": 12},
    "reddit":     {"collector": _chay_reddit, "moi_gio": 6},
    "darwinex":   {"collector": _chay_darwinex, "moi_gio": 12},
    "dien_dan":   {"collector": _chay_dien_dan, "moi_gio": 12},
    "code":       {"collector": _chay_code, "moi_gio": 12},
    "evo_nguon":  {"collector": _chay_evo_nguon, "moi_gio": 6},
    "theo_doi":   {"collector": _chay_theo_doi, "moi_gio": 24},
}


def _tai_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _ghi_state(s):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")


def _log(msg):
    STATE.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    HB.write_text(time.strftime('%Y-%m-%d %H:%M:%S') + " alive\n", encoding="utf-8")
    print(msg)


def chay_mot(ten, state):
    it = LICH[ten]
    t0 = time.time()
    try:
        kw = {k: v for k, v in it.items() if k in ("so", "ngon")}
        kq = it["collector"](**kw)
        _log(f"[OK] {ten}: {kq} ({round(time.time()-t0,1)}s)")
        state[ten] = {"lan_cuoi": time.time(), "ok": True}
    except Exception as e:
        _log(f"[LOI] {ten}: {e} :: {traceback.format_exc(limit=1)}")
        state[ten] = {"lan_cuoi": time.time(), "ok": False, "loi": str(e)[:120]}
    _ghi_state(state)


def loop(chu_ky=60):
    state = _tai_state()
    _log("QUAN LI QUET bat dau (24/7)")
    while True:
        now = time.time()
        for ten, it in LICH.items():
            last = state.get(ten, {}).get("lan_cuoi", 0)
            if now - last >= it["moi_gio"] * 3600:
                chay_mot(ten, state)
        time.sleep(chu_ky)


if __name__ == "__main__":
    if "--chay" in sys.argv:
        ten = sys.argv[sys.argv.index("--chay") + 1]
        state = _tai_state()
        chay_mot(ten, state)
        sys.exit(0)
    loop()
