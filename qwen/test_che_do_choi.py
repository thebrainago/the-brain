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


def test_co_tay_bao_truoc(tmp_path, monkeypatch):
    f = tmp_path / "dang_choi.flag"
    monkeypatch.setattr(CM, "CO_TAY", f)
    assert CM.dang_choi([]) is None
    f.write_text("1")
    assert CM.dang_choi([]) == "(chu du an bao)"


# ---- het han phai giet CA CAY va KHONG BAO GIO treo vi ong dan (08/10/2026: p9, p11 ~594 phut tren don han 120 phut) ----
def _giet_theo_dong_lenh(mau: str) -> int:
    import psutil
    n = 0
    for p in psutil.process_iter(["cmdline"]):
        try:
            if mau in " ".join(p.info.get("cmdline") or []):
                p.kill()
                n += 1
        except Exception:
            pass
    return n


def _con_song(mau: str) -> bool:
    import psutil
    for p in psutil.process_iter(["cmdline"]):
        try:
            if mau in " ".join(p.info.get("cmdline") or []) and p.status() != psutil.STATUS_ZOMBIE:
                return True
        except Exception:
            pass
    return False


CHAU = ("import subprocess, sys, time\n"
        "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(%d)'])\n"      # chau thua huong stdout / stderr
        "time.sleep(60)\n")


def test_het_han_giet_ca_cay_ke_ca_chau():
    t = time.time()
    try:
        try:
            CM.chay_co_giam_sat([PY, "-c", CHAU % 241], ".", 1.5, ENV, ten_dang_chay=[], nhip=0.5)
        except subprocess.TimeoutExpired:
            pass
        else:
            assert False, "phai het han"
        assert time.time() - t < 20
        for _ in range(50):
            if not _con_song("sleep(241)"):
                break
            time.sleep(0.2)
        assert not _con_song("sleep(241)"), "tien trinh chau song sot sau khi het han"
    finally:
        _giet_theo_dong_lenh("sleep(241)")


def test_het_han_van_giet_duoc_khi_thieu_psutil(monkeypatch):
    if os.name == "nt":
        return                                          # tren Windows lop du phong la taskkill /T (khong test o cloud)
    monkeypatch.setitem(sys.modules, "psutil", None)    # `import psutil` -> ImportError
    t = time.time()
    try:
        try:
            CM.chay_co_giam_sat([PY, "-c", CHAU % 242], ".", 1.5, ENV, ten_dang_chay=[], nhip=0.5)
        except subprocess.TimeoutExpired:
            pass
        else:
            assert False, "phai het han"
        assert time.time() - t < 20
    finally:
        monkeypatch.undo()
        for _ in range(50):
            if not _con_song("sleep(242)"):
                break
            time.sleep(0.2)
        song = _con_song("sleep(242)")
        _giet_theo_dong_lenh("sleep(242)")
        assert not song, "killpg phai giet ca nhom khi khong co psutil"


def test_het_han_khong_treo_khi_chau_giu_ong_dan_ma_khong_giet_duoc(monkeypatch):
    # _giet_cay chi giet duoc tien trinh con truc tiep -> chau van giu ong stdout. Truoc day `p.communicate()` doi mai.
    def chi_giet_con(pid):
        import psutil
        psutil.Process(pid).kill()
    monkeypatch.setattr(CM, "_giet_cay", chi_giet_con)
    monkeypatch.setattr(CM, "GIAY_CHO_ONG_SAU_KHI_GIET", 2.0)
    t = time.time()
    try:
        try:
            CM.chay_co_giam_sat([PY, "-c", CHAU % 243], ".", 1.5, ENV, ten_dang_chay=[], nhip=0.5)
        except subprocess.TimeoutExpired:
            pass
        else:
            assert False, "phai het han"
        assert time.time() - t < 20, "bo chay bi treo vi ong dan"
    finally:
        _giet_theo_dong_lenh("sleep(243)")
