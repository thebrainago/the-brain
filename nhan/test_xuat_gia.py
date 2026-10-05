import tempfile
from pathlib import Path
import numpy as np, pandas as pd
from nhan import xuat_gia as X

def _df(n=50):
    i = pd.date_range("2024-01-01", periods=n, freq="15min", tz="Europe/Athens")
    p = 0.9 + np.cumsum(np.random.default_rng(1).normal(0, 1e-4, n))
    return pd.DataFrame({"open": p, "high": p + 1e-4, "low": p - 1e-4, "close": p, "tick_volume": 5, "spread": 3}, index=i)

def test_khu_tron():
    d = Path(tempfile.mkdtemp()); sl = Path(tempfile.mkdtemp())
    m = X.ghi(_df(), "AUDCAD", "M15", d, sl)
    assert m["so_bar"] == 50 and (sl / "AUDCAD_M15.csv.gz").exists()   # co ban sao luu ngoai thu muc dich
    r = X.doc("AUDCAD", "M15", d)
    assert len(r) == 50 and abs(r["close"].iloc[0] - _df()["close"].iloc[0]) < 1e-5
    assert r.index.tz is None   # UTC khong mui gio

def test_thieu_ohlc():
    try:
        X.ghi(pd.DataFrame({"x": [1]}, index=pd.date_range("2024", periods=1)), "A", "M15", Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp()))
    except ValueError:
        return
    assert False
