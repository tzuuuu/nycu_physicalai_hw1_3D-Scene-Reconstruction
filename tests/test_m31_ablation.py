"""M3.1 選取唯一性、正式寫入保全及唯讀觀測的真實流程測試。"""
import argparse
import sys
import numpy as np
import pytest
from rdflib import Graph, Literal
from rdflib.namespace import XSD
from scripts import m31_ablation as a
from test_reconstruction import rgbd_capture


def test_exact_query_over_191_synthetic_frames():
    graph=Graph(); api=a.m.api
    exp=api.data_run_iri('p1_baseline_20261118_map005_s0_01','baseline').rsplit('/run/',1)[0]
    from rdflib import URIRef
    exp=URIRef(exp); batch=api.batch_iri('synthetic_only')
    graph.add((exp,api.HW1.onBatch,batch))
    for i in range(1,192):
        frame=api.frame_iri('synthetic_only',i)
        graph.add((batch,api.HW1.hasFrame,frame))
        graph.add((frame,api.HW1.frameIndex,Literal(i,datatype=XSD.integer)))
    rows=list(api.query_graph(graph,a.QUERY.read_text()))
    selected=[int(r[0]) for r in rows]
    a.verify_selection(selected)
    assert len(selected)==len(set(selected))==190
    assert selected[:2]==[1,2] and 104 not in selected
    assert list(zip(selected,selected[1:]))[102]==(103,105)


@pytest.mark.parametrize('frames', [list(range(1,192)), a.FRAMES+[105], a.FRAMES[1:],
                                   [v for v in a.FRAMES if v!=105], a.FRAMES[::-1]])
def test_refuse_any_other_selection(frames):
    with pytest.raises(ValueError): a.verify_selection(frames)


def test_profile_observation_matches_real_callbacks_without_changing_pipeline(rgbd_capture,tmp_path):
    output=tmp_path/'observed'; output.mkdir()
    observer=a.ReturnObserver(output)
    callback,frame_records,pair_records=a.m.api.make_pipeline_measurement_callback(a.m.api.load_quality_factors())
    diagnostics=[]; original=a.m.utils.reconstruct
    (rgbd_capture/'GT_pose.npy').write_bytes(b'GT must remain unread by reconstruction')
    previous=sys.getprofile()
    try:
        sys.setprofile(observer)
        _,positions=original(str(rgbd_capture),frames=[3,101],voxel_size=.08,verbose=False,
                             build_cloud=False,pipeline_callback=callback,diagnostics_callback=diagnostics.append)
    finally: sys.setprofile(previous)
    assert a.m.utils.reconstruct is original
    assert observer.calls==1 and len(observer.transforms)==1
    assert [(t['prev_stem'],t['stem']) for t in observer.transforms]==[(3,101)]
    observed=observer.transforms[0]; actual=diagnostics[0]
    for k in ['trans_init','icp_transformation']:
        np.testing.assert_array_equal(observed[k],actual[k])
    for k in ['coarse_fitness','coarse_rmse','coarse_correspondences','icp_fitness','icp_rmse','icp_correspondences']:
        assert observed[k]==actual[k]
    assert len(observer.events)==3 and len(frame_records)==4 and len(pair_records)==6
    np.testing.assert_array_equal(np.load(output/'positions.npy'),positions)


def test_official_selected_writer_preserves_sealed_baseline(rgbd_capture,tmp_path):
    api=a.m.api
    path=tmp_path/'synthetic_m31.ttl'
    api.cmd_declare(argparse.Namespace(name='synthetic_m31',out=str(path),data_dir=str(rgbd_capture),floor=1))
    decl=api.read_declaration(str(path))
    callback,frames,pairs=api.make_pipeline_measurement_callback(api.load_quality_factors())
    a.m.utils.reconstruct(str(rgbd_capture),voxel_size=.08,verbose=False,build_cloud=False,pipeline_callback=callback)
    api.seal_experiment(str(path),decl,api._pair_frames(str(rgbd_capture)),frames,pairs)
    api.write_run(str(path),'baseline',{'mapMeanL2':.25},frame_count=3)
    before=a.snapshot(path)
    api.write_run(str(path),'selected',{'mapMeanL2':.1},used_frames=[3,101],frame_count=2,
                  metadata={'spliceCount':1,'maxGapLength':97})
    after=a.snapshot(path)
    a.verify_preservation(before,after)
    assert before['turtle_sha256']!=after['turtle_sha256']
    assert len(after['run_nodes'])==2 and after['measured_factors']==18
    # 保全檢查確實能抓到Baseline被改寫，而非只驗證TTL可解析。
    api.write_run(str(path),'baseline',{'mapMeanL2':999},frame_count=3)
    with pytest.raises(RuntimeError,match='baseline'):
        a.verify_preservation(before,a.snapshot(path))
