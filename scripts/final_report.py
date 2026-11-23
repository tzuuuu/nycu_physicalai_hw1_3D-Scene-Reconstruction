"""Final Chinese review: read saved scientific results; never reconstruct.

Run with the existing habitat Python, from any directory. All writes are confined
to reports/final_zh. Commands: snapshot, analyze, figures, finalize.
"""
import argparse
import ast
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/final_zh'
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MPLCONFIGDIR', '/tmp/hw1-final-mpl')
sys.path.insert(0, str(ROOT))
import numpy as np
from scipy.spatial.transform import Rotation

FIELDS = ['raw_point_count', 'point_yield', 'coarse_fitness', 'coarse_rmse',
          'coarse_correspondences', 'icp_fitness', 'icp_rmse', 'icp_correspondences']
NAMES = ['RawPointCount', 'VoxelizedPointYield', 'CoarseRANSACFitness',
         'CoarseRANSACRMSE', 'CoarseRANSACCorrespondences', 'ICPInlierFitness',
         'ICPInlierRMSE', 'ICPInlierCorrespondences']


def read(p):
    return json.loads(Path(p).read_text())


def lines(p):
    return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def write(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def table(p):
    with Path(p).open() as f:
        return list(csv.DictReader(f))


def csvwrite(p, rows):
    with Path(p).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def protected_paths():
    files = []
    for folder in ['eval', 'experiments', 'research_outputs', 'docs', 'configs', 'ontology', 'packages']:
        files += [p for p in (ROOT/folder).rglob('*') if p.is_file()
                  and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts]
    files += list(ROOT.glob('*.py')) + [ROOT/'README.md', ROOT/'pixi.toml', ROOT/'pixi.lock']
    files += [p for d in ['scripts', 'tests'] for p in (ROOT/d).glob('*.py')
              if p.name != 'final_report.py']
    return sorted(set(files))


def snapshot():
    p = OUT/'audit/protected_before.json'
    if p.exists():
        raise RuntimeError('Existing snapshot is never replaced')
    write(p, {str(f.relative_to(ROOT)): sha(f) for f in protected_paths()})
    print('Protected snapshot:', len(read(p)), 'files')


def truth(capture, frames):
    # Promote float32 BEFORE subtracting the first position.
    gt = np.load(capture/'GT_pose.npy', allow_pickle=False).astype(np.float64)
    r = Rotation.from_quat(gt[0, [4, 5, 6, 3]]).as_matrix()
    return ((gt[:, :3]-gt[0, :3]) @ r @ np.diag([1., -1., -1.]))[np.asarray(frames)-1]


def load_runs():
    p1 = ROOT/'eval/_data/first_floor'
    p2 = ROOT/'eval/_data/second_floor/114753116/P2_A_01'
    runs = {}
    p1rows = table(ROOT/'research_outputs/phase1_report_assets/data/run_comparison.csv')
    for row in p1rows:
        key = row['run']
        if key in ['M2 Baseline', 'B1']:
            continue
        if key == 'M3.1 Selected':
            key = 'A_selected'
            obs = ROOT/'research_outputs/m31_20261118_official_observation_01'
            experiment = 'p1_baseline_20261118_map005_s0_01'
            frames = [i for i in range(1, 192) if i != 104]
        else:
            spec = next(c for c in read(ROOT/'research_outputs/m32_20261118_suite_01/suite.json')['conditions'] if c['condition'] == key)
            obs = Path(spec['output'])/'observation'
            experiment = spec['name']
            frames = list(range(1, 192))
        runs[key] = dict(obs=obs, experiment=experiment, frames=frames, capture=p1,
                         mean=float(row['mean_l2_m']), seconds=float(row['runtime_s']),
                         voxel=float(row['voxel_m']), seed=int(row['seed']), backend='open3d',
                         label=key, map_status='Saved stride sample; full original cloud unavailable')
    diagnostic = ROOT/'research_outputs/m3_20261118_diagnostic_02'
    runs['M2'] = dict(obs=diagnostic, experiment='p1_baseline_20261118_map005_s0_01',
        frames=list(range(1, 192)), capture=p1, mean=float(p1rows[0]['mean_l2_m']),
        seconds=float(p1rows[0]['runtime_s']), voxel=.05, seed=0, backend='open3d', label='M2',
        map_status='No original M2 cloud; verified matching M3.0 diagnostic poses only')
    p2rows = read(ROOT/'research_outputs/m43_p2b_closeout_01/analysis/comparison.json')['runs']
    for key, directory, row in zip(['P2A', 'P2B'], ['m42_p2_a01_baseline_01', 'm43_p2b_selected_01'], p2rows):
        frames = list(range(1, 321)) if key == 'P2A' else read(ROOT/'docs/implementation/m43/selection_rule.json')['selected_indices']
        runs[key] = dict(obs=ROOT/'research_outputs'/directory/'observation',
            experiment='p2_114753116_a01_baseline_01', frames=frames, capture=p2,
            mean=row['mean_l2_m'], seconds=row['worker_runtime_s'], voxel=.05, seed=0,
            backend='open3d', label=key, map_status='Complete same-run returned map')
    for row in table(ROOT/'research_outputs/m5_bonus_01/analysis/comparison.csv'):
        key = 'custom_'+row['condition']
        hist = runs[{'f1_baseline': 'M2', 'f1_c1': 'C1', 'f2_baseline': 'P2A', 'f2_sparse': 'P2B'}[row['condition']]]
        experiment = {'f1_baseline':'bonus_f1_baseline_01', 'f1_c1':'bonus_f1_c1_01',
                      'f2_baseline':'bonus_f2_baseline_01', 'f2_sparse':'bonus_f2_baseline_01'}[row['condition']]
        runs[key] = dict(obs=ROOT/'research_outputs/m5_bonus_01'/row['condition']/'observation',
            experiment=experiment, frames=hist['frames'], capture=hist['capture'],
            mean=float(row['custom_mean_l2_m']), seconds=float(row['custom_worker_s']),
            voxel=.05, seed=int(row['seed']), backend='my_icp', label=key,
            map_status='Complete same-run returned map')
    for key, r in runs.items():
        r['pred'] = np.load(r['obs']/'positions.npy', allow_pickle=False)
        r['gt'] = truth(r['capture'], r['frames'])
        r['errors'] = np.linalg.norm(r['pred']-r['gt'], axis=1)
        r['events'] = lines(r['obs']/'events.jsonl')
        r['pairs'] = lines(r['obs']/'transforms.jsonl')
    return runs


def analyze():
    import api
    from rdflib import Graph
    from rdflib.compare import isomorphic
    runs = load_runs()
    checks, totals, perframes, stats = [], [], [], []
    for key, r in runs.items():
        n = len(r['frames'])
        np.testing.assert_allclose(r['errors'].mean(), r['mean'], atol=1e-12, rtol=0)
        assert r['pred'].shape == (n, 3)
        assert len(r['pairs']) == n-1
        assert [(p['prev_stem'], p['stem']) for p in r['pairs']] == list(zip(r['frames'], r['frames'][1:]))
        pose = np.eye(4)
        centers = [pose[:3, 3].copy()]
        for p in r['pairs']:
            pose = pose @ np.asarray(p['icp_transformation'])
            centers.append(pose[:3, 3].copy())
        np.testing.assert_allclose(centers, r['pred'], atol=1e-12, rtol=0)
        count = sum(sum(field in e for field in FIELDS) for e in r['events'])
        assert count == 8*n-6
        for field, name in zip(FIELDS, NAMES):
            v = np.array([e[field] for e in r['events'] if field in e], dtype=float)
            assert np.isfinite(v).all() and len(v) == (n if field in FIELDS[:2] else n-1)
            stats.append(dict(run=key, factor=name, count=len(v), minimum=v.min(), p05=np.percentile(v,5),
                              median=np.median(v), mean=v.mean(), p95=np.percentile(v,95), maximum=v.max()))
        expdir = ROOT/'experiments'/r['experiment']
        exp = api.read_experiment(str(expdir/(r['experiment']+'.ttl')))
        assert exp['complete'] and sum(exp['factor_counts'].values()) == 8*len(exp['frame_indices'])-6
        mode = 'selected' if key in ['A_selected', 'P2B', 'custom_f2_sparse'] else 'baseline'
        runnode = api.data_run_iri(exp['exp_name'], mode)
        assert int(exp['graph'].value(runnode, api.HW1.runFrameCount)) == n
        assert float(exp['graph'].value(runnode, api.HW1.mapMeanL2)) == api._storable(r['mean'])
        if mode == 'selected':
            assert len(list(exp['graph'].objects(runnode, api.HW1.usedFrame))) == n
        else:
            # Independently compare all baseline factors to same-run observations
            # at the official Turtle precision; M2 uses the matching diagnostic.
            lookup = {}
            for e in r['events']:
                for field, factor in zip(FIELDS, NAMES):
                    if field in e:
                        lookup[(factor, e.get('prev_stem'), e['stem'])] = e[field]
            for node in exp['graph'].subjects(api.HW1.inExperiment, exp['exp_iri']):
                g = exp['graph']; factor = str(g.value(node, api.HW1.hasDefinition)).split('#')[-1]
                cur = g.value(node, api.HW1.hasCurrentFrame); prev = g.value(node, api.HW1.hasPrevious)
                # Image -> frame -> numeric stem, without interpreting IRI syntax.
                cf = next(g.subjects(api.HW1.hasDepthImage, cur))
                current = int(g.value(cf, api.HW1.frameIndex))
                previous = None if prev is None else int(g.value(next(g.subjects(api.HW1.hasDepthImage, prev)), api.HW1.frameIndex))
                assert float(g.value(node, api.HW1.value)) == api._storable(float(lookup[(factor,previous,current)]))
        sourcefiles = [r['obs']/'positions.npy', r['obs']/'transforms.jsonl', r['obs']/'events.jsonl', r['capture']/'GT_pose.npy']
        mp = r['obs']/'map_points.npy'
        if mp.exists():
            meta = read(r['obs']/'map_summary.json')
            for name, spec in meta['arrays'].items():
                f = r['obs']/(name+'.npy'); a = np.load(f, mmap_mode='r', allow_pickle=False)
                assert sha(f) == spec['sha256'] and list(a.shape) == spec['shape']
                for start in range(0, len(a), 65536):
                    assert np.isfinite(a[start:start+65536]).all()
                sourcefiles.append(f)
        checks.append(dict(run=key, evaluated_frames=n, observed_factors=count, mean_l2_recomputed_m=float(r['errors'].mean()),
            transform_chain_valid=True, seal_valid=True, baseline_factors_match=True if mode=='baseline' else 'baseline preserved; new selected factors external',
            sources={str(p.relative_to(ROOT)):sha(p) for p in sourcefiles}))
        totals.append(dict(run=key, floor=1 if r['capture'].name=='first_floor' else 2, backend=r['backend'],
            status='complete', input_frames=n, evaluated_frames=n, retained_fraction=n/(191 if r['capture'].name=='first_floor' else 320),
            mean_l2_m=r['mean'], runtime_s=r['seconds'], registration_voxel_m=r['voxel'], map_voxel_m=.05,
            seed=r['seed'], observed_factors=count, map_source_status=r['map_status'],
            observation_directory=str(r['obs'].relative_to(ROOT))))
        for frame,e in zip(r['frames'], r['errors']):
            perframes.append(dict(run=key, original_frame=frame, l2_m=e))
    b1 = read(ROOT/'research_outputs/m32_20261118_resume_failure_audit_01/failed_pair_result.json')
    assert b1['coarse_correspondences']==0 and b1['prev_stem']==70 and b1['stem']==71
    totals.append(dict(run='B1', floor=1, backend='open3d', status='failed RANSAC 70->71', input_frames=191,
        evaluated_frames='', retained_fraction=1., mean_l2_m='', runtime_s=290.755402875, registration_voxel_m=.03,
        map_voxel_m=.05, seed=0, observed_factors=562, map_source_status='No complete map; accepted prefix 70 frames',
        observation_directory='research_outputs/m32_p1_m32_20261118_b_v003_s0_01/observation'))
    failures = []
    bttl = ROOT/'experiments/p1_m32_20261118_b_v003_s0_01/p1_m32_20261118_b_v003_s0_01.ttl'
    assert not api.is_assessed(str(bttl))
    bonus = []
    for custom, old in [('custom_f1_baseline','M2'),('custom_f1_c1','C1'),('custom_f2_baseline','P2A'),('custom_f2_sparse','P2B')]:
        r,h=runs[custom],runs[old]
        a=np.array([p['trans_init'] for p in r['pairs']]);b=np.array([p['trans_init'] for p in h['pairs']])
        np.testing.assert_array_equal(a,b)
        timings=lines(r['obs']/'icp_timing.jsonl')
        bonus.append(dict(run=custom, identical_ransac_pairs=len(a), max_abs_ransac_delta=float(np.abs(a-b).max()),
            converged=sum(t['reason']=='converged' for t in timings), max_iterations=sum(t['reason']=='max_iterations' for t in timings)))
    # Recompute both common-frame comparisons, not averages over different sets.
    commonA=np.array(runs['A_selected']['frames'])-1
    commonB=np.array(runs['P2B']['frames'])-1
    same=dict(phase1_baseline_common190_m=float(runs['M2']['errors'][commonA].mean()),
        phase1_selected_common190_m=runs['A_selected']['mean'],
        phase2_baseline_common204_m=float(runs['P2A']['errors'][commonB].mean()),
        phase2_selected_common204_m=runs['P2B']['mean'],
        custom_phase2_baseline_common204_m=float(runs['custom_f2_baseline']['errors'][commonB].mean()),
        custom_phase2_selected_common204_m=runs['custom_f2_sparse']['mean'])
    vals=np.array([runs[k]['mean'] for k in ['B0','C1','C2','C3','C4']])
    seeds=dict(n=5, mean=float(vals.mean()), sample_std=float(vals.std(ddof=1)),median=float(np.median(vals)),minimum=float(vals.min()),maximum=float(vals.max()))
    # Verify original Open3D function byte-for-byte against accepted text.
    source=(ROOT/'utils.py').read_text();tree=ast.parse(source)
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='local_icp_algorithm')
    original=(ROOT/'research_outputs/m5_bonus_01/original_local_icp_algorithm.txt').read_text()
    assert ast.get_source_segment(source,node)==original.rstrip('\n')
    # Preserve declaration and baseline RDF while excluding only Selected node.
    final=api.read_experiment(str(ROOT/'experiments/bonus_f2_baseline_01/bonus_f2_baseline_01.ttl'))
    oldtext=(ROOT/'research_outputs/m5_bonus_01/f2_baseline/experiment.after.ttl').read_text()
    assert api._split_sections(oldtext)[0]==api._split_sections((ROOT/'experiments/bonus_f2_baseline_01/bonus_f2_baseline_01.ttl').read_text())[0]
    selected=api.data_run_iri(final['exp_name'],'selected'); reduced=Graph()
    for s,p,o in final['graph']:
        if s!=selected and (s,p,o)!=(final['exp_iri'],api.HW1.hasRun,selected):reduced.add((s,p,o))
    assert isomorphic(Graph().parse(data=oldtext,format='turtle'),reduced)
    # Historical accepted arrays and scientific sources, without mutating old validators.
    historic=read(ROOT/'research_outputs/m5_bonus_01/protected.before.json')
    diffs=[dict(path=p, expected=h, actual=sha(ROOT/p) if (ROOT/p).is_file() else None)
           for p,h in historic.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    csvwrite(OUT/'data/all_runs.csv',totals);csvwrite(OUT/'data/per_frame_l2.csv',perframes)
    csvwrite(OUT/'data/eight_factor_statistics.csv',stats)
    write(OUT/'audit/result_validation.json',dict(runs=checks,bonus=bonus,same_frame=same,seed_statistics=seeds,
        historical_protected_count=len(historic),historical_differences=diffs,original_open3d_unchanged=True,
        bonus_selected_preserves_baseline=True,b1_complete_score_absent=True,registration_executed=False))
    print('Validated',len(runs),'complete observations; B1 remains incomplete. Historical differences:',diffs)


def figures():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from PIL import Image, ImageOps, ImageDraw
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':13,
        'axes.labelsize':11,'legend.fontsize':10,'figure.titlesize':15,'savefig.dpi':240,
        'axes.spines.top':False,'axes.spines.right':False,'axes.grid':False})
    runs=load_runs(); manifest=[]
    blue,orange,green='#3269A8','#CB742C','#32816B'
    def save(fig,name,sources,caption,details=None):
        path=OUT/'figures'/name
        fig.savefig(path,dpi=240,facecolor='white',bbox_inches='tight',pad_inches=.18)
        plt.close(fig)
        with Image.open(path) as im: size=list(im.size)
        manifest.append(dict(file='figures/'+name,sha256=sha(path),pixels=size,caption_zh=caption,
            sources={str(Path(s).relative_to(ROOT)):sha(s) for s in sorted(set(sources))},
            rendering=details or {'tool':'Python Matplotlib','font':'DejaVu Sans','dpi':240}))
    def source(r):
        return [r['obs']/'positions.npy',r['obs']/'transforms.jsonl',r['capture']/'GT_pose.npy']
    def cloud(r):
        obs=r['obs']
        if (obs/'map_points.npy').exists():
            p=np.load(obs/'map_points.npy',mmap_mode='r');c=np.load(obs/'map_colors.npy',mmap_mode='r')
            return p,c,[obs/'map_points.npy',obs/'map_colors.npy']
        with np.load(obs/'map_sample.npz') as z:
            return z['points'],z['colors'],[obs/'map_sample.npz']
    # Reference-style top views: full RGB, white background, no synthesized
    # surfaces. Z-buffer only determines visible saved point at each pixel.
    def raster(p,c,bounds,width=1800):
        xmin,xmax,zmin,zmax=bounds
        height=max(1,int(width*(zmax-zmin)/(xmax-xmin)))
        px=np.clip(((p[:,0]-xmin)/(xmax-xmin)*(width-1)).astype(int),0,width-1)
        py=np.clip(((zmax-p[:,2])/(zmax-zmin)*(height-1)).astype(int),0,height-1)
        flat=np.full(width*height,len(p),dtype=np.int64)
        # Painter order: +Y points down; smallest Y is nearest top camera.
        order=np.argsort(p[:,1],kind='stable')
        rank=np.arange(len(p),dtype=np.int64)
        # A fixed metric point footprint (one 0.05m voxel), bounded for
        # readability. No interpolation, inpainting, texture or RGB edits.
        radius=max(1,min(3,round(.025*width/(xmax-xmin))))
        for dy in range(-radius,radius+1):
            for dx in range(-radius,radius+1):
                if dx*dx+dy*dy>radius*radius: continue
                xx=np.clip(px[order]+dx,0,width-1); yy=np.clip(py[order]+dy,0,height-1)
                np.minimum.at(flat,yy*width+xx,rank)
        image=np.full((width*height,3),255,dtype=np.uint8)
        ok=flat<len(p);image[ok]=np.clip(c[order[flat[ok]]]*255,0,255).astype(np.uint8)
        return image.reshape(height,width,3),radius
    # Shared bounds within all Phase 1, Phase 2 and same-floor Bonus groups.
    groups=[['B0','B2','C1','C2','C3','C4','A_selected'],['P2A','P2B'],
            ['custom_f1_baseline','custom_f1_c1'],['custom_f2_baseline','custom_f2_sparse']]
    bounds={}; allcloud={}
    for group in groups:
        lo=np.array([np.inf,np.inf]);hi=-lo
        for k in group:
            p,c,paths=cloud(runs[k]); allcloud[k]=(p,c,paths)
            for a in [p,runs[k]['pred'],runs[k]['gt']]:
                lo=np.minimum(lo,a[:,[0,2]].min(axis=0));hi=np.maximum(hi,a[:,[0,2]].max(axis=0))
        pad=np.maximum((hi-lo)*.04,.25);lo-=pad;hi+=pad
        for k in group: bounds[k]=[float(lo[0]),float(hi[0]),float(lo[1]),float(hi[1])]
    for k,(p,c,paths) in allcloud.items():
        r=runs[k];b=bounds[k]
        details=dict(tool='Python NumPy RGB point z-buffer + Matplotlib',font='DejaVu Sans',dpi=240,
            saved_point_count=len(p),use_all_saved_points=True,
            camera='orthographic top-down; X right, Z up; height=-Y',bounds_xmin_xmax_zmin_zmax=b,
            map_source_status=r['map_status'],gt_fit=False,ceiling='already removed by original reconstruction',
            colors='original RGB; no recoloring or completion')
        for reference in [False,True]:
            local=b
            if reference:
                arrays=np.concatenate([p,r['pred'],r['gt']])[:,[0,2]]
                lo=arrays.min(axis=0);hi=arrays.max(axis=0);pad=np.maximum((hi-lo)*.025,.2)
                local=[lo[0]-pad[0],hi[0]+pad[0],lo[1]-pad[1],hi[1]+pad[1]]
            img,radius=raster(p,c,local)
            display_bounds=[-local[3],-local[2],local[0],local[1]] if reference else local
            fig,ax=plt.subplots(figsize=(10,7) if reference else (9,8))
            ax.imshow(np.rot90(img) if reference else img,extent=display_bounds,origin='upper',interpolation='nearest')
            for path,color,label,z in [(r['gt'],'black','GT',5),(r['pred'],'#E02424','Estimated',6)]:
                ax.plot(-path[:,2] if reference else path[:,0],path[:,0] if reference else path[:,2],color=color,lw=1.0,label=label,zorder=z)
            ax.set(xlim=display_bounds[:2],ylim=display_bounds[2:]);ax.set_aspect('equal')
            if reference:ax.axis('off')
            else:ax.set(xlabel='First-camera X (m)',ylabel='First-camera Z (m)')
            label={'A_selected':'Phase 1: exclude frame 104','P2A':'Phase 2: FullBatch','P2B':'Phase 2: sparse-v1'}.get(k,k)
            fig.suptitle(label+' | '+('Custom Point-to-Point' if r['backend']=='my_icp' else 'Open3D Point-to-Plane'))
            fig.text(.5,.025,f"N={len(r['frames'])} | Mean L2={r['mean']:.6f} m | v={r['voxel']:.2f} m | seed={r['seed']}",ha='center',fontsize=10)
            handles=[Line2D([0],[0],color='black',lw=1.3,label='GT'),Line2D([0],[0],color='#E02424',lw=1.3,label='Estimated')]
            fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.05),ncol=2,frameon=False)
            fig.subplots_adjust(bottom=.14,top=.91)
            name=k+('_reference.png' if reference else '_map.png')
            view=dict(details,bounds_xmin_xmax_zmin_zmax=[float(x) for x in local],point_footprint_radius_pixels=radius,
                camera='orthographic top-down; screen horizontal=-Z, vertical=X; fixed 90 degree display rotation' if reference else details['camera'],
                comparison_limits='individual complete extent' if reference else 'shared group bounds')
            save(fig,name,paths+source(r),f'{label} 全彩重建，黑線 GT、紅線估計；'+r['map_status'],view)
        print('Rendered RGB map:',k,flush=True)
    # All data and statistical plots share labels, font, units and palette.
    per=OUT/'data/per_frame_l2.csv'; val=OUT/'audit/result_validation.json'
    fig,axes=plt.subplots(2,1,figsize=(11,7))
    for k,color,label in [('M2',blue,'M2: matching diagnostic'),('A_selected',orange,'Exclude 104')]:
        r=runs[k];axes[0].plot(r['frames'],r['errors'],label=label,color=color,lw=1.4)
    axes[0].set(ylabel='Camera-centre L2 (m)',title='Phase 1: baseline and single-frame ablation')
    for k,color in [('B0',blue),('B2',green),('C1',orange),('C2','#8D67AC'),('C3','#6594BA'),('C4','#8C6655')]:
        r=runs[k];axes[1].plot(r['frames'],r['errors'],label=k,color=color,lw=1.2)
    axes[1].set(ylabel='Camera-centre L2 (m)',xlabel='Original frame index',title='Phase 1: scale and seed conditions')
    for ax in axes:ax.axvline(104,color='#666666',ls='--',lw=.8);ax.grid(alpha=.18);ax.legend(ncol=3)
    fig.tight_layout();save(fig,'phase1_errors.png',[per,val], '一樓逐張 L2；虛線標示第104張，M2使用相符診斷位姿。')
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    labels=['B0 .05','B1 .03','B2 .08']; vals=[runs['B0']['mean'],np.nan,runs['B2']['mean']]
    axes[0].bar([0,2],[vals[0],vals[2]],color=[blue,green]);axes[0].set_xticks(range(3),labels)
    axes[0].text(1,.25,'Failed\n70 -> 71',ha='center',color='#AC3434');axes[0].set(ylabel='Mean L2 (m)',title='Registration scale v (m)')
    ks=['B0','C1','C2','C3','C4'];axes[1].bar(range(5),[runs[k]['mean'] for k in ks],color=[blue,orange,'#8D67AC',green,'#8C6655'])
    axes[1].set_xticks(range(5),[f'seed {i}' for i in range(5)]);axes[1].set(title='Five seeds; seed 0 = B0',ylabel='Mean L2 (m)')
    for ax in axes:ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
    fig.tight_layout();save(fig,'phase1_scale_seed.png',[OUT/'data/all_runs.csv',val], '尺度與五seed完整結果；B1無完整誤差，B0只計入seed0一次。')
    fig,axes=plt.subplots(2,1,figsize=(11,7))
    for k,color in [('P2A',blue),('P2B',orange)]:
        r=runs[k];axes[0].plot(r['frames'],r['errors'],label=k,color=color,lw=1.4)
    s=np.array(runs['P2B']['frames'])-1
    axes[1].plot(s+1,runs['P2A']['errors'][s],label='P2-A evaluated on S',color=blue)
    axes[1].plot(s+1,runs['P2B']['errors'],label='P2-B only S',color=orange)
    for ax,title in zip(axes,['All evaluated frames','Common 204 indices; different input information']):
        ax.set(title=title,xlabel='Original frame index',ylabel='Camera-centre L2 (m)');ax.grid(alpha=.18);ax.legend()
    fig.tight_layout();save(fig,'phase2_errors.png',[per,val], '二樓完整及共同204索引L2；共同評估索引不等於相同輸入資訊。')
    for tag,keys in [('phase1',['M2','A_selected']),('phase2',['P2A','P2B']),('phase1_sensitivity',['B0','B2','C1','C2','C3','C4'])]:
        fig,axes=plt.subplots(4,2,figsize=(12,11))
        for ax,field,name in zip(axes.flat,FIELDS,NAMES):
            for k,color in zip(keys,[blue,orange,green,'#8D67AC','#6594BA','#8C6655']):
                e=[e for e in runs[k]['events'] if field in e]
                ax.plot([x['stem'] for x in e],[x[field] for x in e],label=k,color=color,lw=.9)
            ax.set(title=name,xlabel='Original current-frame index',ylabel='m' if 'rmse' in field else ('fraction' if 'fitness' in field else 'count'))
            ax.grid(alpha=.16)
        axes.flat[0].legend();fig.tight_layout()
        save(fig,tag+'_eight_factors.png',[runs[k]['obs']/'events.jsonl' for k in keys], '八項原始因素時序；Selected使用新配對的同次Observer量測。')
    fig,axes=plt.subplots(4,2,figsize=(12,11))
    for ax,field,name in zip(axes.flat,FIELDS,NAMES):
        bins=np.histogram_bin_edges([e[field] for k in ['P2A','P2B'] for e in runs[k]['events'] if field in e],bins=24)
        for k,color in [('P2A',blue),('P2B',orange)]:
            ax.hist([e[field] for e in runs[k]['events'] if field in e],bins=bins,density=True,histtype='step',color=color,label=k,lw=1.5)
        ax.set(title=name,xlabel='m' if 'rmse' in field else ('fraction' if 'fitness' in field else 'count'),ylabel='Density')
    axes.flat[0].legend();fig.tight_layout();save(fig,'phase2_factor_distributions.png',[runs[k]['obs']/'events.jsonl' for k in ['P2A','P2B']], '二樓八因素分布；配對母體及抽樣組成不同。')
    corr=ROOT/'research_outputs/m3_20261118_analysis_02/correlations.csv';rows=table(corr)
    targets=['l2_m','l2_change_m','relative_translation_error_m','relative_rotation_error_deg']
    matrix=np.array([[float(next(r['spearman_rho'] for r in rows if r['factor']==f and r['target']==t)) for t in targets] for f in FIELDS])
    fig,ax=plt.subplots(figsize=(10,6));im=ax.imshow(matrix,cmap='RdBu_r',vmin=-1,vmax=1,aspect='auto')
    ax.set_yticks(range(8),NAMES);ax.set_xticks(range(4),['Global L2','L2 change','Pair translation error','Pair rotation error'],rotation=15,ha='right')
    for i in range(8):
        for j in range(4):ax.text(j,i,f'{matrix[i,j]:.2f}',ha='center',va='center',fontsize=10)
    ax.set_title('Phase 1: descriptive Spearman correlations (190 pairs)');fig.colorbar(im,ax=ax,label='Spearman rho');fig.tight_layout()
    save(fig,'factor_correlations.png',[corr], '一樓八因素與誤差的描述性Spearman相關；序列有相依性，未做顯著性或因果推論。')
    fig,axes=plt.subplots(2,2,figsize=(12,7))
    for ax,(custom,old) in zip(axes.flat,[('custom_f1_baseline','M2'),('custom_f1_c1','C1'),('custom_f2_baseline','P2A'),('custom_f2_sparse','P2B')]):
        for k,color,label in [(old,blue,'Historical Point-to-Plane'),(custom,orange,'Custom Point-to-Point')]:
            r=runs[k];ax.plot(r['frames'],r['errors'],label=label,color=color,lw=1.2)
        ax.set(title=custom.replace('custom_',''),xlabel='Original frame index',ylabel='Camera-centre L2 (m)');ax.grid(alpha=.18)
    axes.flat[0].legend(fontsize=9);fig.tight_layout();save(fig,'bonus_errors.png',[per], 'Bonus四條件逐張誤差；原M2歷史軌跡來自相符診斷。')
    comparison=ROOT/'research_outputs/m5_bonus_01/analysis/comparison.csv';rows=table(comparison)
    fig,axes=plt.subplots(1,2,figsize=(12,4));x=np.arange(4)
    for ax,a,b,title,ylabel in [(axes[0],'open3d_mean_l2_m','custom_mean_l2_m','Trajectory error','Mean L2 (m)'),(axes[1],'historical_worker_s','custom_worker_s','Recorded process time; boundaries differ','Time (s)')]:
        ax.bar(x-.18,[float(r[a]) for r in rows],.36,color=blue,label='Historical Point-to-Plane');ax.bar(x+.18,[float(r[b]) for r in rows],.36,color=orange,label='Custom Point-to-Point')
        ax.set_xticks(x,['F1 base','F1 C1','F2 base','F2 sparse']);ax.set(title=title,ylabel=ylabel);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
    axes[0].legend(fontsize=8);fig.tight_layout();save(fig,'bonus_metrics.png',[comparison], 'Bonus誤差與歷史程序時間；非純ICP速度比較。')
    fig,axes=plt.subplots(2,2,figsize=(12,7))
    keys=['custom_f1_baseline','custom_f1_c1','custom_f2_baseline','custom_f2_sparse']
    for ax,k in zip(axes.flat,keys):
        ts=lines(runs[k]['obs']/'icp_timing.jsonl');ax.plot([t['current'] for t in ts],[t['iterations'] for t in ts],color=green,lw=1)
        ax.axhline(60,color='#AC3434',ls='--',lw=1);ax.set(title=k.replace('custom_',''),xlabel='Original current-frame index',ylabel='Custom ICP updates',ylim=(0,64));ax.grid(alpha=.18)
    fig.tight_layout();save(fig,'bonus_iterations.png',[runs[k]['obs']/'icp_timing.jsonl' for k in keys], '自製ICP更新數；899對距離變化停止、3對達60次上限。')
    # Exact all-point precomputed coverage distances: no reconstruction or KD-tree rerun.
    distance=ROOT/'research_outputs/m43_p2b_closeout_01/analysis/baseline_to_selected_distances.npy'
    d=np.load(distance,mmap_mode='r');ds=np.sort(d)
    fig,ax=plt.subplots(figsize=(9,4));ix=np.unique(np.linspace(0,len(ds)-1,3000,dtype=int))
    ax.plot(ds[ix],(ix+1)/len(ds),color=blue,lw=1.5);ax.axvline(.2,color=orange,ls='--',label='0.20 m threshold')
    ax.set(xlabel='Baseline to Selected nearest-point distance (m)',ylabel='Cumulative fraction',title='Relative observed-map agreement; not surface completeness',ylim=(0,1.02));ax.legend();ax.grid(alpha=.18)
    fig.tight_layout();save(fig,'phase2_relative_map_cdf.png',[distance,ROOT/'research_outputs/m43_p2b_closeout_01/analysis/scene_coverage.json'], '完整基準地圖至Selected的最近點距離累積分布；非樓層絕對完整率。')
    fig,ax=plt.subplots(figsize=(9,6));r=runs['P2A'];gt=r['gt']
    ax.plot(-gt[:,2],gt[:,0],color='black',lw=1.1,label='GT capture route')
    for i in [0,79,159,239,319]:
        ax.scatter(-gt[i,2],gt[i,0],s=22,color=blue,zorder=5)
        ax.annotate(str(i+1),(-gt[i,2],gt[i,0]),xytext=(5,6),textcoords='offset points',fontsize=10)
    ax.set_aspect('equal');ax.set(xlabel='First-camera -Z (m)',ylabel='First-camera X (m)',title='Phase 2 capture route | frame order markers | GT for description only')
    ax.grid(alpha=.18);ax.legend();fig.tight_layout()
    save(fig,'phase2_capture_route.png',[r['capture']/'GT_pose.npy'], '二樓採集路線，標記原始影格1、80、160、240、320；只作路線描述，不作配準輸入。')
    fig,axes=plt.subplots(2,1,figsize=(11,6))
    for k,color in [('M2',blue),('A_selected',orange),('B2',green),('C1','#8D67AC')]:
        r=runs[k];gt=np.load(r['capture']/'GT_pose.npy').astype(float)
        rots=Rotation.from_quat(gt[:,[4,5,6,3]]).as_matrix();A=np.diag([1.,-1.,-1.])
        rot_err=[];tr_err=[]
        for p in r['pairs']:
            i,j=p['prev_stem']-1,p['stem']-1
            gR=A@rots[i].T@rots[j]@A;gtT=A@rots[i].T@(gt[j,:3]-gt[i,:3]);T=np.asarray(p['icp_transformation'])
            rot_err.append(np.degrees(Rotation.from_matrix(gR.T@T[:3,:3]).magnitude()));tr_err.append(np.linalg.norm(T[:3,3]-gtT))
        x=[p['stem'] for p in r['pairs']]
        axes[0].plot(x,rot_err,label=k,color=color,lw=1);axes[1].plot(x,tr_err,label=k,color=color,lw=1)
    axes[0].set(ylabel='Pair rotation error (deg)',title='Local ICP transform errors against GT; offline diagnosis')
    axes[1].set(ylabel='Pair translation error (m)',xlabel='Original current-frame index')
    for ax in axes:ax.grid(alpha=.18);ax.legend(ncol=4)
    fig.tight_layout();save(fig,'phase1_local_errors.png',[p for k in ['M2','A_selected','B2','C1'] for p in source(runs[k])], '一樓逐對姿態誤差；GT只供離線診斷，局部錯誤與累積軌跡誤差分開。')
    fig,axes=plt.subplots(1,2,figsize=(11,4));x=np.arange(4)
    for ax,a,b,title,ylabel in [(axes[0],'historical_mean_icp_rmse_m','custom_mean_icp_rmse_m','Mean local Euclidean inlier RMSE','RMSE (m)'),(axes[1],'open3d_mean_l2_m','custom_mean_l2_m','Global camera-centre disagreement','Mean L2 (m)')]:
        ax.bar(x-.18,[float(r[a]) for r in rows],.36,color=blue,label='Historical Point-to-Plane');ax.bar(x+.18,[float(r[b]) for r in rows],.36,color=orange,label='Custom Point-to-Point')
        ax.set_xticks(x,['F1 base','F1 C1','F2 base','F2 sparse']);ax.set(title=title,ylabel=ylabel);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
    axes[0].legend(fontsize=8);fig.tight_layout();save(fig,'bonus_local_global.png',[comparison], '自製ICP局部歐氏RMSE較低，但四組全域Mean L2皆較高；兩者不是相同目標。')
    write(OUT/'figure_manifest.json',dict(source_script='scripts/final_report.py',source_script_sha256=sha(__file__),
        style=dict(font='DejaVu Sans',dpi=240,estimated='#E02424',GT='black',historical=blue,intervention=orange),figures=manifest))
    # Python-generated review contact sheets, not official scientific figures.
    for tag,items in [('maps',[m for m in manifest if m['file'].endswith('_reference.png')]),('charts',[m for m in manifest if '_map.png' not in m['file'] and '_reference.png' not in m['file']])]:
        cols=3;w,h=480,390;sheet=Image.new('RGB',(cols*w,int(np.ceil(len(items)/cols))*h),'#eeeeee');draw=ImageDraw.Draw(sheet)
        for i,m in enumerate(items):
            im=ImageOps.contain(Image.open(OUT/m['file']).convert('RGB'),(w-12,h-30))
            x=(i%cols)*w;y=(i//cols)*h;sheet.paste(im,(x+(w-im.width)//2,y+25));draw.text((x+8,y+5),Path(m['file']).stem,fill='black')
        sheet.save(OUT/'audit'/('contact_'+tag+'.jpg'))
    print('Figures:',len(manifest))


def finalize():
    before=read(OUT/'audit/protected_before.json')
    changed=[p for p,h in before.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    now={str(p.relative_to(ROOT)) for p in protected_paths()}
    added=sorted(now-set(before))
    # This review does not write Finder metadata. Record the two exact observed
    # paths independently; never apply an extension-wide integrity exemption.
    metadata_paths={'docs/.DS_Store','research_outputs/m43_p2b_closeout_01/analysis/.DS_Store'}
    metadata=[]
    for name in sorted((set(changed)|set(added)) & metadata_paths):
        path=ROOT/name
        kind=subprocess.check_output(['file','-b',str(path)],text=True).strip()
        assert path.is_file() and not path.is_symlink() and path.read_bytes()[:8]==bytes.fromhex('0000000142756431')
        assert kind=='Apple Desktop Services Store'
        metadata.append(dict(path=name,original_sha256=before.get(name),current_sha256=sha(path),
            type=kind,header_hex=path.read_bytes()[:8].hex(),written_by_review_tools=False,
            writer_or_time_of_external_change='not established'))
    scientific_changes=[p for p in changed if p not in metadata_paths]
    links=[]
    for f in OUT.rglob('*.md'):
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',f.read_text()):
            if '://' in target or target.startswith('#'): continue
            path=target.strip('<>').split('#')[0]
            p=(ROOT/path.lstrip('/')) if path.startswith('/Users/') is False and path.startswith('/') else Path(path)
            if not path.startswith('/'):p=f.parent/path
            # These two linked receipts are emitted immediately below. Their
            # first creation must not be misclassified as a broken user link.
            generated=p.resolve() in {(OUT/'delivery_manifest.json').resolve(),(OUT/'audit/final_integrity.json').resolve()}
            links.append(dict(document=str(f.relative_to(OUT)),target=target,exists=p.exists() or generated))
    write(OUT/'audit/final_integrity.json',dict(protected_files=len(before),changed=changed,
        scientific_or_historical_changes=scientific_changes,finder_metadata_observations=metadata,new_files_in_protected_trees=added,
        markdown_links=links,broken_links=[l for l in links if not l['exists']],formal_reconstruction_executed=False,
        english_report_created=False,formal_pdf_created=False,final_zip_created=False))
    write(OUT/'delivery_manifest.json',{str(p.relative_to(ROOT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json'})
    assert not scientific_changes and not [l for l in links if not l['exists']]
    print('Preservation and Markdown links passed;',len(before),'protected files;',len(links),'links')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['snapshot','analyze','figures','finalize'])
    globals()[parser.parse_args().command]()
