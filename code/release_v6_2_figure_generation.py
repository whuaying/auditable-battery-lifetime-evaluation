from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import csv
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'pdf.fonttype':42,'svg.fonttype':'none','font.size':8})
R=Path(__file__).resolve().parents[1]; out=R/"figures_v6_2"; out.mkdir(exist_ok=True)
import json
with (R/"data"/"b0_reconciliation.json").open(encoding="utf-8") as f:
    b0=json.load(f)["fields"]
fields=["planned action","effective action","maintenance flag","evaluable loss"]
counts=[b0["planned_action"]["changed"],b0["effective_action"]["changed"],b0["maintenance_flag"]["changed"],b0["loss"]["changed"]]
fig,ax=plt.subplots(figsize=(7.2,3.2)); bars=ax.bar(fields,counts,color=["#355C7D","#6C8EBF","#99B898","#C06C84"]); ax.set_ylabel("Changed scenarios (of 504)"); ax.set_ylim(0,220); ax.bar_label(bars,fmt="%d"); ax.set_title("B0 nearest-feasible opportunity correction"); fig.tight_layout(); fig.savefig(out/"fig_v6_2_b0_repair.pdf",bbox_inches="tight"); fig.savefig(out/"fig_v6_2_b0_repair.svg",bbox_inches="tight"); fig.savefig(out/"fig_v6_2_b0_repair.png",dpi=600,bbox_inches="tight"); fig.savefig(out/"fig_v6_2_b0_repair.tiff",dpi=600,bbox_inches="tight"); plt.close(fig)
with (R/"data"/"mit_grid_confirmation_summary.csv").open(encoding="utf-8-sig",newline="") as f:
    grid=list(csv.DictReader(f))
x=np.arange(len(grid)); confirmed=np.array([int(r["confirmed_events"]) for r in grid]); censor=np.array([float(r["right_censor_fraction"]) for r in grid]); labels=[f'{r["grid"]}-cycle' for r in grid]
fig,ax=plt.subplots(figsize=(7.2,3.2)); bars=ax.bar(x,confirmed,color="#4C78A8"); ax.set_xticks(x,labels); ax.set_ylabel("Confirmed events"); ax.set_ylim(0,50); ax.bar_label(bars,fmt="%d",padding=10); ax2=ax.twinx(); ax2.plot(x,censor,"o-",color="#D95F02",zorder=0); ax2.set_ylim(0,1.05); ax2.set_ylabel("Right-censoring fraction"); ax.set_title("MIT observation-grid confirmation and support"); fig.tight_layout(); fig.savefig(out/"fig_v6_2_mit_grid.pdf",bbox_inches="tight"); fig.savefig(out/"fig_v6_2_mit_grid.svg",bbox_inches="tight"); fig.savefig(out/"fig_v6_2_mit_grid.png",dpi=600,bbox_inches="tight"); fig.savefig(out/"fig_v6_2_mit_grid.tiff",dpi=600,bbox_inches="tight"); plt.close(fig)
