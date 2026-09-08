# -*- coding: utf-8 -*-
"""dieu_toc.py - GIU MAY O ~85% CPU, do bang phep do chu khong bang gia dinh.

## Vi sao khong dat cung "8 tien trinh"

Da do tren dung may nay hai bai khac han nhau:

  - quet be mat pheu D1 (mot o ~128 KB, nam gon trong cache):
        1 tien trinh 18,6 o/giay · 8 tien trinh 70,6 (3,8 lan) · 16 tien trinh 79,0
  - bai mang lon:
        1 luong 8,9 GB/s · 20 luong 9,4 GB/s  -> song song hoa KHONG an gi

Cung mot may, hai ket luan nguoc nhau. Nen so tien trinh dung KHONG suy ra duoc
tu so nhan; no phai DO. Bo dieu toc nay do CPU that moi 5 giay va cong/tru slot
theo phep do (AIMD), nen bai nao no cung tu tim ra muc cua bai do.

## Ba thu no phai chong

1. **Vot luc vua phong.** CPU mat vai giay moi leo len. Neu chi nhin phep do thi
   trong 5 giay dau no phong het slot roi may nghen. -> moi viec vua phong duoc
   GIU VON `nang` cua no trong `giu_von_giay`; het han thi phep do thay the.
2. **Tien trinh nguoi khac.** MT5 tester, Chrome, trinh nen. Muc tieu 85% la cua
   CA MAY, nen khi MT5 an 60% thi lan CPU cua ta tu co lai. Do la dung.
3. **Cuop may cua nguoi dung.** Moi tien trinh con chay o BELOW_NORMAL, va co
   `tran_lan` de mot lan don khong nuot het.
"""
from __future__ import annotations

import time
from collections import deque

import psutil

from . import cau_hinh as CH


class DieuToc:
    """Cap phat 'loi' cho cac lan, giu tong CPU may quanh muc tieu."""

    def __init__(self, c: dict | None = None) -> None:
        self.c = c or CH.nap()
        self.so_loi = psutil.cpu_count() or 1
        self.muc_tieu = float(self.c["muc_tieu_cpu"])
        self.mau = deque(maxlen=int(self.c["cua_so_do"]))
        self.lan_do = 0.0
        #: {ma_viec: (lan, nang, luc_phong)} - von da cap, chua kip vao phep do
        self.von = {}
        #: {lan: so loi DO DUOC} - hoc dan tu chinh cac lan chay truoc
        self.do_duoc = dict(self.c.get("nang_do_duoc") or {})
        psutil.cpu_percent(interval=None)   # moi lan goi dau tra 0, bo di

    # ------------------------------------------------------------- phep do
    def do(self) -> float:
        """Tra % CPU trung binh truot cua CA MAY."""
        gio = time.time()
        if gio - self.lan_do >= float(self.c["chu_ky_do_giay"]):
            self.mau.append(psutil.cpu_percent(interval=None))
            self.lan_do = gio
        if not self.mau:
            return 0.0
        return sum(self.mau) / len(self.mau)

    def loi_dang_dung(self) -> float:
        """So loi dang bi chiem - lay MAX cua (phep do, von vua cap).

        Lay MAX chu khong lay tong: sau `giu_von_giay` thi viec da vao phep do
        roi, cong them nua la dem hai lan.
        """
        do_duoc = self.do() / 100.0 * self.so_loi
        gio = time.time()
        han = float(self.c["giu_von_giay"])
        von_moi = sum(n for _, n, t in self.von.values() if gio - t < han)
        return max(do_duoc, von_moi)

    def con_trong(self) -> float:
        """So loi con duoc phep cap phat."""
        return self.so_loi * self.muc_tieu / 100.0 - self.loi_dang_dung()

    # ------------------------------------------------------------- cap phat
    def dem_lan(self, lan: str) -> int:
        return sum(1 for l, _, _ in self.von.values() if l == lan)

    def cho_phep(self, lan: str) -> tuple[bool, str]:
        """Co duoc phong them mot viec cua `lan` khong?"""
        tran = int(self.c["tran_lan"].get(lan, 4))
        dang = self.dem_lan(lan)
        if dang >= tran:
            return False, "lan %s da day (%d/%d)" % (lan, dang, tran)
        nang = self.nang(lan)
        con = self.con_trong()
        # MOI lan deu di qua ngan sach, KHONG co lan nao duoc mien.
        #
        # Truoc 20:30 08/09 o day mien cho LLM/MANG/NHE, voi ly do "chung cho
        # mang chu khong an CPU". Do la mot GIA DINH CHUA DO. Do that luc chu du
        # an dang choi game: `TT_boc` an **768% = 7,7 loi** (16 luong doc + 20
        # luong boc, va boc tach JSON/HTML la viec CPU chu khong phai cho mang),
        # trong khi bang `nang_lan` cua toi khai 1,2. Che do nghi ha muc tieu
        # xuong 35% ma may van 97%, vi hai thu an nhieu nhat deu duoc mien.
        if con < nang:
            return False, "con %.1f loi, viec can %.1f (CPU %.0f%%/%.0f%%)" % (
                con, nang, self.do(), self.muc_tieu)
        return True, "ok (con %.1f loi)" % con

    # --------------------------------------------------------------- hoc nang
    def nang(self, lan: str) -> float:
        """Suat cua mot viec lan nay: lay MAX cua bang khai va cai DO DUOC.

        Lay max chu khong lay cai do duoc: bang khai la chan duoi cho lan chua
        chay bao gio, con phep do la su that cho lan da chay.
        """
        return max(float(self.c["nang_lan"].get(lan, 1.0)),
                   float(self.do_duoc.get(lan, 0.0)))

    def hoc(self, lan: str, loi: float) -> None:
        """Ghi lai suat CPU that cua mot lan (trung binh truot, nghieng ve cao).

        Nghieng ve cao (0,3 khi tang / 0,05 khi giam) vi hau qua hai chieu khong
        can nhau: uoc thap thi may nghen va chu du an phai di giet tay; uoc cao
        thi chi cham hon mot chut.
        """
        cu = float(self.do_duoc.get(lan, 0.0))
        a = 0.3 if loi > cu else 0.05
        self.do_duoc[lan] = round(cu + a * (loi - cu), 2)

    def giu(self, ma: str, lan: str) -> None:
        self.von[ma] = (lan, self.nang(lan), time.time())

    def nha(self, ma: str) -> None:
        self.von.pop(ma, None)

    # ------------------------------------------------------------- bao cao
    def dong_trang_thai(self) -> str:
        return "CPU %4.0f%% / muc tieu %.0f%%  |  con %4.1f loi  |  dang chay %d  [%s]" % (
            self.do(), self.muc_tieu, self.con_trong(), len(self.von),
            ", ".join("%s:%d" % (l, self.dem_lan(l))
                      for l in ("CPU", "LLM", "MANG", "TESTER", "NHE")
                      if self.dem_lan(l)) or "trong") + (
            "  suat do duoc: " + " ".join("%s=%.1f" % kv for kv in
                                          sorted(self.do_duoc.items()))
            if self.do_duoc else "")


def do_nhanh(giay: float = 3.0) -> dict:
    """Anh CPU/RAM/dia mot phat - dung cho `q trang-thai`."""
    import shutil
    ra = {"cpu": psutil.cpu_percent(interval=giay),
          "so_loi": psutil.cpu_count(),
          "ram_pc": psutil.virtual_memory().percent}
    for o in ("C:/", "F:/"):
        try:
            ra["dia_" + o[0]] = round(shutil.disk_usage(o).free / 1e9, 2)
        except Exception:
            pass
    return ra
