# -*- coding: utf-8 -*-
"""_boc_video_khoa_hoc.py - doc 55 video khoa hoc SONG SONG roi boc co che.

Chu du an 13/09/2026: *"May khoa hoc do that ra toi da hoc roi nhung cho bro
coi nhu bai tap. Boc va test 14gb du lieu do di. Xong roi xoa."*

Nen day khong chi la mot lan thu hoach - no la **phep thu tren du lieu that**
cho ca hai khau: video -> van ban, va van ban -> co che.

## CHIA VIEC

Moi tien trinh lay mot LAT theo chi so (`i % so_luong == lat`), khong chia theo
khoi. Lat theo chi so thi moi tien trinh nhan ca file to lan file nho; chia
theo khoi thi tien trinh om nam file `.mov` 1,7 GB chay mot minh ba tieng trong
khi ba tien trinh kia da xong.

`cpu_threads` chia deu 20 luong cua may cho so tien trinh. De mac dinh (0 = lay
het) thi bon tien trinh moi cai doi 20 luong va tranh nhau, cham hon chay it
tien trinh.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

THU_MUC = "F:/TeraBoxDownload"
SO_LUONG = 4
LUONG_CPU = 5          # 20 luong may / 4 tien trinh


def _lat(lat: int, so_luong: int, model: str) -> int:
    """Than cua MOT tien trinh con."""
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    os.environ["OMP_NUM_THREADS"] = str(LUONG_CPU)
    from faster_whisper import WhisperModel
    from nhan import doc_video_cuc_bo as DV

    ds = [f for i, f in enumerate(DV.tim(THU_MUC)) if i % so_luong == lat]
    ds = [f for f in ds if not DV.da_doc(f)]
    print("[lat %d] %d video" % (lat, len(ds)), flush=True)
    if not ds:
        return 0
    m = WhisperModel(model, device="cpu", compute_type="int8",
                     cpu_threads=LUONG_CPU)
    t0 = time.time()
    for i, f in enumerate(ds, 1):
        if DV.da_doc(f):        # tien trinh khac vua lam xong
            continue
        r = DV.mot_video(f, m, model, "vi")
        print("[lat %d] %2d/%d %-40s %6s ky tu x%-5s %.0f phut"
              % (lat, i, len(ds), f.name[:40], r.get("ky_tu", "LOI"),
                 r.get("nhanh_hon_thuc_te", "-"), (time.time() - t0) / 60),
              flush=True)
    return 0


def main() -> int:
    if "--lat" in sys.argv:
        i = sys.argv.index("--lat")
        return _lat(int(sys.argv[i + 1]), int(sys.argv[i + 2]), sys.argv[i + 3])

    from nhan import doc_video_cuc_bo as DV
    model = "small"
    ds = DV.tim(THU_MUC)
    chua = [f for f in ds if not DV.da_doc(f)]
    gio = sum(DV._thoi_luong(f) for f in chua) / 3600
    print("%d video, %d chua doc, %.1f gio -> uoc %.1f gio voi %d tien trinh"
          % (len(ds), len(chua), gio, gio / 3.2 / SO_LUONG, SO_LUONG),
          flush=True)
    if not chua:
        print("het viec")
        return 0

    (LAB / "nhat_ky").mkdir(exist_ok=True)
    con = []
    for lat in range(SO_LUONG):
        f = open(LAB / "nhat_ky" / ("video_lat%d.log" % lat), "w",
                 encoding="utf-8")
        con.append((subprocess.Popen(
            [sys.executable, "-u", __file__, "--lat", str(lat),
             str(SO_LUONG), model], cwd=str(LAB), stdout=f,
            stderr=subprocess.STDOUT), f))
    t0 = time.time()
    for p, f in con:
        p.wait()
        f.close()
    print("xong %.1f phut" % ((time.time() - t0) / 60), flush=True)

    from nhan import so as SO
    r = SO.mot("SELECT COUNT(*) n, SUM(so_ky_tu) k FROM noi_dung WHERE kieu=?",
               DV.KIEU)
    print("trong kho: %s ban doc, %s ky tu" % (r["n"], r["k"]), flush=True)
    (LAB / "reports" / "VIDEO_KHOA_HOC.json").write_text(
        json.dumps({"video": len(ds), "ban_doc": r["n"], "ky_tu": r["k"],
                    "gio_video": round(gio, 1)}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
