# -*- coding: utf-8 -*-
"""chay.py - VONG LAP DIEU PHOI. Mot lenh `q` la du de he chay tiep nhieu ngay.

## Mot vong lam gi

    1. do CPU (dieu_toc)                     -> con bao nhieu loi de cap
    2. thu hoach tien trinh da xong          -> cong.cham() -> so tay
       (roi giao cho qwen doc va viet, o LUONG RIENG de khong chan vong lap)
    3. giet tien trinh qua gio               -> QUA_GIO, khong phai ket qua am
    4. phong them viec san sang, lap day lan -> trong gioi han CPU va tran lan
    5. dau ngay / cuoi ngay                  -> qwen mo dau va viet bao cao
    6. ngu mot nhip roi lap lai

## Vi sao goi qwen o LUONG rieng

Mot luot tac tu ton 15-60 giay. Neu goi thang trong vong lap thi trong 60 giay do
khong ai phong viec moi va CPU tut xuong. Nen phan viec: vong lap chinh chi lam
viec do va phong; nhan xet cua qwen chay o hai luong nen.

## Dung the nao

    q                he chay lien tuc cho den khi het viec (hoac Ctrl-C)
    q dung           dat co dung - vong lap dang chay se thoat EM sau vong hien tai
    q trang-thai     in bang viec + trang thai may, khong chay gi
    q mot-vong       chay dung mot vong roi thoat (de thu)
    q bao-cao        sinh bao cao ngay ngay bay gio
    q de-xuat        xem viec qwen de xuat, chua ai duyet
    q xong <ma>      danh dau mot viec `can_nguoi` la da lam xong
    q kiem           tu kiem ca duong: mo hinh, cong, dieu toc, bang
"""
from __future__ import annotations

import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from . import bang_viec as BV
from . import cau_hinh as CH
from . import cong as CONG
from . import cong_cu as CC
from . import dieu_toc as DT
from . import so_tay as ST
from . import tien_trinh as TT

KHOA = threading.Lock()


def _han(phut: float) -> str:
    return "%.0f giay" % (phut * 60) if phut < 1 else "%g phut" % phut


# ===================================================================== in
def tieu_de(s: str) -> None:
    print("\n" + "=" * 78 + "\n" + s + "\n" + "=" * 78, flush=True)


def in_trang_thai(bg, st, dt) -> None:
    tieu_de("THE BRAIN / QWEN — BANG VIEC")
    print(bg.bang_chu(st))
    treo = bg.ket_treo(st)
    if treo:
        print("\n--- CAN CHU DU AN (he khong tu chay) ---")
        for v in treo:
            print("  * %-22s %s" % (v["ma"], v["ten"]))
            if v.get("ghi_chu"):
                print("      %s" % v["ghi_chu"])
            print("      xong roi thi go:  q xong %s" % v["ma"])
    m = DT.do_nhanh(1.0)
    print("\nmay: CPU %.0f%% / %d loi | RAM %.0f%% | C: %.1f GB | F: %.1f GB"
          % (m["cpu"], m["so_loi"], m["ram_pc"], m.get("dia_C", 0), m.get("dia_F", 0)))
    if m.get("dia_C", 99) < 6:
        print("!! C: duoi 6 GB - tester se treo va ghi 'low disk space' chu khong bao loi.")
    if st.d["de_xuat"]:
        print("qwen da de xuat %d viec chua duyet - xem `q de-xuat`" % len(st.d["de_xuat"]))


