"""Shell entry point"""
import atexit
import sys
import os
import readline
from .libs import state
from .libs.builtins import (handle_echo, handle_cd, handle_pwd, handle_type, handle_history, handle_declare)
from .libs.parser import parse_command, parse_redirection
from .libs.executor import execute_command, execute_pipeline
from .libs.jobs import handle_jobs, start_background_job, reap_jobs
from .libs.completion import ShellCompleter, handle_complete

def setup_readline():
  completer = ShellCompleter()
  readline.set_completer(completer.complete)
  readline.parse_and_bind("tab: complete")
  readline.set_completer_delims(' \t\n')

  histfile = os.environ.get("HISTFILE")
  if histfile and os.path.exists(histfile):
    try:
      with open(histfile, 'r', errors='replace') as f:
        for raw in f:
          entry = raw.rstrip('\n')
          if entry:
            state.manual_history.append(entry)
      state.history_base_for_append = len(state.manual_history)
    except Exception:
      pass

  def save_history():
    if histfile:
      try:
        new_cmds = state.manual_history[state.history_base_for_append:]
        if new_cmds:
          with open(histfile, 'a') as f:
            for cmd in new_cmds:
              f.write(cmd + '\n')
      except Exception:
        pass

  atexit.register(save_history)

def run_builtin(args, parsed):
  """Dispatch to builtin; return True if handled"""
  cmd = args[0]
  rs = parsed['redirect_stdout']
  as_ = parsed['append_stdout']
  re_ = parsed['redirect_stderr']
  ae = parsed['append_stderr']

  if cmd == "exit":
    sys.exit(int(args[1]) if len(args) > 1 else 0)
  elif cmd == "echo":    handle_echo(args, rs, as_, re_, ae)
  elif cmd == "pwd":     handle_pwd()
  elif cmd == "cd":      handle_cd(args)
  elif cmd == "type":    handle_type(args)
  elif cmd == "history": handle_history(args)
  elif cmd == "declare": handle_declare(args)
  elif cmd == "jobs":    handle_jobs(args)
  elif cmd == "complete": handle_complete(args)
  else:
    return False
  
  return True

def main():
  setup_readline()
  sys.stdout.reconfigure(line_buffering=True)

  while True:
    try:
      reap_jobs()  # collect finished background jobs before each prompt

      try:
        line = input("$ ")
      except EOFError:
        print(); break

      if line:
        last = state.manual_history[-1] if state.manual_history else None
        if not last or last != line:
          try:
            readline.add_history(line)
          except NameError:
            pass
        state.manual_history.append(line)

      if not line.strip():
        continue

      # Background job: strip trailing &
      background = line.rstrip().endswith('&')
      if background:
        line = line.rstrip()[:-1].rstrip()

      # Pipeline
      if '|' in line:
        execute_pipeline(line)
        continue

      args = parse_command(line)
      if not args:
        continue

      parsed = parse_redirection(args)
      if parsed is None:
        continue
      args = parsed['args']
      if not args:
        continue

      if background:
        start_background_job(args)
        continue

      if not run_builtin(args, parsed):
        execute_command(
          args,
          redirect_stdout=parsed['redirect_stdout'],
          redirect_stderr=parsed['redirect_stderr'],
          append_stdout=parsed['append_stdout'],
          append_stderr=parsed['append_stderr'],
        )

    except KeyboardInterrupt:
      print()
    except Exception as e:
      print(f"Error: {e}", file=sys.stderr)

 
if __name__ == "__main__":
  main()
    

  