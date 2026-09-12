# -*- coding: utf-8 -*-
"""day_viec.py - HANG DOI VIEC XAY, chay TUAN TU va LIEN TUC.

Chu du an 12/09/2026: *"Thi phai thiet lap sao de chay lien tuc va tuan tu chu?"*

## VI SAO CAN FILE NAY

Ba lan trong mot phien toi ket thuc luot bang mot LOI HUA ("sang Q3") thay vi
bang KET QUA. Nguyen nhan khong phai y chi - la thieu co cau: moi buoc deu phai
do toi tu tay khoi dong lai, nen he dung ngay khi toi dung.

Lab da co hai hang doi nhung khong cai nao lam viec nay:
    `nhan/hang_doi.py`  hang doi UNG VIEN cua QUANTLAB (lease SQLite)
    `hang_doi.py`       dong bo VPS <-> may nha qua thu muc chung
Ca hai deu xu ly DU LIEU. Khong cai nao chay VIEC XAY (chay module moi, do dac,
sinh bao cao). Day la cai con thieu.

## BON RANG BUOC

  1. **TUAN TU, mot viec mot luc.** Cac module nang (`ho_so_song`, `ho_so_mua_vu`)
     tu no da mo 10 tien trinh con. Chay hai viec do cung luc thi 20 tien trinh
     tranh nhau 20 luong -> cham hon chay lan luot. Ngoai ra `terminal64.exe` chi
     co MOT (xem `nhan/khoa_tester.py`), nen viec dung tester BAT BUOC tuan tu.

  2. **BEN QUA SU CO.** Ghi trang thai xuong dia SAU MOI chuyen doi, khong giu
     trong RAM. May treo / dong may / Ctrl-C -> chay lai la di tiep tu cho do,
     khong lam lai tu dau.

  3. **LOI KHONG CHAN HANG.** Mot viec hong thi danh dau `loi` roi DI TIEP. Bai
     hoc `hang-doi-doc-bi-url-chet-chiem`: 406 URL chet lam ca hang doi bao "het
     ton kho". Hang doi tuan tu ma dung lai o loi dau tien thi vo dung hon nua.

  4. **CO HAN GIO.** Moi viec co `han_giay`. Qua han thi giet ca CAY tien trinh
     (module nang de lai tien trinh con mo coi neu chi giet tien trinh cha).

## DUNG

    python day_viec.py              chay tiep den khi het hang doi
    python day_viec.py --xem        bang trang thai (khong chay gi)
    python day_viec.py --them MA "mo ta" "lenh" [han_giay]
    python day_viec.py --lam-lai MA dat lai mot viec ve `cho`
    python day_viec.py --bo MA      bo mot viec khoi hang doi
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

LAB = Path(__file__).resolve().parent
SO = LAB / "config" / "day_viec.json"
NHAT_KY = LAB / "nhat_ky" / "day_viec"

#: Han mac dinh cho mot viec neu khong khai bao (giay).
HAN_MAC_DINH = 3600
#: So dong duoi cua log giu lai trong so, de `b` doc duoc ma khong mo file.
DUOI_GIU = 40


#: Duoi bao nhieu GB thi DUNG hang doi. 2 GB vi mot lan chay pheu +
#: pool 10 tien trinh an vai GB file tam - do that 12/09: dung tien
#: trinh xong thi dia tu 177 MB nhay len 6,4 GB.
NGUONG_DIA_GB = 2.0


def _gio() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def doc() -> dict:
    if SO.exists():
        try:
            return json.loads(SO.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"viec": [], "sua_luc": _gio()}


def ghi(so: dict) -> None:
    """Ghi NGUYEN TU: ghi ban tam roi doi ten. Ghi thang de mat so neu treo."""
    so["sua_luc"] = _gio()
    SO.parent.mkdir(parents=True, exist_ok=True)
    tam = SO.with_suffix(".tam")
    tam.write_text(json.dumps(so, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tam, SO)


def them(ma: str, mo_ta: str, lenh: str, han: int = HAN_MAC_DINH,
         truoc: str | None = None) -> dict:
    """Them mot viec. Cung `ma` thi GHI DE - hang doi khai bao lai duoc."""
    so = doc()
    moi = {"ma": ma, "mo_ta": mo_ta, "lenh": lenh, "han_giay": int(han),
           "trang_thai": "cho", "them_luc": _gio()}
    for i, v in enumerate(so["viec"]):
        if v["ma"] == ma:
            moi["them_luc"] = v.get("them_luc", moi["them_luc"])
            so["viec"][i] = moi
            break
    else:
        if truoc:
            vt = next((i for i, v in enumerate(so["viec"]) if v["ma"] == truoc),
                      len(so["viec"]))
            so["viec"].insert(vt, moi)
        else:
            so["viec"].append(moi)
    ghi(so)
    return moi


def _giet_cay(p: subprocess.Popen) -> None:
    """Giet ca CAY tien trinh. Module nang mo 10 tien trinh con qua
    multiprocessing; giet moi tien trinh cha de lai chung mo coi va chung giu
    CPU den het phien."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)],
                           capture_output=True, timeout=30)
        else:
            p.kill()
    except Exception:
        try:
            p.kill()
        except Exception:
            pass


