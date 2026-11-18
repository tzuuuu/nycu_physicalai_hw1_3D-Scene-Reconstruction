"""唯讀驗證官方 Baseline Turtle，另存診斷摘要；不更動實驗檔案。"""
import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import utils
import api
import numpy as np


def summarize_rows(rows):
    output = {}
    for name in sorted({row['factor'] for row in rows}):
        items = [row for row in rows if row['factor'] == name]
        values = np.array([row['value'] for row in items], float)
        if not np.isfinite(values).all():
            raise ValueError(f'Non-finite recorded factor: {name}')
        output[name] = {'count': len(items), 'min': float(values.min()), 'max': float(values.max()),
                        'mean': float(values.mean()), 'median': float(np.median(values)),
                        'min_frames': [row['current'] for row in items if row['value'] == values.min()],
                        'max_frames': [row['current'] for row in items if row['value'] == values.max()]}
    return output


def validate(path, record_root, prefix_root):
    path, record_root, prefix_root = Path(path), Path(record_root), Path(prefix_root)
    before = path.read_bytes()
    experiment = api.read_experiment(str(path))  # 會解析 Turtle 並驗證宣告 seal。
    assert experiment['complete'] and experiment['completion']['expected'] == 1522
    assert experiment['completion']['measured'] == 1522
    assert len(experiment['frame_indices']) == 191
    declaration, _ = api._split_sections(before.decode('utf-8'))
    assert declaration.encode() == (record_root / 'declaration.before_run.ttl').read_bytes()
    config = json.loads((record_root / 'config.before_run.json').read_text())
    assert hashlib.sha256(declaration.encode()).hexdigest() == config['declaration_sha256_before_run']
    graph, exp = experiment['graph'], experiment['exp_iri']
    image_indices = {}
    for frame in graph.objects(experiment['batch_iri'], api.HW1.hasFrame):
        index = int(graph.value(frame, api.HW1.frameIndex))
        for relation in [api.HW1.hasRGBImage, api.HW1.hasDepthImage]:
            image_indices[graph.value(frame, relation)] = index
    rows = []
    for node in graph.subjects(api.HW1.inExperiment, exp):
        previous = graph.value(node, api.HW1.hasPrevious)
        row = {'factor': api._local(graph.value(node, api.HW1.hasDefinition)),
               'previous': image_indices[previous] if previous else None,
               'current': image_indices[graph.value(node, api.HW1.hasCurrentFrame)],
               'value': float(graph.value(node, api.HW1.value))}
        assert graph.value(node, api.HW1.evaluationState) == api.HW1.Measured
        rows.append(row)
    rows.sort(key=lambda row: (row['current'], row['factor']))
    summary = summarize_rows(rows)
    for name, count in experiment['factor_counts'].items():
        assert count == (191 if name in ['RawPointCount', 'VoxelizedPointYield'] else 190)
    runs = list(graph.objects(exp, api.HW1.hasRun))
    assert len(runs) == 1
    baseline = runs[0]
    assert str(baseline).endswith('/run/baseline')
    assert graph.value(baseline, api.HW1.selectionMode) == api.HW1.FullBatch
    assert int(graph.value(baseline, api.HW1.runFrameCount)) == 191
    stored_l2 = float(graph.value(baseline, api.HW1.mapMeanL2))
    assert math.isfinite(stored_l2)
    console = (record_root / 'baseline_command/console.log').read_text()
    match = re.search(r'Mean L2 distance: (\S+) meters  \(over (\d+) frames, (\d+) reconstructed\)', console)
    assert match and match.groups()[1:] == ('191', '191')
    exact = re.search(r'Mean L2 Distance = (\S+) \(stored as', console)
    assert exact and stored_l2 == api._storable(float(exact[1]))
    # 首 20 幀正式因素與既有 Preflight 比對，依官方儲存精度檢查。
    events = [json.loads(line) for line in (prefix_root / 'events.jsonl').read_text().splitlines()]
    lookup = {(r['factor'], r['previous'], r['current']): r['value'] for r in rows}
    mapping = {'raw_point_count': 'RawPointCount', 'point_yield': 'VoxelizedPointYield',
               'coarse_fitness': 'CoarseRANSACFitness', 'coarse_rmse': 'CoarseRANSACRMSE',
               'coarse_correspondences': 'CoarseRANSACCorrespondences', 'icp_fitness': 'ICPInlierFitness',
               'icp_rmse': 'ICPInlierRMSE', 'icp_correspondences': 'ICPInlierCorrespondences'}
    prefix_count = 0
    for event in events:
        for field, name in mapping.items():
            if field in event:
                assert lookup[name, event.get('prev_stem'), event['stem']] == api._storable(event[field])
                prefix_count += 1
    assert prefix_count == 154
    result = {'valid_turtle': True, 'seal_valid': True, 'declaration_unchanged': True,
              'frames': 191, 'evaluated_frames': 191, 'retained_fraction': 1.0,
              'factor_occurrences': len(rows), 'factor_summary': summary, 'baseline_run_exists': True,
              'selected_run_exists': False, 'mean_l2_raw_m': float(exact[1]), 'mean_l2_stored_m': stored_l2,
              'prefix_factor_comparison_count': prefix_count, 'prefix_matches_at_official_precision': True,
              'turtle_sha256': hashlib.sha256(before).hexdigest()}
    with (record_root / 'factor_occurrences.csv').open('x', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=['factor', 'previous', 'current', 'value'])
        writer.writeheader(); writer.writerows(rows)
    (record_root / 'validation.json').write_text(json.dumps(result, indent=2))
    assert path.read_bytes() == before
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment', required=True)
    parser.add_argument('--record-root', required=True)
    parser.add_argument('--prefix-root', required=True)
    args = parser.parse_args()
    result = validate(args.experiment, args.record_root, args.prefix_root)
    print(json.dumps({k: v for k, v in result.items() if k != 'factor_summary'}, indent=2))
