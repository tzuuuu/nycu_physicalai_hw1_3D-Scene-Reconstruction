"""Additional offline report views and descriptive pair/error diagnostics only."""
import csv
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.stats import spearmanr
from scripts import m43_analysis as a
from scripts.m42_integrity import read,inventory
from scripts.m42_monitor import write
from scripts.m42_results import csv_write
from scripts.m43_results import frame_errors
from scripts.m4_capture_check import sha


def report():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    close=a.ROOT/'research_outputs/m43_p2b_closeout_01'
    out=close/'report_details';out.mkdir(exist_ok=False)
    frames=read(a.SPEC)['selected_indices'];src=a.OUT/'observation'
    gt=np.load(a.CAPTURE/'GT_pose.npy')
    bp,bt,be=frame_errors(np.load(a.BASE/'observation/positions.npy'),gt,list(range(1,321)))
    sp,st,se=frame_errors(np.load(src/'positions.npy'),gt,frames)
    pairs=a.lines(src/'transforms.jsonl');diagnostics=[]
    for j,pair in enumerate(pairs):
        t=np.asarray(pair['icp_transformation'])
        diagnostics.append(dict(previous=pair['prev_stem'],current=pair['stem'],original_index_step=pair['stem']-pair['prev_stem'],
            **{key:pair[key] for key in a.KEYS.values()},
            estimated_translation_m=float(np.linalg.norm(t[:3,3])),
            estimated_rotation_deg=float(Rotation.from_matrix(t[:3,:3]).magnitude()*180/np.pi),
            selected_l2_m=float(se[j+1]),selected_l2_change_m=float(se[j+1]-se[j]),
            baseline_l2_at_current_m=float(be[pair['stem']-1])))
    csv_write(out/'selected_pair_diagnostics.csv',diagnostics)
    groups={}
    for gap in [1,2]:
        subset=[p for p in diagnostics if p['original_index_step']==gap]
        groups[str(gap)]=dict(count=len(subset),**{key+'_median':float(np.median([p[key] for p in subset])) for key in [*a.KEYS.values(),'estimated_translation_m','estimated_rotation_deg']})
    tails={key:sorted(diagnostics,key=lambda r:r[key],reverse='rmse' in key)[:8] for key in a.KEYS.values()}
    correlations={key:float(spearmanr([r[key] for r in diagnostics],[r['selected_l2_change_m'] for r in diagnostics]).statistic) for key in a.KEYS.values()}
    intervals=[]
    for start,end in [(1,100),(101,200),(201,296),(297,320)]:
        mask=(np.array(frames)>=start)&(np.array(frames)<=end)
        intervals.append(dict(start=start,end=end,count=int(mask.sum()),baseline_same_mean_l2_m=float(be[np.array(frames)[mask]-1].mean()),
            selected_mean_l2_m=float(se[mask].mean()),baseline_same_max_l2_m=float(be[np.array(frames)[mask]-1].max()),selected_max_l2_m=float(se[mask].max())))
    summary=dict(pair_index_step_groups=groups,worst_pair_tails=tails,error_intervals=intervals,
        spearman_with_selected_l2_increment=correlations,correlation_limit='Descriptive ranks only; autocorrelated sequential data, no significance test or causal attribution.',
        largest_selected_l2_increases=sorted(diagnostics,key=lambda r:r['selected_l2_change_m'],reverse=True)[:8],
        selected_worse_than_baseline_at_same_frame_count=int(np.sum(se>be[np.array(frames)-1])),
        total_same_frames=len(frames),selected_last_l2_m=float(se[-1]),baseline_last_l2_m=float(be[-1]),
        selected_l2_median_m=float(np.median(se)),selected_l2_p95_m=float(np.percentile(se,95)))
    write(out/'diagnostics_summary.json',summary)
    maps=[np.load(a.BASE/'observation/map_points.npy',mmap_mode='r'),np.load(src/'map_points.npy',mmap_mode='r')]
    colors=[np.load(a.BASE/'observation/map_colors.npy',mmap_mode='r'),np.load(src/'map_colors.npy',mmap_mode='r')]
    bounds=np.stack([np.minimum(maps[0].min(axis=0),maps[1].min(axis=0)),np.maximum(maps[0].max(axis=0),maps[1].max(axis=0))])
    strides=[max(1,int(np.ceil(len(p)/150000))) for p in maps];figures={}
    def save(fig,name):
        fig.savefig(out/name,dpi=180,bbox_inches='tight',pad_inches=.2);plt.close(fig);figures[name]=sha(out/name)
    for i,(name,p,c,pred,truth,stride) in enumerate(zip(['P2-A FullBatch','P2-B Selected'],maps,colors,[bp,sp],[bt,st],strides)):
        points=p[::stride]*[1,-1,-1]
        fig=plt.figure(figsize=(12,9));ax=fig.add_subplot(111,projection='3d')
        ax.scatter(points[:,0],points[:,2],points[:,1],c=c[::stride],s=.35,rasterized=True)
        for path,color,label in [(pred,'red','Estimated'),(truth,'black','GT')]:ax.plot(path[:,0],path[:,2],path[:,1],c=color,label=label,lw=1.4)
        ax.set(xlim=bounds[:,0],ylim=-bounds[::-1,2],zlim=-bounds[::-1,1],xlabel='X (m)',ylabel='Z (m)')
        ax.set_zlabel('');ax.set_box_aspect(np.ptp(bounds[:,[0,2,1]],axis=0));ax.view_init(55,-65);ax.legend(loc='upper left')
        fig.suptitle(name+': same-call saved map',fontsize=17);fig.text(.92,.54,'Y up (m)',rotation=90,ha='center',va='center')
        fig.subplots_adjust(left=.02,right=.87,bottom=.06,top=.91);save(fig,'reconstruction_3d_'+('baseline' if i==0 else 'selected')+'_report.png')
    mid=(maps[0].min(axis=0)+maps[0].max(axis=0))/2
    fig,axes=plt.subplots(4,2,figsize=(12,17))
    for row,(highx,highz) in enumerate([(False,False),(False,True),(True,False),(True,True)]):
        x0,x1=(mid[0],bounds[1,0]) if highx else (bounds[0,0],mid[0])
        z0,z1=(mid[2],bounds[1,2]) if highz else (bounds[0,2],mid[2])
        for col,(p,c,pred,truth,stride) in enumerate(zip(maps,colors,[bp,sp],[bt,st],strides)):
            ax=axes[row,col];points=p[::stride]*[1,-1,-1]
            ax.scatter(points[:,0],points[:,2],c=c[::stride],s=.4,rasterized=True)
            ax.plot(pred[:,0],pred[:,2],c='red',lw=1);ax.plot(truth[:,0],truth[:,2],c='black',lw=1)
            ax.set(xlim=(x0,x1),ylim=(-z1,-z0),xlabel='X (m)',ylabel='Display Z (m)',
                title=('P2-A' if col==0 else 'P2-B')+': '+('High' if highx else 'Low')+' X / '+('High' if highz else 'Low')+' raw Z')
            ax.set_aspect('equal')
    fig.tight_layout();save(fig,'spatial_regions_comparison.png')
    d=np.load(close/'analysis/baseline_to_selected_distances.npy',mmap_mode='r');missing=maps[0][d>.2]*[1,-1,-1]
    fig,ax=plt.subplots(figsize=(10,8));points=maps[0][::strides[0]]*[1,-1,-1]
    ax.scatter(points[:,0],points[:,2],c='lightgray',s=.4,rasterized=True)
    ax.scatter(missing[:,0],missing[:,2],c='red',s=12,label='%d full-map points >0.20m from Selected'%len(missing))
    ax.set_aspect('equal');ax.set(xlabel='X (m)',ylabel='Display Z (m)',title='Relative map disagreement; no room completeness GT');ax.legend(fontsize=8)
    save(fig,'relative_map_disagreement.png')
    with (close/'analysis/selected_factors.csv').open() as f:srows=list(csv.DictReader(f))
    with (a.BASE/'factors.csv').open() as f:brows=list(csv.DictReader(f))
    fig,axes=plt.subplots(4,2,figsize=(13,12))
    for ax,factor in zip(axes.flat,sorted({r['factor'] for r in srows})):
        for rows,label in [(brows,'P2-A'),(srows,'P2-B')]:
            rows=[r for r in rows if r['factor']==factor]
            ax.plot([int(r['current']) for r in rows],[float(r['value']) for r in rows],lw=.8,label=label)
        ax.set(title=factor,xlabel='Original current frame');ax.legend(fontsize=7);ax.grid(alpha=.2)
    fig.tight_layout();save(fig,'eight_factor_series_comparison.png')
    write(out/'figure_provenance.json',dict(figures=figures,strides=strides,
        sources=read(close/'analysis/figure_manifest.json')['sources'],relative_disagreement_point_count=len(missing),
        raw_to_display='[X,Y,Z] -> [X,-Y,-Z]; spatial region labels use raw camera X/Z, display vertical axis is -raw Z',
        notes='Full maps unchanged. Plot samples only; both 3D views share metric bounds/view/aspect. Original combined 3D figure retained; report variants provide label margin.'))
    write(out/'manifest.json',inventory([out]))


if __name__=='__main__':report()
