# -*- coding: utf-8 -*-
"""nhan/khoi_co_che.py - kho khoi co che cua cac con bot (bot = to hop khoi; khoi dung chung de thu ap cheo).

Du lieu cua kho la KIEN THUC TRUOC SO LIEU (loi tac gia, bo .set, thong bao) nen khong co "dap an dung" de so. Bai test chi
bat duoc cac loi CO THE bat:
  * du lieu tu mau thuan (khoi khong ton tai, muc la, khoi mo coi, he cua ta khong khop engine) - va chinh bo kiem tra phai bat
    duoc cac loi do (gieo loi co y);
  * kho noi dung sai ve ENGINE: khoi ghi 'engine co' ma truong `luoi.ThamSo` khong ton tai / chua duoc cai dat;
  * bo xep thu tu / de xuat tren catalog NHO tu dung voi dap an biet truoc;
  * bo phan loai ten tham so `.set` tren ten that cua CCBSN, kem cac bay da gap (MaxLots chua 'xLot', ATR trong 'Matrix');
  * tai lieu sinh tu ma khop tep da commit (khong bao gio cu).
Khong kiem duoc: chat luong cua tung khoi (co that so bot dung no hay khong) - do la viec cua `ho_so_bot` tren lich su lenh that.
"""
from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pytest

from nhan import khoi_co_che as KC
from nhan import luoi as L

LAB = Path(__file__).resolve().parent


# ========================================================================== du lieu tu nhat quan
def test_du_lieu_nhat_quan():
    assert KC.kiem_tinh_nhat_quan() == []


def test_moi_nhom_co_khoi_va_moi_khoi_co_nhom():
    dung = {k.nhom for k in KC.KHOI_DS}
    assert dung == set(KC.NHOM)
    assert len(KC.KHOI) == len(KC.KHOI_DS) and len(KC.BOT) == len(KC.BOT_DS)


def test_dac_ta_khop_ket_qua_that_thu_nha():
    """Con so tu thu 60fa / 6487 (Model 1 / Model 4): neu ai sua kho thi cac moc nay khong duoc vo tinh mat."""
    assert KC.bot_song_sot() == ["ccbsn"]   # cap nhat khi co bot thu hai qua xac nhan
    kq = KC.BOT["ccbsn"].ket_qua
    for moc in ("+4923", "1467", "+5939", "0% tick", "2021-10-13..2024-04-07"):
        assert moc in kq, moc
    assert "Black Dragon" in KC.BOT["black_dragon"].ten and "chay het tai khoan" in KC.BOT["black_dragon"].ket_qua


# ========================================================================== bo kiem tinh phai bat duoc loi co y
@pytest.fixture
def tam(monkeypatch):
    """Cho test sua kho tam thoi (monkeypatch tra lai nguyen ven sau moi test)."""
    return monkeypatch


def _khoi_mau(ma="khoi_mau", engine="chua", nhom="LOC", **kw):
    d = dict(ma=ma, nhom=nhom, ten="Ten", mo_ta="Mo ta", tham_so=(), dau_van_tay="dau van tay", kiem=None, engine=engine,
             engine_ghi_chu="ghi chu", ap_cheo="ap cheo", rui_ro="rui ro")
    d.update(kw)
    return KC.Khoi(**d)


def _them_khoi(tam, k):
    tam.setattr(KC, "KHOI_DS", KC.KHOI_DS + [k])
    tam.setitem(KC.KHOI, k.ma, k)


