# -*- coding: utf-8 -*-
"""Tho (model re): chi co cong cu kham pha, doan bi ep ve kham_pha, moi thu ghi mang nguon 'tho'."""
from __future__ import annotations

import json

import pytest

from nhan import nc_so_tay as ST
from nhan import nc_tho as THO
from qwen import mo_hinh as QM


@pytest.fixture(autouse=True)
def so_tam(tmp_path, monkeypatch):
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    monkeypatch.setattr(THO, "LAB", tmp_path)
    monkeypatch.setattr(THO, "_lan_sai_de_leo", lambda: 2)      # khong phu thuoc config that
    yield


def test_tho_khong_co_cong_cu_tieu_doan_quy():
    ten = {t["function"]["name"] for t in THO.cong_cu_openai()}
    assert ten == set(THO.CONG_CU_THO)
    assert not ten & {"xac_nhan", "niem_phong", "xuat_mq5"}


def test_vong_tho_ep_kham_pha_tu_choi_niem_phong_va_danh_dau_nguon():
    cau = [{"choices": [{"message": {"content": "", "tool_calls": [
        {"id": "a", "type": "function", "function": {"name": "ghi_gia_thuyet", "arguments": json.dumps(
            {"cau": "EURGBP H4 hoi quy sau cu soc 1 bar khi bien dong cao",
             "vi_sao": "thanh khoan cheo cap mong"})}},
        {"id": "b", "type": "function", "function": {"name": "niem_phong", "arguments": "{}"}},
        {"id": "c", "type": "function", "function": {"name": "thu_luoi", "arguments": json.dumps(
            {"ma": "TONG_HOP_NHIEU_1", "khung": "H1", "doan": "xac_nhan",
             "tham_so": {"buoc": 40, "tp": 30, "tran_tang": 6}})}}]}}],
            "usage": {"prompt_tokens": 1000, "completion_tokens": 50}},
           {"choices": [{"message": {"content": "Da thu luoi tren nhieu: khong co gi."}}],
            "usage": {"prompt_tokens": 1200, "completion_tokens": 20}}]
    goi_cuoi = []

    def goi(than):
        goi_cuoi.append(than)
        return cau.pop(0)
    r = THO.chay_vong(goi=goi, so_cong_cu=10)
    assert r["so_cong_cu"] == 3 and r["token_vao"] == 2200 and "khong co gi" in r["ket_luan"]
    tool = {m["tool_call_id"]: m["content"] for m in goi_cuoi[-1]["messages"] if m["role"] == "tool"}
    assert "tho khong co cong cu" in tool["b"]
    assert '"doan":"kham_pha"' in tool["c"], tool["c"][:200]
    assert ST.mot("SELECT nguon FROM gia_thuyet ORDER BY id DESC LIMIT 1")["nguon"] == "tho"


def test_duong_tu_bien_moi_truong(monkeypatch):
    monkeypatch.setenv("THO_KHOA_ENV", "KHOA_GIA")
    monkeypatch.setenv("KHOA_GIA", "sk-khong-that")
    d = THO.duong()
    assert d["url"] == "https://api.deepseek.com/chat/completions" and d["mo_hinh"] == "deepseek-chat"


# ------------------------------------------------------------------ leo thang model (thu nha c91d, 03/10/2026)
def _txt(t, vao=0, ra=0, finish="stop"):
    return {"choices": [{"message": {"content": t}, "finish_reason": finish}], "usage": {"prompt_tokens": vao, "completion_tokens": ra}}


def _rong(vao=0, ra=0):
    return _txt("", vao, ra, finish="length")


def _cc(*tens):
    return {"choices": [{"message": {"content": "", "tool_calls": [
        {"id": "t%d" % i, "type": "function", "function": {"name": n, "arguments": "{}"}} for i, n in enumerate(tens)]}}], "usage": {}}


def _kich_ban(*cau):
    """goi(than) gia: tra lan luot `cau` (ngoai le thi nem). Ghi model + so tin nhan luc GOI vao .model / .tin."""
    hang = list(cau)

    def goi(than):
        goi.model.append(than["model"])
        goi.tin.append(len(than["messages"]))
        x = hang.pop(0)
        if isinstance(x, Exception):
            raise x
        return x
    goi.model, goi.tin = [], []
    return goi