def _kiem_chung_cu(bc: dict, t0: float) -> tuple[bool, str]:
    """Viec co thuc su SINH RA gi khong. Tra (dat, ly do doc duoc).

    Hai dang chung cu, khai trong truong `bang_chung` cua viec:

        {"tep_moi_hon": "reports/TO_HOP.json"}   tep phai duoc ghi SAU khi
                                                 viec bat dau
        {"kho_tang": true}                       so co che trong kho phai tang

    Co y de don gian: mot co cau chung cu phuc tap se khong ai khai, va mot
    truong khong ai khai thi bang khong co.
    """
    tep = bc.get("tep_moi_hon")
    if tep:
        p = LAB / tep if not Path(tep).is_absolute() else Path(tep)
        try:
            if p.stat().st_mtime >= t0:
                return True, "%s da duoc ghi lai" % p.name
            return False, "%s KHONG doi (ghi lan cuoi truoc khi viec chay)" % p.name
        except FileNotFoundError:
            return False, "khong co %s" % p.name
    if bc.get("kho_tang"):
        truoc = bc.get("_kho_truoc")
        try:
            import sys as _s
            if str(LAB) not in _s.path:
                _s.path.insert(0, str(LAB))
            from nhan import ngu_phap as NP
            nay = len(NP.doc_kho())
        except Exception as e:
            return False, "khong doc duoc kho: %s" % e
        if truoc is None:
            return True, "kho %d (chua co moc truoc de so)" % nay
        if nay > truoc:
            return True, "kho %d -> %d (+%d)" % (truoc, nay, nay - truoc)
        return False, "kho van %d - viec khong sinh ra co che nao" % nay
    return True, "khong khai chung cu"


