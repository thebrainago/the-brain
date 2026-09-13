# -*- coding: utf-8 -*-
"""_tong_bench_qt.py - TONG HOP ban do quan tri qua DA TAI SAN x DA ENGINE.

## CAU HOI MA FILE NAY TRA LOI

Mot bang rieng le noi duoc "ho X hon moc tren ma Y voi engine Z". Do chua phai
cau tra loi ma so do he thong doi - *"tet thu tung phuong phap quan li lenh
khac nhau de xem hieu qua thay doi ra sao"* - vi mot ho co the hon moc o mot
o don le hoan toan ngau nhien.

Ba cot quyet dinh, xep theo do dang tin TANG DAN:

    so_luot_cao_nguyen   ho hon moc ON DINH tren bao nhieu luot (ma x engine)
    tren_deu_dan         ho co hon moc tren engine VAO NGAU NHIEN khong
    do_ben               = so_luot_cao_nguyen / so_luot_do_duoc

`tren_deu_dan` la cot QUAN TRONG NHAT. Engine `deu_dan` vao moi N nen va luan
phien chieu - no khong mang mot mau thong tin thi truong nao. Mot ho cai thien
duoc CA tren engine do la mot ho co tac dung THAT cua quan tri vi the. Mot ho
chi sang len tren `donchian` hay `quay_ve` la ho an theo TUONG TAC voi entry,
va no se bien mat khi doi entry.

Day la phep thu phan chung cua ban do - tuong duong vai tro cua chuoi null
trong phan con lai cua lab, nhung o day null co san trong chinh EA nen khong
ton them mot duong ma nao.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
F = LAB / "reports" / "QUET_BENCH_QT.json"


def tong(duong: Path = F) -> dict:
    ds = json.loads(duong.read_text(encoding="utf-8"))
    ho_tat = sorted({h for d in ds for h in (d.get("ho") or {})})

    bo_qua = [d for d in ds if d.get("trang_thai") == "CHUA_DO_DUOC"
              or not (d.get("moc_lenh") or 0)]
    dung = [d for d in ds if d not in bo_qua]

    bang = {}
    for h in ho_tat:
        if h == "moc":
            continue
        cao, gai, do_duoc, deu_dan_cao, deu_dan_co = 0, 0, 0, 0, 0
        lai_hon, dd_hon = 0, 0
        for d in dung:
            if h not in (d.get("ho") or {}):
                continue
            do_duoc += 1
            la_cao = h in (d.get("cao_nguyen") or [])
            if la_cao:
                cao += 1
            elif h in (d.get("cai_gai") or []):
                gai += 1
            k = d["ho"][h]
            m = d["ho"].get("moc") or {}
            if k.get("lai", 0) > m.get("lai", 0):
                lai_hon += 1
            if k.get("dd", 99) < m.get("dd", 0):
                dd_hon += 1
            if d.get("vao") == "deu_dan":
                deu_dan_co += 1
                if la_cao:
                    deu_dan_cao += 1
        bang[h] = {
            "so_luot_do_duoc": do_duoc,
            "so_luot_cao_nguyen": cao,
            "so_luot_cai_gai": gai,
            "do_ben": round(cao / do_duoc, 3) if do_duoc else None,
            "luot_lai_hon_moc": lai_hon,
            "luot_dd_thap_hon_moc": dd_hon,
            "tren_deu_dan": f"{deu_dan_cao}/{deu_dan_co}",
            "qua_phan_chung": deu_dan_co > 0 and deu_dan_cao == deu_dan_co,
        }
    xep = dict(sorted(bang.items(),
                      key=lambda x: (-(x[1]["do_ben"] or 0),
                                     -x[1]["so_luot_cao_nguyen"])))
    ra = {"so_luot": len(ds), "dung_duoc": len(dung), "bo_qua": len(bo_qua),
          "luot_bo_qua": [{"ma": d["ma"], "vao": d["vao"],
                           "ly_do": d.get("ly_do") or "moc 0 lenh"}
                          for d in bo_qua],
          "bang": xep,
          "qua_phan_chung": [h for h, v in xep.items() if v["qua_phan_chung"]]}
    (LAB / "reports" / "TONG_BENCH_QT.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    return ra


def main() -> int:
    r = tong(Path(sys.argv[1]) if len(sys.argv) > 1 else F)
    print("%d luot chay | %d dung duoc | %d bo qua"
          % (r["so_luot"], r["dung_duoc"], r["bo_qua"]))
    for b in r["luot_bo_qua"]:
        print("   bo qua: %s/%s - %s" % (b["ma"], b["vao"], b["ly_do"]))
    print("\n%-14s %8s %8s %7s %9s %8s %10s"
          % ("ho", "cao_ngu", "cai_gai", "do_ben", "lai>moc", "DD<moc",
             "deu_dan"))
    for h, v in r["bang"].items():
        print("%-14s %4d/%-3d %8d %7.2f %5d/%-3d %4d/%-3d %10s%s"
              % (h, v["so_luot_cao_nguyen"], v["so_luot_do_duoc"],
                 v["so_luot_cai_gai"], v["do_ben"] or 0,
                 v["luot_lai_hon_moc"], v["so_luot_do_duoc"],
                 v["luot_dd_thap_hon_moc"], v["so_luot_do_duoc"],
                 v["tren_deu_dan"], "  <= QUA PHAN CHUNG"
                 if v["qua_phan_chung"] else ""))
    print("\nQUA PHEP THU PHAN CHUNG (cai thien ca tren entry ngau nhien):")
    print("   " + (", ".join(r["qua_phan_chung"]) or "khong ho nao"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
