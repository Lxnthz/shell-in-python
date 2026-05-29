import os
import sys
import subprocess
import readline
from .. import state

def _common_prefix(strings: list[str]) -> str:
  if not strings:
    return ""
  prefix = strings[0]
  for s in strings[1:]:
    while not s.startswith(prefix):
      prefix = prefix[:-1]
      if not prefix:
        return ""
  return prefix
 
 
def _complete_path(prefix: str) -> list[str]:
  """Return file/dir completions for prefix (handles nested paths)."""
  directory, partial = os.path.split(prefix)
  base = directory or "."
  try:
    entries = os.listdir(base)
  except OSError:
    return []

  results = []
  for entry in entries:
    if entry.startswith(partial):
      full = os.path.join(directory, entry) if directory else entry
      if os.path.isdir(full):
        full += "/"
      results.append(full)
  return sorted(results)
 
 
def _complete_commands(text: str) -> list[str]:
  """Return matching builtin + PATH commands."""
  matches, seen = [], set()
  for cmd in state.BUILTIN_COMMANDS:
    if cmd.startswith(text):
      matches.append(cmd); seen.add(cmd)
  for d in os.environ.get("PATH", "").split(os.pathsep):
    try:
      if os.path.isdir(d):
        for entry in os.listdir(d):
          fp = os.path.join(d, entry)
          if entry.startswith(text) and entry not in seen and os.access(fp, os.X_OK):
            matches.append(entry); seen.add(entry)
    except OSError:
      continue
  return sorted(matches)
 
 
# ---------------------------------------------------------------------------
# Programmable completion (complete builtin)
# ---------------------------------------------------------------------------
 
def handle_complete(args: list[str]):
  """
  complete -F func cmd   → register completer function
  complete -A action cmd → register action-based completer
  complete -p [cmd]      → print specs
  complete -r cmd        → remove spec
  complete               → print all specs (same as -p)
  """
  if len(args) == 1 or (len(args) == 2 and args[1] == "-p"):
    # print all specs
    if not state.complete_specs:
      print("complete: no programmable completions registered", file=sys.stderr)
    else:
      for cmd, spec in sorted(state.complete_specs.items()):
        _print_spec(cmd, spec)
    return

  if args[1] == "-p":
    cmd = args[2]
    if cmd not in state.complete_specs:
      print(f"complete: {cmd}: no completion specification", file=sys.stderr)
    else:
      _print_spec(cmd, state.complete_specs[cmd])
    return

  if args[1] == "-r":
    if len(args) < 3:
      print("complete: -r: option requires an argument", file=sys.stderr); return
    cmd = args[2]
    if cmd in state.complete_specs:
      del state.complete_specs[cmd]
    else:
      print(f"complete: {cmd}: no completion specification", file=sys.stderr)
    return

  # Parse flags and register
  spec: dict = {"flags": [], "env": {}}
  i = 1
  while i < len(args):
    flag = args[i]
    if flag in ("-F", "-C", "-A", "-W"):
      if i + 1 >= len(args):
        print(f"complete: {flag}: option requires an argument", file=sys.stderr); return
      spec["flags"].append((flag, args[i + 1])); i += 2
    elif flag.startswith("-e") or flag == "--env":
      # -e VAR=VALUE pass env to completer
      if i + 1 >= len(args):
        print(f"complete: {flag}: option requires an argument", file=sys.stderr); return
      k, _, v = args[i + 1].partition("=")
      spec["env"][k] = v; i += 2
    else:
      # positional = command name
      state.complete_specs[flag] = spec; i += 1
  
 
def _print_spec(cmd: str, spec: dict):
  flags_str = " ".join(f"{f} '{v}'" for f, v in spec.get("flags", []))
  print(f"complete {flags_str} {cmd}")
 
 
# ---------------------------------------------------------------------------
# Main completer class wired into readline
# ---------------------------------------------------------------------------
 
class ShellCompleter:
  def __init__(self):
    self.matches: list[str] = []

  def complete(self, text: str, state: int):
    if state == 0:
      self.matches = self._get_matches(text)
    try:
      m = self.matches[state]
      return m + " " if len(self.matches) == 1 and not m.endswith("/") else m
    except IndexError:
      return None

  def _get_matches(self, text: str) -> list[str]:
    line = readline.get_line_buffer()
    tokens = line.lstrip().split()

    # Are we completing a command name (first token)?
    completing_cmd = not tokens or (len(tokens) == 1 and not line.endswith(" "))

    if completing_cmd:
      return _complete_commands(text)

    cmd = tokens[0]

    # Programmable completion
    if cmd in state.complete_specs:
      return self._programmable_matches(cmd, tokens, text)

    # Filename / directory completion for arguments
    return _complete_path(text)

  def _programmable_matches(self, cmd: str, tokens: list[str], text: str) -> list[str]:
    spec = state.complete_specs[cmd]
    results: list[str] = []

    for flag, value in spec.get("flags", []):
      if flag in ("-F", "-C"):
        # Call external completer script/function
        try:
          env = os.environ.copy()
          env.update(spec.get("env", {}))
          # Bash passes: $1=cmd, $2=current word, $3=previous word
          prev_word = tokens[-1] if not text else (tokens[-2] if len(tokens) >= 2 else "")
          
          # Add COMP_LINE and COMP_POINT
          line_buf = readline.get_line_buffer()
          env["COMP_LINE"] = line_buf
          env["COMP_POINT"] = str(readline.get_endidx() if hasattr(readline, 'get_endidx') else len(line_buf))
          
          out = subprocess.check_output(
              [value, tokens[0], text, prev_word], env=env, text=True, stderr=subprocess.DEVNULL
          )
          results.extend(w for w in out.split() if w.startswith(text))
        except Exception:
          pass
      elif flag == "-A":
        if value == "file":
          results.extend(_complete_path(text))
        elif value == "command":
          results.extend(_complete_commands(text))
        elif value == "directory":
          results.extend(p for p in _complete_path(text) if p.endswith("/"))
      elif flag == "-W":
        wordlist = value.split()
        results.extend(w for w in wordlist if w.startswith(text))

    # Partial completion: longest common prefix
    if len(results) > 1:
      prefix = _common_prefix(results)
      if prefix and prefix != text:
        return [prefix] + results
    return sorted(set(results))