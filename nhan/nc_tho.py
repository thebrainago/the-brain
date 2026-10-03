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

Model + duong goi (thu nha c91d, 03/10/2026) - khoa chi o MOT noi, KHONG bao gio trong repo / thu / log:
  MAC DINH = AI Box (api.ai-box.vn/v1, chuan OpenAI): `ds/deepseek-flash` (nhanh, it token); DU PHONG `qwen3.8-max-0902` (suy luan sau,
  cham ~5 lan). Ten model + URL o `config/qwen.json` (cung cau hinh voi `q`). Khoa: bien moi truong `AIBOX_API_KEY` (may nha: bien User;
  cloud: cai dat moi truong) hoac cc-switch provider `aibox` (`THO_PROVIDER` doi ten provider - khi do dat them THO_MO_HINH).
  Doi tuyen (cloud, nha cung cap khac): `THO_KHOA_ENV` (TEN bien chua khoa, vd DEEPSEEK_API_KEY) + `THO_BASE_URL` (mac dinh
  https://api.deepseek.com) + `THO_MO_HINH` (mac dinh deepseek-chat) + `THO_MO_HINH_DU_PHONG` (tuy chon).
  `THO_MO_HINH` doi model chinh o ca hai duong. Gia (USD / 1 trieu token): THO_GIA_VAO / THO_GIA_RA, va THO_GIA_VAO_DU_PHONG /
  THO_GIA_RA_DU_PHONG cho model du phong (khong khai thi ghi 0 / dung gia chinh). Tran token moi luot: THO_MAX_TOKENS (mac dinh 12000:
  mo hinh suy luan an token suy luan TRONG max_tokens, tran thap = tra rong, doc y het "mo hinh kem").

Leo thang: sai 2 lan LIEN TIEP (`leo_thang_sau_lan_sai` trong config) -> doi sang model du phong DUNG MOT LAN. "Sai" = loi goi (HTTP /
het gio / JSON hong), tra rong (khong chu, khong cong cu), hay MOI cong cu trong mot luot deu bi tu choi. Lich su hoi thoai giu nguyen.
Da doi roi ma goi van hong 2 lan -> dong vong (trang_thai LOI) + nem loi, khong im lang. `--sau` = viec can suy luan sau: BAT DAU bang
model du phong. Moi lan doi ghi vao `leo_thang` cua ket qua, bao cao `reports/nc_tho/vong_*.md` va cot `mo_hinh` cua vong ("a>b").

    b nc tho [--vong N] [--cong-cu N] [--sau]     N vong kham pha, moi vong toi da N lan goi cong cu
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
#: tran max_tokens: mo hinh suy luan an token suy luan TRONG tran nay - de thap thi tra rong (thu c91d)
TRAN_TOKEN_VONG = 12000
TRAN_TOKEN_TOM_TAT = 6000

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


def _lan_sai_de_leo() -> int:
    try:
        from qwen import cau_hinh as CH
        return max(1, int(CH.nap().get("leo_thang_sau_lan_sai") or 2))
    except Exception:                                       # noqa: BLE001
        return 2


def _duong_aibox() -> dict | None:
    """AI Box (mac dinh): khoa tu AIBOX_API_KEY hoac cc-switch, URL + model o config/qwen.json. None neu khong co khoa."""
    try:
        from qwen import cau_hinh as CH, mo_hinh as QM
        c = CH.nap()
        if os.environ.get("THO_PROVIDER"):
            c = dict(c, cc_switch_provider=os.environ["THO_PROVIDER"])
        d = QM.duong(c)
    except (Exception, SystemExit):                         # noqa: BLE001 - SystemExit: `duong` bao thieu khoa bang SystemExit
        return None
    if not (d.get("khoa") and d.get("base_url")):
        return None
    mo_hinh = os.environ.get("THO_MO_HINH") or d["model"]
    du_phong = str(c.get("model_du_phong") or "")
    return {"url": d["base_url"].rstrip("/") + "/chat/completions", "khoa": d["khoa"], "mo_hinh": mo_hinh,
            "du_phong": "" if du_phong == mo_hinh else du_phong, "nguon": d["nguon"]}


def duong(sau: bool = False) -> dict:
    """-> {url, khoa, mo_hinh, du_phong, nguon}. Uu tien: THO_KHOA_ENV (cloud tu khai) -> AI Box (AIBOX_API_KEY, roi cc-switch).
    `sau=True`: dao mo hinh / du_phong (bat dau bang model du phong - viec can suy luan sau)."""
    ten_env = os.environ.get("THO_KHOA_ENV", "")
    if ten_env and os.environ.get(ten_env):
        base = os.environ.get("THO_BASE_URL", "https://api.deepseek.com")
        d = {"url": base.rstrip("/") + "/chat/completions", "khoa": os.environ[ten_env],
             "mo_hinh": os.environ.get("THO_MO_HINH", "deepseek-chat"),
             "du_phong": os.environ.get("THO_MO_HINH_DU_PHONG", ""), "nguon": "env:" + ten_env}
    else:
        d = _duong_aibox()
        if d is None:
            raise RuntimeError("chua co duong model re: dat bien moi truong AIBOX_API_KEY hoac them provider 'aibox' vao cc-switch "
                               "(may nha); hoac THO_KHOA_ENV + khoa trong cai dat moi truong (cloud, tu chon URL + model)")
    if sau and d["du_phong"]:
        d = dict(d, mo_hinh=d["du_phong"], du_phong=d["mo_hinh"])
    return d


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
    """Mot loi goi KHONG cong cu (tom tat, nen log). Dung o cau noi: `qwen/cau_git.py` tom tat ket qua don.
    Loi / tra rong -> thu lai; sai du `leo_thang_sau_lan_sai` lan thi doi sang model du phong; van sai het -> RuntimeError."""
    d = duong()
    ke = [d["mo_hinh"]] * _lan_sai_de_leo() + ([d["du_phong"]] if d.get("du_phong") else [])
    loi = []
    for m in ke:
        try:
            r = _post(d, {"model": m, "max_tokens": max(max_tokens, TRAN_TOKEN_TOM_TAT), "temperature": 0.1,
                          "messages": [{"role": "user", "content": nhac}]})
            tl = (r["choices"][0]["message"].get("content") or "").strip()
            if tl:
                return tl
            loi.append("%s: tra rong" % m)
        except Exception as e:                              # noqa: BLE001
            loi.append("%s: %s" % (m, str(e)[:120]))
    raise RuntimeError("model re sai het: " + " | ".join(loi))


def cong_cu_openai() -> list[dict]:
    return [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                              "parameters": t["input_schema"]}}
            for t in CC.schema_api() if t["name"] in CONG_CU_THO]


