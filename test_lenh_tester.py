# -*- coding: utf-8 -*-
"""nhan/lenh_tester.py - bo doc bao cao tester MT5 (bang Deals / Orders) + ghep deal vao/ra thanh vi the.

CLOUD KHONG CO BAO CAO THAT (tep that nam o may nha; khong vao git). Nen bai test dung BAO CAO GIA dung bo cuc MT5 da biet
(UTF-16, nghin tach bang khoang trang, bang Orders co "khop / tong", dong balance, colspan, ban tieng Viet) kem DAP AN BIET TRUOC:
  * `luoi.chay(ghi_lenh=True)` sinh ra lich su lenh (dap an), bai test dung deal tu do roi bat bo doc dung lai TUNG LENH - khong
    chep con so tu dau ra cua chinh no;
  * ky nang tay: vi the vang, dong tung phan, lenh trung gia, dao chieu, ma vi the, FIFO du phong;
  * bay: so doc sai (dau phay / nghin) lat nguoc bang kiem so du; tu la phai BAO LOI chu khong doan.
Dieu khong kiem duoc o day: dinh dang THAT cua tep may nha. Khi co mau that (`reports/fixture/tester_*`) them test tren mau do.
"""
from __future__ import annotations

import collections
import gzip
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nhan import boc_lich_su as BL
from nhan import lenh_tester as LT
from nhan import luoi as L

HOP_FX = 100000.0
HOP_VANG = 100.0


