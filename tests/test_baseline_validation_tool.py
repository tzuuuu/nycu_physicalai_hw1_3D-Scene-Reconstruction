"""診斷工具以原始因素值統計，拒絕非有限量測。"""
import importlib.util
from pathlib import Path
import pytest
spec = importlib.util.spec_from_file_location('validate_baseline', Path(__file__).parents[1] / 'scripts/validate_baseline.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def test_summarize_records_keeps_frame_identity():
    rows = [{'factor': 'ICPInlierFitness', 'current': 3, 'value': 0.25},
            {'factor': 'ICPInlierFitness', 'current': 7, 'value': 0.75}]
    summary = validator.summarize_rows(rows)['ICPInlierFitness']
    assert summary['mean'] == 0.5 and summary['count'] == 2
    assert summary['min_frames'] == [3] and summary['max_frames'] == [7]


def test_nonfinite_factors_cannot_be_reported_as_valid():
    with pytest.raises(ValueError, match='Non-finite'):
        validator.summarize_rows([{'factor': 'ICPInlierFitness', 'current': 3, 'value': float('nan')}])
