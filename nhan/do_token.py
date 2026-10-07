# -*- coding: utf-8 -*-
"""do_token.py - DO token that cua mot phien Claude Code tu file transcript (.jsonl) va chi ra khoan nao dang ton.

## Vi sao (02/10/2026)
Chu du an: *"nghien cuu cach toi uu he thong va dung token hieu qua nhat, neu khong se rat ton"*. Do tren phien cloud that
(629 goi API, ngu canh TB 445k token/goi): doc lai cache 64% · ghi cache 20% · dau ra 16,5% (thinking 58% dau ra). Moi goi API
doc lai TOAN BO ngu canh, nen chi phi la **so goi x kich thuoc ngu canh**, khong phai do dai tung tin nhan; token do chinh toi sinh ra
(thinking + lenh) la nhom 'mang theo' lon nhat vi nam trong ngu canh cho toi khi nen. Cong cu nay do lai moi khi can (may nha, cloud).

Don vi chi phi = 1 token dau-vao thuong, theo ty le gia chuan cua Anthropic: doc cache 0,1 · ghi cache 5 phut 1,25 / 1 gio 2 · dau ra 5.
(Ty le, khong phai tien: khong phu thuoc model hay goi cuoc.) Uoc luong token tu ky tu = ky tu / 3,2 (chi dung xep hang, khong dung lam so chinh xac).

    python -m nhan.do_token [file.jsonl] [--json]     (mac dinh: transcript moi nhat cua thu muc hien tai)
    b token [file.jsonl] [--json]
"""
from __future__ import annotations

import bisect
import collections
import datetime as dt
import json
import re
import sys
from pathlib import Path

K_KY_TU = 3.2                 # ky tu / token (uoc luong)
NGUONG_LANH = 0.5             # goi 'lanh' = hon nua ngu canh phai ghi lai cache
NGHI_LANH_GIAY = 3600         # nghi lau hon ngan nay: cache 1 gio het han
GIA_DOC, GIA_RA, GIA_GHI_5P, GIA_GHI_1H = 0.1, 5.0, 1.25, 2.0
LOAI_KHONG_TINH = {"prompt_snapshot"}      # ban chup de ghi log, khong nam trong ngu canh cua model


def _g(d: dict | None, k: str) -> int:
    try:
        return int((d or {}).get(k) or 0)
    except (TypeError, ValueError):
        return 0


def _ngu_canh(u: dict) -> int:
    return _g(u, "input_tokens") + _g(u, "cache_creation_input_tokens") + _g(u, "cache_read_input_tokens")


def _doc_dong(path: Path) -> list[dict]:
    ra = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if isinstance(d, dict):
                ra.append(d)
    return ra


def _ky_tu_ket_qua(b: dict) -> int:
    c = b.get("content")
    if isinstance(c, list):
        return sum(len(x.get("text", "")) for x in c if isinstance(x, dict))
    return len(str(c or ""))


