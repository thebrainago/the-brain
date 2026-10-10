# -*- coding: utf-8 -*-
"""nhan/giao_llm.py - goi model re qua AI Box, ghi so chi, giu tran ngan sach (10/10/2026).

Module nay TIEU TIEN THAT nen moi dieu sau phai co bang chung bang test (khong goi mang that, `requests.post` bi thay):
  (1) cong thuc gia: token vao KHONG cache tinh gia vao, token cache tinh gia cache (re hon), token ra tinh gia ra - sai mot trong ba la
      so chi sai ma khong ai thay, tran ngay mat tac dung;
  (2) tran ngay chan TRUOC khi chi tien (khong goi mang) va chi tinh dong cua HOM NAY;
  (3) moi lan goi thanh cong de lai DUNG MOT dong so chi; lan loi mang khong de lai dong nao (khong tinh tien cho cai khong chay);
  (4) khong doc / in khoa: module khong cham vao bien moi truong hay tieu de Authorization (proxy gan san) - repo la PUBLIC."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from nhan import giao_llm as GL


class _PhanHoi:
    def __init__(self, du_lieu: dict, ma_loi: Exception | None = None):
        self._d = du_lieu
        self._loi = ma_loi

    def raise_for_status(self):
        if self._loi is not None:
            raise self._loi

    def json(self):
        return self._d


class _Mang:
    """Thay `requests.post`: ghi lai moi lan goi de kiem tra noi dung gui di."""

    def __init__(self, du_lieu: dict | None = None, loi: Exception | None = None):
        self.du_lieu = du_lieu if du_lieu is not None else {
            "choices": [{"message": {"content": "OK"}}],
            "usage": {"prompt_tokens": 1000, "completion_tokens": 200, "prompt_tokens_details": {"cached_tokens": 400}}}
        self.loi = loi
        self.cac_lan: list[dict] = []

    def __call__(self, url, json=None, timeout=None, **kw):
        self.cac_lan.append({"url": url, "body": json, "timeout": timeout, "kw": kw})
        return _PhanHoi(self.du_lieu, self.loi)


@pytest.fixture
def mang(tmp_path, monkeypatch):
    """So chi o tep tam + mang gia. Tra ve (mang gia, duong dan so chi)."""
    so_chi = tmp_path / "reports" / "deepseek" / "so_chi.jsonl"
    monkeypatch.setattr(GL, "SO_CHI", so_chi)
    m = _Mang()
    monkeypatch.setattr(GL.requests, "post", m)
    return m, so_chi


def _ghi_so_chi(so_chi: Path, dong: list[dict]):
    so_chi.parent.mkdir(parents=True, exist_ok=True)
    so_chi.write_text("".join(json.dumps(d) + "\n" for d in dong), encoding="utf-8")


# ---------------------------------------------------------------------------------------------------------------- bang gia
def test_bang_tang_hop_le_va_cache_re_hon_gia_vao():
    assert set(GL.TANG) == {"T1", "T2", "T3", "T4", "T4m"}
    for ten, (model, gia_vao, gia_ra, gia_cache, them) in GL.TANG.items():
        assert model and isinstance(them, dict), ten
        assert gia_vao > 0 and gia_ra > 0 and gia_cache > 0, ten
        assert gia_cache < gia_vao, "%s: token cache phai re hon token vao thuong" % ten             # neu khong cong thuc cache vo nghia
        assert gia_ra > gia_vao, "%s: token ra dat hon token vao" % ten


# ---------------------------------------------------------------------------------------------------------------- cong thuc gia
def test_cong_thuc_gia_tach_ba_loai_token(mang):
    m, _ = mang
    r = GL.goi("T1", "xin chao", 50, "thu")
    gv, gr, gc = GL.TANG["T1"][1:4]
    mong_doi = ((1000 - 400) * gv + 400 * gc + 200 * gr) / 1e6                       # 600 vao thuong + 400 cache + 200 ra
    assert r["dong"] == pytest.approx(mong_doi)
    assert r["dong"] == pytest.approx(1.02128)                                        # chot cung con so de loi doi bang gia khong lot qua
    assert (r["vao"], r["ra"], r["noi_dung"]) == (1000, 200, "OK")


def test_khong_cache_thi_khong_tinh_gia_cache(mang):
    m, _ = mang
    m.du_lieu = {"choices": [{"message": {"content": "x"}}], "usage": {"prompt_tokens": 1000, "completion_tokens": 0}}
    r = GL.goi("T2", "p")
    assert r["dong"] == pytest.approx(1000 * GL.TANG["T2"][1] / 1e6)


def test_phan_hoi_thieu_usage_va_noi_dung_khong_sap(mang):
    m, so_chi = mang
    m.du_lieu = {"choices": [{"message": {"content": None}}]}                         # model tra content rong + khong co usage
    r = GL.goi("T1", "p")
    assert r == {"noi_dung": "", "dong": 0.0, "vao": 0, "ra": 0}
    assert len(so_chi.read_text("utf-8").splitlines()) == 1                           # van ghi so (goi that da xay ra)


def test_tang_la_bi_tu_choi_truoc_khi_goi_mang(mang):
    m, so_chi = mang
    with pytest.raises(KeyError):
        GL.goi("T9", "p")
    assert m.cac_lan == [] and not so_chi.exists()


# ---------------------------------------------------------------------------------------------------------------- noi dung gui di
def test_noi_dung_gui_di_dung_model_tham_so_va_he(mang):
    m, _ = mang
    GL.goi("T1", "cau hoi", 77, "viec1", he="ban la tro ly")
    (lan,) = m.cac_lan
    assert lan["url"] == GL.URL and lan["timeout"] == 120
    b = lan["body"]
    assert b["model"] == "qwen3.8-flash" and b["max_tokens"] == 77 and b["temperature"] == 0.2
    assert b["enable_thinking"] is False                                              # tham so tat suy luan cua tang phai di kem
    assert b["messages"] == [{"role": "system", "content": "ban la tro ly"}, {"role": "user", "content": "cau hoi"}]


def test_khong_co_he_thi_khong_gui_tin_nhan_system(mang):
    m, _ = mang
    GL.goi("T2", "chi co cau hoi")
    b = m.cac_lan[0]["body"]
    assert b["messages"] == [{"role": "user", "content": "chi co cau hoi"}]
    assert b["thinking"] == {"type": "disabled"}                                      # tang T2 tat suy luan theo kieu khac T1


def test_tang_t3_khong_co_tham_so_them(mang):
    m, _ = mang
    GL.goi("T3", "p")
    b = m.cac_lan[0]["body"]
    assert "enable_thinking" not in b and "thinking" not in b and b["model"] == GL.TANG["T3"][0]


# ---------------------------------------------------------------------------------------------------------------- so chi
def test_moi_lan_goi_thanh_cong_de_lai_dung_mot_dong_so_chi(mang):
    m, so_chi = mang
    GL.goi("T1", "a", viec="viec_a")
    GL.goi("T2", "b", viec="viec_b")
    dong = [json.loads(x) for x in so_chi.read_text("utf-8").splitlines()]
    assert [d["viec"] for d in dong] == ["viec_a", "viec_b"] and [d["tang"] for d in dong] == ["T1", "T2"]
    d = dong[0]
    assert d["ngay"] == time.strftime("%Y-%m-%d") and d["model"] == "qwen3.8-flash"
    assert (d["vao"], d["cache"], d["ra"]) == (1000, 400, 200) and d["dong"] == pytest.approx(1.021, abs=1e-3)
    assert set(d) == {"ngay", "tang", "model", "viec", "vao", "cache", "ra", "dong", "giay"}


def test_loi_mang_khong_de_lai_dong_so_chi_va_khong_bi_nuot(tmp_path, monkeypatch):
    so_chi = tmp_path / "so_chi.jsonl"
    monkeypatch.setattr(GL, "SO_CHI", so_chi)
    monkeypatch.setattr(GL.requests, "post", _Mang(loi=RuntimeError("HTTP 500")))
    with pytest.raises(RuntimeError, match="HTTP 500"):
        GL.goi("T1", "p")
    assert not so_chi.exists()


def test_da_chi_hom_nay_chi_cong_dong_cua_hom_nay(tmp_path, monkeypatch):
    so_chi = tmp_path / "so_chi.jsonl"
    monkeypatch.setattr(GL, "SO_CHI", so_chi)
    assert GL.da_chi_hom_nay() == 0.0                                                 # chua co tep
    hom_nay = time.strftime("%Y-%m-%d")
    _ghi_so_chi(so_chi, [{"ngay": hom_nay, "dong": 10.5}, {"ngay": "2000-01-01", "dong": 999.0}, {"ngay": hom_nay, "dong": 4.5}, {"ngay": hom_nay}])
    assert GL.da_chi_hom_nay() == pytest.approx(15.0)                                 # dong thieu `dong` tinh 0, ngay cu khong tinh


# ---------------------------------------------------------------------------------------------------------------- tran ngay
def test_vuot_tran_ngay_nem_loi_truoc_khi_goi_mang(mang):
    m, so_chi = mang
    _ghi_so_chi(so_chi, [{"ngay": time.strftime("%Y-%m-%d"), "dong": 100.0}])
    with pytest.raises(RuntimeError, match="vuot tran chi ngay 100"):
        GL.goi("T1", "p", tran_ngay=100.0)                                            # bang tran la da vuot (>=), khong cho chi them
    assert m.cac_lan == []                                                            # khong mot request nao di ra
    assert len(so_chi.read_text("utf-8").splitlines()) == 1                           # va khong them dong so chi


def test_duoi_tran_van_goi_va_cong_don_sau_lan_goi(mang):
    m, so_chi = mang
    _ghi_so_chi(so_chi, [{"ngay": time.strftime("%Y-%m-%d"), "dong": 50.0}])
    GL.goi("T1", "p", tran_ngay=100.0)
    assert len(m.cac_lan) == 1
    assert GL.da_chi_hom_nay() == pytest.approx(51.021, abs=1e-3)
    with pytest.raises(RuntimeError, match="vuot tran chi ngay 51"):                  # gio da chi 51,02 >= 51 -> lan nay bi chan
        GL.goi("T1", "p", tran_ngay=51.0)
    assert len(m.cac_lan) == 1


def test_ngay_cu_khong_tinh_vao_tran(mang):
    m, so_chi = mang
    _ghi_so_chi(so_chi, [{"ngay": "2000-01-01", "dong": 1e9}])
    GL.goi("T1", "p", tran_ngay=1.0)                                                  # so chi cua ngay xua khong chan hom nay
    assert len(m.cac_lan) == 1


def test_khong_dat_tran_thi_khong_doc_so_chi_de_chan(mang):
    m, so_chi = mang
    _ghi_so_chi(so_chi, [{"ngay": time.strftime("%Y-%m-%d"), "dong": 1e9}])
    GL.goi("T1", "p")                                                                 # tran_ngay=None: caller tu chiu trach nhiem
    assert len(m.cac_lan) == 1


# ---------------------------------------------------------------------------------------------------------------- khong cham khoa
def test_module_khong_doc_khoa_khong_dat_tieu_de_xac_thuc():
    nguon = Path(GL.__file__).read_text(encoding="utf-8").lower()
    for tu in ("authorization", "bearer", "environ", "getenv", "api_key", "apikey", "password"):
        assert tu not in nguon, "giao_llm khong duoc cham vao khoa / tieu de xac thuc: thay '%s'" % tu
