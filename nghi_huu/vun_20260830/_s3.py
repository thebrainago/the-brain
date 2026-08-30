p = r"C:\Users\SV STORE\Downloads\Research SP500\lab\seeker_quy_tac.py"
s = open(p, encoding="utf-8").read()
o = '''    return {
        "tru": "SEEKER",'''
n = '''    r = {
        "tru": "SEEKER",'''
assert o in s
s = s.replace(o, n, 1)
open(p, "w", encoding="utf-8").write(s)
print("return{ -> r={ ok")
