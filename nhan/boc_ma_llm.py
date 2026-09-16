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
#
# NANG TIEP LEN 16.000 (05/09, toi). Ly do do duoc: trong 17 loi giai thich
# `khong_dien_dat_duoc` ma mo hinh tra ve, **10 cai noi "doan ma duoc cung cap
# khong chua dieu kien vao lenh"** - tuc mat mat nam o khau KHOANH VUNG chu
# khong o ngu phap. Va mo rong vung gan nhu mien phi: gia cua `qwen3.7-flash`
# la 0,010 cho token VAO so voi 0,040 cho token RA, con do dai dau ra khong doi
# theo do dai dau vao.
MAX_VUNG = 16000
LUONG = 6


def vung_vao_lenh(src: str, so_vung: int = 5) -> list[str]:
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
- **Du lieu CHI CO nam cot: open, high, low, close, volume.** KHONG co `bid`,
  `ask`, `spread`, `tick`, so lenh, hay do sau thi truong. EA co doc bid/ask thi
  dich sang `close` (hoac bo ve do neu no that su can chenh bid-ask). Do 16/09:
  19 khai bao bi bo chi vi goi cot `bid`/`ask` khong ton tai.
- Neu mot bien nhu `g_ORB_High` la "cao nhat cua N bar gan day" thi dich thanh
  {{"chi_bao":"cao_nhat","cua":{{"chi_bao":"gia","cot":"high"}},"n":N}}. Phan
  "CHO GAN BIEN" duoi day cho biet cac bien do duoc tinh the nao.

VUNG MA (vung dau: quanh lenh vao · vung sau: cho GOI ham · cuoi: CHO GAN BIEN):
```
{chr(10).join(vung)[:MAX_VUNG]}
```

