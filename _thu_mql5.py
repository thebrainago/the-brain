# -*- coding: utf-8 -*-
"""Thu duyet MQL5 nhu nguoi: 8 trang, giu phien, co Referer, nhip ngau nhien."""
import sys, re, time
sys.path.insert(0, '.')
from nhan import duyet_nguoi as DN

if __name__ == "__main__":
    k = DN.khach_cua()
    t0 = time.time()
    tong = set()
    for n in range(1, 9):
        u = 'https://www.mql5.com/en/code/mt5/experts' + ('' if n == 1 else f'/page{n}')
        t = k.lay(u)
        lk = set(re.findall(r'/en/code/(\d+)', t or '')) if t else set()
        tong |= lk
        print(f'  trang {n}: {("OK " + str(len(t))) if t else "HONG":<14} '
              f'{len(lk):>3} link ma   (tong {len(tong)})   {time.time()-t0:.0f}s',
              flush=True)
    print(' thong ke:', k.thong_ke(), flush=True)
    print(f' TONG {len(tong)} ma nguon rieng biet', flush=True)
