# -*- coding: utf-8 -*-
"""pheu_gia_tri.py - PHEU GIA TRI: tai lieu -> "DANG TIEN KHONG" -> co che -> phuong phap suy ra -> ket qua tien -> hoc nguoc ve NGUON.

Chu du an 06/10/2026: *"toi can nguon chat luong, hut nhieu du lieu, nhieu thu ra tien. Boc tach co che that thong minh, suy luan ra
phuong phap, dao nguoc lich su, loc cai gi ra duoc doanh thu"*. Cac manh da co (`vuon_nguon` do suat nguon theo UNG VIEN, `boc_llm` /
`boc_ma_llm` / `boc_lich_su` boc co che, `ngu_phap` + `nc_cong_cu` thu) KHONG noi nhau bang THUOC DO TIEN: nguon duoc xep theo "bao nhieu
ung vien tren 100 bai", khong theo "bao nhieu he CO LAI". Module nay la MAT PHANG con thieu, khong thay manh nao:

  1. `chan_doan`  - LLM re doc MOT tai lieu -> JSON co CAU TRUC (co che kinh te, loi nhuan cong bo, dau hieu do, du lieu can) + `suy_ra`:
                    cung CO CHE do con tra tien o dau nua (tai san / khung / chieu khac), moi cho kem LY DO va CACH BAC BO. May kiem tung
                    truong (tu vung kin, do dai, kieu), sai thi sua toi da 2 vong (giao thuc da_agent).
  2. `diem_dang_tien` - MAY (khong LLM) cham 0..100 = tin cay bang chung x kha thi tren du lieu cua lab x moi x ben vung. Khong dung diem
                    LLM tu cham. Tai lieu cong bo loi qua dep ma khong ngoai mau / khong phi bi tru, khong phai bi loai.
  3. `so`         - so cai JSONL: moi tai lieu, diem, tung phuong phap suy ra, va KET QUA (DAT / AM / CHUA_DO_DUOC) khi phep thu chay xong.
  4. `xep_nguon` / `bai_hoc` - hoc nguoc: nguon nao CO LAI (khong phai nhieu ung vien), loai co che x lop tai san nao hay chet -> dua vao
                    loi nhac lan sau + chia ngan sach nguon.

Khong goi mang o day: `goi_llm` do ben goi truyen vao (test dung ban gia). Du lieu that o `reports/pheu_gia_tri/so.jsonl`.
"""
from __future__ import annotations

import json
import math
import re
import time
from collections import defaultdict
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
SO = GOC / "reports" / "pheu_gia_tri" / "so.jsonl"

# ---------------------------------------------------------------- TU VUNG KIN (may kiem)
LOP_TAI_SAN = ("co_phieu", "chi_so", "fx", "hang_hoa", "kim_loai", "tien_so", "trai_phieu", "khac")
KHUNG = ("tick", "phut", "gio", "ngay", "tuan", "thang")
LOAI_CO_CHE = ("hanh_vi", "cau_truc_thi_truong", "rui_ro_bu_dap", "thanh_khoan", "thong_tin_cham",
               "lich_mua_vu", "dong_luong", "quay_ve", "bien_dong", "vi_mo", "quan_li_lenh", "khac")
DU_LIEU = ("gia_ngay", "gia_phut", "tick", "so_lenh", "co_phieu_cat_ngang", "quyen_chon", "vi_mo", "co_ban", "cot", "tin_tuc",
           "dong_tien_ca_nhan")
DAU_HIEU_DO = ("khong_phi", "trong_mau", "mau_ngan", "tinh_nguyen_chon", "ngoai_le_rieng_le", "khong_co_co_che",
               "quang_cao_khoa_hoc", "song_sot")
CHIEU = (1, -1, 0)   # mua / ban / chua ro (do mo phong quyet)

#: Lab THAT SU thu duoc (cap nhat khi co nguon moi). Khong tick, khong so lenh, khong cat ngang co phieu.
LAB_CO = {"lop": ("fx", "chi_so", "hang_hoa", "kim_loai"),
          "khung": ("phut", "gio", "ngay"),
          "du_lieu": ("gia_ngay", "gia_phut", "vi_mo", "cot")}   # vi_mo = FRED, cot = CFTC (tai tu cloud)

