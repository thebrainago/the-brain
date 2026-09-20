# -*- coding: utf-8 -*-
"""cau_git.py - CAU NOI HAI MAY. Git la duong truyen duy nhat.

## VI SAO CO FILE NAY

Chot 20/09/2026 (`tai_lieu/VAN_HANH_HAI_MAY.md`). Chu du an: *"may tinh toi cho
toan bo phan tinh toan va cloud cua claude code phu trach giam sat va suy nghi
+ goi llm"*.

**Phien cloud KHONG co duong mang nao toi may chu du an.** No chi thay GitHub.
Nen duong truyen duy nhat la git:

    CLOUD                    GIT                      MAY (q)
      nghi, ra don     ->  viec/cho/*.json   ->   `dong_bo()` keo ve
      viet BAI TEST                                tho local chay
      doc, quyet dinh  <-  viec/xong/*.json  <-   `dong_bo()` day len

Khong co cau nay thi may chu du an RANH trong luc cloud nghi - va do la lang
phi that, vi rang buoc chan he la lan TESTER = 1 chu khong phai token.

## BON THU MUC, BON VAI

    viec/cho/<ma>.json    DON HANG   - cloud ghi, may doc
    viec/dang/<ma>.json   DANG LAM   - may ghi, chong chay trung
    viec/xong/<ma>.json   KET QUA    - may ghi, cloud doc
    viec/hoi/<ma>.json    LEO THANG  - may hoi, cloud tra loi

## BA LUAT AN TOAN - day la module TU CHAY `git` TREN MAY NGUOI KHAC

1. **KHONG BAO GIO `git add -A`.** Chi them dung cac duong trong `DUOC_DAY`.
   Ly do: `q` chay nhieu ngay tren may that, canh nhung file dang sua do. Mot
   `add -A` tu dong se cuon ca cong viec chua xong cua chu du an len remote.

2. **KHONG BAO GIO vut viec local.** Khong `stash`, khong `reset --hard`,
   khong `checkout --force`, khong `push --force`. Dung do thi DUNG va BAO.

3. **Dong bo HONG khong bao gio la ket qua AM.** Mat mang, xung dot, remote
   tu choi - tat ca la `CHUA_DO_DUOC`. Mot vong `q` khong keo duoc don moi
   thi no chay tiep viec cu, khong duoc ket luan "het viec".

## LUAT SO 0 o day: THIEU KET QUA KHAC KET QUA AM

`doc_ket_qua()` tra `CHUA_DO_DUOC` cho moi truong hop khong chac: file khong
co, JSON hong, thieu truong `trang_thai`, hay `trang_thai` la mot chu la. Chi
dung ba chu DAT / AM / CHUA_DO_DUOC moi duoc di qua.
"""
from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
VIEC = GOC / "viec"
CHO, DANG, XONG, HOI = VIEC / "cho", VIEC / "dang", VIEC / "xong", VIEC / "hoi"

#: Ba trang thai cua ca du an. Khong co cai thu tu.
TRANG_THAI = ("DAT", "AM", "CHUA_DO_DUOC")

#: DUY NHAT nhung duong nay duoc `git add`. Xem luat an toan 1.
#:
#: `config/` KHONG co trong danh sach, co chu dich: `CLAUDE.md` quy tac phien
#: cam phien [DOC] sua `config/*.json`, va may chay `q` dung la mot phien nhu
#: vay doi voi ma nguon. `data/` va `nao.db` da bi gitignore san nhung van
#: khong liet ke o day - hai lop chan tot hon mot.
DUOC_DAY = ("viec/xong", "viec/hoi", "viec/dang", "reports")

#: Vong `q` goi `dong_bo()` moi nhip. Keo/day that thi ton mang, nen chi lam
#: khi da qua ngan nay giay ke tu lan truoc.
NHIP_GIAY = 60.0

_LAN_CUOI = 0.0