def _vong(vid):
    return ST.mot("SELECT mo_hinh, trang_thai, token_vao, token_ra, usd FROM vong WHERE id=?", vid)


class TestLeoThang:
    def test_sai_hai_lan_goi_lien_tiep_doi_sang_du_phong_giu_nguyen_lich_su(self):
        goi = _kich_ban(RuntimeError("HTTP 500"), RuntimeError("HTTP 500"), _txt("Xong bang du phong.", 10, 5))
        r = THO.chay_vong(goi=goi, so_cong_cu=5)
        assert goi.model == ["gia_lap", "gia_lap", "gia_lap_du_phong"]
        assert goi.tin == [2, 2, 2], "loi goi khong them tin nhan nao; doi model van gui dung lich su cu"
        assert r["ket_luan"] == "Xong bang du phong." and r["mo_hinh"] == "gia_lap" and r["mo_hinh_cuoi"] == "gia_lap_du_phong"
        (x,) = r["leo_thang"]
        assert (x["tu"], x["sang"], x["sau_cong_cu"]) == ("gia_lap", "gia_lap_du_phong", 0) and "HTTP 500" in x["ly_do"]
        v = _vong(r["vong_id"])
        assert v["mo_hinh"] == "gia_lap>gia_lap_du_phong" and v["trang_thai"] == "XONG"
        assert "DOI MODEL" in (THO.LAB / r["bao_cao"]).read_text(encoding="utf-8")

    def test_mot_loi_le_te_hoac_loi_khong_lien_tiep_khong_doi_model(self):
        goi = _kich_ban(RuntimeError("mang chap chon"), _cc("xem_so_tay"), RuntimeError("lai chap chon"), _txt("Xong."))
        r = THO.chay_vong(goi=goi, so_cong_cu=5)
        assert goi.model == ["gia_lap"] * 4 and r["leo_thang"] == [] and r["mo_hinh_cuoi"] == "gia_lap"
        assert _vong(r["vong_id"])["mo_hinh"] == "gia_lap"

    def test_tra_rong_tinh_la_sai_va_token_van_duoc_dem(self):
        goi = _kich_ban(_rong(100, 40), _rong(100, 40), _txt("Co chu.", 100, 10))
        r = THO.chay_vong(goi=goi, so_cong_cu=5)
        assert goi.model == ["gia_lap", "gia_lap", "gia_lap_du_phong"] and "finish=length" in r["leo_thang"][0]["ly_do"]
        assert (r["token_vao"], r["token_ra"]) == (300, 90), "luot tra rong van ton token that"

    def test_moi_cong_cu_bi_tu_choi_hai_luot_lien_tiep_cung_la_sai(self):
        goi = _kich_ban(_cc("xac_nhan", "niem_phong"), _cc("xuat_mq5"), _txt("Thoi."))
        r = THO.chay_vong(goi=goi, so_cong_cu=9)
        assert goi.model == ["gia_lap", "gia_lap", "gia_lap_du_phong"] and "bi tu choi" in r["leo_thang"][0]["ly_do"]
        assert r["so_cong_cu"] == 3 and r["leo_thang"][0]["sau_cong_cu"] == 3

    def test_doi_roi_ma_van_hong_hai_lan_thi_dong_vong_LOI_va_nem(self):
        goi = _kich_ban(*[RuntimeError("HTTP 503")] * 4, _txt("khong bao gio toi"))
        with pytest.raises(RuntimeError) as e:
            THO.chay_vong(goi=goi, so_cong_cu=5)
        assert goi.model == ["gia_lap", "gia_lap", "gia_lap_du_phong", "gia_lap_du_phong"], "doi DUNG MOT lan, khong quay lai"
        assert "da doi sang gia_lap_du_phong" in str(e.value) and "HTTP 503" in str(e.value)
        v = ST.mot("SELECT trang_thai, tom_tat FROM vong ORDER BY id DESC LIMIT 1")
        assert v["trang_thai"] == "LOI" and v["tom_tat"].startswith("!! DUNG")

    def test_sau_bat_dau_bang_model_du_phong_va_doi_nguoc_lai_khi_hong(self):
        goi = _kich_ban(_txt("Suy luan sau xong."))
        r = THO.chay_vong(goi=goi, so_cong_cu=5, sau=True)
        assert goi.model == ["gia_lap_du_phong"] and r["mo_hinh"] == "gia_lap_du_phong" and r["leo_thang"] == []
        goi = _kich_ban(RuntimeError("1"), RuntimeError("2"), _txt("Xong."))
        r = THO.chay_vong(goi=goi, so_cong_cu=5, sau=True)
        assert goi.model == ["gia_lap_du_phong", "gia_lap_du_phong", "gia_lap"] and r["mo_hinh_cuoi"] == "gia_lap"

    def test_usd_theo_gia_tung_model(self, monkeypatch):
        for k, v in (("THO_GIA_VAO", "1"), ("THO_GIA_RA", "2"), ("THO_GIA_VAO_DU_PHONG", "10"), ("THO_GIA_RA_DU_PHONG", "20")):
            monkeypatch.setenv(k, v)
        goi = _kich_ban(_rong(500_000, 50_000), _rong(500_000, 50_000), _txt("Xong.", 1_000_000, 100_000))
        r = THO.chay_vong(goi=goi, so_cong_cu=5)
        # model chinh: 1,0M vao x1 + 0,1M ra x2 = 1,2 USD; du phong: 1,0M x10 + 0,1M x20 = 12 USD
        assert r["usd"] == pytest.approx(13.2) and _vong(r["vong_id"])["usd"] == pytest.approx(13.2)

    def test_khong_khai_gia_du_phong_thi_dung_gia_chinh(self, monkeypatch):
        monkeypatch.setenv("THO_GIA_VAO", "1")
        monkeypatch.setenv("THO_GIA_RA", "2")
        monkeypatch.delenv("THO_GIA_VAO_DU_PHONG", raising=False)
        monkeypatch.delenv("THO_GIA_RA_DU_PHONG", raising=False)
        goi = _kich_ban(_rong(), _rong(), _txt("Xong.", 1_000_000, 100_000))
        assert THO.chay_vong(goi=goi, so_cong_cu=5)["usd"] == pytest.approx(1.2)


