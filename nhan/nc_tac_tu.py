# -*- coding: utf-8 -*-
"""nc_tac_tu.py - NHA NGHIEN CUU AI: vong tu chu (Claude) nam quyen nghien cuu, The Brain la bo cong cu.

## DAO NGUOC QUYEN DIEU KHIEN (chu du an 25/09/2026)

Truoc file nay, ai quyet dinh "nghien cuu cai gi tiep theo"?

    chu du an        chat voi Claude, giao tung viec (tia lenh, nang lot, AUDCAD...)
    NHIEM_VU.json    43 viec VIET TAY, `q` chay tuan tu - qwen bi CAM chon viec
    dieu_phoi.py     5 tru chay theo DONG HO, moi tru mot kich ban co dinh
    tru NGHI         qwen-flash, 6 de xuat / 90 phut, chi thay dem PASS/FAIL

Tuc LLM duy nhat chay 24/7 la lao dong boc tach gia re, va phan NGHI cua he nam
o nguoi dung. Chu du an noi dung: nhu vay thi khong co loi the gi.

File nay dat mot vong nghien cuu CO NAM QUYEN len tren:

    doc so tay  ->  chon cau hoi  ->  dat gia thuyet  ->  thi nghiem (cong cu)
        ^                                                        |
        +------ ghi hieu biet + cau hoi moi  <-  doc ket qua  <--+

Ranh gioi giu nguyen tu `qwen/DOC_TRUOC.md`, vi no dung: **AI quyet dinh va
suy luan; CODE do va cham**. Moi con so di qua `nc_thi_nghiem` (engine, chi phi
that, cong tien, niem phong mot lan). AI khong tu viet ket qua.

## BA CACH CHAY (cung bo cong cu, cung so tay)

    chay_vong()          Claude API (goi `anthropic`), vong cong cu thu cong.
                         Can ANTHROPIC_API_KEY (hoac `ant auth login`).
    chay_claude_code()   `claude -p` headless - dung goi Claude Code chu du an
                         dang co, chi mo quyen `python b.py nc ...`.
    phien tuong tac      Claude Code dang chat: CLAUDE.md "LUAT SO 1" bao no
                         doc `b nc so-tay` va tu chay `b nc cc ...`.

Vi sao vong thu cong chu khong dung Tool Runner cua SDK: moi chu ky co NGAN
SACH cong cu va USD, het ngan sach thi phai cho AI MOT luot ghi hieu biet roi
buoc ket (tool_choice none) - va khong muon ke thuoc vao mot API beta tren may
chu du an.

## MO HINH

Mac dinh `claude-opus-5`, effort `high`, thinking adaptive, bat `fallbacks:
"default"` (server-side, beta `server-side-fallback-2026-07-01`) de mot lan bi
tu choi nham khong lam dut chu ky. Doi bang `config/nha_nghien_cuu.json` hoac
bien moi truong NC_MO_HINH / NC_EFFORT / NC_USD_NGAY / NC_CONG_CU_MOI_VONG.
"""
from __future__ import annotations

import inspect
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nhan import nc_cong_cu as CC, nc_dac_trung as DT, nc_so_tay as ST, ngu_phap as NP

LAB = Path(__file__).resolve().parent.parent
CAU_HINH = LAB / "config" / "nha_nghien_cuu.json"
THU_MUC_VONG = LAB / "reports" / "nc_vong"
CO_DUNG = LAB / "DUNG_LAI"

MAC_DINH = {
    "mo_hinh": "claude-opus-5",
    "effort": "high",
    "max_tokens": 16000,
    "cong_cu_moi_vong": 40,
    "usd_moi_vong": 6.0,
    "usd_moi_ngay": 30.0,
    "fallback": True,
    "nghi_giua_vong_giay": 120,
    "claude_code_lenh": "claude",
    "claude_code_timeout_giay": 5400,
}
#: USD / 1 trieu token (vao, ra). Doc tu bang gia hien hanh; mo hinh la -> gia Opus 5.
GIA = {"claude-opus-5": (5.0, 25.0), "claude-opus-5-5": (4.0, 20.0),
       "claude-sonnet-5": (2.0, 10.0), "claude-fable-5-1": (10.0, 50.0),
       "claude-fable-5": (10.0, 50.0), "claude-haiku-4-5": (1.0, 5.0),
       "claude-opus-4-8": (5.0, 25.0)}
