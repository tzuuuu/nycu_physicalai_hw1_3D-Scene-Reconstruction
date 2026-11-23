"""Read-only source/capture audit and isolated SOURCE check (not a final ZIP).

Writes only reports/final_zh and an automatically removed /tmp directory.
Does not invoke reconstruction on the official captures or install packages.
"""
import ast
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.final_report import ROOT,OUT,sha,write,read,truth
import cv2
import numpy as np


def main():
    captures=[]
    for folder,n in [('first_floor',191),('second_floor/114753116/P2_A_01',320)]:
        p=ROOT/'eval/_data'/folder
        rgb={int(f.stem):f for f in (p/'rgb').glob('*.png')}
        depth={int(f.stem):f for f in (p/'depth').glob('*.png')}
        assert sorted(rgb)==sorted(depth)==list(range(1,n+1))
        invalid=[]
        for i in range(1,n+1):
            color=cv2.imread(str(rgb[i]),cv2.IMREAD_UNCHANGED)
            d=cv2.imread(str(depth[i]),cv2.IMREAD_UNCHANGED)
            assert color.shape==(512,512,3) and color.dtype==np.uint8
            assert d.shape==(512,512) and d.dtype==np.uint16
            invalid.append(float(np.mean(d==0)))
        gt=np.load(p/'GT_pose.npy',allow_pickle=False)
        assert gt.shape==(n,7) and np.isfinite(gt).all()
        assert np.max(np.abs(np.linalg.norm(gt[:,3:],axis=1)-1))<1e-5
        intr=read(p/'intrinsics.json');assert intr['width']==intr['height']==512 and intr['hfov']==90
        frozen=read(ROOT/'research_outputs/m5_bonus_01/protected.before.json')
        science=[*rgb.values(),*depth.values(),p/'GT_pose.npy',p/'intrinsics.json']
        assert all(sha(f)==frozen[str(f.relative_to(ROOT))] for f in science)
        captures.append(dict(capture=str(p.relative_to(ROOT)),rgb=n,depth=n,scientific_files=len(science),
            decoded=True,historical_sha_match=True,intrinsics=intr,GT_dtype=str(gt.dtype),
            invalid_depth_fraction=dict(median=float(np.median(invalid)),p95=float(np.percentile(invalid,95)),maximum=max(invalid)),
            GT_centre_chord_sum_m=float(np.linalg.norm(np.diff(gt[:,:3].astype(float),axis=0),axis=1).sum())))
    source=['load.py','reconstruct.py','utils.py','api.py','plot.py','pixi.toml','pixi.lock','ontology/hw1.ttl','configs/second_floor.yaml']
    source += [str(p.relative_to(ROOT)) for p in (ROOT/'packages/simulator').rglob('*') if p.is_file()
        and '__pycache__' not in p.parts and '.egg-info' not in str(p) and '/tests/' not in str(p)]
    source += [str(p.relative_to(ROOT)) for p in (ROOT/'dependencies/habitat-lab/habitat-lab').rglob('*') if p.is_file()
        and '__pycache__' not in p.parts and '.egg-info' not in str(p)]
    source += ['dependencies/habitat-lab/LICENSE']
    tests=['tests/'+name for name in ['test_depth_unprojection.py','test_point_cloud_preprocessing.py','test_registration.py',
        'test_capture_inputs.py','test_reconstruction.py','test_trajectory_evaluation.py','test_cli_down_voxel.py','test_custom_icp.py']]
    support=set()
    pending=[ROOT/name for name in tests]
    while pending:
        f=pending.pop()
        for node in ast.walk(ast.parse(f.read_text())):
            names=[]
            if isinstance(node,ast.ImportFrom) and node.module:
                if node.module=='scripts':names=[alias.name for alias in node.names]
                elif node.module.startswith('scripts.'):names=[node.module.split('.')[1]]
            if isinstance(node,ast.Import):names += [a.name.split('.')[1] for a in node.names if a.name.startswith('scripts.')]
            for name in names:
                rel='scripts/'+name+'.py'
                if (ROOT/rel).is_file() and rel not in support:
                    support.add(rel);pending.append(ROOT/rel)
    docs=['docs/'+name+'.md' for name in ['pixi','load','reconstruct','api','e2e-workflow','plot','utils','factors','triplestore']]
    source=sorted(set(source))
    function_map={}
    for name in ['utils.py','reconstruct.py','api.py','load.py','plot.py']:
        function_map[name]=[dict(name=n.name,line=n.lineno,end=n.end_lineno) for n in ast.parse((ROOT/name).read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
    isolated={}
    with tempfile.TemporaryDirectory(prefix='hw1-source-review-') as td:
        dest=Path(td)
        for name in source+tests+sorted(support)+['conftest.py']:
            target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MPLCONFIGDIR='/tmp/hw1-final-source-mpl',
                 PYTHONPATH=os.pathsep.join([str(dest),str(dest/'packages/simulator'),str(dest/'dependencies/habitat-lab/habitat-lab')]))
        code="import json,api,utils,plot,simulator,habitat; print(json.dumps({'factors':len(api.load_quality_factors()),'simulator_source':simulator.__file__,'habitat_source':habitat.__file__}))"
        commands=[('import',[sys.executable,'-c',code]),('load_help',[sys.executable,'load.py','--help']),
            ('reconstruct_help',[sys.executable,'reconstruct.py','--help']),('api_help',[sys.executable,'api.py','--help']),
            ('portable_core_tests',[sys.executable,'-m','pytest','-q','-p','no:cacheprovider',*tests,
                '-k','not test_original_open3d_function_is_byte_for_byte_preserved'])]
        for label,cmd in commands:
            result=subprocess.run(cmd,cwd=dest,env=env,capture_output=True,text=True,timeout=120)
            isolated[label]=dict(returncode=result.returncode,command=cmd,stdout=result.stdout,stderr=result.stderr)
            if result.returncode:
                receipt=OUT/'audit/source_isolation_failure.json'
                if not receipt.exists():write(receipt,dict(checks=isolated,captures=captures,temporary_source_paths=source+tests+sorted(support)))
            assert result.returncode==0,(label,result.stdout,result.stderr)
        paths=json.loads(isolated['import']['stdout'].strip().splitlines()[-1])
        assert str(dest) in paths['simulator_source'] and str(dest) in paths['habitat_source']
    versions={name:metadata.version(name) for name in ['numpy','open3d','scipy','opencv-python','rdflib','matplotlib','Pillow','panel','bokeh','habitat-lab']}
    git={label:subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip() for label,args in [
        ('HEAD',['rev-parse','HEAD']),('snapshot',['rev-parse','snapshot/pre-implementation']),('status',['status','--short'])]}
    write(OUT/'audit/source_and_capture_audit.json',dict(captures=captures,function_map=function_map,versions=versions,
        git=git,isolated_source_checks=isolated,linux_clean_install_tested=False,
        code_findings=[
            'pixi test task refers to three absent tests; use explicit python -m pytest commands.',
            'test_custom_icp original-function preservation case needs git HEAD; isolated portable subset deselects only that provenance check.',
            'Sealed runs require --write to save outcomes, but may write PNG even without --write.',
            'Selected segments are flattened; gaps create new pair registrations, not independent submaps.',
            'Original snapshot comments still say point-to-plane for Bonus; actual custom implementation is Point-to-Point, permitted by PDF 3.5.',
            'Pixi uses local editable simulator and Habitat-Lab paths; package must retain them.',
            'Current Bonus source changes are not all committed; Git HEAD alone does not identify the submitted source.'],
        official_capture_reconstruction_executed=False))
    write(OUT/'submission_source_plan.json',dict(required_explicit=['load.py','reconstruct.py','utils.py','api.py','ontology/hw1.ttl','README.md','report.pdf'],
        required_runtime_sources={p:sha(ROOT/p) for p in source},recommended_portable_tests=tests,conftest='conftest.py',
        recommended_test_support_sources={p:sha(ROOT/p) for p in sorted(support)},
        recommended_docs=docs,query_sources=[
            dict(source='experiments/p1_baseline_20261118_map005_s0_01/queries/exploratory_ablation_exclude_104.rq',destination='queries/phase1_exclude_104.rq'),
            dict(source='docs/implementation/m43/p2b_sparse.rq',destination='queries/phase2_sparse.rq'),
            dict(source='docs/implementation/m43/selection_rule.json',destination='queries/phase2_selection_rule.json')],
        phase1_query_hardcodes_experiment='p1_baseline_20261118_map005_s0_01',phase2_query_hardcodes_experiment='p2_114753116_a01_baseline_01',
        exclude=['experiments/**/*.ttl','research_outputs/**','eval/_data/**','replica_v1/**','.pixi/**','.git/**','**/__pycache__/**','**/.DS_Store','reports/**/figures/**','*.zip'],
        report_and_readme_pending_user_review=True,zip_created=False))
    print('Capture decode + source checks passed; portable tests:',isolated['portable_core_tests']['stdout'].strip().splitlines()[-1])


if __name__=='__main__':main()
