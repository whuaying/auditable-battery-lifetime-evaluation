# v6.1 to v6.2 revision difference report

The production correction is isolated in `eda/rebuild_v6_2/04_run_replacement.py`.
For all 504 settings, nearest feasible opportunity to cycle 1000 is selected,
with the earlier opportunity resolving ties. Absolute cycle and residual-time
conventions are unchanged.

| Field | Changed settings | Largest absolute change | Support note |
|---|---:|---:|---|
| planned action | 196 | 500 cycles | all 504 comparable |
| effective action | 28 | 50 cycles | all 504 comparable |
| maintenance flag | 168 | 1 | all 504 comparable |
| evaluable loss | 20 | 0.275862 | 408 finite common-support rows; 96 remain NA |
| early cycles | 12 | 49.402597 | row-level timing decomposition; no imputation |
| late cycles | 20 | 50 | row-level timing decomposition; no imputation |
| late rate | 12 | 0.021277 | only rows with known late denominator |

The frozen round-4 audit agrees on planned action, effective action, the
maintenance flag and all 408 finite losses. The 196/168/28/20 expected counts
are therefore reproduced without forcing values. The complete old/new field
table is `data/b0_old_new_field_diff.csv`; round-3/round-4 comparison is in
`data/b0_round3_round4_comparison.csv`. Paired bootstrap rows change only in
B0-relative contrasts (240 records, 960 material fields); model selections and
non-B0 action fields do not change.

The stable Cox implementation is unchanged in its invalid-fit handling:
non-finite predictors, invalid hazards and unconverged fits remain unavailable;
no probability clipping is applied. The clean replay reports 17 tests, 1,036
fresh fits, zero material model/action/loss differences and only floating-point
IBS deltas below 1e-16.

The release adds real-data CALCE far-tail diagnostics, MIT 1/5/20-cycle
confirmation/support results, matched-support selection controls, and the B0
audit table/figures. Negative results, NA support and the B0 baseline remain in
the Supplementary tables S21--S25. The repaired endpoint artwork is a layout
only re-render; the retained author-approved framework asset remains unchanged
and has an open strict collision decision recorded in the figure audit.

The former standalone 002/003 figure-map copies remain under their original
names. They are historical records; `figure_source_map.json` is the only map
used by the v6.2 bundle. A standalone copy can differ because it was exported
from an earlier package state (before the v6.2 aggregate inputs and repaired
endpoint asset were bound). Its bytes and SHA-256 are preserved in the package
history and are not silently rewritten.
