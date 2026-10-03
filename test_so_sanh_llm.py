# -*- coding: utf-8 -*-
"""so_sanh_llm: cham bang MA. Dung nha cung cap GIA (ham post) - khong goi mang; hieu chuan hai chieu: mo hinh tot DAT, mo hinh te KHONG."""
from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

import pytest

from nhan import so_sanh_llm as S

SPEC_TOT = [
    {"ten": "a1", "co_che": "Gia dong cua o day bien do ngay thuong hoi lai vi nguoi ban thao chay.", "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 1,
     "vao": [{"trai": {"chi_bao": "ibs"}, "phep": "<", "phai": {"hang": 0.2}}], "ra": []},
    {"ten": "a2", "co_che": "RSI ngan han qua thap cho thay nguoi ban bi ep phai cat lo nen gia hoi lai.", "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 3,
     "vao": [{"trai": {"chi_bao": "rsi", "n": 14}, "phep": "<", "phai": {"hang": 30}}], "ra": []},
    {"ten": "a3", "co_che": "RSI rat cao cho thay mua duoi da qua da va thuong dao chieu som.", "ho": "quay_ve_trung_binh", "chieu": -1, "giu": 2,
     "vao": [{"trai": {"chi_bao": "rsi", "n": 7}, "phep": ">", "phai": {"hang": 80}}], "ra": []},
    {"ten": "a4", "co_che": "Gia vuot trung binh dai han cho thay xu huong dang duoc tra tien de nam giu.", "ho": "xu_huong", "chieu": 1, "giu": 5,
     "vao": [{"trai": {"chi_bao": "sma", "n": 20}, "phep": ">", "phai": {"chi_bao": "sma", "n": 100}}], "ra": []},
    {"ten": "a5", "co_che": "Bien do tuyet doi lon so voi ATR cho thay co dong luong moi dang bat dau hinh thanh.", "ho": "pha_vo", "chieu": -1, "giu": 4,
     "vao": [{"trai": {"chi_bao": "atr", "n": 14}, "phep": ">", "phai": {"hang": 0.5}}], "ra": []},
]


def _tin(text="", tool_calls=None, vao=100, ra=50):
    return {"choices": [{"message": {"content": text, "tool_calls": tool_calls or []}}], "usage": {"prompt_tokens": vao, "completion_tokens": ra}}


def post_tot(d, than, timeout=0):
    nhac = than["messages"][0]["content"]
    if than.get("tools"):
        return _tin("", [{"function": {"name": "tim_quy_luat", "arguments": '{"ma": "AUDCAD", "khung": "H4", "so_null": 200}'}}])
    if "ngay_con_lai" in nhac:
        return _tin('{"ngay_con_lai": 29, "la_ngay_cuoi_tuan": false}')
    if "co_che" in nhac and "5 khai bao" in nhac:
        return _tin(json.dumps({"co_che": SPEC_TOT}))
    if "hold %/nam" in nhac:
        return _tin("Cau hinh buoc30 hs1,0 tp60 tia: hold 13,26 %/nam, DD hold -3,5%.")
    if "tong_loi_pct" in nhac:
        return _tin('{"tong_loi_pct": 50.0, "max_dd_pct": 25.0, "cagr_pct": 22.47}')
    if '"chan"' in nhac:
        return _tin('{"chan": [true, false, true, true]}')
    if "Tom tat" in nhac:
        return _tin("b test: 108 fail, 2642 pass. kiem 30 khop cloud. MT5 XM mai cai.")
    if "prompt cache" in nhac:
        return _tin("Prompt cache là cơ chế lưu lại phần đầu của yêu cầu để lần sau không phải xử lý lại. Nhờ cache, các yêu cầu lặp lại rẻ hơn và nhanh hơn nhiều.")
    if "MA_XAC_NHAN_DUY_NHAT" in nhac:
        return _tin(S.NEEDLE["ma"])
    raise AssertionError("task la: " + nhac[:60])


