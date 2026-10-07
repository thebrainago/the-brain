# -*- coding: utf-8 -*-
"""Test pheu_gia_tri: kiem cau truc, diem HAI CHIEU (tot len / xau xuong), so cai + hoc nguoc, vong sua LLM."""
import json
import tempfile
from pathlib import Path

from nhan import pheu_gia_tri as P

TOT = {"co_che": "Nguoi mua duoi cuoi phien bi am hoi qua dem nen ban thao, nguoi cung cap thanh khoan duoc tra phi.",
       "lop_tai_san": "chi_so", "khung": "gio", "loai_co_che": "thanh_khoan",
       "loi_nhuan_cong_bo": {"pct_nam": 12.0, "sau_phi": True, "ngoai_mau": True},
       "du_lieu_can": ["gia_phut"], "dau_hieu_do": [],
       "suy_ra": [{"lop_tai_san": "hang_hoa", "khung": "gio", "chieu": 1, "bien_the_id": "x",
                   "vi_sao_tra_tien": "fix gio dong cua hang hoa co dong tien tai can bang cuoi phien",
                   "cach_bac_bo": "ky vong sau phi <= 0 tren nua sau cua mau thi bo"}]}


def _cp(d):
    return json.loads(json.dumps(d))


def test_kiem():
    assert P.kiem(TOT) == []
    x = _cp(TOT); x["co_che"] = "ngan"; x["khung"] = "nam"; x["dau_hieu_do"] = ["la"]
    assert len(P.kiem(x)) == 3
    x = _cp(TOT); x["suy_ra"][0]["chieu"] = 2
    assert P.kiem(x)


def test_diem_hai_chieu():
    tot = P.diem_dang_tien(TOT)["diem"]
    # tai lieu qua dep, khong phi, khong ngoai mau, khong co che -> thap han han
    x = _cp(TOT); x["loi_nhuan_cong_bo"] = {"pct_nam": 200.0, "sau_phi": False, "ngoai_mau": False}
    x["dau_hieu_do"] = ["khong_phi", "trong_mau", "khong_co_co_che"]
    assert P.diem_dang_tien(x)["diem"] < tot / 4
    # khong thu duoc tren lab (co phieu cat ngang, tick) va khong cho nao chuyen duoc -> 0
    y = _cp(TOT); y["lop_tai_san"] = "co_phieu"; y["du_lieu_can"] = ["co_phieu_cat_ngang"]; y["suy_ra"] = []
    assert P.diem_dang_tien(y)["kha_thi"] == 0 and P.diem_dang_tien(y)["diem"] == 0
    # co che chuyen duoc sang tai san lab co -> kha thi > 0 du ban goc khong thu duoc
    y["suy_ra"] = TOT["suy_ra"]
    assert P.diem_dang_tien(y)["kha_thi"] == 1.0
    # bao hoa: da thu nhieu loai nay -> moi giam
    assert P.diem_dang_tien(TOT, {"thanh_khoan": 80})["diem"] < tot


def test_so_va_hoc_nguoc():
    with tempfile.TemporaryDirectory() as t:
        so = Path(t) / "so.jsonl"
        for nguon, n_dat, n_am in (("a", 3, 0), ("b", 0, 3), ("c", 0, 0)):
            for i in range(n_dat + n_am + 1):
                x = _cp(TOT); x["suy_ra"][0]["bien_the_id"] = "%s#%d" % (nguon, i)
                P.ghi({"loai": "chan_doan", "tai_lieu_id": "%s%d" % (nguon, i) if i else nguon, "nguon": nguon, "the": x,
                       "diem": P.diem_dang_tien(x)}, so)
            # ghi ket qua cho cac bien the dau
            gap = 0
        # ket qua: nguon a - 3 DAT; nguon b - 3 AM
        for nguon, tt, n in (("a", "DAT", 3), ("b", "AM", 3)):
            for i in range(n):
                P.ghi_ket_qua("%s#%d" % (nguon, i), tt, so=so)
        r = {x["nguon"]: x for x in P.xep_nguon(so)}
        assert r["a"]["suat_tien"] > r["c"]["suat_tien"] > r["b"]["suat_tien"], r
        assert r["a"]["dat"] == 3 and r["b"]["am"] == 3
        # nguon chua co ket qua khong bi phat (suat tien nen = (0+1)/(0+10))
        assert abs(r["c"]["suat_tien"] - 0.1) < 1e-9
        bh = P.bai_hoc(so)
        assert bh and bh[0]["ty_le"] > bh[-1]["ty_le"] - 1e-9
        assert "thanh_khoan" in P.bai_hoc_van_ban(so)
        try:
            P.ghi_ket_qua("a#0", "TOT", so=so); assert False
        except ValueError:
            pass


def test_vong_sua_llm():
    dem = {"n": 0}

    def llm(he, nguoi):
        dem["n"] += 1
        if dem["n"] == 1:
            return "khong phai json"
        if dem["n"] == 2:
            x = _cp(TOT); x["khung"] = "nam"
            return json.dumps(x)
        return "```json\n" + json.dumps(TOT) + "\n```"
    kq = P.chan_doan("tai lieu", "n", llm, "t1", ghi_so=False)
    assert kq["the"] and kq["so_vong"] == 3 and kq["diem"]["diem"] > 0 and kq["the"]["suy_ra"][0]["bien_the_id"] == "t1#0"
    kq = P.chan_doan("tai lieu", "n", lambda h, n: "{}", "t2", ghi_so=False)
    assert kq["the"] is None and kq["loi"]


def test_xep_viec_bo_cho_khong_thu_duoc():
    with tempfile.TemporaryDirectory() as t:
        so = Path(t) / "so.jsonl"
        x = _cp(TOT); x["suy_ra"] = [dict(TOT["suy_ra"][0], bien_the_id="v#0"),
                                     dict(TOT["suy_ra"][0], bien_the_id="v#1", lop_tai_san="co_phieu")]
        P.ghi({"loai": "chan_doan", "tai_lieu_id": "v", "nguon": "n", "the": x, "diem": P.diem_dang_tien(x)}, so)
        ids = [v["bien_the_id"] for v in P.xep_viec(so)]
        assert ids == ["v#0"]
        P.ghi_ket_qua("v#0", "AM", so=so)
        assert P.xep_viec(so) == []


def test_viec_luoi():
    b = {"bien_the_id": "t#1", "lop_tai_san": "kim_loai", "khung": "phut", "vi_sao_tra_tien": "vang hoi quy o moi thang do"}
    j = P.viec_luoi(b)
    a = json.loads(j["lenh"][-1])
    assert a["ma"] == "XAUUSDM" and a["khung"] == "M15" and j["lenh"][4] == "quet_luoi" and a["luoi"]["che_do"] == ["mua", "ban"]
    assert P.viec_luoi(dict(b, lop_tai_san="co_phieu")) is None and P.viec_luoi(dict(b, khung="tick")) is None


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v(); print("ok", k)
