import sys,json,numpy as np
sys.path.insert(0,'..'); import kmc_model as km
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":13,"axes.spines.top":False,"axes.spines.right":False,"savefig.dpi":200})
c0=json.load(open('calib.json')); d=json.load(open('apply.json')); PN=d['params']; TGT=tuple(d['tgt']); X0=tuple(d['x0'])
BL="#1D5B8F"; OR="#C8572A"; AM="#B7791F"; GR="#2E7D4F"; GY="#7A8290"
# F1 rocket
r=c0['rocket']; n=np.arange(1,9)
fig,ax=plt.subplots(figsize=(8,4.2))
ax.bar(n,r['p_post'],color="#D9E3EE",edgecolor=BL,label=r"fitted failure probability (posterior median $\lambda_T$)")
ax.plot(n,r['p_mle'],"--",color=GY,label=r"data only (MLE $\lambda_T$)")
for i in range(8):
    if i<7: ax.plot(n[i],1.05,"x",color=OR,ms=11,mew=3)
    else: ax.plot(n[i],1.05,"o",color=GR,ms=11)
ax.set_xticks(n,[f"{i}\nK={k:.2f}" for i,k in zip(n,r['K'])]); ax.set_ylim(0,1.12); ax.set_ylabel("P(failure) of one flight")
ax.text(0.6,1.09,"observed:  × failure   ● success",fontsize=11,color="#333")
ax.legend(frameon=False,fontsize=10.5,loc="lower left"); fig.tight_layout(); fig.savefig("t_rocket.png"); plt.close(fig)
# F2 fits
fig,a=plt.subplots(1,4,figsize=(16,4))
e=c0['E1']; c=np.array(e['c']); K=np.array(e['K']); cc=np.linspace(0,4.2,50)
a[0].plot(c,K,"o",color=BL); a[0].plot(cc,1-(1-e['K0fit'])*np.exp(-e['rE']*cc),color=BL); a[0].set_title(r"(a) Separate-effects campaign"+"\n"+r"$r_E$ = %.3f /BU"%e['rE'],fontsize=12); a[0].set_xlabel("cost (BU)"); a[0].set_ylabel("K")
s=c0['S_rate']; c=np.array(s['c']); K=np.array(s['K']); cc=np.linspace(0,3.5,50)
a[1].plot(c,K,"o",color=BL); a[1].plot(cc,s['Kbar']-(s['Kbar']-0.20)*np.exp(-s['rS']*cc),color=BL); a[1].axhline(s['Kbar'],ls=":",color=GY); a[1].set_title(r"(b) CFD campaign, rate"+"\n"+r"$r_S$ = %.2f /BU"%s['rS'],fontsize=12); a[1].set_xlabel("cost (BU)"); a[1].set_ylabel("K")
q=c0['S_ceiling']; M=np.array(q['M']); K=np.array(q['K']); mm=np.linspace(0,0.8,10)
a[2].plot(M,K,"s",color=BL); a[2].plot(mm,q['kb']+q['kl']*mm,color=BL); a[2].set_title("(c) Simulation ceiling\n"+r"$\bar K$ = %.2f + %.2f $M$"%(q['kb'],q['kl']),fontsize=12); a[2].set_xlabel("demonstrated M"); a[2].set_ylabel("plateau K")
q=c0['T_ceiling']; K=np.array(q['K']); M=np.array(q['M']); kk=np.linspace(0.2,0.8,10)
a[3].plot(K,M,"s",color=AM); a[3].plot(kk,q['mb']+q['ml']*kk,color=AM); a[3].set_title("(d) Test ceiling\n"+r"$\bar M$ = %.2f + %.2f $K$"%(q['mb'],q['ml']),fontsize=12); a[3].set_xlabel("validated K"); a[3].set_ylabel("plateau M")
fig.tight_layout(); fig.savefig("t_fits.png"); plt.close(fig)
# F3 plane with paths
def path(pol):
    K,M=X0;c=0;pts=[(K,M,"-")]
    while not km.in_target(K,M,TGT,tol=0.005) and c<100:
        a_=pol(K,M,{}); fk,fm,_=km.rates(K,M,a_,PN); K=min(K+float(fk)*0.1,1); M=min(M+float(fm)*0.1,1); c+=0.1; pts.append((K,M,a_))
    return pts
Kn=d['Kneed']; HM=d['hmax']
def hr(K,M,h):
    hz=float(km.rates(K,M,"T",PN)[2])
    if TGT[1]-M>0 and K>=Kn and hz<=HM: return "T"
    if K<TGT[0] or K<Kn or hz>HM: return max("SET",key=lambda a_: float(km.rates(K,M,a_,PN)[0])-float(km.rates(K,M,a_,PN)[2])*PN["dK"])
    return "T"
