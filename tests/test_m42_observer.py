"""Observer invariance, actual official CLI and full map streaming on synthetic data."""
import argparse
import json
import resource
import sys
import numpy as np
import open3d as o3d
import pytest
import api
import utils
from test_reconstruction import rgbd_capture
from scripts import m42_observer as o
from scripts import m32_experiments as old


def test_dynamic_counts():
    assert o.expected_counts(320)==dict(frames=320,pairs=319,factors=2554)
    assert o.expected_counts(191)==dict(frames=191,pairs=190,factors=1522)
    assert o.expected_counts(1)==dict(frames=1,pairs=0,factors=2)
    with pytest.raises(ValueError): o.expected_counts(0)


def test_observer_exact_return_factor_transform_mean_and_rng_invariance(rgbd_capture,tmp_path):
    np.save(rgbd_capture/'GT_pose.npy',np.tile([0,0,0,1,0,0,0],(3,1)))
    results=[]
    for observed in [False,True]:
        out=tmp_path/str(observed); out.mkdir()
        observer=o.Observer(out)
        callback,frames,pairs=api.make_pipeline_measurement_callback(api.load_quality_factors())
        diagnostics=[]
        np.random.seed(713)
        try:
            if observed: sys.setprofile(observer)
            cloud,positions=utils.reconstruct(str(rgbd_capture),frames=[3,20,101],voxel_size=.05,
                registration_seed=0,down_voxel=.05,verbose=False,pipeline_callback=callback,
                diagnostics_callback=diagnostics.append)
            mean=utils.visualize_and_evaluate(cloud,positions,str(rgbd_capture),frames=[3,20,101],show=False)
        finally: sys.setprofile(None)
        results.append((positions,frames,pairs,diagnostics,mean,np.random.random(5),
            np.asarray(cloud.points).copy(),np.asarray(cloud.colors).copy()))
        if observed:
            np.testing.assert_array_equal(np.load(out/'map_points.npy'),np.asarray(cloud.points))
            np.testing.assert_array_equal(np.load(out/'map_colors.npy'),np.asarray(cloud.colors))
            assert np.load(out/'camera_poses.npy').shape==(3,4,4)
            for r,d in zip(observer.transforms,diagnostics):
                np.testing.assert_array_equal(r['trans_init'],d['trans_init'])
                np.testing.assert_array_equal(r['icp_transformation'],d['icp_transformation'])
    a,b=results
    for i in [0,5,6,7]: np.testing.assert_array_equal(a[i],b[i])
    assert a[1]==b[1] and a[2]==b[2] and a[4]==b[4]
    for d,e in zip(a[3],b[3]):
        for key in d:
            np.testing.assert_array_equal(d[key],e[key])


def test_official_cli_seal_run_and_return_map(rgbd_capture,tmp_path,monkeypatch):
    np.save(rgbd_capture/'GT_pose.npy',np.tile([0,0,0,1,0,0,0],(3,1)))
    ttl=tmp_path/'m42_synthetic.ttl'
    api.cmd_declare(argparse.Namespace(name='m42_synthetic',out=str(ttl),data_dir=str(rgbd_capture),floor=2))
    output=tmp_path/'evidence'; output.mkdir()
    (output/'declaration.before.ttl').write_bytes(ttl.read_bytes())
    original=np.load
    def guard(path,*args,**kwargs):
        if str(path).endswith('GT_pose.npy'):
            assert (output/'observation/map_summary.json').is_file(), 'GT must remain unused until return saved'
        return original(path,*args,**kwargs)
    monkeypatch.setattr(np,'load',guard)
    obs=o.execute_cli(ttl,output/'observation')
    exp,rows,mean=old.validate_evidence(ttl,output/'observation',[3,20,101])
    assert obs.calls==1 and len(rows)==18 and exp['complete'] and mean<1e-8
    meta=json.loads((output/'observation/map_summary.json').read_text())
    assert meta['point_count']==len(np.load(output/'observation/map_points.npy'))
    assert meta['full_returned_map'] and meta['sample_stride']==1
    trajectory=json.loads((output/'observation/trajectory_metadata.json').read_text())
    assert trajectory['arrays']['camera_poses']['shape']==[3,4,4]
    assert trajectory['arrays']['camera_poses']['dtype']=='float64'
    assert trajectory['frame_indices']==[3,20,101] and trajectory['pairwise_direction']=='current->previous'
    with pytest.raises(FileExistsError): o.execute_cli(ttl,output/'observation')


