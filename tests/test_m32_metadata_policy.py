"""精確OS中繼檔政策：科學檔案仍須完全保護。"""
import json
import pytest
from scripts import m32_experiments as x
from scripts.m32_metadata_policy import metadata_policy


@pytest.mark.parametrize('name', ['experiments/.DS_Store', 'research_outputs/.DS_Store'])
def test_exact_metadata_change_is_logged_and_original_inventory_preserved(tmp_path, monkeypatch, name):
    monkeypatch.setattr(x, 'ROOT', tmp_path)
    p = tmp_path/name
    p.parent.mkdir(); p.write_bytes(b'original')
    original = x.sha(p); hashes = {name: original}
    p.write_bytes(b'changed'); log = tmp_path/'metadata.jsonl'
    with metadata_policy(log):
        assert x.verify_hashes(hashes) == 1
    row = json.loads(log.read_text())
    assert row['path'] == name
    assert row['before_sha256'] == original and row['after_sha256'] == x.sha(p)
    assert hashes == {name: original}
    assert row['exists'] is True and row['regular_file'] is True
    assert row['symlink'] is False and row['changed'] is True
    with pytest.raises(RuntimeError, match='Protected'):
        x.verify_hashes(hashes)


@pytest.mark.parametrize('name', ['experiments/sub/.DS_Store', 'research_outputs/sub/.DS_Store',
    'eval/_data/first_floor/rgb/1.png', 'eval/_data/first_floor/GT_pose.npy',
    'utils.py', 'pixi.lock', 'experiments/run/result.ttl',
    'experiments/run/reconstruction_baseline.png', 'research_outputs/poses.npy'])
def test_metadata_policy_does_not_allow_other_file_changes(tmp_path, monkeypatch, name):
    monkeypatch.setattr(x, 'ROOT', tmp_path)
    p = tmp_path/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'original')
    hashes = {name: x.sha(p)}; p.write_bytes(b'changed')
    with metadata_policy(tmp_path/'metadata.jsonl'):
        with pytest.raises(RuntimeError, match='Protected'):
            x.verify_hashes(hashes)


def test_metadata_exception_does_not_mask_simultaneous_scientific_change(tmp_path, monkeypatch):
    monkeypatch.setattr(x, 'ROOT', tmp_path)
    (tmp_path/'experiments').mkdir()
    paths = [tmp_path/'experiments/.DS_Store', tmp_path/'utils.py']
    for p in paths: p.write_bytes(b'original')
    hashes = {str(p.relative_to(tmp_path)): x.sha(p) for p in paths}
    for p in paths: p.write_bytes(b'changed')
    with metadata_policy(tmp_path/'metadata.jsonl'):
        with pytest.raises(RuntimeError, match='utils.py'):
            x.verify_hashes(hashes)
    assert json.loads((tmp_path/'metadata.jsonl').read_text())['before_sha256'] == hashes['experiments/.DS_Store']


def test_deleted_metadata_is_not_authorized(tmp_path, monkeypatch):
    monkeypatch.setattr(x, 'ROOT', tmp_path)
    with metadata_policy(tmp_path/'metadata.jsonl'):
        with pytest.raises(RuntimeError, match='Protected'):
            x.verify_hashes({'experiments/.DS_Store': 'original'})


@pytest.mark.parametrize('name', ['experiments/.DS_Store', 'research_outputs/.DS_Store'])
@pytest.mark.parametrize('kind', ['missing', 'symlink', 'directory'])
def test_exact_path_requires_existing_regular_file_and_records_state(tmp_path, monkeypatch, name, kind):
    monkeypatch.setattr(x, 'ROOT', tmp_path)
    p = tmp_path/name; p.parent.mkdir()
    if kind == 'symlink':
        target = tmp_path/'other'; target.write_bytes(b'changed'); p.symlink_to(target)
    elif kind == 'directory': p.mkdir()
    log = tmp_path/'metadata.jsonl'
    with metadata_policy(log):
        with pytest.raises(RuntimeError, match='Protected'):
            x.verify_hashes({name: x.sha(p) if kind == 'symlink' else 'historical'})
    row = json.loads(log.read_text())
    assert row['path'] == name and row['excluded'] is False
    assert row['exists'] == (kind != 'missing')
    assert row['symlink'] == (kind == 'symlink')


