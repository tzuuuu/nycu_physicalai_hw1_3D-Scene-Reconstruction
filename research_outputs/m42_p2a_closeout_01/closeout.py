"""Read-only M4.2 closeout; never imports/calls reconstruction entrypoints."""
from pathlib import Path
import sys,json,csv,hashlib,shutil,resource
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.m42_baseline import FORMAL,EXPERIMENT,NAME,CAPTURE
from scripts.m42_integrity import read,verify,inventory,compare,frozen_capture,historical_sources
from scripts.m42_monitor import write
from scripts.m4_capture_check import sha
from scripts.m32_experiments import validate_evidence
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path(__file__).resolve().parent
manifest=read(FORMAL/'manifest.json')
manifest_count=verify(manifest['scientific'])
shutil.copyfile(ROOT/'docs/implementation/M4_Phase2_P2A_Baseline_Acceptance.md',OUT/'runner_generated_acceptance_original.md')
config=read(FORMAL/'preregistration.json')
preflight=Path(config['preflight']); pre=read(preflight/'preflight.json')
assert pre['passed'] and sha(preflight/'preflight.json')==config['preflight_sha256']
assert all(c['passed'] for c in pre['checks'])
exp,rows,mean=validate_evidence(EXPERIMENT/(NAME+'.ttl'),FORMAL/'observation',list(range(1,321)))
source=dict(config['tracked_source_sha256'])
expected_doc=source.pop('docs/implementation/M4_Phase2_P2A_Baseline_Acceptance.md')
verify(source)
frozen_count=len(frozen_capture());core=historical_sources()
verify(read(OUT.parent/'m42_interrupted_attempt_01/manifest.json')['scientific'])
verify(read(OUT.parent/'m42_retry_after_interrupt_01/manifest.json')['scientific'])
protected=read(preflight/'protected.before.json')
after=inventory([ROOT/'eval/_data',ROOT/'experiments',ROOT/'research_outputs'],
    exclude=[FORMAL,EXPERIMENT,preflight,OUT])
protected_count=compare(protected,after,OUT/'os_metadata_closeout.jsonl')
obs=FORMAL/'observation'
meta=read(obs/'trajectory_metadata.json')
for name,spec in meta['arrays'].items():
    path=obs/(name+'.npy');a=np.load(path,mmap_mode='r',allow_pickle=False)
    assert sha(path)==spec['sha256'] and str(a.dtype)==spec['dtype'] and list(a.shape)==spec['shape']
    assert np.isfinite(a).all()
mapmeta=read(obs/'map_summary.json')
for name,spec in mapmeta['arrays'].items():
    path=obs/(name+'.npy');assert sha(path)==spec['sha256']
    a=np.load(path,mmap_mode='r',allow_pickle=False)
    assert list(a.shape)==spec['shape'] and str(a.dtype)==spec['dtype']
    for i in range(0,len(a),65536):assert np.isfinite(a[i:i+65536]).all()
assert mapmeta['full_returned_map'] and mapmeta['sample_stride']==1
monitor=[]
for directory in ['command','postprocess_command']:
    run=read(FORMAL/directory/'execution.json')
    samples=[json.loads(s) for s in (FORMAL/directory/'rss.jsonl').read_text().splitlines()]
    assert run['passed'] and run['exit_code']==0 and run['reason'] is None
    assert all(s['tree_rss_bytes']==sum(r['rss_bytes'] for r in s['pids']) for s in samples)
    assert max(s['tree_rss_bytes'] for s in samples)==run['peak_tree_rss_bytes']<3*2**30
    assert len(samples)==run['samples']
    assert read(FORMAL/directory/'watchdog.json')['status']=='disarmed_after_workload_exit'
    gaps=np.diff([s['elapsed_s'] for s in samples]);assert np.all(gaps>0)
    monitor.append(dict(stage=directory,elapsed_s=run['elapsed_s'],samples=len(samples),
        peak_tree_rss_bytes=run['peak_tree_rss_bytes'],max_sample_gap_s=float(gaps.max())))