class LoiCau(RuntimeError):
    """Dong bo khong lam duoc. LUON la CHUA_DO_DUOC, khong bao gio la AM."""


# ------------------------------------------------------------------ git tho
def _git(*doi, goc: Path | None = None, han: float = 120.0,
         tho: bool = False) -> tuple[int, str, str]:
    """Chay mot lenh git. Tra (ma_thoat, stdout, stderr) - KHONG nem.

    Khong nem vi moi loi goi o day deu phai tu quyet dinh no la loi nghiem
    trong hay mot tinh huong binh thuong (vd `rev-parse` tren repo chua co
    commit nao).

    ## `tho=True`: KHONG cat trang - va vi sao phai co lua chon nay

    Ban dau ham nay luon `.strip()` stdout. Loi do sap ngay trong bai kiem dau
    tien: `git status --porcelain` in moi dong theo dang `XY<cach>DUONG`, tuc
    mot file bi SUA ra ` M README.md` co dau cach dan dau. `.strip()` tren CA
    chuoi chi an dau cach cua **dong dau**, nen dong dau bi cat lech mot ky tu
    (`README.md` -> `EADME.md`) con cac dong sau thi dung.

    Do la hinh dang hong te nhat: khong nem loi, khong sai ro rang, chi doc ra
    mot duong dan LECH - va `dong_bo` se ket luan sai ve viec file nao dang do
    dang, tuc quyet dinh sai giua "keo duoc" va "khong duoc keo".
    """
    r = subprocess.run(["git", *doi], cwd=str(goc or GOC), capture_output=True,
                       text=True, timeout=han,
                       # Git co the treo cho nhap mat khau tren may khong ai
                       # ngoi. Mot vong `q` treo vi thi la kieu chet im lang
                       # te nhat: bang viec van hien "dang chay".
                       env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    if tho:
        return r.returncode, r.stdout, r.stderr
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def nhanh_hien_tai(goc: Path | None = None) -> str | None:
    ma, ra, _ = _git("rev-parse", "--abbrev-ref", "HEAD", goc=goc)
    return ra if ma == 0 and ra != "HEAD" else None


def co_viec_chua_commit(goc: Path | None = None) -> list[str]:
    """Danh sach duong dang do dang. Rong = cay sach.

    Dung `--porcelain` chu khong doc van ban `git status`: van ban doi theo
    ngon ngu va theo ban git, va mot phep doc hong o day se ket luan "cay
    sach" tren mot cay day viec dang lam.
    """
    # `-z` tach ban ghi bang NUL: khong trich dan, khong escape, va khong co
    # cach nao mot ten file co ky tu la lam lech phep doc. Ban `--porcelain`
    # thuong trich dan ten co dau cach thanh `"a b"` - tuc lai mot lop phai
    # go dung, va go sai thi ra mot duong dan khong ton tai.
    ma, ra, _ = _git("status", "--porcelain", "-z", goc=goc, tho=True)
    if ma != 0:
        raise LoiCau("khong doc duoc trang thai git")
    ban = [x for x in ra.split("\0") if x]
    duong, i = [], 0
    while i < len(ban):
        d = ban[i]
        # `XY<cach>DUONG`. Doi ten (`R`) an them MOT ban ghi la ten cu - phai
        # nhay qua, neu khong ten cu se bi doc thanh mot muc do dang rieng.
        duong.append(d[3:])
        i += 2 if d[:1] == "R" else 1
    return duong


# ------------------------------------------------------------------ dong bo
def _keo(nhanh: str, goc: Path | None = None) -> dict:
    """`fetch` + `merge --ff-only`. KHONG rebase, KHONG merge thuong.

    `--ff-only` la lua chon co y: no THAT BAI thay vi tao mot merge commit tu
    dong tren may chu du an. Mot merge tu dong luc 3 gio sang, khong ai nhin,
    tren mot cay dang co viec do dang - do la cach nhanh nhat de mat viec ma
    khong ai biet. That bai o day chi ton mot vong `q`.
    """
    ma, _, loi = _git("fetch", "origin", nhanh, goc=goc, han=180.0)
    if ma != 0:
        raise LoiCau("fetch hong: %s" % (loi or "khong ro")[:200])
    ma, ra, loi = _git("merge", "--ff-only", "FETCH_HEAD", goc=goc)
    if ma != 0:
        raise LoiCau("khong ff-only duoc (nhanh da re) - can nguoi xu li: %s"
                     % (loi or ra)[:200])
    return {"da_keo": True}


def _day(nhanh: str, loi_nhan: str, goc: Path | None = None) -> dict:
    """Commit CHI cac duong trong `DUOC_DAY` roi push. Khong co gi thi khong
    tao commit rong."""
    co = []
    for d in DUOC_DAY:
        if (goc or GOC).joinpath(d).exists():
            ma, _, _ = _git("add", "--", d, goc=goc)
            if ma == 0:
                co.append(d)
    if not co:
        return {"da_day": False, "ly_do": "khong thu muc nao de day"}
    ma, ra, _ = _git("diff", "--cached", "--name-only", goc=goc)
    if ma != 0 or not ra.strip():
        return {"da_day": False, "ly_do": "khong co thay doi"}
    so_file = len(ra.splitlines())
    ma, _, loi = _git("commit", "-m", loi_nhan, goc=goc)
    if ma != 0:
        raise LoiCau("commit hong: %s" % (loi or "khong ro")[:200])
    ma, _, loi = _git("push", "origin", "HEAD:%s" % nhanh, goc=goc, han=180.0)
    if ma != 0:
        # Commit da tao roi nhung push hong (mat mang / remote di truoc). KHONG
        # duoc go commit ra: no la ket qua that cua may. Vong sau se keo roi
        # day lai.
        raise LoiCau("push hong (commit da giu lai o local): %s"
                     % (loi or "khong ro")[:200])
    return {"da_day": True, "so_file": so_file}


def dong_bo(nhanh: str | None = None, ep: bool = False,
            goc: Path | None = None) -> dict:
    """MOT nhip dong bo: keo don ve, day ket qua len.

    Tra ve mot dict LUON co truong `trang_thai` trong `TRANG_THAI`. Hong thi
    la `CHUA_DO_DUOC` kem `ly_do` - khong bao gio nem ra vong `q`, vi mot loi
    mang khong duoc phep giet mot dot chay nhieu ngay.
    """
    global _LAN_CUOI
    g = goc or GOC
    if not ep and (time.time() - _LAN_CUOI) < NHIP_GIAY:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "chua toi nhip",
                "bo_qua": True}
    _LAN_CUOI = time.time()
    try:
        nh = nhanh or nhanh_hien_tai(g)
        if not nh:
            raise LoiCau("dang o trang thai HEAD roi - khong biet day di dau")
        do_dang = co_viec_chua_commit(g)
        # File trong `DUOC_DAY` dang do dang la BINH THUONG - chinh may vua
        # ghi ket qua ra do. Chi cac duong KHAC moi la viec cua nguoi.
        nguoi = [d for d in do_dang
                 if not any(d.startswith(x) for x in DUOC_DAY)]
        keo = {"da_keo": False, "ly_do": "co viec nguoi chua commit: %s"
                                         % ", ".join(nguoi[:5])}
        if not nguoi:
            keo = _keo(nh, g)
        day = _day(nh, "may: ket qua %s" % time.strftime("%Y-%m-%d %H:%M"), g)
        return {"trang_thai": "DAT", "nhanh": nh, "keo": keo, "day": day,
                "viec_nguoi_do_dang": nguoi}
    except LoiCau as e:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": str(e)}
    except (OSError, subprocess.SubprocessError) as e:
        return {"trang_thai": "CHUA_DO_DUOC",
                "ly_do": "%s: %s" % (type(e).__name__, e)}