def post_te(d, than, timeout=0):
    nhac = than["messages"][0]["content"]
    if than.get("tools"):
        return _tin("Toi se tim quy luat cho ban.")
    if "ngay_con_lai" in nhac:
        return _tin('```json\n{"ngay_con_lai": 28, "la_ngay_cuoi_tuan": true}\n```')
    if "5 khai bao" in nhac:
        xau = dict(SPEC_TOT[0], ho="khong_co", co_che="ngan")
        return _tin(json.dumps({"co_che": [xau, SPEC_TOT[1], SPEC_TOT[1], dict(SPEC_TOT[2], vao=[{"trai": {"chi_bao": "bia_ra"}, "phep": "<", "phai": {"hang": 1}}])]}))
    if "hold %/nam" in nhac:
        return _tin("Cau hinh thu hai.")
    if "tong_loi_pct" in nhac:
        return _tin('{"tong_loi_pct": 50, "max_dd_pct": 13.6, "cagr_pct": 50}')
    if '"chan"' in nhac:
        return _tin('{"chan": [false, false, true, false]}')
    if "Tom tat" in nhac:
        return _tin("Co 999 test hong va 77 thanh cong, " + "rat " * 80)
    if "prompt cache" in nhac:
        return _tin("- Cache la bo nho dem.\n- Giup nhanh hon.")
    return _tin("khong biet")


def ncc(ten, **kw):
    return dict({"ten": ten, "url": "http://x/chat/completions", "khoa": "KHOA_BI_MAT", "mo_hinh": ten + "-m", "nguon": "gia", "them": {}, "gia_vao": None, "gia_ra": None}, **kw)


class TestHaiChieu:
    def test_mo_hinh_tot_dat_tuyet_doi_mo_hinh_te_bi_phat(self):
        kq = S.so_sanh([ncc("tot"), ncc("te")], S.tao_task(), lan=1, post=lambda d, t, to=0: (post_tot if d["ten"] == "tot" else post_te)(d, t))
        tot, te = kq["ncc"]["tot"], kq["ncc"]["te"]
        assert tot["tb"] == pytest.approx(1.0), {k: v["tb"] for k, v in tot["task"].items()}
        assert te["tb"] < 0.35, {k: v["tb"] for k, v in te["task"].items()}
        assert "CHON tot" in kq["ket_luan"] and "tot thang 8" in kq["ket_luan"]

    def test_diem_gan_nhau_thi_chon_re_hon_dung_gia(self):
        a, b = ncc("dat", gia_vao=1.0, gia_ra=2.0), ncc("re", gia_vao=0.1, gia_ra=0.2)
        kq = S.so_sanh([a, b], S.tao_task(), lan=1, post=post_tot)
        assert kq["ncc"]["dat"]["chi_phi_usd"] == pytest.approx((kq["ncc"]["dat"]["tok_vao"] * 1.0 + kq["ncc"]["dat"]["tok_ra"] * 2.0) / 1e6, abs=1e-5)
        assert "RE HON = re" in kq["ket_luan"], kq["ket_luan"]

    def test_chua_khai_gia_thi_noi_that(self):
        kq = S.so_sanh([ncc("a"), ncc("b")], S.tao_task(), lan=1, post=post_tot)
        assert kq["ncc"]["a"]["chi_phi_usd"] is None and "chua khai gia" in kq["ket_luan"]
        assert "chua khai" in S.bao_cao(kq)

    def test_loi_mang_tinh_la_0_diem_va_dem_loi_khong_nem(self):
        def hong(d, t, to=0):
            raise RuntimeError("model re HTTP 500: boom")
        kq = S.so_sanh([ncc("hong")], S.tao_task()[:3], lan=2, post=hong)
        r = kq["ncc"]["hong"]
        assert r["tb"] == 0.0 and r["loi"] == 6 and r["task"]["json_ky_luat"]["ghi"][0].startswith("LOI RuntimeError")

    def test_bao_cao_gon_va_co_du_cot(self):
        kq = S.so_sanh([ncc("tot"), ncc("te")], S.tao_task(), lan=1, post=lambda d, t, to=0: (post_tot if d["ten"] == "tot" else post_te)(d, t))
        b = S.bao_cao(kq)
        assert len(b) < 2200 and "DIEM TB" in b and "KET LUAN" in b and "tot-m" in b and "KHOA_BI_MAT" not in b


