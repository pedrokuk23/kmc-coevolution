import sys, json, numpy as np
sys.path.insert(0,'..'); import kmc_model as km
d=json.load(open('apply.json')); PN=d['params']; TGT=tuple(d['tgt']); X0=tuple(d['x0'])
def mk(hmax):
    Kn=km.K_need(PN,TGT)
    def f(K,M,h):
        gM=TGT[1]-M; hz=float(km.rates(K,M,"T",PN)[2])
        if gM>0 and K>=Kn and hz<=hmax: return "T"
        if K<TGT[0] or K<Kn or hz>hmax:
            return max("SET",key=lambda a: float(km.rates(K,M,a,PN)[0])-float(km.rates(K,M,a,PN)[2])*PN["dK"])
        return "T"
    return f
res={}
for hm in [0.03,0.05,0.07,0.10]:
    f=mk(hm); rng=np.random.default_rng(7)
    r=np.array([km.simulate(f,p=PN,tgt=TGT,x0=X0,rng=rng) for _ in range(1000)])
    # deterministic
    K,M=X0;c=0;sw=[]
    while not km.in_target(K,M,TGT,tol=0.005) and c<100:
        a=f(K,M,{}); 
        if not sw or sw[-1][0]!=a: sw.append([a,round(c,1),round(K,3),round(M,3)])
        fk,fm,_=km.rates(K,M,a,PN); K=min(K+float(fk)*0.1,1); M=min(M+float(fm)*0.1,1); c+=0.1
    res[hm]=dict(mean=float(r[:,0].mean()),p90=float(np.percentile(r[:,0],90)),shocks=float(r[:,1].mean()),Khaz=1-np.sqrt(hm/PN['lamT']),det=c,sw=sw)
print(json.dumps(res,indent=0,default=float))
json.dump(res,open('variant.json','w'),default=float)
