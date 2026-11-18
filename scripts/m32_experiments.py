"""M3.2 固定七條件：官方入口、同次唯讀觀測與獨立封存。"""
import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import resource
import runpy
import shutil
import subprocess
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import m3_diagnose as m
from scripts.m31_ablation import ReturnObserver, snapshot
from scripts.m31_analysis import cumulative, read_jsonl
from scripts.validate_baseline import summarize_rows
import numpy as np

ROOT, DATA = m.ROOT, m.DATA
CONDITIONS = [('B0', .05, 0), ('B1', .03, 0), ('B2', .08, 0),
              ('C1', .05, 1), ('C2', .05, 2), ('C3', .05, 3), ('C4', .05, 4)]
CORE = ['utils.py', 'reconstruct.py', 'api.py', 'ontology/hw1.ttl', 'load.py',
        'plot.py', 'pixi.toml', 'pixi.lock']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def verify_hashes(hashes):
    changed = [name for name, value in hashes.items()
               if not (ROOT/name).is_file() or sha(ROOT/name) != value]
    if changed:
        raise RuntimeError('Protected files changed: ' + repr(changed))
    return len(hashes)


def validate_frames(data):
    for modality in ['rgb', 'depth']:
        stems = sorted(int(p.stem) for p in (Path(data)/modality).glob('*.png'))
        if stems != list(range(1, 192)):
            raise ValueError('Expected exact original 191 RGB/depth stems: ' + modality)
    # 僅讀npy標頭驗證shape，不把GT陣列載入配準或前置程式。
    with (Path(data)/'GT_pose.npy').open('rb') as f:
        version = np.lib.format.read_magic(f)
        shape, _, _ = np.lib.format._read_array_header(f, version)
    if shape != (191, 7):
        raise ValueError('GT header must report (191,7)')


def validate_condition(condition, voxel, seed):
    if (condition, voxel, seed) not in CONDITIONS:
        raise ValueError('Condition outside the seven authorized settings')


def run_logged(argv, directory, label):
    directory = Path(directory)
    started = time.perf_counter()
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    (directory/(label+'.stdout.log')).write_text(proc.stdout)
    (directory/(label+'.stderr.log')).write_text(proc.stderr)
    m.dump(directory/(label+'.json'), {'argv': argv, 'exit_code': proc.returncode,
                                      'elapsed_s': time.perf_counter()-started})
    if proc.returncode:
        raise RuntimeError('Official CLI failed: ' + label)
    return proc.stdout


def suite_prepare(output):
    output = m.fresh_output(output)
    config = read(m.BASE/'config.before_run.json')
    validate_frames(DATA)
    if m.capture_digest() != config['capture_sha256']:
        raise RuntimeError('Capture differs from M2')
    for name in CORE:
        original = subprocess.check_output(['git', 'show', config['git_commit']+':'+name], cwd=ROOT)
        if original != (ROOT/name).read_bytes():
            raise RuntimeError('Core differs from M2: '+name)
    versions = {name: importlib.metadata.version(name) for name in config['versions']}
    if versions != config['versions'] or os.environ.get('OMP_NUM_THREADS') != '1':
        raise RuntimeError('Version/thread control mismatch')
    protected = [p for root in [ROOT/'research_outputs', ROOT/'experiments', DATA]
                 for p in root.rglob('*') if p.is_file() and output not in p.parents]
    protected += [ROOT/name for name in CORE]
    m.dump(output/'protected.before.json', m.fingerprint(protected))
    shutil.copytree(m.EXP, output/'official_before')
    m.dump(output/'original_experiment.json', snapshot(m.EXP/(m.EXP.name+'.ttl')))
    free = shutil.disk_usage(ROOT).free
    if free < 2*2**30:
        raise RuntimeError('Less than 2 GiB remaining; stop without deleting evidence')
    items = []
    for condition, voxel, seed in CONDITIONS:
        suffix = 'c_v005_s%d' % seed
        # 與既定命名一致：005代表0.05，003代表0.03，008代表0.08。
        if condition.startswith('B'):
            suffix = { 'B0':'b_v005_s0', 'B1':'b_v003_s0', 'B2':'b_v008_s0'}[condition]
        name = 'p1_m32_20261118_'+suffix+'_01'
        exp = ROOT/'experiments'/name
        out = ROOT/'research_outputs'/('m32_'+name)
        if exp.exists() or out.exists():
            raise FileExistsError('Refuse existing condition workspace: '+name)
        items.append({'condition': condition, 'voxel': voxel, 'seed': seed,
                      'name': name, 'experiment': str(exp), 'output': str(out)})
    m.dump(output/'suite.json', {'kind':'M3.2 preregistered seven full-batch conditions',
        'conditions':items, 'capture_sha256':config['capture_sha256'],
        'versions':versions, 'algorithm_control':config['algorithm'],
        'core_sha256':m.fingerprint([ROOT/p for p in CORE]),
        'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'OMP_NUM_THREADS':os.environ['OMP_NUM_THREADS'], 'disk_free_bytes':free,
        'rss_limit_gib':3, 'seed_zero_shared_between_B_and_C':True,
        'GT_selection':'offline diagnosis informed hypothesis; never choose minimum-GT seed',
        'stop':'Any registration, resource or integrity failure stops subsequent conditions; no retries.'})
    print(json.dumps({'prepared':str(output),'conditions':7,'disk_free_bytes':free},indent=2))


