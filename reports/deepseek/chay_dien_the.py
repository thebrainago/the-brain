# -*- coding: utf-8 -*-
"""chay_dien_the.py - bo chay goi model re dien kieu + mien cho the phuong phap (tai_lieu/GIAO_VIEC_DEEPSEEK.md muc 3).

Chi GHI vao reports/deepseek/the/ (ban nhap) + reports/deepseek/the/_nhat_ky.jsonl. Khong sua nhan/, kho_phuong_phap/, config/.
Khoa AI Box do proxy gan san (khong doc / in khoa). Chay: python3 reports/deepseek/chay_dien_the.py [ma ...]
Vong: 0 = lan dau (qwen3.8-flash); sua 1 = qwen3.8-flash; sua 2 = ds/deepseek-v4-pro (leo thang). Qua 2 lan sua -> _CON_HONG.txt.
"""
from __future__ import annotations

import dataclasses
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

LAB = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(LAB))
from nhan import dich_tham_so as DTS  # noqa: E402
from nhan import kiem_the_nhap as KT  # noqa: E402
from nhan import luoi as LU  # noqa: E402
from nhan import the_phuong_phap as TP  # noqa: E402

URL = "https://api.ai-box.vn/v1/chat/completions"
DIR = LAB / "reports" / "deepseek" / "the"
NHAT_KY = DIR / "_nhat_ky.jsonl"
MODEL_VONG = ["qwen3.8-flash", "qwen3.8-flash", "ds/deepseek-v4-pro"]
MAX_TOKENS = [1500, 1500, 1500]
SONG_SONG = 6

# ---- TIEN TO GIONG HET moi lan goi (de trung cache), phan doi o CUOI ----
_ThamSo = "\n".join("  - %s (%s)" % (f.name, DTS.LOP_THAM_SO_LUOI.get(f.name, "?")) for f in dataclasses.fields(LU.ThamSo))
_MAU = json.dumps({k: TP.O_CHUAN[k] for k in ("luoi_buoc_gian_dan", "lot_nhan", "lenh_doi_ung_sau_n_lenh")}, ensure_ascii=True)
TIEN_TO = """Ban dien KIEU + MIEN cho cac o tham so cua mot THE PHUONG PHAP (mot co che cua con bot forex luoi/DCA).
Tra DUNG MOT doi tuong JSON (khong giai thich, khong markdown) la BAN THE DAY DU, giu NGUYEN moi khoa, CHI DOI khoa "tham_so".

LUAT cho "tham_so" (danh sach 1..8 o):
- Moi o la {"ten","lop","don_vi","mien","ten_trong_set":null,"ten_trong_engine":null}.
- "ten": snake_case ASCII chu thuong (^[a-z][a-z0-9_]{1,40}$), KHONG trung. Phai la ten THAT cua tham so: neu the da co ten
  (vd 'InpMaxLots', 'ADX') thi doi sang snake_case cung nghia ('inp_max_lots', 'adx'); neu khop truong cua luoi.ThamSo thi DUNG
  ten truong do. Khong bia o ngoai y nghia cua the. Neu ten hien co la CAU MO TA tieng Viet thi dat ten snake_case ngan cung nghia.
  Neu the khong co o nao nhung co che co tham so ro rang thi them 1..4 o; neu hoan toan khong co tham so thi giu danh sach rong KHONG DUOC
  (kiem_the_nhap can 1..8 o) -> dat o cong tac/khoang hop ly nhat theo mo ta.
- "lop": MOT trong """ + ", ".join(DTS.LOP) + """ (khong dung CHUA_PHAN_LOP).
  KC_BUOC khoang cach tang luoi (pip) | KC_TP khoang cach chot loi (pip) | KC_SL khoang cach cat lo (pip) | TAM tam luoi |
  SO_DEM so lenh/so nen/so lan | HE_SO he so nhan khong thu nguyen | LOT lot | TIEN tien (USD) | PHI spread/phi (point) |
  THOI_GIAN gio/phut/so nen | NGUONG_CHI_BAO nguong chi bao (RSI, ADX, ATR...) | CONG_TAC bat/tat/lua chon (mien co the null).
- "don_vi": chuoi khong rong (pip, lenh, lot, tien, point, phut, gio, nen, %, he_so...) TRU lop CONG_TAC / HE_SO (de "").
- "mien": [min, max, buoc] toan SO, min <= max, buoc > 0, khoang hop ly de RAI LUOI thu (khong phai gia tri cua bot nao); CONG_TAC mien null.
- Moi o co nhan 'tho' (them khoa "nhan":"tho"). Khong ket luan tot/xau, khong cham diem.
Cac truong cua luoi.ThamSo that (ten -> lop):
""" + _ThamSo + """
Vi du o da dien tay cua cac khoi mau (O_CHUAN): """ + _MAU + """
Tra dung mot JSON. Bat dau bang { va ket thuc bang }.
--- THE CAN DIEN (phan thay doi) ---
"""


