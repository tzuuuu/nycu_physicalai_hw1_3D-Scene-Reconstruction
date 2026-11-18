"""失敗配對不可當成已接受位姿；保留空RANSAC與其後ICP的差異。"""
import numpy as np
import pytest
from scripts.m32_failure_audit import classify


def result(coarse=5,icp=5):
    return {'coarse_correspondences':coarse,'coarse_fitness':float(coarse>0),'coarse_rmse':0.,
            'icp_correspondences':icp,'icp_fitness':float(icp>0),'icp_rmse':0.,
            'trans_init':np.eye(4).tolist(),'icp_transformation':np.eye(4).tolist()}


def test_icp_success_does_not_accept_failed_ransac():
    accepted,failed=classify([result(),result(coarse=0)])
    assert len(accepted)==1 and len(failed)==1
    assert failed[0]['icp_correspondences']==5


def test_no_continuation_after_failed_pair():
    with pytest.raises(ValueError,match='later accepted'):
        classify([result(coarse=0),result()])