# ------------------------------------------------------------------ don hang
def bao_dam_thu_muc(goc: Path | None = None) -> None:
    for d in (CHO, DANG, XONG, HOI):
        p = (goc / "viec" / d.name) if goc else d
        p.mkdir(parents=True, exist_ok=True)
        # Git khong theo doi thu muc rong. Thieu cai nay thi mot clone moi
        # khong co `viec/cho/` va vong dau tien bao "khong co don" thay vi
        # "chua dong bo" - lai dung cai bay CHUA_DO_DUOC doc thanh AM.
        gk = p / ".gitkeep"
        if not gk.exists():
            gk.write_text("", encoding="utf-8")


def _doc_json(p: Path) -> dict | None:
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def don_dang_cho(goc: Path | None = None) -> list[dict]:
    """Don CHUA co ket qua, xep theo `uu_tien` roi theo ten file.

    Bo qua don da co `viec/xong/<ma>.json`: dong bo co the keo ve mot don cu
    ma may nay da lam roi. Chay lai khong sai nhung ton mot slot TESTER, va
    slot do la thu hiem nhat trong ca he.
    """
    thu = (goc / "viec") if goc else VIEC
    ra = []
    for p in sorted((thu / "cho").glob("*.json")):
        d = _doc_json(p)
        if not d or not d.get("ma"):
            continue
        if (thu / "xong" / ("%s.json" % d["ma"])).exists():
            continue
        d["_duong"] = str(p)
        ra.append(d)
    ra.sort(key=lambda x: (int(x.get("uu_tien", 5)), str(x.get("ma"))))
    return ra


