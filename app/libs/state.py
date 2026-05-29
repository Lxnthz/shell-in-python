"""Shared shell state"""

import readline

BUILTIN_COMMANDS = [
  "echo",
  "exit",
  "history",
  "type",
  "pwd",
  "cd",
  "jobs",
  "complete",
  "declare"
]

# History
manual_history: list[str] = []
history_base_for_append: int = 0

# Variables (declare builtins)
shell_variables: dict[str, str] = {}

# Jobs
# {job_num: {"pid": num, "cmd": str, "status": "running"|"done"}}
jobs: dict[int, dict] = {}

# Programmable completion specs
# {"cmd": {"flags": [...], "action": str, "env": dict}}
complete_specs: dict[str, dict] = {}