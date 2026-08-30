# -*- coding: utf-8 -*-
"""bang_dieu_khien.py - MOT MAN HINH DUY NHAT de biet he dang the nao.

THIET_KE muc 9: man hinh phai doc xong trong 60 giay, va phai cho thay
MOT CAU MO TA CO CHE chu khong phai danh sach tham so.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))
from nhan import ket_qua_hoat_dong as KQHD, so as SO

KHOA = LAB / "dieu_phoi.lock"
CONTROL = LAB / "reports" / "control_plane.json"


def _doc_json(path: Path) -> dict:
    try:
        x = json.loads(path.read_text(encoding="utf-8-sig"))
        return x if isinstance(x, dict) else {}
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}


def _tre(luc: str) -> str:
    try:
        s = (datetime.now() - datetime.strptime(luc, "%Y-%m-%d %H:%M:%S")).total_seconds()
    except Exception:
        return "?"
    if s < 90:
        return f"{int(s)} giay truoc"
    if s < 5400:
        return f"{int(s//60)} phut truoc"
    return f"{s/3600:.1f} gio truoc"


def main() -> int:
    SO.khoi_tao()
    W = 78
    print("=" * W)
    print("  THE BRAIN - BANG DIEU KHIEN".center(W))
    print(f"  {SO.bay_gio()}".center(W))
    print("=" * W)

    cp = _doc_json(CONTROL)
    dang = KHOA.exists()
    if dang:
        try:
            tuoi = time.time() - float(cp.get("updated_epoch") or KHOA.stat().st_mtime)
        except (OSError, TypeError, ValueError):
            tuoi = float("inf")
        dang = bool(cp.get("live", True)) and tuoi < 45
        tuoi_text = f"{int(tuoi)}s" if tuoi != float("inf") else "?"
        print(f"\nDIEU PHOI : {'LIVE' if dang else 'STALE'}  "
              f"READY={'YES' if cp.get('ready') else 'NO'}  "
              f"HEALTH={str(cp.get('health', '?')).upper()}  (lease {tuoi_text})")
        cpu = cp.get("cpu") or {}
        workers = cp.get("workers") or {}
        print(f"  CPU      : {cpu.get('current_percent', '?')}% / hard cap "
              f"{cpu.get('hard_limit_percent', '?')}%  guard={cpu.get('guard', '?')}")
        print(f"  WORKERS  : {len(workers.get('running') or {})}/{workers.get('max', '?')} "
              f"running={list((workers.get('running') or {}).keys())} "
              f"pending={workers.get('pending') or []}")
        if cp.get("backpressure"):
            print(f"  BACKPRESS: {cp['backpressure']}")
    else:
        print("\nDIEU PHOI : KHONG CHAY   -> bat bang BAT_DAU.bat")

    print("\n--- 5 TRU " + "-" * (W - 10))
    print(f"  {'TRU':<11}{'LAN CUOI':<22}{'TRANG THAI':<16}CHI TIET")
    for n in SO.doc_nhip():
        if n["tru"] == "DIEU_PHOI":
            continue
        ct = (n["chi_tiet"] or "")[:34]
        print(f"  {n['tru']:<11}{_tre(n['luc']):<22}{n['trang_thai']:<16}{ct}")

    print("\n--- SAN LUONG " + "-" * (W - 14))
    tl = SO.mot("SELECT COUNT(*) n FROM tai_lieu")["n"]
    hang = {r["tu_khoa"]: r["n"] for r in SO.nhieu(
        "SELECT tu_khoa, COUNT(*) n FROM tai_lieu GROUP BY tu_khoa")}
    tk = SO.mot("SELECT COUNT(*) n FROM tu_khoa")["n"]
    print(f"  SEEKER   : {tl} tai lieu (A={hang.get('A',0)} B={hang.get('B',0)} "
          f"C={hang.get('C',0)}) | {tk} tu khoa")
    gt = {r["trang_thai"]: r["n"] for r in SO.nhieu(
        "SELECT trang_thai, COUNT(*) n FROM gia_thuyet GROUP BY trang_thai")}
    kq = SO.mot("SELECT COUNT(*) n FROM ket_qua")["n"]
    kq_hoat_dong = SO.mot(KQHD.truy_van("COUNT(*) n"))["n"]
    print(f"  QUANTLAB : {sum(gt.values())} gia thuyet {json.dumps(gt, ensure_ascii=False)} "
          f"| {kq} dong ket qua lich su, {kq_hoat_dong} dang hoat dong")
    vm = SO.mot("SELECT COUNT(DISTINCT seri) n FROM vi_mo")["n"]
    vmd = SO.mot("SELECT COUNT(*) n FROM vi_mo")["n"]
    print(f"  BANKER   : {vm} seri vi mo, {vmd} diem du lieu")
    v = SO.dem_viec()
    print(f"  VIEC     : {json.dumps(v, ensure_ascii=False)}")

    bc = LAB / "reports" / "banker_che_do.json"
    if bc.exists():
        try:
            cd = json.loads(bc.read_text(encoding="utf-8-sig"))
            print("\n--- BOI CANH VI MO " + "-" * (W - 19))
            for k, x in cd.get("che_do", {}).items():
                print(f"  {k:<24}{x['nhan']:<18}{x.get('gia_tri')}")
        except Exception:
            pass

    cl = LAB / "reports" / "so_chenh_lech_chi_phi.json"
    if cl.exists():
        try:
            b = json.loads(cl.read_text(encoding="utf-8-sig"))
            dk = [x for x in b if x["chenh_diem_pct_nam"] >= 1.0 and x["tin_cay"] == "CAO"]
            print(f"\n--- ALPHA PHEP TRU: chenh lech chi phi ({len(dk)} dang ke) "
                  + "-" * max(W - 52, 3))
            print("  (khong can backtest, khong can placebo, khong ton slot FDR)")
            for x in dk[:6]:
                print(f"  {x['phoi_nhiem']:<10} {x['kenh_re']:<8}{x['phi_re_pct_nam']:+7.2f}%"
                      f"  vs {x['kenh_dat']:<8}{x['phi_dat_pct_nam']:+7.2f}%"
                      f"   CHENH {x['chenh_diem_pct_nam']:+6.2f} diem %/nam")
        except Exception:
            pass

    # NGUONG PHAT HIEN phai nam NGAY TREN danh sach ung vien. Mot man hinh
    # bao "chua co ung vien" ma khong noi he nhin thay duoc tu muc nao thi
    # khong phan biet duoc "thi truong rong" voi "thuoc do qua tho".
    print("\n--- HE NHIN THAY DUOC TU DAU " + "-" * (W - 29))
    try:
        import json as _json
        moc = SO.mot("SELECT gia_tri, chi_tiet FROM chi_so_vh "
                     "WHERE ten='sharpe_nho_nhat_thay_duoc_tot_nhat' "
                     "ORDER BY id DESC LIMIT 1")
        if moc:
            hc = ((_json.loads(moc["chi_tiet"] or "{}").get("hai_chang") or {})
                  .get("chang") or {})
            for ten, v in hc.items():
                if v:
                    print(f"  {ten:<12} Sharpe >= {v['nguong']:<7}"
                          f"(do tren {v['tai_san']} {v['khung']})")
            print("  Co che nam GIUA hai nguong = PHAT HIEN duoc, CHUA CHUNG")
            print("  NHAN duoc. Do la hang doi bac cau, khong phai am tinh.")
        else:
            print("  Chua do. Doc ket luan am tinh ma khong co con so nay thi")
            print("  khong phan biet duoc thi truong rong voi thuoc do tho.")
    except Exception as e:
        print(f"  khong doc duoc: {type(e).__name__}")

    print("\n--- UNG VIEN DA QUA CONG " + "-" * (W - 25))
    ung = SO.nhieu(KQHD.truy_van(
        "k.gt_ma, k.verdict, k.alpha, k.t_alpha, k.p_placebo, g.co_che",
        dieu_kien_them="k.verdict IN ('PASS','UNG_VIEN')",
        sap_xep="k.id DESC",
        gioi_han=10,
    ))
    if not ung:
        print("  Chua co. (Day KHONG phai loi - 1.758 phep thu truoc day cung ra 0.)")
    for u in ung:
        print(f"  [{u['verdict']}] {u['gt_ma']}")
        print(f"      co che : {(u['co_che'] or '?')[:70]}")
        print(f"      alpha {u['alpha']}%/nam  t={u['t_alpha']}  placebo p={u['p_placebo']}")

    # Duong GOP tra loi mot cau KHAC voi duong don le ("co che nay co song
    # o lop thi truong nay khong"), nen bao rieng.
    gop = SO.nhieu(
        "SELECT gt_ma, verdict, alpha, t_alpha FROM ket_qua "
        "WHERE gt_ma LIKE 'GOP.%' AND superseded_by IS NULL "
        "ORDER BY id DESC LIMIT 6")
    if gop:
        print("\n--- DUONG GOP (mot co che / mot lop / MOT suat FDR) "
              + "-" * max(W - 51, 3))
        for g in gop:
            print(f"  [{g['verdict']}] {g['gt_ma']}")
            print(f"      alpha {g['alpha']}%/nam  t={g['t_alpha']}")

    mo = SO.van_de_mo()
    print(f"\n--- VAN DE DANG MO ({len(mo)}) " + "-" * (W - 24))
    for x in mo[:8]:
        print(f"  [{x['muc']:<4}] {x['ma']}")
        print(f"         {x['mo_ta'][:100]}")
    if not mo:
        print("  Khong co.")

    lanh, mt = SO.kiem_chuoi_hash()
    print(f"\nSO CAI    : {'LANH' if lanh else 'HONG'} - {mt}")
    print("=" * W)
    return 0


if __name__ == "__main__":
    sys.exit(main())
