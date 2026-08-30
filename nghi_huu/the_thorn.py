# -*- coding: utf-8 -*-
r"""the_thorn.py - THE THORN: watchdog 3 tru (SEEKER/QUANT/BANKER) chay lien tuc.
Quy tac (xem THE_THORN.md):
  R1  Moi tru 1 tien trinh doc lap, chay LAU DAI theo lich.
  R2  KICH HOAT LAI 1 LAN: khi tru LOI / KHONG dau ra / kem may -> tu restart LAI
      1 lan ngay (guard mat ket noi / mat mang ro rac).
  R3  Retry 1 lan van loi -> ghi thong ke + cooldown, reset nhuong (khong boom).
  R4  Dung im khong co output moi vuot han -> coi kem may, restart 1 lan.
  R5  Chay tru EVOLUTION dinh ky de quan sat loi + toi uu.
  R6  Dung dung 23:00 hom nay hoac co file THORN_STOP hoac CTRL-C.
Chay:  python the_thorn.py            (den 23:00)
       python the_thorn.py --phut 40  (chay 40 phut)
"""
import json, msvcrt, os, re, subprocess, sys, time
from pathlib import Path

LAB = Path(__file__).resolve().parent
PY  = r"C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe"
STATS  = LAB / "reports" / "thorn_stats.json"
LOGRAW = LAB / "reports" / "thorn_log.jsonl"
HB     = LAB / "reports" / "thorn_heartbeat.txt"
STOP   = LAB / "THORN_STOP"
LOCK   = LAB / "thorn.lock"
LOCK_H = None   # file handle giu k het quyen trong luc chay

# (ten, doi so, chu ky_giay, han_dung_im_giay)
TRU = [
    {"ten": "SEEKER", "args": [str(LAB / "seeker_quy_tac.py")], "chu_ky": 90, "han_dung_im": 150},
    {"ten": "QUANT", "args": [str(LAB / "quant" / "auto_kham_pha.py"), "--n-worker", "6"], "chu_ky": 600, "han_dung_im": 480},
    {"ten": "BANKER", "args": [str(LAB / "banker.py")], "chu_ky": 600, "han_dung_im": 300},
]
EVO_CHU_KY = 1800
EVO_TIMEOUT = 600
MAU_LOI = re.compile(r"Traceback|Error|Exception|Khong tim thay", re.I)
MAU_MANG = re.compile(r"LOI\s+mang|Connection|Proxy|timed out|time out|DEADLINE", re.I)


def ghi_log(e):
    LOGRAW.parent.mkdir(exist_ok=True)
    with LOGRAW.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")


def ghi_stats(tham, tru, evo):
    STATS.parent.mkdir(exist_ok=True)
    STATS.write_text(json.dumps(
        {"luc": time.strftime("%Y-%m-%d %H:%M:%S"), "thong_tin": tham,
         "tru": tru, "evolution": evo},
        ensure_ascii=False, indent=1), encoding="utf-8")


