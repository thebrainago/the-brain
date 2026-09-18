# -*- coding: utf-8 -*-
"""
do_bang_thong_ram.py - Do bang thong bo nho, de doi chieu TRUOC va SAU khi nang RAM.

Vi sao can: may dang cam 1 thanh RAM tren bo mach quad-channel -> chay single-channel.
MT5 chay 20 agent va the_brain chay Pool(10) deu doc/ghi mang lon cung luc, tuc bi
chan o BANG THONG chu khong phai o so nhan CPU.

Chay truoc khi mua RAM, luu lai so. Cam RAM xong chay lai, so sanh.
Neu so KHONG tang thi RAM khong phai nut that, dung mua them gi nua.

    python do_bang_thong_ram.py
"""
import time
import numpy as np
from multiprocessing import Pool, cpu_count

MB = 1024 ** 2
KICH_THUOC = 256 * MB // 8   # 256 MB moi mang float64


def _mot_luong(_):
    """Copy + cong don mang 256MB, tra ve so byte da cham vao."""
    a = np.ones(KICH_THUOC, dtype=np.float64)
    b = np.empty_like(a)
    t0 = time.perf_counter()
    vong = 5
    for _ in range(vong):
        np.copyto(b, a)      # doc 256MB + ghi 256MB
        b += 1.0             # doc 256MB + ghi 256MB
    dt = time.perf_counter() - t0
    byte = vong * 4 * KICH_THUOC * 8
    return byte, dt


def do(so_luong):
    t0 = time.perf_counter()
    if so_luong == 1:
        ket_qua = [_mot_luong(0)]
    else:
        with Pool(so_luong) as p:
            ket_qua = p.map(_mot_luong, range(so_luong))
    tong_giay = time.perf_counter() - t0
    tong_byte = sum(k[0] for k in ket_qua)
    return tong_byte / tong_giay / 1e9   # GB/s


if __name__ == "__main__":
    print(f"So luong logic: {cpu_count()}")
    print("Dang do (moi muc ~vai giay)...\n")
    print(f"{'So luong':>10} | {'Bang thong (GB/s)':>18}")
    print("-" * 33)
    for n in (1, 2, 4, 10, 20):
        if n > cpu_count():
            continue
        gbs = do(n)
        print(f"{n:>10} | {gbs:>18.1f}")

    print("\nDoc ket qua:")
    print("  - 1 luong ~10-14 GB/s la binh thuong cho DDR4-2133.")
    print("  - Diem MAU CHOT: con so o 10 va 20 luong.")
    print("    Single-channel: no BAO HOA quanh 12-17 GB/s du tang bao nhieu luong.")
    print("    Quad-channel:  no phai leo len 45-60 GB/s.")
    print("  - Neu 20 luong khong nhanh hon 2 luong bao nhieu -> DANG DOI BANG THONG,")
    print("    nang RAM se an. Neu no van leo deu -> RAM khong phai nut that.")
