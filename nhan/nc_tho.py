# -*- coding: utf-8 -*-
"""nc_tho.py - THO: model GIA RE (DeepSeek, qwen... chuan OpenAI) lam phan LAO DONG kham pha.

Phan viec (chu du an duyet 29/09/2026 - "phan ro viec ... goi duoc model gia re de uu chi phi"):

    tho (file nay)   KHAM PHA tren doan kham_pha: ho so, tim quy luat, thu co che, quet, mo xe lenh,
                     luoi; GHI so tay (gia thuyet / cau hoi mang nguon 'tho') cho nha nghien cuu doc
    Claude           doc so tay, quyet XAC NHAN va NIEM PHONG, xuat MQL5

Tho KHONG co `xac_nhan`, `niem_phong`, `xuat_mq5`: moi lan nhin doan xac nhan deu bi dem, niem phong
chi mo mot lan - tieu hai doan do la viec khong lui duoc, de cho mo hinh manh (hoac chu du an).
Ly do co so: lab tung do LLM re dien `co_che` cho 48 khai bao, tham dinh bac 41. Tho van TIEU phep
thu tren kham pha (dem theo dong gia thuyet) - so tay ghi dung, Sharpe giam phat tinh dung.

Duong goi - khoa chi o MOT noi:
  1. May nha: cc-switch (`qwen.mo_hinh.tu_cc_switch`), provider chua chuoi `THO_PROVIDER`
     (mac dinh "deepseek"). Khoa khong roi may.
  2. Phien cloud: bien `THO_KHOA_ENV` (ten bien chua khoa, vd DEEPSEEK_API_KEY) trong cai dat moi
     truong + `THO_BASE_URL` (mac dinh https://api.deepseek.com) + `THO_MO_HINH` (mac dinh
     deepseek-chat). Gia (USD / 1 trieu token) khai qua THO_GIA_VAO / THO_GIA_RA - khong khai thi ghi 0.

    b nc tho [--vong N] [--cong-cu N]     N vong kham pha, moi vong toi da N lan goi cong cu
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nhan import nc_cong_cu as CC, nc_so_tay as ST

LAB = Path(__file__).resolve().parent.parent
CONG_CU_THO = ("xem_so_tay", "danh_sach_du_lieu", "ho_so_tai_san", "tim_quy_luat", "thu_co_che",
               "quet_tham_so", "mo_xe_lenh", "thu_luoi", "ghep_danh_muc", "ghi_gia_thuyet",
               "ghi_hieu_biet", "ghi_cau_hoi")
#: cong cu co tham so `doan` -> ep ve kham_pha (tho khong duoc nhin doan xac nhan)
EP_KHAM_PHA = ("thu_luoi", "ghep_danh_muc")

VAI_THO = """VAI CUA BAN O LUOT NAY: THO KHAM PHA (khong phai nha nghien cuu chinh).
- Ban chi co cac cong cu duoc cap trong luot nay, tat ca chay tren doan KHAM PHA. Moi dong trong hien
  chuong duoi day noi ve xac_nhan / niem_phong / xuat_mq5 la viec cua NHA NGHIEN CUU CHINH (Claude) -
  ban khong co va khong duoc de nghi goi chung.
- Muc tieu: tim 1-3 huong CO TRIEN VONG that (co lai sau phi, nhieu lenh, cao nguyen khi quet, qua null)
  roi GHI LAI cho Claude: ghi_gia_thuyet (phat bieu + vi sao + tn_id bang chung trong vi_sao), ghi_cau_hoi
  cho viec tiep. Huong da bac bo cung ghi (ghi_hieu_biet) de khong ai thu lai.
- Moi lan goi cong cu la mot phep thu bi dem. Thu CO CHU DICH, khong quet cho co.
- Ket thuc bang 5-8 dong: da thu gi (kem so), gia thuyet nao dang giao cho Claude, vi sao.

