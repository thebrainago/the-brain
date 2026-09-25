# -*- coding: utf-8 -*-
"""kien_truc.py - SINH SO DO KIEN TRUC: module nao, VAI TRO gi, thuoc LOP nao.

## No khac `ban_do.py` cho nao

`ban_do.py` tra loi mot cau: *"module nay co nam tren duong chay khong?"* -
tuc TOI DUOC hay MO COI. Do la cau hoi de khong xoa nham va khong xay trung.

File nay tra loi cau KHAC, cau ma chu du an hoi ngay 16/09/2026:

    **"He qua do so, toi can mot cho nhin thay TAT CA module va VAI TRO cua no
    de len ke hoach quan li - xay - phat trien."**

Mot module co the TOI DUOC ma van vo nghia trong so do (khong ai biet no o
tang nao), va mot lop co the rong hoac phinh ma `ban_do` khong bao gio thay
duoc, vi `ban_do` dem CANH chu khong dem VAI TRO.

## No doc vai tro o dau ra

Khong o mot file mo ta rieng - file do se cu di sau ba ngay, dung nhu
`BAN_DO.md` viet tay hoi 30/08. No doc **docstring dong dau cua chinh module**.
497/523 file trong lab da tu khai vai tro o do roi; 26 file con lai hien ra o
muc "KHONG TU KHAI VAI TRO" va do la mot muc NO, khong phai mot loi cua
bo sinh.

## LOP la thu duy nhat viet tay o day - va co ly do

`LOP` ben duoi la bang xep module vao tang. No viet tay vi khong co cach nao
doc duoc "tang" tu ma nguon: `du_lieu.py` va `cong.py` deu la `.py` trong
`nhan/`, chi NGUOI moi biet cai truoc la tang du lieu con cai sau la cai cong.

Nhung no khong rot duoc nhu mot ban do viet tay, vi module nao KHONG co trong
bang thi khong bi bo qua - no roi vao muc **CHUA XEP LOP** o cuoi bao cao.
Them mot module moi ma quen xep lop thi bao cao keu ngay lan chay sau. Do la
cai gia mot dong de giu so do khong rot.

Chay:  python -m nhan.kien_truc          in ra
       python -m nhan.kien_truc --ghi    ghi de KIEN_TRUC.md
       b kien-truc                       (duong chay that - lenh nguoi go)
"""
from __future__ import annotations

import ast
import re
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

from nhan import ban_do as BD                                    # noqa: E402

TEP = LAB / "KIEN_TRUC.md"

#: Vai tro cua tung THU MUC. Viet tay, cung ly do voi LOP ben duoi: khong co
#: cach nao doc duoc "thu muc nay de lam gi" tu ma nguon. Va cung mot cai
#: phanh: thu muc khong co trong bang thi KHONG bi bo qua, no hien ra o muc
#: "chua khai vai tro" cuoi muc 0, nen them thu muc moi la bao cao keu ngay.
THU_MUC_GOC = {
    "lab": "**The Brain** — toan bo he 24/7 (tru + nhan + cua vao). "
           "Moi thu con lai o goc la Phase 1 (SP500), da dong.",
    "ds": "Ho so giao viec cho agent ngoai (DeepSeek). Git rieng, gop vao 30/08.",
    "nap_tay": "Kho NAP TAY: repo github + file chu du an tu tha vao. "
               "Nguyen lieu tho, Seeker doc tu day.",
    "sp500_phase1": "**Phase 1 SP500 — DA DONG 18/09.** Dong bang: `ma/` 256 "
                    "script, `tai_lieu/`, `nut_bam/`, `reports/` 1,4 GB ket qua "
                    "tho. Khong module song nao goi vao day.",
    "V6_DONG_GOI": "He V6 dong goi CHAY THAT moi sang — tu chua (`%~dp0`), "
                   "khong phu thuoc goc. Dung dong.",
}

