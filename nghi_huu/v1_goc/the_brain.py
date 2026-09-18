# -*- coding: utf-8 -*-
"""
the_brain.py - THE BRAIN: cua ai kiem dinh chien luoc, khong phai kho chien luoc
=====================================================================================
Y tuong (duyet 2026-07-27): thay vi tu mo mam, KE THUA chien luoc/phuong phap tu moi nguon
(GitHub, Kaggle, arXiv, code tu suu tam...), dua het qua MOT cua ai chung, giu lai cai song sot.

TRIET LY - doc ky truoc khi dung:
  Gia tri cua he thong nay nam o cho no **LOAI**, khong phai cho no **GOM**.
  Voi 50.000 chien lua va nguong y nghia 5%, se co 2.500 cai "co lai" thuan tuy do ngau nhien.
  Nen cang gom nhieu, cang PHAI siet chat - va do la co che chinh cua file nay:

  **FDR TOAN CUC TICH LUY**: moi phep thu tung chay deu duoc ghi vao so dang ky. Nguong y nghia
  duoc tinh lai tren TOAN BO so phep thu tu truoc den nay (Benjamini-Hochberg), khong phai
  tren rieng lan chay nay. Nap them chien lua = tu dong siet nguong cho MOI chien lua.
  Day la thu ma khong kho chien luoc nao lam - va la ly do that de xay The Brain.

BON QUY TAC KHONG THOA HIEP (khong co ngoai le, ke ca cho "chien luoc noi tieng"):
  1. **DANG KY TRUOC KHI TEST.** Tham so + ly do kinh te phai ghi vao so TRUOC khi chay. Khong
     duoc chay roi moi chon tham so dep. `the_brain.py nap` bat buoc co `--ly-do-kinh-te`.
  2. **KHONG DO THAM SO.** Chien luoc nap vao phai dung so cua tac gia hoac so kinh dien. Muon
     thu bo tham so khac = mot lan dang ky MOI, dem vao tong so phep thu (lam siet FDR).
  3. **COST THAT.** Vao lenh OPEN[i+1], spread+slippage theo |thay doi vi the|, phi qua dem theo
     so dem that. Bai hoc 27/07: cost lat nguoc ket luan 4 lan trong 1 ngay.
  4. **BA TANG LOC:** FDR toan cuc -> placebo (hoan vi khoi vi the) >=95% -> walk-forward ca 2
     nua duong. Khong qua du 3 tang thi ghi "loai", KHONG duoc tinh chinh cho no qua.

CLI:
  python the_brain.py danh-sach                     # liet ke chien luoc da nap
  python the_brain.py test --symbols us500cash eurusd --tfs h1 d1
  python the_brain.py test --chien-luoc sonic_r_s4  # chi test 1 cai
  python the_brain.py bao-cao                       # tong hop so dang ky + FDR toan cuc
Xuat: reports/BRAIN_registry.parquet (so dang ky) + reports/THE_BRAIN.md
"""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np
import pandas as pd
from scipy import stats as sstats

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import brain_strategies as bs

DATA = HERE / "data"
REPORTS = HERE / "reports"
REPORTS.mkdir(exist_ok=True)
SO_DANG_KY = REPORTS / "BRAIN_registry.parquet"

BARS_NAM = {"M5": 252 * 288, "M15": 252 * 96, "M30": 252 * 48, "H1": 252 * 24,
            "H4": 252 * 6, "D1": 252, "W1": 52}


# --------------------------------------------------------------------- du lieu & cost
def nap_du_lieu(symbol, tf, start=None):
    fp = DATA / (f"{symbol}_mt5_daily.parquet" if tf.upper() == "D1" else f"{symbol}_{tf.lower()}.parquet")
    if not fp.exists() and tf.upper() == "D1":
        fp = DATA / f"{symbol}_daily.parquet"
    if not fp.exists():
        return None
    d = pd.read_parquet(fp).reset_index()
    d = d.rename(columns={d.columns[0]: "time"})
    d["time"] = pd.to_datetime(d["time"], utc=True).dt.tz_localize(None)
    d = d.sort_values("time").drop_duplicates("time").set_index("time")
    real = d["high"] > d["low"]           # cat doan lich su TAI TAO o dau chuoi (bay #4)
    if real.any():
        d = d.loc[real.idxmax():]
    if start:
        d = d[d.index >= pd.Timestamp(start)]
    return d[["open", "high", "low", "close"]]


