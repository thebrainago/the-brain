import numpy as np, pandas as pd, json
from pathlib import Path


if __name__ == "__main__":
    # Bo than script vao chot nay: truoc day chi can import module la
    # chay het ca bai quet/ghi bao cao, ke ca khi nguoi goi chi muon
    # dung mot ham trong file.

    lab=Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
    rd=lab.parent/"data"
    def atr(h,l,c,n=14):
        pc=np.roll(c,1); pc[0]=c[0]; tr=np.maximum(h-l,np.maximum(abs(h-pc),abs(l-pc)))
        return pd.Series(tr).ewm(alpha=1.0/n,adjust=False).mean().values
    def scan(g,N,k,am,rr):
        c=g.close.values; h=g.high.values; l=g.low.values; o=g.open.values
        a=atr(h,l,c); mid=pd.Series(c).rolling(N).mean().values; sd=pd.Series(c).rolling(N).std(ddof=0).values
        lo=mid-k*sd; sig=np.flatnonzero(c < np.roll(lo,1))
        R=0.;w=0;n=0
        for i in sig:
            j=i+1
            if j>=len(c)-1: continue
            en=o[j]; at=max(a[j],1e-9); slp=en-am*at; tpp=en+rr*am*at; e=min(j+250,len(h))
            ht=np.flatnonzero(h[j:e]>=tpp); st=np.flatnonzero(l[j:e]<=slp)
            if ht.size and (not st.size or ht[0]<st[0]): rv=rr; w+=1
            elif st.size: rv=-1.0
            else: rv=(c[e-1]-en)/(am*at)
            R+=rv; n+=1
        return (w/n*100,(w*rr)/max(n-w,1e-9),n) if n else (0,0,0)
    def load(pair):
        f=rd/(pair+"_M1_mq.parquet"); df=pd.read_parquet(f); df.columns=[str(x).lower() for x in df.columns]
        df["_t"]=pd.to_datetime(df["time"],errors="coerce"); df=df.dropna(subset=["_t"]).set_index("_t")
        if "time" in df.columns: df=df.drop(columns=["time"])
        return df.resample("1D").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
    cands=[("EURCAD",20,3.0,1.5,3.0),("EURCAD",20,3.0,1.5,2.0),("GBPCAD",20,2.5,1.5,3.0),
           ("EURCAD",10,3.0,1.5,2.0),("EURNZD",20,3.0,2.0,3.0),("EURCAD",10,2.5,1.5,2.0)]
    IT=300; rng=np.random.default_rng(123); out=[]
    print(f"{'cap':7s} {'N k am rr':13s} {'REALpf':>6s} {'plb_mean':>8s} {'plb_p95':>7s} {'pctle+':>7s} {'KD':6s}")
    for pair,N,k,am,rr in cands:
        g=load(pair); _,rp,n=scan(g,N,k,am,rr)
        c0=g.close.values; ret=np.diff(c0)/c0[:-1]
        pfs=[]
        for _ in range(IT):
            sh=rng.permutation(ret)
            cc=c0[0]*np.concatenate([[1.0],np.cumprod(1+sh)])
            gg=g.copy(); gg["close"]=cc; gg["open"]=gg["close"]*1.0; gg["high"]=np.maximum(gg["open"],gg["close"]); gg["low"]=np.minimum(gg["open"],gg["close"])
            _,p2,_=scan(gg,N,k,am,rr); pfs.append(p2)
        arr=np.array(pfs); p95=np.percentile(arr,95); pct=(arr<rp).mean()*100
        kd="GIU (edge)" if pct>=95 else "LOAI (nhieu)"
        out.append({"cap":pair,"p":[N,k,am,rr],"real_pf":round(rp,2),"plb_mean":round(arr.mean(),2),"p95":round(p95,2),"pctle":round(pct,1),"kd":kd})
        print(f"{pair:7s} {N} {k} {am} {rr}  {rp:6.2f} {arr.mean():8.2f} {p95:7.2f} {pct:7.1f} {kd}")
    (lab/"reports"/"PLACEBO_D1.json").write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding="utf-8")

