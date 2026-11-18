"""系統停止後唯讀彙整M3.2已存在證據；不解除護欄、不重建。"""
import argparse
import csv
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import m32_experiments as x
from scripts import m32_analysis as analysis
from scripts import m3_diagnose as m
from scripts.m31_analysis import read_jsonl
import numpy as np


def differences(hashes):
    return [{'path':name,'before':digest,'after':x.sha(ROOT/name) if (ROOT/name).is_file() else None}
            for name,digest in hashes.items() if not (ROOT/name).is_file() or x.sha(ROOT/name)!=digest]


def review(suite,output):
    suite=Path(suite).resolve(); target=m.fresh_output(output)
    plan=x.read(suite/'suite.json')
    if x.read(suite/'resume_02/system_stopped.json')['condition']!='C2':
        raise RuntimeError('Unexpected stopped condition')
    inventories={}
    c2=next(i for i in plan['conditions'] if i['condition']=='C2')
    for label,path in [('initial',suite/'protected.before.json'),('resume02',suite/'resume_02/protected.before.json'),
                       ('C2',Path(c2['output'])/'protected.before.json')]:
        hashes=x.read(path); delta=differences(hashes)
        inventories[label]={'count':len(hashes),'unchanged':len(hashes)-len(delta),'differences':delta}
        # 僅離線說明已觸發的差異；不改驗證器、原SHA或鎖定狀態。
        if {d['path'] for d in delta}!={'experiments/.DS_Store'}:
            raise RuntimeError('Additional unexplained changes; stop review')
    x.verify_hashes(plan['core_sha256'])
    if m.capture_digest()!=plan['capture_sha256']: raise RuntimeError('Capture changed')
    shutil.copyfile(ROOT/'experiments/.DS_Store',target/'changed_experiments_DS_Store.bin')
    m.dump(target/'preservation_differences.json',inventories)
    # 前一個離線啟動因缺少父目錄，尚未寫出分析／讀GT即停止；保留啟動原因。
    (target/'offline_startup_note.txt').write_text('Prior standalone C2 analysis invocation failed at target.mkdir because this parent directory did not exist. No reconstruction, original artifact write, or GT analysis occurred; this review creates its independent parent before analysis.\n')
    analysis.analyze(c2['output'],target/'C2_analysis')
    statuses=[]; summaries={}; locations={}
    for item in plan['conditions']:
        key=item['condition']; out=Path(item['output'])
        if key in ['C3','C4']:
            if out.exists() or Path(item['experiment']).exists(): raise RuntimeError('Unexpected unstarted output')
            statuses.append(dict(item,status='Not Executed',mean_l2_m=None,failure=None))
        elif key=='B1':
            record=x.terminal_receipt(suite,key)
            statuses.append(dict(item,status='Failed Registration',mean_l2_m=None,failure=record['failure']))
        else:
            if key!='C2': x.terminal_receipt(suite,key)
            directory=target/'C2_analysis' if key=='C2' else out/'analysis'
            locations[key]=directory
            summary=x.read(directory/'summary.json'); summaries[key]=summary
            exp=Path(item['experiment'])
            x.validate_evidence(exp/(exp.name+'.ttl'),out/'observation',list(range(1,192)))
            statuses.append(dict(item,status='Success',mean_l2_m=summary['mean_l2_m'],failure=None,
                full_workflow_integrity_passed=key!='C2',system_integrity_stop=key=='C2'))
    m.dump(target/'summary.json',{'states':statuses,'successful_full191':len(summaries),'registration_failed':1,
        'not_executed':2,'formal_reconstruction_attempts':5,'B0_B1_repeated':False,'summaries':summaries,
        'system_guard_kept_stopped':True,'full_protection_sha_check_passed':False,
        'preservation':inventories,'capture_sha256':m.capture_digest(),
        'interpretation':'Success denotes completed formal reconstruction; C2 final all-file integrity check stopped at OS folder metadata.'})
    rows=[]
    for state in statuses:
        key=state['condition']; summary=summaries.get(key); p=summary['pair103_104'] if summary else {}
        execution=x.read(Path(state['output'])/'command/execution.json') if state['status']!='Not Executed' else {}
        rows.append({'condition':key,'status':state['status'],'voxel_m':state['voxel'],'seed':state['seed'],
            'mean_l2_m':state['mean_l2_m'],'failure':state['failure']['message'] if state['failure'] else None,
            'ransac103_rotation_deg':p.get('coarse_rotation_error_deg'),'icp103_rotation_deg':p.get('relative_rotation_error_deg'),
            'ransac103_translation_m':p.get('coarse_translation_error_m'),'icp103_translation_m':p.get('relative_translation_error_m'),
            'runtime_s':execution.get('total_process_s'),'rss_bytes':execution.get('child_peak_rss_bytes'),
            'workflow_integrity_passed':state.get('full_workflow_integrity_passed',False)})
    m.write_csv(target/'all_conditions.csv',rows)
    for group,keys in [('B',['B0','B1','B2']),('C',['B0','C1','C2','C3','C4'])]:
        known=[k for k in keys if k in summaries]
        group_summary={'planned_conditions':keys,'successes':known,'not_executed':[k for k in keys if k in ['C3','C4']],
            'failed_registration':[k for k in keys if k=='B1'],
            'mean_l2_success_only':analysis.describe([summaries[k]['mean_l2_m'] for k in known]),
            'C2_integrity_caveat':group=='C','not_a_full_five_seed_result':group=='C'}
        m.dump(target/(group+'_statistics.json'),group_summary)
        plots(target,group,known,summaries,locations,plan)
    m.dump(target/'manifest.json',m.fingerprint([p for p in target.rglob('*') if p.is_file()]))
    print(rows)


