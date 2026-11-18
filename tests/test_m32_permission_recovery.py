"""新權限授權保留舊停止，只放行固定C3/C4與原監控器。"""
import json
from pathlib import Path
import pytest
from scripts import m32_experiments as x
from scripts import m32_permission_recovery as r


def authorized(tmp_path, monkeypatch):
    monkeypatch.setattr(x,'ROOT',tmp_path)
    new = tmp_path/'resume_04'; (new/'authorized_monitor_probe').mkdir(parents=True)
    (new/'authorized_monitor_probe/probe.json').write_text('{"passed":true}')
    links = {}
    for name in r.HISTORY:
        p = tmp_path/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('{}'); links[name] = x.sha(p)
    data = dict(remaining_conditions=['C3','C4'],rerun_B0_through_C2=False,
        metadata_exclusion=list(r.EXACT_PATHS),rss_limit_gib=3,monitor='unchanged record_command.py ps',
        historical_links=links,tool_sha256={},permission_probe_sha256={})
    (new/'authorization.json').write_text(json.dumps(data))
    return new,data


def test_new_permission_authorization_preserves_but_supersedes_prior_stop(tmp_path,monkeypatch):
    new,data = authorized(tmp_path,monkeypatch)
    assert x.sensitivity_authorization(tmp_path) == data
    assert (tmp_path/'resume_03/system_stopped.json').read_text() == '{}'
    (tmp_path/'resume_03/system_stopped.json').write_text('changed')
    with pytest.raises(RuntimeError,match='Historical'): x.sensitivity_authorization(tmp_path)


@pytest.mark.parametrize('change',['limit','monitor','scope','metadata'])
def test_permission_recovery_cannot_weaken_monitor_or_expand_scope(tmp_path,monkeypatch,change):
    new,data = authorized(tmp_path,monkeypatch)
    if change == 'limit': data['rss_limit_gib'] = 4
    elif change == 'monitor': data['monitor'] = 'exit-only peak'
    elif change == 'scope': data['remaining_conditions'].append('C2')
    else: data['metadata_exclusion'].append('third/.DS_Store')
    (new/'authorization.json').write_text(json.dumps(data))
    with pytest.raises(RuntimeError,match='scope'): x.sensitivity_authorization(tmp_path)


def test_permission_recovery_stops_on_new_system_failure(tmp_path,monkeypatch):
    new,_ = authorized(tmp_path,monkeypatch)
    (new/'system_stopped.json').write_text('{}')
    with pytest.raises(RuntimeError,match='stopped'): x.sensitivity_authorization(tmp_path)


def test_existing_c2_receipt_is_read_from_original_audit_without_rewriting(tmp_path,monkeypatch):
    new,_ = authorized(tmp_path,monkeypatch)
    (tmp_path/'resume_03/status/C2.json').write_text(json.dumps(dict(
        condition='C2',status=r.prior.C2_STATUS,integrity_verified=True,evidence_sha256={},
        original_finalize_succeeded=False,analysis_directory='original-audit')))
    # 原C2審計receipt也是歷史保護項；為此合成fixture更新其初始授權。
    auth = json.loads((new/'authorization.json').read_text())
    auth['historical_links']['resume_03/status/C2.json'] = x.sha(tmp_path/'resume_03/status/C2.json')
    (new/'authorization.json').write_text(json.dumps(auth))
    record = x.terminal_receipt(tmp_path,'C2')
    assert record['original_finalize_succeeded'] is False
    assert record['analysis_directory'] == 'original-audit'
    assert not (new/'status/C2.json').exists()