#: loai co che -> ben vung (co ly do cau truc hon la thoi quen). Cac con so la TIEN NGHIEM, `bai_hoc` sua lai bang ket qua that.
BEN_VUNG = {"cau_truc_thi_truong": 0.85, "rui_ro_bu_dap": 0.8, "lich_mua_vu": 0.75, "thanh_khoan": 0.75, "quan_li_lenh": 0.7,
            "thong_tin_cham": 0.65, "hanh_vi": 0.6, "vi_mo": 0.6, "bien_dong": 0.55, "quay_ve": 0.5, "dong_luong": 0.5, "khac": 0.3}

LOI_QUA_DEP_PCT_NAM = 60.0


# ---------------------------------------------------------------- KIEM CAU TRUC
def chuan_hoa(d):
    """Sua loi KIEU vo hai LLM hay gap (chieu '1' / '-1' / 0.0 dang chuoi) truoc khi kiem. Khong sua noi dung."""
    if isinstance(d, dict) and isinstance(d.get("suy_ra"), list):
        for b in d["suy_ra"]:
            if isinstance(b, dict) and isinstance(b.get("chieu"), (str, float)):
                try:
                    b["chieu"] = int(float(b["chieu"]))
                except (TypeError, ValueError):
                    pass
    return d


def kiem(d) -> list[str]:
    """Tra danh sach loi (rong = hop le). May kiem, khong hoi LLM."""
    loi: list[str] = []
    if not isinstance(d, dict):
        return ["khong phai object JSON"]
    co = d.get("co_che")
    if not isinstance(co, str) or len(co.strip()) < 25:
        loi.append("co_che phai la chuoi >= 25 ky tu: AI tra tien va VI SAO")
    if d.get("lop_tai_san") not in LOP_TAI_SAN:
        loi.append("lop_tai_san phai thuoc %s" % (LOP_TAI_SAN,))
    if d.get("khung") not in KHUNG:
        loi.append("khung phai thuoc %s" % (KHUNG,))
    if d.get("loai_co_che") not in LOAI_CO_CHE:
        loi.append("loai_co_che phai thuoc %s" % (LOAI_CO_CHE,))
    lc = d.get("loi_nhuan_cong_bo")
    if not isinstance(lc, dict):
        loi.append("loi_nhuan_cong_bo phai la object {pct_nam, sau_phi, ngoai_mau}")
    else:
        v = lc.get("pct_nam")
        if v is not None and not isinstance(v, (int, float)):
            loi.append("loi_nhuan_cong_bo.pct_nam phai la so hoac null")
        for k in ("sau_phi", "ngoai_mau"):
            if lc.get(k) not in (True, False, None):
                loi.append("loi_nhuan_cong_bo.%s phai la true/false/null" % k)
    for ten, vung in (("du_lieu_can", DU_LIEU), ("dau_hieu_do", DAU_HIEU_DO)):
        x = d.get(ten)
        if not isinstance(x, list) or any(i not in vung for i in x):
            loi.append("%s phai la danh sach con cua %s" % (ten, vung))
    sr = d.get("suy_ra")
    if not isinstance(sr, list) or not 0 <= len(sr) <= 6:
        loi.append("suy_ra phai la danh sach 0..6 phuong phap")
    else:
        for i, b in enumerate(sr):
            if not isinstance(b, dict):
                loi.append("suy_ra[%d] khong phai object" % i)
                continue
            if b.get("lop_tai_san") not in LOP_TAI_SAN or b.get("khung") not in KHUNG or b.get("chieu") not in CHIEU:
                loi.append("suy_ra[%d]: lop_tai_san / khung / chieu ngoai tu vung" % i)
            for k in ("vi_sao_tra_tien", "cach_bac_bo"):
                if not isinstance(b.get(k), str) or len(b[k].strip()) < 20:
                    loi.append("suy_ra[%d].%s phai la chuoi >= 20 ky tu" % (i, k))
    return loi


# ---------------------------------------------------------------- DIEM (MAY CHAM)
def kha_thi_mot(lop: str, khung: str, du_lieu: list[str] | None = None) -> float:
    """Phep thu nay co CHAY DUOC tren du lieu cua lab khong (0..1)."""
    d = 1.0 if lop in LAB_CO["lop"] else 0.0
    d *= 1.0 if khung in LAB_CO["khung"] else 0.0
    if du_lieu:
        thieu = [x for x in du_lieu if x not in LAB_CO["du_lieu"] and x not in ("tin_tuc", "co_ban", "dong_tien_ca_nhan")]
        d *= 0.0 if thieu else 1.0
    return d