def _ep(ten: str, dv: dict) -> dict:
    dv = dict(dv or {})
    if ten in EP_KHAM_PHA:
        dv["doan"] = "kham_pha"
    return dv


def _gia(ten: str) -> float:
    return float(os.environ.get(ten, 0) or 0)


def chay_vong(nhiem_vu: str = "", so_cong_cu: int = 30, max_tokens: int | None = None, goi=None, sau: bool = False) -> dict:
    """MOT vong kham pha cua tho. `goi(than) -> phan hoi chuan OpenAI` de test khong can mang.

    Leo thang (docstring dau file): sai `leo_thang_sau_lan_sai` lan lien tiep -> doi model DUNG MOT LAN; da doi ma van hong -> dong vong
    (LOI) + nem RuntimeError. `sau=True` bat dau bang model du phong."""
    from nhan import nc_tac_tu as TT
    max_tokens = int(max_tokens or os.environ.get("THO_MAX_TOKENS") or TRAN_TOKEN_VONG)
    d = {"mo_hinh": "gia_lap", "nguon": "test", "du_phong": "gia_lap_du_phong"} if goi else duong()
    ten_du_phong = d.get("du_phong") or ""
    if sau and ten_du_phong:
        d = dict(d, mo_hinh=ten_du_phong, du_phong=d["mo_hinh"])
    goi = goi or (lambda than: _post(d, than))
    mo_hinh_dau = d["mo_hinh"]
    vong_id = ST.bat_dau_vong("tho", mo_hinh_dau)
    gt0 = int(ST.mot("SELECT COALESCE(MAX(id),0) n FROM gia_thuyet").get("n") or 0)
    ch0 = int(ST.mot("SELECT COALESCE(MAX(id),0) n FROM cau_hoi").get("n") or 0)
    tools = cong_cu_openai()
    msgs = [{"role": "system", "content": VAI_THO + TT.HIEN_CHUONG},
            {"role": "user", "content": "HO SO NGHIEN CUU HIEN TAI:\n\n" + ST.tom_tat_md()
             + "\n\n" + (nhiem_vu or "Chon viec kham pha co gia tri nhat va lam.")}]
    n_cc, cuoi = 0, ""
    tok = {}                                # model -> [vao, ra]: de tinh USD theo gia tung model
    sai_cho, sai, lan_goi, leo = _lan_sai_de_leo(), 0, 0, []

    def doi_model(ly_do: str) -> bool:
        nonlocal d, sai
        if leo or not d.get("du_phong"):
            return False
        leo.append({"tu": d["mo_hinh"], "sang": d["du_phong"], "sau_cong_cu": n_cc, "ly_do": ly_do[:160]})
        d, sai = dict(d, mo_hinh=d["du_phong"], du_phong=""), 0
        return True

    def danh_dau_nguon():                   # moi thu tho ghi mang nguon 'tho' - Claude loc duoc
        with ST.ket_noi() as cn:
            cn.execute("UPDATE gia_thuyet SET nguon='tho' WHERE id>?", (gt0,))
            cn.execute("UPDATE cau_hoi SET nguon='tho' WHERE id>? AND nguon!='nguoi'", (ch0,))

    while lan_goi < so_cong_cu + 2:
        het = n_cc >= so_cong_cu
        than = {"model": d["mo_hinh"], "messages": msgs, "max_tokens": max_tokens, "temperature": 0.3}
        if not het:
            than.update(tools=tools, tool_choice="auto")
        ly_do, r, m = "", None, {}
        try:
            r = goi(than)
            m = r["choices"][0]["message"]
        except Exception as e:                              # noqa: BLE001 - loi goi la mot lan SAI, khong phai mot cai chet
            ly_do = "%s: %s" % (type(e).__name__, str(e)[:160])
        u = (r.get("usage") if isinstance(r, dict) else None) or {}
        t = tok.setdefault(than["model"], [0, 0])
        t[0] += int(u.get("prompt_tokens") or 0)
        t[1] += int(u.get("completion_tokens") or 0)
        calls = [] if het else (m.get("tool_calls") or [])
        if not ly_do and not calls and not (m.get("content") or "").strip():
            ly_do = "tra rong (finish=%s)" % (r["choices"][0].get("finish_reason") or "?")
        if ly_do:
            sai += 1
            if sai >= sai_cho and not doi_model(ly_do):
                danh_dau_nguon()
                ST.ket_thuc_vong(vong_id, tom_tat="!! DUNG: %d lan goi sai lien tiep (%s): %s" % (sai, d["mo_hinh"], ly_do),
                                 so_cong_cu=n_cc, token_vao=sum(v[0] for v in tok.values()),
                                 token_ra=sum(v[1] for v in tok.values()), trang_thai="LOI")
                raise RuntimeError("tho: %d lan goi sai lien tiep%s - %s" % (
                    sai, " (da doi sang %s)" % d["mo_hinh"] if leo else "", ly_do))
            continue
        lan_goi += 1
        tin = {"role": "assistant", "content": m.get("content") or ""}
        if calls:
            tin["tool_calls"] = calls
        msgs.append(tin)
        if not calls:
            cuoi = m.get("content") or ""
            break
        n_loi = 0
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
            n_loi += isinstance(out, dict) and bool(out.get("loi"))
            msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": CC._gon(out, 6000)})
        if n_loi == len(calls):                 # MOI cong cu bi tu choi = mot lan sai (mo hinh khong theo duoc schema)
            sai += 1
            if sai >= sai_cho:
                doi_model("moi cong cu bi tu choi %d luot lien tiep" % sai)
        else:
            sai = 0
        if n_cc >= so_cong_cu:
            msgs.append({"role": "user", "content": "Het ngan sach cong cu. Ghi lai ket luan 5-8 dong."})
    mo_hinh_cuoi = d["mo_hinh"]
    danh_dau_nguon()
    if leo:
        with ST.ket_noi() as cn:
            cn.execute("UPDATE vong SET mo_hinh=? WHERE id=?", ("%s>%s" % (mo_hinh_dau, mo_hinh_cuoi), vong_id))
    gv, gr = _gia("THO_GIA_VAO"), _gia("THO_GIA_RA")
    gv2, gr2 = _gia("THO_GIA_VAO_DU_PHONG") or gv, _gia("THO_GIA_RA_DU_PHONG") or gr
    usd = sum((tv * (gv2 if mo == ten_du_phong else gv) + tr * (gr2 if mo == ten_du_phong else gr)) / 1e6
              for mo, (tv, tr) in tok.items())
    tok_vao, tok_ra = sum(v[0] for v in tok.values()), sum(v[1] for v in tok.values())
    ST.ket_thuc_vong(vong_id, tom_tat=cuoi[:2000], so_cong_cu=n_cc, token_vao=tok_vao, token_ra=tok_ra, usd=usd)
    f = LAB / "reports" / "nc_tho" / ("vong_%05d.md" % vong_id)
    f.parent.mkdir(parents=True, exist_ok=True)
    dong_leo = "".join("DOI MODEL sau %d lan goi cong cu: %s -> %s (%s)\n\n" % (x["sau_cong_cu"], x["tu"], x["sang"], x["ly_do"])
                       for x in leo)
    f.write_text("# THO vong %d (%s, %s)\n\n%d lan goi cong cu · %d token vao · %d token ra · %.4f USD\n\n%s%s\n"
                 % (vong_id, mo_hinh_dau, d["nguon"], n_cc, tok_vao, tok_ra, usd, dong_leo, cuoi), encoding="utf-8")
    return {"vong_id": vong_id, "mo_hinh": mo_hinh_dau, "mo_hinh_cuoi": mo_hinh_cuoi, "leo_thang": leo, "so_cong_cu": n_cc,
            "token_vao": tok_vao, "token_ra": tok_ra, "usd": round(usd, 4), "ket_luan": cuoi, "bao_cao": str(f.relative_to(LAB))}


def main(argv: list[str]) -> int:
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    so_vong = int(argv[argv.index("--vong") + 1]) if "--vong" in argv else 1
    so_cc = int(argv[argv.index("--cong-cu") + 1]) if "--cong-cu" in argv else 30
    for _ in range(max(1, so_vong)):
        r = chay_vong(so_cong_cu=so_cc, sau="--sau" in argv)
        print(json.dumps({k: v for k, v in r.items() if k != "ket_luan"}, ensure_ascii=False))
        print(r["ket_luan"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
