"""限明確恢復範圍使用的OS Metadata Exclusion Policy；預設仍嚴格比較。"""
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
from pathlib import Path
import time

_LOG = ContextVar('m32_metadata_log', default=None)
EXACT_PATHS = ('experiments/.DS_Store', 'research_outputs/.DS_Store')
CLOSEOUT_PATHS = EXACT_PATHS + ('research_outputs/m32_20261118_suite_01/.DS_Store',)


@contextmanager
def metadata_policy(log, *, authorized_paths=EXACT_PATHS, authorization_sha256=None):
    paths = tuple(authorized_paths)
    if len(set(paths)) != len(paths) or any(p not in CLOSEOUT_PATHS for p in paths):
        raise ValueError('Unknown exact metadata path')
    if any(p not in EXACT_PATHS for p in paths) and (not isinstance(authorization_sha256, str)
            or len(authorization_sha256) != 64
            or any(c not in '0123456789abcdef' for c in authorization_sha256)):
        raise ValueError('Closeout metadata policy requires explicit authorization SHA-256')
    token = _LOG.set((Path(log), paths, authorization_sha256))
    try:
        yield
    finally:
        _LOG.reset(token)


def record_exclusion(root, name, before):
    """只排除精確路徑的既存一般檔案，逐次另存前後SHA；缺檔仍停止。"""
    scope = _LOG.get()
    if scope is None:
        return False
    log, paths, authorization_sha256 = scope
    p = Path(root)/name
    if name not in paths:
        return False
    symlink = p.is_symlink()
    exists = p.exists() or symlink
    regular = p.is_file() and not symlink
    after = hashlib.sha256(p.read_bytes()).hexdigest() if regular else None
    with log.open('a') as f:
        f.write(json.dumps({'path':name, 'before_sha256':before, 'after_sha256':after,
            'exists':exists, 'regular_file':regular, 'symlink':symlink, 'excluded':regular,
            'changed':before != after, 'unix':time.time(),
            'authorization_sha256':authorization_sha256,
            'policy':'Exact OS metadata exclusion; scientific files remain protected'})+'\n')
    if not regular:
        raise RuntimeError('Protected metadata path is not an existing regular file: '+name)
    return True
