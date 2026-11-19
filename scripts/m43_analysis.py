"""Offline P2-A verification and one non-GT sparse rule; never reconstructs."""
import csv
import json
import sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from scripts.m42_integrity import ROOT, read, verify, inventory, frozen_capture, historical_sources
from scripts.m42_monitor import write
from scripts.m4_capture_check import sha
from scripts.m42_results import csv_write

BASE=ROOT/'research_outputs/m42_p2_a01_baseline_01'
CLOSE=ROOT/'research_outputs/m42_p2a_closeout_01'
EXP=ROOT/'experiments/p2_114753116_a01_baseline_01'
TTL=EXP/(EXP.name+'.ttl')
CAPTURE=ROOT/'eval/_data/second_floor/114753116/P2_A_01'
PREP=ROOT/'research_outputs/m43_p2b_preparation_01'
OUT=ROOT/'research_outputs/m43_p2b_selected_01'
SPEC=ROOT/'docs/implementation/m43/selection_rule.json'
QUERY=ROOT/'docs/implementation/m43/p2b_sparse.rq'
KEYS={'CoarseRANSACFitness':'coarse_fitness','CoarseRANSACRMSE':'coarse_rmse',
      'CoarseRANSACCorrespondences':'coarse_correspondences','ICPInlierFitness':'icp_fitness',
      'ICPInlierRMSE':'icp_rmse','ICPInlierCorrespondences':'icp_correspondences'}


def lines(path): return [json.loads(s) for s in Path(path).read_text().splitlines()]


def baseline_check(initial=True):
    """Verify old manifests without rewriting the historical document digests."""
    close_manifest=read(CLOSE/'manifest.json')['scientific']
    verify(close_manifest)
    old=dict(read(BASE/'manifest.json')['scientific'])
    document='docs/implementation/M4_Phase2_P2A_Baseline_Acceptance.md'
    old_sha=old.pop(document)
    if sha(CLOSE/'runner_generated_acceptance_original.md')!=old_sha:
        raise RuntimeError('Historical runner document snapshot mismatch')
    # The official selected CLI may refresh only the shared PNG and TTL.
    if not initial:
        old.pop(str(TTL.relative_to(ROOT)),None)
        old.pop(str((EXP/'reconstruction.png').relative_to(ROOT)),None)
    verify(old)
    frozen_capture(); historical_sources()
    import api
    exp=api.read_experiment(str(TTL))
    if exp['frame_indices']!=list(range(1,321)) or not exp['complete']:
        raise RuntimeError('Invalid original sealed factor set')
    if sum(exp['factor_counts'].values())!=2554: raise RuntimeError('Wrong original factors')
    if initial:
        from scripts.m32_experiments import validate_evidence
        validate_evidence(TTL,BASE/'observation',list(range(1,321)))
    return dict(closeout_manifest_files=len(close_manifest),baseline_artifacts=len(old),
                capture_files=642,factors=2554,seal_valid=True)


def summarize(rows):
    result={}
    for factor in sorted(set(r['factor'] for r in rows)):
        v=np.array([float(r['value']) for r in rows if r['factor']==factor])
        result[factor]=dict(count=len(v),mean=float(v.mean()),std=float(v.std()),
            **{k:float(x) for k,x in zip(['min','p05','median','p95','max'],np.percentile(v,[0,5,50,95,100]))})
    return result


def selection(rows,transforms):
    """Only raw factors and non-GT estimated pair translations are inputs."""
    reasons={i:['odd_original_index'] for i in range(1,321,2)}
    reasons.setdefault(320,[]).append('last_original_frame')
    thresholds={}; flagged=[]
    for factor in KEYS:
        subset=[r for r in rows if r['factor']==factor]
        high=factor.endswith('RMSE')
        cutoff=float(np.percentile([float(r['value']) for r in subset],95 if high else 5))
        thresholds[factor]=dict(percentile=95 if high else 5,value=cutoff,comparison='>=' if high else '<=')
        for r in subset:
            if (float(r['value'])>=cutoff if high else float(r['value'])<=cutoff):
                a,b=int(r['previous']),int(r['current'])
                flagged.append(dict(factor=factor,previous=a,current=b,value=float(r['value'])))
                for i in [a,b]: reasons.setdefault(i,[]).append('bridge_'+factor)
    for r in transforms:
        d=float(np.linalg.norm(np.asarray(r['icp_transformation'])[:3,3]))
        if d>.35:
            for i in [r['prev_stem'],r['stem']]: reasons.setdefault(i,[]).append('estimated_translation_gt_0.35m')
    return sorted(reasons),reasons,thresholds,flagged


