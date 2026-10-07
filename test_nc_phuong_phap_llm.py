from nhan import nc_phuong_phap as NCP


def _tt(ma="X", kp=60, a=1.0, c=1.0, pip=0.0001, pv=10.0, von=1000.0):
    return {"ma": ma, "khung_phut": kp, "A": a, "C": c, "pip": pip, "pv": pv, "von": von}


def test_thi_truong_hop_le():
    d = _tt()
    tt = NCP._thi_truong(d, "test")
    assert tt.ma == "X"
    assert tt.khung_phut == 60.0
    assert tt.A == 1.0
    assert tt.do_tin_chi_phi == "KHAI"
    assert tt.lot_toi_thieu == 0.01
    assert tt.lot_buoc == 0.01


def test_thi_truong_khong_phai_dict():
    r = None
    try:
        NCP._thi_truong("chuoi", "nguon")
    except ValueError as e:
        r = str(e)
    assert r is not None
    assert "phai la dict" in r


def test_thi_truong_thieu_khoa():
    d = {"ma": "X"}
    r = None
    try:
        NCP._thi_truong(d, "dich")
    except ValueError as e:
        r = str(e)
    assert r is not None
    assert "thieu" in r
    assert "khung_phut" in r


def test_bao_bat_value_error():
    @NCP._bao
    def ham_loi(**kw):
        raise ValueError("loi roi")

    kq = ham_loi(vong_id=1)
    assert kq["trang_thai"] == "CHUA_DO_DUOC"
    assert kq["loi"] == "loi roi"


def test_bao_bat_file_not_found():
    @NCP._bao
    def ham_fnf(**kw):
        raise FileNotFoundError("khong thay")

    kq = ham_fnf()
    assert kq["trang_thai"] == "CHUA_DO_DUOC"
    assert "khong thay" in kq["loi"]


def test_bao_khong_loi_tra_ket_qua():
    @NCP._bao
    def ham_ok(**kw):
        return {"ok": True}

    kq = ham_ok(vong_id=99)
    assert kq == {"ok": True}


def test_luu_the_hong_tra_chua_do_duoc():
    the_hong = {"ma": "x"}
    kq = NCP._bao(NCP._luu_the)(the=the_hong)
    assert kq["trang_thai"] == "CHUA_DO_DUOC"
    assert "the hong" in kq["loi"]
    assert "thieu khoa" in kq["loi"]


def test_luu_the_none_tra_loi():
    kq = NCP._bao(NCP._luu_the)(the=None)
    assert kq["trang_thai"] == "CHUA_DO_DUOC"
    assert "loi" in kq


def test_chuyen_bot_the_khong_ton_tai():
    kq = NCP._bao(NCP._chuyen_bot)(
        the_ma="khong_ton_tai_xyz", gia_tri={}, nguon=_tt(), dich=_tt("Y")
    )
    assert kq["trang_thai"] == "CHUA_DO_DUOC"
    assert "No such file" in kq["loi"] or "khong_ton_tai_xyz" in kq["loi"]


def test_ke_hoach_do_dich_ds_rong():
    kq = NCP._bao(NCP._ke_hoach_do)(
        the_ma="khong_ton_tai_xyz", gia_tri={}, nguon=_tt(), dich_ds=[]
    )
    assert kq["trang_thai"] == "CHUA_DO_DUOC"
    assert "loi" in kq


def test_ke_hoach_do_dich_ds_khong_phai_list():
    kq = NCP._bao(NCP._ke_hoach_do)(
        the_ma="khong_ton_tai_xyz", gia_tri={}, nguon=_tt(), dich_ds="chuoi"
    )
    assert kq["trang_thai"] == "CHUA_DO_DUOC"
    assert "loi" in kq


def test_quet_o_the_khong_ton_tai():
    kq = NCP._bao(NCP._quet_o)(the_ma="khong_ton_tai_xyz", o="buoc")
    assert kq["trang_thai"] == "CHUA_DO_DUOC"
    assert "No such file" in kq["loi"] or "khong_ton_tai_xyz" in kq["loi"]


def test_cmt_loc_thieu_khai_bao():
    kq = NCP._bao(NCP._cmt_loc)(khai_bao=None, kho=False)
    assert kq["trang_thai"] == "CHUA_DO_DUOC"
    assert "can `khai_bao`" in kq["loi"]


def test_cmt_loc_khai_bao_rong():
    kq = NCP._bao(NCP._cmt_loc)(khai_bao=[], kho=False)
    assert kq["trang_thai"] == "CHUA_DO_DUOC"
    assert "can `khai_bao`" in kq["loi"]


def test_cmt_loc_khai_bao_khong_phai_list():
    kq = NCP._bao(NCP._cmt_loc)(khai_bao="chuoi", kho=False)
    assert kq["trang_thai"] == "CHUA_DO_DUOC"
    assert "can `khai_bao`" in kq["loi"]


def test_cong_cu_co_du_6_muc():
    assert len(NCP.CONG_CU) == 6
    ten = [c[0] for c in NCP.CONG_CU]
    assert "luu_the" in ten
    assert "chuyen_bot" in ten
    assert "ke_hoach_do" in ten
    assert "quet_o" in ten
    assert "thu_chuyen" in ten
    assert "cmt_loc" in ten
