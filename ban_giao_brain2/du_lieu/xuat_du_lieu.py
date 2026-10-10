"""Xuat cac bang so co the ban giao cho brain2 (10/10/2026).

CHI de TRUY NGUON GOC cac file trong thu muc nay: script doc cac file cua kho the-brain
(reports/, viec/xong/, so_cai/nc/) nen chi chay duoc o goc kho the-brain, KHONG chay duoc o brain2.
Chi xuat so lieu TU TAY the-brain do duoc. Khong co ma / file cai dat / lenh tho / ten tac gia cua bot nguoi khac.
Chay lai: cd <goc kho the-brain> && python3 ban_giao_brain2/du_lieu/xuat_du_lieu.py
"""
import json, glob, csv, os, shutil, statistics as st, collections, math
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[2])
OUT = str(Path(__file__).resolve().parent)
os.makedirs(f"{OUT}/so_tay_nghien_cuu", exist_ok=True)

# ---------- 1. vung lai trong mau (+ 2 nhom doi chung) ----------
u = json.load(open(f"{ROOT}/reports/vong_lap/ung_vien.json", encoding="utf-8"))
cols = ["id", "nhom", "lop", "ma", "khung", "co_che", "o_lai", "o_quet", "ty_le_o_lai", "n_quet",
        "che_do", "kieu_lot", "buoc", "tp", "tran_tang", "he_so_lot", "cho_lui", "lot", "xac_nhan_ngoai_mau", "tham_so_json"]