def chay_mot(v: dict, in_ra=print) -> dict:
    """Chay MOT viec den khi xong/loi/qua han. Tra ve chinh `v` da cap nhat."""
    NHAT_KY.mkdir(parents=True, exist_ok=True)
    log = NHAT_KY / ("%s.log" % v["ma"])
    t0 = time.time()
    # Chup MOC TRUOC khi chay - khong co moc thi khong so duoc, va khong so
    # duoc thi `kho_tang` chi la mot truong trang tri.
    bc0 = v.get("bang_chung") or {}
    if bc0.get("kho_tang"):
        try:
            if str(LAB) not in sys.path:
                sys.path.insert(0, str(LAB))
            from nhan import ngu_phap as NP
            bc0["_kho_truoc"] = len(NP.doc_kho())
            v["bang_chung"] = bc0
        except Exception:
            pass
    in_ra("[%s] >>> %s  %s" % (_gio(), v["ma"], v["mo_ta"]))
    with open(log, "w", encoding="utf-8", errors="replace") as f:
        f.write("# %s\n# %s\n# %s\n\n" % (v["ma"], v["mo_ta"], v["lenh"]))
        f.flush()
        moi = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        p = subprocess.Popen(v["lenh"], shell=True, cwd=str(LAB), env=moi,
                             stdout=f, stderr=subprocess.STDOUT)
        han = v.get("han_giay", HAN_MAC_DINH)
        try:
            rc = p.wait(timeout=han)
            qua_han = False
        except subprocess.TimeoutExpired:
            _giet_cay(p)
            rc, qua_han = -9, True
    giay = round(time.time() - t0, 1)
    try:
        dong = log.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        dong = []
    v["trang_thai"] = "qua_han" if qua_han else ("xong" if rc == 0 else "loi")

    # MA THOAT KHONG PHAI CHUNG CU. Do 12/09/2026 (toi):
    #     xao_ma_llm     221s  rc=0  -> kho co che 2.554 khong doi mot dong
    #     xao_hoc_thuat  222s  rc=0  -> y het
    # Ca hai that bai vi dia day, nhung ham boc bat Exception roi tra ve rong,
    # va o day ta cham theo `rc == 0` nen ghi "xong". Hai viec chay het 443 giay
    # de sinh ra so 0, va so 0 do doc duoc y het mot ket luan that.
    #
    # Nen viec nao KHAI `bang_chung` thi phai chung minh: mot tep phai MOI HON
    # luc bat dau, hoac mot so trong so phai TANG. Khong chung minh duoc thi
    # trang thai la `khong_chung_cu` - KHONG phai `xong`, cung khong phai `loi`
    # ([[ket-luan-am-phai-phan-biet-CHUA-DO]]).
    bc = v.get("bang_chung")
    if bc and v["trang_thai"] == "xong":
        dat, vi_sao = _kiem_chung_cu(bc, t0)
        v["chung_cu"] = vi_sao
        if not dat:
            v["trang_thai"] = "khong_chung_cu"
            in_ra("  [chung cu] rc=0 NHUNG %s" % vi_sao)
    v["ma_thoat"] = rc
    v["giay"] = giay
    v["xong_luc"] = _gio()
    v["duoi_log"] = dong[-DUOI_GIU:]
    in_ra("[%s] <<< %s  %s  %.0fs  rc=%s"
          % (_gio(), v["ma"], v["trang_thai"].upper(), giay, rc))
    return v