@pytest.mark.parametrize("ten_loi, sua", [
    ("bot tro khoi khong ton tai",
     lambda t: t.setitem(KC.BOT["ccbsn"].khoi, "khoi_khong_co", ("knob", "x"))),
    ("muc bang chung la",
     lambda t: t.setitem(KC.BOT["ccbsn"].khoi, "loc_spread", ("tin_don", "x"))),
    ("bot ngoai dung muc ma_nguon",
     lambda t: t.setitem(KC.BOT["ccbsn"].khoi, "loc_spread", ("ma_nguon", "x"))),
    ("he cua ta dung muc khac ma_nguon",
     lambda t: t.setitem(KC.BOT["luoi_cua_ta"].khoi, "mot_chieu", ("video", "x"))),
    ("he cua ta thieu mot khoi engine=co",
     lambda t: t.delitem(KC.BOT["luoi_cua_ta"].khoi, "lot_nhan")),
    ("he cua ta co khoi ma engine khong co",
     lambda t: t.setitem(KC.BOT["luoi_cua_ta"].khoi, "all_sniper", ("ma_nguon", "x"))),
    ("loi khuyen tro bot la",
     lambda t: t.setattr(KC, "LOI_KHUYEN_VAN_HANH", KC.LOI_KHUYEN_VAN_HANH + [("a", "bot_la", "loc_spread", "c")])),
    ("loi khuyen tro khoi la",
     lambda t: t.setattr(KC, "LOI_KHUYEN_VAN_HANH", KC.LOI_KHUYEN_VAN_HANH + [("a", "nuti", "khoi_la", "c")])),
    ("LOAI_TRU tro khoi la",
     lambda t: t.setattr(KC, "LOAI_TRU", KC.LOAI_TRU + (("lot_phang", "khoi_la"),))),
    ("_TRUONG_ENGINE tro khoi la",
     lambda t: t.setitem(KC._TRUONG_ENGINE, "khoi_la", ("buoc",))),
])
def test_kiem_tinh_bat_loi_co_y(tam, ten_loi, sua):
    sua(tam)
    assert KC.kiem_tinh_nhat_quan(), "bo kiem khong bat duoc: " + ten_loi


def test_kiem_bat_khoi_mo_coi_nhom_la_ma_la(tam):
    # khoi khong bot nao dung va engine khong co -> mo coi
    _them_khoi(tam, _khoi_mau("khoi_mo_coi"))
    assert any("mo coi" in e and "khoi_mo_coi" in e for e in KC.kiem_tinh_nhat_quan())
    tam.undo()
    # nhom la / engine la / ma sai dang / thieu mo ta
    for kw, mau in (({"nhom": "NHOM_LA"}, "nhom la"), ({"engine": "engine_la"}, "engine la"),
                    ({"ma": "KhoiHoa"}, "snake_case"), ({"mo_ta": "  "}, "thieu mo_ta")):
        _them_khoi(tam, _khoi_mau(**{"ma": "khoi_sai", **kw}))
        assert any(mau in e for e in KC.kiem_tinh_nhat_quan()), mau
        tam.undo()


def test_kiem_bat_trung_ma(tam):
    k = KC.KHOI_DS[0]
    tam.setattr(KC, "KHOI_DS", KC.KHOI_DS + [k])
    assert any("trung ma khoi" in e for e in KC.kiem_tinh_nhat_quan())


# ========================================================================== khoi <-> engine luoi.py: khong ghi khong
def test_engine_co_phai_tro_toi_truong_that_va_da_cai_dat():
    ten_truong = {f.name for f in dataclasses.fields(L.ThamSo)}
    for k in KC.KHOI_DS:
        assert set(k.truong_engine) <= ten_truong, k.ma
        if k.engine in ("co", "mot_phan"):
            assert k.truong_engine, k.ma
            assert not set(k.truong_engine) & set(L.CHUA_CAI_DAT), k.ma
        else:
            assert set(k.truong_engine) <= set(L.CHUA_CAI_DAT), k.ma


