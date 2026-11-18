"""M2.0：只執行首段連續影格 Preflight；不建立實驗或 Turtle。"""
import argparse
import json
import platform
import resource
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import utils  # 先沿用 OpenMP 設定，再載入數值套件。
import api
import numpy as np
import open3d as o3d


def peak_rss_bytes():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == 'darwin' else value * 1024)


def factor_summary(frame, pair):
    records = {**frame, **pair}
    names = sorted({key[0] for key in records})
    return {name: {'count': len(values), 'min': min(values), 'max': max(values),
                   'mean': float(np.mean(values))}
            for name in names
            for values in [[float(record['value']) for key, record in records.items() if key[0] == name]]}


def run(data_root, output, frame_count, down_voxel=None):
    if frame_count < 2:
        raise ValueError('Preflight requires at least two frames')
    if down_voxel is not None and (not np.isfinite(down_voxel) or down_voxel <= 0):
        raise ValueError('down_voxel must be finite and positive')
    data_root = Path(data_root).resolve()
    output = Path(output).resolve()
    # 禁止輸出進入原始 capture，且不覆蓋任何既有執行目錄。
    if output == data_root or data_root in output.parents:
        raise ValueError('Preflight output must be outside the source capture')
    paired = api._pair_frames(str(data_root))
    if frame_count > len(paired):
        raise ValueError('Requested frame count exceeds capture')
    frames = [int(stem) for stem, _, _ in paired[:frame_count]]
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    callback, frame_records, pair_records = api.make_pipeline_measurement_callback(api.load_quality_factors())
    raw_points = 0
    diagnostics = []
    summary = {'kind': 'M2.0_preflight_not_formal_baseline',
               'started_utc': datetime.now(timezone.utc).isoformat(),
               'data_root': str(data_root), 'output': str(output), 'frames': frames,
               'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
               'parameters': {'version': 'open3d', 'voxel_size': 0.05,
                              'registration_seed': 0, 'build_cloud': True, 'down_voxel': down_voxel},
               'python': platform.python_version(), 'open3d': o3d.__version__,
               'numpy': np.__version__, 'rss_at_start_bytes': peak_rss_bytes()}
    log = (output / 'events.jsonl').open('x', encoding='utf-8')

    def record(kind, payload):
        nonlocal raw_points
        callback(kind, payload)
        if kind == 'frame':
            raw_points += payload['raw_point_count']
        event = {'kind': kind, 'elapsed_s': time.perf_counter() - started,
                 'peak_rss_bytes': peak_rss_bytes(), **payload}
        log.write(json.dumps(event) + '\n')
        log.flush()
        print(json.dumps(event), flush=True)

    def diagnostic(payload):
        item = {key: value.tolist() if isinstance(value, np.ndarray) else value
                for key, value in payload.items()}
        diagnostics.append(item)
        with (output / 'transforms.jsonl').open('a', encoding='utf-8') as fh:
            fh.write(json.dumps(item) + '\n')

    try:
        pcd, positions = utils.reconstruct(str(data_root), frames=frames,
                                           pipeline_callback=record, diagnostics_callback=diagnostic,
                                           **summary['parameters'])
        summary['reconstruction_s'] = time.perf_counter() - started
        # 必須在重建回傳後才進行 GT 評估。
        l2 = utils.visualize_and_evaluate(pcd, positions, str(data_root), frames=frames,
                                          show=False, title=f'M2.0 preflight {frame_count} frames',
                                          save_path=str(output / 'reconstruction.png'))
        if len(positions) != frame_count or len(frame_records) + len(pair_records) != 8 * frame_count - 6:
            raise RuntimeError('Incomplete preflight frames or factors')
        if not np.isfinite(l2):
            raise RuntimeError('Preflight trajectory cannot be evaluated')
        np.save(output / 'positions.npy', positions)
        summary.update(status='completed_requires_review', mean_l2_m=l2,
                       reconstructed_frames=len(positions), evaluated_frames=len(positions),
                       map_points=len(pcd.points), raw_points_total=raw_points,
                       map_axis_min=np.asarray(pcd.points).min(axis=0).tolist() if len(pcd.points) else None,
                       map_axis_max=np.asarray(pcd.points).max(axis=0).tolist() if len(pcd.points) else None)
    except Exception as exc:
        summary.update(status='failed', error_type=type(exc).__name__, error=str(exc))
        (output / 'traceback.txt').write_text(traceback.format_exc(), encoding='utf-8')
    finally:
        log.close()
        summary.update(total_s=time.perf_counter() - started, peak_rss_bytes=peak_rss_bytes(),
                       factor_summary=factor_summary(frame_records, pair_records),
                       frame_factor_count=len(frame_records), pair_factor_count=len(pair_records))
        (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
        print(json.dumps(summary, indent=2), flush=True)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--frames', required=True, type=int)
    parser.add_argument('--down-voxel', type=float, default=None)
    args = parser.parse_args()
    result = run(args.data_root, args.output, args.frames, down_voxel=args.down_voxel)
    raise SystemExit(0 if result['status'] == 'completed_requires_review' else 1)
