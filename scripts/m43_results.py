"""Offline same-frame error and full-map relative coverage; no reconstruction."""
import csv
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
from scripts import m43_analysis as a
from scripts.m42_integrity import read
from scripts.m42_monitor import write
from scripts.m42_results import csv_write
from scripts.m4_capture_check import sha


def frame_errors(positions,gt,indices):
    q=gt[0,3:7];rotation=Rotation.from_quat([q[1],q[2],q[3],q[0]]).as_matrix()
    truth=(gt[:,:3]-gt[0,:3])@rotation
    pred=np.asarray(positions)*np.array([1.,-1.,-1.])
    return pred,truth[np.asarray(indices)-1],np.linalg.norm(pred-truth[np.asarray(indices)-1],axis=1)


def observed_rows(events):
    rows=[]
    for r in events:
        if r['kind']=='frame':
            for factor,key in [('RawPointCount','raw_point_count'),('VoxelizedPointYield','point_yield')]:
                rows.append(dict(factor=factor,previous='',current=r['stem'],value=r[key]))
        else:
            for factor,key in a.KEYS.items():
                rows.append(dict(factor=factor,previous=r['prev_stem'],current=r['stem'],value=r[key]))
    return rows


def validated_arrays(obs,frames):
    arrays={}
    for meta_name in ['trajectory_metadata.json','map_summary.json']:
        for name,spec in read(obs/meta_name)['arrays'].items():
            path=obs/(name+'.npy')
            if sha(path)!=spec['sha256']:raise RuntimeError('Array SHA changed: '+name)
            arr=np.load(path,mmap_mode='r',allow_pickle=False)
            if str(arr.dtype)!='float64' or list(arr.shape)!=spec['shape']:raise RuntimeError('Array dtype/shape mismatch')
            for start in range(0,len(arr),65536):
                if not np.isfinite(arr[start:start+65536]).all():raise RuntimeError('Nonfinite array')
            arrays[name]=arr
    n=len(frames)
    if arrays['camera_poses'].shape!=(n,4,4) or arrays['positions'].shape!=(n,3):raise RuntimeError('Pose count mismatch')
    if read(obs/'trajectory_metadata.json')['frame_indices']!=frames:raise RuntimeError('Original frame indices changed')
    transforms=a.lines(obs/'transforms.jsonl')
    if [(r['prev_stem'],r['stem']) for r in transforms]!=list(zip(frames,frames[1:])) or not all(r['accepted_by_core'] for r in transforms):
        raise RuntimeError('Wrong/failed selected pair')
    pose=np.eye(4);np.testing.assert_array_equal(arrays['camera_poses'][0],pose)
    for j,r in enumerate(transforms):
        for name,key in [('pairwise_icp','icp_transformation'),('pairwise_ransac','trans_init')]:
            np.testing.assert_array_equal(arrays[name][j],r[key])
        pose=pose@np.asarray(r['icp_transformation']);np.testing.assert_allclose(pose,arrays['camera_poses'][j+1],rtol=0,atol=1e-12)
    np.testing.assert_array_equal(arrays['camera_poses'][:,:3,3],arrays['positions'])
    meta=read(obs/'map_summary.json')
    if not meta['full_returned_map'] or meta['sample_stride']!=1 or len(arrays['map_points'])!=meta['point_count']:
        raise RuntimeError('Incomplete map export')
    return arrays


def coverage(source,target,threshold=.20):
    tree=cKDTree(target)
    distances=np.empty(len(source))
    for start in range(0,len(source),65536):
        distances[start:start+65536]=tree.query(source[start:start+65536],k=1,workers=1)[0]
    return distances,dict(source_points=len(source),target_points=len(target),threshold_m=threshold,
        fraction_within_threshold=float(np.mean(distances<=threshold)),
        median_distance_m=float(np.median(distances)),p95_distance_m=float(np.percentile(distances,95)))


def occupancy(points,size=.20):
    result=set()
    for start in range(0,len(points),65536):
        result.update(map(tuple,np.floor(points[start:start+65536]/size).astype(np.int64)))
    return result