def test_cat_lo_theo_tien_chi_ghi_mot_phan_vi_cat_theo_tai_khoan_chua_cai_dat():
    # Engine cat CA CHUOI theo tien (cat_lo_tien, 08/10/2026) nhung cat theo TAI KHOAN (dung_lo_tong) van khong cai dat: khong duoc ghi "co".
    k = KC.khoi("cat_lo_theo_tien")
    assert "dung_lo_tong" in L.CHUA_CAI_DAT and "cat_lo_tien" not in L.CHUA_CAI_DAT
    assert k.engine == "mot_phan" and k.truong_engine == ("cat_lo_tien",)
    assert "dung_lo_tong" in k.engine_ghi_chu           # noi ro phan nao chua co


def test_co_che_thoat_va_loc_gio_cua_engine_duoc_ghi_dung_trang_thai():
    # Moi truong "tinh nang duong_di" cua engine phai thuoc DUNG MOT khoi (khong khoi nao quen, khong khoi nao ghi chung truong).
    chu = {}
    for k in KC.KHOI_DS:
        for t in k.truong_engine:
            if t in L.TINH_NANG_DUONG_DI:
                chu.setdefault(t, []).append(k.ma)
    assert chu == {"cat_lo_pip": ["cat_lo_chuoi_theo_pip"], "cat_lo_tien": ["cat_lo_theo_tien"], "thoat_gio": ["thoat_theo_thoi_gian"],
                   "nghi_gio": ["nghi_sau_cat_lo"], "gio_vao_tu": ["loc_gio_giao_dich"], "gio_vao_den": ["loc_gio_giao_dich"]}, chu
    assert {m: KC.khoi(m).engine for m in ("cat_lo_chuoi_theo_pip", "thoat_theo_thoi_gian", "nghi_sau_cat_lo")} == {
        "cat_lo_chuoi_theo_pip": "co", "thoat_theo_thoi_gian": "co", "nghi_sau_cat_lo": "co"}
    assert KC.khoi("loc_gio_giao_dich").engine == "mot_phan"       # chi MOT cua so, khong nhieu cua so / ngay trong tuan
    for m in ("cat_lo_chuoi_theo_pip", "thoat_theo_thoi_gian", "nghi_sau_cat_lo"):
        assert m in KC.BOT["luoi_cua_ta"].khoi                      # engine "co" => he cua ta co khoi do


def test_kiem_bat_khoi_ghi_co_ma_truong_khong_ton_tai_hoac_chua_cai_dat(tam):
    k = KC.khoi("lot_phang")
    # truong khong ton tai
    moi = dataclasses.replace(k, truong_engine=("truong_ma_khong_co",))
    tam.setattr(KC, "KHOI_DS", [moi if x.ma == k.ma else x for x in KC.KHOI_DS])
    assert any("khong co trong luoi.ThamSo" in e for e in KC.kiem_tinh_nhat_quan())
    # engine 'co' nhung chi tro vao truong CHUA cai dat
    moi = dataclasses.replace(k, truong_engine=("dung_lo_tong",))
    tam.setattr(KC, "KHOI_DS", [moi if x.ma == k.ma else x for x in KC.KHOI_DS])
    assert any("CHUA cai dat" in e for e in KC.kiem_tinh_nhat_quan())
    # engine 'co' nhung khong tro truong nao
    moi = dataclasses.replace(k, truong_engine=())
    tam.setattr(KC, "KHOI_DS", [moi if x.ma == k.ma else x for x in KC.KHOI_DS])
    assert any("khong chi ra truong" in e for e in KC.kiem_tinh_nhat_quan())
    # khoi 'chua' ma truong da duoc engine doc
    k2 = KC.khoi("lot_nhan_theo_bac")
    moi = dataclasses.replace(k2, truong_engine=("he_so_lot",))
    tam.setattr(KC, "KHOI_DS", [moi if x.ma == k2.ma else x for x in KC.KHOI_DS])
    assert any("da duoc engine doc" in e for e in KC.kiem_tinh_nhat_quan())


