"""執行紀錄工具不將程序成功誤當成產物驗證，也保留失敗輸出。"""
import importlib.util
import json
import sys
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('record_command', Path(__file__).parents[1] / 'scripts/record_command.py')
recorder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recorder)


@pytest.mark.parametrize('code', [0, 3])
def test_records_actual_exit_output_and_does_not_overwrite(tmp_path, code):
    output = tmp_path / 'record'
    result = recorder.run([sys.executable, '-c', f"print('actual child output'); raise SystemExit({code})"], output)
    assert result['exit_code'] == code
    assert result['total_process_s'] > 0
    assert 'actual child output' in (output / 'console.log').read_text()
    assert json.loads((output / 'execution.json').read_text()) == result
    assert result['status'] == ('process_completed_requires_artifact_validation' if code == 0 else 'failed')
    with pytest.raises(FileExistsError):
        recorder.run([sys.executable, '-c', 'pass'], output)
