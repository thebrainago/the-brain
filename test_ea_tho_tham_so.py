# -*- coding: utf-8 -*-
"""ea_tho: tham_so bi KIEM (sai ten / khong phai so), bo_set (file .set cua tac gia chay NGUYEN VAN) va EA nhi phan (.ex5).

Khong co MT5 o day: tester la `MayGia` (test_ea_tho), phan cham terminal that (`_chay_voi_slot`) chay voi slot gia + thu muc
tam. Cai kiem duoc la QUYET DINH cua code: cai gi bi tu choi TRUOC khi ton mot luot tester / mot phep thu / mot lan niem
phong, cai gi duoc phep vao so tay (CONG KHAI, git la public), va cac dieu kien an toan cua nhanh nhi phan.
Chua kiem duoc o day (can may nha): MT5 co nap dung .ex5 copy vao Experts\\_tu_dong va .set ten kem khong - xem
`nhan/ea_tho.py` diem hieu chuan 5.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import shutil
import subprocess
import types
from pathlib import Path

import pytest

import ea_tu_dong as EA
from nhan import ea_tho as E
from nhan import nc_so_tay as ST
from test_ea_tho import CHIEN_LUOC, dat_tester, dem, ea_cl, moi_truong  # noqa: F401  (fixture dung chung)

RICH = """
#include <Trade/Trade.mqh>
input group "Chung"
input int                InpFast   = 12;       // nhanh
input int                InpSlow   = 26;
input double             InpStep   = 50.0;
input ENUM_MA_METHOD     InpMethod = MODE_SMA;
input bool               InpBuoc   =
     true;                                     // khai bao tren hai dong
