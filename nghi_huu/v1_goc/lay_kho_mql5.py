# -*- coding: utf-8 -*-
"""Lay mot kho chien luoc MQL5 CO GIAY PHEP RO RANG ve nap_tay/.

KHONG cao MQL5 CodeBase (dieu khoan cam, da gap 403). Chi lay tu GitHub, va chi lay
repo co SPDX license ro rang - dung nguyen tac da co trong brain_sources.py.

  python lay_kho_mql5.py geraked/metatrader5
"""
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
NAP_TAY = HERE / "nap_tay"
UA = {"User-Agent": "TheBrain-research/1.0 (doc tu dong, ton trong robots)"}


def _get(url, nhi_phan=False):
    r = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(r, timeout=60) as f:
        b = f.read()
    return b if nhi_phan else b.decode("utf-8", errors="replace")


def lay(repo):
    thong_tin = json.loads(_get(f"https://api.github.com/repos/{repo}"))
    gp = (thong_tin.get("license") or {}).get("spdx_id")
    if not gp or gp == "NOASSERTION":
        raise SystemExit(f"{repo}: khong ro giay phep -> KHONG lay")
    nhanh = thong_tin.get("default_branch", "main")
    print(f"{repo} | giay phep {gp} | {thong_tin.get('stargazers_count')} sao | nhanh {nhanh}")

    cay = json.loads(_get(
        f"https://api.github.com/repos/{repo}/git/trees/{nhanh}?recursive=1"))
    tep = [t for t in cay.get("tree", [])
           if t["type"] == "blob" and re.search(r"\.(mq5|mqh|md)$", t["path"], re.I)]
    print(f"{len(tep)} tep .mq5/.mqh/.md")

    dich = NAP_TAY / repo.replace("/", "__")
    dich.mkdir(parents=True, exist_ok=True)
    (dich / "_GIAY_PHEP.txt").write_text(
        f"{repo}\nSPDX: {gp}\nnguon: https://github.com/{repo}\n"
        f"tai luc: {time.strftime('%Y-%m-%d %H:%M')}\n", encoding="utf-8")

    n = 0
    for t in tep:
        url = f"https://raw.githubusercontent.com/{repo}/{nhanh}/{t['path']}"
        try:
            noi = _get(url)
        except Exception as e:
            print(f"  [loi] {t['path']}: {str(e)[:50]}")
            continue
        f = dich / t["path"].replace("/", "__")
        f.write_text(noi, encoding="utf-8")
        n += 1
        if n % 10 == 0:
            print(f"  ... {n}")
        time.sleep(0.4)          # ton trong may chu
    print(f"-> {n} tep vao {dich}")
    return dich


if __name__ == "__main__":
    lay(sys.argv[1] if len(sys.argv) > 1 else "geraked/metatrader5")