def diem_dang_tien(d: dict, da_thu: dict[str, int] | None = None) -> dict:
    """0..100. Khong dung diem do LLM tu cham. `da_thu` = so he da thu theo loai_co_che (do bao hoa)."""
    lc = d.get("loi_nhuan_cong_bo") or {}
    tin = 0.5
    tin += 0.2 if lc.get("sau_phi") is True else (-0.1 if lc.get("sau_phi") is False else 0.0)
    tin += 0.2 if lc.get("ngoai_mau") is True else 0.0
    tin -= 0.12 * len(set(d.get("dau_hieu_do") or []))
    v = lc.get("pct_nam")
    if isinstance(v, (int, float)) and v > LOI_QUA_DEP_PCT_NAM and lc.get("ngoai_mau") is not True:
        tin -= 0.2
    tin = min(1.0, max(0.05, tin))
    # kha thi: lay ban GOC va moi phuong phap suy ra, lay ban tot nhat (co che chuyen duoc sang tai san lab co)
    cac = [kha_thi_mot(d.get("lop_tai_san"), d.get("khung"), d.get("du_lieu_can") or [])]
    cac += [kha_thi_mot(b.get("lop_tai_san"), b.get("khung")) for b in (d.get("suy_ra") or []) if isinstance(b, dict)]
    kt = max(cac) if cac else 0.0
    loai = d.get("loai_co_che")
    n = (da_thu or {}).get(loai, 0)
    moi = 1.0 / (1.0 + n / 40.0)
    ben = BEN_VUNG.get(loai, 0.3)
    if "khong_co_co_che" in (d.get("dau_hieu_do") or []):
        ben = min(ben, 0.2)
    diem = round(100.0 * tin * kt * moi * ben, 1)
    return {"diem": diem, "tin_cay": round(tin, 2), "kha_thi": round(kt, 2), "moi": round(moi, 2), "ben_vung": round(ben, 2)}


# ---------------------------------------------------------------- LOI NHAC + CHAN DOAN
_HE = ("Ban la nha nghien cuu dinh luong KHAT KHE. Doc MOT tai lieu va tra DUNG MOT object JSON (khong markdown, khong loi giai) de tim thu "
       "DANG RA TIEN, khong de khen ngoi tai lieu. Chi tieu duy nhat: tai lieu nay co chi ra mot CO CHE KINH TE that (ai tra tien, vi sao ho cam "
       "chiu lo, vi sao khong bi bao hoa) khong, va co the thu lai tren GIA cua ta (FX, chi so, hang hoa, kim loai; nen phut / gio / ngay; "
       "khong co tick, so lenh, quyen chon, cat ngang co phieu). TIEU CHI DUYET CUA CHU DU AN la tien: co lai sau phi + maxDD < 80%, "
       "KHONG phai su thanh khiet hoc thuat. Vi vay QUAN LI LENH (luoi, DCA, martingale, hedging, cat lo / chot theo tai khoan) la mot CO CHE HOP LE "
       "(loai_co_che = quan_li_lenh), khong duoc gan 'khong_co_co_che' chi vi khong co ly thuyet: co che cua no la hinh dang loi nhuan (nhieu "
       "lan thang nho, duoi lo hiem) va viec CHON tai san noi gia hay quay ve; chi ghi dau hieu do neu thieu so lieu / phi / duoi rui ro, va "
       "trong `suy_ra` hay chi tai san / khung noi hinh dang do CO THE tra tien (vd cap tien it xu huong) kem cach bac bo bang so.")


