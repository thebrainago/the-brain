# -*- coding: utf-8 -*-
"""ho_so_tai_san.py - MOT CUA cho toan bo dac diem tai san da do duoc.

Chu du an 13/09/2026: *"Cac module so sanh dac diem tai san, tuong quan, mua vu
da hoan thanh chua, can hoan thanh cho ra ket qua va thong tin phuc vu duoc cho
giao dich chu khong phai hoi hot"*, va lam ro them: *"Muc tieu van chua phai la
ra nhieu co che hay kiem tien ma cai he thong phai tot da. Cac module va tru la
de lam co so va phuong phap cho boc tach va test sau nay"*.

## HIEN TRANG TRUOC FILE NAY: NAM HON DAO RIENG

Nam module da CHAY va GHI ra 5 file, nhung KHONG module nao khac trong lab doc
lai chung - moi ho so la mot ngo cut:

    tinh_cach.py        -> reports/tinh_cach_tai_san.json       (157 ma, D1)
    ho_so_symbol.py     -> config/ho_so_symbol.json             (159 ma, D1)
    ho_so_mua_vu.py     -> reports/HO_SO_MUA_VU.json            (159 ma, D1)
    ho_so_tuong_quan.py -> reports/HO_SO_TUONG_QUAN_{D1,H4,H1}.json (158 ma)
    ho_so_song.py       -> reports/HO_SO_SONG.json              (159 ma, H4)

File nay KHONG do lai gi ca - no chi GOP va TRA LOI qua bon ham: `ho_so()`,
`tom_tat()`, `chon()`, `ghep_duoc()`. Muon do THEM (mua vu tren H4, song tren
D1...) phai chay lai module goc truoc, roi file nay tu doc duoc ngay vi no doc
thang tu file/cache, khong dong cung.

## CON SO DA DO (13/09/2026, khung D1 tru khi ghi rieng) - PHAN "KHONG HOI HOT"

  MUA VU: 72/159 (ma|khung) co it nhat mot phep M1/M2/M3 `dat=true` (p<0,05
  SAU hoan vi nhan thang - da tu dong hieu chinh cuc tri chon, xem docstring
  `ho_so_mua_vu.py`). Nhung 40/72 dong dat=true nam tren ma co `chi_phi_do_tin
  = KHAI` (spread 1,0 bps la MAC DINH, chua do that) - loai het, con 32/72 co
  spread THAT (DO/SAN). Trong 32 do, chi 22 co `chenh_bps > spread_bps` cua
  chinh no - tuc CHI 22/159 (ma|khung), tren 18 MA DUY NHAT, vua co mua vu do
  duoc VUA song qua phi giao dich CUA CHINH MA DO (khong phai gia dinh phi noi
  chung).

  **NHAN THU DA SUA TAI GOC 13/09/2026** (`ho_so_mua_vu.thu_da_sua`). Ban dau
  82/159 ma dinh `canh_bao_nhan` "thu lech mot ngay" nhung CHI doan qua thong
  ke gian tiep (%T6/%CN) - chu du an chi dung: mot canh bao khong ai chan la
  bang khong co canh bao, va 41/50 phat hien M3 dat=true "di qua" mang theo no.
  Da tim NGUYEN NHAN GOC that (khong doan +-1 nua): bar D1 cua 82 ma nguon SAN
  (XM/Exness/MetaQuotes) dong o **21:00 UTC dong nhat suot toan bo lich su**
  (nua dem gio may chu UTC+3), nen ngay-lich cua timestamp UTC LUON it hon
  ngay giao dich that 1 ngay; 77 ma con lai (Yahoo...) dong dung 00:00, khong
  lech. Kiem tra cheo tin hieu GIO nay voi tin hieu thong ke cu tren CA 159 ma:
  khop nhau 100% - 0 sai lech ca hai chieu, nen sau khi sua **KHONG co dong
  dat=true nao doi ket luan** (0/159 ma bi ha ve CHUA_DO_DUOC boi cong chan
  moi). `canh_bao_nhan` gio la GHI NHAN mot nhan da SUA+XAC NHAN CHEO, khong
  con la nghi van chua giai quyet. Da them CHOT CHAN: neu tin hieu gio UTC va
  tin hieu thong ke MAU THUAN nhau (chua tung xay ra tren du lieu hien tai,
  nhung co the xay khi mot ma la du lieu hon-hop nhieu nguon), `M3_ngay_trong_
  tuan` tu dong ha ve `CHUA_DO_DUOC` - khong con duong nao de mot nhan khong
  chac di qua duoi dang "dat=true kem canh bao" nua.

  TUONG QUAN (D1, 158 ma, C(158,2)=11.960 cap tinh nhung file chi LUU top 400
  |r| lon nhat): trong 340 cap luu co |r|>=0,7, 306 on_dinh>=0,9 (dung ghep
  danh muc duoc that), chi 1 cap la "dong xu ngau nhien trong doi song ngan".
  O muc TUNG MA (ho_so con, luon co top-3 moi chieu cho ca 158 ma bat ke co
  lot top-400 toan cuc hay khong): 45/158 co it nhat mot doi tac AM ON DINH
  (r<=-0,5, on_dinh>=0,85) de ghep chan nguoc; NGUOC LAI 128/158 co doi tac
  DUONG manh+on dinh (r>=0,5, on_dinh>=0,85) - tuc PHAN LON ma trong kho TRUNG
  RUI RO voi it nhat mot ma khac (thuong la quan he co hoc: chung dong tien,
  chung chi so, hop dong tuong lai cua cung underlying). 59/158 co
  r_tuyet_doi_trung_vi < 0,05 voi CA kho - gan nhu doc lap voi phan con lai.

  SONG (H4): CHI 27/159 ma co du lieu goc du min (<=240 phut/bar) de dung
  duoc H4. 132/159 con lai bao `loi` ro rang "du lieu goc cach nhau ~1440
  phut" (chi co D1) - day la CHUA_DO_DUOC vi THIEU DO PHAN GIAI NGUON, khong
  phai am tinh ve hinh dang song. Trong 27 ma do duoc, so cap day/hoi dao dong
  114 (XM_US100CASH) - 2.325 (EURUSD); chon nguong DU=200 cap: duoi do la
  MONG, dung duoc nhung phai than trong voi TP/SL suy ra.

  DO PHU: 157/159 ma co du CA 5 nguon (tru song, vi song von chi 27/159 ma co
  H4). AUDTHB va USDCNH co trong 4/5 nguon (mua_vu, ho_so_symbol, tuong_quan,
  song) nhung THIEU tinh_cach - it hon 400 bar hoac thieu OHLC.

## KIEM TRA CHEO NHAN TINH_CACH (13/09/2026)

Nhan HOI_QUY/XU_HUONG co du bao duoc that khong? Hai nguon, mot cu mot moi:

  (a) `tinh_cach.nhan()` (dong ~171 file nay) da tu ghi lai ket qua doi chieu
      cu: Hurst r=-0,567, ER r=-0,348, VR(10) r=-0,256 tren 157 ma, khi so
      hieu Sharpe trung vi ho `quay_ve_trung_binh` tru ho `xu_huong` cho TUNG
      ma (nguon `reports/quet_rong_d1.json`, 262 co che x 194 ma - file nay
      da bi don dep theo quy tac "bao cao gon mot file" nen khong con de chay
      lai, nhung ket qua da ghi vao code va memory du an).
  (b) Kiem tra DOC LAP tren so ket qua LIVE nhat (`nao.db`, bang
      `gia_thuyet`/`ket_qua`, thoi diem viet file nay: 16 ma / 383 gia thuyet
      con hieu luc, 373 FAIL - 7 INVALIDATED - 2 PASS - 1 CO_CO_CHE). Nhom co
      che theo ho (HOI_QUY_MECH = bollinger_ve/rsi_dao_chieu/ibs_bat_day/
      ichimoku_cheo; XU_HUONG_MECH = sma_cheo/donchian/momentum_ema), roi cheo
      voi nhan cua tai_san: tai san nhan HOI_QUY chay co che HOI_QUY_MECH
      trung binh alpha -0,165 (n=60) TOT HON han chay XU_HUONG_MECH tren cung
      nhom ma, trung binh -3,854 (n=33) - dung huong ky vong. Ca HAI ket qua
      PASS/CO_CO_CHE THAT trong toan bo nao.db (AUDCAD.H4.rsi_dao_chieu,
      XM_US100CASH.D1.mean_reversion_z5) deu roi vao ma nhan HOI_QUY va deu la
      co che ho hoi quy - khong co phan vi du nao di NGUOC nhan.

  => Nhan CO KHA NANG du bao (huong nhat quan qua hai nguon doc lap, cach
  nhau ~1 thang), NHUNG kiem tra (b) qua mong (16 ma, 2 PASS) de tu no la
  bang chung - day la XAC NHAN THEM cho ket qua 157-ma cu, khong phai phep do
  moi doc lap. Dung nhan nay de XEP HANG uu tien trong `chon()`, KHONG dung de
  LOAI cung mot ma/co che nao chi vi trai nhan.

## BA TRANG THAI, THEO DUNG QUY UOC DU AN

`DAT` / `AM` / `CHUA_DO_DUOC`. Moi nhom con trong `ho_so()` hoac co du lieu
that, hoac tra `{"trang_thai": "CHUA_DO_DUOC", "vi_sao": "..."}` - khong bao
gio bia gia tri mac dinh de lap day mot cot.

Chay:  python -m nhan.ho_so_tai_san [MA] [KHUNG]        (in tom_tat)
       python -m nhan.ho_so_tai_san bang [KHUNG]        (ghi BANG_TAI_SAN.md)
       python -m nhan.ho_so_tai_san thongke [KHUNG]     (in JSON thong ke)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

BAO_CAO = LAB / "reports" / "BANG_TAI_SAN.md"

CHUA_DO_DUOC = "CHUA_DO_DUOC"

# Nguong GHEP/TRANH dung chung - lay lai dung tu `ho_so_tuong_quan.py` de hai
# module khong lech tieu chi khi cung noi ve "on dinh".
GHEP_R_AM_TOI_THIEU = -0.5
GHEP_ON_DINH_TOI_THIEU = 0.85
TRUNG_R_TOI_THIEU = 0.5

# Do tin cua ho so song: do tu chinh phan bo 27 ma do duoc ngay 13/09 (min
# khong-0 la 114 cap XM_US100CASH, p90 la 871). 200 la nguong GIUA hai cum do,
# khong phai so tron chon bua.
SONG_SO_CAP_DU = 200


# --------------------------------------------------------------- NAP NGUON
def _doc_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _tinh_cach_theo_ma() -> dict[str, dict]:
    arr = _doc_json(LAB / "reports" / "tinh_cach_tai_san.json")
    if not isinstance(arr, list):
        return {}
    return {x["ma"]: x for x in arr if isinstance(x, dict) and x.get("ma")}


def _symbol_theo_ma() -> dict[str, dict]:
    from nhan import ho_so_symbol as HSS
    hs = HSS.doc()
    if isinstance(hs, dict):
        hs = list(hs.values())
    return {h["ma"]: h for h in (hs or []) if isinstance(h, dict) and h.get("ma")}


def _mua_vu_theo_key() -> dict[str, dict]:
    from nhan import ho_so_mua_vu as MV
    d = MV.doc()
    return d if isinstance(d, dict) else {}


def _tuong_quan_full(khung: str) -> dict:
    from nhan import ho_so_tuong_quan as TQ
    d = TQ.doc(khung)
    return d if isinstance(d, dict) else {}


def _song_theo_key() -> dict[str, dict]:
    from nhan import ho_so_song as SO
    d = SO.doc()
    return d if isinstance(d, dict) else {}


# ------------------------------------------------------------------ HO SO
def ho_so(ma: str, khung: str = "D1", *, _tinh_cach=None, _symbol=None,
         _mua_vu=None, _tuong_quan=None, _song=None) -> dict:
    """Ho so DAY DU mot ma tren mot khung - gop 5 nguon, KHONG do them gi moi.

    Cac tham so `_tinh_cach=`/`_symbol=`/`_mua_vu=`/`_tuong_quan=`/`_song=`
    danh cho test/goi hang loat: truyen thang dict cache thay vi doc lai file
    (cung quy uoc `ho_so_symbol.chon_ung_vien(ho_so=...)`).
    """
    ma = str(ma).strip()
    tc_all = _tinh_cach if _tinh_cach is not None else _tinh_cach_theo_ma()
    sy_all = _symbol if _symbol is not None else _symbol_theo_ma()
    mv_all = _mua_vu if _mua_vu is not None else _mua_vu_theo_key()
    tq_all = _tuong_quan if _tuong_quan is not None else _tuong_quan_full(khung)
    so_all = _song if _song is not None else _song_theo_key()

    ra: dict = {"ma": ma, "khung": khung}

    # --- TINH CACH (D1 - dac tinh cau truc chuoi gia, khong gan voi 1 khung)
    tc = tc_all.get(ma)
    if tc:
        ra["tinh_cach"] = dict(tc)
        if khung != "D1":
            ra["tinh_cach"]["_ghi_chu"] = "do tren D1, dung chung cho moi khung"
    else:
        ra["tinh_cach"] = {
            "trang_thai": CHUA_DO_DUOC,
            "vi_sao": "khong co trong tinh_cach_tai_san.json (thieu OHLC "
                     "hoac chuoi ngan hon 400 bar)"}

    # --- CHI PHI + BIEN DO (D1)
    sy = sy_all.get(ma)
    if sy:
        cbd = {k: sy.get(k) for k in (
            "spread_bps", "phi_nam_mua_pct", "phi_nam_ban_pct",
            "chi_phi_do_tin", "vong_quay_toi_da", "bien_dong_nam_pct",
            "atr_pct_bar", "bien_do_bar_pct", "buoc_goi_y_pct",
            "so_nam", "so_bar", "tu", "den", "nguon")}
        if sy.get("chi_phi_do_tin") == "KHAI":
            cbd["_canh_bao"] = ("spread/phi KHAI BAO (uoc mac dinh) - CHUA do "
                               "tu du lieu hay san that, khong dung de ket "
                               "luan song/chet vi phi")
        ra["chi_phi_bien_do"] = cbd
    else:
        ra["chi_phi_bien_do"] = {
            "trang_thai": CHUA_DO_DUOC,
            "vi_sao": "khong co trong config/ho_so_symbol.json"}

    # --- MUA VU (module chi moi do D1)
    khoa_mv = "%s|D1" % ma
    mv = mv_all.get(khoa_mv)
    if mv:
        rmv = {"tu": mv.get("tu"), "den": mv.get("den"), "so_nam": mv.get("so_nam"),
              "cau_tra_loi": mv.get("cau_tra_loi")}
        phep = {}
        for k in ("M1_thang_trong_nam", "M2_tuan_giao_thang", "M3_ngay_trong_tuan"):
            p = mv.get(k)
            if not p:
                continue
            if p.get("trang_thai") == CHUA_DO_DUOC:
                # Khau do CHINH no da tu ha ve CHUA_DO_DUOC (vd: M3 khong xac
                # dinh duoc nhan thu - xem `ho_so_mua_vu.thu_da_sua`). Giu
                # nguyen trang thai nay, KHONG duoc doc `dat=False` thanh AM.
                phep[k] = {"trang_thai": CHUA_DO_DUOC, "vi_sao": p.get("vi_sao")}
                continue
            muc = {"dat": p.get("dat"), "chenh_bps": p.get("chenh_bps"),
                   "p": p.get("p"), "nhom_cao": p.get("nhom_cao"),
                   "nhom_thap": p.get("nhom_thap")}
            if "canh_bao_nhan" in p:
                muc["canh_bao"] = p["canh_bao_nhan"]
            # song qua CHINH spread cua ma nay khong - can spread THAT (DO/SAN),
            # spread KHAI BAO (mac dinh) khong du de ket luan ca hai chieu.
            if muc["dat"]:
                if sy and sy.get("chi_phi_do_tin") in ("DO", "SAN") and sy.get("spread_bps") is not None:
                    muc["song_qua_spread"] = bool(muc["chenh_bps"] > sy["spread_bps"])
                else:
                    muc["song_qua_spread"] = None
            phep[k] = muc
        rmv["phep_thu"] = phep
        if khung != "D1":
            rmv["_ghi_chu"] = "mua vu moi do o D1, chua do o " + khung
        ra["mua_vu"] = rmv
    else:
        ra["mua_vu"] = {
            "trang_thai": CHUA_DO_DUOC,
            "vi_sao": "khong co %s trong HO_SO_MUA_VU.json (module chi moi "
                     "do D1)" % khoa_mv}

    # --- TUONG QUAN (mot file rieng moi khung: D1/H4/H1)
    tq_ho_so = (tq_all or {}).get("ho_so", {}) if isinstance(tq_all, dict) else {}
    tq = tq_ho_so.get(ma)
    if tq:
        ra["tuong_quan"] = {
            "so_cap_do": tq.get("so_cap"), "r_trung_vi": tq.get("r_trung_vi"),
            "r_tuyet_doi_trung_vi": tq.get("r_tuyet_doi_trung_vi"),
            "on_dinh_trung_vi": tq.get("on_dinh_trung_vi"),
            "cao_nhat": tq.get("cao_nhat", []), "am_nhat": tq.get("am_nhat", []),
            "_ghi_chu": ("chi top-3 moi chieu cho ma nay; bang toan cuc chi "
                        "giu top 400/%s cap |r| lon nhat trong ca kho - mot cap "
                        "CU THE ngoai hai danh sach tren KHONG nam o day, nhung "
                        "dung `ho_so_tai_san.tuong_quan(ma_a, ma_b)` de tinh "
                        "TAI CHO thay vi coi la khong biet (sua 13/09/2026)"
                        % (tq_all.get("so_cap", "?")))}
    else:
        ra["tuong_quan"] = {
            "trang_thai": CHUA_DO_DUOC,
            "vi_sao": "khong co trong HO_SO_TUONG_QUAN_%s.json" % khung.upper()}

    # --- SONG (module chi moi do H4)
    khoa_so = "%s|H4" % ma
    sg = so_all.get(khoa_so)
    if sg and "loi" not in sg:
        song = sg.get("song") or {}
        n = int(song.get("so_cap_day_hoi") or 0)
        if n <= 0:
            ra["song"] = {"trang_thai": CHUA_DO_DUOC,
                         "vi_sao": "zigzag khong tao duoc cap day/hoi nao "
                                  "(du lieu qua ngan hoac qua phang)"}
        else:
            do_tin_song = "DU" if n >= SONG_SO_CAP_DU else "MONG"
            rsong = {
                "khung_do": "H4", "so_cap_day_hoi": n, "do_tin": do_tin_song,
                "bien_do_day_pct_trung_vi": (song.get("bien_do_day_pct") or {}).get("trung_vi"),
                "bien_do_hoi_pct_trung_vi": (song.get("bien_do_hoi_pct") or {}).get("trung_vi"),
                "ty_le_hoi_pct_trung_vi": (song.get("ty_le_hoi_pct") or {}).get("trung_vi"),
                "tre_xac_nhan_bar_trung_vi": (song.get("tre_xac_nhan_bar") or {}).get("trung_vi"),
                "boi_atr_dung": song.get("boi_atr")}
            if khung != "H4":
                rsong["_ghi_chu"] = "song moi do o H4, chua do o " + khung
            if do_tin_song == "MONG":
                rsong["_canh_bao"] = ("chi %d cap day/hoi - duoi nguong %d, "
                                     "dung duoc de goi y TP/SL nhung DUNG tin "
                                     "qua muc" % (n, SONG_SO_CAP_DU))
            ra["song"] = rsong
    else:
        vi_sao = (sg.get("loi") if sg else None) or (
            "khong co %s trong HO_SO_SONG.json" % khoa_so)
        ra["song"] = {"trang_thai": CHUA_DO_DUOC, "vi_sao": vi_sao}

    nhom = ("tinh_cach", "chi_phi_bien_do", "mua_vu", "tuong_quan", "song")
    co = sum(1 for k in nhom if ra[k].get("trang_thai") != CHUA_DO_DUOC)
    ra["do_phu"] = "%d/%d" % (co, len(nhom))
    return ra


# -------------------------------------------------------------- TUONG QUAN 1-1
def tuong_quan(ma_a: str, ma_b: str, khung: str = "D1", *,
               _tuong_quan: dict | None = None) -> dict:
    """Tuong quan giua HAI ma CU THE - lo hong thu 3 da ghi trong bao cao truoc
    (13/09/2026): `ho_so_tuong_quan.py` chi luu top 400/11.960 cap D1 toan cuc
    (cong voi top-3 moi chieu cho tung ma), nen hoi mot cap TUY Y ngoai ca hai
    danh sach do se khong tra loi duoc du thuc te co tinh - truoc ban sua nay
    ham nay tra ve "khong biet" trong nhung truong hop do.

    Thu tu tra loi, RE truoc DAT sau:
      1. Bang toan cuc da luu (top 400 |r|)                    - khong tinh lai
      2. Top-3 rieng cua `ma_a` HOAC `ma_b` (luon co cho moi ma) - khong tinh lai
      3. TINH TAI CHO bang `ho_so_tuong_quan.bang_loi_suat` + `mot_cap` tren
         DUNG hai ma nay (nap du lieu, gong hang ngay, doi song, on dinh cua
         so truot) - cham hon (nap 2 bang gia) nhung tra loi duoc BAT KY cap
         nao, khong con "khong biet" chi vi khong lot top 400.

    Neu ca ba buoc deu that bai (vd mot trong hai ma khong co du lieu, hoac so
    bar chung < nguong `BAR_CHUNG_TOI_THIEU`) thi tra CHUA_DO_DUOC voi vi_sao,
    KHONG bao gio bia mot con so.
    """
    from nhan import ho_so_tuong_quan as TQ
    ma_a, ma_b = str(ma_a).strip(), str(ma_b).strip()
    if ma_a == ma_b:
        return {"trang_thai": CHUA_DO_DUOC, "vi_sao": "hai ma trung nhau",
                "ma_a": ma_a, "ma_b": ma_b}

    tq_all = _tuong_quan if _tuong_quan is not None else _tuong_quan_full(khung)
    cap = (tq_all or {}).get("cap", {})
    for key, nguoc in ((f"{ma_a}|{ma_b}", False), (f"{ma_b}|{ma_a}", True)):
        if key in cap:
            v = dict(cap[key])
            if nguoc:
                v["r"] = -v["r"] if v.get("r") is not None else None
                if "r_min" in v and "r_max" in v:
                    v["r_min"], v["r_max"] = -v["r_max"], -v["r_min"]
            return {**v, "ma_a": ma_a, "ma_b": ma_b, "khung": khung,
                   "nguon": "bang_toan_cuc_da_luu"}

    ho_tq = (tq_all or {}).get("ho_so", {})
    for chu, doi_tac in ((ma_a, ma_b), (ma_b, ma_a)):
        ho = ho_tq.get(chu)
        if not ho:
            continue
        for nhom in ("cao_nhat", "am_nhat"):
            for x in ho.get(nhom, []):
                if x.get("voi") == doi_tac:
                    v = dict(x)
                    if chu == ma_b:            # doi tac la ma_a -> r doi chieu
                        v["r"] = -v["r"] if v.get("r") is not None else None
                        if "r_min" in v and "r_max" in v:
                            v["r_min"], v["r_max"] = -v["r_max"], -v["r_min"]
                    return {**v, "ma_a": ma_a, "ma_b": ma_b, "khung": khung,
                           "nguon": "top3_rieng_cua_%s" % chu}

    # Khong co trong ca hai nguon da luu - TINH TAI CHO thay vi tra "khong biet".
    try:
        bang = TQ.bang_loi_suat([ma_a, ma_b], khung)
        if ma_a not in bang.columns or ma_b not in bang.columns:
            return {"trang_thai": CHUA_DO_DUOC, "ma_a": ma_a, "ma_b": ma_b,
                    "vi_sao": "khong nap duoc gia cho ca hai ma tren khung %s "
                             "(thieu du lieu hoac < %d bar)"
                             % (khung, TQ.BAR_CHUNG_TOI_THIEU)}
        v = TQ.mot_cap(bang[ma_a], bang[ma_b])
        if v is None:
            return {"trang_thai": CHUA_DO_DUOC, "ma_a": ma_a, "ma_b": ma_b,
                    "vi_sao": "hai ma khong du bar CHUNG (>= %d) tren cung "
                             "khoang thoi gian de tinh tuong quan"
                             % TQ.BAR_CHUNG_TOI_THIEU}
        qh = TQ.quan_he_co_hoc(ma_a, ma_b)
        if qh:
            v["co_hoc"] = qh
        if TQ.trung_cong_cu(ma_a, ma_b):
            v["trung"] = True
        return {**v, "ma_a": ma_a, "ma_b": ma_b, "khung": khung,
               "nguon": "tinh_tai_cho (khong co trong bang da luu)"}
    except Exception as e:
        return {"trang_thai": CHUA_DO_DUOC, "ma_a": ma_a, "ma_b": ma_b,
                "vi_sao": "loi khi tinh tai cho: %s: %s" % (type(e).__name__, e)}


# --------------------------------------------------------------- GHEP DUOC
def ghep_duoc(ma: str, khung: str = "D1", *,
             r_am_toi_thieu: float = GHEP_R_AM_TOI_THIEU,
             on_dinh_toi_thieu: float = GHEP_ON_DINH_TOI_THIEU,
             r_trung_toi_thieu: float = TRUNG_R_TOI_THIEU,
             voi: str | None = None,
             ho_so_da_co: dict | None = None, **kwargs) -> dict:
    """Ma nao ghep chan NGUOC duoc voi `ma` (am + on dinh), ma nao TRUNG rui ro.

    Mac dinh chi doc top-3 moi chieu da luu san CHO TUNG MA (`ho_so_tuong_quan.
    tinh`, muc "ho so tung ma") - khong quet lai toan bo cap, vi xep hang "ma
    nao tot nhat trong ca kho" tren TOAN BO 159 ma moi lan goi se cham.

    Truyen `voi="MA_KHAC"` khi ban da co MOT doi tac cu the muon hoi ("X va Y
    co ghep duoc khong") - luc do goi `tuong_quan(ma, voi, khung)` de TINH TAI
    CHO neu can, thay vi chi tra loi duoc khi cap do tinh co lot top-3/top-400.
    """
    ma = str(ma).strip()
    if voi is not None:
        v = tuong_quan(ma, voi, khung)
        if v.get("trang_thai") == CHUA_DO_DUOC:
            return v
        r, on_dinh = v.get("r"), v.get("on_dinh") or 0
        la_am_on_dinh = r is not None and r <= r_am_toi_thieu and on_dinh >= on_dinh_toi_thieu
        la_trung = r is not None and r >= r_trung_toi_thieu and on_dinh >= on_dinh_toi_thieu
        return {"ma": ma, "voi": voi, "khung": khung, **v,
               "am_on_dinh": la_am_on_dinh, "trung_rui_ro": la_trung}

    h = ho_so_da_co if ho_so_da_co is not None else ho_so(ma, khung, **kwargs)
    tq = h["tuong_quan"]
    if tq.get("trang_thai") == CHUA_DO_DUOC:
        return {"trang_thai": CHUA_DO_DUOC, "vi_sao": tq["vi_sao"], "ma": ma}
    am = [x for x in tq.get("am_nhat", [])
         if x.get("voi") != ma and (x.get("r") or 0) <= r_am_toi_thieu
         and (x.get("on_dinh") or 0) >= on_dinh_toi_thieu]
    tr = [x for x in tq.get("cao_nhat", [])
         if x.get("voi") != ma and (x.get("r") or 0) >= r_trung_toi_thieu
         and (x.get("on_dinh") or 0) >= on_dinh_toi_thieu]
    return {"ma": ma, "khung": khung, "am_on_dinh": am, "trung_rui_ro": tr}


# -------------------------------------------------------------------- CHON
def chon(yeu_cau: dict) -> list[dict]:
    """Xep hang ma phu hop cho MOT yeu cau.

    Mo rong `ho_so_symbol.chon_ung_vien` (loc chi phi TRUOC, xep tinh cach
    SAU - xem canh bao GBPPLN/GBPZAR trong module do) bang cach gan them co
    mua vu/song cho tung ung vien. Nhan cung tham so voi `chon_ung_vien`
    (kieu, so_nam_min, spread_toi_da, tran, vong_quay_can, chi_phi_do_duoc)
    cong hai co rieng:

      khung        khung tuong quan dung de xep ghep_duoc (mac dinh D1)
      can_mua_vu   True -> chi giu ma co >=1 phep mua vu dat=True VA song
                   qua CHINH spread cua no (mac dinh False = khong loc, chi
                   gan co de nguoi doc tu quyet)
      can_song_du  True -> chi giu ma co ho so song H4 do_tin='DU'
    """
    from nhan import ho_so_symbol as HSS
    yc = dict(yeu_cau or {})
    can_mua_vu = yc.pop("can_mua_vu", False)
    can_song_du = yc.pop("can_song_du", False)
    khung = yc.pop("khung", "D1")
    ung_vien = HSS.chon_ung_vien(**yc)

    tc_all = _tinh_cach_theo_ma()
    sy_all = _symbol_theo_ma()
    mv_all = _mua_vu_theo_key()
    tq_all = _tuong_quan_full(khung)
    so_all = _song_theo_key()

    ra = []
    for u in ung_vien:
        ma = u["ma"]
        h = ho_so(ma, khung, _tinh_cach=tc_all, _symbol=sy_all, _mua_vu=mv_all,
                 _tuong_quan=tq_all, _song=so_all)
        mua_vu_ok = (h["mua_vu"].get("trang_thai") != CHUA_DO_DUOC and any(
            p.get("dat") and p.get("song_qua_spread") is True
            for p in h["mua_vu"].get("phep_thu", {}).values()))
        song_du = h["song"].get("do_tin") == "DU"
        if can_mua_vu and not mua_vu_ok:
            continue
        if can_song_du and not song_du:
            continue
        u2 = dict(u)
        u2["_mua_vu_dat_va_song_qua_spread"] = mua_vu_ok
        u2["_song_do_tin"] = h["song"].get("do_tin", h["song"].get("trang_thai"))
        ra.append(u2)
    return ra


# ---------------------------------------------------------------- TOM TAT
_GOI_Y_KIEU = {
    "HOI_QUY": "mean-reversion (bollinger_ve / rsi_dao_chieu / ibs_bat_day - "
              "danh vao luc gia lech xa roi keo ve)",
    "XU_HUONG": "breakout / theo xu huong (donchian / momentum_ema / sma_cheo)",
    "TRUNG_TINH": "ca hai huong deu yeu tren thuoc do cau truc - can bang "
                 "chung khac (mua vu, song) truoc khi chon kieu co che"}


def _r(v, n=3):
    """Lam tron hien thi - `None` va gia tri khong phai so giu nguyen."""
    try:
        return round(float(v), n)
    except (TypeError, ValueError):
        return v


def tom_tat(ma: str, khung: str = "D1") -> str:
    """Vai dong NGUOI doc duoc: nen danh kieu gi, buoc/TP/SL, thang nao tranh,
    ghep voi ma nao. Moi dong deu bam vao mot truong trong `ho_so()`."""
    h = ho_so(ma, khung)
    dong = ["=== %s (%s) - do phu %s ===" % (ma, khung, h["do_phu"])]

    tc = h["tinh_cach"]
    if tc.get("trang_thai") == CHUA_DO_DUOC:
        dong.append("Tinh cach: CHUA_DO_DUOC (%s)" % tc["vi_sao"])
    else:
        nhan_tc = tc.get("nhan", "?")
        hurst = tc.get("hurst")
        dong.append("Tinh cach: %s (hurst=%s) -> nghi kieu %s"
                    % (nhan_tc, ("%.3f" % hurst if hurst is not None else "?"),
                       _GOI_Y_KIEU.get(nhan_tc, "?")))
        dong.append("  (nhan nay tuong quan r~-0,57 voi Sharpe that tren 157 "
                    "ma - dung de XEP HANG, khong dung de LOAI mot minh)")

    cp = h["chi_phi_bien_do"]
    if cp.get("trang_thai") == CHUA_DO_DUOC:
        dong.append("Chi phi/bien do: CHUA_DO_DUOC (%s)" % cp["vi_sao"])
    else:
        canh_bao = " [%s]" % cp["_canh_bao"] if "_canh_bao" in cp else ""
        dong.append("Chi phi: spread %s bps (do_tin=%s)%s | phi qua dem "
                    "mua %s%%/nam, ban %s%%/nam"
                    % (_r(cp.get("spread_bps"), 4), cp.get("chi_phi_do_tin"), canh_bao,
                       _r(cp.get("phi_nam_mua_pct")), _r(cp.get("phi_nam_ban_pct"))))
        dong.append("Bien do: ATR/bar %s%% -> buoc luoi/TP1 goi y ~%s%%; %s "
                    "nam du lieu (%s -> %s)"
                    % (_r(cp.get("atr_pct_bar"), 4), _r(cp.get("buoc_goi_y_pct"), 4),
                       _r(cp.get("so_nam"), 1), cp.get("tu"), cp.get("den")))

    mv = h["mua_vu"]
    if mv.get("trang_thai") == CHUA_DO_DUOC:
        dong.append("Mua vu: CHUA_DO_DUOC (%s)" % mv["vi_sao"])
    else:
        phep_thu = mv.get("phep_thu", {})
        chua_do = [(k, p) for k, p in phep_thu.items() if p.get("trang_thai") == CHUA_DO_DUOC]
        hits = [(k, p) for k, p in phep_thu.items()
               if p.get("trang_thai") != CHUA_DO_DUOC and p.get("dat")]
        for k, p in chua_do:
            dong.append("Mua vu [%s]: CHUA_DO_DUOC (%s)" % (k, p.get("vi_sao")))
        if not hits:
            dong.append("Mua vu: KHONG do duoc (%s)" % mv.get("cau_tra_loi"))
        else:
            for k, p in hits:
                sq = p.get("song_qua_spread")
                tag = ("song qua spread" if sq is True else
                      "KHONG du de song qua spread" if sq is False else
                      "chua ro co song qua spread duoc khong (spread KHAI BAO)")
                # Tu 13/09/2026 "canh_bao" o day la GHI NHAN mot nhan thu da
                # duoc SUA va XAC NHAN CHEO (gio UTC + thong ke T6/CN khop
                # nhau) - khong con la loi nghi ngo chua giai quyet nhu truoc,
                # nen KHONG con nhan chu "CANH BAO" de tranh doc nham la loi.
                cb = " - GHI CHU: %s" % p["canh_bao"] if "canh_bao" in p else ""
                dong.append("Mua vu [%s]: chenh %s bps, p=%s -> %s%s"
                           % (k, _r(p["chenh_bps"]), _r(p["p"], 4), tag, cb))

    sg = h["song"]
    if sg.get("trang_thai") == CHUA_DO_DUOC:
        dong.append("Song (H4): CHUA_DO_DUOC (%s)" % sg["vi_sao"])
    else:
        dong.append("Song (H4, do_tin=%s, n=%d cap): day trung vi %s%%, hoi "
                    "trung vi %s%% (~%s%% cua day), tre xac nhan trung vi %s bar"
                    % (sg["do_tin"], sg["so_cap_day_hoi"], _r(sg["bien_do_day_pct_trung_vi"]),
                       _r(sg["bien_do_hoi_pct_trung_vi"]), _r(sg["ty_le_hoi_pct_trung_vi"], 1),
                       _r(sg["tre_xac_nhan_bar_trung_vi"], 1)))
        if "_canh_bao" in sg:
            dong.append("  CANH BAO: %s" % sg["_canh_bao"])
        # NHUNG SO NAY DA DO TU LAU MA KHONG AI IN RA.
        #
        # Chu du an 15/09 hoi: *"1 nam co bao nhieu song, bao nhieu song day/
        # giam, day bao nhieu giam bao nhieu / trong bao lau"*. Kiem lai thi
        # `HO_SO_SONG.json` da co du `song_moi_nam`, `bar_moi_day`,
        # `bar_moi_hoi` tu truoc - chi la `tom_tat` khong in. Mot so da do ma
        # khong hien ra thi voi nguoi dung no bang chua do.
        _s = _song_theo_key().get("%s|%s" % (ma, "H4"), {}).get("song", {})
        if _s:
            dong.append("  nhip: **%s song/nam** | day keo %s bar, hoi %s bar"
                        % (_r(_s.get("song_moi_nam"), 1),
                           _r((_s.get("bar_moi_day") or {}).get("trung_vi"), 1),
                           _r((_s.get("bar_moi_hoi") or {}).get("trung_vi"), 1)))
            ln, xu = _s.get("day_len") or {}, _s.get("day_xuong") or {}
            if ln.get("so") and xu.get("so"):
                dong.append("  doi xung: day LEN %d cai, %s%% / %s bar  |  day "
                            "XUONG %d cai, %s%% / %s bar"
                            % (ln["so"], _r(ln.get("bien_do_pct_trung_vi")),
                               _r(ln.get("bar_trung_vi"), 1),
                               xu["so"], _r(xu.get("bien_do_pct_trung_vi")),
                               _r(xu.get("bar_trung_vi"), 1)))
        dong.append("  -> TP/SL nen lay tu bien do day/hoi THUC TE o tren, "
                    "khong phai boi so ATR dat tay")

    try:
        from nhan import dem_nen as DN
        _d = DN.ho_so(ma, khung)
        _t = _d["bo_dem"]["thuong"]
        dong.append("Nen: tang %s%% | than/bien do %s | doji %s%% | chuoi cung "
                    "mau %s lan ngau nhien"
                    % (_r(_t["ty_le_tang_pct"], 1),
                       _r(_t["than_tren_bien_do"]["trung_vi"], 3),
                       _r(_t["doji_pct"], 1), _r(_d["hon_ngau_nhien_tb"], 3)))
        dong.append("  (do 15/09 tren 134 ma: dem nen KHONG noi them gi so voi "
                    "hurst - chuoi gan nhu hang so giua cac ma. Doc de MO TA, "
                    "dung dung de du bao.)")
    except Exception:
        pass

    # DON THUOC: tinh cach -> CHIEU dat luoi, BUOC, CHAN TROI.
    #
    # `nhan/tinh_cach_chieu.py` ra doi 15/09 de tra loi dung cau hoi cua chu du
    # an (*"cap co trend thi danh ve chieu thuan trend, cap sideway ta danh ve
    # giua"*) - roi nam MO COI ngay tu hom do. Do la nua sau cua chinh module
    # nay: ho so NOI tai san the nao, don thuoc noi NEN LAM GI voi no.
    try:
        from nhan import tinh_cach_chieu as TCC
        dt = TCC.don_thuoc(ma)
        c = dt.get("chieu") or {}
        if c.get("chieu"):
            dong.append("Don thuoc: dat luoi chieu **%s** (do tin %s) - %s"
                        % (c["chieu"], c.get("do_tin"), str(c.get("vi_sao"))[:90]))
        else:
            dong.append("Don thuoc: CHUA_DO_DUOC chieu - %s"
                        % str(c.get("vi_sao"))[:100])
        b = dt.get("buoc") or {}
        ct = dt.get("chan_troi") or dt.get("giu") or {}
        if b.get("buoc_pct"):
            dong.append("  buoc luoi toi thieu %s%% (%.1fx bien do nen)"
                        % (_r(b["buoc_pct"], 3), TCC.BOI_BUOC_TOI_THIEU))
        if ct.get("giu_bar"):
            dong.append("  giu lenh toi thieu %s bar (tu nua doi)"
                        % _r(ct["giu_bar"], 0))
    except Exception as e:
        dong.append("Don thuoc: CHUA_DO_DUOC (%s: %s)"
                    % (type(e).__name__, str(e)[:70]))

    gd = ghep_duoc(ma, khung, ho_so_da_co=h)
    if gd.get("trang_thai") == CHUA_DO_DUOC:
        dong.append("Ghep duoc: CHUA_DO_DUOC (%s)" % gd["vi_sao"])
    else:
        am = gd.get("am_on_dinh", [])
        if am:
            best = am[0]
            dong.append("Ghep tot nhat (chan am, on dinh): %s (r=%s, on_dinh=%s)"
                       % (best["voi"], _r(best["r"]), _r(best["on_dinh"])))
        else:
            dong.append("Ghep duoc: KHONG co doi tac am du manh+on dinh "
                       "(r<=-0.5, on_dinh>=0.85) trong top da luu")
        tr = gd.get("trung_rui_ro", [])
        if tr:
            dong.append("Tranh chay CUNG voi (trung rui ro): "
                       + ", ".join(x["voi"] for x in tr[:3]))

    return "\n".join(dong)


# ---------------------------------------------------------------- THONG KE
def thong_ke_tong_quan(khung: str = "D1") -> dict:
    """Cac con so "khong hoi hot" o dau file - tinh LAI tu 5 nguon goc moi
    lan goi, khong hardcode, de khong troi khi cac module goc chay lai."""
    tc_all = _tinh_cach_theo_ma()
    sy_all = _symbol_theo_ma()
    mv_all = _mua_vu_theo_key()
    tq_d1 = _tuong_quan_full("D1")
    so_all = _song_theo_key()

    phep_keys = ("M1_thang_trong_nam", "M2_tuan_giao_thang", "M3_ngay_trong_tuan")
    n_dat = n_tin_do = n_song_qua = n_nhan_thu_chua_do_duoc = 0
    ma_song_qua = set()
    for v in mv_all.values():
        ma = v.get("ma")
        sy = sy_all.get(ma, {})
        for pk in phep_keys:
            p = v.get(pk, {})
            if p.get("trang_thai") == CHUA_DO_DUOC:
                # Chot chan nhan thu (13/09/2026): khong xac dinh duoc nhan
                # ngay-trong-tuan thi HA VE CHUA_DO_DUOC, khong tinh dat/am.
                n_nhan_thu_chua_do_duoc += 1
                continue
            if not p.get("dat"):
                continue
            n_dat += 1
            if sy.get("chi_phi_do_tin") in ("DO", "SAN"):
                n_tin_do += 1
                if sy.get("spread_bps") is not None and p["chenh_bps"] > sy["spread_bps"]:
                    n_song_qua += 1
                    ma_song_qua.add(ma)

    ho_tq = (tq_d1.get("ho_so") or {})
    n_am_on_dinh = sum(1 for v in ho_tq.values() if any(
        (x.get("r") or 0) <= GHEP_R_AM_TOI_THIEU
        and (x.get("on_dinh") or 0) >= GHEP_ON_DINH_TOI_THIEU
        for x in v.get("am_nhat", [])))
    n_trung = sum(1 for v in ho_tq.values() if any(
        (x.get("r") or 0) >= TRUNG_R_TOI_THIEU
        and (x.get("on_dinh") or 0) >= GHEP_ON_DINH_TOI_THIEU
        for x in v.get("cao_nhat", [])))
    n_doc_lap = sum(1 for v in ho_tq.values()
                   if (v.get("r_tuyet_doi_trung_vi") if v.get("r_tuyet_doi_trung_vi")
                       is not None else 1.0) < 0.05)

    n_song_ok = sum(1 for v in so_all.values()
                    if ((v.get("song") or {}).get("so_cap_day_hoi") or 0) > 0)
    n_song_du = sum(1 for v in so_all.values()
                    if ((v.get("song") or {}).get("so_cap_day_hoi") or 0) >= SONG_SO_CAP_DU)

    tat_ca = (set(tc_all) | set(sy_all) | {k.split("|")[0] for k in mv_all}
             | {k.split("|")[0] for k in so_all} | set(ho_tq))
    du_ca_5 = sum(1 for ma in tat_ca if (
        ma in tc_all and ma in sy_all and ("%s|D1" % ma) in mv_all
        and ma in ho_tq and ("%s|H4" % ma) in so_all))

    return {
        "so_ma_tong": len(tat_ca),
        "mua_vu": {
            "so_dong_ma_khung_co_dat_true": n_dat,
            "trong_do_chi_phi_do_tin_DO_SAN": n_tin_do,
            "trong_do_song_qua_spread_cua_chinh_no": n_song_qua,
            "ma_duy_nhat_song_qua_spread": sorted(ma_song_qua),
            "M3_ha_ve_CHUA_DO_DUOC_do_khong_xac_dinh_duoc_nhan_thu": n_nhan_thu_chua_do_duoc},
        "tuong_quan_D1": {
            "so_ma": len(ho_tq),
            "co_doi_tac_am_on_dinh_de_ghep": n_am_on_dinh,
            "co_doi_tac_duong_manh_trung_rui_ro": n_trung,
            "gan_doc_lap_r_tuyet_doi_trung_vi_duoi_0_05": n_doc_lap},
        "song_H4": {
            "tong_ma_kiem_tra": len(so_all),
            "co_zigzag_do_duoc": n_song_ok,
            "du_tin_cay_n_gte_%d" % SONG_SO_CAP_DU: n_song_du},
        "do_phu_ca_5_nguon": du_ca_5}


# ------------------------------------------------------------- BANG_TAI_SAN
def _tat_ca_ma() -> list[str]:
    tq = _tuong_quan_full("D1")
    mas = (set(_tinh_cach_theo_ma()) | set(_symbol_theo_ma())
          | {k.split("|")[0] for k in _mua_vu_theo_key()}
          | {k.split("|")[0] for k in _song_theo_key()}
          | set((tq.get("ho_so") or {})))
    return sorted(mas)


def _diem_dung_duoc(h: dict) -> int:
    """Xep hang cho BANG_TAI_SAN.md - "dung duoc" o day la CO SO DAY DU DE
    XET, khong phai da co edge."""
    d = sum(1 for k in ("tinh_cach", "chi_phi_bien_do", "mua_vu", "tuong_quan", "song")
           if h[k].get("trang_thai") != CHUA_DO_DUOC)
    if h["chi_phi_bien_do"].get("chi_phi_do_tin") in ("DO", "SAN"):
        d += 1
    if any(p.get("dat") and p.get("song_qua_spread") is True
          for p in h.get("mua_vu", {}).get("phep_thu", {}).values()):
        d += 2
    return d


def sinh_bang_md(khung: str = "D1", duong_dan: Path | None = None) -> Path:
    """Ghi `reports/BANG_TAI_SAN.md`: mot ma mot dong, xep theo do dung duoc,
    kem phan dau tom tat cac con so o `thong_ke_tong_quan()`."""
    duong_dan = duong_dan or BAO_CAO
    tk = thong_ke_tong_quan(khung)
    mas = _tat_ca_ma()
    hang = [ho_so(ma, khung) for ma in mas]
    hang.sort(key=lambda h: -_diem_dung_duoc(h))

    dong = [
        "# Bang tai san - tong hop 5 ho so (%s)" % khung, "",
        "Sinh boi `nhan/ho_so_tai_san.sinh_bang_md()`. KHONG do them gi moi - "
        "chi gop lai 5 module da chay san. Doc cot `do_phu` va `(tin)` truoc "
        "khi tin bat ky con so nao trong hang.", "",
        "## Tom tat do phu / do tin (%d ma, tinh lai luc sinh bang)" % tk["so_ma_tong"],
        "",
        "- Mua vu: %d dong (ma|phep) co `dat=true`; %d trong so co spread "
        "THAT (DO/SAN) de xet chi phi; chi **%d** vua dat=true vua song qua "
        "CHINH spread cua no - tren ma: %s. (%d dong M3 bi HA ve CHUA_DO_DUOC "
        "vi khong xac dinh chac chan duoc nhan thu - xem `thu_da_sua`, sua "
        "13/09/2026; khong con dong nao 'dat=true' mang canh bao lech nhan ma "
        "khong bi chan.)"
        % (tk["mua_vu"]["so_dong_ma_khung_co_dat_true"],
           tk["mua_vu"]["trong_do_chi_phi_do_tin_DO_SAN"],
           tk["mua_vu"]["trong_do_song_qua_spread_cua_chinh_no"],
           ", ".join(tk["mua_vu"]["ma_duy_nhat_song_qua_spread"]) or "(khong co)",
           tk["mua_vu"]["M3_ha_ve_CHUA_DO_DUOC_do_khong_xac_dinh_duoc_nhan_thu"]),
        "- Tuong quan D1: %d/%d ma co doi tac AM+ON DINH de ghep chan nguoc; "
        "%d/%d co doi tac DUONG manh+on dinh (trung rui ro voi mot ma khac); "
        "%d/%d gan doc lap voi ca kho (r tuyet doi trung vi < 0,05)"
        % (tk["tuong_quan_D1"]["co_doi_tac_am_on_dinh_de_ghep"], tk["tuong_quan_D1"]["so_ma"],
           tk["tuong_quan_D1"]["co_doi_tac_duong_manh_trung_rui_ro"], tk["tuong_quan_D1"]["so_ma"],
           tk["tuong_quan_D1"]["gan_doc_lap_r_tuyet_doi_trung_vi_duoi_0_05"], tk["tuong_quan_D1"]["so_ma"]),
        "- Song H4: %d/%d ma co zigzag do duoc (con lai CHUA_DO_DUOC vi du "
        "lieu goc chi co D1); %d/%d du tin cay (n>=%d cap day/hoi)"
        % (tk["song_H4"]["co_zigzag_do_duoc"], tk["song_H4"]["tong_ma_kiem_tra"],
           tk["song_H4"]["du_tin_cay_n_gte_%d" % SONG_SO_CAP_DU],
           tk["song_H4"]["tong_ma_kiem_tra"], SONG_SO_CAP_DU),
        "- Do phu ca 5 nguon cung luc: %d/%d ma" % (tk["do_phu_ca_5_nguon"], tk["so_ma_tong"]),
        "",
        "| ma | do_phu | tinh_cach(hurst) | ATR%/bar | spread bps(tin) | "
        "phi/nam mua-ban% | so nam | mua vu | song day/hoi%(n,tin) | ghep tot nhat |",
        "|---|---|---|---|---|---|---|---|---|---|"]

    for h in hang:
        ma = h["ma"]
        tc, cp, mv, sg = h["tinh_cach"], h["chi_phi_bien_do"], h["mua_vu"], h["song"]
        gd = ghep_duoc(ma, khung, ho_so_da_co=h)

        c_tc = ("%s(%.2f)" % (tc.get("nhan"), tc["hurst"])
               if tc.get("trang_thai") != CHUA_DO_DUOC and tc.get("hurst") is not None else "-")
        c_atr = ("%.3f" % cp["atr_pct_bar"]
                if cp.get("trang_thai") != CHUA_DO_DUOC and cp.get("atr_pct_bar") is not None else "-")
        c_sp = ("%.2f(%s)" % (cp["spread_bps"], cp["chi_phi_do_tin"])
               if cp.get("trang_thai") != CHUA_DO_DUOC and cp.get("spread_bps") is not None else "-")
        c_phi = ("%.2f/%.2f" % (cp.get("phi_nam_mua_pct") or 0.0, cp.get("phi_nam_ban_pct") or 0.0)
                if cp.get("trang_thai") != CHUA_DO_DUOC else "-")
        c_nam = ("%.1f" % cp["so_nam"]
                if cp.get("trang_thai") != CHUA_DO_DUOC and cp.get("so_nam") is not None else "-")

        if mv.get("trang_thai") == CHUA_DO_DUOC:
            c_mv = "-"
        else:
            phep_thu = mv.get("phep_thu", {})
            chua_do = [k for k, p in phep_thu.items() if p.get("trang_thai") == CHUA_DO_DUOC]
            hits = [(k, p) for k, p in phep_thu.items()
                   if p.get("trang_thai") != CHUA_DO_DUOC and p.get("dat")]
            parts = ["%s:CHUA_DO_DUOC" % k.split("_")[0] for k in chua_do]
            for k, p in hits:
                tag = ("OK" if p.get("song_qua_spread") is True else
                      "kem" if p.get("song_qua_spread") is False else "?")
                parts.append("%s:%.0fbps(%s)" % (k.split("_")[0], p["chenh_bps"], tag))
            c_mv = "; ".join(parts) if parts else "khong"

        if sg.get("trang_thai") == CHUA_DO_DUOC:
            c_song = "-"
        else:
            c_song = ("%.2f/%.2f(n=%d,%s)"
                     % (sg.get("bien_do_day_pct_trung_vi") or 0.0,
                        sg.get("bien_do_hoi_pct_trung_vi") or 0.0,
                        sg["so_cap_day_hoi"], sg["do_tin"]))

        c_ghep = ("%s(r=%.2f)" % (gd["am_on_dinh"][0]["voi"], gd["am_on_dinh"][0]["r"])
                 if gd.get("am_on_dinh") else "-")

        dong.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
                   % (ma, h["do_phu"], c_tc, c_atr, c_sp, c_phi, c_nam, c_mv, c_song, c_ghep))

    duong_dan.parent.mkdir(parents=True, exist_ok=True)
    duong_dan.write_text("\n".join(dong), encoding="utf-8")
    return duong_dan


# ---------------------------------------------------------------------- CLI
def main(argv: list[str]) -> int:
    if argv and argv[0] == "bang":
        p = sinh_bang_md(argv[1] if len(argv) > 1 else "D1")
        print("da ghi", p)
        return 0
    if argv and argv[0] == "thongke":
        print(json.dumps(thong_ke_tong_quan(argv[1] if len(argv) > 1 else "D1"),
                         ensure_ascii=False, indent=1))
        return 0
    ma = argv[0] if argv else "XAUUSD"
    khung = argv[1] if len(argv) > 1 else "D1"
    print(tom_tat(ma, khung))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
