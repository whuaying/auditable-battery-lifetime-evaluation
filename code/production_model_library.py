"""Release v6.1: unchanged candidate models with validated log-domain Cox curves.

The archived v4 implementation is retained as evidence. Only the shared v6
entry point changes. Invalid fits are rejected, never probability-clipped.
"""
import importlib.util
from pathlib import Path
import warnings
import numpy as np

spec = importlib.util.spec_from_file_location('archived_candidate_library',
    Path(__file__).resolve().parents[1] / 'rebuild_v4/01_residual_survival_benchmark.py')
archived = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archived)
for name in dir(archived):
    if not name.startswith('_'):
        globals()[name] = getattr(archived, name)

CODE_VERSION = 'v6.2-b0-nearest-feasible-20261010'

def stable_cox_survival(eta, hazard):
    eta, hazard = np.asarray(eta, float), np.asarray(hazard, float)
    if eta.ndim != 1 or hazard.ndim != 1:
        raise ValueError('Cox inputs must be one-dimensional')
    if not np.all(np.isfinite(eta)) or not np.all(np.isfinite(hazard)):
        raise ValueError('Non-finite Cox predictor/baseline hazard')
    if np.any(hazard < 0) or np.any(np.diff(hazard) < 0):
        raise ValueError('Invalid Cox cumulative baseline hazard')
    logh = np.full(hazard.shape, -np.inf)
    np.log(hazard, out=logh, where=hazard > 0)
    with np.errstate(over='ignore', under='ignore'):
        # Overflow of the inner exponential has the exact limiting survival 0.
        # H0=0 is represented as logH0=-inf, even for extreme finite eta.
        survival = np.exp(-np.exp(eta[:, None] + logh[None, :]))
    if not np.all(np.isfinite(survival)):
        raise ValueError('Invalid Cox probability')
    return survival

def validate_prediction(p):
    # Keep unconverged fits as explicit invalid records so tuning can reject
    # them. They are never converted into usable probability curves.
    if not np.all(np.isfinite(p['risk_score'])):
        raise ValueError('Non-finite risk score')
    if p['kind'] == 'step':
        grid, v = np.asarray(p['grid']), np.asarray(p['survival'])
        if (v.shape != (len(p['risk_score']), len(grid)) or
            not np.all(np.isfinite(grid)) or np.any(np.diff(grid) <= 0) or
            not np.all(np.isfinite(v)) or np.any((v < 0) | (v > 1)) or
            np.any(np.diff(v, axis=1) > 1e-10)):
            raise ValueError('Invalid survival distribution; no clipping permitted')
    elif (not np.all(np.isfinite(p['mu'])) or
          not np.isfinite(p['sigma']) or p['sigma'] <= 0):
        raise ValueError('Invalid lognormal distribution')
    return p

def fit_predict(model_name, candidate, xtr_raw, xte_raw, ytr, seed=0):
    if model_name != 'cox':
        return validate_prediction(archived.fit_predict(
            model_name, candidate, xtr_raw, xte_raw, ytr, seed))
    imputer = SimpleImputer(strategy='median').fit(xtr_raw)
    xtr, xte = imputer.transform(xtr_raw), imputer.transform(xte_raw)
    scaler = StandardScaler().fit(xtr)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        model = CoxPHSurvivalAnalysis(alpha=float(candidate), n_iter=1000).fit(
            scaler.transform(xtr), ytr)
    converged = not any(issubclass(w.category, (ConvergenceWarning, RuntimeWarning)) for w in caught)
    eta = model.predict(scaler.transform(xte))
    p = dict(kind='step', grid=np.asarray(model.unique_times_, float),
        survival=stable_cox_survival(eta, model.cum_baseline_hazard_.y),
        risk_score=eta, sigma=None, fitted=converged,
        source_max_followup=float(ytr['time'].max()))
    return validate_prediction(p)