def plots(target,group,keys,summaries,locations,plan):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    colors=plt.get_cmap('tab10').colors
    fig,axes=plt.subplots(3,1,figsize=(12,10),constrained_layout=True)
    for j,key in enumerate(keys):
        fs=analysis.read_csv(locations[key]/'frames.csv'); ps=analysis.read_csv(locations[key]/'pairs.csv')
        axes[0].plot([r['frame'] for r in fs],[r['l2_m'] for r in fs],label=key,color=colors[j])
        axes[1].plot([r['current'] for r in ps],[r['coarse_rotation_error_deg'] for r in ps],label=key,color=colors[j])
        axes[2].plot([r['current'] for r in ps],[r['relative_rotation_error_deg'] for r in ps],label=key,color=colors[j])
    for ax,label in zip(axes,['191-frame L2 (m)','RANSAC local rotation error (deg)','ICP local rotation error (deg)']):
        ax.set_ylabel(label); ax.grid(alpha=.3); ax.axvline(104,c='gray',ls='--'); ax.legend()
    axes[-1].set_xlabel('Original frame')
    fig.suptitle(group+' completed reconstructions only; '+('B1 failed at 70->71' if group=='B' else 'seeds 3/4 not executed; C2 metadata integrity stop'))
    fig.savefig(target/(group+'_errors.png'),dpi=150); plt.close(fig)
    fig,axes=plt.subplots(1,len(keys),figsize=(6*len(keys),6),constrained_layout=True,squeeze=False)
    items={i['condition']:i for i in plan['conditions']}
    samples={k:np.load(Path(items[k]['output'])/'observation/map_sample.npz')['points'] for k in keys}
    bounds=np.concatenate(list(samples.values())); lo=bounds.min(axis=0); hi=bounds.max(axis=0)
    for ax,key in zip(axes[0],keys):
        points=samples[key]; fs=analysis.read_csv(locations[key]/'frames.csv')
        ax.scatter(points[::3,0],points[::3,2],s=.2,c='gray',alpha=.4)
        ax.plot([r['pred_x_m'] for r in fs],[r['pred_z_m'] for r in fs],c='red',lw=1,label='Estimated')
        ax.plot([r['gt_x_m'] for r in fs],[r['gt_z_m'] for r in fs],c='black',lw=1,label='GT')
        ax.set(xlim=(lo[0]-.5,hi[0]+.5),ylim=(lo[2]-.5,hi[2]+.5),xlabel='X (m)',ylabel='Z (m)',title=f'{key}: {summaries[key]["mean_l2_m"]:.6f} m')
        ax.set_aspect('equal'); ax.legend(fontsize=8)
    fig.suptitle(group+' actual map samples - common first-camera bounds')
    fig.savefig(target/(group+'_maps.png'),dpi=150); plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--suite',required=True); p.add_argument('--output',required=True)
    a=p.parse_args(); review(a.suite,a.output)