def _song(pid):
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def tu_khoa():
    global LOCK_H
    LOCK.parent.mkdir(exist_ok=True)
    if not LOCK.exists():
        LOCK.write_text("0", encoding="utf-8")
    LOCK_H = LOCK.open("r+", encoding="utf-8")
    try:
        msvcrt.locking(LOCK_H.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        print("Thorn dang chay boi tien trinh khac - thoat.")
        sys.exit(0)
    LOCK_H.seek(0)
    LOCK_H.write(str(os.getpid()))
    LOCK_H.flush()


def khoi_dong(t):
    logf = (LAB / f"tru_{t['ten'].lower()}.log").open("w", encoding="utf-8", buffering=1)
    p = subprocess.Popen([PY, *t["args"]], stdout=logf, stderr=subprocess.STDOUT,
                         cwd=str(LAB))
    t["proc"] = p
    t["logf"] = logf
    t["bat"] = time.time()
    t["kich_thuoc_cu"] = 0
    t["due"] = None
    t["revive"] = True
    return p


def kt_tra(ten, rc):
    """Phan loai dau ra tru: ok / loi-code / loi-mang.
    rc==0 -> chay thanh cong (chi xuong phan loi khi tien trinh that bat)."""
    if rc == 0:
        return "ok"
    try:
        s = (LAB / f"tru_{ten.lower()}.log").read_text(encoding="utf-8",
                                                        errors="replace") or ""
    except Exception:
        return "no-log"
    if MAU_MANG.search(s):
        return "loi-mang"
    if MAU_LOI.search(s):
        return "loi-code"
    return "khong-ro"


def xu_ly_xong(t, rc):
    ten = t["ten"]
    loai = kt_tra(ten, rc)
    # dau ra trong ("khong tac vu") cung coi la ket thuc binh thuong
    ok = (rc == 0) and loai == "ok"
    if ok:
        t["ok_lien_tuc"] = t.get("ok_lien_tuc", 0) + 1
        t["loi_lien_tuc"] = 0
        t["revive"] = True
        t["due"] = time.time() + t["chu_ky"]
        ghi_log({"luc": ts(), "tru": ten, "loai": "ok", "rc": rc})
    elif t["revive"]:
        # R2: kich hoat lai 1 lan ngay
        t["revive"] = False
        t["due"] = time.time() + 6
        t.pop("proc", None)
        ghi_log({"luc": ts(), "tru": ten, "loai": loai, "rc": rc, "retry": "lan-1"})
    else:
        # R3: het nhuong -> cooldown
        t["loi_lien_tuc"] = t.get("loi_lien_tuc", 0) + 1
        t["revive"] = True
        t["due"] = time.time() + max(t["chu_ky"], 120)
        t.pop("proc", None)
        ghi_log({"luc": ts(), "tru": ten, "loai": loai, "rc": rc, "retry": "huy-bo"})


def ts():
    return time.strftime("%H:%M:%S")


def cho_1_luot(evo_due):
    now = time.time()
    for t in TRU:
        ten = t["ten"]
        proc = t.get("proc")
        if proc is not None:
            if proc.poll() is None:
                # dang chay: kiem tra dung im (R4)
                dung_im = now - t["bat"]
                kl = 0
                try:
                    if t.get("logf"):
                        t["logf"].flush()
                        kl = t["logf"].tell()
                except Exception:
                    kl = t["kich_thuoc_cu"]
                if dung_im > t["han_dung_im"] and kl <= t["kich_thuoc_cu"]:
                    proc.kill(); proc.wait()
                    t.pop("proc", None)
                    try:
                        if t.get("logf"):
                            t["logf"].close()
                    except Exception:
                        pass
                    if t["revive"]:
                        t["revive"] = False
                        t["due"] = now + 6
                        ghi_log({"luc": ts(), "tru": ten, "loai": "kem-may",
                                 "retry": "lan-1"})
                    else:
                        t["revive"] = True
                        t["due"] = now + max(t["chu_ky"], 120)
                        ghi_log({"luc": ts(), "tru": ten, "loai": "kem-may",
                                 "retry": "huy-bo"})
                else:
                    t["kich_thuoc_cu"] = kl
                continue
            # tien trinh da ket thuc
            try:
                if t.get("logf"):
                    t["logf"].close()
            except Exception:
                pass
            t.pop("proc", None)
            xu_ly_xong(t, proc.returncode)
        else:
            if t.get("due") is not None and now >= t["due"]:
                khoi_dong(t)
                ghi_log({"luc": ts(), "tru": ten, "loai": "start",
                         "lan": t.get("ok_lien_tuc", 0)})
    #--- EVOLUTION (R5) ---
    if now >= evo_due:
        try:
            r = subprocess.run([PY, str(LAB / "evolution.py")], capture_output=True,
                               text=True, cwd=str(LAB), timeout=EVO_TIMEOUT,
                               encoding="utf-8", errors="replace")
            ghi_log({"luc": ts(), "tru": "EVOLUTION",
                     "loai": "ok" if r.returncode == 0 else "loi",
                     "tail": (r.stdout or "")[-120:], "rc": r.returncode})
        except Exception as e:
            ghi_log({"luc": ts(), "tru": "EVOLUTION", "loai": "loi",
                     "tail": str(e)[:120]})
        evo_due = now + EVO_CHU_KY
    HB.write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
    return evo_due


def main(phut=None):
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    tu_khoa()
    den = time.time() + phut * 60 if phut else None
    if den is None:
        # 23:00 hom nay
        h = time.localtime().tm_hour
        den = time.time() if h >= 23 else time.mktime(
            time.strptime(time.strftime("%Y-%m-%d 23:00:00"), "%Y-%m-%d %H:%M:%S"))
    tham = {"bat_dau": time.strftime("%Y-%m-%d %H:%M:%S"),
            "den_den": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(den))}
    print(f"=== THE THORN: 3 tru chay lien tuc den {tham['den_den']} ===")
    for t in TRU:
        khoi_dong(t)
        print(f"  start {t['ten']} (chu ky {t['chu_ky']}s)")
    evo_due = time.time() + EVO_CHU_KY
    while True:
        if STOP.exists():
            print("  thay THORN_STOP - dung.")
            break
        if den is not None and time.time() >= den:
            print(f"  het gio ({time.strftime('%H:%M:%S')}) - dung.")
            break
        try:
            evo_due = cho_1_luot(evo_due)
            time.sleep(10)
        except KeyboardInterrupt:
            print("  CTRL-C - dung.")
            break
        except Exception as e:
            try:
                ghi_log({"luc": ts(), "tru": "THORN", "loai": "loi",
                         "tail": str(e)[:150]})
            except Exception:
                pass
            print("  [loi vong lap] " + str(e)[:100], flush=True)
            time.sleep(10)
    stat_t = {t["ten"]: {"ok_lien_tuc": t.get("ok_lien_tuc", 0),
                         "loi_lien_tuc": t.get("loi_lien_tuc", 0),
                         "revive": t.get("revive", True)} for t in TRU}
    ghi_stats(tham, stat_t, {})
    print("  ghi thong ke:", STATS)


if __name__ == "__main__":
    phut = None
    if "--phut" in sys.argv:
        i = sys.argv.index("--phut")
        phut = float(sys.argv[i + 1])
    main(phut)
