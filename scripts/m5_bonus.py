"""Four authorized custom-ICP runs; original Open3D code/results remain read-only.

Use prepare, then run (native process-table access needed), then analyze.
No automatic retries. Selected uses the new custom baseline's experiment and
the original frozen sparse-v1 indices, not new factor-based selection.
"""
import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('OMP_NUM_THREADS', '1')
import numpy as np
import utils
import api
from scripts.m42_monitor import write, append, run as guarded, process_table
from scripts.m42_observer import Observer as BaseObserver
from scripts.m4_capture_check import sha

OUT = ROOT/'research_outputs/m5_bonus_01'
P2 = ROOT/'eval/_data/second_floor/114753116/P2_A_01'
SPARSE = ROOT/'docs/implementation/m43/p2b_sparse.rq'
OLD_P2 = 'p2_114753116_a01_baseline_01'
NEW_P2 = 'bonus_f2_baseline_01'
CONDITIONS = {
    'f1_baseline': dict(capture='eval/_data/first_floor', n=191, seed=0,
                        experiment='bonus_f1_baseline_01', floor=1),
    'f1_c1': dict(capture='eval/_data/first_floor', n=191, seed=1,
                  experiment='bonus_f1_c1_01', floor=1),
    'f2_baseline': dict(capture=str(P2.relative_to(ROOT)), n=320, seed=0,
                        experiment=NEW_P2, floor=2),
    'f2_sparse': dict(capture=str(P2.relative_to(ROOT)), n=204, seed=0,
                      experiment=NEW_P2, floor=2),
}


def read(path):
    return json.loads(Path(path).read_text())


def lines(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines()]


def original_icp(text):
    node = next(n for n in ast.parse(text).body
                if isinstance(n, ast.FunctionDef) and n.name == 'local_icp_algorithm')
    return ''.join(text.splitlines(keepends=True)[node.lineno-1:node.end_lineno])


def sparse_frames():
    values = re.search(r'VALUES\s+\?frameIndex\s*\{([^}]+)\}', SPARSE.read_text()).group(1)
    result = [int(v) for v in values.split()]
    if len(result) != 204 or result != sorted(set(result)) or result[0] != 1:
        raise RuntimeError('Invalid frozen selection')
    return result


def expected_frames(key):
    return sparse_frames() if key == 'f2_sparse' else list(range(1, CONDITIONS[key]['n']+1))


def inventory(roots):
    result = {}
    for root in roots:
        for path in ([root] if root.is_file() else sorted(root.rglob('*'))):
            if path.is_symlink():
                raise RuntimeError('Protected input is a symlink: '+str(path))
            if path.is_file():
                result[str(path.relative_to(ROOT))] = sha(path)
    return result


def verify(items):
    for path, digest in items.items():
        if sha(ROOT/path) != digest:
            raise RuntimeError('Protected file changed: '+path)


def prepare():
    if OUT.exists():
        raise FileExistsError(OUT)
    if any((ROOT/'experiments'/c['experiment']).exists() for c in CONDITIONS.values()):
        raise FileExistsError('Bonus experiment already exists')
    if shutil.disk_usage(ROOT).free < 4*2**30:
        raise RuntimeError('Require 4 GiB disk space')
    old = subprocess.check_output(['git', 'show', 'HEAD:utils.py'], cwd=ROOT, text=True)
    original = original_icp(old)
    if original != original_icp((ROOT/'utils.py').read_text()):
        raise RuntimeError('Original Open3D function modified')
    for key, spec in CONDITIONS.items():
        _, pairs, _ = utils._capture_inputs(str(ROOT/spec['capture']), expected_frames(key))
        if len(pairs) != spec['n']:
            raise RuntimeError('Capture count mismatch')
    OUT.mkdir()
    (OUT/'original_local_icp_algorithm.txt').write_text(original)
    protected = inventory([ROOT/'eval/_data/first_floor', P2, ROOT/'experiments',
        ROOT/'docs/implementation/m43', ROOT/'ontology/hw1.ttl', ROOT/'pixi.toml', ROOT/'pixi.lock',
        ROOT/'research_outputs/phase1_report_assets',
        ROOT/'research_outputs/m32_p1_m32_20261118_c_v005_s1_01',
        ROOT/'research_outputs/m3_20261118_diagnostic_02',
        ROOT/'research_outputs/m42_p2_a01_baseline_01',
        ROOT/'research_outputs/m43_p2b_selected_01'])
    write(OUT/'protected.before.json', protected)
    sources = inventory([ROOT/'utils.py', ROOT/'reconstruct.py', Path(__file__),
                         ROOT/'scripts/m42_observer.py', ROOT/'scripts/m42_monitor.py'])
    write(OUT/'plan.json', dict(conditions=CONDITIONS, sparse_frames=sparse_frames(),
        sources=sources, original_icp_sha256=hashlib.sha256(original.encode()).hexdigest(),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        versions={k:importlib.metadata.version(k) for k in ['numpy','scipy','open3d','opencv-python','rdflib']},
        python=sys.version, OMP_NUM_THREADS=os.environ['OMP_NUM_THREADS'],
        registration_voxel_m=.05, map_voxel_m=.05, max_iterations=60,
        threshold_m=.075, convergence_mean_distance_change_m=1e-6, minimum_correspondences=10,
        hypothesis='Changing only ICP can alter drift and map artifacts. Improvement is not guaranteed.',
        selection='Frozen historical 204 indices, no reselection from custom factors.',
        timing='ICP Python call-to-return includes array validation, target tree, final metrics; '
               'reconstruct timer includes observer overhead but stops before map export; '
               'worker includes official evaluation, exports, PNG and Turtle. Historical times have different boundaries.',
        scope='Exactly four reconstructions; no additional Open3D or parameter/seed runs.',
        created_unix=time.time()))
    print('Prepared '+str(OUT), flush=True)


