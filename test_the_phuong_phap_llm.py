import inspect
from nhan import the_phuong_phap as T
from nhan import dich_tham_so as DTS


def _the_hop_le():
    return {
        "ma": "abc",
        "loai": "VAO",
        "ten": "Test",
        "mo_ta": "Mo ta test",
        "tham_so": [{"ten": "buoc", "lop": DTS.KC_BUOC, "don_vi": "pip", "mien": [50, 400, 25], "ten_trong_set": None, "ten_trong_engine": None}],
        "can": [],
        "xung_dot": [],
        "tuong_tac_biet": [],
        "vet": ["v1"],
        "engine": {"trang_thai": "chua_ro"},
        "nguon": [],
        "dieu_kien_dung": []
    }


def test_kiem_the_hop_le_tra_rong():
    the = _the_hop_le()
    assert T.kiem_the(the) == []


def test_kiem_the_khong_phai_dict():
    loi = T.kiem_the("chuoi")
    assert "the phai la dict" in loi


def test_kiem_the_thieu_khoa():
    the = _the_hop_le()
    del the["ma"]
    loi = T.kiem_the(the)
    assert any("thieu khoa 'ma'" in x for x in loi)


def test_kiem_the_ma_khong_hop_le():
    the = _the_hop_le()
    the["ma"] = "AB"
    loi = T.kiem_the(the)
    assert any("khong hop le" in x for x in loi)

    the["ma"] = "1abc"
    loi = T.kiem_the(the)
    assert any("khong hop le" in x for x in loi)

    the["ma"] = "a" * 65
    loi = T.kiem_the(the)
    assert any("khong hop le" in x for x in loi)


def test_kiem_the_loai_sai():
    the = _the_hop_le()
    the["loai"] = "SAI_LOAI"
    loi = T.kiem_the(the)
    assert any("loai" in x and "khong thuoc" in x for x in loi)


def test_kiem_the_ten_mo_ta_rong():
    the = _the_hop_le()
    the["ten"] = "   "
    loi = T.kiem_the(the)
    assert any("ten / mo_ta rong" in x for x in loi)

    the["ten"] = "Ok"
    the["mo_ta"] = ""
    loi = T.kiem_the(the)
    assert any("ten / mo_ta rong" in x for x in loi)


def test_kiem_the_tham_so_trung_ten():
    the = _the_hop_le()
    o = {"ten": "buoc", "lop": DTS.KC_BUOC, "don_vi": "pip", "mien": None, "ten_trong_set": None, "ten_trong_engine": None}
    the["tham_so"] = [o, dict(o)]
    loi = T.kiem_the(the)
    assert any("trung ten" in x for x in loi)


def test_kiem_the_mien_sai_dinh_dang():
    the = _the_hop_le()
    the["tham_so"][0]["mien"] = [10, 5, 1]
    loi = T.kiem_the(the)
    assert any("mien phai la" in x for x in loi)

    the["tham_so"][0]["mien"] = [1, 10, 0]
    loi = T.kiem_the(the)
    assert any("mien phai la" in x for x in loi)

    the["tham_so"][0]["mien"] = [1, 10]
    loi = T.kiem_the(the)
    assert any("mien phai la" in x for x in loi)


def test_kiem_the_engine_trang_thai_sai():
    the = _the_hop_le()
    the["engine"] = {"trang_thai": "sai"}
    loi = T.kiem_the(the)
    assert any("engine.trang_thai" in x for x in loi)


def test_kiem_the_danh_sach_khong_phai_list():
    the = _the_hop_le()
    the["can"] = "khong_phai_list"
    loi = T.kiem_the(the)
    assert any("'can' phai la danh sach" in x for x in loi)


def test_o_tu_ten_tra_dung_cau_truc():
    o = T._o_tu_ten("buoc")
    assert o["ten"] == "buoc"
    assert "lop" in o
    assert "don_vi" in o
    assert o["mien"] is None
    assert o["ten_trong_set"] is None
    assert o["ten_trong_engine"] is None


def test_thay_so_o_la_raise_value_error():
    sig = inspect.signature(DTS.ThiTruong.__init__)
    params = list(sig.parameters.keys())
    if "von" not in params:
        return
    args = {}
    for p in params:
        if p == "self":
            continue
        ann = sig.parameters[p].annotation
        if ann is str or ann == "str":
            args[p] = "x"
        else:
            args[p] = 1.0
    src = DTS.ThiTruong(**args)
    dst = DTS.ThiTruong(**args)
    the = _the_hop_le()
    try:
        T.thay_so(the, {"o_la": 10}, src, dst)
        assert False, "phai raise ValueError"
    except ValueError as e:
        assert "o khong co trong the" in str(e)
