import readline
import sys
from .. import state

def handle_history(args):
  if len(args) > 1:
    flag = args[1]
    if flag == "-r":
      if len(args) < 3:
        print("history: -r: option requires an argument", file=sys.stderr)
        return
      try:
        with open(args[2], 'r', errors='replace') as f:
          state.manual_history.clear()
          for raw in f:
            entry = raw.rstrip('\n')
            if entry:
              state.manual_history.append(entry)
      except Exception:
        print(f"history: {args[2]}: cannot read history file", file=sys.stderr)
    
    elif flag == '-w':
      if len(args) < 3:
        print("history: -w: option requires an argument", file=sys.stderr)
        return
      try:
        with open(args[2], 'w') as f:
          for line in state.manual_history:
            f.write(line + '\n')
      except Exception:
        print(f"history: {args[2]}: cannot write history file", file=sys.stderr)
    
    elif flag == '-a':
      if len(args) < 3:
        print("history: -a: option requires an argument", file=sys.stderr)
        return
      new = len(state.manual_history) - state.history_base_for_append
      if new > 0:
        try:
          with open(args[2], 'a') as f:
            for i in range(state.history_base_for_append, len(state.manual_history)):
              f.write(state.manual_history[i] + '\n')
          state.history_base_for_append = len(state.manual_history)
        except Exception:
          print(f"history: {args[2]}: cannot append to history file", file=sys.stderr)
    
    elif flag.strip('-').isdigit():
      n = int(flag)
      total = len(state.manual_history)
      for i in range(max(0, total - n), total):
        print(f"{i + 1:5d} {state.manual_history[i]}")
    
    else:
      print(f"history: {flag}: invalid option", file=sys.stderr)
  else:
    for i, line in enumerate(state.manual_history):
      print(f"{i + 1:5d} {line}")