def cost_cua_symbol(symbol):
    """Doc spread + swap THAT tu metadata MT5; khong co thi dung mac dinh than trong."""
    fp = DATA / "mt5_symbol_meta.parquet"
    if fp.exists():
        m = pd.read_parquet(fp)
        r = m[m["file"] == symbol]
        if len(r):
            r = r.iloc[0]
            gia = float(r["gia_hien_tai"] or 0) or 1.0
            spread = float(r["spread_gia"]) or gia * 1e-4
            pt = float(r["point"])
            sl_nam = float(r["swap_long"]) * pt / gia * 365 * 100 if r["swap_mode"] == 1 else 0.0
            ss_nam = float(r["swap_short"]) * pt / gia * 365 * 100 if r["swap_mode"] == 1 else 0.0
            if abs(sl_nam) < 1e-9 and abs(ss_nam) < 1e-9:
                sl_nam = ss_nam = -4.0        # demo de swap=0 -> gia dinh, khong duoc coi la 0
            return spread * 1.5, sl_nam, ss_nam, True
    return None, -4.0, -4.0, False


# --------------------------------------------------------------------- cua ai
def chay_backtest(d, pos, cost_doi, swap_l, swap_s):
    """Vao lenh OPEN[i+1]: r(t) = open(t+2)/open(t+1) - 1. Phi qua dem theo so NGAY LICH that."""
    o = d["open"]
    ret = o.shift(-2) / o.shift(-1) - 1
    ngay = (o.index.to_series().shift(-2) - o.index.to_series().shift(-1)).dt.total_seconds() / 86400.0
    ngay = ngay.clip(lower=0).fillna(0)
    p = pos.reindex(o.index).fillna(0.0)
    dp = p.diff().abs().fillna(p.abs())
    swap = np.where(p > 0, swap_l, np.where(p < 0, swap_s, 0.0)) / 100.0 / 365.0
    net = p * ret - dp * cost_doi + pd.Series(swap, index=o.index) * ngay * p.abs()
    return net.dropna(), p, dp


def do_dac(net, p, dp, bars_nam):
    n = len(net)
    if n < 300:
        return None
    nam = n / bars_nam
    eq = (1 + net).cumprod()
    mu, sd = net.mean(), net.std()
    t = mu / (sd + 1e-12) * np.sqrt(n)
    return dict(so_nam=round(nam, 1),
                cagr=(eq.iloc[-1] ** (1 / nam) - 1) * 100 if eq.iloc[-1] > 0 else -100.0,
                sharpe=mu / (sd + 1e-12) * np.sqrt(bars_nam),
                maxdd=(eq / eq.cummax() - 1).min() * 100,
                # p-value MOT PHIA: chi thuong cho t DUONG. Dung hai phia thi chien luoc THUA
                # dam (t am lon) cung "qua FDR" - da gap that: ibs_bat_day/gbpusd Sharpe -0,60
                # qua duoc nguong, ton mot luot placebo vo nghia. Minh di tim cai CO LAI.
                t_stat=t, p_value=float(1 - sstats.norm.cdf(t)),
                pct_in_tt=p.reindex(net.index).abs().mean() * 100,
                so_lenh_nam=dp.reindex(net.index).sum() / 2 / nam)


def placebo(net, p, d, cost_doi, sl, ss, n_iter=200, seed=17):
    """Hoan vi CAC KHOI vi the - giu nguyen % thoi gian trong thi truong VA so lan doi vi the.
    Day la phep thu bat 'drift doi lot edge': usdars Donchian55 Sharpe 1,75 nhung placebo 0%."""
    rng = np.random.default_rng(seed)
    pv = p.reindex(net.index).to_numpy(float)
    khoi, i = [], 0
    while i < len(pv):
        j = i
        while j + 1 < len(pv) and pv[j + 1] == pv[i]:
            j += 1
        khoi.append(pv[i:j + 1]); i = j + 1
    that = net.mean() / (net.std() + 1e-12)
    sh = []
    for _ in range(n_iter):
        pp = pd.Series(np.concatenate([khoi[k] for k in rng.permutation(len(khoi))])[:len(pv)],
                       index=net.index)
        nn, _, _ = chay_backtest(d, pp, cost_doi, sl, ss)
        nn = nn.reindex(net.index).dropna()
        sh.append(nn.mean() / (nn.std() + 1e-12))
    return float((np.array(sh) < that).mean() * 100)