def test_he_cua_ta_la_dung_cac_khoi_engine_co():
    co = {k.ma for k in KC.KHOI_DS if k.engine == "co"}
    assert set(KC.BOT["luoi_cua_ta"].khoi) == co
    assert all(v[0] == "ma_nguon" for v in KC.BOT["luoi_cua_ta"].khoi.values())
    # khong bot ngoai nao duoc phep ghi muc ma_nguon
    for b in KC.BOT_DS:
        if b.ma != "luoi_cua_ta":
            assert all(v[0] != "ma_nguon" for v in b.khoi.values()), b.ma


# ========================================================================== xep thu tu / de xuat tren catalog nho (dap an biet truoc)
def _bot_mau(ma, khoi, song_sot=False):
    return KC.Bot(ma, ma, "MT5", "-", "-", "-", song_sot, "-", {m: ("video", "x") for m in khoi})


@pytest.fixture
def nho(monkeypatch):
    """Catalog nho: A (3 bot khong song sot), B (1 bot SONG SOT), C (2 bot), D (engine co), E (ngoai), F (khong ai dung)."""
    khoi = [_khoi_mau("khoi_a", "chua", "LOT"), _khoi_mau("khoi_b", "chua", "LOT"), _khoi_mau("khoi_c", "mot_phan", "THOAT"),
            _khoi_mau("khoi_d", "co", "LOT"), _khoi_mau("khoi_e", "ngoai", "VAO"), _khoi_mau("khoi_f", "chua", "LOC")]
    bot = [_bot_mau("b1", ["khoi_a", "khoi_c"]), _bot_mau("b2", ["khoi_a", "khoi_c"]), _bot_mau("b3", ["khoi_a", "khoi_e"]),
           _bot_mau("song", ["khoi_b", "khoi_d"], song_sot=True),
           _bot_mau("luoi_cua_ta", [])]
    monkeypatch.setattr(KC, "KHOI_DS", khoi)
    monkeypatch.setattr(KC, "KHOI", {k.ma: k for k in khoi})
    monkeypatch.setattr(KC, "BOT_DS", bot)
    monkeypatch.setattr(KC, "BOT", {b.ma: b for b in bot})
    monkeypatch.setattr(KC, "LOAI_TRU", (("khoi_a", "khoi_b", "khoi_d"),))
    return khoi


def test_khoang_trong_song_sot_truoc_roi_so_bot(nho):
    ds = KC.khoang_trong_engine()
    # engine co (D) va ngoai (E) khong vao danh sach; F khong ai dung van vao (nhung o cuoi)
    assert [r["ma"] for r in ds] == ["khoi_b", "khoi_a", "khoi_c", "khoi_f"]
    assert [r["uu_tien"] for r in ds] == [1, 2, 3, 4]
    assert ds[0]["o_bot_song_sot"] == ["song"] and ds[1]["o_bot_song_sot"] == []
    assert [r["so_bot"] for r in ds] == [1, 3, 2, 0]
    assert ds[2]["engine"] == "mot_phan"


def test_khoang_trong_dung_voi_catalog_that():
    ds = KC.khoang_trong_engine()
    assert ds and all(r["engine"] in ("chua", "mot_phan") for r in ds)
    co_song = [bool(r["o_bot_song_sot"]) for r in ds]
    assert co_song == sorted(co_song, reverse=True)
    for a, b in zip(ds, ds[1:]):
        if bool(a["o_bot_song_sot"]) == bool(b["o_bot_song_sot"]):
            assert a["so_bot"] >= b["so_bot"]
    # cac khoi ma khao sat CCBSN da liet ke la "khoang trong" phai nam trong so do
    ma = {r["ma"] for r in ds}
    assert {"lot_nhan_theo_bac", "luoi_buoc_theo_bac", "lenh_doi_ung_sau_n_lenh", "doi_tp_khi_lo", "all_sniper"} <= ma
    # va tat ca deu thuoc bot song sot (ccbsn)
    thu = {r["ma"]: r for r in ds}
    for m in ("lot_nhan_theo_bac", "luoi_buoc_theo_bac", "lenh_doi_ung_sau_n_lenh", "doi_tp_khi_lo", "all_sniper"):
        assert thu[m]["o_bot_song_sot"] == ["ccbsn"], m