BETA_FALLBACK = "server-side-fallback-2026-07-01"


def cau_hinh() -> dict:
    c = dict(MAC_DINH)
    if CAU_HINH.exists():
        try:
            c.update(json.loads(CAU_HINH.read_text(encoding="utf-8-sig")))
        except Exception:
            pass
    for k, bien, kieu in (("mo_hinh", "NC_MO_HINH", str), ("effort", "NC_EFFORT", str),
                          ("usd_moi_ngay", "NC_USD_NGAY", float),
                          ("cong_cu_moi_vong", "NC_CONG_CU_MOI_VONG", int)):
        if os.environ.get(bien):
            try:
                c[k] = kieu(os.environ[bien])
            except ValueError:
                pass
    return c


# ================================================================ HIEN CHUONG
def _ngu_phap_tom_tat() -> str:
    return """Mot co che = object JSON:
  {"ten": "chu_thuong_gach_duoi", "co_che": "MOT CAU >= 25 ky tu: AI TRA TIEN cho phoi nhiem nay va VI SAO",
   "ho": "quay_ve_trung_binh|xu_huong|pha_vo|lich|phien|bien_dong|dong_tien|vi_mo",
   "chieu": 1 (mua) | -1 (ban), "giu": so bar giu sau khi dieu kien dung (1..500),
   "vao": [dieu_kien, ...]   (VA voi nhau),  "ra": [dieu_kien, ...]  (HOAC; rong = het `giu` thi ra)}
  dieu_kien = {"trai": toan_hang, "phep": "<|<=|>|>=|==|!=|cheo_len|cheo_xuong", "phai": toan_hang}
  toan_hang:
    {"hang": so}
    {"chi_bao": "gia", "cot": "open|high|low|close|hl2|hlc3|ohlc4"}
    {"chi_bao": "rsi|atr|ema|sma|wma|smma|adx|cci|stochastic|dong_luong", "n": so}   (ema/sma/rsi nhan "cot" hoac "cua")
    {"chi_bao": "ibs"} {"chi_bao": "bien_do"} {"chi_bao": "than_nen"} {"chi_bao": "khoi_luong"}
    {"chi_bao": "gio|ngay_trong_tuan|ngay_trong_thang|thang"}   (gio chi co tren khung trong ngay)
    {"chi_bao": "bollinger|keltner", "n": 20, "k": 2, "lay": "tren|giua|duoi|do_rong|phan_tram_b"}
    {"chi_bao": "donchian", "n": 20, "lay": "tren|duoi|giua|do_rong|vi_tri"}   (kenh cua n bar TRUOC)
    {"chi_bao": "macd", "nhanh": 12, "cham": 26, "tin_hieu": 9, "lay": "macd|tin_hieu|hieu"}
    {"chi_bao": "supertrend", "n": 10, "k": 3, "lay": "chieu"}   {"chi_bao": "heiken", "lay": "chieu|than"}
    {"chi_bao": "ichimoku", "lay": "tenkan|kijun|senkou_a|senkou_b|day_may|chikou"}
    bien doi mot toan hang con qua "cua":
    {"chi_bao": "tb|do_lech|zscore|phan_vi|doi|doi_pct|tre|cao_nhat|thap_nhat|tuyet_doi|tong|lech_tb", "cua": toan_hang, "n": so}
    {"chi_bao": "tuyen_tinh", "toan_hang": [..], "he_so": [..], "cong_them": so}   (to hop tuyen tinh)
  `n` LUON lui ve qua khu; khong co cach nao viet toan hang nhin tuong lai. Dung `phan_vi`/`zscore`
  thay vi nguong tuyet doi tren dai luong co don vi gia. Nguong co don vi gia chet tren FX.
  Vi du: mua khi IBS < 0,2 VA bien dong dang cao:
   {"ten":"ibs_day_bd_cao","co_che":"...","ho":"quay_ve_trung_binh","chieu":1,"giu":1,
    "vao":[{"trai":{"chi_bao":"ibs"},"phep":"<","phai":{"hang":0.2}},
           {"trai":{"chi_bao":"phan_vi","cua":{"chi_bao":"atr","n":14},"n":250},"phep":">","phai":{"hang":0.7}}]}"""


