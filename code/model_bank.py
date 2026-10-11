"""Source-subset fit cache with full label isolation and versioned inputs."""
import hashlib
import itertools
import json
import pickle
import numpy as np
from common import HERE,OLD,ROOT,read,sha,benchmark
from survival_contract import brier,ibs,concordance

MODELS=('km','lognormal_aft','cox','rsf','xgb_aft')

class Bank:
    def __init__(self, landmark):
        self.l=landmark;self.b=benchmark();self.d=self.b.load(landmark)
        self.ext=[r for r in read(HERE/'external_features.csv') if int(r['landmark_cycle'])==landmark]
        self.x=np.r_[self.d['x'],np.array([[float(r[k]) if r[k] else np.nan for k in self.b.FEATURES] for r in self.ext])]
        self.domain=np.r_[self.d['domain'],np.repeat('ISEA',len(self.ext))]
        self.time=np.r_[self.d['time'],[float(r['eol80_cycle'])-landmark for r in self.ext]]
        self.event=np.r_[self.d['event'],np.ones(len(self.ext),bool)]
        self.ids=[r['dataset']+'/'+r['cell_id'] for r in self.d['rows']+self.ext]
        self.fingerprint=hashlib.sha256(json.dumps(dict(l=landmark,
            features=sha(ROOT/f'eda/rebuild_v2/landmark_{landmark}_features.csv'),external=sha(HERE/'external_features.csv'),
            library=sha(OLD/'01_residual_survival_benchmark.py'),
            production_library=sha(HERE/'production_model_library.py'),
            bank=sha(HERE/'model_bank.py'),common=sha(HERE/'common.py'),
            survival_contract=sha(HERE/'survival_contract.py'),decision_contract=sha(HERE/'decision_contract.py'),
            code_version=self.b.CODE_VERSION,environment=sha(HERE/'environment_lock.json')),
            sort_keys=True).encode()).hexdigest()
        self.cache=HERE/'cache'/self.fingerprint;self.cache.mkdir(parents=True,exist_ok=True)
        self.selection={};self.memberships={}

    def fit(self,train,model,candidate):
        train=tuple(sorted(train));assert train and 'ISEA' not in train
        name='_'.join(train)+f'_{model}_{candidate}.pkl';path=self.cache/name
        mask=np.isin(self.domain,train)
        key=hashlib.sha256('\n'.join(self.ids[i] for i in np.flatnonzero(mask)).encode()).hexdigest()
        self.memberships[name]=dict(train_sources=list(train),train_cell_key_sha256=key,n_train=int(mask.sum()),
            fitted_feature_access='training imputer/scaler only; outcomes restricted to train_sources')
        if path.exists():
            with path.open('rb') as f:p=pickle.load(f)
        else:
            p=self.b.fit_predict(model,candidate,self.x[mask],self.x,self.b.structured(self.event[mask],self.time[mask]))
            with path.open('wb') as f:pickle.dump(p,f,protocol=5)
        return self.b.validate_prediction(p)

    def subset(self,p,domain):
        mask=self.domain==domain
        return {k:v[mask] if k in ('mu','risk_score','survival') else v for k,v in p.items()}

    def score(self,p,domain):
        if not p.get('fitted',False):
            return dict(mean_brier=None,ibs=None,grid=[],medape=None,
                n_event_medians=0,all_event_medians=False,c=None,
                support_reason='unconverged_fit')
        q=self.subset(p,domain);mask=self.domain==domain;t=self.time[mask];e=self.event[mask]
        grid=[];scores=[]
        for h in self.b.HORIZONS:
            if h<=self.l:continue
            z=brier(t,e,1-self.b.survival_at(q,h-self.l),h-self.l,q['source_max_followup'])[0]
            if z is not None:grid.append(h);scores.append(z)
        med=self.b.median_residual(q)+self.l;available=np.isfinite(med[e]);truth=t[e]+self.l
        return dict(mean_brier=float(np.mean(scores)) if scores else None,ibs=ibs(grid,scores),grid=grid,
            medape=float(np.median(abs(med[e][available]-truth[available])/truth[available]*100)) if available.any() else None,
            n_event_medians=int(available.sum()),all_event_medians=bool(available.all() and e.any()),
            c=concordance(t,e,q['risk_score']))

    def tune(self,train,model):
        train=tuple(sorted(train));key=(train,model)
        if key in self.selection:return self.selection[key]
        if model=='km':self.selection[key]=None;return None
        results=[]
        for candidate in self.b.CANDIDATES[model]:
            values=[]
            for v in train:
                fitting=[d for d in train if d!=v];assert v not in fitting
                p=self.fit(fitting,model,candidate);s=self.score(p,v)['mean_brier']
                values.append(s if p['fitted'] and s is not None else np.inf)
            results.append(float(np.mean(values)))
        if not np.isfinite(results).any():raise RuntimeError(f'No supported candidate: {self.l}/{train}/{model}')
        chosen=self.b.CANDIDATES[model][int(np.argmin(results))];self.selection[key]=chosen
        return chosen

    def chosen(self,train):
        return {m:self.fit(train,m,self.tune(train,m)) for m in MODELS}
