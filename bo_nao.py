# -*- coding: utf-8 -*-
"""bo_nao.py - Orchestrator THE BRAIN: bang cong viec + dieu phoi 8 vai.

Khuon theo KHUNG.md (quy trinh chuan). Mo hinh:
  - Moi viec la mot dong trong bang `cong_viec` (SQLite thu_vien.db).
  - Trang thai: CHO -> DANG -> XONG | LOI | BO.
  - Vai 'test' la PYTHON (chay MT5 tester qua mt5_worker.py); cac vai con lai goi LLM.
  - Vai XONG -> sinh task con dung luong trong KHUNG.md / prompts/cac_vai.md.

Chay:
  python bo_nao.py --xem          : xem hang doi + thong ke
  python bo_nao.py --nhip 1       : chay 1 nhip (rui 1 task CHO uu tien cao nhat)
  python bo_nao.py --them <url>   : cao 1 url -> tao task scout
  python bo_nao.py --kho          : che do khong goi API (chỉ xem/khong xu ly LLM)
"""
import argparse
import hashlib
import loc_chat_luong
import json
import os
import re
import sqlite3
import time
from pathlib import Path

import requests
import subprocess
from urllib.parse import quote

LAB = Path(__file__).parent
DB = LAB / "thu_vien.db"
PROMPT_GOC = LAB / "PROMPT_DEEPSEEK.md"
CAC_VAI = LAB / "prompts" / "cac_vai.md"
# Box API cong ty: dat env DEEPSEEK_API_BASE / DEEPSEEK_API_KEY / DEEPSEEK_API_MODE
# hoac tu dong doc tu ~/.codex/config.toml ([model_providers.*], wire_api = chat|responses).
API_BASE = ""
KEY = ""
API_MODE = "chat"


def _cau_hinh_deepseek():
    """Tra ve (api_base, key, mode). Env co uu tien, neu khong thi doc config.toml."""
    global API_BASE, KEY, API_MODE, MODEL
    base = os.environ.get("DEEPSEEK_API_BASE", "")
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    mode = os.environ.get("DEEPSEEK_API_MODE", "")
    mdl = os.environ.get("DEEPSEEK_MODEL", "")
    if base and key:
        API_BASE, KEY, API_MODE = base, key, (mode or "chat")
        if mdl:
            MODEL = mdl
        return
    # doc .codex/config.toml
    cfg = Path.home() / ".codex" / "config.toml"
    if not cfg.exists():
        return
    import re as _re
    t = cfg.read_text(encoding="utf-8")
    mm = _re.search(r"(?m)^model\s*=\s*\"([^\"]+)\"", t)
    if mm:
        MODEL = mm.group(1)
        if mdl:
            MODEL = mdl
    # tim [model_providers.<ten>] block (den dau [ tiep theo hoac het file)
    for m in _re.finditer(r"\[model_providers\.([^]]+)\](.*?)(?=\n\[|\Z)", t, _re.S):
        blob = m.group(2)
        bu = _re.search(r"base_url\s*=\s*\"([^\"]+)\"", blob)
        tok = _re.search(r"(?:experimental_bearer_token|api_key)\s*=\s*\"([^\"]+)\"", blob)
        wire = _re.search(r"wire_api\s*=\s*\"([^\"]+)\"", blob)
        if bu and tok:
            API_BASE = bu.group(1)
            KEY = tok.group(1)
            API_MODE = (wire.group(1) if wire else "chat")
            return
MODEL = "deepseek-chat"
NGUONG_DIEM = 8
UU_TIEN_TANG = {"scout": 0, "extractor": 10, "banker": 15, "reverser": 20,
                "surveyor": 30, "mapper": 40, "test": 50, "judge": 60,
                "optimizer": 70, "coder": 80, "improver": 90}
HUONG = ("seeker", "quantlab", "banker", "evolution")
VAI_LLM = {"scout", "extractor", "reverser", "surveyor", "mapper",
           "judge", "optimizer", "coder", "banker", "improver"}
NHAT_KY_TOKEN = LAB / "reports" / "nhat_ky_token.json"

import hang_doi
import mt5_worker as mt5
import toc_do

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TheBrainResearch/0.1"}


# ------------------------------------------------------------- DB + task
def mo_db():
    con = sqlite3.connect(DB)
    con.executescript("""
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
    CREATE TABLE IF NOT EXISTS noi_dung(
        muc_id TEXT PRIMARY KEY, url TEXT, van_ban TEXT, luc REAL);
    CREATE TABLE IF NOT EXISTS nguon_hi(
        id INTEGER PRIMARY KEY AUTOINCREMENT, nguon TEXT,
        phan_quyet TEXT, muc_id TEXT, co_che_id INTEGER, luc REAL);
    CREATE TABLE IF NOT EXISTS cong_viec(
        id TEXT PRIMARY KEY, vai TEXT, muc_id TEXT, co_che_id INTEGER,
        trang_thai TEXT DEFAULT 'CHO', uu_tien INTEGER DEFAULT 0,
        input_json TEXT, output_json TEXT, loi TEXT,
        nguoi_tao TEXT, tao_luc REAL, xong_luc REAL, so_lan_thu INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS de_xuat_cai_tien(
        id INTEGER PRIMARY KEY AUTOINCREMENT, van_de TEXT, nguyen_nhan TEXT,
        phuong_phap TEXT, nguon TEXT, muc_do INTEGER DEFAULT 2,
        trang_thai TEXT DEFAULT 'MOI', ket_qua TEXT, tao_luc REAL);
    CREATE TABLE IF NOT EXISTS macro_brief(
        id INTEGER PRIMARY KEY AUTOINCREMENT, luc REAL, regime TEXT,
        brief TEXT, chi_tiet TEXT);
    CREATE TABLE IF NOT EXISTS cong_dong(
        id INTEGER PRIMARY KEY AUTOINCREMENT, loai TEXT, ten TEXT, url TEXT,
        ngon_ngu TEXT, quoc_gia TEXT, truy_cap TEXT, ghi_chu TEXT,
        mau_khoa TEXT, luc REAL);
    """)
    con.commit()
    for ddl in ("ALTER TABLE cong_viec ADD COLUMN huong TEXT DEFAULT 'seeker'",
                "ALTER TABLE co_che ADD COLUMN huong TEXT DEFAULT 'seeker'"):
        try:
            con.execute(ddl)
        except Exception:
            pass
    con.commit()
    con.execute("INSERT OR IGNORE INTO moc VALUES(1,'EURCAD ema50-2atr dl4000',"
                "'',1.71,559,3194,'cau hinh thang kiem cheo 02/08')")
    con.commit()
    return con



