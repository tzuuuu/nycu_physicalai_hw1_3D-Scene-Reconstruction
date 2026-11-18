"""M3.1 單次 Exploratory Ablation：安全前置檢查與正式 CLI 唯讀觀測。"""
import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import m3_diagnose as m
import numpy as np
from rdflib import Graph
from rdflib.compare import to_canonical_graph

ROOT, DATA, EXP = m.ROOT, m.DATA, m.EXP
TTL = EXP / (EXP.name + '.ttl')
QUERY = EXP / 'queries/exploratory_ablation_exclude_104.rq'
FRAMES = [i for i in range(1, 192) if i != 104]
CLI_ARGS = ['--experiment', str(EXP), '--selection-query', str(QUERY),
            '--version', 'open3d', '--voxel-size', '0.05', '--seed', '0',
            '--down-voxel', '0.05', '--no-vis', '--write']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def graph_sha(graph):
    lines = sorted(' '.join(term.n3() for term in triple) + ' .' for triple in to_canonical_graph(graph))
    return sha('\n'.join(lines).encode())


def without_selected(graph, exp):
    selected = m.api.data_run_iri(m.api._experiment_name_from_iri(exp, 'snapshot'), 'selected')
    result = Graph()
    for s, p, o in graph:
        if s != selected and (s, p, o) != (exp, m.api.HW1.hasRun, selected):
            result.add((s, p, o))
    return result


def snapshot(path):
    raw = Path(path).read_bytes()
    exp = m.api.read_experiment(str(path))  # 會驗證Seal。
    declaration, _ = m.api._split_sections(raw.decode())
    graph, iri = exp['graph'], exp['exp_iri']
    baseline = m.api.data_run_iri(exp['exp_name'], 'baseline')
    baseline_graph = Graph()
    for triple in graph.triples((baseline, None, None)):
        baseline_graph.add(triple)
    baseline_graph.add((iri, m.api.HW1.hasRun, baseline))
    return {'turtle_sha256': sha(raw), 'declaration_sha256': sha(declaration.encode()),
            'seal': str(graph.value(iri, m.api.HW1.declarationDigest)), 'seal_valid': True,
            'complete': exp['complete'], 'measured_factors': exp['completion']['measured'],
            'baseline_run_sha256': graph_sha(baseline_graph),
            'baseline_mean_l2_stored_m': float(graph.value(baseline, m.api.HW1.mapMeanL2)),
            'baseline_frame_count': int(graph.value(baseline, m.api.HW1.runFrameCount)),
            'preserved_graph_sha256': graph_sha(without_selected(graph, iri)),
            'run_nodes': sorted(str(n) for n in graph.objects(iri, m.api.HW1.hasRun))}


def verify_preservation(before, after):
    for key in ['declaration_sha256', 'seal', 'baseline_run_sha256', 'preserved_graph_sha256',
                'baseline_mean_l2_stored_m', 'baseline_frame_count', 'measured_factors', 'complete']:
        if before[key] != after[key]:
            raise RuntimeError('Sealed baseline changed: ' + key)
    if not after['seal_valid'] or not after['complete']:
        raise RuntimeError('Invalid sealed baseline')


def verify_selection(frames):
    if frames != FRAMES:
        raise ValueError('Only ordered 1..191 excluding 104 is authorized')


