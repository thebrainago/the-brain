# -*- coding: utf-8 -*-
"""so.py - SO CAI CUA THE BRAIN. Mot nguon su that duy nhat cho ca 4 tru.

Thay cho: bo_nao.py/thu_vien.db, brain_24h queue, vong_lap_state.json,
quant_offline_state.json, ket_hop_state.json, lich_quet_state.json...

Nguyen tac (THIET_KE_DAY_CHUYEN muc 8):
  - So CHI-THEM. Khong ghi de. Chay lai cung params_hash voi du lieu moi ->
    them dong moi, dong cu tro `superseded_by`.
  - Chuoi hash tren bang su_kien: sua lang le mot dong se lam dut chuoi.
  - Tien trinh chet giua chung -> viec o trang thai CHAY; khoi dong lai
    chuyen thanh LOI, KHONG BAO GIO thanh XONG.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
DB = LAB / "nao.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS su_kien(
  id INTEGER PRIMARY KEY AUTOINCREMENT, luc TEXT, tru TEXT, loai TEXT,
  noi_dung TEXT, hash_truoc TEXT, hash TEXT);

CREATE TABLE IF NOT EXISTS nguon(
  ma TEXT PRIMARY KEY, ten TEXT, loai TEXT, url TEXT, lay_gi TEXT,
  chu_ky_giay INTEGER DEFAULT 21600, uu_tien INTEGER DEFAULT 3,
  lan_cuoi REAL DEFAULT 0, so_lan INTEGER DEFAULT 0, so_loi INTEGER DEFAULT 0,
  loi_lien_tuc INTEGER DEFAULT 0, thu_hoach INTEGER DEFAULT 0,
  trang_thai TEXT DEFAULT 'BAT', ghi_chu TEXT);

CREATE TABLE IF NOT EXISTS tai_lieu(
  id INTEGER PRIMARY KEY AUTOINCREMENT, van_tay TEXT UNIQUE, nguon TEXT,
  loai TEXT, tieu_de TEXT, url TEXT, tom_tat TEXT, tu_khoa TEXT,
  diem REAL DEFAULT 0, luc TEXT, da_khai_thac INTEGER DEFAULT 0);

CREATE TABLE IF NOT EXISTS tu_khoa(
  tu TEXT PRIMARY KEY, linh_vuc TEXT DEFAULT 'tai_chinh', diem REAL DEFAULT 1.0,
  so_lan_dung INTEGER DEFAULT 0, so_ket_qua INTEGER DEFAULT 0,
  sinh_tu TEXT, luc TEXT);

CREATE TABLE IF NOT EXISTS gia_thuyet(
  id INTEGER PRIMARY KEY AUTOINCREMENT, ma TEXT UNIQUE, co_che TEXT,
  template TEXT, tham_so TEXT, tai_san TEXT, khung TEXT, cua_so TEXT,
  plan_hash TEXT, dang_ky_luc TEXT, nguon TEXT, tru_sinh TEXT, ho TEXT,
  trang_thai TEXT DEFAULT 'DANG_KY', ghi_chu TEXT,
  -- Hai cot nay KHONG nam trong plan_hash (xem `dang_ky_gia_thuyet`).
  -- Day la cho duy nhat chung duoc luu, de mot PASS sau nay tra loi duoc
  -- cau: bo tham so nay duoc chon ra tu bao nhieu bo?
  so_phep_thu INTEGER, the_he_cong INTEGER);

CREATE TABLE IF NOT EXISTS ket_qua(
  id INTEGER PRIMARY KEY AUTOINCREMENT, gt_id INTEGER, gt_ma TEXT, luc TEXT,
  chi_so TEXT, cong TEXT, verdict TEXT, p_placebo REAL, alpha REAL,
  t_alpha REAL, superseded_by INTEGER);

CREATE TABLE IF NOT EXISTS khang_dinh(
  id INTEGER PRIMARY KEY AUTOINCREMENT, gt_ma TEXT, hang TEXT, luc TEXT,
  het_han TEXT, dieu_kien_sai TEXT, trang_thai TEXT DEFAULT 'HIEU_LUC');

CREATE TABLE IF NOT EXISTS viec(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tru TEXT, loai TEXT, tham_so TEXT,
  uu_tien INTEGER DEFAULT 5, trang_thai TEXT DEFAULT 'CHO', van_tay TEXT,
  tao_luc TEXT, bat_luc TEXT, xong_luc TEXT, ket_qua TEXT, so_lan INTEGER DEFAULT 0);

CREATE TABLE IF NOT EXISTS van_de(
  id INTEGER PRIMARY KEY AUTOINCREMENT, ma TEXT, muc TEXT, mo_ta TEXT,
  bang_chung TEXT, phat_hien_luc TEXT, trang_thai TEXT DEFAULT 'MO',
  hanh_dong TEXT, sua_luc TEXT);

CREATE TABLE IF NOT EXISTS vi_mo(
  seri TEXT, ngay TEXT, gia_tri REAL, PRIMARY KEY(seri, ngay));

CREATE TABLE IF NOT EXISTS vi_mo_seri(
  ma TEXT PRIMARY KEY, ten TEXT, nguon TEXT, chu_ky_giay INTEGER DEFAULT 86400,
  lan_cuoi REAL DEFAULT 0, so_diem INTEGER DEFAULT 0, ghi_chu TEXT);

-- `gt_ma` o day la DANH TINH CUA PHEP THU trong epoch (economic plan hash),
-- KHONG phai ma gia thuyet trong bang `gia_thuyet`. Truoc 17/08 hai thu do
-- trung nhau nen khong ai thay khac biet; tu khi lord_v2 dung plan_hash thi
-- **0/1124 hang moi co gt_ma khop bang gia_thuyet**, va moi phep doi soat
-- `JOIN ket_qua k ON k.gt_ma = f.gt_ma` lang le chi con nhin thay 675 hang cu
-- cua 15-16/08. Do la goc that cua van de `vd_so_sach_khong_khop`.
-- `gt_ma_nguon` giu ma gia thuyet de doi soat duoc; NULL cho hang cu va cho
-- cac ho do dac (khong co gia thuyet nao dang sau).
CREATE TABLE IF NOT EXISTS fdr(
  id INTEGER PRIMARY KEY AUTOINCREMENT, luc TEXT, ho TEXT, gt_ma TEXT,
  p REAL, nguong REAL, bac_bo INTEGER, tai_nguyen REAL, gt_ma_nguon TEXT);

-- NOI DUNG THAT cua tai lieu (toan van bai bao / ma nguon / bai dien dan).
-- Tach khoi `tai_lieu` vi hai thu khac han ve kich thuoc va vong doi: `tai_lieu`
-- la muc luc (vai tram byte, giu mai), `noi_dung` la ban doc (vai chuc nghin
-- byte, co the don khi da boc xong). Truoc 16/08 bang nay khong ton tai - ca
-- "thu vien" cua he la 51 trang A4 tieu de va tom tat.
CREATE TABLE IF NOT EXISTS noi_dung(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tai_lieu_id INTEGER, van_tay TEXT UNIQUE,
  url TEXT, kieu TEXT, cach TEXT, so_ky_tu INTEGER, so_ky_tu_goc INTEGER,
  van_ban TEXT, luc TEXT, da_boc INTEGER DEFAULT 0, ket_boc TEXT);

CREATE INDEX IF NOT EXISTS ix_nd_boc ON noi_dung(da_boc, id);

-- HOP DONG SEEKER -> QUANTLAB. Hai bang nay la log CHI-THEM: fingerprint
-- dam bao retry idempotent; Quantlab doc candidate_queue bang cursor id.
CREATE TABLE IF NOT EXISTS artifact(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fingerprint TEXT NOT NULL UNIQUE CHECK(length(fingerprint)=64),
  artifact_type TEXT NOT NULL CHECK(artifact_type IN('document','code','trade_history','candidate')),
  schema_version INTEGER NOT NULL CHECK(schema_version>0),
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS candidate_queue(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  candidate_fingerprint TEXT NOT NULL UNIQUE,
  artifact_id INTEGER NOT NULL UNIQUE,
  priority INTEGER NOT NULL DEFAULT 5 CHECK(priority BETWEEN 1 AND 9),
  route TEXT NOT NULL DEFAULT 'QUANTLAB',
  enqueued_at TEXT NOT NULL,
  FOREIGN KEY(artifact_id) REFERENCES artifact(id));

CREATE INDEX IF NOT EXISTS ix_artifact_type ON artifact(artifact_type, id);
CREATE INDEX IF NOT EXISTS ix_candidate_route ON candidate_queue(route, id);

CREATE TRIGGER IF NOT EXISTS candidate_queue_valid_artifact
BEFORE INSERT ON candidate_queue
WHEN NOT EXISTS(
  SELECT 1 FROM artifact
  WHERE id=NEW.artifact_id
    AND fingerprint=NEW.candidate_fingerprint
    AND artifact_type='candidate')
BEGIN
  SELECT RAISE(ABORT, 'candidate_queue must reference its CandidateArtifact');
END;

CREATE TRIGGER IF NOT EXISTS artifact_no_update
BEFORE UPDATE ON artifact BEGIN
  SELECT RAISE(ABORT, 'artifact is append-only');
END;

CREATE TRIGGER IF NOT EXISTS artifact_no_delete
BEFORE DELETE ON artifact BEGIN
  SELECT RAISE(ABORT, 'artifact is append-only');
END;

CREATE TRIGGER IF NOT EXISTS candidate_queue_no_update
BEFORE UPDATE ON candidate_queue BEGIN
  SELECT RAISE(ABORT, 'candidate_queue is append-only');
END;

CREATE TRIGGER IF NOT EXISTS candidate_queue_no_delete
BEFORE DELETE ON candidate_queue BEGIN
  SELECT RAISE(ABORT, 'candidate_queue is append-only');
END;

-- DE XUAT CO CHE cua tru NGHI. Song tach khoi `gia_thuyet` co chu y: mot de
-- xuat BI TU CHOI (sai cu phap, nhin truoc, kich hoat 0,1% so bar) khong phai
-- mot gia thuyet - no chua bao gio duoc kiem dinh. Nhung no van phai duoc ghi
-- lai, vi vong sau chinh no la du lieu day: khong co so nay thi tang suy nghi
-- lap lai dung mot loi mai mai.
-- THANH PHAN THU HOI DUOC tu mot ban doc, KE CA khi ca he thong bi loai.
-- Xem `nhan/thu_hoi_thanh_phan.py`. Mot he toi khong co nghia moi manh cua no
-- deu toi: Sonic R khong dung duoc don lap nhung EMA34 high/low, EMA89,
-- linreg 89, Hull 377, Donchian 55 thi dung duoc lam tham so va bo loc.
-- `dien_dat_duoc=0` khong phai rac - do la danh sach TOAN HANG CAN THEM, do tu
-- ma nguoi ta that su viet.
CREATE TABLE IF NOT EXISTS thanh_phan(
  id INTEGER PRIMARY KEY AUTOINCREMENT, van_tay TEXT UNIQUE,
  chi_bao TEXT, tham_so TEXT, cot TEXT, ngon_ngu TEXT,
  dien_dat_duoc INTEGER DEFAULT 0, con_thieu TEXT, trich TEXT,
  nguon TEXT, url TEXT, tieu_de TEXT, ly_do_loai TEXT,
  so_lan INTEGER DEFAULT 1, luc TEXT);

CREATE INDEX IF NOT EXISTS ix_tp_dien_dat ON thanh_phan(dien_dat_duoc, so_lan);

CREATE TABLE IF NOT EXISTS de_xuat(
  id INTEGER PRIMARY KEY AUTOINCREMENT, luc TEXT, tru TEXT, ten TEXT UNIQUE,
  ho TEXT, co_che TEXT, dsl TEXT, nguon TEXT, nhan INTEGER DEFAULT 0,
  ly_do_tu_choi TEXT, verdict TEXT, chi_tiet TEXT,
  trang_thai TEXT DEFAULT 'MOI');

CREATE TABLE IF NOT EXISTS nhip(
  tru TEXT PRIMARY KEY, luc TEXT, trang_thai TEXT, chi_tiet TEXT);

CREATE TABLE IF NOT EXISTS chi_so_vh(
  id INTEGER PRIMARY KEY AUTOINCREMENT, luc TEXT, ten TEXT, gia_tri REAL, chi_tiet TEXT);

CREATE INDEX IF NOT EXISTS ix_viec_cho ON viec(trang_thai, tru, uu_tien);
CREATE INDEX IF NOT EXISTS ix_tl_nguon ON tai_lieu(nguon, luc);
CREATE INDEX IF NOT EXISTS ix_kq_gt ON ket_qua(gt_ma, luc);
CREATE INDEX IF NOT EXISTS ix_csvh ON chi_so_vh(ten, luc);
"""


