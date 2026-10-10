# -*- coding: utf-8 -*-
"""ea_tho_toi_uu - MT5 OPTIMIZE cho EA co file (EA cong khai .mq5 / .ex5, hoac EA lab dung lai tu lich su lenh).

Chu du an 09/10 va 10/10/2026: *"Tai sao ko chay che do optimize tren mt5, co phai nhanh hon khong? Ta chi gia lap khi khong
co san file mql5; co roi thi viec can la backtest dang optimize de tim input tot nhat + thu them co che quan li von / lenh."*
`ea_tho.tinh` chay tung diem bang MOT lan tester rieng (moi lan boot terminal + dong bo lich su); Optimize boot MOT lan va chay ca
luoi. Module nay chi them DUONG DI do, khong them tieu chi moi: cong van la `ea_tho.phan_quyet` (co lai sau phi VA maxDD < 80%),
cua so van la doan dong bang cua `ea_tho.ke_hoach`.

KY LUAT (chay nhanh khong phai la ly do de noi long):
 1. Chi quet tren doan `kham_pha`. MOI to hop la MOT phep thu: `so_phep_thu` = so to hop (chon tot nhat trong N to hop la mot cuc tri
    cua N lan rut, khong phai mot lan do).
 2. Diem dem di XAC NHAN la diem ON DINH nhat = lon nhat theo TRUNG VI lai cua chinh o do va cac o ke (loc trung vi tren be mat lai),
    khong phai dinh nhon. Dinh tho van duoc ghi (`dinh_tho`) de thay no cao hon diem duoc chon bao nhieu.
 3. Xac nhan DUNG diem do MOT lan tren doan `xac_nhan` qua `ea_tho.chay` (cong day du: chi phi do duoc, swap uoc, du lenh). KHONG BAO GIO
    cham `niem_phong` o day: do la quyet dinh rieng cua cloud. Buoc xac nhan chay lai duoc ma KHONG chay lai ca luoi (luoi da co trong so
    tay thi lay tu so tay) - don bi ngat giua chung thi giao lai la di tiep.
 4. Con so tung pass la TRUOC swap (tester khong ghi swap) va khong kem chat luong lich su tung pass: chi de XEP HANG va ve HINH DANG
    (cao nguyen / lo cho / cai gai), giong `chay_bench_quan_tri._cao_nguyen`. DAT chi den tu buoc xac nhan. Luoi / DCA giu lenh lau
    la loai bi nhieu nhat boi viec thieu swap, nen doc them `swap_nguon` / `lai_sau_swap` o buoc xac nhan.
 5. Chay tren may LOCAL (`UseRemote=0`, `UseCloud=0` trong .ini): EA cua nguoi khac khong bao gio roi khoi may.

CHUA CHAY TREN MT5 THAT cho duong EA-tho (cach ghi `Optimization=1` + `[TesterInputs]` va doc cot `Profit / Equity DD % / Trades` da chay
that trong `chay_tester_kho.py`, `chay_bench_quan_tri.py`). Ba diem phai xac nhan o lan chay dau tien o may nha (`tai_lieu/DAO_SAU_10_HE.md`
muc 3): (a) `ExpertParameters` (.set) mang khoang `||tu||buoc||den||Y` ma MT5 doc dung - neu khong, [TesterInputs] van giu cung noi dung;
(b) bang ra o `_bao_cao\\<ten>.xml`; (c) cot input mang TEN BIEN cua EA (nhu `InpP1` o script cu). Sai mot trong ba thi khong co pass nao hoac
thieu cot -> tra CHUA_DO_DUOC ha tang (khong an phep thu, khong ghi so tay) kem ly do, va bang goc duoc giu o `reports/chan_doan_tester/`
(gitignore) de doc lai - KHONG phai AM. Dia: moi agent cua tester co the chep lich su tick rieng - lan dau chay luoi nho va xem `C:`.
"""
from __future__ import annotations

import math
import re
import shutil
import statistics
import tempfile
import time
from itertools import product
from pathlib import Path

from nhan import ea_tho as E
from nhan import nc_so_tay as ST
from nhan import nc_thi_nghiem as TN

