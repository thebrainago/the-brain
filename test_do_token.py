# -*- coding: utf-8 -*-
"""do_token: do token that tu transcript Claude Code. Dung transcript gia nho, tinh tay duoc tung con so."""
from __future__ import annotations

import io
import json
import os
import time
from contextlib import redirect_stdout

from nhan import do_token as DT


def _goi(rid, ts, tao=0, doc=0, ra=0, nghi=0, khoi=None, g1h=True):
    u = {"input_tokens": 2, "cache_creation_input_tokens": tao, "cache_read_input_tokens": doc, "output_tokens": ra,
         "output_tokens_details": {"thinking_tokens": nghi},
         "cache_creation": {"ephemeral_1h_input_tokens": tao if g1h else 0, "ephemeral_5m_input_tokens": 0 if g1h else tao}}
    return {"type": "assistant", "requestId": rid, "timestamp": ts, "message": {"id": rid, "usage": u, "content": khoi or []}}


def _viet(p, dong):
    p.write_text("\n".join(json.dumps(d) for d in dong) + "\n", encoding="utf-8")


def _mau(tmp_path):
    f = tmp_path / "p.jsonl"
    _viet(f, [
        _goi("r1", "2026-10-02T10:00:00Z", tao=10_000, ra=100, nghi=60, khoi=[{"type": "tool_use", "id": "tu1", "name": "Bash"}]),
        _goi("r1", "2026-10-02T10:00:01Z", tao=10_000, ra=500, nghi=300),            # cung goi, dong thu hai (dau ra day du hon)
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "tu1", "content": "x" * 3200}]}},
        _goi("r2", "2026-10-02T10:00:10Z", tao=800, doc=10_000, ra=200),
        {"type": "system", "subtype": "compact_boundary"},
        _goi("r3", "2026-10-02T12:00:10Z", tao=9_000, doc=0, ra=100),               # nghi 2 gio -> goi lanh
    ])
    return f


class TestPhanTich:
    def test_dedupe_goi_va_cong_don_dung(self, tmp_path):
        d = DT.phan_tich(_mau(tmp_path))
        assert d["so_goi"] == 3, "hai dong cua cung requestId la MOT goi"
        t = d["tong_token"]
        assert t["ghi_cache"] == 19_800 and t["doc_cache"] == 10_000
        assert t["ra"] == 800, "lay dau ra day du nhat cua goi r1 (500), khong cong trung"
        assert t["thinking"] == 300

    def test_chi_phi_theo_ty_le_gia_chuan(self, tmp_path):
        d = DT.phan_tich(_mau(tmp_path))
        c = d["chi_phi"]
        assert c["ghi_cache"] == round(19_800 * 2.0), "TTL 1 gio ghi cache 2x"
        assert c["doc_cache"] == round(10_000 * 0.1) and c["ra"] == 800 * 5
        assert abs(sum(d["phan_tram"].values()) - 100) < 0.2

    def test_ttl_5_phut_ghi_cache_1_25x(self, tmp_path):
        f = tmp_path / "q.jsonl"
        _viet(f, [_goi("a", "2026-10-02T10:00:00Z", tao=1000, ra=10, g1h=False)])
        assert DT.phan_tich(f)["chi_phi"]["ghi_cache"] == round(1000 * 1.25)

    def test_goi_lanh_nghi_lau_va_nen(self, tmp_path):
        d = DT.phan_tich(_mau(tmp_path))
        assert d["goi_lanh"]["so"] == 2, "r1 (lan dau) va r3 (sau nghi 2 gio) phai ghi lai gan het ngu canh"
        assert len(d["nghi_lau"]) == 1 and d["nghi_lau"][0]["nghi_gio"] == 2.0 and d["nghi_lau"][0]["ghi_lai_token"] == 9_000
        assert d["so_lan_nen"] == 1 and len(d["cua_so"]) == 2

    def test_ket_qua_cong_cu_gan_ten_va_mang_theo(self, tmp_path):
        d = DT.phan_tich(_mau(tmp_path))
        cc = d["cong_cu"][0]
        assert cc["ten"] == "Bash" and cc["lan"] == 1 and cc["ky_tu"] == 3200
        assert d["ket_qua_lon"][0]["mang_theo_qua_goi"] == 1, "chi con 1 goi (r2) truoc ranh gioi nen"
        assert {"dau_ra_cua_ai", "ket_qua_cong_cu"} <= set(d["mang_theo"])

    def test_khuyen_nghi_noi_ro_nghi_lau_va_khong_bua(self, tmp_path):
        d = DT.phan_tich(_mau(tmp_path))
        assert any("nghi > 1 gio" in s for s in d["khuyen_nghi"])
        # ngu canh nho (~10k) thi KHONG duoc khuyen nen o 250k
        assert not any("250k" in s for s in d["khuyen_nghi"])

    def test_khuyen_nghi_cua_so_nen_khi_ngu_canh_lon(self, tmp_path):
        f = tmp_path / "l.jsonl"
        _viet(f, [_goi("a%d" % i, "2026-10-02T10:00:%02dZ" % i, doc=500_000, ra=50) for i in range(5)])
        d = DT.phan_tich(f)
        assert d["ngu_canh"]["tb"] == 500_002 and any("250k" in s for s in d["khuyen_nghi"])

    def test_file_rong_hoac_hong_khong_nem(self, tmp_path):
        f = tmp_path / "r.jsonl"
        f.write_text("khong phai json\n{}\n", encoding="utf-8")
        d = DT.phan_tich(f)
        assert d["so_goi"] == 0 and "Khong thay goi API" in DT.tom_tat(d)


class TestTimVaMain:
    def test_tim_transcript_lay_moi_nhat_trong_thu_muc_cua_cwd(self, tmp_path):
        cwd = tmp_path / "du an"
        cwd.mkdir()
        goc = tmp_path / "projects"
        slug = DT.re.sub(r"[^A-Za-z0-9]", "-", str(cwd.resolve()))
        (goc / slug).mkdir(parents=True)
        (goc / "khac").mkdir()
        cu, moi, khac = goc / slug / "cu.jsonl", goc / slug / "moi.jsonl", goc / "khac" / "x.jsonl"
        for p in (cu, moi, khac):
            p.write_text("{}\n", encoding="utf-8")
        t = time.time()
        os.utime(cu, (t - 100, t - 100))
        os.utime(moi, (t - 50, t - 50))
        os.utime(khac, (t, t))                       # moi nhat nhung thuoc thu muc khac
        assert DT.tim_transcript(cwd, goc) == moi
        assert DT.tim_transcript(tmp_path / "khong-co-slug", goc) == khac, "khong co thu muc cua cwd thi lay moi nhat bat ky"
        assert DT.tim_transcript(cwd, tmp_path / "khong-ton-tai") is None

    def test_main_in_tom_tat_va_json(self, tmp_path):
        f = _mau(tmp_path)
        b = io.StringIO()
        with redirect_stdout(b):
            assert DT.main([str(f)]) == 0
        assert "DO TOKEN" in b.getvalue() and "KHUYEN NGHI" in b.getvalue()
        b = io.StringIO()
        with redirect_stdout(b):
            assert DT.main([str(f), "--json"]) == 0
        assert json.loads(b.getvalue())["so_goi"] == 3
        b = io.StringIO()
        with redirect_stdout(b):
            assert DT.main([str(tmp_path / "khong-co.jsonl")]) == 1