def bay_gio() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def van_tay(*phan) -> str:
    return hashlib.sha1("|".join(str(p) for p in phan).encode("utf-8", "replace")).hexdigest()


@contextmanager
def ket_noi(timeout: float = 30.0):
    """Ket noi SQLite dung chung cho nhieu tien trinh (WAL)."""
    DB.parent.mkdir(parents=True, exist_ok=True)
    cn = sqlite3.connect(DB, timeout=timeout, isolation_level=None)
    cn.row_factory = sqlite3.Row
    try:
        cn.execute("PRAGMA journal_mode=WAL")
        cn.execute("PRAGMA synchronous=NORMAL")
        cn.execute("PRAGMA busy_timeout=30000")
        yield cn
    finally:
        cn.close()


#: Cot them vao sau khi bang da ton tai. `CREATE TABLE IF NOT EXISTS` khong
#: dong bo cot cho bang cu, nen mot cot moi khai trong SCHEMA se khong bao gio
#: xuat hien tren so cai dang chay - va se hong lang le o dung lan ghi dau.
COT_THEM_SAU = [("fdr", "gt_ma_nguon", "TEXT"),
                # 11/09/2026 - van tay TAP DU LIEU da ghim luc dang ky. GHI LAI,
                # KHONG dua vao plan_hash: dua vao se doi danh tinh cua moi gia
                # thuyet da co va lam ket luan cu khong doi chieu duoc - dung ly
                # do ma `so_phep_thu` / `the_he_cong` cung chi duoc ghi ra cot.
                ("gia_thuyet", "anh_chup_hash", "TEXT")]


