# -*- coding: utf-8 -*-
"""Ban giao LLM (thu nha c91d, 03/10/2026): DeepSeek flash mac dinh, Qwen3.8 max du phong sau 2 lan sai.

Kiem phan `qwen/` (khong goi mang, khong doc khoa that): thu tu model, ke hoach thu, duong khoa (env truoc cc-switch,
KHONG lo khoa), tac tu `hoi` doi model dung luc, va ghim quyet dinh trong config. Phan `b nc tho` o test_nc_tho.py,
phan `b so-sanh` o test_so_sanh_llm.py.
"""
from __future__ import annotations

import json
import re
import sqlite3

import pytest

from qwen import cau_hinh as CH
from qwen import cau_trang as CT
from qwen import mo_hinh as MH
from qwen import tac_tu as TT

CFG = {"model": "a", "model_du_phong": "b", "leo_thang_sau_lan_sai": 2}


@pytest.fixture
def khong_khoa_that(tmp_path, monkeypatch):
    """Khong env, khong cc-switch cua may dang chay test."""
    monkeypatch.delenv("AIBOX_API_KEY", raising=False)
    monkeypatch.setattr(MH, "CC_SWITCH_DB", tmp_path / "khong_co.db")
    return tmp_path


class TestQuyetDinhTrongConfig:
    def test_ghim_quyet_dinh_thu_c91d(self):
        c = CH.nap()
        assert c["model"] == "ds/deepseek-flash" and c["model_du_phong"] == "qwen3.8-max-0902"
        assert c["leo_thang_sau_lan_sai"] == 2
        assert c["base_url"] == "https://api.ai-box.vn/v1"

    def test_mac_dinh_trong_code_khop_config_de_mat_config_van_dung(self):
        m = CH.MAC_DINH
        assert (m["model"], m["model_du_phong"], m["leo_thang_sau_lan_sai"]) == ("ds/deepseek-flash", "qwen3.8-max-0902", 2)

    def test_config_json_con_hop_le_va_khong_chua_khoa(self):
        """Repo PUBLIC: config chi ghi TEN bien moi truong, khong bao gio gia tri khoa."""
        txt = (CH.LAB / "config" / "qwen.json").read_text(encoding="utf-8-sig")
        json.loads(txt)
        assert not re.search(r"sk-[A-Za-z0-9]{10,}", txt), "giong khoa OpenAI-kieu"
        assert not re.findall(r"[A-Za-z0-9]{32,}", txt), "chuoi dai khong khoang trang = nghi la khoa"


class TestKeHoachThu:
    def test_thu_tu_va_dao_khi_can_suy_luan_sau(self):
        assert MH.thu_tu_model(CFG) == ["a", "b"]
        assert MH.thu_tu_model(CFG, sau=True) == ["b", "a"]

    def test_bo_ten_rong_va_ten_trung(self):
        assert MH.thu_tu_model({"model": "a", "model_du_phong": "a"}) == ["a"]
        assert MH.thu_tu_model({"model": "a", "model_du_phong": ""}) == ["a"]
        assert MH.thu_tu_model({"model": "", "model_du_phong": ""}) == []

    def test_model_dau_thu_hai_lan_roi_moi_den_du_phong(self):
        assert MH.ke_hoach_thu(CFG) == ["a", "a", "b"]
        assert MH.ke_hoach_thu(CFG, sau=True) == ["b", "b", "a"]
        assert MH.ke_hoach_thu(dict(CFG, leo_thang_sau_lan_sai=1)) == ["a", "b"]
        assert MH.ke_hoach_thu(dict(CFG, leo_thang_sau_lan_sai=0)) == ["a", "a", "b"], "0 / thieu -> mac dinh 2, khong the vo han"
        assert MH.ke_hoach_thu({"model": "a", "model_du_phong": "a"}) == ["a", "a"]
        assert MH.ke_hoach_thu({"model": "", "model_du_phong": ""}) == []


