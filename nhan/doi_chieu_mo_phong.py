"""Tong hop cac don `hieu_chuan_luoi` (engine luoi.py <-> MT5 tester): cung dau bao nhieu, lac quan bao nhieu lan,
va LUAT LOC de xuat. Chi dem don co so that (don hong / TesterDangBan bi bo, khong tinh nhu 'am').
Chay: python3 -m nhan.doi_chieu_mo_phong [--giao-lai]"""
import glob, json, re, sys, statistics as S

_RE = re.compile(r'"so_khoa":\s*\[\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)')


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


if __name__ == "__main__":
    mau, hong = doc()
    print(json.dumps(tom_tat(mau), ensure_ascii=False))
    print("don hong/thieu so:", len(hong))
    if "--giao-lai" in sys.argv:
        print("\n".join(hong))