def _dac_trung_tom_tat() -> str:
    return "\n".join("  %-10s %s  <- %s" % (t, m, json.dumps(op, separators=(",", ":")))
                     for t, (op, m, _n) in DT.DAC_TRUNG.items())


HIEN_CHUONG = """Ban la NHA NGHIEN CUU CHINH cua The Brain - phong lab tim he giao dich RA TIEN cua chu du an.
Chu du an da giao quyen: BAN quyet dinh nghien cuu cai gi, thiet ke thi nghiem, doc ket qua, rut bai
hoc va day nghien cuu toi tien. The Brain (engine, chi phi that, cong, so tay) la bo cong cu cua ban.
Chu du an la nha tai tro: dat muc tieu, gui y tuong (cau hoi nguon 'nguoi' - uu tien CAO NHAT), doc bao
cao. Khong cho ho giao viec; tu chon viec co gia tri nhat va lam.

## MUC TIEU (tieu chi chu du an, 25/09/2026)
- Nguyen van: "toi khong quan tam martingale hay dca hay la phuong phap gi. Toi trade don bay toi chap
  nhan rui ro, chi can co lai va maxdd duoi 80% la ok". Muc dich cuoi cung la TIEN (LUAT SO 0), khong
  phai chat che hoc thuat.
- He DAT = CO LAI sau moi chi phi that (spread theo gio, truot gia, phi qua dem bat doi xung) VA maxDD
  duoi 80%. `tien.cagr_duoi_tran_pct` = CAGR tot nhat voi maxDD < 80% (don bay <= 10, khong qua
  Kelly), `tien.don_bay` = don bay do. Xep va chon theo so nay; Sharpe chi la so phu.
- MOI phuong phap hop le: tin hieu vao, martingale, DCA, luoi, gong lo, nang lot, tia lenh. Dung loai
  mot huong vi "kieu martingale" - do la NHAN, khong phai ly do bac bo.
- "FX" = kieu giao dich LONG/SHORT co don bay: cap tien, chi so, hang hoa, kim loai deu duoc. Chon tai
  san theo viec no ra tien, khong theo lop.
- QUAN LI LENH quan trong hon ENTRY (so do cua chu du an). He = tin hieu vao x luat quan tri.
- CHAN (cong ep): khong co lai sau phi; maxDD >= 80% o don bay chot truoc niem phong; chi phi khong
  do duoc; qua it lenh. MOI THU KHAC la NHAN (`nhan_canh_bao`) - doc ky, bao cao lai, khong chan:
    * KHONG hon moc (mua-giu/ban-giu co don bay cung tran DD ra tien hon) hoac `beta.ty_le_beta` >= 0,5
      (phan lon lai gop = phoi nhiem TB x troi tai san): he dung, nhung chi la BETA - noi ro cho chu du
      an, va uu tien he hon moc khi chon huong dao sau. Do 25/09 (`b nc kiem 30` muc 5): tren chuoi troi
      nhu chi so, ~20% y tuong NGAU NHIEN lot ca ba doan theo tieu chi nay - cong khong loc beta, BAN loc.
    * rr thuc te < 0,2 / lai rong < 3x phi spread (kieu martingale / edge mong so voi phi).
    * `duoi_lo`: he lai nho nhieu lan lo lon it lan chi lo gia that khi gap du lenh thua. Neu so lenh
      chua toi `so_lenh_can_de_thay_duoi` thi lai CHUA kiem voi duoi - chay tren doan/ma/khung dai hon
      TRUOC khi niem phong. Day la cach DO dung mot he martingale, khong phai cach cam no.
    * MDE/FDR/placebo/Sharpe giam phat.

## CACH LAM VIEC - vong khoa hoc, khong phai pheu
1. Doc ho so (so tay) trong loi nhac. Thi nghiem y het tra ket qua cu - dung phi luot.
2. Chon 1-2 cau hoi co gia tri ky vong cao nhat (xac suat dung x tien neu dung / chi phi thu). ~70% dao
   sau huong dang co dau hieu, ~30% huong moi. Cau hoi nguon 'nguoi' lam truoc.
3. ghi_gia_thuyet: phat bieu kiem duoc + VI SAO co nguoi tra tien cho phoi nhiem nay. Moi thi nghiem
   gan gt_id de phep thu duoc dem theo dong.
4. Thi nghiem, thu tu thuong dung:
   ho_so_tai_san -> tim_quy_luat (tu du lieu) hoac thu_co_che (y tuong cua ban) -> mo_xe_lenh (hoc tu
   lenh dung/sai: bo loc + luat quan tri) -> thu lai bien the tren kham pha -> quet_tham_so (chon theo
   HINH DANG) -> xac_nhan -> niem_phong -> xuat_mq5. ghep_danh_muc khi co vai chan song.
   Ho quan tri KHONG can tin hieu vao (luoi, tia lenh, nang lot): thu_luoi (hien chi AUDCAD).
5. Ghi lai: ket qua quan trong -> ghi_hieu_biet (kem tn_id); huong moi -> ghi_cau_hoi; cap nhat trang
   thai gia thuyet (BAC_BO kem ly do so, TRIEN_VONG khi qua xac nhan). Chu ky khong ghi gi = mat trang.
6. Ket thuc chu ky bang 5-10 dong: da hoc gi (kem so va so lenh), gia thuyet nao doi trang thai, viec
   tiep theo dang gia nhat.

## KY LUAT DU LIEU (cong cu ep; hieu vi sao de khong tu lua minh)
- kham_pha = 60% dau: tu do do tim. xac_nhan = 60-80%: chi cho bien the DA CHOT, moi lan nhin bi dem.
  niem_phong = 20% cuoi: MOT lan cho mot khai bao, toi da 3 lan cho mot dong gia thuyet.
- Cuc dai cua nhieu phep thu luon dep. Tin CAO NGUYEN (quet_tham_so), tin p_null (tim_quy_luat,
  mo_xe_lenh - da tinh ca viec do tim), khong tin mot o le loi hay mot luat p_null > 0,1.
- Loc hau kiem tren chinh doan kham pha luon dep hon that: moi bo loc phai chay lai qua thu_co_che roi
  xac_nhan.
- Ba trang thai: DAT / AM / CHUA_DO_DUOC. CHUA_DO_DUOC (it lenh, khai bao sai, chi phi khai) KHONG
  phai am - sua cach do, dung ket luan "khong co edge".
- t_lenh > 5, CAGR phi thuc, hay he tot bat thuong = nghi loi do / nhin truoc TRUOC khi mung.
- Chuoi TONG_HOP_* co dap an biet truoc: chi de kiem cong cu va quy trinh, khong bao gio la phat hien.
- niem_phong chot DON BAY tu kham pha + xac nhan roi moi mo doan cuoi: DAT = co lai VA maxDD < 80% o
  chinh don bay do. Chon don bay tren doan niem phong la nhin truoc.
- Mot phat hien DAT niem phong van chi la "canh bac co ky vong duong do duoc" - buoc tiep la MT5
  tester (xuat_mq5) roi demo.

## LAB DA DO DUOC (dinh huong; kiem lai duoc)
- Thu thap them tai lieu KHONG tang dau ra: 12.078 tai lieu -> 18 mau; kho x6 -> ung vien van 21. Dao
  du lieu va lenh cua chinh minh truoc; chi nho SEEKER (yeu_cau_seeker) khi can y tuong cu the.
- Tren FX tien nam o QUAN TRI VI THE: AUDCAD luoi hai chieu CO TIA LENH holdout +13,26%/nam DD -3,5%,
  khong tia chi +0,66%/nam. 668 co che entry thuan tren AUDCAD H4: 0 cai vua du 2 lenh/tuan vua Sharpe
  duong.
- Dang "A KHI B" (mot dieu kien la CHE DO bien dong/xu huong) song tot hon nhan to don. He don qua
  holdout 822 -> 40; cap ghep giu hang 39/45; chan am nguoc pha lam ro tot len.
- Phi qua dem ~1,56 bps/dem dat hon spread; chieu ban co the NHAN phi. He giu nhieu ngay phai tinh phi.
- Cap cheo FX va vang HOI QUY o moi thang do (AUDCAD/EURGBP, XAUUSD); chi so gan nhu khong co gi o M5.
- Bar D1 cua CFD chi so ~23 gio, khong phai bar phien. Chi phi an 12% bien do nen M5 nhung 0,7% nen D1.

## NGU PHAP CO CHE (khai bao, khong viet ma)
__NGU_PHAP__

## DAC TRUNG CO SAN (ten dung trong tim_quy_luat/mo_xe_lenh; toan hang tuong ung dung trong spec)
__DAC_TRUNG__

## QUAN TRI VI THE (tham so `quan_tri`, don vi ATR tai bar vao)
  sl_atr (cat lo), tp_atr (chot loi), hue_tu_atr (lai X ATR thi keo SL ve gia vao), trail_tu_atr +
  trail_buoc (trailing), thoat_bar (thoat sau N bar), chot_phan (chot mot nua o X ATR). Khong co
  quan_tri = vao roi giu `giu` bar / toi dieu kien `ra`.

Viet tieng Viet khong dau, ngan, di thang vao so. Moi con so kem so lenh. Neu khong chac thi noi khong
chac.""".replace("__NGU_PHAP__", _ngu_phap_tom_tat()).replace("__DAC_TRUNG__", _dac_trung_tom_tat())


