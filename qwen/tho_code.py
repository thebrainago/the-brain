# -*- coding: utf-8 -*-
"""tho_code.py - GIAO VIEC VIET MA CHO LLM RE, con cong van la code.

Chu du an 19/09/2026: *"code bang claude rat ton, cau co the goi llm vao nhu
tren may toi khong, toi nghi se tiet kiem hon nhieu con cau lo giam sat thoi"*.

Dung. Va `qwen/` da co san duong LLM (`mo_hinh.chat`) cung nguyen tac phan
viec (`cong.py`): **qwen doc va viet; code cham va chan.** Cai thieu la mot
THO CODE - dua mot DON HANG, no sua file, chay lenh cham, lap den khi xanh.

## CHIA VIEC NAY DUA TREN MOT QUAN SAT CU THE

Phien 19/09 tim ra ba loi that trong bo mo phong. Ca ba **khong** tim ra bang
cach go ma - chung tim ra bang cach CHAY THU roi NGHI NGO mot ket qua dep:

  * 51/84 cau hinh duoc cham "CHAY_DUOC" tren random walk -> lan ra `cat_hoa`
    dang gat bien do trong nen;
  * 12.805%/nam voi sut giam 4,67 -> lan ra cong phan giai bo sot cac nut;
  * 50% lot tren chuoi da pha edge -> lan ra "cham mot duong khong phan biet
    duoc gi".

Mot mo hinh re viet ma se sinh ra dung nhung dong ma do, va se bao cao "51 cau
hinh CHAY_DUOC" nhu mot THANH CONG.

Nen ranh gioi khong phai "re lam viec de, dat lam viec kho". No la:

    DAT (hoac nguoi)  quyet dinh XAY GI, va viet BAI TEST - tuc dac ta
    RE                go phan cai dat cho den khi bai test xanh
    CODE              cham dat/khong. Khong ai duoc tu phan.

Bai test la hop dong. Viet duoc bai test dung la phan kho; dien cho no xanh la
phan lap lai.

## RAO CHAN QUAN TRONG NHAT: KHONG DUOC SUA FILE TEST

Kieu hong kinh dien cua moi vong lap "sua den khi xanh": mo hinh thay sua test
de hon sua ma. Luc do bang so van xanh con cai cong thi bien mat.

Day khong phai noi lo ly thuyet. Chinh trong phien 19/09, bai
`test_ty_le_lot_tren_nhieu_phai_THAP` do o muc 50%, va cach de nhat la ha
nguong. Neu ha thi phat hien "cham mot duong khong phan biet duoc gi" da khong
bao gio ton tai.

Nen: file test nam ngoai `duoc_sua` LA MOT LOI DON HANG (nem `ValueError`), va
moi khoi ma tro toi mot file ngoai danh sach deu bi bo qua **truoc khi ghi**.

## BA TRANG THAI, KHONG PHAI HAI

    DAT           lenh cham chay duoc va tra ma thoat 0
    KHONG_DAT     lenh cham chay duoc va van do sau khi het vong
    CHUA_DO_DUOC  duong LLM hong, tra rong, hay lenh cham khong chay duoc

Trang thai thu ba la trang thai quan trong nhat. Het quota, lech ten provider,
`max_tokens` cat giua chung - ca ba deu tra ve rong va **doc y het** "mo hinh
khong sua noi". Lich su lab day nhung lan lan mot khau HONG voi mot ket qua am
(xem `qwen/cong.py`).

## HET VONG THI TRA LAI NGUYEN TRANG

Bo dang mot file da sua giua chung con te hon khong lam gi: lan sau chay se
xuat phat tu mot trang thai khong ai mo ta duoc. Nen khi het vong ma chua xanh,
moi file trong `duoc_sua` duoc tra ve dung noi dung luc bat dau.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

DAT, KHONG_DAT, CHUA = "DAT", "KHONG_DAT", "CHUA_DO_DUOC"

#: ```python:duong/dan.py  ... ```  - khoi ma co ghi ten file.
#: ```python ... ```                - khoi ma khong ghi ten (file dau tien).
_KHOI = re.compile(r"```(?:[a-zA-Z0-9_+-]*)?(?::([^\s`]+))?[ \t]*\n(.*?)```",
                   re.S)


def tach_khoi(vb: str) -> list[tuple[str | None, str]]:
    """(ten file hoac None, noi dung) cho moi khoi ma trong cau tra loi."""
    return [(m.group(1), m.group(2)) for m in _KHOI.finditer(vb or "")]


def _chay(lenh, goc: Path) -> tuple[int | None, str]:
    """Ma thoat va dau ra. `None` = lenh KHONG CHAY DUOC, khac han ma thoat != 0."""
    try:
        p = subprocess.run(lenh, cwd=str(goc), capture_output=True, text=True,
                           timeout=900)
    except (OSError, subprocess.SubprocessError) as e:
        return None, "%s: %s" % (type(e).__name__, e)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _nhac(don: dict, goc: Path, loi: str) -> str:
    """Loi nhac: DAC TA (bai test) + ma hien tai + loi that cua vong truoc."""
    test = (goc / don["file_test"]).read_text(encoding="utf-8", errors="ignore")
    phan = ["Ban dang sua ma Python cho mot du an.",
            "MUC TIEU: " + str(don.get("muc_tieu", "")), "",
            "BAI TEST duoi day la DAC TA. Ban KHONG duoc sua no.",
            "```python", test[:8000], "```", ""]
    for ten in don["duoc_sua"]:
        p = goc / ten
        cur = p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""
        phan += ["FILE DUOC SUA: " + ten, "```python:" + ten, cur[:12000],
                 "```", ""]
    if loi:
        phan += ["LOI CUA LAN CHAY TRUOC:", "```", loi[-4000:], "```", ""]
    phan += ["Tra ve TOAN BO noi dung moi cua file can sua, trong mot khoi",
             "```python:<ten file>```. Chi sua cac file da liet ke o tren.",
             "Khong giai thich dai dong."]
    return "\n".join(phan)


def lam(don: dict, hoi=None) -> dict:
    """Thuc hien mot DON HANG. `hoi(nhac) -> str` la duong LLM.

    `don`:
        ma, muc_tieu     mo ta
        goc              thu muc du an
        file_test        bai test dong vai DAC TA - KHONG duoc nam trong `duoc_sua`
        lenh_cham        danh sach doi so, vi du [sys.executable, "-m", "pytest", ...]
        duoc_sua         danh sach file mo hinh duoc phep ghi
        so_vong_toi_da   so lan thu
    """
    goc = Path(don.get("goc") or ".").resolve()
    duoc = list(don.get("duoc_sua") or [])
    test = str(don.get("file_test") or "")

    # DON HANG SAI thi dung han, khong chay nua nuoc. De bai test vao
    # `duoc_sua` la cho phep mo hinh sua chinh cai cong dang cham no.
    if test and test in duoc:
        raise ValueError(
            "file_test '%s' nam trong `duoc_sua` - do la cho phep mo hinh sua "
            "chinh dac ta dang cham no" % test)
    if not duoc:
        raise ValueError("`duoc_sua` rong - khong co gi de sua")

    if hoi is None:
        from . import tac_tu as TT
        hoi = TT.hoi

    ma0, ra0 = _chay(don["lenh_cham"], goc)
    if ma0 is None:
        return {"trang_thai": CHUA, "so_vong": 0,
                "ly_do": "lenh cham khong chay duoc: " + ra0[:200]}
    if ma0 == 0:
        return {"trang_thai": DAT, "so_vong": 0,
                "ly_do": "da xanh san - khong goi LLM lan nao"}

    # Ban chup de tra lai nguyen trang neu het vong ma chua xanh.
    chup = {t: (goc / t).read_text(encoding="utf-8", errors="ignore")
            for t in duoc if (goc / t).exists()}

    loi = ra0
    hong_llm, so_vong = 0, 0
    for _ in range(int(don.get("so_vong_toi_da", 5))):
        so_vong += 1
        try:
            tl = hoi(_nhac(don, goc, loi))
        except Exception as e:
            hong_llm += 1
            loi = "%s: %s" % (type(e).__name__, e)
            continue
        khoi = tach_khoi(tl or "")
        if not khoi:
            hong_llm += 1
            continue
        da_ghi = False
        for ten, noi_dung in khoi:
            # Khoi khong ghi ten -> hieu la file DUOC SUA dau tien. Khoi ghi
            # ten mot file NGOAI danh sach thi bo qua HOAN TOAN: khong ghi, va
            # cung khong bao loi cho mo hinh biet de no thu lai duong khac.
            dich = duoc[0] if ten is None else ten
            if dich not in duoc:
                continue
            (goc / dich).write_text(noi_dung, encoding="utf-8")
            da_ghi = True
        if not da_ghi:
            hong_llm += 1
            continue
        ma, ra = _chay(don["lenh_cham"], goc)
        if ma is None:
            return {"trang_thai": CHUA, "so_vong": so_vong,
                    "ly_do": "lenh cham khong chay duoc: " + ra[:200]}
        if ma == 0:
            return {"trang_thai": DAT, "so_vong": so_vong, "ly_do": ""}
        loi = ra

    for t, vb in chup.items():
        (goc / t).write_text(vb, encoding="utf-8")

    # LLM hong CA so vong -> chua do duoc, khong phai "mo hinh khong sua noi".
    if hong_llm >= so_vong:
        return {"trang_thai": CHUA, "so_vong": so_vong,
                "ly_do": "duong LLM khong tra ve khoi ma nao: " + str(loi)[:200]}
    return {"trang_thai": KHONG_DAT, "so_vong": so_vong,
            "ly_do": str(loi)[-600:]}
