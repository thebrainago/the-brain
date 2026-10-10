# -*- coding: utf-8 -*-
"""vong_lap.py - NHAC TRUONG cua VONG LAP KHEP KIN: TIM -> BOC -> KIEM -> GIU -> AP DUNG -> vong sau (chu du an 10/10/2026).

Chu du an: "muc tieu cua the brain la VONG LAP lien tuc: tim nguon chien luoc/he thong chat luong -> boc tach co che -> kiem dinh ->
giu lai va chon loc co che hieu qua -> ap dung va bo sung vao cac vong ve sau. Viec ta dang lam chi la nhung module nho."

Do 10/10 tren `viec/xong` (1.573 viec, 105 gio may): 72% thoi gian may dem vao 1.246 luot QUET LUOI (kham pha, trong mau), 0 viec kiem
tren doan xac_nhan, 0 co che giu lai, 0 viec ap dung nguoc. 880 "vung lai" (cao nguyen) chua lan nao duoc kiem ngoai mau. Vong khong khep.

Module nay KHONG them mot phep do moi. No lam ba viec ma truoc do khong ai lam, chi tu `viec/` (git), khong LLM, khong du lieu gia, khong ghi nao.db:
  1. DO tung chang: bao nhieu viec, may chay bao nhieu giay, ra cai gi, hang doi sap chay cai gi (chay duoc / bi chan boi ma cu).
  2. NOI KIEM -> GIU: moi vung lai (cao nguyen) cua mot luot quet duoc dua sang `thu_luoi` tren doan XAC_NHAN (mo, khong tinh phep thu),
     co nhom DOI CHUNG (o tot nhat cua luot quet khong phai cao nguyen) de biet cao nguyen co du bao duoc gi khong.
  3. NAP NGUOC (AP DUNG): co che GIU LAI (qua xac_nhan o nhieu thi truong, hon nhom doi chung) -> don quet chuyen sang thi truong / khung
     lan can + yeu cau SEEKER di tim nguon cung loai.

Ranh gioi (CLAUDE.md): nhan DAT/QUA o day la NHAN CANH BAO tren engine mo phong, KHONG phai niem phong. Niem phong la quyet dinh co chu dich
cua cloud, mot lan cho moi khai bao da dong bang: module nay chi danh dau `SAN_SANG_NIEM_PHONG`, khong bao gio mo doan niem phong.

Dung:
    python3 -m nhan.vong_lap                 # bang diem + ghi reports/VONG_LAP.md (khong ra don)
    python3 -m nhan.vong_lap --giao [N]      # + ra toi da N don (mac dinh 240) vao viec/cho, KHONG push (nguoi goi commit)
    python3 -m nhan.vong_lap --in            # chi in, khong ghi gi
"""
from __future__ import annotations

import collections
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path

from qwen import cau_git as CG

LAB = Path(__file__).resolve().parent.parent

#: Cac chang cua vong. HA_TANG la chang PHU (do dung engine, don dep) - khong thuoc vong nhung an thoi gian may nen van do.
CHANG = ("TIM", "BOC", "KIEM", "GIU", "AP_DUNG", "HA_TANG")
TEN_CHANG = {"TIM": "tim nguon", "BOC": "boc tach co che", "KIEM": "kiem dinh", "GIU": "giu lai & chon loc",
             "AP_DUNG": "ap dung vao vong sau", "HA_TANG": "ha tang do luong"}
#: Ty le thoi gian may DE XUAT cho moi chang (chu du an sua duoc). KIEM chiem nhieu nhat nhung phai co ca kham pha lan xac nhan.
DICH = {"TIM": 0.10, "BOC": 0.10, "KIEM": 0.50, "GIU": 0.05, "AP_DUNG": 0.15, "HA_TANG": 0.10}

#: Tien to ten don do module nay ra. Dung tien to de nhan lai don cua minh ma khong can so luu rieng (stateless).
TT_XAC = "vl-xn-"        # kiem ngoai mau (engine may nha hien tai)
TT_XAC4 = "vl-xn4-"      # kiem lai bang engine moi (chi chay khi may nha da nap ma moi: can engine4)
TT_CHUYEN = "vl-tf-"     # quet chuyen sang thi truong / khung lan can
TT_SEEKER = "vl-sk-"     # yeu cau SEEKER tim nguon cung loai
TT_GHI = "vl-gh-"        # ghi hieu biet vao so tay nghien cuu

#: Cong cu `nc cc <ten>` -> chang. Cong cu la (khong co o day) rot vao HA_TANG de khong tinh nham vao vong.
_TIM = {"yeu_cau_seeker"}
_BOC = {"ho_so_tai_san", "ho_so_bot", "ho_so_set", "ho_so_symbol"}
_KHAM = {"quet_luoi", "thu_lo_co_che", "thu_co_che", "ea_tho_quet", "ea_tho_kham", "thu_hinh_dang", "mo_xe_lenh", "tim_quy_luat"}
_XAC = {"niem_phong_luoi", "xac_nhan", "niem_phong"}
_GIU = {"ghi_gia_thuyet", "ghi_hieu_biet"}

#: Lan CPU/TESTER... xem `qwen.cau_git.LAN`. Don kiem ngoai mau chi ton CPU vai giay: khong chiem slot tester.
LAN_XAC = "CPU"
UU_TIEN_XAC = 3
HAN_PHUT_XAC = 20.0
DON_TOI_DA_MAC_DINH = 240
TY_LE_DOI_CHUNG = 0.12    # ty le don moi dot danh cho o tot nhat cua luot quet KHONG phai cao nguyen (de co so sanh)
GIU_TOI_THIEU_THI_TRUONG = 3
GIU_TY_LE_QUA_TOI_THIEU = 0.5
GIU_HON_DOI_CHUNG = 0.10  # co che giu lai phai hon ty le qua cua nhom doi chung it nhat chung nay (khi nhom doi chung du lon)
DOI_CHUNG_TOI_THIEU = 10
TRAN_DD = 80.0            # tieu chi chu du an 25/09: co lai sau phi + maxDD < 80%
NAM_XAC_NHAN_MAC_DINH = 1.5
ENGINE_CU = 3             # ket qua khong khai engine = engine bar cu cua may nha (PHIEN_BAN_ENGINE 3), lac quan ~15-55% so voi EA
TY_LE_NGAU_NHIEN = 0.25   # moi 4 ung vien cao nguyen co 1 o NGAU NHIEN cung luot quet de lam doi chung ghep cap


# ---------------------------------------------------------------------------------------------- doc git

