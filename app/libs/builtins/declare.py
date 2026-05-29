"""declare builtin - store and print shell variables"""

import sys
import re
from .. import state

_VALID_NAME = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

def handle_declare(args):
  """
  declare               -> print all variables
  declare -p            -> print all variables (bash compat)
  declare -p NAME       -> print one variable
  declare NAME-VALUE    -> set variable
  declare NAME          -> print 'declare: NAME: not found' if absent
  """

  if len(args) == 1:
    if not state.shell_variables:
      print("declare: no variables set", file=sys.stderr)
    else:
      for k, v in sorted(state.shell_variables.items()):
        print(f"declare -- {k}=\"{v}\"")
    return

  # -p flag
  if args[1] == '-p':
    if len(args) == 2:
      if not state.shell_variables:
        print("declare: no variables set", file=sys.stderr)
      else:
        for k, v in sorted(state.shell_variables.items()):
          print(f"declare -- {k}=\"{v}\"")
    else:
      name = args[2]
      if name in state.shell_variables:
        print(f"declare -- {name}=\"{state.shell_variables[name]}\"")
      else:
        print(f"declare: {name}: not found", file=sys.stderr)
    return

  # NAME=VALUE or bare NAME
  for token in args[1:]:
    if '=' in token:
      name, _, value = token.partition('=')
      if not _VALID_NAME.match(name):
        print(f"declare: `{name}={value}`: not a valid identifier", file=sys.stderr)
        continue
      state.shell_variables[name] = value
    else:
      name = token
      if not _VALID_NAME.match(name):
        print(f"declare: `{name}={value}`: not a valid identifier", file=sys.stderr)
        continue
      if name not in state.shell_variables:
        print(f"declare: `{name}`: not found", file=sys.stderr)
      else:
        print(f"declare -- {name}=\"{state.shell_variables[name]}\"")