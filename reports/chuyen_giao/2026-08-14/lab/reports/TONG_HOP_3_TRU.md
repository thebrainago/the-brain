# TỔNG HỢP 3 TRỤ (chạy SONG SONG)
> Lúc: 2026-08-12 21:20:08 · tổng thời gian: 25.1s (3 trụ chạy đồng thời)

## SEEKER
```
{
 "tru": "SEEKER",
 "so_nguon": 13,
 "nguon_uu_tien_cao": [
  "SSRN - Financial Economics/Trading",
  "Darwinex (1000 DARWIN)",
  "Myfxbook Autotrade/Verified"
 ],
 "so_ung_vien_qua_loc": 30,
 "ung_vien_top": [
  {
   "a": "VAJJ",
   "url": "https://www.darwinex.com/darwin/VAJJ",
   "loi_pct": 144.1,
   "dd_pct": -15.8,
   "diem": 1.636
  },
  {
   "a": "AACU",
   "url": "https://www.darwinex.com/darwin/AACU",
   "loi_pct": 119.3,
   "dd_pct": -8.9,
   "diem": 1.619
  },
  {
   "a": "XKA",
   "url": "https://www.darwinex.com/darwin/XKA",
   "loi_pct": 64.0,
   "dd_pct": -6.1,
   "diem": 1.414
  },
  {
   "a": "PHRT",
   "url": "https://www.darwinex.com/darwin/PHRT",
   "loi_pct": 60.2,
   "dd_pct": -5.2,
   "diem": 1.39
  },
  {
   "a": "LSP",
   "url": "https://www.darwinex.com/darwin/LSP",
   "loi_pct": 67.3,
   "dd_pct": -12.6,
   "diem": 1.384
  },
  {
   "a": "QEEU",
   "url": "https://www.darwinex.com/darwin/QEEU",
   "loi_pct": 72.3,
   "dd_pct": -7.3,
   "diem": 1.315
  },
  {
   "a": "MQOH",
   "url": "https://www.darwinex.com/darwin/MQOH",
   "loi_pct": 52.2,
   "dd_pct": -11.9,
   "diem": 1.245
  },
  {
   "a": "CFZ",
   "url": "https://www.darwinex.com/darwin/CFZ",
   "loi_pct": 46.4,
   "dd_pct": -9.5,
   "diem": 1.239
  },
  {
   "a": "MLTY",
   "url": "https://www.darwinex.com/darwin/MLTY",
   "loi_pct": 64.0,
   "dd_pct": -7.1,
   "diem": 1.224
  },
  {
   "a": "EJL",
   "url": "https://www.darwinex.com/darwin/EJL",
   "loi_pct": 48.7,
   "dd_pct": -12.9,
   "diem": 1.195
  }
 ],
 "goi_y_keyword": [],
 "giay": 0.0
}
```
## QUANTLAB
```
{
 "tru": "QUANTLAB",
 "giay": 3.1,
 "da_quet": 36,
 "dat": 0,
 "top": [
  {
   "lai": 5.86,
   "buy_hold": 3.59,
   "edge": 2.27,
   "pf": 1.256,
   "sharpe": 0.32,
   "so_lenh": 31,
   "placebo_p": 0.1,
   "era_edges": [
    -5.0,
    7.03
   ],
   "dat": false,
   "ten": "rsi_revert",
   "params": {
    "n": 14,
    "nhap": 30,
    "thoat": 55
   },
   "symbol": "EURUSD=X"
  },
  {
   "lai": 5.77,
   "buy_hold": 3.59,
   "edge": 2.18,
   "pf": 3.023,
   "sharpe": 0.637,
   "so_lenh": 10,
   "placebo_p": 0.03,
   "era_edges": [
    -3.5,
    5.38
   ],
   "dat": false,
   "ten": "rsi_revert",
   "params": {
    "n": 14,
    "nhap": 25,
    "thoat": 60
   },
   "symbol": "EURUSD=X"
  },
  {
   "lai": 1.46,
   "buy_hold": 3.59,
   "edge": -2.13,
   "pf": 1.027,
   "sharpe": 0.063,
   "so_lenh": 99,
   "placebo_p": 0.28,
   "era_edges": [
    -4.94,
    2.56
   ],
   "dat": false,
   "ten": "rsi_revert",
   "params": {
    "n": 7,
    "nhap": 30,
    "thoat": 55
   },
   "symbol": "EURUSD=X"
  },
  {
   "lai": 1.2,
   "buy_hold": 3.59,
   "edge": -2.39,
   "pf": 1.009,
   "sharpe": 0.052,
   "so_lenh": 204,
   "placebo_p": 0.21,
   "era_edges": [
    -11.87,
    9.82
   ],
   "dat": false,
   "ten": "momentum",
   "params": {
    "n": 50
   },
   "symbol": "EURUSD=X"
  },
  {
   "lai": -9.65,
   "buy_hold": 3.59,
   "edge": -13.24,
   "pf": 0.983,
   "sharpe": -0.103,
   "so_lenh": 75,
   "placebo_p": 0.43,
   "era_edges": [
    -15.34,
    1.94
   ],
   "dat": false,
   "ten": "sma_cross",
   "params": {
    "fast": 10,
    "slow": 50
   },
   "symbol": "EURUSD=X"
  },
  {
   "lai": -12.63,
   "buy_hold": 3.59,
   "edge": -16.22,
   "pf": 0.974,
   "sharpe": -0.152,
   "so_lenh": 34,
   "placebo_p": 0.52,
   "era_edges": [
    -14.91,
    -1.82
   ],
   "dat": false,
   "ten": "sma_cross",
   "params": {
    "fast": 20,
    "slow": 100
   },
   "symbol": "EURUSD=X"
  },
  {
   "lai": -15.66,
   "buy_hold": 3.59,
   "edge": -19.26,
   "pf": 0.967,
   "sharpe": -0.196,
   "so_lenh": 43,
   "placebo_p": 0.6,
   "era_edges": [
    -26.32,
    8.27
   ],
   "dat": false,
   "ten": "donchian",
   "params": {
    "n": 20
   },
   "symbol": "EURUSD=X"
  },
  {
   "lai": -17.33,
   "buy_hold": 3.59,
   "edge": -20.93,
   "pf": 0.963,
   "sharpe": -0.225,
   "so_lenh": 20,
   "placebo_p": 0.58,
   "era_edges": [
    -29.6,
    10.69
   ],
   "dat": false,
   "ten": "donchian",
   "params": {
    "n": 55
   },
   "symbol": "EURUSD=X"
  }
 ]
}
```
## BANKER
```
{
 "tru": "BANKER",
 "giay": 24.6,
 "loi": "cannot access free variable 'v' where it is not associated with a value in enclosing scope"
}
```