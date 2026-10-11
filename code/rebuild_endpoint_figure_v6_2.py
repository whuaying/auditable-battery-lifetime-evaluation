"""Re-render the historical endpoint figure with collision-free label placement.

The inputs are the protected v4/v2 aggregate audits; this script writes only
the independent v6.2 release asset and does not change historical outputs.
"""
from pathlib import Path
import csv, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
R = Path(__file__).resolve().parents[1]
with (ROOT/"eda/rebuild_v4/source_evidence_cards.csv").open(encoding="utf-8-sig", newline="") as f:
    cards = list(csv.DictReader(f))
with (ROOT/"eda/rebuild_v4/endpoint_observation_audit.csv").open(encoding="utf-8-sig", newline="") as f:
    audit = list(csv.DictReader(f))
hust = json.loads((ROOT/"eda/rebuild_v2/hust_source_audit.json").read_text(encoding="utf-8"))["details"]
obs = {r["cell_id"]: float(r["endpoint_3_cycle"]) for r in audit if r["dataset"] == "HUST"}
x = np.array([obs[r["cell_id"]] for r in hust]); y = np.array([r["source_rul_terminal_cycle"] for r in hust])
assert len(x) == 77 and np.median(y-x) == 258 and ((y-x) > 0).all()

plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":9, "axes.labelsize":9,
                     "axes.titlesize":10, "pdf.fonttype":42, "ps.fonttype":42,
                     "axes.spines.top":False, "axes.spines.right":False})
fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.8), layout="constrained")
ax = axes[0,0]; ax.set_title("(a) Retrospective event vs confirmation", loc="left", pad=28)
ax.axhline(.8, color="#777777", ls="--", lw=1); ax.plot([0,1,2,3],[.84,.78,.77,.76],"o-",color="#0072B2",lw=1.4)
ax.annotate("Event assigned here", xy=(1,.78), xytext=(.9,.845), ha="center", fontsize=8, arrowprops={"arrowstyle":"->","color":"#333333"})
ax.annotate("Alarm confirmed here", xy=(3,.76), xytext=(2.45,.705), ha="center", fontsize=8, arrowprops={"arrowstyle":"->","color":"#333333"})
ax.set_xticks([0,1,2,3],["Prior","Low 1","Low 2","Low 3"]); ax.set_ylim(.68,.865); ax.set_yticks([.8]); ax.set_ylabel("SOH (schematic)"); ax.set_xlabel("Consecutive records; cycles may skip")
ax = axes[0,1]; ax.set_title("(b) Actual confirmation lag", loc="left", pad=28)
pos=np.arange(6); med=np.array([float(r["confirmation_lag_median"]) for r in cards]); low=np.array([float(r["confirmation_lag_min"]) for r in cards]); high=np.array([float(r["confirmation_lag_max"]) for r in cards])
ax.errorbar(pos,med,yerr=[med-low,high-med],fmt="o",color="#0072B2",capsize=3,lw=1.3)
for i,r in enumerate(cards):
    # Offset the badge from the vertical error-bar cap so its glyphs remain clear.
    dx = 0.30 if i == 0 else (-0.12 if i == len(cards)-1 else 0.0)
    ax.text(i + dx, high[i]+0.8, "n="+r["n_confirmed_all_verified"], ha="center", fontsize=8)
ax.set_xticks(pos,[r["domain"] for r in cards],rotation=25); ax.set_ylim(0,14.5); ax.set_ylabel("Confirmation lag (cycles)"); ax.text(.03,1.02,"Median and min–max; all verified events",transform=ax.transAxes,fontsize=8,va="bottom")
ax = axes[1,0]; ax.set_title("(c) Cells with any skipped cycle record", loc="left", pad=12)
perc=[100*int(r["n_cells_with_skipped_cycle_gaps"])/int(r["n_verified"]) for r in cards]; ax.bar(pos,perc,color="#56B4E9",width=.6)
for i,r in enumerate(cards): ax.text(i,perc[i]+3,f'{r["n_cells_with_skipped_cycle_gaps"]}/{r["n_verified"]}',ha="center",fontsize=8)
ax.set_xticks(pos,[r["domain"] for r in cards],rotation=25); ax.set_ylim(0,125); ax.set_yticks([0,25,50,75,100]); ax.set_ylabel("Verified cells with a gap >1 cycle (%)"); ax.text(.02,.96,"Processed record grid; not instrument frequency",transform=ax.transAxes,fontsize=8,va="top")
ax = axes[1,1]; ax.set_title("(d) HUST: distinct lifetime targets", loc="left", pad=12)
ax.scatter(x,y,s=12,color="#0072B2",alpha=.65,edgecolors="none"); lo=0; hi=np.ceil(max(x.max(),y.max())/500)*500; ax.plot([lo,hi],[lo,hi],ls="--",color="#777777",lw=1,label="Equal targets")
ax.set_xlim(lo,hi); ax.set_ylim(lo,hi); ax.set_aspect("equal",adjustable="box"); ax.set_xlabel("Three-observation EOL80 proxy (cycle)"); ax.set_ylabel("Archive terminal cycle"); ax.text(.04,.96,"77/77 differ\nMedian +258 cycles\nRange +104–524",transform=ax.transAxes,va="top",fontsize=8); ax.legend(loc="lower right",fontsize=8,frameon=False)
out=R/"figures_v4"; out.mkdir(exist_ok=True)
fig.savefig(out/"fig_v5_endpoint_observation.pdf"); fig.savefig(out/"fig_v5_endpoint_observation.png", dpi=600); plt.close(fig)
print(out/"fig_v5_endpoint_observation.pdf")
