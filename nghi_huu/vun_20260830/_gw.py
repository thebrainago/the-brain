CFG = "CREATE_NO_WINDOW"
kw = ', creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))'
jobs = [
 (r"C:\Users\SV STORE\Downloads\Research SP500\lab\brain_master.py", []),
 (r"C:\Users\SV STORE\Downloads\Research SP500\lab\tru_worker.py", []),
 (r"C:\Users\SV STORE\Downloads\Research SP500\lab\quant_sweep.py", []),
]
def apply(p, reps):
    s = open(p, encoding="utf-8").read()
    for o, n in reps:
        if o in s: s = s.replace(o, n)
        else: print("  NOT FOUND in", p, "->", o[:60])
    open(p, "w", encoding="utf-8").write(s)

# brain_master: cpu() + 2 Popen
apply(jobs[0][0], [
 ("""subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Processor|Measure-Object -Property LoadPercentage -Average).Average"],
            capture_output=True, text=True, timeout=15)""",
  """subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Processor|Measure-Object -Property LoadPercentage -Average).Average"],
            capture_output=True, text=True, timeout=15, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))"""),
 ("""stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)""",
  """stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))"""),
])
# tru_worker: run_task
apply(jobs[1][0], [
 ("""timeout=3600).returncode""",
  """timeout=3600, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).returncode"""),
])
# quant_sweep: cpu()
apply(jobs[2][0], [
 ("""capture_output=True, text=True, timeout=15)""",
  """capture_output=True, text=True, timeout=15, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))"""),
])
print("CREATE_NO_WINDOW applied to all subprocess")
