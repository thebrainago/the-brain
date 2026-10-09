import json

import pytest

from nhan import doi_chieu_mo_phong as DC


def _bao_cao(q, lai_e, swap_e, lai_t, ngay=365.25, von=10000.0, ma="AUDCAD", khung="M15", tu="2019.01.01", den="2019.12.31", pb=3):
    """Phan cua bao cao `reports/hieu_chuan/*.json` ma doc_day_du can (lai_* la TIEN, khong phai %)."""
    return {"ma": ma, "khung": khung, "von": von, "phien_ban_engine": pb,
            "cua_so": {"tu": tu, "den": den, "ngay": ngay},
            "tester": {"chat_luong_pct": q, "thong_ke": {"lai_chua_swap": lai_t, "swap": 0.0}},
            "engine": {"thong_ke": {"lai_chua_swap": lai_e, "swap": swap_e}}}


def _don(thu_muc, ten, so_khoa, bao_cao_json, duong="reports/hieu_chuan/A_e3.json", luc="2026-10-08T10:00:00",
         lenh=("{py}", "b.py", "nc", "cc", "hieu_chuan_luoi", "{}"), co_duong=True, co_tep=True):
    dong_cuoi = ' "so_khoa": [%s], "tn_id": 1' % ", ".join(str(x) for x in so_khoa)
    if co_duong:
        dong_cuoi = ' "bao_cao": "%s",' % duong + dong_cuoi
    bc = {"lenh": list(lenh), "dong_cuoi": [dong_cuoi],
          "tep_moi": ({duong: json.dumps(bao_cao_json)} if co_tep else {})}
    (thu_muc / ("%s.json" % ten)).write_text(json.dumps({"ma": ten, "luc": luc, "bang_chung": bc}), "utf-8")


@pytest.fixture
def xong(tmp_path):
    return tmp_path


def _so_khoa(e=5.0, t=4.0, de=10.0, dt=10.0, ne=50, nt=50):
    return [e, t, de, dt, ne, nt]


def test_doc_day_du_doi_lai_tien_ra_phan_tram_nam_truoc_swap(xong):
    # ngay=365.25 -> dung 1 nam: lai tien 700 tren von 10.000 = 7 %/nam; swap -300 = -3 %/nam
    _don(xong, "j1-hc-AUDCAD-H1-k0", _so_khoa(4.0, 5.0, 11.0, 12.0, 61, 62), _bao_cao(100.0, 700.0, -300.0, 500.0))
    (r,) = DC.doc_day_du(str(xong))
    assert r["e_truoc"] == pytest.approx(7.0)
    assert r["t_truoc"] == pytest.approx(5.0)
    assert r["swap_e"] == pytest.approx(-3.0)
    assert (r["q"], r["ma"], r["khung"], r["pb"]) == (100.0, "AUDCAD", "M15", 3)
    assert (r["engine"], r["tester"], r["dd_e"], r["dd_t"], r["n_e"], r["n_t"]) == (4.0, 5.0, 11.0, 12.0, 61.0, 62.0)


def test_doc_day_du_nua_nam_nhan_len_hai_lan(xong):
    # cua so 182,625 ngay = nua nam: cung lai tien thi %/nam gap doi
    _don(xong, "j1", _so_khoa(), _bao_cao(100.0, 350.0, 0.0, 200.0, ngay=182.625))
    (r,) = DC.doc_day_du(str(xong))
    assert r["e_truoc"] == pytest.approx(7.0)
    assert r["t_truoc"] == pytest.approx(4.0)


def test_doc_day_du_chi_lay_don_hieu_chuan_luoi(xong):
    _don(xong, "khac", _so_khoa(), _bao_cao(100.0, 1.0, 0.0, 1.0), lenh=("{py}", "b.py", "nc", "cc", "quet_luoi", "{}"))
    _don(xong, "dung", _so_khoa(), _bao_cao(100.0, 1.0, 0.0, 1.0), duong="reports/hieu_chuan/B_e3.json")
    assert [r["job"] for r in DC.doc_day_du(str(xong))] == ["dung"]


def test_doc_day_du_bo_don_khong_co_so_khoa_hoac_khong_co_duong_bao_cao(xong):
    _don(xong, "thieu_duong", _so_khoa(), _bao_cao(100.0, 1.0, 0.0, 1.0), co_duong=False)
    (xong / "hong.json").write_text("{khong phai json", "utf-8")
    (xong / "khong_so_khoa.json").write_text(json.dumps({"ma": "x", "bang_chung": {"lenh": ["hieu_chuan_luoi"], "dong_cuoi": ["chet"]}}), "utf-8")
    assert DC.doc_day_du(str(xong)) == []