def luu_noi_dung(con, muc_id, url, van_ban):
    try:
        con.execute("INSERT OR REPLACE INTO noi_dung(muc_id,url,van_ban,luc) VALUES(?,?,?,?)",
                    (muc_id, url, van_ban, time.time()))
    except Exception:
        pass
    # CHAT LUONG: tu phan loai (RA_TIEN / DU_BAO / NOISE) + cham diem khi luu
    try:
        con.execute("CREATE TABLE IF NOT EXISTS chat_luong(muc_id TEXT PRIMARY KEY,"
                    " loai TEXT, diem REAL, ly_do TEXT, luc REAL)")
        kq = loc_chat_luong.phan_loai(van_ban or "")
        con.execute("INSERT OR REPLACE INTO chat_luong(muc_id,loai,diem,ly_do,luc) VALUES(?,?,?,?,?)",
                    (muc_id, kq["loai"], kq["diem"], kq["ly_do"], time.time()))
    except Exception:
        pass
    try:
        con.commit()
    except Exception:
        pass


def lay_noi_dung(con, muc_id):
    try:
        r = con.execute("SELECT van_ban FROM noi_dung WHERE muc_id=?", (muc_id,)).fetchone()
        return r[0] if r else ""
    except Exception:
        return ""
def bam(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def _ghi_token(tk):
    ra = []
    if NHAT_KY_TOKEN.exists():
        try:
            ra = json.loads(NHAT_KY_TOKEN.read_text(encoding="utf-8"))
        except Exception:
            ra = []
    ra.append({**tk, "luc": time.strftime("%Y-%m-%d %H:%M:%S")})
    NHAT_KY_TOKEN.parent.mkdir(exist_ok=True)
    NHAT_KY_TOKEN.write_text(json.dumps(ra, ensure_ascii=False, indent=1),
                             encoding="utf-8")


def tao_task(con, vai, input_obj, muc_id=None, co_che_id=None, uu_tien=0, huong="seeker"):
    inp = json.dumps(input_obj, ensure_ascii=False)
    tid = bam(vai + inp)
    if con.execute("SELECT 1 FROM cong_viec WHERE id=?", (tid,)).fetchone():
        return None
    con.execute("""INSERT INTO cong_viec(id,vai,muc_id,co_che_id,trang_thai,
        uu_tien,input_json,nguoi_tao,tao_luc,huong)
        VALUES(?,?,?,?, 'CHO',?,?,?,?,?)""",
                (tid, vai, muc_id, co_che_id, uu_tien, inp, "bo_nao", time.time(), huong))
    con.commit()
    return tid


def nhan_task(con, vai=None):
    """Lay task CHO uu tien cao nhat (theo vai neu khong ro). Chuyen sang DANG."""
    if vai:
        r = con.execute("""SELECT id,input_json,muc_id,co_che_id,vai,huong FROM cong_viec
            WHERE trang_thai='CHO' AND vai=? ORDER BY uu_tien DESC, tao_luc LIMIT 1""",
                        (vai,)).fetchone()
    else:
        r = con.execute("""SELECT id,input_json,muc_id,co_che_id,vai,huong FROM cong_viec
            WHERE trang_thai='CHO' ORDER BY uu_tien DESC, tao_luc LIMIT 1""").fetchone()
    if not r:
        return None
    con.execute("UPDATE cong_viec SET trang_thai='DANG' WHERE id=? AND trang_thai='CHO'",
                (r[0],))
    con.commit()
    if con.execute("SELECT trang_thai FROM cong_viec WHERE id=?", (r[0],)).fetchone()[0] != "DANG":
        return None  # ai khac dang giu
    return {"id": r[0], "input": json.loads(r[1] or "{}"),
            "muc_id": r[2], "co_che_id": r[3], "vai": r[4],
            "huong": (r[5] if len(r) > 5 else "seeker")}


def tra_ket_qua(con, tid, output_obj):
    con.execute("UPDATE cong_viec SET trang_thai='XONG', output_json=?, xong_luc=? "
                "WHERE id=?", (json.dumps(output_obj, ensure_ascii=False), time.time(), tid))
    con.commit()


def bao_loi(con, tid, loi):
    con.execute("UPDATE cong_viec SET loi=?, so_lan_thu=so_lan_thu+1 WHERE id=?", (loi, tid))
    con.commit()
    r = con.execute("SELECT so_lan_thu FROM cong_viec WHERE id=?", (tid,)).fetchone()
    if r and r[0] >= 3:
        con.execute("UPDATE cong_viec SET trang_thai='BO', xong_luc=? WHERE id=?",
                    (time.time(), tid))
        con.commit()
    else:
        con.execute("UPDATE cong_viec SET trang_thai='CHO' WHERE id=?", (tid,))
        con.commit()


def _nguon_cua(con, muc_id):
    """Ten nguon goc (muc.nguon) cua mot co_che, "" neu khong ro."""
    if not muc_id:
        return ""
    r = con.execute("SELECT nguon FROM muc WHERE id=?", (muc_id,)).fetchone()
    return (r[0] if r else "") or ""


def _ghi_nguon_hi(con, muc_id, co_che_id, phan_quyet):
    """Ghi 1 su kien 'ket thuc' cua co che the nguon goc -> bang nguon_hi.
    Day la vong phan hoi de The Brain biet nguon nao that su ra co che THAT."""
    try:
        n = _nguon_cua(con, muc_id)
        if not n:
            return
        con.execute("INSERT INTO nguon_hi(nguon, phan_quyet, muc_id, co_che_id, luc) "
                    "VALUES(?,?,?,?,?)", (n, phan_quyet, muc_id, co_che_id, time.time()))
        con.commit()
    except Exception:
        pass


def nguon_xep_hang(con, tong_toi_thieu=1):
    """Ranking nang suat nguon: bao nhieu co_che ket thuc, THAT/AO/KHONG_ANH_XA.
    Sort theo so THAT (giam), roi AO it, roi KHONG_ANH_XA it."""
    ra = []
    for (nguon,) in con.execute("SELECT DISTINCT nguon FROM nguon_hi ORDER BY nguon"):
        if not nguon:
            continue
        dem = {"THAT": 0, "AO": 0, "KHONG_ANH_XA": 0}
        for (pq,) in con.execute("SELECT phan_quyet FROM nguon_hi WHERE nguon=?", (nguon,)):
            dem[pq] = dem.get(pq, 0) + 1
        tong = sum(dem.values())
        if tong < tong_toi_thieu:
            continue
        ra.append({"nguon": nguon, "tong": tong,
                   "THAT": dem["THAT"], "AO": dem["AO"],
                   "KHONG_ANH_XA": dem["KHONG_ANH_XA"]})
    ra.sort(key=lambda d: (d["THAT"], -d["AO"], -d["KHONG_ANH_XA"]), reverse=True)
    return ra


# ------------------------------------------------------------- LLMdef _system_prompt(vai):
    """Prompt goc (playbook+bay) + khoi vai rieng trong prompts/cac_vai.md."""
    nen = PROMPT_GOC.read_text(encoding="utf-8") if PROMPT_GOC.exists() else ""
    if not CAC_VAI.exists():
        return nen
    t = CAC_VAI.read_text(encoding="utf-8")
    m = re.search(r"## VAI[^\n]*?" + vai.upper() + r"[^\n]*\n(.*?)(?=\n════|## VAI|\Z)", t, re.S)
    return (nen + "\n\n## VAI CUA BAN\n" + (m.group(1).strip() if m else "")) if nen else ""


def json_tu(y):
    y = re.sub(r"^```(?:json)?|```$", "", y.strip(), flags=re.M).strip()
    try:
        return json.loads(y)
    except Exception:
        m = re.search(r"[\[{].*[\]}]", y, re.S)
        return json.loads(m.group(0)) if m else None


def goi_llm(vai, noi_dung):
    _cau_hinh_deepseek()
    if not KEY:
        raise RuntimeError("Chua co DEEPSEEK_API_KEY (hoac .codex/config.toml)")
    base = API_BASE.rstrip("/")
    he_thong = _system_prompt(vai)
    if API_MODE == "responses":
        url = base + "/responses"
        body = {"model": MODEL, "stream": False,
                "input": [{"role": "system", "content": he_thong},
                          {"role": "user", "content": noi_dung}]}
    else:
        url = base if base.endswith("chat/completions") else base + "/chat/completions"
        body = {"model": MODEL, "temperature": 0.2, "messages": [
            {"role": "system", "content": he_thong},
            {"role": "user", "content": noi_dung}]}
    r = requests.post(url, timeout=300, headers={
        "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        json=body)
    r.raise_for_status()
    j = r.json()
    u = j.get("usage", {})
    _ghi_token({"vai": vai, "vao": u.get("prompt_tokens", 0),
                "ra": u.get("completion_tokens", 0), "mode": API_MODE})
    if API_MODE == "responses":
        # tra ve output_text neu co, khong thi gop output[].content[].text
        ot = j.get("output_text")
        if ot:
            return ot
        out = j.get("output", [])
        thu = []
        for o in out:
            if isinstance(o, dict) and isinstance(o.get("content"), list):
                for c in o["content"]:
                    if isinstance(c, dict) and c.get("text"):
                        thu.append(c["text"])
        return "\n".join(thu)
    return j["choices"][0]["message"]["content"]


# ------------------------------------------------------------- chay mot vai
def _chay_test(input_obj):
    """Vai 'test': chay MT5 tester cho tung cau hinh -> mang ket qua."""
    cau_hinh = (input_obj.get("cau_hinh") or [])
    if isinstance(cau_hinh, dict):
        cau_hinh = [cau_hinh]
    ra = []
    for i, ch in enumerate(cau_hinh):
        nhan = f"bn_{int(time.time())}_{i}"
        mt5.viet_set(nhan, ch.get("input") or {})
        kq = mt5.chay_tester(nhan) or {}
        kq["ten"] = ch.get("ten", nhan)
        kq["nam"] = 13.42
        ra.append(kq)
    return ra


def chay_vai(vai, input_obj, con=None, muc_id=None):
    """Dieu phoi mot vai: tra ve JSON ket qua (da parse).
    Voi vai LLM: neu co url ma van_ban qua ngan, tu lay van ban day du tu trang
    (Python lam viec lay van ban, LLM khong phai do) va luu vao cache noi_dung."""
    if vai == "test":
        return _chay_test(input_obj)
    inp = dict(input_obj)
    url = inp.get("url") or ""
    vb = inp.get("van_ban") or ""
    if url and len(vb) < 800:
        full = cao_url(url, con=con, muc_id=muc_id)
        if full:
            vb = full
    inp["van_ban"] = vb
    return json_tu(goi_llm(vai, json.dumps(inp, ensure_ascii=False)))


# ------------------------------------------------------------- lop VPS / may nha
def _xep_vps(con, task, ct, cau_hinh):
    """VPS: ghi cau hinh vao hang_doi_test.jsonl (may nha se chay tester)."""
    for i, ch in enumerate(cau_hinh):
        job_id = bam(f"{task.get('id','bn')}_{ct}_{i}")
        hang_doi.vps_xep(job_id, ch.get("symbol", mt5.CAP_CHINH),
                         ch.get("input") or {}, mt5.TU, mt5.DEN,
                         ghi_chu=json.dumps({"co_che_id": ct, "ten": ch.get("ten", job_id)},
                                            ensure_ascii=False))
        con.execute("UPDATE co_che SET da_kiem=1 WHERE id=?", (ct,))
        con.commit()


def xu_ly_maynha(con, so_job=4):
    """MAY NHA: doc hang doi, chay tester THAT, ghi ket qua, tao task judge."""
    jobs = hang_doi.maynha_job_cho()
    chay = 0
    for j in jobs[:so_job]:
        if not hang_doi.maynha_giu(j["id"]):
            continue
        try:
            kq = _chay_test({"cau_hinh": [{"ten": j["id"], "input": j.get("input", {})}]})
        except Exception as e:
            hang_doi.maynha_xong(j["id"], {"loi": str(e)[:200]})
            continue
        ghi = {}
        try:
            ghi = json.loads(j.get("ghi_chu") or "{}")
        except Exception:
            pass
        hang_doi.maynha_xong(j["id"], (kq[0] if kq else {"loi": "no result"}))
        moc = con.execute("SELECT pf,dd FROM moc WHERE id=1").fetchone()
        tao_task(con, "judge", {"co_che_id": ghi.get("co_che_id"),
                                "ten": ghi.get("ten", j["id"]),
                                "ket_qua": kq, "moc": {"pf": moc[0], "dd": moc[1]}},
                 co_che_id=ghi.get("co_che_id"), uu_tien=UU_TIEN_TANG["judge"])
        con.commit()
        chay += 1
    print(f"  maynha: doc {len(jobs)} job, chay {chay} test")
    return chay


# ------------------------------------------------------------- sinh task con
def _them_co_che(con, task, cc):
    ten = cc.get("ten", "co_che")
    con.execute("""INSERT INTO co_che(muc_id,ten,loai,vao_lenh,quan_ly,thoat,moi,
        diem,json,huong) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (task["muc_id"], ten, cc.get("loai", ""), cc.get("vao_lenh", ""),
                 cc.get("quan_ly", ""), cc.get("thoat", ""),
                 cc.get("moi_so_voi_thu_vien", ""), int(cc.get("diem", 0)),
                 json.dumps(cc, ensure_ascii=False), task.get("huong", "seeker")))
    con.commit()
    return con.execute("SELECT last_insert_rowid()").fetchone()[0]


def sinh_task_con(con, task, out, che_do="noi"):
    vai, mid, cid = task["vai"], task["muc_id"], task["co_che_id"]
    if vai == "scout" and isinstance(out, dict) and out.get("lien_quan"):
        inp = task["input"]
        vb = lay_noi_dung(con, mid) or inp.get("van_ban", "")
        tao_task(con, "extractor",
                 {"muc_id": mid, "url": inp.get("url", ""), "ten": inp.get("ten", ""),
                  "van_ban": vb},
                 muc_id=mid, uu_tien=UU_TIEN_TANG["extractor"],
                 huong=task.get("huong", "seeker"))
    elif vai == "extractor" and isinstance(out, list):
        for cc in out:
            cid2 = _them_co_che(con, task, cc)
            if int(cc.get("diem", 0)) >= NGUONG_DIEM:
                tao_task(con, "surveyor", {"co_che_id": cid2, "co_che": cc},
                         muc_id=mid, co_che_id=cid2, uu_tien=UU_TIEN_TANG["surveyor"],
                         huong=task.get("huong", "seeker"))
    elif vai == "reverser" and isinstance(out, list):
        for i, luat in enumerate(out):
            tao_task(con, "surveyor", {"luat": luat, "muc_id": mid},
                     muc_id=mid, uu_tien=UU_TIEN_TANG["surveyor"],
                     huong=task.get("huong", "seeker"))
    elif vai == "surveyor" and isinstance(out, dict):
        ct = (cid or (task["co_che_id"]) or 0)
        tao_task(con, "mapper", {"co_che_id": ct, "survey": out, "muc_id": mid},
                 muc_id=mid, co_che_id=ct, uu_tien=UU_TIEN_TANG["mapper"])
    elif vai == "mapper" and isinstance(out, dict):
        ct = cid or 0
        if out.get("anh_xa_duoc"):
            ch = out.get("cau_hinh", [])
            if che_do == "vps":
                _xep_vps(con, task, ct, ch)
            else:
                tao_task(con, "test", {"co_che_id": ct, "cau_hinh": ch},
                         muc_id=mid, co_che_id=ct, uu_tien=UU_TIEN_TANG["test"])
        else:
            tao_task(con, "coder", {"co_che_id": ct, "can_input_moi": out.get("can_input_moi", [])},
                     muc_id=mid, co_che_id=ct, uu_tien=UU_TIEN_TANG["coder"])
    elif vai == "test" and isinstance(out, list):
        moc = con.execute("SELECT pf,dd FROM moc WHERE id=1").fetchone()
        # loc tu dong (chong overfit) truoc khi dua cho judge
        auto = loc_tu_dong(out)
        tao_task(con, "judge", {"co_che_id": cid or 0, "ket_qua": out,
                                "moc": {"pf": moc[0], "dd": moc[1]},
                                "loc_tu_dong": auto},
                 muc_id=mid, co_che_id=cid, uu_tien=UU_TIEN_TANG["judge"])
    elif vai == "judge" and isinstance(out, dict):
        pq = out.get("phan_quyet")
        if pq == "THAT":
            con.execute("UPDATE co_che SET da_kiem=1, phan_quyet='THAT' WHERE id=?", (cid,))
            con.commit()
            _ghi_nguon_hi(con, mid, cid, "THAT")
        elif pq == "CHUA_RO":
            tao_task(con, "optimizer",
                     {"co_che_id": cid or 0, "ket_qua": out.get("ket_qua"),
                      "buoc_tiep": out.get("buoc_tiep", [])},
                     muc_id=mid, co_che_id=cid, uu_tien=UU_TIEN_TANG["optimizer"])
        elif pq == "AO":
            con.execute("UPDATE co_che SET da_kiem=1, phan_quyet='AO' WHERE id=?", (cid,))
            con.commit()
            _ghi_nguon_hi(con, mid, cid, "AO")
    elif vai == "optimizer" and isinstance(out, dict):
        tao_task(con, "test", {"co_che_id": cid or 0, "cau_hinh": out.get("buoc_tiep", [])},
                 muc_id=mid, co_che_id=cid, uu_tien=UU_TIEN_TANG["test"])
    elif vai == "banker" and isinstance(out, dict):
        try:
            con.execute("INSERT INTO macro_brief(luc, regime, brief, chi_tiet) "
                        "VALUES(?,?,?,?)",
                        (time.time(), out.get("regime", ""),
                         json.dumps(out, ensure_ascii=False),
                         json.dumps(out.get("chi_tiet", {}), ensure_ascii=False)))
            con.commit()
        except Exception:
            pass
    elif vai == "improver" and isinstance(out, dict):
        try:
            con.execute("""INSERT INTO de_xuat_cai_tien(van_de, nguyen_nhan,
                phuong_phap, nguon, muc_do, trang_thai, tao_luc)
                VALUES(?,?,?,?,?, 'MOI', ?)""",
                        (out.get("van_de", ""), out.get("nguyen_nhan", ""),
                         out.get("phuong_phap", ""),
                         json.dumps(out.get("nguon", []), ensure_ascii=False),
                         int(out.get("muc_do", 2)), time.time()))
            con.commit()
        except Exception:
            pass
    elif vai == "coder":
        # stub: ban giao mo ta EA moi (chua tu bien dich). Ghi loi vao co_che.
        con.execute("UPDATE co_che SET da_kiem=1, phan_quyet='KHONG_ANH_XA' WHERE id=?",
                    (cid,))
        con.commit()
        _ghi_nguon_hi(con, mid, cid, "KHONG_ANH_XA")


# ------------------------------------------------------------- NEN TANG (bậc 2 trong NGUON.md)
NEN_TANG = {
    "sa_dau":  ["wccta", "robbins", "usic", "tradingcup", "tthc", "hungarian_tc"],
    "prop":    ["ftmo", "topstep", "apex", "fundednext", "the5ers", "e8", "funderpro"],
    "copy_signal": ["collective2", "darwinex", "etoro", "zulutrade", "myfxbook",
                    "fxblue", "mql5_signals"],
    "chi_so_quy": ["sg_cta", "barclay", "nilsson", "eurekahedge"],
    "thi_dau_quant": ["quantconnect", "kaggle", "numerai", "worldquant_websim"],
}
# Trang thai kich hoat: co=da co script, cho=chua co (can parser/api/login)
NEN_TANG_TRANG_THAI = {x: "cho" for cat in NEN_TANG.values() for x in cat}
NEN_TANG_TRANG_THAI.update({"collective2": "cho", "mql5_signals": "cho"})


def loc_tu_dong(bang, nguong_pf=1.15, n_cap=2):
    """Loc tu dong chong overfit (Python, khong can LLM).
    bang: list dict {cau_hinh, symbol, nua(full|dau|sau), pf,...}.
    THAT: PF_final >= nguong_pf VA duong tren >= n_cap symbol VA duong ca 2 nua.
    AO:   PF_final < 1.10 (bien mong / don bay). Con lai: CHUA.
    Tra ve: {cau_hinh: 'THAT'|'AO'|'CHUA'|'THIEU_DU_LIEU'}.
    """
    from collections import defaultdict
    g = defaultdict(list)
    for r in bang:
        g[r.get("cau_hinh", r.get("ten", "?") )].append(r)
    quyet = {}
    for ten, rows in g.items():
        pf_full = [x["pf"] for x in rows if x.get("nua") in (None, "", "full")]
        if pf_full:
            pf = pf_full[0]
        else:
            pf = max(x.get("pf", 0) for x in rows)
        symbols = {x.get("symbol") for x in rows if x.get("symbol")}
        n_2nua = 0
        for sym in symbols:
            dau = [x for x in rows if x.get("symbol") == sym and x.get("nua") == "dau"]
            sau = [x for x in rows if x.get("symbol") == sym and x.get("nua") == "sau"]
            if dau and sau and dau[0].get("pf", 0) > 1 and sau[0].get("pf", 0) > 1:
                n_2nua += 1
        if len(symbols) < n_cap + 1 and not pf_full:
            quyet[ten] = "THIEU_DU_LIEU"
        elif pf >= nguong_pf and len(symbols) >= n_cap and n_2nua >= n_cap:
            quyet[ten] = "THAT"
        elif pf < 1.10:
            quyet[ten] = "AO"
        else:
            quyet[ten] = "CHUA"
    return quyet


# ------------------------------------------------------------- Evolution: tim giai phap
def tim_giai_phap(van_de, so=6):
    """Tim repo/package thuc su cho 1 nan de cu the (khong bia). Vi du: can giai phap
    cao trang JS react -> tra ve playwright/puppeteer kem so sao va ghi chu."""
    ra = []
    r = toc_do.lay("https://api.github.com/search/repositories",
                   nguon="github_search",
                   params={"q": f"{van_de} trading python", "sort": "stars",
                           "per_page": so}, headers=UA, timeout=30)
    if r is None:
        print("  tim giai phap: bi chan/loi")
        return ra
    for it in r.json().get("items", []):
        ra.append({"ten": it["full_name"], "url": it["html_url"],
                   "sao": it.get("stargazers_count", 0),
                   "mo_ta": (it.get("description") or "")[:160]})
    return ra


# ------------------------------------------------------------- CAO NGUON -> scout
def cao_mql5(so=12):
    """Lay danh sach code MQL5 cong khai (nhieu danh muc + phan trang)."""
    ra = []
    pages = 1 if so <= 12 else 12
    for dm in ("experts", "indicators", "scripts", "libraries"):
        for trang in range(1, pages + 1):
            r = toc_do.lay(f"https://www.mql5.com/en/code/mt5/{dm}/page{trang}",
                           nguon="mql5", headers=UA, timeout=30)
            if r is None:
                print(f"    mql5 {dm}: bi chan/loi")
                continue
            h = r.text
            for m in re.finditer(r'href="(/en/code/\d+)"[^>]*>([^<]{5,120})<', h):
                ra.append({"nguon": "mql5", "url": "https://www.mql5.com" + m.group(1),
                           "ten": m.group(2).strip()})
            if len(ra) >= so * 2:
                break
        if len(ra) >= so * 2:
            break
    return _loc_loc(ra)[:so]


def cao_github(so=12):
    """Tim repo GitHub co sao cao cho nhieu huong chien luoc + phan trang."""
    ra = []
    qs = (
        "metatrader5 expert advisor", "mql5 grid martingale ea",
        "pine script mean reversion strategy", "forex dca ea",
        "tradingview strategy pine indicator", "quant trading strategy python",
        "vectorbt backtest strategy", "freqtrade strategy",
        "mean reversion market making", "trend following breakout strategy",
        "order flow tape reading bot", "seasonality trading strategy",
        "macro trading signal", "momentum factor strategy",
        "adaptive indicator ema", "bollinger bands strategy",
        "smart money concept ict forex", "liquidity sweep mt5", "fair value gap trading",
        "supertrend strategy", "parabolic sar scalping", "heiken ashi strategy",
        "donchian channel breakout", "keltner channel strategy", "vwap strategy",
        "support resistance zone trading", "pivot point strategy mt5",
        "fibonacci retracement strategy", "elliot wave indicator",
        "hurricane oscillator", "ztl support resistance", "ru sure win indicator",
        "noro ea", "dragon mql5", "golden memphis ea", "proxima ea",
        "forex factory news trading bot", "correlation trading multiple pairs",
        "hedging bot mt5", "arbitrage crypto bot", "grid trading bot",
        "dca bot crypto", "backtrader strategy", "zipline algorithmic trading",
        "profit factor strategy", "machine learning forex prediction",
        "reinforcement learning trading agent", "portfolio optimization backtest",
        "position sizing risk management", "pairs trading statistical arbitrage",
        "sentiment analysis trading bot", "crypto trading bot open source",
        "factor investing quant library", "options greeks strategy",
        "volume profile trading", "order block liquidity strategy",
        "tick data replay backtest", "walk forward optimization strategy",
        "drawdown control ea", "half trend indicator", "zigzag fibonacci trading",
    )
    qs_recent = tuple(q + " created:>2024-01-01" for q in qs[:12])
    for q in qs_recent + qs:
        for trang in (1, 2):
            r = toc_do.lay("https://api.github.com/search/repositories",
                           nguon="github_search",
                           params={"q": q, "sort": "updated",
                                   "per_page": 10, "page": trang},
                           headers=UA, timeout=30)
            if r is None:
                print("    github: bi chan/loi - bo qua")
                continue
            j = r.json()
            for it in j.get("items", []):
                ra.append({"nguon": "github", "url": it["html_url"],
                           "ten": f"{it['full_name']} ({it.get('stargazers_count',0)}*)"})
            if len(ra) >= so * 2:
                break
        if len(ra) >= so * 2:
            break
    return _loc_loc(ra)[:so]


def _loc_loc(ds):
    """Loai bo trung url, giu thu tu."""
    seen, out = set(), []
    for it in ds:
        u = it["url"]
        if u in seen:
            continue
        seen.add(u)
        out.append(it)
    return out


def cao_dan(con, so=24):
    """Cao nhieu nguon cong khai -> tao task scout cho cac muc MOI (queue luon day)."""
    nguon = cao_mql5(so // 2) + cao_github(so // 2)
    them = 0
    for it in nguon:
        mid = bam(it["url"])
        if con.execute("SELECT 1 FROM muc WHERE id=?", (mid,)).fetchone():
            continue
        con.execute("INSERT OR IGNORE INTO muc VALUES(?,?,?,?,?,0)",
                    (mid, it["nguon"], it["ten"], it["url"], time.time()))
        tao_task(con, "scout", {"ten": it["ten"], "url": it["url"], "van_ban": ""},
                 muc_id=mid, uu_tien=UU_TIEN_TANG["scout"])
        them += 1
    print(f"  cao dan: {len(nguon)} nguon, them {them} scout task moi")
    return them


# ------------------------------------------------------------- nhip
def chay_mot_nhip(con, che_do="noi"):
    t = nhan_task(con)
    if not t:
        return None
    print(f"  [chay] {t['id'][:10]} vai={t['vai']}")
    try:
        out = chay_vai(t["vai"], t["input"], con, t["muc_id"])
        tra_ket_qua(con, t["id"], out)
        sinh_task_con(con, t, out, che_do)
        print(f"  [xong] {t['vai']}: {json.dumps(out, ensure_ascii=False)[:120]}")
    except Exception as e:
        bao_loi(con, t["id"], str(e)[:200])
        print(f"  [loi] {t['vai']}: {str(e)[:120]}")
    return t


def thong_ke(con):
    dem = {}
    for (tt,) in con.execute("SELECT trang_thai FROM cong_viec"):
        dem[tt] = dem.get(tt, 0) + 1
    cc = con.execute("SELECT COUNT(*) FROM co_che").fetchone()[0]
    print(f"  cong_viec: {dict(sorted(dem.items()))} | co_che: {cc}")
    return dem



def _pid_song(pid):
    try:
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                           capture_output=True, text=True, timeout=20)
        return str(pid) in r.stdout
    except Exception:
        return False


def _giu_khoa():
    """Khoa don phien: chi mot tien trinh bo_nao chay. True = da giu duoc.
    Dung file O_EXCL (atomic) chua PID; neu lock cu chet thi xoa va cuop."""
    kf = LAB / "bo_nao.lock"
    if kf.exists():
        try:
            pid = int(kf.read_text(encoding="utf-8").strip())
            if _pid_song(pid):
                return False
            kf.unlink()
        except Exception:
            return False
    try:
        fd = os.open(str(kf), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False


def ghi_trang_thai(con, hanh_dong="", loi=""):
    """Ghi trang thai truc tiep ra reports/trang_thai.json (de user xem ma khong can log)."""
    dem = {}
    for (tt,) in con.execute("SELECT trang_thai FROM cong_viec"):
        dem[tt] = dem.get(tt, 0) + 1
    cc = con.execute("SELECT COUNT(*) FROM co_che").fetchone()[0]
    nd = con.execute("SELECT COUNT(*) FROM noi_dung").fetchone()[0]
    st = {"luc": time.strftime("%Y-%m-%d %H:%M:%S"), "cong_viec": dem,
          "co_che": cc, "noi_dung_cache": nd,
          "hanh_dong_cuoi": hanh_dong, "loi_cuoi": loi}
    (LAB / "reports").mkdir(exist_ok=True)
    (LAB / "reports" / "trang_thai.json").write_text(
        json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    return st


def xem(con):
    print("=== CONG VIEC (xep theo uu tien) ===")
    for r in con.execute("""SELECT id,vai,trang_thai,uu_tien,muc_id,co_che_id,so_lan_thu
        FROM cong_viec ORDER BY uu_tien DESC, tao_luc LIMIT 30"""):
        print(f"  {r[0][:10]} | {r[1]:9} | {r[2]:5} | ut={r[3]:3} | muc={str(r[4])[:8]} | co={r[5]}")
    thong_ke(con)


def _html_than_chu(h, gioi_han=20000):
    h = re.sub(r"<(script|style).*?</\1>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    import html as _html
    h = _html.unescape(h)
    return re.sub(r"\s+", " ", h).strip()[:gioi_han]


def _cao_github(owner, repo):
    """GitHub: lay README + danh sach file + noi dung file ma nguon chinh."""
    phan = []
    # README (doc ve y tuong/chien luoc)
    try:
        r = requests.get(f"https://api.github.com/repos/{owner}/{repo}/readme",
                         headers={"Accept": "application/vnd.github.raw", **UA},
                         timeout=30)
        if r.ok:
            phan.append("README:\n" + r.text[:6000])
    except Exception as e:
        print(f"  github readme {owner}/{repo}: {e}")
    # danh sach file .mq5/.py/.set nho nhat de xac dinh file ma nguon
    try:
        r = requests.get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1",
                         headers=UA, timeout=30)
        if not r.ok:
            r = requests.get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1",
                             headers=UA, timeout=30)
        if r.ok:
            files = [x["path"] for x in r.json().get("tree", [])
                     if x.get("type") == "blob" and re.search(r"\.(mq5|mq4|py)$", x["path"].lower())]
            files = sorted(files, key=lambda p: (p.count("/"), len(p)))[:6]
            for f in files:
                try:
                    rr = requests.get(f"https://raw.githubusercontent.com/{owner}/{repo}/master/{f}",
                                      headers=UA, timeout=30)
                    if not rr.ok:
                        rr = requests.get(f"https://raw.githubusercontent.com/{owner}/{repo}/main/{f}",
                                          headers=UA, timeout=30)
                    if rr.ok:
                        phan.append(f"FILE {f}:\n" + rr.text[:4000])
                except Exception:
                    pass
    except Exception as e:
        print(f"  github tree {owner}/{repo}: {e}")
    return "\n\n".join(phan)[:20000]


def cao_url(url, con=None, muc_id=None, gioi_han=20000):
    """Cao noi dung trang ve van ban. GitHub dung API (README+file ma nguon).
    Co cache trong bang noi_dung (theo muc_id) de khong cao lai lap lai."""
    if con is not None and muc_id:
        vb = lay_noi_dung(con, muc_id)
        if vb:
            return vb
    vb = ""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/?", url)
    if m:
        vb = _cao_github(m.group(1), m.group(2))
    else:
        r = toc_do.lay(url, nguon="web",
                       headers={"User-Agent": "Mozilla/5.0 (quant lab)"}, timeout=40)
        if r is None:
            print(f"  loi cao {url}: bi chan/loi")
            return ""
        vb = _html_than_chu(r.text, gioi_han)
    if con is not None and muc_id and vb:
        luu_noi_dung(con, muc_id, url, vb)
    return vb


def main():
    ap = argparse.ArgumentParser(description="THE BRAIN orchestrator (khung 8 vai)")
    ap.add_argument("--xem", action="store_true")
    ap.add_argument("--nhip", type=int, default=1)
    ap.add_argument("--them", metavar="URL", help="cao 1 url -> tao task scout")
    ap.add_argument("--kho", action="store_true", help="khong goi API")
    ap.add_argument("--vps", action="store_true", help="che do VPS (cao+rut+xep hang doi)")
    ap.add_argument("--maynha", action="store_true", help="che do MAY NHA (test+judge)")
    ap.add_argument("--dan", action="store_true", help="cao nhieu nguon -> tao scout tasks")
    ap.add_argument("--so", type=int, default=24, help="so muc cao cho --dan")
    ap.add_argument("--lien-tuc", action="store_true", help="chay daemon 24/7")
    ap.add_argument("--nghi", type=int, default=60, help="giay nghi giua cac nhip khi --lien-tuc")
    ap.add_argument("--nguon", action="store_true", help="liet ke registry nen tang (bậc 2)")
    ap.add_argument("--trang-thai", action="store_true", help="in trang thai hien tai roi thoat")
    a = ap.parse_args()
    con = mo_db()
    if a.nguon:
        print("=== NEN TANG (bậc 2 - NGUON.md) ===")
        for cat, ds in NEN_TANG.items():
            print(f"  {cat}:")
            for d in ds:
                print(f"      {d:16} [{NEN_TANG_TRANG_THAI.get(d, 'cho')}]")
        print("\n=== NANG SUAT NGUON (co_che da ket thuc) ===")
        xh = nguon_xep_hang(con)
        if not xh:
            print("  chua co du lieu - chua co_che nao duoc phan quyet THAT/AO/KHONG_ANH_XA")
        for d in xh:
            print(f"  {d['nguon']:22} tong={d['tong']:<3} THAT={d['THAT']} "
                  f"AO={d['AO']} KHONG_ANH_XA={d['KHONG_ANH_XA']}")
        return
    if a.maynha:
        while True:
            lam = xu_ly_maynha(con)
            if not lam:
                print("  hang doi test rong — nghi")
                if not a.lien_tuc:
                    break
            time.sleep(a.nghi)
            if not a.lien_tuc:
                break
        return
    if a.dan:
        cao_dan(con, a.so)
        return
    if a.them:
        ten = a.them.split("/")[-1][:60] or a.them
        mid = bam(a.them)
        con.execute("INSERT OR IGNORE INTO muc VALUES(?,?,?,?,?,0)",
                    (mid, "web", ten, a.them, time.time()))
        tid = tao_task(con, "scout", {"ten": ten, "url": a.them, "van_ban": ""},
                       muc_id=mid, uu_tien=UU_TIEN_TANG["scout"])
        print(f"  da them scout task {tid[:10] if tid else '(trung)'} (scout tu lay van ban khi chay)")
        return
    if a.xem:
        xem(con)
        return
    if a.trang_thai:
        ghi_trang_thai(con, "xem trang thai")
        print(json.dumps(ghi_trang_thai(con), ensure_ascii=False, indent=1))
        return
    if not _giu_khoa():
        print("  Da co tien trinh bo_nao khac dang chay — thoat (khoa don phien).")
        return
    print(f"=== BO NAO - nhip = {a.nhip} | kho = {a.kho} | key = {'co' if KEY else 'KHONG'} ===")
    n = 0
    while True:
        n += 1
        if a.kho:
            # che do kho: chi liet ke task LLM dang cho, khong goi API
            dem = thong_ke(con)
            so = con.execute("SELECT COUNT(*) FROM cong_viec WHERE trang_thai='CHO' "
                             "AND vai!='test'").fetchone()[0]
            print(f"  --kho: {so} task LLM dang cho (can DEEPSEEK_API_KEY de chay)")
            break
        che_do = "vps" if a.vps else "noi"
        lam = chay_mot_nhip(con, che_do)
        ghi_trang_thai(con, f"nhip {n} | {lam['vai'] if lam else 'rong'}")
        if not lam:
            # o che do vps, judge + cap nhat moc chay tren may NHA (doc ket_qua_test.jsonl)
            print("  hang doi rong — (vps: doi may nha doc hang doi; "
                  "maynha: doi --maynha de test+judge)")
            if not a.lien_tuc:
                break
        if not a.lien_tuc and n >= a.nhip:
            break
        time.sleep(a.nghi)


if __name__ == "__main__":
    main()

