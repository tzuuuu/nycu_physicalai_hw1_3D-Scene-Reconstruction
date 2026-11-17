"""M1.1：以合成像素驗證反投影，不讀取 capture 或 Ground Truth。"""

import numpy as np
import pytest

from utils import depth_image_to_point_cloud


def test_known_pixels_axes_and_metres():
    # 4×4、90 度時焦距為 2；涵蓋主點、四個方向及不同公尺深度。
    depth = np.zeros((4, 4))
    depth[0, 0], depth[1, 2], depth[2, 2], depth[2, 3], depth[3, 2] = 2, 2, 3, 4, 2
    cloud = depth_image_to_point_cloud(np.zeros((4, 4, 3), np.uint8), depth, 4, 4, 90)
    np.testing.assert_allclose(
        np.asarray(cloud.points),
        [[-2, -2, 2], [0, -1, 2], [0, 0, 3], [2, 0, 4], [0, 1, 2]],
        atol=1e-14,
    )


@pytest.mark.parametrize('width,height,hfov,expected', [
    (4, 2, 90, [-2, -1, 2]),
    (8, 2, 90, [-2, -0.5, 2]),
    (4, 2, 60, [-2 / np.sqrt(3), -1 / np.sqrt(3), 2]),
    (3, 5, 90, [-2, -10 / 3, 2]),
])
def test_capture_specific_intrinsics(width, height, hfov, expected):
    # 非正方形影像仍使用方形像素，垂直焦距不以影像高度另算。
    depth = np.zeros((height, width))
    depth[0, 0] = 2
    cloud = depth_image_to_point_cloud(
        np.zeros((height, width, 3), np.uint8), depth, width, height, hfov)
    np.testing.assert_allclose(np.asarray(cloud.points), [expected], atol=1e-14)


def test_invalid_depth_and_bgr_correspondence_without_mutation():
    depth = np.array([[0, 2, np.nan], [-1, np.inf, 4]], dtype=np.float32)
    rgb = np.array([[[0, 0, 0], [0, 128, 255], [255, 0, 0]],
                    [[1, 2, 3], [4, 5, 6], [255, 64, 0]]], dtype=np.uint8)
    original_depth, original_rgb = depth.copy(), rgb.copy()
    cloud = depth_image_to_point_cloud(rgb, depth, 3, 2, 90)
    np.testing.assert_allclose(np.asarray(cloud.points),
                               [[-2 / 3, -4 / 3, 2], [4 / 3, 0, 4]], atol=1e-14)
    np.testing.assert_allclose(np.asarray(cloud.colors),
                               np.array([[255, 128, 0], [0, 64, 255]]) / 255)
    np.testing.assert_array_equal(depth, original_depth)
    np.testing.assert_array_equal(rgb, original_rgb)


def test_all_invalid_returns_empty_cloud():
    cloud = depth_image_to_point_cloud(
        np.zeros((2, 3, 3), np.uint8), [[0, -1, np.nan], [np.inf, -np.inf, 0]], 3, 2, 90)
    assert np.asarray(cloud.points).shape == (0, 3)
    assert np.asarray(cloud.colors).shape == (0, 3)


@pytest.mark.parametrize('dtype', [np.float32, np.float64, np.uint16])
def test_metres_are_not_rescaled_by_dtype(dtype):
    # 單位來自 depth_m 契約，型別不能作為再除以 1000 的理由。
    cloud = depth_image_to_point_cloud(
        np.zeros((2, 2, 3), np.uint8), np.full((2, 2), 2, dtype=dtype), 2, 2, 90)
    np.testing.assert_allclose(np.asarray(cloud.points)[:, 2], 2)


@pytest.mark.parametrize('depth', [np.zeros((2, 3)), np.zeros((2, 2, 1)), np.zeros(4)])
def test_rejects_depth_shape_mismatch(depth):
    with pytest.raises(ValueError, match='Depth image shape'):
        depth_image_to_point_cloud(np.zeros((2, 2, 3), np.uint8), depth, 2, 2, 90)


@pytest.mark.parametrize('rgb', [np.zeros((2, 3, 3), np.uint8),
                              np.zeros((2, 2), np.uint8),
                              np.zeros((2, 2, 4), np.uint8)])
def test_rejects_color_shape_mismatch(rgb):
    with pytest.raises(ValueError, match='BGR image shape'):
        depth_image_to_point_cloud(rgb, np.ones((2, 2)), 2, 2, 90)


@pytest.mark.parametrize('width,height', [(0, 2), (2, -1), (2.0, 2), (True, 2)])
def test_rejects_invalid_dimensions(width, height):
    with pytest.raises(ValueError, match='positive integers'):
        depth_image_to_point_cloud(np.zeros((2, 2, 3), np.uint8), np.ones((2, 2)), width, height, 90)


@pytest.mark.parametrize('hfov', [0, -1, 180, 181, np.nan, np.inf, [90], 90 + 1j,
                                90 + 0j, '90', True])
def test_rejects_invalid_hfov(hfov):
    with pytest.raises(ValueError, match='hfov'):
        depth_image_to_point_cloud(np.zeros((2, 2, 3), np.uint8), np.ones((2, 2)), 2, 2, hfov)


def test_rejects_non_uint8_colors():
    with pytest.raises(ValueError, match='uint8'):
        depth_image_to_point_cloud(np.zeros((2, 2, 3)), np.ones((2, 2)), 2, 2, 90)


@pytest.mark.parametrize('depth', [np.full((2, 2), '2'), np.ones((2, 2), complex)])
def test_rejects_non_real_depth(depth):
    with pytest.raises(ValueError, match='real numeric'):
        depth_image_to_point_cloud(np.zeros((2, 2, 3), np.uint8), depth, 2, 2, 90)