THU_MUC_LAB = {
    "bao_cao": "Bao cao phien The Brain (tu 15/08). Gom ve day 18/09.",
    "mau_thu": "Bo mau .mq5 THAT + `do_moc.py` — bai do chay duoc TREN CLOUD "
               "(khong can nao.db/MT5). Moc 18/09: thay 22 diem vao lenh, ra 0 co che.",
    "co_che_ds": "Co che do DeepSeek viet ra, cho kiem dinh.",
    "so_do": "So do he thong dang html/svg/png.",
    "tru": "**Bay tru** — Seeker/Quantlab/Evolution/Banker/Finder/Nghi. Tang tren.",
    "nhan": "**Lop nhan** — module thu vien, tang duoi cua moi tru. Xem muc 3.",
    "quant": "Lane nghien cuu Quantlab V2 (thu_vien/pseud + ket qua).",
    "qwen": "Bang viec + vong chay tu dong cua qwen — cua vao thu 4.",
    "config": "Cau hinh: api_keys, chi_phi_do, co_che_dsl...",
    "reports": "**Dau ra chinh** — ket qua may sinh (json/csv) cua kiem dinh.",
    "nhat_ky": "Ban giao song + log theo phien.",
    "downloaded_codes": "File Seeker tai ve (github/mql5/myfxbook/tradingview/transcripts).",
    "data": "Du lieu gia da nap (csv).",
    "data_khung": "Du lieu gia theo khung, dang parquet.",
    "roles": "Mo ta vai tro cho agent (BANKER/CHUNG/QUANTLAB/SEEKER).",
    "prompts": "Prompt cac vai.",
    "tai_lieu": "Dac ta viet tay (PMG, SLOT_TESTER).",
    "nghi_huu": "Module DA NGHI HUU, giu lai de tra cuu — khong nam tren duong chay. "
                "`v1_goc/` la The Brain V1 (26 script + 4 nut bam) go ve 18/09.",
    "_luu_tru": "Script cu cat di. Phan lon muc 4.1 nam o day.",
    "archive": "Script/anh chup cu cat di.",
    "browser_backup_20260821": "Ban sao ho so trinh duyet Seeker (21/08).",
    ".browser_darwinex": "Ho so trinh duyet RIENG cua Seeker, dang chay.",
    "ma_tai_ve": "Cho ma tai ve (rong).",
}

#: Cache/ha tang — dem lam nhieu so, khong phai kien truc.
BO_QUA_TM = {".git", ".claude", "__pycache__", ".pytest_cache",
             ".mermaid", ".mermaid-cache", "node_modules", ".venv"}

#: Nam tru theo so do cua chu du an (Desktop/hethong.txt - LUAT SO 0).
#: Thu tu o day la thu tu XUAT HIEN trong bao cao, khong phai thu tu uu tien.
TRU = ("seeker", "quantlab", "evolution", "banker", "finder", "nghi")

