"""Canonical six-fold fits and true six-fold source-only external tuning."""
import json
import numpy as np
from common import HERE,OLD,read,write,dump
from model_bank import Bank,MODELS
from survival_contract import brier
metrics=[];horizons=[];configs=[];memberships=[]
for l in (50,100):
    bank=Bank(l);domains=bank.b.DOMAINS
    for target in (*domains,'ISEA'):
        train=[d for d in domains if d!=target];pred=bank.chosen(train)
        for m,p in pred.items():
            assert p['fitted'],(l,target,m)
            q=bank.subset(p,target);mask=bank.domain==target;t=bank.time[mask];e=bank.event[mask]
            s=bank.score(p,target)
            metrics.append(dict(version='canonical_v6_refit',landmark=l,domain=target,model=m,n_target=len(t),n_events=int(e.sum()),
                 ibs=s['ibs'],harrell_c=s['c'],event_medape_pct=s['medape'],n_event_medians=s['n_event_medians'],grid=';'.join(map(str,s['grid']))))
            configs.append(dict(landmark=l,target=target,model=m,candidate=bank.tune(train,m),train_sources=';'.join(train),
                 validation_sources=';'.join(train),tuning='source LOOCV mean common-horizon Brier; target excluded'))
            if target!='ISEA':
                old=[r for r in read(OLD/'benchmark_predictions.csv') if int(r['landmark'])==l and r['held_out_domain']==target and r['model']==m]
                lookup={r['cell_id']:r for r in old}
                ids=[bank.ids[i].split('/',1)[1] for i in np.flatnonzero(mask)]
                error=float(np.max(abs(q['risk_score']-np.array([float(lookup[k]['risk_score']) for k in ids]))))
                assert error<1e-7,(l,target,m,'internal prediction drift',error)
            for h in bank.b.HORIZONS:
                if h<=l:continue
                risk=1-bank.b.survival_at(q,h-l);z,g,n,reason=brier(t,e,risk,h-l,q['source_max_followup'])
                horizons.append(dict(landmark=l,domain=target,model=m,horizon=h,brier=z,n_target=len(t),
                    n_events_by_horizon=int(sum(e&(t<=h-l))),n_at_risk=n,censor_survival=g,
                    mean_predicted_risk=float(risk.mean()),observed_km_risk=1-bank.b.legacy.km_survival(t,e,h-l),support_reason=reason))
        print('P2 verified fits',l,target,flush=True)
    memberships.extend(dict(landmark=l,fit_id=k,**v) for k,v in bank.memberships.items())
write('benchmark_metrics.csv',metrics);write('benchmark_horizons.csv',horizons);write('benchmark_configs.csv',configs)
dump('benchmark_protocol.json',dict(status='VERIFIED',input_fingerprints={str(l):Bank(l).fingerprint for l in (50,100)},
    historical_internal_identity='all outer prediction risk scores match within 1e-7; inputs/configuration/definition unchanged',
    external_tuning='six validation folds at each own landmark; each trains remaining five sources; all six refit once',
    fitted_model_memberships=memberships,feature_imputation='training-only median',target_outcomes_used_for_fit_or_tuning=False))
