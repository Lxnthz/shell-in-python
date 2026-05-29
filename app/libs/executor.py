"""Execute external commands and pipelines"""

import subprocess
import os
import sys
import subprocess
from .parser import parse_redirection, parse_command
from .builtins import (handle_echo, handle_pwd, handle_cd, handle_type, handle_history, handle_declare)
from .jobs import handle_jobs
from . import state

def execute_command(args, redirect_stdout=None, redirect_stderr=None, append_stdout=False, append_stderr=False, stdin_pipe=None, stdout_pipe=None):
  try:
    stdin_arg = stdin_pipe or None
    stdout_arg = stdout_pipe or None
    stderr_arg = None

    if redirect_stdout and not stdout_pipe:
      stdout_arg = open(redirect_stdout, 'a' if append_stdout else 'w')
    if redirect_stderr:
      stderr_arg = open(redirect_stderr, 'a' if append_stderr else 'w')

    result = subprocess.run(args, stdin=stdin_arg, stdout=stdout_arg, stderr=stderr_arg, text=True)

    if redirect_stdout and stdout_arg and not stdout_pipe:
      stdout_arg.close()
    if redirect_stderr and stderr_arg:
      stderr_arg.close()

    return result.returncode
  except FileNotFoundError:
    print(f"{args[0]}: command not found", file=sys.stderr)
    return 127
  except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    return 1

def execute_pipeline(command_str: str):
  """Fork-exec pipeline of commands connected with pipes"""
  commands = [c.strip() for c in command_str.split('|')]
  processes = []
  prev_pipe = None

  for i, cmd in enumerate(commands):
    args = parse_command(cmd)
    if not args:
      continue
    parsed = parse_redirection(args)
    if parsed is None:
      continue

    args = parsed['args']
    redir = {k: parsed[k] for k in ('redirect_stdout', 'redirect_stderr', 'append_stdout', 'append_stderr')}
    is_last = (i == len(commands) - 1)
    
    read_pipe, write_pipe = (None, None) if is_last else os.pipe()

    pid = os.fork()
    if pid == 0:
      try:
        if prev_pipe is not None:
          os.dup2(prev_pipe, 0); os.close(prev_pipe)
        if write_pipe is not None and not redir['redirect_stdout']:
          os.dup2(write_pipe, 1); os.close(write_pipe); os.close(read_pipe)
        elif write_pipe is not None:
          os.close(write_pipe); os.close(read_pipe)

        if redir['redirect_stdout']:
          fd = os.open(redir['redirect_stdout'],
                        os.O_WRONLY | os.O_CREAT | (os.O_APPEND if redir['append_stdout'] else os.O_TRUNC),
                        0o644
                      )
          os.dup2(fd, 1); os.close(fd)
        
        if redir['redirect_stderr']:
          fd = os.open(redir['redirect_stderr'],
                        os.O_WRONLY | os.O_CREAT | (os.O_APPEND if redir['append_stderr'] else os.O_TRUNC),
                        0o644
                      )
          os.dup2(fd, 2); os.close(fd)

        _run_in_child(args)
      except Exception:
        print(f"{args[0]}: command not found", file=sys.stderr)
        os.exit(127)
    
    if prev_pipe is not None:
      os.close(prev_pipe)
    if write_pipe is not None:
      os.close(write_pipe)

    prev_pipe = read_pipe
    processes.append(pid)
  
  for pid in processes:
    os.waitpid(pid, 0)

def _run_in_child(args):
  """Dispatch builtins or exec external; always exits"""
  dispatch = {
    "echo": lambda: (sys.stdout.write(' '.join(args[1:]) + '\n'), sys.exit(0)),
    "pwd": lambda: (handle_pwd(), sys.exit(0)),
    "cd": lambda: (handle_pwd(), sys.exit(0)),
    "type": lambda: (handle_type(), sys.exit(0)),
    "history": lambda: (handle_history(), sys.exit(0)),
    "declare": lambda: (handle_declare(), sys.exit(0)),
    "jobs": lambda: (handle_jobs(), sys.exit(0)),
    "exit": lambda: sys.exit(0),
  }

  if args[0] in dispatch:
    dispatch[args[0]]()
  else:
    os.execvp(args[0], args)