TO_HOP_TOI_THIEU = 4                  # duoi muc nay bang .xml nho hon nguong 2000 byte cua chay_mot va khong con la mot luoi
TO_HOP_TOI_DA = 400                   # luoi lon hon la quet mu; chia nho theo co che (HEPHAESTUS) thay vi tang tran
KHOA_TOI_DA = 4
GIA_TRI_TOI_DA_MOI_KHOA = 60
GIAY_NEN, GIAY_MOI_TO_HOP, HAN_GIAY_TOI_DA = 1800, 30, 14400
NGUONG_CAO_NGUYEN = 0.6               # ty le o DAT toan luoi: >= 0,6 cao nguyen, <= 0,2 cai gai (nhu chay_bench_quan_tri._cao_nguyen)
NGUONG_CAI_GAI = 0.2
TI_LE_PASS_TOI_THIEU = 0.9            # doc duoc it hon 90% so to hop mong doi = luoi bi cat / khoang bi MT5 bo qua
TOP = 10
COT = {"lai": "Profit", "dd": "Equity DD %", "lenh": "Trades"}
_KIEU_SO = frozenset("int uint long ulong short ushort char uchar double float bool".split())
_SO = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_NGHIN = re.compile(r"[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?")


def han_giay(n_to_hop: int) -> int:
    """Han chay tester cho ca luoi: 30 phut nen + 30 giay moi to hop, toi da 4 gio (tren tick that, moi pass la mot lan chay day du)."""
    return int(min(HAN_GIAY_TOI_DA, GIAY_NEN + GIAY_MOI_TO_HOP * int(n_to_hop)))


# ============================================================ 1. LUOI
def _num(x) -> float | None:
    """Chuoi so THAN -> float; bat ky thu gi khac (chu, 'true', '1,2,3', '1_000', nan, inf) -> None. Khong tu 'sua' van ban."""
    s = str(x).strip()
    if not _SO.fullmatch(s):
        return None
    v = float(s)
    return v if math.isfinite(v) else None


def _s(x) -> str:
    """So -> chu cho .set / .ini: nguyen khong co '.0', so le toi da 10 chu so thap phan, khong ky hieu khoa hoc."""
    x = float(x)
    if x == int(x) and abs(x) < 1e15:
        return str(int(x))
    return ("%.10f" % x).rstrip("0").rstrip(".")


def chuan_luoi(luoi) -> dict:
    """{ten: [tu, buoc, den] | {tu, buoc, den}} -> {ten: {tu, buoc, den, gia_tri:[...]}}. NEM ValueError neu khong dung.

    `den` tra ve = gia tri CUOI THAT CO (khong phai so nguoi dung go vao): khoang `||tu||buoc||den` ghi xuong .set va so to hop mong doi
    khong lech nhau. Moi input phai co >= 2 gia tri (1 gia tri thi la tham_so, khong phai luoi). Ten input di thang vao .set / .ini nen
    phai la ten bien hop le (khong xuong dong, khong `||`)."""
    if not isinstance(luoi, dict) or not luoi:
        raise ValueError("luoi phai la dict {ten_input: [tu, buoc, den]} khong rong")
    if len(luoi) > KHOA_TOI_DA:
        raise ValueError("luoi co %d input > toi da %d: quet nhieu chieu cung luc la quet mu, chon cac input co co che (hoac chia luoi)"
                         % (len(luoi), KHOA_TOI_DA))
    ra: dict = {}
    for k in sorted(luoi, key=str):
        v = luoi[k]
        if not isinstance(k, str) or not E._KHOA_SET.match(k):
            raise ValueError("ten input '%s' khong phai ten bien hop le" % str(k)[:40])
        if isinstance(v, dict):
            bo = [v.get("tu"), v.get("buoc"), v.get("den")]
        elif isinstance(v, (list, tuple)) and len(v) == 3:
            bo = list(v)
        else:
            raise ValueError("luoi['%s'] phai la [tu, buoc, den]" % k)
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(float(x)) for x in bo):
            raise ValueError("luoi['%s']: tu / buoc / den phai la so huu han" % k)
        tu, buoc, den = (float(x) for x in bo)
        if buoc <= 0:
            raise ValueError("luoi['%s']: buoc phai > 0" % k)
        if den <= tu:
            raise ValueError("luoi['%s']: den phai > tu (1 gia tri la tham_so, khong phai luoi)" % k)
        n = int(math.floor((den - tu) / buoc + 1e-9)) + 1
        if n > GIA_TRI_TOI_DA_MOI_KHOA:
            raise ValueError("luoi['%s']: %d gia tri > toi da %d (tang buoc)" % (k, n, GIA_TRI_TOI_DA_MOI_KHOA))
        if n < 2:
            raise ValueError("luoi['%s']: buoc %s lon hon khoang tu..den, chi con 1 gia tri" % (k, _s(buoc)))
        gia_tri = [round(tu + i * buoc, 10) for i in range(n)]
        ra[k] = {"tu": tu, "buoc": buoc, "den": gia_tri[-1], "gia_tri": gia_tri}
    return ra


