# -*- coding: utf-8 -*-
"""
brain_vong_lap.py - BO DIEU PHOI CHAY LIEN TUC 24/7 cho The Brain
=====================================================================================
Muc dich: mot vong lap KHONG DUNG, tu bo sung viec, tu hoi phuc sau loi, chay het
tai san nay sang tai san khac, co che nay sang co che khac - va KHONG BAO GIO tu
dang ky bat cu thu gi vao so FDR.

BON SO TACH BIET (day la thiet ke cot loi, doc ky truoc khi sua):

  1. THU VIEN      `BRAIN_thu_vien.parquet`   MIEN PHI. Cong thuc, ham, mo hinh, ky
                                              thuat. Nap bao nhieu cung duoc. Khong
                                              ton mot slot FDR nao.
  2. CONG NGHE     `BRAIN_cong_nghe.parquet`  MIEN PHI. Mo hinh/thu vien/ky thuat moi.
                                              Sinh ra NANG LUC, khong sinh gia thuyet.
  3. SANG          `BRAIN_sang.parquet`       MIEN PHI - voi DIEU KIEN chi chay tren
                                              TAP SANG. Quet bao nhieu cung duoc.
                                              KET QUA O DAY KHONG BAO GIO DUOC BAO CAO
                                              LA EDGE. No chi de xep hang uu tien.
  4. SO DANG KY    `BRAIN_registry.parquet`   TON TIEN. Moi dong siet nguong FDR cho
                                              TAT CA nhung dong da co. Chi vao duoc
                                              bang tay, co `ly_do_kinh_te`, co nguoi ky.

VI SAO PHAI TACH: neu bot chay 24/7 duoc phep tu dang ky, sau 1 thang so co 50.000
phep thu va nguong FDR se sieu chat den muc khong y tuong nao qua noi, ke ca y tuong
dung. Bot cang cham chi cang tu giet minh. Tach so la cach duy nhat de vua chay 24/7
vua giu duoc suc manh thong ke.

TAP SANG vs TAP XAC NHAN:
  Sang 10.000 thu tren TAP SANG roi xac nhan 5 cai tren TAP XAC NHAN thi gia FDR la
  5, khong phai 10.005 - VOI DIEU KIEN tap xac nhan chua tung bi nhin trong luc sang.
  Vong lap nay CUONG CHE dieu do: `chay_sang()` khong duoc phep cham vao tap xac nhan.

AN TOAN PHAN CUNG (bai hoc 03-05/08/2026: chay tai nang keo dai lam chay bo mach):
  - Ha uu tien tien trinh xuong BELOW_NORMAL
  - Nghi giua moi don vi viec (`--nghi`)
  - Gioi han thoi gian moi don vi viec (`--gioi-han-viec`)
  - Ngan sach gio moi ngay (`--gio-moi-ngay`), het thi ngu den hom sau

CLI:
  python brain_vong_lap.py                      # chay mai, mac dinh an toan
  python brain_vong_lap.py --mot-vong           # chay 1 vong roi thoat (de test)
  python brain_vong_lap.py --gio-moi-ngay 8     # chi chay 8 tieng/ngay
  python brain_vong_lap.py --trang-thai         # xem tinh hinh, khong chay gi
  python brain_vong_lap.py --nap-viec           # sinh them viec vao hang doi roi thoat
"""
import argparse
import json
import os
import signal
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
REPORTS = HERE / "reports"
REPORTS.mkdir(exist_ok=True)

# --- bon so ---
SO_THU_VIEN = REPORTS / "BRAIN_thu_vien.parquet"
SO_CONG_NGHE = REPORTS / "BRAIN_cong_nghe.parquet"
SO_SANG = REPORTS / "BRAIN_sang.parquet"
SO_DANG_KY = REPORTS / "BRAIN_registry.parquet"       # CHI NGUOI KY

# --- dieu phoi ---
HANG_DOI = REPORTS / "BRAIN_hang_doi.parquet"
NHIP_TIM = REPORTS / "BRAIN_nhip_tim.json"            # de xem tu xa co con song khong
NHAT_KY = REPORTS / "BRAIN_nhat_ky.md"
BAO_CAO = REPORTS / "BRAIN_BAO_CAO.md"                # ghi de moi vong

