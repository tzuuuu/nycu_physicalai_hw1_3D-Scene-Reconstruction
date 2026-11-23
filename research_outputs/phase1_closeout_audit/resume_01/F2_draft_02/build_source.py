"""F2：僅讀凍結點雲取樣、位姿、CSV與PNG；不匯入或執行配準核心。"""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys

os.environ.setdefault('MPLCONFIGDIR','/tmp/phase1-report-assets-mpl')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageOps,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
SUITE=ROOT/'research_outputs/m32_20261118_suite_01'
RENDER_LIMIT=90000
FIELDS=['raw_point_count','point_yield','coarse_fitness','coarse_rmse','coarse_correspondences',
        'icp_fitness','icp_rmse','icp_correspondences']
LABELS=['Raw points (count)','Voxel points (count)','RANSAC fitness','RANSAC RMSE (m)',
        'RANSAC correspondences','ICP fitness','ICP RMSE (m)','ICP correspondences']


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def read_csv(path):
    with Path(path).open() as f:return [{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]

def uniform_points(points,limit=RENDER_LIMIT):
    points=np.asarray(points)
    if points.ndim!=2 or points.shape[1]!=3 or not np.isfinite(points).all():raise ValueError('Expected finite saved Nx3 cloud')
    return points[np.linspace(0,len(points)-1,min(limit,len(points)),dtype=int)] if len(points) else points

def shared_bounds(runs):
    # 所有實際保存地圖／估計／GT都參與顯示界線，不以GT擬合或裁掉錯誤區域。
    arrays=[a[:,[0,2]] for r in runs for a in [r['points'],r['pred'],r['gt']]]
    values=np.concatenate(arrays);lo=np.floor(values.min(axis=0))-1;hi=np.ceil(values.max(axis=0))+1
    return [float(lo[0]),float(hi[0]),float(lo[1]),float(hi[1])]


def load_runs():
    plan=read(SUITE/'suite.json');runs={}
    for item in plan['conditions']:
        c=item['condition']
        if c=='B1':continue
        out=Path(item['output']);exp=Path(item['experiment'])
        analysis=SUITE/'resume_03/C2_audit/analysis' if c=='C2' else out/'analysis'
        frames=read_csv(analysis/'frames.csv');summary=read(analysis/'summary.json')
        csv_path=analysis/'frames.csv';cloud=out/'observation/map_sample.npz'
        runs[c]=dict(key=c,label=f"{c}: v={item['voxel']:.2f} m, seed={item['seed']}",n=191,
            mean=summary['mean_l2_m'],voxel=item['voxel'],seed=item['seed'],runtime=summary['total_process_s'],
            points=np.load(cloud)['points'],pred=np.array([[r['pred_'+k+'_m'] for k in ['x','y','z']] for r in frames]),
            gt=np.array([[r['gt_'+k+'_m'] for k in ['x','y','z']] for r in frames]),frames=frames,
            pairs=read_csv(analysis/'pairs.csv'),events=[json.loads(l) for l in (out/'observation/events.jsonl').read_text().splitlines()],
            official=exp/(exp.name+'.ttl'),native=exp/'reconstruction_baseline.png',
            sources=[csv_path,cloud,analysis/'summary.json',analysis/'pairs.csv',out/'observation/events.jsonl'],
            caveat='C2 supplemental scientific audit passed; original finalize metadata stop preserved.' if c=='C2' else '')
    base=ROOT/'research_outputs/m31_20261118_analysis_01';obs=ROOT/'research_outputs/m31_20261118_official_observation_01'
    poses=np.load(base/'poses_offline.npz');s=read(base/'summary.json');fs=read_csv(base/'common_frame_errors.csv')
    exp=ROOT/'experiments/p1_baseline_20261118_map005_s0_01'
    runs['Selected']=dict(key='Selected',label='M3.1 Selected: exclude frame 104',n=190,mean=s['selected_common190_official_mean_l2_m'],
        voxel=.05,seed=0,runtime=s['execution']['total_process_s'],points=np.load(obs/'map_sample.npz')['points'],
        pred=poses['predicted'][:,:3,3],gt=poses['gt'][:,:3,3],
        frames=[dict(frame=r['frame'],l2_m=r['selected_l2_m']) for r in fs],pairs=read_csv(base/'selected_pair_metrics.csv'),
        events=[json.loads(l) for l in (obs/'events.jsonl').read_text().splitlines()],official=exp/(exp.name+'.ttl'),
        native=exp/'reconstruction_selected.png',sources=[base/'poses_offline.npz',base/'summary.json',base/'common_frame_errors.csv',obs/'map_sample.npz',obs/'events.jsonl',base/'selected_pair_metrics.csv'],
        caveat='Exploratory ablation informed by prior GT diagnosis; not a GT-independent selection rule.')
    return runs


def map_panel(ax,r,bounds,title=None):
    p=uniform_points(r['points'])
    ax.scatter(p[:,0],p[:,2],s=.32,c='#66727A',alpha=.65,rasterized=True,linewidths=0)
    ax.plot(r['pred'][:,0],r['pred'][:,2],color='red',lw=1.7,label='Estimated')
    ax.plot(r['gt'][:,0],r['gt'][:,2],color='black',lw=1.5,label='Ground truth')
    ax.set(xlim=bounds[:2],ylim=bounds[2:],xlabel='X (m)',ylabel='Z (m)',
        title=title or f"{r['label']}\nN={r['n']}, Mean L2={r['mean']:.6f} m")
    ax.set_aspect('equal',adjustable='box');ax.legend(loc='best',fontsize=11)


def build(output):
    output=Path(output).resolve()
    if not read(ROOT/'research_outputs/phase1_closeout_audit/resume_01/F1_acceptance.json')['F1_complete']:
        raise RuntimeError('F1 gate not accepted')
    output.mkdir(exist_ok=False)
    for name in ['single_runs','comparisons','diagnostics','captions','data','previews']: (output/name).mkdir()
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.titlesize':13,'axes.labelsize':12,'legend.fontsize':11})
    runs=load_runs();assets=[];limitations=[
        'Original M2 did not retain its same-run full cloud or poses. The original PNG is preserved; no exact new M2 top-down map can be made without new reconstruction.',
        'The harmonized Baseline/Selected map comparison uses the explicitly labeled B0 matched-control cloud; it is not the original M2 map.',
        'Saved clouds were already ceiling-cropped by the original pipeline, and were originally stride-sampled. New rendering uses the same 90,000-index cap on each saved sample; lost detail cannot be recovered.',
        'Isometric views are not required here; original native PNGs provide their original viewpoints. No synthetic scene or repaired reconstruction is used.']
    def register(rel,caption,sources,experiments,kind='offline redraw',view='not a scene view',bounds=None,limits=None):
        path=output/rel
        with Image.open(path) as im:size=list(im.size)
        sources=sorted(set(Path(p).resolve() for p in sources))
        rec=dict(path=str(path.relative_to(ROOT)),sha256=sha(path),size_px=size,caption=caption,
            experiments=experiments,kind=kind,view=view,coordinate_frame=('fixed first-camera display axes: image axes multiplied by diag(1,-1,-1); no fit' if view=='native legacy view' else 'original source/target camera axes; local diagnostic' if view=='source local projections' else 'fixed first-camera image axes: +X right, +Y down, +Z forward'),
            display_bounds_xz_m=bounds,sampling='90,000 equally spaced indices of each saved sample (or all if smaller)' if view=='top-down' else 'source-specific; see caption',
            source_files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in sources],limitations=limits or [])
        assets.append(rec)
    def save(fig,rel,caption,source_runs=(),extra=(),**kw):
        fig.savefig(output/rel,dpi=300);plt.close(fig)
        sources=[p for k in source_runs for p in runs[k]['sources']+[runs[k]['official']]]+list(extra)
        register(rel,caption,sources,list(source_runs),**kw)
    # 原生截圖逐bytes複製，不升採樣或換成別次run。
    native_m2=ROOT/'experiments/p1_baseline_20261118_map005_s0_01/reconstruction_baseline.png'
    m2_summary=ROOT/'research_outputs/m2_phase1_baseline_20261118_01/validation.json'
    shutil.copyfile(native_m2,output/'single_runs/M2_baseline_native.png')
    register('single_runs/M2_baseline_native.png',
        'Original M2 baseline reconstruction (191 frames; registration voxel 0.05 m, seed 0; map voxel 0.05 m; Mean L2 3.174055104788 m). The ceiling-cropped scene is shown with the estimated trajectory in red and ground truth in black, in the capture-first-camera reference. This is the original saved PNG; sparse legacy rendering and its native view limit visible scene detail.',
        [native_m2,m2_summary,runs['Selected']['official']],['M2 Baseline'],'native PNG copy','native legacy view',limits=[limitations[0],'Original helper displayed approximately 5,000 map points; no denser original M2 cloud is available.'])
    shutil.copyfile(runs['Selected']['native'],output/'single_runs/M31_selected_native.png')
    register('single_runs/M31_selected_native.png',
        'Original M3.1 Selected reconstruction (190 frames, excluding frame 104; Mean L2 4.200397987246 m). The saved ceiling-cropped scene and red estimated / black GT trajectories show the negative ablation outcome. Native camera limits differ from the M2 screenshot; this copy is not a harmonized metric map comparison.',
        [runs['Selected']['native'],runs['Selected']['official']]+runs['Selected']['sources'],['Selected'],'native PNG copy','native legacy view',limits=['Native automatic ranges are not common comparison bounds.'])
    for key in ['Selected','B0','B2','C1','C2','C3','C4']:
        r=runs[key];bounds=shared_bounds([r]);fig,ax=plt.subplots(figsize=(9,8),constrained_layout=True)
        map_panel(ax,r,bounds)
        caption=(f"{r['label']} reconstruction ({r['n']} frames; map voxel 0.05 m; Mean L2 {r['mean']:.12f} m). "
            'The saved ceiling-cropped scene is redrawn top-down with the estimated trajectory in red and ground truth in black, in the fixed first-camera frame, with no fitted alignment. '
            +('The retained route is displaced and extended after the new 103-to-105 mismatch. ' if key=='Selected' else
              'The late route is visibly displaced following the 103-to-104 rotation mismatch. ' if key in ['B0','C2','C4'] else
              'The estimated route is closer to GT than the flipped controls, but residual displacement remains. ')+r['caveat'])
        save(fig,'single_runs/'+key+'_topdown.png',caption,[key],view='top-down',bounds=bounds,limits=[limitations[2]])
    # A：原M2圖無重繪來源；matched-control圖明示B0來源，不冒充M2。
    bounds=shared_bounds([runs['B0'],runs['Selected']]);fig,axs=plt.subplots(1,2,figsize=(11,10),constrained_layout=True)
    map_panel(axs[0],runs['B0'],bounds,'B0 matched baseline control\n(not original M2 cloud)\n191 frames; Mean L2=3.174055 m')
    map_panel(axs[1],runs['Selected'],bounds)
    save(fig,'comparisons/A_baseline_reference_vs_selected_maps.png',
        'Harmonized top-down reference for the baseline/Selected comparison. Left: the separately measured B0 matched-control cloud (191 frames; Mean L2 3.174055104788 m), not the unavailable original M2 cloud. Right: actual M3.1 Selected cloud (190 frames; Mean L2 4.200397987246 m). Red is estimated trajectory and black is GT. Common first-camera bounds and identical display sampling retain the displaced geometry. The original M2 baseline scores 3.185555603874 m on the common 190 frames; Selected is 31.86% worse. No alignment or reconstruction correction is applied.',
        ['B0','Selected'],view='top-down',bounds=bounds,limits=limitations[:3])
    fig,ax=plt.subplots(figsize=(11,5.8),constrained_layout=True)
    common=read_csv(ROOT/'research_outputs/m31_20261118_analysis_01/common_frame_errors.csv')
    ax.plot([r['frame'] for r in common],[r['baseline_l2_m'] for r in common],label='Baseline matching diagnostic (common 190)',color='#36758F')
    ax.plot([r['frame'] for r in common],[r['selected_l2_m'] for r in common],label='Selected (190)',color='#D97732')
    ax.axvline(105,color='gray',ls='--',lw=1);ax.set(xlabel='Original frame index',ylabel='Camera-center L2 (m)',
        title='Baseline vs Selected: common 190 frames\nBaseline 3.185556 m; Selected 4.200398 m (+31.86%)');ax.legend();ax.grid(alpha=.2)
    save(fig,'comparisons/A_baseline_selected_errors.png',
        'Baseline/Selected camera-center errors on the common 190 frames. The original full-191 baseline Mean L2 is 3.174055104788 m; its matching M3.0 diagnostic scores 3.185555603874 m on the retained 190 frames. Selected scores 4.200397987246 m, 31.86% worse, with the new 103-to-105 mismatch. The diagnostic baseline trajectory is not an original same-run M2 pose export. Line colors identify runs, not trajectory roles.',
        ['Selected'],extra=[ROOT/'research_outputs/m3_20261118_analysis_02/frames.csv'])
    for group,keys,cols in [('B',['B0','B1','B2'],3),('C',['B0','C1','C2','C3','C4'],3)]:
        available=[runs[k] for k in keys if k!='B1'];bounds=shared_bounds(available)
        fig,axs=plt.subplots(math.ceil(len(keys)/cols),cols,figsize=(11,5.2*math.ceil(len(keys)/cols)),constrained_layout=True,squeeze=False)
        for ax,key in zip(axs.flat,keys):
            if key=='B1':
                ax.axis('off');ax.text(.5,.5,'B1: voxel=0.03 m, seed=0\nRANSAC failed at 70 -> 71\nNo complete 191-frame map\nNo full Mean L2',ha='center',va='center',transform=ax.transAxes,fontsize=13)
            else:map_panel(ax,runs[key],bounds)
        for ax in list(axs.flat)[len(keys):]:ax.axis('off')
        fig.suptitle('Registration Pipeline Scale' if group=='B' else 'RANSAC Seed Sensitivity: all five fixed seeds (B0 is seed 0)',fontsize=15)
        caption=('Registration Pipeline Scale, seed 0: B0 (v=0.05 m, 191 frames, Mean L2 3.174055104788 m), '
            'B1 (v=0.03 m, RANSAC failure at 70-to-71; no complete map or Mean L2), and B2 (v=0.08 m, 191 frames, Mean L2 0.274959466593 m). '
            if group=='B' else
            'RANSAC seed sensitivity at v=0.05 m, with 191 frames per run: seeds 0/1/2/3/4 have Mean L2 values 3.174055104788/0.155696709607/3.165352438552/0.221466815796/3.366709232590 m. Seeds 0, 2 and 4 have a major 103-to-104 rotation mismatch; seeds 1 and 3 do not. ')
        caption+='All actual saved ceiling-cropped scenes use common top-down X/Z limits, equal aspect, and identical display sampling. Estimated trajectories are red and GT black; no fitted alignment is used. Completed reconstructions can still have poor accuracy.'
        save(fig,'comparisons/'+group+'_maps.png',caption,[k for k in keys if k!='B1'],view='top-down',bounds=bounds,limits=[limitations[2]])
        fig,ax=plt.subplots(figsize=(10,5.5),constrained_layout=True)
        for i,key in enumerate(keys):
            if key=='B1':
                ax.text(i,.12,'Failed 70 -> 71\nNo full Mean L2',transform=ax.get_xaxis_transform(),ha='center',fontsize=11);continue
            value=runs[key]['mean'];ax.bar(i,value,color='#5C7894' if key in ['B0','C2','C4'] else '#2C9B85');ax.text(i,value+.06,f'{value:.6f}',ha='center')
        ax.set_xticks(range(len(keys)),[k+(' (seed 0)' if group=='C' and k=='B0' else '') for k in keys]);ax.set(ylabel='191-frame Mean L2 (m)',ylim=(0,3.95),title=group+' - all preregistered conditions')
        ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
        save(fig,'comparisons/'+group+'_mean_l2.png',caption+' Bars report full-sequence errors only; no zero is inserted for B1.',[k for k in keys if k!='B1'])
    # 凍結CSV與events直接作圖，不重新估計任何矩陣。
    fig,ax=plt.subplots(figsize=(12,6),constrained_layout=True)
    for key,r in runs.items():ax.plot([v['frame'] for v in r['frames']],[v['l2_m'] for v in r['frames']],label=key)
    ax.axvline(104,c='gray',ls='--',lw=1);ax.set(xlabel='Original frame index',ylabel='Camera-center L2 (m)',title='Per-frame errors: all complete M3.2 runs and M3.1 Selected');ax.legend(ncol=4);ax.grid(alpha=.2)
    save(fig,'diagnostics/per_frame_l2.png',
        'Per-frame L2 errors from six complete M3.2 runs (191 frames each) and the actual M3.1 Selected run (190 frames). The original frame identity is preserved. B1 has no full-sequence curve because it failed at 70-to-71. Colors identify runs; this is an error plot, not a map. High-error seeds are retained.',list(runs))
    fig,axs=plt.subplots(2,2,figsize=(11,8),constrained_layout=True)
    for key in ['B0','B2','C1','C2','C3','C4']:
        r=runs[key]
        for ax,field in zip(axs.flat,['coarse_rotation_error_deg','relative_rotation_error_deg','coarse_translation_error_m','relative_translation_error_m']):
            ax.plot([v['current'] for v in r['pairs']],[v[field] for v in r['pairs']],label=key)
    for ax,label in zip(axs.flat,['RANSAC rotation error (deg)','ICP rotation error (deg)','RANSAC translation error (m)','ICP translation error (m)']):
        ax.set(xlabel='Current frame index',ylabel=label,xlim=(1,191),xticks=[1,50,100,150,191]);ax.axvline(104,c='gray',ls='--',lw=1);ax.grid(alpha=.2)
    axs[0,0].legend(ncol=3)
    save(fig,'diagnostics/local_registration_errors.png',
        'RANSAC and ICP local rotation/translation errors for all six complete M3.2 runs, evaluated offline using their saved same-run matrices and fixed first-camera GT convention. B0/C2/C4 have major rotation mismatches at 103-to-104; B2/C1/C3 do not. B1 has no complete sequence. No registration is rerun and no matrix is replaced.',[k for k in runs if k!='Selected'])
    r=runs['B0'];fig,axs=plt.subplots(3,1,figsize=(11,9),constrained_layout=True)
    axs[0].plot([p['current'] for p in r['pairs']],[p['coarse_rotation_error_deg'] for p in r['pairs']],label='RANSAC')
    axs[0].plot([p['current'] for p in r['pairs']],[p['relative_rotation_error_deg'] for p in r['pairs']],label='ICP');axs[0].set_ylabel('Local rotation error (deg)');axs[0].legend()
    axs[1].plot([p['current'] for p in r['pairs']],[p['coarse_translation_error_m'] for p in r['pairs']],label='RANSAC')
    axs[1].plot([p['current'] for p in r['pairs']],[p['relative_translation_error_m'] for p in r['pairs']],label='ICP');axs[1].set_ylabel('Local translation error (m)');axs[1].legend()
    axs[2].plot([p['frame'] for p in r['frames']],[p['l2_m'] for p in r['frames']]);axs[2].set(ylabel='Global camera L2 (m)',xlabel='Current frame index')
    for ax in axs:ax.set_xlim(95,120);ax.axvline(104,c='gray',ls='--',lw=1);ax.grid(alpha=.2)
    fig.suptitle('103 -> 104 pose-flip diagnosis: saved B0 control evidence')
    save(fig,'diagnostics/pose_flip_103_104.png',
        'The saved B0 control (v=0.05 m, seed 0, 191 frames; full Mean L2 3.174055104788 m) shows a coarse rotation error of 176.074504 degrees at 103-to-104 and an ICP error of 179.778159 degrees. ICP reduces local residuals without recovering the correct pose; the wrong orientation then affects global motion accumulation. These are offline errors from frozen results, not a new registration experiment.', ['B0'])
    for group,keys in [('B',['B0','B1','B2']),('C',['B0','C1','C2','C3','C4'])]:
        fig,axs=plt.subplots(4,2,figsize=(10.5,12.5),constrained_layout=True)
        extra=[]
        for key in keys:
            if key=='B1':
                source=ROOT/'research_outputs/m32_p1_m32_20261118_b_v003_s0_01/observation/events.jsonl';extra.append(source)
                events=[json.loads(l) for l in source.read_text().splitlines()];label='B1 partial (unsealed)';style='--'
            else:events=runs[key]['events'];label=key;style='-'
            for ax,field in zip(axs.flat,FIELDS):
                rows=[r for r in events if field in r];ax.plot([r['stem'] for r in rows],[r[field] for r in rows],ls=style,label=label,alpha=.85,lw=1)
        for ax,label in zip(axs.flat,LABELS):ax.set(xlabel='Original current frame',ylabel=label,xlim=(1,191),xticks=[1,50,100,150,191]);ax.grid(alpha=.2)
        axs[0,0].legend(ncol=2);fig.suptitle(group+' - eight native pipeline factors; thresholds and point sets are run-specific')
        save(fig,'diagnostics/'+group+'_eight_factors.png',
            group+' pipeline-grounded factor timelines. Complete runs contain 191 single-frame and 190 pair measurements per factor type. '+
            ('B1 contributes only the actual unsealed prefix through its failed 70-to-71 pair (562 observed values total); it is not a complete factor set. ' if group=='B' else 'All five seeds are shown, including overlapping raw-count/yield curves and high-error seeds. ')+
            'Fitness and correspondence RMSE are internal metrics at native thresholds and do not establish GT pose accuracy. VoxelizedPointYield is a count, not a proportion.',[k for k in keys if k!='B1'],extra=extra)
    # 原有細部診斷保留來源與原解析度，不假稱重畫或新實驗。
    original=ROOT/'research_outputs/m3_20261118_details_01/pair103_104_cloud_projections.png'
    shutil.copyfile(original,output/'diagnostics/existing_pair_cloud_projections.png')
    register('diagnostics/existing_pair_cloud_projections.png',
        'Existing M3.0 diagnostic cloud projections for 103-to-104. Saved coarse/ICP transforms and the offline GT reference are applied for diagnosis; no new RANSAC/ICP is run and GT is not used to correct a reconstruction. This is a local projection diagnostic, not a full-floor map.',[original,ROOT/'research_outputs/m3_20261118_details_01/provenance.json'],['M3.0'],'existing diagnostic PNG copy','source local projections',limits=['Original image resolution retained.'])
    rows=[dict(run='M2 Baseline',frames=191,mean_l2_m=3.174055104788137,voxel_m=.05,seed=0,map_voxel_m=.05,runtime_s=286.378044),
          dict(run='M3.1 Selected',frames=190,mean_l2_m=runs['Selected']['mean'],voxel_m=.05,seed=0,map_voxel_m=.05,runtime_s=runs['Selected']['runtime'])]
    for key in ['B0','B1','B2','C1','C2','C3','C4']:
        if key=='B1':rows.append(dict(run=key,frames=70,mean_l2_m=None,voxel_m=.03,seed=0,map_voxel_m=.05,runtime_s=read(ROOT/'research_outputs/m32_p1_m32_20261118_b_v003_s0_01/command/execution.json')['total_process_s']));continue
        r=runs[key];rows.append(dict(run=key,frames=r['n'],mean_l2_m=r['mean'],voxel_m=r['voxel'],seed=r['seed'],map_voxel_m=.05,runtime_s=r['runtime']))
    with (output/'data/run_comparison.csv').open('x') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with (output/'captions/figure_captions.md').open('x') as f:
        f.write('# Phase 1 figure captions (asset drafts, not the final English report)\n\n')
        for rec in assets:f.write('## '+rec['path'].split('phase1_report_assets/')[-1]+'\n\n'+rec['caption']+'\n\n')
    with (output/'README.md').open('x') as f:
        f.write('# Phase 1報告素材\n\n本目錄只保存F2素材，不是正式ZIP或英文最終報告。所有圖片由既有正式PNG、已保存點雲／位姿／CSV離線產生；沒有讀取原始RGB-D重建、配準、GT擬合或修正錯圖。\n\n'
            '## 使用\n\n優先使用single_runs中的Selected／B2／C1／C3 Top-down與M2原生PNG；B0／C2／C4同樣保留，不隱藏負面條件。comparisons包含A／B／C圖，diagnostics保存各誤差與八因素。captions/figure_captions.md為英文Figure Caption素材。完整來源、尺寸、SHA與限制在manifest.json。\n\n'
            '## 已知限制\n\n'+'\n'.join('- '+s for s in limitations)+'\n\n'
            'B1沒有完整地圖或完整Mean L2，data/run_comparison.csv的70是已接受位姿前綴，不是完整重建或已評估190/191張。M2原生圖不放大捏造細節；A等尺度地圖參考明示使用B0控制組。所有新地圖只顯示保存且已裁天花板的取樣，不能量出全樓層正確涵蓋百分比。\n\n'
            '## 視覺驗收\n\n請參考visual_review.json；previews為檢視用聯絡表，不是新增科學結果。原生PNG沒有宣稱300 dpi重繪；其餘新Matplotlib圖以300 dpi輸出。\n')
    native_index=[]
    for key,r in runs.items():
        with Image.open(r['native']) as im:size=list(im.size)
        native_index.append(dict(run=key,path=str(r['native'].relative_to(ROOT)),sha256=sha(r['native']),size_px=size))
    native_index.insert(0,dict(run='M2 Baseline',path=str(native_m2.relative_to(ROOT)),sha256=sha(native_m2)))
    native_index.append(dict(run='B1',path=None,status='Failed Registration; no complete map'))
    with (output/'data/native_png_index.json').open('x') as f:json.dump(native_index,f,indent=2)
    # 每張都放入可讀聯絡表供目視檢視，保留各自原圖。
    previews=[]
    for start in range(0,len(assets),4):
        subset=assets[start:start+4];sheet=Image.new('RGB',(2400,2200),'white');draw=ImageDraw.Draw(sheet)
        for j,rec in enumerate(subset):
            image=Image.open(ROOT/rec['path']).convert('RGB');image.thumbnail((1160,1000))
            ox=20+(j%2)*1200;oy=20+(j//2)*1100
            draw.text((ox,oy),rec['path'].split('phase1_report_assets/')[-1],fill='black')
            sheet.paste(image,(ox+(1160-image.width)//2,oy+35+(1000-image.height)//2))
        path=output/'previews'/f'contact_{start//4+1:02}.png';sheet.save(path);previews.append(str(path.relative_to(ROOT)))
    manifest=dict(assets=assets,limitations=limitations,source_code_sha256=sha(Path(__file__)),
        rendering=dict(dpi=300,display_limit=RENDER_LIMIT,point_size=.32,point_alpha=.65,red='estimated',black='GT',
            fitted_alignment=False,registration_executed=False,original_RGBD_reconstructed=False),
        visual_review_file='visual_review.json',previews=previews,
        files={str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file()})
    with (output/'manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
    print(json.dumps(dict(asset_count=len(assets),previews=previews,limitations=limitations),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',default=str(ROOT/'research_outputs/phase1_report_assets'))
    args=p.parse_args();build(args.output)
