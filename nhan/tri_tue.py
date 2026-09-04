# -*- coding: utf-8 -*-
"""tri_tue.py - Cau noi OpenAI tuy chon cho tien trinh nen 24/7.

Dung de EVO (va sau nay cac tru khac) suy nghi sau hon: doc so lieu van hanh,
dat gia thuyet ve nguyen nhan, de xuat cai tien. KHONG dung de sinh ket luan
giao dich - moi ket luan ve tien van phai di qua `nhan/cong.py`.

Claude/Anthropic da nghi su dung. Module nay khong tu dong tim CLI va khong co
duong fallback sang mot nha cung cap khac. Chi co hai trang thai:
  - `tat` (mac dinh);
  - `openai`, va chi khi co `OPENAI_API_KEY` trong moi truong cung model duoc
    khai bao ro trong config.

VI SAO CAN HAN MUC: day la tien trinh NEN chay 24/7. Mot vong lap goi LLM khong
co phanh se dot tien va rate limit ma khong ai nhin thay. Nen o day co:
  - tran so lan goi MOI NGAY (mac dinh 40)
  - khoang cach toi thieu giua hai lan goi (mac dinh 10 phut)
  - bo nho tam: cung mot cau hoi trong N gio -> tra lai ket qua cu, khong goi lai
  - moi lan goi deu ghi vao so (bang `chi_so_vh` + su kien) de dem duoc
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import so as SO
else:
    from . import so as SO

LAB = Path(__file__).resolve().parent.parent
CAU_HINH = LAB / "config" / "tri_tue.json"
BO_NHO = LAB / "reports" / "tri_tue_cache.json"
MAC_DINH = {
    "model_openai": "",
    "max_tokens": 8000,
    "tran_moi_ngay": 40,
    "cach_nhau_giay": 600,
    "cache_gio": 6,
    "timeout_giay": 300,
    "duong": "tat",         # tat | openai
    "_ghi_chu": "Chi bat openai sau khi dat OPENAI_API_KEY va model_openai ro rang.",
}


def cau_hinh() -> dict:
    c = dict(MAC_DINH)
    if CAU_HINH.exists():
        try:
            c.update(json.loads(CAU_HINH.read_text(encoding="utf-8-sig")))
        except Exception:
            pass
    return c


def _bo_nho() -> dict:
    try:
        return json.loads(BO_NHO.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _luu_bo_nho(d: dict) -> None:
    BO_NHO.parent.mkdir(parents=True, exist_ok=True)
    # giu 200 muc gan nhat
    muc = sorted(d.items(), key=lambda kv: kv[1].get("luc", 0), reverse=True)[:200]
    BO_NHO.write_text(json.dumps(dict(muc), ensure_ascii=False, indent=1), encoding="utf-8")


# ------------------------------------------------------------------ HAN MUC
def con_duoc_goi(c: dict | None = None) -> tuple[bool, str]:
    """Kiem tran ngay + khoang cach. Tra (duoc, ly_do)."""
    c = c or cau_hinh()
    if c.get("duong") == "tat":
        return False, "da khoa (duong=tat trong config/tri_tue.json)"
    hom_nay = time.strftime("%Y-%m-%d")
    n = SO.mot("SELECT COUNT(*) n FROM chi_so_vh WHERE ten='tri_tue_goi' AND luc LIKE ?",
               hom_nay + "%")["n"]
    if n >= c["tran_moi_ngay"]:
        return False, f"da goi {n} lan hom nay, tran la {c['tran_moi_ngay']}"
    cuoi = SO.mot("SELECT luc FROM chi_so_vh WHERE ten='tri_tue_goi' ORDER BY id DESC LIMIT 1")
    if cuoi:
        try:
            from datetime import datetime
            cach = time.time() - datetime.strptime(cuoi["luc"], "%Y-%m-%d %H:%M:%S").timestamp()
            if cach < c["cach_nhau_giay"]:
                return False, f"moi goi {int(cach)}s truoc, can cach {c['cach_nhau_giay']}s"
        except Exception:
            pass
    return True, "ok"


#: So cua `cc-switch` - noi chu du an da khai san provider va khoa API.
CC_SWITCH_DB = Path.home() / ".cc-switch" / "cc-switch.db"


def tu_cc_switch(ten: str = "deepseek") -> dict:
    """Doc khoa + base_url + model tu `cc-switch` DA CO SAN tren may.

    Vi sao doc TAI CHO chu khong chep sang `config/tri_tue.json`: mot khoa API
    chi nen ton tai o MOT noi. Chep di la tao them mot cho de ro ri, va tao them
    mot ban co the lech khi chu du an doi khoa trong cc-switch.

    Tra {} khi khong co - de goi y KHONG cham vao duong quyet dinh nao.
    """
    if not CC_SWITCH_DB.exists():
        return {}
    import re as _re
    import sqlite3
    try:
        cn = sqlite3.connect(f"file:{CC_SWITCH_DB}?mode=ro", uri=True)
        cn.row_factory = sqlite3.Row
        for r in cn.execute("SELECT name, settings_config FROM providers"):
            if ten.lower() not in str(r["name"] or "").lower():
                continue
            cfg = json.loads(r["settings_config"] or "{}")
            khoa = (cfg.get("auth") or {}).get("OPENAI_API_KEY") or ""
            tho = str(cfg.get("config") or "")
            m_url = _re.search(r'base_url\s*=\s*"([^"]+)"', tho)
            m_model = _re.search(r'^model\s*=\s*"([^"]+)"', tho, _re.M)
            m_wire = _re.search(r'wire_api\s*=\s*"([^"]+)"', tho)
            if not khoa:
                continue
            return {"khoa": khoa,
                    "base_url": (m_url.group(1) if m_url else "").rstrip("/"),
                    "model": m_model.group(1) if m_model else "",
                    "wire_api": m_wire.group(1) if m_wire else "chat",
                    "ten": r["name"]}
    except Exception:
        return {}
    finally:
        try:
            cn.close()
        except Exception:
            pass
    return {}


def _co_openai() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY") or tu_cc_switch().get("khoa"))


def _goi_openai(nhac: str, he_thong: str, c: dict, ep_json: bool = False) -> dict:
    """Goi bat ky API tuong thich OpenAI (`/chat/completions`) - giup may nay
    khong le thuoc mot he LLM duy nhat (Claude).

    HAI THAM SO THEM 04/09/2026, sau khi do lai duong boc:

    - `temperature`. Truoc do KHONG dat, nen deepseek-chat chay o mac dinh
      **1.0** - muc lay mau cho hoi thoai - trong khi viec o day la TRICH XUAT
      co cau truc. Do la nguon rat co kha nang cua lop loi dinh dang ma
      `boc_llm.chuan_hoa_spec` dang phai di va (`giu` tra ve so thuc, chuoi,
      hoac null; 2/4 khai bao bi loai chi vi kieu). Trich xuat thi lay 0.

    - `response_format={"type":"json_object"}` (JSON mode). Truoc do JSON chi
      duoc XIN BANG LOI trong prompt roi `hoi_json` tu cat chuoi tim dau `{`.
      Xin bang loi thi mo hinh duoc phep khong nghe.

    Ca hai chi bat khi nguoi goi noi ro `ep_json`, va co duong tat qua config
    (`temperature`, `json_mode`) vi khong phai API tuong thich-OpenAI nao cung
    nhan `response_format`.
    """
    import requests
    # Uu tien bien moi truong; khong co thi lay tu `cc-switch` da khai san tren
    # may. Chu du an noi ro: "co san deepseek trong may, trong cc switch co cau
    # hinh". Doc tai cho, khong chep khoa sang file nao cua du an.
    cc = tu_cc_switch(c.get("cc_switch_provider", "deepseek"))
    key = os.environ.get("OPENAI_API_KEY") or cc.get("khoa") or ""
    base = (os.environ.get("OPENAI_BASE_URL") or c.get("openai_base_url")
            or cc.get("base_url") or "https://api.openai.com/v1").rstrip("/")
    model = c.get("model_openai") or cc.get("model") or ""
    if not key:
        return {"loi": "thieu OPENAI_API_KEY (va cc-switch khong co provider nao)"}
    if not model:
        return {"loi": "thieu model_openai trong config/tri_tue.json"}
    msgs = []
    if he_thong:
        msgs.append({"role": "system", "content": he_thong})
    msgs.append({"role": "user", "content": nhac})
    than = {"model": model, "messages": msgs,
            "max_tokens": int(c["max_tokens"])}
    nd = c.get("temperature")
    if nd is not None:
        than["temperature"] = float(nd)
    if ep_json and c.get("json_mode", True):
        than["response_format"] = {"type": "json_object"}
    r = requests.post(
        base + "/chat/completions",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        json=than, timeout=int(c["timeout_giay"]))
    if r.status_code != 200:
        return {"loi": "HTTP %d: %s" % (r.status_code, r.text[:300])}
    jp = r.json()
    van_ban = ((jp.get("choices") or [{}])[0].get("message") or {}).get("content", "")
    return {"van_ban": _sua_mojibake((van_ban or "").strip()), "duong": "openai",
            "model": jp.get("model") or model}


def _co_anthropic() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _goi_anthropic(nhac: str, he_thong: str, c: dict) -> dict:
    """Goi API Anthropic (Claude).

    Vi sao can duong RIENG: Claude khong tuong thich `/chat/completions`. No
    dung `/v1/messages`, doi header `x-api-key` + `anthropic-version`, va dat
    cau he thong o truong `system` RIENG chu khong phai mot phan tu trong
    `messages`. Nen `_goi_openai` khong dung duoc du chi doi `base_url`.

    (DeepSeek thi NGUOC LAI: no tuong thich OpenAI, nen chay duoc ngay bang
    `OPENAI_BASE_URL=https://api.deepseek.com` va `model_openai=deepseek-chat`,
    khong can them dong nao.)
    """
    import requests
    key = os.environ.get("ANTHROPIC_API_KEY") or ""
    if not key:
        return {"loi": "thieu ANTHROPIC_API_KEY"}
    model = c.get("model_anthropic")
    if not model:
        return {"loi": "thieu model_anthropic trong config/tri_tue.json"}
    base = (os.environ.get("ANTHROPIC_BASE_URL")
            or c.get("anthropic_base_url") or "https://api.anthropic.com").rstrip("/")
    than = {"model": model, "max_tokens": int(c["max_tokens"]),
            "messages": [{"role": "user", "content": nhac}]}
    if he_thong:
        than["system"] = he_thong
    r = requests.post(
        base + "/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json=than, timeout=int(c["timeout_giay"]))
    if r.status_code != 200:
        return {"loi": "HTTP %d: %s" % (r.status_code, r.text[:300])}
    jp = r.json()
    # `content` la mot DANH SACH khoi; khoi van ban co `type == "text"`.
    van_ban = "".join(x.get("text", "") for x in (jp.get("content") or [])
                      if x.get("type") == "text")
    return {"van_ban": _sua_mojibake(van_ban.strip()), "duong": "anthropic",
            "model": jp.get("model") or model}


def _sua_mojibake(t: str) -> str:
    """Sua chu bi giai ma hai lan (`â€”` thay vi `—`).

    Duong CLI tra ra byte UTF-8 nhung qua mot chang bi doc bang cp1252 roi ma
    hoa lai. Khong phai chuyen tham my: chuoi nay chinh la `co_che` - CAU ma
    nguoi doc o man hinh duyet. Mot cau ro ri ky tu rac lam nguoi doc mat long
    tin vao ca ban ghi, va so cai la thu chi-them nen chua vao roi la nam do.
    """
    if "â€" not in t and "Ã" not in t:
        return t
    try:
        sua = t.encode("cp1252", errors="strict").decode("utf-8", errors="strict")
        return sua if sua.count("�") == 0 else t
    except Exception:
        return t


# ------------------------------------------------------------------- CUA RA
def hoi(nhac: str, he_thong: str = "", bo_qua_han_muc: bool = False,
        dung_cache: bool = True, ep_json: bool = False) -> dict:
    """Hoi LLM mot cau. Tra dict co `van_ban` hoac `loi`/`bo_qua`."""
    c = cau_hinh()
    khoa = hashlib.sha1(
        (c.get("model_openai", "") + str(ep_json) + he_thong + nhac).encode("utf-8", "replace")
    ).hexdigest()

    if dung_cache:
        bn = _bo_nho()
        cu = bn.get(khoa)
        if cu and (time.time() - cu.get("luc", 0)) < c["cache_gio"] * 3600:
            return {**cu["ket_qua"], "tu_cache": True}

    if not bo_qua_han_muc:
        duoc, ly_do = con_duoc_goi(c)
        if not duoc:
            return {"bo_qua": ly_do}

    t0 = time.time()
    duong = c.get("duong", "tat")
    if duong == "anthropic":
        try:
            kq = _goi_anthropic(nhac, he_thong, c)
        except Exception as e:
            kq = {"loi": f"{type(e).__name__}: {str(e)[:160]}"}
    elif duong == "openai":
        try:
            kq = _goi_openai(nhac, he_thong, c, ep_json=ep_json)
        except Exception as e:
            kq = {"loi": "OPENAI: %s: %s" % (type(e).__name__, str(e)[:150])}
    else:
        return {"bo_qua": "cau noi AI ngoai dang tat"}
    kq["giay"] = round(time.time() - t0, 1)

    SO.ghi_chi_so("tri_tue_goi", 1, {"duong": kq.get("duong"), "giay": kq["giay"],
                                     "loi": kq.get("loi")})
    SO.ghi_su_kien("TRI_TUE", "goi", {"duong": kq.get("duong"), "model": kq.get("model"),
                                      "giay": kq["giay"], "co_loi": bool(kq.get("loi"))})
    if dung_cache and kq.get("van_ban"):
        bn = _bo_nho()
        bn[khoa] = {"luc": time.time(), "ket_qua": kq}
        _luu_bo_nho(bn)
    return kq


def hoi_json(nhac: str, he_thong: str = "", **kw) -> dict:
    """Nhu `hoi` nhung ep dau ra la JSON va tu phan tich.

    Khong dung `output_config.format` vi duong CLI khong co no - de hai duong
    cho cung mot hinh dang, ta yeu cau JSON bang loi va boc tach phong thu.
    """
    kq = hoi(nhac + "\n\nTra loi CHI bang mot khoi JSON hop le, khong kem giai thich "
                    "ngoai JSON, khong kem dau ```.", he_thong, **kw)
    if not kq.get("van_ban"):
        return kq
    t = kq["van_ban"].strip()
    if t.startswith("```"):
        t = t.split("```")[1]
        t = t[4:] if t.lower().startswith("json") else t
    i, j = t.find("{"), t.rfind("}")
    if i >= 0 and j > i:
        try:
            kq["json"] = json.loads(t[i:j + 1])
        except Exception as e:
            kq["loi_phan_tich"] = str(e)[:120]
    return kq


def trang_thai() -> dict:
    c = cau_hinh()
    duoc, ly_do = con_duoc_goi(c)
    hom_nay = time.strftime("%Y-%m-%d")
    return {
        "duong_se_dung": (c.get("duong")
                          if c.get("duong") in ("openai", "anthropic") else "tat"),
        "co_openai_api": _co_openai(),
        "co_anthropic_api": _co_anthropic(),
        "model": c.get("model_openai") or None,
        "da_goi_hom_nay": SO.mot("SELECT COUNT(*) n FROM chi_so_vh WHERE ten='tri_tue_goi' "
                                 "AND luc LIKE ?", hom_nay + "%")["n"],
        "tran_moi_ngay": c["tran_moi_ngay"],
        "con_duoc_goi": duoc, "ly_do": ly_do,
    }


if __name__ == "__main__":
    SO.khoi_tao()
    print(json.dumps(trang_thai(), ensure_ascii=False, indent=1))
    if "--thu" in sys.argv:
        r = hoi("Tra loi dung mot tu: OK", bo_qua_han_muc=True, dung_cache=False)
        print(json.dumps(r, ensure_ascii=False, indent=1))