class TestCham:
    def test_json_tu_phan_biet_sach_rao_va_hong(self):
        assert S._json_tu('{"a": 1}') == ({"a": 1}, "sach")
        assert S._json_tu('Day:\n```json\n{"a": 1}\n```') == ({"a": 1}, "rao")
        assert S._json_tu("khong co json") == (None, None)

    def test_spec_phat_dung_loi_thuc_te_cua_ngu_phap(self):
        xau = [dict(SPEC_TOT[0], co_che="ngan")] + [dict(SPEC_TOT[1], vao=[{"trai": {"chi_bao": "zscore", "n": 5}, "phep": "<", "phai": {"hang": -1}}])]
        d, g = S.cham_spec_co_che({"text": json.dumps({"co_che": xau + SPEC_TOT[2:]})})
        assert d == pytest.approx(3 / 5) and "cu phap" in g and "KeyError" in g, "zscore thieu 'cua' la loi that cua trinh thong dich"

    def test_spec_trung_dieu_kien_vao_khong_duoc_tinh_hai_lan(self):
        d, g = S.cham_spec_co_che({"text": json.dumps({"co_che": [SPEC_TOT[0]] * 5})})
        assert d == pytest.approx(1 / 5) and "trung" in g

    def test_tinh_cagr_khop_dap_an_tinh_tay(self):
        # von 100..150 sau 2 nam: tong 50%, CAGR = 1,5^(1/2)-1 = 22,47%; sut giam lon nhat 120 -> 90 = 25%
        assert (1.5 ** 0.5 - 1) * 100 == pytest.approx(22.47, abs=0.01) and (120 - 90) / 120 * 100 == 25.0
        assert S.cham_cagr_maxdd({"text": '{"tong_loi_pct": 50, "max_dd_pct": -25, "cagr_pct": 22.5}'})[0] == pytest.approx(1.0)

    def test_luat_chan_dap_an_theo_tieu_chi_chu_du_an(self):
        assert S.cham_luat_chan({"text": '{"chan": [true, false, true, true]}'})[0] == 1.0
        assert S.cham_luat_chan({"text": '[true, true, true, true]'})[0] == 0.75, "(b) kieu martingale chi la NHAN, khong chan"

    def test_tom_tat_phat_so_bia_va_dai(self):
        d, g = S.cham_tom_tat({"text": "108 fail, 2642 pass, kiem 30 khop, mai cai MT5 va them 555 loi"})
        assert d == pytest.approx(0.75) and "555" in g

    def test_tieng_viet_bat_markdown_va_sai_so_cau(self):
        assert S.cham_tieng_viet({"text": "Một. Hai cache ạ ỉ ở."})[0] >= 0.75
        assert S.cham_tieng_viet({"text": "- gạch đầu dòng\n- thứ hai cache"})[0] < 0.5


class TestNhaCungCap:
    def test_env_thang_cc_switch_va_khong_in_khoa(self):
        env = {"SO_SANH_QWEN_KHOA": "k1", "SO_SANH_QWEN_URL": "https://q.example/v1", "SO_SANH_QWEN_MO_HINH": "qwen-x",
               "SO_SANH_QWEN_GIA_VAO": "0.3", "SO_SANH_QWEN_THEM": '{"enable_thinking": false}'}
        d = S.nha_cung_cap("qwen", env=env, cc=lambda ten: pytest.fail("co env thi khong duoc hoi cc-switch"))
        assert d["url"] == "https://q.example/v1/chat/completions" and d["mo_hinh"] == "qwen-x" and d["gia_vao"] == 0.3 and d["them"] == {"enable_thinking": False}

    def test_cc_switch_khi_khong_co_env_va_mac_dinh_deepseek(self):
        d = S.nha_cung_cap("deepseek", env={}, cc=lambda ten: {"khoa": "kk", "base_url": "", "model": "", "ten": "DeepSeek"} if ten == "deepseek" else {})
        assert d["url"] == "https://api.deepseek.com/chat/completions" and d["mo_hinh"] == "deepseek-chat" and d["nguon"].startswith("cc-switch")
        q = S.nha_cung_cap("qwen", env={}, cc=lambda ten: {"khoa": "k2", "base_url": "https://api.ai-box.vn/v1", "model": "qwen3.7-flash", "ten": "aibox"} if ten == "aibox" else {})
        assert q["url"] == "https://api.ai-box.vn/v1/chat/completions" and q["mo_hinh"] == "qwen3.7-flash"

    def test_thieu_gi_noi_dung_cai_do_va_khong_lo_khoa(self):
        with pytest.raises(S.ThieuCauHinh) as e:
            S.nha_cung_cap("qwen", env={"SO_SANH_QWEN_KHOA": "BI_MAT"}, cc=lambda ten: {})
        m = str(e.value)
        assert "thieu url, mo_hinh" in m and "BI_MAT" not in m and "_URL" in m


