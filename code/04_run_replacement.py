"""Nested family selection and a fully specified replacement-timing proxy."""
import itertools
import json
import numpy as np
from common import HERE,write,dump
from model_bank import Bank,MODELS
from decision_contract import opportunities,distribution_action,median_action,mean_loss,timing_loss,censor_weights

SCENARIOS=list(itertools.product((500,1000,1500),(1,2,4,8),(25,50,100)))

def validation(bank,train):
    result={}
    for v in train:
        fitting=[d for d in train if d!=v]
        # The validation source is excluded both from fit and hyperparameter selection.
        predictions=bank.chosen(fitting)
        result[v]=dict(predictions={m:bank.subset(p,v) for m,p in predictions.items()},
            scores={m:bank.score(p,v) for m,p in predictions.items()},fitting=fitting)
    return result

def select(bank,train,validation,h,rho,delta):
    eligible=[];losses={};fixed={};metric_sources=[]
    a=opportunities(bank.l,h,delta)
    for v,r in validation.items():
        mask=bank.domain==v;t=bank.time[mask];e=bank.event[mask]
        if any(h-bank.l>=p['source_max_followup'] or not p['fitted'] for p in r['predictions'].values()):continue
        w,reason=censor_weights(t,e,h-bank.l)
        if w is None:continue
        eligible.append(v)
        fixed[v]=np.mean(w[:,None]*timing_loss(a[None,:],t[:,None],bank.l,h,rho),axis=0)
        losses[v]={m:mean_loss(distribution_action(p,bank.l,h,rho,delta),t,e,bank.l,h,rho)[0] for m,p in r['predictions'].items()}
        if all(r['scores'][m]['ibs'] is not None and r['scores'][m]['all_event_medians'] for m in MODELS):metric_sources.append(v)
    b1=float(a[np.argmin(np.mean([fixed[v] for v in eligible],axis=0))]) if eligible else None
    rules={k:None for k in ('S_M','S_I','S_D')}
    values={}
    if metric_sources:
        for rule,key in [('S_M','medape'),('S_I','ibs'),('S_D','decision')]:
            values[rule]={m:float(np.mean([losses[v][m] if key=='decision' else validation[v]['scores'][m][key] for v in metric_sources])) for m in MODELS}
            rules[rule]=min(MODELS,key=lambda m:values[rule][m])
    return b1,rules,eligible,metric_sources,values

