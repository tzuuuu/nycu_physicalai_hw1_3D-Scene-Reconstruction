"""Offline four-condition Bonus comparisons; never invokes registration."""
import csv
import os
from pathlib import Path
import subprocess
import sys

os.environ.setdefault('MPLCONFIGDIR', '/tmp/m5-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation
from scripts.m5_bonus import ROOT, OUT, CONDITIONS, expected_frames, read, lines, verify, original_icp
from scripts.m42_monitor import write
from scripts.m4_capture_check import sha
import api

C1 = ROOT/'research_outputs/m32_p1_m32_20261118_c_v005_s1_01'
HIST = {
 'f1_baseline': dict(obs=ROOT/'research_outputs/m3_20261118_diagnostic_02',
    mean=3.174055104788137, worker_s=286.378044, reconstruction_s=None,
    png=ROOT/'experiments/p1_baseline_20261118_map005_s0_01/reconstruction_baseline.png',
    note='Original M2 native image and score; positions/RANSAC from previously verified matching M3.0 diagnostic. No original full map saved.'),
 'f1_c1': dict(obs=C1/'observation', mean=.15569670960683304, worker_s=301.956051667,
    reconstruction_s=290.21397812500004,
    png=ROOT/'experiments/p1_m32_20261118_c_v005_s1_01/reconstruction_baseline.png',
    note='Historical same-run poses and stride-sampled map; original complete cloud unavailable.'),
 'f2_baseline': dict(obs=ROOT/'research_outputs/m42_p2_a01_baseline_01/observation',
    mean=.07025845236530649, worker_s=220.751497, reconstruction_s=207.318515709,
    png=ROOT/'research_outputs/m42_p2_a01_baseline_01/observation/unused.png', note='Historical same-run full saved map.'),
 'f2_sparse': dict(obs=ROOT/'research_outputs/m43_p2b_selected_01/observation',
    mean=.04487258932911286, worker_s=163.365968959, reconstruction_s=145.343667667,
    png=ROOT/'experiments/p2_114753116_a01_baseline_01/reconstruction_selected.png', note='Historical frozen sparse-v1; same-run full saved map.'),
}
HIST['f2_baseline']['png'] = ROOT/'experiments/p2_114753116_a01_baseline_01/reconstruction_baseline.png'


def csv_write(path, rows):
    with Path(path).open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def gt_camera(capture, frames):
    gt = np.load(capture/'GT_pose.npy').astype(np.float64)
    q = gt[0, 3:]
    r = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()
    return ((gt[:, :3]-gt[0, :3]) @ r @ np.diag([1., -1., -1.]))[np.array(frames)-1]


def matrices(obs):
    if (obs/'pairwise_ransac.npy').exists():
        return np.load(obs/'pairwise_ransac.npy')
    return np.array([r['trans_init'] for r in lines(obs/'transforms.jsonl')])


def sampled_map(obs, limit=90000):
    if (obs/'map_points.npy').exists():
        points = np.load(obs/'map_points.npy', mmap_mode='r')
        colors = np.load(obs/'map_colors.npy', mmap_mode='r')
    elif (obs/'map_sample.npz').exists():
        with np.load(obs/'map_sample.npz') as data:
            points, colors = data['points'], data['colors']
    else:
        return None
    indices = np.linspace(0, len(points)-1, min(limit, len(points)), dtype=int)
    return np.asarray(points[indices]), np.asarray(colors[indices])


def analyze():
    if not (OUT/'suite.accepted.json').exists():
        raise RuntimeError('Four accepted reconstructions required')
    verify(read(OUT/'protected.before.json'))
    if original_icp((ROOT/'utils.py').read_text()) != (OUT/'original_local_icp_algorithm.txt').read_text():
        raise RuntimeError('Original ICP changed')
    dest = OUT/'analysis'
    dest.mkdir(exist_ok=False)
    figures = dest/'figures'
    figures.mkdir()
    # Backend declarations use a Turtle blank node. Compare graph isomorphism,
    # not parser-local blank-node IDs, after removing only the new Selected run.
    from rdflib import Graph
    from rdflib.compare import isomorphic
    baseline_text = (OUT/'f2_baseline/experiment.after.ttl').read_text()
    final_ttl = ROOT/'experiments'/CONDITIONS['f2_sparse']['experiment']
    final_ttl = final_ttl/(final_ttl.name+'.ttl')
    final_text = final_ttl.read_text()
    if api._split_sections(baseline_text)[0] != api._split_sections(final_text)[0]:
        raise RuntimeError('Selected changed declaration bytes')
    original_graph = Graph().parse(data=baseline_text, format='turtle')
    final_exp = api.read_experiment(str(final_ttl))
    selected_run = api.data_run_iri(final_exp['exp_name'], 'selected')
    reduced = Graph()
    for s, p, o in final_exp['graph']:
        if s != selected_run and (s, p, o) != (final_exp['exp_iri'], api.HW1.hasRun, selected_run):
            reduced.add((s, p, o))
    if not isomorphic(original_graph, reduced):
        raise RuntimeError('Selected changed sealed baseline graph or factors')
    write(dest/'selected_preservation.json', dict(declaration_bytes_unchanged=True,
        baseline_graph_isomorphic=True, baseline_factors_retained=2554, seal_valid=True))
    for experiment in sorted({spec['experiment'] for spec in CONDITIONS.values()}):
        workspace = ROOT/'experiments'/experiment
        ttl = workspace/(experiment+'.ttl')
        before = sha(ttl)
        result = subprocess.run([sys.executable, str(ROOT/'api.py'), 'explore', str(workspace)],
                                capture_output=True, text=True, check=True)
        (dest/(experiment+'_explore.log')).write_text(result.stdout+result.stderr)
        if sha(ttl) != before:
            raise RuntimeError('Explore changed experiment Turtle')
    rows, all_frames, pair_rows, loaded = [], [], [], {}
    flip_diagnostics = []
    for key, spec in CONDITIONS.items():
        new = OUT/key/'observation'
        old = HIST[key]['obs']
        frames = expected_frames(key)
        gt = gt_camera(ROOT/spec['capture'], frames)
        pred, before = np.load(new/'positions.npy'), np.load(old/'positions.npy')
        error, old_error = np.linalg.norm(pred-gt, axis=1), np.linalg.norm(before-gt, axis=1)
        mean = read(new/'official_evaluation.json')['mean_l2_raw_m']
        np.testing.assert_allclose(error.mean(), mean, rtol=0, atol=1e-12)
        np.testing.assert_allclose(old_error.mean(), HIST[key]['mean'], rtol=0, atol=1e-12)
        coarse, reference = matrices(new), matrices(old)
        difference = np.max(np.abs(coarse-reference), axis=(1, 2))
        np.save(dest/(key+'_ransac_absolute_delta.npy'), difference)
        timing = read(new/'observer_summary.json')
        worker = read(OUT/(key+'_monitor')/'execution.json')
        final = read(OUT/key/'accepted.json')
        iteration = lines(new/'icp_timing.jsonl')
        new_pairs, old_pairs = lines(new/'transforms.jsonl'), lines(old/'transforms.jsonl')
        new_events, old_events = lines(new/'events.jsonl'), lines(old/'events.jsonl')
        fields = ['raw_point_count', 'point_yield', 'coarse_fitness', 'coarse_rmse',
                  'coarse_correspondences', 'icp_fitness', 'icp_rmse', 'icp_correspondences']
        fig, axes = plt.subplots(4, 2, figsize=(13, 12))
        for ax, field in zip(axes.flat, fields):
            for events, label, color in [(old_events, 'Historical Open3D', '#356ca5'),
                                         (new_events, 'Custom ICP', '#d97721')]:
                relevant = [e for e in events if field in e]
                ax.plot([e['stem'] for e in relevant], [e[field] for e in relevant],
                        label=label, color=color, lw=1.)
            ax.set(title=field+(' (m)' if 'rmse' in field else ''), xlabel='Original frame index')
            ax.grid(alpha=.2)
        axes.flat[0].legend(fontsize=8)
        fig.suptitle(key+' | Eight observed pipeline factors; no qualification thresholds')
        fig.tight_layout(); fig.savefig(figures/(key+'_factors.png'), dpi=180, bbox_inches='tight'); plt.close(fig)
        row = dict(condition=key, frames=len(frames), retained_fraction=len(frames)/(191 if spec['floor']==1 else 320),
            voxel_m=.05, seed=spec['seed'], map_voxel_m=.05,
            open3d_mean_l2_m=HIST[key]['mean'], custom_mean_l2_m=mean,
            l2_delta_m=mean-HIST[key]['mean'],
            custom_max_l2_m=float(error.max()), custom_final_l2_m=float(error[-1]),
            historical_worker_s=HIST[key]['worker_s'], custom_worker_s=worker['elapsed_s'],
            historical_reconstruction_s=HIST[key]['reconstruction_s'],
            custom_reconstruction_s=timing['reconstruction_s_with_observation'],
            custom_icp_total_s=timing['icp_total_s'], historical_icp_s=None,
            historical_mean_icp_rmse_m=float(np.mean([p['icp_rmse'] for p in old_pairs])),
            custom_mean_icp_rmse_m=float(np.mean([p['icp_rmse'] for p in new_pairs])),
            historical_mean_icp_fitness=float(np.mean([p['icp_fitness'] for p in old_pairs])),
            custom_mean_icp_fitness=float(np.mean([p['icp_fitness'] for p in new_pairs])),
            custom_peak_tree_rss_gib=worker['peak_tree_rss_bytes']/2**30,
            ransac_exact_matching_pairs=int(np.count_nonzero(difference==0)),
            ransac_pairs=len(difference), ransac_max_abs_delta=float(difference.max()),
            median_icp_iterations=float(np.median([r['iterations'] for r in iteration])),
            max_iteration_pairs=sum(r['reason']=='max_iterations' for r in iteration),
            map_points=read(new/'map_summary.json')['point_count'],
            factor_observations=final['factor_observations'])
        rows.append(row)
        for stem, a, b in zip(frames, old_error, error):
            all_frames.append(dict(condition=key, frame=stem, open3d_l2_m=float(a), custom_l2_m=float(b)))
        pairs = new_pairs
        for p, t, d in zip(pairs, iteration, difference):
            pair_rows.append(dict(condition=key, previous=p['prev_stem'], current=p['stem'],
                coarse_fitness=p['coarse_fitness'], coarse_rmse_m=p['coarse_rmse'],
                custom_fitness=p['icp_fitness'], custom_rmse_m=p['icp_rmse'],
                correspondences=p['icp_correspondences'], iterations=t['iterations'],
                termination=t['reason'], icp_s=t['seconds'], ransac_max_abs_delta=float(d)))
        if spec['floor'] == 1:
            raw_gt = np.load(ROOT/spec['capture']/'GT_pose.npy').astype(float)
            rotations = Rotation.from_quat(raw_gt[:, [4, 5, 6, 3]]).as_matrix()
            axes_change = np.diag([1., -1., -1.])
            truth_pair = np.eye(4)
            truth_pair[:3, :3] = axes_change @ rotations[102].T @ rotations[103] @ axes_change
            truth_pair[:3, 3] = axes_change @ rotations[102].T @ (raw_gt[103, :3]-raw_gt[102, :3])
            old_pair = old_pairs[102]
            for backend, transform in [('RANSAC', coarse[102]),
                ('historical_open3d', np.array(old_pair['icp_transformation'])),
                ('custom', np.array(pairs[102]['icp_transformation']))]:
                flip_diagnostics.append(dict(condition=key, previous=103, current=104, backend=backend,
                    rotation_error_deg=float(np.degrees(Rotation.from_matrix(
                        truth_pair[:3, :3].T @ transform[:3, :3]).magnitude())),
                    translation_error_m=float(np.linalg.norm(truth_pair[:3, 3]-transform[:3, 3]))))
        oldmap, newmap = sampled_map(old), sampled_map(new)
        loaded[key] = dict(pred=pred, before=before, gt=gt, frames=frames, error=error,
                           old_error=old_error, oldmap=oldmap, newmap=newmap, iteration=iteration)
        # Same axes include all displayed maps and all trajectory extrema.
        arrays = [pred, before, gt]+[m[0] for m in [oldmap, newmap] if m is not None]
        xz = np.concatenate([a[:, [0, 2]] for a in arrays])
        lo, hi = np.floor(xz.min(axis=0))-1, np.ceil(xz.max(axis=0))+1
        fig, axes = plt.subplots(1, 2, figsize=(13, 6))
        for ax, cloud, path, title in zip(axes, [oldmap, newmap], [before, pred],
                ['Historical Open3D Point-to-Plane', 'Custom Point-to-Point']):
            if cloud is not None:
                p, c = cloud
                ax.scatter(p[:, 0], p[:, 2], c=c, s=.35, linewidths=0, rasterized=True)
            else:
                ax.text(.02, .98, 'Original full map unavailable; trajectory only\nVerified matching diagnostic trajectory',
                        transform=ax.transAxes, va='top', fontsize=8)
            ax.plot(path[:, 0], path[:, 2], c='red', lw=1.2, label='Estimated')
            ax.plot(gt[:, 0], gt[:, 2], c='black', lw=1.1, label='Ground truth')
            ax.set(xlim=(lo[0], hi[0]), ylim=(lo[1], hi[1]), xlabel='Camera X (m)', ylabel='Camera Z (m)', title=title)
            ax.set_aspect('equal')
            ax.legend(loc='lower left', fontsize=8)
        fig.suptitle('%s | %d frames | Mean L2: %.6f -> %.6f m'%(key, len(frames), HIST[key]['mean'], mean))
        fig.tight_layout()
        fig.savefig(figures/(key+'_maps.png'), dpi=200, bbox_inches='tight')
        plt.close(fig)
        # Preserve original native screenshot comparison without claiming common view.
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        for ax, image, title in zip(axes, [HIST[key]['png'], OUT/key/'reconstruction_native.png'],
                                    ['Historical Open3D (original view)', 'Custom ICP (native view)']):
            ax.imshow(Image.open(image)); ax.axis('off'); ax.set_title(title)
        fig.suptitle(key+' | Native images; viewpoints and limits may differ')
        fig.tight_layout(); fig.savefig(figures/(key+'_native.png'), dpi=160, bbox_inches='tight'); plt.close(fig)
        # Standalone 3D rendering of the saved custom map.
        fig = plt.figure(figsize=(10, 8)); ax = fig.add_subplot(111, projection='3d')
        p, c = newmap
        ax.scatter(p[:, 0], p[:, 2], -p[:, 1], c=c, s=.35, linewidths=0, rasterized=True)
        for path, color, label in [(pred, 'red', 'Estimated'), (gt, 'black', 'Ground truth')]:
            ax.plot(path[:, 0], path[:, 2], -path[:, 1], c=color, label=label, lw=1.4)
        span = np.ptp(np.concatenate([p, pred, gt]), axis=0)
        ax.set_box_aspect(np.maximum(span[[0, 2, 1]], .01))
        ax.set(xlabel='Camera X (m)', ylabel='Camera Z (m)', zlabel='Height (-Y, m)', title=key+' | Custom ICP')
        ax.view_init(35, -55); ax.legend(loc='upper left')
        fig.savefig(figures/(key+'_custom_3d.png'), dpi=200, bbox_inches='tight'); plt.close(fig)
    csv_write(dest/'comparison.csv', rows)
    csv_write(dest/'per_frame_l2.csv', all_frames)
    csv_write(dest/'pairs.csv', pair_rows)
    csv_write(dest/'frame103_104_diagnostics.csv', flip_diagnostics)
    for left, right, name in [('f1_baseline', 'f1_c1', 'custom_f1_seed_comparison'),
                              ('f2_baseline', 'f2_sparse', 'custom_f2_density_comparison')]:
        selected = [loaded[left], loaded[right]]
        xz = np.concatenate([a[:, [0, 2]] for r in selected for a in [r['newmap'][0], r['pred'], r['gt']]])
        lo, hi = np.floor(xz.min(axis=0))-1, np.ceil(xz.max(axis=0))+1
        fig, axes = plt.subplots(1, 2, figsize=(13, 6))
        for ax, key, r in zip(axes, [left, right], selected):
            p, c = r['newmap']
            ax.scatter(p[:, 0], p[:, 2], c=c, s=.35, linewidths=0, rasterized=True)
            for path, color, label in [(r['pred'], 'red', 'Estimated'), (r['gt'], 'black', 'Ground truth')]:
                ax.plot(path[:, 0], path[:, 2], c=color, lw=1.2, label=label)
            ax.set(xlim=(lo[0], hi[0]), ylim=(lo[1], hi[1]), xlabel='Camera X (m)', ylabel='Camera Z (m)',
                   title='%s | N=%d | Mean L2 %.6f m'%(key, len(r['frames']), r['error'].mean()))
            ax.set_aspect('equal'); ax.legend(fontsize=8)
        fig.suptitle('Custom ICP | fixed first camera | shared limits and scale')
        fig.tight_layout(); fig.savefig(figures/(name+'.png'), dpi=200, bbox_inches='tight'); plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    for ax, (key, r) in zip(axes.flat, loaded.items()):
        ax.plot(r['frames'], r['old_error'], label='Historical Open3D', color='#356ca5')
        ax.plot(r['frames'], r['error'], label='Custom ICP', color='#d97721')
        ax.set(title=key, xlabel='Original frame index', ylabel='L2 error (m)'); ax.legend(); ax.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(figures/'per_frame_l2.png', dpi=200, bbox_inches='tight'); plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    for ax, (key, r) in zip(axes.flat, loaded.items()):
        timing = r['iteration']
        ax.plot([p['current'] for p in timing], [p['iterations'] for p in timing], color='#447c69')
        ax.axhline(60, color='#ad4545', ls='--', lw=1., label='60-update cap')
        ax.set(title=key, xlabel='Current original frame index', ylabel='Custom ICP updates', ylim=(0, 64))
        ax.legend(fontsize=8); ax.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(figures/'custom_iterations.png', dpi=200, bbox_inches='tight'); plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(13, 11))
    for ax, (key, r), summary in zip(axes.flat, loaded.items(), rows):
        p, c = r['newmap']
        ax.scatter(p[:, 0], p[:, 2], c=c, s=.4, linewidths=0, rasterized=True)
        for path, color, label in [(r['pred'], 'red', 'Estimated'), (r['gt'], 'black', 'Ground truth')]:
            ax.plot(path[:, 0], path[:, 2], c=color, lw=1.2, label=label)
        ax.set_aspect('equal')
        ax.set(xlabel='Camera X (m)', ylabel='Camera Z (m)',
               title='%s | N=%d | Mean L2 %.6f m'%(key, summary['frames'], summary['custom_mean_l2_m']))
        ax.legend(fontsize=8)
    fig.suptitle('Custom ICP reconstructions | ceiling removed | fixed first-camera reference')
    fig.tight_layout(); fig.savefig(figures/'custom_overview.png', dpi=200, bbox_inches='tight'); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    x = np.arange(4)
    for ax, old_key, new_key, ylabel, title in [
        (axes[0], 'open3d_mean_l2_m','custom_mean_l2_m','Mean L2 (m)','Trajectory error'),
        (axes[1], 'historical_worker_s','custom_worker_s','Seconds','Recorded worker times (different boundaries)')]:
        ax.bar(x-.18,[r[old_key] for r in rows],.36,label='Historical Open3D')
        ax.bar(x+.18,[r[new_key] for r in rows],.36,label='Custom ICP')
        ax.set_xticks(x); ax.set_xticklabels(list(CONDITIONS), rotation=15)
        ax.set(ylabel=ylabel,title=title); ax.legend()
    fig.tight_layout(); fig.savefig(figures/'error_and_recorded_runtime.png', dpi=200, bbox_inches='tight'); plt.close(fig)
    sparse = np.array(expected_frames('f2_sparse'))-1
    density = dict(open3d_baseline_on_sparse_mean_l2_m=float(loaded['f2_baseline']['old_error'][sparse].mean()),
        open3d_sparse_mean_l2_m=float(loaded['f2_sparse']['old_error'].mean()),
        custom_baseline_on_sparse_mean_l2_m=float(loaded['f2_baseline']['error'][sparse].mean()),
        custom_sparse_mean_l2_m=float(loaded['f2_sparse']['error'].mean()))
    write(dest/'summary.json', dict(comparison=rows, density_same_frame=density,
        original_icp_unchanged=True, historical_inputs_unchanged=True,
        limitations=['Single run per condition; no significance claim.',
          'Point-to-Point and Point-to-Plane minimize different objectives and use different stopping criteria (60 vs 100 cap).',
          'Historical runtime boundaries/overhead and run dates differ; no pure ICP speedup can be inferred.',
          'F1 original M2 has no saved full map; verified matching diagnostic poses are explicitly labeled.',
          'C1 historical cloud is a saved stride sample, not the complete cloud.',
          'No GT fitting or GT-informed reselection; map completeness has no surface ground truth.']))
    source_paths = [SP for SP in [ROOT/'scripts/m5_analysis.py', OUT/'plan.json', OUT/'suite.accepted.json']]
    for key in CONDITIONS:
        source_paths += [OUT/key/'accepted.json', OUT/key/'observation/positions.npy',
            OUT/key/'observation/map_points.npy', OUT/key/'observation/map_colors.npy',
            HIST[key]['obs']/'positions.npy', HIST[key]['obs']/'transforms.jsonl', HIST[key]['png']]
    write(dest/'sources.json', {str(p.relative_to(ROOT)):sha(p) for p in source_paths})
    verify(read(OUT/'protected.before.json'))
    write(dest/'manifest.json', {str(p.relative_to(ROOT)):sha(p) for p in sorted(dest.rglob('*')) if p.is_file()})
    print('Analysis complete: '+str(dest))


if __name__ == '__main__':
    analyze()
