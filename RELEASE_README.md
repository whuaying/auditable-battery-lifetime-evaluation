# Applied Energy v6.2 release bundle

This directory is the independent v6.2 release output. The authoritative
production entry points are `code/03_run_benchmark.py` and
`code/04_run_replacement.py`; the latter implements the frozen nearest-feasible
opportunity B0 rule. The clean replay receipt is recorded in
`qa/release_reproducibility_receipt.json` and was generated in
`replay_003/` using the locked Python 3.11 environment.

`figure_source_map.json` is the only authoritative figure/table provenance map.
`legacy_figure_source_map_002.json` and `legacy_figure_source_map_003.json` are
retained historical copies and are not inputs to the v6.2 map. Cell-level
derived rows, fit caches and provider archives remain excluded from this
release because redistribution rights are unresolved; aggregate CSV/JSON
outputs used by the manuscript are included and hash-recorded.

The PDFs are compiled from the LaTeX files under `manuscript/`. The author
list, affiliations, corresponding-author email, CRediT, funding, competing
interests, provider permissions, public data deposit and DOI remain
`AUTHOR_ACTION_REQUIRED` pending author confirmation.
