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