def goi(model: str, noi_dung: str, max_tokens: int) -> dict:
    t = time.time()
    # TAT che do suy luan: bat len thi token nghi an het max_tokens (ds -> noi dung rong) hoac qwen bi 502 sau ~30s (do 05/10).
    tat = {"thinking": {"type": "disabled"}} if model.startswith("ds/") else {"enable_thinking": False}
    r = requests.post(URL, json={"model": model, "messages": [{"role": "user", "content": noi_dung}], "max_tokens": max_tokens,
                                 "temperature": 0.1, **tat}, timeout=180)
    if r.status_code != 200:
        return {"loi": "HTTP %d %s" % (r.status_code, r.text[:200]), "giay": time.time() - t, "model": model}
    j = r.json()
    u = j.get("usage", {})
    return {"text": (j["choices"][0]["message"].get("content") or ""), "model": model, "giay": time.time() - t,
            "vao": u.get("prompt_tokens", 0), "ra": u.get("completion_tokens", 0),
            "cache": u.get("prompt_cache_hit_tokens", 0) or (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0)}


def tach_json(s: str):
    s = re.sub(r"^```(?:json)?|```$", "", s.strip(), flags=re.M).strip()
    a, b = s.find("{"), s.rfind("}")
    if a < 0 or b <= a:
        return None
    try:
        return json.loads(s[a:b + 1])
    except Exception:
        return None


def lam_mot(ma: str) -> dict:
    goc = TP.doc(ma)
    nd = TIEN_TO + json.dumps(goc, ensure_ascii=True)
    kq = {"ma": ma, "so_lan_sua": 0, "dat": False, "goi": [], "loi_cuoi": []}
    for vong in range(3):
        model, mt = MODEL_VONG[vong], MAX_TOKENS[vong]
        g = goi(model, nd, mt)
        g["vong"] = vong
        if "loi" in g:
            time.sleep(3)
            g = goi(model, nd, mt)
            g["vong"] = vong
        kq["goi"].append({k: v for k, v in g.items() if k != "text"})
        if "loi" in g:
            loi = ["goi that bai: " + g["loi"]]
            ban = None
        else:
            ban = tach_json(g["text"])
            loi = ["khong ra JSON hop le (bi cat? hay co chu thua) - tra DUNG mot JSON"] if ban is None else None
        if ban is not None:
            for o in ban.get("tham_so", []) if isinstance(ban.get("tham_so"), list) else []:
                if isinstance(o, dict):
                    o["nhan"] = "tho"
            ban["ghi_chu_tho"] = {"viec": "dien kieu + mien", "so_lan_sua": vong, "model": model, "nhan": "tho"}
            loi = KT.cham({k: v for k, v in ban.items() if k != "ghi_chu_tho"}) or None
        if not loi:
            DIR.mkdir(parents=True, exist_ok=True)
            (DIR / (ma + ".json")).write_text(json.dumps(ban, ensure_ascii=True, indent=1) + "\n", encoding="utf-8")
            kq.update(dat=True, so_lan_sua=vong, loi_cuoi=[])
            return kq
        kq["so_lan_sua"] = vong
        kq["loi_cuoi"] = loi[:5]
        nd = (TIEN_TO + json.dumps(goc, ensure_ascii=True) + "\n--- BAN BAN DA TRA VA LOI MAY CHAM ---\n" + (g.get("text") or "")[:3000]
              + "\nLOI: " + "; ".join(loi[:6]) + "\nSua DUNG cac loi tren, tra lai DUNG mot JSON day du.")
    kq["so_lan_sua"] = 2
    return kq


def main(argv: list) -> int:
    ds = argv[1:] or (DIR / "_DANH_SACH_VIEC.txt").read_text(encoding="utf-8").split()
    t0 = time.time()
    with ThreadPoolExecutor(SONG_SONG) as ex:
        kqs = list(ex.map(lam_mot, ds))
    with NHAT_KY.open("a", encoding="utf-8") as f:
        for k in kqs:
            f.write(json.dumps(k, ensure_ascii=True) + "\n")
    hong = [k["ma"] for k in kqs if not k["dat"]]
    if hong:
        (DIR / "_CON_HONG.txt").write_text("\n".join(hong) + "\n", encoding="utf-8")
    print("%d the, %d dat, %d hong, %.0fs" % (len(kqs), len(kqs) - len(hong), len(hong), time.time() - t0))
    for k in kqs:
        if not k["dat"]:
            print("HONG", k["ma"], k["loi_cuoi"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
