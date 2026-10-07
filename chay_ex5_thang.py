# -*- coding: utf-8 -*-
r"""chay_ex5_thang.py - chay THANG mot EA bien dich (.ex5) + bo .set tren MT5 tester (terminal XM DEMO).

Viet 04/10/2026 cho bot tai tu Drive/Telegram (khong co ma nguon -> khong qua `ea_tho` bien dich).
- Chi tai khoan DEMO (tester khong dat lenh that). Khong dung terminal cua tai khoan that.
- Mac dinh Model=1 (1-minute OHLC) de QUET NHANH; ket qua Model 1 chi la khao sat, chua phai bang chung
  (niem phong can Model=4 + chat luong lich su >= 90%, xem tai_lieu/LAN_EA_THO.md).
- GIU TEN FILE GOC cua EA (nhieu bot tu kiem ten: "Khong duoc doi ten EA").
- slot 0 = terminal XM that cua may (AppData); slot N>=1 = ban PORTABLE C:\MT5slots\sN (dung_slot_mt5.ps1)
  de chay song song (MT5 khong cho hai tien trinh dung chung thu muc du lieu).
- Dau ra: JSON mot dong / lan chay trong reports/drive_bot_tester.jsonl (khong ghi khoa/so tai khoan).

Chay don:  python chay_ex5_thang.py --ex5 PATH --set PATH --nhan TEN [--slot 0] [--sym GOLD.i#] [--khung M15]
             [--tu 2018-01-01] [--den 2021-10-11] [--model 1] [--von 10000] [--don-bay 500] [--han 1500]
Chay lo:   python chay_ex5_thang.py --lo reports/drive_bot_lo.json --cong 0 --tong 4   (cong 0 = slot 0, chia ca theo chi so)
"""
import argparse, glob, json, os, shutil, subprocess, sys, time, pathlib, datetime

LAB = pathlib.Path(__file__).parent
sys.path.insert(0, str(LAB))
from nhan import bao_cao_mt5 as BC

DAT0 = pathlib.Path(os.environ["APPDATA"]) / "MetaQuotes" / "Terminal" / "BB16F565FAAA6B23A20C26C49416FF05"
CAI0 = pathlib.Path(r"C:\Program Files\XM Global MT5")
KQ = LAB / "reports" / "drive_bot_tester.jsonl"


def duong(slot):
    """(thu muc du lieu, thu muc cai dat, thu muc log agent)"""
    if not slot:
        return DAT0, CAI0, pathlib.Path(os.environ["APPDATA"]) / "MetaQuotes" / "Tester" / DAT0.name
    d = pathlib.Path(r"C:\MT5slots") / f"s{slot}"
    return d, d, d / "Tester"


def dong_terminal(slot):
    _, cai, _ = duong(slot)
    ps = ("Get-Process terminal64,metatester64 -ErrorAction SilentlyContinue | "
          "Where-Object { $_.Path -like '" + str(cai).replace("'", "''") + "\\*' } | Stop-Process -Force")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)
    time.sleep(2)


def con_song(slot):
    """True neu terminal64/metatester64 cua slot con chay (phat hien terminal thoat som: 'account is not specified'...)."""
    import psutil
    _, cai, _ = duong(slot)
    for p in psutil.process_iter(["name", "exe"]):
        try:
            if p.info["name"] and p.info["name"].lower() in ("terminal64.exe", "metatester64.exe") and                     str(p.info["exe"] or "").lower().startswith(str(cai).lower() + os.sep):
                return True
        except Exception:
            pass
    return False


def log_mb(slot):
    """Kich thuoc (MB) lon nhat cua log agent tester cua slot. Mot bot spam log da lam day dia C 26,9 GB (04/10/2026)."""
    _, _, glog = duong(slot)
    fs = (glob.glob(str(glog / "Agent-*" / "logs" / "*.log")) + glob.glob(str(glog / "logs" / "*.log")) +
          glob.glob(str(duong(slot)[0] / "logs" / "*.log")))
    return max([os.path.getsize(f) for f in fs] + [0]) / 1e6


def cat_log(slot, giu_mb=2):
    """Cat log agent ve ~giu_mb MB cuoi (khong xoa tep dang mo)."""
    _, _, glog = duong(slot)
    for f in glob.glob(str(glog / "Agent-*" / "logs" / "*.log")) + glob.glob(str(glog / "logs" / "*.log")):
        try:
            if os.path.getsize(f) > giu_mb * 1e6 * 5:
                with open(f, "rb") as fh:
                    fh.seek(-int(giu_mb * 1e6), 2)
                    d = fh.read()
                with open(f, "wb") as fh:
                    fh.write(d)
        except OSError:
            pass


def log_cuoi(slot, n=10):
    """Cac dong cuoi cua log agent tester (ly do OnInit hong, thieu symbol...), bo dong tham so."""
    _, _, glog = duong(slot)
    fs = sorted(glob.glob(str(glog / "Agent-*" / "logs" / "*.log")), key=os.path.getmtime)
    if not fs:
        return ""
    dong = [l for l in BC.doc_van_ban(fs[-1]).splitlines() if "Tester\t  " not in l]
    return " | ".join(l.strip()[:160] for l in dong[-n:])


