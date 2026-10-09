# -*- coding: utf-8 -*-
"""SO EA DUNG LAI <-> MAY THU MT5: tim QUY LUAT BACKTEST (mini-Brain CanCuBo, 09/10/2026).

Chu du an 09/10: "mo xe 1 con bot ... thu ki tren gia lap va MT5 (co the cho may nha chay MT5 roi cat du lieu sang) nham so sanh va tim ra quy luat
backtest". `nhan/ea_cancubo_lai.py` da dung lai bot CCBSN (vang) tu LENH THAT va chung minh EA ra DUNG tung chuoi tren duong gia toi thieu. Con lai
cau hoi ma deal khong tra loi duoc: MAY THU MT5 sinh tick tu nen M1 NHU THE NAO? Tu deal that da biet: moi nen = 4 tick o giay 0 / 20 / 40 / 59, lenh
DAU chuoi luon o giay 0, lenh DCA o giay 40 (88%) / 20 (12%), thoat SL o giay 40 (87%) / 20 (10%) / 0 / 59 -> hop voi "Model 1 - 1 minute OHLC" va
thu tu cuc tri THEO MAU NEN (nen tang: open, LOW, HIGH, close; nen giam: open, HIGH, LOW, close). Nhung do moi la hop CHU CHUA KIEM voi nen M1 that
(Linux khong co gia). Module nay la dung cu kiem do:

  1. `kiem_luat_tick`  (CHI CAN nen M1 + deal goc, chay duoc tren Linux, khong can tester): voi MOI luat thu tu tick ung vien (`G.THU_TU_NEN`: theo_nen,
                       nguoc_nen, thap_truoc, cao_truoc, xen_ke) dung lai duong tick tu nen M1 roi hoi tung su kien cua deal goc co "hop le" khong:
                         - lenh DAU chuoi: gia = open + spread cua nen (giay 0) - kiem NGUYEN LIEU (spread M1, lech gio) chu khong phai luat;
                         - lenh DCA: tick DAU TIEN co ask <= gia lenh truoc - 100 pip phai la dung tick ghi trong deal (cung giay), gia = ask cua tick do;
                         - thoat TP: tick dau tien co bid >= muc TP phai la tick thoat;
                         - thoat SL: bid cua tick thoat <= muc SL va dinh bid truoc do >= muc SL + 15 pip (dieu kien can, KHONG phu thuoc SL truot hay bam theo).
                       Xep hang luat theo ti le su kien hop le; so luat tot nhat voi tung luat con lai bang kiem dau chinh xac (mot phia) tren cac su kien
                       hai luat KHAC nhau (`ket_luan`: RO / CHUA_RO / KHONG_KHOP). `do_lech_gio` quet lech gio (gio nen M1 kho <-> gio tester).
  2. `quet_mo_phong`  chay EA dung lai (C++ san gia) tren nen M1 voi tung luat x {SL chi doi len, SL bam theo} roi so CHUOI voi deal goc.
  3. `so_ba_chieu`    goc (bot goc tren tester) <-> mo phong (EA dung lai tren san gia) <-> tester (EA dung lai tren MT5 cua may nha, `chay_tester`).
  4. `tu_kiem`         thu CHINH dung cu tren gia tong hop co dap an (luat that biet truoc): dung cu phai chon dung luat, ra 100% o luat that, tu choi luat
                       sai, va cho biet can BAO NHIEU chuoi de phan biet duoc (do phan giai) - roi moi do tren du lieu that.

Viec can may nha (Linux khong tu lam duoc): nen M1 vang (`b xuat-gia XAUUSD M1 --tu .. --den ..`) de chay 1. va 2.; chay MT5 tester cho EA dung lai
(`che_do=tester`, Model 1 va 0) de chay 3. Hai viec nay cho den khi may nha nap ma moi (thu 20261008-165737-eea9 / 20261008-094857-6bd4).

  python -m nhan.so_ea_voi_tester tu-kiem [--ngay 20] [--seed 1]
  python -m nhan.so_ea_voi_tester luat [--thu-muc DIR] [--tu NGAY --den NGAY]     (doc nen M1 trong hop thu `du_lieu_gia`)
  python -m nhan.so_ea_voi_tester so   [--thu-muc DIR] [--tu NGAY --den NGAY]     (them quet mo phong va, neu co, bang vi the cua tester)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

from nhan import ea_cancubo_lai as C
from nhan import ea_gia_lap as G
from nhan import xuat_gia as XG

POINT = 0.01                         # buoc gia vang XM GOLD.i# (digits 2)
LUAT = G.THU_TU_NEN
VON_MO_PHONG = 100000.0              # von lon: khong ai bi stop-out (san gia khong co margin; xem ghi chu cua ea_cancubo_lai)
NGUONG_RO = 0.99                     # luat tot nhat phai hop le >= 99% su kien phan biet duoc luat ...
P_RO = 1e-6                          # ... va hon HAN luat ke tiep voi p <= P_RO (kiem dau chinh xac, mot phia)
NGUONG_KHONG_KHOP = 0.90             # luat tot nhat van duoi 90% -> khong luat nao trong danh sach giai thich duoc su kien
THU_MUC_RA = "so_ea_voi_tester"      # reports/<ten>/ (van ban) va <hop thu>/du_lieu_gia/<ten>/ (bang vi the .csv.gz)
TEP_TOI_DA = 38_000                  # bo chay don chi mang ve tep van ban <= 40.000 ky tu


# ==================================================================================================================== 1. GIA M1
def chuan_gia(bars: pd.DataFrame) -> pd.DataFrame:
    """Nen M1 -> bang sach: index thoi gian khong mui gio, tang dan, khong trung, CANH PHUT; cot open high low close spread (spread = point, nguyen;
    thieu cot -> 0). Hong (thieu OHLC, o trong, nen khong canh phut, high < max(open, close) hay low > min(...)) -> ValueError noi ro nen dau tien hong."""
    thieu = {"open", "high", "low", "close"} - set(bars.columns)
    if thieu:
        raise ValueError("nen M1 thieu cot %s (co %s)" % (sorted(thieu), list(bars.columns)))
    d = bars[[c for c in ("open", "high", "low", "close", "spread") if c in bars.columns]].copy()
    d.index = pd.to_datetime(d.index)
    if d.index.tz is not None:
        d.index = d.index.tz_convert("UTC").tz_localize(None)
    d = d[~d.index.duplicated(keep="last")].sort_index()
    if not len(d):
        raise ValueError("khong co nen M1 nao")
    if (d.index.second != 0).any() or (d.index.microsecond != 0).any():
        raise ValueError("nen M1 phai canh phut (nen dau tien lech: %s)" % d.index[(d.index.second != 0) | (d.index.microsecond != 0)][0])
    for c in ("open", "high", "low", "close"):
        d[c] = d[c].astype(float)
    if d[["open", "high", "low", "close"]].isna().any().any():
        raise ValueError("nen M1 co o trong (NaN) trong open / high / low / close")
    xau = (d["high"] < d[["open", "close"]].max(axis=1) - 1e-9) | (d["low"] > d[["open", "close"]].min(axis=1) + 1e-9)
    if xau.any():
        raise ValueError("nen M1 hong: high < max(open, close) hoac low > min(open, close) (nen dau tien: %s)" % d.index[xau][0])
    d["spread"] = d["spread"].fillna(0).round().astype(np.int64) if "spread" in d.columns else 0
    return d


def doc_gia(ma: str = "XAUUSD", tu: str | None = None, den: str | None = None, thu_muc=None) -> pd.DataFrame:
    """Nen M1 cua `ma` do may nha xuat (`b xuat-gia`) trong `thu_muc` (mac dinh hop thu `du_lieu_gia`), cat [tu, den] (den gom ca ngay cuoi)."""
    return chuan_gia(XG.doc_het(ma, "M1", Path(thu_muc) if thu_muc else None, tu, den))


def gia_tong_hop(ngay: float = 20, seed: int = 1, gia0: float = 1300.0, sigma_phut: float = 0.35, bat_dau="2019-03-04 00:00",
                 xac_suat_nhay: float = 0.0004) -> pd.DataFrame:
    """Nen M1 TONG HOP giong vang (duoi day Student-t4, bien do ~`sigma_phut` USD / phut, vai khoang trong gia luc mo nen, spread 18-32 point) DE THU DUNG CU,
    khong de ket luan ve thi truong. ~1380 nen / ngay. Cung `seed` -> cung nen. Gia tren luoi 0,01; high / low bao ca open / close."""
    rng = np.random.default_rng(seed)
    n = max(int(round(ngay * 1380)), 2)
    vi = 6                                                       # buoc vi mo trong 1 nen -> cuc tri that su nam giua open va close
    buoc = rng.standard_t(4, size=(n, vi)) * (sigma_phut / math.sqrt(vi)) / math.sqrt(2.0)       # phuong sai t(4) = 2
    nhay = np.where(rng.random(n) < xac_suat_nhay, rng.normal(0.0, 2.0, n), 0.0)
    dich = nhay + buoc.sum(axis=1)
    dong = gia0 + np.cumsum(dich)
    mo = dong - buoc.sum(axis=1)                                 # = dong nen truoc + khoang trong
    duong = mo[:, None] + np.cumsum(buoc, axis=1)
    cao, thap = np.maximum(duong.max(axis=1), mo), np.minimum(duong.min(axis=1), mo)
    q = lambda x: np.rint(x / POINT) * POINT                     # noqa: E731
    o, h, l, c = q(mo), q(cao), q(thap), q(dong)
    h, l = np.maximum.reduce([h, o, c]), np.minimum.reduce([l, o, c])
    sp = np.clip(np.rint(25 + 5 * np.sin(np.arange(n) / 700.0) + rng.integers(-2, 3, n)), 18, 32).astype(np.int64)
    return pd.DataFrame(dict(open=o, high=h, low=l, close=c, spread=sp), index=pd.date_range(bat_dau, periods=n, freq="min"))


# ==================================================================================================================== 2. LUAT TICK MUC SU KIEN
def luong_tick(bars: pd.DataFrame, luat: str, lech_s: int = 0) -> dict:
    """Duong tick cua `luat` tu nen M1 `bars` (da `chuan_gia`) o DON VI POINT NGUYEN: bid, sp (spread), t (giay epoch + `lech_s`)."""
    tk = G.tick_ohlc4(bars, luat, POINT)
    return dict(bid=np.rint(tk["bid"] / POINT).astype(np.int64), sp=np.rint(tk["spread"] / POINT).astype(np.int64),
                t=np.rint(tk["time"]).astype(np.int64) + int(lech_s))


def _tim(S: dict, giay: int) -> int:
    """Chi so tick co gio dung `giay`, hoac -1 (luat nay KHONG co tick o giay do)."""
    i = int(np.searchsorted(S["t"], giay))
    return i if i < len(S["t"]) and int(S["t"][i]) == giay else -1


def _p_dau(b: int, c: int) -> float:
    """P(X >= b), X ~ Binomial(b + c, 1/2): xac suat de mot luat tot hon luat kia it nhat `b` trong `b + c` su kien hai luat KHAC nhau, neu that ra
    hai luat ngang nhau (kiem dau chinh xac, mot phia). Khong co su kien phan biet (b + c = 0) -> 1."""
    n = b + c
    if n <= 0:
        return 1.0
    return float(sum(math.comb(n, k) for k in range(b, n + 1)) / 2 ** n)


def _kiem_chuoi(r, S: dict, ts: dict, slack: int = 0) -> list[tuple]:
    """Mot chuoi goc x mot duong tick -> danh sach (loai, hop_le, ly, chi_tiet). `loai`: vao | dca | tp | sl. `ly` khi sai: giay_la (luat khong co tick o giay
    do) | som_hon (co tick SOM hon cung thoa dieu kien) | khong_cham (den tick do van chua thoa) | sai_gia | khong_bang_ask | bid_tren_muc | dinh_thap."""
    pip_d = int(round(ts["InpPipSize"] / POINT))
    buoc_d = int(round(ts["InpStepPips"] * pip_d))
    init_d = int(round(ts["InpTrailInit"] * pip_d))
    t = [C._giay(x) for x in r.gio_cac_lenh]
    gia = [int(round(g / POINT)) for g in r.gia_cac_lenh]
    idx = [_tim(S, e) for e in t]
    bid, sp = S["bid"], S["sp"]
    ra = []
    if idx[0] < 0:
        ra.append(("vao", False, "giay_la", dict(giay=t[0] % 60)))
    else:
        ask = int(bid[idx[0]] + sp[idx[0]])
        ra.append(("vao", ask == gia[0], "" if ask == gia[0] else "khong_bang_ask",
                   dict(giay=t[0] % 60, quan_sat=gia[0], du_doan=ask, lech=gia[0] - ask)))
    for k in range(1, int(r.n)):
        ip, ik = idx[k - 1], idx[k]
        if ik < 0 or ip < 0:
            ra.append(("dca", False, "giay_la", dict(giay=t[k] % 60)))
            continue
        ask = bid[ip + 1:ik + 1] + sp[ip + 1:ik + 1]
        cham = np.flatnonzero(ask <= gia[k - 1] - buoc_d)
        if not len(cham):
            ra.append(("dca", False, "khong_cham", dict(giay=t[k] % 60, quan_sat=gia[k], ask_tai_tick=int(ask[-1]) if len(ask) else None)))
        elif ip + 1 + int(cham[0]) != ik:
            ra.append(("dca", False, "som_hon", dict(giay=t[k] % 60, tick_som_hon_giay=int(S["t"][ip + 1 + int(cham[0])]) - t[k])))
        elif int(ask[cham[0]]) != gia[k]:
            ra.append(("dca", False, "sai_gia", dict(giay=t[k] % 60, quan_sat=gia[k], du_doan=int(ask[cham[0]]))))
        else:
            ra.append(("dca", True, "", dict(giay=t[k] % 60)))
    if r.ly_do in ("tp", "sl") and not pd.isna(r.dong):
        ix, il = _tim(S, C._giay(r.dong)), idx[-1]
        muc = int(round(r.gia_ra / POINT))
        if ix < 0 or il < 0:
            ra.append((r.ly_do, False, "giay_la", dict(giay=C._giay(r.dong) % 60)))
        elif r.ly_do == "tp":
            cham = np.flatnonzero(bid[il + 1:ix + 1] >= muc)
            if not len(cham):
                ra.append(("tp", False, "khong_cham", dict(giay=C._giay(r.dong) % 60, muc=muc, bid_tai_tick=int(bid[ix]))))
            elif il + 1 + int(cham[0]) != ix:
                ra.append(("tp", False, "som_hon", dict(giay=C._giay(r.dong) % 60, tick_som_hon_giay=int(S["t"][il + 1 + int(cham[0])]) - C._giay(r.dong))))
            else:
                ra.append(("tp", True, "", dict(giay=C._giay(r.dong) % 60)))
        else:
            if int(bid[ix]) > muc:
                ra.append(("sl", False, "bid_tren_muc", dict(giay=C._giay(r.dong) % 60, muc=muc, bid_tai_tick=int(bid[ix]))))
            else:
                dinh = int(bid[il:ix].max()) if ix > il else int(bid[ix])
                ok = dinh >= muc + init_d - slack
                ra.append(("sl", ok, "" if ok else "dinh_thap", dict(giay=C._giay(r.dong) % 60, muc=muc, dinh=dinh, can=muc + init_d)))
    return ra


def _chuoi_trong_gia(ch: pd.DataFrame, bars: pd.DataFrame, lech_s: int = 0) -> pd.DataFrame:
    """Chuoi co lenh dau nam trong nen M1 `bars` va (neu da dong) dong trong khoang nen do (cho tick cuoi nen 59 giay). `lech_s` = gio deal - gio nen
    (cung nghia voi `luong_tick`): khoang nen duoc dich cung chieu."""
    if not len(ch):
        return ch
    dau = bars.index[0] + pd.Timedelta(seconds=int(lech_s))
    cuoi = bars.index[-1] + pd.Timedelta(seconds=59 + int(lech_s))
    mo = pd.to_datetime(ch["mo"])
    dong = pd.to_datetime(ch["dong"])
    return ch[(mo >= dau) & (mo <= cuoi) & (dong.isna() | (dong <= cuoi))]


def kiem_luat_tick(ch: pd.DataFrame, bars: pd.DataFrame, luat=LUAT, ts: dict | None = None, lech_s: int = 0, toi_da_vi_du: int = 4,
                   slack: int = 0) -> dict:
    """Kiem tung luat thu tu tick bang SU KIEN cua deal goc (xem docstring module). `ch` = bang chuoi goc (`C.doc_hai_nguon`), `bars` = nen M1.
    Chi chuoi nam tron trong `bars` va dong bang SL / TP duoc xet (chuoi thoat 'ea' / het gio khong co dieu kien tick de kiem).

    Tra {n_chuoi, n_xet, n_ngoai_gia, su_kien (dem theo loai), vao (kiem nguyen lieu: lenh dau = open + spread nen), luat {ten: {hop_le, sai, ti_le,
    theo_loai {loai: [dung, sai]}, ly_sai {ly: so}, vi_du_sai}}, xep_hang, tot_nhat, so_voi {luat: {tot_hon, kem_hon, p}}, ket_luan, ly_do, giay_quan_sat}.
    `ti_le` = dca + tp + sl hop le / tong (lenh dau KHONG tinh: no giong nhau o moi luat)."""
    ts = dict(C.THAM_SO_GOC, **(ts or {}))
    bars = chuan_gia(bars)
    luat = list(luat)
    trong = _chuoi_trong_gia(ch, bars, lech_s)
    xet = trong[trong["ly_do"].isin(["sl", "tp"])]
    ra = dict(n_chuoi=int(len(ch)), n_xet=int(len(xet)), n_ngoai_gia=int(len(ch) - len(trong)), luat={}, ghi_chu=[])
    seconds: dict[str, dict[int, int]] = {}
    vec: dict[str, list[bool]] = {}
    vao_dung = None
    for lt in luat:
        S = luong_tick(bars, lt, lech_s)
        theo = {k: [0, 0] for k in ("vao", "dca", "tp", "sl")}
        ly_sai: dict[str, int] = {}
        vi_du: list[dict] = []
        ok_vec: list[bool] = []
        lech_vao: dict[int, int] = {}
        for r in xet.itertuples():
            for loai, ok, ly, ct in _kiem_chuoi(r, S, ts, slack):
                theo[loai][0 if ok else 1] += 1
                if loai == "vao":
                    if not ok and "lech" in ct:
                        lech_vao[ct["lech"]] = lech_vao.get(ct["lech"], 0) + 1
                    continue
                ok_vec.append(bool(ok))
                if lt == luat[0]:
                    seconds.setdefault(loai, {})
                    seconds[loai][ct["giay"]] = seconds[loai].get(ct["giay"], 0) + 1
                if not ok:
                    ly_sai[ly] = ly_sai.get(ly, 0) + 1
                    if len(vi_du) < toi_da_vi_du:
                        vi_du.append(dict(chuoi=int(r.id), gio=str(r.mo), loai=loai, ly=ly, **ct))
        dung, sai = sum(theo[k][0] for k in ("dca", "tp", "sl")), sum(theo[k][1] for k in ("dca", "tp", "sl"))
        ra["luat"][lt] = dict(hop_le=dung, sai=sai, ti_le=(dung / (dung + sai)) if dung + sai else None, theo_loai=theo, ly_sai=ly_sai, vi_du_sai=vi_du)
        vec[lt] = ok_vec
        if vao_dung is None:
            vao_dung = dict(dung=theo["vao"][0], sai=theo["vao"][1], lech_diem=dict(sorted(lech_vao.items(), key=lambda x: -x[1])[:6]))
    ra["vao"] = vao_dung or dict(dung=0, sai=0, lech_diem={})
    ra["su_kien"] = {k: ra["luat"][luat[0]]["theo_loai"][k][0] + ra["luat"][luat[0]]["theo_loai"][k][1] for k in ("vao", "dca", "tp", "sl")} if luat else {}
    ra["giay_quan_sat"] = {k: dict(sorted(v.items())) for k, v in seconds.items()}
    xh = sorted(luat, key=lambda l: (-(ra["luat"][l]["ti_le"] or 0.0), -ra["luat"][l]["hop_le"], luat.index(l)))
    ra["xep_hang"], ra["tot_nhat"] = xh, (xh[0] if xh else None)
    ra["so_voi"] = {}
    if len(xh) > 1:
        a = np.asarray(vec[xh[0]], bool)
        for lt in xh[1:]:
            b_ = np.asarray(vec[lt], bool)
            tot, kem = int((a & ~b_).sum()), int((~a & b_).sum())
            ra["so_voi"][lt] = dict(tot_hon=tot, kem_hon=kem, p=_p_dau(tot, kem))
    ra["ket_luan"], ra["ly_do"] = _ket_luan(ra)
    return ra


def _ket_luan(ra: dict) -> tuple[str, str]:
    tot = ra.get("tot_nhat")
    if tot is None or not ra["n_xet"]:
        return "CHUA_DO_DUOC", "khong co chuoi nao nam trong khoang nen M1 de kiem (n_xet = 0)"
    ti = ra["luat"][tot]["ti_le"]
    if ti is None:
        return "CHUA_DO_DUOC", "chuoi da xet khong co su kien DCA / thoat de phan biet luat"
    if ti < NGUONG_KHONG_KHOP:
        return "KHONG_KHOP", ("luat tot nhat (%s) chi giai thich %.1f%% su kien (< %.0f%%): khong luat nao trong danh sach dung - kiem lech gio (do_lech_gio), "
                              "semantics spread cua nen M1 (muc `vao`), hoac tester dung luat khac" % (tot, 100 * ti, 100 * NGUONG_KHONG_KHOP))
    p_max = max((v["p"] for v in ra["so_voi"].values()), default=0.0)
    yeu = [l for l, v in ra["so_voi"].items() if v["p"] > P_RO]
    if ti >= NGUONG_RO and not yeu:
        return "RO", "%s giai thich %.2f%% su kien; hon moi luat con lai voi p <= %.1e" % (tot, 100 * ti, p_max)
    return "CHUA_RO", ("luat tot nhat %s (%.2f%%) nhung %s" % (tot, 100 * ti, ("chua hon han %s (p toi da %.1e > %.0e): can them chuoi" % (yeu, p_max, P_RO))
                                                                 if yeu else "chua dat nguong %.0f%%" % (100 * NGUONG_RO)))


def do_lech_gio(ch: pd.DataFrame, bars: pd.DataFrame, gio=range(-6, 7)) -> dict:
    """Quet LECH GIO giua nen M1 trong kho va deal: voi moi lech `h` (gio), bao nhieu chuoi co gia lenh dau == open nen (lech h) + spread cua nen do.
    Lech dung -> gan nhu moi chuoi khop; lech sai -> khop ngau nhien (rat it). Tra {n_chuoi, khop {h: so}, tot_nhat, ti_le}."""
    bars = chuan_gia(bars)
    ma_open = {int(t): (int(round(o / POINT)), int(s)) for t, o, s in zip(bars.index.values.astype("datetime64[s]").astype(np.int64), bars["open"], bars["spread"])}
    mo = [(C._giay(pd.Timestamp(r.gio_cac_lenh[0]).floor("min")), int(round(r.gia_cac_lenh[0] / POINT))) for r in ch.itertuples()]
    khop = {int(h): 0 for h in gio}
    for t, g in mo:
        for h in khop:
            v = ma_open.get(t - h * 3600)
            if v is not None and v[0] + v[1] == g:
                khop[h] += 1
    tot = max(khop, key=lambda h: (khop[h], -abs(h))) if khop else None
    return dict(n_chuoi=len(mo), khop=khop, tot_nhat=tot, ti_le=(khop[tot] / len(mo)) if mo and tot is not None else None)


# ==================================================================================================================== 3. MO PHONG
def bien_dich(vao: list[int]):
    """Viet EA dung lai (mang gio vao = `vao`) roi bien dich bang san gia -> duong exe. Khong co trinh bien dich C++ -> RuntimeError."""
    with tempfile.TemporaryDirectory(prefix="ccbl_so_") as d:
        exe = G.bien_dich(C.viet_ea(vao, Path(d) / "ea_CanCuBoLai.mq5"))
    if exe is None:
        raise RuntimeError("khong co trinh bien dich C++ (c++ / g++ / clang++): khong chay duoc san gia")
    return exe


def chay_mo_phong(exe, bars: pd.DataFrame, luat: str, ratchet: int = 1, ts: dict | None = None, von: float = VON_MO_PHONG) -> tuple[pd.DataFrame, dict]:
    """EA dung lai tren duong tick `luat` cua nen M1 -> (bang chuoi, ket qua san gia). `ratchet` 1 = SL chi doi len, 0 = SL bam theo loi hien tai."""
    tk = G.tick_ohlc4(bars, luat, POINT)
    res = G.chay(exe, tk, von, tham_so=dict(ts or {}, InpTrailRatchet=int(ratchet)), digits=2, hop_dong=C.HOP_DONG, lot=C.LOT_VANG)
    if not res["ok"]:
        raise RuntimeError("EA khong chay duoc tren san gia (luat %s): ma thoat %s %s" % (luat, res["ma_thoat"], str(res["loi"])[-300:]))
    return C.chuoi_tu_vi_the(C.vi_the_tu_ket_qua(res, tk)), res


def _khoa_phut(c: pd.DataFrame) -> set:
    return {C._giay(pd.Timestamp(t).floor("min")) for t in c["mo"]}


def quet_mo_phong(ch: pd.DataFrame, bars: pd.DataFrame, luat=LUAT, ratchet=(1, 0), ts: dict | None = None, von: float = VON_MO_PHONG, toi_da_lech: int = 3) -> dict:
    """EA dung lai chay tren nen M1 voi tung (luat x ratchet), so CHUOI voi deal goc (`C.so_chuoi`). Tap chuoi duoc so = chuoi goc dong bang SL / TP nam tron
    trong nen; CUA VAO phat lai = dung gio lenh dau cua cac chuoi do (EA bo qua gio vao khi chuoi dang mo, giong bot goc). Chuoi goc dong tay ('ea') hoac con
    mo qua het nen khong co hanh vi tick de kiem va se giu cho cua vao ke sau, nen KHONG phat lai. Tra {n_goc, bang (xep theo so chuoi khop giam dan: luat,
    ratchet, khop, chung, n_goc, n_lai, dem_lech, chi_tiet), tot_nhat, khop_tuyet_doi}."""
    bars = chuan_gia(bars)
    trong = _chuoi_trong_gia(ch, bars)
    goc = trong[trong["ly_do"].isin(["sl", "tp"])]
    ra = dict(n_goc=int(len(goc)), bang=[], tot_nhat=None, khop_tuyet_doi=False)
    if not len(goc):
        return ra
    exe = bien_dich(C.thoi_diem_vao(goc))                 # phat lai CHI cua vao cua chuoi dem so (chuoi dong tay / dang mo khong lam EA bo lo cua vao sau)
    giu = _khoa_phut(goc)
    for lt in luat:
        for r in ratchet:
            lai, res = chay_mo_phong(exe, bars, lt, r, ts, von)
            lai = lai[[C._giay(pd.Timestamp(t).floor("min")) in giu for t in lai["mo"]]] if len(lai) else lai
            so = C.so_chuoi(goc, lai, toi_da=toi_da_lech)
            ra["bang"].append(dict(luat=lt, ratchet=int(r), khop=so["khop"], chung=so["chung"], n_goc=so["n_goc"], n_lai=so["n_lai"], dem_lech=so["dem_lech"],
                                   chi_tiet=so["chi_tiet"], chi_goc=len(so["chi_goc"]), chi_lai=len(so["chi_lai"])))
    ra["bang"].sort(key=lambda x: (-x["khop"], x["n_lai"] != x["n_goc"]))
    ra["tot_nhat"] = {k: ra["bang"][0][k] for k in ("luat", "ratchet", "khop", "chung")} if ra["bang"] else None
    b = ra["bang"][0] if ra["bang"] else None
    ra["khop_tuyet_doi"] = bool(b and b["khop"] == b["chung"] == b["n_goc"] == b["n_lai"])
    return ra


# ==================================================================================================================== 4. SO BA CHIEU
def tong_hop_chuoi(c: pd.DataFrame) -> dict:
    d = c[c["ly_do"].isin(["sl", "tp"])]
    return dict(n=int(len(d)), n_lenh=int(d["n"].sum()), loi=round(float(d["loi"].sum()), 2), tp=int((d["ly_do"] == "tp").sum()), sl=int((d["ly_do"] == "sl").sum()),
                sau_nhat=int(d["n"].max()) if len(d) else 0)


def so_ba_chieu(goc: pd.DataFrame, mo_phong: pd.DataFrame, tester: pd.DataFrame | None = None, nguong: float = 0.99) -> dict:
    """Ba bang chuoi cung mot cua so: goc (bot goc tren tester), mo_phong (EA dung lai tren san gia), tester (EA dung lai tren MT5 may nha).
    Tra so chuoi khop tung cap + tong ket + `chan_doan` bang loi thuong: tach loi 'dung lai sai' khoi loi 'luat backtest sai'."""
    ra = dict(tong_hop=dict(goc=tong_hop_chuoi(goc), mo_phong=tong_hop_chuoi(mo_phong)))
    ra["goc_mo_phong"] = C.so_chuoi(goc, mo_phong)
    ti = {"goc_mo_phong": _ti_le(ra["goc_mo_phong"])}
    if tester is not None:
        ra["tong_hop"]["tester"] = tong_hop_chuoi(tester)
        ra["goc_tester"] = C.so_chuoi(goc, tester)
        ra["mo_phong_tester"] = C.so_chuoi(mo_phong, tester)
        ti["goc_tester"], ti["mo_phong_tester"] = _ti_le(ra["goc_tester"]), _ti_le(ra["mo_phong_tester"])
    ra["ti_le_khop"] = ti
    ra["chan_doan"] = chan_doan(ti, nguong)
    return ra


def _ti_le(so: dict) -> float | None:
    m = max(so["n_goc"], so["n_lai"])
    return (so["khop"] / m) if m else None


def chan_doan(ti: dict, nguong: float = 0.99) -> str:
    gm, gt, mt = ti.get("goc_mo_phong"), ti.get("goc_tester"), ti.get("mo_phong_tester")
    ok = lambda x: x is not None and x >= nguong                  # noqa: E731
    if gm is None:
        return "CHUA_DO_DUOC: khong co chuoi nao de so"
    if "goc_tester" not in ti:
        return ("EA dung lai + luat tick trong mo phong tai tao %.1f%% chuoi cua bot goc; CHUA co tester de biet luat do co dung la luat cua MT5 hay khong" % (100 * gm)
                if ok(gm) else "mo phong chi tai tao %.1f%% chuoi cua bot goc (< %.0f%%): luat tick hoac EA dung lai con sai (xem chi_tiet)" % (100 * gm, 100 * nguong))
    if ok(gm) and ok(gt) and ok(mt):
        return "CA BA KHOP: EA dung lai ra y het bot goc tren MT5, va mo phong tai tao dung MT5 - luat tick trong mo phong la luat cua tester"
    if ok(gt) and not ok(mt):
        return ("tester ra y het bot goc (EA dung lai DUNG) nhung MO PHONG lech tester: luat tick / khop lenh cua mo phong chua dung luat MT5 (%.1f%% khop voi tester)" % (100 * (mt or 0)))
    if ok(gm) and not ok(gt):
        return ("mo phong tai tao bot goc nhung TESTER (cung EA) thi khong: tester dang chay khac may chay bot goc (Model / du lieu / thoi gian) hoac mo phong khop nhu "
                "nhau o day nhung khac tester o cho chua nhin thay - doi Model roi chay lai")
    if ok(mt) and not ok(gt):
        return "mo phong va tester giong nhau nhung deu lech bot goc: EA dung lai CHUA dung co che bot goc (xem chi_tiet), hoac tester chay bot goc voi Model khac"
    return "ca ba deu lech nhau: kiem du lieu / lech gio / cua so truoc (do_lech_gio), roi moi den luat"


# ==================================================================================================================== 5. TU KIEM (gia tong hop co dap an)
def _vao_ngau_nhien(bars: pd.DataFrame, seed: int, moi_bao_nhieu_nen: int = 120) -> list[int]:
    rng = np.random.default_rng(seed + 1000)
    n = max(len(bars) // moi_bao_nhieu_nen, 1)
    i = np.sort(rng.choice(len(bars) - 1, size=n, replace=False))
    return [int(x) for x in bars.index.values.astype("datetime64[s]").astype(np.int64)[i]]


CHUOI_MOI_NGAY_GIAO_DICH = 1.38      # do tu 2.246 chuoi that cua CCBSN tren ~1.629 ngay giao dich (kp + xn): doi 'so chuoi can' ra 'bao nhieu ngay M1'


def tu_kiem(luat_that=("theo_nen", "nguoc_nen", "thap_truoc", "cao_truoc"), ngay: float = 120, seed: int = 1, quet: bool = True, ra=print) -> dict:
    """Thu DUNG CU tren gia tong hop co DAP AN: voi moi `luat_that` chay EA dung lai tren duong tick cua luat do (SL chi doi len) de co 'deal goc gia', roi hoi
    `kiem_luat_tick` (+ `quet_mo_phong`) co chon dung khong. `dat` = o MOI luat that: luat that hop le 100% su kien, lenh dau khop open + spread, va (neu quet)
    EA chay lai tren dung luat do + SL doi len ra DUNG moi chuoi. `ro` = them: luat that duoc xep nhat va hon han moi luat con lai (p <= P_RO) - phu thuoc SO CHUOI.
    `do_phan_giai.so_chuoi_can` = so chuoi can de cap luat KHO nhat tach duoc voi p <= P_RO (tinh tu ti le su kien phan biet do duoc), doi ra so ngay M1 that."""
    bars = gia_tong_hop(ngay, seed)
    exe = bien_dich(_vao_ngau_nhien(bars, seed))
    kq = dict(dat=True, ro=True, ngay=ngay, seed=seed, n_nen=int(len(bars)), ca={})
    ev_cap: dict[str, float] = {}
    for lt in luat_that:
        ch, _ = chay_mo_phong(exe, bars, lt, 1)
        ch = ch[ch["ly_do"].isin(["sl", "tp"])].reset_index(drop=True)
        k = kiem_luat_tick(ch, bars)
        ti = k["luat"][lt]["ti_le"]
        c = dict(n_chuoi=int(len(ch)), su_kien=k["su_kien"], tot_nhat=k["tot_nhat"], ket_luan=k["ket_luan"], ti_le_luat_that=ti, vao_sai=k["vao"]["sai"],
                 so_voi={r: dict(tot_hon=v["tot_hon"], kem_hon=v["kem_hon"], p=v["p"]) for r, v in k["so_voi"].items()})
        dat = ti == 1.0 and k["vao"]["sai"] == 0
        c["ro"] = bool(k["tot_nhat"] == lt and k["ket_luan"] == "RO")
        if quet:
            q = quet_mo_phong(ch, bars, luat=LUAT, ratchet=(1, 0))
            o_that = next((b for b in q["bang"] if b["luat"] == lt and b["ratchet"] == 1), None)
            hang = [(b["luat"], b["ratchet"]) for b in q["bang"] if q["bang"] and b["khop"] == q["bang"][0]["khop"]]
            c["quet"] = dict(n_goc=q["n_goc"], khop_o_luat_that=o_that["khop"] if o_that else None, dong_hang=hang, phan_biet=len(hang) == 1)
            dat = bool(dat and o_that and o_that["khop"] == o_that["chung"] == o_that["n_goc"] == o_that["n_lai"] == q["n_goc"])
        c["dat"] = bool(dat)
        kq["dat"], kq["ro"] = kq["dat"] and c["dat"], kq["ro"] and c["ro"]
        kq["ca"][lt] = c
        for rv, v in k["so_voi"].items():
            cap = " > ".join(sorted((lt, rv)))
            ev = v["tot_hon"] / max(len(ch), 1)
            ev_cap[cap] = min(ev_cap.get(cap, ev), ev)
        ra("[tu kiem] luat that %-10s: %3d chuoi; chon %-10s (%s) hop le %.2f%%%s; %s" % (
            lt, c["n_chuoi"], k["tot_nhat"], k["ket_luan"], 100 * (ti or 0), (", quet khop %s/%s" % (c["quet"]["khop_o_luat_that"], c["quet"]["n_goc"])) if quet else "",
            "DAT" if c["dat"] else "KHONG DAT"))
    if ev_cap:
        cap, ev = min(ev_cap.items(), key=lambda x: x[1])
        so_can = int(math.ceil(math.log2(1.0 / P_RO) / ev)) if ev > 0 else None
        kq["do_phan_giai"] = dict(cap_kho_nhat=cap, su_kien_moi_chuoi=round(ev, 3), so_chuoi_can=so_can,
                                  ngay_giao_dich_can=int(math.ceil(so_can / CHUOI_MOI_NGAY_GIAO_DICH)) if so_can else None)
        ra("[tu kiem] do phan giai: cap kho nhat %s co %.3f su kien phan biet / chuoi -> %s" % (
            cap, ev, ("can ~%d chuoi (~%d ngay giao dich M1 that) de p <= %.0e" % (so_can, kq["do_phan_giai"]["ngay_giao_dich_can"], P_RO)) if so_can
            else "CHUA phan biet duoc cap nay tren gia tong hop nay (tang --ngay)"))
    return kq


# ==================================================================================================================== 6. VAO / RA TEP (bang chuoi)
_COT_CSV = ["id", "mo", "dong", "n", "lot", "gia_vao", "gia_tb", "gia_thap", "gia_ra", "ly_do", "loi", "lot_cac_lenh", "gia_cac_lenh", "gio_cac_lenh"]
_DANG_GIO = "%Y-%m-%d %H:%M:%S"


def chuoi_ra_csv(c: pd.DataFrame) -> str:
    """Bang chuoi -> CSV van ban (cot danh sach noi bang ';'). Dang cua file gui tu may nha ve; `chuoi_tu_csv` doc nguoc LAI Y NGUYEN."""
    d = pd.DataFrame(columns=_COT_CSV) if c is None or not len(c) else c[_COT_CSV].copy()
    if len(d):
        d["mo"] = pd.to_datetime(d["mo"]).dt.strftime(_DANG_GIO)
        d["dong"] = pd.to_datetime(d["dong"]).dt.strftime(_DANG_GIO)          # NaT -> NaN -> o trong
        d["lot_cac_lenh"] = d["lot_cac_lenh"].map(lambda x: ";".join(repr(float(v)) for v in x))
        d["gia_cac_lenh"] = d["gia_cac_lenh"].map(lambda x: ";".join(repr(float(v)) for v in x))
        d["gio_cac_lenh"] = d["gio_cac_lenh"].map(lambda x: ";".join(pd.Timestamp(v).strftime(_DANG_GIO) for v in x))
    return d.to_csv(index=False, float_format="%.10g", lineterminator="\n")


def chuoi_tu_csv(van_ban: str) -> pd.DataFrame:
    """Nguoc lai `chuoi_ra_csv`. Thieu cot -> ValueError."""
    import io
    d = pd.read_csv(io.StringIO(van_ban), keep_default_na=True, dtype={"ly_do": str})
    thieu = [c for c in _COT_CSV if c not in d.columns]
    if thieu:
        raise ValueError("bang chuoi thieu cot %s" % thieu)
    if not len(d):
        return pd.DataFrame(columns=C.COT_CHUOI)
    d["mo"], d["dong"] = pd.to_datetime(d["mo"]), pd.to_datetime(d["dong"])
    for c in ("lot_cac_lenh", "gia_cac_lenh"):
        d[c] = d[c].map(lambda s: [float(x) for x in str(s).split(";")])
    d["gio_cac_lenh"] = d["gio_cac_lenh"].map(lambda s: [pd.Timestamp(x) for x in str(s).split(";")])
    d["n"] = d["n"].astype(int)
    return d[C.COT_CHUOI].reset_index(drop=True)


def _gz_co_dinh(van_ban: str) -> bytes:
    """gzip CO DINH (khong ten goc, khong mtime): cung noi dung ra cung byte, chay lai khong them ban sao vao lich su git."""
    import gzip
    import io
    bo = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=bo, compresslevel=9, mtime=0) as gz:
        gz.write(van_ban.encode("utf-8"))
    return bo.getvalue()


def ghi_chuoi_gz(c: pd.DataFrame, duong: Path) -> int:
    """Ghi bang chuoi thanh .csv.gz co dinh; tra so byte. Ghi qua .tam roi doi ten (`du_lieu_gia/**/*.tam` nam trong .gitignore)."""
    import os
    duong = Path(duong)
    duong.parent.mkdir(parents=True, exist_ok=True)
    gz = _gz_co_dinh(chuoi_ra_csv(c))
    tam = duong.with_name(duong.name + ".tam")
    try:
        tam.write_bytes(gz)
        os.replace(tam, duong)
    finally:
        if tam.exists():
            tam.unlink()
    return len(gz)


def doc_chuoi_gz(duong: Path) -> pd.DataFrame:
    import gzip
    with gzip.open(duong, "rb") as fh:
        return chuoi_tu_csv(fh.read().decode("utf-8"))


def thu_muc_tester(thu_muc=None) -> Path:
    """Noi bang chuoi cua tester nam (cung cho voi file gia de bo chay day len git): `<hop thu>/du_lieu_gia/so_ea_voi_tester`."""
    return (Path(thu_muc) if thu_muc else XG.thu_muc_mac_dinh()) / THU_MUC_RA


def ten_tep_tester(tu: str, den: str, model: int, ratchet: int = 1) -> str:
    return "tester_m%d_r%d_%s_%s.csv.gz" % (int(model), int(ratchet), str(tu).replace("-", "").replace(".", ""), str(den).replace("-", "").replace(".", ""))


# ==================================================================================================================== 7. NUA MAY NHA (CHI WINDOWS + MT5)
def _loi(ly: str, **kw) -> dict:
    return dict(trang_thai="CHUA_DO_DUOC", ly_do=ly, **kw)


def chay_tester(tu: str, den: str, model: int = 1, ma: str = "XAUUSD", ratchet: int = 1, von: int = 10000, han_giay: int | None = None,
                thu_muc=None, ghi: bool = True, goc_bao_cao=None) -> dict:
    """CHI may nha co MT5: chay EA dung lai tren MAY THU MT5 trong cua so [tu, den] voi `model` (0 = moi tick sinh tu M1; 1 = OHLC 1 phut - ung vien cua
    bot goc), gom deal thanh CHUOI roi so voi chuoi that cua bot goc trong cung cua so. Cua so PHAI nam trong doan kham_pha da dong bang (khong cham xac_nhan /
    niem_phong) va >= 14 ngay. Gio vao chuoi = gio lenh dau cua chuoi bot goc (phat lai), nen tester ra CUNG chuoi thi luat khop lenh cua tester = luat da dung
    de dung lai EA. Ghi: bang chuoi tester -> `<hop thu>/du_lieu_gia/so_ea_voi_tester/tester_m<model>_r<ratchet>_<tu>_<den>.csv.gz` (len git), tom tat ->
    `<goc_bao_cao hay lab>/reports/so_ea_voi_tester/<ten>.json`. Hong ha tang -> CHUA_DO_DUOC (khong bao gio AM). DAT = tester ra >= 99% chuoi giong bot goc (do duoc, khong phai
    'dat tieu chi lai'); AM = do duoc nhung lech."""
    from nhan import bao_cao_mt5 as BC
    from nhan import ea_tho as E
    from nhan import hieu_chuan_luoi as HC
    from nhan import lenh_tester as LT
    if model not in (0, 1):
        return _loi("model phai la 0 (moi tick sinh tu M1) hoac 1 (OHLC 1 phut); 4 (tick that) chi co tu 2024-02 -> ngoai doan kham_pha, nhan %r" % (model,))
    if ratchet not in (0, 1):
        return _loi("ratchet phai la 0 hoac 1, nhan %r" % (ratchet,))
    try:
        von = int(von)
    except (TypeError, ValueError):
        return _loi("von phai la so nguyen")
    if von < 1000:
        return _loi("von phai >= 1000 (lot 0,01 nhieu tang can du von de khong bi stop-out)")
    ma = str(ma).upper()
    cfg = E.cau_hinh()
    cfg2 = dict(cfg, model=int(model), von=von, tick_tu=None)
    if han_giay:
        cfg2["han_giay"] = int(han_giay)
    cs, ly = HC.chuan_cua_so(ma, "M15", tu, den, cfg2)                 # M15 = khoa doan dong bang cua cap nay; KHONG goi voi M1 (se dong bang khoa moi)
    if cs is None:
        return _loi(ly)
    goc = C.doc_hai_nguon()
    t0, t1 = pd.Timestamp(cs["tu"].replace(".", "-")), pd.Timestamp(cs["den"].replace(".", "-")) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    trong = goc[(pd.to_datetime(goc["mo"]) >= t0) & (pd.to_datetime(goc["mo"]) <= t1)]
    trong = trong[trong["ly_do"].isin(["sl", "tp"]) & ~pd.to_datetime(trong["dong"]).gt(t1)].reset_index(drop=True)
    if len(trong) < 5:
        return _loi("cua so %s .. %s chi co %d chuoi cua bot goc (< 5): chon cua so dai hon" % (cs["tu"], cs["den"], len(trong)))
    vao = C.thoi_diem_vao(trong)
    ts = {} if int(ratchet) == 1 else {"InpTrailRatchet": 0}
    with tempfile.TemporaryDirectory(prefix="ccbl_tester_") as d:
        mq5 = C.viet_ea(vao, Path(d) / "ea_CanCuBoLai.mq5")
        try:
            ea = E.doc_ea(str(mq5))
        except (KeyError, ValueError, OSError) as e:
            return _loi("khong doc duoc EA dung lai: %s" % str(e)[:200], ha_tang=True)
    lo = E.lap_lenh(ea, ma, "M1", "kham_pha", ts, None, cfg2, None, cua_so_tay=cs)
    if lo.get("trang_thai") != "SAN_SANG":
        return lo
    lenh = lo["lenh"]
    t_dau = time.time()
    r = (E.CHAY_TESTER or E._chay_that)(lenh, ea, cfg2)
    if not r.get("xong"):
        return _loi("tester khong ra ket qua: %s" % (r.get("loi") or "khong ro"), ha_tang=True)
    bc = BC.doc_bao_cao(r["bao_cao"], cfg2.get("nhan_them"))
    ly = HC._hong_ha_tang(bc, cs, r.get("log", ""))
    if ly:
        return _loi(ly, ha_tang=True)
    try:
        v = LT.vi_the_tu_tep(r["bao_cao"])
    except (ValueError, KeyError, OSError) as e:
        return _loi("bao cao khong co bang Deals doc duoc: %s" % str(e)[:160], ha_tang=True)
    tc = C.chuoi_tu_vi_the(v)
    g_t = C.so_chuoi(trong, tc)
    kq = dict(trang_thai="DAT" if (g_t["khop"] >= 0.99 * max(g_t["n_goc"], 1) and g_t["n_goc"] == g_t["n_lai"]) else "AM",
              ghi_chu="DAT o day = DO DUOC va tester ra >= 99% chuoi giong bot goc; AM = do duoc nhung lech (xem chi_tiet) - KHONG phai 'dat tieu chi lai'",
              ma=ma, cua_so=dict(tu=cs["tu"], den=cs["den"], ngay=cs["ngay"]), model=int(model), ratchet=int(ratchet), von=von, n_vao=len(vao),
              ea_sha=lenh["ea_sha"], bao_cao=dict(bars=bc.get("bars"), ticks=bc.get("ticks"), chat_luong_pct=bc.get("chat_luong_pct"), tu=bc.get("tu"), den=bc.get("den"),
                                                  lai_rong=bc.get("lai_rong"), so_lenh=bc.get("so_lenh")),
              goc_tester=g_t, tong_hop=dict(goc=tong_hop_chuoi(trong), tester=tong_hop_chuoi(tc)), giay=round(float(r.get("giay") or (time.time() - t_dau)), 1))
    if ghi:
        ten = ten_tep_tester(cs["tu"], cs["den"], model, ratchet)
        kq["tep_chuoi"] = dict(ten=ten, byte=ghi_chuoi_gz(tc, thu_muc_tester(thu_muc) / ten))
        kq["bao_cao_tom_tat"] = ghi_bao_cao(kq, ten.replace(".csv.gz", ""), goc_bao_cao)
    return kq


# ==================================================================================================================== 8. PHAN TICH TREN GIA THAT
def gon(x, toi_da_chuoi: int = 220, toi_da_ds: int = 4):
    """Cat gon de vua tep <= 38k ky tu: chuoi dai -> cat, danh sach dai -> vai phan tu dau (+ so con lai)."""
    if isinstance(x, dict):
        return {k: gon(v, toi_da_chuoi, toi_da_ds) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        ra = [gon(v, toi_da_chuoi, toi_da_ds) for v in x[:toi_da_ds]]
        return ra + (["... +%d" % (len(x) - toi_da_ds)] if len(x) > toi_da_ds else [])
    if isinstance(x, str):
        return x if len(x) <= toi_da_chuoi else x[:toi_da_chuoi] + "..."
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    return x


def ghi_bao_cao(ra: dict, ten: str, goc: Path | None = None) -> str | None:
    """Ghi `reports/so_ea_voi_tester/<ten>.json` (bo chay don chi mang ve tep van ban <= 40k ky tu). Qua lon -> cat gon hon. Tra duong tuong doi hoac None."""
    thu = (Path(goc) if goc else C.GOC) / "reports" / THU_MUC_RA
    thu.mkdir(parents=True, exist_ok=True)
    for toi_da in (6, 3, 1):
        vb = json.dumps(gon(ra, 220, toi_da), ensure_ascii=False, indent=1, default=str)
        if len(vb) <= TEP_TOI_DA:
            p = thu / ("%s.json" % ten)
            p.write_text(vb, encoding="utf-8")
            return "reports/%s/%s.json" % (THU_MUC_RA, ten)
    return None


def phan_tich(thu_muc=None, tu: str | None = None, den: str | None = None, ma: str = "XAUUSD", quet: bool = True, tester: str | None = None) -> dict:
    """PHAN TICH TREN GIA THAT (can nen M1 do may nha xuat): lech gio -> luat tick tung su kien -> quet mo phong -> (neu co) so ba chieu voi tester.
    `tester` = ten tep trong `<thu_muc>/so_ea_voi_tester/` (None = khong; chi TEN tep, khong duong dan). Khong co nen M1 -> CHUA_DO_DUOC (cho may nha)."""
    if tester and Path(str(tester)).name != str(tester):
        return _loi("tester phai la TEN tep trong du_lieu_gia/%s (khong kem duong dan), nhan %r" % (THU_MUC_RA, str(tester)[:80]))
    try:
        bars = doc_gia(ma, tu, den, thu_muc)
    except FileNotFoundError as e:
        return _loi("chua co nen M1 %s (cho may nha: `b xuat-gia %s M1 --tu .. --den ..`): %s" % (ma, ma, str(e)[:120]), cho_may_nha=True)
    except ValueError as e:
        return _loi("nen M1 hong: %s" % str(e)[:200], ha_tang=True)
    goc = C.doc_hai_nguon()
    trong = _chuoi_trong_gia(goc, bars)
    kq = dict(trang_thai="CHUA_DO_DUOC", ma=ma, nen_m1=dict(n=int(len(bars)), tu=str(bars.index[0]), den=str(bars.index[-1])), n_chuoi_goc_trong_gia=int(len(trong)))
    if not len(trong):
        kq["ly_do"] = "khong chuoi nao cua bot goc nam trong khoang nen M1 %s .. %s" % (bars.index[0], bars.index[-1])
        return kq
    lg = do_lech_gio(trong, bars)
    kq["lech_gio"] = lg
    if lg["tot_nhat"] not in (None, 0) and (lg["ti_le"] or 0) >= 0.5:
        bars = bars.copy()
        bars.index = bars.index + pd.Timedelta(hours=int(lg["tot_nhat"]))
        kq["ghi_chu_gio"] = "nen M1 lech %+d gio so voi deal: da dich nen %+d gio truoc khi kiem" % (lg["tot_nhat"], lg["tot_nhat"])
    kq["luat_tick"] = kiem_luat_tick(goc, bars)
    if quet:
        try:
            kq["mo_phong"] = quet_mo_phong(goc, bars)
        except RuntimeError as e:
            kq["mo_phong"] = dict(loi=str(e)[:300])
    if tester:
        p = thu_muc_tester(thu_muc) / tester
        if not p.exists():
            kq["tester"] = dict(ly_do="chua co %s (cho may nha chay `so_ea_voi_tester che_do=tester`)" % p.name)
        else:
            tc = doc_chuoi_gz(p)
            mp = kq.get("mo_phong", {}).get("tot_nhat")
            kq["tester"] = dict(tep=p.name, n_chuoi=int(len(tc)))
            sub = trong[trong["ly_do"].isin(["sl", "tp"])]
            kq["tester"]["goc_tester"] = C.so_chuoi(sub, tc)
            if mp and quet:
                exe = bien_dich(C.thoi_diem_vao(sub))
                lai, _ = chay_mo_phong(exe, bars, mp["luat"], mp["ratchet"])
                lai = lai[[C._giay(pd.Timestamp(t).floor("min")) in _khoa_phut(sub) for t in lai["mo"]]] if len(lai) else lai
                kq["tester"]["ba_chieu"] = so_ba_chieu(sub, lai, tc)
    kq["trang_thai"] = "DAT"
    kq["ghi_chu"] = "DAT o day = DO DUOC (khong phai dat tieu chi lai): xem luat_tick.ket_luan, mo_phong.tot_nhat, tester.ba_chieu.chan_doan"
    return kq


def loi_thuong(kq: dict) -> list[str]:
    """Ket qua `phan_tich` -> vai dong LOI THUONG cho chu du an (khong thuat ngu): da biet gi, chua biet gi."""
    if kq.get("trang_thai") != "DAT":
        return ["Chua do duoc: %s" % kq.get("ly_do", "khong ro")]
    ra = []
    nm = kq["nen_m1"]
    ra.append("Da doi chieu %d chuoi lenh that cua con bot voi %d cay nen 1 phut that (%s .. %s)." % (
        kq["n_chuoi_goc_trong_gia"], nm["n"], nm["tu"][:10], nm["den"][:10]))
    lt = kq["luat_tick"]
    if lt.get("tot_nhat"):
        ra.append("Cach may thu MT5 'di' qua mot cay nen: %s (%s) - %s" % (
            lt["tot_nhat"], lt["ket_luan"], lt["ly_do"]))
    mp = kq.get("mo_phong", {}).get("tot_nhat")
    if mp:
        ra.append("Con bot dung lai chay tren gia that: khop %d/%d chuoi o cach '%s'%s." % (
            mp["khop"], mp["chung"], mp["luat"], ", SL chi doi len" if mp["ratchet"] else ", SL bam theo"))
    bc = kq.get("tester", {}).get("ba_chieu")
    if bc:
        ra.append("Ba ben (bot goc / may gia lap / MT5 that): %s" % bc["chan_doan"])
    return ra


# ==================================================================================================================== 9. CONG CU NGHIEN CUU
LOAI_SO_TAY = "so_ea_voi_tester"
DOAN_SO_TAY = "hieu_chuan"            # cung doan voi hieu_chuan_luoi: dem_phep_thu / thi_nghiem_tot_nhat khong bao gio thay no (do dac, khong phai phep thu y tuong)
PHIEN_BAN = "1"                       # doi khi doi CACH TINH -> khong dung nham dong so tay cu


def _tom_tat(che_do: str, kq: dict) -> str:
    """Mot dong ASCII cho so tay."""
    if che_do == "tu_kiem":
        dp = kq.get("do_phan_giai") or {}
        return "tu kiem %s: %d/%d luat that duoc chon dung%s" % (
            "DAT" if kq.get("dat") else "KHONG DAT", sum(1 for c in kq.get("ca", {}).values() if c.get("dat")), len(kq.get("ca", {})),
            ", can ~%s chuoi de phan biet" % dp["so_chuoi_can"] if dp.get("so_chuoi_can") else "")
    if che_do == "tester":
        g = kq.get("goc_tester") or {}
        return "tester Model %s ratchet %s %s..%s: %s, khop %s/%s chuoi" % (
            kq.get("model"), kq.get("ratchet"), (kq.get("cua_so") or {}).get("tu"), (kq.get("cua_so") or {}).get("den"), kq.get("trang_thai"),
            g.get("khop"), g.get("n_goc"))
    return " | ".join(loi_thuong(kq))


def cong_cu(che_do: str = "tu_kiem", vong_id: int | None = None, tu: str | None = None, den: str | None = None, model: int = 1, ratchet: int = 1,
            ngay: float = 120, seed: int = 1, ma: str = "XAUUSD", tester: str | None = None, von: int = 10000, han_giay: int | None = None,
            quet: bool | None = None, **_) -> dict:
    """Cong cu `nc cc so_ea_voi_tester`: bon che do. `tu_kiem` (gia tong hop co dap an), `luat` (luat tick tung su kien tren nen M1 that), `so` (them quet
    mo phong va, neu co `tester`, so ba chieu), `tester` (CHI may nha co MT5). Ket qua DO DUOC (DAT / AM) duoc ghi so tay (doan `hieu_chuan`, 0 phep thu,
    khong an FDR); CHUA_DO_DUOC khong ghi gi; cung dau vao + cung du lieu = khong ghi trung."""
    from nhan import nc_so_tay as ST
    if che_do not in ("tu_kiem", "luat", "so", "tester"):
        raise ValueError("che_do phai la tu_kiem | luat | so | tester, nhan %r" % (che_do,))
    t0 = time.time()
    if che_do == "tu_kiem":
        kq = tu_kiem(ngay=float(ngay), seed=int(seed), quet=True if quet is None else bool(quet), ra=lambda *_a: None)
        tt = "DAT" if kq.get("dat") else "AM"
        dau_vao = dict(che_do=che_do, ngay=float(ngay), seed=int(seed), quet=True if quet is None else bool(quet))
        du_lieu = None
    elif che_do in ("luat", "so"):
        kq = phan_tich(None, tu, den, ma, quet=(che_do == "so") if quet is None else bool(quet), tester=tester)
        tt = "DAT" if kq.get("trang_thai") == "DAT" else "CHUA_DO_DUOC"
        kq["loi_thuong"] = loi_thuong(kq)
        dau_vao = dict(che_do=che_do, tu=tu, den=den, ma=ma, quet=(che_do == "so") if quet is None else bool(quet), tester=tester)
        du_lieu = [kq.get("nen_m1"), kq.get("n_chuoi_goc_trong_gia"), (kq.get("tester") or {}).get("n_chuoi")]
    else:
        kq = chay_tester(tu, den, int(model), ma, int(ratchet), von, han_giay)
        tt = kq.get("trang_thai") if kq.get("trang_thai") in ("DAT", "AM") else "CHUA_DO_DUOC"
        dau_vao = dict(che_do=che_do, tu=tu, den=den, model=int(model), ratchet=int(ratchet), ma=ma, von=von)
        du_lieu = [kq.get("ea_sha"), kq.get("cua_so"), (kq.get("goc_tester") or {}).get("n_lai")]
    if tt != "CHUA_DO_DUOC":
        vt = ST.van_tay(LOAI_SO_TAY, PHIEN_BAN, dau_vao, du_lieu)
        cu = ST.da_thu(vt)
        if cu:
            kq["tn_id"], kq["tu_so_tay"] = cu["id"], "da ghi dong so tay %s (cung dau vao + cung du lieu)" % cu["id"]
        else:
            kq["tn_id"] = ST.ghi_thi_nghiem(LOAI_SO_TAY, dau_vao, gon(kq), tt, vt, str(ma).upper(), "M1", DOAN_SO_TAY, gt_id=None, so_phep_thu=0,
                                            giay=time.time() - t0, vong_id=vong_id, tom_tat=_tom_tat(che_do, kq))
    return gon(kq)


# ==================================================================================================================== 10. DONG LENH
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="so_ea_voi_tester", description=__doc__.split("\n")[0])
    sp = ap.add_subparsers(dest="lenh", required=True)
    a = sp.add_parser("tu-kiem", help="thu dung cu tren gia tong hop co dap an (khong can du lieu ngoai)")
    a.add_argument("--ngay", type=float, default=120)
    a.add_argument("--seed", type=int, default=1)
    a.add_argument("--khong-quet", action="store_true")
    for ten in ("luat", "so"):
        b = sp.add_parser(ten, help="phan tich tren nen M1 that do may nha xuat")
        b.add_argument("--thu-muc")
        b.add_argument("--tu")
        b.add_argument("--den")
        b.add_argument("--ma", default="XAUUSD")
        b.add_argument("--tester", help="ten tep bang chuoi tester trong du_lieu_gia/so_ea_voi_tester (chi cho `so`)")
        b.add_argument("--ghi", action="store_true", help="ghi reports/so_ea_voi_tester/phan_tich.json")
    t = sp.add_parser("tester", help="CHI may nha co MT5: chay EA dung lai tren may thu")
    t.add_argument("--tu", required=True)
    t.add_argument("--den", required=True)
    t.add_argument("--model", type=int, default=1)
    t.add_argument("--ratchet", type=int, default=1)
    t.add_argument("--ma", default="XAUUSD")
    t.add_argument("--von", type=int, default=10000)
    a_ = ap.parse_args(argv)
    if a_.lenh == "tu-kiem":
        kq = tu_kiem(ngay=a_.ngay, seed=a_.seed, quet=not a_.khong_quet)
        print("TU KIEM: %s%s" % ("DAT" if kq["dat"] else "KHONG DAT", " (va RO)" if kq["ro"] else " (chua RO: can nhieu chuoi hon)"))
        return 0 if kq["dat"] else 1
    if a_.lenh in ("luat", "so"):
        kq = phan_tich(a_.thu_muc, a_.tu, a_.den, a_.ma, quet=a_.lenh == "so", tester=getattr(a_, "tester", None))
        for d in loi_thuong(kq):
            print(d)
        if a_.ghi:
            print("ghi:", ghi_bao_cao(kq, "phan_tich"))
        return 0 if kq.get("trang_thai") == "DAT" else 2
    kq = chay_tester(a_.tu, a_.den, a_.model, a_.ma, a_.ratchet, a_.von)
    print(json.dumps(gon(kq), ensure_ascii=False, indent=1, default=str))
    return 0 if kq.get("trang_thai") in ("DAT", "AM") else 2


if __name__ == "__main__":
    sys.exit(main())
