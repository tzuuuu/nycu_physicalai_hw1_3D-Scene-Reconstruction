"""診斷的座標方向、局部誤差、正式因素比較與不覆寫護欄。"""
import json
import numpy as np
import pytest
from scipy.spatial.transform import Rotation
from scripts import m3_diagnose as m


def test_gt_relative_motion_nontrivial_reference():
    rotation = Rotation.from_euler('xyz', [[23,41,13],[25,53,20]], degrees=True)
    gt = np.column_stack(([[7,2,-3],[8,4,-6]], rotation.as_quat()[:,[3,0,1,2]]))
    poses = m.gt_camera_poses(gt)
    np.testing.assert_allclose(poses[0], np.eye(4), atol=1e-14)
    axes = m.utils.CAM_TO_GT_AXES
    expected_translation = axes @ rotation[0].as_matrix().T @ (gt[1,:3]-gt[0,:3])
    np.testing.assert_allclose(poses[1,:3,3], expected_translation, atol=1e-14)
    expected_rotation = axes @ (rotation[0].inv()*rotation[1]).as_matrix() @ axes
    np.testing.assert_allclose(poses[1,:3,:3], expected_rotation, atol=1e-14)
    metrics = m.pair_metrics(poses[1], poses[1], poses[1])
    assert metrics['relative_translation_error_m'] == 0
    assert metrics['relative_rotation_error_deg'] < 1e-12


def test_known_translation_and_rotation_error():
    truth = np.eye(4)
    prediction = np.eye(4)
    prediction[:3,3] = [3,4,0]
    prediction[:3,:3] = Rotation.from_euler('y',30,degrees=True).as_matrix()
    metrics = m.pair_metrics(prediction,truth,truth)
    assert metrics['relative_translation_error_m'] == 5
    assert metrics['relative_rotation_error_deg'] == pytest.approx(30)
    assert metrics['icp_correction_translation_m'] == 5
    assert metrics['icp_correction_rotation_deg'] == pytest.approx(30)


def test_float32_gt_matches_official_evaluation_precision(tmp_path):
    gt = np.array([[3.141592,2.718281,-5.123456,1,0,0,0],
                   [4.234567,2.718282,-6.234567,1,0,0,0]], dtype=np.float32)
    np.save(tmp_path/'GT_pose.npy',gt)
    centres = m.gt_camera_poses(gt)[:,:3,3]
    assert m.utils.visualize_and_evaluate(None,centres,str(tmp_path),show=False) == 0


def test_factor_identity_precision_and_missing_detection():
    events = [{'kind':'pair','prev_stem':1,'stem':2,'icp_rmse':.0123456789}]
    rows = [{'factor':'ICPInlierRMSE','previous':'1','current':'2','value':m.api._storable(.0123456789)}]
    assert m.compare_factors(events,rows)['mismatch_count'] == 0
    assert m.compare_factors([],rows)['mismatch_count'] == 1
    events[0]['prev_stem'] = 3
    assert m.compare_factors(events,rows)['mismatch_count'] == 2
    with pytest.raises(ValueError,match='Duplicate'):
        m.compare_factors(events*2,rows)


def test_reject_existing_or_protected_output(tmp_path,monkeypatch):
    monkeypatch.setattr(m,'ROOT',tmp_path)
    with pytest.raises(ValueError):
        m.fresh_output(tmp_path/'experiments'/'bad')
    path=tmp_path/'research_outputs'/'new'
    assert m.fresh_output(path) == path
    with pytest.raises(FileExistsError):
        m.fresh_output(path)


def test_analysis_refuses_unmatched_run(tmp_path,monkeypatch):
    monkeypatch.setattr(m,'ROOT',tmp_path)
    run=tmp_path/'run'; run.mkdir()
    (run/'comparison.json').write_text(json.dumps({'baseline_equivalent':False,'protected_files_unchanged':True}))
    with pytest.raises(RuntimeError,match='unmatched'):
        m.analyze(run,tmp_path/'research_outputs'/'analysis')
