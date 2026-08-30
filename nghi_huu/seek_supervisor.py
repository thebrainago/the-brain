# -*- coding: utf-8 -*-
r"""seek_supervisor.py - LAM SEEKER CHAY MUOT 24/7: chay quan_li_quet.py lam tien
trinh con, neu no crash thi tu dong khoi dong lai. Ghi heartbeat + log.
Chay nhan:  python seek_supervisor.py
"""
import subprocess, time, sys, pathlib

LAB = pathlib.Path(__file__).parent
PY = r"C:\Users\SV STORE\sp500_env\Scripts\python.exe"
HB = LAB / "reports" / "seek_heartbeat.txt"
LOG = LAB / "reports" / "seek_supervisor.log"

def log(msg):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    print(msg)

def main():
    log("SEEK SUPERVISOR bat dau (24/7)")
    while True:
        try:
            p = subprocess.Popen([PY, str(LAB / "quan_li_quet.py")],
                                 cwd=str(LAB), stdout=open(LAB/"reports/quet_super.log","w",encoding="utf-8"),
                                 stderr=subprocess.STDOUT)
            log(f"quan_li_quet khoi dong pid={p.pid}")
            while True:
                rc = p.poll()
                if rc is not None:
                    break
                HB.write_text(time.strftime('%Y-%m-%d %H:%M:%S') + " alive\n", encoding="utf-8")
                time.sleep(20)
            log(f"quan_li_quet thoat rc={rc} -> khoi dong lai sau 5s")
        except Exception as e:
            log(f"LOI supervisor: {e}")
            HB.write_text("LOI " + str(e)[:80] + "\n", encoding="utf-8")
        time.sleep(5)

if __name__ == "__main__":
    main()
