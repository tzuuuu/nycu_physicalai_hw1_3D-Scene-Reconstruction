"""只用暫存合成檔案驗證 M4 防覆寫與稽核失敗邊界，不啟動模擬器。"""
import json
from pathlib import Path
import cv2
import numpy as np
import pytest
from scripts.m4_capture_check import check_target, inspect_capture, inventory


def test_target_refuses_parent_existing_and_symlink(tmp_path):
    student = tmp_path / 'eval/_data/second_floor/114753116'
    target = student / 'P2_A_01'
    assert check_target(target, tmp_path)['target_absent']
    assert not student.exists()  # preflight 真正唯讀
    for path in [student, student.parent / 'env_test', student / 'P2_B_01', student / '../P2_A_01']:
        with pytest.raises(ValueError):
            check_target(path, tmp_path)
    target.mkdir(parents=True)
    (target / 'keep').write_bytes(b'original')
    with pytest.raises(FileExistsError):
        check_target(target, tmp_path)
    assert (target / 'keep').read_bytes() == b'original'
    (student / 'P2_C_01').symlink_to(tmp_path / 'missing')
    with pytest.raises(ValueError, match='符號連結'):
        check_target(student / 'P2_C_01', tmp_path)


@pytest.fixture
def capture(tmp_path):
    for name in ['rgb', 'depth']:
        (tmp_path / name).mkdir()
    (tmp_path / 'intrinsics.json').write_text(json.dumps({'width': 8, 'height': 6, 'hfov': 90.0}))
    for i in [1, 2]:
        cv2.imwrite(str(tmp_path / 'rgb' / f'{i}.png'), np.full((6, 8, 3), 90, np.uint8))
        depth = np.full((6, 8), 2500, np.uint16)
        depth[0, 0] = 0
        cv2.imwrite(str(tmp_path / 'depth' / f'{i}.png'), depth)
    np.save(tmp_path / 'GT_pose.npy', np.array([[0, 0, 0, 1, 0, 0, 0], [.2, 0, 0, 1, 0, 0, 0]], np.float32))
    return tmp_path


def test_inspection_readonly_units_motion_and_duplicates(capture):
    before = inventory(capture)
    result = inspect_capture(capture)
    assert inventory(capture) == before == result['sha256']
    assert result['frame_count'] == 2
    assert result['frames'][0]['invalid_depth_fraction'] == pytest.approx(1 / 48)
    assert result['frames'][0]['positive_depth_mm']['median'] == 2500
    assert result['adjacent_gt']['captured_chord_length_m'] == pytest.approx(.2)
    assert result['identical_rgb_groups'] == [[1, 2]]
    assert result['human_coverage_review'] == 'pending'
    assert result['first_pass_data_verification'] == 'not_run'


@pytest.mark.parametrize('fault', ['missing', 'gt_rows', 'nonfinite', 'quaternion', 'depth8', 'corrupt', 'extra', 'link'])
def test_corrupt_inputs_fail_loud(capture, fault):
    if fault == 'missing':
        (capture / 'depth/2.png').unlink()
    elif fault in ['gt_rows', 'nonfinite', 'quaternion']:
        poses = np.load(capture / 'GT_pose.npy')
        if fault == 'gt_rows': poses = poses[:1]
        elif fault == 'nonfinite': poses[0, 0] = np.nan
        else: poses[0, 3:] = 0
        np.save(capture / 'GT_pose.npy', poses)
    elif fault == 'depth8':
        cv2.imwrite(str(capture / 'depth/1.png'), np.ones((6, 8), np.uint8))
    elif fault == 'corrupt':
        (capture / 'rgb/1.png').write_bytes(b'bad png')
    elif fault == 'extra':
        (capture / 'rgb/.DS_Store').write_bytes(b'preserve this')
    else:
        (capture / 'rgb/3.png').symlink_to(capture / 'rgb/1.png')
    before = {str(p): p.read_bytes() for p in capture.rglob('*') if p.is_file()}
    with pytest.raises(ValueError):
        inspect_capture(capture)
    assert before == {str(p): p.read_bytes() for p in capture.rglob('*') if p.is_file()}
