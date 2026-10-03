# -*- coding: utf-8 -*-
"""passview.py - TAI KHOAN XEM (investor password) -> LICH SU LENH THAT.

Chu du an 15/09/2026: *"phan doc passview thi can tim tu khoa nay => dang nhap
vao mt5 de xem. Hoac cac trang co san lich su thi quet va xem cach quan li lenh."*

## Passview la gi va vi sao no manh hon dau chan

`nhan/dau_chan.py` luan nguoc KIEU quan li lenh tu duong VON cong khai - doc
duoc y do nhung khong thay tung lenh. Passview di xa hon mot bac: nguoi ta chia
se **mat khau XEM** (investor password, chi doc, khong dat lenh duoc) cua tai
khoan MT5 that de nguoi khac theo doi. Voi no, `MetaTrader5.history_deals_get`
tra ve TUNG DEAL: gio vao, gio ra, khoi luong, gia, lai. Do la lich su lenh
that, khong phai suy tu duong von.

## AN TOAN - ĐAY LA CHI DOC

Investor password KHONG dat/sua/dong lenh duoc - MT5 tu chan o tang giao thuc.
Ta chi goi `history_deals_get` / `history_orders_get` / `positions_get` /
`account_info` (test_passview_lenh.py kiem danh sach nay). Khong bao gio goi
`order_send` voi mot tai khoan passview.

Va: **KHONG commit credential**. Kho tai khoan xem nam o `config/passview.json`,
da them vao `.gitignore`. Mot mat khau xem la cua nguoi khac chia se cong khai,
nhung van khong dua no vao lich su git cua ta.

## LUONG

  1. `boc_tai_khoan(van_ban)` - tach (login, mat_khau, server) tu mot bai post
  2. `luu(...)` - vao `config/passview.json` (ngoai git)
  3. `doc_lich_su(login, mat_khau, server)` - dang nhap, keo history_deals
  4. `phan_tich(deals)` - dung `dau_chan.phan_loai` de doc CACH QUAN LI LENH
  5. `deals_thanh_lenh(deals)` - ghep deal vao/ra thanh TUNG LENH (gio mo, gio dong, gia, lot, SL/TP,
     magic) -> `ghi_lenh_csv` -> `b nc cc boc_lich_su` boc luat quan li lenh + dieu kien vao.
     Buoc 4 chi doc duoc KIEU (luoi/scalp/...); buoc 5 moi cho ra bang lenh de BOC LUAT va lam lai.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

KHO = LAB / "config" / "passview.json"

#: Tu dung ngay TRUOC mot mat khau XEM. Passview thuong ghi ro "investor" de
#: phan biet voi mat khau chinh. Bat theo cac tu nay giam nham mat khau chinh.
DAU_HIEU_XEM = re.compile(
    r"(investor|read[\s-]?only|xem|view|mã\s*xem|mat\s*khau\s*xem|"
    r"投資者|инвестор|观摩|只读)", re.I)

#: Login MT5 that thuong 6-9 chu so. Loai so tron (100000) va so bai viet /
#: gia. `hop_le_login` bo them cac so <100000 va so lap toan chu so giong nhau.
_LOGIN = re.compile(r"\b(\d{6,9})\b")


def _hop_le_login(n: int) -> bool:
    if n < 100000 or n > 999999999:
        return False
    ch = str(n)
    if len(set(ch)) <= 1:          # 1111111
        return False
    if ch.endswith("0000"):        # 100000, 1000000 - so tron, khong phai login
        return False
    return True
#: Link trong bai dan (id trong duong dan khong phai login) va login co nhan di truoc.
_LINK = re.compile(r"(?:https?://|www\.)\S+", re.I)
_LOGIN_NHAN = re.compile(
    r"(?:log\s?in|account(?:\s*(?:no|number|id))?|acc(?:ount)?\s*(?:no|number|id)|tai\s*khoan|\btk\b|\u53e3\u5ea7|\u8d26[\u6237\u53f7])"
    r"\s*[:=#]?\s*(\d{6,9})\b", re.I)
#: Server MT5 THAT co dang `Broker-MT5`, `Broker-MT5 3`, `Exness-Real8`,
#: `ICMarkets-Demo`. Do 15/09/2026 ban long `[- ](?:MT5|Real|...)` bat 902 cum
#: RAC: "Controllable Realism" (khop "Real"), "and Live Trading" (khop "Live").
#: Nen bat GAT: phai co GACH NOI cung `-`, va sau do la MT5/MT4 HOAC
#: Real/Demo/Live co the kem so - "Real" DUNG MOT MINH khong tinh, no la tu
#: tieng Anh thuong. [[luat-do-phai-thay-duoc-cai-co]] theo chieu nguoc: bo do
#: khong duoc bat cai KHONG phai.
_SERVER = re.compile(
    r"\b([A-Za-z][A-Za-z0-9.]{2,20}-(?:"
    r"MT[45](?:[ -]?\d{1,3}|[A-Za-z]{2,8}\d{1,3})?"          # XMGlobal-MT5 7 · ICMarketsSC-MT5-4 · Exness-MT5Real8
    r"|(?:Real|Demo|Live)[ -]?\d{1,3}))\b")                   # Exness-Real8 · XMGlobal-Real 31 · FBS-Real-3
#: Phien 03/10/2026: duoi cu `(?:[- ]?[A-Za-z0-9]{1,10})?` NUOT CA TU KE BEN: "Server: Exness-Real8 Login: 123" cho ra server
#: "Exness-Real8 Login" (dang nhap that bai ma khong ai thay loi), va "XMGlobal-Real 31" (XM - san pho bien nhat o VN) khong bat duoc.

_PASS = re.compile(
    r"(?:pass(?:word)?|mat\s*khau|\bmk\b|\u043f\u0430\u0440\u043e\u043b\u044c|"
    r"\u5bc6\s*\u7801|\u30d1\u30b9\u30ef\u30fc\u30c9|\ube44\ubc00\ubc88\ud638|pwd)"
    r"[^\n:=]{0,18}[:=]\s*([A-Za-z0-9!@#$%^&*._-]{4,32})", re.I)


def boc_tai_khoan(van_ban: str) -> list[dict]:
    """Tach cac bo (login, mat_khau, server) tu mot bai post.

    Tra ve DANH SACH (mot bai co the co nhieu tai khoan). Cai gi khong day du
    ba manh thi BO - mot tai khoan thieu server khong dang nhap duoc, va doan
    server la cach nhanh nhat de bi khoa IP.
    """
    if not van_ban:
        return []
    vb = str(van_ban)
    servers = _SERVER.findall(vb)
    if not servers:
        return []
    # BA MANH PHAI NAM GAN NHAU. Mot bai co the co server MT5 o dau va mot con
    # so 7 chu so o cuoi khong lien quan gi. Passview that ghi ca ba trong mot
    # khoi (login/pass/server lien tiep vai dong). Nen cat vb thanh cua so 300
    # ky tu quanh MOI vi tri server va chi bat login/pass TRONG cua so do.
    #: Tu tieng Anh/Viet thuong bi nham la mat khau - loai.
    _RAC_PASS = {"forgot", "your", "the", "password", "reset", "change",
                 "enter", "email", "please", "click", "here", "login",
                 "account", "mat", "khau", "khong"}
    ra, da_co = [], set()
    for m in _SERVER.finditer(vb):
        sv = m.group(1).strip()
        a, b = max(0, m.start() - 300), min(len(vb), m.end() + 300)
        cua = vb[a:b]
        if not DAU_HIEU_XEM.search(cua):
            continue                    # dau hieu XEM phai o GAN, khong o xa
        # Id tin hieu / bai viet nam trong LINK (mql5.com/signals/2196457) la so 7 chu so hop le nhu mot login: bo link
        # khoi cua so truoc khi tim, va uu tien so co NHAN ("Login:", "Account", "TK") truoc so tran.
        sach = _LINK.sub(" ", cua)
        lg = [int(x) for x in _LOGIN_NHAN.findall(sach) if _hop_le_login(int(x))] or \
             [int(x) for x in _LOGIN.findall(sach) if _hop_le_login(int(x))]
        pw = [x for x in _PASS.findall(sach) if x.lower() not in _RAC_PASS]
        if not lg or not pw:
            continue
        khoa = (lg[0], sv)
        if khoa in da_co:
            continue
        da_co.add(khoa)
        ra.append({"login": lg[0], "mat_khau": pw[0], "server": sv,
                   "co_dau_hieu_xem": True,
                   "servers_khac": []})
    return ra


# ------------------------------------------------------------------ KHO
def _doc() -> dict:
    if not KHO.exists():
        return {"tai_khoan": []}
    try:
        return json.loads(KHO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"tai_khoan": []}


def _ghi_kho(d: dict) -> None:
    """Ghi kho ra dia NGUYEN TU (tep tam + doi ten): mat dien giua luc ghi khong lam hong kho tai khoan."""
    import os
    KHO.parent.mkdir(parents=True, exist_ok=True)
    tam = KHO.with_suffix(".tmp")
    tam.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tam, KHO)


def luu(bo: list[dict], nguon: str = "") -> int:
    """Them tai khoan xem vao kho. Tra so MOI. Khu trung theo (login, server)."""
    d = _doc()
    co = {(t["login"], t["server"]) for t in d["tai_khoan"]}
    moi = 0
    for b in bo:
        khoa = (b["login"], b["server"])
        if khoa in co or not b.get("mat_khau"):
            continue
        co.add(khoa)
        d["tai_khoan"].append(dict(b, nguon=nguon, trang_thai="CHUA_THU"))
        moi += 1
    _ghi_kho(d)
    return moi


def ma_tai_khoan(login, server) -> str:
    """Ma BAM 8 ky tu cua (login, server): dung de goi ten tep / bao cao ma KHONG lo so tai khoan."""
    import hashlib
    return hashlib.sha1(("%s|%s" % (login, server)).encode()).hexdigest()[:8]


def cap_nhat(login, server, **truong) -> bool:
    """Ghi them truong (trang_thai, so_lenh, lan_cuoi...) vao MOT tai khoan trong kho. True neu tim thay."""
    d = _doc()
    for t in d["tai_khoan"]:
        if str(t.get("login")) == str(login) and t.get("server") == server:
            t.update(truong)
            _ghi_kho(d)
            return True
    return False


def danh_sach() -> list[dict]:
    return _doc().get("tai_khoan", [])


# ------------------------------------------------------------------ MT5
class KhongDoc(RuntimeError):
    """Khong doc duoc tai khoan nay - sai pass, sai server, hoac tk da dong."""


#: DEAL_ENTRY_* cua MT5: 0 vao · 1 ra · 2 dao chieu (ra het + vao phan du) · 3 ra bang lenh doi ung
#: DEAL_REASON_*: ai/cai gi dong lenh (TP/SL cham hay tay/EA dong - khac nhau han ve cach quan li)
LY_DO_DEAL = {0: "may_tinh", 1: "di_dong", 2: "web", 3: "ea", 4: "sl", 5: "tp", 6: "stop_out", 7: "rollover", 8: "vmargin",
              9: "chia_co_phieu"}


def _so_dep(x, mac_dinh=0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return mac_dinh


def _deal_dict(d, sl_tp: dict) -> dict:
    """Mot deal MT5 -> dict. Truong tuy chon lay bang getattr (ban MT5 / nha moi gioi khac nhau). SL/TP cua deal VAO
    nam o LENH sinh ra deal (`deal.order`), nen tra theo `sl_tp`."""
    sl, tp = sl_tp.get(int(getattr(d, "order", 0) or 0), (0.0, 0.0))
    ly_do = getattr(d, "reason", None)
    return {"time": int(d.time), "time_msc": int(getattr(d, "time_msc", 0) or 0), "ticket": int(getattr(d, "ticket", 0) or 0),
            "position_id": int(getattr(d, "position_id", 0) or 0), "symbol": str(d.symbol or ""),
            "type": int(d.type), "volume": float(d.volume), "price": float(d.price), "profit": float(d.profit),
            "commission": _so_dep(getattr(d, "commission", 0.0)), "swap": _so_dep(getattr(d, "swap", 0.0)),
            "entry": int(d.entry), "magic": int(getattr(d, "magic", 0) or 0), "reason": -1 if ly_do is None else int(ly_do),
            "comment": str(getattr(d, "comment", "") or "")[:60], "sl": _so_dep(sl), "tp": _so_dep(tp)}


def keo_tu_mt5(mt5, tu=None, den=None) -> dict:
    """Phan DOC THUAN: nhan doi tuong giong module `MetaTrader5` (da dang nhap) -> {account, deals, positions}.

    Tach rieng khoi dang nhap de thu bang MT5 gia tren cloud. CHI goi ham doc (xem docstring dau tep)."""
    import datetime as _dt
    tu = tu or _dt.datetime(2000, 1, 1)
    # may chu MT5 co the o mui gio sau may ta: lay den ngay mai de khong sot deal moi nhat
    den = den or (_dt.datetime.now() + _dt.timedelta(days=2))
    tk = mt5.account_info()
    deals = mt5.history_deals_get(tu, den) or []
    try:
        lenh_ls = mt5.history_orders_get(tu, den) or []
    except Exception:
        lenh_ls = []
    sl_tp = {int(o.ticket): (_so_dep(getattr(o, "sl", 0.0)), _so_dep(getattr(o, "tp", 0.0))) for o in lenh_ls}
    pos = mt5.positions_get() or []
    return {
        "account": None if tk is None else {
            "login": tk.login, "server": tk.server,
            "balance": tk.balance, "equity": tk.equity,
            "profit": tk.profit, "currency": tk.currency,
            # `trade_mode`: 0 demo / 1 contest / 2 real
            "loai": {0: "DEMO", 1: "CONTEST", 2: "REAL"}.get(int(tk.trade_mode), tk.trade_mode)},
        "deals": [_deal_dict(d, sl_tp) for d in deals],
        "positions": [{"symbol": p.symbol, "volume": float(p.volume), "type": int(p.type), "profit": float(p.profit),
                       "magic": int(getattr(p, "magic", 0) or 0)} for p in pos]}


def doc_lich_su(login: int, mat_khau: str, server: str,
                cho_giay: int = 25) -> dict:
    """Dang nhap CHI DOC va keo toan bo history deals.

    Tra {account, deals, positions}. CHI GOI HAM DOC - khong bao gio order_send.
    """
    import MetaTrader5 as mt5
    from chay_tester_z5 import XM_EXE
    # Terminal chi co MOT - phai giu khoa; va WARP phai tat de ket noi may chu.
    from nhan import khoa_tester as KT
    from nhan import ngan_sach as NS
    with NS.giu_warp(False, "passview"), KT.giu("passview %s" % login):
        ok = mt5.initialize(path=str(XM_EXE), login=int(login),
                            password=str(mat_khau), server=str(server),
                            timeout=cho_giay * 1000)
        if not ok:
            loi = mt5.last_error()
            mt5.shutdown()
            raise KhongDoc("initialize that bai: %s" % (loi,))
        try:
            return keo_tu_mt5(mt5)
        finally:
            mt5.shutdown()


def _duong_von(deals: list[dict]) -> tuple:
    """Dung von (lai cong don) va tai (khoi luong mo) tung buoc thoi gian.

    Tra ve dinh dang ma `dau_chan.dac_trung` an: von[:, (t, dinh, day)] va
    tai[:, (t, khoi_luong)]. Xap xi: von day = von dinh (khong co lo treo tung
    tick tu history deals, chi co lai chot). Nen `nhoi_khi_lo` se yeu hon dau
    chan that - va do la gioi han da biet cua nguon nay.
    """
    import numpy as np
    ds = sorted(deals, key=lambda d: d["time"])
    von_cong, t, dinh, day, mo = 0.0, [], [], [], []
    tai_hien = 0.0
    for d in ds:
        von_cong += d["profit"]
        # entry: 0 = mo, 1 = dong; type 0 buy / 1 sell
        if d["entry"] == 0:
            tai_hien += d["volume"]
        else:
            tai_hien = max(0.0, tai_hien - d["volume"])
        t.append(d["time"])
        dinh.append(von_cong)
        day.append(von_cong)
        mo.append(tai_hien)
    if not t:
        return None, None, None
    von = np.column_stack([t, dinh, day]).astype(float)
    tai = np.column_stack([t, mo]).astype(float)
    loi = np.array([d["profit"] for d in ds if d["entry"] == 1], float)
    return von, tai, loi


# ------------------------------------------------------------------ DEAL -> LENH
_EPS = 1e-8


def _khoa_sap(i: int, d: dict) -> tuple:
    """Thu tu xu ly deal: theo gio (den mili-giay, ticket neu co); cung luc thi deal VAO truoc deal RA."""
    return (d["time"], d.get("time_msc") or 0, d.get("ticket") or 0, 0 if d.get("entry") in (0, 2, None) else 1, i)


def _gio_iso(epoch) -> str:
    import datetime as _dt
    return _dt.datetime.fromtimestamp(int(epoch), _dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def deals_thanh_lenh(deals: list[dict]) -> dict:
    """Ghep deal VAO / RA thanh TUNG LENH - dung dinh dang `boc_lich_su.chuan_hoa` doc duoc.

    Deal chi la tung lan khop; `boc_lich_su` can tung LENH (gio mo, gio dong, gia mo, gia dong, lot). Ghep theo `position_id`
    (neu deal khong co thi theo ma), kieu VAO-TRUOC-RA-TRUOC (FIFO), nen:
      * chot tung phan (mot lenh vao 0.3 lot, ra 0.1 + 0.2) -> 2 lenh, cung gia mo;
      * tai khoan netting cong don (vao 2 lan, ra 1 lan) -> 2 lenh, moi lenh giu gia/gio vao RIENG;
      * deal DAO CHIEU (entry=2): phan ra het lenh cu, phan du mo lenh moi nguoc chieu;
      * deal khong phai mua/ban (nap/rut tien, thuong, phi...) bo qua; deal RA khong co deal VAO (lich su bi cat) dem rieng.
    `loi` = lai deal RA (profit + swap + phi) + phi cua deal VAO chia theo ty le lot - tuc LAI RONG theo phan lot khop.
    Lenh chua dong: `dong` = None, `gia_dong` = None, `loi` = None (khong bia lai tam tinh).

    Tra {"lenh": [...], "khong_phai_lenh", "ra_mo_coi", "chua_dong"}. Moi lenh: mo, dong (chuoi UTC-giong gio may chu), chieu
    ('buy'/'sell' - tranh nham enum 0/1), lot, gia_mo, gia_dong, loi, phi, sl, tp, ma, magic, position_id, ly_do_dong, ghi_chu."""
    from collections import deque
    ds = sorted(((i, d) for i, d in enumerate(deals)), key=lambda x: _khoa_sap(*x))
    hang: dict = {}                     # (khoa nhom, chieu cua lenh DANG MO) -> deque cac manh con mo
    ra, khong_lenh, mo_coi, rows = [], 0, 0, []

    def them_manh(khoa, d, lot, phi):
        chieu = 1 if d["type"] == 0 else -1
        hang.setdefault((khoa, chieu), deque()).append(
            {"d": d, "con": lot, "tong": lot, "phi_vao": phi, "chieu": chieu})

    def khoa_nhom(d):
        return d.get("position_id") or ("ma", d.get("symbol"))

    for _i, d in ds:
        if d.get("type") not in (0, 1) or not d.get("symbol"):
            khong_lenh += 1
            continue
        vol = float(d["volume"])
        if vol <= _EPS:
            khong_lenh += 1
            continue
        khoa = khoa_nhom(d)
        entry = d.get("entry", 0)
        phi_deal = float(d.get("commission", 0.0)) + float(d.get("swap", 0.0))
        if entry == 0:
            them_manh(khoa, d, vol, float(d.get("commission", 0.0)))
            continue
        # RA (1), RA-BANG-LENH-DOI-UNG (3) hoac DAO CHIEU (2): khop voi lenh dang mo NGUOC chieu deal
        chieu_dang_mo = -1 if d["type"] == 0 else 1
        q = hang.get((khoa, chieu_dang_mo))
        con = vol
        while con > _EPS and q:
            m = q[0]
            lay = min(con, m["con"])
            ty_le_ra, ty_le_vao = lay / vol, lay / m["tong"]
            loi_tho = float(d["profit"]) * ty_le_ra
            phi = phi_deal * ty_le_ra + m["phi_vao"] * ty_le_vao
            rows.append({"d_vao": m["d"], "d_ra": d, "lot": lay, "loi": loi_tho + phi, "phi": phi})
            m["con"] -= lay
            con -= lay
            if m["con"] <= _EPS:
                q.popleft()
        if con > _EPS:
            if entry == 2:              # phan du cua deal dao chieu = lenh MOI cung chieu deal
                them_manh(khoa, d, con, float(d.get("commission", 0.0)) * con / vol)
            else:
                mo_coi += 1
    for (khoa, _c), q in hang.items():
        for m in q:
            if m["con"] > _EPS:
                rows.append({"d_vao": m["d"], "d_ra": None, "lot": m["con"], "loi": None,
                             "phi": m["phi_vao"] * m["con"] / m["tong"]})
    for r in rows:
        v, o = r["d_vao"], r["d_ra"]
        ra.append({"mo": _gio_iso(v["time"]), "dong": _gio_iso(o["time"]) if o else None,
                   "chieu": "buy" if v["type"] == 0 else "sell", "lot": round(r["lot"], 8),
                   "gia_mo": v["price"], "gia_dong": o["price"] if o else None,
                   "loi": None if r["loi"] is None else round(r["loi"], 6), "phi": round(r["phi"], 6),
                   "sl": v.get("sl") or None, "tp": v.get("tp") or None, "ma": v["symbol"],
                   "magic": int(v.get("magic") or 0), "position_id": int(v.get("position_id") or 0),
                   "ly_do_dong": LY_DO_DEAL.get(o.get("reason"), "") if o else "",
                   "ghi_chu": str(v.get("comment") or "")[:60], "_t": (v["time"], v.get("time_msc") or 0, v.get("ticket") or 0)})
    ra.sort(key=lambda x: (x["_t"], x["dong"] or "9999"))
    for x in ra:
        del x["_t"]
    return {"lenh": ra, "khong_phai_lenh": khong_lenh, "ra_mo_coi": mo_coi,
            "chua_dong": sum(1 for x in ra if x["dong"] is None)}


#: Cot tep lenh: ten chuan cua `boc_lich_su` + vai cot phu (magic, position_id...) de nguoi doc lai doi chieu
COT_LENH = ("mo", "dong", "chieu", "lot", "gia_mo", "gia_dong", "loi", "sl", "tp", "ma", "magic", "position_id",
            "ly_do_dong", "ghi_chu")


def ghi_lenh_csv(lenh: list[dict], ma_nguon: str, thu_muc=None, toi_thieu: int = 30) -> list[dict]:
    """Ghi lenh ra CSV trong `du_lieu_cao/lenh/` (NAM TRONG lab/ de `b nc cc boc_lich_su {"tep": ...}` nhan; bi gitignore).

    Mot ma (symbol) -> mot tep (`boc_lich_su` chi co nghia tren MOT ma). Ma co >= 2 magic moi du `toi_thieu` lenh thi them tep
    rieng tung magic (EA khac nhau trong cung tai khoan). Ten tep chi chua ma bam `ma_nguon` (KHONG chua so tai khoan).
    Tra [{tep (tuong doi voi lab/), ma, magic|None, so_lenh, so_dong, tu, den}]; ma it hon `toi_thieu` lenh -> khong ghi."""
    import csv
    goc = Path(thu_muc) if thu_muc else LAB / "du_lieu_cao" / "lenh"
    goc.mkdir(parents=True, exist_ok=True)
    theo_ma: dict = {}
    for x in lenh:
        theo_ma.setdefault(str(x["ma"]), []).append(x)
    ra = []

    def ghi(ten, ds, ma, magic):
        duong = goc / ten
        with duong.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(COT_LENH)
            for x in ds:
                w.writerow(["" if x.get(c) is None else x.get(c) for c in COT_LENH])
        try:
            tep = str(duong.resolve().relative_to(LAB.resolve()))
        except ValueError:
            tep = str(duong)
        dong = [x for x in ds if x["dong"]]
        ra.append({"tep": tep.replace("\\", "/"), "ma": ma, "magic": magic, "so_lenh": len(ds), "so_dong": len(dong),
                   "tu": ds[0]["mo"], "den": max([x["dong"] or x["mo"] for x in ds])})

    for ma, ds in sorted(theo_ma.items()):
        if len(ds) < toi_thieu:
            continue
        sach = re.sub(r"[^A-Za-z0-9]", "", ma) or "X"
        ghi("%s_%s.csv" % (ma_nguon, sach), ds, ma, None)
        theo_magic: dict = {}
        for x in ds:
            theo_magic.setdefault(int(x.get("magic") or 0), []).append(x)
        lon = {k: v for k, v in theo_magic.items() if len(v) >= toi_thieu}
        if len(lon) >= 2:
            for k, v in sorted(lon.items()):
                ghi("%s_%s_m%d.csv" % (ma_nguon, sach, k), v, ma, k)
    return ra


def phan_tich(kq: dict) -> dict:
    """Doc CACH QUAN LI LENH tu lich su - dung chinh bo `dau_chan`."""
    from nhan import dau_chan as DC
    deals = kq.get("deals") or []
    von, tai, loi = _duong_von(deals)
    dac = DC.dac_trung(von, tai, loi)
    # Bo sung cac truong `phan_loai` can ma dac_trung khong tinh.
    dong = [d for d in deals if d["entry"] == 1]
    thang = 100.0 * sum(1 for d in dong if d["profit"] > 0) / max(len(dong), 1)
    dac["thang_pct"] = thang
    dac["so_lenh"] = len(dong)
    kieu, ly_do = DC.phan_loai(dac)
    sym = {}
    for d in deals:
        sym[d["symbol"]] = sym.get(d["symbol"], 0) + 1
    return {"kieu": kieu, "ly_do": ly_do, "dac_trung": dac,
            "so_deal": len(deals), "so_lenh_dong": len(dong),
            "symbol_hay_danh": sorted(sym.items(), key=lambda x: -x[1])[:6],
            "account": kq.get("account")}


def quet_kho(gioi_han: int = 5000) -> dict:
    """Quet ban doc trong nao.db, tach tai khoan xem, luu vao config/passview.json.

    Chay tren TOAN BO ban doc chu khong chi cai qua bo loc luat: mot bai chia
    se tai khoan thuong KHONG co "buy when RSI", nen di qua `boc_llm.ung_vien`
    thi bo lo het. O day chi la regex, re - quet ca kho van duoi mot giay.
    """
    from nhan import so as SO
    ds = SO.nhieu(
        "SELECT n.van_ban, t.url FROM noi_dung n "
        "LEFT JOIN tai_lieu t ON t.id = n.tai_lieu_id "
        "WHERE n.so_ky_tu > 40 LIMIT ?", gioi_han) or []
    tong, co_dau_hieu = 0, 0
    for r in ds:
        d = dict(r)
        vb = d.get("van_ban") or ""
        if not DAU_HIEU_XEM.search(vb):
            continue
        co_dau_hieu += 1
        bo = boc_tai_khoan(vb)
        if bo:
            tong += luu(bo, nguon=str(d.get("url") or "")[:120])
    return {"ban_doc_quet": len(ds), "co_dau_hieu_xem": co_dau_hieu,
            "tai_khoan_moi": tong, "tong_trong_kho": len(danh_sach())}


def _cli(argv: list) -> int:
    if argv and argv[0] == "boc" and len(argv) > 1:
        vb = Path(argv[1]).read_text(encoding="utf-8") if Path(argv[1]).exists() \
            else argv[1]
        bo = boc_tai_khoan(vb)
        print(json.dumps(bo, ensure_ascii=False, indent=1))
        return 0
    if argv and argv[0] == "quet":
        import json as _j
        print(_j.dumps(quet_kho(), ensure_ascii=False, indent=1))
        return 0
    if argv and argv[0] == "danh-sach":
        for t in danh_sach():
            print("%-10s %-22s %s" % (t["login"], t["server"],
                                      t.get("trang_thai")))
        return 0
    if argv and argv[0] == "doc" and len(argv) >= 4:
        kq = doc_lich_su(int(argv[1]), argv[2], argv[3])
        print(json.dumps(phan_tich(kq), ensure_ascii=False, indent=1, default=str))
        return 0
    print("passview quet                 - quet ca kho ban doc -> tai khoan xem")
    print("passview boc <van_ban|file>   - tach (login,pass,server)")
    print("passview danh-sach            - kho tai khoan xem")
    print("passview doc <login> <pass> <server>  - doc lich su + phan loai")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