def loi_nhac(van_ban: str, nguon: str, bai_hoc_txt: str = "") -> str:
    mau = {"co_che": "...>=25 ky tu: AI tra tien va VI SAO",
           "lop_tai_san": "|".join(LOP_TAI_SAN), "khung": "|".join(KHUNG), "loai_co_che": "|".join(LOAI_CO_CHE),
           "loi_nhuan_cong_bo": {"pct_nam": "so hoac null", "sau_phi": "true|false|null", "ngoai_mau": "true|false|null"},
           "du_lieu_can": ["tap con cua: " + ",".join(DU_LIEU)],
           "dau_hieu_do": ["tap con cua: " + ",".join(DAU_HIEU_DO) + " (rong neu khong thay)"],
           "suy_ra": [{"lop_tai_san": "...", "khung": "...", "chieu": "1|-1|0", "vi_sao_tra_tien": "...>=20 ky tu",
                       "cach_bac_bo": "...>=20 ky tu: ket qua nao chung to y tuong SAI o cho nay"}]}
    return ("NGUON: %s\n%s\nTAI LIEU:\n%s\n\nQUY TAC: (1) `loi_nhuan_cong_bo` chi dien so tac gia NEU tai lieu viet ro; khong doan. (2) `dau_hieu_do`: "
            "khong tinh phi, chi trong mau, mau ngan, chon tham so sau khi thay du lieu, ngoai le rieng le, khong co co che, nhan nhu quang cao. "
            "(3) `suy_ra` = 0..6 cho KHAC nhau ma CHINH CO CHE NAY con dung (vd co che 'nguoi mua duoi cuoi phien bi am hoi' co dung o fix gio "
            "dong cua hang hoa, chi so, FX khong?) - moi cho phai nam trong tai san lab thu duoc, kem LY DO tra tien va CACH BAC BO. Khong dua cho "
            "chi vi cung loai tai san; khong dua cho chi de PHU DINH (chieu 0 + 'khong co co che' la vo ich: bo cho do). 0 cho cung duoc neu co che gan chat vao cau truc co phieu.\nMau: %s"
            % (nguon, bai_hoc_txt, van_ban[:6000], json.dumps(mau, ensure_ascii=False)))


def _json(s: str):
    s = s.strip()
    s = re.sub(r"^```(?:json)?|```$", "", s, flags=re.M).strip()
    i, j = s.find("{"), s.rfind("}")
    return json.loads(s[i:j + 1]) if i >= 0 and j > i else None


def chan_doan(van_ban: str, nguon: str, goi_llm, tai_lieu_id: str = "", da_thu: dict | None = None,
              vong_sua: int = 2, ghi_so: bool = True) -> dict:
    """goi_llm(he, nguoi) -> str. Tra {tai_lieu_id, nguon, the, loi, diem, so_vong} ; `the` None neu van sai sau `vong_sua` lan sua."""
    nguoi = loi_nhac(van_ban, nguon, bai_hoc_van_ban())
    loi: list[str] = []
    the = None
    for vong in range(vong_sua + 1):
        tra = goi_llm(_HE, nguoi if not loi else nguoi + "\n\nLAN TRUOC SAI: " + "; ".join(loi[:6]) + "\nTra lai JSON day du da sua.")
        try:
            the = _json(tra)
        except Exception as e:
            the, loi = None, ["khong doc duoc JSON: %s" % str(e)[:80]]
            continue
        loi = kiem(chuan_hoa(the))
        if not loi:
            break
    kq = {"tai_lieu_id": tai_lieu_id or "tl-%d" % int(time.time()), "nguon": nguon, "the": the if not loi else None,
          "loi": loi, "so_vong": vong + 1}
    if not loi:
        kq["diem"] = diem_dang_tien(the, da_thu)
        for i, b in enumerate(the["suy_ra"]):
            b["bien_the_id"] = "%s#%d" % (kq["tai_lieu_id"], i)
    if ghi_so:
        ghi({"loai": "chan_doan", "t": time.strftime("%Y-%m-%dT%H:%M:%S"), **kq})
    return kq