class TestMainVaNeedle:
    def test_khai_va_main_thieu_cau_hinh_khong_in_khoa(self, monkeypatch):
        for k in list(__import__("os").environ):
            if k.startswith("SO_SANH_") or k in ("DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY", "AIBOX_API_KEY"):
                monkeypatch.delenv(k)
        monkeypatch.setattr(S, "_cc_switch", lambda ten: {})
        b = io.StringIO()
        with redirect_stdout(b):
            assert S.main(["--khai"]) == 0
        assert b.getvalue().count("THIEU") == len(S.MAC_DINH) == 7, "moi ho so ten san phai hien trong --khai"
        b = io.StringIO()
        with redirect_stdout(b):
            assert S.main([]) == 2
        assert "THIEU CAU HINH" in b.getvalue()

    def test_needle_dai_co_ma_trong_van_ban_va_cham_dung(self):
        ts = S.tao_task(dai=True)
        t = ts[-1]
        assert t["ten"] == "needle_dai" and S.NEEDLE["ma"] in t["nhac"] and len(t["nhac"]) > 10_000
        assert S.cham_needle({"text": "Ma la %s" % S.NEEDLE["ma"]})[0] == 1.0 and S.cham_needle({"text": "khong biet"})[0] == 0.0


# ------------------------------------------------------------------ ban giao LLM (thu nha c91d, 03/10/2026)
def _khoa_that(*_a, **_k):
    pytest.fail("co env thi khong duoc hoi cc-switch")


class TestHoSoAiBox:
    def test_nam_ho_so_ten_san_tro_dung_model_cua_thu_c91d(self):
        env = {"AIBOX_API_KEY": "khoa-gia"}
        mo_hinh = {"ds": "ds/deepseek-flash", "qwen38": "qwen3.8-max-0902", "qwen38f": "qwen3.8-flash", "kimi": "kimi-k3", "glm": "glm-5.3"}
        for ten, m in mo_hinh.items():
            d = S.nha_cung_cap(ten, env=env, cc=_khoa_that)
            assert d["url"] == "https://api.ai-box.vn/v1/chat/completions" and d["mo_hinh"] == m and d["khoa"] == "khoa-gia" and d["nguon"] == "env"

    def test_cc_switch_cho_khoa_nhung_khong_duoc_doi_model_va_khong_lay_cau_noi_codex(self):
        cc = lambda ten: {"khoa": "kk", "base_url": "http://127.0.0.1:8317/v1", "model": "gpt-codex", "ten": "aibox"} if ten == "aibox" else {}
        d = S.nha_cung_cap("qwen38", env={}, cc=cc)
        assert d["khoa"] == "kk" and d["mo_hinh"] == "qwen3.8-max-0902", "model cua ho so THANG model cua cc-switch"
        assert d["url"] == "https://api.ai-box.vn/v1/chat/completions", "cau noi 127.0.0.1 chi cho /v1/responses cua Codex"
        assert d["nguon"] == "cc-switch:aibox"

    def test_ho_so_cu_qwen_giu_nghia_cu_cc_switch_van_quyet_model(self):
        cc = lambda ten: {"khoa": "k2", "base_url": "https://api.ai-box.vn/v1", "model": "qwen3.7-flash", "ten": "aibox"}
        assert S.nha_cung_cap("qwen", env={}, cc=cc)["mo_hinh"] == "qwen3.7-flash"

    def test_doi_id_chua_thu_bang_bien_moi_truong(self):
        env = {"AIBOX_API_KEY": "k", "SO_SANH_KIMI_MO_HINH": "kimi-k3-0902", "SO_SANH_GLM_URL": "https://glm.example/v1"}
        assert S.nha_cung_cap("kimi", env=env, cc=_khoa_that)["mo_hinh"] == "kimi-k3-0902"
        assert S.nha_cung_cap("glm", env=env, cc=_khoa_that)["url"] == "https://glm.example/v1/chat/completions"

    def test_thieu_khoa_ai_box_khong_lo_khoa_va_chi_cach_sua(self):
        with pytest.raises(S.ThieuCauHinh) as e:
            S.nha_cung_cap("ds", env={}, cc=lambda ten: {})
        assert "ds: thieu khoa" in str(e.value) and "SO_SANH_DS_KHOA" in str(e.value)


