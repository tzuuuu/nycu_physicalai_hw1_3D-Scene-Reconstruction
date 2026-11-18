"""M3.2 離線配對方向、旋轉角度與seed描述統計。"""
import numpy as np
import pytest
from scipy.spatial.transform import Rotation
from scripts.m32_analysis import metrics, severe, describe


def test_known_local_and_global_errors_no_alignment_fit():
    truth=np.repeat(np.eye(4)[None],3,axis=0)
    truth[1,0,3]=1; truth[2,0,3]=2
    t1=np.eye(4); t1[0,3]=1
    t2=np.eye(4); t2[:3,:3]=Rotation.from_euler('z',179,degrees=True).as_matrix(); t2[0,3]=1.5
    poses=np.array([np.eye(4),t1,t1@t2])
    transforms=[{'prev_stem':1,'stem':2,'trans_init':t1,'icp_transformation':t1},
                {'prev_stem':2,'stem':3,'trans_init':t2,'icp_transformation':t2}]
    fs,ps=metrics(poses,truth,transforms)
    assert [f['l2_m'] for f in fs]==[0,0,.5]
    assert ps[1]['relative_rotation_error_deg']==pytest.approx(179)
    assert ps[1]['relative_translation_error_m']==pytest.approx(.5)
    assert severe(ps,'coarse_rotation_error_deg',150)==[3]
    assert fs[-1]['orientation_error_deg']==pytest.approx(179)
    assert sum(f['l2_m'] for f in fs)/3==pytest.approx(1/6)


def test_seed_statistics_uses_sample_std_and_all_outcomes():
    d=describe([1,2,3,4,10])
    assert d['count']==5 and d['mean_m']==4 and d['median_m']==3
    assert d['sample_std_m']==pytest.approx(np.std([1,2,3,4,10],ddof=1))
    assert d['min_m']==1 and d['max_m']==10 and d['range_m']==9


def test_reject_wrong_local_identity():
    poses=np.repeat(np.eye(4)[None],2,axis=0)
    with pytest.raises(ValueError,match='pair identity'):
        metrics(poses,poses,[{'prev_stem':1,'stem':3}])


def test_single_success_std_is_undefined_not_nan():
    import json
    d=describe([3.])
    assert d['sample_std_m'] is None
    json.dumps(d,allow_nan=False)


def test_comparison_keeps_failed_condition_without_mean_l2(tmp_path,monkeypatch):
    import csv,json
    from scripts import m32_analysis as a
    suite=tmp_path/'suite'; suite.mkdir(); (suite/'resume_02').mkdir()
    (suite/'resume_02/authorization.json').write_text('{}')
    items=[]
    for key,mean in [('B0',1.),('B1',None),('B2',3.)]:
        out=tmp_path/key; out.mkdir(); items.append({'condition':key,'voxel':.03 if key=='B1' else .05,'seed':0,'output':str(out)})
        if mean is None:
            (out/'command').mkdir(); (out/'command/execution.json').write_text(json.dumps({'total_process_s':2.,'child_peak_rss_bytes':1000}))
            continue
        target=out/'analysis'; target.mkdir(); obs=out/'observation'; obs.mkdir()
        pair={k:.1 for k in ['coarse_rotation_error_deg','relative_rotation_error_deg','coarse_translation_error_m','relative_translation_error_m']}
        summary={'condition':key,'voxel_m':.05,'seed':0,'mean_l2_m':mean,'pair103_104':pair,
                 'severe_coarse_gt150_current_frames':[],'severe_icp_gt150_current_frames':[],
                 'total_process_s':3.,'reconstruction_s':2.,'cpu_user_s':1.,'cpu_system_s':.1,'peak_rss_bytes':1000}
        (target/'summary.json').write_text(json.dumps(summary))
        a.m.write_csv(target/'frames.csv',[{'frame':i,'l2_m':mean,'orientation_error_deg':0.,'pred_x_m':i/100,'pred_z_m':0.,'gt_x_m':i/100,'gt_z_m':0.} for i in range(1,192)])
        a.m.write_csv(target/'pairs.csv',[dict(current=i,**pair) for i in range(2,192)])
        (obs/'events.jsonl').write_text('\n'.join(json.dumps(dict(stem=i,**{k:1 for k in a.m.FIELDS})) for i in range(1,192)))
        np.savez(obs/'map_sample.npz',points=np.array([[0,0,0],[2,1,2]]))
    (suite/'suite.json').write_text(json.dumps({'conditions':items}))
    monkeypatch.setattr(a.x,'terminal_receipt',lambda _,k: {'status':'Failed Registration' if k=='B1' else 'Success','failure':{'previous':70,'current':71,'accepted_pairs':69}})
    monkeypatch.setattr(a.m,'ROOT',tmp_path)
    target=tmp_path/'comparison'; a.compare(suite,'B',target)
    result=json.loads((target/'comparison.json').read_text())
    assert result['planned_count']==3 and result['successful_full191_count']==2
    assert result['mean_l2_distribution']['mean_m']==2.
    with (target/'comparison.csv').open() as f: rows=list(csv.DictReader(f))
    assert [r['condition'] for r in rows]==['B0','B1','B2']
    assert rows[1]['mean_l2_m']=='' and rows[1]['status']=='Failed Registration'
