import numpy as np, pandas as pd
from nhan import hang_hoa as H

def _gia(n=252*20, mua_vu=0.0, chu_ky_ngay=0, hat=3):
    i = pd.bdate_range("2004-01-01", periods=n); rng = np.random.default_rng(hat)
    r = rng.normal(0, 0.01, n)
    if mua_vu: r += mua_vu * ((i.dayofyear >= 150) & (i.dayofyear < 165))
    if chu_ky_ngay: r += 0.004 * np.sin(2 * np.pi * np.arange(n) / chu_ky_ngay)
    c = 100 * np.exp(np.cumsum(r)); h = c * (1 + abs(rng.normal(0, .004, n))); l = c * (1 - abs(rng.normal(0, .004, n)))
    return pd.DataFrame({"open": c, "high": h, "low": l, "close": c}, index=i.rename("date"))

def test_mua_vu_hai_chieu():
    assert H.mua_vu_ngay(_gia(mua_vu=0.004), so_null=200)["trang_thai"] == "DAT"     # co that -> bat duoc
    assert H.mua_vu_ngay(_gia(), so_null=200)["trang_thai"] == "AM"                  # khong co -> tu choi
def test_chu_ky_hai_chieu():
    assert H.chu_ky(_gia(chu_ky_ngay=60), so_null=100)["trang_thai"] == "DAT"
    assert H.chu_ky(_gia(), so_null=100)["trang_thai"] == "AM"
def test_it_nam_chua_do_duoc():
    assert H.mua_vu_ngay(_gia(n=252*3))["trang_thai"] == "CHUA_DO_DUOC"
def test_ibs_du_lenh_va_phi():
    r = H.ibs_ngay(_gia()); assert r["so_lenh"] > 100 and r["trang_thai"] in ("DAT", "AM")
    assert H.ibs_ngay(_gia(), chi_phi_bps=0)["ky_vong_bps"] > r["ky_vong_bps"]
def test_tai_loi_ro_va_luu():
    import tempfile; from pathlib import Path
    def hong(u): raise OSError("403")
    try: H.tai("vang", get=hong, thu_muc=Path(tempfile.mkdtemp()))
    except RuntimeError as e: assert "stooq.com" in str(e)
    else: assert False
    d = Path(tempfile.mkdtemp())
    csv = "Date,Open,High,Low,Close,Volume\n" + "".join("2024-01-%02d,1,2,0.5,1.%d,10\n" % (k, k) for k in range(1, 10))
    f = H.tai("vang", get=lambda u: csv, thu_muc=d)
    assert len(H.doc("vang", d)) == 9 and f.exists()
    try: H.tai("vang", get=lambda u: "<html>blocked</html>" + " " * 60, thu_muc=d)
    except RuntimeError: pass
    else: assert False
