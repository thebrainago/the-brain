# -*- coding: utf-8 -*-
"""doc_video_cuc_bo.py - VIDEO TREN DIA -> VAN BAN. Khau con thieu cua Seeker.

## VI SAO CO FILE NAY, VA MOT GHI CHU SAI DA CHAN NO MOT THANG

`hethong.txt` doi *"chuyen doi video thanh co che"*. `doc_video.py` (11/09) lam
duoc mot nua: no lay PHU DE YouTube. Con video NAM TREN DIA thi khong co duong
nao.

Chinh `doc_video.py` giai thich vi sao khong lam not:

    "`faster_whisper` co san trong may va duoc giu lam duong LUI cho video
     khong co phu de - nhung no can ffmpeg nen hien tai chua bat."

**Ghi chu do sai, va do 13/09/2026 no sai theo cach dat nhat:** mot nang luc
CO SAN bi khai la khong co, nen khong ai thu lai suot mot thang. `faster_whisper`
giai ma bang **PyAV** (`av`, da cai san, ban 18.1.0) chu khong goi `ffmpeg` CLI.
Thu that: khong co `ffmpeg` tren PATH, va no van chay.

Day la mot ho loi rieng, khac voi "khau do hong doc nhu ket qua am": o day
**mot gia dinh chua kiem duoc viet thanh tai lieu**, roi tai lieu duoc doc nhu
su that. Luat cua lab - *truoc khi ket luan "khong co X", lay ba thu chac chan
CO ra thu* - phai ap cho ca NANG LUC chu khong chi cho du lieu.

## SO DO DUOC TREN MAY NAY (13/09/2026, 55 video khoa hoc tieng Viet, 37,5 gio)

    model   toc do        chat luong tieng Viet
    tiny    x20 thuc te   khong dung duoc - chu vo nghia
    small   x3,2 thuc te  doc duoc, dung thuat ngu giao dich

`tiny` nhanh gap 6 lan nhung san pham cua no la rac, nen no khong nhanh hon -
no chi khong lam gi. Mac dinh la `small`.

## RANH GIOI

Module nay CHI bien video thanh van ban va ghi vao `noi_dung`. Viec bien van
ban thanh co che van la cua `boc_llm` - mot duong, mot bo luat, mot cho de sua.
Giong het ranh gioi cua `doc_video.py`.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(GOC))

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from nhan import so as SO  # noqa: E402

#: Nhan RIENG, khong dung lai `video_phu_de` cua duong YouTube. Hai duong co
#: do tin khac han nhau: phu de la chu cua tac gia, ban nay la may nghe lai.
KIEU = "video_cuc_bo"

DUOI = (".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".flv", ".wmv",
        ".mp3", ".m4a", ".wav")

#: `small` chu khong `tiny` - xem bang do o dau file. `int8` vi may khong GPU.
MODEL = "small"


def _thoi_luong(f: Path) -> float:
    try:
        import av
        with av.open(str(f)) as c:
            return (c.duration or 0) / 1e6
    except Exception:
        return 0.0


def tim(thu_muc: str | Path) -> list[Path]:
    goc = Path(thu_muc)
    return sorted((p for p in goc.rglob("*") if p.suffix.lower() in DUOI),
                  key=lambda p: p.stat().st_size)


def _van_tay(f: Path) -> str:
    """Van tay theo TEN + KICH THUOC, khong theo noi dung.

    Bam ca file 1,7 GB chi de biet "da doc chua" la tu bo 20 phut cho moi lan
    quet. Ten + kich thuoc du de nhan lai dung file, va neu trung nham thi hau
    qua chi la bo qua mot video - re hon nhieu lan bam."""
    return SO.van_tay("video_cuc_bo", f.name, str(f.stat().st_size))


def da_doc(f: Path) -> bool:
    return SO.mot("SELECT id FROM noi_dung WHERE van_tay = ?",
                  _van_tay(f)) is not None


def ghi(f: Path, van_ban: str, giay_video: float, giay_chay: float,
        model: str) -> bool:
    vb = (van_ban or "").strip()
    if len(vb) < 200:
        return False
    vt = _van_tay(f)
    if SO.mot("SELECT id FROM noi_dung WHERE van_tay = ?", vt):
        return False
    with SO.ket_noi() as cn:
        cn.execute(
            "INSERT INTO noi_dung(tai_lieu_id,van_tay,url,kieu,cach,so_ky_tu,"
            "so_ky_tu_goc,van_ban,luc,da_boc) VALUES(NULL,?,?,?,?,?,?,?,?,0)",
            (vt, f.as_uri(), KIEU,
             "whisper:%s %.0fs/%.0fs" % (model, giay_chay, giay_video),
             len(vb), len(vb), vb, SO.bay_gio()))
    return True


def mot_video(f: Path, model=None, ten_model: str = MODEL,
              ngon_ngu: str | None = None, in_ra=print,
              gioi_han_giay: float = 0.0) -> dict:
    """`gioi_han_giay > 0` = chi nghe TUNG DAY phut dau roi dung.

    Chu du an 13/09: *"cac clip tren toi da xem het roi, cau khong can chay het
    dau, xem 1 phan nho de quan trong la test he thong thoi"*.

    Va do la cach LAY MAU dung cho mot phep thu day chuyen: 12 phut cua 10
    video khac nhau noi duoc nhieu hon 2 tieng cua mot video, vi cai dang do
    la **suat boc tren nhieu loai noi dung**, khong phai do sau cua mot bai.
    Toc do tren may nay la x3,2 thoi gian thuc (CPU, khong GPU) nen nghe het
    37,5 gio la ~12 gio - khong dang cho mot phep thu.
    """
    from faster_whisper import WhisperModel
    if model is None:
        model = WhisperModel(ten_model, device="cpu", compute_type="int8")
    t0 = time.time()
    try:
        segs, info = model.transcribe(str(f), language=ngon_ngu, beam_size=1,
                                      vad_filter=True)
        cac = []
        for s in segs:
            cac.append(s.text.strip())
            if gioi_han_giay and s.end >= gioi_han_giay:
                break
        vb = " ".join(cac)
    except Exception as e:
        return {"file": f.name, "loi": repr(e)[:200]}
    gi = time.time() - t0
    ok = ghi(f, vb, getattr(info, "duration", 0.0), gi, ten_model)
    return {"file": f.name, "ky_tu": len(vb), "giay_video": info.duration,
            "giay_chay": round(gi, 1),
            "nhanh_hon_thuc_te": round(info.duration / max(gi, 0.1), 1),
            "ghi": ok, "ngon_ngu": getattr(info, "language", "")}


def quet(thu_muc: str | Path, gioi_han: int = 0, ten_model: str = MODEL,
         ngon_ngu: str | None = "vi", in_ra=print) -> dict:
    from faster_whisper import WhisperModel
    from nhan import ngan_sach as NS
    with NS.xin("CPU_NANG", "doc video cuc bo", cho_giay=120, ram_gb=3.0):
        pass

    ds = [f for f in tim(thu_muc) if not da_doc(f)]
    if gioi_han:
        ds = ds[:gioi_han]
    tong_gio = sum(_thoi_luong(f) for f in ds) / 3600
    in_ra("%d video chua doc, %.1f gio" % (len(ds), tong_gio))
    if not ds:
        return {"video": 0}

    t0 = time.time()
    m = WhisperModel(ten_model, device="cpu", compute_type="int8")
    dem = {"video": 0, "ghi": 0, "loi": 0, "ky_tu": 0, "giay_video": 0.0}
    for i, f in enumerate(ds, 1):
        r = mot_video(f, m, ten_model, ngon_ngu, in_ra)
        dem["video"] += 1
        if r.get("loi"):
            dem["loi"] += 1
            in_ra("  %2d/%d  LOI  %s  %s" % (i, len(ds), f.name[:40], r["loi"]))
            continue
        dem["ghi"] += int(bool(r["ghi"]))
        dem["ky_tu"] += r["ky_tu"]
        dem["giay_video"] += r["giay_video"]
        in_ra("  %2d/%d  %-44s %6d ky tu  x%.1f  (%.0f/%.0f phut)"
              % (i, len(ds), f.name[:44], r["ky_tu"], r["nhanh_hon_thuc_te"],
                 (time.time() - t0) / 60, tong_gio * 60 / 3.2))
    dem["giay"] = round(time.time() - t0, 1)
    return dem


if __name__ == "__main__":
    import json
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    tm = a[0] if a else "F:/TeraBoxDownload"

    def lay(c, md):
        return sys.argv[sys.argv.index(c) + 1] if c in sys.argv else md
    if "--xem" in sys.argv:
        ds = tim(tm)
        chua = [f for f in ds if not da_doc(f)]
        print("%d file, %d chua doc, %.1f gio tong"
              % (len(ds), len(chua), sum(_thoi_luong(f) for f in ds) / 3600))
    else:
        print(json.dumps(quet(tm, int(lay("--so", "0")),
                              lay("--model", MODEL)), ensure_ascii=False))