class TestChamGoiCongCuNoiLong:
    @staticmethod
    def _goi(*cau):
        return {"tool_calls": [{"function": {"name": n, "arguments": a}} for n, a in cau]}

    DUNG = '{"ma": "AUDCAD", "khung": "H4", "so_null": 200}'

    def test_doc_so_tay_truoc_roi_tim_quy_luat_van_dung_diem_tuyet_doi(self):
        d, g = S.cham_goi_cong_cu(self._goi(("xem_so_tay", "{}"), ("tim_quy_luat", self.DUNG)))
        assert d == pytest.approx(1.0) and "them: xem_so_tay" in g, "Qwen3.8 hay doc so tay truoc - ban cu cham 0 vi chi xet loi goi dau"

    def test_chi_doc_so_tay_ma_khong_tim_quy_luat_la_0(self):
        assert S.cham_goi_cong_cu(self._goi(("xem_so_tay", "{}")))[0] == 0.0
        assert S.cham_goi_cong_cu({"tool_calls": []})[0] == 0.0

    def test_bia_ten_cong_cu_bi_tru_dung_0_2(self):
        d, g = S.cham_goi_cong_cu(self._goi(("tim_quy_luat", self.DUNG), ("xoa_het", "{}")))
        assert d == pytest.approx(0.8) and "xoa_het" in g

    def test_sai_tham_so_tru_tung_phan_va_arguments_dang_dict_van_doc_duoc(self):
        assert S.cham_goi_cong_cu(self._goi(("tim_quy_luat", '{"ma": "AUDCAD", "khung": "D1", "so_null": 100}')))[0] == pytest.approx(0.6)
        goi = {"tool_calls": [{"function": {"name": "tim_quy_luat", "arguments": {"ma": "audcad", "khung": "h4", "so_null": 200}}}]}
        assert S.cham_goi_cong_cu(goi)[0] == pytest.approx(1.0)

    def test_arguments_hong_va_bia_ten_cong_don_nhung_khong_xuong_duoi_0(self):
        assert S.cham_goi_cong_cu(self._goi(("tim_quy_luat", "{khong json")))[0] == pytest.approx(0.25)
        assert S.cham_goi_cong_cu(self._goi(("tim_quy_luat", "[1, 2]")))[0] == pytest.approx(0.25)
        assert S.cham_goi_cong_cu(self._goi(("tim_quy_luat", "{khong json"), ("bia", "{}")))[0] == pytest.approx(0.05)


