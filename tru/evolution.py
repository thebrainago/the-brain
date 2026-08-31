# -*- coding: utf-8 -*-
"""evolution.py - TRU EVOLUTION. Giam sat, nhin ra van de, tu cai tien.

Khac ban cu (`evo_giam_sat.py` chay 8.413 lan/5,3 gio, moi 2,3 giay ghi de mot
bao cao khong ai doc): o day EVO do SUC KHOE DAY CHUYEN, khong do "so PASS".

THIET_KE muc 12 - ba tang do:
  1. Placebo FDR   : ty le placebo vuot toan bo cong. Lech target = dang san
                     xuat phat hien sai.
  2. Sai so ngoai mau chuan hoa: z = (OOS thuc - du bao)/sd. Khong xap xi N(0,1)
                     = dang uoc luong sai do khong chac chan.
  3. Hieu chuan nhom live: % chien luoc da chay nam ngoai khoang du bao 95%.

Va bon phep do VAN HANH ma bao cao 15/08 chi ra la thieu:
  4. Ty le vong lap rong  : lan chay khong sinh ra gi / tong lan chay.
  5. Tuoi du lieu tung tru: tru nao dang dung im.
  6. Toan ven so         : chuoi hash co dut khong.
  7. Tai nguyen          : dia, viec treo, viec loi.

EVO duoc phep TU SUA nhung viec da khai bao truoc (danh sach `TU_SUA_DUOC`).
Viec ngoai danh sach -> chi ghi van de, cho nguoi. Khong tu y sua code.

NANG CAP 31/08/2026 - KHU TRUNG VAN DE THEO NOI DUNG.

`phan_tich_sau` danh ma van de bang `SO.van_tay(van_ban)[:10]`, tuc BAM CUA
CHUOI. Cung mot phat hien dien dat khac di mot chu la thanh mot van de moi.
Do that tren so ngay 31/08: 25 van de dang mo, 12 trong so do la `llm_<bam>`
va chung noi trung nhau ve DUNG BA chuyen ("nha may null qua nho", "phan phoi
p cua ung vien lech khoi null", "cong loai sach gia thuyet da vuot FDR") -
moi luot chan doan 6 gio lai de ra mot ma bam moi.

Cach sua: mot phat hien = mot ma CHU DE CHUAN (`CHU_DE_VAN_DE`), va lan sau
gap lai thi TANG SO LAN TAI PHAT chu khong de dong moi. Ba tang nhan dang, tu
chac chan xuong:

  1. `CHU_DE_VAN_DE` - chu ky khai bao tay (VA cua cac nhom tu dong nghia).
     Chinh xac cao, kiem lai duoc bang mat.
  2. Do trung voi van de DANG MO bang Jaccard tren tap tu da chuan hoa
     (nguong `NGUONG_TRUNG`). Bat nhung dien dat lech nhau it.
  3. Bam cua TAP TU da chuan hoa (bo dau, bo so, bo tu dem). Hai cau khac nhau
     thu tu tu hoac khac con so van ra cung ma.

Rieng tang 2 va 3 KHONG bao gio gop hai van de da co ma chuan khac nhau: chu
de chuan luon thang. Do la de mot phat hien that khong bi nuot vao mot phat
hien khac chi vi dung nhieu tu giong nhau.
"""
from __future__ import annotations

import ctypes
import json
import re
import shutil
import sys
import time
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nhan import (do_tai_nguyen as DTN, ket_qua_hoat_dong as KQHD,
                  san_cong_cu as SCC, so as SO, tri_tue as TT)

TRU = "EVO"
LAB = Path(__file__).resolve().parent.parent
REPORTS = LAB / "reports"
TRU_CAN_SONG = ["SEEKER", "QUANTLAB", "NGHI", "BANKER", "EVO"]
HAN_DUNG_IM = {"SEEKER": 3 * 3600, "QUANTLAB": 2 * 3600, "NGHI": 6 * 3600,
               "BANKER": 12 * 3600, "EVO": 3600}

TU_SUA_DUOC = {
    "don_viec_treo": "chuyen viec CHAY mo coi thanh LOI",
    "don_cache_khung": "xoa cache khung cu khi dia thap",
    "xep_lai_viec_loi": "xep lai viec LOI duoi 3 lan thu",
    "gian_nguon_chet": "gian chu ky nguon loi lien tuc (tru/seeker.py da tu gian "
                       "bang he so 2**loi_lien_tuc; EVO chi theo doi va bao)",
    "dong_van_de_da_het": "dong van de cua chinh EVO khi dieu kien khong con dung",
    # --- them 31/08/2026. Ca hai deu DAO NGUOC DUOC va khong cham duong
    # quyet dinh: mot cai doi truong `ma`/`bang_chung` cua bang `van_de`, mot
    # cai doi truong `trang_thai` trong `reports/cong_cu.json`. Khong cai nao
    # dong toi ma nguon, nguong, hay mot con so thong ke nao.
    "gop_van_de_trung_lap": "gop van de LLM trung NOI DUNG ve mot ma chu de "
                            "chuan; ban goc giu lai trong so de mo lai duoc",
    "xep_hang_doc_cong_cu": "danh dau kho ma trong HANG_DOI_DOC la CHO_DOC de "
                            "nguoi doc doi chieu voi cong - khong tich hop gi",
}


# =================================================== KHU TRUNG VAN DE THEO NOI DUNG
#: CHU DE CHUAN. Moi muc: `(ma, [nhom1, nhom2, ...])`.
#: Khop khi MOI nhom co it nhat mot bien the xuat hien trong van ban da chuan
#: hoa (VA cua cac OR). Thu tu trong danh sach la thu tu xet - muc dung truoc
#: thang.
#:
#: Cac cum duoi day duoc rut tu 15 dong `llm_*` co that trong so ngay 31/08.
#: Nguyen tac: mot chu de phai co it nhat HAI nhom rang buoc. Mot nhom don
#: (vi du chi "null") se nuot nhung phat hien khac han nhau.
CHU_DE_VAN_DE: list[tuple[str, list[list[str]]]] = [
    ("vd_null_qua_nho",
     [["nha may null", "null factory"],
      ["qua nho", "khong dai dien", "khong du de"]]),
    ("vd_p_ung_vien_lech_null",
     [["phan phoi p", "p cua ung vien", "p-value cua ung vien"],
      ["ung vien", "null"]]),
    ("vd_cong_loai_sach_fdr",
     [["vuot fdr", "qua fdr", "song sot kiem soat"],
      ["cong loai", "loai bo", "loai sach", "bi cong", "khong co gi di ra",
       "khong di duoc ra"]]),
    ("vd_so_sach_khong_khop",
     [["so sach", "so lieu", "mau thuan"],
      ["khong khop", "mau thuan", "giua cac tang", "ba tang", "tang dem"]]),
    ("vd_duong_du_phong",
     [["du phong", "du_phong"], ["ket qua", "duong"]]),
    ("vd_nguon_im_lang",
     [["nguon"], ["loi im", "im lang", "khong thu duoc", "khong thu hoach"]]),
    ("vd_tick_test_bi_khoa",
     [["tick-test", "tick test", "mt5"], ["bi khoa", "dang khoa", "dia"]]),
]

#: Tu khong mang thong tin phan biet. Bo truoc khi bam / do trung.
TU_DEM = {
    "va", "voi", "cua", "cho", "co", "khong", "la", "mot", "cac", "nhung",
    "nay", "do", "thi", "ma", "de", "duoc", "bi", "tren", "trong", "tu",
    "den", "ra", "vao", "khi", "neu", "hay", "hoac", "ca", "chi", "nhu",
    "the", "nao", "gi", "day", "kia", "se", "dang", "da", "chua", "van",
    "lan", "so", "phai", "con", "chan", "doan", "llm", "muc",
}

