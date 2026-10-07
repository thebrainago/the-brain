# -*- coding: utf-8 -*-
"""nc_ho_so.py - cong cu nc `ho_so_bot`: HO SO CO CHE cua mot con bot tu LENH THAT + doi chieu bo .set cua tac gia.

Chu du an 04/10/2026: moi bot co chien luoc va cach quan tri khac nhau; the brain phai boc tach co che / yeu to dac sac cua tung con bot
de ap dung cheo. `nhan/ho_so_bot.py` do co che tu lich su lenh, `nhan/ho_so_set.py` doi tung tham so .set voi lenh that; module nay la
LOP CONG CU (LUAT SO 1: moi phep do di qua `b nc cc`):
  - doc duong dan AN TOAN: chi tep trong thu muc du an (model khong doc duoc tep tuy y tren may);
  - moi cap (tep lenh, bo .set) -> ho so + doi chieu; nhieu cap thi so sanh cac bo .set voi nhau (`so_sanh_bo_set`: tham so nao that su
    dieu khien hanh vi, khoi nao co o bot nay khong o bot kia);
  - ghi MOT dong so tay (`ho_so_bot`, doan 'ho_so', so_phep_thu 0: khong tieu phep thu, khong an FDR, khong vao 'thi nghiem tot nhat';
    cung van tay thi dung dong cu);
  - viet bao cao ASCII <= 38.000 ky tu / tep vao `reports/ho_so/` (bo chay o nha chi mang theo 40.000 ky tu moi tep).
Day KHONG phai phep thu y tuong: ho so MO TA bot da co, khong noi bot co lai hay khong. Gia tri cua no la `cong_thuc` (co che do duoc, thay
so duoc) va `mau_thuan` / `nut_an` (cho nao tac gia noi mot dang, lenh that cho thay dang khac) - nguyen lieu cua the phuong phap
(tai_lieu/CHUYEN_BOT_SANG_TAI_SAN_KHAC.md). Trang thai: DAT = ho so xong khong loi phep do; CHUA_DO_DUOC = co phep do loi / cap hong
(khong bao gio la AM).

    python b.py nc cc ho_so_bot '{"lenh":"reports/fixture/tester_vamge10k_kp_deals.csv.gz","bo_set":"reports/fixture/ccbsn305_vamge10k.set.txt","ma":"GOLD.i#"}'
"""
from __future__ import annotations

import hashlib
import re
import time
import unicodedata
from pathlib import Path

from nhan import nc_so_tay as ST

LAB = Path(__file__).resolve().parent.parent
THU_MUC = LAB / "reports" / "ho_so"
LOAI = "ho_so_bot"
DOAN = "ho_so"
TEP_TOI_DA = 38_000
TOI_DA_CAP = 6
_KHOA_CAP = ("lenh", "bo_set", "ten", "ma", "he_so_don_vi")


# ------------------------------------------------------------------------------------------------------------------ tien ich
def _ascii(s) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.replace("\u0111", "d").replace("\u0110", "D").encode("ascii", "replace").decode("ascii")


def _o(x) -> str:
    return " ".join(_ascii(x).replace("|", "/").split())


def _cat(s: str, n: int) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 3].rstrip() + "..."


def _duong(p, truong: str) -> Path:
    """Tep trong thu muc du an (tuong doi hoac tuyet doi); ngoai thu muc / khong co tep -> ValueError."""
    if not isinstance(p, str) or not p.strip():
        raise ValueError("`%s` phai la duong dan (chuoi) toi mot tep trong thu muc du an" % truong)
    goc = LAB.resolve()
    d = Path(p.strip())
    d = (d if d.is_absolute() else goc / d).resolve()
    try:
        d.relative_to(goc)
    except ValueError:
        raise ValueError("`%s` phai nam trong thu muc du an (%s); chep tep vao do roi goi lai" % (truong, goc.name)) from None
    if not d.is_file():
        raise ValueError("`%s`: khong thay tep %s" % (truong, d.relative_to(goc).as_posix()))
    return d


def _tuong_doi(d: Path) -> str:
    try:
        return d.resolve().relative_to(LAB.resolve()).as_posix()
    except ValueError:
        return d.name


def _ten_tu_tep(d: Path) -> str:
    t = re.sub(r"(\.(gz|csv|htm|html|txt|set))+$", "", d.name, flags=re.I)
    t = re.sub(r"[^A-Za-z0-9_-]+", "_", t).strip("_")[:60]
    return t or "bot"