error=[]
with (FORMAL/'per_frame_l2.csv').open() as f:
    errors=list(csv.DictReader(f));error=np.array([float(r['l2_m']) for r in errors])
assert len(error)==320 and abs(error.mean()-mean)<1e-12
largest=np.argsort(np.diff(error))[-5:][::-1]+1
summary=dict(status='M4.2 Baseline Accepted / Complete / Stopped',first_pass_success=True,
    frames=320,pairs=319,factors=len(rows),mean_l2_m=mean,
    max_l2_m=float(error.max()),max_l2_frame=int(error.argmax())+1,
    median_l2_m=float(np.median(error)),p95_l2_m=float(np.percentile(error,95)),
    largest_error_increases=[dict(current_frame=int(i)+1,increase_m=float(error[i]-error[i-1])) for i in largest],
    full_returned_map_points=mapmeta['point_count'],frozen_capture_sha_matches=frozen_count,
    protected_scientific_sha_matches=protected_count,original_run_manifest_verified_items=manifest_count,
    same_run_factor_match=True,seal_valid=True,baseline_only=True,source_core_sha256=core,
    original_runner_document_sha256=sha(OUT/'runner_generated_acceptance_original.md'),
    prepared_document_sha256=expected_doc,monitor=monitor,
    native_selftests=next(c['details'] for c in pre['checks'] if c['name']=='monitor_observer_map_selftests'),
    execution_history='One interrupted official attempt archived after explicit user cleanup request; one explicitly authorized fresh attempt succeeded; no automatic registration retry',
    archived_interrupt_manifest_sha256=sha(OUT.parent/'m42_interrupted_attempt_01/manifest.json'),
    retry_authorization_sha256=sha(OUT.parent/'m42_retry_after_interrupt_01/authorization.json'))
write(OUT/'independent_validation.json',summary)
# Alternate offline report figure: metric axis aspect and room for every label.
p=np.load(obs/'map_points.npy',mmap_mode='r'); c=np.load(obs/'map_colors.npy',mmap_mode='r')
stride=max(1,int(np.ceil(len(p)/150000)))
points=p[::stride]*np.array([1.,-1.,-1.]); colors=c[::stride]
est=np.load(obs/'positions.npy')*np.array([1.,-1.,-1.]);gt=np.load(FORMAL/'gt_centers_evaluation.npy')
fig=plt.figure(figsize=(12,9));ax=fig.add_subplot(111,projection='3d')
ax.scatter(points[:,0],points[:,2],points[:,1],c=colors,s=.5,rasterized=True)
for path,color,label in [(est,'red','Estimated'),(gt,'black','Ground truth')]:
    ax.plot(path[:,0],path[:,2],path[:,1],c=color,lw=1.4,label=label)
ax.set(xlabel='X (m)',ylabel='Z (m)');ax.set_zlabel('')
ax.set_box_aspect(np.ptp(points[:,[0,2,1]],axis=0));ax.view_init(elev=55,azim=-65)
ax.legend(loc='upper left');fig.suptitle('P2-A baseline: 320 frames; Mean L2 = %.6f m'%mean,fontsize=17)
fig.text(.92,.54,'Y up (m)',rotation=90,ha='center',va='center')
fig.subplots_adjust(left=.02,right=.87,bottom=.06,top=.91)
fig.savefig(OUT/'reconstruction_3d_report.png',dpi=180,bbox_inches='tight',pad_inches=.2);plt.close(fig)
write(OUT/'alternate_figure_provenance.json',dict(sha256=sha(OUT/'reconstruction_3d_report.png'),
    map_sources=mapmeta['arrays'],positions_sha256=sha(obs/'positions.npy'),
    gt_centers_sha256=sha(FORMAL/'gt_centers_evaluation.npy'),visualization_stride=stride,
    displayed_points=len(points),view_elevation_deg=55,view_azimuth_deg=-65,
    change='Offline display only: proportional metric axis aspect, larger label margins, Y/Z display flips. No registration, new trajectory, map correction or GT fitting.',
    process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
print(json.dumps(summary,indent=2))
