"""Compare v6.2 B0 fields with frozen round-3 and round-4 audits."""
import csv, json
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
def read(p):
    with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def key(r): return tuple(r[k] for k in ('landmark','domain' if 'domain' in r else 'source','H','rho','delta'))
new={key(r):r for r in read(HERE/'replacement_metrics.csv') if r['policy']=='B0'}
r3={key(r):r for r in read(ROOT/'review_round3_20261010/b0_before_after_all_scenarios.csv')}
r4={key(r):r for r in read(ROOT/'review_round4_20261010/results_002/b0_feasibility_audit.csv')}
assert len(new)==len(r3)==len(r4)==504
rows=[]
for k in sorted(new):
    n=new[k]
    vals={'planned_action':float(n['mean_planned_cycle']),'effective_action':float(n['mean_effective_cycle']),'maintenance_flag':int(float(n['maintenance_count'])>0),'loss':n['loss']}
    for source,audit,fields in [('round3',r3,{'planned_action':'corrected_action','effective_action':'corrected_action','maintenance_flag':None,'loss':'corrected_loss'}),('round4',r4,{'planned_action':'corrected_planned_action','effective_action':'corrected_effective_action','maintenance_flag':'corrected_maintenance_flag','loss':'recomputed_corrected_loss'})]:
        for field,col in fields.items():
            av='' if col is None else audit[k].get(col,''); nv=str(vals[field])
            ok='' if av=='' or nv=='' else (abs(float(nv)-float(av))<1e-10)
            rows.append({'landmark':k[0],'domain':k[1],'H':k[2],'rho':k[3],'delta':k[4],'field':field,'audit':source,'v6_2':nv,'audit_value':av,'matches':ok})
with open(HERE/'b0_round3_round4_comparison.csv','w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
summary={}
for source in ('round3','round4'):
  summary[source]={}
  for field in ('planned_action','effective_action','maintenance_flag','loss'):
    rr=[x for x in rows if x['audit']==source and x['field']==field and x['audit_value']!='']
    summary[source][field]={'common_support':len(rr),'mismatches':sum(str(x['matches'])=='False' for x in rr)}
(HERE/'b0_round3_round4_comparison.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
