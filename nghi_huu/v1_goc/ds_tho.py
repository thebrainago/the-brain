# -*- coding: utf-8 -*-
"""
ds_tho.py - GOI DEEPSEEK LAM THO, CLAUDE LAM GIAM SAT
=====================================================================================
Phan vai da chot: Claude xay khung + thiet ke gia thuyet; DeepSeek chay khoi luong
(re hon nhieu lan); Claude soi lai loi. File nay la duong day noi hai ben.

NGUYEN LY THIET KE QUAN TRONG NHAT
----------------------------------
DeepSeek KHONG duoc tu dat luat do. No chi duoc viet DUNG MOT HAM:

    def do(khoa, df, rng) -> dict(thong_ke=float, p=float, n=int, ghi_chu=str)

Con lai - tap sang la nhung thi truong nao, chay may hat, gop the nao, doc ket qua
ra sao - do `brain_co_che.py` giu. Nghia la mot tho au KHONG THE che ra edge gia,
vi no khong cam cai can de che: no khong chon duoc tap du lieu, khong chon duoc
nguong, khong viet duoc cau ket luan.

Cai no de sai nhat va bi bat o day:
  - nhin truoc (dung close[i] de vao lenh o bar i)     -> bat bang cong nhan qua
  - khong co null tu than                              -> bat bang p bat buoc
  - dung bien do cum lai lam ket qua                   -> Claude soi tay
  - goi ra mang / xoa file / doc tap xac nhan          -> bat bang quet an toan

CLI:
  python ds_tho.py --thu                       # goi thu API 1 cau
  python ds_tho.py --lam <ten_co_che> --y-tuong "mo ta khang dinh can do"
  python ds_tho.py --kiem <ten_co_che>         # in code + ket qua de Claude soi
  python ds_tho.py --hang-doi                  # lam het viec 'sang' con treo
  python ds_tho.py --tho <so>                  # id tho, de chay nhieu ban song song
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
CO_CHE_DS = HERE / "co_che_ds"          # noi DeepSeek duoc phep ghi code
REPORTS = HERE / "reports"
GHI_CHEP = REPORTS / "ds"               # toan van hoi dap, de Claude soi lai
for d in (CO_CHE_DS, REPORTS, GHI_CHEP):
    d.mkdir(exist_ok=True)

CAU_HINH = Path.home() / ".codex" / "config.toml"
SO_VONG_SUA = 4                          # so lan cho no tu sua khi code hong
HET_GIO_CHAY = 900                       # giay cho moi lan chay thu


# ---------------------------------------------------------------------------
# Goi API
# ---------------------------------------------------------------------------

def _doc_cau_hinh():
    t = CAU_HINH.read_text(encoding="utf-8")
    khoa = re.search(r'experimental_bearer_token\s*=\s*"([^"]+)"', t)
    url = re.search(r'base_url\s*=\s*"([^"]+)"', t)
    mo_hinh = re.search(r'^model\s*=\s*"([^"]+)"', t, re.M)
    if not (khoa and url):
        raise SystemExit(f"Khong doc duoc khoa/base_url trong {CAU_HINH}")
    return khoa.group(1), url.group(1).rstrip("/"), (mo_hinh.group(1) if mo_hinh else "deepseek-v4-flash")


def goi(tin_nhan, nhiet=0.4, toi_da_token=32000):
    """Goi API. Hai bay da sap va da vá:
      - day la mo hinh CO SUY NGHI: token suy nghi tinh vao `max_tokens`, de 8000
        thi no nghi het sach va tra content RONG (khong bao loi gi).
      - content rong nhung `reasoning_content` co code -> phai lay bu.
    """
    khoa, url, mo_hinh = _doc_cau_hinh()
    du_lieu = json.dumps({"model": mo_hinh, "messages": tin_nhan,
                          "temperature": nhiet, "max_tokens": toi_da_token}).encode()
    yc = urllib.request.Request(f"{url}/chat/completions", data=du_lieu, headers={
        "Authorization": f"Bearer {khoa}", "Content-Type": "application/json"})
    # 6 lan, cho lui dan toi 4 phut. Ly do: chay HAI tho song song thi API co luc
    # nghen (429), va truoc day chi thu 3 lan roi nem loi -> ca vong tu sinh chet.
    # Da xay ra that: hai tho chet luc 10:36 sau 11 phut, cua so van mo nhung rong.
    cho = [5, 15, 40, 90, 180, 240]
    for lan in range(6):
        try:
            with urllib.request.urlopen(yc, timeout=900) as r:
                j = json.loads(r.read())
            lc = j["choices"][0]
            m = lc.get("message", {})
            noi_dung = (m.get("content") or "").strip()
            if not noi_dung:
                noi_dung = (m.get("reasoning_content") or "").strip()
            if not noi_dung:
                raise KeyError(f"tra ve rong (finish={lc.get('finish_reason')}, "
                               f"usage={j.get('usage')})")
            return noi_dung
        except (urllib.error.URLError, TimeoutError, KeyError,
                json.JSONDecodeError, OSError) as e:
            if lan == 5:
                raise RuntimeError(f"goi API hong 6 lan: {e}")
            print(f"      (API loi: {str(e)[:80]} - cho {cho[lan]}s roi thu lai)", flush=True)
            time.sleep(cho[lan])


# ---------------------------------------------------------------------------
# Hop dong dau ra - phan quyet dinh chat luong
# ---------------------------------------------------------------------------

HOP_DONG = """Ban la nha nghien cuu dinh luong lam viec trong mot he thong da co san
ky luat thong ke. Ban duoc TU DO hoan toan ve PHUONG PHAP: cach dinh nghia su kien,
cach do, dung mo hinh gi, tao dac trung the nao - do la phan viec cua ban va he
thong khong can thiep. Neu ban thay cach phat bieu khang dinh la sai hoac co cach
do sac hon, HAY LAM THEO CACH CUA BAN va noi ro trong `ghi_chu`.