def results(out):
    import api
    from scripts.m43_selected import graph_delta
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=Path(out);frames=read(a.SPEC)['selected_indices'];n=len(frames);obs=out/'observation'
    delta=graph_delta(out/'baseline.before.ttl',a.TTL,frames)
    arrays=validated_arrays(obs,frames)
    events=a.lines(obs/'events.jsonl');fr=[r['stem'] for r in events if r['kind']=='frame']
    if fr!=frames:raise RuntimeError('Wrong frame event order')
    factors=observed_rows(events)
    if len(factors)!=8*n-6:raise RuntimeError('Incomplete selected factor observations')
    keys=[(r['factor'],r['previous'],r['current']) for r in factors]
    if len(set(keys))!=len(keys):raise RuntimeError('Duplicate selected factor observations')
    csv_write(out/'selected_factors.csv',factors)
    with (a.BASE/'factors.csv').open() as f:baseline_factors=list(csv.DictReader(f))
    baseline_single={(r['factor'],int(r['current'])):float(r['value']) for r in baseline_factors if not r['previous']}
    for row in factors:
        if not row['previous'] and float(row['value'])!=baseline_single[(row['factor'],row['current'])]:
            raise RuntimeError('Selected single-frame measurement differs from saved baseline')
    stats={'baseline':a.summarize(baseline_factors),'selected':a.summarize(factors)}
    write(out/'factor_statistics.json',stats)
    actual=read(obs/'actual_reconstruct_arguments.json')
    expected=dict(version='open3d',voxel_size=.05,registration_seed=0,down_voxel=.05,build_cloud=True,frames=frames)
    if any(actual[k]!=v for k,v in expected.items()):raise RuntimeError('Effective reconstruction parameters mismatch')
    gt=np.load(a.CAPTURE/'GT_pose.npy',allow_pickle=False)
    bp=np.load(a.BASE/'observation/positions.npy',allow_pickle=False)
    bpred,btruth,be=frame_errors(bp,gt,list(range(1,321)))
    spred,struth,se=frame_errors(arrays['positions'],gt,frames)
    same=be[np.asarray(frames)-1]
    np.testing.assert_allclose(be.mean(),read(a.BASE/'observation/official_evaluation.json')['mean_l2_raw_m'],atol=1e-12,rtol=0)
    np.testing.assert_allclose(se.mean(),read(obs/'official_evaluation.json')['mean_l2_raw_m'],atol=1e-12,rtol=0)
    exp=api.read_experiment(str(a.TTL));run=api.data_run_iri(exp['exp_name'],'selected')
    if float(exp['graph'].value(run,api.HW1.mapMeanL2))!=api._storable(float(se.mean())):raise RuntimeError('Selected official L2 mismatch')
    csv_write(out/'same_frame_l2.csv',[dict(original_frame=i,baseline_l2_m=float(x),selected_l2_m=float(y),difference_m=float(y-x)) for i,x,y in zip(frames,same,se)])
    fullmap=np.load(a.BASE/'observation/map_points.npy',mmap_mode='r')
    selectedmap=arrays['map_points']
    d,bc=coverage(fullmap,selectedmap)
    np.save(out/'baseline_to_selected_distances.npy',d,allow_pickle=False)
    _,sc=coverage(selectedmap,fullmap)
    bo,so=occupancy(fullmap),occupancy(selectedmap)
    occ=dict(voxel_m=.20,baseline_cells=len(bo),selected_cells=len(so),intersection=len(bo&so),
             union=len(bo|so),intersection_over_union=len(bo&so)/len(bo|so))
    del bo,so
    mid=(fullmap[:,[0,2]].min(axis=0)+fullmap[:,[0,2]].max(axis=0))/2
    regions=[]
    for highx in [False,True]:
        for highz in [False,True]:
            mask=((fullmap[:,0]>=mid[0])==highx)&((fullmap[:,2]>=mid[1])==highz)
            regions.append(dict(region=('High' if highx else 'Low')+' X / '+('High' if highz else 'Low')+' Z',
                baseline_points=int(mask.sum()),fraction_within_0_20m=float(np.mean(d[mask]<=.2))))
    write(out/'scene_coverage.json',dict(baseline_to_selected=bc,selected_to_baseline=sc,occupancy=occ,regions=regions,
        limitation='Relative observed-map agreement in fixed reference; combines changed viewpoints, density and pose error. No absolute room/surface completeness GT.'))
    csv_write(out/'spatial_coverage.csv',regions)
    baseexec=read(a.BASE/'command/execution.json');selexec=read(out/'command/execution.json')
    baseobs=read(a.BASE/'observation/observer_summary.json');selobs=read(obs/'observer_summary.json')
    summary=[]
    for name,count,errors,ex,ob,points,same_errors in [
        ('P2-A FullBatch',320,be,baseexec,baseobs,len(fullmap),same),
        ('P2-B Selected',n,se,selexec,selobs,len(selectedmap),se)]:
        summary.append(dict(run=name,frames=count,retained_fraction=count/320,pairs=count-1,observed_factors=8*count-6,
            mean_l2_m=float(errors.mean()),same_frame_mean_l2_m=float(same_errors.mean()),
            worker_runtime_s=ex['elapsed_s'],reconstruction_function_s=ob['reconstruction_s_with_observation'],
            observer_overhead_s=ob['return_observer_overhead_s'],map_points=points,peak_tree_rss_bytes=ex['peak_tree_rss_bytes']))
    csv_write(out/'comparison.csv',summary)
    criteria=dict(worker_time_reduced=selexec['elapsed_s']<baseexec['elapsed_s'],
        same_frame_error_increase_within_0_05m=bool(se.mean()-same.mean()<=.05),
        observed_map_coverage_at_least_0_85=bool(bc['fraction_within_threshold']>=.85))
    comparison=dict(status='Scientific validation passed; human visual acceptance pending',runs=summary,
        worker_time_reduction_fraction=1-selexec['elapsed_s']/baseexec['elapsed_s'],
        function_time_reduction_fraction=1-selobs['reconstruction_s_with_observation']/baseobs['reconstruction_s_with_observation'],
        same_frame_mean_l2_difference_m=float(se.mean()-same.mean()),preregistered_tradeoff_criteria=criteria,
        tradeoff_supported_under_preregistered_criteria=all(criteria.values()),
        selected_max_l2_m=float(se.max()),selected_max_l2_original_frame=frames[int(se.argmax())],
        turtle=delta,new_selected_measurements=len(factors),coverage=bc,
        runtime_caveat='Worker includes imports, observer/export, evaluation, native image and Turtle write. Baseline measures/seals 2554 factors; Selected queries and writes run only. Neither includes preflight or separate comparison/plot worker. Function timer is the secondary consistent computational boundary.',
        fairness='P2-A uses 320 historical inputs; P2-B only S. Same-frame evaluation equalizes targets, not reconstruction information.',
        conclusion_limit='One realization, no significance or optimal retention inference; geometry/coverage needs visual review.')
    figdir=out/'figures';figdir.mkdir(exist_ok=False);manifest={}
    def save(fig,name):
        fig.savefig(figdir/name,dpi=170,bbox_inches='tight');plt.close(fig);manifest[name]=sha(figdir/name)
    maps=[fullmap,selectedmap];col=[np.load(a.BASE/'observation/map_colors.npy',mmap_mode='r'),arrays['map_colors']]
    bounds=np.stack([np.minimum(fullmap.min(axis=0),selectedmap.min(axis=0)),np.maximum(fullmap.max(axis=0),selectedmap.max(axis=0))])
    strides=[max(1,int(np.ceil(len(m)/150000))) for m in maps]
    for view3d in [False,True]:
        fig=plt.figure(figsize=(15,7))
        for j,(m,c,pp,tt,name,stride) in enumerate(zip(maps,col,[bpred,spred],[btruth,struth],['P2-A FullBatch','P2-B Selected'],strides)):
            ax=fig.add_subplot(1,2,j+1,projection='3d' if view3d else None)
            p=m[::stride]*[1,-1,-1]
            if view3d:
                ax.scatter(p[:,0],p[:,2],p[:,1],c=c[::stride],s=.25,rasterized=True)
                for path,color,label in [(pp,'red','Estimated'),(tt,'black','GT')]:ax.plot(path[:,0],path[:,2],path[:,1],c=color,label=label,lw=1)
                ax.set(xlim=bounds[:,0],ylim=-bounds[::-1,2],zlim=-bounds[::-1,1],xlabel='X (m)',ylabel='Z (m)',zlabel='Y up (m)')
                ax.set_box_aspect(np.ptp(bounds[:,[0,2,1]],axis=0));ax.view_init(55,-65)
            else:
                ax.scatter(p[:,0],p[:,2],c=c[::stride],s=.3,rasterized=True)
                for path,color,label in [(pp,'red','Estimated'),(tt,'black','GT')]:ax.plot(path[:,0],path[:,2],c=color,label=label,lw=1)
                ax.set(xlim=bounds[:,0],ylim=-bounds[::-1,2],xlabel='X (m)',ylabel='Z (m)');ax.set_aspect('equal')
            ax.set_title(name);ax.legend(fontsize=8)
        fig.subplots_adjust(wspace=.2);save(fig,'reconstruction_3d.png' if view3d else 'reconstruction_top_down.png')
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    for ax,pp,tt,title in zip(axes,[bpred,spred],[btruth,struth],['P2-A 320 inputs','P2-B selected inputs']):
        ax.plot(pp[:,0],pp[:,2],c='red',label='Estimated');ax.plot(tt[:,0],tt[:,2],c='black',label='GT')
        ax.set(title=title,xlim=bounds[:,0],ylim=-bounds[::-1,2],xlabel='X (m)',ylabel='Z (m)');ax.set_aspect('equal');ax.legend()
    save(fig,'trajectories.png')
    fig,ax=plt.subplots(figsize=(12,4));ax.plot(frames,same,label='P2-A saved poses at S');ax.plot(frames,se,label='P2-B only S')
    ax.set(xlabel='Original frame',ylabel='L2 (m)',title='Same-frame fixed-reference L2');ax.legend();ax.grid(alpha=.2);save(fig,'same_frame_l2.png')
    fig,axes=plt.subplots(4,2,figsize=(13,12))
    for ax,factor in zip(axes.flat,stats['baseline']):
        for rows,label in [(baseline_factors,'P2-A'),(factors,'P2-B new selected pairs')]:
            v=[float(r['value']) for r in rows if r['factor']==factor]
            ax.hist(v,bins=25,alpha=.5,density=True,label=label)
        ax.set(title=factor,ylabel='Density');ax.legend(fontsize=7)
    fig.tight_layout();save(fig,'eight_factor_distributions.png')
    fig,axes=plt.subplots(1,3,figsize=(13,4))
    for ax,key,label in zip(axes,['same_frame_mean_l2_m','worker_runtime_s','frames'],['Same-frame mean L2 (m)','Worker time (s)','Frame count']):
        ax.bar(['P2-A','P2-B'],[r[key] for r in summary]);ax.set_title(label)
    fig.tight_layout();save(fig,'comparison_metrics.png')
    write(out/'comparison.json',comparison)
    write(out/'figure_manifest.json',dict(figures=manifest,plot_strides=strides,plot_point_counts=[len(m[::s]) for m,s in zip(maps,strides)],
        full_maps_saved_separately=True,sources=dict(baseline_map=sha(a.BASE/'observation/map_points.npy'),selected_map=sha(obs/'map_points.npy'),
        baseline_poses=sha(a.BASE/'observation/camera_poses.npy'),selected_poses=sha(obs/'camera_poses.npy'),gt=sha(a.CAPTURE/'GT_pose.npy')),
        caption='Shared metric bounds, deterministic stride displays; full map/coverage not sampled. Red estimated, black GT; no fitted alignment.'))
    (out/'research_conclusions.md').write_text('''# P2-B 單次結果與人工驗收素材\n\n'''+
        '\n'.join('- '+str(k)+'：'+str(v) for k,v in comparison.items())+
        '\n\n品質因素分布與場景象限關係為描述性證據；新配對跨距與取樣組成已改變，不能直接將分布變化當成因果。圖中缺失須人工對照房間／轉角觀測，不能由點數比例推論完整率。單次實驗無統計顯著性；不得調整規則重跑。\n')
    return comparison
