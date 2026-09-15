# -*- coding: utf-8 -*-
"""_do_dien_dan_quoc_gia.py - DO xem dien dan nao VAO DUOC tu may nay.

## Vi sao do truoc khi dang ky

Chu du an, 15/09/2026: *"o vietnam co dien dan traderviet, vay o hang bao nhieu
nuoc kia cung co nhung dien dan nhu the. Can them vao bo thu thap va tien hanh
thu thap."*

Dung, va `tru/seeker.py` dang thieu han lop nay: cac nguon phi-Anh hien co
(qiita, habr, smart-lab, cnblogs, velog) deu la **blog ky thuat chung**, khong
mot cai nao la dien dan GIAO DICH.

Nhung khong duoc dang ky bua roi bao "da them 20 nguon". Hai bai hoc cu:
  - danh sach "bi chan tren may nay" do 22/08 hoa ra **phan lon SAI** khi do lai
  - `Accept-Encoding: br` khi khong co brotli tra HTTP 200 voi `r.text` la RAC:
    cung mot trang cho 21.245 ky tu / 0 link so voi 82.347 ky tu / 40 link

Nen file nay DO truoc: moi ung vien mot luot, ghi lai **so ky tu** va **so link
bai**. Vao duoc ma 0 link thi cung nhu khong vao duoc - do la dau hieu trang
dung JS hoac ta doc nham kieu trang (trang TIM KIEM vs trang CHUYEN MUC, dung
cai bay da sap voi habr).

Chay:  python _do_dien_dan_quoc_gia.py
Ket qua ghi ra `reports/DIEN_DAN_QUOC_GIA.json` de buoc dang ky doc lai.
"""
from __future__ import annotations

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from tru import seeker as SK   # noqa: E402

#: (ma ngon ngu, ten, URL hat giong, regex link BAI VIET).
#:
#: Chon trang CHUYEN MUC / trang chu chu khong phai trang TIM KIEM - habr da
#: day mot lan: trang tim kiem dung JS tra 535 ky tu va 0 link, trang chuyen
#: muc tra 23.631 ky tu va 108 link.
UNG_VIEN = [
    # --- Viet Nam: cai chu du an chi ra ---
    # Bai viet cua traderviet la `/t/<slug>`, KHONG phai `/threads/`. Ban do
    # dau tien doan theo XenForo chuan va ra 0 link tren mot trang 156k ky tu.
    ("vi", "traderviet", "https://traderviet.com/", r"traderviet\.com/t/[^\"'\s]+"),
    ("vi", "traderviet_ea", "https://traderviet.com/forums/robot-ea-indicator.44/",
     r"traderviet\.com/t/[^\"'\s]+"),
    # --- Nga: nha cua MetaQuotes, kho MQL lon nhat ---
    ("ru", "mql5_forum_ru", "https://www.mql5.com/ru/forum",
     r"mql5\.com/ru/forum/\d+"),
    ("ru", "mmgp", "https://mmgp.com/forums/", r"mmgp\.com/(showthread|threads)[^\"']*"),
    ("ru", "smartlab_blog", "https://smart-lab.ru/blogs/",
     r"smart-lab\.ru/(blog|company)/[^\"']+/\d+"),
    # --- Nhat: ban le FX tu dong rat manh, co ca cho ban EA rieng ---
    ("ja", "gogojungle", "https://www.gogojungle.co.jp/systemtrade/fx",
     r"gogojungle\.co\.jp/(systemtrade|fx)/[^\"']*\d+"),
    ("ja", "fxon", "https://fx-on.com/",
     r"fx-on\.com/(?:\w\w/)?(?:post|systemtrade|review)/[^\"'\s]*\d+"),
    ("ja", "note_fx", "https://note.com/hashtag/FX自動売買",
     r"note\.com/[^/\"']+/n/n[0-9a-f]+"),
    # --- Trung ---
    ("zh", "fx168", "https://www.fx168.com/", r"fx168\.com/[^\"']+\.html"),
    # --- Thai: pantip rat lon ---
    ("th", "thaiforexschool", "https://www.thaiforexschool.com/",
     r"thaiforexschool\.com/[^\"']+"),
    ("th", "pantip_sinlapa", "https://pantip.com/tag/Forex",
     r"pantip\.com/topic/\d+"),
    # An Do: `traderji.com` tra ve **trang mac dinh cua Apache** (`/manual`,
    # `/ubuntu/+source/apache2`) - ten mien con song nhung khong con trang web.
    # Trung: `bbs.pinggu.org` tra 13,7k ky tu toan CSS + `/member.php` = tuong
    # dang nhap. Ca hai bo khoi danh sach chu khong de lai, neu khong thi moi
    # luot do deu bao "khong vao duoc" va ta quen mat ly do that.
    # --- Indonesia ---
    ("id", "indomt5", "https://www.kaskus.co.id/forum/64/forex",
     r"kaskus\.co\.id/thread/[0-9a-f]+"),
    # --- Tho Nhi Ky ---
    ("tr", "forexforum_tr", "https://www.forexforum.com.tr/",
     r"forexforum\.com\.tr/[^\"']+"),
    # --- Ba Lan ---
    ("pl", "forex_nawigator", "https://www.forex-nawigator.biz/forum/",
     r"forex-nawigator\.biz/forum/[^\"']+"),
    # --- Duc ---
    ("de", "wallstreet_online", "https://www.wallstreet-online.de/diskussion/",
     r"wallstreet-online\.de/diskussion/[^\"']+"),
    # --- A Rap ---
    ("ar", "arabictrader", "https://www.arabictrader.com/", r"arabictrader\.com/[^\"']+"),
    # --- Anh ngu, nhung chua tung co trong seeker ---
    ("en", "forexfactory", "https://www.forexfactory.com/forum",
     r"forexfactory\.com/thread/\d+"),
    ("en", "babypips_forum", "https://forums.babypips.com/",
     r"forums\.babypips\.com/t/[^\"']+/\d+"),
]


