# -*- coding: utf-8 -*-
"""b — MOT cua vao cho moi viec hang ngay cua THE BRAIN.

Vi sao co file nay: lab co ~94 file .py o muc goc, ds/ co them 40 thu muc.
Nho ten file la viec cua may, khong phai cua nguoi. Go `b` de xem menu.

    b                 menu
    b vao             VAO PHIEN: trang thai song + ban giao hom qua
    b ket "tom tat"   KET PHIEN: chot git + sinh TIEP_TUC_MAI.md cho mai
    b bg ["dong"]     ghi BAN GIAO SONG (khong doi cuoi phien moi ban giao)
    b bg-xem          xem ban giao song hien tai
    b xa              bat DIEU KHIEN XA qua Telegram (tat may / dung he tu xa)
    b xa-thu          kiem cau hinh Telegram + gui mot tin thu
    b test [tu-khoa]  chay test SONG SONG (8 tien trinh, ~1 phut thay vi 6)
    b test-me         chay test theo ME (ben khi may nghet - xem chay_test_tung_me.py)
    b test1 [tu-khoa] chay test MOT tien trinh (khi nghi song song lam sai)
    b toan-canh       MOT man hinh: dau vao + kho co che + tang kham pha
    b trang-thai      bang dieu khien (van hanh cua dieu phoi)
    b chay / b dung   bat / dung dieu phoi 24/7
    b canary          tu kiem engine (5 canary)
    b he [--het]      BANG CAC HE DA QUA CONG: tien, so lenh, so voi mua-giu
    b mach [--be]     MACH DAP 10 chang duong ong (--be = mutation audit)
    b ngan-sach [--don]  SO NGAN SACH tai nguyen (dia/RAM/LLM/tester/nhip host)
    b phan-loai       389 file ma -> 4 lan + BANG SUAT BOC tung lan
    b chi-bao [N]     boc co che tu file CHI BAO (N = test me; --that = chay het)
    b loc [--khung K] loc TINH truoc pheu: suy bien / trung hanh vi / spec hong
    b thang-gia       loi khai nao co NGUONG DON VI GIA (chet sach tren FX)
    b ten-ma [MA]     ma co tren may chu dang dang nhap khong (+ ten gan dung)
    b demo            HE RA TAI KHOAN THAT: dang-ky / bat / nhip [--that]
    b passview        tai khoan XEM MT5 -> lich su lenh: quet / boc / doc
    b tai-san <MA>    MOT CUA: tinh cach + chi phi + song + mua vu + ghep duoc
    b dem-nen <MA>    bo dem nen thuong + Heikin-Ashi (mo ta, khong du bao)
    b quet            quet_be_mat.py  (da tu goi `b loc` truoc khi quet)
    b mde             chay_bang_mde.py
    b cham-lai        cham lai MOI gia thuyet duoi the he cong hien tai
    b on-dinh         edge la CAO NGUYEN hay CAI GAI (do vung lan can)
    b hinh-dang       hinh dang do co khac NGAU NHIEN khong (so voi chuoi null)
    b mde-nap [khung] nap TRUOC bang MDE cho ca be mat (D1: ~4 phut, mot lan)
    b thanh-phan      kho THANH PHAN thu hoi tu he bi loai + toan hang con thieu
    b vong [--nhanh]  MOT LENH ca ba tru: SEEKER -> QUANTLAB -> EVO (6 chang)
    b luat            15 LUAT DOC KET QUA (sinh tu loi da xay ra that)
    b suy-nguoc [quet KHUNG]  truoc cu di manh co DAU HIEU gi (do dong thuan da ma)
    b evo [--ghi]     EVO: suc khoe TUNG MODULE + cat nghia + de xuat chay duoc
    b xay [--xem]     hang doi VIEC XAY (tuan tu, lien tuc, ben qua su co)
    b san             EVO di san cong cu/du an ngoai de tich hop
    b san-xem         xem kho cong cu da tim duoc
    b san-quet        nhat lai cong cu tu TOAN BO ban doc da co (khong tai gi moi)
    b trinh-duyet     mo Chrome bot + CDP 9224 (de doc nguon can dang nhap)
    b tai-khoan       nen tang nao da dang nhap, thieu cai gi
    b tai-khoan --mo <ten>   mo san trang tao tai khoan
    b ds [args]       chay pytest ben ds/ (kho DeepSeek)
    b tim <tu>        tim trong MA NGUON (bo qua data/reports/backups)
    b luu "msg"       chot nhanh vao git (thay cho copy vao backups/)
    b lich [n]        n commit gan nhat
    b lui <file>      tra mot file ve ban da chot
    b qwen [lenh]     HE TU CHAY: qwen lam tiep bang viec (xem qwen/DOC_TRUOC.md)
                      `b qwen` = `q`. `b qwen trang-thai` xem bang. `b qwen kiem`.
    b ban-do          SINH ban do tu ma nguon + chi ra module MO COI
    b kien-truc       SINH so do KIEN TRUC: module + VAI TRO + LOP + no kien truc
    b github          DAY lab/ len GitHub rieng (thebrainago/the-brain, rieng tu)
    b ho-so           HO SO HE THONG: mot file TU DU dua cho AI khong co dia
    b slot [kiem]     SLOT TESTER: may lan tester dung duoc, nang tran duoc chua
    b quantlab        QUY TRINH CHUAN 4 buoc: boc -> loc -> ho so -> ghep
    b phanh           han muc / kill-switch cua he chay that
    b quan-tri        75 khai bao quan tri -> MQL5 -> chen vao EA ngoai
    b bench-qt [MA]   BAN DO 11 ho quan tri tren tester (engine vao CO DINH)
    b pmg [g0|quet|so|bang]  PMG: ho quan li lenh KHONG CO TIN HIEU VAO (luoi ro)
    b tran-cpu [60|80|95]  TRAN CPU ca may - moi viec nang tu ha theo
    b uu-tien lan     HAI LAN: khai thac (WIP<=3, co han chot) vs xay may
    b go-html [N]     go trang HTML tho trong kho ra van ban (khau truoc BOC)
    b luan-lenh       truy nguoc tu DANH SACH LENH that -> luat vao lenh
    b chuyen          mang he sang KHUNG / TAI SAN khac (giu ty le kich hoat)
    b dau-chan        400 ho so signal -> KIEU chien luoc x tai san
    b im-lang         tang nao dang cam + nut that cua day chuyen
    b don-dia         gop WAL (thu phinh lang le an gap doi dia)
    b tien-ich        58 file tien ich bi bo: cai nao dang lay ve
    b nen-tang        ma chien luoc tu cTrader / NinjaTrader / ...
    b quy-luat [MA]   song co QUY LUAT khong (6 cau hoi + moc magnetic)
    b profile <file>  do cProfile mot script, in 25 dong ton nhat

Nguyen tac: file nay chi DIEU HUONG. Khong co logic nghien cuu nao o day.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
GOC = LAB.parent
DS = GOC / "ds"

# Trinh thong dich: `sys.executable`, khong go cung.
#
# Duong cu (`AppData\Local\Python\pythoncore-3.14-64\python.exe`) khong chi la
# duong cua mot MAY - no la duong cua mot BAN CAI. Nang Python len 3.15, hoac
# chuyen sang moi truong ao, hoac chuyen VPS: ca ba deu lam `b` gay ngay.
PY = Path(sys.executable)


def chay(cmd: list, cwd: Path = LAB) -> int:
    return subprocess.call([str(c) for c in cmd], cwd=str(cwd))


def _git(args: list, cwd: Path = GOC, im: bool = False):
    r = subprocess.run(["git", *args], cwd=str(cwd),
                       capture_output=im, text=True, encoding="utf-8", errors="ignore")
    return r


# ----------------------------------------------------------------- cac lenh
def c_vao(_):
    return chay([PY, LAB / "BAN_GIAO.py"])


def c_ket(a):
    return chay([PY, LAB / "KET_PHIEN.py", *a])


def c_test(a, song_song=True):
    cmd = [PY, "-m", "pytest", "-q"]
    if song_song:
        cmd += ["-n", "8", "--dist", "loadfile"]
    if a:
        cmd += ["-k", " or ".join(a)]
    return chay(cmd)


def c_toan_canh(_):
    return chay([PY, LAB / "toan_canh.py"])


def c_trang_thai(_):
    return chay([PY, LAB / "bang_dieu_khien.py"])


def c_chay(_):
    (LAB / "DUNG_LAI").unlink(missing_ok=True)
    return chay([PY, LAB / "dieu_phoi.py"])


def c_dung(_):
    (LAB / "DUNG_LAI").write_text("dung\n", encoding="utf-8")
    print("da dat co DUNG_LAI — dieu phoi se dung sau khi tru dang chay xong luot.")
    return 0


def c_canary(_):
    return chay([PY, LAB / "nhan" / "canary.py", "--tu-kiem"])


def c_quet(a):
    return chay([PY, LAB / "quet_be_mat.py", *a])


def c_phan_loai(a):
    """b phan-loai - chia kho ma thanh 4 lan + bang suat boc tung lan."""
    return chay([PY, LAB / "nhan" / "phan_loai_ma.py",
                 *(a or ["--suat"])], cwd=LAB)


def c_test_me(a):
    """b test-me - chay ca bo test bang NHIEU tien trinh pytest NGAN.

    Dung khi `b test` chet giua chung. Do 13/09: `b test` chet 4 lan lien o
    56-94% khong ban tom tat, vi mot tien trinh pytest song suot ~1.060 bai
    tich du bo nho tren mot may dang nghet paging. Chia me thi khong me nao
    song du lau, va me nao chet ta BIET la me nao.
    """
    return chay([PY, LAB / "chay_test_tung_me.py", *a], cwd=LAB)


def c_he(a):
    """b he [--het] - BANG CAC HE DA QUA CONG.

    Mat xich cuoi cung cua day chuyen, va no tung thieu: he CO san pham
    nhung khong cho nao tra loi duoc "hien co may he, moi cai bao nhieu".
    `--het` xem ca he chua qua cong.
    """
    return chay([PY, "-m", "nhan.bang_he", *a], cwd=LAB)


def c_ngan_sach(a):
    """b ngan-sach [--don] - SO NGAN SACH TAI NGUYEN.

    Cua vao chung cho moi viec nang: dia, RAM, so tien trinh, lop LLM/TESTER/
    CPU_NANG/BANG_THONG, va NHIP TOI THIEU theo tung host. `--don` giet tien
    trinh python mo coi. Xem dau `nhan/ngan_sach.py` de biet moi con so den
    tu phep do nao.
    """
    return chay([PY, "-m", "nhan.ngan_sach", *a], cwd=LAB)


def c_mach(a):
    """b mach [--be] - MACH DAP DUONG ONG: 9 chang, ~1,5 phut.

    `b canary` hoi "engine backtest con dung khong". `b mach` hoi "**day
    chuyen co dang chay khong**" - o dia, WAL, kho co che, pheu HTML, pheu ung
    vien, duong LLM, bang quan tri, lich su tester, engine.

    `--be` chay mutation audit: co tinh be tung chang roi doi mach phai BAT.
    Trong luot chay dau tien no tim ra HAI chang TOT GIA, mot trong so do nam
    ngay trong chinh no.
    """
    return chay([PY, "-m", "nhan.mach", *a], cwd=LAB)


def c_bench_qt(a):
    """b bench-qt [MA] - BAN DO HO QUAN TRI tren MT5 tester.

    Khac `b quan-tri`: cai do chen quan tri vao EA NGOAI (tra loi "co cai thien
    EA co san khong"); cai nay co dinh ENGINE VAO roi chi doi HO QUAN TRI (tra
    loi "ho nao manh hon ho nao"). Xem dau file `chay_bench_quan_tri.py`.

        b bench-qt                 US500Cash H1, engine donchian
        b bench-qt --ma EURUSD     mot ma khac
        b bench-qt --quet          quet DA TAI SAN x DA ENGINE (co phan chung)
    """
    if "--quet" in a:
        return chay([PY, LAB / "_quet_bench_qt.py",
                     *[x for x in a if x != "--quet"]], cwd=LAB)
    return chay([PY, LAB / "chay_bench_quan_tri.py", *a], cwd=LAB)


def c_go_html(a):
    """b go-html [N] - go trang HTML tho trong kho ra van ban.

    KHAU DUNG TRUOC `b boc`. Do 13/09: 3.948/5.486 ban chua boc la trang HTML
    tho, nen `boc_llm` chi tim duoc 8 ung vien tren ca kho. Go xong: 785.
    `b go-html --xem` chi dem, khong sua gi.
    """
    return chay([PY, LAB / "nhan" / "go_html.py", *a], cwd=LAB)


def c_chi_bao(a):
    """b chi-bao [N|--that] - boc co che tu 190 file CHI BAO."""
    return chay([PY, LAB / "nhan" / "doc_chi_bao.py", *a], cwd=LAB)


def c_loc(a):
    """b loc [--khung K] - bo loc TINH chay truoc pheu V0-V3."""
    return chay([PY, LAB / "nhan" / "loc_co_che.py", *a], cwd=LAB)


def c_tai_san(a):
    """b tai-san <MA> [KHUNG] - MOT CUA: moi dac diem tai san da do duoc."""
    return chay([PY, "-m", "nhan.ho_so_tai_san", *(a or ["AUDCAD"])], cwd=LAB)


def c_dem_nen(a):
    """b dem-nen <MA> [KHUNG] - bo dem nen thuong + Heikin-Ashi."""
    return chay([PY, "-m", "nhan.dem_nen", *(a or ["AUDCAD"])], cwd=LAB)


def c_passview(a):
    """b passview - TAI KHOAN XEM MT5 -> lich su lenh that (chi doc)."""
    return chay([PY, "-m", "nhan.passview", *a], cwd=LAB)


def c_demo(a):
    """b demo - DUONG TU HE DA QUA TESTER RA TAI KHOAN THAT (mac dinh DIEN TAP)."""
    return chay([PY, "-m", "nhan.chay_that", *a], cwd=LAB)


def c_thang_gia(a):
    """b thang-gia - loi khai nao dinh NGUONG TINH BANG DON VI GIA."""
    return chay([PY, LAB / "_quet_thang_gia.py", *a], cwd=LAB)


def c_ten_ma(a):
    """b ten-ma [MA...] - ma nay CO tren may chu dang dang nhap khong."""
    return chay([PY, "-m", "nhan.ten_ma", *a], cwd=LAB)


def c_mde(a):
    return chay([PY, LAB / "chay_bang_mde.py", *a])


def c_cham_lai(a):
    return chay([PY, LAB / "cham_lai_the_he.py", *a])


def c_on_dinh(a):
    return chay([PY, LAB / "do_on_dinh.py", *a])


def c_bg(a):
    return chay([PY, LAB / "ban_giao_song.py", *a])


def c_bg_xem(a):
    return chay([PY, LAB / "ban_giao_song.py", "--xem"])


def c_xa(a):
    return chay([PY, LAB / "dieu_khien_xa.py", *a])


def c_xa_thu(a):
    return chay([PY, LAB / "dieu_khien_xa.py", "--thu"])


def c_hinh_dang(a):
    return chay([PY, LAB / "hinh_dang_vs_null.py", *a])


def c_mde_nap(a):
    return chay([PY, LAB / "nap_truoc_mde.py", *a])


def c_thanh_phan(a):
    ma = [
        "import sys; sys.path.insert(0, r'%s')" % LAB,
        "from nhan import thu_hoi_thanh_phan as TH, so as SO",
        "print('KHO THANH PHAN: %d dong (%d viet ra duoc bang ngu phap)' % ("
        "SO.mot('SELECT COUNT(*) n FROM thanh_phan')['n'],"
        "SO.mot('SELECT COUNT(*) n FROM thanh_phan WHERE dien_dat_duoc=1')['n']))",
        "print()",
        "print('-- DUNG DUOC NGAY (top 20 theo so lan) --')",
        "[print('  %-14s %-14s cot=%-7s x%s' % (r['chi_bao'], r['tham_so'],"
        " r['cot'] or '-', r['so_lan'])) for r in TH.kho(True, 20)]",
        "print()",
        "print('-- TOAN HANG CON THIEU (do tu ma THAT, xep theo so lan dung) --')",
        "[print('  %-16s %5d lan · %2d bien the · %s' % (r['chi_bao'],"
        " r['tong_lan'], r['so_bien_the'], r['con_thieu']))"
        " for r in TH.toan_hang_con_thieu(20)]",
    ]
    return chay([PY, "-c", chr(10).join(ma)])


def c_san(a):
    return chay([PY, LAB / "nhan" / "san_cong_cu.py", *a])


def c_suy_nguoc(a):
    """SUY NGUOC: truoc mot cu di manh thi co dau hieu gi (QUANTLAB noi sinh)."""
    return chay([PY, "-m", "nhan.suy_nguoc", *a])


def c_luat(_):
    """15 luat doc con so - sinh tu loi da xay ra that."""
    p = LAB / "LUAT_GIAM_SAT.md"
    print(p.read_text(encoding="utf-8") if p.exists() else "chua co LUAT_GIAM_SAT.md")
    return 0


def c_vong(a):
    """MOT LENH chay ca ba tru: SEEKER -> QUANTLAB -> EVO."""
    return chay([PY, "-m", "nhan.vong_day_du", *a])


def c_evo(a):
    """EVO: suc khoe tung module + cat nghia + de xuat. `b evo --ghi` ghi van de."""
    return chay([PY, "-m", "nhan.evo", *a])


def c_xay(a):
    """Hang doi VIEC XAY, chay tuan tu va lien tuc."""
    return chay([PY, LAB / "day_viec.py", *a])


def c_san_quet(_):
    return chay([PY, "-c",
                 "import sys;sys.path.insert(0,'.');"
                 "from nhan import san_cong_cu as S;S.quet_lai_thu_vien()"])


def c_san_xem(_):
    return chay([PY, LAB / "nhan" / "san_cong_cu.py", "--xem"])


def c_tai_khoan(a):
    return chay([PY, LAB / "nhan" / "tai_khoan_nen_tang.py", *a])


def c_trinh_duyet(_):
    return chay([PY, LAB / "mo_chrome_cdp.py"])


def c_ds(a):
    if not DS.exists():
        print(f"khong thay {DS}")
        return 1
    return chay([PY, "-m", "pytest", "-q", *a], cwd=DS)


def c_tim(a):
    if not a:
        print("dung: b tim <tu khoa>")
        return 2
    loai = ["--glob=!data/**", "--glob=!data_khung/**", "--glob=!backups/**",
            "--glob=!reports/**", "--glob=!nghi_huu/**", "--glob=!__pycache__/**",
            "--glob=!.git/**", "--glob=!downloaded_codes/**", "--glob=!*.parquet"]
    for exe in ("rg", "rg.exe"):
        try:
            return subprocess.call([exe, "-n", "--color=never", *loai, a[0], str(GOC)])
        except FileNotFoundError:
            continue
    return subprocess.call(["grep", "-rn", "--include=*.py", "--include=*.md",
                            a[0], str(LAB)])


def c_luu(a):
    msg = a[0] if a else "chot nhanh"
    _git(["add", "-A"])
    r = _git(["commit", "-m", msg], im=True)
    print((r.stdout or "") + (r.stderr or ""), end="")
    return 0


def c_lich(a):
    n = a[0] if a else "15"
    return _git(["log", "--oneline", "--decorate", f"-{n}"]).returncode


def c_lui(a):
    if not a:
        print("dung: b lui <duong dan file>")
        return 2
    return _git(["restore", "--", *a]).returncode


def c_profile(a):
    if not a:
        print("dung: b profile <file.py> [args]")
        return 2
    ra = LAB / "reports" / "profile.prof"
    ra.parent.mkdir(exist_ok=True)
    rc = chay([PY, "-m", "cProfile", "-o", ra, a[0], *a[1:]])
    chay([PY, "-c",
          f"import pstats;pstats.Stats(r'{ra}').sort_stats('cumtime').print_stats(25)"])
    return rc


def c_phanh(a):
    """Khai / xem / mo lai HAN MUC - cai phanh cua he chay that.

    Them 12/09: EVO bat dau canh `phanh.chua_khai` va de xuat `b phanh <he>`.
    Mot de xuat khong go duoc la mot loi khuyen rong - dung benh ma chinh
    `nhan/evo.py` sinh ra de tranh.

        b phanh                      liet ke han muc cua moi he
        b phanh <he> --dd 20 --lenh 10 --phoi-nhiem 1.0 --von 1000
        b phanh-mo <he>              mo lai sau khi bi ngat (PHAI co nguoi)
    """
    from nhan import han_muc as HM
    from nhan import so as SO
    a = a or []
    if not a or a[0].startswith("-"):
        HM._khoi_tao()
        hs = SO.nhieu("SELECT * FROM han_muc ORDER BY he")
        if not hs:
            print("chua he nao khai han muc.")
        for r in hs:
            print("%-46s dd %5.1f%% | %2d lenh/ngay | phoi nhiem %.2f | von %.0f%s"
                  % (r["he"][:46], (r["tran_sut_giam"] or 0) * 100,
                     r["tran_lenh_ngay"] or 0, r["tran_phoi_nhiem"] or 0,
                     r["tran_von"] or 0, "  [NGAT]" if r["ngat"] else ""))
        chay = [r["ma"] for r in
                SO.nhieu("SELECT ma FROM he_chay WHERE trang_thai <> 'DUNG'")]
        thieu = [m for m in chay if not HM.cua(m)]
        if thieu:
            print("")
            print("%d he DANG CHAY ma chua khai han muc:" % len(thieu))
            for m in thieu:
                print("   %s" % m)
        return

    def _so(ten, mac_dinh):
        return float(a[a.index(ten) + 1]) if ten in a else mac_dinh

    r = HM.dat(a[0], tran_sut_giam=_so("--dd", 20.0) / 100.0,
               tran_lenh_ngay=int(_so("--lenh", 10)),
               tran_phoi_nhiem=_so("--phoi-nhiem", 1.0),
               tran_von=_so("--von", 1000.0))
    print(r)


def c_phanh_mo(a):
    """Mo lai mot he da bi ngat. Theo thiet ke PHAI co nguoi lam viec nay."""
    from nhan import han_muc as HM
    if not a:
        print("can ten he: b phanh-mo <he>")
        return
    print(HM.mo_lai(a[0], nguoi="nguoi_dung"))


def c_quy_luat(a):
    """SONG CO QUY LUAT KHONG - sau cau hoi, moi cau mot quy luat ung vien.

    `ho_so_song` MO TA song; file nay hoi song co QUY LUAT khong - do la cho
    sinh ra co che. Do 12/09 tren US500CASH D1: 4/5 quy luat dat, trong do
    L5 "hoi dung o moc thang" (1,67% so voi null 46,18%) chinh la **moc
    magnetic** ma so do neu ra.
    """
    return chay([PY, LAB / "nhan" / "quy_luat_song.py", *(a or [])])


def c_tien_ich(a):
    """58 file "TIEN ICH" bi bo o khau boc: cai nao dang LAY VE dung?

    Chu du an 05/09: *"tien ich thi can xem xem cai nao phu hop de lay ve"*.
    `phan_loai_ma` bo chung CO CHU DICH (khong dat lenh, khong buffer, khong lop
    quan tri) - dung cho khau boc co che, nhung "khong co co che" khong co nghia
    la "khong dung duoc": 31 file co `OnTick`, 19 co giao dien, 17 co
    `OnChartEvent`. Do la cong cu van hanh.
    """
    return chay([PY, LAB / "nhan" / "tien_ich_xet.py", *(a or [])])


def c_nen_tang(a):
    """Ma nguon chien luoc tu cac NEN TANG GIAO DICH KHAC (cTrader, NinjaTrader...).

    Dong so do: *"tim kiem da ngon ngu lap trinh nhu mql, c++, mql5 ctrader,..."*
    """
    return chay([PY, LAB / "nhan" / "nen_tang.py", *(a or [])])


def c_don_dia(a):
    """DON DIA: gop WAL + bao cai gi dang chiem cho.

    12/09/2026: o C con 177 MB va ba me boc lien tiep bao "XONG rc=0" ma kho
    khong nhich mot dong - loi that la `disk is full` bi nuot qua ba lop.
    Thu pham chinh la `nao.db-wal` 1,4 GB (bang dung chinh `nao.db`): WAL chi
    duoc gop khi mot checkpoint chay tron, tien trinh bi giet giua chung thi
    no o lai va lon len lang le.
    """
    rc = chay([PY, "-m", "nhan.gop_wal", "--het", *(a or [])])
    # Do them TRANG TRONG sau khi gop WAL. Gop WAL khong thu hoi trang trong -
    # do 16/09: WAL da 0 MB ma DB van 1,59 GB, trong do 0,95 GB la trang trong
    # tu xoa/ghi de lau ngay. Hai thu khac nhau, va lenh nay truoc gio chi bao
    # mot nua.
    from nhan import so as SO
    SO.nhip_ngay()
    return rc


def c_im_lang(a):
    """TANG NAO DANG CAM - bang thong luong tung khau cua ca day chuyen.

    Noi 12/09: `do_im_lang` mo coi. No tra loi noi so ma chu du an neu ra:
    *"so nhat la gio no bug hoac bo sot ma khong biet tai dau"*. Do 12/09:
    9 tang deu co dau ra, nut that la `ban doc -> thanh phan` 4,2%.
    """
    return chay([PY, LAB / "nhan" / "do_im_lang.py", *(a or [])])


def c_dau_chan(a):
    """LUAN NGUOC kieu chien luoc tu 400 ho so signal cong khai.

    Noi 12/09: `tin_hieu_mql5` + `dau_chan` deu mo coi, va
    `reports/signal_ho_so.json` (400 ho so) nam do tu truoc. Ba manh canh nhau
    ma khong ai noi. Ket qua: luoi_dca 142 tai khoan, tai san dau bang AUDCAD 70.

        b dau-chan                  phan loai het + bang tai san theo kieu
        b dau-chan --kieu luoi_dca  cac tai khoan mot kieu, xep theo SONG BAO LAU
    """
    return chay([PY, "-m", "nhan.luan_dau_chan", *(a or [])])


def c_chuyen(a):
    """MANG MOT HE SANG KHUNG / TAI SAN KHAC ma no van la chinh no.

    Gom ba module tung mo coi: `doi_khung` · `ngoai_sinh` · `quy_doi_tham_so`.
    Nguyen tac chung: giu TY LE KICH HOAT, khong giu con so - cai khong doi khi
    sang cho khac la DO HIEM cua su kien, khong phai nguong.

        b chuyen --khung H4      he dang co -> khung khac
        b chuyen --ma XAUUSDM    he DA PASS -> tai san khac
    """
    return chay([PY, "-m", "nhan.chuyen_he", *(a or [])])


def c_luan_lenh(a):
    """TRUY NGUOC tu DANH SACH LENH that -> luat vao lenh.

    Dong so do: *"Xay dung kha nang truy nguoc lich su giao dich de tim ra
    chien luoc roi dung mo phong chien luoc"*. Hai manh (`doc_lenh_tester` doc
    bao cao tester, `mimic_cau_noi` dich luat sang DSL) deu mo coi cho toi
    12/09 - hieu chuan da chay dung: tu 305 lenh cua he z5 no lay lai duoc
    chinh luat cua z5 (`stochastic(20) <= 16,16`, ty le vao 0,629 = 2,52 lan nen).

        b luan-lenh                        doc bao cao mac dinh
        b luan-lenh <bao_cao.htm>          doc mot bao cao khac
        b luan-lenh <bao_cao.htm> --luat <MA>   chung luat tu lenh that
    """
    return chay([PY, LAB / "nhan" / "doc_lenh_tester.py", *(a or [])])


def c_quan_tri(a):
    """CHUOI QUAN TRI VI THE - module chu du an goi la quan trong nhat.

    Noi 12/09 sau khi ban do cho thay ca BA manh deu mo coi:
    `quan_tri_dsl` (75 khai bao) · `dich_mq5_qtvt` · `de_quan_tri`.

        b quan-tri              xem kho 75 khai bao
        b quan-tri --dich-het   bao nhieu dich duoc sang MQL5, cai nao khong
        b quan-tri --dich 3     in khoi MQL5 cua mot khai bao
        b quan-tri --dich-nhieu in BANG N luat trong MOT EA (qua cong (1)+(2))
        b quan-tri --cap <EA.mq5> --khai-bao 3   sinh cap GOC / CO QUAN TRI
    """
    return chay([PY, "-m", "nhan.chuoi_quan_tri", *(a or [])])


def c_quantlab(a):
    """QUY TRINH QUANTLAB CHUAN 4 buoc (`CLAUDE.md`, chot 05/09).

    Noi vao `b` ngay 12/09 sau khi `b ban-do` cho thay `day_chuyen_quantlab.py`
    MO COI: quy trinh duoc ghi la CHUAN trong CLAUDE.md nhung khong cua vao nao
    goi toi, tuc no chi chay khi co nguoi nho ra ma go tay. Do 12/09: chay het
    19 giay va cho 127 co che + 8 ung vien - no van tot nguyen, chi la bi bo quen.
    """
    from nhan import day_chuyen_quantlab as DQ
    kieu = "hoi_quy"
    for x in (a or []):
        if not x.startswith("-"):
            kieu = x
            break
    DQ.chay(kieu=kieu, lam_moi="--moi" in (a or []))


def c_ban_do(a):
    """SINH lai ban do roi in. Khong in ban cu.

    Truoc 12/09 lenh nay chi `print` file `BAN_DO.md`. File do viet TAY va da
    cu 13 ngay, bo sot 11 module - tuc lenh nay dang phuc vu thong tin sai.
    Nay no goi `nhan.ban_do.sinh()` doc thang tu ma nguon; `b ban-do --cu` neu
    that su muon xem ban da ghi.
    """
    if "--cu" in (a or []):
        print((LAB / "BAN_DO.md").read_text(encoding="utf-8")
              if (LAB / "BAN_DO.md").exists() else "chua co BAN_DO.md")
        return
    from nhan import ban_do as BD
    vb = BD.sinh(in_ra=None)
    (LAB / "BAN_DO.md").write_text(vb, encoding="utf-8")
    print(vb)
    return 0


def c_ho_so(a):
    """SINH HO SO HE THONG — mot file TU DU dua cho AI khong co dia.

    Khac hai lenh tren o NGUOI DOC. `b ban-do` va `b kien-truc` viet cho nguoi
    (hoac AI) dang mo repo. Lenh nay viet cho Claude chat / ChatGPT / nguoi ngoai:
    so do + so lieu song + van de + de xuat + LUAT DOC KET QUA, gom mot file.

    Muc luat doc khong phai trang tri: thieu no thi nguoi ngoai se khuyen mot
    cach tu tin va sai, vi ho khong biet `Model=1` che ra lai gia hay placebo
    phai hoan vi chuoi vi the.
    """
    if "--cu" in (a or []):
        print((LAB / "HO_SO_HE_THONG.md").read_text(encoding="utf-8")
              if (LAB / "HO_SO_HE_THONG.md").exists() else "chua co HO_SO_HE_THONG.md")
        return
    from nhan import ho_so_he as HS
    vb = HS.sinh(in_ra=None)
    (LAB / "HO_SO_HE_THONG.md").write_text(vb, encoding="utf-8")
    print(vb)
    return 0


def c_slot(a):
    """SLOT TESTER: xem trang thai cac lan tester, va co duoc nang tran chua.

    `ngan_sach.TESTER = 1` lau nay duoc goi la "rang buoc VAT LY". Do 16/09:
    may co 6 ban cai MT5 va 8 thu muc du lieu - rang buoc nam o MA NGUON.
    Lenh nay cho biet dang co may lan dung duoc, va con thieu gi de nang.
    """
    from nhan import slot_tester as ST
    if a and a[0] in ("kiem", "k"):
        return ST.kiem()
    ST.bang()
    return 0


def c_github(a):
    """DAY lab/ len GitHub rieng (thebrainago/the-brain, repo RIENG TU).

    Vi sao phai co lenh nay: repo GitHub chi chua `lab/`, khong chua ca du an -
    goc du an co `sp500_phase1/` (da dong) va `nap_tay/` (ma cua nguoi khac),
    hai thu khong nen day di. Nen moi lan day phai TACH lich su cua rieng
    `lab/` ra (`git subtree split`) roi day nhanh do len `main`.

    Token doc tu `config/gh_token.txt` (da nam trong .gitignore). Lenh tat han
    credential helper: Git Credential Manager tren may nay treo cho mot cua so
    dang nhap khong bao gio hien ra.

        b github            day len
        b github --xem      chi in trang thai, khong day
    """
    import os as _os, subprocess as _sp
    kho = LAB / "config" / "gh_token.txt"
    if not kho.exists():
        print("thieu config/gh_token.txt - tao token scope `repo` roi luu vao do")
        return 1
    tok = kho.read_text(encoding="utf-8").strip()
    url = "https://%s@github.com/thebrainago/the-brain.git" % tok
    che = lambda s: s.replace(tok, "***")

    if "--xem" in (a or []):
        r = _sp.run(["git", "log", "-1", "--format=%h %s"], cwd=str(GOC),
                    capture_output=True, text=True)
        print("commit moi nhat o may:", r.stdout.strip())
        print("repo               : https://github.com/thebrainago/the-brain (rieng tu)")
        return 0

    print("1/2 tach lich su cua rieng lab/ ...")
    _sp.run(["git", "branch", "-D", "the-brain"], cwd=str(GOC),
            capture_output=True, text=True)
    r = _sp.run(["git", "subtree", "split", "--prefix=lab", "-b", "the-brain"],
                cwd=str(GOC), capture_output=True, text=True, timeout=1800)
    if r.returncode:
        print("tach that bai:", che(r.stderr)[-500:])
        return r.returncode

    print("2/2 day len GitHub ...")
    env = dict(_os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    r = _sp.run(["git", "-c", "credential.helper=",
                 "-c", "credential.interactive=never",
                 "push", url, "the-brain:main", "--force"],
                cwd=str(GOC), capture_output=True, text=True, env=env, timeout=1800)
    print(che(r.stdout + r.stderr)[-600:])
    print("=> " + ("XONG" if r.returncode == 0 else "LOI, ma thoat %d" % r.returncode))
    return r.returncode


def c_tho(a):
    """THO CODE: giao mot don hang viet ma cho LLM re. `b tho <don_hang.json>`

    Chia viec, va no den tu mot quan sat cu the chu khong tu so thich:

        NGUOI / mo hinh manh   quyet dinh XAY GI, va viet BAI TEST (= dac ta)
        LLM RE                 go phan cai dat cho den khi bai test xanh
        CODE                   cham dat/khong - `pytest`, khong ai tu phan

    Viet duoc bai test dung la phan kho. Dien cho no xanh la phan lap lai, va
    do la phan dang tra tien cho mot mo hinh re.

    `b tho don.json --thu` chay kho: in loi nhac se gui, khong goi LLM.
    """
    import json
    from qwen import tho_code as TC
    if not a:
        print("dung: b tho <don_hang.json> [--thu]")
        print("mau co san: don_hang_mau.json")
        return
    don = json.loads(Path(a[0]).read_text(encoding="utf-8-sig"))
    don.setdefault("goc", str(LAB))
    if "--thu" in a:
        goc = Path(don["goc"])
        print(TC._nhac(don, goc, "(chay kho - chua co loi that)")[:4000])
        return
    r = TC.lam(don)
    print("%s  (%d vong)" % (r["trang_thai"], r["so_vong"]))
    if r.get("ly_do"):
        print(r["ly_do"][:1500])
    if r["trang_thai"] == "CHUA_DO_DUOC":
        print("\n^ CHUA_DO_DUOC khac KHONG_DAT: duong LLM hong hoac lenh cham")
        print("  khong chay duoc, nen chua noi duoc gi ve viec mo hinh co sua")
        print("  noi hay khong. Kiem `q kiem` truoc khi ket luan.")


def _sau(co: str, a) -> str | None:
    """Gia tri dung sau mot co trong danh sach doi so, hoac None."""
    a = list(a or [])
    return a[a.index(co) + 1] if co in a and a.index(co) + 1 < len(a) else None


def c_hepha(a):
    """HEPHAESTUS - DE CO CHE. `b hepha [do|duc|tu-vung] [so]`

    So do he thong (LUAT SO 0) khai lenh nay tu 13/09 nhung module chua tung
    duoc viet, nen he chi biet may mo cai co san. Ba viec:

        b hepha do        ngu phap NOI DUOC bao nhieu, kho DANG DUNG bao nhieu
        b hepha duc 200   de 200 co che moi, in lo + plan_hash de tien dang ky
        b hepha bien-the  rai luoi tham so quanh co che DA CO trong kho
        b hepha ghep      ghep doi co che trong kho thanh he hai dieu kien
        b hepha tu-vung   huong tim kiem day nguoc ve SEEKER, uu tien cho TRONG
        b hepha qt 200    de 200 CAU HINH QUAN TRI LENH (ho ra tien nhat da do)
        b hepha qt 200 --ma AUDCAD --khung H4   chay that + xep hang SO VOI NULL
        b hepha nap 200   de 200 co che roi NAP vao kho (chay KHO mac dinh)
        b hepha nap 200 --that   ghi THAT vao kho

    `nap` chay KHO neu khong co `--that`. Kho co che la du lieu san xuat - no
    da tung tut 2.975 xuong 21 co che trong mot buoi sang - nen mot lenh go
    nham khong duoc phep sua no.
    """
    from nhan import hephaestus as HP
    viec = (a[0] if a else "do").lower()
    so = next((int(x) for x in (a or [])[1:] if str(x).isdigit()), 200)

    if viec == "do":
        r = HP.do_phu()
        print("ngu phap NOI DUOC : %d toan hang" % r["so_noi_duoc"])
        print("kho DANG DUNG     : %d" % r["so_dang_dung"])
        print("BO TRONG          : %d" % len(r["bo_trong"]))
        print("  " + ", ".join(r["bo_trong"]))
        return

    if viec in ("tu-vung", "tu_vung"):
        for h in HP.tu_vung(so_huong=so if so != 200 else 10):
            print("%-16s %s" % (h["chi_bao"], " · ".join(h["tu_khoa"])))
        return

    if viec in ("qt", "quan-tri"):
        # De CAU HINH QUAN TRI LENH. Khong co du lieu thi chi liet ke; co
        # `--ma X --khung Y` thi chay that va xep hang SO VOI NULL.
        ds = HP.duc_quan_tri(han_ngach=so)
        from collections import Counter
        for k, v in Counter(c["khuon"] for c in ds).most_common():
            print("  %-20s %d" % (k, v))
        print("\nde ra: %d cau hinh quan tri" % len(ds))
        ma = _sau("--ma", a)
        if not ma:
            print("them `--ma EURUSD --khung H1` de chay that va xep hang.")
            return
        from nhan import du_lieu as DL
        df = DL.nap(ma, _sau("--khung", a) or "H1")
        r = HP.danh_gia_vs_null(ds, df, so_null=int(_sau("--null", a) or 20))
        hc = HP.hieu_chuan(ds, df, so_lan=3)
        print("\nTY LE LOT TREN NHIEU: %.0f%%  <- doc con so nay TRUOC bang duoi"
              % (100 * hc["ty_le_lot"]))
        print("%-30s %8s %10s %8s" % ("cau hinh", "vuot", "lai/nam", "muc"))
        for d in r["dong"][:20]:
            if d.get("vuot_null") is None:
                continue
            print("%-30s %7.0f%% %10.1f %8s"
                  % (d["ten"][:30], 100 * d["vuot_null"],
                     (d.get("ket_qua") or {}).get("lai_nam", 0.0),
                     d["diem"]["muc"]))
        print("\nplan_hash: %s  (FDR tinh %d suat)"
              % (r["plan_hash"], r["so_phep_thu"]))
        return

    if viec == "nap":
        that = "--that" in (a or [])
        r = HP.nap(HP.duc(han_ngach=so), that=that)
        print("%s: %d nhan · %d trung kho · %d tu choi"
              % ("GHI THAT" if that else "chay KHO", r["nhan"], r["trung"],
                 r["tu_choi"]))
        print("plan_hash: %s   (FDR tinh %d suat)"
              % (r["plan_hash"], r["so_phep_thu"]))
        print("do ty le kich hoat: %s" % r["do_kich_hoat"])
        if r["do_kich_hoat"] == "CHUA_DO_DUOC":
            print("  ^ khong nap duoc chuoi kiem nao - con so 'nhan' o tren MOI")
            print("    chi la qua cong CU PHAP, chua ai do ty le kich hoat ca.")
        for k, v in sorted(r["ly_do"].items(), key=lambda x: -x[1])[:5]:
            print("   %3dx %s" % (v, k))
        if not that:
            print("\nchua ghi gi. Them `--that` de ghi vao kho.")
        return

    if viec in ("bien-the", "bien_the", "ghep"):
        from nhan import ngu_phap as NP
        kho = NP.doc_kho(cho_rong_khi_hong=True)
        if not kho:
            print("kho rong (khong doc duoc nao.db) - lenh nay can kho that")
            return
        if viec == "ghep":
            ds = HP.ghep_lo(kho, han_ngach=so)
        else:
            ds = []
            for g in kho:
                ds += HP.bien_the(g, han_ngach=6)
                if len(ds) >= so:
                    break
            ds = ds[:so]
        lo = HP.dang_ky_lo(ds)
        print("tu %d co che trong kho -> %d ban moi" % (len(kho), len(ds)))
        print("plan_hash: %s   (FDR tinh %d suat)"
              % (lo["plan_hash"], lo["so_phep_thu"]))
        return

    ds = HP.duc(han_ngach=so)
    lo = HP.dang_ky_lo(ds)
    from collections import Counter
    for k, v in Counter(x["khuon"] for x in ds).most_common():
        print("  %-18s %d" % (k, v))
    print("\nde ra   : %d co che" % len(ds))
    print("plan_hash: %s   (tien dang ky - FDR tinh %d suat)"
          % (lo["plan_hash"], lo["so_phep_thu"]))
    print("\nDe nhieu la luong thien NEU tra du gia FDR. De nhieu roi chi khai")
    print("vai cai dep la gian lan - nen con so tren phai di kem moi ket luan.")


def c_kien_truc(a):
    """SINH so do KIEN TRUC: module nao, VAI TRO gi, thuoc LOP nao.

    Khac `b ban-do` o cau hoi no tra loi. `ban-do` hoi "co nam tren duong chay
    khong" (toi duoc / mo coi). Lenh nay hoi "he co nhung TANG gi, module nao
    thuoc tang nao, va tang nao dang phinh hay rong" - tuc cau de LEN KE HOACH,
    khong phai cau de khoi xoa nham.

    Sinh thang tu ma nguon nhu `ban-do`, vi cung mot ly do: mot so do viet tay
    cu 13 ngay thi con te hon khong co. `b kien-truc --cu` xem ban da ghi.
    """
    if "--cu" in (a or []):
        print((LAB / "KIEN_TRUC.md").read_text(encoding="utf-8")
              if (LAB / "KIEN_TRUC.md").exists() else "chua co KIEN_TRUC.md")
        return
    from nhan import kien_truc as KT
    vb = KT.sinh(in_ra=None)
    (LAB / "KIEN_TRUC.md").write_text(vb, encoding="utf-8")
    print(vb)
    return 0



# ---- DAY CHUYEN 03/09/2026: san -> doc -> boc -----------------------------
def _nhan(a, i, mac_dinh):
    return a[i] if len(a) > i else mac_dinh


def c_day_chuyen(a):
    """b day-chuyen [MA] - ca day chuyen mot lenh."""
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import day_chuyen as D;"
                 f"D.mot_luot({_nhan(a, 0, 'US500CASH')!r})"], cwd=LAB)


def c_san(a):
    """b san-nguon [MA] - LUONG 1: san theo tai san + ten he thong + MQL5."""
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import day_chuyen as D;"
                 f"D.san({_nhan(a, 0, 'US500CASH')!r})"], cwd=LAB)


def c_boc(a):
    """b boc [SO_DOC] [SO_BOC] - LUONG 2: doc song song + boc co che."""
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import day_chuyen as D;"
                 f"D.boc({int(_nhan(a, 0, 500))}, {int(_nhan(a, 1, 200))})"], cwd=LAB)


def c_noi_sinh(a):
    """b noi-sinh [MA] [KHUNG] - LUONG 3: sinh co che tu chinh lich su."""
    return chay([PY, LAB / "_noi_sinh_chay.py", "--ma", _nhan(a, 0, "US500CASH"),
                 "--khung", _nhan(a, 1, "H4")], cwd=LAB)


def c_pheu(a):
    """b pheu - do tung chang cua pheu nguon."""
    return chay([PY, LAB / "_pheu_nguon.py"], cwd=LAB)


def c_mang(a):
    """b mang - kiem duong ra cho cac nguon, bat WARP neu can."""
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import day_chuyen as D;"
                 "m=D.kiem_mang();"
                 "_=D.bat_warp() if m.get('mql5')!='OK' else None"], cwd=LAB)


def c_chi_tieu(a):
    """b chi-tieu [NGAY] - hom nay dat chi tieu nao, thieu cai nao."""
    n = repr(a[0]) if a else "None"
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import chi_tieu as CT;"
                 f"CT.in_bao_cao({n})"], cwd=LAB)


def c_kham_pha(a):
    """b kham-pha - chay het cac kenh TU TIM nguon moi (blog + telegram)."""
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import kham_pha_nguon as KP; KP.mot_luot()"], cwd=LAB)


def c_nguon_cho(a):
    """b nguon-cho - liet ke nguon ung vien dang cho nguoi gat."""
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import kham_pha_nguon as KP;"
                 "[print(f\"{str(d.get('nguoi')):>8}  {d['khoa'][:36]:36s} "
                 "{str(d.get('ten'))[:44]}\") for d in KP.dang_cho_duyet()]"],
                cwd=LAB)


def c_finder(a):
    """b finder [--khong-san] - san cong cu ngoai + phan loai the de xuat."""
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from tru import finder as F;"
                 f"F.mot_luot(san={'--khong-san' not in a})"], cwd=LAB)


def c_tinix(a):
    """b tinix - nap chi muc du an tu repo.tinix.ai vao kho cong cu."""
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import nguon_tinix as T; T.nap_vao_kho()"], cwd=LAB)


def c_tele(a):
    """b tele [KENH] - quet kenh Telegram (web, hoac MTProto neu co khoa)."""
    if a:
        return chay([PY, "-c",
                     "import sys; sys.path.insert(0,'.');"
                     "from nhan import telegram as TG;"
                     f"print(TG.quet_tat_ca(kenh=({a[0]!r},)))"], cwd=LAB)
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import telegram as TG; print(TG.quet_tat_ca())"], cwd=LAB)


def c_qwen(a):
    """b qwen [...] - he tu chay bang qwen. Cua vao ngan hon la `q` o cung thu muc.

    Vi sao co ca hai: `q` la lenh chu du an go hang ngay; `b qwen` de nguoi doc
    menu `b` biet la he do TON TAI.
    """
    return chay([PY, "-X", "utf8", "-m", "qwen.chay", *a], cwd=LAB)



def c_da_thu(a: list) -> int:
    """`b da-thu "<mo ta>"` - so BAI HOC da co gi ve huong nay chua.

    Cua tra cuu cua khoi 2. Truoc khi dang ky mot gia thuyet hay mo mot huong,
    hoi cai nay. No KHONG phan xet - no dua ra nhung lan truoc he da di huong
    do, de cai gi lap lai thi lap lai CO Y THUC.
    """
    from nhan import bai_hoc as BH
    if not a:
        d = BH.dem()
        print(f"so bai hoc: {d['tong']} the")
        for k, v in sorted(d["theo_loai"].items(), key=lambda x: -x[1]):
            print(f"  {k:22s} {v}")
        print('')
        print('Go:  b da-thu "phi qua dem CFD chi so"')
        return 0
    the = BH.tra(" ".join(a), so_the=6)
    if not the:
        print("khong co the nao lien quan - huong nay CHUA tung duoc ghi.")
        return 0
    for t in the:
        print(f"[{t['loai']}] {t['tieu_de']}   (diem {t['diem']})")
        noi = " ".join(t["noi_dung"].split())
        print(f"    {noi[:220]}")
        if t["bang_chung"]:
            print(f"    bang chung: {' '.join(t['bang_chung'].split())[:170]}")
        print()
    return 0



def c_uu_tien(a: list) -> int:
    """`b uu-tien <url|file>` - LUONG UU TIEN cua chu du an.

    Mot link -> toan van -> co che -> dang ky, ngay trong phien. Khong phai cho
    hang doi 10.000 tai lieu may tu quet.
    """
    from nhan import uu_tien as UT
    if a and a[0] == "lan":
        # HAI LAN (ban giao 13/09 muc 11): khai thac vs xay may, ngan sach tach han
        UT.bang_lan()
        het = UT.het_han()
        if het:
            print("  QUA HAN - tra ve kho hoac gia han CO Y THUC:")
            for v in het:
                print(f"     {v['ten']}  (han {v['han']})")
        return 0
    if not a:
        print('go: b uu-tien <url hoac duong dan file>')
        print('    b uu-tien lan          HAI LAN: khai thac (WIP<=3) vs xay may')
        print('vi du: b uu-tien https://www.youtube.com/watch?v=...')
        return 2
    UT.in_ra(UT.xu_ly(a[0]))
    return 0


def c_video(a: list) -> int:
    """`b video [N]` - lay phu de cho N video trong kho (mac dinh 20)."""
    from nhan import doc_video as DV
    import json as _j
    print(_j.dumps(DV.mot_luot(int(a[0]) if a else 20), ensure_ascii=False, indent=1))
    return 0


def c_pmg(a: list) -> int:
    """`b pmg ...` - PMG: ho quan li lenh KHONG CO TIN HIEU VAO.

    Dac ta cua chu du an (`tai_lieu/PMG_DAC_TA.md`, vao qua LUONG UU TIEN
    14/09/2026), xep thang vao module QUAN LI LENH. Day la ho ma ban giao 13/09
    muc 4.B'.2 doi: bench cu gan quan tri len mot engine vao CO DINH roi hoi
    "them quan tri thi doi gi"; PMG khong co entry nao ca, no song hoan toan
    bang luoi + chot ro.

        b pmg g0 [MA...]   CONG G0 - o nao co bat doi xung that (re, chay TRUOC)
        b pmg bang         in lai ban do G0 da co
        b pmg quet MA      G1 -> G2 -> G3 -> G4 tren mot o da qua G0
        b pmg so           so LOAI TRU (o nao da dong, dong o cong nao)

    Thu tu la BAT BUOC, khong phai goi y: engine PMG duoi random walk co ky vong
    bang dung `-chi phi`, nen chay G2 trên mot o chua qua G0 la dot CPU vao mot o
    da biet truoc ket qua. `b pmg quet` tu choi o chua co ket qua G0.
    """
    from nhan import pmg_g0 as G0
    lenh = (a[0] if a else "g0").lower()
    if lenh == "g0":
        ma = a[1:] or ["US500CASH", "XM_US500CASH", "XM_US100CASH", "XAUUSDM",
                       "EURGBP", "AUDCAD"]
        b = G0.chay_bang(ma, "M5", "H1")
        G0.in_bang(b)
        G0.nap_ket_qua_vao_so(b)
        return 0
    if lenh == "bang":
        import json as _j
        if not G0.BANG_G0.exists():
            print("chua co ban do G0 - chay `b pmg g0` truoc")
            return 1
        G0.in_bang(_j.loads(G0.BANG_G0.read_text(encoding="utf-8")))
        return 0
    if lenh == "so":
        so = G0.doc_loai_tru()
        if not so:
            print("so loai tru rong")
            return 0
        vv = sum(1 for d in so if d.get("vinh_vien"))
        print(f"SO LOAI TRU: {len(so)} dong ({vv} dong VINH VIEN - chet o G0)")
        print(f"{'ma':<16}{'phien':<14}{'tf':<5}{'h':>5}{'cong':>6}  ghi chu")
        for d in so[-40:]:
            print(f"{d['ma']:<16}{d['phien']:<14}{d['atr_tf']:<5}{float(d['h']):5g}"
                  f"{d['cong']:>6}  {str(d.get('ghi_chu',''))[:60]}")
        return 0
    if lenh == "quet":
        if len(a) < 2:
            print("go: b pmg quet <MA> [KHUNG] [ATR_TF]")
            return 2
        from nhan import pmg_quet as Q
        r = Q.quet(a[1], a[2] if len(a) > 2 else "M5", a[3] if len(a) > 3 else "H1")
        Q.in_ket_qua(r)
        return 0
    print("b pmg [g0|bang|quet MA|so]")
    return 2



def c_tran_cpu(a: list) -> int:
    """`b tran-cpu [so]` - TRAN CPU cua ca may. Moi viec nang tu ha theo con so nay.

    May nay la may CA NHAN cua chu du an. Khong so nay thi moi lan chu du an choi
    game lai phai cat ngang phien de sua tay.

        b tran-cpu          xem dang de bao nhieu, may dang chay bao nhieu
        b tran-cpu 60       choi game nang
        b tran-cpu 80       vua lam vua dung may
        b tran-cpu 95       di ngu, de may chay het suc
    """
    from nhan import tran_cpu as TC
    if a:
        cu = TC.tran(lam_moi=True)
        moi = TC.dat_tran(float(a[0]))
        print(f"tran CPU: {cu:.0f}%  ->  {moi:.0f}%")
        print("viec dang chay se tu ha trong vong mot phut (chung doc lai moi 30 giay).")
        return 0
    print(f"tran CPU dang khai  : {TC.tran(lam_moi=True):.0f}%")
    print(f"CPU toan may bay gio: {TC.cpu_hien_tai(1.0):.0f}%")
    print(f"so tien trinh nen mo: {TC.so_luong_goi_y()}")
    return 0



LENH = {
    "vao": c_vao, "ket": c_ket,
    "qwen": c_qwen, "q": c_qwen,
    "test": lambda a: c_test(a, True), "test1": lambda a: c_test(a, False),
    "toan-canh": c_toan_canh, "tc": c_toan_canh,
    "trang-thai": c_trang_thai, "tt": c_trang_thai,
    "chay": c_chay, "dung": c_dung, "canary": c_canary,
    "quet": c_quet, "mde": c_mde, "mde-nap": c_mde_nap,
    # --- 05/09/2026: khau boc tach + bo loc truoc pheu ---
    "phan-loai": c_phan_loai, "chi-bao": c_chi_bao, "loc": c_loc,
    # --- 15/09/2026: hai cong tung CO ma khong nam tren duong chay ---
    "thang-gia": c_thang_gia, "ten-ma": c_ten_ma, "demo": c_demo,
    "tai-san": c_tai_san, "dem-nen": c_dem_nen, "passview": c_passview,
    "cham-lai": c_cham_lai, "on-dinh": c_on_dinh,
    "hinh-dang": c_hinh_dang,
    "bg": c_bg, "bg-xem": c_bg_xem, "xa": c_xa, "xa-thu": c_xa_thu,
    "thanh-phan": c_thanh_phan, "san": c_san, "san-xem": c_san_xem, "san-quet": c_san_quet,
    "evo": c_evo, "xay": c_xay, "suy-nguoc": c_suy_nguoc, "luat": c_luat,
    "vong": c_vong,
    "tai-khoan": c_tai_khoan, "trinh-duyet": c_trinh_duyet,
    "ds": c_ds, "tim": c_tim,
    "luu": c_luu, "lich": c_lich, "lui": c_lui,
    "ban-do": c_ban_do, "profile": c_profile,
    "kien-truc": c_kien_truc, "kt": c_kien_truc,
    "hepha": c_hepha, "hephaestus": c_hepha,
    "tho": c_tho, "tho-code": c_tho,
    "github": c_github, "gh": c_github,
    "slot": c_slot,
    "ho-so": c_ho_so, "hs": c_ho_so,
    "quantlab": c_quantlab, "ql": c_quantlab,
    "phanh": c_phanh, "phanh-mo": c_phanh_mo,
    "quan-tri": c_quan_tri, "qt": c_quan_tri,
    "bench-qt": c_bench_qt, "pmg": c_pmg, "tran-cpu": c_tran_cpu, "go-html": c_go_html, "mach": c_mach,
    "ngan-sach": c_ngan_sach, "ns": c_ngan_sach, "he": c_he,
    "test-me": c_test_me,
    "luan-lenh": c_luan_lenh, "chuyen": c_chuyen,
    "dau-chan": c_dau_chan, "im-lang": c_im_lang,
    "don-dia": c_don_dia,
    "tien-ich": c_tien_ich, "nen-tang": c_nen_tang,
    "quy-luat": c_quy_luat,
    # --- day chuyen 03/09/2026 ---
    "day-chuyen": c_day_chuyen, "dc": c_day_chuyen,
    "san-nguon": c_san, "boc": c_boc,
    "noi-sinh": c_noi_sinh, "pheu": c_pheu, "mang": c_mang,
    # --- 04/09/2026 ---
    "finder": c_finder, "tinix": c_tinix, "tele": c_tele,
    "kham-pha": c_kham_pha, "nguon-cho": c_nguon_cho,
    "chi-tieu": c_chi_tieu, "ct": c_chi_tieu,
    # --- khoi 2 (11/09/2026): so bai hoc ---
    "da-thu": c_da_thu, "bai-hoc": c_da_thu,
    # --- khoi 5 (11/09/2026): cac cua vao con thieu ---
    "uu-tien": c_uu_tien, "ut": c_uu_tien, "video": c_video,
}


def main(argv: list) -> int:
    if not argv or argv[0] in ("-h", "--help", "help", "?"):
        print(__doc__)
        return 0
    ten, *con = argv
    if ten not in LENH:
        gan = [k for k in LENH if k.startswith(ten[:2])]
        print(f"khong co lenh '{ten}'." + (f" Y ban la: {', '.join(gan)}?" if gan else ""))
        print("\nGo `b` de xem menu.")
        return 2
    return LENH[ten](con) or 0


if __name__ == "__main__":
    os.chdir(LAB)
    raise SystemExit(main(sys.argv[1:]))
