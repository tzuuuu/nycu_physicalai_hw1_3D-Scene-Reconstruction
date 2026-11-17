"""合成 PNG 的配對、相機來源、深度編碼與失敗案例。"""
import json
import cv2
import numpy as np
import pytest
import utils


@pytest.fixture
def capture(tmp_path):
    for name in ['rgb', 'depth']:
        (tmp_path / name).mkdir()
    (tmp_path / 'intrinsics.json').write_text(json.dumps({'width': 8, 'height': 6, 'hfov': 73}))
    for stem in [20, 3, 101]:
        cv2.imwrite(str(tmp_path / 'rgb' / f'{stem}.png'), np.full((6, 8, 3), [1, 2, 3], np.uint8))
        cv2.imwrite(str(tmp_path / 'depth' / f'{stem}.png'), np.full((6, 8), 2500, np.uint16))
    return tmp_path


def test_numeric_pairing_and_capture_intrinsics(capture):
    intr, pairs, scale = utils._capture_inputs(capture, None)
    assert intr == {'width': 8, 'height': 6, 'hfov': 73}
    assert [int(p[1].split('/')[-1][:-4]) for p in pairs] == [3, 20, 101]
    assert scale == 1000
    rgb, depth = utils._read_rgbd(*pairs[0], scale)
    np.testing.assert_array_equal(rgb[0, 0], [1, 2, 3])
    np.testing.assert_allclose(depth, 2.5)


def test_selected_order_and_scale_override(capture):
    (capture / 'intrinsics.json').write_text(json.dumps({'width': 8, 'height': 6, 'hfov': 73, 'depth_scale': 500}))
    _, pairs, scale = utils._capture_inputs(capture, [101, 3])
    assert pairs[0][1].endswith('/101.png')
    assert pairs[1][1].endswith('/3.png')
    np.testing.assert_allclose(utils._read_rgbd(*pairs[0], scale)[1], 5)


@pytest.mark.parametrize('frames', [[999], [3, 3], ['3']])
def test_invalid_selection(capture, frames):
    with pytest.raises(ValueError):
        utils._capture_inputs(capture, frames)


def test_unpaired_files_are_disclosed(capture):
    (capture / 'depth' / '3.png').unlink()
    with pytest.warns(RuntimeWarning, match='Unpaired'):
        _, pairs, _ = utils._capture_inputs(capture, None)
    assert len(pairs) == 2


def test_corrupt_frame_is_disclosed(capture):
    path = capture / 'depth' / '3.png'
    path.write_bytes(b'not a PNG')
    with pytest.warns(RuntimeWarning, match='Unreadable'):
        assert utils._read_rgbd(str(capture / 'rgb' / '3.png'), str(path), 1000)[1] is None


def test_8bit_depth_is_not_misinterpreted(capture):
    path = capture / 'depth' / '3.png'
    cv2.imwrite(str(path), np.full((6, 8), 25, np.uint8))
    with pytest.raises(ValueError, match='uint16'):
        utils._read_rgbd(str(capture / 'rgb' / '3.png'), str(path), 1000)


@pytest.mark.parametrize('scale', [0, -1, '1000', float('nan')])
def test_invalid_scale(capture, scale):
    (capture / 'intrinsics.json').write_text(json.dumps({'width': 8, 'height': 6, 'hfov': 73, 'depth_scale': scale}))
    with pytest.raises(ValueError, match='depth_scale'):
        utils._capture_inputs(capture, None)