def resume_authorization(suite):
    """保留原停止檔，以另存的明確恢復授權銜接；失敗後不得自動再恢復。"""
    suite = Path(suite)
    if (suite/'resume_failed.json').exists():
        raise RuntimeError('Resumed suite failed; stop without retry')
    auth_path = suite/'resume_authorization.json'
    if not auth_path.is_file():
        raise RuntimeError('Suite explicitly stopped; further execution needs user acceptance')
    auth = read(auth_path)
    if (auth['user_instruction'] != '核准繼續，恢復後置作業與剩餘六組'
            or auth['remaining_conditions'] != ['B1','B2','C1','C2','C3','C4']
            or auth['original_stop_sha256'] != sha(suite/'suite_stopped.json')
            or auth['original_suite_sha256'] != sha(suite/'suite.json')):
        raise RuntimeError('Resume authorization does not match stopped suite')
    return auth


def evidence_directory(suite, item):
    suite = Path(suite)
    if item['condition']=='B0' and (suite/'resume_authorization.json').is_file():
        return Path(resume_authorization(suite)['B0_postprocess_output'])
    return Path(item['output'])


def condition_prepare(suite, condition):
    suite = Path(suite)
    if (suite/'suite_stopped.json').exists():
        resume_authorization(suite)
        if condition=='B0':
            raise RuntimeError('B0 reconstruction must never be repeated')
    plan = read(suite/'suite.json')
    item = next(i for i in plan['conditions'] if i['condition']==condition)
    index = plan['conditions'].index(item)
    for previous in plan['conditions'][:index]:
        check = read(evidence_directory(suite,previous)/'integrity.after.json')
        if not check['passed']:
            raise RuntimeError('Prior condition did not pass')
    if index and not read(evidence_directory(suite,plan['conditions'][0])/'historical_comparison.json')['matched']:
        raise RuntimeError('B0 has not matched M2')
    verify_hashes(read(suite/'protected.before.json'))
    verify_hashes(plan['core_sha256'])
    if m.capture_digest()!=plan['capture_sha256']:
        raise RuntimeError('Capture changed')
    validate_condition(condition,item['voxel'],item['seed'])
    exp, output = Path(item['experiment']), Path(item['output'])
    if exp.exists() or output.exists():
        raise FileExistsError('Refuse workspace overwrite')
    output.mkdir()
    # 保存此次之前的全部成果，後續條件也保護已完成的新結果。
    protected = [p for root in [ROOT/'research_outputs', ROOT/'experiments', DATA]
                 for p in root.rglob('*') if p.is_file() and output not in p.parents]
    protected += [ROOT/name for name in CORE]
    m.dump(output/'protected.before.json', m.fingerprint(protected))
    algorithm = dict(plan['algorithm_control'])
    v = item['voxel']
    algorithm.update(registration_voxel_m=v, seed=item['seed'],normal_radius_m=2*v,
                     fpfh_radius_m=5*v,ransac_distance_m=1.5*v,icp_distance_m=1.5*v)
    hypothesis = ('Scale alters geometric support and matching tolerances jointly; finer can preserve edges '
                  'but amplify perturbations; coarser can supply context but erase distinguishing structure.'
                  if condition.startswith('B') else
                  'Fixed-scale seeds probe sampling stability; lower GT error does not define a general seed strategy.')
    manifest = dict(item, algorithm=algorithm, versions=plan['versions'],
                    capture_sha256=plan['capture_sha256'],core_sha256=plan['core_sha256'],
                    git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                    original_suite_commit=plan['git_commit'],
                    recording_tool_sha256=sha(Path(__file__)), suite=str(suite.resolve()),
                    hypothesis=hypothesis,frames=list(range(1,192)),factor_count=1522,
                    prediction='Outcome unknown; pose flip may persist or move. All outcomes retained.',
                    official_entrypoint=[sys.executable,str(ROOT/'reconstruct.py')]+cli_args(exp,v,item['seed']),
                    OMP_NUM_THREADS='1',rss_limit_gib=3,registered_unix=time.time())
    m.dump(output/'preregistration.json', manifest)
    run_logged([sys.executable,str(ROOT/'api.py'),'declare','--name',item['name'],
                '--data-dir','eval/_data/first_floor','--floor','1'],output,'declare')
    ttl = exp/(item['name']+'.ttl')
    text = ttl.read_text().replace('TODO: one line naming the condition this experiment tests',
             'M3.2 '+condition+' fixed full-batch parameter intervention')
    text = text.replace('pipeline: TODO', 'pipeline: Measured support may change; all outcomes retained. Guidance:')
    text = text.replace('baseline: TODO', 'baseline: Unknown Mean L2; no improvement guaranteed. Guidance:')
    # 註解也納入官方declaration seal；不增設Ontology未宣告的Parameter。
    text = ('# M3.2 hypothesis: '+hypothesis+'\n# preregistration_sha256: '+sha(output/'preregistration.json')+
            '\n# Effective algorithm: '+json.dumps(algorithm,sort_keys=True)+'\n'+text)
    ttl.write_text(text)
    m.api.read_declaration(str(ttl))
    (output/'declaration.before.ttl').write_bytes(ttl.read_bytes())
    query = f'''PREFIX hw1: <http://taica.course/hw1/ontology#>
PREFIX exp: <http://taica.course/hw1/experiment/>
SELECT DISTINCT ?frameIndex WHERE {{
 exp:{item['name']} hw1:onBatch ?batch .
 ?batch hw1:hasFrame ?frame . ?frame hw1:frameIndex ?frameIndex .
}} ORDER BY ASC(?frameIndex)
'''
    (exp/'queries/audit.rq').write_text(query)
    print('Prepared '+condition+' '+str(ttl),flush=True)