rows=[];selectors=[];contrasts=[];disagreements=[];memberships=[];all_actions=[]
for l in (50,100):
    bank=Bank(l)
    for target in (*bank.b.DOMAINS,'ISEA'):
        train=[d for d in bank.b.DOMAINS if d!=target]
        val=validation(bank,train);preds=bank.chosen(train)
        mask=bank.domain==target;t=bank.time[mask];e=bank.event[mask];n=len(t)
        for h,rho,delta in SCENARIOS:
            b1,rules,eligible,common,values=select(bank,train,val,h,rho,delta)
            prefix=dict(landmark=l,domain=target,H=h,rho=rho,delta=delta,n_target=n,n_events_before_H=int(sum(e&(t+l<=h))))
            supported=b1 is not None and all(h-l<p['source_max_followup'] and p['fitted'] for p in preds.values())
            weights,reason=censor_weights(t,e,h-l)
            if not supported:reason='source_prediction_or_validation_support'
            # B0 is a fixed 1000-cycle reference mapped to the nearest feasible
            # opportunity for this (L,H,delta) grid. np.argmin on sorted
            # opportunities makes an exact tie choose the earlier opportunity.
            b0_grid=opportunities(l,h,delta)
            b0=float(b0_grid[np.argmin(np.abs(b0_grid-1000.))])
            policies={'B0':np.full(n,b0)};fallbacks={'B0':0}
            if supported:
                policies['B1']=np.full(n,b1);fallbacks['B1']=0
                for m,p in preds.items():
                    q=bank.subset(p,target);policies[f'Pd_{m}']=distribution_action(q,l,h,rho,delta);fallbacks[f'Pd_{m}']=0
                    med=bank.b.median_residual(q)+l
                    policies[f'Pm_{m}'],fallbacks[f'Pm_{m}']=median_action(q,med,l,h,delta,b1)
                policies['B2']=policies['Pd_km'].copy();fallbacks['B2']=0
                for rule,m in rules.items():
                    if m is not None:policies[rule]=policies[f'Pd_{m}'].copy();fallbacks[rule]=0
            for rule,m in rules.items():
                selectors.append(dict(**prefix,rule=rule,selected_model=m,status='VERIFIED' if m is not None else 'NOT_ESTIMABLE',
                     common_sources=';'.join(common),decision_validation_sources=';'.join(eligible),B1_cycle=b1,
                     selection_values=json.dumps(values.get(rule,{}),sort_keys=True)))
            valid=bool(supported and weights is not None)
            for policy,action in policies.items():
                loss=timing_loss(action,t,l,h,rho)
                u=np.minimum(t+l,h);eff=np.minimum(action,h);known=(e&(t+l<=h))|(t+l>=h)
                rows.append(dict(**prefix,policy=policy,loss=float(np.mean(weights*loss)) if valid else None,
                    early_cycles=float(np.mean(weights*np.maximum(u-eff,0))) if valid else None,
                    late_cycles=float(np.mean(weights*np.maximum(eff-u,0))) if valid else None,
                    late_rate=float(np.mean(weights*(eff>u))) if valid else None,
                    late_known_count=int(sum(known&(eff>u))),known_outcomes=int(sum(known)),
                    maintenance_count=int(sum(action<=h)),fallback_count=fallbacks[policy],
                    mean_planned_cycle=float(action.mean()),mean_effective_cycle=float(eff.mean()),
                    support_reason='OK' if valid else reason,estimator='direct_complete_events' if e.all() else 'marginal_censor_KM_IPCW'))
                for i,a0 in enumerate(action):all_actions.append(dict(**prefix,cell_id=bank.ids[np.flatnonzero(mask)[i]],policy=policy,
                     planned_cycle=float(a0),effective_cycle=float(min(a0,h)),maintenance_in_window=int(a0<=h)))
            for a0,z in itertools.combinations(('S_M','S_I','S_D'),2):
                disagreements.append(dict(**prefix,contrast=f'{a0}_vs_{z}',model_disagreement=int(rules[a0]!=rules[z]) if rules[a0] and rules[z] else None,
                    action_disagreements=int(sum(policies[a0]!=policies[z])) if a0 in policies and z in policies else None))
            if valid:
                names=list(policies);action=np.array([policies[k] for k in names]);loss=np.array([timing_loss(a,t,l,h,rho) for a in action])
                point=np.mean(loss*weights,axis=1)
                rng=np.random.default_rng(20261008);draws=[]
                for _ in range(2000):
                    idx=rng.integers(0,n,n);w,why=censor_weights(t[idx],e[idx],h-l)
                    if w is not None:draws.append(np.mean(loss[:,idx]*w,axis=1))
                draws=np.array(draws)
                comparisons=[(k,base) for k in names if k not in ('B0','B1','B2','Pd_km') for base in ('B0','B1','B2')]
                comparisons += [(a0,z) for a0,z in [('S_D','S_I'),('S_D','S_M')] if a0 in names and z in names]
                for a0,z in comparisons:
                    ai=names.index(a0);zi=names.index(z);diff=draws[:,ai]-draws[:,zi]
                    contrasts.append(dict(**prefix,contrast=f'{a0}_minus_{z}',difference=float(point[ai]-point[zi]),
                        low=float(np.quantile(diff,.025)) if len(diff) else None,high=float(np.quantile(diff,.975)) if len(diff) else None,
                        relative_pct=float(100*(point[ai]/point[zi]-1)) if point[zi]>0 else None,
                        valid_draws=len(diff),total_draws=2000,classification='primary' if a0=='S_D' and z in ('S_I','S_M') else 'exploratory_pointwise'))
        memberships.extend(dict(landmark=l,outer_target=target,fit_id=k,**v) for k,v in bank.memberships.items() if target not in v['train_sources'])
        print('P4 replacement scenarios finished',l,target,flush=True)
        # Persist completed blocks so long runs have auditable progress.
        write('replacement_metrics.csv',rows);write('selection_results.csv',selectors);write('replacement_pairwise_bootstrap.csv',contrasts)
        write('selection_disagreements.csv',disagreements);write('replacement_actions.csv',all_actions)
dump('replacement_protocol.json',dict(status='VERIFIED',analysis='post hoc exploratory; ISEA previously examined',
    loss='((min(T,H)-min(A,H))_+ + rho*(min(A,H)-min(T,H))_+)/(H-L)',
    parameters=dict(landmarks=[50,100],H=[500,1000,1500],rho=[1,2,4,8],delta=[25,50,100]),
    B0='nearest feasible opportunity to 1000; earlier opportunity on ties',B1='source-validation fixed-cycle minimum',B2='identical to Pd_KM',
    Pm='nearest common opportunity; missing median uses B1 with fallback count',Pd='exact survival-integral minimum; numerical ties earlier',
    oracle='a=min(T,H) loss zero; evaluation lower bound only, not fitted or selectable',
    model_order=list(MODELS),selector='equal-source criterion on common estimable source intersection for all three rules',
    nested_label_isolation='outer target excluded; inner validation source excluded from both fit and source-only hyperparameter tuning',
    censoring='marginal reverse KM; independent censoring within source assumed; G(Y-) and G(H), floor .10; incomplete U not imputed',
    bootstrap='2000 paired target-cell draws; frozen models and selected families; weights reestimated; pointwise conditional intervals',
    memberships=memberships,physical_cost_or_derating_claim=False))