def so_to_hop(lu: dict) -> int:
    return math.prod(len(g["gia_tri"]) for g in lu.values())


def van_ban_luoi(co_so: dict, lu: dict, so_khoa=frozenset()) -> str:
    """Van ban .set / [TesterInputs] cho Optimize. Input trong luoi: `K=v0||tu||buoc||den||Y` (v0 = gia tri nen neu nam tren luoi, khong thi
    `tu`). Input khac: giu NGUYEN gia tri nen; neu biet chac la so (`so_khoa`) thi viet dang day du `K=v||v||0||0||N` nhu cac script cu da
    chay that, con lai (chuoi, ten enum, khong ro kieu) viet tran `K=v` de khong lam hong gia tri."""
    dong = []
    for k in sorted(set(co_so) | set(lu)):
        if k in lu:
            g = lu[k]
            v0 = _num(co_so.get(k))
            if v0 is None or not any(abs(v0 - x) < 1e-9 for x in g["gia_tri"]):
                v0 = g["tu"]
            dong.append("%s=%s||%s||%s||%s||Y" % (k, _s(v0), _s(g["tu"]), _s(g["buoc"]), _s(g["den"])))
        else:
            v = str(co_so[k])
            x = _num(v) if k in so_khoa else None
            dong.append(("%s=%s||%s||0||0||N" % (k, _s(x), _s(x))) if x is not None else "%s=%s" % (k, v))
    return "\n".join(dong) + "\n"


# ============================================================ 2. BANG PASS
def _so(x) -> float | None:
    """So trong o bang MT5: bo dau cach / nbsp ('1 234.50') va dau phay NGHIN ('1,234.50'); hong -> None. Dau phay thap phan ('12,5')
    KHONG duoc doan: do thanh 125 la sai im lang, nen pass do bi bo va tinh vao ty le doc duoc."""
    s = str(x).replace(" ", "").replace("\xa0", "")
    if _NGHIN.fullmatch(s):
        s = s.replace(",", "")
    return _num(s)


def doc_bang(duong) -> list[dict]:
    """Bang Optimize cua MT5 (SpreadsheetML .xml, moi Row la mot pass) -> list[dict theo ten cot]. Dung lai `chay_tester_kho.doc_xml`."""
    from chay_tester_kho import doc_xml
    return doc_xml(Path(duong))


def thieu_cot(hang: list[dict], khoa: list[str] | None = None) -> list[str]:
    """Ten cot bat buoc (Profit / Equity DD % / Trades) va cot input cua luoi ma bang khong co (rong = du)."""
    can = list(COT.values()) + list(khoa or [])
    if not hang:
        return can
    return [c for c in can if c not in hang[0]]


def chuan_pass(hang: dict, khoa: list[str], von: float, ngay: int) -> dict | None:
    """Mot dong bang -> {gia_tri, lai, dd_pct, so_lenh, pf, cagr_pct, dat}, hoac None neu thieu so / sai kieu.

    `cagr_pct` = lai TRUOC swap quy ra %/nam (cung cong thuc `ea_tho.phan_quyet`). `dat` = lai > 0 VA maxDD < tran VA du lenh
    (cung `TN.LENH_TOI_THIEU`): tieu chi cua chu du an, chi la cong LOC pass, chua phai ket luan."""
    lai, dd, n = (_so(hang.get(COT[k])) for k in ("lai", "dd", "lenh"))
    if lai is None or dd is None or n is None:
        return None
    gia_tri = {}
    for k in khoa:
        x = _so(hang.get(k))
        if x is None:
            return None
        gia_tri[k] = x
    cagr = ((1.0 + lai / von) ** (365.25 / ngay) - 1.0) * 100.0 if von > 0 and ngay > 0 and 1.0 + lai / von > 0 else -100.0
    return {"gia_tri": gia_tri, "lai": round(lai, 2), "dd_pct": round(dd, 2), "so_lenh": int(n), "pf": _so(hang.get("Profit Factor")),
            "cagr_pct": round(cagr, 2), "dat": bool(lai > 0 and dd < E.DD_TRAN and n >= TN.LENH_TOI_THIEU)}


