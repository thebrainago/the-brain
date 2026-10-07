# -*- coding: utf-8 -*-
"""chay.py - bo thuc thi cua he da tac tu: nhan KE HOACH (DAG viec, do Claude thiet ke) -> chay song song theo lop -> may cham -> sua toi da 2 vong
(vong cuoi leo thang model) -> phan bien cheo (model khac) -> bao cao cho Claude. Khong niem phong / khong ghi ngoai thu muc chay."""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from da_agent import cham as CH
from da_agent import llm

GOC = Path(__file__).resolve().parent.parent
LEO_THANG = {"re": "nhanh", "nhanh": "manh", "manh": "manh", "pro": "manh"}
HE_MAC_DINH = ("Ban la mot tac tu chuyen trach trong he da tac tu. Lam DUNG viec duoc giao, khong lan man, khong bia thong tin ngoai tai lieu duoc cap. "
               "Khi duoc yeu cau JSON thi tra DUNG mot JSON, khong markdown. Neu khong chac thi noi 'khong chac' thay vi doan.")


def _doc_tep(ds):
    return {p: (GOC / p).read_text(encoding="utf-8", errors="replace") for p in ds}


def _lam_mot(t, plan, kq, run, tep_all):
    try:
        return _lam_mot_that(t, plan, kq, run, tep_all)
    except Exception as e:                       # noqa: BLE001 - mot viec hong khong duoc lam sap ca ke hoach
        return {"id": t["id"], "ok": False, "du_lieu": None, "loi_cuoi": ["NGOAI LE: %s" % e], "lich_su": [], "phan_bien": None, "dong": 0}


def _lam_mot_that(t, plan, kq, run, tep_all):
    vai = t.get("vai", "re")
    he = HE_MAC_DINH + "\n" + plan.get("boi_canh", "") + ("\n" + t["he"] if t.get("he") else "")
    tep = {p: tep_all[p] for p in t.get("doc_tep", [])}
    phan_tep = "".join("=== TEP %s ===\n%s\n" % (p, s[:t.get("cat_tep", 60000)]) for p, s in tep.items())
    dep = "".join("=== KET QUA VIEC %s ===\n%s\n" % (d, json.dumps(kq[d]["du_lieu"], ensure_ascii=False)[:20000]) for d in t.get("dung", []))
    goc = phan_tep + dep + "--- VIEC ---\n" + t["prompt"]
    loi_cu, lich, dong = "", [], 0.0
    max_sua = t.get("max_sua", 2)
    for lan in range(max_sua + 1):
        ten_model = vai if lan < max_sua else t.get("leo_thang", LEO_THANG[vai])
        if lan == max_sua and max_sua == 0:
            ten_model = vai
        r = llm.goi(ten_model, he, goc + loi_cu, t.get("max_tokens", 1500), run / "so_chi.jsonl", "%s/%d" % (t["id"], lan))
        dong += r["dong"]
        du_lieu, loi = CH.cham(r["noi_dung"], t.get("cham", {}), {"tep_nguon": tep_all})
        if r["ket_thuc"] == "length":
            loi = loi + ["bi cat do het max_tokens"]
        lich.append({"lan": lan, "model": ten_model, "loi": loi})
        if not loi:
            break
        loi_cu = "\n\nBAN TRUOC KHONG DAT MAY CHAM: " + "; ".join(loi[:6]) + "\nSua lai va tra day du."
    ok = not loi
    pb = None
    if ok and t.get("phan_bien"):
        vp = (t["phan_bien"] if isinstance(t["phan_bien"], str) else "nhanh")
        yc = ("Ban la NGUOI PHAN BIEN doc lap. Duoi day la tai lieu, viec duoc giao va ket qua cua tac tu khac. Kiem tung muc ket qua co dung / co bia / co thieu khong. "
              'Tra DUNG mot JSON {"nhan_xet":[{"muc":"<so thu tu hoac ten>","phan_dinh":"dung|nghi_sai|khong_ro","ly_do":"..."}],"tong":"mot cau"}.\n'
              + phan_tep + "--- VIEC ---\n" + t["prompt"] + "\n--- KET QUA CAN PHAN BIEN ---\n" + json.dumps(du_lieu, ensure_ascii=False)[:20000])
        r2 = llm.goi(vp, HE_MAC_DINH, yc, 1500, run / "so_chi.jsonl", "%s/pb" % t["id"])
        dong += r2["dong"]
        pb, loi_pb = CH.cham_json(r2["noi_dung"], {"khoa": ["nhan_xet"]}, {})
        pb = pb if not loi_pb else {"loi": loi_pb}
    return {"id": t["id"], "ok": ok, "du_lieu": du_lieu if ok else None, "loi_cuoi": loi if not ok else [], "lich_su": lich, "phan_bien": pb, "dong": round(dong, 2)}


def chay(duong_plan: str, song_song: int = 6) -> Path:
    plan = json.loads(Path(duong_plan).read_text("utf-8"))
    run = GOC / "reports" / "da_agent" / ("%s_%s" % (plan["ten"], time.strftime("%Y%m%d_%H%M%S")))
    (run / "ket_qua").mkdir(parents=True)
    (run / "ke_hoach.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), "utf-8")
    tep_all = _doc_tep(sorted({p for t in plan["tasks"] for p in t.get("doc_tep", [])}))
    xong: dict = {}
    chua = {t["id"]: t for t in plan["tasks"]}
    while chua:
        san = [t for t in chua.values() if all(d in xong and xong[d]["ok"] for d in t.get("dung", []))]
        if not san:                                    # phu thuoc hong -> dung han, khong im lang
            for t in chua.values():
                xong[t["id"]] = {"id": t["id"], "ok": False, "du_lieu": None, "loi_cuoi": ["phu thuoc khong dat: %s" % t.get("dung")], "lich_su": [], "phan_bien": None, "dong": 0}
            break
        with ThreadPoolExecutor(song_song) as ex:
            for r in ex.map(lambda t: _lam_mot(t, plan, xong, run, tep_all), san):
                xong[r["id"]] = r
                (run / "ket_qua" / ("%s.json" % r["id"])).write_text(json.dumps(r, ensure_ascii=False, indent=1), "utf-8")
        for t in san:
            chua.pop(t["id"])
    bao_cao(plan, xong, run)
    return run


def bao_cao(plan, xong, run):
    tong = sum(r["dong"] for r in xong.values())
    d = ["# BAO CAO CHAY: %s" % plan["ten"], "", "Muc tieu: %s" % plan.get("muc_tieu", ""), "",
         "Tong chi: %.1f d · %d / %d viec dat may cham" % (tong, sum(1 for r in xong.values() if r["ok"]), len(xong)), "",
         "| Viec | May cham | Vong | Chi (d) | Phan bien |", "|---|---|---|---|---|"]
    for r in xong.values():
        pb = r["phan_bien"]
        nghi = sum(1 for x in (pb or {}).get("nhan_xet", []) if x.get("phan_dinh") != "dung") if pb and "nhan_xet" in pb else "-"
        d.append("| %s | %s | %d | %.1f | nghi/khong ro: %s |" % (r["id"], "DAT" if r["ok"] else "HONG", len(r["lich_su"]), r["dong"], nghi))
    d += ["", "Claude doc: ket_qua/<id>.json (du_lieu, lich_su, phan_bien). Hong may cham = CHUA_DO_DUOC, khong phai ket qua am."]
    (run / "BAO_CAO.md").write_text("\n".join(d), "utf-8")
    print("\n".join(d))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "chay":
        chay(sys.argv[2])
    else:
        print(__doc__)
