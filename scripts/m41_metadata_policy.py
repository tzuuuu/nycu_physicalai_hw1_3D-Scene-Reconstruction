"""僅 M4.1 resume_01 使用的兩路徑政策；預設 SHA 比較保持嚴格。"""
import json
from pathlib import Path
import stat
import subprocess
from scripts.m4_capture_check import no_links, sha

EXACT_PATHS = (
    'eval/_data/second_floor/.DS_Store',
    'eval/_data/second_floor/114753116/P2_A_01/.DS_Store',
)
RESUME = 'research_outputs/m41_p2_a01_acceptance_01/resume_01'


def inspect_metadata(root, name):
    if name not in EXACT_PATHS:
        raise ValueError('未授權的精確中繼資料路徑：' + name)
    path = no_links(Path(root) / name)
    mode = path.lstat().st_mode
    if not stat.S_ISREG(mode):
        raise ValueError('中繼資料不是既存一般檔案：' + name)
    header = path.read_bytes()[:8]
    kind = subprocess.check_output(['file', '-b', str(path)], text=True).strip()
    if header != b'\x00\x00\x00\x01Bud1' or 'Apple Desktop Services Store' not in kind:
        raise ValueError('中繼資料格式不符 Finder DS_Store：' + name)
    return {'path': name, 'regular_file': True, 'symlink': False,
            'file_type': kind, 'header_hex': header.hex(), 'current_sha256': sha(path)}


def verify_hashes(root, expected, *, authorization_file=None, log=None):
    """未顯式提供本次授權時，不排除任何差異；不寫入受檢來源。"""
    root = Path(root).resolve()
    auth_sha = None
    if authorization_file is not None:
        auth_path = no_links(authorization_file)
        if auth_path.resolve() != root / RESUME / 'authorization.json':
            raise ValueError('授權只能放在本次精確恢復目錄')
        auth = json.loads(auth_path.read_text())
        if (auth.get('authorized_paths') != list(EXACT_PATHS)
                or auth.get('scope') != 'M4.1 resume_01 only'
                or auth.get('m42_authorized') is not False
                or not auth.get('user_instruction')):
            raise ValueError('授權範圍無效')
        if log is None or no_links(log).parent.resolve() != root / RESUME:
            raise ValueError('必須在本次恢復目錄記錄每次例外檢查')
        auth_sha = sha(auth_path)
    matched, exceptions = 0, []
    for name, before in sorted(expected.items()):
        rel = Path(name)
        if rel.is_absolute() or '..' in rel.parts or str(rel) != name:
            raise ValueError('清單必須使用正規專案相對路徑')
        path = no_links(root / name)
        if not path.is_file():
            raise RuntimeError('受保護檔案缺失／非一般檔案：' + name)
        after = sha(path)
        if auth_sha is not None and name in EXACT_PATHS:
            row = inspect_metadata(root, name)
            row.update(historical_sha256=before, changed=before != after,
                       authorization_sha256=auth_sha, exception_applied=before != after)
            with Path(log).open('a') as f:
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
            if before != after:
                exceptions.append(row)
            else:
                matched += 1
        elif before != after:
            raise RuntimeError('未授權的 SHA 差異：' + name)
        else:
            matched += 1
    return {'expected_count': len(expected), 'strict_matches': matched,
            'authorized_differences': exceptions, 'authorization_sha256': auth_sha}
