p = r"C:\Users\SV STORE\Downloads\Research SP500\lab\seeker_quy_tac.py"
s = open(p, encoding="utf-8").read()
o = '''def loc_web(toi_da=12, gioi_han_gio=6):
    """Loc LIVE tu arXiv (q-fin.ST/PM/TR), cache gioi_han. web_live=so bai loc duoc."""
    out = REPORTS / "seeker_web.json"
    state = REPORTS / "seeker_web_state.json"
    now = time.time()'''
n = '''def loc_web(toi_da=12, gioi_han_gio=6):
    """Loc LIVE tu arXiv (q-fin.ST/PM/TR), cache gioi_han. web_live=so bai loc duoc."""
    global last_fetch
    out = REPORTS / "seeker_web.json"
    state = REPORTS / "seeker_web_state.json"
    now = time.time(); last_fetch = {"luc": now}'''
if o in s:
    s = s.replace(o, n, 1); open(p, "w", encoding="utf-8").write(s); print("fix time ok")
else:
    print("anchor not found (skip)")
