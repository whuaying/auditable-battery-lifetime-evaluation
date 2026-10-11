# Auditable Battery Lifetime Evaluation

Public release staging for the Applied Energy v6.2 manuscript and its source-conditional battery lifetime evaluation audit.

Repository name: `auditable-battery-lifetime-evaluation`

## Included

- Reproducible analysis code, contracts, configuration and dependency locks under `code/`.
- Machine-readable aggregate results and reporting outputs under `data/`.
- Manuscript and Supplementary source/PDF files under `manuscript/`.
- Vector figures, Graphical Abstract, Highlights, source maps, release manifests and QA receipts.

## Data access boundary

Provider archives, cell- and cycle-level derived tables, row-level predictions, fit caches and local environments are excluded. See `DATA_ACCESS.md` for source links, access conditions and the exact public/restricted boundary. The public aggregate outputs do not grant redistribution rights to third-party data.

## Reproduction status

The clean Python 3.11 canonical-fit replay and v6.2 production B0 correction are recorded in `qa/` and `release_gate_v6_2.json`. A complete provider-archive-to-model replay remains dependent on access to the original archives and their permissions.

## Scientific scope

Results concern observed-record EOL80 proxies, processed external series and restricted timing-loss scenarios. They do not establish physical failure, pack-level reliability, operating-cost savings or intervention benefit.

## Manuscript metadata

Author names, affiliations, corresponding-author details, funding, competing interests, CRediT roles, provider permissions and DOI remain pending author completion.
