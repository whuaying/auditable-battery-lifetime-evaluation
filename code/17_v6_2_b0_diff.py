"""Create an auditable old/new B0 field diff for the v6.2 release."""
import csv, json, hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "rebuild_v6"
ROUND4 = HERE.parents[1] / "review_round4_20261010" / "results_002" / "b0_feasibility_audit.csv"

def read(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write(path, rows):
    with Path(path).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def key(r):
    return tuple(r[k] for k in ("landmark", "domain" if "domain" in r else "source", "H", "rho", "delta"))

old = {key(r): r for r in read(OLD / "replacement_metrics.csv") if r["policy"] == "B0"}
new = {key(r): r for r in read(HERE / "replacement_metrics.csv") if r["policy"] == "B0"}
r4_rows = read(ROUND4)
r4 = {key(r): r for r in r4_rows}
r4_maintenance = {}
for r in r4_rows:
    r4_maintenance[key(r)] = r4_maintenance.get(key(r), 0) + int(r["corrected_maintenance_flag"])
assert len(old) == len(new) == len(r4) == 504

fields = {
    "planned_action": ("mean_planned_cycle", "mean_planned_cycle"),
    "effective_action": ("mean_effective_cycle", "mean_effective_cycle"),
    "maintenance_count": ("maintenance_count", "maintenance_count"),
    "maintenance_flag": ("maintenance_count", "maintenance_count"),
    "loss": ("loss", "loss"),
    "early_cycles": ("early_cycles", "early_cycles"),
    "late_cycles": ("late_cycles", "late_cycles"),
    "late_rate": ("late_rate", "late_rate"),
    "late_known_count": ("late_known_count", "late_known_count"),
}
rows = []
for k in sorted(old):
    for field, (oc, nc) in fields.items():
        ov = old[k].get(oc, "")
        nv = new[k].get(nc, "")
        if field == "maintenance_flag":
            ov, nv = str(int(float(ov) > 0)), str(int(float(nv) > 0))
        of = float(ov) if ov not in ("", None) else None
        nf = float(nv) if nv not in ("", None) else None
        diff = "" if of is None or nf is None else nf - of
        r4v = ""
        if field == "planned_action": r4v = r4[k]["corrected_planned_action"]
        elif field == "effective_action": r4v = r4[k]["corrected_effective_action"]
        elif field == "maintenance_count": r4v = r4[k]["corrected_maintenance_flag"]
        elif field == "maintenance_flag": r4v = r4[k]["corrected_maintenance_flag"]
        elif field == "loss": r4v = r4[k]["recomputed_corrected_loss"]
        rows.append(dict(landmark=k[0], domain=k[1], H=k[2], rho=k[3], delta=k[4],
                         policy="B0", field=field, old=ov, new=nv,
                         difference="" if diff == "" else f"{diff:.15g}",
                         round4_corrected=r4v,
                         matches_round4=("not_comparable_count" if field == "maintenance_count" else
                                         ("" if r4v == "" else str(abs(float(nv)-float(r4v)) < 1e-10)))))
write(HERE / "b0_old_new_field_diff.csv", rows)

summary = {"scenarios": 504, "fields": {}, "input_sha256": {}}
for field in fields:
    rr = [x for x in rows if x["field"] == field]
    changed = [x for x in rr if x["difference"] not in ("", "0", "0.0") and abs(float(x["difference"])) > 1e-12]
    comparable = [x for x in rr if x["round4_corrected"] != ""]
    summary["fields"][field] = {"changed": len(changed), "max_abs_difference": max([abs(float(x["difference"])) for x in changed], default=0.0),
                                  "round4_common_support": len(comparable),
                                  "round4_unavailable": len(rr) - len(comparable),
                                  "matches_round4": (all(x["matches_round4"] == "True" for x in comparable) if comparable and field != "maintenance_count" else "NOT_COMPARABLE")}
for p in [OLD / "replacement_metrics.csv", HERE / "replacement_metrics.csv", ROUND4, HERE / "b0_old_new_field_diff.csv"]:
    summary["input_sha256"][str(p.relative_to(HERE.parents[1]))] = hashlib.sha256(p.read_bytes()).hexdigest()
(HERE / "b0_reconciliation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