g,V,pol,Q=km.solve_dp(p=PN,tgt=TGT); dpf=km.make_dp_policy(g,pol,Q)
fig,ax=plt.subplots(figsize=(7.6,7.0))
mm=np.linspace(0,1,50); ax.plot(np.minimum(1,PN['kb']+PN['kl']*mm),mm,":",color=BL,lw=2,label=r"simulation ceiling $\bar K(M)$")
kk=np.linspace(0,1,50); ax.plot(kk,np.minimum(1,PN['mb']+PN['ml']*kk),":",color=AM,lw=2,label=r"test ceiling $\bar M(K)$")
ax.add_patch(plt.Rectangle((TGT[0],TGT[1]),1-TGT[0],1-TGT[1],color=GR,alpha=0.15)); ax.text(0.87,0.9,"target",color=GR,ha="center")
ax.axvline(Kn,color=GY,ls="--",lw=1.2); ax.text(Kn-0.01,0.03,r"$K_{need}$ = %.3f"%Kn,rotation=90,ha="right",color=GY,fontsize=11)
ax.axvline(d['Khaz'],color=OR,ls="--",lw=1.2); ax.text(d['Khaz']+0.01,0.03,r"$K_{haz}$ = %.3f"%d['Khaz'],rotation=90,color=OR,fontsize=11)
pd=path(dpf); ax.plot([p[0] for p in pd],[p[1] for p in pd],"-",color="#999",lw=6,alpha=0.5,label="optimal (DP)")
ph=path(hr); col={"S":BL,"E":"#2A9D8F","T":AM}
for a_ in "SET":
    xs=[p[0] if p[2]==a_ else np.nan for p in ph]; ys=[p[1] if p[2]==a_ else np.nan for p in ph]
    ax.plot(xs,ys,"-",color=col[a_],lw=3,label={"S":"S","E":"E · separate-effects tests","T":"T · integrated tests"}[a_] if a_!="S" else None)
ax.plot(*X0,"ko"); ax.text(X0[0]+0.01,X0[1]-0.045,"start (0.20, 0.10)",fontsize=11)
sw=[p for p in ph if p[2]=="T"][0]; ax.plot(sw[0],sw[1],"s",color=OR,ms=9); ax.text(sw[0]-0.02,sw[1]+0.03,"switch to T\n14.8 BU",ha="right",fontsize=11,color=OR)
ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_xlabel("validated knowledge K"); ax.set_ylabel("evidence-backed maturity M"); ax.legend(frameon=False,fontsize=10.5,loc="upper left")
fig.tight_layout(); fig.savefig("t_plane.png"); plt.close(fig)
# F4 realized run
rng=np.random.default_rng(d['run']['seed']); c,sh,tr=km.simulate(hr,p=PN,tgt=TGT,x0=X0,rng=rng,record=True)
C=[];K=[];M=[];A=[];shock_at=None
for i,t in enumerate(tr):
    if t[3].endswith("!"):
        cp=tr[i-1][0]; shock_at=cp
        C+= [cp, t[0]]; K+=[t[1],t[1]]; M+=[t[2],t[2]]; A+=["X","X"]
    else:
        C.append(t[0]); K.append(t[1]); M.append(t[2]); A.append(t[3])
C=np.array(C);K=np.array(K);M=np.array(M)
fig,ax=plt.subplots(figsize=(10,4.6))
ax.plot(C,K,color=BL,lw=2.5,label="K"); ax.plot(C,M,color=AM,lw=2.5,label="M")
ax.axvspan(shock_at,shock_at+2.1,color=OR,alpha=0.12); ax.text(shock_at+0.2,0.13,"shock at %.1f BU\n+2 BU rework"%shock_at,color=OR,fontsize=11)
ax.axhline(d['Khaz'],color=OR,ls="--",lw=1); ax.text(C[-1]+0.3,d['Khaz']+0.005,r"$K_{haz}$",color=OR,fontsize=11,va="bottom")
ax.axhline(0.8,color=GR,ls=":",lw=1); ax.text(C[-1]+0.3,0.79,r"$M_{req}$",color=GR,fontsize=11,va="top")
for i in range(1,len(C)):
    a_=A[i][0]; ax.axvspan(C[i-1],C[i],ymin=0,ymax=0.03,color={"S":BL,"E":"#2A9D8F","T":AM,"X":OR}[a_],lw=0)
ax.set_xlabel("cumulative cost (BU)"); ax.set_ylabel("score"); ax.set_ylim(0,1); ax.set_xlim(0,C[-1]+2.5); ax.legend(frameon=False,loc="upper left",bbox_to_anchor=(0.0,0.75))
ax.text(0.2,0.05,"bar: E (teal), T (amber), rework (red)",fontsize=10,color=GY)
fig.tight_layout(); fig.savefig("t_run.png"); plt.close(fig)
print("ok", c, shock_at)