class Observer(BaseObserver):
    def __init__(self, output):
        super().__init__(output)
        # Reuse the read-only return observer without changing its Open3D code.
        self.codes['local_icp_algorithm'] = utils.my_local_icp_algorithm.__code__
        self.icp_start = None
        self.icp_times = []

    def __call__(self, frame, event, value):
        custom = frame.f_code is self.codes['local_icp_algorithm']
        if custom and event == 'call':
            self.icp_start = time.perf_counter()
        if custom and event == 'return' and value is not None:
            elapsed = time.perf_counter() - self.icp_start
            local = frame.f_back.f_locals
            row = dict(previous=local['prev_stem'], current=local['stem'], seconds=elapsed,
                       iterations=value.iterations, reason=value.termination_reason, success=value.success)
            self.icp_times.append(row)
            append(self.output/'icp_timing.jsonl', row)
        super().__call__(frame, event, value)


def declare(key, output):
    spec = CONDITIONS[key]
    experiment = ROOT/'experiments'/spec['experiment']
    if key == 'f2_sparse':
        exp = api.read_experiment(str(experiment/(experiment.name+'.ttl')))
        if exp['settings']['icpBackend'] != 'my_icp':
            raise RuntimeError('Selected requires new custom baseline')
        return experiment
    result = subprocess.run([sys.executable, str(ROOT/'api.py'), 'declare',
        '--name', spec['experiment'], '--data-dir', str(ROOT/spec['capture']), '--floor', str(spec['floor'])],
        capture_output=True, text=True, check=True)
    (output/'declare.log').write_text(result.stdout+result.stderr)
    ttl = experiment/(experiment.name+'.ttl')
    text = ttl.read_text().replace('TODO: one line naming the condition this experiment tests',
                                  'Bonus custom Point-to-Point ICP '+key)
    text = text.replace('pipeline: TODO', 'pipeline: Raw support may vary; no guaranteed improvement. Context:')
    text = text.replace('baseline: TODO', 'baseline: Unknown Mean L2; retain all outcomes. Context:')
    text = '# Effective voxel=0.05m, map voxel=0.05m, seed=%d; see M5 plan.json\n'%spec['seed']+text
    text += '''\nexp:%s hw1:hasFactorSetting [
 a hw1:FactorSetting ; hw1:settingParameter hw1:icpBackend ;
 hw1:settingRole hw1:ReconstructionSetting ; hw1:settingForFactor hw1:ReconstructionRun ;
 hw1:settingValue "my_icp"^^xsd:string ] .\n'''%spec['experiment']
    ttl.write_text(text)
    if api.read_declaration(str(ttl))['required']['icpBackend'] != 'my_icp':
        raise RuntimeError('Custom backend not declared')
    (output/'declaration.before.ttl').write_bytes(ttl.read_bytes())
    return experiment