def cli_args(experiment, voxel, seed):
    return ['--experiment',str(experiment),'--version','open3d','--voxel-size',str(voxel),
            '--seed',str(seed),'--down-voxel','0.05','--no-vis']


class Observer(ReturnObserver):
    """沿用已驗證的return觀測，另存完整位姿、配對標記與CPU時間。"""
    def __init__(self, output):
        super().__init__(output)
        self.global_code = m.utils._global_registration.__code__
        self.actual_pairs = []
        self.cpu_start = None

    def __call__(self, frame, event, value):
        if event=='call' and frame.f_code is self.codes['reconstruct']:
            self.cpu_start = resource.getrusage(resource.RUSAGE_SELF)
        if event=='call' and frame.f_code is self.global_code:
            parent = frame.f_back
            local = parent.f_locals
            self.actual_pairs.append({'previous':local['prev_stem'],'current':local['stem'],
                                      'voxel':frame.f_locals['voxel_size'],'seed':frame.f_locals['seed']})
            print('[M3.2 pair begin] %s->%s' % (local['prev_stem'],local['stem']),flush=True)
        super().__call__(frame,event,value)
        if event=='return' and frame.f_code is self.codes['reconstruct'] and value is not None:
            poses = cumulative(self.transforms)
            np.testing.assert_allclose(poses[:,:3,3],value[1],rtol=0,atol=1e-12)
            np.save(self.output/'camera_poses.npy',poses)
            cpu = resource.getrusage(resource.RUSAGE_SELF)
            m.dump(self.output/'reconstruction_cpu.json',{
                'user_s':cpu.ru_utime-self.cpu_start.ru_utime,
                'system_s':cpu.ru_stime-self.cpu_start.ru_stime})


