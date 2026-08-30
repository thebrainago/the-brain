from playwright.sync_api import sync_playwright
CDP="http://127.0.0.1:9224"
try:
    with sync_playwright() as p:
        b=p.chromium.connect_over_cdp(CDP)
        ctx=b.contexts[0]
        pg=ctx.new_page()
        pg.goto("https://www.darwinex.com/account", timeout=30000, wait_until="domcontentloaded")
        pg.wait_for_timeout(5000)
        t=pg.inner_text("body", timeout=25000)
        low=t.lower()
        print("LOGIN? (welcome/signout/logout/account name):", any(k in low for k in ["sign out","log out","my account","welcome","logout"]) or "login" in low)
        print("co 'email' form?", "create account" in low or "your email" in low or "log in" in low)
        print("--- body (600) ---")
        print(t[:600].replace("\n"," | "))
        pg.close()
except Exception as e:
    print("ERR", repr(e)[:200])
