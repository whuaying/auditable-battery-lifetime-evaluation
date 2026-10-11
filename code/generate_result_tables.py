"""Generate v6.2 tables only from frozen aggregates; never fits a model."""
import csv,json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(name):
    with (R/'data'/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def esc(s):return str(s).replace('_',r'\_').replace('%',r'\%').replace('&',r'\&')
def fmt(x,n=1):return 'NA' if x in ('',None) else f'{float(x):.{n}f}'
def table(label,caption,headers,rows):
    return '\n'.join([r'\begin{longtable}{'+'l'*len(headers)+'}',r'\caption{'+caption+r'}\label{'+label+r'}\\',r'\toprule',' & '.join(headers)+r'\\\midrule\endfirsthead',' & '.join(headers)+r'\\\midrule\endhead',*[' & '.join(map(esc,r))+r'\\' for r in rows],r'\bottomrule\end{longtable}'])
chunks=[r'\clearpage\section*{S15. Frozen result tables for v6.2}']
calce=[x for x in read('calce_event_error_diagnostics.csv') if x['landmark']=='100' and x['target']=='CALCE' and x['family']=='lognormal_aft' and (x['mode'],x['rule']) in [('native','one'),('common','three')]]
assert len(calce)==2 and all(x['n_events']=='7' and x['n_finite']=='7' for x in calce)
chunks.append(table('tab:v62_calce','Frozen CALCE far-tail diagnostic at L100 for LN-AFT. MedAPE uses total observed endpoint cycle in its denominator. MAE and MedAE are cycle errors; Pred. R is median predicted residual life. These distinct refits do not replace the primary nine-cell three-reading benchmark.',['Cohort/rule','Events/finite','MedAPE (\\%)','MAE','MedAE','Pred. R'],[[x['mode']+'/'+x['rule'],x['n_events']+'/'+x['n_finite'],fmt(x['MedAPE']),fmt(x['MAE']),fmt(x['MedAE']),fmt(json.loads(x['predicted_residual_quantiles'])[2])] for x in calce]))
grid=read('mit_grid_confirmation_summary.csv')
chunks.append(table('tab:v62_grid','Frozen MIT confirmation and support at L100; all grids contain 124 cells. Delay is relative to the reference on commonly confirmed events. At 20 cycles no event is confirmed and delay is NA.',['Grid','Events','Rate','Censor fraction','Median delay'],[[x['grid'],x['confirmed_events']+'/'+x['n_cells'],fmt(x['confirmation_rate'],3),fmt(x['right_censor_fraction'],3),fmt(x['median_confirmation_difference'])] for x in grid]))
labels={'rsf':'RSF','cox':'Cox','xgb_aft':'XGB-AFT','lognormal_aft':'LN-AFT','km':'KM'}
def sources(x):return x.replace('CALCE','C').replace('HUST','H').replace('MIT','M').replace('XJTU','X').replace('TJU','T').replace(';',',')
select=read('grid_selection_comparison.csv')
chunks.append(r'\small C=CALCE, H=HUST, M=MIT, X=XJTU, T=TJU. Fixed and refit arms are separate; S-D below uses loss-only support. S-I original has probability-only support. S-I and S-M use their within-grid matched support.')
chunks.append(table('tab:v62_select','Frozen ISEA observation-grid family selection. Gaps retain each criterion units and are not stability probabilities. All S-D rows are separately labelled loss-only sensitivities.',['Arm','Grid','Selector','Sources','Winner','Gap'],[[('Fixed' if x['experiment']=='fixed_prediction' else 'Refit'),x['grid'],x['selector']+(' (loss)' if x['selector']=='S_D' else ''),sources(x['common_sources']),labels[x['winner']],fmt(x['margin'],5)] for x in select]))
common=read('grid_common_support_sensitivity.csv')
chunks.append(table('tab:v62_common','Frozen common-support and probability-only negative controls. The unchanged C/T/X common set excludes intervened MIT. S-D has a separate five-source loss-only set, not the three-source set used by S-I/S-M. The negative results are retained.',['Control','Grid','Selector','Sources','Winner','Gap'],[[('Probability-only' if x['contrast'].startswith('fixed_probability') else ('Loss-only' if x['selector']=='S_D' else 'Common grid')),x['grid'],x['selector'],sources(x['sources']),labels[x['winner']],fmt(x['margin'],5)] for x in common]))
diff=json.loads((R/'data/b0_reconciliation.json').read_text())['fields']
chunks.append(table('tab:v62_b0','B0 old/new audit across 504 settings. Finite old/new losses have 408 scenarios of common support and 96 NA; event support is not expanded. The complete field rows and all B0-relative paired bootstrap differences accompany the release.',['Field','Changed settings','Largest absolute change'],[[k,str(v['changed']),fmt(v['max_abs_difference'],6)] for k,v in diff.items()]))
(R/'manuscript/generated_results_v6_2.tex').write_text('\n\n'.join(chunks)+'\n',encoding='utf8')
print('generated tables',len(chunks))