# ===================================================================== vong
class DieuPhoi:
    def __init__(self) -> None:
        CH.bao_dam_thu_muc()
        self.c = CH.nap()
        self.st = ST.SoTay()
        self.bg = BV.BangViec()
        self.dt = DT.DieuToc(self.c)
        self.dang: dict[str, TT.Viec] = {}
        self.tho = ThreadPoolExecutor(max_workers=2, thread_name_prefix="qwen")
        self.ngay_da_mo = set(self.st.d.get("ngay_da_mo", []))
        CC.NGU_CANH["so_tay"] = self.st
        CC.NGU_CANH["bang"] = self.bg
        n = ST.don_treo(self.st)
        if n:
            print("!! %d viec con DANG_CHAY tu lan truoc -> danh dau GIAN_DOAN" % n)

    # ------------------------------------------------------------ thu hoach
    def thu_hoach(self) -> None:
        for ma in list(self.dang):
            v = self.dang[ma]
            if v.con_chay():
                if v.qua_gio():
                    v.giet()
                    ma_thoat, log = v.dong()
                    self.dt.nha(ma)
                    del self.dang[ma]
                    with KHOA:
                        self.st.ket_thuc(ma, ma_thoat,
                                         {"ket": CONG.CHUA,
                                          "vi_sao": "qua han %s -> bi giet. Day la "
                                                    "CHUA DO DUOC, khong phai ket qua am."
                                                    % _han(v.v["toi_da_phut"])}, log[-1500:])
                        self.st.dat(ma, trang_thai="QUA_GIO")
                    print("  [t] %-22s qua gio, da giet" % ma, flush=True)
                continue
            ma_thoat, log = v.dong()
            self.dt.nha(ma)
            del self.dang[ma]
            ket = CONG.cham(v.v, ma_thoat, v.bat_dau, log, self.st)
            with KHOA:
                self.st.ket_thuc(ma, ma_thoat, ket, log[-1500:])
            print("  [%s] %-22s %s  |  %s" % (
                "x" if ma_thoat == 0 else "!", ma, ket["ket"], ket["vi_sao"][:96]),
                flush=True)
            self.tho.submit(self.qwen_doc, ma, dict(v.v), ket)

    def qwen_doc(self, ma: str, viec: dict, ket: dict) -> None:
        from . import tac_tu as TA
        try:
            r = TA.doc_ket_qua_viec(ma, viec, ket)
            if r:
                print("  qwen> %s" % r.replace("\n", "\n         ")[:600], flush=True)
        except Exception as e:
            print("  !! qwen doc %s loi: %s" % (ma, e), flush=True)

    # ------------------------------------------------------------ phong
    def phong(self) -> int:
        n = 0
        for v in self.bg.san_sang(self.st):
            if v["ma"] in self.dang:
                continue
            duoc, ly_do = self.dt.cho_phep(v["lan"])
            if not duoc:
                continue
            try:
                tv = TT.Viec(v, self.c)
            except Exception as e:
                with KHOA:
                    self.st.dat(v["ma"], trang_thai="LOI",
                                cong={"ket": CONG.CHUA,
                                      "vi_sao": "khong phong duoc: %s" % e})
                print("  !! %s khong phong duoc: %s" % (v["ma"], e), flush=True)
                continue
            self.dang[v["ma"]] = tv
            self.dt.giu(v["ma"], v["lan"])
            with KHOA:
                self.st.bat_dau(v["ma"], v["lan"], v["lenh"])
            print("  [>] %-22s %-6s pid %-6d %s  (%s)" % (
                v["ma"], v["lan"], tv.p.pid, v["ten"][:40], ly_do), flush=True)
            n += 1
        return n

    def ai_dang_an(self) -> str:
        """Viec nao dang an CPU THAT - do tren cay tien trinh, khong doan.

        Can no khi mot dot chay nhieu ngay: dong trang thai noi 'CPU 88%' nhung
        khong noi 88% do la cua tester hay cua mot viec treo dang quay vong lap.
        """
        an = sorted(((v.loi_dang_an(), m) for m, v in self.dang.items()), reverse=True)
        an = [(c, m) for c, m in an if c >= 0.2]
        return ("  | " + " ".join("%s %.1f" % (m, c) for c, m in an[:4])) if an else ""

    # ------------------------------------------------------------ ngay
    def moc_ngay(self) -> None:
        hom_nay = time.strftime("%Y-%m-%d")
        if hom_nay not in self.ngay_da_mo:
            self.ngay_da_mo.add(hom_nay)
            self.st.d["ngay_da_mo"] = sorted(self.ngay_da_mo)
            self.st.luu()
            ngay = len(self.ngay_da_mo)
            self.tho.submit(self._mo_dau, ngay)
        if (int(time.strftime("%H")) >= int(self.c["gio_bao_cao"])
                and not (CH.GOC / ("BAO_CAO_%s.md" % hom_nay.replace("-", "_"))).exists()
                and not self.dang):
            self.bao_cao()

    def _mo_dau(self, ngay: int) -> None:
        from . import tac_tu as TA
        try:
            print("\nqwen mo dau ngay %d>\n%s\n" % (ngay, TA.mo_dau_ngay(ngay)), flush=True)
        except Exception as e:
            print("!! mo dau ngay loi: %s" % e, flush=True)

    def bao_cao(self) -> str:
        from . import tac_tu as TA
        md = TA.viet_bao_cao(self.st.d["nhat_ky"], self.bg.bang_chu(self.st))
        p = CH.GOC / ("BAO_CAO_%s.md" % time.strftime("%Y_%m_%d"))
        dau = ("# BAO CAO %s — do qwen sinh tu dot chay tu dong\n\n"
               "> Ban NHAP. So do `qwen/cong.py` cham; van do qwen viet. Chu du an\n"
               "> doc lai truoc khi tin.\n\n" % time.strftime("%d/%m/%Y"))
        p.write_text(dau + md, encoding="utf-8")
        print("-> %s" % p, flush=True)
        return str(p)

    # ------------------------------------------------------------ vong lap
    def mot_vong(self) -> None:
        self.thu_hoach()
        self.phong()
        self.moc_ngay()

    def chay(self) -> int:
        tieu_de("QWEN DIEU PHOI — muc tieu CPU %.0f%% tren %d loi"
                % (self.dt.muc_tieu, self.dt.so_loi))
        print("dung: `q dung` (hoac tao file lab/DUNG_QWEN) | Ctrl-C cung an toan")
        print(self.bg.bang_chu(self.st))
        if CH.CO_DUNG.exists():
            CH.CO_DUNG.unlink()
        im = 0
        try:
            while True:
                if CH.CO_DUNG.exists():
                    print("\nthay co DUNG_QWEN -> thoat em")
                    break
                self.mot_vong()
                con = self.bg.san_sang(self.st)
                if not self.dang and not con:
                    print("\n=== HET VIEC TU CHAY DUOC ===")
                    treo = self.bg.ket_treo(self.st)
                    if treo:
                        print("Con %d viec CAN CHU DU AN:" % len(treo))
                        for v in treo:
                            print("  * %s — %s" % (v["ma"], v["ten"]))
                    self.bao_cao()
                    break
                if im % 6 == 0:
                    print("  ~ %s | san sang %d | %s%s" % (
                        time.strftime("%H:%M:%S"), len(con), self.dt.dong_trang_thai(),
                        self.ai_dang_an()), flush=True)
                im += 1
                time.sleep(float(self.c["nhip_vong_giay"]))
        except KeyboardInterrupt:
            print("\nCtrl-C — de tien trinh con chay tiep, so tay da ghi.")
            print("Chay lai `q` la no thu hoach tiep. Muon giet het: `q giet`")
            return 130
        finally:
            self.tho.shutdown(wait=True)
            self.st.luu()
        return 0

    def giet_het(self) -> int:
        n = 0
        for ma, v in list(self.dang.items()):
            v.giet()
            n += 1
        return n