@pytest.mark.parametrize("nguoc", [False, True])
def test_doc_day_du_cung_bao_cao_chay_hai_lan_giu_lan_moi_nhat(xong, monkeypatch, nguoc):
    _don(xong, "a-cu", _so_khoa(1.0, 1.0), _bao_cao(100.0, 100.0, 0.0, 100.0), luc="2026-10-07T10:00:00")
    _don(xong, "b-moi", _so_khoa(2.0, 2.0), _bao_cao(100.0, 200.0, 0.0, 200.0), luc="2026-10-08T10:00:00")
    _don(xong, "c-nhat-ten-nhung-cu", _so_khoa(3.0, 3.0), _bao_cao(100.0, 300.0, 0.0, 300.0), luc="2026-10-06T10:00:00")
    thuc = DC.glob.glob
    monkeypatch.setattr(DC.glob, "glob", lambda p: sorted(thuc(p), reverse=nguoc))      # thu tu thu muc khong duoc anh huong ket qua
    rows = DC.doc_day_du(str(xong))
    assert [r["job"] for r in rows] == ["b-moi"]
    assert rows[0]["engine"] == 2.0


def test_thieu_bao_cao_trong_tep_moi_chat_luong_chua_ro_va_khong_co_so_truoc_swap(xong):
    _don(xong, "j1", _so_khoa(3.0, 2.0), _bao_cao(100.0, 1.0, 0.0, 1.0), co_tep=False)
    (r,) = DC.doc_day_du(str(xong))
    assert r["q"] is None and r["e_truoc"] is None and r["t_truoc"] is None
    assert (r["engine"], r["tester"]) == (3.0, 2.0)             # so_khoa van doc duoc
    assert DC.phan_nhom([r])["chua_ro"] == [r]
    assert DC.so_nhom([r], truoc_swap=True) == {"n": 0}          # khong co so truoc swap -> khong dem
    assert DC.so_nhom([r], truoc_swap=False)["n"] == 1


def test_bao_cao_json_hop_le_nhung_khong_phai_doi_tuong_khong_lam_chet_ca_lo(xong):
    _don(xong, "j1", _so_khoa(3.0, 2.0), [1, 2, 3])
    (r,) = DC.doc_day_du(str(xong))
    assert r["q"] is None and r["e_truoc"] is None


def test_so_nhom_bo_hang_thieu_mot_trong_hai_so_truoc_swap():
    thieu_t = dict(_r(1, 1), t_truoc=None)
    thieu_e = dict(_r(1, 1), e_truoc=None)
    du = _r(2, 1)
    assert DC.so_nhom([thieu_t, thieu_e, du])["n"] == 1


@pytest.mark.parametrize("q,nhom", [(100.0, "sach"), (95.0, "sach"), (94.9, "nhiem"), (51.0, "nhiem"), (1.0, "nhiem"), (0.0, "nhiem"), (None, "chua_ro")])
def test_phan_nhom_theo_nguong_chat_luong(q, nhom):
    r = {"q": q}
    kq = DC.phan_nhom([r])
    assert kq[nhom] == [r]
    assert sum(len(v) for v in kq.values()) == 1


def _r(e, t, e_truoc=None, t_truoc=None, de=10.0, dt=10.0, ne=50, nt=50, q=100.0):
    return {"engine": e, "tester": t, "e_truoc": e if e_truoc is None else e_truoc, "t_truoc": t if t_truoc is None else t_truoc,
            "dd_e": de, "dd_t": dt, "n_e": ne, "n_t": nt, "q": q}


def test_so_nhom_dem_dau_va_do_lech():
    rows = [_r(10, 5), _r(4, 8), _r(3, -2), _r(-1, 2), _r(-4, -6), _r(0, 0), _r(2, 0), _r(0, 3), _r(8, 2)]
    kq = DC.so_nhom(rows)
    assert kq["n"] == 9
    # cung dau (duong/duong, khong-duong/khong-duong): (10,5) (4,8) (-4,-6) (0,0) = 4 ; khac: (3,-2) (-1,2) (2,0) (0,3)
    assert kq["cung_dau"] == 5                                   # them (8, 2)
    assert kq["engine_duong_tester_khong"] == 2                  # (3, -2) va (2, 0): tester = 0 tinh la KHONG lai
    assert kq["engine_khong_tester_duong"] == 2                  # (-1, 2) va (0, 3): engine = 0 tinh la KHONG lai
    assert kq["tester_duong"] == 5                               # 5, 8, 2, 3, 2
    # e - t = 5, -4, 5, -3, 2, 0, 2, -3, 6 -> sap xep -4 -3 -3 0 2 2 5 5 6 -> trung vi 2 (trung binh 1,22)
    assert kq["lech_trung_vi"] == 2.0
    # |e - t| = 5 4 5 3 2 0 2 3 6 -> trung binh 30 / 9 = 3,33 (trung vi 3)
    assert kq["sai_so_tb"] == 3.33
    # ti le chi tinh khi ca hai duong: 10/5 = 2 ; 4/8 = 0,5 ; 8/2 = 4 -> trung vi 2 (trung binh 2,17)
    assert kq["ti_le_trung_vi"] == 2.0