class TestKetLuanNhieuNhaCungCap:
    @staticmethod
    def _kq(**diem_chi_phi):
        ncc = {n: {"tb": tb, "chi_phi_usd": cp, "tok_ra": 1000, "task": {}} for n, (tb, cp) in diem_chi_phi.items()}
        return {"task": [], "ncc": ncc}

    def test_dan_dau_hon_cai_ke_tiep_tu_0_1_thi_chon_diem_cao(self):
        k = S.ket_luan(self._kq(ds=(0.95, None), qwen38=(0.7, None), kimi=(0.5, None)))
        assert k.startswith("Xep hang (diem TB): ds 0.950 > qwen38 0.700 > kimi 0.500") and "CHON ds" in k

    def test_chenh_duoi_0_1_khong_duoc_goi_la_thang_dung_voi_mau_nho(self):
        k = S.ket_luan(self._kq(ds=(0.906, None), qwen38=(0.854, None), kimi=(0.5, None)))
        assert k.startswith("Xep hang (diem TB): ds 0.906 > qwen38 0.854 > kimi 0.500")
        assert "2 cai gan nhau" in k and "CHON" not in k, "0,906 vs 0,854 la nhieu cua mau 8 task x 2 lan"

    def test_gan_nhau_co_gia_thi_chon_re_hon_khong_gia_thi_noi_that(self):
        k = S.ket_luan(self._kq(ds=(0.90, 0.5), qwen38=(0.88, 2.0), kimi=(0.3, 0.1)))
        assert "2 cai GAN NHAU" in k and "RE HON = ds (0.50000 USD)" in k, "kimi re nhat nhung diem thua xa -> khong duoc vao nhom gan nhau"
        k = S.ket_luan(self._kq(ds=(0.90, None), qwen38=(0.88, 2.0), glm=(0.89, 1.0)))
        assert "chua khai gia" in k and "ds 1000" in k

    def test_bao_cao_ba_nha_cung_cap_du_cot_va_khong_lo_khoa(self):
        kq = S.so_sanh([ncc("a"), ncc("b"), ncc("c")], S.tao_task()[:4], lan=1, post=post_tot)
        b = S.bao_cao(kq)
        assert "3 nha cung cap" in b and "a-m" in b and "c-m" in b and "KHOA_BI_MAT" not in b and "Xep hang" in kq["ket_luan"]


class TestBiCatVaNhanTran:
    @staticmethod
    def _post_cat(ghi=None):
        def post(d, than, timeout=0):
            if ghi is not None:
                ghi.append(than)
            r = post_tot(d, than)
            r["choices"][0]["finish_reason"] = "length"
            return r
        return post

    def test_goi_mot_danh_dau_bi_cat_khi_finish_length(self):
        t = S.tao_task()[0]
        assert S.goi_mot(ncc("x"), t, post=self._post_cat())["bi_cat"] is True
        assert S.goi_mot(ncc("x"), t, post=post_tot)["bi_cat"] is False

    def test_so_sanh_dem_bi_cat_canh_bao_trong_ket_luan_va_bao_cao(self):
        kq = S.so_sanh([ncc("cat"), ncc("lanh")], S.tao_task()[:2], lan=1,
                       post=lambda d, t, to=0: (self._post_cat() if d["ten"] == "cat" else post_tot)(d, t))
        assert kq["ncc"]["cat"]["bi_cat"] == 2 and kq["ncc"]["lanh"]["bi_cat"] == 0
        assert "CANH BAO: cat bi cat 2 luot" in kq["ket_luan"] and "CHUA DO DUOC" in kq["ket_luan"]
        assert "BI CAT" in kq["ncc"]["cat"]["task"]["json_ky_luat"]["ghi"][0]
        assert "bi cat (length)" in S.bao_cao(kq)

    def test_khong_bi_cat_thi_khong_canh_bao_va_khong_them_dong(self):
        kq = S.so_sanh([ncc("a"), ncc("b")], S.tao_task()[:2], lan=1, post=post_tot)
        assert "CANH BAO" not in kq["ket_luan"] and "bi cat (length)" not in S.bao_cao(kq)

    def test_nhan_max_tokens_mac_dinh_12_bien_moi_truong_doi_duoc_va_rac_khong_lam_chet(self, monkeypatch):
        t = dict(S.tao_task()[0], max_tokens=200)
        ghi = []
        monkeypatch.delenv("SO_SANH_NHAN_MAX_TOKENS", raising=False)
        S.goi_mot(ncc("x"), t, post=self._post_cat(ghi))
        assert ghi[-1]["max_tokens"] == 2400
        for v, mong in (("3", 600), ("0", 200), ("-5", 200), ("abc", 2400), ("", 2400)):
            monkeypatch.setenv("SO_SANH_NHAN_MAX_TOKENS", v)
            S.goi_mot(ncc("x"), t, post=self._post_cat(ghi))
            assert ghi[-1]["max_tokens"] == mong, v

    def test_tham_so_them_cua_nha_cung_cap_de_len_than_yeu_cau(self):
        ghi = []
        S.goi_mot(ncc("x", them={"enable_thinking": False}), S.tao_task()[0], post=self._post_cat(ghi))
        assert ghi[0]["enable_thinking"] is False and ghi[0]["model"] == "x-m"
