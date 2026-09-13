# -*- coding: utf-8 -*-
"""kham_pha_nguon.py - SO DANG KY CAC KENH TU TIM NGUON MOI.

VI SAO CO FILE NAY. Chu du an 04/09/2026: *"cac nguon thi sao? Toi cu chi ra
nguon nao cau moi search nguon do thi ko on"*. Do lai thi ong dung, va nguyen
nhan cu the hon "thieu cham":

  - `nhan/vuon_nguon.py` CO tu tim nguon, va no ĐANG duoc noi day: `seeker.
    mot_luot` goi `VN.mot_luot_tim()` moi luot, 6 nguon no tim duoc dang BAT va
    da thu that (aligrithm 17 tai lieu, betterbuyandhold 3).
  - Nhung no chi co **DUNG MOT KENH KHAM PHA**: quet lien ket ra ngoai trong
    cac bai blog da thu, cong voi thu muc quantocracy. Mot kenh nhu vay chi de
    ra duoc **blog tieng Anh**. Telegram, GitHub org, YouTube, dien dan can dang
    nhap - khong cai nao tu tim duoc.
  - Va no khong chay tu 23/08/2026, vi SEEKER khong chay: khong co lich thi
    khong co lan nao.

Nen cai thieu khong phai mot bo tim nguon nua, ma la mot **SO DANG KY**: kenh
kham pha la mot danh sach khai bao duoc, moi kenh mot ham, chay het trong mot
luot, va bao cao rieng tung kenh de biet kenh nao de ra nguon that.

QUY TAC KHONG DUOC PHA:

  1. **Kham pha KHONG BAO GIO tu bat mot nguon.** No chi de nghi. Mot nguon moi
     vao dien `THU` (tham do) va phai tu chung minh bang SUAT (`vuon_nguon`),
     y het vong doi cua nguon blog. Ly do: mot nguon la mot khoan ngan sach
     mang lien tuc, va "cai gi cung dang doc" thi khong khac gi khong doc gi.
  2. **Moi kenh phai bao SO**, khong bao "xong". Kenh nao nhieu luot lien tiep
     de ra 0 nguon thi do la mot ket luan can biet.
  3. Khong kenh nao duoc chay qua ngan sach giay cua no.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from nhan import so as SO

LAB = Path(__file__).resolve().parent.parent
SO_UNG_VIEN = LAB / "config" / "nguon_ung_vien.json"


def _doc() -> dict:
    if SO_UNG_VIEN.exists():
        try:
            return json.loads(SO_UNG_VIEN.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _luu(d: dict) -> None:
    SO_UNG_VIEN.parent.mkdir(parents=True, exist_ok=True)
    SO_UNG_VIEN.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                           encoding="utf-8")


def de_nghi(khoa: str, kenh: str, chi_tiet: dict) -> bool:
    """Ghi mot nguon UNG VIEN. Tra True neu la cai moi.

    Khong bat, khong thu thap, khong dung vao bang `nguon`. Chi de nghi.
    """
    d = _doc()
    if khoa in d:
        d[khoa]["gap_lai"] = int(d[khoa].get("gap_lai", 0)) + 1
        _luu(d)
        return False
    d[khoa] = {**chi_tiet, "kenh_kham_pha": kenh, "trang_thai": "THU",
               "phat_hien_luc": SO.bay_gio(), "gap_lai": 0}
    _luu(d)
    return True


# ------------------------------------------------------------ KENH 1: blog

def kenh_blog(ngan_sach_giay: float = 120.0, in_ra=print) -> dict:
    """Uy quyen cho `vuon_nguon`: lien ket ra ngoai trong bai + thu muc nganh."""
    from nhan import vuon_nguon as VN
    t0 = time.time()
    try:
        kq = VN.mot_luot_tim(so_mien=8, so_ten_thu_muc=8,
                             ngan_sach_giay=ngan_sach_giay)
    except Exception as e:
        return {"kenh": "blog", "loi": f"{type(e).__name__}: {str(e)[:90]}"}
    return {"kenh": "blog", "de_nghi": int(kq.get("them_moi") or 0),
            "chi_tiet": kq, "giay": round(time.time() - t0, 1)}


# -------------------------------------------------------- KENH 2: telegram

#: Tu khoa san kenh Telegram. KHAI BAO TAY, va co ca tieng Viet - do la nua thi
#: truong ma truy van tieng Anh khong cham toi. Do 04/09: 8 tu khoa -> 49 kenh,
#: trong do `@mqlfree` (604 nguoi) cho 39 file .mq4/.mq5 tho tren 300 tin, cao
#: hon moi kenh dong nguoi khac. **So nguoi theo doi khong du bao mat do luat.**
TU_KHOA_TELEGRAM = (
    "forex ea", "expert advisor mt5", "mql5 source", "trading bot",
    "robot forex", "chien luoc forex", "scalping vang", "giao dich thuat toan",
    "quant trading", "algo trading vietnam", "pine script", "backtest ea",
    # --- them 13/09/2026: nham HO QUAN TRI VI THE rieng (trailing/hedge/
    # grid/martingale), theo yeu cau chu du an. Kem tieng Nga vi cong dong
    # grid/hedge EA (Ilan/Ultima-kieu) tap trung o do - `mql5.com` von la san
    # cua Nga truoc khi dich sang tieng Anh (xem `TRUY_VAN` cua seeker_deep.py
    # ap dung cach nay cho tim theo TEN, o day ap cho tim KENH).
    "grid ea forex", "hedging ea mt5", "trailing stop ea",
    "martingale forex bot", "сетка форекс советник", "хеджирование форекс",
    "quan ly von giao dich", "nhoi lenh forex",
)

#: Duoi muc nay thi mot kenh chua du de dat mot suat ngan sach mang.
NGUOI_TOI_THIEU = 300


def kenh_telegram(tu_khoa=TU_KHOA_TELEGRAM, gioi_han: int = 12,
                  in_ra=print) -> dict:
    """San kenh Telegram bang chinh o tim kiem cua Telegram (can phien dang nhap)."""
    from nhan import telegram as TG
    t0 = time.time()
    duoc, ly_do = TG.san_sang_mtproto()
    if not duoc:
        return {"kenh": "telegram", "bo_qua": ly_do}
    try:
        ds = TG.tim_kenh(list(tu_khoa), gioi_han=gioi_han, in_ra=lambda *a: None)
    except Exception as e:
        return {"kenh": "telegram", "loi": f"{type(e).__name__}: {str(e)[:90]}"}
    moi = 0
    da_theo = {k.lower() for k in TG.KENH_CHU_DU_AN}
    for d in ds:
        if d.get("loi") or not d.get("la_kenh"):
            continue
        if (d.get("nguoi_tham_gia") or 0) < NGUOI_TOI_THIEU:
            continue
        if d["kenh"].lower() in da_theo:
            continue
        if de_nghi(f"telegram:{d['kenh']}", "telegram",
                   {"url": f"https://t.me/{d['kenh']}", "ten": d.get("tieu_de"),
                    "loai": "telegram", "nguoi": d.get("nguoi_tham_gia"),
                    "tu_khoa": d.get("tu_khoa")}):
            moi += 1
    return {"kenh": "telegram", "thay": len(ds), "de_nghi": moi,
            "giay": round(time.time() - t0, 1)}


#: SO DANG KY. Them mot kenh = them mot dong o day, khong sua `mot_luot`.
KENH = {"blog": kenh_blog, "telegram": kenh_telegram}

#: KENH CHUA LAM - va chung TU DANG KY thanh van de moi luot chay.
#:
#: VI SAO khong de la mot chu thich. Chu du an 04/09/2026: *"sao khi co van de
#: finder va evo khong lam di"*. Cau do dung, va no chi ra dung mot thoi quen
#: sai: hom do toi phat hien "he chua co bo doc video" roi **viet no vao mot
#: dong chu thich** thay vi ghi thanh `van_de` de Finder di san. Mot lo hong
#: nam trong chu thich thi khong ai san no bao gio - no chi duoc nho den khi
#: tinh co co nguoi doc lai file.
#:
#: Nen: moi muc o day sinh ra mot `van_de` muc VUA moi luot `mot_luot()`. Muc
#: VUA co y: no NEO duoc the cong cu (mien phi) nhung KHONG sinh truy van san
#: (chi muc NANG moi duoc, xem `san_cong_cu.MUC_SINH_NHU_CAU`) - nen mot danh
#: sach viec-chua-lam khong the tu no nuot ngan sach mang.
CHUA_LAM = {
    "kham_pha_github_topic": (
        "Chua co kenh kham pha GitHub topic / awesome-list. Do la noi NGUOI "
        "KHAC da gom san nguon (awesome-quant, awesome-systematic-trading), "
        "tuc mot dong chay qua giong tinix chu khong phai truy van tu nghi ra."),
    "kham_pha_youtube_kenh": (
        "Chua co kenh kham pha YouTube. Duong DOC video da co va chay tot "
        "(71 ban doc, 1,37 trieu ky tu tu phu de), nhung khong co gi tu tim ra "
        "KENH moi - danh sach kenh van la khai bao tay."),
    "kham_pha_dien_dan_dang_nhap": (
        "Chua co kenh kham pha dien dan can dang nhap (forexfactory, myfxbook). "
        "Ha tang dang nhap da co o `nhan/tu_dang_nhap.py` nhung chua noi vao "
        "kham pha nguon."),
}


def dang_ky_chua_lam(in_ra=print) -> dict:
    """Moi muc CHUA_LAM -> mot van de muc VUA. Tra so muc VUA MO ra.

    `SO.bao_van_de` tu khu trung: van de dang mo thi khong de them ban ghi moi.
    """
    moi = 0
    for ma, mo_ta in CHUA_LAM.items():
        vid = SO.bao_van_de(ma, "VUA", mo_ta,
                            {"tu": "kham_pha_nguon.CHUA_LAM",
                             "do_luc": SO.bay_gio()})
        if vid:
            moi += 1
    if moi:
        in_ra(f"  CHUA_LAM: dang ky {moi} van de moi")
    return {"tong": len(CHUA_LAM), "moi": moi}


def mot_luot(kenh=None, ngan_sach_giay: float = 300.0, in_ra=print) -> dict:
    """Chay het cac kenh kham pha, bao cao TUNG kenh."""
    ten = list(kenh or KENH)
    t0 = time.time()
    bao = {"kenh_chay": ten, "ket": {}, "de_nghi_moi": 0,
           "chua_lam": dang_ky_chua_lam(in_ra=in_ra)}
    for k in ten:
        f = KENH.get(k)
        if not f:
            bao["ket"][k] = {"loi": "khong co kenh nay"}
            continue
        con = ngan_sach_giay - (time.time() - t0)
        if con < 20:
            bao["ket"][k] = {"bo_qua": "het ngan sach giay"}
            continue
        r = f(in_ra=in_ra) if k != "blog" else f(ngan_sach_giay=min(con, 150),
                                                 in_ra=in_ra)
        bao["ket"][k] = r
        bao["de_nghi_moi"] += int(r.get("de_nghi") or 0)
        in_ra(f"  kham pha [{k}]: {r.get('de_nghi', 0)} de nghi moi"
              + (f"  ({r['bo_qua']})" if r.get("bo_qua") else "")
              + (f"  LOI {r['loi']}" if r.get("loi") else ""))
    bao["giay"] = round(time.time() - t0, 1)
    bao["tong_ung_vien"] = len(_doc())
    SO.ghi_chi_so("kham_pha_de_nghi", float(bao["de_nghi_moi"]),
                  {"kenh": ten})
    in_ra(f"KHAM PHA: {bao['de_nghi_moi']} de nghi moi, "
          f"kho ung vien {bao['tong_ung_vien']}")
    return bao


def dang_cho_duyet() -> list[dict]:
    """Nguon ung vien dang cho NGUOI gat - doc thuan tuy, khong ghi gi."""
    return [{"khoa": k, **v} for k, v in sorted(
        _doc().items(), key=lambda x: -(x[1].get("nguoi") or 0))
        if v.get("trang_thai") == "THU"]
