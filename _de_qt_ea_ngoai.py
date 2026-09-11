# -*- coding: utf-8 -*-
"""_de_qt_ea_ngoai.py - CONG CUOI cua khoi 6: de bo quan tri len MOT EA NGOAI.

Cau hoi: bo quan tri cua ta co dieu khien duoc mot he KHONG PHAI cua ta khong?

Cach do - va vi sao khong the do cach khac:
  MT5 Strategy Tester chi chay MOT EA moi lan, nen khong the cho EA ngoai va
  EA giam sat chay song song. Nhung ta CO MA NGUON (seeker da tai 145 file .mq5,
  25 la EA that). Chen khoi quan tri vao chinh ma do, bien dich MOT lan, roi
  quet `QT_MaLuat` 0..K trong CUNG mot lan boot:

      QT_MaLuat = 0   quan tri TAT  -> MOC
      QT_MaLuat = k   luat thu k    -> so voi moc

  Cung EA, cung cua so, cung du lieu, cung mot ban .ex5. Chenh lech chi con mot
  nguyen nhan. Va "cung mot lan boot" la bat buoc: so hai lan boot khac nhau la
  so hai thu khac nhau [[tester-nhoi-het-vao-mot-lan-boot]].

CONG: it nhat mot luat lam DOI SO LENH so voi moc. Khong doi so lenh nghia la
quan tri khong cham vao vi the nao - luc do moi con so lai/lo deu vo nghia, va
day la trang thai CHUA_DO_DUOC chu khong phai "quan tri khong an".

Chay:  python _de_qt_ea_ngoai.py [symbol] [duong dan .mq5]
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

import chay_tester_kho as C  # noqa: E402
from nhan import de_quan_tri as DQ  # noqa: E402
from nhan import khoa_tester as KT  # noqa: E402
from nhan import quan_tri_dsl as QT  # noqa: E402

TEN_EA = "DeQT_EaNgoai"
RA = GOC / "reports" / "DE_QT_EA_NGOAI.json"


def _ini(ten: str, symbol: str, so_luat: int, tu: str, den: str,
         khung: str = "D1") -> Path:
    p = C.XM_DATA / f"{ten}.ini"
    p.write_text(f"""[Tester]
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
Deposit=10000
Currency=USD
Leverage=1:500
ProfitInPips=0
Report={ten}
ReplaceReport=1
ShutdownTerminal=1

