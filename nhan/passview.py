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
Ta chi goi `history_deals_get` / `positions_get` / `account_info`. Khong bao
gio goi `order_send` voi mot tai khoan passview.

Va: **KHONG commit credential**. Kho tai khoan xem nam o `config/passview.json`,
da them vao `.gitignore`. Mot mat khau xem la cua nguoi khac chia se cong khai,
nhung van khong dua no vao lich su git cua ta.

## LUONG

  1. `boc_tai_khoan(van_ban)` - tach (login, mat_khau, server) tu mot bai post
  2. `luu(...)` - vao `config/passview.json` (ngoai git)
  3. `doc_lich_su(login, mat_khau, server)` - dang nhap, keo history_deals
  4. `phan_tich(deals)` - dung `dau_chan.phan_loai` de doc CACH QUAN LI LENH
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
#: Server MT5 THAT co dang `Broker-MT5`, `Broker-MT5 3`, `Exness-Real8`,
#: `ICMarkets-Demo`. Do 15/09/2026 ban long `[- ](?:MT5|Real|...)` bat 902 cum
#: RAC: "Controllable Realism" (khop "Real"), "and Live Trading" (khop "Live").
#: Nen bat GAT: phai co GACH NOI cung `-`, va sau do la MT5/MT4 HOAC
#: Real/Demo/Live co the kem so - "Real" DUNG MOT MINH khong tinh, no la tu
#: tieng Anh thuong. [[luat-do-phai-thay-duoc-cai-co]] theo chieu nguoc: bo do
#: khong duoc bat cai KHONG phai.
_SERVER = re.compile(
    r"\b([A-Za-z][A-Za-z0-9.]{2,20}-(?:MT[45]|(?:Real|Demo|Live)\d{1,3})"
    r"(?:[- ]?[A-Za-z0-9]{1,10})?)\b")

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
        lg = [int(x) for x in _LOGIN.findall(cua) if _hop_le_login(int(x))]
        pw = [x for x in _PASS.findall(cua) if x.lower() not in _RAC_PASS]
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
    KHO.parent.mkdir(parents=True, exist_ok=True)
    KHO.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return moi


def danh_sach() -> list[dict]:
    return _doc().get("tai_khoan", [])


# ------------------------------------------------------------------ MT5
class KhongDoc(RuntimeError):
    """Khong doc duoc tai khoan nay - sai pass, sai server, hoac tk da dong."""


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
            import datetime as _dt
            tk = mt5.account_info()
            deals = mt5.history_deals_get(
                _dt.datetime(2000, 1, 1), _dt.datetime.now()) or []
            pos = mt5.positions_get() or []
            return {
                "account": None if tk is None else {
                    "login": tk.login, "server": tk.server,
                    "balance": tk.balance, "equity": tk.equity,
                    "profit": tk.profit, "currency": tk.currency,
                    # `trade_mode`: 0 demo / 1 contest / 2 real
                    "loai": {0: "DEMO", 1: "CONTEST", 2: "REAL"}.get(
                        int(tk.trade_mode), tk.trade_mode)},
                "deals": [{"time": int(d.time), "symbol": d.symbol,
                           "type": int(d.type), "volume": float(d.volume),
                           "price": float(d.price), "profit": float(d.profit),
                           "entry": int(d.entry)} for d in deals],
                "positions": [{"symbol": p.symbol, "volume": float(p.volume),
                               "type": int(p.type), "profit": float(p.profit)}
                              for p in pos]}
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
