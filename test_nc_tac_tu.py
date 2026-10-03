# -*- coding: utf-8 -*-
"""Vong tac tu cua NHA NGHIEN CUU chay dung KHONG can API that (client gia lap).

Kiem ba dieu ma mot vong tu chu hay hong ma khong ai bao:
  1. tool_result phai tra DUNG id, gop MOT tin nhan, va cong cu that duoc goi;
  2. ngan sach chu ky phai chan duoc AI (het ngan sach -> chi con ghi so -> buoc ket);
  3. mo hinh tu choi / cat max_tokens KHONG duoc chay cong cu voi dau vao do.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from nhan import nc_so_tay as ST
from nhan import nc_tac_tu as TT


@pytest.fixture(autouse=True)
def so_tam(tmp_path, monkeypatch):
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    monkeypatch.setattr(TT, "THU_MUC_VONG", tmp_path / "nc_vong")
    monkeypatch.setattr(TT, "CO_DUNG", tmp_path / "DUNG_LAI")
    yield


class _K:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _U:
    input_tokens = 2000
    output_tokens = 300
    cache_creation_input_tokens = 0
    cache_read_input_tokens = 1000


def _resp(noi_dung, dung):
    return _K(content=noi_dung, stop_reason=dung, usage=_U(), stop_details=None)


def _tool(i, ten, dv):
    return _K(type="tool_use", id=i, name=ten, input=dv)


def _text(t):
    return _K(type="text", text=t)


class _Msgs:
    def __init__(self, kich_ban):
        self.kich_ban = list(kich_ban)
        self.goi = []

    def create(self, **kw):
        self.goi.append(kw)
        return self.kich_ban.pop(0)(kw)


class _Client:
    def __init__(self, kich_ban):
        self.beta = _K(messages=_Msgs(kich_ban))


SPEC = {"ten": "ibs_day_bd_cao", "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 1,
        "co_che": "Ban thao cuoi bar trong bien dong cao day gia qua sau; nguoi cung cap "
                  "thanh khoan duoc tra cu hoi.",
        "vao": [{"trai": {"chi_bao": "ibs"}, "phep": "<", "phai": {"hang": 0.15}},
                {"trai": {"chi_bao": "phan_vi", "cua": {"chi_bao": "atr", "n": 14}, "n": 250},
                 "phep": ">", "phai": {"hang": 0.65}}]}
C = dict(TT.MAC_DINH, cong_cu_moi_vong=5, usd_moi_vong=100.0, usd_moi_ngay=1000.0)


def test_mot_chu_ky_goi_cong_cu_that_va_ghi_so():
    def r1(kw):
        assert "NHA NGHIEN CUU CHINH" in kw["system"][0]["text"]
        assert kw["extra_body"]["fallbacks"] == "default"
        assert TT.BETA_FALLBACK in kw["betas"]
        assert {t["name"] for t in kw["tools"]} >= {"thu_co_che", "mo_xe_lenh", "niem_phong"}
        return _resp([_text("doc so tay roi thu IBS"), _tool("a1", "xem_so_tay", {}),
                      _tool("a2", "thu_co_che", {"ma": "TONG_HOP_HOI_QUY_1", "khung": "H4",
                                                 "spec": SPEC})], "tool_use")

    def r2(kw):
        ket = kw["messages"][-1]["content"]
        ids = [k["tool_use_id"] for k in ket if k.get("type") == "tool_result"]
        assert ids == ["a1", "a2"], "moi tool_use phai co tool_result cung id, cung mot tin"
        kq = json.loads(ket[1]["content"])
        assert kq["trang_thai"] in ("DAT", "AM") and kq["lenh"]["so_lenh"] > 0
        return _resp([_text("Tom tat: IBS day khi bien dong cao DAT tren kham pha.")], "end_turn")

    cl = _Client([r1, r2])
    r = TT.chay_vong(client=cl, c=C)
    assert r["trang_thai"] == "XONG"
    assert r["so_cong_cu"] == 1, "xem_so_tay la cong cu GHI, khong tinh vao ngan sach do"
    assert r["usd"] > 0
    v = ST.mot("SELECT * FROM vong WHERE id=?", r["vong_id"])
    assert v["trang_thai"] == "XONG" and "IBS" in v["tom_tat"]
    tn = ST.nhieu("SELECT * FROM thi_nghiem WHERE vong_id=?", r["vong_id"])
    assert len(tn) == 1 and tn[0]["loai"] == "thu_co_che"
    assert Path(TT.THU_MUC_VONG / ("vong_%05d.md" % r["vong_id"])).exists()


def test_het_ngan_sach_chi_con_ghi_so_roi_buoc_ket():
    spec2 = dict(SPEC, ten="ibs_day_2", vao=[SPEC["vao"][0]])

    def r1(kw):
        return _resp([_tool("b1", "thu_co_che", {"ma": "TONG_HOP_HOI_QUY_1", "khung": "H4", "spec": SPEC}),
                      _tool("b2", "thu_co_che", {"ma": "TONG_HOP_HOI_QUY_1", "khung": "H4", "spec": spec2})],
                     "tool_use")

    def r2(kw):
        ket = kw["messages"][-1]["content"]
        loi = [k for k in ket if k.get("type") == "tool_result" and k.get("is_error")]
        assert len(loi) == 1 and "het ngan sach" in loi[0]["content"]
        assert any(k.get("type") == "text" and "Het ngan sach" in k["text"] for k in ket)
        assert "tool_choice" not in kw
        return _resp([_tool("b3", "thu_co_che", {"ma": "TONG_HOP_HOI_QUY_1", "khung": "H4",
                                                 "spec": dict(SPEC, ten="x3", giu=2)})], "tool_use")

    def r3(kw):
        assert kw.get("tool_choice") == {"type": "none"}, "van goi cong cu do sau khi bao het -> cam"
        return _resp([_text("Tom tat: het ngan sach.")], "end_turn")

    cl = _Client([r1, r2, r3])
    r = TT.chay_vong(client=cl, c=dict(C, cong_cu_moi_vong=1))
    assert r["trang_thai"] == "XONG" and r["so_cong_cu"] == 1


def test_tu_choi_va_cat_max_tokens_khong_chay_cong_cu():
    cl = _Client([lambda kw: _resp([], "refusal")])
    r = TT.chay_vong(client=cl, c=C)
    assert r["trang_thai"] == "TU_CHOI"
    assert ST.mot("SELECT COUNT(*) n FROM thi_nghiem")["n"] == 0

    def m1(kw):
        return _resp([_tool("c1", "thu_co_che", {"ma": "TONG_HOP_HOI_QUY_1", "khung": "H4",
                                                 "spec": SPEC})], "max_tokens")

    def m2(kw):
        k = kw["messages"][-1]["content"][0]
        assert k["is_error"] and "max_tokens" in k["content"]
        return _resp([_text("xong")], "end_turn")

    r = TT.chay_vong(client=_Client([m1, m2]), c=C)
    assert r["so_cong_cu"] == 0
    assert ST.mot("SELECT COUNT(*) n FROM thi_nghiem")["n"] == 0


def test_co_dung_va_ngan_sach_ngay_chan_truoc_khi_goi_api(tmp_path):
    (TT.CO_DUNG).write_text("x")
    assert TT.chay_vong(client=_Client([]), c=C)["trang_thai"] == "DUNG"
    TT.CO_DUNG.unlink()
    v = ST.bat_dau_vong("claude_api", "m")
    ST.ket_thuc_vong(v, "t", usd=5.0)
    r = TT.chay_vong(client=_Client([]), c=dict(C, usd_moi_ngay=4.0))
    assert r["trang_thai"] == "HET_NGAN_SACH"


def test_hien_chuong_on_dinh_va_noi_du_luat_chinh():
    a = TT.HIEN_CHUONG
    import importlib
    b = importlib.reload(TT).HIEN_CHUONG
    assert a == b, "hien chuong phai TAT DINH - thay doi tung byte la mat cache prompt"
    for cum in ("LUAT SO 0", "CAGR", "maxdd duoi 80%", "martingale", "DON BAY", "niem_phong",
                "CHUA_DO_DUOC", "QUAN LI LENH", "TONG_HOP", "p_null", "vao", "atr_pv"):
        assert cum in a, cum


def test_lenh_claude_code_chi_mo_quyen_cong_cu_nghien_cuu():
    lenh = TT.lenh_claude_code(7, dict(C, claude_code_lenh="claude"))
    s = " ".join(lenh)
    assert "-p" in lenh and "--allowedTools" in lenh
    assert "Bash(python b.py nc:*)" in lenh
    assert not any(x.startswith("Bash(") and "nc" not in x for x in lenh), \
        "Claude Code headless chi duoc chay lenh `b nc ...`"
    assert "#7" in s and "NHA NGHIEN CUU CHINH" in s