# =============================================================== bao cao gia (dung bo cuc MT5)
def _so_mt5(x, d: int = 2, nghin: str = " ", thap_phan: str = ".") -> str:
    """MT5: tach nghin bang khoang trang cung (nbsp), '-' truoc so, rong khi khong co gia tri."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    s = "{:,.{d}f}".format(abs(float(x)), d=d)
    s = s.replace(",", "\x00").replace(".", thap_phan).replace("\x00", nghin)
    return ("-" if x < 0 else "") + s


def _gio(t) -> str:
    return pd.Timestamp(t).strftime("%Y.%m.%d %H:%M:%S")


_NHAN = {
    "en": dict(deals=["Time", "Deal", "Symbol", "Type", "Direction", "Volume", "Price", "Order", "Commission", "Swap", "Profit",
                      "Balance", "Comment"],
               orders=["Open Time", "Order", "Symbol", "Type", "Volume", "Price", "S / L", "T / P", "Time", "State", "Comment"],
               mua="buy", ban="sell", vao="in", ra="out", vao_ra="in/out", so_du="balance", khop="filled", vi_the="Position",
               gh="limit", dg="stop"),
    "vi": dict(deals=["Thời gian", "Giao dịch", "Mã", "Loại", "Hướng", "Khối lượng", "Giá", "Lệnh", "Hoa hồng", "Swap",
                      "Lợi nhuận", "Số dư", "Bình luận"],
               orders=["Thời gian mở", "Lệnh", "Mã", "Loại", "Khối lượng", "Giá", "S / L", "T / P", "Thời gian", "Trạng thái",
                       "Bình luận"],
               mua="mua", ban="bán", vao="vào", ra="ra", vao_ra="vào/ra", so_du="số dư", khop="đã khớp", vi_the="Vị thế",
               gh="giới hạn", dg="dừng"),
}


def dung_giao_dich(vi_the: list[dict], von: float = 10000.0, hop_dong: float = HOP_FX, digits: int = 5, bd: str = "2018.01.01 00:00:00",
                   hoa_hong_lot: float = 0.0) -> tuple[list[dict], list[dict]]:
    """Danh sach VI THE (dap an) -> (deals, orders) dang list dict nhu bao cao MT5. Dap an duoc ghi nguoc vao tung vi the:
    `deal_vao`, `order_vao`, `deal_ra` (list), `order_ra` (list).

    vi_the[i]: ma, chieu (+1 mua / -1 ban), lot, gia_mo, mo (gio khop), cm_vao="", kieu="" ('' = thi truong; 'limit' / 'stop' = cho),
               dat (gio dat lenh cho), sl=0, tp=0, dong=[(gio, lot, gia, cm_ra)] (nhieu phan tu = dong tung phan)."""
    ev = []
    seq = 0
    for i, p in enumerate(vi_the):
        ev.append((pd.Timestamp(p["mo"]), seq, "vao", i, 0))
        seq += 1
        for j, _ in enumerate(p.get("dong", [])):
            ev.append((pd.Timestamp(p["dong"][j][0]), seq, "ra", i, j))
            seq += 1
    ev.sort(key=lambda e: (e[0], e[1]))
    deals = [dict(gio=pd.Timestamp(bd), deal=1, ma="", loai="balance", huong="", lot=None, gia=None, order=None, hoa_hong=None,
                  swap=None, loi=von, so_du=von, cm="", vi_the="")]
    orders = []
    so_du, deal_id, order_id = von, 1, 0
    for t, _, k, i, j in ev:
        p = vi_the[i]
        ma = p["ma"]
        if k == "vao":
            deal_id += 1
            order_id += 1
            p["deal_vao"], p["order_vao"] = deal_id, order_id
            p["deal_ra"], p["order_ra"] = [], []
            hh = -hoa_hong_lot * p["lot"] if hoa_hong_lot else 0.0
            so_du += hh
            deals.append(dict(gio=t, deal=deal_id, ma=ma, loai="mua" if p["chieu"] > 0 else "ban", huong="vao", lot=p["lot"],
                              gia=p["gia_mo"], order=order_id, hoa_hong=hh, swap=0.0, loi=0.0, so_du=so_du, cm=p.get("cm_vao", ""),
                              vi_the=str(p["order_vao"])))
            kieu = p.get("kieu", "")
            orders.append(dict(gio_dat=pd.Timestamp(p.get("dat", p["mo"])), order=order_id, ma=ma,
                               loai=("mua" if p["chieu"] > 0 else "ban") + ((" " + kieu) if kieu else ""), lot=p["lot"],
                               gia=p["gia_mo"], sl=p.get("sl", 0.0), tp=p.get("tp", 0.0), gio=t, trang_thai="khop",
                               cm=p.get("cm_vao", "")))
        else:
            gio_ra, lot, gia, cm = p["dong"][j]
            deal_id += 1
            order_id += 1
            p["deal_ra"].append(deal_id)
            p["order_ra"].append(order_id)
            loi = round(p["chieu"] * (gia - p["gia_mo"]) * lot * hop_dong, 2)
            hh = -hoa_hong_lot * lot if hoa_hong_lot else 0.0
            so_du = round(so_du + loi + hh, 2)
            deals.append(dict(gio=t, deal=deal_id, ma=ma, loai="ban" if p["chieu"] > 0 else "mua", huong="ra", lot=lot, gia=gia,
                              order=order_id, hoa_hong=hh, swap=0.0, loi=loi, so_du=so_du, cm=cm, vi_the=str(p["order_vao"])))
            orders.append(dict(gio_dat=t, order=order_id, ma=ma, loai="ban" if p["chieu"] > 0 else "mua", lot=lot, gia=gia,
                               sl=0.0, tp=0.0, gio=t, trang_thai="khop", cm=cm))
    return deals, orders


def html_bao_cao(deals: list[dict], orders: list[dict], inputs: dict | None = None, ngon_ngu: str = "en", digits: int = 5,
                 colspan: bool = True, nghin: str = " ", thap_phan: str = ".", cot_vi_the: bool = False,
                 ten_ea: str = "Mau EA") -> str:
    """(deals, orders) -> HTML nhu bao cao tester MT5 (cau truc, khong phai tung dau cach)."""
    n = _NHAN[ngon_ngu]
    d = digits

    def num(x, dd=2):
        return _so_mt5(x, dd, nghin, thap_phan)

    def td(x, cs=0):
        return "<td%s>%s</td>" % (' colspan="%d"' % cs if cs and colspan else "", x)

    ra = ["<html><head><meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-16\"><title>Strategy Tester Report</title>",
          "</head><body><div align=\"center\"><div style=\"font: 20pt Tahoma\"><b>Strategy Tester Report</b></div>",
          "<div style=\"font: 16pt Tahoma\"><b>%s</b></div>" % ten_ea,
          "<table width=\"820\" cellspacing=\"1\" cellpadding=\"3\" border=\"0\">",
          "<tr align=\"left\"><th>Expert:</th><td colspan=\"3\"><b>%s</b></td></tr>" % ten_ea,
          "<tr align=\"left\"><th>Symbol:</th><td colspan=\"3\"><b>AUDCAD</b></td></tr>"]
    for i, (k, v) in enumerate((inputs or {}).items()):
        ra.append("<tr align=\"left\"><th>%s</th><td colspan=\"3\"><b>%s=%s</b></td></tr>" % ("Inputs:" if i == 0 else "", k, v))
    ra.append("</table>")
    # ---- Orders
    ra.append("<div align=\"center\"><b>Orders</b></div><table width=\"1000\" cellspacing=\"1\" cellpadding=\"3\" border=\"0\">")
    to = n["orders"]
    ra.append("<tr align=\"center\" bgcolor=\"#E5F0FC\">" + "".join(
        td("<b>%s</b>" % h, 2 if h in (to[4], to[10]) else 0) for h in to) + "</tr>")
    for o in orders:
        loai = o["loai"].replace("mua", n["mua"]).replace("ban", n["ban"]).replace("limit", n["gh"]).replace("stop", n["dg"])
        ra.append("<tr bgcolor=\"#FFFFFF\" align=\"right\">" + td(_gio(o["gio_dat"])) + td(o["order"]) + td(o["ma"]) + td(loai) +
                  td("%s / %s" % (num(o["lot"]), num(o["lot"])), 2) + td(num(o["gia"], d)) + td(num(o["sl"], d)) +
                  td(num(o["tp"], d)) + td(_gio(o["gio"])) + td(n["khop"]) + td(o["cm"], 2) + "</tr>")
    ra.append("</table>")
    # ---- Deals
    ra.append("<div align=\"center\"><b>Deals</b></div><table width=\"1000\" cellspacing=\"1\" cellpadding=\"3\" border=\"0\">")
    td_ = list(n["deals"])
    if cot_vi_the:
        td_.insert(12, n["vi_the"])
    ra.append("<tr align=\"center\" bgcolor=\"#E5F0FC\">" + "".join(td("<b>%s</b>" % h) for h in td_) + "</tr>")
    for x in deals:
        loai = {"mua": n["mua"], "ban": n["ban"], "balance": n["so_du"]}.get(x["loai"], x["loai"])
        huong = {"vao": n["vao"], "ra": n["ra"], "vao_ra": n["vao_ra"], "": ""}[x["huong"]]
        cells = [td(_gio(x["gio"])), td(x["deal"]), td(x["ma"]), td(loai), td(huong), td(num(x["lot"])), td(num(x["gia"], d)),
                 td("" if x["order"] is None else x["order"]), td(num(x["hoa_hong"])), td(num(x["swap"])), td(num(x["loi"])),
                 td(num(x["so_du"]))]
        if cot_vi_the:
            cells.append(td(x.get("vi_the", "")))
        cells.append(td(x["cm"]))
        ra.append("<tr bgcolor=\"#F7F7F7\" align=\"right\">" + "".join(cells) + "</tr>")
    ra.append("</table></div></body></html>")
    return "\n".join(ra)


def ghi_htm(duong: Path, van: str, ma_hoa: str = "utf-16") -> Path:
    """MT5 ghi bao cao UTF-16 LE co BOM."""
    duong.write_bytes(van.encode(ma_hoa))
    return duong


def csv_deals(deals: list[dict], duong: Path, digits: int = 5, sep: str = ",") -> Path:
    """Deal -> CSV voi COT GOC cua bao cao (cach may nha luu mau): time, deal, symbol, type, direction, volume, price, order,
    commission, swap, profit, balance, comment."""
    cot = ["time", "deal", "symbol", "type", "direction", "volume", "price", "order", "commission", "swap", "profit", "balance",
           "comment"]
    ten = {"mua": "buy", "ban": "sell", "balance": "balance"}
    hang = []
    for x in deals:
        hang.append([_gio(x["gio"]), x["deal"], x["ma"], ten.get(x["loai"], x["loai"]), {"vao": "in", "ra": "out", "": ""}[x["huong"]],
                     _so_mt5(x["lot"], 2, "", "."), _so_mt5(x["gia"], digits, "", "."),
                     "" if x["order"] is None else x["order"], _so_mt5(x["hoa_hong"], 2, "", "."), _so_mt5(x["swap"], 2, "", "."),
                     _so_mt5(x["loi"], 2, "", "."), _so_mt5(x["so_du"], 2, "", "."), x["cm"]])
    df = pd.DataFrame(hang, columns=cot)
    if str(duong).endswith(".gz"):
        with gzip.open(duong, "wt", encoding="utf-8", newline="") as f:
            df.to_csv(f, index=False, sep=sep)
    else:
        df.to_csv(duong, index=False, sep=sep, encoding="utf-8")
    return duong


def csv_orders(orders: list[dict], duong: Path, digits: int = 5) -> Path:
    cot = ["Open Time", "Order", "Symbol", "Type", "Volume", "Price", "S / L", "T / P", "Time", "State", "Comment"]
    ten = {"mua": "buy", "ban": "sell"}
    hang = []
    for o in orders:
        loai = o["loai"].replace("mua", ten["mua"]).replace("ban", ten["ban"])
        hang.append([_gio(o["gio_dat"]), o["order"], o["ma"], loai, "%s / %s" % (_so_mt5(o["lot"], 2, "", "."), _so_mt5(o["lot"], 2, "", ".")),
                     _so_mt5(o["gia"], digits, "", "."), _so_mt5(o["sl"], digits, "", "."), _so_mt5(o["tp"], digits, "", "."),
                     _gio(o["gio"]), "filled", o["cm"]])
    pd.DataFrame(hang, columns=cot).to_csv(duong, index=False)
    return duong


# =============================================================== dap an tu engine luoi
def bars_that(n: int = 1500, seed: int = 1, spread_pts: int = 20) -> pd.DataFrame:
    """Bar M15 gia lap quanh 0,90 (cap FX), bien do ~7 pip: du de luoi mo nhieu tang va dong nhieu chuoi."""
    r = np.random.RandomState(seed)
    o, h, l, c = [], [], [], []
    p = 90000
    for _ in range(n):
        o_ = p
        c_ = o_ + int(round(r.normal(-0.01 * (p - 90000), 45)))
        hi = max(o_, c_) + int(abs(r.normal(0, 25)))
        lo = min(o_, c_) - int(abs(r.normal(0, 25)))
        if hi - lo > 250:
            ex = (hi - lo) - 250
            hi = max(hi - (ex // 2 + ex % 2), max(o_, c_))
            lo = min(lo + ex // 2, min(o_, c_))
        o.append(o_ * 1e-5), h.append(hi * 1e-5), l.append(lo * 1e-5), c.append(c_ * 1e-5)
        p = c_
    return pd.DataFrame(dict(open=o, high=h, low=l, close=c, spread=spread_pts),
                        index=pd.date_range("2024-01-01", periods=n, freq="15min"))


def vi_the_tu_engine(ts: L.ThamSo, df: pd.DataFrame, giay_le: bool = True, xao: bool = True, seed: int = 11) -> list[dict]:
    """Chay engine, doi `lenh` thanh danh sach vi the dap an (gia lam tron 5 chu so nhu MT5).

    Gio: lenh MO trong cung mot bar cach nhau 1 giay theo thu tu engine; lenh DONG cung bar duoc xep SAU het cac lenh mo cua bar do
    va theo thu tu XAO TRON (co hat giong). Bao cao that dong theo thu tu cua EA - khong ai biet truoc - nen thu tu dong KHONG duoc
    trung voi thu tu mo (neu khong FIFO tu no la dap an dung va phep thu khong chung minh duoc gi). Gioi han 450 su kien moi loai / bar."""
    r = L.chay(df, ts, 10000.0, ghi_lenh=True)
    lenh = list(r.lenh.itertuples(index=False))
    rng = np.random.RandomState(seed)
    n_mo: dict = {}
    t_mo = []
    for x in lenh:
        t = pd.Timestamp(x.mo)
        k = n_mo.get(t, 0)
        n_mo[t] = k + 1
        t_mo.append(t + pd.Timedelta(seconds=min(k, 449)) if giay_le else t)
    theo_bar: dict = {}
    for i, x in enumerate(lenh):
        if pd.notna(x.dong):
            theo_bar.setdefault(pd.Timestamp(x.dong), []).append(i)
    t_dong: dict = {}
    for t, idx in theo_bar.items():
        if xao:
            rng.shuffle(idx)
        goc = min(n_mo.get(t, 0), 450) if giay_le else 0
        for k, i in enumerate(idx):
            t_dong[i] = t + pd.Timedelta(seconds=goc + min(k, 449)) if giay_le else t
    ra = []
    for i, x in enumerate(lenh):
        p = dict(ma="AUDCAD", chieu=int(x.chieu), lot=round(float(x.lot), 2), gia_mo=round(float(x.gia_mo), 5), mo=t_mo[i],
                 cm_vao="t%d" % int(x.tang), dong=[])
        if i in t_dong:
            t_ra = max(t_dong[i], p["mo"] + pd.Timedelta(seconds=1))
            p["dong"] = [(t_ra, p["lot"], round(float(x.gia_dong), 5), "ea")]
        ra.append(p)
    return ra


CAU_HINH = {
    "luoi_deu": L.ThamSo(buoc=15, tp=6, tran_tang=5, che_do="hai_chieu", lot=0.01),
    "tn5": L.ThamSo(buoc=21, tp=9, tran_tang=9, che_do="hai_chieu", lot=0.04, kieu_lot="cong", he_so_lot=0.25, he_so_buoc=1.2,
                    tia_lenh=True, bien_cap=5),
    "chot_tien": L.ThamSo(buoc=16, tp=7, tran_tang=6, che_do="hai_chieu", lot=0.04, kieu_lot="cong", he_so_lot=0.25, chot_tien=3),
    "nhan_lot": L.ThamSo(buoc=18, tp=7, tran_tang=5, che_do="hai_chieu", lot=0.01, kieu_lot="nhan", he_so_lot=2.0, he_so_buoc=1.5),
}


def doc_lai(vi_the: list[dict], tmp_path: Path, **kw) -> tuple[pd.DataFrame, list[dict], list[dict]]:
    deals, orders = dung_giao_dich(vi_the, hop_dong=kw.pop("hop_dong", HOP_FX))
    f = ghi_htm(tmp_path / "bc.htm", html_bao_cao(deals, orders, **kw))
    return LT.vi_the_tu_tep(f), deals, orders


def so_dap_an(v: pd.DataFrame, vi_the: list[dict]) -> dict:
    """So tung lenh dap an voi bang vi the doc lai. `dung` = dung deal vao + deal ra; `tuong_duong` = deal ra dong dung mot lenh
    CUNG chieu / gia / lot (hai lenh giong het nhau khong the phan biet tu bao cao: chon nham giua chung khong sai kinh te)."""
    tim = {(int(r.deal_vao), int(r.deal_ra)) for r in v.itertuples(index=False)}
    can = {(p["deal_vao"], d) for p in vi_the for d in (p["deal_ra"] or [0])}
    cc = collections.Counter((d, p["chieu"], round(p["gia_mo"], 5), p["lot"]) for p in vi_the for d in p["deal_ra"])
    tc = collections.Counter((int(r.deal_ra), int(r.chieu), round(float(r.gia_mo), 5), round(float(r.lot), 2))
                             for r in v.itertuples(index=False) if r.deal_ra > 0)
    return {"can": len(can), "dung": len(can & tim), "thua": len(tim - can),
            "tuong_duong": sum((cc & tc).values()), "can_dong": sum(cc.values())}


# =============================================================== 1. doc dung (khong ghep)
def test_doc_html_utf16_ba_bang_va_inputs(tmp_path):
    vt = [dict(ma="AUDCAD", chieu=1, lot=0.01, gia_mo=0.90000, mo="2018.01.02 01:00:00", sl=0.89, tp=0.91, cm_vao="t1",
               dong=[("2018.01.02 03:00:00", 0.01, 0.90500, "[tp 0.90500]")])]
    deals, orders = dung_giao_dich(vt)
    f = ghi_htm(tmp_path / "a.htm", html_bao_cao(deals, orders, inputs={"InpTP": "200", "InpMultiplier": "1.18"}))
    r = LT.doc_tep(f)
    d = r["deals"]
    assert list(d["loai"]) == ["so_du", "mua", "ban"] and list(d["huong"]) == ["", "vao", "ra"]
    assert d["loi"].iloc[-1] == pytest.approx(5.0) and d["so_du"].iloc[-1] == pytest.approx(10005.0)
    assert d["ghi_chu"].iloc[-1] == "[tp 0.90500]"
    o = r["orders"]
    assert len(o) == 2 and o["lot"].iloc[0] == pytest.approx(0.01) and o["lot_khop"].iloc[0] == pytest.approx(0.01)
    assert o["sl"].iloc[0] == pytest.approx(0.89) and np.isnan(o["sl"].iloc[1])        # 0.00 = khong dat
    assert r["inputs"] == {"InpTP": "200", "InpMultiplier": "1.18"}
    assert LT.kiem_so_du(d)["sai"] == 0


def test_doc_html_colspan_va_khong_colspan_cho_cung_ket_qua(tmp_path):
    vt = [dict(ma="AUDCAD", chieu=-1, lot=0.02, gia_mo=0.91000, mo="2018.01.02 01:00:00", cm_vao="x y",
               dong=[("2018.01.02 03:00:00", 0.02, 0.90900, "")])]
    deals, orders = dung_giao_dich(vt)
    a = LT.doc_html(html_bao_cao(deals, orders, colspan=True))
    b = LT.doc_html(html_bao_cao(deals, orders, colspan=False))
    pd.testing.assert_frame_equal(a["deals"], b["deals"])
    pd.testing.assert_frame_equal(a["orders"], b["orders"])
    assert a["orders"]["ghi_chu"].iloc[0] == "x y" and a["orders"]["trang_thai"].iloc[0] == "filled"


def test_doc_html_tieng_viet_va_phay_thap_phan(tmp_path):
    vt = [dict(ma="XAUUSD", chieu=1, lot=0.05, gia_mo=1306.10, mo="2018.01.02 01:00:00", kieu="limit",
               dat="2018.01.02 00:30:00", dong=[("2018.01.02 03:00:00", 0.05, 1309.00, "[tp 1309.00]")])]
    deals, orders = dung_giao_dich(vt, hop_dong=HOP_VANG)
    for kw in (dict(ngon_ngu="vi"), dict(ngon_ngu="vi", thap_phan=",", nghin=" "), dict(ngon_ngu="en", nghin=" ")):
        r = LT.doc_html(html_bao_cao(deals, orders, digits=2, **kw))
        d, o = r["deals"], r["orders"]
        assert list(d["loai"]) == ["so_du", "mua", "ban"], kw
        assert list(d["huong"]) == ["", "vao", "ra"], kw
        assert d["gia"].iloc[1] == pytest.approx(1306.10) and d["gia"].iloc[2] == pytest.approx(1309.00), kw
        assert d["loi"].iloc[2] == pytest.approx(14.5) and d["so_du"].iloc[2] == pytest.approx(10014.5), kw
        assert o["kieu"].iloc[0] == "cho_limit" and o["chieu"].iloc[0] == 1, kw
        assert o["gio_dat"].iloc[0] == pd.Timestamp("2018-01-02 00:30:00") and o["gio"].iloc[0] == pd.Timestamp("2018-01-02 01:00:00")
        assert LT.kiem_so_du(d)["sai"] == 0, kw


def test_doc_html_cot_position_dung_thu_tu_that():
    vt = [dict(ma="AUDCAD", chieu=1, lot=0.01, gia_mo=0.90000, mo="2018.01.02 01:00:00",
               dong=[("2018.01.02 03:00:00", 0.01, 0.90050, "")])]
    deals, orders = dung_giao_dich(vt)
    r = LT.doc_html(html_bao_cao(deals, orders, cot_vi_the=True))
    assert list(r["deals"]["vi_the"]) == ["", "1", "1"]
    assert any("tieu de" in c for c in r["canh_bao"])


def test_doc_html_khong_co_deal_nem_loi_chi_ro():
    with pytest.raises(ValueError, match="khong thay dong DEAL"):
        LT.doc_html("<html><body><table><tr><td>Strategy Tester Report</td></tr></table></body></html>")


def test_loai_deal_la_phai_bao_loi_khong_doan():
    vt = [dict(ma="AUDCAD", chieu=1, lot=0.01, gia_mo=0.9, mo="2018.01.02 01:00:00", dong=[("2018.01.02 03:00:00", 0.01, 0.9005, "")])]
    deals, orders = dung_giao_dich(vt)
    van = html_bao_cao(deals, orders).replace("<td>buy</td>", "<td>kaufen</td>")
    with pytest.raises(ValueError, match="loai deal la"):
        LT.doc_html(van)
    with pytest.raises(ValueError, match="kaufen"):                              # thong bao phai neu DUNG tu la
        LT.doc_html(van)


def test_bang_loai_bo_sung_tu_la_cho_phep_doc(tmp_path):
    vt = [dict(ma="AUDCAD", chieu=1, lot=0.01, gia_mo=0.9, mo="2018.01.02 01:00:00", dong=[("2018.01.02 03:00:00", 0.01, 0.9005, "")])]
    deals, orders = dung_giao_dich(vt)
    van = html_bao_cao(deals, orders).replace("<td>buy</td>", "<td>kaufen</td>").replace("<td>sell</td>", "<td>verkaufen</td>")
    f = ghi_htm(tmp_path / "de.htm", van)
    r = LT.doc_tep(f, bang_loai={"kaufen": "mua", "verkaufen": "ban"})
    assert list(r["deals"]["loai"]) == ["so_du", "mua", "ban"]


def test_kiem_so_du_bat_so_doc_sai():
    vt = [dict(ma="AUDCAD", chieu=1, lot=0.01, gia_mo=0.90000, mo="2018.01.02 01:00:00",
               dong=[("2018.01.02 03:00:00", 0.01, 0.90050, ""), ])]
    deals, orders = dung_giao_dich(vt)
    d = LT.doc_html(html_bao_cao(deals, orders))["deals"]
    assert LT.kiem_so_du(d)["sai"] == 0
    d.loc[d.index[-1], "loi"] = 50.0                       # doc nham 5.00 thanh 50.00 (dau thap phan)
    k = LT.kiem_so_du(d)
    assert k["sai"] == 1 and k["dong_sai_dau"] == [3]


def test_so_dinh_dang_so():
    assert LT._so("10 000.00") == 10000.0 and LT._so("1 306.10") == 1306.10 and LT._so("1 306.10") == 1306.10
    assert LT._so("-1 234,50", ",") == -1234.5 and LT._so("0,01", ",") == 0.01 and LT._so("−1.5") == -1.5
    assert np.isnan(LT._so("")) and np.isnan(LT._so("-"))


def test_ly_do_ra():
    assert LT.ly_do_ra("[sl 1308.72]") == "sl" and LT.ly_do_ra("[tp 1310.90]") == "tp" and LT.ly_do_ra("[TP 0.9]") == "tp"
    assert LT.ly_do_ra("so: 20.00% / 100.00") == "stopout" and LT.ly_do_ra("stop out") == "stopout"
    assert LT.ly_do_ra("") == "ea" and LT.ly_do_ra("Close All") == "ea" and LT.ly_do_ra("tp3") == "ea"


# =============================================================== 2. ghep: dap an tu engine
@pytest.mark.parametrize("ten", sorted(CAU_HINH))
def test_dap_an_engine_ghep_dung_tung_lenh(ten, tmp_path):
    vt = vi_the_tu_engine(CAU_HINH[ten], bars_that(1500, seed=3))
    dong = sum(1 for p in vt if p["dong"])
    assert dong >= 40, "cau hinh phai dong du nhieu lenh de phep thu co nghia"
    v, deals, orders = doc_lai(vt, tmp_path)
    kq = so_dap_an(v, vt)
    assert kq["thua"] == 0, kq
    assert kq["dung"] / kq["can"] >= 0.995, (ten, kq, v.attrs["ghep"])
    assert v.attrs["mo_coi"] == 0 and v.attrs["kiem_so_du"]["sai"] == 0
    # hop dong uoc luong dung (cap tien bao gia = tien tai khoan -> 100000)
    assert v.attrs["hop_dong"]["AUDCAD"] == pytest.approx(HOP_FX, rel=1e-3)
    # gio / lot / gia doc THANG: khop dap an tung lenh
    vao = {p["deal_vao"]: p for p in vt}
    for r in v[v["deal_ra"] > 0].itertuples(index=False):
        p = vao[int(r.deal_vao)]
        assert r.gia_mo == pytest.approx(p["gia_mo"]) and r.lot == pytest.approx(p["lot"]) and r.chieu == p["chieu"]
        assert r.mo == p["mo"] and r.dong == p["dong"][0][0] and r.gia_dong == pytest.approx(p["dong"][0][2])
    # lenh chua dong den het du lieu: khong co gia dong
    mo = v[v["cach_ghep"] == "chua_dong"]
    assert mo["gia_dong"].isna().all() and mo["dong"].isna().all() and len(mo) == sum(1 for p in vt if not p["dong"])


def test_cach_ghep_duoc_bao_cao_va_loi_chiem_phan_lon(tmp_path):
    vt = vi_the_tu_engine(CAU_HINH["tn5"], bars_that(1500, seed=5))
    v, *_ = doc_lai(vt, tmp_path)
    g = v.attrs["ghep"]
    assert g.get("fifo", 0) <= 0.02 * sum(g.values()), g
    assert g.get("loi", 0) + g.get("don", 0) >= 0.95 * sum(g.values()) - g.get("chua_dong", 0)


def test_comment_vao_ra_va_order_nguyen_ven(tmp_path):
    vt = vi_the_tu_engine(CAU_HINH["tn5"], bars_that(900, seed=2))
    v, deals, orders = doc_lai(vt, tmp_path)
    vao = {p["deal_vao"]: p for p in vt}
    d = v[v["deal_ra"] > 0].iloc[0]
    assert d["cm_vao"] == vao[int(d["deal_vao"])]["cm_vao"] and d["cm_ra"] == "ea" and d["ly_do_ra"] == "ea"
    assert v["order_vao"].gt(0).all() and v[v["deal_ra"] > 0]["order_ra"].gt(0).all()


# =============================================================== 3. ghep: tinh huong tay
def _vang(mo, gia, lot=0.01, chieu=1, dong=None, **kw):
    p = dict(ma="XAUUSD", chieu=chieu, lot=lot, gia_mo=gia, mo=mo, dong=dong or [])
    p.update(kw)
    return p


def _t(m):
    return pd.Timestamp("2018.01.02 01:00:00") + pd.Timedelta(minutes=m)


def test_phuong_trinh_loi_chon_dung_lenh_khi_dong_ca_ro(tmp_path):
    """Ba lenh mua o ba gia, dong cung gia 1309 theo thu tu NGUOC voi thu tu mo - FIFO se sai; phuong trinh loi phai dung."""
    gia = [1306.10, 1303.10, 1300.10]
    # dong NGUOC thu tu mo (lenh mo sau dong truoc): FIFO se ghep sai ca ba
    vt = [_vang(_t(i), g, lot=l, dong=[(_t(20 - i), l, 1309.00, "")]) for i, (g, l) in enumerate(zip(gia, (0.01, 0.01, 0.02)))]
    # them 3 chuoi don le truoc do de hop dong uoc luong duoc (>= 3 mau |loi| >= 2)
    dau = [_vang(_t(-100 + 10 * k), 1290.0, lot=0.1, dong=[(_t(-95 + 10 * k), 0.1, 1290.5 + k, "")]) for k in range(3)]
    v, *_ = doc_lai(dau + vt, tmp_path, hop_dong=HOP_VANG, digits=2)
    sau = v[v["mo"] >= _t(0)]
    assert v.attrs["hop_dong"]["XAUUSD"] == pytest.approx(100.0)
    assert set(sau["cach_ghep"]) <= {"loi", "don"}, list(sau["cach_ghep"])        # lenh cuoi cung con lai la 'don'
    assert (sau["cach_ghep"] == "loi").sum() >= 2
    pairs = {round(r.gia_mo, 2): round(r.loi, 2) for r in sau.itertuples(index=False)}
    assert pairs == {1306.10: 2.90, 1303.10: 5.90, 1300.10: 17.80}


def _deal_df(deals: list[dict]) -> pd.DataFrame:
    """Deal dang list dict (dap an) -> bang deal chuan, khong qua HTML."""
    return LT._hoan_thien_deal(pd.DataFrame([
        dict(gio=_gio(x["gio"]), deal=x["deal"], ma=x["ma"], loai_goc={"mua": "buy", "ban": "sell", "balance": "balance"}[x["loai"]],
             huong_goc={"vao": "in", "ra": "out", "": ""}[x["huong"]], lot=x["lot"], gia=x["gia"], order=x["order"] or 0,
             hoa_hong=x["hoa_hong"] or 0.0, swap=0.0, loi=x["loi"], so_du=x["so_du"], ghi_chu=x["cm"], vi_the="") for x in deals]))


def test_hop_dong_vang_uoc_luong_tu_mau_sach_va_khong_dung_mau_mo_ho():
    dau = [_vang(_t(10 * k), 1290.0, lot=0.1, dong=[(_t(10 * k + 5), 0.1, 1290.5 + k, "")]) for k in range(4)]
    deals, _ = dung_giao_dich(dau, hop_dong=HOP_VANG)
    r = LT.uoc_hop_dong(_deal_df(deals))
    assert r == {"XAUUSD": pytest.approx(100.0)}


def test_hop_dong_thieu_mau_thi_khong_uoc_va_ghep_van_chay(tmp_path):
    vt = [_vang(_t(0), 1306.1, dong=[(_t(5), 0.01, 1306.6, "")]), _vang(_t(10), 1306.1, dong=[(_t(15), 0.01, 1306.9, "")])]
    deals, orders = dung_giao_dich(vt, hop_dong=HOP_VANG)
    f = ghi_htm(tmp_path / "x.htm", html_bao_cao(deals, orders, digits=2))
    v = LT.vi_the_tu_tep(f)
    assert "XAUUSD" not in v.attrs["hop_dong"]
    assert len(v) == 2 and set(v["cach_ghep"]) == {"don"}


def test_dong_tung_phan_chia_loi_theo_lot(tmp_path):
    p = _vang(_t(0), 1300.00, lot=0.05, dong=[(_t(5), 0.02, 1301.00, "sniper1"), (_t(6), 0.03, 1302.00, "[tp 1302.00]")])
    deals, orders = dung_giao_dich([p], hop_dong=HOP_VANG)
    v = LT.vi_the_tu_tep(ghi_htm(tmp_path / "p.htm", html_bao_cao(deals, orders, digits=2)))
    assert len(v) == 2 and list(v["lot"]) == [0.02, 0.03] and set(v["lot_vao"]) == {0.05}
    assert list(v["deal_vao"].unique()) == [p["deal_vao"]]
    assert list(v["loi"]) == [pytest.approx(2.0), pytest.approx(6.0)]
    assert list(v["ly_do_ra"]) == ["ea", "tp"]
    g = LT.gop_theo_lenh(v)
    assert len(g) == 1 and g["lot"].iloc[0] == pytest.approx(0.05) and g["so_lan_dong"].iloc[0] == 2
    assert g["loi"].iloc[0] == pytest.approx(8.0) and g["gia_dong"].iloc[0] == pytest.approx((0.02 * 1301 + 0.03 * 1302) / 0.05)
    assert g["dong"].iloc[0] == _t(6) and g["ly_do_ra"].iloc[0] == "tp"


def test_hai_lenh_cung_gia_ghep_theo_thu_tu_mo(tmp_path):
    """Hai lenh mua cung gia, cung lot (+ mot lenh o gia khac khong dong): khong phan biet duoc -> dong theo thu tu mo, van la cach
    'loi' (phuong trinh chi ra dung gia 1300) chu khong phai fifo."""
    vt = [_vang(_t(0), 1300.00, dong=[(_t(10), 0.01, 1301.00, "")]), _vang(_t(1), 1300.00, dong=[(_t(11), 0.01, 1302.00, "")]),
          _vang(_t(2), 1295.00)]
    deals, orders = dung_giao_dich(vt, hop_dong=HOP_VANG)
    r = LT.doc_tep(ghi_htm(tmp_path / "s.htm", html_bao_cao(deals, orders, digits=2)))
    v = LT.ghep_vi_the(r["deals"], r["orders"], hop_dong=HOP_VANG)
    d = v[v["deal_ra"] > 0]
    assert len(d) == 2 and set(d["gia_mo"]) == {1300.0} and set(d["cach_ghep"]) == {"loi"}
    assert list(d["deal_vao"]) == [vt[0]["deal_vao"], vt[1]["deal_vao"]]           # thu tu mo
    mo = v[v["cach_ghep"] == "chua_dong"]
    assert len(mo) == 1 and mo["gia_mo"].iloc[0] == 1295.0


def test_khong_biet_hop_dong_nhung_moi_lenh_dang_mo_cung_gia_thi_la_cung_gia(tmp_path):
    """Khong co hop dong (khong uoc luong / hieu chuan duoc) nhung ca hai lenh dang mo cung gia: chon lenh nao cung ra cung loi."""
    vt = [_vang(_t(0), 1300.00, dong=[(_t(10), 0.01, 1301.00, "")]), _vang(_t(1), 1300.00, dong=[(_t(11), 0.01, 1302.00, "")])]
    deals, orders = dung_giao_dich(vt, hop_dong=HOP_VANG)
    v = LT.vi_the_tu_tep(ghi_htm(tmp_path / "cg.htm", html_bao_cao(deals, orders, digits=2)))
    assert v.attrs["hop_dong"] == {}
    assert list(v["cach_ghep"]) == ["cung_gia", "don"] and list(v["deal_vao"]) == [vt[0]["deal_vao"], vt[1]["deal_vao"]]


def test_fifo_du_phong_duoc_ghi_co_khi_khong_khop_phuong_trinh(tmp_path):
    """Hop dong sai (truyen 10 thay vi 100) -> khong lenh nao khop gia: moi phep ghep la 'fifo' va co ghi."""
    vt = [_vang(_t(0), 1300.00, dong=[(_t(10), 0.01, 1301.00, "")]), _vang(_t(1), 1290.00, dong=[(_t(11), 0.01, 1291.00, "")]),
          _vang(_t(2), 1280.00, dong=[(_t(12), 0.01, 1281.00, "")])]
    deals, orders = dung_giao_dich(vt, hop_dong=HOP_VANG)
    # ba lenh mo cung luc truoc khi dong, hop dong khong the uoc luong (khong mau sach) va bi ep sai
    f = ghi_htm(tmp_path / "f.htm", html_bao_cao(deals, orders, digits=2))
    r = LT.doc_tep(f)
    v = LT.ghep_vi_the(r["deals"], r["orders"], hop_dong=10.0)
    assert len(v) == 3 and set(v["cach_ghep"]) <= {"fifo", "don"}


def test_gia_nguyen_khong_lam_tick_bang_1():
    """Mau chi toan gia nguyen (1300.0, 1290.0, 1280.0) khong duoc suy ra tick = 1.0: dung sai se nuot lenh ke ben va phuong trinh
    loi (hop dong bi ep sai) se 'khop' nham lenh 1290 thay vi tra ve fifo co co."""
    vt = [_vang(_t(0), 1300.00, dong=[(_t(10), 0.01, 1301.00, "")]), _vang(_t(1), 1290.00, dong=[(_t(11), 0.01, 1291.00, "")]),
          _vang(_t(2), 1280.00, dong=[(_t(12), 0.01, 1281.00, "")])]
    deals, _ = dung_giao_dich(vt, hop_dong=HOP_VANG)
    d = _deal_df(deals)
    assert not d.attrs.get("digits")                              # khong co chuoi goc -> phai uoc luong tu so
    v = LT.ghep_vi_the(d, hop_dong=10.0)
    assert v.attrs["tick"]["XAUUSD"] <= 0.01 + 1e-12
    assert set(v["cach_ghep"]) <= {"fifo", "don"}, list(v["cach_ghep"])
    assert list(v["deal_vao"]) == [vt[0]["deal_vao"], vt[1]["deal_vao"], vt[2]["deal_vao"]]


def test_dao_chieu_in_out_tach_hai_phan(tmp_path):
    """Deal 'in/out' (netting): phan dau dong lenh mua dang mo, phan du mo lenh ban moi."""
    d = pd.DataFrame([
        dict(gio="2018.01.02 01:00:00", deal=1, ma="", loai_goc="balance", huong_goc="", lot=np.nan, gia=np.nan, order=0, hoa_hong=np.nan,
             swap=np.nan, loi=10000.0, so_du=10000.0, ghi_chu="", vi_the=""),
        dict(gio="2018.01.02 01:10:00", deal=2, ma="XAUUSD", loai_goc="buy", huong_goc="in", lot=0.02, gia=1300.0, order=2, hoa_hong=0.0,
             swap=0.0, loi=0.0, so_du=10000.0, ghi_chu="", vi_the=""),
        dict(gio="2018.01.02 01:20:00", deal=3, ma="XAUUSD", loai_goc="sell", huong_goc="in/out", lot=0.05, gia=1301.0, order=3,
             hoa_hong=0.0, swap=0.0, loi=2.0, so_du=10002.0, ghi_chu="", vi_the=""),
        dict(gio="2018.01.02 01:30:00", deal=4, ma="XAUUSD", loai_goc="buy", huong_goc="out", lot=0.03, gia=1300.0, order=4,
             hoa_hong=0.0, swap=0.0, loi=3.0, so_du=10005.0, ghi_chu="", vi_the="")])
    v = LT.ghep_vi_the(LT._hoan_thien_deal(d))
    mua = v[v["chieu"] == 1].iloc[0]
    ban = v[v["chieu"] == -1].iloc[0]
    assert mua["lot"] == pytest.approx(0.02) and mua["gia_dong"] == 1301.0 and mua["loi"] == pytest.approx(2.0)
    assert ban["lot"] == pytest.approx(0.03) and ban["gia_mo"] == 1301.0 and ban["gia_dong"] == 1300.0 and ban["lot_vao"] == pytest.approx(0.03)


def test_deal_ra_khong_co_lenh_mo_la_mo_coi(tmp_path):
    d = pd.DataFrame([
        dict(gio="2018.01.02 01:10:00", deal=2, ma="XAUUSD", loai_goc="sell", huong_goc="out", lot=0.02, gia=1300.0, order=2, hoa_hong=0.0,
             swap=0.0, loi=5.0, so_du=10005.0, ghi_chu="", vi_the="")])
    v = LT.ghep_vi_the(LT._hoan_thien_deal(d))
    assert v.empty and v.attrs["mo_coi"] == 1


def test_deal_thieu_huong_phai_bao_loi():
    d = pd.DataFrame([dict(gio="2018.01.02 01:10:00", deal=2, ma="XAUUSD", loai_goc="buy", huong_goc="", lot=0.02, gia=1300.0, order=2,
                           hoa_hong=0.0, swap=0.0, loi=0.0, so_du=10000.0, ghi_chu="", vi_the="")])
    with pytest.raises(ValueError, match="khong co huong"):
        LT.ghep_vi_the(LT._hoan_thien_deal(d))


def test_ma_vi_the_ghep_chinh_xac_khi_bao_cao_co_cot_position(tmp_path):
    vt = [_vang(_t(0), 1300.0, dong=[(_t(10), 0.01, 1301.0, "")]), _vang(_t(1), 1300.0, dong=[(_t(11), 0.01, 1302.0, "")])]
    # dao thu tu dong: lenh mo sau dong truoc -> chi ma vi the moi ghep dung
    vt[0]["dong"] = [(_t(12), 0.01, 1301.0, "")]
    deals, orders = dung_giao_dich(vt, hop_dong=HOP_VANG)
    f = ghi_htm(tmp_path / "pos.htm", html_bao_cao(deals, orders, digits=2, cot_vi_the=True))
    v = LT.vi_the_tu_tep(f)
    assert set(v["cach_ghep"]) == {"ma_vi_the"}
    assert {(int(r.deal_vao), int(r.deal_ra)) for r in v.itertuples(index=False)} == {
        (vt[0]["deal_vao"], vt[0]["deal_ra"][0]), (vt[1]["deal_vao"], vt[1]["deal_ra"][0])}


def test_phi_hoa_hong_vao_ra_chia_theo_lot(tmp_path):
    p = _vang(_t(0), 1300.0, lot=0.04, dong=[(_t(5), 0.01, 1301.0, ""), (_t(6), 0.03, 1301.0, "")])
    deals, orders = dung_giao_dich([p], hop_dong=HOP_VANG, hoa_hong_lot=5.0)
    v = LT.vi_the_tu_tep(ghi_htm(tmp_path / "h.htm", html_bao_cao(deals, orders, digits=2)))
    # vao: -5 * 0.04 = -0.20 chia theo lot (0,25 / 0,75); ra: -5 * lot_phan (-0,05 / -0,15)
    assert v["hoa_hong"].sum() == pytest.approx(-0.20 - 0.05 - 0.15)
    assert list(v["hoa_hong"]) == [pytest.approx(-0.05 - 0.05), pytest.approx(-0.15 - 0.15)]


def test_lenh_cho_stop_ghi_kieu_vao_va_gio_dat(tmp_path):
    p = _vang(_t(30), 1305.0, kieu="stop", dat=_t(0), sl=1290.0, tp=1310.0, dong=[(_t(60), 0.01, 1310.0, "[tp 1310.00]")])
    deals, orders = dung_giao_dich([p], hop_dong=HOP_VANG)
    v = LT.vi_the_tu_tep(ghi_htm(tmp_path / "st.htm", html_bao_cao(deals, orders, digits=2)))
    r = v.iloc[0]
    assert r["kieu_vao"] == "cho_stop" and r["gio_dat"] == _t(0) and r["mo"] == _t(30)
    assert r["sl"] == 1290.0 and r["tp"] == 1310.0 and r["ly_do_ra"] == "tp"


def test_nap_rut_tien_di_rieng_khong_thanh_lenh(tmp_path):
    p = _vang(_t(0), 1300.0, dong=[(_t(5), 0.01, 1301.0, "")])
    deals, orders = dung_giao_dich([p], hop_dong=HOP_VANG)
    deals.insert(2, dict(gio=_t(2), deal=99, ma="", loai="balance", huong="", lot=None, gia=None, order=None, hoa_hong=None, swap=None,
                         loi=-500.0, so_du=9500.0, cm="withdrawal", vi_the=""))
    # deal 99 chen giua: so du cac dong sau lech 500 -> kiem so du phai ve 'sai' o dong sau, nhung nap/rut phai duoc ghi nhan
    v = LT.vi_the_tu_tep(ghi_htm(tmp_path / "w.htm", html_bao_cao(deals, orders, digits=2)))
    assert len(v) == 1 and [x[1] for x in v.attrs["nap_rut"]] == [10000.0, -500.0]
    assert v.attrs["von_dau"] == 10000.0


# =============================================================== 4. CSV, mot cua, tich hop voi bo boc luoi
def test_csv_gz_va_html_cho_cung_bang_vi_the(tmp_path):
    vt = vi_the_tu_engine(CAU_HINH["tn5"], bars_that(600, seed=4))
    deals, orders = dung_giao_dich(vt)
    va = LT.vi_the_tu_tep(ghi_htm(tmp_path / "a.htm", html_bao_cao(deals, orders)))
    vb = LT.vi_the_tu_tep(csv_deals(deals, tmp_path / "a_deals.csv.gz"), orders_csv=csv_orders(orders, tmp_path / "a_orders.csv"))
    cot = ["mo", "dong", "chieu", "lot", "gia_mo", "gia_dong", "loi", "deal_vao", "deal_ra", "cach_ghep"]
    pd.testing.assert_frame_equal(va[cot], vb[cot], check_exact=False, rtol=1e-9)


def test_csv_chi_deal_khong_co_order_van_ghep(tmp_path):
    vt = vi_the_tu_engine(CAU_HINH["luoi_deu"], bars_that(500, seed=6))
    deals, _ = dung_giao_dich(vt)
    v = LT.vi_the_tu_tep(csv_deals(deals, tmp_path / "d.csv"))
    assert v["kieu_vao"].eq("").all() and v["sl"].isna().all()
    assert so_dap_an(v, vt)["thua"] == 0


def test_csv_thieu_cot_bao_loi_ro(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("time,deal,symbol\n2018.01.02 01:00:00,1,X\n", encoding="utf-8")
    with pytest.raises(ValueError, match="thieu cot"):
        LT.doc_deals_csv(p)


def test_dinh_dang_tep_la_bi_tu_choi(tmp_path):
    p = tmp_path / "x.pdf"
    p.write_bytes(b"%PDF")
    with pytest.raises(ValueError, match="dinh dang"):
        LT.doc_tep(p)


def test_lenh_cho_boc_dua_thang_vao_phan_tich_lenh(tmp_path):
    vt = vi_the_tu_engine(CAU_HINH["luoi_deu"], bars_that(2500, seed=7))
    v, *_ = doc_lai(vt, tmp_path)
    c = LT.lenh_cho_boc(v)
    assert c.attrs["da_chuan_hoa"] and set(c.columns) >= {"mo", "dong", "chieu", "lot", "gia_mo", "gia_dong", "loi", "ma"}
    assert len(c) == len(vt)
    kq = BL.phan_tich_lenh(c)
    # luoi_deu: buoc 15 pip, tp 6 pip, tran 5 tang - bo boc co san phai gan dung tu lenh DOC LAI tu bao cao
    assert kq["buoc"]["buoc"] == pytest.approx(15, abs=2), kq["buoc"]
    assert kq["tp"]["tp"] == pytest.approx(6, abs=2), kq["tp"]
    assert kq["che_do"]["gia_tri"] == "hai_chieu" and kq["lot"]["kieu_lot"] == "phang"


def test_attrs_day_du(tmp_path):
    vt = vi_the_tu_engine(CAU_HINH["luoi_deu"], bars_that(400, seed=8))
    v, *_ = doc_lai(vt, tmp_path, inputs={"InpTP": "6"})
    for k in ("ghep", "mo_coi", "hop_dong", "nap_rut", "so_deal", "kiem_so_du", "tick", "pip", "inputs", "canh_bao", "von_dau"):
        assert k in v.attrs, k
    assert v.attrs["inputs"] == {"InpTP": "6"} and v.attrs["von_dau"] == 10000.0 and v.attrs["pip"] == pytest.approx(1e-4)
    assert sum(v.attrs["ghep"].values()) == len(v) and v.attrs["ghep"].get("chua_dong", 0) == (v["cach_ghep"] == "chua_dong").sum()
    assert v.attrs["hop_dong_nguon"] == {"AUDCAD": "tu_hieu_chuan"} or v.attrs["hop_dong_nguon"] == {"AUDCAD": "mau_sach"}