Chi co MOT giao dien co dinh, de he thong chay code cua ban tren 28 thi truong roi
gop ket qua giup ban:

    def do(khoa, df, rng):
        \"\"\"khoa: ten thi truong (str). df: DataFrame index=time, cot
        open/high/low/close/volume, da lam sach. rng: numpy Generator.
        Tra ve dict hoac None. Bat buoc 3 khoa: thong_ke (float), p (float),
        n (int). Muon them khoa nao tuy y - he thong se giu nguyen va bao cao.\"\"\"

Ban co the dinh nghia bao nhieu ham phu tuy thich trong cung file.

HAI DIEU KHONG THUONG LUONG - khong phai de bo cach lam cua ban, ma vi thieu chung
thi con so ban tao ra khong doc duoc, va ca hai deu tung lam hong ket qua that o
du an nay:

1. NHAN QUA. Quyet dinh o bar i chi duoc dung thong tin toi het bar i-1 (hoac chinh
   bar i neu ban vao lenh o open[i+1]). Khong dat nguong bang thong ke cua CA chuoi.
   Bat cu nhan nao co the bi VE LAI khi co bar moi thi phai tu bao trong `ghi_chu`.

2. `p` la p-value tu HOAN VI cua chinh du lieu do (khong lay tu cong thuc t-test),
   va hoan vi phai GIU PHOI NHIEM: hoan vi NGAY XAY RA su kien / nhan nhom, giu
   nguyen so su kien va ty le mua-ban. Hoan vi chuoi lai/lo luon ra ~50% - do la
   loi kinh dien va du an nay da mac.

Ba dieu NEN, ban tu can nhac:

3. `thong_ke` phai NEO VAO NULL CUA CHINH NO, khong neo vao so 0. Cu the: da tinh
   phan phoi hoan vi roi thi tra ve
        thong_ke = (quan_sat - trung_binh_null) / do_lech_chuan_null
   Ly do ky thuat: he thong gop 28 thi truong bang PHEP THU DAU tren `thong_ke`, ma
   phep thu dau chi dung khi null nam o 0. Nhieu phep do co null LECH KHOI 0 mot
   cach he thong (vi drift, vi ty le long/short, vi phi doi xung cua loi suat) -
   luc do dau cua so tho khong con y nghia gi. Da bat duoc dung loi nay: mot phep do
   co null trung binh -0,0246 trong khi quan sat +0,0647; doc dau tho thi thanh
   "duong nhe", doc theo null thi la +2,6 do lech chuan.
   Dat them `quan_sat_tho`, `null_tb`, `null_sd` vao dict de nguoi soi doi chieu.
   Duong = ung ho khang dinh; neu ban chon quy uoc khac thi ghi ro trong `ghi_chu`.

3b. CUNG MOT MAU SO. Neu quan sat chia cho N nay ma hoan vi chia cho N khac thi hai
   con so khong so sanh duoc, va p tra ve la rac - nhung code van chay, van in ra so
   dep, khong bao loi gi. Da bat duoc loi nay that: quan sat chia 8.022 (tat ca cac
   ngay) trong khi hoan vi chia 993 (so su kien) -> p nhay tu 0,0025 len 0,1785.
   Truoc khi nop, hay tu hoi: hai ve co dung mot mau so khong.

4. Neu thuoc do cua ban lien quan den DO LON (do doc, do dai, bien do), hay can nhac
   chia cho bien do duong nhien tai thoi diem do. Ly do: bien dong cum lai, nen hai
   doan canh nhau tu dong giong nhau, va phep do se bao "co cau truc" trong khi chi
   la volatility clustering. Da lam hong mot phep do trong du an nay tuan truoc.
   Neu ban co cach xu ly khac tot hon, cu dung - chi can noi ro.

5. Mau nho de ra ao giac. Duoi ~30 su kien thi nen tra None.

CO SAN, NEN DUNG (khong bat buoc, nhung tu viet lai thi de sai va de cham):
Trong file cua ban duoc phep `import brain_co_che as bc` va dung:
    bc.chan_song(df)      -> DataFrame cac chan: vi_tri | xac_nhan | gia | loai
    bc.cac_doan(df, ch)   -> cac doan noi hai chan: tu | den | biet_tai | do_dai |
                             thoi_luong | do_doc | huong
    bc.atr(df, 14)        -> ATR
GIOI HAN DA DO CUA TAP SANG - biet truoc de khoi phi vong:
Voi `bc.chan_song(df)` mac dinh (nguong 3xATR) tren khung NGAY, moi thi truong chi co
**150 den 600 chan** (trung vi 322). Nghia la:
  - khang dinh ve QUAN HE giua cac chan: du mau (trung vi 322 doan, 216 doan nguoc xu the)
  - khang dinh loc them theo PHAN VI CAO cua do dai chan: con 10-20% -> 15 den 64 su kien,
    nhieu thi truong TUT DUOI 30 va ham cua ban se tra None o gan het tap sang.
Neu khang dinh cua ban roi vao ve thu hai, ban duoc phep HA NGUONG: `bc.chan_song(df, he_so=1.5)`
hoac thap hon, tang dan cho toi khi du mau. Dieu kien: chon nguong theo SO MAU, tuyet doi
khong theo KET QUA, va ghi nguong da chon vao `ghi_chu`. Ha nguong thi "chan" thanh mot
vat khac (nho hon, nhieu nhieu hon) - noi ro de nguoi doc biet.

Diem mau chot: hai bang tren co CA HAI cot thoi gian. `vi_tri` la cho dinh/day THAT
SU nam; `xac_nhan` / `biet_tai` la bar ma ta MOI BIET no la dinh/day. Tu viet zigzag
thi hau nhu ai cung chi giu cot dau roi tinh loi suat tu do - tuc dung mot cai dinh
truoc khi bat ky ai biet no la dinh. Do la nhin truoc, va no lam moi ket qua dep len.
Neu ban tu viet bo tim chan, ban PHAI tu sinh ra cot thu hai va dung no.

KY THUAT:
- Duoc dung: numpy, pandas, math, itertools, functools, collections, scipy,
  statsmodels, sklearn (neu import loi thi tu lui ve numpy/pandas).
- KHONG duoc: goi mang (requests/urllib/socket), doc-ghi file, subprocess, exec/eval.
  Khong phai vi khong tin ban, ma vi tien trinh nay chay khong ai truc.