def chay(ex5, tap_set, nhan, sym="GOLD.i#", khung="M15", tu="2018-01-01", den="2021-10-11",
         model=1, von=10000, don_bay=500, han=1500, slot=0):
    dat, cai, _ = duong(slot)
    ex5 = pathlib.Path(ex5)
    exp = dat / "MQL5" / "Experts" / "_drive"
    exp.mkdir(parents=True, exist_ok=True)
    ten_ea = ex5.name                      # GIU TEN GOC
    shutil.copyfile(ex5, exp / ten_ea)
    prof = dat / "MQL5" / "Profiles" / "Tester"
    prof.mkdir(parents=True, exist_ok=True)
    ten_set = nhan + ".set"
    if tap_set:
        shutil.copyfile(tap_set, prof / ten_set)
    ra = dat / "_bao_cao"
    ra.mkdir(exist_ok=True)
    for g in ra.glob(nhan + ".*"):
        g.unlink()
    ini = (f"[Tester]\nExpert=_drive{chr(92)}{ten_ea[:-4]}\n" + (f"ExpertParameters={ten_set}\n" if tap_set else "") +
           f"Symbol={sym}\nPeriod={khung}\nModel={model}\nExecutionMode=0\nOptimization=0\n"
           f"FromDate={tu.replace('-', '.')}\nToDate={den.replace('-', '.')}\nForwardMode=0\n"
           f"Deposit={von}\nCurrency=USD\nLeverage=1:{don_bay}\nProfitInPips=0\n"
           f"Report=_bao_cao{chr(92)}{nhan}\nReplaceReport=1\nShutdownTerminal=1\n")
    pini = pathlib.Path(r"C:\MT5slots\ini")      # duong KHONG dau cach: MT5 portable tach sai tham so /config co dau cach
    pini.mkdir(parents=True, exist_ok=True)
    f_ini = pini / (f"s{slot}_" + nhan + ".ini")
    f_ini.write_text(ini, encoding="utf-16")
    dong_terminal(slot)
    t0 = time.time()
    lenh = [str(cai / "terminal64.exe")] + (["/portable"] if slot else []) + [f"/config:{f_ini}"]
    subprocess.Popen(lenh)
    ok = False
    bc = None
    spam = False
    while time.time() - t0 < han:
        if log_mb(slot) > 300:           # bot spam log -> dung ngay
            spam = True
            break
        if time.time() - t0 > 60 and not con_song(slot):      # terminal da thoat ma chua co bao cao
            time.sleep(3)
            if not [p for p in ra.glob(nhan + ".*") if p.suffix.lower() in (".htm", ".html")]:
                break
        bao = [p for p in ra.glob(nhan + ".*") if p.suffix.lower() in (".htm", ".html") and p.stat().st_size > 2000]
        if bao:
            time.sleep(2)
            bc = bao[0]
            ok = True
            break
        time.sleep(4)
    giay = round(time.time() - t0, 1)
    dong_terminal(slot)
    cat_log(slot)
    kq = {"nhan": nhan, "ea": ex5.name, "set": pathlib.Path(tap_set).name if tap_set else "", "sym": sym, "khung": khung,
          "tu": tu, "den": den, "model": model, "von": von, "don_bay": don_bay, "giay": giay, "slot": slot,
          "luc": datetime.datetime.now().isoformat(timespec="seconds"), "xong": ok}
    if ok:
        d = BC.doc_bao_cao(bc)
        kq["bao_cao"] = str(bc)
        kq["doc_duoc"] = d.get("doc_duoc")
        kq["thieu"] = d.get("thieu")
        kq["so"] = {k: v for k, v in d.items() if k not in ("doc_duoc", "thieu", "van_ban", "file")}
        if not (kq["so"].get("so_lenh") or 0):
            kq["log_cuoi"] = log_cuoi(slot)
    else:
        kq["loi"] = "log_spam (>300MB): dung de khong day dia" if spam else "khong ra bao cao trong %ds" % han
        kq["log_cuoi"] = log_cuoi(slot)
    with open(KQ, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(kq, ensure_ascii=False) + "\n")
    return kq


def tom_tat(k):
    s = k.get("so") or {}
    return "%s | %ss | lenh %s | lai %s | DD %s%% | PF %s | chat luong %s%%" % (
        k["nhan"], k["giay"], s.get("so_lenh"), s.get("lai_rong"), s.get("dd_pct"), s.get("pf"), s.get("chat_luong_pct"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ex5")
    ap.add_argument("--set", dest="tap_set", default="")
    ap.add_argument("--nhan")
    ap.add_argument("--sym", default="GOLD.i#")
    ap.add_argument("--khung", default="M15")
    ap.add_argument("--tu", default="2018-01-01")
    ap.add_argument("--den", default="2021-10-11")
    ap.add_argument("--model", type=int, default=1)
    ap.add_argument("--von", type=int, default=10000)
    ap.add_argument("--don-bay", type=int, default=500)
    ap.add_argument("--han", type=int, default=1500)
    ap.add_argument("--slot", type=int, default=0)
    ap.add_argument("--lo")
    ap.add_argument("--cong", type=int, default=0, help="chi so cong/slot nay trong lo (0..tong-1); slot = cong")
    ap.add_argument("--tong", type=int, default=1)
    a = ap.parse_args()
    if a.lo:
        viec = json.load(open(a.lo, encoding="utf-8"))
        da = set()
        if KQ.exists():
            for l in KQ.read_text(encoding="utf-8").splitlines():
                try:
                    j = json.loads(l)
                    if j.get("xong"):
                        da.add(j["nhan"])
                except ValueError:
                    pass
        for i, v in enumerate(viec):
            if i % a.tong != a.cong or v["nhan"] in da:
                continue
            kv = dict(v)
            kv.setdefault("han", a.han)
            k = chay(slot=a.cong, **kv)
            print(tom_tat(k), flush=True)
    else:
        k = chay(a.ex5, a.tap_set, a.nhan, a.sym, a.khung, a.tu, a.den, a.model, a.von, a.don_bay, a.han, a.slot)
        print(tom_tat(k), "|", json.dumps(k, ensure_ascii=False)[:600])