def _doc_json(p: Path) -> dict:
    try:
        d = json.loads(p.read_text(encoding="utf-8-sig"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _thu(goc: Path | None) -> Path:
    return (goc / "viec") if goc else CG.VIEC


def doc_xong(goc: Path | None = None) -> list[dict]:
    return [d for d in (_doc_json(p) for p in sorted((_thu(goc) / "xong").glob("*.json"))) if d.get("ma")]


def doc_cho(goc: Path | None = None) -> list[dict]:
    """Don CHUA co ket qua (qua `CG.don_dang_cho`: bo don da xong, don may khac dang lam)."""
    return CG.don_dang_cho(goc)


def kha_nang_biet(goc: Path | None = None) -> set[str]:
    """Hop cac `kha_nang` ma MOI nhip tim (ke ca nhip da cu) tung khai. May nha tat thi khong bo chay nao song, nhung tap nay van noi
    ro may nha CO THE lam gi: don khai `can` ngoai tap nay (engine4, ma-0810...) se KHONG chay cho toi khi nap ma moi."""
    ra: set[str] = set()
    for p in (_thu(goc) / "may").glob("*.json"):
        ra |= {str(x) for x in (_doc_json(p).get("kha_nang") or [])}
    return ra


# ------------------------------------------------------------------------------------------ doc lenh

def _bo_lenh(lenh) -> list[str]:
    return [str(x) for x in lenh] if isinstance(lenh, list) else []


def tach_lenh(lenh) -> tuple[str, dict]:
    """(ten cong cu, doi so JSON) tu `lenh` dang danh sach. `nc cc quet_luoi {..}` -> ("quet_luoi", {..}); `hepha qt` -> ("hepha qt", {}).

    Khong nhan ra -> ("?", {})."""
    t = _bo_lenh(lenh)
    if "b.py" not in t:
        if len(t) >= 3 and t[1] == "-m":
            return "-m " + t[2], {}
        return "?", {}
    r = t[t.index("b.py") + 1:]
    if not r:
        return "?", {}
    if r[0] == "nc" and len(r) >= 3 and r[1] == "cc":
        arg: dict = {}
        if len(r) >= 4:
            try:
                x = json.loads(r[3])
                arg = x if isinstance(x, dict) else {}
            except Exception:
                arg = {}
        return r[2], arg
    if r[0] == "nc" and len(r) >= 2:
        return "nc " + r[1], {}
    if len(r) >= 2 and not r[1].startswith(("-", "{", "http")):
        return "%s %s" % (r[0], r[1]), {}
    return r[0], {}


def chang_cua(cong_cu: str, doi_so: dict | None = None, ma_don: str = "") -> tuple[str, str]:
    """(chang, nhan_phu). nhan_phu cho KIEM: 'kham' (trong mau) | 'xac' (ngoai mau). Cho AP_DUNG: 'chuyen' | 'seeker'."""
    doi_so = doi_so or {}
    if ma_don.startswith((TT_XAC, TT_XAC4)):
        return "KIEM", "xac"
    if ma_don.startswith(TT_CHUYEN):
        return "AP_DUNG", "chuyen"
    if ma_don.startswith(TT_SEEKER):
        return "AP_DUNG", "seeker"
    if ma_don.startswith(TT_GHI):
        return "GIU", "ghi"
    if cong_cu.startswith(("dien-dan", "link")) or cong_cu in _TIM or cong_cu in ("seeker", "san-nguon"):
        return "TIM", ""
    if cong_cu in _BOC or cong_cu in ("hepha do", "hepha duc", "boc"):
        return "BOC", ""
    if cong_cu in _GIU:
        return "GIU", "ghi"
    if cong_cu == "thu_luoi":
        return "KIEM", ("xac" if doi_so.get("doan") == "xac_nhan" else "kham")
    if cong_cu == "ea_tho_chay":
        return "KIEM", ("xac" if doi_so.get("doan") in ("xac_nhan", "niem_phong") else "kham")
    if cong_cu in _XAC:
        return "KIEM", "xac"
    if cong_cu in _KHAM or cong_cu in ("hepha qt", "nc tho"):
        return "KIEM", "kham"
    return "HA_TANG", ""


def _giay(d: dict) -> float:
    try:
        return max(0.0, float((d.get("bang_chung") or {}).get("giay") or 0.0))
    except (TypeError, ValueError):
        return 0.0


# ---------------------------------------------------------------------------------- ung vien cao nguyen

_RE_LOP = re.compile(r'"ly_do":\s*"([A-Z_]+):\s*(\d+)/(\d+) o co lai(?:, tot nhat ([+-]?[\d.]+)%/nam o tran DD (\d+)%)?')
_RE_THAM_SO = re.compile(r'"tham_so_day_du":\s*(\{.*?\n\s*\})', re.S)
_RE_TOM_TAT = re.compile(r"^TOM_TAT\s+(\{.*\})\s*$", re.M)


def chuan_hoa_tham_so(ts: dict) -> dict:
    """So nguyen-dang-thuc (10.0) thanh so nguyen (10) de cung mot o khong thanh hai id."""
    ra = {}
    for k, v in sorted(ts.items()):
        if isinstance(v, float) and math.isfinite(v) and v == int(v):
            v = int(v)
        ra[str(k)] = v
    return ra


def id_ung_vien(ma: str, khung: str, tham_so: dict) -> str:
    s = json.dumps([str(ma).upper(), str(khung).upper(), chuan_hoa_tham_so(tham_so)], sort_keys=True, ensure_ascii=True)
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:10]


def _tom_tat_dong(txt: str) -> dict | None:
    """Dong `TOM_TAT {...}` cuoi cung (do `nc_cong_cu.main` in tu 10/10/2026). None neu khong co / hong."""
    ms = _RE_TOM_TAT.findall(txt)
    for s in reversed(ms):
        try:
            x = json.loads(s)
            if isinstance(x, dict):
                return x
        except Exception:
            continue
    return None


def doc_quet(d: dict) -> dict | None:
    """Mot ket qua `quet_luoi` (mot don da xong) -> ban ghi ung vien, hoac None neu khong du tham so de kiem lai.

    Nguon uu tien: dong TOM_TAT (ma moi); roi doan duoi `dong_cuoi` (ma cu, 25 dong - ~11% bi cat mat `tham_so_day_du`)."""
    b = d.get("bang_chung") or {}
    cc, arg = tach_lenh(b.get("lenh"))
    if cc != "quet_luoi" or not arg.get("ma") or not arg.get("khung"):
        return None
    txt = "\n".join(str(x) for x in (b.get("dong_cuoi") or []))
    lop = o_lai = o_tong = tran = None
    ts = None
    tt = _tom_tat_dong(txt)
    if tt and isinstance(tt.get("tham_so_day_du"), dict):
        ts = tt["tham_so_day_du"]
        m = _RE_LOP.search('"ly_do": "%s"' % str(tt.get("ly_do") or ""))
        if m:
            lop, o_lai, o_tong = m.group(1), int(m.group(2)), int(m.group(3))
            tran = float(m.group(4)) if m.group(4) else None
    if ts is None:
        m = _RE_LOP.search(txt)
        if m:
            lop, o_lai, o_tong = m.group(1), int(m.group(2)), int(m.group(3))
            tran = float(m.group(4)) if m.group(4) else None
        m2 = _RE_THAM_SO.search(txt)
        if m2:
            try:
                ts = json.loads(m2.group(1))
            except Exception:
                ts = None
    if not isinstance(ts, dict) or not ts or lop is None or not o_tong:
        return None
    ts = chuan_hoa_tham_so(ts)
    ma, khung = str(arg["ma"]).upper(), str(arg["khung"]).upper()
    luoi = arg.get("luoi") if isinstance(arg.get("luoi"), dict) else {}
    co_dinh = arg.get("co_dinh") if isinstance(arg.get("co_dinh"), dict) else {}
    return {"id": id_ung_vien(ma, khung, ts), "ma": ma, "khung": khung, "tham_so": ts, "von": arg.get("von", 10000),
            "lop": lop, "o_co_lai": o_lai, "o_tong": o_tong, "ty_le": round(o_lai / o_tong, 4), "tran_loi_pct": tran,
            "che_do": ts.get("che_do", "?"), "kieu_lot": ts.get("kieu_lot", "phang"),
            "co_che": co_che_khoa(ts), "nguon": [d.get("ma")], "luoi": luoi, "co_dinh": co_dinh}


def co_che_khoa(ts: dict) -> str:
    """Khoa CO CHE cua mot o luoi: kieu vao (mua|ban|hai_chieu) x kieu lot x co/khong cho gia lui. Khong gom thi truong (de dem
    bang chung XUYEN thi truong)."""
    return "%s|%s|%s" % (ts.get("che_do", "?"), ts.get("kieu_lot", "phang"), "lui" if ts.get("cho_lui") else "-")


def gom_ung_vien(xong: list[dict]) -> list[dict]:
    """Moi luot quet cho ra mot o tot nhat; trung (ma, khung, tham so) thi gop (dem `n_quet`, giu lop manh nhat)."""
    thu_tu = {"CAO_NGUYEN": 0, "HON_HOP": 1, "CAI_GAI": 2, "KHONG_CO_LAI": 3}
    gop: dict[str, dict] = {}
    for d in xong:
        u = doc_quet(d)
        if not u:
            continue
        c = gop.get(u["id"])
        if c is None:
            u["n_quet"] = 1
            gop[u["id"]] = u
            continue
        c["n_quet"] += 1
        c["nguon"].extend(u["nguon"])
        if (thu_tu.get(u["lop"], 9), -u["ty_le"]) < (thu_tu.get(c["lop"], 9), -c["ty_le"]):
            for k in ("lop", "o_co_lai", "o_tong", "ty_le", "tran_loi_pct"):
                c[k] = u[k]
    return sorted(gop.values(), key=lambda u: u["id"])


# ------------------------------------------------------------------------------------ ket qua xac nhan

def doc_xac_nhan(d: dict, nam_xac_nhan: float = NAM_XAC_NHAN_MAC_DINH) -> dict:
    """Ket qua mot don `thu_luoi` doan xac_nhan -> {ket_luan: QUA|RUOT|KHONG_DO_DUOC, ...}. Khong doan: thieu so lieu = KHONG_DO_DUOC.

    Nguon: dong TOM_TAT (ma moi, co trang_thai that); neu khong: khoi `chi_so_luoi` trong 25 dong cuoi (ma cu - mat `trang_thai`
    nen QUA = khong chay tai khoan + loi suat > 0 + du lenh uoc tinh). `ky_vong_o_tran_pct` = calmar x 80: UOC LUONG, khong phai do."""
    b = d.get("bang_chung") or {}
    txt = "\n".join(str(x) for x in (b.get("dong_cuoi") or []))
    ra = {"ket_luan": "KHONG_DO_DUOC", "nguon_so": None, "loi_suat_nam_pct": None, "maxdd_pct": None, "calmar": None,
          "so_lenh": None, "phien_ban_engine": ENGINE_CU, "tn_id": None, "hon_moc_pct": None, "ly_do": ""}
    mt = re.findall(r'"tn_id":\s*(\d+)', txt)
    if mt:
        ra["tn_id"] = int(mt[-1])
    if d.get("trang_thai") == "CHUA_DO_DUOC" and str(b.get("ma_thoat")) not in ("0", "None", ""):
        ra["ly_do"] = "don chet (ma thoat %s)" % b.get("ma_thoat")
        return ra
    tt = _tom_tat_dong(txt)
    if tt:
        tien = tt.get("tien") if isinstance(tt.get("tien"), dict) else {}
        cs = tt.get("chi_so_luoi") if isinstance(tt.get("chi_so_luoi"), dict) else {}
        lenh = tt.get("lenh") if isinstance(tt.get("lenh"), dict) else {}
        eng = tt.get("engine") if isinstance(tt.get("engine"), dict) else {}
        ra.update(nguon_so="TOM_TAT", loi_suat_nam_pct=_so(tien.get("loi_suat_nam_pct", cs.get("loi_suat_nam_pct"))),
                  maxdd_pct=_so(tien.get("maxdd_pct", cs.get("maxdd_pct"))), calmar=_so(cs.get("calmar")),
                  so_lenh=lenh.get("so_lenh"), phien_ban_engine=eng.get("phien_ban") or ENGINE_CU,
                  hon_moc_pct=_so(tien.get("hon_moc_pct")), ly_do=str(tt.get("ly_do") or "")[:160])
        if tt.get("tn_id") is not None:
            ra["tn_id"] = tt.get("tn_id")
        trang = tt.get("trang_thai")
        if trang == "DAT":
            ra["ket_luan"] = "QUA"
        elif trang == "AM":
            ra["ket_luan"] = "RUOT"
        return _bo_sung(ra, _so(tien.get("loi_suat_o_tran_pct")))
    m = re.search(r'"chi_so_luoi":\s*\{(.*?)\n\s*\}', txt, re.S)
    if not m:
        ra["ly_do"] = "khong tim thay khoi chi_so_luoi/TOM_TAT trong 25 dong cuoi"
        return ra
    try:
        cs = json.loads("{" + m.group(1) + "}")
    except Exception:
        ra["ly_do"] = "khoi chi_so_luoi hong"
        return ra
    mv = re.search(r'"phien_ban":\s*(\d+)', txt)
    ra.update(nguon_so="chi_so_luoi", loi_suat_nam_pct=_so(cs.get("loi_suat_nam_pct")), maxdd_pct=_so(cs.get("maxdd_pct")),
              calmar=_so(cs.get("calmar")), phien_ban_engine=int(mv.group(1)) if mv else ENGINE_CU)
    lenh_nam = _so(cs.get("lenh_nam"))
    if lenh_nam is not None:
        ra["so_lenh"] = int(round(lenh_nam * nam_xac_nhan))
    if ra["loi_suat_nam_pct"] is None:
        ra["ly_do"] = "thieu loi_suat_nam_pct"
        return ra
    if cs.get("chay"):
        ra["ket_luan"] = "RUOT"
        ra["ly_do"] = "chay tai khoan o lot thu"
    elif ra["loi_suat_nam_pct"] <= 0:
        ra["ket_luan"] = "RUOT"
        ra["ly_do"] = "khong co lai: %+.2f%%/nam" % ra["loi_suat_nam_pct"]
    elif ra["so_lenh"] is not None and ra["so_lenh"] < 10:
        ra["ly_do"] = "chi ~%d lenh (<10): chua du de ket luan" % ra["so_lenh"]
    else:
        ra["ket_luan"] = "QUA"
    return _bo_sung(ra)


def _so(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _bo_sung(ra: dict, o_tran: float | None = None) -> dict:
    """Them `ky_vong_o_tran_pct` khi QUA: so do that cua `thu_luoi` (`tien.loi_suat_o_tran_pct`, da tinh don bay) neu co; khong thi
    calmar x 80 (UOC LUONG: lot tuyen tinh toi tran DD, bo qua don bay / stop-out)."""
    c = ra.get("calmar")
    if ra.get("ket_luan") != "QUA":
        ra["ky_vong_o_tran_pct"] = None
    elif o_tran is not None:
        ra["ky_vong_o_tran_pct"] = round(o_tran, 1)
    else:
        ra["ky_vong_o_tran_pct"] = round(c * TRAN_DD, 1) if (c is not None and c > 0) else None
    return ra


def nam_xac_nhan_cua(ma: str, khung: str, goc: Path | None = None) -> float:
    """So nam cua doan xac_nhan (so_cai/doan.json) cho tinh so lenh uoc luong; thieu thi 1,5 nam."""
    p = (goc or LAB) / "so_cai" / "doan.json"
    try:
        x = json.loads(p.read_text(encoding="utf-8-sig")).get("%s|%s" % (ma, khung))
        a = time.mktime(time.strptime(x["t_xac_nhan"][:10], "%Y-%m-%d"))
        z = time.mktime(time.strptime(x["t_niem_phong"][:10], "%Y-%m-%d"))
        return max(0.1, (z - a) / (365.25 * 86400.0))
    except Exception:
        return NAM_XAC_NHAN_MAC_DINH


def xac_nhan_da_co(xong: list[dict], cho: list[dict], goc: Path | None = None) -> tuple[dict[str, list[dict]], dict[str, dict]]:
    """(da_xong, dang_cho): id ung vien -> [ket qua...] (moi engine mot ban) / {ma_don, can} cho MOI don thu_luoi doan xac_nhan
    (do module nay ra hay do tay). Id tinh tu (ma, khung, tham so) nen don tay trung o cung duoc nhan ra."""
    da: dict[str, list[dict]] = {}
    for d in xong:
        cc, arg = tach_lenh((d.get("bang_chung") or {}).get("lenh"))
        if cc == "thu_luoi" and arg.get("doan") == "xac_nhan" and isinstance(arg.get("tham_so"), dict):
            ma, khung = str(arg.get("ma", "")).upper(), str(arg.get("khung", "")).upper()
            kq = doc_xac_nhan(d, nam_xac_nhan_cua(ma, khung, goc))
            kq.update(ma_don=d.get("ma"), luc=d.get("luc"), giay=_giay(d))
            da.setdefault(id_ung_vien(ma, khung, arg["tham_so"]), []).append(kq)
    dc: dict[str, dict] = {}
    for d in cho:
        cc, arg = tach_lenh(d.get("lenh"))
        if cc == "thu_luoi" and arg.get("doan") == "xac_nhan" and isinstance(arg.get("tham_so"), dict):
            dc.setdefault(id_ung_vien(arg.get("ma", ""), arg.get("khung", ""), arg["tham_so"]),
                          {"ma_don": d.get("ma"), "can": list(d.get("can") or [])})
    return da, dc


def moi_nhat(kqs: list[dict] | None) -> dict | None:
    """Ket qua dang tin nhat trong cac ban: ket qua KET LUAN DUOC (QUA/RUOT) truoc, roi engine cao nhat, roi moi nhat. Engine moi nhin gan
    EA hon nen thay the engine cu; nhung mot don engine moi chet / khong do duoc khong duoc xoa ket luan da co cua engine cu."""
    if not kqs:
        return None
    return max(kqs, key=lambda k: (k.get("ket_luan") in ("QUA", "RUOT"), k.get("phien_ban_engine") or ENGINE_CU, str(k.get("luc") or "")))


# ----------------------------------------------------------------------------- doi chung & chon dot kiem

def nhom_cua(u: dict) -> str:
    """cao = o tot nhat cua luot quet CAO NGUYEN; doi = o tot nhat cua luot quet KHONG phai cao nguyen; ngau = o ngau nhien ghep cap."""
    if u["lop"] == "NGAU_NHIEN":
        return "ngau"
    return "cao" if u["lop"] == "CAO_NGUYEN" else "doi"


def _xen_ke(pool: list[dict], k: int) -> list[dict]:
    """k ung vien, xen ke qua tung tang (thi truong, khung, che do) de phu rong truoc khi di sau; trong tang: ty le o co lai giam dan."""
    tang: dict[tuple, list[dict]] = collections.defaultdict(list)
    for u in sorted(pool, key=lambda u: (-u["ty_le"], -(u.get("tran_loi_pct") or 0.0), u["id"])):
        tang[(u["ma"], u["khung"], u["che_do"])].append(u)
    khoa = sorted(tang)
    ra: list[dict] = []
    while len(ra) < k and any(tang[t] for t in khoa):
        for t in khoa:
            if tang[t] and len(ra) < k:
                ra.append(tang[t].pop(0))
    return ra


def sinh_ngau_nhien(u: dict) -> dict | None:
    """Mot o NGAU NHIEN trong CHINH luoi cua luot quet da cho ra `u` (cung truc, cung tham so co dinh) - doi chung ghep cap.

    Hat gieo tu id nen chay lai ra dung o do. Hoi: neu o tot nhat cua 3.000 o ma ngoai mau khong hon o ngau nhien cung luot quet,
    thi quet rong khong them gi so voi thu vai o - va thoi gian may nen dem vao chieu rong (thi truong, co che), khong vao chieu sau."""
    import random
    luoi = u.get("luoi") or {}
    if not luoi:
        return None
    rng = random.Random(int(hashlib.sha1(("ngau|" + u["id"]).encode("utf-8")).hexdigest()[:12], 16))
    ts = None
    for _ in range(8):
        x = dict(u.get("co_dinh") or {})
        for k in sorted(luoi):
            v = luoi[k]
            x[k] = v[rng.randrange(len(v))] if isinstance(v, (list, tuple)) and v else v
        x = chuan_hoa_tham_so(x)
        if id_ung_vien(u["ma"], u["khung"], x) != u["id"]:
            ts = x
            break
    if ts is None:
        return None
    return {"id": id_ung_vien(u["ma"], u["khung"], ts), "ma": u["ma"], "khung": u["khung"], "tham_so": ts, "von": u["von"],
            "lop": "NGAU_NHIEN", "o_co_lai": None, "o_tong": None, "ty_le": 0.0, "tran_loi_pct": None,
            "che_do": ts.get("che_do", "?"), "kieu_lot": ts.get("kieu_lot", "phang"), "co_che": co_che_khoa(ts),
            "nguon": [], "cha": u["id"], "n_quet": 0, "luoi": {}, "co_dinh": {}}


def chon_dot(ung_vien: list[dict], da_co: set[str], n: int, ty_le_doi_chung: float = TY_LE_DOI_CHUNG,
             ty_le_ngau: float = TY_LE_NGAU_NHIEN) -> list[dict]:
    """Toi da n ung vien CHUA co don: cao nguyen (xen ke) + nhom doi chung + o ngau nhien ghep cap voi 1/(1/ty_le_ngau) so cao nguyen."""
    cao = [u for u in ung_vien if u["lop"] == "CAO_NGUYEN" and u["id"] not in da_co]
    doi = [u for u in ung_vien if u["lop"] not in ("CAO_NGUYEN", "NGAU_NHIEN") and u["id"] not in da_co]
    buoc = max(1, int(round(1.0 / ty_le_ngau))) if ty_le_ngau > 0 else 0
    n_doi = min(len(doi), int(round(n * ty_le_doi_chung)))
    resto = max(0, n - n_doi)
    n_cao = 0                                                   # cao nhieu nhat sao cho cao + ngau ghep cap con nam trong `resto`
    while n_cao < len(cao) and (n_cao + 1) + ((n_cao + 1 + buoc - 1) // buoc if buoc else 0) <= resto:
        n_cao += 1
    chon_cao = _xen_ke(cao, n_cao)
    ra = list(chon_cao) + _xen_ke(doi, n_doi)
    if buoc:
        da_chon = {x["id"] for x in ra} | set(da_co)
        for j, u in enumerate(chon_cao):
            if j % buoc == 0 and len(ra) < n:
                g = sinh_ngau_nhien(u)
                if g and g["id"] not in da_chon:
                    ra.append(g)
                    da_chon.add(g["id"])
    if len(ra) < n and len(cao) > len(chon_cao):                # le do lam tron / o ngau trung: lap day bang cao nguyen tiep theo (xen ke on dinh theo tien to)
        them = _xen_ke(cao, min(len(cao), len(chon_cao) + (n - len(ra))))[len(chon_cao):]
        ra += them
    return ra[:n]


def _lenh_thu_luoi(u: dict) -> list[str]:
    arg = {"ma": u["ma"], "khung": u["khung"], "tham_so": chuan_hoa_tham_so(u["tham_so"]), "doan": "xac_nhan", "von": u.get("von", 10000)}
    return ["{py}", "b.py", "nc", "cc", "thu_luoi", json.dumps(arg, sort_keys=True, ensure_ascii=True)]


def _kiem_lenh(lenh: list[str]) -> None:
    """Chi xep don nam trong DANH SACH TRANG: don ngoai danh sach may nha se khong chay va hoi lai cloud (mat mot vong)."""
    from qwen import cau_trang as CT
    loi = CT.kiem_lenh(lenh)
    if loi:
        raise ValueError("lenh khong qua danh sach trang: %s" % loi)


def ra_don_xac_nhan(u: dict, goc: Path | None = None, engine4: bool = False) -> Path:
    """Don `thu_luoi` doan xac_nhan cho mot ung vien. engine4=True: kiem LAI bang engine moi (khai `can` engine4: may nha chua nap ma moi
    thi don nam yen, khong chay nham)."""
    lenh = _lenh_thu_luoi(u)
    _kiem_lenh(lenh)
    g = nhom_cua(u)
    ten = {"cao": "vung CAO NGUYEN %d/%d o co lai o kham_pha" % (u["o_co_lai"] or 0, u["o_tong"] or 0) if u.get("o_tong") else "vung cao nguyen",
           "doi": "DOI CHUNG: o tot nhat cua luot quet %s (khong phai cao nguyen)" % u["lop"],
           "ngau": "DOI CHUNG NGAU NHIEN: o bat ky trong luoi cua luot quet cua %s" % u.get("cha", "?")}[g]
    muc_tieu = "KIEM NGOAI MAU (vong lap) %s %s %s: %s - co lai tren xac_nhan khong? (xac_nhan khong tinh phep thu)" % (
        u["ma"], u["khung"], u["che_do"], ten)
    return CG.ra_don((TT_XAC4 if engine4 else TT_XAC) + u["id"], muc_tieu, lenh=lenh, lan=LAN_XAC, uu_tien=UU_TIEN_XAC,
                     han_phut=HAN_PHUT_XAC, cong={"kieu": "chay_duoc"}, goc=goc,
                     them={"can": ["engine4"] if engine4 else None,
                           "vi_sao": "vong lap khep kin: noi chang KIEM (trong mau) voi chang GIU (ngoai mau) - nhom %s" % g})


# ------------------------------------------------------------------------------------- gom CO CHE & GIU

def ty_le_qua(c: dict) -> float | None:
    n = c["qua"] + c["ruot"]
    return round(c["qua"] / n, 4) if n else None


def gom_co_che(ung_vien: list[dict], kq: dict[str, dict]) -> dict:
    """Gom ket qua xac_nhan thanh (a) ba nhom (cao nguyen / doi chung / ngau nhien) va (b) tung CO CHE (che_do x kieu_lot x cho_lui).

    NHAN, khong phai cong chan (CLAUDE.md LUAT SO 0): GIU = qua xac_nhan o >= 3 thi truong, >= 50% so ung vien co ket luan, >= 5 ket luan.
    `so_voi_nen`: HON_NEN neu hon nhom doi chung gop >= 10 diem % (can >= 10 doi chung), NGANG_NEN neu khong - ngang nen nghia la co che
    do ra tien nhu moi o khac cua cung luot quet (van la tien, nhung la 'luoi tren cap nay luc nay', chua phai 'luot chon co ich')."""
    nhom = {g: {"n": 0, "qua": 0, "ruot": 0, "khong_do_duoc": 0} for g in ("cao", "doi", "ngau")}
    cm: dict[str, dict] = {}
    for u in ung_vien:
        r = kq.get(u["id"])
        if not r:
            continue
        g = nhom_cua(u)
        k = {"QUA": "qua", "RUOT": "ruot"}.get(r["ket_luan"], "khong_do_duoc")
        nhom[g]["n"] += 1
        nhom[g][k] += 1
        if g != "cao":
            continue
        m = cm.setdefault(u["co_che"], {"co_che": u["co_che"], "n": 0, "qua": 0, "ruot": 0, "khong_do_duoc": 0,
                                       "thi_truong_qua": set(), "thi_truong_kiem": set(), "tot": []})
        m["n"] += 1
        m[k] += 1
        m["thi_truong_kiem"].add(u["ma"])
        if k == "qua":
            m["thi_truong_qua"].add(u["ma"])
            m["tot"].append((r.get("ky_vong_o_tran_pct") or 0.0, u["id"]))
    for g in nhom.values():
        g["ty_le_qua"] = ty_le_qua(g)
    nen = nhom["ngau"] if nhom["ngau"]["qua"] + nhom["ngau"]["ruot"] >= DOI_CHUNG_TOI_THIEU else nhom["doi"]
    nen_ten = "ngau" if nen is nhom["ngau"] else "doi"
    ty_nen = ty_le_qua(nen) if (nen["qua"] + nen["ruot"]) >= DOI_CHUNG_TOI_THIEU else None
    ra = []
    for m in sorted(cm.values(), key=lambda m: m["co_che"]):
        n_do = m["qua"] + m["ruot"]
        ty = ty_le_qua(m)
        if n_do >= 5 and len(m["thi_truong_qua"]) >= GIU_TOI_THIEU_THI_TRUONG and ty is not None and ty >= GIU_TY_LE_QUA_TOI_THIEU:
            nhan = "GIU"
        elif m["qua"] >= 1:
            nhan = "THEO_DOI"
        elif n_do >= 5:
            nhan = "BO"
        else:
            nhan = "CHUA_DU"
        so_nen = "CHUA_BIET" if (ty_nen is None or ty is None) else ("HON_NEN" if ty >= ty_nen + GIU_HON_DOI_CHUNG else "NGANG_NEN")
        ra.append({"co_che": m["co_che"], "n": m["n"], "qua": m["qua"], "ruot": m["ruot"], "khong_do_duoc": m["khong_do_duoc"],
                   "ty_le_qua": ty, "thi_truong_qua": sorted(m["thi_truong_qua"]), "so_thi_truong_kiem": len(m["thi_truong_kiem"]),
                   "nhan": nhan, "so_voi_nen": so_nen, "ung_vien_tot": [i for _, i in sorted(m["tot"], reverse=True)[:5]]})
    return {"nhom": nhom, "nen_so_sanh": nen_ten, "ty_le_nen": ty_nen, "co_che": ra}


def danh_sach_giu(ung_vien: list[dict], kq: dict[str, dict], co_che: dict) -> list[dict]:
    """Cac co che nhan GIU, kem ung vien tot nhat. `san_sang_niem_phong` = qua xac_nhan bang engine MOI (>= 4) - chi la nhan: niem phong
    la quyet dinh co chu dich cua cloud, va tester that (`ea_tho_chay`) van la cua cuoi (engine ~15% lac quan o tia lenh)."""
    theo_id = {u["id"]: u for u in ung_vien}
    ra = []
    for m in co_che["co_che"]:
        if m["nhan"] != "GIU":
            continue
        uv = []
        for i in m["ung_vien_tot"]:
            u, r = theo_id[i], kq[i]
            uv.append({"id": i, "ma": u["ma"], "khung": u["khung"], "tham_so": u["tham_so"], "von": u.get("von", 10000),
                       "loi_suat_nam_pct": r.get("loi_suat_nam_pct"), "maxdd_pct": r.get("maxdd_pct"),
                       "ky_vong_o_tran_pct": r.get("ky_vong_o_tran_pct"), "phien_ban_engine": r.get("phien_ban_engine"),
                       "tn_id": r.get("tn_id"), "san_sang_niem_phong": (r.get("phien_ban_engine") or ENGINE_CU) >= 4})
        ra.append({"co_che": m["co_che"], "ty_le_qua": m["ty_le_qua"], "thi_truong_qua": m["thi_truong_qua"],
                   "so_voi_nen": m["so_voi_nen"], "ung_vien": uv})
    return ra


# ------------------------------------------------------------------------ SO SANH THONG KE: pheu co hon boc tham khong?

#: Ke hoach doc ket qua, CO DINH TRUOC KHI CO KET QUA (10/10/2026): doi nguong sau khi nhin so la dang tim nguong cho vua so.
SO_SANH_N_TOI_THIEU = 20        # so cap (hoac so phep moi ben) co ket luan toi thieu truoc khi dam noi "hon" / "ngang"
SO_SANH_ALPHA = 0.05            # mot phia; hai phep thu cung luc, khong hieu chinh: day la NHAN canh bao, khong phai cong chan
SO_SANH_CHENH_TOI_THIEU = 0.10  # chenh ty le qua toi thieu (10 diem) de goi HON / KEM - mau lon khong duoc bien chenh be thanh "hon"


def _nhi_thuc_tu(k: int, n: int) -> float:
    """P(X >= k), X ~ Nhi thuc(n, 1/2), chinh xac (so nguyen, khong tran so)."""
    if k <= 0 or n <= 0:
        return 1.0
    if k > n:
        return 0.0
    return min(1.0, sum(math.comb(n, x) for x in range(k, n + 1)) / (1 << n))


def mcnemar_mot_phia(b: int, c: int) -> tuple[float, float]:
    """(p_hon, p_kem), chinh xac. b = so cap ma nhom thu QUA con doi chung RUOT; c = nguoc lai. Cap cung ket qua khong dong gop."""
    n = b + c
    return _nhi_thuc_tu(b, n), _nhi_thuc_tu(c, n)


def fisher_mot_phia(a: int, b: int, c: int, d: int) -> tuple[float, float]:
    """(p_hon, p_kem), chinh xac (sieu hinh hoc) cho bang [[a, b], [c, d]]: a/b = nhom thu QUA/RUOT, c/d = nhom doi chung QUA/RUOT."""
    n1, k, tong = a + b, a + c, a + b + c + d
    if n1 == 0 or tong - n1 == 0:
        return 1.0, 1.0
    lo, hi = max(0, n1 - (tong - k)), min(n1, k)
    mau = math.comb(tong, n1)
    p = {x: math.comb(k, x) * math.comb(tong - k, n1 - x) for x in range(lo, hi + 1)}
    return (min(1.0, sum(v for x, v in p.items() if x >= a) / mau), min(1.0, sum(v for x, v in p.items() if x <= a) / mau))


def khoang_wilson(k: int, n: int, z: float = 1.96) -> list[float] | None:
    """Khoang tin cay 95% (Wilson) cho ty le k/n; None khi n = 0."""
    if n <= 0:
        return None
    p, z2 = k / n, z * z
    mau = 1.0 + z2 / n
    tam = (p + z2 / (2.0 * n)) / mau
    nua = z * math.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n * n)) / mau
    return [round(max(0.0, tam - nua), 4), round(min(1.0, tam + nua), 4)]


def mde_hai_ty_le(n1: int, n2: int, p0: float) -> float | None:
    """Chenh ty le nho nhat (0..1) ma phep so sanh MOT PHIA 5% thay duoc voi luc 80% (xap xi chuan, hai mau doc lap). CLAUDE.md: ket luan
    'ngang / khong thay khac' PHAI di kem con so nay, neu khong 'khong thay' co the chi la 'khong du mau de thay'."""
    if n1 <= 0 or n2 <= 0:
        return None
    p = min(0.95, max(0.05, p0))
    return round((1.645 + 0.8416) * math.sqrt(p * (1.0 - p) * (1.0 / n1 + 1.0 / n2)), 3)


def _ket_luan_so_sanh(n_du: int, chenh: float | None, p_hon: float, p_kem: float) -> str:
    if chenh is None or n_du < SO_SANH_N_TOI_THIEU:
        return "CHUA_DU"
    if chenh >= SO_SANH_CHENH_TOI_THIEU and p_hon < SO_SANH_ALPHA:
        return "HON"
    if chenh <= -SO_SANH_CHENH_TOI_THIEU and p_kem < SO_SANH_ALPHA:
        return "KEM"
    return "NGANG"


def kq_cung_thuoc_do(da: dict[str, list[dict]]) -> dict[str, dict]:
    """Ket qua dung de SO SANH nhom - MOT thuoc do cho moi nhom. Don kiem lai bang engine moi (`vl-xn4-`) chi ra cho vai co che duoc GIU, nen
    dung no de so sanh se don rieng nhom cao vao thuoc do kho hon cac nhom khac. Moi o lay ket luan cua LAN KIEM DAU (engine thap nhat co
    ket luan QUA/RUOT; cung engine thi lan moi nhat). Nhan GIU / niem phong van dung ket qua tot nhat (`moi_nhat`), khong qua day."""
    ra: dict[str, dict] = {}
    for i, v in da.items():
        kl = sorted((r for r in v if r.get("ket_luan") in ("QUA", "RUOT")), key=lambda r: str(r.get("luc") or ""), reverse=True)
        if kl:
            ra[i] = min(kl, key=lambda r: r.get("phien_ban_engine") or ENGINE_CU)
    return ra


def _nhom_tuyet_doi(ung_vien: list[dict], kq: dict[str, dict], g: str) -> dict:
    qua = ruot = 0
    for u in ung_vien:
        if nhom_cua(u) != g:
            continue
        k = (kq.get(u["id"]) or {}).get("ket_luan")
        qua += k == "QUA"
        ruot += k == "RUOT"
    n = qua + ruot
    return {"n": n, "qua": qua, "ty_le": round(qua / n, 4) if n else None, "khoang_tin_cay": khoang_wilson(qua, n)}


def theo_do_manh(ung_vien: list[dict], kq: dict[str, dict], so_nhom: int = 3, n_toi_thieu: int = 30) -> list[dict] | None:
    """Ty le qua cua nhom cao theo DO MANH cua cao nguyen (ty le o co lai o kham_pha): cao nguyen manh hon co song sot nhieu hon khong?
    None khi it hon `n_toi_thieu` ket luan (chia nhom se la nhieu)."""
    xs = sorted([(u["ty_le"], (kq.get(u["id"]) or {}).get("ket_luan") == "QUA") for u in ung_vien
                 if nhom_cua(u) == "cao" and (kq.get(u["id"]) or {}).get("ket_luan") in ("QUA", "RUOT")], key=lambda t: t[0])
    if len(xs) < n_toi_thieu:
        return None
    ra = []
    for j in range(so_nhom):
        lat = xs[j * len(xs) // so_nhom:(j + 1) * len(xs) // so_nhom]
        qua = sum(1 for _, q in lat if q)
        ra.append({"ty_le_o_co_lai": [round(lat[0][0], 3), round(lat[-1][0], 3)], "n": len(lat), "qua": qua, "ty_le_qua": round(qua / len(lat), 4)})
    return ra


def so_sanh_nhom(ung_vien: list[dict], kq: dict[str, dict]) -> dict:
    """Vung lai (cao) co hon doi chung khong? HAI cau hoi khac nhau, hai phep thu khac nhau; nguong CO DINH truoc khi co ket qua (hang SO_SANH_*).

    1. cao vs NGAU (ghep cap cung luoi, McNemar chinh xac): chon o TOT NHAT trong luoi co hon chon BUA mot o cung luoi khong? Neu khong, quet
       3.000 o khong them gi so voi thu vai o -> dem thoi gian may sang chieu rong (thi truong, co che), khong quet sau.
    2. cao vs DOI (hai nhom doc lap, Fisher chinh xac): luot quet duoc xep CAO_NGUYEN co ben hon luot quet khac khi chi so sanh o tot nhat cua moi
       ben (cung 'loi nguoi thang') khong? Neu khong, cach xep cao nguyen khong du bao gi.
    Ca hai: HON = chenh >= 10 diem VA p < 0,05 (mot phia); KEM la nguoc lai; CHUA_DU khi < 20 cap / < 20 phep moi ben; con lai NGANG, kem MDE.
    `kq` phai cung thuoc do cho moi nhom (xem `kq_cung_thuoc_do`). Ket luan duoc = QUA | RUOT; KHONG_DO_DUOC bi bo khoi ca hai phep thu."""
    qr = ("QUA", "RUOT")
    kl = lambda u: (kq.get(u["id"]) or {}).get("ket_luan")
    theo_id = {u["id"]: u for u in ung_vien}
    ca = {"cao_qua_ngau_ruot": 0, "cao_ruot_ngau_qua": 0, "ca_hai_qua": 0, "ca_hai_ruot": 0}
    for u in ung_vien:
        cha = theo_id.get(u.get("cha")) if u["lop"] == "NGAU_NHIEN" else None
        if cha is None or cha["lop"] != "CAO_NGUYEN" or kl(cha) not in qr or kl(u) not in qr:
            continue
        a, g = kl(cha) == "QUA", kl(u) == "QUA"
        ca["ca_hai_qua" if a and g else "cao_qua_ngau_ruot" if a else "cao_ruot_ngau_qua" if g else "ca_hai_ruot"] += 1
    n_cap = sum(ca.values())
    b, c = ca["cao_qua_ngau_ruot"], ca["cao_ruot_ngau_qua"]
    t_cao = (b + ca["ca_hai_qua"]) / n_cap if n_cap else None
    t_ngau = (c + ca["ca_hai_qua"]) / n_cap if n_cap else None
    chenh = None if n_cap == 0 else round(t_cao - t_ngau, 4)
    p_h, p_k = mcnemar_mot_phia(b, c)
    cn = dict(ca, cap=n_cap, ty_le_cao=None if t_cao is None else round(t_cao, 4), ty_le_ngau=None if t_ngau is None else round(t_ngau, 4),
              chenh=chenh, p_hon=round(p_h, 5), p_kem=round(p_k, 5), mde=mde_hai_ty_le(n_cap, n_cap, t_ngau if t_ngau is not None else 0.5),
              ket_luan=_ket_luan_so_sanh(n_cap, chenh, p_h, p_k))
    tc, td = _nhom_tuyet_doi(ung_vien, kq, "cao"), _nhom_tuyet_doi(ung_vien, kq, "doi")
    ph, pk = fisher_mot_phia(tc["qua"], tc["n"] - tc["qua"], td["qua"], td["n"] - td["qua"]) if tc["n"] and td["n"] else (1.0, 1.0)
    chenh_d = None if not (tc["n"] and td["n"]) else round(tc["ty_le"] - td["ty_le"], 4)
    cd = {"n_cao": tc["n"], "n_doi": td["n"], "qua_cao": tc["qua"], "qua_doi": td["qua"], "ty_le_cao": tc["ty_le"], "ty_le_doi": td["ty_le"],
          "chenh": chenh_d, "p_hon": round(ph, 5), "p_kem": round(pk, 5),
          "mde": mde_hai_ty_le(tc["n"], td["n"], td["ty_le"] if td["ty_le"] is not None else 0.5),
          "ket_luan": _ket_luan_so_sanh(min(tc["n"], td["n"]), chenh_d, ph, pk)}
    return {"cao_vs_ngau": cn, "cao_vs_doi": cd,
            "tuyet_doi": {"cao": tc, "doi": td, "ngau": _nhom_tuyet_doi(ung_vien, kq, "ngau")},
            "theo_do_manh": theo_do_manh(ung_vien, kq),
            "luat": {"n_toi_thieu": SO_SANH_N_TOI_THIEU, "alpha": SO_SANH_ALPHA, "chenh_toi_thieu": SO_SANH_CHENH_TOI_THIEU}}


def _loi_so_sanh(ss: dict) -> str | None:
    """Mot dong LOI THUONG (khong thuat ngu) cho chu du an: chon o tot nhat co hon chon bua? cach xep 'cao nguyen' co hon luoi khac? None khi
    chua co phep thu nao."""
    cn, cd = ss.get("cao_vs_ngau") or {}, ss.get("cao_vs_doi") or {}
    if not cn.get("cap") and not (cd.get("n_cao") and cd.get("n_doi")):
        return None
    ra = []
    if cn.get("cap"):
        kl, a, g, n = cn["ket_luan"], _pc(cn["ty_le_cao"]), _pc(cn["ty_le_ngau"]), cn["cap"]
        md = int(round(100 * (cn["mde"] or 0.0)))
        ra.append({"CHUA_DU": "chon o tot nhat trong luoi so voi chon bua: chua du phep thu (%d cap, can >= %d)" % (n, SO_SANH_N_TOI_THIEU),
                   "HON": "chon o tot nhat trong luoi HON chon bua mot o cung luoi (qua ngoai mau %s so voi %s, %d cap, p=%.3f)" % (a, g, n, cn["p_hon"]),
                   "NGANG": "chon o tot nhat trong luoi CHUA THAY hon chon bua (%s so voi %s, %d cap; phep thu chi thay duoc chenh tu ~%d diem)" % (a, g, n, md),
                   "KEM": "chon o tot nhat trong luoi KEM hon chon bua (%s so voi %s, %d cap, p=%.3f)" % (a, g, n, cn["p_kem"])}[kl])
    if cd.get("n_cao") and cd.get("n_doi"):
        kl, a, g = cd["ket_luan"], _pc(cd["ty_le_cao"]), _pc(cd["ty_le_doi"])
        md = int(round(100 * (cd["mde"] or 0.0)))
        ra.append({"CHUA_DU": "xep luoi 'cao nguyen' so voi luoi khac: chua du phep thu (%d vs %d, can >= %d moi ben)" % (cd["n_cao"], cd["n_doi"], SO_SANH_N_TOI_THIEU),
                   "HON": "luoi xep 'cao nguyen' ben hon luoi khac (qua %s so voi %s, %d vs %d phep, p=%.3f)" % (a, g, cd["n_cao"], cd["n_doi"], cd["p_hon"]),
                   "NGANG": "luoi xep 'cao nguyen' CHUA THAY ben hon luoi khac (%s so voi %s, %d vs %d phep; phep thu chi thay duoc chenh tu ~%d diem)" % (a, g, cd["n_cao"], cd["n_doi"], md),
                   "KEM": "luoi xep 'cao nguyen' KEM ben hon luoi khac (%s so voi %s, %d vs %d phep, p=%.3f)" % (a, g, cd["n_cao"], cd["n_doi"], cd["p_kem"])}[kl])
    return "So sanh voi doi chung: " + "; ".join(ra) + "."


# -------------------------------------------------------------------------------------------- AP DUNG

_KHUNG_THU_TU = ("M1", "M5", "M15", "M30", "H1", "H4", "D1")


def khung_ke(khung: str) -> list[str]:
    if khung not in _KHUNG_THU_TU:
        return []
    i = _KHUNG_THU_TU.index(khung)
    return [_KHUNG_THU_TU[j] for j in (i - 1, i + 1) if 0 <= j < len(_KHUNG_THU_TU)]


def thi_truong_ke(ma: str, tat_ca) -> list[str]:
    """Cap tien chung it nhat mot dong tien voi `ma` (AUDCAD -> AUDCHF, AUDNZD, NZDCAD, USDCAD...). Khong phai cap 6 chu: bo qua."""
    if len(ma) != 6:
        return []
    a, b = ma[:3], ma[3:]
    return sorted(m for m in set(tat_ca) if m != ma and len(m) == 6 and (m[:3] in (a, b) or m[3:] in (a, b)))


def _gan(v, he: float):
    x = round(float(v) * he, 1)
    return int(x) if x == int(x) else x


def luoi_quanh(ts: dict) -> tuple[dict, dict]:
    """(truc luoi, tham so co dinh) HEP quanh mot o tot: buoc, tp x{0,75; 1; 1,33}; tran_tang +-2; cho_lui x{0,5; 1; 1,5} (27-81 o).
    Chuyen sang thi truong / khung KHAC: doi hoi cung co che, khong doi hoi cung con so - phai de luoi di chuyen."""
    truc = {}
    for k in ("buoc", "tp"):
        if isinstance(ts.get(k), (int, float)):
            truc[k] = sorted({max(2, _gan(ts[k], h)) for h in (0.75, 1.0, 1.33)})
    if isinstance(ts.get("tran_tang"), (int, float)):
        truc["tran_tang"] = sorted({max(2, int(ts["tran_tang"]) + d) for d in (-2, 0, 2)})
    if isinstance(ts.get("cho_lui"), (int, float)) and ts["cho_lui"]:
        truc["cho_lui"] = sorted({max(0, int(round(ts["cho_lui"] * h))) for h in (0.5, 1.0, 1.5)})
    return truc, {k: v for k, v in ts.items() if k not in truc}


def da_quet_cua(xong: list[dict], cho: list[dict]) -> set[tuple]:
    """(ma, khung, che_do) da co mot luot quet (xong hoac dang cho): don chuyen chi nham vao cho TRONG."""
    ra = set()
    for d in list(xong) + list(cho):
        lenh = (d.get("bang_chung") or {}).get("lenh") if "bang_chung" in d else d.get("lenh")
        cc, arg = tach_lenh(lenh)
        if cc == "quet_luoi" and arg.get("ma") and arg.get("khung"):
            cd = (arg.get("co_dinh") or {}).get("che_do") or (arg.get("luoi") or {}).get("che_do")
            for c in (cd if isinstance(cd, list) else [cd]):
                ra.add((str(arg["ma"]).upper(), str(arg["khung"]).upper(), c))
    return ra


def co_du_lieu_cua(goc: Path | None = None) -> set[tuple]:
    """(ma, khung) co doan du lieu da khai trong so_cai/doan.json (may nha moi co gia that; day chi la danh sach da dong bang)."""
    try:
        x = json.loads(((goc or LAB) / "so_cai" / "doan.json").read_text(encoding="utf-8-sig"))
    except Exception:
        return set()
    return {tuple(k.split("|", 1)) for k in x if "|" in k}


def ke_hoach_ap_dung(giu: list[dict], co_du_lieu: set[tuple], da_quet: set[tuple], toi_da: int = 24) -> list[dict]:
    """Moi co che GIU -> don quet CHUYEN sang thi truong cung dong tien / khung ke chua tung quet voi che_do do (toi da 4 dich / nguon, 3 nguon
    / co che). Moi don la mot `spec` {loai, ma_don, ...}; chua ghi gi."""
    tat_ca_ma = {m for m, _ in co_du_lieu}
    ra: list[dict] = []
    thay = set()
    for g in giu:
        for u in g["ung_vien"][:3]:
            truc, co_dinh = luoi_quanh(u["tham_so"])
            if not truc:
                continue
            dich = [(m, u["khung"]) for m in thi_truong_ke(u["ma"], tat_ca_ma)] + [(u["ma"], k) for k in khung_ke(u["khung"])]
            n = 0
            for (m, k) in dich:
                if (m, k) not in co_du_lieu or (m, k, u["tham_so"].get("che_do")) in da_quet or (m, k, g["co_che"]) in thay:
                    continue
                thay.add((m, k, g["co_che"]))
                arg = {"ma": m, "khung": k, "luoi": truc, "co_dinh": co_dinh, "von": u.get("von", 10000), "toi_da_o": 81}
                ten = "%s%s-%s-%s" % (TT_CHUYEN, m, k, hashlib.sha1(("%s|%s|%s" % (g["co_che"], m, k)).encode()).hexdigest()[:6])
                ra.append({"loai": "chuyen", "ma_don": ten, "co_che": g["co_che"], "tu": u["ma"], "den": "%s %s" % (m, k),
                           "lenh": ["{py}", "b.py", "nc", "cc", "quet_luoi", json.dumps(arg, sort_keys=True, ensure_ascii=True)]})
                n += 1
                if n >= 4 or len(ra) >= toi_da:
                    break
            if len(ra) >= toi_da:
                return ra
    return ra


def ke_hoach_nho_lai(giu: list[dict]) -> list[dict]:
    """Moi co che GIU -> (a) MOT yeu cau SEEKER di tim nguon cung loai, (b) MOT ghi hieu biet vao so tay nghien cuu (de phien sau thay)."""
    ra = []
    for g in giu:
        h = hashlib.sha1(g["co_che"].encode()).hexdigest()[:6]
        che_do, kieu, lui = (g["co_che"].split("|") + ["?", "?", "?"])[:3]
        cap = ",".join(g["thi_truong_qua"][:6])
        sk = {"chu_de": "EA luoi / DCA / martingale kieu %s (%s, %s cho gia lui) tren %s" % (che_do, kieu, "co" if lui == "lui" else "khong", cap),
              "tu_khoa": ["grid EA %s" % cap.split(",")[0], "martingale grid mean reversion forex", "DCA grid EA %s" % che_do,
                          "setka sovetnik martingale", "wang ge EA martingale"],
              "vi_sao": "co che %s qua xac_nhan o %d thi truong (%s): tim nguon / EA cong khai cung kieu de doi chieu tham so va quan li lenh"
                        % (g["co_che"], len(g["thi_truong_qua"]), cap)}
        ra.append({"loai": "seeker", "ma_don": TT_SEEKER + h, "co_che": g["co_che"], "lan": "NHE",
                   "lenh": ["{py}", "b.py", "nc", "cc", "yeu_cau_seeker", json.dumps(sk, sort_keys=True, ensure_ascii=True)]})
        tn = sorted({u["tn_id"] for u in g["ung_vien"] if u.get("tn_id")})
        if tn:
            hb = {"cau": "Co che luoi %s (%s) co lai tren xac_nhan o %d thi truong: %s. ENGINE MO PHONG (chua tester that)." % (
                      g["co_che"], g["so_voi_nen"], len(g["thi_truong_qua"]), cap),
                  "do_tin": 0.4 if any(u.get("san_sang_niem_phong") for u in g["ung_vien"]) else 0.3,
                  "bang_chung": tn, "pham_vi": {"co_che": g["co_che"], "thi_truong": g["thi_truong_qua"], "nguon": "vong_lap"}}
            ra.append({"loai": "ghi", "ma_don": TT_GHI + h, "co_che": g["co_che"], "lan": "NHE",
                       "lenh": ["{py}", "b.py", "nc", "cc", "ghi_hieu_biet", json.dumps(hb, sort_keys=True, ensure_ascii=True)]})
    return ra


def ra_don_ap_dung(spec: dict, goc: Path | None = None) -> Path | None:
    """Ghi mot don AP_DUNG; None neu da co don cung ten (cho hoac xong). Don 'chuyen' chay CPU; 'seeker'/'ghi' chay lan NHE."""
    thu = _thu(goc)
    if (thu / "cho" / ("%s.json" % spec["ma_don"])).exists() or (thu / "xong" / ("%s.json" % spec["ma_don"])).exists():
        return None
    _kiem_lenh(spec["lenh"])
    mo_ta = {"chuyen": "AP DUNG (vong lap): co che %s da giu lai (nguon %s) -> quet hep o %s: co che co chuyen duoc khong?",
             "seeker": "AP DUNG (vong lap): co che %s da giu lai -> nho SEEKER tim nguon cung loai%s",
             "ghi": "GIU (vong lap): ghi hieu biet ve co che %s vao so tay nghien cuu%s"}[spec["loai"]]
    chi_tiet = (spec.get("tu", ""), spec.get("den", "")) if spec["loai"] == "chuyen" else ("", "")
    muc_tieu = mo_ta % ((spec["co_che"],) + chi_tiet if spec["loai"] == "chuyen" else (spec["co_che"], ""))
    return CG.ra_don(spec["ma_don"], muc_tieu, lenh=spec["lenh"], lan=("CPU" if spec["loai"] == "chuyen" else "NHE"),
                     uu_tien=4, han_phut=(30.0 if spec["loai"] == "chuyen" else 10.0), cong={"kieu": "chay_duoc"}, goc=goc,
                     them={"vi_sao": "vong lap khep kin: nap nguoc co che giu lai vao vong sau"})


# --------------------------------------------------------------------------------------- TIM: dien dan

_RE_DIEN_DAN = re.compile(r"^\s*([A-Za-z0-9_\-]+)\s+([a-z]{2,3})\s+([A-Z_]+)\s*(.*)$")
_TRANG_THAI_OK = ("XONG_PASS", "OK", "XONG")


def doc_dien_dan(d: dict) -> dict:
    """Dong ket qua `dien-dan quet|do` -> {nguon_ok, nguon_chan, bai_moi}. Doc tu `dong_cuoi` (nhu `giam_sat_may_nha`)."""
    ok, chan, bai = set(), set(), 0
    for s in (d.get("bang_chung") or {}).get("dong_cuoi") or []:
        m = _RE_DIEN_DAN.match(str(s))
        if not m:
            continue
        ten, _, tt, phan = m.groups()
        if tt in _TRANG_THAI_OK:
            ok.add(ten)
            mb = re.search(r"\+(\d+) bai", phan)
            bai += int(mb.group(1)) if mb else 0
        elif tt.isupper() and len(tt) > 3:
            chan.add(ten)
    return {"nguon_ok": ok, "nguon_chan": chan, "bai_moi": bai}


# ------------------------------------------------------------------------------------------ BANG DIEM

GIAY_MAC_DINH = {"CPU": 60.0, "NHE": 30.0, "MANG": 120.0, "TESTER": 1800.0}


def _gio(giay: float) -> float:
    return round(giay / 3600.0, 1)


def bang_diem(goc: Path | None = None, xong: list[dict] | None = None, cho: list[dict] | None = None) -> dict:
    """Bang diem TUNG CHANG cua vong, sinh tu `viec/` (git). Khong ghi gi."""
    xong = doc_xong(goc) if xong is None else xong
    cho = doc_cho(goc) if cho is None else cho
    kn = kha_nang_biet(goc)
    ch = {c: {"ten": TEN_CHANG[c], "so_don": 0, "dat": 0, "am": 0, "chua_do_duoc": 0, "giay": 0.0, "cho_chay_duoc": 0,
              "cho_bi_chan": 0, "phu": {}, "cong_cu": collections.Counter()} for c in CHANG}
    giay_cc: dict[str, list[float]] = collections.defaultdict(list)
    lop_quet: collections.Counter = collections.Counter()
    tim = {"bai_moi": 0, "nguon_ok": set(), "nguon_chan": set(), "link_trong": 0, "lan": 0}
    boc: collections.Counter = collections.Counter()
    ap_xong: collections.Counter = collections.Counter()
    for d in xong:
        b = d.get("bang_chung") or {}
        cc, arg = tach_lenh(b.get("lenh"))
        c, phu = chang_cua(cc, arg, d["ma"])
        x = ch[c]
        x["so_don"] += 1
        x[{"DAT": "dat", "AM": "am"}.get(d.get("trang_thai"), "chua_do_duoc")] += 1
        g = _giay(d)
        x["giay"] += g
        x["cong_cu"][cc] += 1
        if phu:
            p = x["phu"].setdefault(phu, {"so_don": 0, "giay": 0.0})
            p["so_don"] += 1
            p["giay"] += g
        if g:
            giay_cc[cc].append(g)
        txt = None
        if cc == "quet_luoi":
            txt = "\n".join(str(s) for s in (b.get("dong_cuoi") or []))
            m = _RE_LOP.search(txt)
            lop_quet[m.group(1) if m else "KHONG_DOC_DUOC"] += 1
        if c == "TIM":
            tim["lan"] += 1
            if cc.startswith("dien-dan"):
                dd = doc_dien_dan(d)
                tim["bai_moi"] += dd["bai_moi"]
                tim["nguon_ok"] |= dd["nguon_ok"]
                tim["nguon_chan"] |= dd["nguon_chan"]
            elif cc.startswith("link") and "CHUA CO LINK NAO" in "\n".join(str(s) for s in (b.get("dong_cuoi") or [])):
                tim["link_trong"] += 1
        if c == "BOC" and d.get("trang_thai") == "DAT":
            boc[cc] += 1
        if c in ("AP_DUNG", "GIU"):
            ap_xong[phu] += 1
    tb = {cc: sum(v) / len(v) for cc, v in giay_cc.items()}
    chan_tag: collections.Counter = collections.Counter()
    gio_cho = 0.0
    n_cho = n_chan = 0
    kham_cho = 0
    for d in cho:
        cc, arg = tach_lenh(d.get("lenh"))
        c, phu = chang_cua(cc, arg, d["ma"])
        thieu = sorted({str(x) for x in (d.get("can") or [])} - kn) if kn else []
        n_cho += 1
        if thieu:
            ch[c]["cho_bi_chan"] += 1
            n_chan += 1
            chan_tag.update(thieu)
        else:
            ch[c]["cho_chay_duoc"] += 1
            gio_cho += tb.get(cc, GIAY_MAC_DINH.get(str(d.get("lan") or "NHE").upper(), 60.0)) / 3600.0
            kham_cho += 1 if (c == "KIEM" and phu == "kham") else 0
    tong_giay = sum(x["giay"] for x in ch.values())
    for c, x in ch.items():
        x["gio"] = _gio(x["giay"])
        x["ty_le_gio"] = round(x["giay"] / tong_giay, 4) if tong_giay else 0.0
        x["dich"] = DICH[c]
        for p in x["phu"].values():
            p["gio"] = _gio(p["giay"])
            p["ty_le_gio"] = round(p["giay"] / tong_giay, 4) if tong_giay else 0.0
            del p["giay"]
        del x["giay"]
        x["cong_cu"] = dict(x["cong_cu"].most_common(8))
    # ----- ung vien, co che, giu
    uv = gom_ung_vien(xong)
    da, dc = xac_nhan_da_co(xong, cho, goc)
    uv_id = {u["id"] for u in uv}
    uv_tat_ca = list(uv)
    for u in uv:                                       # o NGAU NHIEN khong nam trong luot quet nao: sinh lai (xac dinh) roi nhan theo don da ra
        if u["lop"] == "CAO_NGUYEN":
            g = sinh_ngau_nhien(u)
            if g and g["id"] not in uv_id and (g["id"] in da or g["id"] in dc):
                uv_tat_ca.append(g)
                uv_id.add(g["id"])
    kq = {i: moi_nhat(v) for i, v in da.items()}
    co_che = gom_co_che(uv_tat_ca, kq)
    giu = danh_sach_giu(uv_tat_ca, kq, co_che)
    cao = [u for u in uv if u["lop"] == "CAO_NGUYEN"]
    ung_vien = {"tong": len(uv), "cao_nguyen": len(cao), "doi_chung": len(uv) - len(cao),
                "cao_co_ket_qua": sum(1 for u in cao if u["id"] in kq),
                "cao_dang_cho": sum(1 for u in cao if u["id"] not in kq and u["id"] in dc),
                "cao_chua_ra_don": sum(1 for u in cao if u["id"] not in kq and u["id"] not in dc),
                "quet_cao_nguyen": lop_quet.get("CAO_NGUYEN", 0),
                "ngau_nhien_da_ra_don": sum(1 for u in uv_tat_ca if u["lop"] == "NGAU_NHIEN")}
    san_luong = {"tim": {"bai_moi": tim["bai_moi"], "nguon_ok": len(tim["nguon_ok"]), "nguon_chan": len(tim["nguon_chan"] - tim["nguon_ok"]),
                         "link_trong": tim["link_trong"], "lan": tim["lan"]},
                 "boc": dict(boc), "lop_quet": dict(lop_quet), "nhom_xac_nhan": co_che["nhom"],
                 "ap_dung_xong": dict(ap_xong), "giu": len(giu)}
    bd = {"luc": time.strftime("%Y-%m-%d %H:%M", time.gmtime()) + " UTC",
          "tong": {"so_don": len(xong), "gio": _gio(tong_giay), "cho_tong": n_cho, "cho_chay_duoc": n_cho - n_chan, "cho_bi_chan": n_chan,
                   "gio_cho_chay_duoc": round(gio_cho, 1), "thieu_ma": dict(chan_tag), "cho_kham_chay_duoc": kham_cho,
                   "kha_nang_biet": sorted(kn)},
          "chang": ch, "san_luong": san_luong, "ung_vien": ung_vien, "co_che": co_che, "giu": giu}
    bd["so_sanh"] = so_sanh_nhom(uv_tat_ca, kq_cung_thuoc_do(da))          # TRUOC tim_diem_nghen: diem nghen doc ket qua so sanh
    bd["diem_nghen"] = tim_diem_nghen(bd)
    bd["khuyen_nghi"] = khuyen_nghi(bd)
    bd["_uv"], bd["_kq"], bd["_da"], bd["_dc"] = uv_tat_ca, kq, da, dc    # cho `chay` / ghi bao cao; bo di khi in JSON
    bd["_xong"], bd["_cho"] = xong, cho
    return bd


def _pc(x: float) -> str:
    return ("%.0f" % (100 * x)) + "%" if x >= 0.095 else ("%.1f" % (100 * x)).replace(".", ",") + "%"


def tim_diem_nghen(bd: dict) -> list[str]:
    """Nhung cho vong dang KET, theo luat don gian (khong LLM). Moi dong: ban than no noi ro cai gi sai va lam gi tiep."""
    ra: list[str] = []
    u, ch, t, sl = bd["ung_vien"], bd["chang"], bd["tong"], bd["san_luong"]
    kham = ch["KIEM"]["phu"].get("kham", {"ty_le_gio": 0.0, "so_don": 0})
    xac = ch["KIEM"]["phu"].get("xac", {"ty_le_gio": 0.0, "so_don": 0})
    if u["cao_nguyen"] and u["cao_chua_ra_don"]:
        ra.append("KIEM->GIU dut: %d vung lai (cao nguyen) chua tung duoc kiem ngoai mau, %d da co ket qua, %d dang cho may -> "
                  "`python3 -m nhan.vong_lap --giao`" % (u["cao_chua_ra_don"], u["cao_co_ket_qua"], u["cao_dang_cho"]))
    if kham["ty_le_gio"] > 0.5 and xac["ty_le_gio"] < 0.05:
        ra.append("thoi gian may lech: quet trong mau %s, kiem ngoai mau %s (de xuat tong chang KIEM %s, trong do ngoai mau it nhat 1/3)" % (
            _pc(kham["ty_le_gio"]), _pc(xac["ty_le_gio"]), _pc(DICH["KIEM"])))
    for c in ("TIM", "BOC", "GIU", "AP_DUNG"):
        if t["gio"] >= 10 and ch[c]["ty_le_gio"] < DICH[c] / 2:
            ra.append("chang %s moi dung %s thoi gian may (de xuat %s)" % (c, _pc(ch[c]["ty_le_gio"]), _pc(DICH[c])))
    if t["cho_tong"] and not t["cho_chay_duoc"]:
        ra.append("MAY NHA BAT LEN SE KHONG CO VIEC: %d don cho deu cho ma moi (%s) -> can nap ma moi (mot lan) hoac ra don khong khai `can`" % (
            t["cho_tong"], ", ".join("%s x%d" % kv for kv in sorted(t["thieu_ma"].items(), key=lambda kv: -kv[1])[:4])))
    elif t["cho_bi_chan"]:
        ra.append("%d don cho ma moi (%s) nam im den khi may nha nap ma moi; %d don chay duoc ngay (~%s gio)" % (
            t["cho_bi_chan"], ", ".join(sorted(t["thieu_ma"])[:5]), t["cho_chay_duoc"], t["gio_cho_chay_duoc"]))
    if sl["tim"]["nguon_chan"] or sl["tim"]["link_trong"]:
        ra.append("TIM: doc duoc %d dien dan (%d bai), %d nguon bi chan/tat/can Chrome, %d lan tham do link khong co link nao" % (
            sl["tim"]["nguon_ok"], sl["tim"]["bai_moi"], sl["tim"]["nguon_chan"], sl["tim"]["link_trong"]))
    ss = bd.get("so_sanh") or {}
    cn, cd = ss.get("cao_vs_ngau") or {}, ss.get("cao_vs_doi") or {}
    if cn.get("ket_luan") in ("NGANG", "KEM"):
        ra.append("chon o tot nhat trong luoi %s chon bua mot o cung luoi: ngoai mau %s so voi %s (%d cap; phep thu chi thay duoc chenh tu ~%d diem) -> "
                  "thoi gian nen dem vao chieu rong (them thi truong / co che), khong quet sau" % (
                      "KHONG hon" if cn["ket_luan"] == "NGANG" else "KEM hon", _pc(cn["ty_le_cao"]), _pc(cn["ty_le_ngau"]), cn["cap"],
                      int(round(100 * (cn["mde"] or 0.0)))))
    if cd.get("ket_luan") in ("NGANG", "KEM"):
        ra.append("xep luoi 'cao nguyen' %s luoi khac: ngoai mau %s so voi %s (%d vs %d phep; phep thu chi thay duoc chenh tu ~%d diem) -> "
                  "phan loai cao nguyen chua du bao duoc gi, dung dung no lam bo loc duy nhat" % (
                      "KHONG ben hon" if cd["ket_luan"] == "NGANG" else "KEM ben hon", _pc(cd["ty_le_cao"]), _pc(cd["ty_le_doi"]), cd["n_cao"],
                      cd["n_doi"], int(round(100 * (cd["mde"] or 0.0)))))
    if not bd["giu"]:
        ra.append("GIU: 0 co che giu lai (can >= 3 thi truong qua xac_nhan, >= 50% ung vien) -> chua co gi de AP DUNG vao vong sau")
    return ra


def khuyen_nghi(bd: dict) -> list[str]:
    """Viec CLOUD nen lam bay gio de vong khep (cho `giam_sat_may_nha` / routine moi gio). Rong = vong dang chay deu."""
    ra: list[str] = []
    u, t = bd["ung_vien"], bd["tong"]
    if u["cao_chua_ra_don"]:
        ra.append("VONG LAP: %d vung lai chua kiem ngoai mau -> `python3 -m nhan.vong_lap --giao 240` (don CPU vai giay, chay duoc tren ma "
                  "hien tai) roi commit viec/cho + reports/vong_lap" % u["cao_chua_ra_don"])
    if bd["giu"] and bd["san_luong"]["ap_dung_xong"].get("chuyen", 0) == 0:
        ra.append("VONG LAP: co %d co che GIU nhung chua don AP DUNG nao xong -> `python3 -m nhan.vong_lap --giao` ra don chuyen + SEEKER + so tay" % len(bd["giu"]))
    kham = bd["chang"]["KIEM"]["phu"].get("kham", {})
    if t["cho_chay_duoc"] and t["cho_kham_chay_duoc"] / max(1, t["cho_chay_duoc"]) > 0.5:
        ra.append("CAN BANG: quet trong mau chiem %d%% hang doi chay duoc (toi da 50%%) -> dung giao them don quet_luoi, giao don TIM/BOC/KIEM ngoai mau" % (
            100 * t["cho_kham_chay_duoc"] / max(1, t["cho_chay_duoc"])))
    elif kham and bd["chang"]["KIEM"]["phu"].get("xac", {}).get("so_don", 0) == 0 and not u["cao_chua_ra_don"] and not u["cao_dang_cho"] and u["cao_nguyen"]:
        ra.append("CAN BANG: moi vung lai da co don kiem; khi het ket qua thi chay lai `python3 -m nhan.vong_lap` de chon co che GIU")
    return ra


# --------------------------------------------------------------------------------------- tom tat & bao cao

#: Dong chu du an dan MOT LAN vao phien Claude Code o may nha de may nha nap ma moi (khong sua tay gi o day).
DONG_NAP_MA_NHA = ("Doc thu cloud: chay `b cau lay && b cau thu`, commit phan sua tay cua ban o qwen/cau_git.py roi `git pull --ff-only`, "
                   "khoi dong lai bo chay `b cau chay --lien-tuc --nghi 20`, va bao ket qua bang `b cau noi`.")


def don_ton_tai(ten: str, goc: Path | None = None) -> bool:
    t = _thu(goc)
    return (t / "cho" / ("%s.json" % ten)).exists() or (t / "xong" / ("%s.json" % ten)).exists()


def tom_tat_cho_chu(bd: dict) -> list[str]:
    """3-8 dong bang loi thuong (khong thuat ngu): xong / chua / ket o dau / can chu du an lam gi. Sinh tu bang diem, khong LLM."""
    t, ch, u, sl = bd["tong"], bd["chang"], bd["ung_vien"], bd["san_luong"]
    kham = ch["KIEM"]["phu"].get("kham", {"ty_le_gio": 0.0})
    xac = ch["KIEM"]["phu"].get("xac", {"ty_le_gio": 0.0})
    d = ["Vong lap (tim -> boc -> kiem -> giu -> ap dung): da chay %d viec, %s gio may. Gio may chia: quet trong mau %s, kiem ngoai mau %s, "
         "tim nguon %s, boc co che %s, giu lai %s, ap dung %s." % (
             t["so_don"], t["gio"], _pc(kham["ty_le_gio"]), _pc(xac["ty_le_gio"]), _pc(ch["TIM"]["ty_le_gio"]), _pc(ch["BOC"]["ty_le_gio"]),
             _pc(ch["GIU"]["ty_le_gio"]), _pc(ch["AP_DUNG"]["ty_le_gio"]))]
    d.append("Vung lai tim duoc: %d. Da kiem ngoai mau: %d, dang cho may: %d, chua ra don: %d." % (
        u["cao_nguyen"], u["cao_co_ket_qua"], u["cao_dang_cho"], u["cao_chua_ra_don"]))
    nhom = sl["nhom_xac_nhan"]
    if nhom["cao"]["n"]:
        def _mot(g, ten):
            tl = ty_le_qua(nhom[g])
            return "%s %s (%d phep)" % (ten, "chua du de noi" if tl is None else _pc(tl), nhom[g]["qua"] + nhom[g]["ruot"])
        d.append("Ket qua ngoai mau, ty le con lai (co lai): vung lai %s; %s; %s." % (
            _mot("cao", "vung lai"), _mot("doi", "o tot nhat cua luot quet thuong"), _mot("ngau", "o ngau nhien")))
        sanh = _loi_so_sanh(bd.get("so_sanh") or {})
        if sanh:
            d.append(sanh)
    d.append("Co che giu lai de ap dung vong sau: %d. Don ap dung (chuyen thi truong / nho SEEKER / ghi so tay) da xong: %d." % (
        len(bd["giu"]), sum(sl["ap_dung_xong"].values())))
    if bd["diem_nghen"]:
        d.append("Dang ket o: " + bd["diem_nghen"][0])
    if t["cho_tong"] and not t["cho_chay_duoc"]:
        d.append("Can chu du an: may nha chua nap ma moi nen se KHONG co viec khi bat len; dan MOT dong (reports/VONG_LAP.md muc 'Viec cho may nha') vao phien Claude Code o may nha.")
    return d[:8]


def _bang_md(hang: list[list], tieu_de: list[str]) -> list[str]:
    ra = ["| " + " | ".join(tieu_de) + " |", "|" + "|".join("---" for _ in tieu_de) + "|"]
    for h in hang:
        ra.append("| " + " | ".join(str(x).replace("|", "/") for x in h) + " |")
    return ra


def _gt(x, kieu: str = "{:.3f}") -> str:
    return "-" if x is None else kieu.format(x)


def _doan_so_sanh(ss: dict) -> list[str]:
    """Muc 'Phep so sanh voi doi chung' cua bao cao (ASCII): hai phep thu, ty le tuyet doi co khoang tin cay, theo do manh cua cao nguyen."""
    if not ss:
        return []
    cn, cd, td, lu = ss["cao_vs_ngau"], ss["cao_vs_doi"], ss["tuyet_doi"], ss["luat"]
    L = ["## Phep so sanh voi doi chung (ke hoach dong bang 10/10/2026 - nguong dat TRUOC khi co ket qua)", "",
         "Hai cau hoi khac nhau. HON = chenh >= %d diem va p < %s (mot phia, chinh xac); KEM = nguoc lai; CHUA_DU = it hon %d cap / %d phep moi ben; con lai "
         "NGANG (kem MDE: chenh nho nhat phep thu thay duoc voi luc 80%%). Ca hai dung ket luan cua lan kiem DAU (cung engine) cho moi o; khong hieu chinh "
         "da phep thu vi day la NHAN canh bao, khong phai cong chan." % (int(100 * lu["chenh_toi_thieu"]), lu["alpha"], lu["n_toi_thieu"], lu["n_toi_thieu"]), ""]
    L += _bang_md([["1. chon o TOT NHAT trong luoi co hon chon BUA mot o cung luoi? (ghep cap, McNemar)", cn["cap"], cn["ca_hai_qua"], cn["cao_qua_ngau_ruot"],
                    cn["cao_ruot_ngau_qua"], cn["ca_hai_ruot"], _gt(cn["ty_le_cao"], "{:.1%}"), _gt(cn["ty_le_ngau"], "{:.1%}"), _gt(cn["chenh"], "{:+.3f}"),
                    _gt(cn["p_hon"] if cn["cap"] else None), _gt(cn["mde"]), cn["ket_luan"]]],
                  ["Phep thu", "So cap", "Ca hai qua", "Cao qua / ngau ruot", "Cao ruot / ngau qua", "Ca hai ruot", "Ty le cao", "Ty le ngau", "Chenh", "p (hon)",
                   "MDE", "Ket luan"])
    L += [""]
    L += _bang_md([["2. luoi xep CAO NGUYEN co ben hon luoi khac? (hai nhom, Fisher)", cd["n_cao"], cd["qua_cao"], cd["n_doi"], cd["qua_doi"],
                    _gt(cd["ty_le_cao"], "{:.1%}"), _gt(cd["ty_le_doi"], "{:.1%}"), _gt(cd["chenh"], "{:+.3f}"),
                    _gt(cd["p_hon"] if cd["n_cao"] and cd["n_doi"] else None), _gt(cd["mde"]), cd["ket_luan"]]],
                  ["Phep thu", "Cao: da kiem", "Cao: qua", "Doi: da kiem", "Doi: qua", "Ty le cao", "Ty le doi", "Chenh", "p (hon)", "MDE", "Ket luan"])
    L += [""]
    L += _bang_md([[ten, td[g]["n"], td[g]["qua"], _gt(td[g]["ty_le"], "{:.1%}"),
                    "-" if not td[g]["khoang_tin_cay"] else "%.1f%% - %.1f%%" % (100 * td[g]["khoang_tin_cay"][0], 100 * td[g]["khoang_tin_cay"][1])]
                   for g, ten in (("cao", "vung lai"), ("doi", "doi chung: o tot nhat luot quet khac"), ("ngau", "doi chung: o ngau nhien"))],
                  ["Nhom (ty le tuyet doi)", "Da kiem", "QUA", "Ty le qua", "Khoang tin cay 95% (Wilson)"])
    dm = ss.get("theo_do_manh")
    if dm:
        L += ["", "Ty le qua cua nhom cao theo DO MANH cua cao nguyen (ty le o co lai o kham_pha; manh hon co song sot nhieu hon khong?):", ""]
        L += _bang_md([["%s - %s" % (_gt(x["ty_le_o_co_lai"][0], "{:.2f}"), _gt(x["ty_le_o_co_lai"][1], "{:.2f}")), x["n"], x["qua"], _gt(x["ty_le_qua"], "{:.1%}")]
                       for x in dm], ["Ty le o co lai o kham_pha", "Da kiem", "QUA", "Ty le qua"])
    return L


def viet_bao_cao(bd: dict) -> str:
    """Noi dung `reports/VONG_LAP.md` (ASCII, tieng Viet khong dau theo quy uoc repo)."""
    t, ch, u, sl = bd["tong"], bd["chang"], bd["ung_vien"], bd["san_luong"]
    L = ["# VONG LAP KHEP KIN - bang diem theo chang", "",
         "Sinh tu `viec/` (git) boi `python3 -m nhan.vong_lap`, %s. Khong LLM, khong du lieu gia. Chu du an 10/10/2026: *muc tieu la VONG LAP "
         "tim -> boc -> kiem -> giu -> ap dung -> vong sau; cac module nho chi la phan cua vong*." % bd["luc"], "",
         "## Tom tat (loi thuong)", ""]
    L += ["- " + s for s in tom_tat_cho_chu(bd)]
    L += ["", "## Thoi gian may theo chang (tong %s gio, %d viec da xong)" % (t["gio"], t["so_don"]), ""]
    hang = []
    for c in CHANG:
        x = ch[c]
        hang.append([c + " - " + x["ten"], x["so_don"], x["dat"], x["am"], x["chua_do_duoc"], x["gio"], _pc(x["ty_le_gio"]), _pc(x["dich"]),
                     "%d / %d" % (x["cho_chay_duoc"], x["cho_bi_chan"])])
        for p, v in sorted(x["phu"].items()):
            hang.append(["&nbsp;&nbsp;" + {"kham": "trong mau (kham pha)", "xac": "NGOAI mau (xac nhan)", "chuyen": "chuyen thi truong",
                                            "seeker": "yeu cau SEEKER", "ghi": "ghi so tay"}.get(p, p), v["so_don"], "", "", "", v["gio"],
                         _pc(v["ty_le_gio"]), "", ""])
    L += _bang_md(hang, ["Chang", "Viec xong", "DAT", "AM", "CHUA DO", "Gio may", "Ty le", "De xuat", "Cho: chay duoc / bi chan"])
    L += ["", "DAT o cot nay chi nghia 'don chay xong, ma thoat 0' (xem `bang_chung.dong_cuoi` cua tung don). De xuat = muc tieu vong, chu du an sua duoc "
          "trong `nhan/vong_lap.DICH`.", "", "## Diem nghen", ""]
    L += ["- " + s for s in bd["diem_nghen"]] or ["- (khong co)"]
    L += ["", "## San luong tung chang", "",
          "- TIM: %d lan chay; doc duoc %d dien dan (%d bai moi), %d nguon bi chan / tat / can Chrome, %d lan tham do link khong co link." % (
              sl["tim"]["lan"], sl["tim"]["nguon_ok"], sl["tim"]["bai_moi"], sl["tim"]["nguon_chan"], sl["tim"]["link_trong"]),
          "- BOC: %s" % (", ".join("%s x%d" % kv for kv in sorted(sl["boc"].items())) or "chua co don nao"),
          "- KIEM trong mau: %s" % (", ".join("%s %d" % kv for kv in sorted(sl["lop_quet"].items())) or "chua co luot quet"),
          "- KIEM ngoai mau: vung lai %d da kiem, %d dang cho, %d chua ra don; o ngau nhien da ra don %d" % (
              u["cao_co_ket_qua"], u["cao_dang_cho"], u["cao_chua_ra_don"], u["ngau_nhien_da_ra_don"]),
          "- GIU: %d co che duoc giu lai" % sl["giu"],
          "- AP DUNG: %s" % (", ".join("%s %d" % kv for kv in sorted(sl["ap_dung_xong"].items()) if kv[0]) or "chua co don nao xong")]
    nhom = sl["nhom_xac_nhan"]
    L += ["", "## Kiem ngoai mau: cao nguyen co du bao duoc gi khong?", ""]
    L += _bang_md([[ten, nhom[g]["n"], nhom[g]["qua"], nhom[g]["ruot"], nhom[g]["khong_do_duoc"],
                    "-" if nhom[g]["ty_le_qua"] is None else _pc(nhom[g]["ty_le_qua"])]
                   for g, ten in (("cao", "vung lai (o tot nhat cua luot quet CAO NGUYEN)"), ("doi", "doi chung: o tot nhat cua luot quet khac"),
                                  ("ngau", "doi chung: o ngau nhien cung luoi"))],
                  ["Nhom", "Da kiem", "QUA (co lai)", "RUOT", "Khong do duoc", "Ty le qua"])
    L += ["", "QUA = co lai tren doan xac_nhan (mo, khong tinh phep thu) bang ENGINE MO PHONG. Ben trong mau luon dep hon ngoai mau (chon o tot "
          "nhat trong 3.000 o); so sanh voi nhom doi chung moi cho biet cao nguyen co hon ngau nhien hay khong.", ""]
    L += _doan_so_sanh(bd.get("so_sanh") or {})
    L += ["", "## Co che (che_do | kieu_lot | cho_lui)", ""]
    L += _bang_md([[m["co_che"], m["n"], m["qua"], m["ruot"], "-" if m["ty_le_qua"] is None else _pc(m["ty_le_qua"]),
                    "%d/%d" % (len(m["thi_truong_qua"]), m["so_thi_truong_kiem"]), m["nhan"], m["so_voi_nen"]] for m in bd["co_che"]["co_che"]],
                  ["Co che", "Da kiem", "QUA", "RUOT", "Ty le qua", "Thi truong qua/kiem", "Nhan", "So voi nen"]) if bd["co_che"]["co_che"] else ["(chua co ket qua ngoai mau)"]
    L += ["", "GIU = qua xac_nhan o >= %d thi truong va >= %d%% so ung vien co ket luan (NHAN, khong phai cong chan; niem phong la quyet dinh rieng)." % (
        GIU_TOI_THIEU_THI_TRUONG, int(100 * GIU_TY_LE_QUA_TOI_THIEU)), "", "## Co che giu lai (dau vao vong sau)", ""]
    if bd["giu"]:
        for g in bd["giu"]:
            L.append("- **%s**: qua %s o %d thi truong (%s), %s" % (g["co_che"], _pc(g["ty_le_qua"] or 0.0), len(g["thi_truong_qua"]),
                                                                 ", ".join(g["thi_truong_qua"]), g["so_voi_nen"]))
    else:
        L.append("- (chua co co che nao du dieu kien giu lai)")
    L += ["", "## Viec cho may nha", "",
          "- %d don dang cho: %d chay duoc ngay (uoc ~%s gio), %d nam im vi cho ma moi (%s)." % (
              t["cho_tong"], t["cho_chay_duoc"], t["gio_cho_chay_duoc"], t["cho_bi_chan"],
              ", ".join("%s x%d" % kv for kv in sorted(t["thieu_ma"].items(), key=lambda kv: -kv[1])[:6]) or "-"),
          "- May nha tung khai kha nang: %s." % (", ".join(t["kha_nang_biet"]) or "(chua co nhip tim)")]
    if t["cho_bi_chan"]:
        L += ["- MOT LAN, chu du an dan dong sau vao phien Claude Code o may nha de nap ma moi (khong lam gi them):", "", "      " + DONG_NAP_MA_NHA]
    L += ["", "## Khuyen nghi cho phien cloud / `giam_sat_may_nha`", ""]
    L += ["- " + s for s in bd["khuyen_nghi"]] or ["- (vong dang chay deu)"]
    dm = bd.get("don_moi")
    if dm:
        L += ["", "## Don vua ra lan nay", "", "- kiem ngoai mau: %d; kiem lai engine moi: %d; ap dung: %d; loi: %d" % (
            len(dm["xac_nhan"]), len(dm["engine4"]), len(dm["ap_dung"]), len(dm["loi"]))]
        L += ["  - loi: " + s for s in dm["loi"][:5]]
    return "\n".join(L) + "\n"


def _dau_van_tay(bd: dict) -> dict:
    t, u = bd["tong"], bd["ung_vien"]
    return {"so_don": t["so_don"], "cho": t["cho_tong"], "chay_duoc": t["cho_chay_duoc"], "uv": u["tong"], "cao": u["cao_nguyen"],
            "cao_kq": u["cao_co_ket_qua"], "cao_cho": u["cao_dang_cho"], "giu": len(bd["giu"])}


def _dong_ung_vien(u: dict, kq: dict) -> dict:
    r = kq.get(u["id"])
    return {"id": u["id"], "ma": u["ma"], "khung": u["khung"], "nhom": nhom_cua(u), "co_che": u["co_che"], "lop": u["lop"],
            "o": ("%s/%s" % (u["o_co_lai"], u["o_tong"])) if u.get("o_tong") else None, "n_quet": u.get("n_quet"), "tham_so": u["tham_so"],
            "xac_nhan": {k: r.get(k) for k in ("ket_luan", "loi_suat_nam_pct", "maxdd_pct", "calmar", "so_lenh", "phien_ban_engine", "tn_id",
                                              "ma_don")} if r else None}


def ghi_bao_cao(bd: dict, goc: Path | None = None) -> list[Path]:
    """reports/VONG_LAP.md + reports/vong_lap/{so.jsonl, ung_vien.json, giu.json}. so.jsonl chi them dong khi so dem doi."""
    g = (goc or LAB) / "reports"
    (g / "vong_lap").mkdir(parents=True, exist_ok=True)
    ra = []
    p = g / "VONG_LAP.md"
    p.write_text(viet_bao_cao(bd), encoding="utf-8")
    ra.append(p)
    p = g / "vong_lap" / "ung_vien.json"
    dong = [json.dumps(_dong_ung_vien(u, bd["_kq"]), sort_keys=True, ensure_ascii=True) for u in sorted(bd["_uv"], key=lambda u: (u["lop"], u["id"]))]
    p.write_text("[\n" + ",\n".join(dong) + "\n]\n", encoding="utf-8")
    ra.append(p)
    p = g / "vong_lap" / "giu.json"
    p.write_text(json.dumps(bd["giu"], sort_keys=True, ensure_ascii=True, indent=1) + "\n", encoding="utf-8")
    ra.append(p)
    p = g / "vong_lap" / "so.jsonl"
    cu = None
    if p.exists():
        for s in reversed(p.read_text(encoding="utf-8").splitlines()):
            try:
                cu = json.loads(s).get("dau_van_tay")
                break
            except Exception:
                continue
    moi = _dau_van_tay(bd)
    if moi != cu:
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"luc": bd["luc"], "dau_van_tay": moi, "gio": bd["tong"]["gio"],
                                "ty_le_gio": {c: bd["chang"][c]["ty_le_gio"] for c in CHANG}}, sort_keys=True, ensure_ascii=True) + "\n")
    ra.append(p)
    return ra


