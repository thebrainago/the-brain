# -*- coding: utf-8 -*-
"""san_cong_cu.py - DI SAN CONG CU CO SAN, thay vi tu viet lai tu dau.

VI SAO CO FILE NAY (chu du an chot 30/08/2026).

EVOLUTION cho toi hom nay chi lam mot nua viec cua no: **do suc khoe day chuyen
va tu sua nhung viec da khai bao**. Nua con lai chua ai lam: **di tim nhung du
an va cong cu da co san ngoai kia de tich hop vao he**.

Hai vi du chu du an dua ra, va ca hai deu dung:

  - `hoainama8/convertOCR` - doi PDF sang Markdown/JSON/HTML. Khau doc bai viet
    cua ta dang thieu dung thu do.
  - `coding-kitties/investing-algorithm-framework` - 2.022 sao, Apache-2.0,
    con hoat dong. Co HAI engine backtest (vector + su kien), 50+ chi so, sweep
    tham so, kiem dinh nhieu cua so (rolling/anchored/holdout/walk-forward),
    Monte Carlo permutation, bao cao HTML, ket noi san qua CCXT.

RANH GIOI PHAI GIU. Khung do manh hon `lab` o BAN THI NGHIEM, nhung no **khong
co lop chong tu lua minh** cua du an nay: khong kiem soat FDR tren ca chuong
trinh nghien cuu, khong dang ky truoc bang plan hash, khong so cai chi-them,
khong do MDE, khong canary tu chung minh la nhay, khong xuat xu chi phi
(`do_tin` DO/SAN/KHAI). Permutation test tren MOT chien luoc **khong phai** la
kiem soat sai lech khi thu hang tram gia thuyet.

Nen quy tac tich hop la mot chieu:

    Cong cu ngoai duoc lam BAN THI NGHIEM (engine, bao cao, nap du lieu).
    Cong cu ngoai KHONG BAO GIO lam ONG TOA (cong PASS, FDR, dang ky truoc).

Va: mot cong cu tim duoc la UNG VIEN, khong phai mot quyet dinh tich hop. No di
vao so nhu moi thu khac, va nguoi doc no.

NANG CAP 31/08/2026 - NOI VAO SO VAN DE.

Cho toi 30/08 module nay di san theo mot danh sach NHU_CAU **tinh**: viet mot
lan roi khong bao gio doi. Do luot san gan nhat: `tim_them=0, loi=3`. Mo ra thi
ca ba "loi" deu la TIM DUOC MA KHONG CO KET QUA (`tim_github` tra `[]`,
`tim_dien_dan` tra `[]`) - dung cai bay `da_quet=0` bi bao thanh "khong co gi",
chi la nguoc chieu. Va vi truy van khong ra ket qua thi khong ghi vet o dau,
lan sau `mot_luot` lai chon dung ba truy van do -> 17 truy van con lai khong
bao gio den luot.

Hai thu duoc them:

  1. **SO TRUY VAN** (`cong_cu_truy_van.json`): moi truy van ghi lai `luc`,
     `ket` (CO_KET_QUA / RONG / LOI) va so ket qua. Chu ky thu lai khac nhau
     theo `ket` - LOI thu lai ngay, RONG doi 14 ngay (do la CAU TRA LOI, khong
     phai su co), CO_KET_QUA doi 30 ngay. Nho do hang doi truy van XOAY VONG.
  2. **NHU CAU SINH TU VAN DE DANG MO** (`NHU_CAU_TU_VAN_DE`): mot van de muc
     NANG trong so -> mot nhu cau ky thuat -> mot truy van san. Anh xa la KHAI
     BAO TRUOC (`VAN_DE_SANG_NHU_CAU`), khong phai do LLM sinh ra: nguyen tac
     "kien thuc moi chi vao he bang khai bao" ap ca o day.

Chay:
    python nhan/san_cong_cu.py            mot luot san theo NHU_CAU
    python nhan/san_cong_cu.py --xem      xem kho cong cu da tim duoc
    python nhan/san_cong_cu.py --so       xem so truy van (cai gi da thu, ra gi)
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import so as SO
else:
    from . import so as SO

LAB = Path(__file__).resolve().parent.parent
KHO = LAB / "reports" / "cong_cu.json"

#: Giay nghi giua hai lan goi API. GitHub search khong khoa cho **10 lan/phut**.
NGHI_GIAY = 7.0

#: Giay phep dung duoc — cong cu se nam TRONG ma nguon cua du an.
GIAY_PHEP_OK = {"MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "ISC",
                "MPL-2.0", "Unlicense", "0BSD"}
#: Giay phep LAY NHIEM: dung trong du an kin thi rang buoc phai mo nguon theo.
GIAY_PHEP_LAY_NHIEM = {"GPL-3.0", "GPL-2.0", "AGPL-3.0", "LGPL-3.0"}

#: NHU CAU — cho ta DANG THIEU, viet ro truoc khi di tim.
#:
#: `cam_vao` la noi ma nao cua cong cu se duoc GOI TU. Neu mot cong cu chi de
#: doi chieu tu ben ngoai (chay rieng, so ket qua bang tay) thi `cam_vao` phai
#: la "KHONG cam vao dau ca" va dat ten dich vao `doi_chieu_voi`. Phan biet nay
#: khong phai chu nghia hinh thuc: `test_san_cong_cu` chan bat ky nhu cau nao
#: khai `cam_vao` tro toi ong toa (cong / do_luc / so / quant_plan / canary).
#:
#: Viet nhu cau truoc roi moi tim la co y: tim truoc roi moi nghi ra ly do can
#: no thi lan nao cung "tim thay thu huu ich", va do la mot dang tu lua minh
#: khac. Moi muc phai noi ro NO CAM VAO DAU va CAI GI NO KHONG DUOC THAY.
NHU_CAU = {
    # ------------------------------------------------------------------
    # NHOM KY THUAT (them 30/08/2026 theo chi dan chu du an: EVO nam RONG
    # HON linh vuc giao dich - phan lon van de cua ta la van de TIN HOC
    # thuong, va cong dong da giai chung tu lau).
    #
    # Moi nhu cau duoi day gan voi mot nut that DA DO DUOC tren may nay,
    # khong phai mot mong muon chung chung. Do la ly do chung dang mot suat
    # tim kiem con "lam cho he nhanh hon" thi khong.
    # ------------------------------------------------------------------
    "do_nut_that": {
        "vi_sao": "Do 29/08: 42% thoi gian chay la `nt.stat` - khong ai doan "
                  "ra, phai profile moi thay. Sua bang cache TTL -> pheu nhanh "
                  "8 lan, bo test 6:07 -> 1:15. Ta khong co bo do thuong truc, "
                  "nen lan sau lai phai doan.",
        "cam_vao": "cong cu ngoai, chay canh day chuyen - khong nhap vao ma",
        "khong_duoc_thay": "khong duoc cham nhan/cong.py, nhan/so.py; do dac "
                           "khong duoc chiem suat FDR",
        "truy_van": ["python sampling profiler production",
                     "python profiling slow file system calls"],
        "sao_toi_thieu": 500,
        "duong": ["github", "dien_dan"],
    },
    "song_song_va_bo_nho": {
        "vi_sao": "May 20 luong nhung nghen BANG THONG BO NHO: co viec 20 luong "
                  "= 1 luong, co viec (pheu D1, tap lam viec 128 KB nam trong "
                  "cache CPU) nhanh that 3,8 lan. Ta chua co cach BIET TRUOC "
                  "viec nao thuoc loai nao, nen dang thu-va-sai.",
        "cam_vao": "quet_be_mat.py, dieu_phoi.py - cach chia viec",
        "khong_duoc_thay": "khong duoc doi ket qua tinh toan; song song chi "
                           "duoc doi TOC DO, khong duoc doi mot con so nao",
        "truy_van": ["memory bandwidth bound numpy multiprocessing",
                     "when multiprocessing does not speed up python"],
        "sao_toi_thieu": 0,
        "duong": ["dien_dan"],
    },
    "nhanh_hon_so_hoc": {
        "vi_sao": "Quet be mat va placebo la vong lap numpy tren hang trieu "
                  "bar; mot lan placebo day du la 995 luot backtest. Nhanh hon "
                  "o day doi thang ra SO GIA THUYET kiem duoc moi ngay.",
        "cam_vao": "nhan/mo_phong.py, nhan/mau.py - lop tinh toan",
        "khong_duoc_thay": "TUYET DOI khong duoc doi ket qua so hoc. Bat ky "
                           "thay the nao phai doi chieu tung bar voi ban cu "
                           "truoc khi dung.",
        "truy_van": ["numba vectorized backtest speedup",
                     "polars vs pandas time series performance"],
        "sao_toi_thieu": 800,
        "duong": ["github", "dien_dan"],
    },
    "luu_tru_va_doc_gia": {
        "vi_sao": "Do 29/08: 42% thoi gian chay la `nt.stat` cua `kho()` - "
                  "cache TTL keo pheu nhanh 8 lan va bo test tu 6:07 xuong "
                  "1:15. Kho co 111 bang >= 12 nam va con phinh; doc gia van "
                  "la duong nong nhat cua ca day chuyen.",
        "cam_vao": "nhan/du_lieu.py - lop doc du lieu gia",
        "khong_duoc_thay": "khong duoc doi cach CHON ban du lieu (do phu), "
                           "chi duoc doi cach DOC",
        "truy_van": ["duckdb parquet time series query speed",
                     "fastest way to load large parquet python"],
        "sao_toi_thieu": 300,
        "duong": ["github", "dien_dan"],
    },
    "chay_lau_dai_khong_nguoi_truc": {
        "vi_sao": "The Brain phai chay 24/7 khong nguoi truc. Task Scheduler bi "
                  "Access denied nen dang phai dung Startup; Chrome tung phinh "
                  "356 tab va treo ca luot keo ma khong mot ban ghi nao. Ta "
                  "chua co cach TU HOI PHUC.",
        "cam_vao": "dieu_phoi.py - lop giam sat tien trinh",
        "khong_duoc_thay": "khong duoc tu khoi dong lai mot tru dang giua mot "
                           "phep ghi so cai",
        "truy_van": ["supervise long running python process windows restart",
                     "detect hung headless chrome automation"],
        "sao_toi_thieu": 0,
        "duong": ["dien_dan"],
    },
    # Them 30/08/2026 sau khi do pheu doc: trong 2.504 cau bo doc nhan la "luat
    # vao", 42,0% la manh MA NGUON va 44,7% la VAN TAN GAU. Bo doc tu choi
    # chung la dung, nhung cong doc van bi tieu vao 87% rac.
    "xep_thu_tu_doc": {
        "vi_sao": "87% cau ung vien la rac (manh ma nguon + van tan gau). Mot "
                  "bo phan loai van ban tra loi 'bai nay co ta mot luat khong' "
                  "du de doi thu tu doc va don gap cong doc ve phia bai co luat.",
        "cam_vao": "tru/seeker.py - xep hang tai lieu truoc khi doc toan van",
        "khong_duoc_thay": "TUYET DOI khong duoc sinh co che, khong duoc cham "
                           "nhan/cong.py hay nhan/ngu_phap.py. Doan sai thi hau "
                           "qua toi da la doc nham THU TU - khong bao gio la "
                           "mot gia thuyet sai duoc dang ky.",
        "truy_van": ["text classification trading strategy",
                     "financial text classification",
                     "zero shot text classification"],
        "sao_toi_thieu": 0,
        "tren_hugging": True,
    },
    "doc_pdf": {
        "vi_sao": "275 tai lieu la lien ket doi.org va 133 la arXiv PDF. "
                  "`toan_van.tu_arxiv` chi boc duoc arXiv; PDF nha xuat ban thi khong.",
        "cam_vao": "nhan/toan_van.py - them mot bo boc PDF",
        "khong_duoc_thay": "khong lien quan den cong PASS",
        "truy_van": ["pdf to markdown converter",
                     "pdf text extraction layout language:python"],
        "sao_toi_thieu": 200,
    },
    "engine_backtest": {
        "vi_sao": "engine cua ta chay dung nhung it tinh nang (khong co bao cao, "
                  "khong co sweep san, mot engine duy nhat).",
        "cam_vao": "co the lam BAN THI NGHIEM song song de doi chieu ket qua",
        "khong_duoc_thay": "TUYET DOI khong thay nhan/cong.py, nhan/do_luc.py, "
                           "nhan/so.py - do la ong toa, khong phai ban thi nghiem",
        "truy_van": ["quantitative trading backtesting framework language:python",
                     "vectorized backtesting engine language:python"],
        "sao_toi_thieu": 300,
    },
    "kiem_dinh_thong_ke": {
        "vi_sao": "FDR/LORD, deflated Sharpe, reality check cua ta tu viet. "
                  "Ban da duoc nhieu nguoi doc thi dang tin hon.",
        "cam_vao": "KHONG cam vao dau ca - chay ngoai, doc lap",
        "doi_chieu_voi": "nhan/cong.py",
        "khong_duoc_thay": "chi DOI CHIEU tu ben ngoai: hai ban tinh doc lap cung "
                           "mot con so roi so ket qua. Khong mot dong nao cua no "
                           "duoc goi tu duong quyet dinh.",
        "truy_van": ["multiple hypothesis testing false discovery rate language:python",
                     "deflated sharpe ratio probability backtest overfitting"],
        "sao_toi_thieu": 100,
    },
    # ---------------- PHUONG PHAP, khong phai cong cu ----------------
    # Chu du an chot 30/08: "the gioi co rat nhieu nguoi lam quant, nhieu bo loc
    # va cong trinh nghien cuu se giup tang toc quy trinh ta dang lam".
    #
    # Khac voi nam nhu cau tren: cai ta di tim o day khong phai mot kho ma de
    # `pip install`, ma la mot PHUONG PHAP - mot bo loc, mot phep hieu chuan,
    # mot cach tranh mot cai bay. No vao he qua NGUOI DOC roi khai bao lai,
    # khong bao gio qua `import`.
    #
    # Vi sao tach rieng: mot bai bao khong co sao GitHub, khong co giay phep,
    # khong co "lan day cuoi". Cham diem theo suc khoe kho ma la vo nghia voi
    # chung. Chung chi co mot thu de danh gia: **no giai bai toan nao cua ta**.
    "phuong_phap_chong_qua_khop": {
        "vi_sao": "Cong cua ta tu viet: FDR LORD, MDE, placebo hoan vi. Ba thu "
                  "nay co ban chuan trong tai lieu hoc thuat, va doi chieu voi "
                  "ban chuan la cach duy nhat biet ta co tu che ra luat rieng.",
        "cam_vao": "KHONG cam vao dau ca - nguoi doc roi quyet",
        "doi_chieu_voi": "nhan/cong.py, nhan/do_luc.py",
        "khong_duoc_thay": "khong mot dong ma nao tu day duoc goi tu duong "
                           "quyet dinh. Doc, hieu, roi KHAI BAO LAI bang tay.",
        # Truy van NGAN. Ghep bang AND nen moi tu them vao la mot rang buoc
        # nua; sau tu thi gan nhu chac chan ra rong.
        "truy_van": ["backtest overfitting", "deflated sharpe ratio",
                     "multiple testing finance"],
        "sao_toi_thieu": 50,
    },
    "phuong_phap_chi_phi_giao_dich": {
        "vi_sao": "Chi phi qua dem la thu quyet dinh cua ca du an (do that: "
                  "4-7%/nam), va mo hinh cua ta tu dung. Ai do da lam ky hon.",
        "cam_vao": "KHONG cam vao dau ca",
        "doi_chieu_voi": "nhan/chi_phi.py",
        "khong_duoc_thay": "the he chi phi (THE_HE) doi thi phai quet lai TOAN "
                           "BO va tach chuoi FDR - khong duoc sua len tai cho",
        "truy_van": ["transaction cost slippage", "market impact execution"],
        "sao_toi_thieu": 50,
    },
    "thu_thap_web": {
        "vi_sao": "reddit bi chan DNS tren may nay; nhieu nguon can dang nhap.",
        "cam_vao": "nhan/doc_trinh_duyet.py",
        "khong_duoc_thay": "khong lien quan den cong PASS",
        "truy_van": ["playwright scraping anti detection stealth language:python"],
        "sao_toi_thieu": 300,
    },
    "doc_ma_chien_luoc": {
        "vi_sao": "12/18 chien luoc .mq5 da tai ve khong co template tuong ung. "
                  "Bo phan tich ma co the rut duoc luat vao/ra.",
        "cam_vao": "nhan/ma_nguon.py + nhan/ngu_phap.py",
        "khong_duoc_thay": "ngu phap co che - kien thuc moi chi vao bang KHAI BAO",
        "truy_van": ["mql5 expert advisor parser", "pine script parser language:python"],
        "sao_toi_thieu": 30,
    },
}

#: NHU CAU SINH RA TU MOT VAN DE DANG MO TRONG SO.
#:
#: Khac `NHU_CAU` (tinh, viet mot lan): nhung muc duoi day chi duoc kich hoat
#: khi CO mot van de tuong ung dang MO. Het van de thi het nhu cau, va suat tim
#: kiem tra ve cho truy van khac.
#:
#: Vi sao phai KHAI BAO TRUOC thay vi de LLM sinh truy van tu van de: mot truy
#: van do LLM viet ra tu chinh chan doan cua no la vong tron tu xac nhan, va no
#: cung khong the kiem lai duoc. O day nguoi viet anh xa, may chi chay no.
NHU_CAU_TU_VAN_DE = {
    "nha_may_null_qua_nho": {
        "vi_sao": "Van de dang mo: nha may null chi 10 ca, 1 tai san (EURCAD), "
                  "1 khung (H4). Voi 0/10 lot, chan tren khoang tin cay 95% van "
                  "la ~26% - so lieu do KHONG phan biet duoc 'cong hieu chuan "
                  "5%' voi 'cong tu choi 100%'. Can cach sinh chuoi null giu "
                  "duoc tinh chat chuoi that (tu tuong quan, cum bien dong).",
        "cam_vao": "KHONG cam vao dau ca - doi chieu tu ben ngoai",
        "doi_chieu_voi": "nhan/nha_may_null.py",
        "khong_duoc_thay": "khong mot dong nao duoc goi tu duong quyet dinh; "
                           "chuoi null cua he van do nhan/nha_may_null.py sinh, "
                           "cong cu ngoai chi de doi chieu phan phoi",
        "truy_van": ["surrogate time series bootstrap",
                     "stationary block bootstrap financial"],
        "sao_toi_thieu": 30,
        "duong": ["arxiv", "github"],
    },
    "do_luc_cong": {
        "vi_sao": "Van de dang mo: cong loai sach ca gia thuyet DA vuot FDR. "
                  "'Null lot 0%' mot minh khong phan biet duoc cong hieu chuan "
                  "tot voi cong tu choi tat ca - can thuoc do LUC doc lap "
                  "(deflated Sharpe, haircut Sharpe, Minimum Track Record) de "
                  "biet nguong cua ta co qua tay khong.",
        "cam_vao": "KHONG cam vao dau ca - chay ngoai, doc lap",
        "doi_chieu_voi": "nhan/cong.py, nhan/do_luc.py",
        "khong_duoc_thay": "hai ban tinh doc lap cung mot con so roi so ket "
                           "qua. Khong mot dong nao cua no duoc goi tu duong "
                           "quyet dinh, va no khong duoc doi mot nguong nao.",
        "truy_van": ["haircut sharpe ratio multiple testing",
                     "minimum track record length sharpe"],
        "sao_toi_thieu": 30,
        "duong": ["arxiv", "github"],
    },
    "p_value_chuoi_chong_lan": {
        "vi_sao": "Van de dang mo: p cua ung vien lech han khoi null (trung vi "
                  "0,325 thay vi 0,5; 18% duoi 0,05 thay vi 5%). Hai kha nang "
                  "chua tach duoc: co tin hieu that bi chan, hoac p bi thoi do "
                  "bar chong lan / kiem dinh phu thuoc. Day la bai toan thong "
                  "ke chuan, da co nguoi giai.",
        "cam_vao": "KHONG cam vao dau ca - doi chieu tu ben ngoai",
        "doi_chieu_voi": "nhan/cong.py",
        "khong_duoc_thay": "khong duoc doi cach tinh p cua he bang mot thu vien "
                           "ngoai; chi duoc DOC de biet ta sai o dau roi khai "
                           "bao lai bang tay",
        "truy_van": ["overlapping observations inference bias",
                     "hansen hodrick newey west overlapping returns"],
        "sao_toi_thieu": 20,
        "duong": ["arxiv"],
    },
    "nguon_im_lang": {
        "vi_sao": "Van de dang mo: co nguon BAT, da goi, khong nem loi va "
                  "khong thu duoc gi. Loi=0 nen no khong hien o dem loi - dung "
                  "hinh dang 'hong im lang' ma nhan/do_tai_nguyen.py sinh ra de "
                  "chong.",
        "cam_vao": "tru/seeker.py - lop goi nguon",
        "khong_duoc_thay": "khong duoc tu tat mot nguon; chi duoc do va bao",
        "truy_van": ["detect silent api failure empty response",
                     "python requests retry rate limit detection"],
        "sao_toi_thieu": 0,
        "duong": ["dien_dan"],
    },
    "supervisor_chet_im_lang": {
        "vi_sao": "Van de dang mo: supervisor chet va khoi dong lai lien tuc. "
                  "Do that 31/08/2026: ~12 lan/gio, nguyen nhan la `os.replace` "
                  "len file lease dang bi watchdog MO (WinError 5 - Windows "
                  "khoa file dang mo, POSIX thi khong). Trieu chung duy nhat "
                  "hien ra la `rc=1`, khong mot traceback nao ton tai o dau. "
                  "Ta chua co cach BIET ngay khi vong lap chet-restart bat dau.",
        "cam_vao": "dieu_phoi.py - lop giam sat tien trinh",
        "khong_duoc_thay": "khong duoc tu khoi dong lai mot tru dang giua mot "
                           "phep ghi so cai; khong duoc doi cach cham lease",
        "truy_van": ["atomic file replace windows permission error",
                     "python crash loop detection restart backoff"],
        "sao_toi_thieu": 0,
        "duong": ["dien_dan"],
    },
    "dia_va_tick_test": {
        "vi_sao": "Van de dang mo: dia tut duoi 15 GB nen buoc kiem dinh quyet "
                  "dinh (MT5 tick-test) bi KHOA. Khong co tick-test that thi "
                  "khong xac nhan duoc con so nao (CLAUDE.md muc 40).",
        "cam_vao": "cong cu ngoai, chay canh day chuyen - khong nhap vao ma",
        "khong_duoc_thay": "khong duoc tu xoa du lieu gia hay so cai; chi don "
                           "cache va thu muc tam da khai bao",
        "truy_van": ["find large files disk usage windows cli",
                     "chrome profile cache bloat cleanup"],
        "sao_toi_thieu": 0,
        "duong": ["dien_dan"],
    },
}

#: MA VAN DE -> NHU CAU. Mot nhu cau co the duoc nhieu ma van de kich hoat
#: (cung mot phat hien, hai duong phat hien khac nhau: mot cua `phat_hien`
#: viet tay, mot cua chan doan LLM da duoc khu trung ve chu de chuan).
#:
#: Ma `vd_*` la ma CHU DE CHUAN cua `tru/evolution.py: CHU_DE_VAN_DE`. Hai file
#: dung chung chuoi nay; `test_san_cong_cu` khoa lai de khong ai doi mot ben.
VAN_DE_SANG_NHU_CAU = {
    "vd_null_qua_nho": "nha_may_null_qua_nho",
    "chua_hieu_chuan_null": "nha_may_null_qua_nho",
    "vd_cong_loai_sach_fdr": "do_luc_cong",
    "cong_khong_co_luc": "do_luc_cong",
    "cong_co_the_qua_chat": "do_luc_cong",
    "vd_p_ung_vien_lech_null": "p_value_chuoi_chong_lan",
    "vd_nguon_im_lang": "nguon_im_lang",
    "nguon_khong_thu_hoach": "nguon_im_lang",
    "vd_tick_test_bi_khoa": "dia_va_tick_test",
    "dia_thap": "dia_va_tick_test",
    # Them 31/08 sau khi bat duoc nguyen nhan goc cua "thoi gian song 0,0%".
    "supervisor_restart_lien_tuc": "supervisor_chet_im_lang",
    "dieu_phoi_khong_cham_duoc_lease": "supervisor_chet_im_lang",
    "dieu_phoi_chet_khong_bat": "supervisor_chet_im_lang",
}

#: Muc van de duoc phep sinh nhu cau san. VUA/NHE khong duoc: mot suat tim
#: kiem la co han, va "cai gi cung dang di tim" thi khong khac gi khong tim.
MUC_SINH_NHU_CAU = ("NANG",)


def nhu_cau_tu_van_de(van_de_mo: list[dict] | None) -> dict:
    """Van de dang MO muc NANG -> nhu cau ky thuat -> truy van san.

    Tra ve dict cung hinh dang `NHU_CAU` de `mot_luot` dung chung mot duong.
    Moi muc duoc gan them `tu_van_de` (danh sach ma van de da kich hoat no) de
    bao cao noi duoc VI SAO truy van nay co mat.

    Tra `{}` khi khong co van de nao khop - do la cau tra loi THAT. Tra `{}`
    khi `van_de_mo` la None cung the, nhung `mot_luot` phan biet hai truong
    hop bang `da_doc_van_de`.
    """
    ra: dict = {}
    for v in (van_de_mo or []):
        if (v.get("muc") or "").upper() not in MUC_SINH_NHU_CAU:
            continue
        khoa = VAN_DE_SANG_NHU_CAU.get(v.get("ma") or "")
        if not khoa or khoa not in NHU_CAU_TU_VAN_DE:
            continue
        if khoa not in ra:
            ra[khoa] = dict(NHU_CAU_TU_VAN_DE[khoa])
            ra[khoa]["tu_van_de"] = []
        ra[khoa]["tu_van_de"].append(v["ma"])
    return ra


#: HANG DOI DOC - kho ma da nam trong kho cong cu, can NGUOI doc de DOI CHIEU
#: voi cong (khong bao gio de thay cong). Chu du an chot 30/08/2026.
#:
#: Day khong phai "cong cu de tich hop": ba trong bon muc duoi la ban cai dat
#: cua chinh nhung phep tinh ma `nhan/cong.py` tu viet. Doc chung la cach duy
#: nhat biet ta co tu che ra luat rieng hay khong.
HANG_DOI_DOC = [
    {"khop": "quantopian/zipline", "doi_chieu_voi": "nhan/chi_phi.py, nhan/mo_phong.py",
     "vi_sao": "mo hinh truot gia + phi giao dich cua mot engine 20.041 sao; "
               "mo hinh chi phi cua ta tu viet va la thu quyet dinh ca du an"},
    {"khop": "OutOfSampleLab/oos-lab", "doi_chieu_voi": "nhan/cong.py, nhan/do_luc.py",
     "vi_sao": "haircut Sharpe - doi chieu voi nguong FDR LORD ta tu viet"},
    {"khop": "0scarito/deflated-alpha", "doi_chieu_voi": "nhan/cong.py",
     "vi_sao": "deflated Sharpe - chieu LUC cua hieu chuan hai chieu"},
    {"khop": "quantskills/skill-backtest-overfit", "doi_chieu_voi": "nhan/do_luc.py",
     "vi_sao": "Minimum Track Record Length - do 'bao nhieu quan sat moi du ket "
               "luan', dung bai toan MDE cua ta"},
]


def xep_hang_doc(kho: dict | None = None) -> list[str]:
    """Danh dau cac kho ma trong HANG_DOI_DOC la CHO_DOC trong kho cong cu.

    KHONG tai gi, KHONG tich hop gi, KHONG doi mot nguong nao: chi doi mot
    truong `trang_thai` tu MOI sang CHO_DOC va ghi kem `doi_chieu_voi`. Dao
    nguoc bang mot phep gan nguoc lai.

    Tra ve danh sach ten vua duoc xep hang (rong neu tat ca da xep roi).
    """
    tu_luu = kho is None
    kho = doc_kho() if tu_luu else kho
    moi = []
    for m in HANG_DOI_DOC:
        khop = m["khop"].lower()

        def _trung(khoa, v, _k=khop):
            ten = str(v.get("full_name") or v.get("url") or khoa)
            return _k in ten.lower() or _k in khoa.lower()

        # Da co mot ban ghi cua kho ma nay dang CHO_DOC thi thoi. Thieu chot
        # nay thi moi luot lai danh dau THEM mot ban ghi trung ten khac khoa
        # (kho co nhieu ban ghi cho cung mot kho ma, nhat tu nhieu bai doc),
        # va hang doi doc phinh len o moi luot.
        if any(v.get("trang_thai") == "CHO_DOC" and _trung(k, v)
               for k, v in kho.items()):
            continue
        for khoa, v in kho.items():
            if not _trung(khoa, v):
                continue
            v["trang_thai"] = "CHO_DOC"
            v["doi_chieu_voi"] = m["doi_chieu_voi"]
            v["vi_sao_doc"] = m["vi_sao"]
            v["xep_hang_luc"] = SO.bay_gio()
            moi.append(m["khop"])
            break
    if moi and tu_luu:
        luu_kho(kho)
    return moi


def dang_cho_doc(kho: dict | None = None) -> list[dict]:
    """Danh sach dang cho nguoi doc. Doc thuan tuy, khong ghi gi."""
    kho = doc_kho() if kho is None else kho
    return [{"ten": v.get("full_name") or v.get("url"),
             "doi_chieu_voi": v.get("doi_chieu_voi"),
             "vi_sao": v.get("vi_sao_doc")}
            for v in kho.values() if v.get("trang_thai") == "CHO_DOC"]


# ============================================================= SO TRUY VAN
#: Nhat ky tung truy van da san. Tach khoi `cong_cu.json` co chu y: kho la
#: danh sach KET QUA, so nay la danh sach VIEC DA LAM. Truoc 31/08 chi co cai
#: dau, nen mot truy van khong ra ket qua khong de lai vet nao va bi thu lai
#: mai mai.
def _duong_so_truy_van() -> Path:
    return KHO.with_name("cong_cu_truy_van.json")


#: Bao lau moi thu lai mot truy van, theo KET QUA lan truoc.
#:
#: `RONG` khong phai su co - do la cau tra loi "khong ai viet ve chuyen nay".
#: Thu lai sau 14 ngay la du. `LOI` la su co moi truong (mang, rate limit) nen
#: thu lai o luot sau. Tron hai muc nay lam mot la dung cai bay ma
#: `test_HOI_DUOC_ma_khong_co_gi_thi_tra_RONG_chu_khong_phai_LOI` da chan o
#: muc `tim_dien_dan`, nhung con ho o muc `mot_luot`.
CHU_KY_THU_LAI = {"CO_KET_QUA": 30 * 86400, "RONG": 14 * 86400, "LOI": 3600}


def doc_so_truy_van() -> dict:
    try:
        return json.loads(_duong_so_truy_van().read_text(encoding="utf-8"))
    except Exception:
        return {}


def luu_so_truy_van(d: dict) -> None:
    p = _duong_so_truy_van()
    p.parent.mkdir(exist_ok=True)
    tam = p.with_suffix(".json.tam")
    tam.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tam.replace(p)


def _den_han_truy_van(tv: str, so: dict, da_co_trong_kho: set) -> bool:
    """Truy van nay den luot chua?"""
    g = so.get(tv)
    if not g:
        # Tuong thich nguoc: truy van chay TRUOC khi co so nay. Neu no da tung
        # de lai ket qua trong kho thi coi nhu CO_KET_QUA va chua den han;
        # nguoc lai coi nhu chua thu bao gio.
        return tv not in da_co_trong_kho
    try:
        cu = time.mktime(time.strptime(g.get("luc", ""), "%Y-%m-%d %H:%M:%S"))
    except Exception:
        return True
    ket = g.get("ket") or "LOI"
    # Mot duong hong ma duong kia tra ve rong: van ghi RONG (co duong tra loi
    # duoc), nhung THU LAI SOM nhu LOI - vi cai duong hong co the chinh la
    # duong duy nhat co cau tra loi cho truy van do.
    if g.get("duong_hong"):
        ket = "LOI"
    return (time.time() - cu) >= CHU_KY_THU_LAI.get(ket, 3600)


#: Cong cu do chu du an chi thang. Vao kho khong qua API.
GIEO_TAY = [
    {"full_name": "hoainama8/convertOCR", "nhu_cau": "doc_pdf",
     "ghi_chu": "chu du an chi 30/08. Server Go, PDF -> md/json/html/docx/csv. "
                "OCR can cgo. Dung duoc nhu dich vu ngoai tien trinh."},
    {"full_name": "coding-kitties/investing-algorithm-framework",
     "nhu_cau": "engine_backtest",
     "ghi_chu": "chu du an chi 30/08. 2.022 sao, Apache-2.0. Hai engine "
                "(vector + su kien), 50+ chi so, sweep, kiem dinh nhieu cua so, "
                "Monte Carlo permutation, bao cao HTML, CCXT. "
                "KHONG co FDR chuong trinh / dang ky truoc / MDE / canary."},
]


# =============================================================== NHAT DOC DUONG
#: DAU HIEU cua mot cong cu nang cap duoc, tim NGAY TRONG van ban SEEKER da doc.
#:
#: Day moi la duong chinh, khong phai `tim_github`. Ly do: SEEKER **da** di qua
#: hang nghin kho ma va bai viet de san chien luoc. Thu khong phai chien luoc
#: thi hien bi bo di - trong khi `bien_dich_ung_vien.loai_ma_nguon` do duoc
#: 24/08 rang **34/52 file .mq5 la `tien_ich` hoac `chi_bao`**, tuc phan lon
#: nhung gi cham vao deu khong phai chien luoc. Trong so do co nhung thu nang
#: cap duoc chinh cai may nay.
#:
#: Nhat doc duong thi khong ton mot lan tai trang nao: van ban da nam trong so.
#:
#: KHOP THEO CUM CO RANH GIOI TU, khong khop chuoi tho. Da sap that tren chinh
#: kho nay: `rsi` khop trong **Ve-rsi-on** -> 117/156 tai lieu "co RSI".
DAU_HIEU = {
    "doc_pdf": [r"pdf\s+to\s+markdown", r"extract\s+text\s+from\s+pdf",
                r"\bpdfplumber\b", r"\bpymupdf\b", r"\bpdfminer\b",
                r"\blayout\s+aware\s+pdf\b", r"\bdocling\b"],
    "engine_backtest": [r"\bbacktest(?:ing)?\s+engine\b",
                        r"\bvectori[sz]ed\s+backtest", r"\bevent[- ]driven\s+backtest",
                        r"\bwalk[- ]forward\s+(?:analysis|optimi[sz]ation)\b"],
    "kiem_dinh_thong_ke": [r"\bfalse\s+discovery\s+rate\b", r"\bdeflated\s+sharpe\b",
                           r"\bmultiple\s+(?:hypothesis\s+)?testing\b",
                           r"\bpurged\s+(?:k[- ]fold|cross[- ]validation)\b",
                           r"\bcombinatorial\s+purged\b",
                           r"\bprobability\s+of\s+backtest\s+overfitting\b",
                           r"\breality\s+check\b", r"\bwhite'?s\s+reality\b",
                           r"\bbenjamini[- ]hochberg\b"],
    "thu_thap_web": [r"\bundetected[- ]chromedriver\b", r"\bplaywright[- ]stealth\b",
                     r"\banti[- ]?bot\s+detection\b", r"\bcloudflare\s+bypass\b"],
    # Dau hieu muc PHUONG PHAP: mot bo loc / phep hieu chuan / cai bay da co
    # nguoi mo ta, khong phai mot goi de `pip install`. Kho hien co CO san
    # chung: do 30/08 tren 923 ban doc - 23 ban co "deflated sharpe",
    # 39 ban "market impact", 8 ban "data snooping", 7 ban "superior predictive".
    "phuong_phap_chong_qua_khop": [
        r"\bdata\s+snooping\b",
        r"\bp[- ]hacking\b",
        r"\bfamily[- ]wise\s+error\b",
        r"\bsuperior\s+predictive\s+ability\b",
        r"\bhaircut\s+sharpe\b",
        r"\bminimum\s+track\s+record\b",
        r"\bwhite'?s\s+bootstrap\b",
    ],
    "phuong_phap_chi_phi_giao_dich": [
        r"\bmarket\s+impact\s+model\b",
        r"\bimplementation\s+shortfall\b",
        r"\bslippage\s+model\b",
        r"\balmgren[- ]chriss\b",
        r"\beffective\s+spread\b",
        r"\bovernight\s+financing\b",
    ],
    "doc_ma_chien_luoc": [r"\bmql[45]\s+parser\b", r"\bpine\s*script\s+parser\b",
                          r"\bstrategy\s+(?:rule\s+)?extraction\b",
                          r"\bast\s+(?:based\s+)?(?:parser|analysis)\b"],
}

#: Van canh BAT BUOC quanh cum khop. Mot bai sinh hoc noi "reality check" khong
#: phai la cong cu kiem dinh. Cung nguyen tac voi `bien_dich_ung_vien`: chu
#: `strateg` da bi loai khoi danh sach van canh vi qua chung.
VAN_CANH = re.compile(
    r"(python|library|package|framework|repo|toolkit|module|pip install|"
    r"import |github|open[- ]source|cli|api|implementation)", re.I)

#: Khong nhat lai chinh minh, va khong nhat nhung thu da la chien luoc.
BO_QUA_URL = re.compile(r"(investing-algorithm-framework|/lab/|Research%20SP500)", re.I)

CUA_SO_VAN_CANH = 400


def xet_van_ban(tieu_de: str, van_ban: str, url: str = "",
                nguon: str = "") -> list[dict]:
    """Van ban nay co chua mot CONG CU nang cap duoc khong?

    Tra ve danh sach ung vien, moi ung vien kem **trich dan nguyen van + vi tri
    ky tu** - cung hop dong bang chung ma `CandidateArtifact` doi. Khong co
    trich dan thi khong co ung vien.

    Day KHONG phai ung vien chien luoc: no khong vao `candidate_queue`, khong
    tieu mot suat FDR nao, va khong bao gio tu dong duoc tich hop.
    """
    if not van_ban or len(van_ban) < 200:
        return []
    if url and BO_QUA_URL.search(url):
        return []
    ra: list[dict] = []
    da_co: set[str] = set()
    for nhu_cau, cac_mau in DAU_HIEU.items():
        for mau in cac_mau:
            m = re.search(mau, van_ban, re.I)
            if not m:
                continue
            i = m.start()
            quanh = van_ban[max(0, i - CUA_SO_VAN_CANH): i + CUA_SO_VAN_CANH]
            if not VAN_CANH.search(quanh):
                continue
            if nhu_cau in da_co:
                continue
            da_co.add(nhu_cau)
            ra.append({
                "nhu_cau": nhu_cau, "cum_khop": m.group(0),
                "vi_tri": i, "trich_dan": quanh.strip()[:360],
                "tieu_de": (tieu_de or "")[:160], "url": url, "nguon": nguon,
                "thay_luc": SO.bay_gio(), "trang_thai": "MOI",
                "nguon_phat_hien": "nhat_doc_duong",
            })
    return ra


def nhat_tu_ban_doc(tieu_de: str, van_ban: str, url: str = "",
                    nguon: str = "") -> int:
    """Xet mot ban doc va cat ung vien vao kho. Tra so ung vien MOI."""
    uv = xet_van_ban(tieu_de, van_ban, url, nguon)
    if not uv:
        return 0
    kho = doc_kho()
    them = 0
    for u in uv:
        khoa = f"doc:{u['nhu_cau']}:{url or tieu_de}"
        if khoa in kho:
            continue
        kho[khoa] = u
        them += 1
    if them:
        luu_kho(kho)
    return them


def quet_lai_thu_vien(gioi_han: int = 0, im_lang: bool = False) -> dict:
    """Nhat lai tren TOAN BO ban doc da co trong so.

    Chay mot lan sau khi them dau hieu moi: kho da co san hang tram ban doc,
    khong can tai lai gi.
    """
    cau = ("SELECT n.tieu_de_url, n.van_ban, n.url, n.nguon FROM ("
           "SELECT t.tieu_de AS tieu_de_url, n.van_ban, n.url, t.nguon "
           "FROM noi_dung n JOIN tai_lieu t ON t.id = n.tai_lieu_id "
           "WHERE n.so_ky_tu > 200) n")
    if gioi_han:
        cau += f" LIMIT {int(gioi_han)}"
    ds = SO.nhieu(cau)
    them, co = 0, 0
    for r in ds:
        n = nhat_tu_ban_doc(r["tieu_de_url"], r["van_ban"], r["url"], r["nguon"])
        them += n
        co += bool(n)
    if not im_lang:
        print(f"quet {len(ds)} ban doc -> {them} ung vien cong cu tu {co} ban")
    return {"ban_doc": len(ds), "ung_vien_moi": them, "ban_co_ung_vien": co}


# --------------------------------------------------------------------- KHO
def doc_kho() -> dict:
    try:
        return json.loads(KHO.read_text(encoding="utf-8"))
    except Exception:
        return {}


def luu_kho(d: dict) -> None:
    KHO.parent.mkdir(exist_ok=True)
    tam = KHO.with_suffix(".json.tam")
    tam.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tam.replace(KHO)


# ------------------------------------------------------------------- CHAM DIEM
def _tuoi_ngay(iso: str | None) -> float:
    if not iso:
        return 9_999.0
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - t).days
    except Exception:
        return 9_999.0


def cham_diem(r: dict) -> dict:
    """Diem 0-100. Khong phai phan xu — chi de xep thu tu cho NGUOI doc.

    Bon truc, moi truc toi da 25: dung nguoi (sao), con song (lan day cuoi),
    dung duoc (giay phep), va co ai kiem khong (issue/fork).
    """
    sao = int(r.get("stargazers_count") or 0)
    tuoi = _tuoi_ngay(r.get("pushed_at"))
    gp = ((r.get("license") or {}).get("spdx_id")) or "?"

    d_sao = min(25.0, 25.0 * (min(sao, 5000) / 5000) ** 0.45)
    d_song = 25.0 if tuoi <= 90 else 18.0 if tuoi <= 365 else 8.0 if tuoi <= 730 else 0.0
    d_gp = 25.0 if gp in GIAY_PHEP_OK else 10.0 if gp in GIAY_PHEP_LAY_NHIEM else 3.0
    d_cong = min(25.0, 25.0 * (min(int(r.get("forks_count") or 0), 400) / 400) ** 0.5)

    canh = []
    if gp in GIAY_PHEP_LAY_NHIEM:
        canh.append(f"giay phep {gp} LAY NHIEM - dung trong du an kin phai mo nguon theo")
    if gp == "?":
        canh.append("KHONG khai giay phep - khong duoc dua vao ma nguon du an")
    if tuoi > 730:
        canh.append(f"lan day cuoi {int(tuoi)} ngay truoc - co the da bo")
    return {"diem": round(d_sao + d_song + d_gp + d_cong, 1),
            "sao": sao, "tuoi_ngay": int(tuoi), "giay_phep": gp,
            "canh_bao": canh}


# ---------------------------------------------------------------------- TIM
def tim_github(truy_van: str, sao_toi_thieu: int = 100, so_luong: int = 8) -> list[dict]:
    import requests
    q = f"{truy_van} stars:>{sao_toi_thieu}"
    try:
        r = requests.get("https://api.github.com/search/repositories",
                         params={"q": q, "sort": "stars", "per_page": so_luong},
                         headers={"Accept": "application/vnd.github+json"}, timeout=25)
    except Exception as e:
        return [{"loi": f"{type(e).__name__}: {str(e)[:80]}"}]
    if r.status_code != 200:
        return [{"loi": f"HTTP {r.status_code}", "con_lai":
                 r.headers.get("x-ratelimit-remaining")}]
    return r.json().get("items", []) or []


def tim_huggingface(truy_van: str, so_luong: int = 8,
                    loai: str = "models") -> list[dict]:
    """Tim MO HINH / BO DU LIEU tren HuggingFace.

    Khac GitHub (tim mot goi de goi) va arXiv (tim mot phuong phap de doc): HF
    la cho co san TRONG SO da huan luyen. Voi The Brain chi co mot cho dung
    duoc, va no phai nam NGOAI duong ra quyet dinh:

      **xep thu tu doc**, khong phai sinh co che.

    Do 30/08/2026: trong 2.504 cau bo doc nhan la "luat vao", 42,0% la manh ma
    nguon va 44,7% la van tan gau — 87% cong doc bo vao rac. Mot bo phan loai
    van ban chi can tra loi "bai nay co ta mot luat khong" la du de doi thu tu
    doc. No khong sinh co che, khong cham cong, khong tieu suat FDR; doan sai
    thi hau qua toi da la doc nham thu tu.

    Hien phap cam `exec` ma LLM sinh va cam co che khong qua `ngu_phap`. Cai
    nay khong pham vi no khong tao ra dieu kien nao - no chi sap hang doi.
    """
    import requests
    duong = "https://huggingface.co/api/" + ("datasets" if loai == "datasets"
                                             else "models")
    try:
        r = requests.get(duong, params={"search": truy_van, "limit": so_luong,
                                        "sort": "downloads", "direction": -1},
                         timeout=25)
    except Exception as e:
        return [{"loi": f"{type(e).__name__}: {str(e)[:80]}"}]
    if r.status_code != 200:
        return [{"loi": f"HTTP {r.status_code}"}]
    ra = []
    for it in (r.json() or [])[:so_luong]:
        ten = it.get("id") or it.get("modelId") or ""
        if not ten:
            continue
        tags = it.get("tags") or []
        # HF khong tra `license` / `pushed_at` nhu GitHub: giay phep nam trong
        # tag dang "license:apache-2.0", con ngay sua o `lastModified`. Khong
        # anh xa thi `cham_diem` doc ra "khong khai giay phep" va "lan day cuoi
        # 9999 ngay truoc" cho MOI mo hinh - tuc no phat oan ca mot nguon.
        gp = next((t.split(":", 1)[1] for t in tags
                   if isinstance(t, str) and t.startswith("license:")), None)
        ra.append({
            "full_name": ten,
            "html_url": f"https://huggingface.co/{'datasets/' if loai == 'datasets' else ''}{ten}",
            "description": ", ".join(str(t) for t in tags[:8])[:300],
            "stargazers_count": int(it.get("downloads") or 0),
            "forks_count": int(it.get("likes") or 0),
            "license": {"spdx_id": gp} if gp else None,
            "pushed_at": it.get("lastModified") or it.get("createdAt"),
            "_nguon": "huggingface"})
    return ra


def tim_dien_dan(truy_van: str, so_luong: int = 8) -> list[dict]:
    """Tim tren DIEN DAN KY THUAT (Hacker News, Stack Overflow, Lobsters).

    Duong thu tu, va no khac ba duong kia ve BAN CHAT cai tim duoc:

      GitHub      -> mot goi de goi
      arXiv       -> mot phuong phap de doc
      HuggingFace -> mot bo trong so da huan luyen
      **Dien dan  -> mot KINH NGHIEM: cai gi cham, vi sao, ai da vap**

    Hai nguon: Hacker News (Algolia) va Stack Overflow. Ca hai da do that
    la vao duoc tu may nay ngay 30/08/2026.

    Phan lon nut that cua The Brain khong giai bang mot thu vien moi ma bang
    mot cau "hoa ra `os.stat` goi 80.000 lan/phut". Do la thu chi nam trong
    bai viet va cau tra loi cua nguoi khac.

    EVO nam RONG HON linh vuc giao dich (chu du an chi 30/08/2026): phan lon
    van de cua ta la van de TIN HOC thuong - I/O, bo nho, song song, cache -
    va cong dong giai quyet chung tu lau roi.

    Diem: HN lay `points`, SO lay `score`. Deu quy ve `stargazers_count` de
    `cham_diem` doc duoc mot cach duy nhat.
    """
    import json as _json
    import urllib.parse as _up
    import urllib.request as _ur

    # `voi_toi` dem so dien dan TRA LOI DUOC (khac so dien dan CO KET QUA).
    # Hai cau phai tach bach: "khong dien dan nao voi toi duoc" la loi moi
    # truong va phai thu lai; "ca hai dien dan deu tra ve rong" la cau tra loi
    # THAT cho truy van do. Tron hai cau lai la cach du an nay da nhieu lan tu
    # tin vao mot dieu no chua kiem.
    trang_thai = {"voi_toi": 0, "hong": []}

    def _lay(u, ten):
        try:
            rq = _ur.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            with _ur.urlopen(rq, timeout=25) as f:
                txt = f.read().decode("utf-8", "replace")
            trang_thai["voi_toi"] += 1
            return txt
        except Exception as e:
            trang_thai["hong"].append(f"{ten}: {type(e).__name__}")
            return None

    q = _up.quote(truy_van)
    ra: list[dict] = []

    txt = _lay(f"https://hn.algolia.com/api/v1/search?query={q}"
               f"&tags=story&hitsPerPage={so_luong}", "hackernews")
    if txt:
        try:
            for it in _json.loads(txt).get("hits", [])[:so_luong]:
                ten = (it.get("title") or "").strip()
                if not ten:
                    continue
                ra.append({
                    "full_name": f"HN: {ten}"[:120],
                    "html_url": it.get("url") or
                    f"https://news.ycombinator.com/item?id={it.get('objectID')}",
                    "description": (it.get("story_text") or "")[:300],
                    "stargazers_count": int(it.get("points") or 0),
                    "forks_count": int(it.get("num_comments") or 0),
                    "license": None, "pushed_at": it.get("created_at"),
                    "_nguon": "hackernews"})
        except Exception:
            pass

    txt = _lay("https://api.stackexchange.com/2.3/search/advanced?order=desc"
               f"&sort=votes&q={q}&site=stackoverflow&pagesize={so_luong}",
               "stackoverflow")
    if txt:
        try:
            for it in _json.loads(txt).get("items", [])[:so_luong]:
                ten = (it.get("title") or "").strip()
                if not ten:
                    continue
                ra.append({
                    "full_name": f"SO: {ten}"[:120],
                    "html_url": it.get("link") or "",
                    "description": ", ".join(it.get("tags", [])[:8])[:300],
                    "stargazers_count": int(it.get("score") or 0),
                    "forks_count": int(it.get("answer_count") or 0),
                    "license": None, "pushed_at": None,
                    "_nguon": "stackoverflow"})
        except Exception:
            pass

    # Lobsters: DA BO. `search.json` tra HTTP 400 - trang khong co endpoint
    # tim kiem dang JSON. Giu mot loi goi luon hong chi lam nhieu nhat ky va
    # ton mot vong mang moi luot.
    if ra:
        return ra
    if trang_thai["voi_toi"] == 0:
        return [{"loi": "khong dien dan nao voi toi duoc ("
                 + ", ".join(trang_thai["hong"]) + ")"}]
    return []          # da hoi duoc, that su khong co gi - KHONG phai loi


# ------------------------------------------------------- TIM CONG TRINH
def tim_arxiv(truy_van: str, so_luong: int = 8) -> list[dict]:
    """Tim BAI BAO, khong tim kho ma.

    Nhu cau nao khai `doi_chieu_voi` la nhu cau PHUONG PHAP - cai ta can la mot
    bo loc / mot phep hieu chuan / mot cai bay da co nguoi mo ta, khong phai mot
    goi de `pip install`. GitHub khong phai cho tim nhung thu do.

    Bai bao khong co sao, khong co giay phep, khong co "lan day cuoi", nen
    `cham_diem` (do suc khoe kho ma) khong ap duoc: chung mang `diem=None` va
    duoc xep theo NGAY, roi nguoi doc quyet.

    Dung `requests` chu khong `urllib` tran: WARP dang bat va urllib khong co
    chung chi -> `CERTIFICATE_VERIFY_FAILED`. `tru/seeker.n_arxiv` da di duong
    nay tu lau va chay tot.
    """
    import re as _re
    import urllib.parse
    try:
        import requests
    except Exception as e:
        return [{"loi": f"{type(e).__name__}"}]
    # HAI CAI BAY, ca hai deu tra HTTP 200 kem KHONG MOT <entry> nao - im lang,
    # khong bao mot loi nao:
    #   1. Ma hoa dau hai cham cua `all:` thanh %3A -> arXiv khong hieu truy van.
    #   2. Boc CA CUM vao ngoac kep -> arXiv tim DUNG NGUYEN CUM. Cum bon tu nhu
    #      "backtest overfitting multiple testing" khong bai nao co nguyen van.
    # Nen: ghep TUNG TU bang AND, va giu nguyen dau hai cham.
    tu = [x for x in truy_van.split() if len(x) > 2][:6]
    if not tu:
        return []
    q = "+AND+".join("all:" + urllib.parse.quote(x) for x in tu)
    url = ("http://export.arxiv.org/api/query?search_query=" + q +
           f"&start=0&max_results={so_luong}"
           "&sortBy=submittedDate&sortOrder=descending")
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent": "TheBrain/1.0"})
        if r.status_code != 200:
            return [{"loi": f"HTTP {r.status_code}"}]
        xml = r.text
    except Exception as e:
        return [{"loi": f"{type(e).__name__}: {str(e)[:80]}"}]

    khoang = _re.compile(r"\s+")
    ra = []
    for muc in _re.findall(r"<entry>(.*?)</entry>", xml, _re.S):
        def _lay(the, _m=muc):
            m = _re.search(rf"<{the}>(.*?)</{the}>", _m, _re.S)
            return khoang.sub(" ", m.group(1)).strip() if m else ""
        ten = _lay("title")
        if not ten:
            continue
        ra.append({"full_name": ten[:130], "html_url": _lay("id"),
                   "description": _lay("summary")[:300],
                   "ngay": _lay("published")[:10], "la_bai_bao": True})
    return ra


def _gon(r: dict, nhu_cau: str, truy_van: str) -> dict:
    # Bai bao khong co sao/giay phep/lan day cuoi -> cham diem suc khoe kho ma
    # la vo nghia. Tra `diem=None` chu khong tra 0: 0 nghia la "do duoc va rat
    # te", None nghia la "khong do duoc bang thuoc nay". Cung nguyen tac voi
    # `do_tai_nguyen`.
    d = ({"diem": None, "canh_bao": [], "ngay": r.get("ngay")}
         if r.get("la_bai_bao") else cham_diem(r))
    return {
        "full_name": r.get("full_name"), "url": r.get("html_url"),
        "mo_ta": (r.get("description") or "")[:220],
        "ngon_ngu": r.get("language"), "nhu_cau": nhu_cau, "truy_van": truy_van,
        "loai": "bai_bao" if r.get("la_bai_bao") else "kho_ma",
        "thay_luc": SO.bay_gio(), "trang_thai": "MOI", **d,
    }


# ------------------------------------------------------------------ MOT LUOT
def _duong_cua(nc: dict) -> list[str]:
    """Nhu cau nay di duong nao. Tach ra de `mot_luot` doc duoc mot dong."""
    duong = nc.get("duong")
    if duong:
        return list(duong)
    # Nhu cau khai `doi_chieu_voi` = nhu cau PHUONG PHAP -> tim BAI BAO.
    # Nhu cau con lai = can mot goi chay duoc -> tim KHO MA.
    return (["dien_dan"] if nc.get("tren_dien_dan") else
            ["hugging"] if nc.get("tren_hugging") else
            ["arxiv"] if nc.get("doi_chieu_voi") else ["github"])


def _san_mot_truy_van(nc: dict, tv: str) -> tuple[list, dict]:
    """San MOT truy van tren moi duong cua nhu cau.

    Tra `(ket_qua_that, thong_ke)`. `thong_ke["ket"]` la mot trong ba:

      CO_KET_QUA - hoi duoc va co thu
      RONG       - hoi duoc, that su khong co gi. **Day la CAU TRA LOI.**
      LOI        - khong duong nao voi toi duoc. Day moi la su co.

    Ba trang thai nay phai tach bach. Ban truoc 31/08 gop RONG vao LOI (dong
    `ds[:1] or [{"loi": "khong duong nao tra ve"}]`), va do la ly do luot san
    gan nhat bao `loi=3` trong khi ca ba truy van deu chay tot - GitHub va hai
    dien dan deu tra loi, chi la khong co ket qua nao khop.
    """
    that: list = []
    duong_hong: list[str] = []
    duong_tra_loi = 0
    for d in _duong_cua(nc):
        if d == "dien_dan":
            ds = tim_dien_dan(tv)
        elif d == "hugging":
            ds = tim_huggingface(tv)
        elif d == "arxiv":
            ds = tim_arxiv(tv)
        else:
            ds = tim_github(tv, nc.get("sao_toi_thieu", 100))
        hong = [x for x in ds if "loi" in x]
        if hong:
            duong_hong.append(f"{d}: {hong[0]['loi']}")
            continue
        duong_tra_loi += 1
        that += ds
    if duong_tra_loi == 0:
        ket = "LOI"
    elif not that:
        ket = "RONG"
    else:
        ket = "CO_KET_QUA"
    # `so_tu` + `sao_toi_thieu` di kem KET QUA co chu y. GitHub ghep tu bang
    # AND: moi tu them vao la mot rang buoc nua, va do that 31/08 cho thay
    # "numba vectorized backtest speedup" + `stars:>800` ra DUNG 0 kho trong
    # khi "numba backtest" + `stars:>100` cung ra 0 nhung "polars time series"
    # + `stars:>300` ra 2. Khong co hai con so nay thi moi lan doc so lai
    # phai doan xem RONG la vi khong ai viet, hay vi truy van qua chat.
    return that, {"ket": ket, "so_ket_qua": len(that),
                  "duong_hong": duong_hong, "luc": SO.bay_gio(),
                  "so_tu": len(tv.split()),
                  "sao_toi_thieu": nc.get("sao_toi_thieu")}


def mot_luot(gioi_han_truy_van: int = 5, im_lang: bool = False,
             van_de_mo: list[dict] | None = None) -> dict:
    """San mot luot. Ton it nhat co the: GitHub search khong khoa cho 10 lan/phut.

    `van_de_mo`: danh sach van de dang mo trong so (EVO truyen vao). Van de muc
    NANG co anh xa trong `VAN_DE_SANG_NHU_CAU` se sinh ra nhu cau san **duoc uu
    tien di truoc** danh sach tinh. Khong truyen thi chi san theo `NHU_CAU`.

    Tra ve:
      tim_them  so muc moi vao kho, hoac **None** khi khong thu duoc truy van
                nao (khong do duoc != do duoc bang 0)
      loi       so truy van that su hong (khong duong nao voi toi duoc)
      rong      so truy van hoi duoc ma khong co ket qua - KHONG phai loi
      da_thu    so truy van da chay luot nay
      con_cho   so truy van da khai bao nhung chua den han thu lai
    """
    kho = doc_kho()

    for g in GIEO_TAY:
        if g["full_name"] not in kho:
            kho[g["full_name"]] = {
                "full_name": g["full_name"],
                "url": f"https://github.com/{g['full_name']}",
                "nhu_cau": g["nhu_cau"], "truy_van": "chu du an chi",
                "mo_ta": g["ghi_chu"], "thay_luc": SO.bay_gio(),
                "trang_thai": "MOI", "diem": None, "nguon": "nguoi_chi"}

    # NHU CAU DONG di truoc NHU CAU TINH: mot van de dang mo la bang chung
    # manh hon mot danh sach viet tu thang truoc.
    dong = nhu_cau_tu_van_de(van_de_mo)
    bang_nhu_cau = {**NHU_CAU, **dong}
    thu_tu = [(k, tv) for k, v in dong.items() for tv in v["truy_van"]]
    thu_tu += [(k, tv) for k, v in NHU_CAU.items() for tv in v["truy_van"]]

    so_tv = doc_so_truy_van()
    da_co_trong_kho = {v.get("truy_van") for v in kho.values()}
    da_xet: set[str] = set()
    ung_vien = []
    for k, tv in thu_tu:
        if tv in da_xet:
            continue
        da_xet.add(tv)
        if _den_han_truy_van(tv, so_tv, da_co_trong_kho):
            ung_vien.append((k, tv))
    con_cho = len(da_xet) - len(ung_vien)
    # Chua thu bao gio di truoc; con lai xep theo lan thu CU NHAT -> hang doi
    # xoay vong thay vi dam vao dung ba truy van dau danh sach.
    ung_vien.sort(key=lambda x: so_tv.get(x[1], {}).get("luc") or "")
    viec = ung_vien[:gioi_han_truy_van]

    moi, loi, rong = 0, 0, 0
    for i, (nhu_cau, tv) in enumerate(viec):
        if i:
            time.sleep(NGHI_GIAY)
        ds, tk = _san_mot_truy_van(bang_nhu_cau[nhu_cau], tv)
        tk["nhu_cau"] = nhu_cau
        so_tv[tv] = tk
        if tk["ket"] == "LOI":
            loi += 1
            if not im_lang:
                print(f"  [LOI ] {tv[:52]:52s} {'; '.join(tk['duong_hong'])[:60]}")
            continue
        them = 0
        for r in ds:
            ten = r.get("full_name")
            if not ten or ten in kho:
                continue
            kho[ten] = _gon(r, nhu_cau, tv)
            them += 1
        moi += them
        if tk["ket"] == "RONG":
            rong += 1
            if not im_lang:
                print(f"  [RONG] {tv[:52]:52s} hoi duoc, khong co ket qua nao")
        elif not im_lang:
            print(f"  [{them:2d} moi] {tv[:52]:52s} ({len(ds)} ket qua)")

    xep_hang_doc(kho)
    luu_kho(kho)
    luu_so_truy_van(so_tv)

    cao = sorted((v for v in kho.values()
                  if v.get("trang_thai") == "MOI" and (v.get("diem") or 0) >= 70),
                 key=lambda v: -(v.get("diem") or 0))
    if cao:
        try:
            SO.bao_van_de(
                "cong_cu_dang_xem", "VUA",
                f"{len(cao)} cong cu ngoai diem >=70 dang cho nguoi xem tich hop. "
                f"Cao nhat: {cao[0]['full_name']} ({cao[0]['diem']}). "
                f"Quy tac: cong cu ngoai lam BAN THI NGHIEM, khong bao gio lam ONG TOA.",
                bang_chung={"top": [{"ten": c["full_name"], "diem": c["diem"],
                                     "nhu_cau": c["nhu_cau"]} for c in cao[:8]]})
        except Exception:
            pass
    return {"tim_them": moi if viec else None, "loi": loi, "rong": rong,
            "da_thu": len(viec), "con_cho": con_cho, "tong_kho": len(kho),
            "diem_cao": len(cao), "nhu_cau_tu_van_de": sorted(dong),
            "cho_doc": len(dang_cho_doc(kho))}


def xem(toi_da: int = 25) -> None:
    kho = doc_kho()
    if not kho:
        print("kho cong cu rong - chay `python nhan/san_cong_cu.py` truoc")
        return
    ds = sorted(kho.values(), key=lambda v: -(v.get("diem") or 0))
    print(f"KHO CONG CU: {len(kho)} muc\n")
    for v in ds[:toi_da]:
        d = v.get("diem")
        nhan = (f"{d:5.1f}" if d is not None
                else ("BAI BAO" if v.get("loai") == "bai_bao" else "  -  "))
        # `.get` chu khong `[...]`: kho co ban ghi den tu nhieu duong (GitHub,
        # arXiv, HuggingFace, nhat tu ban doc) va mot ban thieu khoa khong duoc
        # phep lam vo ca man hinh - da vo that 30/08/2026.
        print(f"  {nhan:>7s}  {str(v.get('nhu_cau')):26s} "
              f"{str(v.get('full_name') or v.get('url') or '?')[:70]}")
        if v.get("mo_ta"):
            print(f"           {v['mo_ta'][:100]}")
        for c in v.get("canh_bao", []):
            print(f"           /!\\ {c}")


def xem_so() -> None:
    """Cai gi da thu, ra gi, va con bao lau nua moi thu lai."""
    so = doc_so_truy_van()
    if not so:
        print("so truy van rong - chua luot san nao chay voi ban 31/08")
        return
    print(f"SO TRUY VAN: {len(so)} muc\n")
    for tv, g in sorted(so.items(), key=lambda x: x[1].get("luc") or ""):
        print(f"  {g.get('ket','?'):11s} {g.get('so_ket_qua',0):3d} ket qua  "
              f"{g.get('luc','?')}  {tv[:60]}")
        for h in g.get("duong_hong") or []:
            print(f"              /!\\ {h}")


if __name__ == "__main__":
    if "--xem" in sys.argv:
        xem()
    elif "--so" in sys.argv:
        xem_so()
    else:
        print(json.dumps(mot_luot(), ensure_ascii=False, indent=1))