def test_dac_sac_la_khoi_it_bot_dung(nho):
    ds = KC.dac_sac_theo_bot(tran=1)
    assert "luoi_cua_ta" not in ds
    assert ds["song"] == ["khoi_b", "khoi_d"]          # moi khoi chi 1 bot dung
    assert ds["b1"] == []                               # khoi_a (3 bot) va khoi_c (2 bot) deu qua tran
    assert KC.dac_sac_theo_bot(tran=2)["b1"] == ["khoi_c"]
    assert KC.dac_sac_theo_bot(tran=3)["b1"] == ["khoi_a", "khoi_c"]


def test_dac_sac_voi_catalog_that():
    ds = KC.dac_sac_theo_bot(tran=1)
    assert "all_sniper" in ds["ccbsn"] and "lot_tong_gap_doi" in ds["bigmouse"]
    assert "lot_nhan" not in ds["ccbsn"]                # nhieu bot dung lot_nhan -> khong dac sac
    assert all(v == [] for v in KC.dac_sac_theo_bot(tran=0).values())


def test_de_xuat_ap_cheo_dap_an_biet_truoc(nho):
    ds = KC.de_xuat_ap_cheo(host=("khoi_d",), top=10)
    thu_tu = [r["ma"] for r in ds]
    # E la 'ngoai' khong duoc de xuat; D da co trong host; F khong ai dung -> khong de xuat
    assert thu_tu == ["khoi_b", "khoi_a", "khoi_c"]
    kieu = {r["ma"]: r["kieu"] for r in ds}
    assert kieu["khoi_b"] == "thay khoi_d" and kieu["khoi_a"] == "thay khoi_d"   # cung nhom tru nhau voi khoi_d dang co
    assert kieu["khoi_c"] == "them"
    assert ds[0]["o_bot_song_sot"] == ["song"]
    assert KC.de_xuat_ap_cheo(host=("khoi_d",), top=2)[-1]["ma"] == "khoi_a"
    # host rong: khong khoi nao 'thay'
    assert {r["kieu"] for r in KC.de_xuat_ap_cheo(host=(), top=10)} == {"them"}


def test_de_xuat_voi_catalog_that():
    ds = KC.de_xuat_ap_cheo(top=100)
    ma = [r["ma"] for r in ds]
    host = {k.ma for k in KC.KHOI_DS if k.engine == "co"}
    assert not host & set(ma)                           # khong de xuat khoi da co
    assert not {k.ma for k in KC.KHOI_DS if k.engine == "ngoai"} & set(ma)
    assert all(KC.bot_dung_khoi(m) for m in ma)         # khoi khong bot nao dung khong duoc de xuat
    kieu = {r["ma"]: r["kieu"] for r in ds}
    assert kieu["lot_nhan_theo_bac"].startswith("thay") and "lot_nhan" in kieu["lot_nhan_theo_bac"]
    assert kieu["luoi_buoc_theo_bac"].startswith("thay")
    assert kieu["all_sniper"] == "them" and kieu["doi_tp_khi_lo"] == "them"
    # khoi o bot song sot dung dau
    dau = [r for r in ds if r["o_bot_song_sot"]]
    assert ds[: len(dau)] == dau
    # host nho: lot_nhan co the thay lot_phang
    x = {r["ma"]: r["kieu"] for r in KC.de_xuat_ap_cheo(host=("lot_phang", "hai_chieu_doc_lap"), top=100)}
    assert x["lot_nhan"] == "thay lot_phang" and x["mot_chieu"] == "thay hai_chieu_doc_lap"


