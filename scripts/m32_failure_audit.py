"""唯讀保存M3.2恢復後的實際配準失敗，不重跑或修補正式成果。"""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import m32_experiments as x
from scripts import m3_diagnose as m
from scripts.m31_analysis import read_jsonl, cumulative
import numpy as np


def classify(transforms):
    accepted=[]; failed=[]
    for item in transforms:
        valid=all(item[prefix+'_correspondences']>0 and item[prefix+'_fitness']>0
                  and np.isfinite(item[prefix+'_fitness']) and np.isfinite(item[prefix+'_rmse'])
                  and np.isfinite(np.asarray(item[matrix])).all()
                  for prefix,matrix in [('coarse','trans_init'),('icp','icp_transformation')])
        if not valid:
            failed.append(item)
        elif failed:
            raise ValueError('A failed run cannot have later accepted pairs')
        else:
            accepted.append(item)
    return accepted,failed


def audit(suite,output):
    suite=Path(suite).resolve(); output=m.fresh_output(output)
    plan=x.read(suite/'suite.json')
    item=next(i for i in plan['conditions'] if i['condition']=='B1')
    source=Path(item['output']); exp=Path(item['experiment']); ttl=exp/(exp.name+'.ttl')
    stop=x.read(suite/'resume_failed.json')
    if stop['condition']!='B1': raise RuntimeError('Unexpected failure identity')
    original_protected=x.verify_hashes(x.read(suite/'protected.before.json'))
    b1_protected=x.verify_hashes(x.read(source/'protected.before.json'))
    resume_protected=x.verify_hashes(x.read(suite/'resume_01/protected.before.json'))
    if m.capture_digest()!=plan['capture_sha256']: raise RuntimeError('Capture changed')
    if x.m.api.is_assessed(str(ttl)) or ttl.read_bytes()!=(source/'declaration.before.ttl').read_bytes():
        raise RuntimeError('Failed condition must remain an unchanged unsealed declaration')
    transforms=read_jsonl(source/'observation/transforms.jsonl')
    events=read_jsonl(source/'observation/events.jsonl')
    accepted,failed=classify(transforms)
    if len(failed)!=1 or (failed[0]['prev_stem'],failed[0]['stem'])!=(70,71):
        raise RuntimeError('Unexpected actual failure point')
    frames=[e for e in events if e['kind']=='frame']
    if [e['stem'] for e in frames]!=list(range(1,72)):
        raise RuntimeError('Wrong partial frame identity')
    np.save(output/'offline_accepted_prefix_poses.npy',cumulative(accepted))
    factors=[{'factor':name,'previous':e.get('prev_stem'),'current':e['stem'],'value':e[field]}
             for e in events for field,name in m.FIELDS.items() if field in e]
    m.write_csv(output/'partial_observed_factors.csv',factors)
    m.dump(output/'failed_pair_result.json',failed[0])
    b0=plan['conditions'][0]
    reference={e['stem']:e for e in read_jsonl(Path(b0['output'])/'observation/events.jsonl') if e['kind']=='frame'}
    if not all(e['raw_point_count']==reference[e['stem']]['raw_point_count'] for e in frames):
        raise RuntimeError('Raw point counts changed')
    states=[]
    for i in plan['conditions']:
        path=Path(i['output'])
        states.append({'condition':i['condition'],'voxel_m':i['voxel'],'seed':i['seed'],
                       'status':'complete' if i['condition']=='B0' else 'registration_failed' if i['condition']=='B1' else 'not_started',
                       'reconstruction_started':(path/'execution.started.json').is_file()})
    if sum(i['reconstruction_started'] for i in states)!=2:
        raise RuntimeError('Unexpected extra reconstruction')
    summary={'states':states,'formal_reconstruction_attempts_total':2,'successful_full191_reconstructions':1,
        'B0_postprocess_passed':x.read(suite/'resume_01/B0_postprocess/integrity.after.json')['passed'],
        'B1_input_frames':191,'B1_preprocessed_frames':len(frames),'B1_observed_pairs':len(transforms),
        'B1_accepted_pairs_before_failure':len(accepted),'B1_accepted_prefix_frames':len(accepted)+1,
        'partial_factor_values':len(factors),'B1_full191_mean_l2_m':None,'B1_official_map_available':False,
        'B1_sealed':False,'B1_baseline_run_exists':False,'failure_pair':{'previous':70,'current':71},
        'failed_pair':failed[0], 'execution':x.read(source/'command/execution.json'),
        'observer':x.read(source/'observation/observer_summary.json'),
        'protected_counts':{'initial_suite':original_protected,'B1':b1_protected,'resume':resume_protected},
        'all_preexisting_evidence_unchanged':True,'capture_sha256':m.capture_digest(),
        'mean_registration_yield_ratio_on_observed71_frames':sum(e['point_yield'] for e in frames)/sum(reference[e['stem']]['point_yield'] for e in frames),
        'failed_pair_is_not_a_valid_pose':'ICP ran from returned RANSAC identity before core rejected coarse result; never accepted or accumulated.',
        'source_sha256':x.sha(Path(__file__))}
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(3,1,figsize=(12,9),constrained_layout=True)
    xx=[e['stem'] for e in frames]
    ax[0].plot(xx,[reference[i]['point_yield'] for i in xx],label='B0 v=0.05')
    ax[0].plot(xx,[e['point_yield'] for e in frames],label='B1 v=0.03 (partial)')
    ax[0].set_ylabel('Registration voxel point count'); ax[0].legend()
    for axis,key,label in [(ax[1],'coarse_fitness','RANSAC fitness'),(ax[2],'coarse_correspondences','RANSAC correspondences')]:
        axis.plot([e['stem'] for e in transforms],[e[key] for e in transforms]); axis.set_ylabel(label)
    for axis in ax: axis.axvline(71,c='red',ls='--'); axis.grid(alpha=.25); axis.set_xlabel('Current frame (B1 stopped at 71)')
    fig.suptitle('B1 registration failure: partial observations only; native thresholds differ')
    fig.savefig(output/'B1_partial_failure.png',dpi=150); plt.close(fig)
    m.dump(output/'summary.json',summary)
    m.dump(output/'manifest.json',m.fingerprint([p for p in output.rglob('*') if p.is_file()]))
    print({k:summary[k] for k in ['formal_reconstruction_attempts_total','B1_preprocessed_frames','B1_accepted_prefix_frames','partial_factor_values','protected_counts']})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--suite',required=True); p.add_argument('--output',required=True)
    a=p.parse_args(); audit(a.suite,a.output)
