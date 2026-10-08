# -*- coding: utf-8 -*-
"""cau_loi.py - PHAT HIEN DON "DAT" GIA: ma thoat 0 nhung dau ra bao LOI (chu du an 08/10/2026).

## Vi sao co file nay

`_cham` (cau_git.py) cham don kieu `chay_duoc` bang MA THOAT: 0 la `DAT`. Nhung cac cong cu `b nc cc ...`
bat loi ben trong roi in `{"loi": ...}` va van thoat 0. Do 08/10/2026 tren 1.585 don da xong:
23 don chay bang Python he thong KHONG co pyarrow (ImportError), 16 don doi ma hang hoa ma may khong co du lieu
(FileNotFoundError), 8 lan quet kho EA chet vi "het slot tester" / "dia con 3,5 GB" / "tester khong ra bao cao" -
TAT CA deu hien `DAT`. Ket qua: bao cao "xong" nhung khong do duoc gi, va khong ai sua vi tuong da xong.

Quy tac moi (ap dung cho kieu `chay_duoc`): thoat 0 MA dau ra (cuoi) co dau vet hong ha tang -> `CHUA_DO_DUOC`,
kem `bang_chung.loi_ha_tang` (nhan + dong bang chung) de may / cloud sua dung nguyen nhan roi cho chay lai.

Ba nhom nhan:
- `sua_duoc`   : thieu thu vien, tester ban, het dia -> may tu khoi phuc roi chay lai la ra ket qua (toi da 2 lan).
- `khong_chay_lai` : thieu du lieu gia (ma khong co trong data/), ngoai doan -> chay lai y het van hong,
  phai sua DON (doi ma / doi cua so), khong tu dua lai.
- `can_chan_doan`  : bien dich EA hong (thieu Include), tester chay xong ma KHONG ra bao cao -> phai co NGUOI/phien nha
  mo log tester ra xem; dua lai chi dot them gio tester (do 08/10: 24 don hieu_chuan_luoi chet o giay 92-95 vi
  `Include\\Trade\\Trade.mqh` khong thay trong thu muc du lieu cua terminal).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# (nhan, nhom, bieu thuc) - nhom: "sua_duoc" | "khong_chay_lai" | "can_chan_doan"   (THU TU QUAN TRONG: dong dau khop truoc)
DAU_VET = (
    ("thieu_thu_vien", "sua_duoc", r"ImportError|ModuleNotFoundError|Unable to find a usable engine"),
    ("tester_ban", "sua_duoc", r"TesterDangBan|het slot ranh"),
    ("het_dia", "sua_duoc", r"dia con [\d.,]+ ?GB ?<"),
    ("bien_dich_hong", "can_chan_doan", r"bien dich hong|error \d+: file '.*' not found"),
    # Nhan do LOG tester dat (`nhan/chan_doan_tester.py`, 08/10/2026): `... tester khong ra bao cao sau 94s [tester:mat_ket_noi] <dong log goc> ...`.
    # DUNG TRUOC dong chung `tester_khong_ra`. Tat ca `can_chan_doan`: dua lai chi dot them gio tester khi nguyen nhan chua duoc go.
    ("tester_chua_dang_nhap", "can_chan_doan", r"\[tester:chua_dang_nhap\]"),
    ("tester_mat_ket_noi", "can_chan_doan", r"\[tester:mat_ket_noi\]"),
    ("tester_thieu_lich_su", "can_chan_doan", r"\[tester:thieu_lich_su\]"),
    ("tester_khong_nap_ea", "can_chan_doan", r"\[tester:khong_nap_ea\]"),
    ("tester_ea_tu_choi", "can_chan_doan", r"\[tester:ea_tu_choi\]"),
    ("tester_het_bo_nho", "can_chan_doan", r"\[tester:het_bo_nho\]"),
    ("tester_agent_chet", "can_chan_doan", r"\[tester:agent_chet\]"),
    ("tester_khong_ra", "can_chan_doan", r"tester khong ra (?:bao cao|ket qua)"),
    ("thieu_du_lieu", "khong_chay_lai", r"FileNotFoundError|khong co du lieu cho \w+"),
    ("ngoai_doan", "khong_chay_lai", r"ngoai doan kham_pha|ngoai doan xac_nhan"),
    ("loi_ben_trong", "sua_duoc", r"loi khi chay:|Traceback \(most recent call last\)"),
)
_RX = [(n, g, re.compile(rx)) for n, g, rx in DAU_VET]
SO_DONG_XET = 40


def dau_vet(dong_cuoi: list | str | None, loi_cuoi: list | str | None = None) -> dict | None:
    """-> {"nhan","nhom","bang_chung"} cua dau vet hong DAU TIEN trong phan cuoi dau ra, hoac None."""
    def _ds(x):
        if not x:
            return []
        return x.splitlines() if isinstance(x, str) else [str(v) for v in x]
    dong = (_ds(dong_cuoi) + _ds(loi_cuoi))[-SO_DONG_XET:]
    for d in dong:
        for nhan, nhom, rx in _RX:
            if rx.search(d):
                return {"nhan": nhan, "nhom": nhom, "bang_chung": d.strip()[:240]}
    return None


def quet_ket_qua(thu_muc: Path) -> list[dict]:
    """Quet `viec/xong/*.json`: don mang `DAT` ma dau ra hong. -> [{ma, nhan, nhom, bang_chung}]"""
    ra = []
    for p in sorted(Path(thu_muc).glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        tt = d.get("trang_thai")
        bc = d.get("bang_chung") or {}
        if tt == "DAT":                                     # ket qua CU (truoc khi cau_git biet bat loi dau ra)
            if not bc.get("lenh") or [str(x) for x in bc.get("lenh", [])][1:3] == ["b.py", "tran-cpu"]:
                continue
            r = dau_vet(bc.get("dong_cuoi"), bc.get("loi_cuoi"))
        elif tt == "CHUA_DO_DUOC" and isinstance(bc.get("loi_ha_tang"), dict):   # ket qua MOI da ha bac
            r = bc["loi_ha_tang"]
        else:
            continue
        if r:
            ra.append({"ma": d.get("ma") or p.stem, "nhan": r["nhan"], "nhom": r["nhom"], "bang_chung": r["bang_chung"]})
    return ra


def dua_lai(goc: Path, toi_da_lan: int = 2) -> dict:
    """Don DAT gia thuoc nhom `sua_duoc`: chuyen file ket qua sang `viec/luu_tru/loi_ha_tang/` de don (van o `viec/cho/`)
    thanh DANG CHO va chay lai. Moi don dua lai toi da `toi_da_lan` lan (so lan ghi o `_so_lan.json`).
    -> {"dua_lai": [...], "khong_chay_lai": [...], "can_chan_doan": [...], "het_lan": [...]}"""
    goc = Path(goc)
    xong, kho = goc / "viec" / "xong", goc / "viec" / "luu_tru" / "loi_ha_tang"
    kho.mkdir(parents=True, exist_ok=True)
    so = kho / "_so_lan.json"
    try:
        dem = json.loads(so.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        dem = {}
    kq = {"dua_lai": [], "khong_chay_lai": [], "can_chan_doan": [], "het_lan": []}
    for r in quet_ket_qua(xong):
        if r["nhom"] in ("khong_chay_lai", "can_chan_doan"):
            kq[r["nhom"]].append(r["ma"])
            continue
        if dem.get(r["ma"], 0) >= toi_da_lan:
            kq["het_lan"].append(r["ma"])
            continue
        if not (goc / "viec" / "cho" / ("%s.json" % r["ma"])).exists():
            kq["khong_chay_lai"].append(r["ma"])      # khong con don goc de chay lai
            continue
        dem[r["ma"]] = dem.get(r["ma"], 0) + 1
        (xong / ("%s.json" % r["ma"])).replace(kho / ("%s.lan%d.json" % (r["ma"], dem[r["ma"]])))
        kq["dua_lai"].append(r["ma"])
    so.write_text(json.dumps(dem, ensure_ascii=False, indent=1), encoding="utf-8")
    return kq


if __name__ == "__main__":                                      # python -m qwen.cau_loi [quet|dua-lai]
    import sys
    goc = Path(__file__).resolve().parent.parent
    if len(sys.argv) > 1 and sys.argv[1] == "dua-lai":
        print(json.dumps(dua_lai(goc), ensure_ascii=False, indent=1))
    else:
        import collections
        r = quet_ket_qua(goc / "viec" / "xong")
        c = collections.Counter((x["nhom"], x["nhan"]) for x in r)
        print("don DAT gia: %d" % len(r))
        for (g, n), v in c.most_common():
            print("  %-15s %-16s %d" % (g, n, v))
