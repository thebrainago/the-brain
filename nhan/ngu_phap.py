# -*- coding: utf-8 -*-
"""ngu_phap.py - NGU PHAP CO CHE. Cach duy nhat kien thuc moi di vao day chuyen.

VAN DE NO GIAI (do tren so cai 16/08):
  SEEKER da thu 303 tai lieu, trong do 17 tai lieu HANG A mo ta co che CHUA CO
  trong `nhan/mau.py`. Van de `can_mau_moi` mo tu 15/08 va khong bao gio dong
  duoc, vi buoc "doc duoc co che -> co template kiem dinh duoc" la buoc DUY NHAT
  con phai lam bang tay. Ket qua: mot phong lab doc rat nhieu ma hoc duoc rat it.

CACH GIAI - va vi sao khong sinh MA:
  Cho LLM viet ham Python roi `exec` la mo hai cua cung luc: cua bao mat, va
  cua nhin truoc (mot dong `.shift(-1)` hay `transform("last")` la du - bay do
  da sap that ngay 15/08 trong `m_lap_gap`, cho EURCAD H1 ra CAGR 115%).
  O day co che duoc khai bao bang DU LIEU: mot cay JSON gom toan hang va phep
  so sanh. Trinh thong dich nay la thu duy nhat cham vao chuoi gia, va no
  KHONG CO toan tu nao nhin ve tuong lai. Nhin truoc tro thanh dieu KHONG PHAT
  BIEU DUOC, khong phai dieu bi cam.

HINH DANG MOT CO CHE:
    {
      "ten": "ibs_day_khi_bien_dong_cao",
      "co_che": "Mot cau ve vi sao co nguoi tra tien cho phoi nhiem nay.",
      "ho": "quay_ve_trung_binh",
      "chieu": 1,                       # 1 = mua, -1 = ban
      "giu": 1,                         # so bar giu sau khi dieu kien dung
      "vao": [                          # VA voi nhau
        {"trai": {"chi_bao": "ibs"}, "phep": "<", "phai": {"hang": 0.2}},
        {"trai": {"chi_bao": "phan_vi", "cua": {"chi_bao": "atr", "n": 14}, "n": 250},
         "phep": ">", "phai": {"hang": 0.7}}
      ],
      "ra": []                          # HOAC voi nhau; rong = het `giu` thi ra
    }

QUY UOC THOI GIAN (khong the vi pham):
  Moi toan hang chi duoc tinh tu thong tin BIET TAI CLOSE cua bar i. Trinh
  thong dich tra ve `tin_hieu[i]`; `nhan/mo_phong.py` tu dich mot bar. Khong co
  toan hang nao nhan `shift` am, va `_kiem_khong_nhin_truoc` con kiem lai bang
  thuc nghiem: doi mot gia tri o bar cuoi KHONG duoc lam doi tin hieu bar truoc.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import mau as MAU_MOD
else:
    from . import mau as MAU_MOD

LAB = Path(__file__).resolve().parent.parent
KHO_CO_CHE = LAB / "config" / "co_che_dsl.json"

PHEP = {"<", "<=", ">", ">=", "cheo_len", "cheo_xuong"}
HO_HOP_LE = {"quay_ve_trung_binh", "xu_huong", "pha_vo", "lich", "phien",
             "bien_dong", "dong_tien", "vi_mo", "khac"}


# --------------------------------------------------------------- TOAN HANG
def _cot(df: pd.DataFrame, ten: str) -> pd.Series:
    if ten not in df.columns:
        raise KeyError(f"du lieu khong co cot '{ten}'")
    return df[ten].astype(float)


def toan_hang(df: pd.DataFrame, t: dict) -> pd.Series:
    """Dich mot toan hang thanh chuoi gia tri tai tung bar.

    MOI nhanh o day chi doc qua khu va hien tai. Khong co nhanh nao dich am.
    """
    if not isinstance(t, dict):
        raise TypeError(f"toan hang phai la dict, nhan duoc {type(t).__name__}")
    if "hang" in t:
        return pd.Series(float(t["hang"]), index=df.index)

    cb = str(t.get("chi_bao", "")).lower()
    n = int(t.get("n", 14) or 14)

    if cb == "gia":
        return _cot(df, str(t.get("cot", "close")).lower())
    if cb == "rsi":
        return MAU_MOD.rsi(_cot(df, "close"), n)
    if cb == "ibs":
        return MAU_MOD.ibs(df)
    if cb == "atr":
        return MAU_MOD.atr(df, n)
    if cb == "ema":
        return MAU_MOD.ema(_cot(df, str(t.get("cot", "close")).lower()), n)
    if cb == "sma":
        return MAU_MOD.sma(_cot(df, str(t.get("cot", "close")).lower()), n)
    if cb == "bien_do":
        return _cot(df, "high") - _cot(df, "low")
    if cb == "than_nen":
        return _cot(df, "close") - _cot(df, "open")
    if cb == "khoi_luong":
        return _cot(df, "tick_volume") if "tick_volume" in df.columns \
            else pd.Series(np.nan, index=df.index)
    if cb == "gio":
        return pd.Series(df.index.hour, index=df.index, dtype=float)
    if cb == "ngay_trong_tuan":
        return pd.Series(df.index.dayofweek, index=df.index, dtype=float)
    if cb == "ngay_trong_thang":
        return pd.Series(df.index.day, index=df.index, dtype=float)
    if cb == "thang":
        return pd.Series(df.index.month, index=df.index, dtype=float)

    # --- toan tu GOP: nhan MOT DANH SACH toan hang ---
    # Them 16/08 vi tang BOC bao dung cho thieu: GMMA can
    # mean(EMA3,EMA5,EMA7,EMA10,EMA12,EMA15) vs mean(EMA30..EMA60), va no da
    # phai xap xi bang EMA9 vs EMA43 - khong tuong duong. Mot dai chi bao khong
    # phai mot chi bao trung binh: dai bo qua khi cac duong PHAN KY.
    if cb in ("tb_cua_cac", "cao_nhat_cua_cac", "thap_nhat_cua_cac", "tong_cua_cac"):
        ds = t.get("toan_hang") or []
        if not isinstance(ds, list) or not ds:
            raise KeyError(f"'{cb}' can truong 'toan_hang' la danh sach khong rong")
        khung = pd.concat([toan_hang(df, x) for x in ds[:24]], axis=1)
        if cb == "tb_cua_cac":
            return khung.mean(axis=1)
        if cb == "tong_cua_cac":
            return khung.sum(axis=1)
        return khung.max(axis=1) if cb == "cao_nhat_cua_cac" else khung.min(axis=1)

    # --- toan tu BIEN DOI: nhan mot toan hang con ---
    con = t.get("cua")
    if con is None:
        raise KeyError(f"chi bao '{cb}' khong biet, va khong co truong 'cua'")
    x = toan_hang(df, con)
    if cb == "tb":
        return x.rolling(n).mean()
    if cb == "do_lech":
        return x.rolling(n).std()
    if cb == "zscore":
        sd = x.rolling(n).std()
        return (x - x.rolling(n).mean()) / sd.replace(0, np.nan)
    if cb == "phan_vi":
        # thu hang cua gia tri HIEN TAI trong N bar GAN NHAT, ke ca bar nay.
        # Hop le: bar nay da dong. `rank(pct=True)` tren cua so truot.
        return x.rolling(n).rank(pct=True)
    if cb == "doi":
        return x.diff(n)
    if cb == "doi_pct":
        return x.pct_change(n)
    if cb == "tre":
        return x.shift(max(n, 1))          # LUI ve qua khu; n am bi chan o duoi
    if cb == "cao_nhat":
        return x.rolling(n).max()
    if cb == "thap_nhat":
        return x.rolling(n).min()
    if cb == "tuyet_doi":
        return x.abs()
    raise KeyError(f"chi bao khong biet: '{cb}'")


def _so_sanh(a: pd.Series, phep: str, b: pd.Series) -> pd.Series:
    if phep == "<":
        return a < b
    if phep == "<=":
        return a <= b
    if phep == ">":
        return a > b
    if phep == ">=":
        return a >= b
    if phep == "cheo_len":
        return (a > b) & (a.shift(1) <= b.shift(1))
    if phep == "cheo_xuong":
        return (a < b) & (a.shift(1) >= b.shift(1))
    raise KeyError(f"phep so sanh khong biet: '{phep}'")


def _dieu_kien(df: pd.DataFrame, ds: list, mac_dinh: bool) -> pd.Series:
    """Danh sach dieu kien -> chuoi bool. Rong thi tra `mac_dinh`."""
    if not ds:
        return pd.Series(mac_dinh, index=df.index)
    ra = None
    for d in ds:
        m = _so_sanh(toan_hang(df, d["trai"]), d.get("phep", ">"),
                     toan_hang(df, d["phai"]))
        m = m.fillna(False)
        ra = m if ra is None else (ra & m)
    return ra


# ------------------------------------------------------------------ KIEM TRA
def kiem_khai_bao(spec: dict) -> list[str]:
    """Kiem CU PHAP truoc khi cham vao du lieu. Tra danh sach loi (rong = dat)."""
    loi = []
    if not isinstance(spec, dict):
        return ["khai bao khong phai dict"]
    for k in ("ten", "co_che", "ho", "vao"):
        if not spec.get(k):
            loi.append(f"thieu truong bat buoc '{k}'")
    if spec.get("ho") and spec["ho"] not in HO_HOP_LE:
        loi.append(f"ho '{spec['ho']}' khong thuoc {sorted(HO_HOP_LE)}")
    if len(str(spec.get("co_che", ""))) < 25:
        loi.append("'co_che' phai la MOT CAU giai thich vi sao co nguoi tra tien "
                   "cho phoi nhiem nay - man hinh duyet doc cau nay, khong doc tham so")
    if spec.get("chieu") not in (None, 1, -1):
        loi.append("'chieu' chi duoc la 1 hoac -1")
    giu = spec.get("giu", 1)
    if not isinstance(giu, int) or not (1 <= giu <= 500):
        loi.append("'giu' phai la so nguyen 1..500")
    for nhom in ("vao", "ra"):
        for i, d in enumerate(spec.get(nhom) or []):
            if not isinstance(d, dict) or "trai" not in d or "phai" not in d:
                loi.append(f"{nhom}[{i}] phai co 'trai' va 'phai'")
                continue
            if d.get("phep", ">") not in PHEP:
                loi.append(f"{nhom}[{i}] phep '{d.get('phep')}' khong hop le")
            for ben in ("trai", "phai"):
                loi += [f"{nhom}[{i}].{ben}: {e}" for e in _kiem_toan_hang(d[ben])]
    return loi


def _kiem_toan_hang(t, sau: int = 0) -> list[str]:
    if sau > 6:
        return ["toan hang long qua sau (> 6 tang)"]
    if not isinstance(t, dict):
        return ["toan hang phai la dict"]
    if "hang" in t:
        return [] if isinstance(t["hang"], (int, float)) else ["'hang' phai la so"]
    if "toan_hang" in t:
        ds = t["toan_hang"]
        if not isinstance(ds, list) or not ds:
            return ["'toan_hang' phai la danh sach khong rong"]
        if len(ds) > 24:
            return ["'toan_hang' qua 24 phan tu"]
        loi = []
        for x in ds:
            loi += _kiem_toan_hang(x, sau + 1)
        return loi
    if "n" in t:
        try:
            n = int(t["n"])
        except Exception:
            return ["'n' phai la so nguyen"]
        if n < 0:
            # Chan duy nhat can thiet cho nhin truoc: moi cua so deu lui ve qua khu.
            return ["'n' AM = nhin ve tuong lai - khong phat bieu duoc trong ngu phap nay"]
        if n > 5000:
            return ["'n' > 5000 bar"]
    return _kiem_toan_hang(t["cua"], sau + 1) if "cua" in t else []


def kiem_khong_nhin_truoc(spec: dict, df: pd.DataFrame, k: int = 5) -> tuple[bool, str]:
    """Kiem THUC NGHIEM bang PHEP CAT: tin hieu tai bar t phai GIONG HET du ta
    co biet cac bar sau t hay khong.

    Kiem cu phap da chan `n` am, nhung mot chi bao moi them sau nay co the lam
    ro ri ma cu phap khong thay. Bai kiem nay khong phu thuoc vao danh sach
    chi bao - no do TRIEU CHUNG, khong do nguyen nhan.

    Hai cach lam nhieu DA THU VA DA TRUOT truoc khi den cach nay (16/08), giu
    lai day vi ca hai deu "co ve dung":
      1. Nhan bon cot cua bar cuoi voi 1,5 - IBS la TY LE trong bar nen nhan deu
         ca bon cot khong lam IBS doi mot ly nao. Bay khong he rung.
      2. Pha hinh dang 5 bar cuoi - chi ~5 bar bi anh huong, va neu dieu kien
         thu hai cua co che tinh co sai o dung may bar do thi tin hieu khong
         doi, bay van khong rung. Do nhay phu thuoc vao du lieu = khong dung duoc.
    Phep CAT thi khong the truot: neu tin hieu dung point-in-time thi hai ben
    bang nhau THEO DINH NGHIA; lech mot moc la du ket toi.
    """
    if len(df) < 300:
        return True, "khong du bar de kiem"
    day_du = sinh_tu_spec(spec, df)
    rng = np.random.default_rng(20260816)
    diem = sorted(set(int(x) for x in rng.integers(len(df) // 3, len(df) - 2, size=40)))
    lech, vi_du = 0, []
    for t in diem:
        cat = sinh_tu_spec(spec, df.iloc[: t + 1])       # chi biet den bar t
        if abs(float(cat[-1]) - float(day_du[t])) > 1e-12:
            lech += 1
            if len(vi_du) < 3:
                vi_du.append(f"bar {t} ({str(df.index[t])[:16]}): "
                             f"cat={float(cat[-1]):+.3f} vs day_du={float(day_du[t]):+.3f}")
    if lech:
        return False, (f"{lech}/{len(diem)} moc: tin hieu tai bar t DOI khi biet them "
                       "bar sau t - co NHIN TRUOC. " + " | ".join(vi_du))
    return True, f"dat ({len(diem)} moc cat)"


# ------------------------------------------------------------------ SINH
def sinh_tu_spec(spec: dict, df: pd.DataFrame) -> np.ndarray:
    """Khai bao -> `tin_hieu[i]` = phoi nhiem mong muon biet tai close[i]."""
    chieu = float(spec.get("chieu", 1) or 1)
    giu = int(spec.get("giu", 1) or 1)
    vao = _dieu_kien(df, spec.get("vao") or [], mac_dinh=False)
    ra = _dieu_kien(df, spec.get("ra") or [], mac_dinh=False)

    v = vao.astype(float)
    if giu > 1:
        v = v.rolling(giu, min_periods=1).max()
    if (spec.get("ra") or []):
        # co dieu kien ra tuong minh: giu vi the tu luc VAO cho toi luc RA
        trang_thai = np.zeros(len(df))
        dang = 0.0
        vao_a, ra_a = vao.to_numpy(), ra.to_numpy()
        for i in range(len(df)):
            if dang and ra_a[i]:
                dang = 0.0
            elif vao_a[i]:
                dang = 1.0
            trang_thai[i] = dang
        v = pd.Series(trang_thai, index=df.index)
    return MAU_MOD._ra(v.to_numpy() * chieu, len(df))


# --------------------------------------------------------------- KHO CO CHE
_XAU = __import__("re").compile(r"[^a-z0-9_]+")


def chuan_hoa_ten(ten: str) -> str:
    """Ten co che -> chi con [a-z0-9_]. Xem ly do o `them_co_che`."""
    import unicodedata
    t = unicodedata.normalize("NFKD", str(ten or "").strip().lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = _XAU.sub("_", t).strip("_")
    while "__" in t:
        t = t.replace("__", "_")
    return t[:60]


def doc_kho() -> list[dict]:
    try:
        d = json.loads(KHO_CO_CHE.read_text(encoding="utf-8-sig"))
        return d if isinstance(d, list) else []
    except Exception:
        return []


def luu_kho(ds: list[dict]) -> None:
    KHO_CO_CHE.parent.mkdir(parents=True, exist_ok=True)
    KHO_CO_CHE.write_text(json.dumps(ds, ensure_ascii=False, indent=1), encoding="utf-8")


def van_tay_dieu_kien(spec: dict) -> str:
    """Van tay theo NOI DUNG QUYET DINH, bo qua ten va cau giai thich.

    Hai co che cung `vao`/`ra`/`chieu`/`giu` la MOT co che du dat ten khac nhau -
    va do la truong hop pho bien khi rut tu dong tu nhieu nguon noi ve cung mot
    y tuong.
    """
    return json.dumps({"vao": spec.get("vao"), "ra": spec.get("ra"),
                       "chieu": spec.get("chieu", 1), "giu": spec.get("giu", 1)},
                      sort_keys=True, ensure_ascii=False, default=str)


def them_co_che(spec: dict, df_kiem: pd.DataFrame | None = None) -> dict:
    """Them mot co che vao kho SAU KHI qua ca hai bai kiem.

    Khong dat -> KHONG vao kho, va tra ly do de tang suy nghi hoc duoc tu no.
    """
    # Chuan hoa TEN truoc moi thu. Ten di thang vao `gia_thuyet.ma` duoi dang
    # `{tai_san}.{khung}.{ten}.{tham_so}`, va sau do bi tim lai bang LIKE
    # '%.{ten}.%'. Mot cai ten nhu `sma2_cat_keo_(nhanh_tren_cham)` (tang BOC
    # sinh ra that 16/08) lam hong ca hai: dau cham/ngoac trong ten pha cach
    # tach, con `%` `_` la ky tu dai dien cua LIKE.
    spec = dict(spec)
    spec["ten"] = chuan_hoa_ten(spec.get("ten", ""))
    if not spec["ten"]:
        return {"nhan": False, "ly_do": ["ten rong sau khi chuan hoa"]}

    loi = kiem_khai_bao(spec)
    if loi:
        return {"nhan": False, "ly_do": loi[:6]}
    if df_kiem is not None:
        try:
            th = sinh_tu_spec(spec, df_kiem)
        except Exception as e:
            return {"nhan": False, "ly_do": [f"chay loi: {type(e).__name__}: {str(e)[:120]}"]}
        ty_le = float(np.mean(np.abs(th) > 1e-12))
        if ty_le < 0.002:
            return {"nhan": False, "ly_do": [f"chi kich hoat {ty_le:.3%} so bar - "
                                             "khong du lenh de kiem dinh bao gio"]}
        if ty_le > 0.98:
            return {"nhan": False, "ly_do": [f"kich hoat {ty_le:.1%} so bar - "
                                             "day la mua-giu tra hinh, khong phai co che"]}
        sach, mo_ta = kiem_khong_nhin_truoc(spec, df_kiem)
        if not sach:
            return {"nhan": False, "ly_do": [mo_ta]}
        spec = dict(spec, _ty_le_kich_hoat=round(ty_le, 4))

    kho = doc_kho()
    if any(c.get("ten") == spec["ten"] for c in kho):
        return {"nhan": False, "ly_do": [f"da co co che ten '{spec['ten']}'"]}
    # KHU TRUNG THEO DIEU KIEN, khong chi theo TEN.
    #
    # Do that 01/09: mot lo tu dong dua thu vien tu 29 len 146 co che, nhung chi
    # **81 dieu kien rieng biet** - 65 cai trung y het nhau va chi khac ten, vi
    # cung mot script duoc xu ly hai lan (mot lan luc thu thap, mot lan luc quet
    # lai kho) nen sinh ra `x_...` va `pine_x_...`. Khu trung theo ten khong bat
    # duoc, va moi ban trung se an MOT SUAT FDR rieng o tang kham pha.
    vt = van_tay_dieu_kien(spec)
    trung = next((c for c in kho if van_tay_dieu_kien(c) == vt), None)
    if trung is not None:
        return {"nhan": False,
                "ly_do": [f"trung DIEU KIEN voi co che '{trung.get('ten')}' "
                          "(chi khac ten) - mot dieu kien chi duoc mot suat FDR"]}
    kho.append(spec)
    luu_kho(kho)
    return {"nhan": True, "ten": spec["ten"], "so_co_che": len(kho)}


def nap_vao_mau() -> int:
    """Dua toan bo co che trong kho vao `MAU.MAU` de QUANTLAB quet nhu mau goc.

    Diem cot yeu: co che tu hoc KHONG co duong tat nao. No di qua dung engine,
    dung cong, dung ngan sach FDR nhu mau viet tay.
    """
    them = 0
    for spec in doc_kho():
        ten = spec.get("ten")
        if not ten or ten in MAU_MOD.MAU:
            continue

        def _ham(df, _s=spec, **_):
            return sinh_tu_spec(_s, df)

        MAU_MOD.MAU[ten] = {
            "ham": _ham, "ho": spec.get("ho", "khac"),
            "co_che": spec.get("co_che", ""),
            "nguon": spec.get("nguon", "ngu_phap"),
            "luoi": spec.get("luoi") or [{}],
            "dsl": True,
        }
        them += 1
    return them


if __name__ == "__main__":
    from nhan import du_lieu as DL
    thu = {
        "ten": "thu_ibs_bien_dong",
        "co_che": "Dong cua o day bien do khi bien dong cao: nguoi ban can thanh khoan "
                  "gap, nguoi mua duoc tra cong o phien sau.",
        "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 1,
        "vao": [{"trai": {"chi_bao": "ibs"}, "phep": "<", "phai": {"hang": 0.2}},
                {"trai": {"chi_bao": "phan_vi", "cua": {"chi_bao": "atr", "n": 14}, "n": 250},
                 "phep": ">", "phai": {"hang": 0.6}}],
    }
    print("kiem cu phap:", kiem_khai_bao(thu) or "DAT")
    df = DL.nap("EURCAD", "H4")
    th = sinh_tu_spec(thu, df)
    print(f"kich hoat {np.mean(np.abs(th) > 0):.2%} so bar tren {len(df)} bar")
    print("khong nhin truoc:", kiem_khong_nhin_truoc(thu, df))

    # BAI KIEM DO NHAY: mot bay chua tung bat duoc gi thi khong biet no co hoat
    # dong khong. Chen mot chi bao NHIN TRUOC roi xem `kiem_khong_nhin_truoc`
    # co gao len khong (cung cach `canary.tu_kiem` lam voi engine).
    goc = globals()["toan_hang"]

    def _ro_ri(d, t):
        if isinstance(t, dict) and t.get("chi_bao") == "ibs":
            return MAU_MOD.ibs(d).shift(-1)      # dung IBS cua bar KE TIEP
        return goc(d, t)

    globals()["toan_hang"] = _ro_ri
    try:
        bat = kiem_khong_nhin_truoc(thu, df)
    finally:
        globals()["toan_hang"] = goc
    print("do nhay (chen ro ri co y):", "BAT DUOC" if not bat[0] else "TRUOT - PHAI SUA",
          "|", bat[1])