# ================================================================ API
def _tao_client():
    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError("chua cai goi `anthropic` (pip install anthropic) - hoac chay "
                           "`b nc claude` (Claude Code) / `b nc tu-lai` (khong LLM)") from e
    return anthropic.Anthropic()


def _usd(mo_hinh: str, usage) -> float:
    vao, ra = GIA.get(mo_hinh, GIA["claude-opus-5"])
    g = lambda k: float(getattr(usage, k, 0) or 0)  # noqa: E731
    return (g("input_tokens") * vao + g("output_tokens") * ra
            + g("cache_creation_input_tokens") * vao * 1.25
            + g("cache_read_input_tokens") * vao * 0.10) / 1e6


def _goi_api(client, c: dict, messages: list, tools: list, ket_thuc: bool = False):
    """Mot request. Tham so moi (output_config, cache_control, fallbacks) di qua `extra_body`
    neu SDK dang cai chua biet chung - khong de mot SDK cu lam vo ca vong."""
    ham = client.beta.messages.create
    try:
        co = set(inspect.signature(ham).parameters)
    except (TypeError, ValueError):
        co = set()
    kw = {"model": c["mo_hinh"], "max_tokens": int(c["max_tokens"]),
          "system": [{"type": "text", "text": HIEN_CHUONG, "cache_control": {"type": "ephemeral"}}],
          "tools": tools, "messages": messages, "thinking": {"type": "adaptive"}}
    them = {"output_config": {"effort": c["effort"]}, "cache_control": {"type": "ephemeral"}}
    if c.get("fallback"):
        kw["betas"] = [BETA_FALLBACK]
        them["fallbacks"] = "default"
    if ket_thuc:
        kw["tool_choice"] = {"type": "none"}
    extra = {}
    for k, v in them.items():
        if k in co:
            kw[k] = v
        else:
            extra[k] = v
    if extra:
        kw["extra_body"] = extra
    return ham(**kw)