def _chi_so_o(p: dict, lu: dict) -> tuple | None:
    """Gia tri input cua pass -> chi so o trong luoi, hoac None neu nam ngoai luoi / lech buoc."""
    idx = []
    for k in sorted(lu):
        g = lu[k]
        x = (p["gia_tri"][k] - g["tu"]) / g["buoc"]
        i = round(x)
        if abs(x - i) > 0.02 or not 0 <= i < len(g["gia_tri"]):
            return None
        idx.append(i)
    return tuple(idx)


def _gon_pass(p: dict | None) -> dict | None:
    if p is None:
        return None
    return {"gia_tri": dict(p["gia_tri"]), "lai": p["lai"], "cagr_pct": p["cagr_pct"], "dd_pct": p["dd_pct"], "so_lenh": p["so_lenh"],
            "pf": p["pf"], "on_dinh": p.get("on_dinh"), "so_hang_xom": p.get("so_hang_xom"),
            "ty_le_hang_xom_dat": p.get("ty_le_hang_xom_dat")}


def phan_tich(passes: list[dict], lu: dict) -> dict:
    """Hinh dang luoi + diem ON DINH nhat. Thuan (khong tester, khong so tay).

    On dinh cua mot o DAT = trung vi `cagr_pct` cua o do va moi o ke (lech <= 1 buoc moi chieu, ke ca duong cheo) co trong bang: dinh nhon
    (o tot xung quanh la o lo) bi keo xuong, vai cao nguyen thi giu. Hoa -> lai cua chinh o do cao hon thang, roi lai tho (CAGR da lam tron 2 so le), roi DD thap hon. Gia tri input cua pass duoc
    DONG VAO dung gia tri luoi (0,3 chu khong phai 0,29999999) de diem chon co van tay sach khi xac nhan."""
    khoa = sorted(lu)
    o: dict = {}
    ngoai = lap = 0
    for p in passes:
        idx = _chi_so_o(p, lu)
        if idx is None:
            ngoai += 1
        elif idx in o:
            lap += 1
        else:
            p["gia_tri"] = {k: lu[k]["gia_tri"][i] for k, i in zip(khoa, idx)}
            o[idx] = p

    def hang_xom(idx):
        for d in product((-1, 0, 1), repeat=len(idx)):
            if any(d):
                q = tuple(a + b for a, b in zip(idx, d))
                if q in o:
                    yield o[q]
    for idx, p in o.items():
        if p["dat"]:
            hx = list(hang_xom(idx))
            p["on_dinh"] = round(statistics.median([p["cagr_pct"]] + [h["cagr_pct"] for h in hx]), 2)
            p["so_hang_xom"] = len(hx)
            p["ty_le_hang_xom_dat"] = round(sum(1 for h in hx if h["dat"]) / len(hx), 3) if hx else None
    dat = [p for p in o.values() if p["dat"]]
    cagr = sorted(p["cagr_pct"] for p in o.values())
    n = len(o)

    def vi(q: float) -> float | None:
        return round(cagr[min(n - 1, int(q * n))], 2) if n else None
    ty_le = len(dat) / n if n else 0.0
    hinh = ("khong_co_o_dat" if not dat else "cao_nguyen" if ty_le >= NGUONG_CAO_NGUYEN
            else "cai_gai" if ty_le <= NGUONG_CAI_GAI else "lo_cho")
    chon = max(dat, key=lambda p: (p["on_dinh"], p["cagr_pct"], p["lai"], -p["dd_pct"])) if dat else None      # CAGR lam tron 2 so: hoa -> lai tho, roi DD
    dinh = max(dat, key=lambda p: (p["cagr_pct"], p["lai"], -p["dd_pct"])) if dat else None
    return {"so_o": n, "ngoai_luoi": ngoai, "lap": lap, "so_dat": len(dat), "ty_le_dat": round(ty_le, 3), "hinh_dang": hinh,
            "cagr_phan_vi": {"min": vi(0.0), "p25": vi(0.25), "trung_vi": vi(0.5), "p75": vi(0.75), "max": vi(1.0)},
            "khoa": khoa, "dinh_tho": _gon_pass(dinh), "chon": _gon_pass(chon),
            "chenh_dinh_chon_pct": round(dinh["cagr_pct"] - chon["cagr_pct"], 2) if chon else None,
            "top": [_gon_pass(p) for p in sorted(dat, key=lambda p: (-p["on_dinh"], -p["cagr_pct"], -p["lai"], p["dd_pct"]))[:TOP]],
            "phang": bool(n > 1 and len({(p["lai"], p["so_lenh"]) for p in o.values()}) == 1),
            "khong_lenh": bool(n and all(p["so_lenh"] == 0 for p in o.values()))}


