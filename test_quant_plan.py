# -*- coding: utf-8 -*-
"""QUANT PLAN — hop dong dang ky truoc, va cai chua ai cam vao o dau.

`nhan/quant_plan.py` la ban dac ta chat che nhat cua bat bien PRE-REGISTRATION:
mot ke hoach dong bang CA template, tham so, pham vi ap dung, khong gian tim
kiem, bang chung, VA luat quyet dinh - roi bam thanh mot `plan_hash` dia chi
theo noi dung. Doi bat ky manh nao la mot gia thuyet KHAC.

PHAT HIEN 30/08/2026, ghi lai o day de khong ai quen:

    `tru/quantlab.py` **import `quant_plan` nhung khong goi mot ham nao cua no**.
    Docstring cua chinh no viet "Both lanes freeze a full QuantPlan before a
    result", nhung duong dang ky that di qua `so.dang_ky_gia_thuyet`, va
    plan_hash o do chi phu: co che + template + tham so + tai san + khung +
    cua so. **Thieu LUAT QUYET DINH va KHONG GIAN TIM KIEM.**

    Hau qua: doi luat quyet dinh, hoac noi rong luoi tham so da quet, KHONG lam
    doi plan_hash - tuc hai phep thu khac han nhau van mang cung mot danh tinh
    gia thuyet. `PLAN_DIR = REPORTS / "quant_plans"` cung chua bao gio duoc tao.

Day la khoang trong THIET KE, khong phai loi mot dong, nen phien nay khong tu y
noi day. Nhung module thi phai duoc khoa hanh vi truoc da: neu sau nay noi vao
that, khong duoc phep noi vao mot thu dang hong.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import quant_plan as QP   # noqa: E402


H64 = "a" * 64          # cho vao cho doi chuoi sha256 hop le


def _ke_hoach(**doi) -> QP.QuantPlan:
    tham_so = doi.pop("parameters", {"nguong": 0.2, "giu_bar": 1})
    template = doi.pop("template", "ibs_bat_day")
    goc = {
        "lane": "autonomous_discovery",
        "origin": {"kind": "template_sweep", "producer": "quantlab",
                   "reference": "kham_pha_theo_mau"},
        "strategy": QP.strategy_spec(template, QP.sha256_json(template), tham_so),
        "scope": {"assets": ["EURCAD"], "timeframes": ["D1"],
                  "applicability": {"lop_tai_san": "fx"}},
        "search": {"batch_id": "lo-2026-08-30", "family": "quay_ve_trung_binh",
                   "max_trials": 3},
        "evidence": {
            "data_release_id": H64, "cost_snapshot_id": H64,
            "cost_model_generation": 2,
            "train_window": {"start": "2015-01-01", "end": "2021-12-31"},
            "confirmation_window": {"start": "2022-01-01", "end": "2026-06-30"},
            "confirmation_status": "clean_unseen"},
        "decision_rule": {
            "generation": 4, "min_trades": 30,
            "primary_p": {"metric": "p_alpha", "maximum": 0.05},
            "primary_effect": {"metric": "alpha_nam_pct", "minimum": 1.0,
                               "unit": "phan_tram_nam"}},
    }
    goc.update(doi)
    return QP.QuantPlan(**goc)


class PlanHashDiaChiTheoNoiDung(unittest.TestCase):

    def test_cung_noi_dung_thi_cung_hash(self):
        self.assertEqual(_ke_hoach().plan_hash, _ke_hoach().plan_hash)

    def test_thu_tu_khai_bao_tham_so_khong_lam_doi_hash(self):
        a = _ke_hoach(parameters={"nguong": 0.2, "giu_bar": 1})
        b = _ke_hoach(parameters={"giu_bar": 1, "nguong": 0.2})
        self.assertEqual(a.plan_hash, b.plan_hash,
                         "hash phu thuoc thu tu khoa - khong con la dia chi noi dung")

    def test_doi_tham_so_thi_doi_hash(self):
        a = _ke_hoach()
        b = _ke_hoach(parameters={"nguong": 0.3, "giu_bar": 1})
        self.assertNotEqual(a.plan_hash, b.plan_hash)

    def test_doi_LUAT_QUYET_DINH_thi_doi_hash(self):
        """Chinh cho ma plan_hash cua `so.dang_ky_gia_thuyet` khong phu."""
        a = _ke_hoach()
        b = _ke_hoach(decision_rule={
            "generation": 5, "min_trades": 30,
            "primary_p": {"metric": "p_alpha", "maximum": 0.05},
            "primary_effect": {"metric": "alpha_nam_pct", "minimum": 1.0,
                               "unit": "phan_tram_nam"}})
        self.assertNotEqual(
            a.plan_hash, b.plan_hash,
            "doi the he cong ma plan_hash khong doi - hai luat quyet dinh khac "
            "nhau mang cung mot danh tinh gia thuyet")

    def test_noi_rong_KHONG_GIAN_TIM_KIEM_thi_doi_hash(self):
        a = _ke_hoach()
        b = _ke_hoach(search={"batch_id": "lo-2026-08-30",
                              "family": "quay_ve_trung_binh", "max_trials": 5})
        self.assertNotEqual(
            a.plan_hash, b.plan_hash,
            "quet 5 diem thay vi 3 ma van cung hash - da nhieu phep thu hon "
            "nhung khong khai bao")

    def test_doi_cua_so_train_thi_doi_hash(self):
        a = _ke_hoach()
        b = _ke_hoach(evidence={
            "data_release_id": H64, "cost_snapshot_id": H64,
            "cost_model_generation": 2,
            "train_window": {"start": "2016-01-01", "end": "2021-12-31"},
            "confirmation_window": {"start": "2022-01-01", "end": "2026-06-30"},
            "confirmation_status": "clean_unseen"})
        self.assertNotEqual(a.plan_hash, b.plan_hash)


class KeHoachLaBatBien(unittest.TestCase):

    def test_khong_gan_lai_duoc_truong(self):
        kh = _ke_hoach()
        with self.assertRaises(Exception):
            kh.lane = "candidate_validation"

    def test_khong_sua_duoc_tham_so_ben_trong(self):
        kh = _ke_hoach()
        with self.assertRaises(Exception):
            kh.strategy["parameters"]["nguong"] = 0.9


class TuChoiKeHoachHONG(unittest.TestCase):

    def test_lane_la_khong_hop_le(self):
        with self.assertRaises(QP.QuantPlanError):
            _ke_hoach(lane="lane_bia_ra")

    def test_hash_tham_so_khong_khop_thi_bi_tu_choi(self):
        spec = QP.strategy_spec("ibs_bat_day", QP.sha256_json("ibs_bat_day"),
                                {"nguong": 0.2})
        gia = dict(spec)
        gia["parameters"] = {"nguong": 0.9}      # doi tham so, giu hash cu
        with self.assertRaises(QP.QuantPlanError):
            _ke_hoach(strategy=gia)

    def test_truong_la_bi_tu_choi(self):
        with self.assertRaises(QP.QuantPlanError):
            _ke_hoach(origin={"kind": "template_sweep", "producer": "quantlab",
                              "reference": "kham_pha_theo_mau",
                              "them_mot_truong_la": 1})

    def test_schema_version_khac_bi_tu_choi(self):
        with self.assertRaises(QP.QuantPlanError):
            _ke_hoach(schema_version=QP.SCHEMA_VERSION + 1)


class DiQuaJsonVanGiuNguyenDanhTinh(unittest.TestCase):

    def test_to_dict_roi_from_dict_giu_nguyen_hash(self):
        kh = _ke_hoach()
        lai = QP.QuantPlan.from_dict(kh.to_dict())
        self.assertEqual(lai.plan_hash, kh.plan_hash)

    def test_di_qua_json_giu_nguyen_hash(self):
        kh = _ke_hoach()
        lai = QP.QuantPlan.from_json(QP.canonical_json(kh.to_dict()))
        self.assertEqual(lai.plan_hash, kh.plan_hash)


class ChuaAiNoiVaoDayChuyen(unittest.TestCase):
    """Khoa lai PHAT HIEN, de khi ai do noi that thi bai kiem nay do va bi go.

    Day khong phai mot bai kiem "hanh vi dung"; no la mot cai moc. Neu
    `quantlab` bat dau dong bang QuantPlan that thi test nay se do, va nguoi sua
    phai doc lai docstring dau file de biet vi sao no tung ton tai.
    """

    def test_quantlab_van_chua_goi_ham_nao_cua_quant_plan(self):
        van = (Path(LAB) / "tru" / "quantlab.py").read_text(encoding="utf-8")
        goi = [d for d in van.splitlines()
               if "QP." in d and not d.lstrip().startswith("#")]
        self.assertEqual(
            goi, [],
            "quantlab da bat dau goi quant_plan - go bai kiem nay va cap nhat "
            "docstring dau file:\n  " + "\n  ".join(goi))


if __name__ == "__main__":
    unittest.main()