#: Tang cua `nhan/`. Viet tay - xem docstring dau file ve vi sao.
#: Module khong co trong bang nao se hien o muc CHUA XEP LOP.
LOP: dict[str, tuple[str, tuple[str, ...]]] = {
    "NHA NGHIEN CUU — AI nam quyen": (
        "Tang tren cung tu 25/09/2026: AI (Claude) quyet dinh nghien cuu gi, cac lop duoi la "
        "bo cong cu cua no. Code do va cham; AI dat gia thuyet, doc ket qua, hoc tu lenh.",
        ("nc_tac_tu", "nc_cong_cu", "nc_so_tay", "nc_thi_nghiem", "nc_mo_xe",
         "nc_dac_trung", "nc_du_lieu", "nc_tu_lai"),
    ),
    "SO & HOP DONG": (
        "Nguon su that chung. Moi tru doc va ghi qua day, khong tu giu so rieng.",
        ("so", "hop_dong", "quant_plan", "anh_chup", "bai_hoc",
         "ket_qua_hoat_dong", "bang_he", "pham_vi", "bi_mat", "duong_dan"),
    ),
    "THU THAP — Seeker di lay ve": (
        "Di ra ngoai lay tai lieu ve. Do dau vao, khong do ket qua.",
        ("doc_trinh_duyet", "cau_browser", "duyet_nguoi", "dns_vuot",
         "tu_dang_nhap", "telegram", "theo_doi", "nguon_bai_viet",
         "nguon_tinix", "kham_pha_nguon", "vuon_nguon", "tu_khoa_da_ngon_ngu",
         "toan_van", "doc_song_song", "hang_doi", "san_cong_cu", "nen_tang",
         "tien_ich_xet", "chi_tieu"),
    ),
    "BOC TACH — tai lieu thanh co che": (
        "Khau hep nhat cua he: van xuoi/ma nguon/anh/video -> khai bao kiem dinh duoc.",
        ("doc_pdf", "doc_anh", "doc_video", "doc_video_cuc_bo", "go_html",
         "doc_ma", "doc_chi_bao", "doc_hieu", "boc_llm", "boc_ma_llm",
         "ma_nguon", "bien_dich_ung_vien", "phan_loai_ma", "ngu_phap", "mau",
         "quan_tri", "quan_tri_llm", "uu_tien", "mimic_cau_noi"),
    ),
    "DU LIEU & TAI SAN": (
        "Nap gia tu chinh cong cu se giao dich, va do dac tinh cua tung ma.",
        ("du_lieu", "nen", "dem_nen", "doi_khung", "chi_phi", "tai_tro",
         "thang_gia", "ten_ma", "ho_so_symbol", "ho_so_tai_san",
         "ho_so_mua_vu", "ho_so_song", "ho_so_tuong_quan", "tinh_cach",
         "tinh_cach_chieu", "quy_luat_song", "dia", "gop_wal",
         "quy_doi_tham_so"),
    ),
    "SINH GIA THUYET": (
        "Bon luong sinh: noi sinh, ngoai sinh, suy nguoc tu dau chan, to hop.",
        ("noi_sinh", "ngoai_sinh", "suy_nguoc", "dau_chan", "luan_dau_chan",
         "tin_hieu_mql5", "to_hop", "da_thoi_dai", "gop_lop", "chuyen_he",
         "thu_hoi_thanh_phan"),
    ),
    "QUAN TRI VI THE": (
        "Ho co che THU HAI. 262 co che dau la tin hieu VAO; day la nua con lai.",
        ("pmg", "pmg_engine", "pmg_g0", "pmg_quet", "quan_tri_dsl",
         "quan_tri_nhieu", "chuoi_quan_tri", "dap_quan_tri", "de_quan_tri",
         "luoi", "vao_lenh", "bien_don_bay"),
    ),
    "KIEM DINH & CONG": (
        "Noi mot gia thuyet duoc phep doi doi. Hai cong: co that khong, va co ra tien khong.",
        ("mo_phong", "sang_loc", "cong", "cong_ra_tien", "cham_diem",
         "do_luong", "do_luc", "loc_co_che", "danh_muc", "nha_may_null",
         "suy_giam"),
    ),
    "MT5 / TESTER — do that": (
        "Quy tac cua chu du an: MT5 tester TRUOC, Python SAU.",
        ("dich_mq5", "dich_mq5_ghep", "dich_mq5_qtvt", "dich_mq5_quan_tri",
         "doc_lenh_tester", "khoa_tester", "dang_nhap_mt5", "passview",
         "chay_that", "so_lenh", "san_sang_vps", "tai_khoan_nen_tang"),
    ),
    "DIEU HANH & GIAM SAT": (
        "Giu he chay 24/7 va tu thay duoc minh dang hong cho nao.",
        ("evo", "canary", "mach", "do_im_lang", "do_tai_nguyen", "don_mo_coi",
         "han_muc", "ngan_sach", "tran_cpu", "ban_do", "kien_truc", "tri_tue",
         "muc_tieu", "vong_day_du", "day_chuyen", "day_chuyen_quantlab"),
    ),
}


def _vai_tro(p: Path) -> str:
    """Dong dau docstring, da cat khuc `ten_file.py -` neu module tu nhac ten.

    `ban_do._mo_ta` lam gan giong, nhung mau cua no an mat ky tu dau tren mot
    so file (`anh_chup.py` -> `nh_chup.py`) vi `[\\w./\\\\]+` nuot luon ky tu
    dau roi lui sai nhip. O day cat bang chinh TEN FILE nen khong doan mo ho.
    """
    try:
        cay = ast.parse(p.read_text(encoding="utf-8-sig", errors="ignore"))
    except Exception:
        return ""
    d = (ast.get_docstring(cay) or "").strip()
    if not d:
        return ""
    dong = d.splitlines()[0].strip()
    dong = re.sub(r"^%s\s*[-–—:]\s*" % re.escape(p.name), "", dong)
    dong = re.sub(r"^%s\s*[-–—:]\s*" % re.escape(p.stem), "", dong)
    return dong.strip()


def _so_dong(p: Path) -> int:
    try:
        return len(p.read_text(encoding="utf-8-sig", errors="ignore").splitlines())
    except Exception:
        return 0