def bang_gon(passes: list[dict], khoa: list[str]) -> dict:
    """Bang pass gon de vao so tay (cho phep so voi mo phong sau nay): cot = input..., lai, dd_pct, so_lenh, dat."""
    return {"cot": list(khoa) + ["lai", "dd_pct", "so_lenh", "dat"],
            "hang": [[p["gia_tri"][k] for k in khoa] + [p["lai"], p["dd_pct"], p["so_lenh"], int(p["dat"])] for p in passes]}


# ============================================================ 3. CHAY
def _ha_tang(ly: str, **them) -> dict:
    return {"trang_thai": "CHUA_DO_DUOC", "ha_tang": True, "ly_do": ly, **them}


def _co_so(d: dict, tham_so: dict | None, bo_set: str | None, lu: dict):
    """-> (co_so {khoa: chu}, bs|None, ts|None, so_khoa, ly_do|None). Gia tri nen cua moi input: .set cua tac gia, hoac tham_so, hoac rong."""
    ts = E._chuan_ts(tham_so)
    kieu = {} if d.get("nhi_phan") else E.input_khai_bao(d["ma"])
    if bo_set:
        if ts:
            return None, None, None, None, ("bo_set va tham_so loai tru nhau (xem ea_tho_chay): doi input trong .set roi chay lai, "
                                            "hoac dung luoi de quet no")
        try:
            bs = E.doc_set(bo_set)
        except (OSError, ValueError) as e:
            return None, None, None, None, "khong doc duoc .set: %s" % str(e)[:160]
        thieu = sorted(k for k in lu if k not in bs["khoa"])
        if thieu and (d.get("nhi_phan") or any(k not in kieu for k in thieu)):
            return None, None, None, None, ("input trong luoi khong co trong .set cua tac gia%s: %s"
                                            % ("" if d.get("nhi_phan") else " va khong phai input khai trong ma EA", ", ".join(thieu[:6])))
        so_khoa = {k for k in bs["khoa"] if kieu.get(k) in _KIEU_SO or str(kieu.get(k, "")).upper().startswith("ENUM_")}
        return dict(bs["khoa"]), bs, None, so_khoa, None
    if d.get("nhi_phan"):
        return None, None, None, None, ("EA nhi phan (.ex5) khong co ma nguon nen khong doi chieu duoc ten input: can bo_set = file .set "
                                        "CUA TAC GIA (luoi chi doi cac khoa co trong .set do)")
    chong = sorted(set(ts) & set(lu))
    if chong:
        return None, None, None, None, "input vua trong tham_so vua trong luoi: %s (bo mot trong hai)" % ", ".join(chong[:6])
    for k, g in lu.items():
        for i in sorted({0, 1, len(g["gia_tri"]) - 1}):          # kieu nguyen / bool chi lo ra o 2 gia tri dau va cuoi
            ly = E.kiem_tham_so({k: g["gia_tri"][i]}, d["ma"])
            if ly:
                return None, None, None, None, "luoi: %s" % ly
    ly = E.kiem_tham_so(ts, d["ma"])
    if ly:
        return None, None, None, None, ly
    return {k: _s(v) for k, v in ts.items()}, None, ts, set(ts), None


def _set_xac_nhan(bs: dict, gia_tri: dict, thu_muc: Path) -> str:
    """.set cua tac gia voi cac input da chon: ghi vao thu muc TAM (khong vao git: .set cua nguoi la). Tra duong de truyen cho bo_set."""
    khoa = dict(bs["khoa"])
    for k, v in gia_tri.items():
        khoa[k] = _s(v)
    f = thu_muc / (str(bs["ten"])[:30] + "_toi_uu.set")
    f.write_text("".join("%s=%s\n" % (k, khoa[k]) for k in sorted(khoa)), encoding="utf-8")
    return str(f)


def _giu_bang_goc(bao_cao, vt: str) -> str:
    """Giu ban sao bang goc o `reports/chan_doan_tester/` (gitignore) khi khong doc duoc: khoi chay lai ca luoi chi de xem cot. '' neu khong chep duoc."""
    try:
        thu = Path(E.THU_MUC_CHAN_DOAN)
        thu.mkdir(parents=True, exist_ok=True)
        dich = thu / ("toi_uu_%s.xml" % vt)
        shutil.copyfile(str(bao_cao), str(dich))
        return " | bang goc giu o reports/chan_doan_tester/%s" % dich.name
    except OSError:
        return ""


