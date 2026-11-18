"""M3.2 重建後的離線誤差、八因素、地圖與B/C比較；不呼叫配準。"""
import argparse
import csv
import json
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import m32_experiments as x
from scripts import m3_diagnose as m
from scripts.m31_analysis import read_jsonl
import numpy as np


def metrics(poses,truth,transforms):
    if poses.shape!=truth.shape or len(poses)!=len(transforms)+1:
        raise ValueError('Pose/pair count mismatch')
    errors=np.linalg.norm(poses[:,:3,3]-truth[:,:3,3],axis=1)
    frames=[]
    for i in range(len(poses)):
        frames.append({'frame':i+1,'l2_m':float(errors[i]),
            'orientation_error_deg':m.angle(truth[i,:3,:3].T@poses[i,:3,:3]),
            'pred_x_m':float(poses[i,0,3]),'pred_y_m':float(poses[i,1,3]),'pred_z_m':float(poses[i,2,3]),
            'gt_x_m':float(truth[i,0,3]),'gt_y_m':float(truth[i,1,3]),'gt_z_m':float(truth[i,2,3])})
    pairs=[]
    for i,t in enumerate(transforms,1):
        if (t['prev_stem'],t['stem'])!=(i,i+1):
            raise ValueError('Unexpected pair identity')
        gt=np.linalg.inv(truth[i-1])@truth[i]
        p=m.pair_metrics(np.array(t['icp_transformation']),gt,np.array(t['trans_init']))
        p.update(previous=i,current=i+1)
        p.update({k:t[k] for k in m.FIELDS if k in t})
        pairs.append(p)
    return frames,pairs


def severe(pairs,key,threshold):
    return [p['current'] for p in pairs if p[key]>threshold]


