# THE BRAIN - dang ky AlphaVantage lay API key (email cong tac)
import time, json, re, pathlib, imaplib, email
from playwright.sync_api import sync_playwright
from email.header import decode_header

LAB = pathlib.Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
EMA = json.loads((LAB / "config" / "email_cong_tac.json").read_text(encoding="utf-8"))
CFG_FILE = LAB / "config" / "credentials.json"
URL = "https://www.alphavantage.co/support/"
HB = LAB / "reports" / "alphavantage_dk_heartbeat.txt"

def lay_key_email(so_phut=5):
    """Doc email moi nhat, tim chuoi key dai 10-20 ky tu 'cap'."""
    deadline = time.time() + so_phut * 60
    pat = re.compile(r"\b[A-Z0-9]{16,}\b")
    while time.time() < deadline:
        try:
            with imaplib.IMAP4_SSL("imap.gmail.com", 993) as m:
                m.login(EMA["email"], EMA["app_password"])
                m.select("INBOX")
                typ, data = m.search(None, "ALL")
                ids = data[0].split()
                for i in reversed(ids[-8:]):
                    typ, d = m.fetch(i, "(RFC822)")
                    msg = email.message_from_bytes(d[0][1])
                    subj = ""
                    for part, enc in decode_header(msg.get("Subject") or ""):
                        subj += part.decode(enc or "utf-8","replace") if isinstance(part,bytes) else part
                    snd = (msg.get("From") or "").lower()
                    if "alphavantage" not in snd:
                        continue
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type()=="text/plain":
                                try: body += part.get_payload(decode=True).decode("utf-8","replace")
                                except Exception: pass
                    else:
                        try: body = msg.get_payload(decode=True).decode("utf-8","replace")
                        except Exception: body = str(msg.get_payload())
                    for mm in pat.finditer(body + " " + subj):
                        k = mm.group(0)
                        if "ALPHA" not in k:  # key chu yeu chu hoa+so
                            return k, subj
        except Exception as e:
            HB.write_text("email err " + str(e)[:120], encoding="utf-8")
        time.sleep(10)
    return None, None

def main():
    (LAB / "reports").mkdir(exist_ok=True)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            channel="chrome", user_data_dir=str(LAB / ".profile_alphavantage"),
            headless=False, viewport={"width":1280,"height":900})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(URL, wait_until="load", timeout=60000)
        time.sleep(3)
        try:
            page.wait_for_selector("#email-text", timeout=20000)
            page.select_option("#occupation-text", "Software Developer")
            page.fill("#organization-text", "The Brain Project")
            page.fill("#email-text", EMA["email"])
            HB.write_text("da dien form", encoding="utf-8")
            page.click("#submit-btn")
            HB.write_text("da submit", encoding="utf-8")
        except Exception as e:
            try:
                diag = "URL=" + page.url + "\n" + page.inner_text("body")[:1500]
            except Exception:
                diag = "khong doc duoc page"
            (LAB / "reports" / "alphavantage_dk_page.txt").write_text(diag, encoding="utf-8")
            HB.write_text("loi dien form: " + str(e)[:200], encoding="utf-8")
            ctx.close()
            return
        # cho trang phan hoi
        for _ in range(20):
            try:
                txt = page.inner_text("body")
                if "key" in txt.lower() and ("sent" in txt.lower() or "email" in txt.lower()):
                    break
            except Exception:
                pass
            time.sleep(2)
        TB = page.inner_text("body")
        (LAB / "reports" / "alphavantage_dk_page.txt").write_text(TB, encoding="utf-8")
        ctx.close()
    # doc key tu email
    key, subj = lay_key_email(6)
    creds = {}
    if CFG_FILE.exists():
        try: creds = json.loads(CFG_FILE.read_text(encoding="utf-8"))
        except Exception: pass
    if key:
        creds["alphavantage"] = {"api_key": key, "email": EMA["email"]}
        CFG_FILE.write_text(json.dumps(creds, ensure_ascii=False, indent=2), encoding="utf-8")
        HB.write_text("KEY: " + key, encoding="utf-8")
        print("DA LAY KEY:", key)
    else:
        creds["alphavantage"] = {"ghi_chu": "chua nhan duoc key qua email"}
        CFG_FILE.write_text(json.dumps(creds, ensure_ascii=False, indent=2), encoding="utf-8")
        HB.write_text("chua co key", encoding="utf-8")
        print("chua nhan duoc key")

if __name__ == "__main__":
    main()