class TestDuongModelRe:
    @pytest.fixture
    def sach(self, tmp_path, monkeypatch):
        for k in ("THO_KHOA_ENV", "THO_BASE_URL", "THO_MO_HINH", "THO_MO_HINH_DU_PHONG", "THO_PROVIDER", "AIBOX_API_KEY"):
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setattr(QM, "CC_SWITCH_DB", tmp_path / "khong_co.db")

    def test_mac_dinh_la_ai_box_flash_va_du_phong_qwen_max(self, sach, monkeypatch):
        monkeypatch.setenv("AIBOX_API_KEY", "khoa-gia")
        d = THO.duong()
        assert d["url"] == "https://api.ai-box.vn/v1/chat/completions" and d["khoa"] == "khoa-gia"
        assert (d["mo_hinh"], d["du_phong"], d["nguon"]) == ("ds/deepseek-flash", "qwen3.8-max-0902", "env:AIBOX_API_KEY")

    def test_sau_dao_hai_model(self, sach, monkeypatch):
        monkeypatch.setenv("AIBOX_API_KEY", "khoa-gia")
        d = THO.duong(sau=True)
        assert (d["mo_hinh"], d["du_phong"]) == ("qwen3.8-max-0902", "ds/deepseek-flash")

    def test_THO_MO_HINH_doi_model_chinh_o_duong_ai_box(self, sach, monkeypatch):
        monkeypatch.setenv("AIBOX_API_KEY", "khoa-gia")
        monkeypatch.setenv("THO_MO_HINH", "qwen3.8-flash")
        d = THO.duong()
        assert d["mo_hinh"] == "qwen3.8-flash" and d["du_phong"] == "qwen3.8-max-0902"
        monkeypatch.setenv("THO_MO_HINH", "qwen3.8-max-0902")
        assert THO.duong()["du_phong"] == "", "model chinh trung model du phong thi khong con gi de doi sang"

    def test_duong_cloud_tu_khai_van_chay_va_co_du_phong_tuy_chon(self, sach, monkeypatch):
        monkeypatch.setenv("THO_KHOA_ENV", "KHOA_GIA")
        monkeypatch.setenv("KHOA_GIA", "k")
        monkeypatch.setenv("THO_MO_HINH_DU_PHONG", "deepseek-reasoner")
        assert THO.duong()["du_phong"] == "deepseek-reasoner"
        d = THO.duong(sau=True)
        assert (d["mo_hinh"], d["du_phong"]) == ("deepseek-reasoner", "deepseek-chat")

    def test_thieu_khoa_noi_ro_cach_sua_va_khong_lo_gi(self, sach):
        with pytest.raises(RuntimeError) as e:
            THO.duong()
        assert "AIBOX_API_KEY" in str(e.value) and "cc-switch" in str(e.value) and "THO_KHOA_ENV" in str(e.value)


