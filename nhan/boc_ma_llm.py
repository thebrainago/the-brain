# -*- coding: utf-8 -*-
"""boc_ma_llm.py - BOC CO CHE tu ma nguon EA: regex khoanh vung, LLM dich.

Chu du an 05/09/2026: *"khi nao ty le chuyen doi tu dau vao cho den ra hoan
thien la chien luoc giao dich ro rang hon 70% moi la tam chap nhan"*.

## VI SAO CAN CA HAI, KHONG CHI MOT

Do duoc 05/09 tren 389 file `.mq5`, sau BON lan va `doc_ma.py`:

    ban dau                          0 file nhan ra lenh vao
    + cu phap MQL5 vao `_VAO_LENH`   113 file (29%)
    + bo qua `if` kiem loi           113 file, 0 co che
    + lan qua ranh gioi ham          113 file, 0 co che
    + tu vung gia/ham MQL5           113 file, 0 co che

Moi lan va lai lo ra mot tang sau hon: dieu kien phan nhanh -> bien cuc bo ->
`if` don dep -> bieu thuc so hoc long nhau. **Regex sai cong cu** cho viec dich
MQL5 tuy y sang mot DSL ngu nghia.

Nhung bon lan va do KHONG bo di: chung cho ta **vung lenh vao** - ten ham bao,
guard tho, cac dong gan bien quanh do. Do la mot doan ~40 dong thay vi mot file
50.000 ky tu. LLM dich mot doan nho thi re va dung; nem ca file thi dat va lac.

## RANG BUOC KHONG DUOC PHA

Moi khai bao LLM tra ve deu phai qua `ngu_phap.kiem_khai_bao` +
`kiem_khong_nhin_truoc` truoc khi vao kho. **Khong `exec` ma LLM sinh.** LLM chi
duoc dien vao mot SCHEMA co san - no khong duoc tao ra chi bao moi.
"""
from __future__ import annotations

import concurrent.futures as _cf
import json
import re

# 3.200 ky tu du cho file vua, nhung file >40k (EquityGuardPanel, Frontend,
# breakrevertpro...) bi cat mat dieu kien. Do 05/09: 4/33 file khong chuyen doi
# duoc roi vao dung nhom nay. Nang len 8.000 - van re so voi ca file 50k.
MAX_VUNG = 8000
LUONG = 6


def vung_vao_lenh(src: str, so_vung: int = 2) -> list[str]:
    """Khoanh cac VUNG quanh lenh vao. Dung chinh bo tim cua `doc_ma`."""
    from nhan import doc_ma as DM
    vb = DM._chuan_hoa(src)
    L = vb.splitlines(keepends=True)
    dau = []
    p = 0
    for l in L:
        dau.append(p)
        p += len(l)
    ra = []
    for m in DM._VAO_LENH.finditer(vb):
        i = max(k for k, x in enumerate(dau) if x <= m.start())
        # 30 dong ngay tren lenh vao thuong la doan DIEN LENH (`request.tp=`,
        # `OrderCheck`, `GetFillType`) - khong phai dieu kien. Do 05/09: vung
        # lay ra toan boilerplate, LLM khong co gi de doc.
        # Lay CA HAI: doan quanh lenh, VA doan quanh cho GOI ham bao no.
        ra.append("".join(L[max(0, i - 12):min(len(L), i + 3)])[:1200])
        ten_ham = DM._ham_bao(vb, m.start())
        if ten_ham:
            for vt in DM._cho_goi(vb, ten_ham, m.start())[:2]:
                k = max(kk for kk, xx in enumerate(dau) if xx <= vt)
                ra.append("".join(L[max(0, k - 22):min(len(L), k + 3)])[:1600])
        if len(ra) >= so_vung + 2:
            break
    ra = ra[:so_vung + 2]
    ra += _ngu_canh_bien("".join(ra), L, dau)
    return ra


#: Bien la BIEN CUC BO cua EA (khong phai ham chuan MQL5).
_RX_BIEN = re.compile(r"\b(g_\w+|[a-z]\w*_\w+|\w*[Hh]igh\w*|\w*[Ll]ow\w*)\b")
_BO_QUA_BIEN = {"iHigh", "iLow", "prev_high", "prev_low", "high", "low"}


def _ngu_canh_bien(vung: str, L: list, dau: list, toi_da: int = 6) -> list[str]:
    """Cac dong GAN cac bien xuat hien trong vung. LLM khong doan duoc
    `g_ORB_High` la gi neu khong thay dong tinh no."""
    ten = []
    for m in _RX_BIEN.finditer(vung):
        t = m.group(1)
        if t in _BO_QUA_BIEN or t in ten:
            continue
        ten.append(t)
        if len(ten) >= toi_da:
            break
    if not ten:
        return []
    ra = []
    for t in ten:
        rx = re.compile(r"^[ \t]*(?:\w+[ \t]+)?" + re.escape(t) +
                        r"[ \t]*(?:=|\+=)[^=]", re.M)
        for i, ln in enumerate(L):
            if rx.match(ln):
                ra.append("".join(L[max(0, i - 3):min(len(L), i + 2)])[:420])
                break
    return ra[:toi_da]