def _nhac_dau(vong_id: int, c: dict, loi_nhan: str = "") -> str:
    p = ["Chu ky nghien cuu #%d. Ngan sach chu ky: %d lan goi cong cu do, $%.1f."
         % (vong_id, c["cong_cu_moi_vong"], c["usd_moi_vong"]), "",
         ST.tom_tat_md(12), ""]
    if loi_nhan:
        p += ["## Loi nhan cua chu du an cho chu ky nay", loi_nhan, ""]
    tong = ST.tom_tat(1)["dem"]
    if tong["thi_nghiem"] == 0:
        p += ["So tay dang TRONG - day la chu ky dau. Goi danh_sach_du_lieu, chon 1-2 ma that co du "
              "lieu dai va chi phi do duoc (uu tien nhung ma lab da thay dau hieu: AUDCAD, EURGBP, "
              "XAUUSD, chi so My), lap chuong trinh nghien cuu ban dau bang ghi_cau_hoi, roi bat "
              "dau thi nghiem.", ""]
    p.append("Bat dau. Tu chon viec, dung cong cu, ghi so tay, ket thuc bang tom tat ngan.")
    return "\n".join(p)


def _ghi_nhat_ky(f: Path, dong: str) -> None:
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as g:
        g.write(dong.rstrip() + "\n")


