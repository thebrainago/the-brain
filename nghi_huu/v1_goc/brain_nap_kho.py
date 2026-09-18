# -*- coding: utf-8 -*-
"""
brain_nap_kho.py - TANG NAP: loc kho ma nguon thanh UNG VIEN cho The Brain
=====================================================================================
Day la mieng ghep giua "cao/nap ve mot dong file" va "so dang ky cua The Brain".

VI SAO KHONG NAP THANG - doc truoc khi sua:

  1. **FDR toan cuc**. The Brain tinh nguong y nghia tren TOAN BO phep thu tich luy
     (`bh_fdr` trong the_brain.py). Da quan sat: 40 phep thu -> t~2,73; 306 phep thu ->
     t~3,48. Nghia la moi ung vien nap them **siet bar cho tat ca nhung cai da co**.
     Nap 5.000 script khong phai "co them 5.000 co hoi"; no la lam kho hon cho ca
     nhung y tuong tot da nam trong so. File nay IN RA cai gia do truoc khi nap.

  2. **`ly_do_kinh_te` la bat buoc** (brain_strategies.py dong 10-12). May doc code khong
     sinh ra duoc ly do kinh te. Vi vay file nay KHONG tu dang ky bat cu thu gi - no chi
     ra DANH SACH UNG VIEN kem cho trong de nguoi dien. Do la co y.

  3. **Ba cong chan cung** - loai truoc khi ton mot phep thu nao:
       martingale/grid  -> khong phai co che, la doi no tai khoan
       repaint          -> nhin truoc tra hinh
       nhom da dong so  -> momentum / moc gia / to hop chi bao: du an da chay 35.932 +
                           12,17 trieu to hop -> 0 song sot. Nap lai = tra tien FDR cho
                           cau tra loi da biet.

NGUON NAP: thu muc `nap_tay/` (chu du an tu lay ve hop le roi tha vao) - dung nguyen tac
cua brain_sources.py. Co the tro toi thu muc khac bang --tu.

CLI:
  python brain_nap_kho.py                                  # doc nap_tay/
  python brain_nap_kho.py --tu "F:/Download web/mql5_codebase/nguon"
  python brain_nap_kho.py --gia-fdr 200                    # xem gia phai tra neu nap 200 cai
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
REPORTS = HERE / "reports"
NAP_TAY = HERE / "nap_tay"
SO_DANG_KY = REPORTS / "BRAIN_registry.parquet"
RA_MD = REPORTS / "BRAIN_ung_vien.md"
RA_PQ = REPORTS / "BRAIN_ung_vien.parquet"

CO_CHE = {
    "bien dong / phong ho": ["atr", "volatility", "stddev", "bollinger", "keltner", "vix",
                             "chaikin", "envelope", "garch"],
    "dao chieu / qua ban": ["rsi", "stochastic", "cci", "williams", "wpr", "mfi", "ibs",
                            "oversold", "overbought", "reversal", "mean revers"],
    "xu huong / momentum": ["macd", "momentum", "adx", "moving average", "ema", "sma",
                            "trend", "ichimoku", "sar", "supertrend"],
    "khoi luong / dong tien": ["volume", "obv", "money flow", "accumulation", "vwap", "flow"],
    "moc gia / cau truc": ["fractal", "pivot", "support", "resistance", "fibo", "zigzag",
                           "donchian", "channel", "breakout", "order block"],
    "mua vu / lich": ["season", "day of week", "time filter", "session", "turn of month",
                      "opex", "expiry"],
    "vi cau truc / thanh khoan": ["spread", "order flow", "microstructure", "tick", "depth",
                                  "imbalance", "auction"],
    "quan tri von / lenh": ["risk", "money management", "trailing", "position size", "hedge"],
    "thong ke / hoc may": ["neural", "regression", "correlation", "hurst", "fourier",
                           "kalman", "bayes", "cluster", "machine learning"],
}
# Ba cong chan cung. Doc THAN MA NGUON, khong doc ten - khong ai dat ten file la martingale.
CHAN = {
    "martingale/grid": ["martingale", "averaging down", "recovery mode", "grid step",
                        "multiplier", "lot multiplier"],
    "repaint": ["repaint"],
}
# Nhom da dong so bang chinh ket qua cua du an - nap lai chi ton ngan sach FDR.
DA_DONG_SO = {"xu huong / momentum", "moc gia / cau truc"}

# CONG THU TU: cong cu / bang dieu khien / tien ich KHONG phai chien luoc.
# Bat duoc khi soi tay ket qua lan dau: TradingJournal, EA_Money_Management, CKS_Dashboard,
# zProfitLossCalendar, RuinExport deu lot qua vi co chu "volume"/"flow" trong ngu canh tinh lot.
# Dau hieu: khong sinh TIN HIEU VI THE - chi ve, dem, xuat bao cao, hoac chi tinh size.
CONG_CU = ["dashboard", "journal", "panel", "calculator", "export", "report",
           "utility", "monitor", "screener", "copier", "manager", "calendar"]


def la_cong_cu(ten, code):
    """Chien luoc thi phai co logic VAO LENH. Cong cu thi chi ve/dem/xuat."""
    if any(khop(t, ten) for t in CONG_CU):
        return True
    # khong he goi ham dat lenh -> khong the la chien luoc
    co_dat_lenh = re.search(r"OrderSend|PositionOpen|trade\.(Buy|Sell)\b|CTrade", code, re.I)
    ve_hoac_dem = re.search(r"ObjectCreate|Comment\s*\(|FileWrite", code, re.I)
    return (not co_dat_lenh) and bool(ve_hoac_dem)


def khop(tu, van_ban):
    """Tu <= 4 ky tu phai khop BIEN TU: 'atr' tung khop trong M-atr-ix lam hong ca bang."""
    mau = rf"\b{re.escape(tu)}\b" if len(tu) <= 4 else re.escape(tu)
    return re.search(mau, van_ban, re.I) is not None


def phan_loai(bang, van_ban):
    return [n for n, tu in bang.items() if any(khop(t, van_ban) for t in tu)]


def doc(fp):
    for enc in ("utf-8", "utf-16", "cp1252", "latin-1"):
        try:
            return fp.read_text(encoding=enc)
        except (UnicodeError, UnicodeDecodeError, OSError):
            continue
    try:
        return fp.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def bh_nguong(p, q=0.10):
    """Nguong p sau Benjamini-Hochberg - cung cong thuc voi the_brain.bh_fdr."""
    p = np.asarray([x for x in p if np.isfinite(x)], float)
    if len(p) == 0:
        return np.nan
    p = np.sort(p)
    m = len(p)
    k = np.where(p <= q * np.arange(1, m + 1) / m)[0]
    return float(p[k[-1]]) if len(k) else float(q / m)


def gia_fdr(them):
    """In cai gia phai tra khi nap them N phep thu vao so dang ky."""
    if not SO_DANG_KY.exists():
        print("  (chua co so dang ky - bo qua phan gia FDR)")
        return
    df = pd.read_parquet(SO_DANG_KY)
    cot_p = next((c for c in df.columns if c.lower() in ("p", "pval", "p_value", "p_mot_phia")),
                 None)
    n = len(df)
    print(f"\n  So dang ky hien co: **{n} phep thu**")
    if cot_p is None:
        print("  (khong tim thay cot p - chi bao so luong)")
    else:
        p = df[cot_p].to_numpy(float)
        cu = bh_nguong(p)
        # them `them` phep thu GIA DINH la null (p ~ U(0,1)) - kich ban trung binh
        gia_dinh = np.concatenate([p, np.random.default_rng(0).uniform(size=them)])
        moi = bh_nguong(gia_dinh)
        print(f"  Nguong p (BH, q=0.10) hien tai      : {cu:.5f}")
        print(f"  Nguong p neu nap them {them:>5} cai : {moi:.5f}  "
              f"({'SIET' if moi < cu else 'noi'} {abs(moi-cu)/max(cu,1e-12)*100:.0f}%)")
    print("  => Moi ung vien nap them lam KHO HON cho tat ca nhung cai da nam trong so.")
    print("     Day la ly do khong nap hang loat, khong phai su than trong tuy tien.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tu", default=None, help="thu muc nguon (mac dinh nap_tay/)")
    ap.add_argument("--gia-fdr", type=int, default=100, help="in gia FDR neu nap them N cai")
    args = ap.parse_args()

    goc = Path(args.tu) if args.tu else NAP_TAY
    if not goc.exists():
        sys.exit(f"khong thay thu muc {goc}")
    files = [f for f in goc.rglob("*")
             if f.is_file() and f.suffix.lower() in (".mq5", ".mqh", ".pine", ".txt", ".py")]
    print(f"=== TANG NAP: {len(files)} file trong {goc} ===")

    # ten chien luoc da co - de khoi nap trung
    da_co = set()
    try:
        sys.path.insert(0, str(HERE))
        import brain_strategies as bs
        da_co = set(bs.CHIEN_LUOC)
        print(f"  so dang ky dang co {len(da_co)} chien luoc")
    except Exception as e:
        print(f"  [khong doc duoc brain_strategies: {str(e)[:50]}]")

    hang, dem_chan = [], Counter()
    for fp in files:
        code = doc(fp)
        if len(code) < 200:
            dem_chan["file rong/qua ngan"] += 1
            continue
        ten = fp.stem
        chan = phan_loai(CHAN, code)
        co_che = phan_loai(CO_CHE, f"{ten} {code[:3000]}")
        ly_do = None                       # may KHONG sinh duoc - phai nguoi dien

        # ---------------------------------------------------------------------------
        # SUA 2026-07-28 sau phan hoi cua chu du an: ban truoc VUT BO 39/53 file. Do la
        # loc sai CAP DO. Du an dong so "momentum nhu mot CHIEN LUOC doc lap", khong dong
        # so "momentum nhu mot MANH TINH TOAN". Mot chi bao la cong thuc - lay ve, mo ra,
        # tu gan sizing/thoat lenh la viec hop ly.
        #
        # Ranh gioi dung khong phai "lay hay khong" ma la HAI VIEC KHAC NHAU:
        #   THU VIEN  - giu lai phep tinh. KHONG ton ngan sach FDR. Nen ROONG.
        #   UNG VIEN  - mot gia thuyet cu the dem di test. Moi cai siet bar cho ca 324
        #               phep thu da co. Nen CHAT.
        # Vi vay khong con "CHAN" nghia la vut; moi file duoc DINH TUYEN, va nhan
        # martingale/repaint la NHAN tren file chu khong phai lenh xoa.
        # ---------------------------------------------------------------------------
        nhan = list(chan)
        if la_cong_cu(ten, code):
            nhan.append("cong cu")
        if co_che and set(co_che) <= DA_DONG_SO:
            nhan.append("nhom da dong so")
        if ten.lower() in {t.lower() for t in da_co}:
            nhan.append("trung ten da nap")
        for n in nhan:
            dem_chan[n] += 1

        if "martingale/grid" in chan:
            # Van giu file: cong thuc sizing cua no la vi du CACH KHONG NEN lam, va phan
            # tin hieu ben trong co the van dung duoc. Chi cam DANG KY.
            lan = "THU VIEN (cam dang ky: martingale)"
        elif "repaint" in chan:
            lan = "THU VIEN (cam dang ky: repaint = nhin truoc)"
        elif "cong cu" in nhan:
            lan = "CHI DE HOC (ky thuat MQL5, khong sinh tin hieu)"
        elif "trung ten da nap" in nhan:
            lan = "THU VIEN (da co ban dang ky)"
        elif not co_che:
            lan = "CHO (chua doan duoc co che - doc tay)"
        elif set(co_che) <= DA_DONG_SO:
            # KHONG vut: giu lam thu vien, chi khong tu dong len ung vien.
            lan = "THU VIEN (nhom da dong so - giu phep tinh, khong dang ky lai)"
        else:
            lan = "UNG VIEN (can dien ly_do_kinh_te truoc khi nap)"
        trang_thai = lan

        # ham/cong thuc rut duoc ra thu vien - day moi la thu co gia tri tai su dung
        ham = re.findall(r"^\s*(?:double|int|bool|void|string|datetime)\s+(\w+)\s*\(",
                         code, re.M)
        hang.append(dict(file=fp.name, duong_dan=str(fp), so_dong=code.count("\n") + 1,
                         co_che=" | ".join(co_che) or "chua ro",
                         nhan=" | ".join(nhan), trang_thai=trang_thai,
                         lan=trang_thai.split(" ")[0],
                         so_ham=len(ham), ham=" ".join(sorted(set(ham))[:12]),
                         ly_do_kinh_te=ly_do or ""))

    df = pd.DataFrame(hang)
    if df.empty:
        sys.exit("khong co file nao doc duoc")
    df.to_parquet(RA_PQ, index=False)

    print(f"\n--- dinh tuyen (khong file nao bi vut) ---")
    for k, v in Counter(df["lan"]).most_common():
        print(f"  {k:12} {v:>4}")
    print(f"\n  tong ham rut duoc vao thu vien: {int(df['so_ham'].sum())} "
          f"tu {len(df)} file")
    print("\n--- nhan (mo ta, khong phai lenh xoa) ---")
    for k, v in dem_chan.most_common():
        print(f"  {k:24} {v:>4}")
    print("\n--- co che, tinh tren TOAN BO file ---")
    for k, v in Counter(c for r in df["co_che"] for c in r.split(" | ")).most_common():
        print(f"  {k:28} {v:>4}")

    gia_fdr(args.gia_fdr)

    ung_vien = df[df["trang_thai"].str.startswith("UNG VIEN")]
    md = ["# THE BRAIN - ung vien tu kho ma nguon", "",
          f"Nguon: `{goc}` — {len(files)} file, **{len(ung_vien)} ung vien** sau ba cong chan.", "",
          "> **Khong cai nao duoc tu dong nap.** `brain_strategies.py` bat buoc co "
          "`ly_do_kinh_te` — tai sao chien luoc nay PHAI co lai — va may doc code khong sinh ra "
          "duoc thu do. Cot duoi de trong la co y: dien tay, khong dien duoc thi khong nap.", "",
          "| file | cơ chế đoán được | dòng | lý do kinh tế (phải điền) |", "|---|---|---|---|"]
    for _, r in ung_vien.head(60).iterrows():
        md.append(f"| `{r['file']}` | {r['co_che']} | {r['so_dong']} | |")
    md += ["", "## Bị chặn", "", "| lý do | số file |", "|---|---|"]
    md += [f"| {k} | {v} |" for k, v in dem_chan.most_common()]
    RA_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"\n-> {RA_MD}\n-> {RA_PQ}")


if __name__ == "__main__":
    main()
