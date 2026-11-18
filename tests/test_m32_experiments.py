"""M3.2 七條件界線、正式CLI同次觀測與防覆寫測試；只用合成資料。"""
import argparse
import sys
from pathlib import Path
import numpy as np
import pytest
import api
import reconstruct as cli
import utils
from scripts import m32_experiments as x
from test_reconstruction import rgbd_capture


@pytest.mark.parametrize('condition,voxel,seed', x.CONDITIONS)
def test_authorized_cli_parameters_reach_official_first_pass(monkeypatch,condition,voxel,seed):
    x.validate_condition(condition,voxel,seed)
    monkeypatch.setattr(sys,'argv',['reconstruct.py']+x.cli_args('synthetic.ttl',voxel,seed))
    monkeypatch.setattr(api,'is_assessed',lambda _:False)
    monkeypatch.setattr(api,'read_declaration',lambda _: {'batch_path':'synthetic_capture','required':{'icpBackend':'open3d'}})
    monkeypatch.setattr(api,'_pair_frames',lambda _: [('1','r','d'),('2','r','d')])
    captured={}
    class ReachedPipeline(Exception): pass
    def sentinel(*args,**kwargs):
        captured.update(args=args,kwargs=kwargs)
        raise ReachedPipeline
    monkeypatch.setattr(utils,'reconstruct',sentinel)
    with pytest.raises(ReachedPipeline): cli.main()
    assert captured['args']==('synthetic_capture','open3d')
    kw=captured['kwargs']
    assert (kw['voxel_size'],kw['registration_seed'],kw['down_voxel'],kw['build_cloud'])==(voxel,seed,.05,True)
    assert kw['frames']==[1,2] and callable(kw['pipeline_callback'])


@pytest.mark.parametrize('value',[('B1',.04,0),('C1',.03,1),('C5',.05,5),('B0',.05,2)])
def test_no_other_condition(value):
    with pytest.raises(ValueError): x.validate_condition(*value)


def test_real_official_cli_same_run_evidence_seal_query_and_no_gt_in_pipeline(rgbd_capture,tmp_path,monkeypatch):
    np.save(rgbd_capture/'GT_pose.npy',np.tile([0,0,0,1,0,0,0],(3,1)))
    name='synthetic_m32'
    ttl=tmp_path/(name+'.ttl')
    api.cmd_declare(argparse.Namespace(name=name,out=str(ttl),data_dir=str(rgbd_capture),floor=1))
    output=tmp_path/'records'; output.mkdir()
    (output/'declaration.before.ttl').write_bytes(ttl.read_bytes())
    original_reconstruct,original_ransac,original_icp=utils.reconstruct,utils._global_registration,utils.local_icp_algorithm
    real_load=np.load
    def guarded_load(path,*args,**kwargs):
        if str(path).endswith('GT_pose.npy'):
            assert (output/'observation/camera_poses.npy').is_file(), 'GT before completed reconstruction'
        return real_load(path,*args,**kwargs)
    monkeypatch.setattr(np,'load',guarded_load)
    observer=x.execute_cli(ttl,output/'observation',.05,1)
    exp,rows,l2=x.validate_evidence(ttl,output/'observation',[3,20,101])
    assert observer.calls==1 and len(observer.transforms)==2 and len(rows)==18
    assert exp['complete'] and l2<1e-8
    assert utils.reconstruct is original_reconstruct
    assert utils._global_registration is original_ransac and utils.local_icp_algorithm is original_icp
    assert (tmp_path/name/'reconstruction_baseline.png').is_file()
    assert len(api.frames_from_sparql_query(exp,write_query(tmp_path,exp)))==3
    with pytest.raises(FileExistsError): x.execute_cli(ttl,output/'observation',.05,1)
    # 宣告封存後若run被覆寫，核對確實能偵測，不只檢查語法與Seal。
    api.write_run(str(ttl),'baseline',{'mapMeanL2':999},frame_count=3)
    with pytest.raises(RuntimeError,match='Mean L2'): x.validate_evidence(ttl,output/'observation',[3,20,101])


def write_query(path,exp):
    q=path/'audit.rq'
    q.write_text('''PREFIX hw1: <http://taica.course/hw1/ontology#>
SELECT DISTINCT ?frameIndex WHERE { ?batch hw1:hasFrame ?frame . ?frame hw1:frameIndex ?frameIndex . }
ORDER BY ASC(?frameIndex)''')
    return str(q)


def test_observer_matches_callbacks_and_reconstruct_never_reads_gt(rgbd_capture,tmp_path):
    (rgbd_capture/'GT_pose.npy').write_bytes(b'not an array; registration must not read GT')
    out=tmp_path/'observe'; out.mkdir()
    observer=x.Observer(out)
    cb,frames,pairs=api.make_pipeline_measurement_callback(api.load_quality_factors())
    diagnostics=[]
    try:
        sys.setprofile(observer)
        utils.reconstruct(str(rgbd_capture),frames=[3,20,101],voxel_size=.08,
                          registration_seed=0,build_cloud=False,verbose=False,
                          pipeline_callback=cb,diagnostics_callback=diagnostics.append)
    finally: sys.setprofile(None)
    assert len(observer.actual_pairs)==len(diagnostics)==2
    for a,b in zip(observer.transforms,diagnostics):
        for key in ['trans_init','icp_transformation']:
            np.testing.assert_array_equal(a[key],b[key])
    assert len(frames)==6 and len(pairs)==12
    assert np.load(out/'camera_poses.npy').shape==(3,4,4)


def test_hash_and_exclusive_execution_guard(tmp_path,monkeypatch):
    monkeypatch.setattr(x,'ROOT',tmp_path)
    p=tmp_path/'protected'; p.write_text('original')
    hashes={'protected':x.sha(p)}
    assert x.verify_hashes(hashes)==1
    p.write_text('changed')
    with pytest.raises(RuntimeError,match='Protected'): x.verify_hashes(hashes)
    x.m.dump(tmp_path/'execution.started.json',{'one':1})
    with pytest.raises(FileExistsError): x.m.dump(tmp_path/'execution.started.json',{'two':2})


def test_frame_validation_requires_both_full_sets_and_gt_header(tmp_path):
    for modality in ['rgb','depth']:
        (tmp_path/modality).mkdir()
        for i in range(1,192): (tmp_path/modality/(str(i)+'.png')).touch()
    np.save(tmp_path/'GT_pose.npy',np.zeros((191,7)))
    x.validate_frames(tmp_path)
    (tmp_path/'depth/104.png').unlink()
    with pytest.raises(ValueError,match='191'): x.validate_frames(tmp_path)