# ========================================================================== phan loai ten tham so .set
TEN_THAT_CCBSN = [
    ("InpTypeBuySell", ("hai_chieu_doc_lap", "mot_chieu")),
    ("InpMaxSpread", ("loc_spread",)),
    ("InpMaxBuyOrders", ("tran_so_lenh",)),
    ("InpMaxSellOrders", ("tran_so_lenh",)),
    ("InpMaxLots", ("tran_lot_tong",)),                   # bay: 'MaxLots' chua 'xLot' (lot_nhan)
    ("InpMultiplier", ("lot_nhan",)),
    ("InpOrders2NewMultiplier1", ("lot_nhan_theo_bac",)),
    ("InpOrders2NewMultiplier5", ("lot_nhan_theo_bac",)),
    ("InpNewMultiplier1", ("lot_nhan_theo_bac",)),
    ("InpNewMultiplier5", ("lot_nhan_theo_bac",)),
    ("InpPlus", ("lot_cong",)),
    ("InpDistance0", ("luoi_gian_cach_deu",)),
    ("InpDistance1", ("luoi_buoc_theo_bac",)),
    ("InpDistance4", ("luoi_buoc_theo_bac",)),
    ("InpDistanceMulti", ("luoi_buoc_gian_dan",)),
    ("InpTP", ("tp_tung_lenh",)),
    ("InpTPDCA", ("tp_chuoi_tu_gia_tb",)),
    ("InpUseChangeTPDCA", ("doi_tp_khi_lo",)),            # 'ChangeTP' phai thang 'TPDCA'
    ("InpPerLoss2ChangeTP", ("doi_tp_khi_lo",)),
    ("InpOrders2OpenOpp", ("lenh_doi_ung_sau_n_lenh",)),
    ("InpLotsOpp", ("lenh_doi_ung_sau_n_lenh",)),
    ("InpPerLotsOpp", ("lenh_doi_ung_sau_n_lenh",)),      # 'PerLots' khong phai 'PerLoss'
    ("InpUseSniper", ("tia_n_lenh_khi_chuoi_dai",)),
    ("InpTPSniper", ("tia_n_lenh_khi_chuoi_dai",)),       # 'Sniper' phai thang 'TP'
    ("InpMoneySniperFull", ("tia_n_lenh_khi_chuoi_dai",)),
    ("InpFirstOrdersSniper", ("tia_n_lenh_khi_chuoi_dai",)),
    ("InpLastOrdersSniper", ("tia_n_lenh_khi_chuoi_dai",)),
    ("InpUseFilterDCA", ("loc_dca_tu_lenh_n",)),
    # chua biet nghia / khong thuoc khoi nao: PHAI de trong, khong doan bua
    ("InpDCAMODE", ()),
    ("InpMagicID", ()),
]


@pytest.mark.parametrize("ten, mong", TEN_THAT_CCBSN)
def test_loai_ten_that_ccbsn(ten, mong):
    assert KC.loai_tu_ten_tham_so(ten) == mong


@pytest.mark.parametrize("ten, mong", [
    ("InpUseAllSniper", ("all_sniper",)),                 # 'All Sniper' thang 'Sniper'
    ("InpAtrMultiplier", ("loc_adx_atr",)),                # ATR thang 'Multiplier'
    ("InpATRPeriod", ("loc_adx_atr",)),
    ("InpADXLevel", ("loc_adx_atr",)),
    ("InpMatrixSize", ()),                                 # 'atr' trong tu khac khong phai ATR
    ("InpStrategyName", ()),
    ("InpNewsFilter", ("loc_tin_tuc",)),                  # 'News' (khong phai 'New' + Multiplier)
    ("InpStartHour", ("loc_gio_giao_dich",)),
    ("InpTimeTrade1", ("loc_gio_giao_dich",)),
    ("InpXLot", ("lot_nhan",)),                            # 'xlot' that van nhan ra
    ("lot_multiplier", ("lot_nhan",)),
    ("InpStopLoss", ("sl_cung",)),
    ("InpTrailingStart", ("trailing_stop_chuoi",)),
    ("InpRSIPeriod", ("vao_rsi_qua_ban",)),
    ("InpMaPeriod", ()),                                   # 'Ma' chu thuong khong phai MA (bay 'Max' / 'Magic')
    ("EMA_Period", ("vao_theo_ma",)),
    ("", ()),
    (None, ()),
    ("   ", ()),
])
def test_loai_ten_bay_va_duong_bien(ten, mong):
    assert KC.loai_tu_ten_tham_so(ten) == mong


