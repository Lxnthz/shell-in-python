import os
import sys

def handle_cd(args):
  if len(args) < 2:
    print("cd: missing argument", file=sys.stderr)
    return
  path = args[1]
  if path == "~":
    path = os.environ.get("HOME", os.path.expanduser("~"))
  try:
    os.chdir(path)
  except FileNotFoundError:
    print(f"cd: {path}: No such file or directory", file=sys.stderr)
  except Exception as e:
    print(f"cd: {e}", file=sys.stderr)