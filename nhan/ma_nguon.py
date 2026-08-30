# -*- coding: utf-8 -*-
"""MA NGUON EA / CHI BAO -> CodeArtifact.

VI SAO CAN. Cho toi 22/08/2026 SEEKER chi thu duoc VAN BAN: tieu de + tom tat
cua bai bao, bai dien dan, bai blog. Van ban mo ta co che bang tieng nguoi, va
mot mo ta bang tieng nguoi thi mo ho o dung cho quan trong nhat - "mua khi RSI
thap" khong noi nguong bao nhieu, khung nao, giu bao lau, thoat bang gi.

MA NGUON thi khong mo ho. Mot file `.mq5` noi ro nguong, khung, dieu kien vao,
dieu kien ra, va no la thu DA CHAY THAT tren MT5 cua ai do. Day la nguon co mat
do co che cao nhat ma may nay lay duoc.

BON RANG BUOC AN TOAN - **khong duoc noi long**:

1. **KHONG BAO GIO chay ma tai ve.** Khong `exec`, khong `import`, khong bien
   dich, khong dua vao MetaEditor. Ma nguon o day la VAN BAN de doc, y het mot
   bai bao. Mot dong `.shift(-1)` du de che ra CAGR 115% (da sap that 15/08);
   mot file `.mq5` la tui do cua nguoi la va no con nguy hon nhieu.

2. **Chi anh xa vao mau CO SAN** trong `nhan/mau.py`, qua
   `nhan/bien_dich_ung_vien.py`. Ma nguon duoc phep CHON mot mau da kiem duyet,
   khong duoc dinh nghia mau moi. Do do khong co duong nao de ma tren mang chen
   logic vao may.

3. **Co tran kich thuoc.** Mot file 5 MB khong phai chien luoc, no la thu vien
   dinh kem hoac binary. Doc no vao so cai chi lam phinh CSDL.

4. **Provenance day du.** `CodeArtifact` doi repository_url + revision + path,
   va do la co y: mot doan ma khong biet den tu dau thi khong doi chieu lai duoc
   khi ket qua dang ngo.
"""
from __future__ import annotations

import re
import time
from html import unescape

from nhan import hop_dong as HD
from nhan import so as SO

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TheBrainResearch/0.1"

#: Tran kich thuoc mot file ma nguon (byte). Tren muc nay gan nhu chac chan la
#: thu vien dinh kem chu khong phai mot chien luoc doc duoc.
TRAN_BYTE = 400_000
#: Duoi kich thuoc nay thi file khong du de mo ta mot co che.
SAN_BYTE = 400
#: Duoi ma nguon chap nhan. `.mqh` la header - thuong la thu vien, bo qua.
DUOI_NHAN = (".mq5", ".mq4")

_CHU_DE = {"experts": "EA", "indicators": "chi bao"}


def _lay(url: str, timeout: int = 30, nhi_phan: bool = False):
    try:
        import requests
        r = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
        if r.status_code != 200:
            return None
        return r.content if nhi_phan else r.text
    except Exception:
        return None


