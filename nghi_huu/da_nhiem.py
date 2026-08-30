# -*- coding: utf-8 -*-
r"""da_nhiem.py - EVOLUTION: giai phap DA NHIEM THAT.
3 tru chay la 3 TIEN TRINH python DOC LAP va SONG SONG (subprocess.Popen),
khong phai tuan tu trong 1 luot. Giam sat, ghi ket qua moi tru vao 1 state chung,
tai khoi dong tru khi crash. Chay (da nhiem that, khong block moi tru):
  python da_nhiem.py                 chay 1 dot, 3 tru song song
  python da_nhiem.py --co-tru quant   chay 1 tru
"""
import sys, time, subprocess, json
from pathlib import Path

LAB = Path(__file__).resolve().parent
PY = r"C:\Users\SV STORE\sp500_env\Scripts\python.exe"
STATE = LAB / "ket_hop_state.json"

# (ten, danh sách doi so) mot tien trinh doc lap
TRU = [
    ("SEEKER",  [str(LAB / "seeker_quy_tac.py")]),
    ("QUANTLAB",[str(LAB / "quant" / "auto_kham_pha.py")]),
    ("BANKER",  [str(LAB / "banker.py")]),
]

def chay_mot(ten, args, logf):
    t0 = time.time()
    try:
        with open(logf, "w", encoding="utf-8") as f:
            r = subprocess.run([PY, *args], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=600)
            f.write(r.stdout or ""); f.write(r.stderr or "")
        return ten, round(time.time() - t0, 1), (r.returncode == 0), (r.stdout or "")[-200:]
    except Exception as e:
        return ten, round(time.time() - t0, 1), False, str(e)[:200]

def main(co_tru=None):
    ds = [t for t in TRU if (not co_tru) or t[0] in co_tru]
    t0 = time.time()
    procs = []
    # phong TAT CA trung luc -> song song
    for ten, args in ds:
        logf = LAB / f"da_nhiem_{ten.lower()}.log"
        p = subprocess.Popen([PY, *args], stdout=open(logf, "w", encoding="utf-8"),
                             stderr=subprocess.STDOUT, cwd=str(LAB))
        procs.append((ten, p, logf))
    # cho tat ca xong (song song)
    kq = {}
    for ten, p, logf in procs:
        rc = p.wait(timeout=600)
        so = (logf.read_text(encoding="utf-8", errors="replace") or "")
        kq[ten] = {"time": "{:.1f}s".format(time.time() - t0), "rc": rc,
                   "tail": so.strip().splitlines()[-4:] if so else []}
    tong = time.time() - t0
    print(f"=== DA NHIEM: tong {tong:.1f}s (3 tru phong cum luc, chay song song) ===")
    for ten, v in kq.items():
        print(f"  {ten}: hoan tat (rc={v['rc']})")
        for l in v["tail"]:
            print(f"      {l[:120]}")
    # gop state
    st = {"luc": time.strftime("%Y-%m-%d %H:%M:%S"), "tong_giay": round(tong, 1),
          "tru": {t: {"rc": v["rc"], "thoi_gian": v["time"]} for t, v in kq.items()}}
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
    print("DA GHI:", STATE)
    print("(tong ~ thoi gian tru cham nhat => 3 tru that su song song, khong cong don)")

if __name__ == "__main__":
    co = None
    if "--co-tru" in sys.argv:
        co = [x.strip() for x in sys.argv[sys.argv.index("--co-tru")+1].split(",") if x.strip()]
    main(co)