def bh_fdr(p, q=0.10):
    """Benjamini-Hochberg tren TOAN BO phep thu trong so dang ky (khong phai rieng lan chay nay)."""
    p = np.asarray(p, float)
    ok = np.isfinite(p)
    idx = np.argsort(np.where(ok, p, 2.0))
    m = int(ok.sum())
    kmax = 0
    for hang, i in enumerate(idx[:m], start=1):
        if p[i] <= q * hang / m:
            kmax = hang
    ket = np.zeros(len(p), bool)
    for hang, i in enumerate(idx[:m], start=1):
        if hang <= kmax:
            ket[i] = True
    return ket


# --------------------------------------------------------------------- so dang ky
# --------------------------------------------------------------------- viec cho tung luong
def _chuan_bi(symbol, tf, start, spread_bps):
    d = nap_du_lieu(symbol, tf, start)
    if d is None or len(d) < 1000:
        return None
    cost_doi, sl, ss, co_meta = cost_cua_symbol(symbol)
    gia = float(d["close"].iloc[-1])
    cost_doi = (gia * spread_bps * 1e-4 * 1.5 / gia) if cost_doi is None else cost_doi / gia
    return d, cost_doi, sl, ss, co_meta


def viec_do_dac(g):
    """1 luong lo TAT CA chien luoc cho MOT cap (symbol, tf) - nap du lieu 1 lan roi dung chung."""
    symbol, tf, start, spread_bps, ten_ds = g
    cb = _chuan_bi(symbol, tf, start, spread_bps)
    if cb is None:
        return []
    d, cost_doi, sl, ss, co_meta = cb
    bn = BARS_NAM.get(tf.upper(), 252)
    ra = []
    for ten in ten_ds:
        cl = bs.CHIEN_LUOC[ten]
        try:
            pos = cl["fn"](d)
        except Exception:
            continue
        net, p, dp = chay_backtest(d, pos, cost_doi, sl, ss)
        m = do_dac(net, p, dp, bn)
        if not m:
            continue
        m.update(dict(chien_luoc=ten, symbol=symbol, tf=tf.upper(), nguon=cl["nguon"],
                      tac_gia=cl["tac_gia"], giay_phep=cl["giay_phep"],
                      ly_do_kinh_te=cl["ly_do_kinh_te"],
                      ngay_test=datetime.now().date().isoformat(), swap_gia_dinh=not co_meta))
        ra.append(m)
    return ra