with open(f"{OUT}/vung_lai_trong_mau.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(cols)
    for x in sorted(u, key=lambda x: (x["nhom"], x["ma"], x["khung"], x["id"])):
        a, b = ((x.get("o") or "").split("/") + ["", ""])[:2]
        ts = x.get("tham_so") or {}
        w.writerow([x["id"], x["nhom"], x["lop"], x["ma"], x["khung"], x["co_che"], a, b,
                    round(int(a) / int(b), 4) if a.isdigit() and b.isdigit() and int(b) else "",
                    x.get("n_quet", ""), ts.get("che_do", ""), ts.get("kieu_lot", ""), ts.get("buoc", ""),
                    ts.get("tp", ""), ts.get("tran_tang", ""), ts.get("he_so_lot", ""), ts.get("cho_lui", ""),
                    ts.get("lot", ""), "" if x.get("xac_nhan") is None else json.dumps(x["xac_nhan"], ensure_ascii=False),
                    json.dumps(ts, ensure_ascii=False, sort_keys=True)])
print("vung_lai:", len(u), collections.Counter(x["nhom"] for x in u))

# ---------- 2. 125 o hieu chuan engine <-> MT5 tester ----------
rep = {}
for p in sorted(glob.glob(f"{ROOT}/viec/xong/*.json")):
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    tm = ((d.get("bang_chung") or {}).get("tep_moi")) or {}
    for k, v in tm.items():
        if k.startswith("reports/hieu_chuan/") and k.endswith("_e3.json"):
            try:
                rep[os.path.basename(k)] = json.loads(v) if isinstance(v, str) else v
            except Exception:
                pass
print("hieu_chuan reports:", len(rep))

PK = ["che_do", "buoc", "tp", "tran_tang", "lot", "kieu_lot", "he_so_lot", "he_so_buoc", "tia_lenh", "bien_cap", "cho_lui", "chot_tien", "don_bay"]
hc_cols = ["ma", "khung", "tu", "den", "ngay", "model", "chat_luong_lich_su_pct", "von"] + PK + [
    "tester_lai_nam_pct", "tester_dd_pct", "tester_pf", "tester_so_lenh", "tester_swap_tien",
    "engine_lai_nam_pct", "engine_dd_pct", "engine_so_lenh", "engine_swap_tien", "engine_swap_nam_pct",
    "engine_hon_tester", "ty_le_engine_tren_tester", "lech_lai_pp", "lech_dd_pp", "lech_lenh_pct", "ket_luan", "tham_so_json"]
rows = []
for name, r in sorted(rep.items()):
    t, e, th = r["tester"], r["engine"], r.get("tham_so", {})
    cs = r["cua_so"]
    von = r.get("von") or 10000.0
    ngay = cs.get("ngay") or 1
    es = (e.get("thong_ke") or {}).get("swap")
    ts = (t.get("thong_ke") or {}).get("swap")
    tl, el = t.get("lai_nam_pct"), e.get("lai_nam_pct")
    row = {"ma": r["ma"], "khung": r["khung"], "tu": cs["tu"], "den": cs["den"], "ngay": ngay, "model": r.get("model"),
           "chat_luong_lich_su_pct": t.get("chat_luong_pct"), "von": von}
    for k in PK:
        row[k] = th.get(k, "")
    row.update({
        "tester_lai_nam_pct": round(tl, 3) if tl is not None else "",
        "tester_dd_pct": (t.get("dd") or {}).get("so_sanh_pct", ""),
        "tester_pf": t.get("pf", ""),
        "tester_so_lenh": (t.get("thong_ke") or {}).get("so_lenh_mo", ""),
        "tester_swap_tien": ts if ts is not None else "",
        "engine_lai_nam_pct": round(el, 3) if el is not None else "",
        "engine_dd_pct": round(e.get("dd_pct", 0), 3),
        "engine_so_lenh": (e.get("thong_ke") or {}).get("so_lenh_mo", ""),
        "engine_swap_tien": round(es, 2) if es is not None else "",
        "engine_swap_nam_pct": round(es / von / ngay * 365 * 100, 3) if es is not None else "",
        "engine_hon_tester": int(el > tl) if (el is not None and tl is not None) else "",
        "ty_le_engine_tren_tester": round(el / tl, 3) if (el is not None and tl and tl > 0) else "",
        "lech_lai_pp": (r.get("lech") or {}).get("lai_nam_pp", ""),
        "lech_dd_pp": (r.get("lech") or {}).get("dd_pp", ""),
        "lech_lenh_pct": (r.get("lech") or {}).get("lenh_pct", ""),
        "ket_luan": r.get("ket_luan", ""),
        "tham_so_json": json.dumps(th, ensure_ascii=False, sort_keys=True)})
    rows.append(row)
with open(f"{OUT}/hieu_chuan_125_o.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=hc_cols)
    w.writeheader()
    w.writerows(rows)

# ---------- thong ke tai lap duoc tu CSV ----------
def med(x):
    return round(st.median(x), 3) if x else None
def rank(v):
    s = sorted((x, i) for i, x in enumerate(v)); r = [0.0] * len(v); i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1][0] == s[i][0]:
            j += 1
        for k in range(i, j + 1):
            r[s[k][1]] = (i + j) / 2 + 1
        i = j + 1
    return r
def spearman(a, b):
    ra, rb = rank(a), rank(b); n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return round(num / den, 3) if den else None

N = len(rows)
spark = [r for r in rows if r["tia_lenh"] is True]
non = [r for r in rows if r["tia_lenh"] is not True]
def cnt_hon(rs): return sum(1 for r in rs if r["engine_hon_tester"] == 1)
rat = [r["ty_le_engine_tren_tester"] for r in spark if r["ty_le_engine_tren_tester"] != ""]
non_pp = [r["lech_lai_pp"] for r in non if r["lech_lai_pp"] != ""]
spark_pp = [r["lech_lai_pp"] for r in spark if r["lech_lai_pp"] != ""]
sw_zero = sum(1 for r in rows if r["tester_swap_tien"] == 0)
sw_e = [r["engine_swap_nam_pct"] for r in rows if r["engine_swap_nam_pct"] != ""]
top = sorted(rows, key=lambda r: -float(r["engine_lai_nam_pct"]))[:15]
toptest = sorted(rows, key=lambda r: -float(r["tester_lai_nam_pct"]))[:15]
key = lambda r: (r["ma"], r["khung"], r["tu"], r["den"], r["tham_so_json"])
overlap = len({key(r) for r in top} & {key(r) for r in toptest})
sp = spearman([float(r["engine_lai_nam_pct"]) for r in rows], [float(r["tester_lai_nam_pct"]) for r in rows])
bycell = collections.defaultdict(list)
for r in spark:
    bycell[(r["ma"], r["khung"])].append(r["lech_lai_pp"])
tom = {
    "so_o": N, "so_ma": sorted({r["ma"] for r in rows}), "so_khung": sorted({r["khung"] for r in rows}),
    "cua_so_tu": min(r["tu"] for r in rows), "cua_so_den": max(r["den"] for r in rows),
    "engine_hon_tester": f"{cnt_hon(rows)}/{N}",
    "tia_lenh_so_o": len(spark), "tia_lenh_engine_hon": f"{cnt_hon(spark)}/{len(spark)}",
    "tia_lenh_ty_le_trung_vi_(tester>0)": med(rat), "tia_lenh_ty_le_lon_nhat": max(rat) if rat else None, "tia_lenh_n_ty_le": len(rat),
    "tia_lenh_lech_lai_pp_trung_vi": med(spark_pp),
    "khong_tia_lenh_so_o": len(non), "khong_tia_lenh_engine_hon": f"{cnt_hon(non)}/{len(non)}",
    "khong_tia_lenh_lech_lai_pp_trung_vi": med(non_pp),
    "tester_swap_bang_0": f"{sw_zero}/{N}",
    "engine_swap_nam_pct_trung_vi": med(sw_e),
    "top15_engine_lai_nam_pct": [round(float(r["engine_lai_nam_pct"]), 1) for r in top],
    "top15_engine_ma_tester_lai_nam_pct": [round(float(r["tester_lai_nam_pct"]), 1) for r in top],
    "top15_trung_voi_top15_tester": f"{overlap}/15", "spearman_engine_vs_tester_lai": sp,
    "tester_lai_nam_duong": f"{sum(1 for r in rows if float(r['tester_lai_nam_pct'])>0)}/{N}",
    "tester_lai_nam_sau_swap_uoc_duong": None,
    "chat_luong_lich_su_pct_phan_bo": dict(collections.Counter(int(r['chat_luong_lich_su_pct']) if r['chat_luong_lich_su_pct'] not in ('', None) else -1 for r in rows)),
    "ghi_chu": "Tinh lai tu hieu_chuan_125_o.csv bang xuat_du_lieu.py; engine = nhan/luoi.py v3 (cuc_tri), tester = MT5 Strategy Tester model 0.",
}
# lai sau swap uoc (xap xi): tester_lai_nam - |engine_swap_nam_pct| (swap tren cung cau hinh)
sau = 0; n_pos = 0
for r in rows:
    tl = float(r["tester_lai_nam_pct"])
    if tl > 0:
        n_pos += 1
        if tl + float(r["engine_swap_nam_pct"] or 0) <= 0:
            sau += 1
tom["tester_duong_nhung_<=0_sau_swap_engine_uoc"] = f"{sau}/{n_pos}"
tom["tester_lai_nam_sau_swap_uoc_duong"] = f"{n_pos-sau}/{N}"
json.dump(tom, open(f"{OUT}/hieu_chuan_tom_tat.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(tom, ensure_ascii=False, indent=1))
print("theo ma/khung (tia lenh), lech trung vi:", {f"{k[0]}-{k[1]}": med(v) for k, v in sorted(bycell.items())})


# ---- thong ke bo sung: ben vung hon (loai o tester ~0, tach swap, rieng cua so lich su sach) ----
def tong_hop(rs, ten):
    sp_ = [r for r in rs if r["tia_lenh"] is True]
    nn_ = [r for r in rs if r["tia_lenh"] is not True]
    rat5 = [r["ty_le_engine_tren_tester"] for r in sp_ if r["ty_le_engine_tren_tester"] != "" and float(r["tester_lai_nam_pct"]) >= 5]
    rat1 = [r["ty_le_engine_tren_tester"] for r in sp_ if r["ty_le_engine_tren_tester"] != "" and float(r["tester_lai_nam_pct"]) >= 1]
    def exs(r): return float(r["lech_lai_pp"]) - float(r["engine_swap_nam_pct"] or 0)
    return {
        "so_o": len(rs),
        "engine_hon_tester": f"{sum(1 for r in rs if r['engine_hon_tester']==1)}/{len(rs)}",
        "tia_lenh": {"so_o": len(sp_), "engine_hon": f"{sum(1 for r in sp_ if r['engine_hon_tester']==1)}/{len(sp_)}",
                     "ty_le_trung_vi_khi_tester>=1%": med(rat1), "n_1": len(rat1), "ty_le_lon_nhat_khi_tester>=1%": (max(rat1) if rat1 else None),
                     "ty_le_trung_vi_khi_tester>=5%": med(rat5), "n": len(rat5), "ty_le_lon_nhat_khi_tester>=5%": (max(rat5) if rat5 else None),
                     "lech_pp_trung_vi": med([r["lech_lai_pp"] for r in sp_ if r["lech_lai_pp"] != ""]),
                     "lech_pp_trung_vi_khong_tinh_swap": med([exs(r) for r in sp_ if r["lech_lai_pp"] != ""])},
        "khong_tia_lenh": {"so_o": len(nn_), "engine_hon": f"{sum(1 for r in nn_ if r['engine_hon_tester']==1)}/{len(nn_)}",
                           "lech_pp_trung_vi": med([r["lech_lai_pp"] for r in nn_ if r["lech_lai_pp"] != ""]),
                           "lech_pp_trung_vi_khong_tinh_swap": med([exs(r) for r in nn_ if r["lech_lai_pp"] != ""])},
    }
tom["tat_ca"] = tong_hop(rows, "tat_ca")
tom["chi_lich_su_sach_100pct"] = tong_hop([r for r in rows if r["chat_luong_lich_su_pct"] == 100], "q100")
tom["chi_lich_su_51pct"] = tong_hop([r for r in rows if r["chat_luong_lich_su_pct"] == 51], "q51")
json.dump(tom, open(f"{OUT}/hieu_chuan_tom_tat.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k in ("tat_ca", "chi_lich_su_sach_100pct", "chi_lich_su_51pct"):
    print(k, json.dumps(tom[k], ensure_ascii=False))

# ---------- 3. doi chung nhieu (chuoi gia do tay tao) ----------
d = json.load(open(f"{ROOT}/reports/vong_lap/doi_chung_nhieu.json", encoding="utf-8"))
nh = {"cau_hinh": d["cau_hinh"], "khung": d["khung"], "phien_ban": d["phien_ban"], "tom_tat": d["tom_tat"], "kich_ban": {}}
for k, v in d["kich_ban"].items():
    nh["kich_ban"][k] = {kk: vv for kk, vv in v.items() if kk not in ("mau", "khop_bar")}
json.dump(nh, open(f"{OUT}/doi_chung_nhieu_tom_tat.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("doi_chung_nhieu_tom_tat.json bytes:", os.path.getsize(f"{OUT}/doi_chung_nhieu_tom_tat.json"))

# ---------- 4. so tay nghien cuu ----------
# Lam sach: bo khoa `ung_vien_dau` (ten tin hieu / EA cua nguoi khac) khoi `pham_vi` cua gia thuyet; giu ID so neu nam o noi khac.
# Danh sach ten cam (ten bot / tin hieu / tac gia cua nguoi khac) KHONG ghi vao kho cong khai: dua qua moi truong, vd
#   CAM_TEN="ten1,ten2" python3 ban_giao_brain2/du_lieu/xuat_du_lieu.py
CAM_TEN = tuple(t.strip() for t in os.environ.get("CAM_TEN", "").split(",") if t.strip())
for n in ("cau_hoi", "gia_thuyet", "thi_nghiem"):
    out_lines = []
    for line in open(f"{ROOT}/so_cai/nc/{n}.jsonl", encoding="utf-8"):
        if not line.strip():
            continue
        d = json.loads(line)
        pv = (d.get("r") or {}).get("pham_vi")
        if isinstance(pv, str) and "ung_vien_dau" in pv:
            o = json.loads(pv)
            o.pop("ung_vien_dau", None)
            d["r"]["pham_vi"] = json.dumps(o, ensure_ascii=False, sort_keys=True)
        out_lines.append(json.dumps(d, ensure_ascii=False, sort_keys=True))
    text = "\n".join(out_lines) + "\n"
    bad = [t for t in CAM_TEN if t in text]
    assert not bad, f"so tay {n} con ten nguoi khac: {bad}"
    with open(f"{OUT}/so_tay_nghien_cuu/{n}.jsonl", "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

# ---------- 5. 400 ho so tin hieu MQL5 (BO ten tac gia + BO cot symbol cu bi gan sai) va 31 nguoi thang song >= 2 nam ----------
L = json.load(open(f"{ROOT}/reports/LUAN_DAU_CHAN.json", encoding="utf-8"))
S = {x["id"]: x for x in json.load(open(f"{ROOT}/reports/signal_ho_so.json", encoding="utf-8"))}
kieu = {x["id"]: x for x in L["bang"]}
cols5 = ["id", "kieu", "ly_do_phan_loai", "song_ngay", "song_2_nam_tang_duong_dd_duoi_80", "so_lenh", "lenh_moi_tuan", "giu_phut", "thang_pct",
         "pf", "sharpe", "tai_dinh_pct", "dd_cong_bo_pct", "tang_truong_pct", "nhoi_khi_lo", "bac_tai", "lo_treo_dinh", "cat_sach",
         "tai_deu", "tai_trung_vi_pct", "lech_trai", "so_diem_tai"]
n31 = 0
with open(f"{OUT}/mql5_400_phan_loai.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(cols5)
    for sid, k in sorted(kieu.items()):
        x = S.get(sid, {})
        song = k.get("song_ngay") if k.get("song_ngay") is not None else x.get("song_ngay")
        dd = x.get("dd_pct", k.get("dd_pct")); tt = x.get("tang_truong_pct", k.get("tang_truong_pct"))
        c31 = int(bool(song is not None and song >= 730 and tt is not None and tt > 0 and dd is not None and dd < 80))
        n31 += c31
        w.writerow([sid, k["kieu"], k["ly_do"], "" if song is None else round(song, 1), c31, x.get("so_lenh", k.get("so_lenh", "")),
                    x.get("tuan", ""), x.get("giu_phut", ""), x.get("thang_pct", ""), x.get("pf", ""), x.get("sharpe", ""),
                    x.get("tai_dinh_pct", ""), "" if dd is None else dd, "" if tt is None else tt, x.get("nhoi_khi_lo", ""),
                    x.get("bac_tai", ""), x.get("lo_treo_dinh", ""), x.get("cat_sach", ""), x.get("tai_deu", ""),
                    x.get("tai_trung_vi_pct", ""), x.get("lech_trai", ""), x.get("so_diem_tai", "")])
print("mql5_400: so ho so", len(kieu), "| thoa song>=2n/tang>0/dd<80:", n31)

V = json.load(open(f"{ROOT}/viec/xong/link-ho-so-symbol.json", encoding="utf-8"))
V = json.loads(V["bang_chung"]["tep_moi"]["reports/nguoi_thang_symbol.json"])
with open(f"{OUT}/mql5_31_nguoi_thang.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "kieu", "song_ngay", "dd_cong_bo_pct", "tang_truong_pct", "so_lenh", "ma_chinh_da_sua", "ty_le_lenh_ma_chinh",
                "6_ma_dau_(ma:so_lenh)", "nhan_symbol_cu_dung", "ly_do_phan_loai"])
    for m in sorted(V["muc"], key=lambda m: m["id"]):
        k = kieu.get(m["id"], {}); x = S.get(m["id"], {})
        w.writerow([m["id"], k.get("kieu", ""), m["song_ngay"], x.get("dd_pct", ""), x.get("tang_truong_pct", ""), x.get("so_lenh", ""),
                    m["symbol_chinh"], m["ty_le_lenh"], ";".join(f'{s["chuan"]}:{s["lenh"]}' for s in m["symbol"]),
                    int(bool(m.get("nhan_cu_dung"))), k.get("ly_do", "")])
print("mql5_31:", len(V["muc"]), "kieu:", dict(collections.Counter(kieu.get(m["id"], {}).get("kieu", "?") for m in V["muc"])),
      "ma chinh:", V["dem_symbol_chinh"])

print("done")
