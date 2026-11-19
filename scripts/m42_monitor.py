"""Process-tree RSS guard; an independent heartbeat watchdog fails closed.

Only the new workload session is signalled. RSS is sampled, not a hard OS cap.
The supervisor/watchdog are outside the scientific workload RSS measurement.
"""
import argparse
import json
import math
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
import traceback

INTERVAL = .5
WATCHDOG_TIMEOUT = 8.


def json_value(value):
    if isinstance(value,float) and not math.isfinite(value):
        return {'nonfinite_float':repr(value)}
    if isinstance(value,dict): return {k:json_value(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [json_value(v) for v in value]
    return value


def write(path, value):
    with Path(path).open('x') as f:
        json.dump(json_value(value), f, indent=2, allow_nan=False)
        f.write('\n')


def append(path, value):
    with Path(path).open('a') as f:
        f.write(json.dumps(json_value(value), allow_nan=False) + '\n')
        f.flush()


def process_table():
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,rss=,stat='],
                            capture_output=True, text=True, timeout=2, check=True)
    table = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) != 5:
            raise RuntimeError('Unreadable ps row: ' + repr(line))
        pid, ppid, pgid, rss = map(int, fields[:4])
        if pid in table or min(pid, ppid, pgid) < 0 or rss < 0:
            raise RuntimeError('Invalid ps data')
        table[pid] = dict(pid=pid, ppid=ppid, pgid=pgid, rss_bytes=rss*1024,
                          state=fields[4])
    if os.getpid() not in table:
        raise RuntimeError('ps cannot read the monitor itself')
    return table


def tree_sample(table, root, pgid, known=()):
    # Also retain session group members after the root exits/reparents children.
    selected = {p for p, r in table.items() if r['pgid'] == pgid}
    selected.update(p for p in known if p in table)
    if root in table:
        selected.add(root)
    while True:
        more = {p for p, r in table.items() if r['ppid'] in selected}
        if more <= selected:
            break
        selected.update(more)
    rows = [table[p] for p in sorted(selected) if not table[p]['state'].startswith('Z')]
    if any(r['pgid'] != pgid for r in rows):
        raise RuntimeError('Workload descendant escaped its process group')
    if any(r['rss_bytes'] <= 0 for r in rows):
        raise RuntimeError('Live workload PID has unreadable/nonpositive RSS')
    return rows


def kill_group(pgid):
    if pgid <= 1 or pgid == os.getpgrp():
        raise RuntimeError('Refuse unsafe process group')
    # SIGKILL prevents a TERM handler from spawning children or ignoring the stop.
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def watchdog(fd, pgid, output):
    last = time.monotonic()
    reason = None
    try:
        while True:
            ready, _, _ = select.select([fd], [], [], .25)
            if ready:
                data = os.read(fd, 4096)
                if not data:
                    reason = 'supervisor pipe closed unexpectedly'
                    break
                if b'D' in data:
                    write(Path(output)/'watchdog.json', {'status':'disarmed_after_workload_exit'})
                    return
                last = time.monotonic()
            if time.monotonic()-last > WATCHDOG_TIMEOUT:
                reason = 'supervisor heartbeat timeout'
                break
    except BaseException:
        reason = traceback.format_exc()
    finally:
        os.close(fd)
    kill_group(pgid)
    write(Path(output)/'watchdog.json', {'status':'terminated_workload', 'reason':reason,
                                        'pgid':pgid, 'unix':time.time()})


