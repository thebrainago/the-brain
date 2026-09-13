# -*- coding: utf-8 -*-
"""_quet_bench_qt.py - quet ban do quan tri tren DA TAI SAN x DA ENGINE VAO.

So do he thong doi *"test da cap / da khung / da phuong phap quan li lenh"*. Mot
ma mot engine thi khong phan biet duoc "ho quan tri manh" voi "ho hop voi dung
cai engine do tren dung cai ma do".

ENGINE `deu_dan` (vao moi N nen, luan phien chieu) la PHEP THU PHAN CHUNG cua
ban do nay: no khong mang thong tin thi truong nao. Ho nao cai thien duoc CA
tren engine do la ho co tac dung THAT cua quan tri; ho nao chi sang len tren
engine donchian la ho an theo tuong tac voi entry.
"""
import json, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

MA = sys.argv[1].split(",") if len(sys.argv) > 1 else [
    "US500Cash", "EURUSD", "XAUUSD", "US100Cash"]
VAO = [("donchian", 0, 20), ("deu_dan", 1, 20), ("quay_ve", 2, 20)]

import chay_bench_quan_tri as B

tong = []
for ma in MA:
    for ten_vao, kieu, n in VAO:
        print(f"\n######## {ma} | vao={ten_vao} ########", flush=True)
        try:
            r = B.chay(ma, "H1", kieu, n, False, "2016.01.01", "2026.07.29", 1.0)
        except Exception as e:
            print("LOI:", repr(e)[:200], flush=True)
            continue
        # Ghi rieng tung to hop, neu khong thi file sau de len file truoc.
        f = B.LAB / "reports" / f"BENCH_QT_{ma}_H1_{ten_vao}.json"
        f.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        m = r.get("moc") or {}
        print("  %s | %s | moc sharpe %.2f | cao nguyen: %s"
              % (ma, ten_vao, m.get("sharpe", 0),
                 ", ".join(r.get("cao_nguyen_hon_moc") or []) or "-"), flush=True)
        tong.append({"ma": ma, "vao": ten_vao,
                     "trang_thai": r.get("trang_thai"),
                     "ly_do": r.get("ly_do", ""),
                     "moc_sharpe": m.get("sharpe"),
                     "moc_lenh": m.get("lenh"),
                     "cao_nguyen": r.get("cao_nguyen_hon_moc"),
                     "cai_gai": r.get("chi_cuc_dai_hon_moc"),
                     "cap_trung": r.get("cap_trung_nhau"),
                     "ho": {h: {"sh_max": k["sharpe"],
                                "sh_tv": k.get("sharpe_trung_vi"),
                                "ty_le": k.get("ty_le_o_hon_moc"),
                                "lai": k["lai"], "lenh": k["lenh"],
                                "dd": k["dd_pct"]}
                            for h, k in (r.get("tot_moi_ho") or {}).items()}})
        (B.LAB / "reports" / "QUET_BENCH_QT.json").write_text(
            json.dumps(tong, ensure_ascii=False, indent=1), encoding="utf-8")

print("\n==== XONG", len(tong), "luot ====")