class TestGoiRe:
    @pytest.fixture
    def duong_gia(self, monkeypatch):
        d = {"url": "http://x/chat/completions", "khoa": "k", "mo_hinh": "a", "du_phong": "b", "nguon": "t"}
        monkeypatch.setattr(THO, "duong", lambda sau=False: dict(d))
        return d

    @staticmethod
    def _post(monkeypatch, *cau):
        hang, thay = list(cau), []

        def post(d, than, timeout=180):
            thay.append(than)
            x = hang.pop(0)
            if isinstance(x, Exception):
                raise x
            return x
        monkeypatch.setattr(THO, "_post", post)
        return thay

    def test_thanh_cong_lan_dau_va_tran_token_khong_thap_hon_6000(self, duong_gia, monkeypatch):
        thay = self._post(monkeypatch, _txt("Tom tat."))
        assert THO.goi_re("x", max_tokens=800) == "Tom tat." and [t["model"] for t in thay] == ["a"]
        assert thay[0]["max_tokens"] == THO.TRAN_TOKEN_TOM_TAT == 6000, "mo hinh suy luan an token suy luan trong tran"
        thay = self._post(monkeypatch, _txt("Dai."))
        THO.goi_re("x", max_tokens=9000)
        assert thay[0]["max_tokens"] == 9000

    def test_hai_lan_sai_roi_moi_den_du_phong(self, duong_gia, monkeypatch):
        thay = self._post(monkeypatch, RuntimeError("500"), _rong(), _txt("Tu du phong."))
        assert THO.goi_re("x") == "Tu du phong." and [t["model"] for t in thay] == ["a", "a", "b"]

    def test_sai_het_thi_nem_ro_tung_model(self, duong_gia, monkeypatch):
        self._post(monkeypatch, RuntimeError("500"), _rong(), RuntimeError("503"))
        with pytest.raises(RuntimeError) as e:
            THO.goi_re("x")
        m = str(e.value)
        assert m.startswith("model re sai het:") and "a: 500" in m and "a: tra rong" in m and "b: 503" in m

    def test_khong_co_du_phong_thi_chi_thu_model_chinh(self, duong_gia, monkeypatch):
        duong_gia["du_phong"] = ""
        thay = self._post(monkeypatch, RuntimeError("1"), RuntimeError("2"))
        with pytest.raises(RuntimeError):
            THO.goi_re("x")
        assert [t["model"] for t in thay] == ["a", "a"]


def test_main_chuyen_co_sau_xuong_chay_vong(monkeypatch, capsys):
    goi_la = []
    monkeypatch.setattr(THO, "chay_vong", lambda **kw: goi_la.append(kw) or {"vong_id": len(goi_la), "ket_luan": "ok"})
    assert THO.main(["--vong", "2", "--cong-cu", "5", "--sau"]) == 0
    assert goi_la == [{"so_cong_cu": 5, "sau": True}] * 2
    goi_la.clear()
    assert THO.main([]) == 0 and goi_la == [{"so_cong_cu": 30, "sau": False}]
    assert "vong_id" in capsys.readouterr().out