def _chay_luoi(ea: str, d: dict, pl: dict | None, ma: str, khung: str, lu: dict, co_so: dict, bs, ts, so_khoa, gt_id, vong_id, kh: dict,
               cfg: dict, vt: str) -> dict:
    """MOT lan Optimize + doc bang + chon diem on dinh + ghi so tay. Tra `ra` (trang_thai DAT | AM, co `tn_id`) hoac ket qua ha tang."""
    n_to_hop = so_to_hop(lu)
    thieu = [] if d.get("nhi_phan") else E.tep_thieu(E.can_tep(d["ma"], E.sach(d["ma"])), cfg["tep_san"])
    if thieu:
        return _ha_tang("EA can tep may nay khong co: %s - %s" % (", ".join(thieu[:4]), E.LOI_KHAC_PHUC_TEP), thieu_tep=thieu)
    lenh = {"toi_uu": True, "van_tay": vt, "doan": "kham_pha", "ma": ma, "khung": khung, "gt_id": gt_id, "ea_ten": d["ten"], "ea_sha": d["sha"],
            "tham_so": {}, "cua_so": kh, "model": int(cfg["model"]), "von": cfg["von"],
            "viec": {"terminal": "", "ea": d["ten"], "nhan": "eo_" + vt[:10], "symbol": E.symbol_san(ma, cfg), "khung": khung, "tu": kh["tu"],
                     "den": kh["den"], "model": int(cfg["model"]), "von": int(cfg["von"]), "don_bay": int(cfg["don_bay"]),
                     "han_giay": han_giay(n_to_hop), "toi_uu": 1, "tieu_chi": 0, "tep_set_tho": van_ban_luoi(co_so, lu, so_khoa)}}
    if d.get("nhi_phan"):
        lenh["nhi_phan"] = {"sha": d["sha"], "dung_luong": d.get("dung_luong")}
    t0 = time.time()
    r = (E.CHAY_TESTER or E._chay_that)(lenh, d, cfg)
    if not r.get("xong"):
        return _ha_tang("tester khong ra bang pass: %s" % (r.get("loi") or "khong ro"))
    khoa = sorted(lu)
    try:
        hang = doc_bang(r["bao_cao"])
    except OSError as e:
        return _ha_tang("khong doc duoc bang pass: %s%s" % (str(e)[:160], _giu_bang_goc(r.get("bao_cao"), vt)))
    thieu_c = thieu_cot(hang, khoa)
    if thieu_c:
        return _ha_tang("bang pass thieu cot %s (co: %s) - ten cot khac tieng Anh / cot input khong mang ten bien / dinh dang la%s" % (
            ", ".join(thieu_c[:6]), ", ".join(list(hang[0])[:12]) if hang else "bang rong", _giu_bang_goc(r.get("bao_cao"), vt)))
    passes = [p for p in (chuan_pass(h, khoa, float(cfg["von"]), int(kh["ngay"])) for h in hang) if p is not None]
    toi_thieu = max(2, math.ceil(TI_LE_PASS_TOI_THIEU * n_to_hop - 1e-9))     # 22/25 = 88% < 90% bi tu choi; 23/25 qua
    if len(passes) < toi_thieu:
        return _ha_tang("chi %d/%d pass doc duoc (mong >= %d): MT5 co the da chay MOT lan (khong doc khoang ||..||Y trong .set), cat luoi, "
                        "hoac o so hong%s" % (len(passes), n_to_hop, toi_thieu, _giu_bang_goc(r.get("bao_cao"), vt)))
    pt = phan_tich(passes, lu)
    if pt["khong_lenh"]:
        return _ha_tang("TAT CA %d pass deu 0 lenh - hong MOI TRUONG (dang nhap / thieu lich su / ma sai ten / EA khong vao lenh), khong phai "
                        "ket qua chien luoc%s" % (pt["so_o"], _giu_bang_goc(r.get("bao_cao"), vt)))
    if pt["phang"]:
        return _ha_tang("moi pass cho CUNG lai va so lenh: input trong luoi khong tac dong len EA (sai ten / EA khong dung input do)%s"
                        % _giu_bang_goc(r.get("bao_cao"), vt))
    gt = gt_id if gt_id is not None else E.gia_thuyet_ea(d, ma, khung, pl)
    canh_bao: list[str] = []
    if pt["hinh_dang"] == "cai_gai":
        canh_bao.append("CAI GAI: chi %.0f%% to hop DAT - diem tot nhat co the la cuc tri cua %d lan rut, khong phai vung lai"
                        % (100 * pt["ty_le_dat"], n_to_hop))
    if pt["chon"] and (pt["chon"]["ty_le_hang_xom_dat"] or 0) < 0.5:
        canh_bao.append("diem chon co it hon mot nua o ke DAT (%s): vung lai hep, nhay voi input" % pt["chon"]["ty_le_hang_xom_dat"])
    if pt["ngoai_luoi"] or pt["lap"]:
        canh_bao.append("%d pass nam ngoai luoi / lech buoc, %d pass lap - doi chieu cot input voi luoi" % (pt["ngoai_luoi"], pt["lap"]))
    canh_bao.append("lai tung pass la TRUOC swap, khong co chat luong lich su tung pass: chi de xep hang + ve hinh dang")
    ra = {"trang_thai": "DAT" if pt["chon"] else "AM", "ma": ma, "khung": khung, "doan": "kham_pha", "ea": d["ten"], "ea_sha": d["sha"],
          "gt_id": gt, "luoi": {k: [g["tu"], g["buoc"], g["den"]] for k, g in lu.items()}, "so_to_hop": n_to_hop, "so_pass": len(passes),
          "cua_so": kh, "model": int(cfg["model"]), "von": cfg["von"],
          "so_phep_thu_dong_gia_thuyet": ST.dem_phep_thu(gt_id=gt, doan="kham_pha") + n_to_hop,
          "tong_quan": {k: pt[k] for k in ("so_o", "so_dat", "ty_le_dat", "hinh_dang", "cagr_phan_vi", "ngoai_luoi", "lap")},
          "dinh_tho": pt["dinh_tho"], "chon": pt["chon"], "chenh_dinh_chon_pct": pt["chenh_dinh_chon_pct"], "top": pt["top"],
          "canh_bao": canh_bao, "bang": bang_gon(passes, khoa), "xac_nhan": None}
    if bs:
        ra["bo_set"] = {"ten": bs["ten"], "sha": bs["sha"], "so_khoa": bs["n"]}
    ra["ly_do"] = ("%d/%d to hop co lai (truoc swap) va maxDD < %.0f%% tren kham_pha, hinh dang %s" % (pt["so_dat"], pt["so_o"], E.DD_TRAN, pt["hinh_dang"])
                   if pt["chon"] else "khong to hop nao co lai + maxDD < %.0f%% + du lenh tren kham_pha (%d to hop)" % (E.DD_TRAN, pt["so_o"]))
    dau_vao = {"ea_sha": d["sha"], "ea": d["ten"], "luoi": ra["luoi"], "tham_so_nen": ts or {}, "cua_so": kh, "model": int(cfg["model"]),
               "von": cfg["von"]}
    if bs:
        dau_vao["bo_set"] = {"ten": bs["ten"], "sha": bs["sha"]}
    tom_tat = "OPTIMIZE %s %s/%s: %d to hop, %d DAT (%s)%s" % (
        d["ten"], ma, khung, n_to_hop, pt["so_dat"], pt["hinh_dang"],
        (", chon %s -> %s%%/nam DD%s%%" % (pt["chon"]["gia_tri"], pt["chon"]["cagr_pct"], pt["chon"]["dd_pct"])) if pt["chon"] else "")
    ra["tn_id"] = ST.ghi_thi_nghiem("ea_tho_toi_uu", dau_vao, ra, ra["trang_thai"], vt, ma, khung, "kham_pha", gt_id=gt, so_phep_thu=n_to_hop,
                                    giay=time.time() - t0, vong_id=vong_id, tom_tat=tom_tat)
    ST.cap_nhat_gia_thuyet(gt, trang_thai="DANG_THU")
    return ra


