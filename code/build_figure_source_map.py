"""Build the v6.2 authoritative figure/table provenance map from this release."""
from pathlib import Path
import hashlib, json

R = Path(__file__).resolve().parents[1]
ROOT = R.parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

old = json.loads((R / "legacy_figure_source_map_003.json").read_text(encoding="utf-8"))
for row in old:
    asset = R / row["asset"]
    row["asset_sha256"] = sha(asset)
    if row["asset"].endswith("fig_v5_endpoint_observation.pdf"):
        row["generating_script"] = "code/rebuild_endpoint_figure_v6_2.py (layout-only re-render from protected historical audits)"
        row["generating_script_sha256"] = sha(R / "code/rebuild_endpoint_figure_v6_2.py")
        row["input_status"] = "BOUND_TO_PROTECTED_HISTORICAL_AUDIT_OUTSIDE_RELEASE"
    else:
        row["generating_script"] = "eda/rebuild_v6/07_make_figures.py (historical frozen asset; unchanged in v6.2)"
        row["generating_script_sha256"] = sha(ROOT / "eda/rebuild_v6/07_make_figures.py")
    row["script_status"] = "historical_script_hash_verified_in_repository"
    kept = []
    for src in row.get("input_files", []):
        src["path"] = src["path"].replace("data/legacy/", "data/historical_aggregate/")
        p = R / src["path"]
        if p.exists():
            src["sha256"] = sha(p)
            kept.append(src)
    row["input_files"] = kept
    if not kept:
        row["input_status"] = "HISTORICAL_FROZEN_ASSET_SOURCE_INPUT_OUTSIDE_RELEASE"
        row["source_note"] = "The original source table is retained in the protected v6 history; this release records the asset hash and does not recreate it from a substitute input."
    else:
        row["input_status"] = "HISTORICAL_FROZEN_ASSET_AGGREGATE_INPUT"

new_script = "code/release_v6_2_figure_generation.py"
new_rows = [
    ("figures_v6_2/fig_v6_2_b0_repair.pdf", "tab:v62_b0", ["data/b0_reconciliation.json", "data/b0_old_new_field_diff.csv"]),
    ("figures_v6_2/fig_v6_2_mit_grid.pdf", "tab:v62_grid", ["data/mit_grid_confirmation_summary.csv"]),
]
for asset_name, label, inputs in new_rows:
    row = {
        "manuscript": "manuscript/AE论文_Supplementary_v6_2.tex",
        "citation": label,
        "asset": asset_name,
        "asset_sha256": sha(R / asset_name),
        "input_files": [{"path": p, "sha256": sha(R / p)} for p in inputs],
        "generating_script": new_script,
        "generating_script_sha256": sha(R / new_script),
        "input_status": "BOUND_TO_FROZEN_V6_2_AGGREGATE",
    }
    old.append(row)

for label, inputs in {
    "tab:v62_calce": ["data/calce_event_error_diagnostics.csv"],
    "tab:v62_grid": ["data/mit_grid_confirmation_summary.csv"],
    "tab:v62_select": ["data/grid_selection_comparison.csv"],
    "tab:v62_common": ["data/grid_common_support_sensitivity.csv"],
    "tab:v62_b0": ["data/b0_reconciliation.json", "data/b0_old_new_field_diff.csv"],
}.items():
    old.append({
        "manuscript": "manuscript/generated_results_v6_2.tex",
        "citation": label,
        "asset": "manuscript/generated_results_v6_2.tex",
        "asset_sha256": sha(R / "manuscript/generated_results_v6_2.tex"),
        "input_files": [{"path": p, "sha256": sha(R / p)} for p in inputs],
        "generating_script": "code/generate_result_tables.py",
        "generating_script_sha256": sha(R / "code/generate_result_tables.py"),
        "input_status": "BOUND_TO_FROZEN_V6_2_AGGREGATE",
    })

(R / "figure_source_map.json").write_text(json.dumps(old, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"status": "PASS", "entries": len(old)}, indent=2))