def chay_vong(loi_nhan: str = "", client=None, c: dict | None = None) -> dict:
    """MOT chu ky nghien cuu bang Claude API. Tra {vong_id, tom_tat, so_cong_cu, usd, trang_thai}."""
    c = dict(c or cau_hinh())
    if CO_DUNG.exists():
        return {"trang_thai": "DUNG", "ly_do": "co DUNG_LAI dang bat"}
    da_chi = ST.usd_hom_nay()
    if da_chi >= float(c["usd_moi_ngay"]):
        return {"trang_thai": "HET_NGAN_SACH", "ly_do": "hom nay da chi $%.2f >= $%.2f"
                % (da_chi, c["usd_moi_ngay"])}
    client = client or _tao_client()
    vong_id = ST.bat_dau_vong("claude_api", c["mo_hinh"])
    nk = THU_MUC_VONG / ("vong_%05d.md" % vong_id)
    _ghi_nhat_ky(nk, "# Chu ky %d - %s - %s\n" % (vong_id, ST.bay_gio(), c["mo_hinh"]))
    tools = CC.schema_api()
    messages: list = [{"role": "user", "content": _nhac_dau(vong_id, c, loi_nhan)}]
    so_cc, usd, tk_vao, tk_ra, luot = 0, 0.0, 0, 0, 0
    da_bao_het, ket_thuc = False, False
    tom_tat, trang_thai = "", "XONG"
    toi_da, tran_luot = int(c["cong_cu_moi_vong"]), int(c["cong_cu_moi_vong"]) * 2 + 12
    while luot < tran_luot:
        luot += 1
        resp = _goi_api(client, c, messages, tools, ket_thuc=ket_thuc)
        u = getattr(resp, "usage", None)
        if u is not None:
            usd += _usd(c["mo_hinh"], u)
            tk_vao += int(getattr(u, "input_tokens", 0) or 0) + int(
                getattr(u, "cache_read_input_tokens", 0) or 0)
            tk_ra += int(getattr(u, "output_tokens", 0) or 0)
        van = [b.text for b in resp.content if getattr(b, "type", "") == "text" and b.text.strip()]
        for t in van:
            _ghi_nhat_ky(nk, "\n" + t)
        dung = resp.stop_reason
        if dung == "refusal":
            trang_thai, tom_tat = "TU_CHOI", "mo hinh tu choi: %s" % getattr(resp, "stop_details", None)
            break
        if dung == "pause_turn":
            messages.append({"role": "assistant", "content": resp.content})
            continue
        dung_cc = [b for b in resp.content if getattr(b, "type", "") == "tool_use"]
        if dung in ("end_turn", "stop_sequence") or not dung_cc:
            tom_tat = "\n".join(van)[-3000:]
            break
        messages.append({"role": "assistant", "content": resp.content})
        ket, bi_chan = [], False
        for b in dung_cc:
            if dung == "max_tokens":          # dau vao co the bi cat - khong chay
                ket.append({"type": "tool_result", "tool_use_id": b.id, "is_error": True,
                            "content": "dau ra bi cat o max_tokens; goi lai voi dau vao gon hon"})
                continue
            do_luong = b.name not in CC.CONG_CU_GHI
            if do_luong and (so_cc >= toi_da or usd >= float(c["usd_moi_vong"])):
                bi_chan = True
                ket.append({"type": "tool_result", "tool_use_id": b.id, "is_error": True,
                            "content": "het ngan sach chu ky - chi con duoc ghi_hieu_biet / "
                                       "ghi_cau_hoi / ghi_gia_thuyet, roi tom tat va ket thuc"})
                continue
            kq = CC.goi(b.name, dict(b.input or {}), vong_id=vong_id)
            if do_luong:
                so_cc += 1
            _ghi_nhat_ky(nk, "\n> %s %s\n> -> %s" % (b.name, json.dumps(b.input, ensure_ascii=False)[:400],
                                                    CC._gon(kq, 600)))
            ket.append({"type": "tool_result", "tool_use_id": b.id,
                        "content": CC._gon(kq), "is_error": bool(isinstance(kq, dict) and kq.get("loi"))})
        if (so_cc >= toi_da or usd >= float(c["usd_moi_vong"])) and not da_bao_het:
            da_bao_het = True
            ket.append({"type": "text", "text": (
                "[he thong] Het ngan sach chu ky (%d cong cu do, $%.2f). Ghi hieu biet/cau hoi con "
                "thieu roi viet tom tat 5-10 dong va dung." % (so_cc, usd))})
        elif bi_chan:
            # Da bao het ngan sach ma van goi cong cu do: luot sau CAM cong cu, buoc viet tom tat.
            ket_thuc = True
        messages.append({"role": "user", "content": ket})
    else:
        trang_thai = "CHAM_TRAN_LUOT"
    ST.ket_thuc_vong(vong_id, tom_tat or "(khong co tom tat)", so_cc, tk_vao, tk_ra, usd, trang_thai)
    _ghi_nhat_ky(nk, "\n---\n%s | %d cong cu | $%.3f | %s" % (trang_thai, so_cc, usd, ST.bay_gio()))
    return {"vong_id": vong_id, "trang_thai": trang_thai, "so_cong_cu": so_cc, "usd": round(usd, 3),
            "tom_tat": tom_tat, "nhat_ky": CC._tuong_doi(nk)}