#: Nguong Jaccard de coi hai phat hien la MOT. Dat cao co chu y: gop nham hai
#: phat hien khac nhau la mat mot phat hien, con khong gop duoc thi chi la mot
#: dong thua - hai loi khong ngang gia.
NGUONG_TRUNG = 0.60

_KY_TU = re.compile(r"[^a-z0-9\s]+")
_SO = re.compile(r"\b\d[\d.,%]*\b")


def khong_dau(s: str) -> str:
    """Bo dau tieng Viet + ha chu thuong. `d`/`D` gach ngang thanh `d`."""
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def chuan_hoa(s: str) -> str:
    """Van ban da bo dau, bo dau cau, bo so. Dung de KHOP CUM."""
    s = khong_dau(s)
    s = _SO.sub(" ", s)
    s = _KY_TU.sub(" ", s)
    return " ".join(s.split())


def tap_tu(s: str) -> frozenset:
    """Tap tu con lai sau khi bo tu dem. Dung de DO TRUNG va de BAM."""
    return frozenset(t for t in chuan_hoa(s).split()
                     if len(t) > 1 and t not in TU_DEM)


def trung_nhau(a: frozenset, b: frozenset) -> float:
    """Jaccard. Tra 0.0 khi mot ben rong - khong phai 1.0."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def chu_de_van_de(van_ban: str) -> str | None:
    """Van ban nay thuoc chu de chuan nao? `None` khi khong chu de nao khop."""
    s = chuan_hoa(van_ban)
    for ma, nhom in CHU_DE_VAN_DE:
        if all(any(chuan_hoa(x) in s for x in nhom_con) for nhom_con in nhom):
            return ma
    return None


def ma_chuan_van_de(mo_ta: str, bang_chung: str = "",
                    dang_mo: list[dict] | None = None) -> str:
    """Ma chuan cho MOT phat hien. Cung phat hien -> cung ma, du dien dat khac.

    Ba tang, tang tren thang tang duoi (xem docstring dau module).
    """
    ma = chu_de_van_de(mo_ta) or chu_de_van_de(f"{mo_ta} {bang_chung}")
    if ma:
        return ma
    tt = tap_tu(mo_ta)
    # Tang 2: trung voi mot van de dang mo. Chi so voi van de do CHINH duong
    # nay sinh ra (`llm_`/`vd_`); khong bao gio nuot mot ma nguoi dat.
    tot, diem = None, 0.0
    for v in (dang_mo or []):
        if not str(v.get("ma", "")).startswith(("llm_", "vd_")):
            continue
        d = trung_nhau(tt, tap_tu(v.get("mo_ta") or ""))
        if d > diem:
            tot, diem = v["ma"], d
    if tot and diem >= NGUONG_TRUNG:
        return tot
    # Tang 3: bam tren TAP TU da chuan hoa, khong phai tren chuoi tho.
    return "llm_" + SO.van_tay("|".join(sorted(tt)))[:10]


_THU_TU_MUC = {"NANG": 0, "VUA": 1, "NHE": 2}


def _muc_cao_hon(a: str, b: str) -> str:
    return a if _THU_TU_MUC.get(a, 9) <= _THU_TU_MUC.get(b, 9) else b


def _doc_bang_chung(row: dict) -> dict:
    try:
        d = json.loads(row.get("bang_chung") or "{}")
        return d if isinstance(d, dict) else {"bang_chung": d}
    except Exception:
        return {}


def bao_van_de_gop(muc: str, mo_ta: str, bang_chung: dict | None = None,
                   dang_mo: list[dict] | None = None) -> tuple[str, str]:
    """Bao mot phat hien. Trung NOI DUNG voi van de dang mo -> DEM TAI PHAT.

    Tra `(ma, "MOI" | "TAI_PHAT")`. Khong bao gio de ra mot dong moi cho cung
    mot phat hien: do la ly do so van de phinh tu 3 chuyen len 12 dong.
    """
    dang_mo = SO.van_de_mo() if dang_mo is None else dang_mo
    ma = ma_chuan_van_de(mo_ta, json.dumps(bang_chung or {}, ensure_ascii=False,
                                           default=str), dang_mo)
    cu = next((v for v in dang_mo if v.get("ma") == ma), None)
    luc = SO.bay_gio()
    if cu is None:
        bc = dict(bang_chung or {})
        bc.update({"so_lan_tai_phat": 1, "lan_dau": luc, "lan_gan_nhat": luc,
                   "cac_dien_dat": [mo_ta[:200]]})
        SO.bao_van_de(ma, muc, mo_ta, bc)
        return ma, "MOI"
    bc = _doc_bang_chung(cu)
    bc.update(bang_chung or {})
    bc["so_lan_tai_phat"] = int(bc.get("so_lan_tai_phat") or 1) + 1
    bc.setdefault("lan_dau", cu.get("phat_hien_luc") or luc)
    bc["lan_gan_nhat"] = luc
    dd = [x for x in (bc.get("cac_dien_dat") or []) if x]
    if mo_ta[:200] not in dd:
        dd.append(mo_ta[:200])
    bc["cac_dien_dat"] = dd[-8:]
    SO.chay("UPDATE van_de SET muc=?, bang_chung=? WHERE id=?",
            _muc_cao_hon(cu.get("muc") or muc, muc),
            json.dumps(bc, ensure_ascii=False, default=str)[:3000], cu["id"])
    return ma, "TAI_PHAT"


def gop_van_de_trung_lap() -> list[str]:
    """TU SUA (da khai bao): gop cac dong `llm_*` dang mo noi CUNG mot chuyen.

    RANH GIOI - chi dong vao dong co ma bat dau bang `llm_` (do CHINH duong
    chan doan LLM cua EVO sinh ra). Van de do nguoi hoac do tru khac dat ten
    khong bao gio bi cham toi.

    DAO NGUOC DUOC: dong bi gop khong bi xoa. No o lai trong `van_de` voi
    nguyen van cu, `trang_thai='DA_SUA'` va `hanh_dong` ghi ro no da gop vao
    ma nao. Mo lai la mot cau UPDATE.
    """
    mo = [v for v in SO.van_de_mo() if str(v.get("ma", "")).startswith("llm_")]
    if len(mo) < 2:
        return []
    nhom: dict[str, list[dict]] = {}
    for v in sorted(mo, key=lambda x: x["id"]):
        ma = chu_de_van_de(v.get("mo_ta") or "") or \
            chu_de_van_de(f"{v.get('mo_ta')} {v.get('bang_chung')}")
        if not ma:
            # Khong co chu de chuan -> do trung voi cac dong da xet trong nhom.
            tt = tap_tu(v.get("mo_ta") or "")
            ma = next((k for k, ds in nhom.items()
                       if trung_nhau(tt, tap_tu(ds[0].get("mo_ta") or ""))
                       >= NGUONG_TRUNG), None)
            if not ma:
                ma = "llm_" + SO.van_tay("|".join(sorted(tt)))[:10]
        nhom.setdefault(ma, []).append(v)

    da_lam = []
    for ma, ds in nhom.items():
        if len(ds) < 2 and ds[0]["ma"] == ma:
            continue                      # da dung ma chuan va khong trung ai
        giu = ds[0]                       # dong CU NHAT lam dai dien
        bc = _doc_bang_chung(giu)
        dien_dat, bang_chung_con = [], []
        for v in ds:
            if (v.get("mo_ta") or "")[:200] not in dien_dat:
                dien_dat.append((v.get("mo_ta") or "")[:200])
            b = _doc_bang_chung(v).get("bang_chung")
            if b and b not in bang_chung_con:
                bang_chung_con.append(str(b)[:300])
        bc.update({
            "so_lan_tai_phat": len(ds),
            "lan_dau": ds[0].get("phat_hien_luc"),
            "lan_gan_nhat": ds[-1].get("phat_hien_luc"),
            "cac_dien_dat": dien_dat[-8:],
            "cac_bang_chung": bang_chung_con[-4:],
            "gop_tu": [v["ma"] for v in ds],
        })
        muc = ds[0].get("muc") or "NHE"
        for v in ds[1:]:
            muc = _muc_cao_hon(muc, v.get("muc") or "NHE")
        SO.chay("UPDATE van_de SET ma=?, muc=?, bang_chung=? WHERE id=?",
                ma, muc, json.dumps(bc, ensure_ascii=False, default=str)[:3000],
                giu["id"])
        for v in ds[1:]:
            SO.chay("UPDATE van_de SET trang_thai='DA_SUA', hanh_dong=?, sua_luc=? "
                    "WHERE id=?",
                    f"gop vao `{ma}` (khu trung theo noi dung 31/08; ban goc giu "
                    "nguyen van, mo lai bang UPDATE trang_thai='MO')",
                    SO.bay_gio(), v["id"])
        if len(ds) > 1:
            da_lam.append(f"{ma} <- {len(ds)} dong ({', '.join(v['ma'] for v in ds)})")
        else:
            da_lam.append(f"{ma} <- doi ten tu {ds[0]['ma']}")
    return da_lam


#: Nhat ky watchdog. `tru/evolution.py` doc DE DEM, khong bao gio ghi.
NHAT_KY_WATCHDOG = LAB / "reports" / "watchdog.log"

#: Bao nhieu lan supervisor khoi dong lai trong 24 gio thi coi la HONG.
#: Do that 31/08/2026: **~12 lan/gio** (supervisor chet moi 4-5 phut vi
#: `os.replace` len file lease dang bi watchdog mo - WinError 5 tren Windows),
#: va khong mot phep do nao cua EVO nhin thay. EVO chi bao "thoi gian song 7
#: ngay 0,0%" ma khong noi duoc VI SAO. Mot lan restart mot ngay la binh
#: thuong (may ngu, cap nhat); ba lan tro len la co chuyen.
TRAN_RESTART_24H = 3

_DONG_WATCHDOG = re.compile(
    r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\s+WATCHDOG\s+(.*)$")


def do_watchdog(gio: int = 24) -> dict:
    """Supervisor da chet va khoi dong lai bao nhieu lan trong `gio` gio qua?

    Tra `so_lan=None` khi khong doc duoc nhat ky - **khong tra 0**. "Chua do
    duoc" va "do roi, khong lan nao" la hai cau khac han, va du an nay da
    nham chung ba lan trong mot phien (`da_quet=0` bao thanh "khong bo nao
    thang"). Mot nhat ky watchdog vang mat co the nghia la watchdog chua bao
    gio chay - do la tin XAU, khong phai tin tot.
    """
    if not NHAT_KY_WATCHDOG.exists():
        return {"so_lan": None, "ly_do": "khong co reports/watchdog.log"}
    try:
        van = NHAT_KY_WATCHDOG.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"so_lan": None, "ly_do": f"{type(e).__name__}"}
    moc = datetime.now() - timedelta(hours=gio)
    chet, rc, cuoi = 0, {}, None
    for dong in van.splitlines():
        m = _DONG_WATCHDOG.match(dong.strip())
        if not m:
            continue
        try:
            luc = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        noi = m.group(2)
        if luc < moc:
            continue
        if "supervisor thoat" in noi:
            chet += 1
            cuoi = m.group(1)
            k = re.search(r"rc=(-?\d+)", noi)
            if k:
                rc[k.group(1)] = rc.get(k.group(1), 0) + 1
    return {"so_lan": chet, "gio": gio, "theo_rc": rc, "lan_cuoi": cuoi,
            "moi_gio": round(chet / gio, 2) if gio else None}


def dia_trong_gb() -> float:
    try:
        return shutil.disk_usage("C:/").free / (1024 ** 3)
    except Exception:
        return 99.0


# ------------------------------------------------------------- CAC PHEP DO
def do_suc_khoe_day_chuyen() -> dict:
    """Tang 1: dang san xuat phat hien that hay phat hien sai?"""
    ra = {}
    # MOI PHEP THU = MOI GIA THUYET (dong ket qua MOI NHAT `.superseded_by IS NULL`).
    # Truoc day `so_ket_qua` dem CA dong chay lai -> roi `theo_verdict`/`ty_le_qua_cong`
    # lai bo superseded -> tu so va mau so dem khac don vi, khong the thao hiep.
    ra["so_ket_qua_tho"] = SO.mot("SELECT COUNT(*) n FROM ket_qua")["n"]
    ra["so_ket_qua_du_phong"] = SO.mot(
        "SELECT COUNT(*) n FROM ket_qua WHERE superseded_by IS NOT NULL")["n"]
    theo = {r["verdict"]: r["n"] for r in SO.nhieu(KQHD.truy_van(
        "k.verdict, COUNT(*) n", nhom_theo="k.verdict"))}
    ra["so_ket_qua"] = sum(theo.values())   # so gia thuyet MOI NHAT dang co ket qua
    ra["so_gt_da_ket"] = ra["so_ket_qua"]
    ra["theo_verdict"] = theo
    qua = sum(theo.get(k, 0) for k in ("PASS", "UNG_VIEN"))
    ra["ty_le_qua_cong"] = round(qua / max(ra["so_gt_da_ket"], 1), 4)

    # HIEU CHUAN dung cach: do ty le LOT cua NULL FACTORY (thu khong co edge),
    # KHONG do bang phan phoi p cua cac ung vien da chon loc.
    # Ung vien duoc chon vi thang mua-giu tren train -> p cua chung LE RA phai
    # lech thap; lech thap o do khong chung minh duoc gi ca.
    nl = SO.mot("SELECT gia_tri, chi_tiet, luc FROM chi_so_vh WHERE ten='null_ty_le_lot' "
                "ORDER BY id DESC LIMIT 1")
    if nl:
        ra["null_ty_le_lot"] = round(nl["gia_tri"], 4)
        ra["null_do_luc"] = nl["luc"]
        try:
            ra["null_chi_tiet"] = json.loads(nl["chi_tiet"] or "{}")
        except Exception:
            pass
    else:
        ra["null_ty_le_lot"] = None

    # CHIEU CON LAI cua hieu chuan: cong co cho thu CO edge di qua khong.
    # Thieu so nay thi "null lot 0%" khong phan biet duoc voi "tu choi tat ca".
    lc = SO.mot("SELECT gia_tri, chi_tiet, luc FROM chi_so_vh WHERE ten='cong_co_luc' "
                "ORDER BY id DESC LIMIT 1")
    if lc:
        ra["cong_co_luc"] = bool(lc["gia_tri"])
        ra["cong_co_luc_luc"] = lc["luc"]
        try:
            ra["cong_co_luc_chi_tiet"] = json.loads(lc["chi_tiet"] or "{}").get("ket")
        except Exception:
            pass
    else:
        ra["cong_co_luc"] = None

    # Doc them: p cua ung vien - chi de THAM KHAO, khong dung lam cong.
    ps = [r["p_placebo"] for r in SO.nhieu(KQHD.truy_van(
        "k.p_placebo",
        dieu_kien_them="k.p_placebo IS NOT NULL AND k.gt_ma NOT LIKE 'NULL.%'",
    )) if r["p_placebo"]]
    if len(ps) >= 20:
        import numpy as np
        ra["ung_vien_n"] = len(ps)
        ra["ung_vien_p_trung_vi"] = round(float(np.median(ps)), 4)
        ra["ung_vien_duoi_005"] = round(float(np.mean(np.array(ps) <= 0.05)), 4)
    # Chi dem FDR cho GIẢ THUYẾT DA DANG KY (JOIN gia_thuyet). Probe hieu chuan
    # (NULL.*, LUC.*...) khong phai giả thuyết -> khong duoc phong "so bi bac bo".
    # Chi doi soat FDR cua gia thuyet co ket qua DANG HOAT DONG; slot lich su
    # cua hypothesis quarantine van o lai trong so, nhung khong the lam lech
    # suc khoe day chuyen hien tai.
    fdr_nguon = KQHD.tu_ket_qua_hoat_dong(join_them="JOIN fdr f ON f.gt_ma=k.gt_ma")
    ra["fdr_da_bac_bo"] = SO.mot(
        "SELECT COUNT(DISTINCT f.gt_ma) n " + fdr_nguon + " AND f.bac_bo=1")["n"]
    ra["fdr_tong"] = SO.mot(
        "SELECT COUNT(DISTINCT f.gt_ma) n " + fdr_nguon)["n"]
    ra["fdr_tong_tho"] = SO.mot("SELECT COUNT(*) n FROM fdr")["n"]
    # Dong bo ba tang: moi giả thuyết co ket qua cuoi phai vao dung 1 FDR.
    # `khop`=True khi dem theo giả thuyết o tang ket_qua va tang fdr bang nhau.
    ra["khop_ba_tang"] = bool(ra["so_gt_da_ket"] == ra["fdr_tong"])
    return ra


def do_van_hanh() -> dict:
    """Tang 4-7: day chuyen co dang BAN RON MA KHONG LAM GI khong?"""
    ra = {"luc": SO.bay_gio()}
    nhip = {n["tru"]: n for n in SO.doc_nhip()}
    ra["tru"] = {}
    for t in TRU_CAN_SONG:
        n = nhip.get(t)
        if not n:
            ra["tru"][t] = {"trang_thai": "CHUA CHAY LAN NAO"}
            continue
        try:
            tre = (datetime.now() - datetime.strptime(n["luc"], "%Y-%m-%d %H:%M:%S")).total_seconds()
        except Exception:
            tre = 1e9
        ra["tru"][t] = {"lan_cuoi": n["luc"], "tre_giay": int(tre),
                        "trang_thai": n["trang_thai"],
                        "dung_im": tre > HAN_DUNG_IM.get(t, 3600)}

    # TAI NGUYEN VAN HANH. Ba loi lam dung day chuyen ngay 30/08 deu khong bao
    # mot loi nao; cach duy nhat bat duoc chung la DO. Xem nhan/do_tai_nguyen.py.
    try:
        ra["tai_nguyen"] = DTN.tat_ca()
    except Exception as e:
        ra["tai_nguyen"] = {"loi": f"{type(e).__name__}: {str(e)[:60]}"}

    # THONG LUONG DOC: bao nhieu ban doc / bao nhieu hong trong 20 luot gan nhat.
    doc = SO.nhieu("SELECT gia_tri FROM chi_so_vh WHERE ten='seeker_doc_toan_van' "
                   "ORDER BY id DESC LIMIT 20")
    if doc:
        ra["doc_toan_van_20_luot"] = sum(float(d["gia_tri"] or 0) for d in doc)

    v = SO.dem_viec()
    ra["viec"] = v
    ra["viec_treo"] = sum(x.get("CHAY", 0) for x in v.values())
    ra["viec_loi"] = sum(x.get("LOI", 0) for x in v.values())
    ra["viec_cho"] = sum(x.get("CHO", 0) for x in v.values())

    # vong lap rong: lan chay SEEKER khong thu duoc tai lieu moi
    gan = SO.nhieu("SELECT gia_tri FROM chi_so_vh WHERE ten='seeker_tai_lieu_moi' "
                   "ORDER BY id DESC LIMIT 50")
    if gan:
        rong = sum(1 for g in gan if (g["gia_tri"] or 0) <= 0)
        ra["seeker_ty_le_vong_rong"] = round(rong / len(gan), 3)

    # THOI GIAN SONG THAT. "Chay 24/7" phai do bang gio, khong phai bang y dinh:
    # so cai co lo hong 00:15 -> 08:35 ngay 16/08 vi may ngu, va khong mot phep
    # do nao cua ban cu thay dieu do.
    gd = SO.nhieu("SELECT gia_tri, luc FROM chi_so_vh WHERE ten='gian_doan_gio' "
                  "AND luc >= datetime('now','-7 days') ORDER BY id DESC")
    ra["gian_doan_7ngay_gio"] = round(sum(float(g["gia_tri"] or 0) for g in gd), 1)
    ra["gian_doan_lan"] = len(gd)
    ra["ty_le_song_7ngay"] = round(max(0.0, 1 - ra["gian_doan_7ngay_gio"] / (7 * 24)), 4)

    # SUPERVISOR CO DANG CHET LIEN TUC KHONG. `ty_le_song_7ngay` noi duoc
    # "mat bao nhieu gio" nhung KHONG noi duoc VI SAO - va do dung la cho EVO
    # mu ngay 31/08: supervisor chet moi 4-5 phut, chi hien ra duoi dang rc=1,
    # khong mot traceback nao ton tai o dau ca.
    ra["watchdog"] = do_watchdog()

    ra["dia_trong_gb"] = round(dia_trong_gb(), 1)
    ra["mt5_tick_test"] = "GO" if ra["dia_trong_gb"] >= 15 else "KHOA (dia < 15GB)"
    lanh, mo_ta = SO.kiem_chuoi_hash()
    ra["so_toan_ven"] = {"lanh": lanh, "mo_ta": mo_ta}

    ng = SO.nhieu("SELECT ma,so_lan,so_loi,loi_lien_tuc,thu_hoach,trang_thai FROM nguon")
    ra["nguon"] = {n["ma"]: {"lan": n["so_lan"], "loi": n["so_loi"],
                             "thu_hoach": n["thu_hoach"], "trang_thai": n["trang_thai"]}
                   for n in ng}
    ra["tai_lieu"] = SO.mot("SELECT COUNT(*) n FROM tai_lieu")["n"]
    ra["gia_thuyet"] = {r["trang_thai"]: r["n"] for r in SO.nhieu(
        "SELECT trang_thai, COUNT(*) n FROM gia_thuyet GROUP BY trang_thai")}
    return ra


# ------------------------------------------------------------- PHAT HIEN
def phat_hien(vh: dict, sk: dict) -> list[dict]:
    ra = []

    for t, d in vh["tru"].items():
        if d.get("trang_thai") == "CHUA CHAY LAN NAO":
            ra.append({"ma": f"tru_chua_chay_{t}", "muc": "VUA",
                       "mo_ta": f"Tru {t} chua chay lan nao ke tu khi dung so moi", "bc": d})
        elif d.get("dung_im"):
            ra.append({"ma": f"tru_dung_im_{t}", "muc": "NANG",
                       "mo_ta": f"Tru {t} dung im {d['tre_giay']//60} phut "
                                f"(han {HAN_DUNG_IM.get(t,3600)//60} phut)", "bc": d})

    if not vh["so_toan_ven"]["lanh"]:
        ra.append({"ma": "so_dut_chuoi", "muc": "NANG",
                   "mo_ta": "Chuoi hash cua so bi dut - co dong bi sua hoi to",
                   "bc": vh["so_toan_ven"]})

    if vh["dia_trong_gb"] < 15:
        ra.append({"ma": "dia_thap", "muc": "NANG",
                   "mo_ta": f"Dia con {vh['dia_trong_gb']} GB (< 15) -> MT5 tick-test bi KHOA, "
                            "tuc dang tu cam minh lam buoc quyet dinh cua chinh du an",
                   "bc": {"goi_y": "lab/.browser_thebrain2 (848MB, INVENTORY ghi la mo nham), "
                                   "lab/.browser_darwinex_tmp (480MB tmp)"}})

    if vh.get("seeker_ty_le_vong_rong", 0) > 0.8:
        ra.append({"ma": "vong_lap_rong", "muc": "VUA",
                   "mo_ta": f"{vh['seeker_ty_le_vong_rong']:.0%} lan chay SEEKER khong thu duoc "
                            "gi moi - chu ky nguon dang qua day so voi toc do nguon cap nhat",
                   "bc": {"ty_le": vh["seeker_ty_le_vong_rong"]}})

    # --- tai nguyen van hanh -------------------------------------------
    tn = vh.get("tai_nguyen") or {}
    so_tab = (tn.get("tab") or {}).get("so_tab")
    if isinstance(so_tab, int) and so_tab > TRAN_TAB_BAO_DONG:
        ra.append({"ma": "trinh_duyet_phinh_tab", "muc": "NANG",
                   "mo_ta": f"Chrome bot dang mo {so_tab} tab (tran bao dong "
                            f"{TRAN_TAB_BAO_DONG}). Da sap that 30/08: 356 tab lam "
                            "luot keo toan van dung han 10 phut MA KHONG BAO LOI. "
                            "Chay `doc_trinh_duyet.don_tab_ngay()`.",
                   "bc": tn.get("tab")})

    gb = (tn.get("chrome") or {}).get("gb")
    if isinstance(gb, (int, float)) and gb > TRAN_RAM_CHROME_GB:
        ra.append({"ma": "trinh_duyet_ngon_ram", "muc": "VUA",
                   "mo_ta": f"Chrome bot chiem {gb} GB (tran {TRAN_RAM_CHROME_GB} GB)",
                   "bc": tn.get("chrome")})

    if isinstance(tn.get("ram_trong_gb"), (int, float)) and tn["ram_trong_gb"] < 3.0:
        ra.append({"ma": "ram_may_sap_het", "muc": "NANG",
                   "mo_ta": f"RAM trong chi con {tn['ram_trong_gb']} GB",
                   "bc": {"ram_dung_pct": tn.get("ram_dung_pct")}})

    # SUPERVISOR CHET LIEN TUC. Phan biet ba trang thai, khong gop:
    #   so_lan = None  -> CHUA DO DUOC (khong co nhat ky) -> van de rieng
    #   so_lan = 0     -> do roi, khong lan nao -> im lang
    #   so_lan > tran  -> hong that
    wd = vh.get("watchdog") or {}
    n_restart = wd.get("so_lan")
    if n_restart is None:
        ra.append({"ma": "watchdog_khong_do_duoc", "muc": "VUA",
                   "mo_ta": "Khong doc duoc reports/watchdog.log nen KHONG BIET "
                            "supervisor co dang chet lien tuc hay khong. Day la "
                            "'chua do duoc', khong phai 'khong co van de' - mot "
                            "nhat ky vang mat co the nghia la watchdog chua bao "
                            "gio chay.",
                   "bc": wd})
    elif n_restart > TRAN_RESTART_24H:
        ra.append({"ma": "supervisor_restart_lien_tuc", "muc": "NANG",
                   "mo_ta": f"Supervisor chet va khoi dong lai {n_restart} lan "
                            f"trong 24 gio ({wd.get('moi_gio')} lan/gio, tran "
                            f"{TRAN_RESTART_24H}). Ma thoat: "
                            f"{json.dumps(wd.get('theo_rc') or {}, ensure_ascii=False)}. "
                            "Mot vong lap chet-restart giu ty le song thap ma "
                            "khong tru nao bao 'dung im' - do la cach 24/7 dut "
                            "quang ma khong ai thay.",
                   "bc": wd})

    if vh["viec_loi"] > 20:
        ra.append({"ma": "nhieu_viec_loi", "muc": "VUA",
                   "mo_ta": f"{vh['viec_loi']} viec o trang thai LOI", "bc": vh["viec"]})

    # THIET_KE muc 9: qua nhieu PASS trong mot ngay la tin hieu HONG
    hom_nay = datetime.now().strftime("%Y-%m-%d")
    n_pass = SO.mot(KQHD.truy_van(
        "COUNT(*) n", dieu_kien_them="k.verdict='PASS' AND k.luc LIKE ?"
    ), hom_nay + "%")["n"]
    if n_pass > 5:
        ra.append({"ma": "qua_nhieu_pass", "muc": "NANG",
                   "mo_ta": f"{n_pass} PASS trong mot ngay. Theo THIET_KE muc 9 day la tin hieu "
                            "HONG chu khong phai tin vui - phai kiem day chuyen truoc khi duyet",
                   "bc": {"so_pass": n_pass}})

    if sk.get("null_ty_le_lot") is None and sk.get("so_ket_qua", 0) >= 30:
        ra.append({"ma": "chua_hieu_chuan_null", "muc": "NANG",
                   "mo_ta": f"Da ghi {sk['so_ket_qua']} ket qua ma CHUA lan nao do ty le lot cua "
                            "null factory. Khong biet cong dang xa hay chat thi moi ket luan "
                            "am tinh deu vo nghia.", "bc": {}})
    elif sk.get("null_ty_le_lot") is not None:
        import json as _j
        muc = 0.10
        if sk["null_ty_le_lot"] > muc * 2:
            ra.append({"ma": "null_lot_qua_nhieu", "muc": "NANG",
                       "mo_ta": f"Null factory lot {sk['null_ty_le_lot']:.0%} (muc tieu {muc:.0%}) "
                                "- cong dang san xuat phat hien sai",
                       "bc": sk.get("null_chi_tiet", {})})
        elif sk["null_ty_le_lot"] == 0 and (sk.get("ty_le_qua_cong") or 0) == 0:
            if sk.get("cong_co_luc") is True:
                # Da co cau tra loi cho chieu con lai: cong CHO thu co edge di qua.
                # Vay "null 0% + that 0%" la ket luan THAT, khong phai trieu chung.
                pass
            elif sk.get("cong_co_luc") is False:
                ra.append({"ma": "cong_khong_co_luc", "muc": "NANG",
                           "mo_ta": "Bai kiem LUC bao cong chan ca thu CO edge that "
                                    "(p=0,60). Moi ket luan am tinh cua day chuyen "
                                    "dang vo nghia cho toi khi sua cong.",
                           "bc": {"ket": sk.get("cong_co_luc_chi_tiet")}})
            else:
                ra.append({"ma": "cong_co_the_qua_chat", "muc": "VUA",
                           "mo_ta": "Null lot 0% VA kham pha that cung 0%, ma CHUA chay bai "
                                    "kiem LUC. Phai phan biet 'khong co edge' (cau tra loi "
                                    "dung) voi 'cong tu choi ca that lan gia' (loi phai sua) "
                                    "- hai truong hop cho so lieu Y HET nhau.",
                           "bc": {"null_lot": 0, "that_qua_cong": 0}})

    kh = [n for n, d in vh["nguon"].items()
          if d["trang_thai"] == "BAT" and d["lan"] >= 3 and d["thu_hoach"] == 0]
    if kh:
        ra.append({"ma": "nguon_khong_thu_hoach", "muc": "VUA",
                   "mo_ta": f"Nguon {', '.join(kh)} da goi >=3 lan ma chua thu duoc tai lieu nao",
                   "bc": {"nguon": kh}})
    return ra


# --------------------------------------------------------------- TU SUA
def tu_sua(vh: dict) -> list[str]:
    """Chi lam nhung viec DA KHAI BAO TRUOC trong TU_SUA_DUOC."""
    da = []
    n = SO.don_viec_treo()
    if n:
        da.append(f"don_viec_treo: {n} viec CHAY mo coi -> LOI (khong bao gio thanh XONG)")

    r = SO.chay("UPDATE viec SET trang_thai='CHO' WHERE trang_thai='LOI' AND so_lan<3")
    if r:
        da.append(f"xep_lai_viec_loi: {r} viec duoc thu lai")

    if vh["dia_trong_gb"] < 20:
        cache = LAB / "data_khung"
        if cache.exists():
            cu = time.time() - 14 * 86400
            xoa = 0
            for f in cache.glob("*.parquet"):
                try:
                    if f.stat().st_mtime < cu:
                        f.unlink()
                        xoa += 1
                except Exception:
                    pass
            if xoa:
                da.append(f"don_cache_khung: xoa {xoa} file cache khung > 14 ngay")

    # --- gop_van_de_trung_lap (khai bao 31/08) ------------------------------
    # Dieu kien chay: co it nhat HAI dong `llm_*` dang mo. Duoi nguong do thi
    # khong co gi de gop va ham khong dong vao so mot cau nao.
    try:
        gop = gop_van_de_trung_lap()
        if gop:
            da.append("gop_van_de_trung_lap: " + "; ".join(gop))
    except Exception as e:
        da.append(f"gop_van_de_trung_lap: BO QUA ({type(e).__name__})")

    # --- xep_hang_doc_cong_cu (khai bao 31/08) ------------------------------
    # Doi mot truong `trang_thai` trong reports/cong_cu.json. Khong tai gi,
    # khong tich hop gi. Chay xong lan dau thi cac luot sau khong doi gi nua.
    try:
        xep = SCC.xep_hang_doc()
        if xep:
            da.append("xep_hang_doc_cong_cu: " + ", ".join(xep))
    except Exception as e:
        da.append(f"xep_hang_doc_cong_cu: BO QUA ({type(e).__name__})")
    return da


# -------------------------------------------------------------- SUY NGHI SAU
HE_THONG_EVO = """Ban la tru EVOLUTION cua mot phong lab nghien cuu tai chinh chay 24/7.
Viec cua ban KHONG phai de xuat chien luoc giao dich - moi ket luan ve tien deu
phai di qua cong kiem dinh rieng. Viec cua ban la nhin so lieu VAN HANH va noi:
day chuyen dang hong o dau, va sua the nao.

Boi canh bat buoc nho:
- Day chuyen nay da chay 1.758 phep thu truoc day va ra 0 chien luoc dung duoc.
  "Khong tim thay gi" la ket qua BINH THUONG, khong phai trieu chung hong.
- Trieu chung hong that su la: qua nhieu PASS trong mot ngay, null factory lot
  qua nhieu, tru dung im, so bi dut chuoi, hoac vong lap chay ma khong sinh ra gi.
- Mot cong tu choi TAT CA cho ra so lieu y het mot cong hieu chuan tot. Neu ban
  thay ca null lan that deu bang 0, hay noi ro rang do la hai gia thuyet khac nhau.

Tra loi ngan, cu the, bang tieng Viet. Khong khen ngoi, khong dao to bua lon."""


def phan_tich_sau(vh: dict, sk: dict, ep: bool = False) -> dict:
    """Goi LLM doc so lieu van hanh va de xuat cai tien.

    Chay toi da 1 lan moi 6 gio (ngoai han muc chung cua `tri_tue`). Ket qua
    ghi vao van_de/bao cao chu KHONG tu dong thanh hanh dong - EVO chi duoc tu
    sua nhung viec da khai bao trong TU_SUA_DUOC.
    """
    cuoi = SO.mot("SELECT luc FROM chi_so_vh WHERE ten='evo_phan_tich_sau' "
                  "ORDER BY id DESC LIMIT 1")
    if cuoi and not ep:
        try:
            if (time.time() - datetime.strptime(cuoi["luc"], "%Y-%m-%d %H:%M:%S").timestamp()
                    ) < 6 * 3600:
                return {"bo_qua": "chua den ky (6 gio)"}
        except Exception:
            pass

    mo = SO.van_de_mo()
    nhac = (
        "Duoi day la so lieu van hanh cua phong lab. Hay tra loi bang JSON voi cac khoa:\n"
        '  "chan_doan": [ {"van_de": "...", "bang_chung": "...", "muc": "NANG|VUA|NHE"} ],\n'
        '  "de_xuat":   [ {"viec": "...", "vi_sao": "...", "kiem_the_nao": "..."} ],\n'
        '  "cau_hoi_cho_nguoi": ["..."]\n\n'
        "Chi neu ra thu ban CHUNG MINH duoc bang so lieu duoi day. Neu khong thay van de "
        "nao thi tra ve mang rong - dung bia ra viec.\n\n"
        "== VAN HANH ==\n" + json.dumps(vh, ensure_ascii=False, default=str)[:6000] +
        "\n\n== SUC KHOE DAY CHUYEN ==\n" + json.dumps(sk, ensure_ascii=False, default=str)[:3000] +
        "\n\n== VAN DE DANG MO ==\n" +
        json.dumps([{k: v[k] for k in ("ma", "muc", "mo_ta")} for v in mo],
                   ensure_ascii=False)[:3000]
    )
    # ep=True (goi tay) bo qua ca han muc chung cua tri_tue, khong chi ky 6 gio
    kq = TT.hoi_json(nhac, HE_THONG_EVO, bo_qua_han_muc=ep, dung_cache=not ep)
    SO.ghi_chi_so("evo_phan_tich_sau", 1, {"co_json": bool(kq.get("json")),
                                           "duong": kq.get("duong")})
    if kq.get("json"):
        j = kq["json"]
        # KHU TRUNG THEO NOI DUNG. Ban cu dat ma bang `van_tay(van_ban)[:10]`
        # nen mot chan doan dien dat khac di la mot dong moi - 12/25 van de
        # dang mo ngay 31/08 la cung ba chuyen viet lai ba lan.
        dang_mo = SO.van_de_mo()
        for c in (j.get("chan_doan") or [])[:5]:
            bao_van_de_gop(c.get("muc", "NHE"),
                           "[LLM chan doan] " + str(c.get("van_de", ""))[:300],
                           {"bang_chung": c.get("bang_chung"), "nguon": "tri_tue"},
                           dang_mo=dang_mo)
            dang_mo = SO.van_de_mo()
        (REPORTS / "evo_phan_tich_sau.json").write_text(
            json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    return kq


def _dong_watchdog(vh: dict) -> str:
    """Mot dong bao cao cho phep do watchdog. Ba trang thai, ba cau khac nhau."""
    wd = vh.get("watchdog") or {}
    n = wd.get("so_lan")
    if n is None:
        return ("- **Supervisor restart 24h: CHUA DO DUOC** "
                f"({wd.get('ly_do','?')}) - khong phai '0 lan'")
    if n == 0:
        return "- Supervisor restart 24h: **0 lan** (do duoc, khong lan nao)"
    return (f"- **Supervisor restart 24h: {n} lan** ({wd.get('moi_gio')} lan/gio, "
            f"tran {TRAN_RESTART_24H}) - ma thoat "
            f"{json.dumps(wd.get('theo_rc') or {}, ensure_ascii=False)}, "
            f"lan cuoi {wd.get('lan_cuoi')}")


# ------------------------------------------------------------------ BAO CAO
def viet_bao_cao(vh: dict, sk: dict, vd: list, da_sua: list, sau: dict | None = None,
                 san: dict | None = None) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    d = [f"# EVOLUTION - SUC KHOE DAY CHUYEN", f"*{vh['luc']}*", "",
         "> Do bang SUC KHOE, khong do bang so PASS. Mot he lanh manh hieu chuan tot "
         "ke ca khi tim duoc it edge.", ""]

    d += ["## 1. Bon tru", "| Tru | Lan cuoi | Tre | Trang thai |", "|---|---|---|---|"]
    for t, x in vh["tru"].items():
        tre = f"{x.get('tre_giay',0)//60} phut" if "tre_giay" in x else "-"
        dau = " **DUNG IM**" if x.get("dung_im") else ""
        d.append(f"| {t} | {x.get('lan_cuoi','-')} | {tre} | {x.get('trang_thai','-')}{dau} |")

    _so_tho = sk.get("so_ket_qua_tho", sk.get("so_ket_qua", 0))
    _du_phong = sk.get("so_ket_qua_du_phong", 0)
    d += ["", "## 2. San luong",
          f"- Tai lieu da thu: **{vh['tai_lieu']}**",
          f"- Gia thuyet: {json.dumps(vh['gia_thuyet'], ensure_ascii=False)}",
          f"- Gia thuyet co ket qua cuoi: **{sk.get('so_gt_da_ket', sk.get('so_ket_qua',0))}** "
          f"(chua {_so_tho - sk.get('so_gt_da_ket', sk.get('so_ket_qua',0))} dong lich su "
          "da supersede, invalidated hoac quarantine)"]
    d.append(f"- Viec: cho {vh['viec_cho']} / treo {vh['viec_treo']} / loi {vh['viec_loi']}")
    if "seeker_ty_le_vong_rong" in vh:
        d.append(f"- Ty le vong lap rong cua SEEKER: **{vh['seeker_ty_le_vong_rong']:.0%}**")

    d += ["", "## 3. Hieu chuan (thu quan trong hon so PASS)"]
    if sk.get("null_ty_le_lot") is not None:
        d += [f"- **Null factory: {sk['null_ty_le_lot']:.0%} ca KHONG CO EDGE lot qua cong** "
              f"(do luc {sk.get('null_do_luc','?')}, muc tieu <= 10%)",
              "  Day la phep do hieu chuan DUY NHAT dang tin: cho thu khong co edge di qua "
              "ca day chuyen roi dem xem bao nhieu lot."]
    else:
        d.append("- **Chua do null factory lan nao** - chua biet cong xa hay chat.")
    if sk.get("cong_co_luc") is not None:
        d += [f"- **Bai kiem LUC: cong {'PHAN BIET DUOC' if sk['cong_co_luc'] else 'KHONG phan biet duoc'} "
              f"co edge voi khong co edge** (do luc {sk.get('cong_co_luc_luc','?')})",
              "  Hai phep do phai doc CUNG NHAU: 'null lot 0%' mot minh khong phan biet duoc "
              "mot cong hieu chuan tot voi mot cong tu choi tat ca."]
        for k in (sk.get("cong_co_luc_chi_tiet") or []):
            d.append(f"  - biet truoc {k.get('p')} cua so lan -> `{k.get('verdict')}` "
                     f"(sharpe {k.get('sharpe')})")
    else:
        d.append("- **Chua chay bai kiem LUC** - chua biet cong co cho thu CO edge di qua khong.")
    if sk.get("ung_vien_n"):
        d += [f"- (tham khao) p placebo cua {sk['ung_vien_n']} ung vien: trung vi "
              f"{sk['ung_vien_p_trung_vi']}, ty le p<=0,05 la {sk['ung_vien_duoi_005']:.1%}",
              "  KHONG dung so nay lam hieu chuan: ung vien da bi chon loc tren train nen p "
              "cua chung LE RA phai lech thap."]
    d.append(f"- FDR online: {sk.get('fdr_da_bac_bo',0)}/{sk.get('fdr_tong',0)} "
              f"gia thuyet bi bac bo (dem theo gia thuyet, bo du phong/NULL; tho {sk.get('fdr_tong_tho',0)} hang)")
    if "khop_ba_tang" in sk:
        _k = sk["khop_ba_tang"]
        d.append(f"- Dong bo ba tang (so_gt_da_ket == fdr_tong): "
                 f"{'**KHOP**' if _k else '**TACH** - doi soat tiep khoan tinh nay'}")

    d += ["", "## 4. Tai nguyen + toan ven",
          f"- **Thoi gian song 7 ngay: {vh.get('ty_le_song_7ngay', 1):.1%}** "
          f"(mat {vh.get('gian_doan_7ngay_gio', 0)} gio qua {vh.get('gian_doan_lan', 0)} lan "
          "gian doan - may ngu hoac tat, khong phai tru chet)",
          _dong_watchdog(vh),
          f"- Dia trong: **{vh['dia_trong_gb']} GB** - MT5 tick-test: **{vh['mt5_tick_test']}**",
          f"- So cai: {'LANH' if vh['so_toan_ven']['lanh'] else '**HONG**'} "
          f"({vh['so_toan_ven']['mo_ta']})"]

    d += ["", "## 5. Nguon", "| Nguon | Lan goi | Loi | Thu hoach | Trang thai |",
          "|---|---|---|---|---|"]
    for n, x in sorted(vh["nguon"].items()):
        d.append(f"| {n} | {x['lan']} | {x['loi']} | {x['thu_hoach']} | {x['trang_thai']} |")

    mo = SO.van_de_mo()
    d += ["", f"## 6. Van de dang mo ({len(mo)})",
          "> Mot PHAT HIEN = mot dong. Dien dat khac di khong de ra dong moi; "
          "no cong vao `x<n> lan`. Xem `CHU_DE_VAN_DE` trong tru/evolution.py."]
    if mo:
        for v in mo[:15]:
            bc = _doc_bang_chung(v)
            n = int(bc.get("so_lan_tai_phat") or 1)
            dem = f" **x{n} lan** (gan nhat {bc.get('lan_gan_nhat')})" if n > 1 else ""
            d.append(f"- **[{v['muc']}]** `{v['ma']}`{dem} - {v['mo_ta']}")
    else:
        d.append("- Khong co van de nao dang mo.")

    # SAN CONG CU. Hai con so phai tach bach: `rong` la CAU TRA LOI ("hoi
    # duoc, khong ai viet ve chuyen nay"), `loi` la SU CO ("khong voi toi
    # duoc"). Gop chung lam mot la ly do luot 30/08 bao `loi=3` oan.
    try:
        cho_doc = SCC.dang_cho_doc()
    except Exception:
        cho_doc = []
    if cho_doc:
        d += ["", f"## 6b. Kho ma dang cho NGUOI doc de doi chieu ({len(cho_doc)})",
              "> Doc de DOI CHIEU voi cong, khong bao gio de THAY cong.",
              "| Kho | Doi chieu voi | Vi sao |", "|---|---|---|"]
        for c in cho_doc:
            d.append(f"| {c['ten']} | `{c['doi_chieu_voi']}` | {c['vi_sao']} |")

    if san:
        d += ["", "## 6c. San cong cu luot nay"]
        if isinstance(san.get("loi"), str):
            d.append(f"- Luot san NEM NGOAI LE: {san['loi']}")
        elif san.get("tim_them") is None:
            d.append("- **KHONG THU DUOC TRUY VAN NAO** luot nay (moi truy van "
                     f"con trong chu ky cho: {san.get('con_cho','?')} muc). "
                     "Day KHONG phai 'san khong ra gi' - la chua do.")
        else:
            d.append(f"- Da thu {san.get('da_thu',0)} truy van -> "
                     f"**{san['tim_them']} muc moi**; "
                     f"{san.get('rong',0)} truy van **hoi duoc ma khong co ket qua** "
                     f"(day la CAU TRA LOI, khong phai loi); "
                     f"{san.get('loi',0)} truy van **that su hong**; "
                     f"con {san.get('con_cho',0)} truy van cho den han.")
        if san.get("nhu_cau_tu_van_de"):
            d.append("- Nhu cau sinh TU VAN DE DANG MO: "
                     + ", ".join(f"`{x}`" for x in san["nhu_cau_tu_van_de"]))

    d += ["", "## 7. EVO da tu sua trong luot nay"]
    d += [f"- {x}" for x in da_sua] if da_sua else ["- Khong co gi can sua."]
    d += ["", "> EVO chi tu sua nhung viec da khai bao truoc: "
          + ", ".join(f"`{k}`" for k in TU_SUA_DUOC) + ". Ngoai danh sach do thi chi ghi "
          "van de va cho nguoi - khong tu sua code."]

    if sau:
        d += ["", "## 8. Suy nghi sau (LLM doc so lieu van hanh)"]
        if sau.get("bo_qua"):
            d.append(f"- Bo qua luot nay: {sau['bo_qua']}")
        elif sau.get("loi"):
            d.append(f"- Loi goi: {sau['loi']}")
        elif sau.get("json"):
            j = sau["json"]
            for c in (j.get("chan_doan") or []):
                d.append(f"- **[{c.get('muc','?')}]** {c.get('van_de','')}")
                if c.get("bang_chung"):
                    d.append(f"  - bang chung: {c['bang_chung']}")
            if j.get("de_xuat"):
                d += ["", "**De xuat:**"]
                for x in j["de_xuat"]:
                    d.append(f"- {x.get('viec','')} — *vi sao:* {x.get('vi_sao','')} "
                             f"— *kiem:* {x.get('kiem_the_nao','')}")
            if j.get("cau_hoi_cho_nguoi"):
                d += ["", "**Cau hoi cho nguoi:**"] + [f"- {q}" for q in j["cau_hoi_cho_nguoi"]]
            d += ["", f"> Goi qua duong `{sau.get('duong','?')}`, {sau.get('giay','?')}s. "
                  "Day la CHAN DOAN, khong phai hanh dong - EVO khong tu thuc thi."]
        else:
            d.append(f"- Khong phan tich duoc JSON: {sau.get('loi_phan_tich', '?')}")

    (REPORTS / "EVOLUTION.md").write_text("\n".join(d), encoding="utf-8")
    (REPORTS / "evo_suc_khoe.json").write_text(
        json.dumps({"van_hanh": vh, "day_chuyen": sk, "van_de": vd,
                    "da_sua": da_sua, "san_cong_cu": san},
                   ensure_ascii=False, indent=1, default=str), encoding="utf-8")


# Cac ma van de do CHINH EVO sinh ra -> EVO cung phai TU DONG LAI khi het.
# Van de khong tu dong lai duoc thi danh sach se chi dai ra, va bang dieu khien
# se hien thi mai nhung thu da sua xong - dung cai lam nguoi dung mat long tin
# vao danh sach. (Da xay ra that ngay 15/08 voi `dia_thap`.)
EVO_TU_QUAN = {
    "dia_thap", "vong_lap_rong", "nhieu_viec_loi", "qua_nhieu_pass",
    "so_dut_chuoi", "nguon_khong_thu_hoach", "chua_hieu_chuan_null",
    "null_lot_qua_nhieu", "cong_co_the_qua_chat",
    # Them 31/08: ca hai deu suy ra tu mot phep do chay moi luot, nen khi dieu
    # kien het thi chung phai tu dong lai - neu khong danh sach van de chi dai
    # ra va nguoi dung mat long tin vao no (da xay ra that voi `dia_thap`).
    "supervisor_restart_lien_tuc", "watchdog_khong_do_duoc",
}


#: EVO san cong cu moi 12 gio. Kho cong cu khong doi nhanh, va GitHub search
#: khong khoa chi cho 10 lan/phut - san day hon la vua ton suat vua khong them
#: thong tin.
CHU_KY_SAN_GIAY = 12 * 3600

#: Tran canh bao tai nguyen van hanh. Do that 30/08 truoc khi dat cac so nay:
#: 356 tab lam luot keo dung han; sau khi don ve 6 tab thi moi trang doc het
#: 10-13 giay thay vi ~20. Chrome bot binh thuong chiem ~2,9 GB voi 19 tien trinh.
TRAN_TAB_BAO_DONG = 25
TRAN_RAM_CHROME_GB = 6.0


def _den_han_san() -> bool:
    try:
        r = SO.mot("SELECT luc FROM chi_so_vh WHERE ten='evo_san_cong_cu' "
                   "ORDER BY id DESC LIMIT 1")
    except Exception:
        return True
    if not r or not r["luc"]:
        return True
    try:
        cu = time.mktime(time.strptime(r["luc"], "%Y-%m-%d %H:%M:%S"))
    except Exception:
        return True
    return (time.time() - cu) > CHU_KY_SAN_GIAY


def mot_luot() -> dict:
    SO.nhip_tim(TRU, "chay")
    vh = do_van_hanh()
    sk = do_suc_khoe_day_chuyen()
    vd = phat_hien(vh, sk)
    for v in vd:
        SO.bao_van_de(v["ma"], v["muc"], v["mo_ta"], v.get("bc"))
    # TU DONG LAI: van de cua EVO ma luot nay khong con kich hoat nua
    dang_kich_hoat = {v["ma"] for v in vd}
    da_dong = []
    for m in SO.van_de_mo():
        ma = m["ma"]
        if ma in dang_kich_hoat:
            continue
        if ma.startswith(("tru_dung_im_", "tru_chua_chay_")):
            SO.dong_van_de(ma, "tru da chay lai binh thuong")
            da_dong.append(ma)
        elif ma in EVO_TU_QUAN:
            SO.dong_van_de(ma, "dieu kien phat hien khong con dung")
            da_dong.append(ma)
    # SAN CONG CU NGOAI. Nua viec con lai cua EVO (chu du an chot 30/08): khong
    # chi canh he hong, ma con di tim du an/cong cu da co san de tich hop.
    # Tan suat thap - GitHub search khong khoa cho 10 lan/phut, va kho cong cu
    # khong doi nhanh. Loi o day KHONG duoc lam hong luot EVO.
    #
    # Tu 31/08: truyen SO VAN DE DANG MO vao. Van de muc NANG co anh xa khai
    # bao truoc (`SCC.VAN_DE_SANG_NHU_CAU`) sinh ra nhu cau ky thuat, va nhu
    # cau sinh ra truy van san. Truoc do `san_cong_cu` di theo mot danh sach
    # tinh va khong biet gi ve tinh trang cua chinh day chuyen.
    san = {}
    try:
        if _den_han_san():
            san = SCC.mot_luot(gioi_han_truy_van=3, im_lang=True,
                               van_de_mo=SO.van_de_mo())
            # `tim_them=None` nghia la KHONG THU DUOC truy van nao (moi truy
            # van con trong chu ky cho) - khac han "thu roi ma khong ra gi".
            # Ghi 0 vao cho nay se bien "chua do" thanh "do roi, bang 0".
            if san.get("tim_them") is None:
                SO.ghi_chi_so("evo_san_cong_cu_bo_qua", 1, san)
            else:
                SO.ghi_chi_so("evo_san_cong_cu", san["tim_them"], san)
    except Exception as e:
        san = {"loi": f"{type(e).__name__}: {str(e)[:80]}"}

    da_sua = tu_sua(vh)
    if da_dong:
        da_sua.append("dong_van_de_da_het: " + ", ".join(da_dong))
    try:
        sau = phan_tich_sau(vh, sk)
    except Exception as e:
        sau = {"loi": f"{type(e).__name__}: {str(e)[:80]}"}
    viet_bao_cao(vh, sk, vd, da_sua, sau, san)
    SO.ghi_chi_so("evo_van_de_mo", len(SO.van_de_mo()))
    SO.nhip_tim(TRU, "nghi", {"van_de": len(vd), "da_sua": len(da_sua),
                              "san_cong_cu": san.get("tim_them")})
    return {"van_de_moi": [v["ma"] for v in vd], "da_sua": da_sua,
            "san_cong_cu": san,
            "van_de_dang_mo": len(SO.van_de_mo()),
            "tru_dung_im": [t for t, x in vh["tru"].items() if x.get("dung_im")],
            "dia_gb": vh["dia_trong_gb"], "tai_lieu": vh["tai_lieu"],
            "phan_tich_sau": {k: v for k, v in sau.items() if k != "van_ban"}}


if __name__ == "__main__":
    SO.khoi_tao()
    print(json.dumps(mot_luot(), ensure_ascii=False, indent=1))