def _xac_nhan(ra: dict, ea: str, ma: str, khung: str, ts, bs, vong_id) -> dict:
    """Xac nhan DUNG diem on dinh nhat MOT lan tren doan `xac_nhan` (qua `ea_tho.chay`: da co trong so tay thi tra tu so tay, khong chay lai)."""
    chon, gt = ra["chon"]["gia_tri"], ra["gt_id"]
    tam = None
    try:
        if bs:
            tam = Path(tempfile.mkdtemp(prefix="toi_uu_"))
            rx = E.chay(ea, ma, khung, "xac_nhan", None, gt, vong_id, bo_set=_set_xac_nhan(bs, chon, tam))
        else:
            rx = E.chay(ea, ma, khung, "xac_nhan", {**(ts or {}), **chon}, gt, vong_id)
    finally:
        if tam is not None:
            shutil.rmtree(tam, ignore_errors=True)
    ra = dict(ra)
    ra["xac_nhan"] = {"gia_tri": chon, **E._gon(rx)}
    ra["trang_thai"] = rx.get("trang_thai")
    ra["ly_do"] = "diem on dinh nhat tren kham_pha (%s) -> xac_nhan: %s" % (chon, rx.get("ly_do"))
    if rx.get("ha_tang"):
        ra["ha_tang"] = True
    if rx.get("tn_id") or ra["trang_thai"] in ("DAT", "AM"):
        ST.cap_nhat_gia_thuyet(gt, trang_thai="TRIEN_VONG" if ra["trang_thai"] == "DAT" else "DANG_THU")
    return ra


