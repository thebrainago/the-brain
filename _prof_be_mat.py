"""Driver profile co gioi han: 1 co che x N tai san, de do TY LE thoi gian."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nhan import pham_vi as PV, sang_loc as SL, du_lieu as DL

MAU_TEN = sys.argv[1] if len(sys.argv) > 1 else "ibs_bat_day"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 20

t0 = time.time()
ma = list(PV.kho_du_bar("D1"))[:N]
print(f"[{time.time()-t0:.1f}s] {len(ma)} tai san D1", flush=True)
pv = SL.pham_vi_cua(MAU_TEN)
print(f"[{time.time()-t0:.1f}s] pham_vi_cua({MAU_TEN}) xong", flush=True)
n_ok = 0
for m in ma:
    try:
        r = SL.chay_pheu(MAU_TEN, None, m, "D1", pham_vi=pv)
        n_ok += 1
    except Exception as e:
        print(f"  {m}: {type(e).__name__}: {str(e)[:70]}", flush=True)
print(f"[{time.time()-t0:.1f}s] xong {n_ok}/{len(ma)} o", flush=True)
