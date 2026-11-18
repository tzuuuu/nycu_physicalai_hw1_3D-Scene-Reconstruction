"""最終恢復只銜接已核准條件，不把C2審計偽裝成原finalize成功。"""
import json
import pytest
from scripts import m32_experiments as x
from scripts import m32_final_recovery as r


def authorized(tmp_path, monkeypatch):
    monkeypatch.setattr(x, 'ROOT', tmp_path)
    recovery = tmp_path/'resume_03'; (recovery/'status').mkdir(parents=True)
    links = {}
    for name in r.LINKS:
        p = tmp_path/name; p.parent.mkdir(exist_ok=True); p.write_text('{}'); links[name] = x.sha(p)
    auth = dict(remaining_conditions=['C3','C4'], C2_reconstruction_authorized=False,
        metadata_exclusion=list(r.EXACT_PATHS),historical_links=links,tool_sha256={},
        prior_recovery_links={},B0_postprocess_output=str(tmp_path/'B0_postprocess'))
    for name in r.PRIOR_LINKS:
        p = tmp_path/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('{}')
        auth['prior_recovery_links'][name] = x.sha(p)
    (recovery/'authorization.json').write_text(json.dumps(auth))
    return recovery, auth


def test_new_authorization_keeps_old_stop_and_checks_every_historical_marker(tmp_path, monkeypatch):
    recovery, auth = authorized(tmp_path,monkeypatch)
    assert x.sensitivity_authorization(tmp_path) == auth
    assert (tmp_path/'resume_02/system_stopped.json').read_text() == '{}'
    (tmp_path/'resume_02/system_stopped.json').write_text('changed')
    with pytest.raises(RuntimeError, match='Historical'): x.sensitivity_authorization(tmp_path)


def test_new_system_stop_blocks_further_conditions(tmp_path, monkeypatch):
    recovery, _ = authorized(tmp_path,monkeypatch)
    (recovery/'system_stopped.json').write_text('{}')
    with pytest.raises(RuntimeError, match='system stopped'): x.sensitivity_authorization(tmp_path)


def test_c2_audit_is_separate_verified_terminal_evidence(tmp_path, monkeypatch):
    recovery, _ = authorized(tmp_path,monkeypatch)
    evidence = tmp_path/'original_c2'; evidence.write_text('original')
    data = dict(condition='C2',status=r.C2_STATUS,integrity_verified=True,
        original_finalize_succeeded=False,evidence_sha256={'original_c2':x.sha(evidence)})
    (recovery/'status/C2.json').write_text(json.dumps(data))
    assert x.terminal_receipt(tmp_path,'C2')['original_finalize_succeeded'] is False
    assert not (tmp_path/'resume_02/status/C2.json').exists()
    evidence.write_text('changed')
    with pytest.raises(RuntimeError, match='Protected'): x.terminal_receipt(tmp_path,'C2')


@pytest.mark.parametrize('change', ['C2', 'extra', 'wide_metadata'])
def test_final_authorization_cannot_expand_scope(tmp_path, monkeypatch, change):
    recovery, auth = authorized(tmp_path,monkeypatch)
    if change == 'C2': auth['C2_reconstruction_authorized'] = True
    elif change == 'extra': auth['remaining_conditions'].append('D')
    else: auth['metadata_exclusion'] = ['*.DS_Store']
    (recovery/'authorization.json').write_text(json.dumps(auth))
    with pytest.raises(RuntimeError, match='scope'): x.sensitivity_authorization(tmp_path)


def test_final_recovery_keeps_historical_b0_postprocessing_location(tmp_path, monkeypatch):
    recovery, auth = authorized(tmp_path, monkeypatch)
    result = x.evidence_directory(tmp_path, {'condition':'B0'})
    assert result == tmp_path/'B0_postprocess'


def test_final_recovery_checks_previous_metadata_stop_evidence(tmp_path, monkeypatch):
    recovery, auth = authorized(tmp_path, monkeypatch)
    (tmp_path/r.PRIOR_LINKS[0]).write_text('changed')
    with pytest.raises(RuntimeError, match='Protected'):
        x.sensitivity_authorization(tmp_path)