DUNG = False          # co dung, bat boi SIGINT/SIGTERM


# ---------------------------------------------------------------------------
# Ha tang: dung dep, nhip tim, so sach
# ---------------------------------------------------------------------------

def _bat_tin_hieu_dung():
    def _xu_ly(signum, frame):
        global DUNG
        DUNG = True
        print("\n[dung] nhan tin hieu, se ket thuc sau khi xong viec dang chay...")
    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(s, _xu_ly)
        except (ValueError, OSError):
            pass


def ha_uu_tien():
    """VPS hay may de ban deu khong duoc de vong lap nay giat may."""
    try:
        import psutil
        p = psutil.Process(os.getpid())
        if os.name == "nt":
            p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        else:
            p.nice(10)
        return True
    except Exception:
        return False


def doc(duong_dan):
    if Path(duong_dan).exists():
        try:
            return pd.read_parquet(duong_dan)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def ghi(df, duong_dan):
    """Ghi an toan: ghi ra file tam roi doi ten, tranh hong so khi mat dien giua chung."""
    tam = Path(str(duong_dan) + ".tam")
    df.to_parquet(tam, index=False)
    os.replace(tam, duong_dan)


def them_vao_so(hang, duong_dan, khoa):
    """Them dong vao so, khu trung theo `khoa`. Tra ve so dong THAT SU moi."""
    moi = pd.DataFrame(hang if isinstance(hang, list) else [hang])
    if moi.empty:
        return 0
    cu = doc(duong_dan)
    truoc = len(cu)
    gop = pd.concat([cu, moi], ignore_index=True) if len(cu) else moi
    khoa_co = [k for k in khoa if k in gop.columns]
    if khoa_co:
        gop = gop.drop_duplicates(subset=khoa_co, keep="last").reset_index(drop=True)
    ghi(gop, duong_dan)
    return len(gop) - truoc