def _nhac(ten: str, vung: list[str], ngu_phap_tom_tat: str) -> str:
    return f"""Day la vung VAO LENH rut tu mot Expert Advisor MQL5 (`{ten}`).
Nhiem vu: doc dieu kien VAO LENH that su va dien vao schema JSON duoi.

{ngu_phap_tom_tat}

QUY TAC:
- Chi lay dieu kien QUYET DINH VAO LENH. BO QUA: kiem loi (`if(!OrderSend)`),
  chon chieu (`if(type==ORDER_TYPE_BUY)`), kiem margin, kiem gio/spread.
- LAY HET dieu kien doc duoc. Bien the duoc hoan nghenh - chong trung la viec
  cua he, khong phai viec cua ban. (Ban truoc dat cau "khong dien duoc thi tra
  ve rong" ngay trong loi nhac va nhan 0/20: bo loc nam TRONG loi nhac thi mo
  hinh im truoc khi co gi de loc.)
- Ve nao that su khong dien duoc thi ghi vao "khong_dien_dat_duoc", VAN tra ve
  cac ve con lai.
- `chieu`: 1 neu la lenh MUA, -1 neu BAN.
- Chu ky chi bao phai la SO CU THE.
- Neu mot bien nhu `g_ORB_High` la "cao nhat cua N bar gan day" thi dich thanh
  {{"chi_bao":"cao_nhat","cua":{{"chi_bao":"gia","cot":"high"}},"n":N}}. Phan
  "CHO GAN BIEN" duoi day cho biet cac bien do duoc tinh the nao.

VUNG MA (vung dau: quanh lenh vao · vung sau: cho GOI ham · cuoi: CHO GAN BIEN):
```
{chr(10).join(vung)[:MAX_VUNG]}
```

Tra ve DUNG mot JSON: {{"co_che": [{{"ten": "...", "ho": "...", "chieu": 1,
"giu": 1, "vao": [{{"trai": {{...}}, "phep": "<", "phai": {{...}}}}]}}]}}"""


def _mot(d: dict, tom_tat: str) -> dict:
    from nhan import tri_tue as TT
    vung = vung_vao_lenh(d["src"])
    if not vung:
        return {"ten": d["ten"], "co_che": [], "vi_sao": "khong khoanh duoc vung"}
    try:
        # `tri_tue` co phanh 600 giay/luot cho duong hoi thuong. Duong BOC co
        # han muc RIENG - `boc_llm._mot_ban` goi voi `bo_qua_han_muc=True`.
        # Quen cho nay thi 20 luot song song deu nhan
        # `{"bo_qua": "moi goi 103s truoc, can cach 600s"}` va ra 0/20 (do 05/09).
        r = TT.hoi_json(_nhac(d["ten"], vung, tom_tat),
                        bo_qua_han_muc=True, dung_cache=False)
    except Exception as e:
        return {"ten": d["ten"], "co_che": [],
                "vi_sao": "%s: %s" % (type(e).__name__, str(e)[:60])}
    # `hoi_json` tra `{"loi": ...}` chu KHONG nem ngoai le khi goi hong. Khong
    # tach ra thi mot me het quota chay 2 giay va bao "0/20 file ra co che" -
    # doc y het mot ket qua am that (do 05/09, [[ket-luan-am-phai-phan-biet-chua-do]]).
    if isinstance(r, dict) and r.get("loi"):
        return {"ten": d["ten"], "co_che": [], "chua_do": True,
                "vi_sao": "CHUA DO - %s" % str(r["loi"])[:90]}
    j = (r or {}).get("json") or r or {}
    cc = j.get("co_che") or []
    return {"ten": d["ten"], "co_che": cc, "chua_do": False,
            "vi_sao": "" if cc else "LLM tra ve rong"}


def mot_file(d: dict, tom_tat: str, so_lan: int = 2) -> dict:
    """Boc MOT file, thu lai toi da `so_lan` neu tra rong.

    LLM khong tat dinh: do 05/09, ba file ra co che o me 15 lai tra rong o me 45
    du khong doi mot ky tu nao. Mot lan rong khong phai ket luan.

    Nhung mot lan `chua_do` (quota/mang) THI la ket luan - thu lai chi ton thoi
    gian de ra cung con so 0.
    """
    cuoi = {"ten": d["ten"], "co_che": [], "vi_sao": "chua chay"}
    for _ in range(max(1, so_lan)):
        cuoi = _mot(d, tom_tat)
        if cuoi["co_che"] or cuoi.get("chua_do"):
            return cuoi
    return cuoi


