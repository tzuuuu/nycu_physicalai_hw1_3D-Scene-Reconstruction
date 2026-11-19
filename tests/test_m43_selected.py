"""Selected official-CLI contract, one-attempt refusal, fixed reference and export."""
import argparse
import json
from pathlib import Path
import numpy as np
import pytest
import api
from scripts import m43_analysis as a
from scripts import m43_selected as s
from scripts import m43_results as r
from scripts.m42_observer import execute_cli
from test_reconstruction import rgbd_capture


def synthetic(rgbd_capture,tmp_path):
    np.save(rgbd_capture/'GT_pose.npy',np.tile([0,0,0,1,0,0,0],(3,1)))
    ttl=tmp_path/'m43_synthetic.ttl'
    api.cmd_declare(argparse.Namespace(name='m43_synthetic',out=str(ttl),data_dir=str(rgbd_capture),floor=2))
    out=tmp_path/'baseline';out.mkdir()
    execute_cli(ttl,out/'observation')
    query=tmp_path/'selected.rq'
    query.write_text('PREFIX hw1: <http://taica.course/hw1/ontology#> SELECT DISTINCT ?frameIndex WHERE { ?f hw1:frameIndex ?frameIndex . VALUES ?frameIndex { 3 101 } } ORDER BY ?frameIndex')
    return ttl,query,out


def test_official_selected_preserves_seal_baseline_factors_and_saves_new_pairs(rgbd_capture,tmp_path,monkeypatch):
    ttl,query,base=synthetic(rgbd_capture,tmp_path)
    before=tmp_path/'before.ttl';before.write_bytes(ttl.read_bytes())
    real=np.load
    output=tmp_path/'selected'
    def load(path,*args,**kw):
        if str(path).endswith('GT_pose.npy'):
            assert (output/'map_summary.json').exists(), 'GT only after same-call selected map export'
        return real(path,*args,**kw)
    monkeypatch.setattr(np,'load',load)
    observer=s.execute_selected(ttl,query,output)
    assert observer.calls==1
    delta=s.graph_delta(before,ttl,[3,101])
    assert delta['baseline_factors_retained']==18 and delta['seal_valid']
    assert r.validated_arrays(output,[3,101])['camera_poses'].shape==(2,4,4)
    events=a.lines(output/'events.jsonl')
    rows=r.observed_rows(events)
    assert len(rows)==10
    assert {x['previous'] for x in rows if x['factor']=='ICPInlierFitness'}=={3}
    assert {x['current'] for x in rows if x['factor']=='ICPInlierFitness'}=={101}
    assert json.loads((output/'actual_reconstruct_arguments.json').read_text())['frames']==[3,101]
    with pytest.raises(FileExistsError):s.execute_selected(ttl,query,output)


def test_failed_preflight_never_launches_or_reserves(tmp_path,monkeypatch):
    monkeypatch.setattr(s,'preflight',lambda native:(tmp_path,{'passed':False}))
    monkeypatch.setattr(s,'guarded',lambda *args:pytest.fail('No workload allowed'))
    monkeypatch.setattr(a,'OUT',tmp_path/'formal')
    assert s.run()==2 and not a.OUT.exists()


def test_permanent_attempt_lock(tmp_path,monkeypatch):
    out=tmp_path/'formal';out.mkdir();monkeypatch.setattr(a,'OUT',out)
    with pytest.raises(FileExistsError):s.absent()


def test_fixed_original_first_reference_and_original_index_mapping():
    gt=np.array([[10,20,30,1,0,0,0],[11,20,30,1,0,0,0],[12,20,30,1,0,0,0]],float)
    p,t,error=r.frame_errors([[0,0,0],[1.8,0,0]],gt,[1,3])
    np.testing.assert_allclose(t,[[0,0,0],[2,0,0]])
    np.testing.assert_allclose(error,[0,.2])


def test_directed_coverage_not_point_count_ratio():
    source=np.array([[0,0,0],[1,0,0],[2,0,0]],float)
    target=np.array([[0,0,0],[1,0,0]],float)
    distance,report=r.coverage(source,target)
    assert report['fraction_within_threshold']==2/3
    np.testing.assert_array_equal(distance,[0,0,1])
    assert len(r.occupancy(np.vstack([source,source])))==3