def execute_cli(experiment, output, voxel, seed):
    """原生runpy入口；測試可用合成capture，正式路徑由observe加上嚴格護欄。"""
    output = Path(output)
    output.mkdir(exist_ok=False)
    if sys.getprofile() is not None:
        raise RuntimeError('Existing profiler; refusing replacement')
    observer = Observer(output)
    prior = sys.argv
    sys.argv = [str(ROOT/'reconstruct.py')]+cli_args(experiment,voxel,seed)
    started = resource.getrusage(resource.RUSAGE_SELF)
    status = 'failed'
    try:
        sys.setprofile(observer)
        runpy.run_path(str(ROOT/'reconstruct.py'),run_name='__main__')
        status = 'official_cli_returned'
    except BaseException:
        (output/'failure.traceback.txt').write_text(traceback.format_exc())
        raise
    finally:
        sys.setprofile(None)
        sys.argv = prior
        cpu = resource.getrusage(resource.RUSAGE_SELF)
        m.dump(output/'observer_summary.json',{'status':status,'reconstruct_calls':observer.calls,
            'frame_events':sum(e['kind']=='frame' for e in observer.events),
            'pair_events':len(observer.transforms),'reconstruction_s_with_observation':observer.elapsed,
            'return_observer_overhead_s':observer.overhead_s,
            'cpu_user_s':cpu.ru_utime-started.ru_utime,'cpu_system_s':cpu.ru_stime-started.ru_stime,
            'process_peak_rss_bytes':cpu.ru_maxrss if sys.platform=='darwin' else cpu.ru_maxrss*1024})
        m.dump(output/'actual_pairs.json',observer.actual_pairs)
    return observer


def observe(output):
    output = Path(output).resolve()
    p = read(output/'preregistration.json')
    validate_condition(p['condition'],p['voxel'],p['seed'])
    exp = Path(p['experiment']); ttl = exp/(exp.name+'.ttl')
    if ttl.read_bytes() != (output/'declaration.before.ttl').read_bytes() or m.api.is_assessed(str(ttl)):
        raise RuntimeError('Declaration changed/already sealed')
    if '# preregistration_sha256: '+sha(output/'preregistration.json') not in ttl.read_text():
        raise RuntimeError('Preregistration digest mismatch')
    verify_hashes(p['core_sha256']); verify_hashes(read(output/'protected.before.json'))
    if m.capture_digest()!=p['capture_sha256'] or os.environ.get('OMP_NUM_THREADS')!='1':
        raise RuntimeError('Input/environment changed')
    if {n:importlib.metadata.version(n) for n in p['versions']}!=p['versions']:
        raise RuntimeError('Software versions changed')
    # 獨占標記在任何重建前寫入，失敗也禁止相同條件重跑。
    m.dump(output/'execution.started.json',{'unix':time.time(),'argv':p['official_entrypoint']})
    obs = execute_cli(exp,output/'observation',p['voxel'],p['seed'])
    if obs.calls!=1 or len(obs.transforms)!=190 or len(obs.events)!=381:
        raise RuntimeError('Incomplete same-run evidence')
    if [(t['prev_stem'],t['stem']) for t in obs.transforms] != list(zip(range(1,191),range(2,192))):
        raise RuntimeError('Wrong actual pair identity')
    actual = read(output/'observation/actual_reconstruct_arguments.json')
    if (actual['voxel_size'],actual['registration_seed'],actual['down_voxel'],actual['version'],
            actual['build_cloud'],actual['frames']) != (p['voxel'],p['seed'],.05,'open3d',True,list(range(1,192))):
        raise RuntimeError('CLI effective arguments differ from preregistration')