def test_ten_tham_so_trong_danh_muc_tu_xep_ve_dung_khoi():
    """Moi tham so ten THAT (bat dau 'Inp') ghi trong `Khoi.tham_so` phai duoc bo phan loai xep ve chinh khoi do."""
    n = 0
    for k in KC.KHOI_DS:
        for t in k.tham_so:
            if not re.fullmatch(r"Inp[A-Za-z0-9]+(\d-\d)?", t):
                continue
            ten = re.sub(r"\d-\d$", "", t)
            n += 1
            assert k.ma in KC.loai_tu_ten_tham_so(ten), (k.ma, t)
    assert n >= 15       # co du tham so that de phep thu co nghia


def test_moi_khoi_knob_cua_ccbsn_co_ten_that_trong_bang_mau():
    """Khoi nao CCBSN ghi muc 'knob' phai co it nhat mot ten that trong TEN_THAT_CCBSN, tru khoi ma khao sat chua chep ten
    tham so (all_sniper, lich gio, lich ngay): tranh ghi 'knob' cho thu chua tung thay ten."""
    da_co = {m for _, mong in TEN_THAT_CCBSN for m in mong}
    chua_chep_ten = {"all_sniper", "loc_gio_giao_dich", "loc_ngay_thu_lich"}
    for ma, (muc, _gc) in KC.BOT["ccbsn"].khoi.items():
        if muc == "knob" and ma not in chua_chep_ten:
            assert ma in da_co, ma


# ========================================================================== truy van co ban
def test_bot_dung_khoi_va_ma_tran():
    assert "ccbsn" in KC.bot_dung_khoi("lot_nhan")
    assert "luoi_cua_ta" not in KC.bot_dung_khoi("lot_nhan")
    assert "luoi_cua_ta" in KC.bot_dung_khoi("lot_nhan", gom_cua_ta=True)
    assert KC.so_bot_dung("all_sniper") == 1
    mt = KC.ma_tran()
    assert mt["ccbsn"]["lot_nhan_theo_bac"] == "knob" and mt["bigmouse"]["lot_tong_gap_doi"] == "video"
    assert mt["copy_lot"] == {}                     # copy lot khong phai bot giao dich


def test_bot_khong_co_nguon_mo_ta_la_hang_rong_that_thu():
    for ma in ("black_wolf", "goldminer", "trailing_hbot", "unforgiven", "copy_lot"):
        assert KC.BOT[ma].khoi == {}
    # ... nhung ket qua tester that van duoc ghi
    assert "treo" in KC.BOT["black_wolf"].ket_qua and "treo" in KC.BOT["goldminer"].ket_qua


def test_khoi_hai_chieu_va_mot_chieu_khong_cung_luc_trong_he_cua_ta_la_cua_che_do():
    # he cua ta chay ca hai che do (tham so che_do), nen dung ca hai khoi
    assert {"hai_chieu_doc_lap", "mot_chieu"} <= set(KC.BOT["luoi_cua_ta"].khoi)


# ========================================================================== tai lieu sinh tu ma
def test_tai_lieu_khop_ban_sinh_tu_ma():
    assert KC.TAI_LIEU.exists(), "chay: python -m nhan.khoi_co_che --viet"
    assert KC.TAI_LIEU.read_text(encoding="utf-8") == KC.viet_tai_lieu(), \
        "tai_lieu/KHO_CO_CHE_BOT.md cu so voi ma - chay: python -m nhan.khoi_co_che --viet"