@pytest.mark.parametrize('name', ['experiments/.DS_Store', 'research_outputs/.DS_Store',
    'research_outputs/m32_20261118_suite_01/.DS_Store'])
def test_closeout_three_exact_paths_require_authorization_and_log_it(tmp_path, monkeypatch, name):
    monkeypatch.setattr(x,'ROOT',tmp_path)
    p=tmp_path/name;p.parent.mkdir(parents=True);p.write_bytes(b'old')
    before=x.sha(p);p.write_bytes(b'new')
    paths=('experiments/.DS_Store','research_outputs/.DS_Store','research_outputs/m32_20261118_suite_01/.DS_Store')
    with metadata_policy(tmp_path/'closeout.jsonl',authorized_paths=paths,authorization_sha256='a'*64):
        x.verify_hashes({name:before})
    row=json.loads((tmp_path/'closeout.jsonl').read_text())
    assert row['path']==name and row['before_sha256']==before and row['after_sha256']==x.sha(p)
    assert row['authorization_sha256']=='a'*64 and row['regular_file'] and row['exists']
    with pytest.raises(RuntimeError,match='Protected'):x.verify_hashes({name:before})


def test_closeout_third_path_does_not_silently_expand_old_authorizations(tmp_path,monkeypatch):
    monkeypatch.setattr(x,'ROOT',tmp_path)
    p=tmp_path/'research_outputs/m32_20261118_suite_01/.DS_Store'
    p.parent.mkdir(parents=True);p.write_bytes(b'new')
    with metadata_policy(tmp_path/'old.jsonl'):
        with pytest.raises(RuntimeError,match='Protected'):x.verify_hashes({str(p.relative_to(tmp_path)):'old'})
    with pytest.raises(ValueError,match='authorization'):
        with metadata_policy(tmp_path/'no_auth.jsonl',authorized_paths=('research_outputs/m32_20261118_suite_01/.DS_Store',)):
            pass


@pytest.mark.parametrize('name',['research_outputs/m32_20261118_suite_01/nested/.DS_Store',
    'experiments/another/.DS_Store','utils.py','research_outputs/result.json','ontology/hw1.ttl'])
def test_closeout_exception_never_masks_fourth_path_or_scientific_change(tmp_path,monkeypatch,name):
    monkeypatch.setattr(x,'ROOT',tmp_path)
    p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'changed')
    paths=('experiments/.DS_Store','research_outputs/.DS_Store','research_outputs/m32_20261118_suite_01/.DS_Store')
    with metadata_policy(tmp_path/'closeout.jsonl',authorized_paths=paths,authorization_sha256='b'*64):
        with pytest.raises(RuntimeError,match='Protected'):x.verify_hashes({name:'old'})


@pytest.mark.parametrize('kind',['missing','directory','symlink'])
def test_closeout_third_path_rejects_non_regular_files(tmp_path,monkeypatch,kind):
    monkeypatch.setattr(x,'ROOT',tmp_path)
    name='research_outputs/m32_20261118_suite_01/.DS_Store';p=tmp_path/name;p.parent.mkdir(parents=True)
    if kind=='directory':p.mkdir()
    if kind=='symlink':
        target=tmp_path/'target';target.write_bytes(b'target');p.symlink_to(target)
    before=x.sha(p) if kind=='symlink' else 'old'
    with metadata_policy(tmp_path/'bad.jsonl',authorized_paths=(name,),authorization_sha256='c'*64):
        with pytest.raises(RuntimeError,match='Protected'):x.verify_hashes({name:before})
