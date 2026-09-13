# -*- coding: utf-8 -*-
"""_thu_day_chuyen_video.py - PHEP THU DAY CHUYEN tren du lieu that.

Chu du an 13/09: *"cac clip tren toi da xem het roi, cau khong can chay het
dau, xem 1 phan nho de quan trong la test he thong thoi xong roi xoa di cho do
nang. Viec chinh van la hoan thien he thong."*

Nen day khong phai mot dot thu hoach - la mot phep DO cua ba chang:

    1 NGHE   video -> van ban   (`doc_video_cuc_bo`, whisper small, CPU)
    2 LOC    van ban -> co dau hieu luat khong (`boc_llm._diem_luat`)
    3 BOC    van ban -> co che   (`boc_llm.boc` -> LLM -> cong `them_co_che`)

Cai can biet la SUAT tung chang, khong phai so co che. 12 phut cua 12 video
khac loai do duoc suat tot hon 2 tieng cua mot video.
"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nhan import doc_video_cuc_bo as DV, boc_llm as BL

PHUT = 6
SO_VIDEO = 5

if __name__ == "__main__":
    ds = DV.tim("F:/TeraBoxDownload")
    # Lay MAU RAI DEU theo kich thuoc, khong lay 12 cai dau (toan file be xiu
    # kieu "Ghi Man hinh" - mot loai noi dung duy nhat).
    buoc = max(len(ds) // SO_VIDEO, 1)
    mau = [f for f in ds[::buoc]][:SO_VIDEO]
    mau = [f for f in mau if not DV.da_doc(f)]
    print("%d/%d video lam mau, nghe %d phut dau moi cai" % (len(mau), len(ds), PHUT), flush=True)

    from faster_whisper import WhisperModel
    m = WhisperModel("small", device="cpu", compute_type="int8")
    t0 = time.time(); ket = []
    for i, f in enumerate(mau, 1):
        r = DV.mot_video(f, m, "small", "vi", gioi_han_giay=PHUT * 60)
        r["diem_luat"] = BL._diem_luat(
            (dict(__import__("nhan.so", fromlist=["x"]).mot(
                "SELECT van_ban FROM noi_dung WHERE van_tay=?",
                DV._van_tay(f)) or {"van_ban": ""}))["van_ban"])
        ket.append(r)
        print("  %2d/%d %-42s %6s ky tu  diem_luat=%s  (%.0f phut)"
              % (i, len(mau), f.name[:42], r.get("ky_tu", "LOI"),
                 r.get("diem_luat"), (time.time() - t0) / 60), flush=True)

    ok = [r for r in ket if not r.get("loi")]
    ra = {"video_nghe": len(ok), "phut_moi_video": PHUT,
          "ky_tu_tong": sum(r["ky_tu"] for r in ok),
          "ghi_vao_kho": sum(1 for r in ok if r["ghi"]),
          "co_dau_hieu_luat": sum(1 for r in ok if (r.get("diem_luat") or 0) >= 1),
          "giay": round(time.time() - t0, 1), "chi_tiet": ket}
    Path("reports/THU_DAY_CHUYEN_VIDEO.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nCHANG 1 NGHE : %d video -> %d ky tu" % (ra["video_nghe"], ra["ky_tu_tong"]))
    print("CHANG 2 LOC  : %d/%d ban co dau hieu luat" % (ra["co_dau_hieu_luat"], ra["video_nghe"]))
    print("   (chang 3 BOC chay rieng bang _xao_toan_kho.py)")
