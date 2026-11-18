"""限明確恢復範圍使用的OS Metadata Exclusion Policy；預設仍嚴格比較。"""
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
from pathlib import Path
import time

_LOG = ContextVar('m32_metadata_log', default=None)
EXACT_PATHS = ('experiments/.DS_Store', 'research_outputs/.DS_Store')


@contextmanager
def metadata_policy(log):
    token = _LOG.set(Path(log))
    try:
        yield
    finally:
        _LOG.reset(token)


def record_exclusion(root, name, before):
    """只排除精確路徑的既存一般檔案，逐次另存前後SHA；缺檔仍停止。"""
    log = _LOG.get()
    p = Path(root)/name
    if log is None or name not in EXACT_PATHS:
        return False
    symlink = p.is_symlink()
    exists = p.exists() or symlink
    regular = p.is_file() and not symlink
    after = hashlib.sha256(p.read_bytes()).hexdigest() if regular else None
    with log.open('a') as f:
        f.write(json.dumps({'path':name, 'before_sha256':before, 'after_sha256':after,
            'exists':exists, 'regular_file':regular, 'symlink':symlink, 'excluded':regular,
            'changed':before != after, 'unix':time.time(),
            'policy':'Exact OS metadata exclusion; scientific files remain protected'})+'\n')
    if not regular:
        raise RuntimeError('Protected metadata path is not an existing regular file: '+name)
    return True
