"""Explicit observed-record endpoint, risk, scoring and censoring contracts."""
import numpy as np
from sksurv.metrics import concordance_index_censored

def boolean(value):
    if value in (True, 1, '1'): return True
    if value in (False, 0, '0'): return False
    raise ValueError(f'Expected explicit 0/1: {value!r}')

def outcome(row, landmark, measurement_layer='provider_processed_capacity'):
    event = boolean(row['event_observed'])
    terminal = float(row.get('last_observed_cycle', row['followup_cycle']))
    t = float(row['eol80_cycle']) if event else terminal
    if not landmark < t <= terminal: raise ValueError('Invalid endpoint/follow-up')
    last = float(row['last_feature_cycle'])
    if last > landmark: raise ValueError('Feature beyond landmark')
    return dict(last_observed_cycle=terminal, event_observed=event,
                event_cycle=t if event else None, confirmation_cycle=float(row['confirmation_cycle']) if row.get('confirmation_cycle') else None,
                analysis_stop_cycle=t, residual_time=t-landmark,
                last_feature_cycle=last, endpoint_rule_id='EOL80_first_of_3_observed',
                measurement_layer=measurement_layer)

def km(time, event, t, left=False):
    s = 1.
    for u in np.unique(time):
        if u >= t if left else u > t: break
        s *= 1 - np.sum((time == u) & event) / np.sum(time >= u)
    return float(s)

def brier(time, event, risk, t, source_max=np.inf):
    g = km(time, ~event, t)
    reason = 'OK'
    if t >= source_max: reason = 'source_prediction_support'
    elif t >= np.max(time): reason = 'no_target_followup_beyond_horizon'
    elif g < .1: reason = 'censor_survival_below_0.10'
    weights = np.zeros(len(time)); cases = event & (time <= t)
    for i in np.flatnonzero(cases):
        gi = km(time, ~event, time[i], left=True)
        if gi < .1: reason = 'event_censor_survival_below_0.10'
        else: weights[i] = (1-risk[i])**2 / gi
    weights[time > t] = risk[time > t]**2 / max(g, 1e-300)
    return (float(weights.mean()) if reason == 'OK' else None, g, int(sum(time > t)), reason)

def ibs(grid, scores):
    if len(grid) < 2 or any(x is None or not np.isfinite(x) for x in scores): return None
    if np.any(np.diff(grid) <= 0): raise ValueError('Grid not increasing')
    return float(np.trapezoid(scores, grid) / (grid[-1]-grid[0]))

def concordance(time, event, risk):
    try: return float(concordance_index_censored(event, time, risk)[0])
    except ValueError: return None

def common_keys(groups):
    keys = sorted(set.intersection(*(set(g) for g in groups.values())))
    return keys, {m:len(g)-len(keys) for m,g in groups.items()}