def test_full_export_memory_and_no_sampling(tmp_path):
    # 2 million points = 96 MB points+colors, above any legacy 150k sample.
    cloud=o3d.geometry.PointCloud()
    cloud.points=o3d.utility.Vector3dVector(np.zeros((2000000,3),dtype=np.float64))
    cloud.colors=o3d.utility.Vector3dVector(np.full((2000000,3),.5,dtype=np.float64))
    result=o.save_map(cloud,tmp_path)
    points=np.load(tmp_path/'map_points.npy',mmap_mode='r')
    colors=np.load(tmp_path/'map_colors.npy',mmap_mode='r')
    assert points.shape==colors.shape==(2000000,3)
    assert result['peak_rss_increase_bytes']<24*2**20
    np.testing.assert_array_equal(points[-1],np.asarray(cloud.points)[-1])
    np.testing.assert_array_equal(colors[-1],np.asarray(cloud.colors)[-1])


def test_failure_retains_real_prefix_and_not_fake_map(rgbd_capture,tmp_path,monkeypatch):
    # Inject an explicit read exception at second frame; core's skip policy is unchanged.
    real=utils._read_rgbd
    def broken(rgb,depth,scale):
        if str(depth).endswith('/20.png'): raise OSError('synthetic I/O failure')
        return real(rgb,depth,scale)
    monkeypatch.setattr(utils,'_read_rgbd',broken)
    out=tmp_path/'prefix'; out.mkdir(); observer=o.Observer(out)
    try:
        sys.setprofile(observer)
        with pytest.raises(Exception):
            utils.reconstruct(str(rgbd_capture),frames=[3,20,101],verbose=False)
    finally: sys.setprofile(None)
    assert (out/'events.jsonl').exists()
    assert not (out/'map_summary.json').exists()


def test_full_official_postprocess_figures_and_manifest(rgbd_capture,tmp_path):
    from scripts.m42_results import results
    np.save(rgbd_capture/'GT_pose.npy',np.tile([0,0,0,1,0,0,0],(3,1)))
    ttl=tmp_path/'synthetic_results.ttl'
    api.cmd_declare(argparse.Namespace(name='synthetic_results',out=str(ttl),data_dir=str(rgbd_capture),floor=2))
    out=tmp_path/'results'; out.mkdir()
    (out/'declaration.before.ttl').write_bytes(ttl.read_bytes())
    o.execute_cli(ttl,out/'observation')
    (out/'command').mkdir()
    (out/'command/execution.json').write_text(json.dumps(dict(elapsed_s=1.,peak_tree_rss_bytes=123)))
    import shutil
    shutil.copyfile(ttl,ttl.parent/'synthetic_results'/ttl.name)
    summary=results(out,ttl.parent/'synthetic_results',rgbd_capture,expected_frames=[3,20,101])
    assert summary['frames']==3 and summary['factors']==18
    assert len(list((out/'figures').glob('*.png')))==5
    assert json.loads((out/'validation.json').read_text())['seal_valid']


def test_registration_failure_preserves_actual_zero_support_without_fake_success(rgbd_capture,tmp_path,monkeypatch):
    def zero_support(*args): return o3d.pipelines.registration.RegistrationResult()
    monkeypatch.setattr(utils,'_global_registration',zero_support)
    out=tmp_path/'zero_support';out.mkdir();observer=o.Observer(out)
    try:
        sys.setprofile(observer)
        with pytest.raises(RuntimeError,match='RANSAC failed'):
            utils.reconstruct(str(rgbd_capture),frames=[3,20,101],verbose=False)
    finally: sys.setprofile(None)
    r=json.loads((out/'ransac_returns.jsonl').read_text())
    assert r['fitness']==0 and r['correspondences']==0
    transform=json.loads((out/'transforms.jsonl').read_text())
    assert transform['accepted_by_core'] is False
    assert len(observer.poses)==1
    assert not (out/'camera_poses.npy').exists() and not (out/'map_points.npy').exists()