def test_so_nhom_ti_le_lenh_va_dd_bo_dd_tester_nho():
    rows = [_r(1, 1, ne=75, nt=50, de=30.0, dt=10.0), _r(1, 1, ne=60, nt=50, de=15.0, dt=10.0), _r(1, 1, ne=55, nt=50, de=3.0, dt=0.5),
            _r(1, 1, ne=100, nt=50, de=12.0, dt=10.0)]
    kq = DC.so_nhom(rows)
    assert kq["ti_le_lenh_trung_vi"] == 1.35                     # 1,5 ; 1,2 ; 1,1 ; 2,0 -> trung vi (1,2 + 1,5) / 2
    assert kq["ti_le_dd_trung_vi"] == 1.5                        # chi 3 hang co DD tester > 1: 3,0 ; 1,5 ; 1,2
    for dt in (0.5, 1.0):                                        # DD tester <= 1 %: ti le vo nghia, khong dem (ke ca dung 1,0)
        assert DC.so_nhom([_r(1, 1, de=3.0, dt=dt)])["ti_le_dd_trung_vi"] is None
    assert DC.so_nhom([_r(-1, -1)])["ti_le_trung_vi"] is None   # khong hang nao duong/duong


def test_so_nhom_truoc_swap_va_so_khoa_cho_hai_con_so_khac_nhau():
    # so_khoa: engine 3 (SAU swap), tester 5 ; TRUOC swap: engine 8, tester 5 -> engine lac quan khi bo swap
    r = _r(3.0, 5.0, e_truoc=8.0, t_truoc=5.0)
    assert DC.so_nhom([r], truoc_swap=True)["lech_trung_vi"] == 3.0
    assert DC.so_nhom([r], truoc_swap=False)["lech_trung_vi"] == -2.0


def test_so_nhom_rong():
    assert DC.so_nhom([]) == {"n": 0}


def test_doc_cu_van_chay_voi_ten_hc_luoi(xong):
    _don(xong, "7-hc-luoi-AUDCAD", _so_khoa(6.0, 3.0, 12.0, 11.0), _bao_cao(100.0, 1.0, 0.0, 1.0))
    mau, hong = DC.doc(str(xong))
    assert mau == {"7-hc-luoi-AUDCAD": (6.0, 3.0, 12.0, 11.0)}
    assert hong == []


def test_in_theo_chat_luong_tach_o_sach_va_o_nhiem(xong):
    _don(xong, "s1", _so_khoa(4.0, 5.0), _bao_cao(100.0, 700.0, -300.0, 500.0), duong="reports/hieu_chuan/S_e3.json")
    _don(xong, "n1", _so_khoa(9.0, 5.0), _bao_cao(51.0, 900.0, -300.0, 500.0), duong="reports/hieu_chuan/N_e3.json")
    dong = []
    rows = DC.in_theo_chat_luong(str(xong), out=dong.append)
    assert len(rows) == 2
    assert "sach 1, nhiem 1, chua ro 0" in dong[0]
    sach = [d for d in dong if d.startswith("sach ") and "TRUOC swap" in d]
    nhiem = [d for d in dong if d.startswith("nhiem ") and "TRUOC swap" in d]
    assert len(sach) == 1 and '"lech_trung_vi": 2.0' in sach[0]       # 7 - 5
    assert len(nhiem) == 1 and '"lech_trung_vi": 4.0' in nhiem[0]     # 9 - 5


def test_hang_so_nguong_nhat_quan_voi_bao_cao():
    # 2019 = 100 % (sach), 2018-H2 = 51 % (nhiem): nguong phai nam giua
    assert 51.0 < DC.NGUONG_CHAT_LUONG <= 100.0
    assert DC.NGUONG_CAT == -10.0                                # luat loc cu khong bi doi am tham
