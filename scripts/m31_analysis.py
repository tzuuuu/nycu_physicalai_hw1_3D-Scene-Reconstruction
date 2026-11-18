"""M3.1 正式執行完成後的離線比較；不執行配準或改寫正式實驗。"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import m31_ablation as a
from scripts import m3_diagnose as m
import numpy as np

PREP=m.ROOT/'research_outputs/m31_20261118_preparation_01'
OBS=m.ROOT/'research_outputs/m31_20261118_official_observation_01'
COMMAND=m.ROOT/'research_outputs/m31_20261118_official_command_01'
BASE_RUN=m.ROOT/'research_outputs/m3_20261118_diagnostic_02'


def read_jsonl(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def cumulative(transforms):
    poses=[np.eye(4)]
    for t in transforms:
        poses.append(poses[-1]@np.array(t['icp_transformation']))
    return np.array(poses)


def cell_rows(points,size=.1):
    """固定首相機座標格網；此解析度只供覆蓋評估，不參與重建。"""
    coords=np.floor(points/size).astype(np.int32)
    dtype=np.dtype([('x','<i4'),('y','<i4'),('z','<i4')])
    return np.unique(np.ascontiguousarray(coords).view(dtype).ravel())


def coverage_proxy(gt,output,baseline_yield):
    # GT僅用於離線觀測覆蓋評估；不建立或替換正式地圖／配準。
    intr,paths,scale=m.utils._capture_inputs(str(m.DATA),None)
    retained=[]; excluded=None; minimum_y=float('inf')
    for ordinal,(rgb_path,depth_path) in enumerate(paths):
        stem=int(Path(depth_path).stem)
        rgb,depth=m.utils._read_rgbd(rgb_path,depth_path,scale)
        cloud=m.utils.depth_image_to_point_cloud(rgb,depth,**intr).voxel_down_sample(.05)
        points=np.asarray(cloud.points)
        if len(points)!=baseline_yield[stem]:
            raise RuntimeError('Coverage voxel count differs from baseline frame')
        transformed=points@gt[ordinal,:3,:3].T+gt[ordinal,:3,3]
        minimum_y=min(minimum_y,float(transformed[:,1].min()))
        if stem==104: excluded=transformed.copy()
        else: retained.append(transformed)
    threshold=minimum_y+1.
    kept=np.concatenate(retained)
    kept=kept[kept[:,1]>threshold]
    removed=excluded[excluded[:,1]>threshold]
    kept_cells=cell_rows(kept); removed_cells=cell_rows(removed)
    lost=np.setdiff1d(removed_cells,kept_cells,assume_unique=True)
    full=np.union1d(kept_cells,removed_cells)
    np.savez_compressed(output/'gt_observation_coverage_cells.npz',full=full,retained=kept_cells,lost=lost)
    sample=kept[::max(1,int(np.ceil(len(kept)/100000)))]
    np.save(output/'gt_reference_sample.npy',sample)
    return {'kind':'GT_reference_observed_coverage_proxy_not_reconstructed_map_accuracy',
            'per_frame_map_voxel_m':.05,'evaluation_grid_m':.1,'common_ceiling_y_threshold_m':threshold,
            'full_191_observed_cells':len(full),'retained_190_observed_cells':len(kept_cells),
            'cells_only_supported_by_frame104':len(lost),
            'retained_observed_cell_fraction':len(kept_cells)/len(full),
            'limitation':'Fixed-pose observed support only; no complete scene surface GT, no absolute floor coverage percentage.'}


def analyze(output):
    output=m.fresh_output(output)
    execution=json.loads((COMMAND/'execution.json').read_text())
    if execution['exit_code']!=0:
        raise RuntimeError('Official run failed: preserve evidence; no further registration permitted')
    before=json.loads((PREP/'baseline.before.json').read_text())
    after=a.snapshot(a.TTL); a.verify_preservation(before,after)
    if len(after['run_nodes'])!=2:
        raise RuntimeError('Expected one Baseline and one Selected run')
    exp=m.api.read_experiment(str(a.TTL)); graph=exp['graph']
    selected=m.api.data_run_iri(exp['exp_name'],'selected')
    used=sorted(int(graph.value(node,m.api.HW1.frameIndex)) for node in graph.objects(selected,m.api.HW1.usedFrame))
    a.verify_selection(used)
    assert int(graph.value(selected,m.api.HW1.runFrameCount))==190
    assert int(graph.value(selected,m.api.HW1.spliceCount))==1
    assert int(graph.value(selected,m.api.HW1.maxGapLength))==1
    protected=json.loads((PREP/'protected.before.json').read_text())
    allowed={str(a.TTL.relative_to(m.ROOT)),str((a.EXP/'reconstruction.png').relative_to(m.ROOT))}
    changed=[]
    for name,value in protected.items():
        path=m.ROOT/name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=value:
            changed.append(name)
    if set(changed)-allowed:
        raise RuntimeError('Unexpected protected file change: '+str(set(changed)-allowed))
    original=json.loads((PREP/'preregistration.json').read_text())
    if m.capture_digest()!=original['capture_sha256']:
        raise RuntimeError('Capture changed')
    m.dump(output/'turtle_and_source_validation.json',{
        'before':before,'after':after,'preservation_passed':True,
        'protected_existing_file_count':len(protected),'changed_files':changed,
        'only_expected_turtle_and_latest_image_changes':True,'capture_unchanged':True,
        'selected_frames':used,'selected_mode':str(graph.value(selected,m.api.HW1.selectionMode)),
        'selected_frame_count':190,'selected_splice_count':1,'selected_max_gap_length':1})
    observer=json.loads((OBS/'observer_summary.json').read_text())
    assert observer['reconstruct_calls']==1 and observer['pair_events']==189 and observer['frame_events']==190
    events=read_jsonl(OBS/'events.jsonl'); transforms=read_jsonl(OBS/'transforms.jsonl')
    assert [(t['prev_stem'],t['stem']) for t in transforms]==list(zip(used,used[1:]))
    poses=cumulative(transforms); positions=np.load(OBS/'positions.npy')
    np.testing.assert_allclose(poses[:,:3,3],positions,atol=1e-12,rtol=0)
    # 只有上述正式重建完整完成且寫入驗證通過後，才讀取GT陣列。
    full_gt=m.gt_camera_poses(np.load(m.DATA/'GT_pose.npy'))
    indices=np.array(used)-1
    gt=full_gt[indices]
    baseline_transforms=read_jsonl(BASE_RUN/'transforms.jsonl')
    baseline_poses=cumulative(baseline_transforms)
    np.testing.assert_allclose(baseline_poses[:,:3,3],np.load(BASE_RUN/'positions.npy'),atol=1e-12,rtol=0)
    baseline_error=np.linalg.norm(baseline_poses[:,:3,3]-full_gt[:,:3,3],axis=1)
    error=np.linalg.norm(positions-gt[:,:3,3],axis=1)
    official_l2=json.loads((OBS/'official_evaluation.json').read_text())['mean_l2_raw_m']
    np.testing.assert_allclose(error.mean(),official_l2,atol=1e-12,rtol=0)
    assert float(graph.value(selected,m.api.HW1.mapMeanL2))==m.api._storable(official_l2)
    np.savez(output/'poses_offline.npz',frames=used,predicted=poses,gt=gt,baseline=baseline_poses)
    frame_events={e['stem']:e for e in events if e['kind']=='frame'}
    rows=[]
    for i,stem in enumerate(used):
        r={'frame':stem,'selected_l2_m':float(error[i]),'baseline_l2_m':float(baseline_error[stem-1]),
           'selected_orientation_error_deg':m.angle(gt[i,:3,:3].T@poses[i,:3,:3]),
           'baseline_orientation_error_deg':m.angle(full_gt[stem-1,:3,:3].T@baseline_poses[stem-1,:3,:3]),
           'raw_point_count':frame_events[stem]['raw_point_count'],'point_yield':frame_events[stem]['point_yield']}
        for prefix,array in [('selected',positions[i]),('baseline',baseline_poses[stem-1,:3,3]),('gt',gt[i,:3,3])]:
            r.update({prefix+'_'+axis+'_m':float(v) for axis,v in zip('xyz',array)})
        rows.append(r)
    pairs=[]
    for i,t in enumerate(transforms,1):
        truth=np.linalg.inv(gt[i-1])@gt[i]
        pair=m.pair_metrics(np.array(t['icp_transformation']),truth,np.array(t['trans_init']))
        pair.update(previous=t['prev_stem'],current=t['stem'])
        pair.update({k:t[k] for k in ['coarse_fitness','coarse_rmse','coarse_correspondences',
                                     'icp_fitness','icp_rmse','icp_correspondences']})
        pairs.append(pair)
    m.write_csv(output/'common_frame_errors.csv',rows)
    m.write_csv(output/'selected_pair_metrics.csv',pairs)
    factor_rows=[]
    for e in events:
        for key,factor in m.FIELDS.items():
            if key in e: factor_rows.append({'factor':factor,'previous':e.get('prev_stem'),
                                             'current':e['stem'],'value':e[key]})
    assert len(factor_rows)==1514
    m.write_csv(output/'selected_actual_factors.csv',factor_rows)
    bpair={(t['prev_stem'],t['stem']):t for t in baseline_transforms}
    common=[t for t in transforms if (t['prev_stem'],t['stem']) in bpair]
    matrix_differences={name:max(float(np.abs(np.array(t[name])-np.array(bpair[t['prev_stem'],t['stem']][name])).max())
                                for t in common) for name in ['trans_init','icp_transformation']}
    baseline_events=read_jsonl(BASE_RUN/'events.jsonl')
    baseline_frame={e['stem']:e for e in baseline_events if e['kind']=='frame'}
    for stem in used:
        assert frame_events[stem]==baseline_frame[stem]
    matching_factors=0
    for t in common:
        b=bpair[t['prev_stem'],t['stem']]
        for k in ['coarse_fitness','coarse_rmse','coarse_correspondences','icp_fitness','icp_rmse','icp_correspondences']:
            matching_factors+=int(t[k]==b[k])
    prefix_diff=float(np.abs(poses[:103]-baseline_poses[:103]).max())
    provenance={'kind':'Exploratory Ablation','selection_informed_by_gt_diagnosis':True,
                'formal_execution_commit':observer['git_commit'],'reconstruction_calls':1,
                'baseline_trajectory_source':str(BASE_RUN),
                'baseline_trajectory_limitation':'M3.0 matching diagnostic; original formal CLI did not save per-frame poses',
                'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    m.dump(output/'analysis_provenance.json',provenance)
    coverage=coverage_proxy(full_gt,output,{s:e['point_yield'] for s,e in baseline_frame.items()})
    m.dump(output/'coverage_proxy.json',coverage)
    summary={'kind':'Exploratory Ablation','baseline_frames':191,'selected_frames':190,'retained_fraction':190/191,
             'baseline_full_official_mean_l2_m':json.loads((m.BASE/'validation.json').read_text())['mean_l2_raw_m'],
             'baseline_common190_mean_l2_m':float(baseline_error[indices].mean()),
             'selected_common190_official_mean_l2_m':official_l2,
             'new_pair103_105':next(p for p in pairs if p['previous']==103 and p['current']==105),
             'global_frame105':next(r for r in rows if r['frame']==105),
             'global_frame191':next(r for r in rows if r['frame']==191),
             'max_selected_l2_m':float(error.max()),'max_selected_l2_frame':used[int(np.argmax(error))],
             'max_selected_global_orientation_error_deg':max(r['selected_orientation_error_deg'] for r in rows),
             'max_selected_pair_rotation_error_deg':max(p['relative_rotation_error_deg'] for p in pairs),
             'near180_pair_errors_frames_over150deg':[p['current'] for p in pairs if p['relative_rotation_error_deg']>150],
             'near180_global_errors_frames_over150deg':[r['frame'] for r in rows if r['selected_orientation_error_deg']>150],
             'unchanged_pairs_count':len(common),'common_pair_max_matrix_differences':matrix_differences,
             'common_pair_factor_values_equal_count':matching_factors,
             'prefix1_103_max_pose_difference':prefix_diff,
             'baseline_valid_depth_points_total':sum(e['raw_point_count'] for e in baseline_frame.values()),
             'selected_valid_depth_points_total':sum(e['raw_point_count'] for e in frame_events.values()),
             'baseline_voxel_points_total':sum(e['point_yield'] for e in baseline_frame.values()),
             'selected_voxel_points_total':sum(e['point_yield'] for e in frame_events.values()),
             'execution':execution,'observer':observer,'coverage_proxy':coverage,
             'selected_map':json.loads((OBS/'map_summary.json').read_text())}
    m.dump(output/'summary.json',summary)
    plots(output,rows,pairs,poses,gt,baseline_poses,full_gt)
    print(json.dumps(summary,indent=2))


def plots(output,rows,pairs,poses,gt,baseline,full_gt):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    def save(fig,name):
        fig.savefig(output/name,dpi=150); plt.close(fig)
    x=[r['frame'] for r in rows]
    fig,axes=plt.subplots(3,1,figsize=(13,10),constrained_layout=True)
    axes[0].plot(x,[r['baseline_l2_m'] for r in rows],label='Baseline on common 190 frames',color='firebrick')
    axes[0].plot(x,[r['selected_l2_m'] for r in rows],label='Selected: exclude only 104',color='teal')
    axes[0].set_ylabel('L2 (m)'); axes[0].legend()
    axes[1].plot(x,[r['baseline_l2_m'] for r in rows],color='firebrick')
    axes[1].plot(x,[r['selected_l2_m'] for r in rows],color='teal'); axes[1].set_yscale('symlog',linthresh=.01)
    axes[1].set_ylabel('L2 (m, symlog)')
    axes[2].plot(x,[r['baseline_orientation_error_deg'] for r in rows],label='Baseline',color='firebrick')
    axes[2].plot(x,[r['selected_orientation_error_deg'] for r in rows],label='Selected',color='teal')
    axes[2].set_ylabel('Global orientation error (deg)')
    for ax in axes:
        ax.axvline(104,color='grey',linestyle='--'); ax.grid(alpha=.3); ax.set_xlabel('Original frame stem; 104 excluded from Selected')
    fig.suptitle('M3.1 Exploratory Ablation (choice informed by prior GT diagnosis)')
    save(fig,'common_frame_comparison.png')
    fig,axes=plt.subplots(2,1,figsize=(12,8),constrained_layout=True)
    xx=[p['current'] for p in pairs]
    for ax,coarse,icp,ylabel in zip(axes,['coarse_translation_error_m','coarse_rotation_error_deg'],
                                  ['relative_translation_error_m','relative_rotation_error_deg'],['Local translation error (m)','Local rotation error (deg)']):
        ax.plot(xx,[p[coarse] for p in pairs],label='RANSAC')
        ax.plot(xx,[p[icp] for p in pairs],label='ICP'); ax.set_yscale('symlog',linthresh=.001)
        ax.axvline(105,color='red',linestyle='--',label='New pair 103 -> 105'); ax.grid(alpha=.3)
        ax.set(xlabel='Current frame stem',ylabel=ylabel); ax.legend()
    save(fig,'selected_relative_errors.png')
    fig,ax=plt.subplots(figsize=(9,7),constrained_layout=True)
    for points,color,label in [(baseline[:,:3,3],'firebrick','Baseline diagnostic'),(poses[:,:3,3],'teal','Selected actual CLI'),(full_gt[:,:3,3],'black','GT evaluation only')]:
        ax.plot(points[:,0],points[:,2],color=color,label=label)
    ax.axis('equal'); ax.legend(); ax.grid(alpha=.3); ax.set(xlabel='First camera X (m)',ylabel='First camera Z (m)')
    save(fig,'trajectory_comparison.png')
    fig,axes=plt.subplots(1,2,figsize=(15,7),constrained_layout=True)
    for ax,name,label in zip(axes,['reconstruction_baseline.png','reconstruction_selected.png'],['Official Baseline (191)','Official Selected (190)']):
        ax.imshow(plt.imread(a.EXP/name)); ax.set_title(label); ax.axis('off')
    save(fig,'official_map_comparison.png')
    sample=np.load(OBS/'map_sample.npz'); reference=np.load(output/'gt_reference_sample.npy')
    fig,axes=plt.subplots(1,2,figsize=(14,6),constrained_layout=True)
    all_points=np.concatenate([sample['points'],reference]); mins=all_points.min(axis=0); maxs=all_points.max(axis=0)
    for ax,pts,colors,label in [(axes[0],sample['points'],sample['colors'],'Selected map (actual CLI sample)'),
                               (axes[1],reference,'steelblue','GT-posed retained observations (evaluation only)')]:
        ax.scatter(pts[:,0],pts[:,2],s=.3,c=colors,alpha=.5)
        ax.set(xlabel='First camera X (m)',ylabel='First camera Z (m)',title=label,
               xlim=(mins[0],maxs[0]),ylim=(mins[2],maxs[2])); ax.set_aspect('equal')
    save(fig,'selected_map_reference.png')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',required=True)
    analyze(parser.parse_args().output)
