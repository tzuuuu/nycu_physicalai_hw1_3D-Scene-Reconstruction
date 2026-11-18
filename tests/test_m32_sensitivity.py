"""新停止政策只接受有核心與部分觀測支持的配準失敗，未知例外仍停。"""
import json
import numpy as np
import pytest
from scripts import m32_sensitivity as s
from scripts import m32_experiments as x


def failure_case():
    t={'prev_stem':70,'stem':71,'coarse_fitness':0.,'coarse_rmse':0.,'coarse_correspondences':0,
       'icp_fitness':.9,'icp_rmse':.02,'icp_correspondences':100,
       'trans_init':np.eye(4).tolist(),'icp_transformation':np.eye(4).tolist()}
    execution={'exit_code':1,'resource_guard':{'reason':None}}
    observer={'status':'failed','reconstruct_calls':1}
    trace='Traceback (synthetic)\nRuntimeError: RANSAC failed for 70->71: fitness=0.0, RMSE=0.0, correspondences=0\n'
    return trace,execution,observer,[t]


def test_classifies_real_registration_failure_without_using_icp_as_fallback():
    trace,e,o,ts=failure_case()
    result=s.registration_failure(trace,e,o,ts)
    assert result['current']==71 and result['stage']=='RANSAC' and result['accepted_pairs']==0
    assert ts[0]['icp_fitness']==.9


@pytest.mark.parametrize('problem',['resource','signal','unexpected','pair','values','observation'])
def test_system_or_inconsistent_failure_cannot_continue(problem):
    trace,e,o,ts=failure_case()
    if problem=='resource': e['resource_guard']['reason']='RSS limit'
    if problem=='signal': e['exit_code']=-15
    if problem=='unexpected': trace='TypeError: Object is not JSON serializable'
    if problem=='pair': trace=trace.replace('70->71','69->70')
    if problem=='values': trace=trace.replace('correspondences=0','correspondences=3')
    if problem=='observation': o['reconstruct_calls']=2
    with pytest.raises(RuntimeError): s.registration_failure(trace,e,o,ts)


def test_terminal_failed_registration_requires_intact_evidence(tmp_path,monkeypatch):
    monkeypatch.setattr(x,'ROOT',tmp_path)
    status=tmp_path/'resume_02/status'; status.mkdir(parents=True)
    evidence=tmp_path/'trace'; evidence.write_text('original failure')
    receipt={'condition':'B1','status':'Failed Registration','integrity_verified':True,
             'evidence_sha256':{'trace':x.sha(evidence)}}
    (status/'B1.json').write_text(json.dumps(receipt))
    assert x.terminal_receipt(tmp_path,'B1')['status']=='Failed Registration'
    evidence.write_text('changed')
    with pytest.raises(RuntimeError,match='Protected'): x.terminal_receipt(tmp_path,'B1')


def test_new_policy_binds_every_historical_marker_and_remains_system_locked(tmp_path):
    directory=tmp_path/'resume_02'; directory.mkdir()
    historical={}
    for name in ['suite_stopped.json','resume_failed.json','resume_authorization.json']:
        (tmp_path/name).write_text('{}'); historical[name]=x.sha(tmp_path/name)
    (tmp_path/'suite.json').write_text('{}')
    auth={'remaining_conditions':['B2','C1','C2','C3','C4'],'registration_failure_policy':'preserve_verify_then_continue',
          'B0_B1_rerun_authorized':False,'historical_links':historical,'suite_sha256':x.sha(tmp_path/'suite.json')}
    (directory/'authorization.json').write_text(json.dumps(auth))
    assert x.resume_authorization(tmp_path)==auth
    with pytest.raises(RuntimeError): x.condition_prepare(tmp_path,'B1')
    (directory/'system_stopped.json').write_text('{}')
    with pytest.raises(RuntimeError,match='system'): x.resume_authorization(tmp_path)
