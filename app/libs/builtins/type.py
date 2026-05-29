import os
import sys
from .. import state

def handle_type(args):
  if len(args) < 2:
    print("type: missing file operand", file=sys.stderr)
    return
  cmd = args[1]
  if cmd in state.BUILTIN_COMMANDS:
    print(f"{cmd} is a shell builtin")
    return
  for d in os.environ.get("PATH", "").split(os.pathsep):
    fp = os.path.join(d, cmd)
    if os.path.isfile(fp) and os.access(fp, os.X_OK):
      print(f"{cmd} is {fp}")
      return
  print(f"{cmd}: not found")