def do_mot(x) -> dict:
    ma, ten, url, loc = x
    t0 = time.time()
    txt = None
    try:
        txt = SK._lay(url, timeout=25)
    except Exception as e:
        return {"ma": ma, "ten": ten, "url": url, "trang_thai": "LOI",
                "loi": repr(e)[:80], "giay": round(time.time() - t0, 1)}
    giay = round(time.time() - t0, 1)
    if not txt:
        return {"ma": ma, "ten": ten, "url": url, "trang_thai": "KHONG_VAO_DUOC",
                "so_ky_tu": 0, "so_link": 0, "giay": giay}
    # HREF TUONG DOI. Ban do dau tien khop regex thang tren HTML tho va
    # mql5.com ra dung **1 link** trong khi trang co 175 - vi moi href deu la
    # `/ru/forum/N` chu khong phai `https://www.mql5.com/ru/forum/N`. Dung cai
    # bay `seeker.n_mql5_code` da ghi lai tu truoc, va toi vua sap lai.
    tuyet_doi = " ".join(urljoin(url, h) for h in
                         re.findall(r'href="([^"]{2,200})"', txt))
    link = set(re.findall(loc, txt)) | set(re.findall(loc, tuyet_doi))
    # Vao duoc ma 0 link BAI thi cung nhu khong vao duoc: hoac trang dung JS,
    # hoac ta doc nham kieu trang. Ghi rieng de khong nham voi "bi chan".
    tt = "VAO_DUOC" if link else ("VAO_NHUNG_0_LINK" if len(txt) > 2000
                                  else "TRA_VE_RAC")
    return {"ma": ma, "ten": ten, "url": url, "trang_thai": tt,
            "so_ky_tu": len(txt), "so_link": len(link),
            "link_mau": sorted(link)[:3], "giay": giay}


def main() -> int:
    print("DO %d dien dan quoc gia - vao duoc tu may nay khong\n" % len(UNG_VIEN))
    with ThreadPoolExecutor(max_workers=6) as ex:
        ket = list(ex.map(do_mot, UNG_VIEN))
    ket.sort(key=lambda d: (-d.get("so_link", 0), d["ma"]))
    print("%-4s %-20s %-18s %9s %7s %6s" %
          ("ma", "ten", "trang thai", "ky tu", "link", "giay"))
    print("-" * 70)
    for d in ket:
        print("%-4s %-20s %-18s %9s %7s %6s"
              % (d["ma"], d["ten"], d["trang_thai"], d.get("so_ky_tu", "-"),
                 d.get("so_link", "-"), d.get("giay", "-")))
    vao = [d for d in ket if d["trang_thai"] == "VAO_DUOC"]
    print("\n%d/%d VAO DUOC va co link bai" % (len(vao), len(ket)))
    print("ngon ngu phu duoc: %s"
          % ", ".join(sorted({d["ma"] for d in vao})))
    ra = LAB / "reports" / "DIEN_DAN_QUOC_GIA.json"
    ra.parent.mkdir(exist_ok=True)
    ra.write_text(json.dumps(
        {"luc": time.strftime("%Y-%m-%d %H:%M:%S"), "ket": ket},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("ghi %s" % ra.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
