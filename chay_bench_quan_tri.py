# -*- coding: utf-8 -*-
"""chay_bench_quan_tri.py - DUA 11 HO QUAN TRI VI THE RA MT5 TESTER.

## VI SAO FILE NAY TON TAI

Chu du an, `SO_DO_HE_THONG.txt`: *"tet thu tung phuong phap quan li lenh khac
nhau de xem hieu qua cung nhu ket qua thay doi ra sao"*. Va 13/09/2026: *"Cac
module quan li lenh bang trailing, hedge, tia lenh, lenh limit stop... can phai
hoan thanh ki"*.

Duong cu (`de_quan_tri.py`) chen khoi quan tri vao EA NGOAI. Ket qua 12/09 ghi
trong `reports/DE_QT_EA_NGOAI.json`: **14/15 luat cho so lieu GIONG HET NHAU**
(1759 lenh, lai -108,76, sut giam 1,3121), va file tu ket luan `"AM"`.

Do khong phai `AM`, do la `CHUA_DO_DUOC`, vi hai le do duoc:

  1. Bang tham so sinh ra TOAN SO 0 (`dich_mq5_qtvt._atr0` chi nhan
     `{"atr": x}` con 141/146 gia tri trong kho la `{"pip": x}`).
  2. Ke ca bang dung, EA ngoai tu dat TP/SL va tu thoat theo tin hieu cua no,
     nen quan tri khong con CHO de hanh dong.

File nay chua duong thu hai: mot EA rieng (`ea_QuanTriBench.mq5`) co ENGINE VAO
CO DINH, khong TP, khong thoat theo tin hieu - chi mot luoi an toan. Tat ca
chenh lech doc duoc chi con mot nguyen nhan la HO QUAN TRI.

## BA CONG PHAI QUA TRUOC KHI TIN MOT CON SO

    so_ho_khac_moc == 0     -> CHUA_DO_DUOC (quan tri im lang, lai loi 12/09)
    so_lenh == 0            -> CHUA_DO_DUOC (tester khong chay duoc)
    moc khong co mat        -> CHUA_DO_DUOC (khong co gi de so)

Ba cai nay la CONG chu khong phai ghi chu, vi ky luat con nguoi da hong ba lan
o dung cho nay.

Chay:
    python chay_bench_quan_tri.py --ma US500Cash --khung H1
    python chay_bench_quan_tri.py --ma EURUSD --khung H1 --vao 2 --nhanh
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chay_tester_kho import (bien_dich, doc_xml, _so)          # noqa: E402
from chay_tester_z5 import XM_DATA, XM_EXE, dong_terminal, kiem_log_agent  # noqa: E402

LAB = Path(__file__).resolve().parent
TEN_EA = "QuanTriBench"

#: Ten ho, khop voi `#define QT_*` trong ea_QuanTriBench.mq5.
HO = ["moc", "tp_co_dinh", "trailing", "dat_hue", "hue_trailing", "tia",
      "hedge", "stop_2_dau", "tt_stop_doi", "luoi_dca", "thoi_gian"]

#: Y NGHIA THAM SO tung ho - phai in ra cung bang ket qua, neu khong thi
#: "P1=1,5" la mot con so khong doc duoc.
Y_NGHIA = {
    "moc": "(khong dung tham so)",
    "tp_co_dinh": "P1 = TP boi ATR",
    "trailing": "P1 = khoang trail boi ATR | P2 = lai bat dau trail",
    "dat_hue": "P2 = lai de keo SL ve hoa von",
    "hue_trailing": "P1 = khoang trail | P2 = lai kich hoat",
    "tia": "P1 = ty le dong (0..0,9) | P2 = lai de tia",
    "hedge": "P1 = lot khoa x lot goc | P2 = lo de khoa, boi ATR",
    "stop_2_dau": "P1 = khoang dat stop boi ATR | P2 = SL boi ATR",
    "tt_stop_doi": "P1 = khoang stop doi dien | P2 = lot stop x lot goc",
    "luoi_dca": "P1 = buoc nhoi boi ATR | P2 = TP chung boi ATR",
    "thoi_gian": "P1 = so nen thi dong",
}


def viet_ini(ten: str, symbol: str, khung: str, ho_tu: int, ho_den: int,
             p1: tuple, p2: tuple, vao_kieu: int, vao_n: int,
             tu: str, den: str, lot: float = 1.0,
             deposit: int = 10000) -> Path:
    """`Optimization=1` = QUET DAY DU.

    KHONG dung `2` (thuat di truyen): voi mot tham so la "ma ho", lay mau mot
    phan khong gian nghia la BO SOT CA MOT HO chu khong phai bo sot mot cau
    hinh - va bang ket qua thieu mot dong doc y het "ho do khong vao lenh".
    """
    p = XM_DATA / f"{ten}.ini"
    # TU DANG NHAP trong chinh `.ini` - xem `bi_mat.khoi_common_ini`.
    # Khong co khoi nay thi tester chet voi "tester not started because the
    # account is not specified", va thong bao do KHONG noi gi ve dang nhap.
    from nhan import bi_mat as _BM
    _chung = _BM.khoi_common_ini("XM")
    p.write_text(_chung + f"""[Tester]