def _ten_sach(t: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(t)).strip("_")[:60] or "bot"


def _sha(d: Path | None) -> str | None:
    return hashlib.sha1(d.read_bytes()).hexdigest()[:16] if d is not None else None


def _cat_tep(s: str) -> str:
    if len(s) <= TEP_TOI_DA:
        return s
    ghi = "\n\n(cat bot: bao cao dai hon %d ky tu; day du trong dong so tay)\n" % len(s)
    c = s[: TEP_TOI_DA - len(ghi)]
    return c[: c.rfind("\n")] + ghi if "\n" in c else c + ghi


def _viet(ten_tep: str, noi_dung: str) -> str:
    THU_MUC.mkdir(parents=True, exist_ok=True)
    p = THU_MUC / ten_tep
    p.write_text(_cat_tep(_ascii(noi_dung)), encoding="utf-8", newline="\n")
    return _tuong_doi(p)


# ------------------------------------------------------------------------------------------------------------------ bao cao
def _bao_cao_ho_so(ten: str, hs: dict) -> str:
    m = hs.get("mau") or {}
    L = ["# Ho so co che cua bot '%s' (do tu lenh that)" % ten, ""]
    L += ["- " + _o(t) for t in hs.get("bao_cao", [])]
    L += ["", "## Mau", "",
          "- %s lenh %s (%s lenh bao hiem tach rieng), %s chuoi, %s den %s; luoi thoi gian cua lich su %s giay" % (
              m.get("so_lenh"), _o(m.get("ma")), m.get("so_lenh_doi_ung_bo"), m.get("so_chuoi"), _o(m.get("tu")), _o(m.get("den")), m.get("tick_s"))]
    khoi = hs.get("khoi") or {}
    co = [(k, v) for k, v in khoi.items() if v.get("ket_luan") == "co"]
    L += ["", "## Co che DANG CHAY trong lenh that (%d khoi)" % len(co), ""]
    if co:
        L += ["| Khoi | Nhom | Do tin | Lenh that cho thay |", "|---|---|---|---|"]
        L += ["| %s (%s) | %s | %s | %s |" % (_o(v.get("ten")), k, _o(v.get("nhom")), v.get("do_tin"), _cat(_o(v.get("ly_do")), 320)) for k, v in co]
    else:
        L.append("(khong khoi nao)")
    ro = [(k, v) for k, v in khoi.items() if v.get("ket_luan") == "khong_ro"]
    if ro:
        L += ["", "## Chua ket luan duoc (co tiep xuc nhung bang chung khong du)", ""]
        L += ["- **%s** (%s): %s" % (_o(v.get("ten")), k, _cat(_o(v.get("ly_do")), 260)) for k, v in ro]
    khong = [v.get("ten") for v in khoi.values() if v.get("ket_luan") == "khong" and v.get("do_tin") in ("cao", "vua")]
    L += ["", "## Khong thay (da do, co tiep xuc, do tin vua tro len)", "",
          "- " + (_o("; ".join(str(x) for x in khong)) if khong else "(khong)")]
    kdd = [v.get("ten") for v in khoi.values() if v.get("ket_luan") == "khong_do_duoc"]
    L += ["", "## Lich su lenh KHONG cho do duoc (%d khoi: can duong gia / .set / ma nguon)" % len(kdd), "",
          "- " + (_o("; ".join(str(x) for x in kdd)) if kdd else "(khong)")]
    ts = hs.get("tham_so") or {}
    L += ["", "## Tham so do duoc", ""]
    if ts:
        L += ["| Tham so | Gia tri | Don vi | Khoi | Ghi chu |", "|---|---|---|---|---|"]
        L += ["| %s | %s | %s | %s | %s |" % (_o(k), _o(v.get("gia_tri")), _o(v.get("don_vi")), _o(v.get("khoi")), _cat(_o(v.get("ghi_chu")), 160))
              for k, v in ts.items()]
    else:
        L.append("(khong)")
    if hs.get("canh_bao"):
        L += ["", "## Luu y", ""] + ["- " + _cat(_o(t), 400) for t in hs["canh_bao"]]
    tk = hs.get("tong_ket") or {}
    if tk.get("phep_do_loi") or tk.get("khoi_thieu") or tk.get("khoi_la"):
        L += ["", "## Loi (ho so chua day du)", "",
              "- phep do loi: %s; khoi thieu: %s; khoi la: %s" % (_o(tk.get("phep_do_loi")), _o(tk.get("khoi_thieu")), _o(tk.get("khoi_la")))]
    return "\n".join(L) + "\n"


