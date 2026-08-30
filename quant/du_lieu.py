# -*- coding: utf-8 -*-
"""du_lieu.py - Load du lieu OHLCV D1 tu Yahoo (yfinance) ve DataFrame.
Cache ra CSV trong lab/quant/data/ de lan sau khong phai tai lai.

Ca 3 tai san: S&P500 (^GSPC), vang (GC=F - futures, thay XAUUSD=X da delisted
tren Yahoo), EURUSD (EURUSD=X).
"""
from pathlib import Path
import pandas as pd

THU_MUC = Path(__file__).resolve().parent
DATA_DIR = THU_MUC / "data"
DATA_DIR.mkdir(exist_ok=True)

# symbol Yahoo: (nhan hien thi, ten day du)
SYMBOLS = {
    "^GSPC": ("SP500", "S&P 500 Index"),
    "GC=F":  ("XAU",   "Gold (GC=F futures, thay XAUUSD=X)"),
    "EURUSD=X": ("EURUSD", "EUR/USD"),
    "^NDX":     ("NDX",    "Nasdaq 100 Index"),
    "GBPUSD=X": ("GBPUSD", "GBP/USD"),
}

DEFAULT_PERIOD = "10y"


def flatten(df: pd.DataFrame) -> pd.DataFrame:
    """Yahoo tra ve MultiIndex cot khi nhieu symbol - don gian ve 1 cap."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    return df


def tai_yahoo(symbol: str, period: str = DEFAULT_PERIOD) -> pd.DataFrame:
    import yfinance as yf
    raw = yf.download(symbol, period=period, interval="1d", progress=False, auto_adjust=False)
    if raw is None or len(raw) == 0:
        raise RuntimeError(f"Khong lay duoc du lieu {symbol}")
    df = flatten(raw).copy()
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns=str.lower)
    keep = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
    df = df[keep].dropna()
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df


def nap(symbol: str, period: str = DEFAULT_PERIOD, cache: bool = True) -> pd.DataFrame:
    ten = SYMBOLS[symbol][0]
    f = DATA_DIR / f"{ten}_D1_{period}.csv"
    if cache and f.exists() and f.stat().st_size > 100:
        try:
            return pd.read_csv(f, index_col=0, parse_dates=True)
        except Exception:
            f.unlink(missing_ok=True)
    df = tai_yahoo(symbol, period=period)
    if cache:
        df.to_csv(f)
    return df


def nap_nhieu(symbols=None, period: str = DEFAULT_PERIOD) -> dict:
    if symbols is None:
        symbols = list(SYMBOLS.keys())
    return {s: nap(s, period=period) for s in symbols}


if __name__ == "__main__":
    import sys
    syms = sys.argv[1:] or list(SYMBOLS.keys())
    for s in syms:
        df = nap(s)
        print(s, "->", len(df), "nen |", df.index.min().date(), "->", df.index.max().date())
