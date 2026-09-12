import numpy as np, pandas as pd, json
from pathlib import Path


if __name__ == "__main__":
    # Bo than script vao chot nay: truoc day chi can import module la
    # chay het ca bai quet/ghi bao cao, ke ca khi nguoi goi chi muon
    # dung mot ham trong file.

    lab=Path(__file__).resolve().parent
    rd=lab.parent/"data"
    SPREAD={"AUDCAD":0.00022,"AUDCHF":0.00025,"AUDNZD":0.00026,"EURCAD":0.00020,"EURGBP":0.00026,"EURNZD":0.00030,"GBPCAD":0.00030}
    def atr(h,l,c,n=14):
        pc=np.roll(c,1); pc[0]=c[0]; tr=np.maximum(h-l,np.maximum(abs(h-pc),abs(l-pc)))
        return pd.Series(tr).ewm(alpha=1.0/n,adjust=False).mean().values
    def scan(g,N,k,am,rr,sp=0.0,start=0):
        c=g.close.values; h=g.high.values; l=g.low.values; o=g.open.values
        a=atr(h,l,c); mid=pd.Series(c).rolling(N).mean().values; sd=pd.Series(c).rolling(N).std(ddof=0).values
        lo=mid-k*sd; sig=np.flatnonzero(c < np.roll(lo,1))
        R=0.;w=0;n=0
        for i in sig:
            j=i+1
            if j>=len(c)-1 or j<start: continue
            en=o[j]; at=max(a[j],1e-9); slp=en-am*at; tpp=en+rr*am*at; e=min(j+250,len(h))
            ht=np.flatnonzero(h[j:e]>=tpp); st=np.flatnonzero(l[j:e]<=slp)
            if ht.size and (not st.size or ht[0]<st[0]): rv=rr; w+=1
            elif st.size: rv=-1.0
            else: rv=(c[e-1]-en)/(am*at)
            R+=rv-(sp/(am*at) if sp else 0.0); n+=1
        if not n: return 0.0,0.0,0,0.0
        roi=R*0.005*((len(c)-start)/1.0)
        return w/n*100, (w*rr)/max(n-w,1e-9), n, roi
    def load(pair):
        f=rd/(pair+"_M1_mq.parquet")
        df=pd.read_parquet(f); df.columns=[str(x).lower() for x in df.columns]
        df["_t"]=pd.to_datetime(df["time"],errors="coerce"); df=df.dropna(subset=["_t"]).set_index("_t")
        if "time" in df.columns: df=df.drop(columns=["time"])
        return df.resample("1d").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
    cands=[("EURCAD",20,3.0,1.5,3.0),("EURCAD",20,3.0,1.5,2.0),("GBPCAD",20,2.5,1.5,3.0),
           ("EURCAD",10,3.0,1.5,2.0),("EURNZD",20,3.0,2.0,3.0),("EURCAD",10,2.5,1.5,2.0)]
    print(f"{'cap':7s} {'N k am rr':14s} {'RAWpf':>6s} {'COSTpf':>7s} {'OOSpf':>6s} {'OOSROI%':>8s} {'VL':>3s} {'KD':6s}")
    out=[]
    for pair,N,k,am,rr in cands:
        g=load(pair); sp=SPREAD.get(pair,0.00025)
        wr,pf,n,_=scan(g,N,k,am,rr,0.0)
        cwr,cpf,cn,_=scan(g,N,k,am,rr,sp)
        split=int(len(g)*0.6)
        owr,opf,on,oro=scan(g,N,k,am,rr,sp,split)
        kd="OOS-GIU" if opf>=1.0 and cpf>=1.15 else ("LOAI" if opf<1.0 else "DU")
        out.append({"cap":pair,"N":N,"k":k,"am":am,"rr":rr,"raw_pf":round(pf,2),"cost_pf":round(cpf,2),"oos_pf":round(opf,2),"oos_roi":round(oro,2),"oos_n":on,"kd":kd})
        print(f"{pair:7s} {N} {k} {am} {rr}   {pf:6.2f} {cpf:7.2f} {opf:6.2f} {oro:8.1f} {on:3d} {kd}")
    (lab/"reports"/"XAC_NHAN_D1.json").write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding="utf-8")

