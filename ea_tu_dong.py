# -*- coding: utf-8 -*-
"""ea_tu_dong.py - TAI EA THAT -> BIEN DICH -> CHAY STRATEGY TESTER.

VI SAO CO FILE NAY (chu du an chot 01/09/2026).

Do that cung ngay: bo doc ma bang bieu thuc chinh quy (`nhan/doc_ma.py`) rut duoc
**0 co che tren 7 EA MQL5 that su la chien luoc**. Ly do la kien truc chu khong
phai tinh chinh: EA MQL5 hien dai la CHUONG TRINH CO CAU TRUC - quyet dinh vao
lenh nam rai qua nhieu ham, dong vao mot bien `orderType` roi moi toi
`trade.Buy(...)`. Regex khong lan qua duoc. (Pine thi nguoc lai: doc tot, mot
file ra trung binh 4,9 kieu danh.)

Nen voi MQL5, duong nhanh hon va don gian hon la KHONG DOC MA MA CHAY NO. Do la
dung quy trinh cua du an ("MT5 tester TRUOC, Python SAU") va da lam that voi bot
DongDongTV.

RANH GIOI PHAI GIU - va no KHONG phai ly do an ninh nen khong bo theo VPS duoc:

    Tester la BAN THI NGHIEM, khong bao gio la ONG TOA.

Tester tra ve P/L cua MOT bot o MOT cau hinh. No khong sinh ra mot gia thuyet co
`plan_hash`, khong dang ky truoc, khong ton suat FDR va cung khong duoc mien.
Mot con so dep o day la LY DO DE KHAI BAO MOT GIA THUYET roi cho no qua cong
nhu moi gia thuyet khac - khong phai mot ket luan.

BA CAI BAY DA SAP THAT, deu phai kiem lai moi lan doc so:

  1. `Model=1` NOI DOI khi TP hoac SL < ~2x bien do nen M1: +1.161,5% so voi
     -100,7% o tick that. Mac dinh o day la `Model=4` (tick that).
  2. Bao cao .htm tieng Viet goi **Gross Profit** la "Loi nhuan rong"; loi that
     la "**Tong** loi nhuan rong" - sai 13,5 lan.
  3. Tester ap muc swap CUA HOM NAY cho ca lich su, va Exness chi co bar tu
     2022-08 cho 24/25 symbol. Kiem do sau lich su truoc khi so sanh da thi truong.

VA MOT BAY CUA CHINH METAEDITOR, do 01/09: `metaeditor64.exe /compile:<duong dan
TUYET DOI>` tra rc=0 va **khong lam gi ca** - khong .ex5, khong log. Phai dung
duong dan TUONG DOI tinh tu thu muc `MQL5`, kem `cwd` dat o do.

Chay:
    python ea_tu_dong.py --tai 24              # tai + bien dich, khong chay tester
    python ea_tu_dong.py --chay <ten_ea> --symbol US500m --khung H1
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import doc_ma as DM          # noqa: E402
from nhan import ma_nguon as MN        # noqa: E402

REPORTS = LAB / "reports"
KHO_EA = REPORTS / "ea"

#: Thu muc du lieu cua tung terminal + duong toi metaeditor/terminal cua no.
#: May nay co NAM thu muc du lieu MT5 (bai hoc 29/07: phai quet het truoc khi
#: ket luan "khong tim thay").
# Thu muc DU LIEU MT5 doc qua `nhan.duong_dan` - ten nguoi dung khac nhau tren
# moi may, va VPS chac chan khong co "SV STORE".
from nhan.duong_dan import mt5_du_lieu as _mt5_du_lieu

_DAT = _mt5_du_lieu() or Path(
    r"C:\Users\SV STORE\AppData\Roaming\MetaQuotes\Terminal")
_CAI = Path(r"C:\Program Files")

#: ten -> (thu muc DU LIEU, thu muc CAI DAT, symbol mac dinh co lich su that).
#: Nam terminal = nam thu muc du lieu RIENG, va do chinh la co so de chay song
#: song: MT5 khong cho hai tien trinh dung chung mot thu muc du lieu, nhung nam
#: thu muc khac nhau thi chay dong thoi duoc.
TERMINAL = {
    "fxce":       (_DAT / "1A842330F5C043A17800E34E35E4EA61",
                   _CAI / "FXCE MT5 Terminal", "SP500"),
    "metaquotes": (_DAT / "D0E8209F77C8CF37AD8BF550E51FF075",
                   _CAI / "MetaTrader 5", "EURUSD"),
    "xm":         (_DAT / "656C351524AFFE300FAFE576FA4C7845",
                   _CAI / "XM MT5", "EURUSDmicro"),
    "exness":     (_DAT / "53785E099C927DB68A545C249CDBCE06",
                   _CAI / "MetaTrader 5 EXNESS", "XAUUSDm"),
    "ultima":     (_DAT / "43A9BD896CCB6BF2DF5C71EA198AE39D",
                   _CAI / "Ultima Markets MT5 Terminal", "EURUSD"),
}


def _duong(ten_terminal: str) -> tuple[Path, Path, Path]:
    dat, cai, _sym = TERMINAL[ten_terminal]
    return dat / "MQL5", cai / "metaeditor64.exe", cai / "terminal64.exe"


def symbol_mac_dinh(ten_terminal: str) -> str:
    return TERMINAL[ten_terminal][2]


def ten_sach(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s)[:40].strip("_") or "ea"


def tai_lo(so_bai: int = 24, muc: str = "mt5/experts") -> list[dict]:
    """Tai `so_bai` EA that tu MQL5 Code Base. Chi file .mq5 don, khong .zip."""
    from tru import seeker as S
    S._ghi_con_tro("mql5_code", {"trang": {muc: 1}, "danh_muc_ke": 0})
    ds = [d for d in S.n_mql5_code([]) if muc.split("/")[-1] in d["tieu_de"]]
    ra = []
    for d in ds[:so_bai]:
        try:
            r = MN.tai_ma_nguon({"url": d["url"], "tieu_de": d["tieu_de"]})
        except Exception:
            r = None
        if r and r.get("noi_dung"):
            ra.append({"url": d["url"], "ten": d["tieu_de"], "ma": r["noi_dung"]})
        time.sleep(0.4)
    KHO_EA.mkdir(parents=True, exist_ok=True)
    (KHO_EA / "kho.json").write_text(
        json.dumps(ra, ensure_ascii=False), encoding="utf-8")
    return ra


def bien_dich(ds: list[dict], ten_terminal: str = "exness") -> list[dict]:
    """Ghi .mq5 vao MQL5/Experts/_tu_dong roi bien dich tung file.

    Duong dan phai TUONG DOI tinh tu `MQL5` - duong tuyet doi cho rc=0 va khong
    sinh gi ca (do that 01/09, mat mot luot moi phat hien vi khong co thong bao
    loi nao).
    """
    mql5, me, _ = _duong(ten_terminal)
    thu = mql5 / "Experts" / "_tu_dong"
    thu.mkdir(parents=True, exist_ok=True)
    ra = []
    for x in ds:
        ten = ten_sach(x["ten"].split("]")[-1])
        f = thu / f"{ten}.mq5"
        f.write_text(x["ma"], encoding="utf-8")
        rel = "Experts" + chr(92) + "_tu_dong" + chr(92) + f.name
        p = subprocess.Popen([str(me), f"/compile:{rel}", "/log"], cwd=str(mql5))
        for _ in range(48):
            if f.with_suffix(".ex5").exists():
                break
            time.sleep(0.25)
        else:
            try:
                p.kill()
            except Exception:
                pass
        co = f.with_suffix(".ex5").exists()
        loi = ""
        lg = f.with_suffix(".log")
        if not co and lg.exists():
            t = lg.read_text(encoding="utf-16", errors="ignore")
            d = [l for l in t.splitlines() if "error" in l.lower()]
            loi = (d[0] if d else "")[:160]
        ra.append({**x, "ten_file": ten, "bien_dich": co, "loi": loi,
                   "input": DM.rut_input(x["ma"])})
    return ra


def viet_set(ten: str, khai: dict, ten_terminal: str = "exness") -> str:
    """File .set tu khai bao input cua chinh tac gia (gia tri MAC DINH cua ho).

    Khong doan tham so: doc dung cai ho viet. Quet quanh do la buoc sau, va moi
    diem quet la mot suat FDR nen khong duoc quet bua.
    """
    mql5, _, _ = _duong(ten_terminal)
    thu = mql5 / "Profiles" / "Tester"
    thu.mkdir(parents=True, exist_ok=True)
    dong = [f"{k}={v['gia_tri']:g}" for k, v in khai.items()]
    f = thu / f"{ten}.set"
    f.write_text("\n".join(dong) + "\n", encoding="utf-16")
    return f.name


def viet_ini(ten: str, ea: str, tap_set: str, symbol: str, khung: str,
             tu: str, den: str, model: int = 4, von: int = 10000,
             don_bay: int = 100, ten_terminal: str = "exness") -> Path:
    """`.ini` cho tester.

    `Report=` PHAI la duong TUONG DOI - duong tuyet doi bi lo di khong bao loi
    (bai hoc 27/07), va file ra nam trong thu muc DU LIEU cua terminal.
    `Model=4` la tick that: xem cai bay 1 o dau file.
    """
    mql5, _, _ = _duong(ten_terminal)
    ra = mql5.parent / "_bao_cao"
    ra.mkdir(parents=True, exist_ok=True)
    noi = (f"[Tester]\nExpert=_tu_dong{chr(92)}{ea}\nExpertParameters={tap_set}\n"
           f"Symbol={symbol}\nPeriod={khung}\nModel={model}\nExecutionMode=0\n"
           f"Optimization=0\nFromDate={tu}\nToDate={den}\nForwardMode=0\n"
           f"Deposit={von}\nCurrency=USD\nLeverage=1:{don_bay}\nProfitInPips=0\n"
           f"Report=_bao_cao{chr(92)}{ten}\nReplaceReport=1\nShutdownTerminal=1\n")
    f = REPORTS / "tester_ini"
    f.mkdir(parents=True, exist_ok=True)
    p = f / f"{ten}.ini"
    p.write_text(noi, encoding="utf-16")
    return p


def _pid_cua_ten(ten_terminal: str) -> list[int]:
    """PID cua terminal nay, ke ca ban sao LiveUpdate.

    Do that 01/09: `/config:` duoc doc thanh cong roi terminal ghi
    `LiveUpdate start "<data>\\liveupdate\\terminal64.exe" /update /path:... /config:...`
    va tien trinh CHA thoat ngay ("exit with code 0"). Test that chay o tien
    trinh CON, va con do nam duoi thu muc DU LIEU chu khong phai thu muc cai dat
    - nen loc theo mot minh thu muc cai dat thi thay "khong con tien trinh nao"
    va bo cuoc trong khi test dang chay.
    """
    dat, cai, _ = TERMINAL[ten_terminal]
    return _pid_cua(cai) + _pid_cua(dat / "liveupdate")


def _pid_cua(cai: Path) -> list[int]:
    """PID cua nhung `terminal64.exe` chay TU thu muc cai dat nay.

    Ban cu (`chay_mt5_tester.chay_va_cho`) dem TONG so `terminal64.exe`, va cach
    do chi dung khi chay MOT cai mot luc: chay song song thi mot terminal xong se
    bi doc thanh "tat ca da xong", con mot terminal khac dang chay lai giu vong
    cho mai. Phai loc theo DUONG DAN thuc thi.

    Va con bay LiveUpdate cua XM: tien trinh dau doc config roi CHUYEN GIAO cho
    ban sao trong `liveupdate\\` va thoat ngay - nen loc theo tien to thu muc cai
    dat chu khong theo duong dan tuyet doi cua chinh `terminal64.exe`.
    """
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='terminal64.exe'\" | "
         "Select-Object ProcessId,ExecutablePath | ConvertTo-Json -Compress"],
        capture_output=True, text=True, timeout=90)
    try:
        d = json.loads((r.stdout or "").strip() or "[]")
    except Exception:
        return []
    if isinstance(d, dict):
        d = [d]
    # So khop theo BIEN THU MUC, khong phai tien to chuoi. `C:\\Program Files\\
    # MetaTrader 5` la tien to cua `...\\MetaTrader 5 EXNESS`, nen `startswith`
    # gan tien trinh Exness cho ca "metaquotes" - va `dong_terminal("metaquotes")`
    # se giet luon Exness. Da do that: mot PID hien o ca hai muc.
    goc = str(cai).lower().rstrip(chr(92))
    ra = []
    for x in d:
        duong = str(x.get("ExecutablePath") or "").lower()
        if duong == goc + chr(92) + "terminal64.exe" or duong.startswith(goc + chr(92)):
            ra.append(int(x["ProcessId"]))
    return ra


def dong_terminal(ten_terminal: str) -> int:
    """Dong RIENG terminal nay, khong dong cai khac.

    An toan ve vi the: terminal chi la cua so ket noi, lenh nam tren server. Chu
    du an da xac nhan moi tai khoan tren may deu la demo hoac chua dang nhap.
    """
    pids = _pid_cua_ten(ten_terminal)
    for pid in pids:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                       capture_output=True, timeout=60)
    if pids:
        time.sleep(3)
    return len(pids)


#: Duoi nguong nay thi khong chay tester nua. `evolution` khoa buoc kiem tick
#: khi dia < 15 GB, nen chay tiep la tu dap vao cong quyet dinh cua chinh minh.
DIA_TOI_THIEU_GB = 15.0


def dia_trong_gb() -> float:
    import shutil
    return shutil.disk_usage("C:/")[2] / 1024 ** 3


def don_tick(ten_terminal: str, gi_u_history: bool = True) -> float:
    """Xoa bo dem TICK da tai ve. Tra ve so MB thu hoi.

    Vi sao can: do that 01/09 - NAM luot tester tick that lam du lieu MT5 phinh
    **757 MB trong 12 gio**, va dia tu 15,7 GB tut ve 14,8 GB, tuc khoa lai dung
    cai cong `mt5_tick_test` ma sang nay vua mo duoc. Chay not 21 EA se lam mat
    them vai GB.

    An toan: bo dem tick la BAN SAO tu server, xoa di thi lan sau tester tu tai
    lai. Khong dong vao `history` (bar OHLC) vi cai do dung cho ca `du_lieu.nap`
    va tai lai cham hon nhieu.
    """
    dat, _cai, _sym = TERMINAL[ten_terminal]
    thu = dat / "bases"
    if not thu.exists():
        return 0.0
    thu_hoi = 0.0
    for d in thu.rglob("ticks"):
        if not d.is_dir():
            continue
        for f in d.rglob("*"):
            try:
                if f.is_file():
                    thu_hoi += f.stat().st_size / 1024 ** 2
                    f.unlink()
            except OSError:
                pass
    return round(thu_hoi, 1)


def chay_mot(viec: dict) -> dict:
    """Mot luot tester tren MOT terminal. Tra ve duong bao cao va thoi gian."""
    ten_t = viec["terminal"]
    dat, _cai, _sym = TERMINAL[ten_t]
    _, _, term = _duong(ten_t)
    nhan = viec["nhan"]
    bc = dat / "_bao_cao" / f"{nhan}.htm"
    try:
        bc.unlink()
    except OSError:
        pass
    # VAN DIA. Chay tiep khi dia da thap la tu dap vao cong quyet dinh cua chinh
    # minh: `evolution` khoa buoc kiem tick khi dia < 15 GB. Don bo dem tick
    # truoc; van khong du thi TU CHOI chay chu khong chay roi hong giua chung.
    if dia_trong_gb() < DIA_TOI_THIEU_GB:
        thu_hoi = don_tick(ten_t)
        if dia_trong_gb() < DIA_TOI_THIEU_GB:
            return {**viec, "bao_cao": "", "xong": False, "giay": 0.0,
                    "bo_qua": f"dia con {dia_trong_gb():.1f} GB < {DIA_TOI_THIEU_GB} "
                              f"(da don {thu_hoi} MB tick nhung van khong du)"}
    tap_set = viet_set(nhan, viec.get("input") or {}, ten_t)
    ini = viet_ini(nhan, viec["ea"], tap_set, viec["symbol"], viec["khung"],
                   viec["tu"], viec["den"], model=viec.get("model", 4),
                   ten_terminal=ten_t)
    dong_terminal(ten_t)
    t0 = time.time()
    subprocess.Popen([str(term), f"/config:{ini}"])
    # Cho BAO CAO xuat hien, khong cho tien trinh bien mat: LiveUpdate lam tien
    # trinh dau thoat ngay lap tuc trong khi test that chay o tien trinh con.
    han = viec.get("han_giay", 900)
    while time.time() - t0 < han:
        if bc.exists() and bc.stat().st_size > 2000:
            time.sleep(2)
            break
        if time.time() - t0 > 90 and not _pid_cua_ten(ten_t):
            break                       # terminal da thoat ma khong ra bao cao
        time.sleep(3)
    xong = bc.exists() and bc.stat().st_size > 2000
    if not xong:
        dong_terminal(ten_t)
    return {**viec, "bao_cao": str(bc) if xong else "", "xong": xong,
            "giay": round(time.time() - t0, 1)}


def chay_song_song(ds_viec: list[dict]) -> list[dict]:
    """Chay nhieu luot cung luc - MOI TERMINAL MOT LUOT tai mot thoi diem.

    Song song duoc vi moi terminal co thu muc du lieu rieng. Khoa theo terminal
    chu khong theo so luong: hai luot cung mot terminal se dam nhau o khoa thu
    muc du lieu, va cai thu hai chet lang le.
    """
    from concurrent.futures import ThreadPoolExecutor
    theo_t: dict[str, list] = {}
    for v in ds_viec:
        theo_t.setdefault(v["terminal"], []).append(v)

    def _mot_terminal(ds):
        return [chay_mot(v) for v in ds]

    ra = []
    with ThreadPoolExecutor(max_workers=len(theo_t) or 1) as ex:
        for kq in ex.map(_mot_terminal, theo_t.values()):
            ra += kq
    return ra


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tai", type=int, default=0, help="tai va bien dich N EA")
    ap.add_argument("--muc", default="mt5/experts")
    ap.add_argument("--terminal", default="exness")
    a = ap.parse_args()

    if a.tai:
        ds = tai_lo(a.tai, a.muc)
        print(f"tai duoc {len(ds)} file .mq5")
        kq = bien_dich(ds, a.terminal)
        ok = sum(1 for x in kq if x["bien_dich"])
        print(f"bien dich: {ok}/{len(kq)}")
        for x in kq:
            n_in = len(x["input"])
            print(f"  {'OK ' if x['bien_dich'] else 'LOI'} {x['ten_file'][:42]:44} "
                  f"{n_in:3} input  {x['loi'][:60]}")
        (KHO_EA / "bien_dich.json").write_text(
            json.dumps([{k: v for k, v in x.items() if k != "ma"} for x in kq],
                       ensure_ascii=False, indent=1), encoding="utf-8")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
