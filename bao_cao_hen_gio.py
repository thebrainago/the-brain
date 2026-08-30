import time
from pathlib import Path


if __name__ == "__main__":
    # Bo than script vao chot nay: truoc day chi can import module la
    # chay het ca bai quet/ghi bao cao, ke ca khi nguoi goi chi muon
    # dung mot ham trong file.

    DESK = Path(r"C:\Users\SV STORE\Desktop")
    OUT = DESK / "Bao_cao"; OUT.mkdir(exist_ok=True)
    LAB = Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
    REP = LAB / "reports"
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    def read(p, tail=3000):
        try: return p.read_text(encoding="utf-8-sig")[-tail:]
        except Exception: return "(chua co)"
    def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    evo = read(REP / "EVO_BAO_CAO.md", 2600)
    master = read(REP / "brain_master.log", 500)
    try: gate = (REP/"cpu_gate.txt").read_text().strip()
    except Exception: gate = "?"
    heart = [(f.name.replace("worker_","").replace(".txt",""), f.read_text().strip()) for f in REP.glob("worker_*.txt")]
    tt = "\n".join(f"{k}={v}" for k,v in heart)
    for f in REP.glob("worker_*.txt"):
        pass
    fds = read(DESK / "for ds.txt", 350)
    h = f"""<meta charset=utf-8><title>The Brain</title>
    <h2>The Brain - Bao cao cap nhat</h2>
    <p><b>{now}</b> — cap nhat moi 1 gio (F5)</p>
    <h3>Da / Dang / Se lam</h3>
    <ul><li><b>Da:</b> 5 tru 24-7 (SEEKER,QUANT,BANKER,EVO,COMPUTE); param-grid 128 job xong; RANK_DARWIN; web_live=12 arXiv; ghi console codex tiep tuc.</li>
    <li><b>Dang:</b> quet M1 + ichimoku (QUANT); param grid chay (COMPUTE); governor giu ~83%; SEEKER thu web/loc Darwinex.</li>
    <li><b>Se:</b> xac nhan combo duong (spread/OOS/placebo) -&gt; MT5 -&gt; chien luoc dau tien; mo nguon (browser/social; doc for_ds moi ngay).</li></ul>
    <h3>Tru (nhip tim)</h3><pre>{esc(tt)} ({'KHOA gate='+gate})</pre>
    <h3>EVO giam sat</h3><pre>{esc(evo)}</pre>
    <h3>brain_master (governor)</h3><pre>{esc(master)}</pre>
    <h3>FOR_DS (y tuong ban - doc moi ngay)</h3><pre>{esc(fds)}</pre>
    """
    (OUT / "BAO_CAO_CAP_NHAT.html").write_text(h, encoding="utf-8")
    (OUT / "BAO_CAO_CAP_NHAT.txt").write_text(f"Cap nhat {now}\n---TRU---\n{tt}\n---EVO---\n{evo}\n", encoding="utf-8")
    print("OK bao_cao", now)