- 1 thi truong ~10.000 bar nen xong duoi 20 giay. Hoan vi 2000 lan la du. Vector hoa.

DUOC KHUYEN KHICH - cua rieng cho y tuong cua ban:
Neu trong luc do ban nghi ra mot khang dinh KHAC dang test hon, hay them vao dict
tra ve khoa `de_xuat` (chuoi, 1-3 cau). He thong se gom lai thanh mot danh sach
rieng cho nguoi doc. Day khong phai muc trang tri - hai thu song sot duy nhat cua
du an nay deu la dang "A khi B" (ghep co dieu kien), nen mot y tuong ghep dung
gia hon mot phep do sach.

Tra ve DUY NHAT khoi code python, bat dau bang ```python va ket thuc bang ```.
"""

# Chan tinh: chi chan thu that su nguy hiem cho mot tien trinh chay khong ai truc.
# KHONG chan thu vien mo hinh, khong chan vong lap - do la viec cua no.
CAM = [r"\bimport\s+(subprocess|shutil|socket|requests|urllib|ctypes|multiprocessing)\b",
       r"\bfrom\s+(subprocess|shutil|socket|requests|urllib|ctypes)\b",
       r"\bos\.(remove|unlink|rmdir|system|popen)\b",
       r"\bopen\s*\([^)]*['\"][wa]", r"\beval\s*\(", r"\bexec\s*\(",
       r"\bto_parquet\b", r"\bto_csv\b"]


def quet_an_toan(code):
    loi = [m for m in CAM if re.search(m, code)]
    return loi


def rut_code(tra_loi):
    m = re.search(r"```(?:python)?\s*(.+?)```", tra_loi, re.S)
    return (m.group(1) if m else tra_loi).strip()


# ---------------------------------------------------------------------------
# Chay thu qua dung khung ky luat cua brain_co_che
# ---------------------------------------------------------------------------

KICH_BAN_CHAY = r'''# -*- coding: utf-8 -*-
"""Chay ham `do` cua tho qua dung bo ky luat tang kham pha, in JSON ra stdout."""
import json, sys, importlib.util
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
import brain_co_che as bc

ten = sys.argv[1]
duong_dan = Path(sys.argv[2])
chi_kl = len(sys.argv) > 3 and sys.argv[3] == "kl"

spec = importlib.util.spec_from_file_location("co_che_tho", duong_dan)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

kq = bc.chay_ham(m.do, ten, ma_kd="DS", chi_kl=chi_kl, in_ra=False, so_hat=3)
if not kq or "loi_mau" in kq:
    print(json.dumps({"loi": (kq or {}).get("loi_mau", "khong thi truong nao chay duoc")},
                     ensure_ascii=False)); sys.exit(0)
g = kq["gop"]
print(json.dumps({
    "co_che": ten, "tom_tat": kq["tom_tat"],
    "trung_vi": g["trung_vi"], "so_thi_truong": g["so_thi_truong"],
    "so_duong": g["so_duong"], "nhom_duong": g["nhom_duong"], "so_nhom": g["so_nhom"],
    "p_theo_nhom": g["p_theo_nhom"], "p_28_dong": g["p_phep_thu_dau"],
    "trung_vi_nhom": g["trung_vi_nhom"],
    "theo_thi_truong": [{k: (float(v) if isinstance(v, (int, float, np.floating)) else v)
                         for k, v in r.items()} for r in kq["theo_thi_truong"]],
}, ensure_ascii=False))
'''

KICH_BAN = HERE / "_ds_chay.py"


def chay_thu(ten, duong_dan, chi_kl=False):
    KICH_BAN.write_text(KICH_BAN_CHAY, encoding="utf-8")
    try:
        r = subprocess.run([sys.executable, str(KICH_BAN), ten, str(duong_dan),
                            "kl" if chi_kl else "-"],
                           cwd=str(HERE), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=HET_GIO_CHAY)
    except subprocess.TimeoutExpired:
        return None, f"HET GIO sau {HET_GIO_CHAY}s - code qua cham, phai vector hoa"
    ra = (r.stdout or "").strip().splitlines()
    for dong in reversed(ra):
        if dong.startswith("{"):
            try:
                return json.loads(dong), None
            except json.JSONDecodeError:
                pass
    return None, ((r.stderr or "")[-2500:] or "khong co dau ra JSON")


# ---------------------------------------------------------------------------
# Vong lam viec: giao -> chay -> bao loi -> tu sua
# ---------------------------------------------------------------------------

def lam(ten, y_tuong, chi_kl=False, tho=0, gop_y=None):
    """gop_y: nhan xet cua Claude sau khi soi code vong truoc. Day la vong hoc that -
    khong phai sua loi cu phap ma sua CACH NGHI, nen no duoc nap kem code cu."""
    print(f"[tho {tho}] === {ten} ===")
    boi_canh = ""
    p = Path.home() / "Desktop" / "PROMPT_DEEPSEEK_TU_DUY.md"
    if p.exists():
        boi_canh = ("\n\nBoi canh he thong (doc de hieu tai sao co cac luat tren, "
                    "KHONG can lam theo dinh dang trong do):\n" + p.read_text(
                        encoding="utf-8", errors="replace")[:6000])

    tn = [{"role": "system", "content": HOP_DONG + boi_canh},
          {"role": "user", "content":
           f"Khang dinh can do: {y_tuong}\n\n"
           f"Viet ham `do(khoa, df, rng)` do dung khang dinh nay. Nho luat 4 "
           f"(chia cho bien do duong nhien) va luat 2 (hoan vi giu phoi nhiem)."}]

    if gop_y:
        cu = CO_CHE_DS / f"{ten}.py"
        tn.append({"role": "assistant", "content":
                   "```python\n" + (cu.read_text(encoding="utf-8") if cu.exists() else "") + "\n```"})
        tn.append({"role": "user", "content":
                   "Ban da nop ban tren. Nguoi soi ket qua tim ra may cho sau. Day khong "
                   "phai loi cu phap - code chay duoc - ma la cho lam CON SO KHONG DOC "
                   "DUOC. Doc ky, sua, va giai thich ngan o docstring vi sao cach moi dung "
                   "hon:\n\n" + gop_y +
                   "\n\nNeu ban thay mot trong cac nhan xet la SAI, hay noi ro va giu cach "
                   "cua ban - nhung phai lap luan, dung im lang lam theo."})

    lich_su = []
    for vong in range(1, SO_VONG_SUA + 1):
        print(f"  vong {vong}: hoi DeepSeek...", flush=True)
        tra_loi = goi(tn)
        code = rut_code(tra_loi)
        lich_su.append({"vong": vong, "tra_loi": tra_loi})

        if not code.strip() or "def do" not in code:
            print("    tra ve khong co ham `do` - hoi lai")
            tn += [{"role": "assistant", "content": tra_loi[:2000]},
                   {"role": "user", "content":
                    "Toi khong thay khoi ```python nao co `def do(khoa, df, rng)`. "
                    "Tra lai DUY NHAT mot khoi code python day du."}]
            lich_su[-1]["loi"] = "khong co ham do"
            continue

        vi_pham = quet_an_toan(code)
        if vi_pham:
            loi = f"QUET AN TOAN CHAN: {vi_pham}. Viet lai, chi dung numpy/pandas/math."
            print(f"    chan: {vi_pham}")
        else:
            f = CO_CHE_DS / f"{ten}.py"
            f.write_text(code, encoding="utf-8")
            print(f"    chay thu {f.name} ...", flush=True)
            kq, loi = chay_thu(ten, f, chi_kl)
            if kq and "loi" in kq:
                loi = kq["loi"]
                kq = None
            if kq:
                lich_su[-1]["ket_qua"] = kq
                (GHI_CHEP / f"{ten}.json").write_text(
                    json.dumps({"ten": ten, "y_tuong": y_tuong, "tho": tho,
                                "luc": datetime.now().isoformat(timespec="seconds"),
                                "so_vong": vong, "ket_qua": kq, "lich_su": lich_su},
                               ensure_ascii=False, indent=2), encoding="utf-8")
                gom_de_xuat(ten, kq)
                print(f"  XONG sau {vong} vong: {kq.get('tom_tat','')}")
                print(f"    p(theo nhom)={kq.get('p_theo_nhom', float('nan')):.4f}  "
                      f"nhom duong {kq.get('nhom_duong','?')}/{kq.get('so_nhom','?')}")
                return kq
            loi = loi or (kq or {}).get("loi", "?")
            print(f"    hong: {str(loi)[:160]}")

        lich_su[-1]["loi"] = str(loi)[:2500]
        tn += [{"role": "assistant", "content": tra_loi},
               {"role": "user", "content":
                f"Code hong. Loi thuc te khi chay:\n\n{str(loi)[:2500]}\n\n"
                f"Sua va tra lai TOAN BO file, van dung hop dong cu."}]

    (GHI_CHEP / f"{ten}.json").write_text(
        json.dumps({"ten": ten, "y_tuong": y_tuong, "tho": tho, "that_bai": True,
                    "lich_su": lich_su}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  THAT BAI sau {SO_VONG_SUA} vong - Claude phai soi tay")
    return None


DE_XUAT = REPORTS / "BRAIN_DE_XUAT_DS.md"


def gom_de_xuat(ten, kq):
    """Cua rieng cho y tuong cua tho. Gom lai de nguoi doc, khong tu dua vao so nao.

    Y tuong cua tho KHONG duoc tu dong thanh gia thuyet - do van la viec cua nguoi ky.
    Nhung cung khong duoc vut di: hai thu song sot cua du an deu la dang ghep dieu kien,
    va do la thu mot mo hinh doc code ca ngay de nghi ra tot hon nguoi.
    """
    dx = []
    for r in kq.get("theo_thi_truong", []):
        d = str(r.get("de_xuat", "")).strip()
        if d and d.lower() not in ("nan", "none", ""):
            dx.append((r.get("thi_truong", "?"), d))
    if not dx:
        return
    # khu trung y tuong lap lai giong nhau tren nhieu thi truong
    thay = {}
    for tt, d in dx:
        thay.setdefault(d, []).append(tt)
    cu = DE_XUAT.read_text(encoding="utf-8") if DE_XUAT.exists() else (
        "# DE XUAT TU THO (DeepSeek) - CHUA AI DUYET\n\n"
        "> Khong phai gia thuyet da dang ky. Chua ton slot FDR nao.\n"
        "> Nguoi doc chon cai nao dang test thi moi dua sang `brain_khang_dinh.py`.\n")
    moi = [f"\n## tu `{ten}` — {datetime.now():%Y-%m-%d %H:%M}\n"]
    for d, ds in thay.items():
        moi.append(f"- {d}\n  *(nay o {len(ds)} thi truong: {', '.join(ds[:6])})*")
    DE_XUAT.write_text(cu + "\n".join(moi) + "\n", encoding="utf-8")
    print(f"    + {len(thay)} de xuat rieng cua no -> {DE_XUAT.name}")


def kiem(ten):
    """In ra de Claude soi: code + ket qua + toan van hoi dap."""
    f = CO_CHE_DS / f"{ten}.py"
    g = GHI_CHEP / f"{ten}.json"
    if f.exists():
        print(f"===== CODE {f} =====\n{f.read_text(encoding='utf-8')}")
    if g.exists():
        d = json.loads(g.read_text(encoding="utf-8"))
        print(f"===== KET QUA =====\n{json.dumps(d.get('ket_qua', d), ensure_ascii=False, indent=2)[:6000]}")


# Cac khang dinh con treo trong so - moi cai mot dong y tuong cho tho
VIEC_MAC_DINH = {
    "smc_lay_thanh_khoan_hai_dau": (
        "Sau khi gia quet qua DAY 20 phien roi dong cua tro lai TREN day do, thi trong "
        "5 phien ke tiep gia di len nhieu hon binh thuong (va nguoc lai voi dinh). Do ca "
        "hai chieu, doi dau chieu ban, so voi bar ngau nhien cung so luong.", False),
    "vsa_no_khoi_luong_cuoi_xu_the": (
        "Mot bar co khoi luong cao bat thuong (z>2 so 20 phien truoc) VA bien do lon "
        "xuat hien sau mot doan tang keo dai bao hieu ket thuc doan tang: loi suat 10 "
        "phien sau am hon binh thuong.", True),
    "chu_ky_thoi_gian_lap": (
        "Khoang cach (so phien) giua cac dinh 20-phien lien tiep co cau truc lap lai: "
        "biet hai khoang truoc thi du bao duoc khoang sau tot hon la doan trung binh.", False),
    # BO "hut ve POC": tra so khang dinh truoc khi giao viec thi thay no trung
    # KD_GIA_CO_TRI_NHO, da DA_DONG_SO sau 35.932 + 12,17 trieu to hop. So dong cho
    # MUC GIA; con mo cho QUAN HE GIUA CAC CHAN. POC la muc gia -> dong that.

    "ghep_dieu_kien_quet_thanh_khoan": (
        "Do 09/08 cho thay 'quet qua dinh/day 20 phien roi dong cua tro lai' KHONG co "
        "hieu ung chung (2/7 nhom), nhung rieng DAX ra +2,6 do lech chuan. Gia thuyet "
        "moi la no la dang 'A KHI B': hieu ung chi ton tai trong mot che do nhat dinh. "
        "Hay do TUONG TAC chu khong do hieu ung chinh: chia cac lan quet theo che do "
        "(tang bien dong, gia tren hay duoi trung binh 200 phien, khoang cach toi trung "
        "binh, do rong cua bar quet), roi hoi che do nao lam hieu ung khac 0. thong_ke = "
        "chenh lech chuan hoa giua o manh nhat va o yeu nhat, voi null la hoan vi nhan "
        "che do (giu nguyen tap su kien). Canh bao: chia cang nhieu o thi cang de vo "
        "duoc mot o dep do may - hay tu phat mot cach nao do cho viec chia o, va noi ro "
        "ban phat the nao.", False),

    # --- Dot 2, nap 09/08 sau khi 4 viec dau xong ---
    # Ca ba deu ve QUAN HE GIUA CAC CHAN - khe ho ma moi cuoc quet truoc cua du an bo
    # sot vi chi quet MUC GIA. Va ca ba deu buoc phai dung bc.chan_song() nen khong
    # con cho de tu dung chan roi nhin truoc (diem mu da lo ra 3 lan lien tiep).

    "chan_giua_theo_che_do": (
        "Khang dinh 'trong 3 chan cung chieu lien tiep, chan giua khong phai ngan nhat' "
        "la khang dinh NHAT QUAN NHAT do duoc (7/7 nhom cung dau) nhung do lon ti hon: "
        "P(chan giua ngan nhat) chi lech khoang 1 diem phan tram so voi 1/3. Cau hoi: do "
        "lech ay co DON LAI o mot che do nao khong, hay rai deu? Dung bc.cac_doan() de "
        "lay cac bo ba chan cung chieu, roi chia theo che do tai luc bo ba HOAN THANH "
        "(biet_tai): bien dong cao/thap, trong hay nguoc xu the dai han, chan dau dai hay "
        "ngan bat thuong. Phat da phep thu giong cach ban da lam o "
        "ghep_dieu_kien_quet_thanh_khoan - cach do dung.", False),

    "luan_phien_doc_lap": (
        "Do doc lap khang dinh 'hai dot dieu chinh lien tiep co hinh dang doi lap (nhon "
        "<-> phang)'. DUNG doc cach lam cua ai, tu chon cach dinh nghia 'hinh dang' cua "
        "ban. Canh bao da tra gia: neu do hinh dang bang do doc THO thi 28/28 thi truong "
        "ra ket qua nguoc, nhung do la bien dong cum lai gia dang - hai doan canh nhau "
        "nam cung che do vol nen tu dong giong nhau. Phai khu thanh phan do truoc. "
        "Ket qua doi chieu se so voi mot phep do khac da co; hai cach doc lap cung ket "
        "luan thi dang tin hon nhieu so voi mot cach.", False),

    "chan_dai_bat_thuong_thi_sao": (
        "Khang dinh chua ai quet: sau mot chan DAI BAT THUONG (do dai chuan hoa theo bien "
        "do duong nhien nam o phan vi cao), chan cung chieu KE TIEP co ngan hon binh "
        "thuong khong - tuc do dai chan co hoi quy ve trung binh? Va loi suat 10 phien "
        "sau khi chan dai do duoc XAC NHAN xong co khac binh thuong khong? Day la quan he "
        "giua cac chan, khac han moi thu du an da dong so (deu la MUC GIA). Dung "
        "bc.chan_song()/bc.cac_doan() de co san cot `biet_tai`.", False),

    "chuoi_5_chan_do_phan_giai": (
        "Khang dinh 'chuoi 5 chan khac chuoi 3 chan ve thong ke' KHONG DO DUOC o khung "
        "ngay voi zigzag nguong 3xATR - so lan cham toi chan thu 5 duoi 15 o hau het thi "
        "truong. Nhiem vu cua ban gom hai phan: (1) tu chon cach dinh nghia chan sao cho "
        "co du su kien de do ma van NHAN QUA (chan chi duoc dung sau khi da xac nhan); "
        "(2) do xem sau khi hoan thanh chan thu 5 thi loi suat 10 phien ke tiep co khac "
        "voi sau chan thu 3 khong. Neu ban ket luan la khong the do duoc mot cach trung "
        "thuc o khung ngay, hay noi ro vi sao - ket luan do cung co gia tri.", False),
}


# ---------------------------------------------------------------------------
# CHE DO TU SINH - tang kham pha chay khong nguoi truc
# ---------------------------------------------------------------------------

SO_TU_SINH = REPORTS / "BRAIN_TU_SINH.md"
DEM_PHEP_THU = REPORTS / "BRAIN_dem_phep_thu.json"

DE_NGHI = """Ban dang lam viec o TANG KHAM PHA cua mot he nghien cuu dinh luong. Nhiem
vu bay gio KHONG phai viet code - ma la NGHI RA MOT KHANG DINH MOI dang do.

