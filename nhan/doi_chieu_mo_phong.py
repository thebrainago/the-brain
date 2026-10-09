"""Tong hop cac don `hieu_chuan_luoi` (engine luoi.py <-> MT5 tester): cung dau bao nhieu, lac quan bao nhieu lan,
va LUAT LOC de xuat. Chi dem don co so that (don hong / TesterDangBan bi bo, khong tinh nhu 'am').
Chay: python3 -m nhan.doi_chieu_mo_phong [--giao-lai] [--theo-chat-luong]

CHAT LUONG LICH SU TESTER (09/10/2026): moi bao cao ghi `tester.chat_luong_pct` = bao nhieu % lich su M1 la THAT trong cua so.
Do tren 125 bao cao da luu: cua so 2019 = 100%, 2018-H2 = 51%, 2018-H1 = 1% (AUDCAD / NZDCAD / EURCAD: M1 that chi bat dau ~10/2018).
Cua so < `NGUONG_CHAT_LUONG` la o NHIEM: tester tu doan phan lich su thieu nen so voi engine o do khong noi gi ve ENGINE.
Va `so_khoa` cua engine la SAU swap con tester la TRUOC swap (MT5 tester khong ghi swap): muon so mo hinh gia / thu tu lenh
thi phai so TRUOC swap ca hai ben (`lai_chua_swap`). `--theo-chat-luong` in ca hai cach, tach o sach / o nhiem."""
import glob, json, re, sys, statistics as S

#: LUAT LOC CHOT 07/10/2026 (n=52 mau that engine <-> MT5): chi CAT khi engine <= nguong nay (%/nam).
#: Do duoc: cung dau 41/52; engine <= -10 co 10 mau, MT5 deu am (0 cat nham); engine <= -5: 12 mau, 1 cat nham;
#: engine <= 0: 22 mau, 6 cat nham (KHONG dung). Engine duong khong chung minh gi: 5/52 MT5 am; engine lac quan ~1,8 lan.
#: CANH BAO 09/10/2026: ~80% mau do la cua so 2018 (chat luong lich su tester 1-51%) va so engine SAU swap voi tester TRUOC swap;
#: tren o SACH (2019, 100%) ket qua khac (xem `--theo-chat-luong`). Giu luat nhu cu cho den khi dung lai tren o sach, truoc swap.
NGUONG_CAT = -10.0

#: Chat luong lich su tester (%) tu muc nay moi coi la o SACH (2019 = 100; 2018-H2 = 51).
NGUONG_CHAT_LUONG = 95.0

_RE = re.compile(r'"so_khoa":\s*\[\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)')
_RE6 = re.compile(r'"so_khoa":\s*\[\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)')
_RE_BAO_CAO = re.compile(r'"bao_cao":\s*"([^"]+)"')


def doc(thu_muc="viec/xong"):
    mau, hong = {}, []
    for f in glob.glob(thu_muc + "/*hc-luoi-*.json"):
        d = json.load(open(f, encoding="utf-8"))
        t = "".join(d.get("bang_chung", {}).get("dong_cuoi") or [])
        m = _RE.search(t)
        if m:
            e, mt, dde, dmt = (float(x) for x in m.groups())
            mau[d["ma"]] = (e, mt, dde, dmt)
        else:
            hong.append(d["ma"])
    return mau, hong


def _pct_nam(thong_ke, von, nam, khoa="lai_chua_swap"):
    """Mot khoan trong `thong_ke` (mac dinh lai TRUOC swap; tien tai khoan) doi ra %/nam; None neu thieu."""
    try:
        return float(thong_ke[khoa]) / von / nam * 100.0
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None


def _bao_cao(tep_moi, duong):
    """Bao cao hieu chuan nhung trong ket qua don (`tep_moi[duong]` la van ban JSON). Hong / thieu -> {}."""
    try:
        r = json.loads((tep_moi or {})[duong])
        return r if isinstance(r, dict) else {}
    except (KeyError, TypeError, ValueError):
        return {}


def doc_day_du(thu_muc="viec/xong"):
    """MOT dong cho moi bao cao hieu chuan (khong trung), tu moi don co lenh `hieu_chuan_luoi` (khong chi `hc-luoi-*`).
    Cot: job, bao_cao, ma, khung, tu, den, q (chat luong lich su tester %, None neu khong doc duoc bao cao),
    engine / tester (%/nam, `so_khoa`: engine SAU swap, tester TRUOC swap), dd_e / dd_t, n_e / n_t (so lenh),
    e_truoc / t_truoc (%/nam TRUOC swap, None neu bao cao thieu), swap_e (%/nam), pb (phien ban engine)."""
    dong = {}
    files = []
    for f in glob.glob(thu_muc + "/*.json"):
        try:
            files.append(json.load(open(f, encoding="utf-8")))
        except (OSError, ValueError):
            continue
    for d in sorted(files, key=lambda x: str(x.get("luc") or "")):         # cung bao cao chay hai lan: giu lan moi nhat
        b = d.get("bang_chung") or {}
        if "hieu_chuan_luoi" not in " ".join(map(str, b.get("lenh") or [])):
            continue
        van_ban = "".join(b.get("dong_cuoi") or [])
        k, bc = _RE6.search(van_ban), _RE_BAO_CAO.search(van_ban)
        if not k or not bc:
            continue
        e, t, de, dt, ne, nt = (float(x) for x in k.groups())
        r = _bao_cao(b.get("tep_moi"), bc.group(1))
        ts_, es = (r.get("tester") or {}), (r.get("engine") or {})
        cs = r.get("cua_so") or {}
        von = float(r.get("von") or 0) or None
        nam = (float(cs.get("ngay") or 0) / 365.25) or None
        dong[bc.group(1)] = {
            "job": d.get("ma"), "bao_cao": bc.group(1), "ma": r.get("ma"), "khung": r.get("khung"),
            "tu": cs.get("tu"), "den": cs.get("den"), "q": ts_.get("chat_luong_pct"),
            "engine": e, "tester": t, "dd_e": de, "dd_t": dt, "n_e": ne, "n_t": nt,
            "e_truoc": _pct_nam(es.get("thong_ke"), von, nam) if von and nam else None,
            "t_truoc": _pct_nam(ts_.get("thong_ke"), von, nam) if von and nam else None,
            "swap_e": _pct_nam(es.get("thong_ke"), von, nam, "swap") if von and nam else None,
            "pb": r.get("phien_ban_engine")}
    return list(dong.values())


