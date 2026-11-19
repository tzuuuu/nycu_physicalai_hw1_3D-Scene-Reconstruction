"""Preflight/declaration ordering and single-attempt failure locks, no real data run."""
from pathlib import Path
import json
import pytest
from scripts import m42_baseline as b


def test_existing_workspace_and_failure_output_are_permanent_locks(tmp_path,monkeypatch):
    exp=tmp_path/'exp'; out=tmp_path/'formal'
    monkeypatch.setattr(b,'EXPERIMENT',exp); monkeypatch.setattr(b,'FORMAL',out)
    assert b.workspace_absent()['absent']
    out.mkdir()
    with pytest.raises(FileExistsError): b.workspace_absent()
    out.rmdir(); exp.mkdir()
    with pytest.raises(FileExistsError): b.workspace_absent()


def test_failed_preflight_never_declares_or_reconstructs(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'preflight',lambda:(tmp_path,{'passed':False}))
    monkeypatch.setattr(b,'declare',lambda *args:pytest.fail('declaration forbidden'))
    monkeypatch.setattr(b,'guarded',lambda *args:pytest.fail('reconstruction forbidden'))
    assert b.terminal_run()==2


def test_exact_official_command_has_no_selection_or_gt_input():
    argv=b.official_argv()
    assert argv[2:]==['--experiment',str(b.EXPERIMENT),'--version','open3d',
        '--voxel-size','0.05','--seed','0','--down-voxel','0.05','--no-vis']
    assert '--selection-query' not in argv


def test_preflight_failure_rejects_declaration_before_workspace_creation(tmp_path,monkeypatch):
    out=tmp_path/'formal'; pre=tmp_path/'pre'; pre.mkdir()
    (pre/'preflight.json').write_text('{"passed":false}')
    monkeypatch.setattr(b,'workspace_absent',lambda:None)
    with pytest.raises(RuntimeError,match='preflight'): b.declare(out,pre)
    assert not out.exists()


def test_failure_report_has_true_partial_counts_and_last_pair(tmp_path):
    out=tmp_path/'failure';obs=out/'observation';obs.mkdir(parents=True)
    (obs/'progress.jsonl').write_text('{"kind":"pair_begin","previous":8,"current":9}\n{"partial"')
    (obs/'events.jsonl').write_text('{"kind":"frame","stem":8}\n')
    (obs/'ransac_returns.jsonl').write_text('{"fitness":0,"correspondences":0}\n')
    result=b.failure_evidence(out,{'exit_code':1,'passed':False})
    assert result['last_progress']['current']==9
    assert result['preprocessed_frames']==1 and result['returned_ransac_pairs']==1
    assert result['complete_mean_l2_m'] is None and not result['full_factors_verified']
    assert result['partial_json_lines']['progress']==[2]