def prepare(output):
    output = m.fresh_output(output)
    before = snapshot(TTL)
    if len(before['run_nodes']) != 1 or not before['run_nodes'][0].endswith('/baseline'):
        raise RuntimeError('Selected already exists; do not overwrite or rerun')
    if (EXP/'reconstruction_selected.png').exists():
        raise RuntimeError('Selected image already exists')
    if before['measured_factors'] != 1522 or before['baseline_frame_count'] != 191:
        raise RuntimeError('Wrong baseline identity')
    baseline_config = json.loads((m.BASE/'config.before_run.json').read_text())
    if m.capture_digest() != baseline_config['capture_sha256']:
        raise RuntimeError('Original capture changed')
    for name in ['utils.py','reconstruct.py','api.py','ontology/hw1.ttl','pixi.toml','pixi.lock']:
        original = subprocess.check_output(['git','show',baseline_config['git_commit']+':'+name],cwd=ROOT)
        if original != (ROOT/name).read_bytes():
            raise RuntimeError('Core differs from baseline: '+name)
    versions={name:importlib.metadata.version(name) for name in baseline_config['versions']}
    if versions != baseline_config['versions']:
        raise RuntimeError('Versions differ from baseline')
    # 原始完整TTL與所有官方舊檔案備份；不回寫、不重新封存。
    backup=output/'official_before'; backup.mkdir()
    for path in EXP.rglob('*'):
        if path.is_file():
            target=backup/path.relative_to(EXP); target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(path.read_bytes())
    protected=[p for root in [ROOT/'research_outputs',ROOT/'experiments',DATA]
               for p in root.rglob('*') if p.is_file() and output not in p.parents]
    protected += [ROOT/name for name in ['utils.py','reconstruct.py','api.py','ontology/hw1.ttl',
                                        'load.py','plot.py','pixi.toml','pixi.lock']]
    m.dump(output/'protected.before.json',m.fingerprint(protected))
    m.dump(output/'baseline.before.json',before)
    query_command=[sys.executable,str(ROOT/'api.py'),'query',str(EXP),'--query-file',str(QUERY),'--format','csv']
    process=subprocess.run(query_command,capture_output=True,text=True,cwd=ROOT)
    (output/'query.stdout.csv').write_text(process.stdout)
    (output/'query.stderr.log').write_text(process.stderr)
    if process.returncode:
        raise RuntimeError('Official query failed')
    frames=[int(r['frameIndex']) for r in csv.DictReader(io.StringIO(process.stdout))]
    verify_selection(frames)
    verify_selection(m.api.frames_from_sparql_query(m.api.read_experiment(str(TTL)),str(QUERY)))
    if TTL.read_bytes() != (backup/TTL.name).read_bytes():
        raise RuntimeError('Read-only query changed TTL')
    m.dump(output/'preregistration.json',{
        'kind':'Exploratory Ablation', 'selection_informed_by_gt_diagnosis':True,
        'hypothesis':'Excluding only 104 may avoid the pose flip; 103->105 may still fail.',
        'no_general_gt_independent_selection_rule_claimed':True,'frames':frames,
        'removed_frames':[104], 'retained_fraction':190/191,
        'query_command':query_command,'query_sha256':sha(QUERY.read_bytes()),
        'official_entrypoint':[sys.executable,str(ROOT/'reconstruct.py')]+CLI_ARGS,
        'observation':'sys.setprofile reads return values; no function replacement or input changes',
        'baseline_algorithm':baseline_config['algorithm'],'versions':versions,
        'capture_sha256':baseline_config['capture_sha256'],
        'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip(),
        'prepared_unix':time.time(), 'rss_limit_gib':3,
        'stop':'One selected reconstruction only; no repair, extra exclusion, parameter search or Phase 2.'})
    print(json.dumps({'selection_count':len(frames),'first':frames[0],'last':frames[-1],
                      'excluded':[104],'duplicates':len(frames)-len(set(frames)),
                      'baseline':before},indent=2))