input string             InpGhiChu = "abc";
sinput int               InpMagic  = 777;
extern double            InpLots   = 0.1;
input datetime           InpTu     = D'2020.01.01';
input color              InpMau    = clrRed;
// input int InpDaBo = 5;     <- input da bo, khong con trong EA
CTrade trade;
void OnTick() { if(iMA(_Symbol,PERIOD_CURRENT,InpFast,0,MODE_SMA,PRICE_CLOSE,0) > 0) trade.Buy(InpLots); }
"""

CO_MQH = """
#include "Cuc.mqh"
input int InpFast = 12;
CTrade trade;
void OnTick() { trade.Buy(0.1); }
"""

KHAI_RICH = {"InpFast": "int", "InpSlow": "int", "InpStep": "double", "InpMethod": "ENUM_MA_METHOD", "InpBuoc": "bool",
             "InpGhiChu": "string", "InpMagic": "int", "InpLots": "double", "InpTu": "datetime", "InpMau": "color"}


@pytest.fixture
def ea_rich(tmp_path):
    f = tmp_path / "RichEA.mq5"
    f.write_text(RICH, encoding="utf-8")
    return str(f)


def _gt():
    return ST.them_gia_thuyet("EA cong khai co lai sau phi tren EURUSD H1", "EA da ban cong khai", ho="ea_tho")


def _set(tmp_path, ten, dong, ma_hoa="utf-16"):
    """Ghi file .set nhu MT5 (UTF-16 LE co BOM, CRLF) hoac utf-8."""
    f = tmp_path / ten
    if ma_hoa == "utf-16":
        f.write_bytes(b"\xff\xfe" + ("\r\n".join(dong) + "\r\n").encode("utf-16-le"))
    else:
        f.write_text("\n".join(dong) + "\n", encoding=ma_hoa)
    return str(f)


def _bo(tmp_path, ten, *dong):
    return _set(tmp_path, ten, list(dong))


def _ex5(tmp_path, ten="BotDen.ex5", mau=b"\x00\x01\x02MQL5\x7f\xfe", n=1500):
    """Byte gia dang chuong trinh: co NUL, it ky tu in duoc (van ban thuan hay HTML thi bi tu choi)."""
    f = tmp_path / ten
    f.write_bytes((mau * (n // len(mau) + 1))[:n])
    return str(f)


def _bi_mat_gia() -> str:
    """Chuoi mang DANG token Telegram, ghep luc chay: khong de nguyen van trong repo cong khai (secret scanning)."""
    return "123456789" + ":" + "A" * 35


# ============================================================ A. THAM_SO BI KIEM
def test_input_khai_bao_ke_ca_bool_chuoi_enum_nhieu_dong_va_bo_chu_thich():
    assert E.input_khai_bao(RICH) == KHAI_RICH, "input_so chi giu so; day phai thay het (tru input da comment)"
    assert "InpDaBo" not in E.input_khai_bao(RICH)


def test_kiem_tham_so_chap_nhan_so_dung_kieu():
    ok = {"InpFast": 8, "InpStep": 35.5, "InpMethod": 1, "InpBuoc": 0, "InpLots": 0.05, "InpMau": 255,
          "InpTu": 1577836800}
    assert E.kiem_tham_so(ok, RICH) is None
    assert E.kiem_tham_so({"InpBuoc": True, "InpFast": 8.0}, RICH) is None, "True = 1; 8.0 la so nguyen"
    assert E.kiem_tham_so({}, RICH) is None


@pytest.mark.parametrize("ts, mong", [
    ({"InpFasst": 8}, "gan giong: InpFasst -> InpFast"),
    ({"InpDaBo": 5}, "InpDaBo"),                                # input da bi comment khong con la input
    ({"InpGhiChu": 5}, "bo_set"),                               # input chuoi: so khong qua duoc o day
    ({"InpFast": "8"}, "SO huu han"),
    ({"InpFast": float("nan")}, "SO huu han"),
    ({"InpFast": float("inf")}, "SO huu han"),
    ({"InpFast": 10 ** 400}, "SO huu han"),                     # so nguyen khong lo: khong duoc vo cong cu
    ({"InpFast": None}, "SO huu han"),
    ({"InpFast": [8]}, "SO huu han"),
    ({"InpFast": 8.5}, "nguyen"),
    ({"InpMethod": 1.5}, "nguyen"),
    ({"InpBuoc": 0.5}, "nguyen"),
    ({"InpBuoc": 2}, "0 / 1"),
])
def test_kiem_tham_so_tu_choi(ts, mong):
    ly = E.kiem_tham_so(ts, RICH)
    assert ly and mong in ly, ly


def test_kiem_tham_so_khong_sua_doi_dau_vao():
    ts = {"InpFast": 8, "InpBuoc": True}
    E.kiem_tham_so(ts, RICH)
    assert ts == {"InpFast": 8, "InpBuoc": True}


def test_ea_co_mqh_cua_tac_gia_khong_bi_tu_choi_oan_vi_ten_la(tmp_path):
    f = tmp_path / "CoMqh.mq5"
    f.write_text(CO_MQH, encoding="utf-8")
    d = E.doc_ea(str(f))
    assert E.co_input_ngoai(CO_MQH) and not E.co_input_ngoai(RICH)
    cfg = dict(E.cau_hinh(), tep_san=["Cuc.mqh"])
    r = E.lap_lenh(d, "EURUSD", "H1", "kham_pha", {"InpFast": 8, "InpTrongMqh": 3}, cfg=cfg)
    assert r["trang_thai"] == "SAN_SANG" and r["lenh"]["khoa_chua_kiem"] == ["InpTrongMqh"]
    # van kiem KIEU tren khoa biet, va gia tri khong phai so van bi chan
    assert E.lap_lenh(d, "EURUSD", "H1", "kham_pha", {"InpTrongMqh": "x"}, cfg=cfg)["trang_thai"] == "CHUA_DO_DUOC"
    assert E.lap_lenh(d, "EURUSD", "H1", "kham_pha", {"InpFast": 8.5}, cfg=cfg)["trang_thai"] == "CHUA_DO_DUOC"
    # khoa dung ten thi khong co canh bao "chua kiem"
    assert "khoa_chua_kiem" not in E.lap_lenh(d, "EURUSD", "H1", "kham_pha", {"InpFast": 8}, cfg=cfg)["lenh"]


def test_tham_so_sai_bi_chan_truoc_tester_khong_ghi_so_tay_khong_dem_phep_thu(ea_cl, tmp_path, monkeypatch):
    t = dat_tester(monkeypatch, tmp_path)
    gt = _gt()
    for ts in ({"InpFasst": 8}, {"InpFast": "8"}, {"InpFast": float("nan")}, {"InpFast": 8.5}, {"InpFast": 10 ** 400}):
        r = E.chay(ea_cl, "EURUSD", "H1", "kham_pha", ts, gt)
        assert r["trang_thai"] == "CHUA_DO_DUOC" and r["ly_do"] and "tn_id" not in r, (ts, r)
    assert t.lan == 0 and dem("thi_nghiem") == 0 and ST.dem_phep_thu(gt_id=gt) == 0
    # xac_nhan / niem_phong cung khong lot qua: kiem nam truoc ke_hoach va truoc moi cong khac
    for doan in ("xac_nhan", "niem_phong"):
        assert E.chay(ea_cl, "EURUSD", "H1", doan, {"InpFasst": 8}, gt)["trang_thai"] == "CHUA_DO_DUOC"
    assert t.lan == 0 and dem("niem_phong") == 0


def test_tham_so_dung_van_chay_va_van_tay_khong_doi_so_voi_truoc_khi_co_kiem_tra(ea_cl, tmp_path, monkeypatch):
    """Kiem them khong duoc doi van tay: nhung thi nghiem da co trong so tay phai con khop (8 va 8.0 van la mot)."""
    t = dat_tester(monkeypatch, tmp_path)
    gt = _gt()
    r = E.chay(ea_cl, "EURUSD", "H1", "kham_pha", {"InpFast": 8, "InpStep": 35}, gt)
    r2 = E.chay(ea_cl, "EURUSD", "H1", "kham_pha", {"InpStep": 35.0, "InpFast": 8.0}, gt)
    assert r["trang_thai"] == "DAT" and r2["tu_so_tay"] and t.lan == 1
    assert r["tham_so"] == {"InpFast": 8.0, "InpStep": 35.0}


# ============================================================ B. doc_set
def test_doc_set_doc_utf16_bom_bo_hau_to_toi_uu_chu_thich_va_dong_trong(tmp_path):
    f = _set(tmp_path, "CLMCA_Gold.set", ["; saved by MT5", "InpFast=8||5||1||20||N", "",
                                          "InpSlow=26||26||1||260||Y", "InpBuoc=true", "InpGhiChu=BUY SELL"])
    s = E.doc_set(f)
    assert s["khoa"] == {"InpFast": "8", "InpSlow": "26", "InpBuoc": "true", "InpGhiChu": "BUY SELL"} and s["n"] == 4
    assert s["ten"] == "CLMCA_Gold"
    assert s["van_ban"] == "InpBuoc=true\nInpFast=8\nInpGhiChu=BUY SELL\nInpSlow=26\n", "sap theo khoa, khong dong thua"


def test_doc_set_van_tay_khong_phu_thuoc_thu_tu_ma_hoa_ten_file_hay_hau_to_toi_uu(tmp_path):
    a = E.doc_set(_set(tmp_path, "a.set", ["InpFast=8", "InpBuoc=true"]))
    b = E.doc_set(_set(tmp_path, "b_khac_ten.set", ["InpBuoc=true||0||0||0||N", "; c", "InpFast=8"], "utf-8"))
    assert a["sha"] == b["sha"] and a["van_ban"] == b["van_ban"] and a["ten"] != b["ten"]
    assert E.doc_set(_set(tmp_path, "c.set", ["InpFast=9", "InpBuoc=true"]))["sha"] != a["sha"]
    assert E.doc_set(_set(tmp_path, "d.set", ["InpFast=8", "InpBuoc=false"]))["sha"] != a["sha"], "doi bool = bo khac"


@pytest.mark.parametrize("ten, dong, mong", [
    ("a.txt", ["InpFast=8"], ".set"),
    ("a.ini", ["InpFast=8"], ".set"),
    ("a.set", ["InpFast"], "dong 1"),
    ("a.set", ["InpFast=8", "Inp Fast=9"], "dong 2"),
    ("a.set", ["InpFast,F=0", "InpSlow,F=1"], "dong 1"),         # kieu MT4: dau phay khong phai khoa MT5
    ("a.set", ["InpFast=8", "InpFast=9"], "lap"),
    ("a.set", ["InpFast=8\x07x"], "dieu khien"),
    ("a.set", ["Inp=" + "x" * 201], "qua dai"),
    ("a.set", ["; chi comment", ""], "khong co khoa"),
    ("a.set", [], "khong co khoa"),
])
def test_doc_set_tu_choi(tmp_path, ten, dong, mong):
    with pytest.raises(ValueError) as e:
        E.doc_set(_set(tmp_path, ten, dong))
    assert mong in str(e.value)


def test_doc_set_gioi_han_dung_luong_so_khoa_va_tep_khong_ton_tai(tmp_path, monkeypatch):
    f = _set(tmp_path, "a.set", ["K%d=1" % i for i in range(6)])
    monkeypatch.setattr(E, "SET_TOI_DA_KHOA", 5)
    with pytest.raises(ValueError, match="qua nhieu khoa"):
        E.doc_set(f)
    monkeypatch.setattr(E, "SET_TOI_DA_KHOA", 500)
    monkeypatch.setattr(E, "SET_TOI_DA_BYTE", 20)
    with pytest.raises(ValueError, match="lon bat thuong"):
        E.doc_set(f)
    with pytest.raises(OSError):
        E.doc_set(str(tmp_path / "khong_co.set"))


def test_doc_set_loi_khong_lap_lai_noi_dung_dong_sai(tmp_path):
    with pytest.raises(ValueError) as e:
        E.doc_set(_set(tmp_path, "a.set", ["InpFast=8", "bi-mat-cua-toi 123456"]))
    msg = str(e.value)
    assert "dong 2" in msg and "bi-mat" not in msg and "123456" not in msg, "loi vao so tay CONG KHAI: khong in noi dung"


@pytest.mark.parametrize("dong, khoa", [
    ("TelegramToken=" + _bi_mat_gia(), "TelegramToken"),
    ("LicenseKey=ABCD-1234-EFGH", "LicenseKey"),
    ("InpApiKey=abc", "InpApiKey"),
    ("Password=hunter2", "Password"),
    ("InvestorPass=hunter2", "InvestorPass"),
    ("InpGhiChu=ghp_" + "a" * 36, "InpGhiChu"),                 # khoa vo hai nhung gia tri mang dang token
    ("InpTen=AKIA" + "A" * 16, "InpTen"),
    ("InpGhiChu=" + _bi_mat_gia(), "InpGhiChu"),
])
def test_doc_set_chan_bi_mat_khong_dua_len_so_tay_cong_khai(tmp_path, dong, khoa):
    with pytest.raises(ValueError) as e:
        E.doc_set(_set(tmp_path, "a.set", ["InpFast=8", dong]))
    msg, gia_tri = str(e.value), dong.split("=", 1)[1]
    assert khoa in msg and "CONG KHAI" in msg
    assert gia_tri not in msg and "hunter2" not in msg and "ABCD-1234" not in msg, "chi neu TEN khoa, khong neu gia tri"


def test_doc_set_khoa_nhay_cam_co_gia_tri_so_ngan_hay_rong_van_chay(tmp_path):
    f = _set(tmp_path, "a.set", ["InpLicenseDays=30", "PasswordLen=8", "InvestorMode=true", "TokenSize=0.5", "InpApiKey="])
    assert E.doc_set(f)["n"] == 5


# ============================================================ C. bo_set trong lap_lenh / chay
def test_bo_set_loai_tru_tham_so_va_loi_doc_deu_la_chua_do_duoc_khong_ton_tester(ea_rich, tmp_path, monkeypatch):
    t = dat_tester(monkeypatch, tmp_path)
    ok = _bo(tmp_path, "a.set", "InpFast=8")
    r = E.chay(ea_rich, "EURUSD", "H1", "kham_pha", {"InpFast": 8}, None, bo_set=ok)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "loai tru" in r["ly_do"]
    for hong in (str(tmp_path / "khong_co.set"), _set(tmp_path, "b.txt", ["InpFast=8"]), _bo(tmp_path, "c.set", "InpFast")):
        r = E.chay(ea_rich, "EURUSD", "H1", "kham_pha", None, None, bo_set=hong)
        assert r["trang_thai"] == "CHUA_DO_DUOC" and "khong doc duoc .set" in r["ly_do"], r
    r = E.chay(ea_rich, "EURUSD", "H1", "kham_pha", None, None,
               bo_set=_bo(tmp_path, "d.set", "TelegramToken=" + _bi_mat_gia()))
    assert "nhay cam" in r["ly_do"] and "AAAA" not in r["ly_do"]
    assert t.lan == 0 and dem("thi_nghiem") == 0


def test_bo_set_lap_lenh_chay_nguyen_van_khong_dich_tung_input(ea_rich, tmp_path):
    d = E.doc_ea(ea_rich)
    f = _bo(tmp_path, "CLMCA_Gold.set", "InpFast=8||5||1||20||N", "InpBuoc=true", "InpGhiChu=Alpha beta", "InpLa=1")
    r = E.lap_lenh(d, "EURUSD", "H1", "kham_pha", bo_set=f)
    assert r["trang_thai"] == "SAN_SANG"
    l, s = r["lenh"], E.doc_set(f)
    assert l["viec"]["tep_set_tho"] == s["van_ban"] == "InpBuoc=true\nInpFast=8\nInpGhiChu=Alpha beta\nInpLa=1\n"
    assert l["viec"]["input"] == {}, "khong dich sang input so: bool / chuoi di nguyen trong tep_set_tho"
    assert l["tham_so"] == {"@bo_set": s["sha"]}
    assert l["bo_set"] == {"ten": "CLMCA_Gold", "sha": s["sha"], "so_khoa": 4, "van_ban": s["van_ban"],
                           "khoa_la": ["InpLa"], "doi_chieu": "du"}
    # khong co bo_set: khong co tep_set_tho (chay dung duong input cu)
    r0 = E.lap_lenh(d, "EURUSD", "H1", "kham_pha", {"InpFast": 8})["lenh"]
    assert "tep_set_tho" not in r0["viec"] and "bo_set" not in r0 and r0["viec"]["input"] == {"InpFast": {"gia_tri": 8}}


def test_bo_set_van_tay_khac_theo_tung_bo_khac_mac_dinh_va_giong_khi_cung_noi_dung(ea_rich, tmp_path):
    d = E.doc_ea(ea_rich)

    def vt(**kw):
        return E.lap_lenh(d, "EURUSD", "H1", "kham_pha", **kw)["lenh"]["van_tay"]
    a = vt(bo_set=_bo(tmp_path, "a.set", "InpFast=8", "InpBuoc=true"))
    a2 = vt(bo_set=_bo(tmp_path, "ten_khac.set", "InpBuoc=true", "InpFast=8||1||1||9||N"))
    b = vt(bo_set=_bo(tmp_path, "b.set", "InpFast=8", "InpBuoc=false"))
    assert a == a2 and len({a, b, vt(), vt(tham_so={"InpFast": 8})}) == 4


def test_bo_set_chay_day_du_so_tay_giu_van_ban_set_ket_qua_thi_khong_va_chay_lai_khong_ton_tester(
        ea_rich, tmp_path, monkeypatch):
    t = dat_tester(monkeypatch, tmp_path)
    gt = _gt()
    f = _bo(tmp_path, "CLMCA_Gold.set", "InpFast=8", "InpBuoc=true", "InpLa=1")
    r = E.chay(ea_rich, "EURUSD", "H1", "kham_pha", None, gt, bo_set=f)
    assert r["trang_thai"] == "DAT" and t.lan == 1
    assert t.lenh[0]["viec"]["tep_set_tho"] == "InpBuoc=true\nInpFast=8\nInpLa=1\n"
    assert "van_ban" not in r["bo_set"] and r["bo_set"]["khoa_la"] == ["InpLa"]
    assert any("InpLa" in x and ".set" in x for x in r["nhan"]["canh_bao"]), r["nhan"]
    dv = ST.mot("SELECT dau_vao FROM thi_nghiem WHERE id=?", r["tn_id"])["dau_vao"]
    dv = json.loads(dv) if isinstance(dv, str) else dv
    assert dv["bo_set"]["van_ban"] == "InpBuoc=true\nInpFast=8\nInpLa=1\n", "so tay giu van ban .set (o D:\\ co the mat)"
    r2 = E.chay(ea_rich, "EURUSD", "H1", "kham_pha", None, gt, bo_set=f)
    assert r2["tu_so_tay"] and t.lan == 1 and ST.dem_phep_thu(gt_id=gt) == 1
    E.chay(ea_rich, "EURUSD", "H1", "kham_pha", None, gt, bo_set=_bo(tmp_path, "CLMCA_Eur.set", "InpFast=9", "InpBuoc=true"))
    assert ST.dem_phep_thu(gt_id=gt) == 2 and t.lan == 2, "moi .set khac = mot phep thu duoc dem"


def test_bo_set_khoa_la_cua_ea_co_mqh_chi_canh_bao_nhe(tmp_path, monkeypatch):
    f = tmp_path / "CoMqh.mq5"
    f.write_text(CO_MQH, encoding="utf-8")
    d = E.doc_ea(str(f))
    cfg = dict(E.cau_hinh(), tep_san=["Cuc.mqh"])
    r = E.lap_lenh(d, "EURUSD", "H1", "kham_pha", bo_set=_bo(tmp_path, "a.set", "InpFast=8", "InpTrongMqh=3"), cfg=cfg)
    assert r["lenh"]["bo_set"]["doi_chieu"] == "mot_phan" and r["lenh"]["bo_set"]["khoa_la"] == ["InpTrongMqh"]


def test_niem_phong_voi_bo_set_phai_la_dung_bo_da_qua_xac_nhan(ea_rich, tmp_path, monkeypatch):
    t = dat_tester(monkeypatch, tmp_path, kq=lambda l: {"lenh": 40})
    gt = _gt()
    a = _bo(tmp_path, "a.set", "InpFast=8", "InpBuoc=true")
    b = _bo(tmp_path, "b.set", "InpFast=9", "InpBuoc=true")
    r = E.chay(ea_rich, "EURUSD", "H1", "niem_phong", None, gt, bo_set=a)
    assert "xac_nhan DAT" in r["ly_do"] and t.lan == 0
    assert E.chay(ea_rich, "EURUSD", "H1", "xac_nhan", None, gt, bo_set=a)["trang_thai"] == "DAT"
    for sai in ({"bo_set": b}, {}, {"tham_so": {"InpFast": 8}}):          # bo .set khac / mac dinh / tham_so: deu la bo KHAC
        kw = dict(sai)
        r = E.chay(ea_rich, "EURUSD", "H1", "niem_phong", kw.pop("tham_so", None), gt, **kw)
        assert "xac_nhan DAT" in r["ly_do"] and "CHINH bo" in r["ly_do"], (sai, r)
    assert dem("niem_phong") == 0 and t.lan == 1
    r = E.chay(ea_rich, "EURUSD", "H1", "niem_phong", None, gt, bo_set=a)
    assert r["trang_thai"] == "DAT" and dem("niem_phong") == 1 and t.lan == 2
    spec = ST.mot("SELECT spec FROM niem_phong")["spec"]
    spec = json.loads(spec) if isinstance(spec, str) else spec
    assert spec["bo_set"]["van_ban"] == "InpBuoc=true\nInpFast=8\n"


def test_cong_cu_ea_tho_chay_tu_choi_tham_so_sai_va_nhan_bo_set(ea_rich, tmp_path, monkeypatch):
    from nhan import nc_cong_cu as CC
    t = dat_tester(monkeypatch, tmp_path)
    r = CC.goi("ea_tho_chay", {"ea": ea_rich, "ma": "EURUSD", "khung": "H1", "tham_so": {"InpFasst": 8}})
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "InpFasst" in r["ly_do"] and t.lan == 0
    f = _bo(tmp_path, "a.set", "InpFast=8", "InpBuoc=true")
    r = CC.goi("ea_tho_chay", {"ea": ea_rich, "ma": "EURUSD", "khung": "H1", "bo_set": f})
    assert r["trang_thai"] == "DAT" and r["bo_set"]["so_khoa"] == 2 and "van_ban" not in r["bo_set"] and t.lan == 1
    r = CC.goi("ea_tho_chay", {"ea": ea_rich, "ma": "EURUSD", "khung": "H1", "bo_set": f, "tham_so": {"InpFast": 8}})
    assert "loai tru" in r["ly_do"]
    api = {c["name"]: c for c in CC.schema_api()}["ea_tho_chay"]
    assert "bo_set" in api["input_schema"]["properties"] and "bo_set" in api["description"]
    assert "bo_set" not in api["input_schema"]["required"]


# ============================================================ D. EA NHI PHAN (.ex5)
def test_doc_ea_ex5_la_nhi_phan_khong_ma_nguon_sha_theo_byte(tmp_path):
    f = _ex5(tmp_path, "Bot Den v3.0.5.ex5")
    d = E.doc_ea(f)
    assert d["nhi_phan"] is True and d["ma"] == "" and d["url"] == "" and d["duong"] == f and d["dung_luong"] == 1500
    assert d["tieu_de"] == "Bot Den v3.0.5" and d["ten"].startswith("Bot_Den_v3_0_5_")
    assert d["sha"] == hashlib.sha1(Path(f).read_bytes()).hexdigest()[:16]
    g = _ex5(tmp_path, "Bot Den v3.0.5 (2).ex5", mau=b"\x00\x01\x02XYZ\x7f\xfe")
    assert E.doc_ea(g)["sha"] != d["sha"] and E.doc_ea(g)["ten"] != d["ten"]
    assert E.doc_ea(_ex5(tmp_path, "Hoa.EX5"))["nhi_phan"] is True, "duoi viet hoa van la .ex5"


@pytest.mark.parametrize("ten, noi_dung, mong", [
    ("a.ex4", b"\x00" * 2000, "MT4"),
    ("a.mq4", b"void OnTick(){}" * 100, "MQL4"),
    ("a.set", b"InpFast=8\n", "bo_set"),
    ("a.zip", b"PK\x03\x04" + b"\x00" * 2000, "KHONG chay"),
    ("a.exe", b"MZ" + b"\x00" * 2000, "KHONG chay"),
    ("a.dll", b"MZ" + b"\x00" * 2000, "KHONG chay"),
    ("a.msi", b"\xd0\xcf" + b"\x00" * 2000, "KHONG chay"),
    ("a.rar", b"Rar!" + b"\x00" * 2000, "KHONG chay"),
    ("a.7z", b"7z\xbc\xaf" + b"\x00" * 2000, "KHONG chay"),
    ("a.ex5", b"\x00" * 100, "qua nho"),
    ("a.ex5", b"<!DOCTYPE html><html><body>Quota exceeded</body></html>" + b" " * 800, "van ban"),
    ("a.ex5", b"<html>" + b"\x00" * 800, "van ban"),
    ("a.ex5", b'{"error": "not found"} ' * 60, "van ban"),
    ("a.ex5", b"hello world " * 100, "van ban"),
])
def test_doc_ea_khong_chap_nhan_loai_nay(tmp_path, ten, noi_dung, mong):
    f = tmp_path / ten
    f.write_bytes(noi_dung)
    with pytest.raises(ValueError) as e:
        E.doc_ea(str(f))
    assert mong in str(e.value)


def test_doc_ea_ex5_qua_lon_va_tep_khong_ton_tai(tmp_path, monkeypatch):
    f = _ex5(tmp_path)
    monkeypatch.setattr(E, "EX5_TOI_DA_BYTE", 1000)
    with pytest.raises(ValueError, match="lon bat thuong"):
        E.doc_ea(f)
    with pytest.raises(KeyError):
        E.doc_ea(str(tmp_path / "khong_co.ex5"))


def test_kham_nhi_phan_khong_phan_loai_khong_goi_tester(tmp_path, monkeypatch):
    t = dat_tester(monkeypatch, tmp_path)
    k = E.kham(_ex5(tmp_path))
    assert k["nhi_phan"] is True and k["phan_loai"]["loai"] == "NHI_PHAN" and k["phan_loai"]["input_so"] == []
    assert "NHI PHAN" in k["ket_luan"] and "Allow DLL imports" in k["ket_luan"]
    assert "ma_khung" not in k, "khong co ma nguon: khong tu chon ma / khung"
    assert t.lan == 0


def test_lap_lenh_nhi_phan_chi_nhan_bo_set_hoac_mac_dinh(tmp_path):
    d = E.doc_ea(_ex5(tmp_path))
    r = E.lap_lenh(d, "XAUUSD", "H1", "kham_pha", {"InpFast": 8})
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "bo_set" in r["ly_do"] and "nhi phan" in r["ly_do"]
    r0 = E.lap_lenh(d, "XAUUSD", "H1", "kham_pha")
    assert r0["trang_thai"] == "SAN_SANG" and r0["lenh"]["nhi_phan"] == {"sha": d["sha"], "dung_luong": 1500}
    assert "bo_set" not in r0["lenh"] and "tep_set_tho" not in r0["lenh"]["viec"]
    f = _bo(tmp_path, "CCBSN_XAU.set", "Lots=0.01", "UseTP=true")
    r1 = E.lap_lenh(d, "XAUUSD", "H1", "kham_pha", bo_set=f)["lenh"]
    assert r1["bo_set"]["khoa_la"] == [] and r1["bo_set"]["doi_chieu"] == "khong", "khong ma nguon de doi chieu ten khoa"
    assert r1["van_tay"] != r0["lenh"]["van_tay"]
    d2 = E.doc_ea(_ex5(tmp_path, "Khac.ex5", mau=b"\x00\x01\x02XYZ\x7f\xfe"))
    assert E.lap_lenh(d2, "XAUUSD", "H1", "kham_pha", bo_set=f)["lenh"]["van_tay"] != r1["van_tay"]


def test_chay_nhi_phan_ghi_so_tay_va_nhan_canh_bao_hop_den(tmp_path, monkeypatch):
    t = dat_tester(monkeypatch, tmp_path)
    thay: list[dict] = []

    def bat(lenh, ea, cfg):
        thay.append(ea)
        return t(lenh, ea, cfg)
    monkeypatch.setattr(E, "CHAY_TESTER", bat)
    ex5, gt = _ex5(tmp_path), _gt()
    r = E.chay(ex5, "XAUUSD", "H1", "kham_pha", None, gt, bo_set=_bo(tmp_path, "a.set", "Lots=0.01"))
    assert r["trang_thai"] == "DAT" and r["nhi_phan"]["dung_luong"] == 1500 and t.lan == 1
    assert thay[0]["nhi_phan"] is True and thay[0]["duong"] == ex5, "tester nhan duong .ex5 de copy"
    assert any("EA NHI PHAN (hop den)" in x for x in r["nhan"]["canh_bao"])
    dv = ST.mot("SELECT dau_vao FROM thi_nghiem WHERE id=?", r["tn_id"])["dau_vao"]
    dv = json.loads(dv) if isinstance(dv, str) else dv
    assert dv["nhi_phan"]["sha"] == E.doc_ea(ex5)["sha"] and dv["bo_set"]["van_ban"] == "Lots=0.01\n"
    r2 = E.chay(ex5, "XAUUSD", "H1", "kham_pha", None, gt, bo_set=_bo(tmp_path, "b.set", "Lots=0.01"))
    assert r2["tu_so_tay"] and t.lan == 1, "cung noi dung .set (khac ten file): cung van tay"


def test_quet_va_tinh_bo_qua_ea_nhi_phan_co_ly_do(tmp_path, monkeypatch):
    t = dat_tester(monkeypatch, tmp_path)
    ex5 = _ex5(tmp_path)
    q = E.quet([ex5], co_san=["EURUSD"])
    assert q["so_lan_chay"] == 0 and [b["loai"] for b in q["bo_qua"]] == ["NHI_PHAN"] and not q["bang"]
    r = E.tinh(ex5, "EURUSD", "H1")
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "bo_set" in r["ly_do"]
    assert t.lan == 0 and dem("thi_nghiem") == 0 and dem("gia_thuyet") == 0


def test_niem_phong_nhi_phan_ghi_ro_hop_den_chua_phai_cua_ta(ea_rich, tmp_path, monkeypatch):
    dat_tester(monkeypatch, tmp_path, kq=lambda l: {"lenh": 40})
    ex5, gt, f = _ex5(tmp_path), _gt(), _bo(tmp_path, "a.set", "Lots=0.01")
    assert E.chay(ex5, "EURUSD", "H1", "xac_nhan", None, gt, bo_set=f)["trang_thai"] == "DAT"
    r = E.chay(ex5, "EURUSD", "H1", "niem_phong", None, gt, bo_set=f)
    assert r["trang_thai"] == "DAT" and "hop den" in r["goi_ten_dung"] and "chua phai 'cua ta'" in r["goi_ten_dung"]
    # EA co ma nguon: khong co cau nay
    gt2, g = _gt(), _bo(tmp_path, "g.set", "InpFast=8")
    assert E.chay(ea_rich, "EURUSD", "H1", "xac_nhan", None, gt2, bo_set=g)["trang_thai"] == "DAT"
    r2 = E.chay(ea_rich, "EURUSD", "H1", "niem_phong", None, gt2, bo_set=g)
    assert r2["trang_thai"] == "DAT" and "hop den" not in r2["goi_ten_dung"]


# ---- phan cham terminal that: `_chay_voi_slot` voi slot gia + thu muc tam
class SlotGia:
    """Thay `slot_tester`: `cap` tra mot slot tro vao thu muc tam."""

    def __init__(self, goc: Path):
        self.goc, self.da_cap = goc, []
        self.dat = goc / "dat"
        self.cai = goc / "cai"

    @contextlib.contextmanager
    def cap(self, ten):
        self.da_cap.append(ten)
        yield types.SimpleNamespace(ten="s1", exe=self.cai / "terminal64.exe", du_lieu=self.dat)

    def ex5_trong_terminal(self, ten_file: str) -> Path:
        return self.dat / "MQL5" / "Experts" / "_tu_dong" / (ten_file + ".ex5")


def _common_ini(dat: Path, noi: str):
    (dat / "config").mkdir(parents=True, exist_ok=True)
    (dat / "config" / "common.ini").write_bytes(b"\xff\xfe" + noi.replace("\n", "\r\n").encode("utf-16-le"))


@pytest.fixture
def may(tmp_path, monkeypatch):
    """Slot gia + `ea_tu_dong` that voi `chay_mot` / `bien_dich` thay bang ban ghi lai."""
    sl = SlotGia(tmp_path / "may")
    monkeypatch.setattr(EA, "TERMINAL", dict(EA.TERMINAL))
    ghi: list[dict] = []
    bien: list[dict] = []

    def chay_mot(viec):
        dat = EA.TERMINAL[viec["terminal"]][0]
        ghi.append({"viec": viec, "co_ex5": (dat / "MQL5" / "Experts" / "_tu_dong" / (viec["ea"] + ".ex5")).exists()})
        return {"xong": True, "bao_cao": str(tmp_path / "bc.htm"), "giay": 1.0}

    def bien_dich(ds, ten_terminal, cho_giay=12.0):
        bien.append({"ds": ds, "terminal": ten_terminal})
        return [{"bien_dich": True, "ten_file": "MaCross_abc123", "loi": ""}]
    monkeypatch.setattr(EA, "chay_mot", chay_mot)
    monkeypatch.setattr(EA, "bien_dich", bien_dich)
    return types.SimpleNamespace(slot=sl, ghi=ghi, bien=bien)


def _lenh_va_ea(tmp_path, ex5_hay_mq5, *, bo_set=None):
    d = E.doc_ea(ex5_hay_mq5)
    lo = E.lap_lenh(d, "EURUSD", "H1", "kham_pha", bo_set=bo_set)
    assert lo["trang_thai"] == "SAN_SANG", lo
    return lo["lenh"], d


def test_chay_voi_slot_nhi_phan_dll_dang_bat_tu_choi_truoc_khi_copy(tmp_path, may):
    _common_ini(may.slot.dat, "[Common]\nLogin=0\n[Experts]\nAllowDllImport=1\n")
    lenh, d = _lenh_va_ea(tmp_path, _ex5(tmp_path))
    r = E._chay_voi_slot(lenh, d, E.cau_hinh(), EA, may.slot)
    assert r["xong"] is False and "DANG BAT" in r["loi"] and "Allow DLL imports" in r["loi"]
    assert may.ghi == [] and not (may.slot.dat / "MQL5" / "Experts" / "_tu_dong").exists(), "chua copy, chua chay"


def test_chay_voi_slot_nhi_phan_khong_doc_duoc_common_ini_cung_tu_choi(tmp_path, may):
    (may.slot.dat / "config" / "common.ini").mkdir(parents=True)        # thu muc o cho tep: doc se loi
    lenh, d = _lenh_va_ea(tmp_path, _ex5(tmp_path))
    r = E._chay_voi_slot(lenh, d, E.cau_hinh(), EA, may.slot)
    assert r["xong"] is False and "khong doc duoc" in r["loi"] and may.ghi == []


@pytest.mark.parametrize("noi", ["[Experts]\nAllowDllImport=0\n", "[Common]\nLogin=0\n", None])
def test_chay_voi_slot_nhi_phan_dll_tat_copy_chay_roi_xoa_ban_copy(tmp_path, may, noi):
    if noi is not None:                                                  # None = chua co common.ini: mac dinh MT5 la tat
        _common_ini(may.slot.dat, noi)
    ex5 = _ex5(tmp_path)
    lenh, d = _lenh_va_ea(tmp_path, ex5, bo_set=_bo(tmp_path, "a.set", "Lots=0.01"))
    r = E._chay_voi_slot(lenh, d, E.cau_hinh(), EA, may.slot)
    ten_file = EA.ten_sach(d["ten"])
    assert r["xong"] is True and r["bao_cao"] and len(may.ghi) == 1
    assert may.ghi[0]["co_ex5"] is True, ".ex5 phai co mat trong terminal LUC tester chay"
    assert may.ghi[0]["viec"]["ea"] == ten_file and may.ghi[0]["viec"]["terminal"] == "slot:s1"
    assert may.ghi[0]["viec"]["tep_set_tho"] == "Lots=0.01\n", "ban .set cua tac gia di cung viec"
    assert not may.slot.ex5_trong_terminal(ten_file).exists(), "xong thi xoa ban copy"
    assert may.slot.da_cap and may.slot.da_cap[0].startswith("ea_tho:") and may.bien == [], "khong bien dich .ex5"


def test_chay_voi_slot_nhi_phan_copy_dung_tung_byte(tmp_path, may, monkeypatch):
    ex5 = _ex5(tmp_path)
    lenh, d = _lenh_va_ea(tmp_path, ex5)
    da_thay = {}

    def chay_mot(viec):
        p = may.slot.ex5_trong_terminal(viec["ea"])
        da_thay["tho"] = p.read_bytes()
        return {"xong": True, "bao_cao": "", "giay": 0.1}
    monkeypatch.setattr(EA, "chay_mot", chay_mot)
    E._chay_voi_slot(lenh, d, E.cau_hinh(), EA, may.slot)
    assert da_thay["tho"] == Path(ex5).read_bytes()


def test_chay_voi_slot_nhi_phan_file_doi_giua_luc_doc_va_luc_chay_thi_tu_choi(tmp_path, may):
    ex5 = _ex5(tmp_path)
    lenh, d = _lenh_va_ea(tmp_path, ex5)
    Path(ex5).write_bytes(Path(ex5).read_bytes() + b"\x00\x01")        # bi thay sau khi lap van tay
    r = E._chay_voi_slot(lenh, d, E.cau_hinh(), EA, may.slot)
    assert r["xong"] is False and "khong dua duoc .ex5" in r["loi"] and "DOI" in r["loi"] and may.ghi == []
    assert not may.slot.ex5_trong_terminal(EA.ten_sach(d["ten"])).exists()


def test_chay_voi_slot_nhi_phan_tester_no_loi_van_xoa_ban_copy(tmp_path, may, monkeypatch):
    ex5 = _ex5(tmp_path)
    lenh, d = _lenh_va_ea(tmp_path, ex5)

    def no(viec):
        assert may.slot.ex5_trong_terminal(viec["ea"]).exists()
        raise RuntimeError("terminal chet")
    monkeypatch.setattr(EA, "chay_mot", no)
    with pytest.raises(RuntimeError):
        E._chay_voi_slot(lenh, d, E.cau_hinh(), EA, may.slot)
    assert not may.slot.ex5_trong_terminal(EA.ten_sach(d["ten"])).exists(), "finally: khong de bot nguoi la nam lai terminal"


def test_chay_voi_slot_ea_ma_nguon_van_bien_dich_va_khong_hoi_dll(tmp_path, may, ea_cl):
    _common_ini(may.slot.dat, "[Experts]\nAllowDllImport=1\n")           # DLL bat: chi chan EA NHI PHAN
    lenh, d = _lenh_va_ea(tmp_path, ea_cl)
    r = E._chay_voi_slot(lenh, d, E.cau_hinh(), EA, may.slot)
    assert r["xong"] is True and len(may.bien) == 1 and may.bien[0]["terminal"] == "slot:s1"
    assert may.bien[0]["ds"][0]["ma"] == d["ma"] and may.ghi[0]["viec"]["ea"] == "MaCross_abc123"
    assert not (may.slot.dat / "MQL5" / "Experts" / "_tu_dong").exists()


def test_chay_voi_slot_bien_dich_hong_la_loi_ha_tang(tmp_path, may, monkeypatch, ea_cl):
    monkeypatch.setattr(EA, "bien_dich", lambda ds, t, cho_giay=12.0: [{"bien_dich": False, "ten_file": "", "loi": "x"}])
    lenh, d = _lenh_va_ea(tmp_path, ea_cl)
    r = E._chay_voi_slot(lenh, d, E.cau_hinh(), EA, may.slot)
    assert r == {"xong": False, "loi": "bien dich hong: x"} and may.ghi == []


def test_chay_that_khong_phai_windows_van_tu_choi_noi_ro(tmp_path, monkeypatch):
    monkeypatch.setattr(E.os, "name", "posix")
    lenh, d = _lenh_va_ea(tmp_path, _ex5(tmp_path))
    r = E._chay_that(lenh, d, E.cau_hinh())
    assert r["xong"] is False and "may nha" in r["loi"]


# ============================================================ E. KHONG BAO GIO DUA BOT CUA NGUOI KHAC LEN GIT
@pytest.mark.skipif(shutil.which("git") is None, reason="khong co git")
@pytest.mark.parametrize("ten", ["Bot.ex5", "Bot.ex4", "x.dll", "setup.exe", "setup.msi", "bots.rar", "bots.7z", "bots.zip",
                                 "du_lieu_cao/telegram/nhom/Bot.ex5"])
def test_gitignore_chan_nhi_phan_va_goi_cai_cua_nguoi_khac(ten):
    r = subprocess.run(["git", "check-ignore", "-q", ten], cwd=str(Path(__file__).resolve().parent), capture_output=True)
    assert r.returncode == 0, "%s phai bi .gitignore chan (repo PUBLIC)" % ten