def prepare():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import Image
    if PREP.exists() or SPEC.exists() or QUERY.exists(): raise FileExistsError('Frozen preparation already exists')
    PREP.mkdir()
    validation=baseline_check()
    with (BASE/'factors.csv').open() as f: rows=list(csv.DictReader(f))
    stats=summarize(rows); transforms=lines(BASE/'observation/transforms.jsonl')
    frames,reasons,thresholds,flagged=selection(rows,transforms)
    csv_write(PREP/'eight_factors.csv',rows)
    csv_write(PREP/'eight_factor_statistics.csv',[dict(factor=k,**v) for k,v in stats.items()])
    write(PREP/'factor_statistics.json',stats)
    csv_write(PREP/'quality_tail_pairs.csv',flagged)
    motion=[]
    for r in transforms:
        t=np.asarray(r['icp_transformation'])
        motion.append(dict(previous=r['prev_stem'],current=r['stem'],
            estimated_translation_m=float(np.linalg.norm(t[:3,3])),
            estimated_rotation_deg=float(Rotation.from_matrix(t[:3,:3]).magnitude()*180/np.pi),
            coarse_fitness=r['coarse_fitness'],icp_fitness=r['icp_fitness']))
    csv_write(PREP/'non_gt_motion.csv',motion)
    fig,axes=plt.subplots(4,2,figsize=(13,12))
    for ax,(factor,stat) in zip(axes.flat,stats.items()):
        subset=[r for r in rows if r['factor']==factor]
        x=[int(r['current']) for r in subset]; y=[float(r['value']) for r in subset]
        ax.plot(x,y,lw=.8); ax.axhline(stat['p05'],c='orange',ls='--',lw=.6)
        ax.axhline(stat['p95'],c='red',ls='--',lw=.6)
        ax.set(title=factor,xlabel='Original current frame');ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(PREP/'eight_factor_series.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(4,2,figsize=(13,12))
    for ax,(factor,stat) in zip(axes.flat,stats.items()):
        ax.hist([float(r['value']) for r in rows if r['factor']==factor],bins=30)
        ax.set(title=factor,ylabel='Observations')
    fig.tight_layout();fig.savefig(PREP/'eight_factor_distributions.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(3,1,figsize=(13,8),sharex=True)
    for ax,key in zip(axes[:2],['estimated_translation_m','estimated_rotation_deg']):
        ax.plot([r['current'] for r in motion],[r[key] for r in motion]);ax.set_ylabel(key)
    axes[2].vlines(frames,0,1,lw=.7); axes[2].set(xlabel='Original frame',ylabel='Selected')
    fig.tight_layout();fig.savefig(PREP/'non_gt_motion_and_selection.png',dpi=150);plt.close(fig)
    # Diagnostic contact sheet: fixed regions, chosen before any Selected evaluation.
    indices=[1,2,73,74,75,103,104,105,122,123,124,146,147,148,149,150,151,257,258,259,296,297,301,320]
    fig,axes=plt.subplots(4,6,figsize=(15,10))
    for ax,i in zip(axes.flat,indices):
        ax.imshow(Image.open(CAPTURE/'rgb'/('%d.png'%i)));ax.set_title('Frame %d'%i);ax.axis('off')
    fig.tight_layout();fig.savefig(PREP/'diagnostic_rgb_contact_sheet.png',dpi=140);plt.close(fig)
    redundancy=sum(r['icp_fitness']>=.9 and r['estimated_translation_m']<=.21 and r['estimated_rotation_deg']<=6.2 for r in motion)
    spec=dict(version='M4.3 P2-B sparse-v1',experiment=EXP.name,original_indices=list(range(1,321)),
        rule='Union: odd original indices + final frame + both endpoints of any baseline pair in inclusive lower 5% fitness/correspondence or upper 5% RMSE tails + both endpoints of estimated ICP translation >0.35m.',
        quantiles='NumPy percentile linear interpolation over 319 official Turtle-rounded observations per pair factor',
        thresholds=thresholds,translation_bridge_m=.35,selected_indices=frames,
        selected_count=len(frames),retained_fraction=len(frames)/320,expected_selected_factors=8*len(frames)-6,
        maximum_original_index_step=max(np.diff(frames).tolist()),gt_used_for_selection=False,
        hypothesis='Dropping redundant short-baseline observations reduces worker time; protecting measured weak pairs limits connectivity losses, but skipping can increase drift or fail.',
        expected_result='Fewer preprocessing/registration steps and map samples; no guaranteed L2 improvement. One attempt only.',
        comparison=dict(reference='original first camera; GT only offline; no fitted alignment',
            error='Euclidean camera-center L2; full 320 baseline, full Selected, and same selected indices from saved baseline',
            primary_runtime='same guarded reconstruction worker boundary incl imports, observer, map export, evaluation, native image, official Turtle write; measuring/sealing vs selected query/write overhead disclosed',
            secondary_runtime='same reconstruct function call-to-return boundary, includes in-pipeline observer overhead; full map export outside function timer',
            exploratory_tradeoff_acceptance=dict(worker_runtime_less_than_baseline=True,
                same_frame_mean_l2_increase_at_most_m=.05,
                baseline_to_selected_full_map_fraction_within_0_20m_at_least=.85),
            coverage='Directed nearest-neighbor distances on full ceiling-cropped maps in fixed first-camera reference, threshold 0.20m; 0.20m occupancy and spatial quadrants; relative observed-map agreement, not absolute surface GT completeness',
            limitations='One route, one seed, no statistical significance; baseline pose drift affects map distances; no room labels or globally optimal ratio inferred'),
        official_contract=dict(cli='reconstruct.py --selection-query --override-experiment',
            turtle='Existing 2554 baseline factors remain unchanged; selected run adds usedFrame/count/mapMeanL2/splice metadata only. New 8N-6 observations saved outside TTL by read-only Observer.',
            pair_registration='Across gaps register previous selected frame to current selected frame; contiguous segments are metadata, not independently reconstructed'),
        forbidden='No Phase 1 Frame104 exclusion; no GT selection, no baseline rerun, no rule/seed/voxel retuning, no second capture/P2-C/Bonus/submission')
    SPEC.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
    values=' '.join(map(str,frames))
    QUERY.write_text('''# Frozen M4.3 sparse-v1; VALUES generated solely by the non-GT rule.\nPREFIX hw1: <http://taica.course/hw1/ontology#>\nPREFIX exp: <http://taica.course/hw1/experiment/>\nSELECT DISTINCT ?frameIndex WHERE {\n  exp:p2_114753116_a01_baseline_01 hw1:onBatch ?batch .\n  ?batch hw1:hasFrame ?frame .\n  ?frame hw1:frameIndex ?frameIndex .\n  VALUES ?frameIndex { '''+values+''' }\n} ORDER BY ASC(?frameIndex)\n''')
    csv_write(PREP/'selected_indices.csv',[dict(frame=i,reasons=';'.join(reasons[i])) for i in frames])
    import api
    actual=api.frames_from_sparql_query(api.read_experiment(str(TTL)),str(QUERY))
    if actual!=frames: raise RuntimeError('Official SPARQL selection mismatch')
    write(PREP/'verification.json',dict(baseline=validation,selected_count=len(frames),
        selected_factors=8*len(frames)-6,non_gt_high_overlap_small_motion_pairs=redundancy,
        total_pairs=319,selection_rule_sha256=sha(SPEC),sparql_sha256=sha(QUERY),
        gt_not_read_by_selection=True,formal_selected_started=False))
    # Complete local source binding; manifest excludes itself.
    write(PREP/'manifest.json',inventory([PREP]))
    print(json.dumps(read(PREP/'verification.json'),indent=2))


if __name__=='__main__': prepare()
