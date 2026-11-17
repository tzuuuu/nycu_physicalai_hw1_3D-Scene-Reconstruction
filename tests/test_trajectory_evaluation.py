"""已知首姿態與非連續影格的固定參考系評分。"""
import json
import numpy as np
import open3d as o3d
import pytest
from scipy.spatial.transform import Rotation
import utils


@pytest.fixture
def trajectory(tmp_path):
    for kind in ['rgb', 'depth']:
        (tmp_path / kind).mkdir()
        for stem in [3, 20, 101, 205]:
            (tmp_path / kind / f'{stem}.png').touch()
    # 評估不讀取 PNG 或相機內參，只需要影格身分與 GT。
    local = np.array([[0, 0, 0], [1, 2, 0], [2, 1, -3], [4, 2, -1]], float)
    rotation = Rotation.from_euler('xyz', [20, 35, 70], degrees=True)
    world = local @ rotation.as_matrix().T + [7, -3, 11]
    quaternion = rotation.as_quat()[[3, 0, 1, 2]]
    gt = np.column_stack((world, np.tile(quaternion, (4, 1))))
    np.save(tmp_path / 'GT_pose.npy', gt)
    return tmp_path, local @ utils.CAM_TO_GT_AXES, gt


def test_nonzero_reference_position_and_rotation(trajectory):
    path, predicted, _ = trajectory
    assert utils.visualize_and_evaluate(None, predicted, path, show=False) == pytest.approx(0, abs=1e-14)


def test_nonconsecutive_numbering_and_requested_order(trajectory):
    path, predicted, _ = trajectory
    result = utils.visualize_and_evaluate(None, predicted[[0, 3, 1]], path,
                                          frames=[3, 205, 20], show=False)
    assert result == pytest.approx(0, abs=1e-14)


def test_known_error_is_not_fitted_away(trajectory):
    path, predicted, _ = trajectory
    assert utils.visualize_and_evaluate(None, predicted + [3, 4, 0], path, show=False) == pytest.approx(5)


def test_missing_selected_gt_rows_keep_prediction_indices(trajectory):
    path, predicted, gt = trajectory
    np.save(path / 'GT_pose.npy', gt[:2])
    assert utils.visualize_and_evaluate(None, predicted[[0, 3, 1]], path,
                                       frames=[3, 205, 20], show=False) == pytest.approx(0, abs=1e-14)


def test_selected_without_original_reference_is_rejected(trajectory):
    path, predicted, _ = trajectory
    with pytest.raises(ValueError, match='first frame'):
        utils.visualize_and_evaluate(None, predicted[1:], path, frames=[20, 101, 205], show=False)


def test_missing_gt_and_empty_predictions(trajectory):
    path, predicted, _ = trajectory
    assert np.isinf(utils.visualize_and_evaluate(None, None, path, show=False))
    assert np.isinf(utils.visualize_and_evaluate(None, predicted[:-1], path, show=False))
    np.save(path / 'GT_pose.npy', np.empty((0, 7)))
    assert np.isinf(utils.visualize_and_evaluate(None, predicted, path, show=False))
    (path / 'GT_pose.npy').unlink()
    assert np.isinf(utils.visualize_and_evaluate(None, predicted, path, show=False))


def test_visualization_colors_axes_and_input_preservation(trajectory, monkeypatch):
    path, predicted, _ = trajectory
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector([[1, 2, 3]])
    seen = []
    monkeypatch.setattr(o3d.visualization, 'draw_geometries', lambda geoms, **kwargs: seen.extend(geoms))
    utils.visualize_and_evaluate(pcd, predicted[[0, 2]], path, frames=[3, 101], show=True)
    assert len(seen) == 3
    np.testing.assert_array_equal(np.asarray(seen[0].points), [[1, -2, -3]])
    np.testing.assert_array_equal(np.asarray(pcd.points), [[1, 2, 3]])
    np.testing.assert_array_equal(np.asarray(seen[1].colors), [[1, 0, 0]])
    np.testing.assert_array_equal(np.asarray(seen[2].colors), [[0, 0, 0]])
    np.testing.assert_allclose(np.asarray(seen[1].points), np.asarray(seen[2].points), atol=1e-14)


def test_headless_never_opens_visualizer(trajectory, monkeypatch):
    path, predicted, _ = trajectory
    def fail(*args, **kwargs):
        pytest.fail('headless evaluation opened a window')
    monkeypatch.setattr(o3d.visualization, 'draw_geometries', fail)
    utils.visualize_and_evaluate(None, predicted, path, show=False)
