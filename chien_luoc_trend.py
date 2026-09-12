import numpy as np, pandas as pd, json
from pathlib import Path


if __name__ == "__main__":
    # Bo than script vao chot nay: truoc day chi can import module la
    # chay het ca bai quet/ghi bao cao, ke ca khi nguoi goi chi muon
    # dung mot ham trong file.

    lab = Path(__file__).resolve().parent
    rd = lab.parent / "data"
    files = sorted([f for f in rd.glob("*.parquet") if "_m1_mq" in f.name.lower()])
    print("found:", len(files))

    def atr(h,l,c,n=14):
        pc=np.roll(c,1); pc[0]=c[0]
        tr=np.maximum(h-l,np.maximum(abs(h-pc),abs(l-pc)))
        return pd.Series(tr).ewm(alpha=1.0/n,adjust=False).mean().values

    def scan(df,N,am,rr,risk=0.005,max_hold=400):
        c=df.close.values; h=df.high.values; l=df.low.values; o=df.open.values
        a=atr(h,l,c)
        hh=pd.Series(h).rolling(N).max().values
        sig=np.flatnonzero(c > np.roll(hh,1))
        R=0.; w=0; n=0; eq=0.; pk=0.; dd=0.
        for i in sig:
            j=i+1
            if j>=len(o)-1: break
            en=o[j]; at=max(a[j],1e-9); slp=en-am*at; tpp=en+rr*am*at
            e=min(j+max_hold,len(h))
            ht=np.flatnonzero(h[j:e]>=tpp); st=np.flatnonzero(l[j:e]<=slp)
            if ht.size and (not st.size or ht[0]<st[0]): rv=rr; w+=1
            elif st.size: rv=-1.
            else: rv=(c[e-1]-en)/(am*at)
            R+=rv; n+=1; eq+=rv; pk=max(pk,eq); dd=min(dd,eq-pk)
        if not n: return None
        return {"lenh":n,"roi":round(R*risk*100,2),"dd":round(abs(dd)*risk*100,2),
                "pf":round((w*rr)/max(n-w,1e-9),2),"win":round(w/n*100,1)}

    res=[]
    for f in files:
        pair=f.name.replace("_M1_mq.parquet","")
        df=pd.read_parquet(f); df.columns=[str(x).lower() for x in df.columns]
        if "time" in df.columns: df["_t"]=pd.to_datetime(df["time"],errors="coerce"); df=df.dropna(subset=["_t"]).set_index("_t").drop(columns=["time"])
        elif str(df.index.name).lower()!="time": df=df.iloc[::20]
        g=df.resample("15min").agg({"open":"first","high":"max","low":"min","close":"last"})
        g=g.dropna()
        if not g.index.name or g.index.name!="time": g=g.reset_index().set_index("time") if "time" in g.index.name.lower() else g
        for N in (120,250):
            for am in (2.0,3.0):
                for rr in (2.0,3.0):
                    r=scan(g,N,am,rr)
                    if r: res.append({"cap":pair,"N":N,"am":am,"rr":rr,**r})
    res.sort(key=lambda x:-x["roi"])
    (lab/"reports"/"TREND_SIM.json").write_text(json.dumps(res,ensure_ascii=False,indent=1),encoding="utf-8")
    print("TONG:",len(res))
    for r0 in res[:18]:
        print(f"{r0['cap']:7s} N={r0['N']} am={r0['am']} rr={r0['rr']} roi={r0['roi']:>6}% dd={r0['dd']:>5}% pf={r0['pf']} l={r0['lenh']} win={r0['win']}%")
