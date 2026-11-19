import json
from pathlib import Path
import pytest
from scripts import m42_integrity as i


def test_strict_source_and_unknown_file_inventory(tmp_path,monkeypatch):
    monkeypatch.setattr(i,'ROOT',tmp_path)
    p=tmp_path/'source'; p.write_text('one')
    assert i.verify({'source':i.sha(p)},tmp_path)==1
    before=i.inventory([tmp_path])
    (tmp_path/'unknown').write_text('not metadata')
    with pytest.raises(RuntimeError,match='inventory changed'):
        i.compare(before,i.inventory([tmp_path]),tmp_path/'log')
    p.write_text('two')
    with pytest.raises(RuntimeError,match='SHA'): i.verify({'source':before['scientific']['source']},tmp_path)


def test_finder_only_exact_name_type_header_and_no_links(tmp_path,monkeypatch):
    p=tmp_path/'.DS_Store'; p.write_bytes(b'\0\0\0\1Bud1'+bytes(4096))
    monkeypatch.setattr(i,'ROOT',tmp_path)
    old=i.inventory([tmp_path])
    p.write_bytes(p.read_bytes()+b'changed')
    new=i.inventory([tmp_path])
    assert i.compare(old,new,tmp_path/'meta.jsonl')==0
    row=json.loads((tmp_path/'meta.jsonl').read_text())
    assert row['changed'] and row['before']['sha256']!=row['after']['sha256']
    p.write_bytes(b'not finder')
    with pytest.raises(RuntimeError,match='Finder'): i.metadata(p)
    p.unlink(); p.symlink_to(tmp_path/'meta.jsonl')
    with pytest.raises(ValueError,match='符號連結'): i.metadata(p)


def test_manifest_is_not_itself_in_inventory(tmp_path,monkeypatch):
    monkeypatch.setattr(i,'ROOT',tmp_path)
    (tmp_path/'a').write_text('one')
    manifest=tmp_path/'manifest.json'
    data=i.inventory([tmp_path],exclude=[manifest])
    i.write(manifest,data)
    assert 'manifest.json' not in data['scientific']
    assert i.inventory([tmp_path],exclude=[manifest])==data
