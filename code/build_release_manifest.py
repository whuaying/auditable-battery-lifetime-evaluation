"""Create the single authoritative v6.2 payload manifest."""
from pathlib import Path
import hashlib, json

R = Path(__file__).resolve().parents[1]
EXCLUDE_DIRS = {"replay_003", "qa/rendered_final", "qa/rendered_final2", "qa/rendered", "package"}
EXCLUDE_NAMES = {"release_manifest_v6_2.json", "package_validation.json", "release_gate_v6_2.json", "AppliedEnergy_v6_2_release_20261010.zip"}
EXCLUDE_EXT = {".aux", ".fdb_latexmk", ".fls", ".log", ".out", ".spl", ".synctex.gz"}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for p in sorted(R.rglob("*")):
    if not p.is_file(): continue
    rel=p.relative_to(R).as_posix()
    if rel in EXCLUDE_NAMES or any(rel == d or rel.startswith(d+"/") for d in EXCLUDE_DIRS): continue
    if any(rel.endswith(ext) for ext in EXCLUDE_EXT): continue
    if rel.endswith(".pyc") or "__pycache__/" in rel: continue
    rows.append({"path":rel,"bytes":p.stat().st_size,"sha256":sha(p)})
manifest={"manifest_version":"v6.2-authoritative-20261011","release_id":"AppliedEnergy-v6.2-20261010","status":"PASS","entry_count":len(rows),"entries":rows,"excluded":{"historical_maps":["legacy_figure_source_map_002.json","legacy_figure_source_map_003.json"],"local_replay":"replay_003/","row_level_actions":"replay_003/replacement_actions.csv","renders":"qa/rendered_final2/","provider_archives":"external"}}
(R/"release_manifest_v6_2.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps({"status":"PASS","entry_count":len(rows)},indent=2))
