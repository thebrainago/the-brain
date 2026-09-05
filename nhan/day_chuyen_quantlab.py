# -*- coding: utf-8 -*-
"""day_chuyen_quantlab.py - QUY TRINH CHUAN: ma nguon -> co che -> he thong.

Chu du an 05/09/2026: *"Sau khi seeker lay file ma ve can lam khau boc tach co
che. Co che can phai co buoc loc... Boc tach co che xong roi test tren cac symbol
khac nhau + thay doi tham so / input / cac co che quan li vi the... Quy trinh
cang ro rang va chuan hoa bao nhieu thi cang nhanh va hieu qua bay nhieu"*.

## HAI DUONG RA, KHONG DUOC TRON

Chu du an 05/09: *"Boc tach ra se gom chien luoc va cac he thong ho tro. Luc nay
chien luoc thi phai kiem dinh con tien ich thi can xem xem cai nao phu hop de
lay ve"*.

    CHIEN LUOC  (ho 1, sinh tin hieu vao)
      -> `SO.dang_ky_gia_thuyet` -> `quantlab.xac_nhan` -> cong that
      -> kiem dinh DOC LAP duoc vi no tu sinh vi the

    QUAN TRI VI THE (ho 2, khong sinh tin hieu)
      -> `_thu_quan_tri.py`: DAP len mot he NEN, do truoc/sau
      -> KHONG kiem dinh doc lap duoc. Gia tri cua no chi hien ra khi ghep.
      -> giu cai lam TANG LAI TUYET DOI tren CA HAI nua train+holdout

Nham duong la sai nghiem trong: cham mot co che quan tri bang `cong.py` se luon
truot (no khong co chuoi loi suat rieng), con cham mot chien luoc bang phep
"dap len he nen" se giau mat viec no co edge hay khong.

## NAM BUOC, CHAY NOI TIEP

    1 BOC     `quan_tri.boc_kho`      389 file ma  -> spec co che
    2 LOC     `quan_tri.loc`          giu cai DUNG LAI DUOC (ghep voi moi he)
    3 HO SO   `ho_so_symbol.quet`     194 symbol   -> tinh cach + bien do + chi phi
    4 GHEP    `chon_ung_vien` x kho gia tri that -> ma tran thu
    5 CHAM    `cham_diem.cham`        tien + rui ro, KHONG Sharpe/p-value

## VI SAO NOI TIEP CHU KHONG SONG SONG - do 05/09

    boc tach 389 file ma  : **1,01 giay**
    ho so 194 symbol      : 92 giay (1 luong)
    MOT backtest luoi M5  : 8,17 giay

Boc tach ton bang **0,12 lan mot backtest**. Khong co gi de song song hoa: hai
buoc dau cong lai chua toi 1,5 phut, con buoc 4 la 100% thoi gian. Chay noi tiep
roi de backtest chiem may.

**Chua nhan**: khi chay 16 tien trinh quet, `mt5.initialize()` het 60 giay va bao
IPC timeout - dung thu dang chan `PASS`. Bao hoa nhan co gia that. Mac dinh
`luong = so_nhan - 4`.

## NGUYEN TAC KHONG DUOC PHA

Buoc 5 tra loi "co dang chay khong", KHONG tra loi "co that khong". Cai nao
CHAY_DUOC van phai qua `nhan/cong.py` truoc khi goi la phat hien - `cham_diem`
danh dau bang `da_qua_cong_that`.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
BC = LAB / "reports"


def _luong(chua: int = 4) -> int:
    return max(1, (os.cpu_count() or 8) - chua)


def buoc1_boc(in_ra=print) -> list[dict]:
    from nhan import quan_tri as QT
    t = time.time()
    specs = QT.boc_kho(in_ra=lambda *a: None)
    in_ra("  1 BOC   : %d co che tu artifact ma (%.2fs)" % (len(specs), time.time() - t))
    return specs


def buoc2_loc(specs: list[dict], in_ra=print) -> tuple[list[dict], dict]:
    from nhan import quan_tri as QT
    giu, bo = QT.loc(specs, in_ra=lambda *a: None)
    in_ra("  2 LOC   : giu %d/%d (loai: %s)"
          % (len(giu), len(specs), ", ".join("%s %d" % kv for kv in bo.items())))
    (BC / "quan_tri_da_loc.json").write_text(
        json.dumps(giu, ensure_ascii=False, indent=1), encoding="utf-8")
    return giu, QT.kho_ghep(giu)


def buoc3_ho_so(khung: str = "D1", lam_moi: bool = False, in_ra=print) -> list[dict]:
    from nhan import ho_so_symbol as HS
    hs = [] if lam_moi else HS.doc()
    if not hs:
        t = time.time()
        hs = HS.quet(khung=khung, luong=_luong(), in_ra=lambda *a: None)
        in_ra("  3 HO SO : do moi %d symbol (%.0fs)" % (len(hs), time.time() - t))
    else:
        in_ra("  3 HO SO : dung ban da luu, %d symbol" % len(hs))
    return hs


def buoc4_ghep(hs: list[dict], kho_gt: dict, kieu: str = "hoi_quy",
               so_symbol: int = 8, in_ra=print) -> dict:
    """Chon ung vien + dung ma tran thu tu GIA TRI THAT cua cac EA."""
    from nhan import ho_so_symbol as HS
    uv = HS.chon_ung_vien(kieu=kieu, ho_so=hs, tran=so_symbol)
    in_ra("  4 GHEP  : %d symbol %s | kho gia tri that: %s"
          % (len(uv), kieu.upper(), ", ".join("%s(%d)" % (k, len(v))
                                              for k, v in kho_gt.items())))
    for h in uv:
        in_ra("            %-16s hurst %.3f  ATR %.2f%%  spread %s bps  %s"
              % (h["ma"], h.get("hurst") or 0, h.get("atr_pct_bar") or 0,
                 h.get("spread_bps"), h.get("chi_phi_do_tin")))
    return {"ung_vien": uv, "kho_gia_tri": kho_gt}


def chay(kieu: str = "hoi_quy", khung: str = "D1", lam_moi: bool = False,
         in_ra=print) -> dict:
    """Bon buoc dau. Buoc 5 (cham diem) goi rieng vi no can ket qua backtest."""
    in_ra("=" * 78)
    in_ra("DAY CHUYEN QUANTLAB - %s" % time.strftime("%Y-%m-%d %H:%M"))
    in_ra("=" * 78)
    t0 = time.time()
    specs = buoc1_boc(in_ra)
    giu, kho_gt = buoc2_loc(specs, in_ra)
    hs = buoc3_ho_so(khung=khung, lam_moi=lam_moi, in_ra=in_ra)
    g = buoc4_ghep(hs, kho_gt, kieu=kieu, in_ra=in_ra)
    in_ra("")
    in_ra("  xong 4 buoc trong %.0fs. Buoc 5 (backtest + cham diem) chay rieng"
          % (time.time() - t0))
    in_ra("  vi no chiem 100%% thoi gian: 1 cau hinh luoi M5 = 8,2 giay.")
    return {"co_che": giu, "kho_gia_tri": kho_gt, **g}