Khang dinh phai:
- NGUYEN TU: mot cau, bac bo duoc bang so lieu gia OHLCV khung ngay.
- CHUA CO TRONG SO duoi day (doc ky truoc khi de nghi).
- KHONG thuoc hai ho da dong so cua du an: "xu huong / momentum" va "moc gia / cau
  truc" (muc gia, ho tro-khang cu, Fibonacci, order block, volume profile POC). Hai ho
  nay da bi dot 35.932 + 12,17 trieu to hop, 0 song sot. Nhung chu y RANH GIOI: dong
  cho MUC GIA, KHONG dong cho QUAN HE giua cac chan song.
- Tot nhat la dang GHEP CO DIEU KIEN ("A khi B"). Bang chung: ca hai thu duy nhat song
  sot cua du an nay deu co dang do, khong cai nao la nhan to don.

{so_khang_dinh}

DA THU O TANG NAY (dung de nghi lai):
{da_thu}

Tra ve DUNG dinh dang nay, khong them gi:
TEN: <ten_khong_dau_gach_duoi_ngan_gon>
KHANG_DINH: <mot den ba cau, noi ro do cai gi va dau nao la ung ho>
VI_SAO: <mot cau: co che kinh te / ai bi ep lam gi, khong duoc noi "vi bieu do cho thay">
CAN_KHOI_LUONG: <co hoac khong>
"""


def _dem_phep_thu(them=0):
    d = {"so_phep_thu_tang_1": 0, "tu": datetime.now().date().isoformat()}
    if DEM_PHEP_THU.exists():
        try:
            d = json.loads(DEM_PHEP_THU.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    if them:
        d["so_phep_thu_tang_1"] = d.get("so_phep_thu_tang_1", 0) + them
        d["cap_nhat"] = datetime.now().isoformat(timespec="seconds")
        DEM_PHEP_THU.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return d.get("so_phep_thu_tang_1", 0)


def _boi_canh_so():
    p = HERE / "reports" / "BRAIN_KHANG_DINH.md"
    return ("SO KHANG DINH HIEN CO:\n" + p.read_text(encoding="utf-8")[:4000]) if p.exists() else ""


def _da_thu():
    ds = sorted(f.stem for f in GHI_CHEP.glob("*.json"))
    return "\n".join(f"- {t}" for t in ds) or "(chua co)"


def _rut_de_nghi(s):
    ra = {}
    for dong in s.splitlines():
        for k in ("TEN", "KHANG_DINH", "VI_SAO", "CAN_KHOI_LUONG"):
            if dong.strip().upper().startswith(k + ":"):
                ra[k] = dong.split(":", 1)[1].strip()
    ten = re.sub(r"[^a-z0-9_]", "", ra.get("TEN", "").lower().replace(" ", "_").replace("-", "_"))
    if not ten or not ra.get("KHANG_DINH"):
        return None
    return {"ten": ten[:60], "khang_dinh": ra["KHANG_DINH"],
            "vi_sao": ra.get("VI_SAO", ""),
            "can_kl": ra.get("CAN_KHOI_LUONG", "").lower().startswith("c")}


def tu_sinh(so_vong=20, gio=3.0, tho=0):
    """Vong kham pha khong nguoi truc: tu de nghi khang dinh -> tu do -> ghi so.

    KY LUAT VAN GIU NGUYEN: van chay tren TAP SANG, van gop theo nhom tuong quan, van
    phai co null tu than. Cai duy nhat duoc noi la NGUON y tuong.
    Va moi phep thu deu duoc DEM. Tang 1 khong ton ngan sach FDR (do la ca kien truc),
    nhung khi mot khang dinh duoc mang len tang xac nhan thi phai biet no la lan boc
    tham thu bao nhieu - neu khong thi cai bo dem mat nghia va he tu lua chinh minh.
    """
    het = time.time() + gio * 3600
    for vong in range(1, so_vong + 1):
        if time.time() > het:
            print(f"\n[tho {tho}] het gio ({gio}h)"); break
        print(f"\n[tho {tho}] ###### VONG {vong}/{so_vong} ######", flush=True)

        # Uu tien y tuong RUT TU TAI LIEU THAT. Chi khi het hang moi tu bia ra -
        # mot khang dinh co nguoi da nghi ky va viet ra giay thi tien nghiem cao hon
        # han mot khang dinh mo hinh nghi ra trong ba giay.
        dn = _lay_ung_vien()
        if dn:
            print(f"  (lay tu hang ung vien rut tu nguon)")
        else:
            try:
                tl = goi([{"role": "user", "content": DE_NGHI.format(
                    so_khang_dinh=_boi_canh_so(), da_thu=_da_thu())}], nhiet=0.9)
            except Exception as e:
                print(f"  loi goi API: {e}"); time.sleep(30); continue
            dn = _rut_de_nghi(tl)
        if not dn:
            print("  khong rut duoc de nghi dung dinh dang, bo qua vong nay"); continue
        if (GHI_CHEP / f"{dn['ten']}.json").exists():
            print(f"  '{dn['ten']}' da thu roi, bo qua"); continue

        print(f"  DE NGHI: {dn['ten']}")
        print(f"    {dn['khang_dinh']}")
        print(f"    vi sao: {dn['vi_sao']}")

        # BOC KIN. Truoc day `lam()` nem loi thi ca vong tu sinh chet cung - vong lap
        # khong nguoi truc thi MOT loi khong duoc phep giet ca ca dem chay.
        try:
            kq = lam(dn["ten"], dn["khang_dinh"] + "\n\nCo che de nghi: " + dn["vi_sao"],
                     dn["can_kl"], tho)
        except Exception as e:
            import traceback
            with open(REPORTS / f"ds/_su_co_tho{tho}.log", "a", encoding="utf-8") as g:
                g.write(f"\n=== {datetime.now():%Y-%m-%d %H:%M:%S} {dn['ten']} ===\n"
                        + traceback.format_exc())
            print(f"  SU CO: {str(e)[:120]} (da ghi log, di tiep sau 60s)")
            time.sleep(60)
            kq = None
        tong = _dem_phep_thu(1)

        with open(SO_TU_SINH, "a", encoding="utf-8") as f:
            if f.tell() == 0:
                f.write("# THE BRAIN - tang kham pha tu sinh\n\n"
                        "> Ket qua o day KHONG PHAI edge. Tang 1, khong cong nao, khong ton\n"
                        "> slot FDR. Cot `phep thu so` la de khi mot khang dinh duoc mang len\n"
                        "> tang xac nhan thi con biet no la lan boc tham thu bao nhieu.\n\n"
                        "| phep thu so | ten | nhom duong | z trung vi | p theo nhom | khang dinh |\n"
                        "|---|---|---|---|---|---|\n")
            # `lam()` tra ve dict cua _ds_chay.py (khoa `trung_vi`), KHONG phai dict cua
            # do_ic() (khoa `ic`). Viet nham `ic` lam ca hai tho chet dung o buoc GHI SO -
            # tuc do xong roi mat ket qua. Loi thu ba cung dang trong ngay: duong THAT BAI
            # duoc thu ky, duong THANH CONG thi khong.
            if kq:
                f.write(f"| {tong} | `{dn['ten']}` | {kq.get('nhom_duong','?')}/"
                        f"{kq.get('so_nhom','?')} | {kq.get('trung_vi', float('nan')):+.3f} | "
                        f"{kq.get('p_theo_nhom', float('nan')):.4f} | {dn['khang_dinh'][:150]} |\n")
            else:
                f.write(f"| {tong} | `{dn['ten']}` | HONG | - | - | {dn['khang_dinh'][:150]} |\n")

        print(f"  (tong phep thu tang 1 tu truoc den nay: {tong})")

    print(f"\n[tho {tho}] xong. So: {SO_TU_SINH}")


# ---------------------------------------------------------------------------
# RUT KHANG DINH TU NGUON DA THU THAP
# ---------------------------------------------------------------------------
# Vong lap 24/7 gom duoc 162 muc (arXiv, GitHub, HuggingFace) nhung KHONG AI DOC.
# Chung chi nam do de dem so. Do la cho nghen that: khau lay du lieu chay tot, khau
# CHUYEN HOA thi chua ton tai. Them nguon nua chi lam dong do to hon.

UNG_VIEN = REPORTS / "BRAIN_UNG_VIEN_KHANG_DINH.md"
DA_DOC = REPORTS / "ds" / "_da_doc_nguon.json"
HANG_UNG_VIEN = REPORTS / "ds" / "_ung_vien.json"

DOC_NGUON = """Duoi day la mot so muc vua thu thap duoc (bai bao, kho code, mo hinh).
Viec cua ban: xem tung muc co chua KHANG DINH NGUYEN TU nao dang do khong.

