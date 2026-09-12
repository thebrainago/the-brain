# -*- coding: utf-8 -*-
"""_nap_viec_qwen.py - Nap viec THAT vao bang cua qwen.

Chu du an 12/09/2026: *"Qwen da nap day quota, vat no het co di"* +
*"Bat che do ultracode maxtoken"*.

Chay `q trang-thai` thi thay: **khong co viec chay duoc ngay** - 7 viec dang cho
hen gio, 4 viec can nguoi, con lai da xong. Tuc qwen dang ranh, va bat che do
ultracode cho mot bang viec rong thi khong nhanh hon duoc.

Va 55 de xuat qwen tu nghi ra phan lon tro toi **script khong ton tai**
(`_loc_hurst.py`, `_test_grid_ea.py`, `_buoc_tiep_theo.py`...). Duyet bua chi
sinh ra 55 dong loi.

Nen o day nap viec **co that**, va uu tien LAN LLM - do la thu vua duoc mo khoa
va la thu duy nhat qwen lam duoc ma may khong lam duoc:

  * LAN LLM  boc co che tu kho van ban. Do 12/09: `doc_hieu` (tat dinh) chi rut
             duoc **4 dieu kien tu 24.244 cau**. Khong phai bo doc hong - phan
             lon cau that su khong phai luat. Nhung phan CON LAI thi LLM doc
             duoc ma may khong. Cong van chan nhu cu, nen sinh de khong nguy.
  * LAN CPU  chay cac ban quet toan kho vua co toan hang moi (mau nen, 5 chi
             bao, 3 toan hang hinh hoc). Nhung toan hang do chua bao gio duoc
             quet tren ca kho.
  * LAN NHE  bao cao + do suc khoe.

TESTER van la 1 lan - may co MOT `terminal64.exe`, ngan sach khong mua duoc cai
thu hai (`nhan/khoa_tester.py`).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
BANG = LAB / "qwen" / "NHIEM_VU.json"

#: Viec nap them. `lenh` la danh sach doi so cho `python` (khuon cua bang).
VIEC_MOI = [
    {
        "ma": "L1_boc_llm_kho",
        "ten": "LLM boc co che tu kho van ban (200 ban doc moi luot)",
        "vi_sao": "doc_hieu tat dinh chi rut 4 dieu kien tu 24.244 cau - phan "
                  "lon cau khong phai luat, nhung phan con lai thi LLM doc duoc. "
                  "Quota vua thong 12/09, va cong van chan nhu cu nen sinh de "
                  "khong nguy.",
        "lan": "LLM", "uu_tien": 1, "ngay": 1, "toi_da_phut": 240,
        "lap": 20, "cach_nhau_gio": 0.5,
        "lenh": ["-c", "import sys;sys.path.insert(0,'.');"
                       "from nhan import boc_llm as B;"
                       "r=B.boc(gioi_han=200, luong=6, ghi_kho=True);"
                       "import json;print(json.dumps(r, ensure_ascii=False, default=str)[:2000])"],
        "cong": "boc duoc >= 1 co che moi vao kho",
    },
    {
        "ma": "Q1_to_hop_toan_hang_moi",
        "ten": "To hop D1+H4 voi toan hang MOI (mau nen, 5 chi bao, hinh hoc)",
        "vi_sao": "Mau nen, supertrend/keltner/donchian/ichimoku/heiken va "
                  "fibo/duong_xu_huong/goc deu them ngay 12/09 va CHUA BAO GIO "
                  "duoc quet tren ca kho.",
        "lan": "CPU", "uu_tien": 2, "ngay": 1, "toi_da_phut": 180,
        "lenh": ["-m", "nhan.to_hop", "D1", "H4", "--tien-trinh", "6"],
        "cong": "sinh reports/TO_HOP.json + bang tong ket",
    },
    {
        "ma": "Q2_suy_nguoc_H4",
        "ten": "Suy nguoc dau hieu truoc su kien tren H4",
        "vi_sao": "D1 da chay (126/154 ma cung dau ve bien dong no ra truoc cu "
                  "tang). Chua biet H4 co giong khong - va neu khac thi do la "
                  "mot phat hien ve KHUNG.",
        "lan": "CPU", "uu_tien": 3, "ngay": 1, "toi_da_phut": 120,
        "lenh": ["-m", "nhan.suy_nguoc", "quet", "H4", "6"],
        "cong": "sinh reports/SUY_NGUOC.json cho H4",
    },
    {
        "ma": "Q3_ho_so_song_H4",
        "ten": "Ho so song + moc magnetic tren H4 cho toan kho",
        "vi_sao": "Ho so song moi chay D1. Chan troi song cua H4 khac han, va "
                  "`to_hop` dung `tre_xac_nhan_bar` cua ho so nay.",
        "lan": "CPU", "uu_tien": 4, "ngay": 1, "toi_da_phut": 120,
        "lenh": ["-m", "nhan.ho_so_song", "quet", "H4", "6"],
        "cong": "sinh reports/HO_SO_SONG.json cho H4",
    },
    {
        "ma": "Q4_quan_tri_H4",
        "ten": "Quet ca hai ho quan tri tren H4",
        "vi_sao": "Chan troi giu lenh vua duoc sua (theo tung co che thay vi 60 "
                  "cung), nen moi so quan tri cu deu phai do lai.",
        "lan": "CPU", "uu_tien": 5, "ngay": 1, "toi_da_phut": 120,
        "lenh": ["_quet_quan_tri.py", "H4", "0", "6"],
        "cong": "sinh reports/QUET_QUAN_TRI_H4.json",
    },
    {
        "ma": "E1_evo_bao_xa",
        "ten": "EVO do suc khoe + bao ra Telegram khi tap van de DOI",
        "vi_sao": "Dich la VPS 24/7 nhieu thang khong nguoi truc. Bo giam sat "
                  "chi ghi vao reports/ thi trong khoang do bang khong co.",
        "lan": "NHE", "uu_tien": 2, "ngay": 1, "toi_da_phut": 15,
        "lap": 50, "cach_nhau_gio": 1.0,
        "lenh": ["-m", "nhan.evo", "--ghi", "--xa"],
        "cong": "sinh reports/EVO_SUC_KHOE.md",
    },
    {
        "ma": "V1_san_sang_vps",
        "ten": "Do lai do san sang chuyen VPS",
        "vi_sao": "Moi lan them module/phu thuoc la danh sach 'phai cai tren "
                  "VPS' doi. Do lai de no khong cu dan.",
        "lan": "NHE", "uu_tien": 6, "ngay": 1, "toi_da_phut": 15,
        "lap": 20, "cach_nhau_gio": 3.0,
        "lenh": ["-m", "nhan.san_sang_vps"],
        "cong": "sinh reports/SAN_SANG_VPS.md",
    },
]


def main(argv: list[str]) -> int:
    d = json.loads(BANG.read_text(encoding="utf-8-sig"))
    ds = d["viec"] if isinstance(d, dict) else d
    co = {v["ma"] for v in ds}
    them = 0
    for v in VIEC_MOI:
        if v["ma"] in co:
            # ghi de de sua duoc lenh ma khong sinh ban trung
            for i, cu in enumerate(ds):
                if cu["ma"] == v["ma"]:
                    ds[i] = v
                    break
            print("  cap nhat %s" % v["ma"])
        else:
            ds.append(v)
            them += 1
            print("  them    %s  [%s] %s" % (v["ma"], v["lan"], v["ten"][:52]))
    if isinstance(d, dict):
        d["viec"] = ds
    else:
        d = ds
    BANG.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print("\nbang viec: %d -> %d (them %d)" % (len(co), len(ds), them))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
