import numpy as np, json
from scipy.optimize import minimize_scalar
out={}
# ---- 1. Rocket R (fictional): 8 flights, 2014-2024, first success on flight 8
cf=2.0
K=np.array([0.10,0.16,0.21,0.27,0.32,0.37,0.42,0.47])   # assessed K before each flight
y=np.array([0,0,0,0,0,0,0,1])                           # 1 = success
def nll(lam):
    p=1-np.exp(-lam*(1-K)**2*cf)
    return -np.sum(np.where(y==0,np.log(p),np.log(1-p)))
r=minimize_scalar(nll,bounds=(0.01,20),method="bounded"); lam_mle=r.x
# prior from public data (FAA): lognormal median 0.90, sigma 0.5 ; posterior on grid
g=np.linspace(0.05,8,4000)
logprior=-0.5*((np.log(g)-np.log(0.9))/0.5)**2-np.log(g)
loglik=np.array([-nll(l) for l in g])
post=np.exp(logprior+loglik-np.max(logprior+loglik)); post/=np.trapezoid(post,g)
cdf=np.cumsum(post)*(g[1]-g[0])
med=g[np.searchsorted(cdf,0.5)]; lo=g[np.searchsorted(cdf,0.05)]; hi=g[np.searchsorted(cdf,0.95)]
out["rocket"]=dict(K=K.tolist(),lam_mle=lam_mle,lam_post_med=med,lam_post_90=[lo,hi])
p_mle=1-np.exp(-lam_mle*(1-K)**2*cf); p_post=1-np.exp(-med*(1-K)**2*cf)
out["rocket"]["p_mle"]=p_mle.tolist(); out["rocket"]["p_post"]=p_post.tolist()
# per-flight knowledge gain -> e_T : dK = e_T (1-K) cf
dK=np.diff(K); x=(1-K[:-1])*cf
eT=float(np.sum(dK*x)/np.sum(x*x)); out["rocket"]["eT"]=eT
# ---- 2. Engine separate-effects campaign E-1: K(c)=1-(1-K0)exp(-rE c)
c=np.array([0,1,2,3,4.]); KE=np.array([0.30,0.37,0.43,0.48,0.53])
yv=np.log(1-KE); A=np.vstack([np.ones_like(c),c]).T; b=np.linalg.lstsq(A,yv,rcond=None)[0]
out["E1"]=dict(c=c.tolist(),K=KE.tolist(),rE=-b[1],K0fit=1-np.exp(b[0]))
# ---- 3. CFD validation campaigns: plateau K vs demonstrated M -> kb, kl
Mp=np.array([0.10,0.30,0.50,0.70]); Kp=np.array([0.47,0.57,0.71,0.82])
A=np.vstack([np.ones_like(Mp),Mp]).T; kb,kl=np.linalg.lstsq(A,Kp,rcond=None)[0]
out["S_ceiling"]=dict(M=Mp.tolist(),K=Kp.tolist(),kb=kb,kl=kl)
# simulation rate: K(c)=Kbar-(Kbar-K0)exp(-rS c), Kbar=0.46 (M=0.10)
cs=np.array([0,1,2,3.]); Ks=np.array([0.20,0.27,0.32,0.36]); Kb=kb+kl*0.10
yv=np.log(Kb-Ks); A=np.vstack([np.ones_like(cs),cs]).T; b=np.linalg.lstsq(A,yv,rcond=None)[0]
out["S_rate"]=dict(c=cs.tolist(),K=Ks.tolist(),Kbar=Kb,rS=-b[1])
# ---- 4. Integrated ground-test campaigns: M plateau vs K -> mb, ml ; rT from approach
Kq=np.array([0.30,0.45,0.60,0.75]); Mq=np.array([0.36,0.53,0.67,0.84])
A=np.vstack([np.ones_like(Kq),Kq]).T; mb,ml=np.linalg.lstsq(A,Mq,rcond=None)[0]
out["T_ceiling"]=dict(K=Kq.tolist(),M=Mq.tolist(),mb=mb,ml=ml)
ct=np.array([0,1,2,3.]); Mt=np.array([0.10,0.20,0.28,0.34]); Mb=mb+ml*0.50
yv=np.log(Mb-Mt); b=np.linalg.lstsq(np.vstack([np.ones_like(ct),ct]).T,yv,rcond=None)[0]
out["T_rate"]=dict(c=ct.tolist(),M=Mt.tolist(),K=0.50,Mbar=Mb,rT=-b[1])
print(json.dumps(out,indent=1,default=float))
json.dump(out,open("calib.json","w"),indent=1,default=float)
