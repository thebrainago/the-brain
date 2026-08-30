# -*- coding: utf-8 -*-
r"""vong_lap.py - VONG LAP 24/7 LIEN TUC (theo thoi gian KHONG deu).
Moi chien luoc co thoi gian test khac nhau (20p - 2h). Vong lap:
  - UOC TINH thoi gian can cho moi chien luoc (dựa tren do phuc tap).
  - KIEM TRA NHANH + EARLY-EXIT: bo combo loi ro rang de khong lang phi.
  - CACHE: cung chien luoc+params+symbol -> khong test lai.
  - NGAN SACH THOI GIAN: chay trong khoang thoi gian cho truoc, luu state, ngu,
    roi tiep tuc -> chay 24/7 hang nam, khong bao gio tinh lai.
Chay:  python vong_lap.py --chay 1   (chay 1 chu ky nhanh de test)
       python vong_lap.py --350      (chay 350 giay)
"""
import sys, time, json, random, pathlib, hashlib
from concurrent.futures import ProcessPoolExecutor

LAB = pathlib.Path(__file__).parent
sys.path.insert(0, str(LAB))
QUANT = LAB / "quant"
sys.path.insert(0, str(QUANT))
import du_lieu, kiem_dinh, auto_kham_pha as ak

STATE = LAB / "vong_lap_state.json"
QUEUE = LAB / "vong_lap_queue.json"
LOG = LAB / "vong_lap_log.json"
HB = LAB / "reports" / "vong_lap_heartbeat.txt"
SYMBOLS = du_lieu.SYMBOLS

def bam(*x):
    return hashlib.sha1(json.dumps(x, default=str).encode()).hexdigest()[:16]

# ---------- UOC TINH THOI GIAN (khong deu nhau) ----------
def uoc_tinh_thoigian(cl):
    do_phuc_tap = {"nhanh": 1, "trung": 2, "sau": 4}.get(cl.get("do_sau", "trung"), 2)
    n_params = len(cl.get("params_grid", [])) or 1
    n_sym = len(cl.get("symbols", SYMBOLS))
    # moi combo ~0.05s + moi lan lam 99 perm; heuristic:
    return round(n_params * n_sym * do_phuc_tap * 0.05, 2)

# ---------- CACHE ----------
def _doc_cache():
    if LOG.exists():
        try:
            return json.loads(LOG.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def _save_cache(c):
    LOG.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")

# ---------- KIEM TRA NHANH + EARLY-EXIT ----------
def _combo_ok(ten, params, sym):
    df = du_lieu.nap(sym, period="10y")
    loai = SYMBOLS[sym][0]
    fn = ak.MECH[ten][0]
    pos = fn(df, **params).shift(1).fillna(0.0)
    so_lenh = int((pos.diff().abs() / 2).sum())
    v = kiem_dinh.sang_loc(df["close"], pos, loai, so_lenh, n_perm=99)
    v.update({"ten": ten, "params": params, "symbol": sym, "loai": loai})
    return v

def kiem_tra_nhanh(cl, ngat_giay=600):
    """Test cac combo cua 1 chien luoc, EARLY-EXIT, co cache. Tra ket qua."""
    ten = cl["ten"]; grid = cl.get("params_grid", []); syms = cl.get("symbols", SYMBOLS)
    cache = _doc_cache()
    t0 = time.time(); ds = []
    for p in grid:
        for sym in syms:
            key = bam(ten, p, sym)
            if key in cache:
                ds.append(cache[key]); continue
            if time.time() - t0 > ngat_giay:   # ngung neu het ngan sach
                return {"bi_ngat": True, "da_quet": ds, "thoigian": time.time() - t0}
            v = _combo_ok(ten, p, sym)
            cache[key] = v
            ds.append(v)
            # EARLY-EXIT: combo loi ro rang -> khong say them
            if v["so_lenh"] >= 20 and v["edge"] < -5:
                cache[key] = v
    _save_cache(cache)
    dat = [d for d in ds if d.get("dat")]
    return {"bi_ngat": False, "da_quet": ds, "dat": dat,
            "thoigian": round(time.time() - t0, 2)}

# ---------- STATE ----------
def _doc_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"xong": [], "ngay": time.strftime("%Y-%m-%d")}

def _save_state(st):
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")

# ---------- VONG LAP ----------
def lay_queue():
    if QUEUE.exists():
        try:
            return json.loads(QUEUE.read_text(encoding="utf-8"))
        except Exception:
            pass
    # mac dinh: 2 chien luoc mau de test
    return [
        {"id": "dk_mau", "ten": "donchian", "params_grid": [{"n": 10}, {"n": 20}, {"n": 55}],
         "symbols": ["^GSPC", "GC=F", "EURUSD=X"], "do_sau": "nhanh"},
        {"id": "sma_mau", "ten": "sma_cross", "params_grid": [{"fast": 5, "slow": 20}, {"fast": 10, "slow": 50}],
         "symbols": ["^GSPC", "EURUSD=X"], "do_sau": "nhanh"},
    ]

def main_loop(ngan_sach_giay=3600, ngu_giua=30):
    st = _doc_state()
    xong_ids = set(st.get("xong", []))
    print(f"=== VONG LAP 24/7 bat dau (ngan sach {ngan_sach_giay}s, ngu {ngu_giua}s) ===")
    while True:
        queue = lay_queue()
        viec = [cl for cl in queue if cl["id"] not in xong_ids]
        if not viec:
            print("[vong_lap] het viec trong queue, ngu 60s..."); time.sleep(60); continue
        for cl in viec:
            tg = uoc_tinh_thoigian(cl)
            print(f"  -> {cl['id']}: uoc tinh ~{tg}s (do_sau={cl.get('do_sau')})")
            kq = kiem_tra_nhanh(cl, ngat_giay=ngan_sach_giay)
            dat = kq["dat"]
            print(f"      quet {len(kq['da_quet'])} combo trong {kq['thoigian']}s, DAT={len(dat)}")
            for r in dat[:6]:
                print(f"        edge={r['edge']:+.1f}% {r['ten']} {r['params']} {r['symbol']} PF={r['pf']} p={r['placebo_p']}")
            st["xong"] = list(xong_ids) + [cl["id"]]
            _save_state(st)
        HB.write_text(time.strftime('%Y-%m-%d %H:%M:%S') + " alive\n", encoding="utf-8")
        print(f"[vong_lap] het chu ky, ngu {ngu_giua}s...")
        time.sleep(ngu_giua)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--chay", action="store_true")
    a = ap.parse_args()
    if a.chay:
        main_loop(ngan_sach_giay=120, ngu_giua=5)
    else:
        # test 1 chu ky nhanh
        for cl in lay_queue():
            tg = uoc_tinh_thoigian(cl)
            print(f"{cl['id']}: uoc tinh {tg}s")
        print("dung: --chay de chay vong lap that")
