"""純顯示規則不擬合、修改或隱藏錯誤場景。"""
import numpy as np
import pytest
from scripts.phase1_report_assets import uniform_points,shared_bounds


def test_saved_cloud_sampling_is_deterministic_and_does_not_modify_source():
    points=np.arange(60,dtype=float).reshape(20,3);before=points.copy()
    actual=uniform_points(points,limit=4)
    np.testing.assert_array_equal(actual,points[[0,6,12,19]])
    np.testing.assert_array_equal(points,before)


def test_common_bounds_include_bad_map_and_both_trajectories():
    runs=[dict(points=np.array([[0,0,0],[2,0,2]]),pred=np.array([[20,0,-30]]),gt=np.array([[-2,0,3]]))]
    assert shared_bounds(runs)==[-3.,21.,-31.,4.]


def test_render_sampling_rejects_nonfinite_geometry():
    with pytest.raises(ValueError):uniform_points(np.array([[0.,np.nan,0.]]))
