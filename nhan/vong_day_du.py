# -*- coding: utf-8 -*-
"""vong_day_du.py - MOT LENH chay CA BA TRU theo dung so do cua chu du an.

## Lo hong cau truc nay vá

`SO_DO_HE_THONG.txt` mo ta ba tru noi tiep nhau:

    SEEKER  ->  QUANTLAB  ->  EVO
    (pheu)      (tong quan · quan li · chien luoc · noi sinh · uu tien)
                                                      |
                                            EVO giam sat ca hai tru tren

Nhung do ngay 12/09/2026: `day_chuyen.mot_luot` - cho duy nhat noi cac manh -
chi chay **san -> doc -> boc**, roi DUNG. Chinh docstring cua no hua co khau
`DO: bien_don_bay.do_bien + cong + do_on_dinh`, ma ma nguon khong goi. Toan bo
phia QUANTLAB (`to_hop`, `suy_nguoc`, `vao_lenh`, `dap_quan_tri`) va ca EVO
nam ngoai day chuyen - chung chi chay khi co nguoi go tay.

He qua: mot he "24/7" se quay mai o khau thu thap, kho co che phinh ra, va
KHONG AI CHAM no. Do dung la hinh dang cua `bo-cat-tach-het-la-nut-that`:
kho x6 ma ung vien cham cong van 21.

## TAM CHANG, VA MOI CHANG DEU BAO SUAT

Mot day chuyen khong bao suat tung chang thi khong ai biet nut that o dau -
bai hoc `pheu-nguon-do-tung-chang`: *"toc do khong bao gio la thu ban doan
duoc"*. Nen moi chang o day tra ve `vao / ra / giay`.

    1 SAN_BOC     nguon -> tai lieu -> co che        (SEEKER)
    2 HO_SO       song · mua vu · tuong quan          (QUANTLAB tong quan)
    3 NOI_SINH    tu sinh co che tu chinh lich su     (QUANTLAB noi sinh)
    4 SUY_NGUOC   truoc cu di manh co dau hieu gi     (QUANTLAB noi sinh)
    5 TO_HOP      da ma x da khung x quan li + HOLDOUT (QUANTLAB chien luoc)
    6 DA_THOI_DAI co song qua MOI thoi ky khong, hay chi mot che do
    7 CHAM_TIEN   bang diem TIEN + RUI RO           (LUAT SO 0)
    8 EVO         suc khoe + cat nghia + bao ra ngoai

## KHONG TRUNG VOI `tru/quantlab.py`

`dieu_phoi.py` (control plane 24/7) chay 5 tru, trong do `tru/quantlab.py` la
mot module 1.700 dong co canary + xu ly ung vien + tu kham pha. File nay KHONG
thay no.

Khac nhau o cho: tru QUANTLAB chay vong ung vien da co trong so. Con `to_hop`,
`suy_nguoc`, `vao_lenh`, `dap_quan_tri` - dung hom 12/09 - thi tru khong biet
den. Vong nay la cho chay nhung thu do, cho toi khi chung duoc dua han vao tru.

## HAI NGUYEN TAC

**Khong chay lai thu con moi.** Moi chang co `han_gio`: ho so con moi thi bo
qua. Mot vong day du ma lan nao cung quet lai tu dau thi khong ai dam chay no.

**Mot chang hong KHONG chan cac chang sau.** Cung ly do voi `day_viec.py`:
day chuyen dung o loi dau tien la day chuyen khong ai dam bat.

Chay:  python -m nhan.vong_day_du [--ma US500CASH] [--khung D1 H4] [--nhanh]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

SO = LAB / "reports" / "VONG_DAY_DU.json"

#: Ten cac ham chang, theo dung thu tu `vong()` goi. MOT nguon su that - test
#: doc tu day chu khong go cung con so. Ban cu go cung 6; them hai chang moi
#: (CHAM_TIEN, DA_THOI_DAI) lam test do voi "7 != 6" - test do dang kiem mot
#: CON SO chu khong kiem mot TINH CHAT.
TEN_CHANG = ("_san_boc", "_ho_so", "_noi_sinh", "_suy_nguoc", "_to_hop",
             "_da_thoi_dai", "_cham_tien", "_evo")

#: Ho so cu hon bay nhieu GIO thi chay lai. Khong thi bo qua - chang nay dat.
HAN_GIO = {"ho_so": 24 * 7, "noi_sinh": 24 * 3, "suy_nguoc": 24 * 7,
           "to_hop": 24 * 2}


def _tuoi(tep: str) -> float:
    """So gio ke tu lan ghi cuoi. Vo cung neu chua co."""
    p = LAB / "reports" / tep
    try:
        return (time.time() - p.stat().st_mtime) / 3600.0
    except Exception:
        return float("inf")


def _chang(ten: str, ham, _in, **kw) -> dict:
    """Chay mot chang, BAT MOI LOI. Tra {ten, ok, giay, ...}."""
    t0 = time.time()
    _in("")
    _in("=== %s ===" % ten)
    try:
        ra = ham(**kw) or {}
        ra = ra if isinstance(ra, dict) else {"ket": str(ra)[:200]}
        ra.update({"ten": ten, "ok": True, "giay": round(time.time() - t0, 1)})
    except Exception as e:
        # Mot chang hong khong duoc chan chang sau - cung ly do voi `day_viec`.
        ra = {"ten": ten, "ok": False, "giay": round(time.time() - t0, 1),
              "loi": "%s: %s" % (type(e).__name__, str(e)[:200])}
        _in("  LOI: %s" % ra["loi"])
    _in("  %s trong %.0fs" % ("xong" if ra["ok"] else "HONG", ra["giay"]))
    return ra


# --------------------------------------------------------------- CAC CHANG
def _san_boc(ma: str, in_ra) -> dict:
    from nhan import day_chuyen as DC
    k = DC.mot_luot(ma, in_ra=in_ra)
    ra = {"san": k.get("san"), "boc": k.get("boc")}
    # KENH DA DUYET, doc lai theo LICH. Dong so do: *"biet doc lai cac bai cua
    # nhung nguon da follow mot luot de update file moi (tinh toan lich trinh
    # khong can lam hang ngay)"*.
    #
    # `theo_doi` co tu 11/09 voi 9 kenh da duyet tay, nhung khong bo lap lich
    # nao goi no - `lan_quet_cuoi` dung yen tu 13/08. Cua nay dang gia hon quet
    # chung chung: corpus video tim kiem chung chung cho 27 phu de -> 3 spec ->
    # **0 co che moi**, vi phan lon la video nhap mon noi ve khai niem.
    try:
        from nhan import theo_doi as TD
        TD._khoi_tao()
        han = TD.den_han()
        if han:
            t = TD.mot_luot()
            ra["theo_doi"] = "%d kenh den han -> %s" % (len(han), t)
            in_ra("  theo doi: quet %d kenh den han" % len(han))
        else:
            ra["theo_doi"] = "0/%d kenh den han" % len(TD.bang())
            in_ra("  theo doi: khong kenh nao den han (chu ky ~11 ngay)")
    except Exception as e:
        in_ra("  theo doi: %s" % e)
    return ra


def _ho_so(khung: str, sp: int, in_ra) -> dict:
    ra = {}
    if _tuoi("HO_SO_SONG.json") > HAN_GIO["ho_so"]:
        from nhan import ho_so_song as HS
        ra["song"] = len((HS.quet(khung=khung, so_tien_trinh=sp,
                                  in_ra=in_ra) or {}).get("ma", []) or [])
    else:
        in_ra("  ho so song con moi - bo qua")
    # MUA VU / ENTRY-TIME: dong "Nghien cuu cac dang entry time cua cac loai
    # tai san nhu thoi diem mua ban co xac suat cao trong nam" cua so do.
    # Module co tu truoc nhung MO COI - ban do 12/09 tim ra.
    if _tuoi("HO_SO_MUA_VU.json") > HAN_GIO["ho_so"]:
        from nhan import ho_so_mua_vu as MV
        k = MV.quet(khung=khung, so_tien_trinh=sp, in_ra=in_ra) or {}
        # `quet` tra {"MA|KHUNG": {...}} chu khong phai {"bang": [...]}.
        co = sum(1 for v in k.values()
                 if isinstance(v, dict)
                 and not str(v.get("cau_tra_loi", "")).startswith("KHONG"))
        ra["mua_vu"] = "%d/%d ma co mua vu do duoc" % (co, len(k))
    else:
        in_ra("  ho so mua vu con moi - bo qua")
    if _tuoi("HO_SO_TUONG_QUAN_%s.json" % khung.upper()) > HAN_GIO["ho_so"]:
        from nhan import ho_so_tuong_quan as TQ
        from nhan import ho_so_symbol as HSS
        hs = HSS.doc()
        hs = list(hs.values()) if isinstance(hs, dict) else hs
        ma = sorted({str(x.get("ma")) for x in hs
                     if isinstance(x, dict) and x.get("ma")})
        ra["tuong_quan"] = (TQ.tinh(ma, khung, in_ra=in_ra) or {}).get("so_cap")
    else:
        in_ra("  ho so tuong quan con moi - bo qua")
    return ra


def _noi_sinh(ma: str, khung: str, in_ra) -> dict:
    from nhan import du_lieu as DL
    from nhan import ngu_phap as NP
    from nhan import noi_sinh as NS
    df = DL.cat_theo_chat_luong(DL.nap(ma, khung), ma)[0]
    if len(df) < 800:
        return {"bo": "chi %d bar sau kiem chat luong" % len(df)}
    tr = DL.hai_nua(df, 0.6)[0]
    ds = NS.sinh(tr)
    kho = NP.doc_kho()
    co = {x.get("van_tay") for x in kho}
    them = []
    for s in ds:
        try:
            vt = NP.van_tay_dieu_kien(s)
        except Exception:
            continue
        if vt in co:
            continue
        s["van_tay"] = vt
        co.add(vt)
        them.append(s)
    if them:
        NP.luu_kho(kho + them)
    in_ra("  sinh %d co che, MOI %d -> kho %d"
          % (len(ds), len(them), len(kho) + len(them)))
    ra = {"sinh": len(ds), "moi": len(them), "kho": len(kho) + len(them)}

    # QUY LUAT SONG: dong so do *"nghien cuu cac dac diem chung bang zigzag de do
    # cac song, bien do thuong day, tan suat day, tan suat hoi, bien do hoi,...
    # cac moc magnetic"*.
    #
    # `ho_so_song` MO TA song; `quy_luat_song` hoi song co QUY LUAT khong - mot
    # buoc xa hon va la cho sinh ra co che. No mo coi cho toi 12/09. Chay ton 2
    # giay tren mot ma nen khong co ly do de khong goi.
    try:
        from nhan import quy_luat_song as QS
        k = QS.quet(ma, [khung], in_ra=in_ra) or {}
        ra["quy_luat_song"] = "%s quy luat dat tren moi khung da thu" % k.get(
            "dat_tren_may_khung")
    except Exception as e:
        in_ra("  quy luat song: %s" % e)
    return ra


def _suy_nguoc(khung: str, sp: int, in_ra) -> dict:
    from nhan import suy_nguoc as SN
    k = SN.quet(khung=khung, so_tien_trinh=sp, in_ra=in_ra) or {}
    manh = [d for d in (k.get("bang") or [])
            if d.get("p_dau_gop", 1.0) <= SN.NGUONG_P_GOP]
    return {"so_ma": k.get("so_ma"), "dau_hieu_dong_thuan": len(manh)}


def _to_hop(cac_khung, sp: int, in_ra) -> dict:
    from nhan import to_hop as TH
    k = TH.chay(tuple(cac_khung), sp=sp, in_ra=in_ra) or {}
    TH.tong_ket(k, in_ra=in_ra)
    c4 = (k.get("chang") or {}).get("4") or {}
    return {"chang": k.get("chang"), "qua_holdout": c4.get("qua_holdout")}


def _da_thoi_dai(in_ra, tran: int = 12) -> dict:
    """Co che qua holdout co song qua MOI THOI DAI khong, hay chi mot thoi ky.

    Dong so do: *"tat ca moi chien luoc can test da cap / da khung"*. Va bai hoc
    `ba-ho-ba-thoi-ky`: quantora chi song truoc 1987, loc xu huong truoc 1990,
    z5 sau 2002 - ba he "qua cong" ma thuc ra la ba hien tuong CHE DO.

    `nhan/da_thoi_dai.py` co tu 04/09 nhung MO COI. No lam dung viec can: chay
    co che tren TUNG cua so du lieu sach roi gop, thay vi lay mot doan dai nhat
    (SP500: 3.404 nen dang dung tren 24.754 nen co that).

    KHONG noi cac cua so thanh mot chuoi gia - gop o muc THONG KE.
    """
    from nhan import da_thoi_dai as DTD
    from nhan import ngu_phap as NP
    so = LAB / "reports" / "TO_HOP.json"
    if not so.exists():
        return {"bo": "chua co TO_HOP.json"}
    d = json.loads(so.read_text(encoding="utf-8"))
    qua = [r for r in (d.get("holdout") or []) if r.get("qua_holdout")][:tran]
    if not qua:
        return {"bo": "0 co che qua holdout - khong co gi de thu"}
    # Tra theo CA `ten` lan `van_tay`: `to_hop` ghi `co_che` = ten cua spec.
    # Chi tra van_tay thi moi dong bao "khong tim thay spec" va chang nay im
    # lang bo qua tat ca - am tinh gia.
    kho = {}
    for x in NP.doc_kho():
        if isinstance(x, dict):
            for kk in (x.get("ten"), x.get("van_tay")):
                if kk:
                    kho.setdefault(kk, x)
    # Mot co che qua holdout o nhieu CAU TRUC/LUAT khac nhau van la MOT co che
    # tren MOT ma - chay lai 4 lan chi ton thi gio va in ra 4 dong y het nhau.
    da = set()
    qua = [r for r in qua
           if not (((r.get("ma"), r.get("co_che")) in da)
                   or da.add((r.get("ma"), r.get("co_che"))))]
    ra, thieu = [], 0
    for r in qua:
        spec = kho.get(r.get("co_che"))
        if not isinstance(spec, dict):
            thieu += 1
            continue                      # khong doan spec tu ten
        try:
            k = DTD.chay_co_che(spec, r["ma"], r.get("khung", "D1"))
        except Exception as e:
            ra.append({"ma": r["ma"], "loi": "%s: %s"
                       % (type(e).__name__, str(e)[:60])})
            continue
        td = [x for x in k["thoi_dai"] if x.get("sharpe") is not None]
        duong = sum(1 for x in td if x["sharpe"] > 0)
        ra.append({"ma": r["ma"], "co_che": str(r.get("co_che"))[:28],
                   "so_thoi_dai": len(td), "duong": duong,
                   "sharpe_gop": (k.get("gop") or {}).get("sharpe")})
        in_ra("  %-10s %-28s %d/%d thoi dai duong  sharpe gop %s"
              % (r["ma"], str(r.get("co_che"))[:28], duong, len(td),
                 (k.get("gop") or {}).get("sharpe")))
    if thieu:
        in_ra("  %d/%d co che khong tim thay spec trong kho - bo qua, khong doan"
              % (thieu, len(qua)))
    # BA trang thai, khong phai hai. Mot ma chi co MOT cua so sach thi phep thu
    # nay khong noi duoc gi ve no - goi do la "hien tuong che do" la bia ra ket
    # luan tu cho khong co du lieu ([[ket-luan-am-phai-phan-biet-CHUA-DO]]).
    do_duoc = [x for x in ra if x.get("so_thoi_dai", 0) >= 2]
    chua_do = [x for x in ra if 0 < x.get("so_thoi_dai", 0) < 2]
    moi_thoi = [x for x in do_duoc if x["duong"] == x["so_thoi_dai"]]
    if ra:
        in_ra("")
        in_ra("  DO DUOC   %d co che (>=2 cua so sach): %d duong o MOI thoi dai"
              % (len(do_duoc), len(moi_thoi)))
        if chua_do:
            in_ra("  CHUA DO   %d co che chi co 1 cua so sach - phep thu nay"
                  % len(chua_do))
            in_ra("            khong noi duoc gi ve chung, KHONG phai am tinh.")
        if len(do_duoc) > len(moi_thoi):
            in_ra("  Trong so DO DUOC, %d co che chet o it nhat mot thoi dai ->"
                  % (len(do_duoc) - len(moi_thoi)))
            in_ra("  ung vien cua mot CHE DO, khong phai cua thi truong.")
    return {"thu": len(ra), "thieu_spec": thieu, "do_duoc": len(do_duoc),
            "chua_do_duoc": len(chua_do), "moi_thoi_dai": len(moi_thoi)}


def _cham_tien(in_ra) -> dict:
    """Chang CUOI: doc ket qua to_hop roi tra loi cau hoi TIEN.

    Them 12/09 sau khi `nhan/ban_do.py` cho thay `cham_diem` va `cong_ra_tien`
    deu MO COI. Mot day chuyen ket thuc o "bao nhieu co che qua holdout" la tra
    loi SAI cau hoi: chu du an hoi *"ra tien bao nhieu, rui ro the nao"*.
    """
    from nhan import cham_diem as CD
    so = LAB / "reports" / "TO_HOP.json"
    if not so.exists():
        return {"bo": "chua co TO_HOP.json"}
    d = json.loads(so.read_text(encoding="utf-8"))
    top = d.get("top") or []
    ho = {(r.get("ma"), r.get("khung"), r.get("co_che"), r.get("luat"))
          for r in (d.get("holdout") or []) if r.get("qua_holdout")}
    def _nam(r) -> float:
        """So nam cua dong. Thieu thi DO LAI tu du lieu - do khong phai doan.

        Phan biet hai viec: lay mac dinh 0 la DOAN (va no thoi `so_lenh_nam`
        thanh tong so lenh); doc chi muc thoi gian cua chinh chuoi la DO. Ban
        TO_HOP.json cu khong co truong nay, va chay lai ca pheu mat ~110 phut
        chi de co mot con so doc duoc trong vai giay.
        """
        if r.get("so_nam"):
            return float(r["so_nam"])
        k = (r.get("ma"), r.get("khung", "D1"))
        if k not in _nam.cache:
            try:
                from nhan import du_lieu as DL
                from nhan import vao_lenh as VL
                _nam.cache[k] = VL.so_nam_cua(DL.nap(k[0], k[1]))
            except Exception:
                _nam.cache[k] = 0.0
        return _nam.cache[k]
    _nam.cache = {}

    diem, thieu_nam = [], 0
    for r in top:
        r = dict(r, so_nam=_nam(r))
        if not r["so_nam"]:
            thieu_nam += 1
            continue           # khong doan: khong do duoc thi khong cham
        x = CD.tu_to_hop(r)
        x["da_qua_cong_that"] = (r.get("ma"), r.get("khung"),
                                 r.get("co_che"), r.get("luat")) in ho
        diem.append(x)
    if thieu_nam:
        in_ra("  %d/%d dong thieu `so_nam` (ban TO_HOP.json cu) - bo qua, "
              "chay lai to_hop de co" % (thieu_nam, len(top)))
    if not diem:
        return {"bo": "0/%d dong cham duoc" % len(top), "thieu_nam": thieu_nam}
    CD.bang(diem, in_ra=in_ra, tran=15)
    return {"cham": len(diem), "thieu_nam": thieu_nam,
            "chay_duoc": sum(1 for x in diem if x["muc"] == "CHAY_DUOC"),
            "qua_holdout": len(ho)}


def _evo(in_ra) -> dict:
    from nhan import evo as EVO
    k = EVO.do_het()
    EVO.bao_cao(k, in_ra=in_ra, ghi_so=True)
    try:
        EVO.bao_xa(k, in_ra=in_ra)
    except Exception as e:
        in_ra("  khong bao xa duoc: %s" % e)
    return {"dem": k.get("dem")}


# ------------------------------------------------------------------- VONG
def vong(ma: str = "US500CASH", cac_khung=("D1",), sp: int = 4,
         nhanh: bool = False, in_ra=print) -> dict:
    """Chay ca sau chang. `nhanh=True` bo chang SAN_BOC (khau cham nhat)."""
    t0 = time.time()
    khung = cac_khung[0]
    chang = []
    if not nhanh:
        chang.append(_chang("1 SAN_BOC (SEEKER)", _san_boc, in_ra,
                            ma=ma, in_ra=in_ra))
    chang.append(_chang("2 HO_SO (QUANTLAB tong quan)", _ho_so, in_ra,
                        khung=khung, sp=sp, in_ra=in_ra))
    chang.append(_chang("3 NOI_SINH (QUANTLAB noi sinh)", _noi_sinh, in_ra,
                        ma=ma, khung=khung, in_ra=in_ra))
    if _tuoi("SUY_NGUOC.json") > HAN_GIO["suy_nguoc"]:
        chang.append(_chang("4 SUY_NGUOC (QUANTLAB noi sinh)", _suy_nguoc,
                            in_ra, khung=khung, sp=sp, in_ra=in_ra))
    else:
        in_ra("\n=== 4 SUY_NGUOC === con moi - bo qua")
    if _tuoi("TO_HOP.json") > HAN_GIO["to_hop"]:
        chang.append(_chang("5 TO_HOP (QUANTLAB chien luoc)", _to_hop, in_ra,
                            cac_khung=cac_khung, sp=sp, in_ra=in_ra))
    else:
        in_ra("\n=== 5 TO_HOP === con moi - bo qua")
    chang.append(_chang("6 DA_THOI_DAI (chong hien tuong che do)", _da_thoi_dai,
                        in_ra, in_ra=in_ra))
    chang.append(_chang("7 CHAM_TIEN (LUAT SO 0)", _cham_tien, in_ra,
                        in_ra=in_ra))
    chang.append(_chang("8 EVO", _evo, in_ra, in_ra=in_ra))

    ket = {"ma": ma, "khung": list(cac_khung),
           "luc": time.strftime("%Y-%m-%d %H:%M:%S"),
           "giay": round(time.time() - t0, 1), "chang": chang,
           "hong": [c["ten"] for c in chang if not c["ok"]]}
    SO.parent.mkdir(exist_ok=True)
    SO.write_text(json.dumps(ket, ensure_ascii=False, indent=1, default=str),
                  encoding="utf-8")
    in_ra("")
    in_ra("=" * 62)
    in_ra("VONG DAY DU xong trong %.0f phut" % (ket["giay"] / 60))
    for c in chang:
        in_ra("  %-34s %-5s %7.0fs" % (c["ten"], "ok" if c["ok"] else "HONG",
                                       c["giay"]))
    if ket["hong"]:
        in_ra("  CHANG HONG: %s" % ", ".join(ket["hong"]))
    in_ra("-> %s" % SO)
    return ket


def main(argv: list[str]) -> int:
    ma = "US500CASH"
    kh = ["D1"]
    sp = 4
    if "--ma" in argv:
        ma = argv[argv.index("--ma") + 1]
    if "--khung" in argv:
        i = argv.index("--khung") + 1
        kh = [x for x in argv[i:] if not x.startswith("--")] or ["D1"]
    if "--tien-trinh" in argv:
        sp = int(argv[argv.index("--tien-trinh") + 1])
    vong(ma, tuple(kh), sp=sp, nhanh="--nhanh" in argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