def khoi_tao() -> None:
    with ket_noi() as cn:
        cn.executescript(SCHEMA)
        for bang, cot, kieu in COT_THEM_SAU:
            co = {r["name"] for r in cn.execute(f"PRAGMA table_info({bang})")}
            if cot not in co:
                cn.execute(f"ALTER TABLE {bang} ADD COLUMN {cot} {kieu}")


# --------------------------------------------------------------- SO SU KIEN
def ghi_su_kien(tru: str, loai: str, noi_dung: dict) -> str:
    """Ghi mot dong vao so chi-them. Tra ve hash cua dong vua ghi."""
    with ket_noi() as cn:
        # SELECT-last + INSERT phai la MOT critical section. Khi control plane
        # chay cac tru song song, autocommit o day co the de hai writer cung doc
        # mot hash cuoi va tao hai nhanh. BEGIN IMMEDIATE serialize writer truoc
        # khi doc dau chuoi, trong khi reader WAL van hoat dong binh thuong.
        cn.execute("BEGIN IMMEDIATE")
        try:
            r = cn.execute("SELECT hash FROM su_kien ORDER BY id DESC LIMIT 1").fetchone()
            truoc = r["hash"] if r else "0" * 40
            luc = bay_gio()
            noi = json.dumps(noi_dung, ensure_ascii=False, default=str, sort_keys=True)
            h = van_tay(truoc, luc, tru, loai, noi)
            cn.execute(
                "INSERT INTO su_kien(luc,tru,loai,noi_dung,hash_truoc,hash) VALUES(?,?,?,?,?,?)",
                (luc, tru, loai, noi, truoc, h))
            cn.execute("COMMIT")
            return h
        except Exception:
            cn.execute("ROLLBACK")
            raise


