# -*- coding: utf-8 -*-
"""NGHI HUU 04/09/2026 - ngay trong ngay no duoc viet. Ly do la SO, khong phai
cam tinh.

Chu du an: *"doc video co le kho, chua ke ngoai phu de con can hinh anh minh
hoa, can nhac bo nhanh nay"*. Y ve HINH ANH la y quyet dinh, va toi da bo sot
no: video trading thuong hien luat TREN MAN HINH (cau hinh chi bao, moc vao
lenh, khung nen) chu khong doc thanh loi. Nen mot bo ASR hoan hao cung chi lay
duoc LOI DAN. Muon du thi phai OCR tung khung hinh + ASR + khop thoi gian - to
hon han, va do dung la thu khong nen bat dau.

SO 04/09 - PHAI DOC KY CHO NAY. Bang "moi trieu ky tu" duoi day **DA BI BAC BO
ngay trong cung ngay**: mau so dem trung (bang `artifact` loai `document` la ban
sao cua `noi_dung`), chia ca ton kho chua doc, va gop `.mq5` voi bai viet
mql5.com lam mot. Giu lai de thay lap luan goc da sai o dau.

BANG DUNG - co che tren 100 BAN DA BOC:
    tradingview 166 | youtube phu de 39 | .mq5 file 18,2
    telegram 14,8   | github 9,3        | mql5.com bai viet 5,0

Theo bang dung, ASR la **~6,4 phut CPU mot co che**, KHONG phai 53 phut.
Quyet dinh nghi huu VAN GIU, nhung ly do dung la **PHAM VI**, khong phai kinh te:
phu de tu dong da phu 97% (3/115 video thieu), va luat trong video trading nam
TREN MAN HINH chu khong doc thanh loi.

Bang cu (da bac bo, giu de doi chieu):

    tradingview   133 co che / 1,80 trieu ky tu  ->  73,7
    pdf             6 /  0,13                    ->  44,6
    telegram       10 /  1,07                    ->   9,4
    youtube        16 /  2,91                    ->   5,5
    mql5           25 /  9,25                    ->   2,7
    blog           42 / 41,42                    ->   1,0
    github         30 / 174,27                   ->   0,2

Doc bang nay cho hai ket luan khac nhau, va khong duoc tron:

  1. **PHU DE thi GIU.** 5,5 co che/trieu la muc GIUA - hon mql5 (2,7) va hon
     blog (1,0). Va phu de la MIEN PHI: `toan_van.tu_youtube` khong ton mot
     giay CPU nao. Duong do van chay, khong dung gi ca.

  2. **ASR thi BO.** Do that: 150 giay CPU cho mot video 8 phut ra ~8.600 ky
     tu. O suat 5,5/trieu, do la **0,047 co che mot video**, tuc khoang **53
     phut CPU cho MOT co che**. Cung 53 phut do dat vao tradingview (73,7)
     cho gap hang chuc lan.

Va them: goi tu vung sua duoc CHINH TA NGANH ("bot truyen dinh tren san OK" ->
"Bot trading tren san OKX") nhung KHONG sua duoc do chinh xac chung ("Diem" thay
vi "Kiem", "voi so 4 chi" thay vi "voi so von chi"). Luat giao dich song bang
CON SO va NGUONG - dung cho `small` con yeu nhat. Diem dau hieu luat khong doi:
1 truoc va 1 sau.

DIEU KIEN HOI SINH - viet ra de lan sau khong phai cai lai tu dau:
  - co GPU (ASR nhanh len ~10 lan, thi 5 phut CPU/co che, khac han), HOAC
  - kho kenh Viet KHONG PHU DE lon len den muc bo lo dang ke (hom nay: 3/115),
    HOAC
  - co bo doc KHUNG HINH, vi luc do video moi cho duoc cai no thuc su giau -
    cau hinh chi bao tren man hinh.

File giu nguyen, chay duoc, da co test. Khong xoa - xoa thi lan sau lai mat mot
buoi do lai chinh nhung con so tren.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import time
from pathlib import Path

#: Kho tam cho tieng tai ve + cache model. Dat tren F: vi C: dang o ~13 GB, va
#: `dia_va_tick_test` la mot van de DANG MO: duoi 15 GB thi buoc kiem dinh
#: tick that tren MT5 bi khoa. Mot bo thu thap khong duoc lam nang them mot
#: van de dang mo.
KHO_TAM = Path(r"F:\brain_data\tieng")

#: Model. `small` la diem can cho tieng Viet: `base` sai dau nhieu, `medium`
#: gap 3 lan thoi gian tren CPU. `int8` de chay duoc tren CPU khong AVX512.
MODEL = "small"
NEN = "int8"

#: Tran do dai video. Mot video 3 gio tren CPU la hang gio ASR - khong dang cho
#: mot ban doc. Video dai hon thi bo qua va ghi ly do.
TRAN_GIAY = 3600

#: GOI TU VUNG bom vao bo giai ma. Whisper nhan `initial_prompt` nhu van canh,
#: nen mot danh sach thuat ngu keo no ve dung chinh ta cua nganh.
#:
#: DO DUOC 04/09/2026 tren cung mot video (8 phut, tieng Viet):
#:   khong goi : "bot truyen dinh tren san OK"      (bot trading tren san OKX)
#:   co goi    : "Bot trading tren san OKX"          DUNG
#: Danh tu rieng va ten chi bao duoc sua han. Nhung tieng Viet THUONG thi
#: khong: "Diem 50 do" (dung: "Kiem"), "voi so 4 chi" (dung: "voi so von chi").
#: Va **diem dau hieu luat khong doi: 1 truoc va 1 sau**.
#:
#: Ket luan phai giu cho ngay thang: goi tu vung sua CHINH TA NGANH, khong sua
#: DO CHINH XAC CHUNG. Luat giao dich song bang CON SO va NGUONG, ma do dung la
#: cho `small` con yeu. Nen ban doc tu duong nay la ban doc HANG HAI.
GOI_TU_VUNG = (
    "Bot trading, sàn OKX, Binance, MT5, MetaTrader, chỉ báo RSI, EMA, SMA, "
    "MACD, Bollinger, Ichimoku, ATR, khung H1 H4 D1 M15, vào lệnh, cắt lỗ, "
    "chốt lời, đòn bẩy, vốn, lot, pip, spread, DCA, backtest, chiến lược, "
    "kháng cự, hỗ trợ, xu hướng, đảo chiều."
)

_MODEL = None


def _model():
    global _MODEL
    if _MODEL is None:
        os.environ.setdefault("HF_HOME", str(KHO_TAM / "hf"))
        # BAY WINDOWS: huggingface_hub tao SYMLINK trong cache, va Windows doi
        # quyen dac biet cho symlink (`OSError [WinError 1314] A required
        # privilege is not held by the client`). Loi hien ra o giua mot vet
        # goi 40 dong cua `hf_hub_download`, khong lien quan gi den ASR, nen
        # rat de doc nham thanh "model hong".
        #
        # Tat symlink thi hub chep file that. Ton them cho nhung khong doi
        # quyen quan tri, va may nay chay duoi tai khoan thuong.
        os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
        os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
        from faster_whisper import WhisperModel
        _MODEL = WhisperModel(MODEL, device="cpu", compute_type=NEN,
                              download_root=str(KHO_TAM / "hf"))
    return _MODEL


def ma_video(url: str) -> str | None:
    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{6,})", url or "")
    return m.group(1) if m else None


def tai_tieng(url: str, thu_muc: Path, tran_giay: int = TRAN_GIAY) -> dict:
    """Tai RIENG duong tieng cua video. Khong tai hinh - hinh la 95% dung luong."""
    import yt_dlp
    thu_muc.mkdir(parents=True, exist_ok=True)
    ra = {"url": url}
    cau_hinh = {
        "format": "bestaudio/best",
        "outtmpl": str(thu_muc / "%(id)s.%(ext)s"),
        "quiet": True, "no_warnings": True, "noprogress": True,
        # KHONG hau ky: khong doi dinh dang, khong nhung thumbnail. `av` doc
        # duoc m4a/webm truc tiep, nen moi buoc chuyen ma la thoi gian vut di.
        "postprocessors": [],
    }
    try:
        with yt_dlp.YoutubeDL(cau_hinh) as y:
            tt = y.extract_info(url, download=False)
            ra["ten"] = tt.get("title")
            ra["giay"] = tt.get("duration")
            if (tt.get("duration") or 0) > tran_giay:
                ra["bo_qua"] = f"video dai {tt['duration']}s > tran {tran_giay}s"
                return ra
            tt = y.extract_info(url, download=True)
            ra["duong"] = y.prepare_filename(tt)
    except Exception as e:
        ra["loi"] = f"{type(e).__name__}: {str(e)[:120]}"
    return ra


def nghe(duong: str, ngon_ngu: str | None = None) -> dict:
    """Mot file tieng -> chu. `ngon_ngu=None` de model tu nhan."""
    t0 = time.time()
    doan, tt = _model().transcribe(duong, language=ngon_ngu, beam_size=1,
                                   vad_filter=True, initial_prompt=GOI_TU_VUNG)
    van = " ".join(d.text.strip() for d in doan).strip()
    return {"van_ban": van, "ngon_ngu": tt.language,
            "do_tin_ngon_ngu": round(float(tt.language_probability or 0), 3),
            "giay": round(time.time() - t0, 1), "ky_tu": len(van)}


def tu_video(url: str, ngon_ngu: str | None = None, giu_tieng: bool = False,
             in_ra=None) -> dict | None:
    """Video KHONG co phu de -> ban doc, cung hinh dang `toan_van.tu_youtube`.

    Tra `None` khi khong lam duoc - de nguoi goi phan biet voi ban doc rong.
    """
    vid = ma_video(url)
    if not vid:
        return None
    tam = KHO_TAM / vid
    try:
        t = tai_tieng(url, tam)
        if t.get("loi") or t.get("bo_qua") or not t.get("duong"):
            if in_ra:
                in_ra(f"  {vid}: {t.get('loi') or t.get('bo_qua')}")
            return None
        kq = nghe(t["duong"], ngon_ngu)
        if len(kq["van_ban"]) < 400:
            return None
        if in_ra:
            in_ra(f"  {vid}: {kq['ky_tu']:,} ky tu, {kq['giay']:.0f}s, "
                  f"tieng={kq['ngon_ngu']} ({kq['do_tin_ngon_ngu']})")
        return {"van_ban": kq["van_ban"], "kieu": "video",
                "cach": f"asr_whisper:{vid}",
                "ghi_chu": {"ngon_ngu": kq["ngon_ngu"],
                            "do_tin": kq["do_tin_ngon_ngu"],
                            "giay_asr": kq["giay"], "ten": t.get("ten"),
                            "giay_video": t.get("giay")}}
    finally:
        # Tieng da nghe xong thi khong con gia tri - xoa ngay. Giu lai thi kho
        # tam phinh len hang GB va lam nang `dia_va_tick_test`.
        if not giu_tieng:
            shutil.rmtree(tam, ignore_errors=True)


def doc_video(url: str, in_ra=None) -> dict | None:
    """DUONG DAY DU va DUNG THU TU: phu de that truoc, ASR sau.

    Day la ham nen goi tu ben ngoai, khong phai `tu_video`.
    """
    from nhan import toan_van as TV
    kq = TV.tu_youtube(url)
    if kq:
        return kq
    return tu_video(url, in_ra=in_ra)