def _bao_cao_so_sanh(sc: dict) -> str:
    bo = sc.get("bo") or []
    L = ["# So sanh cac bo .set: %s" % ", ".join(_o(b) for b in bo), ""]
    L += ["- " + _o(t) for t in sc.get("tom_tat", [])]
    for ma, tieu_de in (("bang_chung", "Bang chung: doi khai bao keo theo doi hanh vi (moi dong deu khop)"),
                        ("khong_quyet_dinh", "Khong quyet dinh: cung khai bao nhung hanh vi khac (con yeu to khac)"),
                        ("khong_tac_dung", "Khong tac dung nhin thay: khac khai bao nhung cung hanh vi")):
        L += ["", "## " + tieu_de, ""]
        ds = sc.get(ma) or []
        if not ds:
            L.append("(khong co)")
            continue
        L += ["| Tham so | Do tin | " + " | ".join(_o(b) + ": khai / do" for b in bo) + " |", "|---|---|" + "---|" * len(bo)]
        for e in ds:
            theo = {x["bo"]: x for x in e["cac_bo"]}
            L.append("| %s | %s | %s |" % (_o(e["tham_so"]), e.get("do_tin", ""), " | ".join(
                "%s / %s" % (_o(theo[b]["khai"]) if b in theo else "-", _o(theo[b]["do"]) if b in theo else "-") for b in bo)))
    L += ["", "## Khoi co che co o bo nay, khong co o bo kia", ""]
    kd = sc.get("khoi_doi") or []
    if kd:
        L += ["| Khoi | Co o | Khong o | Tham so .set noi toi khoi (theo bo) |", "|---|---|---|---|"]
        for k in kd:
            ts = "; ".join("%s: %s" % (_o(b), ", ".join(_o(x.get("ten")) for x in (v or [])[:6]) or "-") for b, v in (k.get("tham_so_theo_bo") or {}).items())
            L.append("| %s (%s) | %s | %s | %s |" % (_o(k.get("ten") or k["khoi"]), k["khoi"], _o("/".join(k["co_o"])), _o("/".join(k["khong_o"])), _cat(ts, 300)))
    else:
        L.append("(khong co)")
    ch = sc.get("chua_du") or []
    L += ["", "## Chua du so do de so sanh: %d tham so" % len(ch), ""]
    L += ["- %s: %s" % (_o(e["tham_so"]), _o(e.get("vi_sao", ""))) for e in ch[:60]]
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------------------------------------------------------ ban gon
def _gon_cap(ten: str, d_lenh: Path, d_set: Path | None, hs: dict, r: dict | None) -> dict:
    khoi = hs.get("khoi") or {}
    tk = hs.get("tong_ket") or {}
    g = {"ten": ten, "lenh": _tuong_doi(d_lenh), "bo_set": _tuong_doi(d_set) if d_set else None,
         "mau": {k: (hs.get("mau") or {}).get(k) for k in ("ma", "so_lenh", "so_chuoi", "tu", "den", "tick_s", "so_lenh_doi_ung_bo")},
         "khoi_co": {k: v["do_tin"] for k, v in khoi.items() if v.get("ket_luan") == "co"},
         "khoi_khong_ro": [k for k, v in khoi.items() if v.get("ket_luan") == "khong_ro"],
         "so_khoi_khong_do_duoc": sum(1 for v in khoi.values() if v.get("ket_luan") == "khong_do_duoc"),
         "tham_so_do": {k: v.get("gia_tri") for k, v in (hs.get("tham_so") or {}).items()},
         "loi_phep_do": tk.get("phep_do_loi") or {}, "khoi_thieu": tk.get("khoi_thieu") or [], "khoi_la": tk.get("khoi_la") or [],
         "canh_bao": [_cat(t, 300) for t in (hs.get("canh_bao") or [])[:6]]}
    if r is not None:
        g["set"] = {"don_vi": r.get("don_vi"), "dem": r.get("dem"),
                    "mau_thuan": [{"ten": x["ten"], "khai": x["khai"], "do_tin": x["do_tin"], "ly_do": _cat(x["ly_do"], 300)} for x in r.get("mau_thuan", [])],
                    "nut_an": [{"khoi": x["khoi"], "ten": x.get("ten"), "do_tin": x["do_tin"]} for x in r.get("nut_an", [])],
                    "cong_thuc": r.get("cong_thuc", []), "kiem_lot": r.get("kiem_lot"), "canh_bao": r.get("canh_bao", [])[:6],
                    "loi": r.get("loi", []), "tom_tat": r.get("tom_tat", [])}
    return g