def kiem_chuoi_hash(gioi_han: int | None = None) -> tuple[bool, str]:
    """Kiem tinh toan ven cua so. Mac dinh kiem TOAN BO chuoi."""
    with ket_noi() as cn:
        sql = ("SELECT id,luc,tru,loai,noi_dung,hash_truoc,hash FROM su_kien "
               "ORDER BY id")
        rows = (cn.execute(sql + " LIMIT ?", (gioi_han,)).fetchall()
                if gioi_han is not None else cn.execute(sql).fetchall())
    truoc = "0" * 40
    for r in rows:
        if r["hash_truoc"] != truoc:
            return False, f"dut chuoi tai dong id={r['id']} ({r['luc']})"
        h = van_tay(r["hash_truoc"], r["luc"], r["tru"], r["loai"], r["noi_dung"])
        if h != r["hash"]:
            return False, f"dong id={r['id']} bi sua noi dung ({r['luc']})"
        truoc = r["hash"]
    return True, f"{len(rows)} dong lien mach"


# ------------------------------------------------------------- HANG DOI VIEC
def them_viec(tru: str, loai: str, tham_so: dict | None = None,
              uu_tien: int = 5, chong_trung: bool = True) -> int | None:
    """Them viec vao hang doi chung. Tra id, hoac None neu da co viec y het dang cho."""
    tham_so = tham_so or {}
    vt = van_tay(tru, loai, json.dumps(tham_so, sort_keys=True, ensure_ascii=False))
    with ket_noi() as cn:
        if chong_trung:
            r = cn.execute(
                "SELECT id FROM viec WHERE van_tay=? AND trang_thai IN('CHO','CHAY')",
                (vt,)).fetchone()
            if r:
                return None
        cur = cn.execute(
            "INSERT INTO viec(tru,loai,tham_so,uu_tien,trang_thai,van_tay,tao_luc) "
            "VALUES(?,?,?,?,'CHO',?,?)",
            (tru, loai, json.dumps(tham_so, ensure_ascii=False), uu_tien, vt, bay_gio()))
        return int(cur.lastrowid)


def nhan_viec(tru: str) -> dict | None:
    """Lay 1 viec CHO cua tru, danh dau CHAY. Nguyen tu."""
    with ket_noi() as cn:
        cn.execute("BEGIN IMMEDIATE")
        r = cn.execute(
            "SELECT * FROM viec WHERE tru=? AND trang_thai='CHO' "
            "ORDER BY uu_tien ASC, id ASC LIMIT 1", (tru,)).fetchone()
        if not r:
            cn.execute("COMMIT")
            return None
        cn.execute("UPDATE viec SET trang_thai='CHAY', bat_luc=?, so_lan=so_lan+1 "
                   "WHERE id=?", (bay_gio(), r["id"]))
        cn.execute("COMMIT")
        d = dict(r)
        d["tham_so"] = json.loads(d.get("tham_so") or "{}")
        return d


def xong_viec(vid: int, ket_qua: dict | None = None, loi: str | None = None) -> None:
    with ket_noi() as cn:
        cn.execute(
            "UPDATE viec SET trang_thai=?, xong_luc=?, ket_qua=? WHERE id=?",
            ("LOI" if loi else "XONG", bay_gio(),
             json.dumps(ket_qua or ({"loi": loi} if loi else {}), ensure_ascii=False,
                        default=str)[:4000], vid))


def don_viec_treo() -> int:
    """Khoi dong lai: moi viec dang CHAY la viec cua tien trinh da chet.
    Chuyen thanh LOI (khong bao gio thanh XONG). Tra so dong da doi."""
    with ket_noi() as cn:
        cur = cn.execute(
            "UPDATE viec SET trang_thai='LOI', xong_luc=?, "
            "ket_qua='{\"loi\":\"tien trinh chet giua chung\"}' WHERE trang_thai='CHAY'",
            (bay_gio(),))
        return cur.rowcount


def dem_viec() -> dict:
    with ket_noi() as cn:
        rows = cn.execute(
            "SELECT tru,trang_thai,COUNT(*) n FROM viec GROUP BY tru,trang_thai").fetchall()
    out: dict = {}
    for r in rows:
        out.setdefault(r["tru"], {})[r["trang_thai"]] = r["n"]
    return out


# ----------------------------------------------- HOP DONG SEEKER -> QUANTLAB
def _nap_hop_dong():
    """Import duoc ca khi chay nhu package va khi chay truc tiep so.py."""
    try:
        from . import hop_dong
    except ImportError:  # pragma: no cover - chi dung khi `python nhan/so.py`
        import hop_dong
    return hop_dong


