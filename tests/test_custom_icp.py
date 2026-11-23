"""Bonus 核心的幾何正確性、失敗回報與正式後端保全。"""
import ast
from pathlib import Path
import subprocess

import numpy as np
import open3d as o3d
import pytest
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
import utils


def cloud(points):
    result = o3d.geometry.PointCloud()
    result.points = o3d.utility.Vector3dVector(points)
    return result


def test_custom_recovers_pose_and_final_metrics_without_open3d_icp(monkeypatch):
    rng = np.random.default_rng(123)
    points = rng.uniform(-1, 1, (500, 3))
    rotation = Rotation.from_euler('xyz', [2, -1, 3], degrees=True).as_matrix()
    shift = np.array([.02, -.03, .01])
    target = points @ rotation.T + shift
    source_cloud, target_cloud = cloud(points), cloud(target)
    initial = np.eye(4)
    def forbidden(*args, **kwargs):
        raise AssertionError('Custom backend must not delegate to Open3D ICP')
    monkeypatch.setattr(o3d.pipelines.registration, 'registration_icp', forbidden)
    result = utils.my_local_icp_algorithm(source_cloud, target_cloud, initial, .15)
    assert result.success and result.termination_reason == 'converged'
    np.testing.assert_allclose(result.transformation[:3, :3], rotation, atol=1e-10)
    np.testing.assert_allclose(result.transformation[:3, 3], shift, atol=1e-10)
    np.testing.assert_array_equal(np.asarray(source_cloud.points), points)
    np.testing.assert_array_equal(np.asarray(target_cloud.points), target)
    np.testing.assert_array_equal(initial, np.eye(4))
    moved = points @ result.transformation[:3, :3].T + result.transformation[:3, 3]
    distance, index = cKDTree(target).query(moved)
    keep = distance < .225
    np.testing.assert_array_equal(result.correspondence_set,
                                  np.column_stack([np.flatnonzero(keep), index[keep]]))
    assert result.fitness == keep.mean()
    assert result.inlier_rmse == pytest.approx(np.sqrt(np.mean(distance[keep] ** 2)), abs=1e-15)


def test_reflection_cannot_produce_improper_rotation():
    points = np.random.default_rng(19).normal(size=(80, 3))
    reflected = points * [-1, 1, 1]
    result = utils.my_local_icp_algorithm(cloud(points), cloud(reflected), np.eye(4), 5.)
    assert np.linalg.det(result.transformation[:3, :3]) == pytest.approx(1., abs=1e-12)


def test_nonidentity_ransac_initialization_and_left_composed_updates():
    points = np.random.default_rng(31).uniform(-1, 1, (500, 3))
    rotation = Rotation.from_euler('xyz', [25, -12, 85], degrees=True).as_matrix()
    shift = np.array([3., -2., 1.])
    initial = np.eye(4)
    initial[:3, :3] = Rotation.from_euler('xyz', [24, -11, 84], degrees=True).as_matrix()
    initial[:3, 3] = shift + [.01, -.01, .02]
    result = utils.my_local_icp_algorithm(cloud(points), cloud(points @ rotation.T + shift), initial, .15)
    assert result.success
    np.testing.assert_allclose(result.transformation[:3, :3], rotation, atol=1e-10)
    np.testing.assert_allclose(result.transformation[:3, 3], shift, atol=1e-10)


def test_distance_gate_excludes_source_outliers():
    points = np.random.default_rng(32).uniform(-1, 1, (100, 3))
    source = np.vstack([points, [[50., 50., 50.], [60., 50., 50.]]])
    result = utils.my_local_icp_algorithm(cloud(source), cloud(points), np.eye(4), .05)
    assert result.success and len(result.correspondence_set) == 100
    assert result.fitness == pytest.approx(100/102)


def test_insufficient_and_degenerate_support_are_not_success():
    points = np.random.default_rng(2).normal(size=(20, 3))
    result = utils.my_local_icp_algorithm(cloud(points), cloud(points + 100), np.eye(4), .05)
    assert not result.success and result.termination_reason == 'insufficient_correspondences'
    assert result.fitness == 0 and result.correspondence_set.shape == (0, 2)
    line = np.column_stack([np.arange(20), np.zeros((20, 2))])
    result = utils.my_local_icp_algorithm(cloud(line), cloud(line), np.eye(4), .05)
    assert not result.success and result.termination_reason == 'degenerate_correspondences'


@pytest.mark.parametrize('voxel', [0, -1, float('nan'), float('inf'), True])
def test_invalid_voxel(voxel):
    points = cloud(np.eye(3))
    with pytest.raises(ValueError, match='voxel_size'):
        utils.my_local_icp_algorithm(points, points, np.eye(4), voxel)


def test_nonrigid_initialization_rejected():
    points = cloud(np.random.default_rng(2).normal(size=(20, 3)))
    with pytest.raises(ValueError, match='SE'):
        utils.my_local_icp_algorithm(points, points, np.diag([2., 1, 1, 1]), .05)


def test_original_open3d_function_is_byte_for_byte_preserved():
    root = Path(__file__).resolve().parents[1]
    original = subprocess.check_output(['git', 'show', 'HEAD:utils.py'], cwd=root, text=True)
    def extract(text):
        node = next(n for n in ast.parse(text).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'local_icp_algorithm')
        return ''.join(text.splitlines(keepends=True)[node.lineno-1:node.end_lineno])
    assert extract(original) == extract((root/'utils.py').read_text())
