"""Command parsing: tokenisation, redirections, variable expansion"""

import sys
import os
import re
from . import state

def expand_variables(text: str) -> str:
  """Expand $VAR and ${VAR} references"""
  def replace(m):
    name = m.group(1) or m.group(2)
    if name in state.shell_variables:
      return state.shell_variables[name]
    return os.environ.get(name, "")

  text = re.sub(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)', replace, text)
  return text

def parse_command(command_str: str) -> list[str]:
  """Tokenise a command string honouring quotes, escapes, and $VAR expansion"""
  args = []
  current: list[str] = []
  in_sq = in_dq = False
  token_started = False
  i = 0

  while i < len(command_str):
    ch = command_str[i]

    if ch == '\\' and not in_sq:
      token_started = True
      if in_dq:
        if i + 1 < len(command_str) and command_str[i + 1] in ('"', '\\', '$', '\n'):
          current.append(command_str[i + 1])
          i += 2
        else:
          current.append('\\')
          i += 1
      else:
        if i + 1 < len(command_str):
          current.append(command_str[i + 1])
          i += 2
        else:
          current.append('\\')
          i += 1
    elif ch == "'" and not in_dq:
      token_started = True
      in_sq = not in_sq; i += 1
    elif ch == '"' and not in_sq:
      token_started = True
      in_dq = not in_dq; i += 1
    elif ch == '$' and not in_sq:
      m = re.match(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)', command_str[i:])
      if m:
        name = m.group(1) or m.group(2)
        val = state.shell_variables.get(name, os.environ.get(name, ""))
        if val:
          current.append(val)
          token_started = True
        i += len(m.group(0))
      else:
        current.append(ch); token_started = True; i += 1
    elif ch.isspace() and not in_sq and not in_dq:
      if token_started:
        args.append(''.join(current))
        current = []
        token_started = False
      i += 1
    else:
      current.append(ch)
      token_started = True
      i += 1
  
  if token_started:
    args.append(''.join(current))
  
  return args

def parse_redirection(args: list[str]) -> dict | None:
  """Strip redirection tokens from args and return a parsed dict"""
  redir = dict(redirect_stdout=None, redirect_stderr=None, append_stdout=False, append_stderr=False, args=[])
  
  clean = []
  i = 0

  OPS = {
    ">": ("stdout", False), "1>": ("stdout", False),
    ">>": ("stdout", True), "1>>": ("stdout", True),
    "2>": ("stderr", False), "2>>": ("stderr", True),
  }

  while i < len(args):
    a = args[i]
    if a in OPS:
      if i + 1 >= len(args):
        print(f"syntax error: expected file after '{a}", file=sys.stderr)
        return None
      stream, append = OPS[a]

      if stream == "stdout":
        redir["redirect_stdout"] = args[i + 1]
        redir["append_stdout"] = append
      else:
        redir["redirect_stderr"] = args[i + 1]
        redir["append_stderr"] = append
      i += 2
    else:
      clean.append(a); i += 1
  
  redir["args"] = clean
  return redir