def _them_artifact_trong(cn: sqlite3.Connection, artifact) -> tuple[int, bool]:
    hd = _nap_hop_dong()
    artifact = hd.validate_artifact(artifact)
    cur = cn.execute(
        "INSERT OR IGNORE INTO artifact(fingerprint,artifact_type,schema_version,payload,created_at) "
        "VALUES(?,?,?,?,?)",
        (artifact.fingerprint, artifact.artifact_type, artifact.schema_version,
         artifact.to_json(), bay_gio()))
    row = cn.execute(
        "SELECT id FROM artifact WHERE fingerprint=?", (artifact.fingerprint,)).fetchone()
    if row is None:
        raise RuntimeError("khong the ghi artifact")
    return int(row["id"]), cur.rowcount == 1


def them_artifact(artifact) -> tuple[int, bool]:
    """Ghi artifact bat bien. Tra ``(id, moi_tao)``; retry tra lai cung id."""
    with ket_noi() as cn:
        cn.execute("BEGIN IMMEDIATE")
        try:
            result = _them_artifact_trong(cn, artifact)
            cn.execute("COMMIT")
            return result
        except Exception:
            cn.execute("ROLLBACK")
            raise


def xep_candidate(candidate, priority: int = 5,
                  route: str = "QUANTLAB") -> tuple[int, bool]:
    """Ghi CandidateArtifact va xep vao log ban giao mot cach nguyen tu/idempotent.

    Moi artifact nguon ma candidate tham chieu phai da ton tai va phai la
    document/code/trade_history. Hang doi khong co UPDATE; consumer doc theo id.
    """
    hd = _nap_hop_dong()
    candidate = hd.validate_artifact(candidate)
    if not isinstance(candidate, hd.CandidateArtifact):
        raise hd.ContractError("xep_candidate chi nhan CandidateArtifact")
    if isinstance(priority, bool) or not isinstance(priority, int) or not 1 <= priority <= 9:
        raise hd.ContractError("priority must be an integer from 1 to 9")
    if not isinstance(route, str) or not route.strip():
        raise hd.ContractError("route must not be empty")
    route = route.strip().upper()

    refs = tuple(candidate.source_artifact_fingerprints)
    placeholders = ",".join("?" for _ in refs)
    with ket_noi() as cn:
        cn.execute("BEGIN IMMEDIATE")
        try:
            rows = cn.execute(
                f"SELECT fingerprint,artifact_type FROM artifact WHERE fingerprint IN ({placeholders})",
                refs).fetchall()
            found = {row["fingerprint"]: row["artifact_type"] for row in rows}
            missing = sorted(set(refs) - set(found))
            if missing:
                raise hd.ContractError(
                    "candidate references missing source artifacts: " + ", ".join(missing))
            invalid = sorted(fp for fp, kind in found.items() if kind == "candidate")
            if invalid:
                raise hd.ContractError(
                    "candidate cannot use another candidate as source: " + ", ".join(invalid))

            artifact_id, _ = _them_artifact_trong(cn, candidate)
            cur = cn.execute(
                "INSERT OR IGNORE INTO candidate_queue("
                "candidate_fingerprint,artifact_id,priority,route,enqueued_at) "
                "VALUES(?,?,?,?,?)",
                (candidate.fingerprint, artifact_id, priority, route, bay_gio()))
            row = cn.execute(
                "SELECT id FROM candidate_queue WHERE candidate_fingerprint=?",
                (candidate.fingerprint,)).fetchone()
            if row is None:
                raise RuntimeError("khong the xep candidate")
            result = int(row["id"]), cur.rowcount == 1
            cn.execute("COMMIT")
            return result
        except Exception:
            cn.execute("ROLLBACK")
            raise


