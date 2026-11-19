"""Synthetic guard faults and native macOS process-tree tests (no real Capture)."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest
from scripts import m42_monitor as m


def test_tree_includes_children_and_reparented_group_excludes_unrelated():
    def row(pid,ppid,pgid,rss):
        return dict(pid=pid,ppid=ppid,pgid=pgid,rss_bytes=rss,state='S')
    table={r['pid']:r for r in [row(100,1,100,10),row(101,100,100,20),
        row(102,101,100,30),row(103,1,100,40),row(200,1,200,999)]}
    rows=m.tree_sample(table,100,100)
    assert [r['pid'] for r in rows]==[100,101,102,103]
    assert sum(r['rss_bytes'] for r in rows)==100
    table[102]['pgid']=102
    with pytest.raises(RuntimeError,match='escaped'): m.tree_sample(table,100,100)
    table[102]['pgid']=100; table[102]['rss_bytes']=0
    with pytest.raises(RuntimeError,match='RSS'): m.tree_sample(table,100,100)


def test_permission_denied_before_launch_leaves_evidence(tmp_path):
    def denied(): raise PermissionError('synthetic ps denied')
    out=tmp_path/'denied'
    r=m.run([sys.executable,'-c','raise Exception("must not run")'],out,sampler=denied)
    assert not r['passed'] and r['exit_code'] is None and r['samples']==0
    assert 'synthetic ps denied' in r['reason']
    assert (out/'execution.json').exists() and (out/'failure.traceback.txt').exists()
    assert not (out/'started.json').exists()


@pytest.fixture(scope="session")
def native():
    if os.environ.get("M42_SKIP_NATIVE")=="1":
        pytest.skip("Known Codex ps restriction; native tests deferred to Terminal")
    # Only the permission probe can skip. Functional failures never become skips.
    try: m.process_table()
    except (PermissionError,subprocess.CalledProcessError) as e:
        if os.environ.get('M42_REQUIRE_NATIVE')=='1': pytest.fail('Native ps required: '+repr(e))
        pytest.skip('Native process-table permission unavailable in Codex sandbox')


def alive(pid):
    table=m.process_table()
    return pid in table and not table[pid]['state'].startswith('Z')


def test_native_single_exit_code_and_partial_stdout(native,tmp_path):
    r=m.run([sys.executable,'-c','import time; print("partial evidence",flush=True); time.sleep(1.2); raise SystemExit(7)'],tmp_path/'single')
    assert r['exit_code']==7 and r['reason'] is None and r['samples']>=3
    assert 'partial evidence' in (tmp_path/'single/stdout.log').read_text()
    good=m.run([sys.executable,'-c','import time; time.sleep(.7)'],tmp_path/'normal')
    assert good['passed'] and good['exit_code']==0


def workload_code():
    return ('import os,subprocess,sys,time; x=bytearray(12*2**20); '
        'print(os.getpid(),flush=True); '
        '[subprocess.Popen([sys.executable,"-c","import os,time; x=bytearray(24*2**20); print(os.getpid(),flush=True); time.sleep(2)"]) for _ in range(2)]; '
        'time.sleep(1.7)')


def test_native_multichild_sum_and_root_exits_before_children(native,tmp_path):
    r=m.run([sys.executable,'-c',workload_code()],tmp_path/'tree')
    assert r['passed']
    samples=[json.loads(s) for s in (tmp_path/'tree/rss.jsonl').read_text().splitlines()]
    rich=[s for s in samples if len(s['pids'])>=3]
    assert rich and max(s['tree_rss_bytes'] for s in rich)>60*2**20
    for s in samples: assert s['tree_rss_bytes']==sum(p['rss_bytes'] for p in s['pids'])
    assert not any(alive(int(p)) for p in (tmp_path/'tree/stdout.log').read_text().split())


def test_native_limit_kills_whole_group_not_unrelated(native,tmp_path):
    unrelated=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],start_new_session=True)
    try:
        r=m.run([sys.executable,'-c',workload_code()],tmp_path/'limit',limit_bytes=48*2**20)
        assert not r['passed'] and 'exceeds' in r['reason']
        pids=[int(p) for p in (tmp_path/'limit/stdout.log').read_text().split()]
        assert len(pids)==3 and not any(alive(p) for p in pids)
        assert unrelated.poll() is None
        assert (tmp_path/'limit/execution.json').is_file()
    finally: unrelated.kill(); unrelated.wait()


def test_native_monitor_read_failure_after_start(native,tmp_path):
    calls=[0]
    def broken():
        calls[0]+=1
        if calls[0]>=4: raise PermissionError('injected live ps denial')
        return m.process_table()
    r=m.run([sys.executable,'-c',workload_code()],tmp_path/'broken',sampler=broken)
    assert 'injected live ps denial' in r['reason'] and not r['passed']
    assert not any(alive(int(p)) for p in (tmp_path/'broken/stdout.log').read_text().split())


def test_native_unexpected_supervisor_exit_watchdog_kills_tree(native,tmp_path):
    out=tmp_path/'crash'
    script=('from scripts.m42_monitor import run; import sys; '
        'run([sys.executable,"-c",'+repr(workload_code())+'],'+repr(str(out))+',crash_after=3)')
    p=subprocess.run([sys.executable,'-c',script])
    assert p.returncode==91
    for _ in range(40):
        if (out/'watchdog.json').exists(): break
        time.sleep(.1)
    receipt=json.loads((out/'watchdog.json').read_text())
    assert receipt['status']=='terminated_workload'
    assert (out/'rss.jsonl').is_file()
    assert not any(alive(int(pid)) for pid in (out/'stdout.log').read_text().split())


def test_native_watchdog_unexpected_exit_terminates_workload(native,tmp_path):
    out=tmp_path/'dead_watchdog'
    killed=[False]
    def sampler():
        path=out/'started.json'
        if path.exists() and not killed[0]:
            os.kill(json.loads(path.read_text())['watchdog_pid'],signal.SIGKILL)
            killed[0]=True
        return m.process_table()
    r=m.run([sys.executable,'-c','import time; time.sleep(30)'],out,sampler=sampler)
    assert killed[0] and not r['passed'] and 'watchdog' in r['reason'].lower()
    assert r['exit_code']!=0


def test_nonfinite_failure_values_are_saved_without_fake_numeric_replacements(tmp_path):
    path=tmp_path/'nonfinite.jsonl'
    m.append(path,dict(fitness=float('nan'),transformation=[[float('inf')]],valid=False))
    row=json.loads(path.read_text())
    assert row['fitness']=={'nonfinite_float':'nan'}
    assert row['transformation']==[[{'nonfinite_float':'inf'}]]
    assert row['valid'] is False


def test_process_table_accepts_kernel_pid_zero_and_rejects_malformed_rows(monkeypatch):
    from types import SimpleNamespace
    pid=os.getpid()
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='0 0 0 0 Ss\n%d 1 %d 123 S\n'%(pid,pid)))
    table=m.process_table()
    assert table[0]['rss_bytes']==0 and table[pid]['rss_bytes']==123*1024
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='unreadable row\n'))
    with pytest.raises(RuntimeError,match='Unreadable'): m.process_table()


@pytest.mark.parametrize('disarm',[False,True])
def test_independent_watchdog_pipe_exit_and_disarm_without_ps(tmp_path,disarm):
    out=tmp_path/'watchdog';out.mkdir()
    worker=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],start_new_session=True)
    read_fd,write_fd=os.pipe()
    try:
        guard=subprocess.Popen([sys.executable,str(Path(m.__file__).resolve()),'_watchdog',str(read_fd),str(worker.pid),str(out)],pass_fds=(read_fd,))
        os.close(read_fd);read_fd=None
        if disarm: os.write(write_fd,b'D')
        os.close(write_fd);write_fd=None
        assert guard.wait(timeout=5)==0
        receipt=json.loads((out/'watchdog.json').read_text())
        if disarm:
            assert receipt['status']=='disarmed_after_workload_exit' and worker.poll() is None
        else:
            assert receipt['status']=='terminated_workload' and worker.wait(timeout=5)==-signal.SIGKILL
    finally:
        if read_fd is not None: os.close(read_fd)
        if write_fd is not None: os.close(write_fd)
        if worker.poll() is None: worker.kill()
        worker.wait()


def test_darwin_repeated_kill_of_zombie_group_is_verified_not_false_permission_failure(tmp_path,monkeypatch):
    worker=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],start_new_session=True)
    try:
        m.kill_group(worker.pid)
        time.sleep(.05)  # Do not reap: Darwin retains a zombie-only group and returns EPERM.
        monkeypatch.setattr(m,'process_table',lambda:{worker.pid:dict(pid=worker.pid,ppid=os.getpid(),
            pgid=worker.pid,rss_bytes=0,state='Z')})
        result=m.kill_group(worker.pid)
        assert result['status'] in ['no_live_members_verified','group_absent']
        assert worker.wait(timeout=5)==-signal.SIGKILL
    finally:
        if worker.poll() is None: worker.kill()
        worker.wait()


def test_real_permission_denial_for_live_group_is_never_ignored(monkeypatch):
    def denied(*args): raise PermissionError('synthetic live-group denial')
    monkeypatch.setattr(m.os,'killpg',denied)
    monkeypatch.setattr(m,'process_table',lambda:{34567:dict(pid=34567,ppid=1,pgid=34567,rss_bytes=0,state='Z'),
        34568:dict(pid=34568,ppid=1,pgid=34567,rss_bytes=1024,state='S')})
    with pytest.raises(PermissionError,match='live-group denial'): m.kill_group(34567)


def test_denied_cleanup_with_unreadable_process_table_fails_closed(monkeypatch):
    def denied(*args): raise PermissionError('synthetic denial')
    monkeypatch.setattr(m.os,'killpg',denied)
    monkeypatch.setattr(m,'process_table',denied)
    with pytest.raises(PermissionError): m.kill_group(34567)


def test_missing_pid_information_does_not_turn_denial_into_success(monkeypatch):
    def denied(*args): raise PermissionError('required group information unavailable')
    monkeypatch.setattr(m.os,'killpg',denied)
    monkeypatch.setattr(m,'process_table',lambda:{})
    with pytest.raises(PermissionError,match='unavailable'): m.kill_group(34567)