# ===================================================================== cli
def kiem() -> int:
    tieu_de("TU KIEM DUONG QWEN")
    ok = True
    from . import mo_hinh as MH
    try:
        d = MH.kiem()
        print("mo hinh : %s" % json.dumps(d, ensure_ascii=False))
        ok &= all("loi" not in v for k, v in d.items() if isinstance(v, dict))
    except Exception as e:
        print("mo hinh : LOI %s" % e)
        ok = False
    try:
        bg = BV.BangViec()
        st = ST.SoTay()
        print("bang    : %d viec, %d san sang, %d can nguoi"
              % (len(bg.ds), len(bg.san_sang(st)), len(bg.ket_treo(st))))
    except SystemExit as e:
        print("bang    : LOI %s" % e)
        ok = False
    # Cong phai qua CA HAI bai: bat duoc bang chet, va KHONG keu oan bang song.
    song = [{"lai": i * 1.5, "dd": 20 + i, "lenh": 30 + i, "lot": 0.1} for i in range(8)]
    g1, l1 = CONG.dong_giong_het_nhau(song)
    print("cong    : bang SONG (1 cot hang so hop le) -> %s (%s)"
          % ("khong keu oan, dat" if not g1 else "KEU OAN!", l1))
    chet = [{"lai": 5.0, "dd": 20.0, "lenh": 30, "lot": 0.1} for _ in range(8)]
    g2, l2 = CONG.dong_giong_het_nhau(chet)
    print("cong    : bang CHET (tham so khong tac dung) -> %s (%s)"
          % ("bat duoc, dat" if g2 else "SOT!", l2))
    ok &= (not g1) and g2
    dt = DT.DieuToc()
    time.sleep(1)
    print("dieu toc: %s" % dt.dong_trang_thai())
    print("\n%s" % ("TAT CA DAT" if ok else "!! CO CHO CHUA DAT — doc lai o tren"))
    return 0 if ok else 1


