import sys,json,numpy as np
sys.path.insert(0,'..'); import kmc_model as km
d=json.load(open('apply.json')); c0=json.load(open('calib.json'))
PN=d['params']; TGT=tuple(d['tgt']); X0=tuple(d['x0']); HMAX=d['hmax']; Kn=d['Kneed']
def pol(K,M,h):
    hz=float(km.rates(K,M,"T",PN)[2])
    if TGT[1]-M>0 and K>=Kn and hz<=HMAX: return "T"
    if K<TGT[0] or K<Kn or hz>HMAX:
        return max("SET",key=lambda a: float(km.rates(K,M,a,PN)[0])-float(km.rates(K,M,a,PN)[2])*PN["dK"])
    return "T"
rng=np.random.default_rng(d['run']['seed']); c,sh,tr=km.simulate(pol,p=PN,tgt=TGT,x0=X0,rng=rng,record=True)
expo=0.0; nT=0; shT=0
for (c1,K1,M1,a1),(c2,K2,M2,a2) in zip(tr[:-1],tr[1:]):
    if a2.startswith("T"): expo+=(1-K1)**2*0.1; nT+=1; shT+=a2.endswith("!")
# prior: rocket posterior (recompute grid) ; likelihood Poisson(shT | lam*expo)
cf=2.0; K=np.array(c0['rocket']['K']); y=np.array([0]*7+[1])
g=np.linspace(0.05,8,4000)
def ll_rocket(l): p=1-np.exp(-l*(1-K)**2*cf); return np.sum(np.where(y==0,np.log(p),np.log(1-p)))
lp=-0.5*((np.log(g)-np.log(0.9))/0.5)**2-np.log(g)+np.array([ll_rocket(l) for l in g])
lp2=lp+shT*np.log(g*expo)-g*expo
def summ(lp):
    w=np.exp(lp-lp.max()); w/=w.sum(); cd=np.cumsum(w)
    return [float(g[np.searchsorted(cd,q)]) for q in (0.05,0.5,0.95)]
out=dict(T_BU=nT*0.1,shocks_T=int(shT),exposure=expo,before=summ(lp),after=summ(lp2))
print(out); json.dump(out,open('update.json','w'))