def kiem_va_giu(cc: list[dict], nguon: str = "") -> tuple[list[dict], list[str]]:
    """Moi khai bao phai qua `ngu_phap.kiem_khai_bao`. Khong qua thi BO."""
    from nhan import ngu_phap as NP
    giu, ho = [], []
    for c in cc:
        # LLM doi khi tra `co_che: ["mua khi rsi < 30"]` - danh sach CHUOI.
        # Bo qua yen lang thay vi nem loi lam mat ca me (da sap 05/09).
        if not isinstance(c, dict):
            ho.append("khong phai dict: %s" % str(c)[:40])
            continue
        # HO `khac` KHONG DUOC VAO KHO.
        #
        # `doc_ma.doc_ma` da bo ho nay tu 01/09 voi ly do da viet ra: moi ho
        # phai khai duoc PHAM VI ("chay o lop tai san nao, hong o lop nao, vi
        # sao" - `nhan/pham_vi.py`), va mot dieu kien khong goi ten duoc co che
        # kinh te thi khong co co so de doi hoi phep thu phan chung cho no.
        # Duong LLM khong ap luat do, nen me 05/09 dua **61 co che ho `khac`**
        # vao kho va lam do bai `test_moi_ho_trong_thu_vien_mau_deu_da_khai_pham_vi`.
        # Chan o day - cho ca hai duong boc dung chung ham nay.
        # Danh sach ho hop le lay THANG tu `pham_vi.PHAM_VI` chu khong viet
        # cung o day: bai kiem `test_moi_ho_trong_thu_vien_mau_deu_da_khai_pham_vi`
        # so voi dung bang do, nen hai noi phai la MOT nguon. Me 05/09 con de
        # LLM tu che ra ho `khong_dien_dat_duoc` - mot ho khong ai khai bao.
        from nhan import pham_vi as _PV
        if str(c.get("ho") or "").strip() not in _PV.PHAM_VI:
            ho.append("%s: ho '%s' chua khai pham vi"
                      % (str(c.get("ten", "?"))[:26], str(c.get("ho"))[:18]))
            continue
        c.setdefault("nguon", nguon)
        c.setdefault("giu", 1)
        try:
            bao = NP.kiem_khai_bao(c) if hasattr(NP, "kiem_khai_bao") else {"dat": True}
        except Exception as e:
            ho.append("%s: %s" % (c.get("ten", "?"), str(e)[:50]))
            continue
        if isinstance(bao, dict) and bao.get("dat") is False:
            ho.append("%s: %s" % (c.get("ten", "?"), str(bao.get("ly_do"))[:50]))
            continue
        giu.append(c)
    return giu, ho


def moi(so_file: int = 20, in_ra=print) -> dict:
    """TEST MOI: chay tren mot mau nho de DO SUAT truoc khi chay het.

    Chu du an: *"test nen co test moi truoc khi test that de do ton thoi gian"*.
    """
    from nhan import boc_llm as BL
    from nhan import so as SO

    tom_tat = BL._ngu_phap_tom_tat()
    r = SO.nhieu("SELECT id,payload FROM artifact WHERE artifact_type='code'")
    ds = []
    for x in r:
        try:
            p = json.loads(x["payload"])
        except Exception:
            continue
        con = p.get("payload") or p
        src = con.get("content") or ""
        if not isinstance(src, str) or len(src) < 200:
            continue
        if not vung_vao_lenh(src):
            continue                       # khong co lenh vao -> khong goi LLM
        ds.append({"ten": str(con.get("ten") or con.get("path") or x["id"]),
                   "src": src, "id": x["id"]})
        if len(ds) >= so_file:
            break
    in_ra("TEST MOI tren %d file co lenh vao" % len(ds))
    ket = []
    with _cf.ThreadPoolExecutor(max_workers=LUONG) as ex:
        for z in ex.map(lambda d: mot_file(d, tom_tat, so_lan=2), ds):
            ket.append(z)
    co = [k for k in ket if k["co_che"]]
    tong_cc = sum(len(k["co_che"]) for k in ket)
    in_ra("  LLM tra ve co che : %d/%d file (%.0f%%), %d khai bao"
          % (len(co), len(ds), 100 * len(co) / max(len(ds), 1), tong_cc))
    giu_tong, ho_tong = [], []
    for k in ket:
        g, h = kiem_va_giu(k["co_che"], nguon=k["ten"])
        giu_tong += g
        ho_tong += h
    in_ra("  qua KIEM KHAI BAO : %d/%d khai bao" % (len(giu_tong), tong_cc))
    if ho_tong:
        in_ra("  bi loai: " + "; ".join(ho_tong[:4]))
    from collections import Counter
    vs = Counter(k["vi_sao"] for k in ket if not k["co_che"])
    for k, v in vs.most_common(4):
        in_ra("  khong ra: %-40s %d" % (k[:40], v))
    return {"so_file": len(ds), "ra_co_che": len(co), "khai_bao": tong_cc,
            "qua_kiem": len(giu_tong), "ket": ket}



