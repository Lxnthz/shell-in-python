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
    state.jobs[job_num] = {"pid": pid, "cmd": " ".join(args), "status": "running"}
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
    print(f"\n[{num}]+ Done                {info['cmd']}")
  
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
        _print_job(n, state.jobs[n], is_last=(n == nums[-1]))
      else:
        print(f"jobs: {args[1]}: no such job", file=sys.stderr)
      return

  for n in nums:
    _print_job(n, state.jobs[n], is_last=(n == nums[-1]))

def _print_job(num, info, is_last=False):
  marker = '+' if is_last else '-'
  status = info["status"].capitalize()
  print(f"[{num}]{marker}  {status:<20} {info['cmd']}")