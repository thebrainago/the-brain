# -*- coding: utf-8 -*-
"""_qwen_het_cong_suat.py - vong lap DOC -> BOC chay den khi het ton kho.

Do 08/09/2026: 6.970/7.297 tai lieu chua khai thac, nhung `boc_llm.ung_vien`
chi tra 78 van ban - vi phai DOC TOAN VAN truoc khi co dau hieu chua luat. Nen
mot lan `doc` roi mot lan `boc` khong vet duoc kho; phai lap.

Song song: da do 24/24 loi goi qwen dong thoi deu OK (AI Box, 08/09), nen
`luong` o day dat 20 chu khong phai 6 nhu mac dinh.

PHAN VAI: qwen lam KHOI LUONG (doc + boc). Cong / con so / dien giai ket qua
KHONG giao cho may - da do `co_che` LLM dien 48, tham dinh bac 41, rong cuu 3
[[co-che-khong-dien-duoc-bang-may]]. `them_co_che` van chay spec tren du lieu
that va tu choi cai khong chay duoc, nen loi cua qwen o khau boc bi MAY bat.

Chay: python _qwen_het_cong_suat.py [so_vong] [doc_moi_vong] [boc_moi_vong]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

LUONG_DOC = 16      # tai HTTP, khong phai qwen
LUONG_BOC = 20      # qwen - da do 24 dong thoi van OK


def main() -> int:
    so_vong = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    so_doc = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    so_boc = int(sys.argv[3]) if len(sys.argv) > 3 else 250

    from nhan import boc_llm as BL
    from nhan import doc_song_song as DS
    from nhan import loc_co_che as LCC
    from nhan import ngu_phap as NP
    from nhan import so as SO

    df_kiem = LCC.df_kiem_chuan()
    if df_kiem is None:
        print("!! khong nap duoc chuoi kiem - dung, vi ghi kho ma khong chay thu "
              "la cach 54 spec hong da lot vao kho hom 05/09")
        return 1

    t0 = time.time()
    cc0 = len(NP.doc_kho())
    n = lambda s: (SO.mot(s) or {}).get("n")
    print("=== QWEN HET CONG SUAT (doc %d x boc %d) x %d vong ==="
          % (so_doc, so_boc, so_vong))
    print("co che truoc: %d | tai lieu chua khai thac: %s\n"
          % (cc0, n("SELECT COUNT(*) n FROM tai_lieu WHERE COALESCE(da_khai_thac,0)=0")),
          flush=True)

    for v in range(1, so_vong + 1):
        tv = time.time()
        truoc = len(NP.doc_kho())
        d = DS.doc(gioi_han=so_doc, luong=LUONG_DOC, in_ra=lambda *a: None)
        uv = len(BL.ung_vien(so_boc)) + len(BL.ung_vien_artifact(so_boc))
        b = BL.boc(gioi_han=so_boc, luong=LUONG_BOC, ghi_kho=True,
                   df_kiem=df_kiem, in_ra=lambda *a: None)
        sau = len(NP.doc_kho())
        print("vong %2d | doc %3s/%-3s | ung vien %3d | co che %d -> %d (+%d) | %.0fs"
              % (v, d.get("doc_duoc"), d.get("tai_lieu"), uv, truoc, sau,
                 sau - truoc, time.time() - tv), flush=True)
        if b:
            print("         boc: %s" % ({k: val for k, val in b.items()
                                         if k not in ("chi_tiet",)},), flush=True)
        # "Het ton kho" phai DO, khong duoc suy tu "khong con ung vien".
        #
        # Vong 08/09 dau tien da bao "het ton kho" khi kho con 4.560 tai lieu
        # chua doc: 406 URL chet cua TradingView (`/script/PUB;<id>`) xep truoc
        # trong hang doi va khong bao gio bi danh dau, nen `doc_duoc` = 0 mai
        # va `ung_vien` tut ve 0 theo. Doc y het mot ket qua am
        # [[ket-luan-am-phai-phan-biet-chua-do]].
        ton = n("SELECT COUNT(*) n FROM tai_lieu t "
                "LEFT JOIN noi_dung nd ON nd.tai_lieu_id=t.id "
                "WHERE nd.id IS NULL AND t.url IS NOT NULL AND t.url!=''")
        if not uv and not d.get("doc_duoc"):
            if ton:
                print("  !! ung vien 0 NHUNG kho con %s tai lieu chua doc - "
                      "day la KHAU DOC HONG, khong phai het ton kho. Dung de "
                      "nguoi xem." % ton)
            else:
                print("  -> het ton kho THAT (da do: 0 tai lieu chua doc)")
            break

    cc1 = len(NP.doc_kho())
    print("\n=== XONG %.0fs | co che %d -> %d (+%d) ==="
          % (time.time() - t0, cc0, cc1, cc1 - cc0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
