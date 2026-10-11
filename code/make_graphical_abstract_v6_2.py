from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
ROOT=Path(r'D:\AEpaper'); OUT=ROOT/'figures_v6_2'; OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','pdf.fonttype':42,'svg.fonttype':'none'})
fig,ax=plt.subplots(figsize=(12.5,5.0));fig.patch.set_facecolor('white');ax.set(xlim=(0,12.5),ylim=(0,5));ax.axis('off')
ax.text(.35,4.65,'Auditable cross-source battery lifetime evaluation',fontsize=24,fontweight='bold',color='#18364d',va='center')
ax.text(.35,4.18,'6 source cases  |  429 verified cells  |  observed-record EOL80 proxy',fontsize=16,color='#526b7b')
cards=[(.35,'1  Audit endpoints','#edf4f8','#3475a7'),(4.55,'2  Test transfer','#eef5f0','#338365'),(8.75,'3  Bound conclusions','#fcf3eb','#a56530')]
for x,title,face,edge in cards:
 ax.add_patch(FancyBboxPatch((x,1.05),3.40,2.83,boxstyle='round,pad=.025,rounding_size=.12',facecolor=face,edgecolor=edge,linewidth=1.5));ax.text(x+.18,3.50,title,fontsize=18,fontweight='bold',color=edge)
ax.text(.60,3.03,'Endpoint schematic',fontsize=14,color='#526b7b')
ax.plot([.72,1.08,1.48,1.87,2.24,2.60,2.97,3.31],[2.79,2.75,2.55,2.34,2.07,1.97,1.85,1.72],color='#3475a7',lw=2)
ax.plot([.70,3.37],[2.22,2.22],'--',color='#75828c',lw=1.1);ax.text(3.40,2.22,'0.8',ha='right',va='bottom',fontsize=14)
ax.scatter([2.24,2.60,2.97],[2.07,1.97,1.85],s=52,color='#D55E00',zorder=3)
for x,y,label in [(2.24,2.07,'1'),(2.60,1.97,'2'),(2.97,1.85,'3')]: ax.text(x,y-.24,label,ha='center',fontsize=14,color='#a56530')
ax.text(2.22,1.23,'First low record; third confirms',ha='center',fontsize=13.5,color='#233f51')
for i,name in enumerate(['MIT','XJTU','TJU','NASA','CALCE','HUST']):
 x=4.80+(i%3)*.99;y=2.38-(i//3)*.60;held=i==0
 ax.add_patch(FancyBboxPatch((x,y),.84,.44,boxstyle='round,pad=.01,rounding_size=.04',facecolor='#cfe2ef' if held else '#daeade',edgecolor='#3475a7' if held else '#83a991',linewidth=1));ax.text(x+.42,y+.22,name,ha='center',va='center',fontsize=15,color='#233f51')
ax.text(6.25,3.00,'5 train / 1 held out',ha='center',fontsize=17,color='#233f51');ax.text(6.25,1.30,'Rotate through all 6 sources',ha='center',fontsize=14,color='#233f51')
ax.text(10.45,2.91,'Winners vary by source',ha='center',fontsize=16,fontweight='bold',color='#233f51');ax.text(10.45,2.43,'Adaptation can worsen IBS',ha='center',fontsize=15,color='#233f51');ax.text(10.45,1.78,'Source-specific support',ha='center',fontsize=15,color='#233f51');ax.text(10.45,1.34,'Conditional uncertainty',ha='center',fontsize=15,color='#233f51')
for start in (3.84,8.04): ax.add_patch(FancyArrowPatch((start,2.42),(start+.40,2.42),arrowstyle='-|>',mutation_scale=20,color='#718896',linewidth=2))
ax.add_patch(FancyBboxPatch((.35,.16),11.80,.58,boxstyle='round,pad=.02,rounding_size=.05',facecolor='#18364d',edgecolor='none'));ax.text(6.25,.45,'Evidence checks before storage decisions; system benefits remain unvalidated',ha='center',va='center',fontsize=16,color='white')
fig.subplots_adjust(left=0,right=1,top=1,bottom=0);fig.savefig(OUT/'graphical_abstract_v6_2.pdf',facecolor='white');fig.savefig(OUT/'graphical_abstract_v6_2.png',dpi=300,facecolor='white');plt.close(fig)
print(OUT/'graphical_abstract_v6_2.pdf')