def chay_that(gioi_han: int = 0, so_lan: int = 2, ghi_kho: bool = True,
              in_ra=print) -> dict:
    """Chay tren TOAN BO file co lenh vao, ghi khai bao dat vao kho co che.

    Khac `moi()` o hai cho: khong cat mau, va CO ghi kho. Moi khai bao van phai
    qua `kiem_va_giu` (tuc `ngu_phap.kiem_khai_bao`) truoc khi vao.
    """
    import time
    from nhan import boc_llm as BL
    from nhan import ngu_phap as NP
    from nhan import so as SO

    tom_tat = BL._ngu_phap_tom_tat()
    r = SO.nhieu("SELECT id,payload FROM artifact WHERE artifact_type='code'")
    ds = []
    for x in r:
        try:
            p = json.loads(x["payload"])
        except Exception:
            continue
        con = p.get("payload") or p
        src = con.get("content") or ""
        if not isinstance(src, str) or len(src) < 200:
            continue
        if not vung_vao_lenh(src):
            continue
        ds.append({"ten": str(con.get("ten") or con.get("path") or x["id"]),
                   "src": src, "id": x["id"]})
        if gioi_han and len(ds) >= gioi_han:
            break
    in_ra("CHAY THAT tren %d file co lenh vao (thu lai %d lan)" % (len(ds), so_lan))
    t0 = time.time()
    ket = []
    with _cf.ThreadPoolExecutor(max_workers=LUONG) as ex:
        for i, z in enumerate(
                ex.map(lambda d: mot_file(d, tom_tat, so_lan), ds), 1):
            ket.append(z)
            if i % 20 == 0:
                in_ra("  ... %d/%d (%.0fs)" % (i, len(ds), time.time() - t0))
    # GHI THO NGAY, truoc khi kiem. Mot me la ~25 phut goi API; mot loi hau ky
    # khong duoc phep lam mat no.
    try:
        import pathlib
        pathlib.Path("reports/boc_ma_llm_tho.json").write_text(
            json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")
        in_ra("  da ghi tho -> reports/boc_ma_llm_tho.json")
    except Exception as e:
        in_ra("  khong ghi duoc ban tho: %s" % str(e)[:60])

    co = [k for k in ket if k["co_che"]]
    giu, ho = [], []
    for k in ket:
        g, h = kiem_va_giu(k["co_che"], nguon=k["ten"])
        giu += g
        ho += h
    in_ra("")
    in_ra("  file ra co che   : %d/%d (%.0f%%)"
          % (len(co), len(ds), 100 * len(co) / max(len(ds), 1)))
    in_ra("  khai bao qua kiem: %d" % len(giu))
    them = 0
    if ghi_kho and giu:
        # VAO KHO BANG `them_co_che`, KHONG TU GHI.
        #
        # Ban truoc tu goi `doc_kho()` + `luu_kho()` va chi chong trung bang van
        # tay dieu kien. No bo qua `ngu_phap.them_co_che` - "cua duy nhat cho
        # kien thuc moi vao he" - nen bo qua luon ba bai kiem chi chay duoc khi
        # co DU LIEU: chay thu, ty le kich hoat, va nhin truoc.
        #
        # Gia phai tra, do 05/09: **20 spec trong kho khong chay duoc**
        # (`vao: ["khong_dien_dat_duoc"]`, thieu khoa `trai`, toan hang la chuoi,
        # doi cot `bid`/`ask`). Tat ca deu qua `kiem_khai_bao` - bai kiem TINH -
        # roi no o buoc sinh tin hieu, tuc chung nam trong kho nhu co che that
        # va duoc dem vao con so "326 co che".
        from collections import Counter as _C
        from nhan import loc_co_che as LCC
        tu_choi = _C()
        df_kiem = LCC.df_kiem_chuan()
        if df_kiem is None:
            in_ra("  !! khong nap duoc chuoi kiem - KHONG ghi kho (khong ha cong)")
        else:
            for c in giu:
                r = NP.them_co_che(c, df_kiem)
                if r.get("nhan"):
                    them += 1
                else:
                    tu_choi[str((r.get("ly_do") or ["?"])[0])[:46]] += 1
            for k, v in tu_choi.most_common(5):
                in_ra("  cong tu choi %3d: %s" % (v, k))
    in_ra("  them vao kho     : %d" % them)
    return {"so_file": len(ds), "ra_co_che": len(co), "qua_kiem": len(giu),
            "them_kho": them, "ket": ket}