[TesterInputs]
QT_MaLuat=0||0||1||{max(so_luat - 1, 1)}||Y
QT_Magic=0||0||0||0||N
QT_LotGoc=0.10||0.10||0||0||N
""", encoding="utf-16")
    return p


def chay(symbol: str = "US500Cash", nguon_ea: str | None = None,
         tu: str = "2018.01.01", den: str = "2026.07.29",
         khung: str = "H1", so_luat: int = 14) -> dict:
    """`khung` MAC DINH LA H1, khong phai D1 - va do la mot bai hoc da tra gia.

    So bai hoc, the `chay EA D1 tren CFD chi so trong MT5 tester`:
    `Model=2` tren khung D1 thi MT5 dat tick o OPEN, tuc 00:00 - NGOAI PHIEN cua
    CFD chi so - nen 463 lenh deu `Market closed` va bao cao ghi ra "0 lenh",
    khong loi, khong canh bao.

    Lan chay dau tien cua ham nay (23:1x 11/09) lap lai dung loi do: Period=D1,
    moc 0 lenh. Hoi `b da-thu "EA D1 chay tester CFD chi so bao 0 lenh"` thi so
    tra ra ngay the tren. Do la lan dau so bai hoc cua khoi 2 tra cong trong mot
    tinh huong that.
    """
    ea = Path(nguon_ea or (GOC / "downloaded_codes" / "github" /
                           "EA Snippets_Breakout_Breakout1.mq5"))
    if not ea.exists():
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": f"khong thay EA {ea}"}

    kho = [c for c in QT.doc_kho() if not QT.kiem_khai_bao(c)][:so_luat]
    if len(kho) < 2:
        return {"trang_thai": "CHUA_DO_DUOC",
                "ly_do": f"kho quan tri chi co {len(kho)} luat qua cong"}

    ma_goc = ea.read_text(encoding="utf-8", errors="ignore")
    ma_moi, luat = DQ.chen_tu_spec(ma_goc, kho, khung=khung, magic=0)
    loi_chen = DQ.kiem_da_chen(ma_moi)
    if loi_chen:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "; ".join(loi_chen)}

    src = C.XM_DATA / "MQL5" / "Experts" / f"{TEN_EA}.mq5"
    src.write_text(ma_moi, encoding="utf-8")
    loi = C.bien_dich(src)
    if loi:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": loi[:400], "ea": ea.name}

    ten = f"deqt_{symbol}"
    ini = _ini(ten, symbol, len(luat), tu, den, khung)
    for h in (".xml", ".htm"):
        f = C.XM_DATA / (ten + h)
        if f.exists():
            f.unlink()

    t0 = time.time()
    # CHO khoa thay vi bo cuoc: lan chay dau (23:08 ngay 11/09) bi tu choi vi
    # qwen dang chay mot viec tester khac. Do la cai khoa lam DUNG viec - truoc
    # hom nay ca hai da cung chay va ghi de ket qua cua nhau trong im lang.
    # Mot lan quet tester ~2-20 phut nen cho 45 phut la hop ly.
    KT.phong(C.XM_EXE, ini, tran=3600, nhip=8, dong_truoc=C.dong_terminal,
             viec=f"de_qt_ea_ngoai {symbol}", cho_giay=45 * 60)
    hong = C.kiem_log_agent()
    f = C.XM_DATA / (ten + ".xml")
    if hong.startswith("TESTER KHONG CHAY DUOC") or not f.exists():
        return {"trang_thai": "CHUA_DO_DUOC",
                "ly_do": hong if hong else "khong thay bang ket qua",
                "giay": round(time.time() - t0)}

    ket = []
    for d in C.doc_xml(f):
        k = int(C._so(d.get("QT_MaLuat", -1), -1))
        if k < 0:
            continue
        ket.append({"luat": k,
                    "ten": (luat[k].get("ten") if k < len(luat) else "?"),
                    "lenh": int(C._so(d.get("Trades"))),
                    "lai": C._so(d.get("Profit")),
                    "sut_giam": C._so(d.get("Equity DD %", d.get("Drawdown", 0)))})
    ket.sort(key=lambda x: x["luat"])
    moc = next((x for x in ket if x["luat"] == 0), None)
    if not moc:
        return {"trang_thai": "CHUA_DO_DUOC",
                "ly_do": "khong co pass QT_MaLuat=0 - khong co MOC de so"}
    if not moc["lenh"]:
        # EA ngoai khong dat lenh nao thi khong the ket luan gi ve quan tri.
        return {"trang_thai": "CHUA_DO_DUOC", "moc": moc,
                "ly_do": "EA ngoai KHONG dat lenh nao o moc - doi symbol/cua so",
                "ket": ket}

    # CONG: bat ky SO NAO doi - khong chi so lenh.
    #
    # Lan dat cong dau tien cua toi chi hoi "so lenh co doi khong", va no SAI:
    # mot luat `dat_hue` hay `trailing` doi GIA THOAT chu khong doi SO LENH. Chay
    # that 23:2x ngay 11/09: 0/14 luat doi so lenh, nhung luat 6 doi LAI tu
    # -108,76 sang -99,20 - tuc quan tri CO cham vao vi the, va cong cua toi se
    # bao "AM" cho mot nang luc dang chay dung.
    #
    # Chi nhung luat NHOI hay CAT SOM moi doi so lenh; ca ho `dat_hue`/`trailing`
    # - tuc phan lon kho quan tri - khong bao gio doi no.
    def _khac(a, b, eps=1e-9):
        return abs(float(a or 0) - float(b or 0)) > eps

    doi = [x for x in ket if x["luat"] and (
        x["lenh"] != moc["lenh"] or _khac(x["lai"], moc["lai"])
        or _khac(x["sut_giam"], moc["sut_giam"]))]
    doi_lenh = [x for x in doi if x["lenh"] != moc["lenh"]]
    kq = {
        "trang_thai": "DAT" if doi else "AM",
        "ea": ea.name, "symbol": symbol, "khung": khung, "cua_so": f"{tu}..{den}",
        "giay": round(time.time() - t0),
        "so_luat": len(ket) - 1,
        "moc_tat_quan_tri": moc,
        "so_luat_cham_duoc_vi_the": len(doi),
        "so_luat_doi_SO_LENH": len(doi_lenh),
        "luat_cham_duoc": [{"luat": x["luat"], "ten": x["ten"],
                            "lenh": x["lenh"], "lai": x["lai"]} for x in doi[:8]],
        "ly_do": ("" if doi else
                  "KHONG luat nao doi duoc so nao - quan tri khong cham vao vi "
                  "the nao. Moi con so lai/lo deu vo nghia o day."),
        "ket": ket,
    }
    RA.parent.mkdir(exist_ok=True)
    RA.write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    return kq


if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "XM_US500Cash"
    ea = sys.argv[2] if len(sys.argv) > 2 else None
    r = chay(sym, ea)
    print(json.dumps({k: v for k, v in r.items() if k != "ket"},
                     ensure_ascii=False, indent=1))
    for x in (r.get("ket") or [])[:16]:
        print(f"  luat {x['luat']:2d} · {str(x['ten'])[:34]:36s} "
              f"lenh {x['lenh']:5d} · lai {x['lai']:10.1f}")