# ---------------------------------------------------------------- SO CAI
def ghi(d: dict, so: Path | None = None) -> None:
    so = so or SO
    so.parent.mkdir(parents=True, exist_ok=True)
    with open(so, "a", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")


def doc_so(so: Path | None = None) -> list[dict]:
    so = so or SO
    if not so.exists():
        return []
    return [json.loads(x) for x in so.read_text(encoding="utf-8").splitlines() if x.strip()]


def ghi_ket_qua(bien_the_id: str, trang_thai: str, ky_vong_bps: float | None = None, cagr_pct: float | None = None,
                ghi_chu: str = "", so: Path | None = None) -> None:
    """Goi khi mot phuong phap suy ra da duoc thu (kham_pha) / xac nhan. trang_thai: DAT | AM | CHUA_DO_DUOC."""
    if trang_thai not in ("DAT", "AM", "CHUA_DO_DUOC"):
        raise ValueError("trang_thai phai la DAT | AM | CHUA_DO_DUOC")
    ghi({"loai": "ket_qua", "t": time.strftime("%Y-%m-%dT%H:%M:%S"), "bien_the_id": bien_the_id, "trang_thai": trang_thai,
         "ky_vong_bps": ky_vong_bps, "cagr_pct": cagr_pct, "ghi_chu": ghi_chu[:200]}, so)


# ---------------------------------------------------------------- HOC NGUOC
def _gop(so: Path | None = None):
    cd, kq = {}, defaultdict(dict)
    for r in doc_so(so):
        if r.get("loai") == "chan_doan" and r.get("the"):
            cd[r["tai_lieu_id"]] = r
        elif r.get("loai") == "ket_qua":
            kq[r["bien_the_id"]] = r      # ket qua moi nhat thang
    return cd, kq


def xep_nguon(so: Path | None = None, tien_nghiem: float = 10.0) -> list[dict]:
    """Xep nguon theo SUAT TIEN = (he DAT + 1) / (he DA THU + tien_nghiem): lam min de nguon moi khong bi 0 vinh vien.
    `chua_thu` = he suy ra chua co ket qua: khong tinh vao mau so (khong phat nguon vi viec cua ta chua chay)."""
    cd, kq = _gop(so)
    nguon = defaultdict(lambda: {"tai_lieu": 0, "diem_tb": 0.0, "da_thu": 0, "dat": 0, "am": 0, "chua_do_duoc": 0, "chua_thu": 0})
    for tl, r in cd.items():
        n = nguon[r["nguon"]]
        n["tai_lieu"] += 1
        n["diem_tb"] += (r.get("diem") or {}).get("diem", 0.0)
        for b in r["the"]["suy_ra"]:
            k = kq.get(b["bien_the_id"])
            if not k:
                n["chua_thu"] += 1
            elif k["trang_thai"] == "DAT":
                n["da_thu"] += 1; n["dat"] += 1
            elif k["trang_thai"] == "AM":
                n["da_thu"] += 1; n["am"] += 1
            else:
                n["chua_do_duoc"] += 1
    out = []
    for ten, n in nguon.items():
        n["diem_tb"] = round(n["diem_tb"] / max(1, n["tai_lieu"]), 1)
        n["suat_tien"] = round((n["dat"] + 1) / (n["da_thu"] + tien_nghiem), 3)
        out.append({"nguon": ten, **n})
    return sorted(out, key=lambda x: (-x["suat_tien"], -x["diem_tb"]))


def so_da_thu(so: Path | None = None) -> dict[str, int]:
    """So phuong phap da co ket qua (DAT/AM) theo loai co che - de do bao hoa trong `diem_dang_tien`."""
    cd, kq = _gop(so)
    dem: dict[str, int] = defaultdict(int)
    for r in cd.values():
        for b in r["the"]["suy_ra"]:
            if kq.get(b["bien_the_id"], {}).get("trang_thai") in ("DAT", "AM"):
                dem[r["the"]["loai_co_che"]] += 1
    return dict(dem)


def bai_hoc(so: Path | None = None, toi_thieu: int = 3) -> list[dict]:
    """Ty le DAT theo (loai_co_che, lop_tai_san) khi da co >= toi_thieu ket qua. Cho LLM lan sau biet cho nao hay chet."""
    cd, kq = _gop(so)
    nhom = defaultdict(lambda: [0, 0])
    for r in cd.values():
        for b in r["the"]["suy_ra"]:
            k = kq.get(b["bien_the_id"])
            if k and k["trang_thai"] in ("DAT", "AM"):
                nhom[(r["the"]["loai_co_che"], b["lop_tai_san"])][0] += k["trang_thai"] == "DAT"
                nhom[(r["the"]["loai_co_che"], b["lop_tai_san"])][1] += 1
    return sorted(({"loai_co_che": a, "lop_tai_san": b, "dat": d, "thu": n, "ty_le": round(d / n, 2)}
                   for (a, b), (d, n) in nhom.items() if n >= toi_thieu), key=lambda x: -x["ty_le"])


NEN = GOC / "reports" / "pheu_gia_tri" / "bai_hoc_nen.md"


def bai_hoc_van_ban(so: Path | None = None) -> str:
    """Bai hoc NEN (do tay, tu lab) + bai hoc TU KET QUA cua so nay. Dua vao loi nhac de LLM suy luan theo cai ta da biet."""
    nen = NEN.read_text(encoding="utf-8").strip() if NEN.exists() else ""
    nen = ("DIEU TA DA BIET TU LAB (dung de suy cho nao tra tien, khong de nhai lai):\n" + nen + "\n") if nen else ""
    bh = bai_hoc(so)
    if not bh:
        return nen
    xau = [x for x in bh if x["ty_le"] == 0][:4]
    tot = [x for x in bh if x["ty_le"] > 0][:4]
    dong = []
    if tot:
        dong.append("BAI HOC TU KET QUA THAT - cho hay ra tien: " + "; ".join("%s x %s (%d/%d)" % (x["loai_co_che"], x["lop_tai_san"], x["dat"], x["thu"]) for x in tot))
    if xau:
        dong.append("hay chet (0 DAT): " + "; ".join("%s x %s (0/%d)" % (x["loai_co_che"], x["lop_tai_san"], x["thu"]) for x in xau))
    return nen + "\n".join(dong)


def xep_viec(so: Path | None = None, toi_da: int = 20) -> list[dict]:
    """Phuong phap suy ra CHUA THU, xep theo diem tai lieu x suat tien nguon. Dau ra cho nguoi/cloud dat viec thu."""
    cd, kq = _gop(so)
    suat = {n["nguon"]: n["suat_tien"] for n in xep_nguon(so)}
    ds = []
    for tl, r in cd.items():
        for b in r["the"]["suy_ra"]:
            if b["bien_the_id"] in kq or kha_thi_mot(b["lop_tai_san"], b["khung"]) == 0.0:
                continue
            ds.append({"bien_the_id": b["bien_the_id"], "diem": round(r["diem"]["diem"] * (0.5 + suat.get(r["nguon"], 0.1)), 1),
                       "nguon": r["nguon"], "lop_tai_san": b["lop_tai_san"], "khung": b["khung"], "chieu": b["chieu"],
                       "vi_sao": b["vi_sao_tra_tien"], "bac_bo": b["cach_bac_bo"]})
    return sorted(ds, key=lambda x: -x["diem"])[:toi_da]


# ---------------------------------------------------------------- RA VIEC (quan li lenh -> quet luoi, khong can LLM)
MA_THEO_LOP = {"fx": "AUDCAD", "kim_loai": "XAUUSDM", "chi_so": "US500CASH", "hang_hoa": "XTIUSD"}
KHUNG_MT5 = {"phut": "M15", "gio": "H1", "ngay": "D1"}


def viec_luoi(b: dict, uu_tien: int = 3) -> dict | None:
    """Phuong phap suy ra thuoc quan li lenh (luoi / DCA) -> don `quet_luoi` mot chieu mua + ban rieng. None neu khong gan duoc ma / khung.
    Moi tham so quet la mot phep thu (so_phep_thu tinh trong cong cu), khong them cong quet moi."""
    ma, kh = MA_THEO_LOP.get(b.get("lop_tai_san")), KHUNG_MT5.get(b.get("khung"))
    if not ma or not kh:
        return None
    return {"ma": "pgt-%s-%s-%s" % (b["bien_the_id"].replace("#", "-"), ma, kh), "lan": "CPU", "uu_tien": uu_tien, "han_phut": 60.0,
            "muc_tieu": "PHEU GIA TRI: %s - luoi mot chieu (mua, ban) tren %s %s (kham_pha)" % (b["bien_the_id"], ma, kh),
            "vi_sao": b["vi_sao_tra_tien"][:200], "cong": {"kieu": "chay_duoc"},
            "lenh": ["{py}", "b.py", "nc", "cc", "quet_luoi", json.dumps(
                {"ma": ma, "khung": kh, "luoi": {"che_do": ["mua", "ban"], "buoc": [30, 60, 100, 150], "tp": [30, 60, 100],
                                                 "kieu_lot": ["phang", "cong"]},
                 "co_dinh": {"tran_tang": 20, "he_so_lot": 0.5}, "toi_da_o": 100, "von": 10000})]}