def dap_nhip(trang_thai, viec=None, them=None):
    """Ghi file nhip tim de tu xa biet bot con song va dang lam gi."""
    d = {"luc": datetime.now().isoformat(timespec="seconds"),
         "trang_thai": trang_thai, "pid": os.getpid(),
         "viec": viec or "", **(them or {})}
    try:
        NHIP_TIM.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def ghi_nhat_ky(dong):
    try:
        cu = NHAT_KY.read_text(encoding="utf-8") if NHAT_KY.exists() else "# THE BRAIN - nhat ky\n"
        NHAT_KY.write_text(cu + dong + "\n", encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Hang doi cong viec
# ---------------------------------------------------------------------------

COT_VIEC = ["id", "loai", "muc_tieu", "tham_so", "uu_tien", "trang_thai",
            "lan_chay", "luc_cuoi", "ket_qua", "ghi_chu"]

# Loai viec. Moi loai ghi vao MOT so, va KHONG loai nao ghi vao SO_DANG_KY.
LOAI = {
    "nguon":     "thu thap nguon moi            -> THU VIEN",
    "cong_nghe": "quet mo hinh/thu vien/ky thuat -> CONG NGHE",
    "boc_code":  "boc file thanh ham tin hieu    -> THU VIEN",
    "sang":      "do IC co che tren TAP SANG     -> SANG",
    "chi_phi":   "do swap/phi that theo san      -> THU VIEN",
    "doi_chieu": "so ban port voi .ex5 goc       -> THU VIEN",
}


def viec_moi(loai, muc_tieu, tham_so=None, uu_tien=50, ghi_chu=""):
    return {"id": f"{loai}:{muc_tieu}:{json.dumps(tham_so or {}, sort_keys=True)}",
            "loai": loai, "muc_tieu": muc_tieu,
            "tham_so": json.dumps(tham_so or {}, ensure_ascii=False),
            "uu_tien": uu_tien, "trang_thai": "cho", "lan_chay": 0,
            "luc_cuoi": "", "ket_qua": "", "ghi_chu": ghi_chu}


def nap_viec_mac_dinh():
    """Sinh hang doi ban dau. Uu tien theo 'ra tien nhanh nhat' chu khong theo 'thu vi nhat'.

    100 = ban do chi phi   : tien co that, khong can du doan, khong ton slot FDR
     90 = mo thi truong VN : hao sau nhat, khong ai lay duoc
     70 = nguon & cong nghe: mien phi, cang nhieu cang tot
     50 = sang co che      : mien phi nhung phai giu ky luat tap sang
     30 = boc code         : co hoc, chay khi ranh
    """
    v = []

    # --- 100: ban do chi phi (cua 2) ---
    for san in ["XM", "Exness", "Ultima", "FXCE"]:
        v.append(viec_moi("chi_phi", san, {"do": "swap_dem"}, 100,
                          "cung phoi nhiem, san nao re nhat"))
    v.append(viec_moi("chi_phi", "cash_vs_futures", {"do": "so_sanh_lop"}, 100,
                      "XM futures CFD swap=0 - da phat hien, chua tieu"))

    # --- 90: mo thi truong Viet Nam (cua 1) ---
    for nguon in ["SSI", "VNDirect", "TCBS"]:
        v.append(viec_moi("nguon", f"api_{nguon}", {"loai": "kh mo thi truong"}, 90,
                          "API cong khai - keo VN30, VN30F1M, room ngoai, du no margin"))
    for cc in ["room_ngoai", "giai_chap_margin", "vn30_rebalance", "phien_atc"]:
        v.append(viec_moi("sang", f"vn_{cc}", {"tap": "sang", "thi_truong": "VN"}, 90,
                          "dong tien BI EP - cung ho co che voi IBS"))

    # --- 70: nguon & cong nghe ---
    for kho in ["huggingface_models", "huggingface_datasets", "huggingface_papers"]:
        v.append(viec_moi("cong_nghe", kho, {}, 70, "noi cong nghe moi xuat hien truoc GitHub"))
    v.append(viec_moi("cong_nghe", "github_trending", {"tu_khoa": "time series forecasting"}, 70))
    v.append(viec_moi("nguon", "hop_thu_imap", {}, 75,
                      "Facebook/Substack/YouTube tu DAY vao hop thu - khong scrape gi ca"))
    v.append(viec_moi("nguon", "youtube_phu_de", {}, 65,
                      "tai lieu that cua bot nam trong clip, khong nam trong .rar"))
    for nen in ["darwinex", "myfxbook"]:
        v.append(viec_moi("nguon", f"track_record_{nen}", {}, 70,
                          "nguoi thang DAI khac nguoi thang MAY o cho nao"))

    # --- 50: sang co che ---
    v.append(viec_moi("sang", "elliott_cong_repaint", {"tap": "sang"}, 60,
                      "CHAY TRUOC MOI THU VE ELLIOTT - re nhat, dut diem nhat"))
    for kd in ["luan_phien", "song3_khong_ngan_nhat", "bat_doi_xung_5_3"]:
        v.append(viec_moi("sang", f"elliott_{kd}", {"tap": "sang"}, 45,
                          "khang dinh QUAN HE - vung chua ai quet"))

    # --- 30: boc code ---
    v.append(viec_moi("boc_code", "quet_nap_tay", {}, 30))

    n = them_vao_so(v, HANG_DOI, ["id"])
    print(f"  nap {n} viec moi (hang doi hien co {len(doc(HANG_DOI))})")
    return n


def lay_viec():
    """Lay viec uu tien cao nhat dang cho. Viec loi duoc thu lai toi da 3 lan."""
    hd = doc(HANG_DOI)
    if hd.empty:
        return None, hd
    san = hd[(hd["trang_thai"] == "cho") |
             ((hd["trang_thai"] == "loi") & (hd["lan_chay"] < 3))]
    if san.empty:
        return None, hd
    # uu tien cao truoc; cung uu tien thi cai lau chua chay truoc
    san = san.sort_values(["uu_tien", "lan_chay", "luc_cuoi"],
                          ascending=[False, True, True])
    return san.iloc[0].to_dict(), hd


def cap_nhat_viec(hd, viec_id, **thay_doi):
    m = hd["id"] == viec_id
    for k, giatri in thay_doi.items():
        hd.loc[m, k] = giatri
    ghi(hd, HANG_DOI)


# ---------------------------------------------------------------------------
# Cac bo thuc thi. Moi cai NHAN mot viec, TRA ve (so_dong_ghi, tom_tat).
# Chua cai nao duoc phep cham vao SO_DANG_KY.
# ---------------------------------------------------------------------------

# Dau hieu "viec nay chua co bo thuc thi". Viec mang dau hieu nay se bi CHUYEN SANG
# trang thai `cho_trien_khai` va KHONG duoc lay lai trong ngay - neu khong no se quay
# vong mai o dau hang doi (uu tien cao) va chan het viec chay duoc o phia sau.
# Moi lan sang ngay moi, chung duoc mo lai mot lan de thu (biet dau module da duoc viet).
CHUA_CO = "CHUA_TRIEN_KHAI: "


def _thu_module(ten):
    """Nap module cua du an neu co. Khong co thi bao ro, khong lam sap vong lap."""
    try:
        return __import__(ten)
    except Exception:
        return None


def chay_nguon(viec):
    """Thu thap nguon -> THU VIEN. Uu tien dung brain_sources.py da co."""
    mt = viec["muc_tieu"]

    if mt == "hop_thu_imap":
        m = _thu_module("brain_nguon_moi")
        if m is None or not hasattr(m, "doc_hop_thu"):
            return 0, CHUA_CO + "brain_nguon_moi.doc_hop_thu - xem huong dan trong file do"
        hang = m.doc_hop_thu()
        return them_vao_so(hang, SO_THU_VIEN, ["nguon", "khoa"]), f"{len(hang)} thu"

    if mt.startswith("track_record_") or mt == "youtube_phu_de" or mt.startswith("api_"):
        m = _thu_module("brain_nguon_moi")
        ten_ham = {"youtube_phu_de": "youtube_phu_de"}.get(mt, mt)
        if m is None or not hasattr(m, ten_ham):
            return 0, CHUA_CO + f"{ten_ham}() trong brain_nguon_moi.py"
        hang = getattr(m, ten_ham)()
        return them_vao_so(hang, SO_THU_VIEN, ["nguon", "khoa"]), f"{len(hang)} muc"

    return 0, CHUA_CO + "muc tieu chua co bo thuc thi"


def chay_cong_nghe(viec):
    """Quet cong nghe -> so CONG NGHE. Sinh NANG LUC, khong sinh gia thuyet."""
    m = _thu_module("brain_nguon_moi")
    if m is None or not hasattr(m, "quet_cong_nghe"):
        return 0, CHUA_CO + "brain_nguon_moi.quet_cong_nghe"
    hang = m.quet_cong_nghe(viec["muc_tieu"], json.loads(viec["tham_so"] or "{}"))
    return them_vao_so(hang, SO_CONG_NGHE, ["nguon", "khoa"]), f"{len(hang)} muc"


def chay_chi_phi(viec):
    """Do chi phi that theo san -> THU VIEN. Day la PHEP TRU, khong phai gia thuyet,
    nen khong ton mot slot FDR nao ma van ra tien."""
    m = _thu_module("brain_chi_phi")
    if m is None or not hasattr(m, "do_chi_phi"):
        return 0, (CHUA_CO + "brain_chi_phi.do_chi_phi - can MetaTrader5 + tai khoan. "
                   "Doc swap tu symbol_info(), doi chieu bar H1 co cot spread that")
    hang = m.do_chi_phi(viec["muc_tieu"], json.loads(viec["tham_so"] or "{}"))
    return them_vao_so(hang, SO_THU_VIEN, ["nguon", "khoa"]), f"{len(hang)} phep do"


def chay_boc_code(viec):
    """Boc file thanh ham tin hieu -> THU VIEN. Dung lai brain_nap_kho.py da co."""
    import subprocess
    try:
        r = subprocess.run([sys.executable, "brain_nap_kho.py"], cwd=str(HERE),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=900)
        dong = [d for d in (r.stdout or "").splitlines() if "ham rut duoc" in d or "UNG" in d]
        return len(dong), " | ".join(dong[:3]) or "chay xong"
    except subprocess.TimeoutExpired:
        return 0, "het gio"


def chay_sang(viec):
    """Do co che tren TAP SANG -> so SANG.

    CUONG CHE KY LUAT: ham nay KHONG duoc cham vao tap xac nhan. Ket qua o day
    KHONG BAO GIO duoc bao cao la edge - no chi de xep hang uu tien cho buoc
    xac nhan, ma buoc xac nhan thi PHAI co nguoi ky.
    """
    ts = json.loads(viec["tham_so"] or "{}")
    if ts.get("tap") != "sang":
        return 0, "TU CHOI: viec sang phai co tham_so tap='sang'"

    m = _thu_module("brain_co_che")
    if m is None or not hasattr(m, "do_ic"):
        return 0, (CHUA_CO + f"brain_co_che.do_ic('{viec['muc_tieu']}') - "
                   "moi co che = 1 ham, tra ve dict(ic, n, placebo_so_bo)")
    kq = m.do_ic(viec["muc_tieu"], ts)
    if not kq:
        return 0, "khong tra ve gi"
    kq = {**kq, "co_che": viec["muc_tieu"], "tap": "sang",
          "ngay": datetime.now().date().isoformat(),
          "CANH_BAO": "ket qua TAP SANG - khong phai edge, chua tinh FDR"}
    return (them_vao_so(kq, SO_SANG, ["co_che", "tap"]),
            f"IC {kq.get('ic', float('nan')):+.4f} n={kq.get('n', 0)}")


def chay_doi_chieu(viec):
    """So ban port Python voi .ex5 goc trong MT5 tester.
    Quy tac 18 cua du an: co .ex5 chay duoc thi DUNG dich nguoc tham so."""
    m = _thu_module("brain_doi_chieu")
    if m is None or not hasattr(m, "doi_chieu"):
        return 0, (CHUA_CO + "brain_doi_chieu.doi_chieu - chay .ex5 trong tester, xuat log, "
                   "so THOI DIEM VAO LENH voi ban Python. Lech >5% = boc sai.")
    kq = m.doi_chieu(viec["muc_tieu"], json.loads(viec["tham_so"] or "{}"))
    return them_vao_so(kq, SO_THU_VIEN, ["nguon", "khoa"]), str(kq)[:120]


BO_THUC_THI = {
    "nguon": chay_nguon,
    "cong_nghe": chay_cong_nghe,
    "chi_phi": chay_chi_phi,
    "boc_code": chay_boc_code,
    "sang": chay_sang,
    "doi_chieu": chay_doi_chieu,
}


# ---------------------------------------------------------------------------
# Bao cao
# ---------------------------------------------------------------------------

def viet_bao_cao():
    """Ghi de mot file duy nhat moi vong (dung quy tac 'bao cao gon mot file')."""
    hd, tv, cn, sg = doc(HANG_DOI), doc(SO_THU_VIEN), doc(SO_CONG_NGHE), doc(SO_SANG)
    dk = doc(SO_DANG_KY)

    md = [f"# THE BRAIN - bao cao vong lap",
          f"", f"*Cap nhat {datetime.now():%Y-%m-%d %H:%M}*", "",
          "## Bon so",  "",
          "| So | Vai tro | So dong | Ton FDR |",
          "|---|---|---|---|",
          f"| THU VIEN | cong thuc, ham, ky thuat | {len(tv)} | khong |",
          f"| CONG NGHE | mo hinh/thu vien moi | {len(cn)} | khong |",
          f"| SANG | IC co che tren tap sang | {len(sg)} | khong |",
          f"| **SO DANG KY** | **gia thuyet da ky** | **{len(dk)}** | **CO** |", "",
          "> So dang ky chi tang khi NGUOI ky. Vong lap 24/7 khong bao gio tu them vao day.",
          ""]

    if len(hd):
        md += ["## Hang doi", "", "| trang thai | so viec |", "|---|---|"]
        for k, v in hd["trang_thai"].value_counts().items():
            md.append(f"| {k} | {v} |")
        md += ["", "### 10 viec ke tiep", "",
               "| uu tien | loai | muc tieu | lan chay | ket qua gan nhat |", "|---|---|---|---|---|"]
        cho = hd[hd["trang_thai"].isin(["cho", "loi"])].sort_values(
            ["uu_tien", "lan_chay"], ascending=[False, True]).head(10)
        for _, r in cho.iterrows():
            md.append(f"| {r['uu_tien']} | {r['loai']} | {r['muc_tieu']} | "
                      f"{r['lan_chay']} | {str(r['ket_qua'])[:60]} |")
        md.append("")

    if len(sg):
        md += ["## Ket qua TAP SANG", "",
               "> **Day khong phai edge.** Tap sang chi de xep hang uu tien. Muon goi la edge "
               "thi phai chay lai tren TAP XAC NHAN, va lan do TON ngan sach FDR.", "",
               "| co che | IC | n | ngay |", "|---|---|---|---|"]
        for _, r in sg.sort_values("ic", ascending=False, key=abs).head(20).iterrows():
            md.append(f"| {r.get('co_che','')} | {r.get('ic', float('nan')):+.4f} | "
                      f"{r.get('n', 0)} | {r.get('ngay','')} |")
        md.append("")

    if len(cn):
        md += ["## Cong nghe moi (nang luc, khong phai gia thuyet)", "",
               "| nguon | ten | ngay |", "|---|---|---|"]
        for _, r in cn.tail(20).iloc[::-1].iterrows():
            md.append(f"| {r.get('nguon','')} | {str(r.get('ten',''))[:70]} | {r.get('ngay','')} |")
        md.append("")

    try:
        BAO_CAO.write_text("\n".join(md), encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Vong lap chinh
# ---------------------------------------------------------------------------

def mot_don_vi_viec(gioi_han_giay):
    """Chay dung 1 viec. Loi thi ghi nhan va di tiep - khong bao gio lam sap vong lap."""
    viec, hd = lay_viec()
    if viec is None:
        return False, "hang doi rong"

    vid = viec["id"]
    cap_nhat_viec(hd, vid, trang_thai="dang_chay",
                  luc_cuoi=datetime.now().isoformat(timespec="seconds"))
    dap_nhip("dang_chay", vid)
    t0 = time.time()

    try:
        fn = BO_THUC_THI.get(viec["loai"])
        if fn is None:
            raise ValueError(f"khong co bo thuc thi cho loai '{viec['loai']}'")
        so_dong, tom_tat = fn(viec)
        # Viec chua co bo thuc thi -> `cho_trien_khai`, KHONG lay lai trong ngay.
        # Neu de nguyen "cho" thi no quay vong mai o dau hang doi va chan het viec
        # chay duoc phia sau (da mac dung loi nay khi chay thu lan dau).
        chua_lam_duoc = str(tom_tat).startswith(CHUA_CO)
        hd = doc(HANG_DOI)
        cap_nhat_viec(hd, vid,
                      trang_thai="cho_trien_khai" if chua_lam_duoc else "xong",
                      lan_chay=int(viec["lan_chay"]) + 1,
                      ket_qua=f"{so_dong} dong | {tom_tat}"[:200],
                      luc_cuoi=datetime.now().isoformat(timespec="seconds"))
        print(f"  [{viec['loai']:10}] {viec['muc_tieu']:28} {time.time()-t0:5.0f}s  "
              f"{so_dong:>4} dong | {str(tom_tat)[:70]}")
        return True, tom_tat

    except Exception as e:
        loi = f"{type(e).__name__}: {str(e)[:150]}"
        hd = doc(HANG_DOI)
        cap_nhat_viec(hd, vid, trang_thai="loi",
                      lan_chay=int(viec["lan_chay"]) + 1, ket_qua=loi,
                      luc_cuoi=datetime.now().isoformat(timespec="seconds"))
        print(f"  [{viec['loai']:10}] {viec['muc_tieu']:28} LOI: {loi}")
        ghi_nhat_ky(f"- {datetime.now():%Y-%m-%d %H:%M} LOI `{vid}`: {loi}")
        return True, loi


def vong_lap(args):
    _bat_tin_hieu_dung()
    co_uu_tien = ha_uu_tien()
    print(f"=== THE BRAIN - vong lap 24/7 ===")
    print(f"  ha uu tien tien trinh: {'co' if co_uu_tien else 'KHONG (thieu psutil)'}")
    print(f"  nghi giua viec: {args.nghi}s | gioi han moi viec: {args.gioi_han_viec}s")
    print(f"  ngan sach: {args.gio_moi_ngay}h/ngay\n")

    if doc(HANG_DOI).empty:
        print("hang doi rong - nap viec mac dinh:")
        nap_viec_mac_dinh()

    ngay = datetime.now().date()
    da_chay = 0.0
    vong = 0

    while not DUNG:
        # doi ngay -> nap lai ngan sach va bo sung viec dinh ky
        if datetime.now().date() != ngay:
            ngay, da_chay = datetime.now().date(), 0.0
            nap_viec_mac_dinh()
            # Mo lai viec `cho_trien_khai` mot lan moi ngay - biet dau module da duoc viet
            hd = doc(HANG_DOI)
            if len(hd):
                n = int((hd["trang_thai"] == "cho_trien_khai").sum())
                if n:
                    hd.loc[hd["trang_thai"] == "cho_trien_khai", "trang_thai"] = "cho"
                    ghi(hd, HANG_DOI)
                    print(f"  mo lai {n} viec cho_trien_khai de thu lai")
            ghi_nhat_ky(f"\n## {ngay} - nap lai ngan sach")

        if da_chay >= args.gio_moi_ngay * 3600:
            mai = datetime.combine(ngay + timedelta(days=1), datetime.min.time())
            cho = max(60, (mai - datetime.now()).total_seconds())
            print(f"  het ngan sach {args.gio_moi_ngay}h - ngu {cho/3600:.1f}h den mai")
            dap_nhip("ngu_het_ngan_sach", them={"day_den": mai.isoformat()})
            for _ in range(int(cho // 30)):
                if DUNG:
                    break
                time.sleep(30)
            continue

        t0 = time.time()
        con_viec, _ = mot_don_vi_viec(args.gioi_han_viec)
        da_chay += time.time() - t0
        vong += 1

        if not con_viec:
            print("  hang doi rong - nap them viec")
            if nap_viec_mac_dinh() == 0:
                print(f"  khong con viec moi - nghi {args.nghi_rong}s")
                dap_nhip("cho_viec")
                for _ in range(int(args.nghi_rong // 10)):
                    if DUNG:
                        break
                    time.sleep(10)
                continue

        if vong % 5 == 0:
            viet_bao_cao()

        if args.mot_vong:
            break

        dap_nhip("nghi")
        for _ in range(int(max(1, args.nghi) // 1)):
            if DUNG:
                break
            time.sleep(1)

    viet_bao_cao()
    dap_nhip("da_dung")
    print(f"\nDa dung sau {vong} vong. Bao cao: {BAO_CAO}")


def in_trang_thai():
    hd = doc(HANG_DOI)
    print("=== TRANG THAI THE BRAIN ===\n")
    if NHIP_TIM.exists():
        d = json.loads(NHIP_TIM.read_text(encoding="utf-8"))
        tre = (datetime.now() - datetime.fromisoformat(d["luc"])).total_seconds()
        print(f"  nhip tim: {d['luc']} ({tre/60:.0f} phut truoc) - {d['trang_thai']}")
        print(f"  {'CON SONG' if tre < 900 else '!!! CO VE DA CHET (>15 phut khong dap)'}\n")
    for ten, dd in [("THU VIEN", SO_THU_VIEN), ("CONG NGHE", SO_CONG_NGHE),
                    ("SANG", SO_SANG), ("SO DANG KY (ton FDR)", SO_DANG_KY)]:
        print(f"  {ten:24} {len(doc(dd)):>6} dong")
    if len(hd):
        print()
        for k, v in hd["trang_thai"].value_counts().items():
            print(f"  hang doi [{k:10}] {v:>4}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nghi", type=float, default=5, help="giay nghi giua moi viec")
    ap.add_argument("--nghi-rong", type=float, default=600, help="giay nghi khi het viec")
    ap.add_argument("--gioi-han-viec", type=int, default=900, help="giay toi da moi viec")
    ap.add_argument("--gio-moi-ngay", type=float, default=24, help="ngan sach gio/ngay")
    ap.add_argument("--mot-vong", action="store_true", help="chay 1 viec roi thoat")
    ap.add_argument("--nap-viec", action="store_true", help="chi nap hang doi roi thoat")
    ap.add_argument("--trang-thai", action="store_true", help="xem tinh hinh, khong chay")
    args = ap.parse_args()

    if args.trang_thai:
        return in_trang_thai()
    if args.nap_viec:
        return nap_viec_mac_dinh()
    vong_lap(args)


if __name__ == "__main__":
    main()
