# -*- coding: utf-8 -*-
"""Test `nhan/chan_doan_tester.py` + noi vao `ea_tho._chay_voi_slot` (08/10/2026).

Khong co MT5 o day: cay thu muc terminal / tester / log la FILE GIA trong tmp_path, dung dinh dang that cua MT5
(log UTF-16 LE co BOM, cot ngan cach bang TAB: `MA\\t0\\t12:01:02.123\\tCore 1\\tnoi dung`). Moi test co mot LOI CO Y de bat
(xem docstring) - `pytest -k <ten>` roi sua code cho hong thu xem test co do khong.
"""
import contextlib
import os
import sys
import time
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nhan import chan_doan_tester as CDT        # noqa: E402
from nhan import ea_tho as E                    # noqa: E402
import ea_tu_dong as EA                         # noqa: E402


# ------------------------------------------------------------------ do dung
def ghi_log(p: Path, dong: list[str], utf16: bool = True, mtime: float | None = None):
    """Ghi log kieu MT5: moi dong `XX\\t0\\t<gio>\\t<nguon>\\t<noi dung>`."""
    p.parent.mkdir(parents=True, exist_ok=True)
    van = "\r\n".join("XX\t0\t12:%02d:%02d.123\t%s\t%s" % (i // 60 % 60, i % 60, nguon, nd)
                     for i, (nguon, nd) in enumerate(dong)) + "\r\n"
    p.write_bytes((b"\xff\xfe" + van.encode("utf-16-le")) if utf16 else van.encode("utf-8"))
    if mtime is not None:
        os.utime(p, (mtime, mtime))
    return p


@pytest.fixture
def cay(tmp_path):
    """Thu muc du lieu terminal GIA + 'home' gia (Tester kieu THUONG nam o home/AppData/Roaming/MetaQuotes/Tester/<ten du lieu>)."""
    dl = tmp_path / "Terminal" / "ABCDEF0123456789"
    (dl / "MQL5" / "Include" / "Trade").mkdir(parents=True)
    (dl / "MQL5" / "Include" / "Trade" / "Trade.mqh").write_text("//", encoding="utf-8")
    home = tmp_path / "home"
    tester = home / "AppData" / "Roaming" / "MetaQuotes" / "Tester" / dl.name
    return types.SimpleNamespace(dl=dl, home=home, tester=tester, tmp=tmp_path)


# ------------------------------------------------------------------ 1. doc log
def test_doc_duoi_utf16_bo_hai_cot_ma_va_chi_lay_dong_cuoi(tmp_path):
    f = ghi_log(tmp_path / "a.log", [("Core 1", "dong %d" % i) for i in range(20)])
    d = CDT.doc_duoi(f, so_dong=3)
    assert d == ["12:00:17 Core 1 dong 17", "12:00:18 Core 1 dong 18", "12:00:19 Core 1 dong 19"]


def test_doc_duoi_utf8_va_file_rong_va_khong_ton_tai(tmp_path):
    f = ghi_log(tmp_path / "b.log", [("Tester", "xin chao")], utf16=False)
    assert CDT.doc_duoi(f) == ["12:00:00 Tester xin chao"]
    (tmp_path / "rong.log").write_bytes(b"")
    assert CDT.doc_duoi(tmp_path / "rong.log") == []
    assert CDT.doc_duoi(tmp_path / "khong_co.log") == []                 # khong nem


def test_doc_duoi_chi_doc_duoi_file_lon_va_khong_cat_doi_cap_byte_utf16(tmp_path):
    """LOI CO Y: doc ca file (cham/het RAM voi log agent hang chuc MB) hoac bat dau o byte LE trong UTF-16 (ra rac)."""
    n = 40_000
    f = ghi_log(tmp_path / "lon.log", [("Core 1", "dong so %d" % i) for i in range(n)])
    assert f.stat().st_size > 5 * CDT.DOC_TOI_DA_BYTE
    for gioi_han in (CDT.DOC_TOI_DA_BYTE, CDT.DOC_TOI_DA_BYTE + 1, 4097, 4098):           # ca bien chan lan le
        d = CDT.doc_duoi(f, so_dong=2, toi_da_byte=gioi_han)
        assert d[-1].endswith("dong so %d" % (n - 1)), (gioi_han, d)
        assert all("\x00" not in x and "�" not in x for x in d)
        # doc DUNG phan duoi: van ban tra ve khong dai hon `gioi_han` byte UTF-16 (= gioi_han // 2 ky tu) - khong phai ca file
        assert len(CDT.doc_text(f, toi_da_byte=gioi_han)) <= gioi_han // 2 + 1, gioi_han


def test_chuan_hoa_che_so_tai_khoan_va_ip_nhung_giu_localhost(tmp_path):
    """Repo PUBLIC: so tai khoan va IP may chu khong duoc di vao ket qua."""
    f = ghi_log(tmp_path / "t.log", [("Network", "'12345678': authorization on XMGlobal-MT5 10 failed via 185.12.34.56"),
                                     ("Core 1", "connecting to 127.0.0.1:3000"), ("Network", "login 87654321 ok")])
    d = " ".join(CDT.doc_duoi(f))
    assert "12345678" not in d and "185.12.34.56" not in d and "87654321" not in d
    assert "<tk>" in d and "<ip>" in d and "127.0.0.1:3000" in d and "authorization on XMGlobal-MT5 10 failed" in d


# ------------------------------------------------------------------ 2. tim log dung slot
def test_thu_muc_log_hai_kieu_bo_cuc_va_chi_thu_muc_co_that(cay):
    ghi_log(cay.dl / "logs" / "20261008.log", [("Terminal", "x")])
    ghi_log(cay.tester / "Agent-127.0.0.1-3000" / "logs" / "20261008.log", [("Core 1", "y")])
    ghi_log(cay.dl / "Tester" / "Agent-127.0.0.1-3001" / "logs" / "20261008.log", [("Core 1", "z")])         # portable
    loai = [k for k, _ in CDT.thu_muc_log(cay.dl, cay.home)]
    assert "terminal" in loai and "agent:a3000" in loai and "agent:a3001" in loai
    assert "ea" not in loai and "tester" not in loai                    # khong co thu muc thi khong liet ke


def test_thu_thap_khong_lay_log_cua_slot_khac_va_bo_log_cu(cay):
    """LOI CO Y: lay 'file log moi nhat cua ca may' (nhu truoc) - log cua slot khac / lan chay truoc se bi gan cho lan nay."""
    bat_dau = time.time()
    khac = cay.tmp / "Terminal" / "SLOTKHAC999999"
    ghi_log(cay.home / "AppData" / "Roaming" / "MetaQuotes" / "Tester" / khac.name / "Agent-127.0.0.1-3000" / "logs" / "a.log",
            [("Core 1", "connection closed cua SLOT KHAC")], mtime=bat_dau + 5)
    ghi_log(cay.tester / "Agent-127.0.0.1-3000" / "logs" / "cu.log", [("Core 1", "no history data lan truoc")], mtime=bat_dau - 3600)
    ghi_log(cay.dl / "logs" / "20261008.log", [("Terminal", "terminal moi"), ("Terminal", "authorized on XMGlobal-MT5 10")],
            mtime=bat_dau + 2)
    cd = CDT.thu_thap(cay.dl, bat_dau, home=cay.home)
    noi_dung = " ".join(" ".join(x["dong"]) for x in cd["log"])
    assert "SLOT KHAC" not in noi_dung and "lan truoc" not in noi_dung
    assert "terminal moi" in noi_dung and cd["cu"] == ["agent:a3000"] and cd["nhan"] is None


def test_thu_thap_nhan_dau_vet_va_dong_goc_di_kem(cay):
    bat_dau = time.time()
    ghi_log(cay.tester / "Agent-127.0.0.1-3000" / "logs" / "20261008.log",
            [("Core 1", "connecting to 127.0.0.1:3000"), ("Core 1", "AUDCAD: no history data for 2019.03.01"),
             ("Core 1", "tester stopped")], mtime=bat_dau + 1)
    cd = CDT.thu_thap(cay.dl, bat_dau, ma="AUDCAD", tu="2019.03.01", den="2019.08.31", home=cay.home, giay=94.2)
    assert cd["nhan"] == "thieu_lich_su" and "no history data" in cd["dong_chinh"]
    ts = CDT.tom_tat(cd, ten_slot="s1")
    assert ts.startswith("tester khong ra bao cao sau 94s [tester:thieu_lich_su] ") and "no history data" in ts


@pytest.mark.parametrize("dong,nhan", [
    ("Network 'x': authorization on XMGlobal-MT5 10 failed (Invalid account)", "chua_dang_nhap"),
    ("Network connection closed", "mat_ket_noi"),
    ("Tester terminal is not synchronized with the trade server", "mat_ket_noi"),
    ("Core 1 EURCAD: no history data", "thieu_lich_su"),
    ("Core 1 0 ticks, 0 bars generated", "thieu_lich_su"),
    ("Core 1 cannot load Experts\\_tu_dong\\x.ex5 [2]", "khong_nap_ea"),
    ("Core 1 OnInit returned non-zero code 1", "ea_tu_choi"),
    ("Core 1 not enough memory", "het_bo_nho"),
    ("Core 1 test passed in 0:00:05.123", None),
    ("Core 1 final balance 10234.50 USD", None),
])
def test_nhan_dau_vet_bieu_thuc(dong, nhan):
    r = CDT.nhan_dau_vet(["12:00:00 " + dong])
    assert (r[0] if r else None) == nhan


def test_moi_nhan_log_deu_co_hang_o_cau_loi_va_di_het_duong_ly_do():
    """Hai noi giu danh sach nhan (`NHAN_LOG` o day, `DAU_VET` o `qwen/cau_loi.py`): them nhan o mot noi ma quen noi kia thi don
    do mang nhan la nhung bi xep vao 'tester_khong_ra' chung (mat thong tin) - bat o day."""
    from qwen import cau_loi as CL
    hang = {n: g for n, g, _ in CL.DAU_VET}
    for nhan, _ in CDT.NHAN_LOG:
        assert hang.get("tester_" + nhan) == "can_chan_doan", nhan
    # va dung ca duong: dong `tom_tat` that -> `ly_do` -> dong in ra cua `b nc cc` -> cau_loi.dau_vet
    cd = {"nhan": "mat_ket_noi", "dong_chinh": "12:00:00 Network connection closed", "giay": 94.0, "ma": "AUDCAD",
          "slot": {"include_trade": True, "lich_su_m1": {"co_thu_muc": True, "nam": {"2019": None}, "tep_mau": []},
                   "dang_nhap": None},
          "log": [{"loai": "agent:a3000", "tep": "a.log", "dong": ["x"]}], "cu": [], "tien_do": None}
    dong_in = '{"loi": "tester khong ra ket qua: %s"}' % CDT.tom_tat(cd, ten_slot="s1")
    r = CL.dau_vet([dong_in])
    assert r["nhan"] == "tester_mat_ket_noi" and "[tester:mat_ket_noi]" in r["bang_chung"]


def test_nhan_dau_vet_lay_nhan_nghiem_trong_nhat_khong_phai_dong_cuoi():
    """Dang nhap hong nang hon mat ket noi (mat dang nhap => moi thu sau do la he qua)."""
    r = CDT.nhan_dau_vet(["connection closed", "authorization on X failed", "tester stopped"])
    assert r[0] == "chua_dang_nhap" and "authorization" in r[1]
    # cung nhan: lay dong CUOI (dong gan thoi diem chet nhat)
    r2 = CDT.nhan_dau_vet(["connection closed lan 1", "OK", "connection closed lan 2"])
    assert r2 == ("mat_ket_noi", "connection closed lan 2")


# ------------------------------------------------------------------ 3. kiem slot + tien do
def test_kiem_slot_thieu_include_va_lich_su_theo_nam(cay):
    his = cay.dl / "bases" / "XMGlobal-MT5 10" / "history" / "EURCAD"
    his.mkdir(parents=True)
    (his / "2019.hcc").write_bytes(b"0" * (3 * 1024 * 1024))
    (cay.dl / "MQL5" / "Include" / "Trade" / "Trade.mqh").unlink()
    r = CDT.kiem_slot(cay.dl, "EURCAD", "2018.07.01", "2019.12.31")
    assert r["include_trade"] is False
    assert r["lich_su_m1"]["co_thu_muc"] is True and r["lich_su_m1"]["nam"] == {"2018": None, "2019": 3.0}
    r2 = CDT.kiem_slot(cay.dl, "AUDCAD", "2019.03.01", "2019.08.31")
    assert r2["lich_su_m1"]["co_thu_muc"] is False and r2["lich_su_m1"]["nam"] == {"2019": None}


def test_kiem_slot_dang_nhap_lay_dong_cuoi_va_ma_la_ky_tu_la_thi_khong_glob(cay):
    ghi_log(cay.dl / "logs" / "20261008.log", [("Network", "authorized on XMGlobal-MT5 10 through Access Server"),
                                               ("Terminal", "dong khac"), ("Network", "disconnected")])
    assert CDT.kiem_slot(cay.dl)["dang_nhap"].endswith("disconnected")
    assert CDT.kiem_slot(cay.dl, "../../etc/*", "2019.01.01", "2019.02.01")["lich_su_m1"] is None     # khong glob ma la


def test_tien_do_lay_ngay_mo_phong_cuoi_va_phan_tram():
    dong = ["12:00:00 Core 1 2019.03.01 00:05:00 LuoiDayDu mo lenh", "12:00:05 Core 1 2019.05.31 10:00:00 chot"]
    r = CDT.tien_do(dong, "2019.03.01", "2019.08.31")
    assert r["ngay_mo_phong_cuoi"] == "2019.05.31" and 40 <= r["phan_tram"] <= 60
    assert CDT.tien_do(["12:00:00 Core 1 khong co moc"], "2019.03.01", "2019.08.31") is None
    assert CDT.tien_do(dong, "khong phai ngay", None)["ngay_mo_phong_cuoi"] == "2019.05.31"        # thieu cua so: van cho ngay


def test_tom_tat_ngan_nhan_o_dau_va_khong_nem_khi_chan_doan_trong():
    assert CDT.tom_tat({}) == "tester khong ra bao cao"
    cd = {"nhan": "mat_ket_noi", "dong_chinh": "12:00:00 Network " + "x" * 400, "giay": 95.0, "ma": "AUDCAD",
          "slot": {"include_trade": False, "lich_su_m1": {"co_thu_muc": True, "nam": {"2019": None}, "tep_mau": []},
                   "dang_nhap": "12:00:00 Network disconnected " + "y" * 400},
          "log": [{"loai": "agent:a%d" % (3000 + i), "tep": "a.log", "dong": ["a"] * 6} for i in range(25)],
          "cu": [], "tien_do": None}
    t = CDT.tom_tat(cd, ten_slot="m1")
    assert len(t) == CDT.TOI_DA_KY_TU_TOM_TAT                                   # dau vao dai hon nhieu -> bi cat dung 700
    assert t.startswith("tester khong ra bao cao sau 95s [tester:mat_ket_noi] 12:00:00 Network ")       # cat o CUOI, nhan o DAU
    assert t.count("x") <= CDT.TOI_DA_KY_TU_DONG                               # dong chinh bi cat o 170 ky tu


def test_thu_thap_khong_bao_gio_nem_ke_ca_khi_thu_muc_khong_ton_tai(tmp_path):
    cd = CDT.thu_thap(tmp_path / "khong" / "co", time.time(), ma="AUDCAD", tu="2019.01.01", den="2019.02.01", home=tmp_path)
    assert cd["log"] == [] and cd["nhan"] is None
    assert "khong thay thu muc log" in CDT.tom_tat(cd)


def test_thu_thap_khong_nem_ke_ca_khi_ben_trong_hong(tmp_path, monkeypatch):
    """LOI CO Y: `except` hep (chi bat OSError) - mot loi la o buoc kiem slot se lam `ea_tho` mat ly do tester thay bang traceback."""
    def no(*a, **k):
        raise RuntimeError("kiem slot no")
    monkeypatch.setattr(CDT, "kiem_slot", no)
    cd = CDT.thu_thap(tmp_path, time.time(), ma="AUDCAD", home=tmp_path)
    assert cd["loi_chan_doan"] == "RuntimeError: kiem slot no"
    assert "chan doan loi: RuntimeError: kiem slot no" in CDT.tom_tat(cd)


def test_ghi_chi_tiet_ghi_json_day_du_va_loi_ghi_khong_nem(tmp_path):
    ten = CDT.ghi_chi_tiet({"nhan": "x", "log": []}, tmp_path / "cd", "s1")
    assert ten and (tmp_path / "cd" / ten).is_file() and ten.endswith("_s1.json")
    (tmp_path / "chan").write_text("la mot file", encoding="utf-8")
    assert CDT.ghi_chi_tiet({}, tmp_path / "chan" / "con", "s1") is None


def test_log_agent_slot_chi_lay_log_agent_moi_cua_dung_slot(cay):
    bat_dau = time.time()
    ghi_log(cay.tester / "Agent-127.0.0.1-3000" / "logs" / "a.log", [("Core 1", "MetaTester 5 started"), ("Core 1", "no history data")],
            mtime=bat_dau + 1)
    ghi_log(cay.dl / "logs" / "t.log", [("Terminal", "khong phai agent")], mtime=bat_dau + 50)       # MOI HON log agent
    van = CDT.log_agent_slot(cay.dl, bat_dau, home=cay.home)
    assert "no history data" in van and "khong phai agent" not in van
    assert CDT.log_agent_slot(cay.dl, bat_dau + 100, home=cay.home) == ""        # log cu hon luc chay -> khong lay


# ------------------------------------------------------------------ 4. NOI VAO ea_tho._chay_voi_slot
class SlotGia:
    def __init__(self, dl: Path):
        self.dl = dl

    @contextlib.contextmanager
    def cap(self, ten):
        yield types.SimpleNamespace(ten="s1", exe=self.dl.parent / "cai" / "terminal64.exe", du_lieu=self.dl)


@pytest.fixture
def moi_truong(cay, monkeypatch):
    monkeypatch.setattr(EA, "TERMINAL", dict(EA.TERMINAL))
    monkeypatch.setattr(E, "THU_MUC_CHAN_DOAN", cay.tmp / "chan_doan")
    monkeypatch.setattr(Path, "home", classmethod(lambda c: cay.home))
    return types.SimpleNamespace(slot=SlotGia(cay.dl), cay=cay)


def _lenh_ea():
    lenh = {"van_tay": "vt123", "viec": {"nhan": "n1", "symbol": "AUDCAD", "khung": "M5", "tu": "2019.03.01",
                                          "den": "2019.08.31", "model": 0, "han_giay": 900}}
    ea = {"nhi_phan": False, "ten": "ea", "ma": "//", "url": ""}
    return lenh, ea


def test_chay_voi_slot_tester_hong_mang_bang_chung_dung_slot_va_ghi_file(moi_truong, monkeypatch):
    cay = moi_truong.cay

    def chay_mot(viec):
        ghi_log(cay.tester / "Agent-127.0.0.1-3000" / "logs" / "20261008.log",
                [("Core 1", "AUDCAD: no history data for 2019.03.01")])
        return {"xong": False, "bao_cao": "", "giay": 93.0}
    monkeypatch.setattr(EA, "chay_mot", chay_mot)
    monkeypatch.setattr(EA, "bien_dich", lambda ds, t, cho_giay=12.0: [{"bien_dich": True, "ten_file": "ea_x", "loi": ""}])
    lenh, ea = _lenh_ea()
    r = E._chay_voi_slot(lenh, ea, E.cau_hinh(), EA, moi_truong.slot)
    assert r["xong"] is False
    assert "tester khong ra bao cao sau 93s [tester:thieu_lich_su]" in r["loi"] and "no history data" in r["loi"]
    assert "chi tiet: reports/chan_doan_tester/" in r["loi"]
    assert len(list((cay.tmp / "chan_doan").glob("*_s1.json"))) == 1
    assert "no history data" in r["log"]                                                # log cua dung slot, cho nhan_ket_qua dung


def test_chay_voi_slot_tester_hong_nhung_khong_co_log_van_noi_ro_dieu_do(moi_truong, monkeypatch):
    monkeypatch.setattr(EA, "chay_mot", lambda viec: {"xong": False, "bao_cao": "", "giay": 91.0})
    monkeypatch.setattr(EA, "bien_dich", lambda ds, t, cho_giay=12.0: [{"bien_dich": True, "ten_file": "ea_x", "loi": ""}])
    lenh, ea = _lenh_ea()
    r = E._chay_voi_slot(lenh, ea, E.cau_hinh(), EA, moi_truong.slot)
    assert r["xong"] is False and r["loi"].startswith("tester khong ra bao cao sau 91s")
    assert "khong thay thu muc log nao cua slot" in r["loi"] and "KHONG co thu muc" in r["loi"]       # lich su AUDCAD khong co


def test_chay_voi_slot_thanh_cong_khong_goi_chan_doan_va_khong_ghi_file(moi_truong, monkeypatch):
    """LOI CO Y: chan doan cung chay khi thanh cong (ghi file moi lan chay -> day dia, cham)."""
    monkeypatch.setattr(EA, "chay_mot", lambda viec: {"xong": True, "bao_cao": "bc.htm", "giay": 5.0})
    monkeypatch.setattr(EA, "bien_dich", lambda ds, t, cho_giay=12.0: [{"bien_dich": True, "ten_file": "ea_x", "loi": ""}])
    goi = []
    monkeypatch.setattr(CDT, "thu_thap", lambda *a, **k: goi.append(1))
    lenh, ea = _lenh_ea()
    r = E._chay_voi_slot(lenh, ea, E.cau_hinh(), EA, moi_truong.slot)
    assert r["xong"] is True and r["loi"] == "" and goi == []
    assert not (moi_truong.cay.tmp / "chan_doan").exists()


def test_chay_voi_slot_bo_qua_do_dia_giu_nguyen_ly_do_khong_chan_doan(moi_truong, monkeypatch):
    monkeypatch.setattr(EA, "chay_mot", lambda viec: {"xong": False, "bao_cao": "", "giay": 0.0, "bo_qua": "dia con 3.5 GB < 15.0"})
    monkeypatch.setattr(EA, "bien_dich", lambda ds, t, cho_giay=12.0: [{"bien_dich": True, "ten_file": "ea_x", "loi": ""}])
    lenh, ea = _lenh_ea()
    assert E._chay_voi_slot(lenh, ea, E.cau_hinh(), EA, moi_truong.slot)["loi"] == "dia con 3.5 GB < 15.0"


def test_chay_voi_slot_chan_doan_no_cung_khong_lam_hong_ket_qua(moi_truong, monkeypatch):
    """LOI CO Y: de loi chan doan lan ra ngoai (tester da hong, chan doan khong duoc lam no hong kieu khac)."""
    monkeypatch.setattr(EA, "chay_mot", lambda viec: {"xong": False, "bao_cao": "", "giay": 93.0})
    monkeypatch.setattr(EA, "bien_dich", lambda ds, t, cho_giay=12.0: [{"bien_dich": True, "ten_file": "ea_x", "loi": ""}])

    def no(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(CDT, "thu_thap", no)
    lenh, ea = _lenh_ea()
    r = E._chay_voi_slot(lenh, ea, E.cau_hinh(), EA, moi_truong.slot)
    assert r["xong"] is False and r["loi"].startswith("tester khong ra bao cao") and "boom" in r["loi"]


def test_chay_voi_slot_bien_dich_hong_noi_ro_thieu_include(moi_truong, monkeypatch):
    (moi_truong.cay.dl / "MQL5" / "Include" / "Trade" / "Trade.mqh").unlink()
    monkeypatch.setattr(EA, "bien_dich", lambda ds, t, cho_giay=12.0: [{"bien_dich": False, "ten_file": "",
                                                                         "loi": "ea.mq5 : error 106: file 'Include\\Trade\\Trade.mqh' not found"}])
    lenh, ea = _lenh_ea()
    r = E._chay_voi_slot(lenh, ea, E.cau_hinh(), EA, moi_truong.slot)
    assert r["xong"] is False and r["loi"].startswith("bien dich hong: ea.mq5 : error 106") and "Trade.mqh=THIEU" in r["loi"]
    # MetaEditor khong ghi dong loi nao (het 90 giay): phai noi ra chu khong de 'bien dich hong: ' tron
    monkeypatch.setattr(EA, "bien_dich", lambda ds, t, cho_giay=12.0: [{"bien_dich": False, "ten_file": "", "loi": ""}])
    r2 = E._chay_voi_slot(lenh, ea, E.cau_hinh(), EA, moi_truong.slot)
    assert "khong co dong loi trong log bien dich" in r2["loi"]


def test_ly_do_di_het_qua_chay_va_nua_tester(moi_truong, monkeypatch):
    """`chay()` va `hieu_chuan_luoi.nua_tester` ghep `r['loi']` vao `ly_do`: phai mang NGUYEN bang chung (khong cat)."""
    from nhan import hieu_chuan_luoi as HC
    dai = "tester khong ra bao cao sau 93s [tester:mat_ket_noi] 12:00:00 Network connection closed | slot s1 Trade.mqh=co"
    monkeypatch.setattr(E, "CHAY_TESTER", lambda lenh, d, cfg: {"xong": False, "loi": dai})
    r = HC.nua_tester({"lenh": {"cua_so": {"tu": "2019.03.01", "den": "2019.08.31"}}}, {}, {}, None, 1000, "vt", None, False, 1.0)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and dai in r["ly_do"]