def phan_nhom(rows, nguong=NGUONG_CHAT_LUONG):
    """{'sach': q >= nguong, 'nhiem': q < nguong, 'chua_ro': khong doc duoc chat luong}."""
    kq = {"sach": [], "nhiem": [], "chua_ro": []}
    for r in rows:
        q = r.get("q")
        kq["chua_ro" if q is None else ("sach" if q >= nguong else "nhiem")].append(r)
    return kq


def so_nhom(rows, truoc_swap=True):
    """Do lech engine - tester cua mot nhom o (`truoc_swap=True`: lai TRUOC swap ca hai ben; False: `so_khoa` nhu bao cao).
    Tra {n, cung_dau, engine_duong_tester_khong, engine_khong_tester_duong, lech_trung_vi, sai_so_tb, ti_le_trung_vi,
    ti_le_lenh_trung_vi, ti_le_dd_trung_vi}; hang thieu so TRUOC swap bi bo (n cho biet con lai bao nhieu)."""
    if truoc_swap:
        cap = [(r["e_truoc"], r["t_truoc"], r) for r in rows if r.get("e_truoc") is not None and r.get("t_truoc") is not None]
    else:
        cap = [(r["engine"], r["tester"], r) for r in rows]
    n = len(cap)
    if not n:
        return {"n": 0}
    ty = [e / t for e, t, _ in cap if e > 0 and t > 0]
    ty_lenh = [r["n_e"] / r["n_t"] for _, _, r in cap if r.get("n_t")]
    ty_dd = [r["dd_e"] / r["dd_t"] for _, _, r in cap if r.get("dd_t") and r["dd_t"] > 1]
    return {"n": n,
            "cung_dau": sum((e > 0) == (t > 0) for e, t, _ in cap),
            "engine_duong_tester_khong": sum(e > 0 >= t for e, t, _ in cap),
            "engine_khong_tester_duong": sum(e <= 0 < t for e, t, _ in cap),
            "tester_duong": sum(t > 0 for _, t, _ in cap),
            "lech_trung_vi": round(S.median(e - t for e, t, _ in cap), 2),
            "sai_so_tb": round(S.mean(abs(e - t) for e, t, _ in cap), 2),
            "ti_le_trung_vi": round(S.median(ty), 2) if ty else None,
            "ti_le_lenh_trung_vi": round(S.median(ty_lenh), 3) if ty_lenh else None,
            "ti_le_dd_trung_vi": round(S.median(ty_dd), 2) if ty_dd else None}


def tom_tat(mau):
    v = list(mau.values())
    n = len(v)
    if not n:
        return {"n": 0}
    cung = sum((e > 0) == (m > 0) for e, m, *_ in v)
    ea_duong_mt_am = sum(e > 0 >= m for e, m, *_ in v)
    ea_am_mt_duong = sum(e <= 0 < m for e, m, *_ in v)
    ty = [e / m for e, m, *_ in v if e > 0 and m > 0]
    # luat loc: cat khi engine <= nguong; do bao nhieu mau MT5 duong bi cat nham / mau MT5 am bi cat dung
    kq = {"n": n, "cung_dau": cung, "engine_duong_MT5_am": ea_duong_mt_am, "engine_am_MT5_duong": ea_am_mt_duong,
          "lac_quan_trung_vi": round(S.median(ty), 2) if ty else None, "luat_cat": {}}
    for ng in (0, -5, -10, -20):
        cat = [(e, m) for e, m, *_ in v if e <= ng]
        kq["luat_cat"][ng] = {"cat": len(cat), "cat_nham_MT5_duong": sum(m > 0 for _, m in cat)}
    return kq


def in_theo_chat_luong(thu_muc="viec/xong", out=print):
    rows = doc_day_du(thu_muc)
    nhom = phan_nhom(rows)
    out("bao cao hieu chuan: %d (sach %d, nhiem %d, chua ro %d)" % (len(rows), len(nhom["sach"]), len(nhom["nhiem"]), len(nhom["chua_ro"])))
    for ten, g in nhom.items():
        for nhan, ts in (("TRUOC swap", True), ("so_khoa (engine sau swap)", False)):
            out("%-8s %-26s %s" % (ten, nhan, json.dumps(so_nhom(g, ts), ensure_ascii=False)))
    return rows


if __name__ == "__main__":
    mau, hong = doc()
    print(json.dumps(tom_tat(mau), ensure_ascii=False))
    print("don hong/thieu so:", len(hong))
    if "--giao-lai" in sys.argv:
        print("\n".join(hong))
    if "--theo-chat-luong" in sys.argv:
        in_theo_chat_luong()