def doc_candidate_queue(after_id: int = 0, limit: int = 100,
                        route: str = "QUANTLAB") -> list[dict]:
    """Doc log ban giao theo cursor id ma khong thay doi bat ky dong nao."""
    if isinstance(after_id, bool) or not isinstance(after_id, int) or after_id < 0:
        raise ValueError("after_id must be a non-negative integer")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
        raise ValueError("limit must be an integer from 1 to 1000")
    if not isinstance(route, str) or not route.strip():
        raise ValueError("route must not be empty")
    hd = _nap_hop_dong()
    with ket_noi() as cn:
        rows = cn.execute(
            "SELECT q.id,q.priority,q.route,q.enqueued_at,a.payload "
            "FROM candidate_queue q JOIN artifact a ON a.id=q.artifact_id "
            "WHERE q.route=? AND q.id>? ORDER BY q.id ASC LIMIT ?",
            (route.strip().upper(), after_id, limit)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["candidate"] = hd.artifact_from_json(item.pop("payload"))
        result.append(item)
    return result


# ------------------------------------------------------------------- NHIP TIM
def nhip_tim(tru: str, trang_thai: str = "song", chi_tiet: dict | None = None) -> None:
    with ket_noi() as cn:
        cn.execute(
            "INSERT INTO nhip(tru,luc,trang_thai,chi_tiet) VALUES(?,?,?,?) "
            "ON CONFLICT(tru) DO UPDATE SET luc=excluded.luc, "
            "trang_thai=excluded.trang_thai, chi_tiet=excluded.chi_tiet",
            (tru, bay_gio(), trang_thai,
             json.dumps(chi_tiet or {}, ensure_ascii=False, default=str)[:2000]))


def doc_nhip() -> list[dict]:
    with ket_noi() as cn:
        return [dict(r) for r in cn.execute("SELECT * FROM nhip ORDER BY tru")]


def ghi_chi_so(ten: str, gia_tri: float, chi_tiet: dict | None = None) -> None:
    """Chi so van hanh cho EVO theo doi theo thoi gian."""
    with ket_noi() as cn:
        cn.execute("INSERT INTO chi_so_vh(luc,ten,gia_tri,chi_tiet) VALUES(?,?,?,?)",
                   (bay_gio(), ten, float(gia_tri),
                    json.dumps(chi_tiet or {}, ensure_ascii=False, default=str)[:2000]))


# ------------------------------------------------------------------- VAN DE
def bao_van_de(ma: str, muc: str, mo_ta: str, bang_chung: dict | None = None) -> int | None:
    """EVO bao van de. Trung ma + con MO thi khong nhan ban."""
    with ket_noi() as cn:
        r = cn.execute("SELECT id FROM van_de WHERE ma=? AND trang_thai='MO'",
                       (ma,)).fetchone()
        if r:
            return None
        cur = cn.execute(
            "INSERT INTO van_de(ma,muc,mo_ta,bang_chung,phat_hien_luc,trang_thai) "
            "VALUES(?,?,?,?,?,'MO')",
            (ma, muc, mo_ta,
             json.dumps(bang_chung or {}, ensure_ascii=False, default=str)[:3000], bay_gio()))
        return int(cur.lastrowid)


def dong_van_de(ma: str, hanh_dong: str) -> None:
    with ket_noi() as cn:
        cn.execute("UPDATE van_de SET trang_thai='DA_SUA', hanh_dong=?, sua_luc=? "
                   "WHERE ma=? AND trang_thai='MO'", (hanh_dong, bay_gio(), ma))


def van_de_mo() -> list[dict]:
    with ket_noi() as cn:
        return [dict(r) for r in cn.execute(
            "SELECT * FROM van_de WHERE trang_thai='MO' ORDER BY "
            "CASE muc WHEN 'NANG' THEN 0 WHEN 'VUA' THEN 1 ELSE 2 END, id DESC")]


# --------------------------------------------------------------- GIA THUYET
def _ghi_pham_vi_quet(cn, ma: str, so_phep_thu, the_he_cong) -> None:
    """Ghi SO PHEP THU va LUAT QUYET DINH kem theo mot gia thuyet.

    Hai con so nay KHONG nam trong `plan_hash` (xem `dang_ky_gia_thuyet`), nen
    day la cho duy nhat chung duoc luu. Muc dich khong phai de tinh toan gi, ma
    de mot ket qua PASS sau nay tra loi duoc cau: *"bo tham so nay duoc chon ra
    tu bao nhieu bo?"*

    Ghi bang UPDATE, khong bao gio giam: neu goi lai voi so lon hon thi lay so
    LON (luoi da noi rong). Giam thi bo qua - de tranh mot lan goi thieu doi so
    xoa mat con so that.
    """
    if so_phep_thu is None and the_he_cong is None:
        return
    try:
        cn.execute("ALTER TABLE gia_thuyet ADD COLUMN so_phep_thu INTEGER")
    except Exception:
        pass
    try:
        cn.execute("ALTER TABLE gia_thuyet ADD COLUMN the_he_cong INTEGER")
    except Exception:
        pass
    try:
        if so_phep_thu is not None:
            cn.execute("UPDATE gia_thuyet SET so_phep_thu=? WHERE ma=? "
                       "AND (so_phep_thu IS NULL OR so_phep_thu < ?)",
                       (int(so_phep_thu), ma, int(so_phep_thu)))
        if the_he_cong is not None:
            cn.execute("UPDATE gia_thuyet SET the_he_cong=? WHERE ma=?",
                       (int(the_he_cong), ma))
    except Exception:
        pass


def dang_ky_gia_thuyet(ma: str, co_che: str, template: str, tham_so: dict,
                       tai_san: str, khung: str, cua_so: str, ho: str,
                       nguon: str = "", tru_sinh: str = "QUANTLAB",
                       ghi_chu: str = "", so_phep_thu: int | None = None,
                       the_he_cong: int | None = None) -> tuple[int | None, str]:
    """PRE-REGISTRATION. Dong bang ke hoach TRUOC khi cham du lieu.

    plan_hash phu len: co che + template + tham so + tai san + khung + cua so.
    Doi bat ky thu nao -> hash doi -> la mot gia thuyet KHAC.

    HAI THU plan_hash KHONG PHU, do 30/08/2026 - ghi ro de khong ai tuong no
    phu het:

      1. **SO PHEP THU da quet truoc khi chon ra bo tham so nay.** Quet mot luoi
         3 bo roi dang ky bo thang, va quet mot luoi 20 bo roi dang ky bo thang,
         cho ra plan_hash Y HET NHAU. Muoi bay phep thu kia bien mat khoi so -
         va do dung la lo hong qua khop ma ca cai cong sinh ra de chan.
      2. **LUAT QUYET DINH** (`cong.THE_HE_CONG`). Cai nay da duoc tach o CAP
         FDR (`tao_epoch_fdr(..., decision_generation=...)`) nen ngan sach kiem
         dinh khong bi tron; nhung o cap DANH TINH gia thuyet thi chua.
      3. **TAP DU LIEU** (them 11/09/2026). `du_lieu.kho()` chon ban theo KICH
         THUOC FILE, nen them mot file vao `data/` la doi ban cua ca mot ma -
         khong mot canh bao nao. Hai gia thuyet cung plan_hash van co the da
         chay tren hai bang gia khac nhau. Tu 11/09 co `nhan/anh_chup.py` ghim
         ban va `van_tay_ghim()` bam ca tap ghim; van tay do duoc ghi vao cot
         `anh_chup_hash` - **cung ly do nhu hai muc tren, khong dua vao hash**.

    `nhan/quant_plan.py` (368 dong) dac ta day du ca hai, nhung `tru/quantlab.py`
    **import no ma khong goi mot ham nao** - do la khoang trong THIET KE.

    Buoc nay (30/08) chi GHI LAI hai con so vao cot rieng, KHONG dua vao hash:
    dua vao hash se doi danh tinh cua 361 gia thuyet da dang ky va lam moi ket
    luan truoc do khong doi chieu duoc. Ghi lai truoc thi lo hong nhin thay
    duoc va do dem duoc; dong han no la mot lan chay lai toan bo, can chu du an
    ngoi may.
    """
    ke_hoach = json.dumps(
        {"co_che": co_che, "template": template, "tham_so": tham_so,
         "tai_san": tai_san, "khung": khung, "cua_so": cua_so},
        sort_keys=True, ensure_ascii=False)
    ph = hashlib.sha256(ke_hoach.encode("utf-8")).hexdigest()[:16]
    with ket_noi() as cn:
        r = cn.execute("SELECT id,plan_hash FROM gia_thuyet WHERE ma=?", (ma,)).fetchone()
        if r:
            if r["plan_hash"] != ph:
                raise ValueError(
                    f"gia thuyet {ma} da ton tai voi plan_hash={r['plan_hash']}, "
                    f"khong duoc im lang doi thanh {ph}")
            _ghi_pham_vi_quet(cn, ma, so_phep_thu, the_he_cong)
            _ghi_anh_chup(cn, ma)
            return int(r["id"]), r["plan_hash"]
        cur = cn.execute(
            "INSERT INTO gia_thuyet(ma,co_che,template,tham_so,tai_san,khung,cua_so,"
            "plan_hash,dang_ky_luc,nguon,tru_sinh,ho,trang_thai,ghi_chu) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,'DANG_KY',?)",
            (ma, co_che, template, json.dumps(tham_so, ensure_ascii=False, sort_keys=True),
             tai_san, khung, cua_so, ph, bay_gio(), nguon, tru_sinh, ho, ghi_chu))
        _ghi_pham_vi_quet(cn, ma, so_phep_thu, the_he_cong)
        _ghi_anh_chup(cn, ma)
        ghi_su_kien(tru_sinh, "dang_ky_gia_thuyet",
                    {"ma": ma, "plan_hash": ph, "co_che": co_che, "ho": ho,
                     "so_phep_thu": so_phep_thu, "the_he_cong": the_he_cong})
        return int(cur.lastrowid), ph


def _ghi_anh_chup(cn, ma: str) -> None:
    """Ghi van tay TAP DU LIEU da ghim tai thoi diem dang ky.

    KHONG dua vao `plan_hash` - xem muc 3 trong docstring cua
    `dang_ky_gia_thuyet`. O day chi ghi lai, de sau nay tra loi duoc cau hoi
    "ket qua nay chay tren bang gia nao" ma khong pha danh tinh cua 361 gia
    thuyet da dang ky truoc 11/09.

    Loi o day KHONG duoc chan viec dang ky: mot so ghi chu hong khong duoc lam
    dung ca day chuyen.
    """
    try:
        from nhan import anh_chup as AC
        cn.execute("UPDATE gia_thuyet SET anh_chup_hash=? WHERE ma=?",
                   (AC.van_tay_ghim(), ma))
    except Exception:
        pass


def doi_trang_thai_gt(ma: str, trang_thai: str, ghi_chu: str = "") -> None:
    with ket_noi() as cn:
        cn.execute("UPDATE gia_thuyet SET trang_thai=?, ghi_chu=? WHERE ma=?",
                   (trang_thai, ghi_chu, ma))


class ChamLaiHoldout(RuntimeError):
    """Dinh ghi ket qua thu HAI cho cung mot gia thuyet ma khong khai ly do.

    Luat goc cua du an: "Xac nhan la NHIN Y NGUYEN. Chay lai cung gia thuyet =
    nhin lai cung holdout." Chay lai roi lay ban dep nhat la cach chac chan nhat
    de che ra mot edge khong ton tai.

    LOI DA SAP (do 01/09/2026): luat nay CO duoc viet - nhung viet o BON CHO GOI
    trong `tru/quantlab.py` (`WHERE gt_ma=? AND superseded_by IS NULL`), khong
    viet o CHO GHI. Duong nao quen kiem thi cham lai tu do. Do that tren so cai:
    373 gia thuyet / 1.270 lan cham = **3,40 lan moi gia thuyet**, mot gia thuyet
    bi cham 10 lan, va 3 gia thuyet di FAIL -> PASS. Ca 7 gia thuyet tung PASS
    deu co lich su nhieu lan cham.

    Nen chot chan chuyen ve day: mot luat chi duoc thuc thi o CHO HEP NHAT ma
    moi duong deu phai di qua. Muon cham lai that (co du lieu moi) thi phai KHAI
    `cham_lai="<ly do>"` - tuc phai co y thuc, khong xay ra do quen.
    """


def phoi_nhiem_holdout(gt_ma: str) -> int:
    """Gia thuyet nay da NHIN holdout bao nhieu lan roi (ke ca lan bi superseded).

    VI SAO CAN MOT SO RIENG (do 01/09/2026). FDR dem suat theo HO, va ho duoc
    phep tach khi doi cau truc mo hinh chi phi - dung theo THIET_KE muc 7, vi
    hai the he chi phi la hai thuoc do khac nhau. Nhung khi ho tach thi `j` ve 1
    va nguong LORD nhay tu 5,0e-6 len 0,0129 (**noi gap 2.600 lan**), trong khi
    HOLDOUT thi van la holdout cu - no khong duoc lam moi theo mo hinh chi phi.

    Hau qua do duoc tren so cai: 375 gia thuyet / 1.272 lan cham =
    **3,39 lan moi gia thuyet**, mot gia thuyet cham 10 lan, va 3 gia thuyet di
    tu FAIL sang PASS qua cac lan cham lai - ca ba deu nam trong ro cach ly.
    `AUDCAD.H4.rsi_dao_chieu.n14_vao30_ra_55` co lich su
    FAIL FAIL FAIL FAIL FAIL PASS PASS PASS INVALIDATED PASS.

    Tung buoc mot deu hop le. Cai thieu la khong ai dem TONG so lan nhin, nen
    mot PASS o lan nhin thu 10 trong y het mot PASS o lan nhin dau tren moi
    bao cao. Con so nay khong chan ai ca - no bat mot PASS phai khai ra no la
    lan nhin thu may.
    """
    with ket_noi() as cn:
        r = cn.execute("SELECT COUNT(*) n FROM ket_qua WHERE gt_ma=?", (gt_ma,)).fetchone()
        return int(r["n"]) if r else 0


def ghi_ket_qua(gt_ma: str, chi_so: dict, cong: dict, verdict: str,
                p_placebo: float | None, alpha: float | None,
                t_alpha: float | None, cham_lai: str = "") -> int:
    """CHI-THEM: chay lai cung gia thuyet -> dong moi, dong cu tro superseded_by.

    `cham_lai` la LY DO CHINH DANG de cham lai holdout (vi du: "du lieu moi den
    2026-09"). De rong = day la lan dau; neu that ra da co ket qua song thi ham
    NEM `ChamLaiHoldout` chu khong lang le ghi de.
    """
    with ket_noi() as cn:
        r = cn.execute("SELECT id FROM gia_thuyet WHERE ma=?", (gt_ma,)).fetchone()
        gt_id = int(r["id"]) if r else None
        cu = cn.execute(
            "SELECT id FROM ket_qua WHERE gt_ma=? AND superseded_by IS NULL "
            "ORDER BY id DESC LIMIT 1", (gt_ma,)).fetchone()
        if cu and not cham_lai:
            raise ChamLaiHoldout(
                f"gia thuyet {gt_ma} da co ket qua song (ket_qua id={cu['id']}). "
                "Cham lai holdout phai khai ly do: ghi_ket_qua(..., cham_lai='...')")
        cur = cn.execute(
            "INSERT INTO ket_qua(gt_id,gt_ma,luc,chi_so,cong,verdict,p_placebo,alpha,t_alpha) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (gt_id, gt_ma, bay_gio(),
             json.dumps(chi_so, ensure_ascii=False, default=str),
             json.dumps(cong, ensure_ascii=False, default=str),
             verdict, p_placebo, alpha, t_alpha))
        moi = int(cur.lastrowid)
        if cu:
            cn.execute("UPDATE ket_qua SET superseded_by=? WHERE id=?", (moi, cu["id"]))
    # `lan_nhin` di kem MOI dong ket qua, khong chi dong PASS: mot con so chi
    # doc duoc khi no luon co mat. Dem SAU khi da chen nen dong nay la lan thu
    # may, khong phai con bao nhieu lan truoc do.
    ghi_su_kien("QUANTLAB", "ket_qua",
                {"gt": gt_ma, "verdict": verdict, "p": p_placebo, "t": t_alpha,
                 "cham_lai": cham_lai or None,
                 "lan_nhin_holdout": phoi_nhiem_holdout(gt_ma)})
    return moi


# ------------------------------------------------------------------- TIEN ICH
def mot(sql: str, *args):
    with ket_noi() as cn:
        r = cn.execute(sql, args).fetchone()
        return dict(r) if r else None


def nhieu(sql: str, *args) -> list[dict]:
    with ket_noi() as cn:
        return [dict(r) for r in cn.execute(sql, args)]


def chay(sql: str, *args) -> int:
    with ket_noi() as cn:
        return cn.execute(sql, args).rowcount


if __name__ == "__main__":
    khoi_tao()
    lanh, mo_ta = kiem_chuoi_hash()
    print("DB:", DB)
    print("so:", "LANH" if lanh else "HONG", "-", mo_ta)
    print("viec:", json.dumps(dem_viec(), ensure_ascii=False))
    for n in doc_nhip():
        print(f"  nhip {n['tru']:<10} {n['luc']} {n['trang_thai']}")
