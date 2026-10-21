import sys, json, numpy as np
sys.path.insert(0,'..')
import kmc_model as km
from scipy.ndimage import map_coordinates
PN=dict(km.P); PN.update(kb=.40,kl=.60,mb=.05,ml=1.05,rS=.30,rE=.10,eE=.05,rT=.24,eT=.035,lamE=.05,lamT=1.5,dK=.06,dM=.15,rework=2.0)
TGT=(0.75,0.80); X0=(0.20,0.10); HMAX=0.05
out={"params":PN,"x0":X0,"tgt":TGT,"hmax":HMAX}
Kn=km.K_need(PN,TGT); Khaz=1-np.sqrt(HMAX/PN["lamT"]); out["Kneed"]=Kn; out["Khaz"]=Khaz
g,V,pol,Q=km.solve_dp(p=PN,tgt=TGT)
n=len(g)
def Vi(K,M): return float(map_coordinates(V,[[np.clip(K,0,1)*(n-1)],[np.clip(M,0,1)*(n-1)]],order=1,mode="nearest")[0])
out["V_x0"]=Vi(*X0)
# decision derivative at x0 (finite differences on V)
def D(K,M,a,h=0.01):
    dVK=(Vi(K+h,M)-Vi(K-h,M))/(2*h); dVM=(Vi(K,M+h)-Vi(K,M-h))/(2*h)
    fk,fm,hz=km.rates(K,M,a,PN); fk,fm,hz=float(fk),float(fm),float(hz)
    loss=hz*(PN["rework"]+Vi(K-PN["dK"],M-PN["dM"])-Vi(K,M))
    return dict(dVdK=dVK,dVdM=dVM,F=fk,G=fm,haz=hz,loss=loss,D=-(dVK*fk+dVM*fm)-loss)
out["D_x0"]={a:D(*X0,a) for a in "SET"}
out["D_mid"]={a:D(0.60,0.25,a) for a in "SET"}
# expected (no-shock) trajectory of the headroom procedure, logging every 2 BU
def pol_hr(K,M,h):
    hz=float(km.rates(K,M,"T",PN)[2])
    if TGT[1]-M>0 and K>=Kn and hz<=HMAX: return "T"
    if K<TGT[0] or K<Kn or hz>HMAX:
        return max("SET",key=lambda a: float(km.rates(K,M,a,PN)[0])-float(km.rates(K,M,a,PN)[2])*PN["dK"])
    return "T"
K,M=X0; c=0.0; dc=0.1; log=[]; nxt=0.0; seq=[]
while not km.in_target(K,M,TGT,tol=0.005) and c<100:
    a=pol_hr(K,M,{})
    if not seq or seq[-1][0]!=a: seq.append([a,round(c,1),round(K,3),round(M,3)])
    if c>=nxt-1e-9:
        r={b:[float(x) for x in km.rates(K,M,b,PN)] for b in "SET"}
        log.append(dict(c=round(c,1),K=K,M=M,Kbar=float(km.Kbar(M,PN)),Mbar=float(km.Mbar(K,PN)),
            rates=r,net={b:r[b][0]-r[b][2]*PN["dK"] for b in "SET"},hazT=r["T"][2],choice=a)); nxt+=2.0
    fk,fm,_=km.rates(K,M,a,PN); K=min(K+float(fk)*dc,1); M=min(M+float(fm)*dc,1); c+=dc
out["hr_det"]=dict(cost=c,end=[K,M],switches=seq,log=log)
# DP expected path switches
dpf=km.make_dp_policy(g,pol,Q); K,M=X0;c=0;seq=[]
while not km.in_target(K,M,TGT,tol=0.005) and c<100:
    a=dpf(K,M,{}); 
    if not seq or seq[-1][0]!=a: seq.append([a,round(c,1),round(K,3),round(M,3)])
    fk,fm,_=km.rates(K,M,a,PN); K=min(K+float(fk)*dc,1); M=min(M+float(fm)*dc,1); c+=dc
out["dp_det"]=dict(cost=c,switches=seq)
# Monte Carlo
pols={"Optimal (DP)":dpf,"Headroom procedure":pol_hr,
 "Analysis-first":lambda K,M,h: km.policy_analysis_first(K,M,h,p=PN,tgt=TGT),
 "Test-first":lambda K,M,h: km.policy_test_first(K,M,h,p=PN,tgt=TGT),
 "Fixed alternation":km.policy_spiral,
 "Naive slope":lambda K,M,h: km.policy_slope(K,M,h,p=PN,tgt=TGT)}
mc={}
for k,f in pols.items():
    rng=np.random.default_rng(7); r=np.array([km.simulate(f,p=PN,tgt=TGT,x0=X0,rng=rng) for _ in range(1000)])
    mc[k]=dict(mean=float(r[:,0].mean()),p90=float(np.percentile(r[:,0],90)),shocks=float(r[:,1].mean()),nr=float(np.mean(r[:,0]>=200)))
out["mc"]=mc
# one realized run with a shock
for s in range(200):
    rng=np.random.default_rng(s); c,sh,tr=km.simulate(pol_hr,p=PN,tgt=TGT,x0=X0,rng=rng,record=True)
    if sh==1: break
ev=[t for t in tr if t[3].endswith("!")]
segs=[];prev=None
for t in tr[1:]:
    a=t[3]
    if a!=prev: segs.append([a,round(t[0],1),round(t[1],3),round(t[2],3)]); prev=a
out["run"]=dict(seed=s,cost=c,shocks=sh,events=[[round(e[0],1),round(e[1],3),round(e[2],3),e[3]] for e in ev],segs=segs)
json.dump(out,open("apply.json","w"),indent=1,default=float)
print(json.dumps({k:out[k] for k in ["Kneed","Khaz","V_x0","D_x0","D_mid","dp_det","mc","run"]},indent=1,default=float))
print(json.dumps(out["hr_det"]["switches"]),out["hr_det"]["cost"])