Khang dinh nguyen tu = mot cau, bac bo duoc bang so lieu gia OHLCV khung ngay cua 28
thi truong (chi so ngoai My, hang hoa, FX major). Khong co du lieu khac.

BO QUA muc nao roi vao cac truong hop sau (noi ngan gon la bo qua, dung co ep):
- Chi la cong cu / thu vien / mo hinh, khong chua khang dinh ve HANH VI GIA.
- Can du lieu ta khong co (so lenh, tin tuc, bao cao tai chinh, du lieu tick, on-chain).
- Rut ve ho "xu huong / momentum" hoac "moc gia / cau truc" - hai ho nay du an da dot
  35.932 + 12,17 trieu to hop, 0 song sot. RANH GIOI: dong cho MUC GIA, khong dong cho
  QUAN HE giua cac chan song.
- Trung voi khang dinh da co trong so (xem duoi).

{so_khang_dinh}

CAC MUC CAN XEM:
{cac_muc}

Tra ve, MOI MUC MOT KHOI, khong them loi giai thich nao khac:
### <so thu tu muc>
TEN: <ten_khong_dau_gach_duoi>  (hoac de trong neu bo qua)
KHANG_DINH: <mot den ba cau, noi ro do cai gi va dau nao la ung ho>
VI_SAO: <co che kinh te: ai bi ep lam gi>
CAN_KHOI_LUONG: <co / khong>
BO_QUA: <de trong, hoac mot cau ly do neu bo qua>
"""


def _tai_json(p, mac_dinh):
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return mac_dinh


def rut_khang_dinh(so_muc=40, moi_lo=5):
    """Doc so NGUON + CONG NGHE -> de nghi khang dinh -> hang ung vien."""
    import pandas as pd

    da_doc = set(_tai_json(DA_DOC, []))
    hang = _tai_json(HANG_UNG_VIEN, [])
    ten_da_co = {h["ten"] for h in hang} | {f.stem for f in GHI_CHEP.glob("*.json")}

    muc = []
    for f, loai in [(REPORTS / "BRAIN_nguon.parquet", "nguon"),
                    (REPORTS / "BRAIN_cong_nghe.parquet", "cong_nghe")]:
        if not f.exists():
            continue
        d = pd.read_parquet(f)
        for _, r in d.iterrows():
            khoa = f"{r.get('nguon','')}|{r.get('ten','')}"[:200]
            if khoa in da_doc:
                continue
            muc.append({"khoa": khoa, "nguon": str(r.get("nguon", "")),
                        "ten": str(r.get("ten", ""))[:200],
                        "tom_tat": str(r.get("tom_tat", ""))[:700],
                        "link": str(r.get("link", ""))[:200]})
    if not muc:
        print("Khong con muc nao chua doc."); return
    muc = muc[:so_muc]
    print(f"Con {len(muc)} muc chua doc (xu ly {moi_lo} muc moi lan goi).\n")

    boi_canh = _boi_canh_so()
    for i in range(0, len(muc), moi_lo):
        lo = muc[i:i + moi_lo]
        mo_ta = "\n\n".join(
            f"### {j+1}\nNguon: {m['nguon']}\nTen: {m['ten']}\nTom tat: {m['tom_tat']}"
            for j, m in enumerate(lo))
        print(f"  lo {i//moi_lo + 1}: {len(lo)} muc ...", flush=True)
        try:
            tl = goi([{"role": "user", "content": DOC_NGUON.format(
                so_khang_dinh=boi_canh, cac_muc=mo_ta)}], nhiet=0.5)
        except Exception as e:
            print(f"    loi API: {str(e)[:100]}"); continue

        moi = 0
        for khoi in re.split(r"^###\s*", tl, flags=re.M)[1:]:
            dn = _rut_de_nghi(khoi)
            bo = re.search(r"^BO_QUA:\s*(.+)$", khoi, re.M)
            if bo and bo.group(1).strip() and bo.group(1).strip() != "-":
                continue
            if not dn or dn["ten"] in ten_da_co:
                continue
            dn["tu_nguon"] = lo[0]["nguon"]
            hang.append(dn); ten_da_co.add(dn["ten"]); moi += 1
        for m in lo:
            da_doc.add(m["khoa"])
        print(f"    -> {moi} ung vien moi")

        HANG_UNG_VIEN.write_text(json.dumps(hang, ensure_ascii=False, indent=2), encoding="utf-8")
        DA_DOC.write_text(json.dumps(sorted(da_doc), ensure_ascii=False), encoding="utf-8")

    md = ["# UNG VIEN KHANG DINH rut tu nguon da thu thap", "",
          f"*Cap nhat {datetime.now():%Y-%m-%d %H:%M}. {len(hang)} ung vien dang cho do.*", "",
          "> Chua ai duyet, chua ton slot FDR nao. Vong tu sinh se lay tu day truoc khi",
          "> tu nghi ra khang dinh moi - y tuong tu tai lieu that dang gia hon y tuong bia.", "",
          "| ten | khang dinh | co che |", "|---|---|---|"]
    for h in hang:
        md.append(f"| `{h['ten']}` | {h['khang_dinh'][:180]} | {h.get('vi_sao','')[:120]} |")
    UNG_VIEN.write_text("\n".join(md), encoding="utf-8")
    print(f"\nTong {len(hang)} ung vien -> {UNG_VIEN.name}")


def _lay_ung_vien():
    """Vong tu sinh uu tien y tuong RUT TU TAI LIEU THAT truoc khi tu bia ra."""
    hang = _tai_json(HANG_UNG_VIEN, [])
    while hang:
        dn = hang.pop(0)
        HANG_UNG_VIEN.write_text(json.dumps(hang, ensure_ascii=False, indent=2), encoding="utf-8")
        if not (GHI_CHEP / f"{dn['ten']}.json").exists():
            return dn
    return None


def ban_bac(duong_dan, ra=None, tiep=None):
    """Hoi DeepSeek mot cau hoi THIET KE (khong phai do luong) va luu tra loi.

    Khac `lam()`: o day khong doi code chay duoc, ma doi mot BAN DE XUAT KIEN TRUC.
    Vai tro: no de xuat, Claude phan bien va hoan thien. Hai dau nhanh hon mot dau.
    """
    noi_dung = Path(duong_dan).read_text(encoding="utf-8")
    tn = []
    if tiep and Path(tiep).exists():
        cu = Path(tiep).read_text(encoding="utf-8")
        tn = [{"role": "user", "content": "Boi canh vong truoc:"},
              {"role": "assistant", "content": cu[-12000:]}]
    tn.append({"role": "user", "content": noi_dung})

    print(f"Gui de bai thiet ke ({len(noi_dung)} ky tu) ...", flush=True)
    tl = goi(tn, nhiet=0.6, toi_da_token=32000)
    ra = Path(ra or (REPORTS / "ds" / f"_banbac_{datetime.now():%m%d_%H%M}.md"))
    ra.write_text(tl, encoding="utf-8")
    print(f"Tra loi {len(tl)} ky tu -> {ra}")
    return tl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thu", action="store_true")
    ap.add_argument("--lam")
    ap.add_argument("--y-tuong", default=None)
    ap.add_argument("--kiem")
    ap.add_argument("--hang-doi", action="store_true")
    ap.add_argument("--tho", type=int, default=0)
    ap.add_argument("--gop-y", default=None, help="nhan xet cua Claude, hoac @file.md")
    ap.add_argument("--tu-sinh", action="store_true", help="tu de nghi khang dinh roi tu do")
    ap.add_argument("--rut-khang-dinh", action="store_true",
                    help="doc so NGUON/CONG NGHE -> rut khang dinh dem do duoc")
    ap.add_argument("--so-muc", type=int, default=40)
    ap.add_argument("--ban-bac", default=None, help="file de bai thiet ke")
    ap.add_argument("--ra", default=None)
    ap.add_argument("--tiep-tu", default=None, help="file tra loi vong truoc lam boi canh")
    ap.add_argument("--so-vong", type=int, default=20)
    ap.add_argument("--gio", type=float, default=3.0)
    a = ap.parse_args()

    if a.thu:
        print(goi([{"role": "user", "content": "Tra loi dung mot cau: ban la mo hinh gi?"}]))
        return
    if a.kiem:
        kiem(a.kiem); return
    if a.ban_bac:
        print(ban_bac(a.ban_bac, a.ra, a.tiep_tu)); return
    if a.rut_khang_dinh:
        rut_khang_dinh(a.so_muc); return
    if a.tu_sinh:
        tu_sinh(a.so_vong, a.gio, a.tho); return
    if a.lam:
        yt = a.y_tuong or VIEC_MAC_DINH.get(a.lam, ("", False))[0]
        if not yt:
            raise SystemExit("can --y-tuong")
        kl = VIEC_MAC_DINH.get(a.lam, ("", False))[1]
        gy = a.gop_y
        if gy and gy.startswith("@"):
            gy = Path(gy[1:]).read_text(encoding="utf-8")
        lam(a.lam, yt, kl, a.tho, gy); return
    if a.hang_doi:
        # chia viec theo id tho: tho 0 lam viec 0,2,4... tho 1 lam 1,3,5...
        so_tho = int(os.environ.get("DS_SO_THO", "1"))
        ds = list(VIEC_MAC_DINH.items())
        for i, (ten, (yt, kl)) in enumerate(ds):
            if i % so_tho != a.tho:
                continue
            if (GHI_CHEP / f"{ten}.json").exists():
                print(f"[tho {a.tho}] bo qua {ten} (da co)"); continue
            lam(ten, yt, kl, a.tho)
        return
    ap.print_help()


if __name__ == "__main__":
    main()
