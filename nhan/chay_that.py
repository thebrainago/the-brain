# -*- coding: utf-8 -*-
"""chay_that.py - DUONG TU MOT HE DA QUA TESTER RA TAI KHOAN THAT.

## Vi sao file nay ton tai

Chu du an 15/09/2026: *"Vay xay duong do."*

Hai he AUDCAD qua duoc MT5 tester tu 13/09 va nam yen ba ngay. Kiem lai thi
**khong co mot dong ma nao trong lab goi `order_send`**: ca he thong do duoc moi
thu tru cai cuoi cung. Cai phanh thi da co tu 11/09 (`nhan/han_muc.py`,
`b phanh`) - no chi chua co gi de phanh.

## VI SAO CHAY BANG PYTHON CHU KHONG PHAI EA TREN CHART

Bo dich MQL5 rat tot cho tester (mot lan boot, 3.000 pass), nhung dua no ra
chay that thi moi loi dich tro thanh tien. Va do 15/09 cho thay bo dich CHUA
phu het kho (226/3.217 chua dich duoc) [[bo-dich-mq5-la-nut-that]].

Chay bang Python thi tin hieu sinh ra tu **dung ma da backtest**
(`ngu_phap.sinh_tu_spec`) - khong co ban dich thu hai de lech. Hai he dang noi
toi danh 0,3-0,6 lenh/TUAN tren H4, nen khong can do tre mili giay.

Danh doi: phai co mot tien trinh Python song (VPS). Do la viec da biet tu
[[v6-van-hanh-thuc-te]].

## BA CHOT AN TOAN, khong cai nao tu mo

1. **Mac dinh la DIEN TAP** (`that=False`): tinh, ghi nhat ky, khong gui lenh.
2. **Tai khoan TIEN THAT bi tu choi** tru khi khai `cho_phep_tien_that=True`
   trong dang ky VA truyen `--tien-that`. Hai chia khoa, o hai cho khac nhau.
3. **`han_muc.duoc_vao_lenh` phai tra True.** Phanh mac dinh la BAT: mot he
   chua khai han muc thi khong vao lenh nao.

## CHI HANH DONG O BAR DA DONG

Tin hieu tinh tren bar cuoi CUNG DA DONG, khong phai bar dang chay. Do la dung
gia dinh cua backtest; dung bar dang chay la nhin truoc, va no se cho mot chuoi
lai dep hon backtest - dau hieu de bi doc nham thanh "chay that tot hon".
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

DANG_KY = LAB / "config" / "he_chay_that.json"
NHAT_KY = LAB / "nhat_ky" / "chay_that.jsonl"

#: Khung -> giay. Dung de biet bar cuoi da dong chua.
GIAY_KHUNG = {"M1": 60, "M5": 300, "M15": 900, "M30": 1800,
              "H1": 3600, "H4": 14400, "D1": 86400}

#: MT5 `account_info().trade_mode`
TK_DEMO, TK_CUOC_THI, TK_TIEN_THAT = 0, 1, 2


# --------------------------------------------------------------- DANG KY
def _doc(p: Path) -> dict:
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def danh_sach() -> dict:
    return _doc(DANG_KY)


def dang_ky(he: str, ma: str, khung: str, co_che: str, lot: float,
            magic: int, giu_bar: int = 0, bat: bool = False,
            cho_phep_tien_that: bool = False, ghi_chu: str = "") -> dict:
    """Ghi mot he vao danh sach chay. `bat=False` = co ten nhung chua chay."""
    d = danh_sach()
    d[he] = {"ma": ma, "khung": khung, "co_che": co_che, "lot": float(lot),
             "magic": int(magic), "giu_bar": int(giu_bar), "bat": bool(bat),
             "cho_phep_tien_that": bool(cho_phep_tien_that),
             "ghi_chu": ghi_chu, "dang_ky_luc": datetime.now().isoformat(" ", "seconds")}
    DANG_KY.parent.mkdir(parents=True, exist_ok=True)
    DANG_KY.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d[he]


def ghi_nhat_ky(muc: dict) -> None:
    """MOI quyet dinh deu ghi, ke ca quyet dinh KHONG LAM GI.

    Mot nhat ky chi ghi luc vao lenh thi khong tra loi duoc cau hoi quan trong
    nhat khi he im: no dang cho, hay no da chet tu hom kia.
    """
    muc = dict(muc, luc=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    NHAT_KY.parent.mkdir(parents=True, exist_ok=True)
    with NHAT_KY.open("a", encoding="utf-8") as f:
        f.write(json.dumps(muc, ensure_ascii=False) + "\n")


# --------------------------------------------------------------- TIN HIEU
def spec_cua(ten: str) -> dict | None:
    from nhan import ngu_phap as NP
    for c in NP.doc_kho():
        if c.get("ten") == ten:
            return c
    return None


def tin_hieu(spec: dict, df) -> float:
    """Phoi nhiem MUC TIEU o bar cuoi da dong: -1 / 0 / +1 (hoac phan so).

    Dung `ngu_phap.sinh_tu_spec` - **dung ham da sinh ra moi con so backtest**.
    """
    import numpy as np
    from nhan import ngu_phap as NP
    v = np.asarray(NP.sinh_tu_spec(spec, df), float)
    if not len(v):
        return 0.0
    x = float(v[-1])
    return 0.0 if not np.isfinite(x) else x


# ------------------------------------------------------------------ MT5
class ChuaDoDuoc(RuntimeError):
    """Moi truong chua san sang. KHAC voi 'khong co tin hieu'."""


def _ly_do_that_bai() -> list:
    """Doc log terminal de noi VI SAO khong noi duoc - dung doan.

    `IPC timeout` la trieu chung chung cho moi kieu hong. Do 15/09/2026: hai
    lan khoi dong luc 15:24 va 15:34 deu co dong `Terminal ... started` va
    `MCP started` nhung **khong co dong `Network ... authorized`** - terminal
    mo len roi nam im, nen IPC khong bao gio san sang. Log noi ngay; con
    `last_error()` thi khong.
    """
    from chay_tester_z5 import XM_DATA
    import time as _t
    f = XM_DATA / "logs" / (_t.strftime("%Y%m%d") + ".log")
    if not f.exists():
        return ["khong co log terminal hom nay (%s)" % f.name]
    try:
        van = f.read_bytes().decode("utf-16-le", errors="replace")
    except OSError as e:
        return ["khong doc duoc log: %s" % e]
    dong = [" ".join(x.split()) for x in van.split(chr(10)) if x.strip()]
    ra, co_auth = [], False
    for x in dong[-40:]:
        if "authorized on" in x:
            co_auth = True
        for manh in ("authorization", "Invalid account", "not exist",
                     "cannot connect", "no connection", "failed"):
            if manh.lower() in x.lower():
                ra.append(x[:140])
                break
    if not co_auth:
        ra.insert(0, "terminal KHOI DONG nhung KHONG CO dong `authorized on` - "
                     "no chua dang nhap duoc vao may chu")
    return ra[:6] or ["log khong noi gi bat thuong - xem %s" % f]


def _mt5(cho_giay: float = 120.0):
    """Mo MT5 va TU DANG NHAP. Dong terminal cu truoc - may chi co MOT.

    Tai khoan khai NGAY o day chu khong dua vao trang thai truoc do: do dung
    bai hoc cua `bi_mat.khoi_common_ini` (*"dang nhap dong lenh KHONG luu tai
    khoan vao ho so terminal"*), va do la dieu kien de he chay hang thang tren
    VPS ma khong co nguoi bam `File -> Login`.
    """
    import MetaTrader5 as mt5
    from chay_tester_z5 import XM_EXE, dong_terminal
    from nhan import bi_mat as BM
    # `nhan/dang_nhap_mt5.py` ton tai tu truoc voi dung muc dich nay ("de
    # tester chay duoc khi khong co nguoi") va nam MO COI. Toi da viet lai mot
    # ban thu hai o day ma khong biet - dung cai benh minh dang di chua. Nay
    # goi no truoc; no chon dung server chay duoc trong danh sach, thu nay chi
    # tu lam khi no khong dung duoc.
    try:
        from nhan import dang_nhap_mt5 as DN5
        DN5.san_sang("XM", in_ra=lambda *a: None)
    except Exception:
        pass
    dong_terminal()
    time.sleep(2)
    d = BM.lay("mt5", "XM") or {}
    tham = {"path": str(XM_EXE), "timeout": int(cho_giay * 1000)}
    if d.get("login") and d.get("mat_khau"):
        tham.update(login=int(d["login"]), password=str(d["mat_khau"]),
                    server=str(d.get("server_chay_duoc")
                               or (d.get("servers") or [""])[0]))
    if not mt5.initialize(**tham):
        loi = mt5.last_error()
        mt5.shutdown()
        raise ChuaDoDuoc("khong mo duoc MT5: %s\n   -> %s"
                         % (loi, "\n   -> ".join(_ly_do_that_bai())))
    return mt5


def _bar(mt5, ma: str, khung: str, n: int = 600):
    import pandas as pd
    k = getattr(mt5, "TIMEFRAME_" + khung.upper(), None)
    if k is None:
        raise ChuaDoDuoc("khung khong biet: %s" % khung)
    if not mt5.symbol_select(ma, True):
        raise ChuaDoDuoc("khong chon duoc ma %s trong Market Watch" % ma)
    r = mt5.copy_rates_from_pos(ma, k, 0, n)
    if r is None or len(r) < 50:
        raise ChuaDoDuoc("khong lay du bar cho %s %s" % (ma, khung))
    df = pd.DataFrame(r)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.set_index("time")[["open", "high", "low", "close", "tick_volume"]]
    # BO BAR DANG CHAY. Bar cuoi cua `copy_rates_from_pos` la bar HIEN TAI,
    # chua dong - dung no la nhin truoc.
    return df.iloc[:-1]


def _vi_the(mt5, ma: str, magic: int) -> float:
    """Phoi nhiem hien tai theo lot co dau. 0 = khong co vi the."""
    ds = mt5.positions_get(symbol=ma) or []
    tong = 0.0
    for p in ds:
        if int(p.magic) != int(magic):
            continue
        tong += float(p.volume) * (1.0 if p.type == mt5.POSITION_TYPE_BUY else -1.0)
    return tong


def _dong_het(mt5, ma: str, magic: int) -> list:
    ra = []
    for p in (mt5.positions_get(symbol=ma) or []):
        if int(p.magic) != int(magic):
            continue
        t = mt5.symbol_info_tick(ma)
        ban = p.type == mt5.POSITION_TYPE_BUY
        r = mt5.order_send({
            "action": mt5.TRADE_ACTION_DEAL, "position": p.ticket,
            "symbol": ma, "volume": float(p.volume),
            "type": mt5.ORDER_TYPE_SELL if ban else mt5.ORDER_TYPE_BUY,
            "price": (t.bid if ban else t.ask) if t else 0.0,
            "magic": int(magic), "deviation": 20,
            "comment": "chay_that dong"})
        ra.append({"ticket": int(p.ticket), "ma_tra_ve": int(getattr(r, "retcode", -1))})
    return ra


def _mo(mt5, ma: str, magic: int, lot: float, mua: bool) -> dict:
    t = mt5.symbol_info_tick(ma)
    if t is None:
        raise ChuaDoDuoc("khong co gia cho %s" % ma)
    r = mt5.order_send({
        "action": mt5.TRADE_ACTION_DEAL, "symbol": ma, "volume": float(lot),
        "type": mt5.ORDER_TYPE_BUY if mua else mt5.ORDER_TYPE_SELL,
        "price": t.ask if mua else t.bid, "magic": int(magic),
        "deviation": 20, "comment": "chay_that"})
    return {"ma_tra_ve": int(getattr(r, "retcode", -1)),
            "mo_ta": str(getattr(r, "comment", "")),
            "ticket": int(getattr(r, "order", 0) or 0)}


# ------------------------------------------------------------------ NHIP
def mot_nhip(that: bool = False, cho_tien_that: bool = False,
             chi_he: str = "") -> list:
    """Mot vong quyet dinh cho MOI he dang bat. Tra ve danh sach ban ghi."""
    from nhan import han_muc as HM
    d = danh_sach()
    if not d:
        return [{"trang_thai": "CHUA_DO_DUOC",
                 "ly_do": "chua he nao duoc dang ky - xem `b demo dang-ky`"}]
    # MT5 khong ket noi duoc toi may chu giao dich qua Cloudflare WARP. Cung
    # rang buoc voi `chay_tester_kho.chay`; thieu no thi luot chay chet voi mot
    # loi khong noi gi ve WARP.
    from nhan import ngan_sach as NS
    with NS.giu_warp(False, "chay_that"):
        return _trong_warp(mt5_moi=_mt5(), that=that,
                           cho_tien_that=cho_tien_that, chi_he=chi_he, d=d)


def _trong_warp(mt5_moi, that: bool, cho_tien_that: bool, chi_he: str,
                d: dict) -> list:
    from nhan import han_muc as HM
    mt5 = mt5_moi
    try:
        tk = mt5.account_info()
        if tk is None:
            raise ChuaDoDuoc("khong doc duoc tai khoan")
        loai = int(tk.trade_mode)
        ra = []
        for he, c in d.items():
            if chi_he and he != chi_he:
                continue
            ban = {"he": he, "ma": c["ma"], "khung": c["khung"],
                   "tai_khoan": int(tk.login), "loai_tk": loai}
            if not c.get("bat"):
                ban.update(trang_thai="TAT", ly_do="he chua duoc bat")
                ra.append(ban); ghi_nhat_ky(ban); continue
            # CHOT 2: hai chia khoa cho tien that, o hai cho khac nhau.
            #
            # Chan o day chan GUI LENH, KHONG chan TINH TOAN. Ban dau toi chan
            # ca hai va no lam mat chinh cai can nhat: khong con biet duong tin
            # hieu co chay khong. Mot chot an toan chan luon ca phep DO la mot
            # chot an toan lam mu.
            khoa_du = (loai != TK_TIEN_THAT) or (c.get("cho_phep_tien_that")
                                                 and cho_tien_that)
            spec = spec_cua(c["co_che"])
            if spec is None:
                ban.update(trang_thai="CHUA_DO_DUOC",
                           ly_do="khong thay co che '%s' trong kho" % c["co_che"])
                ra.append(ban); ghi_nhat_ky(ban); continue
            try:
                df = _bar(mt5, c["ma"], c["khung"])
            except ChuaDoDuoc as e:
                ban.update(trang_thai="CHUA_DO_DUOC", ly_do=str(e))
                ra.append(ban); ghi_nhat_ky(ban); continue

            muc_tieu = tin_hieu(spec, df)
            dang_co = _vi_the(mt5, c["ma"], c["magic"])
            ban.update(bar_cuoi=str(df.index[-1]), muc_tieu=muc_tieu,
                       dang_co=dang_co)

            # CHOT 3: phanh. Chi chan MO THEM; DONG thi luon duoc phep.
            duoc, ly_do = HM.duoc_vao_lenh(he)
            can_mo = (muc_tieu > 0 and dang_co <= 0) or (muc_tieu < 0 and dang_co >= 0)
            can_dong = (muc_tieu == 0 and dang_co != 0) or (
                muc_tieu * dang_co < 0)

            if not can_mo and not can_dong:
                ban.update(trang_thai="GIU", ly_do="vi the da khop tin hieu")
                ra.append(ban); ghi_nhat_ky(ban); continue
            if can_mo and not duoc:
                ban.update(trang_thai="PHANH", ly_do=ly_do)
                ra.append(ban); ghi_nhat_ky(ban); continue
            if that and not khoa_du:
                ban.update(trang_thai="CHAN",
                           ly_do="tai khoan TIEN THAT ma thieu chia khoa "
                                 "(`cho_phep_tien_that` trong dang ky + "
                                 "`--tien-that`)",
                           viec_le_ra="dong+mo" if can_dong and can_mo else
                                      ("dong" if can_dong else "mo"))
                ra.append(ban); ghi_nhat_ky(ban); continue
            if not that:
                ban.update(trang_thai="DIEN_TAP",
                           viec="dong+mo" if can_dong and can_mo else
                                ("dong" if can_dong else "mo"))
                ra.append(ban); ghi_nhat_ky(ban); continue

            viec = {}
            if can_dong or (can_mo and dang_co):
                viec["dong"] = _dong_het(mt5, c["ma"], c["magic"])
            if can_mo:
                viec["mo"] = _mo(mt5, c["ma"], c["magic"], c["lot"],
                                 muc_tieu > 0)
            ban.update(trang_thai="DA_LAM", viec=viec)
            ra.append(ban); ghi_nhat_ky(ban)
        return ra
    finally:
        mt5.shutdown()


def _cli_suy_giam(argv: list) -> int:
    """He DANG CHAY co con giong cai da kiem dinh khong.

    `nhan/suy_giam.py` co tu truoc va nam MO COI - vi truoc 15/09 khong he nao
    CHAY THAT ca, nen khong co gi de so. Nay `chay_that` da co, no co viec.

    Moc backtest lay tu bang tester da luu (`reports/TESTER_KHO_*.json`), khong
    uoc luong: `suy_giam.do` noi ro *"truyen sai o day thi moi ket luan sau deu
    sai, nen ham khong tu doan chung"*.
    """
    import math
    from nhan import suy_giam as SG
    d = danh_sach()
    if not d:
        print("chua he nao duoc dang ky - xem `b demo`")
        return 0
    print("%-22s %-14s %s" % ("he", "trang thai", "mo ta"))
    for he, c in d.items():
        moc = _moc_backtest(c)
        if moc is None:
            print("%-22s %-14s %s" % (he[:22], "CHUA_DO_DUOC",
                                      "khong co bang tester cho %s/%s de lay moc"
                                      % (c["ma"], c["khung"])))
            continue
        tb, sd = moc
        k = SG.do(he, tb, sd)
        print("%-22s %-14s %s" % (he[:22], k["trang_thai"], k["mo_ta"][:96]))
    return 0


def _moc_backtest(c: dict):
    """(trung binh, do lech) MOI LENH tu bang tester da luu. None = chua co."""
    import math
    f = LAB / "reports" / ("TESTER_KHO_%s_%s.json" % (c["ma"], c["khung"]))
    if not f.exists():
        return None
    try:
        r = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    d = next((x for x in r.get("ket") or [] if x.get("ten") == c["co_che"]), None)
    if not d or not d.get("lenh"):
        return None
    n = int(d["lenh"])
    tb = float(d.get("ky_vong") or (float(d["lai"]) / max(n, 1)))
    # Do lech MOI LENH suy tu Sharpe cua tester: sharpe = tb / sd * sqrt(n).
    sh = float(d.get("sharpe") or 0.0)
    sd = abs(tb) * math.sqrt(n) / abs(sh) if sh else abs(tb) * 3.0
    return tb, (sd if sd > 0 else abs(tb) * 3.0)


def _cli(argv: list) -> int:
    from nhan import khoa_tester as KT
    lenh = argv[0] if argv else "xem"
    if lenh == "dang-ky":
        if len(argv) < 6:
            print("b demo dang-ky <he> <ma> <khung> <co_che> <lot> [magic]")
            return 2
        he, ma, khung, cc, lot = argv[1:6]
        magic = int(argv[6]) if len(argv) > 6 else int(time.time()) % 2000000000
        print(json.dumps(dang_ky(he, ma, khung, cc, float(lot), magic),
                         ensure_ascii=False, indent=1))
        print("\nDA DANG KY nhung CHUA BAT. Bat bang: b demo bat %s" % he)
        return 0
    if lenh in ("bat", "tat"):
        d = danh_sach()
        if len(argv) < 2 or argv[1] not in d:
            print("khong thay he. Co: %s" % ", ".join(d) or "(chua co he nao)")
            return 2
        d[argv[1]]["bat"] = (lenh == "bat")
        DANG_KY.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                           encoding="utf-8")
        print("%s: %s" % (argv[1], "BAT" if lenh == "bat" else "TAT"))
        return 0
    if lenh == "suy-giam":
        return _cli_suy_giam(argv[1:])
    if lenh == "nhip":
        that = "--that" in argv
        with KT.giu("chay_that.nhip"):
            for b in mot_nhip(that=that, cho_tien_that="--tien-that" in argv):
                print("%-22s %-12s %s" % (b.get("he", "?"), b["trang_thai"],
                                          b.get("ly_do", b.get("viec", ""))))
        return 0
    d = danh_sach()
    if not d:
        print("chua he nao duoc dang ky.\n  b demo dang-ky <he> <ma> <khung> "
              "<co_che> <lot> [magic]")
        return 0
    print("%-22s %-13s %-4s %-6s %-5s %s" % ("he", "ma", "khung", "lot", "bat", "co che"))
    for he, c in d.items():
        print("%-22s %-13s %-4s %-6g %-5s %s"
              % (he[:22], c["ma"], c["khung"], c["lot"],
                 "CO" if c.get("bat") else "-", str(c["co_che"])[:40]))
    print("\nnhat ky: %s" % NHAT_KY)
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
