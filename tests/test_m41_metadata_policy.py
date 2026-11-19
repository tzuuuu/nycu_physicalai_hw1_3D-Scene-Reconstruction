"""合成檔案驗證精確例外與預設嚴格邊界；不讀正式 Capture、不配準。"""
import json
from pathlib import Path
import pytest
from scripts.m4_capture_check import sha
from scripts.m41_metadata_policy import EXACT_PATHS, RESUME, verify_hashes


@pytest.fixture
def policy(tmp_path):
    record = tmp_path / RESUME
    record.mkdir(parents=True)
    auth = record / 'authorization.json'
    auth.write_text(json.dumps({'authorized_paths': list(EXACT_PATHS),
        'scope': 'M4.1 resume_01 only', 'm42_authorized': False,
        'user_instruction': '合成測試，僅授權兩個精確中繼檔'}))
    for name in EXACT_PATHS:
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b'\x00\x00\x00\x01Bud1' + b'\0' * 64)
    return tmp_path, auth, record / 'metadata.jsonl'


def test_strict_default_and_explicit_two_path_policy(policy):
    root, auth, log = policy
    expected = {n: '0' * 64 for n in EXACT_PATHS}
    with pytest.raises(RuntimeError, match='SHA'):
        verify_hashes(root, expected)
    assert not log.exists()
    before = {n: (root / n).read_bytes() for n in EXACT_PATHS}
    result = verify_hashes(root, expected, authorization_file=auth, log=log)
    assert len(result['authorized_differences']) == 2
    rows = [json.loads(s) for s in log.read_text().splitlines()]
    assert {r['path'] for r in rows} == set(EXACT_PATHS)
    assert all(r['authorization_sha256'] == sha(auth) for r in rows)
    assert before == {n: (root / n).read_bytes() for n in EXACT_PATHS}
    with pytest.raises(RuntimeError):
        verify_hashes(root, expected)  # 政策不會洩漏至下次嚴格比較


@pytest.mark.parametrize('name', ['experiments/.DS_Store', 'research_outputs/.DS_Store',
    'eval/_data/second_floor/114753116/.DS_Store',
    'eval/_data/second_floor/114753116/P2_A_01/rgb/1.png', 'GT_pose.npy',
    'intrinsics.json', 'original.ttl', 'seal.json', 'load.py', 'capture.yaml'])
def test_third_or_scientific_change_stops(policy, name):
    root, auth, log = policy
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b'unchanged evidence')
    with pytest.raises(RuntimeError, match='SHA'):
        verify_hashes(root, {name: '0' * 64}, authorization_file=auth, log=log)
    assert p.read_bytes() == b'unchanged evidence'


@pytest.mark.parametrize('fault', ['missing', 'directory', 'symlink', 'wrong_type', 'wrong_header'])
def test_metadata_must_be_existing_regular_finder_file(policy, fault):
    root, auth, log = policy
    p = root / EXACT_PATHS[0]
    p.unlink()
    if fault == 'directory': p.mkdir()
    elif fault == 'symlink': p.symlink_to(root / EXACT_PATHS[1])
    elif fault == 'wrong_type': p.write_bytes(b'not Finder metadata')
    elif fault == 'wrong_header': p.write_bytes(b'\0' * 80)
    with pytest.raises((ValueError, RuntimeError)):
        verify_hashes(root, {EXACT_PATHS[0]: '0' * 64}, authorization_file=auth, log=log)


@pytest.mark.parametrize('fault', ['expand', 'm42', 'scope', 'missing_log', 'wrong_auth_path'])
def test_authorization_scope_cannot_expand(policy, fault):
    root, auth, log = policy
    data = json.loads(auth.read_text())
    if fault == 'expand': data['authorized_paths'].append('experiments/.DS_Store')
    elif fault == 'm42': data['m42_authorized'] = True
    elif fault == 'scope': data['scope'] = 'all experiments'
    elif fault == 'missing_log': log = None
    elif fault == 'wrong_auth_path': auth = root / 'other_authorization.json'
    auth.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        verify_hashes(root, {EXACT_PATHS[0]: '0' * 64}, authorization_file=auth, log=log)