Expert={TEN_EA}.ex5
Symbol={symbol}
Period={khung}
Model=2
ExecutionMode=0
Optimization=1
OptimizationCriterion=0
FromDate={tu}
ToDate={den}
ForwardMode=0
Deposit={deposit}
Currency=USD
Leverage=1:500
ProfitInPips=0
Report={ten}
ReplaceReport=1
ShutdownTerminal=1

[TesterInputs]
InpHoQT={ho_tu}||{ho_tu}||1||{ho_den}||Y
InpP1={p1[0]}||{p1[0]}||{p1[2]}||{p1[1]}||Y
InpP2={p2[0]}||{p2[0]}||{p2[2]}||{p2[1]}||Y
InpVaoKieu={vao_kieu}||{vao_kieu}||0||0||N
InpVaoN={vao_n}||{vao_n}||0||0||N
InpLot={lot}||{lot}||0||0||N
InpMagic=26091301||26091301||0||0||N
InpATRKy=14||14||0||0||N
InpSLCung=3.0||3.0||0||0||N
InpGiuToiDa=120||120||0||0||N
InpNhoiMax=5||5||0||0||N
InpLoRongPct=25.0||25.0||0||0||N
""", encoding="utf-16")
    return p


def chay(symbol: str = "US500Cash", khung: str = "H1", vao_kieu: int = 0,
         vao_n: int = 20, nhanh: bool = False,
         tu: str = "2016.01.01", den: str = "2026.07.29",
         lot: float = 1.0) -> dict:
    from nhan import khoa_tester as KT
    from nhan import ngan_sach as NS
    # MT5 KHONG ket noi duoc toi may chu giao dich qua Cloudflare WARP. Giu
    # WARP TAT suot luot chay, va cam bo cao mql5 lat no giua chung.
    with NS.giu_warp(False, "MT5 tester"), KT.giu(f"bench_quan_tri {symbol} {khung}"):
        return _trong_khoa(symbol, khung, vao_kieu, vao_n, nhanh, tu, den, lot)


def co_lich_su(symbol: str) -> bool:
    """Symbol co lich su trong kho cua tester khong.

    Do 13/09/2026: chay `XAUUSD` het 2 x 90 giay roi tra ve 0 lenh tren MOI
    pass. Tai khoan XM nay **khong co ma XAUUSD** - vang o day ten la `GOLD`
    (va `GOLDmicro`). Cong `so_lenh == 0` bat duoc, nhung no bat SAU khi da
    chay xong; va mot bang "0 lenh" nam canh cac bang that thi rat de bi doc
    thanh "quan tri khong an tren vang".

    Kiem TRUOC thi mat 1 mili giay va bao duoc dung ten ma.
    """
    goc = XM_DATA / "bases"
    if not goc.exists():
        return True          # khong kiem duoc thi cho chay, dung chan mu
    co = {p.name for p in goc.glob("*/history/*") if p.is_dir()}
    if symbol in co:
        return True
    # CHUA CO LICH SU KHAC VOI KHONG CO MA.
    #
    # Do 13/09/2026, ngay sau khi dang nhap lai XM: `bases/XM.COM-MT5/history`
    # RONG, vi MT5 chi tai lich su khi co ai do YEU CAU mot ma - va nguoi yeu
    # cau dau tien chinh la luot tester nay. Cong cu nay khi do chan dung cai
    # luot se tao ra thu no doi hoi: mot vong quan quanh.
    #
    # Nen khi kho lich su con RONG (moi dang nhap), cho chay - cong `so_lenh
    # == 0` phia sau van bat duoc that bai that. Chi chan khi kho DA co ma
    # khac ma khong co ma nay: luc do "khong co ma" moi la ket luan dung.
    if not co:
        return True
    return False


#: Ten khac nhau cho cung mot tai san giua cac san. Khong doan duoc bang chuoi:
#: `XAUUSD` va `GOLD` khong chung mot ky tu nao.
BI_DANH = {"XAUUSD": ["GOLD", "GOLDmicro"], "XAGUSD": ["SILVER", "SILVERmicro"],
           "SPX500": ["US500Cash"], "NAS100": ["US100Cash"],
           "DE40": ["GER40Cash"], "DAX": ["GER40Cash"]}


def goi_y_ma(symbol: str, n: int = 6) -> list:
    """Ten ma gan dung. Thu BI DANH truoc, roi chuoi con, roi do giong nhau."""
    import difflib
    goc = XM_DATA / "bases"
    co = sorted({p.name for p in goc.glob("*/history/*") if p.is_dir()})
    ra = [x for x in BI_DANH.get(symbol.upper(), []) if x in co]
    kh = symbol.upper().replace("CASH", "").replace("MICRO", "")
    for cat in (kh, kh[:4], kh[:3]):
        if len(ra) >= n or len(cat) < 3:
            break
        ra += [x for x in co if cat in x.upper() and x not in ra]
    ra += [x for x in difflib.get_close_matches(symbol, co, n=n, cutoff=0.5)
           if x not in ra]
    return ra[:n]


def _trong_khoa(symbol, khung, vao_kieu, vao_n, nhanh, tu, den, lot=1.0) -> dict:
    if not co_lich_su(symbol):
        return {"trang_thai": "CHUA_DO_DUOC", "symbol": symbol, "khung": khung,
                "loi": "khong co ma `%s` trong kho lich su cua tester" % symbol,
                "ly_do": "ten ma sai hoac chua tai lich su",
                "goi_y": goi_y_ma(symbol)}
    nguon = LAB / "ea_QuanTriBench.mq5"
    src = XM_DATA / "MQL5" / "Experts" / f"{TEN_EA}.mq5"
    src.write_text(nguon.read_text(encoding="utf-8"), encoding="utf-8")
    loi = bien_dich(src)
    if loi:
        return {"trang_thai": "CHUA_DO_DUOC", "loi": loi}
    print("  bien dich xong", flush=True)

    # Luoi tham so: thua thi tester ton cong, thieu thi mot ho bi ket luan am
    # chi vi khong ai thu dung buoc cua no. 5 x 5 = 25 to hop moi ho.
    p1 = (0.5, 2.5, 0.5) if not nhanh else (1.0, 2.0, 1.0)
    p2 = (0.5, 2.5, 0.5) if not nhanh else (1.0, 2.0, 1.0)

    ten = f"bench_qt_{symbol}_{khung}"
    # LOT PHAI LON HON LOT TOI THIEU NHIEU LAN, neu khong thi ho `tia` chet
    # lang le. Do 13/09 o luot chay dau voi lot 0,10 (= dung lot toi thieu cua
    # US500Cash): `PositionClosePartial` khong the dong mot phan nao, nen `tia`
    # ra ket qua Y HET `dat_hue` - 1.418 lenh / lai -190,79 ca hai.
    #
    # Day la cai bay da duoc canh bao san trong `quan_tri_dsl.py` ("dong_mot_phan
    # phai kiem lot toi thieu") nhung van sap, vi canh bao nam o mot file khac
    # voi cho dat lot.
    ini = viet_ini(ten, symbol, khung, 0, len(HO) - 1, p1, p2,
                   vao_kieu, vao_n, tu, den, lot=lot)
    for hs in (".xml", ".htm"):
        f = XM_DATA / (ten + hs)
        if f.exists():
            f.unlink()

    dong_terminal()
    n_pass = len(HO) * len(range(0, 5)) ** 2
    print(f"  chay optimization (~{n_pass} pass) ...", flush=True)
    t0 = time.time()
    subprocess.Popen([str(XM_EXE), "/config:%s" % ini])
    while time.time() - t0 < 5400:
        time.sleep(10)
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
                           capture_output=True, text=True)
        if "terminal64.exe" not in r.stdout:
            break
    else:
        dong_terminal()
        return {"trang_thai": "CHUA_DO_DUOC", "loi": "qua 5400s"}
    giay = round(time.time() - t0, 1)

    hong = kiem_log_agent()
    if hong.startswith("TESTER KHONG CHAY DUOC"):
        return {"trang_thai": "CHUA_DO_DUOC", "loi": hong, "giay": giay}

    f = next((XM_DATA / (ten + h) for h in (".xml", ".htm")
              if (XM_DATA / (ten + h)).exists()), None)
    if f is None:
        return {"trang_thai": "CHUA_DO_DUOC", "loi": "khong thay bang ket qua",
                "giay": giay}

    ket = []
    for d in doc_xml(f):
        i = int(_so(d.get("InpHoQT", -1), -1))
        if not (0 <= i < len(HO)):
            continue
        ket.append({
            "ho": HO[i], "ma_ho": i,
            "p1": _so(d.get("InpP1")), "p2": _so(d.get("InpP2")),
            "lenh": int(_so(d.get("Trades"))),
            "lai": _so(d.get("Profit")),
            "pf": _so(d.get("Profit Factor")),
            "sharpe": _so(d.get("Sharpe Ratio")),
            "dd_pct": _so(d.get("Equity DD %")),
            "ky_vong": _so(d.get("Expected Payoff"))})

    return _cham(ket, symbol, khung, vao_kieu, vao_n, giay, hong, tu, den)


def _cao_nguyen(cac_o: list, moc: dict) -> dict:
    """CAO NGUYEN hay CAI GAI - do tren CA luoi tham so cua mot ho.

    Vi sao khong duoc bao moi con so tot nhat: mot ho co 25 o tham so, va "tot
    nhat trong 25" la mot CUC TRI cua 25 lan rut. Lab da mot lan thoi p sai 24
    lan vi dung so cuc dai so voi ban gia don le
    [[so-cuc-dai-phai-so-cung-co-mau]].

    Nen bang ket qua tra ve BA con so cho moi ho, va con so DE TIN la hai cai
    sau chu khong phai cai dau:

        tot_nhat    max cua luoi  - de nhin, de bi lua
        trung_vi    trung vi luoi - ho co on dinh khong
        ty_le_duong ty le o vuot moc - cao nguyen rong hay mot cai gai
    """
    if not cac_o:
        return {}
    sh = sorted(k["sharpe"] for k in cac_o)
    n = len(sh)
    tv = sh[n // 2] if n % 2 else (sh[n // 2 - 1] + sh[n // 2]) / 2
    hon = sum(1 for k in cac_o if k["sharpe"] > moc["sharpe"])
    return {"so_o": n, "sharpe_trung_vi": round(tv, 4),
            "sharpe_min": round(sh[0], 4), "sharpe_max": round(sh[-1], 4),
            "ty_le_o_hon_moc": round(hon / n, 3),
            "hinh_dang": ("cao_nguyen" if hon / n >= 0.6 else
                          "cai_gai" if hon / n <= 0.2 else "lo_cho")}


def _do_trung_nhau(theo_ho: dict) -> list:
    """Cap ho cho ket qua Y HET NHAU TREN CA LUOI - dau hieu mot ho khong chay.

    Do 13/09/2026 ngay o luot chay dau: `tia` va `dat_hue` cung ra 1.418 lenh /
    lai -190,79 den tung so le. Nguyen nhan: lot goc 0,10 bang dung lot toi
    thieu, nen `PositionClosePartial` khong the dong mot phan nao - ho `tia`
    chay y het ho `dat_hue`.

    Day KHONG phai mot ket qua ("tia khong co tac dung"), day la mot khau do
    hong. Phai bao ra, va phai bao TUNG CAP chu khong chi so voi moc - so voi
    moc thi ca hai deu "co doi", nen cai bay lot qua.
    """
    def _o(ds):
        return {(k["p1"], k["p2"]): (k["lenh"], round(k["lai"], 2)) for k in ds}

    ten = list(theo_ho)
    trung = []
    for i in range(len(ten)):
        for j in range(i + 1, len(ten)):
            a, b = _o(theo_ho[ten[i]]), _o(theo_ho[ten[j]])
            chung = set(a) & set(b)
            if not chung:
                continue
            if all(a[o] == b[o] for o in chung):
                trung.append([ten[i], ten[j], len(chung)])
    return trung


def _cham(ket, symbol, khung, vao_kieu, vao_n, giay, hong, tu, den) -> dict:
    """BA CONG. Phai qua het moi doc duoc con so."""
    ra = {"symbol": symbol, "khung": khung, "vao_kieu": vao_kieu,
          "vao_n": vao_n, "cua_so": f"{tu}..{den}", "giay": giay,
          "so_pass": len(ket), "ghi_chu": hong}

    if not ket:
        ra["trang_thai"] = "CHUA_DO_DUOC"
        ra["ly_do"] = "bang ket qua rong"
        return _ghi(ra)

    tong_lenh = sum(k["lenh"] for k in ket)
    if tong_lenh == 0:
        ra["trang_thai"] = "CHUA_DO_DUOC"
        ra["ly_do"] = ("0 lenh tren TOAN BO %d pass - engine vao khong kich "
                       "hoat hoac tester khong chay" % len(ket))
        return _ghi(ra)

    moc = [k for k in ket if k["ma_ho"] == 0]
    if not moc:
        ra["trang_thai"] = "CHUA_DO_DUOC"
        ra["ly_do"] = "khong co dong MOC (ho 0) de so sanh"
        return _ghi(ra)
    # Moc khong dung tham so nen moi pass cua no phai giong nhau; lay mot cai.
    m = max(moc, key=lambda k: k["lenh"])
    ra["moc"] = m

    # CONG 3: ho nao DOI duoc ket qua so voi moc? Ho khong doi gi = im lang.
    tot = {}
    for k in ket:
        h = k["ho"]
        cu = tot.get(h)
        if cu is None or k["sharpe"] > cu["sharpe"]:
            tot[h] = k
    im_lang = [h for h, k in tot.items()
               if h != "moc" and k["lenh"] == m["lenh"]
               and abs(k["lai"] - m["lai"]) < 0.01]
    ra["ho_im_lang"] = im_lang
    if len(im_lang) >= len(HO) - 1:
        ra["trang_thai"] = "CHUA_DO_DUOC"
        ra["ly_do"] = ("MOI ho cho ket qua y het moc - quan tri khong cham vao "
                       "vi the nao (dung trieu chung 12/09)")
        ra["tot_moi_ho"] = tot
        return _ghi(ra)

    theo_ho = {}
    for k in ket:
        theo_ho.setdefault(k["ho"], []).append(k)
    for h, k in tot.items():
        k["so_voi_moc_lai"] = round(k["lai"] - m["lai"], 2)
        k["so_voi_moc_sharpe"] = round(k["sharpe"] - m["sharpe"], 4)
        k["so_voi_moc_dd"] = round(k["dd_pct"] - m["dd_pct"], 3)
        k["y_nghia"] = Y_NGHIA.get(h, "")
        k.update(_cao_nguyen(theo_ho.get(h, []), m))
    ra["tot_moi_ho"] = dict(sorted(tot.items(), key=lambda x: -x[1]["sharpe"]))

    # CAP HO TRUNG NHAU = mot ho khong chay. Phai chan TRUOC khi xep hang, neu
    # khong thi ho chet nam giua bang va khong ai thay.
    ra["cap_trung_nhau"] = _do_trung_nhau(theo_ho)

    # XEP HANG THEO CAO NGUYEN, KHONG THEO CUC DAI. Mot ho co `ty_le_o_hon_moc`
    # >= 0,6 la mot ho ON DINH hon moc tren phan lon cach dat tham so; mot ho
    # chi hon o 1/25 o la mot cuc tri.
    ra["cao_nguyen_hon_moc"] = sorted(
        [h for h, k in tot.items()
         if h != "moc" and k.get("ty_le_o_hon_moc", 0) >= 0.6],
        key=lambda h: -tot[h]["sharpe_trung_vi"])
    ra["chi_cuc_dai_hon_moc"] = sorted(
        [h for h, k in tot.items()
         if h != "moc" and k["sharpe"] > m["sharpe"]
         and k.get("ty_le_o_hon_moc", 0) < 0.6])
    ra["trang_thai"] = "DAT" if ra["cao_nguyen_hon_moc"] else "AM"
    if ra["cap_trung_nhau"]:
        ra["canh_bao"] = ("co cap ho cho ket qua Y HET NHAU - it nhat mot ho "
                          "trong moi cap KHONG chay: " +
                          "; ".join("%s=%s tren %d o" % tuple(c) for c in ra["cap_trung_nhau"]))
    ra["ket"] = sorted(ket, key=lambda k: -k["sharpe"])[:80]
    return _ghi(ra)


def _ghi(ra: dict) -> dict:
    f = LAB / "reports" / ("BENCH_QUAN_TRI_%s_%s.json"
                           % (ra["symbol"], ra["khung"]))
    f.write_text(json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    print("  ghi", f.name)
    return ra


def main() -> int:
    def lay(c, md):
        return sys.argv[sys.argv.index(c) + 1] if c in sys.argv else md
    r = chay(lay("--ma", "US500Cash"), lay("--khung", "H1"),
             int(lay("--vao", "0")), int(lay("--vao-n", "20")),
             "--nhanh" in sys.argv, lay("--tu", "2016.01.01"),
             lay("--den", "2026.07.29"), float(lay("--lot", "1.0")))
    print("\nTRANG THAI:", r.get("trang_thai"), r.get("ly_do", ""))
    if r.get("loi"):
        print("LOI:", r["loi"])
        return 1
    m = r.get("moc")
    if m:
        print("\nMOC (chi luoi an toan): %d lenh, lai %.2f, sharpe %.2f, DD %.2f%%"
              % (m["lenh"], m["lai"], m["sharpe"], m["dd_pct"]))
    print("\n%-14s %6s %6s %6s %9s %8s %8s %7s %7s  %s"
          % ("ho", "P1", "P2", "lenh", "lai", "sh.max", "sh.t.vi", "o>moc",
             "hinh", "y nghia"))
    for h, k in (r.get("tot_moi_ho") or {}).items():
        print("%-14s %6.1f %6.1f %6d %9.2f %8.2f %8.2f %7.0f%% %7s  %s"
              % (h, k["p1"], k["p2"], k["lenh"], k["lai"], k["sharpe"],
                 k.get("sharpe_trung_vi", 0), 100 * k.get("ty_le_o_hon_moc", 0),
                 str(k.get("hinh_dang", ""))[:7], k.get("y_nghia", "")))
    print("\nCAO NGUYEN hon moc (dang tin) :", ", ".join(r.get("cao_nguyen_hon_moc") or []) or "-")
    print("CHI CUC DAI hon moc (cai gai) :", ", ".join(r.get("chi_cuc_dai_hon_moc") or []) or "-")
    if r.get("ho_im_lang"):
        print("HO IM LANG (y het moc)        :", ", ".join(r["ho_im_lang"]))
    if r.get("canh_bao"):
        print("\n!! " + r["canh_bao"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
