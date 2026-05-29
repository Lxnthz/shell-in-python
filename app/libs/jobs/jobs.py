import os
import sys
import signal
from .. import state

def _next_job_num() -> int:
  used = set(state.jobs.keys())
  n = 1
  while n in used:
    n += 1
  return n

def start_background_job(args: list[str]) -> int:
  job_num = _next_job_num()
  pid = os.fork()
  if pid == 0:
    os.setpgid(0, 0)
    try:
      os.execvp(args[0], args)
    except Exception:
      print(f"{args[0]}: command not found", file=sys.stderr)
      os.exit(127)
  else:
    os.setpgid(pid, pid)
    cmd_str = " ".join(args) + " &"
    state.jobs[job_num] = {"pid": pid, "cmd": cmd_str, "status": "running"}
    print(f"[{job_num}] {pid}")
    return job_num

def reap_jobs():
  finished = []
  for num, info in list(state.jobs.items()):
    if info["status"] == "running":
      try:
        wpid, wstatus = os.waitpid(info["pid"], os.WNOHANG)
        if wpid != 0:
          info["status"] = "done"
          finished.append(num)
      except ChildProcessError:
        info["status"] = "done"
        finished.append(num)

  for num in sorted(finished):
    info = state.jobs[num]
    cmd = info['cmd']
    if cmd.endswith(' &'):
      cmd = cmd[:-2]
    print(f"[{num}]+  Done                 {cmd}")
  
  for num in finished:
    del state.jobs[num]

def handle_jobs(args: list[str]):
  reap_jobs()
  if not state.jobs:
    return
  
  nums = sorted(state.jobs.keys())

  if len(args) > 1:
    target = args[1].lstrip('%')
    if target.isdigit():
      n = int(target)
      if n in state.jobs:
        marker = '+' if n == nums[-1] else ('-' if len(nums) > 1 and n == nums[-2] else ' ')
        _print_job(n, state.jobs[n], marker)
      else:
        print(f"jobs: {args[1]}: no such job", file=sys.stderr)
      return

  for n in nums:
    marker = '+' if n == nums[-1] else ('-' if len(nums) > 1 and n == nums[-2] else ' ')
    _print_job(n, state.jobs[n], marker)

def _print_job(num, info, marker):
  status = info["status"].capitalize()
  print(f"[{num}]{marker}  {status:<24} {info['cmd']}")