def test_frozen_rule_reproducibility_and_no_phase1_exclusion():
    import csv
    with (a.BASE/'factors.csv').open() as f:rows=list(csv.DictReader(f))
    indices,reasons,thresholds,flags=a.selection(rows,a.lines(a.BASE/'observation/transforms.jsonl'))
    assert indices==json.loads(a.SPEC.read_text())['selected_indices']
    assert len(indices)==204 and indices[0]==1 and indices[-1]==320 and 104 in indices
    assert max(np.diff(indices))==2 and {147,148,149,150,151}.issubset(indices)
    assert 'bridge_CoarseRANSACCorrespondences' in reasons[148]


def test_selected_pair_failure_is_preserved_without_retry(rgbd_capture,tmp_path,monkeypatch):
    import utils,open3d as o3d
    ttl,query,base=synthetic(rgbd_capture,tmp_path)
    before=ttl.read_bytes()
    monkeypatch.setattr(utils,'_global_registration',lambda *args:o3d.pipelines.registration.RegistrationResult())
    out=tmp_path/'failed'
    with pytest.raises(RuntimeError,match='RANSAC failed'):s.execute_selected(ttl,query,out)
    assert ttl.read_bytes()==before
    assert json.loads((out/'observer_summary.json').read_text())['reconstruct_calls']==1
    assert json.loads((out/'ransac_returns.jsonl').read_text())['correspondences']==0
    assert not (out/'map_summary.json').exists()


def test_graph_delta_rejects_changes_to_baseline(rgbd_capture,tmp_path):
    ttl,query,base=synthetic(rgbd_capture,tmp_path)
    before=tmp_path/'before.ttl';before.write_bytes(ttl.read_bytes())
    s.execute_selected(ttl,query,tmp_path/'selected')
    exp=api.read_experiment(str(ttl))
    api.write_run(str(ttl),'baseline',{'mapMeanL2':123.456},frame_count=3)
    with pytest.raises(RuntimeError,match='Historical'):s.graph_delta(before,ttl,[3,101])


def test_offline_report_pipeline_with_synthetic_saved_data(rgbd_capture,tmp_path,monkeypatch):
    """Exercise real exports, fixed axes, NN/occupancy and all comparison figures."""
    import shutil
    ttl,query,base=synthetic(rgbd_capture,tmp_path)
    out=tmp_path/'formal';out.mkdir()
    shutil.copyfile(ttl,out/'baseline.before.ttl')
    s.execute_selected(ttl,query,out/'observation')
    # Synthetic saved 320-pose baseline, explicitly test-only, never formal sources.
    np.save(base/'observation/positions.npy',np.zeros((320,3)))
    (base/'observation/official_evaluation.json').write_text('{"mean_l2_raw_m":0}')
    shutil.copyfile(out/'observation/camera_poses.npy',base/'observation/camera_poses.npy')
    np.save(rgbd_capture/'GT_pose.npy',np.tile([0,0,0,1,0,0,0],(320,1)))
    from scripts.m42_results import csv_write
    csv_write(base/'factors.csv',r.observed_rows(a.lines(base/'observation/events.jsonl')))
    for directory,seconds in [(base,2.0),(out,1.0)]:
        (directory/'command').mkdir()
        (directory/'command/execution.json').write_text(json.dumps(dict(elapsed_s=seconds,peak_tree_rss_bytes=123)))
    spec=tmp_path/'rule.json';spec.write_text('{"selected_indices":[3,101]}')
    for key,value in [('BASE',base),('TTL',ttl),('CAPTURE',rgbd_capture),('SPEC',spec)]:monkeypatch.setattr(a,key,value)
    comparison=r.results(out)
    assert comparison['worker_time_reduction_fraction']==.5
    assert comparison['new_selected_measurements']==10
    assert len(list((out/'figures').glob('*.png')))==6
    assert (out/'scene_coverage.json').is_file() and (out/'figure_manifest.json').is_file()


def test_float32_gt_promoted_before_first_camera_subtraction():
    # Saved capture GT is float32; official evaluation promotes BEFORE subtraction.
    gt=np.array([[10.123,-20.321,30.234,1,0,0,0],
                 [12.7,4.2,-2.2,1,0,0,0]],dtype=np.float32)
    positions=np.array([[0,0,0],[2.5,-24.5,32.5]],dtype=np.float64)
    expected_gt=gt.astype(np.float64)[:,:3]-gt.astype(np.float64)[0,:3]
    expected_error=np.linalg.norm(positions*[1,-1,-1]-expected_gt,axis=1)
    _,truth,error=r.frame_errors(positions,gt,[1,2])
    np.testing.assert_array_equal(truth,expected_gt)
    np.testing.assert_allclose(error,expected_error,rtol=0,atol=1e-12)