def _thu_thap() -> dict:
    """Gom moi thu mot lan: do thi goi, tap toi duoc, vai tro, so dong."""
    toi, canh = BD.voi_toi_duoc()
    nguoc: dict[str, set] = {k: set() for k in canh}
    for k, ra in canh.items():
        for v in ra:
            nguoc.setdefault(v, set()).add(k)
    vai_tro, dong = {}, {}
    for p in BD._cac_file():
        k = BD._khoa(p)
        vai_tro[k] = _vai_tro(p)
        dong[k] = _so_dong(p)
    return {"toi": toi, "canh": canh, "nguoc": nguoc,
            "vai_tro": vai_tro, "dong": dong}


def _dong_module(k: str, d: dict, hien_goi: bool = True) -> str:
    """Mot dong bao cao cho mot module."""
    ten = k.rsplit("/", 1)[-1][:-3]
    vt = d["vai_tro"].get(k) or "_(chua tu khai vai tro)_"
    dau = "" if k in d["toi"] else " ⚠MO COI"
    if hien_goi:
        n = len(d["nguoc"].get(k, ()))
        return "- **`%s`** (%d dong, %d noi goi%s) — %s" % (
            ten, d["dong"].get(k, 0), n, dau, vt)
    return "- **`%s`** (%d dong%s) — %s" % (ten, d["dong"].get(k, 0), dau, vt)


def _do_thu_muc(goc: Path, bang: dict) -> tuple[list, list]:
    """Do THAT tren dia: moi thu muc con cap 1 co bao nhieu file, bao nhieu MB.

    Tra ve (da_khai, chua_khai). Dung luong o day tung la thu cuu mot phien:
    dia day hien ra nhu ket qua rong chu khong bao loi.
    """
    da, chua = [], []
    for p in sorted(goc.iterdir()):
        if not p.is_dir() or p.name in BO_QUA_TM:
            continue
        n = b = 0
        for f in p.rglob("*"):
            if "__pycache__" in f.parts:
                continue
            try:
                if f.is_file():
                    n += 1
                    b += f.stat().st_size
            except OSError:
                pass
        (da if p.name in bang else chua).append((p.name, n, b / 1e6))
    return da, chua