def factor_rows(exp):
    graph, iri = exp['graph'], exp['exp_iri']
    images = {}
    for frame in graph.objects(exp['batch_iri'],m.api.HW1.hasFrame):
        images[graph.value(frame,m.api.HW1.hasDepthImage)] = int(graph.value(frame,m.api.HW1.frameIndex))
    rows = []
    for node in graph.subjects(m.api.HW1.inExperiment,iri):
        previous = graph.value(node,m.api.HW1.hasPrevious)
        if graph.value(node,m.api.HW1.evaluationState)!=m.api.HW1.Measured:
            raise RuntimeError('Unmeasured factor')
        rows.append({'factor':m.api._local(graph.value(node,m.api.HW1.hasDefinition)),
                     'previous':images[previous] if previous else None,
                     'current':images[graph.value(node,m.api.HW1.hasCurrentFrame)],
                     'value':float(graph.value(node,m.api.HW1.value))})
    return sorted(rows,key=lambda r:(r['current'],r['factor']))


def validate_evidence(ttl, output, expected_frames):
    """正式API資料與同次觀測交叉驗證；也用於合成CLI相容性測試。"""
    output = Path(output)
    exp = m.api.read_experiment(str(ttl))
    n = len(expected_frames)
    if not exp['complete'] or exp['frame_indices']!=expected_frames:
        raise RuntimeError('Incomplete/incorrect frame factors')
    if exp['completion']['measured']!=8*n-6:
        raise RuntimeError('Wrong factor count')
    rows = factor_rows(exp)
    events = read_jsonl(output/'events.jsonl')
    comparison = m.compare_factors(events,rows)
    if comparison['mismatch_count']:
        raise RuntimeError('Observed factors disagree with official TTL')
    runs = list(exp['graph'].objects(exp['exp_iri'],m.api.HW1.hasRun))
    run = m.api.data_run_iri(exp['exp_name'],'baseline')
    if runs!=[run] or exp['graph'].value(run,m.api.HW1.selectionMode)!=m.api.HW1.FullBatch:
        raise RuntimeError('Expected exactly one FullBatch baseline, no selected')
    if int(exp['graph'].value(run,m.api.HW1.runFrameCount))!=n:
        raise RuntimeError('Wrong run frame count')
    l2 = read(output/'official_evaluation.json')['mean_l2_raw_m']
    if float(exp['graph'].value(run,m.api.HW1.mapMeanL2))!=m.api._storable(l2):
        raise RuntimeError('Run/evaluation Mean L2 mismatch')
    declaration,_ = m.api._split_sections(Path(ttl).read_text())
    if declaration.encode() != (output.parent/'declaration.before.ttl').read_bytes():
        raise RuntimeError('Declaration bytes changed')
    poses = np.load(output/'camera_poses.npy')
    if poses.shape!=(n,4,4):
        raise RuntimeError('Wrong pose count')
    np.testing.assert_allclose(poses[:,:3,3],np.load(output/'positions.npy'),atol=1e-12,rtol=0)
    return exp, rows, l2


def historical_comparison(l2, historical, comparison, old_poses, new_poses):
    """將數值核對轉為可完整序列化的證據，不修改任何原始成果。"""
    pose_difference = float(np.max(np.abs(old_poses-new_poses)))
    return {'mean_l2_m':float(l2),'historical_mean_l2_m':float(historical),
            'difference_m':float(l2-historical),'factors':comparison,
            'diagnostic_pose_max_abs_difference':pose_difference,
            'matched':bool(abs(l2-historical)<=1e-10 and comparison['mismatch_count']==0
                           and pose_difference<=1e-10),
            'historical_pose_source':'M3.0 matched diagnostic, not original formal M2 poses'}