- Moi muc PHAI co truong `co_che`: MOT CAU (>= 25 ky tu) noi VI SAO co nguoi
  tra tien cho phoi nhiem nay - ai la ben doi ung va vi sao ho buoc phai giao
  dich o trang thai do. **Khong dien lai chinh luat** ("mua khi RSI thap vi RSI
  thap"): neu ban khong biet ly do kinh te thi ghi dung chuoi
  "CHUA_BIET_LY_DO" va he se tu ghi chu, dung bia mot cau nghe hop ly.

Tra ve DUNG mot JSON: {{"co_che": [{{"ten": "...", "ho": "...", "chieu": 1,
"giu": 1, "co_che": "...", "vao": [{{"trai": {{...}}, "phep": "<",
"phai": {{...}}}}]}}]}}"""


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
                        bo_qua_han_muc=True, dung_cache=False,
                        model=d.get("_model") or "")
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


def _nhac_sua(ten: str, khai_bao: dict, loi: list[str]) -> str:
    """Loi nhac SUA: dua lai chinh khai bao + danh sach loi cua bo kiem."""
    return f"""Khai bao JSON duoi day duoc rut tu EA `{ten}`, nhung bo kiem cu
phap cua he **tu choi** no. Sua lai cho dat, giu nguyen Y NGHIA co che.

KHAI BAO BI TU CHOI:
```json
{json.dumps(khai_bao, ensure_ascii=False, indent=1)[:4000]}
```

BO KIEM BAO:
{chr(10).join("- " + str(x)[:160] for x in loi[:12])}

QUY TAC SUA:
- **Khong duoc doi co che.** `cheo_len` van la `cheo_len`, chu ky van la chu ky do.
  Neu de dat ma phai doi y nghia thi DUNG sua - tra ve {{"co_che": []}}.
- Dieu kien nao bi bao la suy bien ("hai ve giong het", "luon dung") thi **BO han
  ve do**, dung vien mot ve khac thay cho no.
- Ve nao ban khong doc duoc tu ma nguon thi BO, dung bia.
- Truong `co_che` BEN TRONG moi muc phai la MOT CAU noi VI SAO co nguoi tra tien
  cho phoi nhiem nay. Neu ban khong biet ly do kinh te that thi ghi dung chuoi
  "CHUA_BIET_LY_DO". **Day la mot CAU nam trong muc, khong phai ca cau tra loi.**

Tra ve DUNG mot JSON co dang nay, khoa ngoai cung ten la `ban_sua`:

{{"ban_sua": [{{"ten": "...", "ho": "...", "chieu": 1, "giu": 1,
"co_che": "mot cau ly do kinh te", "vao": [{{"trai": {{...}}, "phep": "<",
"phai": {{...}}}}]}}]}}"""


def sua_bang_llm(ten: str, khai_bao: dict, loi: list[str],
                 model: str = "") -> tuple[dict | None, str]:
    """Mot luot LLM de SUA khai bao bi cong tu choi. -> (ban sua | None, ly do)

    ## Vi sao dang gia

    Do 16/09 tren me 12 file: `mot_file` chi thu lai khi ket qua **RONG**. Khai
    bao bi cong tu choi thi bi bo im lang, va mo hinh **khong bao gio biet no
    sai cho nao**. Ca me ra `them vao kho: 0` trong khi 26/30 loi la hinh thuc.

    Tien le nam ngay trong file nay: me 05/09 cung `them vao kho 0` cho 80/80
    khai bao, va sua duoc bang cach **xin them mot truong trong loi nhac**. Day
    la cung mot bai hoc, dung o khau sau.

    ## Rang buoc

    Ban sua **van phai qua `kiem_khai_bao`** nhu moi khai bao khac - ham nay
    khong duoc phep dua thang vao kho. Va no chi duoc goi MOT lan cho moi khai
    bao: mot vong sua khong gioi han la mot cach dat tien de mo hinh lan dan
    quanh mot co che no khong doc noi.
    """
    from nhan import tri_tue as TT
    try:
        r = TT.hoi_json(_nhac_sua(ten, khai_bao, loi),
                        bo_qua_han_muc=True, dung_cache=False, model=model)
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, str(e)[:60])
    if isinstance(r, dict) and r.get("loi"):
        return None, "CHUA DO - %s" % str(r["loi"])[:80]
    j = (r or {}).get("json") or r or {}
    # DOC `ban_sua` TRUOC, roi moi lui ve `co_che`.
    #
    # Do 16/09: vong sua dau tien them dung SO 0 (6/19 -> 6/19), va log chi ra
    # nguyen nhan la **dung ten khoa cho hai thu**. `co_che` vua la ten DANH
    # SACH co che, vua la ten truong LY DO KINH TE ben trong moi co che. Loi
    # nhac sua nhac manh luat cua truong ben trong, nen mo hinh tra
    # `{"co_che": ["Nha dau tu chap nhan rui ro..."]}` - dung mot danh sach
    # CHUOI ly do, mat sach cau truc.
    #
    # Doi khoa ngoai cung thanh `ban_sua` de hai thu khong con trung ten. Van
    # nhan `co_che` de khong vo neu mo hinh tra theo thoi quen cu.
    cc = j.get("ban_sua") or j.get("co_che") or []
    if isinstance(cc, dict):
        cc = [cc]
    if not cc:
        return None, "mo hinh tra rong (khong sua duoc ma khong doi y nghia)"
    # `co_che` co the la danh sach CHUOI - mo hinh mo ta bang loi thay vi dien
    # schema. `kiem_va_giu` da chan hinh dang do o dau vao chinh, nhung duong
    # SUA di vong qua cho do nen phai chan lai o day (sap that 16/09:
    # `AttributeError: 'str' object has no attribute 'get'`).
    ds = [x for x in cc if isinstance(x, dict)]
    if not ds:
        return None, "ban sua khong phai dict: %s" % str(cc[0])[:50]
    return ds[0], ""


def mot_file(d: dict, tom_tat: str, so_lan: int = 2) -> dict:
    """Boc MOT file, thu lai toi da `so_lan` neu tra rong.

    LLM khong tat dinh: do 05/09, ba file ra co che o me 15 lai tra rong o me 45
    du khong doi mot ky tu nao. Mot lan rong khong phai ket luan.

    Nhung mot lan `chua_do` (quota/mang) THI la ket luan - thu lai chi ton thoi
    gian de ra cung con so 0.
    """
    from nhan import doc_chi_bao as DC          # dung chung cau hinh hai tang
    cuoi = {"ten": d["ten"], "co_che": [], "vi_sao": "chua chay"}
    for _ in range(max(1, so_lan)):
        cuoi = _mot(dict(d, _model=DC.MODEL_TANG_1), tom_tat)
        if cuoi["co_che"] or cuoi.get("chua_do"):
            return cuoi
    if DC.MODEL_TANG_2:
        z = _mot(dict(d, _model=DC.MODEL_TANG_2), tom_tat)
        if z["co_che"]:
            z["model_tang_2"] = DC.MODEL_TANG_2
            return z
    return cuoi


def _dien_co_che(c: dict, nguon: str) -> None:
    """Dam bao co truong `co_che` — mot cau cho NGUOI DUYET doc.

    `ngu_phap.kiem_khai_bao` doi truong nay dai >= 25 ky tu: *"mot cau giai
    thich vi sao co nguoi tra tien cho phoi nhiem nay - man hinh duyet doc cau
    nay, khong doc tham so"*. Do 05/09: loi nhac cua ca hai duong boc **khong he
    xin truong do**, nen 80/80 khai bao cua me lan chien luoc bi cong tu choi va
    ket qua la `them vao kho: 0` du 64/82 file ra co che.

    KHONG BIA MOT LY LE NGHE HOP LY. Neu mo hinh khong noi duoc thi dien dung
    cau noi rang no CHUA co lap luan kinh te - do la cach kho hien tai dang ghi
    cho co che rut tu tai lieu, va nguoi duyet doc phat hien ra ngay. Mot cau
    bia tron tru con te hon truong bo trong: no lam co che trong nhu da co ly do.
    """
    cu = str(c.get("co_che") or "").strip()
    if len(cu) >= 25:
        return
    if cu.upper().replace(" ", "_") == "CHUA_BIET_LY_DO":
        cu = ""                     # mo hinh da noi thang la khong biet
    ten = str(c.get("ten") or "?")
    # Danh dau de nguoi duyet loc duoc: cau nay do MAY dien, khong phai mot lap
    # luan kinh te ai do da nghi ra.
    c["_ly_do_may_dien"] = True
    c["co_che"] = ("Luat rut TU MA NGUON `%s` (%s), CHUA co lap luan kinh te: "
                   "gia thuyet nay kiem chinh dieu kien do co duoc tra tien hay "
                   "khong, khong kiem cai bot goc.%s"
                   % (nguon or "?", ten, (" Mo hinh ghi: " + cu) if cu else ""))


def _bo_dau(s: str) -> str:
    """'quay_ve_trung_bình' -> 'quay_ve_trung_binh'. Khong doi gi khac."""
    import unicodedata
    t = unicodedata.normalize("NFD", str(s))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return t.replace("đ", "d").replace("Đ", "D")


def sua_may_moc(c: dict) -> tuple[dict, list[str]]:
    """Sua nhung cho SAI HINH THUC, khong dung den LLM. -> (ban sua, da sua gi)

    ## Vi sao co ham nay

    Do 16/09 tren me 12 file lan CHIEN_LUOC: 9/12 file ra co che, 19 khai bao,
    **vao kho 0**. Doc ly do nguyen van thi 26/30 loi la HINH THUC chu khong
    phai sai y. Lon nhat la mot loi **dau tieng Viet**:

        ho 'xu_hướng' khong thuoc [... 'xu_huong' ...]
        ho 'quay_ve_trung_bình' khong thuoc [...]
        ho 'pha_vào' khong thuoc [...]

    Mo hinh doc dung co che va goi dung ten ho - chi go co dau. Bo mot khai bao
    dung vi mot dau sac la lang phi dat nhat trong ca day chuyen: file da tai
    ve, da khoanh vung, da ton mot luot LLM.

    KHONG sua gi thuoc ve NOI DUNG. `cheo_len` khong duoc doi thanh `cheo_xuong`,
    dieu kien suy bien khong duoc "sua" cho het suy bien - nhung cai do phai bi
    tu choi. Ham nay chi chuan hoa CACH VIET.
    """
    from nhan import pham_vi as PV
    da = []
    c = json.loads(json.dumps(c, ensure_ascii=False))     # khong sua ban goc

    # 1. Ten ho: khop lai theo ban da bo dau.
    ho = c.get("ho")
    if isinstance(ho, str) and ho not in PV.PHAM_VI:
        goc = {_bo_dau(k).lower(): k for k in PV.PHAM_VI}
        k = goc.get(_bo_dau(ho).lower())
        if k:
            c["ho"] = k
            da.append("ho %r -> %r" % (ho, k))

    # 2. `co_che` phai la MOT CAU. Mo hinh hay viet ca doan.
    cq = c.get("co_che")
    if isinstance(cq, list):
        cq = " ".join(str(x) for x in cq)
        da.append("co_che: danh sach -> chuoi")
    if isinstance(cq, str):
        cau = re.split(r"(?<=[.!?])\s+", cq.strip())
        if len(cau) > 1:
            cq = cau[0].strip()
            da.append("co_che: giu cau dau")
        if cq != c.get("co_che"):
            c["co_che"] = cq

    # 3. Bo VE KHONG DOC DUOC, nhung DANH DAU khai bao la khong day du.
    #
    # Mo hinh chen thang chuoi `khong_dien_dat_duoc` vao `vao` cho phan no
    # khong doc noi. Do 16/09: mot khai bao co 5 ve, **4 ve dau hoan chinh**,
    # ve thu 5 la chuoi do - va ca khai bao bi bo.
    #
    # Bo ve do thi 4 ve kia dung duoc. NHUNG co che con lai **khong con la co
    # che trong ma nguon**: no thieu mot dieu kien. Nen phai gan `khong_day_du`
    # va so ve da mat, de khong ai doc ket qua cua no nhu mot ban boc trung
    # thanh. Im lang bo ve roi coi nhu day du la cach tot nhat de sinh ra mot
    # "phat hien" ve mot co che chua ai tung viet.
    ve = c.get("vao")
    if isinstance(ve, list):
        sach = [x for x in ve if isinstance(x, dict)]
        if len(sach) != len(ve):
            if sach:
                c["vao"] = sach
                c["khong_day_du"] = True
                c["so_ve_mat"] = len(ve) - len(sach)
                da.append("bo %d ve khong doc duoc -> danh dau khong_day_du"
                          % (len(ve) - len(sach)))
            else:
                da.append("moi ve deu khong doc duoc - giu nguyen de cong tu choi")

    # 4. Toan hang phai la dict; `n` phai la so nguyen.
    for i, ve in enumerate(c.get("vao") or []):
        if not isinstance(ve, dict):
            continue
        for ben in ("trai", "phai"):
            x = ve.get(ben)
            if isinstance(x, str) and x in ("open", "high", "low", "close"):
                ve[ben] = {"chi_bao": "gia", "cot": x}
                da.append("vao[%d].%s: %r -> dict gia" % (i, ben, x))
            elif isinstance(x, (int, float)):
                ve[ben] = {"so": x}
                da.append("vao[%d].%s: so -> {'so': ...}" % (i, ben))
            if isinstance(ve.get(ben), dict):
                n = ve[ben].get("n")
                if isinstance(n, float) and float(n).is_integer():
                    ve[ben]["n"] = int(n)
                    da.append("vao[%d].%s.n: %s -> %d" % (i, ben, n, int(n)))
                elif isinstance(n, str) and n.strip().isdigit():
                    ve[ben]["n"] = int(n.strip())
                    da.append("vao[%d].%s.n: chuoi -> so" % (i, ben))
    return c, da


def kiem_va_giu(cc: list[dict], nguon: str = "", sua_llm: bool = False,
                in_ra=None) -> tuple[list[dict], list[str]]:
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
        # SUA HINH THUC TRUOC KHI CHAM (16/09). Do tren me 12 file: 26/30 loi
        # la hinh thuc chu khong sai y - lon nhat la ten ho go co dau
        # (`quay_ve_trung_bình`). Bo mot khai bao dung vi mot dau sac la lang
        # phi dat nhat ca day chuyen: file da tai, da khoanh vung, da ton mot
        # luot LLM. Do duoc: qua cong 4/19 -> 6/19.
        c, _da_sua = sua_may_moc(c)
        _dien_co_che(c, nguon)
        try:
            bao = NP.kiem_khai_bao(c) if hasattr(NP, "kiem_khai_bao") else {"dat": True}
        except Exception as e:
            # NGOAI LE CUNG LA MOT LY DO TU CHOI, phai di tiep vao vong sua.
            #
            # Do tren me 374 file (16/09): 29 khai bao bi tu choi bang NGOAI LE
            # - `KeyError: du lieu khong co cot 'bid'` (10), `'ask'` (9),
            # `chi bao 'khong_dien_dat_duoc'` (6), `'macd_signal'` (4) - va
            # khong cai nao duoc thu sua, vi dong `continue` o day nhay qua ca
            # nhanh sua. Chung deu la loi CO THE NOI cho mo hinh de no sua.
            bao = ["chay loi: %s: %s" % (type(e).__name__, str(e)[:110])]
        if isinstance(bao, dict) and bao.get("dat") is False:
            bao = [str(bao.get("ly_do"))]
        if bao:
            # MOT luot sua bang LLM, va ban sua VAN phai qua chinh bo kiem nay.
            if sua_llm:
                moi, vi_sao = sua_bang_llm(c.get("ten", nguon), c, list(bao))
                if moi is not None:
                    moi, _ = sua_may_moc(moi)
                    moi.setdefault("nguon", nguon)
                    moi.setdefault("giu", 1)
                    moi["da_sua_bang_llm"] = True
                    try:
                        con = NP.kiem_khai_bao(moi)
                    except Exception as e:
                        con = [str(e)[:60]]
                    if not con:
                        giu.append(moi)
                        if in_ra:
                            in_ra("    + SUA DUOC: %s" % str(c.get("ten"))[:44])
                        continue
                    bao = con
                elif in_ra:
                    in_ra("    - khong sua duoc: %s" % vi_sao[:50])
            ho.append("%s: %s" % (c.get("ten", "?"), str(bao[0])[:50]))
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
        # `sua_llm=True` mac dinh tu 16/09. Do tren chinh 19 khai bao cua me
        # 12 file: khong sua 4 · sua may moc 6 · **co vong sua LLM 11**. Mot
        # luot sua ton ~16 giay cho moi khai bao bi tu choi - re hon han so
        # voi bo mot khai bao dung roi boc lai file tu dau.
        g, h = kiem_va_giu(k["co_che"], nguon=k["ten"], sua_llm=sua_llm,
                           in_ra=in_ra)
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
              in_ra=print, sua_llm: bool = True) -> dict:
    """Chay tren TOAN BO file co lenh vao, ghi khai bao dat vao kho co che.

    Khac `moi()` o hai cho: khong cat mau, va CO ghi kho. Moi khai bao van phai
    qua `kiem_va_giu` (tuc `ngu_phap.kiem_khai_bao`) truoc khi vao.
    """
    import time
    from nhan import boc_llm as BL
    from nhan import ngu_phap as NP
    from nhan import phan_loai_ma as PL
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
        # DINH TUYEN THEO LAN. Truoc 05/09 duong nay nhan MOI file co vung vao
        # lenh, tuc ca 48 file thuoc lan `quan_tri`. Chung khong co dieu kien
        # vao de doc, nen chung tra rong va bi dem nhu boc that bai - keo suat
        # cua lan `chien_luoc` tu 37% xuong 33%, va che mat viec chung ra spec
        # dung 90% o duong `quan_tri.boc_kho`.
        ten = str(con.get("ten") or con.get("path") or x["id"])
        if PL.phan_loai_mot(src, ten)["lan"] != PL.CHIEN_LUOC:
            continue
        ds.append({"ten": ten, "src": src, "id": x["id"]})
        if gioi_han and len(ds) >= gioi_han:
            break
    in_ra("CHAY THAT tren %d file lan CHIEN_LUOC (thu lai %d lan)"
          % (len(ds), so_lan))
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