def analyze(output, audit=None):
    output=Path(output).resolve()
    if audit is None:
        plan=x.read(output/'preregistration.json')
        check=x.read(x.evidence_directory(plan['suite'],plan)/'integrity.after.json')
        if not check['passed']:
            raise RuntimeError('Incomplete official run; no success analysis')
    else:
        # 停止後只讀同次正式證據；不修補、續跑或覆寫失敗的finalize目錄。
        plan=x.read(output/'preregistration.json')
        exp=Path(plan['experiment'])
        _,_,l2=x.validate_evidence(exp/(exp.name+'.ttl'),output/'observation',list(range(1,192)))
        check={'mean_l2_m':l2}
    target=Path(audit).resolve() if audit else output/'analysis'
    target.mkdir(exist_ok=False)
    started=time.perf_counter()
    plan=x.read(output/'preregistration.json')
    obs=output/'observation'
    poses=np.load(obs/'camera_poses.npy')
    # 正式CLI完整完成、Seal與因素驗證後才做GT離線分析。
    truth=m.gt_camera_poses(np.load(m.DATA/'GT_pose.npy'))
    frames,pairs=metrics(poses,truth,read_jsonl(obs/'transforms.jsonl'))
    mean=float(np.mean([f['l2_m'] for f in frames]))
    if abs(mean-check['mean_l2_m'])>1e-12:
        raise RuntimeError('Offline/official mean mismatch')
    m.write_csv(target/'frames.csv',frames); m.write_csv(target/'pairs.csv',pairs)
    np.savez_compressed(target/'poses_offline.npz',predicted=poses,gt=truth)
    execution=x.read(output/'command/execution.json')
    observation=x.read(obs/'observer_summary.json')
    summary={'condition':plan['condition'],'name':plan['name'],'voxel_m':plan['voxel'],'seed':plan['seed'],
        'n':191,'factor_count':1522,'mean_l2_m':mean,'retained_fraction':1.,
        'max_l2_m':max(f['l2_m'] for f in frames),
        'max_l2_frame':max(frames,key=lambda f:f['l2_m'])['frame'],
        'final_l2_m':frames[-1]['l2_m'],'final_orientation_error_deg':frames[-1]['orientation_error_deg'],
        'pair103_104':pairs[102],'pair104_105':pairs[103],
        'severe_coarse_gt150_current_frames':severe(pairs,'coarse_rotation_error_deg',150),
        'severe_icp_gt150_current_frames':severe(pairs,'relative_rotation_error_deg',150),
        'coarse_gt90_current_frames':severe(pairs,'coarse_rotation_error_deg',90),
        'icp_gt90_current_frames':severe(pairs,'relative_rotation_error_deg',90),
        'reconstruction_s':observation['reconstruction_s_with_observation'],
        'total_process_s':execution['total_process_s'],
        'peak_rss_bytes':execution['child_peak_rss_bytes'],
        'sampled_peak_rss_bytes':execution['resource_guard']['sampled_peak_rss_bytes'],
        'cpu_user_s':observation['cpu_user_s'],'cpu_system_s':observation['cpu_system_s'],
        'map':x.read(obs/'map_summary.json'),'factor_summary':x.read(output/'factor_summary.json'),
        'official_pipeline_evidence_validated':True,'full_workflow_complete':audit is None,
        'source_git_commit':plan['git_commit'],
        'analysis_script_sha256':x.sha(Path(__file__))}
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(3,1,figsize=(12,9),constrained_layout=True)
    for axis,key,label in zip(ax,['l2_m','orientation_error_deg','relative_rotation_error_deg'],
                              ['Frame L2 (m)','Global orientation error (deg)','Local rotation error (deg)']):
        values=frames if key!='relative_rotation_error_deg' else pairs
        axis.plot([f.get('frame',f.get('current')) for f in values],[f[key] for f in values])
        if key=='relative_rotation_error_deg':
            axis.plot([p['current'] for p in pairs],[p['coarse_rotation_error_deg'] for p in pairs],alpha=.7,label='RANSAC')
            axis.legend()
        axis.axvline(104,color='orange',alpha=.6); axis.grid(alpha=.25); axis.set_ylabel(label)
    ax[-1].set_xlabel('Current frame'); fig.suptitle(plan['condition']+' — fixed first-camera frame, 191 observations')
    fig.savefig(target/'frame_and_pair_errors.png',dpi=150); plt.close(fig)
    summary['analysis_s']=time.perf_counter()-started
    summary['output_bytes_before_summary']=sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
    m.dump(target/'summary.json',summary)
    m.dump(target/'manifest.json',{str(p.relative_to(m.ROOT)):x.sha(p) for p in target.rglob('*') if p.is_file()})
    print(json.dumps({k:summary[k] for k in ['condition','mean_l2_m','severe_coarse_gt150_current_frames',
          'severe_icp_gt150_current_frames','total_process_s','peak_rss_bytes']},indent=2))


