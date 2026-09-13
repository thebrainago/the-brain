# -*- coding: utf-8 -*-
"""go_html.py - KHAU CON THIEU giua THU THAP va BOC: go trang HTML ra van ban.

## LO HONG DO DUOC 13/09/2026

Ban giao hom truoc ghi *"con 97% kho chua boc: 5.131 file ma nguon, 3.771 tai
lieu hoc thuat"* va xep no la mot bai toan THONG LUONG (goi LLM nhanh hon,
nhieu luong hon). Do that tren dung hang ton do:

    5.486 ban doc chua boc, cho qua bo loc dau vao cua `boc_llm.ung_vien`
        3.948  bi `_la_html_tho` chan   (72%)
        1.530  cham 0 dau hieu luat
            8  QUA

Tuc `boc_llm.boc(gioi_han=300)` chi tim duoc **8 ung vien** tren mot kho 5.486
ban. Khong mot so luong nao, khong mot model nao cuu duoc con so do. Nut that
khong nam o khau BOC.

Vao trong 3.948 ban bi chan:

    2.727  github     - trang repo tho, ~289.000 ky tu boilerplate moi trang
      859  mql5_code  - trang https://mql5.com/en/code/NNNNN, ~60.000 ky tu
      362  con lai    - hackernews, cnblogs, velog, reddit...

`_la_html_tho` **khong sai**. No lam dung viec cua no: chan trang HTML chua boc
de khoi dot mot luot goi API tren 289 KB boilerplate. Cai sai la khong co ai
DUNG SAU no. Khau thu thap luu nguyen trang, bo loc chan lai, va giua hai cai
do la mot khoang trong - nen ca lop nguon nam do khong bao gio den duoc LLM.

## FILE NAY LAM GI, VA KHONG LAM GI

LAM: go HTML -> van ban sach, KHONG can mang. Voi trang github lay duoc README
(phan `.markdown-body` - thuong la cho tac gia mo ta chien luoc); voi trang
mql5 code lay duoc phan mo ta co che cua tac gia.

KHONG LAM: lay MA NGUON ve. Do 13/09 tren chinh cac trang do: trang
`mql5.com/en/code/43355` dai 62.924 ky tu chua **0 lan** chuoi `OnTick`,
`OrderSend`, `CTrade` - ma nam sau nut tai, khong nam trong trang. Trang repo
github cung vay. Nen file nay tra ve MO TA, con viec di tai file that la cua
khau Seeker (`nhan/ma_nguon.py`). Hai viec khac nhau, dung gop.

## VI SAO GHI DE `van_ban` CHU KHONG THEM BANG

Dia con 8,6 GB tren o C va `nao.db` da 1,5 GB. Giu ca HTML goc lan ban go la
nhan doi cho ton nhat. Ban go giu `so_ky_tu_goc` nen van truy nguoc duoc co,
va `kieu` doi thanh `<kieu>_go_html` nen khong bao gio go hai lan.
"""
from __future__ import annotations

import concurrent.futures as _cf
import re
import sys
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(GOC))

from nhan import so as SO  # noqa: E402

#: Hau to danh dau ban da go - de `la_html_tho` khong go lai lan hai.
HAU_TO = "_go_html"

#: The khong bao gio chua noi dung nguoi doc.
BO_THE = ("script", "style", "noscript", "svg", "nav", "header", "footer",
          "form", "iframe", "template", "button", "aside")

#: Cho chua noi dung THAT, xep theo do uu tien. Dung CSS selector cua bs4.
#:
#: Thu tu quan trong: tren trang github, `.markdown-body` (README) la thu duy
#: nhat tac gia viet; con `<article>` boc ca thanh dieu huong. Tren trang mql5
#: code, mo ta co che nam trong `.code-description`.
UU_TIEN = (
    ".markdown-body", "#readme", ".code-description", ".codeDescription",
    "#description", ".post-content", ".entry-content", ".article-content",
    "article", "main", "#content", ".content",
)

_KHOANG = re.compile(r"[ \t\r\f\v]+")
_DONG = re.compile(r"\n{3,}")


def la_html_tho(vb: str) -> bool:
    """Ban doc la TRANG HTML CHUA GO.

    Dinh nghia nay TRUNG voi `boc_llm._la_html_tho` va do la co y: hai file phai
    dong y voi nhau ve "cai gi la HTML tho", neu khong thi bo loc chan mot tap
    con `go_kho` khong go - va phan chenh lech do nam ket mai mai.
    """
    dau = (vb or "")[:600].lstrip()
    if "<!doctype html" in dau.lower() or dau.startswith("<html"):
        return True
    mau = (vb or "")[:2000]
    return mau.count("<") > 40 and mau.count("</") > 20


def go(vb: str, url: str = "") -> str:
    """HTML -> van ban sach. Tra chuoi rong neu khong con gi."""
    from bs4 import BeautifulSoup, Comment
    sup = BeautifulSoup(vb or "", "html.parser")
    for the in sup(list(BO_THE)):
        the.decompose()
    # Comment HTML cua github chua ca mot ban sao trang -> phai bo.
    for c in sup.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()

    phan = None
    for chon in UU_TIEN:
        try:
            phan = sup.select_one(chon)
        except Exception:
            phan = None
        if phan is not None and len(phan.get_text(" ", strip=True)) > 200:
            break
        phan = None
    goc = phan if phan is not None else (sup.body or sup)

    vb2 = goc.get_text("\n", strip=True)
    vb2 = _KHOANG.sub(" ", vb2)
    vb2 = _DONG.sub("\n\n", vb2)
    return vb2.strip()


