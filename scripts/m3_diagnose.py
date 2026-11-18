"""M3.0 獨立全影格診斷；固定參數、不寫正式實驗、不執行介入。"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import utils  # 沿用核心的 OpenMP 設定，先於其他數值套件載入。
import api
import numpy as np
from scipy.spatial.transform import Rotation

BASE = ROOT / 'research_outputs/m2_phase1_baseline_20261118_01'
EXP = ROOT / 'experiments/p1_baseline_20261118_map005_s0_01'
DATA = ROOT / 'eval/_data/first_floor'
FIELDS = {'raw_point_count': 'RawPointCount', 'point_yield': 'VoxelizedPointYield',
          'coarse_fitness': 'CoarseRANSACFitness', 'coarse_rmse': 'CoarseRANSACRMSE',
          'coarse_correspondences': 'CoarseRANSACCorrespondences',
          'icp_fitness': 'ICPInlierFitness', 'icp_rmse': 'ICPInlierRMSE',
          'icp_correspondences': 'ICPInlierCorrespondences'}


def dump(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)


def fingerprint(paths):
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths) if p.is_file()}


def capture_digest():
    h = hashlib.sha256()
    for stem, rgb, depth in api._pair_frames(str(DATA)):
        for path in [Path(rgb), Path(depth)]:
            h.update(str(path.relative_to(DATA)).encode())
            h.update(path.read_bytes())
    for name in ['intrinsics.json', 'GT_pose.npy']:
        h.update(name.encode())
        h.update((DATA / name).read_bytes())
    return h.hexdigest()


def compare_factors(events, rows):
    official = {(r['factor'], int(r['previous']) if r['previous'] else None,
                 int(r['current'])): float(r['value']) for r in rows}
    measured = {}
    for e in events:
        for key, name in FIELDS.items():
            if key in e:
                identity = (name, e.get('prev_stem'), e['stem'])
                if identity in measured:
                    raise ValueError('Duplicate diagnostic factor')
                measured[identity] = api._storable(e[key])
    differences = [{'identity': k, 'official': official.get(k), 'diagnostic': measured.get(k)}
                   for k in official.keys() | measured.keys()
                   if official.get(k) != measured.get(k)]
    return {'official_count': len(official), 'diagnostic_count': len(measured),
            'mismatch_count': len(differences), 'differences': differences}


def gt_camera_poses(gt):
    """世界中的 Habitat 相機姿態轉為首影格影像軸；不做最佳擬合。"""
    rotations = Rotation.from_quat(gt[:, [4, 5, 6, 3]]).as_matrix()
    axes = utils.CAM_TO_GT_AXES
    poses = np.repeat(np.eye(4)[None], len(gt), axis=0)
    poses[:, :3, :3] = axes @ rotations[0].T @ rotations @ axes
    poses[:, :3, 3] = (gt[:, :3] - gt[0, :3]) @ rotations[0] @ axes
    return poses


def angle(matrix):
    return float(np.degrees(Rotation.from_matrix(matrix[:3, :3]).magnitude()))


def pair_metrics(predicted, truth, initial):
    # 平移均在「前一相機」座標系比較；旋轉使用 SO(3) 測地角。
    return {'gt_translation_m': float(np.linalg.norm(truth[:3, 3])),
            'pred_translation_m': float(np.linalg.norm(predicted[:3, 3])),
            'gt_rotation_deg': angle(truth), 'pred_rotation_deg': angle(predicted),
            'relative_translation_error_m': float(np.linalg.norm(predicted[:3, 3] - truth[:3, 3])),
            'relative_rotation_error_deg': angle(truth.T[:3, :3] @ predicted[:3, :3]),
            'coarse_translation_error_m': float(np.linalg.norm(initial[:3, 3] - truth[:3, 3])),
            'coarse_rotation_error_deg': angle(truth.T[:3, :3] @ initial[:3, :3]),
            'icp_correction_translation_m': float(np.linalg.norm(predicted[:3, 3] - initial[:3, 3])),
            'icp_correction_rotation_deg': angle(initial.T[:3, :3] @ predicted[:3, :3])}


def fresh_output(output):
    output = Path(output).resolve()
    if ROOT / 'research_outputs' not in output.parents:
        raise ValueError('Output must be a new directory under research_outputs')
    output.mkdir(parents=True, exist_ok=False)
    return output


def capture(output):
    output = fresh_output(output)
    config = json.loads((BASE / 'config.before_run.json').read_text())
    protected = [p for root in [ROOT / 'research_outputs', ROOT / 'experiments', DATA]
                 for p in root.rglob('*') if output not in p.parents]
    protected += [ROOT / name for name in ['utils.py', 'api.py', 'reconstruct.py',
                                         'ontology/hw1.ttl', 'pixi.toml', 'pixi.lock']]
    before = fingerprint(protected)
    digest = capture_digest()
    if digest != config['capture_sha256']:
        raise RuntimeError('Capture differs from official baseline')
    for name in ['utils.py', 'api.py', 'reconstruct.py', 'ontology/hw1.ttl', 'pixi.toml', 'pixi.lock']:
        original = subprocess.check_output(['git', 'show', config['git_commit'] + ':' + name], cwd=ROOT)
        if original != (ROOT / name).read_bytes():
            raise RuntimeError('Core source differs: ' + name)
    experiment = api.read_experiment(str(EXP))
    frames = [int(s) for s, _, _ in api._pair_frames(str(DATA))]
    if frames != experiment['frame_indices'] or len(frames) != 191 or not experiment['complete']:
        raise RuntimeError('Formal full-batch frame identity/completeness mismatch')
    versions = {name: importlib.metadata.version(name) for name in config['versions']}
    if versions != config['versions']:
        raise RuntimeError('Software versions differ from official baseline')
    params = dict(version='open3d', voxel_size=0.05, registration_seed=0, build_cloud=False)
    dump(output / 'protected.before.json', before)
    dump(output / 'config.json', {'kind': 'M3.0_diagnostic_only', 'frames': frames,
         'baseline_git_commit': config['git_commit'],
         'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
         'core_identical_to_baseline': True, 'capture_sha256': digest,
         'parameters': params, 'baseline_algorithm': config['algorithm'],
         'map_difference': 'build_cloud=False; down_voxel=None; no map or ceiling crop',
         'versions': versions, 'python': sys.version, 'OMP_NUM_THREADS': os.environ.get('OMP_NUM_THREADS'),
         'started_unix': time.time(), 'command': sys.argv,
         'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    events, transforms = [], []
    def record(kind, payload):
        e = dict(kind=kind, **payload)
        events.append(e)
        with (output / 'events.jsonl').open('a') as f:
            f.write(json.dumps(e) + '\n')
    def diagnostic(payload):
        item = {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in payload.items()}
        transforms.append(item)
        with (output / 'transforms.jsonl').open('a') as f:
            f.write(json.dumps(item) + '\n')
    started = time.perf_counter()
    _, positions = utils.reconstruct(str(DATA), pipeline_callback=record,
                                     diagnostics_callback=diagnostic, **params)
    elapsed = time.perf_counter() - started
    np.save(output / 'positions.npy', positions)
    if len(positions) != 191 or len(transforms) != 190:
        raise RuntimeError('Incomplete full-batch reconstruction')
    # 到此重建已完成並保存，才允許評估函式載入 GT。
    l2 = utils.visualize_and_evaluate(None, positions, str(DATA), show=False)
    with (BASE / 'factor_occurrences.csv').open() as f:
        comparison = compare_factors(events, list(csv.DictReader(f)))
    baseline_l2 = json.loads((BASE / 'validation.json').read_text())['mean_l2_raw_m']
    unchanged = fingerprint(protected) == before
    matched = comparison['mismatch_count'] == 0 and abs(l2 - baseline_l2) <= 1e-10
    result = {'reconstructed_frames': len(positions), 'pairs': len(transforms),
              'mean_l2_m': l2, 'official_mean_l2_m': baseline_l2,
              'l2_difference_m': l2 - baseline_l2, 'factor_comparison': comparison,
              'protected_files_unchanged': unchanged, 'protected_files_count': len(before),
              'reconstruction_s': elapsed, 'baseline_equivalent': matched,
              'status': 'matched_ready_for_analysis' if matched and unchanged else 'DIFFERENCE_STOP_REPORT'}
    dump(output / 'comparison.json', result)
    print(json.dumps(result, indent=2), flush=True)
    if not matched or not unchanged:
        raise RuntimeError('Diagnostic differs; report before further interpretation')


def write_csv(path, rows):
    with path.open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def analyze(run, output):
    run, output = Path(run), fresh_output(output)
    check = json.loads((run / 'comparison.json').read_text())
    if not check['baseline_equivalent'] or not check['protected_files_unchanged']:
        raise RuntimeError('Do not mix unmatched diagnostic and official baseline')
    config = json.loads((run / 'config.json').read_text())
    frames = config['frames']
    events = [json.loads(s) for s in (run / 'events.jsonl').read_text().splitlines()]
    transforms = [json.loads(s) for s in (run / 'transforms.jsonl').read_text().splitlines()]
    positions = np.load(run / 'positions.npy')
    truth = gt_camera_poses(np.load(DATA / 'GT_pose.npy'))
    poses = [np.eye(4)]
    for t in transforms:
        poses.append(poses[-1] @ np.array(t['icp_transformation']))
    poses = np.array(poses)
    np.testing.assert_allclose(poses[:, :3, 3], positions, rtol=0, atol=1e-12)
    errors = np.linalg.norm(positions - truth[:, :3, 3], axis=1)
    np.testing.assert_allclose(errors.mean(), check['mean_l2_m'], rtol=0, atol=1e-12)
    import cv2
    rows = []
    frame_events = {e['stem']: e for e in events if e['kind'] == 'frame'}
    for i, stem in enumerate(frames):
        d = cv2.imread(str(DATA / 'depth' / f'{stem}.png'), cv2.IMREAD_UNCHANGED)
        valid = d[d > 0] / 1000
        r = dict(frame=stem, l2_m=float(errors[i]),
                 l2_change_m=float(errors[i] - errors[i-1]) if i else 0.,
                 cumulative_mean_l2_m=float(errors[:i+1].mean()),
                 cumulative_orientation_error_deg=angle(truth[i, :3, :3].T @ poses[i, :3, :3]),
                 valid_depth_fraction=float((d > 0).mean()),
                 depth_p10_m=float(np.percentile(valid, 10)), depth_median_m=float(np.median(valid)),
                 depth_p90_m=float(np.percentile(valid, 90)), **{k: frame_events[stem][k] for k in ['raw_point_count', 'point_yield']})
        for label, array in [('pred', positions[i]), ('gt', truth[i, :3, 3])]:
            r.update({label + '_' + axis + '_m': float(v) for axis, v in zip('xyz', array)})
        rows.append(r)
    pairs = []
    for i, t in enumerate(transforms, 1):
        relative_gt = np.linalg.inv(truth[i-1]) @ truth[i]
        m = pair_metrics(np.array(t['icp_transformation']), relative_gt, np.array(t['trans_init']))
        m.update(previous=t['prev_stem'], current=t['stem'], l2_m=rows[i]['l2_m'],
                 l2_change_m=rows[i]['l2_change_m'], valid_depth_fraction=rows[i]['valid_depth_fraction'])
        m.update({k: t[k] for k in FIELDS if k in t})
        pairs.append(m)
    write_csv(output / 'frames.csv', rows)
    write_csv(output / 'pairs.csv', pairs)
    np.savez(output / 'poses_offline.npz', predicted=poses, gt=truth)
    from scipy.stats import spearmanr
    correlations = []
    for factor in list(FIELDS) + ['valid_depth_fraction', 'gt_translation_m', 'gt_rotation_deg']:
        for target in ['l2_m', 'l2_change_m', 'relative_translation_error_m', 'relative_rotation_error_deg']:
            x, y = [p[factor] for p in pairs], [p[target] for p in pairs]
            correlations.append({'factor': factor, 'target': target,
                                 'spearman_rho': float(spearmanr(x, y).statistic), 'n': len(pairs)})
    write_csv(output / 'correlations.csv', correlations)
    sections = []
    for lo, hi in [(1,20), (21,48), (49,55), (56,70), (71,103), (71,133), (104,116),
                   (117,133), (134,146), (147,151), (152,191)]:
        a = [r for r in rows if lo <= r['frame'] <= hi]
        b = [p for p in pairs if lo <= p['current'] <= hi]
        sections.append({'start': lo, 'end': hi, 'l2_start_m': a[0]['l2_m'],
                         'l2_end_m': a[-1]['l2_m'], 'mean_l2_m': float(np.mean([r['l2_m'] for r in a])),
                         'max_relative_translation_error_m': max([p['relative_translation_error_m'] for p in b], default=0),
                         'max_relative_rotation_error_deg': max([p['relative_rotation_error_deg'] for p in b], default=0),
                         'valid_fraction_min': min(r['valid_depth_fraction'] for r in a),
                         'yield_min': min(r['point_yield'] for r in a)})
    summary = {'source_run': str(run), 'n': len(rows), 'mean_l2_m': float(errors.mean()),
               'first20_mean_l2_m': float(errors[:20].mean()),
               'first_exceedance_frames': {str(v): next((r['frame'] for r in rows if r['l2_m'] > v), None)
                                          for v in [0.02,0.05,0.1,0.25,0.5,1,2,3,5]},
               'largest_l2_increases': sorted(rows, key=lambda r: r['l2_change_m'], reverse=True)[:12],
               'largest_relative_errors': sorted(pairs, key=lambda r: r['relative_translation_error_m'], reverse=True)[:12],
               'sections': sections}
    dump(output / 'summary.json', summary)
    make_plots(output, rows, pairs, positions, truth, correlations)
    print(json.dumps(summary, indent=2))


def make_plots(output, rows, pairs, positions, truth, correlations):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    x = [r['frame'] for r in rows]
    px = [p['current'] for p in pairs]
    def save(fig, name):
        fig.savefig(output / name, dpi=150)
        plt.close(fig)
    def decorate(axes):
        for ax in np.asarray(axes).flat:
            for lo,hi in [(49,55),(71,133),(104,116),(147,151)]:
                ax.axvspan(lo,hi,alpha=.07,color='orange')
            ax.grid(alpha=.25)
            ax.set_xlabel('Frame stem (pair = previous -> current)')
    fig, ax = plt.subplots(3,1,figsize=(13,9),constrained_layout=True)
    ax[0].plot(x,[r['l2_m'] for r in rows],label='Frame L2')
    ax[0].plot(x,[r['cumulative_mean_l2_m'] for r in rows],label='Prefix mean L2')
    ax[0].set_ylabel('m'); ax[0].legend()
    ax[1].plot(x,[r['l2_m'] for r in rows]); ax[1].set_yscale('symlog',linthresh=.01); ax[1].set_ylabel('L2 (m, symlog)')
    ax[2].plot(x,[r['l2_change_m'] for r in rows]); ax[2].set_ylabel('L2 change (m)')
    decorate(ax); fig.suptitle('M3.0 matched full-batch diagnostic: fixed first-pose alignment')
    save(fig,'trajectory_errors.png')
    fig, ax = plt.subplots(4,1,figsize=(13,11),constrained_layout=True)
    for axis,keys,ylabel in zip(ax,[['gt_translation_m','pred_translation_m'],['gt_rotation_deg','pred_rotation_deg'],
                                   ['relative_translation_error_m','coarse_translation_error_m'],
                                   ['relative_rotation_error_deg','coarse_rotation_error_deg']],['Motion (m)','Motion (deg)','Local error (m)','Local error (deg)']):
        for key in keys: axis.plot(px,[p[key] for p in pairs],label=key)
        axis.set_ylabel(ylabel); axis.legend(fontsize=8)
    decorate(ax); save(fig,'relative_motion.png')
    fig, ax = plt.subplots(6,1,figsize=(14,15),constrained_layout=True)
    for axis,keys,ylabel in zip(ax,[['coarse_fitness','icp_fitness'],['coarse_rmse','icp_rmse'],
                                   ['coarse_correspondences','icp_correspondences'],['point_yield','raw_point_count'],
                                   ['icp_correction_translation_m','relative_translation_error_m'],
                                   ['icp_correction_rotation_deg','relative_rotation_error_deg']],
                                ['Fitness','RMSE (m)','Correspondences','Points','Translation (m)','Rotation (deg)']):
        for key in keys: axis.plot(px,[p[key] for p in pairs],label=key)
        axis.set_ylabel(ylabel); axis.legend(fontsize=8,loc='upper left')
    decorate(ax); save(fig,'registration_comparison.png')
    fig, ax = plt.subplots(2,4,figsize=(16,7),constrained_layout=True)
    for axis,factor in zip(ax.flat,FIELDS):
        sc=axis.scatter([p[factor] for p in pairs],[p['relative_translation_error_m'] for p in pairs],
                        c=px,cmap='viridis',s=16)
        axis.set(xlabel=factor,ylabel='Local translation error (m)'); axis.grid(alpha=.2)
    fig.colorbar(sc,ax=list(ax.flat),label='Current frame stem',shrink=.7)
    save(fig,'factor_error_scatter.png')
    fig, ax = plt.subplots(1,2,figsize=(13,5),constrained_layout=True)
    ax[0].plot(positions[:,0],positions[:,2],color='red',label='Estimated')
    ax[0].plot(truth[:,0,3],truth[:,2,3],color='black',label='GT')
    for stem in [1,49,71,104,116,133,147,151,191]:
        i=x.index(stem); ax[0].annotate(str(stem),(positions[i,0],positions[i,2]),fontsize=8)
    ax[0].axis('equal'); ax[0].legend(); ax[0].set(xlabel='First camera X (m)',ylabel='First camera Z (m)')
    ax[1].plot(x,[r['valid_depth_fraction'] for r in rows],label='Valid depth fraction')
    ax[1].plot(x,[r['point_yield']/262144 for r in rows],label='Voxel count / image pixels (not coverage)')
    ax[1].legend(); ax[1].grid(alpha=.2); ax[1].set_xlabel('Frame stem')
    save(fig,'trajectory_and_depth.png')
    # 同一公尺色階，零深度以黑色顯示；影格只用於診斷插圖，不產生選取清單。
    import cv2
    groups = [[1,20,48,49,52,55,56], [70,71,90,103,104,105,114,116,117,133],
              [134,140,145,146,147,148,149,150,151,152],
              [p['current'] for p in sorted(pairs,key=lambda p:p['relative_translation_error_m'],reverse=True)[:6]]]
    cmap=plt.get_cmap('magma').copy(); cmap.set_bad('black')
    for j,group in enumerate(groups,1):
        fig,ax=plt.subplots(len(group),2,figsize=(9,len(group)*2.7),constrained_layout=True)
        for axes,stem in zip(ax,group):
            rgb=cv2.imread(str(DATA/'rgb'/f'{stem}.png'))[:,:,::-1]
            d=cv2.imread(str(DATA/'depth'/f'{stem}.png'),cv2.IMREAD_UNCHANGED)/1000
            axes[0].imshow(rgb); axes[0].set_title(f'RGB {stem}; L2={rows[x.index(stem)]["l2_m"]:.3f} m')
            im=axes[1].imshow(np.ma.masked_where(d<=0,d),vmin=0,vmax=10,cmap=cmap)
            axes[1].set_title(f'Depth {stem}; valid={np.mean(d>0):.1%}')
            for axis in axes: axis.axis('off')
        fig.colorbar(im,ax=list(ax[:,1]),label='Depth (m); black = zero; display capped at 10 m',shrink=.5)
        save(fig,f'rgb_depth_{j:02d}.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    sub.add_parser('capture').add_argument('--output', required=True)
    a = sub.add_parser('analyze')
    a.add_argument('--run', required=True)
    a.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.mode == 'capture':
        capture(args.output)
    else:
        analyze(args.run, args.output)