def run(argv, output, limit_bytes=3*2**30, *, sampler=process_table, crash_after=None):
    """Launch once, sample whole tree, preserve logs even on any supervisor error.

    sampler/crash_after are explicit synthetic fault injection seams, never CLI options.
    """
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    peak = 0
    count = 0
    reason = None
    worker = guard = None
    control = gate_write = None
    known = set()
    try:
        sampler()  # No workload is launched if permissions already fail.
        gate_read, gate_write = os.pipe()
        wrapper = ('import os,sys; fd=int(sys.argv[1]); '
                   'token=os.read(fd,1); os.close(fd); '
                   'token==b"G" or sys.exit(125); os.execvpe(sys.argv[2],sys.argv[2:],os.environ)')
        stdout = (output/'stdout.log').open('xb')
        stderr = (output/'stderr.log').open('xb')
        try:
            worker = subprocess.Popen([sys.executable,'-c',wrapper,str(gate_read)]+list(argv),
                pass_fds=(gate_read,), start_new_session=True, stdout=stdout, stderr=stderr)
        finally:
            os.close(gate_read)
            stdout.close(); stderr.close()
        read_fd, control = os.pipe()
        try:
            guard = subprocess.Popen([sys.executable,str(Path(__file__).resolve()),
                '_watchdog',str(read_fd),str(worker.pid),str(output.resolve())],
                pass_fds=(read_fd,), start_new_session=True)
        finally:
            os.close(read_fd)
        write(output/'started.json', {'argv':list(argv),'pid':worker.pid,'pgid':worker.pid,
            'watchdog_pid':guard.pid,'unix':time.time(),'limit_bytes':limit_bytes})
        first = True
        while True:
            tick = time.monotonic()
            if guard.poll() is not None:
                raise RuntimeError('Independent watchdog exited unexpectedly')
            os.write(control,b'H')
            table = sampler()
            rows = tree_sample(table,worker.pid,worker.pid,known)
            known.update(r['pid'] for r in rows)
            live = worker.poll() is None
            if live and worker.pid not in table:
                # Re-poll handles a process ending between ps snapshot and waitpid.
                if worker.poll() is None:
                    raise RuntimeError('Required workload PID missing from ps')
            total = sum(r['rss_bytes'] for r in rows)
            peak = max(peak,total)
            append(output/'rss.jsonl', {'elapsed_s':time.monotonic()-start,'unix':time.time(),
                'pids':rows,'tree_rss_bytes':total,'peak_tree_rss_bytes':peak})
            count += 1
            if total > limit_bytes:
                raise MemoryError('Process-tree RSS exceeds limit: %d > %d' % (total,limit_bytes))
            if first:
                os.write(gate_write,b'G'); os.close(gate_write); gate_write=None
                first = False
            if crash_after is not None and count >= crash_after:
                os._exit(91)  # Only used in disposable synthetic supervisor tests.
            if not live and not rows:
                break
            time.sleep(max(0,INTERVAL-(time.monotonic()-tick)))
    except BaseException:
        reason = traceback.format_exc()
        if worker is not None:
            kill_group(worker.pid)
        (output/'failure.traceback.txt').write_text(reason)
    finally:
        if gate_write is not None:
            os.close(gate_write)
        if worker is not None:
            if reason:
                kill_group(worker.pid)
            worker.wait(timeout=5)
        if guard is not None:
            # Only disarm after workload exit, or after forced whole-group kill.
            if guard.poll() is None:
                try:
                    os.write(control,b'D')
                    guard.wait(timeout=3)
                except BaseException:
                    kill_group(worker.pid)
                    reason = (reason or '') + '\nWatchdog disarm failed: '+traceback.format_exc()
            elif reason is None:
                kill_group(worker.pid)
                reason = 'Watchdog unexpectedly stopped'
        if control is not None:
            os.close(control)
    result = {'argv':list(argv),'exit_code':worker.returncode if worker else None,
        'reason':reason,'passed':worker is not None and worker.returncode==0 and reason is None,
        'elapsed_s':time.monotonic()-start,'peak_tree_rss_bytes':peak,'samples':count,
        'interval_s':INTERVAL,'watchdog_timeout_s':WATCHDOG_TIMEOUT,
        'method':'ps pid/ppid/pgid/rss/stat; live descendants + retained process group; KiB*1024',
        'limitations':'0.5 s sampled conservative sum; shared pages counted per PID; transient peaks may be missed; watchdog timeout up to 8 s'}
    write(output/'execution.json',result)
    return result


if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=='_watchdog':
        watchdog(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4])
    else:
        parser=argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--output',required=True)
        parser.add_argument('command',nargs=argparse.REMAINDER)
        args=parser.parse_args()
        command=args.command[1:] if args.command[:1]==['--'] else args.command
        if not command: parser.error('command required')
        sys.exit(0 if run(command,args.output)['passed'] else 1)