def finalize(output):
    output = Path(output).resolve(); p = read(output/'preregistration.json')
    execution = read(output/'command/execution.json')
    if execution['exit_code']!=0 or execution['resource_guard']['reason']:
        raise RuntimeError('Official reconstruction/resource monitor failed; stop')
    exp_path = Path(p['experiment']); ttl = exp_path/(exp_path.name+'.ttl')
    exp, rows, l2 = validate_evidence(ttl,output/'observation',list(range(1,192)))
    m.write_csv(output/'factor_occurrences.csv',rows)
    m.dump(output/'factor_summary.json',summarize_rows(rows))
    # B0的歷史門檻先檢查，避免任何後續重建。
    if p['condition']=='B0':
        with (m.BASE/'factor_occurrences.csv').open() as f:
            comparison = m.compare_factors(read_jsonl(output/'observation/events.jsonl'),list(csv.DictReader(f)))
        historical = read(m.BASE/'validation.json')['mean_l2_raw_m']
        old_poses = cumulative(read_jsonl(ROOT/'research_outputs/m3_20261118_diagnostic_02/transforms.jsonl'))
        new_poses = np.load(output/'observation/camera_poses.npy')
        result = historical_comparison(l2,historical,comparison,old_poses,new_poses)
        m.dump(output/'historical_comparison.json',result)
        if not result['matched']:
            raise RuntimeError('B0 differs from historical baseline; STOP')
    before = sha(ttl)
    run_logged([sys.executable,str(ROOT/'api.py'),'explore',str(exp_path)],output,'explore')
    stdout = run_logged([sys.executable,str(ROOT/'api.py'),'query',str(exp_path),'--query-file',
                         str(exp_path/'queries/audit.rq'),'--format','csv'],output,'query')
    frames = [int(r['frameIndex']) for r in csv.DictReader(io.StringIO(stdout))]
    if frames!=list(range(1,192)) or sha(ttl)!=before:
        raise RuntimeError('Official query/explore audit failed')
    plots = sorted(str(p.relative_to(exp_path)) for p in (exp_path/'plots').glob('*.html'))
    if len(plots)<4 or not (exp_path/'reconstruction_baseline.png').is_file():
        raise RuntimeError('Missing official plots/map')
    count = verify_hashes(read(output/'protected.before.json'))
    suite = Path(p['suite'])
    verify_hashes(read(suite/'protected.before.json'))
    if snapshot(m.EXP/(m.EXP.name+'.ttl')) != read(suite/'original_experiment.json'):
        raise RuntimeError('Original M2/M3.1 RDF changed')
    shutil.copytree(exp_path,output/'official_after')
    m.dump(output/'integrity.after.json',{'passed':True,'complete':exp['completion'],
        'frames':191,'pairs':190,'factor_count':len(rows),'same_run_factor_match':True,
        'seal_valid':True,'baseline_only':True,'retained_fraction':1.,'mean_l2_m':l2,
        'protected_files_unchanged':count,'plots':plots,'ttl_sha256':sha(ttl),
        'capture_sha256':m.capture_digest(),'git_commit':p['git_commit']})
    manifest = {str(f.relative_to(ROOT)):sha(f) for root in [output,exp_path]
                for f in root.rglob('*') if f.is_file()}
    m.dump(output/'artifacts_manifest.json',manifest)
    print(json.dumps(read(output/'integrity.after.json'),indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='mode',required=True)
    sub.add_parser('suite-prepare').add_argument('--output',required=True)
    prep=sub.add_parser('prepare'); prep.add_argument('--suite',required=True)
    prep.add_argument('--condition',choices=[c[0] for c in CONDITIONS],required=True)
    for mode in ['observe','finalize']:
        sub.add_parser(mode).add_argument('--output',required=True)
    args=parser.parse_args()
    try:
        if args.mode=='suite-prepare': suite_prepare(args.output)
        elif args.mode=='prepare': condition_prepare(args.suite,args.condition)
        elif args.mode=='observe': observe(args.output)
        else: finalize(args.output)
    except BaseException:
        # 原始traceback另存；失敗也不自動修復／重試配準。
        target = Path(args.output) if hasattr(args, 'output') else None
        if target is not None and target.is_dir() and not (target/'failure.traceback.txt').exists():
            (target/'failure.traceback.txt').write_text(traceback.format_exc())
        raise