# ----------------------------------------------------------------------------------------------- dieu phoi

def chay(goc: Path | None = None, giao: int = 0, ghi: bool = True, toi_da_engine4: int = 60) -> dict:
    """Mot vong dieu phoi: do -> (neu giao) ra don KIEM ngoai mau + kiem lai engine moi + AP DUNG -> do lai -> ghi bao cao.

    Khong git, khong push: nguoi goi commit `viec/cho` va `reports/`. `giao` = so don kiem ngoai mau toi da ra trong lan nay."""
    bd = bang_diem(goc)
    dm = {"xac_nhan": [], "engine4": [], "ap_dung": [], "loi": []}
    if giao and giao > 0:
        da_co = set(bd["_da"]) | set(bd["_dc"])
        for u in chon_dot(bd["_uv"], da_co, giao):
            if don_ton_tai(TT_XAC + u["id"], goc):
                continue
            try:
                dm["xac_nhan"].append(ra_don_xac_nhan(u, goc).stem)
            except Exception as e:
                dm["loi"].append("%s: %s" % (u["id"], e))
        # kiem LAI bang engine moi: chi nhung o da QUA bang engine cu (RUOT o engine lac quan thi van RUOT o engine that hon)
        thu_tu = {"cao": 0, "ngau": 1, "doi": 2}
        qua_cu = [u for u in bd["_uv"] if (bd["_kq"].get(u["id"]) or {}).get("ket_luan") == "QUA"
                  and ((bd["_kq"][u["id"]].get("phien_ban_engine") or ENGINE_CU) < 4)]
        qua_cu.sort(key=lambda u: (thu_tu[nhom_cua(u)], -(bd["_kq"][u["id"]].get("ky_vong_o_tran_pct") or 0.0), u["id"]))
        for u in qua_cu[:max(0, toi_da_engine4)]:
            if don_ton_tai(TT_XAC4 + u["id"], goc):
                continue
            try:
                dm["engine4"].append(ra_don_xac_nhan(u, goc, engine4=True).stem)
            except Exception as e:
                dm["loi"].append("%s: %s" % (u["id"], e))
        if bd["giu"]:
            for spec in ke_hoach_ap_dung(bd["giu"], co_du_lieu_cua(goc), da_quet_cua(bd["_xong"], bd["_cho"])) + ke_hoach_nho_lai(bd["giu"]):
                try:
                    p = ra_don_ap_dung(spec, goc)
                    if p:
                        dm["ap_dung"].append(p.stem)
                except Exception as e:
                    dm["loi"].append("%s: %s" % (spec["ma_don"], e))
        if dm["xac_nhan"] or dm["engine4"] or dm["ap_dung"]:
            bd = bang_diem(goc)
    bd["don_moi"] = dm
    if ghi:
        ghi_bao_cao(bd, goc)
    return bd


