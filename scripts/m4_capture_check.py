"""M4 唯讀路徑檢查與擷取後稽核；不匯入 simulator，不啟動擷取或配準。"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def no_links(path):
    path = Path(path).absolute()
    for p in [path, *path.parents]:
        if p.is_symlink():
            raise ValueError('拒絕符號連結：' + str(p))
    return path


def check_target(target, root=ROOT):
    """僅接受學號下全新版本目錄；不建立任何路徑。"""
    target = no_links(target)
    expected = Path(root).resolve() / 'eval/_data/second_floor/114753116'
    if target.parent.resolve() != expected or not re.fullmatch(r'P2_[AC]_[0-9]{2}', target.name):
        raise ValueError('目標必須是 114753116/P2_A_XX 或 P2_C_XX 的獨立版本')
    if target.exists():
        raise FileExistsError('拒絕既有輸出：' + str(target))
    return {'target': str(target), 'target_absent': True,
            'env_test_exists': (Path(root) / 'eval/_data/second_floor/env_test').exists(),
            'capture_started': False}


def inventory(root):
    files = {}
    for p in sorted(root.rglob('*')):
        no_links(p)
        if p.is_file():
            files[str(p.relative_to(root))] = sha(p)
        elif not p.is_dir():
            raise ValueError('非一般檔案：' + str(p))
    return files


def stats(values):
    import numpy as np
    values = np.asarray(values)
    return None if values.size == 0 else dict(zip(
        ['min', 'median', 'p95', 'max'], map(float, np.percentile(values, [0, 50, 95, 100]))))


def inspect_capture(capture):
    """GT 只供離線描述，不產生選取清單、配準初值或參數建議。"""
    import cv2
    import numpy as np
    capture = no_links(capture).resolve()
    if not capture.is_dir():
        raise FileNotFoundError(capture)
    before = inventory(capture)
    intr = json.loads((capture / 'intrinsics.json').read_text())
    if set(intr) != {'width', 'height', 'hfov'}:
        raise ValueError('內參欄位不符合本擷取器三欄契約')
    w, h, fov = intr['width'], intr['height'], intr['hfov']
    if (type(w) is not int or type(h) is not int or w <= 0 or h <= 0
            or not isinstance(fov, (float, int)) or not np.isfinite(fov) or not 0 < fov < 180):
        raise ValueError('非法內參')
    indices = []
    for kind in ['rgb', 'depth']:
        folder = capture / kind
        if not folder.is_dir():
            raise ValueError('缺少 ' + kind)
        names = [p.name for p in folder.iterdir()]
        if not all(re.fullmatch(r'[1-9][0-9]*\.png', n) for n in names):
            raise ValueError(kind + ' 有非標準檔名；不得自動刪除或忽略')
        indices.append(sorted(int(Path(n).stem) for n in names))
    ids = indices[0]
    if not ids or ids != indices[1] or ids != list(range(1, len(ids) + 1)):
        raise ValueError('RGB/Depth 必須完整配對且連續為 1..N')
    gt = np.load(capture / 'GT_pose.npy', allow_pickle=False)
    if gt.dtype != np.float32 or gt.shape != (len(ids), 7) or not np.isfinite(gt).all():
        raise ValueError('GT 須為有限 float32 (N,7)，列數與影格一致')
    norms = np.linalg.norm(gt[:, 3:], axis=1)
    if not np.allclose(norms, 1.0, atol=1e-4):
        raise ValueError('GT 四元數非單位長度')
    rows = []
    duplicates = defaultdict(list)
    for idx in ids:
        rgb = cv2.imread(str(capture / 'rgb' / f'{idx}.png'), cv2.IMREAD_UNCHANGED)
        d = cv2.imread(str(capture / 'depth' / f'{idx}.png'), cv2.IMREAD_UNCHANGED)
        if rgb is None or rgb.dtype != np.uint8 or rgb.shape != (h, w, 3):
            raise ValueError('RGB 編碼／尺寸錯誤：' + str(idx))
        if d is None or d.dtype != np.uint16 or d.shape != (h, w):
            raise ValueError('Depth 編碼／尺寸錯誤：' + str(idx))
        valid = d[d > 0]
        rows.append({'frame': idx, 'invalid_depth_fraction': float(np.mean(d == 0)),
                     'positive_depth_mm': stats(valid), 'above_10m_pixels': int(np.sum(d > 10000))})
        duplicates[hashlib.sha256(rgb.tobytes()).hexdigest()].append(idx)
    delta = np.linalg.norm(np.diff(gt[:, :3].astype(float), axis=0), axis=1)
    q = gt[:, 3:].astype(float) / norms[:, None]
    angle = np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(q[1:] * q[:-1], axis=1)), 0, 1)))
    after = inventory(capture)
    if before != after:
        raise RuntimeError('稽核期間資料改變；保留現場並停止')
    warnings = []
    if (w, h, float(fov)) != (512, 512, 90.0):
        warnings.append('相機與 second_floor.yaml 不同，須人工確認來源')
    if any(r['invalid_depth_fraction'] == 1 for r in rows):
        warnings.append('存在全無效 Depth；不可默默略過')
    if any(r['above_10m_pixels'] for r in rows):
        warnings.append('存在超過設定 10m 的深度')
    return {'structural_integrity': 'passed', 'human_coverage_review': 'pending',
            'first_pass_data_verification': 'not_run', 'capture': str(capture),
            'frame_count': len(ids), 'indices': ids, 'intrinsics': intr,
            'depth_encoding': 'uint16 PNG millimetres; metres = stored / 1000 (source contract, absent in JSON)',
            'gt_layout': 'float32 (N,7), world color sensor [x,y,z,qw,qx,qy,qz]',
            'invalid_depth_fraction': stats([r['invalid_depth_fraction'] for r in rows]),
            'frames': rows, 'adjacent_gt': {'translation_m': stats(delta), 'rotation_deg': stats(angle),
                'pairs': [{'previous': i, 'current': i + 1, 'translation_m': float(d), 'rotation_deg': float(a)}
                          for i, (d, a) in enumerate(zip(delta, angle), 1)],
                'captured_chord_length_m': float(delta.sum()),
                'stationary_pairs_1e_5m': int(np.sum(delta < 1e-5))},
            'identical_rgb_groups': [v for v in duplicates.values() if len(v) > 1],
            'warnings': warnings, 'sha256': before}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='mode', required=True)
    pre = subs.add_parser('preflight')
    pre.add_argument('--target', required=True)
    verify = subs.add_parser('verify')
    verify.add_argument('--capture', required=True)
    verify.add_argument('--report-dir', required=True)
    args = parser.parse_args()
    if args.mode == 'preflight':
        print(json.dumps(check_target(args.target), indent=2, ensure_ascii=False))
        return
    capture = no_links(args.capture).resolve()
    report = no_links(args.report_dir).resolve()
    research = ROOT / 'research_outputs'
    if research not in report.parents or report == research or capture == report or capture in report.parents or report in capture.parents:
        raise ValueError('報告必須在獨立 research_outputs 子目錄，與 Capture 分離')
    if report.exists():
        raise FileExistsError(report)
    # 檢查成功後才獨占建立報告；不寫入原始 Capture。
    result = inspect_capture(capture)
    result['checked_at_utc'] = datetime.now(timezone.utc).isoformat()
    result['checker_sha256'] = sha(__file__)
    result['git_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    report.mkdir(parents=True, exist_ok=False)
    with (report / 'verification.json').open('x') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, allow_nan=False)
    print(json.dumps({'report': str(report), 'frames': result['frame_count'],
                      'warnings': result['warnings'], 'coverage_review': 'pending'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
