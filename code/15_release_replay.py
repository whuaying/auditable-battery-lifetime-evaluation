"""Clean, append-only production replay; never writes historical result files.

python eda/rebuild_v6_2/15_release_replay.py --output-dir release_v6_2_20261010/replay_003
The output directory must not exist. All affected model fits bypass old caches.
"""
import argparse
import contextlib
import csv
import hashlib
import importlib.metadata as meta
import json
import platform
import runpy
import sys
import unittest
import os
import subprocess
from pathlib import Path
import common
import model_bank

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
    with Path(p).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))
def dump(p, d):
    with Path(p).open('x', encoding='utf8') as f:
        json.dump(d, f, indent=2, allow_nan=False, default=lambda x:x.item())

def compare(old, new, keys, fields, tolerance=0.):
    aa, bb = read(old), read(new)
    index = {tuple(r[k] for k in keys):r for r in bb}
    assert len(index) == len(bb) == len(aa), (old, 'record count or duplicate key')
    changes = []
    for a in aa:
        key = tuple(a[k] for k in keys); b = index[key]
        for f in fields:
            if a[f] != b[f]:
                delta = abs(float(a[f])-float(b[f])) if a[f] and b[f] else None
                changes.append(dict(key=key, field=f, old=a[f], new=b[f],
                    absolute_delta=delta, material=delta is None or delta>tolerance))
    return dict(records=len(aa),changes=changes,material_changes=sum(c['material'] for c in changes))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir', required=True)
    args=ap.parse_args();out=Path(args.output_dir).resolve();out.mkdir(parents=True, exist_ok=False)
    root=common.ROOT;code=common.HERE
    lock=json.loads((code/'environment_lock.json').read_text())['distributions']
    installed={k:meta.version(k) for k in lock}
    assert installed == lock, 'Runtime differs from frozen lock'
    protected=[*root.glob('AE* v6.tex'),root/'AE_paper_elsarticle_v6.tex',root/'AE论文_Supplementary_v6.tex']
    protected += [p for folder in ('review_round5_20261010','review_round6_20261010')
        for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    baseline={str(p.relative_to(root)):sha(p) for p in protected}
    dump(out/'preservation_baseline.json',baseline)
    dump(out/'environment.json',dict(python=sys.version,executable=sys.executable,
        platform=platform.platform(),packages=installed,requirements_sha256=sha(code/'requirements-lock.txt'),
        environment_lock_sha256=sha(code/'environment_lock.json'),working_directory=os.getcwd(),
        entry_script=str(Path(__file__).resolve()),command_arguments=sys.argv,
        base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        random_seeds=dict(model_fits=0,paired_target_bootstrap=20261008),
        run_config=dict(landmarks=[50,100],windows=[500,1000,1500],rho=[1,2,4,8],delta=[25,50,100],bootstrap_draws=2000),
        inputs={str(p.relative_to(root)):sha(p) for p in [code/'external_features.csv',
        root/'eda/rebuild_v2/landmark_50_features.csv',root/'eda/rebuild_v2/landmark_100_features.csv']},
        code={p.name:sha(p) for p in [code/'production_model_library.py',code/'model_bank.py',code/'common.py',
        code/'survival_contract.py',code/'decision_contract.py',code/'03_run_benchmark.py',code/'04_run_replacement.py',Path(__file__)]}))
    with (out/'tests.txt').open('x',encoding='utf8') as log:
        suite=unittest.defaultTestLoader.discover(str(code), pattern='test_*.py')
        result=unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    if not result.wasSuccessful(): raise RuntimeError('Production regression failed')
    original=model_bank.Bank
    class FreshBank(original):
        def __init__(self,l):
            super().__init__(l)
            self.cache=out/'local'/str(l);self.cache.mkdir(parents=True,exist_ok=True)
    model_bank.Bank=FreshBank
    def write(name,rows):
        if not rows: raise ValueError(name)
        path=out/name
        # Production driver checkpoints are atomically replaced only inside this
        # newly reserved run directory; no pre-existing evidence is touched.
        with path.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    common.write=write;common.dump=lambda name,value:dump(out/name,value)
    try:
        for script in ('03_run_benchmark.py','04_run_replacement.py'):
            runpy.run_path(str(code/script),run_name='__main__')
        metrics=compare(code/'benchmark_metrics.csv',out/'benchmark_metrics.csv',
            ('landmark','domain','model'),('ibs','harrell_c','event_medape_pct','n_event_medians','grid'),1e-12)
        configs=compare(code/'benchmark_configs.csv',out/'benchmark_configs.csv',
            ('landmark','target','model'),('candidate',))
        selection=compare(code/'selection_results.csv',out/'selection_results.csv',
            ('landmark','domain','H','rho','delta','rule'),('selected_model','common_sources','decision_validation_sources','B1_cycle'))
        actions=compare(code/'replacement_actions.csv',out/'replacement_actions.csv',
            ('landmark','domain','H','rho','delta','policy','cell_id'),('planned_cycle','effective_cycle','maintenance_in_window'))
        loss=compare(code/'replacement_metrics.csv',out/'replacement_metrics.csv',
            ('landmark','domain','H','rho','delta','policy'),('loss','early_cycles','late_cycles','late_rate','maintenance_count','fallback_count','support_reason'),1e-12)
        bootstrap=compare(code/'replacement_pairwise_bootstrap.csv',out/'replacement_pairwise_bootstrap.csv',
            ('landmark','domain','H','rho','delta','contrast'),('difference','low','high','relative_pct','valid_draws','total_draws'),1e-12)
        comparisons=dict(metrics=metrics,configs=configs,selection=selection,actions=actions,loss=loss,bootstrap=bootstrap)
        status='CONSISTENT' if not any(v['material_changes'] for v in comparisons.values()) else 'BLOCKED_PRODUCTION_DIFFERENCE'
        preserved=all(sha(root/p)==v for p,v in baseline.items())
        assert preserved,'Frozen evidence changed'
        dump(out/'receipt.json',dict(status=status,tests_run=result.testsRun,
            fresh_fit_count=sum(1 for p in (out/'local').rglob('*.pkl')),
            comparisons=comparisons,preservation_verified=preserved,
            outputs={p.name:sha(p) for p in out.iterdir() if p.is_file()},
            probability_clipping=False))
        if status!='CONSISTENT': raise RuntimeError(status)
    except Exception as exc:
        dump(out/'failure.json',dict(status='BLOCKED',exception=repr(exc),paper_result_update='STOP'))
        raise

if __name__=='__main__':main()