"""


def duong() -> dict:
    """-> {url, khoa, mo_hinh, nguon}. Uu tien bien moi truong (cloud), roi cc-switch (may nha)."""
    ten_env = os.environ.get("THO_KHOA_ENV", "")
    if ten_env and os.environ.get(ten_env):
        base = os.environ.get("THO_BASE_URL", "https://api.deepseek.com")
        return {"url": base.rstrip("/") + "/chat/completions", "khoa": os.environ[ten_env],
                "mo_hinh": os.environ.get("THO_MO_HINH", "deepseek-chat"), "nguon": "env:" + ten_env}
    try:
        from qwen import mo_hinh as QM
        cc = QM.tu_cc_switch(os.environ.get("THO_PROVIDER", "deepseek"))
    except Exception:
        cc = {}
    if cc.get("khoa") and cc.get("base_url"):
        return {"url": cc["base_url"].rstrip("/") + "/chat/completions", "khoa": cc["khoa"],
                "mo_hinh": os.environ.get("THO_MO_HINH") or cc.get("model") or "deepseek-chat",
                "nguon": "cc-switch:" + str(cc.get("ten", ""))}
    raise RuntimeError("chua co duong model re: them provider DeepSeek vao cc-switch (may nha) "
                       "hoac dat THO_KHOA_ENV + khoa trong cai dat moi truong (cloud)")


def _post(d: dict, than: dict, timeout: int = 180) -> dict:
    req = urllib.request.Request(d["url"], data=json.dumps(than).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + d["khoa"]})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or i == 3:
                raise RuntimeError("model re HTTP %s: %s" % (e.code, e.read()[:300]))
        except (urllib.error.URLError, TimeoutError) as e:
            if i == 3:
                raise RuntimeError("model re khong goi duoc: %s" % e)
        time.sleep(2 ** (i + 1))
    raise RuntimeError("model re khong tra loi")


def goi_re(nhac: str, max_tokens: int = 800) -> str:
    """Mot loi goi KHONG cong cu (tom tat, nen log). Dung o cau noi: `qwen/cau_git.py` tom tat ket qua don."""
    d = duong()
    r = _post(d, {"model": d["mo_hinh"], "max_tokens": max_tokens, "temperature": 0.1,
                  "messages": [{"role": "user", "content": nhac}]})
    return (r["choices"][0]["message"].get("content") or "").strip()


def cong_cu_openai() -> list[dict]:
    return [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                              "parameters": t["input_schema"]}}
            for t in CC.schema_api() if t["name"] in CONG_CU_THO]


def _ep(ten: str, dv: dict) -> dict:
    dv = dict(dv or {})
    if ten in EP_KHAM_PHA:
        dv["doan"] = "kham_pha"
    return dv


def chay_vong(nhiem_vu: str = "", so_cong_cu: int = 30, max_tokens: int = 4000, goi=None) -> dict:
    """MOT vong kham pha cua tho. `goi(than) -> phan hoi chuan OpenAI` de test khong can mang."""
    from nhan import nc_tac_tu as TT
    d = {"mo_hinh": "gia_lap", "nguon": "test"} if goi else duong()
    goi = goi or (lambda than: _post(d, than))
    vong_id = ST.bat_dau_vong("tho", d["mo_hinh"])
    gt0 = int(ST.mot("SELECT COALESCE(MAX(id),0) n FROM gia_thuyet").get("n") or 0)
    ch0 = int(ST.mot("SELECT COALESCE(MAX(id),0) n FROM cau_hoi").get("n") or 0)
    tools = cong_cu_openai()
    msgs = [{"role": "system", "content": VAI_THO + TT.HIEN_CHUONG},
            {"role": "user", "content": "HO SO NGHIEN CUU HIEN TAI:\n\n" + ST.tom_tat_md()
             + "\n\n" + (nhiem_vu or "Chon viec kham pha co gia tri nhat va lam.")}]
    n_cc, tok_vao, tok_ra, cuoi = 0, 0, 0, ""
    for _ in range(so_cong_cu + 2):
        het = n_cc >= so_cong_cu
        than = {"model": d["mo_hinh"], "messages": msgs, "max_tokens": max_tokens, "temperature": 0.3}
        if not het:
            than.update(tools=tools, tool_choice="auto")
        r = goi(than)
        u = r.get("usage") or {}
        tok_vao += int(u.get("prompt_tokens") or 0)
        tok_ra += int(u.get("completion_tokens") or 0)
        m = r["choices"][0]["message"]
        calls = [] if het else (m.get("tool_calls") or [])
        tin = {"role": "assistant", "content": m.get("content") or ""}
        if calls:
            tin["tool_calls"] = calls
        msgs.append(tin)
        if not calls:
            cuoi = m.get("content") or ""
            break
        for tc in calls:
            ten = tc["function"]["name"]
            try:
                dv = json.loads(tc["function"].get("arguments") or "{}")
            except Exception:
                dv = None
            if ten not in CONG_CU_THO:
                out = {"loi": "tho khong co cong cu '%s' - viec cua nha nghien cuu chinh" % ten}
            elif not isinstance(dv, dict):
                out = {"loi": "arguments khong phai JSON object"}
            else:
                out = CC.goi(ten, _ep(ten, dv), vong_id)
            n_cc += 1
            msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": CC._gon(out, 6000)})
        if n_cc >= so_cong_cu:
            msgs.append({"role": "user", "content": "Het ngan sach cong cu. Ghi lai ket luan 5-8 dong."})
    with ST.ket_noi() as cn:        # moi thu tho ghi mang nguon 'tho' - Claude loc duoc
        cn.execute("UPDATE gia_thuyet SET nguon='tho' WHERE id>?", (gt0,))
        cn.execute("UPDATE cau_hoi SET nguon='tho' WHERE id>? AND nguon!='nguoi'", (ch0,))
    gia_vao = float(os.environ.get("THO_GIA_VAO", 0) or 0)
    gia_ra = float(os.environ.get("THO_GIA_RA", 0) or 0)
    usd = (tok_vao * gia_vao + tok_ra * gia_ra) / 1e6
    ST.ket_thuc_vong(vong_id, tom_tat=cuoi[:2000], so_cong_cu=n_cc, token_vao=tok_vao,
                     token_ra=tok_ra, usd=usd)
    f = LAB / "reports" / "nc_tho" / ("vong_%05d.md" % vong_id)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("# THO vong %d (%s, %s)\n\n%d lan goi cong cu · %d token vao · %d token ra · %.4f USD\n\n%s\n"
                 % (vong_id, d["mo_hinh"], d["nguon"], n_cc, tok_vao, tok_ra, usd, cuoi),
                 encoding="utf-8")
    return {"vong_id": vong_id, "mo_hinh": d["mo_hinh"], "so_cong_cu": n_cc, "token_vao": tok_vao,
            "token_ra": tok_ra, "usd": round(usd, 4), "ket_luan": cuoi,
            "bao_cao": str(f.relative_to(LAB))}


def main(argv: list[str]) -> int:
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    so_vong = int(argv[argv.index("--vong") + 1]) if "--vong" in argv else 1
    so_cc = int(argv[argv.index("--cong-cu") + 1]) if "--cong-cu" in argv else 30
    for _ in range(max(1, so_vong)):
        r = chay_vong(so_cong_cu=so_cc)
        print(json.dumps({k: v for k, v in r.items() if k != "ket_luan"}, ensure_ascii=False))
        print(r["ket_luan"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