def _gio(s) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def phan_tich(path: Path | str) -> dict:
    """Phan tich mot transcript. Tra dict (xem khoa o duoi); khong nem khi file thieu truong (thieu thi coi 0)."""
    rows = _doc_dong(Path(path))
    # --- goi API duy nhat (mot goi co the nam tren nhieu dong: moi khoi noi dung mot dong)
    goi: dict = {}
    thu_tu: list = []
    for i, d in enumerate(rows):
        if d.get("type") != "assistant":
            continue
        m = d.get("message") or {}
        u = m.get("usage") or {}
        khoa = d.get("requestId") or m.get("id") or d.get("uuid")
        if khoa not in goi:
            goi[khoa] = {"i": i, "ts": d.get("timestamp"), "u": u}
            thu_tu.append(khoa)
        elif _g(u, "output_tokens") >= _g(goi[khoa]["u"], "output_tokens"):
            goi[khoa]["u"] = u
    n = len(thu_tu)
    kq: dict = {"so_goi": n, "tep": str(path)}
    if not n:
        kq["khuyen_nghi"] = ["Khong thay goi API nao trong file (dung file transcript .jsonl cua Claude Code?)."]
        return kq

    tong = collections.Counter()
    ghi_tuong_duong = 0.0
    for k in thu_tu:
        u = goi[k]["u"]
        ct = u.get("cache_creation") or {}
        g1h, g5p = _g(ct, "ephemeral_1h_input_tokens"), _g(ct, "ephemeral_5m_input_tokens")
        ghi = _g(u, "cache_creation_input_tokens")
        if g1h + g5p == 0:
            g5p = ghi                                  # khong ro TTL: coi 5 phut (that tay)
        tong["vao"] += _g(u, "input_tokens")
        tong["ghi_cache"] += ghi
        tong["doc_cache"] += _g(u, "cache_read_input_tokens")
        tong["ra"] += _g(u, "output_tokens")
        tong["thinking"] += _g(u.get("output_tokens_details"), "thinking_tokens")
        ghi_tuong_duong += g1h * GIA_GHI_1H + g5p * GIA_GHI_5P
    w_ghi = (ghi_tuong_duong / tong["ghi_cache"]) if tong["ghi_cache"] else GIA_GHI_1H
    chi_phi = {"vao": tong["vao"] * 1.0, "ghi_cache": ghi_tuong_duong,
               "doc_cache": tong["doc_cache"] * GIA_DOC, "ra": tong["ra"] * GIA_RA}
    S = sum(chi_phi.values()) or 1.0
    kq["tong_token"] = dict(tong)
    kq["chi_phi"] = {k: round(v) for k, v in chi_phi.items()}
    kq["phan_tram"] = {k: round(100 * v / S, 1) for k, v in chi_phi.items()}
    kq["chi_phi_tong"] = round(S)
    kq["thinking_ty_le_dau_ra"] = round(tong["thinking"] / tong["ra"], 3) if tong["ra"] else 0.0

    ctx = [_ngu_canh(goi[k]["u"]) for k in thu_tu]
    sx = sorted(ctx)
    kq["ngu_canh"] = {"tb": round(sum(ctx) / n), "trung_vi": sx[n // 2], "max": sx[-1]}

    # --- goi 'lanh' + nghi lau
    lanh = [k for k, c in zip(thu_tu, ctx) if c and _g(goi[k]["u"], "cache_creation_input_tokens") / c > NGUONG_LANH]
    cp_lanh = sum(_g(goi[k]["u"], "cache_creation_input_tokens") * w_ghi for k in lanh)
    nghi, truoc = [], None
    for k in thu_tu:
        t = _gio(goi[k]["ts"])
        if truoc and t and (t - truoc).total_seconds() > NGHI_LANH_GIAY:
            nghi.append({"nghi_gio": round((t - truoc).total_seconds() / 3600, 1),
                         "ghi_lai_token": _g(goi[k]["u"], "cache_creation_input_tokens")})
        if t:
            truoc = t
    kq["goi_lanh"] = {"so": len(lanh), "chi_phi": round(cp_lanh), "phan_tram": round(100 * cp_lanh / S, 1)}
    kq["nghi_lau"] = nghi

    # --- cua so nen (compaction)
    ranh = [i for i, d in enumerate(rows) if d.get("type") == "system" and "compact" in str(d.get("subtype") or "")]
    kq["so_lan_nen"] = len(ranh)
    gioi = [0] + ranh + [len(rows) + 1]
    chi_so_goi = [goi[k]["i"] for k in thu_tu]

    # --- ket qua cong cu + tin nguoi dung / nhac nho (kich thuoc theo dong)
    ten_cc = {}
    for d in rows:
        if d.get("type") == "assistant":
            for b in ((d.get("message") or {}).get("content") or []):
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    ten_cc[b.get("id")] = b.get("name")
    ket_qua, tin = [], {}
    for i, d in enumerate(rows):
        t = d.get("type")
        if t == "user":
            c = (d.get("message") or {}).get("content")
            if isinstance(c, str):
                tin[i] = tin.get(i, 0) + len(c)
            elif isinstance(c, list):
                for b in c:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "tool_result":
                        ket_qua.append((i, ten_cc.get(b.get("tool_use_id"), "?"), _ky_tu_ket_qua(b)))
                    elif b.get("type") == "text":
                        tin[i] = tin.get(i, 0) + len(b.get("text", ""))
        elif t == "attachment":
            a = d.get("attachment") or {}
            if a.get("type") not in LOAI_KHONG_TINH:
                tin[i] = tin.get(i, 0) + len(json.dumps(a, ensure_ascii=False))

    def con_lai(i: int) -> int:               # so goi API sau dong i, trong cung cua so nen
        sau = [r for r in ranh if r > i]
        gh = sau[0] if sau else len(rows) + 1
        return max(0, bisect.bisect_left(chi_so_goi, gh) - bisect.bisect_right(chi_so_goi, i))

    mang = collections.Counter()
    theo_cc = collections.defaultdict(lambda: [0, 0, 0.0])
    lon = []
    for w in range(len(gioi) - 1):
        lo, hi = gioi[w], gioi[w + 1]
        ks = [k for k in thu_tu if lo <= goi[k]["i"] < hi]
        for j, k in enumerate(ks):
            mang["dau_ra_cua_ai"] += _g(goi[k]["u"], "output_tokens") * (w_ghi + GIA_DOC * (len(ks) - 1 - j))
    for i, ten, kt in ket_qua:
        c = kt / K_KY_TU * (w_ghi + GIA_DOC * con_lai(i))
        mang["ket_qua_cong_cu"] += c
        e = theo_cc[ten]
        e[0] += 1
        e[1] += kt
        e[2] += c
        lon.append((c, ten, kt, con_lai(i)))
    for i, kt in tin.items():
        mang["tin_nguoi_dung_va_nhac_nho"] += kt / K_KY_TU * (w_ghi + GIA_DOC * con_lai(i))
    M = sum(mang.values()) or 1.0
    kq["mang_theo"] = {k: {"chi_phi": round(v), "phan_tram_cua_mang_theo": round(100 * v / M, 1),
                           "phan_tram_tong": round(100 * v / S, 1)} for k, v in mang.most_common()}
    kq["cong_cu"] = [{"ten": t, "lan": v[0], "ky_tu": v[1], "chi_phi": round(v[2]), "phan_tram_tong": round(100 * v[2] / S, 2)}
                     for t, v in sorted(theo_cc.items(), key=lambda kv: -kv[1][2])[:6]]
    kq["ket_qua_lon"] = [{"ten": t, "ky_tu": kt, "mang_theo_qua_goi": ca, "phan_tram_tong": round(100 * c / S, 2)}
                         for c, t, kt, ca in sorted(lon, reverse=True)[:5]]
    # --- do dai cua so nen (so goi / lan nen)
    do_dai = []
    for w in range(len(gioi) - 1):
        ks = [k for k in thu_tu if gioi[w] <= goi[k]["i"] < gioi[w + 1]]
        if ks:
            do_dai.append({"so_goi": len(ks), "ngu_canh_dau": _ngu_canh(goi[ks[0]]["u"]),
                           "ngu_canh_cuoi": _ngu_canh(goi[ks[-1]]["u"])})
    kq["cua_so"] = do_dai
    kq["khuyen_nghi"] = khuyen_nghi(kq)
    return kq


def khuyen_nghi(d: dict) -> list[str]:
    """Quy tac ro rang tren so do duoc - khong phai y kien. Moi dong co con so lam can cu."""
    ra = []
    tb = d["ngu_canh"]["tb"]
    if tb > 250_000:
        ra.append("Ngu canh TB %dk token/goi (moi goi doc lai CA ngu canh): dat cua so nen ~250k - `/autocompact 250k` (phien dang chay) "
                  "hoac bien moi truong CLAUDE_CODE_AUTO_COMPACT_WINDOW=250000 (moi truong cloud). Mo hinh uoc tinh: giam ~1/3 chi phi." % (tb // 1000))
    sinh = d.get("mang_theo", {}).get("dau_ra_cua_ai", {}).get("phan_tram_tong", 0) + d["phan_tram"].get("ra", 0)
    if d["thinking_ty_le_dau_ra"] > 0.5 and sinh > 30:
        ra.append("Thinking = %d%% dau ra; token AI tu sinh (dau ra + mang theo) ~%d%% chi phi: ha effort (`/effort high|medium`) cho viec co hoc, "
                  "de `max` cho thiet ke kho." % (round(100 * d["thinking_ty_le_dau_ra"]), round(sinh)))
    if d["goi_lanh"]["phan_tram"] >= 5:
        ra.append("%d lan nghi > 1 gio buoc ghi lai ca ngu canh = %s%% chi phi: gom viec thanh dot, cho bang `send_later` MOT lan dung luc "
                  "(khong tham do), truoc khi nghi dai thi nen/chot phien." % (len(d["nghi_lau"]), d["goi_lanh"]["phan_tram"]))
    if d["phan_tram"].get("doc_cache", 0) > 55:
        ra.append("Doc lai ngu canh = %s%% chi phi: giam SO GOI API (gop lenh doc lap vao mot goi / mot script), khong phai rut ngan tung tin nhan."
                  % d["phan_tram"]["doc_cache"])
    top = sum(x["phan_tram_tong"] for x in d.get("ket_qua_lon", []))
    if top >= 3:
        x = d["ket_qua_lon"][0]
        ra.append("5 ket qua cong cu lon nhat mang theo ~%.1f%% chi phi (lon nhat: %s %d ky tu): loc dau ra (head/cut/grep, tom tat) truoc khi doc." % (top, x["ten"], x["ky_tu"]))
    return ra or ["Khong co khoan nao vuot nguong khuyen nghi."]


def tom_tat(d: dict) -> str:
    if not d.get("so_goi"):
        return "\n".join(d.get("khuyen_nghi") or ["(rong)"])
    p, c = d["phan_tram"], d["ngu_canh"]
    t = d["tong_token"]
    dong = ["DO TOKEN: %s" % Path(d["tep"]).name,
            "  %d goi API · %d lan nen · ngu canh TB %dk / trung vi %dk / max %dk" % (d["so_goi"], d["so_lan_nen"], c["tb"] // 1000, c["trung_vi"] // 1000, c["max"] // 1000),
            "  chi phi: doc cache %s%% · ghi cache %s%% · dau ra %s%% (thinking %d%% dau ra) · vao %s%%" % (
                p["doc_cache"], p["ghi_cache"], p["ra"], round(100 * d["thinking_ty_le_dau_ra"]), p["vao"]),
            "  token: doc %s · ghi %s · ra %s" % (f"{t['doc_cache']:,}", f"{t['ghi_cache']:,}", f"{t['ra']:,}"),
            "  goi lanh (ghi lai >50%% ngu canh): %d goi = %s%% chi phi; nghi > 1 gio: %d lan" % (d["goi_lanh"]["so"], d["goi_lanh"]["phan_tram"], len(d["nghi_lau"]))]
    for k, v in d.get("mang_theo", {}).items():
        dong.append("  mang theo - %-28s %5.1f%% tong" % (k, v["phan_tram_tong"]))
    for x in d.get("ket_qua_lon", [])[:3]:
        dong.append("  ket qua lon: %-9s %7d ky tu, mang theo %d goi = %.2f%% tong" % (x["ten"], x["ky_tu"], x["mang_theo_qua_goi"], x["phan_tram_tong"]))
    dong.append("KHUYEN NGHI:")
    dong += ["  - " + s for s in d.get("khuyen_nghi", [])]
    return "\n".join(dong)


def tim_transcript(cwd: Path | None = None, goc: Path | None = None) -> Path | None:
    """Transcript moi nhat cua thu muc `cwd` (`~/.claude/projects/<cwd-bo-ky-tu-la>/*.jsonl`); khong co -> moi nhat bat ky."""
    goc = goc or (Path.home() / ".claude" / "projects")
    if not goc.is_dir():
        return None
    cwd = Path(cwd or Path.cwd()).resolve()
    ten = re.sub(r"[^A-Za-z0-9]", "-", str(cwd))
    ds = list((goc / ten).glob("*.jsonl")) if (goc / ten).is_dir() else []
    if not ds:
        ds = list(goc.glob("*/*.jsonl"))
    return max(ds, key=lambda p: p.stat().st_mtime) if ds else None


def main(argv: list[str]) -> int:
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    pos = [a for a in argv if not a.startswith("--")]
    f = Path(pos[0]) if pos else tim_transcript()
    if not f or not f.is_file():
        print("Khong thay transcript (.jsonl). Truyen duong dan: b token <file.jsonl>")
        return 1
    d = phan_tich(f)
    print(json.dumps(d, ensure_ascii=False, indent=1) if "--json" in argv else tom_tat(d))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
