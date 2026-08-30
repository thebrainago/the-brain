p = r"C:\Users\SV STORE\Downloads\Research SP500\lab\tru_worker.py"
s = open(p, encoding="utf-8").read()
old = '''def run_task(ten, task):
    script = LAB
    for part in task:
        script = script / part
    return subprocess.run([PY, str(script)], cwd=str(LAB),
                          stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
                          timeout=3600).returncode'''
new = '''def run_task(ten, task):
    head = [x for x in str(task[0]).split("/")]
    script = LAB.joinpath(*head)
    args = [str(x) for x in task[1:]]
    return subprocess.run([PY, str(script)] + args, cwd=str(LAB),
                          stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
                          timeout=3600).returncode'''
assert old in s, "tru_worker.run_task not found"
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("tru_worker args ok")

e = r"C:\Users\SV STORE\Downloads\Research SP500\lab\evo_giam_sat.py"
t = open(e, encoding="utf-8").read()
if '"COMPUTE"' not in t:
    t = t.replace('TRU = ["SEEKER", "QUANT", "BANKER", "EVO"]', 'TRU = ["SEEKER", "QUANT", "BANKER", "EVO", "COMPUTE"]', 1)
    open(e, "w", encoding="utf-8").write(t)
    print("evo TRU includes COMPUTE")
else:
    print("evo already has COMPUTE")