class TestDuongKhoa:
    def test_env_thang_cc_switch_va_khoa_khong_ro_ri_ra_ket_qua_khac(self, khong_khoa_that, monkeypatch):
        monkeypatch.setenv("AIBOX_API_KEY", "sk-khong-that-123")
        d = MH.duong(CFG | {"cc_switch_provider": "aibox", "base_url": "https://x.example/v1"})
        assert d["khoa"] == "sk-khong-that-123" and d["base_url"] == "https://x.example/v1" and d["model"] == "a"
        assert d["nguon"] == "env:AIBOX_API_KEY" and "sk-khong" not in d["nguon"] + d["provider"]

    def test_cc_switch_khi_khong_co_env_va_thay_cau_noi_codex_bang_url_thang(self, khong_khoa_that, monkeypatch):
        db = khong_khoa_that / "cc.db"
        cn = sqlite3.connect(str(db))
        cn.execute("CREATE TABLE providers (name TEXT, settings_config TEXT)")
        cn.execute("INSERT INTO providers VALUES (?, ?)", ("AiBox goi moi", json.dumps(
            {"auth": {"OPENAI_API_KEY": "kk-cc"}, "config": 'base_url = "http://127.0.0.1:8317/v1"\nmodel = "gpt-codex"'})))
        cn.commit()
        cn.close()
        monkeypatch.setattr(MH, "CC_SWITCH_DB", db)
        d = MH.duong(CFG | {"cc_switch_provider": "aibox", "base_url": "https://api.ai-box.vn/v1"})
        assert d["khoa"] == "kk-cc" and d["base_url"] == "https://api.ai-box.vn/v1", "cau noi Codex khong phai duong cua LangChain"
        assert d["model"] == "a", "model o config THANG model cua cc-switch (cc-switch chi cho khoa)"
        assert d["nguon"] == "cc-switch:AiBox goi moi"

    def test_thieu_ca_hai_nguon_noi_ro_cach_sua(self, khong_khoa_that):
        with pytest.raises(SystemExit) as e:
            MH.duong(CFG | {"cc_switch_provider": "aibox", "base_url": "https://x/v1"})
        assert "AIBOX_API_KEY" in str(e.value) and "cc-switch" in str(e.value)


# ------------------------------------------------------------------ tac tu `hoi`
class _Tin:
    def __init__(self, content):
        self.content = content


class _Agent:
    def __init__(self, kich_ban, model, da_goi):
        self.kb, self.model, self.da_goi = kich_ban, model, da_goi

    def invoke(self, *_a, **_k):
        self.da_goi.append(self.model)
        x = self.kb.pop(0)
        if isinstance(x, Exception):
            raise x
        return {"messages": [_Tin(x)]}


@pytest.fixture
def tac_tu_gia(monkeypatch):
    monkeypatch.setattr(CH, "nap", lambda: dict(CFG))

    def dung(kich_ban):
        da_goi = []
        monkeypatch.setattr(TT, "_tac_tu", lambda cong_cu=None, model=None: _Agent(kich_ban, model, da_goi))
        return da_goi
    return dung


class TestHoiLeoThang:
    def test_thanh_cong_lan_dau_khong_dong_den_model_du_phong(self, tac_tu_gia, capsys):
        da_goi = tac_tu_gia(["Xong."])
        assert TT.hoi("x") == "Xong." and da_goi == ["a"]
        assert capsys.readouterr().err == ""

    def test_mot_loi_le_te_khong_doi_model(self, tac_tu_gia):
        da_goi = tac_tu_gia([RuntimeError("mang chap chon"), "Xong."])
        assert TT.hoi("x") == "Xong." and da_goi == ["a", "a"]

    def test_sai_hai_lan_lien_tiep_thi_doi_model_va_bao_ra_stderr(self, tac_tu_gia, capsys):
        da_goi = tac_tu_gia([RuntimeError("HTTP 500"), RuntimeError("HTTP 500"), "Xong bang model du phong."])
        assert TT.hoi("x") == "Xong bang model du phong." and da_goi == ["a", "a", "b"]
        assert "a sai 2 lan lien tiep -> doi sang b" in capsys.readouterr().err

    def test_tra_rong_tinh_la_sai(self, tac_tu_gia):
        da_goi = tac_tu_gia(["", "  ", "Co chu."])
        assert TT.hoi("x") == "Co chu." and da_goi == ["a", "a", "b"]

    def test_viec_sau_di_thang_model_du_phong(self, tac_tu_gia):
        da_goi = tac_tu_gia(["Suy luan sau xong."])
        assert TT.hoi("x", sau=True) == "Suy luan sau xong." and da_goi == ["b"]

    def test_hong_het_thi_tra_chuoi_loi_ro_ca_hai_model_chu_khong_nem(self, tac_tu_gia):
        da_goi = tac_tu_gia([RuntimeError("1"), RuntimeError("2"), ValueError("3")])
        r = TT.hoi("x")
        assert r.startswith("!! tac tu loi:") and da_goi == ["a", "a", "b"]
        assert "a: RuntimeError" in r and "b: ValueError" in r

    def test_content_dang_danh_sach_khoi_van_doc_duoc(self, tac_tu_gia):
        da_goi = tac_tu_gia([[{"type": "text", "text": "Mot "}, {"type": "text", "text": "hai."}]])
        assert TT.hoi("x") == "Mot hai." and da_goi == ["a"], "khong duoc coi la loi roi doi model dat tien"


class TestDanhSachTrang:
    def test_nc_tho_nhan_co_sau_va_van_chan_co_la(self):
        goc = ["{py}", "b.py", "nc", "tho"]
        assert CT.kiem_lenh(goc + ["--vong", "1", "--cong-cu", "20", "--sau"]) is None
        assert CT.kiem_lenh(goc + ["--sau", "--sau"]) is not None, "co lap lai bi chan"
        assert CT.kiem_lenh(goc + ["--model", "x"]) is not None, "khong cho don hang doi model"
