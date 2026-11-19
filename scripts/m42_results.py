"""Offline validation/plots of the single M4.2 run; never starts reconstruction."""
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
from scipy.spatial.transform import Rotation
from scripts.m42_integrity import ROOT, read
from scripts.m42_monitor import write
from scripts.m4_capture_check import sha
from scripts.m32_experiments import validate_evidence


def csv_write(path,rows):
    with Path(path).open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def results(out,experiment,capture,expected_frames=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=Path(out); experiment=Path(experiment); capture=Path(capture)
    obs=out/'observation'; ttl=experiment/(experiment.name+'.ttl')
    expected_frames=list(range(1,321)) if expected_frames is None else list(expected_frames)
    n=len(expected_frames)
    exp,rows,mean=validate_evidence(ttl,obs,expected_frames)
    actual=read(obs/'actual_reconstruct_arguments.json')
    if (actual['version'],actual['voxel_size'],actual['registration_seed'],actual['down_voxel'],
        actual['build_cloud'],actual['frames'])!=('open3d',.05,0,.05,True,expected_frames):
        raise RuntimeError('Effective pipeline arguments mismatch')
    transforms=[json.loads(s) for s in (obs/'transforms.jsonl').read_text().splitlines()]
    if [(r['prev_stem'],r['stem']) for r in transforms]!=list(zip(expected_frames,expected_frames[1:])):
        raise RuntimeError('Actual pairs differ from 319 adjacent pairs')
    if not all(r['accepted_by_core'] for r in transforms): raise RuntimeError('Unaccepted transform')
    for filename,key in [('pairwise_icp.npy','icp_transformation'),('pairwise_ransac.npy','trans_init')]:
        values=np.load(obs/filename,allow_pickle=False)
        if values.shape!=(n-1,4,4): raise RuntimeError('Pairwise shape mismatch')
        np.testing.assert_array_equal(values,np.asarray([r[key] for r in transforms]))
    meta=read(obs/'map_summary.json')
    arrays={}
    for name,spec in meta['arrays'].items():
        path=obs/(name+'.npy')
        if sha(path)!=spec['sha256']: raise RuntimeError('Map SHA mismatch')
        a=np.load(path,mmap_mode='r',allow_pickle=False)
        if list(a.shape)!=spec['shape'] or str(a.dtype)!=spec['dtype']: raise RuntimeError('Map layout mismatch')
        for j in range(0,len(a),65536):
            if not np.isfinite(a[j:j+65536]).all(): raise RuntimeError('Nonfinite map')
        arrays[name]=a
    if not meta['full_returned_map'] or meta['sample_stride']!=1: raise RuntimeError('Incomplete map')
    before=sha(ttl)
    cmd=[sys.executable,str(ROOT/'api.py'),'explore',str(experiment)]
    result=subprocess.run(cmd,capture_output=True,text=True)
    (out/'explore.stdout.log').write_text(result.stdout)
    (out/'explore.stderr.log').write_text(result.stderr)
    if result.returncode or sha(ttl)!=before: raise RuntimeError('Official Explore failed/modified TTL')
    if len(list((experiment/'plots').glob('*.html')))<4: raise RuntimeError('Official Explore plots missing')
    csv_write(out/'factors.csv',rows)
    gt=np.load(capture/'GT_pose.npy',allow_pickle=False).astype(float)
    q=gt[0,3:]; rot=Rotation.from_quat([q[1],q[2],q[3],q[0]]).as_matrix()
    truth=(gt[:,:3]-gt[0,:3])@rot
    pred=np.load(obs/'positions.npy')@np.diag([1.,-1.,-1.])
    error=np.linalg.norm(pred-truth,axis=1)
    np.testing.assert_allclose(error.mean(),mean,atol=1e-12,rtol=0)
    np.save(out/'gt_centers_evaluation.npy',truth)
    csv_write(out/'per_frame_l2.csv',[dict(frame=expected_frames[i],l2_m=float(v)) for i,v in enumerate(error)])
    figdir=out/'figures'; figdir.mkdir(exist_ok=False)
    captions={}
    def save(fig,name,caption):
        fig.savefig(figdir/name,dpi=180,bbox_inches='tight'); plt.close(fig)
        captions[name]=dict(caption=caption,sha256=sha(figdir/name))
    stride=max(1,int(np.ceil(len(arrays['map_points'])/150000)))
    points=arrays['map_points'][::stride]*np.array([1.,-1.,-1.])
    colors=arrays['map_colors'][::stride]
    def scene(ax,view3d=False):
        if view3d:
            ax.scatter(points[:,0],points[:,2],points[:,1],c=colors,s=.3,rasterized=True)
            for path,color,label in [(pred,'red','Estimated'),(truth,'black','Ground truth')]:
                ax.plot(path[:,0],path[:,2],path[:,1],c=color,label=label,lw=1.3)
            ax.set(xlabel='X (m)',ylabel='Z (m)',zlabel='Y up (m)'); ax.view_init(28,-55)
        else:
            ax.scatter(points[:,0],points[:,2],c=colors,s=.4,rasterized=True)
            ax.plot(pred[:,0],pred[:,2],c='red',label='Estimated',lw=1.2)
            ax.plot(truth[:,0],truth[:,2],c='black',label='Ground truth',lw=1.2)
            ax.set(xlabel='X (m)',ylabel='Z (m)'); ax.set_aspect('equal')
        ax.legend(fontsize=8)
    fig,ax=plt.subplots(figsize=(10,8)); scene(ax)
    ax.set_title('P2-A baseline: %d frames; Mean L2 = %.6f m'%(n,mean))
    caption=('Same-call complete returned map saved in map_points.npy/map_colors.npy; figure uses deterministic '
        'stride %d (%d displayed points), ceiling already removed by the official pipeline. Fixed first-camera '
        'reference, display flips Y/Z. Estimated red, GT black. No fitted alignment. '
        'Viewpoint coverage is not a measured whole-floor surface completeness percentage.'%(stride,len(points)))
    save(fig,'reconstruction_top_down.png',caption)
    fig=plt.figure(figsize=(11,8)); ax=fig.add_subplot(111,projection='3d'); scene(ax,True)
    ax.set_title('P2-A baseline: ceiling-cropped returned map')
    save(fig,'reconstruction_3d.png',caption)
    fig,axes=plt.subplots(2,2,figsize=(12,10))
    xmin,zmin=points[:,[0,2]].min(axis=0); xmax,zmax=points[:,[0,2]].max(axis=0)
    xm,zm=(xmin+xmax)/2,(zmin+zmax)/2
    for ax,(x0,x1,z0,z1),name in zip(axes.flat,
        [(xmin,xm,zmin,zm),(xm,xmax,zmin,zm),(xmin,xm,zm,zmax),(xm,xmax,zm,zmax)],
        ['Low X / Low Z','High X / Low Z','Low X / High Z','High X / High Z']):
        scene(ax); ax.set(xlim=(x0,x1),ylim=(z0,z1),title=name)
    save(fig,'spatial_regions.png',caption+' Four map-extent quadrants; these are not inferred room names or route coverage labels.')
    fig,ax=plt.subplots(figsize=(11,4)); ax.plot(expected_frames,error,c='#315f85')
    ax.set(xlabel='Original frame',ylabel='L2 (m)',title='P2-A per-frame trajectory error'); ax.grid(alpha=.2)
    save(fig,'per_frame_l2.png','All 320 same-run camera centers evaluated in fixed first-camera reference; no best-fit transform.')
    fig,axes=plt.subplots(4,2,figsize=(12,12))
    factor_stats={}
    for ax,factor in zip(axes.flat,sorted(set(r['factor'] for r in rows))):
        subset=sorted([r for r in rows if r['factor']==factor],key=lambda r:r['current'])
        values=np.array([r['value'] for r in subset])
        ax.plot([r['current'] for r in subset],values,lw=.8)
        ax.set(title=factor,xlabel='Current original frame'); ax.grid(alpha=.2)
        factor_stats[factor]=dict(count=len(values),min=float(values.min()),median=float(np.median(values)),
            p05=float(np.percentile(values,5)),p95=float(np.percentile(values,95)),max=float(values.max()))
    fig.tight_layout(); save(fig,'eight_quality_factors.png','Raw official pipeline factors; 320 observations per single-frame factor and 319 per pair factor; no qualification thresholds assigned.')
    write(out/'factor_statistics.json',factor_stats)
    execution=read(out/'command/execution.json')
    observer=read(obs/'observer_summary.json')
    current=dict(run='P2-A baseline',status='Success',floor=2,frames=n,pairs=n-1,factors=8*n-6,
        mean_l2_m=mean,registration_voxel_m=.05,seed=0,map_voxel_m=.05,
        runtime_s=execution['elapsed_s'],runtime_boundary='guarded worker incl imports, observation, export, evaluation, plots, seal and baseline write',
        returned_map_points=meta['point_count'],peak_tree_rss_bytes=execution['peak_tree_rss_bytes'])
    csv_write(out/'baseline_comparison.csv',[current])
    legacy=ROOT/'research_outputs/phase1_report_assets/data/run_comparison.csv'
    comparison=[]
    if legacy.exists():
        shutil.copyfile(legacy,out/'phase1_comparison_source.csv')
        with legacy.open() as f:
            for row in csv.DictReader(f):
                comparison.append(dict(run=row['run'],floor=1,status='Failed Registration' if row['run']=='B1' else 'Success',
                    frames=row['frames'],mean_l2_m=row['mean_l2_m'],voxel_m=row['voxel_m'],seed=row['seed'],
                    map_voxel_m=row['map_voxel_m'],runtime_s=row['runtime_s'],
                    runtime_boundary='Legacy recorded boundary; see Phase 1 handoff; B1 frames are accepted pose prefix',
                    source=str(legacy.relative_to(ROOT)),source_sha256=sha(legacy)))
    comparison.append(dict(run='P2-A baseline',floor=2,status='Success',frames=n,mean_l2_m=mean,
        voxel_m=.05,seed=0,map_voxel_m=.05,runtime_s=execution['elapsed_s'],
        runtime_boundary=current['runtime_boundary'],source='validation.json',source_sha256=None))
    csv_write(out/'all_run_comparison.csv',comparison)
    write(out/'figure_manifest.json',dict(figures=captions,map_sources=meta['arrays'],
        trajectory_sha256=sha(obs/'camera_poses.npy'),ttl_sha256=sha(ttl),visualization_stride=stride))
    (out/'candidate_questions.md').write_text('''# Candidate questions only; no intervention executed

- Do low RANSAC support and high residual intervals coincide with subsequent trajectory-error growth?
- Does ICP retain high local fitness during large global drift, indicating locally plausible ambiguous matches?
- Do low voxel yields near connecting spaces predict unstable registration, and would a predeclared bridging-frame rule help?
- Which map quadrants show doubled walls, displaced surfaces or sparse observations in the saved views?

Room names, route segments and absolute floor completeness require human interpretation; no room labels or percentages are fabricated. These questions do not authorize P2-B, a new seed or voxel run.
''')
    write(out/'validation.json',dict(passed=True,counts=dict(frames=n,pairs=n-1,factors=len(rows)),
        same_run_factor_match=True,seal_valid=True,baseline_only=True,mean_l2_m=mean,
        full_returned_map=meta,execution=execution,observer=observer,baseline=current,
        scope_limit='Scientific evidence complete; room-by-room visual interpretation remains human review.'))
    return current
