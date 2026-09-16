import numpy as np, pandas as pd, json
from pathlib import Path


if __name__ == "__main__":
    # Bo than script vao chot nay: truoc day chi can import module la
    # chay het ca bai quet/ghi bao cao, ke ca khi nguoi goi chi muon
    # dung mot ham trong file.

    lab=Path(__file__).resolve().parent
    rd=lab.parent/"data"
    files=sorted([f for f in rd.glob("*.parquet") if "_m1_mq" in f.name.lower()])
    def atr(h,l,c,n=14):
        pc=np.roll(c,1); pc[0]=c[0]; tr=np.maximum(h-l,np.maximum(abs(h-pc),abs(l-pc)))
        return pd.Series(tr).ewm(alpha=1.0/n,adjust=False).mean().values
    def scan(g,N,k,am,rr,risk=0.005,max_hold=250):
        c=g.close.values; h=g.high.values; l=g.low.values; o=g.open.values
        a=atr(h,l,c); mid=pd.Series(c).rolling(N).mean().values; sd=pd.Series(c).rolling(N).std(ddof=0).values
        lo=mid-k*sd; sig=np.flatnonzero(c < np.roll(lo,1))
        R=0.;w=0;n=0;eq=0.;pk=0.;dd=0.
        for i in sig:
            j=i+1
            if j>=len(o)-1: break
            en=o[j]; at=max(a[j],1e-9); slp=en-am*at; tpp=en+rr*am*at; e=min(j+max_hold,len(h))
            ht=np.flatnonzero(h[j:e]>=tpp); st=np.flatnonzero(l[j:e]<=slp)
            if ht.size and (not st.size or ht[0]<st[0]): rv=rr; w+=1
            elif st.size: rv=-1.
            else: rv=(c[e-1]-en)/(am*at)
            R+=rv;n+=1;eq+=rv;pk=max(pk,eq);dd=min(dd,eq-pk)
        if not n: return None
        return {"lenh":n,"roi":round(R*risk*100,2),"dd":round(abs(dd)*risk*100,2),"pf":round((w*rr)/max(n-w,1e-9),2),"win":round(w/n*100,1)}
    res=[]
    for f in files:
        pair=f.name.replace("_M1_mq.parquet","")
        df=pd.read_parquet(f); df.columns=[str(x).lower() for x in df.columns]
        df["_t"]=pd.to_datetime(df["time"],errors="coerce"); df=df.dropna(subset=["_t"]).set_index("_t").drop(columns=["time"]) if "time" in df.columns else df.set_index(pd.to_datetime(df.index))
        for tf,rule in (("H1","1h"),("D1","1d")):
            g=df.resample(rule).agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
            if len(g)<200: continue
            for N in (5,10,20):
                for k in (2.0,2.5,3.0):
                    for am in (1.5,2.0):
                        for rr in (2.0,3.0):
                            r=scan(g,N,k,am,rr)
                            if r: res.append({"cap":pair,"tf":tf,"N":N,"k":k,"am":am,"rr":rr,**r})
    res=[r for r in res if r["roi"]>0]
    ok=sorted([r for r in res if r["pf"]>=1.3 and r["dd"]<=25],key=lambda x:(-x["pf"],x["dd"]))
    (lab/"reports"/"MR_H1D1.json").write_text(json.dumps(ok if ok else res,ensure_ascii=False,indent=1),encoding="utf-8")
    print("positive:",len(res),"| ok (pf>=1.3,dd<=25):",len(ok))
    for r in (ok[:15] if ok else sorted(res,key=lambda x:-x["pf"])[:15]):
        print(f"{r['cap']:7s} {r['tf']} N={r['N']} k={r['k']} am={r['am']} rr={r['rr']} roi={r['roi']:>6}% dd={r['dd']:>5}% pf={r['pf']} l={r['lenh']} win={r['win']}%")

