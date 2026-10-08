# -*- coding: utf-8 -*-
from nhan import giam_sat_may_nha as G


def test_xong_gia_phat_hien_loi_trong_dat():
    assert G.xong_gia({"trang_thai": "DAT", "bang_chung": {"dong_cuoi": ["FileNotFoundError: khong co du lieu"]}})
    assert G.xong_gia({"trang_thai": "DAT", "bang_chung": {"dong_cuoi": ['"co_lai": true']}}) is None
    assert G.xong_gia({"trang_thai": "AM", "bang_chung": {"dong_cuoi": ["Error:"]}}) is None


def test_hanh_dong_bao_het_viec_va_bo_chet():
    k = {"nhip_tim": [{"ten": "a", "song": False, "den": None}, {"ten": "b", "song": True, "den": None}],
         "gio_viec_con": 3, "xong_gia_1h": [], "dang_ket": []}
    h = " ".join(G.hanh_dong(k))
    assert "a" in h and "giao them" in h


def test_hanh_dong_bao_xong_gia_theo_nhom_va_dung_gio_dong_ho():
    k = {"nhip_tim": [{"ten": "a", "song": True, "den": None}], "gio_viec_con": 90, "gio_dong_ho": 4, "xong_gia_1h": [], "dang_ket": [],
         "xong_gia_nhom": {"sua_duoc": 25, "can_chan_doan": 24, "khong_chay_lai": 31}}
    h = " ".join(G.hanh_dong(k))
    assert "giao them" in h and "dua-lai" in h and "mo log tester" in h and "thieu du lieu gia" in h


def _hb(tmp, ten, luc, kha_nang, **them):
    import json
    (tmp / "may").mkdir(parents=True, exist_ok=True)
    (tmp / "may" / (ten + ".json")).write_text(json.dumps({"ten": ten, "luc": luc, "kha_nang": kha_nang, **them}), encoding="utf-8")


def test_nhip_tim_doi_gio_nha_ve_utc_khong_nhan_song_gia(tmp_path, monkeypatch):
    """Nha ghi `luc` theo gio dia phuong UTC+7, cloud chay o UTC. Truoc 08/10/2026 cloud tru thang -> moi nhip 'tre' 7 gio nen bo chay
    chet 3 gio van hien 'song' (19/22 song trong khi chi 1 bo chay con nhip tim moi)."""
    from datetime import datetime, timezone
    bay = datetime(2026, 10, 8, 16, 47, tzinfo=timezone.utc).timestamp()          # = 23:47 gio nha
    _hb(tmp_path, "tuoi", "2026-10-08T23:26:06", ["windows"])                        # 21 phut truoc
    _hb(tmp_path, "cu", "2026-10-08T20:26:12", ["windows"])                          # 3 gio 21 phut truoc
    _hb(tmp_path, "mui_khac", "2026-10-08T16:30:00", ["windows"], mui_gio_phut=0)    # may ghi gio UTC: 17 phut truoc
    monkeypatch.setattr(G, "VIEC", tmp_path)
    ra = {x["ten"]: x for x in G.nhip_tim(30.0, bay)}
    assert [ra[k]["song"] for k in ("tuoi", "cu", "mui_khac")] == [True, False, True]
    assert (ra["tuoi"]["tuoi_phut"], ra["cu"]["tuoi_phut"], ra["mui_khac"]["tuoi_phut"]) == (21, 201, 17)


def test_don_cho_ma_moi_khong_tinh_vao_hang_doi_khi_bo_chay_song_chua_co_the(tmp_path, monkeypatch):
    """Don khai `can` engine4 ma moi bo chay song deu khong co the engine4 thi KHONG chay duoc: dem rieng (bi_chan_ma_cu), khong tinh gio hang doi;
    va `xong` tinh theo MA don (ten file don co the khac ma)."""
    import json
    from datetime import datetime, timezone
    bay = datetime(2026, 10, 8, 16, 47, tzinfo=timezone.utc).timestamp()
    _hb(tmp_path, "nha", "2026-10-08T23:40:00", ["windows", "mt5", "data"])
    (tmp_path / "cho").mkdir()
    (tmp_path / "xong").mkdir()
    for ten, doc in {"a.json": {"ma": "a", "lan": "CPU"}, "b.json": {"ma": "b", "lan": "CPU", "can": ["engine4"]},
                     "00-c.json": {"ma": "c", "lan": "CPU"}, "d.json": {"ma": "d", "lan": "MANG", "can": ["dien-dan-v2"]}}.items():
        (tmp_path / "cho" / ten).write_text(json.dumps(doc), encoding="utf-8")
    (tmp_path / "xong" / "c.json").write_text(json.dumps({"ma": "c", "trang_thai": "DAT"}), encoding="utf-8")   # don 00-c.json DA xong
    monkeypatch.setattr(G, "VIEC", tmp_path)
    k = G.tong_hop(30.0, bay)
    assert (k["con_cho"], k["bi_chan_ma_cu"], k["theo_lan"]) == (3, 2, {"CPU": 1})
    h = " ".join(G.hanh_dong({**k, "xong_gia_1h": [], "dang_ket": []}))
    assert "CHO MA MOI" in h and "KHONG giao them" in h
    # co bo chay nap ma moi (khai the) thi het bi chan
    _hb(tmp_path, "nha-m", "2026-10-08T23:40:00", ["windows", "engine4", "dien-dan-v2"])
    k = G.tong_hop(30.0, bay)
    assert (k["bi_chan_ma_cu"], k["theo_lan"]) == (0, {"CPU": 2, "MANG": 1})
