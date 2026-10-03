# -*- coding: utf-8 -*-
"""may_nha: quet phan cung -> mau -> den XANH/VANG/DO -> do co gian -> ket luan -> nhip tim + danh sach trang.

Khong dung may that: moi lenh he thong di qua MOT `runner` gia (PowerShell tra JSON dung dang Windows that, ke ca cai bay
"1 phan tu -> DOI TUONG, nhieu phan tu -> MANG"). Hieu chuan hai chieu: moi kiem tra 'canh bao' co mot kiem tra 'im lang'
(mot den luon do cung vo dung nhu mot den luon xanh).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from nhan import may_nha as MN
from qwen import cau_git as CG, cau_may as CM, cau_trang as CT

GB = 2 ** 30
REPO = Path(__file__).resolve().parent
_NGUOI_DUNG_THAT = MN._nguoi_dung            # giu ban that (fixture ben duoi thay bang []), de test `an_danh`


@pytest.fixture(autouse=True)
def _khong_cham_vao_repo(tmp_path, monkeypatch):
    """Khong test nao duoc ghi nhat ky / bao cao that cua repo, va so do khong phu thuoc ten nguoi dung cua may chay test."""
    monkeypatch.setattr(MN, "NHAT_KY", tmp_path / "nhat_ky" / "may_nha_mau.jsonl")
    monkeypatch.setattr(MN, "BAO_CAO", tmp_path / "reports")
    monkeypatch.setattr(MN, "_nguoi_dung", lambda: [])


@pytest.fixture
def ram_gia(monkeypatch):
    """psutil.virtual_memory() co dinh: may 32 GB, con trong 30 GB (cho `so_mt5_toi_da`, vi no doc RAM trong that)."""
    import psutil
    monkeypatch.setattr(psutil, "virtual_memory",
                        lambda: SimpleNamespace(total=32 * GB, available=30 * GB, percent=6.0))


# =============================================================== DU LIEU GIA (dang PowerShell that)
def thanh_ram(vi_tri="DIMM_A1", gb=32, speed=2400, cau_hinh=2133, ecc=True, td=8192 | 128, ma="M393A4K40BB1-CRC "):
    return {"BankLabel": "NODE 1", "DeviceLocator": vi_tri, "Capacity": gb * GB, "Speed": speed, "ConfiguredClockSpeed": cau_hinh,
            "SMBIOSMemoryType": 26, "FormFactor": 8, "Manufacturer": "Samsung ", "PartNumber": ma,
            "DataWidth": 64, "TotalWidth": 72 if ecc else 64, "TypeDetail": td}


def ps_quet_gia(**ghi_de):
    """May 10 nhan / 20 luong, MOT thanh 32 GB DDR4 ECC RDIMM (4 khe), SSD 128 GB + HDD 230 GB, ke hoach dien Balanced.
    Cac muc chi co 1 phan tu o dang DOI TUONG (khong phai mang) - dung nhu PowerShell `ConvertTo-Json`."""
    d = {
        "cpu": {"Name": "Intel(R) Xeon(R) CPU E5-2630 v4 @ 2.20GHz", "NumberOfCores": 10, "NumberOfLogicalProcessors": 20,
                "MaxClockSpeed": 2200, "CurrentClockSpeed": 2200, "L2CacheSize": 2560, "L3CacheSize": 25600, "SocketDesignation": "CPU1"},
        "ram_thanh": thanh_ram(),
        "ram_mang": {"MemoryDevices": 4, "MaxCapacity": 1073741824, "MaxCapacityEx": 0, "MemoryErrorCorrection": 6},
        "bo_mach": {"Manufacturer": "Huananzhi", "Product": "X99-8M"},
        "bios": {"Manufacturer": "American Megatrends", "SMBIOSBIOSVersion": "5.11", "Ngay": "2020-01-01"},
        "dia_vat_ly": [
            {"FriendlyName": "SSD 128", "MediaType": 4, "BusType": 11, "Size": 128035676160, "HealthStatus": "Healthy", "SpindleSpeed": 0},
            {"FriendlyName": "HDD 230", "MediaType": 3, "BusType": 11, "Size": 230000000000, "HealthStatus": "Healthy", "SpindleSpeed": 7200}],
        "o_dia": [{"DeviceID": "C:", "Size": 127 * GB, "FreeSpace": 40 * GB, "FileSystem": "NTFS"},
                  {"DeviceID": "G:", "Size": 214 * GB, "FreeSpace": 210 * GB, "FileSystem": "NTFS"}],
        "pagefile_dung": {"Name": "C:\\pagefile.sys", "AllocatedBaseSize": 4096, "CurrentUsage": 800, "PeakUsage": 3000},
        "pagefile_cai": [],
        "he_thong": {"AutomaticManagedPagefile": True, "TotalPhysicalMemory": 32 * GB, "NumberOfProcessors": 1,
                     "NumberOfLogicalProcessors": 20},
        "he_dieu_hanh": {"Caption": "Microsoft Windows 10 Pro", "Version": "10.0.19045", "BuildNumber": "19045", "OSArchitecture": "64-bit"},
        "nhiet": None,
        "dien": "Power Scheme GUID: 381b4222-f694-41f0-9685-ff5bb260df2e  (Balanced)\n",
    }
    d.update(ghi_de)
    return d


def runner_gia(quet=None, mau=None, loi=None, rac_truoc=""):
    """Gia lap `chay_lenh`: nhan dang script theo noi dung (quet phan cung hay mau hieu nang)."""
    cuoc = []

    def run(args, han=40.0):
        cuoc.append(args)
        if loi:
            return None, loi
        script = args[-1]
        if "Win32_PhysicalMemory" in script:
            return rac_truoc + json.dumps(quet if quet is not None else ps_quet_gia()), None
        if "PerfFormattedData" in script:
            return json.dumps(mau or {}), None
        return None, "script la"
    run.cuoc = cuoc
    return run


def quet_gia(**kw):
    return MN.quet(runner=runner_gia(**kw), voi_mt5=False, voi_nhan_c=False)


def diem(n, v, cpu=None, mhz=None):
    return {"n": n, "toc_do_tong": v, "cpu_pct": cpu, "mhz": mhz}


def kernel(luong, nvl, ds):
    pts = [diem(n, v) for n, v in ds]
    return {"diem": pts, "phan_tich": MN.phan_tich_co_gian(pts, luong, nvl)}


# 20 luong / 10 nhan vat ly. Nhe: tuyen tinh toi 10, luong ao them 30%. Nang RAM: bao hoa o ~4 viec.
CONG_N = (1, 2, 4, 8, 10, 16, 20)
DO_CPU_NHO = [(n, float(n)) for n in (1, 2, 4, 8, 10)] + [(16, 11.8), (20, 13.0)]
DO_LUOI = [(n, 5.0 * v) for n, v in DO_CPU_NHO]
DO_LUOI_DAI = [(1, 1.0), (2, 1.9), (4, 2.4), (8, 2.5), (10, 2.5), (16, 2.5), (20, 2.5)]
DO_BANG_THONG = [(1, 5.0), (2, 8.5), (4, 9.2), (8, 9.4), (10, 9.4), (16, 9.4), (20, 9.4)]


def do_gia(bang_thong=DO_BANG_THONG, ly_thuyet=17.1, **them):
    d = {"cpu_nho": kernel(20, 10, DO_CPU_NHO), "luoi": kernel(20, 10, DO_LUOI), "luoi_dai": kernel(20, 10, DO_LUOI_DAI),
         "bang_thong": kernel(20, 10, bang_thong)}
    d["bang_thong"]["ly_thuyet_gbs"] = ly_thuyet
    pt = d["bang_thong"]["phan_tich"]
    if ly_thuyet and pt.get("du_lieu"):
        pt["pct_so_voi_ly_thuyet"] = round(100 * pt["dinh"]["toc_do_tong"] / ly_thuyet, 1)
    d.update(them)
    return d


MAU_KHOE = {"luc": "2026-10-03T10:00:00", "cpu_pct": 78.0, "ram_trong_gb": 12.0, "commit_con_lai_gb": 30.0,
            "dia_trong_gb": {"C:": 40.0, "G:": 210.0}}


# =============================================================== RUNNER + JSON
class TestChayPs:
    def test_bo_rac_truoc_JSON_va_doc_duoc(self):
        d, loi = MN.chay_ps(MN._PS_QUET, runner_gia(rac_truoc="WARNING: abc\nxin chao\n"))
        assert loi is None and d["cpu"]["NumberOfCores"] == 10

    def test_script_that_goi_dung_lop_WMI_cho_runner_nhan_dang(self):
        assert "Win32_PhysicalMemory" in MN._PS_QUET and "PerfFormattedData" in MN._PS_MAU
        assert "Win32_PhysicalMemory" not in MN._PS_MAU and "PerfFormattedData" not in MN._PS_QUET

    def test_loi_runner_tra_None_va_ly_do_khong_nem(self):
        d, loi = MN.chay_ps(MN._PS_QUET, runner_gia(loi="khong co lenh powershell"))
        assert d is None and loi == "khong co lenh powershell"

    def test_JSON_hong_hoac_khong_phai_object_khong_nem(self):
        d, loi = MN.chay_ps("x", lambda a, h=0: ("{khong phai json", None))
        assert d is None and "JSON hong" in loi
        d, loi = MN.chay_ps("x", lambda a, h=0: ("khong co ngoac nhon nao", None))
        assert d is None and "JSON hong" in loi
        d, loi = MN.chay_ps("x", lambda a, h=0: ("[1, 2, 3]", None))     # script cua ta luon tra OBJECT; mang tran = khong dung dinh dang
        assert d is None and "JSON hong" in loi
        d, loi = MN.chay_ps("x", lambda a, h=0: ('{"a": 1} rac phia sau', None))
        assert d is None and "JSON hong" in loi


# =============================================================== QUET PHAN CUNG
class TestQuet:
    def test_may_10_nhan_20_luong_mot_thanh_32GB(self):
        q = quet_gia()
        c, r = q["cpu"], q["ram"]
        assert (c["nhan_vat_ly"], c["luong"], c["nguon"], c["so_o_cam"], c["l3_mb"]) == (10, 20, "wmi", 1, 25.0)
        assert r["so_thanh"] == 1 and r["khe_tong"] == 4 and r["khe_trong"] == 3
        assert r["tong_gb"] == 32.0
        assert r["kenh_dang_dung"] == 1 and r["kenh_suy_tu_ten_khe"] is True
        t = r["thanh"][0]
        assert (t["loai"], t["gb"], t["mt_s"], t["mt_s_toi_da"]) == ("DDR4", 32.0, 2133, 2400)   # toc do DANG CHAY, khong phai ghi tren thanh
        assert t["ecc"] is True and t["registered"] is True and t["lrdimm"] is False
        assert t["ma_hang"] == "M393A4K40BB1-CRC"                       # bo khoang trang thua
        assert r["toi_da_ho_tro_gb"] == 1024.0                           # MaxCapacity tinh bang KB: 1073741824 KB = 1 TB
        assert r["bang_thong_ly_thuyet_gbs"] == round(1 * 2133 * 8 / 1000, 1)

    def test_dia_pagefile_dien(self):
        q = quet_gia()
        assert [x["loai"] for x in q["dia"]["vat_ly"]] == ["SSD", "HDD"] and q["dia"]["vat_ly"][1]["gb"] == 230.0
        assert {o["o"]: o["trong_gb"] for o in q["dia"]["o"]} == {"C:": 40.0, "G:": 210.0}
        pf = q["pagefile"]
        assert pf["dang_dung"][0]["o"] == "C:" and pf["tong_cap_phat_gb"] == 4.0 and pf["he_thong_tu_quan_ly"] is True
        assert q["ke_hoach_dien"]["ten"] == "Balanced" and q["ke_hoach_dien"]["can_chuyen_high_performance"] is True
        assert q["he_dieu_hanh"].startswith("Microsoft Windows 10 Pro")
        assert q["do_duoc_bang_powershell"] is True and q["loi_powershell"] is None

    def test_PowerShell_tra_mang_nhieu_thanh_van_dung(self):
        quet = ps_quet_gia(ram_thanh=[thanh_ram("DIMM_A1"), thanh_ram("DIMM_B1"), thanh_ram("DIMM_B2")])
        r = quet_gia(quet=quet)["ram"]
        assert r["so_thanh"] == 3 and r["tong_gb"] == 96.0 and r["khe_trong"] == 1
        assert r["kenh_dang_dung"] == 2                                  # A, B (hai thanh cung kenh B tinh MOT kenh)
        assert r["bang_thong_ly_thuyet_gbs"] == round(2 * 2133 * 8 / 1000, 1)

    def test_MaxCapacityEx_dung_khi_lon_hon_2TB(self):
        mang = {"MemoryDevices": 8, "MaxCapacity": 2147483648, "MaxCapacityEx": 3221225472, "MemoryErrorCorrection": 6}
        assert quet_gia(quet=ps_quet_gia(ram_mang=mang))["ram"]["toi_da_ho_tro_gb"] == 3072.0
        mang = {"MemoryDevices": 4, "MaxCapacity": 134217728, "MaxCapacityEx": None, "MemoryErrorCorrection": 3}
        assert quet_gia(quet=ps_quet_gia(ram_mang=mang))["ram"]["toi_da_ho_tro_gb"] == 128.0

    def test_RAM_khong_ECC_va_khong_doan_duoc_kenh(self):
        quet = ps_quet_gia(ram_thanh=[thanh_ram("DIMM1", ecc=False, td=16384 | 128), thanh_ram("DIMM3", ecc=False, td=16384 | 128)])
        r = quet_gia(quet=quet)["ram"]
        assert r["thanh"][0]["ecc"] is False and r["thanh"][0]["unbuffered"] is True and r["thanh"][0]["registered"] is False
        assert r["kenh_suy_tu_ten_khe"] is False and r["kenh_dang_dung"] == 2     # khong doan duoc ten kenh -> dem so thanh

    def test_PowerShell_hong_van_tra_cau_truc_day_du_khong_nem(self):
        q = MN.quet(runner=runner_gia(loi="khong co lenh powershell"), voi_mt5=False, voi_nhan_c=False)
        assert q["do_duoc_bang_powershell"] is False and "powershell" in q["loi_powershell"]
        assert q["cpu"]["luong"] and q["cpu"]["luong"] >= 1               # du phong psutil
        assert q["ram"]["khe_trong"] is None and q["ram"]["bang_thong_ly_thuyet_gbs"] is None   # None, KHONG phai 0
        k = MN.ket_luan(q)
        assert any("Chua doc duoc so khe RAM" in t for t in k["tom_tat"])

    @pytest.mark.parametrize("ten, kenh", [
        ("DIMM_A1", "A"), ("DIMM A1", "A"), ("DIMMA1", "A"), ("ChannelB-DIMM0", "B"), ("CHANNELA-DIMM1", "A"),
        ("P0_DIMMC1", "C"), ("P1-DIMM_E2", "E"), ("A1", "A"), ("BANK 0", None), ("DIMM1", None), ("DIMM2", None), ("", None)])
    def test_kenh_tu_ten_khe(self, ten, kenh):
        assert MN._kenh_tu_ten_khe(ten) == kenh

    def test_ten_khe_uu_tien_DeviceLocator_roi_den_BankLabel(self):
        assert MN._kenh_tu_ten_khe("DIMM_A1", "NODE 1") == "A"
        assert MN._kenh_tu_ten_khe("", "ChannelD") == "D"

    @pytest.mark.parametrize("ten, so_o, kmax", [
        ("Intel(R) Xeon(R) CPU E5-2630 v4 @ 2.20GHz", 1, 4), ("Intel(R) Xeon(R) CPU E5-2680 v4", 2, 8),
        ("Intel(R) Xeon(R) CPU E3-1231 v3", 1, 2), ("Intel(R) Core(TM) i7-9700K", 1, 2), ("AMD Ryzen 9 5950X", 1, 2),
        ("Intel(R) Xeon(R) Gold 6130", 1, 6), ("AMD EPYC 7302", 1, 8), ("CPU la", 1, 4), (None, None, 4)])
    def test_so_kenh_toi_da_cua_nen_tang(self, ten, so_o, kmax):
        assert MN._kenh_toi_da(ten, so_o) == kmax


class TestAnDanh:
    def test_thay_ten_nguoi_dung_va_ten_may_va_bo_khoa_serial(self):
        x = {"o": "C:\\Users\\SV STORE\\AppData\\Local", "SerialNumber": "ABC123", "ds": ["pc-nha-01 vua chay", 5],
             "con": {"ProcessorSerial": "X", "ok": 1}}
        r = MN.an_danh(x, ["SV STORE", "pc-nha-01"])
        assert r == {"o": "C:\\Users\\<user>\\AppData\\Local", "ds": ["<user> vua chay", 5], "con": {"ok": 1}}

    def test_khong_phan_biet_hoa_thuong(self):
        assert MN.an_danh("Ten: SVSTORE svstore SvStore", ["svstore"]) == "Ten: <user> <user> <user>"

    def test_ten_nguoi_dung_doc_tu_moi_truong(self, monkeypatch):
        monkeypatch.setenv("USERNAME", "ongchu")
        monkeypatch.setattr(MN.platform, "node", lambda: "MAY-NHA-XYZ")
        ten = _NGUOI_DUNG_THAT()
        assert "ongchu" in ten and "MAY-NHA-XYZ" in ten
        assert all(len(t) >= 3 for t in ten)                              # ten qua ngan se xoa nham chu thuong gap

    def test_bao_cao_ghi_ra_file_khong_chua_ten_that(self, tmp_path, monkeypatch):
        monkeypatch.setattr(MN, "_nguoi_dung", lambda: ["svstore"])
        q = quet_gia(quet=ps_quet_gia(bios={"Manufacturer": "AMI", "SMBIOSBIOSVersion": "x", "Ngay": "C:\\Users\\SVSTORE"}))
        k = MN.ket_luan(q)
        ra = MN.ghi_bao_cao(q, None, None, k, thu_muc=tmp_path / "o")
        for f in ra.values():
            assert "svstore" not in Path(f).read_text(encoding="utf-8").lower(), f


# =============================================================== MAU + DEN
class TestDanhGiaMau:
    def test_may_khoe_xanh(self):
        r = MN.danh_gia_mau(MAU_KHOE)
        assert r == {"den": "XANH", "ly_do": ["on"]}

    def test_CPU_100_phan_tram_van_XANH_vi_chu_du_an_muon_75_80(self):
        assert MN.danh_gia_mau({**MAU_KHOE, "cpu_pct": 100.0, "cpu_max_nhan_pct": 100.0})["den"] == "XANH"

    @pytest.mark.parametrize("cm, den", [(2.0, "DO"), (2.99, "DO"), (3.0, "VANG"), (6.0, "VANG"), (7.99, "VANG"), (8.0, "XANH"), (30.0, "XANH")])
    def test_commit_con_lai(self, cm, den):
        assert MN.danh_gia_mau({**MAU_KHOE, "commit_con_lai_gb": cm})["den"] == den

    @pytest.mark.parametrize("r, den", [(1.0, "DO"), (1.49, "DO"), (1.5, "VANG"), (2.9, "VANG"), (3.0, "XANH"), (12.0, "XANH")])
    def test_ram_trong(self, r, den):
        assert MN.danh_gia_mau({**MAU_KHOE, "ram_trong_gb": r})["den"] == den

    def test_o_he_thong_het_cho_DO_o_du_lieu_chi_VANG(self):
        assert MN.danh_gia_mau({**MAU_KHOE, "dia_trong_gb": {"C:": 3.0, "G:": 210.0}})["den"] == "DO"
        assert MN.danh_gia_mau({**MAU_KHOE, "dia_trong_gb": {"C:": 15.0}})["den"] == "VANG"
        assert MN.danh_gia_mau({**MAU_KHOE, "dia_trong_gb": {"C:": 50.0, "G:": 1.0}})["den"] == "VANG"
        assert MN.danh_gia_mau({**MAU_KHOE, "dia_trong_gb": {"C:": 50.0, "G:": 100.0}})["den"] == "XANH"
        assert MN.danh_gia_mau({**MAU_KHOE, "dia_trong_gb": {"/": 3.0}})["den"] == "DO"        # Linux: goc la o he thong
        assert MN.danh_gia_mau({**MAU_KHOE, "dia_trong_gb": {"/mnt/du_lieu": 0.5}})["den"] == "XANH"   # khong phai o Windows

    def test_doc_file_trang_nhieu_VANG_it_thi_xanh(self):
        assert MN.danh_gia_mau({**MAU_KHOE, "trang_doc_moi_giay": 5000})["den"] == "VANG"
        assert MN.danh_gia_mau({**MAU_KHOE, "trang_doc_moi_giay": 200})["den"] == "XANH"

    def test_DO_thang_VANG_du_thu_tu_nao(self):
        a = MN.danh_gia_mau({**MAU_KHOE, "commit_con_lai_gb": 6.0, "ram_trong_gb": 1.0})
        b = MN.danh_gia_mau({**MAU_KHOE, "commit_con_lai_gb": 2.0, "ram_trong_gb": 2.5})
        assert a["den"] == b["den"] == "DO" and len(a["ly_do"]) == len(b["ly_do"]) == 2

    def test_thieu_so_do_thi_khong_phat_vi_khong_co_so(self):
        assert MN.danh_gia_mau({"luc": "x"})["den"] == "XANH"      # None != 0: khong do duoc khong phai 'het cho'


class TestMauThat:
    def test_mau_nhe_co_cac_truong(self):
        m = MN.mau(nang=False, chu_ky=0.05)
        for k in ("luc", "cpu_pct", "cpu_max_nhan_pct", "ram_trong_gb", "commit_con_lai_gb", "dia_trong_gb", "tien_trinh"):
            assert k in m, k
        assert 0 <= m["cpu_pct"] <= 100 and m["ram_trong_gb"] > 0 and isinstance(m["dia_trong_gb"], dict)
        assert {"python", "terminal64", "metatester64", "mt5_rss_gb"} <= set(m["tien_trinh"])

    def test_mau_nang_doc_them_hieu_nang_tu_WMI(self):
        mau = {"bo_nho": {"CommittedBytes": 10 * GB, "CommitLimit": 40 * GB, "AvailableBytes": 5 * GB, "PagesPersec": 20,
                          "PageReadsPersec": 1500, "PageFaultsPersec": 900},
               "dia": [{"Name": "0 C:", "PercentDiskTime": 40, "AvgDiskQueueLength": 1},
                       {"Name": "_Total", "PercentDiskTime": 55, "AvgDiskQueueLength": 2}]}
        m = MN.mau(nang=True, runner=runner_gia(mau=mau), chu_ky=0.05)
        assert (m["trang_doc_moi_giay"], m["loi_trang_moi_giay"]) == (1500, 900)
        assert (m["dia_ban_pct"], m["dia_hang_doi"]) == (55, 2)          # lay dong _Total, khong lay o dau tien
        assert len(m["cpu_tung_luong"]) >= 1
        assert MN.danh_gia_mau({**MAU_KHOE, **{k: m[k] for k in ("trang_doc_moi_giay",)}})["den"] == "VANG"

    def test_WMI_hong_ghi_loi_nhung_mau_van_con(self):
        m = MN.mau(nang=True, runner=runner_gia(loi="qua han 30s"), chu_ky=0.05)
        assert m["loi_wmi"] == "qua han 30s" and "cpu_pct" in m


class TestNhatKy:
    def test_ghi_doc_va_tom_tat(self, tmp_path):
        p = tmp_path / "mau.jsonl"
        r = MN.ghi_mau_nhe(duong=p)
        assert r["den"] in ("XANH", "VANG", "DO") and r["mau"]["cpu_pct"] is not None and r["ly_do"]
        MN.ghi_mau_nhe(duong=p)
        ds = MN.doc_nhat_ky(gio=1, duong=p)
        assert len(ds) == 2 and ds[0]["den"] in ("XANH", "VANG", "DO")
        assert MN.tom_tat_mau(ds)["so_mau"] == 2

    def test_khong_nem_khi_lay_mau_hong(self, tmp_path, monkeypatch):
        def hong(*a, **k):
            raise RuntimeError("psutil chet")
        monkeypatch.setattr(MN, "mau", hong)
        r = MN.ghi_mau_nhe(duong=tmp_path / "mau.jsonl")
        assert r["den"] is None and r["mau"] is None and "RuntimeError" in r["ly_do"][0]
        assert not (tmp_path / "mau.jsonl").exists()

    def test_khong_nem_khi_khong_ghi_duoc(self, tmp_path):
        chan = tmp_path / "la_mot_file"
        chan.write_text("x", encoding="utf-8")
        r = MN.ghi_mau_nhe(duong=chan / "mau.jsonl")                      # thu muc cha la FILE -> mkdir loi
        assert r["den"] is None

    def test_xoay_vong_khi_file_qua_12MB(self, tmp_path):
        p = tmp_path / "may_nha_mau.jsonl"
        p.write_bytes(b"x" * 12_000_001)
        MN.ghi_mau_nhe(duong=p)
        assert (tmp_path / "may_nha_mau.jsonl.1").stat().st_size == 12_000_001
        assert len(p.read_text(encoding="utf-8").splitlines()) == 1

    def test_doc_nhat_ky_bo_dong_hong_va_mau_cu(self, tmp_path):
        p = tmp_path / "m.jsonl"
        cu = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time() - 3 * 86400))
        moi = time.strftime("%Y-%m-%dT%H:%M:%S")
        p.write_text("khong phai json\n" + json.dumps({"luc": cu}) + "\n" + json.dumps({"luc": moi}) + "\n"
                     + json.dumps({"khong_co_luc": 1}) + "\n", encoding="utf-8")
        assert [d["luc"] for d in MN.doc_nhat_ky(gio=24, duong=p)] == [moi]
        assert MN.doc_nhat_ky(gio=24, duong=tmp_path / "khong_co.jsonl") == []

    def test_tom_tat_phan_bo_cpu_theo_dai_75_80(self):
        cpu = [50, 76, 78, 80, 95, 20]
        ds = [{"luc": "2026-10-03T10:0%d:00" % i, "cpu_pct": c, "ram_trong_gb": 10 - i, "commit_con_lai_gb": 20 - i,
               "dia_trong_gb": {"C:": 30.0 - i}, "den": "DO" if i == 5 else ("VANG" if i == 4 else "XANH"),
               "tien_trinh": {"python": i, "metatester64": 1 if i < 3 else 0, "terminal64": 0}} for i, c in enumerate(cpu)]
        t = MN.tom_tat_mau(ds)
        assert t["so_mau"] == 6 and t["tu"].endswith("10:00:00") and t["den"].endswith("10:05:00")
        assert t["pct_thoi_gian_trong_dai"] == 50.0 and t["pct_thoi_gian_duoi_dai"] == 33.3 and t["pct_thoi_gian_tren_dai"] == 16.7
        assert t["pct_duoi_30"] == 16.7 and t["cpu_p95"] == 95 and t["cpu_tb"] == round(sum(cpu) / 6, 1)
        assert (t["ram_trong_thap_nhat_gb"], t["commit_con_lai_thap_nhat_gb"], t["dia_c_thap_nhat_gb"]) == (5, 15, 25.0)
        assert (t["so_mau_den_do"], t["so_mau_den_vang"]) == (1, 1)
        assert t["mt5_chay_pct"] == 50.0 and t["python_tien_trinh_max"] == 5
        assert MN.tom_tat_mau([]) == {"so_mau": 0}

    def test_giam_sat_ghi_nhat_ky_va_tom_tat(self):
        dong = []
        r = MN.giam_sat(phut=0.01, chu_ky=0.2, nang=False, in_ra=dong.append)
        assert r["so_mau"] >= 1 and r["tom_tat"]["so_mau"] == r["so_mau"] and dong
        assert len(MN.doc_nhat_ky(gio=1)) == r["so_mau"]


# =============================================================== CO GIAN
class TestPhanTichCoGian:
    def test_tuyen_tinh_thi_bao_hoa_o_het_luong_va_80pct_cpu_ra_75pct_toc_do(self):
        r = MN.phan_tich_co_gian([diem(n, float(n)) for n in (1, 2, 4, 6, 8)], luong=8, nhan_vat_ly=4)
        assert r["n_bao_hoa"] == 8 and r["dinh"]["n"] == 8
        assert r["n_o_80pct_cpu"] == 6 and r["pct_toc_do_o_80_so_voi_dinh"] == 75.0 and r["hieu_suat_o_80pct"] == 1.0
        assert r["x_so_voi_1_tien_trinh_o_dinh"] == 8.0

    def test_nghen_bang_thong_bao_hoa_som_va_diem_qua_tai_bi_loai(self):
        pts = [diem(n, v) for n, v in DO_BANG_THONG] + [diem(24, 11.0)]      # n=24 > 20 luong: dinh gia do xep lich
        r = MN.phan_tich_co_gian(pts, luong=20, nhan_vat_ly=10)
        assert r["n_bao_hoa"] == 4                                            # tu 4 viec tro di them viec nao cung < 10%
        assert r["n_dat_90pct_dinh"] == 2                                     # 8.5 / 9.4 = 90,4%: hai viec da dat 90% dinh
        assert r["dinh"]["toc_do_tong"] == 9.4 and r["dinh"]["n"] <= 20     # khong lay diem qua tai lam dinh
        assert r["qua_tai_pct_so_voi_dinh"] == round(100 * 11.0 / 9.4, 1)
        assert r["loi_ich_hyperthreading_pct"] == 0.0

    def test_hyperthreading_va_xung_nhip(self):
        pts = [diem(n, v, mhz=m) for (n, v), m in zip(DO_CPU_NHO, (3100, 3100, 3000, 2900, 2800, 2600, 2500))]
        r = MN.phan_tich_co_gian(pts, luong=20, nhan_vat_ly=10)
        assert r["loi_ich_hyperthreading_pct"] == 30.0                       # 13.0 / 10.0
        assert (r["mhz_1_tien_trinh"], r["mhz_nhieu_nhat"]) == (3100, 2500)
        assert r["n_o_80pct_cpu"] == 16 and r["pct_toc_do_o_80_so_voi_dinh"] == round(100 * 11.8 / 13.0, 1)

    def test_khong_co_du_lieu_hoac_diem_loi_thi_bao_khong_du_lieu(self):
        assert MN.phan_tich_co_gian([], 8, 4) == {"du_lieu": False}
        assert MN.phan_tich_co_gian([{"n": 1, "toc_do_tong": 0.0}, {"n": 2, "toc_do_tong": 5.0, "loi": "x"}], 8, 4) == {"du_lieu": False}

    def test_chi_mot_diem_van_khong_chia_cho_0(self):
        r = MN.phan_tich_co_gian([diem(1, 3.0)], luong=4, nhan_vat_ly=2)
        assert r["du_lieu"] and r["n_bao_hoa"] == 1 and r["pct_toc_do_o_80_so_voi_dinh"] == 100.0


class TestDanhSachN:
    def test_nhanh_va_day_du(self):
        nhanh = MN.danh_sach_n(20, 10, True)
        day = MN.danh_sach_n(20, 10, False)
        assert nhanh == sorted(set(nhanh)) and {1, 10, 16, 20} <= set(nhanh) and len(nhanh) < len(day)
        assert {1, 10, 16, 20, 24} <= set(day)                               # co ca diem qua tai 1.2 x luong

    def test_tran_cat_cac_muc_lon(self):
        assert max(MN.danh_sach_n(20, 10, False, tran=12)) <= 12
        assert MN.danh_sach_n(20, 10, True, tran=1) == [1]

    def test_may_nho(self):
        n = MN.danh_sach_n(2, None, True)
        assert n[0] == 1 and max(n) == 2 and all(x >= 1 for x in n)


class TestDoThat:
    """Chay THAT vai tien trinh con, rat ngan (< 2 giay moi cai): cho thay kernel + vach xuat phat + gom ket qua chay duoc."""

    def test_nhan_cpu_nho_dem_duoc(self):
        assert MN._nhan_cpu_nho(0.05) > 0

    def test_bang_thong_dem_GB(self):
        assert MN._chuan_bi_bang_thong(2)(0.05) > 0

    def test_luoi_chay_chinh_engine_that(self):
        assert MN._chuan_bi_luoi(3000)(0.1) > 0

    def test_hai_tien_trinh_cpu_nho(self):
        r = MN.do_mot_buoc("cpu_nho", 2, 0.5)
        assert r["n"] == 2 and r["toc_do_tong"] > 0 and "loi" not in r

    def test_mot_tien_trinh_bang_thong_va_luoi(self):
        for loai, kw in (("bang_thong", {"mb": 2}), ("luoi", {"so_bar": 3000})):
            r = MN.do_mot_buoc(loai, 1, 0.4, **kw)
            assert r["n"] == 1 and r["toc_do_tong"] > 0 and "loi" not in r, (loai, r)

    def test_loai_la_bao_loi_chu_khong_treo(self):
        r = MN.do_mot_buoc("khong_co_loai_nay", 1, 0.2)
        assert "loi" in r and r["toc_do_tong"] == 0


class TestDoCoGianDieuPhoi:
    """`do()` voi `do_mot_buoc` gia: kiem logic chon muc N, bo qua, dieu kien may ranh - khong ton thoi gian do that."""

    @pytest.fixture
    def gia(self, monkeypatch):
        cuoc = []

        def mot(loai, n, giay, mb=64, so_bar=60_000):
            cuoc.append((loai, n, mb, so_bar))
            v = {"cpu_nho": float(min(n, 10)), "luoi": 5.0 * min(n, 10), "luoi_dai": float(min(n, 4)),
                 "bang_thong": 2.4 * min(n, 4)}[loai]
            return {"n": n, "toc_do_tong": v, "cpu_pct": min(100.0, 5.0 * n), "mhz": 2200}
        monkeypatch.setattr(MN, "do_mot_buoc", mot)
        monkeypatch.setattr(MN, "may_ranh", lambda *a, **k: (True, 4.0))
        return cuoc

    def test_may_ranh_thi_do_het_cac_loai_va_phan_tich(self, gia):
        q = quet_gia()
        q["nhan_c"] = {"san_sang": True}
        d = MN.do(nhanh=True, q=q, loai=("cpu_nho", "luoi_dai", "bang_thong"))
        assert d["trang_thai"] == "DAT" and d["nhieu_nen"] is False and d["luong"] == 20
        assert d["cpu_nho"]["phan_tich"]["n_bao_hoa"] >= 8 and d["luoi_dai"]["phan_tich"]["n_bao_hoa"] == 4
        bt = d["bang_thong"]
        assert bt["ly_thuyet_gbs"] == q["ram"]["bang_thong_ly_thuyet_gbs"] == 17.1
        assert bt["phan_tich"]["pct_so_voi_ly_thuyet"] == round(100 * 9.6 / 17.1, 1)
        assert all(32 <= p["mb_moi_mang"] <= 64 for p in bt["diem"])
        assert {c[3] for c in gia if c[0] == "luoi_dai"} == {MN.SO_BAR_DAI}      # chuoi dai that su duoc dung

    def test_khong_co_nhan_C_thi_bo_qua_chuoi_dai(self, gia):
        q = quet_gia()
        q["nhan_c"] = {"san_sang": False}
        d = MN.do(nhanh=True, q=q, loai=("luoi_dai", "cpu_nho"))
        assert "bo_qua" in d["luoi_dai"] and not any(c[0] == "luoi_dai" for c in gia)
        assert d["cpu_nho"]["phan_tich"]["du_lieu"]

    def test_tran_gioi_han_muc_n(self, gia):
        d = MN.do(nhanh=True, q=quet_gia(), loai=("cpu_nho",), tran=4)
        assert max(d["muc_n"]) <= 4 and max(c[1] for c in gia) <= 4

    def test_may_ban_thi_CHUA_DO_DUOC_khong_phai_so_xau(self, monkeypatch, gia):
        monkeypatch.setattr(MN, "may_ranh", lambda *a, **k: (False, 88.0))
        d = MN.do(nhanh=True, q=quet_gia(), loai=("cpu_nho",))
        assert d["trang_thai"] == "CHUA_DO_DUOC" and "88" in d["ly_do"] and not gia      # chua chay buoc nao

    def test_ep_do_khi_ban_thi_gan_nhieu_nen(self, monkeypatch, gia):
        monkeypatch.setattr(MN, "may_ranh", lambda *a, **k: (False, 88.0))
        d = MN.do(nhanh=True, ep=True, q=quet_gia(), loai=("cpu_nho",))
        assert d["trang_thai"] == "DAT" and d["nhieu_nen"] is True and gia

    def test_do_dia_chi_chay_khi_chon(self, monkeypatch, gia):
        monkeypatch.setattr(MN, "do_dia", lambda o: [{"o": "C:", "ghi_ngau_nhien_4k_iops": 9000, "loai_do_duoc": "nhanh (SSD)"}])
        d = MN.do(nhanh=True, q=quet_gia(), loai=("dia",))
        assert d["dia"][0]["o"] == "C:" and not gia


class TestDia:
    def test_ghi_dia_do_roi_xoa_sach(self, tmp_path):
        thu = tmp_path / "do"
        d = MN._ghi_dia(thu, 4, 20)
        assert d["ghi_tuan_tu_mbs"] > 0 and d["ghi_ngau_nhien_4k_iops"] > 0 and d["tre_fsync_ms_tb"] > 0 and "loi" not in d
        assert not list(thu.glob("may_nha_do_*.bin")), "file tam phai bi xoa"

    def test_ghi_dia_loi_thi_ghi_loi_khong_nem(self, tmp_path):
        chan = tmp_path / "la_file"
        chan.write_text("x", encoding="utf-8")
        d = MN._ghi_dia(chan / "con", 1, 1)
        assert "loi" in d and "ghi_tuan_tu_mbs" not in d

    def test_o_het_cho_thi_khong_do(self, tmp_path):
        r = MN.do_dia([{"o": str(tmp_path), "trong_gb": 0.5}, {"o": "", "trong_gb": 100}])
        assert all("khong du cho" in x["loi"] for x in r)
        assert not (tmp_path / "_may_nha_do_tam").exists()

    def test_o_du_cho_thi_do_va_don_thu_muc_tam(self, tmp_path):
        r = MN.do_dia([{"o": str(tmp_path), "trong_gb": 50.0}], mb=2, iops_lan=5)
        assert r[0]["o"] == str(tmp_path) and r[0]["ghi_tuan_tu_mbs"] > 0 and r[0]["loai_do_duoc"]
        assert not (tmp_path / "_may_nha_do_tam").exists(), "thu muc tam phai bi go"

    @pytest.mark.parametrize("iops, loai", [(100, "cham"), (499, "cham"), (500, "vua"), (4999, "vua"), (5000, "nhanh"), (90000, "nhanh")])
    def test_phan_loai_dia(self, iops, loai):
        assert MN.phan_loai_dia({"ghi_ngau_nhien_4k_iops": iops}).startswith(loai)

    def test_phan_loai_dia_khong_co_so_thi_None(self):
        assert MN.phan_loai_dia({}) is None


# =============================================================== SO TAI KHOAN MT5 TOI DA
class TestSoMt5ToiDa:
    def test_may_nha_nghen_bang_thong_thi_3_den_4(self, ram_gia):
        q = quet_gia()
        r = MN.so_mt5_toi_da(q, do_gia())                                    # dinh 9.4 GB/s / 2 GB/s moi agent
        assert r["tran"]["bang_thong"] == 4 and r["tran"]["ram"] == 9 and r["tran"]["cpu"] == 16
        assert r["tran_nho_nhat_do"] == "bang_thong" and r["agent_toi_da"] == 4
        assert r["tai_khoan_demo_toi_da"] == 4 and r["tai_khoan_demo_neu_xm_cho_dung_chung"] == 1
        assert r["che_do_toi_uu_hoa"] == {"terminal": 1, "agent": 4} and r["che_do_chay_don"] == {"terminal_toi_da": 4}
        assert r["bang_thong_nguon"] == "do" and r["ram_moi_agent_do_that"] is False and r["gb_moi_terminal_do_that"] is False

    def test_nang_len_nhieu_kenh_thi_RAM_thanh_tran(self, ram_gia):
        bt = [(n, min(35.0, 8.0 * n)) for n in CONG_N]                       # 35 GB/s: bang thong du nuoi 17 agent
        r = MN.so_mt5_toi_da(quet_gia(), do_gia(bang_thong=bt))
        assert r["tran"]["bang_thong"] == 17 and r["tran_nho_nhat_do"] == "ram" and r["agent_toi_da"] == 9

    def test_agent_that_da_do_thi_dung_so_that(self, ram_gia):
        q = quet_gia()
        q["mt5"] = {"agent_rss_gb_tb": 1.0, "thu_muc_du_lieu": [{"id": "ab12cd", "gb_bases": 12.0, "gb_tester": 3.0}]}
        r = MN.so_mt5_toi_da(q, do_gia())
        assert r["ram_moi_agent_do_that"] is True and r["ram_moi_agent_gb"] == 1.0 and r["tran"]["ram"] == 24
        assert r["gb_moi_terminal"] == 12.0 and r["gb_moi_terminal_do_that"] is True

    def test_dia_het_cho_thanh_tran(self, ram_gia):
        q = quet_gia(quet=ps_quet_gia(o_dia=[{"DeviceID": "C:", "Size": 127 * GB, "FreeSpace": 10 * GB, "FileSystem": "NTFS"}]))
        r = MN.so_mt5_toi_da(q, do_gia(bang_thong=[(n, 35.0) for n in CONG_N]))
        assert r["tran"]["dia"] == 1 and r["tran_nho_nhat_do"] == "dia" and r["agent_toi_da"] == 1

    def test_chua_do_thi_uoc_tu_ly_thuyet_va_ghi_ro_la_uoc(self, ram_gia):
        q = quet_gia()
        r = MN.so_mt5_toi_da(q, {})
        assert r["bang_thong_nguon"].startswith("uoc") and r["tran"]["bang_thong"] == 4   # 50% cua 17.1 GB/s = 8.55 -> 4
        assert r["tran"]["cpu"] == round(20 * 0.78) and r["agent_toi_da"] >= 1

    def test_khong_biet_gi_ve_bang_thong_thi_bo_tran_do_chu_khong_tra_0(self, ram_gia):
        q = quet_gia(loi="khong co lenh powershell")
        r = MN.so_mt5_toi_da(q, {})
        assert r["tran"]["bang_thong"] is None and r["agent_toi_da"] >= 1


# =============================================================== KET LUAN + BAO CAO
class TestKetLuan:
    def test_may_ngheng_RAM_noi_ro_cai_nghen_va_de_xuat_them_RAM(self, ram_gia):
        q = quet_gia()
        k = MN.ket_luan(q, do_gia(), MAU_KHOE)
        assert k["den"] == "XANH" or k["den"] == "VANG"
        tl = " ".join(k["tom_lai"])
        assert "Cai nghen thuc su" in tl and "~4 viec cung luc" in tl
        assert k["so"]["gioi_han_chinh"] == {"viec_nhe_trong_cache": "CPU", "viec_doc_nhieu_RAM": "bang thong RAM"}
        assert k["so"]["nang_ram_loi_toi_da_x"] == 4.0                       # tran = 4 kenh / 1 kenh hien co
        ram = [x for x in k["khuyen_nghi"] if "Them RAM" in x["viec"]]
        assert len(ram) == 1 and ram[0]["ai_lam"] == "chu_du_an" and ram[0]["can_phep"] is True
        assert "M393A4K40BB1-CRC" in ram[0]["viec"] and "CUNG LOAI" in ram[0]["viec"] and "RDIMM" in ram[0]["viec"]
        assert "Them 1 thanh: 1 -> 2 kenh" in ram[0]["viec"] and "them du 3 thanh: 4 kenh" in ram[0]["viec"]
        assert k["so"]["kenh_ram"] == {"dang_dung": 1, "toi_da_goi_y": 4, "toi_da_nen_tang": 4}

    def test_noi_ro_o_80pct_CPU_duoc_bao_nhieu_phan_tram_toc_do(self, ram_gia):
        k = MN.ket_luan(quet_gia(), do_gia(), MAU_KHOE)
        assert k["so"]["luong_o_80pct"] == 16 and k["so"]["pct_toc_do_o_80pct"] == round(100 * 11.8 / 13.0, 1)
        assert any("O ~78% CPU (16 viec song song) may dat 91% toc do toi da" in t for t in k["tom_lai"])
        assert any("hyperthreading" in t for t in k["tom_lai"])
        assert any("Giu tran CPU 75-80% la dung" in t for t in k["tom_lai"])    # >= 85% -> khong can day len 100%

    def test_khong_nghen_RAM_thi_noi_cai_gioi_han_la_CPU_va_KHONG_de_xuat_them_RAM_la_giai_phap(self, ram_gia):
        rong = [(n, 4.0 * n) for n in CONG_N]                                 # bang thong tuyen tinh: khong nghen
        d = do_gia(bang_thong=rong, luoi_dai=kernel(20, 10, [(n, float(n)) for n in CONG_N]))
        k = MN.ket_luan(quet_gia(), d, MAU_KHOE)
        assert any("Cai gioi han la CPU" in t for t in k["tom_lai"]) and not any("Cai nghen thuc su" in t for t in k["tom_lai"])
        assert k["so"]["gioi_han_chinh"]["viec_doc_nhieu_RAM"] == "CPU"
        assert "nang_ram_loi_toi_da_x" not in k["so"]

    def test_den_do_khi_mau_do_va_thanh_cau_dau_tien(self, ram_gia):
        k = MN.ket_luan(quet_gia(), None, {**MAU_KHOE, "commit_con_lai_gb": 2.0})
        assert k["den"] == "DO" and k["tom_lai"][0].startswith("Suc khoe may: DO")

    def test_thieu_nhan_C_thi_VANG_va_giao_cho_may_khong_phai_chu_du_an(self, ram_gia):
        q = quet_gia()
        q["nhan_c"] = {"san_sang": False, "trinh_bien": None, "ly_do": "khong co gcc/zig", "che_do": "auto"}
        k = MN.ket_luan(q, do_gia(), MAU_KHOE)
        z = [x for x in k["khuyen_nghi"] if "ziglang" in x["viec"]]
        assert k["den"] == "VANG" and len(z) == 1 and z[0]["ai_lam"] == "may" and z[0]["can_phep"] is False

    def test_co_nhan_C_thi_khong_nhac_ziglang(self, ram_gia):
        q = quet_gia()
        q["nhan_c"] = {"san_sang": True, "trinh_bien": "gcc", "ly_do": "", "che_do": "auto"}
        k = MN.ket_luan(q, do_gia(), MAU_KHOE)
        assert not any("ziglang" in x["viec"] for x in k["khuyen_nghi"])

    def test_ke_hoach_dien_Balanced_thi_de_xuat_High_performance_cho_chu_du_an(self, ram_gia):
        k = MN.ket_luan(quet_gia(), None, None)
        dien = [x for x in k["khuyen_nghi"] if "High performance" in x["viec"]]
        assert len(dien) == 1 and dien[0]["ai_lam"] == "chu_du_an" and "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c" in dien[0]["viec"]
        q = quet_gia(quet=ps_quet_gia(dien="Power Scheme GUID: 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c  (High performance)"))
        assert not any("High performance" in x["viec"] for x in MN.ket_luan(q, None, None)["khuyen_nghi"])

    def test_HDD_moi_thi_goi_y_pagefile_co_dinh_dung_van_va_noi_that_HDD_khong_nhanh_hon(self, ram_gia):
        k = MN.ket_luan(quet_gia(), None, None)
        pf = [x for x in k["khuyen_nghi"] if "File trang" in x["viec"]]
        assert len(pf) == 1 and pf[0]["ai_lam"] == "chu_du_an"
        assert "57 GB" in pf[0]["viec"]                                       # 25% cua HDD 230 GB, kep 32..64
        assert "LUOI AN TOAN" in pf[0]["viec"] and "Khong lam bo nho lam viec" in pf[0]["viec"]

    def test_khong_co_HDD_thi_khong_goi_y_pagefile_tren_HDD(self, ram_gia):
        q = quet_gia(quet=ps_quet_gia(dia_vat_ly=[{"FriendlyName": "SSD", "MediaType": 4, "BusType": 17, "Size": 256 * 10 ** 9,
                                                   "HealthStatus": "Healthy", "SpindleSpeed": 0}]))
        assert not any("File trang" in x["viec"] for x in MN.ket_luan(q, None, None)["khuyen_nghi"])

    def test_o_C_sap_het_cho_la_DO_va_dua_viec_cho_chu_du_an(self, ram_gia):
        q = quet_gia(quet=ps_quet_gia(o_dia=[{"DeviceID": "C:", "Size": 127 * GB, "FreeSpace": 2 * GB, "FileSystem": "NTFS"}]))
        k = MN.ket_luan(q, None, None)
        c = [x for x in k["khuyen_nghi"] if x["viec"].startswith("O C:")]
        assert k["den"] == "DO" and len(c) == 1 and c[0]["ai_lam"] == "chu_du_an"

    def test_RAM_du_4_kenh_thi_khong_de_xuat_them(self, ram_gia):
        quet = ps_quet_gia(ram_thanh=[thanh_ram("DIMM_%s1" % c) for c in "ABCD"])
        k = MN.ket_luan(quet_gia(quet=quet), None, None)
        assert not any("Them RAM" in x["viec"] for x in k["khuyen_nghi"]) and "kenh_ram" not in k["so"]

    def test_khe_day_thi_khong_de_xuat_them(self, ram_gia):
        quet = ps_quet_gia(ram_thanh=[thanh_ram("DIMM_A1")], ram_mang={"MemoryDevices": 1, "MaxCapacity": 67108864, "MaxCapacityEx": 0})
        k = MN.ket_luan(quet_gia(quet=quet), None, None)
        assert not any("Them RAM" in x["viec"] for x in k["khuyen_nghi"])

    def test_chi_gioi_han_toi_da_cua_nen_tang_2_kenh(self, ram_gia):
        quet = ps_quet_gia(cpu={"Name": "Intel(R) Core(TM) i7-9700K", "NumberOfCores": 8, "NumberOfLogicalProcessors": 8,
                                "MaxClockSpeed": 3600, "CurrentClockSpeed": 3600, "L3CacheSize": 12288})
        k = MN.ket_luan(quet_gia(quet=quet), None, None)
        assert k["so"]["kenh_ram"] == {"dang_dung": 1, "toi_da_goi_y": 2, "toi_da_nen_tang": 2}
        assert "them du" not in [x for x in k["khuyen_nghi"] if "Them RAM" in x["viec"]][0]["viec"]

    def test_luon_nhac_tran_cpu_78_cho_may_tu_lam(self, ram_gia):
        k = MN.ket_luan(quet_gia(), None, None)
        t = [x for x in k["khuyen_nghi"] if "tran CPU" in x["viec"]]
        assert len(t) == 1 and t[0]["ai_lam"] == "may" and "b tran-cpu 78" in t[0]["viec"]

    def test_tuyen_bo_so_tai_khoan_MT5_va_gia_dinh_duoc_ghi_ro(self, ram_gia):
        k = MN.ket_luan(quet_gia(), do_gia(), MAU_KHOE)
        assert any("tao toi da 4 tai khoan demo" in t for t in k["tom_lai"])
        mt = " ".join(t for t in k["tom_tat"] if t.startswith("MT5 tran"))
        assert "GIA DINH" in mt and "[bang thong la uoc]" not in mt         # RAM/agent la gia dinh; bang thong thi da do

    def test_chua_do_gi_thi_ket_luan_van_co_tom_tat_may_va_khong_nem(self, ram_gia):
        k = MN.ket_luan(quet_gia())
        assert k["tom_tat"][0].startswith("May: Intel(R) Xeon(R) CPU E5-2630 v4") and "10 nhan / 20 luong" in k["tom_tat"][0]
        assert "mt5" not in k["so"]                                           # khong co con so CHINH THUC khi chua do

    def test_chua_do_thi_van_tra_so_UOC_TAM_ghi_ro_la_uoc_va_chi_cach_do(self, ram_gia):
        k = MN.ket_luan(quet_gia())
        assert k["so"]["mt5_uoc_tam"]["bang_thong_nguon"].startswith("uoc") and k["so"]["mt5_uoc_tam"]["agent_toi_da"] == 4
        cau = [t for t in k["tom_lai"] if "UOC TAM" in t]
        assert len(cau) == 1 and "~4 tai khoan MT5" in cau[0] and "CHUA do" in cau[0] and "b may do --nhanh" in cau[0]

    def test_da_do_roi_thi_khong_con_cau_uoc_tam(self, ram_gia):
        k = MN.ket_luan(quet_gia(), do_gia(), MAU_KHOE)
        assert "mt5_uoc_tam" not in k["so"] and not any("UOC TAM" in t for t in k["tom_lai"])

    def test_may_khoe_van_co_dong_suc_khoe_xanh_de_phien_nha_biet_da_kiem_tra(self, ram_gia):
        k = MN.ket_luan(quet_gia(), None, MAU_KHOE)
        assert k["den"] == "XANH" and k["tom_lai"][0].startswith("Suc khoe may: XANH - on (CPU 78.0%")
        assert "RAM trong 12.0 GB" in k["tom_lai"][0] and "cam ket con lai 30.0 GB" in k["tom_lai"][0]
        assert not any(t.startswith("Suc khoe may") for t in MN.ket_luan(quet_gia(), None, None)["tom_lai"])   # khong co mau -> khong noi bua


class TestBaoCaoVanBan:
    def test_toan_ASCII_va_TOM_LAI_dung_truoc_so_lieu(self, ram_gia):
        q = quet_gia()
        van = MN.bao_cao_van_ban(q, do_gia(), MAU_KHOE)
        assert van.isascii(), [c for c in van if ord(c) > 127][:5]
        assert van.startswith("BAO CAO MAY NHA  [")
        i_tom, i_cu, i_may, i_so = (van.index(x) for x in ("TOM LAI:", "CHU DU AN CAN LAM:", "PHIEN NHA / MAY TU LAM:", "SO LIEU:"))
        assert i_tom < i_cu < i_may < i_so
        assert "Them RAM CUNG LOAI" in van and "b tran-cpu 78" in van

    def test_may_khoe_va_chua_do_thi_khong_co_muc_chu_du_an_can_lam_ngoai_de_xuat_that(self, ram_gia):
        q = quet_gia(quet=ps_quet_gia(ram_thanh=[thanh_ram("DIMM_%s1" % c) for c in "ABCD"],
                                      dien="Power Scheme GUID: 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c  (High performance)",
                                      dia_vat_ly=[{"FriendlyName": "SSD", "MediaType": 4, "BusType": 17, "Size": 256 * 10 ** 9,
                                                   "HealthStatus": "Healthy", "SpindleSpeed": 0}]))
        van = MN.bao_cao_van_ban(q, None, MAU_KHOE)
        assert "CHU DU AN CAN LAM:" not in van, van                          # im lang khi khong co gi can nguoi

    def test_ghi_bao_cao_ra_du_nam_file_trong_thu_muc_chi_dinh(self, tmp_path, ram_gia):
        q = quet_gia()
        d = do_gia()
        k = MN.ket_luan(q, d, MAU_KHOE)
        ra = MN.ghi_bao_cao(q, d, MAU_KHOE, k, thu_muc=tmp_path / "bc")
        assert set(ra) == {"quet", "do", "tinh_trang", "ket_luan", "md"}
        assert {Path(f).name for f in ra.values()} == {"may_nha_quet.json", "may_nha_do.json", "may_nha_tinh_trang.json",
                                                        "may_nha_ket_luan.json", "may_nha_bao_cao.md"}
        assert json.loads(Path(ra["ket_luan"]).read_text(encoding="utf-8"))["so"]["mt5"]["agent_toi_da"] == 4
        assert Path(ra["md"]).read_text(encoding="utf-8").isascii()

    def test_mac_dinh_ghi_vao_BAO_CAO_da_doi_huong_khong_cham_repo(self, tmp_path, ram_gia):
        ra = MN.ghi_bao_cao(quet_gia(), None, None, None)
        assert all(str(tmp_path) in f for f in ra.values())


class TestDongLenh:
    @pytest.fixture
    def gia(self, monkeypatch, ram_gia):
        q = quet_gia()
        monkeypatch.setattr(MN, "quet", lambda *a, **k: q)
        monkeypatch.setattr(MN, "mau", lambda nang=False, **k: dict(MAU_KHOE))
        return q

    def test_bao_cao_mac_dinh_in_tom_lai_va_ghi_file(self, gia, capsys, tmp_path):
        assert MN.main([]) == 0
        out = capsys.readouterr().out
        assert out.startswith("BAO CAO MAY NHA") and "TOM LAI:" in out and "SO LIEU:" in out
        assert (tmp_path / "reports" / "may_nha_bao_cao.md").exists() and (tmp_path / "reports" / "may_nha_tinh_trang.json").exists()

    def test_quet_in_JSON_day_du(self, gia, capsys, tmp_path):
        assert MN.main(["quet"]) == 0
        out = capsys.readouterr().out
        assert json.loads(out[out.index("{"):])["cpu"]["luong"] == 20
        assert (tmp_path / "reports" / "may_nha_quet.json").exists()

    def test_mau(self, gia, capsys):
        assert MN.main(["mau"]) == 0
        assert json.loads(capsys.readouterr().out)["cpu_pct"] == 78.0

    def test_do_may_ban_thoat_ma_1_va_ghi_ly_do(self, gia, capsys, monkeypatch, tmp_path):
        monkeypatch.setattr(MN, "do", lambda **k: {"trang_thai": "CHUA_DO_DUOC", "ly_do": "may dang ban (CPU nen 90%)"})
        assert MN.main(["do", "--nhanh"]) == 1
        assert "may dang ban" in capsys.readouterr().out
        assert (tmp_path / "reports" / "may_nha_do.json").exists() and not (tmp_path / "reports" / "may_nha_ket_luan.json").exists()

    def test_do_chuyen_dung_co_cho_do(self, gia, capsys, monkeypatch, tmp_path):
        thay = {}

        def do_gia_lap(**k):
            thay.update(k)
            return {"trang_thai": "DAT", **do_gia()}
        monkeypatch.setattr(MN, "do", do_gia_lap)
        assert MN.main(["do", "--nhanh", "--ep", "--toi-da", "8"]) == 0
        assert thay["nhanh"] is True and thay["ep"] is True and thay["tran"] == 8
        out = capsys.readouterr().out
        assert "tao toi da 4 tai khoan demo" in out
        assert (tmp_path / "reports" / "may_nha_ket_luan.json").exists()

    def test_giam_sat_chay_va_in_tom_tat(self, gia, capsys, monkeypatch, tmp_path):
        monkeypatch.setattr(MN, "giam_sat", lambda phut, ck, in_ra=None: {"tom_tat": {"so_mau": 3, "pct_thoi_gian_trong_dai": 66.7}, "so_mau": 3})
        assert MN.main(["giam-sat", "5", "10"]) == 0
        assert json.loads(capsys.readouterr().out)["so_mau"] == 3

    def test_lenh_la_in_cach_dung_va_thoat_2(self, capsys):
        assert MN.main(["xyz"]) == 2
        assert "b may" in capsys.readouterr().out


class TestDayDuBChay:
    def test_b_py_may_mau_chay_that_qua_cua_vao_b(self):
        r = subprocess.run([sys.executable, "b.py", "may", "mau"], cwd=str(REPO), capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stderr[-500:]
        d = json.loads(r.stdout[r.stdout.index("{"):])
        assert "cpu_pct" in d and "ram_trong_gb" in d

    def test_b_py_may_lenh_la_thoat_2(self):
        r = subprocess.run([sys.executable, "b.py", "may", "khong-co"], cwd=str(REPO), capture_output=True, text=True, timeout=120)
        assert r.returncode == 2 and "b may" in r.stdout

    def test_c_may_nam_trong_bang_LENH(self):
        import b as B
        assert B.LENH["may"] is B.c_may


# =============================================================== DANH SACH TRANG + HANG DOI + NHIP TIM
class TestDanhSachTrangMay:
    @pytest.mark.parametrize("lenh", [
        ["{py}", "b.py", "may", "quet"], ["{py}", "b.py", "may", "bao-cao"],
        ["{py}", "b.py", "may", "mau"], ["{py}", "b.py", "may", "mau", "--nang"],
        ["{py}", "b.py", "may", "do"], ["{py}", "b.py", "may", "do", "--nhanh"],
        ["{py}", "b.py", "may", "do", "--nhanh", "--ep", "--toi-da", "8"],
        ["{py}", "b.py", "may", "giam-sat"], ["{py}", "b.py", "may", "giam-sat", "30"], ["{py}", "b.py", "may", "giam-sat", "30", "15"],
    ])
    def test_cho_qua(self, lenh):
        assert CT.kiem_lenh(lenh) is None, CT.kiem_lenh(lenh)

    @pytest.mark.parametrize("lenh", [
        ["{py}", "b.py", "may"],                                             # tran khong co lenh con: phai goi ro `bao-cao`
        ["{py}", "b.py", "may", "ap-dung"],                                  # lenh 'doi cai dat' khong ton tai va khong duoc co
        ["{py}", "b.py", "may", "do", "--rm"],
        ["{py}", "b.py", "may", "do", "--toi-da", "65"],                     # ngoai 1..64
        ["{py}", "b.py", "may", "do", "--toi-da"],                           # thieu gia tri
        ["{py}", "b.py", "may", "do", "--toi-da", "8; rm -rf /"],
        ["{py}", "b.py", "may", "giam-sat", "999"],                          # > 180 phut
        ["{py}", "b.py", "may", "giam-sat", "30", "1"],                      # chu ky < 5 giay
        ["{py}", "b.py", "may", "giam-sat", "30", "15", "extra"],
        ["{py}", "b.py", "may", "mau", "--nang", "x"],
        ["{py}", "b.py", "may", "quet", "--ghi"],
        ["{py}", "b.py", "may", "powercfg", "/setactive"],
    ])
    def test_tu_choi(self, lenh):
        assert CT.kiem_lenh(lenh) is not None


class TestGiaoVaNhipTim:
    def test_giao_do_di_lan_TESTER_con_quet_di_lan_CPU(self, tmp_path):
        a = CM.giao(["may", "do", "--nhanh"], ma="may-do-1", goc=tmp_path, day=False)
        b = CM.giao(["may", "quet"], ma="may-quet-1", goc=tmp_path, day=False)
        c = CM.giao(["may", "giam-sat", "30"], ma="may-gs-1", goc=tmp_path, day=False)
        lan = lambda ma: json.loads((tmp_path / "viec" / "cho" / ("%s.json" % ma)).read_text("utf-8"))["lan"]   # noqa: E731
        assert (lan("may-do-1"), lan("may-quet-1"), lan("may-gs-1")) == ("TESTER", "CPU", "TESTER")
        assert a["ma"] == "may-do-1" and b["ma"] == "may-quet-1" and c["ma"] == "may-gs-1"

    def test_giao_lenh_may_la_bi_chan_ngay_luc_ra_don(self, tmp_path):
        with pytest.raises(ValueError):
            CM.giao(["may", "ap-dung"], goc=tmp_path, day=False)
        assert not list((tmp_path / "viec" / "cho").glob("*.json")) if (tmp_path / "viec" / "cho").exists() else True

    def test_lan_giao_cac_lenh_cu_khong_doi(self, tmp_path):
        CM.giao(["nc", "so-tay"], ma="a1", goc=tmp_path, day=False)
        CM.giao(["test"], ma="a2", goc=tmp_path, day=False)
        lan = lambda ma: json.loads((tmp_path / "viec" / "cho" / ("%s.json" % ma)).read_text("utf-8"))["lan"]   # noqa: E731
        assert (lan("a1"), lan("a2")) == ("CPU", "CPU")

    def test_nhip_tim_ghi_den_chi_ghi_lai_khi_doi_mau(self, tmp_path):
        c = {"ten": "may-a", "kha_nang": ["windows"]}
        f = tmp_path / "viec" / "may" / "may-a.json"
        assert CM.nhip_tim(tmp_path, c, "RANH", den="XANH") is True
        d = json.loads(f.read_text("utf-8"))
        assert d["den"] == "XANH" and "ly_do_den" not in d
        assert CM.nhip_tim(tmp_path, c, "RANH", den="XANH") is False         # cung mau, moi: khong rac lich su git
        assert CM.nhip_tim(tmp_path, c, "RANH", den="DO", ly_do_den="o C: con 2 GB") is True
        d = json.loads(f.read_text("utf-8"))
        assert d["den"] == "DO" and d["ly_do_den"] == "o C: con 2 GB"
        assert CM.nhip_tim(tmp_path, c, "RANH", den="DO", ly_do_den="o C: con 1 GB") is False   # doi LY DO ma khong doi mau: khong ghi
        assert CM.nhip_tim(tmp_path, c, "RANH", den="XANH") is True          # ve mau xanh thi bao

    def test_nhip_tim_cu_hon_mot_gio_thi_ghi_lai_du_cung_mau(self, tmp_path):
        c = {"ten": "may-a", "kha_nang": ["windows"]}
        f = tmp_path / "viec" / "may" / "may-a.json"
        CM.nhip_tim(tmp_path, c, "RANH", den="VANG", ly_do_den="x")
        d = json.loads(f.read_text("utf-8"))
        d["luc"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time() - 7200))
        f.write_text(json.dumps(d), encoding="utf-8")
        assert CM.nhip_tim(tmp_path, c, "RANH", den="VANG", ly_do_den="x") is True

    def test_ly_do_den_bi_cat_200_ky_tu(self, tmp_path):
        c = {"ten": "may-a", "kha_nang": []}
        CM.nhip_tim(tmp_path, c, "RANH", den="DO", ly_do_den="x" * 500)
        assert len(json.loads((tmp_path / "viec" / "may" / "may-a.json").read_text("utf-8"))["ly_do_den"]) == 200

    def test_bang_may_chi_in_dong_suc_khoe_khi_khong_xanh(self, tmp_path):
        c = {"ten": "may-a", "kha_nang": ["windows"]}
        CM.nhip_tim(tmp_path, c, "RANH", den="XANH")
        assert "suc khoe may" not in CM.bang_may(tmp_path)
        CM.nhip_tim(tmp_path, c, "RANH", den="DO", ly_do_den="o C: con 2 GB")
        assert "suc khoe may: DO - o C: con 2 GB" in CM.bang_may(tmp_path)

    def test_mau_may_tra_den_va_ly_do(self, monkeypatch):
        monkeypatch.setattr(MN, "ghi_mau_nhe", lambda: {"den": "VANG", "ly_do": ["a", "b"], "mau": {}})
        assert CM._mau_may() == ("VANG", "a; b")

    def test_mau_may_khong_bao_gio_nem(self, monkeypatch):
        def hong():
            raise OSError("dia day")
        monkeypatch.setattr(MN, "ghi_mau_nhe", hong)
        assert CM._mau_may() == (None, "")

    def test_mau_may_gioi_han_do_dai(self, monkeypatch):
        monkeypatch.setattr(MN, "ghi_mau_nhe", lambda: {"den": "DO", "ly_do": ["y" * 400], "mau": {}})
        den, ly = CM._mau_may()
        assert den == "DO" and len(ly) == 200


class TestNhipTimTrongBoChay:
    """`chay_mot_luot` ghi den vao nhip tim ma KHONG de loi giam sat lam hong viec chay."""

    def test_den_di_vao_nhip_tim_khi_may_ranh(self, tmp_path, monkeypatch):
        import subprocess as sp
        bare, hop = tmp_path / "t.git", tmp_path / "hop"
        sp.run(["git", "init", "--bare", "-b", "main", str(bare)], check=True, capture_output=True)
        sp.run(["git", "clone", "-q", str(bare), str(hop)], check=True, capture_output=True)
        for k, v in (("user.email", "t@t.t"), ("user.name", "t")):
            sp.run(["git", "-C", str(hop), "config", k, v], check=True, capture_output=True)
        CG.bao_dam_thu_muc(goc=hop)
        (hop / "README.md").write_text("x", encoding="utf-8")
        sp.run(["git", "-C", str(hop), "add", "-A"], check=True, capture_output=True)
        sp.run(["git", "-C", str(hop), "commit", "-m", "dau"], check=True, capture_output=True)
        sp.run(["git", "-C", str(hop), "push", "origin", "HEAD:main"], check=True, capture_output=True)
        lab = tmp_path / "lab"
        (lab / "reports").mkdir(parents=True)
        monkeypatch.setattr(CG, "GOC", lab)
        monkeypatch.setattr(CM, "GOC", lab)
        monkeypatch.setattr(CG, "CAU_HINH", tmp_path / "config" / "cau.json")
        monkeypatch.setattr(CG, "NGU_GIAY", (0, 0, 0))
        monkeypatch.setattr(CM, "_mau_may", lambda: ("VANG", "RAM trong con 2.5 GB (duoi 3)"))
        c = {"ten": "may-a", "hop_thu": str(hop), "nhanh": "main", "kha_nang": ["windows"], "session_cloud": "",
             "bao_cloud": False, "nhip_bao_phut": 30, "tom_tat_re": False}
        r = CM.chay_mot_luot(c)
        assert r["trang_thai"] == "XONG", r
        d = json.loads((hop / "viec" / "may" / "may-a.json").read_text("utf-8"))
        assert d["den"] == "VANG" and d["ly_do_den"].startswith("RAM trong con 2.5 GB")
        assert "suc khoe may: VANG" in CM.bang_may(hop)

    def test_loi_giam_sat_khong_lam_hong_luot_chay(self, tmp_path, monkeypatch):
        def hong():
            raise RuntimeError("giam sat chet")
        monkeypatch.setattr(MN, "ghi_mau_nhe", hong)
        assert CM._mau_may() == (None, "")
