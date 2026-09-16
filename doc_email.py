# THE BRAIN - doc_email: tu dong doc email cong tac (IMAP) va trich ma OTP
# Dung:  python doc_email.py [--tu 5]   (doc 5 email moi nhat)
"""DOC EMAIL qua IMAP: lay ma xac minh / thu tu nguon da dang ky."""

import argparse, imaplib, email, re, json, pathlib
from email.header import decode_header

LAB = pathlib.Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
CFG = json.loads((LAB / "config" / "email_cong_tac.json").read_text(encoding="utf-8"))

def dec(txt):
    if not txt:
        return ""
    out = []
    for part, enc in decode_header(txt):
        if isinstance(part, bytes):
            out.append(part.decode(enc or "utf-8", "replace"))
        else:
            out.append(part)
    return "".join(out)

def lay_ma(text):
    ma = set()
    # 6-8 chu so dung rieng
    for m in re.finditer(r'(?<!\d)(\d{6,8})(?!\d)', text):
        ma.add(m.group(1))
    return ma

def lay_lien_ket(text):
    """Trich lien ket xac nhan (http/https) tu email raw."""
    lk = set()
    for m in re.finditer(r'href=["\'](https?://[^"\' ]+)["\']', text, re.I):
        lk.add(m.group(1))
    # bo link dieu huong cua gmail/loi
    loai = ("unsubscribe", "gstatic", "google.com", "mail.google.com", "accounts.google.com")
    return [l for l in lk if not any(x in l for x in loai)]

def main(n=5):
    with imaplib.IMAP4_SSL("imap.gmail.com", 993) as m:
        m.login(CFG["email"], CFG["app_password"])
        m.select("INBOX")
        typ, data = m.search(None, "ALL")
        ids = data[0].split()
        latest = ids[-n:] if ids else []
        print(f"Tong email: {len(ids)} | doc {len(latest)} moi nhat ({CFG['email']})")
        for i in reversed(latest):
            typ, d = m.fetch(i, "(RFC822)")
            msg = email.message_from_bytes(d[0][1])
            subj = dec(msg.get("Subject"))
            sender = dec(msg.get("From"))
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body += part.get_payload(decode=True).decode("utf-8", "replace")
                        except Exception:
                            pass
            else:
                try:
                    body = msg.get_payload(decode=True).decode("utf-8", "replace")
                except Exception:
                    body = str(msg.get_payload())
            ma = lay_ma(subj + " " + body)
            print("-" * 60)
            print(f"[{i.decode()}] from: {sender} | subj: {subj[:70]}")
            if ma:
                print("   MA OTP:", ", ".join(sorted(ma)))
            else:
                print("   (khong thay ma)")
            lk = lay_lien_ket(subj + " " + body)
            if lk:
                print("   LIEN KET:", "; ".join(lk[:4]))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tu", type=int, default=5)
    a = ap.parse_args()
    main(a.tu)