def sinh(in_ra=print) -> str:
    """Dung bao cao. Tra ve chuoi de `--ghi` ghi thang xuong file."""
    d = _thu_thap()
    ra: list[str] = []
    W = ra.append

    nhan_het = sorted(k for k in d["vai_tro"] if k.startswith("nhan/")
                      and not k.endswith("__init__.py"))
    da_xep: set[str] = set()

    W("# KIEN TRUC HE THONG — sinh tu ma nguon")
    W("")
    W("*%s · %d file `.py` · %d tren duong chay · %d lop nhan · "
      "sinh boi `python -m nhan.kien_truc --ghi` (hoac `b kien-truc`)*"
      % (time.strftime("%Y-%m-%d %H:%M"), len(d["vai_tro"]), len(d["toi"]),
         len(LOP)))
    W("")
    W("**Dung sua tay.** Vai tro o day doc tu docstring dong dau cua chinh")
    W("module; sua mo ta thi sua trong file `.py`, roi chay lai lenh tren.")
    W("Nguon cau truc goc van la `Desktop/hethong.txt` (LUAT SO 0) — file nay")
    W("khong thay the no, no chi cho thay CAI DA XAY toi dau so voi so do do.")
    W("")

    # ---- 0. THU MUC ------------------------------------------------------
    GOC = LAB.parent
    W("## 0. Thu muc — cai gi nam o dau")
    W("")
    W("So file va MB o day DO THAT tren dia luc chay; vai tro thi viet tay")
    W("(`THU_MUC_GOC` / `THU_MUC_LAB` trong `nhan/kien_truc.py`). Cache va")
    W("`.git` khong dem.")
    W("")
    for ten, g, bang in (("`%s/` — goc du an" % GOC.name, GOC, THU_MUC_GOC),
                         ("`lab/` — The Brain", LAB, THU_MUC_LAB)):
        da, chua = _do_thu_muc(g, bang)
        W("### %s" % ten)
        W("")
        W("| Thu muc | File | MB | Vai tro |")
        W("|---|---:|---:|---|")
        for nm, n, mb in sorted(da, key=lambda x: -x[1]):
            W("| `%s/` | %d | %.0f | %s |" % (nm, n, mb, bang[nm]))
        W("")
        if chua:
            W("**Chua khai vai tro — %d thu muc:** %s"
              % (len(chua), " · ".join("`%s/` (%d file)" % (nm, n)
                                       for nm, n, _ in chua)))
            W("")
    kho = sorted(LAB.glob("*.db"))
    if kho:
        W("**Kho o goc `lab/`:** "
          + " · ".join("`%s` %.0f MB" % (k.name, k.stat().st_size / 1e6)
                       for k in kho))
        W("")

    # ---- 1. CUA VAO -------------------------------------------------------
    W("## 1. Cua vao — bon duong chay that")
    W("")
    W("Module khong duoc goi tu mot trong cac duong nay thi *bang khong co*")
    W("(luat L7, `LUAT_GIAM_SAT.md`). Day la ly do phan lon cong cu bi bo quen.")
    W("")
    for c, mo in (("b.py", "lenh nguoi go — ~80 lenh con"),
                  ("dieu_phoi.py", "nam tru chay 24/7"),
                  ("day_viec.py", "hang doi viec xay, chay tuan tu"),
                  ("qwen/NHIEM_VU.json", "bang viec qwen tu chay"),
                  ("BAN_GIAO.py", "chot phien, ghi ban giao")):
        co = "" if (c.endswith(".json") or c in d["vai_tro"]) else "  ⚠KHONG THAY"
        W("- **`%s`** — %s%s" % (c, mo, co))
    W("")

    # ---- 2. TRU -----------------------------------------------------------
    W("## 2. Tru — so do cua chu du an")
    W("")
    for t in TRU:
        k = "tru/%s.py" % t
        if k not in d["vai_tro"]:
            continue
        goi = sorted(x for x in d["canh"].get(k, ()) if x.startswith("nhan/"))
        W("### %s" % t.upper())
        W("")
        W("%s" % (d["vai_tro"].get(k) or "_(chua tu khai vai tro)_"))
        W("")
        W("*%d dong · goi thang %d module nhan*" % (d["dong"].get(k, 0), len(goi)))
        if goi:
            W("")
            W("> " + " · ".join("`%s`" % x[5:-3] for x in goi))
        W("")

    # ---- 3. LOP NHAN ------------------------------------------------------
    W("## 3. Lop nhan — %d module thu vien" % len(nhan_het))
    W("")
    for ten_lop, (mo_ta, ds) in LOP.items():
        co = [("nhan/%s.py" % m) for m in ds if ("nhan/%s.py" % m) in d["vai_tro"]]
        thieu = [m for m in ds if ("nhan/%s.py" % m) not in d["vai_tro"]]
        da_xep.update(co)
        W("### %s — %d module" % (ten_lop, len(co)))
        W("")
        W("*%s*" % mo_ta)
        W("")
        for k in sorted(co):
            W(_dong_module(k, d))
        if thieu:
            W("")
            W("> ⚠ Xep lop nhung KHONG CON FILE: %s"
              % ", ".join("`%s`" % x for x in thieu))
        W("")

    chua = [k for k in nhan_het if k not in da_xep]
    W("### CHUA XEP LOP — %d module" % len(chua))
    W("")
    if chua:
        W("Module moi chua ai xep vao tang nao. Day la muc **can doc truoc")
        W("khi lap ke hoach**: mot module khong co tang thi khong ai biet no")
        W("thuoc ve ai, va no se bi xay lai duoi mot cai ten khac.")
        W("")
        for k in sorted(chua):
            W(_dong_module(k, d))
    else:
        W("(khong con — moi module nhan deu da co tang)")
    W("")

    # ---- 4. NO KIEN TRUC --------------------------------------------------
    W("## 4. No kien truc — cho de lam ke hoach")
    W("")

    # `nghi_huu/` va `co_che_ds/` khong tinh la NO: mot ben da nghi huu, mot ben
    # la CO CHE tho cho kiem dinh chu khong phai module. Bat chung khai vai tro la
    # bat bao cao keu ve thu khong ai dinh dung nua (18/09, sau khi gom v1_goc).
    khong_vt = sorted(k for k, v in d["vai_tro"].items()
                      if not v and not k.endswith("__init__.py")
                      and not k.startswith(("nghi_huu/", "co_che_ds/")))
    W("### 4.1 Khong tu khai vai tro — %d file" % len(khong_vt))
    W("")
    W("Khong co docstring dong dau, nen khong vao duoc ban do vai tro nao.")
    W("Sua mot dong docstring la het no.")
    W("")
    for k in khong_vt[:40]:
        W("- `%s` (%d dong)" % (k, d["dong"].get(k, 0)))
    if len(khong_vt) > 40:
        W("- _(con %d file nua)_" % (len(khong_vt) - 40))
    W("")

    goc = sorted(k for k in d["vai_tro"] if "/" not in k)
    goc_tay = [k for k in goc if k.startswith("_")]
    goc_test = [k for k in goc if k.startswith(("test_", "conftest"))]
    goc_khac = [k for k in goc if k not in goc_tay and k not in goc_test]
    W("### 4.2 Goc `lab/` — %d file roi" % len(goc))
    W("")
    W("**Ba loai khac han nhau — tron chung lai thi con so vo nghia.** Ban sinh")
    W("dau tien cua chinh file nay bao \"231 file phai don\", trong khi 146 trong")
    W("so do la `test_*.py`: pytest TIM chung o goc, chung o dung cho roi.")
    W("")
    W("| Loai | So | Phai lam gi |")
    W("|---|---|---|")
    W("| `test_*.py` + `conftest.py` | %d | khong lam gi — dung cho |" % len(goc_test))
    W("| `_*.py` chay tay mot lan | %d | mo coi la DUNG BAN CHAT — de yen hoac xoa |"
      % len(goc_tay))
    W("| **con lai** | **%d** | **day moi la no**: len `nhan/`, hoac doi ten `_*.py`, hoac xoa |"
      % len(goc_khac))
    W("")
    W("%d file thuoc nhom thu ba:" % len(goc_khac))
    W("")
    for k in goc_khac:
        vt = d["vai_tro"].get(k) or "_(chua tu khai vai tro)_"
        dau = "" if k in d["toi"] else " ⚠MO COI"
        W("- `%s`%s — %s" % (k, dau, vt[:88]))
    W("")

    to = sorted(((d["dong"][k], k) for k in d["dong"] if d["dong"][k] >= 600),
                reverse=True)
    W("### 4.3 File tren 600 dong — %d file" % len(to))
    W("")
    W("Khong phai loi, nhung la cho mot module dang lam nhieu hon mot viec.")
    W("")
    for n, k in to[:25]:
        W("- `%s` — %d dong" % (k, n))
    W("")

    mc = sorted(k for k in d["vai_tro"]
                if k not in d["toi"] and k.startswith(("nhan/", "tru/", "qwen/")))
    W("### 4.4 Module trong goi nhung MO COI — %d" % len(mc))
    W("")
    if mc:
        for k in mc:
            W("- `%s` — %s" % (k, d["vai_tro"].get(k) or "(khong khai vai tro)"))
    else:
        W("(khong co — moi module trong goi deu toi duoc tu mot cua vao)")
    W("")

    # ---- 5. SO TONG -------------------------------------------------------
    W("## 5. So tong")
    W("")
    W("| Muc | So |")
    W("|---|---|")
    W("| File `.py` (bo `nhat_ky/ backups/ __pycache__/ ...`) | %d |" % len(d["vai_tro"]))
    W("| Tren duong chay | %d |" % len(d["toi"]))
    W("| Module thu vien `nhan/` | %d |" % len(nhan_het))
    W("| — da xep lop | %d |" % len(da_xep))
    W("| — chua xep lop | %d |" % len(chua))
    W("| Tru `tru/` | %d |" % len([k for k in d["vai_tro"] if k.startswith("tru/")]))
    W("| File roi o goc `lab/` | %d |" % len(goc))
    W("| — `test_*.py` (dung cho) | %d |" % len(goc_test))
    W("| — script `_*.py` chay tay | %d |" % len(goc_tay))
    W("| — **con lai, la no that** | **%d** |" % len(goc_khac))
    W("| Khong tu khai vai tro | %d |" % len(khong_vt))
    W("")

    vb = "\n".join(ra) + "\n"
    if in_ra is not None:
        in_ra(vb)
    return vb


def main(argv: list[str]) -> int:
    vb = sinh(in_ra=None)
    if "--ghi" in argv:
        TEP.write_text(vb, encoding="utf-8")
        print("da ghi %s (%d dong)" % (TEP, len(vb.splitlines())))
    else:
        print(vb)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