class ReturnObserver:
    """只讀取正式函式的Python return事件；不改函式、參數或局部變數。"""
    def __init__(self, output):
        self.output=Path(output)
        self.events=[]; self.transforms=[]; self.calls=0; self.overhead_s=0.
        self.started=None; self.elapsed=None
        self.codes={name:getattr(m.utils,name).__code__ for name in
                    ['reconstruct','preprocess_point_cloud','local_icp_algorithm','visualize_and_evaluate']}

    def append(self,name,value):
        with (self.output/name).open('a') as f:
            f.write(json.dumps(value,allow_nan=False)+'\n')

    def __call__(self,frame,event,value):
        code=frame.f_code
        if event=='call' and code is self.codes['reconstruct']:
            self.calls+=1; self.started=time.perf_counter()
            values=frame.f_locals
            m.dump(self.output/'actual_reconstruct_arguments.json',
                   {k:values[k] for k in ['data_root','version','voxel_size','build_cloud','frames','down_voxel','registration_seed']})
        if event!='return':
            return
        start=time.perf_counter()
        parent=frame.f_back
        in_pipeline=parent is not None and parent.f_code is self.codes['reconstruct']
        if in_pipeline and code is self.codes['preprocess_point_cloud'] and value is not None:
            local=parent.f_locals
            record={'kind':'frame','stem':local['stem'],'raw_point_count':len(local['pcd'].points),
                    'point_yield':len(value[0].points)}
            self.events.append(record); self.append('events.jsonl',record)
        elif in_pipeline and code is self.codes['local_icp_algorithm'] and value is not None:
            local=parent.f_locals; coarse=local['coarse_result']
            record={'kind':'pair','prev_stem':local['prev_stem'],'stem':local['stem'],
                    'coarse_fitness':float(coarse.fitness),'coarse_rmse':float(coarse.inlier_rmse),
                    'coarse_correspondences':len(coarse.correspondence_set),
                    'icp_fitness':float(value.fitness),'icp_rmse':float(value.inlier_rmse),
                    'icp_correspondences':len(value.correspondence_set)}
            self.events.append(record); self.append('events.jsonl',record)
            transform={**record,'trans_init':np.array(local['trans_init']).tolist(),
                       'icp_transformation':np.array(value.transformation).tolist()}
            self.transforms.append(transform); self.append('transforms.jsonl',transform)
        elif code is self.codes['reconstruct'] and value is not None:
            self.elapsed=time.perf_counter()-self.started
            pcd,positions=value
            np.save(self.output/'positions.npy',positions)
            points=np.asarray(pcd.points); colors=np.asarray(pcd.colors)
            stride=max(1,int(np.ceil(len(points)/150000)))
            np.savez_compressed(self.output/'map_sample.npz',points=points[::stride],colors=colors[::stride])
            m.dump(self.output/'map_summary.json',{'ceiling_cropped_points':len(points),'sample_stride':stride,
                   'axis_min':points.min(axis=0).tolist() if len(points) else None,
                   'axis_max':points.max(axis=0).tolist() if len(points) else None})
        elif code is self.codes['visualize_and_evaluate'] and value is not None:
            m.dump(self.output/'official_evaluation.json',{'mean_l2_raw_m':float(value)})
        self.overhead_s+=time.perf_counter()-start


def observe(preparation, output):
    preparation=Path(preparation).resolve()
    prereg=json.loads((preparation/'preregistration.json').read_text())
    verify_selection(prereg['frames'])
    if sha(TTL.read_bytes()) != json.loads((preparation/'baseline.before.json').read_text())['turtle_sha256']:
        raise RuntimeError('Formal TTL changed since preparation')
    if sha(QUERY.read_bytes()) != prereg['query_sha256']:
        raise RuntimeError('Query changed since preparation')
    # x模式防止同一前置紀錄被再次用來重建；失敗也保留標記，不自動重試。
    m.dump(preparation/'selected_execution.started.json',{'started_unix':time.time(),'argv':CLI_ARGS})
    output=m.fresh_output(output)
    observer=ReturnObserver(output)
    if sys.getprofile() is not None:
        raise RuntimeError('Existing profiler; refusing to replace it')
    previous_argv=sys.argv
    sys.argv=[str(ROOT/'reconstruct.py')]+CLI_ARGS
    status='failed'
    try:
        sys.setprofile(observer)
        runpy.run_path(str(ROOT/'reconstruct.py'),run_name='__main__')
        status='official_cli_returned'
    except BaseException:
        (output/'failure.traceback.txt').write_text(traceback.format_exc())
        raise
    finally:
        sys.setprofile(None)
        sys.argv=previous_argv
        m.dump(output/'observer_summary.json',{'status':status,'reconstruct_calls':observer.calls,
               'frame_events':sum(e['kind']=='frame' for e in observer.events),
               'pair_events':len(observer.transforms),'reconstruction_s_with_observation':observer.elapsed,
               'python_return_observation_overhead_s':observer.overhead_s,
               'source_sha256':sha(Path(__file__).read_bytes()),
               'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip()})
    verify_preservation(json.loads((preparation/'baseline.before.json').read_text()),snapshot(TTL))
    if observer.calls!=1 or len(observer.transforms)!=189 or len(observer.events)!=379:
        raise RuntimeError('Incomplete selected evidence; do not rerun')
    if [(t['prev_stem'],t['stem']) for t in observer.transforms] != list(zip(FRAMES,FRAMES[1:])):
        raise RuntimeError('Wrong actual pair identity')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='mode',required=True)
    sub.add_parser('prepare').add_argument('--output',required=True)
    o=sub.add_parser('observe'); o.add_argument('--preparation',required=True); o.add_argument('--output',required=True)
    args=parser.parse_args()
    if args.mode=='prepare': prepare(args.output)
    else: observe(args.preparation,args.output)