def toi_uu(ea: str, ma: str, khung: str, luoi: dict, tham_so: dict | None = None, bo_set: str | None = None,
           gt_id: int | None = None, xac_nhan: bool = True, vong_id: int | None = None) -> dict:
    """MOT lan MT5 Optimize tren `kham_pha`, chon diem ON DINH nhat, xac_nhan DUNG diem do mot lan. Xem docstring module (ky luat 1-5).

    `luoi` = {input: [tu, buoc, den]}; `tham_so` = gia tri nen cua input KHAC (EA co ma nguon); `bo_set` = .set cua tac gia lam gia tri
    nen (bat buoc voi .ex5; loai tru voi tham_so). Hong ha tang (khong co MT5, tester chet, bang rong / thieu cot / chi 1 pass / 0 lenh)
    tra CHUA_DO_DUOC `ha_tang`, KHONG ghi so tay, khong tieu phep thu. Goi lai cung doi so: luoi da co trong so tay thi KHONG chay lai,
    chi lam tiep buoc xac nhan neu chua xong."""
    try:
        lu = chuan_luoi(luoi)
        d = E.doc_ea(ea)
    except (ValueError, KeyError, OSError) as e:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": str(e)[:300]}
    ma, khung, cfg = str(ma).upper(), str(khung).upper(), E.cau_hinh()
    if khung not in E.KHUNG_HOP_LE:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "khung '%s' khong hop le (co %s)" % (khung, E.KHUNG_HOP_LE)}
    if gt_id is not None:
        try:
            co_gt = bool(ST.mot("SELECT id FROM gia_thuyet WHERE id=?", int(gt_id)))
        except (TypeError, ValueError):
            co_gt = False
        if not co_gt:
            return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "khong co gia thuyet id=%s trong so tay (de trong gt_id de tu tao)" % (gt_id,)}
    n_to_hop = so_to_hop(lu)
    if not TO_HOP_TOI_THIEU <= n_to_hop <= TO_HOP_TOI_DA:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "luoi co %d to hop, can %d..%d: thu hep khoang / tang buoc, hoac chia theo co che" %
                (n_to_hop, TO_HOP_TOI_THIEU, TO_HOP_TOI_DA)}
    pl = None
    if not d.get("nhi_phan"):
        pl = E.phan_loai(d["ma"], d["tieu_de"])
        if pl["loai"] != "CHIEN_LUOC":
            return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "EA khong phai chien luoc (%s)" % pl["loai"]}
    co_so, bs, ts, so_khoa, ly = _co_so(d, tham_so, bo_set, lu)
    if ly:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": ly}
    kh = E.ke_hoach(ma, khung, "kham_pha", cfg)
    if "tu" not in kh:
        return kh
    vt = ST.van_tay("ea_tho_toi_uu", d["sha"], ma, khung, (bs["sha"] if bs else ts), {k: [g["tu"], g["buoc"], g["den"]] for k, g in lu.items()},
                    kh["tu"], kh["den"], int(cfg["model"]), E._so_chuan(cfg["von"]))
    cu = ST.da_thu(vt)
    if cu and cu.get("ket_qua"):
        ra = dict(cu["ket_qua"])
        ra["tn_id"] = cu["id"]
        ra["tu_so_tay"] = "thi nghiem %s da chay y het - luoi lay tu so tay, KHONG chay lai, KHONG tinh them phep thu" % cu["id"]
    else:
        ra = _chay_luoi(ea, d, pl, ma, khung, lu, co_so, bs, ts, so_khoa, gt_id, vong_id, kh, cfg, vt)
        if ra.get("trang_thai") == "CHUA_DO_DUOC":
            return ra
    if not ra.get("chon"):
        return ra
    if not xac_nhan:
        ra["trang_thai"], ra["ly_do"] = "DANG_CHO_XAC_NHAN", "%s; chua xac_nhan" % ra.get("ly_do")
        return ra
    return _xac_nhan(ra, ea, ma, khung, ts, bs, vong_id)
