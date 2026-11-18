"""停止後審計可描述OS中繼檔差異，但不得把原護欄改成通過。"""
import pytest
from scripts import m32_status_review as r
from scripts import m32_experiments as x


def test_metadata_difference_is_reported_without_changing_original_guard(tmp_path,monkeypatch):
    monkeypatch.setattr(r,'ROOT',tmp_path); monkeypatch.setattr(x,'ROOT',tmp_path)
    d=tmp_path/'experiments'; d.mkdir(); p=d/'.DS_Store'; p.write_bytes(b'old metadata')
    hashes={'experiments/.DS_Store':x.sha(p)}
    p.write_bytes(b'new metadata')
    result=r.differences(hashes)
    assert len(result)==1 and result[0]['path']=='experiments/.DS_Store'
    assert result[0]['before']!=result[0]['after']
    with pytest.raises(RuntimeError,match='Protected'): x.verify_hashes(hashes)


def test_review_reports_missing_scientific_file_as_additional_difference(tmp_path,monkeypatch):
    monkeypatch.setattr(r,'ROOT',tmp_path)
    assert r.differences({'poses.npy':'original_hash'})==[{'path':'poses.npy','before':'original_hash','after':None}]
