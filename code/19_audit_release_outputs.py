"""Audit all v6.2 actions and all changed outputs against v6.1; no model fits."""
import csv, json, hashlib, platform, sys, subprocess
from pathlib import Path
import numpy as np
from common import HERE, ROOT
from decision_contract import opportunities
def read(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def equal(a,b):
    if a==b:return True
    if isinstance(a,dict) and isinstance(b,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,str) and isinstance(b,str) and a.startswith('{') and b.startswith('{'):
        return equal(json.loads(a),json.loads(b))
    try:return abs(float(a)-float(b))<=1e-12
    except (ValueError,TypeError):return False
old=HERE.parent/'rebuild_v6'; out=ROOT/'release_v6_2_20261010'; rows=[]; summary={}
specs=[('replacement_metrics.csv',['landmark','domain','H','rho','delta','policy']),('selection_results.csv',['landmark','domain','H','rho','delta','rule']),('replacement_pairwise_bootstrap.csv',['landmark','domain','H','rho','delta','contrast']),('selection_disagreements.csv',['landmark','domain','H','rho','delta','contrast'])]
for name,keys in specs:
    aa=read(old/name); bb=read(HERE/name); ai={tuple(a[k] for k in keys):a for a in aa}; assert len(ai)==len(aa)==len(bb)
    material=0; changed_records=set(); not_b0_material=0
    for b in bb:
        key=tuple(b[k] for k in keys); a=ai[key]
        for f in b:
            if a.get(f,'')!=b[f]:
                match=equal(a.get(f,''),b[f]); delta=''
                try:delta=float(b[f])-float(a[f])
                except (ValueError,TypeError):pass
                rows.append(dict(artifact=name,key='|'.join(key),field=f,old=a.get(f,''),new=b[f],difference=delta,material=int(not match)))
                if not match:
                    material+=1;changed_records.add(key)
                    if name=='replacement_metrics.csv' and b['policy']!='B0':not_b0_material+=1
                    if name=='replacement_pairwise_bootstrap.csv' and not b['contrast'].endswith('_minus_B0'):not_b0_material+=1
    summary[name]=dict(records=len(bb),changed_records=len(changed_records),material_field_changes=material,non_B0_material_changes=not_b0_material)
with (out/'data/all_output_field_differences.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
actions=read(HERE/'replacement_actions.csv'); b0=[r for r in actions if r['policy']=='B0']; scenarios=set(); bad=[]; changes={k:0 for k in ['planned_cycle','effective_cycle','maintenance_in_window']}
oldb={tuple(r[k] for k in ['landmark','domain','H','rho','delta','cell_id']):r for r in read(old/'replacement_actions.csv') if r['policy']=='B0'}
for r in b0:
    l,h,d=map(float,[r['landmark'],r['H'],r['delta']]); a=float(r['planned_cycle']); grid=opportunities(l,h,d); scenarios.add(tuple(r[k] for k in ['landmark','domain','H','rho','delta']))
    if a not in grid or float(r['effective_cycle'])!=a or int(r['maintenance_in_window'])!=1:bad.append(r)
    assert abs(a-1000)==np.min(abs(grid-1000))
    assert a==min(grid[abs(grid-1000)==np.min(abs(grid-1000))])
    key=tuple(r[k] for k in ['landmark','domain','H','rho','delta','cell_id'])
    for f in changes:changes[f]+=not equal(oldb[key][f],r[f])
assert len(scenarios)==504 and len(b0)==30564 and not bad
# The fresh bootstrap replay must agree, including all B0 comparisons.
fresh=read(out/'replay_002/replacement_pairwise_bootstrap.csv'); canon=read(HERE/'replacement_pairwise_bootstrap.csv')
assert len(fresh)==len(canon) and all(all(equal(a[k],b[k]) for k in a) for a,b in zip(fresh,canon))
# Historical displayed Figure 9 loss/late values are unchanged; action flags are corrected elsewhere.
display=[r for r in read(HERE/'replacement_metrics.csv') if r['domain']=='ISEA' and r['landmark']=='100' and r['delta']=='50' and r['policy'] in ['B0','B1','B2','Pd_xgb_aft','Pd_rsf']]
binding=json.loads((old/'figure9_data_binding.json').read_text()); ind={(str(x['H']),x['policy'],str(x['rho'])):x for x in binding['values']}
assert len(display)==60
assert all(equal(r['loss'],str(ind[(r['H'],r['policy'],r['rho'])]['loss'])) and int(r['late_known_count'])==ind[(r['H'],r['policy'],r['rho'])]['late_known_count'] for r in display)
receipt=dict(status='PASS',scenario_count=504,B0_cell_scenario_rows=len(b0),infeasible_B0_rows=len(bad),cell_action_field_changes=changes,output_differences=summary,bootstrap_fresh_replay_matches=True,figure9_displayed_60_values_unchanged=True,inputs={str(p.relative_to(ROOT)):sha(p) for p in [HERE/'04_run_replacement.py',HERE/'replacement_metrics.csv',HERE/'replacement_actions.csv',HERE/'replacement_pairwise_bootstrap.csv']})
(out/'qa/b0_full_output_audit.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8');print(json.dumps(receipt,indent=2))
