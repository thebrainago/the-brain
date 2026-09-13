# -*- coding: utf-8 -*-
"""_thu_hoi_payload.py - tai lai PAYLOAD THAT cho toan bo trang landing con ton.

`ma_nguon.thu_hoi_sai_loai` moi chay tren 40 URL lam mau (31 sua duoc). Con
916 trang `mql5.com/en/code/N` dang nam trong kho duoi dang TRANG chu khong
phai MA. Day la lop nguon giau nhat chua cham toi: mot file `.mq5` that chay
duoc ngay qua tester, khong can LLM luan gi.

Chay lien tuc, ghi tien do xuong dia sau moi me, ben qua su co.
"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nhan import ma_nguon as MN, so as SO

LAB = Path(__file__).resolve().parent

def con_ton() -> int:
    r = SO.mot("SELECT COUNT(*) n FROM noi_dung WHERE url LIKE "
               "'%mql5.com/%/code/%' AND cach != 'mql5_download'")
    return int(r["n"]) if r else 0

if __name__ == "__main__":
    me = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    t0 = time.time()
    tong = {"thu_lai": 0, "sua_duoc": 0, "bo_cuoc": 0, "van_sai": 0, "me": 0}
    for i in range(1, 200):
        ton = con_ton()
        print("=== ME %d | con ton %d | %.0f phut ==="
              % (i, ton, (time.time() - t0) / 60), flush=True)
        if ton <= 0:
            break
        try:
            b = MN.thu_hoi_sai_loai(gioi_han=me, ngan_sach_giay=900)
        except Exception as e:
            print("  LOI ME:", repr(e)[:200], flush=True)
            time.sleep(5); continue
        print("  ", json.dumps(b, ensure_ascii=False), flush=True)
        for k in ("thu_lai", "sua_duoc", "bo_cuoc", "van_sai"):
            tong[k] += b.get(k, 0)
        tong["me"] = i
        tong["con_ton"] = con_ton()
        tong["phut"] = round((time.time() - t0) / 60, 1)
        (LAB / "reports" / "THU_HOI_PAYLOAD.json").write_text(
            json.dumps(tong, ensure_ascii=False, indent=1), encoding="utf-8")
        if b.get("chan_mang"):
            # mql5 bop toc do sau ~50 luot nhanh. Day KHONG phai het viec:
            # cong `_duong_ra_song` da xac nhan la loi DUONG RA, va khong URL
            # nao bi loai. Nghi roi di tiep, dung dung han.
            print("  bi bop toc do -> nghi 600 giay roi di tiep", flush=True)
            time.sleep(600)
            continue
        if b.get("thu_lai", 0) == 0:
            print("me rong -> dung", flush=True); break
        time.sleep(30)   # di cham de khoi bi bop
    print("TONG:", json.dumps(tong, ensure_ascii=False), flush=True)
