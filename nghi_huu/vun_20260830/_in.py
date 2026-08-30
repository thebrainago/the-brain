from pathlib import Path
lab = Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
files = sorted([p.name for p in lab.iterdir() if p.is_file() and p.suffix.lower() in (".py", ".ps1", ".md", ".cmd", ".vbs")])
import json
def group(f):
    n = f.lower()
    if "tele" in n or "social" in n or "kai" in n or "reddit" in n or "nguon" in n or "bao_giay" in n or "fl_cheo" in n or "doc_web" in n or "dang_ky" in n or "dang_nhap" in n or "otp" in n or "doc_email" in n or "follow" in n or "them_tai_khoan" in n: return "SSOCIAL"
    if n.startswith("quant") or "ichimoku" in n or "mo_phong" in n or "sweep" in n or "cross_pair" in n or "backtest" in n or "data_" in n or "vu_" in n or "team" in n: return "QQUANT"
    if n.startswith("thorn") or n.startswith("brain") or n.startswith("bo_nao") or "evolution" in n or "giam_sat" in n or "watchdog" in n or "autopilot" in n or "tru_worker" in n: return "BCO"
    if "seeker" in n or "kiem_tim" in n or "kham_pha" in n or "doc_" in n: return "SSEEK"
    if "banker" in n or "vi_mo" in n or "fed" in n or "cfa" in n: return "PPBANK"
    if "tiep_tuc" in n or "goi" in n or "run_" in n or "ma_so" in n or "phan_phoi" in n or "rea" in n: return " AACTION"
    return "ZHON"
cats = {"SSOCIAL":[], "QQUANT":[], "BCO":[], "SSEEK":[], "PPBANK":[], " AACTION":[], "ZHON":[]}
for f in files: cats[group(f)].append(f)
lines = ["# THE BRAIN - KIEM KE & BAN DO KET NOI", "Ngay: 2026-08-14 ~ 21:00",
         "", "Noi chua: TAT CA code brain nam trong lab. Ngoai ra: C:\\lab\\watchdog_brain.* (watchdog cu).",
         "Recycle Bin: khong co file lien quan.", "",
         "BROWSER DUNG: .browser_darwinex (darwin) - KHONG mo thebrain2/9222.",
         f"- Loi: toi da mo thebrain2 o 9222 (sai). Con dung: darwin (CDP 9224).", ""]
for name, fn in [("0 CONG", "BCO"), ("1 QUANT", "QQUANT"), ("2 SEEKER", "SSEEK"), ("3 SOCIAL", "SSOCIAL"), ("4 BANKER", "PPBANK"), ("5 ACTION(NGUOI DUNG)", " AACTION"), ("6 KHAC", "ZHON")]:
    lines += ["## " + name, ""] + ["- " + x for x in cats[fn]] + [""]
lines += ["## KET NOI CON THIEU (toi uu)",
  "- Social chua chay that qua BRWSER DARWIN: can mo .browser_darwinex + CDP, chay nguon_*/seeker_theo_doi/telethon_ban.",
  "- Seeker web da chay (arXiv web_live=12) OK; Reddit/X/FB bi IP chuyen -> phai qua BRWSER darwin, khong phai requests.",
  "- Brain 5 tru (SEEKER/QUANT/BANKER/EVO/COMPUTE) dang chay 24-7 OK; governor CPU ~83%.",
  "- Telegram: tele_gate.py san, bot @thebrain_point_bot xac minh, tele_bridge da dien; thieu chat_id (chu nhan tin bot 1 lan).",
  "- TOM TAT 2h: doc lor for_ds moi ngay (BrainDocForDs), bao cao gio (BrainBaoCao) ra Desktop."]
(lab / "INVENTORY_THE_BRAIN.md").write_text("\n".join(lines), encoding="utf-8")
print("DA GHI INVENTORY_THE_BRAIN.md, tong file=", len(files))
