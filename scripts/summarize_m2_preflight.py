"""整理既有 Preflight 證據；不執行重建、篩選或正式實驗。"""
import argparse
import json
from pathlib import Path


def summarize(root):
    root = Path(root)
    inventory = json.loads((root / 'inventory.json').read_text())
    runs = [json.loads(path.read_text()) for path in sorted(root.glob('frames_*/summary.json'))]
    estimates = []
    for run in runs:
        slope = (run['peak_rss_bytes'] - run['rss_at_start_bytes']) / run['raw_points_total']
        estimates.append({'preflight_frames': len(run['frames']),
                          'full_peak_GiB_estimate': (run['rss_at_start_bytes'] + slope * inventory['valid_points_total']) / 2**30,
                          'full_reconstruction_s_estimate': run['reconstruction_s'] / len(run['frames']) * inventory['rgb_count']})
    result = {'kind': 'preflight_analysis_not_formal_baseline', 'runs': runs,
              'full_batch_raw_points': inventory['valid_points_total'],
              'map_position_color_GiB_lower_bound': inventory['map_position_color_bytes'] / 2**30,
              'full_batch_estimates': estimates,
              'limitation': 'Extrapolation only; allocation, filtering, difficult pairs and rendering need not scale linearly.'}
    output = root / 'preflight_analysis.json'
    if output.exists():
        raise FileExistsError(output)
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


def plot_timelines(root):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root = Path(root)
    latest = sorted(root.glob('frames_*/summary.json'))[-1].parent
    events = [json.loads(line) for line in (latest / 'events.jsonl').read_text().splitlines()]
    specs = [('RawPointCount', 'frame', 'raw_point_count'),
             ('VoxelizedPointYield', 'frame', 'point_yield'),
             ('CoarseRANSACFitness', 'pair', 'coarse_fitness'),
             ('CoarseRANSACRMSE', 'pair', 'coarse_rmse'),
             ('CoarseRANSACCorrespondences', 'pair', 'coarse_correspondences'),
             ('ICPInlierFitness', 'pair', 'icp_fitness'),
             ('ICPInlierRMSE', 'pair', 'icp_rmse'),
             ('ICPInlierCorrespondences', 'pair', 'icp_correspondences')]
    fig, axes = plt.subplots(4, 2, figsize=(12, 12), constrained_layout=True)
    for ax, (label, kind, key) in zip(axes.flat, specs):
        rows = [event for event in events if event['kind'] == kind]
        ax.plot([r['stem'] for r in rows], [r[key] for r in rows], '.-')
        ax.set(title=label, xlabel='Current frame stem')
        ax.grid(alpha=0.3)
    fig.suptitle('M2.0 preflight only: first 20 frames; no quality thresholds')
    output = root / 'preflight_factors.png'
    if output.exists():
        raise FileExistsError(output)
    fig.savefig(output, dpi=140)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root')
    args = parser.parse_args()
    result = summarize(args.root)
    plot_timelines(args.root)
    print(json.dumps(result['full_batch_estimates'], indent=2))
