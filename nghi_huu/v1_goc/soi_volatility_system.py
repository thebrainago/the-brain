# -*- coding: utf-8 -*-
"""SOI KY ket qua 24/28 cua Volatility System — truoc khi tin.

Nghi van chinh: trong ban dau toi cho he CHI tra phi qua dem khi DANG MUA, con
mua-giu thi tra phi MOI NGAY. He nam o chieu ban khoang nua thoi gian, nen mot phan
"thang mua-giu" co the chi la TRA IT PHI HON, khong phai doan dung.

Bon bien the de tach tin hieu khoi chi phi:
  A. nhu ban dau        : he tra phi khi mua; mua-giu tra phi ca ky
  B. doi xung           : he tra phi ca hai chieu; mua-giu tra phi ca ky
  C. khong phi qua dem  : ca hai deu 0 phi qua dem  -> DO TIN HIEU THUAN
  D. moc kho hon        : he tra phi ca hai chieu, so voi mua-giu KHONG phi
                          (mua chi so/ETF that thi khong ton phi CFD)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import brain_co_che as bc
import thu_volatility_system as vs

REPORTS = Path(__file__).parent / "reports"


def chay_bien_the(df, v, phi_nam, ca_hai_chieu):
    o = df["open"].to_numpy()
    r = np.zeros(len(df)); r[1:] = np.log(o[1:] / o[:-1])
    vv = v.to_numpy()
    ngay = np.r_[0, np.diff(df.index.values).astype("timedelta64[D]").astype(float)]

    phi_spread = np.abs(np.diff(np.r_[0.0, vv])) * (vs.SPREAD_BPS / 1e4)
    if ca_hai_chieu:
        phi_dem = np.abs(vv) * phi_nam * ngay / 365.0
    else:
        phi_dem = np.where(vv > 0, phi_nam * ngay / 365.0, 0.0)
    return vv * r - phi_spread - phi_dem, r, ngay


def main():
    tt = bc.nap_tap_sang()
    bien = {
        "A. nhu ban dau (he tra phi khi MUA; mua-giu co phi)": (0.04, False, True),
        "B. doi xung (he tra phi CA HAI chieu; mua-giu co phi)": (0.04, True, True),
        "C. bo phi qua dem ca hai ben (TIN HIEU THUAN)": (0.0, True, False),
        "D. he tra phi hai chieu vs mua-giu KHONG phi": (0.04, True, False),
    }

    bang = {}
    for ten, (phi, hai_chieu, mg_co_phi) in bien.items():
        ket = []
        for khoa, df in tt.items():
            if len(df) < 800:
                continue
            v = vs.vi_the(df)
            if (v != 0).sum() < 200:
                continue
            r_he, r_mg, ngay = chay_bien_the(df, v, phi, hai_chieu)
            phi_mg = 0.04 if mg_co_phi else 0.0
            r_mg_net = r_mg - phi_mg * ngay / 365.0
            s_he = vs.chi_so(r_he, df.index)["sharpe"]
            s_mg = vs.chi_so(r_mg_net, df.index)["sharpe"]
            ket.append({"thi_truong": khoa, "thong_ke": float(s_he - s_mg),
                        "p": np.nan, "n": 0})
        g = bc.gop_thi_truong(ket, "thong_ke")
        bang[ten] = g
        print(f"{ten}")
        print(f"    {g['so_duong']}/{g['so_thi_truong']} thi truong hon mua-giu | "
              f"{g['nhom_duong']}/{g['so_nhom']} NHOM | trung vi {g['trung_vi']:+.3f} | "
              f"p(nhom)={g['p_theo_nhom']:.4f}")

    md = ["# SOI KY: Volatility System — tach tin hieu khoi chi phi", "",
          f"*{pd.Timestamp.now():%Y-%m-%d %H:%M}*", "",
          "> Ket qua ban dau 24/28 (7/7 nhom) dang ngo: he chi tra phi qua dem khi DANG "
          "MUA con mua-giu tra phi ca ky. He o chieu ban khoang nua thoi gian nen co the "
          "thang chi vi TRA IT PHI HON. Bang duoi tach hai thu do ra.", "",
          "| bien the | thi truong hon mua-giu | NHOM | trung vi hieu Sharpe | p theo nhom |",
          "|---|---|---|---|---|"]
    for ten, g in bang.items():
        md.append(f"| {ten} | {g['so_duong']}/{g['so_thi_truong']} | "
                  f"**{g['nhom_duong']}/{g['so_nhom']}** | {g['trung_vi']:+.3f} | "
                  f"**{g['p_theo_nhom']:.4f}** |")
    md.append("")
    (REPORTS / "BAO_CAO_VOLATILITY_SYSTEM.md").write_text(
        (REPORTS / "BAO_CAO_VOLATILITY_SYSTEM.md").read_text(encoding="utf-8")
        + "\n\n---\n\n" + "\n".join(md), encoding="utf-8")
    print(f"\n-> da noi vao BAO_CAO_VOLATILITY_SYSTEM.md")


if __name__ == "__main__":
    main()