def read_csv(path):
    with Path(path).open() as f:
        return [{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]


def describe(values):
    a=np.asarray(values,dtype=float)
    return {'count':len(a),'mean_m':float(a.mean()),'sample_std_m':float(a.std(ddof=1)) if len(a)>1 else None,
            'median_m':float(np.median(a)),'min_m':float(a.min()),'max_m':float(a.max()),
            'range_m':float(np.ptp(a))}


def compare(suite,group,output):
    suite=Path(suite); target=Path(output).resolve(); target.mkdir(exist_ok=False)
    plan=x.read(suite/'suite.json')
    desired=['B0','B1','B2'] if group=='B' else ['B0','C1','C2','C3','C4'] if group=='C' else [c[0] for c in x.CONDITIONS]
    all_items=[i for i in plan['conditions'] if i['condition'] in desired]
    statuses={i['condition']:x.terminal_receipt(suite,i['condition']) for i in all_items} if (suite/'resume_02/authorization.json').exists() else {}
    items=[i for i in all_items if not statuses or statuses[i['condition']]['status']=='Success']
    summaries=[x.read(Path(i['output'])/'analysis/summary.json') for i in items]
    frames=[read_csv(Path(i['output'])/'analysis/frames.csv') for i in items]
    pairs=[read_csv(Path(i['output'])/'analysis/pairs.csv') for i in items]
    rows=[]
    for s in summaries:
        p=s['pair103_104']
        rows.append({'condition':s['condition'],'status':'Success','failure_pair':None,'voxel_m':s['voxel_m'],'seed':s['seed'],'frames':191,
            'mean_l2_m':s['mean_l2_m'],'ransac103_104_rotation_deg':p['coarse_rotation_error_deg'],
            'icp103_104_rotation_deg':p['relative_rotation_error_deg'],
            'ransac103_104_translation_m':p['coarse_translation_error_m'],
            'icp103_104_translation_m':p['relative_translation_error_m'],
            'coarse_severe_count':len(s['severe_coarse_gt150_current_frames']),
            'icp_severe_count':len(s['severe_icp_gt150_current_frames']),
            'total_process_s':s['total_process_s'],'reconstruction_s':s['reconstruction_s'],
            'cpu_user_s':s['cpu_user_s'],'cpu_system_s':s['cpu_system_s'],
            'peak_rss_bytes':s['peak_rss_bytes'],'peak_rss_gib':s['peak_rss_bytes']/2**30})
    for item in all_items:
        if statuses and statuses[item['condition']]['status']=='Failed Registration':
            e=x.read(Path(item['output'])/'command/execution.json')
            failed={key:None for key in rows[0]}
            f=statuses[item['condition']]['failure']
            failed.update(condition=item['condition'],status='Failed Registration',failure_pair=str(f['previous'])+'->'+str(f['current']),voxel_m=item['voxel'],seed=item['seed'],frames=f['accepted_pairs']+1,total_process_s=e['total_process_s'],peak_rss_bytes=e['child_peak_rss_bytes'],peak_rss_gib=e['child_peak_rss_bytes']/2**30)
            rows.append(failed)
    rows.sort(key=lambda r:desired.index(r['condition']))
    m.write_csv(target/'comparison.csv',rows)
    result={'group':group,'runs':summaries,'mean_l2_distribution':describe([s['mean_l2_m'] for s in summaries]),
            'seed0_shared_B0':True,'statuses':{k:v['status'] for k,v in statuses.items()},
            'successful_full191_count':len(summaries),'planned_count':len(all_items),'completion_fraction':len(summaries)/len(all_items),
            'statistics_conditioned_on_complete_success':True,'analysis_script_sha256':x.sha(Path(__file__))}
    m.dump(target/'comparison.json',result)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    colors=plt.get_cmap('tab10').colors
    fig,ax=plt.subplots(3,1,figsize=(13,10),constrained_layout=True)
    for j,(s,fs) in enumerate(zip(summaries,frames)):
        label='%s v=%g seed=%d'%(s['condition'],s['voxel_m'],s['seed'])
        for a,key in zip(ax,['l2_m','l2_m','orientation_error_deg']):
            a.plot([f['frame'] for f in fs],[f[key] for f in fs],label=label,color=colors[j])
    ax[0].set_ylabel('Frame L2 (m)'); ax[1].set_yscale('symlog',linthresh=.01); ax[1].set_ylabel('L2 (m, symlog)')
    ax[2].set_ylabel('Global orientation error (deg)'); ax[2].set_xlabel('Frame')
    for a in ax: a.axvline(104,color='gray',alpha=.5); a.grid(alpha=.25)
    ax[0].legend(fontsize=8,ncol=2); fig.suptitle('M3.2 '+group+' — complete successes only; failures listed separately; no alignment fit')
    fig.savefig(target/'frame_errors.png',dpi=150); plt.close(fig)
    fig,ax=plt.subplots(2,2,figsize=(14,9),constrained_layout=True)
    keys=['coarse_rotation_error_deg','relative_rotation_error_deg','coarse_translation_error_m','relative_translation_error_m']
    for j,(s,ps) in enumerate(zip(summaries,pairs)):
        for a,key in zip(ax.flat,keys): a.plot([p['current'] for p in ps],[p[key] for p in ps],label=s['condition'],color=colors[j])
    for a,key in zip(ax.flat,keys):
        a.set(xlabel='Current frame',ylabel=key); a.grid(alpha=.25); a.legend(fontsize=8)
    fig.savefig(target/'local_errors.png',dpi=150); plt.close(fig)
    # 八因素原始序列按各次真正距離／點集呈現，不宣稱不同尺度Fitness可直接排名。
    fig,ax=plt.subplots(4,2,figsize=(15,14),constrained_layout=True)
    for j,(item,s) in enumerate(zip(items,summaries)):
        es=read_jsonl(Path(item['output'])/'observation/events.jsonl')
        for a,key in zip(ax.flat,m.FIELDS):
            values=[e for e in es if key in e]
            a.plot([e['stem'] for e in values],[e[key] for e in values],label=s['condition'],color=colors[j],alpha=.8)
    for a,key in zip(ax.flat,m.FIELDS):
        a.set(xlabel='Current frame',ylabel=key); a.grid(alpha=.2)
    ax[0,0].legend(fontsize=8,ncol=3); fig.suptitle('Pipeline factors — native per-run thresholds and point sets')
    fig.savefig(target/'eight_factors.png',dpi=150); plt.close(fig)
    # 同一座標範圍，使用正式地圖的固定上限取樣；不把點數當成覆蓋率。
    cloud_samples=[np.load(Path(i['output'])/'observation/map_sample.npz')['points'] for i in items]
    all_points=np.concatenate(cloud_samples)
    xmin,zmin=np.min(all_points[:,[0,2]],axis=0); xmax,zmax=np.max(all_points[:,[0,2]],axis=0)
    fig,ax=plt.subplots(2,4,figsize=(18,9),constrained_layout=True)
    for a,item,s,fs,points in zip(ax.flat,items,summaries,frames,cloud_samples):
        a.scatter(points[::3,0],points[::3,2],s=.12,c='gray',alpha=.4,rasterized=True)
        a.plot([f['pred_x_m'] for f in fs],[f['pred_z_m'] for f in fs],c='red',lw=1,label='Estimated')
        a.plot([f['gt_x_m'] for f in fs],[f['gt_z_m'] for f in fs],c='black',lw=1,label='GT')
        a.set(xlim=(xmin-1,xmax+1),ylim=(zmin-1,zmax+1),xlabel='X (m)',ylabel='Z (m)',
              title='%s: %.6f m'%(s['condition'],s['mean_l2_m'])); a.set_aspect('equal'); a.legend(fontsize=7)
    for a in list(ax.flat)[len(items):]: a.axis('off')
    fig.suptitle('Actual ceiling-cropped map samples — common first-camera bounds')
    fig.savefig(target/'map_trajectories.png',dpi=150); plt.close(fig)
    text='|條件|v (m)|seed|Mean L2 (m)|103→104 RANSAC誤差 (°)|ICP誤差 (°)|總秒數|峰值GiB|\n|---|---:|---:|---:|---:|---:|---:|---:|\n'
    for r in rows:
        if r['status']!='Success':
            text+='|{condition}|{voxel_m}|{seed}|Failed Registration ({failure_pair})|未到達|未到達|{total_process_s:.3f}|{peak_rss_gib:.4f}|\n'.format(**r)
            continue
        text+='|{condition}|{voxel_m}|{seed}|{mean_l2_m:.9f}|{ransac103_104_rotation_deg:.6f}|{icp103_104_rotation_deg:.6f}|{total_process_s:.3f}|{peak_rss_gib:.4f}|\n'.format(**r)
    (target/'comparison.md').write_text(text)
    m.dump(target/'manifest.json',{str(p.relative_to(m.ROOT)):x.sha(p) for p in target.rglob('*') if p.is_file()})
    print(text,flush=True)
    print(json.dumps(result['mean_l2_distribution'],indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='mode',required=True)
    a=sub.add_parser('analyze'); a.add_argument('--output',required=True); a.add_argument('--stopped-audit-output')
    c=sub.add_parser('compare'); c.add_argument('--suite',required=True); c.add_argument('--group',choices=['B','C','all'],required=True); c.add_argument('--output',required=True)
    args=p.parse_args()
    if args.mode=='analyze': analyze(args.output,args.stopped_audit_output)
    else: compare(args.suite,args.group,args.output)