def ghi_ket_qua(ma: str, trang_thai: str, ly_do: str = "",
                bang_chung: dict | None = None, so_do: dict | None = None,
                can_cloud: bool = False, cau_hoi: str = "",
                goc: Path | None = None) -> Path:
    """Ghi ket qua mot don. `trang_thai` PHAI la mot trong ba chu.

    Nem `ValueError` khi trang thai la chu la - thay vi lang le ghi xuong.
    Mot ket qua mang trang thai khong doc duoc thi ca ben cloud lan ben may
    deu phai doan, va doan o day nghia la doan giua "khong ra tien" voi
    "chua do duoc".
    """
    if trang_thai not in TRANG_THAI:
        raise ValueError("trang_thai phai la mot trong %r, nhan duoc %r"
                         % (list(TRANG_THAI), trang_thai))
    thu = (goc / "viec") if goc else VIEC
    thu.joinpath("xong").mkdir(parents=True, exist_ok=True)
    p = thu / "xong" / ("%s.json" % ma)
    d = {
        "ma": ma,
        "trang_thai": trang_thai,
        "ly_do": ly_do,
        "bang_chung": bang_chung or {},
        "so_do": so_do or {},
        "can_cloud": bool(can_cloud),
        "cau_hoi": cau_hoi or None,
        "may": "%s/%s" % (socket.gethostname(), platform.system()),
        "luc": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    # Ghi NGUYEN TU: ghi file tam roi doi ten. `q` co the bi Ctrl-C giua chung,
    # va mot file JSON viet do dang doc ra thanh `CHUA_DO_DUOC` vinh vien - tuc
    # mot ket qua that bi mat ma khong ai biet no da tung co.
    tam = p.with_suffix(".json.tam")
    tam.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tam, p)
    if can_cloud:
        thu.joinpath("hoi").mkdir(parents=True, exist_ok=True)
        (thu / "hoi" / ("%s.json" % ma)).write_text(
            json.dumps({"ma": ma, "cau_hoi": cau_hoi, "luc": d["luc"]},
                       ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def doc_ket_qua(ma: str, goc: Path | None = None) -> dict:
    """Ben CLOUD doc ket qua mot don. LUON tra mot dict co `trang_thai` hop le.

    Moi truong hop khong chac deu ra `CHUA_DO_DUOC`: file khong co, JSON hong,
    thieu truong, hay trang thai la mot chu la. Day la cho de nhat de mot cai
    hong im lang chui qua - `{}` hay `None` di vao mot cau `if kq:` se doc
    thanh "khong dat", tuc thanh mot ket luan AM bia ra.
    """
    thu = (goc / "viec") if goc else VIEC
    p = thu / "xong" / ("%s.json" % ma)
    if not p.exists():
        return {"ma": ma, "trang_thai": "CHUA_DO_DUOC",
                "ly_do": "chua co ket qua - may chua chay hay chua day len"}
    d = _doc_json(p)
    if not isinstance(d, dict):
        return {"ma": ma, "trang_thai": "CHUA_DO_DUOC",
                "ly_do": "file ket qua hong, khong doc duoc JSON"}
    if d.get("trang_thai") not in TRANG_THAI:
        return {"ma": ma, "trang_thai": "CHUA_DO_DUOC",
                "ly_do": "trang_thai la %r - khong phai mot trong %r"
                         % (d.get("trang_thai"), list(TRANG_THAI)),
                "goc": d}
    return d


def cho_cloud(goc: Path | None = None) -> list[dict]:
    """Cac don dang doi cloud tra loi (`can_cloud: true`)."""
    thu = (goc / "viec") if goc else VIEC
    ra = []
    for p in sorted((thu / "hoi").glob("*.json")):
        d = _doc_json(p)
        if d:
            ra.append(d)
    return ra


def tom_tat(goc: Path | None = None) -> dict:
    """Mot dong cho ca hai ben doc: con bao nhieu don, ket qua ra sao."""
    thu = (goc / "viec") if goc else VIEC
    kq = [_doc_json(p) or {} for p in (thu / "xong").glob("*.json")]
    dem = {t: sum(1 for d in kq if d.get("trang_thai") == t) for t in TRANG_THAI}
    la = sum(1 for d in kq if d.get("trang_thai") not in TRANG_THAI)
    return {"cho": len(don_dang_cho(goc)), "xong": len(kq),
            **dem, "trang_thai_la": la, "hoi_cloud": len(cho_cloud(goc))}


# ------------------------------------------------------------------ ra don
#: Lan chay - quyet dinh may chay song song bao nhieu don cung luc.
#: `TESTER` toi da MOT: `chay_tester_kho` ghi de cung mot `.mq5`/`.ini`/`.xml`
#: va may chi co mot `terminal64.exe`. Hai viec tester cung luc thi ghi de ket
#: qua cua nhau **va khong ai bao loi**.
LAN = ("TESTER", "CPU", "LLM", "MANG", "NHE")


#: Cac kieu cong `_cham` biet cham. Don khai kieu ngoai bang nay se LUON ra
#: `CHUA_DO_DUOC` - nen chan ngay luc ra don thay vi sau mot dem chay.
#:
#:   `chay_duoc`  0 = DAT · moi ma khac = CHUA_DO_DUOC
#:   `pytest`     0 = DAT · 1 = AM · >= 2 = CHUA_DO_DUOC
#:   `ba_muc`     cung quy uoc voi `pytest`, cho SCRIPT tu viet theo no.
#:                Tach ten ra de doc don khong tuong no dang chay pytest.
KIEU_CONG = ("pytest", "chay_duoc", "ba_muc")


def ra_don(ma: str, muc_tieu: str, lenh: list[str] | None = None,
           lan: str = "NHE", uu_tien: int = 5, han_phut: float = 60.0,
           file_test: str = "", duoc_sua: list[str] | None = None,
           ghi_chu: str = "", cong: dict | str | None = None,
           goc: Path | None = None) -> Path:
    """BEN CLOUD ra mot don hang. Ghi ra `viec/cho/<ma>.json`.

    Khong tu `git push` - viec do de cho nguoi goi gop nhieu don vao mot
    commit. Mot commit mot don thi lich su repo thanh nhat ky, khong con doc
    duoc.

    `lan` phai hop le: no la thu quyet dinh may co chay trung slot TESTER hay
    khong, va mot chu go sai o day khong lo ra o dau ca cho toi luc hai viec
    tester ghi de ket qua cua nhau.
    """
    if lan not in LAN:
        raise ValueError("lan phai la mot trong %r, nhan duoc %r" % (list(LAN), lan))
    if not ma or "/" in ma or "\\" in ma:
        raise ValueError("ma don khong duoc rong hay chua dau gach: %r" % ma)
    thu = (goc / "viec") if goc else VIEC
    thu.joinpath("cho").mkdir(parents=True, exist_ok=True)
    d = {"ma": ma, "muc_tieu": muc_tieu, "lan": lan, "uu_tien": int(uu_tien),
         "han_phut": float(han_phut), "ra_luc": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if lenh:
        d["lenh"] = list(lenh)
    if file_test:
        d["file_test"] = file_test
    if duoc_sua:
        d["duoc_sua"] = list(duoc_sua)
        # Bai test la DAC TA. Cho no vao `duoc_sua` la cho pha dac ta de lam
        # xanh bang so - da chan o `tho_code.lam`, chan them o day vi don co
        # the den tu mot duong khac.
        if file_test and file_test in d["duoc_sua"]:
            raise ValueError("file_test nam trong duoc_sua: bai test la DAC TA, "
                             "khong duoc sua de lam xanh")
    if ghi_chu:
        d["ghi_chu"] = ghi_chu
    # CONG LA BAT BUOC khi don co lenh.
    #
    # Do la loi toi tu mac ngay lo don dau tien (20/09/2026): ra sau don khong
    # kem `cong`, va `_cham` cham moi don khong khai kieu la `CHUA_DO_DUOC` -
    # dung theo luat, nhung nghia la **ca sau don se ve CHUA_DO_DUOC bat ke
    # chung chay the nao**. Mot dem may chay het cong suat de lay ve sau dong
    # "khong cham duoc". Nen chan o day, luc ra don.
    if lenh:
        if cong is None:
            raise ValueError(
                "don '%s' co `lenh` nhung khong khai `cong` - moi ket qua cua "
                "no se la CHUA_DO_DUOC du chay the nao. Khai cong=%r"
                % (ma, list(KIEU_CONG)))
        kieu = cong if isinstance(cong, str) else (cong or {}).get("kieu")
        if kieu not in KIEU_CONG:
            raise ValueError("cong.kieu phai la mot trong %r, nhan duoc %r"
                             % (list(KIEU_CONG), kieu))
        d["cong"] = {"kieu": kieu}
    p = thu / "cho" / ("%s.json" % ma)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def bang(goc: Path | None = None) -> str:
    """Mot man hinh cho ca hai ben doc."""
    t = tom_tat(goc)
    d = ["CAU NOI HAI MAY", "-" * 60,
         "don dang cho : %d" % t["cho"],
         "ket qua      : %d  (DAT %d · AM %d · CHUA_DO_DUOC %d)"
         % (t["xong"], t["DAT"], t["AM"], t["CHUA_DO_DUOC"])]
    if t["trang_thai_la"]:
        d.append("!! %d ket qua co trang_thai LA - da ha xuong CHUA_DO_DUOC"
                 % t["trang_thai_la"])
    if t["hoi_cloud"]:
        d.append("!! %d don dang DOI CLOUD tra loi" % t["hoi_cloud"])
        for h in cho_cloud(goc):
            d.append("   %-22s %s" % (h["ma"], str(h.get("cau_hoi"))[:60]))
    for x in don_dang_cho(goc)[:12]:
        d.append("   cho  %-22s [%s] %s"
                 % (x["ma"], x.get("lan", "?"), str(x.get("muc_tieu"))[:46]))
    return "\n".join(d)


# ------------------------------------------------------------------ chay don
#: Khoa lan TESTER. Mot `terminal64.exe` la rang buoc VAT LY: hai viec tester
#: cung luc ghi de `.mq5`/`.ini`/`.xml` cua nhau **va khong ai bao loi**.
KHOA_TESTER = VIEC / ".khoa_tester"

#: Khoa cu hon ngan nay thi coi nhu tien trinh giu no da chet (may tat giua
#: chung, Ctrl-C). Khong co cai nay thi mot lan tat may lam ket lan TESTER
#: vinh vien, va bang viec van trong nhu binh thuong.
KHOA_CU_GIAY = 6 * 3600.0


def _lay_khoa(thu: Path) -> bool:
    k = thu / ".khoa_tester"
    if k.exists():
        try:
            if (time.time() - k.stat().st_mtime) < KHOA_CU_GIAY:
                return False
        except OSError:
            return False
        k.unlink(missing_ok=True)      # khoa cu -> coi nhu da chet
    try:
        # `x` = tao moi hay nem. Day la phep kiem-va-dat NGUYEN TU o muc he
        # dieu hanh; `if not exists: create` thi hai tien trinh vao cung luc
        # deu thay "chua co" va deu tao.
        with open(k, "x", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        return True
    except FileExistsError:
        return False


def _cham(kieu: str, ma_thoat: int, qua_gio: bool) -> tuple[str, str]:
    """Cham MOT don bang CODE. Tra (trang_thai, ly_do).

    ## VI SAO MA THOAT != 0 KHONG MAC NHIEN LA `AM`

    `qwen/DOC_TRUOC.md` chot: *"Ma thoat != 0, thieu file ra, file ra CU hon
    luc bat dau chay, hay bang co phan lon cot so dung im -> deu la
    `CHUA_DO_DUOC`, khong bao gio la `AM`."*

    Nhung `pytest` la ngoai le CO THAT va phai tach ra: ma thoat **1** cua no
    nghia la "bai chay duoc va co bai do" - mot ket qua DO DUOC, tuc `AM`.
    Con **2 tro len** la loi thu gom / dung giua chung: khong bai nao chay,
    tuc `CHUA_DO_DUOC`. Gop hai cai lam mot thi mot loi cu phap trong file
    test se doc ra thanh "co che khong ra tien".

    Kieu khong khai bao -> `CHUA_DO_DUOC`. Mac dinh phai la "chua noi duoc
    gi", khong phai "khong dat".
    """
    if qua_gio:
        return "CHUA_DO_DUOC", "qua han - giet giua chung, khong doc duoc gi"
    if kieu in ("pytest", "ba_muc"):
        if ma_thoat == 0:
            return "DAT", "moi bai test deu xanh"
        if ma_thoat == 1:
            return "AM", "co bai test do (ma thoat 1)"
        return "CHUA_DO_DUOC", ("thoat %d - voi pytest la loi thu gom hay dung "
                                "giua chung; voi script `ba_muc` la khau do "
                                "hong" % ma_thoat)
    if kieu == "chay_duoc":
        return (("DAT", "chay xong, ma thoat 0") if ma_thoat == 0
                else ("CHUA_DO_DUOC", "ma thoat %d" % ma_thoat))
    return "CHUA_DO_DUOC", ("don khong khai `cong.kieu` nen khong cham duoc "
                            "(ma thoat %d)" % ma_thoat)


def _thay_the(lenh) -> list[str] | None:
    """Doi cac the trong lenh cua don thanh thu that cua MAY DANG CHAY.

    ## VI SAO CAN: don duoc viet tren CLOUD (Linux), chay tren WINDOWS

    Cloud viet `python3`; may chu du an khong co `python3`, va `CLAUDE.md` con
    chot Python o day la MOT duong dan cu the:
    `...\pythoncore-3.14-64\python.exe` - khong duoc dung
    `WindowsApps\python.exe`.

    Mot don viet cung `python3` se that bai tren may voi `FileNotFoundError`,
    va `_cham` se cham no `CHUA_DO_DUOC`. Khong sai ve luat, nhung don nao
    cung hong vi mot ly do khong lien quan gi den noi dung don.

    The `{py}` -> `sys.executable`, tuc dung chinh Python dang chay `q` - va
    do la Python ma `b.cmd` da tro dung.
    """
    if not lenh:
        return None
    import sys
    bang = {"{py}": sys.executable, "{goc}": str(GOC)}
    return [bang.get(str(x), str(x)) for x in lenh]


def chay_don(don: dict, goc: Path | None = None,
             chay_that: bool = True) -> dict:
    """BEN MAY chay MOT don roi ghi ket qua. Tra dict ket qua.

    Khong nem: moi duong that bai deu thanh mot ket qua `CHUA_DO_DUOC` ghi
    xuong dia. Mot don lam `q` nem la mot don giet ca dot chay nhieu ngay.
    """
    g = goc or GOC
    thu = g / "viec"
    ma = don.get("ma") or "khong-ten"
    lan = str(don.get("lan") or "NHE").upper()
    han = float(don.get("han_phut") or 60.0) * 60.0
    kieu = str((don.get("cong") or {}).get("kieu") or "")

    if lan == "TESTER" and not _lay_khoa(thu):
        return {"ma": ma, "trang_thai": "CHUA_DO_DUOC",
                "ly_do": "lan TESTER dang ban - de don lai cho vong sau",
                "hoan": True}
    try:
        lenh = _thay_the(don.get("lenh"))
        if not lenh:
            return dict(ghi_va_doc(ma, "CHUA_DO_DUOC",
                                   "don khong co `lenh` nen khong chay duoc gi",
                                   goc=g))
        if not chay_that:
            return {"ma": ma, "trang_thai": "CHUA_DO_DUOC", "kho": True,
                    "ly_do": "chay KHO - khong thuc thi gi"}
        t0 = time.time()
        qua_gio = False
        try:
            r = subprocess.run([str(x) for x in lenh], cwd=str(g),
                               capture_output=True, text=True, timeout=han)
            ma_thoat, ra, loi = r.returncode, r.stdout, r.stderr
        except subprocess.TimeoutExpired:
            ma_thoat, ra, loi, qua_gio = -9, "", "qua han %.0f phut" % (han / 60), True
        except OSError as e:
            ma_thoat, ra, loi = -1, "", "%s: %s" % (type(e).__name__, e)
        tt, ly_do = _cham(kieu, ma_thoat, qua_gio)
        return dict(ghi_va_doc(
            ma, tt, ly_do,
            bang_chung={"ma_thoat": ma_thoat, "giay": round(time.time() - t0, 1),
                        "lenh": [str(x) for x in lenh],
                        # Giu DUOI chuoi: loi that gan nhu luon o cuoi, con
                        # dau ra co the dai hang nghin dong.
                        "dong_cuoi": (ra or "").splitlines()[-25:],
                        "loi_cuoi": (loi or "").splitlines()[-15:]},
            goc=g))
    finally:
        if lan == "TESTER":
            (thu / ".khoa_tester").unlink(missing_ok=True)


def ghi_va_doc(ma, trang_thai, ly_do="", bang_chung=None, goc=None) -> dict:
    ghi_ket_qua(ma, trang_thai, ly_do, bang_chung=bang_chung, goc=goc)
    return doc_ket_qua(ma, goc=goc)


def chay_mot_don_dang_cho(goc: Path | None = None) -> dict | None:
    """Lay don uu tien cao nhat CHAY DUOC roi chay. `None` = khong co gi.

    Bo qua don TESTER khi lan dang ban thay vi dung ca hang doi - neu khong
    mot don tester dai se chan het cac don NHE phia sau.
    """
    g = goc or GOC
    for d in don_dang_cho(g):
        if str(d.get("lan") or "NHE").upper() == "TESTER" \
                and (g / "viec" / ".khoa_tester").exists():
            continue
        return chay_don(d, goc=g)
    return None
