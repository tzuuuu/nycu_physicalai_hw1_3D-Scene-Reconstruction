"""F1唯讀稽核；不呼叫Declare、Explore、Reconstruction或任何配準函式。"""
import ast
from collections import Counter
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tokenize

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from rdflib import Graph,RDF,RDFS,OWL
import api
from scripts import m32_experiments as x
from scripts import m3_diagnose as m
from scripts.m31_ablation import snapshot,verify_preservation
from scripts.m32_metadata_policy import metadata_policy,EXACT_PATHS


def dump(path,value):
    with Path(path).open('x') as f: json.dump(value,f,indent=2,ensure_ascii=False)


def run(output):
    output=Path(output).resolve(); output.mkdir(exist_ok=False)
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    old={ROOT/n for n in tracked if n and (ROOT/n).is_file()}
    old.update(p for base in [ROOT/'experiments',ROOT/'research_outputs',m.DATA] for p in base.rglob('*')
               if p.is_file() and output not in p.parents)
    dump(output/'protected.before.json',m.fingerprint(sorted(old)))
    suite=ROOT/'research_outputs/m32_20261118_suite_01'; final=suite/'resume_04'
    result={}
    with metadata_policy(output/'metadata_checks.jsonl'):
        result['prior_manifest_files']=x.verify_hashes(x.read(final/'final_manifest.json'))
        result['prior_protected_files']=x.verify_hashes(x.read(final/'protected.before.json'))
        result['capture_sha256']=m.capture_digest()
        plan=x.read(suite/'suite.json')
        if result['capture_sha256']!=plan['capture_sha256']:raise RuntimeError('Capture changed')
        x.validate_frames(m.DATA);x.verify_hashes(plan['core_sha256'])
        baseline_path=m.EXP/(m.EXP.name+'.ttl'); base=snapshot(baseline_path)
        before=x.read(ROOT/'research_outputs/m31_20261118_preparation_01/baseline.before.json')
        verify_preservation(before,base)
        if base!=x.read(suite/'original_experiment.json'):raise RuntimeError('M2/M3.1 workspace changed')
        result['baseline_snapshot']=base; result['baseline_before_selected']=before
        exp=api.read_experiment(str(baseline_path)); graph=exp['graph']
        selected=api.data_run_iri(exp['exp_name'],'selected')
        frames=sorted(int(graph.value(v,api.HW1.frameIndex)) for v in graph.objects(selected,api.HW1.usedFrame))
        if frames!=[i for i in range(1,192) if i!=104]:raise RuntimeError('Selected frame identity changed')
        if int(graph.value(selected,api.HW1.runFrameCount))!=190:raise RuntimeError('Selected count changed')
        result['selected_run']={'frames':frames,'mean_l2_stored_m':float(graph.value(selected,api.HW1.mapMeanL2))}
        conditions=[]; scoped=[]
        for item in plan['conditions']:
            c=item['condition']; out=Path(item['output']); path=Path(item['experiment'])/(item['name']+'.ttl')
            directory=final if c in ['C3','C4'] else suite/'resume_03' if c=='C2' else suite/'resume_02'
            receipt=x.read(directory/'status'/(c+'.json'));x.verify_hashes(receipt['evidence_sha256'])
            row={'condition':c,'status':receipt['status'],'ttl_sha256':x.sha(path),'workspace':item['experiment'],
                 'source':item['output'],'mean_l2_m':receipt['mean_l2_m']}
            if c=='B1':
                if api.is_assessed(str(path)) or path.read_bytes()!=(out/'declaration.before.ttl').read_bytes():
                    raise RuntimeError('B1 unsealed declaration changed')
                row.update(seal_valid=False,unsealed_registration_failure=True)
            else:
                official,rows,l2=x.validate_evidence(path,out/'observation',list(range(1,192)))
                occurrences={str(n) for n in official['graph'].subjects(api.HW1.inExperiment,official['exp_iri'])}
                scoped.append(occurrences)
                row.update(seal_valid=True,factors=len(rows),factor_counts=dict(Counter(v['factor'] for v in rows)),
                           frames=official['frame_indices'],mean_l2_m=l2)
            conditions.append(row)
        if any(a&b for i,a in enumerate(scoped) for b in scoped[i+1:]):raise RuntimeError('Shared factor occurrences')
        result['conditions']=conditions; result['factor_occurrences_disjoint']=True
        result['seed0_reuses_B0']=plan['seed_zero_shared_between_B_and_C']
        # 最新全目錄SHA包含M3.0、M3.1及所有歷史停止，不回頭把舊預期Selected異動判錯。
        result['historical_stop_paths']=[str(p.relative_to(ROOT)) for p in (ROOT/'research_outputs').rglob('*')
            if p.is_file() and ('stopped' in p.name or 'traceback' in p.name or 'authorization' in p.name)]
        snapshot_ref='snapshot/pre-implementation'
        code={}
        for name in x.CORE:
            original=subprocess.check_output(['git','show',snapshot_ref+':'+name],cwd=ROOT)
            current=(ROOT/name).read_bytes()
            code[name]={'snapshot_sha256':hashlib.sha256(original).hexdigest(),'current_sha256':x.sha(ROOT/name),
                        'identical_to_snapshot':original==current}
            if name=='utils.py':
                comments=lambda s:[t.string for t in tokenize.generate_tokens(io.StringIO(s).readline) if t.type==tokenize.COMMENT]
                old_comments=comments(original.decode());new_comments=iter(comments(current.decode()))
                code[name]['all_original_comments_preserved_in_order']=all(any(v==c for v in new_comments) for c in old_comments)
                functions={n.name:n for n in ast.walk(ast.parse(current)) if isinstance(n,ast.FunctionDef)}
                code[name]['NotImplemented_functions']=[n.name for n in functions.values() if any(isinstance(v,ast.Raise)
                    and isinstance(v.exc,ast.Call) and getattr(v.exc.func,'id',None)=='NotImplementedError' for v in ast.walk(n))]
                if code[name]['NotImplemented_functions']!=['my_local_icp_algorithm']:raise RuntimeError('Required TODO missing')
        result['code_vs_snapshot']=code
        g=Graph().parse(ROOT/'ontology/hw1.ttl',format='turtle')
        definitions=api.load_quality_factors(); parameters=api.load_parameter_declarations()
        required=set(api.PIPELINE_FACTORS)
        if set(definitions)!=required:raise RuntimeError('Quality factor definitions differ')
        result['ontology']={'triples':len(g),'classes':sorted({str(v).split('#')[-1] for t in [RDFS.Class,OWL.Class] for v in g.subjects(RDF.type,t)}),
            'properties':sorted({str(v).split('#')[-1] for t in [RDF.Property,OWL.ObjectProperty,OWL.DatatypeProperty] for v in g.subjects(RDF.type,t)}),
            'quality_factors':definitions,'parameters':list(parameters),'sha256':x.sha(ROOT/'ontology/hw1.ttl'),
            'identical_to_snapshot':code['ontology/hw1.ttl']['identical_to_snapshot']}
        imports={}
        for file in ['load.py','reconstruct.py','utils.py','api.py','plot.py']+[
            str(p.relative_to(ROOT)) for p in (ROOT/'packages/simulator/simulator').glob('*.py')]:
            tree=ast.parse((ROOT/file).read_text())
            imports[file]=sorted({v.name.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.Import) for v in n.names}|
                                {n.module or '<relative>' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)})
        result['imports']=imports
        env=os.environ.copy();env.pop('PYTHONPATH',None);env['OMP_NUM_THREADS']='1';env['MPLCONFIGDIR']='/tmp/phase1-closeout-mpl'
        with tempfile.TemporaryDirectory(prefix='phase1-minimal-submission-') as tmp:
            folder=Path(tmp);(folder/'ontology').mkdir()
            for name in ['load.py','reconstruct.py','utils.py','api.py','ontology/hw1.ttl']:shutil.copyfile(ROOT/name,folder/name)
            checks={}
            for label,argv in [('reconstruct_help',[sys.executable,'reconstruct.py','--help']),
                               ('load_help',[sys.executable,'load.py','--help']),
                               ('minimal_plot_import',[sys.executable,'-c','import plot'])]:
                p=subprocess.run(argv,cwd=folder,env=env,capture_output=True,text=True)
                checks[label]={'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
            if checks['minimal_plot_import']['exit_code']==0:raise RuntimeError('Minimal dependency probe leaked repository')
            shutil.copyfile(ROOT/'plot.py',folder/'plot.py')
            p=subprocess.run([sys.executable,'-c','import api,utils,plot; print(len(api.load_quality_factors()))'],cwd=folder,env=env,capture_output=True,text=True)
            checks['with_plot_import']={'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
            if p.returncode or checks['reconstruct_help']['exit_code'] or checks['load_help']['exit_code']:raise RuntimeError('Small import smoke failed')
            result['minimal_source_smokes']=checks
        result['scientific_integrity_verified']=True
        result['metadata_exclusion']=list(EXACT_PATHS)
        result['preserved_existing_files']=x.verify_hashes(x.read(output/'protected.before.json'))
    dump(output/'F1_audit.json',result)
    print(json.dumps({k:result[k] for k in ['scientific_integrity_verified','preserved_existing_files','factor_occurrences_disjoint']},indent=2))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.output)
