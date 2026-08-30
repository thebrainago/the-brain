# -*- coding: utf-8 -*-
"""THE BRAIN 24/7 - dieu phoi viec theo chat luong nguon.

Chay:  python brain_24h.py            -> daemon 24/7 (loi chay nen)
       python brain_24h.py --1-lan    -> chay 1 luot roi thoat (de test/lich)
       python brain_24h.py --xem      -> xem hang doi + thu tu uu tien
       python brain_24h.py --them-viec ten=quet_test lenh="python quet_rong.py --nguon arxiv"

Nguyen tac:
  - Hang doi: reports/brain_24h_queue.json (chua lenh, chu ky, nguon, trang thai)
  - Uu tien = diem_chat_luong(nguon) * he_so_loai + 0.3 neu chua chay lan nao
  - Viec nao chay xong -> cap nhat so chat luong nguon (vong phan hoi)
  - Nhip tim ghi reports/BRAIN_nhip_tim.json (cung format cu)
  - Ngan sach viec NANG (sang co che) gioi han moi ngay, khong chan kham pha
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
REPORTS = HERE / "reports"
CONFIG = HERE / "nguon_config.json"
QUEUE = REPORTS / "brain_24h_queue.json"
STATE = REPORTS / "brain_24h_state.json"
LOG_DIR = REPORTS / "24h"
NHIP_TIM = REPORTS / "BRAIN_nhip_tim.json"

import nguon_chat_luong as ncl

HE_SO_LOAI = {"quet": 1.0, "loc": 1.2, "sang": 1.3, "giai_ma": 1.5, "chi_phi": 1.8, "kiem_tra": 0.8}
MAU_CFG = {
    "brain_24h": {
        "nhin_moi_giay": 60,
        "so_tho_song_song": 2,
        "gioi_han_phut": 30,
        "so_viec_nang_moi_ngay": 3,
    }
}

VIEC_MAC_DINH = [
    dict(id="quet_arxiv", loai="quet", nguon="arXiv", chu_ky_phut=1440,
         lenh=["python", "quet_rong.py", "--nguon", "arxiv", "--so", "8"]),
    dict(id="quet_github", loai="quet", nguon="GitHub", chu_ky_phut=1440,
         lenh=["python", "quet_rong.py", "--nguon", "github", "--so", "8"]),
    dict(id="quet_huggingface", loai="quet", nguon="HuggingFace", chu_ky_phut=1440,
         lenh=["python", "quet_rong.py", "--nguon", "huggingface", "--so", "8"]),
    dict(id="quet_reddit", loai="quet", nguon="Reddit", chu_ky_phut=1440,
         lenh=["python", "quet_rong.py", "--nguon", "reddit", "--so", "8"]),
    dict(id="quet_rss", loai="quet", nguon="RSS", chu_ky_phut=1440,
         lenh=["python", "quet_rong.py", "--nguon", "rss", "--so", "6"]),
    dict(id="quet_darwinex", loai="quet", nguon="Darwinex", chu_ky_phut=10080,
         lenh=["python", "quet_rong.py", "--nguon", "darwinex", "--so", "10"]),
    dict(id="quet_myfxbook", loai="quet", nguon="Myfxbook", chu_ky_phut=10080,
         lenh=["python", "quet_rong.py", "--nguon", "myfxbook", "--so", "2"]),
    dict(id="quet_youtube", loai="quet", nguon="YouTube", chu_ky_phut=1440,
         lenh=["python", "quet_rong.py", "--nguon", "youtube", "--so", "5"]),
    dict(id="kiem_tra_ma_khoa", loai="kiem_tra", nguon="IMAP", chu_ky_phut=720,
         lenh=["python", "kiem_tra_ma_khoa.py"]),
    dict(id="doc_hop_thu_imap", loai="quet", nguon="IMAP", chu_ky_phut=360,
         lenh=["python", "brain_nguon_moi.py", "hop-thu"]),
    dict(id="loc_nguon", loai="loc", nguon="kho_code", chu_ky_phut=360,
         lenh=["python", "loc_nguon.py", "--tu-dong"]),
    dict(id="do_chi_phi_mt5", loai="chi_phi", nguon="chi_phi", chu_ky_phut=10080,
         lenh=["python", "brain_chi_phi.py"]),
]


def _doc_cfg():
    if CONFIG.exists():
        try:
            d = json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception:
            d = {}
    else:
        d = {}
    d.setdefault("brain_24h", MAU_CFG["brain_24h"])
    CONFIG.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return d["brain_24h"]


def _doc_queue():
    REPORTS.mkdir(exist_ok=True)
    if QUEUE.exists():
        try:
            return json.loads(QUEUE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _luu_queue(q):
    QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")


def _doc_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"da_sang": [], "ngay": "", "so_nang_hom_nay": 0}


def _luu_state(s):
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def nhip_tim(viec=""):
    NHIP_TIM.write_text(json.dumps({
        "luc": datetime.now().isoformat(timespec="seconds"),
        "trang_thai": "chay" if viec else "nghi",
        "pid": os.getpid(),
        "viec": viec,
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def _moi(d, id_):
    v = {"id": id_, "loai": "quet", "nguon": "arXiv", "chu_ky_phut": 1440,
         "lenh": [], "lan_chay": 0, "lan_chay_cuoi": None, "trang_thai": "cho",
         "ket_qua": "", "nang": False}
    v.update({k: x for k, x in d.items() if k != "id"})
    return v


def seed(q):
    """Them viec mac dinh neu chua co trong hang doi."""
    co = {v["id"] for v in q}
    for v in VIEC_MAC_DINH:
        if v["id"] not in co:
            q.append(_moi(v, v["id"]))
            q[-1]["lenh"] = v["lenh"]
            q[-1]["loai"] = v["loai"]
            q[-1]["nguon"] = v["nguon"]
            q[-1]["chu_ky_phut"] = v["chu_ky_phut"]
            q[-1]["nang"] = (v["loai"] == "sang")
    return q


def uu_tien(v):
    he_so = HE_SO_LOAI.get(v["loai"], 1.0)
    return round(ncl.prior(v["nguon"]) * he_so + (0.3 if v["lan_chay"] == 0 else 0), 3)


def san_sang(v, now):
    if v["trang_thai"] == "dang_chay":
        return False
    if not v["lenh"]:
        return False
    # thieu script -> khong spam loi
    if len(v["lenh"]) > 1 and v["lenh"][1].endswith(".py"):
        script = HERE / v["lenh"][1]
        if not script.exists():
            v["trang_thai"] = "thieu_script"
            return False
    if v["lan_chay_cuoi"]:
        try:
            cuoi = datetime.fromisoformat(v["lan_chay_cuoi"])
            if (now - cuoi).total_seconds() < v["chu_ky_phut"] * 60:
                return False
        except Exception:
            pass
    return True


def chay(q, v, log):
    v["trang_thai"] = "dang_chay"
    v["bat_dau"] = datetime.now().isoformat(timespec="seconds")
    _luu_queue(q)
    f = (LOG_DIR / f"{v['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    f.parent.mkdir(exist_ok=True)
    try:
        proc = subprocess.Popen(v["lenh"], cwd=HERE, stdout=open(f, "w", encoding="utf-8"),
                                stderr=subprocess.STDOUT,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception as e:
        v["trang_thai"] = "loi"
        v["ket_qua"] = f"KHONG CHAY DUOC: {str(e)[:80]}"
        return None, f
    return proc, f


def xu_ly_xong(q, v, proc, f, cfg):
    v["lan_chay"] += 1
    v["lan_chay_cuoi"] = datetime.now().isoformat(timespec="seconds")
    v["trang_thai"] = "cho"
    try:
        code = proc.wait(timeout=cfg["gioi_han_phut"] * 60)
    except subprocess.TimeoutExpired:
        proc.kill()
        code = -1
    log = f.read_text(encoding="utf-8", errors="ignore") if f.exists() else ""
    dong_cuoi = [l for l in log.strip().splitlines() if l.strip()][-3:]
    co_loi = "[LOI" in log or "Traceback" in log
    nhan = "CO_LOI" if (code == 0 and co_loi) else ("OK" if code == 0 else f"LOI code={code}")
    v["ket_qua"] = nhan + " | " + " | ".join(dong_cuoi)[:280]
    # vong phan hoi chat luong nguon
    if code == 0:
        m = re.search(r"TONG:\s*(\d+)\s*muc", log)
        if m and v["loai"] == "quet":
            ncl.cap_nhat(v["nguon"], "gioi_thieu", int(m.group(1)))
        elif v["loai"] == "sang":
            ncl.cap_nhat(v["nguon"], "cong_A", 1)
    _luu_queue(q)
    return v


def chay_sang(q, s, cfg, now):
    """Phan viec sang co che: chay cac file .py trong co_che_ds chua xu ly."""
    ngay = now.strftime("%Y-%m-%d")
    if s["ngay"] != ngay:
        s["ngay"] = ngay
        s["so_nang_hom_nay"] = 0
    if s["so_nang_hom_nay"] >= cfg["so_viec_nang_moi_ngay"]:
        return
    thu_muc = HERE / "co_che_ds"
    if not thu_muc.exists():
        return
    s.setdefault("loi_sang", {})
    moi = sorted(p for p in thu_muc.glob("*.py")
                 if p.name not in s["da_sang"] and p.name != "__init__.py"
                 and s["loi_sang"].get(p.name, 0) < 3)
    if not moi:
        return
    p = moi[0]
    s["so_nang_hom_nay"] += 1
    _luu_state(s)
    lenh = ["python", "_ds_chay.py", p.stem, str(p)]
    f = (LOG_DIR / f"sang_{p.stem}_{now.strftime('%Y%m%d_%H%M%S')}.log")
    f.parent.mkdir(exist_ok=True)
    try:
        proc = subprocess.Popen(lenh, cwd=HERE, stdout=open(f, "w", encoding="utf-8"),
                                stderr=subprocess.STDOUT,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        code = proc.wait(timeout=cfg["gioi_han_phut"] * 60)
    except Exception as e:
        code = -1
    log = f.read_text(encoding="utf-8", errors="ignore") if f.exists() else ""
    if code == 0:
        s["da_sang"].append(p.name)
        ncl.cap_nhat("tu_sinh", "cong_A", 1)
    else:
        s["loi_sang"][p.name] = s["loi_sang"].get(p.name, 0) + 1
    _luu_state(s)
    print(f"  [sang] {p.name}: {'OK' if code == 0 else 'LOI'} - " +
          " | ".join([l for l in log.strip().splitlines() if l.strip()][-2:])[:200])


def tick(cfg, mot_lan=False):
    q = seed(_doc_queue())
    s = _doc_state()
    now = datetime.now()
    nhip_tim()
    # viec nang
    chay_sang(q, s, cfg, now)
    # viec thuong: chon theo uu tien
    cho = [v for v in q if san_sang(v, now)]
    cho.sort(key=uu_tien, reverse=True)
    dang = [v for v in q if v["trang_thai"] == "dang_chay"]
    slots = max(0, cfg["so_tho_song_song"] - len(dang))
    da_chay = []
    for v in cho[:slots]:
        nhip_tim(v["id"])
        proc, f = chay(q, v, LOG_DIR)
        if proc is None:
            _luu_queue(q)
            continue
        print(f"  [chay] {v['id']} (uu tien {uu_tien(v)})")
        da_chay.append((v, proc, f))
        if mot_lan:
            break
    _luu_queue(q)
    # cho ket qua (chi khi --1-lan)
    for v, proc, f in da_chay:
        xu_ly_xong(q, v, proc, f, cfg)
        print(f"  [xong] {v['id']}: {v['ket_qua'][:120]}")
    nhip_tim()


def xem():
    q = seed(_doc_queue())
    _luu_queue(q)
    print(f"=== HANG DOI 24/7 ({len(q)} viec) - xep theo uu tien ===")
    for v in sorted(q, key=uu_tien, reverse=True):
        tt = v["trang_thai"]
        print(f"  {uu_tien(v):>5} | {v['id']:24} | {v['nguon']:12} | {tt:14} | lan={v['lan_chay']} | {v['ket_qua'][:60]}")
    ncl.xem()


def tom_tat():
    '''In tom tat ngan gon: so viec, nhip tim, top 5 uu tien, nguon diem cao.'''
    q = seed(_doc_queue())
    _luu_queue(q)
    dem = {}
    for v in q:
        dem[v["trang_thai"]] = dem.get(v["trang_thai"], 0) + 1
    tt = ", ".join(f"{k} {v}" for k, v in sorted(dem.items(), key=lambda x: -x[1]))
    nhip = {}
    if NHIP_TIM.exists():
        try:
            nhip = json.loads(NHIP_TIM.read_text(encoding="utf-8"))
        except Exception:
            pass
    print("=== THE BRAIN 24/7 - TOM TAT ===")
    print(f"Hang doi: {len(q)} viec ({tt})")
    if nhip.get("luc"):
        print(f"Nhip tim: {nhip['luc']} ({nhip.get('trang_thai', '')})")
    print("Top 5 uu tien:")
    for v in sorted(q, key=uu_tien, reverse=True)[:5]:
        print(f"  {uu_tien(v):>5} | {v['id']:26} | {v['nguon']:12} | {v['trang_thai']:14} | lan={v['lan_chay']}")
    try:
        top = ncl.top(3)
        print("Nguon diem cao: " + " | ".join(f"{ten} {n['diem']:.2f}" for ten, n in top))
    except Exception:
        pass


def them_viec(ten, lenh, loai="quet", nguon="arXiv", chu_ky_phut=1440):
    q = _doc_queue()
    if any(v["id"] == ten for v in q):
        print(f"da co viec {ten}")
        return
    v = _moi({}, ten)
    v.update(lenh=lenh.split(), loai=loai, nguon=nguon, chu_ky_phut=chu_ky_phut)
    q.append(v)
    _luu_queue(q)
    print(f"da them viec {ten} (uu tien {uu_tien(v)})")


def main():
    p = argparse.ArgumentParser(description="THE BRAIN 24/7 - dieu phoi viec theo chat luong nguon")
    p.add_argument("--1-lan", action="store_true", help="chay 1 luot roi thoat")
    p.add_argument("--xem", action="store_true", help="xem hang doi + so nguon")
    p.add_argument("--tom-tat", action="store_true", help="in tom tat ngan gon")
    p.add_argument("--them-viec", nargs="*", metavar="ten=... lenh=... [loai=...] [nguon=...] [chu_ky_phut=...]")
    a = p.parse_args()
    if a.them_viec:
        kv = dict(x.split("=", 1) for x in a.them_viec if "=" in x)
        them_viec(kv.get("ten", "viec_moi"), kv.get("lenh", ""), kv.get("loai", "quet"),
                  kv.get("nguon", "arXiv"), int(kv.get("chu_ky_phut", 1440)))
        return
    if a.xem:
        xem()
        return
    if a.tom_tat:
        tom_tat()
        return
    cfg = _doc_cfg()
    if getattr(a, "1_lan"):
        tick(cfg, mot_lan=True)
        return
    print(f"=== THE BRAIN 24/7 - daemon (pid {os.getpid()}) ===")
    while True:
        try:
            tick(cfg)
        except Exception as e:
            print(f"[loi vong lap] {str(e)[:120]}")
            nhip_tim()
        time.sleep(cfg["nhin_moi_giay"])


if __name__ == "__main__":
    main()