# ------------------------------------------------------------------------------------------------------------------ chay
def chay(lenh: str, bo_set: str | None = None, ten: str | None = None, ma: str | None = None, pip: float | None = None,
         hop_dong: float | None = None, von_dau: float | None = None, khung_phut: float | None = None, he_so_don_vi: float | None = None,
         them: list | None = None, ghi_bao_cao: bool = True, vong_id: int | None = None) -> dict:
    """Ho so co che cua mot bot (+ doi chieu bo .set). `them` = cac cap {lenh, bo_set, ten, ma, he_so_don_vi} nua de so sanh cac bo .set voi nhau.

    Tra: `trang_thai` (DAT / CHUA_DO_DUOC), `tn_id`, `tep_bao_cao`, `cac_bo` (ban gon tung cap), `so_sanh` (neu >= 2 bo .set), `tom_tat` (LAST: bo
    chay o nha chi giu 25 dong cuoi cua dau ra). Duong dan phai nam trong thu muc du an."""
    from nhan import ho_so_bot as HB
    from nhan import ho_so_set as HS
    t0 = time.time()
    cac = [{"lenh": lenh, "bo_set": bo_set, "ten": ten, "ma": ma, "he_so_don_vi": he_so_don_vi}]
    for x in them or []:
        if not isinstance(x, dict):
            raise ValueError("`them` la danh sach cac doi tuong {lenh, bo_set, ten, ma, he_so_don_vi}")
        la = sorted(set(x) - set(_KHOA_CAP))
        if la:
            raise ValueError("`them` co khoa la: %s (chi co %s)" % (la, ", ".join(_KHOA_CAP)))
        cac.append({k: x.get(k) for k in _KHOA_CAP})
    if len(cac) > TOI_DA_CAP:
        raise ValueError("toi da %d cap (lenh, .set) moi lan goi" % TOI_DA_CAP)
    # ---- duong dan + ten (kiem het truoc khi chay gi)
    da_dung: set[str] = set()
    for i, x in enumerate(cac):
        x["d_lenh"] = _duong(x["lenh"], "lenh" if i == 0 else "them[%d].lenh" % (i - 1))
        x["d_set"] = _duong(x["bo_set"], "bo_set" if i == 0 else "them[%d].bo_set" % (i - 1)) if x.get("bo_set") else None
        if x.get("he_so_don_vi") is not None:
            try:
                f = float(x["he_so_don_vi"])
            except (TypeError, ValueError):
                raise ValueError("he_so_don_vi phai la so duong huu han") from None
            if not (f > 0 and f < float("inf")):
                raise ValueError("he_so_don_vi phai la so duong huu han")
            x["he_so_don_vi"] = f
        t = _ten_sach(x["ten"]) if x.get("ten") else _ten_tu_tep(x["d_lenh"])
        goc, k = t, 2
        while t in da_dung:
            t, k = "%s_%d" % (goc, k), k + 1
        da_dung.add(t)
        x["ten"] = t
    # ---- chay tung cap (mot cap hong khong lam mat cac cap khac)
    gon, loi_cap, ket_hop, hs_ra, r_ra = [], [], [], {}, {}
    for x in cac:
        try:
            c = HB.chuan_bi(str(x["d_lenh"]), ma=x["ma"] or ma, pip=pip, hop_dong=hop_dong, von_dau=von_dau, khung_phut=khung_phut)
            hs = HB.ho_so(c, ten=x["ten"])
            r = HS.doi_chieu(hs, str(x["d_set"]), c=c, he_so_don_vi=x.get("he_so_don_vi"), ten=x["ten"] + "_set") if x["d_set"] else None
        except Exception as e:                                      # noqa: BLE001 - loi cua mot cap khong duoc nuot mat, cung khong duoc lam hong ca lan
            loi_cap.append({"ten": x["ten"], "loi": "%s: %s" % (type(e).__name__, _cat(_ascii(e), 300))})
            continue
        hs_ra[x["ten"]], r_ra[x["ten"]] = hs, r
        gon.append(_gon_cap(x["ten"], x["d_lenh"], x["d_set"], hs, r))
        tk = hs.get("tong_ket") or {}
        if tk.get("phep_do_loi") or tk.get("khoi_thieu") or tk.get("khoi_la") or (r or {}).get("loi"):
            ket_hop.append(x["ten"])
    so_sanh = None
    ds_set = [(n, r) for n, r in r_ra.items() if r is not None]
    if len(ds_set) >= 2:
        so_sanh = HS.so_sanh_bo_set(ds_set)
    # ---- bao cao
    tep: list[str] = []
    if ghi_bao_cao:
        for n, hs in hs_ra.items():
            tep.append(_viet("%s.md" % n, _bao_cao_ho_so(n, hs)))
            if r_ra[n] is not None:
                tep.append(_viet("%s_set.md" % n, HS.bao_cao_md(r_ra[n])))
        if so_sanh is not None:
            tep.append(_viet("so_sanh_%s.md" % "_".join(n for n, _ in ds_set)[:80], _bao_cao_so_sanh(so_sanh)))
    # ---- tom tat (3-8 dong moi cap)
    tt: list[str] = []
    for g in gon:
        hs = hs_ra[g["ten"]]
        tt.append("[%s] %s" % (g["ten"], _cat(_ascii((hs.get("bao_cao") or [""])[0]), 230)))
        if r_ra[g["ten"]] is not None:
            tt += ["  " + _cat(_ascii(s), 230) for s in (r_ra[g["ten"]].get("tom_tat") or [])[:3]]
    if so_sanh is not None:
        tt += [_cat(_ascii(s), 230) for s in (so_sanh.get("tom_tat") or [])[:3]]
    for e in loi_cap:
        tt.append("LOI cap %s: %s" % (e["ten"], e["loi"]))
    if ket_hop:
        tt.append("CHUA DAY DU: phep do loi / thieu khoi o %s (xem loi_phep_do)" % ", ".join(ket_hop))
    # ---- ket qua + so tay
    ok = bool(gon) and not loi_cap and not ket_hop
    ra: dict = {"trang_thai": "DAT" if ok else "CHUA_DO_DUOC", "tom_tat_ngan": tt[0] if tt else "khong co cap nao chay duoc"}
    if not ok:
        ra["ly_do"] = "cap hong: %s; ho so chua day du: %s" % ([e["ten"] for e in loi_cap] or "khong", ket_hop or "khong")
    ra["cac_bo"] = gon
    if loi_cap:
        ra["loi_cap"] = loi_cap
    if so_sanh is not None:
        ra["so_sanh"] = {k: so_sanh[k] for k in ("bo", "bang_chung", "khong_quyet_dinh", "khong_tac_dung", "khoi_doi", "tom_tat")}
    if tep:
        ra["tep_bao_cao"] = tep
    dau_vao = {"cap": [{"lenh": _tuong_doi(x["d_lenh"]), "bo_set": _tuong_doi(x["d_set"]) if x["d_set"] else None, "ten": x["ten"],
                        "ma": x["ma"] or ma, "he_so_don_vi": x.get("he_so_don_vi")} for x in cac],
               "pip": pip, "hop_dong": hop_dong, "von_dau": von_dau, "khung_phut": khung_phut}
    vt = ST.van_tay(LOAI, [[_sha(x["d_lenh"]), _sha(x["d_set"]), x["ma"] or ma, x.get("he_so_don_vi")] for x in cac], pip, hop_dong, von_dau, khung_phut,
                    HB.PHIEN_BAN, HS.PHIEN_BAN)
    cu = ST.da_thu(vt) if ok else {}
    if cu and cu.get("id"):
        ra["tn_id"], ra["tu_so_tay"] = cu["id"], "da co dong so tay %s (cung van tay)" % cu["id"]
    else:
        ra["tn_id"] = ST.ghi_thi_nghiem(LOAI, dau_vao, ra, ra["trang_thai"], vt, str((gon[0]["mau"]["ma"] if gon else (ma or ""))).upper(), "", DOAN,
                                        gt_id=None, so_phep_thu=0, giay=round(time.time() - t0, 2), vong_id=vong_id,
                                        tom_tat=_cat(_ascii(" | ".join(tt)), 590))
    ra["tom_tat"] = tt                                              # CUOI CUNG: bo chay o nha giu 25 dong cuoi cua dau ra
    return ra