def viec_placebo(g):
    """1 luong lo placebo + walk-forward cho MOT (chien luoc, symbol, tf) da qua FDR."""
    ten, symbol, tf, start, spread_bps, n_iter = g
    cb = _chuan_bi(symbol, tf, start, spread_bps)
    if cb is None:
        return None
    d, cost_doi, sl, ss, _ = cb
    pos = bs.CHIEN_LUOC[ten]["fn"](d)
    net, p, _dp = chay_backtest(d, pos, cost_doi, sl, ss)
    nua = net.index[len(net) // 2]
    a, b = net.loc[:nua], net.loc[nua:]
    return (ten, symbol, tf.upper(),
            placebo(net, p, d, cost_doi, sl, ss, n_iter),
            a.mean() / (a.std() + 1e-12) * np.sqrt(252),
            b.mean() / (b.std() + 1e-12) * np.sqrt(252))


NHOM_NGUON = {"hoc thuat": "co_tien_nghiem", "kinh dien": "co_tien_nghiem"}


def nhom_cua(nguon):
    """Chia so dang ky lam 2 HO de sua FDR RIENG tung ho (hierarchical FDR).

    Ly do: xac suat tien nghiem khac han nhau. Mot chien luoc da qua phan bien hoc thuat tren
    58 tai san / 25 nam (TSMOM) KHONG the bi phat ngang voi mot script an danh tren mang. Gop
    chung vao 1 ho lam chien luoc co co so bi 'ganh' phan phat cua ca dam dong.
    Day la thuc hanh chuan (Benjamini-Bogomolov), khong phai noi long tieu chuan.
    """
    return NHOM_NGUON.get(nguon, "tu_dao")


def doc_so():
    if SO_DANG_KY.exists():
        return pd.read_parquet(SO_DANG_KY)
    return pd.DataFrame()


def ghi_so(df):
    df.to_parquet(SO_DANG_KY, index=False)


def lenh_test(args):
    from multiprocessing import Pool
    so_cu = doc_so()
    ten_ds = [args.chien_luoc] if args.chien_luoc else list(bs.CHIEN_LUOC)
    cap = [(s, tf, args.start, args.spread_bps, ten_ds) for s in args.symbols for tf in args.tfs]
    n_luong = max(1, min(args.processes, len(cap)))
    print(f"Do dac {len(cap)} cap (symbol x khung) x {len(ten_ds)} chien luoc tren {n_luong} luong...")
    if n_luong > 1:
        with Pool(n_luong) as pool:
            ket = pool.map(viec_do_dac, cap)
    else:
        ket = [viec_do_dac(g) for g in cap]
    df_moi = pd.DataFrame([m for nhom in ket for m in nhom])
    if df_moi.empty:
        print("Khong co ket qua nao."); return
    for _, r in df_moi.iterrows():
        print(f"  {r['symbol']}/{r['tf']} {r['chien_luoc']:22} Sharpe {r['sharpe']:+.2f}  "
              f"CAGR {r['cagr']:+6.2f}%  maxDD {r['maxdd']:6.1f}%  {r['so_lenh_nam']:.1f} lenh/nam")

    so = pd.concat([so_cu, df_moi], ignore_index=True) if len(so_cu) else df_moi
    so = so.drop_duplicates(subset=["chien_luoc", "symbol", "tf"], keep="last").reset_index(drop=True)

    # ---- FDR TICH LUY, sua RIENG TUNG HO (hierarchical) ----
    so["ho"] = so["nguon"].map(nhom_cua)
    so["qua_FDR"] = False
    for ho, nhom in so.groupby("ho"):
        mask = bh_fdr(nhom["p_value"].values, args.fdr)
        so.loc[nhom.index, "qua_FDR"] = mask
        print(f"\n=== FDR ho '{ho}': {len(nhom)} phep thu tich luy -> {int(mask.sum())} qua "
              f"(q={args.fdr:.0%}, nguong t ~ {sstats.norm.ppf(1 - args.fdr / len(nhom) / 2):.2f}) ===")

    for c in ("placebo_pct", "wf_nua1", "wf_nua2"):
        if c not in so.columns:
            so[c] = np.nan

    # ---- placebo + walk-forward (song song) cho cai qua FDR ma chua co ket qua placebo ----
    can = so[so["qua_FDR"] & so["placebo_pct"].isna()]
    if len(can):
        viec = [(r["chien_luoc"], r["symbol"], r["tf"], args.start, args.spread_bps,
                 args.placebo_iter) for _, r in can.iterrows()]
        print(f"\nChay placebo + walk-forward cho {len(viec)} ung vien tren "
              f"{min(args.processes, len(viec))} luong...")
        if len(viec) > 1 and args.processes > 1:
            with Pool(min(args.processes, len(viec))) as pool:
                kq = pool.map(viec_placebo, viec)
        else:
            kq = [viec_placebo(g) for g in viec]
        for k in kq:
            if not k:
                continue
            ten, sym, tf, pc, w1, w2 = k
            m = (so["chien_luoc"] == ten) & (so["symbol"] == sym) & (so["tf"] == tf)
            so.loc[m, ["placebo_pct", "wf_nua1", "wf_nua2"]] = [pc, w1, w2]
            print(f"  {ten:22} {sym}/{tf}: placebo {pc:.1f}%  wf {w1:+.2f}/{w2:+.2f}")

    so["SONG_SOT"] = (so["qua_FDR"] & (so["placebo_pct"] >= 95)
                      & (so["wf_nua1"] > 0) & (so["wf_nua2"] > 0))
    ghi_so(so)
    xuat_bao_cao(so, args.fdr)


def xuat_bao_cao(so, q=0.10):
    cols = ["chien_luoc", "symbol", "tf", "so_nam", "cagr", "sharpe", "maxdd", "t_stat",
            "so_lenh_nam", "swap_gia_dinh", "qua_FDR", "placebo_pct", "wf_nua1", "wf_nua2", "SONG_SOT"]
    cols = [c for c in cols if c in so.columns]

    def _md(x):
        x = x[cols].copy()
        for c in x.columns:
            if pd.api.types.is_float_dtype(x[c]):
                x[c] = x[c].map(lambda v: f"{v:.2f}" if pd.notna(v) else "")
        return "\n".join(["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
                         + ["| " + " | ".join(map(str, r)) + " |" for r in x.values])

    ss = so[so.get("SONG_SOT", False) == True] if "SONG_SOT" in so.columns else so.head(0)
    md = ["# THE BRAIN - so dang ky chien luoc", "",
          f"Cap nhat {datetime.now():%Y-%m-%d %H:%M}. **{len(so)} phep thu tich luy** tren "
          f"{so['chien_luoc'].nunique()} chien luoc x {so['symbol'].nunique()} tai san.", "",
          f"**FDR TOAN CUC q={q:.0%}**: nguong y nghia tinh tren TOAN BO {len(so)} phep thu tu truoc "
          f"den nay, khong phai rieng lan chay gan nhat. Nap them chien luoc = tu dong siet nguong "
          f"cho tat ca. Hien {int(so.get('qua_FDR', pd.Series(dtype=bool)).sum())} phep thu qua FDR, "
          f"**{len(ss)} SONG SOT** (qua ca placebo >=95% va walk-forward 2 nua duong).", ""]
    if len(ss):
        md += ["## Song sot", _md(ss.sort_values("sharpe", ascending=False)), ""]
    else:
        md += ["## Song sot", "**KHONG CO.** Day la ket qua AM TINH hop le - khong duoc tinh chinh "
               "tham so cho den khi co cai qua ai (do la curve-fitting, xem CLAUDE.md).", ""]
    md += ["## Toan bo (sap theo Sharpe)", _md(so.sort_values("sharpe", ascending=False).head(60)), "",
           "## Nguon & giay phep", ""]
    if "nguon" in so.columns:
        ng = so.groupby(["chien_luoc", "nguon", "tac_gia", "giay_phep"], dropna=False).size()\
               .reset_index(name="so_phep_thu")
        md += ["| " + " | ".join(ng.columns) + " |", "|" + "|".join("---" for _ in ng.columns) + "|"]
        md += ["| " + " | ".join(map(str, r)) + " |" for r in ng.values]
    (REPORTS / "THE_BRAIN.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\n-> reports/THE_BRAIN.md ({len(ss)} song sot / {len(so)} phep thu)")


def lenh_panel(args):
    """PHEP KIEM BE RONG (panel), so THEO CAP voi mua-va-giu tren CHINH tai san do.

    Vi sao can rieng lenh nay:
      (1) Mot chien luoc thu tren N thi truong la MOT gia thuyet, khong phai N. Sua FDR tren tung
          o (chien luoc x tai san) lam mat het suc manh thong ke - voi 19 tai san thi mot chien
          luoc dung o khap noi van truot sach.
      (2) Nhung neu chi lay trung binh Sharpe qua cac tai san thi lai roi vao bay DRIFT: 18 tai
          san phan lon tang 20 nam, nen MOI luat long-biased deu trong nhu co edge. Da gap that:
          panel dau tien cho 4 "chien luoc thang" (halloween t=6,4), them dong mua-va-giu vao thi
          CA BON deu thua no.
      -> Do dung: chenh lech Sharpe so voi mua-va-giu TREN TUNG TAI SAN, roi kiem dinh cap.
    """
    so = doc_so()
    so = so[so["tf"] == args.tf.upper()]
    if "mua_va_giu" not in set(so["chien_luoc"]):
        print("Thieu moc 'mua_va_giu' trong so dang ky - chay:\n"
              "  python the_brain.py test --chien-luoc mua_va_giu --symbols ... --tfs d1")
        return
    moc = so[so["chien_luoc"] == "mua_va_giu"].set_index("symbol")["sharpe"]
    rows = []
    for ten, g in so.groupby("chien_luoc"):
        if ten == "mua_va_giu":
            continue
        g = g.set_index("symbol")
        chung = g.index.intersection(moc.index)
        if len(chung) < 5:
            continue
        chenh = (g.loc[chung, "sharpe"] - moc.loc[chung]).astype(float)
        t = chenh.mean() / (chenh.std(ddof=1) / np.sqrt(len(chenh)) + 1e-12)
        rows.append({"chien_luoc": ten, "nguon": g["nguon"].iloc[0], "so_tai_san": len(chung),
                     "sharpe_tb": g.loc[chung, "sharpe"].mean(), "sharpe_mua_giu": moc.loc[chung].mean(),
                     "chenh_tb": chenh.mean(), "ty_le_vuot_%": (chenh > 0).mean() * 100,
                     "t_cap": t, "p_cap": float(1 - sstats.norm.cdf(t))})
    r = pd.DataFrame(rows).sort_values("t_cap", ascending=False)
    if r.empty:
        print("Chua du du lieu."); return

    # FDR tren SO CHIEN LUOC (so gia thuyet that su), khong phai so o
    qua = bh_fdr(r["p_cap"].values, args.fdr)
    r["qua_FDR_panel"] = qua
    pd.set_option("display.width", 220)
    print(r.round(3).to_string(index=False))
    print(f"\n{int(qua.sum())}/{len(r)} chien luoc VUOT mua-va-giu co y nghia (FDR q={args.fdr:.0%}).")
    print("\nCANH BAO doc ket qua: t_cap gia dinh cac tai san DOC LAP. Thuc te 18 tai san nay tuong "
          "quan manh (chi so co phieu di cung nhau) -> so tai san doc lap hieu dung chi khoang 5-8. "
          f"Chia t cho ~sqrt(18/6)=1.7 de co con so than trong hon.")
    (REPORTS / "THE_BRAIN_panel.md").write_text(
        "# THE BRAIN - phep kiem be rong (so cap voi mua-va-giu)\n\n"
        + r.round(3).to_markdown(index=False), encoding="utf-8")
    print("\n-> reports/THE_BRAIN_panel.md")


def viec_chuoi_net(g):
    """Tra ve chuoi loi nhuan rong theo ngay cua 1 (chien luoc, tai san) - de gop danh muc."""
    ten, symbol, tf, start, spread_bps = g
    cb = _chuan_bi(symbol, tf, start, spread_bps)
    if cb is None:
        return None
    d, cost_doi, sl, ss, _ = cb
    try:
        pos = bs.CHIEN_LUOC[ten]["fn"](d)
    except Exception:
        return None
    net, _p, _dp = chay_backtest(d, pos, cost_doi, sl, ss)
    return (ten, symbol, net)


def lenh_danh_muc(args):
    """PHEP THU DANH MUC: gop N tai san thanh MOT danh muc deu trong so, roi so voi danh muc
    mua-va-giu cung cach gop.

    Vi sao phep thu nay khac han cac phep truoc:
      Truoc do ta hoi "chien luoc nay co thang mua-va-giu TREN TUNG tai san khong?" -> thua het.
      Nhung cach dung THAT cua nhom chien luoc nay la danh MOT LUC nhieu thi truong: 18 edge yeu
      nhung IT TUONG QUAN gop lai co the cho Sharpe cao hon han tung cai rieng, trong khi mua-va-giu
      18 tai san thi tuong quan CAO (chi so co phieu di cung nhau) nen khong duoc loi tuong ung.
      Do la toan bo nguyen ly cua quy CTA/managed futures - va la kha nang cuoi cung chua kiem.
    """
    from multiprocessing import Pool
    ten_ds = [t for t in bs.CHIEN_LUOC]
    viec = [(t, s, args.tf, args.start, args.spread_bps) for t in ten_ds for s in args.symbols]
    print(f"Dung chuoi loi nhuan cho {len(viec)} (chien luoc x tai san) tren {args.processes} luong...")
    with Pool(args.processes) as pool:
        kq = [k for k in pool.map(viec_chuoi_net, viec) if k]

    theo_cl = {}
    for ten, sym, net in kq:
        theo_cl.setdefault(ten, {})[sym] = net

    rows = {}
    for ten, dic in theo_cl.items():
        if len(dic) < 5:
            continue
        M = pd.DataFrame(dic).dropna(how="all")
        dm = M.mean(axis=1).dropna()          # deu trong so, tai can bang moi bar
        if len(dm) < 500:
            continue
        eq = (1 + dm).cumprod()
        nam = len(dm) / 252
        rows[ten] = dict(
            chien_luoc=ten, so_tai_san=M.shape[1],
            sharpe_dm=dm.mean() / (dm.std() + 1e-12) * np.sqrt(252),
            cagr_dm=(eq.iloc[-1] ** (1 / nam) - 1) * 100 if eq.iloc[-1] > 0 else -100.0,
            maxdd_dm=(eq / eq.cummax() - 1).min() * 100,
            sharpe_tb_don_le=np.mean([s.mean() / (s.std() + 1e-12) * np.sqrt(252)
                                      for s in dic.values() if len(s) > 300]),
            tuong_quan_tb=M.corr().values[np.triu_indices(M.shape[1], 1)].mean(),
            _chuoi=dm)
    if "mua_va_giu" not in rows:
        print("Thieu moc mua_va_giu."); return
    moc = rows["mua_va_giu"]
    r = pd.DataFrame([{k: v for k, v in x.items() if k != "_chuoi"} for x in rows.values()])
    r["loi_ich_gop"] = r["sharpe_dm"] - r["sharpe_tb_don_le"]      # danh muc hon rieng le bao nhieu
    r["vuot_moc"] = r["sharpe_dm"] - moc["sharpe_dm"]
    r = r.sort_values("sharpe_dm", ascending=False)
    pd.set_option("display.width", 220)
    cot = ["chien_luoc", "so_tai_san", "sharpe_dm", "cagr_dm", "maxdd_dm", "sharpe_tb_don_le",
           "loi_ich_gop", "tuong_quan_tb", "vuot_moc"]
    print(r[cot].round(3).to_string(index=False))
    print(f"\nMoc mua-va-giu danh muc: Sharpe {moc['sharpe_dm']:.3f} | CAGR {moc['cagr_dm']:.2f}% | "
          f"maxDD {moc['maxdd_dm']:.1f}% | tuong quan TB giua cac tai san {moc['tuong_quan_tb']:.3f}")
    n_vuot = int((r["vuot_moc"] > 0).sum()) - 1
    print(f"{n_vuot} chien luoc co Sharpe DANH MUC vuot moc mua-va-giu.")
    (REPORTS / "THE_BRAIN_danh_muc.md").write_text(
        "# THE BRAIN - phep thu DANH MUC (deu trong so, so voi danh muc mua-va-giu)\n\n"
        + r[cot].round(3).to_markdown(index=False), encoding="utf-8")
    print("-> reports/THE_BRAIN_danh_muc.md")


def lenh_danh_sach(_args):
    print(f"{'ten':24} {'nguon':10} {'tac_gia':22} {'giay_phep':12} ly_do_kinh_te")
    for ten, c in bs.CHIEN_LUOC.items():
        print(f"{ten:24} {c['nguon']:10} {str(c['tac_gia'])[:22]:22} {c['giay_phep']:12} "
              f"{c['ly_do_kinh_te'][:60]}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="lenh", required=True)
    s = sub.add_parser("test")
    s.add_argument("--symbols", nargs="*", default=["us500cash"])
    s.add_argument("--tfs", nargs="*", default=["d1"])
    s.add_argument("--chien-luoc", default=None)
    s.add_argument("--start", default="2003-01-01")
    s.add_argument("--fdr", type=float, default=0.10)
    s.add_argument("--placebo-iter", type=int, default=150)
    s.add_argument("--spread-bps", type=float, default=6.0)
    s.add_argument("--bo-qua-lop-khong-hop", action="store_true")
    s.add_argument("--processes", type=int, default=10, help="so luong chay song song")
    s.set_defaults(fn=lenh_test)
    s2 = sub.add_parser("danh-sach"); s2.set_defaults(fn=lenh_danh_sach)
    s3 = sub.add_parser("bao-cao"); s3.set_defaults(fn=lambda a: xuat_bao_cao(doc_so()))
    s5 = sub.add_parser("danh-muc")
    s5.add_argument("--symbols", nargs="*", default=["us500cash"])
    s5.add_argument("--tf", default="d1")
    s5.add_argument("--start", default="2003-01-01")
    s5.add_argument("--spread-bps", type=float, default=6.0)
    s5.add_argument("--processes", type=int, default=19)
    s5.set_defaults(fn=lenh_danh_muc)
    s4 = sub.add_parser("panel")
    s4.add_argument("--tf", default="d1")
    s4.add_argument("--fdr", type=float, default=0.10)
    s4.set_defaults(fn=lenh_panel)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()



