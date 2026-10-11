"""Restricted EOL80 replacement timing proxy, exact predictive integrals."""
import numpy as np
from scipy.special import ndtr,log_ndtr

def opportunities(l,h,delta):
    return np.unique(np.r_[np.arange(l,h+1,delta),h]).astype(float)

def timing_loss(action,time,l,h,rho):
    u=np.minimum(time+l,h);a=np.minimum(action,h)
    return (np.maximum(u-a,0)+rho*np.maximum(a-u,0))/(h-l)

def integral_survival(pred,points):
    """Integral from zero to each residual point, including exact step breaks."""
    points=np.asarray(points,float);out=np.zeros((len(pred['risk_score']),len(points)))
    if pred['kind']=='lognormal':
        mu=pred['mu'][:,None];sigma=pred['sigma'];t=points[None,:]
        positive=t>0;logt=np.log(np.maximum(t,1e-300));z=(logt-mu-sigma**2)/sigma
        out=np.exp(np.minimum(mu+sigma**2/2+log_ndtr(z),700))+t*ndtr((mu-logt)/sigma)
        return np.where(positive,out,0)
    grid=np.asarray(pred['grid']);v=pred['survival']
    for j,t in enumerate(points):
        breaks=np.r_[0,grid[(grid>0)&(grid<t)],t]
        mids=(breaks[:-1]+breaks[1:])/2;ix=np.searchsorted(grid,mids,side='right')-1
        sv=np.ones((len(v),len(ix)));valid=ix>=0;sv[:,valid]=v[:,ix[valid]]
        out[:,j]=sv@np.diff(breaks)
    return out

def distribution_action(pred,l,h,rho,delta):
    a=opportunities(l,h,delta);j=integral_survival(pred,a-l);jh=j[:,-1,None]
    losses=(jh-j+rho*((a-l)[None,:]-j))/(h-l)
    # Ties within numerical roundoff favor the earlier opportunity.
    best=np.min(losses,axis=1)
    index=np.argmax(losses<=best[:,None]+1e-12,axis=1)
    return a[index]

def censor_weights(time,event,h):
    """Marginal censor KM, events use G(Y-), H coverage uses G(H)."""
    unique,inv,count=np.unique(time,return_inverse=True,return_counts=True)
    n=len(time)-np.r_[0,np.cumsum(count)[:-1]]
    dc=np.bincount(inv,weights=(~event).astype(float),minlength=len(unique))
    after=np.cumprod(1-dc/n);before=np.r_[1.,after[:-1]]
    pos=np.searchsorted(unique,h,side='right')-1;gh=1. if pos<0 else after[pos]
    cases=event&(time<=h);covered=(time>=h)&~cases
    if (covered.any() or (~(cases|covered)).any()) and gh<.1:return None,'censor_survival_at_H_below_0.10'
    if np.any(before[inv[cases]]<.1):return None,'event_censor_survival_below_0.10'
    w=np.zeros(len(time));w[cases]=1/before[inv[cases]];w[covered]=1/max(gh,1e-300)
    if not np.any(w):return None,'no_known_restricted_outcomes'
    return w,'OK'

def mean_loss(action,time,event,l,h,rho):
    w,reason=censor_weights(time,event,h-l)
    if w is None:return None,reason
    return float(np.mean(w*timing_loss(action,time,l,h,rho))),reason

def median_action(pred,median,l,h,delta,fixed):
    grid=opportunities(l,h,delta);available=np.isfinite(median)
    result=np.full(len(median),fixed,dtype=float)
    result[available]=grid[np.argmin(abs(grid[None,:]-median[available,None]),axis=1)]
    return result,int((~available).sum())