def _sach(s: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def liet_ke_mql5(muc: str = "experts", trang: int = 1) -> list[dict]:
    """Danh sach bai trong MQL5 Code Base. Tra [{id, url, tieu_de}].

    HREF o day la TUONG DOI (`/en/code/76331`). Regex doi href tuyet doi la loi
    da lam `tru/seeker.py::n_mql5_code` tra ve rong suot ma khong bao gi.
    """
    u = f"https://www.mql5.com/en/code/mt5/{muc}"
    if trang > 1:
        u += f"/page{trang}"
    txt = _lay(u)
    if not txt:
        return []
    ra, da = [], set()
    for m in re.finditer(
            r'href="(?:https://www\.mql5\.com)?/en/code/(\d+)"[^>]*>(.*?)</a>',
            txt, re.S | re.I):
        ma_so, tt = m.group(1), _sach(m.group(2))
        if ma_so in da or len(tt) < 8:
            continue
        da.add(ma_so)
        ra.append({"id": ma_so, "url": f"https://www.mql5.com/en/code/{ma_so}",
                   "tieu_de": tt[:250], "muc": muc})
    return ra


def tai_ma_nguon(bai: dict) -> dict | None:
    """Trang bai -> file ma nguon dau tien. Tra dict co `noi_dung`, hoac None.

    Trang bai co hai loai link tai: `/en/code/download/<id>/<ten>.mq5` (file don)
    va `/en/code/download/<id>.zip` (goi). Chi lay file don: giai nen zip cua
    nguoi la la mot be mat tan cong khong can thiet, va phan lon bai deu co san
    file don.
    """
    txt = _lay(bai["url"])
    if not txt:
        return None
    link = re.findall(r'href="(/en/code/download/\d+/[^"]+)"', txt)
    lay = next((l for l in link if l.lower().endswith(DUOI_NHAN)), None)
    if not lay:
        return None
    ten = lay.rsplit("/", 1)[-1]
    noi_dung = _lay("https://www.mql5.com" + lay, timeout=40, nhi_phan=True)
    if noi_dung is None or not (SAN_BYTE <= len(noi_dung) <= TRAN_BYTE):
        return None
    try:
        vb = noi_dung.decode("utf-8")
    except UnicodeDecodeError:
        try:
            vb = noi_dung.decode("utf-16")     # MetaEditor hay luu UTF-16
        except UnicodeDecodeError:
            return None
    if not vb.strip():
        return None
    return {**bai, "ten_file": ten, "noi_dung": vb, "so_byte": len(noi_dung)}


def thanh_artifact(bai: dict) -> HD.CodeArtifact:
    """Mot bai da tai -> CodeArtifact voi provenance day du."""
    return HD.CodeArtifact(
        source_id=f"mql5_codebase:{bai['muc']}",
        repository_url=bai["url"],
        # MQL5 khong co commit hash; so bai la dinh danh ON DINH cua ban do -
        # bai duoc sua thi tac gia dang mot bai moi voi so khac.
        revision=f"mql5-code-{bai['id']}",
        path=bai["ten_file"],
        retrieved_at=SO.bay_gio().replace(" ", "T") + "Z",
        content=bai["noi_dung"],
        language="mql5" if bai["ten_file"].lower().endswith(".mq5") else "mql4",
        license="MQL5 Code Base (xem trang goc)",
        metadata={"tieu_de": bai["tieu_de"], "muc": bai["muc"],
                  "chu_de": _CHU_DE.get(bai["muc"], bai["muc"]),
                  "so_byte": bai["so_byte"]})


def thu_thap(muc_can: tuple = ("experts", "indicators"), so_bai: int = 10,
             nghi_giay: float = 1.5) -> dict:
    """Thu thap ma nguon va ghi CodeArtifact vao so cai. Tra bao cao dem duoc.

    Dem CA HAI dau: bao nhieu bai nhin thay, bao nhieu tai duoc, bao nhieu ghi
    moi. Mot ham thu thap chi bao "xong" ma khong bao ba con so do thi khong
    phan biet duoc "nguon rong" voi "bo phan tich hong" - va do dung la cach
    `n_mql5_code` chet im lang trong sau ngay.
    """
    bao = {"nhin_thay": 0, "tai_duoc": 0, "ghi_moi": 0, "trung": 0,
           "bo_qua": [], "bai": []}
    for muc in muc_can:
        ds = liet_ke_mql5(muc)
        bao["nhin_thay"] += len(ds)
        for bai in ds[:so_bai]:
            time.sleep(nghi_giay)
            day_du = tai_ma_nguon(bai)
            if not day_du:
                bao["bo_qua"].append(f"{bai['id']}: khong co file don hop le")
                continue
            bao["tai_duoc"] += 1
            try:
                _id, moi = SO.them_artifact(thanh_artifact(day_du))
            except HD.ContractError as e:
                bao["bo_qua"].append(f"{bai['id']}: hop dong tu choi - {str(e)[:70]}")
                continue
            bao["ghi_moi"] += int(moi)
            bao["trung"] += int(not moi)
            bao["bai"].append({"id": bai["id"], "tieu_de": bai["tieu_de"][:70],
                               "url": bai["url"], "file": day_du["ten_file"],
                               "byte": day_du["so_byte"], "moi": bool(moi),
                               # giu tam de `_bao_mau_con_thieu` doc; bi loai
                               # khoi bao cao ghi so ngay sau do.
                               "_noi_dung": day_du["noi_dung"]})
    _bao_mau_con_thieu(bao)
    for b in bao["bai"]:
        b.pop("_noi_dung", None)          # khong doc ca file ma nguon vao so cai
    SO.ghi_chi_so("ma_nguon_ghi_moi", float(bao["ghi_moi"]),
                  {k: v for k, v in bao.items() if k != "bai"})
    return bao


def _bao_mau_con_thieu(bao: dict) -> None:
    """File LA CHIEN LUOC that nhung khong mau nao trong thu vien goi ten duoc.

    Day la con so co gia tri nhat cua ca buoc thu thap, va no de bi nuot nhat:
    mot file bi bo qua vi "khong khop" tron lan ba truong hop khac han nhau -
    (a) tien ich, khong phai chien luoc; (b) chi bao ve duong, khong dat lenh;
    (c) **chien luoc that, dat lenh that, nhung co che cua no CHUA CO template**.

    Chi (c) la viec phai lam. Gop ba loai vao mot con so "22 file khong khop"
    thi khong ai biet nen them template nao - va do dung la cach mot he thong
    hoc duoc bien thanh mot he thong ban ron.
    """
    try:
        from nhan import bien_dich_ung_vien as BD
    except Exception:
        return
    chien_luoc_la = []
    dem = {"chien_luoc": 0, "tien_ich": 0, "chi_bao": 0, "da_co_mau": 0}
    for b in bao.get("bai", []):
        noi_dung = b.get("_noi_dung")
        if not noi_dung:
            continue
        # Ranh gioi la MO VI THE MOI, khong phai "co nhac den giao dich":
        # `CTrade trade;` co trong moi tien ich quan ly lenh (xem
        # `bien_dich_ung_vien.loai_ma_nguon`).
        loai = BD.loai_ma_nguon(noi_dung)
        b["loai_ma"] = loai
        dem[loai] += 1
        if loai != "chien_luoc":
            continue                      # (a) tien ich hoac (b) chi bao
        if BD.do_khop(noi_dung, che_do="ma_nguon"):
            dem["da_co_mau"] += 1
            continue                      # da co template
        chien_luoc_la.append({"tieu_de": b["tieu_de"], "url": b.get("url", ""),
                              "file": b["file"]})
    bao["theo_loai"] = dem
    bao["chien_luoc_chua_co_mau"] = [x["tieu_de"] for x in chien_luoc_la]
    if chien_luoc_la:
        SO.bao_van_de(
            "can_mau_moi_tu_ma_nguon", "VUA",
            f"{len(chien_luoc_la)} file .mq5 DAT LENH THAT nhung co che cua chung "
            "chua co template trong nhan/mau.py - QUANTLAB khong kiem dinh duoc "
            "cho toi khi them template",
            {"file": chien_luoc_la[:12]})
    else:
        SO.dong_van_de("can_mau_moi_tu_ma_nguon",
                       "moi chien luoc thu duoc deu co template tuong ung")


if __name__ == "__main__":
    import json
    SO.khoi_tao()
    r = thu_thap(so_bai=3)
    print(json.dumps(r, ensure_ascii=False, indent=1)[:3000])
