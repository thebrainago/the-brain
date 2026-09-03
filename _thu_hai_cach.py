# -*- coding: utf-8 -*-
"""Tach bach: `requests.get` tran vs `Khach` co phien+cookie. Ai bi 403?"""
import sys, time, re, requests
sys.path.insert(0, '.')
from nhan import duyet_nguoi as DN

H = {'User-Agent': DN.UA}
U = 'https://www.mql5.com/en/code/mt5/experts'

if __name__ == "__main__":
    print("-- CACH 1: requests.get tran, 12s/lan --", flush=True)
    for n in (1, 2, 3, 4):
        u = U + ('' if n == 1 else f'/page{n}')
        try:
            r = requests.get(u, timeout=25, headers=H)
            lk = len(set(re.findall(r'/en/code/(\d+)', r.text)))
            print(f"   trang {n}: HTTP {r.status_code}  {len(r.text):>7} ky tu  {lk:>3} link", flush=True)
        except Exception as e:
            print(f"   trang {n}: LOI {type(e).__name__}", flush=True)
        time.sleep(12)

    print("\n-- CACH 2: Khach (phien + cookie + Referer), nhip 12-18s --", flush=True)
    k = DN.Khach(nhip=(12.0, 18.0))
    for n in (1, 2, 3, 4):
        u = U + ('' if n == 1 else f'/page{n}')
        t = k.lay(u, thu_lai=0)
        lk = len(set(re.findall(r'/en/code/(\d+)', t or ''))) if t else 0
        print(f"   trang {n}: {'OK ' + str(len(t)) if t else 'HONG':<14} {lk:>3} link", flush=True)
    print("   thong ke:", k.thong_ke(), flush=True)