def main(argv: list) -> int:
    lenh = (argv[0] if argv else "chay").lower()

    if lenh in ("-h", "--help", "help", "?"):
        print(__doc__)
        return 0
    if lenh == "dung":
        CH.CO_DUNG.write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
        print("da dat co DUNG_QWEN — vong lap dang chay se thoat sau vong hien tai.")
        return 0
    if lenh == "kiem":
        return kiem()

    dp = DieuPhoi()

    if lenh in ("trang-thai", "tt", "xem"):
        in_trang_thai(dp.bg, dp.st, dp.dt)
        return 0
    if lenh == "mot-vong":
        dp.mot_vong()
        time.sleep(2)
        dp.thu_hoach()
        in_trang_thai(dp.bg, dp.st, dp.dt)
        return 0
    if lenh == "bao-cao":
        dp.bao_cao()
        return 0
    if lenh == "de-xuat":
        if not dp.st.d["de_xuat"]:
            print("chua co de xuat nao.")
            return 0
        for v in dp.st.d["de_xuat"]:
            print("\n* %s  [%s]  %s\n  vi sao: %s\n  lenh  : %s"
                  % (v.get("ma"), v.get("lan"), v.get("ten"), v.get("vi_sao"),
                     " ".join(v.get("lenh", []))))
        print("\nDuyet bang cach chep muc do vao qwen/NHIEM_VU.json.")
        return 0
    if lenh == "xong":
        if len(argv) < 2:
            print("go: q xong <ma_viec>")
            return 2
        ma = argv[1]
        if not dp.bg.viec(ma):
            print("khong co viec `%s` trong bang" % ma)
            return 2
        dp.st.dat(ma, trang_thai="XONG",
                  cong={"ket": CONG.DAT, "vi_sao": "chu du an bao da lam xong"})
        print("da danh dau %s XONG. Cac viec phu thuoc no gio chay duoc." % ma)
        return 0
    if lenh == "giet":
        print("da giet %d tien trinh" % dp.giet_het())
        return 0
    if lenh in ("chay", ""):
        return dp.chay()

    print("khong co lenh `%s`. Go `q help`." % lenh)
    return 2


if __name__ == "__main__":
    import os
    os.chdir(CH.LAB)
    sys.exit(main(sys.argv[1:]))
