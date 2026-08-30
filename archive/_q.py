p = r"C:\Users\SV STORE\Downloads\Research SP500\lab\quant_offline.py"
s = open(p, encoding="utf-8").read()
o = '''    caps = sorted(p.stem.replace("_M1_mq", "") for p in DATA.glob("*_M1_mq.parquet"))
    done = set(st.get("done", []))
    pending = [c for c in caps if c not in done]
    if not pending:
        st = {"vong": st.get("vong", 0) + 1, "done": []}
        pending = caps'''
n = '''    import os
    caps = sorted(p.stem.replace("_M1_mq", "") for p in DATA.glob("*_M1_mq.parquet"))
    phu = int(os.environ.get("BRAIN_PHU", "0")); tong = int(os.environ.get("BRAIN_TONG", "1"))
    caps_mine = caps[phu::tong]
    done = set(st.get("done", []))
    pending = [c for c in caps_mine if c not in done]
    if not pending:
        st = {"vong": st.get("vong", 0) + 1, "done": []}
        pending = caps_mine'''
assert o in s, "quant_offline OLD NOT FOUND"
s = s.replace(o, n, 1)
open(p, "w", encoding="utf-8").write(s)
print("quant_offline partition patched ok")