def _bo_rieng(bd: dict) -> dict:
    return {k: v for k, v in bd.items() if not k.startswith("_")}


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="python3 -m nhan.vong_lap", description="Bang diem + dieu phoi VONG LAP khep kin (tim-boc-kiem-giu-ap dung).")
    ap.add_argument("--giao", nargs="?", const=DON_TOI_DA_MAC_DINH, default=0, type=int, metavar="N",
                    help="ra toi da N don kiem ngoai mau (mac dinh %d) + don kiem lai engine moi + don ap dung; KHONG push" % DON_TOI_DA_MAC_DINH)
    ap.add_argument("--in", dest="chi_in", action="store_true", help="chi in, khong ghi reports/ va khong ra don")
    ap.add_argument("--json", action="store_true", help="in bang diem day du dang JSON")
    ap.add_argument("--goc", default=None, help="thu muc goc thay cho lab/ (de thu)")
    a = ap.parse_args(argv)
    if a.chi_in and a.giao:
        ap.error("--in chi de xem: khong di kem --giao")
    bd = chay(Path(a.goc) if a.goc else None, giao=a.giao, ghi=not a.chi_in)
    if a.json:
        print(json.dumps(_bo_rieng(bd), ensure_ascii=False, indent=1, default=str))
        return 0
    for s in tom_tat_cho_chu(bd):
        print("- " + s)
    if bd["diem_nghen"][1:]:
        print("Diem nghen khac:")
        for s in bd["diem_nghen"][1:]:
            print("  * " + s)
    dm = bd["don_moi"]
    if a.giao:
        print("Don vua ra: kiem ngoai mau %d, kiem lai engine moi %d, ap dung %d, loi %d" % (
            len(dm["xac_nhan"]), len(dm["engine4"]), len(dm["ap_dung"]), len(dm["loi"])))
        for s in dm["loi"][:5]:
            print("  ! " + s)
    if bd["khuyen_nghi"]:
        print("Khuyen nghi:")
        for s in bd["khuyen_nghi"]:
            print("  > " + s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