def chay_het(in_ra=print) -> dict:
    """Chay het cac viec dang `cho`, TUAN TU. Nap lai so sau moi viec de co the
    THEM VIEC TU BEN NGOAI trong khi hang doi dang chay."""
    dem = {"xong": 0, "loi": 0, "qua_han": 0}
    while True:
        # DON MO COI TRUOC MOI VIEC.
        #
        # Do 12/09/2026: cac lan phong nen truoc do de lai 24 worker mo coi an
        # **19,5/20 loi** hon 20 phut. Viec tiep theo van chay - nhung chay tren
        # mot may da day, nen cham gap nhieu lan; va bo dieu toc cua qwen thi
        # tu choi phong han. Don o day re (mot lan quet tien trinh) va no chan
        # dung cai lam he tu te liet ma khong bao gi.
        try:
            from nhan import don_mo_coi as DMC
            k = DMC.quet()
            if k.get("mo_coi") and k.get("cpu_mo_coi", 0) >= 20:
                in_ra("  [don] %d tien trinh mo coi an %.0f%% CPU - dang don"
                      % (len(k["mo_coi"]), k["cpu_mo_coi"]))
                DMC.don(in_ra=in_ra)
        except Exception as e:
            in_ra("  [don] khong quet duoc mo coi: %s" % e)

        # KIEM DIA TRUOC MOI VIEC - cung ly do voi don mo coi o tren, nhung cai
        # nay am hon nhieu.
        #
        # Do 12/09/2026 (toi): o C con 177 MB. Ba viec lien tiep chay day du
        # thoi gian roi bao **XONG rc=0**, va kho co che khong nhich mot dong:
        #     xao_ma_llm     221s  rc=0   kho 2.554 -> 2.554
        #     xao_hoc_thuat  222s  rc=0   kho 2.554 -> 2.554
        # Loi that (`sqlite3.OperationalError: database or disk is full`) nam
        # sau hai lop: ham boc bat Exception roi tra ve rong, va hang doi cham
        # theo MA THOAT. Chay tiep trong tinh trang do la dot thoi gian de sinh
        # ra so 0 - va so 0 do doc duoc y het mot ket luan ("kho nay khong co
        # gi"), dung the benh `ket-luan-am-phai-phan-biet-CHUA-DO`.
        try:
            import shutil
            trong = shutil.disk_usage(str(LAB))[2] / (1024 ** 3)
            if trong < NGUONG_DIA_GB:
                in_ra("  [dia] CHI CON %.2f GB - DUNG HANG DOI." % trong)
                in_ra("  [dia] Chay tiep se cho cac viec 'xong' ma khong ghi")
                in_ra("  [dia] duoc gi. Don dia roi chay lai `python day_viec.py`.")
                dem["dung_vi_dia"] = round(trong, 2)
                break
        except Exception as e:
            in_ra("  [dia] khong do duoc dung luong: %s" % e)

        so = doc()
        v = next((x for x in so["viec"] if x["trang_thai"] == "cho"), None)
        if v is None:
            break
        v["trang_thai"] = "dang"
        v["bat_dau"] = _gio()
        ghi(so)
        chay_mot(v, in_ra=in_ra)
        so2 = doc()   # nap lai: co the co viec moi duoc them trong luc chay
        for i, x in enumerate(so2["viec"]):
            if x["ma"] == v["ma"]:
                so2["viec"][i] = v
                break
        ghi(so2)
        dem[v["trang_thai"]] = dem.get(v["trang_thai"], 0) + 1
    in_ra("\nHANG DOI RONG - xong %(xong)d - loi %(loi)d - qua han %(qua_han)d"
          % dem)
    return dem


def bang(in_ra=print) -> None:
    so = doc()
    if not so["viec"]:
        in_ra("hang doi rong")
        return
    dau = {"cho": "  ", "dang": ">>", "xong": "OK", "loi": "XX", "qua_han": "TT"}
    in_ra("%-3s %-14s %-8s %8s  %s" % ("", "MA", "TRANG THAI", "GIAY", "MO TA"))
    for v in so["viec"]:
        in_ra("%-3s %-14s %-8s %8s  %s"
              % (dau.get(v["trang_thai"], "??"), v["ma"], v["trang_thai"],
                 v.get("giay", "-"), v["mo_ta"][:60]))
    con = sum(1 for v in so["viec"] if v["trang_thai"] == "cho")
    in_ra("\n%d viec - %d cho - sua luc %s" % (len(so["viec"]), con, so["sua_luc"]))


def main(tv: list[str]) -> int:
    if not tv:
        chay_het()
        return 0
    c = tv[0]
    if c == "--xem":
        bang()
    elif c == "--them":
        if len(tv) < 4:
            print('--them MA "mo ta" "lenh" [han_giay]')
            return 2
        them(tv[1], tv[2], tv[3], int(tv[4]) if len(tv) > 4 else HAN_MAC_DINH)
        bang()
    elif c in ("--lam-lai", "--bo"):
        so = doc()
        if c == "--bo":
            so["viec"] = [v for v in so["viec"] if v["ma"] != tv[1]]
        else:
            for v in so["viec"]:
                if v["ma"] == tv[1]:
                    v["trang_thai"] = "cho"
        ghi(so)
        bang()
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
