"""Test che_do_choi: nhan biet game, bo don TESTER / tuong tac, giam sat ha tran, het han thi giet."""
import os, subprocess, sys, time
from qwen import che_do_choi as CM

PY = sys.executable
ENV = dict(os.environ)

def test_nhan_biet_game():
    assert CM.dang_choi(["chrome.exe", "League of Legends.exe"]) == "League of Legends.exe"
    assert CM.dang_choi(["LEAGUECLIENT.EXE"]) == "LeagueClient.exe"          # khong phan biet hoa thuong
    assert CM.dang_choi(["chrome.exe", "terminal64.exe"]) is None
    assert CM.dang_choi([], {"game": ["abc.exe"]}) is None
    assert CM.dang_choi(["abc.exe"], {"game": ["abc.exe"]}) == "abc.exe"

def test_bo_don_nang_khi_choi():
    assert CM.duoc_chay_khi_choi({"lan": "TESTER", "lenh": ["{py}", "b.py"]})[0] is False
    assert CM.duoc_chay_khi_choi({"lan": "CPU", "lenh": ["{py}", "lay_export_man_hinh.py", "1"]})[0] is False
    assert CM.duoc_chay_khi_choi({"lan": "CPU", "lenh": ["{py}", "b.py", "nc", "cc", "thu_luoi", "{}"]}) == (True, "")
    assert CM.duoc_chay_khi_choi({"lan": "NHE", "lenh": ["{py}", "b.py", "link", "tham-do", "https://x"]})[0] is True

def test_so_nhan():
    assert CM.so_nhan_cho_phep({"tran_cpu_choi": 25}, 16) == 4
    assert CM.so_nhan_cho_phep({"tran_cpu_choi": 25}, 2) == 1      # toi thieu 1
    assert CM.so_nhan_cho_phep({"tran_cpu_choi": 100}, 8) == 8

def test_chay_binh_thuong_khong_ha():
    goi = []
    ma, ra, loi, ha = CM.chay_co_giam_sat([PY, "-c", "print('ok')"], ".", 30, ENV, ten_dang_chay=["chrome.exe"], ha=lambda p: goi.append(p) or True)
    assert ma == 0 and ra.strip() == "ok" and ha is False and goi == []

def test_dang_choi_thi_ha_tran():
    goi = []
    ma, ra, loi, ha = CM.chay_co_giam_sat([PY, "-c", "print('ok')"], ".", 30, ENV, ten_dang_chay=["League of Legends.exe"], ha=lambda p: goi.append(p) or True)
    assert ma == 0 and ha is True and len(goi) == 1

def test_ha_tran_that_tren_tien_trinh():
    p = subprocess.Popen([PY, "-c", "import time; time.sleep(5)"])
    try:
        assert CM.ha_tran(p.pid, {"tran_cpu_choi": 25}) is True
        import psutil
        assert psutil.Process(p.pid).nice() >= 10 or os.name == "nt"
    finally:
        p.kill()

def test_het_han_giet():
    t = time.time()
    try:
        CM.chay_co_giam_sat([PY, "-c", "import time; time.sleep(60)"], ".", 1.5, ENV, ten_dang_chay=[], nhip=0.5)
    except subprocess.TimeoutExpired:
        pass
    else:
        assert False, "phai het han"
    assert time.time() - t < 15

if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