def worker(key):
    spec = CONDITIONS[key]
    output = OUT/key
    output.mkdir(exist_ok=False)
    verify(read(OUT/'plan.json')['sources'])
    experiment = declare(key, output)
    obsdir = output/'observation'
    obsdir.mkdir()
    observer = Observer(obsdir)
    argv = [str(ROOT/'reconstruct.py'), '--experiment', str(experiment), '--version', 'my_icp',
            '--voxel-size', '.05', '--seed', str(spec['seed']), '--down-voxel', '.05', '--no-vis']
    if key == 'f2_sparse':
        query = SPARSE.read_text().replace('exp:'+OLD_P2, 'exp:'+NEW_P2)
        query_path = output/'frozen_sparse.rq'
        query_path.write_text(query)
        argv += ['--selection-query', str(query_path), '--write']
    write(output/'execution.started.json', dict(argv=argv, frames=expected_frames(key), unix=time.time()))
    if sys.getprofile() is not None:
        raise RuntimeError('Existing profiler')
    status = 'failed'
    prior = sys.argv
    try:
        sys.argv = argv
        sys.setprofile(observer)
        runpy.run_path(str(ROOT/'reconstruct.py'), run_name='__main__')
        status = 'completed'
    finally:
        sys.setprofile(None)
        sys.argv = prior
        write(obsdir/'observer_summary.json', dict(status=status, reconstruct_calls=observer.calls,
            reconstruction_s_with_observation=observer.elapsed,
            observer_overhead_s=observer.overhead_s, icp_total_s=sum(t['seconds'] for t in observer.icp_times),
            pairs=len(observer.transforms), frames=len(observer.poses)))
    actual = read(obsdir/'trajectory_metadata.json')['frame_indices']
    if actual != expected_frames(key) or len(observer.transforms) != spec['n']-1:
        raise RuntimeError('Unexpected frames/pairs')
    if not all(t['success'] for t in observer.icp_times):
        raise RuntimeError('ICP reported failure')
    ttl = experiment/(experiment.name+'.ttl')
    # Snapshot before later selected run adds a Run and refreshes the shared PNG.
    shutil.copyfile(ttl, output/'experiment.after.ttl')
    shutil.copyfile(experiment/'reconstruction.png', output/'reconstruction_native.png')
    exp = api.read_experiment(str(ttl))
    if not exp['complete'] or exp['settings']['icpBackend'] != 'my_icp':
        raise RuntimeError('Incomplete or wrong-backend Turtle')
    if key != 'f2_sparse':
        from scripts.m32_experiments import validate_evidence
        validate_evidence(ttl, obsdir, expected_frames(key))
    else:
        run = api.data_run_iri(exp['exp_name'], 'selected')
        if int(exp['graph'].value(run, api.HW1.runFrameCount)) != 204:
            raise RuntimeError('Wrong selected run count')
        # New Selected factors stay in same-run observer files; baseline factors are sealed.
        used = sorted(int(exp['graph'].value(f, api.HW1.frameIndex))
                      for f in exp['graph'].objects(run, api.HW1.usedFrame))
        if used != sparse_frames():
            raise RuntimeError('Wrong selected indices in Turtle')
    write(output/'accepted.json', dict(status='passed', frames=spec['n'], pairs=spec['n']-1,
        factor_observations=2*spec['n']+6*(spec['n']-1), seal_valid=True,
        mean_l2_m=read(obsdir/'official_evaluation.json')['mean_l2_raw_m']))


def run_suite():
    plan = read(OUT/'plan.json')
    verify(plan['sources'])
    verify(read(OUT/'protected.before.json'))
    process_table()  # Fail before launching any reconstruction if monitoring is unavailable.
    for key in CONDITIONS:
        if (OUT/key).exists() or (OUT/(key+'_monitor')).exists():
            raise FileExistsError('No automatic retries: '+key)
    results = {}
    for key in CONDITIONS:
        print('Starting '+key, flush=True)
        result = guarded([sys.executable, str(Path(__file__)), 'worker', '--condition', key],
                         OUT/(key+'_monitor'))
        results[key] = result
        if not result['passed'] or not (OUT/key/'accepted.json').exists():
            write(OUT/'suite.stopped.json', dict(condition=key, monitor=result))
            raise RuntimeError('Run not accepted: '+key)
        verify(plan['sources'])
        verify(read(OUT/'protected.before.json'))
        print('Accepted '+key, flush=True)
    write(OUT/'suite.accepted.json', dict(results=results, protected_unchanged=True,
        original_open3d_unchanged=original_icp((ROOT/'utils.py').read_text()) ==
                                  (OUT/'original_local_icp_algorithm.txt').read_text()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare','run','worker'])
    parser.add_argument('--condition', choices=list(CONDITIONS))
    args = parser.parse_args()
    if args.action == 'prepare': prepare()
    elif args.action == 'run': run_suite()
    else:
        if args.condition is None: parser.error('--condition required')
        worker(args.condition)