def _mot(d: dict) -> dict:
    try:
        moi = go(d["van_ban"], d.get("url") or "")
    except Exception as e:
        return {"id": d["id"], "loi": repr(e)[:200]}
    return {"id": d["id"], "moi": moi,
            "goc": d.get("so_ky_tu") or len(d["van_ban"]),
            "kieu": d.get("kieu") or "khac"}


def ung_vien(gioi_han: int = 500) -> list[dict]:
    """Ban doc DANG la HTML tho.

    Loc bang chinh `la_html_tho` chu khong bang SQL: mot truy van
    `LIKE '%<!DOCTYPE%'` bo sot ban bi cat dau (nhom `the_nhieu`).
    """
    ds = SO.nhieu(
        "SELECT id, url, kieu, so_ky_tu, so_ky_tu_goc, van_ban FROM noi_dung "
        "WHERE kieu NOT LIKE ? AND so_ky_tu > 800 AND kieu != 'khong_doc_duoc' "
        "ORDER BY so_ky_tu DESC LIMIT ?", "%" + HAU_TO, gioi_han * 4) or []
    return [d for d in ds if la_html_tho(d["van_ban"])][:gioi_han]


#: Duoi nguong nay thi ban go khong con gi de boc - danh dau de no roi khoi
#: hang doi thay vi quay lai moi vong.
#:
#: 800 la dung con so ma `boc_llm.ung_vien` doi (`so_ky_tu > 800`). Dat thap hon
#: chi de lai mot lop ban "go duoc nhung khong ai lay" - dung cai bay hang doi
#: bi rac chiem da gap voi 406 URL chet.
TOI_THIEU = 800


def go_kho(gioi_han: int = 500, luong: int = 8, in_ra=print) -> dict:
    """Go `gioi_han` ban doc HTML tho, ghi de `van_ban`. Tra ve bang dem."""
    from nhan import dia as _DIA
    _DIA.du_cho(viec="go kho HTML")
    ds = ung_vien(gioi_han)
    in_ra(f"  {len(ds)} ban HTML tho")
    if not ds:
        return {"ban": 0, "rong": 0, "loi": 0}
    t0 = time.time()
    ket = []
    # TIEN TRINH chu khong LUONG. `bs4` voi `html.parser` la Python thuan nen
    # no giu GIL suot ca luot phan tich: do 13/09 tren 30 trang, 8 luong het
    # 18,9 giay = 0,63 giay/trang, dung bang chay mot luong. Voi 3.948 trang do
    # la 41 phut cho mot viec dang le 4.
    #
    # Day KHONG mau thuan voi phep do "20 luong = 1 luong" cua bai mang lon
    # (nghet bang thong RAM): o day nut that la CPU giai ma the, va CPU thi
    # con trong - nen tach tien trinh an that.
    voi = _cf.ProcessPoolExecutor if luong > 1 else _cf.ThreadPoolExecutor
    with voi(max_workers=luong) as ex:
        for i, r in enumerate(ex.map(_mot, ds, chunksize=4), 1):
            ket.append(r)
            if i % 100 == 0:
                in_ra(f"  ... {i}/{len(ds)}  ({time.time()-t0:.0f}s)")

    dem = {"ban": 0, "rong": 0, "loi": 0, "ky_tu_goc": 0, "ky_tu_moi": 0}
    with SO.ket_noi() as cn:
        for r in ket:
            if r.get("loi"):
                dem["loi"] += 1
                continue
            moi, goc = r["moi"], r["goc"]
            dem["ky_tu_goc"] += goc
            kieu_moi = ("hong" if len(moi) < TOI_THIEU else r["kieu"]) + HAU_TO
            cn.execute(
                "UPDATE noi_dung SET kieu=?, van_ban=?, so_ky_tu=?, "
                "so_ky_tu_goc=COALESCE(so_ky_tu_goc, so_ky_tu) WHERE id=?",
                (kieu_moi, moi, len(moi), r["id"]))
            if len(moi) < TOI_THIEU:
                dem["rong"] += 1
            else:
                dem["ban"] += 1
                dem["ky_tu_moi"] += len(moi)
    dem["giay"] = round(time.time() - t0, 1)
    dem["giam_lan"] = round(dem["ky_tu_goc"] / max(dem["ky_tu_moi"], 1), 1)
    return dem


def con_ton(mau: int = 8000) -> int:
    """So ban HTML tho con lai trong `mau` ban dai nhat chua go."""
    return len(ung_vien(mau))


if __name__ == "__main__":
    import json
    a = sys.argv[1:]
    if a and a[0] == "--xem":
        print("ung vien HTML tho:", con_ton())
    else:
        n = int(a[0]) if a else 500
        lg = int(a[1]) if len(a) > 1 else 8
        print(json.dumps(go_kho(n, lg), ensure_ascii=False))