def chay_lien_tuc(so_vong: int | None = None, loi_nhan: str = "", driver: str = "api") -> None:
    """Chay nhieu chu ky (None = mai mai) cho toi DUNG_LAI hoac het ngan sach ngay."""
    c = cau_hinh()
    i = 0
    while so_vong is None or i < so_vong:
        i += 1
        r = (chay_vong(loi_nhan if i == 1 else "") if driver == "api"
             else chay_claude_code(loi_nhan if i == 1 else ""))
        print(json.dumps({k: v for k, v in r.items() if k != "tom_tat"}, ensure_ascii=False))
        if r.get("trang_thai") in ("DUNG", "HET_NGAN_SACH", "TU_CHOI", "LOI"):
            break
        time.sleep(float(c["nghi_giua_vong_giay"]))


# ============================================================ CLAUDE CODE
def lenh_claude_code(vong_id: int, c: dict, loi_nhan: str = "") -> list[str]:
    """Dong lenh `claude -p` cho mot chu ky - chi mo quyen cong cu cua nha nghien cuu."""
    nhac = ("Chu ky nghien cuu tu chu #%d. Ban LA nha nghien cuu (xem hien chuong). Buoc dau: "
            "`python b.py nc so-tay`. Moi phep do: `python b.py nc cc <ten_cong_cu> '<json>'` "
            "(liet ke: `python b.py nc cc`). Toi da %d lan goi cong cu do. Ghi hieu biet va cau "
            "hoi bang `ghi_hieu_biet` / `ghi_cau_hoi`. Ket thuc bang tom tat 5-10 dong."
            % (vong_id, c["cong_cu_moi_vong"]))
    if loi_nhan:
        nhac += "\n\nLoi nhan cua chu du an: " + loi_nhan
    exe = shutil.which(c["claude_code_lenh"]) or c["claude_code_lenh"]
    lenh = [exe, "-p", nhac, "--append-system-prompt", HIEN_CHUONG.replace(
        "Viet tieng Viet khong dau",
        "Cong cu goi qua `python b.py nc cc <ten> '<json>'` (JSON mot dong; hoac @file.json).\n"
        "Viet tieng Viet khong dau"),
            "--allowedTools", "Bash(python b.py nc:*)", "Bash(python -X utf8 b.py nc:*)",
            "Bash(b nc:*)", "Read", "Grep", "Glob", "--output-format", "json",
            # khong ai ngoi may de bam "cho phep": moi cong cu ngoai danh sach tren bi TU CHOI
            # ngay thay vi treo cho hoi. Ban Claude Code cu khong co co nay thi dat
            # "claude_code_co_them": [] trong config/nha_nghien_cuu.json.
            *c.get("claude_code_co_them", ["--permission-mode", "dontAsk"])]
    if c.get("usd_moi_vong"):
        lenh += ["--max-budget-usd", str(c["usd_moi_vong"])]
    if c.get("mo_hinh_claude_code"):
        lenh += ["--model", str(c["mo_hinh_claude_code"])]
    return lenh