def test_tai_lieu_khong_phu_thuoc_thu_tu_chen_dict(tam):
    """Bai hoc: test khac xoa roi khoi phuc khoi cua mot bot dua khoi do xuong CUOI dict -> tai lieu doi thu tu. Nay tai lieu
    di theo thu tu chuan cua danh sach khoi nen khong doi."""
    goc = KC.viet_tai_lieu()
    khoi_ta = KC.BOT["luoi_cua_ta"].khoi
    dau = next(iter(khoi_ta))
    gia_tri = khoi_ta[dau]
    tam.delitem(khoi_ta, dau)
    tam.setitem(khoi_ta, dau, gia_tri)        # dua xuong cuoi dict
    assert list(khoi_ta)[-1] == dau
    assert KC.viet_tai_lieu() == goc
    assert [m for m, _ in KC.khoi_cua_bot(KC.BOT["luoi_cua_ta"])] == [k.ma for k in KC.KHOI_DS if k.ma in khoi_ta]


def test_tai_lieu_xac_dinh_va_chi_ascii(tmp_path):
    a, b = KC.viet_tai_lieu(), KC.viet_tai_lieu()
    assert a == b
    assert a.isascii()
    assert Path(KC.__file__).read_text(encoding="utf-8").isascii()
    p = KC.ghi_tai_lieu(tmp_path / "x" / "kho.md")
    assert p.read_text(encoding="utf-8") == a and "\r" not in a


def test_tai_lieu_co_du_khoi_bot_va_cac_muc():
    doc = KC.viet_tai_lieu()
    for k in KC.KHOI_DS:
        assert doc.count("**`%s`**" % k.ma) == 1, k.ma            # mot khoi mot muc chi tiet
        assert len(re.findall(r"^\| %s \|" % re.escape(k.ma), doc, re.M)) == 1, k.ma   # va mot dong trong ma tran
    for b in KC.BOT_DS:
        assert "### %s - " % b.ma in doc, b.ma
    for muc in ("## 1.", "## 2.", "## 3. MA TRAN", "## 4. TUNG KHOI", "## 5. KHOANG TRONG ENGINE", "## 6. DE XUAT AP CHEO",
                "## 7. LOI KHUYEN VAN HANH", "## 9. KHONG PHAI GI"):
        assert muc in doc, muc
    assert "SONG SOT" in doc and "ccbsn" in doc


def test_tai_lieu_khong_dua_ten_mo_hinh_hay_khoa_vao():
    doc = KC.viet_tai_lieu().lower()
    for cam in ("api_key", "password", "mat khau", "claude-", "deepseek", "qwen"):
        assert cam not in doc, cam
    assert not re.search(r"\bsk-[a-z0-9]{10,}", doc)


def test_tai_lieu_noi_ro_day_la_ban_do_khong_phai_ket_luan():
    doc = KC.viet_tai_lieu()
    assert "Khong phai danh gia bot" in doc
    assert "khong phai du bao khoi nao" in doc.replace("\n", " ")


# ========================================================================== giao dien dong lenh
def test_main_tom_tat_kiem_va_loai(capsys):
    assert KC.main([]) == 0
    out = capsys.readouterr().out
    assert "%d khoi" % len(KC.KHOI_DS) in out and "song sot: ccbsn" in out
    assert KC.main(["--kiem"]) == 0 and "OK" in capsys.readouterr().out
    assert KC.main(["--loai", "InpMaxLots", "InpDCAMODE"]) == 0
    out = capsys.readouterr().out
    assert "InpMaxLots -> tran_lot_tong" in out and "InpDCAMODE -> chua xep" in out


def test_main_kiem_tra_ma_thoat_khac_0_khi_loi(tam, capsys):
    tam.setitem(KC.BOT["ccbsn"].khoi, "khoi_khong_co", ("knob", "x"))
    assert KC.main(["--kiem"]) == 1
    assert "khoi_khong_co" in capsys.readouterr().out
