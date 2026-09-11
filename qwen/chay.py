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
    q ban-giao       BAN GIAO NGUOC: mot man hinh cho nguoi quay lai sau vai ngay
    q xong <ma>      danh dau mot viec `can_nguoi` la da lam xong
    q ultra [N]      CHE DO ULTRA: chay lien tuc ho tro viec XAY, tran CPU N% (mac dinh 65)
    q thuong         ve mac dinh 85% + tran lan goc
    q nghi [phut]    CHOI GAME: ha CPU + khoa lan TESTER/CPU/LLM (mac dinh 60 phut, tu tro lai)
    q thuc           bo che do nghi ngay
    q cpu <N>        doi muc tieu CPU (an ngay, khong can khoi dong lai)
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
        self.dt.do_duoc.update(self.st.moc('nang_do_duoc') or {})
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

    def do_suat_lan(self) -> None:
        """Do suat CPU THAT cua tung lan roi day vao `dieu_toc`.

        Day la khau khep vong: bang `nang_lan` trong config chi la phong doan
        ban dau, con day la su that do tren chinh may nay. 20:30 08/09 khoang
        cach giua hai cai la 6,4 lan (khai 1,2 loi cho lan LLM, that 7,7).
        """
        theo_lan = {}
        for ma, v in self.dang.items():
            try:
                theo_lan.setdefault(v.lan, []).append(v.loi_dang_an())
            except Exception:
                pass
        for lan, ds in theo_lan.items():
            if len(ds) == 1 and ds[0] > 0.1:      # chi hoc khi lan do CHI co 1 viec
                self.dt.hoc(lan, ds[0])           # - nhieu viec thi khong tach duoc
        if theo_lan:
            self.st.dat_moc("nang_do_duoc", dict(self.dt.do_duoc))

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

    def ban_giao(self) -> str:
        """BAN GIAO NGUOC: mot man hinh cho nguoi (hay Claude) quay lai sau vai ngay.

        Khac `bao_cao`: bao cao la van do qwen viet cho chu du an doc. Ban giao la
        SO do may dem, sap theo dung thu tu ma nguoi quay lai can - viec gi da do
        duoc, viec gi hong, va viec gi dang cho chinh ho.
        """
        st, bg = self.st, self.bg
        d = ["# BAN GIAO NGUOC — dot chay tu dong",
             "",
             "phien bat dau : %s" % st.d.get("phien"),
             "den           : %s" % time.strftime("%Y-%m-%d %H:%M"),
             "so ngay da mo : %d" % len(self.ngay_da_mo), ""]

        nhom = {}
        for ma, v in st.d["viec"].items():
            nhom.setdefault((v.get("cong") or {}).get("ket") or v.get("trang_thai", "CHUA"),
                            []).append((ma, v))
        d.append("## Ket qua cong (code cham, khong phai qwen)")
        for ket in (CONG.DAT, CONG.AM, CONG.CHUA):
            ds = nhom.get(ket, [])
            d.append("\n### %s — %d viec" % (ket, len(ds)))
            for ma, v in sorted(ds):
                d.append("- **%s** (%ss) — %s" % (ma, int(v.get("giay") or 0),
                                                  (v.get("cong") or {}).get("vi_sao", "")))

        treo = bg.ket_treo(st)
        if treo:
            d.append("\n## CAN CHU DU AN — he khong tu chay duoc")
            for v in treo:
                d.append("- **%s** — %s\n  %s\n  xong roi thi: `q xong %s`"
                         % (v["ma"], v["ten"], v.get("ghi_chu", ""), v["ma"]))

        if st.d["de_xuat"]:
            d.append("\n## qwen DE XUAT (chua ai duyet, chua chay)")
            for v in st.d["de_xuat"]:
                d.append("- **%s** [%s] %s\n  vi sao: %s\n  lenh: `%s`"
                         % (v.get("ma"), v.get("lan"), v.get("ten"), v.get("vi_sao"),
                            " ".join(v.get("lenh", []))))

        d.append("\n## Nhat ky qwen (%d muc, 30 muc cuoi)" % len(st.d["nhat_ky"]))
        for m in st.d["nhat_ky"][-30:]:
            d.append("- `%s` **%s** — %s" % (m["luc"][5:16], m["ma"],
                                             m["van"].replace("\n", " ")[:300]))

        bc = sorted(CH.GOC.glob("BAO_CAO_*.md"), key=lambda p: p.stat().st_mtime,
                    reverse=True)[:7]
        d.append("\n## Bao cao ngay da sinh")
        d += ["- %s" % p.name for p in bc] or ["- (chua co)"]

        d.append("\n## Buoc tiep — cho Claude khi quay lai")
        d.append("1. Doc muc **CHUA_DO_DUOC** o tren truoc moi thu khac: do la cho he "
                 "khong do duoc, khong phai cho khong co edge.")
        d.append("2. Giao viec moi = sua `lab/qwen/NHIEM_VU.json` roi `q kiem` de "
                 "no soat bang, roi `q`.")
        d.append("3. Duyet muc **qwen DE XUAT** — chep cai nao dang lam vao bang.")

        van = "\n".join(d)
        p = CH.LAB / "BAN_GIAO_QWEN.md"
        p.write_text(van, encoding="utf-8")
        print(van)
        print("\n-> %s" % p, flush=True)
        return str(p)

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
    def nap_lai_bang(self) -> bool:
        """Doc lai NHIEM_VU.json neu no vua bi sua. Cho phep giao viec MOI cho
        mot dot dang chay ma khong phai dung no.

        Can cai nay vi dot chay keo nhieu ngay: chu du an (hay Claude khi quay
        lai) sua bang luc 2 gio sang thi khong co ly do gi bat giet ca lan tester
        dang chay do. Bang hong thi GIU ban cu - dung de mot dau phay thua lam
        chet ca dot chay.
        """
        try:
            moi = self.bg.duong.stat().st_mtime
        except OSError:
            return False
        if moi <= getattr(self, "_moc_bang", 0):
            return False
        cu = getattr(self, "_moc_bang", 0)
        self._moc_bang = moi
        if not cu:
            return False
        try:
            truoc = {v["ma"] for v in self.bg.ds}
            self.bg.nap()
            them = sorted({v["ma"] for v in self.bg.ds} - truoc)
            print("  ~~ bang viec vua doi -> da nap lai (%d viec%s)"
                  % (len(self.bg.ds), ", moi: " + ", ".join(them) if them else ""),
                  flush=True)
            return True
        except SystemExit as e:
            print("  !! bang viec moi HONG (%s) - giu ban cu, khong nap" % e, flush=True)
            return False

    def kiem_ma_doi(self) -> None:
        """Bao khi ma nguon `qwen/*.py` doi giua chung.

        Bang thi nap lai duoc; MA thi khong - Python da nap module vao bo nho roi,
        va `importlib.reload` giua mot vong lap co tien trinh con dang chay la
        cach hay nhat de co hai phien ban cong cung ton tai. Nen o day chi BAO,
        va bao MOT lan.

        Vi sao can bao: 20:17 08/09 toi sua `cong.py` de no do truong `ghi_moi`,
        nhung dot dang chay van cham bang ban cu - va khong co dong nao noi ra
        chuyen do. Mot tuan sau doc nhat ky se khong hieu tai sao cong xu khac
        voi ma dang nam tren dia.
        """
        if getattr(self, "_da_bao_ma_doi", False):
            return
        moi = max((p.stat().st_mtime for p in CH.QWEN.glob("*.py")), default=0)
        if not getattr(self, "_moc_ma", 0):
            self._moc_ma = moi
            return
        if moi > self._moc_ma:
            self._da_bao_ma_doi = True
            print("\n  !! MA NGUON qwen/*.py vua doi, nhung dot nay van chay BAN CU.\n"
                  "     Bang thi nap lai duoc, ma thi khong. Muon ap ma moi:\n"
                  "       q dung        (doi vong lap thoat em)\n"
                  "       q giet        (neu con tien trinh con)\n"
                  "       q             (chay lai - so tay giu nguyen ket qua da co)\n",
                  flush=True)

    def nap_lai_cau_hinh(self) -> None:
        """Doc lai `config/qwen.json` moi vong, va ap CHE DO NGHI neu dang bat.

        Vi sao doc lai moi vong chu khong doc mot lan luc khoi dong: chu du an
        ngoi truoc chinh cai may nay. Khi ho mo game (hay mot viec gi can may),
        khong the bat ho dung ca dot chay nhieu ngay chi de doi mot con so.

        CHE DO NGHI ha muc tieu CPU **va khoa han lan TESTER**. Ha muc tieu thoi
        la chua du: bo dieu toc chan viec MOI PHONG, no khong ghi duoc mot phien
        MT5 tester DANG chay - ma tester voi 20 agent chinh la thu an CPU nang
        nhat o day. Het gio thi tu tro lai, khong can ai nho.
        """
        try:
            c = CH.nap()
        except Exception:
            return
        den = float(c.get("nghi_den") or 0)
        dang_nghi = time.time() < den
        if dang_nghi:
            muc = float(c.get("cpu_khi_nghi", 35.0))
            tran = dict(c["tran_lan"], TESTER=0, CPU=0, LLM=0, MANG=1, NHE=2)
        else:
            muc, tran = float(c["muc_tieu_cpu"]), dict(c["tran_lan"])
            if getattr(self, "_dang_nghi", False):
                print("\n  == HET GIO NGHI -> tra lai muc tieu CPU %.0f%% va mo lan TESTER\n"
                      % muc, flush=True)
        if dang_nghi and not getattr(self, "_dang_nghi", False):
            print("\n  == CHE DO NGHI: muc tieu CPU %.0f%%, KHOA lan TESTER+CPU+LLM, den %s\n"
                  "     (bo som: `q thuc`)\n"
                  % (muc, time.strftime("%H:%M", time.localtime(den))), flush=True)
        self._dang_nghi = dang_nghi
        self.dt.muc_tieu = muc
        self.dt.c["tran_lan"] = tran
        self.c["tran_lan"] = tran

    def mot_vong(self) -> None:
        self.nap_lai_cau_hinh()
        self.nap_lai_bang()
        self.kiem_ma_doi()
        self.do_suat_lan()
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
                    # Bang trong MOT LUC khac han het viec THAT. Viec thuong truc
                    # dang nghi chu ky, hay mot phu thuoc chua toi luot, deu lam
                    # bang trong tam thoi - thoat o day thi may nam khong ca dem.
                    sap = self.bg.sap_san_sang(self.st)
                    if sap:
                        if im % 15 == 0:
                            print("  ... khong co viec chay duoc ngay. %d viec dang cho: %s"
                                  % (len(sap), "; ".join("%s (%s)" % (v["ma"], ly)
                                                         for v, ly in sap[:4])),
                                  flush=True)
                        im += 1
                        time.sleep(float(self.c["nhip_vong_giay"]))
                        continue
                    print("\n=== HET VIEC TU CHAY DUOC ===")
                    treo = self.bg.ket_treo(self.st)
                    if treo:
                        print("Con %d viec CAN CHU DU AN:" % len(treo))
                        for v in treo:
                            print("  * %s — %s" % (v["ma"], v["ten"]))
                            if v.get("ghi_chu"):
                                print("      %s" % v["ghi_chu"])
                    print("\nThem viec: sua qwen/NHIEM_VU.json roi chay lai `q`.")
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
    if lenh in ("nghi", "thuc", "cpu", "ultra", "thuong"):
        import json as _j
        c = {}
        if CH.CAU_HINH_NGOAI.exists():
            c = _j.loads(CH.CAU_HINH_NGOAI.read_text(encoding="utf-8-sig"))
        if lenh in ("ultra", "thuong"):
            # ULTRA = chay lien tuc HO TRO viec xay, trong mot TRAN CPU chua cho
            # nguoi dung. Khac `nghi` (choi game, khoa lan) va khac mac dinh 85%
            # (danh ca may). Chu du an 11/09: "cho cau hon 50% cpu, de lai vua du
            # de toi choi lol" -> 65% cua 20 luong ~ 13 luong, con ~7 cho game.
            #
            # Ultra KHONG nang tran lan TESTER: mot terminal64.exe la rang buoc
            # VAT LY, nang len la hai viec ghi de nhau va khong ai bao loi.
            if lenh == "ultra":
                c["muc_tieu_cpu"] = float(argv[1]) if len(argv) > 1 else \
                    float(c.get("muc_tieu_cpu_ultra", 65.0))
                c["nghi_den"] = 0
                c["che_do"] = "ultra"
                # TRAN LAN PHAI THEO TRONG SO DA DO, khong theo mong muon.
                # Ban dau toi dat LLM 6 - nhung `nang_lan` do duoc LLM = 8,0 loi
                # MOT viec, nen 3 viec LLM da la 24 loi tren mot may 20 luong.
                # Do that 20:10-20:18 ngay 11/09: CPU 66 -> 75 -> 86% trong khi
                # muc tieu la 65%. Bo dieu toc chi chan LUC PHONG; no khong giet
                # duoc viec da chay, nen tran lan dat sai thi muc tieu CPU khong
                # cuu duoc. Ngan sach 65% cua 20 luong = 13 loi:
                #   LLM 1x8,0 + CPU 2x2,0 + MANG 1x0,77  ~ 12,8
                tran = dict(c.get("tran_lan") or {})
                tran.update({"CPU": 3, "LLM": 2, "MANG": 2, "NHE": 4, "TESTER": 1})
                c["tran_lan"] = tran
                print("che do ULTRA: muc tieu CPU %.0f%% ca may (con ~%.0f%% cho game)."
                      % (c["muc_tieu_cpu"], 100 - c["muc_tieu_cpu"]))
                print("lan: CPU 3 · LLM 2 · MANG 2 · NHE 4 · TESTER 1 "
                      "(dat theo TRONG SO da do, khong theo mong muon).")
                print("Ha xuong khi can may: `q nghi 120`  |  ve mac dinh: `q thuong`.")
            else:
                c["che_do"] = "thuong"
                c["muc_tieu_cpu"] = 85.0
                c.pop("tran_lan", None)
                print("ve che do THUONG: muc tieu CPU 85%, tran lan theo mac dinh.")
            CH.CAU_HINH_NGOAI.write_text(_j.dumps(c, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
            print("Dot dang chay se thay trong ~%gs." % CH.nap()["nhip_vong_giay"])
            return 0
        if lenh == "nghi":
            phut = float(argv[1]) if len(argv) > 1 else 60.0
            c["nghi_den"] = time.time() + phut * 60
            c.setdefault("cpu_khi_nghi", 35.0)
            print("nghi %g phut (den %s): muc tieu CPU %.0f%%, KHOA lan TESTER+CPU+LLM (chi con MANG nhe)."
                  % (phut, time.strftime("%H:%M", time.localtime(c["nghi_den"])),
                     c["cpu_khi_nghi"]))
            print("Het gio no TU tro lai - khong phai lam gi. Bo som: `q thuc`.")
        elif lenh == "thuc":
            c["nghi_den"] = 0
            print("da bo che do nghi - muc tieu ve %.0f%%." % c.get("muc_tieu_cpu", 85))
        else:
            if len(argv) < 2:
                print("go: q cpu <phan tram>   (vi du: q cpu 50)")
                return 2
            c["muc_tieu_cpu"] = float(argv[1])
            print("muc tieu CPU -> %.0f%%" % c["muc_tieu_cpu"])
        CH.CAU_HINH_NGOAI.write_text(_j.dumps(c, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
        print("Dot dang chay se thay trong ~%gs (no doc lai config moi vong)."
              % CH.nap()["nhip_vong_giay"])
        return 0

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
    if lenh in ("ban-giao", "bg"):
        dp.ban_giao()
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