def chay_claude_code(loi_nhan: str = "", c: dict | None = None) -> dict:
    """MOT chu ky bang Claude Code headless (`claude -p`) - dung goi Claude Code dang co."""
    c = dict(c or cau_hinh())
    if CO_DUNG.exists():
        return {"trang_thai": "DUNG", "ly_do": "co DUNG_LAI dang bat"}
    vong_id = ST.bat_dau_vong("claude_code", str(c.get("mo_hinh_claude_code") or "mac_dinh"))
    lenh = lenh_claude_code(vong_id, c, loi_nhan)
    moi_truong = dict(os.environ, NC_VONG_ID=str(vong_id), PYTHONIOENCODING="utf-8")
    try:
        p = subprocess.run(lenh, cwd=str(LAB), capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=moi_truong,
                           timeout=int(c["claude_code_timeout_giay"]))
    except FileNotFoundError:
        ST.ket_thuc_vong(vong_id, "khong tim thay lenh claude", trang_thai="LOI")
        return {"vong_id": vong_id, "trang_thai": "LOI", "ly_do": "khong tim thay `claude` tren PATH"}
    except subprocess.TimeoutExpired:
        ST.ket_thuc_vong(vong_id, "qua gio", trang_thai="QUA_GIO")
        return {"vong_id": vong_id, "trang_thai": "QUA_GIO"}
    tom_tat, usd = (p.stdout or "")[-3000:], 0.0
    try:
        j = json.loads(p.stdout)
        tom_tat = str(j.get("result") or "")[-3000:]
        usd = float(j.get("total_cost_usd") or j.get("cost_usd") or 0.0)
    except Exception:
        pass
    so_cc = int(ST.mot("SELECT COUNT(*) n FROM thi_nghiem WHERE vong_id=?", vong_id).get("n") or 0)
    tt = "XONG" if p.returncode == 0 else "LOI"
    ST.ket_thuc_vong(vong_id, tom_tat, so_cc, usd=usd, trang_thai=tt)
    nk = THU_MUC_VONG / ("vong_%05d.md" % vong_id)
    _ghi_nhat_ky(nk, "# Chu ky %d (claude code) - %s\n\n%s\n\n---\nrc=%s | %d thi nghiem | $%.3f\n%s"
                 % (vong_id, ST.bay_gio(), tom_tat, p.returncode, so_cc, usd, (p.stderr or "")[-800:]))
    return {"vong_id": vong_id, "trang_thai": tt, "so_cong_cu": so_cc, "usd": usd,
            "tom_tat": tom_tat, "nhat_ky": CC._tuong_doi(nk)}


def main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="nc_tac_tu")
    ap.add_argument("--vong", type=int, default=1, help="so chu ky (0 = mai mai)")
    ap.add_argument("--claude-code", action="store_true", help="chay bang `claude -p`")
    ap.add_argument("--nhan", default="", help="loi nhan cua chu du an cho chu ky dau")
    ap.add_argument("--hien-chuong", action="store_true", help="in hien chuong roi thoat")
    a = ap.parse_args(argv)
    if a.hien_chuong:
        print(HIEN_CHUONG)
        return 0
    chay_lien_tuc(None if a.vong == 0 else a.vong, a.nhan, "claude_code" if a.claude_code else "api")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
